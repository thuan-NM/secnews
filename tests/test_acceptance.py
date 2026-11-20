"""Kiểm nghiệm thu SRS §5 bằng feed mẫu, Telegram và LLM giả (respx)."""
import json
import logging
from datetime import datetime
from pathlib import Path

import pytest
import respx

from secnews import __main__ as app
from secnews import telegram
from secnews.config import LLM, Config, Source
from secnews.db import DB

FIX = Path(__file__).parent / "fixtures"
TOKEN = "123:SECRETTOKEN"
TG = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
WL = [("keycloak", ["keycloak"]), ("ios", ["ios"])]


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(telegram, "sleep", lambda s: None)


def cfg(sources=None, llm=None):
    return Config(chat_id=-100, admin_chat_id=7, bot_token=TOKEN, watchlist=WL, llm=llm or LLM(),
                  sources=sources or [Source("cisa-kev", "kev", "https://kev"), Source("news", "rss", "https://feed")])


def sent(route, chat_id=None):
    bodies = [json.loads(c.request.read()) for c in route.calls]
    return [b["text"] for b in bodies if chat_id is None or b["chat_id"] == chat_id]


def mock_sources(feed=None, kev=None):
    respx.get("https://kev").respond(200, content=kev or (FIX / "kev.json").read_bytes())
    respx.get("https://feed").respond(200, content=feed or (FIX / "feed.xml").read_bytes())


@respx.mock
def test_ac01_run_twice_sends_once():
    mock_sources()
    tg = respx.post(TG).respond(200, json={"ok": True})
    db = DB(":memory:")
    app.run(cfg(), db)
    app.run(cfg(), db)
    alerts = sent(tg, -100)
    # KEV CVE-2026-2222 (Apple iOS) là ALERT; bài RSS iOS cùng CVE bị chặn bởi FR-05
    assert len(alerts) == 1 and "CVE-2026-2222" in alerts[0]
    tiers = dict(db.conn.execute("SELECT key, tier FROM items").fetchall())
    assert tiers == {"kev:CVE-2026-2222": "ALERT", "kev:CVE-2026-3333": "SKIP",
                     "guid-1": "DIGEST", "https://news.example/ios": "SKIP", "guid-3": "SKIP"}


@respx.mock
def test_ac02_same_cve_three_sources_over_two_days_one_message():
    item = ('<item><guid>{g}</guid><title>Keycloak CVE-2026-7777 ({g})</title>'
            '<link>https://{g}.example/</link><description>x</description></item>')
    srcs = []
    for g in ("a", "b", "c"):
        xml = f'<rss version="2.0"><channel><title>t</title>{item.format(g=g)}</channel></rss>'
        respx.get(f"https://{g}").respond(200, content=xml.encode())
        srcs.append(Source(g, "rss", f"https://{g}"))
    tg = respx.post(TG).respond(200, json={"ok": True})
    db = DB(":memory:")

    def age_one_day():
        db.conn.execute("UPDATE items SET created_at = datetime(created_at, '-1 day')")

    app.run(cfg(srcs[:1]), db)                 # ngày 1: nguồn a, chờ digest
    age_one_day()
    app.run(cfg(srcs[:2]), db)                 # ngày 2: nguồn b, CVE đang chờ digest
    app.digest(cfg(srcs), db, now=datetime(2026, 11, 20))
    age_one_day()
    app.run(cfg(srcs), db)                     # ngày 3: nguồn c, CVE đã gửi
    app.digest(cfg(srcs), db, now=datetime(2026, 11, 21))
    msgs = sent(tg, -100)
    assert len(msgs) == 1 and "(a)" in msgs[0] and "(b)" not in msgs[0]
    tiers = dict(db.conn.execute("SELECT key, tier FROM items").fetchall())
    assert tiers == {"a": "DIGEST", "b": "SKIP", "c": "SKIP"}


@respx.mock
@pytest.mark.parametrize("llm", [LLM(enabled=False), LLM(enabled=True, base_url="https://llm/v1", model="m")])
def test_ac04_llm_off_or_failing_still_sends(llm, fake_llm):
    mock_sources()
    fake_llm.outcome = ConnectionError("down")
    tg = respx.post(TG).respond(200, json={"ok": True})
    db = DB(":memory:")
    app.run(cfg(llm=llm), db)
    app.digest(cfg(llm=llm), db, now=datetime(2026, 11, 20))
    alert, dig = sent(tg, -100)
    assert "Memory corruption" in alert and "Hành động" not in alert   # dùng snippet
    assert "Keycloak 26.1 patches" in dig


@respx.mock
def test_llm_summary_used_in_alert(fake_llm):
    mock_sources()
    fake_llm.outcome = '{"summary_vi": "Tóm tắt VN", "action_vi": "Cập nhật iOS"}'
    tg = respx.post(TG).respond(200, json={"ok": True})
    db = DB(":memory:")
    app.run(cfg(llm=LLM(enabled=True, base_url="https://llm/v1", model="m")), db)
    alert = sent(tg, -100)[0]
    assert "Tóm tắt VN" in alert and "Hành động: Cập nhật iOS" in alert


@respx.mock
def test_ac06_dead_source_other_runs_admin_once():
    respx.get("https://kev").respond(200, content=(FIX / "kev.json").read_bytes())
    respx.get("https://feed").respond(503)
    tg = respx.post(TG).respond(200, json={"ok": True})
    db = DB(":memory:")
    for _ in range(7):
        app.run(cfg(), db)
    assert len(sent(tg, -100)) == 1                         # KEV vẫn chạy
    admin = sent(tg, 7)
    assert len(admin) == 1 and "news" in admin[0] and "5" in admin[0]


@respx.mock
def test_source_recovers_resets_counter():
    mock_sources()
    respx.post(TG).respond(200, json={"ok": True})
    db = DB(":memory:")
    db.record_error("news", "x")
    app.run(cfg(), db)
    assert db.conn.execute("SELECT count(*) FROM source_errors").fetchone()[0] == 0


@respx.mock
def test_ac05_digest_long_with_script():
    items = "".join(
        f'<item><guid>g{i}</guid><title>&lt;script&gt;Keycloak {i}&lt;/script&gt;</title>'
        f'<link>https://x/{i}</link><description>{"y" * 400}</description></item>' for i in range(30))
    mock_sources(feed=f'<rss version="2.0"><channel><title>t</title>{items}</channel></rss>'.encode())
    tg = respx.post(TG).respond(200, json={"ok": True})
    db = DB(":memory:")
    app.run(cfg(), db)
    tg.calls.reset()
    app.digest(cfg(), db, now=datetime(2026, 11, 20))
    msgs = sent(tg, -100)
    assert sum(map(len, msgs)) > 9000 and len(msgs) > 1
    assert all(len(m) <= 4096 for m in msgs) and "<script>" not in "".join(msgs)
    assert db.pending_digest() == []


def test_digest_nothing_sends_nothing(capsys):
    app.digest(cfg(), DB(":memory:"), dry_run=True)
    assert capsys.readouterr().out == ""


@respx.mock
def test_main_crash_notifies_admin_and_hides_token(tmp_path, monkeypatch, caplog):
    (tmp_path / "config.yaml").write_text(
        "chat_id: -100\nadmin_chat_id: 7\ndb_path: " + str(tmp_path / "x.db").replace("\\", "/") +
        "\nsources: [{name: news, type: rss, url: 'https://feed'}]\nwatchlist: {products: [keycloak]}\n",
        encoding="utf-8")
    (tmp_path / ".env").write_text(f"TELEGRAM_BOT_TOKEN={TOKEN}\n", encoding="utf-8")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setattr(app, "run", lambda *a: (_ for _ in ()).throw(RuntimeError(f"boom {TOKEN}")))
    tg = respx.post(TG).respond(200, json={"ok": True})
    with caplog.at_level(logging.INFO):
        code = app.main(["run", "--config", str(tmp_path / "config.yaml"), "--env", str(tmp_path / ".env")])
    assert code == 1
    admin = sent(tg, 7)
    assert len(admin) == 1 and "boom" in admin[0] and "SECRETTOKEN" not in admin[0]
    assert len(admin[0]) <= 4096
    assert "SECRETTOKEN" not in caplog.text


def test_repo_has_no_secrets():
    """NFR-03: không có bot token thật (dạng 123456789:AA...) hay key trong file được commit."""
    import re
    import subprocess
    root = Path(__file__).resolve().parents[1]
    files = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True).stdout.split()
    pattern = re.compile(r"\d{6,}:[A-Za-z0-9_-]{30,}|sk-[A-Za-z0-9]{20,}")
    for f in files:
        if f.endswith((".py", ".md", ".yaml", ".yml", ".txt", ".toml", ".example", ".json", ".xml")):
            assert not pattern.search((root / f).read_text(encoding="utf-8")), f
    assert ".env" in (root / ".gitignore").read_text().split()


def test_admin_message_long_text_stays_valid(capsys):
    c = cfg()
    app.notify_admin(c, "a" * 3497 + "<", dry_run=True)
    out = capsys.readouterr().out
    body = out.split("---\n", 1)[1].strip()
    assert len(body) <= 3500 and not body.endswith(("&", "&l", "&lt"))

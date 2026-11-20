from datetime import datetime
from types import SimpleNamespace

import pytest
import respx

from secnews import telegram

TOKEN = "123:SECRET"
URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    slept = []
    monkeypatch.setattr(telegram, "sleep", slept.append)
    return slept


def entry(**kw):
    d = dict(key="k", title="<script>alert(1)</script>", url='https://x/?a=1&b="2"', snippet="a < b & c")
    d.update(kw)
    return SimpleNamespace(**d)


def test_render_alert_escapes_everything():
    msg = telegram.render_alert(entry(), ["CVE-2026-1"], ["ios"], None)
    assert "<script>" not in msg and "&lt;script&gt;" in msg
    assert 'href="https://x/?a=1&amp;b=&quot;2&quot;"' in msg
    assert "a &lt; b &amp; c" in msg


def test_render_alert_with_summary():
    s = SimpleNamespace(summary_vi="Tóm <b>tắt</b>", action_vi="Cập nhật")
    msg = telegram.render_alert(entry(), ["CVE-2026-1"], ["ios"], s)
    assert "Tóm &lt;b&gt;tắt&lt;/b&gt;" in msg and "Hành động: Cập nhật" in msg


def test_ac05_digest_split_and_escape():
    items = [(f"k{i}", f"<script>bài {i}</script>", f"https://x/{i}", "x" * 300) for i in range(25)]
    msgs = telegram.render_digest(items, datetime(2026, 11, 20))
    total = sum(len(t) for t, _ in msgs)
    assert total > 9000 and len(msgs) >= 3
    assert all(len(t) <= 4096 for t, _ in msgs)
    assert [k for _, ks in msgs for k in ks] == [f"k{i}" for i in range(25)]  # không mất, không cắt bài
    assert msgs[0][0].startswith("<b>Bản tin bảo mật 20/11</b>")
    assert "<script>" not in "".join(t for t, _ in msgs)


def test_send_dry_run_prints(capsys):
    telegram.send("hello", "", 1, dry_run=True)
    assert "hello" in capsys.readouterr().out


@respx.mock
def test_send_payload():
    route = respx.post(URL).respond(200, json={"ok": True})
    telegram.send("hi", TOKEN, -100)
    body = route.calls.last.request.read().decode()
    assert '"parse_mode":"HTML"' in body and '"is_disabled":true' in body


@respx.mock
def test_send_429_waits_retry_after(no_sleep):
    route = respx.post(URL)
    route.side_effect = [respx.MockResponse(429, json={"ok": False, "parameters": {"retry_after": 7}}),
                         respx.MockResponse(200, json={"ok": True})]
    telegram.send("hi", TOKEN, -100)
    assert route.call_count == 2 and 7 in no_sleep


@respx.mock
def test_send_429_gives_up_after_3_retries():
    route = respx.post(URL).respond(429, json={"ok": False, "parameters": {"retry_after": 1}})
    with pytest.raises(telegram.TelegramError):
        telegram.send("hi", TOKEN, -100)
    assert route.call_count == 4


@respx.mock
def test_errors_never_contain_token():
    respx.post(URL).respond(400, json={"ok": False, "description": "Bad Request"})
    with pytest.raises(telegram.TelegramError) as ex:
        telegram.send("hi", TOKEN, -100)
    assert "SECRET" not in str(ex.value)


def test_send_without_token_fails():
    with pytest.raises(telegram.TelegramError, match="TELEGRAM_BOT_TOKEN"):
        telegram.send("hi", "", -100)


def test_esc_fit_never_breaks_entities():
    for budget in range(1, 40):
        out = telegram.esc_fit("a" * 30 + "<&>'\"" * 5, budget)
        assert len(out) <= budget and not out.endswith(("&", "&l", "&lt", "&am", "&amp", "&#", "&#x2"))


def test_alert_with_300_cves_and_worst_case_text_fits():
    cves = [f"CVE-2026-{i:05d}" for i in range(300)]
    s = SimpleNamespace(summary_vi="'" * 400, action_vi="'" * 200)
    msg = telegram.render_alert(entry(title="'" * 300, url="https://x/" + "a" * 900), cves, ["ios"] * 50, s)
    assert len(msg) <= 4096 and "(+290 CVE)" in msg


def test_digest_single_worst_case_item_fits():
    msgs = telegram.render_digest([("k", "'" * 300, "https://x/" + "&" * 150, "'" * 400)], datetime(2026, 1, 1))
    assert len(msgs) == 1 and len(msgs[0][0]) <= 4096


def test_overlong_url_drops_link_keeps_text():
    msg = telegram.render_alert(entry(url="https://x/" + "a" * 2000), [], [], None)
    assert "href" not in msg and "Đọc bài gốc" in msg


def test_dry_run_does_not_print_chat_id(capsys):
    telegram.send("hello", "", -1001234567, dry_run=True)
    assert "1001234567" not in capsys.readouterr().out

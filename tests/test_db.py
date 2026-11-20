from types import SimpleNamespace

from secnews.db import DB


def entry(key, source="feed"):
    return SimpleNamespace(key=key, source=source, url="https://x/" + key, title="t " + key, snippet="s")


def test_seen_save_mark_sent():
    db = DB(":memory:")
    assert not db.seen("a")
    db.save(entry("a"), ["CVE-2026-0001"], ["ios"], "DIGEST")
    assert db.seen("a")
    assert [r["key"] for r in db.pending_digest()] == ["a"]
    db.mark_sent("a")
    assert db.pending_digest() == []


def test_cve_recent_window_and_skip():
    db = DB(":memory:")
    db.save(entry("skip"), ["CVE-2026-0001"], [], "SKIP")
    assert not db.cve_recent(["CVE-2026-0001"])  # SKIP không tính
    db.save(entry("old"), ["CVE-2026-0002"], ["ios"], "ALERT")
    db.conn.execute("UPDATE items SET created_at = datetime('now', '-8 days') WHERE key = 'old'")
    assert not db.cve_recent(["CVE-2026-0002"])  # quá 7 ngày
    db.save(entry("new", "other"), ["CVE-2026-0003"], ["ios"], "DIGEST")
    assert db.cve_recent(["CVE-2026-9999", "CVE-2026-0003"])
    assert not db.cve_recent([])


def test_record_and_reset_error():
    db = DB(":memory:")
    assert [db.record_error("feed", "boom") for _ in range(3)] == [1, 2, 3]
    db.reset_error("feed")
    assert db.record_error("feed", "boom") == 1


def test_creates_parent_dir(tmp_path):
    DB(str(tmp_path / "data" / "x.db"))
    assert (tmp_path / "data" / "x.db").exists()

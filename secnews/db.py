"""SQLite: bảng items, source_errors (SDD §2.1; FR-04, FR-05, FR-12)."""
import json
import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
  key          TEXT PRIMARY KEY,
  source       TEXT,
  url          TEXT,
  title        TEXT,
  snippet      TEXT,
  cves         TEXT,
  matched      TEXT,
  tier         TEXT,
  summary      TEXT,
  sent_at      TEXT,
  created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS source_errors (
  source       TEXT PRIMARY KEY,
  count        INTEGER NOT NULL DEFAULT 0,
  last_error   TEXT
);
"""


class DB:
    def __init__(self, path):
        if path != ":memory:":
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def seen(self, key):
        return self.conn.execute("SELECT 1 FROM items WHERE key = ?", (key,)).fetchone() is not None

    def save(self, e, cves, matched, tier):
        with self.conn:
            self.conn.execute(
                "INSERT INTO items (key, source, url, title, snippet, cves, matched, tier)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (e.key, e.source, e.url, e.title, e.snippet, json.dumps(cves), json.dumps(matched), tier),
            )

    def set_summary(self, key, summary_json):
        with self.conn:
            self.conn.execute("UPDATE items SET summary = ? WHERE key = ?", (summary_json, key))

    def mark_sent(self, key):
        with self.conn:
            self.conn.execute("UPDATE items SET sent_at = CURRENT_TIMESTAMP WHERE key = ?", (key,))

    def cve_recent(self, cves, days=7):
        """CVE đã có trong một bài không bị SKIP trong `days` ngày qua (FR-05)."""
        for cve in cves:
            row = self.conn.execute(
                "SELECT 1 FROM items, json_each(items.cves)"
                " WHERE json_each.value = ? AND items.tier != 'SKIP'"
                " AND items.created_at > datetime('now', ?) LIMIT 1",
                (cve, f"-{int(days)} days"),
            ).fetchone()
            if row:
                return True
        return False

    def pending_digest(self):
        return self.conn.execute(
            "SELECT * FROM items WHERE tier = 'DIGEST' AND sent_at IS NULL ORDER BY created_at, rowid"
        ).fetchall()

    def record_error(self, source, err):
        """Tăng bộ đếm lỗi liên tiếp, trả về số lần hiện tại."""
        with self.conn:
            self.conn.execute(
                "INSERT INTO source_errors (source, count, last_error) VALUES (?, 1, ?)"
                " ON CONFLICT(source) DO UPDATE SET count = count + 1, last_error = excluded.last_error",
                (source, str(err)[:500]),
            )
        return self.conn.execute("SELECT count FROM source_errors WHERE source = ?", (source,)).fetchone()[0]

    def reset_error(self, source):
        with self.conn:
            self.conn.execute("DELETE FROM source_errors WHERE source = ?", (source,))

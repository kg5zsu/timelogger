import sqlite3
import threading
from datetime import datetime, timedelta, timezone


_SCHEMA = """
CREATE TABLE IF NOT EXISTS usage (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    start_ts    TEXT NOT NULL,
    end_ts      TEXT,
    duration    INTEGER DEFAULT 0,
    pid         INTEGER,
    process     TEXT,
    window_title TEXT,
    category    TEXT DEFAULT 'uncategorized'
)
"""

_INDEX = """
CREATE INDEX IF NOT EXISTS idx_usage_category ON usage(category)
"""


def _now():
    return datetime.now(timezone.utc)


class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(_SCHEMA)
        self.conn.execute(_INDEX)
        self.conn.commit()

    def close(self):
        self.conn.close()

    def get_active(self):
        with self._lock:
            cur = self.conn.execute(
                "SELECT * FROM usage WHERE end_ts IS NULL "
                "ORDER BY start_ts DESC LIMIT 1"
            )
            return cur.fetchone()

    def upsert_record(
        self, pid, process, window_title, category, merge_window=60
    ):
        now = _now().isoformat()
        active = self.get_active()
        if active:
            start = datetime.fromisoformat(active["start_ts"])
            elapsed = (_now() - start).total_seconds()
            if (
                active["process"] == process
                and active["window_title"] == window_title
                and active["category"] == category
                and elapsed < merge_window + 5
            ):
                self._extend_active(active["id"], now)
                return active["id"]
            self._close_active(active["id"], now)
        return self._insert_record(now, pid, process, window_title, category)

    def _extend_active(self, record_id, end_ts):
        with self._lock:
            self.conn.execute(
                "UPDATE usage SET end_ts=?, duration=ROUND((julianday(?) - "
                "julianday(start_ts)) * 86400) WHERE id=?",
                (end_ts, end_ts, record_id),
            )
            self.conn.commit()

    def _close_active(self, record_id, end_ts):
        with self._lock:
            self.conn.execute(
                "UPDATE usage SET end_ts=?, duration=ROUND((julianday(?) - "
                "julianday(start_ts)) * 86400) WHERE id=?",
                (end_ts, end_ts, record_id),
            )
            self.conn.commit()

    def _insert_record(self, start_ts, pid, process, window_title, category):
        with self._lock:
            cur = self.conn.execute(
                "INSERT INTO usage (start_ts, pid, process, window_title, category) "
                "VALUES (?, ?, ?, ?, ?)",
                (start_ts, pid, process, window_title, category),
            )
            self.conn.commit()
            return cur.lastrowid

    def prune_old(self, retention_days):
        cutoff = (_now() - timedelta(days=retention_days)).isoformat()
        with self._lock:
            cur = self.conn.execute(
                "DELETE FROM usage WHERE start_ts < ?", (cutoff,)
            )
            self.conn.commit()
            return cur.rowcount

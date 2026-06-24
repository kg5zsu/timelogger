import os
import sqlite3
from datetime import datetime, timedelta, timezone


DEFAULT_DB = "~/.local/share/timelogger/usage.db"


def _connect(db_path):
    conn = sqlite3.connect(os.path.expanduser(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _date_range(days_back):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)
    return start.isoformat(), end.isoformat()


def summary_by_category(db_path=None, days=7, start=None, end=None):
    if db_path is None:
        db_path = DEFAULT_DB
    if start is None or end is None:
        start, end = _date_range(days)
    conn = _connect(db_path)
    cur = conn.execute(
        """
        SELECT category, SUM(duration) as total_seconds, COUNT(*) as sessions
        FROM usage
        WHERE start_ts >= ? AND start_ts <= ?
        GROUP BY category
        ORDER BY total_seconds DESC
        """,
        (start, end),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def summary_by_app(db_path=None, days=7, start=None, end=None):
    if db_path is None:
        db_path = DEFAULT_DB
    if start is None or end is None:
        start, end = _date_range(days)
    conn = _connect(db_path)
    cur = conn.execute(
        """
        SELECT process, window_title, category,
               SUM(duration) as total_seconds, COUNT(*) as sessions
        FROM usage
        WHERE start_ts >= ? AND start_ts <= ?
        GROUP BY process, window_title, category
        ORDER BY total_seconds DESC
        """,
        (start, end),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def daily_breakdown(db_path=None, days=7, start=None, end=None):
    if db_path is None:
        db_path = DEFAULT_DB
    if start is None or end is None:
        start, end = _date_range(days)
    conn = _connect(db_path)
    cur = conn.execute(
        """
        SELECT DATE(start_ts) as day, category,
               SUM(duration) as total_seconds
        FROM usage
        WHERE start_ts >= ? AND start_ts <= ?
        GROUP BY day, category
        ORDER BY day ASC, total_seconds DESC
        """,
        (start, end),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def daily_total(db_path=None, days=7, start=None, end=None):
    if db_path is None:
        db_path = DEFAULT_DB
    if start is None or end is None:
        start, end = _date_range(days)
    conn = _connect(db_path)
    cur = conn.execute(
        """
        SELECT DATE(start_ts) as day,
               SUM(CASE WHEN end_ts IS NULL
                   THEN ROUND((julianday('now') - julianday(start_ts)) * 86400)
                   ELSE duration END) as total_seconds
        FROM usage
        WHERE start_ts >= ? AND start_ts <= ?
        GROUP BY day
        ORDER BY day ASC
        """,
        (start, end),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def check_overlaps(db_path=None):
    if db_path is None:
        db_path = DEFAULT_DB
    conn = _connect(db_path)
    cur = conn.execute(
        """
        SELECT a.id, a.start_ts, a.end_ts, a.process, a.window_title,
               b.id as next_id, b.start_ts as next_start
        FROM usage a
        JOIN usage b ON b.id = a.id + 1
        WHERE a.end_ts IS NOT NULL
          AND b.start_ts < a.end_ts
        ORDER BY a.start_ts
        """
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def raw_entries(db_path=None, days=1, start=None, end=None):
    if db_path is None:
        db_path = DEFAULT_DB
    if start is None or end is None:
        start, end = _date_range(days)
    conn = _connect(db_path)
    cur = conn.execute(
        """
        SELECT id, start_ts, end_ts, duration, process, window_title, category
        FROM usage
        WHERE start_ts >= ? AND start_ts <= ?
        ORDER BY start_ts DESC
        """,
        (start, end),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

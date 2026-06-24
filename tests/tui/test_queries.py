import os
import tempfile
from datetime import datetime, timezone

from logger.db import Database
from tui.queries import (
    daily_breakdown,
    daily_total,
    raw_entries,
    summary_by_app,
    summary_by_category,
)


def _seed_test_db(path):
    db = Database(path)
    db.upsert_record(1, "vim", "vim main.py", "coding")
    db.upsert_record(2, "firefox", "Firefox", "browsing")
    db.upsert_record(3, "terminal", "Terminal", "coding")
    active = db.get_active()
    if active:
        db._close_active(active["id"],
                         datetime.now(timezone.utc).isoformat())
    db.upsert_record(4, "slack", "Slack", "communication")
    active = db.get_active()
    if active:
        db._close_active(active["id"],
                         datetime.now(timezone.utc).isoformat())
    db.close()


def test_summary_by_category():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        _seed_test_db(path)
        rows = summary_by_category(path, days=365)
        categories = {r["category"] for r in rows}
        assert "coding" in categories
        assert "browsing" in categories
        assert "communication" in categories
    finally:
        os.unlink(path)


def test_summary_by_app():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        _seed_test_db(path)
        rows = summary_by_app(path, days=365)
        apps = {r["process"] for r in rows}
        assert "vim" in apps
        assert "firefox" in apps
        assert "slack" in apps
    finally:
        os.unlink(path)


def test_daily_breakdown():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        _seed_test_db(path)
        rows = daily_breakdown(path, days=365)
        assert len(rows) > 0
    finally:
        os.unlink(path)


def test_daily_total():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        _seed_test_db(path)
        rows = daily_total(path, days=365)
        assert len(rows) > 0
        for r in rows:
            assert "day" in r
            assert "total_seconds" in r
            assert r["total_seconds"] >= 0
    finally:
        os.unlink(path)


def test_raw_entries():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        _seed_test_db(path)
        rows = raw_entries(path, days=365)
        assert len(rows) >= 3
    finally:
        os.unlink(path)

import os
import tempfile
from logger.db import Database


def test_init_and_insert():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        db = Database(path)
        rid = db.upsert_record(1234, "vim", "vim - main.py", "coding")
        assert rid is not None
        active = db.get_active()
        assert active is not None
        assert active["process"] == "vim"
        assert active["window_title"] == "vim - main.py"
        assert active["category"] == "coding"
        assert active["pid"] == 1234
        db.close()
    finally:
        os.unlink(path)


def test_merge_same_record():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        db = Database(path)
        rid1 = db.upsert_record(1, "vim", "vim", "coding")
        rid2 = db.upsert_record(1, "vim", "vim", "coding")
        assert rid1 == rid2, "Should merge into same record"
        db.close()
    finally:
        os.unlink(path)


def test_new_record_on_change():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        db = Database(path)
        rid1 = db.upsert_record(1, "vim", "vim", "coding")
        rid2 = db.upsert_record(2, "firefox", "Firefox", "browsing")
        assert rid1 != rid2, "Should create new record for different window"
        active = db.get_active()
        assert active["process"] == "firefox"
        db.close()
    finally:
        os.unlink(path)


def test_prune():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        db = Database(path)
        db.conn.execute(
            "INSERT INTO usage (start_ts, end_ts, pid, process, window_title, category) "
            "VALUES ('2020-01-01T00:00:00', '2020-01-01T01:00:00', 1, 'old', 'old', 'old')"
        )
        db.conn.commit()
        db.upsert_record(2, "current", "current", "current")
        deleted = db.prune_old(365)
        assert deleted >= 1
        db.close()
    finally:
        os.unlink(path)

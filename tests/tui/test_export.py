import os
import tempfile

from logger.db import Database
from tui.export import export_csv


def _seed(path):
    db = Database(path)
    db.upsert_record(1, "vim", "vim", "coding")
    db.upsert_record(2, "firefox", "Firefox", "browsing")
    db.close()


def test_export_raw_csv():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False,
                                     dir="/tmp") as f:
        out = f.name
    try:
        _seed(db_path)
        path = export_csv(out, db_path=db_path, days=365, mode="raw")
        assert os.path.exists(path)
        with open(path) as f:
            content = f.read()
        assert "start_ts" in content
        assert "coding" in content
    finally:
        os.unlink(db_path)
        os.unlink(out)


def test_export_category_csv():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False,
                                     dir="/tmp") as f:
        out = f.name
    try:
        _seed(db_path)
        path = export_csv(out, db_path=db_path, days=365, mode="category")
        assert os.path.exists(path)
        with open(path) as f:
            content = f.read()
        assert "category" in content
        assert "coding" in content
    finally:
        os.unlink(db_path)
        os.unlink(out)

import json
import os
import tempfile

from logger.config import load_config, load_rules
from logger.db import Database
from logger.rules import match_window
from tui.export import export_csv
from tui.queries import summary_by_category


def test_full_flow_config_rules_db_export():
    with tempfile.TemporaryDirectory() as tmp:
        cfg_dir = os.path.join(tmp, "timelogger")
        os.makedirs(cfg_dir)
        config_path = os.path.join(cfg_dir, "config.json")
        rules_path = os.path.join(cfg_dir, "rules.json")
        db_path = os.path.join(tmp, "usage.db")

        with open(config_path, "w") as f:
            json.dump({"poll_interval": 1, "db_path": db_path}, f)

        rules = [
            {"pattern": ".*youtube.*", "process": ".*", "blacklist": True},
            {"pattern": ".*vim.*", "process": ".*", "category": "coding"},
            {"pattern": ".*firefox.*", "process": ".*",
             "category": "browsing"},
        ]
        with open(rules_path, "w") as f:
            json.dump(rules, f)

        orig_cfg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = tmp
        try:
            cfg = load_config()
            assert cfg["poll_interval"] == 1
            assert cfg["db_path"] == db_path

            loaded_rules = load_rules()
            assert len(loaded_rules) == 3

            cat, bl = match_window(loaded_rules, "vim main.py", "vim")
            assert cat == "coding"
            assert bl is False

            cat, bl = match_window(loaded_rules,
                                   "YouTube - Firefox", "firefox")
            assert cat is None
            assert bl is True

            db = Database(db_path)
            db.upsert_record(1, "vim", "vim main.py", "coding")
            db.upsert_record(2, "firefox", "Firefox", "browsing")
            db.upsert_record(3, "terminal", "Terminal", "coding")
            db.close()

            rows = summary_by_category(db_path, days=365)
            categories = {r["category"] for r in rows}
            assert "coding" in categories
            assert "browsing" in categories

            out_csv = os.path.join(tmp, "export.csv")
            export_csv(out_csv, db_path=db_path, days=365, mode="raw")
            with open(out_csv) as f:
                content = f.read()
            assert "coding" in content
            assert "browsing" in content
        finally:
            if orig_cfg is None:
                os.environ.pop("XDG_CONFIG_HOME", None)
            else:
                os.environ["XDG_CONFIG_HOME"] = orig_cfg

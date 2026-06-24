import os
from unittest.mock import patch

from logger.config import load_config, _default_config


def test_db_path_outside_allowed_falls_back_to_default():
    """db_path pointing outside the allowed dir should fall back to default."""
    bad_path = "/etc/passwd"
    with patch("logger.config._load_json", return_value={"db_path": bad_path}):
        cfg = load_config()
    default = os.path.expanduser(_default_config()["db_path"])
    assert cfg["db_path"] == default
    assert cfg["db_path"] != bad_path


def test_db_path_valid_is_kept():
    """db_path inside allowed dir should be used as-is."""
    xdg = os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share"
    )
    good_path = os.path.join(xdg, "timelogger", "custom.db")
    with patch("logger.config._load_json", return_value={"db_path": good_path}):
        cfg = load_config()
    assert cfg["db_path"] == good_path

import json
import logging
import os
import time

log = logging.getLogger("timelogger.config")


def _config_dir():
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return os.path.join(xdg, "timelogger")
    return os.path.join(os.path.expanduser("~"), ".config", "timelogger")


def _config_path():
    return os.path.join(_config_dir(), "config.json")


def _rules_path():
    return os.path.join(_config_dir(), "rules.json")


def _default_config():
    return {
        "poll_interval": 5,
        "db_path": os.path.join(
            os.environ.get(
                "XDG_DATA_HOME",
                os.path.join(os.path.expanduser("~"), ".local", "share"),
            ),
            "timelogger",
            "usage.db",
        ),
        "retention_days": 90,
        "merge_window": 60,
    }


def _load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _allowed_data_dir():
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share"
    )
    return os.path.realpath(os.path.join(base, "timelogger"))


def _validate_db_path(path):
    """Return path if it's inside the allowed data dir, else log + return default."""
    allowed = _allowed_data_dir()
    resolved = os.path.realpath(path)
    if not resolved.startswith(allowed + os.sep) and resolved != allowed:
        log.warning(
            "db_path %r is outside allowed directory %r; using default",
            path,
            allowed,
        )
        return _default_config()["db_path"]
    return path


def load_config():
    cfg = _load_json(_config_path(), {})
    merged = dict(_default_config())
    merged.update(cfg)
    merged["db_path"] = _validate_db_path(os.path.expanduser(merged["db_path"]))
    return merged


def load_rules():
    return _load_json(_rules_path(), [])


def config_mtime():
    try:
        return os.path.getmtime(_config_path())
    except OSError:
        return 0


def rules_mtime():
    try:
        return os.path.getmtime(_rules_path())
    except OSError:
        return 0

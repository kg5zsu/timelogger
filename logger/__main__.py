import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

from .config import load_config, load_rules, config_mtime, rules_mtime
from .db import Database
from .rules import match_window

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("timelogger")

_running = True
_config_mtime = 0
_rules_mtime = 0


def _handle_sighup(signum, frame):
    global _config_mtime, _rules_mtime
    _config_mtime = 0
    _rules_mtime = 0
    log.info("SIGHUP received; config will reload on next poll")


def _handle_sigterm(signum, frame):
    global _running
    log.info("SIGTERM received; shutting down")
    _running = False


def _get_active_window():
    try:
        import pywinctl

        win = pywinctl.getActiveWindow()
        if win is not None:
            title = win.title or win.getTitle() or ""
            return title, win.getPID() if hasattr(win, "getPID") else 0
    except Exception:
        pass

    try:
        win_id = subprocess.check_output(
            ["xdotool", "getactivewindow"], text=True
        ).strip()
        title = subprocess.check_output(
            ["xdotool", "getwindowname", win_id], text=True
        ).strip()
        pid = 0
        try:
            pid_str = subprocess.check_output(
                ["xprop", "-id", win_id, "_NET_WM_PID"], text=True
            )
            pid = int(pid_str.strip().split("=")[-1].strip())
        except Exception:
            pass
        return title, pid
    except Exception:
        return "", 0


def _get_process_name(pid):
    if pid <= 0:
        return ""
    try:
        import psutil

        return psutil.Process(pid).name()
    except Exception:
        return ""


def _run_poll(db, config):
    global _config_mtime, _rules_mtime

    cm = config_mtime()
    if cm != _config_mtime:
        log.info("Config changed, reloading")
        config.update(load_config())
        _config_mtime = cm

    rm = rules_mtime()
    if rm != _rules_mtime:
        log.info("Rules changed, reloading")
        _rules_mtime = rm

    rules = load_rules()

    title, pid = _get_active_window()
    if not title:
        return

    process = _get_process_name(pid)

    category, blacklisted = match_window(rules, title, process)
    if blacklisted:
        return

    if category is None:
        category = "uncategorized"

    db.upsert_record(
        pid,
        process or "unknown",
        title,
        category,
        merge_window=config.get("merge_window", 60),
    )


def main():
    global _config_mtime, _rules_mtime

    signal.signal(signal.SIGHUP, _handle_sighup)
    signal.signal(signal.SIGTERM, _handle_sigterm)
    signal.signal(signal.SIGINT, _handle_sigterm)

    config = load_config()
    _config_mtime = config_mtime()
    _rules_mtime = rules_mtime()

    os.makedirs(os.path.dirname(config["db_path"]), exist_ok=True)
    db = Database(config["db_path"])

    log.info(
        "timelogger started (poll=%ss, db=%s)",
        config["poll_interval"],
        config["db_path"],
    )

    try:
        while _running:
            try:
                _run_poll(db, config)
            except Exception:
                log.exception("Poll error")
            time.sleep(config.get("poll_interval", 5))
    finally:
        active = db.get_active()
        if active:
            db._close_active(
                active["id"], datetime.now(timezone.utc).isoformat()
            )
        db.close()
        log.info("timelogger stopped")


if __name__ == "__main__":
    main()

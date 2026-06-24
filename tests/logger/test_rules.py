from datetime import datetime
from logger.rules import match_window


def test_no_rules():
    assert match_window([], "vim", "vim") == (None, False)


def test_match_by_title():
    rules = [{"pattern": ".*vim.*", "category": "coding"}]
    assert match_window(rules, "vim - main.py", "vim") == ("coding", False)


def test_match_by_process():
    rules = [{"process": "firefox", "category": "browsing"}]
    assert match_window(rules, "Mozilla Firefox", "firefox") == ("browsing", False)


def test_blacklist():
    rules = [{"pattern": ".*youtube.*", "blacklist": True}]
    assert match_window(rules, "YouTube - Firefox", "firefox") == (None, True)


def test_day_constraint_match():
    rules = [
        {
            "pattern": ".*",
            "category": "work",
            "days": ["Mon", "Tue", "Wed", "Thu", "Fri"],
        }
    ]
    now = datetime(2026, 6, 24)  # Wednesday
    assert match_window(rules, "anything", "sh", now=now) == ("work", False)


def test_day_constraint_miss():
    rules = [{"pattern": ".*", "category": "work", "days": ["Mon"]}]
    now = datetime(2026, 6, 24)  # Wednesday
    assert match_window(rules, "anything", "sh", now=now) == (None, False)


def test_time_constraint():
    rules = [
        {
            "pattern": ".*",
            "category": "fun",
            "start_time": "18:00",
            "end_time": "23:59",
        }
    ]
    now = datetime(2026, 6, 24, 20, 0)
    assert match_window(rules, "game", "game", now=now) == ("fun", False)


def test_time_constraint_miss():
    rules = [
        {
            "pattern": ".*",
            "category": "fun",
            "start_time": "18:00",
            "end_time": "23:59",
        }
    ]
    now = datetime(2026, 6, 24, 14, 0)
    assert match_window(rules, "game", "game", now=now) == (None, False)


def test_invalid_pattern_skipped():
    """Invalid regex in pattern should not raise; rule is skipped."""
    rules = [{"pattern": "[invalid", "category": "coding"}]
    assert match_window(rules, "vim - main.py", "vim") == (None, False)


def test_invalid_process_pattern_skipped():
    """Invalid regex in process should not raise; rule is skipped."""
    rules = [{"pattern": ".*", "process": "[invalid", "category": "coding"}]
    assert match_window(rules, "vim - main.py", "vim") == (None, False)

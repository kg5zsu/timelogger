from datetime import datetime
from logger.rules import match_window


def test_empty_pattern_matches_all():
    rules = [{"category": "everything"}]
    assert match_window(rules, "anything at all", "sh") == (
        "everything", False)


def test_case_insensitive():
    rules = [{"pattern": "VIM", "category": "coding"}]
    assert match_window(rules, "vim main.py", "vim") == ("coding", False)
    assert match_window(rules, "VIM main.py", "vim") == ("coding", False)


def test_process_pattern():
    rules = [{"process": ".*python.*", "category": "dev"}]
    assert match_window(rules, "some window", "python3") == ("dev", False)
    assert match_window(rules, "some window", "bash") == (None, False)


def test_blacklist_overrides_category():
    rules = [
        {"pattern": ".*game.*", "blacklist": True},
        {"pattern": ".*", "category": "work"},
    ]
    assert match_window(rules, "Super Game", "game") == (None, True)
    assert match_window(rules, "Other", "sh") == ("work", False)


def test_first_match_wins():
    rules = [
        {"pattern": ".*vim.*", "category": "coding"},
        {"pattern": ".*vim.*", "category": "writing"},
    ]
    assert match_window(rules, "vim main.py", "vim") == ("coding", False)


def test_time_window_midnight_cross():
    rules = [
        {"pattern": ".*", "category": "night",
         "start_time": "22:00", "end_time": "06:00"}
    ]
    now = datetime(2026, 6, 24, 23, 0)
    assert match_window(rules, "anything", "sh", now=now) == ("night", False)
    now = datetime(2026, 6, 24, 12, 0)
    assert match_window(rules, "anything", "sh", now=now) == (None, False)


def test_no_process_match_returns_none():
    rules = [{"process": "firefox", "category": "browsing"}]
    assert match_window(rules, "Firefox", "chrome") == (None, False)


def test_multiple_rules_blacklist_first():
    rules = [
        {"pattern": ".*", "blacklist": True},
        {"pattern": ".*work.*", "category": "work"},
    ]
    assert match_window(rules, "work stuff", "app") == (None, True)

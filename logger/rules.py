import logging
import re
from datetime import datetime

log = logging.getLogger("timelogger.rules")


def _day_match(days, now):
    if not days:
        return True
    return now.strftime("%a") in days


def _time_match(start_time, end_time, now):
    if not start_time and not end_time:
        return True
    t = now.strftime("%H:%M")
    if start_time and end_time and start_time > end_time:
        return t >= start_time or t <= end_time
    if start_time and t < start_time:
        return False
    if end_time and t > end_time:
        return False
    return True


def match_window(rules, title, process_name, now=None):
    if now is None:
        now = datetime.now()

    for rule in rules:
        pattern = rule.get("pattern", ".*")
        proc_pat = rule.get("process", ".*")
        try:
            if not re.search(pattern, title, re.IGNORECASE):
                continue
        except re.error:
            log.warning("Invalid regex pattern in rule (skipping): %r", pattern)
            continue
        try:
            if not re.search(proc_pat, process_name, re.IGNORECASE):
                continue
        except re.error:
            log.warning("Invalid regex process pattern in rule (skipping): %r", proc_pat)
            continue
        if not _day_match(rule.get("days"), now):
            continue
        if not _time_match(
            rule.get("start_time"), rule.get("end_time"), now
        ):
            continue
        if rule.get("blacklist", False):
            return None, True
        return rule.get("category", "uncategorized"), False

    return None, False

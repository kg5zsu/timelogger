from datetime import datetime, timedelta, timezone
import json
import os
import re

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Select,
    TabbedContent,
    TabPane,
)

from .queries import (
    daily_breakdown,
    raw_entries,
    summary_by_app,
    summary_by_category,
)


def _rules_path():
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        base = os.path.join(xdg, "timelogger")
    else:
        base = os.path.join(os.path.expanduser("~"), ".config", "timelogger")
    return os.path.join(base, "rules.json")


def _load_rules():
    try:
        with open(_rules_path()) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_rules(rules):
    path = _rules_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(rules, f, indent=2)


PRESETS = [
    ("Today", "today"),
    ("Yesterday", "yesterday"),
    ("This Week", "week"),
    ("This Month", "month"),
    ("This Year", "year"),
    ("Custom", "custom"),
]


class CategoryEditScreen(Screen):
    def __init__(self, label_text, current_category):
        super().__init__()
        self.label_text = label_text
        self.current_category = current_category

    CSS = """
    Screen {
        align: center middle;
    }
    #dialog {
        width: 50;
        height: auto;
        padding: 2;
        border: thick $primary;
        background: $surface;
    }
    Label {
        margin-bottom: 1;
    }
    Input {
        margin-bottom: 1;
    }
    #buttons {
        height: auto;
        align: center middle;
    }
    Button {
        margin: 0 1;
    }
    """

    def compose(self):
        with Vertical(id="dialog"):
            yield Label(self.label_text)
            yield Input(value=self.current_category, id="cat-input",
                        placeholder="category name")
            with Horizontal(id="buttons"):
                yield Button("Save", id="save-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn")

    def on_button_pressed(self, event):
        if event.button.id == "save-btn":
            new_cat = self.query_one("#cat-input", Input).value.strip()
            self.dismiss(new_cat)
        elif event.button.id == "cancel-btn":
            self.dismiss(None)


class TimeloggerApp(App):
    TITLE = "timelogger"

    CSS = """
    Screen {
        background: $surface;
    }
    #controls {
        height: auto;
        margin: 0 1;
        padding: 0 1;
        align: center middle;
    }
    Label {
        margin: 0 1;
    }
    Input {
        width: 14;
    }
    Select {
        width: 20;
    }
    Button {
        margin: 0 1;
    }
    DataTable {
        height: 1fr;
    }
    #custom-range {
        display: none;
    }
    #custom-range Input {
        width: 14;
    }
    .rule-input {
        width: 20;
    }
    #rule-inputs, #rule-actions {
        height: auto;
        margin: 0 1;
        padding: 0 1;
        align: center middle;
    }
    """

    def __init__(self, db_path=None):
        super().__init__()
        self.db_path = db_path
        self.preset = "week"
        self._app_data = []
        self._cat_rules = []

    def compose(self):
        yield Header()
        with Horizontal(id="controls"):
            yield Label("Range:")
            yield Select(options=PRESETS, id="preset-select", value="week")
            with Horizontal(id="custom-range"):
                yield Label("From:")
                yield Input(placeholder="2026-06-24", id="start-input")
                yield Label("To:")
                yield Input(placeholder="2026-06-24", id="end-input")
            yield Button("Refresh", id="refresh-btn")
        with TabbedContent(initial="tab-categories"):
            with TabPane("Categories", id="tab-categories"):
                yield DataTable(id="cat-table")
                with Horizontal(id="rule-inputs"):
                    yield Input(placeholder="process pattern",
                                id="rule-process", classes="rule-input")
                    yield Input(placeholder="category",
                                id="rule-category", classes="rule-input")
                    yield Button("Add Rule", id="rule-add-btn")
                with Horizontal(id="rule-actions"):
                    yield Button("Delete Sel", id="rule-del-btn")
                    yield Button("Save Rules", id="rule-save-btn",
                                variant="primary")
                    yield Button("Reload", id="rule-reload-btn")
            with TabPane("Apps", id="tab-apps"):
                yield DataTable(id="app-table")
            with TabPane("Daily", id="tab-daily"):
                yield DataTable(id="daily-table")
            with TabPane("Log", id="tab-log"):
                yield RichLog(id="log-view", highlight=True, markup=True)
        yield Footer()

    def on_mount(self):
        self.refresh_all()

    def on_select_changed(self, event: Select.Changed):
        if event.select.id == "preset-select":
            self.preset = event.value
            custom = self.query_one("#custom-range", Horizontal)
            custom.display = event.value == "custom"
            self.refresh_all()

    def on_button_pressed(self, event: Button.Pressed):
        btn = event.button.id
        if btn == "refresh-btn":
            self.refresh_all()
        elif btn == "rule-add-btn":
            self._add_rule()
        elif btn == "rule-del-btn":
            self._delete_selected_rule()
        elif btn == "rule-save-btn":
            self._save_rules_notify()
        elif btn == "rule-reload-btn":
            self._load_categories()
            self._load_apps()

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id in ("start-input", "end-input"):
            self.refresh_all()

    def _compute_range(self):
        now = datetime.now(timezone.utc)
        if self.preset == "today":
            s = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return s.isoformat(), now.isoformat()
        elif self.preset == "yesterday":
            y = now - timedelta(days=1)
            s = y.replace(hour=0, minute=0, second=0, microsecond=0)
            e = y.replace(hour=23, minute=59, second=59, microsecond=999999)
            return s.isoformat(), e.isoformat()
        elif self.preset == "week":
            s = now - timedelta(days=now.weekday())
            s = s.replace(hour=0, minute=0, second=0, microsecond=0)
            return s.isoformat(), now.isoformat()
        elif self.preset == "month":
            s = now.replace(day=1, hour=0, minute=0, second=0,
                            microsecond=0)
            return s.isoformat(), now.isoformat()
        elif self.preset == "year":
            s = now.replace(month=1, day=1, hour=0, minute=0, second=0,
                            microsecond=0)
            return s.isoformat(), now.isoformat()
        elif self.preset == "custom":
            s_str = self.query_one("#start-input", Input).value.strip()
            e_str = self.query_one("#end-input", Input).value.strip()
            try:
                if s_str:
                    s = datetime.strptime(s_str, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc)
                else:
                    s = now - timedelta(days=7)
                if e_str:
                    e = datetime.strptime(e_str, "%Y-%m-%d").replace(
                        hour=23, minute=59, second=59,
                        tzinfo=timezone.utc)
                else:
                    e = now
                return s.isoformat(), e.isoformat()
            except ValueError:
                pass
        s = now - timedelta(days=7)
        return s.isoformat(), now.isoformat()

    def refresh_all(self):
        self._load_categories()
        self._load_apps()
        self._load_daily()
        self._load_log()

    def _load_categories(self):
        start, end = self._compute_range()
        table = self.query_one("#cat-table", DataTable)
        table.clear()
        table.add_columns("Process Pattern", "Category", "Actions")
        self._cat_rules = _load_rules()
        for i, r in enumerate(self._cat_rules):
            proc = r.get("process", ".*")
            cat = r.get("category", "uncategorized")
            table.add_row(proc, cat, "[edit]", key=str(i))

    def _load_apps(self):
        start, end = self._compute_range()
        rows = summary_by_app(self.db_path, start=start, end=end)
        table = self.query_one("#app-table", DataTable)
        table.clear()
        table.add_columns("Process", "Window", "Category", "Time (h)",
                          "Sessions", "Actions")
        self._app_data = list(rows)
        for i, r in enumerate(self._app_data):
            hours = round(r["total_seconds"] / 3600, 2) if r.get(
                "total_seconds") else 0
            table.add_row(
                r["process"] or "",
                r["window_title"] or "",
                r["category"] or "uncategorized",
                str(hours),
                str(r["sessions"]),
                "[edit]",
                key=str(i),
            )

    def _load_daily(self):
        start, end = self._compute_range()
        rows = daily_breakdown(self.db_path, start=start, end=end)
        table = self.query_one("#daily-table", DataTable)
        table.clear()
        table.add_columns("Day", "Category", "Time (h)")
        for r in rows:
            hours = round(r["total_seconds"] / 3600, 2) if r.get(
                "total_seconds") else 0
            table.add_row(r["day"], r["category"], str(hours))

    def _load_log(self):
        start, end = self._compute_range()
        rows = raw_entries(self.db_path, start=start, end=end)
        log = self.query_one("#log-view", RichLog)
        log.clear()
        log.write("[bold]Entries:[/]\n")
        for r in rows:
            dur = r.get("duration") or 0
            mins = round(dur / 60, 1)
            log.write(
                f"  {r['start_ts'][:19]} | {r['process']:<15} "
                f"| {r['category']:<12} | {mins}min"
            )

    def _add_rule(self):
        proc_input = self.query_one("#rule-process", Input)
        cat_input = self.query_one("#rule-category", Input)
        proc = proc_input.value.strip()
        cat = cat_input.value.strip()
        if not proc or not cat:
            return
        rules = _load_rules()
        rules.append({"pattern": ".*", "process": proc, "category": cat})
        _save_rules(rules)
        proc_input.value = ""
        cat_input.value = ""
        self._load_categories()
        self._load_apps()

    def _delete_selected_rule(self):
        table = self.query_one("#cat-table", DataTable)
        row_idx = table.cursor_row
        if row_idx is None or row_idx >= len(self._cat_rules):
            return
        self._cat_rules.pop(row_idx)
        _save_rules(self._cat_rules)
        self._load_categories()
        self._load_apps()

    def _save_rules_notify(self):
        _save_rules(self._cat_rules)
        self._load_categories()
        self._load_apps()

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        table = event.data_table
        if table.id == "app-table":
            row_idx = table.cursor_row
            if row_idx is None or row_idx >= len(self._app_data):
                return
            row = self._app_data[row_idx]
            self.push_screen(
                CategoryEditScreen(
                    f"Change category for [bold]{row['process']}[/]:",
                    row["category"] or "uncategorized",
                ),
                self._on_app_category_edited,
            )
        elif table.id == "cat-table":
            row_idx = table.cursor_row
            if row_idx is None or row_idx >= len(self._cat_rules):
                return
            rule = self._cat_rules[row_idx]
            self.push_screen(
                CategoryEditScreen(
                    f"Edit rule for [bold]{rule.get('process', '.*')}[/]:",
                    rule.get("category", "uncategorized"),
                ),
                self._on_rule_category_edited,
            )

    def _on_app_category_edited(self, new_cat):
        if new_cat is None:
            return
        # We need the row data; retrieve it from the hook context
        table = self.query_one("#app-table", DataTable)
        row_idx = table.cursor_row
        if row_idx is None or row_idx >= len(self._app_data):
            return
        row = self._app_data[row_idx]
        if new_cat == (row["category"] or "uncategorized"):
            return
        self._set_category_for_process(row["process"], new_cat)
        self.refresh_all()

    def _on_rule_category_edited(self, new_cat):
        if new_cat is None:
            return
        table = self.query_one("#cat-table", DataTable)
        row_idx = table.cursor_row
        if row_idx is None or row_idx >= len(self._cat_rules):
            return
        rule = self._cat_rules[row_idx]
        if new_cat == rule.get("category", "uncategorized"):
            return
        rules = _load_rules()
        for r in rules:
            if (r.get("process") == rule.get("process")
                    and r.get("pattern") == rule.get("pattern")):
                r["category"] = new_cat
                break
        _save_rules(rules)
        self._load_categories()
        self._load_apps()

    def _set_category_for_process(self, process_name, new_category):
        escaped = f".*{re.escape(process_name)}.*"
        rules = _load_rules()
        for rule in rules:
            if (rule.get("process") == escaped
                    and rule.get("pattern") == ".*"):
                if rule["category"] != new_category:
                    rule["category"] = new_category
                    _save_rules(rules)
                return
        rules.append({"pattern": ".*", "process": escaped,
                      "category": new_category})
        _save_rules(rules)

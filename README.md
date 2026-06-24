# timelogger

A terminal-based automatic time logging and reporting tool for Linux.

Logs active window/process activity in the background, classifies it by configurable rules, and provides a TUI dashboard for review and export.

## Installation

```bash
git clone <repo-url> && cd timelogger
./install.sh
```

Or manually:

```bash
pip install -r requirements.txt
mkdir -p ~/.config/timelogger
cp config.json rules.json ~/.config/timelogger/
```

## Usage

### Background logger daemon

```bash
python -m logger
```

Runs a polling loop to record active window data into `~/.local/share/timelogger/usage.db`.

### TUI dashboard

```bash
python -m tui
```

Opens an interactive terminal UI to view, filter, and export time logs.

### CSV export

```bash
python -m tui --export report.csv
python -m tui --export report.csv --export-mode category --days 30
```

## Systemd service

The installer sets up a user-level systemd service to run the logger in the background automatically.

```bash
# Status
systemctl --user status timelogger

# Stop / start / restart
systemctl --user stop timelogger
systemctl --user start timelogger
systemctl --user restart timelogger

# View live logs
journalctl --user -u timelogger -f

# Reload config (SIGHUP)
systemctl --user reload timelogger
```

To disable the service:

```bash
systemctl --user stop timelogger
systemctl --user disable timelogger
```

## Configuration

- `~/.config/timelogger/config.json` — daemon settings (poll interval, DB path, etc.)
- `~/.config/timelogger/rules.json` — window-to-category mapping rules

### Config options

| Key | Default | Description |
|---|---|---|
| `poll_interval` | `5` | Seconds between active-window checks |
| `db_path` | `~/.local/share/timelogger/usage.db` | SQLite database path |
| `retention_days` | `90` | Days to keep log entries before pruning |
| `merge_window` | `60` | Seconds of same-window activity to merge into one record |

### Rule format

```json
[
    {
        "pattern": ".*vim.*",
        "process": ".*",
        "category": "coding",
        "blacklist": false,
        "days": ["Mon","Tue","Wed","Thu","Fri"],
        "start_time": "09:00",
        "end_time": "17:00"
    }
]
```

- `pattern` — regex on window title
- `process` — regex on process name
- `category` — label assigned to matching activity
- `blacklist` — if true, skip logging this window entirely
- `days` — optional day-of-week filter (3-letter abbrev)
- `start_time` / `end_time` — optional time window (HH:MM)

## Dependencies

- Python >= 3.8
- pywinctl, psutil (window/process monitoring)
- textual, rich (TUI framework)
- python-dateutil (date handling)

## Privacy

Window titles and process names are recorded verbatim in plaintext SQLite at the configured `db_path` (`~/.local/share/timelogger/usage.db` by default). Anyone with read access to that file can see all logged activity.

To suppress logging for a sensitive application, add a blacklist rule to `~/.config/timelogger/rules.json`:

```json
{"pattern": ".*", "process": ".*keepass.*", "blacklist": true}
```

Blacklisted windows are never written to the database.

## Troubleshooting

### No window data being logged

- Ensure `DISPLAY` and `XAUTHORITY` are set correctly for the service:
  ```bash
  systemctl --user edit timelogger.service
  ```
  Add:
  ```
  [Service]
  Environment=DISPLAY=:0
  Environment=XAUTHORITY=/home/youruser/.Xauthority
  ```
- Restart the service after editing.
- Check the logs: `journalctl --user -u timelogger -f`

### TUI shows no data

- Make sure the logger has been running long enough to collect entries.
- Verify the DB path matches between config and TUI invocation.
- Try: `python -m tui --db ~/.local/share/timelogger/usage.db`

### Permission errors with pywinctl

- pywinctl requires X11 access. On Wayland, some features may not work.
- On X11, ensure `DISPLAY` is set and the user has access to the X server.

### Virtual environment

The installer creates a venv at `~/.local/share/timelogger/venv/`.
Use it directly to run commands without the systemd wrapper:

```bash
~/.local/share/timelogger/venv/bin/python -m logger
~/.local/share/timelogger/venv/bin/python -m tui
```

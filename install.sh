#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/timelogger"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/timelogger"
VENV_DIR="$DATA_DIR/venv"

echo "==> timelogger installer"
echo ""

# --- Python / venv ---
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "ERROR: No Python interpreter found. Install python3 first."
    exit 1
fi

echo "==> Creating virtual environment: $VENV_DIR"
"$PYTHON" -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "==> Installing dependencies..."
pip install --upgrade pip -q
pip install -r "$REPO_DIR/requirements.txt" -q
pip install -e "$REPO_DIR" -q

# --- Config ---
echo "==> Setting up config directory: $CONFIG_DIR"
mkdir -p "$CONFIG_DIR"

if [ ! -f "$CONFIG_DIR/config.json" ]; then
    if [ -f "$REPO_DIR/config.json" ]; then
        cp "$REPO_DIR/config.json" "$CONFIG_DIR/config.json"
    else
        cat > "$CONFIG_DIR/config.json" <<'EOF'
{
    "poll_interval": 5,
    "db_path": "$DATA_DIR/usage.db",
    "retention_days": 90,
    "merge_window": 60
}
EOF
    fi
fi

if [ ! -f "$CONFIG_DIR/rules.json" ]; then
    if [ -f "$REPO_DIR/rules.json" ]; then
        cp "$REPO_DIR/rules.json" "$CONFIG_DIR/rules.json"
    else
        cat > "$CONFIG_DIR/rules.json" <<'EOF'
[]
EOF
    fi
fi

echo "==> Setting up data directory: $DATA_DIR"
mkdir -p "$DATA_DIR"

# --- systemd user service ---
SERVICE_NAME="timelogger.service"
SERVICE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SERVICE_PATH="$SERVICE_DIR/$SERVICE_NAME"

if command -v systemctl &>/dev/null; then
    echo "==> Installing systemd user service..."
    mkdir -p "$SERVICE_DIR"

    cat > "$SERVICE_PATH" <<EOF
[Unit]
Description=timelogger — Automatic time logging daemon
After=graphical-session.target

[Service]
Type=simple
ExecStart=$VENV_DIR/bin/python -m logger
Restart=on-failure
RestartSec=10
Environment=DISPLAY=:0
Environment=XAUTHORITY=$HOME/.Xauthority
Environment=XDG_CONFIG_HOME=$HOME/.config
Environment=XDG_DATA_HOME=$HOME/.local/share
ExecReload=/bin/kill -HUP \$MAINPID

[Install]
WantedBy=default.target
EOF

    echo "==> Enabling and starting service (user mode)..."
    systemctl --user daemon-reload
    systemctl --user enable "$SERVICE_NAME"
    systemctl --user start "$SERVICE_NAME"

    echo "==> Service status:"
    systemctl --user --no-pager status "$SERVICE_NAME" 2>&1 || true
else
    echo "==> systemctl not found; skipping systemd setup."
    echo "    Manually start the logger with:"
    echo "      $VENV_DIR/bin/python -m logger"
fi

# --- .desktop file ---
DESKTOP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
echo "==> Installing .desktop file..."
mkdir -p "$DESKTOP_DIR"
sed "s|@VENV_DIR@|$VENV_DIR|g" "$REPO_DIR/timelogger.desktop" > "$DESKTOP_DIR/timelogger.desktop"
chmod +x "$DESKTOP_DIR/timelogger.desktop"

echo ""
echo "==> timelogger installation complete."
echo "    Config: $CONFIG_DIR"
echo "    Data:   $DATA_DIR"
echo "    Venv:   $VENV_DIR"
echo ""
echo "    Launch TUI:  $VENV_DIR/bin/python -m tui"
echo "    Or find 'timelogger' in your application menu."
echo ""
echo "    Systemd commands:"
echo "      systemctl --user status timelogger"
echo "      systemctl --user restart timelogger"
echo "      journalctl --user -u timelogger -f"

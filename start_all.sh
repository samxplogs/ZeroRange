#!/bin/bash
# ZeroRange - Complete startup script
# Launches main application + web servers

INSTALL_DIR="/home/sam/ZeroRange"
LOG_DIR="$INSTALL_DIR/logs"
PID_DIR="$INSTALL_DIR/run"

# Create local directories (no root needed)
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

echo "[$(date)] Starting ZeroRange services..."

cd "$INSTALL_DIR"

# 1. Start HTTP server for static files (port 8000)
echo "[$(date)] Starting HTTP server on port 8000..."
cd "$INSTALL_DIR/docs"
python3 -m http.server 8000 > "$LOG_DIR/http.log" 2>&1 &
HTTP_PID=$!
echo $HTTP_PID > "$PID_DIR/http.pid"
echo "[$(date)] HTTP server started (PID: $HTTP_PID)"

# 2. Start LCD API server (port 5000)
echo "[$(date)] Starting LCD API server on port 5000..."
cd "$INSTALL_DIR"
python3 web_lcd_server.py > "$LOG_DIR/lcd_api.log" 2>&1 &
API_PID=$!
echo $API_PID > "$PID_DIR/lcd_api.pid"
echo "[$(date)] LCD API server started (PID: $API_PID)"

# Wait for servers to start
sleep 2

# 3. Start main ZeroRange application (foreground — keeps systemd happy)
echo "[$(date)] Starting ZeroRange main application..."
cd "$INSTALL_DIR"
python3 zerorange.py >> "$LOG_DIR/zerorange.log" 2>&1

# Reached if zerorange.py exits
echo "[$(date)] ZeroRange main application stopped"

# Cleanup: kill web servers
echo "[$(date)] Stopping web servers..."
kill $HTTP_PID 2>/dev/null || true
kill $API_PID 2>/dev/null || true
rm -f "$PID_DIR"/*.pid

echo "[$(date)] All services stopped"

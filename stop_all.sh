#!/bin/bash
# ZeroRange - Stop all services

INSTALL_DIR="/home/sam/ZeroRange"
PID_DIR="$INSTALL_DIR/run"

echo "[$(date)] Stopping all ZeroRange services..."

# Stop main application
pkill -f "python3.*zerorange.py" 2>/dev/null || true

# Stop LCD API server
pkill -f "web_lcd_server.py" 2>/dev/null || true

# Stop HTTP server
pkill -f "http.server 8000" 2>/dev/null || true

# Clean PID files
rm -f "$PID_DIR"/*.pid 2>/dev/null || true

echo "[$(date)] All services stopped"

#!/bin/bash
# =============================================================================
# RecordPlayer Launcher Script
# =============================================================================
# Starts both go-librespot (Spotify Connect) and the vinyl visualization app
# Logs are saved for debugging
# =============================================================================

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
LIBRESPOT_LOG="$LOG_DIR/go-librespot.log"
APP_LOG="$LOG_DIR/app.log"

# Create logs directory
mkdir -p "$LOG_DIR"

cd "$SCRIPT_DIR"

echo "=============================================="
echo "  RecordPlayer Launcher"
echo "=============================================="
echo ""

# Stop systemd service if running (we'll run manually for logging)
systemctl --user stop go-librespot 2>/dev/null

# Kill any existing go-librespot processes
pkill -f go-librespot 2>/dev/null
sleep 1

# Start go-librespot with logging
echo "Starting Spotify Connect (go-librespot)..."
echo "Log: $LIBRESPOT_LOG"
/usr/local/bin/go-librespot > "$LIBRESPOT_LOG" 2>&1 &
LIBRESPOT_PID=$!

# Wait for it to start
sleep 3

# Check if it started successfully
if ! kill -0 $LIBRESPOT_PID 2>/dev/null; then
    echo "ERROR: go-librespot failed to start!"
    echo "Check log: $LIBRESPOT_LOG"
    cat "$LIBRESPOT_LOG"
    exit 1
fi

echo "Spotify Connect started (PID: $LIBRESPOT_PID)"
echo ""
echo "Starting Visual App..."
echo "Press ESC to exit."
echo ""

# Start the visual app
# Use PipeWire for audio to allow mixing with Spotify
SDL_AUDIODRIVER=pipewire python3 main.py "$@" 2>&1 | tee "$APP_LOG"

# Cleanup when app exits
echo ""
echo "Shutting down..."
kill $LIBRESPOT_PID 2>/dev/null
pkill -f go-librespot 2>/dev/null

echo "RecordPlayer stopped."
echo ""
echo "Logs saved in: $LOG_DIR/"
echo "  - go-librespot.log (Spotify Connect)"
echo "  - app.log (Visual App)"

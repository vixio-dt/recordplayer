#!/bin/bash
# =============================================================================
# RecordPlayer Launcher Script
# =============================================================================
# Starts the vinyl visualization app
# =============================================================================

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

echo "Starting RecordPlayer..."
echo "Press ESC to exit."
echo ""

# Use PipeWire for audio to allow mixing with Spotify
SDL_AUDIODRIVER=pipewire python3 main.py "$@"


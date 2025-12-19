#!/bin/bash
# Setup script for spotifyd on Raspberry Pi
# Run this script on your Raspberry Pi to replace Raspotify with spotifyd

set -e

echo "=== Stopping and disabling Raspotify ==="
sudo systemctl stop raspotify 2>/dev/null || true
sudo systemctl disable raspotify 2>/dev/null || true

echo "=== Installing spotifyd ==="
sudo apt update
sudo apt install -y spotifyd

echo "=== Creating spotifyd config directory ==="
mkdir -p ~/.config/spotifyd

echo "=== Creating spotifyd configuration ==="
cat > ~/.config/spotifyd/spotifyd.conf << 'EOF'
[global]
# Use PulseAudio backend (compatible with PipeWire)
backend = "pulseaudio"

# Device name shown in Spotify
device_name = "RecordPlayer"

# Audio quality (96, 160, or 320 kbps)
bitrate = 160

# Normalize volume across tracks
volume_normalisation = true

# Device type shown in Spotify
device_type = "speaker"
EOF

echo "=== Enabling spotifyd user service ==="
systemctl --user enable spotifyd
systemctl --user start spotifyd

echo "=== Checking spotifyd status ==="
systemctl --user status spotifyd --no-pager

echo ""
echo "=== Setup complete! ==="
echo "Your Raspberry Pi should now appear as 'RecordPlayer' in Spotify."
echo "Test by opening Spotify on your phone and looking for 'RecordPlayer' in devices."
echo ""
echo "To run the record player app:"
echo "  SDL_AUDIODRIVER=pipewire python3 main.py"


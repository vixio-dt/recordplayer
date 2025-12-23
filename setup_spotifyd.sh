#!/bin/bash
# Setup script for spotifyd on Raspberry Pi
# Run this script on your Raspberry Pi to replace Raspotify with spotifyd

set -e

echo "=== Stopping and disabling Raspotify ==="
sudo systemctl stop raspotify 2>/dev/null || true
sudo systemctl disable raspotify 2>/dev/null || true

echo "=== Downloading spotifyd ARM binary ==="
cd ~
wget -q --show-progress https://github.com/Spotifyd/spotifyd/releases/download/v0.3.5/spotifyd-linux-armhf-slim.tar.gz

echo "=== Installing spotifyd ==="
tar -xzf spotifyd-linux-armhf-slim.tar.gz
sudo mv spotifyd /usr/local/bin/
sudo chmod +x /usr/local/bin/spotifyd
rm spotifyd-linux-armhf-slim.tar.gz

echo "=== Creating spotifyd config ==="
mkdir -p ~/.config/spotifyd
cat > ~/.config/spotifyd/spotifyd.conf << 'EOF'
[global]
# Use ALSA backend
backend = "alsa"

# Device name shown in Spotify
device_name = "RecordPlayer"

# Audio quality (96, 160, or 320 kbps)
bitrate = 160

# Normalize volume across tracks
volume_normalisation = true

# Device type shown in Spotify
device_type = "speaker"
EOF

echo "=== Creating systemd user service ==="
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/spotifyd.service << 'EOF'
[Unit]
Description=Spotifyd
After=network-online.target

[Service]
ExecStart=/usr/local/bin/spotifyd --no-daemon
Restart=always

[Install]
WantedBy=default.target
EOF

echo "=== Enabling spotifyd user service ==="
systemctl --user daemon-reload
systemctl --user enable spotifyd
systemctl --user start spotifyd

echo "=== Enabling auto-start at boot (linger) ==="
sudo loginctl enable-linger $USER

echo "=== Checking spotifyd status ==="
systemctl --user status spotifyd --no-pager || true

echo ""
echo "=== Setup complete! ==="
echo "Your Raspberry Pi should now appear as 'RecordPlayer' in Spotify."
echo "Test by opening Spotify on your phone and looking for 'RecordPlayer' in devices."
echo ""
echo "To run the record player app:"
echo "  python3 main.py"
echo ""
echo "spotifyd will now start automatically at boot."

#!/bin/bash
# =============================================================================
# RecordPlayer V1 Setup Script
# =============================================================================
# This script configures a Raspberry Pi as a multi-source audio receiver with:
# - Spotify Connect (via go-librespot)
# - AirPlay (via shairport-sync)
# - Bluetooth Audio (via bluealsa)
#
# All services will appear as "RecordPlayer" to connecting devices.
# =============================================================================

set -e

DEVICE_NAME="RecordPlayer"
GO_LIBRESPOT_VERSION="v0.6.2"

echo "=============================================="
echo "  RecordPlayer V1 Setup"
echo "=============================================="
echo ""

# -----------------------------------------------------------------------------
# Step 1: Disable old services
# -----------------------------------------------------------------------------
echo "=== Step 1: Disabling old services ==="

# Stop and disable raspotify if present
if systemctl list-units --full -all | grep -q "raspotify.service"; then
    echo "Stopping raspotify..."
    sudo systemctl stop raspotify 2>/dev/null || true
    sudo systemctl disable raspotify 2>/dev/null || true
fi

# Stop and disable spotifyd if present
if systemctl --user list-units --full -all 2>/dev/null | grep -q "spotifyd.service"; then
    echo "Stopping spotifyd..."
    systemctl --user stop spotifyd 2>/dev/null || true
    systemctl --user disable spotifyd 2>/dev/null || true
fi

echo "Old services disabled."
echo ""

# -----------------------------------------------------------------------------
# Step 2: Install dependencies
# -----------------------------------------------------------------------------
echo "=== Step 2: Installing dependencies ==="

sudo apt update
sudo apt install -y \
    shairport-sync \
    bluez \
    bluez-tools \
    python3-pip \
    python3-pygame

# Try to install bluez-alsa (package name varies by distro)
sudo apt install -y bluez-alsa-utils 2>/dev/null || \
sudo apt install -y bluealsa 2>/dev/null || \
echo "Note: Bluetooth audio package not found, Bluetooth may have limited functionality"

# Install Python dependencies
pip3 install --user spotipy requests || true

echo "Dependencies installed."
echo ""

# -----------------------------------------------------------------------------
# Step 3: Install go-librespot (Spotify Connect)
# -----------------------------------------------------------------------------
echo "=== Step 3: Installing go-librespot (Spotify Connect) ==="

cd ~

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    ARCH_NAME="arm64"
elif [ "$ARCH" = "armv7l" ] || [ "$ARCH" = "armhf" ]; then
    ARCH_NAME="armv7"
else
    echo "Unsupported architecture: $ARCH"
    exit 1
fi

# Download go-librespot
DOWNLOAD_URL="https://github.com/devgianlu/go-librespot/releases/download/${GO_LIBRESPOT_VERSION}/go-librespot_linux_${ARCH_NAME}.tar.gz"
echo "Downloading go-librespot for ${ARCH_NAME}..."
wget -q --show-progress "$DOWNLOAD_URL" -O go-librespot.tar.gz

# Extract and install
tar -xzf go-librespot.tar.gz
sudo mv go-librespot /usr/local/bin/
sudo chmod +x /usr/local/bin/go-librespot
rm go-librespot.tar.gz

# Create config directory and file
mkdir -p ~/.config/go-librespot
cat > ~/.config/go-librespot/config.yml << EOF
device_name: "${DEVICE_NAME}"
bitrate: 160
backend: "alsa"
EOF

# Create systemd user service
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/go-librespot.service << EOF
[Unit]
Description=Go Librespot (Spotify Connect)
After=network-online.target sound.target

[Service]
ExecStart=/usr/local/bin/go-librespot
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

# Enable and start service
systemctl --user daemon-reload
systemctl --user enable go-librespot
systemctl --user start go-librespot

echo "go-librespot installed and started."
echo ""

# -----------------------------------------------------------------------------
# Step 4: Configure shairport-sync (AirPlay)
# -----------------------------------------------------------------------------
echo "=== Step 4: Configuring shairport-sync (AirPlay) ==="

# Create shairport-sync config
sudo tee /etc/shairport-sync.conf > /dev/null << EOF
general = {
    name = "${DEVICE_NAME}";
    interpolation = "basic";
    output_backend = "alsa";
};

alsa = {
    output_device = "default";
    mixer_control_name = "PCM";
};
EOF

# Enable and start shairport-sync
sudo systemctl enable shairport-sync
sudo systemctl restart shairport-sync

echo "shairport-sync configured and started."
echo ""

# -----------------------------------------------------------------------------
# Step 5: Configure Bluetooth Audio
# -----------------------------------------------------------------------------
echo "=== Step 5: Configuring Bluetooth Audio ==="

# Set Bluetooth device name
sudo sed -i "s/#Name = .*/Name = ${DEVICE_NAME}/" /etc/bluetooth/main.conf 2>/dev/null || \
    echo "Name = ${DEVICE_NAME}" | sudo tee -a /etc/bluetooth/main.conf

# Enable discoverability and pairing
sudo sed -i "s/#DiscoverableTimeout = .*/DiscoverableTimeout = 0/" /etc/bluetooth/main.conf 2>/dev/null || \
    echo "DiscoverableTimeout = 0" | sudo tee -a /etc/bluetooth/main.conf

sudo sed -i "s/#PairableTimeout = .*/PairableTimeout = 0/" /etc/bluetooth/main.conf 2>/dev/null || \
    echo "PairableTimeout = 0" | sudo tee -a /etc/bluetooth/main.conf

# Enable A2DP Sink profile
sudo sed -i "s/#Class = .*/Class = 0x240414/" /etc/bluetooth/main.conf 2>/dev/null || \
    echo "Class = 0x240414" | sudo tee -a /etc/bluetooth/main.conf

# Create Bluetooth agent service for auto-pairing
sudo tee /etc/systemd/system/bt-agent.service > /dev/null << EOF
[Unit]
Description=Bluetooth Agent
After=bluetooth.service
Requires=bluetooth.service

[Service]
ExecStartPre=/usr/bin/bluetoothctl power on
ExecStartPre=/usr/bin/bluetoothctl discoverable on
ExecStartPre=/usr/bin/bluetoothctl pairable on
ExecStart=/usr/bin/bt-agent -c NoInputNoOutput
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable BlueALSA for Bluetooth audio (if available)
sudo systemctl enable bluealsa 2>/dev/null || \
sudo systemctl enable bluez-alsa 2>/dev/null || true
sudo systemctl restart bluealsa 2>/dev/null || \
sudo systemctl restart bluez-alsa 2>/dev/null || true

# Enable Bluetooth agent
sudo systemctl daemon-reload
sudo systemctl enable bt-agent
sudo systemctl restart bluetooth
sudo systemctl start bt-agent 2>/dev/null || true

echo "Bluetooth configured."
echo ""

# -----------------------------------------------------------------------------
# Step 6: Enable auto-start at boot (linger)
# -----------------------------------------------------------------------------
echo "=== Step 6: Enabling auto-start at boot ==="

sudo loginctl enable-linger $USER

echo "User services will now start at boot."
echo ""

# -----------------------------------------------------------------------------
# Step 7: Verify services
# -----------------------------------------------------------------------------
echo "=== Step 7: Verifying services ==="
echo ""

echo "Spotify Connect (go-librespot):"
systemctl --user status go-librespot --no-pager | head -5 || echo "  Not running (check logs)"
echo ""

echo "AirPlay (shairport-sync):"
sudo systemctl status shairport-sync --no-pager | head -5 || echo "  Not running (check logs)"
echo ""

echo "Bluetooth:"
sudo systemctl status bluetooth --no-pager | head -5 || echo "  Not running (check logs)"
echo ""

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo "=============================================="
echo "  Setup Complete!"
echo "=============================================="
echo ""
echo "Your Raspberry Pi is now configured as '${DEVICE_NAME}'."
echo ""
echo "Connect via:"
echo "  - Spotify: Select '${DEVICE_NAME}' in your Spotify app"
echo "  - AirPlay: Select '${DEVICE_NAME}' in iPhone Control Center"
echo "  - Bluetooth: Pair with '${DEVICE_NAME}' in Bluetooth settings"
echo ""
echo "To start the vinyl visualization:"
echo "  cd ~/Record-Player && python3 main.py"
echo ""
echo "Or use the launcher script:"
echo "  ./start_recordplayer.sh"
echo ""


# Record-Player

## Overview

This project provides a fun and interactive vinyl record player interface for Spotify. Spin the record to seek through songs, scratch for sound effects, and control playback with a tap-to-reveal control panel.

The Raspberry Pi also acts as a **universal audio receiver** supporting:
- **Spotify Connect** - Select "RecordPlayer" in any Spotify app
- **AirPlay** - Stream from iPhone/iPad/Mac
- **Bluetooth** - Pair any Bluetooth device

## Physical Build Manual

For detailed instructions on assembling the physical record player enclosure, wiring diagrams, and parts list, please refer to:

- Concept Bytes: https://concept-bytes.com (Search for "Spotify Record Player")
- Patreon: https://patreon.com/ConceptBytes

## Features

- **Dynamic vinyl with album art**: The vinyl record displays the current album cover in its center (Spotify only)
- **Scratch-seeking**: Drag the vinyl to seek through the song while playing scratch sound effects (Spotify only)
- **Tap-to-show controls**: Tap the album art in the center to reveal/hide playback controls
- **Auto-hiding controls**: Controls automatically hide after 5 seconds
- **Real-time sync**: Displays currently playing track, artist, and progress bar
- **Playback controls**: Play/pause, skip forward, skip back
- **Multi-source audio**: Receive audio from Spotify, AirPlay, or Bluetooth

## Requirements

- Raspberry Pi (tested on Pi 4/5, 64-bit OS)
- Python 3.7+
- Spotify Premium account (for Spotify Connect features)
- A registered Spotify application (Client ID and Client Secret)

## Quick Setup (Raspberry Pi)

### 1. Clone the repository

```bash
cd ~
git clone https://github.com/vixio-dt/recordplayer.git Record-Player
cd Record-Player
```

### 2. Run the V1 setup script

This installs and configures all audio services (Spotify Connect, AirPlay, Bluetooth):

```bash
chmod +x setup_v1.sh
./setup_v1.sh
```

### 3. Configure Spotify API credentials

Create the `env.local` file:

```bash
nano env.local
```

Add your credentials:

```bash
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_USERNAME=your_spotify_username
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

To get these credentials:
1. Go to https://developer.spotify.com/dashboard
2. Create a new app
3. Add `http://localhost:8888/callback` as a Redirect URI
4. Copy the Client ID and Client Secret

### 4. Start the vinyl visualization

```bash
./start_recordplayer.sh
```

Or with windowed mode for testing:

```bash
python3 main.py --windowed
```

Press **ESC** to exit.

## Connecting to RecordPlayer

After setup, your Raspberry Pi will appear as **"RecordPlayer"** on all these services:

### Spotify Connect
1. Open Spotify on your phone/tablet/computer
2. Play any song
3. Tap the speaker/device icon
4. Select "RecordPlayer"

### AirPlay (iPhone/iPad/Mac)
1. Open Control Center
2. Tap the AirPlay icon (or long-press the music controls)
3. Select "RecordPlayer"

### Bluetooth
1. Open your phone's Bluetooth settings
2. Scan for devices
3. Pair with "RecordPlayer"

## Controls

- **Tap the center (album art)**: Show/hide playback controls
- **Drag anywhere on the vinyl**: Seek through the song (with scratch sound effects) - Spotify only
- **Playback buttons** (when visible):
  - ◄ Previous track
  - ▶/⏸ Play/Pause
  - ► Next track

## What Works with Each Source

| Feature | Spotify | AirPlay | Bluetooth |
|---------|---------|---------|-----------|
| Audio Playback | ✅ | ✅ | ✅ |
| Vinyl Spinning | ✅ | ✅ | ✅ |
| Album Art | ✅ | ❌ | ❌ |
| Scratch/Seek | ✅ | ❌ | ❌ |
| Playback Controls | ✅ | ❌ | ❌ |

## Services

The setup script installs these background services:

| Service | Purpose | Check Status |
|---------|---------|--------------|
| go-librespot | Spotify Connect | `systemctl --user status go-librespot` |
| shairport-sync | AirPlay | `sudo systemctl status shairport-sync` |
| bluetooth | Bluetooth Audio | `sudo systemctl status bluetooth` |

All services start automatically at boot.

## Troubleshooting

### Spotify Connect not showing up
```bash
systemctl --user restart go-librespot
systemctl --user status go-librespot
```

### AirPlay not showing up
```bash
sudo systemctl restart shairport-sync
sudo systemctl status shairport-sync
```

### No audio output
```bash
# List audio devices
aplay -l

# Test audio
speaker-test -t wav -c 2
```

### Check service logs
```bash
# Spotify logs
journalctl --user -u go-librespot -f

# AirPlay logs
sudo journalctl -u shairport-sync -f
```

## Manual Installation

If you prefer to set things up manually, see the individual setup scripts:
- `setup_v1.sh` - Full setup (recommended)
- `setup_spotifyd.sh` - Legacy spotifyd setup (deprecated)

## Acknowledgments

Built by Concept Bytes. Learn more at https://concept-bytes.com or support on Patreon at https://patreon.com/ConceptBytes.

# Record-Player

## Overview

This project provides a fun and interactive vinyl record player interface for Spotify. Spin the record to seek through songs, scratch for sound effects, and control playback with a tap-to-reveal control panel.

## Physical Build Manual

For detailed instructions on assembling the physical record player enclosure, wiring diagrams, and parts list, please refer to:

- Concept Bytes: https://concept-bytes.com (Search for "Spotify Record Player")
- Patreon: https://patreon.com/ConceptBytes

## Features

- **Dynamic vinyl with album art**: The vinyl record displays the current album cover in its center
- **Scratch-seeking**: Drag the vinyl to seek through the song while playing scratch sound effects
- **Tap-to-show controls**: Tap the album art in the center to reveal/hide playback controls
- **Auto-hiding controls**: Controls automatically hide after 5 seconds
- **Real-time sync**: Displays currently playing track, artist, and progress bar
- **Playback controls**: Play/pause, skip forward, skip back

## Requirements

- Python 3.7+
- pip
- Spotify Premium account
- A registered Spotify application (Client ID and Client Secret)

Python dependencies:

```bash
pip install pygame requests spotipy
```

## Configuration

This application uses environment variables for Spotify authentication and settings.
It automatically loads values from a `.env` file in the project root (if present).
Required variables:

- `SPOTIFY_CLIENT_ID`: Your Spotify application Client ID.
- `SPOTIFY_CLIENT_SECRET`: Your Spotify application Client Secret.
- `SPOTIFY_USERNAME`: Your Spotify username.

Optional variables (with defaults):

- `SPOTIFY_REDIRECT_URI` (default: `http://localhost:8888/callback`)
- `SPOTIFY_SCOPE` (default: `user-read-currently-playing`)

To configure, create a `.env` file in the project root with:

```bash
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_USERNAME=your_spotify_username
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

On first run, if any required variables are missing, the app will prompt you to enter them,
and save them to `.env` for future use.

## Usage

Run the application from the command line:

- Fullscreen mode (default):

  ```bash
  python main.py
  ```

- Windowed mode:

  ```bash
  python main.py --windowed
  ```

Press **ESC** to exit.

## Controls

- **Tap the center (album art)**: Show/hide playback controls
- **Drag anywhere on the vinyl**: Seek through the song (with scratch sound effects)
- **Playback buttons** (when visible):
  - ◄ Previous track
  - ▶/⏸ Play/Pause
  - ► Next track

## Raspberry Pi Setup (spotifyd)

This project uses **spotifyd** as the Spotify Connect daemon. It runs as a user service and works properly with PipeWire audio.

### Quick Setup

Run the included setup script:

```bash
chmod +x setup_spotifyd.sh
./setup_spotifyd.sh
```

### Manual Setup

1. Disable Raspotify (if previously installed):

   ```bash
   sudo systemctl stop raspotify
   sudo systemctl disable raspotify
   ```

2. Install spotifyd:

   ```bash
   sudo apt update
   sudo apt install spotifyd
   ```

3. Create the configuration file:

   ```bash
   mkdir -p ~/.config/spotifyd
   nano ~/.config/spotifyd/spotifyd.conf
   ```

   Add this content:

   ```toml
   [global]
   backend = "pulseaudio"
   device_name = "RecordPlayer"
   bitrate = 160
   volume_normalisation = true
   device_type = "speaker"
   ```

4. Enable and start spotifyd:

   ```bash
   systemctl --user enable spotifyd
   systemctl --user start spotifyd
   ```

5. Run the record player with PipeWire audio:

   ```bash
   SDL_AUDIODRIVER=pipewire python3 main.py
   ```

Your Raspberry Pi will appear as "RecordPlayer" in Spotify.

## Acknowledgments

Built by Concept Bytes. Learn more at https://concept-bytes.com or support on Patreon at https://patreon.com/ConceptBytes.

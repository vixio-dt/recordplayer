import os
from pathlib import Path
import json
import spotipy
import webbrowser
from spotipy.oauth2 import SpotifyOAuth
import tkinter as tk
from tkinter import simpledialog

# Load environment variables from a .env file if present
def load_env_file(env_path='.env'):
    """
    Load environment variables from a .env file if present.
    Searches first in the current working directory, then beside this script.
    """
    cwd_path = Path(env_path)
    script_path = Path(__file__).resolve().parent / env_path
    if cwd_path.is_file():
        env_file = cwd_path
    elif script_path.is_file():
        env_file = script_path
    else:
        return
    # Read and parse lines
    content = env_file.read_text()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, val = line.split('=', 1)
        key = key.strip()
        # Strip quotes from value
        val = val.strip().strip('"').strip("'")
        # Only set if not already in environment
        if key and val and key not in os.environ:
            os.environ[key] = val

load_env_file()

# Read credentials from environment variables
clientID = os.getenv("SPOTIFY_CLIENT_ID")
clientSecret = os.getenv("SPOTIFY_CLIENT_SECRET")
username = os.getenv("SPOTIFY_USERNAME")
# Optional settings
redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
scope = os.getenv("SPOTIFY_SCOPE", "user-read-currently-playing")

# Prompt for missing credentials
if not all([clientID, clientSecret, username]):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    if not clientID:
        clientID = simpledialog.askstring("Spotify Credentials", "Enter your Spotify Client ID:", parent=root)
    if not clientSecret:
        clientSecret = simpledialog.askstring("Spotify Credentials", "Enter your Spotify Client Secret:", parent=root)
    if not username:
        username = simpledialog.askstring("Spotify Credentials", "Enter your Spotify Username:", parent=root)
    root.destroy()
    # Ensure all credentials are provided
    if not all([clientID, clientSecret, username]):
        raise RuntimeError("Spotify credentials are required to run this application.")
    # Persist to environment
    os.environ["SPOTIFY_CLIENT_ID"] = clientID
    os.environ["SPOTIFY_CLIENT_SECRET"] = clientSecret
    os.environ["SPOTIFY_USERNAME"] = username
    os.environ["SPOTIFY_REDIRECT_URI"] = redirect_uri
    # Save to .env for future runs
    try:
        env_lines = [
            f"SPOTIFY_CLIENT_ID={clientID}",
            f"SPOTIFY_CLIENT_SECRET={clientSecret}",
            f"SPOTIFY_USERNAME={username}",
            f"SPOTIFY_REDIRECT_URI={redirect_uri}",
        ]
        Path('.env').write_text("\n".join(env_lines) + "\n")
    except Exception:
        pass



def get_current_playing_info():
    global spotify
    
    current_track = spotify.current_user_playing_track()
    if current_track is None:
        return None  # Return None if no track is playing

    # Extracting necessary details
    artist_name = current_track['item']['artists'][0]['name']
    album_name = current_track['item']['album']['name']
    album_cover_url = current_track['item']['album']['images'][0]['url']
    track_title = current_track['item']['name']  # Get the track name

    return {
        "artist": artist_name,
        "album": album_name,
        "album_cover": album_cover_url,
        "title": track_title
    }


def spotify_authenticate(client_id, client_secret, redirect_uri, username):
    # OAuth with the required scopes for playback control and reading currently playing track
    scope = "user-read-currently-playing user-modify-playback-state"
    auth_manager = SpotifyOAuth(client_id, client_secret, redirect_uri, scope=scope, username=username)
    return spotipy.Spotify(auth_manager=auth_manager)


spotify = spotify_authenticate(clientID, clientSecret, redirect_uri, username)

def start_music():
    global spotify
    # Start or resume playback on the user's active device
    try:
        spotify.start_playback()
    except spotipy.SpotifyException as e:
        return f"Error in starting playback: {str(e)}"

def stop_music():
    global spotify

    # Pause playback on the user's active device
    try:
        spotify.pause_playback()
    except spotipy.SpotifyException as e:
        return f"Error in stopping playback: {str(e)}"

def skip_to_next():
    global spotify
    # Skip to the next track in the user's queue
    try:
        spotify.next_track()
        return "Skipped to next track."
    except spotipy.SpotifyException as e:
        return f"Error in skipping to next track: {str(e)}"

def skip_to_previous():
    global spotify
    # Skip to the previous track in the user's queue
    try:
        spotify.previous_track()
        return "Skipped to previous track."
    except spotipy.SpotifyException as e:
        return f"Error in skipping to previous track: {str(e)}"

# print(get_current_playing_info(username, clientID, clientSecret, redirect_uri))

# spotify = spotify_authenticate(clientID, clientSecret, redirect_uri, username)
# print(skip_to_previous(spotify))   # Stop music

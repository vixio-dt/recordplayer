"""
go-librespot API Client

This module provides functions to get track information from go-librespot's API server.
This allows the record player to display album art for any user, not just the account owner.
"""

import requests
import time

# go-librespot API configuration
LIBRESPOT_API_HOST = "localhost"
LIBRESPOT_API_PORT = 3678
LIBRESPOT_API_URL = f"http://{LIBRESPOT_API_HOST}:{LIBRESPOT_API_PORT}"

# Cache to avoid hammering the API
_cache = {
    "last_fetch": 0,
    "data": None,
    "cache_duration": 1.0  # seconds
}


def get_player_state():
    """
    Get the current player state from go-librespot API.
    
    Returns:
        dict with player state or None if unavailable
    """
    now = time.time()
    
    # Return cached data if fresh enough
    if _cache["data"] is not None and (now - _cache["last_fetch"]) < _cache["cache_duration"]:
        return _cache["data"]
    
    try:
        response = requests.get(f"{LIBRESPOT_API_URL}/player", timeout=1.0)
        if response.status_code == 200:
            data = response.json()
            _cache["data"] = data
            _cache["last_fetch"] = now
            return data
    except requests.exceptions.RequestException:
        pass
    
    return None


def get_current_track_info():
    """
    Get current track information from go-librespot.
    
    Returns:
        dict with track info or None if nothing playing:
        {
            "title": str,
            "artist": str,
            "album": str,
            "album_cover": str (URL),
            "duration_ms": int,
            "position_ms": int,
            "is_playing": bool
        }
    """
    state = get_player_state()
    
    if state is None:
        return None
    
    # Extract track info from go-librespot response
    # go-librespot API structure may vary, adapt as needed
    track = state.get("track")
    if track is None:
        return None
    
    # Get album art URL - go-librespot provides cover art info
    album_cover = None
    if "album" in track and "images" in track["album"]:
        images = track["album"]["images"]
        if images:
            # Get the largest image
            album_cover = images[0].get("url")
    
    # Alternative: go-librespot might provide cover_url directly
    if album_cover is None:
        album_cover = track.get("cover_url") or state.get("cover_url")
    
    return {
        "title": track.get("name", "Unknown"),
        "artist": ", ".join([a.get("name", "") for a in track.get("artists", [])]) or "Unknown Artist",
        "album": track.get("album", {}).get("name", "Unknown Album"),
        "album_cover": album_cover,
        "duration_ms": track.get("duration_ms", 0),
        "position_ms": state.get("position_ms", 0),
        "is_playing": state.get("is_playing", False)
    }


def is_api_available():
    """
    Check if go-librespot API is available.
    
    Returns:
        bool
    """
    try:
        response = requests.get(f"{LIBRESPOT_API_URL}/player", timeout=0.5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def skip_next():
    """Skip to next track via go-librespot API."""
    try:
        response = requests.post(f"{LIBRESPOT_API_URL}/player/next", timeout=1.0)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def skip_previous():
    """Skip to previous track via go-librespot API."""
    try:
        response = requests.post(f"{LIBRESPOT_API_URL}/player/prev", timeout=1.0)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def play():
    """Resume playback via go-librespot API."""
    try:
        response = requests.post(f"{LIBRESPOT_API_URL}/player/play", timeout=1.0)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def pause():
    """Pause playback via go-librespot API."""
    try:
        response = requests.post(f"{LIBRESPOT_API_URL}/player/pause", timeout=1.0)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def seek(position_ms):
    """
    Seek to position in current track via go-librespot API.
    
    Args:
        position_ms: Position in milliseconds
    """
    try:
        response = requests.post(
            f"{LIBRESPOT_API_URL}/player/seek",
            json={"position_ms": position_ms},
            timeout=1.0
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


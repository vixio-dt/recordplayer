"""
go-librespot API Client

NOTE: go-librespot v0.6.2 uses WebSocket for events, not REST API.
The REST endpoints return empty {} responses.
This module is a placeholder for future WebSocket implementation.
For now, it returns False/None to fall back to Spotify API.
"""


def get_current_track_info():
    """
    Get current track information from go-librespot.
    Currently not implemented - go-librespot requires WebSocket.
    Returns None to fall back to Spotify API.
    """
    return None


def is_api_available():
    """Check if go-librespot API is available."""
    return False


def skip_next():
    """Skip to next track - not implemented, returns False to use Spotify API."""
    return False


def skip_previous():
    """Skip to previous track - not implemented, returns False to use Spotify API."""
    return False


def play():
    """Resume playback - not implemented, returns False to use Spotify API."""
    return False


def pause():
    """Pause playback - not implemented, returns False to use Spotify API."""
    return False


def seek(position_ms):
    """Seek to position - not implemented, returns False to use Spotify API."""
    return False


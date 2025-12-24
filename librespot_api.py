"""
go-librespot API Client (WebSocket + REST)

This module interfaces with go-librespot v0.6.2+.
- Uses WebSockets for real-time state updates (track info, playback status).
- Uses REST API for controls (play, pause, skip, seek).

This enables "Universal Support" - showing album art and controls for ANY connected user.
"""

import json
import threading
import time
import requests
import sys
import logging

try:
    import websocket
except ImportError:
    print("Error: websocket-client not installed. Please run: pip install websocket-client", file=sys.stderr)
    websocket = None

# Configuration
LIBRESPOT_API_URL = "http://localhost:3678"
LIBRESPOT_WS_URL = "ws://localhost:3678/events"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("librespot_api")

class LibrespotClient:
    def __init__(self):
        self.track_info = None
        self.is_playing = False
        self.position_ms = 0
        self.duration_ms = 0
        self.last_update_time = time.time()
        self.connected = False
        self._lock = threading.Lock()
        
        # Start WebSocket thread if library is available
        if websocket:
            self.ws_thread = threading.Thread(target=self._run_ws_loop, daemon=True)
            self.ws_thread.start()
        else:
            logger.error("WebSocket library missing - functionality will be limited.")

    def _run_ws_loop(self):
        while True:
            try:
                # Enable trace for debugging if needed
                # websocket.enableTrace(True)
                
                ws = websocket.WebSocketApp(
                    LIBRESPOT_WS_URL,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                
                logger.info(f"Connecting to go-librespot events at {LIBRESPOT_WS_URL}...")
                ws.run_forever()
                
                # If we get here, connection closed
                logger.info("WebSocket connection closed. Reconnecting in 5s...")
                time.sleep(5)
            except Exception as e:
                logger.error(f"WebSocket loop error: {e}")
                time.sleep(5)

    def _on_open(self, ws):
        logger.info("Connected to go-librespot events.")
        self.connected = True
        
    def _on_message(self, ws, message):
        try:
            event = json.loads(message)
            # logger.debug(f"Event received: {event}")
            self._handle_event(event)
        except json.JSONDecodeError:
            logger.error("Failed to parse WebSocket message")

    def _on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        logger.info("WebSocket closed.")
        self.connected = False

    def _handle_event(self, event):
        """Update internal state based on event data."""
        # DEBUG: Print raw event to see what we are getting
        logger.info(f"WS Event: {json.dumps(event)}")
        
        event_type = event.get("event")
        
        with self._lock:
            # Handle different event types from go-librespot
            
            if event_type == "metadata_available" or event_type == "track_changed" or event_type == "context_changed":
                # Track info update
                track = event.get("track", {})
                if track:
                    self.track_info = {
                        "artist": ", ".join([a.get("name", "") for a in track.get("artists", [])]) if track.get("artists") else "Unknown Artist",
                        "album": track.get("album", {}).get("name", "Unknown Album"),
                        "album_cover": track.get("album", {}).get("coverUrl") or track.get("coverUrl"),
                        "title": track.get("name", "Unknown Title")
                    }
                    self.duration_ms = track.get("durationMs", 0)
            
            elif event_type == "playing" or event_type == "playback_resumed" or event_type == "progress":
                self.is_playing = True
                self.last_update_time = time.time()
                # If position is provided in event
                if "positionMs" in event:
                    self.position_ms = event["positionMs"]

            elif event_type == "paused" or event_type == "playback_paused":
                self.is_playing = False
                if "positionMs" in event:
                    self.position_ms = event["positionMs"]
                
            elif event_type == "stopped":
                self.is_playing = False
                self.position_ms = 0
                
            elif event_type == "seeked":
                if "positionMs" in event:
                    self.position_ms = event["positionMs"]
                    self.last_update_time = time.time()
            
            # Catch-all for position updates if they exist in ANY event
            if "positionMs" in event:
                self.position_ms = event["positionMs"]
                if self.is_playing:
                    self.last_update_time = time.time()

    def get_current_track_info(self):
        with self._lock:
            if not self.connected or not self.track_info:
                return None
            return self.track_info.copy()

    def get_playback_state(self):
        with self._lock:
            if not self.connected:
                return None
            
            current_pos = self.position_ms
            if self.is_playing:
                # Extrapolate position based on time elapsed since last update
                elapsed = (time.time() - self.last_update_time) * 1000
                current_pos += elapsed
                if self.duration_ms > 0:
                    current_pos = min(current_pos, self.duration_ms)
            
            return {
                "progress_ms": int(current_pos),
                "duration_ms": self.duration_ms,
                "is_playing": self.is_playing
            }

    # --- REST API Controls ---
    # These use the HTTP API which listens for commands even if events are WS
    
    def _call_api(self, endpoint, method="POST", data=None):
        try:
            url = f"{LIBRESPOT_API_URL}{endpoint}"
            if method == "POST":
                response = requests.post(url, json=data, timeout=1)
            elif method == "PUT":
                response = requests.put(url, json=data, timeout=1)
            
            return response.status_code >= 200 and response.status_code < 300
        except requests.exceptions.RequestException:
            return False

    def play(self):
        return self._call_api("/player/play")

    def pause(self):
        return self._call_api("/player/pause")

    def skip_next(self):
        return self._call_api("/player/next")

    def skip_previous(self):
        return self._call_api("/player/prev") # or /previous

    def seek(self, position_ms):
        return self._call_api("/player/seek", data={"positionMs": position_ms})


# Singleton instance
client = LibrespotClient()

# --- Module-level exports matching main.py expectations ---

def get_current_track_info():
    return client.get_current_track_info()

def get_playback_state():
    return client.get_playback_state()

def start_music():
    return client.play()

def play():
    return client.play()

def stop_music():
    return client.pause()

def pause():
    return client.pause()

def skip_to_next():
    return client.skip_next()

def skip_next():
    return client.skip_next()

def skip_to_previous():
    return client.skip_previous()

def skip_previous():
    return client.skip_previous()

def seek_position(position_ms):
    return client.seek(position_ms)

def seek(position_ms):
    return client.seek(position_ms)

def is_active():
    """Check if we have an active connection and track."""
    info = client.get_current_track_info()
    return info is not None

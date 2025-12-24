import websocket
import json
import threading
import time
import sys

# Configuration
WS_URL = "ws://localhost:3678/events"

def on_message(ws, message):
    print("\n--- RECEIVED EVENT ---")
    try:
        data = json.loads(message)
        print(json.dumps(data, indent=2))
    except:
        print(message)
    print("----------------------\n")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("### Connection Closed ###")

def on_open(ws):
    print("### Connected to go-librespot API ###")
    print("Waiting for events... (Play/Pause/Seek on Spotify to see data)")

if __name__ == "__main__":
    # Check if websocket-client is installed
    try:
        import websocket
    except ImportError:
        print("Error: websocket-client library not found.")
        print("Run: pip3 install websocket-client")
        sys.exit(1)

    print(f"Connecting to {WS_URL}...")
    
    # Enable debug traces
    # websocket.enableTrace(True)
    
    ws = websocket.WebSocketApp(WS_URL,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)

    try:
        ws.run_forever()
    except KeyboardInterrupt:
        print("\nExiting...")


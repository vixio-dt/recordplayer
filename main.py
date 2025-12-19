import pygame
import sys
import requests
import time
import math
import threading
import random
from io import BytesIO
from spot import (
    get_current_playing_info, 
    start_music, 
    stop_music, 
    skip_to_next, 
    skip_to_previous,
    get_playback_state,
    seek_position
)
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# -------------------------------
# Vinyl Drawing Functions
# -------------------------------
def create_vinyl_surface(size=1080, album_img=None, album_size=300):
    """
    Create a vinyl record surface with optional album art in the center.
    
    Args:
        size: Size of the vinyl in pixels
        album_img: Pygame surface of album art (or None for black center)
        album_size: Size to scale album art to
    
    Returns:
        Pygame surface with vinyl record
    """
    # Create surface with alpha channel
    vinyl = pygame.Surface((size, size), pygame.SRCALPHA)
    
    center = size // 2
    
    # Draw the main black vinyl disc
    pygame.draw.circle(vinyl, (20, 20, 20), (center, center), size // 2)
    
    # Draw subtle groove rings (vinyl texture)
    groove_color = (35, 35, 35)
    for r in range(album_size // 2 + 30, size // 2 - 10, 8):
        pygame.draw.circle(vinyl, groove_color, (center, center), r, 1)
    
    # Draw the center label area (slightly lighter)
    label_radius = album_size // 2 + 20
    pygame.draw.circle(vinyl, (40, 40, 40), (center, center), label_radius)
    
    # Draw album art in center or black circle if none
    if album_img:
        # Scale album art to desired size
        scaled_album = pygame.transform.scale(album_img, (album_size, album_size))
        # Create circular mask for album art
        album_pos = (center - album_size // 2, center - album_size // 2)
        
        # Create a circular surface for the album
        circle_surface = pygame.Surface((album_size, album_size), pygame.SRCALPHA)
        pygame.draw.circle(circle_surface, (255, 255, 255, 255), 
                          (album_size // 2, album_size // 2), album_size // 2)
        
        # Apply circular mask to album art
        masked_album = pygame.Surface((album_size, album_size), pygame.SRCALPHA)
        masked_album.blit(scaled_album, (0, 0))
        masked_album.blit(circle_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        vinyl.blit(masked_album, album_pos)
    else:
        # Draw black center when nothing is playing
        pygame.draw.circle(vinyl, (0, 0, 0), (center, center), album_size // 2)
    
    # Draw spindle hole in center
    pygame.draw.circle(vinyl, (60, 60, 60), (center, center), 8)
    pygame.draw.circle(vinyl, (30, 30, 30), (center, center), 5)
    
    return vinyl


def calculate_rotation_delta(current_pos, last_pos, center):
    """
    Calculate the rotation angle delta based on mouse movement around center.
    
    Returns rotation in degrees (positive = clockwise, negative = counter-clockwise)
    """
    # Calculate angles from center to each position
    last_angle = math.atan2(last_pos[1] - center[1], last_pos[0] - center[0])
    current_angle = math.atan2(current_pos[1] - center[1], current_pos[0] - center[0])
    
    # Calculate delta in radians
    delta = current_angle - last_angle
    
    # Normalize to -pi to pi range
    while delta > math.pi:
        delta -= 2 * math.pi
    while delta < -math.pi:
        delta += 2 * math.pi
    
    # Convert to degrees
    return math.degrees(delta)


def run(windowed=False):
    # Initialize Pygame and audio mixer
    pygame.init()
    pygame.mixer.init()
    flags = 0 if windowed else pygame.FULLSCREEN
    screen = pygame.display.set_mode((1080, 1080), flags)
    pygame.display.set_caption("Spotify Record Player")
    # Hide mouse cursor (useful on touchscreens)
    pygame.mouse.set_visible(False)

    # -------------------------------
    # Load UI assets
    # -------------------------------
    icons_dir = BASE_DIR / 'spotify'
    play_btn  = pygame.image.load(str(icons_dir / 'play.png'))
    pause_btn = pygame.image.load(str(icons_dir / 'pause.png'))
    skip_btn  = pygame.image.load(str(icons_dir / 'skip.png'))
    prev_btn  = pygame.image.load(str(icons_dir / 'previous.png'))
    banner    = pygame.image.load(str(icons_dir / 'banner.png'))

    font = pygame.font.Font(None, 40)
    small_font = pygame.font.Font(None, 28)

    # -------------------------------
    # Load scratch sound effects
    # -------------------------------
    sfx_dir = BASE_DIR / 'sfx'
    sfx_paths = [p for p in sfx_dir.iterdir() if p.is_file() and p.suffix.lower() == '.wav']
    scratch_sounds = [pygame.mixer.Sound(str(path)) for path in sfx_paths]

    # -------------------------------
    # Constants
    # -------------------------------
    SCREEN_SIZE = 1080
    CENTER = (SCREEN_SIZE // 2, SCREEN_SIZE // 2)
    VINYL_SIZE = int(SCREEN_SIZE * 1.1)  # Slightly larger for rotation overflow
    ALBUM_ART_SIZE = 300  # Size of album art in vinyl center
    CENTER_TAP_RADIUS = ALBUM_ART_SIZE // 2  # Tap area to show controls
    CONTROLS_AUTO_HIDE_SECONDS = 5
    SEEK_SENSITIVITY = 100  # ms per degree of rotation (360° = 36 seconds)

    # -------------------------------
    # State variables
    # -------------------------------
    angle = 0
    angle_speed = -0.3  # Slower, more realistic rotation
    is_playing = False
    dragging = False
    last_mouse_pos = None
    details = None
    album_img_raw = None  # Raw album image from Spotify
    vinyl_surface = create_vinyl_surface(VINYL_SIZE, None, ALBUM_ART_SIZE)
    
    # Controls visibility state
    controls_visible = False
    controls_show_time = 0
    
    # Playback state for seeking
    current_position_ms = 0
    track_duration_ms = 0
    last_playback_update = 0
    
    # Scratch state
    accumulated_rotation = 0
    last_scratch_sound_time = 0
    SCRATCH_SOUND_COOLDOWN = 0.15  # Seconds between scratch sounds

    # -------------------------------
    # Helper functions
    # -------------------------------
    def update_details():
        nonlocal details, album_img_raw, vinyl_surface, is_playing
        try:
            new_details = get_current_playing_info()
        except Exception as e:
            print(f"Error fetching current playing info: {e}", file=sys.stderr)
            return
        
        if new_details:
            # Check if track changed
            track_changed = details is None or details.get("title") != new_details.get("title")
            details = new_details
            
            if track_changed:
                try:
                    r = requests.get(details["album_cover"])
                    img = pygame.image.load(BytesIO(r.content))
                    album_img_raw = img
                    # Recreate vinyl with new album art
                    vinyl_surface = create_vinyl_surface(VINYL_SIZE, album_img_raw, ALBUM_ART_SIZE)
                except Exception as e:
                    print(f"Error loading album cover: {e}", file=sys.stderr)
        else:
            # Nothing playing
            details = None
            album_img_raw = None
            vinyl_surface = create_vinyl_surface(VINYL_SIZE, None, ALBUM_ART_SIZE)
            is_playing = False

    def update_playback_state():
        nonlocal current_position_ms, track_duration_ms, is_playing, last_playback_update
        try:
            state = get_playback_state()
            if state:
                current_position_ms = state["progress_ms"]
                track_duration_ms = state["duration_ms"]
                is_playing = state["is_playing"]
                last_playback_update = time.time()
        except Exception as e:
            print(f"Error updating playback state: {e}", file=sys.stderr)

    # Initial fetch
    update_details()
    update_playback_state()

    # Background thread to periodically update details
    def details_thread():
        while True:
            time.sleep(3)
            try:
                update_details()
                update_playback_state()
            except Exception as e:
                print(f"Error in details_thread: {e}", file=sys.stderr)

    threading.Thread(target=details_thread, daemon=True).start()

    # Click timing for tap detection
    click_start_time = None
    click_start_pos = None
    TAP_MAX_DURATION = 0.3  # Max seconds for a tap
    TAP_MAX_DISTANCE = 20   # Max pixels moved for a tap

    # -------------------------------
    # Main loop
    # -------------------------------
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Exit on ESC
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

            # Mouse/touch down
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                click_start_time = time.time()
                click_start_pos = event.pos
                
                # Check if click is on controls (if visible)
                if controls_visible:
                    # Calculate control positions
                    banner_x = (SCREEN_SIZE - banner.get_width()) // 2
                    banner_y = 800
                    
                    prev_w, prev_h = prev_btn.get_width(), prev_btn.get_height()
                    pause_w, pause_h = pause_btn.get_width(), pause_btn.get_height()
                    skip_w, skip_h = skip_btn.get_width(), skip_btn.get_height()
                    
                    # Center the control buttons
                    total_width = prev_w + pause_w + skip_w + 100  # 50px gaps
                    start_x = (SCREEN_SIZE - total_width) // 2
                    control_y = banner_y + banner.get_height() // 2
                    
                    prev_x = start_x
                    prev_y = control_y - prev_h // 2
                    pause_x = prev_x + prev_w + 50
                    pause_y = control_y - pause_h // 2
                    skip_x = pause_x + pause_w + 50
                    skip_y = control_y - skip_h // 2

                    # Previous track
                    if prev_x <= mx <= prev_x + prev_w and prev_y <= my <= prev_y + prev_h:
                        try:
                            skip_to_previous()
                            threading.Thread(target=update_details, daemon=True).start()
                        except Exception as e:
                            print(f"Error skipping to previous: {e}", file=sys.stderr)
                        continue

                    # Play/pause toggle
                    elif pause_x <= mx <= pause_x + pause_w and pause_y <= my <= pause_y + pause_h:
                        if is_playing:
                            try:
                                stop_music()
                                is_playing = False
                            except Exception as e:
                                print(f"Error stopping music: {e}", file=sys.stderr)
                        else:
                            try:
                                start_music()
                                is_playing = True
                            except Exception as e:
                                print(f"Error starting music: {e}", file=sys.stderr)
                        continue

                    # Next track
                    elif skip_x <= mx <= skip_x + skip_w and skip_y <= my <= skip_y + skip_h:
                        try:
                            skip_to_next()
                            threading.Thread(target=update_details, daemon=True).start()
                        except Exception as e:
                            print(f"Error skipping to next: {e}", file=sys.stderr)
                        continue

                # Check if click is on the vinyl record
                dist_from_center = math.hypot(mx - CENTER[0], my - CENTER[1])
                if dist_from_center <= VINYL_SIZE // 2:
                    dragging = True
                    last_mouse_pos = event.pos
                    accumulated_rotation = 0

            # Mouse/touch up
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mx, my = event.pos
                
                # Check if this was a tap (short duration, small movement)
                if click_start_time and click_start_pos:
                    duration = time.time() - click_start_time
                    distance = math.hypot(mx - click_start_pos[0], my - click_start_pos[1])
                    
                    if duration < TAP_MAX_DURATION and distance < TAP_MAX_DISTANCE:
                        # This is a tap - check if on center area
                        dist_from_center = math.hypot(mx - CENTER[0], my - CENTER[1])
                        if dist_from_center <= CENTER_TAP_RADIUS:
                            # Toggle controls visibility
                            controls_visible = not controls_visible
                            controls_show_time = time.time()
                
                # Apply accumulated seek if we were dragging
                if dragging and abs(accumulated_rotation) > 5:  # Minimum rotation threshold
                    seek_delta_ms = int(accumulated_rotation * SEEK_SENSITIVITY)
                    new_position = current_position_ms + seek_delta_ms
                    new_position = max(0, min(new_position, track_duration_ms))
                    try:
                        seek_position(new_position)
                        current_position_ms = new_position
                    except Exception as e:
                        print(f"Error seeking: {e}", file=sys.stderr)
                
                dragging = False
                click_start_time = None
                click_start_pos = None
                accumulated_rotation = 0

            # Mouse/touch motion (dragging)
            elif event.type == pygame.MOUSEMOTION and dragging:
                # Calculate rotation based on circular motion around center
                rotation_delta = calculate_rotation_delta(event.pos, last_mouse_pos, CENTER)
                
                # Update visual angle
                angle += rotation_delta
                angle %= 360
                
                # Accumulate rotation for seeking
                accumulated_rotation += rotation_delta
                
                # Play scratch sound periodically while dragging
                current_time = time.time()
                if (abs(rotation_delta) > 2 and 
                    current_time - last_scratch_sound_time > SCRATCH_SOUND_COOLDOWN and
                    scratch_sounds):
                    random.choice(scratch_sounds).play()
                    last_scratch_sound_time = current_time
                
                last_mouse_pos = event.pos

        # -------------------------------
        # Auto-hide controls
        # -------------------------------
        if controls_visible and time.time() - controls_show_time > CONTROLS_AUTO_HIDE_SECONDS:
            controls_visible = False

        # -------------------------------
        # Update position estimate (interpolate between API updates)
        # -------------------------------
        if is_playing and not dragging:
            elapsed_since_update = time.time() - last_playback_update
            current_position_ms += elapsed_since_update * 1000
            last_playback_update = time.time()

        # -------------------------------
        # Drawing
        # -------------------------------
        # Background - warm cream color
        screen.fill((245, 230, 200))

        # Rotate and draw vinyl
        rotated_vinyl = pygame.transform.rotate(vinyl_surface, angle)
        vinyl_rect = rotated_vinyl.get_rect(center=CENTER)
        screen.blit(rotated_vinyl, vinyl_rect)
        
        # Auto-rotate when playing (and not dragging)
        if is_playing and not dragging:
            angle = (angle + angle_speed) % 360

        # Draw controls overlay (if visible)
        if controls_visible:
            # Semi-transparent overlay at bottom
            overlay = pygame.Surface((SCREEN_SIZE, 280), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 800))
            
            # Draw banner
            banner_x = (SCREEN_SIZE - banner.get_width()) // 2
            banner_y = 810
            screen.blit(banner, (banner_x, banner_y))
            
            # Calculate control positions
            prev_w, prev_h = prev_btn.get_width(), prev_btn.get_height()
            pause_w, pause_h = pause_btn.get_width(), pause_btn.get_height()
            skip_w, skip_h = skip_btn.get_width(), skip_btn.get_height()
            
            total_width = prev_w + pause_w + skip_w + 100
            start_x = (SCREEN_SIZE - total_width) // 2
            control_y = 920
            
            prev_x = start_x
            pause_x = prev_x + prev_w + 50
            skip_x = pause_x + pause_w + 50
            
            # Draw control buttons
            screen.blit(prev_btn, (prev_x, control_y - prev_h // 2))
            screen.blit(pause_btn if is_playing else play_btn, (pause_x, control_y - pause_h // 2))
            screen.blit(skip_btn, (skip_x, control_y - skip_h // 2))
            
            # Draw song info
            if details:
                title_surf = font.render(details["title"], True, (255, 255, 255))
                artist_surf = small_font.render(details["artist"], True, (200, 200, 200))
                
                # Center the text
                title_x = (SCREEN_SIZE - title_surf.get_width()) // 2
                artist_x = (SCREEN_SIZE - artist_surf.get_width()) // 2
                
                screen.blit(title_surf, (title_x, 975))
                screen.blit(artist_surf, (artist_x, 1015))
                
                # Draw progress bar
                if track_duration_ms > 0:
                    bar_width = 400
                    bar_height = 4
                    bar_x = (SCREEN_SIZE - bar_width) // 2
                    bar_y = 1055
                    
                    # Background bar
                    pygame.draw.rect(screen, (80, 80, 80), (bar_x, bar_y, bar_width, bar_height))
                    
                    # Progress bar
                    progress = min(current_position_ms / track_duration_ms, 1.0)
                    pygame.draw.rect(screen, (30, 215, 96), (bar_x, bar_y, int(bar_width * progress), bar_height))

        pygame.display.flip()
        clock.tick(60)  # 60 FPS


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spotify Record Player")
    parser.add_argument('--windowed', action='store_true', help='Run in windowed mode (no fullscreen)')
    args = parser.parse_args()
    run(windowed=args.windowed)

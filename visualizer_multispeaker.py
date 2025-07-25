#!/usr/bin/env python3
"""
Multi-Speaker Tactile Spatialiser Visualizer - Pygame-based visualization tool.

This script provides a real-time visualization of the Multi-Speaker Spatialiser,
showing the speaker positions and current sound source in a simple GUI interface.

Usage:
  python visualizer_multispeaker.py [script_file.txt]

Dependencies:
  - pygame
  - numpy
"""

import os
import sys
import time
import threading
import queue
import pygame
import numpy as np
import colorsys
import re

# Import the spatialiser modules
try:
    import multispeaker_main as spatialiser
except ImportError:
    print("Warning: Could not import multispeaker_main module. Some features may be limited.")
    spatialiser = None

# Initialize pygame
pygame.init()

# Constants
WINDOW_SIZE = (1000, 800)
BACKGROUND_COLOR = (240, 240, 240)
GRID_COLOR = (200, 200, 200)
AXIS_COLOR = (100, 100, 100)
SPEAKER_COLOR = (50, 150, 50)
SPEAKER_ACTIVE_COLOR = (255, 100, 100)
SOUND_COLOR_BASE = (255, 0, 0)  # Base color, will be modified by frequency
PATH_COLOR = (180, 180, 180)
CONNECTION_COLOR = (100, 100, 255, 64)  # Semi-transparent
TEXT_COLOR = (20, 20, 20)
COMMENT_COLOR = (0, 100, 0)  # Green color for comments
SPEAKER_LABEL_COLOR = (60, 60, 60)

SCALE = 2000  # Pixels per meter (higher scale for tactile grid)
SPEAKER_RADIUS = 8
SOUND_RADIUS_MIN = 12
SOUND_RADIUS_MAX = 24

# Message queue for communication between threads
message_queue = queue.Queue()

# Current state
current_position = np.array([0.0, 0.0])
is_playing = False
show_paths = True
show_speaker_labels = True
show_connections = True
current_frequency = 200
current_amplitude = 0.5
script_actions = []
script_path = None
current_comment = ""
speaker_gains = None  # Will store current speaker gains

# Paths to display
arc_paths = []
circle_paths = []
freq_ramp_paths = []

# Speaker configuration
speaker_config = None

def set_speaker_config(config):
    """Set the speaker configuration for visualization."""
    global speaker_config
    speaker_config = config

def meters_to_pixels(coords):
    """Convert coordinates from meters to pixels on screen."""
    center_x, center_y = WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2
    x_pixels = center_x + int(coords[0] * SCALE)
    y_pixels = center_y - int(coords[1] * SCALE)  # Y is inverted in pygame
    return x_pixels, y_pixels

def render_speaker_info(screen, font):
    """Render speaker configuration information."""
    if not speaker_config:
        return
    
    # Create info box in the upper left
    info_width = 300
    info_height = 120
    info_box = pygame.Surface((info_width, info_height), pygame.SRCALPHA)
    info_box.fill((255, 255, 255, 200))  # Semi-transparent white background
    
    # Add configuration info
    y_pos = 5
    
    config_text = f"Config: {speaker_config.config_name}"
    text_surface = font.render(config_text, True, TEXT_COLOR)
    info_box.blit(text_surface, (10, y_pos))
    y_pos += 20
    
    speakers_text = f"Speakers: {len(speaker_config.speakers)}"
    text_surface = font.render(speakers_text, True, TEXT_COLOR)
    info_box.blit(text_surface, (10, y_pos))
    y_pos += 20
    
    channels_text = f"Channels: {speaker_config.get_num_channels()}"
    text_surface = font.render(channels_text, True, TEXT_COLOR)
    info_box.blit(text_surface, (10, y_pos))
    y_pos += 20
    
    method_text = f"Method: {speaker_config.method}"
    text_surface = font.render(method_text, True, TEXT_COLOR)
    info_box.blit(text_surface, (10, y_pos))
    y_pos += 20
    
    # Coverage area
    if speaker_config.speakers:
        positions = speaker_config.get_speaker_positions()
        x_range = np.ptp(positions[:, 0]) * 1000  # Convert to mm
        y_range = np.ptp(positions[:, 1]) * 1000
        coverage_text = f"Coverage: {x_range:.0f}x{y_range:.0f}mm"
        text_surface = font.render(coverage_text, True, TEXT_COLOR)
        info_box.blit(text_surface, (10, y_pos))
    
    # Place the info box in the upper left
    screen.blit(info_box, (10, 10))

def render_position_info(screen, font, position):
    """Render the current position information."""
    # Create a separate info box in the lower left
    info_box = pygame.Surface((400, 30), pygame.SRCALPHA)
    info_box.fill((255, 255, 255, 200))  # Semi-transparent white background

    info_text = f"Position: ({position[0]*1000:.1f}, {position[1]*1000:.1f})mm"
    if current_frequency:
        info_text += f"  |  Freq: {current_frequency:.0f} Hz"
    if current_amplitude:
        info_text += f"  |  Amp: {current_amplitude:.2f}"

    text_surface = font.render(info_text, True, TEXT_COLOR)
    info_box.blit(text_surface, (10, 5))

    # Place the info box in the lower left
    screen.blit(info_box, (10, WINDOW_SIZE[1] - 40))

def render_legend(screen, font):
    """Render a legend explaining the visual elements."""
    # Create a legend box in the upper right
    legend_width = 220
    legend_height = 180
    legend_box = pygame.Surface((legend_width, legend_height), pygame.SRCALPHA)
    legend_box.fill((255, 255, 255, 200))  # Semi-transparent white background

    # Add a title
    title_surface = font.render("Legend", True, TEXT_COLOR)
    legend_box.blit(title_surface, (10, 5))

    # Legend items
    legend_items = [
        ("Green Circles", "Speakers (idle)", SPEAKER_COLOR),
        ("Red Circles", "Speakers (active)", SPEAKER_ACTIVE_COLOR),
        ("Red Circle", "Sound source", SOUND_COLOR_BASE),
        ("Gray Lines", "Paths", PATH_COLOR),
        ("Blue Lines", "Connections", CONNECTION_COLOR[:3])
    ]

    y_pos = 30
    for item, desc, color in legend_items:
        # Draw color sample
        pygame.draw.rect(legend_box, color, (10, y_pos, 15, 15))

        # Draw text
        text_surface = font.render(f"{item}: {desc}", True, TEXT_COLOR)
        legend_box.blit(text_surface, (35, y_pos))
        y_pos += 24

    # Add controls
    y_pos += 10
    controls_text = "Controls:"
    text_surface = font.render(controls_text, True, TEXT_COLOR)
    legend_box.blit(text_surface, (10, y_pos))
    y_pos += 20

    controls = [
        "H = Toggle paths",
        "L = Toggle labels",
        "C = Toggle connections",
        "Q = Quit"
    ]

    for control in controls:
        text_surface = font.render(control, True, TEXT_COLOR)
        legend_box.blit(text_surface, (10, y_pos))
        y_pos += 16

    # Place the legend box in the upper right with some padding
    screen.blit(legend_box, (WINDOW_SIZE[0] - legend_width - 10, 10))

def render_comment(screen, font, comment):
    """Render the current comment as a progress indicator."""
    if not comment:
        return

    # Create a comment box at the bottom center
    comment_box = pygame.Surface((600, 30), pygame.SRCALPHA)
    comment_box.fill((240, 255, 240, 220))  # Light green semi-transparent background

    # Render comment text
    text_surface = font.render(comment, True, COMMENT_COLOR)

    # Center the text in the box
    text_rect = text_surface.get_rect(center=(comment_box.get_width() // 2, comment_box.get_height() // 2))
    comment_box.blit(text_surface, text_rect)

    # Position the box at the bottom center of the screen
    screen.blit(comment_box, (WINDOW_SIZE[0] // 2 - 300, WINDOW_SIZE[1] - 80))

def get_color_by_frequency(freq):
    """
    Generate a color based on frequency.
    Lower frequencies are blue, higher frequencies are red.
    """
    # Normalize frequency to 0-1 range (100-500 Hz typical range)
    normalized = max(0, min(1, (freq - 100) / 400))

    # Convert from HSV to RGB (hue from 240° (blue) to 0° (red))
    h = (1 - normalized) * 0.66  # hue (0.66 = blue, 0 = red)
    s = 1.0  # saturation
    v = 1.0  # value
    r, g, b = colorsys.hsv_to_rgb(h, s, v)

    return (int(r * 255), int(g * 255), int(b * 255))

def render_speakers(screen, font):
    """Render all speakers in the configuration."""
    if not speaker_config:
        return

    for i, speaker in enumerate(speaker_config.speakers):
        x, y = speaker['pos']
        screen_x, screen_y = meters_to_pixels([x, y])

        # Determine speaker color based on activity
        if speaker_gains is not None and i < len(speaker_gains) and speaker_gains[i] > 0.001:
            # Active speaker - make it red with size based on gain
            color = SPEAKER_ACTIVE_COLOR
            radius = int(SPEAKER_RADIUS * (1 + speaker_gains[i] * 2))
        else:
            # Idle speaker
            color = SPEAKER_COLOR
            radius = SPEAKER_RADIUS

        # Draw speaker
        pygame.draw.circle(screen, color, (screen_x, screen_y), radius)
        pygame.draw.circle(screen, (0, 0, 0), (screen_x, screen_y), radius, 2)  # Black border

        # Draw speaker label if enabled
        if show_speaker_labels:
            label_text = f"CH{speaker['channel']}"
            text_surface = font.render(label_text, True, SPEAKER_LABEL_COLOR)
            text_rect = text_surface.get_rect(center=(screen_x, screen_y - radius - 15))
            screen.blit(text_surface, text_rect)

def render_connections(screen):
    """Render connections from sound source to active speakers."""
    if not speaker_config or not show_connections or speaker_gains is None:
        return

    sound_x, sound_y = meters_to_pixels(current_position)

    # Create a surface with per-pixel alpha for semi-transparent lines
    connection_surface = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)

    for i, speaker in enumerate(speaker_config.speakers):
        if i < len(speaker_gains) and speaker_gains[i] > 0.001:
            x, y = speaker['pos']
            speaker_x, speaker_y = meters_to_pixels([x, y])

            # Line thickness based on gain
            thickness = max(1, int(3 * speaker_gains[i]))

            # Draw connection line
            pygame.draw.line(
                connection_surface, CONNECTION_COLOR,
                (sound_x, sound_y), (speaker_x, speaker_y),
                thickness
            )

    # Blit the connection surface onto the main screen
    screen.blit(connection_surface, (0, 0))

def render_paths(screen):
    """Render all paths (ARCs, CIRCLEs, and PATH_FREQ_RAMPs)."""
    if not show_paths:
        return

    # Draw ARC paths
    for path in arc_paths:
        if len(path) < 2:
            continue

        # Convert path points to screen coordinates
        screen_points = [meters_to_pixels(p) for p in path]

        # Draw the path
        pygame.draw.lines(screen, PATH_COLOR, False, screen_points, 2)

    # Draw PATH_FREQ_RAMP paths
    for path in freq_ramp_paths:
        if len(path) < 2:
            continue

        # Convert path points to screen coordinates
        screen_points = [meters_to_pixels(p) for p in path]

        # Draw the path
        pygame.draw.lines(screen, PATH_COLOR, False, screen_points, 2)

    # Draw CIRCLE paths
    center_x, center_y = WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2
    for radius in circle_paths:
        pygame.draw.circle(
            screen,
            PATH_COLOR,
            (center_x, center_y),
            int(radius * SCALE),
            2  # Width of 2 pixels
        )

def generate_bezier_curve_points(p0, p1, p2, num_points):
    """Generate points along a quadratic Bézier curve."""
    points = []
    for i in range(num_points):
        t = i / (num_points - 1) if num_points > 1 else 0
        # Quadratic Bézier formula
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        points.append((x, y))
    return points

def generate_linear_points(p0, p1, num_points):
    """Generate points along a straight line."""
    points = []
    for i in range(num_points):
        t = i / (num_points - 1) if num_points > 1 else 0
        x = p0[0] + t * (p1[0] - p0[0])
        y = p0[1] + t * (p1[1] - p0[1])
        points.append((x, y))
    return points

def extract_paths_from_actions(actions):
    """Extract all paths from the actions list for visualization."""
    global arc_paths, circle_paths, freq_ramp_paths

    arc_paths = []
    circle_paths = []
    freq_ramp_paths = []

    for act in actions:
        cmd = act[0]

        if cmd == 'ARC':
            _, points, _, _, _, _, mode = act

            if mode == 'CURVED' and len(points) == 3:
                # Generate points along the Bézier curve
                curve_points = generate_bezier_curve_points(
                    points[0], points[1], points[2], 50)
                arc_paths.append(curve_points)
            else:
                # Linear path
                line_points = generate_linear_points(
                    points[0], points[-1], 20)
                arc_paths.append(line_points)

        elif cmd == 'CIRCLE_SMOOTH':
            _, radius, _, _, _, _ = act
            circle_paths.append(radius)

        elif cmd == 'PATH_FREQ_RAMP':
            _, points, _, _, _, _, _, mode = act

            if mode == 'CURVED' and len(points) == 3:
                # Generate points along the Bézier curve for PATH_FREQ_RAMP
                curve_points = generate_bezier_curve_points(
                    points[0], points[1], points[2], 50)
                freq_ramp_paths.append(curve_points)
            else:
                # Linear path for PATH_FREQ_RAMP
                line_points = generate_linear_points(
                    points[0], points[-1], 20)
                freq_ramp_paths.append(line_points)

def update_speaker_gains(position, spatialiser_instance):
    """Update speaker gains based on current position."""
    global speaker_gains
    
    if spatialiser_instance and spatialiser_instance.audio_engine:
        try:
            gains, _ = spatialiser_instance.audio_engine.spat_engine.calculate_gains_delays(position)
            speaker_gains = gains
        except Exception as e:
            print(f"Error calculating gains: {e}")
            speaker_gains = None

def run_visualization(position_queue):
    """Run the visualization in a mode that reads from a queue."""
    global current_position, is_playing, script_path
    global current_frequency, current_amplitude, show_paths, show_speaker_labels, show_connections
    global current_comment, speaker_config

    # Setup the display
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Multi-Speaker Spatialiser Visualizer")

    # Setup fonts
    font = pygame.font.Font(None, 20)
    small_font = pygame.font.Font(None, 16)

    # Try to get speaker configuration from spatialiser
    if spatialiser and hasattr(spatialiser, 'generate_tactile_tone') and hasattr(spatialiser.generate_tactile_tone, 'spatialiser'):
        speaker_config = spatialiser.generate_tactile_tone.spatialiser.speaker_config
    
    # Main loop
    running = True
    clock = pygame.time.Clock()
    status_message = "Playing script..."
    is_playing = True

    while running:
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:  # Toggle paths
                    show_paths = not show_paths
                elif event.key == pygame.K_l:  # Toggle labels
                    show_speaker_labels = not show_speaker_labels
                elif event.key == pygame.K_c:  # Toggle connections
                    show_connections = not show_connections
                elif event.key == pygame.K_q:  # Quit
                    running = False

        # Process position updates from queue
        while not position_queue.empty():
            try:
                position, action = position_queue.get_nowait()
                current_position = position

                if action:
                    if 'freq' in action:
                        current_frequency = action['freq']
                    if 'amp' in action:
                        current_amplitude = action['amp']
                    if 'comment' in action:
                        current_comment = action['comment']
                
                # Update speaker gains
                if spatialiser and hasattr(spatialiser, 'generate_tactile_tone') and hasattr(spatialiser.generate_tactile_tone, 'spatialiser'):
                    update_speaker_gains(position, spatialiser.generate_tactile_tone.spatialiser)
                
            except queue.Empty:
                break

        # Clear the screen
        screen.fill(BACKGROUND_COLOR)

        # Draw the grid
        center_x, center_y = WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2
        
        # Determine grid range based on speaker configuration
        if speaker_config and speaker_config.speakers:
            positions = speaker_config.get_speaker_positions()
            max_range = max(np.max(np.abs(positions[:, 0])), np.max(np.abs(positions[:, 1])))
            grid_range = max_range * 1.2  # Add 20% margin
        else:
            grid_range = 0.1  # Default 100mm range

        # Grid lines
        grid_step = 0.02  # 20mm steps
        for i in range(int(-grid_range/grid_step), int(grid_range/grid_step) + 1):
            coord = i * grid_step
            if coord == 0:
                continue  # Skip center lines, drawn separately
            
            # Horizontal lines
            y_pixel = center_y - int(coord * SCALE)
            if 0 <= y_pixel <= WINDOW_SIZE[1]:
                pygame.draw.line(
                    screen, GRID_COLOR,
                    (center_x - int(grid_range * SCALE), y_pixel),
                    (center_x + int(grid_range * SCALE), y_pixel)
                )
            
            # Vertical lines
            x_pixel = center_x + int(coord * SCALE)
            if 0 <= x_pixel <= WINDOW_SIZE[0]:
                pygame.draw.line(
                    screen, GRID_COLOR,
                    (x_pixel, center_y - int(grid_range * SCALE)),
                    (x_pixel, center_y + int(grid_range * SCALE))
                )

        # Draw axes
        pygame.draw.line(
            screen, AXIS_COLOR,
            (center_x - int(grid_range * SCALE), center_y),
            (center_x + int(grid_range * SCALE), center_y),
            2
        )
        pygame.draw.line(
            screen, AXIS_COLOR,
            (center_x, center_y - int(grid_range * SCALE)),
            (center_x, center_y + int(grid_range * SCALE)),
            2
        )

        # Draw paths
        render_paths(screen)

        # Draw speakers
        render_speakers(screen, small_font)

        # Draw connections
        render_connections(screen)

        # Draw current sound position
        sound_x, sound_y = meters_to_pixels(current_position)

        # Calculate sound source radius based on amplitude
        sound_radius = SOUND_RADIUS_MIN + (SOUND_RADIUS_MAX - SOUND_RADIUS_MIN) * current_amplitude

        # Calculate color based on frequency
        sound_color = get_color_by_frequency(current_frequency)

        # Draw sound source
        pygame.draw.circle(screen, sound_color, (sound_x, sound_y), int(sound_radius))
        pygame.draw.circle(screen, (0, 0, 0), (sound_x, sound_y), int(sound_radius), 2)  # Black border

        # Display status and controls
        status_text = font.render(status_message, True, TEXT_COLOR)
        screen.blit(status_text, (10, WINDOW_SIZE[1] - 120))

        # Render speaker configuration info
        render_speaker_info(screen, font)

        # Render position information
        render_position_info(screen, font, current_position)

        # Render current comment
        render_comment(screen, font, current_comment)

        # Render legend
        render_legend(screen, font)

        # Update the display
        pygame.display.flip()

        # Cap the frame rate
        clock.tick(60)

    # Clean up
    pygame.quit()

def main():
    """Main function for the visualizer."""
    global current_position, is_playing, script_path
    global current_frequency, current_amplitude, show_paths, show_speaker_labels, show_connections
    global current_comment, speaker_config

    # Setup the display
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Multi-Speaker Spatialiser Visualizer")

    # Setup fonts
    font = pygame.font.Font(None, 24)

    # Script selection
    if len(sys.argv) > 1:
        script_path = sys.argv[1]
    else:
        print("No script specified. Drag and drop a script file onto the window to load.")

    # Main loop
    running = True
    clock = pygame.time.Clock()
    status_message = "Please run the visualizer by using the --visualizer option in the main script."

    while running:
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.DROPFILE:
                script_path = event.file
                status_message = f"Loaded script: {os.path.basename(script_path)}"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:  # Toggle paths
                    show_paths = not show_paths
                elif event.key == pygame.K_l:  # Toggle labels
                    show_speaker_labels = not show_speaker_labels
                elif event.key == pygame.K_c:  # Toggle connections
                    show_connections = not show_connections
                elif event.key == pygame.K_q:  # Quit
                    running = False

        # Clear the screen
        screen.fill(BACKGROUND_COLOR)

        # Draw basic grid and axes
        center_x, center_y = WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2
        
        # Simple grid for standalone mode
        grid_range = 0.1
        grid_step = 0.02
        for i in range(int(-grid_range/grid_step), int(grid_range/grid_step) + 1):
            coord = i * grid_step
            if coord == 0:
                continue
            
            # Horizontal lines
            y_pixel = center_y - int(coord * SCALE)
            if 0 <= y_pixel <= WINDOW_SIZE[1]:
                pygame.draw.line(
                    screen, GRID_COLOR,
                    (center_x - int(grid_range * SCALE), y_pixel),
                    (center_x + int(grid_range * SCALE), y_pixel)
                )
            
            # Vertical lines
            x_pixel = center_x + int(coord * SCALE)
            if 0 <= x_pixel <= WINDOW_SIZE[0]:
                pygame.draw.line(
                    screen, GRID_COLOR,
                    (x_pixel, center_y - int(grid_range * SCALE)),
                    (x_pixel, center_y + int(grid_range * SCALE))
                )

        # Draw axes
        pygame.draw.line(
            screen, AXIS_COLOR,
            (center_x - int(grid_range * SCALE), center_y),
            (center_x + int(grid_range * SCALE), center_y),
            2
        )
        pygame.draw.line(
            screen, AXIS_COLOR,
            (center_x, center_y - int(grid_range * SCALE)),
            (center_x, center_y + int(grid_range * SCALE)),
            2
        )

        # Draw speakers if available
        render_speakers(screen, font)

        # Draw current sound position
        sound_x, sound_y = meters_to_pixels(current_position)
        sound_radius = SOUND_RADIUS_MIN + (SOUND_RADIUS_MAX - SOUND_RADIUS_MIN) * current_amplitude
        sound_color = get_color_by_frequency(current_frequency)
        pygame.draw.circle(screen, sound_color, (sound_x, sound_y), int(sound_radius))

        # Display status
        status_text = font.render(status_message, True, TEXT_COLOR)
        screen.blit(status_text, (10, 10))

        # Render speaker info and legend
        render_speaker_info(screen, font)
        render_legend(screen, font)

        # Update the display
        pygame.display.flip()

        # Cap the frame rate
        clock.tick(60)

    # Clean up
    pygame.quit()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Multi-Speaker Tactile Spatialiser - FIXED VERSION (No Double Playback + Smooth Tactile Grid)
Complete implementation with text-based configuration files.
Default: 4x4 grid with 40mm spacing between speakers.
CHANNELS START AT 0 AND ARE PROPERLY MAPPED.

FIXES APPLIED:
- Fixed double audio engine creation
- Added proper stream cleanup
- Prevented double playback issues
- Enhanced error handling
- FIXED: Smooth tactile grid spatialization (no more clicking/jumping)

Usage:
  python multispeaker_main.py --config config_4x4_grid.txt
  python multispeaker_main.py --create-configs
  python multispeaker_main.py script.txt  # Run tactile script with multi-speaker
"""

import numpy as np
import sounddevice as sd
import time
import argparse
import re
import os
import threading
import queue

# === GLOBAL PARAMETERS (for compatibility with original system) ===
sample_rate = 48000
tone_duration = 0.1
itd_exaggeration = 1.0
ild_exponent = 1.0
current_position = np.array([0.0, 0.0])
visualizer_callback = None
position_lock = threading.Lock()


# === SPEAKER CONFIGURATION PARSER ===
class SpeakerConfig:
    def __init__(self):
        # Default 4x4 grid with 40mm spacing
        self.spacing = 0.04  # 40mm in meters
        self.grid_size = 4
        self.method = 'tactile_grid'
        self.speakers = []
        self.config_name = 'default_4x4'

        # Initialize default configuration
        self.create_default_grid()

    def create_default_grid(self):
        """Create default 4x4 grid with 40mm spacing - CHANNELS START AT 0."""
        self.speakers = []

        # Calculate positions for 4x4 grid centered at (0,0)
        # Grid spans from -60mm to +60mm (3 * 40mm spacing)
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # Center the grid at (0,0)
                x = (j - (self.grid_size - 1) / 2) * self.spacing  # j for x-axis
                y = ((self.grid_size - 1 - i) - (self.grid_size - 1) / 2) * self.spacing  # Flip i for y-axis

                # Channel assignment: bottom-left = 0, increment left-to-right, bottom-to-top
                channel = i * self.grid_size + j

                speaker = {
                    'id': f'SP_{i:02d}_{j:02d}',
                    'pos': [x, y],
                    'channel': channel,  # Starts at 0
                    'row': i,
                    'col': j
                }
                self.speakers.append(speaker)

        print(f"Created default {self.grid_size}x{self.grid_size} grid with channels 0-{len(self.speakers) - 1}")

    def parse_config_line(self, line):
        """Parse a single configuration line."""
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith('#'):
            return True

        # Grid command - handle this BEFORE config assignments
        if line.upper().startswith('GRID'):
            return self.parse_grid_line(line)

        # Circle array command
        if line.upper().startswith('CIRCLE'):
            return self.parse_circle_line(line)

        # Line array command
        if line.upper().startswith('LINE'):
            return self.parse_line_array(line)

        # Speaker definition
        if line.upper().startswith('SPEAKER'):
            return self.parse_speaker_line(line)

        # Configuration assignments
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip().lower()
            value = value.strip()

            if key == 'spacing':
                self.spacing = float(value)
            elif key == 'grid_size':
                self.grid_size = int(value)
                self.create_default_grid()  # Recreate with new size
            elif key == 'method':
                self.method = value.lower()
            elif key == 'config_name':
                self.config_name = value
            else:
                print(f"Warning: Unknown config parameter: {key}")
            return True

        print(f"Warning: Unknown command: {line}")
        return False

    def parse_speaker_line(self, line):
        """Parse SPEAKER command: SPEAKER ID x,y CHANNEL=n [DESCRIPTION="text"]"""
        try:
            parts = line.split()
            if len(parts) < 3:
                print(f"Warning: Invalid SPEAKER command: {line}")
                return False

            speaker_id = parts[1]
            coords = parts[2].split(',')

            if len(coords) != 2:
                print(f"Warning: Invalid coordinates in SPEAKER: {line}")
                return False

            x, y = float(coords[0]), float(coords[1])

            # Extract channel - ENFORCE 0-BASED INDEXING
            channel_match = re.search(r'CHANNEL=(\d+)', line)
            if not channel_match:
                print(f"Warning: Missing CHANNEL in SPEAKER: {line}")
                return False

            channel = int(channel_match.group(1))

            # Validate channel number
            if channel < 0:
                print(f"Warning: Channel numbers must be >= 0, got {channel}")
                return False

            # Extract optional description
            desc_match = re.search(r'DESCRIPTION="([^"]*)"', line)
            description = desc_match.group(1) if desc_match else ""

            speaker = {
                'id': speaker_id,
                'pos': [x, y],
                'channel': channel,  # 0-based channel
                'description': description
            }

            self.speakers.append(speaker)
            print(f"Added speaker {speaker_id} at channel {channel} (0-based)")
            return True

        except (ValueError, IndexError) as e:
            print(f"Warning: Error parsing SPEAKER command: {line} - {e}")
            return False

    def parse_grid_line(self, line):
        """Parse GRID command: GRID SIZE=4 SPACING=0.04 [OFFSET=0.0,0.0] - CHANNELS START AT 0"""
        try:
            # Extract parameters
            size_match = re.search(r'SIZE=(\d+)', line)
            spacing_match = re.search(r'SPACING=([0-9.]+)', line)
            offset_match = re.search(r'OFFSET=([0-9.-]+),([0-9.-]+)', line)

            if not size_match or not spacing_match:
                print(f"Warning: GRID requires SIZE and SPACING: {line}")
                return False

            size = int(size_match.group(1))
            spacing = float(spacing_match.group(1))

            offset_x, offset_y = 0.0, 0.0
            if offset_match:
                offset_x = float(offset_match.group(1))
                offset_y = float(offset_match.group(2))

            # Clear existing speakers and create grid
            self.speakers = []
            self.grid_size = size
            self.spacing = spacing

            for i in range(size):
                for j in range(size):
                    # Center the grid at offset - FIXED COORDINATE MAPPING
                    x = (j - (size - 1) / 2) * spacing + offset_x  # j maps to x
                    y = ((size - 1 - i) - (size - 1) / 2) * spacing + offset_y  # Flip i for y

                    # Channel assignment: 0-based, left-to-right, bottom-to-top
                    channel = i * size + j

                    speaker = {
                        'id': f'G_{i:02d}_{j:02d}',
                        'pos': [x, y],
                        'channel': channel,  # 0-based channels
                        'row': i,
                        'col': j
                    }
                    self.speakers.append(speaker)

            print(
                f"Created {size}x{size} grid with {spacing * 1000:.1f}mm spacing, channels 0-{len(self.speakers) - 1}")
            return True

        except (ValueError, IndexError) as e:
            print(f"Warning: Error parsing GRID command: {line} - {e}")
            return False

    def parse_circle_line(self, line):
        """Parse CIRCLE command: CIRCLE COUNT=8 RADIUS=2.0 [OFFSET=0.0,0.0] - CHANNELS START AT 0"""
        try:
            count_match = re.search(r'COUNT=(\d+)', line)
            radius_match = re.search(r'RADIUS=([0-9.]+)', line)
            offset_match = re.search(r'OFFSET=([0-9.-]+),([0-9.-]+)', line)

            if not count_match or not radius_match:
                print(f"Warning: CIRCLE requires COUNT and RADIUS: {line}")
                return False

            count = int(count_match.group(1))
            radius = float(radius_match.group(1))

            offset_x, offset_y = 0.0, 0.0
            if offset_match:
                offset_x = float(offset_match.group(1))
                offset_y = float(offset_match.group(2))

            # Clear existing speakers and create circle
            self.speakers = []

            for i in range(count):
                angle = 2 * np.pi * i / count
                x = radius * np.cos(angle) + offset_x
                y = radius * np.sin(angle) + offset_y

                speaker = {
                    'id': f'C_{i:02d}',
                    'pos': [x, y],
                    'channel': i,  # 0-based channels
                    'angle': angle * 180 / np.pi  # Store angle in degrees
                }
                self.speakers.append(speaker)

            print(f"Created {count}-speaker circle with {radius}m radius, channels 0-{count - 1}")
            return True

        except (ValueError, IndexError) as e:
            print(f"Warning: Error parsing CIRCLE command: {line} - {e}")
            return False

    def parse_line_array(self, line):
        """Parse LINE command: LINE COUNT=7 LENGTH=3.0 ANGLE=0 [OFFSET=0.0,0.0] - CHANNELS START AT 0"""
        try:
            count_match = re.search(r'COUNT=(\d+)', line)
            length_match = re.search(r'LENGTH=([0-9.]+)', line)
            angle_match = re.search(r'ANGLE=([0-9.-]+)', line)
            offset_match = re.search(r'OFFSET=([0-9.-]+),([0-9.-]+)', line)

            if not count_match or not length_match:
                print(f"Warning: LINE requires COUNT and LENGTH: {line}")
                return False

            count = int(count_match.group(1))
            length = float(length_match.group(1))
            angle = float(angle_match.group(1)) if angle_match else 0.0

            offset_x, offset_y = 0.0, 0.0
            if offset_match:
                offset_x = float(offset_match.group(1))
                offset_y = float(offset_match.group(2))

            # Clear existing speakers and create line
            self.speakers = []

            # Convert angle to radians
            angle_rad = np.radians(angle)

            for i in range(count):
                # Position along line from -length/2 to +length/2
                t = (i - (count - 1) / 2) * length / (count - 1) if count > 1 else 0

                x = t * np.cos(angle_rad) + offset_x
                y = t * np.sin(angle_rad) + offset_y

                speaker = {
                    'id': f'L_{i:02d}',
                    'pos': [x, y],
                    'channel': i,  # 0-based channels
                    'position': t  # Store position along line
                }
                self.speakers.append(speaker)

            print(f"Created {count}-speaker line array, {length}m length, channels 0-{count - 1}")
            return True

        except (ValueError, IndexError) as e:
            print(f"Warning: Error parsing LINE command: {line} - {e}")
            return False

    def load_from_file(self, filename):
        """Load speaker configuration from text file."""
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()

            # Reset to defaults
            self.speakers = []
            self.method = 'tactile_grid'
            self.config_name = os.path.splitext(os.path.basename(filename))[0]

            success = True
            for line_num, line in enumerate(lines, 1):
                if not self.parse_config_line(line):
                    print(f"Error on line {line_num}: {line.strip()}")
                    success = False

            if not self.speakers:
                print("Warning: No speakers defined, using default 4x4 grid")
                self.create_default_grid()

            # Validate channel assignments
            self.validate_channels()

            return success

        except Exception as e:
            print(f"Error loading config file: {e}")
            return False

    def validate_channels(self):
        """Validate that channel assignments are correct and 0-based."""
        if not self.speakers:
            return

        channels = [sp['channel'] for sp in self.speakers]

        # Check for duplicates
        if len(channels) != len(set(channels)):
            print("WARNING: Duplicate channel assignments detected!")
            channel_counts = {}
            for ch in channels:
                channel_counts[ch] = channel_counts.get(ch, 0) + 1
            for ch, count in channel_counts.items():
                if count > 1:
                    print(f"  Channel {ch} assigned to {count} speakers")

        # Check for gaps
        min_ch, max_ch = min(channels), max(channels)
        if min_ch < 0:
            print(f"WARNING: Negative channel number found: {min_ch}")

        expected_channels = set(range(max_ch + 1))
        actual_channels = set(channels)
        missing = expected_channels - actual_channels
        if missing:
            print(f"WARNING: Missing channel assignments: {sorted(missing)}")

        print(f"Channel validation: {len(channels)} speakers using channels {min_ch}-{max_ch}")

    def save_to_file(self, filename):
        """Save current configuration to text file."""
        try:
            with open(filename, 'w') as f:
                f.write(f"# Speaker Configuration: {self.config_name}\n")
                f.write(f"# Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# CHANNELS START AT 0\n\n")

                f.write(f"config_name = {self.config_name}\n")
                f.write(f"method = {self.method}\n\n")

                f.write("# Speakers (channels are 0-based)\n")
                for speaker in self.speakers:
                    x, y = speaker['pos']
                    desc = speaker.get('description', '')
                    desc_str = f' DESCRIPTION="{desc}"' if desc else ''
                    f.write(f"SPEAKER {speaker['id']} {x:.4f},{y:.4f} CHANNEL={speaker['channel']}{desc_str}\n")

            return True

        except Exception as e:
            print(f"Error saving config file: {e}")
            return False

    def get_num_channels(self):
        """Get the number of audio channels needed (0-based indexing)."""
        if not self.speakers:
            return 0
        return max(sp['channel'] for sp in self.speakers) + 1

    def get_speaker_positions(self):
        """Get array of speaker positions."""
        return np.array([sp['pos'] for sp in self.speakers])

    def print_info(self):
        """Print configuration information with clear channel mapping."""
        print(f"\n=== Speaker Configuration ===")
        print(f"Name: {self.config_name}")
        print(f"Method: {self.method}")
        print(f"Speakers: {len(self.speakers)}")
        print(f"Channels: {self.get_num_channels()} (0-based: 0 to {self.get_num_channels() - 1})")
        if self.speakers:
            positions = self.get_speaker_positions()
            x_range = np.ptp(positions[:, 0]) * 1000  # Convert to mm
            y_range = np.ptp(positions[:, 1]) * 1000
            print(f"Coverage: {x_range:.1f}mm x {y_range:.1f}mm")

        print("\nSpeaker Layout (channels are 0-based):")
        for sp in self.speakers:
            x, y = sp['pos']
            desc = sp.get('description', '')
            desc_str = f' ({desc})' if desc else ''
            print(f"  {sp['id']}: ({x * 1000:6.1f}, {y * 1000:6.1f})mm -> CH{sp['channel']}{desc_str}")

    def get_channel_map(self):
        """Get a mapping of channel numbers to speaker info for debugging."""
        channel_map = {}
        for sp in self.speakers:
            channel_map[sp['channel']] = {
                'id': sp['id'],
                'pos': sp['pos'],
                'description': sp.get('description', '')
            }
        return channel_map


# === SPATIALIZATION METHODS ===
class SpatializationEngine:
    def __init__(self, speaker_config):
        self.config = speaker_config
        self.method = speaker_config.method

        # Parameters for different methods
        self.speed_of_sound = 343.0  # m/s
        self.itd_exaggeration = 1.0
        self.ild_exponent = 1.0
        self.distance_rolloff = 2.0
        self.tactile_exaggeration = 4.0  # Extra exaggeration for tactile

    def set_parameters(self, **kwargs):
        """Set spatialization parameters."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def calculate_gains_delays(self, source_pos):
        """Calculate gains and delays for all speakers based on source position."""
        speakers = self.config.get_speaker_positions()
        num_speakers = len(speakers)

        gains = np.zeros(num_speakers)
        delays = np.zeros(num_speakers)

        if self.method == 'itd_ild':
            return self._calculate_itd_ild(source_pos, speakers)
        elif self.method == 'distance_pan':
            return self._calculate_distance_pan(source_pos, speakers)
        elif self.method == 'vbap':
            return self._calculate_vbap(source_pos, speakers)
        elif self.method == 'nearest_neighbor':
            return self._calculate_nearest_neighbor(source_pos, speakers)
        elif self.method == 'tactile_grid':
            return self._calculate_tactile_grid(source_pos, speakers)
        else:
            # Default: tactile grid for grid setups
            return self._calculate_tactile_grid(source_pos, speakers)

    def _calculate_nearest_neighbor(self, source_pos, speakers):
        """Nearest neighbor - only the closest speaker plays."""
        num_speakers = len(speakers)
        gains = np.zeros(num_speakers)
        delays = np.zeros(num_speakers)

        distances = np.array([np.linalg.norm(source_pos - sp) for sp in speakers])
        nearest_idx = np.argmin(distances)

        gains[nearest_idx] = 1.0

        return gains, delays

    def _calculate_tactile_grid(self, source_pos, speakers):
        """Tactile grid with smooth interpolation between adjacent speakers - FIXED VERSION."""
        num_speakers = len(speakers)
        gains = np.zeros(num_speakers)
        delays = np.zeros(num_speakers)

        # Calculate distances to all speakers
        distances = np.array([np.linalg.norm(source_pos - sp) for sp in speakers])

        # METHOD 1: Gaussian-based weighting for very smooth transitions
        # This provides the smoothest transitions but may feel less "localized"
        if hasattr(self, 'use_gaussian') and self.use_gaussian:
            # Use Gaussian falloff for very smooth transitions
            sigma = getattr(self, 'gaussian_sigma', 0.025)  # 25mm standard deviation - adjust for more/less smoothing
            weights = np.exp(-(distances ** 2) / (2 * sigma ** 2))
            gains = weights

            # Power normalization to maintain consistent perceived loudness
            total_power = np.sum(gains ** 2)
            if total_power > 0:
                gains = gains / np.sqrt(total_power)

        else:
            # METHOD 2: Improved inverse distance with smooth minimum (DEFAULT)
            # Find the nearest speakers for focused spatialization
            max_speakers = getattr(self, 'max_active_speakers', 6)  # Configurable number of active speakers
            nearest_indices = np.argsort(distances)[:min(max_speakers, num_speakers)]

            # Use smooth inverse distance weighting with larger minimum distance
            min_dist = getattr(self, 'smooth_min_distance', 0.008)  # 8mm minimum distance for smoother transitions
            distance_power = getattr(self, 'distance_power', 1.5)  # Power for distance falloff

            # Calculate weights for nearest speakers only
            total_weight = 0
            for idx in nearest_indices:
                dist = distances[idx]
                # Smooth inverse distance - less sharp than 1/d
                weight = 1.0 / ((dist + min_dist) ** distance_power)
                gains[idx] = weight
                total_weight += weight

            # Normalize weights to sum to 1
            if total_weight > 0:
                for idx in nearest_indices:
                    gains[idx] /= total_weight

            # REMOVED: No more tactile exaggeration bias on closest speaker
            # This was causing the uneven volume and clicking issues

            # Apply gentle overall tactile enhancement to all active speakers
            # This maintains tactile sensation without creating bias
            active_mask = gains > 0.001
            if np.any(active_mask):
                # Gentle enhancement: boost all active speakers slightly
                enhancement = getattr(self, 'tactile_enhancement', 1.2)  # Much gentler than the previous 4.0
                gains[active_mask] *= enhancement

                # Power normalization to prevent clipping and maintain consistency
                total_power = np.sum(gains ** 2)
                if total_power > 1.0:
                    gains = gains / np.sqrt(total_power)

        return gains, delays

    def set_tactile_grid_parameters(self, **kwargs):
        """
        Set parameters for tactile grid spatialization to fine-tune smoothness.

        Parameters:
        - use_gaussian (bool): Use Gaussian weighting instead of inverse distance (default: False)
        - gaussian_sigma (float): Standard deviation for Gaussian weighting in meters (default: 0.025)
        - max_active_speakers (int): Maximum number of speakers to use simultaneously (default: 6)
        - smooth_min_distance (float): Minimum distance for smooth transitions in meters (default: 0.008)
        - distance_power (float): Power for distance falloff - higher = more focused (default: 1.5)
        - tactile_enhancement (float): Overall tactile boost factor (default: 1.2)

        Examples:
        # For smoothest possible transitions (less localized but no clicks)
        spatialiser.audio_engine.spat_engine.set_tactile_grid_parameters(
            use_gaussian=True, gaussian_sigma=0.03
        )

        # For more focused spatialization (more localized but potentially more clicks)
        spatialiser.audio_engine.spat_engine.set_tactile_grid_parameters(
            max_active_speakers=4, distance_power=2.0, smooth_min_distance=0.005
        )

        # For gentler tactile enhancement
        spatialiser.audio_engine.spat_engine.set_tactile_grid_parameters(
            tactile_enhancement=1.1
        )
        """
        for key, value in kwargs.items():
            if key in ['use_gaussian', 'gaussian_sigma', 'max_active_speakers',
                       'smooth_min_distance', 'distance_power', 'tactile_enhancement']:
                setattr(self, key, value)
                print(f"Set {key} = {value}")
            else:
                print(f"Warning: Unknown parameter {key}")

        print("Tactile grid parameters updated. Test with a movement pattern to feel the difference.")

    def _calculate_distance_pan(self, source_pos, speakers):
        """Simple distance-based amplitude panning."""
        num_speakers = len(speakers)
        gains = np.zeros(num_speakers)
        delays = np.zeros(num_speakers)

        distances = np.array([np.linalg.norm(source_pos - sp) for sp in speakers])

        # Avoid division by zero
        distances = np.maximum(distances, 0.001)  # 1mm minimum

        # Inverse distance law
        raw_gains = 1.0 / (distances ** self.distance_rolloff)

        # Normalize gains
        total_power = np.sum(raw_gains ** 2)
        if total_power > 0:
            gains = raw_gains / np.sqrt(total_power)

        return gains, delays

    def _calculate_vbap(self, source_pos, speakers):
        """Vector Base Amplitude Panning (simplified 2D version)."""
        num_speakers = len(speakers)
        gains = np.zeros(num_speakers)
        delays = np.zeros(num_speakers)

        # Convert to polar coordinates
        source_angle = np.arctan2(source_pos[1], source_pos[0])
        if source_angle < 0:
            source_angle += 2 * np.pi

        # Calculate speaker angles
        speaker_angles = []
        for sp in speakers:
            angle = np.arctan2(sp[1], sp[0])
            if angle < 0:
                angle += 2 * np.pi
            speaker_angles.append(angle)

        speaker_angles = np.array(speaker_angles)

        # Find the two nearest speakers
        angle_diffs = np.abs(speaker_angles - source_angle)
        # Handle wraparound
        angle_diffs = np.minimum(angle_diffs, 2 * np.pi - angle_diffs)

        # Sort by angle difference
        sorted_indices = np.argsort(angle_diffs)

        # Use the two closest speakers
        sp1_idx = sorted_indices[0]
        sp2_idx = sorted_indices[1] if len(sorted_indices) > 1 else sorted_indices[0]

        if sp1_idx != sp2_idx:
            # Calculate gains using VBAP formula (simplified)
            angle1 = speaker_angles[sp1_idx]
            angle2 = speaker_angles[sp2_idx]

            # Ensure angle2 > angle1 (handle wraparound)
            if angle2 < angle1:
                if source_angle < angle1:
                    source_angle += 2 * np.pi
                angle2 += 2 * np.pi

            # Linear interpolation between the two speakers
            if angle2 != angle1:
                t = (source_angle - angle1) / (angle2 - angle1)
                t = np.clip(t, 0, 1)

                gains[sp1_idx] = np.sqrt(1 - t)
                gains[sp2_idx] = np.sqrt(t)
            else:
                gains[sp1_idx] = 1.0
        else:
            gains[sp1_idx] = 1.0

        return gains, delays

    def _calculate_itd_ild(self, source_pos, speakers):
        """Original ITD/ILD method for tactile systems."""
        num_speakers = len(speakers)
        gains = np.zeros(num_speakers)
        delays = np.zeros(num_speakers)

        if num_speakers < 2:
            if num_speakers == 1:
                gains[0] = 1.0
            return gains, delays

        for i, speaker_pos in enumerate(speakers):
            distance = np.linalg.norm(source_pos - speaker_pos)

            # ITD calculation (only for first two speakers)
            if i < 2:
                if i == 0:  # Left speaker
                    ref_distance = np.linalg.norm(source_pos - speakers[1])
                    time_diff = (distance - ref_distance) / self.speed_of_sound
                    delays[i] = time_diff * self.itd_exaggeration
                else:  # Right speaker
                    ref_distance = np.linalg.norm(source_pos - speakers[0])
                    time_diff = (distance - ref_distance) / self.speed_of_sound
                    delays[i] = time_diff * self.itd_exaggeration

            # ILD calculation
            if num_speakers == 2:
                if i == 0:  # Left
                    right_dist = np.linalg.norm(source_pos - speakers[1])
                    gains[i] = 1.0 if distance <= right_dist else (right_dist / distance) ** self.ild_exponent
                else:  # Right
                    left_dist = np.linalg.norm(source_pos - speakers[0])
                    gains[i] = 1.0 if distance <= left_dist else (left_dist / distance) ** self.ild_exponent
            else:
                gains[i] = 1.0 / (distance + 0.001)  # Avoid division by zero

        return gains, delays


# === AUDIO GENERATION ===
class MultiSpeakerAudioEngine:
    def __init__(self, speaker_config, sample_rate=48000):
        self.config = speaker_config
        self.sample_rate = sample_rate
        self.spat_engine = SpatializationEngine(speaker_config)

        # Audio parameters
        self.tone_duration = 0.1
        self.fade_duration = 0.05
        self.fade_len = int(self.fade_duration * sample_rate)

        # Initialize audio stream
        self.num_channels = self.config.get_num_channels()
        self.stream = None

        # Threading lock for thread-safe operation
        self.lock = threading.Lock()

        print(f"Audio engine initialized: {self.num_channels} channels (0-{self.num_channels - 1})")

    def set_parameters(self, **kwargs):
        """Set audio parameters."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                if key == 'fade_duration':
                    self.fade_len = int(value * self.sample_rate)
            elif hasattr(self.spat_engine, key):
                self.spat_engine.set_parameters(**{key: value})

    def start_stream(self):
        """Start the audio output stream."""
        with self.lock:
            if self.stream is None:
                try:
                    self.stream = sd.OutputStream(
                        samplerate=self.sample_rate,
                        channels=self.num_channels,
                        dtype='float32',
                        blocksize=1024
                    )
                    self.stream.start()
                    print(
                        f"Audio stream started: {self.num_channels} channels (0-{self.num_channels - 1}) at {self.sample_rate}Hz")
                except Exception as e:
                    print(f"Error starting audio stream: {e}")
                    print(f"Available devices:")
                    try:
                        # Use the already imported sd module
                        devices = sd.query_devices()
                        for i, device in enumerate(devices):
                            if device['max_output_channels'] > 0:
                                print(f"  {i}: {device['name']} ({device['max_output_channels']} channels)")
                    except Exception as device_error:
                        print(f"Could not query devices: {device_error}")

                    # Try to use a device with enough channels
                    try:
                        devices = sd.query_devices()
                        suitable_device = None
                        for i, device in enumerate(devices):
                            if device['max_output_channels'] >= self.num_channels:
                                suitable_device = i
                                break

                        if suitable_device is not None:
                            print(f"Trying device {suitable_device}: {devices[suitable_device]['name']}")
                            self.stream = sd.OutputStream(
                                samplerate=self.sample_rate,
                                channels=self.num_channels,
                                dtype='float32',
                                blocksize=1024,
                                device=suitable_device
                            )
                            self.stream.start()
                            print(f"Audio stream started with device {suitable_device}")
                        else:
                            print(f"No device found with {self.num_channels} channels")
                            print(f"Try using a configuration with fewer channels.")
                            self.stream = None
                    except Exception as retry_error:
                        print(f"Retry failed: {retry_error}")
                        self.stream = None

    def stop_stream(self):
        """Stop the audio output stream."""
        with self.lock:
            if self.stream is not None:
                try:
                    self.stream.stop()
                    self.stream.close()
                    self.stream = None
                    print("Audio stream stopped")
                except Exception as e:
                    print(f"Error stopping audio stream: {e}")

    def __del__(self):
        """Cleanup when audio engine is destroyed."""
        try:
            self.stop_stream()
        except:
            pass  # Ignore errors during cleanup

    def generate_tone(self, source_pos, freq, amp):
        """Generate a spatialized tone for all speakers with proper 0-based channel mapping."""
        # Calculate gains and delays for all speakers
        gains, delays = self.spat_engine.calculate_gains_delays(source_pos)

        # Generate the base tone
        N = int(self.tone_duration * self.sample_rate)
        t = np.arange(N) / self.sample_rate

        # Create multi-channel output - ENSURE CORRECT CHANNEL COUNT
        output = np.zeros((N, self.num_channels))

        # Apply fade in/out window
        window = np.ones(N)
        if N > self.fade_len * 2:
            ramp = 0.5 * (1 - np.cos(np.pi * np.arange(self.fade_len) / self.fade_len))
            window[:self.fade_len] = ramp
            window[-self.fade_len:] = ramp[::-1]

        for i, speaker in enumerate(self.config.speakers):
            channel = speaker['channel']
            gain = gains[i]
            delay = delays[i]

            if gain > 0.001:  # Only process if significant gain
                # Apply delay (simplified - just phase shift for now)
                if delay != 0:
                    tone = amp * gain * np.sin(2 * np.pi * freq * (t - delay))
                else:
                    tone = amp * gain * np.sin(2 * np.pi * freq * t)

                # Apply window
                tone *= window

                # CRITICAL: Ensure we don't exceed channel count and use 0-based indexing
                if 0 <= channel < self.num_channels:
                    output[:, channel] = tone
                    # Debug: print active channels
                    if gain > 0.1:  # Only print for significant activity
                        print(f"Active: Speaker {speaker['id']} -> Channel {channel} (gain: {gain:.3f})")
                else:
                    print(
                        f"WARNING: Speaker {speaker['id']} channel {channel} exceeds available channels (0-{self.num_channels - 1})")

        return output

    def play_tone(self, source_pos, freq, amp):
        """Play a tone at the specified position."""
        # Always generate the buffer first
        buffer = self.generate_tone(source_pos, freq, amp)

        if self.stream is None:
            self.start_stream()

        if self.stream is not None:
            try:
                self.stream.write(buffer.astype('float32'))
            except Exception as e:
                print(f"Error writing to audio stream: {e}")

        return buffer  # Return for compatibility with existing code

    def generate_circle_buffer(self, radius, duration, steps, freq, amp):
        """Generate a seamless circular sweep buffer for multi-channel system."""
        N = int(duration * self.sample_rate)
        t = np.arange(N) / self.sample_rate

        # Calculate positions for the entire circular path
        ang = 2 * np.pi * (t / duration)
        x = radius * np.sin(ang)
        y = radius * np.cos(ang)

        # Pre-calculate all positions
        positions = np.column_stack([x, y])

        # Create multi-channel output
        output = np.zeros((N, self.num_channels))

        # Generate continuous sine wave
        continuous_sine = np.sin(2 * np.pi * freq * t)

        # Process in segments for efficiency but maintain continuity
        segment_size = int(self.sample_rate * 0.01)  # 10ms segments

        for i in range(0, N, segment_size):
            end_idx = min(i + segment_size, N)
            segment_length = end_idx - i

            # Use position at middle of segment for stable spatialization
            mid_idx = i + segment_length // 2
            if mid_idx >= N:
                mid_idx = N - 1

            pos = positions[mid_idx]

            # Calculate gains and delays for this position
            gains, delays = self.spat_engine.calculate_gains_delays(pos)

            # Generate tone for each channel
            for j, speaker in enumerate(self.config.speakers):
                channel = speaker['channel']
                gain = gains[j]
                delay = delays[j]

                if gain > 0.001 and 0 <= channel < self.num_channels:
                    # Get the continuous sine wave segment
                    if delay != 0:
                        # Apply delay by phase shifting
                        delay_samples = int(delay * self.sample_rate)
                        if i - delay_samples >= 0:
                            segment_start = i - delay_samples
                            segment_end = end_idx - delay_samples
                            if segment_end <= N:
                                tone_segment = amp * gain * continuous_sine[segment_start:segment_end]
                            else:
                                tone_segment = amp * gain * continuous_sine[i:end_idx]
                        else:
                            tone_segment = amp * gain * continuous_sine[i:end_idx]
                    else:
                        tone_segment = amp * gain * continuous_sine[i:end_idx]

                    # Add to output buffer
                    output[i:end_idx, channel] += tone_segment

        return output

    def generate_freq_ramp_buffer(self, pos, start_freq, end_freq, duration, amp):
        """Generate a seamless frequency sweep buffer at a fixed position."""
        N = int(duration * self.sample_rate)
        t = np.arange(N) / self.sample_rate

        # Linear frequency ramp
        freq_t = start_freq + (end_freq - start_freq) * (t / duration)

        # Calculate phase by integrating frequency
        phase = 2 * np.pi * np.cumsum(freq_t) / self.sample_rate

        # Calculate gains and delays for fixed position
        gains, delays = self.spat_engine.calculate_gains_delays(pos)

        # Create multi-channel buffer
        output = np.zeros((N, self.num_channels))

        # Apply fade in/out
        window = np.ones(N)
        if N > self.fade_len * 2:
            fade_len = self.fade_len
            ramp = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            window[:fade_len] = ramp
            window[-fade_len:] = ramp[::-1]

        # Generate tone for each channel
        for i, speaker in enumerate(self.config.speakers):
            channel = speaker['channel']
            gain = gains[i]
            delay = delays[i]

            if gain > 0.001 and 0 <= channel < self.num_channels:
                # Generate tone with delay
                if delay != 0:
                    tone = amp * gain * np.sin(phase - 2 * np.pi * freq_t * delay)
                else:
                    tone = amp * gain * np.sin(phase)

                # Apply window
                tone *= window

                # Add to buffer
                output[:, channel] = tone

        return output

    def generate_path_freq_ramp_buffer(self, points, mode, start_freq, end_freq, duration, steps, amp):
        """Generate a buffer that combines position movement and frequency ramping."""
        N = int(duration * self.sample_rate)
        t = np.arange(N) / self.sample_rate
        normalized_t = t / duration

        # Calculate positions along the path
        positions = np.zeros((N, 2))

        if mode == 'CURVED' and len(points) == 3:
            # Quadratic Bézier via midpoint
            P0, Pm, P1 = points[0], points[1], points[2]
            for i, nt in enumerate(normalized_t):
                positions[i] = (1 - nt) ** 2 * P0 + 2 * (1 - nt) * nt * Pm + nt ** 2 * P1
        else:
            # Linear interpolation between first and last points
            P0, P1 = points[0], points[-1]
            for i, nt in enumerate(normalized_t):
                positions[i] = P0 * (1 - nt) + P1 * nt

        # Linear frequency ramp
        freq_t = start_freq + (end_freq - start_freq) * normalized_t

        # Calculate phase by integrating frequency
        phase = 2 * np.pi * np.cumsum(freq_t) / self.sample_rate

        # Pre-allocate buffer
        output = np.zeros((N, self.num_channels))

        # Apply fade in/out
        window = np.ones(N)
        if N > self.fade_len * 2:
            fade_len = self.fade_len
            ramp = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
            window[:fade_len] = ramp
            window[-fade_len:] = ramp[::-1]

        # Generate sound for segments to handle changing position
        segment_size = int(self.sample_rate * 0.01)  # 10ms segments

        for i in range(0, N, segment_size):
            end_idx = min(i + segment_size, N)
            segment_length = end_idx - i

            # Use position at middle of segment
            mid_idx = i + segment_length // 2
            pos = positions[mid_idx]

            # Calculate gains for this position
            gains, delays = self.spat_engine.calculate_gains_delays(pos)

            # Generate tone for each channel
            for j, speaker in enumerate(self.config.speakers):
                channel = speaker['channel']
                gain = gains[j]
                delay = delays[j]

                if gain > 0.001 and 0 <= channel < self.num_channels:
                    # Generate tone segment with delay
                    if delay != 0:
                        tone_segment = amp * gain * np.sin(phase[i:end_idx] - 2 * np.pi * freq_t[i:end_idx] * delay)
                    else:
                        tone_segment = amp * gain * np.sin(phase[i:end_idx])

                    # Apply window
                    tone_segment *= window[i:end_idx]

                    # Add to buffer
                    output[i:end_idx, channel] += tone_segment

        return output, positions


# === MAIN INTERFACE ===
class MultiSpeakerSpatialiser:
    def __init__(self, config_file=None):
        self.speaker_config = SpeakerConfig()

        if config_file:
            # FIXED: Only load config, don't create duplicate audio engine
            self.load_config(config_file)
        else:
            # Only create audio engine if no config file was loaded
            self.audio_engine = MultiSpeakerAudioEngine(self.speaker_config)

        # Update global parameters for compatibility
        global sample_rate, tone_duration, itd_exaggeration, ild_exponent
        sample_rate = self.audio_engine.sample_rate
        tone_duration = self.audio_engine.tone_duration
        itd_exaggeration = self.audio_engine.spat_engine.itd_exaggeration
        ild_exponent = self.audio_engine.spat_engine.ild_exponent

        self.print_startup_info()

    def load_config(self, config_file):
        """Load configuration from file."""
        success = self.speaker_config.load_from_file(config_file)
        if success:
            # FIXED: Stop any existing audio engine first
            if hasattr(self, 'audio_engine') and self.audio_engine:
                self.audio_engine.stop_stream()

            # Create new audio engine with new config
            self.audio_engine = MultiSpeakerAudioEngine(self.speaker_config)
            print(f"Loaded configuration from {config_file}")
        return success

    def save_config(self, config_file):
        """Save current configuration to file."""
        return self.speaker_config.save_to_file(config_file)

    def set_parameters(self, **kwargs):
        """Set audio and spatialization parameters."""
        self.audio_engine.set_parameters(**kwargs)

        # Update global parameters for compatibility
        global tone_duration, itd_exaggeration, ild_exponent
        if 'tone_duration' in kwargs:
            tone_duration = kwargs['tone_duration']
        if 'itd_exaggeration' in kwargs:
            itd_exaggeration = kwargs['itd_exaggeration']
        if 'ild_exponent' in kwargs:
            ild_exponent = kwargs['ild_exponent']

    def play_sound(self, x, y, freq=440, amp=0.5):
        """Play a sound at position (x, y)."""
        source_pos = np.array([x, y])
        self.audio_engine.play_tone(source_pos, freq, amp)

    def start(self):
        """Start the audio system."""
        self.audio_engine.start_stream()

    def stop(self):
        """Stop the audio system."""
        self.audio_engine.stop_stream()

    def print_startup_info(self):
        """Print startup information."""
        print(f"Multi-Speaker Spatialiser Ready!")
        print(f"  Configuration: {self.speaker_config.config_name}")
        print(f"  Speakers: {len(self.speaker_config.speakers)}")
        print(f"  Channels: {self.audio_engine.num_channels} (0-based: 0 to {self.audio_engine.num_channels - 1})")
        print(f"  Method: {self.speaker_config.method}")
        if self.speaker_config.speakers:
            positions = self.speaker_config.get_speaker_positions()
            x_range = np.ptp(positions[:, 0]) * 1000  # Convert to mm
            y_range = np.ptp(positions[:, 1]) * 1000
            print(f"  Coverage: {x_range:.1f}mm x {y_range:.1f}mm")

        # Print tactile grid improvement message
        if self.speaker_config.method == 'tactile_grid':
            print("  IMPROVED: Smooth tactile grid spatialization (no more clicking/jumping)")

    def print_info(self):
        """Print detailed configuration information."""
        self.speaker_config.print_info()
        print(f"\nChannel Map (for debugging):")
        channel_map = self.speaker_config.get_channel_map()
        for ch in sorted(channel_map.keys()):
            info = channel_map[ch]
            print(f"  Channel {ch}: {info['id']} at ({info['pos'][0] * 1000:.1f}, {info['pos'][1] * 1000:.1f})mm")


# === COMPATIBILITY FUNCTIONS (for original system) ===
def set_visualizer_callback(callback):
    """Set a callback function to be called when position changes."""
    global visualizer_callback
    visualizer_callback = callback


def update_position(position, action=None):
    """Update the current position and notify visualizer if callback exists."""
    global current_position

    with position_lock:
        current_position = position.copy()

    # Notify visualizer
    if visualizer_callback:
        visualizer_callback(position, action)


def generate_tactile_tone(source_pos, freq, amp):
    """Generate a tactile tone (compatibility with original system)."""
    # Update position for visualization
    update_position(source_pos, {'type': 'SOUND', 'freq': freq, 'amp': amp})

    # Use the global spatialiser if available
    if hasattr(generate_tactile_tone, 'spatialiser'):
        return generate_tactile_tone.spatialiser.audio_engine.generate_tone(source_pos, freq, amp)
    else:
        # Fallback to simple stereo generation
        N = int(tone_duration * sample_rate)
        t = np.arange(N) / sample_rate
        tone = amp * np.sin(2 * np.pi * freq * t)

        # Simple stereo panning
        pan = np.clip(source_pos[0] + 0.5, 0, 1)  # -0.5 to 0.5 -> 0 to 1
        left = tone * (1 - pan)
        right = tone * pan

        return np.column_stack([left, right])


def generate_circle_buffer(radius, duration, steps, freq, amp):
    """Generate a seamless circular sweep buffer."""
    if hasattr(generate_tactile_tone, 'spatialiser'):
        return generate_tactile_tone.spatialiser.audio_engine.generate_circle_buffer(radius, duration, steps, freq, amp)
    else:
        # Fallback to simple stereo
        N = int(duration * sample_rate)
        t = np.arange(N) / sample_rate
        left = amp * np.sin(2 * np.pi * freq * t)
        right = amp * np.sin(2 * np.pi * freq * t)
        return np.column_stack([left, right])


# === SCRIPT PARSING (INTEGRATED FROM ORIGINAL) ===
def is_valid_float(s):
    """Check if string is a valid float."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def parse_script(lines):
    """Parse a script file and return a list of action tuples."""
    actions = []
    global itd_exaggeration, ild_exponent, tone_duration

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('#'):
            continue

        # Config assignment
        m = re.match(r'(\w+)\s*=\s*([0-9.]+)', line)
        if m:
            key, val = m.group(1).lower(), float(m.group(2))
            if key == 'itd_exaggeration':
                itd_exaggeration = val
            elif key == 'ild_exponent':
                ild_exponent = val
            elif key == 'tone_duration':
                tone_duration = val
            continue

        parts = line.split()
        cmd = parts[0].upper()

        if cmd == 'WAIT':
            try:
                actions.append(('WAIT', float(parts[1])))
            except (ValueError, IndexError):
                print(f"Warning: Invalid WAIT command: {line}")
                continue

        elif cmd == 'JUMP':
            try:
                coords = parts[1].split(',')
                if len(coords) != 2 or not all(is_valid_float(c) for c in coords):
                    print(f"Warning: Invalid JUMP coordinates: {line}")
                    continue
                x, y = map(float, coords)
                actions.append(('JUMP', np.array([x, y])))
            except (ValueError, IndexError):
                print(f"Warning: Invalid JUMP command: {line}")
                continue

        elif cmd == 'SOUND':
            try:
                coords = parts[1].split(',')
                if len(coords) != 2 or not all(is_valid_float(c) for c in coords):
                    print(f"Warning: Invalid SOUND coordinates: {line}")
                    continue
                pos = np.array([float(coords[0]), float(coords[1])])

                freq_match = re.search(r'FREQ=([0-9.]+)', line)
                amp_match = re.search(r'AMP=([0-9.]+)', line)

                if not freq_match or not amp_match:
                    print(f"Warning: Missing FREQ or AMP in SOUND command: {line}")
                    continue

                freq = float(freq_match.group(1))
                amp = float(amp_match.group(1))
                actions.append(('SOUND', pos, freq, amp))
            except (ValueError, IndexError):
                print(f"Warning: Invalid SOUND command: {line}")
                continue

        elif cmd == 'ARC':
            try:
                # Extract points (2 or 3 points)
                point_matches = re.findall(r'(-?[0-9.]+),(-?[0-9.]+)', line)

                if len(point_matches) < 2:
                    print(f"Warning: ARC requires at least 2 points: {line}")
                    continue

                if len(point_matches) > 3:
                    print(f"Warning: ARC accepts at most 3 points. Using first 3.")
                    point_matches = point_matches[:3]

                # Convert points to numpy arrays
                points = []
                for x_str, y_str in point_matches:
                    points.append(np.array([float(x_str), float(y_str)]))

                # Extract parameters
                duration_match = re.search(r'DURATION=([0-9.]+)', line)
                steps_match = re.search(r'STEPS=([0-9]+)', line)
                freq_match = re.search(r'FREQ=([0-9.]+)', line)
                amp_match = re.search(r'AMP=([0-9.]+)', line)

                if not all([duration_match, steps_match, freq_match, amp_match]):
                    print(f"Warning: Missing parameters in ARC command: {line}")
                    continue

                duration = float(duration_match.group(1))
                steps = int(steps_match.group(1))
                freq = float(freq_match.group(1))
                amp = float(amp_match.group(1))

                # Check for MODE parameter
                mode_match = re.search(r'MODE=(\w+)', line)
                mode = mode_match.group(1).upper() if mode_match else 'STRAIGHT'

                actions.append(('ARC', points, duration, steps, freq, amp, mode))
            except (ValueError, IndexError) as e:
                print(f"Warning: Invalid ARC command: {line} - {e}")
                continue

        elif cmd == 'CIRCLE_SMOOTH':
            try:
                radius_match = re.search(r'RADIUS=([0-9.]+)', line)
                duration_match = re.search(r'DURATION=([0-9.]+)', line)
                steps_match = re.search(r'STEPS=([0-9]+)', line)
                freq_match = re.search(r'FREQ=([0-9.]+)', line)
                amp_match = re.search(r'AMP=([0-9.]+)', line)

                if not all([radius_match, duration_match, steps_match, freq_match, amp_match]):
                    print(f"Warning: Missing parameters in CIRCLE_SMOOTH command: {line}")
                    continue

                radius = float(radius_match.group(1))
                duration = float(duration_match.group(1))
                steps = int(steps_match.group(1))
                freq = float(freq_match.group(1))
                amp = float(amp_match.group(1))

                actions.append(('CIRCLE_SMOOTH', radius, duration, steps, freq, amp))
            except (ValueError, IndexError):
                print(f"Warning: Invalid CIRCLE_SMOOTH command: {line}")
                continue

        elif cmd == 'FREQ_RAMP':
            try:
                # Extract position
                pos_match = re.search(r'POS=(-?[0-9.]+),(-?[0-9.]+)', line)

                # Extract parameters with regex
                start_freq_match = re.search(r'START_FREQ=([0-9.]+)', line)
                end_freq_match = re.search(r'END_FREQ=([0-9.]+)', line)
                duration_match = re.search(r'DURATION=([0-9.]+)', line)
                steps_match = re.search(r'STEPS=([0-9]+)', line)
                amp_match = re.search(r'AMP=([0-9.]+)', line)

                if not pos_match:
                    print(f"Warning: Missing position in FREQ_RAMP command: {line}")
                    continue

                if not all([start_freq_match, end_freq_match, duration_match, steps_match, amp_match]):
                    print(f"Warning: Missing parameters in FREQ_RAMP command: {line}")
                    continue

                pos = np.array([float(pos_match.group(1)), float(pos_match.group(2))])
                start_freq = float(start_freq_match.group(1))
                end_freq = float(end_freq_match.group(1))
                duration = float(duration_match.group(1))
                steps = int(steps_match.group(1))
                amp = float(amp_match.group(1))

                actions.append(('FREQ_RAMP', pos, start_freq, end_freq, duration, steps, amp))
            except (ValueError, IndexError):
                print(f"Warning: Invalid FREQ_RAMP command: {line}")
                continue

        elif cmd == 'FREQ_RAMP_SMOOTH':
            try:
                # Extract position
                pos_match = re.search(r'POS=(-?[0-9.]+),(-?[0-9.]+)', line)

                # Extract parameters with regex
                start_freq_match = re.search(r'START_FREQ=([0-9.]+)', line)
                end_freq_match = re.search(r'END_FREQ=([0-9.]+)', line)
                duration_match = re.search(r'DURATION=([0-9.]+)', line)
                amp_match = re.search(r'AMP=([0-9.]+)', line)

                if not pos_match:
                    print(f"Warning: Missing position in FREQ_RAMP_SMOOTH command: {line}")
                    continue

                if not all([start_freq_match, end_freq_match, duration_match, amp_match]):
                    print(f"Warning: Missing parameters in FREQ_RAMP_SMOOTH command: {line}")
                    continue

                pos = np.array([float(pos_match.group(1)), float(pos_match.group(2))])
                start_freq = float(start_freq_match.group(1))
                end_freq = float(end_freq_match.group(1))
                duration = float(duration_match.group(1))
                amp = float(amp_match.group(1))

                actions.append(('FREQ_RAMP_SMOOTH', pos, start_freq, end_freq, duration, amp))
            except (ValueError, IndexError):
                print(f"Warning: Invalid FREQ_RAMP_SMOOTH command: {line}")
                continue

        elif cmd == 'PATH_FREQ_RAMP':
            try:
                # Extract points (2 or 3 points)
                point_matches = re.findall(r'(-?[0-9.]+),(-?[0-9.]+)', line)

                if len(point_matches) < 2:
                    print(f"Warning: PATH_FREQ_RAMP requires at least 2 points: {line}")
                    continue

                if len(point_matches) > 3:
                    print(f"Warning: PATH_FREQ_RAMP accepts at most 3 points. Using first 3.")
                    point_matches = point_matches[:3]

                # Convert points to numpy arrays
                points = []
                for x_str, y_str in point_matches:
                    points.append(np.array([float(x_str), float(y_str)]))

                # Extract parameters
                start_freq_match = re.search(r'START_FREQ=([0-9.]+)', line)
                end_freq_match = re.search(r'END_FREQ=([0-9.]+)', line)
                duration_match = re.search(r'DURATION=([0-9.]+)', line)
                steps_match = re.search(r'STEPS=([0-9]+)', line)
                amp_match = re.search(r'AMP=([0-9.]+)', line)

                if not all([start_freq_match, end_freq_match, duration_match, steps_match, amp_match]):
                    print(f"Warning: Missing parameters in PATH_FREQ_RAMP command: {line}")
                    continue

                start_freq = float(start_freq_match.group(1))
                end_freq = float(end_freq_match.group(1))
                duration = float(duration_match.group(1))
                steps = int(steps_match.group(1))
                amp = float(amp_match.group(1))

                # Check for MODE parameter
                mode_match = re.search(r'MODE=(\w+)', line)
                mode = mode_match.group(1).upper() if mode_match else 'STRAIGHT'

                actions.append(('PATH_FREQ_RAMP', points, start_freq, end_freq, duration, steps, amp, mode))
            except (ValueError, IndexError) as e:
                print(f"Warning: Invalid PATH_FREQ_RAMP command: {line} - {e}")
                continue

        else:
            print(f"Warning: Unknown command: {cmd}")

    return actions


def execute(actions, with_visualization=False):
    """Execute a sequence of parsed actions."""
    # FIXED: Use existing spatialiser if available, otherwise create one with warning
    if hasattr(generate_tactile_tone, 'spatialiser') and generate_tactile_tone.spatialiser:
        spatialiser = generate_tactile_tone.spatialiser
        print("Using existing spatialiser configuration")
    else:
        print("WARNING: No spatialiser found, creating default configuration")
        spatialiser = MultiSpeakerSpatialiser()
        generate_tactile_tone.spatialiser = spatialiser

    # FIXED: Make sure we're not starting multiple streams
    if spatialiser.audio_engine.stream is None:
        spatialiser.start()

    current_pos = np.array([0.0, 0.0])

    for act in actions:
        cmd = act[0]

        if cmd == 'WAIT':
            time.sleep(act[1])

        elif cmd == 'JUMP':
            current_pos = act[1]
            update_position(current_pos, {'type': 'JUMP'})

        elif cmd == 'SOUND':
            _, pos, freq, amp = act
            current_pos = pos
            update_position(current_pos, {'type': 'SOUND', 'freq': freq, 'amp': amp})

            # Generate and play the sound
            spatialiser.audio_engine.play_tone(pos, freq, amp)

        elif cmd == 'ARC':
            _, points, duration, steps, freq, amp, mode = act

            if steps <= 0:
                print("Warning: ARC with steps <= 0, skipping")
                continue

            # Calculate the time for each step
            step_time = duration / steps

            # Handle interpolation based on number of points and mode
            for i in range(steps):
                t = i / (steps - 1) if steps > 1 else 0

                if mode == 'CURVED' and len(points) == 3:
                    # Quadratic Bézier via midpoint
                    P0, Pm, P1 = points[0], points[1], points[2]
                    pos = (1 - t) ** 2 * P0 + 2 * (1 - t) * t * Pm + t ** 2 * P1
                else:
                    # Linear interpolation between first and last points
                    P0, P1 = points[0], points[-1]
                    pos = P0 * (1 - t) + P1 * t

                current_pos = pos
                update_position(current_pos, {'type': 'ARC', 'freq': freq, 'amp': amp})

                # Play sound
                spatialiser.audio_engine.play_tone(pos, freq, amp)

                if i < steps - 1:  # Don't sleep after the last point
                    time.sleep(step_time)

        elif cmd == 'CIRCLE_SMOOTH':
            _, radius, duration, steps, freq, amp = act

            # Generate the buffer
            buf = spatialiser.audio_engine.generate_circle_buffer(radius, duration, steps, freq, amp)

            # Start audio playback and visualization synchronously
            if with_visualization:
                import threading

                # Start audio playback in a separate thread
                def play_audio():
                    if spatialiser.audio_engine.stream:
                        spatialiser.audio_engine.stream.write(buf.astype('float32'))

                audio_thread = threading.Thread(target=play_audio)
                audio_thread.daemon = True
                audio_thread.start()

                # Update visualization in sync with audio
                start_time = time.time()
                vis_steps = min(steps, 200)  # Limit to reasonable number of updates

                for i in range(vis_steps):
                    # Calculate current position based on elapsed time
                    elapsed = time.time() - start_time
                    progress = min(1.0, elapsed / duration)

                    # Calculate position on circle
                    angle = 2 * np.pi * progress
                    x = radius * np.sin(angle)
                    y = radius * np.cos(angle)
                    pos = np.array([x, y])

                    update_position(pos, {'type': 'CIRCLE', 'freq': freq, 'amp': amp})

                    # Sleep for smooth animation
                    time.sleep(duration / vis_steps)

                # Wait for audio to complete
                audio_thread.join()

            else:
                # Without visualization, just play the audio
                if spatialiser.audio_engine.stream:
                    spatialiser.audio_engine.stream.write(buf.astype('float32'))

                    # Still need to wait for the duration
                    time.sleep(duration)

        elif cmd == 'FREQ_RAMP':
            _, pos, start_freq, end_freq, duration, steps, amp = act

            if steps <= 0:
                print("Warning: FREQ_RAMP with steps <= 0, skipping")
                continue

            # Calculate the time for each step
            step_time = duration / steps

            # Generate frequencies for each step
            for i in range(steps):
                t = i / (steps - 1) if steps > 1 else 0

                # Linear interpolation of frequency
                freq = start_freq * (1 - t) + end_freq * t

                current_pos = pos
                update_position(current_pos, {'type': 'FREQ_RAMP', 'freq': freq, 'amp': amp})

                # Play sound
                spatialiser.audio_engine.play_tone(pos, freq, amp)

                if i < steps - 1:  # Don't sleep after the last point
                    time.sleep(step_time)

        elif cmd == 'FREQ_RAMP_SMOOTH':
            _, pos, start_freq, end_freq, duration, amp = act

            # Generate a continuous buffer with smooth frequency ramping
            buf = spatialiser.audio_engine.generate_freq_ramp_buffer(pos, start_freq, end_freq, duration, amp)

            # Start audio playback and visualization synchronously
            if with_visualization:
                import threading

                # Start audio playback in a separate thread
                def play_audio():
                    if spatialiser.audio_engine.stream:
                        spatialiser.audio_engine.stream.write(buf.astype('float32'))

                audio_thread = threading.Thread(target=play_audio)
                audio_thread.daemon = True
                audio_thread.start()

                # Update visualization in sync with audio
                start_time = time.time()
                vis_steps = 100  # Reasonable number of updates

                for i in range(vis_steps):
                    # Calculate current frequency based on elapsed time
                    elapsed = time.time() - start_time
                    progress = min(1.0, elapsed / duration)

                    # Calculate current frequency
                    freq = start_freq + (end_freq - start_freq) * progress

                    update_position(pos, {'type': 'FREQ_RAMP_SMOOTH', 'freq': freq, 'amp': amp})

                    # Sleep for smooth animation
                    time.sleep(duration / vis_steps)

                # Wait for audio to complete
                audio_thread.join()

            else:
                # Without visualization, just play the audio
                if spatialiser.audio_engine.stream:
                    spatialiser.audio_engine.stream.write(buf.astype('float32'))

                    # Still need to wait for the duration
                    time.sleep(duration)

        elif cmd == 'PATH_FREQ_RAMP':
            _, points, start_freq, end_freq, duration, steps, amp, mode = act

            if steps <= 0:
                print("Warning: PATH_FREQ_RAMP with steps <= 0, skipping")
                continue

            # Generate a continuous buffer with both position and frequency changes
            buf, positions = spatialiser.audio_engine.generate_path_freq_ramp_buffer(
                points, mode, start_freq, end_freq, duration, steps, amp)

            # Start audio playback and visualization synchronously
            if with_visualization:
                import threading

                # Start audio playback in a separate thread
                def play_audio():
                    if spatialiser.audio_engine.stream:
                        spatialiser.audio_engine.stream.write(buf.astype('float32'))

                audio_thread = threading.Thread(target=play_audio)
                audio_thread.daemon = True
                audio_thread.start()

                # Update visualization in sync with audio
                start_time = time.time()
                vis_steps = min(100, len(positions) // 10)  # Reasonable number of updates

                for i in range(vis_steps):
                    # Calculate current position and frequency based on elapsed time
                    elapsed = time.time() - start_time
                    progress = min(1.0, elapsed / duration)

                    # Calculate position index
                    pos_idx = int(progress * (len(positions) - 1))
                    if pos_idx >= len(positions):
                        pos_idx = len(positions) - 1

                    pos = positions[pos_idx]
                    freq = start_freq + (end_freq - start_freq) * progress

                    update_position(pos, {'type': 'PATH_FREQ_RAMP', 'freq': freq, 'amp': amp})

                    # Sleep for smooth animation
                    time.sleep(duration / vis_steps)

                # Wait for audio to complete
                audio_thread.join()

            else:
                # Without visualization, just play the audio
                if spatialiser.audio_engine.stream:
                    spatialiser.audio_engine.stream.write(buf.astype('float32'))

                    # Still need to wait for the duration
                    time.sleep(duration)

    # Note: Don't automatically stop the spatialiser here to allow for reuse
    # spatialiser.stop()


def execute_with_visualization(actions):
    """Execute script with visualization support."""
    return execute(actions, with_visualization=True)


# === CONFIGURATION FILE GENERATORS ===
def create_example_configs():
    """Create example configuration files with corrected 0-based channel assignments."""

    # 1. Default 4x4 grid (40mm spacing) - FIXED CHANNELS
    with open('config_4x4_grid.txt', 'w') as f:
        f.write("""# 4x4 Tactile Grid Configuration
# 40mm spacing between speaker centers
# Optimized for tactile/haptic feedback
# CHANNELS START AT 0

config_name = 4x4_tactile_grid
method = tactile_grid

# Create 4x4 grid with 40mm spacing
GRID SIZE=4 SPACING=0.04 OFFSET=0.0,0.0

# This creates a 120mm x 120mm grid with speakers at:
# Row 0: (-0.060,-0.060), (-0.020,-0.060), (0.020,-0.060), (0.060,-0.060)
# Row 1: (-0.060,-0.020), (-0.020,-0.020), (0.020,-0.020), (0.060,-0.020)
# Row 2: (-0.060,0.020), (-0.020,0.020), (0.020,0.020), (0.060,0.020)
# Row 3: (-0.060,0.060), (-0.020,0.060), (0.020,0.060), (0.060,0.060)

# Channels are assigned as (0-based):
# CH0  CH1  CH2  CH3     (bottom row)
# CH4  CH5  CH6  CH7     
# CH8  CH9  CH10 CH11    
# CH12 CH13 CH14 CH15    (top row)
""")

    # 2. 2x2 test grid (4 channels) - FIXED CHANNELS
    with open('config_2x2_test.txt', 'w') as f:
        f.write("""# 2x2 Test Grid Configuration
# 40mm spacing for testing with limited channels
# CHANNELS START AT 0

config_name = 2x2_test_grid
method = tactile_grid

# Create 2x2 grid with 40mm spacing
GRID SIZE=2 SPACING=0.04 OFFSET=0.0,0.0

# This creates speakers at:
# (-0.020,-0.020), (0.020,-0.020)  (bottom row)
# (-0.020,0.020), (0.020,0.020)    (top row)

# Channels: CH0, CH1, CH2, CH3 (0-based)
""")

    # 3. 8-speaker circle - FIXED CHANNELS
    with open('config_octagon.txt', 'w') as f:
        f.write("""# Octagon Speaker Array
# 8 speakers in a circle for room audio
# CHANNELS START AT 0

config_name = octagon_room
method = vbap

# Create 8-speaker circle with 2m radius
CIRCLE COUNT=8 RADIUS=2.0 OFFSET=0.0,0.0

# Channels: CH0-CH7 (0-based)
""")

    # 4. Stereo pair - FIXED CHANNELS
    with open('config_stereo.txt', 'w') as f:
        f.write("""# Stereo Speaker Configuration
# Standard left/right speakers
# CHANNELS START AT 0

config_name = stereo_pair
method = itd_ild

# Left and right speakers (0-based channels)
SPEAKER LEFT  -0.5,0.0 CHANNEL=0 DESCRIPTION="Left speaker"
SPEAKER RIGHT  0.5,0.0 CHANNEL=1 DESCRIPTION="Right speaker"
""")

    # 5. 8x8 high-resolution grid - FIXED CHANNELS
    with open('config_8x8_grid.txt', 'w') as f:
        f.write("""# 8x8 High-Resolution Tactile Grid
# 20mm spacing for detailed tactile feedback
# CHANNELS START AT 0

config_name = 8x8_tactile_grid
method = nearest_neighbor

# Create 8x8 grid with 20mm spacing
GRID SIZE=8 SPACING=0.02 OFFSET=0.0,0.0

# This creates a 140mm x 140mm grid with 64 speakers
# Channels: CH0-CH63 (0-based)
""")

    # 6. Development configuration - FIXED CHANNELS
    with open('config_development.txt', 'w') as f:
        f.write("""# Development Configuration
# Minimal setup for testing and development
# CHANNELS START AT 0

config_name = development
method = distance_pan

# Just 4 speakers for easy testing (0-based channels)
SPEAKER TL -0.02,0.02 CHANNEL=0 DESCRIPTION="Top left"
SPEAKER TR  0.02,0.02 CHANNEL=1 DESCRIPTION="Top right"
SPEAKER BL -0.02,-0.02 CHANNEL=2 DESCRIPTION="Bottom left"
SPEAKER BR  0.02,-0.02 CHANNEL=3 DESCRIPTION="Bottom right"
""")

    print("Created example configuration files with 0-based channel assignments:")
    print("  - config_4x4_grid.txt (default 4x4 tactile grid, 40mm spacing, CH0-CH15)")
    print("  - config_2x2_test.txt (2x2 test grid, CH0-CH3)")
    print("  - config_octagon.txt (8-speaker circle, CH0-CH7)")
    print("  - config_stereo.txt (standard stereo, CH0-CH1)")
    print("  - config_8x8_grid.txt (high-resolution 8x8 grid, CH0-CH63)")
    print("  - config_development.txt (development/debug, CH0-CH3)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Multi-Speaker Spatialiser')
    parser.add_argument('script', nargs='?', help='Tactile script file to execute')
    parser.add_argument('--config', help='Speaker configuration file')
    parser.add_argument('--create-configs', action='store_true',
                        help='Create example configuration files')
    parser.add_argument('--info', action='store_true',
                        help='Show configuration info and exit')
    parser.add_argument('--interactive', action='store_true',
                        help='Enter interactive mode')
    parser.add_argument('--visualize', '-v', action='store_true',
                        help='Launch with visualization')

    args = parser.parse_args()

    if args.create_configs:
        create_example_configs()
    elif args.info:
        spatialiser = MultiSpeakerSpatialiser(args.config)
        spatialiser.print_info()
    elif args.script:
        # Execute a tactile script
        spatialiser = MultiSpeakerSpatialiser(args.config)

        # FIXED: Set the global spatialiser BEFORE any execute calls
        generate_tactile_tone.spatialiser = spatialiser

        if args.visualize:
            # Launch the visualizer and let IT handle execution
            import subprocess
            import sys

            try:
                visualizer_script = 'run_with_visualizer_multispeaker.py'
                cmd = [sys.executable, visualizer_script, args.script]
                if args.config:
                    cmd.extend(['--config', args.config])

                print("Launching visualizer to handle script execution...")
                print(f"Script: {args.script}")
                print(f"Config: {args.config if args.config else 'default'}")
                print("The visualizer will execute the script. Close the visualizer window to stop.")

                # Wait for the visualizer process to complete
                process = subprocess.Popen(cmd)
                process.wait()  # This blocks until visualizer closes
                print("Visualizer closed.")

            except Exception as e:
                print(f"Could not launch visualizer: {e}")
                print("Falling back to execution without visualization...")
                # Fallback to non-visualized execution
                try:
                    with open(args.script, 'r') as f:
                        lines = f.read().splitlines()
                    actions = parse_script(lines)
                    execute(actions)
                except Exception as fallback_error:
                    print(f"Fallback execution failed: {fallback_error}")

            # FIXED: Don't execute the script again in main process when using visualizer
            # The visualizer process handles all execution

        else:
            # Non-visualized execution
            try:
                with open(args.script, 'r') as f:
                    lines = f.read().splitlines()

                actions = parse_script(lines)
                print(f"Executing script: {args.script}")
                print(f"Actions: {len(actions)}")
                print(f"Using configuration: {spatialiser.speaker_config.config_name}")

                execute(actions)

            except Exception as e:
                print(f"Error executing script: {e}")
            finally:
                # FIXED: Cleanup after execution
                try:
                    spatialiser.stop()
                except:
                    pass

    elif args.interactive:
        # Interactive mode
        spatialiser = MultiSpeakerSpatialiser(args.config)
        spatialiser.start()

        print("\nCommands:")
        print("  play x y freq amp  - Play sound at position (meters)")
        print("  load filename      - Load configuration file")
        print("  save filename      - Save configuration file")
        print("  info              - Show speaker info")
        print("  smooth            - Configure smooth tactile grid")
        print("  help              - Show this help")
        print("  quit              - Exit")
        print("\nExample: play 0.02 0.02 440 0.5  (20mm, 20mm)")
        print("NOTE: All channels are 0-based (first channel is 0, not 1)")
        print("FIXED: Smooth tactile grid spatialization (no more clicking/jumping)")

        try:
            while True:
                cmd = input("\n> ").strip().split()

                if not cmd:
                    continue

                if cmd[0] == 'quit':
                    break
                elif cmd[0] == 'play' and len(cmd) >= 3:
                    x, y = float(cmd[1]), float(cmd[2])
                    freq = float(cmd[3]) if len(cmd) > 3 else 440
                    amp = float(cmd[4]) if len(cmd) > 4 else 0.5
                    spatialiser.play_sound(x, y, freq, amp)
                elif cmd[0] == 'load' and len(cmd) > 1:
                    spatialiser.load_config(cmd[1])
                elif cmd[0] == 'save' and len(cmd) > 1:
                    spatialiser.save_config(cmd[1])
                elif cmd[0] == 'info':
                    spatialiser.print_info()
                elif cmd[0] == 'smooth':
                    print("Tactile Grid Smoothness Options:")
                    print("1. Default (improved smoothness)")
                    print("2. Extra smooth (Gaussian mode)")
                    print("3. More focused (less smooth, more localized)")
                    print("4. Custom parameters")

                    choice = input("Select option (1-4): ").strip()

                    if choice == '1':
                        print("Using default improved smoothness")
                    elif choice == '2':
                        spatialiser.audio_engine.spat_engine.set_tactile_grid_parameters(
                            use_gaussian=True, gaussian_sigma=0.03
                        )
                        print("Activated extra smooth mode")
                    elif choice == '3':
                        spatialiser.audio_engine.spat_engine.set_tactile_grid_parameters(
                            max_active_speakers=4, distance_power=2.0, smooth_min_distance=0.005
                        )
                        print("Activated more focused mode")
                    elif choice == '4':
                        print("Available parameters:")
                        print("- use_gaussian (True/False)")
                        print("- gaussian_sigma (0.01-0.05)")
                        print("- max_active_speakers (3-8)")
                        print("- smooth_min_distance (0.001-0.02)")
                        print("- distance_power (1.0-3.0)")
                        print("- tactile_enhancement (1.0-2.0)")
                        print("Enter parameters like: use_gaussian=True gaussian_sigma=0.025")
                        params_str = input("Parameters: ").strip()

                        if params_str:
                            try:
                                params = {}
                                for param in params_str.split():
                                    key, value = param.split('=')
                                    if key in ['use_gaussian']:
                                        params[key] = value.lower() == 'true'
                                    else:
                                        params[key] = float(value)

                                spatialiser.audio_engine.spat_engine.set_tactile_grid_parameters(**params)
                            except Exception as e:
                                print(f"Error setting parameters: {e}")

                    print("Test with: play 0.02 0.0 300 0.4 (then try play -0.02 0.0 300 0.4)")

                elif cmd[0] == 'help':
                    print("Commands:")
                    print("  play x y [freq] [amp] - Play sound at position (x,y) in meters")
                    print("  load filename         - Load speaker configuration")
                    print("  save filename         - Save current configuration")
                    print("  info                  - Show detailed speaker info")
                    print("  smooth                - Configure tactile grid smoothness")
                    print("  quit                  - Exit program")
                    print("\nExamples:")
                    print("  play 0.02 0.02 440 0.5   # 20mm right, 20mm forward")
                    print("  play -0.02 -0.02 220 0.3 # 20mm left, 20mm back")
                    print("\nIMPORTANT: All channels are 0-based!")
                    print("IMPROVED: Smooth tactile transitions (no more clicking)")
                else:
                    print("Invalid command. Type 'help' for help.")

        except KeyboardInterrupt:
            pass
        finally:
            spatialiser.stop()
            print("\nGoodbye!")
    else:
        # Default: create configs if they don't exist, then demo
        if not os.path.exists('config_4x4_grid.txt'):
            print("Creating default configuration files...")
            create_example_configs()

        spatialiser = MultiSpeakerSpatialiser('config_4x4_grid.txt')
        spatialiser.start()

        print("\nDemonstrating 4x4 grid with 40mm spacing:")
        print("Playing sounds at the four corners and center...")
        print("Channels are 0-based (first channel = 0)")
        print("IMPROVED: Smooth tactile spatialization!")

        # Demo the 4x4 grid
        positions = [
            (-0.06, -0.06, "Bottom-left"),
            (0.06, -0.06, "Bottom-right"),
            (0.06, 0.06, "Top-right"),
            (-0.06, 0.06, "Top-left"),
            (0.0, 0.0, "Center")
        ]

        for x, y, desc in positions:
            print(f"  {desc}: ({x * 1000:.0f}, {y * 1000:.0f})mm")
            spatialiser.play_sound(x, y, freq=440, amp=0.5)
            time.sleep(0.8)

        # Demo smooth movement
        print("\nDemonstrating smooth movement (left to right):")
        for i in range(10):
            x = -0.04 + (i * 0.008)  # Move from -40mm to +32mm
            spatialiser.play_sound(x, 0.0, freq=300, amp=0.4)
            time.sleep(0.2)

        spatialiser.stop()
        print("\nDemo complete. Use --interactive for interactive mode.")
        print("Remember: All channels are 0-based!")
        print("IMPROVED: Smooth tactile spatialization eliminates clicking/jumping!")
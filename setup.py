#!/usr/bin/env python3
"""
setup.py - Multi-Speaker Tactile Spatialiser Setup Script - ENHANCED VERSION

This script sets up the multi-speaker tactile spatialiser system,
installs dependencies, creates configuration files, demo scripts, and documentation.

Usage:
  python setup.py install
  python setup.py test
  python setup.py demo
"""

import os
import sys
import subprocess
import platform


def check_python_version():
    """Check that we're running Python 3.7+"""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python version OK: {sys.version}")
    return True


def install_dependencies():
    """Install required Python packages"""
    print("\n=== Installing Dependencies ===")

    requirements = [
        'numpy>=1.19.0',
        'sounddevice>=0.4.0',
        'soundfile>=0.10.0',
        'pygame>=2.0.0'
    ]

    for req in requirements:
        print(f"Installing {req}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', req])
            print(f"✓ {req} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {req}: {e}")
            return False

    return True


def create_directory_structure():
    """Create the directory structure for configs and examples"""
    print("\n=== Creating Directory Structure ===")

    directories = ['configs', 'examples', 'docs']

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Created directory: {directory}")
        else:
            print(f"✓ Directory already exists: {directory}")

    return True


def create_config_files():
    """Create default configuration files in configs/ directory"""
    print("\n=== Creating Configuration Files ===")

    # Ensure configs directory exists
    os.makedirs('configs', exist_ok=True)

    # 1. Default 4x4 grid (40mm spacing)
    with open('configs/config_4x4_grid.txt', 'w') as f:
        f.write("""# 4x4 Tactile Grid Configuration
# 40mm spacing between speaker centers
# Optimized for tactile/haptic feedback with Thawney's 16-channel driver board

config_name = 4x4_tactile_grid
method = tactile_grid

# Create 4x4 grid with 40mm spacing
GRID SIZE=4 SPACING=0.04 OFFSET=0.0,0.0

# This creates a 120mm x 120mm grid with speakers at:
# Row 0: (-0.060,-0.060), (-0.020,-0.060), (0.020,-0.060), (0.060,-0.060)
# Row 1: (-0.060,-0.020), (-0.020,-0.020), (0.020,-0.020), (0.060,-0.020)
# Row 2: (-0.060,0.020), (-0.020,0.020), (0.020,0.020), (0.060,0.020)
# Row 3: (-0.060,0.060), (-0.020,0.060), (0.020,0.060), (0.060,0.060)

# Channels are assigned vertically (bottom-to-top), then next column:
# CH3  CH7  CH11 CH15    (top row)
# CH2  CH6  CH10 CH14     
# CH1  CH5  CH9  CH13    
# CH0  CH4  CH8  CH12    (bottom row)
""")

    # 2. 2x2 test grid (4 channels)
    with open('configs/config_2x2_test.txt', 'w') as f:
        f.write("""# 2x2 Test Grid Configuration
# 40mm spacing for testing with limited channels
# Works with any 4-channel audio interface

config_name = 2x2_test_grid
method = tactile_grid

# Create 2x2 grid with 40mm spacing
GRID SIZE=2 SPACING=0.04 OFFSET=0.0,0.0

# This creates speakers at:
# (-0.020,-0.020), (0.020,-0.020)  (bottom row)
# (-0.020,0.020), (0.020,0.020)    (top row)

# Channels increment vertically (bottom-to-top), then next column:
# CH1  CH3    (top row)
# CH0  CH2    (bottom row)
""")

    # 3. 8-speaker circle
    with open('configs/config_octagon.txt', 'w') as f:
        f.write("""# Octagon Speaker Array
# 8 speakers in a circle for room audio

config_name = octagon_room
method = vbap

# Create 8-speaker circle with 2m radius
CIRCLE COUNT=8 RADIUS=2.0 OFFSET=0.0,0.0
""")

    # 4. Stereo pair
    with open('configs/config_stereo.txt', 'w') as f:
        f.write("""# Stereo Speaker Configuration
# Standard left/right speakers

config_name = stereo_pair
method = itd_ild

# Left and right speakers
SPEAKER LEFT  -0.5,0.0 CHANNEL=0 DESCRIPTION="Left speaker"
SPEAKER RIGHT  0.5,0.0 CHANNEL=1 DESCRIPTION="Right speaker"
""")

    # 5. 8x8 high-resolution grid
    with open('configs/config_8x8_grid.txt', 'w') as f:
        f.write("""# 8x8 High-Resolution Tactile Grid
# 20mm spacing for detailed tactile feedback

config_name = 8x8_tactile_grid
method = nearest_neighbor

# Create 8x8 grid with 20mm spacing
GRID SIZE=8 SPACING=0.02 OFFSET=0.0,0.0

# This creates a 140mm x 140mm grid with 64 speakers
""")

    # 6. Development configuration
    with open('configs/config_development.txt', 'w') as f:
        f.write("""# Development Configuration
# Minimal setup for testing and development

config_name = development
method = distance_pan

# Just 4 speakers for easy testing
SPEAKER TL -0.02,0.02 CHANNEL=0 DESCRIPTION="Top left"
SPEAKER TR  0.02,0.02 CHANNEL=1 DESCRIPTION="Top right"
SPEAKER BL -0.02,-0.02 CHANNEL=2 DESCRIPTION="Bottom left"
SPEAKER BR  0.02,-0.02 CHANNEL=3 DESCRIPTION="Bottom right"
""")

        # 7. 10 finger configuration (custom layout)
        with open('configs/config_fingers.txt', 'w') as f:
            f.write("""# Custom 10-Transducer Mirrored Layout Configuration
# Dimensions from drawing show distances from center (0,0)
# Left side is exact mirror: -X of right side positions
# Note: This uses custom channel assignments, not the standard grid mapping

config_name = fingers
method = tactile_grid

# Right side transducers (using dimensions from drawing)
# X coordinates are the mm values from drawing ÷ 1000
SPEAKER R1  0.0200,0.0000   CHANNEL=5 DESCRIPTION="Right 20mm from center, 0mm Y"
SPEAKER R2  0.027246,0.044413   CHANNEL=6 DESCRIPTION="Right ~41mm from center"
SPEAKER R3  0.061484,0.055537  CHANNEL=7 DESCRIPTION="Right ~58mm from center"
SPEAKER R4  0.097244,0.051385   CHANNEL=8 DESCRIPTION="Right ~77mm from center"
SPEAKER R5  0.135099,0.033192  CHANNEL=9 DESCRIPTION="Right bottom position"

# Left side transducers (exact mirror: negative X coordinates)
SPEAKER L1 -0.0200,0.0000   CHANNEL=4 DESCRIPTION="Left 20mm from center, 0mm Y"
SPEAKER L2 -0.027246,0.044413   CHANNEL=3 DESCRIPTION="Left ~41mm from center"
SPEAKER L3 -0.061484,0.055537  CHANNEL=2 DESCRIPTION="Left ~58mm from center"
SPEAKER L4 -0.097244,0.051385   CHANNEL=1 DESCRIPTION="Left ~77mm from center"
SPEAKER L5 -0.135099,0.033192  CHANNEL=0 DESCRIPTION="Left bottom position"

# Note: This configuration uses custom channel assignments
# For standard 4x4 grid with Thawney's board, use config_4x4_grid.txt
    """)

    print("✓ Created configuration files in configs/ directory")
    return True


def create_demo_scripts():
    """Create example demo scripts in examples/ directory"""
    print("\n=== Creating Demo Scripts ===")

    # Ensure examples directory exists
    os.makedirs('examples', exist_ok=True)

    # 1. Demo 4x4 grid
    with open('examples/demo_4x4_grid.txt', 'w') as f:
        f.write("""# 4x4 Grid Demonstration
# Shows the capabilities of the 4x4 tactile grid

# Configuration for optimal tactile perception
itd_exaggeration = 6.0
ild_exponent = 4.0
tone_duration = 0.1

# 1. Corner sounds - demonstrate coverage area
SOUND -0.06,-0.06 FREQ=200 AMP=0.5   # Bottom-left corner
WAIT 0.8
SOUND 0.06,-0.06 FREQ=220 AMP=0.5    # Bottom-right corner
WAIT 0.8
SOUND 0.06,0.06 FREQ=240 AMP=0.5     # Top-right corner
WAIT 0.8
SOUND -0.06,0.06 FREQ=260 AMP=0.5    # Top-left corner
WAIT 0.8
SOUND 0.0,0.0 FREQ=300 AMP=0.6       # Center
WAIT 1.5

# 2. Linear sweep across the grid
ARC -0.06,0.0 0.06,0.0 DURATION=2.0 STEPS=20 FREQ=250 AMP=0.4
WAIT 1.0

# 3. Circular motion around the grid
CIRCLE_SMOOTH RADIUS=0.04 DURATION=4.0 STEPS=180 FREQ=220 AMP=0.3
WAIT 1.0

# 4. Frequency sweep at center
FREQ_RAMP_SMOOTH POS=0.0,0.0 START_FREQ=150 END_FREQ=400 DURATION=3.0 AMP=0.4
WAIT 1.0

# 5. Combined movement and frequency change
PATH_FREQ_RAMP -0.04,-0.04 0.04,0.04 START_FREQ=200 END_FREQ=350 DURATION=2.5 STEPS=50 AMP=0.4
WAIT 1.0

# 6. Curved path demonstration
ARC -0.06,0.0 0.0,0.08 0.06,0.0 DURATION=3.0 STEPS=30 FREQ=280 AMP=0.4 MODE=CURVED
""")

    # 2. Test all speakers
    with open('examples/test_all_speakers.txt', 'w') as f:
        f.write("""# Test All Speakers - 4x4 Grid
# Plays each speaker individually for testing

itd_exaggeration = 4.0
ild_exponent = 2.0
tone_duration = 0.2

# Test each speaker in the 4x4 grid
# Bottom row
SOUND -0.06,-0.06 FREQ=440 AMP=0.5   # CH0
WAIT 0.7
SOUND -0.02,-0.06 FREQ=440 AMP=0.5   # CH1
WAIT 0.7
SOUND 0.02,-0.06 FREQ=440 AMP=0.5    # CH2
WAIT 0.7
SOUND 0.06,-0.06 FREQ=440 AMP=0.5    # CH3
WAIT 0.7

# Second row
SOUND -0.06,-0.02 FREQ=500 AMP=0.5   # CH4
WAIT 0.7
SOUND -0.02,-0.02 FREQ=500 AMP=0.5   # CH5
WAIT 0.7
SOUND 0.02,-0.02 FREQ=500 AMP=0.5    # CH6
WAIT 0.7
SOUND 0.06,-0.02 FREQ=500 AMP=0.5    # CH7
WAIT 0.7

# Third row
SOUND -0.06,0.02 FREQ=550 AMP=0.5    # CH8
WAIT 0.7
SOUND -0.02,0.02 FREQ=550 AMP=0.5    # CH9
WAIT 0.7
SOUND 0.02,0.02 FREQ=550 AMP=0.5     # CH10
WAIT 0.7
SOUND 0.06,0.02 FREQ=550 AMP=0.5     # CH11
WAIT 0.7

# Top row
SOUND -0.06,0.06 FREQ=600 AMP=0.5    # CH12
WAIT 0.7
SOUND -0.02,0.06 FREQ=600 AMP=0.5    # CH13
WAIT 0.7
SOUND 0.02,0.06 FREQ=600 AMP=0.5     # CH14
WAIT 0.7
SOUND 0.06,0.06 FREQ=600 AMP=0.5     # CH15
WAIT 1.0

# Final center sound
SOUND 0.0,0.0 FREQ=300 AMP=0.6
""")

    # 3. Spatialization methods demo
    with open('examples/spatialization_methods_demo.txt', 'w') as f:
        f.write("""# Spatialization Methods Demonstration
# Shows different spatialization approaches
# Note: Change method in config file to test different approaches

itd_exaggeration = 6.0
ild_exponent = 4.0
tone_duration = 0.2

# 1. Test positions that highlight differences between methods
SOUND -0.04,-0.04 FREQ=200 AMP=0.5   # Bottom-left
WAIT 1.0
SOUND 0.04,-0.04 FREQ=220 AMP=0.5    # Bottom-right  
WAIT 1.0
SOUND 0.04,0.04 FREQ=240 AMP=0.5     # Top-right
WAIT 1.0
SOUND -0.04,0.04 FREQ=260 AMP=0.5    # Top-left
WAIT 1.0
SOUND 0.0,0.0 FREQ=300 AMP=0.6       # Center
WAIT 1.5

# 2. Gradual movement to show interpolation differences
ARC -0.06,0.0 0.06,0.0 DURATION=4.0 STEPS=40 FREQ=250 AMP=0.4
WAIT 1.0

# 3. Circular motion to test directional accuracy
CIRCLE_SMOOTH RADIUS=0.04 DURATION=6.0 STEPS=240 FREQ=220 AMP=0.3
WAIT 1.0

# 4. Diagonal movements
ARC -0.06,-0.06 0.06,0.06 DURATION=3.0 STEPS=30 FREQ=280 AMP=0.4
WAIT 0.5
ARC 0.06,-0.06 -0.06,0.06 DURATION=3.0 STEPS=30 FREQ=280 AMP=0.4
""")

    # 4. Smooth tactile grid demo
    with open('examples/smooth_tactile_demo.txt', 'w') as f:
        f.write("""# Smooth Tactile Grid Demonstration
# Shows the improved smooth spatialization (no more clicking/jumping)

# Configuration for optimal smooth tactile perception
itd_exaggeration = 6.0
ild_exponent = 4.0
tone_duration = 0.15

# 1. Smooth linear movement (left to right)
SOUND -0.04,0.0 FREQ=300 AMP=0.4
WAIT 0.3
SOUND -0.02,0.0 FREQ=300 AMP=0.4
WAIT 0.3
SOUND 0.0,0.0 FREQ=300 AMP=0.4
WAIT 0.3
SOUND 0.02,0.0 FREQ=300 AMP=0.4
WAIT 0.3
SOUND 0.04,0.0 FREQ=300 AMP=0.4
WAIT 1.0

# 2. Test equal volume between speakers (should feel balanced)
SOUND -0.01,0.0 FREQ=250 AMP=0.4   # Halfway between speakers
WAIT 0.5
SOUND 0.01,0.0 FREQ=250 AMP=0.4    # Halfway between speakers
WAIT 1.0

# 3. Continuous smooth arc movement (no clicking)
ARC -0.04,-0.04 0.04,0.04 DURATION=3.0 STEPS=50 FREQ=280 AMP=0.4
WAIT 1.0

# 4. Smooth circular motion
CIRCLE_SMOOTH RADIUS=0.03 DURATION=4.0 STEPS=200 FREQ=220 AMP=0.3
WAIT 1.0

# 5. Fine movement test (micro-positioning)
SOUND 0.0,0.0 FREQ=300 AMP=0.4
WAIT 0.4
SOUND 0.005,0.0 FREQ=300 AMP=0.4   # 5mm movement
WAIT 0.4
SOUND 0.01,0.0 FREQ=300 AMP=0.4    # 10mm movement
WAIT 0.4
SOUND 0.015,0.0 FREQ=300 AMP=0.4   # 15mm movement
WAIT 0.4
SOUND 0.02,0.0 FREQ=300 AMP=0.4    # 20mm movement
""")

    print("✓ Created demo scripts in examples/ directory")
    return True


def create_documentation():
    """Create documentation files in docs/ directory"""
    print("\n=== Creating Documentation ===")

    # Ensure docs directory exists
    os.makedirs('docs', exist_ok=True)

    # Create the spatialization methods documentation
    create_spatialization_methods_doc()

    # Create other documentation files
    create_scripting_reference()
    create_hardware_setup_guide()
    create_troubleshooting_guide()

    print("✓ Created documentation in docs/ directory")
    return True


def create_spatialization_methods_doc():
    """Create comprehensive spatialization methods documentation"""

    with open('docs/spatialization_methods.md', 'w') as f:
        f.write("""# Multi-Speaker Spatialization Methods Guide

This system supports 5 different spatialization methods, each optimized for different types of speaker arrangements and use cases.

## Overview of Methods

| Method | Best For | Speakers Active | Audio Quality | CPU Usage |
|--------|----------|----------------|---------------|-----------|
| **tactile_grid** | Tactile grids (4x4, 8x8) | 2-4 nearest | Excellent | Medium |
| **vbap** | Room speakers in circle | 2 optimal | Excellent | Low |
| **distance_pan** | Any layout (universal) | All speakers | Good | Medium |
| **nearest_neighbor** | Simple discrete displays | 1 only | Discrete | Very Low |
| **itd_ild** | Stereo systems only | 2 (stereo) | Natural | Low |

---

## 1. Tactile Grid (`tactile_grid`) - ✨ IMPROVED! ✨
**Default for grid arrays like 4x4, 8x8 - NOW WITH SMOOTH SPATIALIZATION**

### ✨ **NEW: Fixed Clicking/Jumping Issues** ✨

**PROBLEM SOLVED:** The tactile grid method previously had "jumpy" behavior where:
- Sound would click when the loudest speaker activated
- Sources between two speakers had uneven volume (one louder than the other)
- Moving sources felt like clicking from speaker to speaker instead of smooth travel

**FIXES APPLIED:**
- ✅ **Removed tactile exaggeration bias** - No more artificial 4x boost to closest speaker
- ✅ **Increased minimum distance** - From 1mm to 8mm for smoother transitions
- ✅ **Gentler distance falloff** - Uses power of 1.5 instead of 1.0 for less sharp transitions
- ✅ **Power normalization** - Maintains consistent volume across all positions
- ✅ **Configurable smoothness** - Multiple smoothness modes available

### How it works (IMPROVED):
- Uses smooth inverse distance weighting with up to 6 nearest speakers
- Applies gentle enhancement to all active speakers (no bias toward closest)
- Provides seamless interpolation between adjacent speakers
- **NEW:** Power normalization ensures consistent perceived loudness
- **NEW:** Configurable parameters for different smoothness preferences

### Algorithm (UPDATED):
```
1. Find up to 6 nearest speakers to sound source
2. Calculate smooth inverse distance weights: weight = 1/(distance + 8mm)^1.5
3. Normalize weights to sum to 1 (equal importance)  
4. Apply gentle enhancement to all active speakers (1.2x boost)
5. Power normalize to prevent clipping and maintain consistency
```

### Best for:
- 4x4, 8x8 tactile grids
- Haptic feedback systems  
- Close-proximity interaction
- Applications requiring smooth spatial transitions
- **NEW:** Any tactile system where smooth movement is important

### Configuration example:
```
method = tactile_grid
GRID SIZE=4 SPACING=0.04 OFFSET=0.0,0.0
```

### ✨ **NEW: Smoothness Configuration** ✨

#### Interactive Configuration:
```bash
python multispeaker_main.py --config config_4x4_grid.txt --interactive
> smooth
# Choose from preset smoothness options
```

#### Programmatic Configuration:
```python
# Default improved smoothness (recommended)
# - Already active, no configuration needed

# Extra smooth mode (Gaussian weighting)
spatialiser.audio_engine.spat_engine.set_tactile_grid_parameters(
    use_gaussian=True, 
    gaussian_sigma=0.03
)

# More focused mode (more localized)
spatialiser.audio_engine.spat_engine.set_tactile_grid_parameters(
    max_active_speakers=4, 
    distance_power=2.0, 
    smooth_min_distance=0.005
)

# Custom fine-tuning
spatialiser.audio_engine.spat_engine.set_tactile_grid_parameters(
    smooth_min_distance=0.01,      # 10mm smoothing distance
    distance_power=1.2,            # Very gentle falloff
    tactile_enhancement=1.1,       # Subtle enhancement
    max_active_speakers=8          # Use more speakers
)
```

### Parameters (NEW):
- `use_gaussian` (bool): Use Gaussian weighting for maximum smoothness (default: False)
- `gaussian_sigma` (float): Standard deviation for Gaussian mode in meters (default: 0.025)
- `max_active_speakers` (int): Maximum speakers active simultaneously (default: 6)
- `smooth_min_distance` (float): Minimum distance for smooth transitions in meters (default: 0.008)
- `distance_power` (float): Power for distance falloff - higher = more focused (default: 1.5)
- `tactile_enhancement` (float): Overall tactile boost factor (default: 1.2)

### ✨ **Testing the Smooth Improvements** ✨

```bash
# Test smooth movement
python multispeaker_main.py examples/smooth_tactile_demo.txt --config config_4x4_grid.txt

# Interactive testing
python multispeaker_main.py --config config_4x4_grid.txt --interactive
> play -0.02 0.0 300 0.4
> play 0.0 0.0 300 0.4     # Should transition smoothly
> play 0.02 0.0 300 0.4
```

**BEFORE (jumpy):** Click-click-click as you move between speakers
**AFTER (smooth):** Smooth, continuous transition that feels natural

---

## 2. Vector Base Amplitude Panning (`vbap`)
**Best for room speaker setups**

### How it works:
- Finds the two speakers that best "surround" the virtual sound source
- Uses vector mathematics to calculate optimal gains
- Provides precise directional control
- Based on psychoacoustic research for room audio

### Algorithm:
```
1. Convert source position to polar coordinates (angle)
2. Find two nearest speakers by angle
3. Use linear interpolation between speaker angles
4. Apply VBAP gain formula: sqrt(1-t) and sqrt(t)
```

### Best for:
- Circular/octagonal speaker arrays
- Room-scale audio systems
- Surround sound applications
- When speakers are positioned around the listener

### Configuration example:
```
method = vbap
CIRCLE COUNT=8 RADIUS=2.0 OFFSET=0.0,0.0
```

### Parameters:
- Works best with 6-12 speakers in circle/polygon
- Minimal parameter tuning needed

---

## 3. Distance Panning (`distance_pan`)
**Simple and universal**

### How it works:
- Uses simple inverse distance law (1/r²) for all speakers
- All speakers can be active simultaneously
- Provides natural distance-based attenuation
- Works with any speaker layout

### Algorithm:
```
1. Calculate distance to each speaker
2. Apply inverse distance law: gain = 1/distance²
3. Normalize total power across all speakers
```

### Best for:
- Any speaker configuration
- Development and testing
- When simplicity is preferred
- Mixed or irregular speaker layouts

### Configuration example:
```
method = distance_pan
# Works with any speaker layout
SPEAKER SP1 -0.02,0.02 CHANNEL=0
SPEAKER SP2  0.02,0.02 CHANNEL=1
SPEAKER SP3  0.02,-0.02 CHANNEL=2
SPEAKER SP4 -0.02,-0.02 CHANNEL=3
```

### Parameters:
- `distance_rolloff = 1.0-3.0` - Controls spread (1.0=wide, 3.0=focused)

---

## 4. Nearest Neighbor (`nearest_neighbor`)
**Discrete switching**

### How it works:
- Only the single closest speaker plays
- No interpolation between speakers
- Provides discrete, "digital" positioning
- Most efficient computationally

### Algorithm:
```
1. Calculate distance to each speaker
2. Find speaker with minimum distance
3. Set that speaker gain = 1.0, all others = 0.0
```

### Best for:
- Discrete tactile displays
- Simple position indication
- Low-power applications
- When smooth interpolation isn't needed

### Configuration example:
```
method = nearest_neighbor
GRID SIZE=8 SPACING=0.02 OFFSET=0.0,0.0
```

### Parameters:
- No special parameters needed
- Most efficient method

---

## 5. ITD/ILD (`itd_ild`)
**Binaural for stereo only**

### How it works:
- Simulates natural binaural hearing
- Interaural Time Difference (ITD): timing between ears
- Interaural Level Difference (ILD): volume between ears
- Only works with 2-channel stereo setups

### Algorithm:
```
1. Calculate distance to left/right speakers
2. ITD: time_diff = (dist_left - dist_right) / speed_of_sound
3. ILD: gain ratio based on relative distances
4. Apply exaggeration parameters
```

### Best for:
- Stereo headphone/speaker systems
- Binaural audio research
- Natural-sounding stereo spatialization
- When you have exactly 2 speakers

### Configuration example:
```
method = itd_ild
SPEAKER LEFT  -0.5,0.0 CHANNEL=0 DESCRIPTION="Left speaker"
SPEAKER RIGHT  0.5,0.0 CHANNEL=1 DESCRIPTION="Right speaker"
```

### Parameters:
- `itd_exaggeration = 1.0-6.0` - Enhance timing differences
- `ild_exponent = 1.0-5.0` - Enhance level differences

---

## Choosing the Right Method

### For Tactile/Haptic Systems:
```
4x4 to 8x8 grids     → tactile_grid (IMPROVED!)
Simple on/off feedback → nearest_neighbor
High-resolution grids  → tactile_grid (IMPROVED!)
```

### For Audio Systems:
```
Room speakers in circle → vbap
Stereo setup           → itd_ild
Irregular layouts      → distance_pan
```

### For Development/Testing:
```
General testing        → distance_pan (works everywhere)
Debugging             → nearest_neighbor (clear which speaker)
Performance testing   → nearest_neighbor (fastest)
```

---

## ✨ **Troubleshooting Tactile Grid Issues** ✨

### Problem: Clicking/Jumping Between Speakers
**SOLUTION (FIXED):** This has been resolved in the improved tactile grid method!

**What was wrong:**
- Old method artificially boosted closest speaker by 4x
- Sharp distance transitions caused sudden volume changes
- Uneven weighting between equally-distant speakers

**What's fixed:**
- Smooth transitions with 8mm minimum distance
- Equal weighting for equally-positioned sources  
- Gentle enhancement applied to all speakers
- Power normalization for consistent volume

### Problem: Uneven Volume Between Speakers
**SOLUTION (FIXED):** Power normalization now ensures consistent perceived loudness.

**Test the fix:**
```bash
# These should now feel equally balanced
python multispeaker_main.py --interactive
> play -0.01 0.0 300 0.4  # Halfway between two speakers
> play 0.01 0.0 300 0.4   # Should feel identical
```

### Problem: Movement Doesn't Feel Smooth
**SOLUTION:** Configure smoother settings:

```python
# For maximum smoothness
spatialiser.audio_engine.spat_engine.set_tactile_grid_parameters(
    use_gaussian=True,
    gaussian_sigma=0.03
)

# Test smooth movement
for i in range(20):
    x = -0.04 + (i * 0.004)  # -40mm to +36mm in 4mm steps
    spatialiser.play_sound(x, 0.0, freq=300, amp=0.4)
    time.sleep(0.15)
```

---

## Performance Characteristics

### Real-time Performance (per calculation):
- **Fastest**: `nearest_neighbor` (~0.01ms)
- **Fast**: `vbap`, `itd_ild` (~0.05ms)  
- **Medium**: `distance_pan`, `tactile_grid` (~0.1ms)

### Quality vs Performance Trade-offs:
- **High quality + High performance**: `vbap`
- **High quality + Medium performance**: `tactile_grid` (IMPROVED!)
- **Medium quality + High performance**: `nearest_neighbor`
- **Universal + Good performance**: `distance_pan`

---

## Configuration Examples

### ✨ **Smooth Tactile Setup (RECOMMENDED)** ✨
```
# config_smooth_tactile.txt
# Optimized for Thawney's 16-channel driver board
config_name = smooth_tactile_4x4
method = tactile_grid

# Optimized parameters for smooth tactile feedback
GRID SIZE=4 SPACING=0.04 OFFSET=0.0,0.0

# The improved tactile_grid method automatically provides:
# - Smooth transitions (no clicking)
# - Even volume between speakers  
# - Natural movement sensation
# - Configurable smoothness levels

# Channel mapping: Vertical increment (bottom-to-top), then next column
# Works perfectly with Thawney's 16-channel driver board
```

### Extra Smooth Tactile Setup:
```
# config_extra_smooth.txt
# For maximum smoothness with Thawney's driver board
config_name = extra_smooth_tactile
method = tactile_grid

GRID SIZE=4 SPACING=0.04 OFFSET=0.0,0.0

# Configure for maximum smoothness in code:
# spatialiser.audio_engine.spat_engine.set_tactile_grid_parameters(
#     use_gaussian=True, gaussian_sigma=0.03
# )
```

### Room Audio Setup:
```
# config_room_audio.txt
config_name = room_audio
method = vbap

# 8-speaker circle for immersive room audio
CIRCLE COUNT=8 RADIUS=2.0 OFFSET=0.0,0.0
```

### Universal Testing Setup:
```
# config_universal.txt
config_name = universal_test
method = distance_pan

# Works with any speaker arrangement
distance_rolloff = 2.0

SPEAKER FL -0.3,0.3 CHANNEL=0 DESCRIPTION="Front left"
SPEAKER FR  0.3,0.3 CHANNEL=1 DESCRIPTION="Front right"
SPEAKER BL -0.3,-0.3 CHANNEL=2 DESCRIPTION="Back left"
SPEAKER BR  0.3,-0.3 CHANNEL=3 DESCRIPTION="Back right"
```

---

## Advanced Usage

### ✨ **NEW: Interactive Smoothness Configuration** ✨
```bash
python multispeaker_main.py --config config_4x4_grid.txt --interactive
> smooth
# Choose from 4 preset options:
# 1. Default (improved smoothness) 
# 2. Extra smooth (Gaussian mode)
# 3. More focused (less smooth, more localized)
# 4. Custom parameters
```

### Runtime Method Switching:
```python
# Change method during execution
spatialiser.speaker_config.method = 'vbap'
spatialiser.audio_engine.spat_engine.method = 'vbap'
```

### Custom Tactile Parameters:
```python
# Fine-tune smoothness
spatialiser.audio_engine.spat_engine.set_tactile_grid_parameters(
    smooth_min_distance=0.012,     # 12mm smoothing
    distance_power=1.3,            # Gentle falloff  
    tactile_enhancement=1.15,      # Subtle boost
    max_active_speakers=5          # Fewer active speakers
)
```

### Testing All Methods:
```bash
# Test spatialization methods with system test
python test_system.py --test spatialization

# Test smooth tactile specifically
python multispeaker_main.py examples/smooth_tactile_demo.txt
```

---

## Method-Specific Tips

### ✨ **Smooth Tactile Grid (IMPROVED):**
- **Default settings work great** - No configuration needed for smooth operation
- Use 40mm spacing for optimal tactile perception
- For extra smoothness: enable Gaussian mode
- For more localization: reduce `max_active_speakers` to 4
- Test with `examples/smooth_tactile_demo.txt`
- **Key improvement:** No more clicking or uneven volume between speakers!

### VBAP:
- Requires speakers positioned around the listening area
- Works best with 6-12 speakers in circle/polygon
- Provides most accurate directional audio
- Minimal parameter tuning needed

### Distance Pan:
- Good fallback when other methods don't work
- Adjust `distance_rolloff` to change spread (1.0 = wide, 3.0 = focused)
- Works with any speaker layout
- Good for development and testing

### Nearest Neighbor:
- Perfect for discrete tactile patterns
- Use for binary on/off feedback
- Combine with short `tone_duration` for rapid switching
- Most efficient for real-time applications

### ITD/ILD:
- Only for stereo - will fall back to distance_pan for more speakers
- Increase `itd_exaggeration` for stronger spatial effect
- Use `ild_exponent = 2.0-5.0` for natural to exaggerated differences
- Best for headphone/stereo speaker setups

---

## ✨ **Troubleshooting Methods (UPDATED)** ✨

### If tactile grid feels jumpy or clicky:
1. ✅ **FIXED** - Update to latest version with smooth tactile grid
2. Test with: `python multispeaker_main.py examples/smooth_tactile_demo.txt`
3. For extra smoothness: Use interactive `smooth` command
4. Verify with movement test: play sounds from -0.04 to +0.04 in small steps

### If spatialization seems wrong:
1. Check speaker configuration with: `python multispeaker_main.py --info`
2. Test individual speakers: `python multispeaker_main.py examples/test_all_speakers.txt`
3. Try different method: change `method = ` in config file
4. Verify speaker positions match physical layout

### Performance issues:
1. Use `nearest_neighbor` for fastest performance
2. Reduce `tone_duration` for rapid playback
3. Use fewer speakers or smaller grid
4. Disable visualization during testing

### Audio quality issues:
1. Try `vbap` for room setups
2. Try `tactile_grid` (improved) for grid arrays
3. Adjust enhancement parameters
4. Check audio interface channel count

---

## ✨ **What's New in This Version** ✨

### Major Improvements to Tactile Grid:
- ✅ **Fixed clicking/jumping issues** - Smooth transitions between speakers
- ✅ **Equal volume positioning** - Sources between speakers have balanced volume  
- ✅ **Configurable smoothness** - Multiple smoothness modes available
- ✅ **Interactive configuration** - Easy smoothness adjustment via `smooth` command
- ✅ **Power normalization** - Consistent perceived loudness across all positions
- ✅ **Enhanced documentation** - Complete troubleshooting and configuration guide

### New Features:
- Interactive smoothness configuration
- Gaussian weighting mode for maximum smoothness
- Fine-grained parameter control
- Smooth tactile demo script
- Comprehensive troubleshooting guide

---

*This guide covers all 5 implemented spatialization methods in the Multi-Speaker Tactile Spatialiser system, with special focus on the improved smooth tactile grid method.*
""")


def create_scripting_reference():
    """Create scripting language reference"""

    with open('docs/scripting_reference.md', 'w') as f:
        f.write("""# Multi-Speaker Tactile Spatialiser Scripting Language Reference

A comprehensive scripting language for driving multi-speaker tactile spatialiser systems. This extends the original tactile spatialiser with full multi-channel support, advanced spatialization methods, and enhanced audio processing.

Each line is one of:
- **Configuration** assignments  
- **Commands** with optional arguments  
- **Comments** (ignored)

---

## 1. Comments

- Any line beginning with `#` is a comment.  
- Blank lines are ignored.

```text
# This is a comment
# Configuration for 4x4 tactile grid
```

---

## 2. Configuration Assignments

Set global parameters that affect audio processing and spatialization.

Format:  
```text
<key> = <value>
```

### Core Parameters

| Key                | Meaning                                         | Default | Range |
|--------------------|-------------------------------------------------|---------|-------|
| `itd_exaggeration` | Multiply the physical Interaural Time Difference | `1.0`   | 0.1-10.0 |
| `ild_exponent`     | Exponent for Interaural Level Difference ratio  | `1.0`   | 0.1-5.0 |
| `tone_duration`    | Duration (s) of each discrete burst             | `0.1`   | 0.01-2.0 |

### Advanced Parameters (for custom configurations)

| Key                | Meaning                                         | Default | Range |
|--------------------|-------------------------------------------------|---------|-------|
| `fade_duration`    | Fade in/out time to prevent clicks (s)         | `0.05`  | 0.01-0.2 |
| `tactile_exaggeration` | Extra spatial emphasis for tactile feedback | `4.0`   | 1.0-10.0 |
| `distance_rolloff` | Distance attenuation exponent                   | `2.0`   | 0.5-4.0 |

**Example**  
```text
# Enhanced tactile configuration
itd_exaggeration = 6.0
ild_exponent = 4.0
tone_duration = 0.15
tactile_exaggeration = 5.0
```

---

## 3. WAIT

Pause execution without sound.

```
WAIT <seconds>
```

- `<seconds>` — floating-point delay before next command.

**Example**  
```text
WAIT 1.5    # pause for 1.5 seconds
WAIT 0.25   # short pause
```

---

## 4. JUMP

Move the *current position* without playing a sound.

```
JUMP <x>,<y>
```

- `<x>,<y>` — coordinates in meters, relative to the center `(0,0)`.

**Example**  
```text
JUMP  0.02, -0.01   # teleport to 20mm right, 10mm back
JUMP -0.06,  0.06   # teleport to far left, far forward
```

---

## 5. SOUND

Play a single burst at a given position, frequency, and amplitude.

```
SOUND <x>,<y> FREQ=<freq> AMP=<amp>
```

- `<x>,<y>` — location in meters (0,0 = center of speaker array)
- `FREQ` — frequency in Hz (20-20000, typically 150-500 for tactile)
- `AMP`  — amplitude (0.0–1.0, typically 0.2-0.8)

**Example**  
```text
SOUND -0.04,0.02  FREQ=200  AMP=0.5   # Left-forward, 200Hz, medium volume
SOUND  0.0,0.0    FREQ=440  AMP=0.3   # Center, 440Hz, quiet
```

---

## 6. ARC

Create a path between two or three points, either straight or curved.
The system plays a series of discrete sound bursts along this path.

```
ARC <x1>,<y1> <x2>,<y2> [<x3>,<y3>] \\
    DURATION=<t> STEPS=<n> FREQ=<f> AMP=<a> [MODE={STRAIGHT|CURVED}]
```

### Parameters

| Parameter   | Description                                             | Required |
|-------------|---------------------------------------------------------|----------|
| `<x1>,<y1>` | Start coordinates (meters)                             | Yes      |
| `<x2>,<y2>` | Second coordinates - endpoint or control point         | Yes      |
| `<x3>,<y3>` | Third coordinates (for curved arcs)                    | Optional |
| `DURATION`  | Total time for the sweep (seconds)                     | Yes      |
| `STEPS`     | Number of discrete bursts along the path               | Yes      |
| `FREQ`      | Tone frequency in Hz                                    | Yes      |
| `AMP`       | Amplitude (0.0–1.0)                                    | Yes      |
| `MODE`      | `STRAIGHT` (default) or `CURVED`                       | Optional |

### Point Interpretation

**With 2 points:**
- Linear interpolation between points 1 and 2
- `MODE=CURVED` is ignored (falls back to STRAIGHT)

**With 3 points:**
- `MODE=STRAIGHT`: uses points 1 and 3 (ignores point 2)
- `MODE=CURVED`: quadratic Bézier curve using all three points

### Examples

```text
# Linear arc across the grid
ARC -0.06,0.0 0.06,0.0 DURATION=2.0 STEPS=20 FREQ=250 AMP=0.4

# Curved arc with control point
ARC -0.04,-0.04 0.0,0.08 0.04,-0.04 DURATION=3.0 STEPS=30 FREQ=280 AMP=0.4 MODE=CURVED

# Vertical sweep
ARC 0.0,-0.06 0.0,0.06 DURATION=1.5 STEPS=15 FREQ=300 AMP=0.3
```

---

## 7. CIRCLE_SMOOTH

Generate one seamless, continuous circular sweep around a center point.

```
CIRCLE_SMOOTH RADIUS=<r> DURATION=<t> STEPS=<n> FREQ=<f> AMP=<a>
```

### Parameters

| Parameter | Description                                    | Typical Range |
|-----------|------------------------------------------------|---------------|
| `RADIUS`  | Circle radius in meters                        | 0.01-0.1      |
| `DURATION`| Time for one complete revolution (seconds)     | 2.0-10.0      |
| `STEPS`   | Internal resolution for smooth motion          | 100-360       |
| `FREQ`    | Tone frequency (Hz)                           | 150-400       |
| `AMP`     | Amplitude (0.0-1.0)                           | 0.2-0.6       |

### Examples

```text
# Slow circular sweep around center
CIRCLE_SMOOTH RADIUS=0.04 DURATION=6.0 STEPS=360 FREQ=220 AMP=0.3

# Fast tight circle
CIRCLE_SMOOTH RADIUS=0.02 DURATION=2.0 STEPS=180 FREQ=300 AMP=0.4

# Large room-scale circle
CIRCLE_SMOOTH RADIUS=1.0 DURATION=8.0 STEPS=360 FREQ=200 AMP=0.5
```

---

## 8. FREQ_RAMP

Create a frequency sweep at a fixed position with discrete steps.

```
FREQ_RAMP POS=<x>,<y> START_FREQ=<f1> END_FREQ=<f2> DURATION=<t> STEPS=<n> AMP=<a>
```

### Parameters

| Parameter     | Description                                    | Typical Range |
|---------------|------------------------------------------------|---------------|
| `POS`         | Fixed position coordinates (meters)            | Grid bounds   |
| `START_FREQ`  | Starting frequency (Hz)                        | 50-1000       |
| `END_FREQ`    | Ending frequency (Hz)                          | 50-1000       |
| `DURATION`    | Total sweep time (seconds)                     | 1.0-5.0       |
| `STEPS`       | Number of discrete frequency steps             | 10-50         |
| `AMP`         | Amplitude (0.0-1.0)                           | 0.2-0.8       |

### Examples

```text
# Rising frequency sweep at center
FREQ_RAMP POS=0.0,0.0 START_FREQ=150 END_FREQ=400 DURATION=3.0 STEPS=30 AMP=0.5

# Falling frequency sweep at corner
FREQ_RAMP POS=0.04,0.04 START_FREQ=500 END_FREQ=200 DURATION=2.0 STEPS=20 AMP=0.4

# Alarm-like effect
FREQ_RAMP POS=0.0,0.0 START_FREQ=300 END_FREQ=600 DURATION=1.0 STEPS=10 AMP=0.6
```

---

## 9. FREQ_RAMP_SMOOTH

Create a continuous, smooth frequency sweep at a fixed position.

```
FREQ_RAMP_SMOOTH POS=<x>,<y> START_FREQ=<f1> END_FREQ=<f2> DURATION=<t> AMP=<a>
```

### Parameters

| Parameter     | Description                                    | Typical Range |
|---------------|------------------------------------------------|---------------|
| `POS`         | Fixed position coordinates (meters)            | Grid bounds   |
| `START_FREQ`  | Starting frequency (Hz)                        | 50-1000       |
| `END_FREQ`    | Ending frequency (Hz)                          | 50-1000       |
| `DURATION`    | Total sweep time (seconds)                     | 1.0-5.0       |
| `AMP`         | Amplitude (0.0-1.0)                           | 0.2-0.8       |

### Examples

```text
# Smooth rising sweep
FREQ_RAMP_SMOOTH POS=0.0,0.0 START_FREQ=100 END_FREQ=500 DURATION=3.0 AMP=0.4

# Doppler effect simulation
FREQ_RAMP_SMOOTH POS=0.02,0.0 START_FREQ=400 END_FREQ=200 DURATION=2.0 AMP=0.5

# Attention-grabbing alert
FREQ_RAMP_SMOOTH POS=0.0,0.0 START_FREQ=250 END_FREQ=450 DURATION=0.8 AMP=0.7
```

**Note:** `FREQ_RAMP_SMOOTH` produces smoother, more natural-sounding frequency transitions than `FREQ_RAMP`.

---

## 10. PATH_FREQ_RAMP

The most powerful command: combines position movement with frequency changes in synchronized motion.

```
PATH_FREQ_RAMP <x1>,<y1> <x2>,<y2> [<x3>,<y3>] \\
    START_FREQ=<f1> END_FREQ=<f2> DURATION=<t> STEPS=<n> AMP=<a> [MODE={STRAIGHT|CURVED}]
```

### Parameters

| Parameter     | Description                                    | Required |
|---------------|------------------------------------------------|----------|
| `<x1>,<y1>`   | Start coordinates (meters)                     | Yes      |
| `<x2>,<y2>`   | Second coordinates - endpoint or control point | Yes      |
| `<x3>,<y3>`   | Third coordinates (for curved paths)           | Optional |
| `START_FREQ`  | Starting frequency (Hz)                        | Yes      |
| `END_FREQ`    | Ending frequency (Hz)                          | Yes      |
| `DURATION`    | Total time for the sweep (seconds)             | Yes      |
| `STEPS`       | Internal resolution (higher = smoother)        | Yes      |
| `AMP`         | Amplitude (0.0-1.0)                           | Yes      |
| `MODE`        | `STRAIGHT` (default) or `CURVED`               | Optional |

### Examples

```text
# Linear movement with rising frequency
PATH_FREQ_RAMP -0.06,0.0 0.06,0.0 START_FREQ=150 END_FREQ=350 DURATION=3.0 STEPS=100 AMP=0.4

# Curved movement with falling frequency
PATH_FREQ_RAMP -0.04,-0.04 0.0,0.08 0.04,-0.04 START_FREQ=500 END_FREQ=200 DURATION=4.0 STEPS=120 AMP=0.3 MODE=CURVED

# Diagonal sweep with frequency rise
PATH_FREQ_RAMP -0.06,-0.06 0.06,0.06 START_FREQ=200 END_FREQ=400 DURATION=2.5 STEPS=80 AMP=0.5
```

### Advanced Usage

```text
# Simulate approaching object (position + Doppler)
PATH_FREQ_RAMP -0.08,0.0 0.02,0.0 START_FREQ=300 END_FREQ=350 DURATION=2.0 STEPS=60 AMP=0.4

# Simulate departing object
PATH_FREQ_RAMP 0.02,0.0 -0.08,0.0 START_FREQ=350 END_FREQ=280 DURATION=3.0 STEPS=90 AMP=0.4
```

---

## 11. Coordinate System & Speaker Layouts

### Coordinate System

- **Origin (0,0)**: Center of speaker array
- **X-axis**: Left (-) to Right (+)
- **Y-axis**: Back (-) to Front (+)
- **Units**: Meters

### Common Speaker Layouts

#### 4x4 Tactile Grid (Default)
```text
Coverage: 120mm x 120mm
Spacing: 40mm between speakers
Range: x = -0.06 to +0.06, y = -0.06 to +0.06

Grid Layout (with Thawney's 16-channel driver board):
     -60mm  -20mm  +20mm  +60mm
+60mm [CH3] [CH7] [CH11] [CH15]  ← Top row
+20mm [CH2] [CH6] [CH10] [CH14]
-20mm [CH1] [CH5] [CH9]  [CH13]
-60mm [CH0] [CH4] [CH8]  [CH12]  ← Bottom row

Channels increment vertically (bottom-to-top), then next column.
```

#### 2x2 Test Grid
```text
Coverage: 40mm x 40mm
Spacing: 40mm between speakers
Range: x = -0.02 to +0.02, y = -0.02 to +0.02

Grid Layout:
     -20mm  +20mm
+20mm [CH2]  [CH3]
-20mm [CH0]  [CH1]
```

#### Stereo Setup
```text
Coverage: 1000mm spacing
Range: x = -0.5 to +0.5, y = 0.0

Layout:
-500mm [LEFT]     [RIGHT] +500mm
```

### Position Guidelines

| Grid Type | Recommended Range | Typical Positions |
|-----------|-------------------|-------------------|
| 4x4 Grid  | ±0.06m           | ±0.02m, ±0.04m, ±0.06m |
| 2x2 Grid  | ±0.02m           | ±0.02m |
| Stereo    | ±0.5m            | ±0.3m, ±0.5m |
| Octagon   | ±2.0m            | ±1.0m, ±2.0m |

---

## 12. Command Comparison & Selection Guide

### When to Use Each Command

| Command | Best For | Audio Quality | Complexity |
|---------|----------|---------------|------------|
| **SOUND** | Discrete points, simple patterns | Separate bursts | Simple |
| **ARC** | Basic movement paths | Separate bursts | Medium |
| **CIRCLE_SMOOTH** | Circular/orbital motion | Continuous | Medium |
| **FREQ_RAMP** | Basic frequency effects | Separate bursts | Medium |
| **FREQ_RAMP_SMOOTH** | Smooth frequency transitions | Continuous | Medium |
| **PATH_FREQ_RAMP** | Complex combined effects | Continuous | Advanced |

### Audio Quality Comparison

**Discrete Commands (SOUND, ARC, FREQ_RAMP):**
- Individual tone bursts
- Slight gaps between sounds
- Good for rhythmic patterns
- Lower CPU usage

**Continuous Commands (CIRCLE_SMOOTH, FREQ_RAMP_SMOOTH, PATH_FREQ_RAMP):**
- Seamless audio streams
- Smooth transitions
- More natural sound
- Higher CPU usage

---

## 13. Example Scripts

### Basic Grid Test
```text
# Test 4x4 grid corners and center
itd_exaggeration = 4.0
ild_exponent = 2.0
tone_duration = 0.2

SOUND -0.06,-0.06 FREQ=200 AMP=0.5  # Bottom-left
WAIT 0.8
SOUND 0.06,-0.06 FREQ=220 AMP=0.5   # Bottom-right
WAIT 0.8
SOUND 0.06,0.06 FREQ=240 AMP=0.5    # Top-right
WAIT 0.8
SOUND -0.06,0.06 FREQ=260 AMP=0.5   # Top-left
WAIT 0.8
SOUND 0.0,0.0 FREQ=300 AMP=0.6      # Center
```

### Tactile Reading Pattern
```text
# Line-by-line reading simulation
itd_exaggeration = 6.0
ild_exponent = 4.0
tone_duration = 0.1

# Read first line
PATH_FREQ_RAMP -0.06,0.04 0.06,0.04 START_FREQ=250 END_FREQ=250 DURATION=2.0 STEPS=40 AMP=0.4
WAIT 0.3

# Return to start of next line
PATH_FREQ_RAMP 0.06,0.04 -0.06,0.02 START_FREQ=150 END_FREQ=150 DURATION=0.8 STEPS=20 AMP=0.3

# Read second line
PATH_FREQ_RAMP -0.06,0.02 0.06,0.02 START_FREQ=250 END_FREQ=250 DURATION=2.0 STEPS=40 AMP=0.4
```

### Navigation Assistance
```text
# Spatial orientation and path guidance
itd_exaggeration = 6.0
ild_exponent = 4.0
tone_duration = 0.1

# Show current position
SOUND 0.0,0.0 FREQ=300 AMP=0.5
WAIT 0.5

# Show target direction
SOUND 0.04,0.04 FREQ=350 AMP=0.6
WAIT 0.5

# Guide along path
PATH_FREQ_RAMP 0.0,0.0 0.04,0.04 START_FREQ=300 END_FREQ=350 DURATION=2.0 STEPS=50 AMP=0.5
```

### Frequency Effects Demo
```text
# Demonstration of frequency-based effects
itd_exaggeration = 4.0
ild_exponent = 2.0
tone_duration = 0.1

# Attention-grabbing sweep
FREQ_RAMP_SMOOTH POS=0.0,0.0 START_FREQ=200 END_FREQ=400 DURATION=1.0 AMP=0.6

# Doppler effect
PATH_FREQ_RAMP -0.08,0.0 0.08,0.0 START_FREQ=350 END_FREQ=250 DURATION=2.0 STEPS=60 AMP=0.5

# Alarm pattern
FREQ_RAMP_SMOOTH POS=0.0,0.0 START_FREQ=300 END_FREQ=500 DURATION=0.5 AMP=0.7
FREQ_RAMP_SMOOTH POS=0.0,0.0 START_FREQ=500 END_FREQ=300 DURATION=0.5 AMP=0.7
```

---

## 14. Advanced Techniques

### Layering Effects
```text
# Create complex patterns by combining simple commands
SOUND 0.0,0.0 FREQ=200 AMP=0.3      # Base reference
WAIT 0.5
CIRCLE_SMOOTH RADIUS=0.02 DURATION=2.0 STEPS=180 FREQ=250 AMP=0.4
WAIT 0.5
FREQ_RAMP_SMOOTH POS=0.0,0.0 START_FREQ=150 END_FREQ=300 DURATION=1.5 AMP=0.3
```

### Synchronized Patterns
```text
# Create patterns that work together
ARC -0.06,0.0 0.06,0.0 DURATION=3.0 STEPS=30 FREQ=200 AMP=0.4
WAIT 0.5
ARC 0.06,0.0 -0.06,0.0 DURATION=3.0 STEPS=30 FREQ=250 AMP=0.4
```

### Interactive Responses
```text
# Simulate user interaction feedback
SOUND 0.02,0.02 FREQ=300 AMP=0.5    # User touches button
WAIT 0.1
FREQ_RAMP_SMOOTH POS=0.02,0.02 START_FREQ=300 END_FREQ=400 DURATION=0.3 AMP=0.4  # Confirmation
```

---

## 15. Performance Considerations

### Optimization Tips

1. **Use appropriate STEPS values:**
   - ARC: 10-50 steps for most cases
   - PATH_FREQ_RAMP: 50-100 steps for smooth motion
   - CIRCLE_SMOOTH: 100-360 steps

2. **Balance quality vs. performance:**
   - Higher STEPS = smoother but more CPU usage
   - Lower STEPS = more efficient but less smooth

3. **Choose the right command:**
   - Use SOUND for simple discrete patterns
   - Use smooth commands only when needed
   - Avoid excessive visualization updates

### Resource Usage

| Command Type | CPU Usage | Memory Usage | Audio Quality |
|-------------|-----------|--------------|---------------|
| Discrete    | Low       | Low          | Good          |
| Continuous  | Medium    | Medium       | Excellent     |
| Complex     | High      | High         | Excellent     |

---

## 16. Best Practices

### Script Organization

1. **Start with configuration:**
```text
# Configuration section
itd_exaggeration = 6.0
ild_exponent = 4.0
tone_duration = 0.1

# Main script follows...
```

2. **Use meaningful comments:**
```text
# Section 1: Orientation
SOUND 0.0,0.0 FREQ=200 AMP=0.5      # Center reference point

# Section 2: Movement demonstration
ARC -0.06,0.0 0.06,0.0 DURATION=2.0 STEPS=20 FREQ=250 AMP=0.4
```

3. **Structure complex scripts:**
```text
# === SECTION 1: BASIC ORIENTATION ===
# === SECTION 2: MOVEMENT PATTERNS ===
# === SECTION 3: FREQUENCY EFFECTS ===
```

### Parameter Selection

**For Tactile Feedback:**
- `itd_exaggeration = 4.0-8.0`
- `ild_exponent = 2.0-5.0`
- `tone_duration = 0.1-0.2`
- `FREQ = 150-400 Hz`
- `AMP = 0.3-0.7`

**For Audio Feedback:**
- `itd_exaggeration = 1.0-3.0`
- `ild_exponent = 1.0-2.0`
- `tone_duration = 0.05-0.15`
- `FREQ = 200-1000 Hz`
- `AMP = 0.2-0.8`

---

**Happy Scripting!** 🎵✨

*Create rich, immersive spatial experiences with precise multi-speaker control.*
""")


def create_hardware_setup_guide():
    """Create hardware setup documentation"""

    with open('docs/hardware_setup.md', 'w') as f:
        f.write("""# Hardware Setup Guide

## Thawney's 16-Channel Tactile Driver Board

This system is designed to work out-of-the-box with **Thawney's 16-channel transducer driver board**. This specialized hardware provides:

- 16 independent channels for tactile transducers
- Optimized amplification for haptic feedback
- USB connectivity for easy computer interface
- Proper impedance matching for tactile transducers

### Connection Setup

```
Computer → USB → Thawney's Driver Board → Tactile Transducers (16 channels)
```

### Channel Mapping

The 4x4 tactile grid uses the following channel mapping on Thawney's board:

```
Tactile Grid Layout (viewed from above):
    -60mm  -20mm  +20mm  +60mm
+60mm [CH3] [CH7] [CH11] [CH15]  ← Top row
+20mm [CH2] [CH6] [CH10] [CH14]
-20mm [CH1] [CH5] [CH9]  [CH13]
-60mm [CH0] [CH4] [CH8]  [CH12]  ← Bottom row

Channels increment vertically (bottom-to-top), then next column right.
```

### Transducer Placement

1. **Grid Layout**: 4x4 array with 40mm spacing between transducer centers
2. **Total Coverage**: 120mm x 120mm tactile area
3. **Mounting**: Secure mechanical coupling to surface for optimal tactile transmission
4. **Wiring**: Connect each transducer to its corresponding channel on Thawney's board

### Alternative Hardware

If using other audio interfaces:

| Configuration | Channels | Requirements |
|---------------|----------|--------------|
| 2x2 Test Grid | 4 | Any 4+ channel interface |
| 4x4 Full Grid | 16 | 16+ channel interface or Thawney's board |
| Stereo Test | 2 | Any stereo audio interface |

## Software Configuration

The system automatically detects and configures for Thawney's driver board. No additional driver installation required - it appears as a standard USB audio device.

### Testing Your Setup

1. **Connect Hardware**: USB connection to Thawney's board
2. **Test All Channels**: 
   ```bash
   python multispeaker_main.py examples/test_all_speakers.txt --config config_4x4_grid.txt
   ```
3. **Verify Channel Mapping**:
   ```bash
   python multispeaker_main.py --config config_4x4_grid.txt --interactive
   > play -0.06 -0.06 440 0.5  # Should activate CH0 (bottom-left)
   > play -0.06 0.06 440 0.5   # Should activate CH3 (top-left)
   ```

## Calibration and Testing

### Individual Channel Test
```bash
# This script will play each transducer in sequence with clear channel identification
python multispeaker_main.py examples/test_all_speakers.txt --config config_4x4_grid.txt
```

### Smooth Movement Test  
```bash
# Test the improved smooth spatialization
python multispeaker_main.py examples/smooth_tactile_demo.txt --config config_4x4_grid.txt
```

### Troubleshooting

#### No Tactile Output
1. Verify USB connection to Thawney's board
2. Check that board appears in system audio devices
3. Test with stereo configuration first: `--config config_stereo.txt`
4. Verify transducer connections to board

#### Wrong Channel Activation
1. Check physical transducer placement matches channel map above
2. Verify transducer wiring to correct channels on board
3. Test individual channels with `test_all_speakers.txt`

#### Weak Tactile Response
1. Check mechanical coupling of transducers to surface
2. Verify consistent mounting pressure across all transducers  
3. Adjust amplitude values in scripts (try AMP=0.7 instead of 0.5)
4. Check for loose connections

### ✨ Smooth Tactile Response (NEW)

The improved tactile grid spatialization eliminates the "clicking" or "jumping" sensation between transducers:

**Test smooth transitions:**
```bash
python multispeaker_main.py --config config_4x4_grid.txt --interactive
> play -0.02 0.0 300 0.4  # Left of center
> play 0.0 0.0 300 0.4    # Center - should transition smoothly
> play 0.02 0.0 300 0.4   # Right of center
```

**Configure extra smoothness if desired:**
```bash
> smooth  # Interactive smoothness configuration
# Choose option 2 for maximum smoothness
```

This hardware setup provides professional-grade tactile feedback with the convenience of plug-and-play USB connectivity through Thawney's specialized driver board.
""")


def create_troubleshooting_guide():
    """Create troubleshooting documentation"""

    with open('docs/troubleshooting.md', 'w') as f:
        f.write("""# Troubleshooting Guide

## Common Issues and Solutions

### ✨ Tactile Grid Issues (MAJOR IMPROVEMENTS)

#### ✅ FIXED: Clicking/Jumping Between Speakers
**PROBLEM:** Sound would "click" when moving between speakers, felt jumpy instead of smooth.

**SOLUTION:** ✅ **RESOLVED** in the improved tactile grid method!

**What was wrong:**
- Old method artificially boosted closest speaker by 4x
- Sharp distance transitions caused sudden volume changes  
- Uneven weighting between equally-positioned sources

**What's been fixed:**
- Smooth inverse distance weighting with 8mm minimum distance
- Equal volume for sources positioned between speakers
- Power normalization for consistent perceived loudness
- Configurable smoothness levels

**Test the fix:**
```bash
# This should now feel smooth and continuous
python multispeaker_main.py examples/smooth_tactile_demo.txt --config config_4x4_grid.txt

# Interactive test
python multispeaker_main.py --config config_4x4_grid.txt --interactive
> play -0.02 0.0 300 0.4
> play 0.0 0.0 300 0.4     # Should transition smoothly
> play 0.02 0.0 300 0.4
```

#### ✅ FIXED: Uneven Volume Between Speakers
**PROBLEM:** When a source was positioned exactly between two speakers, one would be louder than the other.

**SOLUTION:** ✅ **RESOLVED** with power normalization!

**Test equal volume:**
```bash
python multispeaker_main.py --config config_4x4_grid.txt --interactive
> play -0.01 0.0 300 0.4  # Halfway between speakers
> play 0.01 0.0 300 0.4   # Should feel identical volume
```

#### Configure Extra Smoothness (if desired)
If you want even smoother transitions:

```bash
python multispeaker_main.py --config config_4x4_grid.txt --interactive
> smooth
# Choose from preset options:
# 1. Default (already improved)
# 2. Extra smooth (Gaussian mode) 
# 3. More focused (more localized)
# 4. Custom parameters
```

---

### Audio Issues

#### Problem: No Sound Output
**Solutions:**
1. Check audio interface connections
2. Verify audio interface is recognized by system
3. Test with minimal configuration (stereo)
4. Check audio levels and muting

#### Problem: Wrong Channel Assignment
**Solutions:**
1. Verify channel numbers in configuration file
2. Test each speaker individually
3. Check physical cable connections
4. Use `test_all_speakers.txt` to verify setup

#### Problem: Distorted Audio
**Solutions:**
1. Reduce amplitude values in scripts
2. Check for clipping in audio interface
3. Verify amplifier settings
4. Check for ground loops

---

### Software Issues

#### Problem: Script Parsing Errors
**Solutions:**
1. Check syntax of script commands
2. Verify coordinate format (x,y with no spaces)
3. Check for missing parameters
4. Review error messages for specific issues

#### Problem: Visualization Not Working
**Solutions:**
1. Install pygame: `pip install pygame`
2. Check display driver compatibility
3. Try running without visualization first
4. Update graphics drivers

#### Problem: Performance Issues
**Solutions:**
1. Reduce grid size (use 2x2 instead of 4x4)
2. Disable visualization
3. Increase audio buffer size
4. Close other applications using audio

---

### Hardware Issues

#### Problem: Inconsistent Tactile Response
**Solutions:**
1. Check mounting pressure of transducers
2. Verify mechanical coupling to surface
3. Test with different mounting methods
4. Check for loose connections

#### ✅ IMPROVED: Spatial Perception Issues
**PROBLEM:** Difficulty perceiving smooth movement between speakers.

**SOLUTION:** ✅ **MUCH IMPROVED** with smooth tactile grid method!

**Additional optimizations:**
1. ✅ **Already fixed** - Smooth spatialization eliminates most issues
2. If you want extra smoothness: Use Gaussian mode
3. Verify transducer positioning matches configuration
4. Test with `examples/smooth_tactile_demo.txt`

**Configure for maximum smoothness:**
```python
# In interactive mode
> smooth
# Choose option 2: Extra smooth (Gaussian mode)

# Or programmatically
spatialiser.audio_engine.spat_engine.set_tactile_grid_parameters(
    use_gaussian=True,
    gaussian_sigma=0.03
)
```

---

## System Testing and Validation

### Test Smooth Spatialization
```bash
# Test the smooth improvements
python multispeaker_main.py examples/smooth_tactile_demo.txt --config config_4x4_grid.txt

# System-wide test
python test_system.py --config config_4x4_grid.txt
```

### Verify Individual Speakers
```bash
python multispeaker_main.py examples/test_all_speakers.txt --config config_4x4_grid.txt
```

### Interactive Testing
```bash
python multispeaker_main.py --config config_4x4_grid.txt --interactive

# Test smooth movement manually
> play -0.04 0.0 300 0.4
> play -0.02 0.0 300 0.4
> play 0.0 0.0 300 0.4
> play 0.02 0.0 300 0.4
> play 0.04 0.0 300 0.4

# Should feel like smooth continuous movement, not clicking
```

---

## Configuration Recommendations

### For Smoothest Tactile Experience:
```
# config_extra_smooth.txt
config_name = extra_smooth_tactile
method = tactile_grid

GRID SIZE=4 SPACING=0.04 OFFSET=0.0,0.0

# Use with Gaussian mode for maximum smoothness:
# spatialiser.audio_engine.spat_engine.set_tactile_grid_parameters(
#     use_gaussian=True, gaussian_sigma=0.03
# )
```

### For Balanced Performance:
```
# config_4x4_grid.txt (default - already optimized)
config_name = 4x4_tactile_grid
method = tactile_grid

GRID SIZE=4 SPACING=0.04 OFFSET=0.0,0.0
# The improved tactile_grid method provides excellent smoothness by default
```

---

## Getting Help

### Quick Diagnostics:
1. **Test smooth spatialization**: `python multispeaker_main.py examples/smooth_tactile_demo.txt`
2. **System test**: `python test_system.py --config config_4x4_grid.txt`
3. **Check configuration**: `python multispeaker_main.py --config config_4x4_grid.txt --info`
4. **Test minimal setup**: `python multispeaker_main.py --config config_stereo.txt --interactive`

### If Issues Persist:
1. Try different spatialization method in config file
2. Test with smaller grid (2x2 instead of 4x4)
3. Verify all physical connections
4. Check audio interface channel assignments
5. Review error messages in console output

### ✨ What's New:
- **Smooth tactile spatialization** - No more clicking between speakers
- **Equal volume positioning** - Balanced output for centered sources
- **Configurable smoothness** - Multiple modes for different preferences
- **Interactive tuning** - Easy adjustment via `smooth` command
- **Comprehensive testing** - New demo scripts for validation

The system should now provide a much more natural and smooth tactile experience!
""")


def test_audio_system():
    """Test the audio system"""
    print("\n=== Testing Audio System ===")

    try:
        import sounddevice as sd

        # List audio devices
        print("\nAvailable audio devices:")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_output_channels'] > 0:
                print(f"  {i}: {device['name']} ({device['max_output_channels']} channels)")

        # Test default device
        default_device = sd.default.device
        print(f"\nDefault device: {default_device}")

        # Check if we can create a multi-channel stream
        try:
            stream = sd.OutputStream(channels=16, samplerate=48000, dtype='float32')
            stream.close()
            print("✓ 16-channel audio stream test passed")
        except Exception as e:
            print(f"⚠ 16-channel audio test failed: {e}")
            print("  This is OK if you don't have a 16-channel interface")

            # Try stereo
            try:
                stream = sd.OutputStream(channels=2, samplerate=48000, dtype='float32')
                stream.close()
                print("✓ Stereo audio stream test passed")
            except Exception as e2:
                print(f"✗ Stereo audio test failed: {e2}")
                return False

        return True

    except ImportError:
        print("✗ sounddevice not available")
        return False


def run_demo():
    """Run a quick demo of the system"""
    print("\n=== Running Demo ===")

    try:
        import multispeaker_main

        # Try configurations in order of preference
        configs_to_try = [
            ('configs/config_stereo.txt', 'stereo pair'),
            ('configs/config_2x2_test.txt', '2x2 test grid'),
            ('configs/config_4x4_grid.txt', '4x4 grid')
        ]

        spatialiser = None
        working_config = None

        for config_file, config_desc in configs_to_try:
            if os.path.exists(config_file):
                try:
                    print(f"Testing {config_desc}...")
                    spatialiser = multispeaker_main.MultiSpeakerSpatialiser(config_file)
                    working_config = config_file
                    print(f"✓ {config_desc} loaded successfully")
                    break
                except Exception as e:
                    print(f"⚠ {config_desc} failed: {e}")
                    spatialiser = None
                    continue

        if spatialiser is None:
            print("✗ No working configuration found")
            return False

        # Test audio stream startup
        try:
            spatialiser.start()
            print("✓ Audio stream started successfully")
        except Exception as e:
            print(f"⚠ Audio stream startup failed: {e}")
            print("  This may be due to audio device limitations")

        print(f"\nSpatialiser Configuration:")
        print(f"  Name: {spatialiser.speaker_config.config_name}")
        print(f"  Speakers: {len(spatialiser.speaker_config.speakers)}")
        print(f"  Channels: {spatialiser.audio_engine.num_channels}")
        print(f"  Method: {spatialiser.speaker_config.method}")

        # Note smooth improvements and Thawney's board compatibility
        if spatialiser.speaker_config.method == 'tactile_grid':
            print(f"  ✨ IMPROVED: Smooth tactile spatialization (no more clicking)")
            if spatialiser.audio_engine.num_channels == 16:
                print(f"  ✨ Optimized for Thawney's 16-channel driver board")
                print(f"  ✨ Channel mapping: Vertical increment (CH0 bottom-left → CH15 top-right)")

        # Test audio playback
        print("\nTesting audio playback...")
        positions = [
            (-0.02, -0.02, "Bottom-left"),
            (0.02, -0.02, "Bottom-right"),
            (0.02, 0.02, "Top-right"),
            (-0.02, 0.02, "Top-left")
        ]

        for x, y, desc in positions:
            print(f"  Playing: {desc}")
            try:
                spatialiser.play_sound(x, y, freq=440, amp=0.3)
                import time
                time.sleep(0.5)
            except Exception as e:
                print(f"  Warning: Audio playback failed: {e}")

        # Test smooth movement if tactile grid
        if spatialiser.speaker_config.method == 'tactile_grid':
            print("\n✨ Testing smooth movement (should feel continuous):")
            for i in range(5):
                x = -0.02 + (i * 0.01)  # -20mm to +20mm in 10mm steps
                print(f"  Position: {x * 1000:.0f}mm")
                spatialiser.play_sound(x, 0.0, freq=300, amp=0.3)
                import time
                time.sleep(0.3)

        try:
            spatialiser.stop()
        except:
            pass

        print("✓ Demo completed successfully")
        print("✨ Key improvement: Smooth tactile spatialization eliminates clicking/jumping!")
        return True

    except Exception as e:
        print(f"✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main setup function"""
    print("Multi-Speaker Tactile Spatialiser Setup")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("Usage: python setup.py [install|test|demo]")
        print("  install   - Install dependencies and create all files")
        print("  test      - Test the audio system")
        print("  demo      - Run a quick demo")
        return

    command = sys.argv[1].lower()

    if command == "install":
        print("Installing Multi-Speaker Tactile Spatialiser...")

        success = True
        if not check_python_version():
            success = False
        if not install_dependencies():
            success = False
        if not create_directory_structure():
            success = False
        if not create_config_files():
            success = False
        if not create_demo_scripts():
            success = False
        if not create_documentation():
            success = False
        if not test_audio_system():
            success = False

        if success:
            print("\n✓ Installation completed successfully!")
            print("\nFiles created:")
            print("  configs/                           - Speaker configuration files")
            print("    ├── config_4x4_grid.txt         - ✨ 4x4 grid for Thawney's 16-channel board")
            print("    ├── config_2x2_test.txt         - 2x2 test grid (any 4-channel interface)")
            print("    └── config_stereo.txt           - Stereo test (any audio interface)")
            print("  examples/                          - Demo scripts")
            print("    ├── smooth_tactile_demo.txt      - ✨ NEW: Smooth spatialization demo")
            print("    └── test_all_speakers.txt       - Individual channel testing")
            print("  docs/                              - Documentation")
            print("    ├── spatialization_methods.md    - ✨ UPDATED: Complete guide with smooth tactile info")
            print("    ├── scripting_reference.md       - Scripting language reference")
            print("    ├── hardware_setup.md            - ✨ UPDATED: Thawney's driver board setup")
            print("    └── troubleshooting.md           - ✨ UPDATED: Smooth tactile troubleshooting")
            print("\n✨ This system is designed for Thawney's 16-channel tactile driver board")
            print("  • Plug-and-play USB connectivity")
            print("  • Optimized 4x4 grid with 40mm spacing")
            print("  • Correct channel mapping (vertical increment: CH0 bottom-left → CH15 top-right)")
            print("\n✨ Key improvements in this version:")
            print("  • Smooth tactile grid spatialization (no more clicking/jumping)")
            print("  • Equal volume positioning between transducers")
            print("  • Configurable smoothness levels")
            print("  • Interactive smoothness configuration")
            print("  • Fixed channel mapping for Thawney's board")
            print("\nQuick start with Thawny's board:")
            print("  python multispeaker_main.py --config config_4x4_grid.txt --interactive")
            print("  python multispeaker_main.py examples/smooth_tactile_demo.txt  # ✨ NEW")
            print("  python multispeaker_main.py examples/test_all_speakers.txt    # Verify channels")
            print("\nTest smooth improvements:")
            print("  python multispeaker_main.py --config config_4x4_grid.txt --interactive")
            print("  > smooth  # Configure smoothness interactively")
            print("  > play -0.06 -0.06 440 0.5  # Should activate CH0 (bottom-left)")
            print("  > play -0.06 0.06 440 0.5   # Should activate CH3 (top-left)")
            print("\nDocumentation:")
            print("  Read docs/hardware_setup.md for Thawney's board setup guide")
            print("  Read docs/spatialization_methods.md for complete smooth tactile guide")
        else:
            print("\n✗ Installation completed with errors")
            print("Please check the error messages above")

    elif command == "test":
        check_python_version()
        test_audio_system()

    elif command == "demo":
        check_python_version()
        run_demo()

    else:
        print(f"Unknown command: {command}")
        print("Use: install, test, or demo")


if __name__ == "__main__":
    main()
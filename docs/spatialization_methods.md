# Multi-Speaker Spatialization Methods Guide

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

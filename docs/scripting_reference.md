# Multi-Speaker Tactile Spatialiser Scripting Language Reference

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
ARC <x1>,<y1> <x2>,<y2> [<x3>,<y3>] \
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
PATH_FREQ_RAMP <x1>,<y1> <x2>,<y2> [<x3>,<y3>] \
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

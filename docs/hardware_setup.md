# Hardware Setup Guide

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

The system automatically detects and configures for Thawney's driver board. It appears as a standard class compliant USB audio device. If you are on windows you will need to install the minidsp driver provided and make sure your windows sound setup is aware it is a 16 channel device, otherwise it may treat it as stereo.

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

# Troubleshooting Guide

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

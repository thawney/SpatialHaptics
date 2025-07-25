# Multi-Speaker Tactile Spatialiser

## Quick Start

1. **Install and setup:**
   ```bash
   python setup.py install
   ```

2. **Test your hardware:**
   ```bash
   python setup.py demo
   ```

3. **Start using the system:**
   ```bash
   # Interactive mode
   python multispeaker_main.py --config config_4x4_grid.txt --interactive
   
   # Run example scripts
   python multispeaker_main.py examples/smooth_tactile_demo.txt
   python multispeaker_main.py examples/test_all_speakers.txt
   ```

## Documentation

After running `python setup.py install`, find complete documentation in:

- **`docs/hardware_setup.md`** - Setting up Thawney's 16-channel driver board
- **`docs/spatialization_methods.md`** - Complete guide to smooth tactile spatialization
- **`docs/scripting_reference.md`** - How to write tactile scripts
- **`docs/troubleshooting.md`** - Solutions to common problems

## Configuration Files

- **`configs/config_4x4_grid.txt`** - 4x4 tactile grid (16 channels)
- **`configs/config_2x2_test.txt`** - 2x2 test grid (4 channels) 
- **`configs/config_stereo.txt`** - Stereo testing (2 channels)

## Example Scripts

- **`examples/smooth_tactile_demo.txt`** - Demonstrates smooth spatialization
- **`examples/test_all_speakers.txt`** - Test individual channels
- **`examples/demo_4x4_grid.txt`** - Full 4x4 grid demonstration

## System Requirements

- Python 3.7+
- Thawney's 16-channel tactile driver board (recommended)
- OR any multi-channel audio interface

That's it! Run `python setup.py install` and check the docs folder for detailed guides.
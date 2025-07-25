#!/usr/bin/env python3
"""
setup.py - Multi-Speaker Tactile Spatialiser Setup Script - SIMPLE VERSION

This script installs the required dependencies for the multi-speaker tactile spatialiser system.

Usage:
  python setup.py install
  python setup.py test
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


def run_quick_demo():
    """Run a quick demo of the system"""
    print("\n=== Running Quick Demo ===")

    try:
        import multispeaker_main

        # Try stereo first (most compatible)
        config_file = 'configs/config_stereo.txt'
        if not os.path.exists(config_file):
            print(f"Config file {config_file} not found, skipping demo")
            return True

        try:
            print("Testing stereo configuration...")
            spatialiser = multispeaker_main.MultiSpeakerSpatialiser(config_file)
            spatialiser.start()

            print("✓ Spatialiser loaded successfully")
            print(f"  Configuration: {spatialiser.speaker_config.config_name}")
            print(f"  Speakers: {len(spatialiser.speaker_config.speakers)}")
            print(f"  Channels: {spatialiser.audio_engine.num_channels}")

            # Quick audio test
            print("Playing test sounds...")
            spatialiser.play_sound(-0.5, 0.0, freq=440, amp=0.3)  # Left
            import time
            time.sleep(0.5)
            spatialiser.play_sound(0.5, 0.0, freq=880, amp=0.3)   # Right
            time.sleep(0.5)

            spatialiser.stop()
            print("✓ Demo completed successfully")
            return True

        except Exception as e:
            print(f"⚠ Demo failed: {e}")
            return True  # Don't fail setup for demo issues

    except Exception as e:
        print(f"✗ Demo failed: {e}")
        return True  # Don't fail setup for demo issues


def main():
    """Main setup function"""
    print("Multi-Speaker Tactile Spatialiser Setup")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("Usage: python setup.py [install|test|demo]")
        print("  install   - Install required dependencies")
        print("  test      - Test the audio system")
        print("  demo      - Run a quick demo")
        return

    command = sys.argv[1].lower()

    if command == "install":
        print("Installing Multi-Speaker Tactile Spatialiser dependencies...")

        success = True
        if not check_python_version():
            success = False
        if not install_dependencies():
            success = False
        if not test_audio_system():
            success = False

        if success:
            print("\n✓ Installation completed successfully!")
            print("\nNext steps:")
            print("  1. Test with stereo: python multispeaker_main.py --config configs/config_stereo.txt --interactive")
            print("  2. Test all speakers: python multispeaker_main.py examples/test_all_speakers.txt")
            print("  3. Try visualization: python multispeaker_main.py examples/smooth_tactile_demo.txt --visualize")
            print("\nFor 16-channel setup:")
            print("  python multispeaker_main.py --config configs/config_4x4_grid.txt --interactive")
            print("\nKey improvements:")
            print("  • Smooth tactile grid spatialization (no more clicking/jumping)")
            print("  • Fixed Windows compatibility")
            print("  • Multiple spatialization methods")
        else:
            print("\n✗ Installation failed")
            print("Please check the error messages above")

    elif command == "test":
        check_python_version()
        test_audio_system()

    elif command == "demo":
        check_python_version()
        run_quick_demo()

    else:
        print(f"Unknown command: {command}")
        print("Use: install, test, or demo")


if __name__ == "__main__":
    main()
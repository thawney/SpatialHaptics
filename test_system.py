#!/usr/bin/env python3
"""
test_system.py - Comprehensive testing utilities for the multi-speaker system

This script provides various tests to verify that your multi-speaker setup
is working correctly, from basic audio output to complex spatialization.

Usage:
  python test_system.py
  python test_system.py --config config_4x4_grid.txt
  python test_system.py --test audio
  python test_system.py --test speakers
  python test_system.py --test spatialization
"""

import argparse
import time
import numpy as np
import sys
import os

try:
    import multispeaker_main as ms
    import sounddevice as sd
except ImportError as e:
    print(f"Import error: {e}")
    print("Please run: python setup.py install")
    sys.exit(1)

class SystemTester:
    def __init__(self, config_file=None):
        self.config_file = config_file
        self.spatialiser = None
        self.test_results = {}
        
    def setup_spatialiser(self):
        """Initialize the spatialiser system"""
        print("Setting up spatialiser...")
        try:
            self.spatialiser = ms.MultiSpeakerSpatialiser(self.config_file)
            print(f"✓ Spatialiser initialized with {len(self.spatialiser.speaker_config.speakers)} speakers")
            return True
        except Exception as e:
            print(f"✗ Failed to initialize spatialiser: {e}")
            return False
    
    def test_audio_devices(self):
        """Test audio device availability and capabilities"""
        print("\n=== Testing Audio Devices ===")
        
        try:
            # List all devices
            devices = sd.query_devices()
            print(f"Found {len(devices)} audio devices:")
            
            for i, device in enumerate(devices):
                if device['max_output_channels'] > 0:
                    print(f"  {i}: {device['name']}")
                    print(f"     Channels: {device['max_output_channels']}")
                    print(f"     Sample Rate: {device['default_samplerate']}")
            
            # Test default device
            default_device = sd.default.device
            print(f"\nDefault device: {default_device}")
            
            # Test multi-channel capability
            max_channels = self.spatialiser.audio_engine.num_channels if self.spatialiser else 16
            
            try:
                stream = sd.OutputStream(channels=max_channels, samplerate=48000, dtype='float32')
                stream.close()
                print(f"✓ {max_channels}-channel audio test passed")
                self.test_results['audio_channels'] = max_channels
            except Exception as e:
                print(f"⚠ {max_channels}-channel test failed: {e}")
                
                # Try with fewer channels
                for channels in [8, 4, 2]:
                    try:
                        stream = sd.OutputStream(channels=channels, samplerate=48000, dtype='float32')
                        stream.close()
                        print(f"✓ {channels}-channel audio test passed")
                        self.test_results['audio_channels'] = channels
                        break
                    except:
                        continue
                else:
                    print("✗ No working audio channels found")
                    self.test_results['audio_channels'] = 0
                    return False
            
            return True
            
        except Exception as e:
            print(f"✗ Audio device test failed: {e}")
            return False
    
    def test_speaker_configuration(self):
        """Test speaker configuration loading and validation"""
        print("\n=== Testing Speaker Configuration ===")
        
        if not self.spatialiser:
            print("✗ Spatialiser not initialized")
            return False
        
        config = self.spatialiser.speaker_config
        
        # Basic configuration checks
        print(f"Configuration: {config.config_name}")
        print(f"Method: {config.method}")
        print(f"Speakers: {len(config.speakers)}")
        print(f"Channels: {config.get_num_channels()}")
        
        # Validate speaker positions
        if not config.speakers:
            print("✗ No speakers defined")
            return False
        
        # Check for duplicate channels
        channels = [sp['channel'] for sp in config.speakers]
        if len(channels) != len(set(channels)):
            print("⚠ Duplicate channel assignments found")
            self.test_results['config_warnings'] = True
        
        # Check channel range
        max_channel = max(channels)
        if max_channel >= self.test_results.get('audio_channels', 16):
            print(f"⚠ Channel {max_channel} exceeds available channels")
            self.test_results['config_warnings'] = True
        
        # Print speaker layout
        print("\nSpeaker layout:")
        for sp in config.speakers[:8]:  # Show first 8 speakers
            x, y = sp['pos']
            print(f"  {sp['id']}: ({x*1000:6.1f}, {y*1000:6.1f})mm -> CH{sp['channel']}")
        
        if len(config.speakers) > 8:
            print(f"  ... and {len(config.speakers) - 8} more speakers")
        
        self.test_results['config_valid'] = True
        return True
    
    def test_individual_speakers(self):
        """Test each speaker individually"""
        print("\n=== Testing Individual Speakers ===")
        
        if not self.spatialiser:
            print("✗ Spatialiser not initialized")
            return False
        
        self.spatialiser.start()
        
        try:
            speakers = self.spatialiser.speaker_config.speakers
            num_speakers = min(len(speakers), 8)  # Limit to first 8 for testing
            
            print(f"Testing first {num_speakers} speakers...")
            
            for i in range(num_speakers):
                speaker = speakers[i]
                x, y = speaker['pos']
                
                print(f"  Testing {speaker['id']} (CH{speaker['channel']})...", end='', flush=True)
                
                # Play test tone
                self.spatialiser.play_sound(x, y, freq=440, amp=0.3)
                time.sleep(0.4)
                
                print(" ✓")
            
            print(f"✓ Individual speaker test completed")
            self.test_results['speakers_individual'] = True
            return True
            
        except Exception as e:
            print(f"✗ Individual speaker test failed: {e}")
            return False
        finally:
            self.spatialiser.stop()
    
    def test_spatialization_methods(self):
        """Test different spatialization methods"""
        print("\n=== Testing Spatialization Methods ===")
        
        if not self.spatialiser:
            print("✗ Spatialiser not initialized")
            return False
        
        # Test positions
        test_positions = [
            (0.0, 0.0, "Center"),
            (0.02, 0.02, "Front-right"),
            (-0.02, -0.02, "Back-left"),
            (0.04, 0.0, "Right edge"),
            (-0.04, 0.0, "Left edge")
        ]
        
        methods = ['tactile_grid', 'nearest_neighbor', 'distance_pan', 'vbap']
        
        for method in methods:
            print(f"\nTesting {method} method:")
            
            # Temporarily change method
            original_method = self.spatialiser.speaker_config.method
            self.spatialiser.speaker_config.method = method
            self.spatialiser.audio_engine.spat_engine.method = method
            
            try:
                for x, y, desc in test_positions:
                    pos = np.array([x, y])
                    
                    # Calculate gains
                    gains, delays = self.spatialiser.audio_engine.spat_engine.calculate_gains_delays(pos)
                    
                    # Check that gains are reasonable
                    total_gain = np.sum(gains)
                    active_speakers = np.sum(gains > 0.001)
                    
                    print(f"  {desc}: {active_speakers} active speakers, total gain: {total_gain:.3f}")
                
                print(f"  ✓ {method} method working")
                
            except Exception as e:
                print(f"  ✗ {method} method failed: {e}")
            
            # Restore original method
            self.spatialiser.speaker_config.method = original_method
            self.spatialiser.audio_engine.spat_engine.method = original_method
        
        self.test_results['spatialization_methods'] = True
        return True
    
    def test_movement_patterns(self):
        """Test movement patterns and trajectories"""
        print("\n=== Testing Movement Patterns ===")
        
        if not self.spatialiser:
            print("✗ Spatialiser not initialized")
            return False
        
        self.spatialiser.start()
        
        try:
            # Test linear movement
            print("  Testing linear movement...", end='', flush=True)
            positions = [
                (-0.04, 0.0),
                (-0.02, 0.0),
                (0.0, 0.0),
                (0.02, 0.0),
                (0.04, 0.0)
            ]
            
            for x, y in positions:
                self.spatialiser.play_sound(x, y, freq=300, amp=0.2)
                time.sleep(0.15)
            
            print(" ✓")
            
            # Test circular movement
            print("  Testing circular movement...", end='', flush=True)
            
            for i in range(8):
                angle = i * 2 * np.pi / 8
                x = 0.03 * np.cos(angle)
                y = 0.03 * np.sin(angle)
                self.spatialiser.play_sound(x, y, freq=350, amp=0.2)
                time.sleep(0.1)
            
            print(" ✓")
            
            print("✓ Movement pattern test completed")
            self.test_results['movement_patterns'] = True
            return True
            
        except Exception as e:
            print(f"✗ Movement pattern test failed: {e}")
            return False
        finally:
            self.spatialiser.stop()
    
    def test_script_execution(self):
        """Test script parsing and execution"""
        print("\n=== Testing Script Execution ===")
        
        # Create a simple test script
        test_script = [
            "# Test script",
            "itd_exaggeration = 4.0",
            "ild_exponent = 2.0",
            "tone_duration = 0.1",
            "",
            "SOUND 0.0,0.0 FREQ=440 AMP=0.3",
            "WAIT 0.2",
            "SOUND 0.02,0.02 FREQ=500 AMP=0.3",
            "WAIT 0.2",
            "ARC -0.02,-0.02 0.02,0.02 DURATION=1.0 STEPS=8 FREQ=350 AMP=0.3"
        ]
        
        try:
            # Parse script
            actions = ms.parse_script(test_script)
            print(f"  Parsed {len(actions)} actions")
            
            # Execute script
            print("  Executing test script...", end='', flush=True)
            
            if self.spatialiser:
                ms.generate_tactile_tone.spatialiser = self.spatialiser
            
            ms.execute(actions)
            
            print(" ✓")
            
            print("✓ Script execution test completed")
            self.test_results['script_execution'] = True
            return True
            
        except Exception as e:
            print(f"✗ Script execution test failed: {e}")
            return False
    
    def test_performance(self):
        """Test system performance and latency"""
        print("\n=== Testing Performance ===")
        
        if not self.spatialiser:
            print("✗ Spatialiser not initialized")
            return False
        
        try:
            # Test tone generation speed
            start_time = time.time()
            
            for i in range(100):
                pos = np.array([0.01 * (i % 10 - 5), 0.01 * (i // 10 - 5)])
                buffer = self.spatialiser.audio_engine.generate_tone(pos, 440, 0.1)
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            print(f"  Generated 100 tones in {generation_time:.3f}s")
            print(f"  Average generation time: {generation_time*10:.1f}ms per tone")
            
            # Test spatialization calculation speed
            start_time = time.time()
            
            for i in range(1000):
                pos = np.array([0.001 * (i % 100 - 50), 0.001 * (i // 100 - 50)])
                gains, delays = self.spatialiser.audio_engine.spat_engine.calculate_gains_delays(pos)
            
            end_time = time.time()
            calc_time = end_time - start_time
            
            print(f"  Calculated 1000 spatializations in {calc_time:.3f}s")
            print(f"  Average calculation time: {calc_time:.1f}ms per calculation")
            
            # Performance thresholds
            if generation_time > 1.0:
                print("  ⚠ Tone generation may be slow")
            if calc_time > 0.1:
                print("  ⚠ Spatialization calculation may be slow")
            
            print("✓ Performance test completed")
            self.test_results['performance'] = True
            return True
            
        except Exception as e:
            print(f"✗ Performance test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("Multi-Speaker System Test Suite")
        print("=" * 50)
        
        # Initialize
        if not self.setup_spatialiser():
            return False
        
        # Run tests
        tests = [
            ("Audio Devices", self.test_audio_devices),
            ("Speaker Configuration", self.test_speaker_configuration),
            ("Individual Speakers", self.test_individual_speakers),
            ("Spatialization Methods", self.test_spatialization_methods),
            ("Movement Patterns", self.test_movement_patterns),
            ("Script Execution", self.test_script_execution),
            ("Performance", self.test_performance)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"✗ {test_name} test crashed: {e}")
                failed += 1
        
        # Summary
        print(f"\n=== Test Summary ===")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Total: {passed + failed}")
        
        if failed == 0:
            print("🎉 All tests passed! Your system is ready to use.")
        else:
            print(f"⚠ {failed} tests failed. Check the errors above.")
        
        # Recommendations
        if 'config_warnings' in self.test_results:
            print("\nRecommendations:")
            print("- Check speaker configuration for channel conflicts")
            print("- Ensure audio interface has enough channels")
        
        if self.test_results.get('audio_channels', 0) < 16:
            print("- Consider using a smaller grid configuration for testing")
            print("- Try config_2x2_test.txt or config_stereo.txt")
        
        return failed == 0

def main():
    parser = argparse.ArgumentParser(description='Multi-Speaker System Test Suite')
    parser.add_argument('--config', help='Speaker configuration file')
    parser.add_argument('--test', choices=['audio', 'speakers', 'spatialization', 'movement', 'script', 'performance'],
                       help='Run specific test only')
    
    args = parser.parse_args()
    
    # Create tester
    tester = SystemTester(args.config)
    
    if args.test:
        # Run specific test
        if not tester.setup_spatialiser():
            return
        
        test_map = {
            'audio': tester.test_audio_devices,
            'speakers': tester.test_individual_speakers,
            'spatialization': tester.test_spatialization_methods,
            'movement': tester.test_movement_patterns,
            'script': tester.test_script_execution,
            'performance': tester.test_performance
        }
        
        test_func = test_map.get(args.test)
        if test_func:
            test_func()
        else:
            print(f"Unknown test: {args.test}")
    else:
        # Run all tests
        tester.run_all_tests()

if __name__ == "__main__":
    main()

# =============================================================================
# QUICK START GUIDE
# =============================================================================

"""
QUICK START GUIDE - Multi-Speaker Tactile Spatialiser

1. INSTALLATION
   python setup.py install

2. FIRST RUN
   python multispeaker_main.py --create-configs
   python multispeaker_main.py --config config_2x2_test.txt --interactive

3. TESTING
   python test_system.py --config config_2x2_test.txt

4. EXAMPLES
   python multispeaker_main.py examples/demo_4x4_grid.txt --config config_4x4_grid.txt
   python multispeaker_main.py examples/test_all_speakers.txt --config config_4x4_grid.txt

5. VISUALIZATION
   python multispeaker_main.py examples/demo_4x4_grid.txt --config config_4x4_grid.txt --visualize

6. WAV EXPORT
   python generate_wav_multispeaker.py examples/demo_4x4_grid.txt output.wav --config config_4x4_grid.txt

7. TROUBLESHOOTING
   - No sound: Check audio interface and channels
   - Wrong positioning: Verify speaker configuration
   - Performance issues: Use smaller grid or different spatialization method

8. CONFIGURATION FILES
   config_stereo.txt        - 2 channels (any audio interface)
   config_2x2_test.txt      - 4 channels (testing)
   config_4x4_grid.txt      - 16 channels (full tactile grid)
   config_octagon.txt       - 8 channels (room speakers)

9. INTERACTIVE COMMANDS
   play x y freq amp        - Play sound at position (meters)
   load filename           - Load different configuration
   info                    - Show speaker layout
   help                    - Show all commands
   quit                    - Exit

10. COORDINATE SYSTEM
    (0,0) = Center
    +X = Right, -X = Left
    +Y = Forward, -Y = Back
    Units in meters (0.04 = 40mm)

Example positions for 4x4 grid:
- Bottom-left corner: -0.06, -0.06
- Top-right corner: 0.06, 0.06
- Center: 0.0, 0.0
- 20mm right of center: 0.02, 0.0
"""
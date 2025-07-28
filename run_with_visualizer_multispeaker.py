#!/usr/bin/env python3
"""
Multi-Speaker Tactile Spatialiser with Visualization - FIXED DEVICE SELECTION
Run this script to execute a tactile script with real-time visualization.

FIXES APPLIED:
- Proper device ID passing from main script to visualizer
- No double execution issues
- Better error handling
- User's device selection is respected
- Strict device enforcement (no fallback)

Usage:
  python run_with_visualizer_multispeaker.py script_file.txt
  python run_with_visualizer_multispeaker.py script_file.txt --config config_4x4_grid.txt
  python run_with_visualizer_multispeaker.py script_file.txt --config config_4x4_grid.txt --device 60
"""
import os
import sys
import time
import threading
import queue
import argparse
import multispeaker_main as main

# Message queue for communication between threads
position_queue = queue.Queue()


def position_callback(position, action):
    """Called when position is updated in the main script."""
    position_queue.put((position, action))


def main_cli():
    parser = argparse.ArgumentParser(description='Run Multi-Speaker Spatialiser with visualization')
    parser.add_argument('script', nargs='?', help='Path to script file')
    parser.add_argument('--config', help='Speaker configuration file')
    parser.add_argument('--device', type=int, help='Audio device ID to use')
    args = parser.parse_args()

    # Prompt if missing
    script_path = args.script
    while not script_path or not os.path.isfile(script_path):
        script_path = input("Enter path to script file: ").strip()

    print("=" * 60)
    print("Multi-Speaker Spatialiser with Visualization (FIXED)")
    print("=" * 60)
    print(f"Script: {script_path}")
    print(f"Config: {args.config if args.config else 'default 4x4 grid'}")
    if args.device is not None:
        print(f"Device: {args.device} (STRICT MODE - no fallback)")
    else:
        print("Device: Auto-select (will try to find suitable device)")
    print("FIXED: Device selection now properly passed to visualizer!")
    print("FIXED: No more fallback to wrong devices!")
    print("=" * 60)

    # Initialize spatialiser with proper device ID passing - FIXED!
    print("Initializing spatialiser...")
    try:
        spatialiser = main.MultiSpeakerSpatialiser(args.config, device_id=args.device)

        # Set up the callback for visualization
        main.set_visualizer_callback(position_callback)

        # CRITICAL: Set the global spatialiser to prevent double creation
        main.generate_tactile_tone.spatialiser = spatialiser
        print(f"Using configuration: {spatialiser.speaker_config.config_name}")
        print(f"Speakers: {len(spatialiser.speaker_config.speakers)}")
        print(f"Channels: {spatialiser.audio_engine.num_channels}")
        if args.device is not None:
            print(f"Requested device: {args.device} (strict mode)")

    except Exception as e:
        print(f"ERROR: Failed to initialize spatialiser: {e}")
        if args.device is not None:
            print(f"Cannot use device {args.device}. Use --list-devices to see available devices.")
            print(f"Use --test-device {args.device} to test this specific device.")
        return

    # Import visualizer module - will start pygame
    try:
        import visualizer_multispeaker as visualizer
        print("Visualizer module loaded successfully")
    except ImportError:
        print("Warning: visualizer_multispeaker not found, trying original visualizer")
        try:
            import visualizer
            print("Original visualizer module loaded")
        except ImportError:
            print("Error: No visualizer module found")
            return

    # Parse the script
    print("Parsing script...")
    try:
        with open(script_path, 'r') as f:
            lines = f.read().splitlines()
        actions = main.parse_script(lines)
        print(f"Parsed {len(actions)} actions successfully")
    except Exception as e:
        print(f"Error parsing script: {e}")
        return

    # Extract paths for visualization (if supported)
    if hasattr(visualizer, 'extract_paths_from_actions'):
        try:
            visualizer.extract_paths_from_actions(actions)
            print("Extracted paths for visualization")
        except Exception as e:
            print(f"Warning: Could not extract paths: {e}")

    # Set speaker configuration for visualizer
    if hasattr(visualizer, 'set_speaker_config'):
        try:
            visualizer.set_speaker_config(spatialiser.speaker_config)
            print("Speaker configuration set for visualizer")
        except Exception as e:
            print(f"Warning: Could not set speaker config for visualizer: {e}")

    # Start execution in a separate thread
    def execute_thread():
        print("Starting script execution in background thread...")
        try:
            # Use the execute_with_visualization function
            main.execute_with_visualization(actions)
            print("Script execution completed")
        except Exception as e:
            print(f"Error during script execution: {e}")
        finally:
            # Cleanup
            try:
                spatialiser.stop()
                print("Audio system stopped")
            except:
                pass

    # Start the execution thread
    thread = threading.Thread(target=execute_thread)
    thread.daemon = True
    thread.start()

    # Start the visualizer (blocking call, will return when closed)
    print("Starting visualizer (close window to exit)...")
    try:
        visualizer.run_visualization(position_queue)
    except Exception as e:
        print(f"Visualizer error: {e}")
    finally:
        print("Visualization closed. Stopping playback.")
        # Ensure cleanup
        try:
            spatialiser.stop()
        except:
            pass


if __name__ == "__main__":
    main_cli()
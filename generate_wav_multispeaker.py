#!/usr/bin/env python3
"""
Helper script to convert a tactile spatialiser script file into a multi-channel WAV audio file.

Usage:
  python generate_wav_multispeaker.py path/to/script.txt output.wav
  python generate_wav_multispeaker.py path/to/script.txt output.wav --config config_4x4_grid.txt
  
  If arguments are omitted, you'll be prompted.
"""
import os
import numpy as np
import argparse
import soundfile as sf
import multispeaker_main as main

def script_to_buffer(script_path, config_path=None):
    """
    Parse a script file and convert its actions into a multi-channel buffer.
    """
    # Initialize the spatialiser
    spatialiser = main.MultiSpeakerSpatialiser(config_path)
    
    # Read and parse actions
    with open(script_path, 'r') as f:
        lines = f.read().splitlines()
    actions = main.parse_script(lines)
    
    # Set up the spatialiser for the script
    main.generate_tactile_tone.spatialiser = spatialiser
    
    buffers = []
    sr = spatialiser.audio_engine.sample_rate
    current_pos = np.array([0.0, 0.0])  # Track current position
    
    print(f"Processing {len(actions)} actions...")
    print(f"Output format: {spatialiser.audio_engine.num_channels} channels at {sr}Hz")
    
    for i, act in enumerate(actions):
        if i % 10 == 0:
            print(f"Processing action {i+1}/{len(actions)}: {act[0]}")
        
        cmd = act[0]
        
        if cmd == 'WAIT':
            duration = act[1]
            n = int(duration * sr)
            silence = np.zeros((n, spatialiser.audio_engine.num_channels), dtype=np.float32)
            buffers.append(silence)

        elif cmd == 'JUMP':
            # No sound, just reposition
            current_pos = act[1]
            continue

        elif cmd == 'SOUND':
            _, pos, freq, amp = act
            current_pos = pos
            buf = spatialiser.audio_engine.generate_tone(pos, freq, amp)
            buffers.append(buf.astype(np.float32))

        elif cmd == 'ARC':
            _, points, duration, steps, freq, amp, mode = act

            if steps <= 0:
                print("Warning: ARC with steps <= 0, skipping")
                continue

            # Calculate the time for each step
            step_time = duration / steps

            # Handle step-by-step interpolation
            for j in range(steps):
                t = j / (steps - 1) if steps > 1 else 0

                if mode == 'CURVED' and len(points) == 3:
                    # Quadratic Bézier via midpoint
                    P0, Pm, P1 = points[0], points[1], points[2]
                    pos = (1 - t) ** 2 * P0 + 2 * (1 - t) * t * Pm + t ** 2 * P1
                else:
                    # Linear interpolation between first and last points
                    P0, P1 = points[0], points[-1]
                    pos = P0 * (1 - t) + P1 * t

                current_pos = pos
                buf = spatialiser.audio_engine.generate_tone(pos, freq, amp)
                buffers.append(buf.astype(np.float32))

                # Add silence between bursts if not the last step
                if j < steps - 1:
                    wait_samples = int((step_time - spatialiser.audio_engine.tone_duration) * sr)
                    if wait_samples > 0:
                        silence = np.zeros((wait_samples, spatialiser.audio_engine.num_channels), dtype=np.float32)
                        buffers.append(silence)

        elif cmd == 'CIRCLE_SMOOTH':
            _, radius, duration, steps, freq, amp = act
            
            # Generate continuous circular sweep
            N = int(duration * sr)
            t = np.arange(N) / sr
            ang = 2 * np.pi * (t / duration)
            
            # Pre-allocate buffer
            buf = np.zeros((N, spatialiser.audio_engine.num_channels), dtype=np.float32)
            
            # Generate sound for each time step
            for j in range(0, N, int(sr * 0.01)):  # Update every 10ms
                end_idx = min(j + int(sr * 0.01), N)
                
                # Calculate position for this time segment
                t_seg = j / sr
                angle = 2 * np.pi * (t_seg / duration)
                x = radius * np.sin(angle)
                y = radius * np.cos(angle)
                pos = np.array([x, y])
                
                # Generate short segment
                segment_length = end_idx - j
                t_segment = np.arange(segment_length) / sr
                
                # Calculate gains for this position
                gains, delays = spatialiser.audio_engine.spat_engine.calculate_gains_delays(pos)
                
                # Apply window
                window = np.ones(segment_length)
                if segment_length > 100:  # Only apply fade if segment is long enough
                    fade_len = min(50, segment_length // 4)
                    ramp = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
                    window[:fade_len] = ramp
                    window[-fade_len:] = ramp[::-1]
                
                # Generate tone for each channel
                for k, speaker in enumerate(spatialiser.speaker_config.speakers):
                    channel = speaker['channel']
                    gain = gains[k]
                    delay = delays[k]
                    
                    if gain > 0.001 and channel < spatialiser.audio_engine.num_channels:
                        # Generate tone with delay
                        if delay != 0:
                            tone = amp * gain * np.sin(2 * np.pi * freq * (t_segment + j/sr - delay))
                        else:
                            tone = amp * gain * np.sin(2 * np.pi * freq * (t_segment + j/sr))
                        
                        # Apply window
                        tone *= window
                        
                        # Add to buffer
                        buf[j:end_idx, channel] += tone
                        
            buffers.append(buf)

        elif cmd == 'FREQ_RAMP':
            _, pos, start_freq, end_freq, duration, steps, amp = act

            if steps <= 0:
                print("Warning: FREQ_RAMP with steps <= 0, skipping")
                continue

            # Calculate step-by-step frequencies
            step_time = duration / steps
            
            for j in range(steps):
                t = j / (steps - 1) if steps > 1 else 0

                # Linear interpolation of frequency
                freq = start_freq * (1 - t) + end_freq * t

                current_pos = pos
                buf = spatialiser.audio_engine.generate_tone(pos, freq, amp)
                buffers.append(buf.astype(np.float32))

                # Add silence between bursts if not the last step
                if j < steps - 1:
                    wait_samples = int((step_time - spatialiser.audio_engine.tone_duration) * sr)
                    if wait_samples > 0:
                        silence = np.zeros((wait_samples, spatialiser.audio_engine.num_channels), dtype=np.float32)
                        buffers.append(silence)

        elif cmd == 'FREQ_RAMP_SMOOTH':
            _, pos, start_freq, end_freq, duration, amp = act

            # Generate continuous frequency ramp
            N = int(duration * sr)
            t = np.arange(N) / sr
            
            # Linear frequency ramp
            freq_t = start_freq + (end_freq - start_freq) * (t / duration)
            
            # Calculate phase by integrating frequency
            phase = 2 * np.pi * np.cumsum(freq_t) / sr
            
            # Calculate gains and delays for fixed position
            gains, delays = spatialiser.audio_engine.spat_engine.calculate_gains_delays(pos)
            
            # Create multi-channel buffer
            buf = np.zeros((N, spatialiser.audio_engine.num_channels), dtype=np.float32)
            
            # Apply fade in/out
            window = np.ones(N)
            if N > spatialiser.audio_engine.fade_len * 2:
                fade_len = spatialiser.audio_engine.fade_len
                ramp = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
                window[:fade_len] = ramp
                window[-fade_len:] = ramp[::-1]
            
            # Generate tone for each channel
            for k, speaker in enumerate(spatialiser.speaker_config.speakers):
                channel = speaker['channel']
                gain = gains[k]
                delay = delays[k]
                
                if gain > 0.001 and channel < spatialiser.audio_engine.num_channels:
                    # Generate tone with delay
                    if delay != 0:
                        tone = amp * gain * np.sin(phase - 2 * np.pi * freq_t * delay)
                    else:
                        tone = amp * gain * np.sin(phase)
                    
                    # Apply window
                    tone *= window
                    
                    # Add to buffer
                    buf[:, channel] = tone
                    
            buffers.append(buf)

        elif cmd == 'PATH_FREQ_RAMP':
            _, points, start_freq, end_freq, duration, steps, amp, mode = act

            if steps <= 0:
                print("Warning: PATH_FREQ_RAMP with steps <= 0, skipping")
                continue

            # Generate continuous buffer with both position and frequency changes
            N = int(duration * sr)
            t = np.arange(N) / sr
            normalized_t = t / duration

            # Calculate positions along the path
            positions = np.zeros((N, 2))

            if mode == 'CURVED' and len(points) == 3:
                # Quadratic Bézier via midpoint
                P0, Pm, P1 = points[0], points[1], points[2]
                for j, nt in enumerate(normalized_t):
                    positions[j] = (1 - nt) ** 2 * P0 + 2 * (1 - nt) * nt * Pm + nt ** 2 * P1
            else:
                # Linear interpolation between first and last points
                P0, P1 = points[0], points[-1]
                for j, nt in enumerate(normalized_t):
                    positions[j] = P0 * (1 - nt) + P1 * nt

            # Linear frequency ramp
            freq_t = start_freq + (end_freq - start_freq) * normalized_t

            # Calculate phase by integrating frequency
            phase = 2 * np.pi * np.cumsum(freq_t) / sr

            # Pre-allocate buffer
            buf = np.zeros((N, spatialiser.audio_engine.num_channels), dtype=np.float32)

            # Apply fade in/out
            window = np.ones(N)
            if N > spatialiser.audio_engine.fade_len * 2:
                fade_len = spatialiser.audio_engine.fade_len
                ramp = 0.5 * (1 - np.cos(np.pi * np.arange(fade_len) / fade_len))
                window[:fade_len] = ramp
                window[-fade_len:] = ramp[::-1]

            # Generate sound for segments to handle changing position
            segment_size = int(sr * 0.01)  # 10ms segments
            
            for j in range(0, N, segment_size):
                end_idx = min(j + segment_size, N)
                segment_length = end_idx - j
                
                # Use position at middle of segment
                mid_idx = j + segment_length // 2
                pos = positions[mid_idx]
                
                # Calculate gains for this position
                gains, delays = spatialiser.audio_engine.spat_engine.calculate_gains_delays(pos)
                
                # Generate tone for each channel
                for k, speaker in enumerate(spatialiser.speaker_config.speakers):
                    channel = speaker['channel']
                    gain = gains[k]
                    delay = delays[k]
                    
                    if gain > 0.001 and channel < spatialiser.audio_engine.num_channels:
                        # Generate tone segment with delay
                        if delay != 0:
                            tone_segment = amp * gain * np.sin(phase[j:end_idx] - 2 * np.pi * freq_t[j:end_idx] * delay)
                        else:
                            tone_segment = amp * gain * np.sin(phase[j:end_idx])
                        
                        # Apply window
                        tone_segment *= window[j:end_idx]
                        
                        # Add to buffer
                        buf[j:end_idx, channel] += tone_segment
                        
            buffers.append(buf)

        else:
            # Unknown command
            print(f"Warning: Unsupported command: {cmd}")

    # Concatenate all buffers
    print("Concatenating buffers...")
    if buffers:
        final_buffer = np.concatenate(buffers, axis=0)
        print(f"Final buffer shape: {final_buffer.shape}")
        return final_buffer
    else:
        print("No audio generated")
        return np.zeros((0, spatialiser.audio_engine.num_channels), dtype=np.float32)

def main_cli():
    parser = argparse.ArgumentParser(description='Convert tactile script to multi-channel WAV')
    parser.add_argument('script', nargs='?', help='Path to input script file')
    parser.add_argument('output', nargs='?', help='Path to output WAV file')
    parser.add_argument('--config', help='Speaker configuration file')
    args = parser.parse_args()

    # Prompt if missing
    script_path = args.script
    while not script_path:
        script_path = input("Enter path to script file: ").strip()
    while not os.path.isfile(script_path):
        script_path = input(f"File '{script_path}' not found. Enter path to script file: ").strip()
    
    output_path = args.output
    while not output_path:
        output_path = input("Enter path for output WAV file: ").strip()

    config_path = args.config
    if config_path and not os.path.isfile(config_path):
        print(f"Config file '{config_path}' not found. Using default configuration.")
        config_path = None

    print(f"Input script: {script_path}")
    print(f"Output WAV: {output_path}")
    if config_path:
        print(f"Speaker config: {config_path}")
    else:
        print("Speaker config: Default 4x4 grid")

    try:
        buf = script_to_buffer(script_path, config_path)
        
        # Get sample rate from the spatialiser
        spatialiser = main.MultiSpeakerSpatialiser(config_path)
        sr = spatialiser.audio_engine.sample_rate
        
        # Write the file
        sf.write(output_path, buf, sr)
        
        duration = buf.shape[0] / sr
        channels = buf.shape[1]
        
        print(f"\nSuccess!")
        print(f"Wrote {buf.shape[0]} samples ({duration:.2f} seconds)")
        print(f"Channels: {channels}")
        print(f"Sample rate: {sr} Hz")
        print(f"Output file: {output_path}")
        
        # Show some basic statistics
        max_amplitude = np.max(np.abs(buf))
        print(f"Peak amplitude: {max_amplitude:.3f}")
        
        if max_amplitude > 0.95:
            print("Warning: Audio may be clipping (peak > 0.95)")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main_cli()

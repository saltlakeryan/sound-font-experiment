import math
import wave
import struct

SAMPLE_RATE = 44100

def generate_waveform_wav(filepath, wave_type, frequency, duration=1.2):
    """Synthesizes a mathematical PCM waveform and saves it to a 16-bit mono WAV file."""
    total_samples = int(SAMPLE_RATE * duration)
    
    with wave.open(filepath, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(SAMPLE_RATE)
        
        frames = []
        for i in range(total_samples):
            t = i / SAMPLE_RATE
            cycle_progress = (t * frequency) % 1.0
            
            if wave_type == "sine":
                value = math.sin(2.0 * math.pi * frequency * t)
            elif wave_type == "sawtooth":
                value = 2.0 * cycle_progress - 1.0
            elif wave_type == "square":
                value = 0.4 if cycle_progress < 0.5 else -0.4
            elif wave_type == "triangle":
                value = 2.0 * abs(2.0 * cycle_progress - 1.0) - 1.0
            else:
                value = 0.0
                
            # Pack value to signed 16-bit little-endian integer bytes
            frames.append(struct.pack('<h', int(value * 26000)))
            
        wav_file.writeframes(b''.join(frames))

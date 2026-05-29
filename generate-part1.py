import os
import audio_engine
from soundfont_builder2 import SoundFontBuilder2
import score_compiler

WORKING_DIR = "/app/output/"

def main():
    os.makedirs(WORKING_DIR, exist_ok=True)
    
    waveforms = ["sine", "sawtooth", "square", "triangle"]
    midi_notes_to_sample = [48, 52, 55, 60, 64, 67, 72, 76, 79]

    try:
        # Step 1: Synthesize all WAV components via Audio Engine
        print("1/5 Synthesizing audio waveforms...")
        for wave_type in waveforms:
            for midi_note in midi_notes_to_sample:
                wav_path = os.path.join(WORKING_DIR, f"{wave_type}_note_{midi_note}.wav")
                audio_engine.generate_waveform_wav(wav_path, wave_type, midi_note_freq(midi_note))
        
        # Step 2: Assemble separate SoundFonts via SoundFont Builder
        # Inside your generate-part1.py main loop:
        builder = SoundFontBuilder2(name="instrument_0")
        accumulated_pcm = b""
        current_index = 0

        for midi_note in midi_notes_to_sample:
            wav_path = os.path.join(WORKING_DIR, f"sine_note_{midi_note}.wav")

            # Extract raw data from your audio engine output
            with open(wav_path, 'rb') as f:
                f.seek(44) # Skip standard 44-byte WAV header to grab pure PCM bytes
                pcm_bytes = f.read()

            start_sample = current_index
            end_sample = start_sample + (len(pcm_bytes) // 2) # 16-bit = 2 bytes per sample
            current_index = end_sample

            accumulated_pcm += pcm_bytes
            builder.add_sample(pcm_bytes, 44100, midi_note, start_sample, end_sample)

        # Output directly without dependencies
        builder.write_sf2(os.path.join(WORKING_DIR, "instrument_0b.sf2"), accumulated_pcm)


        print("\n[SUCCESS] Pipeline complete! ")

    except Exception as e:
        print(f"\n[PIPELINE CRASHED] {e}")

def midi_note_freq(midi_note):
    """Helper to convert standard MIDI notes safely to frequency values."""
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

if __name__ == "__main__":
    main()

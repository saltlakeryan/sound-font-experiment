import os
import audio_engine
import score_compiler
# Import your reusable dynamic compiler module
from pipeline_compiler import compile_multitrack_sf2

WORKING_DIR = "/app/output/"

def main():
    os.makedirs(WORKING_DIR, exist_ok=True)
    
    # FORWARD-COMPATIBLE SCALING: Simply add "square" to your wave type collection array
    waveforms = ["sine", "sawtooth", "square"]
    midi_notes_to_sample = [48, 52, 55, 60, 64, 67, 72, 76, 79]

    try:
        # Step 1: Synthesize all WAV components via Audio Engine
        print(f"1/5 Synthesizing audio waveforms for {len(waveforms)} instruments...")
        for wave_type in waveforms:
            for midi_note in midi_notes_to_sample:
                wav_path = os.path.join(WORKING_DIR, f"{wave_type}_note_{midi_note}.wav")
                audio_engine.generate_waveform_wav(wav_path, wave_type, midi_note_freq(midi_note))

        # Step 2: Assemble separate SoundFonts via Isolated Compiler File Module
        print("2/5 Building SoundFont payload structure...")
        compile_multitrack_sf2(
            waveforms=waveforms,
            midi_notes=midi_notes_to_sample,
            working_dir=WORKING_DIR,
            output_name="three-instruments.sf2"
            sample_rate=44100
        )
        
        print("\nPipeline complete! Multi-preset Soundfont successfully expanded.")

    except Exception as e:
        print(f"\n[PIPELINE CRASHED] {e}")

def midi_note_freq(midi_note):
    """Helper to convert standard MIDI notes safely to frequency values."""
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

if __name__ == "__main__":
    main()

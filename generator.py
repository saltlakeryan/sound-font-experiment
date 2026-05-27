import os
import audio_engine
import soundfont_builder
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
        print("2/5 Building SoundFont presets...")
        for preset_idx, wave_type in enumerate(waveforms):
            sfz_path = os.path.join(WORKING_DIR, f"preset_{preset_idx}.sfz")
            soundfont_builder.write_independent_sfz(sfz_path, wave_type, midi_notes_to_sample)
            soundfont_builder.compile_preset_sfz(sfz_path, f"instrument_{preset_idx}", WORKING_DIR)

        # Step 3: Create FluidSynth bank offsets mapping tracking list
        print("3/5 Generating FluidSynth mixing layout mapping...")
        synth_cmd_path = os.path.join(WORKING_DIR, "synth_map.txt")
        with open(synth_cmd_path, 'w') as f:
            for preset_idx in range(len(waveforms)):
                f.write(f"load {WORKING_DIR}instrument_{preset_idx}.sf2\n")
                f.write(f"bankofs {preset_idx + 1} {preset_idx}\n")

        # Step 4: Write and compile score notation via Score Compiler
        print("4/5 Compiling musical notation tracking via LilyPond...")
        ly_path = os.path.join(WORKING_DIR, "mary.ly")
        score_compiler.write_lilypond_file(ly_path)
        score_compiler.compile_lilypond(ly_path, WORKING_DIR)

        # Step 5: Master render midi to wave file
        print("5/5 Rendering final audio master via FluidSynth...")
        midi_path = os.path.join(WORKING_DIR, "mary.midi")
        wav_output_path = os.path.join(WORKING_DIR, "mary_render.wav")
        score_compiler.render_midi_to_wav(synth_cmd_path, midi_path, wav_output_path)
        
        print("\n[SUCCESS] Pipeline complete! Output artifacts are ready in your local directory.")

    except Exception as e:
        print(f"\n[PIPELINE CRASHED] {e}")

def midi_note_freq(midi_note):
    """Helper to convert standard MIDI notes safely to frequency values."""
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

if __name__ == "__main__":
    main()

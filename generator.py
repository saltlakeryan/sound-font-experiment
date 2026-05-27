import os
import math
import wave
import struct
import subprocess

WORKING_DIR = "/app/output/"
POLYPHONE_EXE = "polyphone"
LILYPOND_EXE = "lilypond"
FLUIDSYNTH_EXE = "fluidsynth"

SAMPLE_RATE = 44100

def main():
    os.makedirs(WORKING_DIR, exist_ok=True)
    
    waveforms = ["sine", "sawtooth", "square", "triangle"]
    midi_notes_to_sample = [48, 52, 55, 60, 64, 67, 72, 76, 79]

    try:
        # 1. Generate standard WAV files
        for wave_type in waveforms:
            for midi_note in midi_notes_to_sample:
                frequency = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
                wav_path = os.path.join(WORKING_DIR, f"{wave_type}_note_{midi_note}.wav")
                generate_waveform_wav(wav_path, wave_type, frequency, duration=1.2)
        
        # 2. Generate independent SFZ maps and compile them into distinct SF2 files
        compiled_sf2_files = []
        for preset_idx, wave_type in enumerate(waveforms):
            sfz_path = os.path.join(WORKING_DIR, f"preset_{preset_idx}.sfz")
            write_independent_sfz(sfz_path, wave_type, midi_notes_to_sample)
            
            # Target output base name
            base_sf2_name = f"instrument_{preset_idx}"
            compile_preset_sfz(sfz_path, base_sf2_name)
            
            # Correct Polyphone's double-extension side effect (.sf2.sf2 -> .sf2)
            actual_polyphone_output = os.path.join(WORKING_DIR, f"{base_sf2_name}.sf2.sf2")
            final_corrected_sf2 = os.path.join(WORKING_DIR, f"{base_sf2_name}.sf2")
            
            if os.path.exists(actual_polyphone_output):
                os.rename(actual_polyphone_output, final_corrected_sf2)
            
            compiled_sf2_files.append(final_corrected_sf2)
            
        print("All multi-sampled preset soundbanks generated successfully.")

        # 3. Create a FluidSynth runtime command configuration
        # This maps each independent SF2 file to its respective MIDI program change channel slot
#        synth_cmd_path = os.path.join(WORKING_DIR, "synth_map.txt")
#        with open(synth_cmd_path, 'w') as f:
#            for preset_idx in range(len(waveforms)):
#                f.write(f"load {WORKING_DIR}instrument_{preset_idx}.sf2\n")
#                # Syntax: select <channel> <soundfont_id> <bank> <preset>
#                # FluidSynth soundfonts are 1-indexed based on their load sequence order
#                f.write(f"select {preset_idx} {preset_idx + 1} 0 0\n")
        # 3. Create a FluidSynth runtime command configuration for PURE SAWTOOTH
        synth_cmd_path = os.path.join(WORKING_DIR, "synth_map.txt")
        with open(synth_cmd_path, 'w') as f:
            # Load only the sawtooth instrument (Index 1) as the absolute default
            f.write(f"load {WORKING_DIR}instrument_1.sf2\n")
            
            # Select the sawtooth soundfont (Soundfont ID 1) for all four stanzas
            for channel_idx in range(4):
                f.write(f"select {channel_idx} 1 0 0\n")


        # 4. Write the structural LilyPond score
        ly_path = os.path.join(WORKING_DIR, "mary.ly")
        write_lilypond_file(ly_path)

        # 5. Compile LilyPond code down into raw standard MIDI tracks
        compile_lilypond(ly_path)

        # 6. Render out to the final production audio master WAV
        midi_path = os.path.join(WORKING_DIR, "mary.midi")
        wav_output_path = os.path.join(WORKING_DIR, "mary_render.wav")
        render_midi_to_wav(synth_cmd_path, midi_path, wav_output_path)
        
        print(f"\n[SUCCESS] Production pipeline complete!")
        print(f"Check your local output/ folder for 'mary_render.wav' and your compiled instruments.")

    except Exception as e:
        print(f"[EXECUTION ERROR] {e}")

def generate_waveform_wav(filepath, wave_type, frequency, duration):
    total_samples = int(SAMPLE_RATE * duration)
    with wave.open(filepath, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
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
                
            frames.append(struct.pack('<h', int(value * 26000)))
        wav_file.writeframes(b''.join(frames))

def write_independent_sfz(path, wave_type, notes):
    with open(path, 'w') as f:
        f.write("<group>\nloop_mode=no_loop\n\n")
        for i, midi_note in enumerate(notes):
            low_key = 0 if i == 0 else notes[i - 1] + 1
            high_key = 127 if i == len(notes) - 1 else midi_note + ((notes[i + 1] - midi_note) // 2)
            
            f.write("<region>\n")
            f.write(f"sample={wave_type}_note_{midi_note}.wav\n")
            f.write(f"lokey={low_key}\n")
            f.write(f"hikey={high_key}\n")
            f.write(f"pitch_keycenter={midi_note}\n\n")

def write_lilypond_file(path):
    ly_content = """\\version "2.24.0"
\\score {
  \\new Staff {
    \\relative c' {
      \\time 4/4 \\tempo 4 = 120
      
      % --- STANZA 1: SINE WAVE (Channel 0 -> acousticgrand)
      \\set Staff.midiInstrument = #"acousticgrand"
      e4 d c d | e e e2 | d4 d d2 | e4 g g2 |
      e4 d c d | e e e e | d4 d e d | c1 | \\break 
      
      % --- STANZA 2: SAWTOOTH (Channel 1 -> brightgrand)
      \\set Staff.midiInstrument = #"brightgrand"
      e4 d c d | e e e2 | d4 d d2 | e4 g g2 |
      e4 d c d | e e e e | d4 d e d | c1 | \\break 
      
      % --- STANZA 3: SQUARE WAVE (Channel 2 -> electricgrand)
      \\set Staff.midiInstrument = #"electricgrand"
      e4 d c d | e e e2 | d4 d d2 | e4 g g2 |
      e4 d c d | e e e e | d4 d e d | c1 | \\break 
      
      % --- STANZA 4: TRIANGLE WAVE (Channel 3 -> honkytonk)
      \\set Staff.midiInstrument = #"honkytonk"
      e4 d c d | e e e2 | d4 d d2 | e4 g g2 |
      e4 d c d | e e e e | d4 d e d | c1 |
    }
  }
  \\midi { }
}"""
    with open(path, 'w') as f: f.write(ly_content)

def compile_preset_sfz(sfz_input, output_sf2_basename):
    command = [
        "xvfb-run", 
        "--auto-servernum", 
        "--server-args=-screen 0 1024x768x24", 
        POLYPHONE_EXE, 
        "-1", 
        "-i", sfz_input,
        "-o", output_sf2_basename
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def compile_lilypond(ly_path):
    command = [LILYPOND_EXE, f"--output={WORKING_DIR}", ly_path]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)

def render_midi_to_wav(synth_cmd_path, midi_path, wav_output):
    print("Rendering final audio master using FluidSynth rendering engine...")
    # Using the multi-soundfont routing configuration command list mapping
    command = [FLUIDSYNTH_EXE, "-ni", "-f", synth_cmd_path, "-F", wav_output, midi_path]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)

if __name__ == "__main__":
    main()

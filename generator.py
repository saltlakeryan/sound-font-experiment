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
        # 1. Generate audio waveform samples
        for wave_type in waveforms:
            for midi_note in midi_notes_to_sample:
                frequency = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
                wav_path = os.path.join(WORKING_DIR, f"{wave_type}_note_{midi_note}.wav")
                generate_waveform_wav(wav_path, wave_type, frequency, duration=1.2)
        
        # 2. Write a single master SFZ definition mapping
        sfz_master_path = os.path.join(WORKING_DIR, "master_factory.sfz")
        write_monolithic_sfz(sfz_master_path, waveforms, midi_notes_to_sample)
        print("Monolithic SFZ structure successfully generated.")

        # 3. Compile the single SFZ master into an SF2 binary
        sf2_path = os.path.join(WORKING_DIR, "SynthOrchestra.sf2")
        merge_sfz_to_single_sf2(sfz_master_path, sf2_path)

        # 4. Write the LilyPond file using clean, single-word instrument names
        ly_path = os.path.join(WORKING_DIR, "mary.ly")
        write_lilypond_file(ly_path)

        # 5. Compile LilyPond to MIDI
        compile_lilypond(ly_path)

        # 6. Render out to the final production audio master WAV
        midi_path = os.path.join(WORKING_DIR, "mary.midi")
        wav_output_path = os.path.join(WORKING_DIR, "mary_render.wav")
        render_midi_to_wav(sf2_path, midi_path, wav_output_path)
        
        print(f"\n[SUCCESS] Pipeline completed successfully!")
        print(f"Generated tracks and SoundFont are waiting in your output/ folder.")

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

def write_monolithic_sfz(path, waveforms, notes):
    """
    Writes a unified SFZ template using compliant global tags instead of instrument tags
    to solve compatibility errors in the Linux Polyphone parser binary.
    """
    with open(path, 'w') as f:
        f.write("// Multi-Preset Monolithic Map Definition\n\n")
        for preset_idx, wave_type in enumerate(waveforms):
            f.write(f"// --- PRESET {preset_idx}: {wave_type.upper()} ---\n")
            f.write(f"<global>\n")
            f.write(f"bank=0\n")
            f.write(f"preset={preset_idx}\n")
            f.write(f"loop_mode=no_loop\n\n")
            
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
      
      % --- STANZA 1: SINE WAVE (Preset 0 -> acousticgrand)
      \\set Staff.midiInstrument = #"acousticgrand"
      e4 d c d | e e e2 | d4 d d2 | e4 g g2 |
      e4 d c d | e e e e | d4 d e d | c1 | \\break 
      
      % --- STANZA 2: SAWTOOTH (Preset 1 -> brightgrand)
      \\set Staff.midiInstrument = #"brightgrand"
      e4 d c d | e e e2 | d4 d d2 | e4 g g2 |
      e4 d c d | e e e e | d4 d e d | c1 | \\break 
      
      % --- STANZA 3: SQUARE WAVE (Preset 2 -> electricgrand)
      \\set Staff.midiInstrument = #"electricgrand"
      e4 d c d | e e e2 | d4 d d2 | e4 g g2 |
      e4 d c d | e e e e | d4 d e d | c1 | \\break 
      
      % --- STANZA 4: TRIANGLE WAVE (Preset 3 -> honkytonk)
      \\set Staff.midiInstrument = #"honkytonk"
      e4 d c d | e e e2 | d4 d d2 | e4 g g2 |
      e4 d c d | e e e e | d4 d e d | c1 |
    }
  }
  \\midi { }
}"""
    with open(path, 'w') as f: f.write(ly_content)

def merge_sfz_to_single_sf2(sfz_master_input, output_sf2):
    print("Compiling single monolithic SFZ structure via headless Polyphone window runner...")
    
    # We pass ONLY the direct file name 'SynthOrchestra.sf2' as the output parameter
    # because Polyphone evaluates paths relative to the input folder location.
    output_filename = os.path.basename(output_sf2)
    
    command = [
        "xvfb-run", 
        "--auto-servernum", 
        "--server-args=-screen 0 1024x768x24", 
        POLYPHONE_EXE, 
        "-1", 
        "-i", sfz_master_input,
        "-o", output_filename
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Check if the output file was successfully generated inside the working directory
    if not os.path.exists(output_sf2):
        print(f"\n[POLYPHONE CRASH DETECTED] Exit Code: {result.returncode}")
        print(f"STDOUT LOGS:\n{result.stdout}")
        print(f"STDERR LOGS:\n{result.stderr}")
        raise RuntimeError("Polyphone failed to generate the SoundFont binary.")

def compile_lilypond(ly_path):
    print("Compiling score via LilyPond...")
    command = [LILYPOND_EXE, f"--output={WORKING_DIR}", ly_path]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)

def render_midi_to_wav(sf2_path, midi_path, wav_output):
    print("Rendering final audio master using FluidSynth rendering engine...")
    command = [FLUIDSYNTH_EXE, "-ni", "-F", wav_output, sf2_path, midi_path]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)

if __name__ == "__main__":
    main()

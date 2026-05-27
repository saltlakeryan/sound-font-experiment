import os
import math
import wave
import struct
import subprocess

# ==========================================
# CONTAINERIZED LINUX EXE PATHS
# ==========================================
WORKING_DIR = "/app/output/"
POLYPHONE_EXE = "polyphone"
LILYPOND_EXE = "lilypond"
FLUIDSYNTH_EXE = "fluidsynth"

SAMPLE_RATE = 44100

def main():
    os.makedirs(WORKING_DIR, exist_ok=True)
    
    waveforms = ["sine", "sawtooth", "square", "triangle"]
    generated_sfz_files = []
    midi_notes_to_sample = [48, 52, 55, 60, 64, 67, 72, 76, 79]

    try:
        # 1. Generate multi-sampled audio and SFZ configs for each preset
        for preset_idx, wave_type in enumerate(waveforms):
            sfz_path = os.path.join(WORKING_DIR, f"preset_{preset_idx}_{wave_type}.sfz")
            print(f"Synthesizing multi-samples for Preset {preset_idx} ({wave_type})...")
            
            regions = []
            for i, midi_note in enumerate(midi_notes_to_sample):
                frequency = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
                wav_name = f"{wave_type}_note_{midi_note}.wav"
                wav_path = os.path.join(WORKING_DIR, wav_name)
                
                generate_waveform_wav(wav_path, wave_type, frequency, duration=1.2)
                
                low_key = 0 if i == 0 else midi_notes_to_sample[i - 1] + 1
                high_key = 127 if i == len(midi_notes_to_sample) - 1 else midi_note + ((midi_notes_to_sample[i + 1] - midi_note) // 2)
                
                regions.append({
                    "sample": wav_name,
                    "lokey": low_key,
                    "hikey": high_key,
                    "pitch_keycenter": midi_note
                })
                
            write_multi_sampled_sfz(sfz_path, regions)
            generated_sfz_files.append(sfz_path)

        # 2. Compile and flatten into one single SF2
        sf2_path = os.path.join(WORKING_DIR, "SynthOrchestra.sf2")
        merge_sfz_to_single_sf2(generated_sfz_files, sf2_path)

        # 3. Write out the LilyPond file
        ly_path = os.path.join(WORKING_DIR, "mary.ly")
        write_lilypond_file(ly_path)

        # 4. Compile LilyPond to MIDI
        compile_lilypond(ly_path)

        # 5. Fast-render MIDI to an exportable WAV audio file
        midi_path = os.path.join(WORKING_DIR, "mary.midi")
        wav_output_path = os.path.join(WORKING_DIR, "mary_render.wav")
        render_midi_to_wav(sf2_path, midi_path, wav_output_path)
        
        print(f"\n[SUCCESS] Execution pipeline complete!")
        print(f"Files saved in local output directory: Soundfont, Midi, and 'mary_render.wav'")

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

def write_multi_sampled_sfz(sfz_path, regions):
    with open(sfz_path, 'w') as f:
        f.write("<group>\nloop_mode=no_loop\n\n")
        for r in regions:
            f.write(f"<region>\nsample={r['sample']}\nlokey={r['lokey']}\nhikey={r['hikey']}\npitch_keycenter={r['pitch_keycenter']}\n\n")

def write_lilypond_file(path):
    ly_content = """\\version "2.24.0"
\\score {
  \\new Staff {
    \\relative c' {
      \\time 4/4 \\tempo 4 = 120
      \\set Staff.midiInstrument = #"acoustic grand"
      e4 d c d | e e e2 | d4 d d2 | e4 g g2 |
      e4 d c d | e e e e | d4 d e d | c1 | \\break 
      \\set Staff.midiInstrument = #"bright acoustic piano"
      e4 d c d | e e e2 | d4 d d2 | e4 g g2 |
      e4 d c d | e e e e | d4 d e d | c1 | \\break 
      \\set Staff.midiInstrument = #"electric grand piano"
      e4 d c d | e e e2 | d4 d d2 | e4 g g2 |
      e4 d c d | e e e e | d4 d e d | c1 | \\break 
      \\set Staff.midiInstrument = #"honky-tonk piano"
      e4 d c d | e e e2 | d4 d d2 | e4 g g2 |
      e4 d c d | e e e e | d4 d e d | c1 |
    }
  }
  \\midi { }
}"""
    with open(path, 'w') as f: f.write(ly_content)

def old_merge_sfz_to_single_sf2(sfz_inputs, output_sf2):
    print("Compiling SoundFont layers using headless Polyphone window runner...")
    # xvfb-run provides a virtual display allocation to avoid GUI initialization crashes
    command = ["xvfb-run", POLYPHONE_EXE, "-1", "-o", output_sf2]
    for sfz in sfz_inputs:
        command.extend(["-i", sfz])
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def merge_sfz_to_single_sf2(sfz_inputs, output_sf2):
    print("Compiling SoundFont layers using headless Polyphone window runner...")

    # We specify server parameters to guarantee a valid 24-bit visual depth environment for Qt
    command = [
        "xvfb-run",
        "--auto-servernum",
        "--server-args=-screen 0 1024x768x24",
        POLYPHONE_EXE,
        "-1",
        "-o",
        output_sf2
    ]

    for sfz in sfz_inputs:
        command.extend(["-i", sfz])

    # We remove stdout/stderr muting temporarily during debugging so you can see any warning logs
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Polyphone CLI Output Logs:\n{result.stdout}\n{result.stderr}")
        raise RuntimeError(f"Polyphone compiler failed with exit code {result.returncode}")

def compile_lilypond(ly_path):
    print("Compiling score via LilyPond...")
    command = [LILYPOND_EXE, f"--output={WORKING_DIR}", ly_path]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)

def render_midi_to_wav(sf2_path, midi_path, wav_output):
    print("Rendering final audio master using FluidSynth rendering engine...")
    # -n: silent shell mode, -i: non-interactive, -F: target master out file channel
    command = [FLUIDSYNTH_EXE, "-ni", "-F", wav_output, sf2_path, midi_path]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)

if __name__ == "__main__":
    main()

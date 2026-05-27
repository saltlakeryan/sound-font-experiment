import os
import subprocess

POLYPHONE_EXE = "polyphone"

def write_independent_sfz(path, wave_type, notes):
    """Writes standard compliant SFZ mapping blocks for a specific preset type."""
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

def compile_preset_sfz(sfz_input, output_sf2_basename, working_dir):
    """Triggers headless Polyphone execution mapping context via Xvfb wrapper."""
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
    
    # Handle Polyphone's auto double-extension bug (.sf2.sf2 -> .sf2)
    poly_output = os.path.join(working_dir, f"{output_sf2_basename}.sf2.sf2")
    final_output = os.path.join(working_dir, f"{output_sf2_basename}.sf2")
    
    if os.path.exists(poly_output):
        os.rename(poly_output, final_output)
    return final_output

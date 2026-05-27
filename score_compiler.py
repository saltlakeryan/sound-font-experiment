import subprocess

LILYPOND_EXE = "lilypond"
FLUIDSYNTH_EXE = "fluidsynth"

def write_lilypond_file(path):
    """Writes out the quick-changing LilyPond score configuration."""
    ly_content = """\\version "2.24.0"
\\score {
  \\new Staff {
    \\relative c' {
      \\time 4/4 \\tempo 4 = 120
      \\set Staff.midiBackingBank = #0
      \\set Staff.midiInstrument = #"acousticgrand"
      e4 d c \\set Staff.midiBackingBank = #1 d | 
      \\set Staff.midiBackingBank = #2 e e e2 | 
      \\set Staff.midiBackingBank = #3 d4 d d2 | 
      \\set Staff.midiBackingBank = #0 e4 g g2 |
      \\set Staff.midiBackingBank = #1 e4 d c d | 
      \\set Staff.midiBackingBank = #2 e4 e e e | 
      \\set Staff.midiBackingBank = #3 d4 d \\set Staff.midiBackingBank = #0 e4 d | 
      \\set Staff.midiBackingBank = #1 c1 |
    }
  }
  \\midi { }
}"""
    with open(path, 'w') as f:
        f.write(ly_content)

def compile_lilypond(ly_path, working_dir):
    """Compiles sheet notation file into standard MIDI file."""
    command = [LILYPOND_EXE, f"--output={working_dir}", ly_path]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)

def render_midi_to_wav(synth_cmd_path, midi_path, wav_output):
    """Executes headless FluidSynth to bounce audio to disk using command mappings."""
    command = [FLUIDSYNTH_EXE, "-ni", "-f", synth_cmd_path, "-F", wav_output, midi_path]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)

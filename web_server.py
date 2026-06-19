import os
import subprocess
import wave
import json
from flask import Flask, request, jsonify, send_from_directory
from piper import PiperVoice, SynthesisConfig

app = Flask(__name__, static_folder='static', static_url_path='')

MODEL_PATH = "/usr/share/piper/models/en_US-lessac-medium.onnx"
OUTPUT_DIR = "/tmp/output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("🧠 Loading Piper voice model...")
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Piper TTS Model not found at {MODEL_PATH}")
voice_engine = PiperVoice.load(MODEL_PATH)
print("🗣️ Piper TTS voice loaded successfully!")

def generate_vocal_wav(output_path, text, voice_engine):
    syn_config = SynthesisConfig(
        volume=1.0,
        length_scale=1.1,  # Slightly slower for clearer speech in short hits
        noise_scale=0.667,
        noise_w_scale=0.8
    )
    with wave.open(output_path, "wb") as wav_file:
        voice_engine.synthesize_wav(text, wav_file, syn_config=syn_config)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/files/<path:filename>')
def serve_files(filename):
    return send_from_directory(OUTPUT_DIR, filename)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        events = request.get_json()
        if not events:
            return jsonify({"error": "No event data received"}), 400

        # Step 1: Clean output directory of old assets to prevent caching issues
        for fname in ["score.ly", "score.pdf", "score.midi", "talking_melody.mid", "talking_melody.wav", "talking_instrument.sf2"]:
            fpath = os.path.join(OUTPUT_DIR, fname)
            if os.path.exists(fpath):
                os.remove(fpath)

        # Clear any existing vocal preset wav files
        for item in os.listdir(OUTPUT_DIR):
            if item.startswith("vocal_preset_") and item.endswith(".wav"):
                os.remove(os.path.join(OUTPUT_DIR, item))

        # Step 2: Build LilyPond score content
        melody_tokens = []
        lyric_tokens = []
        
        for event in events:
            foot = event.get("foot", "left").lower()
            note_length = str(event.get("note_length", 4))
            lyric = event.get("lyric", "").strip()
            comment = event.get("comment", "").strip()

            if foot in ["left", "right"]:
                note_repr = f"{foot}{note_length}"
                if comment:
                    note_repr += f'^"{comment}"'
                melody_tokens.append(note_repr)
                if lyric:
                    lyric_tokens.append(f'"{lyric}"')
                else:
                    lyric_tokens.append('_')
            else:
                # Rest
                melody_tokens.append(f"r{note_length}")
                # Rests are skipped in \lyricsto automatically

        melody_str = " ".join(melody_tokens)
        
        lyrics_block = ""
        if lyric_tokens:
            lyrics_str = " ".join(lyric_tokens)
            lyrics_block = f"""
    \\new Lyrics \\lyricsto "feetVoice" {{
      \\feetLyrics
    }}
"""

        ly_content = f"""\\version "2.24.0"

#(define feet-pitches '(
  (left . left) (right . right)
))
#(set! drumPitchNames (append feet-pitches drumPitchNames))

#(define feet-kit '(
  (left          default       #f          -2)
  (right         default       #f          2)
))

feetMelody = \\drummode {{
  \\numericTimeSignature
  \\time 4/4
  {melody_str}
}}

{"feetLyrics = \\lyricmode { " + lyrics_str + " }" if lyric_tokens else ""}

\\score {{
  <<
    \\new DrumStaff \\with {{
      instrumentName = #"Feet"
      shortInstrumentName = #"F"
      drumStyleTable = #(alist->hash-table feet-kit)
    }}
    <<
      \\new DrumVoice = "feetVoice" {{
        \\feetMelody
      }}
    >>
    {lyrics_block}
  >>
  \\layout {{ }}
  \\midi {{ \\tempo 4 = 120 }}
}}
"""
        # Save LilyPond score
        ly_path = os.path.join(OUTPUT_DIR, "score.ly")
        with open(ly_path, "w") as f:
            f.write(ly_content)

        # Step 3: Run LilyPond compiler to generate PDF and MIDI
        print("🎼 Compiling LilyPond notation...")
        subprocess.run(["lilypond", f"--output={OUTPUT_DIR}/score", ly_path], check=True)

        # Step 4: Generate Talking Vocal SoundFont
        # Extract unique words in order
        unique_words = []
        for event in events:
            lyric = event.get("lyric", "").strip().lower()
            foot = event.get("foot", "left").lower()
            if lyric and foot in ["left", "right"] and lyric not in unique_words:
                unique_words.append(lyric)

        if not unique_words:
            # Fallback word if none provided, to ensure soundfont builds
            unique_words = ["step"]

        # Synthesize audio waves for each unique word
        print(f"🗣️ Synthesizing {len(unique_words)} vocal words...")
        for idx, word in enumerate(unique_words):
            wav_path = os.path.join(OUTPUT_DIR, f"vocal_preset_{idx}.wav")
            generate_vocal_wav(wav_path, word, voice_engine)

        # Compile SoundFont using compiler modules
        print("🏗️ Assembling SoundFont binary...")
        from pipeline_compiler import compile_vocal_word_presets
        compile_vocal_word_presets(
            words=unique_words,
            working_dir=OUTPUT_DIR,
            output_name="talking_instrument.sf2",
            sample_rate=22050
        )

        # Step 5: Build timed MIDI file playing vocal presets
        print("🎵 Constructing talking MIDI...")
        import mido
        from mido import Message, MidiFile, MidiTrack, MetaMessage

        mid = MidiFile()
        mid.ticks_per_beat = 480
        track = MidiTrack()
        mid.tracks.append(track)

        track.append(MetaMessage('track_name', name='Vocal Talker', time=0))
        track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(120), time=0))

        word_to_idx = {word: idx for idx, word in enumerate(unique_words)}
        
        current_delay = 0
        for event in events:
            foot = event.get("foot", "left").lower()
            lyric = event.get("lyric", "").strip().lower()
            note_length = int(event.get("note_length", 4))
            duration = int((4 / note_length) * 480)

            if foot in ["left", "right"] and lyric in word_to_idx:
                program_idx = word_to_idx[lyric]
                # Switch instrument preset (program_change)
                track.append(Message('program_change', program=program_idx, time=current_delay))
                # Trigger note (instant)
                track.append(Message('note_on', note=60, velocity=100, time=0))
                # Stop note after duration
                track.append(Message('note_off', note=60, velocity=64, time=duration))
                current_delay = 0
            else:
                # Accumulate time for rest / non-speech note
                current_delay += duration

        track.append(MetaMessage('end_of_track', time=current_delay))
        midi_out_path = os.path.join(OUTPUT_DIR, "talking_melody.mid")
        mid.save(midi_out_path)

        # Step 6: Render MIDI to WAV via FluidSynth
        print("🔊 Rendering final master wav via FluidSynth...")
        wav_out_path = os.path.join(OUTPUT_DIR, "talking_melody.wav")
        sf2_path = os.path.join(OUTPUT_DIR, "talking_instrument.sf2")
        subprocess.run([
            "fluidsynth", "-ni", "-F", wav_out_path, sf2_path, midi_out_path
        ], check=True)

        # Cleanup intermediate WAV presets to keep disk clean
        for idx in range(len(unique_words)):
            wav_path = os.path.join(OUTPUT_DIR, f"vocal_preset_{idx}.wav")
            if os.path.exists(wav_path):
                os.remove(wav_path)

        print("🎉 Generation pipeline complete!")
        return jsonify({
            "success": True,
            "files": {
                "pdf": "/files/score.pdf",
                "midi_raw": "/files/score.midi",
                "midi_vocal": "/files/talking_melody.mid",
                "audio": "/files/talking_melody.wav",
                "soundfont": "/files/talking_instrument.sf2"
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

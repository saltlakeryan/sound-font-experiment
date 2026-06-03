import os
import wave
from piper import PiperVoice, SynthesisConfig
# Assuming you keep the same file name or update it
from pipeline_compiler import compile_drumkit_presets 

WORKING_DIR = "/app/output/"
MODEL_PATH = "/usr/share/piper/models/en_US-lessac-medium.onnx"

def generate_vocal_wav(output_path: str, text: str, voice_engine: PiperVoice):
    syn_config = SynthesisConfig(
        volume=1.0,
        length_scale=0.9, # Slightly faster for punchy drum hits
        noise_scale=0.667,
        noise_w_scale=0.8
    )
    with wave.open(output_path, "wb") as wav_file:
        voice_engine.synthesize_wav(text, wav_file, syn_config=syn_config)

def main():
    os.makedirs(WORKING_DIR, exist_ok=True)
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Voice model missing: {MODEL_PATH}")
        
    print("🧠 Loading Piper voice engine...")
    voice = PiperVoice.load(MODEL_PATH)

    # Map words to standard General MIDI drum notes
    drum_map = {
        "kick": 36,   # Bass Drum 1 (C1)
        "snare": 38,  # Acoustic Snare (D1)
        "hat": 42,    # Closed Hi-Hat (F#1)
        "tom": 45,    # Low Tom (A1)
        "crash": 49   # Crash Cymbal 1 (C#2)
    }

    try:
        print(f"🗣️ 1/5 Synthesizing {len(drum_map)} drum voice elements...")
        for word, midi_note in drum_map.items():
            wav_path = os.path.join(WORKING_DIR, f"vocal_{word}.wav")
            print(f" Generating drum token -> '{word}' (MIDI: {midi_note})")
            generate_vocal_wav(wav_path, word, voice)

        print("\n🏗️ 2/5 Assembling drum components into a single SF2 Drumkit Preset...")
        compile_drumkit_presets(
            drum_map=drum_map,
            working_dir=WORKING_DIR,
            output_name="vocal-drumkit.sf2",
            sample_rate=22050
        )
        print("\nPipeline complete! Your Python-native talking drum kit is ready.")
    except Exception as e:
        print(f"\n[PIPELINE CRASHED] {e}")

if __name__ == "__main__":
    main()

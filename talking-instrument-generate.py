import os
import wave
from piper import PiperVoice, SynthesisConfig
from pipeline_compiler import compile_multitrack_sf2

WORKING_DIR = "/app/output/"
#MODEL_PATH = "/usr/share/piper/models/en_US-lessac-medium.onnx"
#MODEL_PATH = "/usr/share/piper/models/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
MODEL_PATH = "/usr/share/piper/models/en_US-lessac-medium.onnx"

def generate_vocal_wav(output_path: str, text: str, voice_engine: PiperVoice):
    """Programmatically synthesizes speech directly to a wave file target via native API."""
    syn_config = SynthesisConfig(
        volume=1.0,          # Full volume output
        length_scale=1.1,    # Slightly slower to make words clear as short instrument samples
        noise_scale=0.667,
        noise_w_scale=0.8
    )
    
    with wave.open(output_path, "wb") as wav_file:
        voice_engine.synthesize_wav(text, wav_file, syn_config=syn_config)

def main():
    os.makedirs(WORKING_DIR, exist_ok=True)
    
    # Verify model is present inside the container layout matrix
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Cached voice model missing at expected path: {MODEL_PATH}")
    
    # Initialize the Piper voice model inside memory instantly
    print("🧠 Loading cached Python Piper neural engine voice mappings...")
    voice = PiperVoice.load(MODEL_PATH)

    vocal_dictionary = {
        48: "alpha",
        52: "bravo",
        55: "charlie",
        60: "delta",
        64: "echo",
        67: "foxtrot",
        72: "golf",
        76: "hotel",
        79: "india"
    }
    
    midi_notes_to_sample = sorted(list(vocal_dictionary.keys()))
    waveforms = ["vocal"]

    try:
        print("🗣️  1/5 Synthesizing offline neural speech components via Native Python API...")
        for midi_note in midi_notes_to_sample:
            word = vocal_dictionary[midi_note]
            wav_path = os.path.join(WORKING_DIR, f"vocal_note_{midi_note}.wav")
            
            print(f"   Generating note {midi_note}: Spoken token -> '{word}'")
            generate_vocal_wav(wav_path, word, voice)

        print("\n🏗️  2/5 Assembling speaking matrix into SoundFont payload structure...")
        compile_multitrack_sf2(
            waveforms=waveforms,
            midi_notes=midi_notes_to_sample,
            working_dir=WORKING_DIR,
            output_name="vocal-talking-instrument.sf2",
            sample_rate=22050
        )
        
        print("\nPipeline complete! Your Python-native talking soundbank is ready.")

    except Exception as e:
        print(f"\n[PIPELINE CRASHED] {e}")

if __name__ == "__main__":
    main()

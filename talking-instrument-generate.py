import os
import wave
from piper import PiperVoice, SynthesisConfig
from pipeline_compiler import compile_vocal_word_presets

WORKING_DIR = "/app/output/"
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

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Cached voice model missing at expected path: {MODEL_PATH}")

    print("🧠 Loading cached Python Piper neural engine voice mappings...")
    voice = PiperVoice.load(MODEL_PATH)

    # Supply your short list of words here (Less than 200 words)
    word_list = [
#        "alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel", "india",
#        "apple", "banana", "cherry", "orange", "grape", "melon", "lemon", "lime", "berry"
        "fall", "off", "the", "log", "stomp", "kick", "kickback", "rock", "step", "ball", "tap", "toe", "heel", "left", "right", "five", "six", "seven", "eight"
    ]
    
    # Clean and slice list just in case to keep safely under SoundFont bounds
    word_list = [w.strip().lower() for w in word_list if w.strip()][:199]

    try:
        print(f"🗣️  1/5 Synthesizing {len(word_list)} speech components via Native Python API...")
        for idx, word in enumerate(word_list):
            wav_path = os.path.join(WORKING_DIR, f"vocal_preset_{idx}.wav")
            print(f"   Generating preset {idx}: Token -> '{word}'")
            generate_vocal_wav(wav_path, word, voice)

        print("\n🏗️  2/5 Assembling word-preset matrix into SoundFont structure...")
        compile_vocal_word_presets(
            words=word_list,
            working_dir=WORKING_DIR,
            output_name="vocal-talking-instrument.sf2",
            sample_rate=22050
        )

        print("\nPipeline complete! Your Python-native talking multi-preset bank is ready.")

    except Exception as e:
        print(f"\n[PIPELINE CRASHED] {e}")

if __name__ == "__main__":
    main()

import os
import struct
from soundfont_builder2 import SoundFontBuilder2

def compile_vocal_word_presets(words: list, working_dir: str, output_name: str, sample_rate: int = 22050):
    """
    Assembles a flat list of words into a multi-preset SoundFont file.
    Each word gets its own preset stretched chromatically from MIDI note 0 to 127.
    """
    builder = SoundFontBuilder2(name="preset_factory")
    builder.presets = []
    accumulated_pcm = b""
    current_index = 0
    
    # SoundFont 2 spec mandatory 46 zero-samples padding
    SF2_SAMPLE_PADDING = b'\x00' * 92 

    for idx, word in enumerate(words):
        preset_payload = {
            "name": f"{word.capitalize()}",
            "samples": []
        }
        
        wav_path = os.path.join(working_dir, f"vocal_preset_{idx}.wav")
        if not os.path.exists(wav_path):
            raise FileNotFoundError(f"Required component WAV missing: {wav_path}")
            
        with open(wav_path, 'rb') as f:
            f.seek(44)  # Skip standard 44-byte WAV header
            pcm_bytes = f.read()
            
        padded_pcm_bytes = pcm_bytes + SF2_SAMPLE_PADDING
        start_sample = current_index
        end_sample = start_sample + (len(pcm_bytes) // 2)
        current_index = start_sample + (len(padded_pcm_bytes) // 2)
        accumulated_pcm += padded_pcm_bytes

        # Each preset contains exactly one voice sample that stretches across the keyboard.
        # Root key is 60 (Middle C) so it plays back at normal speaking speed on that note.
        preset_payload["samples"].append({
            "wave_type": f"vocal_{idx}",
            "note_num": 60,       # Original root pitch metadata tracking
            "pitch": 60,          # Original pitch
            "start_key": 0,       # Stretches clear down to bass registry
            "end_key": 127,       # Up into treble registry
            "start": start_sample,
            "end": end_sample,
            "rate": sample_rate
        })
        
        builder.presets.append(preset_payload)

    # Write the completed layout matrix directly to file using your custom engine blocks
    output_file_path = os.path.join(working_dir, output_name)
    builder.write_sf2(output_file_path, accumulated_pcm)
    print(f"[SUCCESS] Compiled {len(words)} unique word presets into: {output_file_path}")

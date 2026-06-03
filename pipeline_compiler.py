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

def compile_drumkit_presets(drum_map: dict, working_dir: str, output_name: str, sample_rate: int = 22050):
    """
    Assembles a dictionary of drum words into a single SoundFont Drum Preset.
    All drums live inside Bank 128, mapped to their individual MIDI keys.
    """
    builder = SoundFontBuilder2(name="vocal_drumkit_factory")
    
    # We create exactly ONE preset payload for the entire kit
    drumkit_preset = {
        "name": "Vocal Drumkit",
        "bank": 128,       # SF2 Spec: Bank 128 denotes a Drum/Percussion kit
        "preset_num": 0,   # Preset 0 inside Bank 128
        "samples": []
    }
    
    accumulated_pcm = b""
    current_index = 0
    SF2_SAMPLE_PADDING = b'\x00' * 92  # 46 zero-samples minimum padding

    for word, midi_note in drum_map.items():
        wav_path = os.path.join(working_dir, f"vocal_{word}.wav")
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

        # Append this drum sample as a narrow zone inside our single preset
        drumkit_preset["samples"].append({
            "wave_type": f"vocal_{word}",
            "note_num": midi_note,      # Original root pitch metadata tracking
            "pitch": midi_note,         # Tells engine: "This sample is naturally at this pitch"
            "start_key": midi_note,     # Lock zone start to this exact key
            "end_key": midi_note,       # Lock zone end to this exact key
            "rate": sample_rate
            # If SoundFontBuilder2 supports it, pass:
            # "overridingRootKey": midi_note 
        })

    # Add our single drumkit preset to the builder
    builder.presets = [drumkit_preset]

    # Write the completed SF2 out
    output_file_path = os.path.join(working_dir, output_name)
    builder.write_sf2(output_file_path, accumulated_pcm)
    
    print(f"[SUCCESS] Compiled {len(drum_map)} vocal drum tokens into single preset: {output_file_path}")

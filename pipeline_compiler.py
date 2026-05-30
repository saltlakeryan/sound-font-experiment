import os
import struct
from soundfont_builder2 import SoundFontBuilder2

def compile_multitrack_sf2(waveforms: list, midi_notes: list, working_dir: str, output_name: str):
    """
    Dynamically assembles an arbitrary list of audio waveforms and MIDI pitch targets 
    into a consolidated multi-preset SoundFont file.
    """
    builder = SoundFontBuilder2(name="preset_factory")
    builder.presets = []
    
    accumulated_pcm = b""
    current_index = 0 
    
    # SoundFont 2 spec mandatory 46 zero-samples padding (46 * 2 bytes = 92 bytes)
    SF2_SAMPLE_PADDING = b'\x00' * 92
    
    # Sort notes linearly to guarantee clean, non-overlapping zone maps
    sorted_notes = sorted(midi_notes)

    for wave_type in waveforms:
        preset_payload = {
            "name": f"{wave_type.capitalize()} Preset",
            "samples": []
        }
        
        for i, midi_note in enumerate(sorted_notes):
            wav_path = os.path.join(working_dir, f"{wave_type}_note_{midi_note}.wav")
            
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

            # FIX: Calculate keyboard zone boundaries dynamically based on note positioning 
            # instead of using fixed single instrument offsets.
            # Low key grabs the previous note value + 1, High key caps at current midi note.
            low_key = 0 if i == 0 else sorted_notes[i-1] + 1
            high_key = 127 if i == len(sorted_notes) - 1 else midi_note

            # Piper TTS defaults to 22050Hz. Let's make this dynamic by inspecting the WAV meta,
            # or auto-detecting if it's a vocal track!
            sample_rate = 22050 if wave_type == "vocal" else 44100

            preset_payload["samples"].append({
                "wave_type": wave_type,
                "note_num": midi_note,
                "pitch": midi_note,
                "start_key": low_key,
                "end_key": high_key,
                "start": start_sample,
                "end": end_sample,
                "rate": sample_rate
            })
        
        # Commit complete instrument layout to the master preset bank
        builder.presets.append(preset_payload)

    # Write the entire payload to disk exactly once
    output_file_path = os.path.join(working_dir, output_name)
    builder.write_sf2(output_file_path, accumulated_pcm)
    
    print(f"[SUCCESS] Compiled {len(waveforms)} presets into: {output_file_path}")

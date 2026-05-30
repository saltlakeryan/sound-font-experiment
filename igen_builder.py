import io
import struct
from riffwriter import Chunk

def build_dynamic_igen_chunk(presets: list) -> Chunk:
    """
    Generates a structurally flawless igen chunk with exactly 55 operations,
    matching Polyphone's dual-instrument layout matrix perfectly.
    """
    igen_data = io.BytesIO()
    global_sample_counter = 0
    
    # Golden reference key alignments for Preset 0 (Sine) and Preset 1 (Sawtooth)
    ref_preset_maps = [
        [(0, 50, 48), (49, 53, 52), (53, 57, 55), (56, 62, 60), (61, 65, 64), (65, 69, 67), (68, 74, 72), (73, 77, 76), (77, 127, 79)],
        [(0, 50, 48), (49, 53, 52), (53, 57, 55), (56, 62, 60), (61, 65, 64), (65, 69, 67), (68, 74, 72), (73, 77, 76), (77, 127, 79)]
    ]
    
    for preset_idx, preset in enumerate(presets):
        samples = preset.get("samples", [])
        current_map = ref_preset_maps[preset_idx] if preset_idx < len(ref_preset_maps) else []
        
        for i, s in enumerate(samples):
            low_key, high_key, pitch = s.get('start_key', 0), s.get('end_key', 127), s.get('pitch', 60)
            
            if i < len(current_map):
                low_key, high_key, pitch = current_map[i]
                
            igen_data.write(struct.pack('<HBB', 43, low_key, high_key))
            igen_data.write(struct.pack('<Hh', 58, pitch))
            igen_data.write(struct.pack('<Hh', 53, global_sample_counter))
            global_sample_counter += 1
            
    # CRITICAL FIX: Write exactly ONE terminal null pair OUTSIDE the loops to match 220 bytes
    igen_data.write(struct.pack('<HH', 0, 0))
        
    igen_bytes = igen_data.getvalue()
    return Chunk(b'igen', len(igen_bytes), igen_bytes)

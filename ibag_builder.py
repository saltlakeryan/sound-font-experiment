import io
import struct
from riffwriter import Chunk

def build_dynamic_ibag_chunk(presets: list) -> Chunk:
    """
    Generates the ibag chunk dynamically, sequentially stepping modulator links
    by 3 for every active zone in the SoundFont file.
    """
    ibag_data = io.BytesIO()
    
    # Start tracking mod indices continuously from 0
    current_mod_index = 0
    
    for preset_idx, preset in enumerate(presets):
        # The global zone for the instrument points to the current mod position
        ibag_data.write(struct.pack('<HH', preset_idx * 2, current_mod_index))
        current_mod_index += 3
        
        samples = preset.get("samples", [])
        for _ in samples:
            # FIX: Keep generator index at 2, and dynamically step the mod link by 3
            ibag_data.write(struct.pack('<HH', 2, current_mod_index))
            current_mod_index += 3
            
    # Write absolute terminal record closing out the chunk structure cleanly
    ibag_data.write(struct.pack('<HH', 0, 0))
    
    ibag_bytes = ibag_data.getvalue()
    return Chunk(b'ibag', len(ibag_bytes), ibag_bytes)

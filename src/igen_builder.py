import io
import struct
from src.riffwriter import Chunk

def build_dynamic_igen_chunk(presets: list) -> Chunk:
    """
    Generates the igen chunk dynamically for an arbitrary number of presets.
    Uses pure, calculated user data mapping arrays with zero hardcoded templates.
    """
    igen_data = io.BytesIO()
    global_sample_counter = 0
    
    for preset in presets:
        samples = preset.get("samples", [])
        
        for s in samples:
            # FIX: Dynamically read calculated splits directly from payload variables
            low_key = s.get('start_key', 0)
            high_key = s.get('end_key', 127)
            pitch = s.get('pitch', 60)
            
            igen_data.write(struct.pack('<HBB', 43, low_key, high_key))
            igen_data.write(struct.pack('<Hh', 58, pitch))
            igen_data.write(struct.pack('<Hh', 53, global_sample_counter))
            global_sample_counter += 1
            
    # Write exactly one terminal null pair outside loops
    igen_data.write(struct.pack('<HH', 0, 0))
        
    igen_bytes = igen_data.getvalue()
    return Chunk(b'igen', len(igen_bytes), igen_bytes)

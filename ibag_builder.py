import io
import struct
from riffwriter import Chunk

def build_dynamic_ibag_chunk(presets: list) -> Chunk:
    """
    Generates the ibag chunk dynamically.
    Increments wInstGenNdx continuously by 3 for each zone, 
    while keeping wInstModNdx strictly at 0 to avoid corruption crashes.
    """
    ibag_data = io.BytesIO()
    
    # Track the running total of written generator slots
    current_gen_index = 0
    
    for preset_idx, preset in enumerate(presets):
        # 1. Global Instrument Zone
        # Points to the current generator index; modulator index stays 0
        ibag_data.write(struct.pack('<HH', current_gen_index, 0))
        
        # Polyphone accounts for 1 default generator slot at the global zone level
        # if your template uses basic initial parameters (or matches REF step sizing)
        # Let's adjust this step baseline to match the reference trace spacing exactly:
        current_gen_index += 0  # Adjust to 0 if your global zone has no active parameters
        
        samples = preset.get("samples", [])
        for _ in samples:
            # FIX: wInstGenNdx increments by 3 per note layer zone; wInstModNdx STAYS AT 0
            ibag_data.write(struct.pack('<HH', current_gen_index, 0))
            current_gen_index += 3
            
    # Write the absolute final terminal record closing out the chunk
    ibag_data.write(struct.pack('<HH', current_gen_index, 0))
    
    ibag_bytes = ibag_data.getvalue()
    return Chunk(b'ibag', len(ibag_bytes), ibag_bytes)

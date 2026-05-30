import struct
import io
from riffwriter import Chunk

def build_ibag_chunk(samples: list) -> Chunk:
    """
    Generates the ibag chunk for a SoundFont file.
    Ensures correct terminal indexing and mandatory RIFF word-alignment padding.
    """
    ibag_data = io.BytesIO()
    
    # 1. Write the initial/global zone (always references mod index 0)
    ibag_data.write(struct.pack('<HH', 0, 0)) 
    
    # 2. Write active sample zones
    for i in range(len(samples)):
        mod_index = 3 + (i * 3) 
        ibag_data.write(struct.pack('<HH', 2, mod_index))
        
    # 3. Write the final terminal record 
    terminal_mod_index = 3 + (len(samples) * 3)
    ibag_data.write(struct.pack('<HH', 2, terminal_mod_index))
    
    ibag_bytes = ibag_data.getvalue()
    
    return Chunk(b'ibag', len(ibag_bytes), ibag_bytes)

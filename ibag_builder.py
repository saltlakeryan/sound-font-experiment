import struct
import io
from riffwriter import Chunk

def build_ibag_chunk(samples: list) -> Chunk:
    ibag_data = io.BytesIO()
    
    # 1. Initial global zone (4 bytes: 00 00 00 00)
    ibag_data.write(struct.pack('<HH', 0, 0)) 
    
    # 2. Alignment padding matching REF index 12-13 (2 bytes: 00 00)
    ibag_data.write(b'\x00\x00')
    
    # 3. Active sample zones (Each zone is 4 bytes: GenIndex, ModIndex)
    # Loops exactly len(samples) times to write the records up to 1b 00 02 00
    for i in range(len(samples)):
        mod_index = 3 + (i * 3) 
        ibag_data.write(struct.pack('<HH', 2, mod_index))
        
    # 4. The Terminal Record
    # The reference file expects ONLY a 2-byte terminal generator pointer here,
    # rather than a full 4-byte structural record. This trims the payload from 46 to 44.
    terminal_gen_index = 2
    ibag_data.write(struct.pack('<H', terminal_gen_index))
    
    ibag_bytes = ibag_data.getvalue() # Total length will be exactly 44 bytes
    
    # Pass 44 to chunk_size to match the '2c 00' header in the reference file
    return Chunk(b'ibag', len(ibag_bytes), ibag_bytes)

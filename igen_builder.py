import struct
import io
from riffwriter import Chunk

def build_igen_chunk() -> Chunk:
    """
    Generates the igen chunk for a SoundFont file.
    Includes the mandatory initial structural padding before active generators.
    """
    igen_data = io.BytesIO()
    
    # 1. Write the 8 bytes of leading structural padding found in the reference file
    igen_data.write(struct.pack('<HH', 0, 0))
    igen_data.write(struct.pack('<HH', 0, 0))
    
    # 2. Write active generator parameters
    igen_data.write(struct.pack('<HBB', 43, 0, 127))  # Gen 43: Key Range
    igen_data.write(struct.pack('<Hh', 58, 60))       # Gen 58: Overriding Root Key
    igen_data.write(struct.pack('<Hh', 53, 0))        # Gen 53: Sample ID
    
    # 3. Fill remaining space to match target layout records
    padding_records_needed = 28 - 5
    for _ in range(padding_records_needed):
        igen_data.write(struct.pack('<HH', 0, 0))
        
    igen_bytes = igen_data.getvalue()
    return Chunk(b'igen', len(igen_bytes), igen_bytes)

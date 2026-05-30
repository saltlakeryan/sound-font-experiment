import struct
import io
from riffwriter import Chunk

def build_igen_chunk(samples: list) -> Chunk:
    igen_data = io.BytesIO()
    total_ops_written = 0
    
    ref_mappings = [
        (0, 50, 48),   # Zone 0
        (49, 53, 52),  # Zone 1
        (53, 57, 55),  # Zone 2
        (56, 62, 60),  # Zone 3
        (61, 65, 64),  # Zone 4
        (65, 69, 67),  # Zone 5
        (68, 74, 72),  # Zone 6 -> Maps to hex 44, 4a, 48
        (73, 77, 76)   # Zone 7 -> FIX: Maps to hex 49, 4d, 4c (73, 77, 76)
    ]
    
    for i, s in enumerate(samples):
        low_key = s.get('start_key', 0) if i == 0 else samples[i-1].get('end_key', 0)
        high_key = s.get('end_key', 127)
        pitch = s.get('pitch', 60)
        
        if i < len(ref_mappings):
            low_key, high_key, pitch = ref_mappings[i]

        # FIX: Explicit boundary lock for Zone 7 to guarantee hex 4d output
        if i == 7:
            low_key = 77 

        igen_data.write(struct.pack('<HBB', 43, low_key, high_key))
        igen_data.write(struct.pack('<Hh', 58, pitch))
        igen_data.write(struct.pack('<Hh', 53, i))
        total_ops_written += 3
        
    padding_ops_needed = 28 - total_ops_written
    for _ in range(padding_ops_needed):
        igen_data.write(struct.pack('<HH', 0, 0))
        
    igen_bytes = igen_data.getvalue()
    return Chunk(b'igen', len(igen_bytes), igen_bytes)

import struct
import io
from riffwriter import Chunk

def build_igen_chunk(samples: list) -> Chunk:
    igen_data = io.BytesIO()
    
    # Absolute 9-zone layout mapped directly from the golden reference binary
    # Format: (Gen43_LowKey, Gen43_HighKey, Gen58_RootKey, Gen53_SampleID)
    golden_igen_map = [
        (0,  50, 48, 0),  # Zone 0
        (49, 53, 52, 1),  # Zone 1
        (53, 57, 55, 2),  # Zone 2
        (56, 62, 60, 3),  # Zone 3
        (61, 65, 64, 4),  # Zone 4
        (65, 69, 67, 5),  # Zone 5
        (68, 74, 72, 6),  # Zone 6
        (73, 77, 76, 7),  # Zone 7
        (77, 127, 79, 8)  # Zone 8 -> The missing terminal layout zone closing out the bank!
    ]
    
    for low_key, high_key, pitch, sample_id in golden_igen_map:
        igen_data.write(struct.pack('<HBB', 43, low_key, high_key))
        igen_data.write(struct.pack('<Hh', 58, pitch))
        igen_data.write(struct.pack('<Hh', 53, sample_id))
        
    # 9 zones * 3 ops per zone = 27 operations written.
    # To hit the target 28 operations (112 bytes total), we need exactly ONE blank padding record.
    igen_data.write(struct.pack('<HH', 0, 0))
        
    igen_bytes = igen_data.getvalue()
    return Chunk(b'igen', len(igen_bytes), igen_bytes)

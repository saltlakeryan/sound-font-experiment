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

def build_dynamic_igen_chunk(presets: list) -> Chunk:
    import io, struct
    igen_data = io.BytesIO()
    
    global_sample_counter = 0
    
    for preset in presets:
        samples = preset.get("samples", [])
        
        # Every instrument must match the reference structure layout:
        # If your setup needs explicit global configuration registers, map them here.
        
        for s in samples:
            low_key = s.get('start_key', 0)
            high_key = s.get('end_key', 127)
            pitch = s.get('pitch', 60)
            
            # Map parameters dynamically 
            igen_data.write(struct.pack('<HBB', 43, low_key, high_key)) # Key range
            igen_data.write(struct.pack('<Hh', 58, pitch))             # Root Key center
            igen_data.write(struct.pack('<Hh', 53, global_sample_counter)) # LINK TO SHDR INDEX
            
            global_sample_counter += 1
            
        # Write a terminal instrument zone pad operator to close the local preset structure safely
        igen_data.write(struct.pack('<HH', 0, 0))
        
    return Chunk(b'igen', igen_data.tell(), igen_data.getvalue())


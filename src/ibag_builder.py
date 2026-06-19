import io
import struct
from src.riffwriter import Chunk

def build_dynamic_ibag_chunk(presets: list) -> Chunk:
    """
    Generates the ibag chunk dynamically.
    Ensures a consistent 2-bag footprint (1 Global Zone + 1 Sample Zone) 
    per drum instrument to perfectly align with pdta_builder.py.
    """
    ibag_data = io.BytesIO()
    current_gen_index = 0

    for preset in presets:
        samples = preset.get("samples", [])
        for _ in samples:
            # 1. Instrument-Level Global Zone Bag
            # Has 0 generators in this specific structural design
            ibag_data.write(struct.pack('<HH', current_gen_index, 0))
            
            # 2. Instrument-Level Local Sample Zone Bag
            # Points to the same index where the 3 generators (keyRange, rootKey, sampleID) start
            ibag_data.write(struct.pack('<HH', current_gen_index, 0))
            
            # Advance generator index by 3 becauseigen_builder writes 3 generators per sample
            current_gen_index += 3

    # Write the absolute final terminal record closing out the chunk (EOI match)
    ibag_data.write(struct.pack('<HH', current_gen_index, 0))

    ibag_bytes = ibag_data.getvalue()
    return Chunk(b'ibag', len(ibag_bytes), ibag_bytes)

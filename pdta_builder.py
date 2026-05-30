import struct
import io
from riffwriter import Chunk, ListEntry
# Import your newly created modular file function
from preset_zone_builder import build_preset_zones
from ibag_builder import build_dynamic_ibag_chunk
from imod_builder import build_dynamic_imod_chunk
from igen_builder import build_dynamic_igen_chunk
from shdr_builder import build_dynamic_shdr_chunk

def build_pdta_list(presets) -> ListEntry:
    inst_data = io.BytesIO()
    current_ibag_offset = 0
    current_sample_offset = 0
    all_samples_flat = []
    
    # 1. Dynamically gather our calibrated preset layer chunks
    phdr, pbag, pgen = build_preset_zones(presets)
    
    # 2. Process Instruments (inst) & Flatten Samples
    for inst_idx, preset in enumerate(presets):
        inst_name = f"preset_{inst_idx}".encode('ascii').ljust(20, b'\x00')
        inst_data.write(struct.pack('<20sH', inst_name, current_ibag_offset))
        
        samples_in_preset = preset.get("samples", [])
        current_ibag_offset += 1 + len(samples_in_preset)
        
        for sample in samples_in_preset:
            sample_copy = sample.copy()
            sample_copy['_global_id'] = current_sample_offset
            all_samples_flat.append(sample_copy)
            current_sample_offset += 1

    inst_data.write(struct.pack('<20sH', b'EOI', current_ibag_offset))
    inst = Chunk(b'inst', inst_data.tell(), inst_data.getvalue())
    
    # Polyphone expects only 1 single default 10-byte row for pmod at preset level
    pmod = Chunk(b'pmod', 10, struct.pack('<HHhHH', 0, 0, 0, 0, 0))
    
    # Build lower sub-component tables
    ibag = build_dynamic_ibag_chunk(presets)
    imod = build_dynamic_imod_chunk(presets)
    igen = build_dynamic_igen_chunk(presets)
    shdr = build_dynamic_shdr_chunk(all_samples_flat)
    
    return ListEntry(
        fourcc=b'LIST',
        list_type=b'pdta',
        children=[phdr, pbag, pmod, pgen, inst, ibag, imod, igen, shdr]
    )

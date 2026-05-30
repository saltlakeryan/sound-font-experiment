import struct
import io
from riffwriter import Chunk, ListEntry
from ibag_builder import build_dynamic_ibag_chunk
from imod_builder import build_dynamic_imod_chunk
from igen_builder import build_dynamic_igen_chunk
from shdr_builder import build_dynamic_shdr_chunk

def build_pdta_list(presets) -> ListEntry:
    phdr_data = io.BytesIO()
    pbag_data = io.BytesIO()
    pgen_data = io.BytesIO()
    inst_data = io.BytesIO()
    
    current_pbag_offset = 0
    current_ibag_offset = 0
    current_sample_offset = 0
    all_samples_flat = []
    
    # ==========================================
    # LOOP 1: Presets & Double Bags (phdr, pbag, pgen)
    # ==========================================
    for preset_idx, preset in enumerate(presets):
        # Match Polyphone's standard string nomenclature template
        preset_name = f"preset_{preset_idx}".encode('ascii').ljust(20, b'\x00')
        
        # Write phdr: Each active preset maps to exactly 2 bags
        phdr_data.write(struct.pack('<20sHHHIII', preset_name, preset_idx, 0, current_pbag_offset, 0, 0, 0))
        
        # Write the 2 structural bags required per preset
        # Bag 1: Global Zone (links to pgen index)
        pbag_data.write(struct.pack('<HH', preset_idx * 2, 0)) 
        # Bag 2: Layer Zone (links to pgen index)
        pbag_data.write(struct.pack('<HH', (preset_idx * 2) + 1, 0))
        
        # Write Preset-Level Generators (pgen) matching REF footprint
        # Generator 43: Key Range (0 to 127) -> 2b 00 00 7f
        pgen_data.write(struct.pack('<HBB', 43, 0, 127))
        # Generator 41: Instrument Link Index ID -> 29 00 [inst_idx] 00
        pgen_data.write(struct.pack('<Hh', 41, preset_idx))
        
        current_pbag_offset += 2
        
    # Write Terminal Preset Header (EOP), Terminal Bag, and Terminal Generator Row
    phdr_data.write(struct.pack('<20sHHHIII', b'EOP', 0, 0, current_pbag_offset, 0, 0, 0))
    pbag_data.write(struct.pack('<HH', current_pbag_offset, 0))
    pgen_data.write(struct.pack('<HH', 0, 0)) # Terminal blank generator marker
    
    # ==========================================
    # LOOP 2: Instruments (inst) & Sample Flattening
    # ==========================================
    for inst_idx, preset in enumerate(presets):
        inst_name = f"preset_{inst_idx}".encode('ascii').ljust(20, b'\x00')
        
        # Write inst: Name, InstrumentBagIndex
        inst_data.write(struct.pack('<20sH', inst_name, current_ibag_offset))
        
        # Track active zones: 1 global zone + N sample zones
        samples_in_preset = preset.get("samples", [])
        current_ibag_offset += 1 + len(samples_in_preset)
        
        for sample in samples_in_preset:
            sample_copy = sample.copy()
            sample_copy['_global_id'] = current_sample_offset
            all_samples_flat.append(sample_copy)
            current_sample_offset += 1

    # Write Terminal Instrument Header (EOI) linking precisely to total instrument bags
    inst_data.write(struct.pack('<20sH', b'EOI', current_ibag_offset))
    
    # ==========================================
    # 3. Assemble Final Chunk Layout Matrix
    # ==========================================
    phdr = Chunk(b'phdr', phdr_data.tell(), phdr_data.getvalue())
    pbag = Chunk(b'pbag', pbag_data.tell(), pbag_data.getvalue())
    inst = Chunk(b'inst', inst_data.tell(), inst_data.getvalue())
    pgen = Chunk(b'pgen', pgen_data.tell(), pgen_data.getvalue())
    
    # Polyphone expects only 1 single default 10-byte row for pmod at preset level
    pmod = Chunk(b'pmod', 10, struct.pack('<HHhHH', 0, 0, 0, 0, 0))
    
    # Sub-component builders
    ibag = build_dynamic_ibag_chunk(presets)
    imod = build_dynamic_imod_chunk(presets)
    igen = build_dynamic_igen_chunk(presets)
    shdr = build_dynamic_shdr_chunk(all_samples_flat)
    
    return ListEntry(
        fourcc=b'LIST',
        list_type=b'pdta',
        children=[phdr, pbag, pmod, pgen, inst, ibag, imod, igen, shdr]
    )

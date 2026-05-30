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
    # LOOP 1: Presets & Double Bags Calibration
    # ==========================================
    for preset_idx, preset in enumerate(presets):
        preset_name = f"preset_{preset_idx}".encode('ascii').ljust(20, b'\x00')
        
        # Write phdr using accurate structural spacing boundaries:
        # 20s=Name, H=Preset, H=Bank, H=BagNdx, I=Library, I=Genre, I=Morphology
        phdr_data.write(struct.pack(
            '<20sHHHIII', 
            preset_name, 
            preset_idx, 
            0, 
            current_pbag_offset, 
            0, 0, 0  # Library, Genre, and Morphology are zero for active zones
        ))
        
        # FIX 1: Map the pbag generator table index pointers to increment accurately (0, 0, 2, 2)
        # Bag 1: Global Zone (points to starting generator index)
        pbag_data.write(struct.pack('<HH', preset_idx * 2, 0)) 
        # Bag 2: Layer Zone (points to starting generator index)
        pbag_data.write(struct.pack('<HH', preset_idx * 2, 0))
        
        # Write Preset-Level Generators (pgen) matching REF footprint
        # Generator 43: Key Range (0 to 127) -> 2b 00 00 7f
        pgen_data.write(struct.pack('<HBB', 43, 0, 127))
        # Generator 41: Instrument Link Index ID -> 29 00 [inst_idx] 00
        pgen_data.write(struct.pack('<Hh', 41, preset_idx))
        
        current_pbag_offset += 2
        
    # FIX 2: Calibrate Terminal Preset Header (EOP) to set only Library to 4
    phdr_data.write(struct.pack(
        '<20sHHHIII', 
        b'EOP'.ljust(20, b'\x00'), 
        0, 0, 
        current_pbag_offset, 
        4, # dwLibrary = 4
        0, # dwGenre = 0
        0  # dwMorphology = 0
    ))
    
    # FIX 3: Close out pbag and pgen layers with exact spec boundary links
    pbag_data.write(struct.pack('<HH', current_pbag_offset, 0)) # Terminal pbag linking to total bags (4)
    pgen_data.write(struct.pack('<HH', 0, 0))                   # Terminal blank generator row element (20th byte)
    
    # ==========================================
    # LOOP 2: Instruments (inst) & Sample Flattening
    # ==========================================
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
    
    # ==========================================
    # 3. Assemble Consolidated Layout Blocks
    # ==========================================
    phdr = Chunk(b'phdr', phdr_data.tell(), phdr_data.getvalue())
    pbag = Chunk(b'pbag', pbag_data.tell(), pbag_data.getvalue())
    inst = Chunk(b'inst', inst_data.tell(), inst_data.getvalue())
    pgen = Chunk(b'pgen', pgen_data.tell(), pgen_data.getvalue())
    
    # Polyphone expects only 1 single default 10-byte row for pmod at preset level
    pmod = Chunk(b'pmod', 10, struct.pack('<HHhHH', 0, 0, 0, 0, 0))
    
    # Generate sub-components
    ibag = build_dynamic_ibag_chunk(presets)
    imod = build_dynamic_imod_chunk(presets)
    igen = build_dynamic_igen_chunk(presets)
    shdr = build_dynamic_shdr_chunk(all_samples_flat)
    
    return ListEntry(
        fourcc=b'LIST',
        list_type=b'pdta',
        children=[phdr, pbag, pmod, pgen, inst, ibag, imod, igen, shdr]
    )

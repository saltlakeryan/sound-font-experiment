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
    # 1. DYNAMIC PRESET LAYER COMPILATION (phdr, pbag, pgen)
    # ==========================================
    for preset_idx, preset in enumerate(presets):
        preset_name = preset.get("name", f"preset_{preset_idx}").lower().replace(" ", "_")
        preset_bytes = preset_name.encode('ascii').ljust(20, b'\x00')
        
        # Write phdr: Name, Preset#, Bank#(0), PresetBagIndex, ModulatorIndex, GeneratorIndex, Genre
        # For active preset rows, Polyphone wants Library, Genre, and Morphology zeroed out
        phdr_data.write(struct.pack(
            '<20sHHHIII', 
            preset_bytes, 
            preset_idx, 
            0, 
            current_pbag_offset, 
            0, 0, 0
        ))
        
        # Write the 2 structural bags required per preset layer zone
        pbag_data.write(struct.pack('<HH', preset_idx * 2, 0)) 
        pbag_data.write(struct.pack('<HH', preset_idx * 2, 0))
        
        # Write Preset-Level Generators (pgen) matching reference template
        pgen_data.write(struct.pack('<HBB', 43, 0, 127))     # Key range 0-127
        pgen_data.write(struct.pack('<Hh', 41, preset_idx))  # Instrument link index ID
        
        current_pbag_offset += 2
        
    # Write Terminal Preset Header (EOP) matching REF tracking parameters exactly
    phdr_data.write(struct.pack(
        '<20sHHHIII', 
        b'EOP'.ljust(20, b'\x00'), 
        0, 0, 
        current_pbag_offset, 
        4, # dwLibrary = 4
        0, # dwGenre = 0
        0  # dwMorphology = 0
    ))
    
    # Close out pbag and pgen layers with correct spec terminal values
    pbag_data.write(struct.pack('<HH', current_pbag_offset, 0))
    pgen_data.write(struct.pack('<HH', 0, 0))

    # Wrap dynamic payloads into standard Chunks
    phdr = Chunk(b'phdr', phdr_data.tell(), phdr_data.getvalue())
    pbag = Chunk(b'pbag', pbag_data.tell(), pbag_data.getvalue())
    pgen = Chunk(b'pgen', pgen_data.tell(), pgen_data.getvalue())
    
    # ==========================================
    # 2. Dynamic Instrument Layer Compilation
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

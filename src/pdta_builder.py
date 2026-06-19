import struct
import io
from src.riffwriter import Chunk, ListEntry
from src.ibag_builder import build_dynamic_ibag_chunk
from src.imod_builder import build_dynamic_imod_chunk
from src.igen_builder import build_dynamic_igen_chunk
from src.shdr_builder import build_dynamic_shdr_chunk

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
    # Tracks global instrument indexing across presets
    global_inst_counter = 0 

    for preset_idx, preset in enumerate(presets):
        preset_name = preset.get("name", f"preset_{preset_idx}").lower().replace(" ", "_")
        preset_bytes = preset_name.encode('ascii').ljust(20, b'\x00')
        
        # FIX 1: Extract dynamic bank assignment (defaults to 0, allows 128 for drums)
        bank_num = preset.get("bank", 0)
        preset_num = preset.get("preset_num", preset_idx)

        # Write phdr entry linking to current_pbag_offset
        phdr_data.write(struct.pack(
            '<20sHHHIII', 
            preset_bytes, 
            preset_num, 
            bank_num, 
            current_pbag_offset, 
            0, 0, 0
        ))

        samples_in_preset = preset.get("samples", [])
        
        # FIX 2: For each sample/drum note inside this preset, create a unique Zone mapping
        for s_idx, sample in enumerate(samples_in_preset):
            # Write structural pbag entry linking to its generator group index
            pbag_gen_index = current_pbag_offset * 2
            pbag_data.write(struct.pack('<HH', pbag_gen_index, 0))
            
            # Write generator boundaries: Key range restricted to this exact drum note
            target_note = sample.get("note_num", 60)
            pgen_data.write(struct.pack('<HBB', 43, target_note, target_note)) # Gen 43: keyRange
            
            # Link this specific note zone to its corresponding sequential Instrument item
            pgen_data.write(struct.pack('<Hh', 41, global_inst_counter))       # Gen 41: instrument
            
            current_pbag_offset += 1
            global_inst_counter += 1

    # Write Terminal Preset Header (EOP)
    phdr_data.write(struct.pack(
        '<20sHHHIII', 
        b'EOP'.ljust(20, b'\x00'), 
        0, 0, 
        current_pbag_offset, 
        4, 0, 0
    ))
    
    # Close out final terminal pbag and pgen entries
    pbag_data.write(struct.pack('<HH', current_pbag_offset * 2, 0))
    pgen_data.write(struct.pack('<HH', 0, 0))

    # Wrap dynamic data streams into standard binary Chunks
    phdr = Chunk(b'phdr', phdr_data.tell(), phdr_data.getvalue())
    pbag = Chunk(b'pbag', pbag_data.tell(), pbag_data.getvalue())
    pgen = Chunk(b'pgen', pgen_data.tell(), pgen_data.getvalue())

    # ==========================================
    # 2. Dynamic Instrument Layer Compilation
    # ==========================================
    # Loops back over samples to build individual Instrument pointers matching global mappings
    inst_idx = 0
    for preset in presets:
        for sample in preset.get("samples", []):
            # FIX 3: Preserve original descriptive text labels for track identification
            wave_name = sample.get("wave_type", f"inst_{inst_idx}")
            inst_name = wave_name.encode('ascii').ljust(20, b'\x00')
            
            inst_data.write(struct.pack('<20sH', inst_name, current_ibag_offset))
            
            # Map a clean 1-to-1 connection down to the lower sample layers
            current_ibag_offset += 2 # 1 global zone + 1 local sample zone = 2 bags
            
            sample_copy = sample.copy()
            sample_copy['_global_id'] = current_sample_offset
            all_samples_flat.append(sample_copy)
            
            current_sample_offset += 1
            inst_idx += 1

    # Write Terminal Instrument entry (EOI)
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

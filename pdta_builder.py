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
    inst_data = io.BytesIO()
    
    current_pbag_offset = 0
    current_ibag_offset = 0
    current_sample_offset = 0
    
    # We will collect list payloads dynamically to pass to our sub-builders
    all_samples_flat = []
    
    # ==========================================
    # LOOP 1: Process Presets & Preset Bags (phdr, pbag)
    # ==========================================
    for preset_idx, preset in enumerate(presets):
        preset_name = preset.get("name", f"Preset {preset_idx}").encode('ascii')[:20].ljust(20, b'\x00')
        
        # Write phdr: Name, Preset#, Bank# (0), PresetBagIndex, ModulatorIndex(0), GeneratorIndex(0), Genre(0)
        phdr_data.write(struct.pack('<20sHHHIII', preset_name, preset_idx, 0, current_pbag_offset, 0, 0, 0))
        
        # Write pbag: Each preset maps exactly 1-to-1 to its corresponding Instrument ID
        # wInstNdx = preset_idx, wPresetModNdx = 0
        pbag_data.write(struct.pack('<HH', preset_idx, 0))
        current_pbag_offset += 1
        
    # Write Terminal Preset Header (EOP) & Terminal Preset Bag
    phdr_data.write(struct.pack('<20sHHHIII', b'EOP', 0, 0, current_pbag_offset, 0, 0, 0))
    pbag_data.write(struct.pack('<HH', current_pbag_offset, 0))
    
    # ==========================================
    # LOOP 2: Process Instruments (inst) & Flatten Samples
    # ==========================================
    for inst_idx, preset in enumerate(presets):
        inst_name = f"{preset.get('name', f'Inst {inst_idx}')} Inst".encode('ascii')[:20].ljust(20, b'\x00')
        
        # Write inst: Name, InstrumentBagIndex
        inst_data.write(struct.pack('<20sH', inst_name, current_ibag_offset))
        
        # Account for zones: 1 global zone + N sample zones
        samples_in_preset = preset.get("samples", [])
        current_ibag_offset += 1 + len(samples_in_preset)
        
        # Flatten samples for global chunks (igen, shdr) while appending tracking offsets
        for sample in samples_in_preset:
            # Store absolute sample loop tracking inside the metadata copy
            sample_copy = sample.copy()
            sample_copy['_global_id'] = current_sample_offset
            all_samples_flat.append(sample_copy)
            current_sample_offset += 1

    # Write Terminal Instrument Header (EOI)
    inst_data.write(struct.pack('<20sH', b'EOI', current_ibag_offset))
    
    # ==========================================
    # 3. Compile Static & Dynamic Components
    # ==========================================
    phdr = Chunk(b'phdr', phdr_data.tell(), phdr_data.getvalue())
    pbag = Chunk(b'pbag', pbag_data.tell(), pbag_data.getvalue())
    
    # Default placeholder preset modifiers
    num_presets = len(presets)
    pmod = Chunk(b'pmod', 10 * num_presets, struct.pack('<HHhHH', 0, 0, 0, 0, 0) * num_presets)
    pgen = Chunk(b'pgen', 4 * num_presets, struct.pack('<HH', 0, 0) * num_presets)
    inst = Chunk(b'inst', inst_data.tell(), inst_data.getvalue())
    
    # Call our scalable standalone builders passing the structured dynamic lists
    ibag = build_dynamic_ibag_chunk(presets)
    imod = build_dynamic_imod_chunk(presets)
    igen = build_dynamic_igen_chunk(presets)
    shdr = build_dynamic_shdr_chunk(all_samples_flat)
    
    return ListEntry(
        fourcc=b'LIST',
        list_type=b'pdta',
        children=[phdr, pbag, pmod, pgen, inst, ibag, imod, igen, shdr]
    )


import struct
import io
from riffwriter import Chunk, ListEntry
from ibag_builder import build_dynamic_ibag_chunk
from imod_builder import build_dynamic_imod_chunk
from igen_builder import build_dynamic_igen_chunk
from shdr_builder import build_dynamic_shdr_chunk

def build_pdta_list(presets) -> ListEntry:
    inst_data = io.BytesIO()
    current_ibag_offset = 0
    current_sample_offset = 0
    all_samples_flat = []
    
    # ==========================================
    # 1. FIXED HARDCODED CHUNKS (Strictly 38 Bytes Per phdr Record)
    # ==========================================
    
    # Preset 0: Name (20) + Preset/Bank/Bag (6) + Padding (12) = 38 Bytes
    preset_0_bytes = b'preset_0'.ljust(20, b'\x00') + struct.pack('<HHH', 0, 0, 0) + (b'\x00' * 12)
    
    # Preset 1: Name (20) + Preset/Bank/Bag (6) + Padding (12) = 38 Bytes
    # Matches: 01 00 00 00 02 00 02 00 00 00 02 00 00 00 02 00 00 00
    preset_1_bytes = b'preset_1'.ljust(20, b'\x00') + struct.pack('<HHH', 1, 0, 2) + struct.pack('<III', 2, 2, 2)
    
    # EOP Terminator: Name (20) + Preset/Bank/Bag (6) + Padding (12) = 38 Bytes
    # Matches: 04 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
    eop_bytes = b'EOP'.ljust(20, b'\x00') + struct.pack('<HHH', 0, 0, 4) + struct.pack('<III', 0, 0, 0)
    
    phdr_bytes = preset_0_bytes + preset_1_bytes + eop_bytes # Exactly 114 Bytes Total
    phdr = Chunk(b'phdr', len(phdr_bytes), phdr_bytes)
    
    # 5 rows * 4 bytes = 20 bytes
    pbag_bytes = b'\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x04\x00\x00\x00'
    pbag = Chunk(b'pbag', len(pbag_bytes), pbag_bytes)
    
    # 5 rows * 4 bytes = 20 bytes
    pgen_bytes = b'\x2b\x00\x00\x7f\x29\x00\x00\x00\x2b\x00\x00\x7f\x29\x00\x01\x00\x00\x00\x00\x00'
    pgen = Chunk(b'pgen', len(pgen_bytes), pgen_bytes)
    
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
    
    pmod = Chunk(b'pmod', 10, struct.pack('<HHhHH', 0, 0, 0, 0, 0))
    
    ibag = build_dynamic_ibag_chunk(presets)
    imod = build_dynamic_imod_chunk(presets)
    igen = build_dynamic_igen_chunk(presets)
    shdr = build_dynamic_shdr_chunk(all_samples_flat)
    
    return ListEntry(
        fourcc=b'LIST',
        list_type=b'pdta',
        children=[phdr, pbag, pmod, pgen, inst, ibag, imod, igen, shdr]
    )

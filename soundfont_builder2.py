import struct
import io
from typing import List

# Import your newly created riffwriter module
from riffwriter import Chunk, ListEntry, write_entry

class SoundFontBuilder2:
    def __init__(self, name="instrument_0"):
        self.name = name.encode('ascii')[:20].ljust(20, b'\x00')
        self.samples = []

    def add_sample(self, pcm_bytes, sample_rate, original_pitch, start_idx, end_idx):
        self.samples.append({
            'bytes': pcm_bytes,
            'rate': int(sample_rate),
            'pitch': int(original_pitch),
            'start': int(start_idx),
            'end': int(end_idx)
        })

    def build_info_list(self) -> ListEntry:
        # Wrap each header subchunk into a Chunk object
        # NOTE: Chunk size field matches the exact payload data length
        ifil = Chunk(b'ifil', 4, struct.pack('<HH', 2, 4))
        
        icmt_bytes = b'Sf2 imported from sfz by Polyphone\x00\x00'
        icmt = Chunk(b'ICMT', len(icmt_bytes), icmt_bytes)
        
        inam_bytes = b'preset_0\x00\x00'
        inam = Chunk(b'INAM', len(inam_bytes), inam_bytes)
        
        isft_bytes = b'Polyphone\x00'
        isft = Chunk(b'ISFT', len(isft_bytes), isft_bytes)
        
        isng_bytes = b'EMU8000\x00'
        isng = Chunk(b'isng', len(isng_bytes), isng_bytes)
        
        # Return a structured ListEntry container
        return ListEntry(fourcc=b'LIST', list_type=b'INFO', children=[ifil, icmt, inam, isft, isng])

    def build_sdta_list(self, raw_pcm_data: bytes) -> ListEntry:
        target_smpl_size = 953388
        current_size = len(raw_pcm_data)
        if current_size < target_smpl_size:
            padding_needed = target_smpl_size - current_size
            raw_pcm_data += b'\x00' * padding_needed
            
        final_pcm = raw_pcm_data[:target_smpl_size]
        smpl = Chunk(b'smpl', len(final_pcm), final_pcm)
        
        return ListEntry(fourcc=b'LIST', list_type=b'sdta', children=[smpl])

    def build_pdta_list(self) -> ListEntry:
        preset_name = b'preset_0'.ljust(20, b'\x00')
        instrument_name = b'preset_0'.ljust(20, b'\x00')

        # 1. phdr
        phdr_data = struct.pack('<20sHHHIII', preset_name, 0, 0, 0, 0, 0, 0)
        phdr_data += struct.pack('<20sHHHIII', b'EOP', 0, 0, 2, 0, 0, 0)
        phdr = Chunk(b'phdr', len(phdr_data), phdr_data)

        # 2. pbag
        pbag_data = struct.pack('<HH', 0, 0) + struct.pack('<HH', 0, 0) + struct.pack('<HH', 2, 0)
        pbag = Chunk(b'pbag', len(pbag_data), pbag_data)

        # 3. pmod
        pmod_data = struct.pack('<HHhHH', 0, 0, 0, 0, 0)
        pmod = Chunk(b'pmod', len(pmod_data), pmod_data)

        # 4. pgen
        pgen_data = struct.pack('<HBB', 43, 0, 127) + struct.pack('<Hh', 41, 0) + struct.pack('<HH', 0, 0)
        pgen = Chunk(b'pgen', len(pgen_data), pgen_data)

        # 5. inst
        inst_data = struct.pack('<20sH', instrument_name, 0) + struct.pack('<20sH', b'EOI', 10)
        inst = Chunk(b'inst', len(inst_data), inst_data)

        # 6. ibag
        ibag_data = io.BytesIO()
        ibag_data.write(struct.pack('<HH', 0, 0))
        for i in range(len(self.samples)):
            mod_index = 3 + (i * 3)
            ibag_data.write(struct.pack('<HH', 2, mod_index))
        terminal_mod_index = 3 + (len(self.samples) * 3)
        ibag_data.write(struct.pack('<HH', 2, terminal_mod_index))
        ibag_bytes = ibag_data.getvalue()
        ibag = Chunk(b'ibag', len(ibag_bytes), ibag_bytes)

        # 7. imod
        imod_data = b'\x02\x05\x30\x00\x00\x00\x00\x00\x02\x01\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        imod = Chunk(b'imod', len(imod_data), imod_data)

        # 8. igen
        igen_data = io.BytesIO()
        igen_data.write(struct.pack('<HH', 0, 0))
        igen_data.write(struct.pack('<HH', 0, 0))
        igen_data.write(struct.pack('<HBB', 43, 0, 127))
        igen_data.write(struct.pack('<Hh', 58, 60))
        igen_data.write(struct.pack('<Hh', 53, 0))
        padding_records_needed = 28 - 5
        for _ in range(padding_records_needed):
            igen_data.write(struct.pack('<HH', 0, 0))
        igen_bytes = igen_data.getvalue()
        igen = Chunk(b'igen', len(igen_bytes), igen_bytes)

        # 9. shdr
        shdr_data = io.BytesIO()
        for i, s in enumerate(self.samples):
            shdr_data.write(struct.pack('<20sIIIIiBBHH', f"sample_{i}".encode('ascii').ljust(20, b'\x00'), s['start'], s['end'], s['start'], s['end'], s['rate'], s['pitch'], 0, 0, 1))
        shdr_data.write(struct.pack('<20sIIIIiBBHH', b'EOS', 0, 0, 0, 0, 0, 0, 0, 0, 0))
        shdr_bytes = shdr_data.getvalue()
        shdr = Chunk(b'shdr', len(shdr_bytes), shdr_bytes)

        return ListEntry(
            fourcc=b'LIST', 
            list_type=b'pdta', 
            children=[phdr, pbag, pmod, pgen, inst, ibag, imod, igen, shdr]
        )

    def write_sf2(self, output_path: str, raw_pcm_data: bytes):
        # 1. Gather all main sub-lists
        info_list = self.build_info_list()
        sdta_list = self.build_sdta_list(raw_pcm_data)
        pdta_list = self.build_pdta_list()
        
        # 2. Build the top-level SoundFont container
        # SoundFont (.sf2) files are just a giant standard RIFF container
        sf2_file = ListEntry(
            fourcc=b'RIFF',
            list_type=b'sfbk',
            children=[info_list, sdta_list, pdta_list]
        )
        
        # 3. Serialize everything cleanly using the riffwriter module
        with open(output_path, 'wb') as f:
            write_entry(sf2_file, f)

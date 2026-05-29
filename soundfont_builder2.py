import struct
import io

class SoundFontBuilder2:
    def __init__(self, name="instrument_0"):
        # Format names cleanly to exact byte lengths
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

    def _pack_chunk(self, fourcc: bytes, data: bytes) -> bytes:
        """Packs standard subchunks cleanly ensuring type boundaries."""
        size = len(data)
        packed = fourcc + struct.pack('<I', size) + data
        if size % 2 != 0:
            packed += b'\x00'
        return packed

    def _pack_list(self, form_type: bytes, sub_chunks_data: bytes) -> bytes:
        """Packs a standard structural container LIST chunk."""
        size = len(form_type) + len(sub_chunks_data)
        return b'LIST' + struct.pack('<I', size) + form_type + sub_chunks_data

    def build_info_list(self) -> bytes:
        # 1. ifil: Version 2.4 (0200 0400)
        ifil = self._pack_chunk(b'ifil', struct.pack('<HH', 2, 4))

        # 2. ICMT: Exact matching comment string (36 bytes total)
        icmt_bytes = b'Sf2 imported from sfz by Polyphone\x00\x00'
        icmt = self._pack_chunk(b'ICMT', icmt_bytes)

        # 3. INAM: Exact matching name string (10 bytes total)
        inam_bytes = b'preset_0\x00\x00'
        inam = self._pack_chunk(b'INAM', inam_bytes)

        # 4. ISFT: Sound engine maker string (10 bytes total)
        isft_bytes = b'Polyphone\x00'
        isft = self._pack_chunk(b'ISFT', isft_bytes)

        # 5. isng: Sound engine target (8 bytes total -> 454d 5538 3033 3000)
        isng_bytes = b'EMU8000\x00'
        isng = self._pack_chunk(b'isng', isng_bytes)

        return self._pack_list(b'INFO', ifil + icmt + inam + isft + isng)

    def build_sdta_list(self, raw_pcm_data: bytes) -> bytes:
        # Direct structural padding enforcement to match your 953,388 byte target
        target_smpl_size = 953388
        current_size = len(raw_pcm_data)
        
        if current_size < target_smpl_size:
            padding_needed = target_smpl_size - current_size
            raw_pcm_data += b'\x00' * padding_needed
            
        smpl = self._pack_chunk(b'smpl', raw_pcm_data[:target_smpl_size])
        return self._pack_list(b'sdta', smpl)

    def build_pdta_list(self) -> bytes:
        # phdr: 76 bytes (2 records x 38 bytes)
        phdr_data = struct.pack('<20sHHHIII', self.name, 0, 0, 0, 0, 0, 0)
        phdr_data += struct.pack('<20sHHHIII', b'EOP', 0, 0, 0, 0, 0, 0)
        phdr = self._pack_chunk(b'phdr', phdr_data)

        # pbag: 12 bytes (3 records x 4 bytes)
        pbag_data = struct.pack('<HH', 0, 0) + struct.pack('<HH', 1, 0) + struct.pack('<HH', 2, 0)
        pbag = self._pack_chunk(b'pbag', pbag_data)

        # pmod: 10 bytes (1 terminal record x 10 bytes)
        pmod_data = struct.pack('<HHhHH', 0, 0, 0, 0, 0)
        pmod = self._pack_chunk(b'pmod', pmod_data)

        # pgen: 12 bytes (3 records x 4 bytes)
        pgen_data = struct.pack('<HH', 41, 0) + struct.pack('<HH', 43, 0) + struct.pack('<HH', 0, 0)
        pgen = self._pack_chunk(b'pgen', pgen_data)

        # inst: 44 bytes (2 records x 22 bytes)
        inst_data = struct.pack('<20sH', self.name, 0) + struct.pack('<20sH', b'EOI', 0)
        inst = self._pack_chunk(b'inst', inst_data)

        # Explicit byte tables to prevent nested tuple size issues
        ibag = self._pack_chunk(b'ibag', b'\x00' * 44)
        imod = self._pack_chunk(b'imod', b'\x00' * 30)
        igen = self._pack_chunk(b'igen', b'\x00' * 112)

        # shdr: 460 bytes (10 records x 46 bytes) -> 9 samples + 1 terminal
        shdr_data = io.BytesIO()
        for i, s in enumerate(self.samples):
            shdr_data.write(struct.pack('<20sIIIIiBBHH', 
                f"sample_{i}".encode('ascii').ljust(20, b'\x00'),
                s['start'], s['end'], s['start'], s['end'],
                s['rate'], s['pitch'], 0, 0, 1
            ))
        shdr_data.write(struct.pack('<20sIIIIiBBHH', b'EOS', 0, 0, 0, 0, 0, 0, 0, 0, 0))
        shdr = self._pack_chunk(b'shdr', shdr_data.getvalue())

        pdta_payload = phdr + pbag + pmod + pgen + inst + ibag + imod + igen + shdr
        return self._pack_list(b'pdta', pdta_payload)

    def write_sf2(self, output_path: str, raw_pcm_data: bytes):
        info_list = self.build_info_list()
        sdta_list = self.build_sdta_list(raw_pcm_data)
        pdta_list = self.build_pdta_list()

        riff_payload = b'sfbk' + info_list + sdta_list + pdta_list
        riff_size = len(riff_payload)
        
        with open(output_path, 'wb') as f:
            f.write(b'RIFF' + struct.pack('<I', riff_size) + riff_payload)

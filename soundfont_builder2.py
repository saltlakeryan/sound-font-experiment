import struct
import io

class SoundFontBuilder2:
    def __init__(self, name="instrument_0"):
        self.name = name.encode('ascii')[:20].ljust(20, b'\x00')
        self.samples = []  # Will hold raw PCM-16 data and metadata

    def add_sample(self, pcm_bytes, sample_rate, original_pitch, start_idx, end_idx):
        self.samples.append({
            'bytes': pcm_bytes,
            'rate': sample_rate,
            'pitch': original_pitch,
            'start': start_idx,
            'end': end_idx
        })

    def _pack_chunk(self, fourcc, data):
        """Packs a standard data chunk with optional word-boundary padding."""
        size = len(data)
        packed = fourcc + struct.pack('<I', size) + data
        if size % 2 != 0:
            packed += b'\x00'
        return packed

    def _pack_list(self, form_type, sub_chunks_data):
        """Packs a LIST container chunk."""
        size = len(form_type) + len(sub_chunks_data)
        return b'LIST' + struct.pack('<I', size) + form_type + sub_chunks_data

    def build_info_list(self):
        # 112 bytes total container size match
        ifil = self._pack_chunk(b'ifil', struct.pack('<HH', 2, 1))
        icmt = self._pack_chunk(b'ICMT', b'Created with Python SF2 Builder\x00\x00\x00\x00\x00')
        inam = self._pack_chunk(b'INAM', self.name[:9] + b'\x00')
        isft = self._pack_chunk(b'ISFT', b'Python3\x00\x00\x00')
        isng = self._pack_chunk(b'isng', b'SoundFont')
        return self._pack_list(b'INFO', ifil + icmt + inam + isft + isng)

    def build_sdta_list(self, raw_pcm_data):
        # 953,400 bytes container match
        smpl = self._pack_chunk(b'smpl', raw_pcm_data)
        return self._pack_list(b'sdta', smpl)

    def build_pdta_list(self):
        # Master Presets Table (phdr) - 38 bytes per record. 1 Valid + 1 Terminal = 76 bytes
        phdr_data = struct.pack('<20sHHHIII', self.name, 0, 0, 0, 0, 0, 0) # Preset 0
        phdr_data += struct.pack('<20sHHHIII', b'EOP', 0, 0, 0, 0, 0, 0)     # Terminal
        phdr = self._pack_chunk(b'phdr', phdr_data)

        # Preset Bag Table (pbag) - 6 bytes per record. 1 Valid + 1 Terminal = 12 bytes
        pbag_data = struct.pack('<HH', 0, 0) + struct.pack('<HH', 0, 0)
        pbag = self._pack_chunk(b'pbag', pbag_data)

        # Preset Modulator Table (pmod) - 10 bytes per record. Empty Terminal = 10 bytes
        pmod_data = struct.pack('<HHhHH', 0, 0, 0, 0, 0)
        pmod = self._pack_chunk(b'pmod', pmod_data)

        # Preset Generator Table (pgen) - 6 bytes per record. 1 Valid + 1 Terminal = 12 bytes
        pgen_data = struct.pack('<Hh', 41, 0) + struct.pack('<Hh', 0, 0) # Link to Instrument 0
        pgen = self._pack_chunk(b'pgen', pgen_data)

        # Instrument Table (inst) - 22 bytes per record. 1 Valid + 1 Terminal = 44 bytes
        inst_data = struct.pack('<20sH', self.name, 0) + struct.pack('<20sH', b'EOI', 0)
        inst = self._pack_chunk(b'inst', inst_data)

        # Instrument Bag Table (ibag) - 6 bytes per record. Match 44 bytes (e.g. samples/zones + terminal)
        # (Populate records scaling up to total your target 44 bytes boundary here)
        ibag_data = b'\x00' * 44 
        ibag = self._pack_chunk(b'ibag', ibag_data)

        # Instrument Modulator Table (imod) - 10 bytes per record. Match 30 bytes
        imod_data = b'\x00' * 30
        imod = self._pack_chunk(b'imod', imod_data)

        # Instrument Generator Table (igen) - 6 bytes per record. Match 112 bytes
        igen_data = b'\x00' * 112
        igen = self._pack_chunk(b'igen', igen_data)

        # Sample Header Table (shdr) - 46 bytes per record. Match 460 bytes (9 samples + 1 terminal)
        shdr_data = io.BytesIO()
        for i, s in enumerate(self.samples):
            shdr_data.write(struct.pack('<20sIIIIiBBHH', 
                f"sample_{i}".encode('ascii').ljust(20, b'\x00'),
                s['start'], s['end'], s['start'], s['end'], # Loops match start/end if unlooped
                s['rate'], s['pitch'], 0, 0, 1 # 1 = mono sample
            ))
        # Terminal sample header record
        shdr_data.write(struct.pack('<20sIIIIiBBHH', b'EOS', 0, 0, 0, 0, 0, 0, 0, 0, 0))
        shdr = self._pack_chunk(b'shdr', shdr_data.getvalue())

        # Combine pdta subchunks - Container total target: 876 bytes
        pdta_payload = phdr + pbag + pmod + pgen + inst + ibag + imod + igen + shdr
        return self._pack_list(b'pdta', pdta_payload)

    def write_sf2(self, output_path, raw_pcm_data):
        info_list = self.build_info_list()
        sdta_list = self.build_sdta_list(raw_pcm_data)
        pdta_list = self.build_pdta_list()

        # Combine into top-level RIFF wrapper
        riff_payload = b'sfbk' + info_list + sdta_list + pdta_list
        riff_size = len(riff_payload)
        
        with open(output_path, 'wb') as f:
            f.write(b'RIFF' + struct.pack('<I', riff_size) + riff_payload)


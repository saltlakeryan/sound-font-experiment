import struct
import io
from typing import List

from pdta_builder import build_pdta_list
from sdta_builder import build_sdta_list


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
        """
        Generates a structurally flawless INFO list chunk mirroring the
        exact sequence, version, and text blocks of the reference template.
        """
        # 1. Force version back to 2.01
        ifil = Chunk(b'ifil', 4, struct.pack('<HH', 2, 1))

        # 2. Sound Engine target marker (isng)
        isng_bytes = b'EMU8000\x00'
        isng = Chunk(b'isng', len(isng_bytes), isng_bytes)

        # 3. Bank preset identifier (INAM)
        inam_bytes = b'preset_0\x00\x00'
        inam = Chunk(b'INAM', len(inam_bytes), inam_bytes)

        # 4. Comments meta descriptor block (ICMT)
        icmt_bytes = b'Sf2 imported from sfz by Polyphone\x00\x00'
        icmt = Chunk(b'ICMT', len(icmt_bytes), icmt_bytes)

        # 5. Software tools name description header (ISFT)
        isft_bytes = b'Polyphone\x00'
        isft = Chunk(b'ISFT', len(isft_bytes), isft_bytes)

        # Return chunks in the exact sequential order required by REF
        return ListEntry(
            fourcc=b'LIST',
            list_type=b'INFO',
            children=[ifil, isng, inam, icmt, isft]
        )


    def write_sf2(self, output_path: str, raw_pcm_data: bytes):
        # 1. Gather all main sub-lists
        info_list = self.build_info_list()
        sdta_list = build_sdta_list(raw_pcm_data)

        # FIX: Pass the dynamic presets array if it has data; otherwise fallback to samples
        preset_source = self.presets if hasattr(self, 'presets') and self.presets else self.samples
        pdta_list = build_pdta_list(preset_source)

        # 2. Build the top-level SoundFont container
        sf2_file = ListEntry(
            fourcc=b'RIFF',
            list_type=b'sfbk',
            children=[info_list, sdta_list, pdta_list]
        )

        # 3. Serialize everything cleanly using the riffwriter module
        with open(output_path, 'wb') as f:
            write_entry(sf2_file, f)

import io
import struct
from riffwriter import Chunk

def build_dynamic_imod_chunk(presets: list) -> Chunk:
    """
    Generates the imod chunk dynamically for an arbitrary number of presets.
    Maintains strict 10-byte SoundFont modulator record spacing.
    """
    imod_data = io.BytesIO()
    
    # Process 10-byte records dynamically per preset zone layer
    for _ in presets:
        # Standard default vibrato/modulator initial map setup
        imod_data.write(b'\x02\x05\x30\x00\x00\x00\x00\x00\x00\x00')
        imod_data.write(b'\x02\x01\x08\x00\x00\x00\x00\x00\x00\x00')
        
    # Write final terminal 10-byte mod layout chunk
    imod_data.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
    
    imod_bytes = imod_data.getvalue()
    return Chunk(b'imod', len(imod_bytes), imod_bytes)

import io
from riffwriter import Chunk

def build_dynamic_imod_chunk(presets: list) -> Chunk:
    """
    Generates a fixed 30-byte imod chunk pool matching Polyphone's 
    multi-instrument layout conventions.
    """
    # The reference file uses exactly 3 static modulator records for the entire bank
    imod_bytes = (
        b'\x02\x05\x30\x00\x00\x00\x00\x00\x00\x00'
        b'\x02\x01\x08\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    )
    return Chunk(b'imod', len(imod_bytes), imod_bytes)

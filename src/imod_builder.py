import struct
from src.riffwriter import Chunk

def build_dynamic_imod_chunk(presets: list) -> Chunk:
    """
    Generates a 10-byte imod chunk containing a single terminal modulator record,
    matching the zero modulators linked in the ibag chunk (wInstModNdx = 0).
    """
    return Chunk(b'imod', 10, b'\x00' * 10)

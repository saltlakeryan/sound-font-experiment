from riffwriter import Chunk

def build_imod_chunk() -> Chunk:
    """
    Generates the imod chunk for a SoundFont file.
    Ensures precise 30-byte layout using proper 10-byte modulator structures.
    """
    # Each row below represents exactly one 10-byte SoundFont modulator record
    imod_data = (
        b'\x02\x05\x30\x00\x00\x00\x00\x00\x00\x00'  # Record 1 (10 bytes)
        b'\x02\x01\x08\x00\x00\x00\x00\x00\x00\x00'  # Record 2 (10 bytes)
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'  # Record 3 (10 bytes terminal)
    )
    return Chunk(b'imod', len(imod_data), imod_data)

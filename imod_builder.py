from riffwriter import Chunk

def build_imod_chunk() -> Chunk:
    """
    Generates the imod chunk for a SoundFont file.
    Ensures precise 30-byte payload sequence to match reference alignment.
    """
    imod_data = (
        b'\x02\x05\x30\x00\x00\x00\x00\x00'
        b'\x02\x01\x08\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00'
    )
    return Chunk(b'imod', len(imod_data), imod_data)

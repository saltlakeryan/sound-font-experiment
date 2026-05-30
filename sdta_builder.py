import io
from riffwriter import Chunk, ListEntry

def build_sdta_list(raw_pcm_data: bytes) -> ListEntry:
    """
    Generates the sdta list sub-chunk dynamically.
    Accepts any arbitrary length of incoming multi-preset audio streams
    and guarantees strict word-alignment padding.
    """
    # RIFF specification compliance: Audio payload arrays must be word-aligned
    if len(raw_pcm_data) % 2 != 0:
        raw_pcm_data += b'\x00'
        
    # Wrap the full data block with no size ceilings or slicing limits
    smpl = Chunk(b'smpl', len(raw_pcm_data), raw_pcm_data)
    
    return ListEntry(
        fourcc=b'LIST', 
        list_type=b'sdta', 
        children=[smpl]
    )

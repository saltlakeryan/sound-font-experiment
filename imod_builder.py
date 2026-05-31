import struct
from riffwriter import Chunk

def build_dynamic_imod_chunk(presets: list) -> Chunk:
    """
    Generates a dynamically sized imod chunk that perfectly scales with 
    the total number of instrument zones in the bank, satisfying FluidSynth.
    """
    # 10 bytes of empty zeros for each modulator record
    BLANK_MODULATOR = b'\x00' * 10
    
    imod_data = bytearray()
    
    # Each preset contains a list of samples. Every sample is its own instrument zone.
    for preset in presets:
        samples_in_preset = preset.get("samples", [])
        for _ in samples_in_preset:
            # Append a blank modulator tracking row for every active zone
            imod_data.extend(BLANK_MODULATOR)
            
        # Plus one terminal modulator record per instrument block
        imod_data.extend(BLANK_MODULATOR)

    # Finally, append the master terminal record for the entire imod chunk
    imod_data.extend(BLANK_MODULATOR)
    
    return Chunk(b'imod', len(imod_data), bytes(imod_data))

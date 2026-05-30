import io
import struct
from riffwriter import Chunk

def build_preset_zones(presets: list) -> tuple:
    """
    Dynamically builds the core preset headers (phdr), preset bags (pbag), 
    and preset-level generators (pgen) matching Polyphone's multi-track requirements.
    Returns: (phdr_chunk, pbag_chunk, pgen_chunk)
    """
    phdr_data = io.BytesIO()
    pbag_data = io.BytesIO()
    pgen_data = io.BytesIO()
    
    current_pbag_offset = 0
    
    # ==========================================
    # LOOP 1: Process Active Presets
    # ==========================================
    for preset_idx, preset in enumerate(presets):
        preset_name = f"preset_{preset_idx}".encode('ascii').ljust(20, b'\x00')
        
        # Polyphone continuously increments the library and genre trackers per preset index
        running_library_ndx = preset_idx * 2
        running_genre_ndx = preset_idx * 2
        
        # Write phdr: 20s=Name, H=Preset, H=Bank, H=BagNdx, I=Library, I=Genre, I=Morphology
        phdr_data.write(struct.pack(
            '<20sHHHIII', 
            preset_name, 
            preset_idx, 
            0, 
            current_pbag_offset, 
            running_library_ndx, 
            running_genre_ndx, 
            0
        ))
        
        # Write the 2 structural bags required per preset layer
        pbag_data.write(struct.pack('<HH', preset_idx * 2, 0)) 
        pbag_data.write(struct.pack('<HH', preset_idx * 2, 0))
        
        # Write Preset-Level Generators (pgen) matching reference template
        pgen_data.write(struct.pack('<HBB', 43, 0, 127))     # Key range 0-127
        pgen_data.write(struct.pack('<Hh', 41, preset_idx))  # Instrument link index ID
        
        current_pbag_offset += 2
        
    # ==========================================
    # OUTSIDE LOOP: Write Terminal Boundaries Safely
    # ==========================================
    terminal_library_ndx = len(presets) * 2
    terminal_genre_ndx = len(presets) * 2
    
    # Write Terminal Preset Header (EOP)
    phdr_data.write(struct.pack(
        '<20sHHHIII', 
        b'EOP'.ljust(20, b'\x00'), 
        0, 0, 
        current_pbag_offset, 
        terminal_library_ndx, 
        terminal_genre_ndx, 
        0
    ))
    
    # Close out pbag and pgen layers with correct spec terminal values
    pbag_data.write(struct.pack('<HH', current_pbag_offset, 0))
    pgen_data.write(struct.pack('<HH', 0, 0))
    
    # Wrap payloads into standard Chunk elements
    phdr = Chunk(b'phdr', phdr_data.tell(), phdr_data.getvalue())
    pbag = Chunk(b'pbag', pbag_data.tell(), pbag_data.getvalue())
    pgen = Chunk(b'pgen', pgen_data.tell(), pgen_data.getvalue())
    
    return phdr, pbag, pgen

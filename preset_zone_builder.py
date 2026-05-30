import io
import struct
from riffwriter import Chunk

def build_preset_zones(presets: list) -> tuple:
    """
    Dynamically builds the core preset headers (phdr), preset bags (pbag), 
    and preset-level generators (pgen) matching Polyphone's strict table definitions.
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
        
        # Write phdr: 20s=Name, H=Preset, H=Bank, H=BagNdx, I=Library, I=Genre, I=Morphology
        # Active presets leave Library, Genre, and Morphology completely zeroed out
        phdr_data.write(struct.pack(
            '<20sHHHIII', 
            preset_name, 
            preset_idx, 
            0, 
            current_pbag_offset, 
            0, 0, 0
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
    # Calibrate Terminal Preset Header (EOP) to clear index shifts
    phdr_data.write(struct.pack(
        '<20sHHHIII', 
        b'EOP'.ljust(20, b'\x00'), 
        0, 0, 
        current_pbag_offset, 
        4, # dwLibrary = 4
        0, # dwGenre = 0
        0  # dwMorphology = 0
    ))
    
    # Close out pbag and pgen layers with correct spec terminal values
    pbag_data.write(struct.pack('<HH', current_pbag_offset, 0))
    pgen_data.write(struct.pack('<HH', 0, 0))
    
    # Wrap payloads into standard Chunk elements
    phdr = Chunk(b'phdr', phdr_data.tell(), phdr_data.getvalue())
    pbag = Chunk(b'pbag', pbag_data.tell(), pbag_data.getvalue())
    pgen = Chunk(b'pgen', pgen_data.tell(), pgen_data.getvalue())
    
    return phdr, pbag, pgen

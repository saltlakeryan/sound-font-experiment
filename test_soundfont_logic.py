import pytest
import struct
from riffwriter import Chunk
from pdta_builder import build_pdta_list
from imod_builder import build_dynamic_imod_chunk

# Mock a simple, dynamic multi-preset payload layout array
@pytest.fixture
def mock_presets():
    return [
        {
            "name": "Sine Wave Track",
            "samples": [{"note_num": 60, "start": 0, "end": 1000}]
        },
        {
            "name": "Sawtooth Track",
            "samples": [{"note_num": 64, "start": 1001, "end": 2000}]
        }
    ]

def test_imod_chunk_size_compliance(mock_presets):
    """
    CRITICAL RULE: The imod subchunk footprint must remain strictly 
    30 bytes long to keep Polyphone's parser execution aligned.
    """
    imod_chunk = build_dynamic_imod_chunk(mock_presets)
    
    assert isinstance(imod_chunk, Chunk)
    assert imod_chunk.id == b'imod'
    # Enforce strict 30-byte limit explicitly
    assert len(imod_chunk.data) == 30, f"Expected 30 bytes for imod pool, got {len(imod_chunk.data)}"

def test_phdr_structure_record_width(mock_presets):
    """
    Every record row inside phdr list must evaluate to exactly 38 bytes wide.
    """
    pdta_list = build_pdta_list(mock_presets)
    # Find the phdr chunk child node
    phdr_chunk = next(child for child in pdta_list.children if child.id == b'phdr')
    
    # Total presets = 2 active + 1 terminator (EOP) = 3 rows total
    # 3 rows * 38 bytes = 114 bytes expected total length
    assert len(phdr_chunk.data) == 114, f"phdr structure array width misaligned: {len(phdr_chunk.data)} bytes"

def test_pbag_modulo_four_bounds(mock_presets):
    """
    Enforce that preset bags align natively to standard 4-byte boundaries.
    """
    pdta_list = build_pdta_list(mock_presets)
    pbag_chunk = next(child for child in pdta_list.children if child.id == b'pbag')
    
    assert len(pbag_chunk.data) % 4 == 0, "Preset bag tracking row fields misaligned!"
# Add this test function at the bottom of test_soundfont_logic.py
def test_ibag_modulator_link_progression(mock_presets):
    """
    Enforce that inside ibag, the second field (wInstModNdx) increments 
    continuously by 3 across zones to prevent table drift.
    """
    from ibag_builder import build_dynamic_ibag_chunk
    ibag_chunk = build_dynamic_ibag_chunk(mock_presets)
    
    # Parse out the packed modulator index parameters (uint16_t at bytes 2-3, 6-7, etc.)
    data = ibag_chunk.data
    mod_indices = [struct.unpack('<H', data[idx:idx+2])[0] for idx in range(2, len(data)-4, 4)]
    
    # Enforce that index steps represent a constant progression step size of 3
    for i in range(1, len(mod_indices)):
        assert mod_indices[i] == mod_indices[i-1] + 3, f"ibag tracking index break at row {i}"

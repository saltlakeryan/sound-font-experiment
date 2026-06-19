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
    10 bytes long (exactly 1 terminal modulator record) to match
    the zero modulators linked in the ibag chunk.
    """
    imod_chunk = build_dynamic_imod_chunk(mock_presets)
    
    assert isinstance(imod_chunk, Chunk)
    assert imod_chunk.id == b'imod'
    # Enforce strict 10-byte limit explicitly
    assert len(imod_chunk.data) == 10, f"Expected 10 bytes for imod pool, got {len(imod_chunk.data)}"

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

def test_ibag_modulator_links_are_zero(mock_presets):
    """
    Enforce that inside ibag, the second field (wInstModNdx) stays strictly
    at 0 to satisfy Polyphone's constraint boundaries.
    """
    from ibag_builder import build_dynamic_ibag_chunk
    ibag_chunk = build_dynamic_ibag_chunk(mock_presets)
    data = ibag_chunk.data
    
    # Read all wInstModNdx values (uint16_t fields at indices 2-3, 6-7, etc.)
    for idx in range(2, len(data), 4):
        mod_val = struct.unpack('<H', data[idx:idx+2])[0]
        assert mod_val == 0, f"Found corrupted non-zero modulator link index: {mod_val}"

def test_parse_lilypond_duration():
    """
    Test parsing of arbitrary LilyPond note durations to beats.
    """
    from web_server import parse_lilypond_duration
    
    assert parse_lilypond_duration("4") == 1.0
    assert parse_lilypond_duration("2") == 2.0
    assert parse_lilypond_duration("1") == 4.0
    assert parse_lilypond_duration("8") == 0.5
    assert parse_lilypond_duration("16") == 0.25
    
    # Dotted durations
    assert parse_lilypond_duration("4.") == 1.5
    assert parse_lilypond_duration("4..") == 1.75
    assert parse_lilypond_duration("8.") == 0.75
    
    # Multipliers
    assert parse_lilypond_duration("8*2/3") == pytest.approx(1.0 / 3.0)
    assert parse_lilypond_duration("4*2") == 2.0
    assert parse_lilypond_duration("4*3/2") == 1.5
    
    # Defaults and invalid strings
    assert parse_lilypond_duration("") == 1.0
    assert parse_lilypond_duration("invalid") == 1.0


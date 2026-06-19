import io
import struct
from src.riffwriter import Chunk

def build_dynamic_shdr_chunk(all_samples_flat: list) -> Chunk:
    """
    Generates a structurally flawless shdr chunk driven entirely by dynamic payload data.
    """
    shdr_data = io.BytesIO()
    
    for s in all_samples_flat:
        wave_type = s.get('wave_type', 'sine')
        note_num = s.get('note_num', 60)
        
        # FIX: Generate pristine dynamic naming labels tracking your exact asset type strings
        name_string = f"{wave_type}_note_{note_num}".encode('ascii').ljust(20, b'\x00')
        
        start = s.get('start', 0)
        end = s.get('end', 0)
        rate = s.get('rate', 44100)
        pitch = s.get('pitch', 60) # Tracks note values accurately or locks to 60 if center mapped
        
        sample_length = end - start
        
        # Set loop markers relative to the raw sample memory blocks
        start_loop = start
        end_loop = start + sample_length - 1
        
        # Piper TTS uses a 22050Hz engine. Let's pull the rate property from the source map 
        # to ensure speech playback speed stays perfectly synchronized
        rate = s.get('rate', 22050)

        # Write standard 46-byte SoundFont sample header layout block row
        shdr_data.write(struct.pack(
            '<20sIIIIiBBHH', 
            name_string, 
            start, 
            end, 
            start_loop, 
            end_loop, 
            rate, 
            pitch, 
            0, 0, 1
        ))
        
    # Write mandatory final EOS terminal record chunk block descriptor
    shdr_data.write(struct.pack('<20sIIIIiBBHH', b'EOS', 0, 0, 0, 0, 0, 0, 0, 0, 0))
    
    shdr_bytes = shdr_data.getvalue()
    return Chunk(b'shdr', len(shdr_bytes), shdr_bytes)

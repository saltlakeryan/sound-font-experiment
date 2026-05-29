import sys
import os
import struct
# Import your specific local file
from riff import Riff

def int4cc_to_str(val):
    """Converts a little-endian 4CC integer back into a readable string."""
    try:
        return struct.pack("<I", val).decode('ascii', errors='ignore')
    except Exception:
        return "????"

def parse_subchunks(subchunks_list, depth=1):
    """Recursively traces individual sub-chunk objects."""
    indent = "  " * depth
    for idx, wrapper in enumerate(subchunks_list):
        # Obtain the readable 4-character ID (FourCC string)
        try:
            chunk_id = wrapper.chunk_id_readable
        except Exception:
            chunk_id = "????"
            
        # Size of the chunk payload
        chunk_size = wrapper.chunk.len
        print(f"{indent}[{idx}] ID: {chunk_id:<4} | Size: {chunk_size:,} bytes")
        
        # If the chunk is a 'LIST', it contains its own inner collection
        if hasattr(wrapper, 'chunk_data') and wrapper.chunk_data:
            data_content = wrapper.chunk_data
            if hasattr(data_content, 'form_type_readable'):
                print(f"{indent}    ↳ Form Type: {data_content.form_type_readable}")
            if hasattr(data_content, 'subchunks') and data_content.subchunks:
                parse_subchunks(data_content.subchunks, depth + 2)

def print_riff_summary(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    # Open and initialize the file stream
    target = Riff.from_file(file_path)
    
    print(f"RIFF File Summary: {file_path}")
    print("-" * 50)
    
    # Check if this base file container is valid RIFF
    if target.is_riff_chunk:
        # Convert the integer form_type (e.g., sfbk) into a string safely
        root_format = int4cc_to_str(target.parent_chunk_data.form_type)
        print(f"Root Container: [RIFF] | Format: {root_format}")
        
        # Pull top-level list of chunk layers
        if target.subchunks:
            print("\nFound Top-Level Subchunks:")
            parse_subchunks(target.subchunks, depth=1)
    else:
        print("Warning: The target file does not begin with a valid RIFF magic header.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 riffsummary.py <path_to_file>")
        sys.exit(1)
        
    print_riff_summary(sys.argv[1])

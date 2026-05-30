from dataclasses import dataclass
from typing import List, Union
import struct

# Constants
U32_MAX = 4294967295

@dataclass
class Chunk:
    id: bytes          # 4 bytes (e.g., b'data')
    chunk_size: int    # 32-bit integer
    data: bytes        # Raw payload bytes

@dataclass
class ListEntry:
    fourcc: bytes      # 4 bytes (e.g., b'LIST')
    list_type: bytes   # 4 bytes (e.g., b'WAVE')
    children: List[Union['Chunk', 'ListEntry']]

    def bytes_len(self) -> int:
        """Calculates total size including headers, matching Rust's bytes_len()"""
        # 4 bytes for fourcc + 4 bytes for size + 4 bytes for list_type = 12 bytes
        total = 12 
        for child in self.children:
            if isinstance(child, Chunk):
                total += 8 + len(child.data)
            elif isinstance(child, ListEntry):
                total += child.bytes_len()
        return total

def write_entry(entry: Union[Chunk, ListEntry], writer) -> int:
    """
    Writes a Chunk or ListEntry to a binary file/stream.
    Matches the Rust 'write' method logic.
    """
    if isinstance(entry, Chunk):
        if len(entry.data) > U32_MAX:
            raise ValueError("Data too big")
            
        # Write 4-byte ID
        writer.write(entry.id)
        # Write 4-byte chunk size as little-endian unsigned int (<I)
        writer.write(struct.pack('<I', entry.chunk_size))
        # Write data payload
        writer.write(entry.data)
        
        return 8 + len(entry.data)

    elif isinstance(entry, ListEntry):
        # Write 4-byte container ID (e.g., b'LIST')
        writer.write(entry.fourcc)
        
        # Calculate sub-chunk length minus header
        length = entry.bytes_len() - 8
        writer.write(struct.pack('<I', length))
        
        # Write 4-byte list type (e.g., b'WAVE')
        writer.write(entry.list_type)
        
        # Recursively write all children
        for child in entry.children:
            write_entry(child, writer)
            
        return 8 + length
        
    else:
        raise TypeError("Unknown entry type")

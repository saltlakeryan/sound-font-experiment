from dataclasses import dataclass
from typing import List, Union
import struct

# Constants
U32_MAX = 4294967295

@dataclass
class Chunk:
    id: bytes          # 4 bytes (e.g., b'data')
    chunk_size: int    # 32-bit integer (size of payload ONLY)
    data: bytes        # Raw payload bytes

@dataclass
class ListEntry:
    fourcc: bytes      # 4 bytes (e.g., b'LIST' or b'RIFF')
    list_type: bytes   # 4 bytes (e.g., b'sfbk' or b'pdta')
    children: List[Union['Chunk', 'ListEntry']]

    def bytes_len(self) -> int:
        """
        Calculates total physical size in bytes that will be written to disk.
        Includes headers, payloads, and mandatory word-alignment padding.
        """
        # 4 bytes for fourcc + 4 bytes for size + 4 bytes for list_type = 12 bytes
        total = 12
        for child in self.children:
            if isinstance(child, Chunk):
                # 8 bytes header + raw data length
                child_total = 8 + len(child.data)
                # RIFF padding: if data length is odd, 1 pad byte is added on disk
                if len(child.data) % 2 != 0:
                    child_total += 1
                total += child_total
            elif isinstance(child, ListEntry):
                child_total = child.bytes_len()
                # RIFF padding: if a sub-list's total physical footprint is odd, 1 pad byte is added
                if child_total % 2 != 0:
                    child_total += 1
                total += child_total
        return total

def write_entry(entry: Union[Chunk, ListEntry], writer) -> int:
    """
    Writes a Chunk or ListEntry to a binary file/stream with strict RIFF compliance.
    Includes mandatory modulo-2 padding for odd-sized payloads.
    """
    if isinstance(entry, Chunk):
        if len(entry.data) > U32_MAX:
            raise ValueError("Data too big")
        
        # 1. Write 4-byte ID
        writer.write(entry.id)
        
        # 2. Write 4-byte chunk size header (payload size ONLY, excluding pad byte)
        writer.write(struct.pack('<I', entry.chunk_size))
        
        # 3. Write raw data payload
        writer.write(entry.data)
        bytes_written = 8 + len(entry.data)
        
        # 4. MANDATORY RIFF WORD ALIGNMENT: 
        # Write an extra null byte if the payload data size is odd.
        if len(entry.data) % 2 != 0:
            writer.write(b'\x00')
            bytes_written += 1
            
        return bytes_written

    elif isinstance(entry, ListEntry):
        # 1. Write 4-byte container ID (e.g., b'LIST' or b'RIFF')
        writer.write(entry.fourcc)
        
        # 2. Calculate child payload content size (total list size minus its own 8-byte header)
        payload_size = entry.bytes_len() - 8
        writer.write(struct.pack('<I', payload_size))
        
        # 3. Write 4-byte list type subtype descriptor
        writer.write(entry.list_type)
        
        bytes_written = 12
        
        # 4. Recursively write all children
        for child in entry.children:
            bytes_written += write_entry(child, writer)
            
        return bytes_written
    else:
        raise TypeError("Unknown entry type")

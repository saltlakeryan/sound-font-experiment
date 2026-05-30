import subprocess
import os
import re
import sys
import argparse

def parse_offset(offset_str: str) -> int:
    """Converts hex (0x...) or decimal string to an integer offset."""
    if offset_str.lower().startswith("0x"):
        return int(offset_str, 16)
    return int(offset_str)

def to_ascii_sidebar(data: bytes) -> str:
    """Converts bytes to a readable ASCII sidebar string, replacing non-printables with dots."""
    return "".join(chr(b) if 32 <= b <= 126 else "." for b in data)

def get_reference_bytes(ref_path: str, offset_int: int, byte_count: int) -> bytes:
    """Runs xxd on the reference file at a specific integer offset."""
    if not os.path.exists(ref_path):
        raise FileNotFoundError(f"Missing reference file: {ref_path}")
        
    hex_str = f"0x{offset_int:08x}"
    cmd = ["xxd", "-s", hex_str, "-l", str(byte_count), "-c", str(byte_count), "-g", "1", ref_path]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    match = re.search(r'^[0-9a-fA-F]+:\s+([0-9a-fA-F ]{2,})', result.stdout.strip())
    if not match:
        raise ValueError(f"Could not parse xxd output: {result.stdout}")
        
    hex_payload = match.group(1).replace(" ", "")
    return bytes.fromhex(hex_payload)

def scan_and_compare(ref_path: str, gen_path: str, target_offset: int, byte_count: int):
    try:
        ref_bytes = get_reference_bytes(ref_path, target_offset, byte_count)
    except Exception as e:
        print(f"Error reading reference: {e}")
        return

    if not os.path.exists(gen_path):
        print(f"Error: Generated file '{gen_path}' not found. Run your builder first!")
        return

    print(f"=== SoundFont Alignment Test ===")
    print(f"Reference File: {ref_path}")
    print(f"Generated File: {gen_path}")
    print(f"Targeting Reference Offset: 0x{target_offset:08x} ({target_offset} bytes) | Window Size: {byte_count} bytes")
    print(f"Reference Head: {ref_bytes[:8].hex(' ')} ...")
    print("-" * 70)

    scan_range = max(128, byte_count)

    with open(gen_path, "rb") as gen_file:
        gen_file.seek(0, os.SEEK_END)
        max_size = gen_file.tell()
        
        found_match = False
        for shift in range(-scan_range, scan_range, 2):
            test_offset = target_offset + shift
            if test_offset < 0 or test_offset + byte_count > max_size:
                continue
                
            gen_file.seek(test_offset)
            gen_bytes = gen_file.read(byte_count)
            
            matches = sum(1 for b1, b2 in zip(ref_bytes, gen_bytes) if b1 == b2)
            
            if matches >= byte_count - 16 or (gen_bytes.startswith(ref_bytes[:4]) and matches > 8):
                found_match = True
                print(f"\n[DIAL MATCH FOUND] Shift: {shift:+d} bytes | True Offset: 0x{test_offset:08x}")
                print(f"Similarity: {matches}/{byte_count} bytes align perfectly.")
                
                # Format hex payload with spaces
                ref_hex = ref_bytes.hex(' ')
                gen_hex = gen_bytes.hex(' ')
                
                # Generate matching ASCII sidebars
                ref_ascii = to_ascii_sidebar(ref_bytes)
                gen_ascii = to_ascii_sidebar(gen_bytes)
                
                print(f"REF: {ref_hex}  |  {ref_ascii}")
                print(f"GEN: {gen_hex}  |  {gen_ascii}")
                
                diffs = [i for i, (b1, b2) in enumerate(zip(ref_bytes, gen_bytes)) if b1 != b2]
                if diffs:
                    print(f"First structural diff occurs at window byte index: {diffs}")

        if not found_match:
            print(f"No structural alignment found within +/- {scan_range} bytes.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare specific byte windows across SoundFont binaries.")
    parser.add_argument("offset", type=str, help="Target base offset to investigate (e.g., 0x000e8d90 or 953744)")
    parser.add_argument("--ref", type=str, default="reference/two-instruments.sf2", help="Path to reference binary template file")
    parser.add_argument("--gen", type=str, default="output/two-instruments.sf2", help="Path to generated compilation binary file")
    parser.add_argument("--count", type=int, default=64, help="Byte size window footprint dimension to verify")
    
    args = parser.parse_args()
    
    try:
        numeric_offset = parse_offset(args.offset)
        scan_and_compare(args.ref, args.gen, numeric_offset, args.count)
    except ValueError:
        print(f"Error: Invalid offset format '{args.offset}'. Use decimal or hexadecimal (0x...).")
        sys.exit(1)

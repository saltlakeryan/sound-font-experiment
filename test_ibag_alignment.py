import subprocess
import os
import re
import sys
import argparse

# --- Configuration Base Defaults ---
REFERENCE_SF2 = "output/instrument_0b.sf2"  # Path to your known good file
GENERATED_SF2 = "output/instrument_0.sf2"   # Path to your generated file
BYTE_COUNT = 64                            # Window size to compare

def parse_offset(offset_str: str) -> int:
    """Converts hex (0x...) or decimal string to an integer offset."""
    if offset_str.lower().startswith("0x"):
        return int(offset_str, 16)
    return int(offset_str)

def get_reference_bytes(offset_int: int) -> bytes:
    """Runs xxd on the reference file at a specific integer offset."""
    if not os.path.exists(REFERENCE_SF2):
        raise FileNotFoundError(f"Missing reference file: {REFERENCE_SF2}")
        
    # Format offset back to clean hex string for xxd
    hex_str = f"0x{offset_int:08x}"
    cmd = ["xxd", "-s", hex_str, "-l", str(BYTE_COUNT), "-c", str(BYTE_COUNT), "-g", "1", REFERENCE_SF2]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    # Parse xxd line format
    match = re.search(r'^[0-9a-fA-F]+:\s+([0-9a-fA-F ]{2,})', result.stdout.strip())
    if not match:
        raise ValueError(f"Could not parse xxd output: {result.stdout}")
        
    hex_payload = match.group(1).replace(" ", "")
    return bytes.fromhex(hex_payload)

def scan_and_compare(target_offset: int):
    try:
        ref_bytes = get_reference_bytes(target_offset)
    except Exception as e:
        print(f"Error reading reference: {e}")
        return

    if not os.path.exists(GENERATED_SF2):
        print(f"Error: Generated file '{GENERATED_SF2}' not found. Run your builder first!")
        return

    print(f"=== RIFF Alignment Test ===")
    print(f"Targeting Reference Offset: 0x{target_offset:08x} ({target_offset} bytes)")
    print(f"Reference Head: {ref_bytes[:8].hex(' ')} ...")
    print("-" * 60)

    with open(GENERATED_SF2, "rb") as gen_file:
        gen_file.seek(0, os.SEEK_END)
        max_size = gen_file.tell()
        
        found_match = False
        for shift in range(-128, 128, 2):  # Sweep window
            test_offset = target_offset + shift
            if test_offset < 0 or test_offset + BYTE_COUNT > max_size:
                continue
                
            gen_file.seek(test_offset)
            gen_bytes = gen_file.read(BYTE_COUNT)
            
            matches = sum(1 for b1, b2 in zip(ref_bytes, gen_bytes) if b1 == b2)
            
            if matches >= BYTE_COUNT - 8 or (gen_bytes.startswith(ref_bytes[:4]) and matches > 10):
                found_match = True
                print(f"\n[DIAL MATCH FOUND] Shift: {shift:+d} bytes | True Offset: 0x{test_offset:08x}")
                print(f"Similarity: {matches}/{BYTE_COUNT} bytes align perfectly.")
                print(f"REF: {ref_bytes.hex(' ')}")
                print(f"GEN: {gen_bytes.hex(' ')}")
                
                diffs = [i for i, (b1, b2) in enumerate(zip(ref_bytes, gen_bytes)) if b1 != b2]
                if diffs:
                    print(f"First structural diff occurs at window byte index: {diffs}")

        if not found_match:
            print("No structural alignment found within +/- 128 bytes.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare specific byte windows between SF2 binaries.")
    parser.add_argument(
        "offset", 
        type=str, 
        help="The target base offset to investigate (e.g., 0x000e8d90 or 953744)"
    )
    
    args = parser.parse_args()
    
    try:
        numeric_offset = parse_offset(args.offset)
        scan_and_compare(numeric_offset)
    except ValueError:
        print(f"Error: Invalid offset format '{args.offset}'. Use decimal or hexadecimal (0x...).")
        sys.exit(1)

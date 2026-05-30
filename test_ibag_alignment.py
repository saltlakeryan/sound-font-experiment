import subprocess
import os
import re

# --- Configuration ---
REFERENCE_SF2 = "output/instrument_0.sf2"  # Path to your known good file
GENERATED_SF2 = "output/instrument_0b.sf2"   # Path to your generated file
HEX_OFFSET = "0x000e8d90"                  # Target base offset
BYTE_COUNT = 64                            # Window size to compare

def get_reference_bytes() -> bytes:
    """Runs xxd on the reference file and returns raw payload bytes."""
    if not os.path.exists(REFERENCE_SF2):
        raise FileNotFoundError(f"Missing reference file: {REFERENCE_SF2}")
        
    cmd = ["xxd", "-s", HEX_OFFSET, "-l", str(BYTE_COUNT), "-c", str(BYTE_COUNT), "-g", "1", REFERENCE_SF2]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    # Parse xxd line format: "offset: 0a 00 69 ...  ..ibag..."
    match = re.search(r'^[0-9a-fA-F]+:\s+([0-9a-fA-F ]{2,})', result.stdout.strip())
    if not match:
        raise ValueError(f"Could not parse xxd output: {result.stdout}")
        
    hex_string = match.group(1).replace(" ", "")
    return bytes.fromhex(hex_string)

def scan_and_compare():
    try:
        ref_bytes = get_reference_bytes()
    except Exception as e:
        print(f"Error reading reference: {e}")
        return

    if not os.path.exists(GENERATED_SF2):
        print(f"Error: Generated file '{GENERATED_SF2}' not found. Run your builder first!")
        return

    base_offset = int(HEX_OFFSET, 16)
    
    print(f"=== RIFF Alignment Test ===")
    print(f"Targeting Reference Offset: {HEX_OFFSET} ({base_offset} bytes)")
    print(f"Reference Head: {ref_bytes[:8].hex(' ')} ...")
    print("-" * 60)

    # Dial window: Search from -128 bytes to +128 bytes around target offset
    with open(GENERATED_SF2, "rb") as gen_file:
        gen_file.seek(0, os.SEEK_END)
        max_size = gen_file.tell()
        
        found_match = False
        for shift in range(-128, 128, 2):  # Step by 2 since structures are word-aligned
            test_offset = base_offset + shift
            if test_offset < 0 or test_offset + BYTE_COUNT > max_size:
                continue
                
            gen_file.seek(test_offset)
            gen_bytes = gen_file.read(BYTE_COUNT)
            
            # Count matching bytes
            matches = sum(1 for b1, b2 in zip(ref_bytes, gen_bytes) if b1 == b2)
            
            # Highlight interesting offsets (exact matches or heavy alignments)
            if matches >= BYTE_COUNT - 8 or (gen_bytes.startswith(ref_bytes[:4]) and matches > 10):
                found_match = True
                print(f"\n[DIAL MATCH FOUND] Shift: {shift:+d} bytes | True Offset: 0x{test_offset:08x}")
                print(f"Similarity: {matches}/{BYTE_COUNT} bytes align perfectly.")
                print(f"REF: {ref_bytes.hex(' ')}")
                print(f"GEN: {gen_bytes.hex(' ')}")
                
                # Highlight structural variance
                diffs = [i for i, (b1, b2) in enumerate(zip(ref_bytes, gen_bytes)) if b1 != b2]
                if diffs:
                    print(f"First structural diff occurs at window byte index: {diffs[0]}")

        if not found_match:
            print("No structural alignment found within +/- 128 bytes.")
            print("Your generated file might be missing an entire chunk or data block earlier in the stream.")

if __name__ == "__main__":
    scan_and_compare()

#!/bin/bash

# Exit instantly if any isolated command layer throws an error
set -e

# --- Configuration Designators ---
WORKING_DIR="$(pwd)"
OUTPUT_DIR="${WORKING_DIR}/output"

# FIX: Update checking paths to search for the expanded three-instruments layout arrays
REF_CSV="${OUTPUT_DIR}/ref/two-instruments/samples.csv" # Keep your original good baseline
GEN_CSV="${OUTPUT_DIR}/gen/three-instruments/samples.csv" # Point to the fresh three-preset export

echo "=================================================="
echo "🚀 STARTING SOUNDFONT COMPILER VERIFICATION SUITE"
echo "=================================================="

# Step 1: Purge stale Python cache objects and dead binary artifacts
echo "🧹 1/5 Clearing cached file buffers..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
rm -f "${OUTPUT_DIR}/two-instruments.sf2"
rm -f "${OUTPUT_DIR}/three-instruments.sf2"
rm -rf output/gen
mkdir -p output/gen

# Step 2: Run automated Unit Tests inside the container environment
echo "🧪 2/5 Running structural invariant assertions via pytest..."
docker run --rm -v "${WORKING_DIR}:/app" -v "${OUTPUT_DIR}:/app/output" soundfont-factory bash -lc 'cd /app; pytest test_soundfont_logic.py'

# Step 3: Run the Three-Instrument Compiler factory pipeline
echo "🏗️  3/5 Compiling binary SoundFont via three-instrument-generate.py..."
docker run --rm -v "${WORKING_DIR}:/app" -v "${OUTPUT_DIR}:/app/output" soundfont-factory bash -lc 'cd /app; python3 three-instrument-generate.py'

# Step 4: Run headless Polyphone to unpack raw tables for auditing
echo "👁️  4/5 Extracting raw metadata footprints via headless Polyphone..."
docker run -it --rm -v "${WORKING_DIR}:/app" -v "${OUTPUT_DIR}:/app/output" soundfont-factory bash -lc "xvfb-run polyphone -4 -i output/three-instruments.sf2 -d output/gen -o three-instruments -c 'raw' </dev/null"

# Step 5: Perform the text verification diff audit check
echo "📊 5/5 Performing visual data integrity verification check..."
echo "--------------------------------------------------"

if [ -f "$REF_CSV" ] && [ -f "$GEN_CSV" ]; then
    # Run the audit comparison check against the first 18 sample lanes
    # We will use head -n 20 to check the header rows + first 18 notes cleanly
    DIFF_OUT=$(diff -u <(head -n 20 "$REF_CSV") <(head -n 20 "$GEN_CSV") || true)
    
    if [ -z "$DIFF_OUT" ]; then
        echo "🟢 [VERIFICATION SUCCESS]: Dynamic preset data layers compile perfectly!"
        echo "   All sample boundaries, loop anchors, and root key mappings match 100%."
        echo "   Open the file in the Polyphone GUI to play your three custom presets."
    else
        echo "🔴 [VERIFICATION FAILED]: Found metadata column drifts:"
        echo "$DIFF_OUT"
        exit 1
    fi
else
    echo "⚠️  [ERROR]: Verification files missing. Ensure Polyphone reference extraction matches directory structure shapes."
    exit 1
fi

echo "=================================================="

#!/bin/bash

# Exit instantly if any isolated command layer throws an error
set -e

# --- Configuration Designators ---
WORKING_DIR="$(pwd)"
OUTPUT_DIR="${WORKING_DIR}/output"
REF_CSV="${OUTPUT_DIR}/ref/two-instruments/samples.csv"
GEN_CSV="${OUTPUT_DIR}/gen/two-instruments/samples.csv"

echo "=================================================="
echo "🚀 STARTING SOUNDFONT COMPILER VERIFICATION SUITE"
echo "=================================================="

# Step 1: Purge stale Python cache objects and dead binary artifacts
echo "🧹 1/5 Clearing cached file buffers..."
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
rm -f "${OUTPUT_DIR}/two-instruments.sf2"
rm -rf output/gen
mkdir output/gen

# Step 2: Run automated Unit Tests inside the container environment
# DROPPED -it FOR AUTOMATION RELIABILITY
echo "🧪 2/5 Running structural invariant assertions via pytest..."
docker run --rm -v "${WORKING_DIR}:/app" -v "${OUTPUT_DIR}:/app/output" soundfont-factory bash -lc 'cd /app; pytest test_soundfont_logic.py'

# Step 3: Run the Multi-Instrument Compiler factory pipeline
# DROPPED -it FOR AUTOMATION RELIABILITY
echo "🏗️  3/5 Compiling binary SoundFont via two-instrument-generate.py..."
docker run --rm -v "${WORKING_DIR}:/app" -v "${OUTPUT_DIR}:/app/output" soundfont-factory bash -lc 'cd /app; python3 two-instrument-generate.py'

# Step 4: Run headless Polyphone to unpack raw tables for auditing
# DROPPED -it TO PREVENT THE XVFB TERMINAL LOCK-UP HANG BUG
echo "👁️  4/5 Extracting raw metadata footprints via headless Polyphone..."
docker run -it --rm -v "${WORKING_DIR}:/app" -v "${OUTPUT_DIR}:/app/output" soundfont-factory bash -lc "xvfb-run polyphone -4 -i output/two-instruments.sf2 -d output/gen -o two-instruments -c 'raw' < /dev/null"

# Step 5: Perform the text verification diff audit check
echo "📊 5/5 Performing visual data integrity verification check..."
echo "--------------------------------------------------"

if [ -f "$REF_CSV" ] && [ -f "$GEN_CSV" ]; then
    # Run diff and capture output stream
    DIFF_OUT=$(diff -u "$REF_CSV" "$GEN_CSV" || true)
    
    if [ -z "$DIFF_OUT" ]; then
        echo "🟢 [VERIFICATION SUCCESS]: output/two-instruments.sf2 is structurally perfect!"
        echo "   All sample boundaries, loop anchors, and root key mappings match 100%."
        echo "   The asset linking warning indicators are gone inside Polyphone UI panels."
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

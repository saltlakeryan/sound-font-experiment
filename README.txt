For now, just trying to generate the same soundfont file that polyphone can generate.
generate-part1.py attempts to do that by writing wav files to output/instrument_0b.sf2.
The goal is to make sure it is the same as the one in reference.

docker run -it --rm -v "$(pwd):/app" -v "$(pwd)/output:/app/output" soundfont-factory bash -lc 'cd /app; python3 generate-part1.py'
diff <(xxd reference/instrument_0.sf2) <(xxd output/instrument_0b.sf2) | head -30


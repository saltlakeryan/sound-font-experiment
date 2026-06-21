SOUNDFONT FACTORY PROJECT DOCUMENTATION & OPERATIONS MANUAL
===========================


**PRODUCT OVERVIEW**
--------------------

This is a work-in-progress python project that I used to explore programmatic generation of SoundFont (.sf2) files from scratch. There weren't a lot of other python-based projects for doing so--though there are good options for reading them. sf2cute seems like a good option in C++ world.  There are good docs out there for the format though. With the help of coding agents, I was able to cobble together some tools for generating soundfonts. I added a flask front-end for generating a soundfont based on spoken words by a TTS (text-to-speech) engine.  


**WEB INTERFACE & INTEGRATED PIPELINES**
----------------------------------------

A user-friendly web interface integrates the key compilation and rendering steps into a cohesive dashboard:

*   **Interactive Event Table:** Input sequences specifying the physical foot action (`Left Foot`, `Right Foot`, or `Rest`), standard musical note lengths (Whole to Sixteenth), lyric words, and staff comments.
*   **Dual-Pipeline Synthesis:**
    1.  *LilyPond Score Compiler:* Generates a PDF sheet music layout with a custom 2-instrument percussion voice, attaching lyrics below the staff and comments above.
    2.  *Vocal Synthesizer:* Synthesizes the unique lyric words using the local Piper neural TTS engine, packs them into a custom SoundFont bank, programs a timed MIDI track with instrument switches, and renders a master `.wav` file via `fluidsynth`.
*   **Asset Download & Preview Hub:** Preview the generated sheet music PDF and play the finished audio master directly in the browser, with direct links to download all generated formats (`.pdf`, `.wav`, `.sf2`, `.mid`, `.midi`).

**Running the Web Dashboard:**

Start the Flask server:
```bash
python3 web_server.py

or

docker run -v `pwd`:/app --rm -it -p 7899:8000 soundfont-factory python3 web_server.py
```
Then navigate to `http://localhost:8000` in your web browser.


**QUICK START GUIDE**
---------------------

Prerequisites:

*   Docker installed on your host machine.
*   A local sound font analyzer tool (like Polyphone) to audit files.
    

Build the Toolchain Image:

Compile the core Ubuntu-based image environment. This step downloads and
permanently caches the offline Piper neural TTS models into your image
layers to eliminate future runtime network lag.

Command:

```
docker build -t soundfont-factory -f docker/Dockerfile .
```

Generate a Talking Vocal Instrument:

To compile a SoundFont where a completely different English word is mapped
to each physical keyboard zone, trigger the native text-to-speech script.

Command:
```
docker run --rm -v "$(pwd):/app" -v "$(pwd)/output:/app/output" soundfont-factory bash -lc 'python3 talking-instrument-generate.py'
```

Output Artifact: output/vocal-talking-instrument.sf2 (Sample Rate: 22050 Hz)

Vocal Map Layout: Note 48 speaks "alpha", Note 52 speaks "bravo", Note 79

speaks "india".

Generate a Three-Instrument Synthetic Bank:

To synthesize a multi-preset wavetable bank containing 3 completely unique
instrument channels (Sine, Sawtooth, and Square) back-to-back across 9
target pitches, run:

Command:
```
docker run --rm -v "$(pwd):/app" -v "$(pwd)/output:/app/output" soundfont-factory bash -lc 'python3 three-instrument-generate.py'
```

Output Artifact: output/three-instruments.sf2 (Sample Rate: 44100 Hz)

Run Automated Invariant Validations:

To run unit test assertions protecting structural indices and chunk width

dimensions against regressions, execute:

Command:

```
docker run --rm -v "$(pwd):/app" -v "$(pwd)/output:/app/output" soundfont-factory bash -lc 'cd /app; pytest test\_soundfont\_logic.py'
```

**THE VERIFICATION & QUALITY ASSURANCE SUITE**
----------------------------------------------

The project includes an advanced testing pipeline script (verify\_pipeline.sh)
that completely automates byte-level structural validation.

Execution:

```
chmod +x verify\_pipeline.sh
./verify\_pipeline.sh
```

What verify\_pipeline.sh Completes Automatically:

*   Purges pycaches and old file artifacts to stop ghost caching bugs.
    
*   Runs the pytest testing grid to confirm internal compiler rules.
    
*   Compiles a completely fresh SoundFont binary stream.
    
*   Triggers headless Polyphone (xvfb-run polyphone -c 'raw') inside thecontainer layer to unpack metadata chunks straight to .csv sheets.
    
*   Runs a live diff comparison audit contrasting your generated table layoutwith a known-good reference template, confirming a perfect match.
    

**ENGINEERING PITFALLS ENCOUNTERED & SOLVED**
---------------------------------------------

Building a binary-perfect RIFF compiler from scratch revealed several quirks
in the SoundFont 2 format specification and host software parsers:

The Mono Audio Length Off-by-One Underflow Bug:
The specification requires each sample record row's absolute ending location
(dwEnd) to track the exact sample boundary array limit minus 1 word. Omitting
this caused negative integer calculation underflows (-93), wrapping values
inside the 32-bit unsigned uint32\_t register up to 4294967249 and corrupting
lengths. Resetting start = 0 and mapping end = length - 1 programmatically
solved this.

The Dual Bag-per-Preset Rule:
Host editors like Polyphone enforce that every active preset record inside
the phdr list must map to exactly two sequential structural zones (bags)
inside pbag—an initial global parameter modifier block, followed by the active
instrument linking block. Shorting this by writing only 1 bag caused
downstream tables to shift out of alignment.
The wInstModNdx Zero Constraint Blocker:

We originally assumed the modulator link indices inside instrument bags
(ibag) stepped continuously like generator indices. However, if an instrument
maps 0 active modulators, every single zone row must link strictly to index 0.
Writing incrementing pointers there caused an immediate "invalid imod index"
parser crash.

Docker PyCache & String Redirection Hangs:

When passing long headless strings to xvfb-run polyphone, standard input

(stdin) channels inside Docker would remain open, hanging the script loop

forever. Appending `</dev/null`

signaled an immediate end-of-stream block, allowing headless automated

conversion to run smoothly.

**FUTURE IMPROVEMENTS & SCALABILITY**
-------------------------------------

Dynamic Volume ADSR Envelopes:

Implement programmatic generator insertions inside igen\_builder.py to allow
users to pass custom attack, decay, sustain, and release time values (Gen 34
to Gen 38) straight from their data payloads to customize instrument
performance characters.

Automatic Multi-Channel Stereo Interleaving:

Upgrade pipeline\_compiler.py to auto-detect multi-channel WAV files and
automatically dual-pack Left and Right raw audio samples sequentially into the
smpl data loop while applying the mandatory stereo flags (sfSampleType = 2
and 4) to the shdr table rows.

Real-time WAV Meta Parsing:

Integrate a native header reader inside pipeline\_compiler.py to parse the
44-byte WAV descriptor blocks automatically, completely removing the need to
pass fixed fallback sample rate values manually via terminal arguments.

**FUTURE TESTING STRATEGIES**
-----------------------------

Fuzz Testing Audio Data Alignment:

Introduce random-length mock PCM audio blocks inside test\_soundfont\_logic.py
to confirm that your sdta\_builder.py and structural pointer offsets cleanly
handle odd byte counts by enforcing strict word alignment padding.
Automated Binary Regression Sweeping:

Expand the custom visual alignment script (test\_alignment.py) to run
full-file hash checks against a master catalog of reference models, flagging
any hidden index shifting instantly whenever layout code changes are saved.

Headless Audio Render Assertions:

Integrate a headless synthesizer engine (like fluidsynth) directly into the
validation bash script to render a standard MIDI score using your generated
SoundFont, and assert that the resulting audio waveforms contain active
audio power instead of blank zeros.

**REPOSITORY FILE MAPPING MATRIX**
----------------------------------

*   soundfont\_builder2.py:The root compilation orchestrator organizing file chunks.
    
*   riffwriter.py:Low-level chunk and list-entry byte serialization utility.
    
*   pdta\_builder.py:Packs global layout matrices (phdr, pbag, inst).
    
*   preset\_zone\_builder.py:Computes dynamic preset assignments programmatically.
    
*   ibag\_builder.py / igen\_builder.py / shdr\_builder.py:Generates lower sub-chunk parameters.
    
*   pipeline\_compiler.py:Flattening loops handling multi-preset asset serialization.
    
*   test\_alignment.py:High-density visual binary analysis diagnostic tool with stacked hexand ASCII views.
    
*   web_server.py:Flask application serving the web interface and orchestrating LilyPond compiling, Piper TTS synthesis, and FluidSynth rendering.
    
*   static/:Directory housing index.html, index.js, and index.css for the interactive event sequence editor and preview hub.
    
*   TODO.txt:Initial specifications checklist outlining the web editor layout and pipeline expectations.
    

================================================================================

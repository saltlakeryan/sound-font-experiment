import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage

def build_talking_midi(word_list, output_midi_path="output/dance_routine.mid"):
    # Normalize the word list to match lookups cleanly
    word_to_program = {word.lower(): idx for idx, word in enumerate(word_list)}

    # 1. Clean LilyPond text stream into sequential word tokens
    lilypond_text = """
    fall(R) off(R) the(L) log(R) fall(L) off(L) the(R) log(L) 
    stomp off "kick(R)" kickback(R) rock(L) step(L) fall(R) rock(L) 
    kick(R) ball(R) tap(L) fall(L) rock(R) kick(L) ball(L) tap(R) 
    step(R) tap(L) toe(L) heel(L) toe(R) heel(R) LEFT RIGHT LEFT
    """
    
    # Clean tokens: remove (R), (L), and double quotes
    raw_tokens = lilypond_text.replace('"', '').split()
    cleaned_lyrics = []
    for token in raw_tokens:
        clean = token.split('(')[0].lower()
        if clean in word_to_program:
            cleaned_lyrics.append(clean)
        else:
            # Fallback if a lyric variant isn't in your exact list
            cleaned_lyrics.append(word_list[0])

    # 2. Extract note sequence from your \melody block (ignoring structural breaks/marks)
    # The melody maps directly to 31 notes after counting the initial 7 quarter-note rests.
    # We define the pitch (MIDI note numbers) and durations (in ticks, assuming 480 ticks/quarter note)
    
    # Ticks mappings based on Lilypond syntax:
    # 4 = 480 ticks (quarter)
    # 2 = 960 ticks (half)
    # 8 = 240 ticks (eighth)
    
    QN = 480  # Quarter Note
    HN = 960  # Half Note
    EN = 240  # Eighth Note

    # Sequence of notes extracted chronologically from your LilyPond source:
    note_definitions = [
        # M2: final beat c4
        (60, QN), 
        # M3: c4 c c c
        (60, QN), (60, QN), (60, QN), (60, QN), 
        # M4: d4 d d d8 d8
        (62, QN), (62, QN), (62, QN), (62, EN), (62, EN), 
        # M5 & M6: c2 c | c c
        (60, HN), (60, HN), (60, HN), (60, HN), 
        # M7: c4 c8 c4 c8 c4
        (60, QN), (60, EN), (60, QN), (60, EN), (60, QN), 
        # M8: c4 c8 c4 c8 c4
        (60, QN), (60, EN), (60, QN), (60, EN), (60, QN), 
        # M9: c4 c4 c4 c8 c4
        (60, QN), (60, QN), (60, QN), (60, EN), (60, QN), 
        # M10: c8 c4 c c
        (60, EN), (60, QN), (60, QN), (60, QN)
    ]

    # Initialize Midi Framework Chunks
    mid = MidiFile()
    mid.ticks_per_beat = 480
    track = MidiTrack()
    mid.tracks.append(track)

    # Track Setup Metadata
    track.append(MetaMessage('track_name', name='Dance Melody', time=0))
    track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(120), time=0))

    # Account for the 7 initial Rests (Measure 1 and 3 beats of Measure 2)
    # 7 rests * 480 ticks = 3360 ticks before the first sound occurs
    initial_delay = 7 * QN

    print(f"🎵 Packing {len(note_definitions)} notes against {len(cleaned_lyrics)} text tags...")

    for idx, (pitch, duration) in enumerate(note_definitions):
        # Prevent indexing mismatch errors
        lyric_word = cleaned_lyrics[idx] if idx < len(cleaned_lyrics) else "step"
        program_target = word_to_program[lyric_word]

        # First message handles the initial rest offset delay
        current_time_delay = initial_delay if idx == 0 else 0

        # A. Trigger the program patch switch to the target word instrument index
        track.append(Message('program_change', program=program_target, time=current_time_delay))
        
        # B. Note On Event (Instantly triggered after patch switch)
        track.append(Message('note_on', note=pitch, velocity=100, time=0))
        
        # C. Note Off Event (Sustained for the length of the musical note)
        track.append(Message('note_off', note=pitch, velocity=64, time=duration))

    track.append(MetaMessage('end_of_track', time=0))
    mid.save(output_midi_path)
    print(f"✨ Success! Your lyrics-switching MIDI file is exported to: {output_midi_path}")

# Execute using your updated internal word list array configurations
word_list = [
    "fall", "off", "the", "log", "stomp", "kick", "kickback", "rock", 
    "step", "ball", "tap", "toe", "heel", "left", "right", "five", "six", "seven", "eight"
]

if __name__ == "__main__":
    build_talking_midi(word_list)

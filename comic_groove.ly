\version "2.24.0"

% 1. Register the 9 custom pitches into the global dictionary
#(define my-extended-pitches '(
  (bang . bang) (pow . pow) (thunder . thunder) (zap . zap) (boom . boom)
  (chop . chop) (crack . crack) (swish . swish) (crunch . crunch)
))
#(set! drumPitchNames (append my-extended-pitches drumPitchNames))

% 2. Define the visual layout table
#(define my-comic-kit '(
  (boom          default       #f          -5)
  (thunder       default       tenuto      -3)
  (crunch        triangle      #f          -1)
  (chop          slash         #f           1)
  (crack         default       accent       3)
  (bang          triangle      #f           5)
  (pow           diamond       accent       7)
  (zap           cross         #f           7) 
  (swish         cross         #f           9)
))

% 3. Performance Data - Upper Voice (Hands / High FX)
drumHands = \drummode {
  \stemUp
  \numericTimeSignature
  \time 4/4
  
  zap8 chop zap chop zap chop <zap crack>4 |
  zap8 <zap bang> chop zap8 swish4 <zap crack>8 zap |
  pow4 chop8 crack pow8 pow <chop crack>4 |
  zap16 pow zap pow   chop crunch chop crunch   crack8 <bang crack> swish4 |
}

% 4. Performance Data - Lower Voice (Feet / Deep FX)
drumFeet = \drummode {
  \stemDown
  
  boom4 thunder boom8 boom thunder4 |
  boom8 boom thunder4 boom thunder |
  boom4 r8 thunder boom4 thunder |
  boom4 thunder boom boom |
}

% 5. Render Layout and Configure Table Map
\score {
  \new DrumStaff \with {
    instrumentName = #"FX Kit"
    shortInstrumentName = #"FX"
    drumStyleTable = #(alist->hash-table my-comic-kit)
  }
  <<
    \new DrumVoice { \voiceOne \drumHands }
    \new DrumVoice { \voiceTwo \drumFeet }
  >>
  \layout {
    indent = 1.5\cm
  }
  \midi { \tempo 4 = 110 }
}

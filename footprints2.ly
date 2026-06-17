\version "2.24.0"

\header {
  title = "Mary Had a Little Lamb"
  subtitle = "With Custom Images and Labels"
}

% --- Custom Markup Definition ---
% We use \column to stack the image on top of the text.
% \center-align ensures they share the same center axis.
footprintLeft = \markup {
  \center-align \column {
    \image #X #5.0 #"footprints.png"
    \line { "LEFT" }
  }
}

% You can easily make a second one if you have a right foot image/text later
footprintRight = \markup {
  \center-align \column {
    \image #X #5.0 #"footprints.png" % Swap with right-foot image if needed
    \line { "RIGHT" }
  }
}

% --- Chord/Image Track ---
customImages = \chordmode {
  % Applies the Left footprint + "LEFT" text above the first measure
  \once \override ChordNames.ChordName.text = \footprintLeft
  c1 | 
  
  s1 |
  
  % Applies the Right footprint + "RIGHT" text above the third measure
  \once \override ChordNames.ChordName.text = \footprintRight
  g1 | 
  
  c1 |
}

% --- Melody Track ---
melody = \relative c' {
  \clef treble
  \key c \major
  \time 4/4
  
  e4 d c d | e4 e4 e2 |
  d4 d d2 | e4 g4 g2 |
}

% --- Score Layout ---
\score {
  <<
    \new ChordNames { \customImages }
    \new Staff { \melody }
  >>
  \layout {
    \context {
      \ChordNames
      % Increased padding slightly to make room for both the image and the text
      \override VerticalAxisGroup.nonstaff-relatedstaff-spacing.padding = #3
    }
  }
}

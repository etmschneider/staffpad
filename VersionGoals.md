# Versions #

These versions represent incremental and significant goals for the next minor and major releases. This serves as a list of features that must be implemented before each version is tagged.  This should serve as a structure for coding the project, and allows goals to be set for the next release(s).  Completed versions and features should be boldfaced to indicate their completion.

  * **0.0:**
    * **This is the first commit, which is not usable.  It just indicates placement of some basic code structure in SVN.**
  * **0.1:**
    * **Program should run without errors**
    * **A simple classifier should be implemented, recognizing noteheads, vertical lines, and categorizing everything else as "unknown".**
    * **A default "page" should appear on startup, with staves**
    * **Noteheads should be recognized when drawn, and attached to the appropriate staves**
    * **Barlines should be recognized when drawn, and attached to the appropriate staves**
    * **Other Vertical lines should be recognized and attached to single notes when appropriate**
    * **The basic code structure should be cemented**
  * **0.2:**
    * **Ledger lines should be drawn by notes/chords above or below the staff**
    * **Notes can be drawn and added to existing chords**
    * **The stylus eraser should erase objects it passes over.  When passing over a stem, it should just erase the stem, not the attached notes.**
    * **The classifier should be improved**
      * **filled notes should be easier (possible) to draw**
      * **a training option should be added at some level**
    * **Clustered notes in chords are handled correctly**
  * 0.3:
    * **Support for multi-segment gestures implemented**
    * **Basic accidentals recognized and attached to appropriate notes** (not pretty drawings of shapes, though)
    * **Revamped classifier to boost performance**
    * **Special-cased line detection to make classifier more robust**
    * other note modifiers (hat, marcato, **staccato**, accent, and **rhythm dot**) recognized and attached to appropriate notes
  * 0.4:
    * eighth and sixteenth note stems should be recognized when drawn.
    * Support for (basic) clefs
    * initial support for beams (even if it is restrictive)
    * "drag/drop" movement of notes, stems, barlines, and clefs
    * prettier shape drawings

The first major milestone will be version 0.99  This will be a beta release.  At this point, the program is mostly usable, with basic functionality and structure solidified.  The requirements for this version are listed below:

  * 0.99
    * Recognize most standard music objects, as listed below.  Recognition should be fairly accurate and reliable over a wide variety of users.
      * notes (heads, stems, and flags independently)
        * **ledger lines should be drawn with notes**
      * clefs (at least treble & bass)
      * **accidentals (at least flat, sharp, and natural)**
      * Note additions (accents, staccato markings, rhythm dots)
      * slurs, ties
      * barlines - including double barlines and repeats
      * anything unrecognized should still be drawn and saved, so user can make annotations, etc, but marked as unrecognized
    * Association of new drawn markings with existing symbols
      * **apply accidentals to correct note**
      * **apply stems to noteheads**, flags to notes, etc.
      * **apply noteheads to existing stem/notehead for chords** (including the special case of whole note chords)
      * **handle clusters of notes in chords.**
      * apply slurs and ties to existing notes
    * **Ability to erase symbols and markings with the stylus eraser.**
    * Program should zoom and resize correctly, without causing notes to be lost or anything weird to happen
    * Robust - all possible errors should be handled, and bad input should not be able to crash the program
    * Flexible, well commented, and documented code structure so that it is easy to add new symbols or other features
    * Staff systems - more than one staff in a single system (such as piano staves, or orchestral scores
    * beams - ability to beam together sets of notes
    * time signatures - recognition of time signatures
    * zooming, scrolling, and support for multiple pages.
    * Saving - save and load scores
    * "handwritten" look - program should use what the user actually drew, rather than a perfect computer symbol
    * drag/drop
      * Transposition - notes should be able to be dragged up and down to be tranposed
      * Reposition - notes and symbols should be repositioned via dragging
    * right click
      * right-clicking on an object should bring up options - perhaps change object, etc.

Version 1.0 will be the first full release.  The requirement for version 1.0 is to solicit feedback, and apply any necessary changes to make the program more usable and natural, as well as to collect feature requests for future versions.

# Future Features #
These features have been identified as possibly useful and desirable, but have not been assigned to a particular version.
  * Auto-train: Right click on unrecognized drawn objects to select desired object, and add this to the training set.
  * Export music to a standard notation or music format or formats
  * An "alignment" or "prettify" feature, which lines up the symbols in an aesthetically pleasing (and musical semantics respectful) way
  * Transpose option (select notes with right click, including box select, and then use up and down arrows?)
  * Web interface?
  * drag and move objects
  * undo ability
  * change arrow cursor to an ink-aware cursor
  * visual appeal - better looking noteheads
  * visual style - look like a pad of staff paper; holes in top or side like a tablet; area to write title, set barlines, etc.
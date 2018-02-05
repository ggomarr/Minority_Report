# Minority Report

This was an interface to control a computer with the wave of a hand using a Kinect I developed on in May 2012. I wanted to clean it up (meaning, preparing a video) (and 'refactoring the code' - it is horrendous!) before uploading it here but I think I may never get to it. The main file is controller_2D.py (the other two files being half baked upgrades - a tracker using particle filters and a tracker where the actionable space is in 3D, as opposed to mostly-2D).

The framework allowed controlling different types of services. The code as is would interact with three:
- Banshee (Play/Pause, Next/Previous, Volume Up/Down)
- XBMC (Up/Down/Left/Right, Back/Stop, Select/Play/Pause) (similar to the controller on an AppleTV 2)
- A super fun game that will print "HAM!", "EGG!", or "Bull's Eye!" depending on where the hand moves

Limited feedback on the state of the controller is received through the LED on the Kinect. The screen of the computer running the scripts would show whether it has locked onto what it thinks is a hand, what the controller looks like for the active service, and where the hand is (if present).

Enjoy!

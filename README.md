# APC20/40 Visualizer
Turns your Akai APC20/40s into an eyecatching music visualizer while you're not using it.

## Demo
![](demo.gif)

## Features
- Can be run in background without a noticable performance impact
- Automagically detects current output device and gets audio using a virtual loopback
- Wanna use the APC in Ableton (or any other software)? The visualizer will automatically pause and free the MIDI port (currently Windows only)
- Janky system volume compensation: experience the visualizer's visuals in their full visual glory even at low volumes (also Windows only, sorry)
- Most of the code can be recycled to create your own APC MIDI Remote Scripts / lightshows

## Note
- So far this has only been tested with an APC20, but it should work with an APC40 as well (plz confim thx)
- Contributions are very much appreciated 😉

## Suggestion
1. Create a shortcut that launches apc_visualizer.py
2. put it in your startup folder
3. Hide the window using [TrayIt!](https://www.majorgeeks.com/files/details/trayit.html) or something less abandoned
4. ?
5. Profit

## Improvement Ideas
- better system volume compensation (by getting the audio before it gets mangled by Window's mixer), or even better:
- automatic scaling (using the last x frames to determine a nice volume to height ratio)
- better linux compatability
- using the rightmost column to show system volume + cue knob to control it


## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

[![forthebadge](https://forthebadge.com/images/badges/built-with-science.svg)](https://forthebadge.com) [![forthebadge](https://forthebadge.com/images/badges/contains-tasty-spaghetti-code.svg)](https://forthebadge.com)

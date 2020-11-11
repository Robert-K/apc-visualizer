import soundcard as sc
import numpy as np
import mido
from time import sleep

# -------- APC20 velocity to color mappings --------

OFF = 0
GREEN = 1
GREEN_FLASH = 2
RED = 3
RED_FLASH = 4
ORANGE = 5
ORANGE_FLASH = 6

# ------ Sample Rate and sample size per frame ------

RATE = 48000
CHUNK = 1024

# -- Change this if nothing is visible / fft clips --

SENSITIVITY = 13

# ------- Determines how fast fft bands fall  -------

DECAY = 0.5

MIDI_REOPEN_INTERVAL = 5


def set_led(x, y, color):
    if y < 0 or y > 9:
        return
    if y > 4:
        y = 14 - y
    msg = mido.Message("note_on", channel=x, note=48 + y, velocity=color)
    apc_out.send(msg)


def fill(color):
    for x in range(0, 8):
        for y in range(0, 10):
            set_led(x, y, color)


def clear():
    fill(OFF)


def set_col(col, val):
    if val > cols[col]:
        for y in range(cols[col], val):
            color = GREEN if y < 6 else ORANGE if y < 8 else RED
            set_led(col, y, color)
        cols[col] = val
    elif val < cols[col]:
        for y in range(val, cols[col]):
            set_led(col, y, OFF)
        cols[col] = val


def fft_leds(data):
    fft = np.abs(np.fft.fft(data)[0 : CHUNK // 2])
    for band in range(8):
        val = np.mean(fft[limits[band] : limits[band + 1]]) / (pow(7 - band, 2) + 1)
        val *= SENSITIVITY
        val = min([val, 12])
        val = np.log(val + 0.5) * 4 + 1 + val / 2
        prev = smooth[band]
        smooth[band] = val if val > prev else prev - DECAY
        set_col(band, int(smooth[band]))


limits = [0]
for i in range(7):
    limits.append(CHUNK // pow(2, 8 - i))
limits.append(CHUNK // 2 - 1)

if __name__ == "__main__":
    while True:
        try:
            while True:
                port_name = "Akai APC20 2"
                for port in mido.get_output_names():
                    if "Akai APC" in port:
                        port_name = port
                        break
                print("Opening MIDI Port", port_name)
                with mido.open_output(port_name) as apc_out:
                    clear()
                    while True:
                        speaker = sc.default_speaker()
                        loopback = sc.get_microphone(speaker.id, include_loopback=True)
                        print("Using ", speaker.name)
                        try:
                            with loopback.recorder(
                                samplerate=RATE, channels=[0]
                            ) as mic:
                                cols = [0, 0, 0, 0, 0, 0, 0, 0]
                                smooth = [0, 0, 0, 0, 0, 0, 0, 0]
                                while True:
                                    if sc.default_speaker().id != speaker.id:
                                        print("Audio output changed.")
                                        break
                                    fft_leds(
                                        np.concatenate(mic.record(numframes=CHUNK))
                                    )
                        except RuntimeError:
                            print("Audio output lost.")
        except OSError as e:
            print(
                f"MIDI Device can't be opened. Trying again in {MIDI_REOPEN_INTERVAL} seconds..."
            )
            try:
                sleep(MIDI_REOPEN_INTERVAL)
            except KeyboardInterrupt:
                print("KeyboardInterrupt received. Aborting wait...")
                break
        except KeyboardInterrupt:
            print("KeyboardInterrupt received. Terminating gracefully...")
            break

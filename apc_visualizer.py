# Compensate to get nice results regardless of Windows master volume, success may vary from device to device
VOLUME_COMPENSATION = True

if VOLUME_COMPENSATION:
    from winvol import IAudioEndpointVolume

import soundcard as sc
import numpy as np
import mido
import mido.backends.rtmidi
from time import sleep
import win32ui

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

# ------- Determines how fast fft bands fall  -------

DECAY = 0.5

# If an instance of these window classes is open, the visualizer stops and frees the MIDI port
# You can find a window's class name using Window Spy
BLOCKING_WINDOW_CLASSES = ["Ableton Live Window Class"]

BLOCKING_CHECK_INTERVAL = 5
MIDI_REOPEN_INTERVAL = 5


def blocking_window_open():
    try:
        for classname in BLOCKING_WINDOW_CLASSES:
            win32ui.FindWindow(classname, None)
    except win32ui.error:
        return False
    else:
        return True


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


def show_vol(ev):
    voldb = ev.GetMasterVolumeLevel()
    volsc = ev.GetMasterVolumeLevelScalar()
    volst, nstep = ev.GetVolumeStepInfo()
    print("Master Volume (dB): %0.4f" % voldb)
    print("Master Volume (scalar): %0.4f" % volsc)
    print("Master Volume (step): %d / %d" % (volst, nstep))


def fft_leds(data):
    fft = np.abs(np.fft.fft(data)[0 : CHUNK // 2])
    if VOLUME_COMPENSATION:
        vol = winaudio.GetMasterVolumeLevelScalar()
    else:
        vol = 0
    for band in range(8):
        val = np.mean(fft[limits[band] : limits[band + 1]]) / (pow(7 - band, 2) + 1)
        if vol > 0:
            val = val / vol * 10
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
    can_run = not blocking_window_open()

    while True:
        try:
            while can_run:
                port_name = "Akai APC20 2"
                for port in mido.get_output_names():
                    if "Akai APC" in port:
                        port_name = port
                        break
                print("Opening MIDI Port", port_name)
                with mido.open_output(port_name) as apc_out:
                    clear()
                    while can_run:
                        speaker = sc.default_speaker()
                        loopback = sc.get_microphone(speaker.id, include_loopback=True)
                        if VOLUME_COMPENSATION:
                            winaudio = IAudioEndpointVolume.get_default()
                        print("Using ", speaker.name)
                        try:
                            with loopback.recorder(
                                samplerate=RATE, channels=[0]
                            ) as mic:
                                cols = [0, 0, 0, 0, 0, 0, 0, 0]
                                smooth = [0, 0, 0, 0, 0, 0, 0, 0]
                                iterations = 0
                                while can_run:
                                    if sc.default_speaker().id != speaker.id:
                                        print("Audio output changed.")
                                        break
                                    fft_leds(
                                        np.concatenate(mic.record(numframes=CHUNK))
                                    )
                                    if (
                                        iterations
                                        > RATE / CHUNK * BLOCKING_CHECK_INTERVAL
                                    ):
                                        iterations = 0
                                        if blocking_window_open():
                                            print(
                                                "Ableton detected. Committing sudoku..."
                                            )
                                            can_run = False
                                            clear()
                                    iterations += 1
                        except RuntimeError:
                            print("Audio output lost.")
            print("Instance of Ableton detected. Waiting for it to be closed...")
            while blocking_window_open():
                sleep(BLOCKING_CHECK_INTERVAL)
            can_run = True
        except OSError as e:
            if blocking_window_open():
                print("Instance of Ableton detected. Waiting for it to be closed...")
                sleep(BLOCKING_CHECK_INTERVAL)
                try:
                    while blocking_window_open():
                        sleep(BLOCKING_CHECK_INTERVAL)
                except KeyboardInterrupt:
                    print("KeyboardInterrupt received. Aborting wait...")
                    break
            else:
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

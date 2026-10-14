"""Synthesize an original, gentle piano-style backing track (44s) -> music.wav."""
import pathlib
import wave

import numpy as np

SR = 44100
DUR = 44.0
BAR = 2.6  # seconds per bar (~92 bpm, 4/4)
HERE = pathlib.Path(__file__).parent


def midi_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def piano(freq, length, vel=1.0):
    t = np.arange(int(length * SR)) / SR
    tone = sum(a * np.sin(2 * np.pi * freq * k * t) * np.exp(-t * (2.2 + k * 1.1))
               for k, a in [(1, 1.0), (2, .42), (3, .18), (4, .08)])
    attack = np.minimum(1, t / 0.006)
    return tone * attack * vel


def pad(freq, length):
    t = np.arange(int(length * SR)) / SR
    env = np.minimum(1, t / 0.8) * np.minimum(1, (length - t) / 0.8)
    return (np.sin(2 * np.pi * freq * t) + .5 * np.sin(2 * np.pi * freq * 2.003 * t)) * env * .06


# Chords as (root midi, [chord tones]) — C G Am Em F C F G, played twice.
CHORDS = [
    (48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (40, [59, 64, 67]),
    (41, [60, 65, 69]), (48, [60, 64, 67]), (41, [60, 65, 69]), (43, [59, 62, 67]),
]
# Simple top melody, one note per half bar (second pass only).
MELODY = [76, 74, 74, 71, 72, 76, 71, 69, 69, 67, 72, 67, 69, 72, 71, 74]

out = np.zeros(int((DUR + 3) * SR))


def add(sig, start):
    i = int(start * SR)
    out[i:i + len(sig)] += sig[:max(0, len(out) - i)]


bars = int(DUR // BAR)
for b in range(bars):
    root, tones = CHORDS[b % len(CHORDS)]
    t0 = b * BAR
    add(piano(midi_hz(root), 3.5, .55), t0)
    add(pad(midi_hz(root + 12), BAR + .6), t0)
    pattern = [tones[0], tones[1], tones[2], tones[1] + 12, tones[2], tones[1], tones[0] + 12, tones[1]]
    for j, n in enumerate(pattern):
        add(piano(midi_hz(n), 2.2, .32 if j % 2 else .4), t0 + j * BAR / 8)
    if b >= 8:
        for k in range(2):
            add(piano(midi_hz(MELODY[(b - 8) * 2 + k]), 2.6, .5), t0 + k * BAR / 2)

# Final ringing C chord.
for n in [48, 60, 64, 67, 72]:
    add(piano(midi_hz(n), 4.0, .45), bars * BAR)

# Light room reverb via a few feedback taps.
dry = out.copy()
for delay, gain in [(.043, .28), (.071, .22), (.113, .16), (.167, .11), (.241, .07)]:
    d = int(delay * SR)
    out[d:] += dry[:-d] * gain

out = out[:int(DUR * SR)]
t = np.arange(len(out)) / SR
out *= np.minimum(1, t / 1.5) * np.minimum(1, (DUR - t) / 3.0)
out = out / np.max(np.abs(out)) * 0.7

stereo = np.stack([out, np.roll(out, int(.012 * SR)) * .96], axis=1)
with wave.open(str(HERE / "music.wav"), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((stereo * 32767).astype(np.int16).tobytes())
print("wrote music.wav", round(len(out) / SR, 2), "s")

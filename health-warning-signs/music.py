"""Synthesises an original score for the video from timeline.json (no samples, no licensing).

  hook / intro   dark A-minor drone, a lone heartbeat at heart.bpm
  signs 1-3      emergencies: heartbeat + low pulse + tense minor pads, a boom on each sign
  signs 4-8      same bed, chords cycle Am - F - C - G, one per sign
  flat           everything drops out; a quiet monitor flatline tone
  turn / cta     the heartbeat comes back (heart.bpm_after), warm major chords and rising
                 plucks, ending on a held C major chord
Heartbeat times match heartBeats() in scene.html so the ECG line spikes on every beat.
Usage: python3 music.py [out.wav]
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TL = json.loads((HERE / 'timeline.json').read_text())
SC = {s['id']: s for s in TL['scenes']}
SR = 48000
DUR = TL['duration']
N = int(SR * DUR)
rng = np.random.default_rng(11)


def heart_beats():
    """Beat times, shared with heartBeats() in scene.html."""
    out, flat, turn = [], SC['flat']['start'], SC['turn1']['start']
    t = 0.5
    while t < flat - 0.2:
        out.append(t)
        t += 60 / TL['heart']['bpm']
    t = turn + 0.15
    while t < DUR - 1.5:
        out.append(t)
        t += 60 / TL['heart']['bpm_after']
    return out


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env(n, a, r):
    """Attack/release envelope over n samples (seconds)."""
    t = np.arange(n) / SR
    return np.clip(t / max(a, 1e-6), 0, 1) * np.clip((n / SR - t) / max(r, 1e-6), 0, 1)


def lowpass(x, cutoff):
    """One-pole low-pass (short signals only); cutoff may be per-sample."""
    c = np.broadcast_to(np.asarray(cutoff, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def tone(f, n, harmonics=6, bright=0.55, detune=0.0):
    """Additive saw-ish tone: harmonics rolled off by `bright` (no filter needed)."""
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d in ((-detune, detune) if detune else (0.0,)):
        ph = rng.random() * 2 * np.pi
        for h in range(1, harmonics + 1):
            out += np.sin(2 * np.pi * f * (1 + d) * h * t + ph * h) * bright ** (h - 1) / h
    return out


L = np.zeros(N)
R = np.zeros(N)
verb_send = np.zeros(N)


def add(sig, start, pan=0.0, verb=0.0):
    i = int(start * SR)
    if i >= N or i + len(sig) <= 0:
        return
    sig = sig[: N - i]
    L[i:i + len(sig)] += sig * np.sqrt((1 - pan) / 2)
    R[i:i + len(sig)] += sig * np.sqrt((1 + pan) / 2)
    if verb:
        verb_send[i:i + len(sig)] += sig * verb


# ---- instruments ---------------------------------------------------------
def thump(gain, f0=58):
    n = int(SR * 0.32)
    t = np.arange(n) / SR
    f = f0 + 40 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 13) * gain


def heartbeat(gain):
    """lub-dub"""
    n = int(SR * 0.6)
    out = np.zeros(n)
    a = thump(gain)
    b = thump(gain * 0.7, 66)
    out[:len(a)] += a
    k = int(SR * 0.19)
    out[k:k + len(b)] += b[: n - k]
    return np.tanh(out * 1.4)


def pad(notes, length, gain, bright=0.5, a=1.2, r=1.5):
    n = int(SR * length)
    sig = sum(tone(midi(m), n, 6, bright, detune=0.003) for m in notes)
    lfo = 1 + 0.15 * np.sin(2 * np.pi * 0.2 * np.arange(n) / SR + rng.random() * 6)
    return sig * lfo * env(n, a, r) * gain


def pluck(note, length=1.2, gain=0.1):
    n = int(SR * length)
    t = np.arange(n) / SR
    sig = tone(midi(note), n, 8, 0.6) * np.exp(-t * 4.5)
    sig += np.sin(2 * np.pi * midi(note) * 2 * t) * np.exp(-t * 9) * 0.3   # bell-ish attack
    return sig * env(n, 0.003, 0.2) * gain


def boom(gain=0.5):
    n = int(SR * 2.5)
    t = np.arange(n) / SR
    f = 34 + 50 * np.exp(-t * 6)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    return np.tanh(body * 1.5) * gain


def whoosh(length, gain=0.12, rise=True):
    n = int(SR * length)
    t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    cut = 200 + 6000 * (t ** 2 if rise else (1 - t) ** 2)
    sig = lowpass(noise, cut) - lowpass(noise, cut * 0.25)
    return sig * (t ** 2 if rise else (1 - t) ** 2) * gain


# ---- arrangement ---------------------------------------------------------
flat = SC['flat']
turn = SC['turn1']['start']
cta = SC['cta']['start']
signs = [s for s in TL['scenes'] if s['type'] == 'sign']

for t in heart_beats():
    gain = 0.75 if t < flat['start'] else 0.6
    if t < SC['intro']['start']:
        gain = 0.55
    add(heartbeat(gain), t, verb=0.15)

# dark drone under the hook + intro
add(pad([33, 45, 52], signs[0]['start'] + 1.5, 0.05, bright=0.35, a=2.5, r=1.5), 0.0, verb=0.4)
add(pad([57, 60, 64, 71], SC['intro']['end'] - SC['intro']['start'] + 1.0, 0.035, a=1.5), SC['intro']['start'], verb=0.6)
add(whoosh(1.2, 0.14), SC['intro']['start'] - 1.2, verb=0.3)

MINOR = [(33, [57, 60, 64]), (29, [57, 60, 65]), (36, [55, 60, 64]), (31, [55, 59, 62])]   # Am F C G
for k, s in enumerate(signs):
    root, tones = MINOR[k % 4]
    length = s['end'] - s['start'] + 1.2
    emergency = s['level'] == 'emergency'
    add(pad(tones, length, 0.045 if emergency else 0.04, bright=0.45, a=0.6, r=1.2), s['start'], verb=0.5)
    add(pad([root, root + 12], length, 0.07, bright=0.3, a=0.3, r=1.0), s['start'], verb=0.1)
    add(boom(0.55 if emergency else 0.35), s['start'])
    add(whoosh(0.9, 0.12), s['start'] - 0.9, verb=0.3)
    # high pluck motif on the action line
    act = s['lines_t'][-1][0]
    for j, m in enumerate([tones[0] + 12, tones[2] + 12]):
        add(pluck(m, 1.4, 0.06), act + j * 0.47, pan=(-0.3 if j else 0.3), verb=0.6)
    if emergency:
        # ticking pulse: urgency
        for j in range(int((s['end'] - s['start']) / 0.47)):
            n = int(SR * 0.04)
            click = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 120) * 0.035
            add(click, s['start'] + 0.2 + j * 0.47, pan=0.4 * (-1) ** j)

# flatline: a quiet sine that fades as the next section arrives
n = int(SR * (turn - flat['start'] + 0.2))
add(np.sin(2 * np.pi * 988 * np.arange(n) / SR) * env(n, 0.02, 0.4) * 0.05, flat['start'], verb=0.3)

# turn: warm major progression, one chord per statement scene
MAJOR = [[48, 55, 60, 64], [43, 55, 59, 62, 67], [45, 57, 60, 64], [41, 57, 60, 65]]   # C G Am F
for k, sid in enumerate(['turn1', 'turn2', 'turn3']):
    s = SC[sid]
    add(pad(MAJOR[k], s['end'] - s['start'] + 1.5, 0.045, bright=0.55, a=0.8, r=1.5), s['start'], verb=0.6)
    add(pad([MAJOR[k][0] - 12], s['end'] - s['start'] + 1.0, 0.08, bright=0.3, a=0.5, r=1.0), s['start'])
    for j in range(8):
        add(pluck(MAJOR[k][j % len(MAJOR[k])] + 24, 1.2, 0.04 + 0.006 * j), s['start'] + 0.3 + j * 0.405,
            pan=0.35 * (-1) ** j, verb=0.6)
add(whoosh(1.6, 0.14), cta - 1.6, verb=0.4)

# call to action: lift into F - G - C, ringing out
add(boom(0.6), cta)
cta_len = DUR - cta
for j, chord in enumerate([[41, 57, 60, 65, 69], [43, 55, 59, 62, 67], [36, 48, 55, 60, 64, 67, 72]]):
    start = cta + j * cta_len / 4
    length = cta_len / 4 + 0.6 if j < 2 else DUR - start
    add(pad(chord, length, 0.04, bright=0.6, a=0.4, r=0.8 if j < 2 else 3.0), start, verb=0.6)
for j in range(16):
    m = [72, 76, 79, 84][j % 4] + (0 if j < 12 else 12)
    add(pluck(m, 1.4, 0.05), cta + 0.2 + j * 0.405, pan=0.35 * (-1) ** j, verb=0.7)

# ---- reverb (FFT convolution with a decaying noise tail) -----------------
ir_t = np.arange(int(SR * 2.4)) / SR
mask = np.exp(-ir_t * 2.4)


def conv(x, h):
    m = len(x) + len(h)
    size = 1 << (m - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(h, size), size)[: len(x)]


def dark(x, cutoff=4500):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / (1 + (f / cutoff) ** 2), len(x))


L += conv(verb_send, dark(rng.standard_normal(len(mask)) * mask)) * 0.03
R += conv(verb_send, dark(rng.standard_normal(len(mask)) * mask)) * 0.03

# ---- master --------------------------------------------------------------
stereo = np.stack([L, R], axis=1)
t = np.arange(N) / SR
stereo *= (np.clip(t / 0.05, 0, 1) * np.clip((DUR - t) / 2.5, 0, 1) ** 1.5)[:, None]
stereo = np.tanh(stereo / np.max(np.abs(stereo)) * 1.3)
stereo *= 0.89 / np.max(np.abs(stereo))

out = sys.argv[1] if len(sys.argv) > 1 else 'music.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((stereo * 32767).astype('<i2').tobytes())
print('wrote', out)

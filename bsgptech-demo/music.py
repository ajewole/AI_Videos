"""Synthesises an original 10 s background track for the promo (no samples, no licensing).

150 BPM, so one bar (1.6 s) matches one service scene in scene.html:
  0.0-1.4  intro swell + riser + snare roll
  1.4-7.8  four bars of Am - F - C - G with drums, bass and a plucked arpeggio
  7.8-10   impact on the call to action, held C major chord fading out
Usage: python3 music.py [out.wav]
"""
import sys
import wave

import numpy as np

SR = 48000
DUR = 10.0
BEAT = 60 / 150
BAR = 4 * BEAT
DROP = 1.4           # first service scene
CTA = 7.8            # call-to-action scene
N = int(SR * DUR)
rng = np.random.default_rng(7)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env(n, a, d, s=0.0, r=0.0, hold=None):
    """ADSR envelope over n samples; times in seconds."""
    t = np.arange(n) / SR
    hold = hold if hold is not None else n / SR
    e = np.where(t < a, t / max(a, 1e-6), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-6)))
    if r:
        e = e * np.clip(1 - (t - hold) / r, 0, 1) ** 2 * (t >= hold) + e * (t < hold)
    return e


def lowpass(x, cutoff):
    """One-pole low-pass; cutoff may be a scalar or per-sample array."""
    c = np.broadcast_to(np.asarray(cutoff, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def saw(f, n, detune=0.0, phase=0.0):
    t = np.arange(n) / SR
    out = 0
    for d in (-detune, 0, detune) if detune else (0,):
        ph = (t * f * (1 + d) + phase + rng.random()) % 1
        out = out + (2 * ph - 1)
    return out / (3 if detune else 1)


def place(buf, sig, start):
    i = int(start * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    buf[i:i + len(sig)] += sig


L = np.zeros(N)
R = np.zeros(N)
verb_send = np.zeros(N)


def add(sig, start, pan=0.0, verb=0.0):
    l, r = sig * np.sqrt((1 - pan) / 2), sig * np.sqrt((1 + pan) / 2)
    place(L, l, start)
    place(R, r, start)
    if verb:
        place(verb_send, sig * verb, start)


# ---- instruments ---------------------------------------------------------
def kick(gain=1.0, big=False):
    n = int(SR * (0.9 if big else 0.35))
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * (3.5 if big else 9))
    click = rng.standard_normal(n) * np.exp(-t * 400) * 0.25
    return np.tanh((body + click) * 1.6) * gain


def clap(gain=0.5):
    n = int(SR * 0.25)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    bursts = sum(np.exp(-np.clip(t - k * 0.009, 0, None) * 120) * (t >= k * 0.009) for k in range(3))
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 40) * 0.4
    sig = noise - lowpass(noise, 900)
    return (sig * bursts * 0.5 + tone) * np.exp(-t * 14) * gain


def hat(gain=0.18, open_=False):
    n = int(SR * (0.22 if open_ else 0.05))
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    hp = noise - lowpass(noise, 7000)
    return hp * np.exp(-t * (18 if open_ else 90)) * gain


def bass(note, length, gain=0.45):
    n = int(SR * length)
    f = midi(note)
    t = np.arange(n) / SR
    sig = 0.7 * np.sin(2 * np.pi * f * t) + 0.35 * saw(f, n)
    sig = lowpass(sig, 300 + 1500 * np.exp(-t * 18))
    return sig * env(n, 0.004, 0.18, 0.55, 0.03, hold=length - 0.03) * gain


def pluck(note, length=0.28, gain=0.16):
    n = int(SR * length)
    f = midi(note)
    t = np.arange(n) / SR
    sig = saw(f, n, detune=0.006) + 0.5 * np.sign(np.sin(2 * np.pi * f * t))
    sig = lowpass(sig, 600 + 5000 * np.exp(-t * 22))
    return sig * env(n, 0.002, 0.09) * gain


def pad(notes, length, gain=0.07, cutoff=2200):
    n = int(SR * length)
    sig = sum(saw(midi(m), n, detune=0.004) for m in notes)
    sig = lowpass(sig, cutoff)
    return sig * env(n, 0.25, 9, 1.0, 0.35, hold=length - 0.35) * gain


def noise_sweep(length, rise=True, gain=0.22):
    n = int(SR * length)
    t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    cut = 300 + 9000 * (t ** 2 if rise else (1 - t) ** 2)
    sig = lowpass(noise, cut) - lowpass(noise, cut * 0.3)
    shape = t ** 2 if rise else (1 - t) ** 3
    return sig * shape * gain


# ---- arrangement ---------------------------------------------------------
# chords as (bass root, chord tones) — Am F C G, resolving to C on the CTA
CHORDS = [(45, [57, 60, 64]), (41, [57, 60, 65]), (48, [55, 60, 64]), (43, [55, 59, 62])]
ARP = [0, 1, 2, 1, 2, 1, 0, 2]  # indexes into chord tones (+12) per 8th

# Intro: filtered Am pad swelling, noise riser, snare roll into the drop
add(pad([57, 60, 64, 69], DROP + 0.2, gain=0.09, cutoff=900), 0.0, verb=0.4)
add(noise_sweep(DROP, rise=True, gain=0.25), 0.0, verb=0.3)
for k in range(8):
    t = DROP - BEAT * 2 + k * BEAT / 4
    add(clap(0.12 + 0.05 * k), t, pan=0.1, verb=0.2)
add(pluck(69, 0.5, 0.12), 0.05, pan=-0.3, verb=0.6)
add(pluck(76, 0.5, 0.10), 0.05 + BEAT, pan=0.3, verb=0.6)

# Four bars, one per service scene
for b, (root, tones) in enumerate(CHORDS):
    t0 = DROP + b * BAR
    add(pad(tones + [tones[0] + 12], BAR + 0.1, gain=0.06), t0, verb=0.35)
    add(noise_sweep(0.35, rise=False, gain=0.16), t0, pan=0.0, verb=0.3)   # whoosh on the scene change
    for beat in range(4):
        tb = t0 + beat * BEAT
        add(kick(0.7), tb)
        if beat in (1, 3):
            add(clap(0.42), tb, verb=0.25)
        add(hat(0.16, open_=True), tb + BEAT / 2, pan=0.25)
        add(hat(0.08), tb + BEAT / 4, pan=-0.25)
        add(hat(0.08), tb + 3 * BEAT / 4, pan=-0.25)
        add(bass(root, BEAT / 2 - 0.01), tb + BEAT / 2)
        add(bass(root + 12, BEAT / 4 - 0.01, 0.25), tb + 3 * BEAT / 4)
    for k, idx in enumerate(ARP):
        add(pluck(tones[idx] + 12), t0 + k * BEAT / 2, pan=(-0.4 if k % 2 else 0.4), verb=0.35)
    if b == len(CHORDS) - 1:
        # riser into the call to action
        add(noise_sweep(BAR * 0.75, rise=True, gain=0.2), CTA - BAR * 0.75, verb=0.3)

# Call to action: impact + resolving C major chord, ringing out to the end
add(kick(1.1, big=True), CTA)
crash = rng.standard_normal(int(SR * 2.2))
crash = (crash - lowpass(crash, 5000)) * np.exp(-np.arange(len(crash)) / SR * 2.2) * 0.12
add(crash, CTA, pan=0.0, verb=0.5)
add(bass(36, 2.0, 0.5), CTA)
add(pad([48, 55, 60, 64, 67, 72], DUR - CTA, gain=0.08, cutoff=2600), CTA, verb=0.5)
for k, m in enumerate([72, 76, 79, 84]):
    add(pluck(m, 0.6, 0.11), CTA + 0.2 + k * BEAT / 2, pan=(-0.3 if k % 2 else 0.3), verb=0.7)

# ---- reverb (convolution with a decaying noise tail) ---------------------
ir_len = int(SR * 1.6)
ir_t = np.arange(ir_len) / SR
ir_l = rng.standard_normal(ir_len) * np.exp(-ir_t * 3.2)
ir_r = rng.standard_normal(ir_len) * np.exp(-ir_t * 3.2)
ir_l, ir_r = lowpass(ir_l, 5000), lowpass(ir_r, 5000)


def conv(x, h):
    m = len(x) + len(h)
    size = 1 << (m - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(h, size), size)[: len(x)]


L += conv(verb_send, ir_l) * 0.035
R += conv(verb_send, ir_r) * 0.035

# ---- master: fades, soft clip, normalise ---------------------------------
stereo = np.stack([L, R], axis=1)
t = np.arange(N) / SR
fade = np.clip(t / 0.05, 0, 1) * np.clip((DUR - t) / 1.2, 0, 1) ** 1.5
stereo *= fade[:, None]
stereo = np.tanh(stereo / np.max(np.abs(stereo)) * 1.4)
stereo *= 0.89 / np.max(np.abs(stereo))

out = sys.argv[1] if len(sys.argv) > 1 else 'music.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((stereo * 32767).astype('<i2').tobytes())
print('wrote', out)

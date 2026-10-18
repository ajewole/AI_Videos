# Signs Your Body Is Warning You – 104s narrated video

An inspirational, action-provoking health-awareness video: eight warning signs, what each can mean,
and what to do, carried by a live ECG heartbeat that flatlines before the hopeful turn and call to action.

All versions are 104 s, 30 fps, H.264 with narration over an original score (AAC, -14 LUFS).

| File | Size | Use it for |
|------|------|------------|
| `body-warning-signs-9x16.mp4` | 1080×1920 | Reels, TikTok, YouTube Shorts, Stories, WhatsApp Status |
| `body-warning-signs-16x9.mp4` | 1920×1080 | YouTube, LinkedIn, X/Twitter, Facebook, website |
| `body-warning-signs-4x5.mp4` | 1080×1350 | Instagram & Facebook feed posts |
| `body-warning-signs-1x1.mp4` | 1080×1080 | Square feed posts |

The 9:16 layout keeps the bottom ~420px free of text so platform captions and buttons don't cover it.

| Time | Scene |
|------|-------|
| 0.0–4.9s | Hook: "Your body whispers. Before it screams." |
| 4.9–8.9s | "8 warning signs you should never ignore" |
| 8.9–19.0s | Sign 1: Chest pain or pressure → Heart attack (emergency) |
| 19.0–28.2s | Sign 2: Face drooping, arm weakness, slurred speech → Stroke (emergency) |
| 28.2–36.7s | Sign 3: The worst headache of your life → Bleeding in the brain (emergency) |
| 36.7–44.8s | Sign 4: Breathless doing everyday things → Heart or lung disease (see a doctor) |
| 44.8–53.5s | Sign 5: Constant thirst & frequent urination → Diabetes (see a doctor) |
| 53.5–62.4s | Sign 6: Losing weight without trying → Thyroid problems, diabetes or cancer (see a doctor) |
| 62.4–71.1s | Sign 7: A mole that changes → Skin cancer (see a doctor) |
| 71.1–80.7s | Sign 8: Blood where it shouldn't be → Bowel, bladder or kidney disease (see a doctor) |
| 80.7–82.3s | Flatline: the heartbeat stops |
| 82.3–87.2s | "Listening to your body isn't fear. It's self-respect." |
| 87.2–92.1s | "Caught early, most serious conditions are far more treatable." |
| 92.1–95.1s | "So don't wait for the scream." |
| 95.1–103.6s | Call to action: book the check-up TODAY, share with someone you love |

Red signs are emergencies (call emergency services); amber signs mean "see a doctor, don't wait".
The video carries an on-screen disclaimer that it is awareness, not medical advice, with emergency numbers (911 · 999 · 112).

## How it's built

Everything is generated from `script.json` (on-screen copy + narration for every scene):

```sh
python3 voiceover.py      # Piper TTS → voice.wav, plus timeline.js/.json with every scene and line timing
python3 music.py          # original score from the timeline → music.wav
node render.mjs           # renders all four formats (or: node render.mjs vertical)
PREVIEW=1 node render.mjs # one still per scene in preview/   (TIMES=3.6,81.5 for specific moments)
```

- **Narration**: [Piper](https://github.com/rhasspy/piper) (`pip install piper-tts`), voice `en_US-john-medium`, trained on public-domain LibriVox recordings. `voiceover.py` downloads it into `.cache/` on first run. Change `voice` / `length_scale` in `script.json` to try another voice or pace.
- **Music**: synthesised from scratch by `music.py` (no samples, free to use anywhere). The heartbeat in the music and the ECG spikes on screen use the same beat schedule (`heart` in `script.json`).
- **Mix**: `render.mjs` puts the music ~16 dB under the voice, ducks it while the narrator speaks, and normalises to -14 LUFS.
- **Timing**: scenes are as long as their narration, so editing a line in `script.json` and re-running the three steps keeps everything in sync. Text reveals follow the pauses in each spoken line.
- Open `scene.html?format=vertical&t=40` in a browser to preview any moment (formats: `landscape`, `vertical`, `square`, `portrait`).

Requires Python 3 + numpy, Node, ffmpeg and Playwright (set `PLAYWRIGHT=/path/to/playwright/index.mjs` if it is not importable as `playwright`).

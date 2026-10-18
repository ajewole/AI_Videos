# BSGP Technologies – 10s promo video

All versions are 10 s, 30 fps, H.264 with an original background music track (AAC, -14 LUFS).

| File | Size | Use it for |
|------|------|------------|
| `bsgptech-demo-16x9.mp4` | 1920×1080 | YouTube, LinkedIn, X/Twitter, Facebook, website |
| `bsgptech-demo-9x16.mp4` | 1080×1920 | Instagram Reels & Stories, TikTok, YouTube Shorts, Facebook Reels/Stories, WhatsApp Status, Snapchat |
| `bsgptech-demo-4x5.mp4` | 1080×1350 | Instagram & Facebook feed posts (largest on-screen feed size) |
| `bsgptech-demo-1x1.mp4` | 1080×1080 | Square feed posts (Instagram, Facebook, LinkedIn, X) |

The 9:16 layout keeps the bottom ~400px clear of text so TikTok/Reels captions and buttons don't cover it.

| Time | Scene |
|------|-------|
| 0.0–1.4s | Intro: logo + "Learn. Innovate. Build. Sell." over the site hero |
| 1.4–3.0s | 01 Solution Development (homepage + service card) |
| 3.0–4.6s | 02 Training & Capacity Building (scrolling /training course catalogue) |
| 4.6–6.2s | 03 Engineering Design (CAD course imagery + service card) |
| 6.2–7.8s | 04 Consultancy (site team photo + service card) |
| 7.8–10s | Call to action: WhatsApp, phone, email, bsgptech.com |

All screenshots in `assets/` were captured from https://bsgptech.com/ with headless Chromium.

## Music

`music.wav` is synthesised from scratch by `music.py` (no samples or third-party audio, so it is free to use on any platform). It runs at 150 BPM so each bar lands on a scene change: an intro swell and riser, a drop as the first service appears, one Am–F–C–G bar per service with a whoosh on each transition, and an impact and resolving chord on the call to action.

```sh
python3 music.py music_raw.wav
ffmpeg -i music_raw.wav -af loudnorm=I=-14:TP=-1.5:LRA=7 -ar 48000 music.wav
```

`render.mjs` uses `music.wav` automatically (silent track if it is missing). To swap the music without re-rendering the picture:

```sh
ffmpeg -i bsgptech-demo-9x16.mp4 -i your-track.mp3 -map 0:v -map 1:a -c:v copy -c:a aac -shortest out.mp4
```

## Editing and re-rendering

- Contact details live in the `CONTACT` object at the top of `scene.html`.
- Scene timings are in `SCENES`; per-format positions are in `FORMATS` in `scene.html`.
- Open `scene.html?format=vertical&t=8.5` in a browser to preview any moment (formats: `landscape`, `vertical`, `square`, `portrait`).

```sh
node render.mjs                 # renders all four formats
node render.mjs vertical        # renders just one
PREVIEW=1 node render.mjs       # writes still frames to preview/
```

Requires Node, ffmpeg and Playwright (set `PLAYWRIGHT=/path/to/playwright/index.mjs` if it is not importable as `playwright`).

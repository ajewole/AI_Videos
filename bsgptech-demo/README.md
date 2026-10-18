# BSGP Technologies – 10s promo video

`bsgptech-demo.mp4`: 1920×1080, 30 fps, 10 s, H.264 with a silent AAC track.

| Time | Scene |
|------|-------|
| 0.0–1.4s | Intro: logo + "Learn. Innovate. Build. Sell." over the site hero |
| 1.4–3.0s | 01 Solution Development (homepage + service card) |
| 3.0–4.6s | 02 Training & Capacity Building (scrolling /training course catalogue) |
| 4.6–6.2s | 03 Engineering Design (CAD course imagery + service card) |
| 6.2–7.8s | 04 Consultancy (site team photo + service card) |
| 7.8–10s | Call to action: WhatsApp, phone, email, bsgptech.com |

All screenshots in `assets/` were captured from https://bsgptech.com/ with headless Chromium.

## Editing and re-rendering

- Contact details live in the `CONTACT` object at the top of `scene.html`.
- Scene timings are in `SCENES` in `scene.html`.
- Open `scene.html?t=8.5` in a browser to preview any moment.

```sh
node render.mjs                 # writes bsgptech-demo.mp4
PREVIEW=1 node render.mjs       # writes still frames to preview/
```

Requires Node, ffmpeg and Playwright (set `PLAYWRIGHT=/path/to/playwright/index.mjs` if it is not importable as `playwright`).

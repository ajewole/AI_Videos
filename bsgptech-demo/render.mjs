// Renders scene.html frame-by-frame with headless Chromium and encodes it with ffmpeg.
// Usage: node render.mjs [output.mp4] [fps]
//   PLAYWRIGHT=/path/to/playwright/index.mjs to override the Playwright location.
//   PREVIEW=1 writes a few still frames to ./preview instead of a video.
import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const pwPath = process.env.PLAYWRIGHT || '/opt/node-tools/node_modules/playwright/index.mjs';
const { chromium } = await import(pathToFileURL(pwPath).href).catch(() => import('playwright'));

const out = resolve(process.argv[2] || resolve(here, 'bsgptech-demo.mp4'));
const fps = Number(process.argv[3] || 30);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(pathToFileURL(resolve(here, 'scene.html')).href);
await page.evaluate(() => document.fonts.ready);
await page.waitForFunction(() => [...document.images].every(i => i.complete));
const duration = await page.evaluate(() => window.DURATION);

if (process.env.PREVIEW) {
  mkdirSync(resolve(here, 'preview'), { recursive: true });
  for (const t of [0.9, 2.4, 4.0, 5.6, 7.2, 9.5]) {
    await page.evaluate(t => renderFrame(t), t);
    await page.screenshot({ path: resolve(here, 'preview', `t${t.toFixed(1)}.png`) });
  }
  await browser.close();
  process.exit(0);
}

const ff = spawn('ffmpeg', [
  '-y', '-loglevel', 'error',
  '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
  // silent stereo track so social platforms accept the upload
  '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000',
  '-shortest',
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p',
  '-c:a', 'aac', '-b:a', '128k',
  '-movflags', '+faststart', out,
], { stdio: ['pipe', 'inherit', 'inherit'] });

const total = Math.round(duration * fps);
for (let f = 0; f < total; f++) {
  await page.evaluate(t => renderFrame(t), f / fps);
  const buf = await page.screenshot({ type: 'png' });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
}
ff.stdin.end();
await new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg exited ' + c)))));
await browser.close();
console.log(`Wrote ${out} (${total} frames @ ${fps}fps)`);

// Renders scene.html frame-by-frame with headless Chromium and encodes it with ffmpeg.
// Usage: node render.mjs [format ...]     formats: landscape vertical square portrait (default: all)
//   CUT=30                       30-second cut (default 10); outputs get a -30s suffix
//   FPS=30                       frame rate
//   PLAYWRIGHT=/path/index.mjs   override the Playwright location
//   PREVIEW=1                    write a few still frames to ./preview instead of videos
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const pwPath = process.env.PLAYWRIGHT || '/opt/node-tools/node_modules/playwright/index.mjs';
const { chromium } = await import(pathToFileURL(pwPath).href).catch(() => import('playwright'));

const OUTPUTS = {
  landscape: 'bsgptech-demo-16x9.mp4',
  vertical: 'bsgptech-demo-9x16.mp4',
  square: 'bsgptech-demo-1x1.mp4',
  portrait: 'bsgptech-demo-4x5.mp4',
};
const formats = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(OUTPUTS);
const fps = Number(process.env.FPS || 30);
const cut = process.env.CUT || '10';
const suffix = cut === '10' ? '' : `-${cut}s`;
const music = resolve(here, `music${suffix}.wav`);

const browser = await chromium.launch();
await Promise.all(formats.map(render));
await browser.close();

async function render(format) {
  if (!OUTPUTS[format]) throw new Error(`Unknown format "${format}"`);
  const page = await browser.newPage({ viewport: { width: 1920, height: 1920 } });
  await page.goto(pathToFileURL(resolve(here, 'scene.html')).href + `?format=${format}&cut=${cut}`);
  const { w, h } = await page.evaluate(f => window.FORMATS[f], format);
  await page.setViewportSize({ width: w, height: h });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForFunction(() => [...document.images].every(i => i.complete));
  const duration = await page.evaluate(() => window.DURATION);

  if (process.env.PREVIEW) {
    mkdirSync(resolve(here, 'preview'), { recursive: true });
    // one still near the end of each scene, once its animations have settled
    const times = await page.evaluate(() => window.SCENES.map(([, a, b]) => a + (b - a) * 0.8));
    for (const t of times) {
      await page.evaluate(t => renderFrame(t), t);
      await page.screenshot({ path: resolve(here, 'preview', `${format}${suffix}-t${t.toFixed(1)}.png`) });
    }
    await page.close();
    return;
  }

  const out = resolve(here, OUTPUTS[format].replace('.mp4', `${suffix}.mp4`));
  const ff = spawn('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
    // background music from music.py, or a silent track so platforms still accept the upload
    ...(existsSync(music) ? ['-i', music] : ['-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000']),
    '-shortest',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '192k',
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
  await page.close();
  console.log(`Wrote ${out} (${w}x${h}, ${total} frames @ ${fps}fps)`);
}

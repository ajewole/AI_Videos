// Renders scene.html frame-by-frame with headless Chromium and encodes it with ffmpeg.
// Usage: node render.mjs [format ...]     formats: landscape vertical square portrait (default: all)
//   FPS=30                       frame rate
//   PLAYWRIGHT=/path/index.mjs   override the Playwright location
//   PREVIEW=1                    write a still of every scene to ./preview instead of videos
// Audio: voice.wav (voiceover.py) over music.wav (music.py), with the music ducked under the voice.
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const pwPath = process.env.PLAYWRIGHT || '/opt/node-tools/node_modules/playwright/index.mjs';
const { chromium } = await import(pathToFileURL(pwPath).href).catch(() => import('playwright'));

const OUTPUTS = {
  vertical: 'body-warning-signs-9x16.mp4',
  landscape: 'body-warning-signs-16x9.mp4',
  portrait: 'body-warning-signs-4x5.mp4',
  square: 'body-warning-signs-1x1.mp4',
};
const formats = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(OUTPUTS);
const fps = Number(process.env.FPS || 30);
const mix = resolve(here, '.cache', 'mix.wav');

const run = args => new Promise((res, rej) => {
  const p = spawn('ffmpeg', ['-y', '-loglevel', 'error', ...args], { stdio: 'inherit' });
  p.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg exited ' + c))));
});

if (!process.env.PREVIEW) {
  mkdirSync(dirname(mix), { recursive: true });
  // music sits ~16 dB under the narration and ducks further while the voice is speaking
  await run(['-i', resolve(here, 'voice.wav'), '-i', resolve(here, 'music.wav'), '-filter_complex',
    '[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[v1][v2];' +
    '[1:a]volume=0.22[m];[m][v1]sidechaincompress=threshold=0.02:ratio=4:attack=20:release=450[md];' +
    '[v2][md]amix=inputs=2:normalize=0:duration=longest,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]',
    '-map', '[a]', mix]);
}

const browser = await chromium.launch();
await Promise.all(formats.map(render));
await browser.close();

async function render(format) {
  if (!OUTPUTS[format]) throw new Error(`Unknown format "${format}"`);
  const page = await browser.newPage({ viewport: { width: 1920, height: 1920 } });
  await page.goto(pathToFileURL(resolve(here, 'scene.html')).href + '?format=' + format);
  const { w, h } = await page.evaluate(f => window.FORMATS[f], format);
  await page.setViewportSize({ width: w, height: h });
  await page.evaluate(() => document.fonts.ready);
  const duration = await page.evaluate(() => window.DURATION);

  if (process.env.PREVIEW) {
    mkdirSync(resolve(here, 'preview'), { recursive: true });
    const times = process.env.TIMES ? process.env.TIMES.split(',').map(Number) : await page.evaluate(() => window.PREVIEW_TIMES);
    for (const t of times) {
      await page.evaluate(t => renderFrame(t), t);
      await page.screenshot({ path: resolve(here, 'preview', `${format}-t${t.toFixed(1).padStart(5, '0')}.png`) });
    }
    await page.close();
    return;
  }

  const out = resolve(here, OUTPUTS[format]);
  const ff = spawn('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
    '-i', mix,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '192k', '-shortest',
    '-movflags', '+faststart', out,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });

  const total = Math.round(duration * fps);
  for (let f = 0; f < total; f++) {
    await page.evaluate(t => renderFrame(t), f / fps);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 300 === 0) console.log(`${format}: ${(f / total * 100).toFixed(0)}%`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg exited ' + c)))));
  await page.close();
  console.log(`Wrote ${out} (${w}x${h}, ${total} frames @ ${fps}fps)`);
}

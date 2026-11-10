// Render an animated HTML template to MP4 (H.264, 30fps), frame by frame.
// Usage: node render_video.mjs <page.html> <out.mp4> <seconds> [audio.wav]
// The page must define window.render(t) (t in seconds).
import puppeteer from "puppeteer-core";
import chromium from "@sparticuz/chromium";
import { spawn } from "node:child_process";
import { pathToFileURL } from "node:url";
import path from "node:path";

// Optional 5th and 6th args: first frame and end frame (exclusive), to render a chunk in parallel (pass "" as audio).
const [, , input, output, secs, audio, f0, f1] = process.argv;
const FPS = 30, W = 1080, H = 1920, N = Math.round(Number(secs) * FPS);
const A = f0 ? Number(f0) : 0, Z = f1 ? Number(f1) : N;
const browser = await puppeteer.launch({
  args: [...chromium.args, "--font-render-hinting=none"],
  executablePath: await chromium.executablePath(),
  headless: true,
  defaultViewport: { width: W, height: H, deviceScaleFactor: 1 },
});
const page = await browser.newPage();
await page.goto(pathToFileURL(path.resolve(input)).href, { waitUntil: "networkidle0" });
await page.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map(i => i.decode().catch(() => {}))); });

const args = ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-"];
if (audio) args.push("-i", audio);
args.push("-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", String(FPS));
if (audio) args.push("-c:a", "aac", "-b:a", "160k", "-shortest");
args.push("-movflags", "+faststart", output);
const ff = spawn("ffmpeg", args, { stdio: ["pipe", "ignore", "inherit"] });

for (let i = A; i < Z; i++) {
  await page.evaluate((t) => window.render(t), i / FPS);
  const buf = await page.screenshot({ type: "jpeg", quality: 92 });
  if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
}
ff.stdin.end();
await new Promise((r) => ff.on("close", r));
await browser.close();
console.log("wrote", output, Z - A, "frames");

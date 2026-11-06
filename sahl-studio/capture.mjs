// Capture a local showcase page as Reel frames, fully offline.
// Usage: node capture.mjs <page.html> <site-key>
// Writes frames/<site>_tall.png (375 wide, full page), frames/<site>_header.png
// (the sticky header strip) and frames/<site>_top.png (first screen), then prints
// {tallH, headerH, scrollTo} as JSON for the week/day file.
import puppeteer from "puppeteer-core";
import chromium from "@sparticuz/chromium";
import { pathToFileURL } from "node:url";
import path from "node:path";

const [, , input, site] = process.argv;
if (!input || !site) { console.error("usage: node capture.mjs <page.html> <site>"); process.exit(1); }
const browser = await puppeteer.launch({
  args: [...chromium.args, "--font-render-hinting=none"],
  executablePath: await chromium.executablePath(),
  headless: true,
  defaultViewport: { width: 375, height: 812, deviceScaleFactor: 2 },
});
const page = await browser.newPage();
await page.goto(pathToFileURL(path.resolve(input)).href, { waitUntil: "networkidle0" });
await page.evaluate(() => document.fonts.ready);
// Reveal scroll animations so nothing stays hidden in the full-page shot.
await page.addStyleTag({ content: "*{animation:none!important;transition:none!important}.reveal,[data-reveal]{opacity:1!important;transform:none!important}" });
await page.evaluate(async () => {
  for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
  window.scrollTo(0, 0);
});
await new Promise(r => setTimeout(r, 300));
const headerH = await page.evaluate(() => {
  const h = document.querySelector("[data-sticky], header.top, nav.top, .topbar");
  return h ? Math.round(h.getBoundingClientRect().height) : 64;
});
await page.screenshot({ path: `frames/${site}_top.png`, type: "png" });
await page.screenshot({ path: `frames/${site}_header.png`, type: "png", clip: { x: 0, y: 0, width: 375, height: headerH } });
await page.screenshot({ path: `frames/${site}_tall2x.png`, type: "png", fullPage: true });
await browser.close();
// build_reels.py expects a 375-wide tall image.
const { execFileSync } = await import("node:child_process");
const out = execFileSync("python3", ["-c", `
from PIL import Image
im = Image.open("frames/${site}_tall2x.png").convert("RGB")
w, h = im.size
im = im.resize((375, round(h * 375 / w)), Image.LANCZOS)
im.save("frames/${site}_tall.png")
hd = Image.open("frames/${site}_header.png").convert("RGB")
hd.resize((375, round(hd.size[1] * 375 / hd.size[0])), Image.LANCZOS).save("frames/${site}_header.png")
import os; os.remove("frames/${site}_tall2x.png")
print(im.size[1])
`]).toString().trim();
const tallH = Number(out);
console.log(JSON.stringify({ site, tallH, headerH, scrollTo: Math.max(0, Math.min(tallH - 812, 3300)) }));

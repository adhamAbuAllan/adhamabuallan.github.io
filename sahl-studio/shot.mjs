// Render an HTML file to PNG with headless Chromium.
// Usage: node shot.mjs <input.html> <output.png> <width> <height>
import puppeteer from "puppeteer-core";
import chromium from "@sparticuz/chromium";
import { pathToFileURL } from "node:url";
import path from "node:path";

const [, , input, output, w = "1080", h = "1350"] = process.argv;
const browser = await puppeteer.launch({
  args: [...chromium.args, "--font-render-hinting=none"],
  executablePath: await chromium.executablePath(),
  headless: true,
  defaultViewport: { width: Number(w), height: Number(h), deviceScaleFactor: 1 },
});
const page = await browser.newPage();
await page.goto(pathToFileURL(path.resolve(input)).href, { waitUntil: "networkidle0" });
await page.evaluate(() => document.fonts.ready);
await page.screenshot({ path: output, type: "png" });
await browser.close();
console.log("wrote", output);

"""Build showcase Reels from stitched site captures.
Usage: WEEK_JSON=weeks/w45.json OUT=out/w45 python3 build_reels.py [P08 P10 ...]
Each post needs: code, site (frames/<site>_tall.png + _header.png), chip, hook_html, sub, note; optional scroll_to."""
import json, subprocess, sys, os
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from sfx import make_track

S = 612 / 375
OUT = os.environ.get("OUT", "out/week1")
os.makedirs(OUT, exist_ok=True)
D = json.load(open(os.environ.get("WEEK_JSON", "week1.json")))
SCROLL = {"barber": 3300, "dental": 3300, "restaurant": 2900}
END = {"title": "بدك موقع زي هذا لمصلحتك؟", "cta": "راسلنا عالواتساب", "small": "الرابط بأول تعليق"}


def upscale(src, dst):
    im = Image.open(src).convert("RGB")
    w = 612
    h = round(im.size[1] * w / im.size[0])
    im = im.resize((w, h), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.4, percent=70, threshold=2))
    im.save(dst, quality=93)
    return h


def build_showcase(p, seconds=15.0):
    site = p["site"]
    tall = f"{OUT}/{site}_tall_up.jpg"
    hdr = f"{OUT}/{site}_hdr_up.jpg"
    upscale(f"frames/{site}_tall.png", tall)
    upscale(f"frames/{site}_header.png", hdr)
    tall_h = Image.open(f"frames/{site}_tall.png").size[1]
    cfg = {
        "chip": p["chip"], "hook": p["hook_html"], "sub": p["sub"], "note": p["note"],
        "endTitle": END["title"], "cta": END["cta"], "endSmall": END["small"],
        "tall": tall, "header": hdr, "tallH": tall_h, "scrollTo": p.get("scroll_to", SCROLL.get(site, 3000)),
        "segments": [[1.4, 4.4, 0, 0.34], [5.0, 8.0, 0.34, 0.68], [8.6, 11.2, 0.68, 1.0]],
        "tapAt": 999, "tapX": 0, "tapY": 0, "endAt": 11.8,
    }
    tpl = open("tpl_showcase.html").read()
    html = tpl.replace("<body>", "<body>\n<script>window.__CFG__ = " + json.dumps(cfg, ensure_ascii=False) + ";</script>", 1)
    page = f"reel_{p['code']}.html"
    open(page, "w").write(html)
    wav = f"{OUT}/{p['code']}.wav"
    make_track([("pop", 0.1), ("whoosh", 1.35), ("whoosh", 4.95), ("whoosh", 8.55), ("pop", 11.85), ("click", 12.3)], seconds, wav)
    mp4 = f"{OUT}/{p['code']}.mp4"
    subprocess.run(["node", "render_video.mjs", page, mp4, str(seconds), wav], check=True)
    return mp4


if __name__ == "__main__":
    want = sys.argv[1:] or [p["code"] for p in D["posts"] if p["format"] == "showcase-reel"]
    for p in D["posts"]:
        if p["code"] in want and p["format"] == "showcase-reel":
            print(build_showcase(p))

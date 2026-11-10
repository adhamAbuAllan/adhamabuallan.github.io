"""Studio Reel: one 15 s vertical Reel (1080x1920, sound included) in the Sahl "Studio" style from one spec file.

Usage:  python3 studio_reel.py spec.json [out.mp4]

spec.json (only `hook_html` and one source are required):
{
  "name": "bakery",                       # short key, letters/digits/dashes; also the default output name
  "page": "../sahl/s/sweets/index.html",  # SOURCE A: a local HTML page or an http(s) URL, captured at phone width
  "screenshot": "shots/home.png",         # SOURCE B: one tall phone screenshot (any width); optional "header_px": 64
  "site": "sweets",                       # SOURCE C: frames already captured in frames/<site>_*
  "chip": "مثال من شغلنا",
  "hook_html": "طلبيات <span class=\"em\">المناسبات</span> بتضيع؟",   # 8 words or fewer, exactly one .em word
  "sub": "one or two lines under the hook",
  "points": ["card 1", "card 2", "card 3"],                            # 2 to 4 words each
  "notif": "زبون جديد حجز صدر كنافة", "notif_app": "واتساب", "notif_now": "هسا",
  "end_title": "بدك صفحة زي هاي لمحلك؟", "cta": "احكي معنا عالواتساب",
  "note": "صفحة جاهزة خلال 24 ساعة", "end_small": "الرابط بالوصف",
  "scroll_to": 3100,                      # optional, page px to scroll to (default: near the bottom)
  "flip": 0,                              # optional 0/1: which side the phone tilts and the first card enters from
  "brand": {"logo": "/abs/logo.svg", "accent": "#22C55E", "on_accent": "#052E16", "dir": "rtl", "lang": "ar",
            "cta_icon": "whatsapp", "notif_icon": "whatsapp"}          # all optional; defaults are Sahl's
}
Prints the mp4 path, then writes <out>.sheet.jpg (6 frames) so the result can be checked by eye."""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    spec_path = os.path.abspath(sys.argv[1])
    spec = json.load(open(spec_path))
    base = os.path.dirname(spec_path)
    absp = lambda x: x if re.match(r"^https?:", x) or os.path.isabs(x) else os.path.normpath(os.path.join(base, x))
    name = re.sub(r"[^A-Za-z0-9_-]", "-", spec.get("name") or spec.get("site") or "reel")
    out = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(base, name + ".mp4")
    if "brand" in spec and spec["brand"].get("logo"): spec["brand"]["logo"] = absp(spec["brand"]["logo"])
    words = len(re.sub(r"<[^>]+>", " ", spec["hook_html"]).split())
    if words > 8: print(f"warning: the hook has {words} words; 8 or fewer reads in 2 seconds", file=sys.stderr)
    if spec["hook_html"].count('class="em"') != 1: print("warning: the hook should have exactly one <span class=\"em\"> word", file=sys.stderr)
    for x in spec.get("points", []):
        if len(x) > 24: print(f"warning: card text is long and may be cut at the edge: {x}", file=sys.stderr)

    os.chdir(HERE)
    os.makedirs("frames", exist_ok=True)
    site = spec.get("site") or name
    if spec.get("page"):
        r = subprocess.run(["node", "capture.mjs", absp(spec["page"]), site], check=True, capture_output=True, text=True)
        info = json.loads(r.stdout.strip().splitlines()[-1])
        spec.setdefault("scroll_to", info["scrollTo"])
    elif spec.get("screenshot"):
        from PIL import Image
        im = Image.open(absp(spec["screenshot"])).convert("RGB")
        w, h = im.size
        im.resize((750, round(h * 750 / w)), Image.LANCZOS).save(f"frames/{site}_tall2x.jpg", quality=90)
        small = im.resize((375, round(h * 375 / w)), Image.LANCZOS)
        small.save(f"frames/{site}_tall.png")
        hp = max(1, int(spec.get("header_px", 0) * 750 / w)) if spec.get("header_px") else 1
        Image.open(f"frames/{site}_tall2x.jpg").crop((0, 0, 750, hp)).save(f"frames/{site}_header2x.png")
        small.crop((0, 0, 375, max(1, hp // 2))).save(f"frames/{site}_header.png")
        spec.setdefault("scroll_to", max(0, small.size[1] - 812))
    elif not os.path.exists(f"frames/{site}_tall.png"):
        sys.exit("spec needs one source: page, screenshot, or a site already in frames/")

    tmp = os.path.join(os.path.dirname(out), f".{name}_build")
    os.makedirs(tmp, exist_ok=True)
    os.environ["OUT"] = tmp
    os.environ.setdefault("WEEK_JSON", "week1.json")
    import build_reels
    post = dict(spec, code=name, site=site, chip=spec.get("chip", "مثال من شغلنا"))
    if "flip" in spec: post["_flip"] = spec["flip"]
    mp4 = build_reels.build_showcase_v2(post)
    os.replace(mp4, out)
    sheet = out + ".sheet.jpg"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out, "-vf",
                    "select='eq(n,45)+eq(n,105)+eq(n,195)+eq(n,270)+eq(n,300)+eq(n,400)',scale=360:-1,tile=6x1", "-frames:v", "1", "-vsync", "0", sheet], check=True)
    import shutil; shutil.rmtree(tmp, ignore_errors=True)
    print(out)
    print(sheet)


if __name__ == "__main__":
    main()

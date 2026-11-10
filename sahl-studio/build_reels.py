"""Build showcase Reels from stitched site captures.
Usage: WEEK_JSON=weeks/w45.json OUT=out/w45 python3 build_reels.py [P08 P10 ...]
Each post needs: code, site (frames/<site>_tall.png + _header.png), chip, hook_html, sub, note; optional scroll_to.
Style: "v2" (default, the Studio style: kinetic hook, 3D phone, white cards, WhatsApp moment, music bed) also reads
points [3 short benefit lines for the white cards] and notif (the WhatsApp notification line).
Set "style": "classic" on a post to get the old flat style."""
import json, subprocess, sys, os
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from sfx import make_track, make_track_v2

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
        "endTitle": END["title"], "cta": END["cta"], "endSmall": p.get("end_small", END["small"]),
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


B = 0.625  # one beat at 96 BPM; every cut sits on this grid
V2_POINTS = ["الخدمات والأسعار واضحة", "الطلب بكبسة عالواتساب", "صفحتك شغالة 24 ساعة"]
V2_END = {"title": "بدك صفحة زي هاي لمحلك؟", "cta": "احكي معنا عالواتساب"}


def fit_width(src, dst, w):
    im = Image.open(src).convert("RGB")
    h = round(im.size[1] * w / im.size[0])
    up = im.size[0] < w
    im = im.resize((w, h), Image.LANCZOS)
    if up: im = im.filter(ImageFilter.UnsharpMask(radius=1.4, percent=70, threshold=2))
    im.save(dst, quality=93)


def niche_colors(tall_png):
    """Two glow colors taken from the page itself, so every niche gets its own mood."""
    import colorsys
    im = Image.open(tall_png).convert("RGB")
    im = im.crop((0, 0, im.size[0], min(im.size[1], 2400))).resize((60, 240))
    q = im.quantize(8, kmeans=2).convert("RGB")
    cand = []
    for n, (r, g, b) in q.getcolors(60 * 240):
        h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if s > 0.22 and 0.12 < l < 0.85: cand.append((s * (n ** 0.35), h, l, s))
    cand.sort(reverse=True)
    if not cand: return "#22C55E", "#15803D"
    def hexc(h, l, s):
        r, g, b = colorsys.hls_to_rgb(h, min(0.56, max(0.42, l)), min(0.85, max(0.55, s)))
        return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))
    c1 = cand[0]
    c2 = next((c for c in cand[1:] if min(abs(c[1] - c1[1]), 1 - abs(c[1] - c1[1])) > 0.08), None)
    return hexc(*c1[1:]), (hexc(*c2[1:]) if c2 else "#22C55E")


def build_showcase_v2(p, seconds=15.0):
    site, code = p["site"], p["code"]
    src_tall = f"frames/{site}_tall2x.jpg" if os.path.exists(f"frames/{site}_tall2x.jpg") else f"frames/{site}_tall.png"
    src_hdr = f"frames/{site}_header2x.png" if os.path.exists(f"frames/{site}_header2x.png") else f"frames/{site}_header.png"
    tall, hdr = f"{OUT}/{site}_tall_v2.jpg", f"{OUT}/{site}_hdr_v2.jpg"
    fit_width(src_tall, tall, 1100)        # 2x the 550 px screen, so the tilted phone stays sharp
    fit_width(src_hdr, hdr, 1100)
    tall_h = Image.open(f"frames/{site}_tall.png").size[1]
    r, g, b = Image.open(f"frames/{site}_tall.png").convert("RGB").getpixel((6, 3))
    c1, c2 = niche_colors(f"frames/{site}_tall.png")
    points = [x for x in p.get("points", []) if x][:3] or V2_POINTS
    hook_words = len(p["hook_html"].replace("<span class=\"em\">", " ").replace("</span>", " ").split())
    num = int("".join(ch for ch in code if ch.isdigit()) or 0)
    t = {"hook0": 0.12, "wordGap": 0.11, "underline": 0.12 + hook_words * 0.11 + 0.15, "move": 4 * B - 0.3,
         "cards": [6 * B, 9 * B, 12 * B][: len(points)], "cardsOut": 15 * B, "notif": 15.5 * B, "end": 18 * B,
         "cta": 18 * B + 0.95, "tap": 21 * B}
    br = p.get("brand", {})   # optional: reuse the style for another brand or language
    cfg = {
        "chip": p["chip"], "hook": p["hook_html"], "sub": p.get("sub", ""), "note": p.get("note", "صفحة جاهزة خلال 24 ساعة"),
        "endTitle": p.get("end_title", V2_END["title"]), "cta": p.get("cta", V2_END["cta"]), "endSmall": p.get("end_small", "الرابط بالوصف"),
        "points": points, "notif": p.get("notif", "زبون جديد بعتلك طلبه"), "notifApp": p.get("notif_app", "واتساب"), "notifNow": p.get("notif_now", "هسا"),
        "dir": br.get("dir", "rtl"), "lang": br.get("lang", ""), "accent": br.get("accent", "#22C55E"), "onAccent": br.get("on_accent", "#052E16"),
        "logo": br.get("logo", "out/brand/sahl-wordmark.svg"), "ctaIcon": br.get("cta_icon", "whatsapp"), "notifIcon": br.get("notif_icon", "whatsapp"),
        "tall": tall, "header": hdr, "tallH": tall_h, "scrollTo": p.get("scroll_to", SCROLL.get(site, 3000)),
        "segments": [[5 * B, 8.4 * B, 0, 0.36], [9.2 * B, 11.6 * B, 0.36, 0.7], [12.2 * B, 14.8 * B, 0.7, 1.0]],
        "statusBg": "#%02X%02X%02X" % (r, g, b), "statusFg": "#0B0F0D" if (r * 299 + g * 587 + b * 114) / 1000 > 150 else "#FFFFFF",
        "c1": c1, "c2": c2, "flip": p.get("_flip", num % 2), "t": t,
    }
    html = open("tpl_reel_v2.html").read().replace("<body>", "<body>\n<script>window.__CFG__ = " + json.dumps(cfg, ensure_ascii=False) + ";</script>", 1)
    page = f"reel_{code}.html"
    open(page, "w").write(html)
    ev = [("thud", 0.0)] + [("tick", t["hook0"] + i * t["wordGap"]) for i in range(hook_words)] + [("swish", t["underline"])]
    ev += [("whoosh", t["move"])] + [("pop", c + 0.03) for c in t["cards"]]
    ev += [("swish", s[0]) for s in cfg["segments"]]
    ev += [("ding", t["notif"] + 0.05), ("chime", t["notif"] + 0.17), ("rise", t["end"] - 1.05), ("thud", t["end"] - 0.05), ("whoosh", t["end"] - 0.2),
           ("pop", t["cta"] + 0.05), ("click", t["tap"]), ("pop", t["tap"] + 0.06)]
    wav = f"{OUT}/{code}.wav"
    make_track_v2(ev, seconds, wav, end_at=t["end"])
    mp4 = f"{OUT}/{code}.mp4"
    render_parallel(page, mp4, seconds, wav)
    os.remove(page)
    return mp4


def render_parallel(page, mp4, seconds, wav, fps=30):
    """Render the page in one chunk per CPU core (max 4), then join the chunks and add the sound."""
    n = round(seconds * fps)
    k = max(1, min(4, os.cpu_count() or 1))
    cuts = [round(n * i / k) for i in range(k + 1)]
    parts = [f"{mp4}.part{i}.mp4" for i in range(k)]
    procs = [subprocess.Popen(["node", "render_video.mjs", page, parts[i], str(seconds), "", str(cuts[i]), str(cuts[i + 1])]) for i in range(k)]
    if any(pr.wait() != 0 for pr in procs): raise RuntimeError("render failed")
    lst = mp4 + ".txt"
    open(lst, "w").write("".join(f"file '{os.path.abspath(x)}'\n" for x in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", mp4], check=True)
    for x in parts + [lst]: os.remove(x)


if __name__ == "__main__":
    want = sys.argv[1:] or [p["code"] for p in D["posts"] if p["format"] == "showcase-reel"]
    for p in D["posts"]:
        if p["code"] in want and p["format"] == "showcase-reel":
            print(build_showcase(p) if p.get("style") == "classic" else build_showcase_v2(p))

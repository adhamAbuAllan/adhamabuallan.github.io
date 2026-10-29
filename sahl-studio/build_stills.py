"""Render still posts (carousel, before/after, price card) and brand images.
Usage: WEEK_JSON=weeks/w45.json OUT=out/w45 python3 build_stills.py   (add --brand to also redo cover + profile)"""
import json, subprocess, os
D = json.load(open(os.environ.get("WEEK_JSON", "week1.json")))
OUT = os.environ.get("OUT", "out/week1")
os.makedirs(OUT, exist_ok=True)
os.makedirs("out/brand", exist_ok=True)

HEAD = """<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><link rel="stylesheet" href="brand.css"><style>
body{width:%dpx;height:%dpx;overflow:hidden;position:relative}
.grid{position:absolute;inset:0;background-image:radial-gradient(var(--line) 1.5px,transparent 1.5px);background-size:48px 48px;opacity:.55}
.wm{position:absolute;bottom:56px;left:64px;height:72px}
.count{position:absolute;bottom:70px;right:72px;font:600 30px Inter,sans-serif;color:var(--muted);direction:ltr}
%s</style></head><body><div class="grid"></div>%s</body></html>"""


def shot(html, name, w, h):
    path = "_tmp_" + os.path.basename(name) + ".html"
    open(path, "w").write(html)
    subprocess.run(["node", "shot.mjs", path, name, str(w), str(h)], check=True, capture_output=True)
    return name


def carousel(p):
    css = """
.c{position:absolute;inset:0;padding:120px 88px;display:flex;flex-direction:column;justify-content:center}
.big{font-size:104px;line-height:1.15;font-weight:700;margin:0}
.lead{font-size:44px;color:var(--muted);margin-top:40px;font-weight:500}
.n{font:800 220px/1 Inter,sans-serif;color:var(--emerald);margin-bottom:24px}
.t{font-size:84px;line-height:1.2;font-weight:700;margin:0}
.b{font-size:46px;line-height:1.6;color:var(--muted);margin-top:36px;font-weight:500}
.cta{display:inline-block;margin-top:56px;background:var(--emerald);color:var(--on-emerald);font-size:46px;font-weight:700;padding:26px 52px;border-radius:999px;align-self:flex-start}
"""
    files = []
    n = len(p["slides"])
    for i, s in enumerate(p["slides"], start=1):
        if s["type"] == "cover":
            body = f'<div class="c"><h1 class="big">{s["title"]}</h1><div class="lead">{s["sub"]} ←</div></div>'
        elif s["type"] == "tip":
            body = f'<div class="c"><div class="n">{s["n"]}</div><h2 class="t">{s["title"]}</h2><div class="b">{s["body"]}</div></div>'
        else:
            body = f'<div class="c"><h1 class="big">{s["title"]}</h1><div class="b">{s["sub"]}</div><div class="cta">راسلنا عالواتساب</div></div>'
        body += f'<img class="wm" src="out/brand/sahl-wordmark.svg"><div class="count">{i} / {n}</div>'
        files.append(shot(HEAD % (1080, 1350, css, body), f"{OUT}/{p['code']}_{i}.png", 1080, 1350))
    return files


def before_after(p):
    css = """
.h{position:absolute;top:96px;right:80px;left:80px;font-size:72px;line-height:1.25;font-weight:700;margin:0}
.tag{position:absolute;top:96px;left:80px;font-size:26px;color:var(--muted);border:2px solid var(--line);padding:6px 18px;border-radius:999px}
.cols{position:absolute;top:360px;left:64px;right:64px;bottom:170px;display:flex;gap:28px}
.col{flex:1;border-radius:32px;background:var(--surface);border:2px solid var(--line);padding:28px;position:relative;overflow:hidden}
.lbl{font-size:40px;font-weight:700;margin-bottom:22px}
.before .lbl{color:var(--muted)} .after .lbl{color:var(--emerald)}
.bub{background:#1F2C34;color:#E9EDEF;font-size:32px;padding:16px 22px;border-radius:22px;margin:0 0 18px;width:fit-content;max-width:100%}
.bub:nth-child(odd){margin-right:40px}
.post{height:150px;border-radius:18px;background:var(--surface-2);margin-bottom:18px;display:grid;place-items:center;color:var(--muted);font-size:28px}
.shot{position:absolute;top:96px;left:28px;right:28px;bottom:28px;border-radius:22px;overflow:hidden}
.shot img{width:100%;display:block}
"""
    bubbles = "".join(f'<div class="bub">{x}</div>' for x in p["before_lines"])
    body = (f'<h1 class="h">{p["headline"]}</h1><div class="tag">{p["tag"]}</div><div class="cols">'
            f'<div class="col before"><div class="lbl">{p["before_title"]}</div>{bubbles}</div>'
            f'<div class="col after"><div class="lbl">{p["after_title"]}</div><div class="shot"><img src="frames/restaurant_top.png"></div></div>'
            f'</div><img class="wm" src="out/brand/sahl-wordmark.svg">')
    return [shot(HEAD % (1080, 1350, css, body), f"{OUT}/{p['code']}.png", 1080, 1350)]


def price_card(p):
    css = """
.c{position:absolute;inset:0;padding:110px 88px}
.h{font-size:84px;line-height:1.2;font-weight:700;margin:0}
.price{margin-top:56px;display:flex;align-items:baseline;gap:20px}
.price b{font:800 170px/1 Inter,sans-serif;color:var(--emerald);direction:ltr}
.price span{font-size:52px;color:var(--muted);font-weight:600}
ul{list-style:none;padding:0;margin:56px 0 0}
li{font-size:48px;line-height:1.3;padding:20px 0;border-top:2px solid var(--line);display:flex;align-items:center;gap:24px;font-weight:500}
li:last-child{border-bottom:2px solid var(--line)}
li i{width:44px;height:44px;border-radius:50%;background:var(--emerald);display:grid;place-items:center;flex:none}
li i svg{width:26px;height:26px}
.f{margin-top:44px;font-size:40px;color:var(--muted);font-weight:500}
"""
    check = '<svg viewBox="0 0 24 24" fill="none" stroke="#052E16" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'
    items = "".join(f"<li><i>{check}</i>{x}</li>" for x in p["items"])
    body = (f'<div class="c"><h1 class="h">{p["headline"]}</h1><div class="price"><b>{p["price"]}</b><span>{p["price_note"]}</span></div>'
            f'<ul>{items}</ul><div class="f">{p["foot"]}</div></div><img class="wm" src="out/brand/sahl-wordmark.svg">')
    return [shot(HEAD % (1080, 1350, css, body), f"{OUT}/{p['code']}.png", 1080, 1350)]


def cover():
    # Facebook cover 1640x624: promise and proof in the upper middle, CTA low in the centre (mobile web hides it
    # behind the centred profile picture, so nothing is ever half covered), two showcase phones at the edges.
    css = """
.txt{position:absolute;top:104px;bottom:0;left:380px;right:380px;display:flex;flex-direction:column;justify-content:flex-start;align-items:center;text-align:center}
.k{font-size:28px;color:var(--emerald);font-weight:600;margin-bottom:14px}
.h{font-size:76px;line-height:1.15;font-weight:700;margin:0}
.s{font-size:34px;color:var(--muted);margin-top:18px;font-weight:500}
.cta{margin-top:112px;background:var(--emerald);color:var(--on-emerald);font-size:32px;font-weight:700;padding:16px 36px;border-radius:999px}
.ph{position:absolute;width:250px;height:520px;border-radius:40px;background:var(--surface-2);padding:9px;box-shadow:0 0 0 2px var(--line)}
.ph div{width:100%;height:100%;border-radius:32px;overflow:hidden}
.ph img{width:100%;display:block}
"""
    phones = "".join(f'<div class="ph" style="left:{x}px;top:{y}px"><div><img src="frames/{s}_top.png"></div></div>'
                     for s, x, y in [("restaurant", 60, 80), ("barber", 1330, 40)])
    body = (f'{phones}<div class="txt"><div class="k">Sahl Digital · سهل</div><h1 class="h">مصلحتك أونلاين، <span class="em">بسهولة</span></h1>'
            f'<div class="s">صفحة لمصلحتك جاهزة خلال 24 ساعة</div><div class="cta">راسلنا عالواتساب</div></div>')
    return shot(HEAD % (1640, 624, css, body), "out/brand/sahl-cover.png", 1640, 624)


def profile():
    css = "body{background:#0A0A0A}.g{display:none}img.m{position:absolute;inset:0;width:1080px;height:1080px}"
    body = '<img class="m" src="out/brand/sahl-mark.svg">'
    return shot(HEAD % (1080, 1080, css, body), "out/brand/sahl-profile.png", 1080, 1080)


if __name__ == "__main__":
    for p in D["posts"]:
        if p["format"] == "tips-carousel": print(carousel(p))
        if p["format"] == "before-after": print(before_after(p))
        if p["format"] == "price-card": print(price_card(p))
    import sys
    if "--brand" in sys.argv: print(cover(), profile())

"""Build a WhatsApp-chat demo Reel.
Usage: WEEK_JSON=weeks/w45.json OUT=out/w45 python3 build_chat.py P12
The post needs: code, chip, hook_html, sub, chat [{from: them|bot, text, t}], optional biz_name, biz_sub, end_at, seconds."""
import json, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx import make_track
D = json.load(open(os.environ.get("WEEK_JSON", "week1.json")))
OUT = os.environ.get("OUT", "out/week1")
os.makedirs(OUT, exist_ok=True)
code = sys.argv[1] if len(sys.argv) > 1 else "P05"
p = next(x for x in D["posts"] if x["code"] == code)
secs = float(p.get("seconds", 14.5)); end_at = float(p.get("end_at", 11.4))
cfg = {"chip": p["chip"], "hook": p["hook_html"], "sub": p["sub"], "chat": p["chat"],
       "bizName": p.get("biz_name", "صالون مقص"), "bizSub": p.get("biz_sub", "بوت الحجز، شغال 24 ساعة"), "inputHint": "اكتب رسالة",
       "endTitle": p.get("end_title", "بدك بوت زي هذا لمصلحتك؟"), "cta": "راسلنا عالواتساب", "endSmall": "الرابط بأول تعليق", "endAt": end_at}
html = open("tpl_chat.html").read().replace("<body>", "<body>\n<script>window.__CFG__ = " + json.dumps(cfg, ensure_ascii=False) + ";</script>", 1)
page = f"reel_{code}.html"
open(page, "w").write(html)
ev = [("pop", 0.1)]
for m in p["chat"]:
    ev.append(("ding" if m["from"] == "bot" else "pop", m["t"]))
    if m["from"] == "them":
        for k in range(4): ev.append(("type", m["t"] - 0.7 + k * 0.12))
ev += [("pop", end_at + 0.05), ("click", end_at + 0.5)]
wav = f"{OUT}/{code}.wav"
make_track(ev, secs, wav)
subprocess.run(["node", "render_video.mjs", page, f"{OUT}/{code}.mp4", str(secs), wav], check=True)
print(f"{OUT}/{code}.mp4")

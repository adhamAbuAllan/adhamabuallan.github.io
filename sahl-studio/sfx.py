"""Synthesize short sound effects and mix them into one track with ffmpeg.

Usage from Python: make_track(events, seconds, out_wav)
events: list of (kind, time_s), kind in {"whoosh", "pop", "click", "ding", "type"}.
"""
import subprocess, os, tempfile

SFX = {
    # soft swipe: pink noise, band-limited, quick fade in / longer fade out
    "whoosh": "anoisesrc=color=pink:duration=0.55:amplitude=0.6,highpass=f=300,lowpass=f=4200,afade=t=in:d=0.18,afade=t=out:st=0.2:d=0.35,volume=0.55",
    # UI pop: two short tones
    "pop": "sine=f=660:d=0.09,afade=t=out:st=0.01:d=0.08,volume=0.6",
    # tap click: very short high tone
    "click": "sine=f=1800:d=0.035,afade=t=out:st=0.005:d=0.03,volume=0.5",
    # message arrives
    "ding": "sine=f=988:d=0.16,afade=t=out:st=0.02:d=0.14,volume=0.45",
    # one keystroke
    "type": "anoisesrc=color=white:duration=0.03:amplitude=0.4,highpass=f=2000,afade=t=out:st=0.005:d=0.025,volume=0.35",
}


def make_track(events, seconds, out_wav):
    tmp = tempfile.mkdtemp()
    files = {}
    for k in {k for k, _ in events}:
        f = os.path.join(tmp, f"{k}.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", SFX[k], "-ar", "48000", "-ac", "2", f], check=True)
        files[k] = f
    inputs, filters, labels = [], [], []
    # silent bed so the track always lasts the full video
    inputs += ["-f", "lavfi", "-t", str(seconds), "-i", "anullsrc=r=48000:cl=stereo"]
    for i, (k, t) in enumerate(events, start=1):
        inputs += ["-i", files[k]]
        ms = int(t * 1000)
        filters.append(f"[{i}:a]adelay={ms}|{ms}[e{i}]")
        labels.append(f"[e{i}]")
    mix = f"[0:a]{''.join(labels)}amix=inputs={len(labels)+1}:normalize=0,atrim=0:{seconds}[out]"
    fc = ";".join(filters + [mix])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", fc, "-map", "[out]", "-ar", "48000", out_wav], check=True)
    return out_wav

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

# ---- v2: extra effects and a soft music bed (numpy synth, no samples, no licences) ----
SFX.update({
    "tick": "sine=f=1250:d=0.045,afade=t=out:st=0.004:d=0.04,volume=0.32",
    "thud": "sine=f=58:d=0.42,afade=t=in:d=0.004,afade=t=out:st=0.05:d=0.37,volume=1.5",
    "swish": "anoisesrc=color=white:duration=0.38:amplitude=0.5,highpass=f=1800,lowpass=f=9000,afade=t=in:d=0.2,afade=t=out:st=0.22:d=0.16,volume=0.4",
    "rise": "anoisesrc=color=pink:duration=0.9:amplitude=0.7,highpass=f=500,lowpass=f=7000,afade=t=in:curve=exp:d=0.85,afade=t=out:st=0.86:d=0.04,volume=0.55",
    "chime": "sine=f=1318:d=0.5,afade=t=out:st=0.02:d=0.48,volume=0.4",
})


def make_bed(seconds, out_wav, bpm=96, drums_from=2.5, end_at=None):
    """A quiet, modern bed: warm pad, sub bass, soft kick, off-beat hat and a pluck arpeggio. Am7 F C Em7, one chord a bar."""
    import numpy as np, wave
    sr = 48000
    n = int(seconds * sr)
    t = np.arange(n) / sr
    beat = 60 / bpm
    bar = beat * 4
    mix = np.zeros(n)
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    chords = [[45, 60, 64, 67], [41, 57, 60, 64], [48, 60, 64, 67], [40, 59, 62, 67]]

    def add(sig, at, gain):
        i = int(at * sr)
        if i >= n: return
        sig = sig[: n - i]
        mix[i : i + len(sig)] += sig * gain

    def env(length, a, r):
        m = int(length * sr); e = np.ones(m)
        ai, ri = max(1, int(a * sr)), max(1, int(r * sr))
        e[:ai] = np.linspace(0, 1, ai); e[-ri:] *= np.linspace(1, 0, ri)
        return e

    b = 0
    while b * bar < seconds:
        ch = chords[b % 4]; at = b * bar
        tt = np.arange(int((bar + 0.3) * sr)) / sr
        pad = sum(np.sin(2 * np.pi * hz(m) * tt) + 0.35 * np.sin(2 * np.pi * hz(m) * 2.003 * tt) + 0.12 * np.sin(2 * np.pi * hz(m) * 3.004 * tt) for m in ch[1:])
        add(pad * env(bar + 0.3, 0.35, 0.5), at, 0.030)
        for off in (0, 1.5, 2.5):                       # bass: root, a little syncopated
            bt = np.arange(int(0.5 * sr)) / sr
            add(np.sin(2 * np.pi * hz(ch[0]) * bt) * np.exp(-bt * 5) * env(0.5, 0.005, 0.1), at + off * beat, 0.20)
        for k in range(8):                              # pluck arpeggio, 8th notes
            m = ch[1:][(k * 2) % 3] + (12 if k % 4 == 3 else 0)
            pt = np.arange(int(0.4 * sr)) / sr
            pl = (np.sin(2 * np.pi * hz(m + 12) * pt) + 0.3 * np.sin(2 * np.pi * hz(m + 12) * 2 * pt)) * np.exp(-pt * 11)
            add(pl, at + k * beat / 2, 0.045 if at + k * beat / 2 >= drums_from else 0.028)
        b += 1
    rng = np.random.default_rng(7)
    k = 0
    while k * beat < seconds:
        at = k * beat
        if at >= drums_from:
            kt = np.arange(int(0.22 * sr)) / sr
            ph = 2 * np.pi * (48 * kt + (120 - 48) * (1 - np.exp(-kt * 28)) / 28)
            add(np.sin(ph) * np.exp(-kt * 16), at, 0.42)
            ht = int(0.05 * sr); h = rng.standard_normal(ht); h = np.diff(h, prepend=0) * np.exp(-np.arange(ht) / sr * 90)
            add(h, at + beat / 2, 0.035)
        k += 1
    if end_at:                                          # let the bed breathe on the end card
        i = int(end_at * sr); mix[i:] *= 0.75
    fo = int(0.9 * sr); mix[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    mix = np.tanh(mix * 1.4) * 0.6
    pcm = (np.stack([mix, mix], 1) * 32767).astype("<i2")
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
    return out_wav


def make_track_v2(events, seconds, out_wav, end_at=None):
    """Effects over the music bed, levelled for phones (about -15 LUFS, peaks under -1.5 dB)."""
    tmp = tempfile.mkdtemp()
    fx, bed = os.path.join(tmp, "fx.wav"), os.path.join(tmp, "bed.wav")
    make_track(events, seconds, fx)
    try:
        make_bed(seconds, bed, end_at=end_at)
    except Exception as e:                              # numpy missing: effects only
        print("music bed skipped:", e); bed = None
    if bed:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", fx, "-i", bed, "-filter_complex",
                        "[0:a]volume=1.0[a];[1:a]volume=0.9[b];[a][b]amix=inputs=2:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=9[o]",
                        "-map", "[o]", "-ar", "48000", out_wav], check=True)
    else:
        os.replace(fx, out_wav)
    return out_wav

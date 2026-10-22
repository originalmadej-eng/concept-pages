"""White stage + the mode name in pink behind + a soft contact shadow, for the shot_pudding.py frames.
  python3 tools/comp_pudding.py render/pudding render/pudding_comp [--word MC]
The word fades and rises in as the device lands (F_HIT in shot_pudding.py = 22).
"""
import os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lipstick import lipstick
from electric import electric
from pinprick import pinprick
import math
# --electric "DERMA SHOT": the mode name in electric type (tools/electric.py), struck in on the first needle shot
ELEC = sys.argv[sys.argv.index("--electric") + 1] if "--electric" in sys.argv else ""
# --pinprick "DERMA SHOT": the mode name as a needle dot grid, pricked in on the shots (user 2026-10-15, chosen)
PIN = sys.argv[sys.argv.index("--pinprick") + 1] if "--pinprick" in sys.argv else ""
SHOTS, F_PULL = (12, 24), 40                       # derma timing in shot_pudding.py
def energy(f):
    e = 0.22 + 0.06 * math.sin(f * 1.7)
    for f0, k in ((SHOTS[0], 1.0), (SHOTS[1], 1.0), (F_PULL, 0.6)):
        if f >= f0: e += k * math.exp(-(f - f0) / 4)
    return min(1.0, e)
SRC, DST = sys.argv[1], sys.argv[2]; os.makedirs(DST, exist_ok=True)
WORD = sys.argv[sys.argv.index("--word") + 1] if "--word" in sys.argv else "MC"
# official MC copy: "2X BOUNCE BOOSTING" — the phrase is written in lipstick (the "2X" claim is left out)
PHRASE = sys.argv[sys.argv.index("--phrase") + 1] if "--phrase" in sys.argv else "Bounce Boosting"
HN = "/System/Library/Fonts/HelveticaNeue.ttc"
PINK = (236, 158, 176)
F_HIT = int(sys.argv[sys.argv.index("--f_text") + 1]) if "--f_text" in sys.argv else 22   # when the phrase appears (derma: 12)
def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".png"): continue
    f = int(fn[1:5]) if fn[1:5].isdigit() else 1
    dev = Image.open(os.path.join(SRC, fn)).convert("RGBA"); W, H = dev.size
    bg = Image.new("RGBA", (W, H), (247, 243, 241, 255))
    p = max(0.0, min(1.0, (f - (F_HIT - 2)) / 22))          # written on, left to right, as the device lands
    if PIN:
        bg.alpha_composite(pinprick(W, H, PIN, f, SHOTS))
    elif ELEC and f >= F_HIT:
        bg.alpha_composite(electric(W, H, ELEC, f, energy(f), centre_y=H * 0.30, gap=W * 0.11, height_k=0.13,
                                    alpha=min(1.0, (f - F_HIT + 1) / 2), jitter=W * 0.008 * max(0.0, 1 - (f - F_HIT) / 5)))
    elif p > 0:
        if PHRASE: bg.alpha_composite(lipstick(W, H, PHRASE, p, (W / 2, H * 0.40), height_k=0.20))   # --phrase "" : jelly letters are in the 3D render
        lab = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fnt = ImageFont.truetype(HN, int(H * 0.026), index=10)
        x = W * 0.17; a = int(255 * ease((f - F_HIT) / 10))
        for ch in f"{WORD} MODE":
            ImageDraw.Draw(lab).text((x, H * 0.20), ch, font=fnt, fill=(150, 40, 75, a), anchor="ls"); x += fnt.getlength(ch) + H * 0.008
        bg.alpha_composite(lab)
    sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).ellipse([W * 0.5 - W * 0.22, H * 0.86, W * 0.5 + W * 0.22, H * 0.95], fill=120)
    sh = sh.filter(ImageFilter.GaussianBlur(W * 0.016))
    bg = Image.composite(Image.new("RGBA", (W, H), (200, 192, 190, 255)), bg, sh)
    bg.alpha_composite(dev); bg.convert("RGB").save(os.path.join(DST, fn))
print("done", DST)

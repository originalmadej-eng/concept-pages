"""Comp for the BOOSTER beat (tools/shot_booster.py, strawberry shortcake; user 2026-10-21/22).
  - the transparent render over the white stage
  - a warm bloom round "Glow Boosting" once the letters light up from inside (the letters are 3D in the render)
  - "BOOSTER MODE" small, as MC's "MC MODE" (same face, place and tracking), in the booster orange
  python3 tools/comp_booster.py render/booster render/booster_c
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SRC, DST = sys.argv[1], sys.argv[2]; os.makedirs(DST, exist_ok=True)
F_TXT = int(os.environ.get("F_TXT", "60"))                    # shot_booster.py --f_txt
HN = "/System/Library/Fonts/HelveticaNeue.ttc"
LABEL = (168, 78, 28)
def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
ONLY = [int(x) for x in os.environ.get("ONLY", "").split(",") if x]
for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".png"): continue
    f = int(fn[1:5])
    if ONLY and f not in ONLY: continue
    dev = Image.open(os.path.join(SRC, fn)).convert("RGBA"); W, H = dev.size
    out = Image.new("RGBA", (W, H), (247, 243, 241, 255)); out.alpha_composite(dev)
    kg = ease((f - F_TXT - 8) / 22)                            # follows TGlow in shot_booster.py
    if kg > 0:
        a = np.asarray(dev, np.float32)
        warm = np.clip((a[..., 0] - a[..., 2] - 40) / 80, 0, 1) * (a[..., 3] / 255)
        warm[int(H * 0.47):] = 0                               # only the letters' band (the berries are lower down)
        warm[:, int(W * 0.46):int(W * 0.54)] = 0               # not the device
        m = Image.fromarray((warm * 255).astype(np.uint8))
        glow = np.zeros((H, W), np.float32)
        for r, k in ((W * 0.004, 0.55), (W * 0.014, 0.45), (W * 0.035, 0.30)):
            glow += np.asarray(m.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255 * k
        glow = np.clip(glow * kg, 0, 1)[..., None]
        o = np.asarray(out, np.float32)[..., :3]
        col = np.array((255, 150, 70), np.float32)
        o = o + (col - o * 0.35) * glow * 0.70                 # screen-ish warm light
        out = Image.fromarray(np.clip(o, 0, 255).astype(np.uint8)).convert("RGBA")
    ka = ease((f - F_TXT) / 10)
    if ka > 0:
        lab = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fnt = ImageFont.truetype(HN, int(H * 0.026), index=10); x = W * 0.17
        for ch in "BOOSTER MODE":
            ImageDraw.Draw(lab).text((x, H * 0.20), ch, font=fnt, fill=(*LABEL, int(255 * ka)), anchor="ls"); x += fnt.getlength(ch) + H * 0.008
        out.alpha_composite(lab)
    out.convert("RGB").save(os.path.join(DST, fn))
print("done", DST)

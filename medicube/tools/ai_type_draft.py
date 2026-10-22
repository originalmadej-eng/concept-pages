"""AI v4 type drafts on one still (user 2026-10-21: "폰트 별로 / 설명 너무 많아 / AI 글씨 별로").
Copy cut to "AI" + the official line + the official footnote (the FAQ sentence goes).
  A  light line: "AI" traced as a thin line of light, the colour of the device's AI LED
  C  type only: "AI" in a thin geometric sans, wide tracking
  python3 tools/ai_type_draft.py render/ai4_test/J/f0216.png render/ai4_test/type_
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, DST = sys.argv[1], sys.argv[2]
base = Image.open(SRC).convert("RGBA"); W, H = base.size
MAN = "/Library/Fonts/Manrope-{}.ttf"
X = W * 0.075

def tracked(d, xy, txt, fnt, fill, track):
    x, y = xy
    for c in txt:
        d.text((x, y), c, font=fnt, fill=fill, anchor="ls"); x += fnt.getlength(c) + track
    return x

def lines(lay, y_line):
    d = ImageDraw.Draw(lay)
    tracked(d, (X, y_line), "SMART APP CONNECTED CARE", ImageFont.truetype(MAN.format("Medium"), int(H * 0.024)),
            (214, 210, 206, 255), H * 0.0085)
    d.text((X, H * 0.93), "*AI applies only to in-app custom mode recommendations",
           font=ImageFont.truetype(MAN.format("Regular"), int(H * 0.017)), fill=(118, 116, 120, 255), anchor="ls")

def glow(layer, radii=((2, 0.9), (8, 0.55), (22, 0.35))):
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    a = np.asarray(layer, np.float32)
    acc = np.zeros_like(a)
    for r, k in radii:
        acc += np.asarray(layer.filter(ImageFilter.GaussianBlur(r)), np.float32) * k
    acc += a
    return Image.fromarray(np.clip(acc, 0, 255).astype(np.uint8))

# A: light line (monoline strokes; geometry drawn, not a font, so the line weight is even)
S = 3; la = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(la)
h = H * 0.24 * S; x0 = X * S; yb = H * 0.47 * S; wA = h * 0.78; lw = max(2, int(H * 0.0042 * S))
col = (255, 252, 246, 255)
d.line([(x0, yb), (x0 + wA / 2, yb - h), (x0 + wA, yb)], fill=col, width=lw, joint="curve")
d.line([(x0 + wA * 0.21, yb - h * 0.36), (x0 + wA * 0.79, yb - h * 0.36)], fill=col, width=lw)
xi = x0 + wA + h * 0.30
d.line([(xi, yb), (xi, yb - h)], fill=col, width=lw)
la = la.resize((W, H), Image.LANCZOS)
outA = base.copy(); outA.alpha_composite(glow(la)); lines(outA, H * 0.56)
outA.convert("RGB").save(DST + "A.png")

# C: type only
lc = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lc)
f_ai = ImageFont.truetype(MAN.format("ExtraLight"), int(H * 0.30))
tracked(d, (X - H * 0.012, H * 0.47), "AI", f_ai, (246, 243, 238, 255), H * 0.03)
outC = base.copy(); outC.alpha_composite(lc); lines(outC, H * 0.56)
outC.convert("RGB").save(DST + "C.png")
print("wrote", DST + "A.png", DST + "C.png")

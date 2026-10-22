"""Packs the word with air bubbles (screen positions at 960x540) and writes render/mask_air.json for
tools/mask_air.py, which builds them as real 3D air bubbles in Blender (user 2026-10-17: the 2D-drawn bubbles
looked like a cartoon). Also the ambient bubbles and the fizz that keeps leaving the letters.
  python3 tools/air_letters.py [--word MASK]
"""
import json, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
W, H = 960, 540
WORD = sys.argv[sys.argv.index("--word") + 1] if "--word" in sys.argv else "MASK"
FONT = "/Library/Fonts/Nunito-Black.ttf"
size = int(H * 0.19); fnt = ImageFont.truetype(FONT, size)
m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).text((W * 0.075, H * 0.50), WORD, font=fnt, fill=255, anchor="lm")
ma = np.asarray(m) > 128; ys, xs = np.nonzero(ma)
rnd = random.Random(4); placed = []; grid = {}; G = 14
def free(x, y, r):
    gx, gy = int(x // G), int(y // G)
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for (x2, y2, r2) in grid.get((gx + i, gy + j), ()):
                if (x - x2) ** 2 + (y - y2) ** 2 < (r + r2 + 0.15) ** 2: return False
    return True
for r_max in (6.0, 4.2, 2.8, 1.9, 1.3, 0.9, 0.7):                         # big ones first, then fill the gaps
    for _ in range(14000):
        i = rnd.randrange(len(xs)); x, y = xs[i] + rnd.random(), ys[i] + rnd.random()
        r = r_max * rnd.uniform(0.75, 1.0)
        if not all(ma[min(H - 1, max(0, int(y + dy * r))), min(W - 1, max(0, int(x + dx * r)))]
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): continue
        if not free(x, y, r): continue
        placed.append([x / W, y / H, r / W, rnd.uniform(0, 6.3), rnd.random()])
        grid.setdefault((int(x // G), int(y // G)), []).append((x, y, r))
fizz = []                                                       # tiny ones that keep leaving the tops of the letters
for _ in range(90):
    i = rnd.randrange(len(xs)); fizz.append([xs[i] / W, ys[i] / H, rnd.uniform(0.6, 1.6) / W, rnd.uniform(0, 6.3), rnd.uniform(0, 1)])
ambient = [[rnd.uniform(0.02, 0.98), rnd.uniform(0, 1), rnd.uniform(1.0, 4.0) / W, rnd.uniform(0, 6.3), rnd.uniform(0, 1)] for _ in range(45)]
json.dump({"letters": placed, "fizz": fizz, "ambient": ambient},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "render", "mask_air.json"), "w"))
print(len(placed), "letter bubbles,", len(fizz), "fizz,", len(ambient), "ambient")

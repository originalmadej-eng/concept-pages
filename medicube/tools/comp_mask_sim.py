"""Comp for the MASK beat with real water (tools/render_mask_sim.sh, Mantaflow; user 2026-10-16: "옆으로 하자").
The splash, the surface and the trail of air come from the simulation, so this only puts the render on the white
stage, grades the water below the surface line to the approved blue (mask_v4), adds faint caustics and a few ambient
bubbles, and brings in the wet "MASK" lettering once the camera is under (same as comp_mask.py).

  python3 tools/comp_mask_sim.py render/mask_sim render/mask_sim_c
"""
import json, math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw

# reuse comp_mask.py's helpers (everything above its frame loop)
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "comp_mask.py")).read().split("\nfor fn in sorted(os.listdir(SRC)):")[0]
cm = {}
SRC, DST = sys.argv[1], sys.argv[2]; os.makedirs(DST, exist_ok=True)
exec(compile(_src.replace("SRC, DST = sys.argv[1], sys.argv[2]; os.makedirs(DST, exist_ok=True)", "SRC, DST = %r, %r" % (SRC, DST)),
             "comp_mask.py", "exec"), cm)
WHITE, W_TOP, W_LOW = cm["WHITE"], cm["W_TOP"], cm["W_LOW"]
level, refract, caustics, wet_text, sstep = cm["level"], cm["refract"], cm["caustics"], cm["wet_text"], cm["sstep"]
BUBBLES, HEAD, PATH = cm["BUBBLES"], cm["HEAD"], cm["PATH"]
# brighter, lit from above (user 2026-10-17: "조명이 있듯이 밝은 느낌"): lighter blues than v4, light shafts, less caustic
W_TOP, W_LOW = np.array((238, 246, 255), np.float32), np.array((190, 214, 246), np.float32)
from PIL import ImageFilter, ImageFont
_rays = {}
def light_rays(W, H, f):
    """soft shafts slanting down from a light above the water, drifting slowly; strongest near the surface"""
    xx, yy = cm["grids"](W, H); t = f * 0.035
    u = (xx + (yy - H * 0.0) * 0.22) / W                       # slanted 12 degrees
    b = (0.5 + 0.5 * np.sin(u * 23 + t)) * (0.5 + 0.5 * np.sin(u * 9.0 - t * 0.6 + 1.3)) * (0.6 + 0.4 * np.sin(u * 51 + t * 1.7))
    b = np.clip(b * 1.6 - 0.35, 0, 1) ** 1.6
    return np.asarray(Image.fromarray((b * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(W * 0.006)), np.float32) / 255

# MASK made of air (user 2026-10-17: "공기로 이루어진 느낌"): the letters are packed with air bubbles that rise into place
AIR_F0 = 66
_air = {}
def air_bubbles(W, H):
    if (W, H) in _air: return _air[(W, H)]
    size = int(H * 0.19); fnt = ImageFont.truetype(cm["FONT"], size)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).text((W * 0.075, H * 0.50), "MASK", font=fnt, fill=255, anchor="lm")
    ma = np.asarray(m) > 128; ys, xs = np.nonzero(ma)
    rnd = random.Random(4); k = W / 960; placed = []
    grid = {}
    def free(x, y, r):
        gx, gy = int(x // (14 * k)), int(y // (14 * k))
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for (x2, y2, r2) in grid.get((gx + i, gy + j), ()):
                    if (x - x2) ** 2 + (y - y2) ** 2 < (r + r2 + 0.4 * k) ** 2: return False
        return True
    for r_max in (6.5, 4.5, 3.0, 2.0, 1.4):                        # big ones first, then fill the gaps
        for _ in range(9000):
            i = rnd.randrange(len(xs)); x, y = xs[i] + rnd.random(), ys[i] + rnd.random()
            r = r_max * k * rnd.uniform(0.75, 1.0)
            # keep the whole bubble inside the letter so the edges stay crisp
            if not all(ma[min(H - 1, max(0, int(y + dy * r))), min(W - 1, max(0, int(x + dx * r)))]
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): continue
            if not free(x, y, r): continue
            placed.append((x, y, r, rnd.uniform(0, 6.3), rnd.uniform(0, 1)))
            grid.setdefault((int(x // (14 * k)), int(y // (14 * k))), []).append((x, y, r))
    _air[(W, H)] = (placed, m)
    return _air[(W, H)]

def air_text(W, H, f):
    """each bubble rises from below into its place (staggered by its height in the word), then shimmers"""
    if f < AIR_F0: return None
    placed, m = air_bubbles(W, H); S = 2                         # drawn at 2x, then reduced: smooth rims
    lay = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for x, y, r, ph, lag in placed:
        t = (f - AIR_F0 - lag * 14 - (y / H - 0.42) * 10) / 16    # 0..1 arrival
        if t <= 0: continue
        e = 1 - (1 - min(t, 1)) ** 3
        yy = y + (1 - e) * H * (0.20 + 0.15 * lag) + 0.6 * math.sin(f * 0.21 + ph)
        xx = x + (1 - e) * 10 * math.sin(ph * 3 + f * 0.15) + 0.5 * math.sin(f * 0.17 + ph * 2)
        rr = r * (0.55 + 0.45 * e) * (1 + 0.05 * math.sin(f * 0.3 + ph)); a = min(1, t * 2)
        X, Y, Rr = xx * S, yy * S, rr * S
        d.ellipse([X - Rr - S * 0.6, Y - Rr - S * 0.6, X + Rr + S * 0.6, Y + Rr + S * 0.6], outline=(70, 110, 170, int(120 * a)), width=max(1, S // 2))
        d.ellipse([X - Rr, Y - Rr, X + Rr, Y + Rr], fill=(240, 248, 255, int(90 * a)), outline=(255, 255, 255, int(245 * a)), width=max(1, int(S * 0.9)))
        d.arc([X - Rr * 0.82, Y - Rr * 0.82, X + Rr * 0.82, Y + Rr * 0.82], 20, 110, fill=(120, 160, 215, int(150 * a)), width=max(1, S // 2))
        hr = Rr * 0.28; d.ellipse([X - Rr * 0.45 - hr, Y - Rr * 0.45 - hr, X - Rr * 0.45 + hr, Y - Rr * 0.45 + hr], fill=(255, 255, 255, int(250 * a)))
    lay = lay.resize((W, H), Image.LANCZOS)
    glow = m.filter(ImageFilter.GaussianBlur(H * 0.02)).point(lambda v: int(v * 0.18 * sstep((f - AIR_F0 - 10) / 24)))
    g = Image.new("RGBA", (W, H), (255, 255, 255, 0)); g.putalpha(glow); g.alpha_composite(lay)
    return g

AIRDIR = sys.argv[sys.argv.index("--air") + 1] if "--air" in sys.argv else ""
REF = np.array([float(x) for x in (sys.argv[sys.argv.index("--ref") + 1].split(",") if "--ref" in sys.argv else (222, 230, 240))],
               np.float32)                                       # the render's plain-water colour, graded onto W_TOP..W_LOW

for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".png"): continue
    f = int(fn[1:5])
    ren = Image.open(os.path.join(SRC, fn)).convert("RGBA"); W, H = ren.size
    out = Image.new("RGBA", (W, H), (*WHITE.astype(int), 255)); out.alpha_composite(ren)
    oa = np.asarray(out, np.float32)[..., :3]
    # below the still surface line: grade to the approved blue, faint caustics (the splash above the line stays clear)
    yy = np.arange(H, dtype=np.float32)[:, None]
    under = np.clip((yy - level(H, f)) / (H * 0.02), 0, 1)[..., None]
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    grad = W_TOP * (1 - y) + W_LOW * y
    graded = np.clip(oa * (grad / REF), 0, 255)
    depth = np.clip((yy - level(H, f)) / H, 0, 1.5)[..., None]          # light falls off with depth below the surface
    graded = graded + (255 - graded) * 0.55 * light_rays(W, H, f)[..., None] * np.exp(-depth * 1.3)
    top_ = np.clip(1 - yy / (H * 0.55), 0, 1)[..., None] ** 1.5          # the light source is above the frame
    graded = graded + (255 - graded) * (0.10 + 0.35 * top_)
    oa = oa * (1 - under) + graded * under
    out = Image.fromarray(np.clip(oa, 0, 255).astype(np.uint8)).convert("RGBA")
    # air: rendered in 3D (tools/mask_air.py, render/mask_air) — real air bubbles; the word made of them rises in
    # as soon as the camera is under (user 2026-10-17: the drawn ones looked like a cartoon and came too late)
    ap = os.path.join(AIRDIR, fn)
    if AIRDIR and os.path.exists(ap): out.alpha_composite(Image.open(ap).convert("RGBA"))
    out.convert("RGB").save(os.path.join(DST, fn))
print("done", DST)

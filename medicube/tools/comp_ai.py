"""Comp for the AI beat v4 (tools/shot_ai.py; user 2026-10-21).
  - below the water line: MASK v7's water (the white pass, graded blue with shafts of light); the MASK air letters
    burst as the surface passes them
  - above the water line: the studio pass as rendered (real sweep, real lights) — no painted beam, no motes
  - from F_TXT: "AI" traced as a thin line of light (option A, user "글씨는 a안"), then the official line and the
    official footnote. Nothing else.
  python3 tools/comp_ai.py render/ai_c4
Older: tools/comp_ai_v3.py (white -> black crossfade, beam), _v2 (hole, laser, net), _v1 (2D drain).
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DST = sys.argv[1]; os.makedirs(DST, exist_ok=True)
P = json.load(open("render/ai_path.json")); FR = len(P["surface"])
def g(k, f): return P[k][str(min(max(f, 1), FR))]
WHITE = np.array((247, 243, 241), np.float32)
W_TOP, W_LOW = np.array((238, 246, 255), np.float32), np.array((190, 214, 246), np.float32)   # MASK v7's water
F_TXT = int(os.environ.get("F_TXT", "90"))
F_X0, F_X1 = 4, 30                                             # MASK light -> studio light, while it drains
MAN = "/Library/Fonts/Manrope-{}.ttf"
def sstep(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def load(d, f):
    p = os.path.join(d, f"f{f:04d}.png")
    return Image.open(p).convert("RGBA") if os.path.exists(p) else None

W, H = 960, 540
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_gr = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]; GRAD = W_TOP * (1 - _gr) + W_LOW * _gr
def light_rays(f):                                             # as in comp_mask_sim.py
    t = f * 0.035; u = (xx + yy * 0.22) / W
    b = (0.5 + 0.5 * np.sin(u * 23 + t)) * (0.5 + 0.5 * np.sin(u * 9.0 - t * 0.6 + 1.3)) * (0.6 + 0.4 * np.sin(u * 51 + t * 1.7))
    b = np.clip(b * 1.6 - 0.35, 0, 1) ** 1.6
    return np.asarray(Image.fromarray((b * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(W * 0.006)), np.float32) / 255
AIR = load("render/mask_air", 120)                             # MASK's last frame of air letters

def under_water(f, sy):
    wp = load("render/ai_white", f)
    out = Image.new("RGBA", (W, H), (*WHITE.astype(int), 255))
    if wp is not None: out.alpha_composite(wp)
    oa = np.asarray(out, np.float32)[..., :3]
    gr = np.clip(oa * (GRAD / WHITE), 0, 255)
    depth = np.clip((yy - sy) / H, 0, 1.5)[..., None]
    gr = gr + (255 - gr) * 0.55 * light_rays(f)[..., None] * np.exp(-depth * 1.3)
    top_ = np.clip(1 - (yy - max(sy, 0)) / (H * 0.55), 0, 1)[..., None] ** 1.5
    gr = gr + (255 - gr) * (0.10 + 0.35 * top_)
    out = Image.fromarray(np.clip(gr, 0, 255).astype(np.uint8)).convert("RGBA")
    if AIR is not None:                                        # the air letters burst where the water has gone
        a = np.asarray(AIR, np.float32).copy(); a[..., 3] *= np.clip((yy - sy) / 6, 0, 1)
        out.alpha_composite(Image.fromarray(a.astype(np.uint8)))
    return np.asarray(out, np.float32)[..., :3]

# ---------------------------------------------------------------- "AI" as a line of light (option A)
S = 3; X = W * 0.075; HA = H * 0.24; YB = H * 0.47; WA = HA * 0.78
STROKES = [((X, YB), (X + WA / 2, YB - HA)), ((X + WA / 2, YB - HA), (X + WA, YB)),
           ((X + WA * 0.21, YB - HA * 0.36), (X + WA * 0.79, YB - HA * 0.36)),
           ((X + WA + HA * 0.30, YB - HA), (X + WA + HA * 0.30, YB))]
LENS = [math.dist(a, b) for a, b in STROKES]; TOT = sum(LENS)
def ai_light(f):
    """traced on over 20 frames as one pen of light, a bright head at the tip, then it settles"""
    k = (f - F_TXT) / 20
    if k <= 0: return None
    lay = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    lw = max(2, int(H * 0.0042 * S)); col = (255, 252, 246, 255)
    done = min(1.0, k) * TOT; acc = 0; tip = None
    for (a, b), L in zip(STROKES, LENS):
        if done <= acc: break
        u = min(1.0, (done - acc) / L); e = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        d.line([(a[0] * S, a[1] * S), (e[0] * S, e[1] * S)], fill=col, width=lw); tip = e; acc += L
    lay = lay.resize((W, H), Image.LANCZOS)
    arr = np.asarray(lay, np.float32); acc_ = arr.copy()
    for r, kk in ((2, 0.9), (8, 0.55), (22, 0.35)):
        acc_ += np.asarray(lay.filter(ImageFilter.GaussianBlur(r)), np.float32) * kk
    if tip is not None and k < 1.15:                           # the pen's bright head while it draws
        hk = 1 - sstep((k - 1) / 0.15) if k >= 1 else 1.0
        hd = np.exp(-((xx - tip[0]) ** 2 + (yy - tip[1]) ** 2) / (2 * (H * 0.012) ** 2))[..., None]
        acc_[..., :3] += 255 * 0.8 * hd * hk; acc_[..., 3:] += 255 * 0.8 * hd * hk
    return Image.fromarray(np.clip(acc_, 0, 255).astype(np.uint8))

def tracked(d, x, y, txt, fnt, fill, track):
    for c in txt:
        d.text((x, y), c, font=fnt, fill=fill, anchor="ls"); x += fnt.getlength(c) + track
F_LINE = ImageFont.truetype(MAN.format("Medium"), int(H * 0.024)); F_FOOT = ImageFont.truetype(MAN.format("Regular"), int(H * 0.017))
def words(f):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    k1 = sstep((f - F_TXT - 18) / 14); k2 = sstep((f - F_TXT - 26) / 14)
    if k1 > 0: tracked(d, X, H * 0.56 + (1 - k1) * H * 0.012, "SMART APP CONNECTED CARE", F_LINE, (214, 210, 206, int(255 * k1)), H * 0.0085)
    if k2 > 0: tracked(d, X, H * 0.93, "*AI applies only to in-app custom mode recommendations", F_FOOT, (118, 116, 120, int(255 * k2)), H * 0.0012)
    return lay

ONLY = [int(x) for x in os.environ.get("ONLY", "").split(",") if x]
for f in (ONLY or range(1, FR + 1)):
    st = load("render/ai_studio", f)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    if st is not None: out.alpha_composite(st)
    oa = np.asarray(out, np.float32)[..., :3]
    sy = H * g("surface", f)
    # MASK's bright water fades into the studio while the level comes down (a split at the water line read as a
    # wipe): the whole frame keeps MASK's grade at first, the air letters burst where the surface passes them
    kx = sstep((f - F_X0) / (F_X1 - F_X0))
    if kx < 1:
        ua = under_water(f, sy)
        oa = oa * kx + ua * (1 - kx)
    out = Image.fromarray(np.clip(oa, 0, 255).astype(np.uint8)).convert("RGBA")
    al = ai_light(f)
    if al is not None: out.alpha_composite(al)
    out.alpha_composite(words(f))
    out.convert("RGB").save(os.path.join(DST, f"f{f:04d}.png"))
print("done", DST)

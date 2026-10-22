"""Comp for the MASK beat (tools/shot_mask.py), v2 (user 2026-10-16: "퐁당 빠지는걸로"): a half-in-half-out view —
air above, lilac water below the line at render/mask_path.json water_y. The device drops in and plops: drops fly up,
rings spread on the surface, a burst and trail of bubbles follow it down; then the water rises over the whole frame and
"MASK" appears as clear, wet lettering. Draft: the water is drawn here, not simulated.

  python3 tools/comp_mask.py render/mask render/mask_c
"""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

SRC, DST = sys.argv[1], sys.argv[2]; os.makedirs(DST, exist_ok=True)
WHITE = np.array((247, 243, 241), np.float32)
W_TOP, W_LOW = np.array((226, 238, 252), np.float32), np.array((168, 196, 238), np.float32)   # clear water, a little blue (user v4); MASK purple stays on the LED
import json
PATH = json.load(open(os.path.join(os.path.dirname(SRC.rstrip("/")) or ".", "mask_path.json")))
WY, F_HIT = PATH["water_y"], PATH["hit"]
F_W0, F_W1 = 62, 88                       # after the plop the water rises over the whole frame
FONT = "/Library/Fonts/Nunito-Black.ttf"
def sstep(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

def level(H, f):                          # surface height on screen (y): the camera follows the device down (v3)
    return H * PATH["water_y_f"][str(min(max(f, 1), 120))]
def surface(W, H, f):
    x = np.arange(W, dtype=np.float32)
    y = level(H, f) + H * 0.006 * np.sin(x * 0.011 + f * 0.22) + H * 0.003 * np.sin(x * 0.029 - f * 0.37)
    t = f - F_HIT
    if t >= 0:                                # the plop: a dip where it went in, then a ripple running outwards
        cx = W * PATH["centre"][str(min(f, 120))][0]; d = np.abs(x - cx)
        y += H * 0.03 * math.exp(-t / 6) * np.exp(-(d / (W * 0.05)) ** 2) * math.cos(t * 0.6)
        y -= H * 0.010 * math.exp(-t / 14) * np.exp(-((d - t * W * 0.012) / (W * 0.03)) ** 2)
    return y

_g = {}
def grids(W, H):
    if (W, H) not in _g:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); _g[(W, H)] = (xx, yy)
    return _g[(W, H)]

def refract(img, f, amp):
    """wobble an RGBA image like seen through moving water"""
    W, H = img.size; xx, yy = grids(W, H)
    dx = amp * (np.sin(yy * 0.045 + f * 0.30) + 0.6 * np.sin((xx + yy) * 0.021 - f * 0.21))
    dy = amp * 0.6 * np.sin(xx * 0.038 - f * 0.26)
    a = np.asarray(img)
    sx = np.clip(xx + dx, 0, W - 1).astype(np.int32); sy = np.clip(yy + dy, 0, H - 1).astype(np.int32)
    return Image.fromarray(a[sy, sx])

def caustics(W, H, f):
    xx, yy = grids(W, H); t = f * 0.09
    wx = xx + 18 * np.sin(yy * 0.013 + t) ; wy = yy + 18 * np.sin(xx * 0.011 - t * 0.8)      # warp: no regular mesh
    s = (np.sin(wx * 0.050 + wy * 0.018 + t * 2.0) + np.sin(-wx * 0.024 + wy * 0.047 - t * 1.6)
         + np.sin(wx * 0.036 - wy * 0.040 + t * 1.2) + 0.6 * np.sin(wx * 0.083 + wy * 0.061 + t * 2.6))
    c = np.clip(1 - np.abs(s) / 0.7, 0, 1) ** 2.2
    return np.asarray(Image.fromarray((c * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2)), np.float32) / 255   # soft light, not lines

rnd = random.Random(9)
DROPS = [(rnd.uniform(-1, 1), rnd.uniform(6, 21), rnd.uniform(2.0, 6.0)) for _ in range(95)]   # dir, up speed, size
TRAIL = [(rnd.uniform(-1, 1), rnd.uniform(0, 1), F_HIT + rnd.uniform(0, 26) ** 1.3 * 0.55, rnd.uniform(3.0, 7.0), rnd.uniform(1.0, 6.0),
          rnd.uniform(0, 6.3)) for _ in range(200)]                                         # x across, along the body, birth, speed, r
BUBBLES = [(rnd.uniform(0, 1), rnd.uniform(30, 140), rnd.uniform(2.5, 6.0), rnd.uniform(1.5, 5.0), rnd.uniform(0, 6.3))
           for _ in range(36)]                                    # x, birth frame, speed, radius, phase (ambient)
HEAD = [(rnd.uniform(-0.02, 0.02), rnd.uniform(40, 140), rnd.uniform(2.0, 4.0), rnd.uniform(1.0, 3.0), rnd.uniform(0, 6.3))
        for _ in range(26)]                                       # small ones off the device once it floats

def wet_text(W, H, text, alpha):
    """clear lettering like water on glass: faint body, bright rim on top-left, a lilac shadow edge bottom-right"""
    size = int(H * 0.15); fnt = ImageFont.truetype(FONT, size)
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).text((W * 0.075, H * 0.50), text, font=fnt, fill=255, anchor="lm")
    m = m.filter(ImageFilter.GaussianBlur(size * 0.02))
    a = np.asarray(m, np.float32) / 255
    soft = np.asarray(m.filter(ImageFilter.GaussianBlur(size * 0.06)), np.float32) / 255
    gy, gx = np.gradient(soft)
    lit = np.clip(-(gx + gy) * size * 0.9, 0, 1) * a; dark = np.clip((gx + gy) * size * 0.9, 0, 1) * a
    rgb = np.zeros((H, W, 3), np.float32) + np.array((250, 248, 255), np.float32)
    rgb = rgb * (1 - dark[..., None] * 0.55) + np.array((90, 130, 196), np.float32) * dark[..., None] * 0.55
    al = np.clip(a * 0.30 + lit * 0.9 + dark * 0.5, 0, 1) * alpha
    return Image.fromarray(np.dstack([rgb, al * 255]).astype(np.uint8), "RGBA")

for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".png"): continue
    f = int(fn[1:5])
    dev = Image.open(os.path.join(SRC, fn)).convert("RGBA"); W, H = dev.size
    # above water: the white stage with the device on it
    dry = Image.new("RGBA", (W, H), (*WHITE.astype(int), 255))
    dry.alpha_composite(dev)
    # under water: lilac, wavering, caustics
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    wet = Image.fromarray(np.broadcast_to(W_TOP * (1 - y) + W_LOW * y, (H, W, 3)).astype(np.uint8)).convert("RGBA")
    wet.alpha_composite(refract(dev, f, H * 0.0022))            # gentle: the device must not look bent
    wa = np.asarray(wet, np.float32)
    wa[..., :3] = wa[..., :3] * np.array((0.93, 0.96, 1.0)) + 255 * 0.07 * (caustics(W, H, f) * (1.1 - 0.8 * y[..., 0]))[..., None]   # fainter with depth
    wet = Image.fromarray(np.clip(wa, 0, 255).astype(np.uint8))
    # bubbles (under water only)
    bub = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(bub)   # drawn on a layer, then blended
    for bx, b0, sp, r, ph in BUBBLES:
        t = f - b0
        if t < 0: continue
        by = H * 1.02 - sp * t; x = bx * W + 4 * math.sin(t * 0.25 + ph)
        if by < -10: continue
        bd.ellipse([x - r, by - r, x + r, by + r], outline=(255, 255, 255, 170), width=1)
        bd.ellipse([x - r * 0.45, by - r * 0.55, x - r * 0.05, by - r * 0.15], fill=(255, 255, 255, 200))
    for ax, al_, b0, sp, r, ph in TRAIL:                          # the plop's bubbles, released along the body as it sinks
        t = f - b0
        if t < 0: continue
        fb = int(min(120, max(1, round(b0))))
        cx_, cy_ = W * PATH["centre"][str(fb)][0], H * PATH["centre"][str(fb)][1]
        base_y = H * PATH["base"][str(fb)]
        y0 = cy_ + (base_y - cy_) * al_ * 1.1 + (level(H, f) - level(H, fb))   # along the lower body; moves with the camera
        by = y0 - sp * t * (1 + t * 0.02); x = cx_ + ax * W * 0.04 + 3 * math.sin(t * 0.35 + ph)
        if by < level(H, f) + 2: continue
        bd.ellipse([x - r, by - r, x + r, by + r], outline=(255, 255, 255, 200), width=1)
        if r > 2.5: bd.ellipse([x - r * 0.45, by - r * 0.55, x - r * 0.05, by - r * 0.15], fill=(255, 255, 255, 210))
    for bx, b0, sp, r, ph in HEAD:
        t = f - b0
        if t < 0: continue
        by = H * 0.20 - sp * t; x = W * (0.5 + bx) + 3 * math.sin(t * 0.3 + ph)
        if by < -10: continue
        bd.ellipse([x - r, by - r, x + r, by + r], outline=(255, 255, 255, 190), width=1)
    wet.alpha_composite(bub)
    # the surface: everything below it is wet; a bright meniscus line and a darker band just under it
    surf = surface(W, H, f)
    yy = grids(W, H)[1]
    below = np.clip((yy - surf[None, :]) / 1.5, 0, 1)
    mix = Image.fromarray((below * 255).astype(np.uint8))
    out = Image.composite(wet, dry, mix)
    band = np.clip(1 - np.abs(yy - surf[None, :] - H * 0.012) / (H * 0.012), 0, 1) * 0.18
    line = np.clip(1 - np.abs(yy - surf[None, :]) / 1.6, 0, 1) * 0.85
    oa = np.asarray(out, np.float32)
    oa[..., :3] = oa[..., :3] * (1 - band[..., None]) + np.array((96, 140, 200)) * band[..., None]
    oa[..., :3] = oa[..., :3] * (1 - line[..., None]) + 255 * line[..., None]
    out = Image.fromarray(np.clip(oa, 0, 255).astype(np.uint8))
    # above the line: splash drops and rings on the surface (only while the surface is in view)
    t = f - F_HIT
    if t >= 0 and level(H, f) > -H * 0.2:
        spl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(spl); cx = W * PATH["centre"][str(min(f, 120))][0]; wy = level(H, f)
        for i_, (dx_, up, r) in enumerate(DROPS):
            x = cx + dx_ * W * 0.016 * t * (0.5 + up / 18); y = wy - up * t + 0.9 * t * t
            if y > wy or t > 30: continue
            od.ellipse([x - r, y - r * 1.3, x + r, y + r * 1.3], fill=(236, 244, 255, 235), outline=(128, 160, 215, 220))
            od.ellipse([x - r * 0.5, y - r * 0.8, x - r * 0.05, y - r * 0.3], fill=(255, 255, 255, 255))
        for k_, delay in enumerate((0, 5, 11)):                    # rings spreading out on the surface
            tt = t - delay
            if tt <= 0 or tt > 40: continue
            rx = W * 0.02 + tt * W * 0.010; a_ = int(200 * (1 - tt / 40))
            od.ellipse([cx - rx, wy - rx * 0.10, cx + rx, wy + rx * 0.10], outline=(255, 255, 255, a_), width=2)
        if t < 12:                                                  # the crown: a ring of thrown-up water, soft
            cr = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(cr); crnd = random.Random(31)
            rx = W * 0.032 + t * W * 0.009; hgt = H * 0.10 * math.sin(math.pi * min(t, 12) / 12)
            for j in range(34):
                ang = j / 34 * 2 * math.pi + crnd.uniform(-0.1, 0.1); hj = hgt * crnd.uniform(0.35, 1.0)
                x0 = cx + rx * math.cos(ang); y0 = wy + rx * 0.10 * math.sin(ang)
                for q in range(5):                                       # a little column of water per spike
                    yq = y0 - hj * q / 4; rq = (6 - q) * W / 960 * crnd.uniform(0.8, 1.3)
                    cd.ellipse([x0 - rq, yq - rq * 1.2, x0 + rq, yq + rq * 1.2], fill=(234, 242, 255, 200))
            cd.ellipse([cx - rx * 1.1, wy - rx * 0.13, cx + rx * 1.1, wy + rx * 0.13], fill=(248, 252, 255, 170))   # foam at the base
            spl.alpha_composite(cr.filter(ImageFilter.GaussianBlur(1.6)))
        out = out.convert("RGBA"); out.alpha_composite(spl)
    # MASK: once the frame is under water, wavering with it
    ta = sstep((f - 70) / 16)                                    # once the camera is under
    if ta > 0:  # (F_W1 + 4)
        out = out.convert("RGBA"); out.alpha_composite(refract(wet_text(W, H, "MASK", ta), f, H * 0.003))
    out.convert("RGB").save(os.path.join(DST, fn))
print("done", DST)

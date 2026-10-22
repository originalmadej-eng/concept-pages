"""Composite the five ad shots and join them into one sequence.
 - every shot: near-black backdrop with a soft glow, bloom on the LEDs/highlights, light vignette
 - s1: a warm backlight behind the device whose rays stream past its silhouette (light masked by the device, then
       radially blurred from the light's centre)
 - s5: a big FILLED mode name behind the device and the seven-mode list on the left — the only graphics in the film
Copy: mode names only (medicube.us/en-jp/products/booster-pro-x2, 2026-10-14).

  python3 tools/comp_ad.py render/ad render/ad_comp            # all shots + joined render/ad_comp/all/
  python3 tools/comp_ad.py render/ad_t render/ad_t_comp --shot s1 --frames 1,48
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ad_timeline import SHOTS, ORDER, XFADE
from showcase_timeline import NAMES, RGB

SRC, DST = sys.argv[1], sys.argv[2]
def opt(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
HN = "/System/Library/Fonts/HelveticaNeue.ttc"
TITLE = {"booster": "Booster", "mc": "MC", "derma": "Derma Shot", "air": "Air Shot", "dual": "Dual", "mask": "Mask", "ai": "AI"}
WARM = (1.0, 0.86, 0.78)

def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def mix(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))

def colour_at(cfg, f):
    sw = [(max(1, a), m) for a, m in cfg["SWITCHES"]]
    if not sw or f < sw[0][0]: return WARM
    col = RGB[sw[0][1]]
    for i in range(1, len(sw)):
        if f >= sw[i][0]: col = mix(RGB[sw[i - 1][1]], RGB[sw[i][1]], ease((f - sw[i][0]) / 8))
    return col

def mode_at(cfg, f):
    cur = None; t0 = 0
    for a, m in cfg["SWITCHES"]:
        if f >= a: cur, t0 = m, a
    return cur, f - t0

def radial_blur(img, cx, cy, n=24, reach=0.35):
    """zoom blur towards (cx, cy): average of the image scaled up around that point"""
    a = np.asarray(img).astype(np.float32); acc = np.zeros_like(a)
    W, H = img.size
    for i in range(n):
        s = 1 + reach * i / n
        im = img.transform((W, H), Image.AFFINE, (1 / s, 0, cx - cx / s, 0, 1 / s, cy - cy / s), Image.BILINEAR)
        acc += np.asarray(im).astype(np.float32) * (1 - i / n)
    acc /= sum(1 - i / n for i in range(n))
    return Image.fromarray(np.clip(acc, 0, 255).astype(np.uint8))

def glow_layer(W, H, col, k, cx=0.5, cy=0.5, rx=0.42, ry=0.32):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([W * (cx - rx), H * (cy - ry), W * (cx + rx), H * (cy + ry)], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(W * 0.11))
    return ImageChops.multiply(Image.new("RGB", (W, H), tuple(int(255 * c * k) for c in col)), Image.merge("RGB", [m] * 3))

def comp(shot, f, dev):
    cfg = SHOTS[shot]; W, H = dev.size; FR = cfg["FR"]
    col = colour_at(cfg, f); a = dev.getchannel("A")
    out = Image.new("RGB", (W, H), (8, 6, 7))
    if shot == "s1":
        # backlight: a warm disc just behind the body, partly hidden by it; its rays stream out around the silhouette
        lx, ly = W * 0.52, H * 0.48
        light = Image.new("L", (W, H), 0); r = W * 0.13
        ImageDraw.Draw(light).ellipse([lx - r * 1.6, ly - r, lx + r * 1.6, ly + r], fill=255)
        light = light.filter(ImageFilter.GaussianBlur(W * 0.03))
        grow = ease(f / 30)
        light = light.point(lambda v: int(v * (0.35 + 0.65 * grow)))
        # beams: thin wedges from the light's centre (slowly turning), faded with distance, hidden where the device is
        import math, random
        rnd = random.Random(11); beams = Image.new("L", (W, H), 0); bd = ImageDraw.Draw(beams)
        rot = f * 0.0025; R = W * 0.9
        for k_ in range(56):
            th = rnd.uniform(0, 2 * math.pi) + rot * (1 if k_ % 2 else -0.6); wdt = rnd.uniform(0.004, 0.02)
            v = int(rnd.uniform(60, 255))
            bd.polygon([(lx, ly), (lx + R * math.cos(th - wdt), ly + R * math.sin(th - wdt)),
                        (lx + R * math.cos(th + wdt), ly + R * math.sin(th + wdt))], fill=v)
        beams = beams.filter(ImageFilter.GaussianBlur(W * 0.009))
        fall = Image.new("L", (W, H), 0); ImageDraw.Draw(fall).ellipse([lx - W * 0.36, ly - W * 0.22, lx + W * 0.36, ly + W * 0.22], fill=255)
        fall = fall.filter(ImageFilter.GaussianBlur(W * 0.12))
        beams = ImageChops.multiply(beams, fall).point(lambda v: int(v * 0.42 * (0.2 + 0.8 * grow)))
        unocc = ImageChops.multiply(ImageChops.lighter(light, beams), ImageChops.invert(a.filter(ImageFilter.MaxFilter(5))))
        rays = radial_blur(Image.merge("RGB", [unocc] * 3), lx, ly, 20, 0.30)
        tint = Image.new("RGB", (W, H), tuple(int(255 * c) for c in WARM))
        out = ImageChops.add(out, ImageChops.multiply(rays, tint))
        out = ImageChops.add(out, ImageChops.multiply(Image.merge("RGB", [light.point(lambda v: v // 3)] * 3), tint))
    else:
        k = {"s2": 0.16, "s3": 0.30, "s4": 0.22, "s5": 0.24}[shot]
        on = 1.0 if shot != "s2" else 0.35 + 0.65 * ease((f - 50) / 20)
        out = ImageChops.add(out, glow_layer(W, H, col, k * on))
    if shot == "s5":
        cur, dt = mode_at(cfg, f)
        # big filled mode name behind the device, in a deep tone of the mode colour
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        word = NAMES[cur]; size = int(H * 0.30); fnt = ImageFont.truetype(HN, size, index=1)
        while fnt.getlength(word) > W * 0.62: size -= 4; fnt = ImageFont.truetype(HN, size, index=1)
        fill = tuple(int(255 * min(1, 0.10 + c * 0.32)) for c in col)
        aa = int(255 * ease(dt / 10)) if dt < 900 else 255
        d.text((W * 0.62, H * 0.52 + H * 0.02 * (1 - ease(dt / 14))), word, font=fnt, fill=(*fill, aa), anchor="mm")
        out = Image.alpha_composite(out.convert("RGBA"), lay).convert("RGB")
    # device + bloom
    out = Image.alpha_composite(out.convert("RGBA"), dev).convert("RGB")
    lum = dev.convert("L").point(lambda v: 255 if v > 210 else 0)
    bright = Image.composite(dev.convert("RGB"), Image.new("RGB", (W, H)), ImageChops.multiply(lum, a))
    out = ImageChops.add(out, bright.filter(ImageFilter.GaussianBlur(W * 0.010)).point(lambda v: int(v * 0.7)))
    if shot == "s5":
        # the mode list, left: current one bright with a short bar in its colour
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        s = H / 1080; fnt = ImageFont.truetype(HN, int(30 * s), index=10)
        x0, y0, gap = W * 0.075, H * 0.30, 58 * s
        appear = ease(f / 14)
        for j, m in enumerate(ORDER):
            y = y0 + j * gap; on_ = (m == cur)
            alpha = int(255 * appear * (1.0 if on_ else 0.38))
            d.text((x0 + (22 * s if on_ else 0), y), NAMES[m], font=fnt, fill=(240, 232, 230, alpha), anchor="lm")
            if on_:
                d.line([(x0, y), (x0 + 12 * s, y)], fill=(*[int(255 * c) for c in RGB[m]], int(255 * appear)), width=max(1, int(3 * s)))
        out = Image.alpha_composite(out.convert("RGBA"), lay).convert("RGB")
    vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).ellipse([-W * 0.15, -H * 0.3, W * 1.15, H * 1.3], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(W * 0.08))
    return Image.composite(out, Image.new("RGB", (W, H)), vig.point(lambda v: int(80 + v * 175 / 255)))

def frames_of(shot):
    return [int(x) for x in opt("--frames").split(",")] if opt("--frames") else range(1, SHOTS[shot]["FR"] + 1)

if __name__ == "__main__":
    shots = [opt("--shot")] if opt("--shot") else list(SHOTS)
    for sh in shots:
        os.makedirs(os.path.join(DST, sh), exist_ok=True)
        for f in frames_of(sh):
            dev = Image.open(os.path.join(SRC, sh, f"f{f:04d}.png")).convert("RGBA")
            comp(sh, f, dev).save(os.path.join(DST, sh, f"f{f:04d}.png"))
        print(sh, "done")
    if not opt("--shot"):
        # join with short cross-dissolves
        allp = os.path.join(DST, "all"); os.makedirs(allp, exist_ok=True)
        seqs = [[os.path.join(DST, sh, f"f{f:04d}.png") for f in range(1, SHOTS[sh]["FR"] + 1)] for sh in SHOTS]
        out = list(seqs[0])
        for sq in seqs[1:]:
            tail = out[-XFADE:]; out = out[:-XFADE]
            for i in range(XFADE):
                t = (i + 1) / (XFADE + 1)
                out.append(Image.blend(Image.open(tail[i]).convert("RGB"), Image.open(sq[i]).convert("RGB"), t))
            out += sq[XFADE:]
        for i, item in enumerate(out, 1):
            im = item if isinstance(item, Image.Image) else Image.open(item).convert("RGB")
            im.save(os.path.join(allp, f"f{i:04d}.png"))
        print(len(out), "frames ->", allp)

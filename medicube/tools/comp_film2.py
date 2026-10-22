"""Composite for film v2 (tools/shot_film2.py, timeline FILM2):
 - dark part: near-black backdrop, a faint glow in the LED colour once it is on, bloom
 - white-out: the dive into the lens fills the frame with white, which stays as the backdrop
 - "BOOSTER" drops into the left and settles with a small wobble; at HIT it flies at the camera towards the device's
   base (a ripple marks the strike), then "MC" drops in the same way. Words: official mode names only.

  python3 tools/comp_film2.py render/film2 render/film2_comp [--frames 1,200]
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ad_timeline import FILM2 as F2
from showcase_timeline import NAMES, RGB

SRC, DST = sys.argv[1], sys.argv[2]
os.makedirs(DST, exist_ok=True)
ONLY = [int(x) for x in sys.argv[sys.argv.index("--frames") + 1].split(",")] if "--frames" in sys.argv else None
HN = "/System/Library/Fonts/HelveticaNeue.ttc"
SW = F2["SWITCHES"]
WHITE = (247, 243, 241)
BASE_PT = (0.58, 0.86)                 # where the device's base sits on screen after landing (camera in shot_film2)

def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def ease_in(t): t = max(0.0, min(1.0, t)); return t ** 3
def mix(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))
def colour_at(f):
    if f < F2["LED_ON"]: return (0.6, 0.5, 0.48)
    col = RGB[SW[0][1]]
    for i in range(1, len(SW)):
        if f >= SW[i][0]: col = mix(RGB[SW[i - 1][1]], RGB[SW[i][1]], ease((f - SW[i][0]) / 3))
    return col

def word_layer(W, H, text, col, cx, cy, scale=1.0, rot=0.0, alpha=1.0, anchor_left=None):
    size = int(H * 0.15 * scale); fnt = ImageFont.truetype(HN, max(8, size), index=1)
    tw = fnt.getlength(text); th = size
    pad = int(th * 0.6)
    tile = Image.new("RGBA", (int(tw) + 2 * pad, int(th * 1.4) + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((pad, tile.height / 2), text, font=fnt, fill=(*[int(255 * c) for c in col], int(255 * alpha)), anchor="lm")
    if rot: tile = tile.rotate(rot, resample=Image.BICUBIC, center=(pad + tw / 2, tile.height / 2))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = (anchor_left - pad) if anchor_left is not None else (cx - pad - tw / 2)
    lay.alpha_composite(tile, (int(x), int(cy - tile.height / 2)))
    return lay

def drop(W, H, text, col, f, f0):
    """falls from above the frame to the left-centre, then a small damped wobble"""
    x0 = W * 0.08; y1 = H * 0.50
    t = f - f0
    if t < 0: return None
    if t < 12:
        y = -H * 0.15 + (y1 + H * 0.15) * (t / 12) ** 2; rot = 0
    else:
        tau = (t - 12) / 24
        env = math.exp(-4.5 * tau)
        y = y1 - H * 0.03 * env * math.sin(2 * math.pi * 1.7 * tau) * (1 if tau < 1 else 0)
        rot = 2.5 * env * math.sin(2 * math.pi * 1.7 * tau + 0.6) * (1 if tau < 1 else 0)
    return word_layer(W, H, text, col, 0, y, rot=rot, anchor_left=x0)

def frame(f):
    dev = Image.open(os.path.join(SRC, f"f{f:04d}.png")).convert("RGBA"); W, H = dev.size; a = dev.getchannel("A")
    white_bg = f >= F2["FLY0"] - 1
    if not white_bg:
        col = colour_at(f)
        out = Image.new("RGB", (W, H), (8, 6, 7))
        k = 0.03 + 0.15 * ease((f - F2["LED_ON"]) / 16)
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse([W * 0.12, H * 0.2, W * 0.88, H * 0.8], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(W * 0.12))
        out = ImageChops.add(out, ImageChops.multiply(Image.new("RGB", (W, H), tuple(int(255 * c * k) for c in col)), Image.merge("RGB", [m] * 3)))
    else:
        out = Image.new("RGB", (W, H), WHITE)
        sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).ellipse([-W * 0.2, -H * 0.35, W * 1.2, H * 1.35], fill=255)
        sh = sh.filter(ImageFilter.GaussianBlur(W * 0.1))
        out = Image.composite(out, Image.new("RGB", (W, H), (226, 220, 218)), sh)
    # words behind the device only while they rest; the flying word passes in front
    words_back, words_front = [], []
    if white_bg:
        b = drop(W, H, NAMES["booster"], [c * 0.88 for c in RGB["booster"]], f, F2["DROP1"])
        if b is not None and f < F2["HIT"] - 16: words_back.append(b)
        if F2["HIT"] - 16 <= f <= F2["HIT"] + 2:                 # flies at us, towards the device's base
            t = ease_in((f - (F2["HIT"] - 16)) / 16)
            fnt = ImageFont.truetype(HN, int(H * 0.15), index=1); tw = fnt.getlength(NAMES["booster"])
            cx0, cy0 = W * 0.08 + tw / 2, H * 0.50
            cx = cx0 + (W * BASE_PT[0] - cx0) * t; cy = cy0 + (H * BASE_PT[1] - cy0) * t
            al = 1.0 if f < F2["HIT"] - 2 else max(0.0, 1 - (f - (F2["HIT"] - 2)) / 4)
            words_front.append(word_layer(W, H, NAMES["booster"], [c * 0.88 for c in RGB["booster"]], cx, cy, scale=1 + 2.6 * t, alpha=al))
        mc = drop(W, H, NAMES["mc"], [c * 0.75 for c in RGB["mc"]], f, F2["DROP2"])
        if mc is not None: words_back.append(mc)
    for w in words_back: out = Image.alpha_composite(out.convert("RGBA"), w).convert("RGB")
    out = Image.alpha_composite(out.convert("RGBA"), dev).convert("RGB")
    lum = dev.convert("L").point(lambda v: 255 if v > 210 else 0)
    bright = Image.composite(dev.convert("RGB"), Image.new("RGB", (W, H)), ImageChops.multiply(lum, a))
    out = ImageChops.add(out, bright.filter(ImageFilter.GaussianBlur(W * 0.010)).point(lambda v: int(v * (0.25 if white_bg else 0.6))))
    for w in words_front: out = Image.alpha_composite(out.convert("RGBA"), w).convert("RGB")
    if white_bg and F2["HIT"] <= f < F2["HIT"] + 12:            # strike ripple at the base
        t = (f - F2["HIT"]) / 12; d = ImageDraw.Draw(out); r = W * (0.01 + 0.07 * ease(t))
        px, py = W * BASE_PT[0], H * BASE_PT[1]
        cc = tuple(int(255 * (c * 0.88) * (1 - t) + 247 * t) for c in RGB["booster"])
        d.ellipse([px - r, py - r * 0.35, px + r, py + r * 0.35], outline=cc, width=max(1, int(W / 480 * (1 - t) + 1)))
    if not white_bg:
        vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).ellipse([-W * 0.15, -H * 0.3, W * 1.15, H * 1.3], fill=255)
        vig = vig.filter(ImageFilter.GaussianBlur(W * 0.08))
        out = Image.composite(out, Image.new("RGB", (W, H)), vig.point(lambda v: int(80 + v * 175 / 255)))
    # white-out: rises as the camera dives into the lens, then falls away to reveal the white stage
    w = 0.0
    if F2["WHITE0"] <= f < F2["FLY0"] - 1: w = ease_in((f - F2["WHITE0"]) / (F2["WHITE1"] - F2["WHITE0"]))
    elif F2["FLY0"] - 1 <= f < F2["FLY0"] + 8: w = 1 - ease((f - (F2["FLY0"] - 1)) / 9)
    if w > 0: out = Image.blend(out, Image.new("RGB", (W, H), (255, 253, 250)), min(1.0, w))
    return out

if __name__ == "__main__":
    fr = ONLY or range(1, F2["FR"] + 1)
    for f in fr: frame(f).save(os.path.join(DST, f"f{f:04d}.png"))
    print(len(list(fr)), "frames ->", DST)

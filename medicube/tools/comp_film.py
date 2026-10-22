"""Composite for the continuous film (tools/shot_film.py): near-black backdrop with a faint glow in the LED colour,
bloom on the LEDs/highlights, and — in phase E only — the big filled mode name and the seven-mode list.
No backlight rays (removed on request 2026-10-15). Copy: mode names only.

  python3 tools/comp_film.py render/film render/film_comp [--frames 1,200]
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ad_timeline import FILM, ORDER
from showcase_timeline import NAMES, RGB

SRC, DST = sys.argv[1], sys.argv[2]
os.makedirs(DST, exist_ok=True)
ONLY = [int(x) for x in sys.argv[sys.argv.index("--frames") + 1].split(",")] if "--frames" in sys.argv else None
HN = "/System/Library/Fonts/HelveticaNeue.ttc"
SW = FILM["SWITCHES"]; E0 = FILM["E_START"]; LED_ON = SW[0][0]

def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def mix(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))
def colour_at(f):
    if f < LED_ON: return (0.6, 0.5, 0.48)
    col = RGB[SW[0][1]]
    for i in range(1, len(SW)):
        if f >= SW[i][0]: col = mix(RGB[SW[i - 1][1]], RGB[SW[i][1]], ease((f - SW[i][0]) / 6))
    return col
def mode_at(f):
    cur, t0 = None, 0
    for a, m in SW:
        if f >= a: cur, t0 = m, a
    return cur, f - t0

def frame(f):
    dev = Image.open(os.path.join(SRC, f"f{f:04d}.png")).convert("RGBA"); W, H = dev.size; a = dev.getchannel("A")
    col = colour_at(f)
    out = Image.new("RGB", (W, H), (8, 6, 7))
    k = 0.03 + 0.15 * ease((f - LED_ON) / 24)
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([W * 0.12, H * 0.2, W * 0.88, H * 0.8], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(W * 0.12))
    out = ImageChops.add(out, ImageChops.multiply(Image.new("RGB", (W, H), tuple(int(255 * c * k) for c in col)), Image.merge("RGB", [m] * 3)))
    gfx = ease((f - E0 - 6) / 18)                          # graphics only in phase E
    cur, dt = mode_at(f)
    if gfx > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        word = NAMES[cur]; size = int(H * 0.30); fnt = ImageFont.truetype(HN, size, index=1)
        while fnt.getlength(word) > W * 0.62: size -= 4; fnt = ImageFont.truetype(HN, size, index=1)
        fill = tuple(int(255 * min(1, 0.16 + c * 0.62)) for c in col)   # readable, still behind the device
        d.text((W * 0.62, H * 0.52 + H * 0.02 * (1 - ease(dt / 14))), word, font=fnt, fill=(*fill, int(255 * gfx * ease(dt / 10))), anchor="mm")
        out = Image.alpha_composite(out.convert("RGBA"), lay).convert("RGB")
    out = Image.alpha_composite(out.convert("RGBA"), dev).convert("RGB")
    lum = dev.convert("L").point(lambda v: 255 if v > 210 else 0)
    bright = Image.composite(dev.convert("RGB"), Image.new("RGB", (W, H)), ImageChops.multiply(lum, a))
    out = ImageChops.add(out, bright.filter(ImageFilter.GaussianBlur(W * 0.010)).point(lambda v: int(v * 0.6)))
    if gfx > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        s = H / 1080; fnt = ImageFont.truetype(HN, int(30 * s), index=10)
        x0, y0, gap = W * 0.075, H * 0.30, 58 * s
        for j, md in enumerate(ORDER):
            y = y0 + j * gap; on_ = (md == cur)
            d.text((x0 + (22 * s if on_ else 0), y), NAMES[md], font=fnt, fill=(240, 232, 230, int(255 * gfx * (1.0 if on_ else 0.38))), anchor="lm")
            if on_:
                d.line([(x0, y), (x0 + 12 * s, y)], fill=(*[int(255 * c) for c in RGB[md]], int(255 * gfx)), width=max(1, int(3 * s)))
        out = Image.alpha_composite(out.convert("RGBA"), lay).convert("RGB")
    vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).ellipse([-W * 0.15, -H * 0.3, W * 1.15, H * 1.3], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(W * 0.08))
    return Image.composite(out, Image.new("RGB", (W, H)), vig.point(lambda v: int(80 + v * 175 / 255)))

if __name__ == "__main__":
    fr = ONLY or range(1, FILM["FR"] + 1)
    for f in fr: frame(f).save(os.path.join(DST, f"f{f:04d}.png"))
    print(len(list(fr)), "frames ->", DST)

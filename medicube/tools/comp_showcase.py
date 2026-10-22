"""Composite for the Showcase shot: backdrop glow in the mode colour, a large outlined mode name drifting behind the
device, the transparent device render, a soft bloom, and the foreground type (mode index, name, progress).
Copy uses only what the official page states: the seven mode names, "7 modes", "6 intensity levels"
(medicube.us/en-jp/products/booster-pro-x2, 2026-10-14).

  python3 tools/comp_showcase.py render/shots/showcase3 render/shots/showcase3_comp   [--frames 30,90]
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from showcase_timeline import FR, SWITCHES, NAMES, RGB, BEAT, OUTRO

SRC, DST = sys.argv[1], sys.argv[2]
os.makedirs(DST, exist_ok=True)
ONLY = [int(x) for x in sys.argv[sys.argv.index("--frames") + 1].split(",")] if "--frames" in sys.argv else None
NOTEXT = "--notext" in sys.argv
HN = "/System/Library/Fonts/HelveticaNeue.ttc"; DIDOT = "/System/Library/Fonts/Supplemental/Didot.ttc"
ORDER = ["booster", "mc", "derma", "air", "dual", "mask", "ai"]
UI_ON = SWITCHES[0][0]
NEUTRAL = (0.55, 0.45, 0.45)
TITLE = {"booster": "Booster", "mc": "MC", "derma": "Derma Shot", "air": "Air Shot", "dual": "Dual", "mask": "Mask", "ai": "AI"}

def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def ease_out(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3
def mix(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))
def c8(c, k=1.0, a=255): return (*[int(255 * max(0, min(1, x * k))) for x in c], a)

def beat_at(f):
    """index into SWITCHES of the beat playing at f (-1 = intro)"""
    i = -1
    for j, (fr, _) in enumerate(SWITCHES):
        if f >= fr: i = j
    return i

def colour_at(f):
    i = beat_at(f)
    if i < 0: return NEUTRAL
    cur = RGB[SWITCHES[i][1]]; prev = RGB[SWITCHES[i - 1][1]] if i > 0 else NEUTRAL
    return mix(prev, cur, ease((f - SWITCHES[i][0]) / 16))

def tracked(d, xy, text, fnt, fill, track, anchor="ls"):
    """letter-spaced text; returns width"""
    x, y = xy
    w = sum(fnt.getlength(ch) for ch in text) + track * (len(text) - 1)
    if anchor[0] == "m": x -= w / 2
    if anchor[0] == "r": x -= w
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill, anchor="l" + anchor[1]); x += fnt.getlength(ch) + track
    return w

def big_word(W, H, text, alpha, dx, col):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    size = int(H * 0.40); fnt = ImageFont.truetype(HN, size, index=1)
    track = size * 0.04
    w = sum(fnt.getlength(ch) for ch in text) + track * (len(text) - 1)
    if w > W * 1.15:
        size = int(size * W * 1.15 / w); fnt = ImageFont.truetype(HN, size, index=1); track = size * 0.04
    sw = max(1, round(W / 900))
    x = W / 2 + dx
    tracked_outline(d, (x, H * 0.52), text, fnt, c8(mix(col, (1, 1, 1), 0.35), 1.0, int(255 * alpha)), track, sw)
    return lay

def tracked_outline(d, xy, text, fnt, stroke, track, sw):
    x, y = xy
    w = sum(fnt.getlength(ch) for ch in text) + track * (len(text) - 1); x -= w / 2
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=(0, 0, 0, 0), stroke_width=sw, stroke_fill=stroke, anchor="lm")
        x += fnt.getlength(ch) + track

def frame(f):
    dev = Image.open(os.path.join(SRC, f"f{f:04d}.png")).convert("RGBA")
    W, H = dev.size
    col = colour_at(f); i = beat_at(f)
    on = ease((f - UI_ON + 6) / 18)                       # how much the colour world is "on"
    # ---- backdrop: near-black with a soft glow in the mode colour
    bg = Image.new("RGB", (W, H), (9, 7, 8))
    glow = Image.new("L", (W, H), 0); g = ImageDraw.Draw(glow)
    r = W * 0.42
    g.ellipse([W / 2 - r, H * 0.5 - r * 0.75, W / 2 + r, H * 0.5 + r * 0.75], fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(W * 0.12))
    k = 0.07 + 0.22 * on
    tint = Image.new("RGB", (W, H), tuple(int(255 * c * k) for c in col))
    bg = ImageChops.add(bg, ImageChops.multiply(tint, Image.merge("RGB", [glow] * 3)))
    bg = bg.convert("RGBA")
    # ---- big outlined word behind the device: current beat drifts left; the previous one fades out
    def word_for(j): return "BOOSTER PRO X2" if j < 0 or j == len(SWITCHES) - 1 else NAMES[SWITCHES[j][1]]
    def start_for(j): return 6 if j < 0 else SWITCHES[j][0]
    t_in = (f - start_for(i)) / 18
    drift = -W * 0.035 * (f - start_for(i)) / BEAT
    bg = Image.alpha_composite(bg, big_word(W, H, word_for(i), 0.55 * ease(t_in), W * 0.05 * (1 - ease_out(t_in)) + drift, col))
    if i >= 0 and t_in < 1:
        jp = i - 1; dprev = -W * 0.035 * (f - start_for(jp)) / BEAT
        bg = Image.alpha_composite(bg, big_word(W, H, word_for(jp), 0.55 * (1 - ease(t_in * 1.4)), dprev - W * 0.03 * ease(t_in), colour_at(f)))
    # ---- device, a coloured halo behind it, bloom on the LEDs and highlights
    a = dev.getchannel("A")
    halo = a.filter(ImageFilter.GaussianBlur(W * 0.025))
    halo_rgb = Image.new("RGBA", (W, H), c8(col, 1.0, 0)); halo_rgb.putalpha(halo.point(lambda v: int(v * 0.35 * on)))
    out = Image.alpha_composite(Image.alpha_composite(bg, halo_rgb), dev)
    lum = dev.convert("L").point(lambda v: 255 if v > 215 else 0)
    bright = Image.composite(dev.convert("RGB"), Image.new("RGB", (W, H)), ImageChops.multiply(lum, a))
    bloom = bright.filter(ImageFilter.GaussianBlur(W * 0.010))
    out = ImageChops.add(out.convert("RGB"), bloom.point(lambda v: int(v * 0.8))).convert("RGBA")
    # ---- foreground type
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(fg)
    s = H / 1080
    small = ImageFont.truetype(HN, int(22 * s), index=10)
    serif = ImageFont.truetype(DIDOT, int(86 * s), index=1)
    mx, by = W * 0.06, H * 0.80
    hdr_a = int(200 * ease((f - 4) / 20))
    tracked(d, (mx, H * 0.09), "MEDICUBE", small, (235, 228, 226, hdr_a), 6 * s)
    tracked(d, (W - mx, H * 0.09), "BOOSTER PRO X2", small, (235, 228, 226, hdr_a), 6 * s, anchor="rs")
    if 0 <= i < len(SWITCHES) - 1:
        m = SWITCHES[i][1]; t = f - SWITCHES[i][0]
        a1 = int(230 * ease(t / 10))
        tracked(d, (mx, by - 96 * s), f"MODE {ORDER.index(m) + 1:02d} / 07", small, (235, 228, 226, a1), 6 * s)
        d.line([(mx, by - 78 * s), (mx + W * 0.07 * ease_out(t / 16), by - 78 * s)], fill=c8(col, 1.0, 255), width=max(1, int(2 * s)))
        # name rises into a clipped band
        band = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
        bd.text((mx, by + 40 * s * (1 - ease_out(t / 14))), TITLE[m],
                font=serif, fill=(245, 238, 236, int(255 * ease(t / 10))), anchor="ls")
        clip = Image.new("L", (W, H), 0); ImageDraw.Draw(clip).rectangle([0, by - 70 * s, W, by + 18 * s], fill=255)
        band.putalpha(ImageChops.multiply(band.getchannel("A"), clip))
        fg = Image.alpha_composite(fg, band); d = ImageDraw.Draw(fg)
    else:                                                  # intro / outro title block
        t = f - (6 if i < 0 else OUTRO)
        fade = ease(t / 16) * (1 - ease((f - (UI_ON - 10)) / 8) if i < 0 else 1)
        tracked(d, (mx, by - 96 * s), "MEDICUBE", small, (235, 228, 226, int(230 * fade)), 6 * s)
        d.text((mx, by), "Booster Pro X2", font=serif, fill=(245, 238, 236, int(255 * fade)), anchor="ls")
        tracked(d, (mx, by + 46 * s), "7 MODES  ·  6 INTENSITY LEVELS", small, (235, 228, 226, int(200 * fade)), 5 * s)
    # progress: seven dots, current one in the mode colour
    cur = SWITCHES[i][1] if 0 <= i < len(SWITCHES) - 1 else None
    for j, m in enumerate(ORDER):
        x = W - mx - (6 - j) * 26 * s; y = by - 8 * s; rr = 4.5 * s
        alpha = int(230 * ease((f - UI_ON + 4) / 14))
        if m == cur or (i == len(SWITCHES) - 1):
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=c8(RGB[m], 1.0, alpha))
        else:
            d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(200, 190, 190, int(alpha * 0.6)), width=max(1, int(1.5 * s)))
    if not NOTEXT: out = Image.alpha_composite(out, fg)      # --notext: the page overlays the type in HTML
    # vignette
    vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).ellipse([-W * 0.15, -H * 0.3, W * 1.15, H * 1.3], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(W * 0.08))
    out = Image.composite(out.convert("RGB"), Image.new("RGB", (W, H), (0, 0, 0)), vig.point(lambda v: int(70 + v * 185 / 255)))
    return out

if __name__ == "__main__":
    frames = ONLY or range(1, FR + 1)
    for f in frames:
        frame(f).save(os.path.join(DST, f"f{f:04d}.png"))
    print(len(list(frames)), "frames ->", DST)

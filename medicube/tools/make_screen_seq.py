"""Per-frame screen UI for the Showcase shot -> render/tex/screen_seq/0001.png ...
Layout follows make_textures.screen() (520 x 1360 panel incl. the separate power key) and the live UI in ref/16_*.jpg
(mode name with small X2, battery, level number inside an arc, timer).

  python3 tools/make_screen_seq.py
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from showcase_timeline import FR, FPS, BOOT0, BOOT1, SWITCHES, NAMES, X2, LEVEL, RGB

# --shot sN: use that shot's schedule from ad_timeline.py and write render/tex/screen_sN/
SHOT = sys.argv[sys.argv.index("--shot") + 1] if "--shot" in sys.argv else None
if SHOT:
    from ad_timeline import SHOTS
    FR, BOOT0, BOOT1, SWITCHES = (SHOTS[SHOT][k] for k in ("FR", "BOOT0", "BOOT1", "SWITCHES"))
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "render", "tex", f"screen_{SHOT}" if SHOT else "screen_seq")
os.makedirs(OUT, exist_ok=True)

def mode_at(f):
    """(current mode, previous mode, frames since switch) — None before the UI comes up"""
    cur = prev = None; t0 = None
    for fr, m in SWITCHES:
        if f >= fr: prev, cur, t0 = cur, m, fr
    return (cur, prev, f - t0) if cur else (None, None, 0)
HN = "/System/Library/Fonts/HelveticaNeue.ttc"
def font(size, index=0): return ImageFont.truetype(HN, size, index=index)
W, H = 520, 1360
WHITE = (240, 240, 240)
def ease(t): t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3
def rgb8(c, k=1.0): return tuple(int(255 * min(1, x * k)) for x in c)

def name_layer(mode, alpha, dy):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    txt = NAMES[mode]; fs = 92
    while font(fs, 1).getlength(txt) + (60 if mode in X2 else 0) > W - 80: fs -= 4
    tw = font(fs, 1).getlength(txt) + (54 if mode in X2 else 0)
    x0 = (W - tw) / 2; y = 300 + dy
    a = int(255 * alpha)
    d.text((x0, y), txt, font=font(fs, 1), fill=(*WHITE, a), anchor="lm")
    if mode in X2:
        d.text((x0 + font(fs, 1).getlength(txt) + 8, y - fs * 0.32), "X2", font=font(int(fs * 0.45), 1), fill=(*WHITE, a), anchor="lm")
    return lay

def logo(d, alpha):
    """boot mark: square with a cross cut out (approximation of the medicube box mark, as on the body print)"""
    c = int(235 * alpha); s = 150; cx, cy = W / 2, 560
    d.rectangle([cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2], fill=(c, c, c))
    d.rectangle([cx - s * 0.1, cy - s * 0.32, cx + s * 0.1, cy + s * 0.32], fill=(0, 0, 0))
    d.rectangle([cx - s * 0.32, cy - s * 0.1, cx + s * 0.32, cy + s * 0.1], fill=(0, 0, 0))

def frame(f):
    im = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(im)
    g = (210, 210, 210); px, py, pr = W / 2, 1180, 44          # power key glyph (always printed)
    if f >= BOOT0:
        d.arc([px - pr, py - pr, px + pr, py + pr], 300, 600, fill=g, width=10); d.line([px, py - pr - 8, px, py], fill=g, width=10)
    if BOOT0 <= f < BOOT1:
        a = min(ease((f - BOOT0) / 6), 1 - ease((f - (BOOT1 - 2)) / 6))
        logo(d, max(0, a))
    cur, prev, dt = mode_at(f)
    if not cur:
        return im
    ui_in = ease(dt / 6) if prev is None else 1.0
    # status bar
    w8 = int(255 * ui_in)
    d.rounded_rectangle([340, 70, 450, 110], radius=8, outline=(w8, w8, w8), width=4)
    for i in range(4): d.rectangle([350 + i * 24, 78, 366 + i * 24, 102], fill=(w8, w8, w8))
    # mode name: new slides up into place, old slides up and out
    t = ease(dt / 7)
    names = name_layer(cur, (t if prev else 1) * ui_in, 110 * (1 - t))
    if prev and t < 1:
        names = Image.alpha_composite(name_layer(prev, 1 - t, -110 * t), names)
    band = Image.new("L", (W, H), 0); ImageDraw.Draw(band).rectangle([0, 238, W, 362], fill=255)   # ticker window
    names.putalpha(Image.composite(names.getchannel("A"), Image.new("L", (W, H), 0), band))
    im = Image.alpha_composite(im.convert("RGBA"), names).convert("RGB"); d = ImageDraw.Draw(im)
    # level: the arc refills from zero in the new mode colour; the number swaps once (old rolls up, new rolls in) —
    # no intermediate counting, so each mode shows exactly one value
    cx, cy, rr = W / 2, 560, 170
    l1 = LEVEL[cur]
    OUT_F = 4                                       # frames for the old value to leave before the new one enters
    num = Image.new("RGBA", (W, H), (0, 0, 0, 0)); nd_ = ImageDraw.Draw(num)
    d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 150, 390, fill=(70, 70, 70), width=18)
    if prev and dt < OUT_F:                         # old value drains and rolls up
        t = ease(dt / OUT_F); lv = LEVEL[prev] * (1 - t); col = RGB[prev]
        nd_.text((cx, cy - 120 * t), str(LEVEL[prev]), font=font(150, 1), fill=(*WHITE, int(255 * (1 - t))), anchor="mm")
    else:                                           # new value rolls in, arc refills in the new colour
        k = dt - (OUT_F if prev else 0); t = ease(k / 6); lv = l1 * ease(k / 10); col = RGB[cur]
        a_ = t if prev else ui_in
        nd_.text((cx, cy + (120 * (1 - t) if prev else 0)), str(l1), font=font(150, 1), fill=(*WHITE, int(255 * a_)), anchor="mm")
    if lv > 0.02:
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 150, 150 + 240 * lv / 6, fill=rgb8(col, 1.0), width=18)
    win = Image.new("L", (W, H), 0); ImageDraw.Draw(win).rectangle([cx - 110, cy - 95, cx + 110, cy + 95], fill=255)
    num.putalpha(Image.composite(num.getchannel("A"), Image.new("L", (W, H), 0), win))
    im = Image.alpha_composite(im.convert("RGBA"), num).convert("RGB"); d = ImageDraw.Draw(im)
    # timer counting up from when the UI came on
    secs = (f - SWITCHES[0][0]) // FPS
    d.text((W / 2, 860), f"{secs // 60}:{secs % 60:02d}", font=font(150, 0), fill=WHITE, anchor="mm")
    return im

if __name__ == "__main__":
    for f in range(1, FR + 1):
        frame(f).save(os.path.join(OUT, f"{f:04d}.png"))
    print(FR, "screen frames ->", os.path.abspath(OUT))

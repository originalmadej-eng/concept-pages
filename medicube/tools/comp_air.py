"""Comp for tools/shot_air.py: the white stage turns into a pale sky while the device tips back, the clouds come up,
and "AIR SHOT" appears softly once the device is lying on the cloud (plain soft type, no effects — user 2026-10-15).
  python3 tools/comp_air.py render/air render/air_c
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC, DST = sys.argv[1], sys.argv[2]; os.makedirs(DST, exist_ok=True)
TEXT = sys.argv[sys.argv.index("--text") + 1] if "--text" in sys.argv else "AIR SHOT"
FONT = "/Library/Fonts/Quicksand-Bold.ttf"
# --text_img: the cloud title rendered once in 3D (shot_air.py --pass text --still 110); it condenses in here
TIMG = sys.argv[sys.argv.index("--text_img") + 1] if "--text_img" in sys.argv else ""
_tl = {}
def cloud_title(W, H, f):
    t = (f - (F_LAND + 2)) / 26
    if t <= 0 or not TIMG: return None
    if "img" not in _tl:
        im = Image.open(TIMG).convert("RGBA"); _tl["img"] = im
        rng = np.random.default_rng(5)
        n = sum(np.asarray(Image.fromarray((rng.random((H // s_ + 1, W // s_ + 1)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255 / (i + 1)
                for i, s_ in enumerate((40, 16, 6)))
        _tl["noise"] = (n - n.min()) / (n.max() - n.min())
    im = _tl["img"]; e = sstep(t)
    # wisps first: the brightest/noisiest bits appear, then the letters fill in and sharpen
    m = np.clip((_tl["noise"] - (1 - e * 1.25)) * 4, 0, 1)
    a = np.asarray(im.getchannel("A"), np.float32) * m
    out = im.copy(); out.putalpha(Image.fromarray(a.astype(np.uint8)))
    if e < 1: out = out.filter(ImageFilter.GaussianBlur((1 - e) * H * 0.008))
    return out
WHITE = np.array((247, 243, 241), np.float32)
SKY_TOP, SKY_LOW = np.array((150, 196, 238), np.float32), np.array((228, 240, 250), np.float32)
F_TIP, F_LAND = 14, 34                               # as in shot_air.py
def sstep(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

_sky = {}
def sky(W, H):
    if (W, H) not in _sky:
        y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None] ** 0.8
        _sky[(W, H)] = np.broadcast_to(SKY_TOP * (1 - y) + SKY_LOW * y, (H, W, 3)).copy()
    return _sky[(W, H)]

def text_layer(W, H, f):
    t = (f - (F_LAND + 6)) / 18
    if t <= 0: return None
    al = sstep(t); fnt = ImageFont.truetype(FONT, int(H * 0.12)); tr = H * 0.022
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    wsum = sum(fnt.getlength(c) for c in TEXT) + tr * (len(TEXT) - 1)
    x = W * 0.075; y = H * 0.50 + (1 - al) * H * 0.04 - 0.006 * H * np.sin(f / 9)   # beside the cloud (left), drifts up, floats
    for c in TEXT:
        d.text((x, y), c, font=fnt, fill=(86, 146, 206, int(255 * al)), anchor="lm"); x += fnt.getlength(c) + tr   # air blue: reads on sky and on cloud
    if al < 1: lay = lay.filter(ImageFilter.GaussianBlur((1 - al) * H * 0.012))      # comes out of the haze
    return lay

for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".png"): continue
    f = int(fn[1:5])
    dev = Image.open(os.path.join(SRC, fn)).convert("RGBA"); W, H = dev.size
    k = sstep((f - F_TIP) / (F_LAND - F_TIP))
    bg = Image.fromarray((WHITE * (1 - k) + sky(W, H) * k).astype(np.uint8)).convert("RGBA")
    bg.alpha_composite(dev)
    tl = cloud_title(W, H, f) if TIMG else text_layer(W, H, f)
    if tl is not None: bg.alpha_composite(tl)        # over the far clouds (they hid it); the device lies well below it
    bg.convert("RGB").save(os.path.join(DST, fn))
print("done", DST)

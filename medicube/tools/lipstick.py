"""Lipstick-written type, magazine style: a brush scrawl (Smooch, installed in /Library/Fonts) turned into a
waxy lipstick stroke — rough dragged edges, streaks along the swipe, small dry gaps, a soft waxy sheen — with a
left-to-right write-on.

  layer = lipstick(W, H, "Bounce Boosting", progress=0..1, centre=(x, y), height_k=0.22)
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

FONT = "/Library/Fonts/Smooch-Regular.ttf"      # a fast brush scrawl (chosen over Kaushan: less "typed")
ROSE = (226, 112, 146)                          # soft lipstick pink (the first rose read too red)

def _noise(w, h, scale, seed):
    rng = np.random.default_rng(seed)
    n = rng.random((max(2, h // scale), max(2, w // scale))).astype(np.float32)
    return np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255

_cache = {}
def _base(W, H, text, height_k, colour, seed):
    key = (W, H, text, height_k, colour, seed)
    if key in _cache: return _cache[key]
    size = int(H * height_k); fnt = ImageFont.truetype(FONT, size)
    tw = fnt.getlength(text); pad = int(size * 0.5)
    w, h = int(tw + 2 * pad), int(size * 1.6 + 2 * pad)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).text((pad, h / 2), text, font=fnt, fill=255, anchor="lm")
    m = m.filter(ImageFilter.MaxFilter(max(3, (size // 60) | 1)))      # a lipstick line is fatter than a pen line
    m = m.rotate(5, resample=Image.BICUBIC, expand=True); w, h = m.size
    a = np.asarray(m.filter(ImageFilter.GaussianBlur(size * 0.012))).astype(np.float32) / 255
    # dragged edges: threshold the softened shape against noise
    edge = _noise(w, h, max(2, size // 70), seed) - 0.5
    alpha = np.clip((a - 0.5 + edge * 0.35) * 6 + 0.5, 0, 1)
    # dry gaps where the stick skipped
    gaps = _noise(w, h, max(2, size // 28), seed + 1)
    alpha *= np.clip((gaps - 0.035) * 14, 0, 1)
    # streaks along the swipe direction (stretched noise, tilted)
    st = Image.fromarray((_noise(w * 2, max(4, h // 6), 3, seed + 2) * 255).astype(np.uint8)).resize((w * 2, h * 2), Image.BICUBIC)
    st = np.asarray(st.rotate(-18, resample=Image.BICUBIC).crop((w // 2, h // 2, w // 2 + w, h // 2 + h))).astype(np.float32) / 255
    shade = 0.74 + 0.36 * st
    # waxy sheen from the upper left: slope of the softened mask
    soft = np.asarray(m.filter(ImageFilter.GaussianBlur(size * 0.04))).astype(np.float32) / 255
    gy, gx = np.gradient(soft)
    sheen = np.clip(-(gx * 0.7 + gy * 0.7) * size * 0.35, 0, 1) ** 1.5
    rgb = np.stack([np.clip(c * shade + 255 * 0.20 * sheen, 0, 255) for c in colour], -1)
    tile = np.dstack([rgb, alpha * 255]).astype(np.uint8)
    out = (Image.fromarray(tile, "RGBA"), pad, tw)
    _cache[key] = out
    return out

def lipstick(W, H, text, progress=1.0, centre=None, height_k=0.22, colour=ROSE, seed=7):
    tile, pad, tw = _base(W, H, text, height_k, colour, seed)
    w, h = tile.size
    if progress < 1:                                          # write-on: a soft wipe from the left
        x_edge = pad + tw * progress
        ramp = np.clip((x_edge - np.arange(w)) / (h * 0.08) + 0.5, 0, 1).astype(np.float32)
        a = np.asarray(tile.getchannel("A")).astype(np.float32) * ramp[None, :]
        tile = tile.copy(); tile.putalpha(Image.fromarray(a.astype(np.uint8)))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cx, cy = centre or (W / 2, H / 2)
    lay.alpha_composite(tile, (int(cx - w / 2), int(cy - h / 2)))
    return lay

if __name__ == "__main__":
    W, H = 1920, 1080
    bg = Image.new("RGBA", (W, H), (247, 243, 241, 255))
    bg.alpha_composite(lipstick(W, H, "Bounce Boosting", 1.0, (W / 2, H * 0.42)))
    bg.convert("RGB").save("render/lipstick_test.png"); print("render/lipstick_test.png")

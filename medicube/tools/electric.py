"""Electric type for the DERMA SHOT beat (user 2026-10-15: "더마샷으로 작성하고 전기 느낌을 주는 폰트"): a hard, slanted
display face filled hot yellow to amber (the mode colour), with a haze, and lightning that crawls over the letters and
jumps between them. Bolts are redrawn every frame (that flicker is what reads as current); `energy` adds bolts and heat.

  lay = electric(W, H, "DERMA SHOT", frame, energy=0..1, centre_y=H*0.25, gap=W*0.11)
The two words sit either side of the device (centre of frame) with `gap` between them.
"""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

FONT = "/Library/Fonts/Orbitron-Black.ttf"          # chosen from render/electric_fonts.png (tech, wide, reads as current)
HOT, AMBER, DEEP = (255, 226, 92), (250, 148, 24), (176, 70, 8)

def _words_mask(W, H, text, font, size, cy, gap, shear):
    fnt = ImageFont.truetype(font, size)
    words = text.split(" ", 1) if " " in text else [text]
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    if len(words) == 2:
        d.text((W / 2 - gap / 2, cy), words[0], font=fnt, fill=255, anchor="rm")
        d.text((W / 2 + gap / 2, cy), words[1], font=fnt, fill=255, anchor="lm")
    else:
        d.text((W / 2, cy), text, font=fnt, fill=255, anchor="mm")
    # italic slant around the text line: speed
    return m.transform((W, H), Image.AFFINE, (1, shear, -shear * cy, 0, 1, 0), resample=Image.BICUBIC)

def _bolt(p0, p1, rnd, rough, depth=5):
    pts = [p0, p1]
    for _ in range(depth):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) + 1e-6
            off = (rnd.random() - 0.5) * L * rough
            out += [((a[0] + b[0]) / 2 - dy / L * off, (a[1] + b[1]) / 2 + dx / L * off), b]
        pts = out
    return pts

_edge_cache = {}
def electric(W, H, text, frame, energy=0.5, centre_y=None, gap=None, height_k=0.17, font=FONT, shear=-0.18,
             alpha=1.0, jitter=0.0, seed=3):
    cy = H * 0.25 if centre_y is None else centre_y; gap = W * 0.11 if gap is None else gap
    size = int(H * height_k)
    key = (W, H, text, font, size, int(cy), int(gap), shear)
    if key not in _edge_cache:
        m = _words_mask(W, H, text, font, size, cy, gap, shear)
        a = np.asarray(m).astype(np.float32) / 255
        edge = np.asarray(m.filter(ImageFilter.FIND_EDGES)) > 60
        ys, xs = np.nonzero(edge)
        _edge_cache[key] = (m, a, list(zip(xs.tolist(), ys.tolist())))
    m, a, edge_pts = _edge_cache[key]
    rnd = random.Random(seed * 1000 + frame)
    if jitter:                                                   # strike-in shake
        m = ImageChops.offset(m, int(rnd.uniform(-1, 1) * jitter), int(rnd.uniform(-1, 1) * jitter * 0.5))
        a = np.asarray(m).astype(np.float32) / 255
    heat = min(1.0, 0.35 + 0.65 * energy)
    # fill: hot yellow at the top to amber at the bottom, flaring brighter with energy
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    t = np.clip((yy - (cy - size * 0.45) / H) / (size * 0.9 / H), 0, 1)
    rgb = np.stack([np.broadcast_to(HOT[i] * (1 - t) + AMBER[i] * t, (H, W)) for i in range(3)], -1)
    rgb = rgb + (255 - rgb) * 0.45 * energy                      # whiter when the current spikes
    # dark rim so the letters hold on the white stage, and a thin bright inner line (a lit tube)
    rim = np.asarray(m.filter(ImageFilter.MaxFilter(5))).astype(np.float32) / 255 - a
    inner = a - np.asarray(m.filter(ImageFilter.MinFilter(max(3, (size // 18) | 1)))).astype(np.float32) / 255
    out = np.zeros((H, W, 4), np.float32)
    out[..., :3] = rgb * a[..., None]; out[..., 3] = 255 * a
    out[..., :3] += np.array(DEEP, np.float32) * np.clip(rim, 0, 1)[..., None]; out[..., 3] += 255 * np.clip(rim, 0, 1)
    out[..., :3] = out[..., :3] * (1 - 0.6 * inner[..., None]) + 255 * 0.6 * inner[..., None] * a[..., None]
    out[..., :3] /= np.maximum(out[..., 3:4] / 255, 1e-3)          # un-premultiply
    lay = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")
    # haze: amber, laid under the letters (normal blend: an additive glow would vanish on white)
    haze = Image.new("RGBA", (W, H), (*AMBER, 0))
    haze.putalpha(m.filter(ImageFilter.GaussianBlur(size * 0.18)).point(lambda v: int(v * (0.28 + 0.4 * energy))))
    base = Image.alpha_composite(haze, lay)
    # lightning: short arcs that hug the outline, plus a few long ones that jump across the letters
    bolts = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(bolts)
    core = Image.new("RGBA", (W, H), (0, 0, 0, 0)); cd = ImageDraw.Draw(core)
    n_short, n_long = int(4 + 22 * energy), int(1 + 5 * energy)
    for i in range(n_short + n_long):
        p0 = rnd.choice(edge_pts)
        if i < n_short:
            ang = rnd.uniform(0, 2 * math.pi); L = size * rnd.uniform(0.15, 0.45)
            p1 = (p0[0] + math.cos(ang) * L, p0[1] + math.sin(ang) * L * 0.6); rough = 0.55
        else:
            p1 = rnd.choice(edge_pts); rough = 0.35
            if math.hypot(p1[0] - p0[0], p1[1] - p0[1]) > W * 0.3: continue
        pts = _bolt(p0, p1, rnd, rough)
        w = max(1, int(H / 360))
        bd.line(pts, fill=(255, 112, 0, 235), width=w * 6, joint="curve")
        cd.line(pts, fill=(255, 255, 240, 255), width=max(2, int(w * 1.6)), joint="curve")
        if rnd.random() < 0.35:                                    # forks
            k = rnd.randrange(len(pts) // 3, len(pts)); q = pts[k]
            fk = _bolt(q, (q[0] + rnd.uniform(-1, 1) * size * 0.3, q[1] + rnd.uniform(-1, 1) * size * 0.25), rnd, 0.6, 4)
            bd.line(fk, fill=(255, 112, 0, 200), width=w * 4); cd.line(fk, fill=(255, 255, 240, 235), width=max(1, w))
    bolts = bolts.filter(ImageFilter.GaussianBlur(H / 220))
    out = Image.alpha_composite(base, bolts); out = Image.alpha_composite(out, core)
    if alpha < 1: out.putalpha(out.getchannel("A").point(lambda v: int(v * alpha)))
    return out

if __name__ == "__main__":
    import sys
    fonts = ["RussoOne-Regular", "Bangers-Regular", "Knewave-Regular", "Orbitron-Black", "ClimateCrisis-Regular", "Electrolize-Regular"]
    W, H = 960, 270; sheet = Image.new("RGB", (W, H * len(fonts)), (247, 243, 241))
    for i, fn in enumerate(fonts):
        tile = Image.new("RGBA", (W, H), (247, 243, 241, 255))
        tile.alpha_composite(electric(W, H, "DERMA SHOT", 5, 0.6, centre_y=H * 0.5, gap=W * 0.11, height_k=0.34, font=f"/Library/Fonts/{fn}.ttf"))
        ImageDraw.Draw(tile).text((10, 8), fn, fill=(120, 120, 120))
        sheet.paste(tile.convert("RGB"), (0, H * i))
    sheet.save("render/electric_fonts.png"); print("render/electric_fonts.png")

"""Per-mode mood effects for the white-stage part of the film. One look per mode, built on the official descriptions
(plan.md "모드 공식 설명"):
  booster  glow + absorption: a warm bloom from the head, golden motes drawn INTO it
  mc       bounce / firming: elastic rings that wobble round the device, the word squashes and springs
  derma    dense fine needles + crackling energy arcs (the page: "Delivers Energy")
  air      rising above clouds: pale sky, a cloud bank below, the device lifted
  dual     two modes at once: two colour fields overlap, the word in two offset copies that merge
  mask     moist: condensation droplets and a slow drip on the glass, glossy word
  ai       analysing: a fine grid, a scan beam passing over the device, corner brackets, the word typed

  python3 tools/mood_fx.py            # style frames: render/moods/mood_<mode>.png + render/moods/sheet.png
frame(mode, dev, t, word_t) -> RGB; t = seconds into the beat (effects), word_t = 0..1 entrance progress.
"""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from showcase_timeline import NAMES, RGB

HN = "/System/Library/Fonts/HelveticaNeue.ttc"
WHITE = (247, 243, 241)

def c8(c, k=1.0, a=255): return (*[int(255 * max(0, min(1, x * k))) for x in c], a)
def ease(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
def blank(W, H): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
def bbox_info(dev):
    x0, y0, x1, y1 = dev.getchannel("A").getbbox()
    return dict(cx=(x0 + x1) / 2, top=y0, bot=y1, w=x1 - x0, h=y1 - y0, head=(x0 + x1) / 2, head_y=y0 + (x1 - x0) * 0.25)

def word(W, H, text, fill, x=None, y=None, size_k=0.15, sx=1.0, sy=1.0, rot=0.0, glow=None, glow_r=0.012, shadow=None):
    size = int(H * size_k); fnt = ImageFont.truetype(HN, size, index=1)
    while fnt.getlength(text) > W * 0.40 and size > 8:      # long names shrink to stay clear of the device
        size -= 2; fnt = ImageFont.truetype(HN, size, index=1)
    tw = fnt.getlength(text); pad = int(size * 0.8)
    tile = Image.new("RGBA", (int(tw) + 2 * pad, int(size * 1.3) + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((pad, tile.height / 2), text, font=fnt, fill=fill, anchor="lm")
    if sx != 1 or sy != 1:
        tile = tile.resize((max(1, int(tile.width * sx)), max(1, int(tile.height * sy))), Image.BICUBIC)
    if rot: tile = tile.rotate(rot, resample=Image.BICUBIC, expand=False)
    lay = blank(W, H)
    x = W * 0.08 if x is None else x; y = H * 0.5 if y is None else y
    pos = (int(x - pad * sx), int(y - tile.height / 2))
    if glow:
        g = Image.new("RGBA", tile.size, (*glow[:3], 0)); g.putalpha(tile.getchannel("A").filter(ImageFilter.GaussianBlur(W * glow_r)).point(lambda v: min(255, int(v * glow[3] / 255 * 2))))
        lay.alpha_composite(g, pos)
    if shadow:
        sh = Image.new("RGBA", tile.size, shadow[:3] + (0,)); sh.putalpha(tile.getchannel("A").filter(ImageFilter.GaussianBlur(W * 0.006)).point(lambda v: int(v * shadow[3] / 255)))
        lay.alpha_composite(sh, (pos[0] + int(W * 0.004), pos[1] + int(W * 0.008)))
    lay.alpha_composite(tile, pos)
    return lay

def radial(W, H, cx, cy, r, col, a):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(r * 0.45)).point(lambda v: int(v * a))
    lay = Image.new("RGBA", (W, H), c8(col, 1.0, 0)); lay.putalpha(m); return lay

# ---------------------------------------------------------------------------------------------- moods
def booster(W, H, dev, t, wt):
    b = bbox_info(dev); col = RGB["booster"]
    back = Image.new("RGBA", (W, H), WHITE + (255,))
    back.alpha_composite(radial(W, H, b["head"], b["head_y"], W * 0.22, mix(col, (1, 1, 1), 0.25), 0.55))
    front = blank(W, H); d = ImageDraw.Draw(front)
    rnd = random.Random(3)
    for i in range(70):                                   # motes spiralling in towards the head
        ang = rnd.uniform(0, 2 * math.pi); r0 = rnd.uniform(W * 0.12, W * 0.42); ph = rnd.uniform(0, 1)
        p = (ph + t * 0.6) % 1.0; r = r0 * (1 - p) ** 1.4; a = ang + p * 1.6
        x = b["head"] + r * math.cos(a); y = b["head_y"] + r * math.sin(a) * 0.65
        size = max(1.0, W / 960 * (1.2 + 2.2 * (1 - p)))
        al = int(230 * math.sin(math.pi * p))
        tail = [(x - math.cos(a + 1.2) * size * 5, y - math.sin(a + 1.2) * size * 3), (x, y)]
        d.line(tail, fill=c8(mix(col, (1, 0.85, 0.5), 0.4), 1.0, al // 2), width=max(1, int(size * 0.8)))
        d.ellipse([x - size, y - size, x + size, y + size], fill=c8(mix(col, (1, 0.9, 0.6), 0.5), 1.0, al))
    w = word(W, H, NAMES["booster"], c8(col, 0.9), y=H * 0.5, glow=c8(col, 1.0, 140), glow_r=0.02)
    return back, front, w

def mc(W, H, dev, t, wt):
    b = bbox_info(dev); col = RGB["mc"]; dk = [c * 0.62 for c in col]
    back = Image.new("RGBA", (W, H), WHITE + (255,)); d = ImageDraw.Draw(back)
    cx, cy = b["cx"], (b["top"] + b["bot"]) / 2
    for k in range(4):                                    # elastic rings: radius breathes with a damped wobble
        rr = W * (0.08 + 0.055 * k) * (1 + 0.06 * math.sin(2 * math.pi * (t * 1.4 - k * 0.18)))
        pts = []
        for i in range(181):
            a = 2 * math.pi * i / 180
            wob = 1 + 0.035 * math.sin(4 * a + t * 6 + k) * math.exp(-0.3 * k)
            pts.append((cx + rr * wob * math.cos(a), cy + rr * 1.35 * wob * math.sin(a)))
        d.line(pts, fill=c8(mix(col, (0.55, 0.62, 0.55), 0.45), 1.0, int(110 - 22 * k)), width=max(1, int(W / 960 * (2.2 - 0.3 * k))))
    sq = 1 + 0.12 * math.sin(2 * math.pi * t * 1.2) * math.exp(-1.2 * t)       # squash & stretch
    w = word(W, H, NAMES["mc"], c8(dk, 1.0), y=H * 0.5, sx=1 / sq, sy=sq, shadow=(60, 80, 60, 70))
    return back, blank(W, H), w

def derma(W, H, dev, t, wt):
    b = bbox_info(dev); col = RGB["derma"]
    back = Image.new("RGBA", (W, H), WHITE + (255,)); d = ImageDraw.Draw(back)
    rnd = random.Random(5); step = max(5, int(W / 96))
    cx, cy = b["cx"], (b["top"] + b["bot"]) / 2
    for gy in range(0, H, step):                          # a dense field of fine needles, densest round the device
        for gx in range(0, W, step):
            dist = math.hypot((gx - cx) / W, (gy - cy) / H * 0.8)
            k = max(0.0, 1 - dist / 0.5) ** 1.5
            if k <= 0.01: continue
            n = 0.5 + 0.5 * math.sin(gx * 0.11 + gy * 0.07 + t * 9 + rnd.random() * 6)
            L = step * (0.5 + 0.9 * n) * (0.4 + 0.6 * k)
            d.line([(gx, gy - L / 2), (gx, gy + L / 2)], fill=c8(mix(col, (0.35, 0.22, 0.1), 0.3), 1.0, int(200 * k * (0.4 + 0.6 * n))), width=1)
    front = blank(W, H)
    arcs = blank(W, H); ad = ImageDraw.Draw(arcs)
    rnd2 = random.Random(int(t * 12))                       # arcs re-strike several times a second
    for j in range(6):
        side = -1 if j % 2 else 1
        ang = math.pi / 2 - side * rnd2.uniform(0.9, 1.6); L = W * rnd2.uniform(0.08, 0.16)
        x, y = b["cx"] + side * b["w"] * 0.5, b["top"] + b["h"] * rnd2.uniform(0.05, 0.75); pts = [(x, y)]
        ang = math.atan2(rnd2.uniform(-0.6, 0.6), side)
        for s in range(12):
            x += L / 12 * math.cos(ang) + rnd2.uniform(-1, 1) * W * 0.012
            y += L / 12 * math.sin(ang) + rnd2.uniform(-1, 1) * W * 0.012
            pts.append((x, y))
        ad.line(pts, fill=c8(col, 1.0, 230), width=max(2, int(W / 320)))
        ad.line(pts, fill=(255, 250, 235, 255), width=max(1, int(W / 900)))
    glow = arcs.filter(ImageFilter.GaussianBlur(W * 0.006))
    front.alpha_composite(glow); front.alpha_composite(glow); front.alpha_composite(arcs)
    w = word(W, H, NAMES["derma"], c8([c * 0.85 for c in col]), y=H * 0.5, glow=c8(col, 1.0, 110), glow_r=0.008)
    return back, front, w

def air(W, H, dev, t, wt):
    col = RGB["air"]
    a = np.zeros((H, W, 3), np.float32)
    top = np.array([0.80, 0.92, 0.98]) * 255; bot = np.array(WHITE, np.float32)
    for y in range(H): a[y] = top + (bot - top) * (y / H)
    back = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
    cl = blank(W, H); d = ImageDraw.Draw(cl); rnd = random.Random(9)
    drift = t * W * 0.02
    for i in range(46):                                   # a cloud bank: soft puffs, lit from above
        x = (rnd.uniform(-0.1, 1.1) * W + drift * (0.5 + rnd.random())) % (W * 1.2) - W * 0.1
        y = H * rnd.uniform(0.74, 0.98); r = W * rnd.uniform(0.04, 0.11)
        d.ellipse([x - r * 1.5, y - r * 0.8, x + r * 1.5, y + r * 0.8], fill=(255, 255, 255, 235))
        d.ellipse([x - r * 1.4, y - r * 0.55, x + r * 1.4, y + r * 0.9], fill=(225, 234, 240, 120))
    cl = cl.filter(ImageFilter.GaussianBlur(W * 0.012))
    w = word(W, H, NAMES["air"], c8([c * 0.75 for c in col], 1.0, 235), y=H * 0.46, shadow=(120, 150, 170, 60))
    return back, cl, w           # clouds in front of the device's base: it floats above them

def dual(W, H, dev, t, wt):
    b = bbox_info(dev); c1 = RGB["dual"]; c2 = (1.0, 0.55, 0.35)
    back = Image.new("RGBA", (W, H), WHITE + (255,))
    off = W * 0.07 * (1 - ease(t / 1.2))                  # the two fields slide together
    cy = (b["top"] + b["bot"]) / 2
    back.alpha_composite(radial(W, H, b["cx"] - W * 0.06 - off, cy, W * 0.2, c1, 0.55))
    back.alpha_composite(radial(W, H, b["cx"] + W * 0.06 + off, cy, W * 0.2, c2, 0.45))
    sep = W * 0.012 * (1 - ease(t / 1.0))
    w = blank(W, H)
    w.alpha_composite(word(W, H, NAMES["dual"], c8([c * 0.85 for c in c2], 1.0, 200), x=W * 0.08 + sep, y=H * 0.5 + sep * 0.6))
    w.alpha_composite(word(W, H, NAMES["dual"], c8([c * 0.80 for c in c1], 1.0, 220), x=W * 0.08 - sep, y=H * 0.5 - sep * 0.6))
    return back, blank(W, H), w

def mask(W, H, dev, t, wt):
    col = RGB["mask"]
    back = Image.new("RGBA", (W, H), (244, 240, 248, 255))
    back.alpha_composite(radial(W, H, W * 0.55, H * 0.5, W * 0.35, mix(col, (1, 1, 1), 0.55), 0.35))
    drops = blank(W, H); d = ImageDraw.Draw(drops); rnd = random.Random(21)
    for i in range(160):                                  # condensation on the glass, heavier towards the edges
        x = rnd.uniform(0, W); y = rnd.uniform(0, H)
        edge = min(x, W - x, y, H - y) / (H * 0.5)
        if rnd.random() < edge * 0.8: continue
        r = W * rnd.uniform(0.002, 0.009)
        if i < 5: y = (y + t * H * 0.12 * (1 + i * 0.3)) % H   # a few drips slide down
        d.ellipse([x - r, y - r, x + r, y + r * 1.15], fill=(205, 195, 220, 120))
        d.ellipse([x - r * 0.75, y - r * 0.65, x + r * 0.55, y + r * 0.85], fill=(255, 255, 255, 140))
        d.ellipse([x - r * 0.45, y - r * 0.55, x - r * 0.1, y - r * 0.2], fill=(255, 255, 255, 235))
    w = word(W, H, NAMES["mask"], c8([c * 0.75 for c in col]), y=H * 0.5, shadow=(110, 80, 140, 70))
    # gloss: a highlight band across the letters
    hl = blank(W, H); ImageDraw.Draw(hl).rectangle([0, H * 0.45, W, H * 0.47], fill=(255, 255, 255, 120))
    hl.putalpha(ImageChops.multiply(hl.getchannel("A"), w.getchannel("A")))
    w.alpha_composite(hl)
    return back, drops, w

def ai(W, H, dev, t, wt):
    b = bbox_info(dev)
    back = Image.new("RGBA", (W, H), WHITE + (255,)); d = ImageDraw.Draw(back)
    g = max(8, int(W / 40))
    for x in range(0, W, g): d.line([(x, 0), (x, H)], fill=(225, 222, 224, 255), width=1)
    for y in range(0, H, g): d.line([(0, y), (W, y)], fill=(225, 222, 224, 255), width=1)
    front = blank(W, H); f = ImageDraw.Draw(front)
    sy = b["top"] + (b["bot"] - b["top"]) * ((t * 0.7) % 1.0)          # scan beam
    beam = blank(W, H); ImageDraw.Draw(beam).rectangle([b["cx"] - b["w"] * 2.2, sy - 2, b["cx"] + b["w"] * 2.2, sy + 2], fill=(90, 170, 255, 200))
    front.alpha_composite(beam.filter(ImageFilter.GaussianBlur(W * 0.004))); front.alpha_composite(beam)
    pad = b["w"] * 0.9; L = b["w"] * 0.6; x0, x1, y0, y1 = b["cx"] - pad, b["cx"] + pad, b["top"] - pad * 0.4, b["bot"] + pad * 0.4
    lw = max(1, int(W / 640)); k = (60, 70, 85, 230)
    for (px, py, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        f.line([(px, py), (px + dx * L, py)], fill=k, width=lw); f.line([(px, py), (px, py + dy * L)], fill=k, width=lw)
    small = ImageFont.truetype(HN, max(9, int(H * 0.022)), index=10)
    f.text((x1 + W * 0.01, y0), "ANALYZING", font=small, fill=k, anchor="lt")
    f.text((x1 + W * 0.01, y0 + H * 0.035), f"{int(min(1, t / 1.6) * 100):3d}%", font=small, fill=(90, 150, 230, 230), anchor="lt")
    n = max(1, int(len(NAMES["ai"]) * min(1, wt * 1.5)))            # typed in, with a cursor
    txt = NAMES["ai"][:n] + ("_" if int(t * 3) % 2 == 0 else " ")
    w = word(W, H, txt, (40, 46, 58, 255), y=H * 0.5)
    return back, front, w

def mix(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))
MOODS = dict(booster=booster, mc=mc, derma=derma, air=air, dual=dual, mask=mask, ai=ai)
LIFT = dict(air=-0.05)            # air: the device rides higher, above the clouds

def frame(mode, dev, t, wt=1.0):
    W, H = dev.size
    back, front, w = MOODS[mode](W, H, dev, t, wt)
    out = back.copy(); out.alpha_composite(w)
    lift = int(H * LIFT.get(mode, 0) * (0.5 + 0.5 * math.sin(t * 1.5)))
    out.alpha_composite(dev, (0, lift))
    out.alpha_composite(front)
    return out.convert("RGB")

if __name__ == "__main__":
    D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "render", "moods")
    order = ["booster", "mc", "derma", "air", "dual", "mask", "ai"]
    ims = []
    for m in order:
        dev = Image.open(os.path.join(D, f"dev_{m}.png")).convert("RGBA")
        im = frame(m, dev, 0.9, 1.0); im.save(os.path.join(D, f"mood_{m}.png")); ims.append(im)
    W, H = ims[0].size; tw, th = W // 2, H // 2
    sheet = Image.new("RGB", (tw * 4, th * 2), (30, 30, 30))
    for i, im in enumerate(ims): sheet.paste(im.resize((tw, th)), (tw * (i % 4), th * (i // 4)))
    sheet.save(os.path.join(D, "sheet.png")); print("style frames ->", D)

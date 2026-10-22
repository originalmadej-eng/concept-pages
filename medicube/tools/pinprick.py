"""Pin-prick type for the DERMA SHOT beat (user 2026-10-15 chose option A of tools/derma_type_options.py): the mode
name is a fine offset dot grid, like the marks a needle cartridge leaves. No glow, no effects: the dots are pricked in
all at once on the first needle shot (user 2026-10-15), each with a tiny pop, then stay still.

  lay = pinprick(W, H, "DERMA SHOT", frame, shots=(12, 24), centre_y=H * 0.30, gap=W * 0.11)
"""
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT = "/Library/Fonts/Inter-Black.ttf"
AMBER = (214, 122, 30)
SUB_FONT, SUB_COL = "/Library/Fonts/Inter-Medium.ttf", (120, 84, 60)   # official DERMA SHOT copy: "Facial Definition Care"
SS = 4                                              # supersampling for round dots

_cache = {}
def _dots(W, H, text, cy, gap, height_k, track_k, step_k, shots, seed):
    key = (W, H, text, int(cy), int(gap), height_k, track_k, step_k, shots, seed)
    if key in _cache: return _cache[key]
    fnt = ImageFont.truetype(FONT, int(H * height_k)); track = H * track_k
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    a, b = text.split(" ", 1)
    def width(t): return sum(fnt.getlength(c) for c in t) + track * (len(t) - 1)
    for t, x in ((a, W / 2 - gap / 2 - width(a)), (b, W / 2 + gap / 2)):
        for c in t:
            d.text((x, cy), c, font=fnt, fill=255, anchor="lm"); x += fnt.getlength(c) + track
    step = max(3.0, H * step_k); rnd = random.Random(seed); dots = []
    px = m.filter(ImageFilter.GaussianBlur(step * 0.9)).load()      # depth inside the stroke -> dot size (halftone)
    y, row = 0.0, 0
    while y < H:
        x = (row % 2) * step / 2                       # offset rows, like a needle cartridge
        while x < W:
            v = px[int(x), int(y)] / 255
            if v > 0.30:
                dots.append((x, y, shots[0], min(1.0, (v - 0.22) / 0.55)))      # all at once on the first shot (user)
            x += step
        y += step; row += 1
    xs = [p[0] for p in dots]; ys = [p[1] for p in dots]
    box = (int(min(xs) - step), int(min(ys) - step), int(max(xs) + step), int(max(ys) + step))
    _cache[key] = (dots, step, box)
    return _cache[key]

def pinprick(W, H, text, frame, shots=(12, 24), centre_y=None, gap=None, height_k=0.17, track_k=0.010,
             step_k=0.0095, colour=AMBER, seed=11, sub=""):   # sub-line removed (user 2026-10-15)
    cy = H * 0.30 if centre_y is None else centre_y; gap = W * 0.11 if gap is None else gap
    dots, step, (x0, y0, x1, y1) = _dots(W, H, text, cy, gap, height_k, track_k, step_k, tuple(shots), seed)
    tile = Image.new("RGBA", ((x1 - x0) * SS, (y1 - y0) * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(tile)
    r0 = step * 0.42
    for x, y, t0, sz in dots:
        age = frame - t0
        if age < 0: continue
        k = max(0.0, 1 - age / 3)                      # the prick: a touch bigger and deeper, settling in ~3 frames
        r = r0 * (0.35 + 0.65 * sz) * (1 + 0.6 * k) * SS
        col = tuple(int(c * (1 - 0.25 * k)) for c in colour)
        cx, cy_ = (x - x0) * SS, (y - y0) * SS
        d.ellipse([cx - r, cy_ - r, cx + r, cy_ + r], fill=(*col, 255))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lay.alpha_composite(tile.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0))
    if sub and frame >= shots[0]:
        al = min(1.0, (frame - shots[0] + 1) / 3)
        f2 = ImageFont.truetype(SUB_FONT, int(H * 0.026)); tr = H * 0.012
        wsub = sum(f2.getlength(c) for c in sub) + tr * (len(sub) - 1)
        x = x0 + step; yb = y1 + H * 0.045 + (1 - al) * H * 0.01; dd = ImageDraw.Draw(lay)
        for c in sub:
            dd.text((x, yb), c, font=f2, fill=(*SUB_COL, int(255 * al)), anchor="ls"); x += f2.getlength(c) + tr
    return lay

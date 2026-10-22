"""DUAL beat, draft (user 2026-10-15: "듀얼은 지금까지 있는 것들을 섞어서 보여주기 두개씩").
Official DUAL copy: "Two Modes At Once / Combine two care modes at once" — so the frame is split on a slant and two
of the scenes already made play at the same time, pair after pair; "DUAL" is cut by the same line and takes each
side's mode colour. No claim about which modes can actually be paired (that is set in the AGE-R app, not verified).

  python3 tools/comp_dual.py render/dual_c
Sources (raw RGBA renders): render/pud_mc_nt (MC, no title), render/pud_derma_nt (DERMA SHOT), render/air (AIR SHOT).
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DST = sys.argv[1]; os.makedirs(DST, exist_ok=True)
W, H = 960, 540
WHITE = (247, 243, 241)
SKY_TOP, SKY_LOW = np.array((150, 196, 238), np.float32), np.array((228, 240, 250), np.float32)
FONT = "/Library/Fonts/Montserrat-Black.ttf"; LABEL = "/System/Library/Fonts/HelveticaNeue.ttc"
# name, source, first frame of the segment, device x on screen, background, colour
SCENES = {
    "mc":    ("MC", "render/pud_mc_nt", 14, 480, "white", (214, 96, 140)),
    "derma": ("DERMA SHOT", "render/pud_derma_nt", 6, 480, "white", (214, 122, 30)),
    "air":   ("AIR SHOT", "render/air", 16, 560, "sky", (86, 146, 206)),
}
PAIRS = [("mc", "derma"), ("derma", "air"), ("air", "mc")]
SEG, XF = 36, 6                      # frames per pair, crossfade between pairs
TILT = 0.20                          # slant of the dividing line

def sstep(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
_sky = None
def background(kind):
    global _sky
    if kind == "white":
        bg = Image.new("RGB", (W, H), WHITE)
        sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).ellipse([W * 0.28, H * 0.86, W * 0.72, H * 0.95], fill=120)
        return Image.composite(Image.new("RGB", (W, H), (200, 192, 190)), bg, sh.filter(ImageFilter.GaussianBlur(W * 0.016)))
    if _sky is None:
        y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None] ** 0.8
        _sky = Image.fromarray(np.broadcast_to(SKY_TOP * (1 - y) + SKY_LOW * y, (H, W, 3)).astype(np.uint8))
    return _sky.copy()

def scene_frame(key, k, centre_x):
    """frame k of the scene's segment, composited, shifted so its device sits at centre_x"""
    name, src, f0, dev_x, kind, col = SCENES[key]
    n = len([f for f in os.listdir(src) if f.endswith(".png")])
    f = min(n, f0 + k)
    im = background(kind).convert("RGBA"); im.alpha_composite(Image.open(os.path.join(src, f"f{f:04d}.png")).convert("RGBA"))
    out = Image.new("RGBA", (W, H), (*WHITE, 255)) if kind == "white" else background(kind).convert("RGBA")
    out.paste(im, (int(centre_x - dev_x), 0))
    return out

_mask = None
def left_mask():
    global _mask
    if _mask is None:
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon([(0, 0), (W / 2 + TILT * H / 2, 0), (W / 2 - TILT * H / 2, H), (0, H)], fill=255)
        _mask = m
    return _mask

def pair_frame(a, b, k):
    L = scene_frame(a, k, W * 0.27); R = scene_frame(b, k, W * 0.73)
    out = Image.composite(L, R, left_mask())
    d = ImageDraw.Draw(out)
    d.line([(W / 2 + TILT * H / 2, 0), (W / 2 - TILT * H / 2, H)], fill=(255, 255, 255, 255), width=3)
    # DUAL, cut by the same line: each half in its side's mode colour
    fnt = ImageFont.truetype(FONT, int(H * 0.12)); txt = Image.new("L", (W, H), 0)
    ImageDraw.Draw(txt).text((W / 2, H * 0.12), "DUAL", font=fnt, fill=255, anchor="mm")
    ca, cb = SCENES[a][5], SCENES[b][5]
    colour = Image.composite(Image.new("RGB", (W, H), ca), Image.new("RGB", (W, H), cb), left_mask())
    a_in = sstep(k / 8)
    out.paste(colour, (0, 0), txt.point(lambda v: int(v * a_in)))
    lf = ImageFont.truetype(LABEL, int(H * 0.028), index=10)
    for lab, x, c in ((SCENES[a][0], W * 0.10, ca), (SCENES[b][0], W * 0.90, cb)):
        d.text((x, H * 0.93), lab, font=lf, fill=(*c, int(255 * a_in)), anchor="lm" if x < W / 2 else "rm")
    return out

if __name__ == "__main__":
    i = 0
    for p, (a, b) in enumerate(PAIRS):
        for k in range(SEG):
            fr = pair_frame(a, b, k)
            if p > 0 and k < XF:                                 # crossfade from the previous pair's last frame
                prev = pair_frame(*PAIRS[p - 1], SEG - 1 + k)
                fr = Image.blend(prev, fr, sstep((k + 1) / XF))
            i += 1; fr.convert("RGB").save(os.path.join(DST, f"f{i:04d}.png"))
    print(i, "frames ->", DST)

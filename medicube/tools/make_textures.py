"""Textures for the Booster Pro X2 reconstruction (body print, head emblem mask, screen UI, collar slots).

Measurements come from ref/BoosterProX2_08.jpg (device 254 px wide, 1308 px tall):
  button  x 240-340, y 1148-1233   |   logo  y 1540-1770 (vertical, reading bottom->top)
  screen  x 240-340, y  830-1090   |   body  y 690-1820
Run:  python3 tools/make_textures.py [--mode MASK --level 5 --time 0:00 --color pink]
"""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "render", "tex")
os.makedirs(OUT, exist_ok=True)
args = sys.argv[1:]
def arg(n, d): return args[args.index(n) + 1] if n in args else d

AV = "/System/Library/Fonts/Avenir Next.ttc"
HN = "/System/Library/Fonts/HelveticaNeue.ttc"
def font(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)

# photo -> metres
PX = 0.034 / 254          # m per photo px
R = 0.017
BODY_TOP_Y, BODY_BOT_Y = 690, 1820
BODY_H = (BODY_BOT_Y - BODY_TOP_Y) * PX
CIRC = 2 * math.pi * R
CX = 289

def uv_from_photo(x, y):
    """front-centre u=0.5; v=1 at body top."""
    a = math.asin(max(-0.999, min(0.999, (x - CX) / 127.0)))
    u = 0.5 + a / (2 * math.pi)
    v = (BODY_BOT_Y - y) / (BODY_BOT_Y - BODY_TOP_Y)
    return u, v

# ---------------------------------------------------------------- body
def body(color):
    TW = 2048; TH = round(TW * BODY_H / CIRC)
    base = {"pink": (206, 172, 170), "white": (236, 235, 233)}[color]
    ink = {"pink": (160, 112, 118), "white": (150, 148, 147)}[color]  # ref 08: logo reads clearly darker than the shell
    im = Image.new("RGB", (TW, TH), base); d = ImageDraw.Draw(im)
    def P(x, y):
        u, v = uv_from_photo(x, y); return u * TW, (1 - v) * TH
    # MODE button: rounded-square outline + label
    x0, y0 = P(240, 1148); x1, y1 = P(340, 1233)
    d.rounded_rectangle([x0, y0, x1, y1], radius=(x1 - x0) * 0.28, outline=ink, width=4)
    d.text(((x0 + x1) / 2, (y0 + y1) / 2), "MODE", font=font(AV, int((y1 - y0) * 0.16), 5), fill=ink, anchor="mm")
    # medicube wordmark, vertical (reads bottom -> top); custom logotype approximated with Avenir Next
    lx0, ly1 = P(280, 1770); lx1, ly0 = P(300, 1540)
    L = ly1 - ly0
    word = Image.new("RGBA", (int(L), int(L * 0.2)), (0, 0, 0, 0)); wd = ImageDraw.Draw(word)
    f = font(AV, int(L * 0.17), 2)
    wd.text((0, L * 0.1), "medicube", font=f, fill=ink, anchor="lm")
    w = wd.textlength("medicube", font=f); s = L * 0.09
    bx = w + s * 0.25; by = L * 0.1 - s * 1.0
    wd.rectangle([bx, by, bx + s, by + s], fill=ink)
    wd.rectangle([bx + s * 0.4, by + s * 0.15, bx + s * 0.6, by + s * 0.85], fill=base)
    wd.rectangle([bx + s * 0.15, by + s * 0.4, bx + s * 0.85, by + s * 0.6], fill=base)
    word = word.rotate(90, expand=True)
    im.paste(word, (int((lx0 + lx1) / 2 - word.width / 2), int(ly0)), word)
    im.save(os.path.join(OUT, f"body_{color}.png"))
    # height map: the MODE key is a slightly domed pad (ref 08 / 16 show it standing proud of the shell)
    bump = Image.new("L", (TW, TH), 0)
    ImageDraw.Draw(bump).rounded_rectangle([x0 + 3, y0 + 3, x1 - 3, y1 - 3], radius=(x1 - x0) * 0.28, fill=255)
    bump.filter(ImageFilter.GaussianBlur(5)).save(os.path.join(OUT, "body_bump.png"))
    return TW, TH

# ---------------------------------------------------------------- screen (black panel incl. power icon)
def screen(mode, level, t, name="screen"):
    W, H = 520, 1360
    ui = Image.new("RGB", (W, H), (0, 0, 0)); d = ImageDraw.Draw(ui)
    alpha = Image.new("L", (W, H), 0); ad = ImageDraw.Draw(alpha)
    ad.rounded_rectangle([0, 0, W - 1, H - 1], radius=110, fill=255)
    ad.rectangle([0, 1046, W, 1060], fill=0)   # the power key is its own black block below the display
    if mode != "OFF":
        white = (240, 240, 240)
        # status bar
        d.rounded_rectangle([340, 70, 450, 110], radius=8, outline=white, width=4)
        for i in range(4): d.rectangle([350 + i * 24, 78, 366 + i * 24, 102], fill=white)
        fs = 92
        while font(HN, fs, 1).getlength(mode) > W - 90: fs -= 4
        d.text((W / 2, 300), mode, font=font(HN, fs, 1), fill=white, anchor="mm")
        # level arc
        cx, cy, rr = W / 2, 560, 170
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 150, 390, fill=(90, 90, 90), width=18)
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 150, 150 + 240 * int(level) / 6, fill=white, width=18)
        d.text((cx, cy), str(level), font=font(HN, 150, 1), fill=white, anchor="mm")
        d.text((W / 2, 860), t, font=font(HN, 150, 0), fill=white, anchor="mm")
    # power glyph near the bottom of the panel
    g = (210, 210, 210); px, py, pr = W / 2, 1180, 44
    d.arc([px - pr, py - pr, px + pr, py + pr], 300, 600, fill=g, width=10)
    d.line([px, py - pr - 8, px, py], fill=g, width=10)
    ui.save(os.path.join(OUT, f"{name}.png")); alpha.save(os.path.join(OUT, "screen_alpha.png"))

# mode names as the official page lists them (medicube.us/en-jp/products/booster-pro-x2)
MODES = {"booster": "BOOSTER", "mc": "MC", "derma": "DERMA SHOT", "air": "AIR SHOT",
         "dual": "DUAL", "mask": "MASK", "ai": "AI"}

# ---------------------------------------------------------------- head emblem (planar map over the lens, apex towards +Y)
def rt_radius(theta, R0, apex=math.pi / 2, a=0.10):
    """convex rounded triangle (guitar-pick): corners at apex, apex±120°, max radius R0."""
    return R0 * (1 + a * math.cos(3 * (theta - apex))) / (1 + a)

def rt_poly(cx, cy, R0, n=360, flip=True):
    pts = []
    for i in range(n):
        th = 2 * math.pi * i / n
        r = rt_radius(th, R0)
        pts.append((cx + r * math.cos(th), cy - r * math.sin(th) if flip else cy + r * math.sin(th)))
    return pts

def emblem():
    S = 2048; c = S / 2; R0 = S / 2 * 0.98          # lens fills the map
    metal = Image.new("L", (S, S), 0); md = ImageDraw.Draw(metal)
    md.polygon(rt_poly(c, c, R0 * 0.93), fill=255)  # electrode outer edge
    md.polygon(rt_poly(c, c, R0 * 0.76), fill=0)    # window opening
    md.rectangle([0, c - R0 * 0.07, S, c + R0 * 0.07], fill=255)  # bar across, perpendicular to the apex axis
    edge = Image.new("L", (S, S), 0); ImageDraw.Draw(edge).polygon(rt_poly(c, c, R0 * 0.93), fill=255)
    metal = Image.composite(metal, Image.new("L", (S, S), 0), edge)
    metal.save(os.path.join(OUT, "emblem_metal.png"))
    # LED dots inside each window
    led = Image.new("L", (S, S), 0); ld = ImageDraw.Draw(led)
    for dy in (-R0 * 0.38, R0 * 0.36):
        ld.ellipse([c - R0 * 0.07, c + dy - R0 * 0.07, c + R0 * 0.07, c + dy + R0 * 0.07], fill=255)
    led.save(os.path.join(OUT, "emblem_led.png"))

# ---------------------------------------------------------------- collar slots (u around)
def collar():
    W, H = 2048, 128
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    for i in range(3):
        u0 = i / 3 + 0.03; u1 = (i + 1) / 3 - 0.03
        d.rounded_rectangle([u0 * W, H * 0.3, u1 * W, H * 0.72], radius=H * 0.2, fill=255)
    m.save(os.path.join(OUT, "collar_slots.png"))

if __name__ == "__main__":
    for col in ("pink", "white"):
        body(col)
    screen(arg("--mode", "MASK"), arg("--level", "5"), arg("--time", "0:00"))
    for k, v in MODES.items():
        screen(v, arg("--level", "5"), arg("--time", "0:00"), f"screen_{k}")
    emblem(); collar()
    print("textures ->", os.path.abspath(OUT))

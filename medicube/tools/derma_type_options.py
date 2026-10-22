"""Three quiet type directions for "DERMA SHOT" on one derma frame, to choose from (user 2026-10-15: no big effects;
"what does derma feel like?"):
  A  pin-prick dots: the letters are made of a fine dot grid, the same pattern the needles leave
  B  precise: a thin, widely tracked sans, clinical
  C  sculpted: the official "Sculpted-Looking Skin" — letters pressed into the white, only light and shadow
  python3 tools/derma_type_options.py render/pud_derma_nt/f0030.png render/derma_type_options.png
"""
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

F = "/Library/Fonts/"
AMBER = (214, 122, 30)
WHITE = (247, 243, 241)

def words(W, H, fnt, cy, gap, track=0.0, text="DERMA SHOT"):
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    a, b = text.split(" ")
    def width(t): return sum(fnt.getlength(c) for c in t) + track * (len(t) - 1)
    for t, x in ((a, W / 2 - gap / 2 - width(a)), (b, W / 2 + gap / 2)):
        for c in t:
            d.text((x, cy), c, font=fnt, fill=255, anchor="lm"); x += fnt.getlength(c) + track
    return m

def option_a(W, H, cy, gap):
    m = words(W, H, ImageFont.truetype(F + "Inter-Black.ttf", int(H * 0.13)), cy, gap, track=H * 0.008)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); step = max(3, int(H * 0.0105)); r = step * 0.30
    px = m.load()
    for y in range(0, H, step):
        for x in range((y // step % 2) * step // 2, W, step):           # offset rows, like a needle cartridge
            if px[x, y] > 128: d.ellipse([x - r, y - r, x + r, y + r], fill=(*AMBER, 255))
    return lay

def option_b(W, H, cy, gap):
    m = words(W, H, ImageFont.truetype(F + "Inter-ExtraLight.ttf", int(H * 0.085)), cy, gap, track=H * 0.03)
    lay = Image.new("RGBA", (W, H), (*AMBER, 0)); lay.putalpha(m); return lay

def option_c(W, H, cy, gap):
    m = words(W, H, ImageFont.truetype(F + "Sora-Bold.ttf", int(H * 0.12)), cy, gap, track=H * 0.01).filter(ImageFilter.GaussianBlur(1.2))
    o = max(1, int(H / 270))
    hi = ImageChops.subtract(ImageChops.offset(m, o, o), m)            # lit lower-right inner edge
    sh = ImageChops.subtract(ImageChops.offset(m, -o, -o), m)          # shadowed upper-left inner edge
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lay.alpha_composite(Image.merge("RGBA", [*Image.new("RGB", (W, H), (236, 226, 222)).split(), m.point(lambda v: v * 0.55)]))
    lay.alpha_composite(Image.merge("RGBA", [*Image.new("RGB", (W, H), (170, 140, 132)).split(), sh.point(lambda v: min(255, v * 2))]))
    lay.alpha_composite(Image.merge("RGBA", [*Image.new("RGB", (W, H), (255, 255, 255)).split(), hi.point(lambda v: min(255, v * 2))]))
    return lay

if __name__ == "__main__":
    dev = Image.open(sys.argv[1]).convert("RGBA"); W, H = dev.size
    tiles = []
    for name, fn in (("A  pin-prick dots", option_a), ("B  precise thin", option_b), ("C  sculpted (pressed in)", option_c)):
        bg = Image.new("RGBA", (W, H), (*WHITE, 255))
        bg.alpha_composite(fn(W, H, H * 0.30, W * 0.11)); bg.alpha_composite(dev)
        ImageDraw.Draw(bg).text((12, 10), name, fill=(110, 110, 110), font=ImageFont.truetype(F + "Inter-Medium.ttf", 16))
        tiles.append(bg.convert("RGB"))
    sheet = Image.new("RGB", (W, H * 3))
    for i, t in enumerate(tiles): sheet.paste(t, (0, H * i))
    sheet.save(sys.argv[2]); print(sys.argv[2])

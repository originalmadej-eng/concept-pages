"""Shared timeline for the 'Showcase' ad shot (8 s @ 24 fps): used by make_screen_seq.py (system python, draws the
screen UI per frame) and shot_showcase.py (Blender, keys LED colour / backdrop / camera to the same frames).

Mode names, 7 modes and 6 intensity levels: medicube.us/en-jp/products/booster-pro-x2 (2026-10-14).
"X2" suffix only on the modes the official layering guide calls X2 (Booster X2 > MC X2 > Derma Shot X2 > Dual).
Levels shown per mode are illustrative values within the official 1-6 range.
"""
FPS, FR = 24, 336                 # 14 s: each mode holds ~1.4 s (v2, the fast 8 s cut: showcase_timeline_v2.py)
SPIN_END = 48                     # intro float, screen off
BOOT0, BOOT1 = 48, 62             # boot logo
BEAT = 34
SWITCHES = [(64 + BEAT * i, m) for i, m in enumerate(["booster", "mc", "derma", "air", "dual", "mask", "ai"])] + [(64 + BEAT * 7, "booster")]
OUTRO = SWITCHES[-1][0]           # 302: back to Booster, closing title
NAMES = {"booster": "BOOSTER", "mc": "MC", "derma": "DERMA SHOT", "air": "AIR SHOT", "dual": "DUAL", "mask": "MASK", "ai": "AI"}
X2 = {"booster", "mc", "derma"}
LEVEL = {"booster": 6, "mc": 3, "derma": 5, "air": 2, "dual": 4, "mask": 3, "ai": 5}   # neighbours always differ
# same values as LED_RGB in render_device.py (sampled from the official mode images)
RGB = {"booster": (1.0, 0.32, 0.12), "mc": (0.35, 1.0, 0.3), "derma": (1.0, 0.62, 0.15),
       "air": (0.25, 0.85, 1.0), "mask": (0.62, 0.3, 1.0), "dual": (1.0, 0.8, 0.25), "ai": (1.0, 0.95, 0.9)}

def mode_at(f):
    """(current mode, previous mode, frames since switch) — None before the UI comes up"""
    cur = prev = None; t0 = None
    for fr, m in SWITCHES:
        if f >= fr: prev, cur, t0 = cur, m, fr
    return (cur, prev, f - t0) if cur else (None, None, 0)

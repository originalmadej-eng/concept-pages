"""Five-shot ad film for Booster Pro X2 (24 fps). Screen/LED schedules per shot; shared by make_screen_seq.py,
shot_ad.py (Blender) and comp_ad.py.
 s1  logo pan along the device lying down, backlight with rays, a light sweep tracing the curve
 s2  device rises upright while the camera climbs the body to the display; power on
 s3  bird's-eye on the head: the mode colours step through
 s4  end-over-end 360 while the camera pulls out to the whole device
 s5  modes change on the display; the mode list as the only graphic
"""
FPS = 24
ORDER = ["booster", "mc", "derma", "air", "dual", "mask", "ai"]
NEVER = -999
SHOTS = {
    "s1": dict(FR=96, BOOT0=NEVER, BOOT1=NEVER, SWITCHES=[], LED=False),
    "s2": dict(FR=96, BOOT0=40, BOOT1=54, SWITCHES=[(56, "booster")], LED=True),
    "s3": dict(FR=96, BOOT0=NEVER, BOOT1=NEVER, SWITCHES=[(1 + 13 * i, m) for i, m in enumerate(ORDER)], LED=True),
    "s4": dict(FR=72, BOOT0=NEVER, BOOT1=NEVER, SWITCHES=[(NEVER, "booster")], LED=True),
    "s5": dict(FR=144, BOOT0=NEVER, BOOT1=NEVER,
               SWITCHES=[(NEVER, "booster")] + [(16 + 18 * i, m) for i, m in enumerate(ORDER[1:])] + [(16 + 18 * 6, "booster")], LED=True),
}
XFADE = 6      # frames of cross-dissolve between shots

# One continuous move, no cuts (user 2026-10-15: "전부 이어서 움직이게"). Phases (frames):
#  A 1-96 logo macro pan | B 96-228 rises, camera climbs to the display, settles, then power on | C 228-324 over the top,
#  bird's-eye, colours step | D 324-396 end-over-end 360 while pulling out | E 396-540 modes change, mode list graphic
FILM = dict(FR=540, BOOT0=188, BOOT1=202, LED=True,       # B: the camera settles on the display (182), then it powers on
            SWITCHES=[(204, "booster")] + [(244 + 12 * i, m) for i, m in enumerate(ORDER[1:])] + [(324, "booster")]
                     + [(414 + 18 * i, m) for i, m in enumerate(ORDER[1:])] + [(522, "booster")],
            E_START=396)
SHOTS["film"] = FILM

# v2 choreography (user 2026-10-15, "일단 여기까지"): 1 logo -> display along the body, rising upright, power on at
# arrival | 2 up to the cap, LED on, colours step to white, dive into the lens = white-out | 3 white becomes the
# backdrop; the device flies in from the right spinning 360 end-over-end and 360 around, lands right of centre |
# 4 "BOOSTER" drops into the left with a little settle | 5 the word flies at us, strikes the device's base, the device
# turns once and switches to MC; "MC" drops in.
FILM2 = dict(FR=516, BOOT0=190, BOOT1=204, LED=True, LED_ON=262, WHITE0=314, WHITE1=332, FLY0=334, LAND=384,
             DROP1=392, HIT=456, DROP2=468,
             SWITCHES=[(206, "booster"), (270, "mc"), (278, "derma"), (286, "air"), (294, "dual"), (302, "mask"),
                       (310, "ai"), (334, "booster"), (462, "mc")])
SHOTS["film2"] = FILM2

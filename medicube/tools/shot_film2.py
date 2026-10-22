"""Booster Pro X2 film, v2 choreography (tools/ad_timeline.py FILM2), rendered on a transparent film:
 1 the camera rides along the body from the wordmark, past the MODE key, to the display while the device turns upright;
   the display powers on once the camera has settled
 2 up over the cap, the LED comes on and steps through the colours to white, the camera dives into the lens (white-out
   is finished in comp_film2.py)
 3 on white: the device flies in from the right turning 360 end over end and 360 around, and lands right of centre
 4-5 (graphics in comp_film2.py) "BOOSTER" drops in; the word strikes the base, the device turns once, MC.

  python3 tools/make_screen_seq.py --shot film2
  /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/shot_film2.py -- --out render/film2/ --res 960x540 --samples 24 [--still N,M]
"""
import bpy, math, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ad_timeline import FILM2 as F2, FPS

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d
OUTDIR = arg("--out", "render/film2/")

sys.argv = [sys.argv[0], "--", "--bg", "dark", "--led", "booster", "--color", arg("--color", "pink"),
            "--res", arg("--res", "960x540"), "--samples", arg("--samples", "24"), "--no_render", "1"]
_mine = (OUTDIR, argv)
exec(compile(open(os.path.join(HERE, "render_device.py")).read(), "render_device.py", "exec"))
OUTDIR, argv = _mine
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d

FR = F2["FR"]
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, FR; scene.render.fps = FPS
def fcurves(idb):
    ad = idb.animation_data
    return ad.action.fcurves if ad and ad.action else []
def smooth(idb):
    for fc in fcurves(idb):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"; kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
def set_kp(idb, frame, interp, easing="AUTO"):
    for fc in fcurves(idb):
        for kp in fc.keyframe_points:
            if round(kp.co[0]) == frame: kp.interpolation = interp; kp.easing = easing
def deg(v): return [math.radians(x) for x in v]
def sstep(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

bpy.data.objects["Cyc"].hide_render = True
scene.render.film_transparent = True
bpy.data.objects["Rim"].visible_glossy = False
bpy.data.objects["TopCard"].visible_glossy = False

C0 = Vector((0, 0, 0.09)); Z = C0.z
flt = bpy.data.objects.new("Float", None); scene.collection.objects.link(flt); flt.location = C0
device.parent = flt; device.location = (0, 0, -0.083); device.rotation_euler = (0, 0, 0)
Z_SCR_L = (z_s0 + z_s1) / 2                      # display centre, device-local height
Z_TOP_W = Z - 0.083 + Z_LENS

# ---------------------------------------------------------------- lens reads in its LED colour from above
lnt = bpy.data.materials["Lens"].node_tree
lp = next(nd for nd in lnt.nodes if nd.type == "BSDF_PRINCIPLED" and nd.inputs["Transmission Weight"].default_value > 0)
lp.inputs["Base Color"].default_value = (0.05, 0.05, 0.055, 1); lp.inputs["Specular IOR Level"].default_value = 0.15

# ---------------------------------------------------------------- display: UI sequence + a crisp "on"
snt = bpy.data.materials["Screen"].node_tree
ui = next(nd for nd in snt.nodes if nd.type == "TEX_IMAGE" and nd.image and nd.image.name.startswith("screen"))
seq = bpy.data.images.load(os.path.join(TEX, "screen_film2", "0001.png")); seq.source = "SEQUENCE"
ui.image = seq; ui.image_user.frame_duration = FR; ui.image_user.frame_start = 1; ui.image_user.use_auto_refresh = True
es = next(nd for nd in snt.nodes if nd.type == "BSDF_PRINCIPLED").inputs["Emission Strength"]; full_s = es.default_value
for f, v in ((F2["BOOT0"], full_s), (F2["BOOT0"] + 1, full_s * 1.8), (F2["BOOT0"] + 7, full_s)):
    es.default_value = v; es.keyframe_insert("default_value", frame=f)

# ---------------------------------------------------------------- LED: off until the camera is over the cap, then colours
sw = F2["SWITCHES"]
for mname in ("Ring", "Lens"):
    nt = bpy.data.materials[mname].node_tree
    for nd in nt.nodes:
        socks = []
        if nd.type == "BSDF_PRINCIPLED" and not nd.inputs["Emission Strength"].is_linked and nd.inputs["Emission Strength"].default_value > 0:
            socks.append(nd.inputs["Emission Strength"])
        if nd.type == "MATH" and nd.operation == "MULTIPLY_ADD":
            socks += [nd.inputs[1], nd.inputs[2]]
        for sk in socks:
            fullv = sk.default_value
            sk.default_value = 0; sk.keyframe_insert("default_value", frame=F2["LED_ON"] - 1)
            sk.default_value = fullv; sk.keyframe_insert("default_value", frame=F2["LED_ON"] + 6)
        if nd.type == "BSDF_PRINCIPLED":
            ec = nd.inputs["Emission Color"]
            for i, (f, m) in enumerate(sw):
                if i > 0:
                    ec.default_value = (*LED_RGB[sw[i - 1][1]], 1); ec.keyframe_insert("default_value", frame=f)
                ec.default_value = (*LED_RGB[m], 1); ec.keyframe_insert("default_value", frame=f + (3 if i > 0 else 0))
    for fc in fcurves(nt):
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"

# ---------------------------------------------------------------- light sweeps (seen only in reflection)
def sweep(f0, f1, p0, p1, size, strength):
    c = card("Sweep", p0, size, strength, (1.0, 0.96, 0.92), look=(0, 0, Z)); c.visible_diffuse = False
    for f, p in ((f0, p0), (f1, p1)):
        c.location = p; c.keyframe_insert("location", frame=f)
    for fc in fcurves(c):
        for kp in fc.keyframe_points: kp.interpolation = "SINE"; kp.easing = "EASE_IN_OUT"
sweep(6, 92, (-0.06, -0.22, Z + 0.16), (-0.06, -0.22, Z - 0.14), (0.40, 0.012), 90.0)
sweep(110, 176, (-0.20, -0.22, Z - 0.12), (-0.20, -0.22, Z + 0.16), (0.40, 0.012), 60.0)

# ---------------------------------------------------------------- device
L_OFF = (0.05, 0, 0)                               # resting place in the white part: right of centre
POSE = [
    (1,   (0, 90, 0), (0, 0, 0)),
    (100, (0, 90, 0), (0, 0, 0)),
    (172, (0, 0, 0), (0, 0, 0)),                   # upright as the camera reaches the display
    (230, (0, 0, 0), (0, 0, 0)),
    (262, (0, 0, 18), (0, 0, 0)),
    (332, (0, 0, 46), (0, 0, 0)),
    (F2["FLY0"] - 1, (-360, 0, 346), (0.42, 0, 0.05)),   # off screen right (hidden by the white-out)
    (F2["LAND"], (0, 0, -14), L_OFF),
    (F2["HIT"], (0, 0, -14), L_OFF),
    (F2["HIT"] + 6, (-14, 0, 100), (0.05, 0, 0.004)),     # struck at the base: kicks and turns once
    (F2["HIT"] + 26, (0, 0, 346), L_OFF),
    (FR, (0, 0, 348), L_OFF),
]
for f, rot, off in POSE:
    flt.rotation_euler = deg(rot); flt.location = C0 + Vector(off)
    flt.keyframe_insert("rotation_euler", frame=f); flt.keyframe_insert("location", frame=f)
smooth(flt)
set_kp(flt, 100, "SINE", "EASE_IN_OUT")
set_kp(flt, 332, "CONSTANT")
set_kp(flt, F2["FLY0"] - 1, "QUART", "EASE_OUT")         # fast in, settles
set_kp(flt, F2["HIT"], "LINEAR")
set_kp(flt, F2["HIT"] + 6, "CUBIC", "EASE_OUT")

# ---------------------------------------------------------------- camera
cam = scene.camera
for c in list(cam.constraints): cam.constraints.remove(c)
tgt = bpy.data.objects.new("Target", None); scene.collection.objects.link(tgt)
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
# 1: ride along the body: sample the device's own surface point each frame, camera straight in front of it
for f in range(1, 181, 2):
    scene.frame_set(f); bpy.context.view_layer.update()
    if f <= 96:
        zl = 0.012 + 0.018 * sstep(f / 96); dist = 0.12
    else:
        t = (f - 96) / 84; zl = 0.030 + (Z_SCR_L - 0.030) * sstep(t); dist = 0.12 + 0.05 * sstep(t)
    P = device.matrix_world @ Vector((0, -R, zl))
    cam.location = P + Vector((0, -dist, 0.003)); cam.keyframe_insert("location", frame=f)
    tgt.location = P; tgt.keyframe_insert("location", frame=f)
last_cam, last_tgt = cam.location.copy(), tgt.location.copy()     # the last sampled frame (179): hold there
scene.frame_set(1)
CAM = [  # frame, camera, target
    (230, last_cam, last_tgt),
    (262, Vector((0, -0.07, Z_TOP_W + 0.20)), Vector((0, 0, Z_TOP_W))),            # 2: up over the cap
    (310, Vector((0, -0.05, Z_TOP_W + 0.14)), Vector((0, 0, Z_TOP_W))),
    (332, Vector((0, -0.002, Z_TOP_W + 0.010)), Vector((0, 0, Z_TOP_W - 0.01))),     # dive into the white
    (F2["FLY0"] - 1, Vector((0, -0.68, Z + 0.02)), Vector((0.02, -0.01, Z + 0.004))),       # 3: cut hidden by white
    (FR, Vector((0.004, -0.65, Z + 0.02)), Vector((0.02, -0.01, Z + 0.004))),
]
for f, loc, look in CAM:
    cam.location = loc; cam.keyframe_insert("location", frame=f)
    tgt.location = look; tgt.keyframe_insert("location", frame=f)
smooth(cam); smooth(tgt)
set_kp(cam, 332, "CONSTANT"); set_kp(tgt, 332, "CONSTANT")
for f, L in ((1, 85), (332, 85), (F2["FLY0"] - 1, 60), (FR, 60)):
    cam.data.lens = L; cam.data.keyframe_insert("lens", frame=f)
set_kp(cam.data, 332, "CONSTANT")
cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt; cam.data.dof.aperture_fstop = 5.6

scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = 0.35
scene.render.image_settings.color_mode = "RGBA"
scene.render.use_persistent_data = True
if arg("--still", ""):
    for f in [int(x) for x in arg("--still", "1").split(",")]:
        scene.frame_set(f)
        scene.render.filepath = os.path.join(ROOT, OUTDIR, f"f{f:04d}.png"); bpy.ops.render.render(write_still=True)
else:
    scene.render.filepath = os.path.join(ROOT, OUTDIR, "f"); bpy.ops.render.render(animation=True)
print("WROTE film2", OUTDIR)

"""Booster Pro X2 ad film as ONE continuous camera move, no cuts (phases in tools/ad_timeline.py FILM):
 A logo macro pan on the device lying down -> B it rises while the camera climbs to the display, power on ->
 C the camera lifts over the cap, bird's-eye, the mode colours step -> D end-over-end 360 while pulling out ->
 E modes change (mode list added in comp_film.py). Transparent film; backdrop/bloom/list composited afterwards.
(The five separate shots with dissolves are tools/shot_ad.py.)

  python3 tools/make_screen_seq.py --shot film
  /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/shot_film.py -- --out render/film/ --res 960x540 --samples 24 [--still N]
"""
import bpy, math, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ad_timeline import FILM, FPS

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d
OUTDIR = arg("--out", "render/film/")

sys.argv = [sys.argv[0], "--", "--bg", "dark", "--led", "booster", "--color", arg("--color", "pink"),
            "--res", arg("--res", "960x540"), "--samples", arg("--samples", "24"), "--no_render", "1"]
_mine = (OUTDIR, argv)
exec(compile(open(os.path.join(HERE, "render_device.py")).read(), "render_device.py", "exec"))
OUTDIR, argv = _mine
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d

FR = FILM["FR"]
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, FR; scene.render.fps = FPS
def fcurves(idb):
    ad = idb.animation_data
    return ad.action.fcurves if ad and ad.action else []
def smooth(idb):
    for fc in fcurves(idb):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"; kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
def deg(v): return [math.radians(x) for x in v]

bpy.data.objects["Cyc"].hide_render = True
scene.render.film_transparent = True
bpy.data.objects["Rim"].visible_glossy = False
bpy.data.objects["TopCard"].visible_glossy = False     # its reflection washed the lens out in the overhead views

C0 = Vector((0, 0, 0.09)); Z = C0.z
flt = bpy.data.objects.new("Float", None); scene.collection.objects.link(flt); flt.location = C0
device.parent = flt; device.location = (0, 0, -0.083); device.rotation_euler = (0, 0, 0)
Z_SCR_W = Z - 0.083 + (z_s0 + z_s1) / 2
Z_TOP_W = Z - 0.083 + Z_LENS

# ---------------------------------------------------------------- lens: darker frost so the LED colour reads from above
lnt = bpy.data.materials["Lens"].node_tree
lp = next(nd for nd in lnt.nodes if nd.type == "BSDF_PRINCIPLED" and nd.inputs["Transmission Weight"].default_value > 0)
lp.inputs["Base Color"].default_value = (0.05, 0.05, 0.055, 1)
lp.inputs["Specular IOR Level"].default_value = 0.15     # less grey sheen over the light

# ---------------------------------------------------------------- screen + LED schedule
snt = bpy.data.materials["Screen"].node_tree
ui = next(nd for nd in snt.nodes if nd.type == "TEX_IMAGE" and nd.image and nd.image.name.startswith("screen"))
seq = bpy.data.images.load(os.path.join(TEX, "screen_film", "0001.png")); seq.source = "SEQUENCE"
_es = next(nd for nd in snt.nodes if nd.type == "BSDF_PRINCIPLED").inputs["Emission Strength"]; _full = _es.default_value
for _f, _v in ((FILM["BOOT0"], _full), (FILM["BOOT0"] + 1, _full * 1.8), (FILM["BOOT0"] + 7, _full)):
    _es.default_value = _v; _es.keyframe_insert("default_value", frame=_f)
ui.image = seq; ui.image_user.frame_duration = FR; ui.image_user.frame_start = 1; ui.image_user.use_auto_refresh = True

sw = FILM["SWITCHES"]
for mname in ("Ring", "Lens"):
    nt = bpy.data.materials[mname].node_tree
    for nd in nt.nodes:
        socks = []
        if nd.type == "BSDF_PRINCIPLED" and not nd.inputs["Emission Strength"].is_linked and nd.inputs["Emission Strength"].default_value > 0:
            socks.append(nd.inputs["Emission Strength"])
        if nd.type == "MATH" and nd.operation == "MULTIPLY_ADD":
            socks += [nd.inputs[1], nd.inputs[2]]
        for sk in socks:
            if mname == "Lens": sk.default_value *= float(arg("--lensk", "1.0"))   # keeps the colour in the overhead views
            full = sk.default_value
            sk.default_value = 0; sk.keyframe_insert("default_value", frame=sw[0][0] - 1)
            sk.default_value = full; sk.keyframe_insert("default_value", frame=sw[0][0] + 8)
        if nd.type == "BSDF_PRINCIPLED":
            ec = nd.inputs["Emission Color"]
            for i, (f, m) in enumerate(sw):
                if i > 0:
                    ec.default_value = (*LED_RGB[sw[i - 1][1]], 1); ec.keyframe_insert("default_value", frame=f)
                ec.default_value = (*LED_RGB[m], 1); ec.keyframe_insert("default_value", frame=f + (4 if i > 0 else 0))
    for fc in fcurves(nt):
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"

# ---------------------------------------------------------------- light sweeps: strips seen only in reflection, sliding across the curve
def sweep(f0, f1, p0, p1, size, strength):
    c = card("Sweep", p0, size, strength, (1.0, 0.96, 0.92), look=(0, 0, Z))
    c.visible_diffuse = False                              # a travelling highlight, not a flash of light
    for f, p in ((f0, p0), (f1, p1)):
        c.location = p; c.keyframe_insert("location", frame=f)
    for fc in fcurves(c):
        for kp in fc.keyframe_points: kp.interpolation = "SINE"; kp.easing = "EASE_IN_OUT"
sweep(6, 92, (-0.06, -0.22, Z + 0.16), (-0.06, -0.22, Z - 0.14), (0.40, 0.012), 90.0)     # A: over the wordmark, top to bottom
sweep(120, 196, (-0.20, -0.22, Z - 0.12), (-0.20, -0.22, Z + 0.16), (0.40, 0.012), 60.0)  # B: up the body as it stands
sweep(424, 524, (0.30, -0.25, Z + 0.06), (-0.10, -0.25, Z + 0.06), (0.015, 0.45), 50.0)   # E: across

# ---------------------------------------------------------------- device path
POSE = [  # frame, rotation deg (x pitch, y lay, z turn), offset from C0
    (1,   (0, 90, -6), (0, 0, 0)),
    (96,  (0, 90, 0), (0, 0, 0)),
    (112, (0, 87, -1), (0, 0, 0)),
    (178, (0, 0, -14), (0, 0, 0)),
    (228, (0, 0, -11), (0, 0, 0)),                  # holds on the display while it powers on
    (324, (0, 0, 36), (0, 0, 0)),
    (370, (360, 0, -20), (0.03, 0, 0)),             # the 360 is quicker (46 frames, was 66)
    (402, (360, -6, -24), (0.04, 0, 0)),
]
# E: on every mode change the device leans left or right, alternately pivoting on its base or on its head, with a
# small turn. Pivot at the base: centre moves (h sin t, 0, h cos t - h); at the head: (-h sin t, 0, h - h cos t).
h = 0.083
LEAN = [(+9, "base", -12), (-8, "head", -26), (-10, "base", -4), (+8, "head", -20), (+10, "base", -30), (-7, "head", -8), (0, "base", -16)]
for (f, _), (t, piv, yaw) in zip([x for x in FILM["SWITCHES"] if x[0] >= FILM["E_START"]], LEAN):
    tr = math.radians(t)
    off = (h * math.sin(tr), 0, h * math.cos(tr) - h) if piv == "base" else (-h * math.sin(tr), 0, h - h * math.cos(tr))
    POSE.append((f + 12, (360, t, yaw), (0.04 + off[0], 0, off[2])))
POSE.append((FR, (360, 0, -12), (0.04, 0, 0)))
for f, rot, off in POSE:
    flt.rotation_euler = deg(rot); flt.location = C0 + Vector(off)
    flt.keyframe_insert("rotation_euler", frame=f); flt.keyframe_insert("location", frame=f)
smooth(flt)

# ---------------------------------------------------------------- one camera, never cut
cam = scene.camera
for c in list(cam.constraints): cam.constraints.remove(c)
tgt = bpy.data.objects.new("Target", None); scene.collection.objects.link(tgt)
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
CAM = [  # frame, camera, target
    (1,   (-0.072, -0.135, Z + 0.004), (-0.066, -0.017, Z)),          # A: only the wordmark in frame
    (96,  (-0.052, -0.133, Z + 0.006), (-0.048, -0.017, Z)),
    (140, (0.000, -0.32, Z - 0.02), (0, -0.01, Z)),                    # B: pulls back as it rises
    (182, (0.006, -0.175, Z_SCR_W + 0.004), (0, -0.017, Z_SCR_W + 0.002)),
    (228, (0.005, -0.166, Z_SCR_W + 0.006), (0, -0.017, Z_SCR_W + 0.003)),
    (264, (0.000, -0.07, Z_TOP_W + 0.20), (0, 0, Z_TOP_W)),            # C: lifts over the cap
    (322, (0.000, -0.05, Z_TOP_W + 0.15), (0, 0, Z_TOP_W)),
    (350, (0.000, -0.50, Z + 0.08), (0, 0, Z + 0.02)),                 # D: swings to the front, pulling out
    (390, (0.000, -0.76, Z + 0.02), (0, -0.01, Z)),
    (FR,  (0.010, -0.66, Z + 0.02), (0.005, -0.01, Z)),                # E: slow push
]
for f, loc, look in CAM:
    cam.location = loc; cam.keyframe_insert("location", frame=f)
    tgt.location = look; tgt.keyframe_insert("location", frame=f)
smooth(cam); smooth(tgt)
for f, L in ((1, 85), (324, 85), (396, 60), (FR, 60)):
    cam.data.lens = L; cam.data.keyframe_insert("lens", frame=f)
smooth(cam.data)
cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt; cam.data.dof.aperture_fstop = 5.6

scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = 0.3
scene.render.image_settings.color_mode = "RGBA"
scene.render.use_persistent_data = True
if arg("--still", ""):
    for f in [int(x) for x in arg("--still", "1").split(",")]:
        scene.frame_set(f)
        scene.render.filepath = os.path.join(ROOT, OUTDIR, f"f{f:04d}.png"); bpy.ops.render.render(write_still=True)
else:
    scene.render.filepath = os.path.join(ROOT, OUTDIR, "f"); bpy.ops.render.render(animation=True)
print("WROTE film", OUTDIR)

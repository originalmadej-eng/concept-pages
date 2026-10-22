"""Booster Pro X2 ad film, one shot per run (see tools/ad_timeline.py for the five shots).
Rendered on a transparent film; backdrop, backlight rays, bloom and the s5 mode list are added by tools/comp_ad.py.
All moves are smooth Bezier (auto-clamped, no overshoot, no noise) — nothing twitches.

  python3 tools/make_screen_seq.py --shot s2     (s2..s5)
  /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/shot_ad.py -- --shot s1 \
      --out render/ad/s1/ --res 960x540 --samples 24    [--still N]
"""
import bpy, math, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ad_timeline import SHOTS, FPS

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d
SHOT = arg("--shot", "s1"); CFG = SHOTS[SHOT]; OUTDIR = arg("--out", f"render/ad/{SHOT}/")

sys.argv = [sys.argv[0], "--", "--bg", "dark", "--led", "booster", "--color", arg("--color", "pink"),
            "--res", arg("--res", "960x540"), "--samples", arg("--samples", "24"), "--no_render", "1"]
_mine = (SHOT, CFG, OUTDIR, argv)
exec(compile(open(os.path.join(HERE, "render_device.py")).read(), "render_device.py", "exec"))
SHOT, CFG, OUTDIR, argv = _mine
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d

FR = CFG["FR"]
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

# ---------------------------------------------------------------- device on a centred pivot
C0 = Vector((0, 0, 0.09))
flt = bpy.data.objects.new("Float", None); scene.collection.objects.link(flt); flt.location = C0
device.parent = flt; device.location = (0, 0, -0.083); device.rotation_euler = (0, 0, 0)
Z_SCR_W = C0.z - 0.083 + (z_s0 + z_s1) / 2        # world height of the display centre when upright
Z_TOP_W = C0.z - 0.083 + Z_LENS                   # world height of the cap when upright

# ---------------------------------------------------------------- screen + LED schedule
snt = bpy.data.materials["Screen"].node_tree
psc = next(nd for nd in snt.nodes if nd.type == "BSDF_PRINCIPLED")
if CFG["SWITCHES"] or CFG["BOOT0"] > 0:
    ui = next(nd for nd in snt.nodes if nd.type == "TEX_IMAGE" and nd.image and nd.image.name.startswith("screen"))
    seq = bpy.data.images.load(os.path.join(TEX, f"screen_{SHOT}", "0001.png")); seq.source = "SEQUENCE"
    ui.image = seq; ui.image_user.frame_duration = FR; ui.image_user.frame_start = 1; ui.image_user.use_auto_refresh = True
else:
    psc.inputs["Emission Strength"].default_value = 0          # device off

sw = [(max(1, f), m) for f, m in CFG["SWITCHES"]]
for mname in ("Ring", "Lens"):
    nt = bpy.data.materials[mname].node_tree
    for nd in nt.nodes:
        socks = []
        if nd.type == "BSDF_PRINCIPLED" and not nd.inputs["Emission Strength"].is_linked and nd.inputs["Emission Strength"].default_value > 0:
            socks.append(nd.inputs["Emission Strength"])
        if nd.type == "MATH" and nd.operation == "MULTIPLY_ADD":
            socks += [nd.inputs[1], nd.inputs[2]]
        for sk in socks:
            if mname == "Lens": sk.default_value *= 0.25     # close-ups: keep the lens coloured, not blown to white
            full = sk.default_value
            if not CFG["LED"]:
                sk.default_value = 0
            elif sw and sw[0][0] > 1:                            # LED comes on with the first mode
                sk.default_value = 0; sk.keyframe_insert("default_value", frame=sw[0][0] - 1)
                sk.default_value = full; sk.keyframe_insert("default_value", frame=sw[0][0] + 6)
        if nd.type == "BSDF_PRINCIPLED" and sw:
            ec = nd.inputs["Emission Color"]
            for i, (f, m) in enumerate(sw):                     # 4-frame colour dissolve on every switch
                if i > 0:
                    ec.default_value = (*LED_RGB[sw[i - 1][1]], 1); ec.keyframe_insert("default_value", frame=f)
                ec.default_value = (*LED_RGB[m], 1); ec.keyframe_insert("default_value", frame=f + (4 if i > 0 else 0))
    for fc in fcurves(nt):
        for kp in fc.keyframe_points: kp.interpolation = "LINEAR"

# ---------------------------------------------------------------- light sweep: a soft strip travels across, tracing the curve
def sweep(f0, f1, p0, p1, size=(0.02, 0.45), strength=40.0, look=None):
    c = card("Sweep", p0, size, strength, (1.0, 0.96, 0.92), look=look or (0, 0, C0.z))
    for f, p in ((f0, p0), (f1, p1)):
        c.location = p; c.keyframe_insert("location", frame=f)
    for fc in fcurves(c):
        for kp in fc.keyframe_points: kp.interpolation = "SINE"; kp.easing = "EASE_IN_OUT"
    return c

# ---------------------------------------------------------------- camera rig
cam = scene.camera
for c in list(cam.constraints): cam.constraints.remove(c)
tgt = bpy.data.objects.new("Target", None); scene.collection.objects.link(tgt)
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
cam.data.dof.use_dof = True; cam.data.dof.focus_object = tgt
def cam_keys(keys):
    for f, loc, look in keys:
        cam.location = loc; cam.keyframe_insert("location", frame=f)
        tgt.location = look; tgt.keyframe_insert("location", frame=f)
    smooth(cam); smooth(tgt)
def pose_keys(keys):
    for f, rot, off in keys:
        flt.rotation_euler = deg(rot); flt.location = C0 + Vector(off)
        flt.keyframe_insert("rotation_euler", frame=f); flt.keyframe_insert("location", frame=f)
    smooth(flt)
Z = C0.z

if SHOT == "s1":      # lying down, head to the right; slow macro pan from the wordmark towards the head
    cam.data.lens = 85; cam.data.dof.aperture_fstop = 4.0
    pose_keys([(1, (0, 90, -12), (0, 0, 0)), (FR, (0, 90, 4), (0, 0, 0))])
    cam_keys([(1, (-0.060, -0.34, Z + 0.020), (-0.045, -0.017, Z)),
              (FR, (0.035, -0.32, Z + 0.024), (0.035, -0.017, Z))])
    sweep(8, 84, (-0.28, -0.20, Z + 0.10), (0.28, -0.20, Z + 0.10), (0.02, 0.40), 45.0)
elif SHOT == "s2":    # rises upright; the camera climbs the body and arrives on the display as it powers on
    cam.data.lens = 70; cam.data.dof.aperture_fstop = 4.0
    pose_keys([(1, (0, 90, 4), (0, 0, 0)), (12, (0, 86, 2), (0, 0, 0)), (70, (0, 0, -14), (0, 0, 0)), (FR, (0, 0, -9), (0, 0, 0))])
    cam_keys([(1, (0.00, -0.34, Z - 0.07), (0, 0, Z - 0.01)),
              (40, (0.00, -0.26, Z - 0.03), (0, -0.01, Z + 0.005)),
              (78, (0.006, -0.175, Z_SCR_W + 0.004), (0, -0.017, Z_SCR_W + 0.002)),
              (FR, (0.004, -0.165, Z_SCR_W + 0.006), (0, -0.017, Z_SCR_W + 0.003))])
    sweep(20, 92, (-0.20, -0.22, Z - 0.12), (-0.20, -0.22, Z + 0.16), (0.40, 0.02), 35.0)
elif SHOT == "s3":    # bird's-eye on the cap, a slow turn while the colours step through the modes
    cam.data.lens = 85; cam.data.dof.aperture_fstop = 5.6
    pose_keys([(1, (0, 0, -20), (0, 0, 0)), (FR, (0, 0, 40), (0, 0, 0))])
    cam_keys([(1, (0.0, -0.07, Z_TOP_W + 0.20), (0, 0, Z_TOP_W)),
              (FR, (0.0, -0.05, Z_TOP_W + 0.15), (0, 0, Z_TOP_W))])
elif SHOT == "s4":    # end over end, a full turn, while the camera pulls back to the whole device
    cam.data.lens = 60; cam.data.dof.aperture_fstop = 8.0
    pose_keys([(1, (0, 0, -14), (0, 0, 0)), (FR - 6, (360, 0, -14), (0, 0, 0)), (FR, (360, 0, -12), (0, 0, 0))])
    for fc in fcurves(flt):
        if fc.data_path == "rotation_euler" and fc.array_index == 0:
            for kp in fc.keyframe_points: kp.interpolation = "SINE"; kp.easing = "EASE_IN_OUT"
    cam_keys([(1, (0.0, -0.24, Z + 0.04), (0, 0, Z + 0.03)),
              (FR, (0.0, -0.72, Z + 0.02), (0, -0.01, Z))])
    scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = 0.4
elif SHOT == "s5":    # upright, right of centre; a slow push while the modes change
    cam.data.lens = 60; cam.data.dof.aperture_fstop = 8.0
    pose_keys([(1, (0, -6, -26), (0.040, 0, 0)), (FR, (0, -4, -6), (0.040, 0, 0))])
    cam_keys([(1, (0.0, -0.70, Z + 0.02), (0, -0.01, Z)),
              (FR, (0.01, -0.58, Z + 0.02), (0.005, -0.01, Z))])
    sweep(30, 120, (0.30, -0.25, Z + 0.06), (-0.10, -0.25, Z + 0.06), (0.02, 0.45), 30.0)

scene.render.image_settings.color_mode = "RGBA"
scene.render.use_persistent_data = True
if arg("--still", ""):
    f = int(arg("--still", "1")); scene.frame_set(f)
    scene.render.filepath = os.path.join(ROOT, OUTDIR, f"f{f:04d}.png"); bpy.ops.render.render(write_still=True)
else:
    scene.render.filepath = os.path.join(ROOT, OUTDIR, "f"); bpy.ops.render.render(animation=True)
print("WROTE", SHOT, OUTDIR)

"""Ad shot 'Showcase' v3 (14 s @ 24 fps): the device floats in the dark and glides slowly between upright, diagonal
and horizontal poses while the mode steps through all seven — screen UI and head LED change together. Rendered on a
transparent film; the backdrop glow and the typography are composited afterwards by tools/comp_showcase.py.
(v1 standing/fast: shot_showcase_v1.py, v2 floating/snappy: shot_showcase_v2.py.)
Timeline: tools/showcase_timeline.py; screen frames: tools/make_screen_seq.py.

  python3 tools/make_screen_seq.py
  /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/shot_showcase.py -- \
      --out render/shots/showcase/ --res 960x540 --samples 24        [--still N]
"""
import bpy, math, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from showcase_timeline import FR, FPS, SPIN_END, BOOT0, SWITCHES, RGB

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d
OUTDIR = arg("--out", "render/shots/showcase/")

sys.argv = [sys.argv[0], "--", "--bg", "dark", "--led", "booster", "--color", arg("--color", "pink"),
            "--res", arg("--res", "960x540"), "--samples", arg("--samples", "24"), "--no_render", "1"]
_mine = (FR, OUTDIR, argv)
exec(compile(open(os.path.join(HERE, "render_device.py")).read(), "render_device.py", "exec"))
FR, OUTDIR, argv = _mine
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d

scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, FR; scene.render.fps = FPS
def fcurves(idb):
    ad = idb.animation_data
    return ad.action.fcurves if ad and ad.action else []
def set_interp(fcs, kind, easing="AUTO"):
    for fc in fcs:
        for kp in fc.keyframe_points: kp.interpolation = kind; kp.easing = easing
UI_ON = SWITCHES[0][0]

# ---------------------------------------------------------------- screen: animated UI sequence
snt = bpy.data.materials["Screen"].node_tree
ui = next(nd for nd in snt.nodes if nd.type == "TEX_IMAGE" and nd.image and nd.image.name.startswith("screen"))
seq = bpy.data.images.load(os.path.join(TEX, "screen_seq", "0001.png")); seq.source = "SEQUENCE"
ui.image = seq
ui.image_user.frame_duration = FR; ui.image_user.frame_start = 1; ui.image_user.frame_offset = 0
ui.image_user.use_auto_refresh = True

# ---------------------------------------------------------------- LED: off until the UI comes up, colour per mode
for mname in ("Ring", "Lens"):
    nt = bpy.data.materials[mname].node_tree
    for nd in nt.nodes:
        socks = []
        if nd.type == "BSDF_PRINCIPLED" and not nd.inputs["Emission Strength"].is_linked and nd.inputs["Emission Strength"].default_value > 0:
            socks.append(nd.inputs["Emission Strength"])
        if nd.type == "MATH" and nd.operation == "MULTIPLY_ADD":
            socks += [nd.inputs[1], nd.inputs[2]]
        for sk in socks:
            full = sk.default_value
            sk.default_value = 0; sk.keyframe_insert("default_value", frame=UI_ON - 1)
            for fr, _ in SWITCHES:                           # a short swell on every switch
                sk.default_value = full * 1.3; sk.keyframe_insert("default_value", frame=fr + 2)
                sk.default_value = full; sk.keyframe_insert("default_value", frame=fr + 12)
        if nd.type == "BSDF_PRINCIPLED":
            for fr, m in SWITCHES:
                nd.inputs["Emission Color"].default_value = (*RGB[m], 1)
                nd.inputs["Emission Color"].keyframe_insert("default_value", frame=fr)
    for fc in fcurves(nt):
        frames = {round(kp.co[0]) for kp in fc.keyframe_points}
        set_interp([fc], "CONSTANT" if frames == {fr for fr, _ in SWITCHES} else "BEZIER")

# ---------------------------------------------------------------- no floor; transparent film (backdrop + type are composited)
bpy.data.objects["Cyc"].hide_render = True
scene.render.film_transparent = True
C0 = Vector((0, 0, 0.09))                         # where the device's centre floats (the dark rig is aimed here)
flt = bpy.data.objects.new("Float", None); scene.collection.objects.link(flt); flt.location = C0
device.parent = flt; device.location = (0, 0, -0.083); device.rotation_euler = (0, 0, 0)

# poses: (frame the pose is reached, rotation deg (x pitch to camera, y lay sideways, z turn), offset from C0).
# Every move glides over ~26 frames with a slow in/out; z keeps turning a little all the time so nothing ever stops.
S = {m: fr for fr, m in SWITCHES[:-1]}; OUT = SWITCHES[-1][0]
POSES = [
    (1,   (14, -22, -150), (0, 0, -0.006)),
    (S["booster"] - 4, (4, -8, -40), (0, 0, 0)),
    (S["booster"] + 24, (0, -6, -18), (0, 0, 0)),
    (S["mc"] + 26, (0, 84, -10), (0, 0, 0)),           # horizontal
    (S["derma"] + 26, (0, -32, 2), (0, 0, 0)),          # diagonal
    (S["air"] + 26, (18, -4, -24), (0, 0, 0.004)),      # upright, leaning in
    (S["dual"] + 26, (0, 28, -30), (0, 0, 0)),          # diagonal the other way
    (S["mask"] + 26, (62, 0, -16), (0, 0, 0.008)),      # head to the lens
    (S["ai"] + 26, (0, -84, 6), (0, 0, 0)),             # horizontal the other way
    (OUT + 26, (0, -4, -16), (0, 0, 0)),                # upright
    (FR, (0, -4, 30), (0, 0, 0)),                       # slow quarter turn under the title
]
for fr, rot, off in POSES:
    flt.rotation_euler = [math.radians(v) for v in rot]; flt.location = C0 + Vector(off)
    flt.keyframe_insert("rotation_euler", frame=fr); flt.keyframe_insert("location", frame=fr)
# hold each pose, drifting, until the next switch, then glide: a drifted copy of the pose 2 frames before the switch
for i in range(len(POSES) - 1):
    fr0, rot0, off0 = POSES[i]; fr1 = POSES[i + 1][0]
    sw = next((f for f, _ in SWITCHES if fr0 < f - 2 < fr1 - 6), None)
    if sw:
        flt.rotation_euler = [math.radians(v + d) for v, d in zip(rot0, (2, 2, 8))]; flt.location = C0 + Vector(off0)
        flt.keyframe_insert("rotation_euler", frame=sw - 2); flt.keyframe_insert("location", frame=sw - 2)
for fc in fcurves(flt):
    for kp in fc.keyframe_points:
        kp.interpolation = "SINE"; kp.easing = "EASE_IN_OUT"
# floating: slow, small noise on height and tilt
for fc in fcurves(flt):
    if (fc.data_path == "location" and fc.array_index == 2) or (fc.data_path == "rotation_euler" and fc.array_index in (0, 1)):
        nm = fc.modifiers.new("NOISE"); nm.scale = 70; nm.phase = fc.array_index * 7.3
        nm.strength = 0.005 if fc.data_path == "location" else 0.035

# ---------------------------------------------------------------- camera: slow breathing push, closer on the sideways poses
cam = scene.camera; cam.data.lens = 60
for c in list(cam.constraints): cam.constraints.remove(c)
tgt = bpy.data.objects.new("Target", None); scene.collection.objects.link(tgt)
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
CAMK = [  # frame, camera offset from C0, target offset from C0
    (1,                (0.00, -0.74, 0.03), (0, -0.01, 0)),
    (S["booster"] + 24, (0.00, -0.68, 0.02), (0, -0.01, 0)),
    (S["mc"] + 26,     (0.00, -0.44, 0.00), (0, -0.015, 0)),
    (S["derma"] + 26,  (-0.03, -0.60, 0.03), (0, -0.01, 0)),
    (S["air"] + 26,    (0.03, -0.60, -0.02), (0, -0.01, 0.005)),
    (S["dual"] + 26,   (0.00, -0.60, 0.02), (0, -0.01, 0)),
    (S["mask"] + 26,   (0.00, -0.42, 0.03), (0, -0.05, 0.025)),
    (S["ai"] + 26,     (0.00, -0.46, 0.00), (0, -0.015, 0)),
    (OUT + 26,         (0.00, -0.72, 0.02), (0, -0.01, 0)),
    (FR,               (0.00, -0.70, 0.02), (0, -0.01, 0)),
]
for fr, co_, to_ in CAMK:
    cam.location = C0 + Vector(co_); cam.keyframe_insert("location", frame=fr)
    tgt.location = C0 + Vector(to_); tgt.keyframe_insert("location", frame=fr)
for fc in list(fcurves(cam)) + list(fcurves(tgt)):
    for kp in fc.keyframe_points: kp.interpolation = "SINE"; kp.easing = "EASE_IN_OUT"
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 8.0; cam.data.dof.focus_object = tgt

# ---------------------------------------------------------------- render (no compositor: bloom is done in comp_showcase.py)
bpy.data.objects["Rim"].visible_glossy = False
scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = 0.3
scene.render.image_settings.color_mode = "RGBA"
scene.render.use_persistent_data = True
if arg("--still", ""):
    f = int(arg("--still", "1")); scene.frame_set(f)
    scene.render.filepath = os.path.join(ROOT, OUTDIR, f"still_{f:04d}.png"); bpy.ops.render.render(write_still=True)
else:
    scene.render.filepath = os.path.join(ROOT, OUTDIR, "f"); bpy.ops.render.render(animation=True)
print("WROTE SHOT", OUTDIR)

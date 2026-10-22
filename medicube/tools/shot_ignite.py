"""Ad shot 'Ignition' v2 (~5 s, 120 f @24): a glint sweeps the chrome in the dark, the head ignites with a flash,
shockwave and a burst of sparks, the camera whips round the device while comets of light coil up (the official X2
film's light-painting motif), then the LED cycles through all seven mode colours on the beat and settles.
(v1, the calmer 4 s cut, is kept in tools/shot_ignite_v1.py.)

  /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/shot_ignite.py -- \
      --out render/shots/ignite/ --res 960x540 --samples 24
"""
import bpy, math, os, random, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d
FR = int(arg("--frames", "120")); OUTDIR = arg("--out", "render/shots/ignite/")
ORDER = ["booster", "mc", "derma", "air", "dual", "mask", "ai"]

sys.argv = [sys.argv[0], "--", "--bg", "dark", "--led", "booster", "--color", arg("--color", "pink"),
            "--res", arg("--res", "960x540"), "--samples", arg("--samples", "24"), "--no_render", "1"]
_mine = (FR, OUTDIR, argv)
exec(compile(open(os.path.join(HERE, "render_device.py")).read(), "render_device.py", "exec"))
FR, OUTDIR, argv = _mine
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d

random.seed(7)
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, FR
scene.render.fps = 24
def F(t): return max(1, round(t * FR))          # timeline in 0..1
def interp(owner_fcurves, kind="BEZIER", easing="AUTO"):
    for fc in owner_fcurves:
        for kp in fc.keyframe_points: kp.interpolation = kind; kp.easing = easing
def fcurves(idblock):
    ad = idblock.animation_data
    return ad.action.fcurves if ad and ad.action else []

T_IGN = 0.11                                  # ignition
T_CYC0, T_CYC1 = 0.50, 0.84                    # colour cycle window
cyc_frames = [F(T_CYC0 + (T_CYC1 - T_CYC0) * i / 6) for i in range(7)]   # mc .. ai, then back to booster
mode_at = [("booster", 1)] + [(ORDER[i + 1], cyc_frames[i]) for i in range(6)] + [("booster", cyc_frames[6])]

# ---------------------------------------------------------------- emissive sockets: ignition ramp + colour per beat
def key_colour(sock, tint=0.0):
    for mname, fr in mode_at:
        c = LED_RGB[mname]
        sock.default_value = (*[tint + (1 - tint) * x for x in c], 1); sock.keyframe_insert("default_value", frame=fr)

on0, on1 = F(T_IGN), F(T_IGN) + 3
for mname in ("Ring", "Lens", "Screen"):
    nt = bpy.data.materials[mname].node_tree
    for nd in nt.nodes:
        socks = []
        if nd.type == "BSDF_PRINCIPLED" and not nd.inputs["Emission Strength"].is_linked and nd.inputs["Emission Strength"].default_value > 0:
            socks.append(nd.inputs["Emission Strength"])
        if nd.type == "MATH" and nd.operation == "MULTIPLY_ADD":
            socks += [nd.inputs[1], nd.inputs[2]]
        for sk in socks:
            full = sk.default_value
            sk.default_value = 0; sk.keyframe_insert("default_value", frame=on0)
            sk.default_value = full * 3.0; sk.keyframe_insert("default_value", frame=on1)     # flash
            sk.default_value = full; sk.keyframe_insert("default_value", frame=on1 + 10)
            for fr in cyc_frames:                                                              # a kick on every beat
                sk.default_value = full * 1.9; sk.keyframe_insert("default_value", frame=fr)
                sk.default_value = full; sk.keyframe_insert("default_value", frame=fr + 4)
        if nd.type == "BSDF_PRINCIPLED" and mname != "Screen":
            key_colour(nd.inputs["Emission Color"])
    interp(fcurves(nt))

# colour keys snap (CONSTANT); strength keys ease
for mname in ("Ring", "Lens"):
    for fc in fcurves(bpy.data.materials[mname].node_tree):
        vals = {round(kp.co[0]) for kp in fc.keyframe_points}
        if fc.array_index in (0, 1, 2, 3) and vals == {fr for _, fr in mode_at}:
            for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"

# screen text follows the mode: one image per mode, picked by a stepped index
snt = bpy.data.materials["Screen"].node_tree
ui = next(nd for nd in snt.nodes if nd.type == "TEX_IMAGE" and nd.image and nd.image.name.startswith("screen_"))
idx = snt.nodes.new("ShaderNodeValue")
acc = None
for i, mname in enumerate(ORDER):
    im = snt.nodes.new("ShaderNodeTexImage"); im.image = img(f"screen_{mname}.png")
    cmp = snt.nodes.new("ShaderNodeMath"); cmp.operation = "COMPARE"; cmp.inputs[1].default_value = i; cmp.inputs[2].default_value = 0.5
    snt.links.new(idx.outputs[0], cmp.inputs[0])
    if acc is None:
        acc = im.outputs["Color"]; continue
    mx = snt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
    snt.links.new(cmp.outputs[0], mx.inputs["Factor"]); snt.links.new(acc, mx.inputs["A"]); snt.links.new(im.outputs["Color"], mx.inputs["B"])
    acc = mx.outputs["Result"]
psc = next(nd for nd in snt.nodes if nd.type == "BSDF_PRINCIPLED")
snt.links.new(acc, psc.inputs["Emission Color"])
for mname, fr in mode_at:
    idx.outputs[0].default_value = ORDER.index(mname); idx.outputs[0].keyframe_insert("default_value", frame=fr)
for fc in fcurves(snt):
    if "nodes[\"Value\"]" in fc.data_path:
        for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"

# ---------------------------------------------------------------- helpers for light objects
def glow_mat(name, strength, tint=0.15, cycle=True):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = strength * EXPK
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], out.inputs[0])
    if cycle:
        key_colour(em.inputs["Color"], tint)
        for fc in fcurves(nt):
            if "Color" in fc.data_path or fc.data_path.endswith("inputs[0].default_value"):
                for kp in fc.keyframe_points: kp.interpolation = "CONSTANT"
    else:
        em.inputs["Color"].default_value = (1, 0.93, 0.86, 1)
    return m, em.inputs["Strength"]

def curve_obj(name, pts, depth, mat, parent=None):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth; cu.bevel_resolution = 2
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    ob = bpy.data.objects.new(name, cu); scene.collection.objects.link(ob); ob.parent = parent or device
    ob.data.materials.append(mat); ob.visible_shadow = False; ob.visible_diffuse = False
    return ob, cu

# ---------------------------------------------------------------- opening glint across the chrome
glint = card("Glint", (-0.35, -0.12, 0.2), (0.012, 0.5), 60.0, (1.0, 0.95, 0.9))
for fr, x in ((1, -0.30), (F(0.10), 0.30)):
    glint.location.x = x; glint.keyframe_insert("location", index=0, frame=fr)
interp(fcurves(glint), "SINE", "EASE_IN_OUT")
gm = glint.data.materials[0].node_tree.nodes["Emission"].inputs["Strength"]
for fr, v in ((F(0.10), 60.0), (F(0.10) + 2, 0.0)):
    gm.default_value = v; gm.keyframe_insert("default_value", frame=fr)

# ---------------------------------------------------------------- comets: ten orbits, hot cores and coloured trails
col_m, _ = glow_mat("Comet", 3.2, 0.12)
hot_m, _ = glow_mat("CometHot", 5.0, 0.55)
zc = Z_LENS - 0.006
for k in range(10):
    ph = random.uniform(0, 2 * math.pi); tilt = math.radians(random.uniform(-24, 24))
    r0 = random.uniform(0.022, 0.050); rise = random.uniform(0.0, 0.03); turns = random.uniform(1.1, 1.8)
    pts = []
    for i in range(300):
        t = i / 299; a = ph + t * turns * 2 * math.pi; r = r0 * (1 + 0.35 * t)
        x, y = r * math.cos(a), r * math.sin(a)
        pts.append((x, y * math.cos(tilt), zc + y * math.sin(tilt) + rise * t))
    hot = k % 3 == 0
    ob, cu = curve_obj(f"Comet{k}", pts, 0.00018 if hot else random.choice((0.00008, 0.00012)), hot_m if hot else col_m)
    s0 = F(T_IGN) + 1 + k * 2 + (F(0.42) if k >= 6 else 0)   # two waves: the ignition and the colour cycle
    dur = random.randint(int(FR * 0.20), int(FR * 0.30))
    for fr, a0, b0 in ((1, 0, 0), (s0, 0, 0), (s0 + dur // 2, 0.08, 0.6), (s0 + dur, 0.75, 1.0), (s0 + dur + 5, 1.0, 1.0)):
        cu.bevel_factor_start = a0; cu.bevel_factor_end = b0
        cu.keyframe_insert("bevel_factor_start", frame=fr); cu.keyframe_insert("bevel_factor_end", frame=fr)
    interp(fcurves(cu), "QUAD", "EASE_OUT")

# ---------------------------------------------------------------- shockwave at ignition + a pulse ring on every beat
ring_pts = [(math.cos(2 * math.pi * i / 180), math.sin(2 * math.pi * i / 180), 0) for i in range(181)]
def pulse(name, f0, dur, s_end, z_end, strength, depth=0.008, hot=False):
    m, st = glow_mat(name, strength, 0.5 if hot else 0.1)
    ob, cu = curve_obj(name, ring_pts, depth, m)
    for fr, sc, z, e in ((f0 - 1, 0.0175, Z_LENS, 0), (f0, 0.0175, Z_LENS, strength * EXPK), (f0 + dur, s_end, z_end, 0)):
        ob.scale = (sc, sc, sc); ob.location.z = z
        ob.keyframe_insert("scale", frame=fr); ob.keyframe_insert("location", index=2, frame=fr)
        st.default_value = e; st.keyframe_insert("default_value", frame=fr)
    interp(fcurves(ob), "EXPO", "EASE_OUT")
pulse("Shock", F(T_IGN) + 1, 10, 0.065, Z_LENS + 0.004, 6.0, 0.010, hot=True)
pulse("Shock2", F(T_IGN) + 4, 14, 0.07, Z_LENS + 0.012, 3.0)
for i, fr in enumerate(cyc_frames):
    pulse(f"Beat{i}", fr, 12, 0.05, Z_LENS + 0.014, 3.0)

# ---------------------------------------------------------------- sparks: bursts from the lens (motion blur turns them into streaks)
spark_me = bpy.data.meshes.new("Spark")
import bmesh as _bm
b = _bm.new(); _bm.ops.create_icosphere(b, subdivisions=1, radius=0.00035); b.to_mesh(spark_me); b.free()
spark_m, _ = glow_mat("Spark", 8.0, 0.6)
spark_me.materials.append(spark_m)
def burst(f0, n, speed):
    for i in range(n):
        ob = bpy.data.objects.new("Spark", spark_me); scene.collection.objects.link(ob); ob.parent = device
        ob.visible_shadow = False; ob.visible_diffuse = False
        a = random.uniform(0, 2 * math.pi); rr = random.uniform(0, 0.011)
        p0 = Vector((rr * math.cos(a), rr * math.sin(a), Z_LENS + 0.002))
        d = Vector((math.cos(a) * random.uniform(0.4, 1.0), math.sin(a) * random.uniform(0.4, 1.0), random.uniform(0.3, 1.2))).normalized()
        p1 = p0 + d * speed * random.uniform(0.5, 1.0)
        fs = f0 + random.randint(0, 3); fe = fs + random.randint(8, 16)
        for fr, loc, sc in ((fs - 1, p0, 0), (fs, p0, 1), (fe, p1, 0)):
            ob.location = loc; ob.scale = (sc,) * 3
            ob.keyframe_insert("location", frame=fr); ob.keyframe_insert("scale", frame=fr)
        interp(fcurves(ob), "EXPO", "EASE_OUT")
burst(F(T_IGN) + 1, 70, 0.07)
burst(cyc_frames[-1] - 2, 40, 0.045)

# ---------------------------------------------------------------- camera: low front -> fast orbit rising -> top-down hero
cam = scene.camera; cam.data.lens = 45
for c in list(cam.constraints): cam.constraints.remove(c)
pivot = bpy.data.objects.new("Pivot", None); scene.collection.objects.link(pivot)
tgt = bpy.data.objects.new("Target", None); scene.collection.objects.link(tgt)
cam.parent = pivot
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
keys = [  # t, pivot yaw, cam local (y, z), target z
    (0.00, -25, (-0.20, 0.120), Z_LENS - 0.010),
    (0.12, -18, (-0.17, 0.130), Z_LENS - 0.004),
    (0.45, 140, (-0.15, 0.200), Z_LENS + 0.004),
    (0.80, 300, (-0.15, 0.235), Z_LENS + 0.006),
    (1.00, 335, (-0.13, 0.280), Z_LENS + 0.010),
]
for t, yaw, (y, z), tz in keys:
    fr = F(t); pivot.rotation_euler[2] = math.radians(yaw); pivot.keyframe_insert("rotation_euler", index=2, frame=fr)
    cam.location = (0, y, z); cam.keyframe_insert("location", frame=fr)
    tgt.location = (0, 0, tz); tgt.keyframe_insert("location", frame=fr)
for ob in (pivot, cam, tgt): interp(fcurves(ob), "BEZIER", "AUTO")
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 4.0; cam.data.dof.focus_object = tgt

# ---------------------------------------------------------------- motion blur + bloom
scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = 0.6
scene.use_nodes = True; ct = scene.node_tree; ct.nodes.clear()
rl = ct.nodes.new("CompositorNodeRLayers"); gl = ct.nodes.new("CompositorNodeGlare"); co = ct.nodes.new("CompositorNodeComposite")
gl.glare_type = "BLOOM"
for k, v in (("Threshold", float(arg("--thr", "1.0"))), ("Strength", 0.5), ("Size", 0.55)):
    try: gl.inputs[k].default_value = v
    except Exception as e: print("glare", k, e)
ct.links.new(rl.outputs["Image"], gl.inputs["Image"]); ct.links.new(gl.outputs["Image"], co.inputs["Image"])

# the rim light's specular on the emblem blooms into a white blob once the camera is overhead
bpy.data.objects["Rim"].visible_glossy = False
for nm in arg("--noglossy", "").split(","):     # debug: hide a light from reflections
    if nm in bpy.data.objects: bpy.data.objects[nm].visible_glossy = False
if arg("--nobloom", "0") == "1": ct.links.new(rl.outputs["Image"], co.inputs["Image"])
scene.render.use_persistent_data = True
scene.render.filepath = os.path.join(ROOT, OUTDIR, "f")
if arg("--still", ""):
    scene.frame_set(int(arg("--still", "1"))); scene.render.filepath = os.path.join(ROOT, OUTDIR, f"still_{arg('--still', '1')}.png")
    bpy.ops.render.render(write_still=True)
else:
    bpy.ops.render.render(animation=True)
print("WROTE SHOT", OUTDIR)

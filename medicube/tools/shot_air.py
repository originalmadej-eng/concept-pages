"""AIR SHOT beat (user 2026-10-15): the device stands, tips over backwards as if falling, and is caught lying on a bed
of soft clouds; the camera rises to look down on it while it floats and bobs. Official AIR SHOT copy is
"Pore Refining Care" — the cloud is a mood (lightness), nothing is claimed. Mode colour: sky blue.
Clouds are metaballs (one smooth puffy surface, cheap); the sky is added in comp_air.py (transparent film).

  /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/shot_air.py -- --out render/air/ [--still 1,30,80]
"""
import bpy, math, os, sys, random
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d
OUTDIR = arg("--out", "render/air/"); FR = int(arg("--frames", "120"))

sys.argv = [sys.argv[0], "--", "--bg", "white", "--led", "air", "--color", "pink", "--transparent", "1",
            "--res", arg("--res", "960x540"), "--samples", arg("--samples", "32"), "--no_render", "1"]
_mine = (OUTDIR, FR, argv)
exec(compile(open(os.path.join(HERE, "render_device.py")).read(), "render_device.py", "exec"))
OUTDIR, FR, argv = _mine
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d

scene = bpy.context.scene; scene.frame_start, scene.frame_end = 1, FR; scene.render.fps = 24
def fcurves(idb):
    ad = idb.animation_data
    return ad.action.fcurves if ad and ad.action else []
def sstep(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
for ob in bpy.data.objects:                         # reflection flags must not darken the clouds
    if ob.name.startswith(("Flag", "Ceiling")): ob.visible_diffuse = False
# sky light: a pale blue world so cloud shadows go cool, not grey (the camera still sees transparent)
wb.inputs["Color"].default_value = (0.62, 0.78, 1.0, 1); wb.inputs["Strength"].default_value = 0.8

# ---------------------------------------------------------------- timing
F_TIP, F_LAND = 14, 36          # starts to tip back / lands in the cloud
YAW = math.radians(float(arg("--yaw", "0")))       # straight back (user 2026-10-15)
SPIN = math.radians(float(arg("--spin", "0")))     # display ends facing up, towards the following camera
SINK = 0.006                                        # touches down just inside the cloud, then sinks in (see DEEP)
DEEP = float(arg("--sink", "0.016"))                # rests this far in; the rest of the landing is the jelly squash (v8)
from mathutils import Matrix
def rot(th, ps): return Matrix.Rotation(ps, 3, "Z") @ Matrix.Rotation(th, 3, "X")

# ---------------------------------------------------------------- clouds (metaballs): one fluffy cumulus mattress + far banks
cm = bpy.data.materials.new("Cloud"); cm.use_nodes = True; cn = cm.node_tree; cp = cn.nodes["Principled BSDF"]
cp.inputs["Base Color"].default_value = (0.96, 0.97, 1.0, 1); cp.inputs["Roughness"].default_value = 0.9
cp.inputs["Subsurface Weight"].default_value = 0.35; cp.inputs["Subsurface Radius"].default_value = (0.02, 0.024, 0.032)
cp.inputs["Sheen Weight"].default_value = 0.6; cp.inputs["Sheen Tint"].default_value = (1, 1, 1, 1)
cp.inputs["Emission Color"].default_value = (0.93, 0.96, 1.0, 1)
cp.inputs["Emission Strength"].default_value = float(arg("--cloud_glow", "0.10")) * EXPK      # clouds stay white, shade cool
rnd = random.Random(int(arg("--seed", "4")))
def cloud(name, centre, rx, ry, n, rmin, rmax, height, res=0.005, yaw=0.0):
    """cumulus: a flat-ish base of merged balls, bigger puffs heaped in the middle"""
    mb = bpy.data.metaballs.new(name); mb.resolution = res; mb.render_resolution = res * 0.6; mb.threshold = 0.6
    ob = bpy.data.objects.new(name, mb); scene.collection.objects.link(ob); ob.location = centre; ob.rotation_euler = (0, 0, yaw)
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi); q = math.sqrt(rnd.random())
        x, y = rx * q * math.cos(a), ry * q * math.sin(a)
        r = rnd.uniform(rmin, rmax) * (1.15 - 0.55 * q)
        el = mb.elements.new(); el.co = (x, y, height * (1 - q * q) * rnd.uniform(0.6, 1.0)); el.radius = r; el.stiffness = 2.2
    mb.materials.append(cm)
    return ob

CLOUDS = bpy.data.collections.new("Clouds"); scene.collection.children.link(CLOUDS)
vm = bpy.data.materials.new("CloudVol"); vm.use_nodes = True; vn = vm.node_tree
for nd in list(vn.nodes):
    if nd.type != "OUTPUT_MATERIAL": vn.nodes.remove(nd)
pv = vn.nodes.new("ShaderNodeVolumePrincipled")
pv.inputs["Color"].default_value = (1, 1, 1, 1); pv.inputs["Anisotropy"].default_value = 0.35
pv.inputs["Absorption Color"].default_value = (1, 1, 1, 1)      # default black absorbs: clouds went grey
at = vn.nodes.new("ShaderNodeAttribute"); at.attribute_name = "density"
nz = vn.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 140; nz.inputs["Detail"].default_value = 8
nz.inputs["Roughness"].default_value = 0.6
mr = vn.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = float(arg("--nmin", "0.25")); mr.inputs["From Max"].default_value = float(arg("--nmax", "0.55"))
mr.inputs["To Min"].default_value = float(arg("--nfloor", "0.85"))       # never fully empty inside: a body, wisps only at the edge
mul = vn.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
mul2 = vn.nodes.new("ShaderNodeMath"); mul2.operation = "MULTIPLY"; mul2.inputs[1].default_value = float(arg("--density", "3000"))
vn.links.new(nz.outputs["Fac"], mr.inputs["Value"]); vn.links.new(at.outputs["Fac"], mul.inputs[0]); vn.links.new(mr.outputs["Result"], mul.inputs[1])
vn.links.new(mul.outputs[0], mul2.inputs[0]); vn.links.new(mul2.outputs[0], pv.inputs["Density"])
vn.links.new(pv.outputs[0], vn.nodes["Material Output"].inputs["Volume"])
def to_volume(mbo, voxel, disp, noise, fine=0.0, fine_noise=0.0, micro=0.0, micro_noise=0.0):
    """metaball cumulus -> a real volume with billowing edges; returns the volume object (animate that one)"""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(mbo.evaluated_get(dg))
    vo = bpy.data.objects.new(mbo.name + "Vol", bpy.data.volumes.new(mbo.name)); CLOUDS.objects.link(vo)
    vo.matrix_world = mbo.matrix_world.copy()
    src = bpy.data.objects.new(mbo.name + "Src", me); scene.collection.objects.link(src)
    src.parent = vo; src.hide_render = True; src.hide_viewport = True
    m2v = vo.modifiers.new("M2V", "MESH_TO_VOLUME"); m2v.object = src; m2v.resolution_mode = "VOXEL_SIZE"
    m2v.voxel_size = voxel; m2v.density = 1.0
    tx = bpy.data.textures.new(mbo.name, "CLOUDS"); tx.noise_scale = noise; tx.noise_depth = 4; tx.noise_basis = "BLENDER_ORIGINAL"
    vd = vo.modifiers.new("Disp", "VOLUME_DISPLACE"); vd.texture = tx; vd.strength = disp; vd.texture_mid_level = (0.5, 0.5, 0.5)
    if fine:                                                   # second, small octave: cauliflower detail on the billows
        t2 = bpy.data.textures.new(mbo.name + "F", "CLOUDS"); t2.noise_scale = fine_noise; t2.noise_depth = 3
        v2 = vo.modifiers.new("DispF", "VOLUME_DISPLACE"); v2.texture = t2; v2.strength = fine; v2.texture_mid_level = (0.5, 0.5, 0.5)
    if micro:                                                  # third octave: the small curls that read as cloud texture
        t3 = bpy.data.textures.new(mbo.name + "M", "CLOUDS"); t3.noise_scale = micro_noise; t3.noise_depth = 2
        v3 = vo.modifiers.new("DispM", "VOLUME_DISPLACE"); v3.texture = t3; v3.strength = micro; v3.texture_mid_level = (0.5, 0.5, 0.5)
    vo.data.materials.append(vm)
    bpy.data.objects.remove(mbo)
    return vo

D_LIE = rot(math.radians(-90), YAW) @ Vector((0, 0, 1))        # the device's long axis when lying
C_LIE_XY = Vector((0, 0, 0)) + 0.083 * Vector((D_LIE.x, D_LIE.y, 0))
bed = cloud("CloudBed", (C_LIE_XY.x, C_LIE_XY.y, 0.0), 0.20, 0.12, 110, 0.030, 0.052, 0.030, yaw=YAW + math.pi / 2)
CUT = float(arg("--cut", "0.055"))            # local +y is screen-left: no cloud behind the title's "OT" (user v8)
for el in [e for e in bed.data.elements if e.co.y > CUT]: bed.data.elements.remove(el)
for gx in [i * 0.032 for i in range(-5, 6)]:                # solid core: no holes through the bed (v6, the right "arm")
    for gy in [j * 0.032 for j in range(-3, 4)]:
        if (gx / 0.17) ** 2 + (gy / 0.10) ** 2 < 1 and gy <= CUT:
            el = bed.data.elements.new(); el.co = (gx, gy, 0.008); el.radius = 0.046; el.stiffness = 2.2
bpy.context.view_layer.update()
bme = bed.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
mw = bed.matrix_world
top = max((mw @ v.co).z for v in bme.vertices if ((mw @ v.co).xy - C_LIE_XY.xy).length < 0.06)
bed.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
BED_Z = -R + 0.001 - top                                       # bed top = underside of the device when it lies flat on its base line (v10)
REST_Z = 0.0                                                  # lying centre on the pivot path (base on the origin)
print("CLOUD TOP", round(top, 4))
bed = to_volume(bed, float(arg("--voxel", "0.0015")), 0.030, 0.055, 0.013, 0.015, 0.005, 0.006)
def JELLY(t):                                                   # squash amount of the bed after contact (0 before)
    return 0.0 if t < 0 else float(arg("--jelly", "0.08")) * sstep(t / 6) * (1 - sstep((t - 6) / 18))   # out and back once, no wobble (v9)
Z_FINAL = REST_Z - DEEP
wrap_mb = bpy.data.metaballs.new("Wrap"); wrap_mb.resolution = 0.004; wrap_mb.render_resolution = 0.0025; wrap_mb.threshold = 0.6
wrap = bpy.data.objects.new("Wrap", wrap_mb); scene.collection.objects.link(wrap)
wrap.location = (C_LIE_XY.x, C_LIE_XY.y, Z_FINAL); wrap.rotation_euler = (0, 0, YAW)
for side in (-1, 1):
    for i in range(9):
        y = -0.075 + 0.15 * i / 8 + rnd.uniform(-0.006, 0.006)
        el = wrap_mb.elements.new(); el.co = (side * (R + rnd.uniform(0.004, 0.010)), y, rnd.uniform(-0.004, 0.004))
        el.radius = rnd.uniform(0.016, 0.024); el.stiffness = 2.2
wrap = to_volume(wrap, 0.0016, 0.010, 0.02, 0.006, 0.012)
wrap.hide_render = True                                      # v8: no cloud rising at the sides (user: 옆에 차오르는 구름 없애기)
for f in range(1, FR + 1):                                    # swells up around the device as it sinks in
    g = sstep((f - F_LAND) / 20); bobw = 0.0   # swells while the device sinks, same breath as the device
    wrap.scale = [max(0.001, 0.2 + 0.65 * g)] * 3; wrap.location.z = REST_Z - DEEP - 0.012 * (1 - g) + bobw   # rises around it as it sinks
    wrap.keyframe_insert("scale", frame=f); wrap.keyframe_insert("location", index=2, frame=f)
for f in range(1, FR + 1):                                      # rises to catch the device, squashes, breathes
    rise = -0.30 * (1 - sstep((f - (F_TIP - 4)) / (F_LAND - F_TIP + 2)))
    t = f - F_LAND
    sq = JELLY(t)                                                # pudding-like: pushed out sideways, springs back (v8)
    bob = 0.0
    bed.location.z = BED_Z + rise + bob; bed.scale = (1 + sq * 0.55, 1 + sq * 0.55, 1 - sq)
    bed.keyframe_insert("location", index=2, frame=f); bed.keyframe_insert("scale", frame=f)
far_m = cm.copy(); far_m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.45 * EXPK   # far: lit by the sky
for i, (x, y, z, s) in enumerate(((-0.55, 0.85, -0.19, 1.1), (0.50, 1.05, -0.17, 1.3), (0.0, 1.6, -0.15, 1.8),
                                   (-0.95, 1.4, -0.17, 1.5), (0.95, 1.5, -0.19, 1.4))):
    c = cloud(f"Far{i}", (x, y, z - 0.18), 0.22 * s, 0.10 * s, 40, 0.035 * s, 0.06 * s, 0.05 * s, res=0.008)
    c = to_volume(c, 0.006, 0.03, 0.09)
    for f in range(1, FR + 1):
        up = sstep((f - (F_TIP + i)) / 22)                       # hidden below until the fall starts, then rise
        c.location = (x + (0.03 if i % 2 else -0.025) * f / FR, y, z - 0.18 - 0.35 * (1 - up))
        c.scale = [max(0.001, sstep((f - F_TIP + 2) / 6))] * 3
        c.keyframe_insert("location", frame=f); c.keyframe_insert("scale", frame=f)

sun_d = bpy.data.lights.new("CloudSun", "SUN"); sun_d.energy = float(arg("--sun", "30")) * EXPK   # dense volumes only scatter at the skin: needs a strong sun
sun_d.angle = math.radians(12)   # softer shadow of the device on the cloud
sun_d.color = (1.0, 0.97, 0.92)
sun = bpy.data.objects.new("CloudSun", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = Vector((0.85, 0.3, -0.42)).normalized().to_track_quat("-Z", "Y").to_euler()   # low from the left: billows shade (v5 lower: more relief)
if arg("--sunlink", "1") == "1": sun.light_linking.receiver_collection = CLOUDS
fill_d = bpy.data.lights.new("CloudFill", "SUN"); fill_d.energy = float(arg("--fill", "9")) * EXPK; fill_d.angle = math.radians(40)
fill_d.color = (0.70, 0.82, 1.0)
fill = bpy.data.objects.new("CloudFill", fill_d); scene.collection.objects.link(fill)
fill.rotation_euler = Vector((-0.7, 0.1, -0.7)).normalized().to_track_quat("-Z", "Y").to_euler()
fill.light_linking.receiver_collection = CLOUDS
scene.cycles.volume_bounces = int(arg("--vbounce", "3")); scene.cycles.volume_step_rate = 1.0

# ---------------------------------------------------------------- the device: stands, tips back from its base, lands lying
flt = bpy.data.objects.new("Float", None); scene.collection.objects.link(flt)
device.parent = flt; device.location = (0, 0, -0.083)
import itertools
_vel = [(i / 200) ** 0.7 * (1 - sstep((i / 200 - 0.72) / 0.28)) for i in range(201)]   # speeds up, then the cloud takes it
_cum = list(itertools.accumulate(_vel)); _cum = [c / _cum[-1] for c in _cum]
def FALL(f):                                     # 0 at F_TIP .. 1 (flat) at F_LAND
    s_ = min(1.0, max(0.0, (f - F_TIP) / (F_LAND - F_TIP))) * 200; i_ = min(199, int(s_))
    return _cum[i_] + (_cum[i_ + 1] - _cum[i_]) * (s_ - i_)     # interpolate: rounding the index made the turn stutter
CENTRES = {}
F_END = F_LAND + 22                                 # after this it just breathes with the cloud
for f in range(1, FR + 1):
    if f < F_TIP:                                   # a small lean forward first (anticipation)
        th = math.radians(3) * sstep((f - 4) / (F_TIP - 4)); u = 0.0; k = 0.0
    else:                                           # falls (accelerating), then eases into the cloud: no dead stop (v9)
        u = FALL(f); k = 0.0                                     # pivot only: the body meets the cloud all at once (v10)
        th = math.radians(3) - math.radians(93) * u
    ps = YAW * sstep(u * 1.15); sp = SPIN * sstep(u * 1.1)
    M = rot(th, ps)
    centre = M @ Vector((0, 0, 0.083))                             # pivot on the base
    lie = Vector((C_LIE_XY.x, C_LIE_XY.y, REST_Z))
    if f >= F_TIP: centre = centre * (1 - k) + lie * k
    t = f - F_LAND
    centre.z -= DEEP * sstep((t + 1) / 10) + top * JELLY(t)        # flat on the cloud: sinks in and rides the one soft push
    roll = 0.0                                       # no rocking (v9: the user wants it still once it has landed)
    flt.location = centre; CENTRES[f] = centre.copy(); flt.rotation_mode = "QUATERNION"
    flt.rotation_quaternion = (Matrix.Rotation(roll, 3, D_LIE) @ M).to_quaternion()
    device.rotation_euler = (0, 0, sp)
    flt.keyframe_insert("location", frame=f); flt.keyframe_insert("rotation_quaternion", frame=f)
    device.keyframe_insert("rotation_euler", frame=f)

# ---------------------------------------------------------------- camera: follows the fall, rising over the device
# (user 2026-10-15: falls back, the camera follows, ends on the device lying on the cloud with "AIR SHOT" beside it)
cam = scene.camera
for c_ in list(cam.constraints): cam.constraints.remove(c_)
tgt = bpy.data.objects.new("Target", None); scene.collection.objects.link(tgt)
c_ = cam.constraints.new("TRACK_TO"); c_.target = tgt; c_.track_axis = "TRACK_NEGATIVE_Z"; c_.up_axis = "UP_Y"
EL0, EL1 = math.radians(7.6), math.radians(float(arg("--elev", "52")))       # ends above it looking down: the lying device reads upright in frame (user 2026-10-15: that is right)
D0, D1 = 0.807, float(arg("--dist", "0.56"))
AZ1 = math.radians(float(arg("--azim", "-10")))
SHIFT = Vector((float(arg("--shift", "-0.075")), 0, 0))   # device and cloud right of centre, text left
for f in range(1, FR + 1):
    p = sstep((f - F_TIP - 1) / (F_LAND + 10 - F_TIP - 1))
    q = sstep((f - F_TIP) / (F_LAND + 10 - F_TIP))                             # smooth follow: no shake from the landing
    c = CENTRES[1] * (1 - q) + Vector((C_LIE_XY.x, C_LIE_XY.y, -DEEP)) * q
    el = EL0 + (EL1 - EL0) * p; dd = D0 + (D1 - D0) * p; az = AZ1 * p
    off = Vector((dd * math.cos(el) * math.sin(az), -dd * math.cos(el) * math.cos(az), dd * math.sin(el)))
    t = c + SHIFT * p
    cam.location = t + off; tgt.location = t
    cam.data.lens = 60 - 8 * p
    cam.keyframe_insert("location", frame=f); tgt.keyframe_insert("location", frame=f); cam.data.keyframe_insert("lens", frame=f)
# ---------------------------------------------------------------- "AIR SHOT" in cloud (user 2026-10-16: 글씨도 구름느낌)
# the same volume and light as the clouds, held beside the cloud in frame (parented to the camera), condensing in
TXT = arg("--text", "AIR SHOT")
if TXT:
    scene.frame_set(FR); bpy.context.view_layer.update(); CM = cam.matrix_world.copy()
    cu = bpy.data.curves.new("AirText", "FONT"); cu.body = TXT; cu.font = bpy.data.fonts.load("/Library/Fonts/Nunito-Black.ttf")
    cu.size = float(arg("--text_size", "0.036")); cu.extrude = 0.004; cu.bevel_depth = 0.0022; cu.bevel_resolution = 3
    cu.align_x = "LEFT"; cu.align_y = "CENTER"; cu.space_character = 1.15
    tob = bpy.data.objects.new("AirText", cu); scene.collection.objects.link(tob)
    TD = float(arg("--text_d", "0.56")); hw = TD * 18 / cam.data.lens
    tob.matrix_world = CM @ Matrix.Translation((-hw * 0.86, 0.0, -TD))
    tvo = to_volume(tob, float(arg("--text_voxel", "0.0008")), 0.0032, 0.007, 0.0024, 0.0032, 0.0012, 0.0013)   # rendered once: fine detail is affordable (v6 "텍스쳐")
    tvo.parent = cam; tvo.matrix_parent_inverse = CM.inverted()
    tvo.cycles.use_motion_blur = False                          # a moving volume under motion blur cost ~3 min/frame
    tvm = vm.copy(); tvo.data.materials[0] = tvm
    dens = next(nd for nd in tvm.node_tree.nodes if nd.type == "MATH" and nd.operation == "MULTIPLY" and not nd.inputs[1].is_linked)
    full = dens.inputs[1].default_value; T0, T1 = F_LAND + 2, F_LAND + 26
    for f, v in ((1, 0.0), (T0, 0.0), (T1, full)):
        dens.inputs[1].default_value = v; dens.inputs[1].keyframe_insert("default_value", frame=f)
    dm = tvo.modifiers["Disp"]                                    # wisps first, then the letters gather
    for f, v in ((1, 0.012), (T0, 0.012), (T1, 0.0028)):
        dm.strength = v; dm.keyframe_insert("strength", frame=f)
    scene.frame_set(1)

if arg("--pass", "") == "text":        # the cloud title as its own pass: in one render with the clouds it cost ~4 min/frame
    for o in scene.objects:
        if o.type in ("MESH", "META", "VOLUME", "CURVE", "FONT") and not o.name.startswith("AirText"): o.hide_render = True
elif arg("--pass", "") == "scene" and TXT:
    tvo.hide_render = True
cam.data.dof.use_dof = True; cam.data.dof.focus_object = flt; cam.data.dof.aperture_fstop = 16      # keep the cloud texture sharp

scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = 0.4
scene.render.image_settings.color_mode = "RGBA"
scene.render.use_persistent_data = True
if arg("--still", ""):
    for f in [int(x) for x in arg("--still", "1").split(",")]:
        scene.frame_set(f); scene.render.filepath = os.path.join(ROOT, OUTDIR, f"f{f:04d}.png"); bpy.ops.render.render(write_still=True)
else:
    scene.render.filepath = os.path.join(ROOT, OUTDIR, "f"); bpy.ops.render.render(animation=True)
print("WROTE air", OUTDIR)

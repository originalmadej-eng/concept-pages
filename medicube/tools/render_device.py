"""Booster Pro X2 reconstruction, rendered in Blender (Cycles).

Proportions from ref/BoosterProX2_08.jpg (diameter 254 px : length 1308 px), head structure from
ref/BoosterProX2_03.jpg and ref/16_*.jpg. Textures: tools/make_textures.py.

  /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/render_device.py -- \
     --color pink --led none --out render/test.png --res 1200x1600 --samples 256
options: --led none|booster|mc|derma|air|mask|dual|ai  --led_k 1.0  --yaw deg  --tilt deg
         --explode 0..1  --cam hero|head|wide  --frames N --yaw0 --yaw1  --bg blush|dark
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEX = os.path.join(ROOT, "render", "tex")
COLOR = arg("--color", "pink")
LED = arg("--led", "none")
LED_K = float(arg("--led_k", "1.0"))
EXPLODE = float(arg("--explode", "0"))
CAM = arg("--cam", "hero")
BG = arg("--bg", "blush")
OUT = os.path.join(ROOT, arg("--out", "render/test.png"))
SAMPLES = int(arg("--samples", "256"))
RW, RH = map(int, arg("--res", "1200x1600").split("x"))
EXPOSURE = float(arg("--exposure", "-2.6"))
EXPK = 2 ** (-EXPOSURE)      # emissive parts are multiplied by this so the scene exposure doesn't dim them

# mode colours sampled from the official mode images (03: Booster orange, MC green, Derma Shot amber,
# Air Shot cyan; 01: Mask purple). Dual shows warm yellow in 05; AI colour not shown -> soft white.
LED_RGB = {"booster": (1.0, 0.32, 0.12), "mc": (0.35, 1.0, 0.3), "derma": (1.0, 0.62, 0.15),
           "air": (0.25, 0.85, 1.0), "mask": (0.62, 0.3, 1.0), "dual": (1.0, 0.8, 0.25), "ai": (1.0, 0.95, 0.9)}

R = 0.017
PX = 0.034 / 254
Z_BODY = (1820 - 690) * PX          # 0.1513
Z_GASK = Z_BODY + 0.0026
Z_COLL = Z_GASK + 0.0085
Z_LENS = Z_COLL + 0.0030

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def link(ob): scene.collection.objects.link(ob); return ob
def smooth(me):
    for p in me.polygons: p.use_smooth = True

def lathe(name, pts, steps=192):
    bm = bmesh.new()
    vs = [bm.verts.new((max(r, 0), 0, z)) for r, z in pts]
    es = [bm.edges.new((a, b)) for a, b in zip(vs, vs[1:])]
    bmesh.ops.spin(bm, geom=vs + es, axis=(0, 0, 1), cent=(0, 0, 0), steps=steps, angle=2 * math.pi)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); smooth(me)
    return link(bpy.data.objects.new(name, me))

def tube(name, r, z0, z1, a0=-math.pi, a1=math.pi, segs=256):
    """cylinder patch, u along angle (u=0.5 at -Y = camera side), v bottom->top"""
    me = bpy.data.meshes.new(name); vs = []; fs = []
    for i in range(segs + 1):
        a = a0 + (a1 - a0) * i / segs
        vs += [(r * math.sin(a), -r * math.cos(a), z0), (r * math.sin(a), -r * math.cos(a), z1)]
    for i in range(segs):
        fs.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    me.from_pydata(vs, [], fs)
    uv = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        for li in p.loop_indices:
            vi = me.loops[li].vertex_index; seg, top = divmod(vi, 2)
            uv.data[li].uv = (seg / segs, 1.0 if top else 0.0)
    smooth(me)
    return link(bpy.data.objects.new(name, me))

def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]

def img(name, non_color=False):
    im = bpy.data.images.load(os.path.join(TEX, name))
    if non_color: im.colorspace_settings.name = "Non-Color"
    return im

def rt_radius(theta, R0, apex=math.pi / 2, a=0.10):
    return R0 * (1 + a * math.cos(3 * (theta - apex))) / (1 + a)

led_rgb = LED_RGB.get(LED, (0, 0, 0)); led_on = LED in LED_RGB

# ---------------------------------------------------------------- body (satin plastic, printed)
body_pts = [(0, 0)] + [(R - 0.0035 + 0.0035 * math.sin(t / 8 * math.pi / 2), 0.0035 - 0.0035 * math.cos(t / 8 * math.pi / 2)) for t in range(0, 9)] + [(R, 0.004)]
base = lathe("Base", body_pts)
body = tube("Body", R, 0.004, Z_BODY)
m, n, l, p = mat("Body")
t = n.new("ShaderNodeTexImage"); t.image = img(f"body_{COLOR}.png"); t.interpolation = "Cubic"
l.new(t.outputs["Color"], p.inputs["Base Color"])
bt = n.new("ShaderNodeTexImage"); bt.image = img("body_bump.png", True); bt.interpolation = "Cubic"
bb = n.new("ShaderNodeBump"); bb.inputs["Strength"].default_value = 0.8; bb.inputs["Distance"].default_value = 0.0006
l.new(bt.outputs["Color"], bb.inputs["Height"]); l.new(bb.outputs["Normal"], p.inputs["Normal"])
p.inputs["Roughness"].default_value = 0.42
p.inputs["Coat Weight"].default_value = 0.15; p.inputs["Coat Roughness"].default_value = 0.35
p.inputs["Subsurface Weight"].default_value = 0.04
body.data.materials.append(m)
m2, n2, l2, p2 = mat("BodyPlain")
p2.inputs["Base Color"].default_value = {"pink": (0.62, 0.41, 0.40, 1), "white": (0.84, 0.83, 0.81, 1)}[COLOR]
p2.inputs["Roughness"].default_value = 0.42; p2.inputs["Coat Weight"].default_value = 0.15
base.data.materials.append(m2)
# top lip of the body
lip = lathe("BodyLip", [(R, Z_BODY), (R - 0.0004, Z_BODY + 0.0004), (R - 0.0012, Z_BODY + 0.0004)])
lip.data.materials.append(m2)

# ---------------------------------------------------------------- screen panel (black glass + UI)
sa = 0.0134 / R / 2
z_s0, z_s1 = (1820 - 1090) * PX, (1820 - 830) * PX
scr = tube("Screen", R + 0.00018, z_s0, z_s1, -sa, sa, 64)
m, n, l, p = mat("Screen")
ui = n.new("ShaderNodeTexImage"); ui.image = img(f"screen_{LED}.png" if led_on else "screen.png")
al = n.new("ShaderNodeTexImage"); al.image = img("screen_alpha.png", True)
p.inputs["Base Color"].default_value = (0.004, 0.004, 0.005, 1)
p.inputs["Roughness"].default_value = 0.12; p.inputs["Coat Weight"].default_value = 0.0
l.new(ui.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = 1.4 * EXPK
l.new(al.outputs["Color"], p.inputs["Alpha"])
scr.data.materials.append(m)

# ---------------------------------------------------------------- head group (lifts apart with --explode)
# ref/_dev_head.png, ref/16_*.jpg: black light-guide ring (glows in the mode colour) -> polished chrome collar ->
# frosted rounded-triangle cap, slightly domed, carrying a raised chrome emblem (outline + cross bar).
head = link(bpy.data.objects.new("Head", None))
gask = lathe("Gasket", [(R - 0.0006, Z_BODY), (R + 0.00025, Z_BODY + 0.0004), (R + 0.00025, Z_GASK - 0.0004), (R - 0.0006, Z_GASK)])
m, n, l, p = mat("Ring")
p.inputs["Base Color"].default_value = (0.010, 0.010, 0.011, 1); p.inputs["Roughness"].default_value = 0.45
p.inputs["Specular IOR Level"].default_value = 0.2
if led_on:
    p.inputs["Emission Color"].default_value = (*led_rgb, 1); p.inputs["Emission Strength"].default_value = 2 * LED_K * EXPK
gask.data.materials.append(m)

RC = R + 0.0003
coll = tube("Collar", RC, Z_GASK, Z_COLL)
coll_top = lathe("CollarTop", [(RC, Z_COLL), (RC - 0.0005, Z_COLL + 0.0004), (RC - 0.0013, Z_COLL + 0.0004), (0, Z_COLL + 0.0004)])  # closed chrome deck under the cap
m, n, l, p = mat("Chrome")
p.inputs["Base Color"].default_value = (0.93, 0.93, 0.94, 1); p.inputs["Metallic"].default_value = 1.0; p.inputs["Roughness"].default_value = 0.07
coll.data.materials.append(m); coll_top.data.materials.append(m)
chrome_mat = m

# cap: rounded triangle, side wall + dome
RL = RC - 0.0013
CAP_WALL, DOME = 0.0010, 0.0016
def dome_z(rho): return Z_COLL + CAP_WALL + DOME * (1 - rho * rho)
NA, NR = 240, 24
bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
th = [2 * math.pi * i / NA for i in range(NA)]
rings = []
for k in range(NR + 1):
    rho = 1 - k / NR
    rings.append([bm.verts.new((rho * rt_radius(t, RL) * math.cos(t), rho * rt_radius(t, RL) * math.sin(t), dome_z(rho))) for t in th])
ctr = bm.verts.new((0, 0, dome_z(0)))
bot = [bm.verts.new((rt_radius(t, RL) * math.cos(t), rt_radius(t, RL) * math.sin(t), Z_COLL)) for t in th]
for i in range(NA):
    j = (i + 1) % NA
    bm.faces.new((bot[i], bot[j], rings[0][j], rings[0][i]))
    for k in range(NR):
        bm.faces.new((rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]))
    bm.faces.new((rings[NR][i], rings[NR][j], ctr))
# open shell: recalc can't tell inside from outside, so orient explicitly (dome up, wall out)
for fc in bm.faces:
    c = fc.calc_center_median(); no = fc.normal
    out = no.z if abs(no.z) > 0.5 else (no.x * c.x + no.y * c.y)
    if out < 0: fc.normal_flip()
for fc in bm.faces:
    for lp in fc.loops:
        lp[uvl].uv = (lp.vert.co.x / (2 * RL) + 0.5, lp.vert.co.y / (2 * RL) + 0.5)
me = bpy.data.meshes.new("Lens"); bm.to_mesh(me); bm.free(); smooth(me)
lens = link(bpy.data.objects.new("Lens", me))
m, n, l, p = mat("Lens")
p.inputs["Base Color"].default_value = (0.62, 0.61, 0.62, 1); p.inputs["Roughness"].default_value = 0.42
p.inputs["Transmission Weight"].default_value = 0.35; p.inputs["IOR"].default_value = 1.49
ld = n.new("ShaderNodeTexImage"); ld.image = img("emblem_led.png", True)
if led_on:
    p.inputs["Emission Color"].default_value = (*led_rgb, 1)
    em = n.new("ShaderNodeMath"); em.operation = "MULTIPLY_ADD"
    em.inputs[1].default_value = 6 * LED_K * EXPK; em.inputs[2].default_value = 0.45 * LED_K * EXPK
    l.new(ld.outputs["Color"], em.inputs[0]); l.new(em.outputs["Value"], p.inputs["Emission Strength"])
else:
    # unlit LED dots read as slightly darker spots under the frost
    mc = n.new("ShaderNodeMix"); mc.data_type = "RGBA"
    mc.inputs["A"].default_value = (0.62, 0.61, 0.62, 1); mc.inputs["B"].default_value = (0.35, 0.34, 0.35, 1)
    l.new(ld.outputs["Color"], mc.inputs["Factor"]); l.new(mc.outputs["Result"], p.inputs["Base Color"])
lens.data.materials.append(m)

# raised chrome emblem: rounded-triangle band (0.93 -> 0.76 of RL) + cross bar, following the dome
def emblem_obj(name, loops, lift=0.00075, sink=0.0003):
    bm = bmesh.new(); es = []
    for pts in loops:
        vs = [bm.verts.new((x, y, 0)) for x, y in pts]
        es += [bm.edges.new((vs[i], vs[(i + 1) % len(vs)])) for i in range(len(vs))]
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=es, normal=(0, 0, 1))
    top = list(bm.faces)
    ext = bmesh.ops.extrude_face_region(bm, geom=top)
    new_vs = {e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)}
    def rho_at(v):
        t = math.atan2(v.co.y, v.co.x); return min(1.0, math.hypot(v.co.x, v.co.y) / rt_radius(t, RL))
    for v in bm.verts:
        z = dome_z(rho_at(v))
        v.co.z = z + lift if v in new_vs else z - sink
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new(name, me))
    bv = ob.modifiers.new("bev", "BEVEL"); bv.width = 0.00028; bv.segments = 3; bv.limit_method = "ANGLE"
    ob.data.materials.append(chrome_mat)
    for pl in ob.data.polygons: pl.use_smooth = False
    return ob
def rt_loop(scale, n=240):
    return [(rt_radius(t, RL * scale) * math.cos(t), rt_radius(t, RL * scale) * math.sin(t)) for t in (2 * math.pi * i / n for i in range(n))]
band = emblem_obj("EmblemBand", [rt_loop(0.93), rt_loop(0.76)])
BW, BH = RL * 0.74, RL * 0.07
bar_pts = [(-BW + 2 * BW * i / 40, -BH) for i in range(41)] + [(BW - 2 * BW * i / 40, BH) for i in range(41)]
bar = emblem_obj("EmblemBar", [bar_pts])

for ob in (gask, coll, coll_top, lens, band, bar):
    ob.parent = head
# exploded view: parts separate upward
coll.location.z += 0.006 * EXPLODE; coll_top.location.z += 0.006 * EXPLODE
for ob in (lens, band, bar): ob.location.z += 0.016 * EXPLODE
band.location.z += 0.006 * EXPLODE; bar.location.z += 0.006 * EXPLODE
gask.location.z += 0.002 * EXPLODE

device = link(bpy.data.objects.new("Device", None))
for ob in (base, body, lip, scr, head):
    ob.parent = device
device.rotation_euler = (math.radians(float(arg("--tilt", "0"))), 0, math.radians(float(arg("--yaw", "0"))))

# ---------------------------------------------------------------- studio
def card(name, loc, size, strength, color=(1, 1, 1), look=(0, 0, 0.1)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    ob = bpy.context.active_object; ob.name = name; ob.scale = (size[0], size[1], 1)
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("Z", "Y").to_euler()
    m, n, l, p = mat(name)
    e = n.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*color, 1); e.inputs["Strength"].default_value = strength
    l.new(e.outputs["Emission"], n["Material Output"].inputs["Surface"]); ob.data.materials.append(m)
    ob.visible_camera = False
    return ob

def flag(name, loc, size, look=(0, 0, 0.1)):
    """black card seen only in reflections: gives chrome and glass their dark bands"""
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    ob = bpy.context.active_object; ob.name = name; ob.scale = (size[0], size[1], 1)
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("Z", "Y").to_euler()
    m, n, l, p = mat(name); p.inputs["Base Color"].default_value = (0.004, 0.004, 0.004, 1); p.inputs["Roughness"].default_value = 0.9
    ob.data.materials.append(m)
    ob.visible_camera = False; ob.visible_shadow = False
    return ob

def area(name, loc, look, size, energy, color=(1, 1, 1), spread=None):
    ld = bpy.data.lights.new(name, "AREA"); ld.shape = "RECTANGLE"; ld.size, ld.size_y = size
    ld.energy = energy; ld.color = color
    if spread: ld.spread = math.radians(spread)
    ob = link(bpy.data.objects.new(name, ld)); ob.location = loc
    ob.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob

bg_rgb = {"blush": (0.86, 0.74, 0.72), "dark": (0.012, 0.010, 0.011), "white": (0.9, 0.89, 0.88)}[BG]
path = [(-3.0, 0.0)] + [(0.25 + math.sin(i / 40 * math.pi / 2) * 0.4, 0.4 - math.cos(i / 40 * math.pi / 2) * 0.4) for i in range(41)] + [(0.65, 3.0)]
me = bpy.data.meshes.new("Cyc"); nP = len(path)
me.from_pydata([(-3, y, z) for y, z in path] + [(3, y, z) for y, z in path], [], [(i, i + 1, nP + i + 1, nP + i) for i in range(nP - 1)])
smooth(me); cyc = link(bpy.data.objects.new("Cyc", me))
m, n, l, p = mat("Cyc")
dif = n.new("ShaderNodeBsdfDiffuse"); dif.inputs["Color"].default_value = (*bg_rgb, 1)
# the sweep glows a little so the backdrop stays a clean blush at product exposure
cem = n.new("ShaderNodeEmission"); cem.inputs["Color"].default_value = (*bg_rgb, 1)
cem.inputs["Strength"].default_value = float(arg("--bgk", "0.35")) * (EXPK if BG != "dark" else 0)
add = n.new("ShaderNodeAddShader"); l.new(dif.outputs["BSDF"], add.inputs[0]); l.new(cem.outputs["Emission"], add.inputs[1])
l.new(add.outputs["Shader"], n["Material Output"].inputs["Surface"]); cyc.data.materials.append(m)

world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
wb = world.node_tree.nodes["Background"]
if BG == "dark":
    # low key: one soft key from upper left, a cool-neutral rim behind, strips only seen in the chrome
    wb.inputs["Color"].default_value = (0, 0, 0, 1); wb.inputs["Strength"].default_value = 0
    area("Key", (-0.45, -0.45, 0.42), (0, 0, 0.12), (0.4, 0.4), float(arg("--key", "5")), spread=50)
    area("Rim", (0.3, 0.35, 0.3), (0, 0, 0.12), (0.06, 0.5), 10, spread=30)
    card("StripL", (-0.22, -0.12, 0.12), (0.035, 0.45), 2.5)
    card("StripR", (0.24, -0.08, 0.12), (0.025, 0.45), 1.2)
    card("TopCard", (-0.05, 0.12, 0.40), (0.18, 0.10), 0.8)
    card("Glow", (0, 0.45, 0.25), (0.7, 0.35), 0.6, (1.0, 0.86, 0.84))   # faint warm wall for chrome gradients
else:
    wb.inputs["Color"].default_value = (*bg_rgb, 1); wb.inputs["Strength"].default_value = 0.25
    area("Key", (-0.55, -0.6, 0.32), (0, 0, 0.1), (0.6, 0.6), 60)
    area("Fill", (0.6, -0.5, 0.25), (0, 0, 0.1), (0.8, 0.8), 18)
    area("Top", (0, -0.05, 0.6), (0, 0, 0.15), (0.3, 0.3), float(arg("--top", "4")))
    # long soft strips -> clean vertical highlights on the body and chrome
    card("StripL", (-0.22, -0.12, 0.12), (0.035, 0.45), 9)
    card("StripR", (0.24, -0.08, 0.12), (0.025, 0.45), 6)
    card("TopCard", (-0.05, 0.12, 0.40), (0.18, 0.10), 1.5)
    flag("FlagL", (-0.16, -0.25, 0.2), (0.12, 0.5)); flag("FlagR", (0.17, -0.22, 0.2), (0.10, 0.5))
    flag("Ceiling", (0, 0.05, 0.5), (0.7, 0.5), look=(0, 0.05, 0))

# ---------------------------------------------------------------- camera
cd = bpy.data.cameras.new("Cam"); cd.lens = float(arg("--lens", "85")); cd.sensor_width = 36
cam = link(bpy.data.objects.new("Cam", cd)); scene.camera = cam
CAMS = {"hero": ((0, -0.78, 0.19), (0, 0, 0.088)),
        "head": ((0, -0.16, 0.32), (0, 0, 0.150)),
        "wide": ((0.09, -1.05, 0.17), (0.09, 0, 0.088))}
cl, ct = CAMS[CAM]
cam.location = (float(arg("--camx", cl[0])), float(arg("--camy", cl[1])), float(arg("--camz", cl[2])))
look = Vector((float(arg("--lookx", ct[0])), ct[1], float(arg("--lookz", ct[2]))))
cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
if arg("--transparent", "0") == "1":           # device only, for compositing
    bpy.data.objects["Cyc"].hide_render = True; scene.render.film_transparent = True
for nm in arg("--hide", "").split(","):
    if nm in bpy.data.objects: bpy.data.objects[nm].hide_render = True
if CAM == "head" and arg("--dof", "1") == "1":
    cd.dof.use_dof = True; cd.dof.focus_distance = (look - cam.location).length; cd.dof.aperture_fstop = 4.0

# ---------------------------------------------------------------- render
scene.render.engine = "CYCLES"
pr = bpy.context.preferences.addons["cycles"].preferences; pr.compute_device_type = "METAL"; pr.get_devices()
for d in pr.devices: d.use = True
scene.cycles.device = "GPU"; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
scene.cycles.max_bounces = 16; scene.cycles.transmission_bounces = 12
scene.render.resolution_x, scene.render.resolution_y = RW, RH
VIEW = arg("--view", "Khronos PBR Neutral")
scene.view_settings.view_transform = VIEW
if VIEW == "AgX":
    scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = EXPOSURE
scene.render.image_settings.file_format = "PNG"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

FR = int(arg("--frames", "0"))
if arg("--no_render", "0") == "1":
    pass   # scene is built; a shot script (tools/shot_*.py) animates and renders it
elif FR:
    y0, y1 = math.radians(float(arg("--yaw0", "-35"))), math.radians(float(arg("--yaw1", "0")))
    scene.frame_start, scene.frame_end = 1, FR
    for f, y in ((1, y0), (FR, y1)):
        scene.frame_set(f); device.rotation_euler[2] = y; device.keyframe_insert("rotation_euler", index=2)
    for fc in device.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation = "SINE"; kp.easing = "EASE_IN_OUT"
    scene.render.use_persistent_data = True
    scene.render.filepath = OUT
    bpy.ops.render.render(animation=True); print("WROTE SEQ", OUT)
else:
    scene.render.filepath = OUT
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "render", "device_last.blend"))
    bpy.ops.render.render(write_still=True); print("WROTE", OUT)

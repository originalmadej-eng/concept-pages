"""MC beat prototype: the device drops head-first into a jelly pudding, sticks in, and the jelly wobbles
(official MC copy: "Skin Firming Care / 2X BOUNCE BOOSTING" — the bounce is the metaphor, no claim is drawn).
The jelly's wobble is shape keys (squash, lean, dent) keyed per frame as a damped oscillation.
White studio, transparent film with a shadow catcher; composite over the white stage.

  /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/shot_pudding.py -- --out render/pudding/ --res 960x540 --samples 32 [--still 1,22,30]
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d
OUTDIR = arg("--out", "render/pudding/"); MODE = arg("--mode", "mc"); FR = int(arg("--frames", "72"))

sys.argv = [sys.argv[0], "--", "--bg", "white", "--led", MODE, "--color", "pink", "--transparent", "1",
            "--res", arg("--res", "960x540"), "--samples", arg("--samples", "32"), "--no_render", "1"]
_mine = (OUTDIR, MODE, FR, argv)
exec(compile(open(os.path.join(HERE, "render_device.py")).read(), "render_device.py", "exec"))
OUTDIR, MODE, FR, argv = _mine
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d

scene = bpy.context.scene; scene.frame_start, scene.frame_end = 1, FR; scene.render.fps = 24
def fcurves(idb):
    ad = idb.animation_data
    return ad.action.fcurves if ad and ad.action else []

# ---------------------------------------------------------------- the pudding: a lathe with dense rings on top (for the dent)
RB, RT, HT = 0.092, 0.074, 0.085          # big enough to take ~30% of the device
prof = [(0.0, 0.0), (RB, 0.0)]
for i in range(1, 13): t = i / 12; prof.append((RB + (RT - RB) * t, HT * 0.9 * t))
for i in range(1, 7):
    a = i / 6 * math.pi / 2; prof.append((RT - 0.005 + 0.005 * math.cos(a), HT * 0.9 + (HT * 0.1) * math.sin(a)))
for i in range(1, 25): r_ = (RT - 0.005) * (1 - i / 24); prof.append((r_, HT + 0.005 * (1 - (r_ / (RT - 0.005)) ** 2)))   # soft dome
pud = lathe("Pudding", prof, steps=128)
me = pud.data
pud.shape_key_add(name="Basis")
def key(name, fn):
    k = pud.shape_key_add(name=name, from_mix=False); k.slider_min = -1.5; k.slider_max = 1.5
    for i, v in enumerate(me.vertices):
        k.data[i].co = fn(v.co.copy())
    return k
k_sq = key("squash", lambda c: Vector((c.x * (1 + 0.22 * (c.z / HT) ** 1.5), c.y * (1 + 0.22 * (c.z / HT) ** 1.5), c.z * 0.74)))
k_ln = key("lean", lambda c: Vector((c.x + 0.16 * c.z * (c.z / HT), c.y, c.z)))
k_dn = key("dent", lambda c: Vector((c.x, c.y, c.z - 0.022 * math.exp(-((c.x ** 2 + c.y ** 2) / 0.020 ** 2)) * (c.z / HT) ** 4)))
m = bpy.data.materials.new("Jelly"); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
jcol = (1.0, 0.72, 0.78)       # collagen pink (user 2026-10-15), clear and milky
p.inputs["Base Color"].default_value = (*jcol, 1); p.inputs["Transmission Weight"].default_value = 1.0
p.inputs["Roughness"].default_value = 0.07; p.inputs["IOR"].default_value = 1.36
p.inputs["Subsurface Weight"].default_value = 0.12; p.inputs["Subsurface Radius"].default_value = (0.02, 0.016, 0.012)
p.inputs["Coat Weight"].default_value = 0.6; p.inputs["Coat Roughness"].default_value = 0.03
va = nt.nodes.new("ShaderNodeVolumeAbsorption"); va.inputs["Color"].default_value = (*jcol, 1); va.inputs["Density"].default_value = 2.2
nt.links.new(va.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
pud.data.materials.append(m)

# what the jelly shows through itself: a white stage. Only transmission rays see it, so the device's lighting is unchanged
wnt = scene.world.node_tree; bgn = wnt.nodes["Background"]; outw = wnt.nodes["World Output"]
lpn = wnt.nodes.new("ShaderNodeLightPath"); wbg = wnt.nodes.new("ShaderNodeBackground")
wbg.inputs["Color"].default_value = (0.97, 0.95, 0.94, 1); wbg.inputs["Strength"].default_value = 1.0 * EXPK
mixw = wnt.nodes.new("ShaderNodeMixShader")
mxf = wnt.nodes.new("ShaderNodeMath"); mxf.operation = "MAXIMUM"      # reflections see the white stage too
wnt.links.new(lpn.outputs["Is Transmission Ray"], mxf.inputs[0]); wnt.links.new(lpn.outputs["Is Glossy Ray"], mxf.inputs[1])
wnt.links.new(mxf.outputs[0], mixw.inputs["Fac"]); wnt.links.new(bgn.outputs[0], mixw.inputs[1]); wnt.links.new(wbg.outputs[0], mixw.inputs[2])
wnt.links.new(mixw.outputs[0], outw.inputs["Surface"])

# ---------------------------------------------------------------- the device, head down
flt = bpy.data.objects.new("Float", None); scene.collection.objects.link(flt)
device.parent = flt; device.location = (0, 0, -0.083); device.rotation_euler = (0, 0, 0)
TIP = Z_LENS - 0.083 + 0.0026                       # head tip below the pivot when upside down
CONTACT = HT + TIP
DEPTH = 0.05                                       # ~30% of the 0.165 m device ends up inside
REST = CONTACT - DEPTH
flt.rotation_euler = (math.radians(180), 0, math.radians(200))   # head down, display still towards us
k_pl = key("pull", lambda c: Vector((c.x, c.y, c.z + 0.030 * math.exp(-((c.x ** 2 + c.y ** 2) / 0.026 ** 2)) * (c.z / HT) ** 4)))
def smooth_keys(ob):
    for fc in fcurves(ob):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"; kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
def key_jelly(fn):
    for f in range(1, FR + 1):
        for k, v in zip((k_sq, k_ln, k_dn, k_pl), fn(f)):
            k.value = v; k.keyframe_insert("value", frame=f)

if MODE == "mc":
    # ------------------------------------------------------------ MC: falls in, sticks, the jelly bounces
    F_HIT = F_TXT = 22
    fall = [(1, CONTACT + 0.26), (F_HIT, CONTACT), (F_HIT + 4, REST - 0.014), (F_HIT + 11, REST + 0.007),
            (F_HIT + 19, REST - 0.003), (F_HIT + 30, REST + 0.001), (FR, REST)]
    for f, z in fall:
        flt.location = (0, 0, z); flt.keyframe_insert("location", index=2, frame=f)
    for f, ry in ((F_HIT, 4), (F_HIT + 6, -5), (F_HIT + 14, 3), (F_HIT + 24, -1.5), (FR, 0)):
        flt.rotation_euler[1] = math.radians(ry); flt.keyframe_insert("rotation_euler", index=1, frame=f)
    smooth_keys(flt)
    for fc in fcurves(flt):
        if fc.data_path == "location":
            fc.keyframe_points[0].interpolation = "QUAD"; fc.keyframe_points[0].easing = "EASE_IN"      # gravity
    def mc_jelly(f):
        t = f - F_HIT
        sq = 0.0 if t < 0 else 1.25 * math.exp(-t / 17) * math.cos(2 * math.pi * t / 10)
        ln = 0.0 if t < 2 else 0.85 * math.exp(-(t - 2) / 20) * math.sin(2 * math.pi * (t - 2) / 12)
        dn = 0.0 if t < 0 else min(1.0, t / 4) * (1 + 0.15 * math.exp(-t / 8) * math.cos(2 * math.pi * t / 9))
        return sq, ln, dn, 0.0
    key_jelly(mc_jelly)

elif MODE == "derma":
    # ------------------------------------------------------------ DERMA SHOT: starts where MC ends (stuck in the jelly);
    # a ring of fine needles shoots out of the head into the jelly twice, glowing in the mode colour, then the device
    # is pulled out: the jelly clings, lets go, and the dent closes up again (user 2026-10-15). A metaphor only.
    SHOTS = (12, 24); F_PULL = 40; F_TXT = SHOTS[0]
    zk = [(1, REST), (FR, REST + 0.42)]
    for f0 in SHOTS: zk += [(f0 - 1, REST), (f0 + 1, REST + 0.0035), (f0 + 6, REST)]      # each shot kicks the device a little
    zk += [(F_PULL - 6, REST), (F_PULL, REST - 0.006), (F_PULL + 10, REST + 0.36)]         # dip, then yank out of frame
    for f, z in sorted(zk):
        flt.location = (0, 0, z); flt.keyframe_insert("location", index=2, frame=f)
    for f, ry in ((1, 0), (F_PULL, 0), (F_PULL + 10, 7), (FR, 9)):
        flt.rotation_euler[1] = math.radians(ry); flt.keyframe_insert("rotation_euler", index=1, frame=f)
    smooth_keys(flt)
    for fc in fcurves(flt):
        for kp in fc.keyframe_points:
            if round(kp.co[0]) == F_PULL: kp.interpolation = "QUART"; kp.easing = "EASE_IN"     # sticky start, then fast
    def derma_jelly(f):
        sq = ln = 0.0
        for f0 in SHOTS:                                   # a tight shiver on each shot
            t = f - f0
            if t >= 0: sq += 0.22 * math.exp(-t / 5) * math.cos(2 * math.pi * t / 4.5); ln += 0.10 * math.exp(-t / 6) * math.sin(2 * math.pi * t / 5)
        tp_ = f - F_PULL; tr = f - (F_PULL + 5)
        if 0 <= tp_ < 5: pl = sstep(tp_ / 5); sq += -0.7 * sstep(tp_ / 5)                    # clings and stretches up
        elif tr >= 0:
            pl = math.exp(-tr / 6) * math.cos(2 * math.pi * tr / 8)                              # lets go
            sq += -0.7 * math.exp(-tr / 16) * math.cos(2 * math.pi * tr / 10); ln += 0.45 * math.exp(-tr / 18) * math.sin(2 * math.pi * tr / 12)
        else: pl = 0.0
        dn = 1.0 if tr < 0 else math.exp(-tr / 9) * math.cos(2 * math.pi * tr / 16)           # the hole closes, with a little overshoot
        return sq, ln, dn, pl
    def sstep(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
    key_jelly(derma_jelly)

    # needles: a spiral ring on the head, splayed outwards, fully hidden inside the cap when retracted
    nmesh = bpy.data.meshes.new("Needle"); nb = bmesh.new()
    bmesh.ops.create_cone(nb, cap_ends=True, segments=8, radius1=0.00042, radius2=0.00004, depth=1.0)
    bmesh.ops.translate(nb, verts=nb.verts, vec=(0, 0, 0.5)); nb.to_mesh(nmesh); nb.free(); nmesh.shade_smooth()
    nm = bpy.data.materials.new("Needle"); nm.use_nodes = True; npb = nm.node_tree.nodes["Principled BSDF"]
    npb.inputs["Base Color"].default_value = (0.92, 0.92, 0.94, 1); npb.inputs["Metallic"].default_value = 1.0
    npb.inputs["Roughness"].default_value = 0.12; npb.inputs["Emission Color"].default_value = (*LED_RGB["derma"], 1)
    es = npb.inputs["Emission Strength"]
    for f in range(1, FR + 1):
        v = sum(math.exp(-(f - f0) / 4) for f0 in SHOTS if f >= f0)
        es.default_value = 3.0 * EXPK * min(1.0, v); es.keyframe_insert("default_value", frame=f)
    nmesh.materials.append(nm)
    import random; rnd = random.Random(5); N = 72
    for i in range(N):
        r = 0.0125 * math.sqrt((i + 0.5) / N); a = i * 2.39996
        x, y = r * math.cos(a), r * math.sin(a)
        d = Vector((x / 0.0125 * 0.6, y / 0.0125 * 0.6, 1.0)).normalized()
        ndl = bpy.data.objects.new("Needle", nmesh); scene.collection.objects.link(ndl)
        ndl.parent = device; ndl.location = (x, y, Z_LENS - 0.004 * (1 - (r / 0.0125) ** 2) - 0.0015)
        ndl.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        L = 0.028 + 0.012 * rnd.random(); j = rnd.random()
        for f in range(1, FR + 1):
            e = 0.0
            for f0 in SHOTS:
                t = f - f0 - j
                if -1 < t <= 2: e = max(e, min(1.0, (t + 1) / 3))                         # out in ~2 frames
                elif 2 < t <= 5: e = max(e, 1.0)                                              # hold
                elif 5 < t <= 9: e = max(e, 1 - (t - 5) / 4)                                  # back in
            ndl.scale = (1, 1, max(0.0002, L * e)); ndl.keyframe_insert("scale", frame=f)
else:
    raise SystemExit("--mode mc | derma")

# ---------------------------------------------------------------- the phrase as gummy jelly letters, standing behind the pudding
# (user 2026-10-15: jelly instead of lipstick). Each glyph is its own object so the impact can travel out from the
# centre: letters pop up from their baseline and keep wobbling. Real geometry, so the pudding refracts them.
TEXT = arg("--text", "")
if TEXT:
    cu = bpy.data.curves.new("Phrase", "FONT"); cu.body = TEXT
    cu.font = bpy.data.fonts.load(arg("--font", "/Library/Fonts/Nunito-Black.ttf"))   # Fredoka/Rubik/Quicksand: overlapping contours break the fill
    cu.size = 1.0; cu.align_x = "CENTER"; cu.resolution_u = 6
    cu.extrude = 0.035; cu.bevel_depth = 0.055; cu.bevel_resolution = 5; cu.offset = -0.045   # puffy, nearly no flat cap
    tob = bpy.data.objects.new("PhraseSrc", cu); scene.collection.objects.link(tob)
    bpy.context.view_layer.update()
    src = tob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    bm = bmesh.new(); bm.from_mesh(src); bm.verts.ensure_lookup_table()
    par = list(range(len(bm.verts)))
    def root(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for e in bm.edges: par[root(e.verts[0].index)] = root(e.verts[1].index)
    isl = {}
    for fc in bm.faces: isl.setdefault(root(fc.verts[0].index), []).append(fc)
    # a glyph can be several islands (the dot of an i, the inside of an o): merge islands that share their x-span
    parts = [(min(v.co.x for fc in fs for v in fc.verts), max(v.co.x for fc in fs for v in fc.verts), fs) for fs in isl.values()]
    parts.sort(key=lambda p: p[1] - p[0], reverse=True); merged = []
    for a0, a1, fs in parts:
        for m_ in merged:
            if min(a1, m_[1]) - max(a0, m_[0]) > 0.6 * (a1 - a0): m_[2].extend(fs); break
        else: merged.append([a0, a1, list(fs)])
    isl = {i: m_[2] for i, m_ in enumerate(merged)}
    xs = [v.co.x for v in bm.verts]; S = float(arg("--text_w", "0.40")) / (max(xs) - min(xs))   # scale to a set width
    TY, TZ = float(arg("--text_y", "0.22")), float(arg("--text_z", "0.122"))
    tm = bpy.data.materials.new("JellyText"); tm.use_nodes = True; tn = tm.node_tree; tp = tn.nodes["Principled BSDF"]
    tcol = (1.0, 0.50, 0.63)       # thin letters need a deeper pink than the pudding to read as the same jelly
    tp.inputs["Base Color"].default_value = (1.0, 0.66, 0.75, 1); tp.inputs["Transmission Weight"].default_value = 1.0
    tp.inputs["Roughness"].default_value = 0.05; tp.inputs["IOR"].default_value = 1.36
    tp.inputs["Subsurface Weight"].default_value = 0.10; tp.inputs["Subsurface Radius"].default_value = (0.01, 0.008, 0.006)
    tp.inputs["Coat Weight"].default_value = 1.0; tp.inputs["Coat Roughness"].default_value = 0.02
    tva = tn.nodes.new("ShaderNodeVolumeAbsorption"); tva.inputs["Color"].default_value = (*tcol, 1)
    tva.inputs["Density"].default_value = float(arg("--text_density", "60"))
    tn.links.new(tva.outputs[0], tn.nodes["Material Output"].inputs["Volume"])
    glyphs = []
    for faces in isl.values():
        vs = {v for fc in faces for v in fc.verts}
        cx = sum(v.co.x for v in vs) / len(vs); by = min(v.co.y for v in vs)       # pivot: bottom centre of the glyph
        nb = bmesh.new(); vm = {v: nb.verts.new(((v.co.x - cx) * S, (v.co.y - by) * S, v.co.z * S)) for v in vs}
        for fc in faces:
            try: nb.faces.new([vm[v] for v in fc.verts])
            except ValueError: pass
        bmesh.ops.remove_doubles(nb, verts=nb.verts, dist=1e-6)      # weld the cap/bevel seams so the remesh sees a closed solid
        bmesh.ops.recalc_face_normals(nb, faces=nb.faces)
        gm = bpy.data.meshes.new("Glyph"); nb.to_mesh(gm); nb.free()
        gm.shade_smooth(); gm.materials.append(tm)
        go = bpy.data.objects.new("Glyph", gm); scene.collection.objects.link(go)
        go.location = (cx * S, TY, TZ + by * S); go.rotation_euler = (math.radians(90), 0, 0)
        rm = go.modifiers.new("Remesh", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = 0.0005; rm.use_smooth_shade = True
        glyphs.append(go)                     # (voxel remesh: the font's overlapping contours, as in t, became dark seams)
    bm.free(); tob.to_mesh_clear(); bpy.data.objects.remove(tob)
    bpy.context.view_layer.update(); dg_ = bpy.context.evaluated_depsgraph_get()
    for g in glyphs:              # the remesh can collapse a glyph (Nunito g): then keep the welded font mesh as it is
        ev = g.evaluated_get(dg_).data
        w0 = max(v.co.x for v in g.data.vertices) - min(v.co.x for v in g.data.vertices)
        w1 = max(v.co.x for v in ev.vertices) - min(v.co.x for v in ev.vertices)
        if w1 < 0.9 * w0:
            g.modifiers.remove(g.modifiers["Remesh"]); g.data.shade_smooth(); g.data.set_sharp_from_angle(angle=math.radians(40))
    # open the word space to the device's width and centre it on the device, so the device stands between the words
    glyphs.sort(key=lambda g: g.location.x)
    ext = [(g.location.x + min(v.co.x for v in g.data.vertices), g.location.x + max(v.co.x for v in g.data.vertices)) for g in glyphs]
    i_gap = max(range(1, len(glyphs)), key=lambda i: ext[i][0] - ext[i - 1][1])
    GAP = float(arg("--text_gap", "0.075")); mid = (ext[i_gap][0] + ext[i_gap - 1][1]) / 2; extra = GAP - (ext[i_gap][0] - ext[i_gap - 1][1])
    for i, g in enumerate(glyphs): g.location.x += -mid + (extra / 2 if i >= i_gap else -extra / 2)
    half = max(abs(g.location.x) for g in glyphs)
    for g in glyphs:
        d = F_TXT + 1 + round(9 * abs(g.location.x) / half)          # the hit travels outwards from the device
        for f in range(1, FR + 1):
            t = f - d
            if t < 0: s, st = 0.001, 0.0
            else:
                s = 1 - math.exp(-t / 3.2) * math.cos(2 * math.pi * t / 11)              # springy pop with overshoot
                st = 0.22 * math.exp(-t / 9) * math.sin(2 * math.pi * t / 8)              # then squash and stretch
            sx = min(s, 1.04) * (1 - 0.3 * st)                     # sideways kept near 1 so neighbours never overlap (v7)
            g.scale = (max(0.001, sx), max(0.001, s * (1 + st)), max(0.001, sx))
            g.keyframe_insert("scale", frame=f)

# ---------------------------------------------------------------- camera
cam = scene.camera
for c in list(cam.constraints): cam.constraints.remove(c)
cam.data.lens = 60; cam.data.dof.use_dof = False
cam.location = (0.0, -0.80, 0.19)
look = Vector((0, 0, 0.115)); cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()

scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = 0.4
scene.render.image_settings.color_mode = "RGBA"
scene.render.use_persistent_data = True
if arg("--still", ""):
    for f in [int(x) for x in arg("--still", "1").split(",")]:
        scene.frame_set(f); scene.render.filepath = os.path.join(ROOT, OUTDIR, f"f{f:04d}.png"); bpy.ops.render.render(write_still=True)
else:
    scene.render.filepath = os.path.join(ROOT, OUTDIR, "f"); bpy.ops.render.render(animation=True)
print("WROTE pudding", OUTDIR)

"""AI beat v3 (user 2026-10-20: "물이 자연스럽게 빠지고, 기기 모니터와 뚜껑 쪽으로 줌인, 왼쪽 아래에서 오른쪽 위로 올라가게
비스듬히, 기기를 오른쪽에 두고 왼쪽 빈 공간에 AI 스마트앱 설명, 배경은 검정으로, 조명을 쏘는 느낌").
Official AI copy: "Smart App Connected Care / *AI applies only to in-app custom mode recommendations"; FAQ: "AI Mode
analyzes your skin condition and skincare habits to recommend a personalized care routine ... through the AGE-R App."

Starts on MASK's last frame (camera under water, device hovering). The water drains out of the tank through the floor
at both ends, out of frame (Mantaflow outflow) — the surface comes down past the floating device. Then the device turns
to lie on a diagonal rising to the right, screen to camera, and the camera moves in on the screen and the cap, keeping
the device on the right. Rendered twice from the one bake, --bg white (the stage) and --bg dark (spot-lit low key);
tools/comp_ai.py crossfades them and turns the backdrop black. Writes render/ai_path.json (surface line, device).

  bake:    Blender --factory-startup -b -P tools/shot_ai.py -- --water 1 --bake 1 --norender 1
  render:  ... -- --water 1 --from_cache 1 --bg white|dark --out render/ai_<bg>/ [--f0 N --f1 N]
"""
import bpy, math, os, sys, json
from mathutils import Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d
OUTDIR = arg("--out", "render/ai_white/"); FR = int(arg("--frames", "174")); BGM = arg("--bg", "white")   # white | studio

sys.argv = [sys.argv[0], "--", "--bg", "dark" if BGM == "studio" else BGM, "--led", "mask", "--color", "pink", "--transparent", "1",
            "--res", arg("--res", "960x540"), "--samples", arg("--samples", "32"), "--no_render", "1"]
_mine = (OUTDIR, FR, argv)
exec(compile(open(os.path.join(HERE, "render_device.py")).read(), "render_device.py", "exec"))
OUTDIR, FR, argv = _mine
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d
import bmesh as _bm

scene = bpy.context.scene; scene.frame_start, scene.frame_end = int(arg("--f0", "1")), int(arg("--f1", str(FR))); scene.render.fps = 24
def sstep(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)
for ob in list(scene.objects):
    if ob.name.startswith("Cyc"): bpy.data.objects.remove(ob)

F_OPEN, F_TURN0, F_TURN1 = 4, 24, 64       # drain opens; the device turns and the camera moves in (shared with comp_ai.py)
F_TXT = int(arg("--f_txt", "90"))                          # the words come in (comp_ai.py uses the same frame)
# v4 spin (user 2026-10-21: "천천히 로테이션" + "글이 나와 있을 때도 천천히, 모니터가 보이는 선에서"):
# one turn while the water drains and the camera moves in, easing down before the words; then a slow steady turn
# through the range where the screen faces the camera (-SWING/2 .. +SWING/2) for as long as the words are up.
SWING = float(arg("--swing", "80")); F_SLOW = F_TXT - 6
def _spin_table(a=24, d=30):
    vs = SWING / (FR - F_SLOW)                               # degrees per frame while the words are up (~20 deg/s)
    T1 = F_SLOW - 1; A1 = 360 - SWING / 2
    vm = (A1 - vs * d / 2) / (T1 - a / 2 - d / 2)
    ang, tab = 0.0, {1: 0.0}
    for f_ in range(2, FR + 1):
        t_ = f_ - 1.5                                        # speed at the middle of the step
        if t_ < a: v_ = vm * t_ / a
        elif t_ < T1 - d: v_ = vm
        elif t_ < T1: v_ = vm + (vs - vm) * (t_ - (T1 - d)) / d
        else: v_ = vs
        ang += v_; tab[f_] = ang
    k_ = (A1) / tab[F_SLOW]                                  # tidy the sum so the screen is exactly at -SWING/2 then
    return {f_: (v_ * k_ if f_ <= F_SLOW else A1 + (v_ - tab[F_SLOW])) for f_, v_ in tab.items()}, vm, vs
SPIN_T, _VM, _VS = _spin_table()
print("SPIN peak %.0f deg/s, slow %.0f deg/s" % (_VM * 24, _VS * 24))
def spin_at(f): return math.radians(SPIN_T[max(1, min(FR, f))])

# ---------------------------------------------------------------- device: MASK's last pose, then onto the diagonal
# MASK (tools/shot_mask.py, tilt_in 55) at f120: t = 104 after the plop
_t = 104
M_TILT = math.radians(4) + math.radians(6) * math.sin(2 * math.pi * _t / 80)
M_ROLL = math.radians(4) * math.sin(2 * math.pi * _t / 64 + 1.0)
M_YAW = math.radians(-20)
DIAG = math.radians(float(arg("--diag", "38")))           # lean of the long axis: bottom-left to top-right
flt = bpy.data.objects.new("Float", None); scene.collection.objects.link(flt)
device.parent = flt; device.location = (0, 0, -0.083)
POSE = {}
for f in range(1, FR + 1):
    k = sstep((f - F_TURN0) / (F_TURN1 - F_TURN0))
    tilt = M_TILT * (1 - k); yaw = M_YAW * (1 - k)
    roll = M_ROLL * (1 - k) + DIAG * k                     # about y: the top swings to the right
    bob = 0.0025 * math.sin(2 * math.pi * f / 70) * (1 - k)
    flt.location = (0, 0, bob); flt.rotation_euler = (tilt, roll, yaw)
    flt.keyframe_insert("location", frame=f); flt.keyframe_insert("rotation_euler", frame=f)
    POSE[f] = (Vector((0, 0, bob)), Euler((tilt, roll, yaw)))
    device.rotation_euler = (0, 0, spin_at(f)); device.keyframe_insert("rotation_euler", frame=f)

# LED: MASK purple -> AI white while it turns (the materials are keyed; one render per backdrop)
for mname in ("Ring", "Lens"):
    m_ = bpy.data.materials.get(mname)
    if not m_: continue
    pr_ = [n_ for n_ in m_.node_tree.nodes if n_.type == "BSDF_PRINCIPLED"][0]; ec = pr_.inputs["Emission Color"]
    ec.keyframe_insert("default_value", frame=F_TURN0 + 10)
    ec.default_value = (*LED_RGB["ai"], 1); ec.keyframe_insert("default_value", frame=F_TURN0 + 18)
sm_ = bpy.data.materials.get("Screen")
if sm_:
    nt_ = sm_.node_tree; pr_ = [n_ for n_ in nt_.nodes if n_.type == "BSDF_PRINCIPLED"][0]
    ui0 = [n_ for n_ in nt_.nodes if n_.type == "TEX_IMAGE" and n_.image and n_.image.name.startswith("screen_mask")][0]
    ui1 = nt_.nodes.new("ShaderNodeTexImage"); ui1.image = img("screen_ai.png")
    mx = nt_.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
    nt_.links.new(ui0.outputs["Color"], mx.inputs["A"]); nt_.links.new(ui1.outputs["Color"], mx.inputs["B"])
    nt_.links.new(mx.outputs["Result"], pr_.inputs["Emission Color"])
    fi = mx.inputs["Factor"]; fi.default_value = 0; fi.keyframe_insert("default_value", frame=F_TURN0 + 10)
    fi.default_value = 1; fi.keyframe_insert("default_value", frame=F_TURN0 + 18)

# ---------------------------------------------------------------- camera: MASK's last framing -> in on the screen and cap
cam = scene.camera
for c_ in list(cam.constraints): cam.constraints.remove(c_)
cam.data.lens = 60; cam.data.dof.use_dof = False
C0, L0 = Vector((0.0, -0.80, 0.075)), Vector((0, 0, 0))
def dev_world(f, local):                                   # a point given in the device's own frame (base at z=0)
    loc, rot = POSE[f]; return loc + rot.to_matrix() @ Vector((local[0], local[1], local[2] - 0.083))
tgt = dev_world(FR, (0, 0, 0.138))                         # between the screen and the cap, on the final pose
L1 = tgt + Vector((-float(arg("--offx", "0.075")), 0, -0.004))           # aim left of it: the device sits right
C1 = L1 + Vector((0.0, -float(arg("--dist", "0.38")), 0.035))
for f in range(1, FR + 1):
    k = sstep((f - F_TURN0 - 4) / (F_TURN1 - F_TURN0 + 8))
    look = L0.lerp(L1, k); loc = C0.lerp(C1, k)
    cam.location = loc; cam.rotation_euler = (look - loc).to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)
scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = 0.4
scene.render.image_settings.color_mode = "RGBA"
# ---------------------------------------------------------------- v4 studio (user 2026-10-21: "공간감 있는 어두운 스튜디오, 조명이 저렴")
# references seen 10/21: PX-01 (Behance, dark grey sweep with a soft pool of light behind the product, floor), CCLIME
# (one long clean highlight down the cylinder). A real sweep and real lights instead of black + a painted beam.
def mat_set(name, **kw):
    m_ = bpy.data.materials.get(name)
    if not m_: return None
    p_ = [n_ for n_ in m_.node_tree.nodes if n_.type == "BSDF_PRINCIPLED"][0]
    for k_, v_ in kw.items(): p_.inputs[k_].default_value = v_
    return m_, p_
MAT = arg("--mat", "pearl")
for nm in ("Body", "BodyPlain"):
    if MAT == "lacquer":      # satin paint under a clear lacquer: one crisp highlight over a soft one
        r_ = mat_set(nm, **{"Roughness": 0.30, "Coat Weight": 0.65, "Coat Roughness": 0.04, "Coat IOR": 1.5})
    elif MAT == "pearl":      # soft-touch with a pearl sheen and a fine grain
        r_ = mat_set(nm, **{"Roughness": 0.36, "Coat Weight": 0.3, "Coat Roughness": 0.12, "Sheen Weight": 0.6,
                            "Sheen Roughness": 0.35, "Sheen Tint": (1.0, 0.93, 0.95, 1), "Thin Film Thickness": 320.0})
    else: r_ = None
    if r_ and MAT == "pearl":
        m_, p_ = r_; nt_ = m_.node_tree
        nz = nt_.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9000; nz.inputs["Detail"].default_value = 2
        bz = nt_.nodes.new("ShaderNodeBump"); bz.inputs["Strength"].default_value = 0.06; bz.inputs["Distance"].default_value = 0.00003
        nt_.links.new(nz.outputs["Fac"], bz.inputs["Height"])
        prev = p_.inputs["Normal"].links[0].from_socket if p_.inputs["Normal"].links else None
        if prev: nt_.links.new(prev, bz.inputs["Normal"])
        nt_.links.new(bz.outputs["Normal"], p_.inputs["Normal"])

def add_droplets(name):
    """v4: the device has just come out of the water — small beads on the lacquer, drying to a few by the end.
    Beads: a voronoi cell per ~2.5 mm, ~40 % of cells carry one, radius varies; they ride with the spinning body."""
    m_ = bpy.data.materials.get(name)
    if not m_: return
    nt_ = m_.node_tree; N2 = nt_.nodes.new; L2 = nt_.links.new
    p_ = [n_ for n_ in nt_.nodes if n_.type == "BSDF_PRINCIPLED"][0]
    def mm(op, a_, b_=None, clamp=False):
        n_ = N2("ShaderNodeMath"); n_.operation = op; n_.use_clamp = clamp
        for i_, v_ in enumerate((a_, b_)):
            if v_ is None: continue
            if isinstance(v_, (int, float)): n_.inputs[i_].default_value = v_
            else: L2(v_, n_.inputs[i_])
        return n_.outputs[0]
    tc = N2("ShaderNodeTexCoord"); vo = N2("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = float(arg("--drop_scale", "380"))
    L2(tc.outputs["Object"], vo.inputs["Vector"])
    sep = N2("ShaderNodeSeparateColor"); L2(vo.outputs["Color"], sep.inputs[0])
    rad = mm("ADD", mm("MULTIPLY", sep.outputs["Red"], 0.22), 0.10)               # bead radius in cell units
    bead = mm("POWER", mm("SUBTRACT", 1.0, mm("DIVIDE", vo.outputs["Distance"], rad), clamp=True), 0.5)
    wet = N2("ShaderNodeValue"); wet.name = "Wet"
    keep = mm("GREATER_THAN", sep.outputs["Green"], mm("SUBTRACT", 1.0, mm("MULTIPLY", wet.outputs[0], 0.42)))
    b = mm("MULTIPLY", bead, keep)
    bz = N2("ShaderNodeBump"); bz.inputs["Distance"].default_value = 0.0005; L2(b, bz.inputs["Strength"])
    L2(b, bz.inputs["Height"])
    prev = p_.inputs["Normal"].links[0].from_socket if p_.inputs["Normal"].links else None
    if prev: L2(prev, bz.inputs["Normal"])
    L2(bz.outputs["Normal"], p_.inputs["Normal"])
    cr = mm("MULTIPLY", p_.inputs["Coat Roughness"].default_value, mm("SUBTRACT", 1.0, b)); L2(cr, p_.inputs["Coat Roughness"])
    cw = mm("MAXIMUM", p_.inputs["Coat Weight"].default_value, b); L2(cw, p_.inputs["Coat Weight"])
    for f_, v_ in ((1, 1.0), (F_TURN0, 1.0), (FR, float(arg("--dry", "0.35")))):
        wet.outputs[0].default_value = v_; wet.outputs[0].keyframe_insert("default_value", frame=f_)

if BGM == "studio":
    if arg("--drops", "1") == "1":
        for nm in ("Body", "BodyPlain"): add_droplets(nm)
    for ob in list(scene.objects):                          # render_device's low-key rig goes; this one replaces it
        if ob.name in ("Key", "Rim", "StripL", "StripR", "TopCard", "Glow", "FlagL", "FlagR", "Ceiling"): bpy.data.objects.remove(ob)
    scene.render.film_transparent = False
    # the sweep: floor (the tank's floor, where the water goes) curving up into a back wall
    FLOOR, WALL_Y, RC = -0.20, 0.95, 0.35
    sw = [(-2.0, FLOOR)] + [(WALL_Y - RC + math.sin(i / 32 * math.pi / 2) * RC, FLOOR + RC - math.cos(i / 32 * math.pi / 2) * RC) for i in range(33)] + [(WALL_Y, 2.5)]
    me_s = bpy.data.meshes.new("Sweep"); nS = len(sw)
    me_s.from_pydata([(-3, y, z) for y, z in sw] + [(3, y, z) for y, z in sw], [], [(i, i + 1, nS + i + 1, nS + i) for i in range(nS - 1)])
    for pg in me_s.polygons: pg.use_smooth = True
    swo = bpy.data.objects.new("Sweep", me_s); scene.collection.objects.link(swo)
    ms = bpy.data.materials.new("Sweep"); ms.use_nodes = True; ps = ms.node_tree.nodes["Principled BSDF"]
    g_ = float(arg("--sweep", "0.045")); ps.inputs["Base Color"].default_value = (g_, g_, g_ * 1.04, 1)
    ps.inputs["Roughness"].default_value = 0.95; ps.inputs["Specular IOR Level"].default_value = 0.0   # no floor reflections (user 10/21)
    swo.data.materials.append(ms)

    AX = Vector((math.sin(DIAG), 0, math.cos(DIAG)))         # the device's long axis on its final diagonal
    CEN = dev_world(FR, (0, 0, 0.09))
    def strip(name, loc, size, energy, color=(1, 1, 1), spread=None, along=True, cam_vis=False):
        """area light aimed at the device; with along=True its long side lies along the device's axis"""
        ld = bpy.data.lights.new(name, "AREA"); ld.shape = "RECTANGLE"; ld.size, ld.size_y = size; ld.energy = energy; ld.color = color
        if spread: ld.spread = math.radians(spread)
        ob_ = bpy.data.objects.new(name, ld); scene.collection.objects.link(ob_); ob_.location = loc
        zc = (Vector(loc) - CEN).normalized()                 # light's +Z points away from the device
        yc = AX - zc * AX.dot(zc) if along else Vector((0, 0, 1)) - zc * zc.z
        yc.normalize(); xc = yc.cross(zc)
        from mathutils import Matrix
        ob_.matrix_world = Matrix((xc, yc, zc)).transposed().to_4x4() @ Matrix.Identity(4)
        ob_.location = loc; ld.cycles.is_caustics_light = False
        ob_.visible_camera = cam_vis
        return ob_
    def refl_card(name, ang, dist, width, length, strength, color=(1, 1, 1)):
        """an emissive card seen only in reflections (no diffuse light, no shadow): a clean highlight line down the
        cylinder without flattening its shading. ang: degrees round the axis from the camera side (+ = up/left)"""
        from mathutils import Matrix
        vc = C1 - CEN; vc = (vc - AX * vc.dot(AX)).normalized()
        dirv = Matrix.Rotation(math.radians(ang), 3, AX) @ vc
        loc = CEN + dirv * dist
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc); ob_ = bpy.context.active_object; ob_.name = name
        zc = dirv; yc = AX; xc = yc.cross(zc)
        ob_.matrix_world = Matrix((xc, yc, zc)).transposed().to_4x4(); ob_.location = loc; ob_.scale = (width, length, 1)
        m_ = bpy.data.materials.new(name); m_.use_nodes = True; nt_ = m_.node_tree
        for n_ in list(nt_.nodes):
            if n_.type != "OUTPUT_MATERIAL": nt_.nodes.remove(n_)
        e_ = nt_.nodes.new("ShaderNodeEmission"); e_.inputs["Color"].default_value = (*color, 1)
        # soft edges across the width (a softbox, not a tube): strength falls off as cos^2 from the centre line
        tc = nt_.nodes.new("ShaderNodeTexCoord"); sx = nt_.nodes.new("ShaderNodeSeparateXYZ"); nt_.links.new(tc.outputs["Generated"], sx.inputs[0])
        m1 = nt_.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"; m1.inputs[1].default_value = math.pi
        nt_.links.new(sx.outputs["X"], m1.inputs[0])
        m2 = nt_.nodes.new("ShaderNodeMath"); m2.operation = "SINE"; nt_.links.new(m1.outputs[0], m2.inputs[0])
        m3 = nt_.nodes.new("ShaderNodeMath"); m3.operation = "POWER"; m3.inputs[1].default_value = 2.0; nt_.links.new(m2.outputs[0], m3.inputs[0])
        m4 = nt_.nodes.new("ShaderNodeMath"); m4.operation = "MULTIPLY"; m4.inputs[1].default_value = strength; nt_.links.new(m3.outputs[0], m4.inputs[0])
        nt_.links.new(m4.outputs[0], e_.inputs["Strength"])
        nt_.links.new(e_.outputs[0], [n_ for n_ in nt_.nodes if n_.type == "OUTPUT_MATERIAL"][0].inputs["Surface"])
        ob_.data.materials.append(m_)
        ob_.visible_camera = False; ob_.visible_diffuse = False; ob_.visible_shadow = False; ob_.visible_volume_scatter = False
        return ob_
    refl_card("HiLine", float(arg("--hl_ang", "35")), 0.30, float(arg("--hl_w", "0.12")), 0.7, float(arg("--hl", "10")))
    refl_card("HiSoft", float(arg("--hs_ang", "-55")), 0.30, 0.10, 0.7, float(arg("--hs", "2.5")))
    K = float(arg("--lk", "1.0"))
    strip("TopStrip", CEN + Vector((-0.20, -0.16, 0.22)), (0.05, 0.55), float(arg("--e_top", "0")) * K, spread=40)        # the long highlight
    strip("KeySoft", CEN + Vector((-0.45, -0.35, 0.10)), (0.45, 0.45), float(arg("--e_key", "30")) * K, color=(1.0, 0.97, 0.95), along=False)
    strip("RimL", CEN + Vector((-0.30, 0.28, 0.05)), (0.03, 0.6), float(arg("--e_riml", "22")) * K, spread=30)               # edge lines
    strip("RimR", CEN + Vector((0.32, 0.22, -0.02)), (0.03, 0.6), float(arg("--e_rimr", "18")) * K, color=(0.95, 0.97, 1.0), spread=30)
    # the pool of light on the back wall, behind and a little left of the device: the room
    pl = bpy.data.lights.new("Pool", "SPOT"); pl.energy = float(arg("--pool", "160")) * K; pl.spot_size = math.radians(70)
    pl.spot_blend = 1.0; pl.shadow_soft_size = 0.3; pl.color = (1.0, 0.95, 0.93)
    plo = bpy.data.objects.new("Pool", pl); scene.collection.objects.link(plo); plo.location = (0.10, 0.55, 0.45)
    plo.rotation_euler = (Vector((-0.08, WALL_Y, 0.02)) - plo.location).to_track_quat("-Z", "Y").to_euler()
    pl.cycles.is_caustics_light = False
    # black flags so the chrome keeps dark bands
    for nm_, loc_, sz_ in (("FlagL", (-0.16, -0.25, 0.2), (0.12, 0.5)), ("FlagR", (0.17, -0.22, 0.2), (0.10, 0.5))):
        flag(nm_, loc_, sz_)
    cam.data.dof.use_dof = arg("--dof", "1") == "1"; cam.data.dof.aperture_fstop = float(arg("--fstop", "4"))
    cam.data.dof.focus_object = None
    for f in range(1, FR + 1):
        cam.data.dof.focus_distance = (dev_world(f, (0, 0, 0.14)) - Vector(cam.matrix_world.translation)).length if False else \
            (dev_world(f, (0, 0, 0.13)) - C0.lerp(C1, sstep((f - F_TURN0 - 4) / (F_TURN1 - F_TURN0 + 8)))).length - R
        cam.data.dof.keyframe_insert("focus_distance", frame=f)
    scene.cycles.samples = int(arg("--samples", "48"))
    if arg("--ai3d", "0") == "1":                       # option B: "AI" as edge-lit frosted acrylic standing in the studio
        fwd = (L1 - C1).normalized(); rgt = fwd.cross(Vector((0, 0, 1))).normalized(); upv = rgt.cross(fwd)
        d_ = (CEN - C1).dot(fwd); hw = d_ * 18 / 60; hh = hw * 9 / 16
        tx, ty = float(arg("--ai_x", "0.25")), float(arg("--ai_y", "0.42"))          # centre, as a fraction of the frame
        loc = C1 + fwd * d_ + rgt * ((tx * 2 - 1) * hw) + upv * ((1 - ty * 2) * hh)
        cu = bpy.data.curves.new("AIText", "FONT"); cu.body = "AI"
        cu.font = bpy.data.fonts.load(arg("--ai_font", "/Library/Fonts/Manrope-ExtraBold.ttf"))
        cu.size = float(arg("--ai_h", "0.20")) * 2 * hh * 1.38; cu.align_x = "CENTER"; cu.align_y = "CENTER"
        cu.extrude = cu.size * 0.06; cu.bevel_depth = cu.size * 0.012; cu.bevel_resolution = 3
        txo = bpy.data.objects.new("AIText", cu); scene.collection.objects.link(txo)
        txo.location = loc; txo.rotation_euler = (-fwd).to_track_quat("Z", "Y").to_euler()
        ma = bpy.data.materials.new("Acrylic"); ma.use_nodes = True; na = ma.node_tree.nodes; pa = na["Principled BSDF"]
        pa.inputs["Base Color"].default_value = (1, 1, 1, 1); pa.inputs["Transmission Weight"].default_value = 1.0
        pa.inputs["Roughness"].default_value = float(arg("--ai_rough", "0.4")); pa.inputs["IOR"].default_value = 1.49
        lw = na.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
        em_ = na.new("ShaderNodeMath"); em_.operation = "MULTIPLY"; em_.inputs[1].default_value = float(arg("--ai_glow", "1.6")) * EXPK
        ma.node_tree.links.new(lw.outputs["Facing"], em_.inputs[0])
        pa.inputs["Emission Color"].default_value = (*LED_RGB["ai"], 1); ma.node_tree.links.new(em_.outputs[0], pa.inputs["Emission Strength"])
        cu.materials.append(ma)

# ---------------------------------------------------------------- water (MASK's tank, drained through the floor at both ends)
WATER = arg("--water", "0") == "1"
SURF = {}
if WATER:
    FX0, FX1, FY0, FY1, FZ0, FZ1 = -0.27, 0.27, -0.07, 0.07, -0.20, 0.24
    Z_W0 = 0.17
    CACHE = os.path.join(ROOT, arg("--cache", "render/ai_fluid4")); FROMC = arg("--from_cache", "0") == "1"
    FEND = int(arg("--fend", "110"))
    def box(name, x0, x1, y0, y1, z0, z1):
        me_ = bpy.data.meshes.new(name); b_ = _bm.new(); _bm.ops.create_cube(b_, size=1.0); b_.to_mesh(me_); b_.free()
        ob_ = bpy.data.objects.new(name, me_); scene.collection.objects.link(ob_)
        ob_.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); ob_.scale = (x1 - x0, y1 - y0, z1 - z0)
        return ob_
    dom = box("FluidDomain", FX0, FX1, FY0, FY1, FZ0, FZ1)
    me_ = bpy.data.meshes.new("ColliderMesh"); b_ = _bm.new()
    _bm.ops.create_cone(b_, cap_ends=True, segments=24, radius1=R, radius2=R, depth=0.165)
    _bm.ops.translate(b_, verts=b_.verts, vec=(0, 0, 0.0825)); b_.to_mesh(me_); b_.free()
    col = bpy.data.objects.new("Collider", me_); scene.collection.objects.link(col); col.parent = device; col.hide_render = True
    if not FROMC:
        md = dom.modifiers.new("Fluid", "FLUID"); md.fluid_type = "DOMAIN"; ds = md.domain_settings
        ds.domain_type = "LIQUID"; ds.resolution_max = int(arg("--fres", "170")); ds.cache_directory = CACHE
        ds.cache_type = "ALL"; ds.cache_frame_start = 1; ds.cache_frame_end = FEND
        ds.use_mesh = True; ds.mesh_scale = 2; ds.particle_radius = 1.6; ds.mesh_particle_radius = 1.4
        ds.particle_band_width = 5.0; ds.use_spray_particles = False; ds.use_bubble_particles = False
        ds.timesteps_max = 8; ds.timesteps_min = 2; ds.cfl_condition = 3.0
        ds.time_scale = float(arg("--tscale", "0.6"))            # MASK ran at 0.35; a little quicker here, still slowed
        w0 = box("WaterInit", FX0 + 0.004, FX1 - 0.004, FY0 + 0.004, FY1 - 0.004, FZ0 + 0.004, Z_W0)
        mw_ = w0.modifiers.new("Fluid", "FLUID"); mw_.fluid_type = "FLOW"; fs = mw_.flow_settings
        fs.flow_type = "LIQUID"; fs.flow_behavior = "GEOMETRY"; fs.flow_source = "MESH"; w0.hide_render = True
        # v4: narrow slots spread evenly over the floor. The whole floor open drained it in 0.5 s (free fall); slots
        # limit the flow so the level comes down evenly and calmly (v3's two end drains tilted and sloshed it)
        NS, SW = int(arg("--slots", "9")), float(arg("--slot_w", "0.008"))
        for i_ in range(NS):
            xc_ = FX0 + (FX1 - FX0) * (i_ + 0.5) / NS
            dr = box(f"Drain{i_}", xc_ - SW / 2, xc_ + SW / 2, FY0 + 0.004, FY1 - 0.004, FZ0 + 0.001, FZ0 + 0.012)
            dr.hide_render = True; md2 = dr.modifiers.new("Fluid", "FLUID"); md2.fluid_type = "FLOW"; fs2 = md2.flow_settings
            fs2.flow_type = "LIQUID"; fs2.flow_behavior = "OUTFLOW"; fs2.flow_source = "MESH"
            fs2.use_inflow = False; fs2.keyframe_insert("use_inflow", frame=F_OPEN - 1); fs2.use_inflow = True; fs2.keyframe_insert("use_inflow", frame=F_OPEN)
        mc = col.modifiers.new("Fluid", "FLUID"); mc.fluid_type = "EFFECTOR"; es = mc.effector_settings
        es.effector_type = "COLLISION"; es.subframes = 2; es.use_effector = True
        if arg("--bake", "0") == "1":
            bpy.context.view_layer.objects.active = dom; dom.select_set(True)
            with bpy.context.temp_override(object=dom, active_object=dom):
                bpy.ops.fluid.bake_all()
            print("BAKED", CACHE)
    # MASK v6's water: plain transparent at the tank's faces and on the film that wraps the device; colour is the comp's
    wm = bpy.data.materials.new("Water"); wm.use_nodes = True; nt = wm.node_tree; N_ = nt.nodes.new; L_ = nt.links.new
    wp = [n_ for n_ in nt.nodes if n_.type == "BSDF_PRINCIPLED"][0]
    wp.inputs["Base Color"].default_value = (1, 1, 1, 1); wp.inputs["Transmission Weight"].default_value = 1.0
    wp.inputs["Roughness"].default_value = 0.02; wp.inputs["IOR"].default_value = 1.333
    va_ = N_("ShaderNodeVolumeAbsorption"); va_.inputs["Color"].default_value = (0.70, 0.84, 1.0, 1); va_.inputs["Density"].default_value = 1.2
    outn = [n_ for n_ in nt.nodes if n_.type == "OUTPUT_MATERIAL"][0]; L_(va_.outputs[0], outn.inputs["Volume"])
    def mth(op, a_, b_):
        n_ = N_("ShaderNodeMath"); n_.operation = op
        for i_, v_ in enumerate((a_, b_)):
            if isinstance(v_, (int, float)): n_.inputs[i_].default_value = v_
            else: L_(v_, n_.inputs[i_])
        return n_.outputs[0]
    geo_ = N_("ShaderNodeNewGeometry"); gx_ = N_("ShaderNodeSeparateXYZ"); L_(geo_.outputs["Position"], gx_.inputs[0])
    wall_ = mth("MAXIMUM", mth("GREATER_THAN", mth("ABSOLUTE", gx_.outputs["X"], 0), FX1 - 0.006),
                mth("GREATER_THAN", mth("ABSOLUTE", gx_.outputs["Y"], 0), FY1 - 0.006))
    tc_ = N_("ShaderNodeTexCoord"); tc_.object = col; sx_ = N_("ShaderNodeSeparateXYZ"); L_(tc_.outputs["Object"], sx_.inputs[0])
    rad_ = mth("SQRT", mth("ADD", mth("MULTIPLY", sx_.outputs["X"], sx_.outputs["X"]), mth("MULTIPLY", sx_.outputs["Y"], sx_.outputs["Y"])), 0)
    near_ = mth("MULTIPLY", mth("MULTIPLY", mth("LESS_THAN", rad_, R + 0.007), mth("GREATER_THAN", sx_.outputs["Z"], -0.007)),
                mth("LESS_THAN", sx_.outputs["Z"], 0.172))
    clr_ = mth("MAXIMUM", wall_, near_)
    LEVEL = N_("ShaderNodeValue"); LEVEL.name = "LevelZ"; LEVEL.outputs[0].default_value = 9.0
    if BGM == "studio":   # v4: above the still level the sim's water is the film/skirt on the device -> clear (comp draws the water)
        gpos_ = N_("ShaderNodeNewGeometry"); gz_ = N_("ShaderNodeSeparateXYZ"); L_(gpos_.outputs["Position"], gz_.inputs[0])
        clr_ = mth("MAXIMUM", clr_, mth("GREATER_THAN", gz_.outputs["Z"], LEVEL.outputs[0]))
    FADEV = N_("ShaderNodeValue"); FADEV.name = "WaterFade"; FADEV.outputs[0].default_value = 0.0
    if BGM == "studio":   # once the level is under the device the leftover pool fades out (its reflections distracted)
        clr_ = mth("MAXIMUM", clr_, FADEV.outputs[0])
    tr_ = N_("ShaderNodeBsdfTransparent"); mix_ = N_("ShaderNodeMixShader"); L_(clr_, mix_.inputs["Fac"])
    L_(wp.outputs[0], mix_.inputs[1]); L_(tr_.outputs[0], mix_.inputs[2]); L_(mix_.outputs[0], outn.inputs["Surface"])
    dom.data.materials.append(wm)
    wnt = scene.world.node_tree; bgn = [n_ for n_ in wnt.nodes if n_.type == "BACKGROUND"][0]; outw = [n_ for n_ in wnt.nodes if n_.type == "OUTPUT_WORLD"][0]
    lpn = wnt.nodes.new("ShaderNodeLightPath"); wbg = wnt.nodes.new("ShaderNodeBackground")
    wbg.inputs["Color"].default_value = (0.96, 0.97, 0.99, 1) if BGM == "white" else (0.03, 0.03, 0.035, 1)
    wbg.inputs["Strength"].default_value = 1.0 * EXPK
    mixw = wnt.nodes.new("ShaderNodeMixShader"); mxf = wnt.nodes.new("ShaderNodeMath"); mxf.operation = "MAXIMUM"
    wnt.links.new(lpn.outputs["Is Transmission Ray"], mxf.inputs[0]); wnt.links.new(lpn.outputs["Is Glossy Ray"], mxf.inputs[1])
    wnt.links.new(mxf.outputs[0], mixw.inputs["Fac"]); wnt.links.new(bgn.outputs[0], mixw.inputs[1]); wnt.links.new(wbg.outputs[0], mixw.inputs[2])
    wnt.links.new(mixw.outputs[0], outw.inputs["Surface"])
    scene.cycles.transmission_bounces = 32; scene.cycles.max_bounces = 32; scene.cycles.volume_bounces = 1
    if FROMC:
        import gzip, struct
        import numpy as _np
        L = max(FX1 - FX0, FY1 - FY0, FZ1 - FZ0); dom.scale = (L, L, L)     # the cache is scaled by the longest side
        CEN = Vector(((FX0 + FX1) / 2, (FY0 + FY1) / 2, (FZ0 + FZ1) / 2))
        _loaded = {"f": None}
        def load_water(f):
            f = min(f, FEND)
            if _loaded["f"] == f: return
            fn = os.path.join(CACHE, "mesh", f"fluid_mesh_{f:04d}.bobj.gz")
            if not os.path.exists(fn): return
            raw = gzip.open(fn).read(); o = 0
            nv = struct.unpack_from("i", raw, o)[0]; o += 4; co = _np.frombuffer(raw, _np.float32, nv * 3, o); o += nv * 12
            nn = struct.unpack_from("i", raw, o)[0]; o += 4 + nn * 12
            ntr = struct.unpack_from("i", raw, o)[0]; o += 4; tri = _np.frombuffer(raw, _np.int32, ntr * 3, o)
            m_ = bpy.data.meshes.new(f"Water{f}")
            m_.vertices.add(nv); m_.vertices.foreach_set("co", co)
            m_.loops.add(ntr * 3); m_.loops.foreach_set("vertex_index", tri)
            m_.polygons.add(ntr); m_.polygons.foreach_set("loop_start", _np.arange(0, ntr * 3, 3, dtype=_np.int32))
            m_.update(calc_edges=True); m_.shade_smooth(); m_.materials.append(wm)
            old_ = dom.data; dom.data = m_; bpy.data.meshes.remove(old_); _loaded["f"] = f
            # the still surface in the middle of the tank (for the comp's under-water grade): the median of the
            # highest water in 1 cm columns across the frame
            v = co.reshape(-1, 3) * L + _np.array(CEN, _np.float32)
            sel = (_np.abs(v[:, 0]) < 0.22) & (_np.abs(v[:, 0]) > 0.04)    # away from the water clinging to the device
            if sel.sum() > 100:
                xs = ((v[sel, 0] + 0.22) / 0.01).astype(int); top = _np.full(45, -9.0, _np.float32)
                _np.maximum.at(top, xs, v[sel, 2]); top = top[top > -9]
                SURF[f] = float(_np.median(top)) if len(top) else -1.0
                LEVEL.outputs[0].default_value = SURF[f] + 0.0015 if SURF[f] > -0.19 else -9.0
            else:
                SURF[f] = -1.0
        def _on_frame(sc, *_):
            FADEV.outputs[0].default_value = sstep((sc.frame_current - float(arg("--fade0", "26"))) / 8.0)
            load_water(sc.frame_current)
        bpy.app.handlers.frame_change_pre.append(_on_frame)
        scene.render.use_persistent_data = False

if arg("--still", ""):
    for f in [int(x) for x in arg("--still", "1").split(",")]:
        scene.frame_set(f); scene.render.filepath = os.path.join(ROOT, OUTDIR, f"f{f:04d}.png"); bpy.ops.render.render(write_still=True)
elif arg("--norender", "0") != "1":
    scene.render.filepath = os.path.join(ROOT, OUTDIR, "f"); bpy.ops.render.render(animation=True)

if arg("--path", "0") == "1":                                  # screen positions for the comp
    from bpy_extras.object_utils import world_to_camera_view
    out = {"surface": {}, "head": {}, "base": {}}
    for f in range(1, FR + 1):
        scene.frame_set(f)
        z = SURF.get(min(f, int(arg("--fend", "110"))), -1.0)
        c = world_to_camera_view(scene, cam, Vector((0, 0, z))); out["surface"][f] = 1 - c.y if z > -0.9 else 2.0
        h = world_to_camera_view(scene, cam, dev_world(f, (0, 0, 0.16))); out["head"][f] = [h.x, 1 - h.y]
        b = world_to_camera_view(scene, cam, dev_world(f, (0, 0, 0.0))); out["base"][f] = [b.x, 1 - b.y]
    json.dump(out, open(os.path.join(ROOT, "render", "ai_path.json"), "w")); print("WROTE ai_path.json")
print("WROTE ai", OUTDIR)

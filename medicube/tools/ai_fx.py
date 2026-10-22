"""AI beat, effects pass (run inside tools/shot_ai.py with --fx 1). Everything else is a holdout, so this renders only:
  - the MASK air letters, carried with the draining water down into the hole (glass at the air/water IOR, as in MASK)
  - a laser from the device's light ring sweeping the hole, then tracing its rim          (F_LASER .. F_NET)
  - electricity jumping from the cap to the rim, weaving a net across the hole, a skin over it (F_NET .. F_AI)
  - "AI" written in light on the mended net                                                (F_AI ..)
Light and lines only — no readings (official: AI applies only to in-app custom mode recommendations).
"""
import json, random
import bmesh as _bmx
_air = json.load(open(os.path.join(ROOT, "render", "mask_air.json")))
AI_BLUE = (0.42, 0.68, 1.0)

for ob in list(device.children_recursive) + [floor, pit]:
    if ob.type in ("MESH", "CURVE", "FONT"): ob.is_holdout = True
scene.render.film_transparent = True; scene.cycles.film_transparent_glass = True
scene.cycles.transmission_bounces = 12; scene.cycles.glossy_bounces = 8; scene.cycles.max_bounces = 16

# the bubbles' world, as in tools/mask_air.py (bright above, deep water below)
w_ = bpy.data.worlds.new("FxWorld"); w_.use_nodes = True; scene.world = w_; wn = w_.node_tree.nodes; wl = w_.node_tree.links
tcw = wn.new("ShaderNodeTexCoord"); sxw = wn.new("ShaderNodeSeparateXYZ"); wl.new(tcw.outputs["Generated"], sxw.inputs[0])
mrw = wn.new("ShaderNodeMapRange"); mrw.inputs["From Min"].default_value = -1.0; wl.new(sxw.outputs["Z"], mrw.inputs["Value"])
crw = wn.new("ShaderNodeValToRGB"); wl.new(mrw.outputs["Result"], crw.inputs["Fac"])
crw.color_ramp.elements[0].color = (0.06, 0.13, 0.30, 1); crw.color_ramp.elements[1].position = 0.90
crw.color_ramp.elements[1].color = (1.6, 1.6, 1.6, 1); e_ = crw.color_ramp.elements.new(0.62); e_.color = (0.30, 0.45, 0.72, 1)
bgw = [n_ for n_ in wn if n_.type == "BACKGROUND"][0]; wl.new(crw.outputs["Color"], bgw.inputs["Color"]); bgw.inputs["Strength"].default_value = 1.4 * EXPK

def emit_mat(name, rgb, k, alpha=1.0):
    m_ = bpy.data.materials.new(name); m_.use_nodes = True; n_ = m_.node_tree.nodes
    for x_ in list(n_):
        if x_.type != "OUTPUT_MATERIAL": n_.remove(x_)
    out_ = [x_ for x_ in n_ if x_.type == "OUTPUT_MATERIAL"][0]
    em_ = n_.new("ShaderNodeEmission"); em_.inputs["Color"].default_value = (*rgb, 1); em_.inputs["Strength"].default_value = k * EXPK
    if alpha < 1:
        tr_ = n_.new("ShaderNodeBsdfTransparent"); mx_ = n_.new("ShaderNodeMixShader"); mx_.inputs["Fac"].default_value = alpha
        m_.node_tree.links.new(tr_.outputs[0], mx_.inputs[1]); m_.node_tree.links.new(em_.outputs[0], mx_.inputs[2])
        m_.node_tree.links.new(mx_.outputs[0], out_.inputs["Surface"])
    else:
        m_.node_tree.links.new(em_.outputs[0], out_.inputs["Surface"])
    return m_, em_

# ---------------------------------------------------------------- the MASK air letters go down the drain
am = bpy.data.materials.new("Air"); am.use_nodes = True; an = am.node_tree.nodes
for n_ in list(an):
    if n_.type != "OUTPUT_MATERIAL": an.remove(n_)
gl_ = an.new("ShaderNodeBsdfGlass"); gl_.inputs["IOR"].default_value = 1 / 1.333; gl_.inputs["Roughness"].default_value = 0.0
am.node_tree.links.new(gl_.outputs[0], [n_ for n_ in an if n_.type == "OUTPUT_MATERIAL"][0].inputs["Surface"])
sph = bpy.data.meshes.new("Bubble"); b_ = _bmx.new(); _bmx.ops.create_icosphere(b_, subdivisions=3, radius=1.0); b_.to_mesh(sph); b_.free()
for p_ in sph.polygons: p_.use_smooth = True
sph.materials.append(am)
scene.frame_set(1)                                  # the word sits where MASK's last frame held it
tr, br, bl, tl = [cam.matrix_world @ (v * (0.70 / -v.z)) for v in cam.data.view_frame(scene=scene)]
WID = (tr - tl).length
HOLE = Vector((HX, HY, FLOOR))
rnd_ = random.Random(3); BUB = []
for u, v, r, ph, lag in _air["letters"]:
    p0 = tl + (tr - tl) * u + (bl - tl) * v
    ob_ = bpy.data.objects.new("Air", sph); scene.collection.objects.link(ob_)
    d0 = Vector((p0.x - HX, p0.y - HY)); BUB.append((ob_, p0, d0.length, math.atan2(d0.y, d0.x), r * WID, ph, lag, rnd_.uniform(0.8, 1.25)))

def place_bubbles(t_):
    for ob_, p0, rad0, ang0, r, ph, lag, sp in BUB:
        a = (t_ - 8 - lag * 14 - (rad0 / 0.2) * 6) / (34 * sp)            # nearer the hole goes first
        if a <= 0:
            ob_.hide_render = False; ob_.location = p0 + Vector((0, 0, 0.0006 * math.sin(t_ * 0.2 + ph)))
            ob_.scale = (r, r * 0.86, r); continue
        if a >= 1: ob_.hide_render = True; continue
        e = a ** 1.6                                                       # drawn in, faster and faster
        rad = rad0 * (1 - e) ** 1.3; ang = ang0 + 5.0 * e * e             # swirl tighter as it nears the hole
        z = p0.z + (FLOOR - 0.03 - p0.z) * (e ** 1.2)
        ob_.hide_render = False
        ob_.location = (HX + rad * math.cos(ang), HY + rad * math.sin(ang), z)
        s = r * (1 - 0.6 * e); ob_.scale = (s, s * (0.86 - 0.3 * e), s)    # stretched as it is pulled

# ---------------------------------------------------------------- laser
def dev_pt(z_local, x_local=0.0, y_local=0.0): return device.matrix_world @ Vector((x_local, y_local, z_local))
RING_Z = (Z_BODY + Z_GASK) / 2; TOP_Z = dome_z(0)
lm, lem = emit_mat("Laser", AI_BLUE, 2.5, alpha=0.30)          # the fan of light: faint
hm, hem = emit_mat("LaserHit", (0.75, 0.88, 1.0), 14)          # where it touches the floor: bright
fan_me = bpy.data.meshes.new("Fan"); fan = bpy.data.objects.new("Fan", fan_me); scene.collection.objects.link(fan); fan_me.materials.append(lm)
hit_me = bpy.data.meshes.new("Hit"); hit = bpy.data.objects.new("Hit", hit_me); scene.collection.objects.link(hit); hit_me.materials.append(hm)
def set_mesh(me_, verts, faces):
    me_.clear_geometry(); me_.from_pydata([tuple(v) for v in verts], [], faces); me_.update()
def curve_obj(name, n, mat, bev):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = bev; cu.bevel_resolution = 2
    sp = cu.splines.new("POLY"); sp.points.add(n - 1); cu.materials.append(mat)
    ob_ = bpy.data.objects.new(name, cu); scene.collection.objects.link(ob_); return ob_
rimm, _ = emit_mat("Rim", (0.75, 0.88, 1.0), 10)
rim = curve_obj("RimTrace", 121, rimm, 0.0007)
for i, p_ in enumerate(rim.data.splines[0].points):
    a_ = 2 * math.pi * i / 120; p_.co = (HX + (HR + 0.002) * math.cos(a_), HY + (HR + 0.002) * math.sin(a_), FLOOR + 0.0008, 1)

def place_laser(t_):
    s = (t_ - F_LASER) / 14                                   # sweep across the hole and back
    on = F_LASER <= t_ < F_NET
    fan.hide_render = hit.hide_render = not on
    if on:
        sw = math.sin(math.pi * min(max(s, 0), 2) / 2) if s < 2 else 0
        yoff = -HR * 1.05 + 2.1 * HR * (0.5 - 0.5 * math.cos(math.pi * min(max(s, 0), 2)))   # 0 -> across -> back
        half = math.sqrt(max(HR * HR * 1.21 - (yoff * 0.95) ** 2, (HR * 0.25) ** 2))
        A = Vector((HX - half, HY + yoff, FLOOR + 0.0008)); B = Vector((HX + half, HY + yoff, FLOOR + 0.0008))
        src = dev_pt(RING_Z, -R * 0.6, -R * 0.4)
        set_mesh(fan_me, [src, A, B], [(0, 1, 2)])
        w_ = 0.0009; dl = Vector((0, w_, 0))
        set_mesh(hit_me, [A - dl, B - dl, B + dl, A + dl], [(0, 1, 2, 3)])
    # the rim is traced in light at the end of the sweep, then stays as the frame the net is woven on
    k = (t_ - (F_LASER + 14)) / 10
    rim.hide_render = k <= 0
    rim.data.bevel_factor_end = max(0.0, min(1.0, k)); rim.data.bevel_factor_mapping_end = "SPLINE"

# ---------------------------------------------------------------- electricity and the net
elm, elem = emit_mat("Spark", AI_BLUE, 16)
ARCS = [curve_obj(f"Arc{i}", 28, elm, 0.00045) for i in range(7)]
RIMPTS = [(HX + HR * math.cos(2 * math.pi * i / 7 + 0.4), HY + HR * math.sin(2 * math.pi * i / 7 + 0.4)) for i in range(7)]
def jag(p0, p1, n, amp, seed, bow=0.0):
    rr = random.Random(seed); pts = []
    for i in range(n):
        t = i / (n - 1); p = p0.lerp(p1, t)
        p.z += bow * math.sin(math.pi * t)                     # arcs bow up over the floor
        if 0 < i < n - 1:
            p += Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-0.5, 1))) * amp * math.sin(math.pi * t)
        pts.append(p)
    return pts
def set_curve(ob_, pts):
    for p_, v in zip(ob_.data.splines[0].points, pts): p_.co = (v.x, v.y, v.z, 1)

STEP = 0.0115; STR = []
for d_ in (1, -1):                                             # a diamond net, clipped to the hole
    for k in range(-12, 13):
        c = k * STEP * math.sqrt(2)
        # line x*d_ + y = c through the hole frame; intersect with the circle
        nx, ny = d_ / math.sqrt(2), 1 / math.sqrt(2); off = c / math.sqrt(2)
        if abs(off) >= HR: continue
        h = math.sqrt(HR * HR - off * off); px, py = HX + nx * off, HY + ny * off; tx, ty = -ny, nx
        STR.append((Vector((px - tx * h, py - ty * h, FLOOR + 0.0009)), Vector((px + tx * h, py + ty * h, FLOOR + 0.0009))))
STR.sort(key=lambda ab: (ab[0] + ab[1]).length)
netm, netem = emit_mat("Net", (0.70, 0.85, 1.0), 9)
NETS = [curve_obj(f"Net{i}", 16, netm, 0.00035) for i in range(len(STR))]
skin_me = bpy.data.meshes.new("Skin"); b_ = _bmx.new(); _bmx.ops.create_circle(b_, cap_ends=True, segments=96, radius=HR); b_.to_mesh(skin_me); b_.free()
skin = bpy.data.objects.new("Skin", skin_me); scene.collection.objects.link(skin); skin.location = (HX, HY, FLOOR + 0.0005)
skm, skem = emit_mat("SkinM", (0.55, 0.74, 1.0), 1.6, alpha=0.0); skin_me.materials.append(skm)
skin_mix = [n_ for n_ in skm.node_tree.nodes if n_.type == "MIX_SHADER"][0]

def place_net(t_):
    fi = int(t_)
    head = dev_pt(TOP_Z)
    for i, ob_ in enumerate(ARCS):                              # cap -> rim, flickering
        on = F_NET <= t_ < F_NET + 18 and (fi + i) % 5 != 0
        ob_.hide_render = not on
        if on:
            rx, ry = RIMPTS[i]; set_curve(ob_, jag(head, Vector((rx, ry, FLOOR + 0.001)), 28, 0.010, fi * 13 + i, bow=0.05))
    for i, (ob_, (a, b)) in enumerate(zip(NETS, STR)):         # each strand jumps in as a spark, then settles straight
        t0 = F_NET + 4 + i * 20 / len(STR); k = t_ - t0
        ob_.hide_render = k < 0
        if k >= 0:
            amp = 0.004 * max(0.0, 1 - k / 6); set_curve(ob_, jag(a, b, 16, amp, fi * 7 + i))
            ob_.data.bevel_factor_end = min(1.0, k / 3); ob_.data.bevel_factor_mapping_end = "SPLINE"
    # the skin: the hole is mended
    skin_mix.inputs["Fac"].default_value = 0.55 * sstep((t_ - (F_AI - 12)) / 10)
    skin.hide_render = t_ < F_AI - 12
    netem.inputs["Strength"].default_value = (9 + 10 * max(0.0, 1 - abs(t_ - (F_AI - 4)) / 6)) * EXPK   # a pulse as it closes

# ---------------------------------------------------------------- "AI" written in light on the net
cu_ = bpy.data.curves.new("AIText", "FONT"); cu_.body = "AI"
cu_.font = bpy.data.fonts.load("/Library/Fonts/Montserrat-Black.ttf") if os.path.exists("/Library/Fonts/Montserrat-Black.ttf") else cu_.font
cu_.align_x = "CENTER"; cu_.align_y = "CENTER"; cu_.size = HR * 1.05
ai_t = bpy.data.objects.new("AIText", cu_); scene.collection.objects.link(ai_t); ai_t.location = (HX, HY, FLOOR + 0.0014)
aim = bpy.data.materials.new("AIM"); aim.use_nodes = True; an2 = aim.node_tree.nodes
for x_ in list(an2):
    if x_.type != "OUTPUT_MATERIAL": an2.remove(x_)
o2 = [x_ for x_ in an2 if x_.type == "OUTPUT_MATERIAL"][0]; L2 = aim.node_tree.links.new
tc2 = an2.new("ShaderNodeTexCoord"); sx2 = an2.new("ShaderNodeSeparateXYZ"); L2(tc2.outputs["Object"], sx2.inputs[0])
rev = an2.new("ShaderNodeMath"); rev.operation = "LESS_THAN"; L2(sx2.outputs["X"], rev.inputs[0])   # written left to right
edge2 = an2.new("ShaderNodeMath"); edge2.operation = "SUBTRACT"; L2(sx2.outputs["X"], edge2.inputs[1])
hot = an2.new("ShaderNodeMapRange"); L2(edge2.outputs[0], hot.inputs["Value"]); hot.inputs["From Min"].default_value = 0.0
hot.inputs["From Max"].default_value = 0.012; hot.inputs["To Min"].default_value = 60 * EXPK; hot.inputs["To Max"].default_value = 12 * EXPK
em2 = an2.new("ShaderNodeEmission"); em2.inputs["Color"].default_value = (0.86, 0.93, 1.0, 1); L2(hot.outputs["Result"], em2.inputs["Strength"])
tr2 = an2.new("ShaderNodeBsdfTransparent"); mx2 = an2.new("ShaderNodeMixShader"); L2(rev.outputs[0], mx2.inputs["Fac"])
L2(tr2.outputs[0], mx2.inputs[1]); L2(em2.outputs[0], mx2.inputs[2]); L2(mx2.outputs[0], o2.inputs["Surface"])
cu_.materials.append(aim)
X_FROM, X_TO = -HR * 1.1, HR * 1.1
def place_ai(t_):
    k = sstep((t_ - F_AI) / 14); xw = X_FROM + (X_TO - X_FROM) * k
    rev.inputs[1].default_value = xw; edge2.inputs[0].default_value = xw
    ai_t.hide_render = t_ < F_AI

# --fxpart air | light: the glass bubbles and the light are rendered apart, so the comp can colour the light for the
# white stage (deep blue lines) and the dark pit (bright) without touching the bubbles
PART = arg("--fxpart", "all")
LIGHTS = [fan, hit, rim, skin, ai_t] + ARCS + NETS
def _on_fx(sc, *_):
    t_ = sc.frame_current + sc.frame_subframe
    if PART != "light": place_bubbles(t_)
    else:
        for b_ in BUB: b_[0].hide_render = True
    if PART != "air": place_laser(t_); place_net(t_); place_ai(t_)
    else:
        for o_ in LIGHTS: o_.hide_render = True
bpy.app.handlers.frame_change_pre.append(_on_fx)
print("FX", len(BUB), "bubbles,", len(STR), "net strands")

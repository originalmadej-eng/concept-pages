"""BOOSTER beat — strawberry shortcake (user 2026-10-21 「케이크 같은 걸」→「실제 케이크처럼」→「제대로 된 딸기 생크림케이크로」, 10/22 「다듬고 글자 넣어서 진행」).
Official copy "Boost Active Absorption / Glow care from within" (2X GLOW BOOSTING -> "Glow Boosting", no "2X"); the picture is a
metaphor, no claim is drawn, no numbers. A Japanese shortcake with a slice cut out: rosettes with whole strawberries on top, halved
strawberries in two cream layers on the cut. It starts tired (dry pale sponge, dull berries). The device (orange BOOSTER LED) comes
down head first and rests on the top; orange rings run out from the head over the top and down the cut; the syrup soaks the sponge
from the top down; the berries turn glossy, the cream silky. "Glow Boosting" grows in behind the cake in MC's face (Nunito Black)
and lights up from inside; the device lifts away (MC opens with it falling in). Skin block: shot_booster_v0skin.py; cakes v1/v2/v3a/v3b.

  Blender --factory-startup -b -P tools/shot_booster.py -- --out render/booster/ [--still 12,40,84] [--res 960x540]
  full beat: zsh tools/render_booster.sh v1
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d
OUTDIR = arg("--out", "render/booster/"); FR = int(arg("--frames", "132"))
sys.argv = [sys.argv[0], "--", "--bg", "white", "--led", "booster", "--color", "pink", "--transparent", "1",
            "--res", arg("--res", "960x540"), "--samples", arg("--samples", "48"), "--no_render", "1"]
_mine = (OUTDIR, FR, argv)
exec(compile(open(os.path.join(HERE, "render_device.py")).read(), "render_device.py", "exec"))
OUTDIR, FR, argv = _mine
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d
scene = bpy.context.scene; scene.frame_start, scene.frame_end = 1, FR; scene.render.fps = 24
def sstep(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

F_TOUCH, F_WAVE, F_HEAL0, F_HEAL1, F_LIFT = 24, 26, 34, 72, 96

# ---------------------------------------------------------------- the cake (user 2026-10-21: "케이크 같은 걸 보여주는 건 어때?")
# skin as a layer cake, like the pudding/cloud/water of the other beats: sponge and cream in layers under a glaze, a slice
# cut out so the layers show. Dry first (pale porous sponge, dull cracked glaze); the "essence" is a soaking syrup —
# what a pastry cook brushes on to moisten a sponge — and it soaks in as the rings pass (Boost Active Absorption);
# then the sponge is moist, the cream silky, the glaze a mirror, and the layers glow warm from inside (Glow care from within).
RC, TOP = 0.105, 0.072
BANDS = [(0.000, "sp"), (0.020, "cr"), (0.027, "sp"), (0.047, "cr"), (0.054, "sp"), (0.066, "gl")]
CT = Vector((0, 0, TOP))                  # where the head rests
BW, BD = 2 * RC, 2 * RC
VT = {}
def anim_value(name, keys, linear=False): VT[name] = (keys, linear)
def vnode(nt, name):
    n_ = nt.nodes.new("ShaderNodeValue"); n_.name = name; keys, lin = VT[name]
    for f_, v_ in keys:
        n_.outputs[0].default_value = v_; n_.outputs[0].keyframe_insert("default_value", frame=f_)
    if lin and nt.animation_data and nt.animation_data.action:
        for fc_ in nt.animation_data.action.fcurves:
            if name in fc_.data_path:
                for kp in fc_.keyframe_points: kp.interpolation = "LINEAR"
    return n_.outputs[0]
anim_value("T", [(1, 1.0), (FR, float(FR))], linear=True)                       # frame clock for the rings
anim_value("Heal", [(1, 0.0), (F_HEAL0, 0.0), (F_HEAL1, 1.0), (FR, 1.0)])      # dull/dry -> smooth/dewy
anim_value("Glow", [(1, 0.0), (F_WAVE + 6, 0.0), (F_HEAL0 + 20, 1.0), (F_LIFT, 1.0), (FR, 0.75)])

def math_n(nt, op, a, b=None, clamp=False):
    n_ = nt.nodes.new("ShaderNodeMath"); n_.operation = op; n_.use_clamp = clamp
    for i_, v_ in enumerate((a, b)):
        if v_ is None: continue
        if isinstance(v_, (int, float)): n_.inputs[i_].default_value = v_
        else: nt.links.new(v_, n_.inputs[i_])
    return n_.outputs[0]
def mix_rgb(nt, fac, a, b):
    n_ = nt.nodes.new("ShaderNodeMix"); n_.data_type = "RGBA"; n_.clamp_factor = True
    for sock, v_ in (("A", a), ("B", b)):
        if isinstance(v_, tuple): n_.inputs[sock].default_value = (*v_, 1)
        else: nt.links.new(v_, n_.inputs[sock])
    nt.links.new(fac, n_.inputs["Factor"]); return n_.outputs["Result"]

def rings(nt, pos):
    """orange rings running out from the head: distance from the contact point vs time, three of them"""
    vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = "DISTANCE"; vm.inputs[1].default_value = CT
    nt.links.new(pos, vm.inputs[0]); d = vm.outputs["Value"]
    t = vnode(nt, "T"); acc = None
    for k in range(3):
        t0 = F_WAVE + k * 9
        r = math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", t, t0), float(arg("--wave_v", "0.0036")))
        x = math_n(nt, "DIVIDE", math_n(nt, "SUBTRACT", d, r), 0.0022)
        band = math_n(nt, "EXPONENT", math_n(nt, "MULTIPLY", math_n(nt, "MULTIPLY", x, x), -1.0))
        alive = math_n(nt, "MULTIPLY", math_n(nt, "GREATER_THAN", r, 0.0), math_n(nt, "SUBTRACT", 1.0, math_n(nt, "DIVIDE", r, 0.17), clamp=True))
        b = math_n(nt, "MULTIPLY", band, alive)
        acc = b if acc is None else math_n(nt, "ADD", acc, b)
    return acc

# v3 (user 2026-10-21 "그래픽이 저조해, 제대로 된 딸기 생크림케이크로"): references on Unsplash 10/21 — a strawberry cream
# cake piled with whole and halved strawberries (green tops showing) over rough-whipped cream; a fraisier, whose cut shows
# halved strawberries in the cream: red rim, pale streaked flesh, white heart. Real geometry now: modelled strawberries
# (seeds in dimples, glaze shine, a sliced face), the berries in the cream are halves sitting exactly on the cut planes,
# piped rosettes round the rim. The soak shows on the cut: the sponge turns moist from the top layer down.
TOP = 0.077; CT = Vector((0, 0, TOP))
anim_value("Soak", [(1, -0.01), (F_WAVE + 4, -0.01), (F_HEAL1 + 6, TOP + 0.01), (FR, TOP + 0.01)])   # depth the syrup has reached
import random
rnd = random.Random(7)

def principled(name):
    m_ = bpy.data.materials.new(name); m_.use_nodes = True; nt_ = m_.node_tree; nt_.animation_data_create()
    return m_, nt_, nt_.nodes["Principled BSDF"]
def lerp(nt, a_, b_, k_): return math_n(nt, "ADD", a_, math_n(nt, "MULTIPLY", k_, b_ - a_))
def rgb(nt, c):
    n_ = nt.nodes.new("ShaderNodeRGB"); n_.outputs[0].default_value = (*c, 1); return n_.outputs[0]
def dull(nt, col_out, heal_, sat=0.55, val=0.9):
    hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = sat; hs.inputs["Value"].default_value = val
    nt.links.new(col_out, hs.inputs["Color"]); return mix_rgb(nt, heal_, hs.outputs["Color"], col_out)
def add_rings(nt, p_, extra=None, k=4.0):
    geo_ = nt.nodes.new("ShaderNodeNewGeometry"); ring = rings(nt, geo_.outputs["Position"])
    em = math_n(nt, "MULTIPLY", ring, float(arg("--ring_k", str(k))))
    if extra is not None: em = math_n(nt, "ADD", em, extra)
    p_.inputs["Emission Color"].default_value = (1.0, 0.42, 0.15, 1)
    nt.links.new(math_n(nt, "MULTIPLY", em, EXPK * 0.5), p_.inputs["Emission Strength"])
def bump(nt, p_, h, strength, dist, invert=False, prev=None):
    bz = nt.nodes.new("ShaderNodeBump"); bz.invert = invert; bz.inputs["Distance"].default_value = dist
    if isinstance(strength, (int, float)): bz.inputs["Strength"].default_value = strength
    else: nt.links.new(strength, bz.inputs["Strength"])
    nt.links.new(h, bz.inputs["Height"])
    if prev is not None: nt.links.new(prev, bz.inputs["Normal"])
    if p_ is not None: nt.links.new(bz.outputs["Normal"], p_.inputs["Normal"])
    return bz.outputs["Normal"]
def noise(nt, vec, scale, detail=4, rough=0.5, mapping=None):
    n_ = nt.nodes.new("ShaderNodeTexNoise"); n_.inputs["Scale"].default_value = scale; n_.inputs["Detail"].default_value = detail
    n_.inputs["Roughness"].default_value = rough
    if mapping:
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = mapping
        nt.links.new(vec, mp.inputs["Vector"]); vec = mp.outputs["Vector"]
    nt.links.new(vec, n_.inputs["Vector"]); return n_.outputs["Fac"]

def cream_material(name, strokes=False):
    m_, nt_, p_ = principled(name); h_ = vnode(nt_, "Heal"); tc_ = nt_.nodes.new("ShaderNodeTexCoord")
    nt_.links.new(dull(nt_, rgb(nt_, (0.98, 0.96, 0.92)), h_, 0.6, 0.90), p_.inputs["Base Color"])
    p_.inputs["Subsurface Weight"].default_value = 0.8; p_.inputs["Subsurface Radius"].default_value = (0.006, 0.0055, 0.0045)
    p_.inputs["Subsurface Scale"].default_value = 0.6
    nt_.links.new(lerp(nt_, 0.62, 0.38, h_), p_.inputs["Roughness"]); p_.inputs["Specular IOR Level"].default_value = 0.4
    h1 = noise(nt_, tc_.outputs["Object"], 160, 8, 0.6)
    nb = bump(nt_, None, h1, 0.35, 0.0005)
    nb = bump(nt_, None, noise(nt_, tc_.outputs["Object"], 45, 4, 0.55), 0.35, 0.0009, prev=nb)
    if strokes:
        h2 = noise(nt_, tc_.outputs["Object"], 22, 3, 0.5, mapping=(1, 1, 16))
        nb = bump(nt_, None, h2, 0.35, 0.0008, prev=nb)
    nt_.links.new(nb, p_.inputs["Normal"])
    add_rings(nt_, p_, k=3.0)
    return m_

# ---- the cake body: sponge / cream / sponge / cream / sponge under a top coat; cream outside; cut faces show it all
m, nt, p = principled("Cake")
heal = vnode(nt, "Heal"); glow = vnode(nt, "Glow"); soak = vnode(nt, "Soak")
geo = nt.nodes.new("ShaderNodeNewGeometry"); sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sx.inputs[0])
X, Y, Z = sx.outputs["X"], sx.outputs["Y"], sx.outputs["Z"]
sn = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Normal"], sn.inputs[0])
tc = nt.nodes.new("ShaderNodeTexCoord")
rad = math_n(nt, "SQRT", math_n(nt, "ADD", math_n(nt, "MULTIPLY", X, X), math_n(nt, "MULTIPLY", Y, Y)))
ndot = math_n(nt, "DIVIDE", math_n(nt, "ADD", math_n(nt, "MULTIPLY", sn.outputs["X"], X), math_n(nt, "MULTIPLY", sn.outputs["Y"], Y)), math_n(nt, "MAXIMUM", rad, 1e-4))
outer = math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", ndot, 0.55), 6.0, clamp=True)
topf = math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", sn.outputs["Z"], 0.6), 4.0, clamp=True)
wob = math_n(nt, "MULTIPLY", noise(nt, tc.outputs["Object"], 40, 2), 0.0016)
Zw = math_n(nt, "ADD", Z, wob)
def band(z0, z1, e=2500.0):
    return math_n(nt, "MULTIPLY", math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", Zw, z0), e, clamp=True),
                  math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", z1, Zw), e, clamp=True))
coat_r = math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", rad, RC - 0.0045), 2500.0, clamp=True)      # the outer coat seen on the cut
creamy = math_n(nt, "MAXIMUM", math_n(nt, "MAXIMUM", math_n(nt, "ADD", band(0.0165, 0.0335), band(0.0480, 0.0650)),
                                      math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", Zw, 0.0725), 2500.0, clamp=True)),
                 math_n(nt, "MAXIMUM", coat_r, math_n(nt, "MAXIMUM", outer, topf)))
# sponge (genoise): golden fine crumb, little open pores, moist where the syrup has reached
soaked = math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", soak, math_n(nt, "SUBTRACT", TOP, Z)), 120.0, clamp=True)
warp = nt.nodes.new("ShaderNodeTexNoise"); warp.inputs["Scale"].default_value = 260; warp.inputs["Detail"].default_value = 3
nt.links.new(tc.outputs["Object"], warp.inputs["Vector"])
wv = nt.nodes.new("ShaderNodeVectorMath"); wv.operation = "MULTIPLY_ADD"; wv.inputs[1].default_value = (0.0012, 0.0012, 0.0012)
nt.links.new(warp.outputs["Color"], wv.inputs[0]); nt.links.new(tc.outputs["Object"], wv.inputs[2])
vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 420; nt.links.new(wv.outputs[0], vo.inputs["Vector"])
pit = math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", 0.30, vo.outputs["Distance"]), 9.0, clamp=True)
vo2 = nt.nodes.new("ShaderNodeTexVoronoi"); vo2.inputs["Scale"].default_value = 170; nt.links.new(wv.outputs[0], vo2.inputs["Vector"])
pit2 = math_n(nt, "MULTIPLY", math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", 0.20, vo2.outputs["Distance"]), 9.0, clamp=True), 0.8)
mott = noise(nt, tc.outputs["Object"], 70, 6, 0.65)
C_SP = (0.98, 0.82, 0.50); C_SP_DRY = (0.93, 0.87, 0.70)
sp_col = mix_rgb(nt, soaked, rgb(nt, C_SP_DRY), rgb(nt, C_SP))
sp_col = mix_rgb(nt, math_n(nt, "MULTIPLY", math_n(nt, "MAXIMUM", pit, pit2), 0.75), sp_col, rgb(nt, (0.66, 0.46, 0.20)))
sp_col = mix_rgb(nt, math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", mott, 0.42), 2.2, clamp=True), sp_col, rgb(nt, (1.0, 0.92, 0.66)))
cr_col = mix_rgb(nt, math_n(nt, "MULTIPLY", math_n(nt, "SUBTRACT", noise(nt, tc.outputs["Object"], 28, 4, 0.6), 0.45), 1.6, clamp=True), rgb(nt, (0.985, 0.97, 0.94)), rgb(nt, (0.93, 0.89, 0.82)))
cr_col = dull(nt, cr_col, heal, 0.6, 0.90)
nt.links.new(mix_rgb(nt, creamy, sp_col, cr_col), p.inputs["Base Color"])
p.inputs["Subsurface Weight"].default_value = 0.6; p.inputs["Subsurface Radius"].default_value = (0.006, 0.005, 0.004)
p.inputs["Subsurface Scale"].default_value = 0.6
spm = math_n(nt, "SUBTRACT", 1.0, creamy)
nt.links.new(math_n(nt, "ADD", math_n(nt, "MULTIPLY", spm, lerp(nt, 0.92, 0.62, soaked)), math_n(nt, "MULTIPLY", creamy, lerp(nt, 0.62, 0.38, heal))), p.inputs["Roughness"])
hgt = math_n(nt, "ADD", math_n(nt, "MULTIPLY", math_n(nt, "MULTIPLY", math_n(nt, "MAXIMUM", pit, pit2), spm), lerp(nt, 1.0, 0.6, soaked)),
             math_n(nt, "MULTIPLY", math_n(nt, "MULTIPLY", noise(nt, tc.outputs["Object"], 22, 3, 0.5, mapping=(1, 1, 16)), outer), 0.7))
nb = bump(nt, None, hgt, 1.0, 0.0009, invert=True)
nb = bump(nt, None, math_n(nt, "MULTIPLY", noise(nt, tc.outputs["Object"], 380, 8, 0.7), spm), 0.8, 0.0005, prev=nb)
nb = bump(nt, None, math_n(nt, "MULTIPLY", noise(nt, tc.outputs["Object"], 160, 8, 0.6), creamy), 0.4, 0.0005, prev=nb)
nb = bump(nt, None, math_n(nt, "MULTIPLY", noise(nt, tc.outputs["Object"], 45, 4, 0.55), creamy), 0.4, 0.0009, prev=nb)
nb = bump(nt, None, math_n(nt, "MULTIPLY", noise(nt, tc.outputs["Object"], 30, 4, 0.6, mapping=(0.25, 0.25, 9)), math_n(nt, "MULTIPLY", creamy, math_n(nt, "SUBTRACT", 1.0, outer))), 0.5, 0.0010, prev=nb)
nt.links.new(nb, p.inputs["Normal"])
add_rings(nt, p, math_n(nt, "MULTIPLY", math_n(nt, "MULTIPLY", glow, spm), float(arg("--glow_k", "0.25"))))

RC = 0.105
WEDGE = math.radians(float(arg("--wedge", "90"))); A_MID = -math.pi / 2
a0, a1 = A_MID + WEDGE / 2, A_MID - WEDGE / 2 + 2 * math.pi
NSEG = 192
b_ = bmesh.new()
ring_b = [b_.verts.new((0, 0, 0))] + [b_.verts.new((RC * math.cos(a0 + (a1 - a0) * i / NSEG), RC * math.sin(a0 + (a1 - a0) * i / NSEG), 0)) for i in range(NSEG + 1)]
bot = b_.faces.new(ring_b)
ext = bmesh.ops.extrude_face_region(b_, geom=[bot]); vs = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
bmesh.ops.translate(b_, vec=(0, 0, TOP), verts=vs)
bmesh.ops.recalc_face_normals(b_, faces=b_.faces[:])
bmesh.ops.triangulate(b_, faces=[f for f in b_.faces if len(f.verts) > 4])
me = bpy.data.meshes.new("Cake"); b_.to_mesh(me); b_.free()
cake = bpy.data.objects.new("Cake", me); scene.collection.objects.link(cake)
bv = cake.modifiers.new("Bevel", "BEVEL"); bv.width = 0.0045; bv.segments = 6; bv.limit_method = "ANGLE"
cake.modifiers.new("WN", "WEIGHTED_NORMAL")
me.materials.append(m)
for pg in me.polygons: pg.use_smooth = True

# ---- plate
mpl = bpy.data.materials.new("Plate"); mpl.use_nodes = True; ppl = mpl.node_tree.nodes["Principled BSDF"]
ppl.inputs["Base Color"].default_value = (0.95, 0.94, 0.93, 1); ppl.inputs["Roughness"].default_value = 0.22; ppl.inputs["Coat Weight"].default_value = 0.6
lathe("Plate", [(0.0, -0.006), (0.120, -0.006), (0.140, -0.002), (0.150, 0.004), (0.152, 0.006), (0.148, 0.006), (0.137, 0.0005), (0.0, 0.0)]).data.materials.append(mpl)

# ---- strawberries: skin (seeds in dimples, glazed), sliced face, calyx
def strawberry_skin():
    m_, nt_, p_ = principled("BerrySkin"); h_ = vnode(nt_, "Heal"); tc_ = nt_.nodes.new("ShaderNodeTexCoord")
    sz = nt_.nodes.new("ShaderNodeSeparateXYZ"); nt_.links.new(tc_.outputs["Object"], sz.inputs[0])
    tip = math_n(nt_, "MULTIPLY", math_n(nt_, "SUBTRACT", sz.outputs["Z"], 1.4), 0.8, clamp=True)
    sh = math_n(nt_, "MULTIPLY", math_n(nt_, "SUBTRACT", 0.30, sz.outputs["Z"]), 4.0, clamp=True)          # pale near the hull
    c = mix_rgb(nt_, tip, rgb(nt_, (0.62, 0.02, 0.035)), rgb(nt_, (0.80, 0.06, 0.05)))
    c = mix_rgb(nt_, math_n(nt_, "MULTIPLY", sh, 0.6), c, rgb(nt_, (0.95, 0.55, 0.45)))
    c = mix_rgb(nt_, math_n(nt_, "MULTIPLY", noise(nt_, tc_.outputs["Object"], 6, 4), 0.35), c, rgb(nt_, (0.45, 0.01, 0.03)))
    vs_ = nt_.nodes.new("ShaderNodeTexVoronoi"); vs_.inputs["Scale"].default_value = float(arg("--seed_scale", "4.2"))
    nt_.links.new(tc_.outputs["Object"], vs_.inputs["Vector"]); d_ = vs_.outputs["Distance"]
    seed = math_n(nt_, "SUBTRACT", 1.0, math_n(nt_, "DIVIDE", d_, 0.11), clamp=True)
    dimple = math_n(nt_, "SUBTRACT", 1.0, math_n(nt_, "DIVIDE", d_, 0.36), clamp=True)
    c = mix_rgb(nt_, math_n(nt_, "MULTIPLY", seed, 4.0, clamp=True), c, rgb(nt_, (0.86, 0.66, 0.22)))
    nt_.links.new(dull(nt_, c, h_, 0.72, 0.84), p_.inputs["Base Color"])
    h = math_n(nt_, "SUBTRACT", math_n(nt_, "MULTIPLY", seed, 0.9), math_n(nt_, "MULTIPLY", math_n(nt_, "POWER", dimple, 0.7), 0.8))
    nt_.links.new(bump(nt_, None, h, 0.9, 0.0005), p_.inputs["Normal"])
    p_.inputs["Subsurface Weight"].default_value = 0.5; p_.inputs["Subsurface Radius"].default_value = (0.004, 0.0008, 0.0008)
    p_.inputs["Subsurface Scale"].default_value = 0.6
    nt_.links.new(lerp(nt_, 0.40, 0.22, h_), p_.inputs["Roughness"])
    nt_.links.new(lerp(nt_, 0.0, 1.0, h_), p_.inputs["Coat Weight"]); p_.inputs["Coat Roughness"].default_value = 0.03
    add_rings(nt_, p_, k=1.5)
    return m_
def strawberry_cut():
    m_, nt_, p_ = principled("BerryCut"); h_ = vnode(nt_, "Heal"); tc_ = nt_.nodes.new("ShaderNodeTexCoord")
    sz = nt_.nodes.new("ShaderNodeSeparateXYZ"); nt_.links.new(tc_.outputs["Object"], sz.inputs[0])
    Yc, Zc = sz.outputs["Y"], sz.outputs["Z"]
    # the berry's radius at this height (profile, roughly), so the rim/flesh/heart follow the outline
    Rz = math_n(nt_, "ADD", math_n(nt_, "MULTIPLY", math_n(nt_, "SINE", math_n(nt_, "MULTIPLY", math_n(nt_, "ADD", Zc, 0.10), 1.15)), 0.98), 0.02)
    rn = math_n(nt_, "DIVIDE", math_n(nt_, "ABSOLUTE", Yc), math_n(nt_, "MAXIMUM", Rz, 0.05))
    heart = math_n(nt_, "MULTIPLY", math_n(nt_, "SUBTRACT", 0.42, rn), 2.6, clamp=True)
    heart = math_n(nt_, "MULTIPLY", heart, math_n(nt_, "MULTIPLY", math_n(nt_, "SUBTRACT", 2.1, Zc), 2.0, clamp=True))
    rim = math_n(nt_, "POWER", math_n(nt_, "MULTIPLY", math_n(nt_, "SUBTRACT", rn, 0.55), 2.3, clamp=True), 1.6)
    streak = noise(nt_, tc_.outputs["Object"], 9, 3, 0.5, mapping=(14, 1, 1.5))                       # pale streaks running out
    c = mix_rgb(nt_, math_n(nt_, "MULTIPLY", math_n(nt_, "SUBTRACT", streak, 0.5), 2.5, clamp=True), rgb(nt_, (0.88, 0.16, 0.17)), rgb(nt_, (0.98, 0.52, 0.50)))
    c = mix_rgb(nt_, rim, c, rgb(nt_, (0.70, 0.02, 0.05)))
    c = mix_rgb(nt_, math_n(nt_, "MULTIPLY", heart, 0.9), c, rgb(nt_, (1.0, 0.82, 0.78)))
    nt_.links.new(dull(nt_, c, h_, 0.75, 0.88), p_.inputs["Base Color"])
    p_.inputs["Subsurface Weight"].default_value = 0.6; p_.inputs["Subsurface Radius"].default_value = (0.004, 0.0015, 0.0015)
    p_.inputs["Subsurface Scale"].default_value = 0.6
    nt_.links.new(lerp(nt_, 0.45, 0.12, h_), p_.inputs["Roughness"]); nt_.links.new(lerp(nt_, 0.0, 0.6, h_), p_.inputs["Coat Weight"])
    nt_.links.new(bump(nt_, None, noise(nt_, tc_.outputs["Object"], 30, 4), 0.25, 0.0003), p_.inputs["Normal"])
    return m_
MSKIN, MCUT = strawberry_skin(), strawberry_cut()
MLEAF = bpy.data.materials.new("Calyx"); MLEAF.use_nodes = True; pl_ = MLEAF.node_tree.nodes["Principled BSDF"]
pl_.inputs["Base Color"].default_value = (0.12, 0.32, 0.06, 1); pl_.inputs["Roughness"].default_value = 0.45
pl_.inputs["Subsurface Weight"].default_value = 0.3; pl_.inputs["Subsurface Radius"].default_value = (0.002, 0.004, 0.001)

BL = 2.6                                                   # length: real strawberries are ~1.3x as long as they are wide
BERRY_PROF = [(r, z * BL / 1.35) for r, z in [(0.0, 0.06), (0.28, 0.02), (0.60, 0.04), (0.85, 0.13), (0.98, 0.30), (0.99, 0.50),
              (0.90, 0.74), (0.72, 0.97), (0.48, 1.16), (0.22, 1.30), (0.0, 1.35)]]
def berry_mesh(half=False, seed_=0):
    r_ = random.Random(seed_)
    b2 = bmesh.new()
    vs_ = [b2.verts.new((r, 0, z)) for r, z in BERRY_PROF]
    es_ = [b2.edges.new((a_, b__)) for a_, b__ in zip(vs_, vs_[1:])]
    bmesh.ops.spin(b2, geom=vs_ + es_, axis=(0, 0, 1), cent=(0, 0, 0), steps=48, angle=2 * math.pi)
    bmesh.ops.remove_doubles(b2, verts=b2.verts, dist=1e-6)
    sub = bmesh.ops.subdivide_edges(b2, edges=b2.edges[:], cuts=1, use_grid_fill=True)
    ph = r_.uniform(0, 6.3)
    for v in b2.verts:                                       # a little lopsided, never a perfect lathe
        ang = math.atan2(v.co.y, v.co.x); k = 1 + 0.05 * math.sin(2 * ang + ph) + 0.03 * math.sin(3 * ang + ph * 2)
        v.co.x *= k; v.co.y *= k * r_.uniform(0.97, 1.0); v.co.z *= r_.uniform(0.93, 1.07) if False else 1.0
    if half:
        bmesh.ops.bisect_plane(b2, geom=b2.verts[:] + b2.edges[:] + b2.faces[:], plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
        res = bmesh.ops.edgeloop_fill(b2, edges=[e for e in b2.edges if e.is_boundary])
        for f in res["faces"]: f.material_index = 1
    bmesh.ops.recalc_face_normals(b2, faces=b2.faces[:])
    me_ = bpy.data.meshes.new("BerryH" if half else "Berry"); me_.materials.append(MSKIN); me_.materials.append(MCUT)
    b2.to_mesh(me_); b2.free()
    for pg in me_.polygons: pg.use_smooth = pg.material_index == 0
    if half:
        for pg in me_.polygons:
            if pg.material_index == 1: pg.use_smooth = False
    return me_
def calyx_mesh():
    b2 = bmesh.new(); NL = 7; c0 = b2.verts.new((0, 0, 0.02)); pts = []
    for i in range(NL):
        a_ = 2 * math.pi * i / NL; L = 0.75 + 0.15 * math.sin(i * 2.3)
        tipv = b2.verts.new((L * math.cos(a_), L * math.sin(a_), -0.10 - 0.08 * math.sin(i)))
        l_ = b2.verts.new((0.30 * math.cos(a_ - 0.32), 0.30 * math.sin(a_ - 0.32), 0.0))
        r_ = b2.verts.new((0.30 * math.cos(a_ + 0.32), 0.30 * math.sin(a_ + 0.32), 0.0))
        b2.faces.new((c0, l_, tipv, r_))
    st = b2.verts.new((0, 0, 0.25)); ring_ = [b2.verts.new((0.06 * math.cos(2 * math.pi * i / 6), 0.06 * math.sin(2 * math.pi * i / 6), 0.0)) for i in range(6)]
    for i in range(6): b2.faces.new((ring_[i], ring_[(i + 1) % 6], st))
    me_ = bpy.data.meshes.new("Calyx"); b2.to_mesh(me_); b2.free(); me_.materials.append(MLEAF)
    so = None
    return me_
CALYX = calyx_mesh()
def place(me_, loc, rot_m, s_, name="Berry"):
    ob = bpy.data.objects.new(name, me_); scene.collection.objects.link(ob)
    from mathutils import Matrix
    ob.matrix_world = Matrix.Translation(loc) @ rot_m.to_4x4() @ Matrix.Diagonal((s_, s_, s_, 1))
    if name == "Berry": ob.modifiers.new("Sub", "SUBSURF").levels = 1
    return ob
from mathutils import Matrix
def basis(xv, zv):
    xv = xv.normalized(); zv = (zv - xv * zv.dot(xv)).normalized(); yv = zv.cross(xv)
    return Matrix((xv, yv, zv)).transposed()

# halves inside the two cream layers, their sliced faces lying exactly on the two cut planes
HALF = [berry_mesh(True, i) for i in range(4)]
for (aa, side) in ((a0, -1), (a1, 1)):
    u = Vector((math.cos(aa), math.sin(aa), 0)); nrm = Vector((math.cos(aa + side * math.pi / 2), math.sin(aa + side * math.pi / 2), 0))
    for zc in (0.0250, 0.0565):
        for j, rr in enumerate((0.018, 0.041, 0.064, 0.087)):
            rr_ = rr + rnd.uniform(-0.0015, 0.0015); s_ = rnd.uniform(0.0068, 0.0074)
            ax = u * (1 if (j + (zc > 0.04)) % 2 else -1)                      # tips alternate in and out
            ax = (Matrix.Rotation(rnd.uniform(-0.35, 0.35), 3, nrm) @ ax).normalized()   # not a pattern: each sits a little askew
            ctr = u * rr_ + Vector((0, 0, zc + rnd.uniform(-0.0015, 0.0015))) + nrm * 0.00025 - ax * (0.5 * BL * s_)
            place(HALF[j % 4], ctr, basis(nrm, ax), s_)

# on top: piped rosettes round the rim, whole strawberries (some with their green tops) and a few halves just inside
def rosette_mesh():
    b2 = bmesh.new(); NL, NA, PTS = 30, 64, 9; rings_ = []
    for i in range(NL + 1):
        t = i / NL; z = t; r0 = (1 - t ** 1.5) * 0.66 + 0.02
        row = []
        for j in range(NA):
            th = 2 * math.pi * j / NA + t * 2.8
            rr_ = r0 * (1 + 0.30 * max(0.0, math.cos(PTS * (2 * math.pi * j / NA))) ** 0.6 - 0.12)
            row.append(b2.verts.new((rr_ * math.cos(th), rr_ * math.sin(th), z)))
        rings_.append(row)
    for i in range(NL):
        for j in range(NA):
            b2.faces.new((rings_[i][j], rings_[i][(j + 1) % NA], rings_[i + 1][(j + 1) % NA], rings_[i + 1][j]))
    b2.faces.new(list(reversed(rings_[0]))); bmesh.ops.pointmerge(b2, verts=rings_[-1], merge_co=Vector((0, 0, 1.0)))
    me_ = bpy.data.meshes.new("Rosette"); b2.to_mesh(me_); b2.free(); me_.materials.append(cream_material("RosetteCream"))
    for pg in me_.polygons: pg.use_smooth = True
    return me_
ROS = rosette_mesh(); WHOLE = [berry_mesh(False, 10 + i) for i in range(4)]
R_RIM = RC - 0.0135; N_ROS = int(arg("--ros_n", "12"))
span = 2 * math.pi - WEDGE - 0.10
# classic Japanese shortcake top: a ring of big piped rosettes, a whole strawberry (hull down, tip up) set into each
for i in range(N_ROS):
    a = a0 + 0.05 + span * (i + 0.5) / N_ROS
    out = Vector((math.cos(a), math.sin(a), 0))
    ob = bpy.data.objects.new("Rosette", ROS); scene.collection.objects.link(ob)
    s_ = float(arg("--ros_s", "0.0165")); ob.scale = (s_, s_, s_ * 1.05); ob.location = (R_RIM * math.cos(a), R_RIM * math.sin(a), TOP - 0.0015)
    ob.rotation_euler = (0, 0, rnd.uniform(0, 6.3))
    sb = rnd.uniform(0.0118, 0.0130)
    tilt = (Vector((0, 0, 1)) + out * rnd.uniform(0.10, 0.25) + out.cross(Vector((0, 0, 1))) * rnd.uniform(-0.12, 0.12)).normalized()
    pos = Vector((R_RIM * math.cos(a), R_RIM * math.sin(a), TOP + s_ * 0.40)) - out * 0.003
    place(WHOLE[i % 4], pos, basis(out.cross(tilt), tilt), sb)
# small shell border round the base
N_SH = int(arg("--shell_n", "56")); span_b = 2 * math.pi - WEDGE - 0.04
for i in range(N_SH):
    a = a0 + 0.02 + span_b * (i + 0.5) / N_SH
    ob = bpy.data.objects.new("Shell", ROS); scene.collection.objects.link(ob)
    ob.scale = (0.0068, 0.0068, 0.0052); ob.location = ((RC - 0.001) * math.cos(a), (RC - 0.001) * math.sin(a), 0.0)
    ob.rotation_euler = (0, 0, rnd.uniform(0, 6.3))

# ---------------------------------------------------------------- "Glow Boosting" (official 2X GLOW BOOSTING, the "2X" left out)
# sugar-glass letters standing behind the cake, split round the device like MC's jelly phrase. Clear at first, then they
# light up from inside (a warm volume glow) — "Glow care from within". They grow in gently from the device outwards.
F_TXT = int(arg("--f_txt", "60"))
TEXT = arg("--text", "Glow Boosting")
if TEXT:
    # Nunito Black, as MC's "Bounce Boosting", so the two "Boosting" lines rhyme (Fraunces was tried 10/22: its w and B are
    # overlapping outlines that Blender fills as holes). Same build as shot_pudding.py: one glyph per object.
    cu = bpy.data.curves.new("Phrase", "FONT"); cu.body = TEXT
    cu.font = bpy.data.fonts.load(arg("--font", "/Library/Fonts/Nunito-Black.ttf"))
    cu.size = 1.0; cu.align_x = "CENTER"; cu.resolution_u = 6
    cu.extrude = 0.035; cu.bevel_depth = 0.055; cu.bevel_resolution = 5; cu.offset = -0.045
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
    parts = [(min(v.co.x for fc in fs for v in fc.verts), max(v.co.x for fc in fs for v in fc.verts), fs) for fs in isl.values()]
    parts.sort(key=lambda p: p[1] - p[0], reverse=True); merged = []
    for q0, q1, fs in parts:
        for m_ in merged:
            if min(q1, m_[1]) - max(q0, m_[0]) > 0.6 * (q1 - q0): m_[2].extend(fs); break
        else: merged.append([q0, q1, list(fs)])
    letters = []
    for _, _, faces in merged:
        vs = {v for fc in faces for v in fc.verts}
        nb_ = bmesh.new(); vm = {v: nb_.verts.new(v.co) for v in vs}
        for fc in faces:
            try: nb_.faces.new([vm[v] for v in fc.verts])
            except ValueError: pass
        bmesh.ops.remove_doubles(nb_, verts=nb_.verts, dist=1e-6); bmesh.ops.recalc_face_normals(nb_, faces=nb_.faces[:])
        letters.append(nb_)
    bm.free(); tob.to_mesh_clear()
    allv = [v.co.x for lb in letters for v in lb.verts]
    S = float(arg("--text_w", "0.34")) / (max(allv) - min(allv))
    TY, TZ = float(arg("--text_y", "0.14")), float(arg("--text_z", "0.150"))
    # material: clear warm sugar glass; inside, an amber glow that comes up with "TGlow"
    anim_value("TGlow", [(1, 0.0), (F_TXT + 8, 0.0), (F_TXT + 30, 1.0), (FR, 1.0)])
    tm, tn, tp = principled("GlowLetters")
    tp.inputs["Base Color"].default_value = (1.0, 0.80, 0.64, 1)
    tp.inputs["Subsurface Weight"].default_value = 1.0; tp.inputs["Subsurface Radius"].default_value = (0.012, 0.007, 0.004)
    tp.inputs["Subsurface Scale"].default_value = 0.5; tp.inputs["Roughness"].default_value = 0.28
    tp.inputs["Coat Weight"].default_value = 1.0; tp.inputs["Coat Roughness"].default_value = 0.04
    tg = vnode(tn, "TGlow")
    lw = tn.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.5
    core = math_n(tn, "POWER", math_n(tn, "SUBTRACT", 1.0, lw.outputs["Facing"]), 1.6)       # brighter where the letter is thick
    tp.inputs["Emission Color"].default_value = (1.0, 0.33, 0.05, 1)
    tn.links.new(math_n(tn, "MULTIPLY", math_n(tn, "MULTIPLY", tg, core), float(arg("--text_glow", "2.5")) * EXPK * 0.5), tp.inputs["Emission Strength"])
    glyphs = []
    for nb_ in letters:
        cx = sum(v.co.x for v in nb_.verts) / len(nb_.verts); by = min(v.co.y for v in nb_.verts)
        for v in nb_.verts: v.co = Vector(((v.co.x - cx) * S, (v.co.y - by) * S, v.co.z * S))
        for f_ in nb_.faces: f_.material_index = 0
        gm = bpy.data.meshes.new("Glyph"); nb_.to_mesh(gm); nb_.free(); gm.shade_smooth(); gm.materials.append(tm)
        go = bpy.data.objects.new("Glyph", gm); scene.collection.objects.link(go)
        go.location = (cx * S, TY, TZ + by * S); go.rotation_euler = (math.radians(90), 0, 0)
        rm = go.modifiers.new("Remesh", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = 0.0004; rm.use_smooth_shade = True
        glyphs.append(go)
    bpy.data.objects.remove(tob)
    bpy.context.view_layer.update(); dg_ = bpy.context.evaluated_depsgraph_get()
    for g in glyphs:
        ev = g.evaluated_get(dg_).data
        w0 = max(v.co.x for v in g.data.vertices) - min(v.co.x for v in g.data.vertices)
        w1 = max(v.co.x for v in ev.vertices) - min(v.co.x for v in ev.vertices)
        if w1 < 0.9 * w0:
            g.modifiers.remove(g.modifiers["Remesh"]); g.data.shade_smooth(); g.data.set_sharp_from_angle(angle=math.radians(40))
    glyphs.sort(key=lambda g: g.location.x)
    ext = [(g.location.x + min(v.co.x for v in g.data.vertices), g.location.x + max(v.co.x for v in g.data.vertices)) for g in glyphs]
    i_gap = max(range(1, len(glyphs)), key=lambda i: ext[i][0] - ext[i - 1][1])
    GAP = float(arg("--text_gap", "0.085")); mid = (ext[i_gap][0] + ext[i_gap - 1][1]) / 2; extra = GAP - (ext[i_gap][0] - ext[i_gap - 1][1])
    for i, g in enumerate(glyphs): g.location.x += -mid + (extra / 2 if i >= i_gap else -extra / 2)
    half = max(abs(g.location.x) for g in glyphs)
    for g in glyphs:
        d = F_TXT + round(6 * abs(g.location.x) / half); z0 = g.location.z
        for f in range(1, FR + 1):
            k = sstep((f - d) / 10)
            s_ = max(0.001, k); g.scale = (s_, s_, s_); g.location.z = z0 - (1 - k) * 0.012
            g.keyframe_insert("scale", frame=f); g.keyframe_insert("location", frame=f)

# ---- food light: a big soft back light so the cream glows at its edges and the glaze on the berries sparkles
bl = bpy.data.lights.new("BackSoft", "AREA"); bl.shape = "RECTANGLE"; bl.size, bl.size_y = 0.5, 0.35
bl.energy = float(arg("--back", "40")); bl.color = (1.0, 0.96, 0.92)
blo = bpy.data.objects.new("BackSoft", bl); scene.collection.objects.link(blo); blo.location = (-0.22, 0.38, 0.38)
blo.rotation_euler = (Vector((0, 0, 0.04)) - blo.location).to_track_quat("-Z", "Y").to_euler()

# ---------------------------------------------------------------- device: comes down head first, rests on the surface, lifts away
dev_top = max((ob.matrix_world @ Vector(c)).z for ob in device.children_recursive if ob.type == "MESH" for c in ob.bound_box)
print("device height", dev_top)
for f in range(1, FR + 1):
    kd = sstep((f - 1) / (F_TOUCH - 1)) ** 0.7
    ku = sstep((f - F_LIFT) / 22) ** 1.6
    z_rest = TOP + dev_top + 0.0003                     # upside down: the head touches the top
    z = z_rest + (1 - kd) * 0.30 + ku * 0.40
    device.rotation_euler = (math.pi, 0, math.radians(float(arg("--yaw", "162"))))   # upside down: +180 keeps the screen to camera
    device.location = (0, 0, z)
    device.keyframe_insert("location", frame=f); device.keyframe_insert("rotation_euler", frame=f)

# ---------------------------------------------------------------- camera (MC's) and render
cam = scene.camera
for c in list(cam.constraints): cam.constraints.remove(c)
cam.data.lens = float(arg("--lens", "50")); cam.data.dof.use_dof = False
cam.location = (0.0, -float(arg("--camd", "0.80")), float(arg("--camz", "0.31")))
look = Vector((0, 0, float(arg("--lookz", "0.125")))); cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = 0.4
scene.render.image_settings.color_mode = "RGBA"
if arg("--still", ""):
    for f in [int(x) for x in arg("--still", "1").split(",")]:
        scene.frame_set(f); scene.render.filepath = os.path.join(ROOT, OUTDIR, f"f{f:04d}.png"); bpy.ops.render.render(write_still=True)
else:
    scene.render.filepath = os.path.join(ROOT, OUTDIR, "f"); bpy.ops.render.render(animation=True)
print("WROTE booster", OUTDIR)

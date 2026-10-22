"""MASK beat, device pass (v2: it plops into the water) (user 2026-10-15: "마스크는 화면이 물에 잠기면서 기기가 물속에 있는"). Official MASK copy:
"for better synergy / *Use only with sheet masks" — water is the mood (moisture), no claim is drawn.
The device (purple MASK light) drops in from above and plops into the water (drawn in comp_mask.py), sinks,
then hovers, turning slowly. Writes render/mask_path.json (screen path) for the comp. Transparent film.

  /Applications/Blender.app/Contents/MacOS/Blender -b -P tools/shot_mask.py -- --out render/mask/ [--still 1,60]
"""
import bpy, math, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d
OUTDIR = arg("--out", "render/mask/"); FR = int(arg("--frames", "120"))

sys.argv = [sys.argv[0], "--", "--bg", "white", "--led", "mask", "--color", "pink", "--transparent", "1",
            "--res", arg("--res", "960x540"), "--samples", arg("--samples", "32"), "--no_render", "1"]
_mine = (OUTDIR, FR, argv)
exec(compile(open(os.path.join(HERE, "render_device.py")).read(), "render_device.py", "exec"))
OUTDIR, FR, argv = _mine
def arg(n, d): return argv[argv.index(n) + 1] if n in argv else d

scene = bpy.context.scene; scene.frame_start, scene.frame_end = 1, FR; scene.render.fps = 24
def sstep(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

# v2 (user 2026-10-16: "퐁당 빠지는걸로"): drops in from above the frame, plops through the surface (Z_W, drawn in
# comp_mask.py at the same height), drag slows it under water, it sinks, rises a little and hovers.
Z_W, F_HIT = 0.169, 16                 # water level (world z) = screen y 0.30H for this camera; frame of the plop
Z0, ZHIT = 0.627, Z_W + 0.083          # centre high above the frame / centre when the base touches the water (1.2 m/s at entry: a real plop)
TILT_IN = float(arg("--tilt_in", "0"))      # 2026-10-16: a vertical end-first entry throws almost no crown even in slow motion
TAU, DEPTH = 5.5, 0.274                # drag time constant (speed matches the faster entry), how far it sinks
flt = bpy.data.objects.new("Float", None); scene.collection.objects.link(flt)
device.parent = flt; device.location = (0, 0, -0.083)
for f in range(1, FR + 1):
    if f <= F_HIT:
        s_ = (f - 1) / (F_HIT - 1); z = Z0 - (Z0 - ZHIT) * s_ * s_                 # gravity
        tilt = math.radians(4) * s_; roll = math.radians(TILT_IN) * s_      # --tilt_in: enter leaning sideways (a slap, not a dart)
    else:
        t = f - F_HIT
        z = ZHIT - DEPTH * (1 - math.exp(-t / TAU)) + 0.022 * sstep((t - 18) / 40)   # drag, then a little buoyancy
        z += 0.003 * math.sin(2 * math.pi * (t - 40) / 70) * sstep((t - 40) / 30)
        tilt = math.radians(4) + math.radians(6) * math.sin(2 * math.pi * t / 80) * sstep(t / 30)
        roll = math.radians(4) * math.sin(2 * math.pi * t / 64 + 1.0) * sstep(t / 30)
        roll += math.radians(TILT_IN) * (1 - sstep(t / 24))                # rights itself under water
    yaw = math.radians(-20) * sstep((f - F_HIT) / 70)
    flt.location = (0, 0, z); flt.rotation_euler = (tilt, roll, yaw)
    flt.keyframe_insert("location", frame=f); flt.keyframe_insert("rotation_euler", frame=f)
    PATH = globals().setdefault("PATH", {}); PATH[f] = z

cam = scene.camera
for c_ in list(cam.constraints): cam.constraints.remove(c_)
cam.data.lens = 60; cam.data.dof.use_dof = False
# v3 (user 2026-10-16): after the plop the camera goes down with the device, so the surface climbs the frame and
# leaves it at the top — the water fills the frame because we follow it under, not because the water rises
lz = 0.115                                                     # the camera's look height
for f in range(1, FR + 1):
    if f > F_HIT: lz += (min(0.115, PATH[f]) - lz) * 0.16      # holds until the device passes the middle, then goes down with it
    cam.location = (0.0, -0.80, lz + 0.075)
    cam.rotation_euler = (Vector((0, 0, lz)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)

scene.render.use_motion_blur = True; scene.render.motion_blur_shutter = 0.4
scene.render.image_settings.color_mode = "RGBA"
scene.render.use_persistent_data = True
# ---------------------------------------------------------------- real water (user 2026-10-16: "시뮬레이션 돌려줘")
# Mantaflow FLIP liquid: a tank of water up to Z_W seen through its side (the camera is outside the tank, so the
# surface line, the splash and later the view under water all come from the one render). A simple capsule stands in
# for the device as the collider. --water 1 --bake 1 bakes and then renders in the same run.
WATER = arg("--water", "0") == "1"
if WATER:
    import bmesh as _bm
    # frame-wide (the tank walls must sit outside the frame at the back face too), tall enough for the side-slap
    # splash (>15 cm above the surface in the test) and deep enough for the camera following the device down
    FX0, FX1, FY0, FY1, FZ0, FZ1 = -0.27, 0.27, -0.07, 0.07, -0.20, 0.42   # 2.2 mm cells at res 282
    if arg("--tight", "0") == "1":   # splash test: a small box round the entry so the cells are ~2 mm (a crown sheet is thinner than 3 mm)
        FX0, FX1, FY0, FY1, FZ0, FZ1 = -0.15, 0.15, -0.08, 0.08, -0.12, float(arg("--ftop", "0.32"))
    CACHE = os.path.join(ROOT, arg("--cache", "render/mask_fluid"))
    def box(name, x0, x1, y0, y1, z0, z1):
        me = bpy.data.meshes.new(name); b = _bm.new(); _bm.ops.create_cube(b, size=1.0); b.to_mesh(me); b.free()
        ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
        ob.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2); ob.scale = (x1 - x0, y1 - y0, z1 - z0)
        return ob
    dom = box("FluidDomain", FX0, FX1, FY0, FY1, FZ0, FZ1)
    # --from_cache 1: render an existing bake without Mantaflow — a fresh run cannot read the bake back (REPLAY
    # re-simulates and overwrites it, 2026-10-17), so the cached meshes are loaded frame by frame (load_water below)
    FROMC = arg("--from_cache", "0") == "1"
    if not FROMC:
        md = dom.modifiers.new("Fluid", "FLUID"); md.fluid_type = "DOMAIN"; ds = md.domain_settings
        ds.domain_type = "LIQUID"; ds.resolution_max = int(arg("--fres", "200")); ds.cache_directory = CACHE
        ds.cache_type = arg("--cache_type", "ALL"); ds.cache_frame_start = 1; ds.cache_frame_end = int(arg("--fend", str(FR)))
        ds.use_mesh = True; ds.mesh_scale = 2; ds.particle_radius = 1.6
        ds.mesh_particle_radius = float(arg("--mrad", "2.0"))       # smaller keeps thin sheets in the mesh
        ds.use_fractions = arg("--fractions", "0") == "1"
        ds.particle_band_width = float(arg("--band", "3.0"))          # narrow-band FLIP: the full run lost water steadily after the plop
        snd = arg("--snd", "1") == "1"   # 2026-10-16: res 282 + band 10 crashed allocating particles at frame 1; the spray never showed anyway
        ds.use_spray_particles = snd; ds.use_foam_particles = False; ds.use_bubble_particles = snd
        ds.sndparticle_potential_max_wavecrest = float(arg("--crest", "3.0")); ds.sndparticle_potential_max_trappedair = 5.0
        ds.sndparticle_potential_max_energy = float(arg("--energy", "5.0"))
        ds.timesteps_max = 8; ds.timesteps_min = 2; ds.cfl_condition = 3.0
        ds.use_collision_border_front = ds.use_collision_border_back = True
        # slow motion (2026-10-16): the first res-200 run at real time gave no splash — a 3.4 cm device at 1.2 m/s barely
        # throws water. Product-in-water ads are high-speed footage: same keyframes, fluid time slowed, so the entry is
        # ~3.4 m/s physically and the crown unfolds over many frames.
        ds.time_scale = float(arg("--tscale", "0.35"))
        water0 = box("WaterInit", FX0 + 0.004, FX1 - 0.004, FY0 + 0.004, FY1 - 0.004, FZ0 + 0.004, Z_W)
        mw_ = water0.modifiers.new("Fluid", "FLUID"); mw_.fluid_type = "FLOW"; fs = mw_.flow_settings
        fs.flow_type = "LIQUID"; fs.flow_behavior = "GEOMETRY"; fs.flow_source = "MESH"
        water0.hide_render = True; water0.display_type = "WIRE"
    scene.render.fps = 24
    # the collider: a capsule the size of the device, riding with it (also the reference for clearing the shell below)
    me = bpy.data.meshes.new("ColliderMesh"); b = _bm.new()
    _bm.ops.create_cone(b, cap_ends=True, segments=24, radius1=R, radius2=R, depth=0.165)
    _bm.ops.translate(b, verts=b.verts, vec=(0, 0, 0.0825)); b.to_mesh(me); b.free()
    col = bpy.data.objects.new("Collider", me); scene.collection.objects.link(col)
    col.parent = device; col.hide_render = True
    if not FROMC:
        mc = col.modifiers.new("Fluid", "FLUID"); mc.fluid_type = "EFFECTOR"; es = mc.effector_settings
        es.effector_type = "COLLISION"; es.subframes = 4; es.use_effector = True
    if arg("--bake", "0") == "1" and not FROMC:
        bpy.context.view_layer.objects.active = dom; dom.select_set(True)
        with bpy.context.temp_override(object=dom, active_object=dom):
            bpy.ops.fluid.bake_all()
        print("BAKED", CACHE)              # render in the same run: a fresh run does not pick up the baked cache
    # water material: clear, a little blue in depth; what it refracts is a bright stage (transmission rays only)
    wm = bpy.data.materials.new("Water"); wm.use_nodes = True; wp = wm.node_tree.nodes["Principled BSDF"]
    wp.inputs["Base Color"].default_value = (1, 1, 1, 1); wp.inputs["Transmission Weight"].default_value = 1.0
    wp.inputs["Roughness"].default_value = 0.02; wp.inputs["IOR"].default_value = 1.333
    va_ = wm.node_tree.nodes.new("ShaderNodeVolumeAbsorption"); va_.inputs["Color"].default_value = (0.70, 0.84, 1.0, 1)
    va_.inputs["Density"].default_value = float(arg("--wdens", "3.0"))
    wm.node_tree.links.new(va_.outputs[0], wm.node_tree.nodes["Material Output"].inputs["Volume"])
    # no bubbles stuck to the device (user 2026-10-17: "기기에 버블 붙는거 기괴해"): the liquid surface that wraps the
    # collider comes out lumpy at 2 mm cells and reads as a coat of bubbles. Within --shell of the capsule the water's
    # surface is made plain transparent, so the device is seen as if the water touched it cleanly.
    nt_ = wm.node_tree; N_ = nt_.nodes.new; L_ = nt_.links.new; SH = float(arg("--shell", "0.007"))
    tc_ = N_("ShaderNodeTexCoord"); tc_.object = col; sx_ = N_("ShaderNodeSeparateXYZ"); L_(tc_.outputs["Object"], sx_.inputs[0])
    flat_ = N_("ShaderNodeVectorMath"); flat_.operation = "MULTIPLY"; flat_.inputs[1].default_value = (1, 1, 0)
    L_(tc_.outputs["Object"], flat_.inputs[0]); rad_ = N_("ShaderNodeVectorMath"); rad_.operation = "LENGTH"; L_(flat_.outputs[0], rad_.inputs[0])
    def cmp_(op, a_, v_):
        n_ = N_("ShaderNodeMath"); n_.operation = op; L_(a_, n_.inputs[0]); n_.inputs[1].default_value = v_; return n_.outputs[0]
    def mul_(a_, b_):
        n_ = N_("ShaderNodeMath"); n_.operation = "MULTIPLY"; L_(a_, n_.inputs[0]); L_(b_, n_.inputs[1]); return n_.outputs[0]
    rlim_ = cmp_("LESS_THAN", rad_.outputs["Value"], R + SH)
    near_ = mul_(mul_(rlim_, cmp_("GREATER_THAN", sx_.outputs["Z"], -SH)), cmp_("LESS_THAN", sx_.outputs["Z"], 0.165 + SH))
    # not during the plop: then the water wrapping the device IS the splash and the air cavity — clear only once it has settled
    rn_ = rlim_.node; F_CLR = (F_HIT + 8, F_HIT + 14)
    rn_.inputs[1].default_value = 0.0; rn_.inputs[1].keyframe_insert("default_value", frame=F_CLR[0])
    rn_.inputs[1].default_value = R + SH; rn_.inputs[1].keyframe_insert("default_value", frame=F_CLR[1])
    # the tank's side walls: seen through the front face they showed as bright vertical bars at the frame edges
    geo_ = N_("ShaderNodeNewGeometry"); gx_ = N_("ShaderNodeSeparateXYZ"); L_(geo_.outputs["Position"], gx_.inputs[0])
    ax_ = N_("ShaderNodeMath"); ax_.operation = "ABSOLUTE"; L_(gx_.outputs["X"], ax_.inputs[0])
    wall_ = cmp_("GREATER_THAN", ax_.outputs[0], FX1 - 0.006)
    # and the front face (the "glass" we look through): its flat reflection of the stage light was a vertical bright
    # strip; plain transparent there reads like looking into a clear tank
    fw_ = N_("ShaderNodeMath"); fw_.operation = "MAXIMUM"; L_(wall_, fw_.inputs[0])
    L_(cmp_("LESS_THAN", gx_.outputs["Y"], FY0 + 0.006), fw_.inputs[1]); wall_ = fw_.outputs[0]
    bw_ = N_("ShaderNodeMath"); bw_.operation = "MAXIMUM"; L_(wall_, bw_.inputs[0])     # back face too: a pale block at the top-left corner
    L_(cmp_("GREATER_THAN", gx_.outputs["Y"], FY1 - 0.006), bw_.inputs[1]); wall_ = bw_.outputs[0]
    clr_ = N_("ShaderNodeMath"); clr_.operation = "MAXIMUM"; L_(near_, clr_.inputs[0]); L_(wall_, clr_.inputs[1]); near_ = clr_.outputs[0]
    tr_ = N_("ShaderNodeBsdfTransparent"); mx_ = N_("ShaderNodeMixShader"); L_(near_, mx_.inputs["Fac"])
    L_(wp.outputs[0], mx_.inputs[1]); L_(tr_.outputs[0], mx_.inputs[2]); L_(mx_.outputs[0], nt_.nodes["Material Output"].inputs["Surface"])
    dom.data.materials.append(wm)
    if FROMC:
        import gzip, struct
        import numpy as _np
        L_ = max(FX1 - FX0, FY1 - FY0, FZ1 - FZ0)              # the cache is scaled by the domain's LONGEST side on every axis
        dom.scale = (L_, L_, L_)
        _loaded = {"f": None}
        def load_water(f):
            if _loaded["f"] == f: return
            fn = os.path.join(CACHE, "mesh", f"fluid_mesh_{f:04d}.bobj.gz")
            if not os.path.exists(fn): return
            raw = gzip.open(fn).read(); o = 0
            nv = struct.unpack_from("i", raw, o)[0]; o += 4; co = _np.frombuffer(raw, _np.float32, nv * 3, o); o += nv * 12
            nn = struct.unpack_from("i", raw, o)[0]; o += 4 + nn * 12
            nt = struct.unpack_from("i", raw, o)[0]; o += 4; tri = _np.frombuffer(raw, _np.int32, nt * 3, o)
            m_ = bpy.data.meshes.new(f"Water{f}")
            m_.vertices.add(nv); m_.vertices.foreach_set("co", co)
            m_.loops.add(nt * 3); m_.loops.foreach_set("vertex_index", tri)
            m_.polygons.add(nt); m_.polygons.foreach_set("loop_start", _np.arange(0, nt * 3, 3, dtype=_np.int32))
            m_.update(calc_edges=True); m_.shade_smooth(); m_.materials.append(wm)
            old_ = dom.data; dom.data = m_; bpy.data.meshes.remove(old_); _loaded["f"] = f
        def _on_frame(sc, *_): load_water(sc.frame_current)
        bpy.app.handlers.frame_change_pre.append(_on_frame)
        scene.render.use_persistent_data = False
    wnt = scene.world.node_tree; bgn = wnt.nodes["Background"]; outw = wnt.nodes["World Output"]
    lpn = wnt.nodes.new("ShaderNodeLightPath"); wbg = wnt.nodes.new("ShaderNodeBackground")
    wbg.inputs["Color"].default_value = (0.96, 0.97, 0.99, 1); wbg.inputs["Strength"].default_value = 1.0 * EXPK
    mixw = wnt.nodes.new("ShaderNodeMixShader"); mxf = wnt.nodes.new("ShaderNodeMath"); mxf.operation = "MAXIMUM"
    wnt.links.new(lpn.outputs["Is Transmission Ray"], mxf.inputs[0]); wnt.links.new(lpn.outputs["Is Glossy Ray"], mxf.inputs[1])
    wnt.links.new(mxf.outputs[0], mixw.inputs["Fac"]); wnt.links.new(bgn.outputs[0], mixw.inputs[1]); wnt.links.new(wbg.outputs[0], mixw.inputs[2])
    wnt.links.new(mixw.outputs[0], outw.inputs["Surface"])
    scene.cycles.transmission_bounces = 32; scene.cycles.max_bounces = 32; scene.cycles.volume_bounces = 1   # 12 left black streaks in the splash
    # spray: the thin flying water becomes secondary particles, which render nothing unless given an instance
    drop = bpy.data.meshes.new("Drop"); b = _bm.new(); _bm.ops.create_icosphere(b, subdivisions=2, radius=1.0); b.to_mesh(drop); b.free()
    dob = bpy.data.objects.new("Drop", drop); scene.collection.objects.link(dob); dob.hide_render = True; dob.location = (5, 5, 5)
    drop.materials.append(wm)
    for psys in dom.particle_systems:
        if psys.settings.type in ("SPRAY",):
            st = psys.settings; st.render_type = "OBJECT"; st.instance_object = dob
            st.particle_size = float(arg("--drop", "0.0010")); st.size_random = 0.6
    if arg("--probe", "0") == "1":   # numbers before pictures: how high does any water get above the still surface?
        dg = bpy.context.evaluated_depsgraph_get()
        for f in range(F_HIT - 2, int(arg("--fend", str(FR))) + 1):
            scene.frame_set(f); dg.update(); ev = dom.evaluated_get(dg)
            zs = [ (ev.matrix_world @ v.co).z for v in ev.data.vertices ]
            top = max(zs) if zs else float("nan")
            nsp = 0; zsp = 0.0
            for psys in ev.particle_systems:
                if psys.settings.type == "SPRAY":
                    al = [p for p in psys.particles if p.alive_state == "ALIVE"]; nsp = len(al)
                    zsp = max([p.location.z for p in al], default=0.0)
            print(f"PROBE f{f} mesh_top={(top - Z_W) * 1000:.1f}mm verts={len(zs)} spray={nsp} spray_top={(zsp - Z_W) * 1000:.1f}mm")

if arg("--air", "0") == "1":     # the air-bubble pass only (tools/mask_air.py)
    exec(compile(open(os.path.join(HERE, "mask_air.py")).read(), "mask_air.py", "exec"))

if arg("--still", ""):
    for f in [int(x) for x in arg("--still", "1").split(",")]:
        scene.frame_set(f); scene.render.filepath = os.path.join(ROOT, OUTDIR, f"f{f:04d}.png"); bpy.ops.render.render(write_still=True)
else:
    scene.render.filepath = os.path.join(ROOT, OUTDIR, "f"); bpy.ops.render.render(animation=True)
import json
if WATER and FROMC: bpy.app.handlers.frame_change_pre.remove(_on_frame)
scene.frame_set(1)
def screen_xy(z):
    from bpy_extras.object_utils import world_to_camera_view
    co = world_to_camera_view(scene, cam, Vector((0, 0, z))); return co.x, 1 - co.y
wy, cen, bas = {}, {}, {}
for f in PATH:                                   # the camera moves now: project every frame
    scene.frame_set(f); bpy.context.view_layer.update()
    wy[f] = screen_xy(Z_W)[1]; cen[f] = screen_xy(PATH[f]); bas[f] = screen_xy(PATH[f] - 0.083)[1]
json.dump({"water_y": wy[F_HIT], "water_y_f": wy, "hit": F_HIT, "centre": cen, "base": bas},
          open(os.path.join(ROOT, "render", "mask_path.json"), "w"))
print("WROTE mask", OUTDIR)

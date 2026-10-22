"""Air bubbles for the MASK beat as real 3D air in water (user 2026-10-17: the drawn bubbles looked like a cartoon and
came up too late). Run inside tools/shot_mask.py with --air 1: the device is hidden, and only the bubbles render on a
transparent film — glass at the air/water IOR (1/1.333), so the rims catch the light above as silver and the middles
stay clear (film_transparent_glass). Layout from tools/air_letters.py (render/mask_air.json), held on a plane in front
of the camera so the word stays put while the camera settles. Positions are set per (sub)frame by a handler, so the
rising bubbles get real motion blur.
"""
import json
_air = json.load(open(os.path.join(ROOT, "render", "mask_air.json")))
AIR_F0 = int(arg("--air_f0", "30"))         # the camera is under by about here: the bubbles start rising at once
AIR_D = 0.70                                # plane distance, in front of the device (0.8)

for ob in device.children_recursive: ob.hide_render = True
scene.render.film_transparent = True; scene.cycles.film_transparent_glass = True
scene.cycles.transmission_bounces = 12; scene.cycles.glossy_bounces = 8; scene.cycles.max_bounces = 16

# a lit tank: bright above, blue below, so each bubble reflects a bright rim on top and a darker band below
w_ = bpy.data.worlds.new("AirWorld"); w_.use_nodes = True; scene.world = w_; wn = w_.node_tree.nodes; wl = w_.node_tree.links
tcw = wn.new("ShaderNodeTexCoord"); sxw = wn.new("ShaderNodeSeparateXYZ"); wl.new(tcw.outputs["Generated"], sxw.inputs[0])
mrw = wn.new("ShaderNodeMapRange"); mrw.inputs["From Min"].default_value = -1.0; wl.new(sxw.outputs["Z"], mrw.inputs["Value"])
crw = wn.new("ShaderNodeValToRGB"); wl.new(mrw.outputs["Result"], crw.inputs["Fac"])
# darker below than the comp's water: the rims of real air bubbles mirror the deep water and read as fine dark rings
crw.color_ramp.elements[0].color = (0.06, 0.13, 0.30, 1); crw.color_ramp.elements[1].position = 0.90
crw.color_ramp.elements[1].color = (1.6, 1.6, 1.6, 1); e_ = crw.color_ramp.elements.new(0.62); e_.color = (0.30, 0.45, 0.72, 1)
bgw = wn["Background"]; wl.new(crw.outputs["Color"], bgw.inputs["Color"]); bgw.inputs["Strength"].default_value = 1.4 * EXPK

am = bpy.data.materials.new("Air"); am.use_nodes = True; an = am.node_tree.nodes
for n_ in list(an):
    if n_.type != "OUTPUT_MATERIAL": an.remove(n_)
gl_ = an.new("ShaderNodeBsdfGlass"); gl_.inputs["IOR"].default_value = 1 / 1.333; gl_.inputs["Roughness"].default_value = 0.0
am.node_tree.links.new(gl_.outputs[0], [n_ for n_ in an if n_.type == "OUTPUT_MATERIAL"][0].inputs["Surface"])
import bmesh as _bm2
sph = bpy.data.meshes.new("Bubble"); b_ = _bm2.new(); _bm2.ops.create_icosphere(b_, subdivisions=3, radius=1.0); b_.to_mesh(sph); b_.free()
for p_ in sph.polygons: p_.use_smooth = True
sph.materials.append(am)

def _frame_at(d):
    tr, br, bl, tl = [v * (d / -v.z) for v in cam.data.view_frame(scene=scene)]
    return tl, tr - tl, bl - tl
TL, UX, VY = _frame_at(AIR_D); WID = UX.length
bubbles = []
for kind in ("letters", "fizz", "ambient"):
    for u, v, r, ph, lag in _air[kind]:
        ob_ = bpy.data.objects.new("Air", sph); scene.collection.objects.link(ob_); ob_.parent = cam
        bubbles.append((ob_, kind, u, v, r * WID, ph, lag))

def _place(t_):
    for ob_, kind, u, v, r, ph, lag in bubbles:
        s = 0.0; uu, vv = u, v
        if kind == "letters":                 # rise from below into the letter, quickly, staggered a little
            a = (t_ - AIR_F0 - lag * 6 - (v - 0.42) * 6) / 11
            if a > 0:
                e = 1 - (1 - min(a, 1)) ** 3
                vv = v + (1 - e) * (0.32 + 0.22 * lag)
                uu = u + (1 - e) * 0.012 * math.sin(ph * 3 + t_ * 0.55) + 0.0005 * math.sin(t_ * 0.21 + ph)
                vv += 0.0007 * math.sin(t_ * 0.19 + ph * 2)
                s = r * (0.6 + 0.4 * e) * (1 + 0.04 * math.sin(t_ * 0.33 + ph))
        elif kind == "fizz":                  # tiny ones leaving the letters once they have formed
            P = 34; age = (t_ - AIR_F0 - 14 - lag * P)
            if age >= 0:
                age %= P; vv = v - age * 0.011; uu = u + 0.004 * math.sin(age * 0.5 + ph); s = r
        else:                                 # ambient: rising through the whole frame
            if t_ >= AIR_F0 - 8:
                vv = 1.06 - ((t_ * 0.0055 + lag * 1.2) % 1.2); uu = u + 0.006 * math.sin(t_ * 0.12 + ph); s = r
        if s <= 0 or vv < -0.05:
            ob_.hide_render = True; continue
        ob_.hide_render = False
        ob_.location = TL + UX * uu + VY * vv
        ob_.scale = (s, s * 0.86, s)          # a little oblate, as rising bubbles are
        ob_.rotation_euler = (0, 0, 0.25 * math.sin(t_ * 0.4 + ph))

def _on_air(sc, *_): _place(sc.frame_current + sc.frame_subframe)
bpy.app.handlers.frame_change_pre.append(_on_air)
scene.frame_start = max(1, AIR_F0 - 8)
print("AIR bubbles", len(bubbles))

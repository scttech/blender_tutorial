"""build_props.py - Steps 12 and 15: model a kettlebell, a steel mace and a pull-up bar, low-poly, with simple materials.

    exec(open(".../build_props.py").read(), {})        # safe to re-run: it replaces "Kettlebell" and "Mace"

Both props are built standing on the floor with their origin at the centre of their base (z = 0), in metres.
Kettlebell  16 kg class: round body 20 cm across with a flat base, and a handle loop on top (grip bar along X)
Steel mace  1.1 m: a 33 mm shaft with a spherical head and a small end knob (shaft along Z)
Pull-up bar  a freestanding frame: two posts 1.6 m apart and a 32 mm bar at 2.30 m (bar along X), standing on two base plates
The handle bar and the shaft are where the hands go. Their positions are printed so the rig (build_prop_rig.py) can use them.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

# ---------------------------------------------------------------- dimensions (m)
KB_BODY_R, KB_FLAT = 0.100, 0.060         # body radius, radius of the flat base
KB_HANDLE_R, KB_HANDLE_W, KB_HANDLE_H = 0.0175, 0.070, 0.056   # handle tube radius, half-width and half-height of the loop (centre line)
MACE_SHAFT_R, MACE_SHAFT_L = 0.0165, 1.04
MACE_HEAD_R, MACE_KNOB_R = 0.070, 0.024
BAR_R, BAR_Z, POST_X, POST_R = 0.016, 2.30, 0.80, 0.030          # pull-up bar: radius, height, post spacing / 2, post radius

def fresh(name):
    old = bpy.data.objects.get(name)
    if old:
        m = old.data; bpy.data.objects.remove(old, do_unlink=True)
        if m and m.users == 0: bpy.data.meshes.remove(m)
    return bpy.data.collections.get("Props") or bpy.data.collections.new("Props")

def material(name, color, metallic, rough):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Metallic"].default_value = metallic; b.inputs["Roughness"].default_value = rough
    return m

def finish(name, bm, mat):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(mat)
    coll = bpy.data.collections["Props"]
    if coll.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(coll)
    coll.objects.link(ob); return ob

# ---------------------------------------------------------------- kettlebell
fresh("Kettlebell")
bpy.data.collections.get("Props") or bpy.data.collections.new("Props")
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=KB_BODY_R)
for v in bm.verts:                                       # body centre at z = radius, flat the bottom
    v.co.z += KB_BODY_R
    if v.co.z < 0.014: v.co.z = 0.014                     # flat base about 2 cm tall cut
# handle: a squashed torus standing in the XZ plane on top of the body
cz = 2 * KB_BODY_R + 0.012
seg_major, seg_minor = 20, 8
ring = []
for i in range(seg_major):
    a = 2 * math.pi * i / seg_major
    cx, cz_i = KB_HANDLE_W * math.cos(a), cz + KB_HANDLE_H * math.sin(a)
    # tube cross-section circle in the plane perpendicular to the loop's tangent
    tx, tz = -KB_HANDLE_W * math.sin(a), KB_HANDLE_H * math.cos(a); tl = math.hypot(tx, tz); tx, tz = tx / tl, tz / tl
    nx, nz = tz, -tx                                      # in-plane normal (outward)
    circle = []
    for j in range(seg_minor):
        b = 2 * math.pi * j / seg_minor
        r = KB_HANDLE_R
        circle.append(bm.verts.new((cx + r * math.cos(b) * nx, r * math.sin(b), cz_i + r * math.cos(b) * nz)))
    ring.append(circle)
for i in range(seg_major):
    for j in range(seg_minor):
        a, b = ring[i], ring[(i + 1) % seg_major]
        bm.faces.new((a[j], a[(j + 1) % seg_minor], b[(j + 1) % seg_minor], b[j]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
kb = finish("Kettlebell", bm, material("Mat_Kettlebell", (0.025, 0.025, 0.03), 0.85, 0.42))
top = max(v.co.z for v in kb.data.vertices)
GRIP_Z_KB = top - KB_HANDLE_R                                # centre line of the top of the handle
print(f"Kettlebell: height {top:.3f} m, handle top bar centre at z = {GRIP_Z_KB:.4f}, bar radius {KB_HANDLE_R*1000:.1f} mm, "
      f"verts {len(kb.data.vertices)}, tris {sum(len(p.vertices)-2 for p in kb.data.polygons)}")

# ---------------------------------------------------------------- steel mace
fresh("Mace")
bm = bmesh.new()
def cylinder(radius, z0, z1, seg=16):
    return bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=radius, radius2=radius, depth=z1 - z0,
                                 matrix=Matrix.Translation((0, 0, (z0 + z1) / 2)))
cylinder(MACE_SHAFT_R, 0.0, MACE_SHAFT_L)                    # the shaft
cylinder(MACE_KNOB_R, 0.0, 0.022)                            # end knob
bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=MACE_HEAD_R,
                          matrix=Matrix.Translation((0, 0, MACE_SHAFT_L + MACE_HEAD_R * 0.55)))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
mace = finish("Mace", bm, material("Mat_SteelMace", (0.62, 0.64, 0.68), 1.0, 0.28))
top = max(v.co.z for v in mace.data.vertices)
print(f"Mace: length {top:.3f} m, shaft radius {MACE_SHAFT_R*1000:.1f} mm, head radius {MACE_HEAD_R*1000:.0f} mm, "
      f"verts {len(mace.data.vertices)}, tris {sum(len(p.vertices)-2 for p in mace.data.polygons)}")


# ---------------------------------------------------------------- pull-up bar
fresh("PullupBar")
bm = bmesh.new()
def along_x(radius, x0, x1, z, seg=16):
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=radius, radius2=radius, depth=x1 - x0,
                          matrix=Matrix.Translation(((x0 + x1) / 2, 0, z)) @ Matrix.Rotation(math.radians(90), 4, 'Y'))
along_x(BAR_R, -POST_X, POST_X, BAR_Z)                                          # the bar
for sx in (-1, 1):
    bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=POST_R, radius2=POST_R, depth=BAR_Z + 0.04,
                          matrix=Matrix.Translation((sx * POST_X, 0, (BAR_Z + 0.04) / 2)))        # a post, a little taller than the bar
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((sx * POST_X, 0, 0.015)) @ Matrix.Diagonal((0.16, 0.70, 0.03, 1.0)))   # base plate
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bar = finish("PullupBar", bm, material("Mat_PullupBar", (0.08, 0.09, 0.10), 0.9, 0.35))
print(f"PullupBar: bar radius {BAR_R*1000:.0f} mm at z = {BAR_Z} m, posts {2*POST_X:.1f} m apart, verts {len(bar.data.vertices)}, "
      f"tris {sum(len(p.vertices)-2 for p in bar.data.polygons)}")


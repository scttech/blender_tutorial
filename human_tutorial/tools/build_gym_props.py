"""build_gym_props.py - the dumbbells and the barbell, low-poly, with simple materials. Run before build_prop_rig.py:   exec(open(".../build_gym_props.py").read(), {})

Dumbbell.L, Dumbbell.R   a 5 kg-class pair: a 14 cm handle (32 mm across) with a six-sided head on each end, lying on the floor along X, centre at 7 cm up
Barbell                   a 2.0 m bar (28 mm) with a 20 kg plate (45 cm across) on each end, along X, centre at 22.5 cm up
Origins are at the centre of each (the grip is at the centre of the handle, or two hand-widths either side of the centre of the bar). Safe to re-run: it replaces them.
"""
import bpy, bmesh, math
from mathutils import Matrix

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

def finish(name, bm, mat, location):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(mat); ob.location = location
    coll = bpy.data.collections["Props"]
    if coll.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(coll)
    coll.objects.link(ob); return ob

def along_x(bm, radius, x0, x1, seg):
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=radius, radius2=radius, depth=x1 - x0,
                          matrix=Matrix.Translation(((x0 + x1) / 2, 0, 0)) @ Matrix.Rotation(math.radians(90), 4, 'Y'))

steel, rubber = material("Mat_DumbbellSteel", (0.55, 0.57, 0.60), 1.0, 0.3), material("Mat_DumbbellHead", (0.04, 0.04, 0.045), 0.6, 0.45)
def dumbbell(name, x):
    fresh(name); bm = bmesh.new()
    along_x(bm, 0.016, -0.07, 0.07, 14)                                   # the handle
    for s in (-1, 1): along_x(bm, 0.065, s * 0.075 - 0.02, s * 0.075 + 0.02, 6)           # a hexagonal head each side (so it does not roll)
    return finish(name, bm, steel, (x, -0.25, 0.07))
dumbbell("Dumbbell.L", 0.30); dumbbell("Dumbbell.R", -0.30)

fresh("Barbell"); bm = bmesh.new()
along_x(bm, 0.014, -1.0, 1.0, 16)                                          # the bar
for s in (-1, 1):
    along_x(bm, 0.225, s * 0.60 - 0.02, s * 0.60 + 0.02, 24)                  # a plate each side, 45 cm across and 4 cm thick
    along_x(bm, 0.02, s * 0.60 - 0.05, s * 0.60 + 0.05, 12)                   # the sleeve
finish("Barbell", bm, material("Mat_Barbell", (0.30, 0.31, 0.33), 0.9, 0.35), (0.0, -0.45, 0.225))
for n in ("Dumbbell.L", "Dumbbell.R", "Barbell"):
    ob = bpy.data.objects[n]; print(n, "verts", len(ob.data.vertices), "tris", sum(len(p.vertices) - 2 for p in ob.data.polygons), "at", tuple(round(c, 3) for c in ob.location))


# ---------------------------------------------------------------- a flat bench (a static fixture: no bone)
fresh("Bench"); bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, 0.425)) @ Matrix.Diagonal((0.30, 1.10, 0.10, 1.0)))             # the pad: 30 x 110 cm, 10 cm thick, top at 47.5 cm
for sx in (-1, 1):
    for sy in (-1, 1):
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((sx * 0.12, sy * 0.45, 0.19)) @ Matrix.Diagonal((0.05, 0.05, 0.38, 1.0)))    # four legs
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bench = finish("Bench", bm, material("Mat_Bench", (0.10, 0.10, 0.11), 0.2, 0.6), (0.0, 0.35, 0.0))
print("Bench verts", len(bench.data.vertices), "pad top at z", round(max(v.co.z for v in bench.data.vertices), 3), "y from", round(bench.location.y - 0.55, 2), "to", round(bench.location.y + 0.55, 2))

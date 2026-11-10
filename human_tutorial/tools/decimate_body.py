"""decimate_body.py - Step 3: build the low-poly "Body" from the hidden "Body_HighPoly" reference.

Run inside Blender (Scripting workspace) with the Step 2 scene open (objects "Body" and "Body_HighPoly").
Safe to re-run: it throws away the old "Body" mesh and rebuilds it from the reference each time.

Pipeline
  1. copy Body_HighPoly -> Body
  2. Merge by Distance: the glTF importer splits vertices along UV seams, so without this each UV island is
     decimated on its own and the seams drift apart (steps and cracks, e.g. across the forearm)
  3. paint a "keep_detail" vertex group by region: hands, face and the shoulder/elbow/hip/knee joints
  4. Decimate (Collapse) with that group, inverted so that it PROTECTS instead of targets, then apply
"""
import bpy, bmesh, math

RATIO = 0.09        # overall triangle ratio; 0.09 of 172k is about 15.5k triangles
STRENGTH = 0.3      # how hard the mask protects (1.0 = untouchable; the hands alone would eat the whole budget)
MERGE_DIST = 1e-5   # metres

ref = bpy.data.objects["Body_HighPoly"]

# 1. fresh working copy -------------------------------------------------------------------------------
old = bpy.data.objects.get("Body")
if old:
    mesh_old = old.data
    bpy.data.objects.remove(old, do_unlink=True)
    bpy.data.meshes.remove(mesh_old)
work = ref.copy(); work.data = ref.data.copy(); work.name = work.data.name = "Body"
for c in list(work.users_collection): c.objects.unlink(work)
bpy.data.collections["Collection"].objects.link(work)
work.hide_set(False)

# 2. merge seam vertices --------------------------------------------------------------------------------
bm = bmesh.new(); bm.from_mesh(work.data)
before = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=MERGE_DIST)
print(f"merge by distance: {before} -> {len(bm.verts)} vertices")
bm.to_mesh(work.data); bm.free()

# 3. detail mask ------------------------------------------------------------------------------------------
JOINTS = [(0.20, 1.45, 0.05, .7), (0.48, 1.45, 0.05, .7),     # shoulder, elbow   (|x|, z, radius, weight)
          (0.09, 0.95, 0.06, .7), (0.09, 0.49, 0.06, .7)]     # hip, knee

def falloff(d, r):                       # 1 inside radius r, fading to 0 at 2r
    return 1.0 if d <= r else max(0.0, 1.0 - (d - r) / r)

def mask(co):
    x, y, z = co; ax = abs(x); w = 0.0
    if ax > 0.72 and z > 1.2: w = 1.0                         # hands: wrist to fingertips
    elif ax > 0.64 and z > 1.2: w = (ax - 0.64) / 0.08        # ramp from the forearm into the hand
    if z > 1.62: w = max(w, 0.8)                              # head and face
    for jx, jz, r, k in JOINTS:
        w = max(w, k * falloff(math.dist((ax, z), (jx, jz)), r))
    return w

vg = work.vertex_groups.new(name="keep_detail")
for v in work.data.vertices:
    w = mask(v.co) * STRENGTH
    if w > 0.015: vg.add([v.index], w, 'REPLACE')

# 4. decimate and apply ---------------------------------------------------------------------------------
d = work.modifiers.new("Decimate", 'DECIMATE')
d.decimate_type = 'COLLAPSE'; d.ratio = RATIO
d.vertex_group = "keep_detail"; d.invert_vertex_group = True; d.vertex_group_factor = 1.0
d.use_collapse_triangulate = True
bpy.ops.object.select_all(action='DESELECT'); work.select_set(True); bpy.context.view_layer.objects.active = work
bpy.ops.object.modifier_apply(modifier="Decimate")

P = work.data.polygons
print("result: verts", len(work.data.vertices), "tris", len(P),
      "| hands", sum(1 for p in P if abs(p.center.x) > .72 and p.center.z > 1.2),
      "head", sum(1 for p in P if p.center.z > 1.62),
      "| dims", tuple(round(x, 3) for x in work.dimensions))

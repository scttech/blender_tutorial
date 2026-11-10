"""clean_body.py - Step 4: final mesh checks and fixes on "Body" (run after decimate_body.py).

Reports: smooth shading, flipped normals, sliver triangles, vertices below the floor, and fused-finger connectivity.
Fixes:   recalculates normals outward, and clamps any vertex below z=0 up to the floor.
"""
import bpy, bmesh, math

o = bpy.data.objects["Body"]; me = o.data
print("smooth faces", sum(1 for p in me.polygons if p.use_smooth), "of", len(me.polygons))

bm = bmesh.new(); bm.from_mesh(me)

before = [f.normal.copy() for f in bm.faces]
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)                      # Mesh > Normals > Recalculate Outside
print("faces that pointed the wrong way:", sum(1 for f, n in zip(bm.faces, before) if f.normal.dot(n) < 0))

angs = [math.degrees(min(l.calc_angle() for l in f.loops)) for f in bm.faces]
print("slivers: corner < 5 deg:", sum(a < 5 for a in angs), "| < 1 deg:", sum(a < 1 for a in angs))

for v in bm.verts:                                                      # nothing may sit below the floor
    if v.co.z < 0: v.co.z = 0.0

# how many separate pieces does each hand break into when cut at distance x from the body?
bm.verts.ensure_lookup_table()
for side, sgn in (("left", 1), ("right", -1)):
    row = []
    for cut in (0.80, 0.84, 0.88, 0.91, 0.93):
        keep = {v.index for v in bm.verts if sgn * v.co.x > cut and v.co.z > 1.2}
        seen, pieces = set(), 0
        for i in keep:
            if i in seen: continue
            pieces += 1; stack = [i]; seen.add(i)
            while stack:
                c = stack.pop()
                for e in bm.verts[c].link_edges:
                    w = e.other_vert(bm.verts[c]).index
                    if w in keep and w not in seen: seen.add(w); stack.append(w)
        row.append((cut, pieces))
    print(side, "hand pieces at each cut (1 = fingers fused):", row)

bm.to_mesh(me); bm.free(); me.update()
print("min z", round(min(v.co.z for v in me.vertices), 4))

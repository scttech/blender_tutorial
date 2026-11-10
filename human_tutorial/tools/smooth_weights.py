"""smooth_weights.py - Step 9: blur the skin weights of the body (not the hands) to soften stretching at the joints.

Run after bind_and_weight.py:   G = {"FACTOR": 0.5, "ITER": 2};  exec(open(".../smooth_weights.py").read(), G)

For every vertex outside the hands: new weight = (1 - FACTOR) * own + FACTOR * average of its neighbours', repeated ITER times,
per bone. Then the same export clean-up as Step 8 (drop tiny weights, at most 4 bones, normalize).
Hands are skipped because Step 8 weighted them finger by finger and blurring would undo that.
To undo: re-run bind_and_weight.py.
"""
import bpy, bmesh, collections

FACTOR, ITER = globals().get("FACTOR", 0.5), globals().get("ITER", 2)
body = bpy.data.objects["Body"]
names = {g.index: g.name for g in body.vertex_groups}

bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
nbrs = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
pos = [v.co.copy() for v in bm.verts]; bm.free()

def in_hand(p): return abs(p.x) > 0.74 and p.z > 1.3

W = [{names[g.group]: g.weight for g in v.groups if g.weight > 0} for v in body.data.vertices]
free = [i for i, p in enumerate(pos) if not in_hand(p)]
for _ in range(ITER):
    new = {}
    for i in free:
        acc = collections.defaultdict(float)
        for k, w in W[i].items(): acc[k] += (1 - FACTOR) * w
        if nbrs[i]:
            for j in nbrs[i]:
                for k, w in W[j].items(): acc[k] += FACTOR * w / len(nbrs[i])
        new[i] = dict(acc)
    for i, d in new.items(): W[i] = d

for i in free:
    for g in list(body.data.vertices[i].groups): body.vertex_groups[g.group].remove([i])
    for k, w in W[i].items():
        if w > 1e-4: body.vertex_groups[k].add([i], w, 'REPLACE')

bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active = body
bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0.01, keep_single=True)
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
print(f"smoothed {len(free)} vertices, factor {FACTOR}, {ITER} passes")

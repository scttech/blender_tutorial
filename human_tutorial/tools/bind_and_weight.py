"""bind_and_weight.py - Step 8: attach "Body" to "Rig" and make the skin weights export-ready.

Run inside Blender after build_armature.py (with HANDS=True). Safe to re-run: it rebinds from scratch.

    exec(open(".../bind_and_weight.py").read(), {})

Stages
  1. bind with automatic weights (Ctrl+P > With Automatic Weights)
  2. re-weight the hands FINGER BY FINGER, because the fingers are fused in the mesh and the automatic weights bleed
  3. clean tiny weights, limit to 4 bones per vertex (glTF allows 4), normalize so every vertex sums to 1
  4. report
"""
import bpy, math, collections
from mathutils import Vector

body, rig = bpy.data.objects["Body"], bpy.data.objects["Rig"]
FINGERS = ("Index", "Middle", "Ring", "Pinky", "Thumb")
HAND_X = globals().get("HAND_X", 0.76)   # beyond this |x| the hand weights replace the automatic ones (99 = keep automatic)
BLEND = 0.012          # half-width (m) of the blend at a joint
LATERAL = globals().get("LATERAL", 0.008)   # (m) how close two fingers must be before their weights mix (0 = hard edges)

def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)

# ------------------------------------------------------------------ 1. bind
if "keep_detail" in body.vertex_groups: body.vertex_groups.remove(body.vertex_groups["keep_detail"])   # Step 3 mask, not a bone
for m in list(body.modifiers): body.modifiers.remove(m)
for g in list(body.vertex_groups): body.vertex_groups.remove(g)
body.parent = None
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')

# ------------------------------------------------------------------ helpers
def chains(side):
    """finger -> list of (name, head, tail) for the three bones of that finger, in order"""
    out = {}
    for f in FINGERS:
        out[f] = [(f"{f}{i}.{side}", rig.data.bones[f"{f}{i}.{side}"].head_local.copy(),
                   rig.data.bones[f"{f}{i}.{side}"].tail_local.copy()) for i in (1, 2, 3)]
    return out

def along(chain, p):
    """closest approach of point p to a finger: (distance, arc-length position u along the finger, segments)
    u < 0 means p is in the palm, behind the knuckle; the first segment is extended backward to measure that."""
    segs, total = [], 0.0
    for name, h, t in chain:
        L = (t - h).length; segs.append((name, h, t, L, total)); total += L
    best_d, best_u = 1e9, 0.0
    for k, (name, h, t, L, start) in enumerate(segs):
        d_vec = (t - h) / L; s = (p - h).dot(d_vec)
        s = min(s, L) if k == 0 else max(0.0, min(s, L))
        d = (p - (h + d_vec * s)).length
        if d < best_d: best_d, best_u = d, start + s
    return best_d, best_u, segs

def finger_weights(segs, u):
    """weights for arc-length position u: Hand -> bone1 -> bone2 -> bone3, each handover a smooth blend that sums to 1"""
    b1, b2 = segs[0][3], segs[0][3] + segs[1][3]
    t0 = smooth((u + BLEND) / (2 * BLEND))               # palm -> finger, across the knuckle
    t1 = smooth((u - b1 + BLEND) / (2 * BLEND))          # bone 1 -> bone 2
    t2 = smooth((u - b2 + BLEND) / (2 * BLEND))          # bone 2 -> bone 3
    return {"Hand": 1 - t0, segs[0][0]: t0 * (1 - t1), segs[1][0]: t0 * t1 * (1 - t2), segs[2][0]: t0 * t1 * t2}

def finger_bleed(side_sign, thresh=0.88):
    """tip-region vertices only: how much finger weight is on a finger other than the one the vertex sits in"""
    side = "L" if side_sign > 0 else "R"; ch = chains(side)
    names = {g.index: g.name for g in body.vertex_groups}
    wrong = total = 0.0; mixed = n = 0
    for v in body.data.vertices:
        if side_sign * v.co.x < thresh or v.co.z < 1.3: continue
        own = min(FINGERS, key=lambda f: along(ch[f], v.co)[0])
        per = collections.defaultdict(float)
        for g in v.groups:
            nm = names[g.group]
            for f in FINGERS:
                if nm.startswith(f): per[f] += g.weight
        s = sum(per.values())
        if s <= 0: continue
        n += 1; total += s; wrong += s - per[own]; mixed += sum(1 for f in per if per[f] > 0.05) > 1
    return n, (wrong / total if total else 0.0), mixed

print("BEFORE the hand fix (automatic weights): tip vertices left/right",
      finger_bleed(1)[0], finger_bleed(-1)[0],
      "| weight on the wrong finger: L %.1f%% R %.1f%%" % (100 * finger_bleed(1)[1], 100 * finger_bleed(-1)[1]),
      "| vertices mixing >1 finger: L", finger_bleed(1)[2], "R", finger_bleed(-1)[2])

# ------------------------------------------------------------------ 2. hands, finger by finger
changed = 0
for sign, side in ((1, "L"), (-1, "R")):
    ch = chains(side)
    for v in body.data.vertices:
        if sign * v.co.x < HAND_X or v.co.z < 1.3: continue
        ds = sorted(((along(ch[f], v.co)[0], f) for f in FINGERS))
        (d1, f1), (d2, f2) = ds[0], ds[1]
        mu = 0.5 * (1 - min(1.0, (d2 - d1) / LATERAL))        # 0 deep inside a finger, 0.5 exactly between two
        total = collections.defaultdict(float)
        for f, share in ((f1, 1 - mu), (f2, mu)):
            if share <= 0: continue
            _, u, segs = along(ch[f], v.co)
            for name, w in finger_weights(segs, u).items():
                total["Hand." + side if name == "Hand" else name] += share * w
        for g in list(v.groups):                              # replace whatever the automatic pass gave this vertex
            body.vertex_groups[g.group].remove([v.index])
        for name, w in total.items():
            if w > 1e-4: body.vertex_groups[name].add([v.index], w, 'REPLACE')
        changed += 1
print("hand vertices re-weighted:", changed)

# ------------------------------------------------------------------ 3. clean up for export
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); bpy.context.view_layer.objects.active = body
bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0.01, keep_single=True)
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)

# ------------------------------------------------------------------ 4. report
names = {g.index: g.name for g in body.vertex_groups}
infl = collections.Counter(); bad_sum = 0; none = 0; per = collections.Counter()
for v in body.data.vertices:
    gs = [g for g in v.groups if g.weight > 0]
    infl[len(gs)] += 1; none += (not gs)
    if gs and abs(sum(g.weight for g in gs) - 1) > 1e-3: bad_sum += 1
    for g in gs: per[names[g.group]] += 1
print("AFTER: no weights:", none, "| sum != 1:", bad_sum, "| influences per vertex:", sorted(infl.items()))
deform = {b.name for b in rig.data.bones if b.use_deform}
print("deform bones with no vertices:", sorted(deform - set(per)))
print("tip bleed after: L %.1f%% R %.1f%%" % (100 * finger_bleed(1)[1], 100 * finger_bleed(-1)[1]),
      "| vertices mixing >1 finger: L", finger_bleed(1)[2], "R", finger_bleed(-1)[2])

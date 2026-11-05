"""cat_anim_core.py - shared helpers for building the cat's animations.

Run inside Blender (Scripting workspace), in a Python console or text editor, with the cat scene open:

    exec(open("/path/to/cat_anim_core.py").read(), G)      # G is any dict, e.g. G = {}

The other cat_anim_*.py files build on this one and must be exec'd into the SAME dict, after this one.

What is here
  * a small 3D forward-kinematics engine (fast, no mesh evaluation, matches Blender's pose to 0.0000 m)
  * a planar leg IK solver (legs swing forward/back about the world X axis)
  * helpers to build a pose, bake it as an action, and measure the result
Conventions: the cat faces -Y, its right side is -X, +Z is up. A rotation about +X by a positive angle moves
+Y toward +Z, so on the cat's body "positive pitch" means NOSE DOWN and a positive leg rotation swings the foot BACK.
"""
import bpy, math
import numpy as np
from mathutils import Quaternion, Vector, Matrix

ARM_NAME, MESH_NAME = "SmartRigArmature", "Mesh_0"
arm = bpy.data.objects[ARM_NAME]
mesh = bpy.data.objects[MESH_NAME]
scene = bpy.context.scene
bones = {b.name: b for b in arm.data.bones}
rest_m = {n: b.matrix_local.copy() for n, b in bones.items()}
rel = {n: ((rest_m[b.parent.name].inverted() @ rest_m[n]) if b.parent else rest_m[n]) for n, b in bones.items()}
ZAXIS = Vector((0, 0, 1))

# ---------------------------------------------------------------- 3D forward kinematics
def basis_of(q, loc=(0, 0, 0)):
    return Matrix.Translation(Vector(loc)) @ Quaternion(q).to_matrix().to_4x4()

def make_pm(basis):
    """basis: bone name -> 4x4 pose matrix (identity if missing). Returns pm(name) = the bone's pose matrix."""
    cache = {}
    def pm(n):
        if n not in cache:
            b = bones[n]
            cache[n] = (pm(b.parent.name) if b.parent else Matrix.Identity(4)) @ rel[n] @ basis.get(n, Matrix.Identity(4))
        return cache[n]
    return pm

def tailpos(pm, n):  return pm(n) @ Vector((0, bones[n].length, 0))
def headpos(pm, n):  return pm(n) @ Vector((0, 0, 0))

def axis_local(n, world_axis):
    """A world axis expressed in bone n's REST frame (valid when the bone's parents are only rotated about that same axis)."""
    return (rest_m[n].to_3x3().inverted() @ Vector(world_axis)).normalized()
def x_axis(n): return axis_local(n, (1, 0, 0))

def basis_dict(quats, root_loc):
    return {n: (basis_of(q, root_loc) if n == "root" else basis_of(q)) for n, q in quats.items()}

# ---------------------------------------------------------------- planar maths for the legs
def yz(v): return np.array([v.y, v.z])
def rot(a, v):
    c, s = math.cos(a), math.sin(a)
    return np.array([v[0]*c - v[1]*s, v[0]*s + v[1]*c])
def ang(v): return math.atan2(v[1], v[0])
def wrap(a): return (a + math.pi) % (2*math.pi) - math.pi
def smooth(u):
    u = min(max(u, 0.0), 1.0); return u*u*(3 - 2*u)
def lerp(a, b, s): return a + (b - a)*s
def bump(t, centre, width):                       # smooth periodic bump on t in [0,1)
    d = (t - centre + 0.5) % 1.0 - 0.5
    return math.exp(-(d/width)**2)

def lm(resfn, x0, iters=80, lam=1e-3):
    """Small Levenberg-Marquardt solver with a numeric Jacobian."""
    x = np.array(x0, float)
    for _ in range(iters):
        r = resfn(x); J = np.zeros((len(r), len(x)))
        for k in range(len(x)):
            xe = x.copy(); xe[k] += 1e-5; J[:, k] = (resfn(xe) - r)/1e-5
        dx = np.linalg.solve(J.T @ J + lam*np.eye(len(x)), -J.T @ r); x = x + dx
        if np.linalg.norm(dx) < 1e-9: break
    return x

LEGS = {
    "RF": ["front_leg_upper.R", "front_leg_lower.R", "front_leg_wrist.R", "front_leg_paw.R", "front_leg_toe.R"],
    "LF": ["front_leg_upper.L", "front_leg_lower.L", "front_leg_wrist.L", "front_leg_paw.L", "front_leg_toe.L"],
    "RH": ["back_leg_upper.R",  "back_leg_lower.R",  "back_leg_wrist.R",  "back_leg_paw.R",  "back_leg_toe.R"],
    "LH": ["back_leg_upper.L",  "back_leg_lower.L",  "back_leg_wrist.L",  "back_leg_paw.L",  "back_leg_toe.L"],
}
LEG_BONES = [n for L in LEGS for n in LEGS[L][:4]]          # the toe just follows the paw
TAIL = [f"tail_{i}" for i in range(1, 6)]
KEYED_BODY = ["root", "spine", "neck_1", "neck_2"] + TAIL
KEYED = KEYED_BODY + LEG_BONES
PARENT = {L: bones[LEGS[L][0]].parent.name for L in LEGS}
REST = {}
for _L, _names in LEGS.items():
    _b = [bones[n] for n in _names]
    REST[_L] = [yz(_b[0].head_local), yz(_b[1].head_local), yz(_b[2].head_local), yz(_b[3].head_local), yz(_b[4].head_local), yz(_b[4].tail_local)]

def fk_all(delta, P, hip, beta):
    """Planar forward kinematics of one leg. Returns joint positions Q[0..5] (hip..toe tip) and cumulative world angles A[0..3]."""
    s = [P[i+1] - P[i] for i in range(5)]
    A = [beta + delta[0]]; A.append(A[0] + delta[1]); A.append(A[1] + delta[2]); A.append(A[2] + delta[3])
    Q = [hip, hip + rot(A[0], s[0])]; Q.append(Q[1] + rot(A[1], s[1])); Q.append(Q[2] + rot(A[2], s[2]))
    Q.append(Q[3] + rot(A[3], s[3])); Q.append(Q[4] + rot(A[3], s[4]))
    return Q, A

def leg_frame(pm, L):
    """Where a leg's hip really is, and how much its parent bone is pitched, in the current (non-leg) pose."""
    hip = headpos(pm, LEGS[L][0]); par = PARENT[L]
    R = pm(par).to_3x3() @ rest_m[par].to_3x3().inverted()
    return np.array([hip.y, hip.z]), math.atan2(R[2][1], R[1][1])

def solve_leg(L, hip, beta, tip, x0, flat=0.0, w_flat=0.15, w_reg=0.03, extra=None, iters=80):
    """Joint angles (upper, lower, wrist, paw) that put the toe tip at `tip` with the paw at world angle `flat`.
    extra(Q, A) may return more residuals (e.g. a heel position)."""
    P = REST[L]
    def res(x):
        Q, A = fk_all(x, P, hip, beta)
        r = [[w_flat*(A[3] - flat)], w_reg*x]
        if tip is not None: r.append(Q[5] - tip)             # tip=None: no toe-tip goal (the `extra` goals say where the leg should be)
        if extra: r.append(extra(Q, A))
        return np.concatenate(r)
    return lm(res, x0, iters=iters)

# ---------------------------------------------------------------- building a pose
def tail_quats(droop=0.0, yaws=None, root_pitch=0.0):
    """Tail rotations: the whole tail pitched DOWN by `droop` (rigid), each joint then turned about the true vertical by yaws[i]."""
    yaws = yaws or [0.0]*5; out = []
    for i, n in enumerate(TAIL):
        pp = root_pitch if i == 0 else -droop                      # world pitch of this bone's parent
        a = (rest_m[n].to_3x3().inverted() @ (Matrix.Rotation(-pp, 3, 'X') @ ZAXIS)).normalized()
        tau = (-droop - root_pitch) if i == 0 else 0.0
        out.append(Quaternion(a, yaws[i]) @ Quaternion(x_axis(n), tau))
    return out

def _rest_yaw(b):
    d = b.tail_local - b.head_local
    return math.atan2(-d.x, d.y)
_ry = [_rest_yaw(bones[n]) for n in TAIL]
TAIL_STRAIGHTEN = [-(_ry[i] - (_ry[i-1] if i else 0.0)) for i in range(5)]    # yaw per joint that straightens the curled tail

def neck_split(total):                                   # nose-down pitch shared 40/60 over the two neck bones
    return (0.4*total, 0.6*total)

def neck_quats_vertical(p1, p2, yaw, parent_pitch):
    """Neck rotations: pitches p1, p2 (+ = nose down) plus a head turn `yaw` about the TRUE vertical, even though the neck's parents are
    tilted by `parent_pitch` (body pitch + spine). Yaw is shared 40/60 over the two neck bones."""
    a1 = (rest_m["neck_1"].to_3x3().inverted() @ (Matrix.Rotation(-parent_pitch, 3, 'X') @ ZAXIS)).normalized()
    a2 = (rest_m["neck_2"].to_3x3().inverted() @ (Matrix.Rotation(-(parent_pitch + p1), 3, 'X') @ ZAXIS)).normalized()
    return (Quaternion(a1, 0.4*yaw) @ Quaternion(x_axis("neck_1"), p1), Quaternion(a2, 0.6*yaw) @ Quaternion(x_axis("neck_2"), p2))

def body_pose(dy=0.0, dz=0.0, pitch=0.0, roll=0.0, spine=0.0, neck=0.0, tail=None, neck_q=None):
    """Quaternions for every non-leg keyed bone, and the root's location. pitch/spine/neck: + = nose down. roll: about world Y.
    neck_q=(q1, q2) overrides the neck (see neck_quats_vertical)."""
    q = {}
    loc = rest_m["root"].to_3x3().inverted() @ Vector((0, dy, dz))
    qr = Quaternion(x_axis("root"), pitch)
    if roll: qr = Quaternion(axis_local("root", (0, 1, 0)), roll) @ qr
    q["root"] = qr
    q["spine"] = Quaternion(x_axis("spine"), spine)
    n1, n2 = neck_split(neck)
    q["neck_1"] = Quaternion(x_axis("neck_1"), n1); q["neck_2"] = Quaternion(x_axis("neck_2"), n2)
    if neck_q: q["neck_1"], q["neck_2"] = neck_q
    tq = tail or tail_quats()
    for n, t in zip(TAIL, tq): q[n] = t
    return q, loc

def leg_quats(L, x):
    return {LEGS[L][j]: Quaternion(x_axis(LEGS[L][j]), float(x[j])) for j in range(4)}

# ---------------------------------------------------------------- foot paths for gaits
def foot_target(L, t, cfg):
    """Toe-tip target at cycle time t (0..1): planted and sliding back during stance, lifted and swung forward in the air."""
    y0, z0 = REST[L][5]
    ph = (t - cfg["offset"][L]) % 1.0; d = cfg["duty"][L]; S = cfg["stride"][L]; H = cfg["lift"][L]; c = cfg["shift"][L]
    if ph < d:
        return np.array([y0 + c - S/2 + S*(ph/d), z0]), True
    s = (ph - d)/(1 - d); e = s*s*(3 - 2*s)
    return np.array([y0 + c + S/2 - S*e, z0 + H*math.sin(math.pi*s)]), False

# ---------------------------------------------------------------- solving and baking
def resolve_tip(tg, hip):
    """The toe-tip target for one leg. tg['tip'] is a world position; tg['rel'] = (offset, w) blends toward hip + offset
    (a target that moves with the body, used when the feet are in the air). Returns None if there is no toe-tip goal."""
    base = tg.get("tip")
    if "rel" in tg:
        off, w = tg["rel"]; rel = hip + np.array(off)
        return rel if base is None else (1 - w)*np.array(base) + w*rel
    return base

def solve_frames(n, frame_fn, cyclic=True, warm_from_rest=True, n_warm=24):
    """frame_fn(t) -> dict(body=dict(body_pose kwargs), tips={L: dict(tip=yz, flat=0, w_flat=0.15, contact=bool)}).
    Solves the four legs at frames 0..n (t = k/n). If cyclic, the cycle is solved twice so the end matches the start."""
    xs = {L: np.zeros(4) for L in LEGS}
    if warm_from_rest:                                    # ease from the standing pose into frame 0 so the legs pick a sensible branch
        spec0 = frame_fn(0.0)
        for i in range(1, n_warm + 1):
            s = smooth(i/n_warm)
            body = {k: (v*s if isinstance(v, (int, float)) else v) for k, v in spec0["body"].items()}
            q, loc = body_pose(**{k: v for k, v in body.items() if k != "tail"}, tail=None)
            pm = make_pm(basis_dict(q, loc))
            for L in LEGS:
                hip, beta = leg_frame(pm, L)
                t0 = resolve_tip(spec0["tips"][L], hip)
                tip = None if t0 is None else lerp(REST[L][5], t0, s)
                xs[L] = solve_leg(L, hip, beta, tip, xs[L], flat=spec0["tips"][L].get("flat", 0.0), w_flat=spec0["tips"][L].get("w_flat", 0.15),
                                  extra=spec0["tips"][L].get("extra"))
    out = []
    for p in range(2 if cyclic else 1):
        out = []
        for k in range(n + 1):
            spec = frame_fn(k/n) if not (cyclic and k == n) else frame_fn(0.0)
            q, loc = body_pose(**spec["body"])
            pm = make_pm(basis_dict(q, loc))
            fx = {}
            for L in LEGS:
                tg = spec["tips"][L]; hip, beta = leg_frame(pm, L)
                xs[L] = solve_leg(L, hip, beta, resolve_tip(tg, hip), xs[L], flat=tg.get("flat", 0.0), w_flat=tg.get("w_flat", 0.15), extra=tg.get("extra"))
                fx[L] = xs[L].copy()
            out.append(dict(spec=spec, q=q, loc=loc, legs=fx))
    if cyclic: out[-1] = out[0]
    return out

def new_action(name):
    if name in bpy.data.actions: bpy.data.actions.remove(bpy.data.actions[name])
    a = bpy.data.actions.new(name); a.use_fake_user = True
    arm.animation_data_create(); arm.animation_data.action = a
    return a

def bake(name, frames, first_frame=1, only=None, reset=True):
    """frames: list of dict(q=body quats, loc=root location, legs={L: x}) -> a keyframed action (a key on every frame).
    only: a list of bone names to key (default: every keyed bone). The root's location is keyed whenever 'root' is included."""
    if reset:
        for pb in arm.pose.bones:
            pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    act = new_action(name); prev = {}; keyed = only or KEYED
    for k, fr in enumerate(frames):
        allq = dict(fr["q"])
        for L, x in fr["legs"].items(): allq.update(leg_quats(L, x))
        for n in keyed:
            q = allq.get(n, Quaternion((1, 0, 0, 0)))
            if n in prev and q.dot(prev[n]) < 0: q = Quaternion((-q.w, -q.x, -q.y, -q.z))     # keep the quaternion on one side so it interpolates smoothly
            prev[n] = q
            pb = arm.pose.bones[n]; pb.rotation_quaternion = q; pb.keyframe_insert("rotation_quaternion", frame=first_frame + k)
        if "root" in keyed:
            arm.pose.bones["root"].location = fr["loc"]; arm.pose.bones["root"].keyframe_insert("location", frame=first_frame + k)
    act.use_frame_range = True; act.frame_start = first_frame; act.frame_end = first_frame + len(frames) - 1
    scene.frame_start, scene.frame_end = int(act.frame_start), int(act.frame_end)
    return act

def frame_basis(fr):
    q = dict(fr["q"])
    for L, x in fr["legs"].items(): q.update(leg_quats(L, x))
    return basis_dict(q, fr["loc"])

def report_gait(label, frames, cfg=None, tips_key="tips"):
    """Measure the real toe-tip positions against the plan with the FK engine (contact frames: slide and ground height)."""
    worst = {L: 0.0 for L in LEGS}; spread = {L: [] for L in LEGS}; ground = {L: 1e9 for L in LEGS}
    for fr in frames[:-1]:
        pm = make_pm(frame_basis(fr)); pm_body = make_pm(basis_dict(fr["q"], fr["loc"]))
        for L in LEGS:
            tg = fr["spec"]["tips"][L]; tp = tailpos(pm, LEGS[L][4])
            goal = resolve_tip(tg, leg_frame(pm_body, L)[0])
            if goal is None: continue
            err = math.hypot(tp.y - goal[0], tp.z - goal[1])*100
            worst[L] = max(worst[L], err)
            if tg.get("contact"): spread[L].append(tp.z)
            ground[L] = min(ground[L], tp.z)
    print(f"[{label}] toe-tip error vs plan (max, cm): " + " | ".join(f"{L} {worst[L]:.2f}" for L in LEGS))
    print(f"[{label}] planted-foot height spread (cm): " + " | ".join(f"{L} {(max(v)-min(v))*100:.2f}" if v else f"{L} -" for L, v in spread.items())
          + " | lowest toe tip z (cm): " + " | ".join(f"{L} {ground[L]*100:+.1f}" for L in LEGS))
    return worst

def mesh_min_z():
    """Lowest world-space z of the deformed mesh in the CURRENT pose."""
    bpy.context.view_layer.update()
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh(); mw = mesh.matrix_world
    z = min((mw @ v.co).z for v in me.vertices); ev.to_mesh_clear(); return z

def scan_min_z(first, last, every=3):
    """Lowest mesh point over the frames of the ACTIVE action: returns (z, frame). Slow-ish (evaluates the whole mesh), so it samples."""
    worst = (1e9, None)
    for f in range(int(first), int(last) + 1, every):
        scene.frame_set(f); z = mesh_min_z()
        if z < worst[0]: worst = (z, f)
    return worst

def floor_guard(L, margin=0.01, k=3.0):
    """Extra IK goal for a planted leg: keep the wrist and paw joints at least as high as they are when standing (minus a margin),
    so a folded leg cannot push its mesh through the floor."""
    zw, zp = REST[L][2][1] - margin, REST[L][3][1] - margin
    def extra(Q, A):
        return np.array([k*max(0.0, zw - Q[2][1]), k*max(0.0, zp - Q[3][1])])
    return extra

def set_pose(frame):
    """Put the armature's pose bones into the pose described by a solved frame (no keyframes).
    Clears the active action first: otherwise Blender re-evaluates the action and overwrites the pose we just set."""
    arm.animation_data_create(); arm.animation_data.action = None
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    allq = dict(frame["q"])
    for L, x in frame["legs"].items(): allq.update(leg_quats(L, x))
    for n, q in allq.items(): arm.pose.bones[n].rotation_quaternion = q
    arm.pose.bones["root"].location = frame["loc"]
    bpy.context.view_layer.update()

print("cat_anim_core loaded: %d bones, %d leg bones, tail straighten (deg) %s" % (len(bones), len(LEG_BONES), [round(math.degrees(v)) for v in TAIL_STRAIGHTEN]))

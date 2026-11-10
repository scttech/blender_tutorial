"""poselib.py - shared helpers for exercises written as text (loaded with  python = "poselib.py"  into the anim_core namespace).

ride_arms(pose, style)   a POST HOOK: reads the finished body pose, then puts the hand and elbow targets where `style` says, relative to a
                         part of the body that is moving (the hips or the chest), so the hands stay on the body however it moves.
A style is measured ONCE on the standing rest pose (world coordinates, left side; the right mirrors it):
    frame  the body part the hands ride on ("Hips" or "Spine2")
    hand   where the left wrist is at rest      rot  the hand's rotation in the world at rest (degrees, XYZ; (0,0,0) = the T-pose hand)
    pole   where the left elbow pole is at rest fist the fist slider (0 open .. 1 closed)
When the frame turns and moves, hand and pole turn and move with it, and the hand's orientation turns the same way.
"""
import math
from mathutils import Vector, Euler

STYLES = {
    # fist on the side of the hip, elbow out and a little back (Step 17 lunge)
    # hands cupped behind the head, elbows wide (a crunch); rides on the head
    "behind_head": dict(frame="Head", hand=(0.115, 0.145, 1.75), rot=(180, -110, 0), pole=(0.70, 0.0, 1.70), fist=0.3),
    # hands together in front of the chest, fingers up, palms facing, elbows down and out (a prayer or diamond hold); rides on the chest
    "hands_together": dict(frame="Spine2", hand=(0.045, -0.20, 1.33), rot=(180, -90, 0), pole=(0.38, -0.08, 1.10), fist=0.0),
    # arms hanging straight down at the sides, hands by the thighs, palms in; rides on the hips (so the arms stay at the sides as the hips drop)
    "arms_sides": dict(frame="Hips", hand=(0.26, 0.06, 0.93), rot=(0, 90, 0), pole=(0.34, 0.60, 1.15), fist=0.0),
    # arms hanging loosely at the sides, riding on the CHEST so they swing with a twist
    "arms_swing": dict(frame="Spine2", hand=(0.26, 0.06, 0.93), rot=(0, 90, 0), pole=(0.34, 0.60, 1.15), fist=0.0),
    "hips_fists": dict(frame="Hips", hand=(0.25, 0.05, 1.12), rot=(0, 90, 0), pole=(0.70, 0.20, 1.25), fist=1.0),
}

def _apply_pose(spec):
    clear_pose()
    for frame, flat in expand([(1, spec)], True):
        for c, v in flat.items(): write(c, v)
    rig.update_tag(); bpy.context.view_layer.update()

_PREV_EULER = {}
def reset_poselib():
    """forget the previous keys' Euler angles; the compiler calls this before each exercise"""
    _PREV_EULER.clear()

def _targets(P, st, side="L"):
    """where the hand and elbow pole go for style `st` on `side`, given the posed rig P: (hand position, hand rotation in degrees, pole position or None, fist).
    The right side is the mirror image of the left AT REST (x flips; the rotation becomes (x, -y, -z)), then ridden on the body like the left, so a twisting or leaning
    torso moves the two arms differently, as it should"""
    mir = lambda v: Vector((-v[0], v[1], v[2])); sgn = 1 if side == "L" else -1
    B = rig.data.bones[st["frame"]]
    D = P[st["frame"]].matrix.to_3x3() @ B.matrix_local.to_3x3().inverted()          # how far the part has turned from rest
    head_now, head_rest = P[st["frame"]].head.copy(), B.head_local.copy()
    place = lambda r: head_now + D @ ((Vector(r) if side == "L" else mir(r)) - head_rest)
    rx, ry, rz = st["rot"]; R = D @ Euler([math.radians(a) for a in (rx, ry * sgn, rz * sgn)], 'XYZ').to_matrix()
    # a rotation matrix has several equivalent sets of Euler angles, and converting it back can jump between them from one key to the next (the hand flickers). Pick the set
    # closest to the previous key's, remembered per hand and style
    key = (st["frame"], side, tuple(st["rot"])); prev = _PREV_EULER.get(key)
    e = R.to_euler('XYZ', prev) if prev is not None else R.to_euler('XYZ'); _PREV_EULER[key] = e
    return place(st["hand"]), Vector(math.degrees(a) for a in e), (place(st["pole"]) if st.get("pole") else None), st["fist"]

def _arms_entry(hand, rot, pole, fist, side="L"):
    out = {f"Hand_IK.{side}": {"at": tuple(hand), "wrot": tuple(rot), "props": {"fist": fist}}}
    if pole is not None: out[f"Elbow_Pole.{side}"] = {"at": tuple(pole)}
    return out

def ride_arms(pose, style, sides="LR"):
    """sides: "LR" puts both hands on the body; "L" or "R" only that side (the other arm is free to do something else)"""
    st = STYLES[style] if isinstance(style, str) else style
    _apply_pose(pose); P = pose_bones(); out = {}
    for side in sides: out.update(_arms_entry(*_targets(P, st, side), side))
    return out

def ride_arms_blend(pose, a, b, w):
    """a POST HOOK: the arms between two styles. w = 0 is style `a`, w = 1 is style `b`; each style rides on its own part of the body. Position, rotation, pole and fist are
    blended in a straight line, so key it densely (every 3 to 5 frames) and check the reach"""
    A, Bst = STYLES[a], STYLES[b]; _apply_pose(pose); P = pose_bones(); out = {}
    mix = lambda x, y: x + (y - x) * w
    for side in "LR":
        ta, tb = _targets(P, A, side), _targets(P, Bst, side)
        pole = mix(ta[2], tb[2]) if ta[2] is not None and tb[2] is not None else (tb[2] if w >= 0.5 else ta[2])
        out.update(_arms_entry(mix(ta[0], tb[0]), mix(ta[1], tb[1]), pole, mix(ta[3], tb[3]), side))
    return out

def ride_prop(pose, prop, at, rot=(0, 0, 0), grab="grab_kettlebell", frame="Spine2", pole=None, fist=0.0):
    """a POST HOOK: put a prop where it would be at the standing rest pose (`at` = the prop bone's head, `rot` in degrees), but riding on `frame`
    so it follows the torso, and switch on its grab slider so both hands snap to its grips. `pole` is the left elbow pole at rest (the right mirrors it)."""
    _apply_pose(pose); P = pose_bones(); B = rig.data.bones[frame]
    D = P[frame].matrix.to_3x3() @ B.matrix_local.to_3x3().inverted()
    head_now, head_rest = P[frame].head.copy(), B.head_local.copy()
    place = lambda r: tuple(head_now + D @ (Vector(r) - head_rest))
    R = D @ Euler([math.radians(a) for a in rot], 'XYZ').to_matrix()
    out = {prop: {"at": place(at), "wrot": tuple(math.degrees(a) for a in R.to_euler('XYZ'))}, "Hand_IK.L": {"props": {grab: 1.0, "fist": fist}}}
    if pole: out["Elbow_Pole.L"] = {"at": place(pole)}
    return out


def arms_on_floor(pose, x=0.30, reach=0.52, z=0.05):
    """a POST HOOK for lying exercises: both hands flat on the floor beside the body, `reach` metres from the shoulder toward the feet, palms down"""
    _apply_pose(pose); sh = pose_bones()["UpperArm.L"].head
    return {"Hand_IK.L": {"at": (x, sh.y - reach, z), "wrot": (0, 0, -90), "props": {"fist": 0.0}}, "Elbow_Pole.L": {"at": (x + 0.40, sh.y - 0.25, 0.30)}}


def dead_bug_limbs(pose, a=0.0, b=0.0):
    """a POST HOOK for the dead bug (lying on the back): both arms point at the ceiling and both knees are over the hips, shins level (the 'table top').
    a (0..1) extends the LEFT arm overhead along the floor and the RIGHT leg straight out; b extends the right arm and the left leg. Written for
    exact positions: each limb is a hinge about its shoulder or hip, so the hand and ankle ride an arc and stay at the right length"""
    _apply_pose(pose); P = pose_bones(); out = {}
    for side in "LR":
        ext_arm, ext_leg = (a, b) if side == "L" else (b, a)
        S = P[f"UpperArm.{side}"].head.copy(); T = P[f"Thigh.{side}"].head.copy()
        beta = math.radians(78 * ext_arm); d = Vector((0, math.sin(beta), math.cos(beta)))                    # the arm: up (0) to nearly along the floor over the head (78)
        wrist = S + d * 0.52
        rot = Vector((1, 0, 0)).rotation_difference(d if side == "L" else Vector((0, d.y, d.z))).to_euler('XYZ')
        gam, kap = math.radians(85 * ext_leg), math.radians(90 * (1 - ext_leg))                                # the leg: thigh angle from the ceiling, knee bend
        t = Vector((0, -math.sin(gam), math.cos(gam))); s = Vector((0, -math.sin(gam + kap), math.cos(gam + kap)))
        knee = T + t * 0.42; ankle = knee + s * 0.45
        n = (t - s); n = n.normalized() if n.length > 0.05 else Vector((0, -0.2, 1.0)).normalized()
        out[f"Hand_IK.{side}"] = {"at": tuple(wrist), "wrot": tuple(math.degrees(x) for x in rot), "props": {"fist": 0.2}}
        out[f"Elbow_Pole.{side}"] = {"at": tuple(S + Vector((0.5 if side == "L" else -0.5, -0.1, 0.1)))}
        out[f"Foot_IK.{side}"] = {"at": tuple(ankle), "wrot": (-math.degrees(gam) + math.degrees(kap) * 0, 0, 0)}
        out[f"Knee_Pole.{side}"] = {"at": tuple(knee + n * 0.5)}
    return out


# ------------------------------------------------------------------ lying and standing limbs (hooks and helpers)
def _leg(T, gam, kap, side, length=(0.42, 0.45)):
    """a leg as two hinges about the hip joint T (lying on the back): the thigh at gam degrees from the ceiling toward the feet, the knee bent by kap degrees
    (the shin then points toward the feet). Returns the Foot_IK and Knee_Pole entries"""
    g, k = math.radians(gam), math.radians(kap)
    t = Vector((0, -math.sin(g), math.cos(g))); s = Vector((0, -math.sin(g + k), math.cos(g + k)))
    knee = T + t * length[0]; ankle = knee + s * length[1]
    n = t - s; n = n.normalized() if n.length > 0.05 else Vector((0, -0.2, 1.0)).normalized()
    return {f"Foot_IK.{side}": {"at": tuple(ankle), "wrot": (-(gam + kap), 0, 0)}, f"Knee_Pole.{side}": {"at": tuple(knee + n * 0.5)}}

def _floor_fix(pose, out):
    """the lying body was settled on the floor with its feet planted and knees bent; straight raised legs put the thighs a few mm lower. Lift the pelvis by whatever
    the lowest vertex of the body (hands and feet excluded) is below the floor now"""
    merged = {**pose, **out}; _apply_pose(merged); v, _ = mesh_state(); lo = float(v[regions() == "body", 2].min())
    if abs(lo) > 1e-4:
        mv = pose["Hips"]["move"]; out["Hips"] = {"move": (mv[0], mv[1], mv[2] - lo)}
    return out

def lying_legs(pose, gl, kl, gr, kr):
    """a POST HOOK for exercises lying on the back: place both legs. gl, kl: the LEFT thigh angle from the ceiling (0 = vertical, 85 = nearly flat, toward the feet)
    and knee bend; gr, kr: the right leg. A straight leg is kap = 0; the ankle is then 0.87 m from the hip, which is the leg's full length, so use 0.5 degrees of knee bend
    for a leg that must look straight but stay inside the knee limit"""
    _apply_pose(pose); P = pose_bones(); out = {}
    out.update(_leg(P["Thigh.L"].head.copy(), gl, kl, "L")); out.update(_leg(P["Thigh.R"].head.copy(), gr, kr, "R"))
    return _floor_fix(pose, out)

def arms_toward(pose, u, up=0.14):
    """a POST HOOK for the V-up: the arms point overhead along the floor at u = 0 and reach toward the ankles at u = 1 (straight arms, 0.52 m, a blend of the two directions)"""
    _apply_pose(pose); P = pose_bones(); out = {}
    for side in "LR":
        S = P[f"UpperArm.{side}"].head.copy(); ankle = Vector(pose[f"Foot_IK.{side}"]["at"])
        d0 = Vector((0, 1, up)).normalized(); d1 = (ankle - S).normalized(); d = (d0 * (1 - u) + d1 * u).normalized()
        rot = Vector((1, 0, 0)).rotation_difference(d).to_euler('XYZ')
        out[f"Hand_IK.{side}"] = {"at": tuple(S + d * 0.52), "wrot": tuple(math.degrees(x) for x in rot), "props": {"fist": 0.0}}
        out[f"Elbow_Pole.{side}"] = {"at": tuple(S + Vector((0.5 if side == "L" else -0.5, 0.0, 0.3)))}
    return out

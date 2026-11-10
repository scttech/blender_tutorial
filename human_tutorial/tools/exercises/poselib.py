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
    "behind_head": dict(frame="Head", hand=(0.10, 0.05, 1.74), rot=(180, -110, 0), pole=(0.70, 0.0, 1.70), fist=0.3),
    # hands together in front of the chest, fingers up, palms facing, elbows down and out (a prayer or diamond hold); rides on the chest
    "hands_together": dict(frame="Spine2", hand=(0.045, -0.20, 1.33), rot=(180, -90, 0), pole=(0.38, -0.08, 1.10), fist=0.0),
    # arms hanging straight down at the sides, hands by the thighs, palms in; rides on the hips (so the arms stay at the sides as the hips drop)
    "arms_sides": dict(frame="Hips", hand=(0.26, 0.06, 0.93), rot=(0, 90, 0), pole=(0.34, 0.60, 1.15), fist=0.0),
    "hips_fists": dict(frame="Hips", hand=(0.25, 0.05, 1.12), rot=(0, 90, 0), pole=(0.70, 0.20, 1.25), fist=1.0),
}

def _apply_pose(spec):
    clear_pose()
    for frame, flat in expand([(1, spec)], True):
        for c, v in flat.items(): write(c, v)
    rig.update_tag(); bpy.context.view_layer.update()

def _targets(P, st):
    """where the left hand and elbow pole go for style `st`, given the posed rig P: (hand position, hand rotation in degrees, pole position or None, fist)"""
    B = rig.data.bones[st["frame"]]
    D = P[st["frame"]].matrix.to_3x3() @ B.matrix_local.to_3x3().inverted()          # how far the part has turned from rest
    head_now, head_rest = P[st["frame"]].head.copy(), B.head_local.copy()
    place = lambda r: head_now + D @ (Vector(r) - head_rest)
    R = D @ Euler([math.radians(a) for a in st["rot"]], 'XYZ').to_matrix()
    return place(st["hand"]), Vector(math.degrees(a) for a in R.to_euler('XYZ')), (place(st["pole"]) if st.get("pole") else None), st["fist"]

def _arms_entry(hand, rot, pole, fist):
    out = {"Hand_IK.L": {"at": tuple(hand), "wrot": tuple(rot), "props": {"fist": fist}}}
    if pole is not None: out["Elbow_Pole.L"] = {"at": tuple(pole)}
    return out

def ride_arms(pose, style):
    st = STYLES[style] if isinstance(style, str) else style
    _apply_pose(pose); return _arms_entry(*_targets(pose_bones(), st))

def ride_arms_blend(pose, a, b, w):
    """a POST HOOK: the arms between two styles. w = 0 is style `a`, w = 1 is style `b`; each style rides on its own part of the body. Position, rotation, pole and fist are
    blended in a straight line, so key it densely (every 3 to 5 frames) and check the reach"""
    A, Bst = STYLES[a], STYLES[b]; _apply_pose(pose); P = pose_bones()
    ta, tb = _targets(P, A), _targets(P, Bst)
    mix = lambda x, y: x + (y - x) * w
    pole = mix(ta[2], tb[2]) if ta[2] is not None and tb[2] is not None else (tb[2] if w >= 0.5 else ta[2])
    return _arms_entry(mix(ta[0], tb[0]), mix(ta[1], tb[1]), pole, mix(ta[3], tb[3]))

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


def arms_on_floor(pose, x=0.30, reach=0.52, z=0.041):
    """a POST HOOK for lying exercises: both hands flat on the floor beside the body, `reach` metres from the shoulder toward the feet, palms down"""
    _apply_pose(pose); sh = pose_bones()["UpperArm.L"].head
    return {"Hand_IK.L": {"at": (x, sh.y - reach, z), "wrot": (0, 0, -90), "props": {"fist": 0.0}}, "Elbow_Pole.L": {"at": (x + 0.40, sh.y - 0.25, 0.15)}}


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

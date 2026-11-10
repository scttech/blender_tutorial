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
    "hips_fists": dict(frame="Hips", hand=(0.25, 0.05, 1.12), rot=(0, 90, 0), pole=(0.70, 0.20, 1.25), fist=1.0),
}

def _apply_pose(spec):
    clear_pose()
    for frame, flat in expand([(1, spec)], True):
        for c, v in flat.items(): write(c, v)
    rig.update_tag(); bpy.context.view_layer.update()

def ride_arms(pose, style):
    st = STYLES[style] if isinstance(style, str) else style
    _apply_pose(pose); P = pose_bones(); B = rig.data.bones[st["frame"]]
    D = P[st["frame"]].matrix.to_3x3() @ B.matrix_local.to_3x3().inverted()          # how far the part has turned from rest
    head_now, head_rest = P[st["frame"]].head.copy(), B.head_local.copy()
    place = lambda r: tuple(head_now + D @ (Vector(r) - head_rest))
    R = D @ Euler([math.radians(a) for a in st["rot"]], 'XYZ').to_matrix()
    out = {"Hand_IK.L": {"at": place(st["hand"]), "wrot": tuple(math.degrees(a) for a in R.to_euler('XYZ')), "props": {"fist": st["fist"]}}}
    if st.get("pole"): out["Elbow_Pole.L"] = {"at": place(st["pole"])}
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

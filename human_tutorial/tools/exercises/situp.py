"""situp.py - Step 14: the sit-up, as a keyframe table (see tools/anim_core.py). Floor work, lying on the back.

    G = {}; exec(open(".../anim_core.py").read(), G); exec(open(".../exercises/situp.py").read(), G)

Unlike the push-up the body does not turn as one stiff piece. Instead:
  * the pelvis (Hips) lies on the floor, then rolls up about the hips; the feet stay planted (Foot_IK is not keyed), knees bent
  * the spine curls forward, the neck follows
  * the arms are crossed on the chest: each hand and each elbow pole is RIDING ON THE TORSO, so its target is computed from where
    the torso is in every key (a two-pass build: pose the body, read the chest, place the hands)
  * the pelvis height is SETTLED against the mesh: after posing, the lowest vertex of the body is put on the floor, so nothing floats
    or sinks. Lying down is calibrated in the lying key, and again at every other key.
t runs from 0 (lying flat) to 1 (sitting up). 30 fps, a 2.6 s loop: 1.1 s up, 0.2 s at the top, 1.3 s down.
"""
import math
from mathutils import Vector, Matrix, Euler

Y_HIP, FOOT_DY = 0.10, 0.45               # the hips' y (the head lies toward +Y); the heels sit this far toward the feet
LAY_PHI, TOP_PHI = 90.0, 55.0             # pelvis angle: the Hips turn backwards by phi (90 = lying flat)
SPINE_TOP, NECK_TOP, HEAD_TOP = (20.0, 16.0, 12.0), 14.0, 8.0          # spine flexion at the top: 48 degrees in all
# hand offsets in the Spine2 bone's own frame (x = left, y = up the spine, z = forward from the chest): left hand low, right hand high
HAND_L, HAND_R = Vector((0.13, 0.04, 0.14)), Vector((-0.13, 0.10, 0.145))
ELBOW_POLE = Vector((0.50, -0.05, 0.02))


def _apply(spec):
    for frame, flat in expand([(1, spec)], True):
        for c, v in flat.items(): write(c, v)
    rig.update_tag(); bpy.context.view_layer.update()

def body_pose(t, hips_z, lay=LAY_PHI, top=TOP_PHI, spine=SPINE_TOP, neck=NECK_TOP, head=HEAD_TOP):
    """the body without its arms, at t (0 lying .. 1 sitting up). lay/top: the pelvis angle lying and at the top (a crunch keeps it at 90);
    spine, neck, head: the flexion at the top (degrees)"""
    phi = lay + (top - lay) * t
    s = lambda k: spine[k] * t
    return {"Hips": {"move": (0, Y_HIP - 0.06, hips_z - 0.97), "rot": (-phi, 0, 0)},
            "Spine": {"rot": (s(0), 0, 0)}, "Spine1": {"rot": (s(1), 0, 0)}, "Spine2": {"rot": (s(2), 0, 0)},
            "Neck": {"rot": (neck * t, 0, 0)}, "Head": {"rot": (head * t, 0, 0)},
            "Foot_IK.L": {"at": (0.19, Y_HIP - FOOT_DY, 0.10), "wrot": (0, 0, 0)},
            "Knee_Pole.L": {"at": (0.14, Y_HIP - FOOT_DY / 2, 1.0)}}

def settle(t, hips_z=0.11, **kw):
    """lower or raise the pelvis until the lowest vertex of the body just touches the floor"""
    reg_body = regions() == "body"
    for _ in range(3):
        _apply(body_pose(t, hips_z, **kw)); v, _ = mesh_state()
        hips_z -= float(v[reg_body, 2].min())
    return hips_z

def hand_frame(side):
    """the hand's frame in the Spine2 frame: palm onto the chest (-Z), fingers toward the opposite shoulder and a little up"""
    y = Vector((-0.9 if side == "L" else 0.9, 0.4, 0)).normalized(); z = Vector((0, 0, -1)); x = y.cross(z)
    return Matrix((x, y, z)).transposed()                    # columns x, y, z

def with_arms(t, spec):
    """second pass: read the chest from the posed body, then put the hands and elbow poles on it"""
    _apply(spec); S2 = pose_bones()["Spine2"].matrix                                # the chest's frame in the world (4x4)
    place = lambda v: tuple((S2 @ Vector((v.x, v.y, v.z, 1.0)))[:3])                # a point given in the chest's frame -> the world
    for side, off in (("L", HAND_L), ("R", HAND_R)):
        O = S2.to_3x3() @ hand_frame(side)                                          # the orientation we want for the hand, in the world
        Rw = O @ rig.data.bones[f"Hand_IK.{side}"].matrix_local.to_3x3().inverted()  # ... as a world rotation of the hand's rest frame
        spec[f"Hand_IK.{side}"] = {"at": place(off), "wrot": tuple(math.degrees(a) for a in Rw.to_euler('XYZ'))}
    spec["Elbow_Pole.L"] = {"at": place(ELBOW_POLE)}
    spec["Elbow_Pole.R"] = {"at": place(Vector((-ELBOW_POLE.x, ELBOW_POLE.y, ELBOW_POLE.z)))}
    return spec

def situp_pose(t):
    z = settle(t); spec = body_pose(t, z)
    return with_arms(t, spec), z

_poses = {t: situp_pose(t) for t in (0.0, 0.5, 1.0)}
HIPS_Z = {t: z for t, (spec, z) in _poses.items()}
SITUP = [(1, _poses[0.0][0]), (18, _poses[0.5][0]), (34, _poses[1.0][0]), (40, _poses[1.0][0]), (60, _poses[0.5][0]), (79, _poses[0.0][0])]


def curl_body(t, top=90.0, spine=(12.0, 10.0, 8.0), neck=8.0, head=6.0):
    """a lying curl, no arms, for text files: t = 0 flat, 1 = curled. `top` is the pelvis angle at t = 1 (90 keeps the pelvis flat, as in a crunch; 55 is a sit-up).
    The pelvis height is settled against the mesh so the body lies ON the floor"""
    kw = dict(top=top, spine=tuple(spine), neck=neck, head=head)
    return body_pose(t, settle(t, **kw), **kw)

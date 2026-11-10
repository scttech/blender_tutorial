"""mace.py - Step 16: the steel mace "10-to-2", as a keyframe table (see tools/anim_core.py).

    G = {"bpy": bpy}; exec(open(".../anim_core.py").read(), G); exec(open(".../exercises/mace.py").read(), G)      # G["MACE_10_TO_2"]

The PROP LEADS again: grab_mace = 1 for the whole loop, so both hands stay on the shaft, and the mace is the thing that moves. It is held
in front of the chest with a hammer grip (one hand above the other, see Step 12) and swings like a windscreen wiper in the frontal plane,
turning about the point between the hands: its head sweeps from 10 o'clock (to the character's left) to 2 o'clock (to the right).
gamma is the angle of the shaft from vertical about the front-back axis: +60 = 10 o'clock (head to the left), -60 = 2 o'clock.
The hands keep close to the chest, so they turn WITH the shaft (about 60 degrees of twist each way): the swap-grip twist of Step 15 again.
30 fps, a 2.0 s cycle: left, right, left. The body stays upright with the knees slightly soft.
"""
import math
import numpy as np
from mathutils import Vector, Matrix, Euler

PIVOT = Vector((0.0, -0.28, 1.28))        # the point between the hands, in the world: in front of the chest
GAMMA = 60.0                              # degrees either side of vertical
_b = rig.data.bones
_MACE0 = _b["Mace"].head_local.copy()
_MID = ((_b["Mace_Grip.L"].head_local + _b["Mace_Grip.R"].head_local) / 2) - _MACE0      # the hands' midpoint in the mace's own frame (at rest)

def mace_pose(gamma):
    """the mace turned by gamma about the front-back axis through the pivot, so that the hands' midpoint stays on the pivot"""
    R = Euler((0, math.radians(gamma), 0)).to_matrix()
    # the grip bones sit at their rest positions; the hands' midpoint is _MID + (the hand-to-handle offset) away, so use the grip midpoint itself
    origin = PIVOT - R @ _MID
    return {"Mace": {"at": tuple(origin), "wrot": (0, gamma, 0)},
            "Hand_IK.L": {"props": {"grab_mace": 1.0}},
            "Knee_Pole.L": {"at": tuple(_b["Knee_Pole.L"].head_local)}}

# gamma follows a cosine, keyed every 3 frames: with only the two extremes keyed, the point between the hands would RISE mid-swing, by 13.5 cm
# (a straight line between two positions on an arc passes inside it)
MACE_10_TO_2 = [(f, mace_pose(GAMMA * math.cos(2 * math.pi * (f - 1) / 30))) for f in range(1, 32, 3)]

def _seg_dist(p1, q1, p2, q2):
    """the shortest distance between two line segments (p1-q1 and p2-q2), numerically (50 samples each)"""
    a = np.array(p1)[None, :] + np.linspace(0, 1, 50)[:, None] * (np.array(q1) - np.array(p1))[None, :]
    b = np.array(p2)[None, :] + np.linspace(0, 1, 50)[:, None] * (np.array(q2) - np.array(p2))[None, :]
    return float(np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2).min())

def _arm_arm_clearance(P, radius=0.04):
    """how far the two arms are from each other (mm, minus two arm radii of 4 cm): negative = the arms pass through each other. The forearm and upper arm of one arm
    against the forearm of the other"""
    d = 1e9
    for a in ((P["UpperArm.L"].head, P["ForeArm.L"].head), (P["ForeArm.L"].head, P["ForeArm.L"].tail)):
        for b in ((P["UpperArm.R"].head, P["ForeArm.R"].head), (P["ForeArm.R"].head, P["ForeArm.R"].tail)):
            d = min(d, _seg_dist(a[0], a[1], b[0], b[1]))
    return 1000 * (d - 2 * radius)

def mace_extra():
    """per-frame measurements for measure(): the nearest the body gets to the shaft and to the head, the head's position, the shaft's angle"""
    reg = regions(); mace = bpy.data.objects["Mace"]
    def extra(P, f):
        M = mace.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world
        base, top, head = M @ Vector((0, 0, 0)), M @ Vector((0, 0, 1.04)), M @ Vector((0, 0, 1.0785))     # shaft, and the head's centre (radius 0.07)
        v, _ = mesh_state(); body = v[reg != "hands"]
        ab = np.array(top - base); s = np.clip(((body - np.array(base)) @ ab) / (ab @ ab), 0, 1)
        return {"clear_shaft_mm": 1000 * float(np.linalg.norm(body - (np.array(base) + np.outer(s, ab)), axis=1).min() - 0.0165),
                "clear_head_mm": 1000 * float(np.linalg.norm(body - np.array(head), axis=1).min() - 0.07),
                "arm_arm_mm": _arm_arm_clearance(P), "head_x": head.x, "head_z": head.z, "mace_tilt": math.degrees(math.atan2((top - base).x, (top - base).z))}
    return extra



def mace_behind(theta, px=0.0, py=0.12, pz=1.50, cross=0.0, cross_up=0.0, shift=0.0, swap_at=25.0):
    """the mace held with BOTH hands behind the neck and the head swinging behind the back (the real 10-to-2). The hands' midpoint is the pivot (px, py, pz);
    theta is where the head is: 0 = hanging straight down behind the back, +120 = at 10 o'clock (up and to the character's left), -120 = 2 o'clock.
    The mace is turned half a turn about the X axis (head down). That also puts the shaft BEHIND the hands: the grips sit 9 cm behind the shaft's
    axis otherwise, which would put the shaft inside the back. The Euler angles are written directly as (180, -theta, 0), which stays continuous
    through the whole swing (a matrix converted back to Euler angles would flip at the crossings)."""
    px = px + shift * max(0.0, math.sin(math.radians(theta)))        # swinging to the left: slide the hands toward the head's side, so the right hand does not pass to the left of the left hand
    eul = Euler((math.pi, -math.radians(theta), 0), 'XYZ'); R = eul.to_matrix()
    origin = Vector((px, py, pz)) - R @ _MID
    # When the head swings to the character's LEFT, the right hand (the one nearer the head) ends up to the left of the left hand: the arms cross. Keep them from passing
    # through each other by sending the left elbow low and the right elbow high while they cross, so one forearm goes under the other
    c = max(0.0, min(1.0, theta / 50.0))
    w = max(0.0, min(1.0, theta / swap_at))                    # 0 = the normal grips, 1 = the hands swapped (the head is on the left)
    return {"Mace": {"at": tuple(origin), "wrot": (180.0, -theta, 0.0)},
            "Hand_IK.L": {"props": {"grab_mace": 1.0 - w, "grab_mace_swap": w}}, "Elbow_Pole.L": {"at": (0.65, 0.10, 1.75 - cross * c)}, "Elbow_Pole.R": {"at": (-0.65, 0.10, 1.75 + cross_up * c)},
            "Knee_Pole.L": {"at": tuple(_b["Knee_Pole.L"].head_local)}}

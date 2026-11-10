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
                "head_x": head.x, "head_z": head.z, "mace_tilt": math.degrees(math.atan2((top - base).x, (top - base).z))}
    return extra


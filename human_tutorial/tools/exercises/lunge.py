"""lunge.py - Step 17: the static lunge (split squat). Built from tools/exercises/_template.py to prove the recipe.

    G = {"bpy": bpy}; exec(open(".../anim_core.py").read(), G); exec(open(".../exercises/lunge.py").read(), G)      # G["LUNGE"]

Technique: LEGS DRIVEN BY IK (Step 13) plus a rear foot that pivots on its toes (the push-up's trick, Step 14). Both feet stay put and the hips
drop. The front knee bend is what we ask for; the script SOLVES the hip height that gives it. The rear heel is lifted: the rear ankle target
rides a rigid motion about the ball of the foot and the toes bend back by the same angle, so they lie flat.
Fists on the hips: the hand and elbow targets ride on the hips, the fist slider is 1 and the hand points down against the hip. 30 fps, a 1.87 s loop: 0.83 s down, 0.27 s pause, 0.8 s up.
"""
import math
from mathutils import Vector

FOOT_X = 0.12                          # each foot this far to the side of the centre line
FRONT_ANKLE_Y = -0.45                  # the front foot's ankle
FRONT_ANKLE_Z = 0.1028                 # 10.28 cm, not the rest 10.00: with the knee nearly straight one heel vertex sank 2.7 mm (found by the floor check)
REAR_BALL = Vector((-FOOT_X, 0.30, 0.038))        # where the ball of the rear foot is planted. 3.8 cm: the push-up's 3.5 cm sank the toes 1.6 mm at this heel angle (found by the floor check)
REAR_HEEL = 55.0                       # degrees the rear heel is lifted (the foot turns about the ball)
KNEE_TOP, KNEE_BOTTOM = 18.0, 95.0     # the front knee's bend when standing tall in the split, and at the bottom
HIPS_Y = -0.07                         # the hips sit between the feet
HAND_ON_HIP = (0.25, 0.05, 1.12)       # the left wrist at the standing rest pose: on the side of the hip. The hand turns 90 degrees about Y so the fingers point down and the fist closes against the hip
ELBOW_OUT = (0.70, 0.20, 1.25)         # the left elbow pole: out to the side and a little back, so the elbow points outward (hands on hips)

_b = rig.data.bones
_H0 = _b["Hips"].head_local.copy()
_A0R, _BALL0R = _b["Foot_IK.R"].head_local.copy(), _b["Foot.R"].tail_local.copy()          # the rear ankle and ball at rest
_M = rigid(_BALL0R, REAR_BALL, REAR_HEEL)                                                    # the rear foot's rigid motion about its ball

def _apply(spec):
    for frame, flat in expand([(1, spec)], True):
        for c, v in flat.items(): write(c, v)
    rig.update_tag(); bpy.context.view_layer.update()

def lunge_pose(hips_z, shift=0.0, u=1.0, lift=0.0):
    """shift: slide the whole stance back by this much (0.525 puts the front foot back at rest: a REVERSE lunge, where the front foot never moves).
    u: how far the rear foot has stepped back (0 = beside the front foot, 1 = planted on its toes); lift: how high the rear foot is raised mid-step (m)"""
    hips_y = _H0.y + u * (HIPS_Y + shift - _H0.y)
    dy, dz = hips_y - _H0.y, hips_z - _H0.z                 # how far the hips have moved from rest: the hands ride on them
    ball = Vector((-FOOT_X, _BALL0R.y + u * (REAR_BALL.y + shift - _BALL0R.y), _BALL0R.z + u * (REAR_BALL.z - _BALL0R.z) + lift * 4 * u * (1 - u)))
    M = rigid(_BALL0R, ball, REAR_HEEL * u)                  # the rear foot's rigid motion about its ball
    return {"Hips": {"move": (0, dy, dz)},
            "Foot_IK.L": {"at": (FOOT_X, FRONT_ANKLE_Y + shift, FRONT_ANKLE_Z), "wrot": (0, 0, 0)}, "Knee_Pole.L": {"at": (FOOT_X + 0.02, FRONT_ANKLE_Y + shift - 0.5, 0.45)},
            "Foot_IK.R": {"at": tuple(M(_A0R)), "wrot": (REAR_HEEL * u, 0, 0)}, "Toes.R": {"rot": (-REAR_HEEL * u, 0, 0)},
            "Knee_Pole.R": {"at": (-FOOT_X, -0.30, 0.20)},
            "Hand_IK.L": {"at": (HAND_ON_HIP[0], HAND_ON_HIP[1] + dy, HAND_ON_HIP[2] + dz), "wrot": (0, 90, 0), "props": {"fist": 1.0}},     # a fist on the hip (the right mirrors the left)
            "Elbow_Pole.L": {"at": (ELBOW_OUT[0], ELBOW_OUT[1] + dy, ELBOW_OUT[2] + dz)}}

def _front_knee(hips_z, shift=0.0):
    _apply(lunge_pose(hips_z, shift)); P = pose_bones()
    th = (P["Thigh.L"].tail - P["Thigh.L"].head).normalized(); sh = (P["Shin.L"].tail - P["Shin.L"].head).normalized()
    return math.degrees(th.angle(sh))

def solve_hips_z(knee, shift=0.0):
    """the hip height at which the front knee is bent by `knee` degrees (it bends more as the hips drop)"""
    lo, hi = 0.30, 0.97
    for _ in range(22):
        mid = (lo + hi) / 2
        if _front_knee(mid, shift) > knee: lo = mid
        else: hi = mid
    return (lo + hi) / 2

Z_TOP, Z_BOTTOM = solve_hips_z(KNEE_TOP), solve_hips_z(KNEE_BOTTOM)
LUNGE = [(1, lunge_pose(Z_TOP)), (25, lunge_pose(Z_BOTTOM)), (33, lunge_pose(Z_BOTTOM)), (57, lunge_pose(Z_TOP))]


_KNEE_CACHE = {}
def _solved(knee, shift):
    if (knee, shift) not in _KNEE_CACHE: _KNEE_CACHE[(knee, shift)] = solve_hips_z(knee, shift)
    return _KNEE_CACHE[(knee, shift)]

def lunge_at_knee(knee):
    """the lunge's hips and legs (no arms) with the front knee bent by `knee` degrees: the hip height is solved, as in the table above"""
    p = lunge_pose(_solved(knee, 0.0))
    for k in ("Hand_IK.L", "Elbow_Pole.L"): p.pop(k)
    return p

def reverse_lunge(u, knee, lift=0.14, step=0.525):
    """a reverse lunge, no arms. u: 0 = standing, 1 = stepped back and planted (the front knee bent by `knee` degrees, hips at the height that gives it).
    The hips sink as the rear foot steps back; `lift` is how high the rear foot rises mid-step"""
    z = _H0.z + u * (_solved(knee, step) - _H0.z)
    p = lunge_pose(z, step, u, lift)
    for k in ("Hand_IK.L", "Elbow_Pole.L"): p.pop(k)
    return p

"""lunge.py - Step 17: the static lunge (split squat). Built from tools/exercises/_template.py to prove the recipe.

    G = {"bpy": bpy}; exec(open(".../anim_core.py").read(), G); exec(open(".../exercises/lunge.py").read(), G)      # G["LUNGE"]

Technique: LEGS DRIVEN BY IK (Step 13) plus a rear foot that pivots on its toes (the push-up's trick, Step 14). Both feet stay put and the hips
drop. The front knee bend is what we ask for; the script SOLVES the hip height that gives it. The rear heel is lifted: the rear ankle target
rides a rigid motion about the ball of the foot and the toes bend back by the same angle, so they lie flat.
Arms hang at the sides, the hand targets following the hips. 30 fps, a 1.87 s loop: 0.83 s down, 0.27 s pause, 0.8 s up.
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

_b = rig.data.bones
_H0 = _b["Hips"].head_local.copy()
_A0R, _BALL0R = _b["Foot_IK.R"].head_local.copy(), _b["Foot.R"].tail_local.copy()          # the rear ankle and ball at rest
_M = rigid(_BALL0R, REAR_BALL, REAR_HEEL)                                                    # the rear foot's rigid motion about its ball

def _apply(spec):
    for frame, flat in expand([(1, spec)], True):
        for c, v in flat.items(): write(c, v)
    rig.update_tag(); bpy.context.view_layer.update()

def lunge_pose(hips_z):
    return {"Hips": {"move": (0, HIPS_Y - _H0.y, hips_z - _H0.z)},
            "Foot_IK.L": {"at": (FOOT_X, FRONT_ANKLE_Y, FRONT_ANKLE_Z), "wrot": (0, 0, 0)}, "Knee_Pole.L": {"at": (FOOT_X + 0.02, FRONT_ANKLE_Y - 0.5, 0.45)},
            "Foot_IK.R": {"at": tuple(_M(_A0R)), "wrot": (REAR_HEEL, 0, 0)}, "Toes.R": {"rot": (-REAR_HEEL, 0, 0)},
            "Knee_Pole.R": {"at": (-FOOT_X, -0.30, 0.20)},
            "Hand_IK.L": {"at": (0.27, -0.02, hips_z)}}                                  # the hands hang at hip height (the right mirrors the left)

def _front_knee(hips_z):
    _apply(lunge_pose(hips_z)); P = pose_bones()
    th = (P["Thigh.L"].tail - P["Thigh.L"].head).normalized(); sh = (P["Shin.L"].tail - P["Shin.L"].head).normalized()
    return math.degrees(th.angle(sh))

def solve_hips_z(knee):
    """the hip height at which the front knee is bent by `knee` degrees (it bends more as the hips drop)"""
    lo, hi = 0.30, 0.97
    for _ in range(22):
        mid = (lo + hi) / 2
        if _front_knee(mid) > knee: lo = mid
        else: hi = mid
    return (lo + hi) / 2

Z_TOP, Z_BOTTOM = solve_hips_z(KNEE_TOP), solve_hips_z(KNEE_BOTTOM)
LUNGE = [(1, lunge_pose(Z_TOP)), (25, lunge_pose(Z_BOTTOM)), (33, lunge_pose(Z_BOTTOM)), (57, lunge_pose(Z_TOP))]

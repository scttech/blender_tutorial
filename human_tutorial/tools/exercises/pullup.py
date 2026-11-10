"""pullup.py - Step 15: the pull-up (overhand grip) and the chin-up (underhand grip), as keyframe tables (see tools/anim_core.py).

    G = {}; exec(open(".../anim_core.py").read(), G); exec(open(".../exercises/pullup.py").read(), G)     # G["PULLUP"], G["CHINUP"]

The hands are fixed to the bar (grab_bar_over / grab_bar_under = 1, so each hand control is snapped to a grip bone on the bar frame) and
the BODY moves. The legs simply hang: the foot targets and knee poles are keyed to travel with the hips, so no IK/FK switch is needed.
Two heights are SOLVED against the rig and the mesh, not guessed:
    dead hang   the lowest lift at which the straight arm still reaches the bar
    the top     the lift that puts the chin 30 mm above the bar
and a rise parameter t (0 = hang, 1 = top) moves the hips up, forward and into a slight lean, and extends the spine and head.
30 fps, a 3.3 s loop: 1.5 s up, 0.2 s at the top, 1.6 s down.
"""
import math
import numpy as np
from mathutils import Vector

BAR_Y, BAR_Z, BAR_R = -0.17, 2.30, 0.016            # the frame stands at y = -0.17; the bar is 2.30 m up, 32 mm across
CHIN_OVER = 0.030                                    # the chin ends this far above the top of the bar
# per grip: slider, forward shift of the hips at the top, lean back of the hips at the top (degrees)
GRIPS = {"pullup": ("grab_bar_over", -0.10, -6.0), "chinup": ("grab_bar_under", -0.12, -8.0)}
SPINE_TOP, NECK_TOP, HEAD_TOP = (-5.0, -5.0, -4.0), -6.0, -8.0       # extension at the top (negative = bending backward). A first try with -10 and -15 tipped the head back to look at the ceiling

_b = rig.data.bones
_H0, _A0, _KP0 = (_b[n].head_local.copy() for n in ("Hips", "Foot_IK.L", "Knee_Pole.L"))
_HEAD = torso_masks()[1]

def _apply(spec):
    for frame, flat in expand([(1, spec)], True):
        for c, v in flat.items(): write(c, v)
    rig.update_tag(); bpy.context.view_layer.update()

def rise_pose(grip, lift, t):
    """the body at rise t (0 = hanging, 1 = top) with the hips lifted by `lift` metres"""
    slider, dy_top, lean_top = GRIPS[grip]
    move = Vector((0.0, dy_top * t, lift)); lean = lean_top * t
    M = rigid(_H0, _H0 + move, lean)                       # the legs swing with the hips: the ankles and knee poles ride the same motion
    return {"Hips": {"move": tuple(move), "rot": (lean, 0, 0)},
            "Spine": {"rot": (SPINE_TOP[0] * t, 0, 0)}, "Spine1": {"rot": (SPINE_TOP[1] * t, 0, 0)}, "Spine2": {"rot": (SPINE_TOP[2] * t, 0, 0)},
            "Neck": {"rot": (NECK_TOP * t, 0, 0)}, "Head": {"rot": (HEAD_TOP * t, 0, 0)},
            "Foot_IK.L": {"at": tuple(M(_A0)), "wrot": (lean, 0, 0)}, "Knee_Pole.L": {"at": tuple(M(_KP0))},
            "Hand_IK.L": {"props": {"grab_bar_over": 0.0, "grab_bar_under": 0.0, slider: 1.0}}}      # set BOTH sliders: a stale one would blend in

def _reach_error(spec):
    _apply(spec); P = pose_bones()
    return max((P[f"ForeArm.{s}"].tail - P[f"Hand_IK.{s}"].head).length for s in "LR") * 1000

def _chin_height(spec):
    _apply(spec); v, _ = mesh_state(); return float(v[_HEAD, 2].min()) - (BAR_Z + BAR_R)

def _bisect(f, lo, hi, want_increasing_hits, n=20):
    for _ in range(n):
        mid = (lo + hi) / 2
        if want_increasing_hits(f(mid)): hi = mid
        else: lo = mid
    return (lo + hi) / 2

def solve(grip):
    # dead hang: the smallest lift at which the arm reaches (error below 0.03 mm), plus 1 mm
    hang = _bisect(lambda z: _reach_error(rise_pose(grip, z, 0.0)), 0.20, 0.40, lambda e: e < 0.03) + 0.001
    # top: the lift at which the chin is CHIN_OVER above the bar
    top = _bisect(lambda z: _chin_height(rise_pose(grip, z, 1.0)), 0.40, 1.00, lambda c: c >= CHIN_OVER)
    return hang, top

def table(grip):
    hang, top = solve(grip); mid = (hang + top) / 2
    P = lambda lift, t: rise_pose(grip, lift, t)
    return [(1, P(hang, 0.0)), (24, P(mid, 0.5)), (46, P(top, 1.0)), (52, P(top, 1.0)), (76, P(mid, 0.5)), (100, P(hang, 0.0))], hang, top

PULLUP, LIFT_HANG, LIFT_TOP = table("pullup")
CHINUP, LIFT_HANG_CHIN, LIFT_TOP_CHIN = table("chinup")

def bar_extra(grip_prefix):
    """extra per-frame measurements for measure(): the chin against the bar, the nearest part of the body to the bar's surface (the hands
    excluded, they hold it), and how far each hand control is from its grip bone"""
    reg = regions()
    def extra(P, f):
        v, _ = mesh_state(); d = np.hypot(v[:, 1] - BAR_Y, v[:, 2] - BAR_Z) - BAR_R
        return {"chin_over_mm": 1000 * float(v[_HEAD, 2].min() - (BAR_Z + BAR_R)), "bar_clear_mm": 1000 * float(d[reg != "hands"].min()),
                "grip_err_mm": 1000 * max((P[f"Hand_IK.{s}"].head - P[f"{grip_prefix}.{s}"].head).length for s in "LR"),
                "wrist_y": P["Hand.L"].head.y, "wrist_z": P["Hand.L"].head.z, "shoulder_z": P["UpperArm.L"].head.z}
    return extra


"""carry.py - walking in place (a gait cycle) for the farmer's carry. Loaded with  python = ["poselib.py", "dumbbell.py", "carry.py"]. It uses only anim_core's rigid and the rig's own bones, so
nothing here is tied to one body's size: every length is read from the rig (the model for a second body should need no change).

The loop is a treadmill walk: the body stays put and the planted foot slides back, as the body would move over it. One cycle is two steps (left, right).
"""
import math
from mathutils import Vector, Euler

def _leg_metrics():
    b = rig.data.bones; T = b["Thigh.L"].head_local; A = b["Foot_IK.L"].head_local; B = Vector((0.0, b["Foot.L"].tail_local.y, b["Foot.L"].tail_local.z))
    return T.copy(), A.copy(), B, (T - A).length        # the hip joint, the ankle, the ball of the foot (all at rest) and the leg's length (hip to ankle)

def _foot_phase(ph, stance=0.58):
    """-> (y_fraction, z_lift_fraction, heel_fraction) for one foot at phase ph in 0..1 (0 = heel strike). y_fraction: +1 the foot far back, -1 far forward. Stance: the foot slides from forward to back on the
    floor, the heel rising for the last third; swing: it lifts and comes forward again."""
    ease = lambda x: 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, x)))
    if ph < stance:
        u = ph / stance; heel = max(0.0, (u - 0.62) / 0.38) ** 1.3
        return -1.0 + 2.0 * u, 0.0, heel
    u = (ph - stance) / (1.0 - stance)
    return 1.0 - 2.0 * ease(u), math.sin(math.pi * u) ** 0.8, max(0.0, 1.0 - u * 3.0)

def walk_cycle(s, stride=0.62, lift=0.13, heel=35.0, bend=0.97, sway=0.012, stance=0.58, lean=0.0, bob=0.0):
    """walking in place. s runs 0..2: s = 0 the LEFT foot just struck (forward), 1 the right foot just struck, 2 the same as 0. stride: the distance between the feet at double support (m); lift: the swing
    foot's clearance (m); heel: the heel's lift at toe-off (degrees); bend: the share of the leg's length the hips keep (below 1 the knees stay a little bent). No arms."""
    T, A0, B0, L = _leg_metrics(); out = {}; foot_x = A0.x * 0.75
    hip_min = 9.0; ph0 = (s / 2.0) % 1.0
    for side, ph in (("L", ph0), ("R", (ph0 + 0.5) % 1.0)):
        sgn = 1 if side == "L" else -1
        yf, zf, hf = _foot_phase(ph, stance)
        ang = heel * hf; ball = Vector((sgn * foot_x, B0.y + yf * stride / 2, B0.z + 0.003 + lift * zf))
        ank = rigid(B0, ball, ang)(Vector((0.0, A0.y, A0.z))); ank = Vector((sgn * foot_x, ank.y, ank.z))
        out[f"Foot_IK.{side}"] = {"at": tuple(ank), "wrot": (ang, 0, 0)}; out[f"Toes.{side}"] = {"rot": (-ang, 0, 0)}
        out[f"Knee_Pole.{side}"] = {"at": (sgn * (foot_x + 0.02), ank.y - 0.5, 0.45 + lift * zf)}
        if zf < 0.05:                                              # a foot on the floor limits how high the hips can be
            dx, dy = sgn * T.x - sgn * foot_x, T.y - ank.y
            hip_min = min(hip_min, ank.z + math.sqrt(max(0.0, (bend * L) ** 2 - dx * dx - dy * dy)))
    free = A0.z + bend * L - 0.02                                   # no foot on the floor (a run's flight): the hips are as high as the legs allow, less a little
    if bob:                                                         # a run: the hips bob (lowest at mid-stance, highest in flight), never higher than the planted leg allows
        want = free - bob * 0.5 * (1 + math.cos(4 * math.pi * ph0)); hip_min = min(hip_min, want) if hip_min < 8 else want
    elif hip_min > 8: hip_min = free
    dz = hip_min - T.z
    out["Hips"] = {"move": (sway * math.sin(math.pi * s), 0.0, dz), "rot": (lean, 0, 0)}
    if lean: out["Neck"] = {"rot": (-lean * 0.5, 0, 0)}; out["Head"] = {"rot": (-lean * 0.5, 0, 0)}
    return out


def march(s, alpha=70.0, bob=0.0, sway=0.01):
    """marching or high knees in place: the weight on one leg, the other thigh raised forward `alpha` degrees with the shin hanging straight down; s runs 0..2 (left knee up at s = 0.5, right at 1.5).
    bob: how far the hips drop between the steps (a bounce for high knees)"""
    T, A0, B0, L = _leg_metrics(); out = {}; foot_x = A0.x * 0.75
    ease = lambda x: 0.5 - 0.5 * math.cos(math.pi * x)
    ua = (rig.data.bones["Thigh.L"].tail_local - T).length; la = L - ua                        # thigh and shin (approximately: hip to ankle is the whole leg)
    for side, off in (("L", 0.0), ("R", 1.0)):
        sgn = 1 if side == "L" else -1; u = ((s - off) % 2.0) / 2.0                             # 0..1 over the step pair
        k = math.sin(math.pi * min(1.0, u * 2.0)) if u < 0.5 else 0.0                           # the knee is up during the first half of this leg's turn
        k = ease(k) if k > 0 else 0.0; a = math.radians(alpha) * k
        hip = Vector((sgn * T.x, T.y, T.z - bob * 0.5 * (1 + math.cos(2 * math.pi * s))))
        ank = hip + Vector((0.0, -ua * math.sin(a), -ua * math.cos(a) - la * 0.98))
        if k == 0: ank = Vector((hip.x, A0.y, A0.z))
        ank = Vector((sgn * foot_x, max(ank.y, A0.y - 0.5) if k else A0.y, max(A0.z, ank.z)))
        out[f"Foot_IK.{side}"] = {"at": tuple(ank), "wrot": (-30.0 * k, 0, 0)}; out[f"Knee_Pole.{side}"] = {"at": (sgn * (foot_x + 0.02), ank.y - 0.6, ank.z + 0.5)}
    out["Hips"] = {"move": (sway * math.sin(math.pi * s), 0.0, -bob * 0.5 * (1 + math.cos(2 * math.pi * s)) - 0.01), "rot": (0, 0, 0)}
    return out

def arm_swing(pose, s, amp=30.0, bend=15.0, fist=0.3, per=2.0):
    """a POST HOOK: the arms swing opposite to the legs, in the sagittal plane, the elbow bent `bend` degrees (a run: 90). s as in walk_cycle (the left foot forward at s = 0, so the right arm is
    forward); per = how many steps per cycle of the arm swing (2.0: a cycle is the two steps). Both arms are written out explicitly (they are not mirrors of each other)"""
    _apply_pose(pose); P = pose_bones(); out = {}; b = rig.data.bones
    UA = (b["UpperArm.L"].tail_local - b["UpperArm.L"].head_local).length; FA = 0.95 * (b["Hand.L"].head_local - b["UpperArm.L"].head_local).length - UA
    for side in "LR":
        sg = 1 if side == "L" else -1; th = math.radians(-amp * math.cos(math.pi * s * 2 / per) * sg)           # the left arm is back when the left foot is forward
        be = math.radians(bend * (1.0 + 0.3 * math.sin(math.pi * s * 2 / per * 2)) if bend > 30 else bend)
        S = P[f"UpperArm.{side}"].head.copy()
        E = S + Vector((sg * 0.02, -UA * math.sin(th), -UA * math.cos(th))); ph = th + be
        W = E + Vector((0.0, -FA * math.sin(ph), -FA * math.cos(ph)))
        R = Euler((-ph, 0, 0)).to_matrix() @ Euler((0, math.pi / 2, 0)).to_matrix()
        e = R.to_euler('XYZ'); rot = [math.degrees(x) for x in e]
        if side == "R": rot = [rot[0], -rot[1], -rot[2]]
        out[f"Hand_IK.{side}"] = {"at": tuple(W), "wrot": tuple(rot), "props": {"fist": fist}}
        out[f"Elbow_Pole.{side}"] = {"at": (S.x + sg * 0.3, S.y + 0.6, S.z - 0.1)}
    return out

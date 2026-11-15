"""manmaker.py - the Man Maker and the Devil's Press: burpees with a dumbbell in each hand. Loaded with  python = ["moves.py", "pushup.py", "poselib.py", "dumbbell.py", "manmaker.py"].

The body is the burpee's (moves.py: stand, crouch, plank, push-up bottom; kick the feet back and in), with the hands raised onto the dumbbells standing on the floor, so the plank is higher than the plain burpee's.
Everything that depends on the body's size is read from the rig (arm length, upper arm, plate radius), so a second model with other proportions should need no change here. The ARMS are placed from the shoulders
(the way db_row and db_hang do): a mode and a number say where the wrist goes, and dumbbell.hold() puts the weight and hand there.
  hang       arm straight down from the shoulder                    plant   the hand stays where it was planted on the floor
  row a      the elbow raised back by a degrees, forearm vertical   swing t  the straight arm swung forward t degrees (180 = overhead)
  clean u    from hanging to the rack at the shoulders (u 0..1)     press h  from the rack (h 0) to overhead (h 1)
"""
import math
from mathutils import Vector

_C = {}
def _cfg():
    if _C: return _C
    b = rig.data.bones; S = b["UpperArm.L"].head_local; W = b["Hand.L"].head_local
    _C["UA"] = (b["UpperArm.L"].tail_local - S).length                 # the upper arm
    _C["REACH"] = 0.96 * (W - S).length; _C["ARM"] = 0.95 * (W - S).length                                  # shoulder to wrist, a little short of straight
    ob = bpy.data.objects["Dumbbell.L"]; _C["DBR"] = sorted(ob.dimensions)[1] / 2.0          # the plate's radius (the middle one of the three sizes)
    _C["DBZ"] = _C["DBR"] + 0.091                                      # wrist height with the dumbbell standing on the floor and gripped from above (the grip's wrist offset: 9.1 cm)
    _C["XO"] = 0.065                                                   # the wrist is this far outside the shoulder when the arm hangs (the weight clears the thigh)
    # the push-up body with the hands raised onto the dumbbells: find the angle at which the shoulders are one arm's length above the raised hands
    global HAND_Z, _HAND_Y
    keep = (HAND_Z, _HAND_Y)
    sz_up = rigid(_B0, (0, Y_PIVOT, Z_PIVOT), PHI_UP)(_S0).z; arm_v = sz_up - HAND_Z
    lo, hi = 40.0, PHI_UP
    for _ in range(40):
        mid = (lo + hi) / 2
        if rigid(_B0, (0, Y_PIVOT, Z_PIVOT), mid)(_S0).z > _C["DBZ"] + arm_v: lo = mid
        else: hi = mid
    phi = (lo + hi) / 2; _C["PHI_UP"] = phi; _C["ARM_V"] = arm_v
    try:
        HAND_Z = _C["DBZ"]; _HAND_Y = rigid(_B0, (0, Y_PIVOT, Z_PIVOT), phi)(_S0).y
        x = _S0.x + _C["XO"]
        PLANK, DOWN = pushup_pose(phi, hand_x=x, pole_out=0.45), pushup_pose(PHI_DN, hand_x=x, pole_out=0.45)
    finally:
        HAND_Z, _HAND_Y = keep
    for p in (PLANK, DOWN): p.setdefault("Spine", {"rot": (0, 0, 0)}); p.setdefault("Spine1", {"rot": (0, 0, 0)}); p.setdefault("Spine2", {"rot": (0, 0, 0)})
    hand = PLANK["Hand_IK.L"]["at"]; ph = math.radians(75.0)
    CROUCH = _stand_pose(); CROUCH.pop("Hand_IK.L"); CROUCH.pop("Elbow_Pole.L")
    CROUCH["Hips"] = {"move": (0, hand[1] + 0.48 * math.sin(ph) - 0.06, _C["DBZ"] + arm_v - 0.48 * math.cos(ph) - 0.97), "rot": (75.0, 0, 0)}
    CROUCH["Neck"] = {"rot": (-18, 0, 0)}; CROUCH["Head"] = {"rot": (-28, 0, 0)}
    STAND = _stand_pose(); STAND.pop("Hand_IK.L"); STAND.pop("Elbow_Pole.L")
    for p in (PLANK, DOWN): p.pop("Hand_IK.L")
    _C.update(STAND=STAND, CROUCH=CROUCH, PLANK=PLANK, DOWN=DOWN, PLANT=Vector((hand[0], hand[1], _C["DBZ"])))
    return _C

def _unit(v): return Vector(v).normalized()
def _grip(W, S, f, n, pole):
    f = _unit(f); n = Vector(n); n = _unit(n - f * n.dot(f))
    return hold(W, f, n, pole=pole)

def _arms(body, mode, a=0.0):
    """the dumbbell, hand and elbow pole for a mode (see the module doc), from the shoulder of the posed body"""
    C = _cfg(); _apply_pose(body); S = pose_bones()["UpperArm.L"].head.copy(); XO, ARM, UA = C["XO"], C["ARM_V"], C["UA"]
    side = lambda y, z, x=0.3: (S.x + x, S.y + y, S.z + z)
    IN = (-1, 0, 0)
    if mode == "hang":
        W = S + Vector((XO, 0, -ARM))
        if (W - S).length > C["REACH"]: W = S + (W - S).normalized() * C["REACH"]
        return _grip(W, S, W - S, IN, side(0.6, -0.15))
    if mode == "plant":
        W = C["PLANT"].copy(); d = W - S
        if d.length > C["REACH"]: W = S + d.normalized() * C["REACH"]       # while the feet kick the shoulders rise a little: the dumbbell lifts a centimetre or two rather than the arm stretching
        return _grip(W, S, W - S, IN, body["Elbow_Pole.L"]["at"] if "Elbow_Pole.L" in body else side(0.45, 0.0, 0.45))
    if mode == "row":
        r = math.radians(a); W = S + Vector((XO, UA * math.sin(r), -UA * math.cos(r) - (ARM - UA))); return _grip(W, S, (0, 0, -1), IN, side(0.5, 0.0, 0.5))
    if mode == "swing":
        t = math.radians(a); f = (0, -math.sin(t), -math.cos(t)); W = S + Vector((XO, -ARM * math.sin(t), -ARM * math.cos(t)))
        if (W - S).length > C["REACH"]: W = S + (W - S).normalized() * C["REACH"]
        return _grip(W, S, f, IN, side(0.55, 0.05 if a < 90 else 0.3))
    rack = lambda h: S + Vector((0.14 - 0.12 * h, -0.11 + 0.05 * h, 0.12 + 0.34 * h))
    if mode == "clean":                                     # hanging -> rack: the wrist travels in a straight line, the forearm turns from down to up through the front, the palm from in to toward the face
        u = a; W0 = S + Vector((XO, 0, -ARM)); W = W0 + (rack(0) - W0) * u; r = math.pi * u
        f = (0, -math.sin(r), -math.cos(r)); n0 = Vector(IN); n1 = Vector((0, 1, 0)); n = n0 * (1 - u) + n1 * u
        return _grip(W, S, f, n, side(0.45 - 0.2 * u, -0.1 * u, 0.3 + 0.4 * u))
    if mode == "press":                                     # rack -> overhead: the palms turn from toward the face to facing in
        h = a; n = (-math.sin(math.pi / 2 * h), math.cos(math.pi / 2 * h), 0); return _grip(rack(h), S, (0, 0, 1), n, side(0.04, -0.1 + 0.15 * h, 0.71 - 0.35 * h))
    raise ValueError(mode)

def _mir(d):
    """the right-side copy of a left-side arm (names .L -> .R, x negated, the y and z turns negated): used when the two arms do different things"""
    out = {}
    for k, v in d.items():
        o = dict(v)
        if "at" in o: o["at"] = (-o["at"][0], o["at"][1], o["at"][2])
        if "wrot" in o: o["wrot"] = (o["wrot"][0], -o["wrot"][1], -o["wrot"][2])
        out[k.replace(".L", ".R")] = o
    return out

def _ease(x): return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, x)))

def _burpee_body(f, C, air=0.18):
    """the body for frames 1..81 of both exercises (stand, drop to the dumbbells, kick back, push-up, kick in) -> (body, arm mode, number)"""
    STAND, CROUCH, PLANK, DOWN = C["STAND"], C["CROUCH"], C["PLANK"], C["DOWN"]
    def seg(a, b, A, B, kick=0.0):
        w = _ease((f - a) / (b - a)); p = blend_pose(A, B, w)
        if kick:
            m = math.sin(math.pi * w); fk = p["Foot_IK.L"]["at"]; p["Foot_IK.L"] = {**p["Foot_IK.L"], "at": (fk[0], fk[1], fk[2] + kick * m)}
            mv = p["Hips"]["move"]; p["Hips"] = {**p["Hips"], "move": (mv[0], mv[1], mv[2] + HIP_LIFT * m)}
        return p
    if f <= 13: return seg(1, 13, STAND, CROUCH), "hang", 0
    if f <= 19: return CROUCH, "hang", 0
    if f <= 25: return seg(19, 25, CROUCH, PLANK, air), "plant", 0
    if f <= 31: return seg(25, 31, PLANK, DOWN), "plant", 0
    if f <= 37: return DOWN, "plant", 0
    if f <= 43: return seg(37, 43, DOWN, PLANK), "plant", 0
    return PLANK, "plant", 0

def devils_press(f):
    """the Devil's Press over 113 frames: stand with the dumbbells hanging (1), drop to them (13), kick back to a plank (25), chest to the floor (31), push up (43), kick the feet in (51), then stand up
    swinging both dumbbells forward and up in one motion (51-75, arms straight, overhead at 75), hold (83), lower them to the hang (107), settle (113)"""
    C = _cfg()
    if f <= 43: body, mode, a = _burpee_body(f, C)
    elif f <= 51:
        w = _ease((f - 43) / 8.0); body = blend_pose(C["PLANK"], C["CROUCH"], w); m = math.sin(math.pi * w); fk = body["Foot_IK.L"]["at"]
        body["Foot_IK.L"] = {**body["Foot_IK.L"], "at": (fk[0], fk[1], fk[2] + 0.18 * m)}; mv = body["Hips"]["move"]; body["Hips"] = {**body["Hips"], "move": (mv[0], mv[1], mv[2] + HIP_LIFT * m)}
        mode, a = ("plant", 0) if f < 51 else ("hang", 0)
    elif f <= 75:
        w = _ease((f - 51) / 24.0); body = blend_pose(C["CROUCH"], C["STAND"], w); mode, a = "swing", 180.0 * _ease((f - 51) / 24.0)
    elif f <= 83: body = C["STAND"]; mode, a = "swing", 180.0
    elif f <= 107: body = C["STAND"]; mode, a = "swing", 180.0 * (1 - _ease((f - 83) / 24.0))
    else: body = C["STAND"]; mode, a = "hang", 0
    body = {k: v for k, v in body.items() if k not in ("Hand_IK.L", "Elbow_Pole.L")}
    return {**body, **_arms(body, mode, a)}

def man_maker(f):
    """the Man Maker over 160 frames: stand with the dumbbells hanging (1), drop to them (13), kick back to a plank (25), a push-up (31 down, 43 up), a row with the left arm (49-58) and the right (64-73),
    kick the feet in (81), stand up (93), clean the dumbbells to the shoulders (105), press them overhead (123), hold (129), lower to the shoulders (147), lower to the hang (159)"""
    C = _cfg(); row = lambda a, b: 75.0 * math.sin(math.pi * _ease((f - a) / (b - a)))
    if f <= 43: body, mode, a = _burpee_body(f, C)
    elif f <= 73:
        body, mode, a = C["PLANK"], "plant", 0
    elif f <= 81:
        w = _ease((f - 73) / 8.0); body = blend_pose(C["PLANK"], C["CROUCH"], w); m = math.sin(math.pi * w); fk = body["Foot_IK.L"]["at"]
        body["Foot_IK.L"] = {**body["Foot_IK.L"], "at": (fk[0], fk[1], fk[2] + 0.18 * m)}; mv = body["Hips"]["move"]; body["Hips"] = {**body["Hips"], "move": (mv[0], mv[1], mv[2] + HIP_LIFT * m)}
        mode, a = ("plant", 0) if f < 81 else ("hang", 0)
    elif f <= 93: body = blend_pose(C["CROUCH"], C["STAND"], _ease((f - 81) / 12.0)); mode, a = "hang", 0
    else: body = C["STAND"]; mode, a = "hang", 0
    if f > 93:
        if f <= 105: mode, a = "clean", _ease((f - 93) / 12.0)
        elif f <= 123: mode, a = "press", _ease((f - 105) / 18.0)
        elif f <= 129: mode, a = "press", 1.0
        elif f <= 147: mode, a = "press", 1.0 - _ease((f - 129) / 18.0)
        elif f <= 159: mode, a = "clean", 1.0 - _ease((f - 147) / 12.0)
    body = {k: v for k, v in body.items() if k not in ("Hand_IK.L", "Elbow_Pole.L")}
    arms = _arms(body, mode, a)
    if 43 < f <= 73 and (49 <= f <= 58 or 64 <= f <= 73):          # a row: the working arm rows while the other holds the plank (left, then right)
        left = f <= 58; plant = _arms(body, "plant"); working = _arms(body, "row", row(49, 58) if left else row(64, 73))
        arms = {**working, **_mir(plant)} if left else {**plant, **_mir(working)}
    return {**body, **arms}

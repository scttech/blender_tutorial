"""moves.py - parametric body motions for exercises written as text: generators that return the legs, hips and spine (no arms, no props).
Loaded with  python = "moves.py"  (after anim_core). All distances in metres, angles in degrees, feet planted (the Foot_IK controls stay at rest).

hinge_body(t, back, drop, pitch, spine, neck, head)    t = 0 standing, 1 = the hinge's bottom: the hips go back and down and the torso tips forward.
squat_body(t, depth, back, lean)                       the squat's body, t = 0 standing .. 1 = the bottom
"""
def _lerp(a, b, t): return a + (b - a) * t

def hinge_body(t, back=0.30, drop=0.40, pitch=40.0, spine=(6.0, 5.0, 4.0), neck=-14.0, head=-18.0, stance=None):
    """a hip hinge / deadlift. pitch: how far the pelvis tips forward (the spine stays straight: the spine bones add `spine` degrees of lean);
    neck and head turn the other way so the eyes look ahead and down"""
    pose = {"Hips": {"move": (0, back * t, -drop * t), "rot": (pitch * t, 0, 0)},
            "Spine": {"rot": (spine[0] * t, 0, 0)}, "Spine1": {"rot": (spine[1] * t, 0, 0)}, "Spine2": {"rot": (spine[2] * t, 0, 0)},
            "Neck": {"rot": (neck * t, 0, 0)}, "Head": {"rot": (head * t, 0, 0)}}
    if stance:                                   # feet this far either side of the centre (the rest stance is 0.19): a wider stance leaves room between the legs for the arms
        b = rig.data.bones; A0, P0 = b["Foot_IK.L"].head_local, b["Knee_Pole.L"].head_local
        pose["Foot_IK.L"] = {"at": (stance, A0.y, A0.z), "wrot": (0, 0, 0)}; pose["Knee_Pole.L"] = {"at": (stance + 0.08, P0.y, P0.z)}
        T0 = b["Thigh.L"].head_local; dz = A0.z + math.sqrt(0.86 ** 2 - (stance - T0.x) ** 2) - T0.z       # wide feet are further from the hip joint: lower the hips so the legs still reach (0.86 m, just short of straight)
        mv = pose["Hips"]["move"]; pose["Hips"]["move"] = (mv[0], mv[1], mv[2] + dz)
    return pose

def squat_body(t, depth=0.58, back=0.14, lean=1.0):
    """the bodyweight squat's body. lean: 1 = the squat's 30 degrees of forward lean, 0.3 = more upright (a held weight)"""
    return {"Hips": {"move": (0, back * t, -depth * t)},
            "Spine": {"rot": (14 * lean * t, 0, 0)}, "Spine1": {"rot": (10 * lean * t, 0, 0)}, "Spine2": {"rot": (6 * lean * t, 0, 0)},
            "Neck": {"rot": (-8 * lean * t, 0, 0)}, "Head": {"rot": (-14 * lean * t, 0, 0)}}


def calf_raise(u, angle=50.0):
    """rise onto the balls of the feet. u: 0 flat .. 1 up. Each foot turns about its ball by u * angle degrees (the toes stay flat on the floor) and the hips rise with the ankles"""
    b = rig.data.bones; ball = Vector((0.0, b["Foot.L"].tail_local.y, b["Foot.L"].tail_local.z)); ankle = b["Foot_IK.L"].head_local.copy()
    ph = angle * u; M = rigid(ball, ball, ph); a = M(ankle)
    return {"Hips": {"move": (0, a.y - ankle.y, a.z - ankle.z)}, "Foot_IK.L": {"at": tuple(a), "wrot": (ph, 0, 0)}, "Toes.L": {"rot": (-ph, 0, 0)},
            "Knee_Pole.L": {"at": (0.134, -0.55 + (a.y - ankle.y), 0.55 + (a.z - ankle.z))}}

ARM = 0.50          # arm length used for straight arms (the arm is 0.54 at full stretch)
def jumping_jack(u, spread=0.46, jump=0.12, arm=170.0):
    """one jumping jack. u: 0 = feet together, arms down; 1 = feet apart, arms overhead, landed. Halfway the feet are `jump` metres off the floor.
    The hips sit at the height that keeps each leg a little short of straight; the arms swing about the shoulders in the frontal plane (a = 0 down, 90 out, 170 up)"""
    b = rig.data.bones; A0 = b["Foot_IK.L"].head_local; T = b["Thigh.L"].head_local; S0 = b["UpperArm.L"].head_local
    ax = A0.x + (spread - A0.x) * u; az = A0.z + jump * math.sin(math.pi * u)
    hz = az + math.sqrt(0.86 ** 2 - (ax - T.x) ** 2); dz = hz - T.z
    a = math.radians(arm * u); S = Vector((S0.x, S0.y, S0.z + dz)); w = S + Vector((math.sin(a), 0, -math.cos(a))) * ARM
    return {"Hips": {"move": (0, 0, dz)}, "Foot_IK.L": {"at": (ax, A0.y, az), "wrot": (0, 0, 0)}, "Knee_Pole.L": {"at": (ax + 0.06, -0.55, hz - 0.4)},
            "Hand_IK.L": {"at": tuple(w), "wrot": (0, 90 - arm * u, 0), "props": {"fist": 0.0}}, "Elbow_Pole.L": {"at": (S.x + 0.3, S.y + 0.6, S.z)}}

def hip_abduction(u, angle=40.0):
    """standing on the right leg, the LEFT leg lifted straight out to the side by u * angle degrees; the right hand rests on a wall rail 52 cm out. The hips shift 4 cm over the standing foot"""
    b = rig.data.bones; T = b["Thigh.L"].head_local; A0 = b["Foot_IK.L"].head_local
    a = math.radians(angle * u); dx = -0.04 * u; hips_x = T.x - 0.095 + dx
    ankle = Vector((T.x + dx + 0.86 * math.sin(a) + (A0.x - T.x) * math.cos(a), A0.y, T.z - 0.86 * math.cos(a)))
    return {"Hips": {"move": (dx, 0, 0)}, "Foot_IK.L": {"at": tuple(ankle), "wrot": (0, -angle * u, 0)}, "Knee_Pole.L": {"at": (ankle.x + 0.05, -0.55, 0.55)},
            "Foot_IK.R": {"at": (-A0.x + dx * 0, A0.y, A0.z), "wrot": (0, 0, 0)},
            "Hand_IK.R": {"at": (-0.52, -0.05, 1.12), "wrot": (0, 0, 0), "props": {"fist": 0.0}}, "Elbow_Pole.R": {"at": (-0.40, 0.55, 1.0)}}


def jump_squat(t, air=0.0, depth=0.58, back=0.14):
    """the squat's body (t = 0 standing .. 1 bottom) plus `air` metres of jump: the hips and both feet rise together, so the legs keep their length"""
    p = squat_body(t, depth, back, 1.0); b = rig.data.bones; A0 = b["Foot_IK.L"].head_local
    p["Hips"] = {"move": (0, back * t, -depth * t + air)}
    p["Foot_IK.L"] = {"at": (A0.x, A0.y, A0.z + air), "wrot": (0, 0, 0)}; p["Knee_Pole.L"] = {"at": (0.134, -0.55, 0.55 + air)}
    return p

def single_leg(u, lift=0.10, sway=0.0):
    """balance on the right leg: the LEFT foot a few centimetres off the floor (u: 0 both feet down, 1 lifted), the hips 4.5 cm over the standing foot; the right hand rests on a rail
    52 cm out (not modelled), as in the hip abduction. sway: a small side-to-side drift of the hips (m)"""
    b = rig.data.bones; A0 = b["Foot_IK.L"].head_local; dx = -0.045 * u + sway
    return {"Hips": {"move": (dx, 0, 0)}, "Foot_IK.L": {"at": (A0.x + dx * 0.5, A0.y + 0.04 * u, A0.z + lift * u), "wrot": (0, 0, 0)}, "Knee_Pole.L": {"at": (A0.x + 0.05, -0.55, 0.55)},
            "Foot_IK.R": {"at": (-A0.x, A0.y, A0.z), "wrot": (0, 0, 0)},
            "Hand_IK.R": {"at": (-0.52, -0.05, 1.12), "wrot": (0, 0, 0), "props": {"fist": 0.0}}, "Elbow_Pole.R": {"at": (-0.40, 0.55, 1.0)}}

def bird_dog_base(hip_y=0.30, hip_z=0.50):
    """on hands and knees: the torso level (the pelvis pitched forward 90 degrees about the hips), the head looking down and ahead"""
    return {"Hips": {"move": (0, hip_y - 0.06, hip_z - 0.97), "rot": (90, 0, 0)}, "Neck": {"rot": (-12, 0, 0)}, "Head": {"rot": (-22, 0, 0)}}


def quad_base(hip_y=0.30, hip_z=0.53, pitch=90.0, spine=(0, 0, 0), neck=-12.0, head=-22.0):
    """on hands and knees: the pelvis pitched forward about the hips so the torso is level; spine, neck and head are the flexion of each (degrees; negative = extension)"""
    return {"Hips": {"move": (0, hip_y - 0.06, hip_z - 0.97), "rot": (pitch, 0, 0)}, "Spine": {"rot": (spine[0], 0, 0)}, "Spine1": {"rot": (spine[1], 0, 0)},
            "Spine2": {"rot": (spine[2], 0, 0)}, "Neck": {"rot": (neck, 0, 0)}, "Head": {"rot": (head, 0, 0)}}

def childs_pose(c, ankle_y=0.86, hips_y=0.62, hips_z=0.26, pitch=78.0):
    """from hands and knees (c = 0) to the child's pose (c = 1): the hips sit back toward the heels (not onto them: that bent the knees past their limit and tore the skin), the shins and knees stay where they are, the forehead goes to the floor.
    The ankles are fixed on the floor behind; the legs fold as the hips come back"""
    a = quad_base(0.30 + (hips_y - 0.30) * c, 0.53 + (hips_z - 0.53) * c, 90 + (pitch - 90) * c, (0, 0, 0), -12 + 42 * c, -22 + 40 * c)
    for s in "LR":
        x = 0.12 if s == "L" else -0.12
        a[f"Foot_IK.{s}"] = {"at": (x, ankle_y, 0.12), "wrot": (0, 0, 0)}; w = c ** 2; a[f"Knee_Pole.{s}"] = {"at": (x * (1.25 + 3.75 * w), 0.15 + 0.55 * w, 0.15)}      # at the start the pole is just ahead of the knees; folded, the hip, knee and ankle are level, so the knees open out to the sides at floor height
    return a

def shoulder_roll(psi, tilt=0.0, r=9.0):
    """a backward shoulder roll at phase psi (radians): the shoulders go forward, up, back, down (the clavicles turn about x for forward-back and z for up-down, r degrees at most),
    and the neck tilts the ear toward a shoulder by `tilt` degrees"""
    b = -r * math.cos(psi); c = -r * math.sin(psi)
    p = squat_body(0.0)
    p["Clavicle.L"] = {"rot": (b, 0, c)}
    p["Neck"] = {"rot": (0, 0, 0.7 * tilt)}; p["Head"] = {"rot": (0, 0, 0.3 * tilt)}
    return p

def hip_circle(psi, flex=60.0, amp_flex=12.0, amp_ab=20.0, dx_hips=-0.045):
    """balance on the right leg (the right hand on a rail) and trace a circle with the LEFT knee: the thigh is lifted `flex` degrees forward, plus amp_flex of forward-back and amp_ab of
    out-and-in, around the circle of phase psi (radians). The shin hangs from the knee"""
    b = rig.data.bones; T = b["Thigh.L"].head_local.copy(); A0 = b["Foot_IK.L"].head_local
    fl = math.radians(flex + amp_flex * math.cos(psi)); ab = math.radians(amp_ab * math.sin(psi))
    d = Vector((math.sin(ab), -math.sin(fl) * math.cos(ab), -math.cos(fl) * math.cos(ab)))
    T = Vector((T.x + dx_hips, T.y, T.z)); knee = T + d * 0.42; ankle = knee + Vector((0, 0.15, -1.0)).normalized() * 0.45
    return {"Hips": {"move": (dx_hips, 0, 0)}, "Foot_IK.L": {"at": tuple(ankle), "wrot": (0, 0, 0)}, "Knee_Pole.L": {"at": tuple(knee + d * 0.5 + Vector((0, 0, 0.2)))},
            "Foot_IK.R": {"at": (-A0.x, A0.y, A0.z), "wrot": (0, 0, 0)},
            "Hand_IK.R": {"at": (-0.52, -0.05, 1.12), "wrot": (0, 0, 0), "props": {"fist": 0.0}}, "Elbow_Pole.R": {"at": (-0.40, 0.55, 1.0)}}

def hamstring_stretch(u, stride=0.52, back=0.25, pitch=42.0):
    """stand with the left heel forward and the leg straight, then hinge at the hips with a flat back toward the foot (u: 0 standing, 1 the stretch). The front ankle is placed
    `stride` metres ahead of the standing foot with the toes up; the hips go back and down by the amount that makes the front leg 0.86 m long (just short of straight)"""
    b = rig.data.bones; T = b["Thigh.L"].head_local; A0 = b["Foot_IK.L"].head_local
    dy = (T.y + back) - (A0.y - stride); dx = abs(A0.x - T.x)
    hz1 = A0.z + math.sqrt(max(0.86 ** 2 - dy ** 2 - dx ** 2, 0.04)); drop = max(0.0, T.z - hz1)
    p = hinge_body(u, back=back, drop=drop, pitch=pitch)
    p["Foot_IK.L"] = {"at": (A0.x, A0.y - stride * u, A0.z + 0.014 * u), "wrot": (-30 * u, 0, 0)}; p["Knee_Pole.L"] = {"at": (A0.x, A0.y - stride * u - 0.5, 0.5)}
    p["Foot_IK.R"] = {"at": (-A0.x, A0.y, A0.z + 0.003), "wrot": (0, 0, 0)}            # the standing foot is planted explicitly, a hair above the floor
    return p


def pistol_squat(t, depth=0.52, back=0.14, lean=1.0):
    """a single-leg squat on the RIGHT leg, the left leg held out in front. t: 0 standing .. 1 the bottom. The hips shift over the standing foot, drop and sit back; the torso leans as in the
    squat; the left ankle is held 0.85 m from the left hip, forward and a little below level, so the free leg stays straight, and its foot points up"""
    b = rig.data.bones; T = b["Thigh.L"].head_local; A0 = b["Foot_IK.L"].head_local
    dx = -0.095 * t; dz = -depth * t; dy = back * t
    p = squat_body(t, depth, back, lean)
    p["Hips"] = {"move": (dx, dy, dz)}
    hip = Vector((T.x + dx, T.y + dy, T.z + dz)); fl = math.radians(78)
    ankle = hip + Vector((0, -0.84 * math.sin(fl), -0.84 * math.cos(fl)))
    p["Foot_IK.L"] = {"at": tuple(ankle), "wrot": (-75, 0, 0)}; p["Knee_Pole.L"] = {"at": (ankle.x, ankle.y * 0.5, ankle.z + 0.5)}
    p["Foot_IK.R"] = {"at": (-A0.x, A0.y, A0.z), "wrot": (0, 0, 0)}
    return p

def skater_hop(s, jump=0.10, spread=0.30, dip=0.14):
    """a skater hop: s = 0 balanced on the RIGHT leg at x = -spread with the left leg trailing behind; s = 1 the mirror image on the left leg. In between the body hops across: both
    feet are `jump` metres off the floor at the middle, and the landing leg is bent by `dip` metres at each end"""
    b = rig.data.bones; T = b["Thigh.L"].head_local; A0 = b["Foot_IK.L"].head_local
    fl = math.sin(math.pi * s); hx = -(spread - 0.095) + 2 * (spread - 0.095) * s
    hz = -dip * (1 - fl) + 0.5 * jump * fl                                   # bent at the ends, a little extended in the air
    rx = -spread + (0.10 + spread) * s; lx = -0.10 + (spread + 0.10) * s       # the right foot goes from planted to trailing, the left from trailing to planted
    ry = A0.y + 0.40 * s; ly = A0.y + 0.40 * (1 - s)
    rz = A0.z + 0.10 * s + jump * fl; lz = A0.z + 0.10 * (1 - s) + jump * fl
    return {"Hips": {"move": (hx, 0.06 * (1 - abs(1 - 2 * s)), hz), "rot": (8 * (1 - fl), 0, 0)}, "Spine": {"rot": (6 * (1 - fl), 0, 0)}, "Spine1": {"rot": (6 * (1 - fl), 0, 0)},
            "Foot_IK.L": {"at": (lx, ly, lz), "wrot": (0, 0, 0)}, "Knee_Pole.L": {"at": (lx + 0.04, -0.55, 0.55)},
            "Foot_IK.R": {"at": (rx, ry, rz), "wrot": (0, 0, 0)}, "Knee_Pole.R": {"at": (rx - 0.04, -0.55, 0.55)}}


# ------------------------------------------------------------------ the burpee: five poses, blended
def _lerp_val(a, b, w):
    if isinstance(a, dict): return {k: _lerp_val(a[k], b.get(k, a[k]), w) for k in a}
    if isinstance(a, (list, tuple)): return tuple(x + (y - x) * w for x, y in zip(a, b))
    return a + (b - a) * w

def blend_pose(A, B, w):
    """the pose between A and B (w = 0 .. 1), bone by bone and entry by entry; an entry only one of them has is kept as it is"""
    out = {}
    for bone in set(A) | set(B):
        ea, eb = A.get(bone), B.get(bone)
        if ea is None: out[bone] = dict(eb); continue
        if eb is None: out[bone] = dict(ea); continue
        out[bone] = {k: (_lerp_val(ea[k], eb[k], w) if k in eb else ea[k]) for k in ea}
        for k in eb:
            if k not in ea: out[bone][k] = eb[k]
    return out

def _stand_pose(air=0.0, arms=0.0):
    """standing tall (every entry the burpee blends): arms hang at the sides (arms = 0) or are overhead (arms = 1, the wrist swinging on an arc about the shoulder); air lifts the hips and both feet"""
    b = rig.data.bones; A0 = b["Foot_IK.L"].head_local; S0 = b["UpperArm.L"].head_local; a = math.radians(170 * arms)
    w = Vector((S0.x + 0.50 * math.sin(a), S0.y, S0.z + air - 0.50 * math.cos(a)))
    return {"Hips": {"move": (0, 0, air), "rot": (0, 0, 0)}, "Spine": {"rot": (0, 0, 0)}, "Spine1": {"rot": (0, 0, 0)}, "Spine2": {"rot": (0, 0, 0)}, "Neck": {"rot": (0, 0, 0)}, "Head": {"rot": (0, 0, 0)},
            "Foot_IK.L": {"at": (A0.x, A0.y, A0.z + air), "wrot": (0, 0, 0)}, "Knee_Pole.L": {"at": (0.134, -0.55, 0.55 + air)}, "Toes.L": {"rot": (0, 0, 0)},
            "Hand_IK.L": {"at": tuple(w), "wrot": (0, 90 - 170 * arms, 0), "props": {"fist": 0.0}}, "Elbow_Pole.L": {"at": (S0.x + 0.15, S0.y + 0.6, S0.z + air)}}

def _crouch_pose(pitch=75.0, arm=0.48):
    """the burpee's low position: the hands planted where the plank's hands are, the feet at rest, the hips back and low over the feet with the torso pitched forward"""
    ph = math.radians(pitch); hand = pushup_pose(PHI_UP)["Hand_IK.L"]["at"]; sy = hand[1]
    hy = sy + 0.48 * math.sin(ph); hz = 0.045 + arm - 0.48 * math.cos(ph)
    p = _stand_pose()
    p["Hips"] = {"move": (0, hy - 0.06, hz - 0.97), "rot": (pitch, 0, 0)}
    p["Neck"] = {"rot": (-18, 0, 0)}; p["Head"] = {"rot": (-28, 0, 0)}
    p["Hand_IK.L"] = {"at": tuple(hand), "wrot": (0, 0, -90), "props": {"fist": 0.0}}; p["Elbow_Pole.L"] = {"at": (hand[0] + 0.45, hand[1] + 0.3, hand[2] + 0.35)}
    return p

HIP_LIFT = 0.0165
def burpee(f, jump=0.30, hand_pow=1.0, z_pow=1.0, bulge_y=0.0, bulge_z=0.0):
    """one burpee over 85 frames: stand (1), drop to a crouch with the hands on the floor (13), kick the feet back to a plank (25), a push-up (31 down, 37 hold, 43 up), jump the feet back
    in (51), stand (59), jump with the arms overhead (59-79), land (79), settle (85)"""
    ease = lambda x: 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, x)))
    STAND, CROUCH, PLANK, DOWN = _stand_pose(), _crouch_pose(), pushup_pose(PHI_UP), pushup_pose(PHI_DN)
    for p in (PLANK, DOWN):                                                       # fill in what the push-up pose does not say
        p.setdefault("Spine", {"rot": (0, 0, 0)}); p.setdefault("Spine1", {"rot": (0, 0, 0)}); p.setdefault("Spine2", {"rot": (0, 0, 0)}); p.setdefault("Elbow_Pole.L", CROUCH["Elbow_Pole.L"])
    def seg(a, b, A, B, air=0.0, hp=1.0):
        w = ease((f - a) / (b - a)); p = blend_pose(A, B, w)
        if hp != 1.0:                                                             # the hands travel on their own schedule: they lead (hp < 1) or lag (hp > 1) the body
            for k in ("Hand_IK.L", "Elbow_Pole.L"): p[k] = _lerp_val(A[k], B[k], w ** hp)
        if (hp != 1.0 or z_pow != 1.0 or bulge_y or bulge_z) and A is not B and "Hand_IK.L" in A and a in (1, 51):
            ha, hb = A["Hand_IK.L"]["at"], B["Hand_IK.L"]["at"]; h = p["Hand_IK.L"]["at"]
            m_ = math.sin(math.pi * w)
            p["Hand_IK.L"] = {**p["Hand_IK.L"], "at": (h[0], h[1] + bulge_y * m_, ha[2] + (hb[2] - ha[2]) * w ** z_pow + bulge_z * m_)}      # the hand's path bulges in/up halfway so it stays within reach of the shoulder
        if air:
            m = math.sin(math.pi * w)
            for k in ("Foot_IK.L",): p[k]["at"] = (p[k]["at"][0], p[k]["at"][1], p[k]["at"][2] + air * m)
            mv = p["Hips"]["move"]; p["Hips"]["move"] = (mv[0], mv[1], mv[2] + HIP_LIFT * m)         # the hips rise a little as the feet kick, so the thighs clear the floor
        return p
    if f <= 13: return seg(1, 13, STAND, CROUCH, 0.0, 1.0001)
    if f <= 19: return CROUCH
    if f <= 25: return seg(19, 25, CROUCH, PLANK, 0.18)
    if f <= 31: return seg(25, 31, PLANK, DOWN)
    if f <= 37: return DOWN
    if f <= 43: return seg(37, 43, DOWN, PLANK)
    if f <= 51: return seg(43, 51, PLANK, CROUCH, 0.18)
    if f <= 59: return seg(51, 59, CROUCH, STAND, 0.0, 1.0001)
    if f <= 79:
        x = (f - 59) / 20.0; air = jump * math.sin(math.pi * x); arms = math.sin(math.pi * min(1.0, x * 1.1)) if x < 0.9 else 0.0
        return _stand_pose(air, arms)
    return STAND


def pike_pushup(u, hand_y=-0.30, ankle_y=0.66, shoulder_z=0.55, drop=0.15, phi0=127.0, phi1=140.0, torso=0.48):
    """a pike push-up: the legs straight and the hips high in an inverted V, the hands flat under the shoulders. u: 0 the top, 1 the head lowered between the hands. The shoulders stay over
    the hands and drop by `drop` metres; the torso (a 0.48 m rod) tips from phi0 to phi1 degrees from vertical (pointing down and forward), which moves the hips back and up a little. The
    drop is limited by the legs: the feet are planted, so the hips cannot go further from the ankles than the legs are long"""
    phi = math.radians(phi0 + (phi1 - phi0) * u); sz = shoulder_z - drop * u
    hy, hz = hand_y + torso * math.sin(phi), sz - torso * math.cos(phi)            # the hips, from the shoulders and the torso angle
    return {"Hips": {"move": (0, hy - 0.06, hz - 0.97), "rot": (math.degrees(phi), 0, 0)}, "Neck": {"rot": (30 * u + 10, 0, 0)}, "Head": {"rot": (25 * u + 10, 0, 0)},
            "Foot_IK.L": {"at": (0.12, ankle_y, 0.20), "wrot": (45, 0, 0)}, "Toes.L": {"rot": (-45, 0, 0)}, "Knee_Pole.L": {"at": (0.12, -0.2, 0.9)},
            "Hand_IK.L": {"at": (0.19, hand_y, 0.045), "wrot": (0, 0, -90), "props": {"fist": 0.0}}, "Elbow_Pole.L": {"at": (0.75, hand_y + 0.1, 0.5)}}


def seated_body(hip_y=0.0, pitch=45.0, seat=0.475):
    """sitting on the end of a bench (its pad `seat` metres up), thighs level and apart, the feet flat on the floor 30 cm either side of the middle, the torso pitched forward by `pitch` degrees"""
    hz = seat + 0.10
    p = {"Hips": {"move": (0, hip_y - 0.06, hz - 0.97), "rot": (pitch, 0, 0)}, "Neck": {"rot": (-0.4 * pitch, 0, 0)}, "Head": {"rot": (-0.5 * pitch, 0, 0)},
         "Foot_IK.L": {"at": (0.30, hip_y - 0.42, 0.10), "wrot": (0, 0, 0)}, "Knee_Pole.L": {"at": (0.40, hip_y - 0.95, 0.55)}}
    return p

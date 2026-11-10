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

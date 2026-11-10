"""moves.py - parametric body motions for exercises written as text: generators that return the legs, hips and spine (no arms, no props).
Loaded with  python = "moves.py"  (after anim_core). All distances in metres, angles in degrees, feet planted (the Foot_IK controls stay at rest).

hinge_body(t, back, drop, pitch, spine, neck, head)    t = 0 standing, 1 = the hinge's bottom: the hips go back and down and the torso tips forward.
squat_body(t, depth, back, lean)                       the squat's body, t = 0 standing .. 1 = the bottom
"""
def _lerp(a, b, t): return a + (b - a) * t

def hinge_body(t, back=0.30, drop=0.40, pitch=40.0, spine=(6.0, 5.0, 4.0), neck=-14.0, head=-18.0):
    """a hip hinge / deadlift. pitch: how far the pelvis tips forward (the spine stays straight: the spine bones add `spine` degrees of lean);
    neck and head turn the other way so the eyes look ahead and down"""
    return {"Hips": {"move": (0, back * t, -drop * t), "rot": (pitch * t, 0, 0)},
            "Spine": {"rot": (spine[0] * t, 0, 0)}, "Spine1": {"rot": (spine[1] * t, 0, 0)}, "Spine2": {"rot": (spine[2] * t, 0, 0)},
            "Neck": {"rot": (neck * t, 0, 0)}, "Head": {"rot": (head * t, 0, 0)}}

def squat_body(t, depth=0.58, back=0.14, lean=1.0):
    """the bodyweight squat's body. lean: 1 = the squat's 30 degrees of forward lean, 0.3 = more upright (a held weight)"""
    return {"Hips": {"move": (0, back * t, -depth * t)},
            "Spine": {"rot": (14 * lean * t, 0, 0)}, "Spine1": {"rot": (10 * lean * t, 0, 0)}, "Spine2": {"rot": (6 * lean * t, 0, 0)},
            "Neck": {"rot": (-8 * lean * t, 0, 0)}, "Head": {"rot": (-14 * lean * t, 0, 0)}}

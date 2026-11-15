"""dumbbell.py - dumbbell exercises as generators (loaded with  python = ["moves.py", "poselib.py", "dumbbell.py"]).

A dumbbell is held in each hand (grab_dumbbell = 1). The weight leads and the hand follows, so each generator says where the LEFT wrist goes and which way the hand points:
    fingers  the direction the fingers point (along the forearm, for a hand in line with it)
    palm     the direction the palm faces
The right side is the mirror image (anim_core mirrors the left). The dumbbell's origin is then put where that wrist, hand and grip make it: hold(W, fingers, palm).
The hand frame is the kettlebell top-bar grip: fingers -Y, palm -Z, handle along X, the wrist 9.1 cm behind the handle and 3.4 cm above it (see build_prop_rig.py).
"""
import math
from mathutils import Vector, Matrix

DB_WRIST = Vector((0.0, 0.091, 0.034))                       # the wrist's place in the dumbbell's own frame
def _frame(f, n):
    f = Vector(f).normalized(); n = Vector(n).normalized(); x = f.cross(n)
    return Matrix((x, f, n)).transposed()                    # columns: handle axis, fingers, palm
_LOCAL = _frame((0, -1, 0), (0, 0, -1))
_PREV_DB = {}

def hold(W, fingers, palm, pole=None):
    """the left dumbbell and hand for a wrist at W with the given finger and palm directions (the right is the mirror). pole: the left elbow pole"""
    R = _frame(fingers, palm) @ _LOCAL.inverted()
    centre = Vector(W) - R @ DB_WRIST
    prev = _PREV_DB.get("L"); e = R.to_euler('XYZ', prev) if prev is not None else R.to_euler('XYZ'); _PREV_DB["L"] = e
    out = {"Dumbbell.L": {"at": tuple(centre), "wrot": tuple(math.degrees(a) for a in e)}, "Hand_IK.L": {"props": {"grab_dumbbell": 1.0}}}
    if pole is not None: out["Elbow_Pole.L"] = {"at": tuple(pole)}
    return out

def reset_db():
    _PREV_DB.clear()

_S = Vector((0.19, 0.06, 1.45))                              # the left shoulder at rest
_ARM = 0.52                                                  # shoulder to wrist for a nearly straight arm

def db_curl(kappa, hammer=0.0):
    """a biceps curl: the elbow stays at the side (28.5 cm below the shoulder), the forearm swings forward and up by kappa degrees. Supinated (palm forward, then up) unless hammer = 1
    (palms facing in the whole way)"""
    k = math.radians(kappa); E = Vector((_S.x + 0.025, _S.y + 0.01, _S.z - 0.285))
    f = Vector((0, -math.sin(k), -math.cos(k))); W = E + f * 0.24
    n_sup = Vector((0, -math.cos(k), math.sin(k))); n_ham = Vector((-1, 0, 0)); n = n_sup * (1 - hammer) + n_ham * hammer
    return hold(W, f, n, pole=(0.30, 0.9, 1.10))

def db_lateral(a, forward=0.0):
    """a lateral raise: the arm (nearly straight) swings out to the side by a degrees; the hand leads with the little finger side (palm down at the top). forward turns the plane of the raise
    that many degrees toward the front"""
    r = math.radians(a); fw = math.radians(forward)
    d = Vector((math.cos(fw) * math.sin(r), -math.sin(fw) * math.sin(r), -math.cos(r))); W = _S + d * _ARM
    n = Vector((-math.cos(r) * math.cos(fw), math.cos(r) * math.sin(fw), -math.sin(r)))
    return hold(W, d, n, pole=(_S.x + 0.3, _S.y + 0.7, _S.z))

def db_front(a):
    """a front raise: the straight arm swings forward by a degrees, palms facing down at the top (palms back at the bottom)"""
    r = math.radians(a); d = Vector((0.0, -math.sin(r), -math.cos(r))); W = _S + d * _ARM
    return hold(W, d, Vector((0.0, math.cos(r), -math.sin(r))), pole=(_S.x + 0.3, _S.y + 0.7, _S.z))

def db_shrug(h, rise=0.035):
    """a shrug: the arms hang straight and the shoulders rise by h * rise metres (the clavicles turn); the dumbbells hang with them, palms in"""
    W = _S + Vector((0.065, 0.0, -_ARM + rise * h))
    out = hold(W, (0, 0, -1), (-1, 0, 0), pole=(0.34, 0.6, 1.15))
    out["Clavicle.L"] = {"rot": (0, 0, -rise / 0.029 * 10.0 * h)}
    return out

def db_press(h, turn=1.0):
    """a shoulder press: h = 0 the dumbbells at the shoulders (the forearms vertical, elbows out), h = 1 locked out overhead. turn: how far the palms have turned from facing you (0) through facing
    out (0.5) to facing forward (1); 1 the whole way is a plain press, and turn = h is the Arnold press"""
    W = Vector((0.33 - 0.12 * h, -0.05 + 0.05 * h, 1.57 + 0.34 * h)); r = math.pi * turn
    return hold(W, (0, 0, 1), Vector((math.sin(r), math.cos(r), 0.0)), pole=(0.9 - 0.35 * h, 0.1, 1.35 + 0.15 * h))


def db_lying(pose, mode, h, spread=0.14):
    """a POST HOOK for dumbbell work lying on a bench (the body from situp.bench_body): the wrists are placed from the shoulders as the body lies. mode "press": the forearms vertical, the weights
    pressed from the chest (h = 0) to straight arms over the chest (h = 1). mode "fly": the arms nearly straight over the chest (h = 0) opening out to the sides until level with the chest (h = 1),
    palms facing each other, a slight bend in the elbows"""
    _apply_pose(pose); P = pose_bones(); S = P["UpperArm.L"].head.copy()
    if mode == "incline":                       # pressed along the normal of the reclined torso (50 degrees from vertical)
        ph = math.radians(50.0); n = Vector((0, -math.cos(ph), math.sin(ph)))
        return hold(S + Vector((spread, 0, 0)) + n * (0.08 + 0.40 * h), n, Vector((0, -n.z, n.y)), pole=(S.x + 0.7, S.y, S.z + 0.1))
    if mode == "press":
        W = Vector((S.x + spread, S.y, S.z + 0.08 + 0.40 * h))
        return hold(W, (0, 0, 1), (0, -1, 0), pole=(S.x + 0.7, S.y, S.z + 0.1))
    a = math.radians(8 + 77 * h); d = Vector((math.sin(a), 0, math.cos(a))); W = S + d * 0.47
    return hold(W, d, Vector((-math.cos(a), 0, math.sin(a))), pole=(S.x + 0.5, S.y + 0.3, S.z - 0.2))


def db_bent_lateral(pose, a, arm=0.50):
    """a POST HOOK for the rear-delt fly (bent over, the torso hinged forward): the nearly straight arms hang from the shoulders and swing out to the sides in the frontal plane, a = 0 hanging
    to 90 level with the shoulders, the palms facing each other at the bottom and down at the top. The shoulders are read from the posed body"""
    _apply_pose(pose); P = pose_bones(); S = P["UpperArm.L"].head.copy(); r = math.radians(a)
    d = Vector((math.sin(r), 0.0, -math.cos(r))); W = S + d * arm
    return hold(W, d, Vector((-math.cos(r), 0.0, -math.sin(r))), pole=(S.x + 0.3, S.y + 0.6, S.z))


def db_concentration(pose, kappa):
    """a POST HOOK for the concentration curl (sitting on a bench end, torso pitched forward): the LEFT upper arm hangs from the shoulder with the elbow braced against the inside of the thigh, the
    dumbbell between the knees; the forearm swings from hanging (kappa = 0) up toward the shoulder (kappa = 140). The right hand rests on the right knee and holds nothing"""
    _apply_pose(pose); P = pose_bones(); S = P["UpperArm.L"].head.copy(); k = math.radians(kappa)
    E = S + Vector((-0.03, 0.05, -0.285)); f = Vector((0, -math.sin(k), -math.cos(k))); W = E + f * 0.24
    out = hold(W, f, Vector((0, -math.cos(k), math.sin(k))), pole=(S.x + 0.45, S.y + 0.8, S.z - 0.2))
    out["Dumbbell.R"] = {"at": (-0.30, -0.25, 0.07), "wrot": (0, 0, 0)}
    out["Hand_IK.R"] = {"at": (-0.26, S.y - 0.02, 0.64), "wrot": (0, 0, -90), "props": {"fist": 0.0, "grab_dumbbell": 0.0}}
    out["Elbow_Pole.R"] = {"at": (-0.55, S.y + 0.5, 0.8)}
    return out

"""barbell.py - barbell exercises as generators (loaded with  python = ["moves.py", "poselib.py", "barbell.py"]).

The BAR leads and both hands follow: the bar is one control bone ("Barbell", the middle of the bar), and the grab slider snaps each hand to its grip on the bar:
    grab_barbell        overhand (palms down), hands 56 cm apart
    grab_barbell_close  overhand, 28 cm apart          grab_barbell_wide  overhand, 90 cm apart       grab_barbell_under  underhand (palms up), 56 cm apart
bar_for(W, fingers, palm, grip) works out where the bar must be, and how it must be turned about its own axis, for the LEFT wrist to be at W with the hand pointing `fingers` and the palm facing `palm`.
"""
import math
from mathutils import Vector, Matrix

# per grip: (the grip's hand-x from the bar's middle, local finger direction, local palm direction, the wrist's offset from the handle in the bar frame, the grab slider)
_GRIPS = {"over": (0.28, (0, -1, 0), (0, 0, -1), (0.091, 0.034), "grab_barbell"), "close": (0.14, (0, -1, 0), (0, 0, -1), (0.091, 0.034), "grab_barbell_close"),
          "wide": (0.45, (0, -1, 0), (0, 0, -1), (0.091, 0.034), "grab_barbell_wide"), "under": (0.28, (0, -1, 0), (0, 0, 1), (0.091, -0.034), "grab_barbell_under")}
def _frame(f, n):
    f = Vector(f).normalized(); n = Vector(n).normalized(); x = f.cross(n)
    return Matrix((x, f, n)).transposed()

def bar_for(Wmid, fingers, palm, grip="over", pole=None):
    """the bar's pose for the wrists' MIDPOINT at Wmid (the left wrist is half the grip width to the left of it) with the left hand pointing `fingers` and its palm facing `palm`"""
    hx, fl, nl, (wy, wz), slider = _GRIPS[grip]
    R = _frame(fingers, palm) @ _frame(fl, nl).inverted()
    centre = Vector(Wmid) - R @ Vector((0.0, wy, wz))
    e = R.to_euler('XYZ')
    out = {"Barbell": {"at": tuple(centre), "wrot": tuple(math.degrees(a) for a in e)}, "Hand_IK.L": {"props": {slider: 1.0}}}
    if pole is not None: out["Elbow_Pole.L"] = {"at": tuple(pole)}
    return out

_S = Vector((0.19, 0.06, 1.45))

def bb_curl(kappa, grip_x=0.28):
    """a barbell curl, underhand: the elbows stay at the sides, the forearms swing up by kappa degrees, the wrists in line with the elbows"""
    k = math.radians(kappa); E = Vector((grip_x - 0.065, _S.y + 0.01, _S.z - 0.285))
    f = Vector((0, -math.sin(k), -math.cos(k))); W = E + f * 0.24; W.x = 0.0
    return bar_for(W, f, Vector((0, -math.cos(k), math.sin(k))), "under", pole=(0.30, 0.9, 1.10))


def bb_press(h, grip_x=0.28):
    """a standing overhead press: h = 0 the bar racked on the front of the shoulders (the forearms vertical, hands just outside the shoulders), h = 1 locked out overhead. The hand points up with the palm forward"""
    W = Vector((0.0, -0.05 + 0.05 * h, 1.57 + 0.34 * h)); W_l = Vector((grip_x, 0, 0))
    return bar_for(W, (0, 0, 1), (0, -1, 0), "over", pole=(0.9 - 0.35 * h, 0.1, 1.35 + 0.15 * h))

UPRIGHT_TOP = 0.36
def bb_upright(h):
    """an upright row, close overhand grip: the bar is pulled from the thighs (h = 0) up the front of the body to the chest (h = 1) with the elbows out and above the wrists"""
    W = Vector((0.0, -0.14 + 0.03 * h, 1.0 + UPRIGHT_TOP * h))
    return bar_for(W, (0, 0, -1), (0, 1, 0), "close", pole=(0.8, 0.0, 1.2 + 0.3 * h))

def bb_lift(t, y_floor=-0.12, z_top=0.93, y_top=-0.02, grip="over", bulge=0.0, z_bot=0.316):
    """a deadlift-type pull: the bar runs from the floor (t = 1, its middle 22.5 cm up, level with the shins) to hanging at the hips (t = 0) with the arms straight, overhand (the hand points
    down, the palm toward the legs). The wrists are placed 9 cm above the bar's middle. bulge: lifts the bar's path (m) midway, so the arms stay in reach as the shoulders swing forward"""
    W = Vector((0.0, y_floor + (y_top - y_floor) * (1 - t), z_bot + (z_top - z_bot) * (1 - t) + bulge * math.sin(math.pi * t)))
    return bar_for(W, (0, 0, -1), (0, 1, 0), grip, pole=(0.55, 0.5, 0.8))


def bb_lift_hook(pose, t, bulge=0.0, grip="over", **kw):
    """a POST HOOK: the bar for a pull (bb_lift), placed after the body"""
    return bb_lift(t, bulge=bulge, grip=grip, **kw)

def bb_row(pose, h, drop=0.50, pull=0.22, grip="over"):
    """a POST HOOK for rows (the torso hinged forward): the bar hangs `drop` metres below the shoulders with straight arms (h = 0) and is rowed up until it is `pull` metres below them (h = 1), the elbows
    going back and up. The shoulders are read from the posed body; overhand, the hand pointing down with the palm toward the legs"""
    _apply_pose(pose); P = pose_bones(); S = (P["UpperArm.L"].head + P["UpperArm.R"].head) / 2
    W = Vector((0.0, S.y + 0.03 * h, S.z - drop + (drop - pull) * h))
    return bar_for(W, (0, 0, -1), (0, 1, 0), grip, pole=(0.7, S.y + 0.6, S.z))

def bb_lying(pose, mode, h, grip="wide"):
    """a POST HOOK for barbell work lying on a bench (situp.bench_body). mode "press": the bar from the chest (h = 0) to straight arms over the chest (h = 1), the hand pointing up with the palm toward the feet.
    mode "skull": the elbows stay over the shoulders, the bar swings from over the face... h = 0 the arms straight up, h = 1 the bar lowered to the forehead"""
    _apply_pose(pose); P = pose_bones(); S = (P["UpperArm.L"].head + P["UpperArm.R"].head) / 2
    if mode == "incline":                       # pressed along the normal of the torso reclined 50 degrees from vertical (situp.incline_body)
        ph = math.radians(50.0); n = Vector((0, -math.cos(ph), math.sin(ph)))
        return bar_for(Vector((0.0, S.y, S.z)) + n * (0.12 + 0.34 * h), n, Vector((0, -n.z, n.y)), grip, pole=(S.x + 0.8, S.y, S.z + 0.1))
    if mode == "press":
        return bar_for(Vector((0.0, S.y, S.z + (0.12 if grip == "wide" else 0.18) + (0.46 - (0.12 if grip == "wide" else 0.18)) * h)), (0, 0, 1), (0, -1, 0), grip, pole=(S.x + 0.8, S.y, S.z + 0.1))
    k = math.radians(95 * h); E = Vector((0.0, S.y, S.z + 0.27)); f = Vector((0, math.sin(k), math.cos(k)))
    return bar_for(E + f * 0.24, f, Vector((0, -math.cos(k), math.sin(k))), grip, pole=(S.x + 0.6, S.y, S.z + 0.25))


def bb_rack_press(pose, h, grip="over"):
    """a POST HOOK for the thruster and the clean and press: the bar at the front of the shoulders (h = 0) pressed up to lockout overhead (h = 1), RIDING on the chest so it follows the squat's lean.
    The same hand positions as bb_press, but placed in the chest's frame (poselib.ride_prop)"""
    p = bb_press(h, 0.28) if grip == "over" else bb_press(h, 0.28)
    b = p["Barbell"]
    return ride_prop(pose, "Barbell", at=b["at"], rot=b["wrot"], grab="grab_barbell", frame="Spine2", pole=p["Elbow_Pole.L"]["at"])


def bb_clean_path(pose, u, y_floor=-0.15, y_top=-0.05, z_top=0.95, bulge=0.06):
    """a POST HOOK for the clean and press. u runs 0 to 3 along one path: 0..1 the deadlift (bar from the floor to hanging at the hips, as bb_lift), 1..2 the CLEAN (the bar travels up the body to the front rack on the
    shoulders, close to the body then out and over, while the wrists turn over: the hand points down at the hips and up in the rack), 2..3 the press from the rack to lockout overhead"""
    ease = lambda x: 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, x)))
    if u <= 1.0:
        t = 1.0 - u; W = Vector((0.0, y_floor + (y_top - y_floor) * (1 - t), 0.316 + (z_top - 0.316) * (1 - t) + bulge * math.sin(math.pi * t))); th = 90.0
    elif u <= 2.0:
        c = ease(u - 1.0); W = Vector((0.0, y_top + (-0.05 - y_top) * c - 0.16 * math.sin(math.pi * c), z_top + (1.57 - z_top) * c)); th = 90.0 - 180.0 * c
    else:
        h = ease(u - 2.0); W = Vector((0.0, -0.05 + 0.05 * h, 1.57 + 0.34 * h)); th = -90.0
    a = math.radians(th); f = Vector((0, -math.cos(a), -math.sin(a))); n = Vector((0, math.sin(a), -math.cos(a)))
    return bar_for(W, f, n, "over", pole=(0.6, 0.5, 1.2) if u < 1.7 else (0.9 - 0.35 * ease(u - 2.0), 0.1, 1.35 + 0.15 * ease(u - 2.0)))

"""machines.py - the person using a gym machine, WITHOUT the machine (the machines are not modelled: the hands close on handles that are not there, the seat is a pad you can't see). Loaded with
python = ["moves.py", "poselib.py", "machines.py"]. Every length comes from the rig (upper arm, forearm, thigh, shin); every pose is a seated or standing body from moves.py with the hands or feet then
placed from the posed shoulders or hips, so the arms and legs stay the right length however the torso leans.
"""
import math
from mathutils import Vector

def _lens():
    b = rig.data.bones; UA = (b["UpperArm.L"].tail_local - b["UpperArm.L"].head_local).length
    reach = (b["Hand.L"].head_local - b["UpperArm.L"].head_local).length
    return UA, reach - UA, reach
def _shoulder(p): _apply_pose(p); return pose_bones()["UpperArm.L"].head.copy()
def _lim(W, S, k=0.97):
    UA, FA, R = _lens(); d = W - S
    return S + d.normalized() * (k * R) if d.length > k * R else W
def _hands(W, S, pole, wrot=(0, 0, -90), fist=0.8):
    return {"Hand_IK.L": {"at": tuple(_lim(Vector(W), S)), "wrot": wrot, "props": {"fist": fist}}, "Elbow_Pole.L": {"at": tuple(pole)}}
def _lerp(a, b, t): return a + (b - a) * t
def _ease(x): return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, x)))

# ------------------------------------------------------------------ the arm machines
def chest_press(h):
    """seated, leaning back a little: the handles pressed from the chest (h = 0) to straight arms (h = 1)"""
    p = seated_body(0.0, -6.0, 0.45); S = _shoulder(p)
    p.update(_hands(S + Vector((0.05, -0.08 - 0.42 * h, -0.10)), S, (S.x + 0.6, S.y + 0.4, S.z - 0.1))); return p

def pec_deck(h):
    """seated against the back pad, the forearms vertical against the pads, the elbows level with the shoulders: the arms sweep from open (h = 0) to together in front of the chest (h = 1)"""
    p = seated_body(0.0, -3.0, 0.45); S = _shoulder(p); UA, FA, R = _lens(); a = math.radians(110 * h)
    E = S + Vector((UA * math.cos(a), -UA * math.sin(a), 0.0)); W = E + Vector((0, 0, FA))
    p.update(_hands(W, S, tuple(S + (E - S) * 2 + Vector((0, 0, -0.15))), (180, -90, 0), 0.5)); return p

def cable_crossover(h):
    """standing in a split stance, leaning forward, a handle in each hand from the high pulleys: the nearly straight arms sweep down and together in front of the hips (h = 1)"""
    p = hinge_body(1.0, 0.04, 0.10, 14.0, (3.0, 3.0, 3.0), -5.0, -8.0); b = rig.data.bones; A0 = b["Foot_IK.L"].head_local
    p["Foot_IK.L"] = {"at": (A0.x, A0.y - 0.28, A0.z), "wrot": (0, 0, 0)}; p["Knee_Pole.L"] = {"at": (A0.x + 0.05, A0.y - 0.9, 0.6)}
    p["Foot_IK.R"] = {"at": (-A0.x, A0.y + 0.28, A0.z), "wrot": (0, 0, 0)}; p["Knee_Pole.R"] = {"at": (-A0.x - 0.05, A0.y - 0.5, 0.6)}
    S = _shoulder(p); UA, FA, R = _lens(); d = (Vector((0.9, 0.08, 0.35)) * (1 - h) + Vector((-0.3, -0.45, -0.8)) * h).normalized()
    p.update(_hands(S + d * 0.97 * R, S, (S.x + 0.5, S.y + 0.4, S.z - 0.1))); return p

def seated_cable_row(h):
    """sitting at the cable row, the legs forward and slightly bent, the torso leaning forward with straight arms (h = 0), then pulled upright with the hands to the stomach (h = 1)"""
    p = seated_body(0.0, 18.0 - 23.0 * h, 0.35)
    p["Foot_IK.L"] = {"at": (0.15, -0.76, 0.28), "wrot": (-10, 0, 0)}; p["Knee_Pole.L"] = {"at": (0.2, -0.9, 0.85)}; S = _shoulder(p)
    Wa = S + Vector((0.08, -0.44, -0.22)); Wb = S + Vector((0.12, -0.16, -0.40))
    p.update(_hands(Wa + (Wb - Wa) * h, S, (S.x + 0.5, S.y + 0.5, S.z - 0.15))); return p

def lat_pulldown(h):
    """seated under the bar, the knees held by the pads, leaning back slightly: the bar from overhead (h = 0) to the upper chest (h = 1), the elbows pointing down and out"""
    p = seated_body(0.0, -10.0 - 8.0 * h, 0.45); S = _shoulder(p)
    Wa = S + Vector((0.24, -0.04, 0.44)); Wb = S + Vector((0.26, -0.22, -0.15))
    p.update(_hands(Wa + (Wb - Wa) * h, S, (S.x + 0.5, S.y + 0.35, S.z - 0.1), (0, 0, 0), 0.8)); return p

def tbar_row(h):
    """bent over the T-bar with the knees bent and the back flat, the arms hanging (h = 0), the elbows then driven back (h = 1) with the forearms vertical"""
    p = hinge_body(1.0, 0.25, 0.18, 50.0, (6.0, 5.0, 4.0), -14.0, -18.0, 0.20); S = _shoulder(p); UA, FA, R = _lens(); a = math.radians(70 * h)
    W = S + Vector((-0.10, UA * math.sin(a), -UA * math.cos(a) - FA))
    p.update(_hands(W, S, (S.x + 0.4, S.y + 0.6, S.z), (0, 90, 0))); return p

def preacher_curl(h):
    """seated at the preacher bench, the upper arms resting on the sloping pad: the forearm curls from nearly straight (h = 0) up toward the shoulder (h = 1)"""
    p = seated_body(0.0, 12.0, 0.45); S = _shoulder(p); UA, FA, R = _lens(); th = math.radians(55 + 110 * h)
    E = S + Vector((0.02, -0.20, -0.20)); W = E + Vector((0, -FA * math.sin(th), -FA * math.cos(th)))
    p.update(_hands(W, S, (E.x + 0.3, E.y + 0.4, E.z), (0, 0, -90))); return p

def tricep_pushdown(h):
    """standing at the cable, the elbows pinned at the sides: the forearms from pointing forward and up (h = 0) to straight down (h = 1)"""
    p = {"Hips": {"rot": (8.0, 0, 0)}, "Neck": {"rot": (-3.0, 0, 0)}, "Head": {"rot": (-3.0, 0, 0)}}; S = _shoulder(p); UA, FA, R = _lens(); th = math.radians(105 * (1 - h))
    E = S + Vector((0.02, 0.04, -UA)); W = E + Vector((0, -FA * math.sin(th), -FA * math.cos(th)))
    p.update(_hands(W, S, (E.x + 0.3, E.y + 0.5, E.z), (0, 0, -90))); return p

# ------------------------------------------------------------------ the leg machines
def leg_press(h):
    """reclined on the sled, the back 50 degrees from upright: the feet on the platform (up and ahead, 45 degrees), pushed from a deep bend (h = 0) to nearly straight legs (h = 1)"""
    b = rig.data.bones; T = b["Thigh.L"].head_local; UA, FA, R = _lens(); L = (T - b["Foot_IK.L"].head_local).length
    p = {"Hips": {"move": (0, 0.30, 0.42 - 0.97), "rot": (-50.0, 0, 0)}, "Neck": {"rot": (15, 0, 0)}, "Head": {"rot": (15, 0, 0)}}
    _apply_pose(p); H = pose_bones()["Thigh.L"].head.copy(); be = math.radians(45); d = (0.50 + 0.34 * h) * L / 0.88
    ank = H + Vector((0.0, -d * math.cos(be), d * math.sin(be))); ank.x = 0.19
    p["Foot_IK.L"] = {"at": tuple(ank), "wrot": (-135.0, 0, 0)}; p["Knee_Pole.L"] = {"at": (0.25, ank.y - 0.3, ank.z + 0.8)}
    return p

def _seated_leg(phi, pitch=-5.0):
    p = seated_body(0.0, pitch, 0.45)
    for k in ("Foot_IK.L", "Knee_Pole.L"): p.pop(k, None)
    b = rig.data.bones; UA = (b["Thigh.L"].tail_local - b["Thigh.L"].head_local).length; LA = (b["Shin.L"].tail_local - b["Shin.L"].head_local).length
    _apply_pose(p); H = pose_bones()["Thigh.L"].head.copy(); K = H + Vector((0.0, -UA, -0.02)); a = math.radians(phi)
    ank = K + Vector((0.0, -LA * math.sin(a), -LA * math.cos(a))); ank.x = 0.15; ank.z = max(ank.z, rig.data.bones["Foot_IK.L"].head_local.z + 0.012)
    p["Foot_IK.L"] = {"at": tuple(ank), "wrot": (-max(phi, 0.0), 0, 0)}; p["Knee_Pole.L"] = {"at": (0.2, K.y - 0.1, K.z + 0.6)}; return p
def leg_extension(h): return _seated_leg(-5.0 + 85.0 * h)
def leg_curl(h): return _seated_leg(80.0 - 110.0 * h)

# ------------------------------------------------------------------ the cardio machines
def rower(t):
    """the rowing machine: t = 0..1 the drive (the legs push, then the torso swings back, then the arms pull the handle to the ribs), t = 1..2 the recovery (the arms go out, then the torso swings
    forward, then the knees bend). The feet stay on the footplate; the seat slides"""
    b = rig.data.bones; T = b["Thigh.L"].head_local; A0 = b["Foot_IK.L"].head_local; L = (T - A0).length
    if t <= 1.0: legs, torso, arms = _ease(t / 0.6), _ease((t - 0.3) / 0.5), _ease((t - 0.6) / 0.4)
    else: u = t - 1.0; arms, torso, legs = 1 - _ease(u / 0.3), 1 - _ease((u - 0.2) / 0.5), 1 - _ease((u - 0.5) / 0.5)
    fz, fy = 0.25, -0.80; hz = 0.42; d = (0.50 + 0.36 * legs) * L / 0.88 * 0.97; hy = fy + math.sqrt(max(0.0, d * d - (hz - fz) ** 2 - 0.095 ** 2 * 0))
    p = {"Hips": {"move": (0, hy - T.y, hz - T.z), "rot": (22.0 - 44.0 * torso, 0, 0)}, "Neck": {"rot": (-8 + 15 * torso, 0, 0)}, "Head": {"rot": (-8 + 12 * torso, 0, 0)},
         "Foot_IK.L": {"at": (0.19, fy, fz), "wrot": (-40.0, 0, 0)}, "Knee_Pole.L": {"at": (0.22, hy - 0.5, 1.0)}}
    S = _shoulder(p); Wa = S + Vector((0.08, -0.45, -0.12)); Wb = S + Vector((0.12, -0.12, -0.38))
    p.update(_hands(Wa + (Wb - Wa) * arms, S, (S.x + 0.5, S.y + 0.5, S.z - 0.1))); return p

def _crank(psi, cy, cz, r, hy, hz_extra=0.0, lean=35.0):
    b = rig.data.bones; T = b["Thigh.L"].head_local; A0 = b["Foot_IK.L"].head_local; L = (T - A0).length; out = {}
    low = Vector((0.12, cy, cz - r + 0.09)); hz = low.z + math.sqrt(max(0.0, (0.97 * L) ** 2 - (hy - cy) ** 2 - 0.03 ** 2)) + hz_extra
    out["Hips"] = {"move": (0, hy - T.y, hz - T.z), "rot": (lean, 0, 0)}; out["Neck"] = {"rot": (-lean * 0.5, 0, 0)}; out["Head"] = {"rot": (-lean * 0.5, 0, 0)}
    for side, ph in (("L", psi), ("R", psi + math.pi)):
        sg = 1 if side == "L" else -1; y = cy + r * math.sin(ph); z = cz + r * math.cos(ph) + 0.09
        out[f"Foot_IK.{side}"] = {"at": (sg * 0.12, y, z), "wrot": (6.0 * math.cos(ph), 0, 0)}; out[f"Knee_Pole.{side}"] = {"at": (sg * 0.14, hy - 0.5, z + 0.9)}
    return out

def cycling(psi):
    """an upright exercise bike: the feet go round the pedals (psi = the left crank's angle; 0 = at the top), the hands rest on the bars, the torso leaning forward 35 degrees"""
    p = _crank(psi, -0.12, 0.30, 0.17, 0.12); S = _shoulder(p); p.update(_hands((S.x + 0.03, -0.50, 1.05), S, (S.x + 0.5, S.y + 0.5, S.z - 0.1))); return p

def assault_bike(psi):
    """the fan bike: pedalling as the exercise bike, with the handles pumping back and forth opposite to the legs (each hand moves with the opposite foot)"""
    p = _crank(psi, -0.12, 0.30, 0.17, 0.12, 0.0, 20.0); S = _shoulder(p)
    for side in "LR":
        sg = 1 if side == "L" else -1; ph = psi + math.pi * (1 if side == "L" else 0)
        W = Vector((sg * 0.25, -0.46 + 0.15 * math.sin(ph + math.pi), 1.08)); Sx = pose_bones()[f"UpperArm.{side}"].head.copy()
        p[f"Hand_IK.{side}"] = {"at": tuple(_lim(W, Sx)), "wrot": (0, 0, -90 * sg), "props": {"fist": 0.8}}; p[f"Elbow_Pole.{side}"] = {"at": (Sx.x + sg * 0.5, Sx.y + 0.5, Sx.z - 0.1)}
    return p

def stair_climber(psi):
    """a stair-stepping machine: the two steps rise and fall in opposite turn (psi = the left step's phase), the hips stay level, the hands rest on the rails"""
    b = rig.data.bones; T = b["Thigh.L"].head_local; A0 = b["Foot_IK.L"].head_local; L = (T - A0).length; out = {}
    out["Hips"] = {"move": (0, 0.0, 0.0 - 0.02), "rot": (10.0, 0, 0)}
    for side, ph in (("L", psi), ("R", psi + math.pi)):
        sg = 1 if side == "L" else -1; z = 0.26 + 0.13 * math.sin(ph)
        out[f"Foot_IK.{side}"] = {"at": (sg * 0.14, 0.0, z), "wrot": (0, 0, 0)}; out[f"Knee_Pole.{side}"] = {"at": (sg * 0.14, -0.6, z + 0.5)}
    S = _shoulder(out); out.update(_hands((S.x + 0.1, -0.30, 1.12), S, (S.x + 0.5, S.y + 0.5, S.z - 0.1))); return out

def elliptical(psi):
    """an elliptical trainer: the feet glide forward and back on a flat oval (psi = the left foot's phase) and the handles swing with the opposite foot"""
    b = rig.data.bones; T = b["Thigh.L"].head_local; out = {}
    out["Hips"] = {"move": (0, 0.0, -0.03), "rot": (6.0, 0, 0)}
    for side, ph in (("L", psi), ("R", psi + math.pi)):
        sg = 1 if side == "L" else -1; y = 0.02 + 0.22 * math.cos(ph); z = 0.22 + 0.07 * math.sin(ph)
        out[f"Foot_IK.{side}"] = {"at": (sg * 0.14, y, z), "wrot": (0, 0, 0)}; out[f"Knee_Pole.{side}"] = {"at": (sg * 0.14, y - 0.6, z + 0.5)}
    _apply_pose(out); P = pose_bones()
    for side in "LR":
        sg = 1 if side == "L" else -1; ph = psi + math.pi * (0 if side == "L" else 1) + math.pi; S = P[f"UpperArm.{side}"].head.copy()
        W = Vector((sg * 0.26, -0.30 + 0.18 * math.cos(ph), 1.10)); out[f"Hand_IK.{side}"] = {"at": tuple(_lim(W, S)), "wrot": (0, 0, -90 * sg), "props": {"fist": 0.8}}
        out[f"Elbow_Pole.{side}"] = {"at": (S.x + sg * 0.5, S.y + 0.5, S.z - 0.1)}
    return out

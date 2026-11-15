"""pushup_var.py - push-ups with the hands or the feet raised: the incline push-up (hands on the bench), the decline push-up (feet on the bench) and the wall push-up (hands on a wall). Loaded with
python = ["moves.py", "pushup.py", "poselib.py", "pushup_var.py"].

The plain push-up (pushup.py) turns the whole body about its toes by an angle phi. Here the same body is turned about a pivot at another place (the decline: the toes on the bench) with the hands at another
place, and for each variant the script SOLVES the angle at which the shoulders are exactly one straight arm's length from the hands (the top) and one bent arm's length (the bottom), using the distances the
plain push-up has. So nothing here is measured by eye: the lengths come from the rig through pushup.py.
"""
import math
from mathutils import Vector

_PV = {}
def _shoulder(phi, py, pz):
    return rigid(_B0, (0, py, pz), phi)(_S0)

def _solve(hand, d, py, pz, lo, hi):
    """the first angle from `lo` on at which the shoulder is as near as `d` to `hand` (a scan, then bisection; if it never gets that near, the nearest it gets)"""
    f = lambda p: (_shoulder(p, py, pz) - hand).length - d
    p = lo
    while p < hi and f(p + 1.0) > 0 and f(p + 1.0) < f(p): p += 1.0
    if f(p + 1.0) > 0: return p                                                        # never reaches d: stop at the nearest point
    a, b = p, p + 1.0
    for _ in range(40):
        m = (a + b) / 2
        if f(m) > 0: a = m
        else: b = m
    return (a + b) / 2

def _setup(kind):
    if kind in _PV: return _PV[kind]
    H0 = Vector((HAND_X, _HAND_Y, HAND_Z)); d_up = (_shoulder(PHI_UP, Y_PIVOT, Z_PIVOT) - H0).length; d_dn = (_shoulder(PHI_DN, Y_PIVOT, Z_PIVOT) - H0).length
    if kind == "incline":      py, pz, hz = 1.0, Z_PIVOT, 0.475 + HAND_Z                   # the hands on the pad of the bench (47.5 cm), the toes on the floor
    elif kind == "decline":    py, pz, hz = 0.5, 0.475 + Z_PIVOT, HAND_Z                   # the toes on the bench, the hands on the floor
    elif kind == "wall":       py, pz, hz = Y_PIVOT, Z_PIVOT, None
    if kind == "wall":                                                                      # the hands on a wall at shoulder height, the arms level when straight
        phi_up = 24.0; S = _shoulder(phi_up, py, pz); hand = Vector((HAND_X, S.y - d_up, S.z)); lo, hi = phi_up, 80.0
    else:
        lo, hi = 20.0, 110.0
        a, b = lo, hi                                                                       # the top: the shoulder is d_up's vertical height over the hand (arm straight down)
        g = lambda p: _shoulder(p, py, pz).z - (hz + (_shoulder(PHI_UP, Y_PIVOT, Z_PIVOT).z - HAND_Z))
        for _ in range(60):
            m = (a + b) / 2
            if g(m) > 0: a = m
            else: b = m
        phi_up = (a + b) / 2; S = _shoulder(phi_up, py, pz); hand = Vector((HAND_X, S.y, hz))
        lo, hi = phi_up, 125.0
    if kind == "wall": phi_dn = _solve(hand, d_dn, py, pz, lo, hi)
    else:                                                                                   # the shoulders drop as far above the hands as they do in the plain push-up
        dz = _shoulder(PHI_DN, Y_PIVOT, Z_PIVOT).z - HAND_Z; a, b = phi_up, 125.0
        for _ in range(60):
            m = (a + b) / 2
            if _shoulder(m, py, pz).z > hand.z + dz: a = m
            else: b = m
        phi_dn = (a + b) / 2
    _PV[kind] = dict(py=py, pz=pz, hand=hand, up=phi_up, dn=phi_dn); return _PV[kind]

def pushup_variant(kind, u):
    """the push-up variant `kind` ("incline", "decline", "wall") at u = 0 (top, arms straight) .. 1 (bottom). No arms are left to place: the hands are planted on the bench, floor or wall"""
    global Y_PIVOT, Z_PIVOT, HAND_Z, _HAND_Y
    C = _setup(kind); phi = C["up"] + (C["dn"] - C["up"]) * u; keep = (Y_PIVOT, Z_PIVOT, HAND_Z, _HAND_Y)
    try:
        Y_PIVOT, Z_PIVOT, HAND_Z, _HAND_Y = C["py"], C["pz"], C["hand"].z, C["hand"].y
        p = pushup_pose(phi, hand_x=C["hand"].x, pole_out=0.4)
    finally:
        Y_PIVOT, Z_PIVOT, HAND_Z, _HAND_Y = keep
    k = min(1.0, phi / 88.0); p["Neck"] = {"rot": (-18 * k, 0, 0)}; p["Head"] = {"rot": (-28 * k, 0, 0)}
    p["Hand_IK.L"] = {**p["Hand_IK.L"], "at": tuple(C["hand"]), "wrot": (90, 0, -90) if kind == "wall" else (0, 0, -90)}
    for sp in ("Spine", "Spine1", "Spine2"): p.setdefault(sp, {"rot": (0, 0, 0)})
    return p

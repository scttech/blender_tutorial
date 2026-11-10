"""kbswing.py - Step 16: the two-handed kettlebell (Russian) swing, as a keyframe table (see tools/anim_core.py).

    G = {"bpy": bpy}; exec(open(".../anim_core.py").read(), G); exec(open(".../exercises/kbswing.py").read(), G)      # G["KBSWING"]

The PROP LEADS and the hands follow: grab_kb_swing = 1 for the whole loop, so each hand control is snapped to a grip on the kettlebell, and
the bell is the thing we place. It hangs from straight-ish arms and swings like a pendulum about the shoulders by the angle alpha:
    alpha = 0 hanging straight down, +90 arms horizontal in front, negative = swung back between the legs
The BODY is choreographed to match: a hip hinge (the Hips turn forward by phi, the hips travel back by dy) with the knees bending to a chosen angle.
Per key the script
  1. SOLVES the hip height that gives the chosen knee bend (bisection), with the feet planted in a wide stance;
  2. reads where the shoulders are in that pose;
  3. puts the bell on a circle of radius RW about the shoulders at angle alpha, turned by -alpha so the hand frame still lies along the arm.
30 fps, a 1.77 s loop, keyed every 2 frames. The hips lead the bell: they are already extending when the bell is still low.
"""
import math
import numpy as np
from mathutils import Vector, Matrix, Euler

STANCE = globals().get("STANCE", 0.34)          # feet this far either side of the centre (the bell has to pass between the legs; the rest stance is 0.19)
POLE_OUT = globals().get("POLE_OUT", 0.08)        # how far the knee poles sit outside the feet: pushes the knees out
RW = 0.49                     # shoulder-to-wrist distance on the arc: a little under the 0.53 m arm, so the arms stay just off straight
BOTTOM, END, HINGE, KNEE, BACK = 27, 53, 62.0, 32.0, 0.28      # the bell is lowest at frame 27; the loop ends at 53; extra hinge (degrees), extra knee bend (degrees), hips back (m)
ALPHA_TOP, ALPHA_BOTTOM = 80.0, -48.0                         # arm angle at the top (almost horizontal) and at the bottom (swung back between the legs)
HIPS_DONE = 48                                                # on the way up the hips have finished extending at this frame, five frames BEFORE the bell tops out
DOWN_START, DOWN_DONE = globals().get("DOWN_START", 3), globals().get("DOWN_DONE", 21)   # down: the hips hinge between these frames, EARLY, so they are back before the bell passes under them
UP_POWER = globals().get("UP_POWER", 1.6)                     # up: >1 keeps the hips back a little longer, then snaps them forward

def _ease(x): return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, x)))        # 0 -> 1 with a gentle start and finish

def swing_params(f):
    """the whole motion as smooth functions of the frame. Down: the bell falls and the hips hinge early, so the hips are already back when the
    bell passes under them. Up: the hips hold back, then drive forward and finish their extension before the bell finishes rising (the 'snap')."""
    if f <= BOTTOM:
        alpha = ALPHA_TOP + (ALPHA_BOTTOM - ALPHA_TOP) * _ease((f - 1) / (BOTTOM - 1))
        hinge = _ease((f - DOWN_START) / (DOWN_DONE - DOWN_START))               # 0 = standing tall, 1 = fully hinged
    else:
        alpha = ALPHA_BOTTOM + (ALPHA_TOP - ALPHA_BOTTOM) * _ease((f - BOTTOM) / (END - BOTTOM))
        hinge = 1 - _ease(max(0.0, (f - BOTTOM) / (HIPS_DONE - BOTTOM)) ** UP_POWER)
    return dict(alpha=alpha, phi=HINGE * hinge, kappa=6.0 + KNEE * hinge, dy=BACK * hinge)

_b = rig.data.bones
_FOOT0, _POLE0 = _b["Foot_IK.L"].head_local.copy(), _b["Knee_Pole.L"].head_local.copy()
_BELL0 = _b["Kettlebell"].head_local.copy()
_WRIST_LOCAL = ((_b["KBSwing_Grip.L"].head_local + _b["KBSwing_Grip.R"].head_local) / 2) - _BELL0     # the wrists' midpoint in the bell's own frame

def _apply(spec):
    for frame, flat in expand([(1, spec)], True):
        for c, v in flat.items(): write(c, v)
    rig.update_tag(); bpy.context.view_layer.update()

def body_pose(phi, dy, dz):
    return {"Hips": {"move": (0, dy, dz), "rot": (phi, 0, 0)},
            "Foot_IK.L": {"at": (STANCE, _FOOT0.y, _FOOT0.z), "wrot": (0, 0, 0)}, "Knee_Pole.L": {"at": (STANCE + POLE_OUT, _POLE0.y, _POLE0.z)}}

def _knee_bend(spec):
    _apply(spec); P = pose_bones()
    th = (P["Thigh.L"].tail - P["Thigh.L"].head).normalized(); sh = (P["Shin.L"].tail - P["Shin.L"].head).normalized()
    return math.degrees(th.angle(sh))

def solve_dz(phi, dy, kappa):
    """the hip height at which the knee has bent by kappa degrees (the knee bends more as the hips drop)"""
    lo, hi = -0.60, 0.05
    for _ in range(22):
        mid = (lo + hi) / 2
        if _knee_bend(body_pose(phi, dy, mid)) > kappa: lo = mid          # too bent: raise the hips
        else: hi = mid
    return (lo + hi) / 2

def swing_pose(alpha, phi, kappa, dy):
    dz = solve_dz(phi, dy, kappa); spec = body_pose(phi, dy, dz); _apply(spec); P = pose_bones()
    S = (P["UpperArm.L"].head + P["UpperArm.R"].head) / 2                                  # the shoulders' midpoint
    a = math.radians(alpha); d = Vector((0, -math.sin(a), -math.cos(a)))                    # the arm's direction at this angle
    R = Euler((-a, 0, 0)).to_matrix()                                                       # the bell turns with the arm
    origin = (S + d * RW) - R @ _WRIST_LOCAL                                                # the bell's base centre, so the wrists land on the arc
    spec["Kettlebell"] = {"at": tuple(origin), "wrot": (-alpha, 0, 0)}
    spec["Hand_IK.L"] = {"props": {"grab_kb_swing": 1.0}}
    return spec

# keyed every 2 frames: a pendulum arc and the hip hinge are curved, and a few widely spaced keys would cut straight across them
KBSWING = [(f, swing_pose(**swing_params(f))) for f in range(1, END + 1, 2)]

def bell_extra():
    """per-frame measurements for measure(): the bell's clearance from the body, where it is, how far the hips have hinged, the arm angle"""
    reg = regions(); bell = bpy.data.objects["Kettlebell"]
    def extra(P, f):
        v, _ = mesh_state(); M = bell.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world
        centre = M @ Vector((0, 0, 0.10))                                          # the bell's round body is a sphere of radius 0.10
        up = P["Hips"].matrix.to_3x3().col[1]                                      # the pelvis' up direction
        S = (P["UpperArm.L"].head + P["UpperArm.R"].head) / 2; W = (P["ForeArm.L"].tail + P["ForeArm.R"].tail) / 2; d = W - S
        return {"bell_clear_mm": 1000 * float(np.linalg.norm(v[reg != "hands"] - np.array(centre), axis=1).min() - 0.10),
                "bell_y": centre.y, "bell_z": centre.z, "hinge_deg": math.degrees(math.atan2(-up.y, up.z)),
                "arm_deg": math.degrees(math.atan2(-d.y, -d.z))}
    return extra


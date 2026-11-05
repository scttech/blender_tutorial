"""cat_anim_jump.py - the Jump action.  Needs cat_anim_core.py first.

    build_jump()  -> action "Jump": crouch, launch, flight, landing, recover. 48 frames (2 s), in place.

The root bone carries the vertical arc (about 0.45 m up). If your game moves the character with physics, drop the root's
translation channel (or ignore it) and keep the rest. The feet leave and return to the same spot on the ground.
"""
JUMP_T, JUMP_FPS = 48, 24
J = dict(crouch=-0.32, height=0.45, land_dip=-0.25,
         t_crouch=0.22, t_to_f=0.27, t_to_h=0.33, t_land_f=0.62, t_land_h=0.66, t_dip=0.74, t_end=0.88)   # the front feet leave first, before the nose-up tilt lifts the shoulders out of reach

def _keys(t, pts):
    """Smooth interpolation through (time, value) waypoints."""
    if t <= pts[0][0]: return pts[0][1]
    for (a, va), (b, vb) in zip(pts, pts[1:]):
        if t <= b: return lerp(va, vb, smooth((t - a)/(b - a)))
    return pts[-1][1]

def _zbody(t):
    if t < J["t_crouch"]:                       return J["crouch"]*smooth(t/J["t_crouch"])                       # crouch down
    if t < J["t_to_h"]:                         return lerp(J["crouch"], 0.0, smooth((t - J["t_crouch"])/(J["t_to_h"] - J["t_crouch"]))**0.7)   # launch up (fast)
    if t < J["t_land_f"]:                       return J["height"]*4*((t - J["t_to_h"])/(J["t_land_f"] - J["t_to_h"]))*(1 - (t - J["t_to_h"])/(J["t_land_f"] - J["t_to_h"]))
    if t < J["t_dip"]:                          return J["land_dip"]*smooth((t - J["t_land_f"])/(J["t_dip"] - J["t_land_f"]))      # land and absorb
    return lerp(J["land_dip"], 0.0, smooth((t - J["t_dip"])/(J["t_end"] - J["t_dip"])))                                         # stand back up

_PITCH = [(0, 0), (0.12, 3), (0.22, 5), (0.27, -3), (0.33, -14), (0.47, -8), (0.62, 6), (0.72, 8), (0.88, 0), (1, 0)]   # body, degrees, + = nose down
_SPINE = [(0, 0), (0.22, 8), (0.27, 0), (0.33, -8), (0.47, -6), (0.62, 4), (0.72, 8), (0.88, 0), (1, 0)]
_HEAD  = [(0, 0), (0.22, -5), (0.33, -15), (0.50, -8), (0.62, 5), (0.75, 3), (1, 0)]                             # where the head points in the world, degrees

def _foot(L, t):
    """Toe-tip target: planted on the ground (at its standing spot) except in the air, where it reaches and tucks."""
    y0, z0 = REST[L][5]; front = L[1] == "F"
    t_to = J["t_to_f"] if front else J["t_to_h"]; t_land = J["t_land_f"] if front else J["t_land_h"]
    planted = np.array([y0, z0])
    if t <= t_to or t >= t_land: return dict(tip=planted, contact=True)
    u = (t - t_to)/(t_land - t_to)
    w = smooth(u/0.25)*smooth((1 - u)/0.25)                           # 0 at takeoff and landing (planted), 1 in mid-air (follows the hips)
    rest_off = REST[L][5] - REST[L][0]                                # where the foot hangs below the hip when standing
    s = math.sin(math.pi*u)**1.5
    off = rest_off + s*np.array([-0.30 if front else 0.28, 0.12 if front else 0.05])      # front legs reach forward, hind legs stretch back; both tuck up a little
    return dict(tip=planted, rel=(off, w), contact=False)

def _jump_frame(t):
    pitch = math.radians(_keys(t, _PITCH)); spine = math.radians(_keys(t, _SPINE)); head = math.radians(_keys(t, _HEAD))
    fly = _arc_between(t, J["t_to_h"], J["t_land_f"])
    body = dict(dz=_zbody(t), pitch=pitch, spine=spine, neck=head - pitch - spine,
                tail=tail_quats(-math.radians(12)*fly, list(TAIL_STRAIGHTEN), pitch))
    tips = {}
    for L in LEGS:
        tg = _foot(L, t); contact = tg["contact"]
        tips[L] = dict(tg, flat=0.0, w_flat=0.15 if contact else 0.03, extra=floor_guard(L) if contact else None)
    return dict(body=body, tips=tips)

def _arc_between(t, a, b):
    if not (a <= t <= b): return 0.0
    u = (t - a)/(b - a); return 4*u*(1 - u)

def build_jump():
    frames = solve_frames(JUMP_T, _jump_frame, cyclic=False, warm_from_rest=False)
    for fr in frames: fr["spec"]["tips"]  # (kept for report_gait)
    bake("Jump", frames)
    report_gait("Jump", frames)
    peak = max(f["loc"].length for f in frames)   # rough: location is in the root bone's own axes
    zmin, zf = scan_min_z(1, JUMP_T + 1, every=3)
    air = (J["t_land_f"] - J["t_to_h"])*JUMP_T/JUMP_FPS
    print("Jump built: %d frames (%.2f s) | airborne %.2f s | body rises to %.2f m | mesh lowest z over the jump %+.3f m (frame %d)"
          % (len(frames), (len(frames) - 1)/JUMP_FPS, air, J["height"], zmin, zf))
    return frames

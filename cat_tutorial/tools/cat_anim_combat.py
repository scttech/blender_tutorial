"""cat_anim_combat.py - PawSwipe and Bite.  Needs cat_anim_core.py first.

    build_swipe("right")  -> action "PawSwipe"  : wind up and swat forward with the right front paw. 30 frames, from and back to standing.
    build_bite()          -> action "Bite"      : crouch, lunge, snap the head, shake, recover. 36 frames, from and back to standing.

Both leave the TAIL alone (no tail channels), so TailSwish can play over them. Both start and end in the standing pose.
NOTE: the model's head has no jaw bone, so the mouth does not open. The "bite" is a head lunge and shake.
"""
BODY_ONLY = ["root", "spine", "neck_1", "neck_2"] + LEG_BONES            # everything except the tail

# ================================================================= PAW SWIPE
SWIPE_T = 30

def _swipe_frame_fn(side):
    arm_leg = "RF" if side == "right" else "LF"; other = "LF" if side == "right" else "RF"
    y0, z0 = REST[arm_leg][5]
    P_up, P_hit = np.array([y0 + 0.10, z0 + 0.62]), np.array([y0 - 0.55, z0 + 0.22])        # wind-up (raised, a little back), strike end (forward and low)
    def fn(t):
        if   t < 0.28: w = smooth(t/0.28);               tip = lerp(np.array([y0, z0]), P_up, w);  p = w                   # wind up
        elif t < 0.40: s = smooth((t - 0.28)/0.12);      tip = lerp(P_up, P_hit, s);               p = 1 + s               # strike (fast)
        elif t < 0.48: tip = P_hit.copy();                                                          p = 2.0                 # follow-through
        else:
            r = smooth((t - 0.48)/0.52); tip = lerp(P_hit, np.array([y0, z0]), r) + np.array([0.0, 0.10*math.sin(math.pi*r)]); p = 2*(1 - r)   # recover
        lean = _keys2(p, [(0, 0), (1, -1), (2, 1)])                                           # -1 = leaning back (wound up), +1 = leaning into the strike
        # leaning back must stay small (a nose-up lean lifts the shoulders out of reach of the planted paw) and is paired with a slight crouch
        pitch = math.radians(6 if lean > 0 else 2)*lean; spine = math.radians(4 if lean > 0 else 1)*lean
        head = math.radians(_keys2(p, [(0, 0), (1, -6), (2, 10)]))
        body = dict(dy=-0.07*lean, dz=-0.03*abs(lean) - 0.04*max(0.0, -lean), pitch=pitch, spine=spine, neck=head - pitch - spine)
        tips = {}
        for L in LEGS:
            if L == arm_leg: tips[L] = dict(tip=tip, flat=0.0, w_flat=0.02, contact=False)
            else:            tips[L] = dict(tip=REST[L][5], flat=0.0, w_flat=0.15, contact=True, extra=floor_guard(L))
        return dict(body=body, tips=tips)
    return fn

def _keys2(p, pts):
    if p <= pts[0][0]: return pts[0][1]
    for (a, va), (b, vb) in zip(pts, pts[1:]):
        if p <= b: return lerp(va, vb, (p - a)/(b - a))
    return pts[-1][1]

def build_swipe(side="right"):
    frames = solve_frames(SWIPE_T, _swipe_frame_fn(side), cyclic=False, warm_from_rest=False)
    name = "PawSwipe" if side == "right" else "PawSwipeLeft"
    bake(name, frames, only=BODY_ONLY)
    report_gait(name, frames)
    arm_leg = "RF" if side == "right" else "LF"
    pm_hit = make_pm(frame_basis(frames[int(0.44*SWIPE_T)])); pm_up = make_pm(frame_basis(frames[int(0.28*SWIPE_T)]))
    paw_hit = tailpos(pm_hit, LEGS[arm_leg][4]); paw_up = tailpos(pm_up, LEGS[arm_leg][4])
    zmin, zf = scan_min_z(1, SWIPE_T + 1, every=3)
    print("%s built: %d frames (%.2f s) | wind-up paw height %.2f m, strike reaches %.2f m ahead of the standing spot | mesh lowest z %+.3f m (frame %d)"
          % (name, len(frames), (len(frames) - 1)/24, paw_up.z, REST[arm_leg][5][0] - paw_hit.y, zmin, zf))
    return frames

# ================================================================= BITE
BITE_T = 36
def _bite_frame(t):
    pitch = math.radians(_kk(t, [(0, 0), (0.22, -5), (0.30, 12), (0.55, 10), (1.0, 0)]))
    spine = math.radians(_kk(t, [(0, 0), (0.22, -3), (0.30, 8), (0.55, 6), (1.0, 0)]))
    dz = _kk(t, [(0, 0), (0.22, -0.10), (0.30, -0.14), (0.55, -0.10), (0.85, 0), (1, 0)])
    dy = _kk(t, [(0, 0), (0.22, 0.06), (0.30, -0.32), (0.55, -0.28), (0.85, 0), (1, 0)])        # the body lunges forward over its planted feet
    head = math.radians(_kk(t, [(0, 0), (0.22, -10), (0.30, 18), (0.55, 14), (1.0, 0)]))      # where the head points in the world: up, then snapping down
    n = max(0.0, (t - 0.34)/0.21); shake = (math.radians(10)*math.sin(2*math.pi*3*n)*math.sin(math.pi*min(n, 1.0))) if 0 < n < 1 else 0.0   # 3 quick shakes while biting
    total = head - pitch - spine
    nq = neck_quats_vertical(0.4*total, 0.6*total, shake, pitch + spine)
    body = dict(dy=dy, dz=dz, pitch=pitch, spine=spine, neck_q=nq)
    tips = {L: dict(tip=REST[L][5], flat=0.0, w_flat=0.15, contact=True, extra=floor_guard(L)) for L in LEGS}
    return dict(body=body, tips=tips)

def _kk(t, pts):
    if t <= pts[0][0]: return pts[0][1]
    for (a, va), (b, vb) in zip(pts, pts[1:]):
        if t <= b: return lerp(va, vb, smooth((t - a)/(b - a)))
    return pts[-1][1]

def build_bite():
    frames = solve_frames(BITE_T, _bite_frame, cyclic=False, warm_from_rest=False)
    bake("Bite", frames, only=BODY_ONLY)
    report_gait("Bite", frames)
    nose = [tailpos(make_pm(frame_basis(f)), "nose") for f in frames]
    zmin, zf = scan_min_z(1, BITE_T + 1, every=3)
    print("Bite built: %d frames (%.2f s) | the nose lunges %.2f m forward and %.2f m down, shakes %.2f m side to side | mesh lowest z %+.3f m (frame %d)"
          % (len(frames), (len(frames) - 1)/24, nose[0].y - min(n.y for n in nose), nose[0].z - min(n.z for n in nose),
             max(n.x for n in nose[int(0.34*BITE_T):int(0.55*BITE_T)]) - min(n.x for n in nose[int(0.34*BITE_T):int(0.55*BITE_T)]), zmin, zf))
    return frames

"""cat_anim_gaits.py - Run (a gallop) and Crawl (a low stalking creep).  Needs cat_anim_core.py first.

    build_run()     -> action "Run"   : 20-frame gallop cycle, in place
    build_crawl()   -> action "Crawl" : 48-frame low creep cycle, in place

Both are IN PLACE (the model does not travel). Each build function prints the speed that stops the feet sliding on the ground.
The foot paths are planned, then the four legs are solved with IK from the moved hips (see Steps 11 and 12 of the tutorial).
"""
def _droop_for_floor(body_kw, yaws, clearance, root_pitch, max_deg=60):
    """Largest rigid tail droop that keeps every tail joint at least `clearance` above the floor."""
    def minz(d):
        q, loc = body_pose(**body_kw, tail=tail_quats(d, yaws, root_pitch))
        pm = make_pm(basis_dict(q, loc)); return min(tailpos(pm, n).z for n in TAIL)
    if minz(0.0) < clearance: return 0.0
    lo, hi = 0.0, math.radians(max_deg)
    for _ in range(40):
        mid = (lo + hi)/2; lo, hi = (mid, hi) if minz(mid) > clearance else (lo, mid)
    return lo

# ================================================================= RUN (gallop)
RUN_T, RUN_FPS = 20, 24
RUN_CFG = dict(
    offset=dict(RH=0.00, LH=0.07, RF=0.42, LF=0.50),        # hind pair lands, then the front pair; two flight phases (gathered and extended)
    duty={L: 0.28 for L in LEGS},                          # each foot is on the ground for 28% of the stride
    stride={L: 0.70 for L in LEGS},                        # how far the planted foot travels backward relative to the body (m)
    lift={L: 0.30 for L in LEGS},                          # how high the foot swings in the air (m)
    shift=dict(RF=-0.05, LF=-0.05, RH=0.10, LH=0.10))      # front feet reach forward, hind feet push from behind
RUN_DZ = -0.12                                             # the body runs low: this keeps the planted legs within reach
def _arc(t, a, b):                                         # 0 outside [a, b], a parabola 0..1..0 inside
    if not (a <= t <= b): return 0.0
    u = (t - a)/(b - a); return 4*u*(1 - u)

def _run_frame(t):
    z = RUN_DZ + 0.22*_arc(t, 0.78, 1.0) + 0.08*_arc(t, 0.35, 0.42)                        # body: low in contact, up in the two flights
    spine = math.radians(7)*bump(t, 0.385, 0.06) - math.radians(7)*bump(t, 0.89, 0.09)    # flexed when gathered, extended when stretched
    yaws = [TAIL_STRAIGHTEN[i] + math.radians((3, 5, 7, 9, 11)[i])*math.sin(2*math.pi*t - i*0.5) for i in range(5)]
    body = dict(dz=z, spine=spine, neck=math.radians(5) - spine,                             # head held steady, slightly down
                tail=tail_quats(-math.radians(8), yaws, 0.0))                                 # tail streaming out behind
    tips = {}
    for L in LEGS:
        tip, contact = foot_target(L, t, RUN_CFG)
        tips[L] = dict(tip=tip, flat=0.0, w_flat=0.15 if contact else 0.04, contact=contact, extra=floor_guard(L) if contact else None)
    return dict(body=body, tips=tips)

def build_run():
    frames = solve_frames(RUN_T, _run_frame, cyclic=True)
    bake("Run", frames)
    report_gait("Run", frames)
    v = RUN_CFG["stride"]["RF"]/(RUN_CFG["duty"]["RF"]*RUN_T/RUN_FPS)
    zmin, zf = scan_min_z(1, RUN_T, every=2)
    print("Run built: %d frames (%.2f s) | speed that stops the feet sliding: %.1f m/s | mesh lowest z over the cycle %+.3f m (frame %d)"
          % (len(frames), (len(frames) - 1)/RUN_FPS, v, zmin, zf))
    G["RUN_SPEED"] = v
    return frames

# ================================================================= CRAWL (low stalking creep)
CRAWL_T, CRAWL_FPS = 48, 24
CRAWL_DZ, CRAWL_PITCH, CRAWL_SPINE = -0.50, math.radians(4), math.radians(3)
CRAWL_CFG = dict(
    offset=dict(RH=0.00, RF=0.25, LH=0.50, LF=0.75),
    duty={L: 0.75 for L in LEGS}, stride={L: 0.25 for L in LEGS}, lift={L: 0.07 for L in LEGS},
    shift=dict(RF=0.0, LF=0.0, RH=0.0, LH=0.0))

def _crawl_frame(t, droop=None):
    z = CRAWL_DZ + 0.012*math.sin(4*math.pi*t)                                               # tiny shoulder roll with each footfall
    yaws = [TAIL_STRAIGHTEN[i] + math.radians((6, 8, 10, 12, 14)[i])*math.sin(2*math.pi*t - i*0.5) for i in range(5)]
    body_kw = dict(dz=CRAWL_DZ, pitch=CRAWL_PITCH, spine=CRAWL_SPINE, neck=math.radians(12) - CRAWL_PITCH - CRAWL_SPINE)
    d = G["CRAWL_DROOP"] if droop is None else droop
    body = dict(body_kw, dz=z, tail=tail_quats(d, yaws, CRAWL_PITCH))
    tips = {}
    for L in LEGS:
        tip, contact = foot_target(L, t, CRAWL_CFG)
        tips[L] = dict(tip=tip, flat=0.0, w_flat=0.3 if contact else 0.05, contact=contact, extra=floor_guard(L))
    return dict(body=body, tips=tips)

def build_crawl():
    yaws0 = list(TAIL_STRAIGHTEN)
    G["CRAWL_DROOP"] = _droop_for_floor(dict(dz=CRAWL_DZ, pitch=CRAWL_PITCH, spine=CRAWL_SPINE, neck=math.radians(12) - CRAWL_PITCH - CRAWL_SPINE),
                                        yaws0, TAIL_CLEARANCE if "TAIL_CLEARANCE" in G else 0.125, CRAWL_PITCH)
    frames = solve_frames(CRAWL_T, _crawl_frame, cyclic=True)
    bake("Crawl", frames)
    report_gait("Crawl", frames)
    v = CRAWL_CFG["stride"]["RF"]/(CRAWL_CFG["duty"]["RF"]*CRAWL_T/CRAWL_FPS)
    zmin, zf = scan_min_z(1, CRAWL_T, every=4)
    print("Crawl built: %d frames (%.2f s) | tail droop %.1f deg | speed that stops the feet sliding: %.2f m/s | mesh lowest z over the cycle %+.3f m (frame %d)"
          % (len(frames), (len(frames) - 1)/CRAWL_FPS, math.degrees(G["CRAWL_DROOP"]), v, zmin, zf))
    G["CRAWL_SPEED"] = v
    return frames

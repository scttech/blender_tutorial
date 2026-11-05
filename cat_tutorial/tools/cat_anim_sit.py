"""cat_anim_sit.py - the Sit action and the SitTailSwish action.  Needs cat_anim_core.py exec'd into the same dict first.

    build_sit()              -> action "Sit": standing -> sitting, 61 frames. The tail is straightened as the cat sits.
    build_sit_tail_swish()   -> action "SitTailSwish": the tail sweeps along the floor, eased in and out, starting and ending in the Sit pose.

Both store the finished sitting pose in this module's namespace as SIT_FINAL so LookAround, LickPaw and others can start from it.
"""
THETA, PY, PZ, HOCK_Z, HEAD_UP, HOCK_BEHIND = math.radians(37), 0.20, 0.398, 0.153, math.radians(15), 0.08
SIT_T = 60
TAIL_CLEARANCE = 0.125         # the tail tube is ~12 cm thick around its bones, so keep the tail joints this high above the floor
_pivot = yz(bones["root"].head_local)
_a_flat = wrap(ang(np.array([-1.0, 0.0])) - ang(REST["RH"][3] - REST["RH"][2]))     # rotation that lays the metatarsus flat, pointing forward

def _sit_frame_fn(tail_droop):
    def fn(t):
        s = smooth(t); d = np.array([PY, PZ]) - _pivot
        body = dict(dy=float(d[0]*s), dz=float(d[1]*s), pitch=-THETA*s, neck=(THETA - HEAD_UP)*s,
                    tail=tail_quats(tail_droop*s, [y*s for y in TAIL_STRAIGHTEN], -THETA*s))
        tips = {}
        for L in LEGS:
            if L[1] == "F":
                tips[L] = dict(tip=REST[L][5], flat=0.0, contact=True)                 # front paws stay planted
            else:
                h0 = REST[L][2]
                def extra(Q, A, s=s, h0=h0):                                           # hind: heel to the ground, just behind the hip; metatarsus laid flat
                    ht = np.array([lerp(h0[0], Q[0][0] + HOCK_BEHIND, s), lerp(h0[1], HOCK_Z, s)])
                    return np.concatenate([Q[2] - ht, [0.15*(A[2] - _a_flat*s)]])
                tips[L] = dict(tip=None, flat=0.0, extra=extra)
        return dict(body=body, tips=tips)
    return fn

def _tail_min_z(droop):
    d = np.array([PY, PZ]) - _pivot
    q, loc = body_pose(dy=float(d[0]), dz=float(d[1]), pitch=-THETA, neck=THETA - HEAD_UP, tail=tail_quats(droop, TAIL_STRAIGHTEN, -THETA))
    pm = make_pm(basis_dict(q, loc)); return min(tailpos(pm, n).z for n in TAIL)

def build_sit():
    lo, hi = 0.0, math.radians(75)
    for _ in range(40):                                           # droop the (straightened) tail until it just clears the floor
        mid = (lo + hi)/2; lo, hi = (mid, hi) if _tail_min_z(mid) > TAIL_CLEARANCE else (lo, mid)
    A = (lo + hi)/2
    frames = solve_frames(SIT_T, _sit_frame_fn(A), cyclic=False, warm_from_rest=False)
    bake("Sit", frames)
    drift = {L: 0.0 for L in ("RF", "LF")}
    for fr in frames:
        pm = make_pm(frame_basis(fr))
        for L in drift:
            tp = tailpos(pm, LEGS[L][4]); drift[L] = max(drift[L], math.hypot(tp.y - REST[L][5][0], tp.z - REST[L][5][1])*100)
    scene.frame_set(SIT_T + 1)
    print("Sit built: %d frames | tail droop %.1f deg | front paw drift RF %.2f / LF %.2f cm | mesh lowest z in the final pose %+.3f m" % (len(frames), math.degrees(A), drift["RF"], drift["LF"], mesh_min_z()))
    G["SIT_FINAL"], G["SIT_DROOP"] = frames[-1], A
    return frames

def build_sit_tail_swish(T=96, cycles=3, amp_deg=(5, 8, 11, 14, 17), lag=0.5, ramp=16):
    fin, A = G["SIT_FINAL"], G["SIT_DROOP"]
    set_pose(fin); frames = []; zmin = 1e9
    for k in range(T + 1):
        t = k/T; env = smooth(k/ramp)*smooth((T - k)/ramp)             # 0 at both ends: starts and ends exactly in the Sit pose
        yaws = [TAIL_STRAIGHTEN[i] + env*math.radians(amp_deg[i])*math.sin(2*math.pi*cycles*t - i*lag) for i in range(5)]
        q = dict(fin["q"])
        for n, tq in zip(TAIL, tail_quats(A, yaws, -THETA)): q[n] = tq
        fr = dict(q=q, loc=fin["loc"], legs=fin["legs"]); frames.append(fr)
        pm = make_pm(frame_basis(fr)); zmin = min(zmin, min(tailpos(pm, n).z for n in TAIL))
    bake("SitTailSwish", frames, only=TAIL, reset=False)
    ends = max((frames[0]["q"][n].rotation_difference(fin["q"][n])).angle for n in TAIL)
    print("SitTailSwish built: %d frames | lowest tail joint z over the loop %.3f m | start vs Sit pose %.6f rad" % (len(frames), zmin, ends))
    return frames

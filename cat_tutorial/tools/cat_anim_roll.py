"""cat_anim_roll.py - RollLeft and RollRight.  Needs cat_anim_core.py first.

    build_roll("left")   -> action "RollLeft" : the cat tucks, rolls a full 360 degrees LEFT side down first, and stands back up. 48 frames.
    build_roll("right")  -> action "RollRight": the mirror image.

In place: the model does not travel sideways. The root bone rotates about the world Y axis (the body's long axis); the root's height
follows the real mesh so the cat rolls ALONG the ground (measured at 16 roll angles with the deformed mesh, then interpolated).
"""
ROLL_T = 48
SPINE_CURL, NECK_TUCK = math.radians(12), math.radians(25)
TUCK_OFFSET = dict(F=np.array([-0.30, -0.45]), H=np.array([-0.22, -0.40]))      # where the paws go, relative to their hip, when tucked

def _solve_tuck():
    q, loc = body_pose(spine=SPINE_CURL, neck=NECK_TUCK)
    pm = make_pm(basis_dict(q, loc)); xs = {}
    for L in LEGS:
        hip, beta = leg_frame(pm, L); goal = hip + TUCK_OFFSET[L[1]]; x = np.zeros(4)
        for i in range(1, 13):                                      # ease the paws in from the standing pose so the knees keep bending the right way
            x = solve_leg(L, hip, beta, lerp(REST[L][5], goal, i/12), x, flat=0.0, w_flat=0.0)
        xs[L] = x
    return xs

def _contact_dz(sign, x_tuck, n=16):
    """For roll angles 0..360 degrees: how far to move the root so the lowest point of the (deformed) mesh just touches the ground."""
    angs, dzs = [], []
    for i in range(n + 1):
        rho = sign*2*math.pi*i/n
        q, loc = body_pose(roll=rho, spine=SPINE_CURL, neck=NECK_TUCK)
        set_pose(dict(q=q, loc=loc, legs=x_tuck))
        angs.append(2*math.pi*i/n); dzs.append(-mesh_min_z())
    dzs[-1] = dzs[0]
    return np.array(angs), np.array(dzs)

def _phase(t):
    """k: 0 standing -> 1 fully tucked (and back); r: 0..1 progress of the roll."""
    k = smooth(t/0.20)*smooth((1 - t)/0.20)
    r = smooth((t - 0.20)/0.60)
    return k, r

def build_roll(side):
    sign = 1.0 if side == "left" else -1.0       # rotation about +Y by +90 deg takes the cat's left side (+X) down to the floor and its back toward +X.
                                                 # (Checked by measuring the paws: do not trust the mental picture, see the tutorial.)
    x_tuck = _solve_tuck()
    angs, dzs = _contact_dz(sign, x_tuck)
    print("Roll %s: tucked pose solved | root height needed to touch the ground: %.2f m (on its feet) to %.2f m (on its back/side)"
          % (side, dzs.min(), dzs.max()))
    frames = []
    for k_ in range(ROLL_T + 1):
        t = k_/ROLL_T; k, r = _phase(t)
        a = 2*math.pi*r; dz = k*float(np.interp(a, angs, dzs))
        q, loc = body_pose(dz=dz, roll=sign*a, spine=SPINE_CURL*k, neck=NECK_TUCK*k)
        frames.append(dict(q=q, loc=loc, legs={L: x_tuck[L]*k for L in LEGS}, spec=dict(tips={L: dict(tip=None) for L in LEGS})))
    name = "RollLeft" if side == "left" else "RollRight"
    bake(name, frames)
    zmin, zf = scan_min_z(1, ROLL_T + 1, every=3)
    st = frames[0]["q"]["root"]; en = frames[-1]["q"]["root"]
    print("%s built: %d frames (%.2f s) | lowest mesh point over the roll %+.3f m (frame %d) | root rotation at the end vs the start: %.6f"
          % (name, len(frames), (len(frames) - 1)/24, zmin, zf, 1 - abs(st.dot(en))))
    return frames

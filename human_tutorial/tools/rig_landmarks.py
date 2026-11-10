"""rig_landmarks.py - Step 5: the bone layout as data. Step 6 builds the armature from this.

    exec(open(".../rig_landmarks.py").read(), G)      # then G["BONES"] is a list of (name, head, tail, parent)

Conventions (Blender world space, the character stands on z=0 and faces -Y)
  * +X is the character's LEFT, so ".L" bones live at +X and ".R" bones are mirrored to -X
  * every position was measured on the high-poly reference (Body_HighPoly), not guessed - see Step 5
  * the arms are straight out along X (T-pose) at z = 1.45; the legs splay outward by about 5 degrees
"""

SPINE_Y = 0.06                      # the spine sits in the back third of the torso, not at y=0

# ---- centre line: (name, head, tail, parent) ---------------------------------------------------------
CENTRE = [
    ("Root",   (0, SPINE_Y, 0.00), (0, SPINE_Y, 0.12), None),
    ("Hips",   (0, SPINE_Y, 0.97), (0, SPINE_Y, 1.07), "Root"),
    ("Spine",  (0, SPINE_Y, 1.07), (0, SPINE_Y, 1.22), "Hips"),
    ("Spine1", (0, SPINE_Y, 1.22), (0, SPINE_Y, 1.38), "Spine"),
    ("Spine2", (0, SPINE_Y, 1.38), (0, SPINE_Y, 1.54), "Spine1"),
    ("Neck",   (0, 0.05, 1.54),    (0, 0.00, 1.66),    "Spine2"),
    ("Head",   (0, 0.00, 1.66),    (0, 0.00, 1.870),   "Neck"),
]

# ---- left arm and leg ---------------------------------------------------------------------------------
LEFT = [
    ("Clavicle.L", (0.03, 0.05, 1.50), (0.19, 0.06, 1.45), "Spine2"),
    # the elbow sits 1.5 cm BEHIND the shoulder-wrist line (a 6 degree pre-bend). A perfectly straight arm gives IK no bend
    # direction, so the solver twists the shoulder instead of hinging the elbow (found in Step 10)
    ("UpperArm.L", (0.19, 0.06, 1.45), (0.49, 0.075, 1.45), "Clavicle.L"),
    ("ForeArm.L",  (0.49, 0.075, 1.45), (0.72, 0.06, 1.447), "UpperArm.L"),
    ("Hand.L",     (0.72, 0.06, 1.447), (0.826, 0.053, 1.435), "ForeArm.L"),
    ("Thigh.L",    (0.095, 0.03, 0.97), (0.134, 0.045, 0.55), "Hips"),
    ("Shin.L",     (0.134, 0.045, 0.55), (0.186, 0.075, 0.10), "Thigh.L"),
    ("Foot.L",     (0.186, 0.075, 0.10), (0.195, -0.075, 0.035), "Shin.L"),
    ("Toes.L",     (0.195, -0.075, 0.035), (0.197, -0.148, 0.036), "Foot.L"),
]

# ---- left hand: knuckle (MCP) and tip of each finger, measured on the fingertip profile ---------------------
FINGER_Z = 1.432
FINGERS = {            # name: (y lane, MCP x, tip x). Tips end ~8 mm inside the skin; the right hand is 7 mm shorter than the left
    "Index":  (0.028, 0.822, 0.930),
    "Middle": (0.053, 0.826, 0.943),
    "Ring":   (0.074, 0.820, 0.931),
    "Pinky":  (0.097, 0.805, 0.905),
}
SEGMENTS = (0.45, 0.30, 0.25)       # proximal, middle, distal share of the finger length

def _fingers():
    out = []
    for name, (y, x0, x1) in FINGERS.items():
        xs = [x0, x0 + SEGMENTS[0] * (x1 - x0), x0 + (SEGMENTS[0] + SEGMENTS[1]) * (x1 - x0), x1]
        for i in range(3):
            out.append((f"{name}{i+1}.L", (xs[i], y, FINGER_Z), (xs[i+1], y, FINGER_Z),
                        "Hand.L" if i == 0 else f"{name}{i}.L"))
    thumb = [(0.760, 0.045, 1.435), (0.798, 0.016, 1.432), (0.838, 0.006, 1.432), (0.862, 0.004, 1.432)]
    for i in range(3):
        out.append((f"Thumb{i+1}.L", thumb[i], thumb[i+1], "Hand.L" if i == 0 else f"Thumb{i}.L"))
    return out

def _mirror(bones):
    sw = lambda s: s[:-2] + ".R" if s and s.endswith(".L") else s
    return [(sw(n), (-h[0], h[1], h[2]), (-t[0], t[1], t[2]), sw(p)) for n, h, t, p in bones]

LEFT_ALL = LEFT + _fingers()
BONES = CENTRE + LEFT_ALL + _mirror(LEFT_ALL)      # 7 + 23 + 23 = 53 deform bones

if __name__ == "__main__":
    print(len(BONES), "bones")

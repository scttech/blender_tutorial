"""build_prop_rig.py - Steps 12 and 15: control bones for the props, grip bones for the hands, and "grab" sliders.

Run after build_props.py, build_controls.py and build_finger_controls.py:   exec(open(".../build_prop_rig.py").read(), {})
Safe to re-run.

  1. MEASURE the grip. In the hand's own coordinates, find where a handle should sit in the palm and how far the fingers and
     thumb should close, so the finger bones wrap the handle (each runs one finger-radius outside its surface).
  2. Add prop control bones  Kettlebell, Mace, PullupBar  (props are parented to them) and grip bones  KB_Grip.L/R, Mace_Grip.L/R,
     BarOver_Grip.L/R, BarUnder_Grip.L/R, KBSwing_Grip.L/R  (children of the prop bones; each is the exact frame of the hand that holds it).
  3. On Hand_IK.L / R: sliders  grab_kettlebell, grab_mace, grab_bar_over, grab_bar_under, grab_kb_swing  (0 to 1) and a Copy Transforms per grip
     whose influence is the slider.
  4. Re-run build_finger_controls.py so the same slider also closes the hand to the measured grip.

A hand frame: local Y points along the fingers and local +Z is the palm side. The handle or shaft runs along the hand's X.
"""
import bpy, math
from mathutils import Vector, Matrix

rig = bpy.data.objects["Rig"]; arm = rig.data
KB_HEAD, MACE_HEAD = Vector((0.0, -0.40, 0.0)), Vector((0.65, -0.10, 0.0))     # rest positions of the prop bones (on the floor)
BAR_HEAD = Vector((0.0, -0.17, 0.0))                                           # the pull-up frame stands 17 cm in front of the origin
KB_R, MACE_R, BAR_R, FINGER_R, THUMB_R = 0.0175, 0.0165, 0.016, 0.0095, 0.012
BAR_Z = 2.30
kb_mesh = bpy.data.objects["Kettlebell"]
KB_GRIP_Z = max(v.co.z for v in kb_mesh.data.vertices) - KB_R                  # centre line of the handle's top bar
SLIDERS = ("fist", "index", "middle", "ring", "pinky", "thumb", "thumb_oppose", "grab_kettlebell", "grab_mace", "grab_bar_over", "grab_bar_under", "grab_kb_swing")

if rig.animation_data:
    for fc in list(rig.animation_data.drivers):
        if "Grab_" in fc.data_path: rig.animation_data.drivers.remove(fc)

def evalpose(): return rig.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones
def setprops(side, **kw):
    c = rig.pose.bones[f"Hand_IK.{side}"]
    for k in SLIDERS:
        if k in c.keys(): c[k] = kw.get(k, 0.0)
    rig.update_tag(); bpy.context.view_layer.update()

bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')
for pb in rig.pose.bones:
    for c in list(pb.constraints):
        if c.name.startswith("Grab_"): pb.constraints.remove(c)

# ---------------------------------------------------------------- 1. measure the grip, in the hand's own coordinates
# Hand-local positions of the finger joints at every fist value (the hand is not moved, so reach does not matter)
side = "L"                                      # the right hand is the mirror image and measures identically
fingers = ("Index", "Middle", "Ring", "Pinky")
pos = {}
for k in range(21):
    f = k / 20; setprops(side, fist=f); P = evalpose(); inv = P[f"Hand.{side}"].matrix.inverted()
    pos[f] = [inv @ P[f"{fg}{n}.{side}"].head for fg in fingers for n in (2, 3)] + [inv @ P[f"{fg}3.{side}"].tail for fg in fingers]
setprops(side)

def rms(points, yc, zc, target):
    # distance from the handle axis (the line through (0, yc, zc) along local X) to every point, against the target
    return math.sqrt(sum((math.hypot(p.y - yc, p.z - zc) - target) ** 2 for p in points) / len(points))

def best_grip(radius):
    target = radius + FINGER_R; best = None
    for f, pts in pos.items():
        for yi in range(0, 81):
            for zi in range(0, 61):
                yc, zc = 0.04 + yi * 0.001, 0.0 + zi * 0.001
                e = rms(pts, yc, zc, target)
                if best is None or e < best[0]: best = (e, f, yc, zc)
    return best

kb_fit, mace_fit = best_grip(KB_R), best_grip(MACE_R)
for label, (e, f, yc, zc) in (("kettlebell handle", kb_fit), ("mace shaft", mace_fit)):
    print(f"grip on the {label}: fist {f:.2f}, handle centre at hand-local (0, {yc:.3f}, {zc:.3f}); finger joints {1000 * e:.1f} mm (rms) from ideal")
PALM = (0.0, (kb_fit[2] + mace_fit[2]) / 2, (kb_fit[3] + mace_fit[3]) / 2)       # one shared handle position keeps both grips consistent
print(f"shared handle position in the hand: (0, {PALM[1]:.3f}, {PALM[2]:.3f})")

# the bar: the handle position in the hand is the shared one (kept fixed so the kettlebell and mace grips do not move); only the closure is fitted
def best_fist(radius):
    target = radius + FINGER_R
    return min(((rms(pts, PALM[1], PALM[2], target), f) for f, pts in pos.items()))
bar_e, bar_f = best_fist(BAR_R)
bar_fit = (bar_e, bar_f, PALM[1], PALM[2])
print(f"grip on the pull-up bar (shared handle position): fist {bar_f:.2f}; finger joints {1000 * bar_e:.1f} mm (rms) from ideal")

# thumb: choose its own curl and its opposition so its tip joints sit one thumb-radius outside the handle, on the far side
def thumb_pts(own, opp, fist):
    setprops(side, fist=fist, thumb=own, thumb_oppose=opp); P = evalpose(); inv = P[f"Hand.{side}"].matrix.inverted()
    return [inv @ P[f"Thumb{n}.{side}"].tail for n in (2, 3)]
thumb_best = {}
for label, radius, fit in (("kettlebell", KB_R, kb_fit), ("mace", MACE_R, mace_fit), ("pull-up bar", BAR_R, bar_fit)):
    best = None
    for oi in range(0, 11):
        for ti in range(-10, 1):
            pts = thumb_pts(ti / 10, oi / 10, fit[1])
            e = rms(pts, PALM[1], PALM[2], radius + THUMB_R)
            if best is None or e < best[0]: best = (e, ti / 10, oi / 10)
    thumb_best[label] = best
    print(f"thumb on the {label}: own curl {best[1]:+.1f} (total {max(0, min(1, fit[1] + best[1])):.2f}), opposition {best[2]:.1f}; {1000 * best[0]:.1f} mm (rms) from ideal")
setprops(side)

# ---------------------------------------------------------------- 2. bones
Y_FWD, Z_DN = Vector((0, -1, 0)), Vector((0, 0, -1))
GRIPS = {   # bone: (prop, handle centre in prop space, fingers direction, palm direction, handle axis)
    "KB_Grip.L":   ("Kettlebell", Vector(( 0.045, 0, KB_GRIP_Z)), Y_FWD, Z_DN, Vector((1, 0, 0))),
    "KB_Grip.R":   ("Kettlebell", Vector((-0.045, 0, KB_GRIP_Z)), Y_FWD, Z_DN, Vector((1, 0, 0))),
    "Mace_Grip.L": ("Mace", Vector((0, 0, 0.20)), Y_FWD, Vector((-1, 0, 0)), Vector((0, 0, 1))),
    "Mace_Grip.R": ("Mace", Vector((0, 0, 0.34)), Y_FWD, Vector(( 1, 0, 0)), Vector((0, 0, 1))),
    # the pull-up bar: fingers point UP. Overhand: the palm faces away (-Y), thumbs toward each other. Underhand: the palm faces
    # the body (+Y), thumbs pointing outward. The two differ by a 180 degree twist of the hand about its own length.
    "BarOver_Grip.L":  ("PullupBar", Vector(( 0.28, 0, BAR_Z)), Vector((0, 0, 1)), Vector((0, -1, 0)), Vector((1, 0, 0))),
    "BarOver_Grip.R":  ("PullupBar", Vector((-0.28, 0, BAR_Z)), Vector((0, 0, 1)), Vector((0, -1, 0)), Vector((1, 0, 0))),
    "BarUnder_Grip.L": ("PullupBar", Vector(( 0.20, 0, BAR_Z)), Vector((0, 0, 1)), Vector((0,  1, 0)), Vector((1, 0, 0))),
    "BarUnder_Grip.R": ("PullupBar", Vector((-0.20, 0, BAR_Z)), Vector((0, 0, 1)), Vector((0,  1, 0)), Vector((1, 0, 0))),
    # the kettlebell SWING grip (Step 16): arms hanging, so the fingers point DOWN and the palms face the body (+Y), the way a deadlift
    # is held. The handle bar runs along X as before.
    "KBSwing_Grip.L": ("Kettlebell", Vector(( 0.045, 0, KB_GRIP_Z)), Vector((0, 0, -1)), Vector((0, 1, 0)), Vector((1, 0, 0))),
    "KBSwing_Grip.R": ("Kettlebell", Vector((-0.045, 0, KB_GRIP_Z)), Vector((0, 0, -1)), Vector((0, 1, 0)), Vector((1, 0, 0))),
}
PROP_BONES = {"Kettlebell": KB_HEAD, "Mace": MACE_HEAD, "PullupBar": BAR_HEAD}
NEW = list(PROP_BONES) + list(GRIPS)
for pb in rig.pose.bones:
    if pb.name in NEW: pb.location = (0, 0, 0)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones
for n in NEW:
    if n in eb: eb.remove(eb[n])
for n, head in PROP_BONES.items():
    b = eb.new(n); b.head = head; b.tail = head + Vector((0, 0, 0.10)); b.parent = eb["Root"]; b.use_deform = False
for n, (prop, c, y, z, axis) in GRIPS.items():
    wrist = PROP_BONES[prop] + c - PALM[1] * y - PALM[2] * z                   # c = wrist + yc * y + zc * z
    b = eb.new(n); b.head = wrist; b.tail = wrist + y * 0.10; b.align_roll(z)  # bone Y = fingers, bone Z = palm side
    b.parent = eb[prop]; b.use_connect = False; b.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')

for name in ("Controls", "Grips"):
    if name not in arm.collections_all: arm.collections.new(name)
for n in NEW: arm.bones[n].use_deform = False
for n in PROP_BONES: arm.collections_all["Controls"].assign(arm.bones[n])
for n in GRIPS: arm.collections_all["Grips"].assign(arm.bones[n])
arm.collections_all["Grips"].is_visible = False
box = bpy.data.objects.get("CS_Box")
if box:
    for n, scale in (("Kettlebell", (0.24, 0.24, 0.02)), ("Mace", (0.14, 0.14, 0.02)), ("PullupBar", (0.30, 0.30, 0.02))):
        pb = rig.pose.bones[n]; pb.custom_shape = box; pb.use_custom_shape_bone_size = False; pb.custom_shape_scale_xyz = scale

# parent the meshes to their bones, keeping them where they stand
bpy.context.view_layer.update()
for prop, head in PROP_BONES.items():
    ob = bpy.data.objects[prop]; ob.parent = None
    ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = prop
    P = rig.matrix_world @ rig.pose.bones[prop].matrix @ Matrix.Translation((0, arm.bones[prop].length, 0))     # Blender parents to a bone's TAIL
    ob.matrix_basis = Matrix.Identity(4)
    ob.matrix_parent_inverse = P.inverted() @ Matrix.Translation(head)

# ---------------------------------------------------------------- 3. grab sliders and constraints
# The constraints form a STACK: each Copy Transforms blends the result of the one before it. So two partial grabs do not average (at 0.5
# and 0.5 the ORIGINAL hand position would keep a quarter of the weight, and the arm swings off to the side: found in Step 15). To get
# the blend we want, the slider values are first turned into weights  w_k = s_k * min(1, S) / S  (S = the sum of the sliders; what is
# left over, 1 - min(1, S), stays with the animated hand), and constraint k then gets  w_k / (1 - the weights of the later constraints).
GRAB_ORDER = (("grab_kettlebell", "KB_Grip", "Grab_Kettlebell"), ("grab_mace", "Mace_Grip", "Grab_Mace"),
              ("grab_bar_over", "BarOver_Grip", "Grab_BarOver"), ("grab_bar_under", "BarUnder_Grip", "Grab_BarUnder"),
              ("grab_kb_swing", "KBSwing_Grip", "Grab_KBSwing"))
bpy.ops.object.mode_set(mode='POSE')
for s in "LR":
    hc = rig.pose.bones[f"Hand_IK.{s}"]
    for k, (slider, grip_prefix, cname) in enumerate(GRAB_ORDER):
        hc[slider] = 0.0
        hc.id_properties_ui(slider).update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, description=f"Snap this hand to the {cname[5:]} grip and close it around it")
        con = hc.constraints.new('COPY_TRANSFORMS'); con.name = cname
        con.target = rig; con.subtarget = f"{grip_prefix}.{s}"; con.target_space = 'WORLD'; con.owner_space = 'WORLD'
        S = "(" + "+".join(f"s{j}" for j in range(len(GRAB_ORDER))) + ")"
        later = "+".join(f"s{j}" for j in range(k + 1, len(GRAB_ORDER))) or "0"
        share = lambda terms: f"(({terms})*min(1,{S})/max({S},0.000001))"
        d = con.driver_add("influence").driver; d.type = 'SCRIPTED'
        d.expression = f"{share(f's{k}')} / max(0.000001, 1 - {share(later)})"
        for j, (sl, _, _) in enumerate(GRAB_ORDER):
            v = d.variables.new(); v.name = f"s{j}"; v.type = 'SINGLE_PROP'; v.targets[0].id = rig
            v.targets[0].data_path = f'pose.bones["Hand_IK.{s}"]["{sl}"]'
bpy.ops.object.mode_set(mode='OBJECT')

# ---------------------------------------------------------------- 4. let the same slider close the hand
GRABS = {"grab_kettlebell": {"fist": kb_fit[1], "thumb": thumb_best["kettlebell"][1], "oppose": thumb_best["kettlebell"][2]},
         "grab_mace":       {"fist": mace_fit[1], "thumb": thumb_best["mace"][1], "oppose": thumb_best["mace"][2]},
         "grab_bar_over":   {"fist": bar_fit[1], "thumb": thumb_best["pull-up bar"][1], "oppose": thumb_best["pull-up bar"][2]},
         "grab_bar_under":  {"fist": bar_fit[1], "thumb": thumb_best["pull-up bar"][1], "oppose": thumb_best["pull-up bar"][2]},
         "grab_kb_swing":   {"fist": kb_fit[1], "thumb": thumb_best["kettlebell"][1], "oppose": thumb_best["kettlebell"][2]}}
exec(open("/Users/chris/blender_tutorial/human_tutorial/tools/build_finger_controls.py").read(), {"GRABS": GRABS})
print("grab sliders drive the fingers:", {k: {a: round(b, 2) for a, b in v.items()} for k, v in GRABS.items()})

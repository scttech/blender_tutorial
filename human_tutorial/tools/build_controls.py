"""build_controls.py - Step 10: IK controls for the arms and legs.

Run inside Blender after build_armature.py (HANDS=True) and bind_and_weight.py:   exec(open(".../build_controls.py").read(), {})
Safe to re-run: it removes the old controls and constraints first.

Adds 8 NON-deforming control bones
    Foot_IK.L/R   Hand_IK.L/R     the targets the feet and hands are pinned to (same orientation as the bone they drive)
    Knee_Pole.L/R Elbow_Pole.L/R  point the knee forward and the elbow back
and these constraints
    Shin.*     IK, chain of 2 (Shin + Thigh), pole target, hinge-only (X only, 0 to 155 deg)
    ForeArm.*  IK, chain of 2 (ForeArm + UpperArm), pole target, hinge-only (X only, -150 to 0 deg)
Needs the elbows pre-bent in the rest pose (rig_landmarks.py): with a perfectly straight arm the IK solver has no bend direction.
    Foot.*, Hand.*   Copy Rotation from their IK control
then SCANS the pole angle, because it depends on the bone roll set in Steps 6 and 7.
Controls live in a "Controls" bone collection (the deforming bones are in "Deform") and are drawn with custom shapes: a box for
the foot and hand targets, a diamond for the poles. The shapes are stored in a hidden "Widgets" collection.
Note: IK is solved in Blender only. Before exporting for the web, bake the animation onto the deform bones (Step 21).
"""
import bpy, math
from mathutils import Vector

rig = bpy.data.objects["Rig"]; arm = rig.data
SIDES = ("L", "R")
CONTROLS = [f"{n}.{s}" for n in ("Foot_IK", "Hand_IK", "Knee_Pole", "Elbow_Pole") for s in SIDES]

bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')
for pb in rig.pose.bones:                                   # start from the rest pose and remove old IK
    for c in list(pb.constraints): pb.constraints.remove(c)
    pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0)
    pb.lock_ik_x = pb.lock_ik_y = pb.lock_ik_z = False
    pb.use_ik_limit_x = pb.use_ik_limit_y = pb.use_ik_limit_z = False
bpy.ops.object.mode_set(mode='EDIT')
for n in CONTROLS:
    if n in arm.edit_bones: arm.edit_bones.remove(arm.edit_bones[n])

# ---------------------------------------------------------------- 1. control bones
eb = arm.edit_bones
def copy_of(src_name, new_name, length):
    """a control bone that starts where `src` starts and points the same way (same roll), so rest orientations match"""
    src = eb[src_name]; b = eb.new(new_name)
    d = (src.tail - src.head).normalized()
    b.head = src.head.copy(); b.tail = src.head + d * length; b.roll = src.roll
    b.parent = eb["Root"]; b.use_connect = False; b.use_deform = False
    return b
def pole(new_name, pos):
    b = eb.new(new_name); b.head = Vector(pos); b.tail = Vector(pos) + Vector((0, 0, 0.06))
    b.parent = eb["Root"]; b.use_deform = False

for s in SIDES:
    copy_of(f"Foot.{s}", f"Foot_IK.{s}", 0.18)
    copy_of(f"Hand.{s}", f"Hand_IK.{s}", 0.14)
    sx = 1 if s == "L" else -1
    pole(f"Knee_Pole.{s}",  (sx * 0.134, -0.55, 0.55))          # in front of the knees
    pole(f"Elbow_Pole.{s}", (sx * 0.49,   0.55, 1.45))          # behind the elbows
bpy.ops.object.mode_set(mode='POSE')

# ---------------------------------------------------------------- 2. constraints
def add_ik(bone, target, polename, lim_min, lim_max):
    pb = rig.pose.bones[bone]
    c = pb.constraints.new('IK'); c.target = rig; c.subtarget = target
    c.pole_target = rig; c.pole_subtarget = polename; c.pole_angle = 0.0
    c.chain_count = 2; c.use_stretch = False
    pb.lock_ik_y = pb.lock_ik_z = True                          # hinge joint: bend about X only (needs the rest-pose pre-bend, see rig_landmarks.py)
    pb.use_ik_limit_x = True; pb.ik_min_x = math.radians(lim_min); pb.ik_max_x = math.radians(lim_max)
    return c
def add_copy_rot(bone, target):
    c = rig.pose.bones[bone].constraints.new('COPY_ROTATION'); c.target = rig; c.subtarget = target
    c.target_space = 'WORLD'; c.owner_space = 'WORLD'

iks = {}
for s in SIDES:
    iks[f"Shin.{s}"]    = add_ik(f"Shin.{s}",    f"Foot_IK.{s}", f"Knee_Pole.{s}",   0, 155)      # knee flexion is +X
    iks[f"ForeArm.{s}"] = add_ik(f"ForeArm.{s}", f"Hand_IK.{s}", f"Elbow_Pole.{s}", -150, 0)      # elbow flexion is -X
    add_copy_rot(f"Foot.{s}", f"Foot_IK.{s}"); add_copy_rot(f"Hand.{s}", f"Hand_IK.{s}")

# ---------------------------------------------------------------- 3. pole angle scan
def evalpose():
    return rig.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones

def off_hinge(bone):
    """degrees of the solved rotation that are NOT about the bone's X hinge (read back from the solved pose matrices)"""
    P = evalpose(); b = rig.pose.bones[bone].bone; par = b.parent
    rest_rel = par.matrix_local.inverted() @ b.matrix_local
    e = (rest_rel.inverted() @ (P[par.name].matrix.inverted() @ P[bone].matrix)).to_euler()
    return max(abs(math.degrees(e[1])), abs(math.degrees(e[2])))

def joint_error(bone_with_ik, upper, lower, pole_bone):
    """how far the bent joint is from pointing at its pole target (0 = perfect), in degrees"""
    pb = evalpose()
    hip, joint, end = pb[upper].head.copy(), pb[lower].head.copy(), pb[lower].tail.copy()
    axis = (end - hip).normalized(); mid = hip + axis * (joint - hip).dot(axis)
    a = joint - mid; p = pb[pole_bone].head - mid; p = p - axis * p.dot(axis)
    if a.length < 1e-4 or p.length < 1e-4: return 180.0
    return math.degrees(a.angle(p))

def calibrate(bone, upper, lower, pole_bone, bend):
    """bend the chain by moving the target, then pick the pole angle where the joint points at the pole AND stays a pure hinge.
    (Pointing at the pole alone is not enough: an arm can reach the pole by twisting the shoulder 90 degrees and bending about
    the wrong axis, which gives the same hand position and ruins the skin.)"""
    best = (1e9, 0, 0, 0)
    for deg in range(-180, 180, 5):
        iks[bone].pole_angle = math.radians(deg); bpy.context.view_layer.update()
        e, h = joint_error(bone, upper, lower, pole_bone), off_hinge(lower)
        if e + h < best[0]: best = (e + h, deg, e, h)
    iks[bone].pole_angle = math.radians(best[1]); bpy.context.view_layer.update()
    return best[2], best[1], best[3]

report = {}
for s in SIDES:
    # legs: drop the hips 0.3 m with the feet pinned, so the knees must bend
    rig.pose.bones["Hips"].location = rig.pose.bones["Hips"].bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, -0.30))
    bpy.context.view_layer.update()
    report[f"Shin.{s}"] = calibrate(f"Shin.{s}", f"Thigh.{s}", f"Shin.{s}", f"Knee_Pole.{s}", 0.3)
    rig.pose.bones["Hips"].location = (0, 0, 0)
    # arms: pull the hand targets 0.35 m forward of the shoulders, so the elbows must bend
    for s2 in (s,):
        pbh = rig.pose.bones[f"Hand_IK.{s2}"]; pbh.location = pbh.bone.matrix_local.to_3x3().inverted() @ Vector((-(1 if s == "L" else -1) * 0.25, -0.30, 0))
        bpy.context.view_layer.update()
        report[f"ForeArm.{s}"] = calibrate(f"ForeArm.{s}", f"UpperArm.{s}", f"ForeArm.{s}", f"Elbow_Pole.{s}", 0.3)
        pbh.location = (0, 0, 0)
    bpy.context.view_layer.update()
for k, (err, deg, hinge) in report.items(): print(f"pole angle {k}: {deg:+d} deg (joint points {err:.1f} deg off the pole, {hinge:.1f} deg off the X hinge)")

# ---------------------------------------------------------------- 4. collections and colours
for name in ("Deform", "Controls"):
    if name in arm.collections_all: arm.collections.remove(arm.collections_all[name])
deform, ctrl = arm.collections.new("Deform"), arm.collections.new("Controls")
for b in arm.bones:
    (ctrl if b.name in CONTROLS else deform).assign(b)
for n in CONTROLS:
    pb = rig.pose.bones[n]; pb.color.palette = 'THEME04' if n.endswith(".L") else 'THEME01'      # left blue, right red

# ---------------------------------------------------------------- 5. custom shapes, so the controls are easy to see and grab
WIDGETS = "Widgets"
coll = bpy.data.collections.get(WIDGETS) or bpy.data.collections.new(WIDGETS)
if WIDGETS not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(coll)
def widget(name, verts, edges):
    old = bpy.data.objects.get(name)
    if old: m = old.data; bpy.data.objects.remove(old, do_unlink=True); bpy.data.meshes.remove(m)
    me = bpy.data.meshes.new(name); me.from_pydata(verts, edges, []); ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
    return ob
cube_v = [(x, y, z) for x in (-.5, .5) for y in (-.5, .5) for z in (-.5, .5)]
cube_e = [(i, j) for i in range(8) for j in range(i + 1, 8) if sum(a != b for a, b in zip(cube_v[i], cube_v[j])) == 1]
dia_v = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
dia_e = [(i, j) for i in range(6) for j in range(i + 1, 6) if i // 2 != j // 2]
box, diamond = widget("CS_Box", cube_v, cube_e), widget("CS_Diamond", dia_v, dia_e)
bpy.context.view_layer.layer_collection.children[WIDGETS].exclude = True          # hidden: only used as bone shapes
SHAPES = {"Foot_IK": (box, (0.10, 0.22, 0.04), (0, 0.11, 0)), "Hand_IK": (box, (0.09, 0.11, 0.03), (0, 0.055, 0)),
          "Knee_Pole": (diamond, (0.04, 0.04, 0.04), (0, 0, 0)), "Elbow_Pole": (diamond, (0.04, 0.04, 0.04), (0, 0, 0))}
for n in CONTROLS:
    shape, scale, shift = SHAPES[n[:-2]]; pb = rig.pose.bones[n]
    pb.custom_shape = shape; pb.use_custom_shape_bone_size = False
    pb.custom_shape_scale_xyz = scale; pb.custom_shape_translation = shift

bpy.ops.object.mode_set(mode='OBJECT')
print("controls:", CONTROLS)
print("bones:", len(arm.bones), "| deform:", sum(b.use_deform for b in arm.bones), "| control (non-deform, not Root):",
      sum(1 for b in arm.bones if b.name in CONTROLS))

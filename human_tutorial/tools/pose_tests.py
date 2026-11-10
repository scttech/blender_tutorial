"""pose_tests.py - Step 9: pose the rig like the exercises will, and measure what the skin does.

Run inside Blender with the Step 8 scene (Body bound to Rig):

    G = {"POSE": "squat", "ACTION": "measure"}        # ACTION: "measure" (pose + report), "pose" (just pose), "clear"
    exec(open(".../pose_tests.py").read(), G)

Conventions (from Steps 6 and 7; angles in degrees, Euler XYZ on the bone's own axes)
  * rotating about local X bends the joint, and the same X value moves LEFT and RIGHT bones as mirror images
  * for rotation about local Y or Z the right side needs the opposite sign, so a left-side pose is mirrored with
    (x, -y, -z)
  * elbow: flexion is -X. knee: flexion is +X. hip: flexion (leg forward) is -X. spine/neck: flexion (lean forward) is +X
    wrist/fingers: flexion is +X. arm forward = -X.  arm up (overhead) = -Z on the left, +Z on the right (80 deg from the T-pose, not 150)
IK (Step 10) is muted while posing, because FK poses and IK fight; "pose" leaves it muted so you can look, any other action turns it back on.
Reports: whole-mesh volume change, and the skin edges that stretch past 1.5x or shrink below 0.6x, with where they are.
"""
import bpy, bmesh, math
from mathutils import Euler, Vector

rig, body = bpy.data.objects["Rig"], bpy.data.objects["Body"]

# bone -> (x, y, z) degrees for the LEFT side and the centre line. mirror=True copies the left pose to the right.
POSES = {
    "squat": dict(mirror=True, feet_floor=("L", "R"), bones={
        "Thigh.L": (-85, 0, 0), "Shin.L": (105, 0, 0), "Foot.L": (-20, 0, 0),
        "Spine": (15, 0, 0), "Spine1": (10, 0, 0), "Spine2": (5, 0, 0), "Neck": (-10, 0, 0), "Head": (-10, 0, 0),
        "UpperArm.L": (-90, 0, 0)}),
    "lunge": dict(mirror=False, feet_floor=("L",), bones={
        "Thigh.L": (-80, 0, 0), "Shin.L": (85, 0, 0), "Foot.L": (-5, 0, 0),
        "Thigh.R": (35, 0, 0), "Shin.R": (80, 0, 0), "Foot.R": (-45, 0, 0), "Toes.R": (45, 0, 0)}),
    "overhead": dict(mirror=True, bones={"UpperArm.L": (0, 0, -80), "Clavicle.L": (0, 0, -15)}),   # the T-pose is already 90 deg out, so overhead is about 80 more
    "elbows": dict(mirror=True, bones={"UpperArm.L": (-90, 0, 0), "ForeArm.L": (-100, 0, 0)}),
    "curl": dict(mirror=True, bones={"UpperArm.L": (0, 0, 85), "ForeArm.L": (-115, 0, 0)}),   # arm down at the side, biceps curl (the kettlebell rack)
    "twist_hand": dict(mirror=True, bones={"UpperArm.L": (-90, 0, 0), "Hand.L": (0, 90, 0)}),       # turn the palm 90 deg from the WRIST only
    "twist_fore": dict(mirror=True, bones={"UpperArm.L": (-90, 0, 0), "ForeArm.L": (0, 90, 0)}),     # turn the palm 90 deg from the ELBOW
    "wrists": dict(mirror=True, bones={"UpperArm.L": (-90, 0, 0), "Hand.L": (-70, 0, 0)}),
    "situp": dict(mirror=True, bones={"Spine": (25, 0, 0), "Spine1": (30, 0, 0), "Spine2": (25, 0, 0),
                                      "Neck": (20, 0, 0), "Head": (10, 0, 0)}),
    "seated": dict(mirror=True, bones={"Thigh.L": (-90, 0, 0), "Shin.L": (90, 0, 0)}),
}

def set_ik(enabled):
    """the FK test poses below would fight the IK constraints from Step 10, so mute them while posing"""
    for pb in rig.pose.bones:
        for c in pb.constraints:
            if c.type in ('IK', 'COPY_ROTATION'): c.mute = not enabled

def clear():
    bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')
    for pb in rig.pose.bones:
        pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0)
    bpy.ops.object.mode_set(mode='OBJECT'); bpy.context.view_layer.update()

def mirror_name(n): return n[:-2] + ".R" if n.endswith(".L") else n

def ankle(side):
    return rig.matrix_world @ rig.pose.bones[f"Shin.{side}"].tail

def apply(name):
    spec = POSES[name]; clear()
    rest_ankle = {s: ankle(s).copy() for s in "LR"}
    bpy.ops.object.mode_set(mode='POSE')
    for bone, (x, y, z) in spec["bones"].items():
        rig.pose.bones[bone].rotation_euler = Euler([math.radians(a) for a in (x, y, z)])
        if spec["mirror"] and bone.endswith(".L"):
            rig.pose.bones[mirror_name(bone)].rotation_euler = Euler([math.radians(a) for a in (x, -y, -z)])
    bpy.context.view_layer.update()
    if "feet_floor" in spec:                      # drop and shift the hips so the planted ankles stay where they were
        side = spec["feet_floor"][0]
        delta = rest_ankle[side] - ankle(side)
        hips = rig.pose.bones["Hips"]
        hips.location = hips.bone.matrix_local.to_3x3().inverted() @ delta
        bpy.context.view_layer.update()
    bpy.ops.object.mode_set(mode='OBJECT'); bpy.context.view_layer.update()

def deformed():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    pts = [v.co.copy() for v in me.vertices]
    bm = bmesh.new(); bm.from_mesh(me); vol = bm.calc_volume(signed=True); bm.free(); ev.to_mesh_clear()
    return pts, vol

def nearest_bone(p):
    best, name = 1e9, ""
    for b in rig.data.bones:
        h, t = b.head_local, b.tail_local; d = t - h; L = d.length
        if L < 1e-6: continue
        s = max(0.0, min(L, (p - h).dot(d / L))); dist = (p - (h + d / L * s)).length
        if dist < best: best, name = dist, b.name
    return name

def measure(name):
    clear(); rest_pts, rest_vol = deformed()
    apply(name); pts, vol = deformed()
    stretched, squashed = [], []
    for e in body.data.edges:
        a, b = e.vertices; r0 = (rest_pts[a] - rest_pts[b]).length
        if r0 < 0.004: continue
        ratio = (pts[a] - pts[b]).length / r0
        mid = (rest_pts[a] + rest_pts[b]) / 2
        if ratio > 1.5: stretched.append((ratio, mid))
        elif ratio < 0.6: squashed.append((ratio, mid))
    def where(lst):
        from collections import Counter
        c = Counter(nearest_bone(m) for _, m in lst); return c.most_common(3)
    print(f"[{name}] volume {100 * (vol / rest_vol - 1):+.1f}% | edges >1.5x: {len(stretched)}"
          f"{' worst x%.1f' % max(r for r, _ in stretched) if stretched else ''} {where(stretched) if stretched else ''}"
          f" | edges <0.6x: {len(squashed)} {where(squashed) if squashed else ''}")

ACTION, POSE = globals().get("ACTION", "measure"), globals().get("POSE", "squat")
set_ik(False)
if ACTION == "clear": clear()
elif ACTION == "pose": apply(POSE)
elif ACTION == "measure": measure(POSE)
elif ACTION == "all":
    for n in POSES: measure(n)
    clear()
if ACTION != "pose": set_ik(True)          # leave the posed (FK) result visible for "pose"; every other action restores the IK

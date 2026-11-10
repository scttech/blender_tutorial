"""anim_core.py - Step 13: build looping actions from keyframe TABLES, and measure them.

    G = {}; exec(open(".../anim_core.py").read(), G)          # then use G["build_action"], G["measure"], ...

A motion is a list of keys. Each key is (frame, pose); a pose says what CHANGES at that frame, and anything it does not mention
keeps its previous value (rest at the first key). Pose entries, per bone:
    "move": (dx, dy, dz)    world-space offset from the rest position, metres        (bones whose parent is not posed: Hips, controls)
    "at":   (x, y, z)       absolute world position of a control's head, metres      (Hand_IK, Foot_IK, props)
    "rot":  (rx, ry, rz)    degrees on the bone's own axes. The conventions of Steps 6-7 apply: elbow flexion -X, knee flexion +X,
                            spine/neck flexion +X, wrist/finger flexion +X.
    "props": {name: value}  custom properties (the finger and grab sliders on the Hand_IK bones)
Write the LEFT bone (".L") and the table is mirrored to the right when mirror=True: positions flip x, "rot" becomes (x, -y, -z),
slider values are copied.

build_action() makes one keyframe per channel at every key (so every curve shares the same keys), eases between them (Bezier,
auto-clamped), and for a loop adds a Cycles modifier and marks the action cyclic. The LAST key should equal the FIRST for a loop.
measure() plays an action and records what matters: where the ankles are (no sliding), joint angles, the centre of mass against the
feet (balance), reach errors, and the loop seam.
Blender 5: actions hold their curves in layers > strips > channelbags; there is no action.fcurves.
"""
import bpy, math, json
import numpy as np
from mathutils import Vector, Euler

rig, body, scene = bpy.data.objects["Rig"], bpy.data.objects["Body"], bpy.context.scene
FPS = 30
SLIDERS = ("fist", "index", "middle", "ring", "pinky", "thumb", "thumb_oppose", "grab_kettlebell", "grab_mace")

def mirror_name(n): return n[:-2] + ".R" if n.endswith(".L") else n
def rest_head(bone): return rig.data.bones[bone].head_local.copy()
def to_local(bone, world_delta):
    """a world-space offset, expressed in the bone's own axes (valid when the bone's parent has no pose: Hips and the controls)"""
    return rig.data.bones[bone].matrix_local.to_3x3().inverted() @ world_delta

# ------------------------------------------------------------------ channels
def fcurves_of(action):
    """all F-curves of an action (Blender 5 stores them in layers > strips > channelbags)"""
    out = []
    for layer in action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags: out.extend(cb.fcurves)
    return out

def expand(keys, mirror):
    """-> [(frame, {(bone, kind, name): value})] with every key complete and the right side filled in"""
    chans = []
    for frame, pose in keys:
        flat = {}
        for bone, spec in pose.items():
            sides = [(bone, 1)] + ([(mirror_name(bone), -1)] if mirror and bone.endswith(".L") else [])
            for b, s in sides:
                if "move" in spec: flat[(b, "move", None)] = (spec["move"][0] * s, spec["move"][1], spec["move"][2])
                if "at" in spec:   flat[(b, "at", None)] = (spec["at"][0] * s, spec["at"][1], spec["at"][2])
                if "rot" in spec:  x, y, z = spec["rot"]; flat[(b, "rot", None)] = (x, y * s, z * s)
                for k, v in spec.get("props", {}).items(): flat[(b, "prop", k)] = v
        chans.append((frame, flat))
    return chans

def rest_value(chan):
    bone, kind, name = chan
    return {"move": (0, 0, 0), "at": (0, 0, 0), "rot": (0, 0, 0), "prop": 0.0}[kind]

def write(chan, value):
    bone, kind, name = chan; pb = rig.pose.bones[bone]
    if kind == "move": pb.location = to_local(bone, Vector(value))
    elif kind == "at": pb.location = to_local(bone, Vector(value) - rest_head(bone))
    elif kind == "rot": pb.rotation_mode = 'XYZ'; pb.rotation_euler = Euler([math.radians(a) for a in value])
    else: pb[name] = value

def insert(chan, frame):
    bone, kind, name = chan; pb = rig.pose.bones[bone]
    if kind in ("move", "at"): pb.keyframe_insert("location", frame=frame)
    elif kind == "rot": pb.keyframe_insert("rotation_euler", frame=frame)
    else: pb.keyframe_insert(f'["{name}"]', frame=frame)

def clear_pose():
    if rig.animation_data: rig.animation_data.action = None
    bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0)
        for k in SLIDERS:
            if k in pb.keys(): pb[k] = 0.0
    bpy.ops.object.mode_set(mode='OBJECT'); rig.update_tag(); bpy.context.view_layer.update()

def build_action(name, keys, mirror=True, loop=True, fps=FPS):
    clear_pose()
    for a in [a for a in bpy.data.actions if a.name == name]:
        a.user_clear(); bpy.data.actions.remove(a)
    keys = sorted(keys, key=lambda k: k[0]); table = expand(keys, mirror)
    chans = sorted({c for _, flat in table for c in flat}, key=str)
    action = bpy.data.actions.new(name); action.use_fake_user = True
    rig.animation_data_create(); rig.animation_data.action = action
    current = {c: rest_value(c) for c in chans}
    for frame, flat in table:
        current.update(flat)
        for c in chans: write(c, current[c])
        rig.update_tag(); bpy.context.view_layer.update()
        for c in chans: insert(c, frame)
    f0, f1 = keys[0][0], keys[-1][0]
    for fc in fcurves_of(action):
        for kp in fc.keyframe_points: kp.interpolation = 'BEZIER'; kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
        if loop and not any(m.type == 'CYCLES' for m in fc.modifiers): fc.modifiers.new('CYCLES')
    action.use_frame_range = True; action.frame_start, action.frame_end = f0, f1; action.use_cyclic = loop
    scene.render.fps = fps; scene.render.fps_base = 1.0; scene.frame_start, scene.frame_end = f0, f1; scene.frame_set(f0)
    return action

# ------------------------------------------------------------------ measuring
def mesh_state():
    """(vertex positions, centre of mass) of the deformed Body. The centre is the volume centroid of the closed mesh."""
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    n = len(me.vertices); v = np.empty(n * 3); me.vertices.foreach_get("co", v); v = v.reshape(n, 3)
    me.calc_loop_triangles(); t = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", t); t = t.reshape(-1, 3); ev.to_mesh_clear()
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    vol = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0
    com = (vol[:, None] * (a + b + c) / 4.0).sum(axis=0) / vol.sum()
    return v, com

def pose_bones(): return rig.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones

def measure(action_name, frames=None, extra=None):
    """play the action and record a dict of per-frame lists. extra(P, frame) may return more named values."""
    act = bpy.data.actions[action_name]; rig.animation_data_create(); rig.animation_data.action = act
    f0, f1 = int(act.frame_start), int(act.frame_end); frames = frames or list(range(f0, f1 + 1))
    D = {"frame": frames, "hips_z": [], "hips_y": [], "knee_deg": [], "thigh_deg": [], "lean_deg": [], "com_y": [], "com_x": [],
         "ankle_drift_mm": [], "reach_err_mm": [], "foot_rot_deg": []}
    scene.frame_set(frames[0]); P = pose_bones(); ankle0 = {s: P[f"Shin.{s}"].tail.copy() for s in "LR"}
    foot0 = {s: P[f"Foot.{s}"].matrix.to_quaternion() for s in "LR"}
    for f in frames:
        scene.frame_set(f); P = pose_bones(); _, com = mesh_state()
        th = (P["Thigh.L"].tail - P["Thigh.L"].head).normalized(); sh = (P["Shin.L"].tail - P["Shin.L"].head).normalized()
        D["hips_z"].append(P["Hips"].head.z); D["hips_y"].append(P["Hips"].head.y)
        D["knee_deg"].append(math.degrees(th.angle(sh)))
        D["thigh_deg"].append(math.degrees(math.asin(max(-1, min(1, -th.z)))))        # 90 = thigh vertical, 0 = horizontal
        sp = (P["Spine2"].tail - P["Spine"].head).normalized(); D["lean_deg"].append(math.degrees(sp.angle(Vector((0, 0, 1)))))
        D["com_y"].append(com[1]); D["com_x"].append(com[0])
        D["ankle_drift_mm"].append(max((P[f"Shin.{s}"].tail - ankle0[s]).length for s in "LR") * 1000)
        D["foot_rot_deg"].append(max(math.degrees(P[f"Foot.{s}"].matrix.to_quaternion().rotation_difference(foot0[s]).angle) for s in "LR"))
        D["reach_err_mm"].append(max((P[f"ForeArm.{s}"].tail - P[f"Hand_IK.{s}"].head).length for s in "LR") * 1000)
        if extra:
            for k, v in extra(P, f).items(): D.setdefault(k, []).append(v)
    return D

def loop_report(D, key="hips_z"):
    """how seamless is the loop: pose difference between the last and first frame, and the speeds on both sides of the seam"""
    v = D[key]; fps = FPS
    return {"first_last_mm": abs(v[-1] - v[0]) * 1000, "speed_at_start_mm_s": abs(v[1] - v[0]) * fps * 1000,
            "speed_at_end_mm_s": abs(v[-1] - v[-2]) * fps * 1000, "max_speed_m_s": max(abs(v[i + 1] - v[i]) for i in range(len(v) - 1)) * fps}

def save(D, path):
    json.dump(D, open(path, "w"))

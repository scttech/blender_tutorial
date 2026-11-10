"""anim_core.py - Step 13: build looping actions from keyframe TABLES, and measure them.

    G = {}; exec(open(".../anim_core.py").read(), G)          # then use G["build_action"], G["measure"], ...

A motion is a list of keys. Each key is (frame, pose); a pose says what CHANGES at that frame, and anything it does not mention
keeps its previous value (rest at the first key). Pose entries, per bone:
    "move": (dx, dy, dz)    world-space offset from the rest position, metres        (bones whose parent is not posed: Hips, controls)
    "at":   (x, y, z)       absolute world position of a control's head, metres      (Hand_IK, Foot_IK, props)
    "rot":  (rx, ry, rz)    degrees on the bone's own axes. The conventions of Steps 6-7 apply: elbow flexion -X, knee flexion +X,
                            spine/neck flexion +X, wrist/finger flexion +X.
    "wrot": (rx, ry, rz)    degrees about the WORLD axes, for a control bone whose parent is not posed (Foot_IK, Hand_IK). Use this to
                            orient a hand or foot in the world ("palm flat on the floor") without thinking in bone axes.
    "props": {name: value}  custom properties (the finger and grab sliders on the Hand_IK bones)
Write the LEFT bone (".L") and the table is mirrored to the right when mirror=True: positions flip x, "rot" becomes (x, -y, -z),
slider values are copied.

build_action() keys EVERY control (the base pose, at rest, under the first key), so an action never depends on what played before it.
It makes one keyframe per channel at every key (so every curve shares the same keys), eases between them (Bezier,
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
SLIDERS = ("fist", "index", "middle", "ring", "pinky", "thumb", "thumb_oppose", "grab_kettlebell", "grab_mace", "grab_bar_over", "grab_bar_under", "grab_kb_swing", "grab_kb_goblet")

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
        for bone, spec in sorted(pose.items(), key=lambda kv: kv[0].endswith(".R")):       # explicit right-side entries come last, so they win over the mirrored left
            sides = [(bone, 1)] + ([(mirror_name(bone), -1)] if mirror and bone.endswith(".L") else [])
            for b, s in sides:
                if "move" in spec: flat[(b, "move", None)] = (spec["move"][0] * s, spec["move"][1], spec["move"][2])
                if "at" in spec:   flat[(b, "at", None)] = (spec["at"][0] * s, spec["at"][1], spec["at"][2])
                if "rot" in spec:  x, y, z = spec["rot"]; flat[(b, "rot", None)] = (x, y * s, z * s)
                if "wrot" in spec: x, y, z = spec["wrot"]; flat[(b, "wrot", None)] = (x, y * s, z * s)
                for k, v in spec.get("props", {}).items(): flat[(b, "prop", k)] = v
        chans.append((frame, flat))
    return chans

def rest_value(chan):
    bone, kind, name = chan
    if kind == "at": return tuple(rig.data.bones[bone].head_local)          # a control at rest sits at its rest position
    return {"move": (0, 0, 0), "rot": (0, 0, 0), "wrot": (0, 0, 0), "prop": 0.0}[kind]

def base_pose():
    """EVERY control any exercise may use, at its rest value. build_action() merges this under the first key, so an action keys the
    complete set. Why: an action only controls the channels it keys, so anything it leaves out keeps whatever the PREVIOUS action
    left there (found in Step 14: a squat played after a sit-up came out wrong, up to a metre off). Write the left side; it mirrors."""
    b = rig.data.bones; at = lambda n: tuple(b[n].head_local)
    pose = {"Root": {"move": (0, 0, 0), "rot": (0, 0, 0)}, "Hips": {"move": (0, 0, 0), "rot": (0, 0, 0)}}
    for n in ("Spine", "Spine1", "Spine2", "Neck", "Head"): pose[n] = {"rot": (0, 0, 0)}
    pose["Clavicle.L"] = {"rot": (0, 0, 0)}; pose["Toes.L"] = {"rot": (0, 0, 0)}
    pose["Foot_IK.L"] = {"at": at("Foot_IK.L"), "wrot": (0, 0, 0)}
    pose["Hand_IK.L"] = {"at": at("Hand_IK.L"), "wrot": (0, 0, 0), "props": {k: 0.0 for k in SLIDERS}}
    pose["Knee_Pole.L"] = {"at": at("Knee_Pole.L")}; pose["Elbow_Pole.L"] = {"at": at("Elbow_Pole.L")}
    for n in ("Kettlebell", "Mace", "PullupBar"): pose[n] = {"at": at(n), "rot": (0, 0, 0)}
    return pose

def merge(base, pose):
    out = {k: {a: (dict(v) if isinstance(v, dict) else v) for a, v in spec.items()} for k, spec in base.items()}
    for bone, spec in pose.items():
        o = out.setdefault(bone, {})
        for k, v in spec.items():
            if k == "props": o.setdefault("props", {}).update(v)
            else: o[k] = v
    return out

def write(chan, value):
    bone, kind, name = chan; pb = rig.pose.bones[bone]
    if kind == "move": pb.location = to_local(bone, Vector(value))
    elif kind == "at": pb.location = to_local(bone, Vector(value) - rest_head(bone))
    elif kind == "rot": pb.rotation_mode = 'XYZ'; pb.rotation_euler = Euler([math.radians(a) for a in value])
    elif kind == "wrot":                              # world rotation -> the bone's own axes:  R_local = R_rest^-1 * R_world * R_rest
        R = rig.data.bones[bone].matrix_local.to_3x3(); Rw = Euler([math.radians(a) for a in value]).to_matrix()
        pb.rotation_mode = 'XYZ'; pb.rotation_euler = (R.inverted() @ Rw @ R).to_euler('XYZ')
    else: pb[name] = value

def insert(chan, frame):
    bone, kind, name = chan; pb = rig.pose.bones[bone]
    if kind in ("move", "at"): pb.keyframe_insert("location", frame=frame)
    elif kind in ("rot", "wrot"): pb.keyframe_insert("rotation_euler", frame=frame)
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

def build_action(name, keys, mirror=True, loop=True, fps=FPS, full=True):
    """full=True (the default) keys EVERY control, so the action does not depend on what played before it (see base_pose)"""
    clear_pose()
    for a in [a for a in bpy.data.actions if a.name == name]:
        a.user_clear(); bpy.data.actions.remove(a)
    keys = sorted(keys, key=lambda k: k[0])
    if full: keys[0] = (keys[0][0], merge(base_pose(), keys[0][1]))
    table = expand(keys, mirror)
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

# ------------------------------------------------------------------ rigid motion about a contact point
def rigid(pivot_rest, pivot_target, phi_deg):
    """The map a stiff body makes when it pivots about a contact point: the pivot goes from its rest position to its target, and the
    body turns phi degrees about the world X axis through it. Returns f(point) -> point. Push-up: the toes are the pivot."""
    R = Euler((math.radians(phi_deg), 0, 0)).to_matrix(); b0, bt = Vector(pivot_rest), Vector(pivot_target)
    return lambda p: bt + R @ (Vector(p) - b0)

# ------------------------------------------------------------------ measuring
_REGION = None
def regions():
    """which part of the body each vertex mostly belongs to: hands, feet or body (from its strongest vertex group)"""
    global _REGION
    if _REGION is None:
        names = {g.index: g.name for g in body.vertex_groups}; out = []
        for v in body.data.vertices:
            n = names[max(v.groups, key=lambda g: g.weight).group] if v.groups else ""
            out.append("hands" if n.startswith(("Hand.", "Index", "Middle", "Ring", "Pinky", "Thumb")) else "feet" if n.startswith(("Foot.", "Toes.")) else "body")
        _REGION = np.array(out)
    return _REGION

_MASKS = None
def torso_masks():
    """chest (spine 1-2, clavicles, neck) and head vertices, for clearance measurements in floor work"""
    global _MASKS
    if _MASKS is None:
        names = {g.index: g.name for g in body.vertex_groups}
        dom = np.array([names[max(v.groups, key=lambda g: g.weight).group] if v.groups else "" for v in body.data.vertices])
        _MASKS = (np.array([d.startswith(("Spine1", "Spine2", "Clavicle", "Neck")) for d in dom]), np.array([d.startswith("Head") for d in dom]))
    return _MASKS

def floor_report(v):
    """lowest point of each region, and how many of its vertices are within 1 cm of the floor (z = 0)"""
    reg = regions(); return {r: (float(v[reg == r, 2].min()), int((v[reg == r, 2] < 0.01).sum())) for r in ("hands", "feet", "body")}

_TRI = None
_SKIN = None
def volume(v):
    """the volume of the closed mesh with vertex positions v (uses the triangles cached by mesh_state)"""
    a, b, c = v[_TRI[:, 0]], v[_TRI[:, 1]], v[_TRI[:, 2]]
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)

def skin_baseline():
    """the T-pose: every edge's length, which edges touch a hand, and the volume. Computed once. Skin checks compare against this."""
    global _SKIN
    if _SKIN is None:
        clear_pose(); v0, _ = mesh_state(); me = body.data
        e = np.empty(len(me.edges) * 2, dtype=np.int64); me.edges.foreach_get("vertices", e); e = e.reshape(-1, 2)
        L0 = np.linalg.norm(v0[e[:, 0]] - v0[e[:, 1]], axis=1); reg = regions()
        hand = (reg[e[:, 0]] == "hands") | (reg[e[:, 1]] == "hands"); ok = L0 > 0.004
        _SKIN = (e, L0, ok & ~hand, ok & hand, volume(v0))
    return _SKIN

def mesh_state():
    """(vertex positions, centre of mass) of the deformed Body. The centre is the volume centroid of the closed mesh."""
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    n = len(me.vertices); v = np.empty(n * 3); me.vertices.foreach_get("co", v); v = v.reshape(n, 3)
    me.calc_loop_triangles(); t = np.empty(len(me.loop_triangles) * 3, dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", t); t = t.reshape(-1, 3); ev.to_mesh_clear()
    global _TRI
    if _TRI is None: _TRI = t.copy()
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    vol = np.einsum("ij,ij->i", a, np.cross(b, c)) / 6.0
    com = (vol[:, None] * (a + b + c) / 4.0).sum(axis=0) / vol.sum()
    return v, com

def pose_bones(): return rig.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones

def measure(action_name, frames=None, extra=None):
    """play the action and record a dict of per-frame lists. extra(P, frame) may return more named values."""
    skin_baseline()                                                  # (this clears the pose, so it must come before the action is assigned)
    act = bpy.data.actions[action_name]; rig.animation_data_create(); rig.animation_data.action = act
    f0, f1 = int(act.frame_start), int(act.frame_end); frames = frames or list(range(f0, f1 + 1))
    D = {"frame": frames, "hips_z": [], "hips_y": [], "knee_deg": [], "thigh_deg": [], "lean_deg": [], "com_y": [], "com_x": [],
         "ankle_drift_mm": [], "reach_err_mm": [], "foot_rot_deg": [], "elbow_deg": [], "straight_deg": [],
         "min_z_hands": [], "min_z_feet": [], "min_z_body": [], "min_z_chest": [], "min_z_head": [],
         "vol_pct": [], "stretch_body_max": [], "stretch_body_n": [], "stretch_hands_max": [], "squash_body_n": [], "contacts_hands": [], "contacts_feet": [], "contacts_body": []}
    scene.frame_set(frames[0]); P = pose_bones(); ankle0 = {s: P[f"Shin.{s}"].tail.copy() for s in "LR"}
    foot0 = {s: P[f"Foot.{s}"].matrix.to_quaternion() for s in "LR"}
    for f in frames:
        scene.frame_set(f); P = pose_bones(); verts, com = mesh_state(); fl = floor_report(verts)
        for r in ("hands", "feet", "body"): D[f"min_z_{r}"].append(fl[r][0]); D[f"contacts_{r}"].append(fl[r][1])
        e, L0, body_ok, hand_ok, V0 = skin_baseline(); R = np.linalg.norm(verts[e[:, 0]] - verts[e[:, 1]], axis=1) / np.where(L0 > 0, L0, 1)
        D["vol_pct"].append(100 * (volume(verts) / V0 - 1)); D["stretch_body_max"].append(float(R[body_ok].max())); D["stretch_body_n"].append(int((R[body_ok] > 1.5).sum()))
        D["stretch_hands_max"].append(float(R[hand_ok].max())); D["squash_body_n"].append(int((R[body_ok] < 0.6).sum()))
        chest, head = torso_masks(); D["min_z_chest"].append(float(verts[chest, 2].min())); D["min_z_head"].append(float(verts[head, 2].min()))
        ua = (P["UpperArm.L"].tail - P["UpperArm.L"].head).normalized(); fa = (P["ForeArm.L"].tail - P["ForeArm.L"].head).normalized()
        D["elbow_deg"].append(math.degrees(ua.angle(fa)))
        ank = (P["Shin.L"].tail + P["Shin.R"].tail) / 2                                  # how straight is the body from neck to ankles?
        D["straight_deg"].append(math.degrees((P["Hips"].head - P["Neck"].head).angle(ank - P["Hips"].head)))
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

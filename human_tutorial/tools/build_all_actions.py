"""build_all_actions.py - rebuild EVERY exercise action, measure each, save the measurement files, and run the order test.

    exec(open(".../build_all_actions.py").read(), {})

Run this after changing anything that all actions share (anim_core.py, the controls, the sliders, the props). To add an exercise,
write its table in tools/exercises/ and add one line to EXERCISES. For each one it prints the numbers every exercise is checked on,
then plays every action after every other and confirms each is identical to the same action played from a clean pose (an action that
leaks into the next is a bug; see Step 13).
"""
import bpy
HOME = "/Users/chris/blender_tutorial/human_tutorial"
# (action name, module in tools/exercises, table name, keys to mark on the charts, extra measurements: None or (function in that module, argument))
EXERCISES = [("Squat",  "squat",  "SQUAT",   [1, 25, 33, 61],  None),
             ("Pushup", "pushup", "PUSHUP",  [1, 31, 37, 67],  None),
             ("Situp",  "situp",  "SITUP",   [1, 34, 40, 79],  None),
             ("Pullup", "pullup", "PULLUP",  [1, 46, 52, 100], ("bar_extra", "BarOver_Grip")),
             ("Chinup", "pullup", "CHINUP",  [1, 46, 52, 100], ("bar_extra", "BarUnder_Grip")),
             ("Kbswing", "kbswing", "KBSWING", [1, 27, 53], ("bell_extra", None)),
             ("Mace10to2", "mace", "MACE_10_TO_2", [1, 16, 31], ("mace_extra", None))]
rig, scene = bpy.data.objects["Rig"], bpy.context.scene
r = lambda x, n=3: round(float(x), n)

for name, mod, table, keys, grip in EXERCISES:
    G = {"bpy": bpy}
    exec(open(f"{HOME}/tools/anim_core.py").read(), G); G["clear_pose"]()
    exec(open(f"{HOME}/tools/exercises/{mod}.py").read(), G)
    G["build_action"](name, G[table])
    D = G["measure"](name, extra=(G[grip[0]](grip[1]) if grip[1] is not None else G[grip[0]]()) if grip else None); D["keys"] = keys
    if name == "Squat":
        scene.frame_set(1); v, _ = G["mesh_state"](); sole = v[v[:, 2] < 0.02]; D["support"] = [float(sole[:, 1].min()), float(sole[:, 1].max())]
    G["save"](D, f"{HOME}/exports/{name.lower()}_measure.json")
    print(f"{name:6s} {len(D['frame']):3d} frames | reach {r(max(D['reach_err_mm']),2)} mm | knee {r(min(D['knee_deg']),1)}..{r(max(D['knee_deg']),1)} | "
          f"elbow {r(min(D['elbow_deg']),1)}..{r(max(D['elbow_deg']),1)} | lowest body {r(min(D['min_z_body']),4)} | loop seam {r(G['loop_report'](D)['first_last_mm'],2)} mm")
    rig.animation_data.action = None

# ---- the order test: every action after every other action, against the same action from a clean pose
def ev(): return rig.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones
def clean():
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0)
        for k in pb.keys():
            if k in ("fist", "index", "middle", "ring", "pinky", "thumb", "thumb_oppose") or k.startswith("grab_"): pb[k] = 0.0
    rig.update_tag(); bpy.context.view_layer.update()
def play(name, frame):
    rig.animation_data.action = bpy.data.actions[name]; scene.frame_set(frame); return {b.name: (b.head.copy(), b.tail.copy()) for b in ev()}
names = [e[0] for e in EXERCISES]; worst_all = 0.0
for B in names:
    a = bpy.data.actions[B]; frames = [int(a.frame_start), int((a.frame_start + a.frame_end) // 2), int(a.frame_end) - 5]
    fresh = {}
    for f in frames: clean(); fresh[f] = play(B, f)
    worst = 0.0
    for A in names:
        if A == B: continue
        for f in frames:
            for fa in (int(bpy.data.actions[A].frame_end) // 2, int(bpy.data.actions[A].frame_end) - 3):
                clean(); play(A, fa); after = play(B, f)
                for n, (h, t) in fresh[f].items(): worst = max(worst, (after[n][0] - h).length, (after[n][1] - t).length)
    worst_all = max(worst_all, worst)
print(f"ORDER TEST: {len(names)} actions, every one after every other: worst difference of any bone = {worst_all * 1000:.4f} mm")
print("curves per action:", {n: sum(len(cb.fcurves) for l in bpy.data.actions[n].layers for s in l.strips for cb in s.channelbags) for n in names})
clean(); scene.frame_set(1)

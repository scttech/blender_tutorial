"""build_all_actions.py - rebuild EVERY exercise action, measure each, save the measurement files, and run the order test.

    exec(open(".../build_all_actions.py").read(), {})

Run this after changing anything that all actions share (anim_core.py, the controls, the sliders, the props). To add an exercise,
write its table in tools/exercises/ (Python) or as a .toml file (see exercise_dsl.py) and add one entry to tools/exercise_registry.py. For each one it prints the numbers every exercise is checked on,
then plays every action after every other and confirms each is identical to the same action played from a clean pose (an action that
leaks into the next is a bug; see Step 13).
"""
import bpy
HOME = "/Users/chris/blender_tutorial/human_tutorial"
R = {}; exec(open(f"{HOME}/tools/exercise_registry.py").read(), R); EXERCISES = R["EXERCISES"]          # the one list of exercises
rig, scene = bpy.data.objects["Rig"], bpy.context.scene
r = lambda x, n=3: round(float(x), n)

for ex in EXERCISES:
    name, keys, grip = ex["name"], ex["keys"], ex["extra"]
    G = {"bpy": bpy}
    exec(open(f"{HOME}/tools/anim_core.py").read(), G); G["clear_pose"]()
    if ex.get("file"):                                                      # an exercise written as text (tools/exercise_dsl.py)
        D_ = {}; exec(open(f"{HOME}/tools/exercise_dsl.py").read(), D_)
        table_keys = D_["compile_file"](f"{HOME}/tools/exercises/{ex['file']}", G)
    else:
        exec(open(f"{HOME}/tools/exercises/{ex['module']}.py").read(), G); table_keys = G[ex["table"]]
    G["build_action"](name, table_keys)
    D = G["measure"](name, extra=(G[grip[0]](grip[1]) if grip[1] is not None else G[grip[0]]()) if grip else None); D["keys"] = keys
    scene.frame_set(ex.get("support_frame", 1)); v, _ = G["mesh_state"](); sole = v[v[:, 2] < 0.02]                  # the soles on the floor at the first frame = the base of support
    D["support"] = [float(sole[:, 1].min()), float(sole[:, 1].max())] if len(sole) else None     # (none for an exercise that starts off the floor)
    G["save"](D, f"{HOME}/exports/{name.lower()}_measure.json")
    print(f"{name:10s} {len(D['frame']):3d} frames | reach {r(max(D['reach_err_mm']),2)} mm | knee {r(min(D['knee_deg']),1)}..{r(max(D['knee_deg']),1)} | "
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
names = [e["name"] for e in EXERCISES]; worst_all = 0.0
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
curves = {n: sum(len(cb.fcurves) for l in bpy.data.actions[n].layers for s in l.strips for cb in s.channelbags) for n in names}
print(f"ORDER TEST: {len(names)} actions, every one after every other: worst difference of any bone = {worst_all * 1000:.4f} mm")
print("curves per action:", curves)
import json; json.dump({"worst_mm": worst_all * 1000, "actions": names, "curves": curves}, open(f"{HOME}/exports/order_test.json", "w"))   # read by check_actions.py
clean(); scene.frame_set(1)

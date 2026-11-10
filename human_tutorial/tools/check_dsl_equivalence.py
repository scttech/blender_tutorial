"""check_dsl_equivalence.py - run in Blender: for each (text file, Python table) pair, build both as actions and compare every keyframe.

    exec(open(".../check_dsl_equivalence.py").read(), {})
The Python tables are the ones we verified in Steps 13 to 16; a text file that builds the same action inherits all of those checks.
It builds throwaway actions named T_py and T_text and removes them; the real actions are not touched."""
import bpy, os
HOME = "/Users/chris/blender_tutorial/human_tutorial"; T = f"{HOME}/tools"
PAIRS = [("squat.toml", "squat.py", "SQUAT"), ("mace_10_to_2.toml", "mace.py", "MACE_10_TO_2"), ("pushup.toml", "pushup.py", "PUSHUP"), ("lunge.toml", "lunge.py", "LUNGE")]
def snapshot(G, action):
    return {(fc.data_path, fc.array_index): [(round(kp.co.x, 6), kp.co.y, kp.interpolation) for kp in fc.keyframe_points] for fc in G["fcurves_of"](action)}
for toml, py, table in PAIRS:
    G = {"bpy": bpy}; exec(open(f"{T}/anim_core.py").read(), G); G["clear_pose"]()
    exec(open(f"{T}/exercises/{py}").read(), G)
    ref = snapshot(G, G["build_action"]("T_py", G[table]))
    ex = {}; exec(open(f"{T}/exercise_dsl.py").read(), ex)
    keys = ex["compile_file"](f"{T}/exercises/{toml}", G)
    new = snapshot(G, G["build_action"]("T_text", keys))
    worst = 0.0; problems = []
    if set(ref) != set(new): problems.append(f"curves differ: {len(set(ref) ^ set(new))}")
    for c in set(ref) & set(new):
        a, b = ref[c], new[c]
        if len(a) != len(b): problems.append(f"{c}: {len(a)} vs {len(b)} keys"); continue
        for (f1, v1, i1), (f2, v2, i2) in zip(a, b):
            if f1 != f2 or i1 != i2: problems.append(f"{c}: frame/interp {f1, i1} vs {f2, i2}")
            worst = max(worst, abs(v1 - v2))
    print(f"{toml:20s} vs {py:10s}: {len(ref)} curves, {len(keys)} keys, worst value difference {worst:.2e}" + (f" | PROBLEMS {problems[:3]}" if problems else " | identical"))
    for n in ("T_py", "T_text"):
        a = bpy.data.actions.get(n)
        if a: a.user_clear(); bpy.data.actions.remove(a)
    G["clear_pose"]()
bpy.data.objects["Rig"].animation_data.action = None

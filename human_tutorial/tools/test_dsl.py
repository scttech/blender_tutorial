"""test_dsl.py - tests for exercise_dsl.py. Plain Python: python3 -I tools/test_dsl.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exercise_dsl import compile_exercise, DSLError, evaluate
import math
fails = 0
def check(label, cond):
    global fails
    print(("ok   " if cond else "FAIL ") + label); fails += 0 if cond else 1
def raises(label, fn, text):
    try: fn(); check(label + " (no error)", False)
    except DSLError as e: check(f"{label}: {e}", text in str(e))

BASE = {"name": "A", "params": {"depth": 0.5, "back": 0.1},
        "poses": {"stand": {"Hips": {"move": [0, 0, 0]}, "Hand_IK.L": {"props": {"fist": 0}}},
                  "low": {"extends": "stand", "Hips": {"move": [0, "=back", "=-depth"]}, "Hand_IK.L": {"props": {"grab_mace": 1}}}},
        "timeline": [[1, "stand"], [10, "low"], [20, "stand"]]}
k = compile_exercise(BASE)
check("three keys", [f for f, _ in k] == [1, 10, 20])
check("expression uses params", k[1][1]["Hips"]["move"] == (0, 0.1, -0.5))
check("lists become tuples", isinstance(k[0][1]["Hips"]["move"], tuple))
check("props merge slider by slider", k[1][1]["Hand_IK.L"]["props"] == {"fist": 0, "grab_mace": 1})
check("a pose leaves its parent untouched", BASE["poses"]["stand"]["Hand_IK.L"]["props"] == {"fist": 0})
# exercise-level extends: params override, poses inherited, timeline inherited
lib = {"A": BASE}
k2 = compile_exercise({"name": "B", "extends": "A", "params": {"depth": 0.3}}, lib)
check("child param overrides", k2[1][1]["Hips"]["move"][2] == -0.3 and k2[1][1]["Hips"]["move"][1] == 0.1)
k3 = compile_exercise({"name": "C", "extends": "A", "poses": {"low": {"Hips": {"move": [0, 0, -0.2]}}}}, lib)
check("child pose edits the inherited pose", k3[1][1]["Hips"]["move"] == (0, 0, -0.2) and k3[1][1]["Hand_IK.L"]["props"]["grab_mace"] == 1)
# per-key set, sampling, f
S = {"params": {"amp": 60}, "poses": {"p": {"Hips": {"rot": ["=amp*sin(radians(f))", 0, 0]}}}, "timeline": [{"frames": [0, 90, 30], "pose": "p"}, {"frame": 120, "pose": "p", "set": {"amp": 10}}]}
k4 = compile_exercise(S)
check("sampling gives frames 0,30,60,90,120", [f for f, _ in k4] == [0, 30, 60, 90, 120])
check("f in an expression", abs(k4[1][1]["Hips"]["rot"][0] - 60 * math.sin(math.radians(30))) < 1e-12)
check("per-key set", abs(k4[4][1]["Hips"]["rot"][0] - 10 * math.sin(math.radians(120))) < 1e-12)
# generator
G = {"gen": lambda gamma: {"Mace": {"at": [0, 0, gamma]}}}
k5 = compile_exercise({"poses": {"s": {"generator": "gen", "args": {"gamma": "=f*2"}, "Hips": {"move": [1, 1, 1]}}}, "timeline": [[3, "s"]]}, None, G)
check("generator pose + own entries", k5[0][1]["Mace"]["at"] == (0, 0, 6) and k5[0][1]["Hips"]["move"] == (1, 1, 1))
# layered extends and post hooks
L = {"poses": {"a": {"Hips": {"move": [0, 0, 1]}}, "b": {"Spine": {"rot": [5, 0, 0]}, "Hips": {"move": [0, 0, 2]}}, "c": {"extends": ["a", "b"], "post": [{"fn": "add", "args": {"v": "=f"}}]}}, "timeline": [[4, "c"]]}
k6 = compile_exercise(L, None, {"add": lambda pose, v: {"Head": {"rot": [v + pose["Hips"]["move"][2], 0, 0]}}})
check("layered extends: later replaces earlier", k6[0][1]["Hips"]["move"] == (0, 0, 2) and k6[0][1]["Spine"]["rot"] == (5, 0, 0))
check("post hook sees the finished pose and adds to it", k6[0][1]["Head"]["rot"] == (6, 0, 0))
# a child can swap what a pose is built from (post / extends replace the parent's wiring)
P = {"name": "P", "poses": {"arms": {"post": [{"fn": "add", "args": {"v": 1}}]}, "x": {"extends": "arms", "Hips": {"move": [0, 0, 1]}}}, "timeline": [[1, "x"]]}
C = {"name": "C", "extends": "P", "poses": {"arms": {"post": [{"fn": "add", "args": {"v": 5}}]}}}
gen_ = {"add": lambda pose, v: {"Head": {"rot": [v, 0, 0]}}}
check("child swaps the post hook of an inherited pose", compile_exercise(C, {"P": P}, gen_)[0][1]["Head"]["rot"] == (5, 0, 0) and compile_exercise(P, None, gen_)[0][1]["Head"]["rot"] == (1, 0, 0))
# errors
raises("unknown pose", lambda: compile_exercise({"poses": {}, "timeline": [[1, "x"]]}), "unknown pose 'x'")
raises("misspelt entry", lambda: compile_exercise({"poses": {"p": {"Hips": {"mvoe": [0, 0, 0]}}}, "timeline": [[1, "p"]]}), "unknown entry 'mvoe'")
raises("unknown name", lambda: compile_exercise({"poses": {"p": {"Hips": {"move": [0, 0, "=dept"]}}}, "timeline": [[1, "p"]]}), "unknown name 'dept'")
raises("frames backwards", lambda: compile_exercise({"poses": {"p": {}}, "timeline": [[5, "p"], [2, "p"]]}), "must increase")
raises("no timeline", lambda: compile_exercise({"poses": {}}), "no timeline")
raises("eval is not python", lambda: compile_exercise({"poses": {"p": {"Hips": {"move": [0, 0, "=__import__('os')"]}}}, "timeline": [[1, "p"]]}), "not allowed")
raises("pose cycle", lambda: compile_exercise({"poses": {"a": {"extends": "b"}, "b": {"extends": "a"}}, "timeline": [[1, "a"]]}), "extends itself")
raises("missing generator", lambda: compile_exercise({"poses": {"s": {"generator": "nope"}}, "timeline": [[1, "s"]]}), "not available")
raises("unknown top-level", lambda: compile_exercise({"timline": [], "timeline": [[1, "p"]], "poses": {"p": {}}}), "unknown top-level")
raises("missing parent", lambda: compile_exercise({"extends": "Z", "timeline": [[1, "p"]]}, {}), "no such exercise")
raises("timeline written after a [table]", lambda: compile_exercise({"poses": {"p": {"timeline": [[1, "p"]]}}, "timeline": [[1, "p"]]}), "belongs to that table")
print(f"\n{fails} failing")
sys.exit(1 if fails else 0)

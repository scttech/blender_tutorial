"""test_checker.py - test the CHECKER: feed check_actions.py data with known defects and confirm it catches each one. Plain Python.

    python3 -I tools/test_checker.py

The first four defects are REAL bugs from this project, replayed with the numbers they actually had. A checker that has only ever said PASS has
not shown that it can say FAIL. LIMIT: this tests the checker's THRESHOLDS against those numbers. It does not prove that the measurements made in
Blender would produce those numbers for those bugs (we saw that they did, at the time).
"""
import copy, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); HOME = os.path.dirname(HERE)
sys.path.insert(0, HERE); import check_actions as C

def real(name): return json.load(open(os.path.join(HOME, "exports", f"{name.lower()}_measure.json")))
def ex(name): return next(e for e in C.EXERCISES if e["name"] == name)
ORDER_OK = {"worst_mm": 0.0, "actions": ["a", "b"], "curves": {}}

def run(name, mutate, order=ORDER_OK):
    D = copy.deepcopy(real(name)); o = copy.deepcopy(order); mutate(D, o); res, _ = C.run_checks(ex(name), D, o); return res

CASES = [   # (what went wrong, exercise, mutation, check that must catch it, status it must give)
    ("REAL: the squat leaked into the next action after a sit-up (1,127 mm out)", "Squat", lambda D, o: o.update(worst_mm=1127.0), "order", C.FAIL),
    ("REAL: the swing's hands were 27.6 mm out of reach BETWEEN keys", "Kbswing", lambda D, o: D["reach_err_mm"].__setitem__(10, 27.56), "reach", C.FAIL),
    ("REAL: the swing's bell went 17 mm INTO the body", "Kbswing", lambda D, o: D["bell_clear_mm"].__setitem__(17, -17.0), "clearance", C.FAIL),
    ("REAL: the chin-up's reach error after the stale slider (12.3 mm)", "Chinup", lambda D, o: D["reach_err_mm"].__setitem__(5, 12.32), "reach", C.FAIL),
    ("a planted foot slides 3 mm", "Squat", lambda D, o: D["ankle_drift_mm"].__setitem__(30, 3.0), "ankles", C.FAIL),
    ("a planted contact drifts 2 mm", "Pushup", lambda D, o: D["wrist_y"].__setitem__(20, D["wrist_y"][0] + 0.002), "contacts", C.FAIL),
    ("a foot sinks 1 cm through the floor", "Squat", lambda D, o: D["min_z_feet"].__setitem__(8, -0.010), "floor", C.FAIL),
    ("a foot sinks 3 mm: a warning", "Squat", lambda D, o: D["min_z_feet"].__setitem__(8, -0.003), "floor", C.WARN),
    ("the loop does not close (5 mm)", "Squat", lambda D, o: D["hips_z"].__setitem__(-1, D["hips_z"][0] + 0.005), "loop", C.FAIL),
    ("an elbow reaches the IK limit", "Squat", lambda D, o: D["elbow_deg"].__setitem__(4, 150.4), "limits", C.WARN),
    ("the skin stretches x5", "Squat", lambda D, o: D["stretch_body_max"].__setitem__(4, 5.0), "skin", C.FAIL),
    ("the centre of mass leaves the foot", "Squat", lambda D, o: D["com_y"].__setitem__(10, D["support"][1] + 0.05), "balance", C.FAIL),
    ("a prop comes closer than allowed but does not touch (10 mm of 20)", "Pullup", lambda D, o: D["bar_clear_mm"].__setitem__(30, 10.0), "clearance", C.WARN),
]
def main():
    bad = 0
    print(f"{'what we broke':92s} | check     | expected | got")
    for what, name, mut, check, want in CASES:
        got = run(name, mut)[check]; ok = got == want; bad += (not ok)
        print(f"{what[:92]:92s} | {check:9s} | {want:8s} | {got:5s} {'ok' if ok else 'WRONG'}")
    clean = [run(e["name"], lambda D, o: None) for e in C.EXERCISES]
    nclean = sum(1 for r in clean for v in r.values() if v == C.FAIL)
    print(f"\nunmodified data: {nclean} FAIL across {len(clean)} exercises (must be 0)")
    print(f"{len(CASES)} defects: {len(CASES) - bad} caught as expected, {bad} wrong")
    return 1 if (bad or nclean) else 0
if __name__ == "__main__": sys.exit(main())

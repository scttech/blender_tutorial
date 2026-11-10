"""check_actions.py - run the standard checks on every exercise and print one table. Plain Python: no Blender needed.

    python3 -I tools/check_actions.py            # exit code 1 if anything FAILS (WARN does not fail)

It reads exports/<name>_measure.json (written by build_all_actions.py in Blender), exports/order_test.json and tools/exercise_registry.py.

PASS  the check is met.   WARN  met, but at or near a limit: look at it.   FAIL  not met.   -  the check does not apply to this exercise.

Check        Applies to      PASS if                                                  WARN if
reach        all             every wrist reaches its target within 1 mm              within 3 mm
floor        all             the lowest vertex is above -2 mm                        above -5 mm
loop         all             first and last frame differ by under 0.5 mm              the speeds either side of the seam differ by over 25% of the top speed
limits       all             no elbow bend over 149 and no knee bend over 154 degrees  (the IK limits are 150 and 155; a pose AT the limit hides how far it wanted to go)
skin         all             the body (hands excluded) stretches at most x3          at most x4; or the volume loss is over 15%
order        all             the action plays identically after any other action (under 0.01 mm)
ankles       registry        the ankles move under 0.5 mm
contacts     registry        the planted contacts move under 0.5 mm
balance      registry        the centre of mass stays over the sole of the foot       within 2 cm of its edge
clearance    registry        the prop stays at least the given distance from the body on every frame      closer than the distance but not touching
"""
import json, os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__)); HOME = os.path.dirname(HERE)
R = {}; exec(open(os.path.join(HERE, "exercise_registry.py")).read(), R); EXERCISES = R["EXERCISES"]
PASS, WARN, FAIL, NA = "PASS", "WARN", "FAIL", "-"

def load(name):
    p = os.path.join(HOME, "exports", f"{name.lower()}_measure.json")
    return json.load(open(p)) if os.path.exists(p) else None

def seam_speeds(v, fps=30):
    return abs(v[1] - v[0]) * fps, abs(v[-1] - v[-2]) * fps, max(abs(v[i + 1] - v[i]) for i in range(len(v) - 1)) * fps

def rate(value, good, ok, lower_is_better=True):
    if lower_is_better: return PASS if value < good else WARN if value < ok else FAIL
    return PASS if value > good else WARN if value > ok else FAIL

def run_checks(ex, D, order):
    out, detail = {}, []
    reach = max(D["reach_err_mm"]); out["reach"] = rate(reach, 1.0, 3.0); detail.append(("reach", f"worst wrist error {reach:.3f} mm"))
    low = min(min(D["min_z_hands"]), min(D["min_z_feet"]), min(D["min_z_body"]))
    out["floor"] = rate(-low, 0.002, 0.005) if low < 0 else PASS; detail.append(("floor", f"lowest vertex {low * 1000:+.1f} mm"))
    key = ex.get("loop_key", "hips_z"); v = D[key]; s0, s1, smax = seam_speeds(v); seam = abs(v[-1] - v[0]) * 1000
    out["loop"] = FAIL if seam >= 0.5 else (WARN if smax > 1e-6 and abs(s0 - s1) > 0.25 * smax else PASS)
    detail.append(("loop", f"seam {seam:.3f} mm; speeds either side {s0 * 1000:.0f} and {s1 * 1000:.0f} mm/s (top speed {smax * 1000:.0f})"))
    el, kn = max(D["elbow_deg"]), max(D["knee_deg"])
    out["limits"] = WARN if (el > 149 or kn > 154) else PASS; detail.append(("limits", f"elbow up to {el:.1f}, knee up to {kn:.1f} degrees (limits 150 and 155)"))
    sb, vol = max(D["stretch_body_max"]), min(D["vol_pct"])
    out["skin"] = FAIL if sb > 4 else WARN if (sb > 3 or vol < -15) else PASS; detail.append(("skin", f"body stretch up to x{sb:.1f}, volume {vol:+.1f}% (hands: x{max(D['stretch_hands_max']):.1f})"))
    ow = order["worst_mm"] if order else None
    out["order"] = NA if ow is None else (PASS if ow < 0.01 else FAIL); detail.append(("order", "no order test file" if ow is None else f"worst difference {ow:.4f} mm over {len(order['actions'])} actions"))
    if "ankles" in ex["checks"]:
        a = max(D["ankle_drift_mm"]); out["ankles"] = rate(a, 0.5, 0.5); detail.append(("ankles", f"worst ankle drift {a:.3f} mm"))
    else: out["ankles"] = NA
    if "contacts" in ex["checks"]:
        ks = [k for k in ("ball_y", "ball_z", "wrist_y", "wrist_z") if k in D]
        drift = max((max(D[k]) - min(D[k])) * 1000 for k in ks) if ks else float("nan")
        out["contacts"] = FAIL if math.isnan(drift) else rate(drift, 0.5, 0.5); detail.append(("contacts", f"worst contact drift {drift:.3f} mm"))
    else: out["contacts"] = NA
    if "balance" in ex["checks"]:
        lo, hi = D["support"]; mn, mx = min(D["com_y"]), max(D["com_y"]); margin = min(mn - lo, hi - mx) * 100
        out["balance"] = FAIL if margin < 0 else (WARN if margin < 2 else PASS); detail.append(("balance", f"centre of mass {mn * 100:+.1f} to {mx * 100:+.1f} cm; sole {lo * 100:+.1f} to {hi * 100:+.1f}; margin {margin:.1f} cm"))
    else: out["balance"] = NA
    if ex["clearance"]:
        worst = PASS; txt = []
        for k, need in ex["clearance"]:
            m = min(D[k]); st = PASS if m >= need else (WARN if m >= 0 else FAIL); txt.append(f"{k} {m:.0f} mm (need {need})")
            worst = FAIL if FAIL in (worst, st) else (WARN if WARN in (worst, st) else PASS)
        out["clearance"] = worst; detail.append(("clearance", "; ".join(txt)))
    else: out["clearance"] = NA
    return out, detail

COLUMNS = ["reach", "floor", "loop", "limits", "skin", "order", "ankles", "contacts", "balance", "clearance"]
def main():
    order = json.load(open(os.path.join(HOME, "exports", "order_test.json"))) if os.path.exists(os.path.join(HOME, "exports", "order_test.json")) else None
    rows, details, missing = [], {}, []
    for ex in EXERCISES:
        D = load(ex["name"])
        if D is None: missing.append(ex["name"]); continue
        res, det = run_checks(ex, D, order); rows.append((ex["name"], res)); details[ex["name"]] = (res, det, ex)
    w = max(len(n) for n, _ in rows) if rows else 8
    print(f"{'exercise':{w}s} | " + " | ".join(f"{c:9s}" for c in COLUMNS))
    print("-" * (w + 3 + 12 * len(COLUMNS)))
    for n, res in rows: print(f"{n:{w}s} | " + " | ".join(f"{res[c]:9s}" for c in COLUMNS))
    fails = sum(1 for _, r in rows for c in COLUMNS if r[c] == FAIL); warns = sum(1 for _, r in rows for c in COLUMNS if r[c] == WARN)
    print(f"\n{len(rows)} exercises | {fails} FAIL | {warns} WARN" + (f" | no measurement file for: {', '.join(missing)}" if missing else ""))
    for n, (res, det, ex) in details.items():
        flagged = [(c, t) for c, t in det if res.get(c) in (WARN, FAIL)]
        if flagged or ex.get("notes"):
            print(f"\n{n}" + (f": {ex['notes']}" if ex.get("notes") else ""))
            for c, t in flagged: print(f"  {res[c]} {c}: {t}")
    return 1 if (fails or missing) else 0

if __name__ == "__main__": sys.exit(main())

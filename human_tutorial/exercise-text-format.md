# Writing an exercise as text

An exercise can be a small [TOML](https://toml.io) file in `tools/exercises/` instead of a Python table. [tools/exercise_dsl.py](tools/exercise_dsl.py) compiles it into the same `(frame, pose)` table that `build_action()` takes, so every check from [Step 17](17-the-exercise-recipe.md) applies unchanged. Examples: [squat.toml](tools/exercises/squat.toml), [goblet_squat.toml](tools/exercises/goblet_squat.toml) (extends the squat and swaps the arms for a held kettlebell), [reverse_lunge.toml](tools/exercises/reverse_lunge.toml) (a Python generator plus hands that ride on the hips), [kettlebell_deadlift.toml](tools/exercises/kettlebell_deadlift.toml) (a curve keyed every 5 frames).

```toml
name = "Squat"
timeline = [[1, "stand"], [25, "bottom"], [33, "bottom"], [61, "stand"]]   # keep top-level keys ABOVE the first [table]

[params]                       # named numbers
depth = 0.58

[poses.stand]                  # bone -> move | at | rot | wrot | props   (the table format in anim_core.py)
Hips = { move = [0, 0, 0] }
"Hand_IK.L" = { at = [0.12, -0.40, 1.30] }     # bone names with a dot need quotes; write the left side, the right is mirrored

[poses.bottom]
extends = "stand"              # inherit; what is written here replaces the same entry of the same bone
Hips = { move = [0, 0.14, "=-depth"] }          # "=..." is an expression: params, f (the frame), pi, sin cos tan radians degrees sqrt atan2 abs min max
```

| Feature | How |
|---|---|
| **Variant of another exercise** | `extends = "Squat"` at the top, then only the params and poses that differ. The timeline is inherited unless you write one. |
| **Per-key override** | `{ frame = 25, pose = "bottom", set = { depth = 0.5 } }` |
| **Sampled curve** | `{ frames = [1, 31, 3], pose = "swing" }` is frame 1 to 31, every 3rd, with `f` set in the expressions |
| **Geometry a table cannot say** | `generator = "mace_pose"` on a pose, with `args`; the function lives in a Python file named by `python = "mace.py"`. Rigid pivots, solved heights and two-pass hand placement (push-up, lunge, pull-up, sit-up) are this kind |
| **Layered poses** | `extends = ["body_bottom", "arms_bottom"]` layers poses in order, later ones replacing earlier ones entry by entry. A child exercise that redefines a pose with its own `extends`, `generator` or `post` swaps what that pose is built from: this is how a kettlebell lunge is the lunge with a different `hands_on_hips` |
| **Hands and props that ride the body** | a `post` hook runs after the body pose is made and reads it: `post = [ { fn = "ride_arms", args = { style = "hips_fists" } } ]` puts fists on the hips wherever the hips go; `ride_prop` puts a kettlebell or mace at the chest and snaps both hands to it. Styles are measured once on the standing rest pose (`poselib.py`) |
| **Lying and floor work** | `arms_on_floor` (hands flat beside the body), `dead_bug_limbs` (the table-top legs and arms that extend as hinges about the hip and shoulder) and `curl_body` (the lying body, with the pelvis settled on the floor) in `poselib.py` and `situp.py` |
| **Lying legs and arms** | `lying_legs` places both legs as hinges about the hips (leg raise, flutter kicks, bicycle crunch, V-up) and lifts the pelvis if straight legs would sink the thighs into the floor; `arms_toward` reaches the hands toward the ankles; `ride_arms` computes the right arm separately from the left (a twisting torso moves them differently) and takes `sides = "L"` to leave the other arm free |
| **Standing motions** | `moves.py` also has `calf_raise` (each foot turns about its ball), `jumping_jack` (feet leave the floor, arms swing on an arc) and `hip_abduction` (one leg out to the side, one hand on a rail) |
| **Body motions** | `moves.py` has `hinge_body` (deadlift, good morning, row) and `squat_body`; `lunge.py`, `pushup.py`, `situp.py` (`curl_body`) and `pullup.py` (`hang_pose`) hold the generators for lunges, push-ups, lying curls and hanging |
| **Register it** | one entry in `tools/exercise_registry.py` with `file="x.toml"`, then `build_all_actions.py` and `check_actions.py` as before |

**Mistakes are errors, not silent**: an unknown pose, a misspelt entry (`mvoe`), an unknown name in an expression, frames that go backwards, a pose that extends itself, and a `timeline` written after a `[table]` heading (TOML makes it part of that table) each stop the build and say where. `python3 -I tools/test_dsl.py` runs the 25 tests of the compiler.

**Is it faithful?** `tools/check_dsl_equivalence.py` (run in Blender) builds `pushup.toml` and `lunge.toml` and the Python tables they replace, and compares every keyframe of all 117 curves: the worst difference is 0 for the push-up and 1.2e-7 for the lunge (an Euler-angle round trip). `squat.toml` and `mace_10_to_2.toml` were equivalent to `squat.py` and `mace.py` (difference 0) until we changed them on purpose: the Python version holds the arms forward, which let the elbows flare, so the text squat now has the hands behind the head, and the real 10-to-2 holds the mace behind the neck with the head hanging behind the back (Step 16 built it in front of the chest). The Python tables stay as the Step 13 and Step 16 originals.

**Two bugs worth knowing:** a rotation matrix has several equivalent sets of Euler angles, and converting it back can jump between them from one key to the next. A hand on the bicycle crunch flickered because its rotation flipped by up to 162 degrees between keys; `anim_core.write` now picks the set nearest the previous key (the largest change is now 25 degrees). And an arm placed by mirroring the left side is wrong when the torso is twisted, so `ride_arms` computes each side itself.

**Fixed grips, not swapped ones:** the 10-to-2 first avoided the arms crossing by swapping which hand holds which grip, which made the hands trade places mid-swing. The grips are now fixed, and the mace is turned 55 degrees about the vertical while the head is on the left, so the forearms pass behind each other instead of through each other (the arm-to-arm clearance went from -78 mm to +10 mm). The unused `grab_mace_swap` slider is still on the rig.

**Tuning a new exercise:** write the file, run it, read `tools/check_actions.py`. When reach fails, scan the parameters with a probe (compile the file with a grid of values, pose one key, print the wrist error): the kettlebell deadlift's top and middle were fixed that way (the bell was too far from the shoulders; then the arms were pulled out of reach midway until the bell's path was lifted by 5 cm). **Key a curve densely** (every 3 to 5 frames) whenever a limb sweeps an arc: the hanging leg raise's knee folded to 90 degrees with only the ends keyed, and 32 degrees at the worst of the dense keys.

**What is not converted yet:** the sit-up, pull-up, chin-up and kettlebell swing are still Python tables (their generators are used by text files: `situp.py`, `pullup.py`).

**Limits:** the format does not yet cover a pose that depends on the previous one, the `contact_extra`/`bar_extra` measurement helpers (those stay in Python), or a diagram output. The `HalfSquat` entry in the registry is a demonstration, not an exercise from the app; it passes every check except that nobody has looked at it.

[Contents](README.md)

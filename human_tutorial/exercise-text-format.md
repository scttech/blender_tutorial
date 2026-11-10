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
| **Body motions** | `moves.py` has `hinge_body` (deadlift, good morning, row) and `squat_body`; `lunge.py`, `pushup.py`, `situp.py` (`curl_body`) and `pullup.py` (`hang_pose`) hold the generators for lunges, push-ups, lying curls and hanging |
| **Register it** | one entry in `tools/exercise_registry.py` with `file="x.toml"`, then `build_all_actions.py` and `check_actions.py` as before |

**Mistakes are errors, not silent**: an unknown pose, a misspelt entry (`mvoe`), an unknown name in an expression, frames that go backwards, a pose that extends itself, and a `timeline` written after a `[table]` heading (TOML makes it part of that table) each stop the build and say where. `python3 -I tools/test_dsl.py` runs the 25 tests of the compiler.

**Is it faithful?** `tools/check_dsl_equivalence.py` (run in Blender) builds `squat.toml`, `mace_10_to_2.toml`, `pushup.toml` and `lunge.toml` and the Python tables they replace, and compares every keyframe of all 117 curves: the worst difference is 0 for the first three and 1.2e-7 for the lunge (an Euler-angle round trip).

**Tuning a new exercise:** write the file, run it, read `tools/check_actions.py`. When reach fails, scan the parameters with a probe (compile the file with a grid of values, pose one key, print the wrist error): the kettlebell deadlift's top and middle were fixed that way (the bell was too far from the shoulders; then the arms were pulled out of reach midway until the bell's path was lifted by 5 cm). **Key a curve densely** (every 3 to 5 frames) whenever a limb sweeps an arc: the hanging leg raise's knee folded to 90 degrees with only the ends keyed, and 32 degrees at the worst of the dense keys.

**What is not converted yet:** the sit-up, pull-up, chin-up and kettlebell swing are still Python tables (their generators are used by text files: `situp.py`, `pullup.py`).

**Limits:** the format does not yet cover a pose that depends on the previous one, the `contact_extra`/`bar_extra` measurement helpers (those stay in Python), or a diagram output. The `HalfSquat` entry in the registry is a demonstration, not an exercise from the app; it passes every check except that nobody has looked at it.

[Contents](README.md)

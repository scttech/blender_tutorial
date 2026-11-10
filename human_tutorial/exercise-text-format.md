# Writing an exercise as text

An exercise can be a small [TOML](https://toml.io) file in `tools/exercises/` instead of a Python table. [tools/exercise_dsl.py](tools/exercise_dsl.py) compiles it into the same `(frame, pose)` table that `build_action()` takes, so every check from [Step 17](17-the-exercise-recipe.md) applies unchanged. Examples: [squat.toml](tools/exercises/squat.toml), [half_squat.toml](tools/exercises/half_squat.toml) (extends the squat), [mace_10_to_2.toml](tools/exercises/mace_10_to_2.toml) (uses a Python generator).

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
| **Register it** | one entry in `tools/exercise_registry.py` with `file="x.toml"`, then `build_all_actions.py` and `check_actions.py` as before |

**Mistakes are errors, not silent**: an unknown pose, a misspelt entry (`mvoe`), an unknown name in an expression, frames that go backwards, a pose that extends itself, and a `timeline` written after a `[table]` heading (TOML makes it part of that table) each stop the build and say where. `python3 -I tools/test_dsl.py` runs the 22 tests of the compiler.

**Is it faithful?** `tools/check_dsl_equivalence.py` (run in Blender) builds `squat.toml` and `mace_10_to_2.toml` and the Python tables they replace, and compares every keyframe of all 117 curves: the worst difference is 0.

**What is not converted yet:** the push-up, sit-up, pull-up, chin-up, lunge and kettlebell swing are still Python. Each computes its poses from the mesh or the rig (rigid motion about the toes, a solved hip height, hands placed on the torso), which needs a generator function. Converting them would move code, not simplify it, so it is better done when a variant needs it.

**Limits:** the format does not yet cover a pose that depends on the previous one, the `contact_extra`/`bar_extra` measurement helpers (those stay in Python), or a diagram output. The `HalfSquat` entry in the registry is a demonstration, not an exercise from the app; it passes every check except that nobody has looked at it.

[Contents](README.md)

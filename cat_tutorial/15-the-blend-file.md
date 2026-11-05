# Step 15: The Blender file

**Goal:** a single `.blend` file that someone can download, open, and keep working on: change the animations, add new ones, and re-export.

**The file:** `cat_game_animations.blend` (34.3 MB) in this folder.

## What is inside

- **The cat:** the mesh `Mesh_0`, the armature `SmartRigArmature` with the readable bone names from Step 7, and the shape key `Breathe`.
- **All 15 animations**, each saved as its own action. Every action has a **fake user**, so Blender keeps it even when nothing uses it:

| Group | Actions |
|---|---|
| Idle layers | `TailSwish`, `HeadLook`, `Breathing` (the shape key) |
| Movement | `Walk`, `Run`, `Crawl`, `Jump` |
| Sitting | `Sit`, `SitTailSwish`, `LookAround`, `LickPaw` |
| Rolls | `RollLeft`, `RollRight` |
| Attacks | `PawSwipe`, `Bite` |

- **The textures, packed in.** The four images are stored inside the file, so it does not depend on any other files.
- **The scripts, as text blocks.** `cat_anim_core.py`, `cat_anim_sit.py`, `cat_anim_gaits.py`, `cat_anim_jump.py`, `cat_anim_roll.py` and `cat_anim_combat.py` are inside the file, along with a text block called `README_CAT_ANIMATIONS`.
- **No active action.** The rig is in its rest pose when you open the file. Pick an action to preview it.

## Opening it and trying an animation

1. Open the file in Blender. (Made with Blender 5.2. Older versions may open it, but we have not tested that.)
2. Select `SmartRigArmature`.
3. Switch to the **Animation** workspace. In the **Dope Sheet**, change the mode to **Action Editor**.
4. Use the action drop-down to pick one, for example `Run`.
5. Press **Space** to play. The timeline range is set on the action's own frame range, but the scene range may still be 1 to 96, so extend it for longer actions (for example `LookAround` is 120 frames).

## Changing an animation

**By hand.** In **Pose Mode**, with an action selected, scrub to a frame, move bones, and press **I** to key them. The **Graph Editor** edits the curves. Each action only keys the bones it needs, so a change to `Run` does not affect `Bite`.

**With code.** The scripts in the file rebuild an action from numbers you can edit. In the **Scripting** workspace, make a new text block with:

```python
import bpy
G = {}; G["G"] = G
for n in ["cat_anim_core.py", "cat_anim_sit.py", "cat_anim_gaits.py",
          "cat_anim_jump.py", "cat_anim_roll.py", "cat_anim_combat.py"]:
    exec(bpy.data.texts[n].as_string(), G)

G["build_run"]()          # rebuilds "Run"
```

Then edit a number at the top of the script (for example `stride` in `RUN_CFG` in `cat_anim_gaits.py`), run it again, and the action is replaced. **Building an action replaces the action with the same name**, so duplicate it first if you want to keep the old one.

| Function | Action |
|---|---|
| `build_sit()` | `Sit` (run this first, the sit family depends on it) |
| `build_sit_tail_swish()` | `SitTailSwish` |
| `build_run()` | `Run` |
| `build_crawl()` | `Crawl` |
| `build_jump()` | `Jump` |
| `build_roll("left")`, `build_roll("right")` | `RollLeft`, `RollRight` |
| `build_swipe("right")`, `build_swipe("left")` | `PawSwipe`, `PawSwipeLeft` |
| `build_bite()` | `Bite` |

Each build function prints measurements (foot error, ground contact, the lowest point of the mesh) so you can see if a change broke something.

**What is not in the scripts.** `Walk`, `TailSwish`, `HeadLook`, `Breathing`, `LookAround` and `LickPaw` were made earlier with scripts that are in the tutorial (Steps 8, 9, 11, 12 and 13), not in the library. Their keyframes are in the file and can be edited by hand. Rebuilding `Sit` does not break `LookAround` or `LickPaw`: we checked that all three still join with a **0.0000 degree** joint difference.

## Exporting for the game

1. Select `SmartRigArmature` and `Mesh_0` only.
2. **File, Export, glTF 2.0**. Format: *glTF Binary (.glb)*, tick **Limit to: Selected Objects**.
3. Animation: Mode **Actions**. Under Optimize, **untick** *Keep Animation if no change (armature)*. This is what makes each animation contain only the bones it moves.
4. Data: keep **Shape Keys** and **Shape Key Animation** ticked (for `Breathing`).

The result is the same as `exports/cat_all_animations.glb`: 15 animations, 30.7 MB. See [Step 10](10-export-for-babylon.md) for why those settings matter and [Step 14](14-more-game-animations.md) for which animations can play together.

## Housekeeping and things to know

- **A leftover object:** `Icosphere` is a small mesh that came with the original import. We never found out what it is for. It is not skinned and is not exported (we exported only the armature and the cat). Delete it if you do not want it.
- **The model is large and its textures are heavy.** 30 MB of the export is textures. Shrinking them (for example to 2048 or 1024 pixels) is the obvious next step for the web.
- **The head bone is `neck_2`.** The bone called `head` has no mesh weights (see Step 9). Rename them if you want the names to match.
- **No jaw.** The mouth cannot open.
- **The cat came from a Meshy export.** Check the terms for that model before you share the file publicly. We did not.
- **Everything was measured in Blender, and nothing has been tested in Babylon.js.** That is the biggest open item.

## Ideas for what to build next

A game usually also wants some of these. We have not built them.

| Animation | Why |
|---|---|
| Stand up | the way out of `Sit`. Playing `Sit` backward is the quick version |
| Turn in place, left and right | otherwise the cat can only pivot as a stiff statue |
| Hurt or hit reaction | very common |
| Land or fall | pairs with `Jump` |
| Pounce | a crouch, then a long leap with a paw swipe |
| Lie down and sleep | a good idle for downtime |
| Open mouth (a jaw) | needed to make `Bite` look like a bite |
| Others: stretch or yawn, scratch, shake off, climb, eat or drink, meow | depends on the game |

---

[← Previous: More game animations](14-more-game-animations.md) · [Contents](README.md)

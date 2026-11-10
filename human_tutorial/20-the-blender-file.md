# Step 20: The Blender file

**Goal:** say exactly what is in `human_rig.blend`, how to use it, and what to keep or throw away. It is the one `.blend` we keep; every other scene we made along the way was temporary.

## What is in it (29.85 MB)

| Part | Contents |
|---|---|
| `Body` | the 7,770-vertex low-poly mesh, parented to `Rig` with automatic weights plus the Step 8 finger fixes; one material with the Step 18 **web** textures |
| `Rig` | 74 bones: 52 deform bones, the Root, the IK and pole controls, the finger and grab sliders, the hidden Grips collection, and the three prop bones; 18 constraints and 42 drivers |
| `Kettlebell`, `Mace`, `PullupBar` | the props, each parented to its own bone on `Rig` |
| `Body_HighPoly` | the 94,690-vertex original, hidden, in the `Reference` collection, kept for re-running Step 3 |
| `CS_Box`, `CS_Diamond` | the control-shape meshes, in the `Widgets` collection (excluded from the view layer) |
| 8 actions | Chinup, Kbswing, Lunge, Mace10to2, Pullup, Pushup, Situp, Squat. Each has a **fake user** and **none is assigned**, so the rig opens in the T-pose |
| 10 images | the web set (`base_2048`, `normal_1024p`, `orm_512`, `emission_512`) and the four originals, `orig_base`, `orig_normal`, `orig_orm`, `orig_emission` |

The scene runs at 30 fps. Its frame range (1 to 31) is just what was left over from the last test: each action has its own range, and the animation scripts do not depend on the scene's.

## Using it

**Play an exercise:** select `Rig`, open the **Dope Sheet**'s **Action Editor** and pick an action; or in Python:

```python
rig = bpy.data.objects["Rig"]
rig.animation_data_create().action = bpy.data.actions["Squat"]
bpy.context.scene.frame_end = int(rig.animation_data.action.frame_range[1])
```
Unassign it (`rig.animation_data.action = None`) before running the build and export scripts; the export script does this itself.

**Pose by hand:** the sliders (`fist`, the per-finger sliders, `grab_kettlebell` and the others) are custom properties on the controls, in the **Item** tab of the sidebar. From a script, call `rig.update_tag()` after setting them ([Step 11](11-finger-controls.md)).

**Build a new exercise:** copy `tools/exercises/_template.py`, then follow [Step 17](17-the-exercise-recipe.md).

**Export:** run `tools/export_glb.py` ([Step 19](19-export-for-babylon.md)).

## Decisions

1. **The original textures stay.** The four `orig_*` images are about 19 MB of the file. We could drop them, but then `shrink_textures.py` could not be re-run at another size or with the emission layer in a different state. Disk space is not a concern here, so they stay. They did come from the Meshy GLB, so they could be re-imported from it, but the repo does not keep a copy of that GLB.
2. **The file is committed as the final version.** It is 30 MB and each further committed save adds another 30 MB to the history, so commit it again only for a change that matters. The scripts, documents and the exported GLB are the reproducible part.
3. **Leftovers vanish on their own.** Three unused meshes (`Cube`, `Skeleton_Plan`, `Skeleton_Plan.001`) and one material (`Dots Stroke`) have no users and no fake user. Blender drops them the next time the file is saved and reopened, so we left them alone.

## Still open

- **The emission layer.** It is kept by default; it is a grey glow layer from the source file and may not be wanted. See [Step 18](18-shrink-the-textures.md).
- **Forearm twist bones.** The wrist pinches a little when the forearm twists.
- **Self-collision.** Nothing checks that a hand or knee does not pass through the body.
- **Exercises not built:** goblet squat, barbarian squat, kettlebell clean, mace 360. [Step 17](17-the-exercise-recipe.md) is the recipe.
- **Viewer.** `viewer/index.html` has never rendered in a browser ([Step 19](19-export-for-babylon.md)).

## The whole pipeline, in order

1. `decimate_body.py`, `clean_body.py` (Steps 3 and 4)
2. `build_armature.py` with `HANDS = True`, `bind_and_weight.py`, `build_controls.py`, `build_finger_controls.py` (Steps 6 to 11)
3. `build_props.py`, `build_prop_rig.py` (Steps 12 and 15)
4. `build_all_actions.py`, then `check_actions.py` (Steps 13 to 17)
5. `shrink_textures.py` (Step 18)
6. `export_glb.py`, then `verify_glb.py` and `verify_babylon.js` (Step 19)

---

[← Previous: Export for Babylon.js](19-export-for-babylon.md) · [Contents](README.md)

# Blender Tutorial: Rigging and Animating a Human Model

A learning log built step by step, in the same style as the [cat tutorial](../cat_tutorial/README.md). Each step shows what we did, how to do it by hand in Blender's interface, and the Python equivalent.

**Goal:** take an existing human model, clean it up, give it a skeleton that can articulate every finger and limb, then animate gym exercises (push-ups, sit-ups, lunges, squats, pull-ups, chin-ups, kettlebell and steel mace work) and export them for the web.

**Setup:** Blender, optionally with the MCP for Blender addon running, driven from Claude Code. The model is a Meshy-generated `.glb` (`Meshy_AI_Athletic_Male_Gym_Mod_..._image-to-3d-texture.glb`).

> Tip: any Python snippet in these tutorials can be run yourself. Switch to the **Scripting** workspace, open a new text block, paste, and press **Alt+P**.

## What we know about the model so far

Read straight from the `.glb` header with `../cat_tutorial/tools/inspect_glb.py`, before opening Blender:

| Property | Value |
|---|---|
| File size | 24.5 MB (four JPEG textures, about 19 MB of that) |
| Meshes | 1 single mesh, no skeleton, no animations, no shape keys |
| Vertices / triangles | 94,690 / 172,636 (far too heavy for low-poly, reduced to 7,770 / 15,536 in [Step 3](03-reduce-the-polygon-count.md)) |
| Bounds | 1.9 m wide, 1.89 m tall, 0.33 m deep: a confirmed T-pose (checked in Blender, [Step 1](01-inspect-the-model.md)) |
| Origin | at the waist, so the feet sit about 0.95 m below the floor |
| Materials | 1, unnamed |

## Contents

### Part 1: Inspect and clean up
1. [Inspect the model](01-inspect-the-model.md): import it, check scale, orientation and pose
2. [Fix the origin, scale and orientation](02-fix-scale-origin-orientation.md): apply transforms so the rig behaves
3. [Reduce the polygon count](03-reduce-the-polygon-count.md): hybrid, a masked Decimate down to about 15k triangles
4. [Clean up the mesh](04-clean-up-the-mesh.md): normals and slivers checked, soles fixed, and the finding that the fingers are fused in the source

### Part 2: The skeleton
5. [Plan the bone layout](05-plan-the-bone-layout.md): 53 bones, measured on the body and checked against it
6. [Build the body armature](06-build-the-body-armature.md): the centre line and left side, mirrored with Symmetrize, with bone roll set so rotating about X bends the joint
7. [Build the hands](07-build-the-hands.md): 30 finger bones, a fist test, and a correction to the Step 6 roll rules
8. [Parent and weight](08-parent-and-weight.md): automatic weights, a finger-by-finger fix for the fused hands (with the measured trade-off), and an export-ready clean-up
9. [Test the rig](09-test-the-rig.md): ten poses judged by eye and by numbers, a palm-twist test, and two fixes we tried and rejected

### Part 3: Controls
10. [IK for arms and legs](10-ik-for-arms-and-legs.md): hands and feet that stay planted, and why a straight arm breaks IK
11. [Finger controls](11-finger-controls.md): sliders for a fist, each finger and the thumb, driven by formulas, with the limits of a fused hand shown
12. [Props](12-props.md): a kettlebell and a steel mace the hands grip and move with, and a measured fit of hand to handle (a pull-up bar is added in Step 15)

### Part 4: Movement techniques
Not one tutorial per exercise. Many exercises share the same body mechanics, so each tutorial teaches a *technique*, and the exercises that use it are built afterwards from a recipe.

13. [Legs driven by IK](13-legs-driven-by-ik.md): a keyframe-table workflow, planted feet, balance and a clean loop, taught with the **squat** (also: lunge, goblet squat, deadlift hinge)
14. [Floor work](14-floor-work.md): a stiff body pivoting on its toes, a pelvis settled onto the floor, and hands that ride on the torso (**push-up**, **sit-up**)
15. [Hanging and pulling](15-hanging-and-pulling.md): a pull-up bar prop, hands fixed to it while the body moves, the overhand-to-underhand twist tested, and a rig bug in how grabs blend (**pull-up**, **chin-up**)
16. [Loaded movement](16-loaded-movement.md): the prop leads and the hands follow: a kettlebell on a pendulum arc with a timed hip hinge, and a mace turning about the hands. Curved paths need dense keys (**kettlebell swing**, **mace 10-to-2**; the clean, 360 and barbarian squat are listed as future work)

### Part 5: The exercise library
17. [The exercise recipe](17-the-exercise-recipe.md): a procedure, a template and an **automatic checklist** (tested against four real bugs), proved by building a lunge. After this, an exercise is a table, not a tutorial.

| Exercise | Technique | Status |
|---|---|---|
| Squat, push-up, sit-up, pull-up, chin-up | [13](13-legs-driven-by-ik.md), [14](14-floor-work.md), [15](15-hanging-and-pulling.md) | built |
| Lunge (static) | [13](13-legs-driven-by-ik.md) and [14](14-floor-work.md), built in [17](17-the-exercise-recipe.md) | built |
| Kettlebell swing, mace 10-to-2 | [16](16-loaded-movement.md) | built |
| Goblet squat, barbarian squat | squat plus a prop riding the torso | not built: see Step 17 |
| Kettlebell clean, mace 360 | loaded movement | not built: see Step 17 |

### Part 6: Using the model elsewhere
18. [Shrink the textures for the web](18-shrink-the-textures.md): 19.4 MB to 1.7 MB of textures (a 20 MB GLB to 2.3 MB), with resolution spent where the detail is, and a measured warning that PSNR hides soft eyes
19. [Export for Babylon.js](19-export-for-babylon.md): one 2.75 MB GLB with the props and eight animations; the IK and finger drivers baked, and checked against Blender to 0.036 mm in our own skinning and in Babylon itself
20. [The Blender file](20-the-blender-file.md): what is in `human_rig.blend`, how to use it, what we kept (the original textures) and what is still open

## Files

- Images live in `blender-human-tutorial-images/`.
- `exports/` will hold the exported `.glb` files.
- `tools/decimate_body.py` builds the low-poly `Body` from the hidden `Body_HighPoly` reference ([Step 3](03-reduce-the-polygon-count.md)). `tools/clean_body.py` runs the Step 4 checks and fixes. `tools/rig_landmarks.py` holds the bone layout as data ([Step 5](05-plan-the-bone-layout.md)). `tools/build_armature.py` builds the armature from it ([Step 6](06-build-the-body-armature.md)). `tools/bind_and_weight.py` binds the mesh and makes the weights export-ready ([Step 8](08-parent-and-weight.md)). `tools/build_controls.py` adds the IK controls ([Step 10](10-ik-for-arms-and-legs.md)). The pipeline order is `build_armature.py` (with `HANDS = True`), then `bind_and_weight.py`, then `build_controls.py`. `tools/build_finger_controls.py` adds the finger sliders ([Step 11](11-finger-controls.md)); run it after `build_controls.py`. `tools/anim_core.py` builds looping actions from keyframe tables and measures them, `tools/exercises/squat.py`, `pushup.py`, `situp.py`, `pullup.py` (pull-up and chin-up), `lunge.py`, `kbswing.py` and `mace.py` are the exercise tables, and `_template.py` is the one to copy; `tools/shrink_textures.py` shrinks the textures ([Step 18](18-shrink-the-textures.md)); `tools/export_glb.py`, `tools/verify_glb.py`, `tools/verify_babylon.js` and `viewer/index.html` export, verify and view the result ([Step 19](19-export-for-babylon.md)); `tools/exercise_registry.py` lists them all, `tools/check_actions.py` checks them and `tools/test_checker.py` tests the checker ([Step 17](17-the-exercise-recipe.md)); `tools/build_all_actions.py` rebuilds every action, measures it and runs the order test ([Step 15](15-hanging-and-pulling.md)) ([Step 14](14-floor-work.md) adds world rotation, rigid pivoting and floor checks), and `tools/make_motion_chart.py` draws the measurements ([Step 13](13-legs-driven-by-ik.md)). `tools/build_props.py` and `tools/build_prop_rig.py` add the kettlebell and mace and their grips ([Step 12](12-props.md)); the prop rig re-runs the finger script. `tools/pose_tests.py` poses the rig and measures the skin ([Step 9](09-test-the-rig.md)); `tools/smooth_weights.py` is the weight-smoothing experiment we rejected. More rig and animation scripts will follow.

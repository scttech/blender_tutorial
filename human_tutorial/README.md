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

## Contents (planned)

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
11. Finger controls: a curl control per finger and a fist pose
12. Props: a kettlebell and a steel mace, and parenting them to a hand

### Part 4: Exercises
13. Squat
14. Lunge
15. Push-up
16. Sit-up
17. Pull-up and chin-up (hand grip differs, overhand versus underhand)
18. Kettlebell: swing, goblet squat, clean
19. Steel mace: 360, 10-to-2, and the barbarian squat

### Part 5: Using the model elsewhere
20. Shrink the textures for the web
21. Export for Babylon.js
22. The Blender file

## Files

- Images live in `blender-human-tutorial-images/`.
- `exports/` will hold the exported `.glb` files.
- `tools/decimate_body.py` builds the low-poly `Body` from the hidden `Body_HighPoly` reference ([Step 3](03-reduce-the-polygon-count.md)). `tools/clean_body.py` runs the Step 4 checks and fixes. `tools/rig_landmarks.py` holds the bone layout as data ([Step 5](05-plan-the-bone-layout.md)). `tools/build_armature.py` builds the armature from it ([Step 6](06-build-the-body-armature.md)). `tools/bind_and_weight.py` binds the mesh and makes the weights export-ready ([Step 8](08-parent-and-weight.md)). `tools/build_controls.py` adds the IK controls ([Step 10](10-ik-for-arms-and-legs.md)). The pipeline order is `build_armature.py` (with `HANDS = True`), then `bind_and_weight.py`, then `build_controls.py`. `tools/pose_tests.py` poses the rig and measures the skin ([Step 9](09-test-the-rig.md)); `tools/smooth_weights.py` is the weight-smoothing experiment we rejected. More rig and animation scripts will follow.

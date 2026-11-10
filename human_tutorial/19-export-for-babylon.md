# Step 19: Export for Babylon.js

**Goal:** one GLB file holding the character, the three props and all eight exercise animations, that plays correctly in Babylon.js. And proof that it does, because "the exporter did not report an error" proves nothing about a rig built on IK, drivers and sliders.

**The problem:** glTF has no IK, no drivers, no custom-property sliders and no constraints. It stores one thing: the rotation, translation and scale of each bone on each frame. Everything we built in Steps 10 to 12 has to be **baked** into that. Blender's exporter does this by sampling the finished pose on every frame; whether it did it *right* is what this step tests.

## The export

[`tools/export_glb.py`](tools/export_glb.py) writes `exports/human_all_animations.glb`. The choices, and what we learned:

| Setting | Why |
|---|---|
| `export_animation_mode='ACTIONS'` | every action becomes its own named animation (Chinup, Kbswing, Lunge, Mace10to2, Pullup, Pushup, Situp, Squat). Our actions have a fake user and none is assigned, so this is the mode that finds them. |
| `export_def_bones=True` | only the 52 deform bones leave Blender; the IK targets, poles, sliders and grips stay behind. The exporter samples through them. |
| `export_force_sampling=True` | one key per frame, so IK and driver results are baked rather than guessed from our sparse keys |
| prop bones marked **deform** during the export only | the prop meshes are bone-parented, and with "deform bones only" the exporter silently drops any object parented to a bone it does not export. We got a 2.7 MB file with no kettlebell. The script sets the flag on `Kettlebell`, `Mace` and `PullupBar`, exports, and restores the flags in a `finally`. The props have no vertex groups, so the skin is unchanged. Leaving the flag on would let the next automatic-weights bind give them weights. |
| backface culling on in the body material | exports glTF `doubleSided = false`, half the triangles to draw. The body is a closed shell. |

**Python**
```python
exec(open("/Users/chris/blender_tutorial/human_tutorial/tools/export_glb.py").read(), {})
```

**By hand:** select Body, Rig and the three props, **File, Export, glTF 2.0 (.glb)**, tick **Limit to: Selected Objects**, in **Animation** choose **Actions**, tick **Sampling Animations**, and under **Armature** tick **Export Deform Bones Only**. The prop trick needs the three prop bones' **Deform** checkbox (Bone properties) ticked first.

Result: **2.75 MB**, 55 joints (52 body bones plus 3 prop bones), 8 animations, textures from Step 18 (JPEG 33 KB and 612 KB, PNG 977 KB, JPEG 35 KB).

## Does it match Blender?

Two independent checks, neither of which uses Blender's own importer.

**1. Skin the GLB ourselves** ([`tools/verify_glb.py`](tools/verify_glb.py), run in Blender for numpy only). It parses the file's JSON and binary, samples each animation channel, builds the joint matrices, does linear blend skinning with the file's own weights, and compares **all 7,770 body vertices** (the file has 10,401 because the exporter splits vertices at UV seams; we match them back to Blender's by rest position, which agreed to 0.000 mm) with Blender's evaluated mesh. It does this at 11 frames of each action, and compares 200 vertices of each prop with the prop's Blender position.

**2. Babylon.js itself** ([`tools/verify_babylon.js`](tools/verify_babylon.js)): Babylon 7.54.3 runs in Node with its `NullEngine` (no browser, no GPU), loads the GLB, plays each animation group and reads back the skinned vertices with `getPositionData(true)`, at the first, middle and last frames, against Blender.

| Action | Blender frames | Own skinning, worst vertex | Babylon, worst vertex | Props |
|---|---|---|---|---|
| Squat | 1 to 61 | 0.023 mm | 0.023 mm | 0.000 mm |
| Push-up | 1 to 67 | 0.007 mm | 0.008 mm | 0.000 mm |
| Sit-up | 1 to 79 | 0.026 mm | 0.024 mm | 0.000 mm |
| Pull-up | 1 to 100 | 0.007 mm | 0.008 mm | 0.000 mm |
| Chin-up | 1 to 100 | 0.007 mm | 0.007 mm | 0.000 mm |
| Lunge | 1 to 57 | 0.026 mm | 0.026 mm | 0.000 mm |
| Kettlebell swing | 1 to 53 | 0.036 mm | 0.033 mm | 0.000 mm |
| Mace 10 to 2 | 1 to 31 | 0.007 mm | 0.007 mm | 0.000 mm |

The worst error anywhere is **0.036 mm**, far below anything visible. The IK legs and arms, the finger sliders and the grab constraints all survived the bake, and the kettlebell, mace and bar follow their bones. The prop rows are 0.000 because the props' own vertices are compared after the bone transform; a missing or wrongly parented prop would show.

**What the checks do not cover:** we compared 11 frames per action in our own skinning and 3 in Babylon, not every frame; the 8 actions are only compared at those frames, not at the speed the browser plays them.

## Things worth knowing

1. **Our first comparison reported errors of up to 9 cm. The error was ours.** We assumed glTF time 0 is the action's first frame. The exporter writes **frame / fps**, so frame 1 is at 0.0333 s and every animation has a 1/30 s hold at the start. Once the comparison used the same convention, the errors dropped to 0.036 mm. When a verifier and an exporter disagree, check the verifier's assumptions before the exporter.
2. **Babylon plays animation groups at 60 frames per second.** A 2.033 s squat is a group from 0 to 122. Use the group's `from` and `to`, never frame numbers from Blender.
3. **No animation leaks into another.** Step 13's base pose means every animation carries **165 channels** (55 joints, each with translation, rotation and scale), the same set. The Babylon check plays the actions one after another in one scene, in alphabetical order, stopping each before the next, and every one still matched; that is a switch test of sorts, but not the full every-pair test of Step 15.
4. **The prop materials export as double sided** (we only switched culling on for the body). They are tiny; set it on them too if you want every triangle counted.
5. **The Root bone is not in the file.** The hips are a child of the `Rig` node. The animations move the hips, and nothing in the exercises needs a separate root.
6. **The exporter writes a lot of WARNING lines** during the export. They were harmless here; the check above is why we can say so.

## Viewing it

[`viewer/index.html`](viewer/index.html) is a small Babylon.js page: an orbit camera, a floor, and one button per animation. Serve the folder and open it:

```
cd human_tutorial && python3 -m http.server 8000      # then http://localhost:8000/viewer/
```

**It has not been opened in a real browser.** We checked that the server delivers it and the GLB, and the Node test above exercises the same loader and animation code, but nothing has rendered a frame. Treat it as untested.

**Concepts**
- **Baking:** replacing a computed result (IK, a driver) with plain keys of its output on every frame.
- **Skin and joints (glTF):** a mesh with per-vertex joint indices and weights; the engine blends the joints' matrices.
- **NullEngine:** Babylon without rendering, for tests in Node.
- **Animation group:** Babylon's name for one glTF animation.

**Caveats**
- The file has no IK, so moving a hand in Babylon will not bend the elbow. Every pose comes from the baked animations.
- The 1/30 s hold at the start of each animation loops with the cycle: trim it in the engine if it shows.
- The emission texture is included; drop it in Step 18 if you do not want the glow.

---

[← Previous: Shrink the textures](18-shrink-the-textures.md) · [Contents](README.md) · Next: The Blender file (not written yet)

# Step 10: Export for Babylon.js

**Goal:** export the cat as a `.glb` file where each animation is separate, so a Babylon.js app can play them individually or together, then check what was really written to the file.

> **Status:** the export and the inspection below were run and checked. **We have not loaded the file in Babylon.js**, so the Babylon code in this step is untested.

## What glTF does with animations

- Each Blender **action** becomes one glTF **animation**.
- Babylon.js loads each glTF animation as an **`AnimationGroup`**, which you can `start()`, `stop()` and loop on its own.
- Bone animation is stored as channels on bone nodes (translation, rotation, scale). Shape key animation is stored as a **weights** channel on the mesh.

## The export

**By hand:**
1. Select the armature and the mesh (leave out the camera, light and the stray `Icosphere`).
2. **File**, **Export**, **glTF 2.0 (.glb/.gltf)**.
3. In the export panel: **Format** = *glTF Binary (.glb)*, tick **Limit to: Selected Objects**.
4. Open **Animation**, set **Mode** to *Actions*, tick **Shape Keys** and **Shape Key Animation** under *Data*.
5. Under **Animation > Optimize**, untick **Keep Animation if no change (armature)**. This matters (see below).

**Python**
```python
bpy.ops.export_scene.gltf(
    filepath="/Users/chris/blender_projects/cat_tutorial/exports/cat_idle_test.glb",
    export_format='GLB',
    use_selection=True,                                   # only the armature and mesh we selected
    export_animations=True,
    export_animation_mode='ACTIONS',                      # one glTF animation per Blender action
    export_optimize_animation_size=True,
    export_optimize_animation_keep_anim_armature=False,   # drop bones that do not change in an action
    export_morph=True,                                    # include the shape key
    export_morph_animation=True,                          # include its animation
    export_skins=True)
```

Option names and values differ between Blender versions. We read them from the running Blender instead of guessing:

```python
props = bpy.ops.export_scene.gltf.get_rna_type().properties
print([k for k in props.keys() if "anim" in k])
print([i.identifier for i in props["export_animation_mode"].enum_items])
```

## Check the file, do not trust it

A `.glb` is a binary wrapper around JSON, so you can read what was exported. `tools/inspect_glb.py` prints the animations, which bones each one drives, durations and image sizes:

```
python3 tools/inspect_glb.py exports/cat_idle_test.glb
```

## What we found

**First export** (default settings) had the right animations but a problem:

```
animation 'HeadLook':  102 channels (translation, rotation and scale for all 34 bones)
animation 'TailSwish': 102 channels (all 34 bones)
animation 'Breathing': 1 channel (weights on Mesh_0)
```

`HeadLook` and `TailSwish` each wrote channels for **every bone**, not just the ones they animate. In Babylon, if you played both at once, each would keep forcing the other's bones back to rest, so they could not layer. The cause is the exporter option that keeps unchanging bone channels (`export_optimize_animation_keep_anim_armature`).

**Second export** with that option off:

```
animation 'HeadLook':  2 channels  -> rotation of neck_1, neck_2
animation 'TailSwish': 5 channels  -> rotation of tail_1 ... tail_5
animation 'Breathing': 1 channel   -> weights of Mesh_0 (morph target 'Breathe')
```

Each animation now touches only its own targets, so they can play alone or together without fighting.

**Also in the file:** 1 mesh, 1 skin with 34 joints, 1 morph target named `Breathe`, and each animation is 4 seconds long.

## Using it in Babylon.js (untested)

```js
const result = await BABYLON.SceneLoader.ImportMeshAsync("", "/models/", "cat_idle_test.glb", scene);

// Each glTF animation arrives as an AnimationGroup, found by name.
const anim = Object.fromEntries(result.animationGroups.map(g => [g.name, g]));

// The loader may auto-start the first group. Start from a known state.
result.animationGroups.forEach(g => g.stop());

anim.Breathing.start(true);   // true = loop
anim.TailSwish.start(true);
anim.HeadLook.start(true);

// Later, any one of them can be stopped or restarted on its own:
anim.HeadLook.stop();
```

Things to check when you try it: that the three groups are listed by the names above, that the cat's breathing shows up (it needs the mesh's morph target manager, which the loader creates), and that the loop looks seamless.

## Things to know

- **File size is 30.5 MB, almost all of it textures.** The four JPEG images are 13.5, 8.9, 1.3 and 0.2 MB. That is heavy for a web page. Reducing the texture size (for example 2048 px, or 1024 px for a mobile build) and using WebP or compressed textures would shrink it a lot. We have not done this yet.
- **Timing starts at 1/24 s, not 0.** The exporter writes absolute times, so each animation runs from 0.042 s to 4.0 s. This is harmless for looping in Babylon, but it is why a group's start frame is not 0.
- **Exporter warning:** "More than one shader node tex image used for a texture". The material, from the original Meshy file, has several image nodes feeding one texture slot, and glTF uses the first. It exported fine.
- **The rig's bone names are the animation targets.** If you rename a bone later (for example `neck_2` to `head`), re-export.

## Concepts

- **glTF / GLB:** the "JPEG of 3D" for the web. `.glb` is the single-file binary version.
- **AnimationGroup (Babylon):** a set of animations that start and stop together. One glTF animation becomes one group.
- **Sampling:** the exporter bakes each animation into a key for every frame, so the result does not depend on Blender's interpolation. It makes bigger files but plays back the same everywhere.
- **Verify the output, not just the input.** An export that "finished" can still contain the wrong thing. Open the file and look.

---

[← Previous: Idle breathing and head movement](09-idle-breathing-and-head.md) · [Contents](README.md) · [Next: A walk cycle →](11-walk-cycle.md)

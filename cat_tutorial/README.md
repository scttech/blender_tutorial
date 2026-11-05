# Blender Tutorial: Animating a Cat Model

A learning log built step by step. Each step shows what we did, how to do it by hand in Blender's interface, and the Python equivalent (which is what Claude ran through the Blender connection).

**Setup:** Blender with the MCP for Blender addon running, driven from Claude Code. The cat model is a Meshy-generated `.glb` file.

> Tip: any Python snippet in these tutorials can be run yourself. Switch to the **Scripting** workspace (tab along the top of Blender), open a new text block, paste, and press **Alt+P** (or the play button).

## Contents

### Part 1: Scene basics
1. [Inspect the scene](01-inspect-the-scene.md): find out what is in a scene before changing it
2. [Add a primitive and give it a material](02-add-a-primitive-and-material.md): a red sphere, with the Principled BSDF shader
3. [Clear the scene](03-clear-the-scene.md): delete objects and purge leftover data

### Part 2: The cat and its rig
4. [Import the cat (.glb)](04-import-the-cat.md): bring in a glTF model
5. [Inspect the rig](05-inspect-the-rig.md): armatures, vertex groups and actions
6. [Identify the bones](06-identify-the-bones.md): work out what unnamed bones are from structure
7. [Rename the bones and highlight them](07-rename-and-highlight-bones.md): readable names, labels and colors in the viewport

### Part 3: Animation
8. [Animate a tail swish](08-tail-swish.md): keyframes, phase lag and a seamless loop
9. [Idle breathing and head movement](09-idle-breathing-and-head.md): three separate actions, shape keys for breathing, and a bone-label correction

### Part 4: Using the model elsewhere
10. [Export for Babylon.js](10-export-for-babylon.md): export separate animations to glTF and check what is in the file

11. [A walk cycle](11-walk-cycle.md): foot placement, a hand-made IK solver, and checking foot contact by measuring

12. [Body motion for the walk](12-walk-body-motion.md): dip and rock the body without breaking foot contact, a gait chart, and an interpolation bug found by measuring

13. [Sit down, look around, lick a paw](13-sit-look-lick.md): three chained actions, solving a sitting pose, turning the head about the true vertical, and a 3D nose-to-paw solve

14. [More game animations](14-more-game-animations.md): run, crawl, jump, rolls, paw swipe, bite and a sitting tail swish, plus the bugs we found by measuring
15. [The Blender file](15-the-blend-file.md): what is in `cat_game_animations.blend`, how to change an animation, and how to export

### Coming next
16. Stand up, turn in place, hurt, land, pounce, sleep, and a jaw so the bite can open
17. Sideways sway and spine twist for the walk (needs a 3D leg solver)
18. Shrinking the textures for the web (the exports are about 30 MB)

## Files

- Images live in `blender-cat-tutorial-images/`.
- `cat_game_animations.blend` is the Blender file with the cat and all 15 animations ([Step 15](15-the-blend-file.md)).
- `exports/` holds the exported `.glb` files: `cat_idle_test.glb` (Step 10, three animations) and `cat_all_animations.glb` (all 15 animations, updated as we went).
- `tools/cat_anim_*.py` is the animation script library, also stored inside the `.blend`.
- `tools/inspect_glb.py` prints what is inside a `.glb` (animations, which bones they drive, image sizes).
- `tools/make_gait_chart.py` draws the Step 12 gait chart as an SVG from measured walk data.

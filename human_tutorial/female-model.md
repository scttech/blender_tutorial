# A female model on the same animations

The decision: **keep the skeleton exactly as it is and fit a new mesh to it.** The animations are keyframes on that skeleton's bones, so a second body that rides on the *same* bones (same names, same rest positions) plays all of them unchanged. Nothing in `tools/exercises/` has to be rewritten.

## Why not a second skeleton with different proportions
Many scripts place hands, feet and props at coordinates measured on this skeleton (the shoulder is at z = 1.45 m, an arm reaches 0.52 m, a thigh is 0.43 m, a bench pad is 0.475 m up). About 40 lines across `moves.py`, `dumbbell.py`, `situp.py`, `poselib.py` and a few others do that. A shorter or differently proportioned skeleton would make every one of them wrong at once (hands off the bar, feet through the floor). The code written for the last few exercises (`carry.py`, `manmaker.py`) reads arm, leg and plate sizes from the rig instead, so it would follow a new skeleton; the older code would need the same treatment first.

## The plan
1. **Source mesh.** You generate her in Meshy in the same T-pose and the same style as the man. The T-pose matters most: arms straight out, legs straight, feet flat.
2. **Fit it to the skeleton.** Scale and shape the mesh so the shoulders, hips, knees and ankles sit on the existing joints (a slightly shorter body is fine if it is scaled to the skeleton's height). This is the same clean-up as Steps 1 to 4, then Step 8 (automatic weights, smoothed) onto the existing armature.
3. **Skin split.** Run `split_skin.py` so she has the same `Skin` and `ClothesHairEyes` materials; the app's skin tone code then works for both.
4. **Rerun everything.** `build_all_actions.py`, then `check_actions.py`. The reach and loop checks cannot change (they are about the skeleton). What can change is **clearance**: a different chest, hips and thighs can touch the arms, the floor in push-ups, or each other in squats. Expect a handful of WARN or FAIL lines to fix, mostly in the floor work and the lunge.
5. **Export.** Same `export_glb.py`. Because the bone names and rest positions are identical, the animation tracks in her GLB are identical to his; the app could even load the animations once and apply them to either model.

## Rule for any new exercise from now on
Read lengths from the rig (`rig.data.bones[...]`) rather than typing metres, as `carry.py` and `manmaker.py` do. That keeps open the option of a different skeleton later, at no cost.

## What I need from you
The Meshy model (a GLB or FBX in a T-pose, same pose and scale as the man). Nothing else; the rest is the steps above.

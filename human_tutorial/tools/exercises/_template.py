"""_template.py - copy this file to start a new exercise. It runs as it is: a bodyweight squat to 20 cm, as a worked example.

HOW TO USE IT (the recipe, Step 17)
  1. Copy to tools/exercises/<name>.py and rename TEMPLATE below.
  2. Choose the TECHNIQUE (Steps 13-16) and look at its file for the pattern to copy:
        feet planted, hips move ........ squat.py, lunge.py       (solve the hips against the knee bend)
        floor work, body pivots ........ pushup.py                (anim_core.rigid about the toes), situp.py (settle onto the floor, hands ride the chest)
        hands fixed, body moves ........ pullup.py                (grab the bar, solve the heights)
        prop leads, hands follow ....... kbswing.py, mace.py      (place the prop; two-pass; key densely along an arc)
  3. Write the pose (a dict) and the table: [(frame, pose), ...]. The LAST key must equal the FIRST for a loop.
  4. Add ONE entry to tools/exercise_registry.py (name, module, table, keys, the optional checks that apply).
  5. In Blender run tools/build_all_actions.py, then   python3 -I tools/check_actions.py   and fix anything that is not PASS.

THE VOCABULARY (all positions are world metres; angles are degrees; write the LEFT side and it mirrors; write the right explicitly to override)
    "move":  (dx, dy, dz)     offset of a bone whose parent is not posed (Hips, the controls) from its rest position
    "at":    (x, y, z)        absolute world position of a control (Hand_IK, Foot_IK, poles, props)
    "rot":   (rx, ry, rz)     rotation on the bone's own axes: elbow flexion -X, knee +X, spine/neck/hips flexion +X, finger/wrist flexion +X
    "wrot":  (rx, ry, rz)     rotation about the WORLD axes, for Foot_IK, Hand_IK and the prop bones
    "props": {name: value}    sliders: fist, grab_kettlebell, grab_mace, grab_bar_over, grab_bar_under, grab_kb_swing ...
RULES THAT COST US A BUG EACH
    * every action keys EVERY control (the library does it): never rely on a channel you did not key
    * key a CURVED path (an arc, a hinge) every few frames, never with just the extremes
    * set the grab sliders you need explicitly; a stale one blends in
    * anything that depends on the body (hands on the chest, a prop on an arc) is a TWO-PASS build: pose, read, place
    * measure on every frame, not just the keys
"""
TEMPLATE_DEPTH = 0.20                                  # the example squat's depth in metres

def pose(depth):
    return {"Hips": {"move": (0, 0, -depth)},
            "Spine": {"rot": (6 * depth / 0.2, 0, 0)},                      # a little forward lean, scaled with the depth
            "Hand_IK.L": {"at": (0.12, -0.40, 1.30 - depth)}}              # hands held in front, following the shoulders down

TEMPLATE = [(1, pose(0.0)), (20, pose(TEMPLATE_DEPTH)), (26, pose(TEMPLATE_DEPTH)), (46, pose(0.0))]

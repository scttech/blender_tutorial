"""squat.py - Step 13: the bodyweight squat, as a keyframe table (see tools/anim_core.py for the format).

    G = {}; exec(open(".../anim_core.py").read(), G); exec(open(".../exercises/squat.py").read(), G)

The feet do not move: the Foot_IK controls stay at their rest position (anim_core keys every control at rest unless a table says otherwise,
so the squat plays the same after any other action), and the knees bend because the hips drop.
Hands are held out in front for balance; their targets lower with the shoulders so the arms stay within reach.
30 fps. 2.0 s loop: 0.8 s down, 0.27 s pause at the bottom, 0.93 s up.
"""
DEPTH, SIT_BACK = 0.58, 0.14            # hips drop and move back at the bottom (metres). 0.58 puts the thighs just below parallel

STAND  = {"Hips": {"move": (0, 0, 0)},
          "Spine": {"rot": (0, 0, 0)}, "Spine1": {"rot": (0, 0, 0)}, "Spine2": {"rot": (0, 0, 0)},
          "Neck": {"rot": (0, 0, 0)}, "Head": {"rot": (0, 0, 0)},
          "Hand_IK.L": {"at": (0.12, -0.40, 1.30)}}
BOTTOM = {"Hips": {"move": (0, SIT_BACK, -DEPTH)},
          "Spine": {"rot": (14, 0, 0)}, "Spine1": {"rot": (10, 0, 0)}, "Spine2": {"rot": (6, 0, 0)},      # 30 degrees of forward lean
          "Neck": {"rot": (-8, 0, 0)}, "Head": {"rot": (-14, 0, 0)},                                      # keep the eyes forward
          "Hand_IK.L": {"at": (0.12, -0.42, 0.88)}}
SQUAT = [(1, STAND), (25, BOTTOM), (33, BOTTOM), (61, STAND)]

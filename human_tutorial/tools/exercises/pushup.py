"""pushup.py - Step 14: the push-up, as a keyframe table (see tools/anim_core.py).

    G = {}; exec(open(".../anim_core.py").read(), G); exec(open(".../exercises/pushup.py").read(), G)

The body is held straight and PIVOTS ON THE TOES, so every key is one rigid motion computed from one formula (anim_core.rigid):
  * the Hips move and turn by the angle phi, and take the spine, head and legs with them
  * the ankle targets (Foot_IK) and the knee poles ride the same rigid motion, so the legs keep their shape and the foot keeps its angle
  * the toes bend back by exactly phi, so they stay flat on the floor
  * the hands are planted (they never move): palms flat, fingers forward, 25 cm apart
phi is the angle the body has turned from standing: 90 would be lying flat. 73.5 is the top of the push-up (arms nearly straight),
88 the bottom (chest about 4 cm off the floor). 30 fps, a 2.2 s loop: 1.0 s down, 0.2 s pause, 1.0 s up.
Numbers come from calibrating against the mesh (see Step 14): toe pivot height 3.5 cm, hand height 4.1 cm, top angle for arms that
just reach, bottom angle for the chest 4 cm from the floor.
"""
from mathutils import Vector

PHI_UP, PHI_DN = 73.5, 88.0                    # degrees from standing
Y_PIVOT, Z_PIVOT = 0.65, 0.035                 # where the toes are planted (the ball of the foot): behind the origin, 3.5 cm up
HAND_X, HAND_Z = 0.25, 0.041                   # left hand (the right mirrors it): 25 cm out, wrist 4.1 cm up puts the palm on the floor

_b = rig.data.bones
_H0, _A0, _S0, _KP0 = (_b[n].head_local.copy() for n in ("Hips", "Foot_IK.L", "UpperArm.L", "Knee_Pole.L"))
_B0 = Vector((0.0, _b["Foot.L"].tail_local.y, _b["Foot.L"].tail_local.z))        # the ball of the foot, on the centre line
_HAND_Y = rigid(_B0, (0, Y_PIVOT, Z_PIVOT), PHI_UP)(_S0).y                          # hands directly under the shoulders at the top

def pushup_pose(phi, hand_x=HAND_X, pole_out=0.0, pole_up=0.10):
    """hand_x: how far each wrist is from the centre line (0.25 = the standard push-up; 0.05 = diamond).
    pole_out: 0 leaves the elbow pole where the rig rests it; otherwise the pole sits this far out to the side of the shoulder and rides on the body, so the elbows flare outward. pole_up: how far up (toward the back) it sits; a pole level with the shoulder lets a folded arm drop its elbow through the floor"""
    M = rigid(_B0, (0, Y_PIVOT, Z_PIVOT), phi)
    pose = {"Hips": {"move": tuple(M(_H0) - _H0), "rot": (phi, 0, 0)},
            "Foot_IK.L": {"at": tuple(M(_A0)), "wrot": (phi, 0, 0)}, "Knee_Pole.L": {"at": tuple(M(_KP0))},
            "Toes.L": {"rot": (-phi, 0, 0)},
            "Neck": {"rot": (-18, 0, 0)}, "Head": {"rot": (-28, 0, 0)},                         # lift the eyes to look ahead
            "Hand_IK.L": {"at": (hand_x, _HAND_Y, HAND_Z), "wrot": (0, 0, -90), "props": {"fist": 0.0}}}
    if pole_out: pose["Elbow_Pole.L"] = {"at": tuple(M(_S0 + Vector((pole_out, pole_up, 0.0))))}
    return pose

_MID = (PHI_UP + PHI_DN) / 2                    # a key halfway keeps the hips on their arc (a chord would shorten the legs)
PUSHUP = [(1, pushup_pose(PHI_UP)), (16, pushup_pose(_MID)), (31, pushup_pose(PHI_DN)),
          (37, pushup_pose(PHI_DN)), (52, pushup_pose(_MID)), (67, pushup_pose(PHI_UP))]

def contact_extra():
    """per-frame measurements for measure(): where the planted contacts are (the ball of the foot and the wrist), so their drift can be checked"""
    def extra(P, f):
        return {"ball_y": P["Toes.L"].head.y, "ball_z": P["Toes.L"].head.z, "wrist_y": P["Hand.L"].head.y, "wrist_z": P["Hand.L"].head.z}
    return extra


"""bench.py - exercises that use the Bench (a 47.5 cm high pad, 30 cm wide, y -0.2 to 0.9): the step-up and the Bulgarian split squat. Loaded with python = ["lunge.py", "poselib.py", "bench.py"] (carry.py is
NOT needed). Every length comes from the rig."""
import math
from mathutils import Vector

PAD = 0.475

def step_up(u, drive=75.0, lean=6.0):
    """a lateral step-up onto the bench with the LEFT leg (the body stands beside the bench, the left foot on the pad, the right foot on the floor). u = 0: the left foot on the pad, the right on the floor,
    the hips low (the left knee well bent). u = 1: standing tall on the pad, the right knee driven up `drive` degrees. The hips rise with u; the right foot stays on the floor until the hips have lifted it,
    then the knee comes up. No arms."""
    b = rig.data.bones; T = b["Thigh.L"].head_local; A0 = b["Foot_IK.L"].head_local; L = (T - A0).length
    ua = (b["Thigh.L"].tail_local - T).length; la = L - ua
    e = 0.5 - 0.5 * math.cos(math.pi * u); dx = -A0.x * 0.75                                      # the body shifts so the left foot is over the bench's middle
    left = Vector((0.0, A0.y, PAD + A0.z + 0.003))
    z0 = A0.z + 0.93 * L; z1 = left.z + 0.96 * L                                                   # the hips: low at the start (right leg nearly straight), high at the top (left leg nearly straight)
    hz = z0 + (z1 - z0) * e; a = math.radians(drive) * max(0.0, (e - 0.3) / 0.7)
    hip = Vector((dx - T.x, T.y, hz))                                                              # the right hip joint
    ank = hip + Vector((0.0, -ua * math.sin(a), -ua * math.cos(a) - la * 0.98)); ank.z = max(A0.z, ank.z)
    ank = Vector((dx - A0.x * 0.75 * 1.0, ank.y if a > 0 else A0.y, ank.z)); ang = -25.0 * min(1.0, a / math.radians(drive))
    out = {"Hips": {"move": (dx, 0.0, hz - T.z), "rot": (lean * e, 0, 0)},
           "Foot_IK.L": {"at": tuple(left), "wrot": (0, 0, 0)}, "Knee_Pole.L": {"at": (0.0, -0.6, left.z + 0.5)},
           "Foot_IK.R": {"at": tuple(ank), "wrot": (ang, 0, 0)}, "Knee_Pole.R": {"at": (ank.x, ank.y - 0.6, ank.z + 0.5)},
           "Neck": {"rot": (-lean * 0.3 * e, 0, 0)}, "Head": {"rot": (-lean * 0.3 * e, 0, 0)}}
    return out

def bulgarian(knee):
    """the Bulgarian split squat: a lunge (lunge.py) with the REAR foot (the right) resting its instep on the bench behind, the left foot forward on the floor. knee = the front knee's bend in degrees.
    No arms"""
    p = lunge_at_knee(knee)
    for k in ("Foot_IK.R", "Toes.R"): p.pop(k, None)
    rear = Vector((-FOOT_X, 0.72, PAD + 0.12))
    p["Foot_IK.R"] = {"at": tuple(rear), "wrot": (150.0, 0, 0)}; p["Knee_Pole.R"] = {"at": (-FOOT_X, -0.6, 0.25)}
    return p

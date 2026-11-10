"""build_finger_controls.py - Step 11: sliders that curl the fingers.

Run inside Blender after build_controls.py:   exec(open(".../build_finger_controls.py").read(), {})
Safe to re-run: it removes its own drivers and properties first.

Adds 7 slider properties to each hand control (Hand_IK.L / Hand_IK.R), shown in Pose Mode under  N > Item > Custom Properties:
    fist           0..1   closes all four fingers and the thumb together
    index middle ring pinky   -1..1   one finger's own curl, ADDED to the fist (-1 cancels a fist: fist 1 + index -1 = pointing)
    thumb          -1..1  the thumb's own curl, added to the fist
    thumb_oppose   0..1   swings the thumb toward the palm to meet the fingers (a separate motion from curling)
and a driver on every finger bone's rotation, so the sliders move the bones:
    curl = clamp(fist + own, 0, 1)    bone angle = curl * (the angle at full curl)
Full curl angles (degrees, proximal / middle / distal) come from the Step 7 fist: fingers 80 / 95 / 60, thumb 25 / 40 / 45.
If GRABS is defined before this runs (build_prop_rig.py does that), each grab slider ALSO closes the hand, so that one slider snaps
the hand to a prop and wraps the fingers around it:  GRABS = {"grab_mace": {"fist": 0.9, "thumb": -0.3, "oppose": 0.6}, ...}
    curl = clamp(fist + own + sum(grab * its fist value), 0, 1)       thumb adds its own value too; opposition adds its value
The finger bones are driven, so you pose fingers with the sliders, not by rotating the bones.
Drivers are baked into plain keyframes before export (Step 21).
"""
import bpy, math

rig = bpy.data.objects["Rig"]
GRABS = globals().get("GRABS", {})                  # optional: see the docstring
GRAB_NAMES = list(GRABS)
FINGERS = ("Index", "Middle", "Ring", "Pinky")
FULL = {"1": 80, "2": 95, "3": 60}                  # degrees at full curl
THUMB_FULL = {"1": 25, "2": 40, "3": 45}
OPPOSE_DEG = 35                                      # thumb opposition at 1.0

def hand_ctrl(side): return rig.pose.bones[f"Hand_IK.{side}"]

def add_driver(bone, axis, expression, variables):
    """variables: {name: (control bone, property)}"""
    try: bone.driver_remove("rotation_euler", axis)
    except Exception: pass
    fc = bone.driver_add("rotation_euler", axis); d = fc.driver
    d.type = 'SCRIPTED'; d.expression = expression
    for vname, (ctrl, prop) in variables.items():
        v = d.variables.new(); v.name = vname; v.type = 'SINGLE_PROP'
        v.targets[0].id = rig; v.targets[0].data_path = f'pose.bones["{ctrl}"]["{prop}"]'

def build(oppose_sign):
    for side in "LR":
        c = hand_ctrl(side)
        props = {"fist": (0.0, 1.0, "Close the whole hand"), "thumb_oppose": (0.0, 1.0, "Swing the thumb toward the palm"),
                 "thumb": (-1.0, 1.0, "Thumb's own curl, added to the fist")}
        for f in FINGERS: props[f.lower()] = (-1.0, 1.0, f"{f} finger's own curl, added to the fist")
        for name, (lo, hi, doc) in props.items():
            c[name] = 0.0
            c.id_properties_ui(name).update(min=lo, max=hi, soft_min=lo, soft_max=hi, description=doc)
        ctrl = f"Hand_IK.{side}"
        gvars = {f"g{i}": (ctrl, name) for i, name in enumerate(GRAB_NAMES)}
        extra_f = "".join(f" + g{i}*{GRABS[n]['fist']:.4f}" for i, n in enumerate(GRAB_NAMES))
        extra_t = "".join(f" + g{i}*{GRABS[n]['fist'] + GRABS[n]['thumb']:.4f}" for i, n in enumerate(GRAB_NAMES))
        extra_o = "".join(f" + g{i}*{GRABS[n]['oppose']:.4f}" for i, n in enumerate(GRAB_NAMES))
        for f in FINGERS:
            for k, deg in FULL.items():
                b = rig.pose.bones[f"{f}{k}.{side}"]; b.rotation_mode = 'XYZ'
                add_driver(b, 0, f"max(0.0, min(1.0, fist + own{extra_f})) * {math.radians(deg):.5f}",
                           {"fist": (ctrl, "fist"), "own": (ctrl, f.lower()), **gvars})
        for k, deg in THUMB_FULL.items():
            b = rig.pose.bones[f"Thumb{k}.{side}"]; b.rotation_mode = 'XYZ'
            add_driver(b, 0, f"max(0.0, min(1.0, fist + own{extra_t})) * {math.radians(deg):.5f}",
                       {"fist": (ctrl, "fist"), "own": (ctrl, "thumb"), **gvars})
        b = rig.pose.bones[f"Thumb1.{side}"]
        sign = oppose_sign[side]
        add_driver(b, 2, f"max(0.0, min(1.0, oppose{extra_o})) * {sign * math.radians(OPPOSE_DEG):.5f}",
                   {"oppose": (ctrl, "thumb_oppose"), **gvars})

def evalpose(): return rig.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones

def set_all(side, **kw):
    c = hand_ctrl(side)
    for k in ("fist", "index", "middle", "ring", "pinky", "thumb", "thumb_oppose"): c[k] = kw.get(k, 0.0)
    rig.update_tag()                      # setting a custom property from Python does NOT re-run the drivers by itself
    bpy.context.view_layer.update()

bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')

# ---- find which sign of the opposition rotation moves the thumb toward the palm (down, since the palm faces down)
signs = {"L": 1, "R": 1}
build(signs)
for side in "LR":
    set_all(side); z0 = evalpose()[f"Thumb3.{side}"].tail.z
    set_all(side, thumb_oppose=1.0); z1 = evalpose()[f"Thumb3.{side}"].tail.z
    if z1 > z0: signs[side] = -1
    set_all(side)
build(signs)
for side in "LR":
    set_all(side); z0 = evalpose()[f"Thumb3.{side}"].tail.z
    set_all(side, thumb_oppose=1.0); z1 = evalpose()[f"Thumb3.{side}"].tail.z
    print(f"thumb opposition {side}: sign {signs[side]:+d}, thumb tip moves {1000 * (z1 - z0):+.1f} mm in z (negative = toward the palm)")
    set_all(side)
bpy.ops.object.mode_set(mode='OBJECT')
print("drivers:", len(rig.animation_data.drivers), "| properties per hand:", len([k for k in hand_ctrl("L").keys() if k in
      ("fist", "index", "middle", "ring", "pinky", "thumb", "thumb_oppose")]))

"""build_armature.py - Steps 6 and 7: build the "Rig" armature from tools/rig_landmarks.py.

Run inside Blender with the Step 5 scene open (needs the "Body" mesh only for the final report).
Safe to re-run: it deletes the old "Rig" and rebuilds it.

    G = {}                       # optional: G["HANDS"] = True to include the finger bones (Step 7)
    exec(open(".../build_armature.py").read(), G)

Method: build the centre line and the LEFT side only, then Symmetrize (+X -> -X) to make the right side.
Roll: each bone's local X axis is set to the hinge of its joint, so "rotate about X" means "bend".
      arm, forearm: world Z   hand and fingers: world Y   thumb: world Z   spine, neck, head, legs, feet: world X
"""
import bpy
from mathutils import Vector

HANDS = globals().get("HANDS", False)
G = {}
exec(open("/Users/chris/blender_tutorial/human_tutorial/tools/rig_landmarks.py").read(), G)
FINGER_PREFIX = ("Index", "Middle", "Ring", "Pinky", "Thumb")

def wanted(name):
    return HANDS or not name.startswith(FINGER_PREFIX)

# the source data: centre + left side (the right side is made by Symmetrize)
BONES = [b for b in G["CENTRE"] + G["LEFT_ALL"] if wanted(b[0])]

def hinge_for(name):
    """world-space direction that this bone's local X axis should point along (the joint's hinge)"""
    if name.startswith("Thumb"):
        return Vector((0, 0, 1))        # the thumb curls ACROSS the palm, toward the little finger
    if name.startswith(("Hand", "Index", "Middle", "Ring", "Pinky")):
        return Vector((0, 1, 0))        # wrist and fingers bend in the front-back plane (palm-down T-pose: tips go down)
    if name.startswith(("Clavicle", "UpperArm", "ForeArm")):
        return Vector((0, 0, 1))        # the elbow hinge is vertical in a T-pose
    return Vector((1, 0, 0))            # spine, neck, head, legs, feet: bend forward and back

# ---------------------------------------------------------------- fresh armature
old = bpy.data.objects.get("Rig")
if old:
    data = old.data; bpy.data.objects.remove(old, do_unlink=True); bpy.data.armatures.remove(data)
arm_data = bpy.data.armatures.new("Rig")
rig = bpy.data.objects.new("Rig", arm_data)
bpy.data.collections["Collection"].objects.link(rig)
rig.show_in_front = True
arm_data.display_type = 'OCTAHEDRAL'
bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active = rig

# ---------------------------------------------------------------- bones
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
for name, head, tail, parent in BONES:
    b = eb.new(name)
    b.head, b.tail = Vector(head), Vector(tail)
    # roll: choose Z = X_hinge x Y_bone, so that X ends up on the hinge axis
    y_axis = (b.tail - b.head).normalized()
    z_axis = hinge_for(name).cross(y_axis)
    if z_axis.length > 1e-6: b.align_roll(z_axis.normalized())
for name, head, tail, parent in BONES:
    if parent:
        b = eb[name]; b.parent = eb[parent]
        b.use_connect = (b.head - eb[parent].tail).length < 1e-6      # connected when head sits on the parent's tail

# ---------------------------------------------------------------- mirror the left side to the right
for b in eb: b.select = b.select_head = b.select_tail = True
bpy.ops.armature.symmetrize(direction='POSITIVE_X')                   # copy +X (.L) onto -X (.R)
bpy.ops.object.mode_set(mode='OBJECT')

arm_data.bones["Root"].use_deform = False                             # Root only moves the whole character

# ---------------------------------------------------------------- report
names = [b.name for b in arm_data.bones]
left = [n for n in names if n.endswith(".L")]; right = [n for n in names if n.endswith(".R")]
print("bones:", len(names), "| left", len(left), "right", len(right), "centre", len(names) - len(left) - len(right),
      "| deform", sum(b.use_deform for b in arm_data.bones))
missing = [n[:-2] + ".R" for n in left if n[:-2] + ".R" not in names]
print("left bones without a right twin:", missing)
worst = 0.0
for n in left:
    l, r = arm_data.bones[n], arm_data.bones[n[:-2] + ".R"]
    for a, c in ((l.head_local, r.head_local), (l.tail_local, r.tail_local)):
        worst = max(worst, (Vector((-a.x, a.y, a.z)) - c).length)
print("worst mirror error (m):", round(worst, 6))

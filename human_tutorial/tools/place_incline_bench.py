"""place_incline_bench.py - make the static object "InclineBench" (a seat pad and a back pad tilted 40 degrees) and place it so the back pad just touches the back of the incline_body pose.

    exec(open(".../place_incline_bench.py").read(), {})        (run in Blender; safe to re-run)
The body in the incline exercises is posed by exercises/situp.py: incline_body(50): torso 50 degrees from vertical, hips on a seat 47.5 cm up. This script poses the rig that way, finds how far the chest's lowest point
(measured along the pad's normal) is from the pad plane, and moves the pad to touch it.
"""
import bpy, bmesh, math, numpy as np
from mathutils import Vector, Matrix
HOME = "/Users/chris/blender_tutorial/human_tutorial"; PHI = 50.0; SEAT = 0.475
G = {"bpy": bpy}; exec(open(f"{HOME}/tools/anim_core.py").read(), G); G["clear_pose"]()
ex = {}; exec(open(f"{HOME}/tools/exercises/situp.py").read(), G)
pose = G["incline_body"](PHI, SEAT)
for f, flat in G["expand"]([(1, pose)], True):
    for c, v in flat.items(): G["write"](c, v)
rig = bpy.data.objects["Rig"]; rig.update_tag(); bpy.context.view_layer.update()
v, _ = G["mesh_state"](); chest = v[G["torso_masks"]()[0]]
phi = math.radians(PHI); a = Vector((0, math.sin(phi), math.cos(phi))); n = Vector((0, -math.cos(phi), math.sin(phi)))      # up the torso; out of the pad toward the back
d = float((chest @ np.array(n)).min())                                    # the chest's lowest point along n: the pad's surface must be at this n-height
hips = G["pose_bones"]()["Hips"].head.copy()
old = bpy.data.objects.get("InclineBench")
if old: m = old.data; bpy.data.objects.remove(old, do_unlink=True); bpy.data.meshes.remove(m)
bm = bmesh.new()
# in the object's own frame: the back pad is 30 x 85 x 8 cm centred at the origin with its top at z = +4 cm (so the surface is the plane z = 0.04); the seat is 30 x 40 cm, 40 cm below
bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((0.30, 0.85, 0.08, 1.0)))
bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, -0.58, -0.34)) @ Matrix.Diagonal((0.30, 0.40, 0.08, 1.0)))
bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, -0.25, -0.62)) @ Matrix.Diagonal((0.05, 0.50, 0.80, 1.0)))
me = bpy.data.meshes.new("InclineBench"); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = False
ob = bpy.data.objects.new("InclineBench", me); ob.data.materials.append(bpy.data.materials["Mat_Bench"])
bpy.data.collections["Props"].objects.link(ob)
ob.rotation_euler = (-phi + math.pi / 2 - math.pi / 2, 0, 0)               # replaced below
# orient: local Y -> a (up the torso), local Z -> n
R = Matrix((Vector((1, 0, 0)), a, n)).transposed(); ob.rotation_euler = R.to_euler('XYZ')
P0 = hips + a * 0.40
ob.location = P0 + n * (d - 0.04 - n.dot(P0))
bpy.context.view_layer.update(); G["clear_pose"]()
print(f"incline bench placed: chest contact {d:.3f} along the pad normal; pad centre {tuple(round(x, 3) for x in ob.location)}")

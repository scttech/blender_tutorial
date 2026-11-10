"""export_glb.py - Step 19: export the character, the props and every exercise animation as ONE GLB for Babylon.js.

Run inside Blender with the finished scene open:
    exec(open(".../export_glb.py").read(), {})
Writes exports/human_all_animations.glb (override with OUT = "...").

What it does, and why
  * every action becomes its own glTF animation (export_animation_mode 'ACTIONS'), named after the action.
  * the exporter SAMPLES each frame of the evaluated pose, so IK, constraints and the finger drivers are baked into plain rotations
    and translations on the bones. (glTF cannot store IK, drivers or custom-property sliders.) Step 19 checks that this really holds.
  * only DEFORM bones are exported (export_def_bones): the 52 that move the skin. The controls, grips and the Root are left out.
  * the prop meshes are children of the prop bones, and the exporter drops objects whose bone it does not export, so the three prop
    bones are marked as deform for the duration of the export only (they have no vertex groups, so the skin is unchanged), and put back
    after. Marking them permanently would let the next automatic-weights bind give them weights.
  * backface culling is switched on for the material (exports doubleSided = false: half the triangles to draw). The mesh is a closed shell.
Textures are whatever Step 18 chose (the material's current images): base 2048 JPEG, normal 1024 PNG, small maps 512 JPEG.
"""
import bpy, os, json, struct

HOME = "/Users/chris/blender_tutorial/human_tutorial"
OUT = globals().get("OUT", f"{HOME}/exports/human_all_animations.glb")
PROPS = ("Kettlebell", "Mace", "PullupBar")
rig, body = bpy.data.objects["Rig"], bpy.data.objects["Body"]

# the actions must not be assigned (an assigned action would be exported as the "active" pose too), and the scene must be at rest
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.location = (0, 0, 0); pb.rotation_mode = 'XYZ'; pb.rotation_euler = (0, 0, 0)
bpy.context.scene.frame_set(1)
for n in ("Body", "Rig") + PROPS: bpy.data.objects[n].hide_set(False)
mat = body.data.materials[0]; culling_before = mat.use_backface_culling; mat.use_backface_culling = True

deform_before = {n: rig.data.bones[n].use_deform for n in PROPS}
for n in PROPS: rig.data.bones[n].use_deform = True
try:
    bpy.ops.object.select_all(action='DESELECT')
    for n in ("Body", "Rig") + PROPS: bpy.data.objects[n].select_set(True)
    bpy.context.view_layer.objects.active = rig
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', use_selection=True,
                              export_animation_mode='ACTIONS', export_def_bones=True, export_force_sampling=True,
                              export_optimize_animation_size=True, export_image_format='AUTO', export_apply=False)
finally:
    for n, v in deform_before.items(): rig.data.bones[n].use_deform = v        # always put the flags back
    mat.use_backface_culling = culling_before if globals().get("KEEP_CULLING") is False else True

f = open(OUT, "rb"); f.read(12); n, _ = struct.unpack("<I4s", f.read(8)); g = json.loads(f.read(n))
print(f"wrote {OUT} | {os.path.getsize(OUT) / 1e6:.2f} MB | joints {len(g['skins'][0]['joints'])} | animations {len(g['animations'])}: {[a['name'] for a in g['animations']]}")
print("prop deform flags restored:", {n: rig.data.bones[n].use_deform for n in PROPS}, "| doubleSided:", g["materials"][0].get("doubleSided"))

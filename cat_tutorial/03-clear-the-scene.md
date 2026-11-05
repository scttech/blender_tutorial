# Step 3: Clear the scene

**Goal:** remove the placeholder objects but keep the camera and light.

**By hand**
1. Click the Cube in the Outliner, **Shift+click** the Red Sphere to add it to the selection.
2. Hover over the 3D viewport and press **X**, then *Delete*.
3. To clean up leftover data: **File**, **Clean Up**, **Purge Unused Data**.

**Python**
```python
import bpy
for o in [o for o in bpy.data.objects if o.type == "MESH"]:
    bpy.data.objects.remove(o, do_unlink=True)
for m in [m for m in bpy.data.materials if m.users == 0]:
    bpy.data.materials.remove(m)
```

**Concepts**
- Deleting an object does not delete its **data** (mesh, material). Data with zero users stays in the file until purged.
- We kept the Camera and Light because you need them to view or render the result.

---

[← Previous: Add a primitive and give it a material](02-add-a-primitive-and-material.md) · [Contents](README.md) · [Next: Import the cat →](04-import-the-cat.md)

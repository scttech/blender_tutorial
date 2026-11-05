# Step 5: Inspect the rig

**Goal:** find out what we have to animate with.

**By hand:** select `SmartRigArmature`, then expand it in the Outliner to see the bones. To see how the mesh is attached, select `Mesh_0` and open the **Modifiers** tab (wrench icon) and the **Object Data** tab, where *Vertex Groups* are listed.

**Findings**
- **34 bones** in a single hierarchy, named generically (`Bone_000` to `Bone_033`).
- `Mesh_0` is skinned to the armature through an **Armature modifier**, with 34 **vertex groups** (one per bone, defining which vertices each bone moves).
- **No animations** exist in the file (no Actions).
- Scene timing: frames 1 to 250 at 24 fps.

**Python used to inspect**
```python
import bpy
arm = bpy.data.objects["SmartRigArmature"]
for b in arm.data.bones:
    print(b.name, "<-", b.parent.name if b.parent else None)
print([a.name for a in bpy.data.actions])
```

**Concepts**
- **Armature:** a skeleton made of bones. Moving a bone deforms the vertices weighted to it.
- **Parent/child bones:** rotating a parent (like the spine) carries its children (like the tail and legs).
- **Vertex group / weights:** how strongly each bone influences each vertex.
- **Action:** a saved set of keyframes. Animating creates one.

---

[← Previous: Import the cat](04-import-the-cat.md) · [Contents](README.md) · [Next: Identify the bones →](06-identify-the-bones.md)

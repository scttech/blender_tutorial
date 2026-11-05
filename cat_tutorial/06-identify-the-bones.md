# Step 6: Identify the bones

**Goal:** the bones have generic names, so work out which is which from the skeleton's structure.

**Method:** a skeleton's shape gives away what each bone does. We looked at three clues.

1. **Hierarchy (who is whose child).** Branch points are landmarks. A bone with several children is a junction, like a pelvis or shoulders. A bone with no children is the end of a limb, like a toe or the tail tip.
2. **Position (head and tail coordinates).** Each bone has a *head* (start) and *tail* (end) point. We printed them in world space to see where each chain runs. The cat's nose points toward -Y and its tail toward +Y, so Y tells us front from back. Z is height, so a chain ending near z=0 reaches the ground.
3. **Length and bend.** Leg bones are long, then short toward the paw. Bones that rise and then drop toward the front are a neck and head.

**Python used**
```python
arm = bpy.data.objects["SmartRigArmature"]
mw = arm.matrix_world
for b in arm.data.bones:
    h = mw @ b.head_local   # where the bone starts
    t = mw @ b.tail_local   # where it ends
    print(b.name, "parent:", b.parent.name if b.parent else None,
          "children:", len(b.children), h, t, b.length)
```

**Result** (my reading, not yet checked visually)

| Part | Bones (root to tip) | How we know |
|---|---|---|
| Root | `Bone_000` | No parent, tiny (0.03 m), sits at the rear |
| Pelvis | `Bone_001` | 4 children: spine, two back legs, tail |
| Spine | `Bone_003`, then `Bone_002` | One chain running forward (-Y) from the pelvis. `Bone_002` branches into 3, so it is the chest or shoulders |
| Neck and head | `Bone_023`, `022`, `021`, `020`, `019` | Rises to z=1.36, then drops toward the front. The last three are short, like head and nose |
| Front legs | `Bone_028` to `024`, and `Bone_033` to `029` | Start at the chest, go straight down, end at z of about 0 |
| Back legs | `Bone_008` to `004`, and `Bone_013` to `009` | Start at the pelvis, go down with a bend (`Bone_007`/`012` swing the foot forward) like a cat's hock |
| Tail | `Bone_018`, `017`, `016`, `015`, `014` | Starts at the pelvis, runs toward +Y, 5 bones with no children at the end |

Leg bones in order are upper leg, lower leg, wrist or hock, paw, toe.

**Left and right:** the cat faces -Y, so its right side is -X. That makes `Bone_028` and `Bone_008` the right legs, and `Bone_033` and `Bone_013` the left legs. The skeleton is centered at x of about -0.51, not 0, so the cat is offset from the origin.

**Concepts**
- **Head and tail of a bone:** the start and end points, not the animal's head and tail.
- **Rest pose:** this is the bones' default position. Animation moves bones away from it, then back.
- Guessing from structure works well for typical creature rigs. Checking by highlighting a bone is the confirmation step, which is what [Step 7](07-rename-and-highlight-bones.md) does.

---

[← Previous: Inspect the rig](05-inspect-the-rig.md) · [Contents](README.md) · [Next: Rename the bones and highlight them →](07-rename-and-highlight-bones.md)

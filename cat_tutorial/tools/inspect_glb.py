import json, struct, sys

path = sys.argv[1]
with open(path, "rb") as f:
    magic, version, length = struct.unpack("<4sII", f.read(12))
    clen, ctype = struct.unpack("<I4s", f.read(8))
    gltf = json.loads(f.read(clen))

print(f"GLB v{version}, {length/1e6:.1f} MB total")
nodes = gltf.get("nodes", [])
print("nodes:", len(nodes), "| meshes:", len(gltf.get("meshes", [])), "| skins:", len(gltf.get("skins", [])),
      "| animations:", len(gltf.get("animations", [])))
for s in gltf.get("skins", []):
    print("  skin joints:", len(s["joints"]))

for m in gltf.get("meshes", []):
    for p in m["primitives"]:
        print("mesh", m.get("name"), "| morph targets:", len(p.get("targets", [])),
              "| target names:", m.get("extras", {}).get("targetNames"), "| default weights:", m.get("weights"))

acc = gltf["accessors"]
print()
for a in gltf.get("animations", []):
    chans = a["channels"]
    by_path = {}
    for c in chans:
        tgt = c["target"]
        node = nodes[tgt["node"]].get("name", f"node{tgt['node']}") if "node" in tgt else "?"
        by_path.setdefault(tgt["path"], []).append(node)
    t_max = max(acc[s["input"]]["max"][0] for s in a["samplers"])
    t_min = min(acc[s["input"]]["min"][0] for s in a["samplers"])
    n_keys = max(acc[s["input"]]["count"] for s in a["samplers"])
    print(f"animation '{a.get('name')}': {len(chans)} channels | {t_min:.3f}s to {t_max:.3f}s | up to {n_keys} keys/channel")
    for path, targets in by_path.items():
        print(f"    {path}: {len(targets)} -> {sorted(set(targets))}")

imgs = gltf.get("images", [])
print()
print("images:", [(i.get("name"), i.get("mimeType")) for i in imgs])
bv = gltf.get("bufferViews", [])
for i in imgs:
    if "bufferView" in i:
        print("  image", i.get("name"), f"{bv[i['bufferView']]['byteLength']/1e6:.1f} MB")

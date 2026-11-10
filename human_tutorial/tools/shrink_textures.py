"""shrink_textures.py - Step 18: shrink the model's textures for the web, measure what it costs, and apply a chosen set.

Run inside Blender:
    G = {"ACTION": "report"}                                  # build candidate sets and print a table (changes nothing in the material)
    exec(open(".../shrink_textures.py").read(), G)
    G = {"ACTION": "apply", "SET": "web"}                     # relink the material to a set (the set is built if needed)
Sets are defined in SETS below; add your own. The material's four textures are found from the node graph, not by name:
    base      -> Base Color         (sRGB; the detail lives here)
    normal    -> Normal Map         (data; renormalized after shrinking)
    orm       -> Separate Color     (data; green = roughness, blue = metallic, red unused)
    emission  -> Emission Color     (sRGB; a grey glow layer in the source file)
The ORIGINAL images are kept on a fake user, renamed orig_<role>, so this is reversible and can be re-run at any size.
Shrinking is an area average (every output pixel is the mean of the block of source pixels it replaces).
"""
import bpy, numpy as np, os, tempfile

ACTION, SET = globals().get("ACTION", "report"), globals().get("SET", "web")
# role: (size, format, quality). The sizes are the SIDE of a square texture. emission None = leave the glow layer out.
SETS = {
    "original": None,
    # the recommended set puts the resolution where the detail is: the base colour (faces, veins) at 2048; the normal map (almost flat) at 1024
    "max":    {"base": (2048, "JPEG", 90), "normal": (2048, "PNG", 0), "orm": (1024, "JPEG", 90), "emission": (1024, "JPEG", 85)},
    "web":    {"base": (2048, "JPEG", 90), "normal": (1024, "PNG", 0), "orm": (512, "JPEG", 90),  "emission": (512, "JPEG", 85)},
    "small":  {"base": (1024, "JPEG", 90), "normal": (1024, "PNG", 0), "orm": (512, "JPEG", 90),  "emission": (512, "JPEG", 85)},
    "light":  {"base": (512, "JPEG", 85),  "normal": (512, "PNG", 0),  "orm": (256, "JPEG", 85),  "emission": (256, "JPEG", 80)},
}
mat = bpy.data.objects["Body"].data.materials[0]; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

def feeder(socket_name, via=None):
    """the Image Texture node that feeds a Principled input (directly, or through a Separate Color / Normal Map node)"""
    link = next((l for l in nt.links if l.to_node == bsdf and l.to_socket.name == socket_name), None)
    if link is None: return None
    node = link.from_node
    if node.type == 'TEX_IMAGE': return node
    inp = next(l for l in nt.links if l.to_node == node and l.to_socket.name in ("Color", "Image"))
    return inp.from_node

def roles():
    """the Image Texture node of each role. The emission node is found by its image's name if it has been unlinked (a previous 'drop')."""
    out = {"base": feeder("Base Color"), "normal": feeder("Normal"), "orm": feeder("Roughness"), "emission": feeder("Emission Color")}
    if out["emission"] is None:
        out["emission"] = next((n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image and n.image.name.startswith(("orig_emission", "emission_"))), None)
    return out

def originals():
    """the original images by role. On the FIRST run they are renamed orig_<role> and put on a fake user, so they survive and can be found again."""
    names = ("base", "normal", "orm", "emission")
    found = {r: bpy.data.images.get(f"orig_{r}") for r in names}
    if not any(found.values()):
        for role, node in roles().items():
            if node is not None: node.image.name = f"orig_{role}"; node.image.use_fake_user = True
        found = {r: bpy.data.images.get(f"orig_{r}") for r in names}
    return {r: im for r, im in found.items() if im}

def to_array(im):
    w, h = im.size; buf = np.empty(w * h * 4, dtype=np.float32); im.pixels.foreach_get(buf); return buf.reshape(h, w, 4)[:, :, :3]

def area_down(a, f, normal=False):
    if f == 1: return a
    h, w, c = a.shape
    if normal:                                                   # average the VECTORS, then restore their length
        v = a * 2 - 1; v = v.reshape(h // f, f, w // f, f, c).mean(axis=(1, 3)); v /= np.maximum(np.linalg.norm(v, axis=2, keepdims=True), 1e-6)
        return v * 0.5 + 0.5
    return a.reshape(h // f, f, w // f, f, c).mean(axis=(1, 3))

def encode(role, arr, name, fmt, quality):
    """write arr as a JPEG/PNG file with Blender, read it back and pack it. Returns (image, bytes on disk, the pixels as stored)"""
    h, w = arr.shape[:2]; rgba = np.ones((h, w, 4), np.float32); rgba[:, :, :3] = np.clip(arr, 0, 1)
    tmp = tempfile.mkdtemp(); path = os.path.join(tmp, f"{name}.{'jpg' if fmt == 'JPEG' else 'png'}")
    im = bpy.data.images.new("_enc", w, h, alpha=False, float_buffer=False); im.colorspace_settings.name = "sRGB" if role in ("base", "emission") else "Non-Color"
    im.pixels.foreach_set(rgba.ravel()); im.update(); im.filepath_raw = path; im.file_format = fmt
    im.save(quality=quality) if fmt == "JPEG" else im.save()
    size = os.path.getsize(path); bpy.data.images.remove(im)
    out = bpy.data.images.load(path); out.name = name; out.colorspace_settings.name = "sRGB" if role in ("base", "emission") else "Non-Color"; out.pack()
    stored = to_array(out); return out, size, stored

_CACHE = {}
def build(set_name):
    """the images of a set (built once): {role: (image, bytes, size)}"""
    if set_name in _CACHE: return _CACHE[set_name]
    spec, orig, out = SETS[set_name], originals(), {}
    for role, (size, fmt, q) in spec.items():
        if role not in orig: continue
        name = f"{role}_{size}" + ("" if fmt == "JPEG" else "p")
        old = bpy.data.images.get(name)
        if old is not None and old.packed_file is not None and old.size[0] == size and not globals().get("REBUILD"):   # already built in this session: reuse it
            old.use_fake_user = True; out[role] = (old, old.packed_file.size, size, float("nan")); continue
        if old is not None: bpy.data.images.remove(old)
        src = to_array(orig[role]); f = src.shape[0] // size
        small = area_down(src, f, normal=(role == "normal")); del src
        im, nbytes, stored = encode(role, small, name, fmt, q); im.use_fake_user = True
        out[role] = (im, nbytes, size, float(np.abs(stored - small).mean() * 255))
    _CACHE[set_name] = out; return out

def apply(set_name, emission="keep"):
    """relink the material to a set. 'original' restores the first images."""
    orig = originals(); nodes = roles()
    imgs = {r: orig[r] for r in orig} if set_name == "original" else {r: v[0] for r, v in build(set_name).items()}
    for role, node in nodes.items():
        if node is not None and role in imgs: node.image = imgs[role]
    # the emission layer: keep (linked) or drop (unlinked, black)
    for l in [l for l in nt.links if l.to_node == bsdf and l.to_socket.name == "Emission Color"]:
        if emission == "drop": nt.links.remove(l)
    if emission == "keep" and not any(l.to_node == bsdf and l.to_socket.name == "Emission Color" for l in nt.links):
        nt.links.new(nodes["emission"].outputs["Color"], bsdf.inputs["Emission Color"])
    if emission == "drop": bsdf.inputs["Emission Color"].default_value = (0, 0, 0, 1)

def gpu_mb(size): return size * size * 4 * 4 / 3 / 1e6               # RGBA8 with a full mip chain

if ACTION == "report":
    orig = originals()
    print("set      | role      | size  | file     | GPU memory | encoding loss")
    totals = {}
    for name in ("original", "max", "web", "small", "light"):
        files = gpu = 0.0
        if name == "original":
            for role, im in orig.items():
                nb = im.packed_file.size if im.packed_file else 0; s = im.size[0]; files += nb; gpu += gpu_mb(s)
                print(f"original | {role:9s} | {s:5d} | {nb/1e6:5.2f} MB | {gpu_mb(s):6.1f} MB  | -")
        else:
            for role, (im, nb, s, loss) in build(name).items():
                files += nb; gpu += gpu_mb(s)
                print(f"{name:8s} | {role:9s} | {s:5d} | {nb/1e6:5.2f} MB | {gpu_mb(s):6.1f} MB  | {loss:.2f}/255")
        totals[name] = (files, gpu); print(f"{name:8s} | TOTAL     |       | {files/1e6:5.2f} MB | {gpu:6.1f} MB")
        print("-" * 64)
elif ACTION == "apply":
    apply(SET, emission=globals().get("EMISSION", "keep")); print("applied", SET, "| emission", globals().get("EMISSION", "keep"))

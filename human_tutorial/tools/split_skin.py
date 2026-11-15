"""split_skin.py - give the SKIN its own material, so an app can change the skin tone at runtime (set the material's base colour) and leave the clothes, hair and eyes alone.

Run in Blender with the finished model:   exec(open(".../split_skin.py").read(), {})        (safe to re-run)

  1. Every face is classified from the colour of the base texture at the middle of the face: SKIN if its hue is orange (< 0.11), its saturation is 0.25 to 0.75 and it is not dark (value > 0.35).
     That puts the face, neck, arms, hands and legs on one side and the hair, shirt, shorts, shoes and the eyes (a couple of faces each) on the other: look at the result before you trust it.
  2. Two materials: "Skin" and "ClothesHairEyes" (the original material, renamed). Body face -> its material by that classification.
  3. "Skin" is the original material with one change: its base colour is a GREY texture times a colour. The grey texture is the original texture's brightness (the shading, the veins) scaled so its
     brightest values are 1.0; the colour (the node "SkinTone") is the tone. Multiplying them gives back the original skin. An app changes the tone by setting the material's base colour
     (glTF baseColorFactor; Babylon.js PBRMaterial.albedoColor): a darker or lighter colour gives a darker or lighter skin, keeping the detail.
The normal, roughness and emission textures are shared by both materials.
"""
import bpy, numpy as np, colorsys, os, tempfile

body = bpy.data.objects["Body"]; me = body.data
orig = bpy.data.materials.get("ClothesHairEyes") or bpy.data.materials.get("Material_0") or me.materials[0]
orig.name = "ClothesHairEyes"
nt = orig.node_tree
base_img = next(n.image for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image and n.image.name.startswith(("base", "orig_base")))
w, h = base_img.size; px = np.empty(w * h * 4, np.float32); base_img.pixels.foreach_get(px); px = px.reshape(h, w, 4)[:, :, :3]
uv = me.uv_layers.active.data

# ---- 1. classify the faces: sample the texture at 7 points of each face; a sample looks like skin if its hue is orange, its saturation medium and it is not dark.
# A face on the edge of the skin 
BARY = [(1/3, 1/3, 1/3), (0.5, 0.5, 0.0), (0.0, 0.5, 0.5), (0.5, 0.0, 0.5), (0.8, 0.1, 0.1), (0.1, 0.8, 0.1), (0.1, 0.1, 0.8)]
def sample(x, y): return px[int(np.clip(y, 0, 0.9999) * h), int(np.clip(x, 0, 0.9999) * w)]
face_pts = []                                                          # [face][sample] -> colour (sRGB image values)
for p in me.polygons:
    t = [uv[i].uv for i in list(p.loop_indices)[:3]]
    face_pts.append([sample(*(b0 * t[0] + b1 * t[1] + b2 * t[2])) for b0, b1, b2 in BARY])
face_pts = np.array(face_pts)                                          # (faces, 7, 3)
hsv = np.array([[colorsys.rgb_to_hsv(*c) for c in f] for f in face_pts])
looks_skin = (hsv[:, :, 0] < 0.11) & (hsv[:, :, 1] > 0.25) & (hsv[:, :, 1] < 0.75) & (hsv[:, :, 2] > 0.35)
# the EYES: a face with three or more samples (of seven) that are eye white (bright, grey) or iris (blue/green) near the head belongs to the clothes/hair/eyes material whatever else it covers
eye_like = ((hsv[:, :, 1] < 0.2) & (hsv[:, :, 2] > 0.6)) | ((hsv[:, :, 0] > 0.3) & (hsv[:, :, 0] < 0.75) & (hsv[:, :, 1] > 0.15))
face_z = np.array([np.mean([me.vertices[v].co.z for v in p.vertices]) for p in me.polygons])
eyes = (eye_like.sum(axis=1) >= 3) & (face_z > 1.6)
# every other face with at least 30% skin samples is SKIN: a face on the edge (the hairline, the rim of a sleeve) must tint with the skin, or it shows as a light patch against a dark skin
skin = (looks_skin.mean(axis=1) >= 0.30) & ~eyes
print("eye faces", int(eyes.sum()))
def to_linear(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def to_srgb(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055)
C_lin = to_linear(face_pts[skin][looks_skin[skin]]).mean(axis=0)       # the average skin colour, in LINEAR light (the space colours are multiplied in)
print(f"skin faces {int(skin.sum())} of {len(skin)}; average skin colour: linear {np.round(C_lin, 3)}, as sRGB {np.round(to_srgb(C_lin), 3)}")

# ---- 2. the grey skin texture, made in linear light: brightness of the original / the brightness of the average skin, scaled so the tone colour stays within 0..1; stored as sRGB
luma = lambda a: 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
scale = float(C_lin.max()) * 1.4                                      # the tone colour is C_lin / scale (at most 1/1.4) and the grey texture may reach 1.0 for skin up to 1.4x brighter than average
grey_lin = np.clip(scale * luma(to_linear(px)) / luma(C_lin), 0.0, 1.0)
grey = to_srgb(grey_lin)
rgba = np.ones((h, w, 4), np.float32); rgba[:, :, 0] = rgba[:, :, 1] = rgba[:, :, 2] = grey
tmp = tempfile.mkdtemp(); path = os.path.join(tmp, "skin_grey.jpg")
old = bpy.data.images.get("skin_grey")
if old: bpy.data.images.remove(old)
im = bpy.data.images.new("_sg", w, h, alpha=False, float_buffer=False); im.colorspace_settings.name = "sRGB"
im.pixels.foreach_set(rgba.ravel()); im.update(); im.filepath_raw = path; im.file_format = 'JPEG'; im.save(quality=90)
bpy.data.images.remove(im)
grey_img = bpy.data.images.load(path); grey_img.name = "skin_grey"; grey_img.colorspace_settings.name = "sRGB"; grey_img.pack(); grey_img.use_fake_user = True
print("skin_grey texture", os.path.getsize(path) // 1000, "KB on disk")

# ---- 3. the Skin material: the original, with the base colour = grey texture x SkinTone
skin_mat = bpy.data.materials.get("Skin")
if skin_mat: bpy.data.materials.remove(skin_mat)
skin_mat = orig.copy(); skin_mat.name = "Skin"; snt = skin_mat.node_tree
bsdf = next(n for n in snt.nodes if n.type == 'BSDF_PRINCIPLED')
link = next(l for l in snt.links if l.to_node == bsdf and l.to_socket.name == "Base Color"); tex = link.from_node
tex.image = grey_img
mix = snt.nodes.new("ShaderNodeMix"); mix.name = mix.label = "SkinTone"; mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs["Factor"].default_value = 1.0
mix.location = (tex.location.x + 300, tex.location.y)
snt.links.remove(link)
snt.links.new(tex.outputs["Color"], mix.inputs["A"]); snt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
tone = C_lin / scale; mix.inputs["B"].default_value = (float(tone[0]), float(tone[1]), float(tone[2]), 1.0)
print("SkinTone (the default colour, linear):", np.round(tone, 3), "= sRGB", np.round(to_srgb(tone), 3))

# ---- 4. assign
me.materials.clear(); me.materials.append(skin_mat); me.materials.append(orig)
for p, s in zip(me.polygons, skin): p.material_index = 0 if s else 1
skin_mat.use_backface_culling = orig.use_backface_culling
print("Body materials:", [m.name for m in me.materials], "| faces:", int(skin.sum()), "skin,", int((~skin).sum()), "other")

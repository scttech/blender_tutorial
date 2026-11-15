# Changing the skin tone in the app

The body has **two materials**, so the app can recolour the skin without touching the clothes, hair or eyes:

| Material | Covers | Base colour |
|---|---|---|
| `Skin` | the face, neck, arms, hands and legs (8,713 faces) | a **grey** texture (`skin_grey`, 2048, 480 KB) **times** `baseColorFactor` |
| `ClothesHairEyes` | the shirt, shorts, shoes, hair, the eyes (23 faces) and a few faces on the edges | the original painted texture (`base_2048`) |

The normal, roughness and emission textures are shared by both. Make a different tone by setting the **Skin** material's base colour; the shading, veins and freckles stay, because they are in the grey texture.

## In Babylon.js

```js
const skin = scene.getMaterialByName("Skin");
skin.albedoColor = new BABYLON.Color3(0.440, 0.173, 0.075);      // the tan below: the numbers in the last column
```

Babylon's `albedoColor` holds the **linear** numbers (the same as the GLB's `baseColorFactor`: after loading, `Skin` shows 0.714, 0.358, 0.228, the "Original" row). So set it from the **last column**, not from a hex colour. If you only have an sRGB colour for the skin you want, convert it to linear and divide by 0.938 (below): `BABYLON.Color3.FromHexString("#c68662").toLinearSpace()` gives the linear colour, then divide each channel by 0.938 and cap at 1.

| Tone | Average skin colour you get (sRGB) | `albedoColor` / `baseColorFactor` (linear) |
|---|---|---|
| Original | 214, 157, 128 (`#d69d80`) | 0.717, 0.359, 0.230 |
| Light | 241, 194, 167 (`#f1c2a7`) | 0.938, 0.575, 0.412 |
| Fair | 224, 172, 140 (`#e0ac8c`) | 0.795, 0.440, 0.280 |
| Medium | 198, 134, 98 (`#c68662`) | 0.602, 0.254, 0.130 |
| Tan | 172, 112, 75 (`#ac704b`) | 0.440, 0.173, 0.075 |
| Brown | 128, 80, 52 (`#805034`) | 0.230, 0.086, 0.037 |
| Dark | 86, 52, 36 (`#563424`) | 0.099, 0.037, 0.019 |

The same list is in [`exports/skin_tones.json`](exports/skin_tones.json) (with an sRGB swatch colour for each, for a menu), and `viewer/index.html` has a skin menu that uses it (not tried in a real browser: see Step 19). `tools/verify_skin.js` loads the GLB in Node and checks that setting `Skin` leaves `ClothesHairEyes` untouched.

## Why the numbers differ from the colour you want

The grey texture is scaled so its brightest skin is 1.0, which makes the *average* skin pixel 0.938 (linear). The colour you set is multiplied by that, so the colour to set is the wanted colour divided by 0.938 (in linear light). To make your own tone from an average skin colour `S` (linear): `albedoColor = S / 0.938`, capped at 1.

## What is imperfect

* **Eyes.** The eyes are painted on the face, not separate geometry. 23 faces are the eyes, so the eyes keep their colour, but those faces also include a few pixels of eyelid skin: next to the eyes and brows you may see a few small triangles in the **original** skin colour, which shows against a very dark tone.
* **Lips and eyebrows** are part of the skin texture, so they take the skin tone (the grey texture has no colour, so the lips lose their redness).
* **Hairline and sleeve edges** are decided face by face: a face with at least 30% skin is skin, so a few hair pixels at the roots take the tone.

How the faces are chosen, and the texture made, is in [`tools/split_skin.py`](tools/split_skin.py) (safe to re-run; the checks in it print the face counts and the default tone).

[Contents](README.md)

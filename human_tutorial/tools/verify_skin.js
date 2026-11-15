// verify_skin.js - Step 20 follow-up: load the GLB in Babylon.js (NullEngine) and check the two body materials and that setting the Skin material's albedoColor leaves ClothesHairEyes alone.
// NODE_PATH=<dir with babylonjs and babylonjs-loaders>/node_modules node verify_skin.js human_all_animations.glb
const BABYLON = require("babylonjs"); require("babylonjs-loaders"); const fs = require("fs");
(async () => {
  const engine = new BABYLON.NullEngine(); const scene = new BABYLON.Scene(engine);
  const data = fs.readFileSync(process.argv[2]);
  await BABYLON.SceneLoader.ImportMeshAsync("", "", "data:application/octet-stream;base64," + data.toString("base64"), scene, null, ".glb");
  console.log("materials:", scene.materials.map(m => m.name).join(", "));
  const skin = scene.getMaterialByName("Skin"), other = scene.getMaterialByName("ClothesHairEyes");
  console.log("Skin albedoTexture:", skin.albedoTexture && skin.albedoTexture.name, "| default albedoColor (the linear numbers, shown as 0..255):", skin.albedoColor.toHexString(), "| ClothesHairEyes albedoColor:", other.albedoColor.toHexString());
  skin.albedoColor = new BABYLON.Color3(0.099, 0.037, 0.019);
  console.log("after setting the Dark tone (0.099, 0.037, 0.019): Skin", skin.albedoColor.toHexString(), "| ClothesHairEyes untouched", other.albedoColor.toHexString(), "| same material object on both? ", skin === other);
  process.exit(0);
})();

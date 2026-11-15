// verify_babylon.js - Step 19: load the GLB in Babylon.js (NullEngine, no browser), play every animation at three frames and compare the skinned vertices with Blender.
// npm install babylonjs@7.54.3 babylonjs-loaders@7.54.3 (in a fresh directory), then: NODE_PATH=<that dir>/node_modules node verify_babylon.js human_all_animations.glb /tmp/glb_reference.json
// Babylon animation groups run at 60 frames per second: frame = glTF seconds x 60.
const BABYLON = require("babylonjs"); require("babylonjs-loaders");
const fs = require("fs");
const ref = JSON.parse(fs.readFileSync(process.argv[3]));
(async () => {
  const engine = new BABYLON.NullEngine(); const scene = new BABYLON.Scene(engine); new BABYLON.FreeCamera("c", new BABYLON.Vector3(0,0,-5), scene);
  BABYLON.SceneLoader.OnPluginActivatedObservable.add(p => { if (p.name === "gltf") p.coordinateSystemMode = 1; });
  const data = fs.readFileSync(process.argv[2]);
  const res = await BABYLON.SceneLoader.ImportMeshAsync("", "", "data:application/octet-stream;base64," + data.toString("base64"), scene, null, ".glb");
  console.log("meshes", res.meshes.length, "skeletons", res.skeletons.length, "bones", res.skeletons[0].bones.length, "animationGroups", res.animationGroups.map(a=>`${a.name}[${a.from.toFixed(3)}..${a.to.toFixed(3)}]`).join(" "));
  const bodies = res.meshes.filter(m => m.skeleton && m.getTotalVertices() > 500);        // the body has one mesh per material (Skin, ClothesHairEyes), in glTF primitive order
  const body = bodies[0];
  console.log("body meshes", bodies.length, "verts", bodies.map(b => b.getTotalVertices()).join("+"), "culling/doubleSided:", body.material && body.material.backFaceCulling, "textures:", body.material.getActiveTextures().length);
  for (const g of res.animationGroups) g.stop();
  const FPS = 30;
  for (const g of res.animationGroups) {
    const name = g.name; let worst = 0;
    for (const fs_ of Object.keys(ref[name])) {
      const f = +fs_, t = f / FPS;                       // glTF times are frame/fps
      g.start(false, 1.0, g.from, g.to); g.goToFrame(t * 60); 
      scene.render();
      body.skeleton.prepare(true);
      let w = 0, off = 0; const R = ref[name][fs_];
      for (const b of bodies) {
        const p = b.getPositionData(true, true), n = p.length / 3;
        for (let i = 0; i < n; i++) { const r = R[off + i]; w = Math.max(w, Math.hypot(p[3*i]-r[0], p[3*i+1]-r[1], p[3*i+2]-r[2])); }
        off += n;
      }
      worst = Math.max(worst, w);
      g.stop();
    }
    console.log(name.padEnd(10), "worst vertex error vs Blender", (worst*1000).toFixed(3), "mm");
  }
  // other prop positions at last frame of Kbswing
  process.exit(0);
})().catch(e => { console.error("ERR", e); process.exit(1); });

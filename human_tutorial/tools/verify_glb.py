"""verify_glb.py - Step 19: read the exported GLB WITHOUT Blender importing it, skin the body frame by frame the way a game engine does,
and compare every vertex with what Blender shows. Also compares the prop meshes. Run inside Blender (needs numpy): exec(open(...).read(), {}).
glTF times are frame/fps (the first frame is at 1/30 s). Writes /tmp/glb_reference.json (vertex positions at first/middle/last frame) for verify_babylon.js."""
import bpy, json, struct, numpy as np, math
from mathutils import Matrix, kdtree
P = globals().get("GLB", "/Users/chris/blender_tutorial/human_tutorial/exports/human_all_animations.glb")
raw = open(P, "rb").read(); jl, _ = struct.unpack("<I4s", raw[12:20]); g = json.loads(raw[20:20+jl]); off = 20+jl; bl, _ = struct.unpack("<I4s", raw[off:off+8]); BIN = raw[off+8:off+8+bl]
CT = {5120:np.int8,5121:np.uint8,5122:np.int16,5123:np.uint16,5125:np.uint32,5126:np.float32}; NC = {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}
def acc(i):
    a = g["accessors"][i]; bv = g["bufferViews"][a["bufferView"]]; n = NC[a["type"]]; dt = np.dtype(CT[a["componentType"]])
    stride = bv.get("byteStride", n*dt.itemsize); o = bv.get("byteOffset",0)+a.get("byteOffset",0)
    if stride == n*dt.itemsize: arr = np.frombuffer(BIN, dt, a["count"]*n, o).reshape(a["count"], n)
    else: arr = np.stack([np.frombuffer(BIN, dt, n, o+k*stride) for k in range(a["count"])])
    if a.get("normalized"): arr = arr/np.iinfo(dt).max if dt.kind=="u" else np.maximum(arr/np.iinfo(dt).max,-1)
    return arr.astype(np.float64)
nodes = g["nodes"]; parent = {}
for i,n in enumerate(nodes):
    for c in n.get("children",[]): parent[c]=i
def qmat(q):
    x,y,z,w = q; return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def trs(t,q,s):
    M = np.eye(4); M[:3,:3] = qmat(q)*np.array(s); M[:3,3] = t; return M
def rest(i):
    n = nodes[i]
    if "matrix" in n: return np.array(n["matrix"]).reshape(4,4).T
    return trs(n.get("translation",[0,0,0]), n.get("rotation",[0,0,0,1]), n.get("scale",[1,1,1]))
def slerp(a,b,t):
    d = np.dot(a,b)
    if d<0: b=-b; d=-d
    if d>0.9995: r=a+t*(b-a); return r/np.linalg.norm(r)
    th=math.acos(d); return (math.sin((1-t)*th)*a+math.sin(t*th)*b)/math.sin(th)
def sample(ch, t):
    times, vals, interp = ch
    if t<=times[0]: return vals[0]
    if t>=times[-1]: return vals[-1]
    k = np.searchsorted(times,t,side="right")-1; u=(t-times[k])/(times[k+1]-times[k])
    if interp=="STEP": return vals[k]
    if vals.shape[1]==4: return slerp(vals[k],vals[k+1],u)
    return vals[k]*(1-u)+vals[k+1]*u
anims = {}
for a in g["animations"]:
    d = {}
    for c in a["channels"]:
        s = a["samplers"][c["sampler"]]; d.setdefault(c["target"]["node"],{})[c["target"]["path"]] = (acc(s["input"])[:,0], acc(s["output"]), s.get("interpolation","LINEAR"))
    anims[a["name"]] = d
def local(i, an, t):
    n = nodes[i]; tr = n.get("translation",[0,0,0]); q = n.get("rotation",[0,0,0,1]); sc = n.get("scale",[1,1,1])
    ch = anims[an].get(i,{}) if an else {}
    if "translation" in ch: tr = sample(ch["translation"],t)
    if "rotation" in ch: q = sample(ch["rotation"],t)
    if "scale" in ch: sc = sample(ch["scale"],t)
    return trs(tr,q,sc)
def world(i, an, t):
    M = local(i,an,t); p = parent.get(i)
    return (world(p,an,t) if p is not None else np.eye(4)) @ M
# body mesh
body = bpy.data.objects["Body"]; rig = bpy.data.objects["Rig"]
mesh_node = next(i for i,n in enumerate(nodes) if "skin" in n and "mesh" in n)
skin = g["skins"][nodes[mesh_node]["skin"]]; joints = skin["joints"]; ibm = acc(skin["inverseBindMatrices"]).reshape(-1,4,4).transpose(0,2,1)
prim = g["meshes"][nodes[mesh_node]["mesh"]]["primitives"]
POS = np.concatenate([acc(p["attributes"]["POSITION"]) for p in prim]); J = np.concatenate([acc(p["attributes"]["JOINTS_0"]) for p in prim]).astype(int); W = np.concatenate([acc(p["attributes"]["WEIGHTS_0"]) for p in prim])
print("exported verts", len(POS), "blender verts", len(body.data.vertices))
C = Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))   # blender -> gltf
Cn = np.array(C)
# map exported verts -> blender verts via rest positions
kd = kdtree.KDTree(len(body.data.vertices))
dg = bpy.context.evaluated_depsgraph_get()
if rig.animation_data: rig.animation_data.action = None
bpy.context.scene.frame_set(1); dg.update()
bw = body.matrix_world
for v in body.data.vertices: kd.insert(bw @ v.co, v.index)
kd.balance()
Binv = Cn[:3,:3].T
idx = []; maxd = 0
for p in POS:
    co = Binv @ p; _, vi, d = kd.find((co[0],co[1],co[2])); idx.append(vi); maxd = max(maxd,d)
idx = np.array(idx); print("rest-vertex mapping max distance (mm):", round(maxd*1000,4))
def skinned(an, t):
    mats = np.stack([world(j,an,t) @ ibm[k] for k,j in enumerate(joints)])
    M = (W[:,:,None,None]*mats[J]).sum(1)
    P4 = np.concatenate([POS,np.ones((len(POS),1))],1)
    return np.einsum("nij,nj->ni",M,P4)[:,:3]
props = {n:next(i for i,nd in enumerate(nodes) if nd.get("name")==n and "mesh" in nd) for n in ("Kettlebell","Mace","PullupBar")}
res = {}; REF = {}
for act in sorted(bpy.data.actions, key=lambda a:a.name):
    an = act.name; f0,f1 = act.frame_range; rig.animation_data_create(); rig.animation_data.action = act
    fr = sorted(set([int(f0), int(f1)] + list(np.linspace(f0,f1,9).round().astype(int))))
    worst = 0; wp = 0; wf = None
    for f in fr:
        bpy.context.scene.frame_set(int(f)); dg = bpy.context.evaluated_depsgraph_get(); ev = body.evaluated_get(dg); me = ev.to_mesh()
        arr = np.empty(len(me.vertices)*3); me.vertices.foreach_get("co", arr); arr = arr.reshape(-1,3)
        wm = np.array(body.matrix_world); wpos = (arr@wm[:3,:3].T+wm[:3,3])@Cn[:3,:3].T
        ev.to_mesh_clear()
        t = f/bpy.context.scene.render.fps
        REF.setdefault(an,{})[int(f)] = wpos[idx].round(6).tolist() if int(f) in (int(f0), int(round((f0+f1)/2)), int(f1)) else None
        sk = skinned(an,t); e = np.linalg.norm(sk - wpos[idx],axis=1); 
        if e.max()>worst: worst=e.max(); wf=f
        for n,i in props.items():
            ob = bpy.data.objects[n]; Mb = np.array(C @ ob.matrix_world)   # blender world -> gltf (rotation part conv. below)
            Mg = world(i,an,t); Mexp = Cn @ np.array(ob.matrix_world) @ np.linalg.inv(Cn)
            # compare a sample of the prop's own vertices
            me2 = ob.data; pts = np.array([list(v.co) for v in me2.vertices][:200])
            a_ = (Mg[:3,:3]@pts.T).T+Mg[:3,3]; b_ = (Mexp[:3,:3]@pts.T).T+Mexp[:3,3]
            wp = max(wp, np.linalg.norm(a_-b_,axis=1).max())
    res[an] = (worst*1000, wf, wp*1000, f0, f1)
    print(f"{an:10s} frames {int(f0)}-{int(f1)}  skin worst {worst*1000:.3f} mm (frame {wf})  props worst {wp*1000:.3f} mm  | gltf anim duration {max(max(c[0][-1] for c in d.values()) for d in [ {k:v for k,v in dd.items()} for dd in [ {nn:{p:v for p,v in ch.items()}[next(iter(ch))] for nn,ch in anims[an].items()} ] ]):.3f}s")
rig.animation_data.action = None
for pb in rig.pose.bones: pb.location=(0,0,0); pb.rotation_euler=(0,0,0)
bpy.context.scene.frame_set(1)

REF = {a:{f:v for f,v in d.items() if v} for a,d in REF.items()}
json.dump(REF, open('/tmp/glb_reference.json','w'))

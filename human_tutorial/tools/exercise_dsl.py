"""exercise_dsl.py - compile a text description of an exercise (TOML) into the keyframe table that anim_core.build_action() takes.

Plain Python, no Blender needed to compile (tomllib needs Python 3.11+; Blender 5 has it, the macOS system Python 3.9 does not: pass dicts there).

    compile_exercise(spec, library=None, generators=None) -> [(frame, pose), ...]
    load_exercise(path) -> spec                         reads a .toml file
    in Blender:  keys = compile_file(path, G)           G is the anim_core namespace; the file's `python = "x.py"` is run into it first

The file format (every part optional except `timeline`):

    name    = "Squat"
    extends = "Squat"           # start from another exercise in the library: its params, poses and timeline are inherited
    python  = "mace.py"         # a file (or a list of files) in tools/exercises/ run first, so `generator` below can use the functions it defines

    [params]                    # named numbers; the expressions below can use them
    depth = 0.58

    [poses.stand]               # a pose: bone -> {move | at | rot | wrot | props} (the table format of anim_core.py)
    Hips = { move = [0, 0, 0] }
    [poses.bottom]
    extends = "stand"           # inherit a pose (or a list of poses, layered in order); whatever this one says replaces the same bone's same entry
    Hips = { move = [0, "=sit_back", "=-depth"] }          # a string starting with "=" is an expression
    [poses.swing]
    generator = "mace_pose"     # a pose made by a Python function (for what a table cannot say: solving, rigid pivots)
    args = { gamma = "=60*cos(2*pi*(f-1)/30)" }
    post = [ { fn = "ride_arms", args = { style = "hips_fists" } } ]   # a function that reads the finished pose and adds to it (hands riding on the torso)

    timeline = [ [1, "stand"], [25, "bottom"], [33, "bottom"], [61, "stand"] ]
    # a key can override params:   { frame = 25, pose = "bottom", set = { depth = 0.5 } }
    # or be sampled:               { frames = [1, 31, 3], pose = "swing" }      # frame 1 to 31 inclusive, every 3rd; `f` is the frame in expressions

Expressions can use the params, `f` (the frame), pi and these functions: sin cos tan radians degrees sqrt atan2 abs min max.
A mistake (an unknown pose, a misspelt bone entry, an unknown name in an expression, frames that go backwards) is an error that names where it is.
"""
import ast, math, copy, os

CHANNELS = ("move", "at", "rot", "wrot", "props")
_FUNCS = {k: getattr(math, k) for k in ("sin", "cos", "tan", "radians", "degrees", "sqrt", "atan2")}; _FUNCS.update(abs=abs, min=min, max=max)
_OPS = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b, ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b, ast.Pow: lambda a, b: a ** b,
        ast.Mod: lambda a, b: a % b, ast.FloorDiv: lambda a, b: a // b}

class DSLError(ValueError): pass

def _eval(node, env, where):
    if isinstance(node, ast.Expression): return _eval(node.body, env, where)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool): return node.value
    if isinstance(node, ast.Name):
        if node.id in env: return env[node.id]
        if node.id == "pi": return math.pi
        raise DSLError(f"{where}: unknown name '{node.id}' (known: {', '.join(sorted(env))}, pi)")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        v = _eval(node.operand, env, where); return -v if isinstance(node.op, ast.USub) else v
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS: return _OPS[type(node.op)](_eval(node.left, env, where), _eval(node.right, env, where))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS and not node.keywords:
        return _FUNCS[node.func.id](*[_eval(a, env, where) for a in node.args])
    raise DSLError(f"{where}: this expression is not allowed ({ast.dump(node)[:60]})")

def evaluate(value, env, where):
    """replace every '=expression' string inside value (lists and tables too) by its number; lists become tuples"""
    if isinstance(value, str):
        if not value.startswith("="): return value
        try: tree = ast.parse(value[1:].strip(), mode="eval")
        except SyntaxError as e: raise DSLError(f"{where}: cannot read the expression '{value}' ({e.msg})")
        return _eval(tree, env, f"{where} {value}")
    if isinstance(value, (list, tuple)): return tuple(evaluate(v, env, where) for v in value)
    if isinstance(value, dict): return {k: evaluate(v, env, f"{where}.{k}") for k, v in value.items()}
    return value

def merge_pose(base, over):
    """bone by bone, entry by entry: what `over` says replaces the same entry of `base`; "props" merge slider by slider"""
    out = copy.deepcopy(base)
    for bone, entries in over.items():
        cur = out.setdefault(bone, {})
        for k, v in entries.items():
            if k == "props": cur.setdefault("props", {}).update(v)
            else: cur[k] = v
    return out

RESERVED = ("extends", "generator", "args", "post")
def merge_raw(parent, child):
    """a child exercise's pose over the same-named inherited pose. If the child says extends, generator, args or post, that WHOLE group of
    wiring replaces the parent's (so the child can swap what a pose is built from); the bones it lists merge over the parent's"""
    out = {k: copy.deepcopy(v) for k, v in parent.items()}
    if any(k in child for k in RESERVED):
        for k in RESERVED: out.pop(k, None)
    for k, v in child.items():
        if k in RESERVED: out[k] = copy.deepcopy(v)
    bones = merge_pose({k: v for k, v in out.items() if k not in RESERVED}, {k: v for k, v in child.items() if k not in RESERVED})
    return {**{k: v for k, v in out.items() if k in RESERVED}, **bones}

def _check_pose(pose, where):
    for bone, entries in pose.items():
        if not isinstance(entries, dict):
            hint = " (a top-level key written after a [table] heading belongs to that table: move it above the first heading)" if bone in ("timeline", "name", "python", "extends") else ""
            raise DSLError(f"{where}: '{bone}' must be a table such as {{ move = [0, 0, 0] }}{hint}")
        for k in entries:
            if k not in CHANNELS: raise DSLError(f"{where}: bone '{bone}' has an unknown entry '{k}' (allowed: {', '.join(CHANNELS)})")

def resolve_pose(name, poses, where, seen=()):
    """the pose `name` with its `extends` chain applied; returns (table pose, generator or None, generator args, post hooks).
    `extends` may be a list: the poses are layered in order, later ones replacing earlier ones entry by entry."""
    if name not in poses: raise DSLError(f"{where}: unknown pose '{name}' (known: {', '.join(sorted(poses))})")
    if name in seen: raise DSLError(f"{where}: pose '{name}' extends itself ({' -> '.join(seen + (name,))})")
    raw = poses[name]; parents = raw.get("extends", []); parents = [parents] if isinstance(parents, str) else list(parents)
    table, gen, args, post = {}, None, {}, []
    for parent in parents:
        t, g, a, p = resolve_pose(parent, poses, f"{where} (via '{name}')", seen + (name,))
        table = merge_pose(table, t); post = post + p
        if g is not None: gen, args = g, a
    if "generator" in raw: gen, args = raw["generator"], dict(raw.get("args", {}))
    elif "args" in raw: args = {**args, **raw["args"]}
    post = post + list(raw.get("post", []))
    own = {k: v for k, v in raw.items() if k not in ("extends", "generator", "args", "post")}
    _check_pose(own, f"pose '{name}'")
    return merge_pose(table, own), gen, args, post

def _inherit(spec, library, chain=()):
    """apply `extends` at the exercise level: params merge, poses merge by name, the timeline is replaced if the child has one"""
    parent = spec.get("extends")
    if parent is None: return spec
    if library is None or parent not in library: raise DSLError(f"extends '{parent}': no such exercise in the library")
    if parent in chain: raise DSLError(f"exercise '{parent}' extends itself")
    base = _inherit(library[parent], library, chain + (parent,))
    out = copy.deepcopy(base); out["name"] = spec.get("name", out.get("name"))
    out["params"] = {**base.get("params", {}), **spec.get("params", {})}
    poses = copy.deepcopy(base.get("poses", {}))
    for n, p in spec.get("poses", {}).items():
        poses[n] = merge_raw(poses[n], p) if n in poses else p
    out["poses"] = poses
    for k in ("timeline", "python"):
        if k in spec: out[k] = spec[k]
    return out

def compile_exercise(spec, library=None, generators=None):
    spec = _inherit(spec, library)
    unknown = set(spec) - {"name", "extends", "python", "params", "poses", "timeline"}
    if unknown: raise DSLError(f"unknown top-level entries: {', '.join(sorted(unknown))}")
    params, poses, timeline = spec.get("params", {}), spec.get("poses", {}), spec.get("timeline")
    if not timeline: raise DSLError("no timeline: list the (frame, pose) keys")
    keys = []
    for i, entry in enumerate(timeline):
        where = f"timeline[{i}]"
        if isinstance(entry, (list, tuple)):
            if len(entry) != 2: raise DSLError(f"{where}: expected [frame, \"pose\"]")
            entry = {"frame": entry[0], "pose": entry[1]}
        if "pose" not in entry: raise DSLError(f"{where}: no pose")
        if "frames" in entry:
            a, b, step = entry["frames"]; frames = list(range(a, b + 1, step))
        elif "frame" in entry: frames = [entry["frame"]]
        else: raise DSLError(f"{where}: needs frame or frames")
        for f in frames:
            env = {**params, **entry.get("set", {}), "f": f}
            env = {k: evaluate(v, env, f"{where} param {k}") for k, v in env.items()}
            table, gen, args, post = resolve_pose(entry["pose"], poses, where)
            if gen is not None:
                if generators is None or gen not in generators: raise DSLError(f"{where}: pose '{entry['pose']}' uses generator '{gen}', which is not available")
                made = generators[gen](**evaluate(args, env, f"{where} args"))
                _check_pose(made, f"generator '{gen}'"); table = merge_pose(made, table)
            table = evaluate(table, env, f"{where} pose '{entry['pose']}'")
            for h in post:             # post hooks read the finished pose (the body) and add to it: hands that ride on the torso, for example
                fn = h.get("fn")
                if generators is None or fn not in generators: raise DSLError(f"{where}: post hook '{fn}' is not available")
                extra = generators[fn](table, **evaluate(h.get("args", {}), env, f"{where} post {fn}"))
                _check_pose(extra, f"post hook '{fn}'"); table = merge_pose(table, evaluate(extra, env, f"post {fn}"))
            keys.append((f, table))
    for (a, _), (b, _) in zip(keys, keys[1:]):
        if b <= a: raise DSLError(f"timeline: frame {b} comes after frame {a}; frames must increase")
    return keys

# ------------------------------------------------------------------ files (Blender)
def load_exercise(path):
    import tomllib
    with open(path, "rb") as fh: return tomllib.load(fh)

def compile_file(path, G=None, library_dir=None):
    """compile a .toml exercise. G is the anim_core namespace (needed only for `python =` and generators). Exercises in the same folder can be extended by name."""
    folder = library_dir or os.path.dirname(os.path.abspath(path)); spec = load_exercise(path)
    library = {}
    for fn in os.listdir(folder):
        if fn.endswith(".toml"):
            s = load_exercise(os.path.join(folder, fn)); library[s.get("name", fn[:-5])] = s
    chain, s = [], spec
    while s.get("extends"): s = library[s["extends"]]; chain.append(s)
    if G is not None:
        for s in [spec] + chain:
            for py in ([s["python"]] if isinstance(s.get("python"), str) else s.get("python", [])):
                if not G.get("_loaded_" + py): exec(open(os.path.join(folder, py)).read(), G); G["_loaded_" + py] = True
    if G is not None and callable(G.get("reset_poselib")): G["reset_poselib"]()
    return compile_exercise(spec, library, G)

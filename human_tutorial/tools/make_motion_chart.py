"""make_motion_chart.py - draw an exercise's measurements as an SVG.

    python3 -I make_motion_chart.py data.json out.svg "Title" "key:Label[:scale[:band]]" "key:Label" "key:Label"

Each "key:Label" is one panel: the per-frame list `key` from the measurement file, multiplied by `scale` (default 1). A panel may
shade a band behind the line: add :band and the file must hold D["support"] = [low, high] (already in the panel's units).
Dotted lines mark the keyframes (D["keys"]). Up to four panels. No libraries needed.

    squat:   "hips_z:Hip height (m)" "knee_deg:Knee bend (degrees)" "com_y:Centre of mass, front to back (cm):100:band"
    push-up: "min_z_chest:Chest height above the floor (cm):100" "elbow_deg:Elbow bend (degrees)" "straight_deg:Body line bend (degrees)"
    sit-up:  "lean_deg:Spine angle from vertical (degrees)" "knee_deg:Knee bend (degrees)" "min_z_body:Lowest point of the body (mm):1000"
"""
import json, sys
src, out, title = sys.argv[1], sys.argv[2], sys.argv[3]
specs = [a.split(":") for a in sys.argv[4:]]
D = json.load(open(src)); F = D["frame"]; f0, f1 = F[0], F[-1]; keys = D.get("keys", [f0, f1])
W, L, R = 760, 78, 24; top, ph, gap = 48, 150, 34; H = top + len(specs) * (ph + gap) + 6
x = lambda f: L + (f - f0) / (f1 - f0) * (W - L - R)
s = []; a = s.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">')
a(f'<title id="t">{title}: measured motion</title>')
a(f'<desc id="d">{len(specs)} plots over {len(F)} frames: ' + "; ".join(sp[1] for sp in specs) + '. Dotted lines mark the keyframes.</desc>')
a('<style>text{font:12px sans-serif;fill:#222}.t{font:600 14px sans-serif}.g{stroke:#ccc;stroke-width:1}.k{stroke:#999;stroke-dasharray:3 3}.l{fill:none;stroke:#1f6feb;stroke-width:2.2}.b{fill:#d8e8ff}</style>')
a(f'<rect width="{W}" height="{H}" fill="#fff"/>')
a(f'<text class="t" x="{L}" y="26">{title}: {len(F)} frames at 30 fps</text>')
for i, sp in enumerate(specs):
    key, label = sp[0], sp[1]; scale = float(sp[2]) if len(sp) > 2 and sp[2] else 1.0; band = D["support"] if len(sp) > 3 and sp[3] == "band" else None
    vals = [v * scale for v in D[key]]; y0 = top + i * (ph + gap)
    lo, hi = min(vals), max(vals)
    if band: lo, hi = min(lo, band[0]), max(hi, band[1])
    pad = (hi - lo) * 0.08 or 1; lo -= pad; hi += pad
    Y = lambda v: y0 + ph - (v - lo) / (hi - lo) * ph
    a(f'<text class="t" x="{L}" y="{y0 - 8}">{label}</text>')
    a(f'<rect x="{L}" y="{y0}" width="{W - L - R}" height="{ph}" fill="none" class="g"/>')
    if band: a(f'<rect class="b" x="{L}" y="{Y(band[1])}" width="{W - L - R}" height="{Y(band[0]) - Y(band[1])}"/><text x="{L + 6}" y="{Y(band[1]) + 14}">base of support (the soles)</text>')
    for k in keys: a(f'<line class="k" x1="{x(k)}" x2="{x(k)}" y1="{y0}" y2="{y0 + ph}"/>')
    a('<polyline class="l" points="' + " ".join(f"{x(f):.1f},{Y(v):.1f}" for f, v in zip(F, vals)) + '"/>')
    for v in (lo + pad, hi - pad): a(f'<text x="{L - 6}" y="{Y(v) + 4}" text-anchor="end">{v:.2f}</text>')
for k in keys: a(f'<text x="{x(k)}" y="{H - 22}" text-anchor="middle">{k}</text>')
a(f'<text x="{(L + W - R) / 2}" y="{H - 6}" text-anchor="middle">frame</text></svg>')
open(out, "w").write("\n".join(s)); print("wrote", out)

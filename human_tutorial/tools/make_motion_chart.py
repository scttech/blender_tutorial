"""make_motion_chart.py - draw an exercise's measurements as an SVG:   python3 -I make_motion_chart.py squat_measure.json out.svg "Squat"

Three panels over the frames of the loop: hip height, knee bend, and the centre of mass against the feet (the shaded band is the
sole of the shoe, heel to toe). Dotted lines mark the keyframes. No libraries needed.
"""
import json, sys
src, out, title = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else "Motion")
D = json.load(open(src)); F = D["frame"]; f0, f1 = F[0], F[-1]
keys = D.get("keys", [f0, f1])
W, H = 760, 640; L, R = 78, 24
panels = [("Hip height (m)", D["hips_z"], 1.0, None), ("Knee bend (degrees)", D["knee_deg"], 1.0, None),
          ("Centre of mass, front to back (cm)", [y * 100 for y in D["com_y"]], 1.0, [s * 100 for s in D["support"]])]
top, ph, gap = 48, 150, 34
x = lambda f: L + (f - f0) / (f1 - f0) * (W - L - R)
s = []; a = s.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">')
a(f'<title id="t">{title}: measured motion</title>')
a(f'<desc id="d">Three plots over {len(F)} frames. Top: the hips lower and rise. Middle: the knee bends and straightens. Bottom: the centre of mass stays inside the shaded band under the foot.</desc>')
a('<style>text{font:12px sans-serif;fill:#222}.t{font:600 14px sans-serif}.g{stroke:#ccc;stroke-width:1}.k{stroke:#999;stroke-dasharray:3 3}.l{fill:none;stroke:#1f6feb;stroke-width:2.2}.b{fill:#d8e8ff}</style>')
a(f'<rect width="{W}" height="{H}" fill="#fff"/>')
a(f'<text class="t" x="{L}" y="26">{title}: {len(F)} frames at 30 fps</text>')
for i, (name, vals, _, band) in enumerate(panels):
    y0 = top + i * (ph + gap)
    lo, hi = min(vals), max(vals)
    if band: lo, hi = min(lo, band[0]), max(hi, band[1])
    pad = (hi - lo) * 0.08 or 1; lo -= pad; hi += pad
    Y = lambda v: y0 + ph - (v - lo) / (hi - lo) * ph
    a(f'<text class="t" x="{L}" y="{y0 - 8}">{name}</text>')
    a(f'<rect x="{L}" y="{y0}" width="{W - L - R}" height="{ph}" fill="none" class="g"/>')
    if band: a(f'<rect class="b" x="{L}" y="{Y(band[1])}" width="{W - L - R}" height="{Y(band[0]) - Y(band[1])}"/>'
               f'<text x="{L + 6}" y="{Y(band[1]) + 14}">sole of the shoe</text>')
    for k in keys: a(f'<line class="k" x1="{x(k)}" x2="{x(k)}" y1="{y0}" y2="{y0 + ph}"/>')
    pts = " ".join(f"{x(f):.1f},{Y(v):.1f}" for f, v in zip(F, vals))
    a(f'<polyline class="l" points="{pts}"/>')
    for v in (lo + pad, hi - pad):
        a(f'<text x="{L - 6}" y="{Y(v) + 4}" text-anchor="end">{v:.2f}</text>')
for k in keys: a(f'<text x="{x(k)}" y="{top + 3 * (ph + gap) - gap + 18}" text-anchor="middle">{k}</text>')
a(f'<text x="{(L + W - R) / 2}" y="{H - 8}" text-anchor="middle">frame</text></svg>')
open(out, "w").write("\n".join(s)); print("wrote", out)

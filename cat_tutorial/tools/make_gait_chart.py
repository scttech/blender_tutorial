import json, sys

src, out = sys.argv[1], sys.argv[2]
D = json.load(open(src))
frames = D["frames"]; n = len(frames)

W, H = 720, 520
L, R = 110, 30                      # plot area left / right margins
x0, x1 = L, W - R
def X(f): return x0 + (f - 0.5) / n * (x1 - x0)          # frame f occupies one slot
slot = (x1 - x0) / n

legs = [("RH", "Right hind", "s1"), ("RF", "Right front", "s2"), ("LH", "Left hind", "s3"), ("LF", "Left front", "s4")]

# contact = the measured toe tip is within 1 cm of that foot's lowest height
def contact(code):
    z = D["tipz"][code]; lo = min(z)
    return [(v - lo) < 0.01 for v in z]

svg = []
a = svg.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">')
a('<title id="t">Walk cycle: foot contact and body height</title>')
a('<desc id="d">Top: which feet are on the ground in each of the 30 frames of the walk, in the order right hind, right front, left hind, left front, each a quarter cycle apart. Bottom: the pelvis height over the same frames, moving up and down by about 3 cm twice per stride.</desc>')
a('''<style>
 svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
 :root{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--grid:#e4e3df;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100}
 @media (prefers-color-scheme:dark){:root{--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--grid:#34332f;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500}}
 .bg{fill:var(--surface)} .ink{fill:var(--ink)} .ink2{fill:var(--ink2)} .grid{stroke:var(--grid);stroke-width:1}
 .lbl{font-size:13px} .small{font-size:11.5px} .title{font-size:15px;font-weight:600}
 .s1{fill:var(--s1)} .s2{fill:var(--s2)} .s3{fill:var(--s3)} .s4{fill:var(--s4)}
 .line{fill:none;stroke:var(--s1);stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
 .dot{fill:var(--s1);stroke:var(--surface);stroke-width:2}
</style>''')
a(f'<rect class="bg" width="{W}" height="{H}"/>')

# ---------- panel A: gait diagram ----------
a(f'<text class="title ink" x="{L}" y="28">Which feet are on the ground</text>')
a(f'<text class="small ink2" x="{L}" y="46">Bar = foot planted. Gap = foot in the air. One stride, 30 frames.</text>')
top = 62; row = 34
for i, (code, name, cls) in enumerate(legs):
    y = top + i * row
    a(f'<text class="lbl ink" x="{L-12}" y="{y+17}" text-anchor="end">{name}</text>')
    a(f'<line class="grid" x1="{x0}" x2="{x1}" y1="{y+10}" y2="{y+10}" stroke-dasharray="2 4"/>')
    c = contact(code)
    # merge consecutive contact frames into one bar
    j = 0
    while j < n:
        if c[j]:
            k = j
            while k + 1 < n and c[k + 1]: k += 1
            xa = x0 + j * slot + 1; xb = x0 + (k + 1) * slot - 1
            a(f'<rect class="{cls}" x="{xa:.1f}" y="{y+3}" width="{xb-xa:.1f}" height="14" rx="4"><title>{name}: planted frames {j+1}-{k+1}</title></rect>')
            j = k + 1
        else:
            j += 1
gy = top + 4 * row
for f in (1, 6, 11, 16, 21, 26, 30):
    a(f'<text class="small ink2" x="{X(f):.1f}" y="{gy+4}" text-anchor="middle">{f}</text>')
a(f'<text class="small ink2" x="{(x0+x1)/2:.1f}" y="{gy+22}" text-anchor="middle">frame</text>')

# ---------- panel B: body height ----------
pz = [v * 100 for v in D["pelvis_z"]]
lo, hi = min(pz), max(pz)
by0, by1 = 292, 452                 # plot band for panel B
a(f'<text class="title ink" x="{L}" y="{by0-34}">Body height</text>')
a(f'<text class="small ink2" x="{L}" y="{by0-16}">Pelvis height over the same frames. The body dips twice per stride.</text>')
pad = 0.4
ymin, ymax = lo - pad, hi + pad
def Y(v): return by1 - (v - ymin) / (ymax - ymin) * (by1 - by0)
for v in (round(lo, 1), round((lo + hi) / 2, 1), round(hi, 1)):
    a(f'<line class="grid" x1="{x0}" x2="{x1}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/>')
    a(f'<text class="small ink2" x="{L-12}" y="{Y(v)+4:.1f}" text-anchor="end">{v:.1f} cm</text>')
pts = " ".join(f"{X(f):.1f},{Y(v):.1f}" for f, v in zip(frames, pz))
a(f'<polyline class="line" points="{pts}"/>')
imin = pz.index(lo); imax = pz.index(hi)
for idx, txt, dy in ((imax, "highest", -10), (imin, "lowest", 20)):
    a(f'<circle class="dot" cx="{X(frames[idx]):.1f}" cy="{Y(pz[idx]):.1f}" r="4.5"><title>frame {frames[idx]}: {pz[idx]:.1f} cm</title></circle>')
    a(f'<text class="small ink" x="{X(frames[idx]):.1f}" y="{Y(pz[idx])+dy:.1f}" text-anchor="middle">{txt} {pz[idx]:.1f} cm</text>')
for f in (1, 6, 11, 16, 21, 26, 30):
    a(f'<text class="small ink2" x="{X(f):.1f}" y="{by1+22}" text-anchor="middle">{f}</text>')
a(f'<text class="small ink2" x="{(x0+x1)/2:.1f}" y="{by1+42}" text-anchor="middle">frame</text>')
a(f'<text class="small ink2" x="{L}" y="{H-14}">Swing in the pelvis: {hi-lo:.1f} cm. Feet measured from the animated rig in Blender.</text>')
a('</svg>')
open(out, "w").write("\n".join(svg))
print("wrote", out, "| contact frames per leg:", {c: sum(contact(c)) for c, _, _ in legs}, "| pelvis swing %.1f cm" % (hi - lo))

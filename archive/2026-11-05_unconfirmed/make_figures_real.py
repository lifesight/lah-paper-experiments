"""Draw Figure 4 from cap_study_real_results.json as an SVG (no dependencies): on three recorded turns, honest
sums over the last read and fabricated six-figure amounts accepted, against the base cap. One panel per turn,
two series, colours from the validated reference palette (blue honest, orange fabricated)."""
import json
from pathlib import Path

here = Path(__file__).resolve().parent
d = json.load(open(here / "cap_study_real_results.json"))
turns = [("causal", "causal (plan, report)"), ("cmo", "cmo (model report, plan)"),
         ("promoted-plan", "promoted-plan (plan, report, plan)")]
caps = d["config"]["caps"]
W, H = 720, 300
PW = (W - 64 - 24 - 2 * 24) / 3
T, B = 40, 52
out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
       f'aria-label="Honest sums accepted and fabricated amounts accepted against the base cap, three recorded turns">',
       '<style>text{font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;font-size:11px;fill:#52514e}'
       '.t{font-size:12px;fill:#0b0b0b}.g{stroke:#e5e5e0;stroke-width:1}.ax{stroke:#c3c2b7;stroke-width:1}</style>',
       f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fcfcfb"/>']


def ypix(v: float) -> float:
    return T + (H - T - B) * (1 - v / 100.0)


for i, (key, label) in enumerate(turns):
    x0 = 64 + i * (PW + 24)
    cells = d["threads"][key]["cells"]
    xs = {c["cap"]: x0 + PW * j / (len(caps) - 1) for j, c in enumerate(cells)}
    for tick in (0, 25, 50, 75, 100):
        y = ypix(tick)
        out.append(f'<line class="g" x1="{x0}" y1="{y:.1f}" x2="{x0 + PW:.1f}" y2="{y:.1f}"/>')
        if i == 0:
            out.append(f'<text x="{x0 - 8}" y="{y + 4:.1f}" text-anchor="end">{tick}%</text>')
    out.append(f'<line class="ax" x1="{x0}" y1="{ypix(0):.1f}" x2="{x0 + PW:.1f}" y2="{ypix(0):.1f}"/>')
    for c in cells:
        out.append(f'<text x="{xs[c["cap"]]:.1f}" y="{H - B + 16}" text-anchor="middle">{c["cap"]:,}</text>')
    out.append(f'<text class="t" x="{x0 + PW / 2:.1f}" y="{T - 14}" text-anchor="middle">{label}</text>')
    for field, colour, name in (("honest_last", "#2a78d6", "honest sums, last read"),
                                ("fab_6fig", "#eb6834", "fabricated six-figure amounts")):
        pts = [(xs[c["cap"]], ypix(c[field])) for c in cells]
        path = " ".join(f"{'M' if j == 0 else 'L'}{x:.1f},{y:.1f}" for j, (x, y) in enumerate(pts))
        out.append(f'<path d="{path}" fill="none" stroke="{colour}" stroke-width="2" stroke-linejoin="round"/>')
        for (x, y), c in zip(pts, cells):
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{colour}" stroke="#fcfcfb" stroke-width="2"/>')
        last = cells[-1][field]
        out.append(f'<text x="{pts[-1][0] - 4:.1f}" y="{pts[-1][1] - 7:.1f}" text-anchor="end" fill="{colour}">{last:.0f}%</text>')
out.append(f'<text x="{W / 2:.0f}" y="{H - 8}" text-anchor="middle">base cap (production: 300)</text>')
out.append('<rect x="64" y="8" width="10" height="10" fill="#2a78d6"/><text x="80" y="17">honest sums over the last read accepted</text>')
out.append('<rect x="330" y="8" width="10" height="10" fill="#eb6834"/><text x="346" y="17">fabricated six-figure amounts accepted</text>')
out.append("</svg>")
(here / "figure_real_cap.svg").write_text("\n".join(out))
print("wrote figure_real_cap.svg")

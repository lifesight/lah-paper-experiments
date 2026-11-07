"""Draw the paper's data figure from provenance_study_results.json as an SVG (no dependencies).

Figure: false-accept rate of fabricated six-figure amounts against the number of tool results,
three arms, log-scaled y axis, 95% CI whiskers over seeds, direct labels plus a legend, colours from the validated
reference palette (first three categorical slots).
"""
import json
import math
from pathlib import Path

here = Path(__file__).resolve().parent
d = json.load(open(here / "provenance_study_results.json"))
arms = [("production_one_result", "Production: operands from one result", "#2a78d6"),
        ("pool_capped_300", "Pool, 300-base cap", "#eb6834"),
        ("pool_uncapped", "Pool, uncapped", "#1baf7a")]
sizes = d["config"]["sizes_results"]
W, H = 720, 400
L, R, T, B = 64, 24, 28, 60
xs = {k: L + (W - L - R) * i / (len(sizes) - 1) for i, k in enumerate(sizes)}
ymin, ymax = 0.03, 30.0
def ypix(v):
    v = max(v, ymin)
    return T + (H - T - B) * (1 - (math.log10(v) - math.log10(ymin)) / (math.log10(ymax) - math.log10(ymin)))
out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
       f'aria-label="False-accept rate of fabricated six-figure amounts against the number of tool results, three arms">',
       '<style>text{font-family:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;font-size:12px;fill:#52514e}'
       '.t{font-size:12px;fill:#0b0b0b}.g{stroke:#e5e5e0;stroke-width:1}.ax{stroke:#c3c2b7;stroke-width:1}</style>',
       f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fcfcfb"/>']
for tick in (0.05, 0.1, 0.5, 1, 5, 10, 20):
    y = ypix(tick)
    out.append(f'<line class="g" x1="{L}" y1="{y:.1f}" x2="{W-R}" y2="{y:.1f}"/>')
    out.append(f'<text x="{L-8}" y="{y+4:.1f}" text-anchor="end">{tick:g}%</text>')
out.append(f'<line class="ax" x1="{L}" y1="{H-B}" x2="{W-R}" y2="{H-B}"/>')
for k in sizes:
    bases = next(r for r in d["e1_e4"]["production_one_result"] if r["results"] == k)["bases"]["mean"]
    ub = next(r for r in d["e1_e4"]["pool_uncapped"] if r["results"] == k)["bases"]["mean"]
    out.append(f'<text x="{xs[k]:.1f}" y="{H-B+18}" text-anchor="middle" class="t">{k}</text>')
    out.append(f'<text x="{xs[k]:.1f}" y="{H-B+34}" text-anchor="middle">{ub:.0f}</text>')
out.append(f'<text x="{(L+W-R)/2:.0f}" y="{H-6}" text-anchor="middle">tool results (top) and bases before the cap (bottom)</text>')
out.append(f'<text transform="translate(14,{(T+H-B)/2:.0f}) rotate(-90)" text-anchor="middle">fabricated amounts accepted (log scale)</text>')
for key, label, color in arms:
    rows = d["e1_e4"][key]
    pts = [(xs[r["results"]], ypix(r["e1_accept"]["mean"])) for r in rows]
    path = " ".join(f'{"M" if i == 0 else "L"}{x:.1f},{y:.1f}' for i, (x, y) in enumerate(pts))
    out.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>')
    for r, (x, y) in zip(rows, pts):
        m, c = r["e1_accept"]["mean"], r["e1_accept"]["ci95"]
        # 95% confidence interval over seeds as a whisker (the lower end is clipped at the axis floor)
        if c > 0:
            y_hi, y_lo = ypix(m + c), ypix(max(m - c, ymin))
            out.append(f'<line x1="{x:.1f}" y1="{y_hi:.1f}" x2="{x:.1f}" y2="{y_lo:.1f}" stroke="{color}" stroke-width="1.2"/>')
            out.append(f'<line x1="{x-3:.1f}" y1="{y_hi:.1f}" x2="{x+3:.1f}" y2="{y_hi:.1f}" stroke="{color}" stroke-width="1.2"/>')
            out.append(f'<line x1="{x-3:.1f}" y1="{y_lo:.1f}" x2="{x+3:.1f}" y2="{y_lo:.1f}" stroke="{color}" stroke-width="1.2"/>')
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}" stroke="#fcfcfb" stroke-width="2">'
                   f'<title>{label}: {m:.2f}% ± {c:.2f} at {r["results"]} results</title></circle>')
    lx, ly = pts[-1]
    out.append(f'<text x="{lx-6:.1f}" y="{ly-10:.1f}" text-anchor="end" class="t">{rows[-1]["e1_accept"]["mean"]:.2f}%</text>')
# legend
ly0 = T + 4
for i, (key, label, color) in enumerate(arms):
    y = ly0 + i * 18
    out.append(f'<line x1="{L+12}" y1="{y}" x2="{L+36}" y2="{y}" stroke="{color}" stroke-width="2"/>')
    out.append(f'<circle cx="{L+24}" cy="{y}" r="3.5" fill="{color}"/>')
    out.append(f'<text x="{L+44}" y="{y+4}" class="t">{label}</text>')
out.append("</svg>")
(here / "figure_e1_false_accept.svg").write_text("\n".join(out))
print("wrote", here / "figure_e1_false_accept.svg")

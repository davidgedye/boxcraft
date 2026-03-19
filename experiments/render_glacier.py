"""Render shelf vs glacier at n=20 and n=100 (balanced, non-shuffled)."""

import boxcraft as bc
from boxcraft._algorithms.shelf import ShelfOptions
from boxcraft._algorithms.glacier import GlacierOptions
from boxcraft.testing import UniformGenerator
from boxcraft import render_svg

cases = []
for n in (20, 100):
    gen = UniformGenerator(w_range=(10, 200), h_range=(10, 200), n=n, seed=42)
    boxes = gen.generate()
    for algo, opts in [
        ("shelf",   ShelfOptions(balanced=True, shuffled=False)),
        ("glacier", GlacierOptions(balanced=True, shuffled=False)),
    ]:
        packer = bc.Packer(
            algorithm=algo,
            aspect_ratio=1.0,
            gap_h=5,
            gap_v=5,
            seed=42,
            options=opts,
        )
        packer.add_many(boxes)
        result = packer.pack()
        cases.append((result, f"n={n}"))
        print(f"{algo:8s} n={n:4d}  coverage={result.coverage:.1%}  time={result.wall_time_ms:.1f}ms")

cell_w, cell_h = 540, 580
grid_w, grid_h = cell_w * 2, cell_h * 2

lines = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{grid_w}" height="{grid_h}">',
    f'  <rect width="100%" height="100%" fill="#0e0e1a"/>',
]

positions = [(0, 0), (cell_w, 0), (0, cell_h), (cell_w, cell_h)]
for (dx, dy), (result, subtitle) in zip(positions, cases):
    svg = render_svg(result, subtitle=subtitle, display_px=500)
    inner = svg.split("\n", 1)[1].rsplit("\n", 1)[0]
    lines.append(f'  <g transform="translate({dx},{dy})">')
    lines.append(f'    <svg width="{cell_w}" height="{cell_h}">')
    lines.append(inner)
    lines.append(f'    </svg>')
    lines.append(f'  </g>')

lines.append(f'  <line x1="{cell_w}" y1="0" x2="{cell_w}" y2="{grid_h}" stroke="#ffffff" stroke-width="1"/>')
lines.append(f'  <line x1="0" y1="{cell_h}" x2="{grid_w}" y2="{cell_h}" stroke="#ffffff" stroke-width="1"/>')
lines.append('</svg>')

out = "shelf_vs_glacier.svg"
with open(out, "w") as f:
    f.write("\n".join(lines))
print(f"\nSaved → {out}")

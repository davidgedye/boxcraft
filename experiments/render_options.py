"""Render balanced × justify combinations side by side."""

import boxcraft as bc
from boxcraft._algorithms.shelf import ShelfOptions
from boxcraft.testing import UniformGenerator
from boxcraft import render_svg

gen = UniformGenerator(w_range=(0.1, 1.0), h_range=(0.1, 1.0), n=100, seed=42)
boxes = gen.generate()

cases = [
    (False, "left"),
    (True,  "left"),
    (False, "center"),
    (True,  "center"),
]

svgs = []
for balanced, justify in cases:
    packer = bc.Packer(
        algorithm="shelf",
        aspect_ratio=1.0,
        gap_h=0.05,
        gap_v=0.05,
        seed=42,
        options=ShelfOptions(balanced=balanced, shuffled=True, justify=justify),
    )
    packer.add_many(boxes)
    result = packer.pack()
    bal = "T" if balanced else "F"
    subtitle = f"U[0.1,1]² bal={bal} just={justify}"
    svgs.append(render_svg(result, subtitle=subtitle, display_px=500))
    print(f"bal={balanced} just={justify}  coverage={result.coverage:.1%}  time={result.wall_time_ms:.1f}ms")

# 2×2 grid
cell_w = 540
cell_h = 580
grid_w = cell_w * 2
grid_h = cell_h * 2

lines = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{grid_w}" height="{grid_h}">',
    f'  <rect width="100%" height="100%" fill="#0e0e1a"/>',
]

positions = [(0, 0), (cell_w, 0), (0, cell_h), (cell_w, cell_h)]
for (dx, dy), svg in zip(positions, svgs):
    inner = svg.split("\n", 1)[1].rsplit("\n", 1)[0]
    lines.append(f'  <g transform="translate({dx},{dy})">')
    lines.append(f'    <svg width="{cell_w}" height="{cell_h}">')
    lines.append(inner)
    lines.append(f'    </svg>')
    lines.append(f'  </g>')

lines.append(f'  <line x1="{cell_w}" y1="0" x2="{cell_w}" y2="{grid_h}" stroke="#ffffff" stroke-width="1"/>')
lines.append(f'  <line x1="0" y1="{cell_h}" x2="{grid_w}" y2="{cell_h}" stroke="#ffffff" stroke-width="1"/>')
lines.append('</svg>')

out = "shelf_options.svg"
with open(out, "w") as f:
    f.write("\n".join(lines))
print(f"\nSaved → {out}")

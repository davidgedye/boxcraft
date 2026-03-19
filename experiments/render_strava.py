"""Render strava dataset packing side by side: shelf vs glacier."""

from __future__ import annotations

import json
from pathlib import Path

import boxcraft as bc
from boxcraft._algorithms.glacier import GlacierOptions
from boxcraft import render_svg

rects = json.loads(Path("datasets/2026-03.json").read_text())
boxes = [bc.Box(r["width"], r["height"], label=r["id"], data=r) for r in rects]

cases = []
for algo in ("shelf", "glacier"):
    opts = GlacierOptions(shuffled=True) if algo == "glacier" else None
    packer = bc.Packer(algorithm=algo, aspect_ratio=2/3, gap_h=0.001, gap_v=0.001, edge_gap=0.001, options=opts)
    packer.add_many(boxes)
    result = packer.pack()
    cases.append((result, algo))
    valley = sum(1 for p in result.placements if p.meta and p.meta.get("valley_fill"))
    print(f"{algo:8s}  coverage={result.coverage:.1%}  valley_fills={valley}")

CELL_W, CELL_H = 540, 580
SVG_W, SVG_H = CELL_W * 2, CELL_H

lines = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}">',
    f'  <rect width="100%" height="100%" fill="#0e0e1a"/>',
]

for col, (result, subtitle) in enumerate(cases):
    svg = render_svg(result, subtitle=subtitle, display_px=500)
    inner = svg.split("\n", 1)[1].rsplit("\n", 1)[0]
    dx = col * CELL_W
    lines += [
        f'  <g transform="translate({dx},0)">',
        f'    <svg width="{CELL_W}" height="{CELL_H}">',
        inner,
        f'    </svg>',
        f'  </g>',
    ]

lines.append(f'  <line x1="{CELL_W}" y1="0" x2="{CELL_W}" y2="{CELL_H}" stroke="#ffffff44" stroke-width="1"/>')
lines.append('</svg>')

out = "strava_2026_03.svg"
Path(out).write_text("\n".join(lines))
print(f"\nSaved → {out}")

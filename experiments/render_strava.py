"""Render GPS trails dataset packing side by side: shelf (infill=False) vs glacier (infill=True)."""

from __future__ import annotations

import json
import random
from pathlib import Path

import boxcraft as bc
from boxcraft import render_svg

rects = json.loads((Path(__file__).parent.parent / "datasets" / "gps_trails_bounding_boxes.json").read_text())
all_boxes = [bc.Box(r["width"], r["height"], data=r) for r in rects]

rng = random.Random(0)
boxes = rng.sample(all_boxes, 20)

cases = []
for infill in (False, True):
    result = bc.pack(boxes, infill=infill, aspect_ratio=2/3,
                     gap_h=0.001, gap_v=0.001, edge_gap=0.001, seed=0)
    label = "infill" if infill else "shelf"
    cases.append((result, label))
    print(f"{label:8s}  coverage={result.coverage:.1%}")

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

out = Path(__file__).parent / "render_strava_output.svg"
out.write_text("\n".join(lines))
print(f"\nSaved → {out}")

"""Demo image: ~150 GPS trail bounding boxes packed into a square."""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import boxcraft as bc

DATASET = Path(__file__).parent.parent / "datasets" / "gps_trails_bounding_boxes.json"
N = 250
SEED = 42
GAP = 0.003

rects = json.loads(DATASET.read_text())
all_boxes = [bc.Box(r["width"], r["height"]) for r in rects]

rng = random.Random(SEED)
boxes = rng.sample(all_boxes, N)

result = bc.pack(
    boxes,
    infill=True,
    aspect_ratio=1.0,
    gap_h=GAP,
    gap_v=GAP,
    edge_gap=GAP,
    seed=SEED,
)

print(f"n={N}  coverage={result.coverage:.1%}  "
      f"bbox={result.bounding_box[0]:.3f}×{result.bounding_box[1]:.3f}  "
      f"{result.wall_time_ms:.1f}ms")


def hsl(h: float, s: float = 0.60, l: float = 0.62) -> str:
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if   h < 60:  r, g, b = c, x, 0.0
    elif h < 120: r, g, b = x, c, 0.0
    elif h < 180: r, g, b = 0.0, c, x
    elif h < 240: r, g, b = 0.0, x, c
    elif h < 300: r, g, b = x, 0.0, c
    else:         r, g, b = c, 0.0, x
    return "#{:02x}{:02x}{:02x}".format(
        int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
    )


# Color by log aspect ratio: tall (portrait) → violet, square → green, wide → red
def box_color(w: float, h: float) -> str:
    log_r = math.log(w / h)           # negative=tall, 0=square, positive=wide
    clamp = max(-3.0, min(3.0, log_r))
    t = (clamp + 3.0) / 6.0           # 0=tall, 0.5=square, 1=wide
    hue = 280 - t * 260               # 280=violet → 20=red-orange
    return hsl(hue % 360)


DISPLAY = 800
PAD = 24
TITLE_H = 52
BG = "#0e0e1a"
PACK_BG = "#1c1c30"

bb_w, bb_h = result.bounding_box
scale = DISPLAY / max(bb_w, bb_h)

svg_w = bb_w * scale + 2 * PAD
svg_h = bb_h * scale + 2 * PAD + TITLE_H

lines = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w:.0f}" height="{svg_h:.0f}">',
    f'  <rect width="100%" height="100%" fill="{BG}"/>',
    # title
    f'  <text x="{svg_w/2:.1f}" y="20" text-anchor="middle" '
    f'font-family="monospace" font-size="15" font-weight="bold" fill="#ffffffdd">'
    f'boxcraft</text>',
    # subtitle
    f'  <text x="{svg_w/2:.1f}" y="38" text-anchor="middle" '
    f'font-family="monospace" font-size="11" fill="#ffffffaa">'
    f'{N} GPS trail bounding boxes  ·  glacier infill  ·  {result.coverage:.0%} coverage</text>',
]

top = PAD + TITLE_H
lines.append(
    f'  <rect x="{PAD}" y="{top}" '
    f'width="{bb_w*scale:.1f}" height="{bb_h*scale:.1f}" '
    f'fill="{PACK_BG}" stroke="none"/>'
)

for p in result.placements:
    color = box_color(p.width, p.height)
    x = PAD + p.x * scale
    y = top + p.y * scale
    w = p.width * scale
    h = p.height * scale
    lines.append(
        f'  <rect x="{x:.2f}" y="{y:.2f}" '
        f'width="{w:.2f}" height="{h:.2f}" '
        f'fill="{color}" stroke="{BG}" stroke-width="0.6" rx="1.5"/>'
    )

lines.append('</svg>')

out = Path(__file__).parent / "demo.svg"
out.write_text("\n".join(lines))
print(f"Saved → {out}")

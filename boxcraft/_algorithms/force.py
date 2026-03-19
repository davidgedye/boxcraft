"""
Force-directed packing algorithm.

Boxes are treated as rigid rectangles that repel each other when overlapping
and are attracted toward a common centre by a gravity force.  The system is
iterated until overlaps are resolved and the pack stabilises.

Unlike the row-based algorithms this produces organic, non-grid layouts.  It
is O(n²) per iteration so it is best suited to small sets (n ≲ 30) where many
iterations can be afforded cheaply.

Options
-------
n_iter : int (default 500)
    Number of simulation steps.

gravity : float (default 0.05)
    Strength of the centripetal attraction.  Decays linearly to zero over the
    course of the simulation so boxes settle rather than oscillate.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from boxcraft._types import Box, Placement


@dataclass
class ForceOptions:
    n_iter: int = 500
    gravity: float = 0.05


def pack(
    boxes: list[Box],
    *,
    gap_h: float,
    gap_v: float,
    edge_gap: float,
    aspect_ratio: float | None,
    rng: random.Random,
    options: ForceOptions | None = None,
) -> list[Placement]:
    if not boxes:
        return []

    if len(boxes) == 1:
        return [Placement(box=boxes[0], x=edge_gap, y=edge_gap)]

    opts = options or ForceOptions()
    n = len(boxes)

    # Effective sizes (gaps become part of each box during physics so natural
    # separation between box edges equals the requested gap).
    ew = [b.width  + gap_h for b in boxes]
    eh = [b.height + gap_v for b in boxes]

    # Initialise centres randomly within a circle sized to the total area.
    total_area = sum(b.width * b.height for b in boxes)
    r0 = math.sqrt(total_area) * 0.6
    cx = [rng.uniform(-r0, r0) for _ in range(n)]
    cy = [rng.uniform(-r0, r0) for _ in range(n)]

    # Aspect-ratio gravity bias: stronger pull along the shorter target axis.
    if aspect_ratio is not None:
        gx_scale = math.sqrt(aspect_ratio)
        gy_scale = 1.0 / math.sqrt(aspect_ratio)
    else:
        gx_scale = gy_scale = 1.0

    for step in range(opts.n_iter):
        # ── Repulsion: separate every overlapping pair ────────────────────────
        for i in range(n):
            for j in range(i + 1, n):
                ox = (ew[i] + ew[j]) / 2.0 - abs(cx[i] - cx[j])
                oy = (eh[i] + eh[j]) / 2.0 - abs(cy[i] - cy[j])
                if ox > 0 and oy > 0:
                    if ox <= oy:
                        half = ox / 2.0
                        sign = 1.0 if cx[i] >= cx[j] else -1.0
                        cx[i] += sign * half
                        cx[j] -= sign * half
                    else:
                        half = oy / 2.0
                        sign = 1.0 if cy[i] >= cy[j] else -1.0
                        cy[i] += sign * half
                        cy[j] -= sign * half

        # ── Gravity: pull toward centroid, decaying linearly ──────────────────
        mean_cx = sum(cx) / n
        mean_cy = sum(cy) / n
        g = opts.gravity * (1.0 - step / opts.n_iter)
        for i in range(n):
            cx[i] += g * (mean_cx - cx[i]) * gx_scale
            cy[i] += g * (mean_cy - cy[i]) * gy_scale

    # ── Convert centres to top-left placements ────────────────────────────────
    min_x = min(cx[i] - ew[i] / 2.0 for i in range(n))
    min_y = min(cy[i] - eh[i] / 2.0 for i in range(n))

    return [
        Placement(
            box=boxes[i],
            x=cx[i] - boxes[i].width  / 2.0 - min_x + edge_gap,
            y=cy[i] - boxes[i].height / 2.0 - min_y + edge_gap,
        )
        for i in range(n)
    ]

"""
Shelf (strip) packing algorithm.

Boxes are sorted tallest-first and packed greedily left-to-right into rows.
Within each row boxes are bottom-aligned, so shorter boxes sit flush with the
row bottom leaving open space above them.

Options
-------
first_fit : bool (default False)
    When True, use first-fit-decreasing row assignment: scan all remaining
    items for each row and skip (defer) any that don't fit, rather than
    closing the row at the first non-fitting item.  Produces denser rows and
    meaningfully better coverage, at the cost of O(n²) row assignment.

balanced : bool (default False)
    Reorder boxes within each row so the tallest lands in the centre, with
    shorter boxes radiating outward symmetrically — a mountain silhouette.
    Does not change coverage but looks more visually balanced.

shuffled : bool (default False)
    Randomly permute the vertical order of rows after packing.  Eliminates
    the top-heavy size gradient that results from tallest-first assignment.
    Uses the Packer seed for reproducibility.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from boxcraft._types import Box, Placement


@dataclass
class ShelfOptions:
    first_fit: bool = True        # first-fit-decreasing row assignment (better coverage, O(n²))
    balanced: bool = False        # mountain-order boxes within each row
    shuffled: bool = False        # shuffle row order after packing
    justify: str = "center"       # horizontal row alignment: "left" or "center"


# ---------------------------------------------------------------------------
# Row-level helpers
# ---------------------------------------------------------------------------

def _assign_rows(
    sorted_pairs: list[tuple[int, Box]],
    row_width: float,
    gap_h: float,
    edge_gap: float,
    first_fit: bool = False,
) -> list[list[tuple[int, Box]]] | None:
    """
    Assign boxes to rows of inner width (row_width - 2*edge_gap).

    first_fit=False (default): classic greedy shelf — close the row at the
        first non-fitting item.  Returns None if any box is wider than
        inner_w (signals binary search to try a wider row_width).

    first_fit=True: scan all remaining items for each row, deferring any
        that don't fit.  Never returns None; boxes wider than inner_w are
        silently deferred until they become the only candidate (then placed
        alone, or dropped if they truly can't fit).
    """
    inner_w = row_width - 2 * edge_gap
    rows: list[list[tuple[int, Box]]] = []

    if first_fit:
        queue = list(sorted_pairs)
        while queue:
            row: list[tuple[int, Box]] = []
            leftover: list[tuple[int, Box]] = []
            cur_x = 0.0
            for orig_idx, box in queue:
                bw = box.width
                if bw > inner_w:
                    leftover.append((orig_idx, box))
                    continue
                if not row:
                    row.append((orig_idx, box))
                    cur_x = bw
                elif cur_x + gap_h + bw <= inner_w:
                    row.append((orig_idx, box))
                    cur_x += gap_h + bw
                else:
                    leftover.append((orig_idx, box))
            if not row:
                break
            rows.append(row)
            queue = leftover
    else:
        cur_row: list[tuple[int, Box]] = []
        cur_x = 0.0
        for orig_idx, box in sorted_pairs:
            bw = box.width
            if bw > inner_w:
                return None
            if cur_row:
                if cur_x + gap_h + bw <= inner_w:
                    cur_row.append((orig_idx, box))
                    cur_x += gap_h + bw
                else:
                    rows.append(cur_row)
                    cur_row = [(orig_idx, box)]
                    cur_x = bw
            else:
                cur_row = [(orig_idx, box)]
                cur_x = bw
        if cur_row:
            rows.append(cur_row)

    return rows


def _mountain_order(row: list[tuple[int, Box]]) -> list[tuple[int, Box]]:
    """
    Reorder a tallest-first row so the tallest item lands in the centre,
    with shorter items radiating outward symmetrically to each end.
    """
    n = len(row)
    if n <= 1:
        return row
    result: list[tuple[int, Box] | None] = [None] * n
    mid = n // 2
    positions = [mid]
    l, r = mid - 1, mid + 1
    while l >= 0 or r < n:
        if l >= 0:
            positions.append(l); l -= 1
        if r < n:
            positions.append(r); r += 1
    for item, pos in zip(row, positions):
        result[pos] = item
    return result  # type: ignore[return-value]


def _row_width(row: list[tuple[int, Box]], gap_h: float) -> float:
    return sum(box.width for _, box in row) + gap_h * (len(row) - 1)


def _rows_to_placements(
    rows: list[list[tuple[int, Box]]],
    gap_h: float,
    gap_v: float,
    edge_gap: float,
    justify: str = "center",
    inner_w: float | None = None,
) -> list[tuple[int, float, float]]:
    """Convert row structure to flat (orig_idx, x, y) list."""
    if not rows:
        return []
    center_w = inner_w if inner_w is not None else max(_row_width(row, gap_h) for row in rows)
    out: list[tuple[int, float, float]] = []
    y = edge_gap
    for row in rows:
        row_h = max(box.height for _, box in row)
        row_w = _row_width(row, gap_h)
        if justify == "center":
            x = edge_gap + (center_w - row_w) / 2
        else:  # "left"
            x = edge_gap
        for orig_idx, box in row:
            out.append((orig_idx, x, y + (row_h - box.height)))
            x += box.width + gap_h
        y += row_h + gap_v
    return out


def _bounding_box(
    raw: list[tuple[int, float, float]],
    boxes: list[Box],
    edge_gap: float,
) -> tuple[float, float]:
    right  = max(x + boxes[idx].width  for idx, x, _y in raw)
    bottom = max(y + boxes[idx].height for idx, _x, y  in raw)
    return (right + edge_gap, bottom + edge_gap)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def pack(
    boxes: list[Box],
    *,
    gap_h: float,
    gap_v: float,
    edge_gap: float,
    aspect_ratio: float | None,
    rng: random.Random,
    options: ShelfOptions | None = None,
) -> list[Placement]:
    if not boxes:
        return []

    opts = options or ShelfOptions()
    sorted_pairs = sorted(enumerate(boxes), key=lambda p: -p[1].height)

    total_area = sum(b.width * b.height for b in boxes)
    w_min = max(b.width for b in boxes) + 2 * edge_gap
    w_max = sum(b.width for b in boxes) + (len(boxes) - 1) * gap_h + 2 * edge_gap

    ff = opts.first_fit

    # ── Find the right row width ─────────────────────────────────────────────
    if aspect_ratio is None:
        row_width = max(math.sqrt(total_area), w_min)
        rows = _assign_rows(sorted_pairs, row_width, gap_h, edge_gap, ff)
        if rows is None:
            row_width = w_max
            rows = _assign_rows(sorted_pairs, row_width, gap_h, edge_gap, ff)
    else:
        lo, hi = w_min, w_max
        best_rows: list[list[tuple[int, Box]]] | None = None
        best_row_width = w_max
        for _ in range(15):
            mid = (lo + hi) / 2
            candidate = _assign_rows(sorted_pairs, mid, gap_h, edge_gap, ff)
            if candidate is None:
                lo = mid
                continue
            row_heights = [max(b.height for _, b in row) for row in candidate]
            bb_w = mid
            bb_h = sum(row_heights) + gap_v * (len(row_heights) - 1) + 2 * edge_gap
            if bb_w / bb_h < aspect_ratio:
                lo = mid
            else:
                hi = mid
                best_rows = candidate
                best_row_width = mid
        row_width = best_row_width
        rows = best_rows or _assign_rows(sorted_pairs, w_max, gap_h, edge_gap, ff)

    if not rows:
        rows = []

    inner_w = row_width - 2 * edge_gap

    # ── Apply options ────────────────────────────────────────────────────────
    if opts.balanced:
        rows = [_mountain_order(row) for row in rows]

    if opts.shuffled:
        rng.shuffle(rows)

    # ── Convert to Placement objects ─────────────────────────────────────────
    raw = _rows_to_placements(rows, gap_h, gap_v, edge_gap, opts.justify, inner_w)

    result: list[Placement | None] = [None] * len(boxes)
    for orig_idx, x, y in raw:
        result[orig_idx] = Placement(box=boxes[orig_idx], x=x, y=y)

    for i, p in enumerate(result):
        if p is None:
            result[i] = Placement(box=boxes[i], x=edge_gap, y=edge_gap)

    return result  # type: ignore[return-value]

"""
Glacier packing algorithm.

Shelf-style greedy row packing enhanced with two features:

1. **Mountain ordering** — within each row the tallest box lands in the centre
   with shorter boxes radiating outward symmetrically, creating a mountain
   silhouette (enabled by default; ``balanced=True``).

2. **Valley fill** — boxes that overflow a full row are tried in the triangular
   spaces above the shorter boxes on each side of the mountain.  The largest-area
   box that fits is placed first, working inward from each edge.

Options
-------
balanced : bool (default True)
    Mountain-order boxes within each row.  Defaults to True because valley fill
    is most effective on a mountain silhouette.

shuffled : bool (default False)
    Randomly permute the vertical order of rows after packing.

justify : str (default "center")
    "center" or "left" — horizontal row alignment.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from boxcraft._types import Box, Placement
from boxcraft._algorithms.shelf import _mountain_order, _row_width


@dataclass
class GlacierOptions:
    balanced: bool = True    # mountain-order within rows
    shuffled: bool = False   # shuffle row order after packing
    justify: str = "center"  # "left" or "center"


# ---------------------------------------------------------------------------
# Row-level helpers
# ---------------------------------------------------------------------------

def _assign_one_row(
    queue: list[tuple[int, Box]],
    inner_w: float,
    gap_h: float,
) -> tuple[list[tuple[int, Box]], list[tuple[int, Box]]]:
    """
    First-fit row assignment: visit items in order (tallest-first) and add
    each to the current row if it fits; otherwise send it to leftover.

    Unlike shelf's strict left-to-right greedy, this skips wide items and
    continues checking narrower ones, filling each row more completely.
    """
    row: list[tuple[int, Box]] = []
    leftover: list[tuple[int, Box]] = []
    cur_x = 0.0
    for orig_idx, box in queue:
        bw = box.width
        if not row:
            row.append((orig_idx, box))
            cur_x = bw
        elif cur_x + gap_h + bw <= inner_w:
            row.append((orig_idx, box))
            cur_x += gap_h + bw
        else:
            leftover.append((orig_idx, box))
    return row, leftover


def _valley_fill(
    mtn_info: list[tuple[int, float, float, float]],  # (orig_idx, x_left, width, height)
    candidates: list[tuple[int, Box]],
    row_h: float,
    gap_h: float,
    gap_v: float,
) -> tuple[list[tuple[int, float, float]], list[tuple[int, Box]]]:
    """
    Place candidate boxes into the valley space above shorter mountain items.

    For each fill box candidate we walk inward from the outer edge and find the
    first mountain item it cannot vertically clear (i.e. jh + gap_v > row_h -
    item.height).  The fill box can fly over any item it does clear, so it is
    pushed flush against that first blocker.  This leaves the entire outer strip
    free for subsequent fills, which can be taller because they sit over shorter
    (outer) mountain items.

    Returns (placed, remaining) where placed items carry y_rel=0.0 (top-aligned).
    """
    placed: list[tuple[int, float, float]] = []
    remaining = list(candidates)

    for side in ("left", "right"):
        edge_items = mtn_info if side == "left" else list(reversed(mtn_info))

        if side == "left":
            x_ref = edge_items[0][1]
        else:
            x_ref = edge_items[0][1] + edge_items[0][2]

        # Outer strip width available from x_ref (shrinks after each placement).
        outer_limit: float = (
            (edge_items[-1][1] + edge_items[-1][2] - x_ref) if side == "left"
            else (x_ref - edge_items[-1][1])
        )

        while outer_limit > 0.0 and remaining:
            best_orig_idx: int | None = None
            best_area = 0.0
            best_max_inner = 0.0

            for orig_idx, box in remaining:
                jw, jh = box.width, box.height

                # Find the first mountain item this box cannot vertically clear,
                # walking inward from the outer edge.  The box may fly over any
                # item whose top edge is above the box's bottom (jh + gap_v).
                max_inner = outer_limit  # fallback if no blocker found
                for _, x_k, w_k, h_k in edge_items:
                    if jh + gap_v > row_h - h_k:
                        # Blocker: place box flush against this item (with gap_h).
                        barrier = (
                            x_k - x_ref - gap_h if side == "left"
                            else x_ref - (x_k + w_k) - gap_h
                        )
                        max_inner = min(outer_limit, barrier)
                        break

                if max_inner < jw:
                    continue

                area = jw * jh
                if area > best_area:
                    best_area = area
                    best_orig_idx = orig_idx
                    best_max_inner = max_inner

            if best_orig_idx is None:
                break

            box = next(b for i, b in remaining if i == best_orig_idx)
            jw = box.width
            jh = box.height
            if side == "left":
                px = x_ref + best_max_inner - jw
            else:
                px = x_ref - best_max_inner

            # Drop as low as possible: find the tallest mountain item horizontally
            # covered by this fill box and sit just above it.
            fill_x_r = px + jw
            max_h_under = max(
                (h_m for _, x_m, w_m, h_m in mtn_info if x_m < fill_x_r and x_m + w_m > px),
                default=0.0,
            )
            y_rel = max(row_h - max_h_under - jh - gap_v, 0.0)

            placed.append((best_orig_idx, px, y_rel))
            remaining = [(i, b) for i, b in remaining if i != best_orig_idx]
            outer_limit = best_max_inner - jw - gap_h

    return placed, remaining


# ---------------------------------------------------------------------------
# Bounding-box estimator for binary search
# ---------------------------------------------------------------------------

def _glacier_bb(
    sorted_pairs: list[tuple[int, Box]],
    row_width: float,
    gap_h: float,
    gap_v: float,
    edge_gap: float,
    opts: GlacierOptions | None = None,
) -> tuple[float, float]:
    """
    Accurately estimate the bounding box for a given row_width by simulating
    the full glacier pack including valley fill.  Valley fill absorbs overflow
    boxes into existing rows, reducing the row count and therefore bb_h.

    For center-justified layouts the tight width equals row_width exactly.
    """
    _opts = opts or GlacierOptions()
    inner_w = row_width - 2 * edge_gap
    queue = list(sorted_pairs)
    row_heights: list[float] = []
    while queue:
        row, overflow = _assign_one_row(queue, inner_w, gap_h)
        if not row:
            break

        if _opts.balanced:
            row = _mountain_order(row)

        row_h = max(box.height for _, box in row)
        row_w = _row_width(row, gap_h)

        x_start = edge_gap + (inner_w - row_w) / 2 if _opts.justify == "center" else edge_gap
        x = x_start
        mtn_info: list[tuple[int, float, float, float]] = []
        for orig_idx, box in row:
            mtn_info.append((orig_idx, x, box.width, box.height))
            x += box.width + gap_h

        _, overflow = _valley_fill(mtn_info, overflow, row_h, gap_h, gap_v)

        row_heights.append(row_h)
        queue = overflow

    if not row_heights:
        return (0.0, 0.0)
    bb_w = row_width
    bb_h = sum(row_heights) + gap_v * (len(row_heights) - 1) + 2 * edge_gap
    return (bb_w, bb_h)


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
    options: GlacierOptions | None = None,
) -> list[Placement]:
    if not boxes:
        return []

    opts = options or GlacierOptions()
    sorted_pairs = sorted(enumerate(boxes), key=lambda p: -p[1].height)

    total_area = sum(b.width * b.height for b in boxes)
    w_min = max(b.width for b in boxes) + 2 * edge_gap
    w_max = sum(b.width for b in boxes) + (len(boxes) - 1) * gap_h + 2 * edge_gap

    # ── Find the right row width ─────────────────────────────────────────────
    if aspect_ratio is None:
        row_width = max(math.sqrt(total_area), w_min)
        # Verify the widest box fits
        inner_check = row_width - 2 * edge_gap
        test_row, _ = _assign_one_row(sorted_pairs, inner_check, gap_h)
        if not test_row:
            row_width = w_max
    else:
        lo, hi = w_min, w_max
        best_row_width = w_max
        for _ in range(15):
            mid = (lo + hi) / 2
            bb_w, bb_h = _glacier_bb(sorted_pairs, mid, gap_h, gap_v, edge_gap, opts)
            if bb_h == 0.0:
                lo = mid
                continue
            if bb_w / bb_h < aspect_ratio:
                lo = mid
            else:
                hi = mid
                best_row_width = mid
        row_width = best_row_width

    inner_w = row_width - 2 * edge_gap

    # ── Build rows: mountain ordering + valley fill ──────────────────────────
    # Each row_structure: (row_h, [(orig_idx, x, y_rel)])
    row_structures: list[tuple[float, list[tuple[int, float, float]]]] = []
    queue = list(sorted_pairs)

    while queue:
        row, overflow = _assign_one_row(queue, inner_w, gap_h)
        if not row:
            break

        if opts.balanced:
            row = _mountain_order(row)

        row_h = max(box.height for _, box in row)
        row_w = _row_width(row, gap_h)

        if opts.justify == "center":
            x_start = edge_gap + (inner_w - row_w) / 2
        else:
            x_start = edge_gap

        # Place mountain items (bottom-aligned: y_rel = row_h - box.height)
        x = x_start
        mtn_info: list[tuple[int, float, float, float]] = []
        for orig_idx, box in row:
            mtn_info.append((orig_idx, x, box.width, box.height))
            x += box.width + gap_h

        # (orig_idx, x, y_rel, valley_fill)
        main_entries = [
            (orig_idx, lx, row_h - h, False)
            for orig_idx, lx, _w, h in mtn_info
        ]

        # Valley fill from overflow items
        valley_raw, overflow = _valley_fill(mtn_info, overflow, row_h, gap_h, gap_v)
        valley_entries = [(idx, px, py_rel, True) for idx, px, py_rel in valley_raw]

        row_structures.append((row_h, main_entries + valley_entries))
        queue = overflow

    # ── Shuffle rows if requested ────────────────────────────────────────────
    if opts.shuffled:
        rng.shuffle(row_structures)

    # ── Assign final y coordinates ───────────────────────────────────────────
    result: list[Placement | None] = [None] * len(boxes)
    y = edge_gap
    for row_h, entries in row_structures:
        for orig_idx, px, py_rel, is_valley in entries:
            meta = {"valley_fill": True} if is_valley else None
            result[orig_idx] = Placement(box=boxes[orig_idx], x=px, y=y + py_rel, meta=meta)
        y += row_h + gap_v

    # Safety net for any unplaced boxes
    for i, p in enumerate(result):
        if p is None:
            result[i] = Placement(box=boxes[i], x=edge_gap, y=edge_gap)

    # ── Vertical centering within the aspect-ratio container ─────────────────
    if aspect_ratio is not None:
        tight_h = max(p.y + p.height for p in result if p is not None) + edge_gap  # type: ignore[union-attr]
        target_h = row_width / aspect_ratio
        if target_h > tight_h:
            y_offset = (target_h - tight_h) / 2
            result = [
                Placement(box=p.box, x=p.x, y=p.y + y_offset, meta=p.meta)  # type: ignore[union-attr]
                for p in result
            ]

    return result  # type: ignore[return-value]

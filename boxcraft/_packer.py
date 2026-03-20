from __future__ import annotations

import random
import time
from typing import Iterable

from boxcraft._types import Box, PackResult, Placement
from boxcraft._algorithms.shelf import pack as _shelf_pack, ShelfOptions
from boxcraft._algorithms.glacier import pack as _glacier_pack, GlacierOptions


def pack(
    boxes: Iterable[Box | tuple[float, float]],
    *,
    infill: bool = True,
    balanced: bool = True,
    shuffled: bool = True,
    justify: str = "center",
    aspect_ratio: float | None = None,
    width: float | None = None,
    gap_h: float = 0.0,
    gap_v: float = 0.0,
    edge_gap: float = 0.0,
    seed: int | str = 0,
) -> PackResult:
    """
    Pack boxes into a compact 2D layout and return a PackResult.

    Parameters
    ----------
    boxes        : boxes to pack — Box instances or (width, height) tuples
    infill       : use valley fill (glacier) when True, plain shelf when False
    balanced     : mountain-order boxes within each row (tallest in centre)
    shuffled     : randomise vertical row order after packing
    justify      : "center" or "left" — horizontal row alignment
    aspect_ratio : target width/height ratio for the bounding box
    width        : fix container width exactly and minimise height;
                   mutually exclusive with aspect_ratio
    gap_h        : horizontal gap between adjacent boxes
    gap_v        : vertical gap between adjacent boxes
    edge_gap     : margin between outermost boxes and container edge
    seed         : random seed (int or str) — affects shuffled row order
    """
    if aspect_ratio is not None and width is not None:
        raise ValueError("aspect_ratio and width are mutually exclusive")

    box_list = [_coerce_box(b) for b in boxes]
    rng = random.Random(seed)
    t0 = time.perf_counter()

    if infill:
        opts = GlacierOptions(balanced=balanced, shuffled=shuffled, justify=justify)
        placements = _glacier_pack(
            box_list, gap_h=gap_h, gap_v=gap_v, edge_gap=edge_gap,
            aspect_ratio=aspect_ratio, width=width, rng=rng, options=opts,
        )
        algo_name = "glacier"
    else:
        opts = ShelfOptions(balanced=balanced, shuffled=shuffled, justify=justify)
        placements = _shelf_pack(
            box_list, gap_h=gap_h, gap_v=gap_v, edge_gap=edge_gap,
            aspect_ratio=aspect_ratio, width=width, rng=rng, options=opts,
        )
        algo_name = "shelf"

    wall_ms = (time.perf_counter() - t0) * 1000

    return PackResult(
        placements=placements,
        algorithm=algo_name,
        wall_time_ms=wall_ms,
        _gap_h=gap_h,
        _gap_v=gap_v,
        _edge_gap=edge_gap,
        _target_aspect_ratio=aspect_ratio,
        _target_width=width,
    )


def _coerce_box(b: Box | tuple[float, float]) -> Box:
    if isinstance(b, Box):
        return b
    try:
        w, h = b
    except (TypeError, ValueError):
        raise TypeError(f"Expected Box or (width, height) tuple, got {b!r}")
    return Box(width=float(w), height=float(h))

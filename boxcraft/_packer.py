from __future__ import annotations

import random
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Iterable

from boxcraft._types import Box, PackResult, Placement
from boxcraft._algorithms import get as _get_algo


# ---------------------------------------------------------------------------
# Module-level RNG — used by pack() and as a default for Packer(seed=0)
# ---------------------------------------------------------------------------

_MODULE_RNG = random.Random(0)


@contextmanager
def random_context(seed: int | str) -> Generator[None, None, None]:
    """
    Force all boxcraft packing within this block to use the given seed.

    Example::

        with bc.random_context(42):
            result = bc.pack(boxes, algorithm="glacier")
    """
    old_state = _MODULE_RNG.getstate()
    _MODULE_RNG.seed(seed)
    try:
        yield
    finally:
        _MODULE_RNG.setstate(old_state)


# ---------------------------------------------------------------------------
# Packer
# ---------------------------------------------------------------------------

class Packer:
    """
    Stateful packer.  Configure once, add boxes, call pack().

    Parameters
    ----------
    algorithm     : name of the packing algorithm (see bc.algorithms())
    aspect_ratio  : required width/height ratio for the bounding box; None = free
    width         : fix the container width exactly and minimise height; mutually
                    exclusive with aspect_ratio
    gap_h         : horizontal gap between adjacent boxes
    gap_v         : vertical gap between adjacent boxes
    edge_gap      : margin between outermost boxes and bounding box edge (default 0)
    seed          : int or str seed for algorithms that use randomness; str is hashed
    options       : typed algorithm-specific options dataclass instance
    """

    def __init__(
        self,
        algorithm: str = "shelf",
        *,
        aspect_ratio: float | None = None,
        width: float | None = None,
        gap_h: float = 0.0,
        gap_v: float = 0.0,
        edge_gap: float = 0.0,
        seed: int | str = 0,
        options: object = None,
    ) -> None:
        if aspect_ratio is not None and width is not None:
            raise ValueError("aspect_ratio and width are mutually exclusive")
        self._algo_name = algorithm
        self._algo_fn = _get_algo(algorithm)
        self._aspect_ratio = aspect_ratio
        self._width = width
        self._gap_h = gap_h
        self._gap_v = gap_v
        self._edge_gap = edge_gap
        self._rng = random.Random(seed)
        self._options = options
        self._boxes: list[Box] = []

    def add(self, box: Box | tuple[float, float]) -> None:
        self._boxes.append(_coerce_box(box))

    def add_many(self, boxes: Iterable[Box | tuple[float, float]]) -> None:
        for b in boxes:
            self._boxes.append(_coerce_box(b))

    def pack(self) -> PackResult:
        t0 = time.perf_counter()
        placements: list[Placement] = self._algo_fn(
            self._boxes,
            gap_h=self._gap_h,
            gap_v=self._gap_v,
            edge_gap=self._edge_gap,
            aspect_ratio=self._aspect_ratio,
            width=self._width,
            rng=self._rng,
            options=self._options,
        )
        wall_ms = (time.perf_counter() - t0) * 1000

        return PackResult(
            placements=placements,
            algorithm=self._algo_name,
            wall_time_ms=wall_ms,
            _gap_h=self._gap_h,
            _gap_v=self._gap_v,
            _edge_gap=self._edge_gap,
            _target_aspect_ratio=self._aspect_ratio,
            _target_width=self._width,
        )

    def reset(self) -> None:
        """Clear all added boxes, keeping configuration."""
        self._boxes = []


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def pack(
    boxes: Iterable[Box | tuple[float, float]],
    algorithm: str = "shelf",
    *,
    aspect_ratio: float | None = None,
    width: float | None = None,
    gap_h: float = 0.0,
    gap_v: float = 0.0,
    edge_gap: float = 0.0,
    **options,
) -> PackResult:
    """
    Pack boxes and return a PackResult.

    Always deterministic (uses internal seed 0).
    For custom seeds or reusable configuration, use Packer directly.

    Any extra keyword arguments are passed to the algorithm as raw options;
    for type-safe options use ``Packer(options=AlgoOptions(...))`` instead.
    """
    packer = Packer(
        algorithm=algorithm,
        aspect_ratio=aspect_ratio,
        width=width,
        gap_h=gap_h,
        gap_v=gap_v,
        edge_gap=edge_gap,
        seed=0,
    )
    packer.add_many(boxes)
    return packer.pack()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coerce_box(b: Box | tuple[float, float]) -> Box:
    if isinstance(b, Box):
        return b
    try:
        w, h = b
    except (TypeError, ValueError):
        raise TypeError(f"Expected Box or (width, height) tuple, got {b!r}")
    return Box(width=float(w), height=float(h))

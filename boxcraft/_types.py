from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Box:
    width: float
    height: float
    label: str | None = None
    data: Any = None

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError(
                f"Box dimensions must be positive, got {self.width}x{self.height}"
            )


@dataclass
class Placement:
    box: Box
    x: float        # left edge
    y: float        # top edge  (origin = top-left of bounding box)
    meta: dict | None = field(default=None, repr=False)  # optional algorithm metadata

    @property
    def width(self) -> float:
        return self.box.width

    @property
    def height(self) -> float:
        return self.box.height

    @property
    def rect(self) -> tuple[float, float, float, float]:
        """(x, y, width, height)"""
        return (self.x, self.y, self.width, self.height)

    @property
    def center(self) -> tuple[float, float]:
        """(cx, cy)"""
        return (self.x + self.width / 2, self.y + self.height / 2)


@dataclass
class PackResult:
    placements: list[Placement]
    algorithm: str
    wall_time_ms: float = 0.0
    _gap_h: float = field(default=0.0, repr=False)
    _gap_v: float = field(default=0.0, repr=False)
    _edge_gap: float = field(default=0.0, repr=False)
    _target_aspect_ratio: float | None = field(default=None, repr=False)
    _target_width: float | None = field(default=None, repr=False)

    @property
    def tight_bounding_box(self) -> tuple[float, float]:
        """(width, height) of the actual tight bounding box including edge_gap margins."""
        if not self.placements:
            return (0.0, 0.0)
        min_x = min(p.x for p in self.placements)
        min_y = min(p.y for p in self.placements)
        w = max(p.x + p.width  for p in self.placements) + min_x
        h = max(p.y + p.height for p in self.placements) + min_y
        return (w, h)

    @property
    def bounding_box(self) -> tuple[float, float]:
        """
        (width, height) of the target container.

        When width was specified, this is (width, tight_height) — the container
        is exactly that wide and as tall as the packing requires.

        When aspect_ratio was specified, this is the smallest rectangle with
        that exact ratio enclosing all placements — i.e. what the user's
        container actually looks like.

        When neither was given, this equals tight_bounding_box.
        """
        w, h = self.tight_bounding_box
        if self._target_width is not None:
            return (self._target_width, h)
        if self._target_aspect_ratio is None:
            return (w, h)
        # Expand whichever dimension is short to match the target ratio.
        target = self._target_aspect_ratio
        if w / h > target:
            h = w / target   # actual is too wide: expand height
        else:
            w = h * target   # actual is too tall: expand width
        return (w, h)

    @property
    def aspect_ratio(self) -> float:
        """width / height of bounding_box."""
        w, h = self.bounding_box
        return w / h if h > 0 else float("inf")

    @property
    def coverage(self) -> float:
        """
        (Box areas + inter-box gap areas) as a fraction of bounding_box area.

        Approaches 1.0 when boxes and their surrounding gaps perfectly tile the
        container.  Gaps are intended space, not waste — a perfect grid of boxes
        with any uniform gap should score 1.0.  Only true waste (right-edge
        ragged ends, aspect-ratio letterboxing) reduces coverage below 1.0.

        Each box is treated as claiming (w + gap_h) × (h + gap_v).  This
        slightly overcounts gap-corner intersections but the error is
        negligible for typical n and gap sizes.
        """
        if not self.placements:
            return 0.0
        w, h = self.bounding_box
        bb_area = w * h
        if bb_area == 0.0:
            return 0.0
        claimed = sum(
            (p.width + self._gap_h) * (p.height + self._gap_v)
            for p in self.placements
        )
        return min(claimed / bb_area, 1.0)

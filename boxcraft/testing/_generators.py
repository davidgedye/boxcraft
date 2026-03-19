"""
Box set generators for testing and benchmarking.

All generators are seeded and fully reproducible.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod

from boxcraft._types import Box


class BoxGenerator(ABC):
    @abstractmethod
    def generate(self) -> list[Box]: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def describe(self) -> dict: ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.describe()})"


class UniformGenerator(BoxGenerator):
    """
    Boxes whose width and height are drawn independently from uniform
    distributions over [w_min, w_max] and [h_min, h_max].
    """

    def __init__(
        self,
        *,
        w_range: tuple[float, float] = (10.0, 200.0),
        h_range: tuple[float, float] = (10.0, 200.0),
        n: int = 100,
        seed: int = 0,
    ) -> None:
        self.w_range = w_range
        self.h_range = h_range
        self.n = n
        self.seed = seed

    @property
    def name(self) -> str:
        return (
            f"Uniform  w∈[{self.w_range[0]:.0f},{self.w_range[1]:.0f}]"
            f"  h∈[{self.h_range[0]:.0f},{self.h_range[1]:.0f}]"
            f"  n={self.n}"
        )

    def describe(self) -> dict:
        return {
            "type": "uniform",
            "w_range": self.w_range,
            "h_range": self.h_range,
            "n": self.n,
            "seed": self.seed,
        }

    def generate(self) -> list[Box]:
        rng = random.Random(self.seed)
        w_lo, w_hi = self.w_range
        h_lo, h_hi = self.h_range
        return [
            Box(
                width=rng.uniform(w_lo, w_hi),
                height=rng.uniform(h_lo, h_hi),
            )
            for _ in range(self.n)
        ]


class GaussianGenerator(BoxGenerator):
    """
    Boxes whose width and height are drawn independently from normal
    distributions N(w_mean, w_std) and N(h_mean, h_std), clamped to min_size.

    aspect_clip=(lo, hi) discards boxes whose w/h ratio falls outside [lo, hi].
    Discarded boxes are re-drawn until n valid boxes are produced.
    """

    def __init__(
        self,
        *,
        w_mean: float = 100.0,
        w_std: float = 30.0,
        h_mean: float = 80.0,
        h_std: float = 25.0,
        n: int = 100,
        seed: int = 0,
        min_size: float = 1.0,
        aspect_clip: tuple[float, float] | None = None,
    ) -> None:
        self.w_mean = w_mean
        self.w_std = w_std
        self.h_mean = h_mean
        self.h_std = h_std
        self.n = n
        self.seed = seed
        self.min_size = min_size
        self.aspect_clip = aspect_clip

    @property
    def name(self) -> str:
        return (
            f"Gaussian  w~N({self.w_mean:.0f},{self.w_std:.0f})"
            f"  h~N({self.h_mean:.0f},{self.h_std:.0f})"
            f"  n={self.n}"
        )

    def describe(self) -> dict:
        return {
            "type": "gaussian",
            "w_mean": self.w_mean,
            "w_std": self.w_std,
            "h_mean": self.h_mean,
            "h_std": self.h_std,
            "n": self.n,
            "seed": self.seed,
            "min_size": self.min_size,
            "aspect_clip": self.aspect_clip,
        }

    def generate(self) -> list[Box]:
        rng = random.Random(self.seed)
        boxes: list[Box] = []
        lo_ratio = self.aspect_clip[0] if self.aspect_clip else None
        hi_ratio = self.aspect_clip[1] if self.aspect_clip else None

        while len(boxes) < self.n:
            w = max(rng.gauss(self.w_mean, self.w_std), self.min_size)
            h = max(rng.gauss(self.h_mean, self.h_std), self.min_size)
            if lo_ratio is not None and not (lo_ratio <= w / h <= hi_ratio):
                continue
            boxes.append(Box(width=w, height=h))

        return boxes

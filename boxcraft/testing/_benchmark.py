"""
Benchmark runner for head-to-head algorithm comparisons.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import boxcraft as bc
from boxcraft._types import Box, PackResult
from boxcraft.testing._generators import BoxGenerator


_ALGO_KWARGS: dict[str, dict] = {
    "shelf":   {"infill": False},
    "glacier": {"infill": True},
}
_DEFAULT_ALGORITHMS = list(_ALGO_KWARGS)


@dataclass
class AlgorithmResult:
    algorithm: str
    coverage: float
    wall_time_ms: float
    bounding_box: tuple[float, float]
    result: PackResult


@dataclass
class BenchmarkReport:
    generator_name: str
    n_boxes: int
    pack_options: dict
    results: list[AlgorithmResult] = field(default_factory=list)

    def by_coverage(self) -> list[AlgorithmResult]:
        return sorted(self.results, key=lambda r: -r.coverage)

    def by_speed(self) -> list[AlgorithmResult]:
        return sorted(self.results, key=lambda r: r.wall_time_ms)

    def winner(self) -> AlgorithmResult:
        return self.by_coverage()[0]

    def fastest(self) -> AlgorithmResult:
        return self.by_speed()[0]

    def print_table(self) -> None:
        header = f"Generator : {self.generator_name}"
        opts = "  ".join(f"{k}={v}" for k, v in self.pack_options.items() if v)
        if opts:
            header += f"  [{opts}]"

        col_w = [12, 10, 12, 22, 8]
        sep = "─" * sum(col_w)
        row_fmt = "{:<12}  {:>8}  {:>10}  {:>20}  {:>6}"

        print(header)
        print(sep)
        print(row_fmt.format("Algorithm", "Coverage", "Time (ms)", "Bounding box", "Ratio"))
        print(sep)
        for r in self.by_coverage():
            bb = f"{r.bounding_box[0]:,.0f} × {r.bounding_box[1]:,.0f}"
            ratio = r.bounding_box[0] / r.bounding_box[1] if r.bounding_box[1] else 0
            print(row_fmt.format(
                r.algorithm,
                f"{r.coverage:.3f}",
                f"{r.wall_time_ms:.1f}",
                bb,
                f"{ratio:.3f}",
            ))
        print(sep)
        w = self.winner()
        f = self.fastest()
        print(f"Winner (coverage): {w.algorithm}   Fastest: {f.algorithm}")
        print()


class Benchmark:
    """
    Run one or more algorithms on the same box set and compare results.

    Parameters
    ----------
    algorithms  : list of algorithm names ("shelf", "glacier"); defaults to both
    aspect_ratio, gap_h, gap_v, edge_gap : passed to every pack() call
    """

    def __init__(
        self,
        algorithms: list[str] | None = None,
        *,
        aspect_ratio: float | None = None,
        gap_h: float = 0.0,
        gap_v: float = 0.0,
        edge_gap: float = 0.0,
    ) -> None:
        self._algorithms = algorithms or _DEFAULT_ALGORITHMS
        self._aspect_ratio = aspect_ratio
        self._gap_h = gap_h
        self._gap_v = gap_v
        self._edge_gap = edge_gap

    def run(
        self,
        boxes: list[Box],
        generator: BoxGenerator | None = None,
    ) -> BenchmarkReport:
        report = BenchmarkReport(
            generator_name=generator.name if generator else "(ad hoc)",
            n_boxes=len(boxes),
            pack_options={
                "aspect_ratio": self._aspect_ratio,
                "gap_h": self._gap_h,
                "gap_v": self._gap_v,
                "edge_gap": self._edge_gap,
            },
        )

        for algo in self._algorithms:
            algo_kwargs = _ALGO_KWARGS.get(algo, {})
            result = bc.pack(
                boxes,
                **algo_kwargs,
                aspect_ratio=self._aspect_ratio,
                gap_h=self._gap_h,
                gap_v=self._gap_v,
                edge_gap=self._edge_gap,
                seed=0,
            )

            report.results.append(AlgorithmResult(
                algorithm=algo,
                coverage=result.coverage,
                wall_time_ms=result.wall_time_ms,
                bounding_box=result.bounding_box,
                result=result,
            ))

        return report

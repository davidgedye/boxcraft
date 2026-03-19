"""
Benchmark / comparison tests.

These are not pass/fail correctness tests — they print a human-readable
table of coverage and timing for visual inspection.  Run with -s to see output:

    pytest tests/test_benchmark.py -s
"""

import pytest
import boxcraft as bc
from boxcraft.testing import Benchmark, UniformGenerator, GaussianGenerator


def test_shelf_uniform_various_n():
    """Coverage and speed across increasing N."""
    print()
    for n in [100, 500, 1_000, 5_000, 10_000]:
        gen = UniformGenerator(n=n, seed=42)
        boxes = gen.generate()
        bench = Benchmark(["shelf", "glacier"])
        report = bench.run(boxes, generator=gen)
        report.print_table()


def test_shelf_gap_sensitivity():
    """How much do gaps hurt coverage?"""
    gen = UniformGenerator(n=500, seed=42)
    boxes = gen.generate()
    print()
    for gap_h, gap_v in [(0, 0), (2, 2), (5, 5), (10, 10), (20, 20)]:
        bench = Benchmark(["shelf", "glacier"], gap_h=gap_h, gap_v=gap_v)
        report = bench.run(boxes, generator=gen)
        report.print_table()


def test_shelf_aspect_ratio_sensitivity():
    """Coverage cost of enforcing various aspect ratios."""
    gen = GaussianGenerator(n=500, seed=42)
    boxes = gen.generate()
    print()
    for ratio in [0.5, 1.0, 16/9, 2.0, 4.0]:
        bench = Benchmark(["shelf", "glacier"], aspect_ratio=ratio)
        report = bench.run(boxes, generator=gen)
        report.print_table()


def test_shelf_gaussian_vs_uniform():
    """Does box shape distribution affect coverage?"""
    print()
    for gen in [
        UniformGenerator(n=500, seed=42),
        GaussianGenerator(n=500, seed=42),
        GaussianGenerator(n=500, seed=42, w_mean=200, w_std=5, h_mean=50, h_std=5),
    ]:
        boxes = gen.generate()
        bench = Benchmark(["shelf", "glacier"])
        report = bench.run(boxes, generator=gen)
        report.print_table()

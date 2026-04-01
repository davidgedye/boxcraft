"""
Correctness tests for packing algorithms.

These test invariants that must hold for any valid packing:
  - correct number of placements
  - no two boxes overlap
  - gap constraints respected
  - edge_gap constraints respected
  - coverage in (0, 1]
  - bounding box encloses all placements
"""

import pytest
import boxcraft as bc
from boxcraft._types import Box, Placement
from boxcraft.testing import UniformGenerator, GaussianGenerator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _overlaps(a: Placement, b: Placement, tol: float = 1e-6) -> bool:
    """True if two placements overlap (beyond floating-point tolerance)."""
    return not (
        a.x + a.width  <= b.x + tol or
        b.x + b.width  <= a.x + tol or
        a.y + a.height <= b.y + tol or
        b.y + b.height <= a.y + tol
    )


def _assert_no_overlaps(result: bc.PackResult) -> None:
    ps = result.placements
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            assert not _overlaps(ps[i], ps[j]), (
                f"Overlap between placement {i} ({ps[i].rect}) "
                f"and placement {j} ({ps[j].rect})"
            )


def _assert_gaps(result: bc.PackResult, gap_h: float, gap_v: float, tol: float = 1e-6) -> None:
    """No two boxes should be closer than gap_h (horizontal) or gap_v (vertical)."""
    ps = result.placements
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            a, b = ps[i], ps[j]
            h_sep = max(a.x - (b.x + b.width), b.x - (a.x + a.width))
            v_sep = max(a.y - (b.y + b.height), b.y - (a.y + a.height))
            # Boxes are separated in at least one axis; check the relevant gap
            if h_sep > -tol and v_sep <= tol:
                assert h_sep >= gap_h - tol, (
                    f"Horizontal gap {h_sep:.4f} < {gap_h} between {i} and {j}"
                )
            if v_sep > -tol and h_sep <= tol:
                assert v_sep >= gap_v - tol, (
                    f"Vertical gap {v_sep:.4f} < {gap_v} between {i} and {j}"
                )


def _assert_edge_gap(result: bc.PackResult, edge_gap: float, tol: float = 1e-6) -> None:
    for i, p in enumerate(result.placements):
        assert p.x >= edge_gap - tol, f"Placement {i} left edge {p.x} < edge_gap {edge_gap}"
        assert p.y >= edge_gap - tol, f"Placement {i} top edge {p.y} < edge_gap {edge_gap}"
        bb_w, bb_h = result.bounding_box
        assert p.x + p.width  <= bb_w - edge_gap + tol, (
            f"Placement {i} right edge {p.x + p.width:.2f} > bb_w - edge_gap "
            f"{bb_w - edge_gap:.2f}"
        )
        assert p.y + p.height <= bb_h - edge_gap + tol, (
            f"Placement {i} bottom edge {p.y + p.height:.2f} > bb_h - edge_gap "
            f"{bb_h - edge_gap:.2f}"
        )


# ---------------------------------------------------------------------------
# Parametrised fixtures
# ---------------------------------------------------------------------------

GENERATORS = [
    UniformGenerator(n=50,   seed=1),
    UniformGenerator(n=200,  seed=2),
    GaussianGenerator(n=50,  seed=3),
    GaussianGenerator(n=200, seed=4),
]

GAP_CASES = [
    (0.0, 0.0, 0.0),
    (5.0, 5.0, 0.0),
    (5.0, 8.0, 0.0),
    (4.0, 4.0, 8.0),
]

# Each entry is a dict of kwargs to pass to bc.pack()
PACK_KWARGS = [
    pytest.param({"infill": False}, id="shelf"),
    pytest.param({"infill": True},  id="glacier"),
    pytest.param({"ordered": True}, id="ordered"),
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPlacementCount:
    @pytest.mark.parametrize("kwargs", PACK_KWARGS)
    @pytest.mark.parametrize("gen", GENERATORS)
    def test_all_boxes_placed(self, kwargs, gen):
        boxes = gen.generate()
        result = bc.pack(boxes, **kwargs)
        assert len(result.placements) == len(boxes)

    @pytest.mark.parametrize("kwargs", PACK_KWARGS)
    def test_empty_input(self, kwargs):
        result = bc.pack([], **kwargs)
        assert result.placements == []

    @pytest.mark.parametrize("kwargs", PACK_KWARGS)
    def test_single_box(self, kwargs):
        result = bc.pack([(100, 50)], **kwargs)
        assert len(result.placements) == 1
        p = result.placements[0]
        assert p.width == 100
        assert p.height == 50


class TestNoOverlaps:
    @pytest.mark.parametrize("kwargs", PACK_KWARGS)
    @pytest.mark.parametrize("gen", GENERATORS)
    @pytest.mark.parametrize("gap_h,gap_v,edge_gap", GAP_CASES)
    def test_no_overlaps(self, kwargs, gen, gap_h, gap_v, edge_gap):
        boxes = gen.generate()
        result = bc.pack(boxes, **kwargs, gap_h=gap_h, gap_v=gap_v, edge_gap=edge_gap)
        _assert_no_overlaps(result)


class TestGaps:
    @pytest.mark.parametrize("kwargs", PACK_KWARGS)
    @pytest.mark.parametrize("gap_h,gap_v,edge_gap", [
        (5.0, 5.0, 0.0),
        (10.0, 3.0, 0.0),
        (4.0, 4.0, 8.0),
    ])
    def test_gaps_respected(self, kwargs, uniform_100, gap_h, gap_v, edge_gap):
        result = bc.pack(
            uniform_100, **kwargs,
            gap_h=gap_h, gap_v=gap_v, edge_gap=edge_gap,
        )
        _assert_no_overlaps(result)
        _assert_gaps(result, gap_h, gap_v)

    @pytest.mark.parametrize("kwargs", PACK_KWARGS)
    def test_edge_gap_respected(self, kwargs, uniform_100):
        edge_gap = 12.0
        result = bc.pack(uniform_100, **kwargs, edge_gap=edge_gap)
        _assert_edge_gap(result, edge_gap)


class TestCoverage:
    @pytest.mark.parametrize("kwargs", PACK_KWARGS)
    @pytest.mark.parametrize("gen", GENERATORS)
    def test_coverage_in_range(self, kwargs, gen):
        boxes = gen.generate()
        result = bc.pack(boxes, **kwargs)
        assert 0.0 < result.coverage <= 1.0

    @pytest.mark.parametrize("kwargs", PACK_KWARGS)
    def test_coverage_not_penalized_for_gaps(self, kwargs, uniform_100):
        # Gaps are intended space — coverage should be similar with or without gaps
        r_no_gap = bc.pack(uniform_100, **kwargs)
        r_gap    = bc.pack(uniform_100, **kwargs, gap_h=10, gap_v=10)
        assert abs(r_gap.coverage - r_no_gap.coverage) < 0.05

    @pytest.mark.parametrize("kwargs", PACK_KWARGS)
    def test_coverage_decreases_with_edge_gap(self, kwargs, uniform_100):
        r_no_edge  = bc.pack(uniform_100, **kwargs)
        r_edge     = bc.pack(uniform_100, **kwargs, edge_gap=20)
        assert r_edge.coverage < r_no_edge.coverage

    def test_glacier_beats_shelf(self, uniform_100):
        """Glacier should achieve better or equal coverage than shelf."""
        shelf   = bc.pack(uniform_100, infill=False)
        glacier = bc.pack(uniform_100, infill=True)
        assert glacier.coverage >= shelf.coverage - 0.01  # at least close


class TestBoundingBox:
    @pytest.mark.parametrize("kwargs", PACK_KWARGS)
    @pytest.mark.parametrize("gen", GENERATORS)
    def test_bounding_box_encloses_all(self, kwargs, gen):
        boxes = gen.generate()
        result = bc.pack(boxes, **kwargs)
        bb_w, bb_h = result.bounding_box
        tol = 1e-6
        for i, p in enumerate(result.placements):
            assert p.x + p.width  <= bb_w + tol, f"Placement {i} exceeds bb width"
            assert p.y + p.height <= bb_h + tol, f"Placement {i} exceeds bb height"
            assert p.x >= -tol,  f"Placement {i} has negative x"
            assert p.y >= -tol,  f"Placement {i} has negative y"

    @pytest.mark.parametrize("kwargs", PACK_KWARGS)
    def test_aspect_ratio_exact_on_bounding_box(self, kwargs):
        """bounding_box must have exactly the target ratio when aspect_ratio is set."""
        gen = UniformGenerator(n=200, seed=7)
        boxes = gen.generate()
        for target in [0.5, 1.0, 2.0, 16/9]:
            result = bc.pack(boxes, **kwargs, aspect_ratio=target)
            assert abs(result.aspect_ratio - target) < 1e-9, (
                f"kwargs={kwargs} aspect_ratio={target}: bounding_box ratio={result.aspect_ratio:.6f}"
            )

    @pytest.mark.parametrize("kwargs", PACK_KWARGS)
    def test_tight_bbox_encloses_placements(self, kwargs):
        """tight_bounding_box must still enclose all placements."""
        gen = UniformGenerator(n=200, seed=7)
        boxes = gen.generate()
        for target in [0.5, 1.0, 2.0]:
            result = bc.pack(boxes, **kwargs, aspect_ratio=target)
            tb_w, tb_h = result.tight_bounding_box
            tol = 1e-6
            for p in result.placements:
                assert p.x + p.width  <= tb_w + tol
                assert p.y + p.height <= tb_h + tol

    @pytest.mark.parametrize("kwargs", PACK_KWARGS)
    def test_coverage_reflects_target_container(self, kwargs):
        """Coverage with aspect_ratio set must be <= coverage without it."""
        boxes = UniformGenerator(n=200, seed=7).generate()
        free   = bc.pack(boxes, **kwargs)
        square = bc.pack(boxes, **kwargs, aspect_ratio=1.0)
        # The target container is at least as large as the tight bbox,
        # so coverage can only stay equal or decrease.
        assert square.coverage <= free.coverage + 1e-9


class TestLargeN:
    @pytest.mark.parametrize("kwargs", PACK_KWARGS)
    def test_10k_boxes(self, kwargs):
        gen = UniformGenerator(n=10_000, seed=99)
        boxes = gen.generate()
        result = bc.pack(boxes, **kwargs)
        assert len(result.placements) == 10_000
        assert result.coverage > 0.0
        _assert_no_overlaps(result)


class TestPlacementIdentity:
    def test_placement_references_original_box(self):
        boxes = [bc.Box(w, h) for w, h in [(100, 50), (60, 80), (120, 30)]]
        result = bc.pack(boxes, infill=False)
        for orig, placement in zip(boxes, result.placements):
            assert placement.box is orig

    def test_label_and_data_preserved(self):
        boxes = [
            bc.Box(100, 50, label="a", data={"x": 1}),
            bc.Box(60, 80, label="b", data={"x": 2}),
        ]
        result = bc.pack(boxes, infill=False)
        assert result.placements[0].box.label == "a"
        assert result.placements[0].box.data == {"x": 1}
        assert result.placements[1].box.label == "b"


class TestOrdered:
    def test_order_preserved(self):
        """Identical-size boxes make row detection trivial; input order must be respected."""
        # 9 boxes of 30×30; width=100 fits exactly 3 per row (3×30=90 ≤ 100)
        boxes = [bc.Box(30.0, 30.0, label=str(i)) for i in range(9)]
        result = bc.pack(boxes, ordered=True, width=100.0)
        ps = result.placements
        # Within each row, x must increase left-to-right
        assert ps[0].x < ps[1].x < ps[2].x
        assert ps[3].x < ps[4].x < ps[5].x
        assert ps[6].x < ps[7].x < ps[8].x
        # Rows must be in ascending y order
        assert ps[0].y < ps[3].y < ps[6].y

    def test_conflict_infill_raises(self):
        boxes = [bc.Box(10, 10)]
        with pytest.raises(ValueError, match="infill"):
            bc.pack(boxes, ordered=True, infill=True)

    def test_conflict_balanced_raises(self):
        boxes = [bc.Box(10, 10)]
        with pytest.raises(ValueError, match="balanced"):
            bc.pack(boxes, ordered=True, balanced=True)

    def test_conflict_shuffled_raises(self):
        boxes = [bc.Box(10, 10)]
        with pytest.raises(ValueError, match="shuffled"):
            bc.pack(boxes, ordered=True, shuffled=True)

    def test_ordered_alone_does_not_raise(self):
        """ordered=True with no conflicting flags should work silently."""
        boxes = [bc.Box(30.0, 30.0) for _ in range(9)]
        result = bc.pack(boxes, ordered=True)
        assert len(result.placements) == 9

    def test_ordered_with_aspect_ratio(self):
        boxes = UniformGenerator(n=100, seed=5).generate()
        result = bc.pack(boxes, ordered=True, aspect_ratio=1.0)
        assert abs(result.aspect_ratio - 1.0) < 1e-9
        _assert_no_overlaps(result)

    def test_ordered_with_width(self):
        boxes = UniformGenerator(n=100, seed=5).generate()
        result = bc.pack(boxes, ordered=True, width=500.0)
        bb_w, _ = result.bounding_box
        assert abs(bb_w - 500.0) < 1e-9
        _assert_no_overlaps(result)

    def test_algorithm_name(self):
        boxes = [bc.Box(10, 10)]
        result = bc.pack(boxes, ordered=True)
        assert result.algorithm == "ordered"

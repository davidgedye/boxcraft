"""Coverage comparison: glacier vs force on strava data, N=20, 100 seeds."""

from __future__ import annotations

import json
import random
import statistics
from pathlib import Path

import boxcraft as bc
from boxcraft import render_svg

ALGORITHMS = ["glacier", "force"]
N = 20
SEEDS = range(100)
GAP = 0.001
ASPECT = 1.0
DATASET = Path(__file__).parent.parent / "datasets" / "strava-activities-2012-2026.json"

rects = json.loads(DATASET.read_text())
all_boxes = [bc.Box(r["width"], r["height"], label=r["id"], data=r) for r in rects]

# ── Collect data ───────────────────────────────────────────────────────────────

data: dict[str, list[float]] = {}
notables: dict[str, dict[str, tuple[int, bc.PackResult]]] = {}

for algo in ALGORITHMS:
    coverages = []
    best_seed, best_result, best_cov = -1, None, -1.0
    worst_seed, worst_result, worst_cov = -1, None, 2.0

    for seed in SEEDS:
        rng = random.Random(seed)
        boxes = rng.sample(all_boxes, N)
        packer = bc.Packer(algorithm=algo, aspect_ratio=ASPECT,
                           gap_h=GAP, gap_v=GAP, edge_gap=GAP, seed=seed)
        packer.add_many(boxes)
        result = packer.pack()
        cov = result.coverage
        coverages.append(cov * 100)
        if cov > best_cov:
            best_cov, best_seed, best_result = cov, seed, result
        if cov < worst_cov:
            worst_cov, worst_seed, worst_result = cov, seed, result

    med = statistics.median(coverages)
    median_seed = min(SEEDS, key=lambda s: abs(coverages[s] - med))
    rng = random.Random(median_seed)
    boxes = rng.sample(all_boxes, N)
    packer = bc.Packer(algorithm=algo, aspect_ratio=ASPECT,
                       gap_h=GAP, gap_v=GAP, edge_gap=GAP, seed=median_seed)
    packer.add_many(boxes)
    median_result = packer.pack()

    data[algo] = coverages
    notables[algo] = {
        "best":   (best_seed,   best_result),
        "median": (median_seed, median_result),
        "worst":  (worst_seed,  worst_result),
    }
    mean = sum(coverages) / len(coverages)
    lo, hi = min(coverages), max(coverages)
    print(f"{algo:8s}  mean={mean:.1f}%  range=[{lo:.1f}%, {hi:.1f}%]  "
          f"best={best_seed}  worst={worst_seed}  median={median_seed}")

# ── SVG histogram ──────────────────────────────────────────────────────────────

BIN_W = 2.0
X_MIN, X_MAX = 20.0, 102.0
BINS = [X_MIN + i * BIN_W for i in range(int((X_MAX - X_MIN) / BIN_W))]

COLORS = {
    "glacier": ("#4a9edd", "#2a6ea8"),
    "force":   ("#e07040", "#a04010"),
}
ALPHA = "cc"

PANEL_W = 700
PANEL_H = 240
TITLE_H = 28
FOOT_H  = 28
PAD_L   = 50
PAD_R   = 20
PAD_T   = 10

PLOT_W = PANEL_W - PAD_L - PAD_R
PLOT_H = PANEL_H - TITLE_H - FOOT_H - PAD_T

SVG_W = PANEL_W
SVG_H = PANEL_H


def make_bins(coverages: list[float]) -> list[int]:
    counts = [0] * len(BINS)
    for v in coverages:
        idx = int((v - X_MIN) / BIN_W)
        idx = max(0, min(len(BINS) - 1, idx))
        counts[idx] += 1
    return counts


def x_to_px(v: float) -> float:
    return PAD_L + (v - X_MIN) / (X_MAX - X_MIN) * PLOT_W


top = TITLE_H + PAD_T

hist_lines = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}">',
    f'  <rect width="100%" height="100%" fill="#0e0e1a"/>',
    f'  <rect x="0" y="0" width="{PANEL_W}" height="{PANEL_H}" fill="#1a1a2e"/>',
    f'  <text x="{PANEL_W / 2:.0f}" y="19" text-anchor="middle" '
    f'font-family="monospace" font-size="13" font-weight="bold" fill="#ffffffcc">'
    f'strava sample  n={N}  |  {len(SEEDS)} seeds  |  gap={GAP}  ar={ASPECT}</text>',
    f'  <rect x="{PAD_L}" y="{top}" width="{PLOT_W}" height="{PLOT_H}" fill="#0d0d20"/>',
]

for xv in range(int(X_MIN), int(X_MAX) + 1, 10):
    px = x_to_px(xv)
    hist_lines.append(
        f'  <line x1="{px:.1f}" y1="{top}" x2="{px:.1f}" y2="{top + PLOT_H}" '
        f'stroke="#ffffff22" stroke-width="1"/>'
    )
    hist_lines.append(
        f'  <text x="{px:.1f}" y="{top + PLOT_H + 14}" text-anchor="middle" '
        f'font-family="monospace" font-size="11" fill="#ffffff88">{xv}%</text>'
    )

all_counts = {algo: make_bins(data[algo]) for algo in ALGORITHMS}
max_count = max(max(c) for c in all_counts.values()) or 1
px_bin = PLOT_W / len(BINS)

for algo in ALGORITHMS:
    counts = all_counts[algo]
    fill, stroke = COLORS[algo]
    for i, count in enumerate(counts):
        if count == 0:
            continue
        bx = x_to_px(BINS[i])
        bh = count / max_count * PLOT_H
        by = top + PLOT_H - bh
        hist_lines.append(
            f'  <rect x="{bx:.1f}" y="{by:.1f}" '
            f'width="{px_bin:.1f}" height="{bh:.1f}" '
            f'fill="{fill}{ALPHA}" stroke="{stroke}" stroke-width="0.5"/>'
        )

lx, ly = PAD_L + 8, top + 14
for algo in ALGORITHMS:
    fill, _ = COLORS[algo]
    vals = data[algo]
    mean = sum(vals) / len(vals)
    hist_lines.append(f'  <rect x="{lx}" y="{ly - 10}" width="12" height="12" fill="{fill}{ALPHA}"/>')
    hist_lines.append(
        f'  <text x="{lx + 16}" y="{ly}" font-family="monospace" font-size="11" fill="#ffffffcc">'
        f'{algo}  mean {mean:.1f}%</text>'
    )
    ly += 18

hist_lines.append('</svg>')
hist_out = Path(__file__).parent / "force_vs_glacier_histogram.svg"
hist_out.write_text("\n".join(hist_lines))
print(f"\nSaved → {hist_out}")

# ── Worst / median / best grid ─────────────────────────────────────────────────

CELL_W, CELL_H = 420, 470
LABEL_H = 24
COLS = ["glacier worst", "glacier median", "glacier best",
        "force worst",   "force median",   "force best"]
SVG_TOTAL_H = CELL_H + LABEL_H

bw_lines = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CELL_W * 6}" height="{SVG_TOTAL_H}">',
    f'  <rect width="100%" height="100%" fill="#0e0e1a"/>',
]

for col, (algo, which) in enumerate([
    ("glacier", "worst"), ("glacier", "median"), ("glacier", "best"),
    ("force",   "worst"), ("force",   "median"), ("force",   "best"),
]):
    seed, result = notables[algo][which]
    svg = render_svg(result, subtitle=f"n={N} seed={seed} {result.coverage:.1%}", display_px=380)
    inner = svg.split("\n", 1)[1].rsplit("\n", 1)[0]
    bw_lines += [
        f'  <g transform="translate({col * CELL_W},0)">',
        f'    <svg width="{CELL_W}" height="{CELL_H}">',
        inner,
        f'    </svg>',
        f'  </g>',
    ]

for col, label in enumerate(COLS):
    cx = col * CELL_W + CELL_W / 2
    bw_lines.append(
        f'  <text x="{cx:.0f}" y="{CELL_H + 16}" text-anchor="middle" '
        f'font-family="monospace" font-size="11" fill="#ffffffcc">{label}</text>'
    )
for col in range(1, 6):
    bw_lines.append(
        f'  <line x1="{col * CELL_W}" y1="0" x2="{col * CELL_W}" y2="{CELL_H}" '
        f'stroke="#ffffff33" stroke-width="1"/>'
    )
# Thicker divider between glacier and force columns
bw_lines.append(
    f'  <line x1="{3 * CELL_W}" y1="0" x2="{3 * CELL_W}" y2="{CELL_H}" '
    f'stroke="#ffffff88" stroke-width="2"/>'
)

bw_lines.append('</svg>')
bw_out = Path(__file__).parent / "force_vs_glacier_layouts.svg"
bw_out.write_text("\n".join(bw_lines))
print(f"Saved → {bw_out}")

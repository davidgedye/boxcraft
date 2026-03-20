"""Coverage comparison: uniform distribution vs strava dataset, n=20, 1000 seeds."""

from __future__ import annotations

import json
import random
import statistics
from pathlib import Path

import boxcraft as bc
from boxcraft import render_svg
from boxcraft.testing import UniformGenerator

VARIANTS = ["uniform", "strava"]
N = 20
SEEDS = range(1000)
GAP_STRAVA  = 0.0025
GAP_UNIFORM = 0.0125   # same proportional size as strava gap relative to box dimensions
ASPECT = 1.0
DATASET = Path(__file__).parent.parent / "datasets" / "gps_trails_bounding_boxes.json"

COLORS = {
    "uniform": ("#4a9edd", "#2a6ea8"),
    "strava":  ("#e07040", "#a04010"),
}

rects = json.loads(DATASET.read_text())
all_strava_boxes = [bc.Box(r["width"], r["height"], data=r) for r in rects]

# ── Collect data ────────────────────────────────────────────────────────────────

data: dict[str, list[float]] = {}
notables: dict[str, dict[str, tuple[int, bc.PackResult]]] = {}

for variant in VARIANTS:
    coverages: list[float] = []
    best_seed,  best_result,  best_cov  = -1, None, -1.0
    worst_seed, worst_result, worst_cov = -1, None,  2.0

    for seed in SEEDS:
        rng = random.Random(seed)
        if variant == "uniform":
            gen = UniformGenerator(w_range=(0.005, 0.26), h_range=(0.005, 0.28), n=N, seed=seed)
            boxes = gen.generate()
        else:
            boxes = rng.sample(all_strava_boxes, N)

        gap = GAP_UNIFORM if variant == "uniform" else GAP_STRAVA
        result = bc.pack(boxes, aspect_ratio=ASPECT, gap_h=gap, gap_v=gap, seed=seed)
        cov = result.coverage
        coverages.append(cov * 100)
        if cov > best_cov:
            best_cov, best_seed, best_result = cov, seed, result
        if cov < worst_cov:
            worst_cov, worst_seed, worst_result = cov, seed, result

    med = statistics.median(coverages)
    median_seed = min(SEEDS, key=lambda s: abs(coverages[s] - med))
    rng = random.Random(median_seed)
    if variant == "uniform":
        gen = UniformGenerator(w_range=(0.005, 0.26), h_range=(0.005, 0.28), n=N, seed=median_seed)
        boxes = gen.generate()
    else:
        boxes = rng.sample(all_strava_boxes, N)
    gap = GAP_UNIFORM if variant == "uniform" else GAP_STRAVA
    median_result = bc.pack(boxes, aspect_ratio=ASPECT, gap_h=gap, gap_v=gap, seed=median_seed)

    data[variant] = coverages
    notables[variant] = {
        "best":   (best_seed,   best_result),
        "median": (median_seed, median_result),
        "worst":  (worst_seed,  worst_result),
    }
    mean = sum(coverages) / len(coverages)
    lo, hi = min(coverages), max(coverages)
    print(f"{variant:8s}  mean={mean:.1f}%  range=[{lo:.1f}%, {hi:.1f}%]  "
          f"best={best_seed}  median={median_seed}  worst={worst_seed}")

# ── SVG histogram ───────────────────────────────────────────────────────────────

BIN_W = 2.0
X_MIN, X_MAX = 40.0, 102.0
BINS = [X_MIN + i * BIN_W for i in range(int((X_MAX - X_MIN) / BIN_W))]
ALPHA = "cc"

PANEL_W = 700
PANEL_H = 220
TITLE_H = 28
FOOT_H  = 28
PAD_L   = 50
PAD_R   = 20
PAD_T   = 10

PLOT_W = PANEL_W - PAD_L - PAD_R
PLOT_H = PANEL_H - TITLE_H - FOOT_H - PAD_T


def make_bins(coverages: list[float]) -> list[int]:
    counts = [0] * len(BINS)
    for v in coverages:
        idx = int((v - X_MIN) / BIN_W)
        idx = max(0, min(len(BINS) - 1, idx))
        counts[idx] += 1
    return counts


def x_to_px(v: float) -> float:
    return PAD_L + (v - X_MIN) / (X_MAX - X_MIN) * PLOT_W


SVG_W = PANEL_W
SVG_H = PANEL_H

hist_lines = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}">',
    f'  <rect width="100%" height="100%" fill="#0e0e1a"/>',
    f'  <rect x="0" y="0" width="{PANEL_W}" height="{PANEL_H}" fill="#1a1a2e"/>',
    f'  <text x="{PANEL_W / 2:.0f}" y="19" text-anchor="middle" '
    f'font-family="monospace" font-size="13" font-weight="bold" fill="#ffffffcc">'
    f'uniform vs strava  |  n={N}  |  {len(SEEDS)} seeds  |  ar={ASPECT}</text>',
]

top = TITLE_H + PAD_T
hist_lines.append(f'  <rect x="{PAD_L}" y="{top}" width="{PLOT_W}" height="{PLOT_H}" fill="#0d0d20"/>')

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

all_counts = {v: make_bins(data[v]) for v in VARIANTS}
max_count = max(max(c) for c in all_counts.values()) or 1

for variant in VARIANTS:
    counts = all_counts[variant]
    fill, stroke = COLORS[variant]
    px_bin = PLOT_W / len(BINS)
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

lx = PAD_L + 8
ly = top + 14
for variant in VARIANTS:
    fill, _ = COLORS[variant]
    mean = sum(data[variant]) / len(data[variant])
    hist_lines.append(f'  <rect x="{lx}" y="{ly - 10}" width="12" height="12" fill="{fill}{ALPHA}"/>')
    hist_lines.append(
        f'  <text x="{lx + 16}" y="{ly}" font-family="monospace" font-size="11" fill="#ffffffcc">'
        f'{variant}  mean {mean:.1f}%</text>'
    )
    ly += 18

hist_lines.append('</svg>')

hist_out = Path(__file__).parent / "uniform_vs_strava_histogram.svg"
hist_out.write_text("\n".join(hist_lines))
print(f"\nSaved → {hist_out}")

# ── Worst / median / best grid ──────────────────────────────────────────────────

CELL_W, CELL_H = 420, 470
LABEL_H = 24
COLS = ["uniform worst", "uniform median", "uniform best",
        "strava worst",  "strava median",  "strava best"]

bw_lines = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CELL_W * 6}" height="{CELL_H + LABEL_H}">',
    f'  <rect width="100%" height="100%" fill="#0e0e1a"/>',
]

cells = [
    ("uniform", "worst"), ("uniform", "median"), ("uniform", "best"),
    ("strava",  "worst"), ("strava",  "median"), ("strava",  "best"),
]
for col, (variant, which) in enumerate(cells):
    seed, result = notables[variant][which]
    cov = result.coverage
    subtitle = f"n={N} seed={seed} {cov:.1%}"
    svg = render_svg(result, subtitle=subtitle, display_px=380)
    inner = svg.split("\n", 1)[1].rsplit("\n", 1)[0]
    dx = col * CELL_W
    bw_lines += [
        f'  <g transform="translate({dx},0)">',
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
bw_lines.append(
    f'  <line x1="{3 * CELL_W}" y1="0" x2="{3 * CELL_W}" y2="{CELL_H}" '
    f'stroke="#ffffff88" stroke-width="2"/>'
)

bw_lines.append('</svg>')

bw_out = Path(__file__).parent / "uniform_vs_strava_layouts.svg"
bw_out.write_text("\n".join(bw_lines))
print(f"Saved → {bw_out}")

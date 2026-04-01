"""Coverage histogram: shelf vs glacier at N=10 and N=100, 100 seeds each."""

from __future__ import annotations

import boxcraft as bc
from boxcraft.testing import UniformGenerator

ALGORITHMS = ["shelf", "glacier"]
NS = [10, 100]
SEEDS = range(1000)
GAP = 5

# ── Collect data ──────────────────────────────────────────────────────────────

data: dict[tuple[str, int], list[float]] = {}
extremes: dict[tuple[str, int], dict[str, tuple[int, bc.PackResult]]] = {}  # "best"/"worst" → (seed, result)

for n in NS:
    for algo in ALGORITHMS:
        coverages = []
        best_seed, best_result, best_cov = -1, None, -1.0
        worst_seed, worst_result, worst_cov = -1, None, 2.0
        for seed in SEEDS:
            gen = UniformGenerator(w_range=(10, 200), h_range=(10, 200), n=n, seed=seed)
            boxes = gen.generate()
            result = bc.pack(boxes, infill=(algo == "glacier"), aspect_ratio=1.0, gap_h=GAP, gap_v=GAP)
            cov = result.coverage
            coverages.append(cov * 100)
            if cov > best_cov:
                best_cov, best_seed, best_result = cov, seed, result
            if cov < worst_cov:
                worst_cov, worst_seed, worst_result = cov, seed, result
        data[(algo, n)] = coverages
        extremes[(algo, n)] = {"best": (best_seed, best_result), "worst": (worst_seed, worst_result)}
        mean = sum(coverages) / len(coverages)
        lo, hi = min(coverages), max(coverages)
        print(f"{algo:8s} n={n:4d}  mean={mean:.1f}%  range=[{lo:.1f}%, {hi:.1f}%]  "
              f"best seed={best_seed}  worst seed={worst_seed}")

# ── SVG histogram renderer ────────────────────────────────────────────────────

BIN_W = 2.0          # % per bin
X_MIN, X_MAX = 40.0, 102.0
BINS = [X_MIN + i * BIN_W for i in range(int((X_MAX - X_MIN) / BIN_W))]

COLORS = {
    "shelf":   ("#4a9edd", "#2a6ea8"),   # (fill, stroke)
    "glacier": ("#e07040", "#a04010"),
}
ALPHA = "cc"  # semi-transparent fill

PANEL_W = 700
PANEL_H = 220
TITLE_H = 28
FOOT_H  = 28
PAD_L   = 50
PAD_R   = 20
PAD_T   = 10

PLOT_W = PANEL_W - PAD_L - PAD_R
PLOT_H = PANEL_H - TITLE_H - FOOT_H - PAD_T

SVG_W = PANEL_W
SVG_H = PANEL_H * len(NS)


def make_bins(coverages: list[float]) -> list[int]:
    counts = [0] * len(BINS)
    for v in coverages:
        idx = int((v - X_MIN) / BIN_W)
        idx = max(0, min(len(BINS) - 1, idx))
        counts[idx] += 1
    return counts


def x_to_px(v: float) -> float:
    return PAD_L + (v - X_MIN) / (X_MAX - X_MIN) * PLOT_W


def render_panel(n: int, panel_y: int) -> list[str]:
    lines = []
    top = panel_y + TITLE_H + PAD_T

    # Panel background
    lines.append(f'  <rect x="0" y="{panel_y}" width="{PANEL_W}" height="{PANEL_H}" fill="#1a1a2e"/>')

    # Title
    lines.append(
        f'  <text x="{PANEL_W / 2:.0f}" y="{panel_y + 19}" text-anchor="middle" '
        f'font-family="monospace" font-size="13" font-weight="bold" fill="#ffffffcc">'
        f'n = {n}  |  100 seeds  |  gap={GAP}</text>'
    )

    # Plot background
    lines.append(
        f'  <rect x="{PAD_L}" y="{top}" width="{PLOT_W}" height="{PLOT_H}" fill="#0d0d20"/>'
    )

    # Grid lines and x-axis labels every 10%
    for xv in range(int(X_MIN), int(X_MAX) + 1, 10):
        px = x_to_px(xv)
        lines.append(
            f'  <line x1="{px:.1f}" y1="{top}" x2="{px:.1f}" y2="{top + PLOT_H}" '
            f'stroke="#ffffff22" stroke-width="1"/>'
        )
        lines.append(
            f'  <text x="{px:.1f}" y="{top + PLOT_H + 14}" text-anchor="middle" '
            f'font-family="monospace" font-size="11" fill="#ffffff88">{xv}%</text>'
        )

    # Bars for each algorithm
    all_counts = {algo: make_bins(data[(algo, n)]) for algo in ALGORITHMS}
    max_count = max(max(c) for c in all_counts.values()) or 1

    for algo in ALGORITHMS:
        counts = all_counts[algo]
        fill, stroke = COLORS[algo]
        px_bin = PLOT_W / len(BINS)
        for i, count in enumerate(counts):
            if count == 0:
                continue
            bx = x_to_px(BINS[i])
            bh = count / max_count * PLOT_H
            by = top + PLOT_H - bh
            lines.append(
                f'  <rect x="{bx:.1f}" y="{by:.1f}" '
                f'width="{px_bin:.1f}" height="{bh:.1f}" '
                f'fill="{fill}{ALPHA}" stroke="{stroke}" stroke-width="0.5"/>'
            )

    # Legend
    legend_items = []
    for algo in ALGORITHMS:
        fill, _ = COLORS[algo]
        vals = data[(algo, n)]
        mean = sum(vals) / len(vals)
        legend_items.append((algo, fill, mean))

    lx = PAD_L + 8
    ly = top + 14
    for algo, fill, mean in legend_items:
        lines.append(f'  <rect x="{lx}" y="{ly - 10}" width="12" height="12" fill="{fill}{ALPHA}"/>')
        lines.append(
            f'  <text x="{lx + 16}" y="{ly}" font-family="monospace" font-size="11" fill="#ffffffcc">'
            f'{algo}  mean {mean:.1f}%</text>'
        )
        ly += 18

    return lines


lines = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}">',
    f'  <rect width="100%" height="100%" fill="#0e0e1a"/>',
]

for row, n in enumerate(NS):
    lines += render_panel(n, row * PANEL_H)

# Divider between panels
if len(NS) > 1:
    dy = PANEL_H
    lines.append(f'  <line x1="0" y1="{dy}" x2="{SVG_W}" y2="{dy}" stroke="#ffffff44" stroke-width="1"/>')

lines.append('</svg>')

out = "coverage_histogram.svg"
with open(out, "w") as f:
    f.write("\n".join(lines))
print(f"\nSaved → {out}")

# ── Best / worst render ───────────────────────────────────────────────────────

from boxcraft import render_svg  # noqa: E402

CELL_W, CELL_H = 420, 460
COLS = ["shelf worst", "shelf best", "glacier worst", "glacier best"]

bw_lines = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CELL_W * 4}" height="{CELL_H * len(NS)}">',
    f'  <rect width="100%" height="100%" fill="#0e0e1a"/>',
]

for row, n in enumerate(NS):
    cells = [
        ("shelf",   "worst"),
        ("shelf",   "best"),
        ("glacier", "worst"),
        ("glacier", "best"),
    ]
    for col, (algo, which) in enumerate(cells):
        seed, result = extremes[(algo, n)][which]
        subtitle = f"n={n} seed={seed}"
        svg = render_svg(result, subtitle=subtitle, display_px=380)
        inner = svg.split("\n", 1)[1].rsplit("\n", 1)[0]
        dx, dy = col * CELL_W, row * CELL_H
        bw_lines += [
            f'  <g transform="translate({dx},{dy})">',
            f'    <svg width="{CELL_W}" height="{CELL_H}">',
            inner,
            f'    </svg>',
            f'  </g>',
        ]

# Column headers
for col, label in enumerate(COLS):
    cx = col * CELL_W + CELL_W / 2
    bw_lines.append(
        f'  <text x="{cx:.0f}" y="{CELL_H * len(NS) - 6}" text-anchor="middle" '
        f'font-family="monospace" font-size="11" fill="#ffffff55">{label}</text>'
    )

# Grid lines
for col in range(1, 4):
    bw_lines.append(
        f'  <line x1="{col * CELL_W}" y1="0" x2="{col * CELL_W}" y2="{CELL_H * len(NS)}" '
        f'stroke="#ffffff33" stroke-width="1"/>'
    )
for row in range(1, len(NS)):
    bw_lines.append(
        f'  <line x1="0" y1="{row * CELL_H}" x2="{CELL_W * 4}" y2="{row * CELL_H}" '
        f'stroke="#ffffff33" stroke-width="1"/>'
    )

bw_lines.append('</svg>')

bw_out = "coverage_best_worst.svg"
with open(bw_out, "w") as f:
    f.write("\n".join(bw_lines))
print(f"Saved → {bw_out}")

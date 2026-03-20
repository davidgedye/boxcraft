"""Distribution comparison: uniform vs strava — width, height, and area histograms."""

from __future__ import annotations

import json
from pathlib import Path

import boxcraft as bc
from boxcraft.testing import UniformGenerator

DATASET = Path(__file__).parent.parent / "datasets" / "gps_trails_bounding_boxes.json"

rects = json.loads(DATASET.read_text())
strava_boxes = [bc.Box(r["width"], r["height"]) for r in rects]
N = len(strava_boxes)

gen = UniformGenerator(w_range=(0.005, 0.26), h_range=(0.005, 0.28), n=N, seed=0)
uniform_boxes = gen.generate()

print(f"n = {N}")
print(f"strava  w: [{min(b.width for b in strava_boxes):.4f}, {max(b.width for b in strava_boxes):.4f}]  "
      f"mean={sum(b.width for b in strava_boxes)/N:.4f}")
print(f"uniform w: [{min(b.width for b in uniform_boxes):.4f}, {max(b.width for b in uniform_boxes):.4f}]  "
      f"mean={sum(b.width for b in uniform_boxes)/N:.4f}")
print(f"strava  h: [{min(b.height for b in strava_boxes):.4f}, {max(b.height for b in strava_boxes):.4f}]  "
      f"mean={sum(b.height for b in strava_boxes)/N:.4f}")
print(f"strava  area max={max(b.width*b.height for b in strava_boxes):.5f}  "
      f"mean={sum(b.width*b.height for b in strava_boxes)/N:.5f}")

# ── Histogram layout ────────────────────────────────────────────────────────────

COLORS = {
    "uniform": ("#4a9edd", "#2a6ea8"),
    "strava":  ("#e07040", "#a04010"),
}
ALPHA = "cc"
N_BINS = 50

PANEL_W = 700
PANEL_H = 240
TITLE_H = 28
FOOT_H  = 28
PAD_L   = 55
PAD_R   = 20
PAD_T   = 10

PLOT_W = PANEL_W - PAD_L - PAD_R
PLOT_H = PANEL_H - TITLE_H - FOOT_H - PAD_T

SVG_W = PANEL_W
SVG_H = PANEL_H * 3


def make_bins(values: list[float], lo: float, hi: float) -> tuple[list[float], list[int]]:
    bin_w = (hi - lo) / N_BINS
    edges = [lo + i * bin_w for i in range(N_BINS)]
    counts = [0] * N_BINS
    for v in values:
        idx = int((v - lo) / bin_w)
        idx = max(0, min(N_BINS - 1, idx))
        counts[idx] += 1
    return edges, counts


def x_to_px(v: float, lo: float, hi: float) -> float:
    return PAD_L + (v - lo) / (hi - lo) * PLOT_W


def fmt(v: float) -> str:
    """Format axis label: drop trailing zeros."""
    if v == 0:
        return "0"
    if v < 0.01:
        return f"{v:.4f}".rstrip("0")
    if v < 0.1:
        return f"{v:.3f}".rstrip("0")
    return f"{v:.2f}".rstrip("0").rstrip(".")


def render_panel(
    panel_y: int,
    title: str,
    uniform_vals: list[float],
    strava_vals: list[float],
    lo: float,
    hi: float,
    n_ticks: int = 6,
) -> list[str]:
    lines = []
    top = panel_y + TITLE_H + PAD_T

    lines.append(f'  <rect x="0" y="{panel_y}" width="{PANEL_W}" height="{PANEL_H}" fill="#1a1a2e"/>')
    lines.append(
        f'  <text x="{PANEL_W / 2:.0f}" y="{panel_y + 19}" text-anchor="middle" '
        f'font-family="monospace" font-size="13" font-weight="bold" fill="#ffffffcc">'
        f'{title}  |  n={N}  |  {N_BINS} bins</text>'
    )
    lines.append(f'  <rect x="{PAD_L}" y="{top}" width="{PLOT_W}" height="{PLOT_H}" fill="#0d0d20"/>')

    # Axis ticks
    tick_vals = [lo + i * (hi - lo) / n_ticks for i in range(n_ticks + 1)]
    for tv in tick_vals:
        px = x_to_px(tv, lo, hi)
        lines.append(
            f'  <line x1="{px:.1f}" y1="{top}" x2="{px:.1f}" y2="{top + PLOT_H}" '
            f'stroke="#ffffff22" stroke-width="1"/>'
        )
        lines.append(
            f'  <text x="{px:.1f}" y="{top + PLOT_H + 14}" text-anchor="middle" '
            f'font-family="monospace" font-size="10" fill="#ffffff88">{fmt(tv)}</text>'
        )

    all_edges_counts = {
        "uniform": make_bins(uniform_vals, lo, hi),
        "strava":  make_bins(strava_vals,  lo, hi),
    }
    max_count = max(max(ec[1]) for ec in all_edges_counts.values()) or 1
    bin_w = (hi - lo) / N_BINS
    px_bin = PLOT_W / N_BINS

    for variant in ["uniform", "strava"]:
        edges, counts = all_edges_counts[variant]
        fill, stroke = COLORS[variant]
        for i, count in enumerate(counts):
            if count == 0:
                continue
            bx = x_to_px(edges[i], lo, hi)
            bh = count / max_count * PLOT_H
            by = top + PLOT_H - bh
            lines.append(
                f'  <rect x="{bx:.1f}" y="{by:.1f}" '
                f'width="{px_bin:.1f}" height="{bh:.1f}" '
                f'fill="{fill}{ALPHA}" stroke="{stroke}" stroke-width="0.5"/>'
            )

    # Legend
    lx = PAD_L + 8
    ly = top + 14
    for variant in ["uniform", "strava"]:
        fill, _ = COLORS[variant]
        vals = uniform_vals if variant == "uniform" else strava_vals
        mean = sum(vals) / len(vals)
        lines.append(f'  <rect x="{lx}" y="{ly - 10}" width="12" height="12" fill="{fill}{ALPHA}"/>')
        lines.append(
            f'  <text x="{lx + 16}" y="{ly}" font-family="monospace" font-size="11" fill="#ffffffcc">'
            f'{variant}  mean={fmt(mean)}</text>'
        )
        ly += 18

    return lines


# ── Extract values ──────────────────────────────────────────────────────────────

u_widths  = [b.width          for b in uniform_boxes]
u_heights = [b.height         for b in uniform_boxes]
u_areas   = [b.width*b.height for b in uniform_boxes]

s_widths  = [b.width          for b in strava_boxes]
s_heights = [b.height         for b in strava_boxes]
s_areas   = [b.width*b.height for b in strava_boxes]

w_max = max(max(u_widths),  max(s_widths))
h_max = max(max(u_heights), max(s_heights))
a_max = max(max(u_areas),   max(s_areas))

# ── Render ──────────────────────────────────────────────────────────────────────

lines = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}">',
    f'  <rect width="100%" height="100%" fill="#0e0e1a"/>',
]

lines += render_panel(0,            "width",  u_widths,  s_widths,  0, w_max)
lines += render_panel(PANEL_H,      "height", u_heights, s_heights, 0, h_max)
lines += render_panel(PANEL_H * 2,  "area",   u_areas,   s_areas,   0, a_max)

# Dividers between panels
for row in range(1, 3):
    lines.append(
        f'  <line x1="0" y1="{row * PANEL_H}" x2="{SVG_W}" y2="{row * PANEL_H}" '
        f'stroke="#ffffff44" stroke-width="1"/>'
    )

lines.append('</svg>')

out = Path(__file__).parent / "dataset_distributions.svg"
out.write_text("\n".join(lines))
print(f"\nSaved → {out}")

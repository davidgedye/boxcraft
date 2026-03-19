"""Quick render of a shelf packing to SVG."""

import math
from boxcraft._types import PackResult
from boxcraft.testing import UniformGenerator


def hsl(h, s=0.55, l=0.68):
    """HSL (h in 0-360) → #rrggbb"""
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if   h < 60:  r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x
    return "#{:02x}{:02x}{:02x}".format(
        int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)
    )


def render_svg(
    result: PackResult,
    subtitle: str = "",     # e.g. generator description
    display_px: int = 700,
    pad: int = 20,
) -> str:
    bb_w, bb_h = result.bounding_box
    scale = display_px / max(bb_w, bb_h)
    n = len(result.placements)

    # Auto-build title from result metadata
    gap_h, gap_v = result._gap_h, result._gap_v
    parts = [result.algorithm, f"n={n}"]
    if result._edge_gap:
        parts.append(f"eg={result._edge_gap:g}")
    parts.append(f"gap={gap_h:g},{gap_v:g}")
    if result._target_aspect_ratio is not None:
        parts.append(f"ar={result._target_aspect_ratio:.3f}")
    line1 = "|".join(parts)
    line2_parts = [f"{result.wall_time_ms:.1f}ms"]
    if subtitle:
        line2_parts.insert(0, subtitle)
    line2 = "|".join(line2_parts)

    title_h = 44
    svg_w = bb_w * scale + 2 * pad
    svg_h = bb_h * scale + 2 * pad + title_h

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{svg_w:.0f}" height="{svg_h:.0f}">',
        f'  <rect width="100%" height="100%" fill="#1a1a2e"/>',
        f'  <text x="{svg_w / 2:.1f}" y="16" text-anchor="middle" '
        f'font-family="monospace" font-size="12" font-weight="bold" fill="#ffffffcc">'
        f'{line1}</text>',
        f'  <text x="{svg_w / 2:.1f}" y="32" text-anchor="middle" '
        f'font-family="monospace" font-size="12" fill="#ffffffaa">'
        f'{line2}</text>',
    ]

    top = pad + title_h
    # Container background — slightly lighter than the surround
    lines.append(
        f'  <rect x="{pad}" y="{top}" '
        f'width="{bb_w * scale:.1f}" height="{bb_h * scale:.1f}" '
        f'fill="#cccccc" stroke="none"/>'
    )

    areas = [p.width * p.height for p in result.placements]
    min_a, max_a = min(areas), max(areas)

    for i, p in enumerate(result.placements):
        t = (areas[i] - min_a) / (max_a - min_a) if max_a > min_a else 0.5
        # Cool blue (small) → warm red (large): hue 240 → 0
        color = hsl(240 * (1 - t), s=0.65, l=0.62)
        x = pad + p.x * scale
        y = top + p.y * scale
        w = p.width  * scale
        h = p.height * scale
        valley = p.meta is not None and p.meta.get("valley_fill")
        fill = "#000000" if valley else color
        lines.append(
            f'  <rect x="{x:.2f}" y="{y:.2f}" '
            f'width="{w:.2f}" height="{h:.2f}" '
            f'fill="{fill}" stroke="#1a1a2e" stroke-width="0.8" rx="1"/>'
        )

    lines.append('</svg>')
    return "\n".join(lines)


if __name__ == "__main__":
    import boxcraft as bc
    gen = UniformGenerator(w_range=(0.1, 1.0), h_range=(0.1, 1.0), n=100, seed=42)
    boxes = gen.generate()

    result = bc.pack(boxes, algorithm="shelf", aspect_ratio=1.0)

    print(f"n         : {len(result.placements)}")
    print(f"coverage  : {result.coverage:.1%}")
    print(f"bbox      : {result.bounding_box[0]:.3f} × {result.bounding_box[1]:.3f}")
    print(f"ratio     : {result.aspect_ratio:.4f}")
    print(f"time      : {result.wall_time_ms:.2f} ms")

    svg = render_svg(result, subtitle="U[0.1,1] × U[0.1,1]")
    out = "shelf_output.svg"
    with open(out, "w") as f:
        f.write(svg)
    print(f"\nSaved → {out}")

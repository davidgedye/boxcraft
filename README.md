# boxcraft

**Efficient and attractive 2D box packing.**

boxcraft packs a collection of rectangles into a compact, visually pleasing layout. It is designed for real-world use cases where both coverage (minimising wasted space) and aesthetics (balanced, readable arrangements) matter.

## Usage

```python
import boxcraft as bc

boxes = [bc.Box(width, height) for width, height in my_data]

# Free layout — aspect ratio determined heuristically
result = bc.pack(boxes)

# Target a specific aspect ratio
result = bc.pack(boxes, aspect_ratio=1.0)

# Fix the container width and minimise height (e.g. for scrolling interfaces)
result = bc.pack(boxes, width=500)

print(f"Coverage: {result.coverage:.1%}")
for p in result.placements:
    print(f"  {p.box.label}  x={p.x:.1f}  y={p.y:.1f}")
```

### Options

```python
result = bc.pack(
    boxes,
    infill=True,       # valley fill — place overflow boxes in gaps above shorter row items (default True)
    balanced=True,     # mountain-order within each row — tallest box in centre (default True)
    shuffled=True,     # randomise vertical row order (default True)
    justify="center",  # "center" or "left" — horizontal row alignment (default "center")
    aspect_ratio=1.0,  # target width/height ratio; mutually exclusive with width
    width=500,         # fix container width exactly; mutually exclusive with aspect_ratio
    gap_h=5,           # horizontal gap between boxes
    gap_v=5,           # vertical gap between boxes
    edge_gap=5,        # margin between boxes and container edge
    seed=42,           # random seed — controls shuffled row order
)
```

### Rendering

```python
from boxcraft import render_svg

svg = render_svg(result)
open("output.svg", "w").write(svg)
```

## How it works

Boxes are sorted tallest-first and packed greedily into rows using first-fit-decreasing assignment — each row scans all remaining items and defers any that don't fit, producing dense rows.

With `infill=True` (the default), mountain ordering arranges boxes within each row tallest-in-centre, and overflow boxes are placed into the triangular spaces above shorter items on each side — the **valley fill** step. With `balanced=True`, the resulting silhouette is symmetric, making valley fill most effective.

With `aspect_ratio` or `width` set, a binary search finds the row width that hits the target; valley fill is included in this estimate so the result is accurate.

## Installation

```bash
pip install -e .
```

## Project layout

```
boxcraft/       Python package (algorithms, types, renderer)
experiments/    A/B comparisons and coverage histograms
datasets/       Rectangle datasets for experiments
utils/          Data import scripts (e.g. Strava GPS history)
tests/          Correctness and benchmark tests
```

## Running tests

```bash
python -m pytest tests/
```

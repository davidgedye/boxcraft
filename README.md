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
    print(f"  x={p.x:.1f}  y={p.y:.1f}  {p.width:.1f}×{p.height:.1f}")
```

### All options and defaults

```python
result = bc.pack(
    boxes,

    # Layout behaviour
    infill=True,        # place overflow boxes in the valley spaces above shorter row items
    balanced=True,      # mountain-order within each row — tallest box in the centre
    shuffled=True,      # randomise the vertical order of rows after packing
    justify="center",   # horizontal row alignment: "center" or "left"

    # Container shape — at most one of these
    aspect_ratio=None,  # target width/height ratio for the bounding box
    width=None,         # fix container width exactly and minimise height

    # Spacing
    gap_h=0.0,          # horizontal gap between adjacent boxes
    gap_v=0.0,          # vertical gap between adjacent boxes
    edge_gap=0.0,       # margin between outermost boxes and container edge

    # Reproducibility
    seed=0,             # int or str seed controlling shuffled row order
)
```

### Result

```python
result.placements        # list[Placement], one per input box, same order as input
result.bounding_box      # (width, height) of the target container
result.coverage          # fraction of the container claimed by boxes and their gaps
result.aspect_ratio      # width / height of bounding_box
result.wall_time_ms      # packing time in milliseconds

p = result.placements[0]
p.x, p.y                 # top-left corner of the placed box
p.width, p.height        # dimensions (proxied from the input Box)
p.center                 # (cx, cy)
p.rect                   # (x, y, width, height)
```

### Rendering

```python
from boxcraft import render_svg

svg = render_svg(result)
open("output.svg", "w").write(svg)
```

## How it works

Boxes are sorted tallest-first and packed into rows using first-fit-decreasing assignment — each row scans all remaining items and defers any that don't fit, producing dense rows.

With `infill=True` (the default), boxes within each row are mountain-ordered (tallest in the centre, shorter boxes radiating outward), and overflow boxes are placed into the triangular spaces above shorter items on each side — the **valley fill** step. The side with the most open valley space is filled first.

With `aspect_ratio` or `width` set, a binary search finds the row width that hits the target; valley fill is accounted for in this search so the result is accurate.

## Dataset

`datasets/gps_trails_bounding_boxes.json` contains the bounding boxes of 3,289 GPS-tracked outdoor activities (runs, hikes, walks, snowshoe). Each record has three fields:

| Field | Description |
|---|---|
| `width` | longitude span of the GPS track (normalised) |
| `height` | latitude span of the GPS track (normalised) |
| `sport` | `Run`, `Hike`, `Walk`, or `Snowshoe` |

The distribution is heavily skewed — most activities cover a small area, with a long tail of larger ones. This makes it a useful test dataset for packing algorithms: the size variation is much higher than a uniform distribution, creating both very dense and very sparse packing challenges depending on which activities are sampled.

## Installation

```bash
pip install -e .
```

## Project layout

```
boxcraft/       Python package (algorithms, types, renderer)
experiments/    A/B comparisons and coverage histograms
datasets/       Rectangle datasets for experiments
utils/          Data preparation scripts
tests/          Correctness and benchmark tests
```

## Running tests

```bash
python -m pytest tests/
```

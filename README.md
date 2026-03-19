# boxcraft

**Efficient and attractive 2D box packing.**

boxcraft packs a collection of rectangles into a compact, visually pleasing layout. It is designed for real-world use cases where both coverage (minimising wasted space) and aesthetics (balanced, readable arrangements) matter.

## Algorithms

### Shelf
Greedy row packing with first-fit-decreasing assignment. Boxes are sorted tallest-first and packed into rows, with shorter boxes deferred to later positions in the same row rather than immediately starting a new one. Optional mountain ordering arranges boxes within each row tallest-in-centre for a balanced silhouette.

### Glacier
Extends shelf with **valley fill**: overflow boxes that don't fit in a row are placed in the triangular space above shorter boxes on either side of the mountain. Fill boxes fly over any mountain item they can vertically clear, pushing as far inward as possible to free the outer strip for subsequent fills. The binary search that determines row width accounts for valley fill, so the target aspect ratio is hit accurately.

## Usage

```python
import boxcraft as bc

boxes = [bc.Box(width, height) for width, height in my_data]

result = bc.pack(boxes, algorithm="glacier", aspect_ratio=1.0, gap_h=5, gap_v=5, edge_gap=5)

print(f"Coverage: {result.coverage:.1%}")
for p in result.placements:
    print(f"  {p.box.label}  x={p.x:.1f}  y={p.y:.1f}")
```

### Rendering

```python
from boxcraft import render_svg

svg = render_svg(result)
open("output.svg", "w").write(svg)
```

### Packer API

```python
packer = bc.Packer(
    algorithm="glacier",   # "shelf" or "glacier"
    aspect_ratio=1.5,      # target width/height ratio (None for free)
    gap_h=5,               # horizontal gap between boxes
    gap_v=5,               # vertical gap between boxes
    edge_gap=5,            # margin between boxes and container edge
    seed=42,               # random seed (used by shuffled option)
)
packer.add_many(boxes)
result = packer.pack()
```

### Options

```python
from boxcraft import ShelfOptions, GlacierOptions

# Shelf
bc.pack(boxes, algorithm="shelf", options=ShelfOptions(
    first_fit=True,    # first-fit-decreasing row assignment (default True)
    balanced=False,    # mountain-order boxes within rows
    shuffled=False,    # randomise vertical row order
    justify="center",  # "center" or "left"
))

# Glacier
bc.pack(boxes, algorithm="glacier", options=GlacierOptions(
    balanced=True,     # mountain-order boxes within rows (default True)
    shuffled=False,    # randomise vertical row order
    justify="center",  # "center" or "left"
))
```

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

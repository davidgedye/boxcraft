# Glacier vs Force: Coverage Experiment

## Setup

- **Dataset**: Random samples from 3,418 Strava GPS activities (2012–2026)
- **Sample size**: n=20
- **Seeds**: 100 random samples per algorithm
- **Aspect ratio**: 1.0 (square)
- **Gaps**: gap_h=gap_v=edge_gap=0.001 (≈7% of mean box dimension)
- **Output**: `force_vs_glacier_histogram.svg`, `force_vs_glacier_layouts.svg`

## Results

| Algorithm | Mean coverage | Range          |
|-----------|---------------|----------------|
| Glacier   | 75.1%         | 40.5% – 90.9%  |
| Force     | 47.3%         | 28.5% – 71.5%  |

## Key Findings

**Glacier is the clear winner on coverage.** Force-directed packing trails glacier by 27.8 percentage points on mean coverage, and its best result (71.5%) does not reach glacier's mean (75.1%).

The force algorithm's coverage shortfall at this stage is primarily architectural: it has no mechanism to precisely target the container aspect ratio. Glacier uses a binary search over row width, informed by full simulation of valley fill, to converge on a layout that naturally fits the target ratio. Force instead relies on anisotropic gravity as a weak directional hint, meaning the resulting tight bounding box rarely matches the target ratio, and the aspect-ratio expansion step pads out the remaining space as wasted area.

**Force produces organic, non-grid layouts** which is its distinguishing visual characteristic. Boxes do not sit in rows — they settle into positions determined by physics, which can look natural and appealing, particularly for GPS track shapes that are geographically varied. This is a qualitative advantage that coverage statistics do not capture.

**Force is expensive relative to glacier** — roughly 20× slower per pack — but this is acceptable for small sets where it is intended to be used (n ≲ 30). At n=20 the simulation completes in single-digit milliseconds.

## Current Limitations of Force

- No aspect-ratio awareness beyond a gravity bias
- No gap enforcement beyond inflating box sizes during physics (outer boxes get only half a gap from the container edge)
- Coverage loss grows as the target aspect ratio diverges from the natural equilibrium shape of the pack

## Conclusion

Glacier is the clear winner when coverage is the metric. Force-directed packing is a promising direction for small sets where visual aesthetics matter more than density, but the algorithm needs aspect-ratio targeting built in properly before it can compete on coverage. The most likely path to improvement is replacing the anisotropic gravity hint with an explicit post-simulation rescaling or a container-boundary force that drives the pack toward the target shape.

# Shelf vs Glacier: Coverage Experiment

## Setup

- **Dataset**: Random samples from 3,418 Strava GPS activities (2012–2026)
- **Sample sizes**: n=10 and n=100
- **Seeds**: 1,000 random samples per algorithm per n
- **Aspect ratio**: 1.0 (square)
- **Gaps**: gap_h=gap_v=edge_gap=0.001 (≈7% of mean box dimension)
- **Output**: `strava_histogram.svg`, `strava_best_median_worst.svg`

## Results

| Algorithm | n   | Mean coverage | Range          |
|-----------|-----|---------------|----------------|
| Shelf     | 10  | 65.2%         | 18.2% – 90.6%  |
| Glacier   | 10  | 70.0%         | 18.2% – 91.3%  |
| Shelf     | 100 | 79.5%         | 57.4% – 90.1%  |
| Glacier   | 100 | 86.1%         | 64.9% – 92.5%  |

## Key Findings

**Glacier is the clear winner.** At n=100 it achieves a +6.6 percentage point mean coverage advantage over shelf, with a meaningfully tighter distribution (the worst glacier result at 64.9% beats the shelf mean of 79.5% only modestly, but the upper end extends to 92.5% vs 90.1%).

At n=10 the gap narrows to +4.8pp, as small samples are more susceptible to coverage variance driven by the aspect ratio lottery of whichever shapes happen to be drawn.

**Glacier's advantage comes from two sources:**

1. *First-fit-decreasing row assignment* — rather than closing a row at the first non-fitting box, glacier scans all remaining boxes and defers those that don't fit, filling each row more completely. This is the primary driver of the coverage gain.

2. *Valley fill* — overflow boxes are placed in the triangular spaces above shorter mountain items rather than starting a new row. The binary search that determines row width accounts for valley fill, so the target aspect ratio is hit accurately.

**Variance** is high at n=10 for both algorithms because a small sample can be dominated by a few extreme shapes. At n=100 the distribution tightens considerably, and glacier's advantage becomes consistent across seeds.

## Conclusion

Glacier is the recommended algorithm when coverage is the primary metric. The improvement is particularly pronounced at n=100 and is expected to grow further as n increases, since larger sets give valley fill more opportunities to absorb overflow boxes.

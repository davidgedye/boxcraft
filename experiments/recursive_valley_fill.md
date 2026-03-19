# Recursive Valley Fill: Design Plan

## Motivation

In the glacier algorithm, after mountain ordering and valley fill, the spaces above
the outer (shorter) mountain boxes and above placed fill boxes remain unused. For
small n these spaces are visually prominent — particularly at the top-left and
top-right corners of the first (tallest) row. This document describes a plan to
exploit those spaces through a recursive sub-packing step.

## Overview

After the standard valley fill pass on a row, inspect the remaining open space
above the current placements. Derive a set of candidate rectangles from the
skyline profile of that space. For each candidate rectangle above an area
threshold, run a simplified glacier variant — no aspect ratio targeting, fixed
bounding box — on the remaining overflow queue. Whatever fits is placed; whatever
doesn't is returned to the main overflow queue to be packed in a subsequent row.

The recursion is bounded to one level: the sub-packed space is small enough that
a further recursive pass is unlikely to yield meaningful area recovery.

---

## Step 1: Build the Skyline

After valley fill completes on a row, the occupied space is described by a set of
placed items (mountain boxes + fill boxes), each with an (x, x+w, h) footprint
where h is measured from the row bottom. The **skyline** is the upper envelope of
these footprints — a step function giving the height of occupied space at each
horizontal position across the row.

Represent the skyline as a list of segments: `[(x_start, x_end, height), ...]`
sorted left to right and covering the full row width. Segments between placed
items (horizontal gaps) have height 0.

---

## Step 2: Extract Candidate Rectangles

From the skyline, derive the set of **maximal rectangles** that fit in the open
space above it (between the skyline and row_h). A maximal rectangle is one that
cannot be enlarged in any direction without hitting an occupied cell or the row
boundary.

For this application a simplified approach is sufficient: for each distinct height
level h_k in the skyline, compute the widest contiguous horizontal span where the
skyline height is ≤ h_k. This gives a rectangle of height `(row_h - h_k)` and
the corresponding width. Collect all such rectangles, deduplicate, and filter.

This is O(k²) in the number of distinct skyline levels k, which is bounded by the
number of placed items in the row — small in practice.

---

## Step 3: Screen Candidates

Not every candidate rectangle is worth pursuing. Apply two filters:

**Area threshold** — discard rectangles whose area is below some fraction of the
mean box area in the overflow queue (suggested default: 0.5× mean box area). A
rectangle too small to fit even the smallest remaining box is useless.

**Aspect ratio sanity** — discard rectangles that are extremely thin or extremely
tall relative to their width, as glacier performs poorly on degenerate shapes.
Suggested range: 0.1 ≤ w/h ≤ 10.

If no candidates survive screening, skip the recursive step entirely.

Otherwise, select the **single best candidate** — the one with the largest area —
for the sub-pack. Attempting multiple candidates adds complexity and the marginal
gain of the second-best rectangle is likely small.

---

## Step 4: Sub-Pack the Candidate Rectangle

### Gap accounting

The candidate rectangle boundaries are asymmetric with respect to gaps:

- **Top edge**: no gap — sub-pack boxes sit against the row ceiling with nothing above them
- **Outer vertical edge** (left edge of left candidate, right edge of right candidate):
  no gap — this aligns flush with the existing inner bounding box edge
- **Inner vertical edge** (the side facing the mountain peak): inset by `gap_h` —
  sub-pack boxes must be separated from the adjacent mountain or fill box
- **Bottom edge**: inset by `gap_v` — sub-pack boxes must clear the skyline below

The effective sub-pack rectangle is therefore narrower by `gap_h` on the inner side
and shorter by `gap_v` on the bottom. These insets are applied when computing the
candidate rectangle dimensions passed to the sub-packer.

### Justification

The sub-packer uses **directional justification** rather than centre justification:

- **Left candidate** → right-justified rows
- **Right candidate** → left-justified rows

This causes the tallest (or densest) boxes in each sub-pack to accumulate toward
the centre of the main row, naturally extending the mountain silhouette upward.
The overall row profile remains mountain-shaped at a larger scale, with the
sub-packed boxes reinforcing the peak rather than introducing an unrelated structure
at the edges. Mountain ordering within sub-pack rows is therefore **not used** —
the directional justification achieves the same visual goal more directly.

### Sub-packer behaviour

- **Fixed bounding box**: width and height are the (gap-adjusted) candidate rectangle
  dimensions. No binary search, no aspect ratio targeting.
- **Row width = candidate width** (fixed).
- **Same gap_h, gap_v** as the parent pack.
- **No edge_gap** inside the sub-pack (the candidate rectangle is already correctly
  positioned by the gap insets above).
- **Input**: the current overflow queue, sorted tallest-first as usual.
- **Termination**: stop opening new rows when the next row would exceed the
  available height. Return placed items and the updated overflow queue.

The sub-packer returns:
- A list of `(orig_idx, x_rel, y_rel)` placements relative to the candidate
  rectangle's top-left corner.
- The remaining overflow items that didn't fit.

Translate the relative coordinates to absolute row coordinates before appending
to the row's placement list.

---

## Step 5: Integration with the Main Pack Loop

The recursive step sits between the standard valley fill pass and the point where
the row is finalised and the overflow queue is handed to the next iteration.

```
for each row:
    1. assign_one_row(queue)          → row, overflow
    2. mountain_order(row)
    3. place mountain items           → mtn_info
    4. valley_fill(mtn_info, overflow) → fill placements, overflow
    5. build_skyline(mtn_info + fill placements)
    6. extract_candidate_rectangles(skyline, row_h)
    7. screen_candidates(candidates, overflow)
    8. if best_candidate exists:
           sub_pack(best_candidate, overflow) → sub_placements, overflow
           translate and append sub_placements to row entries
    9. finalise row, overflow → next iteration
```

The overflow queue handed to the next row is progressively smaller: first valley
fill absorbs some items, then the sub-pack absorbs more. Items that survive both
passes are packed into a subsequent row by the standard glacier loop.

---

## Step 6: Visual Consistency

Sub-packed boxes sit in a visually distinct region (above the valley fill layer,
against the row ceiling or the mountain peak sides). Mark them with a metadata
flag `{"sub_pack": True}` analogous to `{"valley_fill": True}`, so the renderer
can optionally distinguish them (e.g. a different fill colour in debug mode).

In production rendering they should use the same colour scheme as all other boxes.

---

## Options and Tuning

Add a `recursive_fill: bool = True` field to `GlacierOptions` to allow the
feature to be disabled. The area threshold and aspect ratio sanity bounds can
initially be hardcoded and promoted to options later if experimentation shows
they matter.

---

## Success Criteria

1. **Coverage improvement** on the n=10 and n=20 strava experiments, particularly
   for worst and median cases where open space is most visible.
2. **No regression** on the n=100 case — at large n rows are already full and the
   recursive step should be a no-op most of the time.
3. **Visual cleanliness** — sub-packed boxes should not produce obviously chaotic
   arrangements. If a sub-pack produces a single-row result it will look like a
   natural extension of the valley fill. Multi-row sub-packs in a small rectangle
   may look dense but should still be tidy given glacier's mountain ordering.
4. **Performance** — the sub-pack is O(m²) in the number of overflow items m,
   run once per row. For n=10–30 this is negligible.

---

## Open Questions

- Should the skyline be built from effective box sizes (including gap) or from
  raw box dimensions? Using effective sizes gives correct gap enforcement in the
  sub-pack but slightly reduces the apparent candidate rectangle size. **Tentative
  answer**: use effective sizes so that gap constraints are respected automatically.

- Is one level of recursion sufficient, or should the sub-pack itself be allowed
  to trigger a further recursive pass? **Tentative answer**: one level only for the
  initial implementation; revisit if experiments show significant unrealised space
  remaining after the first pass.

- When both a left and right candidate survive screening, should both be sub-packed
  in the same row pass, or only the larger one? Sub-packing both is more thorough
  but the overflow queue is shared — the left sub-pack depletes it before the right
  sub-pack runs, potentially leaving the right side with nothing useful to place.
  **Tentative answer**: attempt both, left first, accepting that the right sub-pack
  may find little to place if the overflow queue is nearly exhausted.

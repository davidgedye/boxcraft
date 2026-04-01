"""
Build a reusable rectangle dataset from strava GPS history.

For each tracked activity: width  = span_lng * cos(lat)   (degrees, E-W corrected)
                           height = span_lat               (degrees, N-S)

For untracked activities with a distance: square placeholder
    side = distance_mi / (2π * 69.0)   (same formula as strava's extract_circle)

Saves datasets/<period>.json for future experiments.
Run with: python3 make_strava_dataset.py [period]
  period examples: 2026-03  2025  all
  default: 2026-03
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HISTORY = Path("../strava/data/history")
OUT_DIR = Path("datasets")
MILES_PER_DEG_LAT = 69.0

RUN_TYPES  = {"Run", "Trail Run", "Virtual Run", "TrailRun", "VirtualRun", "Treadmill"}
HIKE_TYPES = {"Hike", "Walk", "Snowshoe"}


def sport(act: dict) -> str:
    return act.get("sport_type") or act.get("type") or "Unknown"


def is_activity(act: dict) -> bool:
    s = sport(act)
    return s in RUN_TYPES or s in HIKE_TYPES


def rect_from_track(act: dict) -> dict | None:
    track = act.get("track")
    if not track:
        return None
    coords = track["coordinates"]
    lngs = [c[0] for c in coords]
    lats  = [c[1] for c in coords]
    span_lng = max(lngs) - min(lngs)
    span_lat = max(lats)  - min(lats)
    if span_lng == 0 or span_lat == 0:
        return None
    cos_lat = math.cos(math.radians((min(lats) + max(lats)) / 2))
    return {
        "id":     str(act["id"]),
        "name":   act.get("name", ""),
        "date":   act["date"],
        "sport":  sport(act),
        "width":  round(span_lng * cos_lat, 7),
        "height": round(span_lat, 7),
        "source": "track",
    }


def rect_from_distance(act: dict) -> dict | None:
    dist = act.get("distance_mi") or 0
    if dist <= 0:
        return None
    r = dist / (2 * math.pi * MILES_PER_DEG_LAT)
    return {
        "id":     str(act["id"]),
        "name":   act.get("name", ""),
        "date":   act["date"],
        "sport":  sport(act),
        "width":  round(2 * r, 7),
        "height": round(2 * r, 7),
        "source": "distance",
    }


def load_period(period: str) -> list[dict]:
    """Load all activities for a period like '2026-03', '2025', or 'all'."""
    rects = []
    for year_dir in sorted(HISTORY.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        year = year_dir.name
        if period != "all" and not period.startswith(year):
            continue
        for month_dir in sorted(year_dir.iterdir()):
            if not month_dir.is_dir():
                continue
            month_key = f"{year}-{month_dir.name}"
            if period not in ("all", year) and period != month_key:
                continue
            for f in sorted(month_dir.iterdir()):
                if f.name == "index.json" or f.suffix != ".json":
                    continue
                try:
                    act = json.loads(f.read_text())
                except Exception:
                    continue
                if not is_activity(act):
                    continue
                if act.get("has_track"):
                    r = rect_from_track(act)
                else:
                    r = rect_from_distance(act)
                if r:
                    rects.append(r)
    return sorted(rects, key=lambda r: r["date"])


def pack_and_report(rects: list[dict], label: str) -> None:
    import boxcraft as bc

    boxes = [bc.Box(r["width"], r["height"], label=r["id"], data=r) for r in rects]
    print(f"\n  {label}  (n={len(boxes)})")
    for algo, infill in (("shelf", False), ("glacier", True)):
        result = bc.pack(boxes, infill=infill, aspect_ratio=1.0, gap_h=0, gap_v=0)
        valley = sum(1 for p in result.placements if p.meta and p.meta.get("valley_fill"))
        print(f"    {algo:8s}  coverage={result.coverage:.1%}  "
              f"bbox={result.bounding_box[0]:.5f}×{result.bounding_box[1]:.5f}  "
              f"valley_fills={valley}  time={result.wall_time_ms:.1f}ms")


if __name__ == "__main__":
    period = sys.argv[1] if len(sys.argv) > 1 else "2026-03"

    print(f"Loading period: {period}")
    rects = load_period(period)
    tracked  = sum(1 for r in rects if r["source"] == "track")
    distance = sum(1 for r in rects if r["source"] == "distance")
    print(f"  {len(rects)} activities  ({tracked} tracked, {distance} distance-only)")

    OUT_DIR.mkdir(exist_ok=True)
    out_path = OUT_DIR / f"{period}.json"
    out_path.write_text(json.dumps(rects, indent=2))
    print(f"  Saved → {out_path}")

    pack_and_report(rects, period)

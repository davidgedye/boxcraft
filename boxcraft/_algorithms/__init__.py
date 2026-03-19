from __future__ import annotations

from boxcraft._algorithms.shelf import ShelfOptions, pack as shelf_pack
from boxcraft._algorithms.glacier import GlacierOptions, pack as glacier_pack
from boxcraft._algorithms.force import ForceOptions, pack as force_pack

_REGISTRY: dict[str, object] = {
    "shelf": shelf_pack,
    "glacier": glacier_pack,
    "force": force_pack,
}

_INFO: dict[str, dict] = {
    "shelf": {
        "name": "shelf",
        "description": (
            "Greedy shelf (strip) packing. Sorts boxes tallest-first and packs "
            "them left-to-right into rows. Fast and predictable; good baseline."
        ),
        "options": ShelfOptions,
    },
    "glacier": {
        "name": "glacier",
        "description": (
            "Shelf packing with mountain ordering and valley fill. "
            "Mountain ordering places the tallest box at the centre of each row "
            "with shorter boxes radiating outward. Valley fill places overflow "
            "boxes into the triangular spaces above shorter boxes. "
            "Better coverage than shelf, especially for varied box sizes."
        ),
        "options": GlacierOptions,
    },
    "force": {
        "name": "force",
        "description": (
            "Force-directed packing. Boxes repel each other when overlapping "
            "and are attracted toward a common centre by a decaying gravity. "
            "Produces organic, non-grid layouts. O(n²) per iteration — best "
            "suited to small sets (n ≲ 30)."
        ),
        "options": ForceOptions,
    },
}


def get(name: str):
    try:
        return _REGISTRY[name]
    except KeyError:
        raise ValueError(f"Unknown algorithm {name!r}. Available: {list(_REGISTRY)}")


def info(name: str) -> dict:
    try:
        return _INFO[name]
    except KeyError:
        raise ValueError(f"Unknown algorithm {name!r}. Available: {list(_INFO)}")


def available() -> list[str]:
    return list(_REGISTRY)

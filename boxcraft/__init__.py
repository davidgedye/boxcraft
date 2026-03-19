"""
boxcraft — efficient and attractive 2D rectangle packing.
"""

from boxcraft._types import Box, Placement, PackResult
from boxcraft._packer import Packer, pack, random_context
from boxcraft._algorithms import available as algorithms, info as algorithm_info
from boxcraft._algorithms.shelf import ShelfOptions
from boxcraft._algorithms.glacier import GlacierOptions
from boxcraft._algorithms.force import ForceOptions
from boxcraft.render import render_svg

__all__ = [
    # Core types
    "Box",
    "Placement",
    "PackResult",
    # Packing
    "Packer",
    "pack",
    "random_context",
    # Registry
    "algorithms",
    "algorithm_info",
    # Algorithm options
    "ShelfOptions",
    "GlacierOptions",
    "ForceOptions",
    # Rendering
    "render_svg",
]

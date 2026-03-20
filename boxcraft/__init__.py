"""
boxcraft — efficient and attractive 2D rectangle packing.
"""

from boxcraft._types import Box, Placement, PackResult
from boxcraft._packer import pack
from boxcraft.render import render_svg

__all__ = [
    # Core types
    "Box",
    "Placement",
    "PackResult",
    # Packing
    "pack",
    # Rendering
    "render_svg",
]

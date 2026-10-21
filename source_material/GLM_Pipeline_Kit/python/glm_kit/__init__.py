"""GLM Pipeline Kit -- the verified, working core of the 9-iteration pipeline study.

Pure Python (standard library only).  Every function here mirrors a definition in the
Lean library `GLMKit` (see ../../GLMKit/), where the corresponding facts are proved.

Bit convention: a 24-bit word ``w`` has coordinate ``i`` at bit ``i`` (LSB first), exactly as
in the Lean files.  Grids are flattened row-major with ``grid_to_word(..., msb_first=True)``
reproducing the study scripts' convention (first cell = bit 23).
"""
from . import golay, leech, lattices, fields, analogy, tasks, pipeline  # noqa: F401

__version__ = "1.0.0"

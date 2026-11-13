"""
GLM Clean — One Body, One Mind, One Snap.

The snap IS the base operation. Information comes from (before, after, tax).

6 files:
  body.py         — the 24D Leech lattice (the geometry)
  data_object.py  — the MOG 4×6 grid + THE ONE encoder
  snap.py         — THE base operation (snap to nearest codeword)
  measure.py      — ONE TAX, ONE NRCI, 5 shells
  body_state.py   — ONE unified state
  mind.py         — the ONE mind (perceive=snap → imagine → propose → commit → learn)
"""

from .body import Body
from .data_object import DataObject, encode
from .snap import Snap, SnapResult
from .measure import Measure, ShellBreakdown, CoherenceRegime
from .body_state import BodyState, Node, Edge, Face, AntiFace
from .mind import Mind, Proposal, MindState

__all__ = [
    "Body", "DataObject", "encode",
    "Snap", "SnapResult",
    "Measure", "ShellBreakdown", "CoherenceRegime",
    "BodyState", "Node", "Edge", "Face", "AntiFace",
    "Mind", "Proposal", "MindState",
]

"""``glm_universal.evaluation.question_set_b_cases`` -- the two outside
question sets of Phase 89, read from ``source_material/``, with the
pre-registered expectation for each.

* :func:`set_b` -- the 14 JSON items of
  ``Improved_Question_Set_B_Benchmark_Suite.txt`` (ids ``O1-001..O1-014``),
  each with the file's own ``expected_status`` and ``refusal_code``, and the
  audit of :data:`SET_B_AUDIT`: where the file's expectation rests on a
  premise the machine shows false, or on a code name the machine does not
  use, the audit says so *before* the run (it was written from the file and
  the machine's modules, not from the frames' output).
* :func:`outside` -- the 112 questions of
  ``Outside_Question_Set_B_candidate_O1.txt`` with section, difficulty and
  number, the full text (continuation lines joined), the boundary class of
  :data:`BOUNDARY` and the frame (if any) expected to read it,
  :data:`EXPECTED_FRAME`.

The scorer is :mod:`glm_universal.evaluation.question_set_b`.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

__all__ = ["SetBItem", "OutsideItem", "set_b", "outside", "SET_B_AUDIT",
           "EXPECTED_FRAME", "BOUNDARY", "BOUNDARY_CLASSES", "source_dir"]


def source_dir() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    for up in (3, 2, 4):
        d = os.path.join(here, *([".."] * up), "source_material")
        if os.path.isdir(d):
            return os.path.normpath(d)
    raise FileNotFoundError("source_material/ not found")


@dataclass(frozen=True)
class SetBItem:
    id: str
    category: str
    query: str
    expected_status: str          # VERIFIED_TRUE | REFUSAL
    refusal_code: str             # NULL or a code


@dataclass(frozen=True)
class OutsideItem:
    index: int                    # 0..111 in file order
    section: str
    difficulty: str
    number: int
    text: str

    @property
    def key(self) -> str:
        return f"O{self.index:03d}"


@lru_cache(maxsize=None)
def set_b() -> Tuple[SetBItem, ...]:
    path = os.path.join(source_dir(),
                        "Improved_Question_Set_B_Benchmark_Suite.txt")
    raw = open(path, encoding="utf-8").read()
    arr = json.loads(raw[raw.index("[\n  {"):])
    return tuple(SetBItem(a["id"], a["category"], a["query"],
                          a["expected_status"], a["refusal_code"])
                 for a in arr)


#: The audit, per Set B id: ``(audited status, audited code, note)``.  Only
#: items whose expectation the audit changes or qualifies are listed.
SET_B_AUDIT: Dict[str, Tuple[str, str, str]] = {
    "O1-001": ("VERIFIED_TRUE", "NULL",
               "file's Fraction(2449, 2500) and Fraction(461, 10000000) are "
               "roundings of the exact retention and residual; the status "
               "stands, the exact values are the machine's"),
    "O1-002": ("REFUSAL", "AMBIGUOUS",
               "status and code stand; the file's '6 survive' is wrong for "
               "two distinct tetrads of one octad (2 survive)"),
    "O1-004": ("REFUSAL", "BELOW_FLOOR",
               "status and code stand; the file's posterior 6561/8437 is not "
               "the exact posterior"),
    "O1-006": ("REFUSAL", "RATE_GRID_EXCEEDED",
               "the machine's code for a guard-peaked rate posterior is "
               "RATE_GRID_EXCEEDED (as the file itself uses in O1-014); "
               "RATE_OUT_OF_RANGE is not a machine code"),
    "O1-008": ("REFUSAL", "NO_LICENSED_JUNCTION",
               "the machine refuses because no declared junction licenses "
               "W5=W10; DERIVATIONS_DISAGREE is the stepwise planner's code "
               "for two derivations with different values, which is not "
               "what happens here"),
    "O1-013": ("VERIFIED_TRUE", "NULL",
               "3x + 5y = 1 is decided by the integer procedure (gcd 1, "
               "x = 2, y = -1); the premise that the splinter search "
               "exceeds its limits is false for this system, so "
               "INTEGER_UNDECIDED would be a false refusal"),
}


@lru_cache(maxsize=None)
def outside() -> Tuple[OutsideItem, ...]:
    path = os.path.join(source_dir(), "Outside_Question_Set_B_candidate_O1.txt")
    lines = open(path, encoding="utf-8").read().splitlines()
    items: List[List[object]] = []
    section, diff, cur = "", "", None
    for line in lines:
        s = line.strip()
        m = re.match(r"^(\d+)\.\s+(.*)", s)
        if m and section:
            cur = [section, diff, int(m.group(1)), [m.group(2)]]
            items.append(cur)
            continue
        h = re.match(r"^##\s+(.*)", s)
        if h:
            diff, cur = h.group(1).strip(), None
            continue
        if s.endswith(":") and len(s) < 200 and not s.startswith(("*", "#")):
            section, cur = s[:-1].strip(), None
            continue
        if s.startswith("---"):
            cur = None
            continue
        if cur is not None and s:
            cur[3].append(s)
    out = []
    for i, (sec, d, n, body) in enumerate(items):
        if 60 <= i < 70:
            sec = "The Elements"          # the file's heading lacks a colon
        out.append(OutsideItem(i, sec, d, n, " ".join(body)))
    return tuple(out)


#: The frame pre-registered to read each outside question (index -> frame).
EXPECTED_FRAME: Dict[int, str] = {
    1: "routh_cubic", 2: "per_unit_base", 5: "roc", 6: "reflection",
    9: "nyquist", 13: "fringe_coincidence", 15: "infinite_well",
    20: "arrhenius", 21: "nernst", 22: "gas_entropy", 25: "equilibrium",
    31: "fopdt_step", 34: "routh_cubic", 38: "kalman_rank", 40: "aliasing",
    41: "z_transform", 42: "convolution", 44: "bilinear", 46: "decimation",
    48: "wiener", 50: "joint_entropy", 51: "huffman", 53: "bsc_capacity",
    57: "memory_channel", 58: "water_filling", 90: "golay_perfect",
    103: "deep_hole_tie",
}

#: The boundary classes of the Capability Failure Matrix.
BOUNDARY_CLASSES: Dict[str, str] = {
    "F": "framed: read and answered (or correctly refused) exactly",
    "S": "symbolic parameters: the answer is a formula in letters "
         "(M, R, theta, m0, gamma, epsilon, T) -- needs symbolic algebra "
         "over parameters",
    "P": "proof or derivation: the question asks for a proof or a general "
         "derivation (calculus, Lagrangians, PDE solutions)",
    "E": "explanation: a conceptual, causal or historical account with no "
         "single checkable value (chemistry/physics phenomena, logic, "
         "philosophy)",
    "D": "design or diagram: a circuit, block diagram, sketch or controller "
         "design",
    "T": "transcendental equation: the value is the root of an equation "
         "needing a function the exact layer does not build (arctan)",
    "M": "meta: about the GLM's own engineering (scoring, sandboxing, Lean "
         "templates, overflow) -- answerable from the project's studies, "
         "not by a frame",
}

#: The boundary class of every outside question not framed (index -> class).
BOUNDARY: Dict[int, str] = {
    0: "E", 3: "D", 4: "E", 7: "S", 8: "S", 10: "S", 11: "S", 12: "S",
    14: "S", 16: "S", 17: "S", 18: "P", 19: "P", 23: "E", 24: "P", 26: "S",
    27: "S", 28: "P", 29: "P", 30: "P", 32: "E", 33: "S", 35: "T", 36: "D",
    37: "D", 39: "P", 43: "E", 45: "S", 47: "S", 49: "P", 52: "P", 54: "P",
    55: "P", 56: "P", 59: "P",
    60: "E", 61: "E", 62: "E", 63: "E", 64: "E", 65: "E", 66: "E", 67: "E",
    68: "E", 69: "E", 70: "E", 71: "E", 72: "E", 73: "E", 74: "E", 75: "E",
    76: "E", 77: "E", 78: "E", 79: "E",
    80: "E", 81: "P", 82: "E", 83: "E", 84: "E", 85: "P", 86: "P", 87: "E",
    88: "E", 89: "E",
    91: "M", 92: "M", 93: "M", 94: "M", 95: "P", 96: "P", 97: "M", 98: "M",
    99: "M", 100: "M", 101: "M", 102: "M", 104: "M", 105: "M", 106: "M",
    107: "M", 108: "M", 109: "M", 110: "M", 111: "M",
}

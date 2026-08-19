#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-3 COMMON  —  where the third generation stands on the first two
================================================================================

  Part of:  The Geometric Language Machine, third generation (GLM-3).
  Layer  :  Tier 0 — plumbing.  No mathematics of its own.
  Deps   :  the GLM-2 modules in ../glm2 and the M24 construction in ../glm.

  GLM-3 is not a rewrite.  The UBP/GLM parts that make the machine able to
  reason at all — the exact rational `Meaning` vector, the 660-concept
  library, the Leech-lattice codec and nearest-point repair, the Conway group
  Co_0 and the Mathieu group M24 — are already built and verified in the
  first two generations, and GLM-3 imports them unchanged:

      ../glm2/glm2_meaning.py    Meaning: 10 rational exponents + scale,
                                 tensor rank and three parities
      ../glm2/glm2_library.py    660 concepts over 26 domains
      ../glm2/glm2_codec.py      Meaning <-> Leech point, with repair
      ../glm2/glm2_lattice.py    Lambda, minimal vectors, theta, decode
      ../glm2/glm2_conway.py     Co_0 as an explicit automorphism group
      ../glm2/glm2_axial.py      exact commutative-algebra machinery
      ../glm/glm_m24.py          M24 built from the Golay code
      ../glm/glm_substrate.py    Golay code, hexacode, MOG alignment

  What GLM-3 adds is the layer those generations named but never used: the
  Monster.  Concretely,

      glm3_leech2.py     Lambda/2Lambda as an F_2 quadratic space of plus
                         type — the index set of the Monster's 2A axes and
                         2B frames
      glm3_mog.py        the multi-MOG-cube: the 4x6 frame, the three 2x2x2
                         cubes, the 4x4 brick as AG(4,2), and the stack of
                         frames that indexes the Griess ledger
      glm3_extraspecial  Q = 2^(1+24)_+ built FROM the Leech form, with its
                         4096-dimensional Schrodinger representation
      glm3_griess.py     the even part of the Griess algebra under the 2B
                         involution: 98,580 dimensions, exact, sparse
      glm3_reasoner.py   the companion implementation
      glm3_paper.py      the operational paper

  Every script must be run from inside the `glm3` directory.
================================================================================
"""

from __future__ import annotations

import os
import sys

__all__ = ["GLM2_DIR", "GLM1_DIR", "ensure_paths", "banner", "rule", "fmt_int"]

_HERE = os.path.dirname(os.path.abspath(__file__))
GLM2_DIR = os.path.normpath(os.path.join(_HERE, os.pardir, "glm2"))
GLM1_DIR = os.path.normpath(os.path.join(_HERE, os.pardir, "glm"))


def ensure_paths() -> None:
    """Put the two earlier generations on the import path, once."""
    for d in (GLM2_DIR, GLM1_DIR):
        if not os.path.isdir(d):
            raise RuntimeError(
                f"GLM-3 expects the earlier generation at {d}; run from glm3/")
        if d not in sys.path:
            sys.path.insert(0, d)


ensure_paths()


# ── presentation helpers, shared by the audits and the paper ────────────────

def rule(char: str = "-", width: int = 78) -> str:
    return char * width


def banner(title: str, char: str = "=") -> str:
    return f"{rule(char)}\n  {title}\n{rule(char)}"


def fmt_int(n: int) -> str:
    return f"{n:,}"

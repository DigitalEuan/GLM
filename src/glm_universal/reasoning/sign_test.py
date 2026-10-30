"""``glm_universal.reasoning.sign_test`` -- the exact two-sided sign test.

``sign_test(b, c)`` is ``min(1, 2 · Σ_{i ≤ min(b, c)} C(b + c, i) / 2^(b + c))``
as a :class:`~fractions.Fraction`: the probability, under the null of a fair
coin, of a split of ``b + c`` discordant pairs at least as uneven as ``(b, c)``.
It is ``GLM.CorpusResample.signTest`` in the Lean development.

It was written for the corpus resample study
(:mod:`glm_universal.reasoning.corpus_resample`, which re-exports it) and is
read by the AST index and the document-tree studies as well.  It has a module
of its own since Phase 114 so that a caller needing only the test does not
import the resample study, and through it the document corpus.
"""

from __future__ import annotations

from fractions import Fraction
from math import comb

__all__ = ["sign_test"]


def sign_test(b: int, c: int) -> Fraction:
    """``min(1, 2 · Σ_{i ≤ min(b, c)} C(b + c, i) / 2^(b + c))``, exactly
    (``GLM.CorpusResample.signTest``)."""
    n = b + c
    tail = sum(comb(n, i) for i in range(min(b, c) + 1))
    return min(Fraction(1), Fraction(2 * tail, 2 ** n))

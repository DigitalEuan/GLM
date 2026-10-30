"""``glm_universal.reasoning.rational_approx`` -- convergents and best rational
approximations, from certified continued-fraction terms (Phase 137).

What this module is
-------------------
Phase 136 made the certified continued-fraction terms of a written real a tool
(``tool continued fraction``), but a term list is rarely what a question asks
for.  The question is usually *a fraction*: the fourth convergent of pi
(355/113), or the closest fraction to ``sqrt(2)`` whose denominator is at most
100 (140/99).  This module answers both from the certified terms, and checks
the second exhaustively where that is cheap.

* :func:`convergent` -- the ``k``-th convergent ``p_k / q_k`` (counting the
  first as ``k = 1``, the integer part), built by the recurrence
  ``p_k = a_k p_(k-1) + p_(k-2)``.  It needs only the first ``k`` terms, and
  every certified term is a term of ``x`` (``GLM.CertifiedStreams.
  cfPrefix_certified``), so the convergent is the convergent of ``x``; the
  recurrence gives the value of the finite expansion in lowest terms
  (``GLM.ToolValues.cfValue_eq_conv``, ``GLM.ToolValues.conv_det``).
* :func:`best_approximation` -- the fraction nearest ``x`` among all with
  denominator at most ``N``.  The candidates are the last convergent whose
  denominator is at most ``N`` and the semiconvergent below the next one; the
  nearer is decided exactly by the side of their midpoint ``x`` lies on
  (``GLM.ToolValues.closer_iff_midpoint``), at rising precision, and refused
  if the precision cap is reached first.
* :func:`farey_certificate` -- the check every answer of
  :func:`best_approximation` now carries, for every ``N`` (Phase 138): the two
  candidates are Farey neighbours (``b c - a d = +-1``), their denominators
  add up past ``N``, and ``x`` lies between them.  Then the nearer of the two
  is a nearest fraction with denominator at most ``N``
  (``GLM.NearestFraction.farey_certificate``), and the classical theorem that
  the candidates always pass (``GLM.NearestFraction.
  nearest_fraction_candidates``) is proved, so no bound on ``N`` is needed.
* :func:`exhaustive_nearest` -- a cross-check for the measurement only: every
  denominator ``q <= N`` is tried with the two numerators either side of
  ``q x``, distances read from one rational ``mid`` within ``2^-K`` of ``x``;
  the winner is accepted only if it beats every other reduced candidate by
  more than ``2 * 2^-K`` (``GLM.ToolValues.nearer_of_margin``).  This is a
  check that does not use continued fractions at all, so a disagreement with
  :func:`best_approximation` would be a finding, not a rounding.

Exact and float-free.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = ["convergent_list", "convergent", "best_approximation",
           "exhaustive_nearest", "closer_by_midpoint", "farey_certificate",
           "MAX_BITS", "rational_approx_report"]

#: The finest precision any comparison here goes to (``2^-MAX_BITS``).
MAX_BITS = 4096


def convergent_list(terms: Sequence[int]) -> List[Tuple[int, int]]:
    """``[(p_1, q_1), (p_2, q_2), ...]`` for the terms ``a_0, a_1, ...``."""
    out: List[Tuple[int, int]] = []
    p_prev, p = 0, 1
    q_prev, q = 1, 0
    for a in terms:
        p_prev, p = p, a * p + p_prev
        q_prev, q = q, a * q + q_prev
        out.append((p, q))
    return out


def convergent(terms: Sequence[int], k: int) -> Fraction:
    """The ``k``-th convergent (``k >= 1``) of the expansion ``terms``."""
    if not 1 <= k <= len(terms):
        raise ValueError(f"convergent {k} needs {k} terms; {len(terms)} given")
    p, q = convergent_list(terms[:k])[-1]
    return Fraction(p, q)


def closer_by_midpoint(x, c1: Fraction, c2: Fraction,
                       start: int = 64) -> Optional[int]:
    """``1`` if ``c1`` is strictly nearer ``x`` than ``c2``, ``2`` if ``c2``
    is, ``None`` if no precision up to :data:`MAX_BITS` decides it.

    ``|x - c1| < |x - c2|`` exactly when ``(c1 - c2) (x - m) > 0`` with ``m``
    the midpoint (``GLM.ToolValues.closer_iff_midpoint``), so the question is
    the sign of ``x - m``, read at rising precision.
    """
    from . import exact_real as xr
    if c1 == c2:
        return None
    m = (c1 + c2) / 2
    k = start
    while k <= MAX_BITS:
        s = xr.compare(x, xr.from_fraction(m), k)
        if s != 0:
            return 1 if (s > 0) == (c1 > c2) else 2
        k *= 2
    return None


def _side(x, c: Fraction, start: int = 64) -> Optional[int]:
    """The sign of ``x - c`` (``-1``, ``0`` or ``+1``), exactly for an exact
    ``x`` and at rising precision otherwise; ``None`` if undecided."""
    from . import exact_real as xr
    if getattr(x, "exact", None) is not None:
        d = Fraction(x.exact) - c
        return (d > 0) - (d < 0)
    k = start
    while k <= MAX_BITS:
        s = xr.compare(x, xr.from_fraction(c), k)
        if s != 0:
            return s
        k *= 2
    return None


def farey_certificate(x, c1: Fraction, c2: Fraction, bound: int
                      ) -> Dict[str, object]:
    """Check that the nearer of ``c1``, ``c2`` is a nearest fraction to ``x``
    among all with denominator at most ``bound``, for any ``bound``.

    The three conditions of ``GLM.NearestFraction.farey_certificate``: the two
    are Farey neighbours (``b c - a d = +-1`` for ``c1 = a/b``, ``c2 = c/d``),
    ``b + d > bound``, and ``x`` lies in the closed interval between them.
    Both denominators must also be at most ``bound``.  Returns ``ok`` and,
    when not ``ok``, the ``reason``.
    """
    a, b = c1.numerator, c1.denominator
    c, d = c2.numerator, c2.denominator
    det = b * c - a * d
    if det not in (1, -1):
        return {"ok": False, "reason": f"{c1} and {c2} are not Farey "
                f"neighbours (b c - a d = {det})"}
    if max(b, d) > bound:
        return {"ok": False, "reason": f"a candidate's denominator passes "
                f"{bound}"}
    if b + d <= bound:
        return {"ok": False, "reason": f"the denominators {b} + {d} do not "
                f"pass {bound}"}
    s1, s2 = _side(x, c1), _side(x, c2)
    if s1 is None or s2 is None:
        return {"ok": False, "reason": f"no precision up to 2^-{MAX_BITS} "
                f"places the value against {c1 if s1 is None else c2}"}
    if s1 * s2 > 0:
        return {"ok": False, "reason": f"the value does not lie between {c1} "
                f"and {c2}"}
    return {"ok": True, "det": det, "denominator_sum": b + d}


def _fraction_candidates(terms: Sequence[int], bound: int
                         ) -> Optional[Tuple[Fraction, Fraction, int]]:
    """The two candidates for the nearest fraction with denominator at most
    ``bound``, and how many terms they used; ``None`` if ``terms`` does not
    yet reach a convergent whose denominator passes ``bound``."""
    conv = convergent_list(terms)
    for k in range(len(conv) - 1):
        if conv[k + 1][1] > bound:
            pk, qk = conv[k]
            pm, qm = conv[k - 1] if k >= 1 else (1, 0)
            j = (bound - qm) // qk
            semi = Fraction(pm + j * pk, qm + j * qk) if qm + j * qk >= 1 \
                else Fraction(pk, qk)
            return Fraction(pk, qk), semi, k + 2
    return None


def best_approximation(x, bound: int, start_terms: int = 12
                       ) -> Dict[str, object]:
    """The nearest fraction to the exact real ``x`` with denominator at most
    ``bound``.

    Returns a record with ``ok``; when ``ok`` it holds ``value`` (a
    :class:`~fractions.Fraction`), the two ``candidates``, the number of
    certified ``terms_used`` and ``exact_input``; otherwise ``reason``.
    """
    from . import exact_real as xr
    from . import substrate_cognition as sc
    if bound < 1:
        return {"ok": False, "reason": "the denominator bound must be at "
                "least 1"}
    if getattr(x, "exact", None) is not None:
        q = Fraction(x.exact)
        if q.denominator <= bound:
            return {"ok": True, "value": q, "candidates": [q],
                    "terms_used": 0, "exact_input": True}
        terms = xr.continued_fraction(q, 200)
        cand = _fraction_candidates(terms, bound)
        assert cand is not None
        c1, c2, used = cand
        winner = c1 if abs(q - c1) < abs(q - c2) else c2
        if abs(q - c1) == abs(q - c2) and c1 != c2:
            return {"ok": False, "reason": f"{c1} and {c2} are equally near "
                    f"{q}", "candidates": [c1, c2]}
        cert = farey_certificate(x, c1, c2, bound)
        if not cert["ok"]:
            return {"ok": False, "reason": f"the Farey certificate fails: "
                    f"{cert['reason']}", "candidates": [c1, c2]}
        return {"ok": True, "value": winner, "candidates": [c1, c2],
                "terms_used": used, "exact_input": True, "certificate": cert}
    want = start_terms
    while True:
        terms, bits, complete = sc.cf_certified(x, want, max_bits=MAX_BITS)
        cand = _fraction_candidates(terms, bound)
        if cand is not None:
            break
        if not complete:
            return {"ok": False, "reason": f"only {len(terms)} terms of the "
                    f"value are certified at 2^-{bits}, and their convergents "
                    f"do not yet pass the denominator {bound} (a value whose "
                    "expansion ends, written as an expression, certifies no "
                    "term past its last one)", "terms": list(terms)}
        want *= 2
    c1, c2, used = cand
    if c1 == c2:
        return {"ok": False, "reason": f"the two candidates coincide at {c1}, "
                "so there is no Farey certificate", "candidates": [c1]}
    side = closer_by_midpoint(x, c1, c2)
    if side is None:
        return {"ok": False, "reason": f"{c1} and {c2} are not told apart by "
                f"any precision up to 2^-{MAX_BITS}: the value may lie on "
                "their midpoint", "candidates": [c1, c2]}
    cert = farey_certificate(x, c1, c2, bound)
    if not cert["ok"]:
        return {"ok": False, "reason": f"the Farey certificate fails: "
                f"{cert['reason']}", "candidates": [c1, c2]}
    return {"ok": True, "value": c1 if side == 1 else c2,
            "candidates": [c1, c2], "terms_used": used,
            "exact_input": False, "certificate": cert}


def exhaustive_nearest(x, bound: int, start: int = 0
                       ) -> Optional[Dict[str, object]]:
    """The nearest fraction with denominator at most ``bound``, by trying
    every denominator -- no continued fractions.  A cross-check for the
    measurement; its cost grows with ``bound``, and the answering path no
    longer calls it (the Farey certificate replaces it).  ``None`` when no
    precision up to :data:`MAX_BITS` separates the winner by the required
    margin."""
    if bound < 1:
        return None
    k = max(start, 2 * bound.bit_length() + 24)
    while k <= MAX_BITS:
        mid = x.at(k)
        eps = Fraction(1, 1 << k)
        best: Dict[Fraction, Fraction] = {}
        for q in range(1, bound + 1):
            base = (mid * q).numerator // (mid * q).denominator
            for p in (base, base + 1):
                r = Fraction(p, q)
                if r not in best:
                    best[r] = abs(mid - r)
        ranked = sorted(best.items(), key=lambda kv: kv[1])
        win, d0 = ranked[0]
        d1 = ranked[1][1] if len(ranked) > 1 else None
        if d1 is None or d1 - d0 > 2 * eps:
            return {"value": win, "bits": k, "tried": len(best)}
        k *= 2
    return None


def rational_approx_report() -> Dict[str, object]:
    """The worked cases the study quotes, recomputed."""
    from . import exact_real as xr
    from . import substrate_cognition as sc
    out: Dict[str, object] = {}
    pi = xr.parse_real("pi")
    terms, _, _ = sc.cf_certified(pi, 6)
    out["pi_convergents"] = [str(convergent(terms, k)) for k in range(1, 6)]
    rows = []
    for name, bound in (("pi", 1000), ("sqrt(2)", 100), ("e", 1000),
                        ("(1+sqrt(5))/2", 50)):
        x = xr.parse_real(name)
        got = best_approximation(x, bound)
        ex = exhaustive_nearest(x, bound)
        rows.append({"x": name, "bound": bound, "value": str(got["value"]),
                     "exhaustive": str(ex["value"]) if ex else None,
                     "agree": bool(ex) and ex["value"] == got["value"]})
    out["best"] = rows
    return out

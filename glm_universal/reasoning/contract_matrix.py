"""``glm_universal.reasoning.contract_matrix`` -- the two contract changes of candidate P, tested four ways.

The question
------------
Phase 86 (``studies/RATE_POSTERIOR_STUDY.md`` section 4) left two changes of
contract for the owner: (P-a) answer the soft floor with the confidence at the
**upper end of a credible set** of rates instead of the posterior-marginal
confidence, and (P-b) let the plain readings print a **session-marginal**
confidence -- one whose rate posterior is taken over every read the session
has seen, not only the reads the call passes.  The owner asked for both to be
tested, alone and together, against the current contract, and for the best to
become the production baseline with the other set aside, not removed
(``studies/CONTRACT_MATRIX_STUDY.md``, Phase 89).

The four variants
-----------------
=====  ==========================  ========================  ===============
name   what it is                  posterior over            rule
=====  ==========================  ========================  ===============
A      control (current contract)  the call's own read       marginal
B      upper-credible alone        the call's own read       upper credible
C      session-marginal alone      every read of the session marginal
D      combined candidate P        every read of the session upper credible
=====  ==========================  ========================  ===============

The model (declared before the table was read)
----------------------------------------------
A **session** of ``S`` plain calls at one fixed true rate ``r`` (J3's model:
one rate for every read).  Call ``k`` presents one subject read with its own
truth and passes no corpus.  Under the call-only variants the posterior at
call ``k`` sees one read; under the session variants it sees the ``k`` reads
of calls ``1..k`` (the reads so far -- a printed confidence never waits for
reads that have not arrived).  The subject's own coset class decides the
answer as before, so call ``k`` of a session variant is exactly the
count-vector engine's cell of ``k`` reads
(:func:`glm_universal.reasoning.rate_posterior_marks.soft_cell`), and a
session is the pooled sum of its calls: residual = pooled wrong over pooled
answered, retention = pooled right over ``S`` times the unfloored decoder's
right mass.  Exact, ``Fraction`` throughout, no sampling.

The figures (each declared before it was computed)
--------------------------------------------------
* **retention** at the two reference cells of Phase 86 (true rate 1/20 and
  1/10, floor 999/1000, ``S = 20``) and its mean over the on-grid cells;
* **soft-floor breaks** -- cells whose pooled residual exceeds ``1 - t`` -- in
  all, on the hunted grid, at 1/5 (twice the highest hunted rate);
* **residual error bounds** -- the worst factor ``residual / (1 - t)`` over
  every cell and over the on-grid cells, and the prior-averaged promise
  (J2's) re-checked for each variant;
* **calibration** of the printed (unfloored) confidence: the largest excess
  of the mean printed confidence over the actual accuracy among answered
  calls, on the grid.

The decoder reading only (as J3 and the repairs); the pair channel is not in
the matrix.  ``int`` / ``Fraction`` only.  No float, no RNG.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from . import confidence_floor_marks as cfm
from . import rate_posterior as rp
from . import rate_posterior_marks as rpm
from .decoder_confidence import N

__all__ = [
    "VARIANTS", "SESSIONS", "REFERENCE_CELLS", "session_cell", "prior_cell",
    "calibration_cell", "frame_one", "variant_row", "matrix", "PRODUCTION", "SET_ASIDE",
]

#: The four variants: ``name -> (label, corpus, rule)``; ``corpus`` is
#: ``call`` (the call's own read) or ``session`` (every read so far);
#: ``rule`` is ``marginal`` (Phase 82) or ``upper`` (Phase 86's R4).
VARIANTS: Dict[str, Tuple[str, str, str]] = {
    "A": ("control (current contract)", "call", "marginal"),
    "B": ("upper-credible rate rule alone", "call", "upper"),
    "C": ("session-marginal confidence alone", "session", "marginal"),
    "D": ("combined candidate P", "session", "upper"),
}

#: The declared session lengths (J3's call sizes).
SESSIONS: Tuple[int, ...] = rpm.SIZES
#: Phase 86's two reference cells: ``(true rate, floor)`` at ``S = 20``.
REFERENCE_CELLS: Tuple[Tuple[Fraction, Fraction], ...] = (
    (Fraction(1, 20), Fraction(999, 1000)),
    (Fraction(1, 10), Fraction(999, 1000)),
)
_HUNT = rp.GRID[:-1]
_UPPER = "R4 upper credible"


@lru_cache(maxsize=None)
def _groups(rule: str, n: int, r: Fraction
            ) -> Tuple[Tuple[Optional[Fraction], int, int], ...]:
    """Per (counts of the ``n - 1`` other reads, subject class ``<= 3``):
    ``(confidence or None when refused at the edge, right, wrong)``, masses
    over ``b^(24 n)``."""
    if rule == "marginal":
        return rpm._soft_groups(n, r, "uniform")
    out = []
    subject = [rpm._subject_masses(d, r) for d in range(4)]
    for m, pm in rpm._corpus_probabilities(n - 1, r):
        for d in range(4):
            full = tuple(k + (1 if j == d else 0) for j, k in enumerate(m))
            conf = rpm._repair_answer(_UPPER, full, d)
            out.append((conf, pm * subject[d][0], pm * subject[d][1]))
    return tuple(out)


#: The resolution of the calibration figure: each printed confidence is
#: bracketed between consecutive multiples of ``1 / RESOLUTION``, so the
#: figure is an exact interval rather than a sum of huge fractions.
RESOLUTION = 10 ** 12


@lru_cache(maxsize=None)
def _call(rule: str, n: int, r: Fraction, t: Optional[Fraction]
          ) -> Tuple[Fraction, Fraction, Fraction]:
    """One call whose posterior sees ``n`` reads: ``(right, wrong, edge)``
    probabilities, answered meaning a confidence at least ``t``."""
    den = r.denominator ** (N * n)
    right = wrong = edge = 0
    for conf, a, b in _groups(rule, n, r):
        if conf is None:
            edge += a + b
        elif t is None or conf >= t:
            right += a
            wrong += b
    return (Fraction(right, den), Fraction(wrong, den), Fraction(edge, den))


@lru_cache(maxsize=None)
def _confidence_mass(rule: str, n: int, r: Fraction
                     ) -> Tuple[Fraction, Fraction]:
    """Bounds ``(lo, hi)`` on the sum over answered outcomes of probability
    times printed confidence (unfloored), each confidence bracketed at
    :data:`RESOLUTION`."""
    den = r.denominator ** (N * n)
    lo = hi = 0
    for conf, a, b in _groups(rule, n, r):
        if conf is None:
            continue
        k = conf.numerator * RESOLUTION // conf.denominator
        lo += k * (a + b)
        hi += (k + (0 if k * conf.denominator == conf.numerator * RESOLUTION
                    else 1)) * (a + b)
    return (Fraction(lo, den * RESOLUTION), Fraction(hi, den * RESOLUTION))


def _decoder_right(r: Fraction) -> Fraction:
    return Fraction(sum(rpm._subject_masses(d, r)[0] for d in range(4)),
                    r.denominator ** N)


def session_cell(variant: str, s: int, r: Fraction,
                 t: Optional[Fraction]) -> Dict[str, object]:
    """The pooled measure of a session of ``s`` plain calls at true rate
    ``r`` under one variant, floored at ``t`` (``None``: unfloored)."""
    _label, corpus, rule = VARIANTS[variant]
    right = wrong = edge = Fraction(0)
    for k in range(1, s + 1):
        n = k if corpus == "session" else 1
        a, b, e = _call(rule, n, r, t)
        right += a
        wrong += b
        edge += e
    answered = right + wrong
    return {"variant": variant, "session": s, "rate": r, "floor": t,
            "residual": wrong / answered if answered else Fraction(0),
            "retention": right / (s * _decoder_right(r)),
            "p_edge": edge / s,
            "accuracy": right / answered if answered else Fraction(0)}


def calibration_cell(variant: str, s: int, r: Fraction
                     ) -> Dict[str, object]:
    """The unfloored printed confidence against the accuracy it claims, over
    a session: bounds on (mean printed confidence - accuracy) among answered
    calls.  Positive means overconfident."""
    _label, corpus, rule = VARIANTS[variant]
    right = wrong = lo = hi = Fraction(0)
    for k in range(1, s + 1):
        n = k if corpus == "session" else 1
        a, b, _e = _call(rule, n, r, None)
        cl, ch = _confidence_mass(rule, n, r)
        right += a
        wrong += b
        lo += cl
        hi += ch
    answered = right + wrong
    acc = right / answered
    return {"variant": variant, "session": s, "rate": r,
            "excess_lo": lo / answered - acc, "excess_hi": hi / answered - acc}


def prior_cell(variant: str, s: int, t: Fraction) -> Dict[str, object]:
    """J2's promise for one variant: the pooled residual with the rate drawn
    from the declared uniform prior over the grid (guard included)."""
    _label, corpus, rule = VARIANTS[variant]
    right = wrong = Fraction(0)
    for w, r in zip(rp.PRIORS["uniform"], rp.GRID):
        for k in range(1, s + 1):
            n = k if corpus == "session" else 1
            a, b, _e = _call(rule, n, r, t)
            right += w * a
            wrong += w * b
    answered = right + wrong
    residual = wrong / answered if answered else Fraction(0)
    return {"variant": variant, "session": s, "floor": t,
            "residual": residual, "promise": residual <= 1 - t}


def frame_one(variant: str, sizes: Sequence[int] = SESSIONS
              ) -> Dict[str, object]:
    """Frame I -- J3's table: one call of ``n`` reads (the subject and the
    ``n - 1`` corpus reads the caller passes), no session history.  A session
    variant with no history is its call variant, so C reads as A here and D
    as B, by construction."""
    _label, _corpus, rule = VARIANTS[variant]
    broken = on_grid = at_1_5 = 0
    worst = Fraction(0)
    for r in rpm.FIXED_RATES:
        for n in sizes:
            for t in cfm.THRESHOLDS:
                a, b, _e = _call(rule, n, r, t)
                res = b / (a + b) if a + b else Fraction(0)
                worst = max(worst, res / (1 - t))
                if res > 1 - t:
                    broken += 1
                    on_grid += r in _HUNT
                    at_1_5 += r == Fraction(1, 5)
    ref = {}
    for r, t in REFERENCE_CELLS:
        a, _b, _e = _call(rule, max(sizes), r, t)
        ref[f"{r}@{t}"] = a / _decoder_right(r)
    return {"cells": len(rpm.FIXED_RATES) * len(sizes) * len(cfm.THRESHOLDS),
            "broken": broken, "on_grid": on_grid, "at_one_fifth": at_1_5,
            "worst_factor": worst, "retention": ref}


def variant_row(variant: str, sessions: Sequence[int] = SESSIONS
                ) -> Dict[str, object]:
    """Every figure of the module docstring for one variant."""
    cells: List[Dict[str, object]] = []
    for r in rpm.FIXED_RATES:
        for s in sessions:
            for t in cfm.THRESHOLDS:
                c = session_cell(variant, s, r, t)
                c["broken"] = c["residual"] > 1 - t
                c["factor"] = c["residual"] / (1 - t)
                c["on_grid"] = r in _HUNT
                cells.append(c)
    broken = [c for c in cells if c["broken"]]
    grid = [c for c in cells if c["on_grid"]]
    worst = max(cells, key=lambda c: c["factor"])
    worst_grid = max(grid, key=lambda c: c["factor"])
    ref = {f"{r}@{t}": session_cell(variant, max(sessions), r, t)["retention"]
           for r, t in REFERENCE_CELLS}
    mean_grid_retention = sum((c["retention"] for c in grid),
                              Fraction(0)) / len(grid)
    priors = [prior_cell(variant, s, t) for s in sessions
              for t in cfm.THRESHOLDS]
    calib = [calibration_cell(variant, s, r) for r in _HUNT
             for s in sessions]
    worst_calib = max(calib, key=lambda x: x["excess_hi"])
    one = frame_one(variant, sessions)
    edge_1_5 = {s: session_cell(variant, s, Fraction(1, 5),
                                cfm.THRESHOLDS[0])["p_edge"]
                for s in sessions}
    return {
        "variant": variant, "label": VARIANTS[variant][0],
        "corpus": VARIANTS[variant][1], "rule": VARIANTS[variant][2],
        "cells": len(cells), "broken": len(broken),
        "on_grid": sum(1 for c in broken if c["on_grid"]),
        "at_one_fifth": sum(1 for c in broken
                            if c["rate"] == Fraction(1, 5)),
        "other_off_grid": sum(1 for c in broken if not c["on_grid"]
                              and c["rate"] != Fraction(1, 5)),
        "worst_factor": worst["factor"],
        "worst_cell": {k: worst[k] for k in ("rate", "session", "floor",
                                             "residual")},
        "worst_grid_factor": worst_grid["factor"],
        "worst_grid_cell": {k: worst_grid[k] for k in
                            ("rate", "session", "floor", "residual")},
        "retention": ref, "mean_grid_retention": mean_grid_retention,
        "prior_cells": len(priors),
        "prior_broken": sum(1 for p in priors if not p["promise"]),
        "worst_prior_factor": max(p["residual"] / (1 - p["floor"])
                                  for p in priors),
        "calibration_excess": (worst_calib["excess_lo"],
                               worst_calib["excess_hi"]),
        "calibration_cell": {"rate": worst_calib["rate"],
                             "session": worst_calib["session"]},
        "edge_at_one_fifth": edge_1_5,
        "frame_one": one,
        "broken_rows": [{k: c[k] for k in ("rate", "session", "floor",
                                           "residual", "retention")}
                        for c in broken],
    }


def matrix(sessions: Sequence[int] = SESSIONS) -> Dict[str, object]:
    """The 4-way matrix: one row per variant, and the decision rule applied.

    The decision rule (declared in the study before the full table was
    read): a variant qualifies for production only if it keeps the
    prior-averaged promise in every cell and breaks no on-grid cell in
    **either** frame (a call passing its own corpus, frame I; a session of
    plain calls, frame II); among those, the highest mean on-grid retention
    in frame II wins; ties go to the smaller contract change."""
    rows = [variant_row(v, sessions) for v in VARIANTS]
    qualified = [r for r in rows if r["prior_broken"] == 0
                 and r["on_grid"] == 0 and r["frame_one"]["on_grid"] == 0]
    changes = {"A": 0, "B": 1, "C": 1, "D": 2}
    best = max(qualified, key=lambda r: (r["mean_grid_retention"],
                                         -changes[r["variant"]]),
               default=None)
    return {"rows": rows, "sessions": tuple(sessions),
            "cells_each": len(rpm.FIXED_RATES) * len(sessions)
            * len(cfm.THRESHOLDS),
            "qualified": [r["variant"] for r in qualified],
            "production": best["variant"] if best else None}


#: The variant the matrix chose (Phase 89; pinned by
#: ``tests/test_contract_matrix.py`` and recomputed by :func:`matrix`).
PRODUCTION = "D"
#: Set aside, not removed: kept callable and named for a later round.
SET_ASIDE: Tuple[str, ...] = ("B", "C")

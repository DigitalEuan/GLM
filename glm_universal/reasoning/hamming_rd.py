"""``glm_universal.reasoning.hamming_rd`` -- the rate-distortion function of
a memoryless source under Hamming distortion on the whole range (Phase 118,
``studies/DERIVATION_THREE_STUDY.md``).

Why it exists
-------------
Phase 107 printed ``R(D)`` only where the Shannon lower bound
``H(X) - H(D) - D log2(m - 1)`` is met -- while the backward test channel
that meets it is a channel -- and refused ``NOT_TIGHT`` between that range
and ``D_max = 1 - p_max``.  The function on the gap is known in closed form
(Erokhin's), and every quantity in its proof is rational when the source
and ``D`` are, so the machine can derive it and a stand-alone script can
check it exactly.

The derivation
--------------
Sort the letters so that ``p_1 >= p_2 >= ... >= p_m`` and put
``P_k = p_1 + ... + p_k``.  At the optimum the reproduction uses only the
``k`` most likely letters, where ``k`` is fixed by ``D``:

    1 - P_k + (k - 1) p_{k+1}  <=  D  <=  1 - P_k + (k - 1) p_k

(``p_{m+1} = 0``).  These intervals tile ``[0, D_max]`` as ``k`` runs from
``m`` down to ``2``.  With ``T = D - (1 - P_k)``, ``lambda = 1 - D`` and
``beta = T / ((k - 1)(1 - D))``:

* **the test channel**: reproduction law ``q(j) = (p_j / lambda - beta) /
  (1 - beta)`` on the top ``k`` letters, and the joint law ``P(x, j) =
  lambda q(j) beta^[x != j]`` for ``x <= k``, ``P(x, j) = p_x q(j)`` for
  ``x > k``.  Its source marginal is ``p``, its distortion is exactly ``D``,
  and its mutual information is

      R(D) = H_k + (1 - D) log2(1 - D) + T log2(T / (k - 1)),
      H_k = -sum_{i <= k} p_i log2 p_i;

* **the dual point**: ``s = -ln beta`` and ``mu(x) = lambda / p_x`` for
  ``x <= k``, ``mu(x) = 1 / beta`` otherwise.  Then
  ``sum_x p_x mu(x) beta^d(x, y) = 1`` for every ``y <= k`` and ``<= 1`` for
  ``y > k`` exactly because ``p_y <= T/(k - 1)`` there (the left end of the
  interval), so by the dual lower bound
  (``GLM.NonShannon.rd_dual_lower_bound``) every channel with distortion at
  most ``D`` has rate at least ``sum_x p_x log2 mu(x) + D log2 beta`` --
  which is the same sum of logarithms as ``R(D)``.

``k = m`` is the Shannon lower bound (``T = D``); ``k = 1`` would be
``D = D_max``, where ``R = 0``.  Integers and ``Fraction`` only (D7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import coding_theory as CT
from .non_shannon import factor_log2

__all__ = ["Piece", "HammingRD", "hamming_rd", "piece_at", "rate_logform",
           "formula_logform", "piece_logform", "slb_logform", "test_channel", "dual_point", "dual_logform"]

LogForm = Dict[int, Fraction]


@dataclass
class Piece:
    lo: Fraction
    hi: Fraction
    k: int
    letters: List[int]              # indices (into the source) of the top k
    formula: str


@dataclass
class HammingRD:
    source_text: str
    m: int
    probs: List[Fraction]
    order: List[int]                # indices sorted by decreasing probability
    pieces: List[Piece]
    d_max: Fraction
    slb_end: Fraction               # end of the Shannon lower bound's range
    entropy_text: str

    @property
    def breakpoints(self) -> List[Fraction]:
        return [self.pieces[0].lo] + [p.hi for p in self.pieces]

    @property
    def letters_per_piece(self) -> List[int]:
        return [p.k for p in self.pieces]


def _ptext(x: Fraction) -> str:
    return f"({x})" if x.denominator != 1 else f"{x}"


def _hk_text(ps: Sequence[Fraction]) -> str:
    out = []
    for x in ps:
        out.append(f"- {_ptext(x)}*log2({x})")
    t = " ".join(out)
    return t[2:] if t.startswith("- ") else t


def _formula(ps_sorted: Sequence[Fraction], k: int, m: int,
             entropy_text: str) -> str:
    if k == m:
        pen = {2: "", 3: " - D"}.get(m, f" - D*log2({m - 1})")
        return f"{entropy_text} - H(D){pen}"
    tail = 1 - sum(ps_sorted[:k], Fraction(0))
    hk = "-" + _hk_text(ps_sorted[:k])
    tt = f"(D - {tail})"
    inner = f"D - {tail}" if k == 2 else f"{tt}/{k - 1}"
    return f"{hk} + (1 - D)*log2(1 - D) + {tt}*log2({inner})"


def hamming_rd(source: str) -> HammingRD:
    """The whole-range function for a source written as Phase 107 reads it
    (``[p1, ..., pm]``, ``uniform(m)`` or ``bernoulli(p)`` with ``p``
    rational); ``CT.CodingError`` otherwise."""
    m, ps, letter = CT._parse_source(source)
    if letter is not None:
        raise CT.CodingError("UNSUPPORTED", "a source in a letter is "
                             "Phase 107's binary case")
    ps = list(ps)
    order = sorted(range(m), key=lambda i: (-ps[i], i))
    srt = [ps[i] for i in order]
    entropy_text = CT._dist_text(ps)
    pieces: List[Piece] = []
    for k in range(m, 1, -1):
        Pk = sum(srt[:k], Fraction(0))
        nxt = srt[k] if k < m else Fraction(0)
        lo = 1 - Pk + (k - 1) * nxt
        hi = 1 - Pk + (k - 1) * srt[k - 1]
        if hi > lo:
            pieces.append(Piece(lo, hi, k, sorted(order[:k]),
                                _formula(srt, k, m, entropy_text)))
    d_max = 1 - srt[0]
    slb_end = pieces[0].hi if pieces and pieces[0].k == m else Fraction(0)
    return HammingRD(source, m, ps, order, pieces, d_max, slb_end,
                     entropy_text)


def piece_at(r: HammingRD, D: Fraction) -> Optional[Piece]:
    D = Fraction(D)
    for p in r.pieces:
        if p.lo <= D <= p.hi:
            return p
    return None


# ---------------------------------------------------------------------------
# exact logarithms
# ---------------------------------------------------------------------------

def _lf(q: Fraction) -> LogForm:
    return factor_log2(Fraction(q))


def _add(a: LogForm, b: LogForm, k: Fraction = Fraction(1)) -> LogForm:
    out = dict(a)
    for p, e in b.items():
        out[p] = out.get(p, Fraction(0)) + k * e
        if out[p] == 0:
            del out[p]
    return out


def _params(r: HammingRD, D: Fraction):
    p = piece_at(r, D)
    if p is None:
        raise ValueError(f"D = {D} is outside [0, {r.d_max}]")
    k = p.k
    srt = [r.probs[i] for i in r.order]
    Pk = sum(srt[:k], Fraction(0))
    T = D - (1 - Pk)
    lam = 1 - D
    beta = T / ((k - 1) * lam)
    return p, k, Pk, T, lam, beta


def formula_logform(r: HammingRD, D: Fraction) -> LogForm:
    """``H_k + (1 - D) log2(1 - D) + T log2(T/(k - 1))`` at rational
    ``0 < D < D_max``."""
    D = Fraction(D)
    p, k, Pk, T, lam, beta = _params(r, D)
    srt = [r.probs[i] for i in r.order]
    out: LogForm = {}
    for x in srt[:k]:
        out = _add(out, _lf(x), -x)
    out = _add(out, _lf(lam), lam)
    if T:
        out = _add(out, _lf(T / (k - 1)), T)
    return out


def piece_logform(r: HammingRD, piece: Piece, D: Fraction) -> LogForm:
    """One piece's formula at ``D`` (also at the piece's own ends)."""
    D = Fraction(D)
    k = piece.k
    srt = [r.probs[i] for i in r.order]
    T = D - (1 - sum(srt[:k], Fraction(0)))
    out: LogForm = {}
    for x in srt[:k]:
        out = _add(out, _lf(x), -x)
    if 1 - D:
        out = _add(out, _lf(1 - D), 1 - D)
    if T:
        out = _add(out, _lf(T / (k - 1)), T)
    return out


def slb_logform(r: HammingRD, D: Fraction) -> LogForm:
    """``H(X) - H(D) - D log2(m - 1)`` at rational ``0 < D < 1``."""
    D = Fraction(D)
    out: LogForm = {}
    for x in r.probs:
        out = _add(out, _lf(x), -x)
    out = _add(out, _lf(D), D)
    out = _add(out, _lf(1 - D), 1 - D)
    if r.m > 2:
        out = _add(out, _lf(Fraction(r.m - 1)), -D)
    return out


def test_channel(r: HammingRD, D: Fraction
                 ) -> Tuple[List[Fraction], List[List[Fraction]]]:
    """``(q, P)``: the reproduction law over all ``m`` letters (zero off
    the top ``k``) and the joint law ``P[x][j]``."""
    D = Fraction(D)
    p, k, Pk, T, lam, beta = _params(r, D)
    top = set(r.order[:k])
    q = [((r.probs[j] / lam - beta) / (1 - beta) if j in top else Fraction(0))
         for j in range(r.m)]
    P = []
    for x in range(r.m):
        row = []
        for j in range(r.m):
            if x in top:
                row.append(lam * q[j] * (1 if x == j else beta))
            else:
                row.append(r.probs[x] * q[j])
        P.append(row)
    return q, P


def rate_logform(r: HammingRD, D: Fraction) -> LogForm:
    """``I(X; Xh)`` of the test channel, exactly."""
    q, P = test_channel(r, D)
    out: LogForm = {}
    for x in range(r.m):
        for j in range(r.m):
            if P[x][j]:
                out = _add(out, _lf(P[x][j] / (r.probs[x] * q[j])), P[x][j])
    return out


def dual_point(r: HammingRD, D: Fraction) -> Tuple[Fraction, List[Fraction]]:
    """``(beta, mu)``: ``beta = e^{-s}`` and the multipliers."""
    D = Fraction(D)
    p, k, Pk, T, lam, beta = _params(r, D)
    top = set(r.order[:k])
    mu = [lam / r.probs[x] if x in top else 1 / beta for x in range(r.m)]
    return beta, mu


def dual_logform(r: HammingRD, D: Fraction) -> LogForm:
    beta, mu = dual_point(r, D)
    out: LogForm = {}
    for x in range(r.m):
        out = _add(out, _lf(mu[x]), r.probs[x])
    return _add(out, _lf(beta), Fraction(D))

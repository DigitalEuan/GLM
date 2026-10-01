"""``glm_universal.reasoning.agree_channel_marks`` -- the second reading's channel, measured.

``studies/AGREE_CHANNEL_STUDY.md`` (Phase 81) declared the marks G1-G8 before
this module existed; :func:`agree_channel_report` measures every one of them.

The reading
-----------
``agree(y1, y2)`` intersects the carried forks of two reads of one carrier
(:mod:`glm_universal.reasoning.carried_fork`): resolved when exactly one
codeword is among the nearest codewords of both reads.  Its confidence is the
posterior of the survivor under the product of the two reads' likelihoods
(:func:`glm_universal.reasoning.decoder_confidence.agree_confidence`).  The
channel: one truth drawn uniformly from the 4096 codewords, two reads of it,
every bit of each read flipping independently at the true rate.

The census
----------
By linearity the truth is the zero word.  Every resolved pair is
``(v + l1, v + l2)`` for the survivor ``v`` and a pair ``(l1, l2)`` of errors
of weight at most four whose forks meet exactly at zero -- every such pair
except two weight-4 errors whose union lies in one octad.  The right mass of a
pair is ``w(l1) w(l2)``, its wrong mass ``sum_{v != 0} w(v + l1) w(v + l2)``
and its confidence ``rho^D(0) / sum_c rho^D(c)`` with ``D(c) = d(l1, c) +
d(l2, c)``: all three are read off the **histogram of D** over the code, a
rate-independent integer table.  The census counts, for each histogram, the
pairs that have it.

A permutation of the coordinates that maps the code onto itself preserves
every histogram, so the census is one pass per weight of ``l1``:
:func:`automorphisms` finds such permutations by a declared search and
verifies them, and :func:`transitive_on_weights` verifies that they move any
error of weight ``w <= 4`` to any other.  The histograms themselves are taken
with bit-sliced counters over 4096-bit integers (one bit per codeword).

Exactness: ``int`` masks, ``int`` weights and :class:`fractions.Fraction`
only.  No float, no RNG.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from itertools import combinations
from math import comb
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate.mog import GOLAY_MASKS, GOLAY_SET
from . import carried_fork as cf
from . import confidence_floor_marks as cfm
from .decoder_confidence import (ConfidenceRefusal, N, agree_confidence,
                                 brute_posterior)

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "OCTAD_PAIRS", "PHASE_80_WORKING",
    "automorphisms", "transitive_on_weights", "pair_key", "pair_census",
    "agree_groups", "agree_cell", "enlarged_hunt", "strict_masses",
    "predict", "DECLARED_PROGRAMS", "g1_census", "g2_class_collapse",
    "g3_promise", "g4_hunt", "g5_residual", "g6_declared_rate",
    "g7_runtime", "agree_channel_report",
]

LEAN_FILE = "RequestProject/GLM/Agree.lean"

#: The theorems of ``RequestProject/GLM/Agree.lean`` (mark G8).
LEAN_THEOREMS: Tuple[str, ...] = (
    "agree_answered_sq", "agree_residual_le_single", "agree_conf_sum",
    "pair_distance_split",
)

#: Ordered pairs of weight-4 errors inside one octad, counted by hand:
#: 759 octads x 70 x 69 ordered pairs of distinct 4-subsets (the union has at
#: least five points, so its octad is unique) plus the 10,626 equal pairs.
OCTAD_PAIRS = 759 * 70 * 69 + comb(N, 4)

#: Phase 80's working threshold per rate over its six readings (study §2.3).
PHASE_80_WORKING: Dict[Fraction, Optional[Fraction]] = {
    Fraction(1, 1000): Fraction(9999, 10000),
    Fraction(1, 100): Fraction(9999, 10000),
    Fraction(1, 50): Fraction(9999, 10000),
    Fraction(1, 20): Fraction(999, 1000),
    Fraction(1, 10): None,
}

_CODE_BITS = len(GOLAY_MASKS)
_FULL = (1 << _CODE_BITS) - 1


# ===========================================================================
# 1.  THE SYMMETRY
# ===========================================================================

@lru_cache(maxsize=None)
def _octads() -> Tuple[int, ...]:
    return tuple(c for c in GOLAY_MASKS if c.bit_count() == 8)


@lru_cache(maxsize=None)
def _octad_of_five() -> Dict[Tuple[int, ...], int]:
    """Every 5-subset of the coordinates lies in exactly one octad."""
    out: Dict[Tuple[int, ...], int] = {}
    for o in _octads():
        pts = [i for i in range(N) if (o >> i) & 1]
        for s in combinations(pts, 5):
            out[s] = o
    return out


def _apply(perm: Sequence[int], mask: int) -> int:
    out = 0
    for i in range(N):
        if (mask >> i) & 1:
            out |= 1 << perm[i]
    return out


def _complete(src: Sequence[int], dst: Sequence[int]
              ) -> Optional[Tuple[int, ...]]:
    """A permutation sending ``src[i]`` to ``dst[i]`` and every octad onto an
    octad, by backtracking; ``None`` if there is none."""
    of5 = _octad_of_five()
    pi = dict(zip(src, dst))
    used = set(dst)
    order = [i for i in range(N) if i not in pi]

    def consistent(x: int, y: int) -> bool:
        dom = list(pi)
        for s in combinations(dom, 4):
            o1 = of5[tuple(sorted(s + (x,)))]
            o2 = of5[tuple(sorted(tuple(pi[z] for z in s) + (y,)))]
            for z in dom:
                if ((o1 >> z) & 1) != ((o2 >> pi[z]) & 1):
                    return False
        return True

    def extend(k: int) -> bool:
        if k == len(order):
            return True
        x = order[k]
        for y in range(N):
            if y in used or not consistent(x, y):
                continue
            pi[x] = y
            used.add(y)
            if extend(k + 1):
                return True
            del pi[x]
            used.discard(y)
        return False

    return tuple(pi[i] for i in range(N)) if extend(0) else None


#: The declared search: images of the first five coordinates.
_SEARCH: Tuple[Tuple[Tuple[int, ...], Tuple[int, ...]], ...] = (
    ((0, 1, 2, 3, 4), (1, 2, 3, 4, 5)),
    ((0, 1, 2, 3, 4), (0, 1, 2, 3, 5)),
    ((0, 1, 2, 3, 4), (23, 7, 11, 2, 19)),
    ((0, 1, 2, 3, 4), (4, 3, 2, 1, 0)),
)


@lru_cache(maxsize=None)
def automorphisms() -> Tuple[Tuple[int, ...], ...]:
    """Coordinate permutations mapping every codeword to a codeword, found by
    the declared search and each verified over all 4096 codewords."""
    out = []
    for src, dst in _SEARCH:
        g = _complete(src, dst)
        if g is None or not all(_apply(g, c) in GOLAY_SET
                                for c in GOLAY_MASKS):
            raise AssertionError(f"no code automorphism for {src} -> {dst}")
        out.append(g)
    return tuple(out)


def transitive_on_weights(weights: Sequence[int] = (1, 2, 3, 4)
                          ) -> Dict[int, int]:
    """The orbit of the first ``w`` coordinates under the group the
    automorphisms generate, per ``w``: transitive when it is ``C(24, w)``."""
    gens = automorphisms()
    out = {}
    for w in weights:
        start = (1 << w) - 1
        seen = {start}
        frontier = [start]
        while frontier:
            nxt = []
            for m in frontier:
                for g in gens:
                    m2 = _apply(g, m)
                    if m2 not in seen:
                        seen.add(m2)
                        nxt.append(m2)
            frontier = nxt
        out[w] = len(seen)
    return out


# ===========================================================================
# 2.  THE CENSUS
# ===========================================================================

@lru_cache(maxsize=None)
def _errors_up_to_four() -> Tuple[Tuple[int, int, Tuple[int, ...]], ...]:
    return tuple((sum(1 << i for i in s), w, s)
                 for w in range(5) for s in combinations(range(N), w))


@lru_cache(maxsize=None)
def _coordinate_slices() -> Tuple[int, ...]:
    """Per coordinate, the 4096-bit set of codewords holding a one there."""
    out = [0] * N
    for idx, c in enumerate(GOLAY_MASKS):
        for i in range(N):
            if (c >> i) & 1:
                out[i] |= 1 << idx
    return tuple(out)


def _octad_pair(l1: int, l2: int) -> bool:
    """Two weight-4 errors inside one octad: their forks share a second
    codeword, so the pair is not resolved."""
    if l1.bit_count() != 4 or l2.bit_count() != 4:
        return False
    return any(o & (l1 | l2) == (l1 | l2) for o in _octads())


def pair_key(l1: int, l2: int) -> Tuple[int, int, int, int, bool]:
    """G2's key: ``(wt l1, wt l2, |l1 & l2|, m, e)`` -- ``m`` the most points
    of the union in one octad, ``e`` whether such an octad holds ``l1`` or
    ``l2``."""
    u = l1 | l2
    pts = [i for i in range(N) if (u >> i) & 1]
    if len(pts) < 5:
        return (l1.bit_count(), l2.bit_count(), (l1 & l2).bit_count(),
                len(pts), True)
    of5 = _octad_of_five()
    meets = {of5[s] for s in combinations(pts, 5)}
    m = max((o & u).bit_count() for o in meets)
    e = any((o & u).bit_count() == m and (o & l1 == l1 or o & l2 == l2)
            for o in meets)
    return (l1.bit_count(), l2.bit_count(), (l1 & l2).bit_count(), m, e)


def _histogram(l1_classes: Sequence[Tuple[int, int]], w2: int,
               support: Sequence[int]) -> Tuple[Tuple[int, int], ...]:
    """The histogram of ``D(c) = d(l1, c) + d(l2, c)`` over the code, from
    the classes of ``d(l1, c) + wt(c)`` and the bits of ``l2``."""
    slices = _coordinate_slices()
    exact = [_FULL] + [0] * w2           # exact[j]: codewords meeting l2 in j
    for i in support:
        b = slices[i]
        for j in range(w2, 0, -1):
            exact[j] = (exact[j] & ~b) | (exact[j - 1] & b)
        exact[0] &= ~b
    hist: Dict[int, int] = {}
    for k, cls in l1_classes:
        for j in range(w2 + 1):
            n = (cls & exact[j]).bit_count()
            if n:
                d = k + w2 - 2 * j
                hist[d] = hist.get(d, 0) + n
    return tuple(sorted(hist.items()))


@lru_cache(maxsize=None)
def _census_rows() -> Tuple[Tuple[int, int, int, Tuple[int, int, int, int,
                                                         bool],
                                  Tuple[Tuple[int, int], ...]], ...]:
    """Per ``(first error of weight w1 = the first w1 coordinates, second
    error)`` of ``R``: ``(w1, w2, l2, key, histogram)``."""
    rows = []
    for w1 in range(5):
        l1 = (1 << w1) - 1
        classes: Dict[int, int] = {}
        for idx, c in enumerate(GOLAY_MASKS):
            k = (c ^ l1).bit_count() + c.bit_count()
            classes[k] = classes.get(k, 0) | (1 << idx)
        cl = tuple(sorted(classes.items()))
        for l2, w2, sup in _errors_up_to_four():
            if _octad_pair(l1, l2):
                continue
            rows.append((w1, w2, l2, pair_key(l1, l2),
                         _histogram(cl, w2, sup)))
    return tuple(rows)


@lru_cache(maxsize=None)
def pair_census() -> Tuple[Tuple[int, int, Tuple[Tuple[int, int], ...], int],
                           ...]:
    """The census over every pair of ``R``: each distinct ``(wt l1, wt l2,
    histogram of D)`` with how many ordered pairs have it."""
    census: Dict[Tuple[int, int, Tuple[Tuple[int, int], ...]], int] = {}
    for w1, w2, _l2, _key, hist in _census_rows():
        k = (w1, w2, hist)
        census[k] = census.get(k, 0) + comb(N, w1)
    return tuple((w1, w2, h, n) for (w1, w2, h), n in sorted(census.items()))


def _pair_weights(p: Fraction) -> Tuple[int, ...]:
    """``a^D (b-a)^(48-D)`` for ``D = 0..48`` at ``p = a/b``."""
    a, b = p.numerator, p.denominator
    return tuple(a ** d * (b - a) ** (2 * N - d) for d in range(2 * N + 1))


def _conf(hist: Sequence[Tuple[int, int]], w: Sequence[int]) -> Fraction:
    d0, n0 = hist[0]
    assert n0 == 1, "the survivor is the unique minimum of D"
    return Fraction(w[d0], sum(n * w[d] for d, n in hist))


@lru_cache(maxsize=None)
def agree_groups(declared: Fraction, true: Fraction
                 ) -> Tuple[Tuple[Fraction, int, int], ...]:
    """Per census group: ``(confidence at the declared rate, right mass,
    wrong mass at the true rate)``, masses over ``b^48``."""
    wd, wt = _pair_weights(declared), _pair_weights(true)
    out = []
    for _w1, _w2, hist, n in pair_census():
        d0 = hist[0][0]
        total = sum(k * wt[d] for d, k in hist)
        out.append((_conf(hist, wd), n * wt[d0], n * (total - wt[d0])))
    return tuple(out)


def agree_cell(declared: Fraction, t: Optional[Fraction],
               true: Optional[Fraction] = None) -> Dict[str, object]:
    """The exact channel measure of the second reading at one floor, in the
    shape of :func:`confidence_floor_marks.cell`."""
    true = declared if true is None else true
    den = true.denominator ** (2 * N)
    groups = agree_groups(declared, true)
    right0 = sum(g[1] for g in groups)
    wrong0 = sum(g[2] for g in groups)
    kept = [g for g in groups if t is None or g[0] >= t]
    right = sum(g[1] for g in kept)
    wrong = sum(g[2] for g in kept)
    answered = right + wrong
    return {
        "reading": "agree", "declared": declared, "true": true, "floor": t,
        "p_right": Fraction(right, den), "p_wrong": Fraction(wrong, den),
        "p_answered": Fraction(answered, den),
        "p_refused": 1 - Fraction(right0 + wrong0, den),
        "p_right_unfloored": Fraction(right0, den),
        "p_wrong_unfloored": Fraction(wrong0, den),
        "residual": Fraction(wrong, answered) if answered else Fraction(0),
        "retention": Fraction(right, right0) if right0 else Fraction(1),
        "wrong_removed": (Fraction(wrong0 - wrong, wrong0) if wrong0
                          else Fraction(1)),
        "least_confidence": min((g[0] for g in groups), default=None),
    }


READINGS: Tuple[str, ...] = cfm.READINGS + ("agree",)


def _cell(reading: str, declared: Fraction, t: Optional[Fraction],
          true: Fraction) -> Dict[str, object]:
    if reading == "agree":
        return agree_cell(declared, t, true)
    return cfm.cell(reading, declared, t, true)


def enlarged_hunt(true_factor: Fraction = Fraction(1),
                  readings: Sequence[str] = READINGS) -> Dict[str, object]:
    """Phase 80's hunt over the seven readings."""
    rows = []
    for p in cfm.HUNT_RATES:
        for t in cfm.THRESHOLDS:
            cells = [_cell(r, p, t, p * true_factor) for r in readings]
            promise = all(c["residual"] <= 1 - t for c in cells)
            cost = all(c["retention"] >= cfm.LEAST_RETENTION for c in cells)
            worst = min(cells, key=lambda c: c["retention"])
            rows.append({"rate": p, "floor": t, "promise": promise,
                         "cost": cost, "works": promise and cost,
                         "least_retention": worst["retention"],
                         "least_retention_reading": worst["reading"],
                         "greatest_residual": max(c["residual"]
                                                  for c in cells),
                         "cells": cells})
    working: Dict[Fraction, Optional[Fraction]] = {}
    for p in cfm.HUNT_RATES:
        ok = [r["floor"] for r in rows if r["rate"] == p and r["works"]]
        working[p] = max(ok) if ok else None
    return {"rows": rows, "working": working, "readings": tuple(readings)}


# ===========================================================================
# 3.  THE SECOND ROUTE -- strict agreement by factorization
# ===========================================================================

#: The weight distribution of the code.
_CODE_WEIGHTS: Tuple[Tuple[int, int], ...] = ((0, 1), (8, 759), (12, 2576),
                                              (16, 759), (24, 1))


def _read_mass(wc: int, error_weights: Sequence[int], p: Fraction) -> Fraction:
    """``sum_{wt l in error_weights} w(c + l)`` for a codeword of weight
    ``wc``: the probability that one read is ``c + l``, truth zero."""
    q = 1 - p
    out = Fraction(0)
    for j in error_weights:
        for i in range(min(wc, j) + 1):
            n = comb(wc, i) * comb(N - wc, j - i)
            if n:
                d = wc + j - 2 * i
                out += n * p ** d * q ** (N - d)
    return out


def strict_masses(p: Fraction) -> Dict[str, Fraction]:
    """By factorization from the code's weight distribution alone:
    ``A_c`` (decoded uniquely to ``c``) and ``T_c`` (at coset weight 4 with
    ``c`` among the six), and the strict and mixed agreement masses."""
    a = {wc: _read_mass(wc, (0, 1, 2, 3), p) for wc, _ in _CODE_WEIGHTS}
    t = {wc: _read_mass(wc, (4,), p) for wc, _ in _CODE_WEIGHTS}
    strict = sum(n * a[wc] ** 2 for wc, n in _CODE_WEIGHTS)
    strict_right = a[0] ** 2
    mixed = 2 * sum(n * a[wc] * t[wc] for wc, n in _CODE_WEIGHTS)
    single = sum(n * a[wc] for wc, n in _CODE_WEIGHTS)
    return {"A": a, "T": t, "strict": strict, "strict_right": strict_right,
            "strict_residual": (strict - strict_right) / strict,
            "mixed": mixed, "single_answered": single,
            "single_residual": (single - a[0]) / single,
            "modal": all(a[0] >= a[wc] for wc, _ in _CODE_WEIGHTS)}


def _census_mass(p: Fraction, part: str) -> Fraction:
    w = _pair_weights(p)
    total = 0
    for w1, w2, hist, n in pair_census():
        both_small = w1 <= 3 and w2 <= 3
        one_four = (w1 == 4) != (w2 == 4)
        if (part == "strict" and both_small) or (part == "mixed"
                                                  and one_four):
            total += n * sum(k * w[d] for d, k in hist)
    return Fraction(total, p.denominator ** (2 * N))


# ===========================================================================
# 4.  THE RUNTIME, PREDICTED FROM THE CENSUS
# ===========================================================================

def predict(rate: Fraction, floor: Optional[Fraction], l1: int, l2: int
            ) -> Tuple[str, Optional[Fraction]]:
    """The outcome of ``agree_floor(rate, floor, v + l1, v + l2)`` (or
    ``agree_at`` when ``floor`` is ``None``) computed from the census: the
    fork rule, then the confidence of the pair's class."""
    f1, f2 = cf.carry(l1), cf.carry(l2)
    common = set(f1.candidates) & set(f2.candidates)
    if not common:
        return ("UNCORRECTABLE", None)
    if len(common) > 1:
        return ("AMBIGUOUS", None)
    (s,) = common
    #  translate so the survivor is zero, then read the class's histogram
    k1, k2 = l1 ^ s, l2 ^ s
    key = pair_key(k1, k2)
    hist = _histogram_of_key()[key]
    conf = _conf(hist, _pair_weights(rate))
    if floor is not None and conf < floor:
        return ("BELOW_FLOOR", conf)
    return ("answer", conf)


@lru_cache(maxsize=None)
def _histogram_of_key() -> Dict[Tuple[int, int, int, int, bool],
                                Tuple[Tuple[int, int], ...]]:
    out: Dict[Tuple[int, int, int, int, bool],
              Tuple[Tuple[int, int], ...]] = {}
    for _w1, _w2, _l2, key, hist in _census_rows():
        out.setdefault(key, hist)
    return out


def _mask(*coords: int) -> int:
    return sum(1 << i for i in coords)


#: G7's declared programs: ``(rate, floor or None, truth index, l1, l2)``.
#: The octad errors are split off the first octad of the code at run time
#: (``"octad:a"`` / ``"octad:b"``: its first and last four points).
DECLARED_PROGRAMS: Tuple[Tuple[Fraction, Optional[Fraction], int, object,
                               object], ...] = (
    (Fraction(1, 10), Fraction(999, 1000), 5, _mask(0, 1, 2), _mask(3, 4, 5)),
    (Fraction(1, 10), Fraction(999, 1000), 5, _mask(0, 1, 2), _mask(0, 1, 2)),
    (Fraction(1, 10), Fraction(999, 1000), 9, _mask(0, 1, 2),
     _mask(3, 4, 5, 6)),
    (Fraction(1, 10), Fraction(9999, 10000), 9, _mask(0, 1, 2, 3),
     _mask(4, 5, 6, 7)),
    (Fraction(1, 10), None, 17, _mask(0, 1, 2), _mask(7, 11)),
    (Fraction(1, 20), Fraction(9999, 10000), 17, _mask(0, 1, 2, 3),
     _mask(3, 9, 14)),
    (Fraction(1, 100), Fraction(99, 100), 2, _mask(0), _mask(23)),
    (Fraction(1, 10), Fraction(99, 100), 3, "octad:a", "octad:b"),
    (Fraction(1, 10), Fraction(99, 100), 3, _mask(0, 1, 2, 3, 4),
     _mask(20)),
    (Fraction(1, 10), Fraction(9, 10), 30, _mask(5, 6, 7, 8),
     _mask(9, 10, 11, 12)),
)


def _resolve_masks(item: object) -> int:
    if isinstance(item, int):
        return item
    octad = _octads()[0]
    pts = [i for i in range(N) if (octad >> i) & 1]
    return _mask(*(pts[:4] if item == "octad:a" else pts[4:]))


# ===========================================================================
# 5.  THE MARKS
# ===========================================================================

def g1_census(stride: int = 331) -> Dict[str, object]:
    """G1: the census is right."""
    rows = _census_rows()
    pairs = sum(comb(N, w1) for w1, *_ in rows)
    expected = len(_errors_up_to_four()) ** 2 - OCTAD_PAIRS
    routes = []
    routes_ok = True
    for p in cfm.HUNT_RATES:
        s = strict_masses(p)
        cs, cm = _census_mass(p, "strict"), _census_mass(p, "mixed")
        routes.append({"rate": p, "strict_factorized": s["strict"],
                       "strict_census": cs, "mixed_factorized": s["mixed"],
                       "mixed_census": cm})
        routes_ok = routes_ok and cs == s["strict"] and cm == s["mixed"]
    #  the stride against the runtime and a brute-force sum, with each pair
    #  moved by an automorphism and translated by a codeword
    gens = automorphisms()
    p = Fraction(1, 10)
    w = _pair_weights(p)
    checked = disagreements = 0
    for i, (w1, _w2, l2, _key, hist) in enumerate(rows):
        if i % stride:
            continue
        g = gens[i % len(gens)]
        l1m, l2m = _apply(g, (1 << w1) - 1), _apply(g, l2)
        v = GOLAY_MASKS[(37 * i) % len(GOLAY_MASKS)]
        reads = (v ^ l1m, v ^ l2m)
        conf = _conf(hist, w)
        r = agree_confidence(list(reads), p)
        brute = brute_posterior(reads, v, GOLAY_MASKS, p)
        checked += 1
        disagreements += not (r["value"] == v and r["confidence"] == conf
                              == brute)
    #  the excluded octad pairs refuse
    octad = _octads()[7]
    pts = [i for i in range(N) if (octad >> i) & 1]
    refused = ambiguous = 0
    for j, (a, b) in enumerate(combinations(combinations(pts, 4), 2)):
        if j % 97:
            continue
        v = GOLAY_MASKS[(11 * j) % len(GOLAY_MASKS)]
        refused += 1
        try:
            agree_confidence([v ^ _mask(*a), v ^ _mask(*b)], p)
        except ConfidenceRefusal as e:
            ambiguous += e.name == "AMBIGUOUS"
    orbits = transitive_on_weights()
    transitive = all(orbits[w] == comb(N, w) for w in orbits)
    subgroups = {}
    for k in cfm.CASE_SIZES:
        cases = set(cf.case_set(k))
        subgroups[k] = (0 in cases
                        and all(a ^ b in cases for a in cases for b in cases))
    return {"pairs": pairs, "pairs_expected": expected,
            "octad_pairs": OCTAD_PAIRS, "groups": len(pair_census()),
            "routes": routes, "routes_agree": routes_ok,
            "checked": checked, "disagreements": disagreements,
            "octad_checked": refused, "octad_ambiguous": ambiguous,
            "automorphisms": len(gens), "orbits": orbits,
            "transitive": transitive, "case_sets_subgroups": subgroups,
            "passed": (pairs == expected and routes_ok and checked > 0
                       and disagreements == 0 and refused == ambiguous > 0
                       and transitive)}


def g2_class_collapse() -> Dict[str, object]:
    """G2: the histogram is a function of the declared key; the owner's
    coarser key recorded beside it."""
    fine: Dict[tuple, set] = {}
    coarse: Dict[tuple, set] = {}
    for _w1, _w2, _l2, key, hist in _census_rows():
        fine.setdefault(key, set()).add(hist)
        coarse.setdefault(key[:3], set()).add(hist)
    fine_split = [k for k, v in fine.items() if len(v) > 1]
    coarse_split = sorted(k for k, v in coarse.items() if len(v) > 1)
    return {"keys": len(fine), "keys_split": len(fine_split),
            "coarse_keys": len(coarse), "coarse_split": len(coarse_split),
            "coarse_split_keys": coarse_split,
            "histograms": len({h for v in fine.values() for h in v}),
            "passed": not fine_split}


def g3_promise() -> Dict[str, object]:
    """G3: ``P(wrong | answered) <= 1 - t`` in every cell of ``agree``."""
    cells = [agree_cell(p, t) for p in cfm.HUNT_RATES for t in cfm.THRESHOLDS]
    broken = [c for c in cells if c["residual"] > 1 - c["floor"]]
    return {"cells": len(cells), "broken": len(broken),
            "passed": not broken and len(cells) == 35}


def _monotone(works: Dict[Tuple[Fraction, Fraction], bool]
              ) -> Tuple[bool, bool]:
    mono_floor = all(works[(p, t2)] for (p, t), ok in works.items() if ok
                     for t2 in cfm.THRESHOLDS if t2 < t)
    mono_rate = all(works[(p2, t)] for (p, t), ok in works.items() if ok
                    for p2 in cfm.HUNT_RATES if p2 < p)
    return mono_floor, mono_rate


def g4_hunt() -> Dict[str, object]:
    """G4: the hunt over seven readings, Phase 80's cells unchanged, the
    working threshold per rate for the grid and for ``agree`` alone."""
    h7 = enlarged_hunt()
    h6 = cfm.hunt()
    same = all(
        r6["cells"] == r7["cells"][:len(cfm.READINGS)]
        for r6, r7 in zip(h6["rows"], h7["rows"]))
    agree_alone = enlarged_hunt(readings=("agree",))
    decoder_alone = enlarged_hunt(readings=("decoder",))
    works7 = {(r["rate"], r["floor"]): r["works"] for r in h7["rows"]}
    works_a = {(r["rate"], r["floor"]): r["works"]
               for r in agree_alone["rows"]}
    m7 = _monotone(works7)
    ma = _monotone(works_a)
    cells = sum(len(r["cells"]) for r in h7["rows"])

    def key(t: Optional[Fraction]) -> Fraction:
        return Fraction(0) if t is None else t

    e1 = all(key(agree_alone["working"][p]) >= key(decoder_alone["working"][p])
             for p in cfm.HUNT_RATES)
    e2 = agree_alone["working"][Fraction(1, 10)] is not None
    table = [{"rate": r["rate"], "floor": r["floor"], "works": r["works"],
              "retention": r["cells"][0]["retention"],
              "residual": r["cells"][0]["residual"],
              "wrong_removed": r["cells"][0]["wrong_removed"]}
             for r in agree_alone["rows"]]
    return {"cells": cells, "phase_80_cells_unchanged": same,
            "working_seven": {str(p): (str(t) if t is not None else None)
                              for p, t in h7["working"].items()},
            "working_agree": {str(p): (str(t) if t is not None else None)
                              for p, t in agree_alone["working"].items()},
            "working_decoder": {str(p): (str(t) if t is not None else None)
                                for p, t in decoder_alone["working"].items()},
            "phase_80_working_holds": h6["working"] == PHASE_80_WORKING,
            "monotone_seven": m7, "monotone_agree": ma,
            "expectation_E1": e1, "expectation_E2": e2, "agree_table": table,
            "passed": (cells == 245 and same and all(m7) and all(ma)
                       and h6["working"] == PHASE_80_WORKING)}


def g5_residual() -> Dict[str, object]:
    """G5: the second reading's residual at most the decoder's, strict
    agreement's too, and the modal hypothesis of the Lean theorem."""
    rows = []
    ok = True
    for p in cfm.HUNT_RATES:
        a = agree_cell(p, None)
        d = cfm.cell("decoder", p, None)
        s = strict_masses(p)
        row = {"rate": p, "agree": a["residual"], "decoder": d["residual"],
               "strict": s["strict_residual"],
               "single_by_factorization": s["single_residual"],
               "modal": s["modal"],
               "agree_right": a["p_right"], "agree_wrong": a["p_wrong"],
               "agree_refused": a["p_refused"], "decoder_right": d["p_right"],
               "decoder_wrong": d["p_wrong"]}
        rows.append(row)
        ok = ok and (a["residual"] <= d["residual"]
                     and s["strict_residual"] <= s["single_residual"]
                     and s["single_residual"] == d["residual"]
                     and s["modal"])
    return {"rows": rows, "passed": ok}


def g6_declared_rate() -> Dict[str, object]:
    """G6: overdeclared (the mark) and underdeclared (reported)."""
    over, under = [], []
    for p in cfm.HUNT_RATES:
        for t in cfm.THRESHOLDS:
            o = agree_cell(p, t, p / 2)
            u = agree_cell(p, t, 2 * p)
            if o["residual"] > 1 - t:
                over.append((p, t))
            if u["residual"] > 1 - t:
                under.append({"declared": p, "floor": t,
                              "residual": u["residual"], "promised": 1 - t})
    return {"cells": 35, "overdeclared_broken": len(over),
            "underdeclared_broken": len(under), "underdeclared_rows": under,
            "passed": not over}


def g7_runtime() -> Dict[str, object]:
    """G7: every declared program's outcome computed from the census, then
    the runtime run and its scripts checked."""
    from . import python_speech as sp
    rows = []
    for rate, floor, idx, a, b in DECLARED_PROGRAMS:
        l1, l2 = _resolve_masks(a), _resolve_masks(b)
        computed, conf = predict(rate, floor, l1, l2)
        v = GOLAY_MASKS[idx]
        r1, r2 = v ^ l1, v ^ l2
        if floor is None:
            src = f"agree_at(Fraction({rate.numerator}, {rate.denominator})" \
                  f", {r1}, {r2})"
        else:
            src = (f"agree_floor(Fraction({rate.numerator}, "
                   f"{rate.denominator}), Fraction({floor.numerator}, "
                   f"{floor.denominator}), {r1}, {r2})")
        payload = sp.speak(src)
        got = payload.refusal or "answer"
        verified = None
        if got == "answer":
            verified = bool(sp.verify_payload(payload)["verified"])
        rows.append({"source": src, "computed": computed,
                     "confidence": conf, "got": got,
                     "verified": verified,
                     "as_computed": got == computed
                     and verified in (None, True)})
    wrong = sum(1 for r in rows if not r["as_computed"])
    return {"rows": rows, "programs": len(rows),
            "as_computed": len(rows) - wrong, "wrong": wrong,
            "passed": wrong == 0}


def _lean_has(names: Sequence[str]) -> bool:
    """Whether the Lean file states every named theorem and holds no
    ``sorry`` (the build itself is the release's Lean instrument)."""
    import re
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "glm_lean" / LEAN_FILE
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return "sorry" not in text and all(
        re.search(rf"\btheorem {n}\b", text) for n in names)


def agree_channel_report() -> Dict[str, object]:
    """Every mark of the study, measured."""
    g1 = g1_census()
    g2 = g2_class_collapse()
    g3 = g3_promise()
    g4 = g4_hunt()
    g5 = g5_residual()
    g6 = g6_declared_rate()
    g7 = g7_runtime()
    g8 = {"file": LEAN_FILE, "theorems": list(LEAN_THEOREMS),
          "passed": _lean_has(LEAN_THEOREMS)}
    marks = {"G1": g1["passed"], "G2": g2["passed"], "G3": g3["passed"],
             "G4": g4["passed"], "G5": g5["passed"], "G6": g6["passed"],
             "G7": g7["passed"], "G8": g8["passed"]}
    return {"G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G6": g6,
            "G7": g7, "G8": g8, "marks": marks, "met": sum(marks.values()),
            "of": len(marks)}

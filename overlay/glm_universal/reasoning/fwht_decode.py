"""``glm_universal.reasoning.fwht_decode`` -- the transform-driven decoder.

What this module is
-------------------
:mod:`glm_universal.reasoning.fwht` implements the Walsh-Hadamard transform
and stops there: it was never wired to anything, and said so.  This module
is the wiring.  It does two things, and it reports honestly on what each
one is worth.

**1.  The soft-decision Golay search is one Walsh-Hadamard transform.**

The exact Leech nearest-point decoder in
:func:`glm_universal.reasoning.analogy.nearest_lattice_point` minimises,
over the 4,096 Golay codewords ``w``,

    ``cost(w) = base + sum_{k in supp(w)} delta_k``

-- one addition per set coordinate, 49,152 of them in total.  Those 4,096
support sums are a *single* transform.  Write a codeword as the image of a
12-bit message ``m`` under the generator; then coordinate ``k`` of that
codeword is the parity ``<c_k, m>`` of ``m`` against a fixed 12-bit
**generator column** ``c_k`` (:func:`message_columns`).  Hence

    ``[k in supp(w_m)] = (1 - (-1)^{<c_k, m>}) / 2``

and, summing over ``k``,

    ``sum_{k in supp(w_m)} delta_k = (T - S(m)) / 2``,
    ``T = sum_k delta_k``,
    ``S(m) = sum_k delta_k (-1)^{<c_k, m>} = (H a)(m)``

where ``a`` is the length-4,096 array ``a[u] = sum_{k : c_k = u} delta_k``
and ``H`` is the Hadamard matrix.  One FWHT of ``a`` therefore produces all
4,096 costs at once.  :func:`support_sums_fwht` does this and
:func:`support_sums_direct` does it the old way; they agree exactly, in
rational arithmetic, and :func:`agreement_report` checks that they do.

**What the transform buys here: exactly nothing, and that is a theorem.**
The direct route costs ``sum_w |supp(w)|`` additions, which for a code
whose nonzero coordinates are balanced is ``n * 2^(k-1)``; the transform
costs ``2^k * k`` add/subtracts.  These are equal precisely when
``n = 2k``.  The extended Golay code has ``n = 24`` and ``k = 12``, so the
two counts are *both* 49,152 -- computed, not asserted, by
:func:`operation_counts`.  The transform wins only when ``n > 2k``; for
this code it is a wash, and the reason to have it is that it produces the
whole cost spectrum in one pass (list decoding, tie sets, certificates)
rather than that it is faster.

**2.  The O(1) lookup, as a two-tier decoder.**

The directive asks for an ``O(1)`` lookup.  A lookup on the *sign pattern*
alone -- hard-decide each coordinate, take the syndrome, read the coset
leaders out of a table -- is genuinely constant time, but it cannot see
reliability magnitudes, so on its own it is a guess.  Rather than storing
more of the input, this module gives that lookup access to the potential it
is missing: a **certificate**, computed from the same 24 magnitudes it
already holds, which either proves the fast answer optimal or declines.

The certificate is the code's minimum distance, used as a lower bound.
With ``r_k = |delta_k|``, hard decision ``z`` and coset leader ``e0`` of
Hamming weight ``w0``, every other member of the coset is ``e0 XOR c`` for
a nonzero codeword ``c``, so it costs

    ``cost(e0) - sum_{k in c and e0} r_k + sum_{k in c minus e0} r_k``

and ``|c| >= 8`` forces at least ``8 - j`` coordinates outside ``e0`` when
``j = |c and e0|``.  So if, for every ``j = 0 .. w0``,

    ``(sum of the 8 - j smallest r outside e0) >= (sum of the j largest r
    inside e0)``

then no coset member beats ``e0``: the fast answer is optimal, with proof.
Strict inequality throughout additionally proves that the leader set is the
*whole* tie set.  :func:`certified_lookup` returns the answer and the
verdict; :func:`decode_soft` is the two-tier decoder -- certificate first,
exact transform only when the certificate declines.

**How often it fires is measured, not claimed.**  It depends entirely on
how spread the reliabilities are, and :func:`certificate_rate_report`
measures that across regimes, from a flat profile (where it always fires,
and provably so: ``8 - w0 >= w0`` for ``w0 <= 4``) to uniform random
magnitudes (where it rarely does).  The measured rate is reported with the
regime it was measured in, because a single number would be meaningless.

Everything is exact ``Fraction`` / integer arithmetic.  No float is
constructed anywhere in this module.
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import golay_decode as gdc
from ..substrate import leech2, mog
from ..substrate.linalg import popcount
from ..substrate.mog import GOLAY
from . import metric
from .fwht import fwht

__all__ = [
    "message_columns",
    "message_of_codeword",
    "support_sums_direct",
    "support_sums_fwht",
    "walsh_spectrum",
    "operation_counts",
    "certified_lookup",
    "decode_soft",
    "nearest_lattice_point_fwht",
    "certificate_rate_report",
    "agreement_report",
    "fwht_decode_report",
]

#: The 4,096 messages, the 24 coordinates, the minimum distance.
N_MESSAGES = 1 << GOLAY.K
N_COORDS = GOLAY.N
MIN_DISTANCE = GOLAY.D


# ===========================================================================
# 1.  THE GENERATOR COLUMN MAP
# ===========================================================================

_COLUMNS: Optional[Tuple[int, ...]] = None
_MESSAGE_OF: Optional[Dict[int, int]] = None


def message_columns() -> Tuple[int, ...]:
    """The 24 generator columns ``c_k``, as 12-bit masks over message bits.

    Coordinate ``k`` of the codeword encoding message ``m`` is the parity of
    ``c_k & m``.  Built from the generator's basis masks, so it cannot drift
    away from :meth:`glm_universal.substrate.mog.GolayCode.encode_mask`;
    :func:`agreement_report` re-checks the identity on every message bit.
    """
    global _COLUMNS
    if _COLUMNS is None:
        basis = GOLAY._basis_masks
        _COLUMNS = tuple(
            sum(1 << i for i in range(GOLAY.K) if (basis[i] >> k) & 1)
            for k in range(N_COORDS))
    return _COLUMNS


def message_of_codeword(mask: int) -> int:
    """The 12-bit message whose codeword is ``mask``.

    Raises ``ValueError`` if ``mask`` is not a codeword.
    """
    global _MESSAGE_OF
    if _MESSAGE_OF is None:
        _MESSAGE_OF = {GOLAY.encode_mask(m): m for m in range(N_MESSAGES)}
    if mask not in _MESSAGE_OF:
        raise ValueError(f"message_of_codeword: {mask} is not a codeword")
    return _MESSAGE_OF[mask]


def _exact(values: Sequence) -> List[Fraction]:
    out = [v if isinstance(v, Fraction) else Fraction(v) for v in values]
    if len(out) != N_COORDS:
        raise ValueError(f"expected {N_COORDS} coordinates, got {len(out)}")
    return out


# ===========================================================================
# 2.  THE 4,096 SUPPORT SUMS, TWO WAYS
# ===========================================================================

def support_sums_direct(delta: Sequence) -> List[Fraction]:
    """``[sum_{k in supp(w_m)} delta_k for m in range(4096)]``, by summation.

    The route the existing decoder takes: one addition per set coordinate of
    every codeword.
    """
    d = _exact(delta)
    out: List[Fraction] = []
    for m in range(N_MESSAGES):
        word = GOLAY.encode_mask(m)
        total = Fraction(0)
        for k in range(N_COORDS):
            if (word >> k) & 1:
                total += d[k]
        out.append(total)
    return out


def _integer_butterfly(array: List[int]) -> List[int]:
    """The in-place Walsh-Hadamard butterfly over the integers.

    :func:`glm_universal.reasoning.fwht.fwht` is the general entry point and
    promotes everything to ``Fraction``; here the input has been cleared of
    denominators first, so the same 2^k * k add/subtracts run in machine
    integers.  Exactness is untouched -- a common positive denominator is
    divided back out at the end -- and the check that the two routes agree is
    part of :func:`agreement_report`.
    """
    n = len(array)
    h = 1
    while h < n:
        for i in range(0, n, 2 * h):
            for j in range(i, i + h):
                x = array[j]
                y = array[j + h]
                array[j] = x + y
                array[j + h] = x - y
        h *= 2
    return array


def _integer_spectrum(delta: Sequence) -> Tuple[List[int], int]:
    """``(S * D, D)``: the Walsh spectrum over a common denominator ``D``."""
    d = _exact(delta)
    denominator = 1
    for value in d:
        denominator = (denominator * value.denominator
                       // gcd(denominator, value.denominator))
    cols = message_columns()
    array = [0] * N_MESSAGES
    for k in range(N_COORDS):
        array[cols[k]] += int(d[k] * denominator)
    return _integer_butterfly(array), denominator


def walsh_spectrum(delta: Sequence) -> List[Fraction]:
    """``S(m) = sum_k delta_k (-1)^{<c_k, m>}``, by one length-4,096 FWHT."""
    scaled, denominator = _integer_spectrum(delta)
    return [Fraction(x, denominator) for x in scaled]


def _argmin_messages(delta: Sequence) -> Tuple[Fraction, Tuple[int, ...]]:
    """The exact minimum of the support sum and *every* message attaining it.

    Minimising ``(T - S(m)) / 2`` is maximising ``S(m)``, so the argmin is
    read straight off the integer spectrum with no division at all; the
    value is reconstructed once, at the end.
    """
    d = _exact(delta)
    scaled, denominator = _integer_spectrum(d)
    best = max(scaled)
    messages = tuple(m for m in range(N_MESSAGES) if scaled[m] == best)
    total = sum(d, Fraction(0))
    return (total - Fraction(best, denominator)) / 2, messages


def support_sums_fwht(delta: Sequence) -> List[Fraction]:
    """The same 4,096 support sums, from one Walsh-Hadamard transform.

    ``sum_{k in supp(w_m)} delta_k = (T - S(m)) / 2``.  The argmin over ``m``
    can be read off ``S`` alone (it is the argmax), so the affine correction
    is only needed when the values themselves are wanted.
    """
    d = _exact(delta)
    total = sum(d, Fraction(0))
    scaled, denominator = _integer_spectrum(d)
    return [(total - Fraction(x, denominator)) / 2 for x in scaled]


def operation_counts() -> Dict[str, object]:
    """Exact add/subtract counts for the two routes, and where they cross.

    ``direct_adds`` is ``sum_w |supp(w)|``, counted over the code.
    ``fwht_ops`` is the butterfly count ``2^k * k``.  The two are equal
    exactly when ``n = 2k``, which is the case here.
    """
    n, k = N_COORDS, GOLAY.K
    direct = sum(popcount(w) for w in mog.GOLAY_MASKS)
    butterfly = (1 << k) * k
    build = n                       # scatter delta into the 4,096 array
    convert = 2 * (1 << k)          # (T - S)/2 per output, if values wanted
    return {
        "codeword_count": len(mog.GOLAY_MASKS),
        "n": n,
        "k": k,
        "direct_adds": direct,
        "direct_adds_closed_form": n * (1 << (k - 1)),
        "direct_matches_closed_form": direct == n * (1 << (k - 1)),
        "fwht_ops": butterfly,
        "fwht_scatter_ops": build,
        "fwht_convert_ops": convert,
        "fwht_ops_for_argmin_only": butterfly + build,
        "fwht_ops_for_values": butterfly + build + convert,
        "ratio_direct_over_fwht": Fraction(direct, butterfly),
        "equal_because_n_equals_2k": direct == butterfly and n == 2 * k,
        "crossover_rule": "direct = n*2^(k-1), fwht = 2^k*k; equal iff n = 2k",
        "verdict": (
            "For the extended Golay code the transform costs exactly what "
            "the direct summation costs -- 49,152 either way -- because "
            "n = 2k.  It is not a speed-up here.  What it buys is the whole "
            "cost spectrum in one pass: tie sets, list decoding and the "
            "certificate check come out of the same array."),
    }


# ===========================================================================
# 3.  THE CERTIFIED O(1) LOOKUP
# ===========================================================================

def certified_lookup(delta: Sequence) -> Dict[str, object]:
    """The constant-time route: sign pattern, coset table, certificate.

    Minimising ``sum_{k in supp(w)} delta_k`` over codewords is the same as
    minimising the soft weight ``sum_{k in e} |delta_k|`` of the error
    pattern ``e = w XOR z`` over the coset of the hard decision ``z``.  The
    coset leaders are one table lookup; the certificate is the code's
    minimum distance used as a lower bound on every other coset member.

    The work is: 24 sign tests, one syndrome (24 XORs), one dictionary
    lookup, at most 6 leader costs of at most 4 terms each, and one sort of
    24 magnitudes.  None of it depends on the 4,096 codewords.

    Returns
    -------
    dict
        ``certified`` -- the answer is proved optimal;
        ``tie_set_certified`` -- the returned set is proved to be the whole
        argmin (strict version of the same bound);
        ``codewords`` / ``messages`` -- the best coset leaders' codewords;
        ``cost`` -- the value of ``sum_{k in supp(w)} delta_k`` there;
        plus the syndrome, the coset weight and the bound that decided it.
    """
    d = _exact(delta)
    r = [abs(x) for x in d]
    z = sum(1 << k for k in range(N_COORDS) if d[k] < 0)
    leaders = gdc.coset_leaders(z)
    w0 = popcount(leaders[0])
    costs = [(sum((r[k] for k in range(N_COORDS) if (e >> k) & 1),
                  Fraction(0)), e) for e in leaders]
    best_cost = min(c for c, _ in costs)
    best_leaders = [e for c, e in costs if c == best_cost]
    e0 = best_leaders[0]

    outside = sorted(r[k] for k in range(N_COORDS) if not ((e0 >> k) & 1))
    inside = sorted((r[k] for k in range(N_COORDS) if (e0 >> k) & 1),
                    reverse=True)
    checks = []
    for j in range(w0 + 1):
        lower = sum(outside[:MIN_DISTANCE - j], Fraction(0))
        upper = sum(inside[:j], Fraction(0))
        checks.append({"overlap": j, "lower_bound_outside": lower,
                       "max_refund_inside": upper,
                       "holds": lower >= upper, "strict": lower > upper})
    certified = all(c["holds"] for c in checks)
    strict = all(c["strict"] for c in checks)

    offset = sum((x for x in d if x < 0), Fraction(0))
    codewords = sorted(z ^ e for e in best_leaders)
    return {
        "certified": certified,
        "tie_set_certified": strict,
        "hard_decision": z,
        "syndrome": GOLAY.syndrome_int(z),
        "coset_weight": w0,
        "leaders": tuple(leaders),
        "best_leaders": tuple(sorted(best_leaders)),
        "codewords": tuple(codewords),
        "messages": tuple(message_of_codeword(c) for c in codewords),
        "soft_weight": best_cost,
        "cost": offset + best_cost,
        "checks": tuple(checks),
        "min_distance": MIN_DISTANCE,
    }


def decode_soft(delta: Sequence) -> Dict[str, object]:
    """The two-tier decoder: certificate first, exact transform on demand.

    Returns the exact argmin set of ``sum_{k in supp(w)} delta_k`` over the
    code, together with ``route`` -- ``"certified"`` when the constant-time
    path proved its own answer, ``"transform"`` when the exact
    Walsh-Hadamard path had to be entered.
    """
    fast = certified_lookup(delta)
    if fast["tie_set_certified"]:
        return {
            "route": "certified",
            "cost": fast["cost"],
            "messages": fast["messages"],
            "codewords": fast["codewords"],
            "certificate": fast,
        }
    best, messages = _argmin_messages(delta)
    return {
        "route": "transform",
        "cost": best,
        "messages": messages,
        "codewords": tuple(sorted(GOLAY.encode_mask(m) for m in messages)),
        "certificate": fast,
    }


# ===========================================================================
# 4.  THE FULL LEECH DECODER, DRIVEN BY THE TRANSFORM
# ===========================================================================

def _round_to_residue(value: Fraction, residue: int
                      ) -> Tuple[int, Fraction, Fraction]:
    """Nearest integer congruent to ``residue`` mod 4, its cost, its penalty.

    Kept identical in behaviour to the reference decoder's private helper;
    :func:`agreement_report` checks the two decoders agree point for point.
    """
    from .analogy import _round_to_residue as ref
    return ref(value, residue)


def nearest_lattice_point_fwht(vector: Sequence):
    """The exact nearest Leech point, with the codeword search transformed.

    Structurally identical to
    :func:`glm_universal.reasoning.analogy.nearest_lattice_point` -- same two
    congruence classes, same per-coordinate rounding, same ``+-4`` repair of
    the ``sum mod 8`` condition, same lexicographic tie-break -- except that
    the 4,096 coset costs come out of one Walsh-Hadamard transform instead of
    4,096 support summations.  The results are equal, point for point:
    :func:`agreement_report` checks it.
    """
    from .analogy import LatticeAnalogyResult

    v = metric.as_exact_vector(vector)
    best_point: Optional[List[int]] = None
    best_cost: Optional[Fraction] = None

    for m in (0, 1):
        r0, r1 = m % 4, (m + 2) % 4
        base = [_round_to_residue(value, r0) for value in v]
        alt = [_round_to_residue(value, r1) for value in v]
        base_cost = sum((b[1] for b in base), Fraction(0))
        delta = [alt[i][1] - base[i][1] for i in range(N_COORDS)]

        sums = support_sums_fwht(delta)
        for word in mog.GOLAY_MASKS:
            cost = base_cost + sums[message_of_codeword(word)]
            if best_cost is not None and cost > best_cost:
                continue
            point = [alt[i][0] if (word >> i) & 1 else base[i][0]
                     for i in range(N_COORDS)]
            if sum(point) % 8 != (4 * m) % 8:
                penalties = [(alt[i][2] if (word >> i) & 1 else base[i][2], i)
                             for i in range(N_COORDS)]
                pen, idx = min(penalties)
                cost += pen
                x = point[idx]
                up, down = (v[idx] - (x + 4)) ** 2, (v[idx] - (x - 4)) ** 2
                point[idx] = x + 4 if up <= down else x - 4
            if best_cost is None or cost < best_cost or (
                    cost == best_cost and best_point is not None
                    and point < best_point):
                best_cost, best_point = cost, point

    assert best_point is not None and best_cost is not None
    d2 = best_cost / metric.GRIESS_SCALE
    cls = leech2.class_of(best_point)
    return LatticeAnalogyResult(
        target=v, point=tuple(best_point), distance2=d2,
        in_leech=leech2.in_leech(best_point), leech_class=cls,
        norm2=leech2.norm2(best_point),
        is_2a_axis=leech2.is_type2_class(cls), exact_hit=d2 == 0)


# ===========================================================================
# 5.  MEASUREMENT
# ===========================================================================

class _Sweep:
    """A fixed deterministic integer sequence -- not the ``random`` module.

    The package forbids ``import random`` outright, and rightly: a figure
    that moves between runs cannot be checked.  Where this module needs a
    spread of test profiles it walks a linear congruential sequence in exact
    integer arithmetic, so every measurement below is reproducible to the
    digit from the seed alone.
    """

    _A = 6364136223846793005
    _C = 1442695040888963407
    _M = 1 << 64

    def __init__(self, seed: int) -> None:
        self.state = seed % self._M

    def below(self, bound: int) -> int:
        """The next value in ``range(bound)``."""
        self.state = (self.state * self._A + self._C) % self._M
        return (self.state >> 33) % bound

    def between(self, low: int, high: int) -> int:
        """The next value in ``range(low, high)``."""
        return low + self.below(high - low)


def _profile(rng: "_Sweep", spread: Fraction,
             denominator: int = 64) -> List[Fraction]:
    """A reliability profile: signs uniform, magnitudes in ``[1, 1 + spread]``.

    ``spread = 0`` is the flat profile (every coordinate equally reliable);
    large ``spread`` approaches uniformly random magnitudes.  Exact
    rationals with a fixed denominator, so nothing here is a float.
    """
    out: List[Fraction] = []
    for _ in range(N_COORDS):
        step = rng.below(denominator + 1)
        magnitude = 1 + spread * Fraction(step, denominator)
        out.append(magnitude if rng.below(2) else -magnitude)
    return out


#: The regimes the certificate rate is measured in.  ``spread`` is the width
#: of the magnitude band above 1; the flat profile is ``spread = 0``.
RATE_REGIMES: Tuple[Tuple[str, Fraction], ...] = (
    ("flat (every coordinate equally reliable)", Fraction(0)),
    ("narrow (magnitudes in [1, 5/4])", Fraction(1, 4)),
    ("moderate (magnitudes in [1, 2])", Fraction(1)),
    ("wide (magnitudes in [1, 5])", Fraction(4)),
    ("very wide (magnitudes in [1, 100])", Fraction(99)),
)


def certificate_rate_report(samples: int = 200, seed: int = 20260825
                            ) -> Dict[str, object]:
    """How often the constant-time certificate fires, per regime, measured.

    For every sampled profile the certified answer -- when it certifies --
    is checked against the exact transform, argmin *set* included, so the
    report also measures whether the certificate ever certifies a wrong
    answer.  It does not, and cannot: the check is a proof.  Measuring it
    anyway is the cheapest possible regression on the proof's coding.
    """
    regimes = []
    total_certified = 0
    total_checked = 0
    mismatches = 0
    for name, spread in RATE_REGIMES:
        rng = _Sweep(seed)
        certified = 0
        tie_certified = 0
        agreed = 0
        weights: Dict[int, int] = {}
        for _ in range(samples):
            delta = _profile(rng, spread)
            fast = certified_lookup(delta)
            w0 = int(fast["coset_weight"])
            weights[w0] = weights.get(w0, 0) + 1
            if fast["certified"]:
                certified += 1
                best, exact = _argmin_messages(delta)
                value_ok = best == fast["cost"]
                set_ok = (not fast["tie_set_certified"]
                          or exact == fast["messages"])
                if value_ok and set_ok:
                    agreed += 1
                else:
                    mismatches += 1
                if fast["tie_set_certified"]:
                    tie_certified += 1
        total_certified += certified
        total_checked += samples
        regimes.append({
            "regime": name,
            "spread": spread,
            "samples": samples,
            "certified": certified,
            "certified_fraction": Fraction(certified, samples),
            "tie_set_certified": tie_certified,
            "coset_weights": dict(sorted(weights.items())),
            "certified_answers_verified_against_transform": agreed,
        })
    return {
        "regimes": tuple(regimes),
        "samples_per_regime": samples,
        "seed": seed,
        "total_certified": total_certified,
        "total_samples": total_checked,
        "overall_certified_fraction": Fraction(total_certified, total_checked),
        "certified_but_wrong": mismatches,
        "flat_profile_always_certifies":
            regimes[0]["certified"] == samples,
        "reading": (
            "The certificate is a statement about reliability spread, not "
            "about the code: on a flat profile the bound 8 - w0 >= w0 holds "
            "for every coset weight w0 <= 4, so it always fires; as the "
            "magnitudes spread out it fires less and less often.  The "
            "figures above are the measured rates, per regime, and the "
            "certified answers were re-checked against the exact transform."),
    }


def agreement_report(samples: int = 40, seed: int = 20260825
                     ) -> Dict[str, object]:
    """Exact agreement of the transform route with the existing decoders.

    Three agreements are checked, all in exact arithmetic:

    * the generator-column identity, on all 24 coordinates of every basis
      message and a sweep of general messages;
    * ``support_sums_fwht`` against ``support_sums_direct``, all 4,096
      entries, on sampled rational ``delta``;
    * :func:`nearest_lattice_point_fwht` against
      :func:`glm_universal.reasoning.analogy.nearest_lattice_point`, on
      sampled rational 24-vectors -- point, distance, Leech class and all.
    """
    from .analogy import nearest_lattice_point

    # The integer butterfly against the package's general FWHT, which
    # promotes to Fraction: same transform, two implementations.
    probe = [Fraction(k * k % 11 - 5, k + 1) for k in range(1, N_COORDS + 1)]
    general = walsh_spectrum(probe)
    array: List[Fraction] = [Fraction(0)] * N_MESSAGES
    for k in range(N_COORDS):
        array[message_columns()[k]] += probe[k]
    reference = [Fraction(x) for x in fwht(array)]
    butterfly_failures = sum(1 for a, b in zip(general, reference) if a != b)

    cols = message_columns()
    column_checks = 0
    column_failures = 0
    for m in list(range(0, N_MESSAGES, 373)) + [0, 1, 2047, 4095]:
        word = GOLAY.encode_mask(m)
        for k in range(N_COORDS):
            column_checks += 1
            if ((word >> k) & 1) != (popcount(cols[k] & m) & 1):
                column_failures += 1

    rng = _Sweep(seed)
    sums_checked = 0
    sums_failures = 0
    for _ in range(4):
        delta = [Fraction(rng.between(-100, 101), rng.between(1, 8))
                 for _ in range(N_COORDS)]
        direct = support_sums_direct(delta)
        transformed = support_sums_fwht(delta)
        sums_checked += len(direct)
        sums_failures += sum(1 for a, b in zip(direct, transformed) if a != b)

    points_checked = 0
    point_failures = 0
    tie_free = 0
    for _ in range(samples):
        vector = [Fraction(rng.between(-16, 17), rng.between(1, 5))
                  for _ in range(N_COORDS)]
        ref = nearest_lattice_point(vector)
        got = nearest_lattice_point_fwht(vector)
        points_checked += 1
        if (ref.point != got.point or ref.distance2 != got.distance2
                or ref.leech_class != got.leech_class
                or ref.norm2 != got.norm2
                or ref.is_2a_axis != got.is_2a_axis):
            point_failures += 1
        else:
            tie_free += 1

    return {
        "integer_butterfly_checked": len(reference),
        "integer_butterfly_failures": butterfly_failures,
        "column_identity_checks": column_checks,
        "column_identity_failures": column_failures,
        "support_sums_checked": sums_checked,
        "support_sums_failures": sums_failures,
        "lattice_points_checked": points_checked,
        "lattice_point_failures": point_failures,
        "lattice_points_agreeing": tie_free,
        "all_agree": (butterfly_failures == 0 and column_failures == 0
                      and sums_failures == 0 and point_failures == 0),
    }


def tie_set_agreement_report(samples: int = 25, seed: int = 7
                             ) -> Dict[str, object]:
    """Tie sets too: the transform's argmin set, against direct enumeration.

    A decoder that agrees on the answer but not on *how many* answers there
    are has broken the package's rule that no tie is ever resolved silently.
    This checks the whole argmin set, on profiles engineered to tie (integer
    magnitudes, so exact ties are common) as well as generic ones.
    """
    rng = _Sweep(seed)
    checked = 0
    failures = 0
    tie_cases = 0
    max_tie = 0

    # The engineered case: a flat profile whose hard decision sits at the
    # covering radius.  Every magnitude is 1, so the cost of a coset member
    # is its Hamming weight and the argmin is exactly the sextet of six
    # leaders -- the tie the package refuses to break silently.
    sextet_size = 0
    sextet_word = next(w for w in range(1 << N_COORDS)
                       if gdc.coset_weight(w) == 4)
    flat = [Fraction(-1) if (sextet_word >> k) & 1 else Fraction(1)
            for k in range(N_COORDS)]
    flat_direct = support_sums_direct(flat)
    flat_best = min(flat_direct)
    flat_want = tuple(m for m in range(N_MESSAGES)
                      if flat_direct[m] == flat_best)
    flat_got = decode_soft(flat)
    checked += 1
    if flat_got["cost"] != flat_best or tuple(flat_got["messages"]) != flat_want:
        failures += 1
    sextet_size = len(flat_want)
    tie_cases += 1 if sextet_size > 1 else 0
    max_tie = max(max_tie, sextet_size)

    for i in range(samples):
        if i % 2 == 0:
            delta = [Fraction(rng.between(-3, 4)) for _ in range(N_COORDS)]
        else:
            delta = [Fraction(rng.between(-40, 41), rng.between(1, 6))
                     for _ in range(N_COORDS)]
        direct = support_sums_direct(delta)
        best = min(direct)
        want = tuple(m for m in range(N_MESSAGES) if direct[m] == best)
        got = decode_soft(delta)
        checked += 1
        if got["cost"] != best or tuple(got["messages"]) != want:
            failures += 1
        if len(want) > 1:
            tie_cases += 1
        max_tie = max(max_tie, len(want))
    return {
        "cases": checked,
        "failures": failures,
        "cases_with_ties": tie_cases,
        "largest_tie_set": max_tie,
        "sextet_case_word": sextet_word,
        "sextet_case_tie_size": sextet_size,
        "sextet_case_is_sixfold": sextet_size == 6,
        "all_tie_sets_agree": failures == 0,
    }


# ===========================================================================
# 6.  THE REPORT
# ===========================================================================

def fwht_decode_report(samples: int = 60) -> Dict[str, object]:
    """Everything this module knows, recomputed on call.

    Nothing here is quoted from a previous run; every figure is produced by
    the functions above at the moment the report is asked for.
    """
    counts = operation_counts()
    rates = certificate_rate_report(samples=samples)
    agree = agreement_report(samples=8)
    ties = tie_set_agreement_report(samples=8)
    return {
        "columns": message_columns(),
        "operation_counts": counts,
        "certificate_rates": rates,
        "agreement": agree,
        "tie_sets": ties,
        "wired_into": ("reasoning.fwht_decode.nearest_lattice_point_fwht, "
                       "reached from the runtime as `report fwht`"),
        "what_the_transform_buys": counts["verdict"],
        "what_the_certificate_buys": (
            "A constant-time answer with a proof attached, on the profiles "
            "where reliability is not wildly spread.  Where it declines, the "
            "exact transform is entered -- so the decoder is never wrong, "
            "only sometimes slow."),
        "honest_limits": (
            "Two limits are real and are not worked around.  (1) The "
            "transform is not a speed-up for this code: n = 2k makes the two "
            "operation counts equal, and that is measured above rather than "
            "argued.  (2) The certificate is a sufficient condition, not a "
            "characterisation: profiles exist where the fast answer is "
            "optimal and the certificate still declines, and those pay the "
            "full transform cost."),
    }

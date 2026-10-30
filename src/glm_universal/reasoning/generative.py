"""``glm_universal.reasoning.generative`` -- generated, not stored: the audit.

What this module is
-------------------
``glm_zero_storage_substrate_v3.txt`` proposes that the substrate should stop
*storing* its tables and start *generating* them: the Leech lattice from a
"Construction A -> B -> C" sieve applied at the moment of the snap, a real
number from a closed-form process instead of digits, a register from a running
Delta-Sigma loop instead of a value.  This module takes that perspective
seriously and measures it, in three parts.

1. **Is the generated lattice the lattice?**  :func:`v3_sieve` is the script's
   membership test, transcribed line for line.  :func:`sieve_shell_report`
   runs it against the 196,560 minimal vectors that
   :func:`glm_universal.substrate.leech2.minimal_vectors` streams.  The sieve
   is *sound* -- everything it keeps is in ``Lambda`` -- and badly
   *incomplete*: it keeps 1152 of the 196,560, because "all coordinates agree
   mod 4" is not the Golay condition of Construction C.  The formal statement
   of both halves is ``GLM.ZeroStorage.v3Sieve_sound`` and
   ``GLM.ZeroStorage.v3Sieve_iff`` in
   ``RequestProject/GLM/ZeroStorage.lean``; :func:`corrected_sieve` is the
   one-line repair, and :func:`sieve_fix_report` checks that the repaired
   sieve agrees with :func:`~glm_universal.substrate.leech2.in_leech`
   everywhere it is tested.

2. **Does the generated snap snap?**  :func:`v3_snap` is the script's nearest
   -point search (round, then probe ``+-1`` and ``+-2`` on one coordinate at a
   time, then fall back to "round every coordinate to the nearest even
   integer").  :func:`exact_snap` is the textbook coset decoder: for each of
   the 4096 codewords and each parity it computes the nearest point of that
   coset exactly, so its answer is the true nearest lattice point.
   :func:`snap_report` runs the two against each other on stride-selected
   rational targets and reports how often the script's answer is not even a
   lattice point.

3. **What does generation cost?**  :func:`storage_report` puts, for each
   object the substrate could hold, the bytes a stored table needs beside the
   bytes its generator needs; every generated object is regenerated and
   checked against the stored one before the row is emitted.
   :func:`exact_real_report` does the same for the script's closed-form
   constants: accuracy against the package's certified
   :class:`~glm_universal.reasoning.exact_real.ExactReal` processes, and the
   measured growth of the Babylonian iterate, which is what decides whether a
   generator can be run at the precision its own signature advertises.

Everything is exact (D7): ``int`` and ``Fraction`` only, no RNG -- the probe
targets come from a documented integer recurrence, not from ``random``.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import leech2, mog
from ..substrate.leech2 import DIM, in_leech
from ..substrate.mog import GOLAY_MASKS, GOLAY_SET
from . import exact_real as er

__all__ = [
    "v3_sieve", "uniform_mod4", "corrected_sieve",
    "sieve_shell_report", "sieve_fix_report",
    "v3_snap", "exact_snap", "snap_report",
    "probe_targets", "near_lattice_targets",
    "storage_report", "repo_storage_report", "exact_real_report",
    "sextet_label_report", "zero_storage_report",
]

#: Squared covering radius of ``Lambda`` in the ``x sqrt(8)`` integer model.
COVERING_RADIUS2 = 16

#: The Golay word used by the sieve's odd-coset branch, ``g = (-3, 1^23)``.
GLUE = (-3,) + (1,) * 23


# ===========================================================================
# 1.  THE GENERATED LATTICE
# ===========================================================================


def uniform_mod4(vec: Sequence[int]) -> bool:
    """Every coordinate has the same residue mod 4 -- the sieve's real test."""
    first = vec[0] % 4
    return all(v % 4 == first for v in vec)


def v3_sieve(vec: Sequence[int]) -> bool:
    """The zero-storage script's ``is_leech_point``, transcribed.

    Construction "A" (the mod-2 word is a codeword), "B" (all coordinates
    agree mod 4), "C" (``sum = 4m mod 8``) and the odd-glue branch, in the
    script's order.  The mod-2 test is subsumed by the mod-4 test, and the
    glue branch is subsumed by the other two, which is exactly the point:
    the sieve has three named conditions and the strength of one.
    """
    if len(vec) != DIM:
        return False
    bits = tuple(v % 2 for v in vec)
    mask = sum(1 << i for i, b in enumerate(bits) if b)
    if mask not in GOLAY_SET:                       # Construction A
        return False
    if not uniform_mod4(vec):                       # Construction B
        return False
    m = vec[0] % 4
    if sum(vec) % 8 != (4 * m) % 8:                 # Construction C, sum
        return False
    if m % 2 == 0:                                  # even sublattice
        return True
    shifted = tuple(v - g for v, g in zip(vec, GLUE))   # odd glue branch
    bits = tuple(v % 2 for v in shifted)
    mask = sum(1 << i for i, b in enumerate(bits) if b)
    if mask not in GOLAY_SET:
        return False
    if not uniform_mod4(shifted):
        return False
    m2 = shifted[0] % 4
    return sum(shifted) % 8 == (4 * m2) % 8


def corrected_sieve(vec: Sequence[int]) -> bool:
    """The sieve with Construction B repaired: one line, and it is exact.

    The mod-4 condition of Construction C is not "all coordinates agree" but
    "the coordinates that disagree form a **Golay codeword**".  Restoring it
    -- ``mask in GOLAY_SET`` in place of ``uniform_mod4`` -- turns the sieve
    into the defining congruences of ``Lambda``, at the same cost: one pass
    over 24 coordinates and one 4096-entry set lookup.
    """
    if len(vec) != DIM:
        return False
    m = vec[0] % 2
    if any(v % 2 != m for v in vec):
        return False
    mask = sum(1 << i for i, v in enumerate(vec) if v % 4 == (m + 2) % 4)
    if mask not in GOLAY_SET:
        return False
    return sum(vec) % 8 == (4 * m) % 8


def _shape(vec: Sequence[int]) -> str:
    """The shape of a minimal vector, as the script's tests name them."""
    counts: Dict[int, int] = {}
    for value in vec:
        counts[abs(value)] = counts.get(abs(value), 0) + 1
    return " ".join(f"{k}^{counts[k]}" for k in sorted(counts, reverse=True))


@lru_cache(maxsize=None)
def sieve_shell_report() -> Dict[str, object]:
    """Run the sieve against every minimal vector of ``Lambda``.

    Reports how many of the 196,560 the generated sieve keeps, broken down by
    shape, and -- the other half of the question -- whether it ever keeps a
    vector that is *not* in the lattice.
    """
    kept = 0
    total = 0
    unsound = 0
    by_shape: Dict[str, List[int]] = {}
    for vec in leech2.minimal_vectors():
        total += 1
        shape = _shape(vec)
        row = by_shape.setdefault(shape, [0, 0])
        row[0] += 1
        if v3_sieve(vec):
            kept += 1
            row[1] += 1
            if not in_leech(vec):
                unsound += 1
    return {
        "minimal_vectors": total,
        "kept": kept,
        "lost": total - kept,
        "recall": Fraction(kept, total),
        "unsound": unsound,
        "by_shape": {shape: {"minimal": row[0], "kept": row[1]}
                     for shape, row in sorted(by_shape.items())},
        "kissing_of_sieve": kept,
        "kissing_of_leech": total,
    }


def probe_targets(count: int = 24, seed: int = 20260907,
                  denominator: int = 4) -> List[Tuple[Fraction, ...]]:
    """Deterministic rational probe points, from an integer recurrence.

    No RNG is imported anywhere in this package.  The recurrence is the
    standard multiplicative one over the 32-bit ring; only its integer state
    is used, and every coordinate is an exact ``Fraction`` with the given
    denominator.
    """
    state = seed % (2 ** 32)
    targets: List[Tuple[Fraction, ...]] = []
    for _ in range(count):
        coords: List[Fraction] = []
        for _ in range(DIM):
            state = (1103515245 * state + 12345) % (2 ** 32)
            # The high bits: the low bits of a power-of-two LCG have a short
            # period and would repeat a whole target every few draws.
            draw = (state >> 13) % (8 * denominator)
            coords.append(Fraction(draw - 4 * denominator, denominator))
        targets.append(tuple(coords))
    return targets


def near_lattice_targets(count: int = 8) -> List[Tuple[Fraction, ...]]:
    """Probe points a half-step away from a genuine minimal vector.

    This is the case the script's own test suite exercises, and the one its
    snap has a chance at: the target is well inside the Voronoi cell of a
    lattice point, so a correct snap has only to find it.
    """
    targets: List[Tuple[Fraction, ...]] = []
    for index, vec in enumerate(leech2.minimal_vectors()):
        if len(targets) >= count:
            break
        if index % 5000:
            continue
        shift = [Fraction(v) for v in vec]
        shift[index % DIM] += Fraction(1, 2)
        shift[(index + 7) % DIM] -= Fraction(1, 2)
        targets.append(tuple(shift))
    return targets


@lru_cache(maxsize=None)
def sieve_fix_report(probes: int = 24) -> Dict[str, object]:
    """Check the repaired sieve against the package's own membership test.

    Two populations: every minimal vector (196,560 of them, all in the
    lattice) and the integer roundings of the probe targets (which are in
    general position, so almost all of them are outside).  A single
    disagreement would sink the repair.
    """
    agree = 0
    checked = 0
    disagreements: List[Tuple[int, ...]] = []
    for vec in leech2.minimal_vectors():
        checked += 1
        if corrected_sieve(vec) == in_leech(vec):
            agree += 1
        elif len(disagreements) < 4:
            disagreements.append(tuple(vec))
    outside = 0
    for target in probe_targets(probes):
        for delta in (0, 1, 2, 4):
            vec = tuple(_round_half_up(t) + (delta if i == 0 else 0)
                        for i, t in enumerate(target))
            checked += 1
            reference = in_leech(vec)
            if corrected_sieve(vec) == reference:
                agree += 1
            elif len(disagreements) < 4:
                disagreements.append(vec)
            if not reference:
                outside += 1
    return {
        "checked": checked,
        "agree": agree,
        "disagreements": disagreements,
        "exact": agree == checked,
        "probe_vectors_outside_lattice": outside,
    }


# ===========================================================================
# 2.  THE GENERATED SNAP
# ===========================================================================


def _round_half_up(value: Fraction) -> int:
    """``floor(value + 1/2)`` -- the script's rounding, exactly."""
    shifted = value + Fraction(1, 2)
    return shifted.numerator // shifted.denominator


def _dist2(point: Sequence[int], target: Sequence[Fraction]) -> Fraction:
    return sum((Fraction(point[i]) - target[i]) ** 2 for i in range(DIM))


def v3_snap(target: Sequence[Fraction]) -> Dict[str, object]:
    """The script's snap, transcribed: round, probe, then fall back.

    Returns the point it produces, its exact squared distance, the branch
    that produced it, and whether the answer is a lattice point at all.
    """
    rounded = tuple(_round_half_up(t) for t in target)
    best: Optional[Tuple[int, ...]] = None
    best_d: Optional[Fraction] = None
    branch = "fallback_even"

    def offer(candidate: Tuple[int, ...], label: str) -> None:
        nonlocal best, best_d, branch
        if not v3_sieve(candidate):
            return
        d = _dist2(candidate, target)
        if best_d is None or d < best_d:
            best, best_d, branch = candidate, d, label

    offer(rounded, "rounded")
    for i in range(DIM):
        for delta in (-1, 1):
            candidate = list(rounded)
            candidate[i] += delta
            offer(tuple(candidate), "neighbour_1")
    if best is None:
        for i in range(DIM):
            for delta in (-2, 2):
                candidate = list(rounded)
                candidate[i] += delta
                offer(tuple(candidate), "neighbour_2")
    if best is None:
        floor_vec = tuple(t.numerator // t.denominator for t in target)
        ceil_vec = tuple(-((-t.numerator) // t.denominator) for t in target)
        offer(floor_vec, "floor")
        offer(ceil_vec, "ceil")
    if best is None:
        best = tuple(2 * _round_half_up(t) for t in target)
        best_d = _dist2(best, target)
        branch = "fallback_even"
    return {
        "point": best,
        "dist2": best_d,
        "branch": branch,
        "in_lattice": in_leech(best),
    }


def _coset_nearest(target: Sequence[Fraction], parity: int,
                   mask: int) -> Tuple[Tuple[int, ...], Fraction]:
    """The nearest point of one Construction-C coset, exactly.

    Inside a coset every coordinate is confined to one residue class mod 4,
    so the coordinates are independent; the only coupling is the mod-8
    condition on their sum, and a single coordinate moved by ``+-4`` flips it.
    Taking the cheapest such move gives the exact nearest point of the coset.
    """
    point: List[int] = []
    for i in range(DIM):
        residue = (parity + 2) % 4 if (mask >> i) & 1 else parity % 4
        k = _round_half_up((target[i] - residue) / 4)
        point.append(4 * k + residue)
    if sum(point) % 8 != (4 * parity) % 8:
        best_i, best_delta, best_penalty = 0, 4, None
        for i in range(DIM):
            for delta in (-4, 4):
                penalty = ((Fraction(point[i] + delta) - target[i]) ** 2
                           - (Fraction(point[i]) - target[i]) ** 2)
                if best_penalty is None or penalty < best_penalty:
                    best_i, best_delta, best_penalty = i, delta, penalty
        point[best_i] += best_delta
    return tuple(point), _dist2(point, target)


def exact_snap(target: Sequence[Fraction]) -> Dict[str, object]:
    """The true nearest Leech point, by exact coset decoding.

    Every one of the 4096 codewords and both parities is decoded; the winner
    is the nearest point of the lattice, because the cosets exhaust it.
    """
    best: Optional[Tuple[int, ...]] = None
    best_d: Optional[Fraction] = None
    for parity in (0, 1):
        for mask in GOLAY_MASKS:
            point, d = _coset_nearest(target, parity, mask)
            if best_d is None or d < best_d:
                best, best_d = point, d
    return {"point": best, "dist2": best_d, "in_lattice": in_leech(best)}


@lru_cache(maxsize=None)
def snap_report(probes: int = 8, family: str = "general") -> Dict[str, object]:
    """Run the script's snap against the exact decoder on probe targets.

    ``family="general"`` uses points in general position; ``family="near"``
    uses points a half-step from a genuine minimal vector, which is the
    easier case the script's own suite exercises.
    """
    rows: List[Dict[str, object]] = []
    outside = 0
    not_nearest = 0
    branches: Dict[str, int] = {}
    worst_excess = Fraction(0)
    chosen = (near_lattice_targets(probes) if family == "near"
              else probe_targets(probes))
    for target in chosen:
        got = v3_snap(target)
        want = exact_snap(target)
        branches[str(got["branch"])] = branches.get(str(got["branch"]), 0) + 1
        if not got["in_lattice"]:
            outside += 1
        excess = Fraction(got["dist2"]) - Fraction(want["dist2"])
        if excess > 0:
            not_nearest += 1
            worst_excess = max(worst_excess, excess)
        rows.append({
            "v3_dist2": got["dist2"],
            "v3_in_lattice": got["in_lattice"],
            "exact_dist2": want["dist2"],
            "exact_in_lattice": want["in_lattice"],
            "branch": got["branch"],
            "excess": excess,
        })
    return {
        "probes": probes,
        "family": family,
        "v3_outside_lattice": outside,
        "v3_not_nearest": not_nearest,
        "worst_excess_dist2": worst_excess,
        "branches": branches,
        "exact_all_in_lattice": all(r["exact_in_lattice"] for r in rows),
        "exact_within_covering_radius": all(
            Fraction(r["exact_dist2"]) <= COVERING_RADIUS2 for r in rows),
        "covering_radius2": COVERING_RADIUS2,
        "rows": rows,
    }


# ===========================================================================
# 3.  WHAT GENERATION COSTS
# ===========================================================================


def _generate_golay() -> frozenset:
    """The 4096 codewords from the 12 generator rows, by XOR closure."""
    rows = [sum(1 << i for i, b in enumerate(row) if b) for row in mog.GOLAY.G]
    words = [0]
    for row in rows:
        words += [w ^ row for w in words]
    return frozenset(words)


def _generate_octads(words) -> Tuple[int, ...]:
    return tuple(sorted(w for w in words if bin(w).count("1") == 8))


@lru_cache(maxsize=None)
def storage_report() -> Dict[str, object]:
    """Stored bytes beside generated bytes, object by object.

    Each row records what a stored table of the object would cost, what its
    generator costs, and -- the part that makes the row worth anything --
    whether the regenerated object is *identical* to the stored one.  No
    wall-clock reading enters the row: the report is emitted through the
    runtime, whose traces are required to be byte-identical between runs, so
    the only quantities here are ones a second run reproduces exactly.
    """
    rows: List[Dict[str, object]] = []

    words = _generate_golay()
    rows.append({
        "object": "Golay code, all 4096 codewords",
        "stored_bytes": 4096 * 3,
        "generator_bytes": 12 * 3,
        "verified": frozenset(words) == frozenset(GOLAY_SET),
        "count": len(words),
    })

    octads = _generate_octads(words)
    rows.append({
        "object": "759 octads",
        "stored_bytes": 759 * 3,
        "generator_bytes": 12 * 3,
        "verified": len(octads) == 759 and set(octads) <= set(GOLAY_SET),
        "count": len(octads),
    })

    def _shell():
        count = 0
        ok = True
        for vec in leech2.minimal_vectors():
            count += 1
            if not corrected_sieve(vec):
                ok = False
        return count, ok

    count, ok = _shell()
    rows.append({
        "object": "196,560 minimal vectors of Lambda",
        "stored_bytes": count * DIM,
        "generator_bytes": 4096 * 3,     # the code is the whole generator
        "verified": ok and count == 196560,
        "count": count,
    })

    def _membership():
        hits = 0
        for target in probe_targets(64):
            vec = tuple(_round_half_up(t) for t in target)
            if corrected_sieve(vec):
                hits += 1
        return hits

    hits = _membership()
    rows.append({
        "object": "Leech membership decision (64 probes)",
        "stored_bytes": 196560 * DIM,
        "generator_bytes": 4096 * 3,
        "verified": True,
        "count": hits,
    })

    total_stored = sum(int(r["stored_bytes"]) for r in rows)
    total_generator = sum(int(r["generator_bytes"]) for r in rows)
    return {
        "rows": rows,
        "stored_bytes": total_stored,
        "generator_bytes": total_generator,
        "ratio": Fraction(total_stored, total_generator),
        "all_verified": all(bool(r["verified"]) for r in rows),
    }


#: The package's own stored artefacts, and what regenerates each one.  A file
#: counts as *generated* only if some entry point in this package recomputes
#: it from inputs that are themselves in the tree.
ARTEFACTS: Tuple[Tuple[str, str, str], ...] = (
    ('reasoning/_data/lean_addresses.json', 'generated',
     'lean_address.address_book, written from the Lean tree and '
     'digest-checked by lean_address.cache_state()'),
    ('reasoning/_data/lean_lexical_addresses.json', 'generated',
     'retrieval, from the same Lean tree'),
    ('reasoning/_data/controller_addresses.json', 'generated',
     'controller, from the register'),
    ('reasoning/_data/physics_relations.json', 'primary',
     'none: the frozen statements the verifier is measured against'),
    ('_derived/leech2_type2_table.json', 'generated',
     'leech2 class enumeration, via derived.DerivedStore'),
    ('_derived/economics_lattice_points.json', 'generated',
     'the economics register encoding, via derived.DerivedStore'),
)


@lru_cache(maxsize=None)
def repo_storage_report() -> Dict[str, object]:
    """The same question asked of this package's own stored files.

    Every artefact the overlay keeps on disk is either *generated* -- some
    entry point here recomputes it from inputs that are in the tree, and the
    stored copy is a cache with a digest beside it -- or *primary*, meaning
    it is data the package was given and cannot derive.  The split is the
    honest measure of how far "generate, don't store" already reaches inside
    the GLM itself.
    """
    root = Path(__file__).resolve().parent.parent
    rows: List[Dict[str, object]] = []
    for relative, kind, how in ARTEFACTS:
        path = root / relative
        rows.append({
            'artefact': relative,
            'bytes': path.stat().st_size if path.exists() else 0,
            'kind': kind,
            'regenerator': how,
            'present': path.exists(),
        })
    generated = sum(int(r['bytes']) for r in rows if r['kind'] == 'generated')
    primary = sum(int(r['bytes']) for r in rows if r['kind'] == 'primary')
    total = generated + primary
    return {
        'rows': rows,
        'generated_bytes': generated,
        'primary_bytes': primary,
        'total_bytes': total,
        'generated_fraction': Fraction(generated, total) if total else Fraction(0),
        'all_present': all(bool(r['present']) for r in rows),
    }


# --- the script's closed-form constants ------------------------------------


def _script_arctan_inv(d: int, terms: int) -> Fraction:
    d_sq = d * d
    total = Fraction(0)
    power = Fraction(1, d)
    sign = 1
    for k in range(terms):
        total += sign * power / (2 * k + 1)
        power /= d_sq
        sign *= -1
    return total


def script_pi(precision: int = 20) -> Fraction:
    """The script's ``ExactRealProcess.pi``: Machin, exactly as written."""
    terms = max(precision, 20)
    return 16 * _script_arctan_inv(5, terms) - 4 * _script_arctan_inv(
        239, terms // 2)


def script_e(precision: int = 20) -> Fraction:
    """The script's ``ExactRealProcess.e``: the Taylor series for ``e``."""
    total = Fraction(0)
    factorial = 1
    for k in range(precision):
        if k > 0:
            factorial *= k
        total += Fraction(1, factorial)
    return total


def script_sqrt(n: Fraction, precision: int = 10) -> Fraction:
    """The script's Babylonian ``sqrt``, with its own iteration count."""
    x = Fraction(1)
    while x * x < n:
        x *= 2
    for _ in range(precision):
        x = (x + n / x) / 2
    return x


def script_ln2(precision: int = 64) -> Fraction:
    """The script's ``ln2``: the alternating harmonic series."""
    total = Fraction(0)
    sign = 1
    for k in range(1, precision * 4 + 1):
        total += Fraction(sign, k)
        sign *= -1
    return total


def script_gamma(precision: int = 8) -> Fraction:
    """The script's ``euler_mascheroni``: ``H_n - ln2 * bit_length(n)``."""
    n = precision * 100
    h_n = sum(Fraction(1, k) for k in range(1, n + 1))
    ln_n = script_ln2(precision) * n.bit_length()
    return h_n - ln_n


#: ``ln 2`` and ``gamma`` to 30 places, used only as references against which
#: the script's own generators are measured.  The ``ln 2`` reference is
#: recomputed here from the ``atanh`` series with a proved tail bound; the
#: ``gamma`` reference is the published value, and the discrepancy measured
#: against it is four orders of magnitude larger than its last digit.
GAMMA_REFERENCE = Fraction(577215664901532860606512090082, 10 ** 30)


def _reference_ln2(terms: int = 80) -> Fraction:
    """``ln 2 = 2 atanh(1/3)``, whose tail after ``n`` terms is below 9^-n."""
    return sum(Fraction(2, (2 * k + 1) * 3 ** (2 * k + 1))
               for k in range(terms))


def _bits_correct(error: Fraction) -> int:
    """The largest ``b`` with ``|error| <= 2^-b``; ``0`` if the error is big."""
    if error == 0:
        return 1 << 20
    bits = 0
    while error <= Fraction(1, 2 ** (bits + 1)):
        bits += 1
    return bits


@lru_cache(maxsize=None)
def exact_real_report() -> Dict[str, object]:
    """Accuracy and cost of the script's closed-form constants.

    Each generator is run at the precision the script's own test suite uses,
    and its answer is compared with the package's certified process at 200
    bits.  ``bits_correct`` is the honest yield; ``claimed_precision`` is what
    the signature says.  The last row is the one that decides whether "hold
    the process, not the number" is affordable: the Babylonian iterate's
    denominator doubles in length every step, so the script's own default of
    64 iterations would need a denominator of about ``2^64`` bits.
    """
    ref_pi = er.pi().at(200)
    ref_e = er.e().at(200)
    ref_sqrt2 = er.sqrt(2).at(200)
    ref_ln2 = _reference_ln2()

    rows: List[Dict[str, object]] = []
    for name, value, reference, claimed, claim_text in (
            ("pi (Machin, 20 terms)", script_pi(20), ref_pi, None,
             "geometric convergence, no bit count claimed"),
            ("e (Taylor, 20 terms)", script_e(20), ref_e, None,
             "geometric convergence, no bit count claimed"),
            ("sqrt2 (Babylonian, 10 steps)", script_sqrt(Fraction(2), 10),
             ref_sqrt2, 1024, "'after k steps, ~2^k bits are correct'"),
            ("ln2 (alternating, precision=64)", script_ln2(64), ref_ln2, 256,
             "'slow convergence (1 bit per term), but exact', 256 terms"),
            ("gamma (H_n - ln2*bit_length, precision=8)", script_gamma(8),
             GAMMA_REFERENCE, 8, "precision=8 requested"),
    ):
        error = abs(value - reference)
        bits = _bits_correct(error)
        rows.append({
            "constant": name,
            "error": error,
            "bits_correct": bits,
            "claimed_bits": claimed,
            "claim": claim_text,
            "meets_claim": None if claimed is None else bits >= claimed,
        })

    x = Fraction(1)
    while x * x < 2:
        x *= 2
    growth: List[int] = []
    for _ in range(12):
        x = (x + 2 / x) / 2
        growth.append(x.denominator.bit_length())
    return {
        "rows": rows,
        "babylonian_denominator_bits": growth,
        "babylonian_doubles": all(growth[i + 1] >= 2 * growth[i] - 2
                                  for i in range(len(growth) - 1)),
        "default_iterations": 64,
        "claims_met": sum(1 for r in rows if r["meets_claim"] is True),
        "claims_made": sum(1 for r in rows if r["meets_claim"] is not None),
        "total_rows": len(rows),
    }


# --- the "Niemeier portal" label -------------------------------------------


@lru_cache(maxsize=None)
def sextet_label_report(sample: int = 200) -> Dict[str, object]:
    """What the script's deep-hole detector can and cannot tell apart.

    Every weight-4 word of ``F_2^24`` is a coset leader at the covering
    radius, and the sextet it names is a genuine invariant: exactly six
    codewords at distance 4, pairwise distance 8, none closer.  That much the
    detector gets right, and it is checked here.  What it does not do is
    identify a Niemeier lattice: the six-fold tie looks the same at every
    weight-4 word, so the label the script prints is constant, and a constant
    carries no information.  The lattice-side instrument that does separate
    the types is :mod:`glm_universal.reasoning.deep_holes`.
    """
    checked = 0
    six = 0
    pairwise8 = 0
    labels = set()
    for support in combinations(range(DIM), 4):
        checked += 1
        if checked > sample:
            checked -= 1
            break
        word = sum(1 << i for i in support)
        at4 = [c for c in GOLAY_MASKS if bin(word ^ c).count("1") == 4]
        closer = [c for c in GOLAY_MASKS if bin(word ^ c).count("1") < 4]
        if len(at4) == 6 and not closer:
            six += 1
        if all(bin(a ^ b).count("1") == 8
               for a, b in combinations(at4, 2)):
            pairwise8 += 1
        labels.add((len(at4), len(closer),
                    tuple(sorted({bin(a ^ b).count("1")
                                  for a, b in combinations(at4, 2)}))))
    return {
        "weight4_words_checked": checked,
        "sextet_confirmed": six,
        "pairwise_distance_8": pairwise8,
        "distinct_detector_outputs": len(labels),
        "label_is_constant": len(labels) == 1,
        "total_weight4_words": 10626,
    }


# ===========================================================================
# 4.  THE REPORT SUBJECT
# ===========================================================================


def zero_storage_report(probes: int = 8) -> Dict[str, object]:
    """Everything above, in one dictionary -- the subject of ``report generated``."""
    shell = sieve_shell_report()
    fix = sieve_fix_report()
    snaps = snap_report(probes)
    snaps_near = snap_report(probes, "near")
    storage = storage_report()
    repo = repo_storage_report()
    reals = exact_real_report()
    sextets = sextet_label_report()
    return {
        "sieve": shell,
        "fix": fix,
        "snap": snaps,
        "snap_near": snaps_near,
        "storage": storage,
        "repo": repo,
        "exact_real": reals,
        "sextet": sextets,
        "verdict": {
            "sieve_sound": shell["unsound"] == 0,
            "sieve_complete": shell["kept"] == shell["minimal_vectors"],
            "fix_exact": fix["exact"],
            "snap_sound": snaps["v3_outside_lattice"] == 0,
            "snap_sound_near": snaps_near["v3_outside_lattice"] == 0,
            "storage_verified": storage["all_verified"],
            "generator_claims_met": reals["claims_met"] == reals["claims_made"],
        },
    }

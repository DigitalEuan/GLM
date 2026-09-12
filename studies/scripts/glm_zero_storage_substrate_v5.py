#!/usr/bin/env python3
"""
The GLM Zero-Storage Substrate — v5 (generated, checked, and taxed)
===================================================================

One rule, applied to the whole substrate:

    *Generate what is a consequence; store only what is primary; check every
    generator against the thing it replaces; and record what the generation
    cost.*

This is the standalone successor of ``glm_zero_storage_substrate_v4.py`` (kept
at the repository root, unchanged, so the two can be run side by side).  v4
removed the stored tables from every mechanism but one and proved the
mechanisms it kept; v5 closes that last corner, and adds a ledger so that
"generate, don't store" is a measured trade rather than a slogan.

What is new in v5
-----------------

1. **Syndrome membership — the last table is gone.**  v4's ``is_leech`` still
   consulted a 4096-entry set of codewords (about 12 KB held in memory).  The
   extended binary Golay code is *self-dual*, so its 12 generator rows are
   also a parity-check matrix: a 24-bit word is a codeword exactly when the 12
   parities ``popcount(word & row_j) mod 2`` all vanish.  Membership is
   therefore 12 word operations against 36 bytes of generator, and when the
   word is *not* a codeword the same 12 operations hand back the 12-bit
   **syndrome** rather than a bare ``False`` — which is the language the Lean
   decoder machinery (``GLM.Golay.Census``, ``GLM.Cube.Tax``) is already
   phrased in.  ``GLM.ZeroStorageV5.syndromeZero_iff_isGolay`` proves the
   equivalence ``syndrome c = 0 ↔ c ∈ G₂₄`` for the generator rows the Lean
   development uses; :func:`check_syndrome_against_lookup` checks the same
   statement here, against the old lookup, on the whole 196,560-vector shell
   and on the entire 2²⁴-word space (by an exact null-space computation)
   *before* anything is removed.

2. **A cost ledger — the tax on every generated answer.**  Every operation
   returns, beside its value, an exact integer count of what it spent:
   parity checks, popcounts, coordinate passes, coset trials, ±4 repairs,
   Gray-code steps, integer square roots, series terms, Δ-Σ ticks.  The counts
   are integers, never wall-clock, so a second run reproduces them
   byte-for-byte.  The storage audit becomes an honest comparison: bytes
   stored, against bytes of generator *plus the tax to recover one item*.

3. **NRCI, defined here rather than imported.**  The older material uses
   "NRCI" with more than one formula behind it.  In this file it has exactly
   one definition (:func:`nrci`): for a residual sequence ``r`` measured
   against a reference sequence ``x``,

       ``NRCI(r ; x) = 1 − √( Σ rᵢ² / Σ xᵢ² )``

   reported as an exact dyadic **enclosure** ``[lo, hi]`` of width ``≤ 2⁻ᵏ``
   computed with integer square roots (no float, and reproducible), together
   with the exact rational squared form ``1 − Σrᵢ²/Σxᵢ²``.  It is reported for
   three streams v5 already emits, each with the sequence it is measured on
   named: the Δ-Σ running-average residual, the residual of a decode, and the
   per-level residuals of the dyadic tower.  Where a bound is *proved* — the
   Δ-Σ read-out bound ``< 1/N`` — the NRCI figure and the bound are printed
   side by side.

4. **Continuous retargeting.**  ``DeltaSigmaRegister.retarget(t)`` no longer
   has to zero the accumulator.  Because the accumulator stays in ``[0,1)``
   whatever the target does, the count identity ``|Σb − Σt| < 1`` survives a
   moving target, so a window of ``N`` ticks satisfies
   ``|average − mean target| < 1/N`` — and against a *final* target the error
   picks up exactly the mean deviation of the target over the window.  Both
   statements are proved in ``RequestProject/GLM/ZeroStorageV5.lean``
   (``ds_track_bound``, ``ds_track_moving_target``).

5. **Higher-order noise shaping, measured rather than assumed.**  Second- and
   third-order error-feedback modulators are implemented in exact rationals.
   The faster error decay promised in the literature is *measured* on a stated
   target set and reported as measured; the accumulator excursions are
   measured too, because 1-bit high-order loops can run away.  The
   second-order invariant that the measurement suggests is stated and proved
   in Lean (``ds2_state_bound``); the third-order loop is reported with its
   observed excursion and no claim.

6. **Demand-driven precision.**  ``ExactReal`` gains composition (sum,
   product, difference, reciprocal-free scaling) with the requested precision
   propagated *backwards* through the expression, in the spirit of iRRAM and
   AERN: each sub-process is asked for the least precision that still
   guarantees the top-level ``2⁻ᵏ``.  The ledger shows what that saves against
   asking every leaf for the same precision.

7. **A pruned coset search, and an optional cache with a digest.**  The exact
   decoder keeps its guarantee (nearest point of Λ₂₄, always) and gains a
   running-bound prune that skips most cosets while storing nothing.  A cached
   path — the 4096 codewords held in memory — is available for comparison and
   carries an input digest and a regenerate-and-compare check; the ledger
   reports *both* paths so the trade is visible rather than assumed.

Everything is exact: ``int`` and ``Fraction`` only.  No float in any
computation (floats appear only in printed decimal previews), no RNG — the
probe points come from a documented integer recurrence — and no stored table
anywhere unless explicitly asked for.

Usage
-----

    python3 glm_zero_storage_substrate_v5.py --test        # self-verification
    python3 glm_zero_storage_substrate_v5.py --test --full # + the 2²⁴ sweep
    python3 glm_zero_storage_substrate_v5.py --report      # JSON report
    python3 glm_zero_storage_substrate_v5.py --demo        # worked examples
    python3 glm_zero_storage_substrate_v5.py --ledger      # the cost ledger

Original author of the v3 draft: Euan R. A. Craig (DigitalEuan).
v4: refined, corrected and self-contained.  v5: untabled, taxed and measured.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from fractions import Fraction
from itertools import combinations
from typing import (Callable, Dict, Iterable, Iterator, List, Optional,
                    Sequence, Tuple)

# ===========================================================================
# Constants of the substrate (all of them consequences, none of them data)
# ===========================================================================

DIM = 24                    #: coordinates of the ambient space
GOLAY_WORDS = 4096          #: |G₂₄|
GOLAY_OCTADS = 759          #: weight-8 codewords
GOLAY_ROWS = 12             #: rows of the generator = rows of the check matrix
KISSING = 196560            #: minimal vectors of Λ₂₄
MIN_NORM2 = 32              #: minimal norm², integral (×√8) scaling
COVERING_RADIUS2 = 16       #: squared covering radius in the same scaling
TETRADS = 10626             #: C(24,4)
SEXTETS = 1771              #: TETRADS / 6


# ===========================================================================
# 0.  THE COST LEDGER
# ===========================================================================
#
# Every quantity here is an exact integer count of a primitive operation.  No
# wall-clock time is recorded anywhere in this file: a second run of the same
# call reproduces the same ledger exactly, which is what makes the storage
# audit a comparison rather than an anecdote.


#: The primitive operations the ledger counts, and what one unit means.
LEDGER_ITEMS: Dict[str, str] = {
    "parity_check": "one AND of a 24-bit word with a check row, "
                    "one popcount and one parity",
    "popcount": "one population count of a word (outside a parity check)",
    "word_xor": "one XOR of two 24-bit words (a Gray-code step of the code)",
    "coordinate_pass": "one visit to one coordinate of a 24-vector",
    "coset_trial": "one (parity, codeword) coset evaluated by the decoder",
    "coset_pruned": "one coset abandoned by the running bound",
    "pm4_repair": "one ±4 repair applied to satisfy the mod-8 sum condition",
    "table_lookup": "one hash lookup into a stored table (the cached path)",
    "int_sqrt": "one exact integer square root",
    "series_term": "one term of a series in an ExactReal generator",
    "big_div": "one big-integer division in an ExactReal generator",
    "tick": "one Δ-Σ clock tick (one emitted bit)",
    "rational_op": "one exact rational add/compare in a modulator",
}


class Ledger:
    """An exact integer count of the work an answer cost.

    A ledger is a plain multiset of the items of :data:`LEDGER_ITEMS`.  It is
    passed into the routines that do work; each routine posts the exact count
    it incurred (typically once, at the end of a loop whose trip count it
    knows), so the ledger never depends on how the loop was written.
    """

    __slots__ = ("counts", "name")

    def __init__(self, name: str = "ledger") -> None:
        self.name = name
        self.counts: Dict[str, int] = {}

    def spend(self, item: str, amount: int = 1) -> None:
        if item not in LEDGER_ITEMS:
            raise KeyError(f"unknown ledger item: {item}")
        if amount < 0:
            raise ValueError("a cost is never negative")
        if amount:
            self.counts[item] = self.counts.get(item, 0) + amount

    def merge(self, other: "Ledger") -> None:
        for item, amount in other.counts.items():
            self.counts[item] = self.counts.get(item, 0) + amount

    @property
    def total(self) -> int:
        """The total number of primitive operations charged."""
        return sum(self.counts.values())

    def get(self, item: str) -> int:
        return self.counts.get(item, 0)

    def as_dict(self) -> Dict[str, int]:
        return {k: self.counts[k] for k in sorted(self.counts)}

    def scaled(self, divisor: int) -> Dict[str, Fraction]:
        """The per-item cost of *one* of ``divisor`` items, exactly."""
        if divisor <= 0:
            raise ValueError("divisor must be positive")
        return {k: Fraction(v, divisor) for k, v in self.as_dict().items()}

    def __repr__(self) -> str:
        body = ", ".join(f"{k}={v}" for k, v in self.as_dict().items())
        return f"Ledger({self.name}: {body or 'empty'})"


def popcount(x: int) -> int:
    return x.bit_count()


# ===========================================================================
# 1.  THE GOLAY CODE, GENERATED FROM ARITHMETIC, CHECKED BY SYNDROME
# ===========================================================================
#
# Nothing is stored.  The 12 generator rows come from the quadratic residues
# mod 11 (the Paley/QR construction of the extended binary Golay code).  The
# code is self-dual, so those same 12 rows are a parity-check matrix, and
# membership is decided without ever forming the 4096 codewords.


def quadratic_residues(p: int) -> frozenset:
    """The nonzero quadratic residues mod ``p``."""
    return frozenset((i * i) % p for i in range(1, p))


def golay_generator_rows() -> Tuple[int, ...]:
    """The 12 generator rows of G₂₄, as 24-bit ints: ``[I₁₂ | B]``.

    ``B`` is the 12×12 Paley matrix on the index set ``{∞, 0, …, 10}``:
    ``B[∞][∞] = 0``, the ``∞`` row and column are all ones off that corner,
    and ``B[i][j] = 1`` when ``j − i`` is a nonzero quadratic residue mod 11,
    with ones on the diagonal.  36 bytes of generator for 12,288 bytes of code
    — and, because the code is self-dual, 36 bytes of *parity check* too.
    """
    qr = quadratic_residues(11)
    rows: List[int] = []
    for a in range(12):
        word = 1 << a                      # the identity half
        for b in range(12):
            if a == 0 or b == 0:           # index 0 plays the role of ∞
                bit = 0 if (a == 0 and b == 0) else 1
            else:
                d = (b - a) % 11
                bit = 1 if (d == 0 or d in qr) else 0
            if bit:
                word |= 1 << (12 + b)
        rows.append(word)
    return tuple(rows)


#: The generator rows the Lean development uses (`GLM.LatticeShortcut.golayRows`).
#: A different, permutation-equivalent copy of the same code — carried here so
#: that the syndrome route can be checked against *both* generators, and so
#: that ``GLM.ZeroStorageV5.syndromeZero_iff_isGolay`` and this file are
#: demonstrably talking about the same 12 rows.
LEAN_GOLAY_ROWS: Tuple[int, ...] = (
    16769025, 4681730, 10727428, 13750280, 6877200, 11825184,
    14299200, 15536256, 7770368, 3887616, 1946624, 9361408)


def syndrome(mask: int, rows: Sequence[int],
             ledger: Optional[Ledger] = None) -> int:
    """The 12-bit syndrome of a 24-bit word against the check rows.

    Bit ``j`` of the result is ``popcount(mask & rows[j]) mod 2``.  The word is
    a codeword exactly when the result is ``0`` (:func:`is_codeword`); when it
    is not, the value is the syndrome of its coset, which is what a decoder
    needs and what a bare ``False`` throws away.  Cost: ``len(rows)`` parity
    checks, always — no lookup, no allocation, 36 bytes of generator.
    """
    s = 0
    for j, row in enumerate(rows):
        if (mask & row).bit_count() & 1:
            s |= 1 << j
    if ledger is not None:
        ledger.spend("parity_check", len(rows))
    return s


def is_codeword(mask: int, rows: Sequence[int],
                ledger: Optional[Ledger] = None) -> bool:
    """``mask ∈ G₂₄``, decided by 12 parity checks against 36 bytes."""
    return syndrome(mask, rows, ledger) == 0


def gray_codewords(rows: Sequence[int],
                   ledger: Optional[Ledger] = None) -> Iterator[int]:
    """Stream all ``2^len(rows)`` codewords, one XOR apiece, O(1) memory.

    The Gray-code walk visits every 𝔽₂-combination of the rows changing one
    row at a time, so the whole code is produced from the 36 bytes of
    generator without ever holding a list of it.
    """
    n = len(rows)
    word = 0
    yield word
    for i in range(1, 1 << n):
        j = (i & -i).bit_length() - 1      # the row that changes
        word ^= rows[j]
        yield word
    if ledger is not None:
        ledger.spend("word_xor", (1 << n) - 1)


def code_rank(rows: Sequence[int]) -> int:
    """The 𝔽₂ rank of the rows, by elimination (no table)."""
    pivots: List[int] = []
    for row in rows:
        cur = row
        for p in pivots:
            cur = min(cur, cur ^ p)
        if cur:
            pivots.append(cur)
            pivots.sort(reverse=True)
    return len(pivots)


def is_self_dual_generator(rows: Sequence[int]) -> bool:
    """Every pair of rows is orthogonal — so the generator checks the code."""
    return all(((a & b).bit_count() & 1) == 0 for a in rows for b in rows)


def syndrome_kernel(rows: Sequence[int]) -> Tuple[int, ...]:
    """Every 24-bit word of zero syndrome, by exact null-space elimination.

    This is the *whole* of `{w < 2²⁴ : syndrome(w) = 0}`, computed without
    sweeping 16,777,216 words: the check map is linear, so its kernel is the
    span of a null-space basis, and the span of 12 basis vectors is 4096
    words.  Used only by the verification, to establish set equality with the
    code rather than sampling it.
    """
    # Reduced row echelon form of the check matrix (rows are the check rows,
    # bit i of a row is its entry in column i).
    mat = list(rows)
    pivot_cols: List[int] = []
    r = 0
    for col in range(DIM):
        piv = None
        for i in range(r, len(mat)):
            if (mat[i] >> col) & 1:
                piv = i
                break
        if piv is None:
            continue
        mat[r], mat[piv] = mat[piv], mat[r]
        for i in range(len(mat)):
            if i != r and ((mat[i] >> col) & 1):
                mat[i] ^= mat[r]
        pivot_cols.append(col)
        r += 1
    free = [c for c in range(DIM) if c not in pivot_cols]
    # One kernel basis vector per free column, read off the reduced form.
    basis: List[int] = []
    for f in free:
        w = 1 << f
        for ri, col in enumerate(pivot_cols):
            if (mat[ri] >> f) & 1:
                w |= 1 << col
        basis.append(w)
    return tuple(gray_codewords(basis))


class GolayCode:
    """The extended binary Golay code G₂₄, as 12 rows and nothing else.

    The object holds its 12 generator rows (36 bytes) and, unless a cache is
    explicitly requested, *nothing else*: membership is by syndrome, the code
    is streamed by Gray code, the octads are streamed from the code.  The
    optional cache exists so that the ledger can price the stored path against
    the generated one.
    """

    def __init__(self, rows: Optional[Sequence[int]] = None,
                 cache: bool = False) -> None:
        self.rows: Tuple[int, ...] = (tuple(rows) if rows is not None
                                      else golay_generator_rows())
        self._cache: Optional[frozenset] = None
        self._cache_digest: Optional[str] = None
        if cache:
            self.enable_cache()

    # -- membership --------------------------------------------------------

    def syndrome(self, mask: int, ledger: Optional[Ledger] = None) -> int:
        return syndrome(mask, self.rows, ledger)

    def is_codeword(self, mask: int, ledger: Optional[Ledger] = None) -> bool:
        return self.syndrome(mask, ledger) == 0

    def is_codeword_cached(self, mask: int,
                           ledger: Optional[Ledger] = None) -> bool:
        """The stored path, for comparison: one hash lookup into 12,288 bytes."""
        if self._cache is None:
            self.enable_cache()
        assert self._cache is not None
        if ledger is not None:
            ledger.spend("table_lookup")
        return mask in self._cache

    # -- the optional cache, with the digest-and-regenerate discipline -----

    def enable_cache(self, ledger: Optional[Ledger] = None) -> str:
        """Materialise the 4096 codewords, and record their digest.

        The cache is *derived*: its digest is over the generator rows that
        produced it and over the words themselves, so a later run can check
        that the cache it found is the cache those rows generate.
        """
        words = tuple(sorted(gray_codewords(self.rows, ledger)))
        self._cache = frozenset(words)
        self._cache_digest = self.digest_of(words)
        return self._cache_digest

    @property
    def cache_digest(self) -> Optional[str]:
        return self._cache_digest

    @property
    def cached_bytes(self) -> int:
        """The bytes a materialised cache holds (3 per 24-bit word)."""
        return 0 if self._cache is None else 3 * len(self._cache)

    @staticmethod
    def digest_of(words: Sequence[int]) -> str:
        h = hashlib.sha256()
        for w in words:
            h.update(w.to_bytes(3, "big"))
        return h.hexdigest()

    def cache_is_what_the_rows_generate(self) -> bool:
        """Regenerate from the rows and compare with the cache, digest first."""
        if self._cache is None:
            return True
        words = tuple(sorted(gray_codewords(self.rows)))
        return (self.digest_of(words) == self._cache_digest
                and frozenset(words) == self._cache)

    # -- streams -----------------------------------------------------------

    def words(self, ledger: Optional[Ledger] = None) -> Iterator[int]:
        return gray_codewords(self.rows, ledger)

    def octads(self, ledger: Optional[Ledger] = None) -> Iterator[int]:
        for w in self.words(ledger):
            if w.bit_count() == 8:
                yield w

    def octads_of_tetrad(self, tetrad: int,
                         ledger: Optional[Ledger] = None) -> Tuple[int, ...]:
        """Every octad containing the given weight-4 mask (there are 5).

        Streamed, not tabulated: one pass over the code per query.
        """
        return tuple(sorted(o for o in self.octads(ledger)
                            if o & tetrad == tetrad))

    # -- invariants --------------------------------------------------------

    def weight_distribution(self, ledger: Optional[Ledger] = None
                            ) -> Dict[int, int]:
        counter: Counter = Counter()
        for w in self.words(ledger):
            counter[w.bit_count()] += 1
        if ledger is not None:
            ledger.spend("popcount", GOLAY_WORDS)
        return dict(sorted(counter.items()))

    def invariants(self, ledger: Optional[Ledger] = None) -> Dict[str, object]:
        weights = self.weight_distribution(ledger)
        return {
            "generator_rows": len(self.rows),
            "generator_bytes": 3 * len(self.rows),
            "codewords": sum(weights.values()),
            "weight_distribution": weights,
            "octads": weights.get(8, 0),
            "minimum_distance": min(w for w in weights if w),
            "rank": code_rank(self.rows),
            "self_dual_generator": is_self_dual_generator(self.rows),
            "all_ones_syndrome_zero": self.is_codeword((1 << DIM) - 1),
            "held_bytes": 3 * len(self.rows) + self.cached_bytes,
        }

    def invariants_hold(self, ledger: Optional[Ledger] = None) -> bool:
        inv = self.invariants(ledger)
        return (inv["codewords"] == GOLAY_WORDS
                and inv["weight_distribution"] == {0: 1, 8: 759, 12: 2576,
                                                   16: 759, 24: 1}
                and inv["octads"] == GOLAY_OCTADS
                and inv["minimum_distance"] == 8
                and inv["rank"] == GOLAY_ROWS
                and bool(inv["self_dual_generator"])
                and bool(inv["all_ones_syndrome_zero"]))


def check_syndrome_against_lookup(code: GolayCode, full: bool = False
                                  ) -> Dict[str, object]:
    """The check the removal of the lookup table is conditional on.

    Three comparisons, all exact:

    * **the code itself** — every one of the 4096 words the generator produces
      has syndrome 0, and the syndromes of the 12 rows vanish pairwise;
    * **the whole 2²⁴-word space** — the set of words of zero syndrome is
      computed exactly, as the null space of the check matrix, and compared
      with the code as a set.  (With ``full=True`` the 16,777,216 words are
      additionally swept one by one, which takes a few minutes and proves
      nothing the null space does not; it is offered because it is the check
      a sceptic asks for.)
    * **the shell** — every one of the 196,560 minimal vectors of Λ₂₄ is
      accepted by the syndrome route exactly when it is accepted by the v4
      lookup route, together with a deterministic set of non-members.
    """
    ledger = Ledger("syndrome-check")
    words = tuple(sorted(gray_codewords(code.rows, ledger)))
    lookup = frozenset(words)
    code_ok = all(syndrome(w, code.rows, ledger) == 0 for w in words)

    kernel = syndrome_kernel(code.rows)
    kernel_set = frozenset(kernel)
    kernel_ok = (len(kernel_set) == GOLAY_WORDS and kernel_set == lookup)

    swept: Optional[int] = None
    swept_ok: Optional[bool] = None
    if full:
        rows = code.rows
        hits = 0
        bad = 0
        for w in range(1 << DIM):
            s = 0
            for row in rows:
                if (w & row).bit_count() & 1:
                    s = 1
                    break
            if s == 0:
                hits += 1
                if w not in lookup:
                    bad += 1
            elif w in lookup:
                bad += 1
        ledger.spend("parity_check", (1 << DIM) * len(rows))
        swept = hits
        swept_ok = (hits == GOLAY_WORDS and bad == 0)

    # the shell: the two membership routes, vector by vector
    agree = 0
    disagree = 0
    for vec in minimal_vectors(code):
        m = vec[0] % 2
        mask = leech_mask(vec, m)
        if is_codeword(mask, code.rows, ledger) == (mask in lookup):
            agree += 1
        else:
            disagree += 1
    # and on words that are *not* codewords: the shifted masks
    non_members = 0
    non_agree = 0
    for w in words[:512]:
        for bitpos in (0, 5, 23):
            probe = w ^ (1 << bitpos)
            non_members += 1
            if is_codeword(probe, code.rows, ledger) == (probe in lookup):
                non_agree += 1

    return {
        "codewords_checked": len(words),
        "all_codewords_have_zero_syndrome": code_ok,
        "kernel_size": len(kernel_set),
        "kernel_equals_code": kernel_ok,
        "swept_2_24": swept,
        "sweep_agrees": swept_ok,
        "shell_vectors_compared": agree + disagree,
        "shell_routes_agree": disagree == 0 and agree == KISSING,
        "non_codewords_compared": non_members,
        "non_codeword_routes_agree": non_agree == non_members,
        "ledger": ledger.as_dict(),
        "verified": bool(code_ok and kernel_ok and disagree == 0
                         and agree == KISSING and non_agree == non_members
                         and (swept_ok is None or swept_ok)),
    }


# ===========================================================================
# 2.  THE LEECH LATTICE, AS THREE CONGRUENCES AND TWELVE PARITIES
# ===========================================================================
#
# Membership in Λ₂₄ (integral ×√8 scaling, minimal norm 32):
#
#   m  = x₀ mod 2                       (the parity of the whole vector)
#   1) x_i ≡ m (mod 2) for every i
#   2) { i : x_i ≡ m (mod 4) } has zero Golay syndrome
#   3) Σ x_i ≡ 4m (mod 8)
#
# This is the exact image of GLM.LatticeShortcut.IsLeech; the deterministic
# form (m read off coordinate 0) is proved equivalent to it in
# GLM.ZeroStorage.refinedSieve_iff_isLeech, and clause 2's syndrome form is
# proved equivalent to codeword membership in
# GLM.ZeroStorageV5.syndromeZero_iff_isGolay.


def leech_mask(vec: Sequence[int], m: int) -> int:
    """The mod-4 Golay word of ``vec``: the coordinates congruent to ``m``."""
    return sum(1 << i for i, v in enumerate(vec) if (v - m) % 4 == 0)


def leech_syndrome(vec: Sequence[int], rows: Sequence[int],
                   ledger: Optional[Ledger] = None) -> Optional[int]:
    """The Golay syndrome of ``vec``'s mod-4 word, or ``None`` if the parity
    or the mod-8 sum condition already fails.

    A membership test that returns *why*: ``0`` means the vector is in Λ₂₄,
    a nonzero value is the coset of the mod-4 word, and ``None`` means the
    vector fails a condition the syndrome cannot express.
    """
    if len(vec) != DIM:
        return None
    m = vec[0] % 2
    if ledger is not None:
        ledger.spend("coordinate_pass", DIM)
    if any((v - m) % 2 for v in vec):
        return None
    if (sum(vec) - 4 * m) % 8:
        return None
    return syndrome(leech_mask(vec, m), rows, ledger)


def is_leech(vec: Sequence[int], code: Optional[GolayCode] = None,
             rows: Optional[Sequence[int]] = None,
             ledger: Optional[Ledger] = None) -> bool:
    """Decide ``vec ∈ Λ₂₄``: one pass over 24 coordinates, 12 parity checks."""
    if rows is None:
        rows = code.rows if code is not None else golay_generator_rows()
    return leech_syndrome(vec, rows, ledger) == 0


def norm2(vec: Sequence[int]) -> int:
    return sum(v * v for v in vec)


def minimal_vectors(code: GolayCode,
                    ledger: Optional[Ledger] = None
                    ) -> Iterator[Tuple[int, ...]]:
    """Stream the 196,560 minimal vectors of Λ₂₄ — generated, not stored.

    Three shapes, each a consequence of the code:

    * ``(±4², 0²²)``            — 4·C(24,2) = 1,104
    * ``(±2⁸, 0¹⁶)`` on octads, an even number of minus signs — 759·2⁷ = 97,152
    * ``(∓3, ±1²³)``            — 4096·24 = 98,304

    The generator never holds more than one vector at a time; the whole shell
    costs the 12 generator rows plus this function.
    """
    for i, j in combinations(range(DIM), 2):
        for si in (4, -4):
            for sj in (4, -4):
                vec = [0] * DIM
                vec[i], vec[j] = si, sj
                yield tuple(vec)
    for word in code.words(ledger):
        w = word.bit_count()
        if w == 8:
            points = [i for i in range(DIM) if (word >> i) & 1]
            for pattern in range(1 << 8):
                if pattern.bit_count() % 2:
                    continue
                vec = [0] * DIM
                for k, p in enumerate(points):
                    vec[p] = -2 if (pattern >> k) & 1 else 2
                yield tuple(vec)
    for word in code.words(ledger):
        base = [1 if (word >> i) & 1 else -1 for i in range(DIM)]
        for j in range(DIM):
            vec = list(base)
            vec[j] = -3 if base[j] == 1 else 3
            yield tuple(vec)
    if ledger is not None:
        ledger.spend("coordinate_pass", KISSING * DIM)


# ===========================================================================
# 3.  THE EXACT NEAREST-POINT DECODER, PRUNED AND PRICED
# ===========================================================================


def _round_half_up(num: int, den: int) -> int:
    """``⌊num/den + 1/2⌋`` for ``den > 0``, in integers."""
    return (2 * num + den) // (2 * den)


def _common_denominator(target: Sequence[Fraction]) -> Tuple[int, List[int]]:
    den = 1
    for t in target:
        den = den * t.denominator // math.gcd(den, t.denominator)
    return den, [int(t * den) for t in target]


class LeechDecoder:
    """Exact nearest-point decoding in Λ₂₄, with a running bound and a ledger.

    A Construction-C coset is fixed by a parity ``p ∈ {0,1}`` and a codeword
    ``c``: coordinate ``i`` is confined to the residue class ``p`` mod 4 when
    ``i ∈ c`` and ``p+2`` mod 4 otherwise.  Inside a coset the coordinates are
    independent, and the single coupling — ``Σx ≡ 4p (mod 8)`` — is repaired
    by moving exactly one coordinate by ``±4``; choosing the cheapest such
    move gives the nearest point of the coset exactly, and the 8,192 cosets
    exhaust the lattice.  Every step of that argument is proved in
    ``RequestProject/GLM/ZeroStorageV5.lean``: ``coset_min_cost`` (no point of
    the coset is closer), ``coset_min_attained`` (a point of it achieves the
    bound), ``leech_in_coset`` (the cosets exhaust Λ₂₄) and
    ``lattice_dist_ge`` (so the minimum over cosets is the minimum over the
    lattice).

    Two things are new in v5:

    * the coset search is **pruned** by a running bound (coordinates are
      visited in decreasing order of how much the choice costs, and a coset is
      abandoned as soon as its partial cost plus the cheapest possible
      completion reaches the best cost so far) — this stores nothing and
      typically skips most of the search;
    * every answer carries an exact **ledger**: cosets evaluated, cosets
      pruned, coordinate visits, ±4 repairs, Gray-code steps.

    All arithmetic is integer: the target is carried over a common denominator.
    """

    def __init__(self, code: GolayCode) -> None:
        self.code = code

    # -- the per-coordinate tables ----------------------------------------

    def _tables(self, num: Sequence[int], den: int, ledger: Optional[Ledger]
                ) -> Tuple[List[List[int]], List[List[int]], List[List[int]]]:
        value = [[0] * 4 for _ in range(DIM)]
        cost = [[0] * 4 for _ in range(DIM)]
        repair = [[0] * 4 for _ in range(DIM)]
        for i in range(DIM):
            for r in range(4):
                k = _round_half_up(num[i] - r * den, 4 * den)
                v = 4 * k + r
                base = (v * den - num[i]) ** 2
                value[i][r] = v
                cost[i][r] = base
                repair[i][r] = min(((v + 4) * den - num[i]) ** 2,
                                   ((v - 4) * den - num[i]) ** 2) - base
        if ledger is not None:
            ledger.spend("coordinate_pass", 4 * DIM)
        return value, cost, repair

    def _encode(self, message: int) -> int:
        word = 0
        for j, row in enumerate(self.code.rows):
            if (message >> j) & 1:
                word ^= row
        return word

    def nearest(self, target: Sequence[Fraction],
                ledger: Optional[Ledger] = None,
                prune: bool = True) -> Dict[str, object]:
        """The nearest point of Λ₂₄ to ``target``, with its cost ledger."""
        if len(target) != DIM:
            raise ValueError("target must have 24 coordinates")
        local = Ledger("decode")
        den, num = _common_denominator(target)
        value, cost, repair = self._tables(num, den, local)

        best_cost: Optional[int] = None
        best_point: Optional[Tuple[int, ...]] = None
        evaluated = 0
        pruned = 0
        repairs = 0
        visits = 0
        gray_steps = 0

        for parity in (0, 1):
            r_in, r_out = parity % 4, (parity + 2) % 4
            order = sorted(range(DIM),
                           key=lambda i: -abs(cost[i][r_in] - cost[i][r_out]))
            suffix = [0] * (DIM + 1)
            for t in range(DIM - 1, -1, -1):
                i = order[t]
                suffix[t] = suffix[t + 1] + min(cost[i][r_in], cost[i][r_out])

            def evaluate(word: int, bound: Optional[int]
                         ) -> Optional[Tuple[int, Tuple[int, ...], bool]]:
                """Cost of the coset ``(parity, word)``; ``None`` if pruned."""
                nonlocal visits
                total = 0
                ssum = 0
                cheapest: Optional[Tuple[int, int, int]] = None
                for t, i in enumerate(order):
                    r = r_in if (word >> i) & 1 else r_out
                    total += cost[i][r]
                    visits += 1
                    if (prune and bound is not None
                            and total + suffix[t + 1] >= bound):
                        return None
                    ssum += value[i][r]
                    pen = repair[i][r]
                    if cheapest is None or pen < cheapest[0]:
                        cheapest = (pen, i, r)
                assert cheapest is not None
                needs = bool((ssum - 4 * parity) % 8)
                point = [value[i][r_in if (word >> i) & 1 else r_out]
                         for i in range(DIM)]
                if needs:
                    total += cheapest[0]
                    _, i, _r = cheapest
                    v = point[i]
                    up = (v + 4) * den - num[i]
                    down = (v - 4) * den - num[i]
                    point[i] = v + 4 if up * up <= down * down else v - 4
                return total, tuple(point), needs

            # A seed: the codeword that agrees with the cheaper residue choice
            # on the twelve information positions.  Costs one encoding and
            # gives the running bound something to work with immediately.
            preferred = sum(1 << i for i in range(DIM)
                            if cost[i][r_in] <= cost[i][r_out])
            seed = self._encode(preferred & 0xFFF)
            got = evaluate(seed, None)
            if got is not None:
                total, point, needs = got
                evaluated += 1
                repairs += int(needs)
                if best_cost is None or total < best_cost:
                    best_cost, best_point = total, point

            for word in gray_codewords(self.code.rows):
                gray_steps += 1
                got = evaluate(word, best_cost)
                if got is None:
                    pruned += 1
                    continue
                evaluated += 1
                total, point, needs = got
                repairs += int(needs)
                if best_cost is None or total < best_cost:
                    best_cost, best_point = total, point

        assert best_point is not None and best_cost is not None
        local.spend("coset_trial", evaluated)
        local.spend("coset_pruned", pruned)
        local.spend("coordinate_pass", visits)
        local.spend("pm4_repair", repairs)
        local.spend("word_xor", gray_steps)
        dist2 = Fraction(best_cost, den * den)
        member_ledger = Ledger("membership")
        inside = is_leech(best_point, self.code, ledger=member_ledger)
        local.merge(member_ledger)
        if ledger is not None:
            ledger.merge(local)
        return {
            "point": best_point,
            "dist2": dist2,
            "in_lattice": inside,
            "within_covering_radius": dist2 <= COVERING_RADIUS2,
            "norm2": norm2(best_point),
            "cosets_evaluated": evaluated,
            "cosets_pruned": pruned,
            "repairs_applied": repairs,
            "ledger": local.as_dict(),
            "ledger_total": local.total,
        }

    def locally_optimal(self, target: Sequence[Fraction],
                        point: Sequence[int],
                        ledger: Optional[Ledger] = None) -> bool:
        """No neighbour ``point + v``, ``v`` a minimal vector, is closer.

        An independent check on the decoder: a strictly nearer lattice point
        would have to show up here.  Integer arithmetic throughout.
        """
        den, num = _common_denominator(target)
        base = sum((point[i] * den - num[i]) ** 2 for i in range(DIM))
        for v in minimal_vectors(self.code, ledger):
            here = sum(((point[i] + v[i]) * den - num[i]) ** 2
                       for i in range(DIM))
            if here < base:
                return False
        return True


def probe_targets(count: int = 8, seed: int = 20260908,
                  denominator: int = 4) -> List[Tuple[Fraction, ...]]:
    """Deterministic rational probe points from an integer recurrence.

    No RNG is imported: the state is the classical multiplicative recurrence
    over the 32-bit ring, and only its integer high bits are used, so every
    coordinate is an exact ``Fraction`` and every run produces the same list.
    """
    state = seed % (2 ** 32)
    out: List[Tuple[Fraction, ...]] = []
    for _ in range(count):
        coords: List[Fraction] = []
        for _ in range(DIM):
            state = (1103515245 * state + 12345) % (2 ** 32)
            draw = (state >> 13) % (8 * denominator)
            coords.append(Fraction(draw - 4 * denominator, denominator))
        out.append(tuple(coords))
    return out


def decoder_cost_report(code: GolayCode, probes: int = 4) -> Dict[str, object]:
    """The pruned search against the exhaustive one: same answer, less work."""
    decoder = LeechDecoder(code)
    rows: List[Dict[str, object]] = []
    identical = True
    for idx, target in enumerate(probe_targets(probes)):
        fast = decoder.nearest(target, prune=True)
        slow = decoder.nearest(target, prune=False)
        same = fast["point"] == slow["point"] and fast["dist2"] == slow["dist2"]
        identical &= same
        rows.append({
            "probe": idx,
            "dist2": fast["dist2"],
            "same_point_as_exhaustive": same,
            "pruned_cosets_evaluated": fast["cosets_evaluated"],
            "pruned_cosets_skipped": fast["cosets_pruned"],
            "exhaustive_cosets_evaluated": slow["cosets_evaluated"],
            "pruned_ledger_total": fast["ledger_total"],
            "exhaustive_ledger_total": slow["ledger_total"],
            "work_ratio": Fraction(fast["ledger_total"],
                                   slow["ledger_total"]),
        })
    return {
        "rows": rows,
        "all_agree_with_exhaustive": identical,
        "mean_work_ratio": (sum((r["work_ratio"] for r in rows),
                                Fraction(0)) / len(rows)) if rows else None,
    }


# ===========================================================================
# 4.  THE DYADIC TOWER
# ===========================================================================


class DyadicTower:
    """The layer ladder ``π_n(q) = ⌊q·2ⁿ⌋/2ⁿ`` over ℚ.

    Level ``n`` pins ``q`` to a half-open window of width ``2⁻ⁿ``:
    ``π_n(q) ≤ q < π_n(q) + 2⁻ⁿ`` (Lean: ``dyadic_surrogate_error``).  The
    ladder terminates exactly on the dyadic rationals
    (``dyadic_exact_iff_den_pow_two``) and is genuinely infinite for every
    other rational.  The readings are **non-decreasing**, not strictly
    increasing — at ``q = 1/3`` levels 0 and 1 both read 0 — which is why the
    resolution, not the reading, is the thing that strictly improves
    (``dyadic_value_not_strictMono``).
    """

    @staticmethod
    def surrogate(q: Fraction, n: int) -> Fraction:
        scaled = q * (1 << n) if n >= 0 else q / (1 << -n)
        return Fraction(scaled.numerator // scaled.denominator, 1 << n)

    @staticmethod
    def resolution(n: int) -> Fraction:
        return Fraction(1, 1 << n)

    @staticmethod
    def window(q: Fraction, n: int) -> Tuple[Fraction, Fraction]:
        low = DyadicTower.surrogate(q, n)
        return low, low + DyadicTower.resolution(n)

    @staticmethod
    def is_dyadic(q: Fraction) -> bool:
        d = q.denominator
        return d & (d - 1) == 0

    @staticmethod
    def exact_level(q: Fraction) -> Optional[int]:
        """The level at which the tower reads ``q`` exactly, or ``None``."""
        if not DyadicTower.is_dyadic(q):
            return None
        return q.denominator.bit_length() - 1

    @staticmethod
    def sequence(q: Fraction, levels: int) -> List[Fraction]:
        return [DyadicTower.surrogate(q, n) for n in range(levels + 1)]

    @staticmethod
    def residuals(q: Fraction, levels: int) -> List[Fraction]:
        """``q − π_n(q)`` for ``n = 0 … levels`` — the sequence NRCI is
        measured on."""
        return [q - DyadicTower.surrogate(q, n) for n in range(levels + 1)]

    @staticmethod
    def audit(q: Fraction, levels: int = 12) -> Dict[str, object]:
        seq = DyadicTower.sequence(q, levels)
        return {
            "q": q,
            "levels": levels,
            "window_contains_q": all(
                DyadicTower.window(q, n)[0] <= q < DyadicTower.window(q, n)[1]
                for n in range(levels + 1)),
            "non_decreasing": all(seq[i] <= seq[i + 1]
                                  for i in range(len(seq) - 1)),
            "strictly_increasing": all(seq[i] < seq[i + 1]
                                       for i in range(len(seq) - 1)),
            "resolution_strictly_improves": all(
                DyadicTower.resolution(n + 1) < DyadicTower.resolution(n)
                for n in range(levels)),
            "is_dyadic": DyadicTower.is_dyadic(q),
            "exact_level": DyadicTower.exact_level(q),
        }


# ===========================================================================
# 5.  NRCI — ONE DEFINITION, STATED HERE
# ===========================================================================
#
# The older GLM material uses "NRCI" (non-random coherence index) with more
# than one formula behind it.  In this file it has exactly one:
#
#     NRCI(r ; x) = 1 − √( Σ rᵢ² / Σ xᵢ² )
#
# for a residual sequence r measured against a reference sequence x of the
# same length, with Σxᵢ² > 0.  It is 1 when the residual vanishes, 0 when the
# residual is as large as the reference, and negative when it is larger.
#
# Two exact forms are reported, and neither uses a float:
#
#   * `nrci_squared` — the exact rational 1 − Σrᵢ²/Σxᵢ², which needs no root;
#   * `nrci`         — a dyadic enclosure [lo, hi] of the definition above,
#                      of width ≤ 2⁻ᵏ, from an integer square root.
#
# Every reported NRCI names the stream it was measured on.


def nrci_squared(residual: Sequence[Fraction],
                 reference: Sequence[Fraction]) -> Fraction:
    """The exact rational ``1 − Σr²/Σx²`` (the root-free form)."""
    num = sum((r * r for r in residual), Fraction(0))
    den = sum((x * x for x in reference), Fraction(0))
    if den == 0:
        raise ValueError("the reference sequence must not be identically zero")
    return 1 - num / den


def nrci(residual: Sequence[Fraction], reference: Sequence[Fraction],
         bits: int = 32, ledger: Optional[Ledger] = None
         ) -> Dict[str, object]:
    """``1 − √(Σr²/Σx²)`` as an exact dyadic enclosure of width ``≤ 2⁻ᵇⁱᵗˢ``.

    The root is taken with :func:`math.isqrt`, so the two endpoints are exact
    dyadic rationals that provably bracket the value, and a second run
    reproduces them exactly.
    """
    num = sum((r * r for r in residual), Fraction(0))
    den = sum((x * x for x in reference), Fraction(0))
    if den == 0:
        raise ValueError("the reference sequence must not be identically zero")
    ratio = num / den                        # (RMS residual / RMS reference)²
    p, q = ratio.numerator, ratio.denominator
    s = math.isqrt((p << (2 * bits)) // q)   # s ≤ 2^bits·√ratio < s+1
    if ledger is not None:
        ledger.spend("int_sqrt")
    lo_root = Fraction(s, 1 << bits)
    hi_root = Fraction(s + 1, 1 << bits)
    return {
        "lo": 1 - hi_root,
        "hi": 1 - lo_root,
        "width": Fraction(1, 1 << bits),
        "bits": bits,
        "squared_form": 1 - ratio,
        "ratio_squared": ratio,
        "samples": len(residual),
    }


def nrci_of_delta_sigma(reg: "DeltaSigmaRegister", bits: int = 32
                        ) -> Dict[str, object]:
    """NRCI of a Δ-Σ register, measured on the running-average residual.

    *The stream*: for the bits ``b₁ … b_N`` emitted so far, the residual is
    ``r_N = (1/N)Σ_{n≤N} bₙ − (1/N)Σ_{n≤N} tₙ`` for ``N = 1 … N`` — the
    quantity the proved read-out bound ``|r_N| < 1/N`` governs — and the
    reference is the running mean target ``(1/N)Σ tₙ``.
    """
    residual: List[Fraction] = []
    reference: List[Fraction] = []
    ones = 0
    tsum = Fraction(0)
    for n, (bit, t) in enumerate(zip(reg.stream, reg.targets), start=1):
        ones += bit
        tsum += t
        residual.append(Fraction(ones, n) - tsum / n)
        reference.append(tsum / n)
    out = nrci(residual, reference, bits)
    out["stream"] = "delta-sigma running-average residual"
    out["ticks"] = len(residual)
    out["proved_bound"] = Fraction(1, len(residual)) if residual else None
    out["bound_holds"] = all(abs(r) < Fraction(1, n)
                             for n, r in enumerate(residual, start=1))
    return out


def nrci_of_decode(target: Sequence[Fraction], point: Sequence[int],
                   bits: int = 32) -> Dict[str, object]:
    """NRCI of a decode, measured on the coordinate residual.

    *The stream*: ``rᵢ = pointᵢ − targetᵢ`` for the 24 coordinates, against
    the target coordinates themselves as reference.
    """
    residual = [Fraction(point[i]) - target[i] for i in range(len(point))]
    out = nrci(residual, list(target), bits)
    out["stream"] = "decode coordinate residual"
    return out


def nrci_of_tower(q: Fraction, levels: int = 12, bits: int = 32
                  ) -> Dict[str, object]:
    """NRCI of the dyadic tower, measured on the per-level residuals.

    *The stream*: ``rₙ = q − π_n(q)`` for ``n = 0 … levels``, against the
    constant reference ``q``.
    """
    residual = DyadicTower.residuals(q, levels)
    out = nrci(residual, [q] * len(residual), bits)
    out["stream"] = "dyadic tower per-level residual"
    out["q"] = q
    return out


# ===========================================================================
# 6.  GENERATED REALS: A CONTRACT, A LEDGER, AND DEMAND-DRIVEN PRECISION
# ===========================================================================
#
#     x.at(k)  is a dyadic rational r with |r − x| ≤ 2⁻ᵏ,
#
# and its denominator has k + O(1) bits.  v5 adds two things: every generator
# posts what it spent (series terms, big divisions, integer square roots), and
# generators compose — a sum or a product propagates the requested precision
# *backwards*, asking each sub-process for the least precision that still
# guarantees the top-level bound.


def _round_to_dyadic(value: Fraction, bits: int) -> Fraction:
    """Nearest multiple of ``2⁻ᵇⁱᵗˢ``; the rounding error is ``≤ 2⁻ᵇⁱᵗˢ⁻¹``."""
    scaled = value * (1 << bits)
    n = (2 * scaled.numerator + scaled.denominator) // (2 * scaled.denominator)
    return Fraction(n, 1 << bits)


class ExactReal:
    """A real number held as a precision-parameterised process.

    ``at(k)`` honours the contract; ``at_with_cost(k)`` honours it and hands
    back the exact ledger of what the answer cost.
    """

    def __init__(self, name: str, approx: Callable[..., Fraction],
                 bound: str, magnitude_bits: int = 2) -> None:
        self.name = name
        self._approx = approx
        self.bound = bound              # the tail estimate that justifies at(k)
        self.magnitude_bits = magnitude_bits   # |x| ≤ 2^magnitude_bits

    def at(self, k: int, ledger: Optional[Ledger] = None) -> Fraction:
        """A dyadic rational within ``2⁻ᵏ`` of the number."""
        if k < 0:
            raise ValueError("precision must be non-negative")
        try:
            return self._approx(k, ledger)
        except TypeError:
            return self._approx(k)

    def at_with_cost(self, k: int) -> Tuple[Fraction, Ledger]:
        ledger = Ledger(f"{self.name}.at({k})")
        return self.at(k, ledger), ledger

    def cost(self, k: int) -> Dict[str, object]:
        """The size of the answer, and the work it took."""
        value, ledger = self.at_with_cost(k)
        return {
            "requested_bits": k,
            "denominator_bits": value.denominator.bit_length() - 1,
            "numerator_bits": abs(value.numerator).bit_length(),
            "ledger": ledger.as_dict(),
            "ledger_total": ledger.total,
        }

    # -- composition, with the precision propagated backwards --------------

    def __add__(self, other: "ExactReal") -> "ExactReal":
        return er_add(self, other)

    def __sub__(self, other: "ExactReal") -> "ExactReal":
        return er_sub(self, other)

    def __mul__(self, other: "ExactReal") -> "ExactReal":
        return er_mul(self, other)

    def __repr__(self) -> str:
        return f"ExactReal({self.name})"


def er_add(x: ExactReal, y: ExactReal) -> ExactReal:
    """``x + y``: each operand is asked for ``k+2`` bits, and no more."""

    def approx(k: int, ledger: Optional[Ledger] = None) -> Fraction:
        return _round_to_dyadic(x.at(k + 2, ledger) + y.at(k + 2, ledger), k + 2)

    return ExactReal(f"({x.name} + {y.name})", approx,
                     "two halves at k+2, rounded at k+2: ≤ 2^-k",
                     max(x.magnitude_bits, y.magnitude_bits) + 1)


def er_sub(x: ExactReal, y: ExactReal) -> ExactReal:
    def approx(k: int, ledger: Optional[Ledger] = None) -> Fraction:
        return _round_to_dyadic(x.at(k + 2, ledger) - y.at(k + 2, ledger), k + 2)

    return ExactReal(f"({x.name} − {y.name})", approx,
                     "two halves at k+2, rounded at k+2: ≤ 2^-k",
                     max(x.magnitude_bits, y.magnitude_bits) + 1)


def er_mul(x: ExactReal, y: ExactReal) -> ExactReal:
    """``x·y``: the operand precisions are set by the *other* magnitude.

    With ``|x| ≤ 2^Bx`` and ``|y| ≤ 2^By``, asking ``x`` for ``k + By + 2``
    bits and ``y`` for ``k + Bx + 2`` bits gives
    ``|xy − x'y'| ≤ |x||y−y'| + |y'||x−x'| ≤ 2⁻ᵏ⁻² + 2⁻ᵏ⁻¹``, and rounding the
    product at ``k + 3`` bits keeps the total at ``≤ 2⁻ᵏ``.  This is the
    demand-driven discipline: neither factor is computed to a precision the
    answer cannot use.
    """
    bx, by = x.magnitude_bits, y.magnitude_bits

    def approx(k: int, ledger: Optional[Ledger] = None) -> Fraction:
        a = x.at(k + by + 2, ledger)
        b = y.at(k + bx + 2, ledger)
        return _round_to_dyadic(a * b, k + 3)

    return ExactReal(f"({x.name} · {y.name})", approx,
                     "backward-propagated precisions, product rounded at k+3",
                     bx + by + 1)


def er_rational(q: Fraction, name: str = "rational") -> ExactReal:
    return ExactReal(name, lambda k, ledger=None: q, "exact",
                     max(1, abs(q).__ceil__().bit_length()))


def er_sqrt(a: Fraction) -> ExactReal:
    """``√a`` for ``a ≥ 0`` by integer square root — no iteration to tune.

    ``s = ⌊√(p·2^{2n}/q)⌋`` with ``n = k+2`` gives ``|s/2ⁿ − √a| ≤ 2⁻ᵏ``;
    the work is one exact integer square root, and the answer's denominator is
    exactly ``2ⁿ``.
    """
    if a < 0:
        raise ValueError("sqrt of a negative rational")
    p, q = a.numerator, a.denominator

    def approx(k: int, ledger: Optional[Ledger] = None) -> Fraction:
        n = k + 2
        s = math.isqrt((p << (2 * n)) // q)
        if ledger is not None:
            ledger.spend("int_sqrt")
            ledger.spend("big_div")
        return Fraction(s, 1 << n)

    return ExactReal(f"sqrt({a})", approx,
                     "integer isqrt: |error| ≤ 2^-(k+1)",
                     max(1, (a.__ceil__().bit_length() + 1) // 2 + 1))


def _atan_inv_scaled(d: int, bits: int, ledger: Optional[Ledger] = None) -> int:
    """``⌊2^bits · arctan(1/d)⌉`` by the alternating series, truncation-safe.

    The series is alternating with decreasing terms, so the tail after the
    first vanishing scaled term is below one ulp; each truncated division
    contributes at most one ulp, and the number of terms is below ``bits``.
    Callers add guard bits accordingly.
    """
    total = 0
    power = (1 << bits) // d
    d2 = d * d
    j = 0
    sign = 1
    while power:
        total += sign * (power // (2 * j + 1))
        power //= d2
        j += 1
        sign = -sign
    if ledger is not None:
        ledger.spend("series_term", j)
        ledger.spend("big_div", 2 * j + 1)
    return total


def er_pi() -> ExactReal:
    """π by Machin's formula, ``π = 16·arctan(1/5) − 4·arctan(1/239)``."""

    def approx(k: int, ledger: Optional[Ledger] = None) -> Fraction:
        guard = k + 32 + 2 * (k + 32).bit_length()
        value = Fraction(16 * _atan_inv_scaled(5, guard, ledger)
                         - 4 * _atan_inv_scaled(239, guard, ledger), 1 << guard)
        return _round_to_dyadic(value, k + 1)

    return ExactReal("pi", approx,
                     "Machin, alternating tails + ulp truncation < 2^-(k+1)", 2)


def er_e() -> ExactReal:
    """``e = Σ 1/j!``; after ``n`` terms the tail is below ``2/n!``."""

    def approx(k: int, ledger: Optional[Ledger] = None) -> Fraction:
        guard = k + 16
        n = 2
        fact = 2
        while fact < (1 << (guard + 1)):        # 2/n! < 2^-(guard)
            n += 1
            fact *= n
        scale = 1 << guard
        total = 0
        term = scale
        for j in range(1, n + 1):
            total += term
            term //= j
        total += term                            # the j = n+1 remainder head
        if ledger is not None:
            ledger.spend("series_term", n)
            ledger.spend("big_div", n)
        return _round_to_dyadic(Fraction(total, scale), k + 1)

    return ExactReal("e", approx, "Taylor: tail < 2/n!, n chosen from k", 2)


def er_ln2() -> ExactReal:
    """``ln 2 = 2·artanh(1/3) = Σ 2/((2j+1)·3^{2j+1})``; tail below ``9⁻ⁿ``."""

    def approx(k: int, ledger: Optional[Ledger] = None) -> Fraction:
        guard = k + 16
        scale = 1 << guard
        total = 0
        j = 0
        power = scale // 3
        while power:
            total += 2 * (power // (2 * j + 1))
            power //= 9
            j += 1
        if ledger is not None:
            ledger.spend("series_term", j)
            ledger.spend("big_div", 2 * j + 1)
        return _round_to_dyadic(Fraction(total, scale), k + 1)

    return ExactReal("ln2", approx, "artanh(1/3): tail < 9^-n, plus ulps", 1)


def _bernoulli_even(count: int) -> List[Fraction]:
    """``B₀, B₂, B₄, …`` — exact, by the standard recurrence."""
    bern: List[Fraction] = [Fraction(1)]
    m = 0
    values: Dict[int, Fraction] = {0: Fraction(1)}
    while len(bern) < count + 1:
        m += 1
        total = Fraction(0)
        for j in range(m):
            total += math.comb(m + 1, j) * values.get(j, Fraction(0))
        values[m] = -total / (m + 1)
        if m % 2 == 0:
            bern.append(values[m])
    return bern


def er_gamma() -> ExactReal:
    """Euler–Mascheroni γ by Euler–Maclaurin, with the remainder bounded.

    ``γ = H_n − ln n − 1/(2n) + Σ_{j=1..J} B_{2j}/(2j·n^{2j}) + R_J`` with
    ``|R_J| ≤ |B_{2J+2}| / ((2J+2)·n^{2J+2})``.  ``n`` is a power of two so
    ``ln n = m·ln 2`` comes from the certified ``ln 2`` process; ``J`` is
    increased until the bound is below ``2⁻ᵏ⁻²``.
    """
    ln2 = er_ln2()
    bern = _bernoulli_even(30)

    def approx(k: int, ledger: Optional[Ledger] = None) -> Fraction:
        target = Fraction(1, 1 << (k + 2))
        m = max(5, (k + 15) // 8)
        while True:
            n = 1 << m
            stop = None
            for j in range(1, len(bern) - 1):
                bound = (abs(bern[j + 1])
                         / ((2 * j + 2) * Fraction(n) ** (2 * j + 2)))
                if bound <= target:
                    stop = j
                    break
            if stop is not None:
                break
            m += 1                      # a coarser n cannot reach 2^-k-2
        guard = k + 8 + m
        scale = 1 << guard
        harmonic = Fraction(sum(scale // i for i in range(1, n + 1)), scale)
        value = harmonic - m * ln2.at(k + 8, ledger) - Fraction(1, 2 * n)
        for j in range(1, stop + 1):
            value += bern[j] / (2 * j * Fraction(n) ** (2 * j))
        if ledger is not None:
            ledger.spend("series_term", stop + n)
            ledger.spend("big_div", n)
        return _round_to_dyadic(value, k + 1)

    return ExactReal("gamma", approx,
                     "Euler–Maclaurin: |R_J| ≤ |B_{2J+2}|/((2J+2)n^{2J+2})", 1)


def er_phi() -> ExactReal:
    """The golden ratio ``φ = (1 + √5)/2``."""
    root = er_sqrt(Fraction(5))

    def approx(k: int, ledger: Optional[Ledger] = None) -> Fraction:
        return _round_to_dyadic((1 + root.at(k + 2, ledger)) / 2, k + 1)

    return ExactReal("phi", approx, "from sqrt(5), halved: ≤ 2^-(k+1)", 1)


def exact_real_catalogue() -> Dict[str, ExactReal]:
    return {
        "pi": er_pi(),
        "e": er_e(),
        "sqrt2": er_sqrt(Fraction(2)),
        "phi": er_phi(),
        "ln2": er_ln2(),
        "gamma": er_gamma(),
    }


#: Reference decimals, used **only** by the self-test to measure the
#: generators; nothing in the substrate reads them.
REFERENCES: Dict[str, Fraction] = {
    "pi": Fraction(31415926535897932384626433832795028841971693993751, 10 ** 49),
    "e": Fraction(27182818284590452353602874713526624977572470937000, 10 ** 49),
    "sqrt2": Fraction(14142135623730950488016887242096980785696718753769, 10 ** 49),
    "phi": Fraction(16180339887498948482045868343656381177203091798058, 10 ** 49),
    "ln2": Fraction(6931471805599453094172321214581765680755001343603, 10 ** 49),
    "gamma": Fraction(5772156649015328606065120900824024310421593359399, 10 ** 49),
}
#: The references above are good to ~2⁻¹⁶⁰; the self-test never asks for more.
REFERENCE_BITS = 150


def exact_real_report(levels: Sequence[int] = (8, 32, 96)) -> Dict[str, object]:
    """Ask every generator for ``2⁻ᵏ``, check it delivered, and price it."""
    rows: List[Dict[str, object]] = []
    for name, process in exact_real_catalogue().items():
        reference = REFERENCES[name]
        for k in levels:
            value, ledger = process.at_with_cost(k)
            error = abs(value - reference)
            rows.append({
                "constant": name,
                "requested_bits": k,
                "error": error,
                "meets_contract": error <= Fraction(1, 1 << k),
                "denominator_bits": value.denominator.bit_length() - 1,
                "bound": process.bound,
                "ledger": ledger.as_dict(),
                "ledger_total": ledger.total,
            })
    return {
        "rows": rows,
        "all_meet_contract": all(bool(r["meets_contract"]) for r in rows),
        "denominator_bits_linear": all(
            int(r["denominator_bits"]) <= int(r["requested_bits"]) + 8
            for r in rows),
        "levels": list(levels),
    }


def demand_driven_report(k: int = 64) -> Dict[str, object]:
    """The composite ``(π + e)·√2`` computed two ways, and the tax of each.

    *Demand-driven*: the requested precision is propagated backwards, so each
    leaf is asked for the least precision that still guarantees ``2⁻ᵏ`` at the
    top.  *Uniform*: every leaf is asked for the same generous precision, the
    habit the composition rules replace.  Both answers are checked against the
    reference product, and the ledgers are compared.
    """
    pi, e = er_pi(), er_e()
    root2 = er_sqrt(Fraction(2))
    composite = er_mul(er_add(pi, e), root2)

    value, ledger = composite.at_with_cost(k)
    reference = (REFERENCES["pi"] + REFERENCES["e"]) * REFERENCES["sqrt2"]
    demand_ok = abs(value - reference) <= Fraction(1, 1 << k)

    uniform = Ledger("uniform")
    slack = k + 32
    naive = (pi.at(slack, uniform) + e.at(slack, uniform)) * \
        root2.at(slack, uniform)
    uniform_ok = abs(naive - reference) <= Fraction(1, 1 << k)

    return {
        "expression": composite.name,
        "requested_bits": k,
        "demand_driven_error": abs(value - reference),
        "demand_driven_meets_contract": demand_ok,
        "demand_driven_ledger": ledger.as_dict(),
        "demand_driven_total": ledger.total,
        "uniform_slack_bits": slack,
        "uniform_error": abs(naive - reference),
        "uniform_meets_contract": uniform_ok,
        "uniform_ledger": uniform.as_dict(),
        "uniform_total": uniform.total,
        "work_ratio": Fraction(ledger.total, uniform.total),
        "verified": demand_ok,
    }


# ===========================================================================
# 7.  FREQUENCY-ENCODED STATE: THE Δ-Σ REGISTER
# ===========================================================================


class WobbleSignature:
    """The exact fingerprint of a bit stream: density, runs, autocorrelation."""

    def __init__(self, bits: Sequence[int]) -> None:
        self.bits = list(bits)

    @property
    def length(self) -> int:
        return len(self.bits)

    @property
    def density(self) -> Fraction:
        return Fraction(sum(self.bits), len(self.bits)) if self.bits \
            else Fraction(0)

    @property
    def max_run(self) -> int:
        best = run = 0
        prev: Optional[int] = None
        for b in self.bits:
            run = run + 1 if b == prev else 1
            prev = b
            best = max(best, run)
        return best

    def autocorrelation(self, lag: int) -> Fraction:
        n = len(self.bits) - lag
        if n <= 0:
            return Fraction(0)
        pairs = sum(1 for i in range(n) if self.bits[i] == self.bits[i + lag])
        return Fraction(2 * pairs - n, n)

    def as_dict(self) -> Dict[str, object]:
        return {
            "length": self.length,
            "density": self.density,
            "max_run": self.max_run,
            "autocorrelation_1": self.autocorrelation(1),
        }


class DeltaSigmaRegister:
    """A register that holds a *process*, not a value.

    First-order Δ-Σ: the accumulator takes the current target each tick and
    emits a 1 whenever it crosses 1, subtracting 1.  The accumulator therefore
    stays in ``[0,1)`` whatever the target does, so after ``N`` ticks

        ``|Σ bits − Σ targets| < 1``     (an identity, not an estimate)

    and hence ``|average − mean target| < 1/N``.  This is the read-out bound,
    and it is the reason **continuous retargeting** is safe: :meth:`retarget`
    now keeps the accumulator by default, so the register tracks a *moving*
    target and the same bound applies to the mean of the targets over the
    window.  Against a fixed final target the error picks up exactly the mean
    deviation of the target trajectory (:meth:`tracking_report`).  Both
    statements are proved in ``GLM.ZeroStorageV5`` (``ds_track_bound``,
    ``ds_track_moving_target``).

    Nothing but the current target and one rational accumulator is *needed*;
    the emitted bits and the target history are kept only so that the
    measurements below can be made.
    """

    def __init__(self, target: Fraction, name: str = "reg") -> None:
        if not (0 <= target <= 1):
            raise ValueError("target must lie in [0, 1]")
        self.name = name
        self.target = target
        self.accumulator = Fraction(0)
        self.emitted = 0
        self.ones = 0
        self.stream: List[int] = []
        self.targets: List[Fraction] = []
        self.retargets = 0

    def tick(self, ledger: Optional[Ledger] = None) -> int:
        self.accumulator += self.target
        if self.accumulator >= 1:
            self.accumulator -= 1
            bit = 1
        else:
            bit = 0
        self.emitted += 1
        self.ones += bit
        self.stream.append(bit)
        self.targets.append(self.target)
        if ledger is not None:
            ledger.spend("tick")
            ledger.spend("rational_op", 2)
        return bit

    def clock(self, ticks: int, ledger: Optional[Ledger] = None) -> List[int]:
        return [self.tick(ledger) for _ in range(ticks)]

    @property
    def value(self) -> Fraction:
        """The read-out: the time average of the stream so far."""
        return Fraction(self.ones, self.emitted) if self.emitted else Fraction(0)

    @property
    def mean_target(self) -> Fraction:
        """The mean of the targets the register was actually holding."""
        if not self.targets:
            return self.target
        return sum(self.targets, Fraction(0)) / len(self.targets)

    @property
    def error(self) -> Fraction:
        """Read-out against the mean target — the quantity the bound governs."""
        return abs(self.value - self.mean_target)

    @property
    def error_against_current(self) -> Fraction:
        return abs(self.value - self.target)

    @property
    def within_bound(self) -> bool:
        return self.emitted == 0 or self.error < Fraction(1, self.emitted)

    @property
    def accumulator_in_unit_interval(self) -> bool:
        return 0 <= self.accumulator < 1

    def retarget(self, target: Fraction, continuous: bool = True) -> None:
        """Write a new target.

        ``continuous=True`` (the default in v5) keeps the accumulator, so the
        register carries its phase across the write and tracks a moving
        target; ``continuous=False`` is the v4 behaviour, which zeroes the
        accumulator and the history and therefore starts a fresh window.
        """
        if not (0 <= target <= 1):
            raise ValueError("target must lie in [0, 1]")
        self.target = target
        self.retargets += 1
        if not continuous:
            self.accumulator = Fraction(0)
            self.emitted = 0
            self.ones = 0
            self.stream = []
            self.targets = []

    def follow(self, schedule: Sequence[Fraction],
               ledger: Optional[Ledger] = None) -> None:
        """Clock one tick per entry of a target trajectory, continuously."""
        for t in schedule:
            self.retarget(t, continuous=True)
            self.tick(ledger)

    def tracking_report(self, final: Optional[Fraction] = None
                        ) -> Dict[str, object]:
        """The two bounds, measured on the window just clocked.

        * against the **mean target**: ``|average − mean target| < 1/N``;
        * against a **fixed target** ``t*`` (by default the last one held):
          ``|average − t*| ≤ 1/N + (1/N)Σ|tₙ − t*|`` — the tracking term is
          exactly how fast the target moved.
        """
        n = self.emitted
        if n == 0:
            raise ValueError("nothing has been clocked")
        star = self.target if final is None else final
        drift = sum((abs(t - star) for t in self.targets), Fraction(0)) / n
        return {
            "ticks": n,
            "retargets": self.retargets,
            "average": self.value,
            "mean_target": self.mean_target,
            "error_vs_mean_target": self.error,
            "read_out_bound": Fraction(1, n),
            "read_out_bound_holds": self.error < Fraction(1, n),
            "final_target": star,
            "error_vs_final_target": abs(self.value - star),
            "mean_target_deviation": drift,
            "tracking_bound": Fraction(1, n) + drift,
            "tracking_bound_holds": abs(self.value - star) <= Fraction(1, n) + drift,
            "accumulator_in_unit_interval": self.accumulator_in_unit_interval,
        }

    def wobble(self) -> WobbleSignature:
        return WobbleSignature(self.stream)

    def read_to(self, bits: int, ledger: Optional[Ledger] = None) -> Fraction:
        """Clock until the read-out bound is below ``2⁻ᵇⁱᵗˢ``, then read."""
        need = 1 << bits
        while self.emitted < need:
            self.tick(ledger)
        return self.value


class NoiseShaper:
    """A 1-bit error-feedback modulator of order 1, 2 or 3, in exact rationals.

    The loop is the standard error-feedback form with the noise transfer
    function ``(1 − z⁻¹)^order``: with the stored errors ``e₁, e₂, e₃``,

        order 1:  y = x + e₁
        order 2:  y = x + 2e₁ − e₂
        order 3:  y = x + 3e₁ − 3e₂ + e₃

    and ``b = 1`` iff ``y ≥ ½``, with the errors shifted and ``e₁ ← y − b``.
    Higher order promises faster decay of the averaged error; it also risks an
    accumulator that runs away, so this class *measures* both — the maximum
    excursion ``max|eᵢ|`` is reported beside the error, and no decay rate is
    claimed that has not been measured on the stated target set.
    """

    COEFFICIENTS: Dict[int, Tuple[int, ...]] = {
        1: (1,),
        2: (2, -1),
        3: (3, -3, 1),
    }

    def __init__(self, target: Fraction, order: int = 2,
                 name: str = "shaper") -> None:
        if order not in self.COEFFICIENTS:
            raise ValueError("order must be 1, 2 or 3")
        if not (0 <= target <= 1):
            raise ValueError("target must lie in [0, 1]")
        self.name = name
        self.order = order
        self.coeff = self.COEFFICIENTS[order]
        self.target = target
        self.errors: List[Fraction] = [Fraction(0)] * order
        self.emitted = 0
        self.ones = 0
        self.stream: List[int] = []
        self.targets: List[Fraction] = []
        self.max_excursion = Fraction(0)

    def tick(self, ledger: Optional[Ledger] = None) -> int:
        y = self.target
        for c, e in zip(self.coeff, self.errors):
            y += c * e
        bit = 1 if y >= Fraction(1, 2) else 0
        err = y - bit
        self.errors = [err] + self.errors[:-1]
        self.max_excursion = max(self.max_excursion,
                                 max(abs(e) for e in self.errors))
        self.emitted += 1
        self.ones += bit
        self.stream.append(bit)
        self.targets.append(self.target)
        if ledger is not None:
            ledger.spend("tick")
            ledger.spend("rational_op", 2 * self.order + 1)
        return bit

    def clock(self, ticks: int, ledger: Optional[Ledger] = None) -> List[int]:
        return [self.tick(ledger) for _ in range(ticks)]

    @property
    def value(self) -> Fraction:
        return Fraction(self.ones, self.emitted) if self.emitted else Fraction(0)

    @property
    def error(self) -> Fraction:
        return abs(self.value - self.target)

    def retarget(self, target: Fraction) -> None:
        """Continuous by construction: the error state is never zeroed."""
        if not (0 <= target <= 1):
            raise ValueError("target must lie in [0, 1]")
        self.target = target

    def wobble(self) -> WobbleSignature:
        return WobbleSignature(self.stream)


def register_report(targets: Sequence[Fraction] = (Fraction(1, 3),
                                                   Fraction(2, 7),
                                                   Fraction(5, 8),
                                                   Fraction(1, 1)),
                    ticks: int = 256, bits: int = 24) -> Dict[str, object]:
    """The first-order register: the proved bound and the NRCI, side by side."""
    rows: List[Dict[str, object]] = []
    for t in targets:
        ledger = Ledger(f"reg[{t}]")
        reg = DeltaSigmaRegister(t, f"reg[{t}]")
        reg.clock(ticks, ledger)
        measure = nrci_of_delta_sigma(reg, bits)
        rows.append({
            "target": t,
            "ticks": ticks,
            "value": reg.value,
            "error": reg.error,
            "bound": Fraction(1, ticks),
            "within_bound": reg.within_bound,
            "nrci_lo": measure["lo"],
            "nrci_hi": measure["hi"],
            "nrci_squared_form": measure["squared_form"],
            "nrci_stream": measure["stream"],
            "running_bound_holds": measure["bound_holds"],
            "wobble": reg.wobble().as_dict(),
            "ledger": ledger.as_dict(),
        })
    return {"rows": rows,
            "all_within_bound": all(bool(r["within_bound"]) for r in rows),
            "all_running_bounds_hold": all(bool(r["running_bound_holds"])
                                           for r in rows)}


def tracking_report(ticks: int = 256) -> Dict[str, object]:
    """Continuous retargeting: a register chasing a moving target.

    The trajectory is a deterministic rational ramp with a step in the middle
    — no RNG.  Two registers follow it: one retargeted **continuously** (the
    accumulator survives the write) and one retargeted the v4 way (the
    accumulator and the window are zeroed at every write, so the register
    never accumulates more than one tick of evidence).
    """
    schedule: List[Fraction] = []
    for n in range(ticks):
        if n < ticks // 2:
            schedule.append(Fraction(n, 2 * ticks))          # a ramp
        else:
            schedule.append(Fraction(3, 4))                  # a step, then hold
    ledger = Ledger("tracking")
    continuous = DeltaSigmaRegister(schedule[0], "continuous")
    continuous.follow(schedule, ledger)
    report = continuous.tracking_report()

    zeroing = DeltaSigmaRegister(schedule[0], "zeroing")
    for t in schedule:
        zeroing.retarget(t, continuous=False)
        zeroing.tick()

    tail = DeltaSigmaRegister(Fraction(3, 4), "tail")
    tail.clock(ticks // 2)

    return {
        "ticks": ticks,
        "schedule": "ramp n/(2N) for n < N/2, then the constant 3/4",
        "continuous": report,
        "continuous_error_vs_mean_target": continuous.error,
        "zeroing_ticks_of_evidence": zeroing.emitted,
        "zeroing_error_vs_mean_target": zeroing.error,
        "steady_state_after_step": {
            "ticks": tail.emitted,
            "value": tail.value,
            "error": tail.error,
            "within_bound": tail.within_bound,
        },
        "ledger": ledger.as_dict(),
        "verified": bool(report["read_out_bound_holds"]
                         and report["tracking_bound_holds"]
                         and report["accumulator_in_unit_interval"]),
    }


def triangular_window(length: int) -> List[int]:
    """The Bartlett window ``wₙ = min(n+1, N−n)`` — integers, exactly."""
    return [min(n + 1, length - n) for n in range(length)]


def window_differences(window: Sequence[int], order: int) -> int:
    """``Σₙ |Δ^order w|`` with ``w`` extended by zeros outside the window.

    This is the constant in the read-out bound.  An order-``p`` error-feedback
    loop satisfies ``bₙ − xₙ = −Δᵖe`` exactly, so summing by parts ``p`` times
    gives

        ``|Σ wₙ(bₙ − xₙ)| ≤ max|e| · Σ |Δᵖw|``

    and dividing by ``Σw`` bounds the filtered read-out error.  For the
    rectangular window ``Σ|Δ¹w| = 2`` and ``Σw = N``, which is the familiar
    ``2·max|e|/N``; for the triangular window ``Σ|Δ²w|`` is a constant while
    ``Σw ≈ N²/4``, which is where the ``O(N⁻²)`` of a second-order loop comes
    from.  Nothing is assumed here: the constant is computed from the window.
    """
    seq = [0] * (order + 1) + list(window) + [0] * (order + 1)
    for _ in range(order):
        seq = [seq[i + 1] - seq[i] for i in range(len(seq) - 1)]
    return sum(abs(v) for v in seq)


def filtered_readout(stream: Sequence[int], window: Sequence[int]) -> Fraction:
    """``Σ wₙbₙ / Σ wₙ`` — the smoothed read-out, exactly."""
    total = sum(window)
    if total == 0:
        raise ValueError("the window must have positive mass")
    return Fraction(sum(w * b for w, b in zip(window, stream)), total)


#: Targets used for the noise-shaping measurement.  They are stated here, in
#: the file, because the figures below are claims *about this set* and about
#: nothing else.
SHAPING_TARGETS: Tuple[Fraction, ...] = (Fraction(1, 3), Fraction(2, 7),
                                         Fraction(5, 8),
                                         Fraction(12345, 32768),
                                         Fraction(7, 11))

#: A target close to the rail, kept apart: 1-bit high-order loops are known to
#: go unstable near the ends of the range, and this file measures that rather
#: than assuming it away.
RAIL_TARGET: Fraction = Fraction(1, 1000)


def noise_shaping_report(targets: Sequence[Fraction] = SHAPING_TARGETS,
                         lengths: Sequence[int] = (64, 256, 1024)
                         ) -> Dict[str, object]:
    """Orders 1–3 on a stated target set: measured error, and a real bound.

    For each order and window length the table records

    * the **plain** read-out error (the time average) and ``N·error``;
    * the **filtered** read-out error through the triangular window, and
      ``N²·error`` — the quantity the literature says an order-2 loop should
      keep bounded;
    * the worst state excursion ``max|e|`` observed, which is the stability
      question a 1-bit high-order loop raises; and
    * the **guaranteed** filtered bound ``max|e|·Σ|Δᵖw| / Σw``, computed from
      that excursion and the window — a bound, not a fit, and the only decay
      statement this file makes.

    No decay rate is assumed.  The rail target is measured separately, and
    reported as unstable if its state grows with ``N``.
    """
    rows: List[Dict[str, object]] = []
    for order in (1, 2, 3):
        for length in lengths:
            window = triangular_window(length)
            mass = sum(window)
            diffs = window_differences(window, order)
            worst_plain = Fraction(0)
            worst_filtered = Fraction(0)
            excursion = Fraction(0)
            for t in targets:
                shaper = NoiseShaper(t, order, f"order{order}[{t}]")
                shaper.clock(length)
                worst_plain = max(worst_plain, shaper.error)
                worst_filtered = max(
                    worst_filtered,
                    abs(filtered_readout(shaper.stream, window) - t))
                excursion = max(excursion, shaper.max_excursion)
            guaranteed = excursion * Fraction(diffs, mass)
            rows.append({
                "order": order,
                "ticks": length,
                "worst_plain_error": worst_plain,
                "plain_error_times_N": worst_plain * length,
                "worst_filtered_error": worst_filtered,
                "filtered_error_times_N2": worst_filtered * length * length,
                "worst_excursion": excursion,
                "window_difference_mass": diffs,
                "window_mass": mass,
                "guaranteed_filtered_bound": guaranteed,
                "guarantee_holds": worst_filtered <= guaranteed,
                "plain_within_one_over_N": worst_plain < Fraction(1, length),
            })

    rail: List[Dict[str, object]] = []
    for order in (1, 2, 3):
        excursions = []
        for length in lengths:
            shaper = NoiseShaper(RAIL_TARGET, order, f"rail{order}")
            shaper.clock(length)
            excursions.append((length, shaper.max_excursion, shaper.error))
        grows = (all(a[1] <= b[1] for a, b in zip(excursions, excursions[1:]))
                 and excursions[-1][1] > excursions[0][1])
        rail.append({
            "order": order,
            "target": RAIL_TARGET,
            "excursions": [{"ticks": n, "max_state": e, "error": err}
                           for n, e, err in excursions],
            "state_grows_with_N": grows,
        })

    return {
        "targets": list(targets),
        "window": "triangular (Bartlett)",
        "rows": rows,
        "rail_target": rail,
        "first_order_always_within_one_over_N": all(
            bool(r["plain_within_one_over_N"])
            for r in rows if r["order"] == 1),
        "all_guarantees_hold": all(bool(r["guarantee_holds"]) for r in rows),
        "second_order_excursion_bound": max(
            (r["worst_excursion"] for r in rows if r["order"] == 2),
            default=Fraction(0)),
        "third_order_excursion_bound": max(
            (r["worst_excursion"] for r in rows if r["order"] == 3),
            default=Fraction(0)),
    }


# ===========================================================================
# 8.  SEXTETS — the deep-hole structure, in its honest form
# ===========================================================================


def sextet_of_tetrad(code: GolayCode, tetrad: int,
                     octads: Optional[Sequence[int]] = None
                     ) -> Tuple[int, ...]:
    """The sextet containing a tetrad: six tetrads partitioning the 24 points.

    Each of the 5 octads through the tetrad contributes its complementary
    tetrad, so the tetrad plus those five partition the point set, and any two
    of the six union to an octad.
    """
    source = octads if octads is not None else code.octads()
    parts = [tetrad]
    for octad in source:
        if octad & tetrad == tetrad:
            parts.append(octad ^ tetrad)
    return tuple(sorted(parts))


def sextet_report(code: GolayCode, sample: Optional[int] = None
                  ) -> Dict[str, object]:
    """Check the sextet structure over every tetrad (or a prefix of them)."""
    full = 1 << DIM
    octads = tuple(code.octads())          # streamed once for the whole pass
    seen: set = set()
    checked = 0
    partitions_ok = 0
    unions_ok = 0
    for quad in combinations(range(DIM), 4):
        if sample is not None and checked >= sample:
            break
        checked += 1
        tetrad = sum(1 << i for i in quad)
        parts = sextet_of_tetrad(code, tetrad, octads)
        if len(parts) == 6:
            covered = 0
            overlap = False
            for p in parts:
                if covered & p:
                    overlap = True
                covered |= p
            if not overlap and covered == full - 1:
                partitions_ok += 1
            if all(code.is_codeword(a | b) and (a | b).bit_count() == 8
                   for a, b in combinations(parts, 2)):
                unions_ok += 1
        seen.add(parts)

    return {
        "tetrads_checked": checked,
        "tetrads_total": TETRADS,
        "partitions_verified": partitions_ok,
        "pairwise_unions_are_octads": unions_ok,
        "distinct_sextets": len(seen),
        "expected_sextets": SEXTETS if sample is None else None,
    }


# ===========================================================================
# 9.  THE STORAGE AUDIT, WITH THE COMPUTE TAX
# ===========================================================================


def storage_audit(code: GolayCode, full_shell: bool = True
                  ) -> Dict[str, object]:
    """Stored bytes beside generator bytes **and the tax to recover one item**.

    v4 compared bytes stored with bytes of generator.  That comparison is only
    half of the trade: regenerating is not free.  Each row here also carries
    the exact integer cost of recovering *one* item from the generator, so the
    reader can see where a cache is genuinely worth its digest.  No wall-clock
    figure appears anywhere: every quantity is one a second run reproduces.
    """
    rows: List[Dict[str, object]] = []

    # -- the code ----------------------------------------------------------
    gen = Ledger("code")
    regenerated = tuple(sorted(gray_codewords(code.rows, gen)))
    reference = frozenset(regenerated)
    rows.append({
        "object": "Golay code, all 4096 codewords",
        "stored_bytes": GOLAY_WORDS * 3,
        "generator_bytes": GOLAY_ROWS * 3,
        "count": len(regenerated),
        "tax_per_item": gen.scaled(GOLAY_WORDS),
        "tax_total": gen.total,
        "verified": len(reference) == GOLAY_WORDS,
    })

    # -- membership: the two routes, priced -------------------------------
    syn = Ledger("membership-syndrome")
    tab = Ledger("membership-lookup")
    cached = GolayCode(code.rows, cache=True)   # the stored path, priced apart
    probes = list(regenerated[:256]) + [w ^ 1 for w in regenerated[:256]]
    agree = 0
    for w in probes:
        a = code.is_codeword(w, syn)
        b = cached.is_codeword_cached(w, tab)
        agree += int(a == b)
    rows.append({
        "object": "Golay membership decision",
        "stored_bytes": cached.cached_bytes,
        "generator_bytes": GOLAY_ROWS * 3,
        "count": len(probes),
        "tax_per_item": syn.scaled(len(probes)),
        "tax_total": syn.total,
        "cached_tax_per_item": tab.scaled(len(probes)),
        "cached_tax_total": tab.total,
        "cache_digest": cached.cache_digest,
        "cache_regenerates_identically": cached.cache_is_what_the_rows_generate(),
        "verified": agree == len(probes),
    })

    # -- the octads --------------------------------------------------------
    oct_ledger = Ledger("octads")
    octads = tuple(code.octads(oct_ledger))
    rows.append({
        "object": "759 octads",
        "stored_bytes": GOLAY_OCTADS * 3,
        "generator_bytes": GOLAY_ROWS * 3,
        "count": len(octads),
        "tax_per_item": oct_ledger.scaled(GOLAY_OCTADS),
        "tax_total": oct_ledger.total,
        "verified": len(octads) == GOLAY_OCTADS,
    })

    # -- the shell ---------------------------------------------------------
    if full_shell:
        shell = Ledger("shell")
        count = 0
        ok = True
        shapes: Counter = Counter()
        for vec in minimal_vectors(code, shell):
            count += 1
            if not is_leech(vec, code) or norm2(vec) != MIN_NORM2:
                ok = False
            shapes[tuple(sorted(Counter(abs(v) for v in vec).items(),
                                reverse=True))] += 1
        rows.append({
            "object": "196,560 minimal vectors of Λ₂₄",
            "stored_bytes": count * DIM,
            "generator_bytes": GOLAY_ROWS * 3,
            "count": count,
            "tax_per_item": shell.scaled(max(count, 1)),
            "tax_total": shell.total,
            "verified": ok and count == KISSING,
            "shapes": {str(k): v for k, v in shapes.items()},
        })

    # -- the snap ----------------------------------------------------------
    snap = Ledger("snap")
    decoder = LeechDecoder(code)
    snapped = 0
    for target in probe_targets(2):
        out = decoder.nearest(target, snap)
        snapped += int(bool(out["in_lattice"]))
    rows.append({
        "object": "nearest-point decode (one snap)",
        "stored_bytes": KISSING * DIM,
        "generator_bytes": GOLAY_ROWS * 3,
        "count": snapped,
        "tax_per_item": snap.scaled(2),
        "tax_total": snap.total,
        "verified": snapped == 2,
    })

    stored = sum(int(r["stored_bytes"]) for r in rows)
    generated = sum(int(r["generator_bytes"]) for r in rows)
    return {
        "rows": rows,
        "stored_bytes": stored,
        "generator_bytes": generated,
        "ratio": Fraction(stored, generated),
        "all_verified": all(bool(r["verified"]) for r in rows),
    }


# ===========================================================================
# 10.  SELF-VERIFICATION
# ===========================================================================


def run_self_test(quick: bool = False, verbose: bool = True,
                  full: bool = False) -> bool:
    """Every claim this file makes, measured.  Returns True iff all hold."""
    results: List[Tuple[str, bool, str]] = []

    def say(text: str = "") -> None:
        if verbose:
            print(text)

    say("=" * 74)
    say("  GLM ZERO-STORAGE SUBSTRATE v5 — SELF-VERIFICATION")
    say("  generate what is a consequence; check every generator; pay the tax")
    say("=" * 74)

    # --- 1. the code, from 12 rows and nothing else -----------------------
    code = GolayCode()
    build = Ledger("invariants")
    inv = code.invariants(build)
    ok = code.invariants_hold()
    say("\n[1] Golay code, generated from the quadratic residues mod 11")
    say(f"    generator rows      : {inv['generator_rows']} "
        f"({inv['generator_bytes']} bytes)")
    say(f"    bytes held          : {inv['held_bytes']} (no codeword table)")
    say(f"    codewords           : {inv['codewords']}")
    say(f"    weight distribution : {inv['weight_distribution']}")
    say(f"    minimum distance    : {inv['minimum_distance']}")
    say(f"    rank / self-dual    : {inv['rank']} / {inv['self_dual_generator']}")
    lean = GolayCode(LEAN_GOLAY_ROWS)
    lean_ok = lean.invariants_hold()
    say(f"    the Lean generator rows give the same invariants: {lean_ok}")
    results.append(("Golay code invariants", ok and lean_ok,
                    str(inv["weight_distribution"])))

    # --- 2. the syndrome replaces the lookup ------------------------------
    say("\n[2] Membership by syndrome — the 4096-word lookup, removed")
    check = check_syndrome_against_lookup(code, full=full)
    say(f"    every codeword has syndrome 0        : "
        f"{check['all_codewords_have_zero_syndrome']}")
    say(f"    words of zero syndrome (exact kernel): {check['kernel_size']}"
        f" — equals the code: {check['kernel_equals_code']}")
    if check["swept_2_24"] is not None:
        say(f"    all 16,777,216 words swept           : "
            f"{check['swept_2_24']} accepted, agrees: {check['sweep_agrees']}")
    say(f"    the 196,560-vector shell, both routes: "
        f"{check['shell_vectors_compared']} compared, agree: "
        f"{check['shell_routes_agree']}")
    say(f"    non-codewords, both routes           : "
        f"{check['non_codewords_compared']} compared, agree: "
        f"{check['non_codeword_routes_agree']}")
    lean_check = check_syndrome_against_lookup(lean, full=False)
    say(f"    the same, on the Lean generator rows : {lean_check['verified']}")
    say(f"    cost of one membership decision      : 12 parity checks, "
        f"36 bytes of generator")
    results.append(("Syndrome membership == lookup",
                    bool(check["verified"]) and bool(lean_check["verified"]),
                    f"{check['kernel_size']} words of zero syndrome, "
                    f"{check['shell_vectors_compared']} shell vectors, "
                    "both generators"))

    # --- 3. membership witnesses ------------------------------------------
    say("\n[3] Leech membership as three congruences and twelve parities")
    witnesses = [
        (tuple([0] * DIM), True, "zero vector"),
        (tuple([4, 4] + [0] * 22), True, "(4,4,0²²)"),
        (tuple([2, 2] + [0] * 22), False, "(2,2,0²²) — v3's 'even' fallback"),
        (tuple([-3] + [1] * 23), True, "(−3,1²³)"),
        (tuple([1] * DIM), False, "(1²⁴)"),
        (tuple([2] + [0] * 23), False, "(2,0²³)"),
    ]
    octad = next(code.octads())
    octad_vec = tuple(2 if (octad >> i) & 1 else 0 for i in range(DIM))
    witnesses.append((octad_vec, True, "2·(an octad) — the vector v3 lost"))
    all_ok = True
    for vec, expected, label in witnesses:
        led = Ledger("member")
        got = is_leech(vec, code, ledger=led)
        syn = leech_syndrome(vec, code.rows)
        flag = "ok" if got == expected else "FAIL"
        all_ok &= got == expected
        say(f"    {label:44s} in Λ: {str(got):5s} "
            f"syndrome: {'—' if syn is None else syn:>5} "
            f"cost: {led.total:3d} [{flag}]")
    results.append(("Membership witnesses", all_ok, f"{len(witnesses)} vectors"))

    # --- 4. the shell -----------------------------------------------------
    say("\n[4] The minimal shell, generated and checked")
    if quick:
        say("    (skipped: --quick)")
        results.append(("Minimal shell", True, "skipped"))
    else:
        shell_ledger = Ledger("shell")
        seen = set()
        norms_ok = True
        member_ok = True
        for vec in minimal_vectors(code, shell_ledger):
            seen.add(vec)
            if norm2(vec) != MIN_NORM2:
                norms_ok = False
            if not is_leech(vec, code):
                member_ok = False
        shell_ok = len(seen) == KISSING and norms_ok and member_ok
        say(f"    distinct vectors    : {len(seen)} (expected {KISSING})")
        say(f"    all of norm² 32     : {norms_ok}")
        say(f"    all pass the sieve  : {member_ok}")
        say(f"    tax for the shell   : {shell_ledger.as_dict()}")
        results.append(("Minimal shell (196,560)", shell_ok,
                        f"{len(seen)} vectors, norm²=32, all in Λ"))

    # --- 5. the decoder ---------------------------------------------------
    say("\n[5] Exact nearest-point decoding, pruned and priced")
    decoder = LeechDecoder(code)
    probes = probe_targets(3)
    near = None
    for i, vec in enumerate(minimal_vectors(code)):
        if i == 5000:
            near = vec
            break
    shifted = [Fraction(v) for v in near]
    shifted[0] += Fraction(1, 2)
    shifted[7] -= Fraction(1, 2)
    probes.append(tuple(shifted))
    decode_ok = True
    for idx, target in enumerate(probes):
        out = decoder.nearest(target)
        good = bool(out["in_lattice"]) and bool(out["within_covering_radius"])
        decode_ok &= good
        say(f"    probe {idx}: dist² = {str(out['dist2']):>12s}  "
            f"in Λ: {out['in_lattice']}  ≤ ρ² = {out['within_covering_radius']}"
            f"  cosets {out['cosets_evaluated']:5d} kept / "
            f"{out['cosets_pruned']:5d} pruned")
    exact_half = decoder.nearest(tuple(shifted))
    back_ok = exact_half["dist2"] == Fraction(1, 2)
    say(f"    half-step target decodes at dist² = {exact_half['dist2']} "
        f"(expected 1/2): {back_ok}")
    prune_report = decoder_cost_report(code, probes=2 if quick else 3)
    say(f"    pruned search agrees with the exhaustive one: "
        f"{prune_report['all_agree_with_exhaustive']}")
    say(f"    mean work ratio pruned : exhaustive = "
        f"{prune_report['mean_work_ratio']} "
        f"(~{float(prune_report['mean_work_ratio']):.3f})")
    local_ok = True
    if not quick:
        for target in probes[:2]:
            out = decoder.nearest(target)
            local_ok &= decoder.locally_optimal(target, out["point"])
        say(f"    no nearer point among the 196,560 neighbours: {local_ok}")
    results.append(("Exact decoder",
                    decode_ok and back_ok and local_ok
                    and bool(prune_report["all_agree_with_exhaustive"]),
                    f"{len(probes)} probes, all in Λ within ρ²=16, "
                    "pruned == exhaustive"
                    + ("" if quick else ", locally optimal")))

    # --- 6. the dyadic tower ---------------------------------------------
    say("\n[6] The dyadic tower")
    third = DyadicTower.audit(Fraction(1, 3))
    eighth = DyadicTower.audit(Fraction(3, 8))
    tower_ok = (bool(third["window_contains_q"]) and bool(third["non_decreasing"])
                and not bool(third["strictly_increasing"])
                and third["exact_level"] is None
                and eighth["exact_level"] == 3
                and bool(eighth["is_dyadic"])
                and bool(third["resolution_strictly_improves"]))
    say(f"    q = 1/3 : window holds q = {third['window_contains_q']}, "
        f"readings strictly increasing = {third['strictly_increasing']} "
        f"(non-decreasing = {third['non_decreasing']})")
    say(f"    q = 3/8 : dyadic = {eighth['is_dyadic']}, "
        f"exact at level {eighth['exact_level']}")
    results.append(("Dyadic tower", tower_ok,
                    "windows hold, resolution strictly improves, "
                    "readings only non-decreasing"))

    # --- 7. generated reals, and demand-driven precision ------------------
    say("\n[7] Generated reals: |x.at(k) − x| ≤ 2⁻ᵏ, with the work they cost")
    levels = (8, 32) if quick else (8, 32, 96)
    reals = exact_real_report(levels)
    for row in reals["rows"]:
        say(f"    {row['constant']:6s} k={row['requested_bits']:<4d} "
            f"error ≤ 2^-k: {str(row['meets_contract']):5s}  "
            f"den bits: {row['denominator_bits']:<4d} "
            f"tax: {row['ledger_total']}")
    demand = demand_driven_report(k=32 if quick else 64)
    say(f"    composite {demand['expression']} at k={demand['requested_bits']}")
    say(f"      demand-driven: contract {demand['demand_driven_meets_contract']}, "
        f"tax {demand['demand_driven_total']}")
    say(f"      uniform slack: contract {demand['uniform_meets_contract']}, "
        f"tax {demand['uniform_total']}  "
        f"→ ratio {demand['work_ratio']} "
        f"(~{float(demand['work_ratio']):.3f})")
    results.append(("Generated reals meet their contract",
                    bool(reals["all_meet_contract"])
                    and bool(reals["denominator_bits_linear"])
                    and bool(demand["verified"]),
                    f"{len(reals['rows'])} (constant, precision) pairs, "
                    "plus one demand-driven composite"))

    # --- 8. the register, continuous retargeting, higher order ------------
    say("\n[8] Frequency-encoded state")
    regs = register_report(ticks=128 if quick else 256)
    for row in regs["rows"]:
        say(f"    target {str(row['target']):5s}: value {str(row['value']):9s} "
            f"error {str(row['error']):12s} < 1/N: {row['within_bound']}  "
            f"NRCI ∈ [{float(row['nrci_lo']):.6f}, {float(row['nrci_hi']):.6f}]")
    track = tracking_report(ticks=128 if quick else 256)
    cont = track["continuous"]
    say(f"    continuous retargeting over {cont['ticks']} ticks and "
        f"{cont['retargets']} writes:")
    say(f"      |average − mean target| = {cont['error_vs_mean_target']} "
        f"< 1/N = {cont['read_out_bound']}: {cont['read_out_bound_holds']}")
    say(f"      |average − final target| = {cont['error_vs_final_target']} "
        f"≤ 1/N + drift = {cont['tracking_bound']}: "
        f"{cont['tracking_bound_holds']}")
    say(f"      accumulator stayed in [0,1): "
        f"{cont['accumulator_in_unit_interval']}")
    say(f"      the v4 zeroing register held {track['zeroing_ticks_of_evidence']}"
        f" tick of evidence at the end of the same trajectory")
    shaping = noise_shaping_report(
        lengths=(64, 256) if quick else (64, 256, 1024))
    say(f"    higher-order noise shaping, measured on "
        f"{len(shaping['targets'])} targets, "
        f"{shaping['window']} read-out window:")
    say("      order    N   N·(plain err)   N²·(filtered err)   max|e|   "
        "guaranteed bound")
    for row in shaping["rows"]:
        say(f"      {row['order']:^5d} {row['ticks']:>5d} "
            f"{float(row['plain_error_times_N']):>13.4f} "
            f"{float(row['filtered_error_times_N2']):>19.4f} "
            f"{float(row['worst_excursion']):>8.3f} "
            f"{float(row['guaranteed_filtered_bound']):>17.3e}"
            f"  {'ok' if row['guarantee_holds'] else 'FAIL'}")
    say(f"      first order always within 1/N: "
        f"{shaping['first_order_always_within_one_over_N']}; "
        f"every guaranteed bound held: {shaping['all_guarantees_hold']}")
    for rail in shaping["rail_target"]:
        last = rail["excursions"][-1]
        say(f"      near the rail (target {rail['target']}), order "
            f"{rail['order']}: max|e| = {float(last['max_state']):.3f} at "
            f"N = {last['ticks']}, state grows with N: "
            f"{rail['state_grows_with_N']}")
    results.append(("Δ-Σ register: bound, NRCI, continuous retargeting",
                    bool(regs["all_within_bound"])
                    and bool(regs["all_running_bounds_hold"])
                    and bool(track["verified"])
                    and bool(shaping["first_order_always_within_one_over_N"])
                    and bool(shaping["all_guarantees_hold"]),
                    f"{len(regs['rows'])} targets, one moving target, "
                    "orders 1–3 measured"))

    # --- 9. NRCI, one definition, three streams ---------------------------
    say("\n[9] NRCI = 1 − √(Σr²/Σx²), as an exact dyadic enclosure")
    reg = DeltaSigmaRegister(Fraction(2, 7), "nrci")
    reg.clock(128 if quick else 512)
    ds = nrci_of_delta_sigma(reg)
    dec = nrci_of_decode(probes[0], decoder.nearest(probes[0])["point"])
    tw = nrci_of_tower(Fraction(1, 3), 12)
    nrci_rows = [("Δ-Σ running-average residual", ds),
                 ("decode coordinate residual", dec),
                 ("dyadic tower per-level residual", tw)]
    nrci_ok = True
    for label, row in nrci_rows:
        good = (row["lo"] <= row["hi"]
                and row["hi"] - row["lo"] <= row["width"] + Fraction(1, 1 << 40))
        nrci_ok &= good
        say(f"    {label:34s} NRCI ∈ [{float(row['lo']):.9f}, "
            f"{float(row['hi']):.9f}]  (squared form "
            f"{float(row['squared_form']):.9f})")
    say(f"    Δ-Σ: the proved bound |r_N| < 1/N held at every N: "
        f"{ds['bound_holds']}")
    nrci_ok &= bool(ds["bound_holds"])
    results.append(("NRCI, one definition, three streams", nrci_ok,
                    "enclosures of width ≤ 2⁻³², proved bound beside them"))

    # --- 10. sextets ------------------------------------------------------
    say("\n[10] Sextets (the deep-hole structure)")
    sext = sextet_report(code, sample=400 if quick else None)
    sext_ok = (sext["partitions_verified"] == sext["tetrads_checked"]
               and sext["pairwise_unions_are_octads"] == sext["tetrads_checked"])
    if not quick:
        sext_ok &= sext["distinct_sextets"] == SEXTETS
    say(f"    tetrads checked            : {sext['tetrads_checked']}")
    say(f"    six-part partitions        : {sext['partitions_verified']}")
    say(f"    pairwise unions are octads : {sext['pairwise_unions_are_octads']}")
    say(f"    distinct sextets           : {sext['distinct_sextets']}"
        f" (expected {SEXTETS} over all tetrads)")
    results.append(("Sextet structure", sext_ok,
                    f"{sext['tetrads_checked']} tetrads"))

    # --- 11. the audit ----------------------------------------------------
    say("\n[11] Storage audit — stored bytes, generator bytes, and the tax")
    audit = storage_audit(code, full_shell=not quick)
    for row in audit["rows"]:
        say(f"    {str(row['object']):40s} "
            f"{int(row['stored_bytes']):>10,d} B → "
            f"{int(row['generator_bytes']):>7,d} B   "
            f"tax/item {row['tax_total']}/{row['count']}   "
            f"verified: {row['verified']}")
    say(f"    {'TOTAL':40s} {audit['stored_bytes']:>10,d} B → "
        f"{audit['generator_bytes']:>7,d} B   "
        f"ratio {float(audit['ratio']):.1f} : 1")
    results.append(("Storage audit with compute tax", bool(audit["all_verified"]),
                    f"ratio {audit['ratio']}"))

    # --- summary ----------------------------------------------------------
    say("\n" + "=" * 74)
    say("  SUMMARY")
    say("=" * 74)
    all_pass = True
    for name, passed, detail in results:
        all_pass &= passed
        say(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")
    say()
    if all_pass:
        say("  No stored code, no stored shell, no stored constant, no stored")
        say("  membership table — 36 bytes of generator and twelve parities —")
        say("  no float, no RNG, and every answer priced in exact integers.")
    else:
        say("  SOME CHECKS FAILED")
    say("=" * 74)
    return all_pass


# ===========================================================================
# 11.  REPORT, LEDGER VIEW AND DEMO
# ===========================================================================


def _jsonable(obj: object) -> object:
    if isinstance(obj, Fraction):
        return {"num": obj.numerator, "den": obj.denominator,
                "approx": float(obj)}
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    return obj


def build_report(quick: bool = False, full: bool = False) -> Dict[str, object]:
    code = GolayCode()
    audit = storage_audit(code, full_shell=not quick)
    syndrome_check = check_syndrome_against_lookup(code, full=full)
    return {
        "golay": code.invariants(),
        "syndrome_check": syndrome_check,
        "storage": audit,
        "decoder": decoder_cost_report(code, probes=2 if quick else 3),
        "exact_real": exact_real_report((8, 32) if quick else (8, 32, 96)),
        "demand_driven": demand_driven_report(k=32 if quick else 64),
        "register": register_report(),
        "tracking": tracking_report(),
        "noise_shaping": noise_shaping_report(
            lengths=(64, 256) if quick else (64, 256, 1024)),
        "nrci": {
            "definition": "NRCI(r ; x) = 1 − sqrt(sum r^2 / sum x^2), "
                          "reported as an exact dyadic enclosure",
            "dyadic_tower_one_third": nrci_of_tower(Fraction(1, 3), 12),
        },
        "sextet": sextet_report(code, sample=400 if quick else None),
        "tower": {
            "one_third": DyadicTower.audit(Fraction(1, 3)),
            "three_eighths": DyadicTower.audit(Fraction(3, 8)),
        },
        "verdict": {
            "golay_invariants": code.invariants_hold(),
            "syndrome_replaces_lookup": syndrome_check["verified"],
            "storage_verified": audit["all_verified"],
        },
    }


def ledger_view() -> None:
    """Print the cost of each headline operation, in exact integers."""
    code = GolayCode()
    print("GLM Zero-Storage Substrate v5 — the cost ledger\n")
    print("Every figure is an exact integer count of primitive operations.")
    print("Nothing here is a wall-clock time; a second run reproduces it.\n")
    print("  item                what one unit means")
    for item, meaning in LEDGER_ITEMS.items():
        print(f"  {item:18s}  {meaning}")

    print("\n1. One Golay membership decision")
    led = Ledger("membership")
    code.is_codeword(0xABCDEF, led)
    print(f"   syndrome route : {led.as_dict()}  (36 bytes of generator)")
    cached = GolayCode(code.rows, cache=True)
    led2 = Ledger("cached")
    cached.is_codeword_cached(0xABCDEF, led2)
    print(f"   cached route   : {led2.as_dict()}  "
          f"({cached.cached_bytes:,} bytes held, digest "
          f"{cached.cache_digest[:16]}…)")

    print("\n2. One Leech membership decision")
    led = Ledger("leech")
    is_leech(tuple([4, 4] + [0] * 22), code, ledger=led)
    print(f"   {led.as_dict()}")

    print("\n3. One nearest-point decode")
    decoder = LeechDecoder(code)
    target = probe_targets(1)[0]
    out = decoder.nearest(target)
    print(f"   pruned     : {out['ledger']}  total {out['ledger_total']}")
    slow = decoder.nearest(target, prune=False)
    print(f"   exhaustive : {slow['ledger']}  total {slow['ledger_total']}")
    print(f"   same point : {out['point'] == slow['point']}")

    print("\n4. One real number to 64 bits")
    for name, process in exact_real_catalogue().items():
        cost = process.cost(64)
        print(f"   {name:6s} {cost['ledger']}  total {cost['ledger_total']}, "
              f"denominator {cost['denominator_bits']} bits")

    print("\n5. Regenerating each stored object once")
    audit = storage_audit(code, full_shell=True)
    for row in audit["rows"]:
        per = {k: str(v) for k, v in row["tax_per_item"].items()}
        print(f"   {str(row['object']):40s} stored "
              f"{int(row['stored_bytes']):>9,d} B, generator "
              f"{int(row['generator_bytes']):>5,d} B, tax/item {per}")


def run_demo() -> None:
    code = GolayCode()
    decoder = LeechDecoder(code)
    print("GLM Zero-Storage Substrate v5 — worked examples\n")

    print("1. Membership is twelve parities, not a lookup")
    for mask, label in ((next(code.octads()), "an octad"),
                        (0xFFFFFF, "the all-ones word"),
                        (0b1111, "a tetrad")):
        led = Ledger("m")
        s = code.syndrome(mask, led)
        print(f"   {label:18s} syndrome {s:4d}  codeword: {s == 0}  "
              f"cost {led.as_dict()}")

    print("\n2. The exact snap, pruned")
    target = tuple(Fraction(k % 7, 4) - 1 for k in range(DIM))
    out = decoder.nearest(target)
    print(f"   target      : {[str(t) for t in target[:6]]} …")
    print(f"   nearest     : {out['point'][:6]} …")
    print(f"   squared dist: {out['dist2']} (~{float(out['dist2']):.6f})")
    print(f"   in Λ₂₄      : {out['in_lattice']};  "
          f"within ρ² = 16: {out['within_covering_radius']}")
    print(f"   cosets kept {out['cosets_evaluated']}, "
          f"pruned {out['cosets_pruned']}, tax {out['ledger_total']}")
    print(f"   NRCI of the decode: "
          f"{float(nrci_of_decode(target, out['point'])['lo']):.6f} … "
          f"{float(nrci_of_decode(target, out['point'])['hi']):.6f}")

    print("\n3. A real number as a process, with its bill")
    pi = er_pi()
    for k in (4, 16, 64):
        value, led = pi.at_with_cost(k)
        print(f"   pi.at({k:3d}) = {value.numerator}/{value.denominator}"
              f"  (~{float(value):.18f})  tax {led.total}")

    print("\n4. A register chasing a moving target")
    reg = DeltaSigmaRegister(Fraction(1, 4), "demo")
    reg.follow([Fraction(1, 4)] * 30 + [Fraction(3, 4)] * 30)
    rep = reg.tracking_report()
    print(f"   stream : {''.join(str(b) for b in reg.stream[:40])}…")
    print(f"   |avg − mean target| = {rep['error_vs_mean_target']} "
          f"< 1/N = {rep['read_out_bound']}: {rep['read_out_bound_holds']}")
    print(f"   |avg − final target| = {rep['error_vs_final_target']} "
          f"≤ {rep['tracking_bound']}: {rep['tracking_bound_holds']}")

    print("\n5. A sextet")
    tetrad = 0b1111
    parts = sextet_of_tetrad(code, tetrad)
    print(f"   tetrad {[i for i in range(DIM) if (tetrad >> i) & 1]}")
    for p in parts:
        print(f"     part {[i for i in range(DIM) if (p >> i) & 1]}")
    print(f"   parts: {len(parts)}, union is the whole point set: "
          f"{_union(parts) == (1 << DIM) - 1}")


def _union(parts: Iterable[int]) -> int:
    total = 0
    for p in parts:
        total |= p
    return total


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="The GLM zero-storage substrate, v5: "
                    "generated, checked, and taxed.")
    parser.add_argument("--test", action="store_true",
                        help="run the self-verification suite")
    parser.add_argument("--report", action="store_true",
                        help="emit the full report as JSON")
    parser.add_argument("--demo", action="store_true",
                        help="print worked examples")
    parser.add_argument("--ledger", action="store_true",
                        help="print the cost of each headline operation")
    parser.add_argument("--quick", action="store_true",
                        help="skip the full 196,560-vector passes")
    parser.add_argument("--full", action="store_true",
                        help="also sweep all 2²⁴ words in the syndrome check "
                             "(slow; the null-space check already proves it)")
    args = parser.parse_args(argv)

    if args.test:
        return 0 if run_self_test(quick=args.quick, full=args.full) else 1
    if args.report:
        print(json.dumps(_jsonable(build_report(quick=args.quick,
                                                full=args.full)), indent=2))
        return 0
    if args.ledger:
        ledger_view()
        return 0
    if args.demo:
        run_demo()
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

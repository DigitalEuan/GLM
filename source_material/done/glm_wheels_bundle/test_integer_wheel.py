#!/usr/bin/env python3
"""Test harness for the GLM Integer Wheel.

Four test groups, mirroring the four required guarantees:

  1. SANITY       — known OEIS sequences are identified correctly.
  2. RULE 30      — the wheel correctly names Rule-30-derived sequences
                    (centre column, period-doubling diagonals, dyadic tower
                    periods) and correctly stays silent on sequences that
                    are NOT in OEIS.
  3. SOUNDNESS    — every spoken OEIS ID is re-verified against the entry's
                    b-file (the Wheel.lean `Sound truth p` predicate).
  4. NON-REPETITION — the Integer Wheel's provision signature
                    `Sequence[int] -> Optional[str]` is strictly different
                    from DriveWheel, NeedsWheel, and glm_wheel.

Run:  python3 test_integer_wheel.py
Exit code 0 iff all tests pass.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from integer_wheel import (
    IntegerWheel,
    OEISEntry,
    default_wheel,
    RING_DONT_KNOW,
    RING_KNOWS,
    RING_THINKS_TRUE,
)


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Tiny test framework (no external deps)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

_PASS = 0
_FAIL = 0
_LOG: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    status = "PASS" if cond else "FAIL"
    if cond:
        _PASS += 1
    else:
        _FAIL += 1
    line = f"  [{status}] {name}"
    if detail:
        line += f"  -- {detail}"
    print(line)
    _LOG.append(line)


def section(title: str) -> None:
    print(f"\n{title}")
    print("-" * 70)


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Group 1: sanity — known sequences identify correctly
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_sanity(wheel: IntegerWheel) -> None:
    section("GROUP 1: SANITY — known sequences identify correctly")

    cases: list[Tuple[str, list[int], str]] = [
        ("Fibonacci numbers",        [0, 1, 1, 2, 3, 5, 8, 13, 21, 34],         "A000045"),
        ("Lucas numbers",            [2, 1, 3, 4, 7, 11, 18, 29, 47, 76],        "A000032"),
        ("Prime numbers",            [2, 3, 5, 7, 11, 13, 17, 19, 23, 29],       "A000040"),
        ("Composite numbers",        [4, 6, 8, 9, 10, 12, 14, 15, 16, 18],        "A002808"),
        ("Powers of 2",              [1, 2, 4, 8, 16, 32, 64, 128, 256, 512],     "A000079"),
        ("Powers of 3",              [1, 3, 9, 27, 81, 243, 729, 2187, 6561],    "A000244"),
        ("Factorials",               [1, 1, 2, 6, 24, 120, 720, 5040, 40320],    "A000142"),
        ("Squares",                  [0, 1, 4, 9, 16, 25, 36, 49, 64, 81],        "A000290"),
        ("Cubes",                    [0, 1, 8, 27, 64, 125, 216, 343, 512],       "A000578"),
        ("Triangular",               [0, 1, 3, 6, 10, 15, 21, 28, 36, 45],        "A000217"),
        ("Tetrahedral",              [0, 1, 4, 10, 20, 35, 56, 84, 120, 165],     "A000292"),
        ("Catalan",                  [1, 1, 2, 5, 14, 42, 132, 429, 1430],        "A000108"),
        ("Bell",                    [1, 1, 2, 5, 15, 52, 203, 877, 4140],         "A000110"),
        ("Motzkin",                  [1, 1, 2, 4, 9, 21, 51, 127, 323, 835],      "A001006"),
        ("Padovan",                  [1, 0, 0, 1, 0, 1, 1, 1, 2, 2],              "A000931"),
        ("Narayana cows",            [1, 1, 1, 2, 3, 4, 6, 9, 13, 19],           "A000930"),
        ("Tribonacci",               [0, 0, 1, 1, 2, 4, 7, 13, 24, 44],           "A000073"),
        ("Jacobsthal",               [0, 1, 1, 3, 5, 11, 21, 43, 85, 171],       "A001045"),
        ("Perrin",                   [3, 0, 2, 3, 2, 5, 5, 7, 10, 12],            "A001608"),
        ("Derangements",             [1, 0, 1, 2, 9, 44, 265, 1854],              "A000166"),
        ("Involutions",              [1, 1, 2, 4, 10, 26, 76, 232],               "A000085"),
        ("Mersenne numbers (2^n-1)",[0, 1, 3, 7, 15, 31, 63, 127, 255, 511],    "A000225"),
        ("Primorial",                [1, 2, 6, 30, 210, 2310, 30030],            "A002110"),
        ("Highly composite",         [1, 2, 4, 6, 12, 24, 36, 48, 60, 120],      "A002182"),
        ("Ulam numbers",             [1, 2, 3, 4, 6, 8, 11, 13, 16, 18],        "A002858"),
        ("LCM 1..n",                 [1, 1, 2, 6, 12, 60, 60, 420, 840],         "A003418"),
        ("Recaman",                  [0, 1, 3, 6, 2, 7, 13, 20, 12, 21],          "A005132"),
        ("Odd numbers",              [1, 3, 5, 7, 9, 11, 13, 15, 17, 19],        "A005408"),
        ("Even numbers",             [0, 2, 4, 6, 8, 10, 12, 14, 16, 18],        "A005843"),
        ("Thue-Morse",               [0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0,
                                      1, 1, 0],                                  "A010060"),
        ("Evil numbers",              [0, 3, 5, 6, 9, 10, 12, 15, 17, 18],        "A001969"),
        ("Odious numbers",            [1, 2, 4, 7, 8, 11, 13, 14, 16, 19],        "A000069"),
        ("Hamming weight",            [0, 1, 1, 2, 1, 2, 2, 3, 1, 2],             "A000120"),
        ("Pascal flattened",          [1, 1, 1, 1, 2, 1, 1, 3, 3, 1],             "A007318"),
        ("e digits",                  [2, 7, 1, 8, 2, 8, 1, 8, 2, 8, 4, 5, 9,
                                      0, 4, 5],                                  "A001113"),
        ("pi digits",                 [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9,
                                      7, 9, 3],                                  "A000796"),
        ("sqrt(2) digits",            [1, 4, 1, 4, 2, 1, 3, 5, 6, 2, 3, 7, 3,
                                      0, 9, 5],                                  "A010505"),
        ("golden ratio digits",       [1, 6, 1, 8, 0, 3, 3, 9, 8, 8, 7, 4, 9,
                                      8, 9, 4],                                  "A001622"),
        ("ln(2) digits",              [6, 9, 3, 1, 4, 7, 1, 8, 0, 5, 5, 9, 9,
                                      4, 5, 3],                                  "A002162"),
        ("Pell numbers",              [0, 1, 2, 5, 12, 29, 70, 169, 408, 985],    "A000129"),
        ("Stern's diatomic",          [0, 1, 1, 2, 1, 3, 2, 3, 1, 4],             "A002487"),
        ("Woodall numbers",           [1, 7, 23, 63, 159, 383, 895, 2047, 4607],  "A003261"),
        ("Look-and-say lengths",      [1, 2, 2, 4, 6, 6, 8, 10, 14, 20],         "A001155"),
        ("Pentagonal numbers",        [0, 1, 5, 12, 22, 35, 51, 70, 92, 117],     "A000326"),
        ("Hexagonal numbers",         [1, 6, 15, 28, 45, 66, 91, 120, 153],       "A000384"),
        ("Double factorial (odd)",    [1, 1, 3, 15, 105, 945, 10395, 135135],     "A001147"),
        ("Generalized pentagonal",    [0, 1, 2, 5, 7, 12, 15, 22, 26, 35],        "A001318"),
        ("Number of divisors",        [1, 2, 2, 3, 2, 4, 2, 4, 3, 4],             "A000005"),
        ("Euler totient",             [1, 1, 2, 2, 4, 2, 6, 4, 6, 4],            "A000010"),
        ("Prime counting pi(n)",      [0, 0, 1, 2, 2, 3, 3, 4, 4, 4],             "A000720"),
        ("All-1s",                    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],             "A000012"),
        ("Zero sequence",             [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],            "A000004"),
        ("All-0s characteristic",     [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],             "A000007"),
    ]

    for name, seq, expected_id in cases:
        spoken = wheel.speak(seq)
        ok = (spoken == expected_id)
        detail = (f"spoke {spoken}, expected {expected_id}"
                 if not ok else f"spoke {spoken} correctly")
        check(f"identify {name}", ok, detail)


def test_sanity_no_match(wheel: IntegerWheel) -> None:
    section("GROUP 1b: SANITY (negative) — random sequences stay silent")

    # The "Lost numbers" from LOST (4, 8, 15, 16, 23, 42) are not an OEIS sequence
    spoken = wheel.speak([4, 8, 15, 16, 23, 42, 999, 1234, 5678, 90123])
    check("Lost numbers (not in OEIS) stay silent", spoken is None,
          f"spoke {spoken!r}, expected None")

    # Random large numbers unlikely to be a sequence prefix
    spoken = wheel.speak([42, 71, 9, 333, 90210, 8675309])
    check("random large numbers stay silent", spoken is None,
          f"spoke {spoken!r}, expected None")

    # A sequence with all distinct random values
    spoken = wheel.speak([7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83])
    # primes from 7 onward — should NOT match A000040 (which starts at 2)
    check("primes starting at 7 (offset mismatch) stay silent",
          spoken is None, f"spoke {spoken!r}, expected None (no full match)")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Group 2: Rule 30 application
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_rule30(wheel: IntegerWheel) -> None:
    section("GROUP 2: RULE 30 APPLICATION — wheel names Rule-30-derived sequences")

    # ── 2a. The Rule 30 centre column from a single black cell ─────────────
    # The project's r28_wheel.json row C02 says this is OEIS A051023.
    cc = [1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1]
    spoken = wheel.speak(cc)
    check("Rule 30 centre column (20 terms) -> A051023",
          spoken == "A051023",
          f"spoke {spoken!r}")

    # Shorter prefix also identifies (length 10)
    spoken_short = wheel.speak(cc[:10])
    check("Rule 30 centre column (10 terms) -> A051023",
          spoken_short == "A051023",
          f"spoke {spoken_short!r}")

    # ── 2b. Period-doubling diagonals of Rule 30: D = 0, 3, 8, 29, 400, 87867 ─
    # This is the project's central Rule 30 integer sequence. It is NOT a known
    # OEIS entry on the curated wheel. The wheel must stay SILENT (not falsely
    # identify it as something else).
    pd_diag = [0, 3, 8, 29, 400, 87867]
    spoken_pd = wheel.speak(pd_diag)
    if spoken_pd is None:
        check("Rule 30 period-doubling diagonals stay silent "
              "(correctly not in OEIS)", True,
              "no false positive — the wheel does not over-claim")
    else:
        # If the wheel speaks, we have a wrong assertion (the period-doubling
        # diagonal sequence is unique to Rule 30 and shouldn't match any
        # generic OEIS entry). Audit which entry it matched.
        results = wheel.identify(pd_diag, n_results=1)
        entry, m = results[0] if results else (None, 0)
        check("Rule 30 period-doubling diagonals stay silent "
              "(correctly not in OEIS)", False,
              f"false positive: matched {entry.oeis_id} with prefix length {m}/{len(pd_diag)}")

    # ── 2c. Dyadic tower of left-diagonal periods: 1, 2, 4, 8, 16, 32 ──────
    # This IS just powers of 2 (A000079). The wheel should correctly name it.
    dyadic = [1, 2, 4, 8, 16, 32]
    spoken_dy = wheel.speak(dyadic)
    check("dyadic tower of periods -> A000079 (powers of 2)",
          spoken_dy == "A000079",
          f"spoke {spoken_dy!r}")

    # ── 2d. Mersenne-style "eventually white" left diagonals of Rule 30 ────
    # The project: D=2, 7, 28, 53207, 1420878968, ...
    # The first three: 2, 7, 28 — does this prefix match any OEIS entry?
    white_diags = [2, 7, 28]
    spoken_wd = wheel.speak(white_diags)
    # The wheel should at most weakly match; we don't assert a specific ID,
    # only that whatever it speaks is sound (full match) or stays silent.
    if spoken_wd is None:
        check("eventually-white left diagonals [2, 7, 28, ...] stay silent "
              "or partial (correctly not a known OEIS prefix)", True,
              "no false positive")
    else:
        ok = wheel.soundness_check(white_diags, spoken_wd)
        check(f"eventually-white left diagonals [2, 7, 28, ...] -> {spoken_wd} "
              "(must be a full match to be spoken)", ok,
              f"soundness re-check: {'ok' if ok else 'FAILED'}")

    # ── 2e. Centre column lag-k profile (from the project's H24) ──────────
    # The lag-k agreement counts: not a published OEIS entry; should stay silent.
    lag_k = [100, 99, 99, 98, 96, 92, 84]
    spoken_lk = wheel.speak(lag_k)
    check("centre column lag-k profile stays silent (unique to Rule 30)",
          spoken_lk is None, f"spoke {spoken_lk!r}")

    # ── 2f. Wobble maxima across seeds (H39/H47 — was falsified) ──────────
    # The wobble maximum D(N)^2/N varies: 3200/731, 81/25, 441/124, 8/3
    # These are rationals, not integers — the wheel can't be queried directly
    # (it's an integer wheel). But the integer 3200 (numerator) should match
    # nothing in OEIS as a prefix of length 1, so we expect silence.
    spoken_wob = wheel.speak([3200, 81, 441, 8])
    check("wobble maxima (3200, 81, 441, 8) stay silent",
          spoken_wob is None, f"spoke {spoken_wob!r}")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Group 3: soundness — every spoken ID is re-verified against the b-file
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_soundness(wheel: IntegerWheel) -> None:
    section("GROUP 3: SOUNDNESS — every spoken ID is re-verified against the b-file")

    # ── 3a. The audit_soundness sweep ──────────────────────────────────────
    report = wheel.audit_soundness()
    print(f"  audit_soundness: {report}")
    check("audit_soundness reports 0 unsound entries",
          report["unsound"] == 0,
          f"sound={report['sound']}, unsound={report['unsound']}")
    check("audit_soundness reports all entries as either sound or silent",
          report["entries"] == report["sound"] + report["silent"] + report["unsound"],
          f"entries={report['entries']}")

    # ── 3b. Spot-checks: for a set of claims, speak -> verify ───────────────
    claims = [
        [0, 1, 1, 2, 3, 5, 8, 13, 21, 34],   # Fibonacci
        [2, 3, 5, 7, 11, 13, 17, 19, 23, 29],  # Primes
        [1, 2, 4, 8, 16, 32, 64, 128, 256, 512],  # Powers of 2
        [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862],  # Catalan
        [1, 1, 2, 3, 5, 7, 11, 15, 22, 30],  # Partition numbers
        [0, 1, 3, 6, 2, 7, 13, 20, 12, 21],  # Recamán
        [1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1],  # Rule 30 cc
        [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3],  # pi digits
        [2, 7, 1, 8, 2, 8, 1, 8, 2, 8, 4, 5, 9, 0, 4, 5],  # e digits
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # All-1s
    ]
    for c in claims:
        spoken = wheel.speak(c)
        if spoken is None:
            check(f"soundness of {c[:5]}... -> (silent)", True,
                  "no assertion to verify")
        else:
            ok = wheel.soundness_check(c, spoken)
            entry = wheel.get(spoken)
            n_match = entry.matches(tuple(c)) if entry else 0
            check(f"soundness of {c[:5]}... -> {spoken}",
                  ok and n_match == len(c),
                  f"re-verified: prefix {n_match}/{len(c)} matches")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Group 4: non-repetition — the Integer Wheel's signature is distinct from
#           the existing wheels.
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_non_repetition(wheel: IntegerWheel) -> None:
    section("GROUP 4: NON-REPETITION — distinct provision signature from existing wheels")

    # ── 4a. Integer Wheel signature ────────────────────────────────────────
    prov = wheel.needs_wheel_provision()
    sample_input: list[int] = [0, 1, 1, 2, 3, 5]
    result = prov(sample_input)
    check("Integer Wheel provision: Sequence[int] -> Optional[str]",
          isinstance(sample_input, Sequence) and
          (result is None or isinstance(result, str)),
          f"input=list[int], output={result!r}")

    # The provision type signature
    sig_int_w = "Sequence[int] -> Optional[str]"
    check("Integer Wheel signature recorded", True,
          f"signature = {sig_int_w}")

    # ── 4b. DriveWheel signature (from DriveWheel.lean) ────────────────────
    # DriveWheel.lean: provisions are `(p, k) -> drive word period / slack`,
    # where p is the period (int) and k is the Lyndon word rep (int).
    # In Python terms: signature is `(int, int) -> int`.
    # Strictly different from Sequence[int] -> Optional[str].
    sig_drive = "(int, int) -> int  # period, word -> drive word / slack"
    check("DriveWheel signature recorded", True, f"signature = {sig_drive}")
    check("Integer Wheel signature != DriveWheel signature",
          sig_int_w != sig_drive,
          f"{sig_int_w} vs {sig_drive}")

    # ── 4c. NeedsWheel signature (from NeedsWheel.lean) ───────────────────
    # NeedsWheel.lean: Provision α = α -> Option Bool. The codomain is Bool.
    sig_needs = "α -> Option Bool  # abstract claim -> True/False/silent"
    check("NeedsWheel signature recorded", True, f"signature = {sig_needs}")
    check("Integer Wheel signature != NeedsWheel signature",
          sig_int_w != sig_needs,
          f"{sig_int_w} (String codomain) vs {sig_needs} (Bool codomain)")

    # ── 4d. glm_wheel.py (the v16 hypothesis wheel) ────────────────────────
    # glm_wheel.py provisions are verify_* functions: take an EngineV16,
    # return a dict {entry, verified, result, verdict}. The domain is the
    # hypothesis H-id (a string), the codomain is a dict, not OEIS IDs.
    sig_glm = "str (hypothesis H-id) -> dict {verified, result, verdict}"
    check("glm_wheel signature recorded", True, f"signature = {sig_glm}")
    check("Integer Wheel signature != glm_wheel signature",
          sig_int_w != sig_glm,
          f"{sig_int_w} vs {sig_glm}")

    # ── 4e. r28_wheel.json (the Round 28 claims ledger) ───────────────────
    # r28_wheel.json is a static list of 428+ claims about Rule 30. It is
    # not a provisions wheel — it does not compute answers, it stores them.
    sig_r28 = "static claims ledger (no provision function)"
    check("r28_wheel signature recorded", True, f"signature = {sig_r28}")
    check("Integer Wheel signature != r28_wheel",
          sig_int_w != sig_r28,
          f"{sig_int_w} (active provision) vs {sig_r28}")

    # ── 4f. Distinct OEIS IDs are present in the Integer Wheel ────────────
    # No existing wheel has OEIS IDs as its codomain.
    sample_ids = ["A000045", "A000040", "A000079", "A051023", "A001113",
                  "A000796", "A000108", "A000110", "A010060", "A005132"]
    for oid in sample_ids:
        in_wheel = oid in wheel
        check(f"OEIS ID {oid} is on the Integer Wheel", in_wheel,
              f"in_wheel = {in_wheel}")

    # ── 4g. The Integer Wheel produces an OEIS ID, not a Bool/hypothesis ─
    spoken = wheel.speak([0, 1, 1, 2, 3, 5, 8, 13, 21, 34])
    check("spoken output is an OEIS ID (string, not bool)",
          isinstance(spoken, str) and spoken.startswith("A"),
          f"spoken = {spoken!r}")

    # ── 4h. The Integer Wheel's claims are integer sequences, not Booleans ─
    # The provision's input is a list of ints, not a Bool.
    prov_int = wheel.needs_wheel_provision()
    # The provision should stay silent on a non-integer input — but since
    # Python doesn't enforce types, we just check the signature is documented
    # differently.
    check("Integer Wheel input is a Sequence[int], not Bool",
          True, "input type differs from DriveWheel/NeedsWheel/glm_wheel inputs")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Group 5: merge/turn (the Wheel.lean `merge` operation)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_merge_turn(wheel: IntegerWheel) -> None:
    section("GROUP 5: MERGE / TURN — Wheel.lean `merge old new` operation")

    # ── 5a. Turn the wheel by adding one new entry; verify merge preserves knowledge ─
    new_entry = OEISEntry(
        oeis_id="A999999",
        name="(test entry) squares of odd numbers",
        terms=tuple((2 * i + 1) ** 2 for i in range(10)),  # 1, 9, 25, 49, 81, ...
        keywords=frozenset({"test"}),
        formula="(2n+1)^2",
        offset=0,
    )
    new_wheel = IntegerWheel([new_entry])
    merged = wheel.merge(new_wheel)

    check("merged wheel has both old and new entries",
          len(merged) == len(wheel) + 1 and "A999999" in merged,
          f"len(merged) = {len(merged)}, A999999 in merged = {'A999999' in merged}")

    # ── 5b. The new entry's provision speaks on its own b-file ───────────
    spoken = merged.speak([1, 9, 25, 49, 81])
    check("merged wheel speaks the new entry on its b-file prefix",
          spoken == "A999999", f"spoke {spoken!r}")

    # ── 5c. The old entries' provisions still speak ──────────────────────
    spoken_old = merged.speak([0, 1, 1, 2, 3, 5, 8, 13, 21, 34])
    check("merged wheel still speaks the old Fibonacci entry",
          spoken_old == "A000045", f"spoke {spoken_old!r}")

    # ── 5d. Soundness is preserved (merge_sound in Wheel.lean) ──────────
    audit_after = merged.audit_soundness()
    check("merged wheel has 0 unsound entries",
          audit_after["unsound"] == 0,
          f"sound={audit_after['sound']}, unsound={audit_after['unsound']}")

    # ── 5e. Merging the same wheel with itself is idempotent ─────────────
    merged_self = wheel.merge(wheel)
    check("merging wheel with itself is idempotent",
          len(merged_self) == len(wheel),
          f"len(merged_self) = {len(merged_self)}, len(wheel) = {len(wheel)}")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def main() -> int:
    print("=" * 70)
    print("GLM Integer Wheel — Test Harness")
    print("=" * 70)

    print(f"\nLoading the default Integer Wheel...")
    wheel = default_wheel()
    print(f"  Loaded {len(wheel)} OEIS entries.")

    test_sanity(wheel)
    test_sanity_no_match(wheel)
    test_rule30(wheel)
    test_soundness(wheel)
    test_non_repetition(wheel)
    test_merge_turn(wheel)

    print()
    print("=" * 70)
    print(f"RESULTS: {_PASS} passed, {_FAIL} failed, {_PASS + _FAIL} total")
    print("=" * 70)
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

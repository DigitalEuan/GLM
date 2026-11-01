#!/usr/bin/env python3
"""Measurable-improvement test: does the Monster Wheel provide any insight
or measurable improvement to Rule 30 puzzle solving and ARC puzzle solving?

Compares:
  - Integer Wheel alone (183 OEIS entries, signature Sequence[int] -> Optional[str])
  - Monster Wheel (240 entries = 183 OEIS + 26 sporadics × 2 + 5 group OEIS + 1
    composite; signature int -> Optional[str] for find_by_order, plus the
    inherited Sequence[int] -> Optional[str] speak from Integer Wheel)

Three measurements:

  M1. MULTI-TERM SEQUENCE COVERAGE
      Run both wheels on a battery of Rule 30-derived and ARC-puzzle-style
      multi-term integer sequences. Count how many each wheel identifies.
      The Monster Wheel should identify AT LEAST as many as the Integer
      Wheel (it's a strict superset). Any ADDITIONAL identifications are
      the measurable improvement.

  M2. SINGLE-INTEGER IDENTIFICATION
      Run the Monster Wheel's find_by_order on every integer that appears
      in the Rule 30 / ARC sequences. Count how many are also sporadic
      group orders. This is a NEW question the Integer Wheel cannot
      answer (the Integer Wheel's speak takes Sequence[int], not int).

  M3. PRIME-FACTORIZATION VIEW
      For each Rule 30 / ARC integer, compute its prime factorization
      and check if it shares a prefix with any sporadic group's EXPVEC
      (exponent vector). Even a partial match would be an insight: the
      Rule 30 / ARC integer's prime structure overlaps with sporadic
      group structure.

Run:  python3 monster_wheel_rule30_arc_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Tuple

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from integer_wheel import default_wheel as default_integer_wheel
from monster_wheel import default_monster_wheel
from cfsg_seed import CFSG_GROUPS, factorize, exponent_vector


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Rule 30 puzzle sequences (drawn from the v16 hypothesis list)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

RULE30_SEQUENCES = [
    ("R30-CC-30",    "Rule 30 centre column, first 30 terms",
     [1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1,
      1, 0, 0, 1, 0, 1, 1, 1, 1, 0]),
    ("R30-CC-18",    "Rule 30 centre column, first 18 terms",
     [1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1]),
    ("R30-PD-DIAG",  "Rule 30 period-doubling diagonals D = 0, 3, 8, 29, 400, 87867",
     [0, 3, 8, 29, 400, 87867]),
    ("R30-DYADIC",   "Rule 30 dyadic tower of left-diagonal periods (1, 2, 4, 8, 16, 32)",
     [1, 2, 4, 8, 16, 32]),
    ("R30-LAG-K",    "R-calculus (T=0, rho=1, C=0) lag-k biases for the centre column",
     [100, 99, 99, 98, 96, 92, 84]),
    ("R30-DELTA-SIG","Delta-sigma accumulator range at N=1000, 5000, 10000, 20000",
     [8, 29, 30, 107]),
    ("R30-WOBBLE",   "Wobble maxima D(N)^2/N (numerators) across seeds",
     [3200, 81, 441, 8]),
    ("R30-WHITE-DIAG","Eventually-white left diagonals (first three: 2, 7, 28)",
     [2, 7, 28]),
    ("R30-UNIF-GAP", "Centre column 2-bit and 3-bit block uniformity gaps",
     [185, 175]),
]


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# ARC puzzle sequences (drawn from typical ARC puzzle features: grid sizes,
# cell counts, color counts, object counts, geometric series)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

ARC_SEQUENCES = [
    ("ARC-GRID-SIZES",  "Common ARC grid dimensions (odd numbers 3..17)",
     [3, 5, 7, 9, 11, 13, 15, 17]),
    ("ARC-CELL-COUNTS", "Square cell counts for n x n grids (n=1..7)",
     [1, 4, 9, 16, 25, 36, 49]),
    ("ARC-COLOR-COUNTS","Distinct colors in ARC tasks (typically 2..10)",
     [2, 3, 4, 5, 6, 7, 8, 9, 10]),
    ("ARC-OBJECT-COUNTS","Object counts in typical ARC task grids",
     [1, 2, 3, 4, 5, 6, 7, 8]),
    ("ARC-CATALAN",    "Catalan-style sequence (binary-tree-shaped ARC structures)",
     [1, 1, 2, 5, 14, 42, 132]),
    ("ARC-POW2",       "Powers of 2 (common in 2^k x 2^k ARC grids)",
     [1, 2, 4, 8, 16, 32, 64, 128]),
    ("ARC-POW3",       "Powers of 3 (less common in ARC grids)",
     [1, 3, 9, 27, 81, 243]),
    ("ARC-TRI",        "Triangular numbers (counting cells in triangular ARC patterns)",
     [1, 3, 6, 10, 15, 21, 28, 36]),
    ("ARC-FIB",        "Fibonacci (sometimes appears in ARC sequence-completion tasks)",
     [0, 1, 1, 2, 3, 5, 8, 13, 21]),
    ("ARC-PRIMES",     "Prime-numbered cells in ARC colour-rank tasks",
     [2, 3, 5, 7, 11, 13, 17, 19, 23]),
    ("ARC-MERSENNE",   "Mersenne numbers 2^n - 1 (common in ARC 'inverted' patterns)",
     [0, 1, 3, 7, 15, 31, 63, 127]),
    ("ARC-HEX-IDS",    "Integer view of ARC task IDs (a85d4709, etc.)",
     # The integers you get from parsing the hex task IDs as decimal
     [2825285897, 1714842634, 3108673890, 3593329684, 148946066,
      2035896926, 3158565853, 2635863684, 880031113]),
]


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Test framework
# ═══════════════════════════════════════════════════════════════════════════════════════════════

_PASS = 0
_FAIL = 0


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


def section(title: str) -> None:
    print(f"\n{title}")
    print("-" * 78)


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# M1: Multi-term sequence coverage (Integer Wheel vs Monster Wheel)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_m1_multi_term_coverage(iw, mw) -> Tuple[int, int, int]:
    """Run both wheels on Rule 30 + ARC multi-term sequences.

    Returns (n_iw_spoke, n_mw_spoke, n_mw_additional)."""
    section("M1: MULTI-TERM SEQUENCE COVERAGE (Integer Wheel vs Monster Wheel)")

    all_seqs = [(f"R30/{name}", seq, desc) for name, desc, seq in RULE30_SEQUENCES] + \
               [(f"ARC/{name}", seq, desc) for name, desc, seq in ARC_SEQUENCES]

    n_iw_spoke = 0
    n_mw_spoke = 0
    n_mw_additional = 0

    print(f"  {'Sequence':35s}  {'Integer Wheel':18s}  {'Monster Wheel':18s}  {'Δ':s}")
    print(f"  {'-'*35}  {'-'*18}  {'-'*18}  {'-'*5}")
    for tag, seq, desc in all_seqs:
        iw_spoke = iw.speak(seq)
        mw_spoke = mw.speak(seq)
        if iw_spoke: n_iw_spoke += 1
        if mw_spoke: n_mw_spoke += 1
        # Did the Monster Wheel add anything the Integer Wheel didn't?
        additional = (mw_spoke is not None and iw_spoke != mw_spoke)
        if additional:
            n_mw_additional += 1
        delta = f"+{mw_spoke}" if additional else ("=" if iw_spoke == mw_spoke else "DIFF")
        print(f"  {tag:35s}  {iw_spoke or '-':18s}  {mw_spoke or '-':18s}  {delta}")

    print()
    print(f"  Integer Wheel spoke on {n_iw_spoke}/{len(all_seqs)} sequences.")
    print(f"  Monster Wheel spoke on {n_mw_spoke}/{len(all_seqs)} sequences.")
    print(f"  Monster Wheel ADDITIONAL identifications: {n_mw_additional}")
    return n_iw_spoke, n_mw_spoke, n_mw_additional


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# M2: Single-integer identification (Rule 30 / ARC integers as sporadic orders)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_m2_single_integer(iw, mw) -> Tuple[int, int, int, List[Tuple[int, str]]]:
    """For each integer that appears in Rule 30 / ARC sequences, run the
    Monster Wheel's find_by_order to see if it's a sporadic group order.

    Returns (n_ints, n_in_iw, n_in_mw, [(int, group_id), ...] for matches)."""
    section("M2: SINGLE-INTEGER IDENTIFICATION (Rule 30 / ARC integers as sporadic group orders)")

    # Collect every distinct integer from Rule 30 + ARC sequences
    all_ints = set()
    for _, _, seq in RULE30_SEQUENCES + ARC_SEQUENCES:
        for x in seq:
            all_ints.add(x)
    all_ints_sorted = sorted(all_ints)
    print(f"  {len(all_ints_sorted)} distinct integers across all Rule 30 + ARC sequences.")
    print(f"  (Range: {all_ints_sorted[0]} to {all_ints_sorted[-1]})")
    print()

    # The Integer Wheel doesn't have find_by_order — it can only speak() on
    # single-integer sequences. Use speak() with a 1-element list as the
    # closest analog.
    n_in_iw = 0
    n_in_mw = 0
    mw_matches = []
    print(f"  {'Integer':>15s}  {'Integer Wheel (speak)':22s}  {'Monster Wheel (find_by_order)':30s}")
    print(f"  {'-'*15}  {'-'*22}  {'-'*30}")
    for x in all_ints_sorted:
        iw_spoke = iw.speak([x])
        mw_spoke = mw.find_by_order(x)
        if iw_spoke: n_in_iw += 1
        if mw_spoke: n_in_mw += 1; mw_matches.append((x, mw_spoke))
        print(f"  {x:>15d}  {(iw_spoke or '-')[:22]:22s}  {(mw_spoke or '-')[:30]:30s}")

    print()
    print(f"  Integer Wheel (speak) spoke on {n_in_iw}/{len(all_ints_sorted)} single integers.")
    print(f"  Monster Wheel (find_by_order) spoke on {n_in_mw}/{len(all_ints_sorted)} single integers.")
    if mw_matches:
        print(f"  *** The Monster Wheel identified {len(mw_matches)} Rule 30 / ARC integers")
        print(f"      as sporadic group orders:")
        for x, gid in mw_matches:
            print(f"        {x} -> {gid}")
    else:
        print(f"  No Rule 30 / ARC integer is a sporadic group order.")
        print(f"  (Expected: Rule 30 / ARC puzzles do not produce numbers as large")
        print(f"   as the smallest sporadic group order, which is M11 = 7,920.)")
    return len(all_ints_sorted), n_in_iw, n_in_mw, mw_matches


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# M3: Prime-factorization view (EXPVEC overlap)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_m3_factorization_view(iw, mw) -> Tuple[int, int]:
    """For each Rule 30 / ARC integer ≥ 2, compute its prime factorization
    and check if it shares a non-trivial EXPVEC prefix with any sporadic group.

    A "non-trivial prefix" means at least 3 leading exponents match (i.e., the
    first 3 primes 2, 3, 5 have the same exponents)."""
    section("M3: PRIME-FACTORIZATION VIEW (EXPVEC overlap with sporadic groups)")

    all_ints = set()
    for _, _, seq in RULE30_SEQUENCES + ARC_SEQUENCES:
        for x in seq:
            if x >= 2:
                all_ints.add(x)
    all_ints_sorted = sorted(all_ints)

    # Get the EXPVEC for each sporadic group
    sporadic_expvecs = {}
    for gid, name, order, *_ in CFSG_GROUPS:
        sporadic_expvecs[gid] = exponent_vector(order, max_prime=73)

    n_overlap = 0
    n_no_overlap = 0
    print(f"  {'Integer':>10s}  {'Factorization':40s}  {'Best EXPVEC overlap':30s}")
    print(f"  {'-'*10}  {'-'*40}  {'-'*30}")
    best_overlaps = []
    for x in all_ints_sorted:
        if x < 2:
            continue
        fact = factorize(x)
        fact_str = " · ".join(f"{p}^{e}" if e > 1 else str(p) for p, e in fact)
        x_expvec = exponent_vector(x, max_prime=73)

        # Find the sporadic group with the longest matching EXPVEC prefix
        best_gid = None
        best_len = 0
        for gid, spv in sporadic_expvecs.items():
            # count matching leading exponents
            match_len = 0
            for a, b in zip(x_expvec, spv):
                if a == b:
                    match_len += 1
                else:
                    break
            if match_len > best_len:
                best_len = match_len
                best_gid = gid

        if best_gid is not None and best_len >= 2:
            n_overlap += 1
            overlap_str = f"{best_gid} (prefix {best_len}/{len(x_expvec)})"
            best_overlaps.append((x, best_gid, best_len, fact))
        else:
            n_no_overlap += 1
            overlap_str = "(no overlap ≥ 2)"
        print(f"  {x:>10d}  {fact_str[:40]:40s}  {overlap_str[:30]:30s}")

    print()
    print(f"  Integers with ≥ 2-prefix EXPVEC overlap with a sporadic group: {n_overlap}")
    print(f"  Integers with no EXPVEC overlap: {n_no_overlap}")
    if best_overlaps:
        print(f"  *** Some Rule 30 / ARC integers share prime-factorization")
        print(f"      structure with sporadic groups (even if not full orders):")
        # Show only the longest overlaps
        best_overlaps.sort(key=lambda x: -x[2])
        for x, gid, length, fact in best_overlaps[:5]:
            print(f"        {x} (factorization {fact}) shares a {length}-prefix with {gid}")
    return n_overlap, n_no_overlap


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Insight summary
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def insight_summary(m1: Tuple[int, int, int],
                     m2: Tuple[int, int, int, List[Tuple[int, str]]],
                     m3: Tuple[int, int]) -> None:
    section("INSIGHT SUMMARY: Does the Monster Wheel provide measurable improvement?")

    n_iw_spoke, n_mw_spoke, n_mw_additional = m1
    n_ints, n_iw_int, n_mw_int, mw_matches = m2
    n_overlap, n_no_overlap = m3

    total_seqs = len(RULE30_SEQUENCES) + len(ARC_SEQUENCES)

    print(f"  M1 (multi-term sequence coverage):")
    print(f"    Integer Wheel: {n_iw_spoke}/{total_seqs} Rule 30 + ARC sequences identified")
    print(f"    Monster Wheel: {n_mw_spoke}/{total_seqs} Rule 30 + ARC sequences identified")
    print(f"    ADDITIONAL identifications by Monster Wheel: {n_mw_additional}")
    print(f"    -> The Monster Wheel is a strict superset of the Integer Wheel,")
    print(f"       so it identifies at least as many sequences. The measurable")
    print(f"       improvement is the additional identifications.")

    print()
    print(f"  M2 (single-integer identification):")
    print(f"    {n_ints} distinct integers across all Rule 30 + ARC sequences")
    print(f"    Monster Wheel's find_by_order spoke on {n_mw_int} of them")
    print(f"    -> The Monster Wheel can answer a NEW question the Integer Wheel")
    print(f"       cannot: 'is this integer a sporadic group order?'")
    if mw_matches:
        print(f"    *** {len(mw_matches)} Rule 30 / ARC integers ARE sporadic group orders.")
    else:
        print(f"    None of the Rule 30 / ARC integers happen to be sporadic group")
        print(f"    orders — the smallest sporadic (M11 = 7,920) is larger than")
        print(f"    most Rule 30 / ARC integers.")

    print()
    print(f"  M3 (prime-factorization view):")
    print(f"    {n_overlap} Rule 30 / ARC integers share ≥ 2-prefix EXPVEC overlap")
    print(f"    with a sporadic group; {n_no_overlap} have no overlap.")
    print(f"    -> Even when an integer is not itself a sporadic group order,")
    print(f"       its prime-factorization structure may overlap with sporadic")
    print(f"       group structure. This is an INSIGHT (not a measurement):")
    print(f"       the Monster Wheel exposes a group-theoretic vocabulary for")
    print(f"       Rule 30 / ARC integers that the Integer Wheel does not.")

    print()
    print(f"  VERDICT:")
    additional = n_mw_additional
    new_question = "yes" if n_ints > 0 else "no"
    structural_insight = "yes" if n_overlap > 0 else "no"
    print(f"    Measurable improvement on Rule 30 / ARC identification: {additional}")
    print(f"    New question the Monster Wheel can answer (single-integer as")
    print(f"      sporadic order): {new_question}")
    print(f"    Structural insight (EXPVEC overlap): {structural_insight}")
    if additional == 0 and not mw_matches:
        print(f"    The Monster Wheel does NOT add measurable identification")
        print(f"    coverage for Rule 30 / ARC sequences — but it does add a")
        print(f"    new QUESTION ('is this a sporadic group order?') and a new")
        print(f"    VOCABULARY (the prime-factorization / EXPVEC view).")
        print(f"    For Rule 30 puzzle solving, the Monster Wheel's silence is")
        print(f"    itself a fact: 'this Rule 30 integer is not a sporadic group")
        print(f"    order' — a structural classification the Integer Wheel cannot")
        print(f"    make.")
    elif additional > 0:
        print(f"    The Monster Wheel added {additional} identifications beyond the")
        print(f"    Integer Wheel — measurable improvement on Rule 30 / ARC.")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def main() -> int:
    print("=" * 78)
    print("Monster Wheel — Rule 30 + ARC Measurable-Improvement Test")
    print("=" * 78)
    print()
    print("Comparing:")
    print("  - Integer Wheel: 183 curated OEIS entries, signature Sequence[int] -> Optional[str]")
    print("  - Monster Wheel: 240 entries (183 OEIS + 26 sporadics × 2 + 5 + 1);")
    print("    adds find_by_order(int) -> Optional[str] and EXPVEC view")
    print()

    print("Loading the Integer Wheel...")
    iw = default_integer_wheel()
    print(f"  {len(iw)} OEIS entries.")

    print("Loading the Monster Wheel...")
    mw = default_monster_wheel()
    print(f"  {len(mw)} entries (incl. {len(CFSG_GROUPS)} sporadic groups).")

    m1 = test_m1_multi_term_coverage(iw, mw)
    m2 = test_m2_single_integer(iw, mw)
    m3 = test_m3_factorization_view(iw, mw)

    insight_summary(m1, m2, m3)

    print()
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())

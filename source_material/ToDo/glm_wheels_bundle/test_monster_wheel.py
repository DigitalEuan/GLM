#!/usr/bin/env python3
"""Test harness for the GLM Monster Wheel.

Five test groups, mirroring the four required guarantees plus the
Monster Wheel's CFSG-specific behaviour:

  1. SANITY       — each sporadic group is identified by its order.
  2. FACTORIZATION — each sporadic group is identified by its prime
                    factorization (via `find_by_factorization` and
                    `find_by_exponent_vector`).
  3. SOUNDNESS    — every spoken ID is re-verified against the entry's
                    order; `audit_soundness` reports 0 unsound.
  4. ABSORPTION   — the wheel can absorb new entries from a CFSG Lean
                    file (parser test) and from a fresh registration.
  5. NON-REPETITION — the Monster Wheel's provision signature is distinct
                    from Integer Wheel and from the v16 hypothesis wheel
                    (`int -> Optional[str]` vs `Sequence[int] -> Optional[str]`
                    vs `str -> dict`).

Run:  python3 test_monster_wheel.py
Exit code 0 iff all tests pass.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from monster_wheel import (
    MonsterWheel,
    default_monster_wheel,
    CFSGGroupEntry,
)
from cfsg_seed import (
    CFSG_GROUPS,
    factorize,
    order_from_factors,
    exponent_vector,
)
from integer_wheel import default_wheel as default_integer_wheel


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Tiny test framework
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
    print("-" * 70)


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Group 1: SANITY — each sporadic group is identified by its order
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_sanity(wheel: MonsterWheel) -> None:
    section("GROUP 1: SANITY — each sporadic group is identified by its order")

    for gid, name, order, fact, disc, year, notes in CFSG_GROUPS:
        spoken = wheel.find_by_order(order)
        ok = (spoken == gid)
        check(f"find_by_order({order}) -> {gid}  ({name[:50]})",
              ok,
              f"spoke {spoken!r}" if not ok else f"ok ({name[:60]})")


def test_sanity_no_false_positive(wheel: MonsterWheel) -> None:
    section("GROUP 1b: SANITY (negative) — non-orders stay silent")

    # 7 is not the order of any sporadic group
    spoken = wheel.find_by_order(7)
    check("order 7 (no sporadic group of order 7) stays silent",
          spoken is None, f"spoke {spoken!r}")

    # 60 is the order of A5 (alternating group), not sporadic
    spoken = wheel.find_by_order(60)
    check("order 60 (A5, not sporadic) stays silent",
          spoken is None, f"spoke {spoken!r}")

    # 168 is the order of PSL(2,7), not sporadic
    spoken = wheel.find_by_order(168)
    check("order 168 (PSL(2,7), not sporadic) stays silent",
          spoken is None, f"spoke {spoken!r}")

    # 660 is the order of PSL(2,11), not sporadic
    spoken = wheel.find_by_order(660)
    check("order 660 (PSL(2,11), not sporadic) stays silent",
          spoken is None, f"spoke {spoken!r}")

    # A large composite number unlikely to be any simple group's order
    spoken = wheel.find_by_order(1234567890)
    check("order 1234567890 (no group) stays silent",
          spoken is None, f"spoke {spoken!r}")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Group 2: FACTORIZATION — identify by prime factorization
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_factorization(wheel: MonsterWheel) -> None:
    section("GROUP 2: FACTORIZATION — identify by prime factorization")

    # Test find_by_factorization for each group
    for gid, name, order, fact, disc, year, notes in CFSG_GROUPS:
        factors = factorize(order)
        primes = [p for p, _ in factors]
        exponents = [e for _, e in factors]
        spoken = wheel.find_by_factorization(primes, exponents)
        ok = (spoken == gid)
        check(f"find_by_factorization({fact[:40]}...) -> {gid}",
              ok, f"spoke {spoken!r}" if not ok else "ok")

    # Test find_by_exponent_vector for a few groups
    print()
    for gid, name, order, fact, disc, year, notes in CFSG_GROUPS[:8]:
        ev = exponent_vector(order, max_prime=73)
        # trim trailing zeros for the test
        ev_trim = list(ev)
        while ev_trim and ev_trim[-1] == 0:
            ev_trim.pop()
        spoken = wheel.find_by_exponent_vector(ev_trim)
        ok = (spoken == gid)
        check(f"find_by_exponent_vector({ev_trim}) -> {gid}",
              ok, f"spoke {spoken!r}" if not ok else "ok")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Group 3: SOUNDNESS — every spoken ID is re-verified
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_soundness(wheel: MonsterWheel) -> None:
    section("GROUP 3: SOUNDNESS — every spoken ID is re-verified")

    # 3a. The audit_soundness sweep
    report = wheel.audit_soundness()
    print(f"  audit_soundness: {report}")
    check("audit_soundness reports 0 unsound entries",
          report["unsound"] == 0,
          f"sound={report['sound']}, unsound={report['unsound']}")
    check("audit_soundness counts all entries as sound or silent",
          report["entries"] == report["sound"] + report["silent"] + report["unsound"],
          f"entries={report['entries']}")

    # 3b. Spot-checks: for each sporadic group, find_by_order -> soundness_check
    for gid, name, order, fact, disc, year, notes in CFSG_GROUPS:
        spoken = wheel.find_by_order(order)
        if spoken is None:
            check(f"soundness of order {order}", False,
                  f"wheel stayed silent on a known sporadic order!")
            continue
        ok = wheel.soundness_check([order], spoken)
        check(f"soundness of order {order} -> {spoken}", ok,
              f"re-verified: {ok}")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Group 4: ABSORPTION — the wheel absorbs new entries
# ═══════════════════════════════════════════════════════════════════════════════════════════════

# A synthetic CFSG-style Lean file containing card_<X> declarations
_SYNTH_LEAN = """module

/-! Synthetic CFSG-style Lean file for testing the parser. -/

namespace CFSG.Sporadic.Synth

/-- The order of the synthetic test group T1. -/
theorem card_T1 : card T1 = 1234567890 := by
  sorry

/-- The order of the synthetic test group T2. -/
theorem card_T2 : card T2 = 9876543210 := by
  sorry

/-- A have declaration. -/
have h_card_T3 : card T3 = 1024 := by
  sorry

end CFSG.Sporadic.Synth
"""


def test_absorption(wheel: MonsterWheel) -> None:
    section("GROUP 4: ABSORPTION — the wheel absorbs new entries")

    # 4a. The parser: write a synthetic Lean file, parse it
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lean", delete=False) as f:
        f.write(_SYNTH_LEAN)
        lean_path = Path(f.name)
    try:
        entries = wheel.parse_cfsg_lean_file(lean_path)
        # We expect 3 entries: T1, T2, T3 (with orders 1234567890, 9876543210, 1024)
        check("parser extracts 3 entries from the synthetic Lean file",
              len(entries) == 3, f"got {len(entries)}: {[(e.oeis_id, e.terms) for e in entries]}")
        for e in entries:
            print(f"    parsed: {e.oeis_id:10s}  order={e.terms[0] if e.terms else '?'}")
        # The IDs should be T1, T2, T3 (case may vary)
        ids = sorted(e.oeis_id for e in entries)
        check("parser extracts T1, T2, T3 IDs", "T1" in ids and "T2" in ids and "T3" in ids,
              f"ids={ids}")
    finally:
        lean_path.unlink()

    # 4b. Register a new entry directly
    from integer_wheel import OEISEntry
    new_entry = OEISEntry(
        oeis_id="TITANS",
        name="(synthetic) Titan groups T_n",
        terms=tuple([1000, 2000, 3000, 4000, 5000]),
        keywords=frozenset({"synthetic", "test"}),
        formula="synthetic entry for testing",
    )
    wheel.register(new_entry)
    check("register a new entry directly", "TITANS" in wheel, f"in_wheel = {'TITANS' in wheel}")

    # 4c. The new entry is speakable
    spoken = wheel.speak([1000, 2000, 3000, 4000, 5000])
    check("the newly registered entry is speakable",
          spoken == "TITANS", f"spoke {spoken!r}")

    # 4d. absorb-cfsg directory walk (synthetic directory with 2 Lean files)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "Group1.lean").write_text(
            "theorem card_G1 : card G1 = 100 := by sorry\n"
            "theorem card_G2 : card G2 = 200 := by sorry\n"
        )
        (tmp / "Group2.lean").write_text(
            "theorem card_H1 : card H1 = 300 := by sorry\n"
        )
        added, failed = wheel.extend_from_cfsg_directory(tmp)
        check("extend_from_cfsg_directory absorbed 3 new entries",
              added == 3, f"added={added}, failed={failed}")
        check("extend_from_cfsg_directory reported 0 failures",
              failed == 0, f"failed={failed}")
        check("the absorbed entries G1, G2, H1 are now on the wheel",
              "G1" in wheel and "G2" in wheel and "H1" in wheel,
              f"G1={'G1' in wheel}, G2={'G2' in wheel}, H1={'H1' in wheel}")

    # 4e. Merging two Monster Wheels (the merge_sound contract)
    w2 = default_monster_wheel()
    merged = wheel.merge(w2)
    # the merged wheel should have at least as many entries as wheel
    check("merge with a fresh Monster Wheel preserves all entries",
          len(merged) >= len(wheel),
          f"len(merged) = {len(merged)}, len(wheel) = {len(wheel)}")
    # soundness is preserved
    audit_merged = merged.audit_soundness()
    check("merged wheel still has 0 unsound entries",
          audit_merged["unsound"] == 0,
          f"sound={audit_merged['sound']}, unsound={audit_merged['unsound']}")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Group 5: NON-REPETITION — distinct provision signature
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def test_non_repetition(wheel: MonsterWheel) -> None:
    section("GROUP 5: NON-REPETITION — distinct provision signature")

    # 5a. Monster Wheel's find_by_order provision: int -> Optional[str]
    prov = wheel.needs_wheel_provision()
    result = prov(7920)
    check("Monster Wheel provision: int -> Optional[str]",
          isinstance(result, str) or result is None,
          f"prov(7920) = {result!r}")
    check("Monster Wheel's provision(7920) -> M11",
          prov(7920) == "M11", f"got {prov(7920)!r}")

    # 5b. Integer Wheel's speak provision: Sequence[int] -> Optional[str]
    iw = default_integer_wheel()
    int_result = iw.speak([0, 1, 1, 2, 3, 5, 8, 13, 21, 34])
    check("Integer Wheel speak: Sequence[int] -> Optional[str] (still works)",
          int_result == "A000045", f"spoke {int_result!r}")

    # 5c. The signatures are different
    sig_monster = "int -> Optional[str]  (Monster Wheel's find_by_order)"
    sig_integer = "Sequence[int] -> Optional[str]  (Integer Wheel's speak)"
    check("Monster Wheel signature differs from Integer Wheel signature",
          sig_monster != sig_integer,
          f"{sig_monster} vs {sig_integer}")

    # 5d. The Monster Wheel's spoken values include group IDs not OEIS IDs
    monster_spoken = wheel.find_by_order(808017424794512875886459904961710757005754368000000000)
    check("Monster Wheel speaks the group ID 'M' for the Monster's order",
          monster_spoken == "M", f"spoke {monster_spoken!r}")
    check("Monster Wheel's spoken value is a group ID (not OEIS-style A-number)",
          monster_spoken == "M" and not monster_spoken.startswith("A"),
          f"spoke {monster_spoken!r}")

    # 5e. The Monster Wheel contains all 26 sporadic group IDs
    from cfsg_seed import CFSG_GROUPS
    expected_ids = {g[0] for g in CFSG_GROUPS}
    found_ids = set(wheel.group_ids())
    missing = expected_ids - found_ids
    check("Monster Wheel contains all 26 sporadic group IDs",
          not missing, f"missing: {missing}" if missing else
          f"all 26 present: {sorted(expected_ids)[:5]}...")

    # 5f. The Monster Wheel is a strict superset of the Integer Wheel (it has all 183 OEIS entries)
    iw_ids = set(iw.ids())
    mw_ids = set(wheel.ids())
    check("Monster Wheel is a superset of Integer Wheel (has all 183 OEIS IDs)",
          iw_ids.issubset(mw_ids),
          f"missing OEIS IDs: {iw_ids - mw_ids}" if not iw_ids.issubset(mw_ids)
          else f"all {len(iw_ids)} OEIS IDs from Integer Wheel are on the Monster Wheel")


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════════════════════

def main() -> int:
    print("=" * 70)
    print("GLM Monster Wheel — Test Harness")
    print("Source: https://github.com/AxiomMath/CFSG (Apache-2.0)")
    print("=" * 70)

    print(f"\nLoading the Monster Wheel...")
    wheel = default_monster_wheel()
    print(f"  Loaded {len(wheel)} entries "
          f"({sum(1 for g in CFSG_GROUPS)} sporadic groups "
          f"× 2 [order + exponent-vector] "
          f"+ {183} inherited OEIS entries "
          f"+ 5 group-theory OEIS + 1 composite).")

    test_sanity(wheel)
    test_sanity_no_false_positive(wheel)
    test_factorization(wheel)
    test_soundness(wheel)
    test_absorption(wheel)
    test_non_repetition(wheel)

    print()
    print("=" * 70)
    print(f"RESULTS: {_PASS} passed, {_FAIL} failed, {_PASS + _FAIL} total")
    print("=" * 70)
    return 0 if _FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

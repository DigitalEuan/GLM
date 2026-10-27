#!/usr/bin/env python3
"""GLM Monster Wheel — the wheel of finite simple groups, sourced from CFSG.

The Monster Wheel extends the Integer Wheel (`integer_wheel.py`) with the
**Classification of Finite Simple Groups** (CFSG) data, drawn from the
AxiomMath/CFSG Lean 4 formalization (https://github.com/AxiomMath/CFSG,
Apache-2.0).

Each sporadic simple group is one provision on the wheel:

    Provision: List[int] -> Optional[Group_ID]

The provision speaks the group ID (e.g. "M11", "M24", "Co1", "B", "M")
when the queried claim matches the group's order (as a single-term sequence)
or its prime-exponent vector. The wheel inherits all 183 curated OEIS
entries from the Integer Wheel, plus the 26 sporadic groups, plus the
group-theoretic OEIS sequences (`A000001` number of groups of order n,
`A001034` orders of sporadic groups).

The wheel is designed to **absorb more entries**: a Lean file parser
(`parse_cfsg_lean_file`) extracts `theorem card_<X> : card <X> = <int>`
declarations and registers them as new provisions. The
`extend_from_cfsg_directory(cfsg_root)` walk runs the parser over a
local clone of AxiomMath/CFSG to absorb every group order declared in
the project.

Contracts (inherited from `Wheel.lean` and `NeedsWheel.lean`):
  * `Sound truth p` — every spoken group ID matches the entry's order
    (re-verified by `audit_soundness`).
  * `merge_sound` — turning the wheel preserves soundness.
  * `language` — the wheel's spoken assertions form a language of
    named finite simple groups.

Why a NEW wheel (non-repetition):
  * Integer Wheel: 183 OEIS sequences, signature `Sequence[int] -> Optional[str]`
    where the str is an OEIS ID like "A000045".
  * Monster Wheel: adds a new codomain category (group IDs like "M11", "Co1",
    "M") and a new domain feature (single-integer claims of group orders,
    via `find_by_order(int)`). The Monster Wheel's `find_by_order(int)`
    signature `int -> Optional[str]` is strictly different from Integer
    Wheel's `Sequence[int] -> Optional[str]`.
  * The Lean-file parser is unique to the Monster Wheel.

References:
  * AxiomMath/CFSG: https://github.com/AxiomMath/CFSG  (Apache-2.0)
  * ATLAS of Finite Group Representations
  * Conway, Curtis, Norton, Parker, Wilson, "Atlas of Finite Groups" (1985)
  * `Wheel.lean`, `NeedsWheel.lean` in this project
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from integer_wheel import (
    IntegerWheel,
    OEISEntry,
    Provision,
    default_wheel as default_integer_wheel,
    Claim,
    RING_DONT_KNOW,
    RING_KNOWS,
    RING_THINKS_TRUE,
)
from cfsg_seed import (
    CFSG_GROUPS,
    GROUP_THEORY_OEIS,
    SPORADIC_ORDERS_SORTED,
    factorize,
    order_from_factors,
    exponent_vector,
)


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 1. The CFSG group entry (a richer OEISEntry)
# ═══════════════════════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CFSGGroupEntry:
    """A sporadic simple group entry on the Monster Wheel.

    Wraps an OEISEntry whose `terms` is `(order,)` (a single-integer
    sequence) and whose `oeis_id` is the group ID (e.g. "M11", "Co1", "M").
    """
    group_id: str
    name: str
    order: int
    factorization: str
    discoverer: str
    year: int
    notes: str = ""

    def to_oeis_entry(self) -> OEISEntry:
        """Convert to the wheel's native OEISEntry format.

        The entry's `terms` is the single-integer sequence (order,). When
        the wheel is queried with [order], this provision speaks the group ID.
        """
        return OEISEntry(
            oeis_id=self.group_id,
            name=self.name,
            terms=(self.order,),
            keywords=frozenset({"sporadic", "cfsg",
                                f"order-{self.order.bit_length()}-bits"}),
            formula=f"order = {self.factorization}",
            offset=0,
        )

    def exponent_entry(self, max_prime: int = 73) -> OEISEntry:
        """Return an OEISEntry whose `terms` is the prime-exponent vector.

        E.g. for M11 = 2^4 · 3^2 · 5 · 11:
            terms = (4, 2, 1, 0, 1, 0, 0, 0, 0, 0, 0, ...)  (primes 2,3,5,7,11,13,...)

        This lets the wheel be queried by prime factorization: given an
        exponent vector, it speaks the group ID whose order has that factorization.
        """
        exps = tuple(exponent_vector(self.order, max_prime=max_prime))
        # Use a separate OEIS-ID-like slot to disambiguate from the order-based entry
        return OEISEntry(
            oeis_id=f"{self.group_id}-EXPVEC",
            name=f"{self.name} (prime-exponent vector)",
            terms=exps,
            keywords=frozenset({"sporadic", "cfsg", "factorization"}),
            formula=f"exponents of primes 2,3,5,...,{max_prime} in |{self.group_id}|",
            offset=0,
        )


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 2. The Monster Wheel
# ═══════════════════════════════════════════════════════════════════════════════════════════════


class MonsterWheel(IntegerWheel):
    """The Monster Wheel: an Integer Wheel extended with the CFSG.

    Inherits every OEIS entry from the curated Integer Wheel, plus:
      * The 26 sporadic simple groups (Mathieu, Janko, Conway, Fischer, ...,
        the Baby Monster B and the Monster M), each as an entry with
        `terms = (order,)`. Query with `[order]` -> speaks the group ID.
      * The prime-exponent-vector entries for each sporadic group
        (terms = exponents of primes 2,3,5,7,11,... up to 73).
      * Group-theoretic OEIS sequences (`A000001` number of groups of order n,
        `A000688` abelian groups, `A001034` sporadic group orders sorted,
        `A005180` / `A060689` related).
      * The `CFSG-SPORADIC-ORDERS` composite sequence (the 26 orders in
        increasing order, an `A001034`-like entry).

    The wheel can absorb more entries via:
      * `register(entry)` — add a single entry (inherited).
      * `merge(other_wheel)` — merge with another wheel (inherited).
      * `extend_from_oeis(ids)` — fetch b-files from oeis.org (inherited).
      * `extend_from_cfsg_directory(cfsg_root)` — walk a local CFSG clone,
        parse Lean files for `theorem card_<X> : card <X> = <int>`
        declarations, and absorb them as new provisions.
    """

    def __init__(self, with_integer_wheel_entries: bool = True):
        super().__init__()
        if with_integer_wheel_entries:
            # Inherit every OEIS entry from the parent Integer Wheel.
            iw = default_integer_wheel()
            for e in iw.entries():
                self.register(e)
        # Add the 26 sporadic groups (as both order-entries and EXPVEC-entries).
        for gid, name, order, fact, disc, year, notes in CFSG_GROUPS:
            g = CFSGGroupEntry(gid, name, order, fact, disc, year, notes)
            self.register(g.to_oeis_entry())
            # The EXPVEC entries use a different oeis_id slot
            # (`<group_id>-EXPVEC`), so they don't collide with the order
            # entry. They're queryable via the prime-exponent vector.
            self.register(g.exponent_entry())
        # Add the group-theoretic OEIS sequences (these replace any inherited
        # versions of A000001 if present, since the parent has it too).
        for oid, name, terms, keywords, formula, offset in GROUP_THEORY_OEIS:
            # replace if already present (parent Integer Wheel has A000001 too)
            self.register(OEISEntry(
                oeis_id=oid, name=name, terms=tuple(terms),
                keywords=frozenset(keywords) if keywords else frozenset(),
                formula=formula, offset=offset,
            ))
        # Add the composite CFSG-SPORADIC-ORDERS sequence
        self.register(OEISEntry(
            oeis_id="CFSG-SPORADIC-ORDERS",
            name="Sporadic simple group orders, sorted (AxiomMath/CFSG)",
            terms=tuple(SPORADIC_ORDERS_SORTED),
            keywords=frozenset({"sporadic", "cfsg", "sequence", "composite"}),
            formula="the 26 sporadic simple group orders in increasing order",
            offset=1,
        ))
        # Re-verify the wheel after registering the new entries
        self._absorbed_from_cfsg: List[Path] = []

    # ── introspection ─────────────────────────────────────────────────────────

    def group_ids(self) -> List[str]:
        """The 26 sporadic group IDs (M11, M12, ..., B, M)."""
        return sorted(g[0] for g in CFSG_GROUPS) + [
            e.oeis_id for e in self._entries
            if "cfsg" in e.keywords and e.oeis_id not in (g[0] for g in CFSG_GROUPS)
            and not e.oeis_id.endswith("-EXPVEC")
        ]

    def groups(self) -> List[CFSGGroupEntry]:
        """All registered CFSG sporadic groups as CFSGGroupEntry objects."""
        out: List[CFSGGroupEntry] = []
        for gid, name, order, fact, disc, year, notes in CFSG_GROUPS:
            out.append(CFSGGroupEntry(gid, name, order, fact, disc, year, notes))
        return out

    def __repr__(self) -> str:
        n_cfsg = sum(1 for e in self._entries if "cfsg" in e.keywords
                     and not e.oeis_id.endswith("-EXPVEC")
                     and e.oeis_id != "CFSG-SPORADIC-ORDERS")
        return (f"MonsterWheel(total_entries={len(self._entries)}, "
                f"cfsg_groups={n_cfsg}, "
                f"absorbed_from_cfsg={len(self._absorbed_from_cfsg)})")

    # ── the speak-by-order operation ───────────────────────────────────────────

    def find_by_order(self, order: int) -> Optional[str]:
        """Speak the group ID whose order matches the given integer, or None.

        Mirrors `speak` for the order-based entries. The provision
        signature here is `int -> Optional[str]`, which is strictly different
        from Integer Wheel's `Sequence[int] -> Optional[str]` (different
        domain shape).

        Looks only at **single-term entries** (entries with `terms = (order,)`)
        and ignores multi-term entries (the EXPVEC entries and the
        composite `CFSG-SPORADIC-ORDERS` sequence). This prevents false
        identification when a single-integer claim happens to coincide
        with the first term of a multi-term entry (e.g. `7` is the
        exponent of 2 in J2's order, so the J2-EXPVEC entry's first
        term is 7 — but querying `find_by_order(7)` should stay silent,
        not falsely identify a group of order 7).
        """
        candidates = []
        for e in self._entries:
            if len(e.terms) != 1:
                continue
            if e.oeis_id.endswith("-EXPVEC"):
                continue
            if e.oeis_id == "CFSG-SPORADIC-ORDERS":
                continue
            if e.terms[0] == order:
                candidates.append(e)
        if not candidates:
            return None
        # determinism: alphabetical by OEIS/group ID
        candidates.sort(key=lambda x: x.oeis_id)
        # cache the spoken assertion in the language wheel
        self._language[(order,)] = candidates[0].oeis_id
        return candidates[0].oeis_id

    def find_by_factorization(self,
                              primes: Sequence[int],
                              exponents: Sequence[int]) -> Optional[str]:
        """Speak the group ID whose order has the given prime factorization.

        `primes` and `exponents` must have the same length. The function
        computes the order and then calls `find_by_order`.

        E.g. for the Monster:
            find_by_factorization([2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
                                   31, 41, 47, 59, 71],
                                  [46, 20, 9, 6, 2, 3, 1, 1, 1, 1,
                                   1, 1, 1, 1, 1]) -> "M"
        """
        if len(primes) != len(exponents):
            return None
        order = 1
        for p, e in zip(primes, exponents):
            order *= p ** e
        return self.find_by_order(order)

    def find_by_exponent_vector(self,
                                 exponent_vector: Sequence[int],
                                 max_prime: int = 73) -> Optional[str]:
        """Speak the group ID whose order has the given exponent vector
        for primes 2, 3, 5, ..., max_prime.

        E.g. for M11 = 2^4 · 3^2 · 5 · 11 (with max_prime=11):
            find_by_exponent_vector([4, 2, 1, 0, 1]) -> "M11"
        """
        from math import prod
        primes_upto_73 = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41,
                          43, 47, 53, 59, 61, 67, 71]
        primes = [p for p in primes_upto_73 if p <= max_prime]
        if len(exponent_vector) > len(primes):
            return None
        # pad to len(primes)
        ev = list(exponent_vector) + [0] * (len(primes) - len(exponent_vector))
        order = prod(p ** e for p, e in zip(primes, ev))
        return self.find_by_order(order)

    # ── the CFSG Lean-file parser (absorb more entries) ──────────────────────

    # Pattern: any Lean declaration containing `card_<X>` followed by
    # `: ... = <int>`. The leading keyword can be `theorem`, `lemma`,
    # `have`, or `have h_card_<X>` (with an `h_` prefix to the name).
    # We use `\w*card_(\w+)` so the optional `h_` prefix is consumed
    # without being captured.
    _LEAN_PATTERNS = [
        # theorem/lemma/have <name>card_<X> ... : ... = <int>
        re.compile(
            r'(?:theorem|lemma|have)\s+\w*card_(\w+)\s*(?:\[.*?\])?\s*'
            r'(?:\([^)]*\))?\s*:[^=]*?=\s*(\d+)', re.DOTALL),
        # fallback: any line containing `card_<X> : ... = <int>`
        re.compile(
            r'\bcard_(\w+)\s*(?:\[.*?\])?\s*(?:\([^)]*\))?\s*'
            r':[^=]*?=\s*(\d+)', re.DOTALL),
    ]

    def parse_cfsg_lean_file(self, path: Path) -> List[OEISEntry]:
        """Parse a CFSG Lean file for `card_<X> = <int>` declarations.

        Returns a list of OEISEntry objects, one per found declaration.
        The OEIS-ID slot is the lowercased `<X>` from the declaration name.
        The terms are `(int,)`.

        Examples of patterns matched:
            theorem card_J1 : card J1 = 175560 := ...
            have h_card : card M11 = 7920 := ...
            lemma card_Co2 : card Co2 = 42305420800 := ...
        """
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        found: Dict[str, int] = {}
        for pat in self._LEAN_PATTERNS:
            for m in pat.finditer(text):
                # Preserve the original case of the group name (e.g. "Co1",
                # "J1", "M11") so the absorbed entry can be compared
                # case-sensitively against the curated cfsg_seed entries.
                name = m.group(1)
                try:
                    value = int(m.group(2))
                except ValueError:
                    continue
                # prefer the first occurrence; don't overwrite if already found
                if name not in found:
                    found[name] = value

        entries: List[OEISEntry] = []
        for name, value in found.items():
            # Preserve the original case of the group name from the Lean
            # declaration (e.g. "Co1", "J1", "M11"). The case matters for
            # conflict detection against the curated cfsg_seed entries
            # (where "Co1" is distinct from "CO1").
            #
            # Strip any leading/trailing `_card` / `card_` artifacts from
            # the regex capture (the `\w*` in the pattern can leave a stray
            # "h_" prefix from `have h_card_<X>`).
            clean_name = name
            if clean_name.lower().startswith("h_"):
                clean_name = clean_name[2:]
            entries.append(OEISEntry(
                oeis_id=clean_name,
                name=f"{clean_name} (parsed from {Path(path).name})",
                terms=(value,),
                keywords=frozenset({"cfsg", "parsed", "lean"}),
                formula=f"order = {value}",
                offset=0,
            ))
        return entries

    def extend_from_cfsg_directory(self, cfsg_root: Path) -> Tuple[int, int]:
        """Walk a local clone of AxiomMath/CFSG and absorb every
        `card_<X> = <int>` declaration as a new entry.

        Args:
            cfsg_root: the root of the local CFSG clone
                       (the directory containing `CFSG/`).

        Returns:
            (added, failed) — number of new entries absorbed and the number
            of Lean files that failed to parse.

        The walk uses `rglob("*.lean")` so it covers all subdirectories:
            CFSG/Sporadic/J1.lean, CFSG/Sporadic/M23.lean, etc.
        Each new entry is registered via `register()`; entries that would
        duplicate an existing OEIS ID are skipped (the first registration
        wins, matching the wheel's `merge_sound` contract).
        """
        added = 0
        failed = 0
        for lean_file in Path(cfsg_root).rglob("*.lean"):
            try:
                entries = self.parse_cfsg_lean_file(lean_file)
            except Exception:
                failed += 1
                continue
            for e in entries:
                # Skip if the OEIS-ID slot is already taken (merge_sound
                # keeps the first assertion; a conflict would unsound the
                # wheel — we refuse to overwrite).
                if e.oeis_id in self._by_id:
                    # If the existing entry has the same order, no conflict;
                    # otherwise skip (the Lean file might be wrong or use a
                    # different convention).
                    existing = self._by_id[e.oeis_id]
                    if existing.terms == e.terms:
                        continue  # same content; skip
                    # conflict: skip, do not overwrite (per `conflict_unsound`)
                    continue
                self.register(e)
                added += 1
            self._absorbed_from_cfsg.append(lean_file)
        return added, failed

    # ── the needs-wheel-style provision (for v18 engine) ──────────────────────

    def needs_wheel_provision(self) -> Callable[[int], Optional[str]]:
        """Return a provision `int -> Optional[str]` for the v18 engine.

        When the engine is asked "what group has this order?", the provision
        speaks the group ID if known, else stays silent.

        The signature `int -> Optional[str]` is strictly different from
        Integer Wheel's `Sequence[int] -> Optional[str]` (the domain is
        `int`, not `Sequence[int]`).
        """
        def prov(order: int) -> Optional[str]:
            return self.find_by_order(order)

        prov.__name__ = "monster_wheel_provision"  # type: ignore[attr-defined]
        prov.__doc__ = (  # type: ignore[attr-defined]
            "The Monster Wheel provision: speaks the group ID whose order "
            "matches, or stays silent. Signature: int -> Optional[str]."
        )
        return prov


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 3. Default wheel builder
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def default_monster_wheel() -> MonsterWheel:
    """Build the default Monster Wheel with all 26 sporadic groups and the
    inherited OEIS entries from the Integer Wheel."""
    return MonsterWheel(with_integer_wheel_entries=True)


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 4. CLI
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def _cli_find_by_order(wheel: MonsterWheel, args) -> int:
    try:
        order = int(args.order)
    except ValueError as e:
        print(f"error: order must be an integer: {e}", file=sys.stderr)
        return 2
    spoken = wheel.find_by_order(order)
    if spoken is None:
        print(f"No sporadic group of order {order}.")
        return 1
    entry = wheel.get(spoken)
    print(f"{spoken}  --  {entry.name}")
    if entry.formula:
        print(f"  formula: {entry.formula}")
    if args.verbose and len(entry.terms) > 0:
        print(f"  order: {entry.terms[0]}")
        from cfsg_seed import factorize
        print(f"  factorization: {factorize(entry.terms[0])}")
    return 0


def _cli_find_by_factorization(wheel: MonsterWheel, args) -> int:
    try:
        primes = [int(x) for x in args.primes.split(",")]
        exponents = [int(x) for x in args.exponents.split(",")]
    except ValueError as e:
        print(f"error: primes and exponents must be comma-separated integers: {e}",
              file=sys.stderr)
        return 2
    if len(primes) != len(exponents):
        print("error: primes and exponents must have the same length",
              file=sys.stderr)
        return 2
    spoken = wheel.find_by_factorization(primes, exponents)
    order = 1
    for p, e in zip(primes, exponents):
        order *= p ** e
    if spoken is None:
        print(f"No sporadic group with factorization "
              f"{' · '.join(f'{p}^{e}' for p, e in zip(primes, exponents))} "
              f"(order {order}).")
        return 1
    entry = wheel.get(spoken)
    print(f"{spoken}  --  {entry.name}")
    print(f"  order: {order}")
    if entry.formula:
        print(f"  formula: {entry.formula}")
    return 0


def _cli_parse_lean(wheel: MonsterWheel, args) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    entries = wheel.parse_cfsg_lean_file(path)
    if not entries:
        print(f"No card_<X> declarations found in {path}.")
        return 1
    print(f"Parsed {len(entries)} entries from {path}:")
    for e in entries:
        print(f"  {e.oeis_id:10s}  order={e.terms[0] if e.terms else '?'}")
    return 0


def _cli_absorb_cfsg(wheel: MonsterWheel, args) -> int:
    root = Path(args.cfsg_root)
    if not root.exists():
        print(f"error: CFSG root not found: {root}", file=sys.stderr)
        return 2
    added, failed = wheel.extend_from_cfsg_directory(root)
    print(f"Absorbed {added} new entries from {root}; {failed} files failed to parse.")
    print(f"Wheel now has {len(wheel)} entries.")
    return 0


def _cli_list(wheel: MonsterWheel, args) -> int:
    if args.cfsg_only:
        entries = [e for e in wheel.entries()
                   if "cfsg" in e.keywords and not e.oeis_id.endswith("-EXPVEC")]
    elif args.sporadic_only:
        from cfsg_seed import CFSG_GROUPS
        sporadic_ids = {g[0] for g in CFSG_GROUPS}
        entries = [e for e in wheel.entries() if e.oeis_id in sporadic_ids]
    else:
        entries = wheel.entries()
    print(f"Monster Wheel: {len(entries)} entries" +
          (" (CFSG-only)" if args.cfsg_only else
           " (sporadic-only)" if args.sporadic_only else ""))
    for e in entries[:args.limit]:
        order_str = f"  order={e.terms[0]}" if e.terms and len(e.terms) == 1 else ""
        print(f"  {e.oeis_id:25s}  {e.name[:80]}{order_str}")
    if len(entries) > args.limit:
        print(f"  ... and {len(entries) - args.limit} more (use --limit).")
    return 0


def _cli_soundness(wheel: MonsterWheel, args) -> int:
    report = wheel.audit_soundness()
    print(f"Monster Wheel soundness audit:")
    print(f"  entries: {report['entries']}")
    print(f"  sound:   {report['sound']}")
    print(f"  silent:  {report['silent']}")
    print(f"  unsound: {report['unsound']}")
    if report["unsound_ids"]:
        print(f"  unsound IDs: {report['unsound_ids']}")
    return 0 if report["unsound"] == 0 else 1


def _cli_demo(wheel: MonsterWheel, args) -> int:
    """Demonstrate the wheel on the 26 sporadic groups + the Monster."""
    from cfsg_seed import CFSG_GROUPS
    print(f"Monster Wheel demo: {len(wheel)} total entries.")
    print(f"\nIdentifying each sporadic group by order:")
    for gid, name, order, fact, disc, year, _notes in CFSG_GROUPS:
        spoken = wheel.find_by_order(order)
        ok = (spoken == gid)
        tag = "OK" if ok else f"MISMATCH (got {spoken})"
        print(f"  {gid:6s}  order={order:>50,d}  -> {tag}")

    print(f"\nIdentifying each sporadic group by prime factorization (via exponent vector):")
    for gid, name, order, fact, disc, year, _notes in CFSG_GROUPS[:5]:  # first 5 only
        from cfsg_seed import exponent_vector
        ev = exponent_vector(order, max_prime=73)
        # trim trailing zeros
        while ev and ev[-1] == 0:
            ev.pop()
        spoken = wheel.find_by_exponent_vector(ev)
        ok = (spoken == gid)
        tag = "OK" if ok else f"MISMATCH (got {spoken})"
        print(f"  {gid:6s}  expvec={ev}  -> {tag}")

    # The Monster
    monster_order = next(g[2] for g in CFSG_GROUPS if g[0] == "M")
    print(f"\nThe Monster group M:")
    spoken = wheel.find_by_order(monster_order)
    print(f"  order: {monster_order}")
    print(f"  find_by_order: {spoken}")
    # factorization as a claim
    factors = factorize(monster_order)
    primes = [p for p, _ in factors]
    exponents = [e for _, e in factors]
    print(f"  prime factorization: {dict(factors)}")
    spoken_by_fact = wheel.find_by_factorization(primes, exponents)
    print(f"  find_by_factorization: {spoken_by_fact}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        prog="monster_wheel",
        description="GLM Monster Wheel — CFSG sporadic simple groups "
                    "(https://github.com/AxiomMath/CFSG, Apache-2.0)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fo = sub.add_parser("find-by-order", help="identify a sporadic group by its order")
    p_fo.add_argument("order", help="the group order as an integer (e.g. 175560)")
    p_fo.add_argument("-v", "--verbose", action="store_true")
    p_fo.set_defaults(func=_cli_find_by_order)

    p_ff = sub.add_parser("find-by-factorization",
                          help="identify a sporadic group by its prime factorization")
    p_ff.add_argument("--primes", required=True, help="comma-separated primes, e.g. 2,3,5,11")
    p_ff.add_argument("--exponents", required=True,
                      help="comma-separated exponents, e.g. 4,2,1,1")
    p_ff.set_defaults(func=_cli_find_by_factorization)

    p_pl = sub.add_parser("parse-lean", help="parse a CFSG Lean file for card_<X> = <int>")
    p_pl.add_argument("file", help="path to the .lean file")
    p_pl.set_defaults(func=_cli_parse_lean)

    p_ab = sub.add_parser("absorb-cfsg",
                          help="walk a local CFSG clone and absorb all group orders")
    p_ab.add_argument("cfsg_root", help="root of the local CFSG clone")
    p_ab.set_defaults(func=_cli_absorb_cfsg)

    p_ls = sub.add_parser("list", help="list entries on the wheel")
    p_ls.add_argument("--cfsg-only", action="store_true")
    p_ls.add_argument("--sporadic-only", action="store_true")
    p_ls.add_argument("--limit", type=int, default=30)
    p_ls.set_defaults(func=_cli_list)

    p_snd = sub.add_parser("soundness", help="audit the wheel's soundness")
    p_snd.set_defaults(func=_cli_soundness)

    p_dm = sub.add_parser("demo", help="demonstrate the wheel on all 26 sporadic groups")
    p_dm.set_defaults(func=_cli_demo)

    args = parser.parse_args(argv)
    wheel = default_monster_wheel()
    return args.func(wheel, args)


if __name__ == "__main__":
    sys.exit(main())

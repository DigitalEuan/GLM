"""``glm_universal.wheels.monster_wheel`` -- the Monster Wheel: the Integer
Wheel plus the 26 sporadic simple groups, keyed by order and by the exponent
vector of the order.

*Taken 31 October 2026 (intake of glm_wheels_bundle; directive D22).*
*PROVISIONAL (31 October 2026, the owner's decision): installed in the wheels
folder ahead of the Lean build; the item stays in ``source_material/ToDo/``
at Lean written until ``scripts/rebuild_lean.sh`` confirms
``Wheels/IntegerWheel.lean`` and ``Wheels/SporadicOrders.lean``, and answers
that rest on it say so (``glm_universal.wheels.provisional_status``).*
Ported from ``source_material/ToDo/glm_wheels_bundle/monster_wheel.py`` (the
item is filed in ``source_material/done/`` at absorption); data
:mod:`glm_universal.wheels.cfsg_seed`; study
``studies/INTEGER_WHEEL_STUDY.md``.  What is proved, in
``src/lean/RequestProject/GLM/Wheels/SporadicOrders.lean`` (namespace
``GLM.SporadicOrders``): each of the 26 stored orders equals its prime
factorisation (``order_M11`` ... ``order_M``), the orders are distinct and so
are the names (``sporadicOrders_nodup``, ``sporadicNames_nodup``), and
``findByOrder`` -- the Lean twin of :meth:`MonsterWheel.find_by_order` -- is
sound and complete, so the answer to *which sporadic group has order n* is
unique.  That the Monster Wheel keeps every Integer Wheel entry is
``merge_keeps`` of ``Wheels/IntegerWheel.lean``.

The CFSG data are drawn by the supplied item from the AxiomMath/CFSG Lean 4
formalisation (https://github.com/AxiomMath/CFSG, Apache-2.0) and the ATLAS.

Changes from the supplied file: package imports; the inherited OEIS entries
are those of the *audited* Integer Wheel
(:func:`glm_universal.wheels.integer_wheel.default_wheel`), and of the five
supplied group-theory sequences only those the independent reference
reproduces are registered (:data:`oeis_reference.ADMITTED_GROUP_THEORY_IDS`);
``supplied=True`` builds the unaudited wheel, kept as the study's control.
No network and no file is read at import; the CFSG Lean-file parser reads only
the files it is given, and the walk of a local CFSG clone is
:func:`glm_universal.wheels.cfsg_import.extend_from_cfsg_directory`.

*Last altered 31 October 2026 (repository check): the CFSG directory walk
moved to* :mod:`glm_universal.wheels.cfsg_import` *(the session's import
closure).*
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .integer_wheel import (
    IntegerWheel,
    OEISEntry,
    default_wheel as default_integer_wheel,
    supplied_wheel as supplied_integer_wheel,
)
from .cfsg_seed import (
    CFSG_GROUPS,
    GROUP_THEORY_OEIS,
    SPORADIC_ORDERS_SORTED,
    exponent_vector,
)

__all__ = [
    "CFSGGroupEntry", "MonsterWheel", "default_monster_wheel",
    "supplied_monster_wheel", "PRIMES_TO_73", "SORTED_ORDERS_ID", "main",
]

#: The primes 2 .. 71 over which an exponent vector is read (the supplied
#: ``max_prime=73`` bound; 73 itself divides no sporadic order).
PRIMES_TO_73: Tuple[int, ...] = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41,
                                 43, 47, 53, 59, 61, 67, 71)

#: The local identifier of the sorted sporadic orders (the OEIS has them as
#: A001228; the supplied data filed them under A001034, which is another
#: sequence, and that entry is held out by the audit).
SORTED_ORDERS_ID = "CFSG-SPORADIC-ORDERS"


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
        """The wheel's native entry: `terms = (order,)`, so the claim
        `[order]` speaks the group ID."""
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
        """An entry whose `terms` is the exponent vector of the order over the
        primes 2, 3, 5, ..., `max_prime` (id `<group_id>-EXPVEC`).

        E.g. for M11 = 2^4 · 3^2 · 5 · 11:
            terms = (4, 2, 1, 0, 1, 0, 0, ...)
        """
        exps = tuple(exponent_vector(self.order, max_prime=max_prime))
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

    Holds the audited Integer Wheel's entries, plus:
      * the 26 sporadic simple groups, each an entry with `terms = (order,)`
        (query `[order]` -> the group ID);
      * their exponent-vector entries (`<id>-EXPVEC`, exponents of 2, 3, 5, ...
        up to 71);
      * the group-theory OEIS sequences the audit admits (`A000001`, `A000688`);
      * the 26 orders in increasing order under the local id
        `CFSG-SPORADIC-ORDERS`.

    With `supplied=True` it is built from the supplied data unaudited (the
    study's control C).
    """

    def __init__(self, with_integer_wheel_entries: bool = True, supplied: bool = False):
        super().__init__()
        if with_integer_wheel_entries:
            iw = supplied_integer_wheel() if supplied else default_integer_wheel()
            for e in iw.entries():
                self.register(e)
        # The 26 sporadic groups (as both order-entries and EXPVEC-entries).
        for gid, name, order, fact, disc, year, notes in CFSG_GROUPS:
            g = CFSGGroupEntry(gid, name, order, fact, disc, year, notes)
            self.register(g.to_oeis_entry())
            self.register(g.exponent_entry())
        # The group-theoretic OEIS sequences (only the audited ones by default).
        if supplied:
            admitted = {row[0] for row in GROUP_THEORY_OEIS}
        else:
            from .oeis_reference import ADMITTED_GROUP_THEORY_IDS
            admitted = set(ADMITTED_GROUP_THEORY_IDS)
        for oid, name, terms, keywords, formula, offset in GROUP_THEORY_OEIS:
            if oid not in admitted:
                continue
            self.register(OEISEntry(
                oeis_id=oid, name=name, terms=tuple(terms),
                keywords=frozenset(keywords) if keywords else frozenset(),
                formula=formula, offset=offset,
            ))
        # The composite sorted-orders sequence.
        self.register(OEISEntry(
            oeis_id=SORTED_ORDERS_ID,
            name="Sporadic simple group orders, sorted (AxiomMath/CFSG)",
            terms=tuple(SPORADIC_ORDERS_SORTED),
            keywords=frozenset({"sporadic", "cfsg", "sequence", "composite"}),
            formula="the 26 sporadic simple group orders in increasing order",
            offset=1,
        ))
        self._absorbed_from_cfsg: List[Path] = []

    # ── introspection ─────────────────────────────────────────────────────────

    def group_ids(self) -> List[str]:
        """The 26 sporadic group IDs (sorted), then any absorbed CFSG ids."""
        sporadic = {g[0] for g in CFSG_GROUPS}
        return sorted(sporadic) + [
            e.oeis_id for e in self._entries
            if "cfsg" in e.keywords and e.oeis_id not in sporadic
            and not e.oeis_id.endswith("-EXPVEC") and e.oeis_id != SORTED_ORDERS_ID
        ]

    def groups(self) -> List[CFSGGroupEntry]:
        """All 26 sporadic groups as CFSGGroupEntry objects."""
        return [CFSGGroupEntry(*g) for g in CFSG_GROUPS]

    def group(self, group_id: str) -> Optional[CFSGGroupEntry]:
        """The sporadic group with this ID, or `None`."""
        for g in CFSG_GROUPS:
            if g[0] == group_id:
                return CFSGGroupEntry(*g)
        return None

    def __repr__(self) -> str:
        n_cfsg = sum(1 for e in self._entries if "cfsg" in e.keywords
                     and not e.oeis_id.endswith("-EXPVEC")
                     and e.oeis_id != SORTED_ORDERS_ID)
        return (f"MonsterWheel(total_entries={len(self._entries)}, "
                f"cfsg_groups={n_cfsg}, "
                f"absorbed_from_cfsg={len(self._absorbed_from_cfsg)})")

    # ── the speak-by-order operation ───────────────────────────────────────────

    def find_by_order(self, order: int) -> Optional[str]:
        """Speak the group ID whose order is `order`, or None (`findByOrder` in
        `Wheels/SporadicOrders.lean`, sound and complete there).

        Looks only at single-term entries, never at the EXPVEC entries or the
        sorted orders: `7` is the exponent of 2 in J2's order, so J2-EXPVEC's
        first term is 7, yet no group has order 7.
        """
        candidates = []
        for e in self._entries:
            if len(e.terms) != 1:
                continue
            if e.oeis_id.endswith("-EXPVEC") or e.oeis_id == SORTED_ORDERS_ID:
                continue
            if e.terms[0] == order:
                candidates.append(e)
        if not candidates:
            return None
        candidates.sort(key=lambda x: x.oeis_id)
        self._language[(order,)] = candidates[0].oeis_id
        return candidates[0].oeis_id

    def find_by_factorization(self, primes: Sequence[int],
                              exponents: Sequence[int]) -> Optional[str]:
        """Speak the group ID whose order is `prod(p ** e)`, or None
        (`primes` and `exponents` of the same length)."""
        if len(primes) != len(exponents):
            return None
        order = 1
        for p, e in zip(primes, exponents):
            order *= p ** e
        return self.find_by_order(order)

    def find_by_exponent_vector(self, exponents: Sequence[int],
                                max_prime: int = 73) -> Optional[str]:
        """Speak the group ID whose order has these exponents of the primes
        2, 3, 5, ..., `max_prime` (a shorter vector is padded with zeros).

        E.g. find_by_exponent_vector([4, 2, 1, 0, 1]) -> "M11".
        """
        primes = [p for p in PRIMES_TO_73 if p <= max_prime]
        if len(exponents) > len(primes):
            return None
        order = 1
        for p, e in zip(primes, list(exponents) + [0] * (len(primes) - len(exponents))):
            order *= p ** e
        return self.find_by_order(order)

    # ── the CFSG Lean-file parser (absorb more entries) ──────────────────────

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
        """Parse a CFSG Lean file for `card_<X> = <int>` declarations; one
        entry `(<X>, (int,))` per declaration, the first occurrence winning."""
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        found: Dict[str, int] = {}
        for pat in self._LEAN_PATTERNS:
            for m in pat.finditer(text):
                name = m.group(1)
                try:
                    value = int(m.group(2))
                except ValueError:
                    continue
                if name not in found:
                    found[name] = value
        entries: List[OEISEntry] = []
        for name, value in found.items():
            clean_name = name[2:] if name.lower().startswith("h_") else name
            entries.append(OEISEntry(
                oeis_id=clean_name,
                name=f"{clean_name} (parsed from {Path(path).name})",
                terms=(value,),
                keywords=frozenset({"cfsg", "parsed", "lean"}),
                formula=f"order = {value}",
                offset=0,
            ))
        return entries

    # ``extend_from_cfsg_directory`` -- the walk of a local CFSG clone -- is
    # :func:`glm_universal.wheels.cfsg_import.extend_from_cfsg_directory`
    # (moved 31 October 2026, repository check): a directory walk for Lean
    # files in this module put the whole Lean development into the import
    # closure of every session, since the parser's ``sequence`` lookup kind
    # builds this wheel (``tests/test_signoff.py``).

    # ── the needs-wheel-style provision (for v18 engine) ──────────────────────

    def needs_wheel_provision(self) -> Callable[[int], Optional[str]]:  # type: ignore[override]
        """A provision `int -> Optional[str]`: the group ID of that order, or
        silence."""
        def prov(order: int) -> Optional[str]:
            return self.find_by_order(order)

        prov.__name__ = "monster_wheel_provision"  # type: ignore[attr-defined]
        prov.__doc__ = (  # type: ignore[attr-defined]
            "The Monster Wheel provision: speaks the group ID whose order "
            "matches, or stays silent. Signature: int -> Optional[str]."
        )
        return prov


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 3. Builders
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def default_monster_wheel() -> MonsterWheel:
    """The absorbed Monster Wheel (audited inherited entries)."""
    return MonsterWheel(with_integer_wheel_entries=True)


def supplied_monster_wheel() -> MonsterWheel:
    """The Monster Wheel from the supplied data, unaudited (control C)."""
    return MonsterWheel(with_integer_wheel_entries=True, supplied=True)


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 4. CLI:  python3 -m glm_universal.wheels.monster_wheel find-by-order 7920
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
    return 0


def _cli_find_by_factorization(wheel: MonsterWheel, args) -> int:
    try:
        primes = [int(x) for x in args.primes.split(",")]
        exponents = [int(x) for x in args.exponents.split(",")]
    except ValueError as e:
        print(f"error: comma-separated integers expected: {e}", file=sys.stderr)
        return 2
    if len(primes) != len(exponents):
        print("error: primes and exponents must have the same length", file=sys.stderr)
        return 2
    spoken = wheel.find_by_factorization(primes, exponents)
    if spoken is None:
        print("No sporadic group has that order.")
        return 1
    print(f"{spoken}  --  {wheel.get(spoken).name}")
    return 0


def _cli_list(wheel: MonsterWheel, args) -> int:
    for g in wheel.groups():
        print(f"  {g.group_id:6s}  {g.order}  = {g.factorization}")
    return 0


def _cli_soundness(wheel: MonsterWheel, args) -> int:
    report = wheel.audit_soundness()
    print("Monster Wheel soundness audit:")
    for key in ("entries", "sound", "silent", "unsound"):
        print(f"  {key}: {report[key]}")
    return 0 if report["unsound"] == 0 else 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        prog="python3 -m glm_universal.wheels.monster_wheel",
        description="GLM Monster Wheel -- the 26 sporadic simple groups",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_fo = sub.add_parser("find-by-order", help="identify a sporadic group by its order")
    p_fo.add_argument("order")
    p_fo.set_defaults(func=_cli_find_by_order)
    p_ff = sub.add_parser("find-by-factorization",
                          help="identify a sporadic group by its prime factorisation")
    p_ff.add_argument("--primes", required=True)
    p_ff.add_argument("--exponents", required=True)
    p_ff.set_defaults(func=_cli_find_by_factorization)
    p_ls = sub.add_parser("list", help="the 26 sporadic groups")
    p_ls.set_defaults(func=_cli_list)
    p_snd = sub.add_parser("soundness", help="audit the wheel's soundness")
    p_snd.set_defaults(func=_cli_soundness)
    args = parser.parse_args(argv)
    return args.func(default_monster_wheel(), args)


if __name__ == "__main__":
    sys.exit(main())

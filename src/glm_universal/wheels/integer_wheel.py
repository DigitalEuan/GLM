"""``glm_universal.wheels.integer_wheel`` -- the Integer Wheel: a provisions
wheel that answers an integer prefix with an OEIS identifier, or stays silent.

*Taken 31 October 2026 (intake of glm_wheels_bundle; directive D22).*
*PROVISIONAL (31 October 2026, the owner's decision): installed in the wheels
folder ahead of the Lean build; the item stays in ``source_material/ToDo/``
at Lean written until ``scripts/rebuild_lean.sh`` confirms
``Wheels/IntegerWheel.lean`` and ``Wheels/SporadicOrders.lean``, and answers
that rest on it say so (``glm_universal.wheels.provisional_status``).*
Ported from ``source_material/ToDo/glm_wheels_bundle/integer_wheel.py`` (the
item is filed in ``source_material/done/`` at absorption); the study is
``studies/INTEGER_WHEEL_STUDY.md`` and the contract is proved in
``src/lean/RequestProject/GLM/Wheels/IntegerWheel.lean`` (namespace
``GLM.IntegerWheel``).

**The contract** (each clause a theorem of the Lean file).  An entry
``(id, terms)`` speaks its id on a claim exactly when the claim is nonempty
and a prefix of its stored terms (``provision_sound``,
``provision_complete``).  :meth:`IntegerWheel.speak` is silent on the empty
claim and when no entry's terms start with the claim (``speak_eq_none``);
otherwise it answers from the entries whose terms *equal* the claim when
there are any, else from those whose terms merely start with it
(``speak_exact``), and returns the least identifier of that tier
(``speak_least``).  Whatever it says is the id of an entry whose stored terms
start with the claim (``speak_sound``).  :meth:`IntegerWheel.merge` keeps
every old entry and adds the new ids (``merge_keeps``, ``mem_merge``,
``merge_self``, ``merge_speak_sound``).

**Soundness against the stored terms is not truth.**  The supplied data
(:mod:`glm_universal.wheels.oeis_seed`) has entries whose stored terms are not
the OEIS sequence of their identifier.  :func:`default_wheel` therefore holds
only the supplied entries that the independent reference
(:mod:`glm_universal.wheels.oeis_reference`) reproduces term for term;
:func:`supplied_wheel` holds all 183 supplied entries and is kept as the
study's control, not for answering.

Changes from the supplied file: package imports instead of ``sys.path``
edits; the OEIS b-file fetch imports ``urllib`` only when called and takes an
integer timeout (directive D7: no float); :func:`default_wheel` is the audited
wheel; :meth:`IntegerWheel.locate` (the earliest run of stored terms equal to
the claim, used by the query surface when ``speak`` is silent) is new.  No
network is touched at import or by any default path: ``extend_from_oeis``
stays opt-in.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

__all__ = [
    "Claim", "Provision", "RING_KNOWS", "RING_THINKS_TRUE", "RING_DONT_KNOW",
    "STATUS_VERIFIED", "STATUS_REFUTED", "STATUS_SURVIVES", "STATUS_OPEN",
    "STATUS_UNTESTED", "ring_of", "OEISEntry", "IntegerWheel",
    "supplied_entries", "supplied_wheel", "default_wheel", "main",
]

# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 1. The contract (mirrors Wheel.lean / NeedsWheel.lean / Wheels/IntegerWheel.lean)
# ═══════════════════════════════════════════════════════════════════════════════════════════════

# A claim is a finite integer prefix. We use tuples (immutable, hashable).
Claim = Tuple[int, ...]

# A provision answers a claim with `Some(oeis_id)` or stays silent with `None`.
# This is `α -> Option String`, generalising `α -> Option Bool` from NeedsWheel.lean.
Provision = Callable[[Claim], Optional[str]]

# The three rings, matching `Wheel.lean`'s `Ring` inductive type.
RING_KNOWS = "knows"
RING_THINKS_TRUE = "thinks-true"
RING_DONT_KNOW = "doesnt-know"

# The statuses, matching `Wheel.lean`'s `Status` inductive type.
STATUS_VERIFIED = "verified"        # KNOWS: asserts the OEIS ID for this prefix
STATUS_REFUTED = "refuted"           # KNOWS: asserts no entry matches this prefix
STATUS_SURVIVES = "survives"         # THINKS-TRUE: a partial match, no full b-file
STATUS_OPEN = "open"                 # DOESN'T-KNOW
STATUS_UNTESTED = "untested"         # DOESN'T-KNOW


def ring_of(status: str) -> str:
    """`ring_of` in the engine; mirrors `Wheel.lean`'s `ring` definition."""
    if status in (STATUS_VERIFIED, STATUS_REFUTED):
        return RING_KNOWS
    if status == STATUS_SURVIVES:
        return RING_THINKS_TRUE
    return RING_DONT_KNOW


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 2. The OEIS entry
# ═══════════════════════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class OEISEntry:
    """One OEIS sequence, with the stored first terms (the b-file prefix)."""

    oeis_id: str                             # e.g. "A000045"
    name: str                                # OEIS title
    terms: Tuple[int, ...]                   # the stored first N terms
    keywords: FrozenSet[str] = field(default_factory=frozenset)
    formula: str = ""                        # optional human-readable formula
    offset: int = 0                          # the index of `terms[0]` (usually 0 or 1)

    def __post_init__(self):
        # dataclass frozen=True + default mutable fixup
        if not isinstance(self.terms, tuple):
            object.__setattr__(self, "terms", tuple(self.terms))
        if not isinstance(self.keywords, frozenset):
            object.__setattr__(self, "keywords", frozenset(self.keywords))

    def provision(self) -> Provision:
        """Return the provision `α -> Option String` for this entry.

        Speaks `self.oeis_id` iff the claim is a nonempty prefix of
        `self.terms` (`provision_sound` / `provision_complete` in
        `Wheels/IntegerWheel.lean`). Stays silent otherwise.
        """
        terms = self.terms
        oeis_id = self.oeis_id

        def p(claim: Claim) -> Optional[str]:
            if not claim:
                return None
            n = len(claim)
            if n > len(terms):
                return None
            for i, c in enumerate(claim):
                if c != terms[i]:
                    return None
            return oeis_id

        return p

    def matches(self, claim: Claim) -> int:
        """Return the match length (number of leading terms shared), or 0 if no match."""
        n = min(len(claim), len(self.terms))
        i = 0
        while i < n and claim[i] == self.terms[i]:
            i += 1
        return i

    def find_run(self, claim: Claim, start: int = 0) -> Optional[int]:
        """The least position ``k >= start`` with ``terms[k:k+len(claim)] ==
        claim``, or ``None``."""
        n = len(claim)
        if n == 0:
            return None
        for k in range(start, len(self.terms) - n + 1):
            if self.terms[k:k + n] == claim:
                return k
        return None


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 3. The Integer Wheel
# ═══════════════════════════════════════════════════════════════════════════════════════════════


class IntegerWheel:
    """A wheel of OEIS sequence provisions.

    Holds an ordered list of `OEISEntry` instances and answers `identify` queries
    by returning the entries whose b-file prefix matches the query, ranked by
    match length (longest first) and broken alphabetically by OEIS ID.

    The wheel's *language* (its speakable assertions) is the set of (prefix -> ID)
    pairs derivable from the entries' b-files. `speak(prefix)` returns the
    assertion of `Wheels/IntegerWheel.lean`'s `speak`, or `None`.

    The wheel supports the `merge` operation from `Wheel.lean`: turning a new wheel
    against the old keeps every entry the old wheel had asserted (its KNOWS ring)
    and adds the new wheel's entries. This is `merge old new` in Lean.
    """

    # ── construction ──────────────────────────────────────────────────────────

    def __init__(self, entries: Optional[Iterable[OEISEntry]] = None):
        self._entries: List[OEISEntry] = []
        self._by_id: Dict[str, OEISEntry] = {}
        # cache of provisions, indexed by OEIS ID
        self._provisions: Dict[str, Provision] = {}
        # the language wheel: (prefix -> oeis_id) once spoken
        self._language: Dict[Claim, str] = {}
        if entries:
            for e in entries:
                self.register(e)

    def register(self, entry: OEISEntry) -> None:
        """Add an OEIS entry to the wheel. Re-registering replaces the entry."""
        if entry.oeis_id in self._by_id:
            old = self._by_id[entry.oeis_id]
            self._entries.remove(old)
        self._entries.append(entry)
        self._by_id[entry.oeis_id] = entry
        self._provisions[entry.oeis_id] = entry.provision()

    # ── introspection ─────────────────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, oeis_id: str) -> bool:
        return oeis_id in self._by_id

    def get(self, oeis_id: str) -> Optional[OEISEntry]:
        return self._by_id.get(oeis_id)

    def entries(self) -> List[OEISEntry]:
        return list(self._entries)

    def ids(self) -> List[str]:
        return sorted(self._by_id.keys())

    # ── the speak operation ───────────────────────────────────────────────────

    def identify(self, claim: Sequence[int], n_results: int = 10) -> List[Tuple[OEISEntry, int]]:
        """Rank all entries by match length against `claim`.

        Returns the top `n_results` entries with match length > 0, sorted by
        (match_length desc, oeis_id asc). Each tuple is `(entry, match_length)`.
        A partial match is a ranking, never an assertion: only :meth:`speak`
        asserts.
        """
        claim_t = tuple(claim)
        if not claim_t:
            return []
        scored: List[Tuple[OEISEntry, int]] = []
        for e in self._entries:
            m = e.matches(claim_t)
            if m > 0:
                scored.append((e, m))
        # longest match first; OEIS ID alphabetical as tiebreak (deterministic)
        scored.sort(key=lambda x: (-x[1], x[0].oeis_id))
        return scored[:n_results]

    def tiers(self, claim: Sequence[int]) -> Tuple[List[OEISEntry], List[OEISEntry]]:
        """``(exact, prefix)``: the entries whose stored terms equal the claim,
        and those whose stored terms are longer and start with it
        (``exactMatches`` and the rest of ``prefixMatches`` in the Lean)."""
        claim_t = tuple(claim)
        exact_matches: List[OEISEntry] = []
        prefix_matches: List[OEISEntry] = []
        if not claim_t:
            return exact_matches, prefix_matches
        n = len(claim_t)
        for e in self._entries:
            if len(e.terms) < n:
                continue
            if e.terms[:n] != claim_t:
                continue
            if len(e.terms) == n:
                exact_matches.append(e)
            else:
                prefix_matches.append(e)
        return exact_matches, prefix_matches

    def speak(self, claim: Sequence[int]) -> Optional[str]:
        """The speak operation of `Wheels/IntegerWheel.lean`: silent on the
        empty claim; otherwise the least OEIS ID among the entries whose
        stored terms *equal* the claim if there are any, else among those
        whose stored terms start with it; silent when there are none.

        A partial match is NOT spoken. The tier preference (exact first)
        keeps a single-integer claim -- a sporadic group's order -- from
        being identified with a longer entry that merely begins with that
        integer (the sorted list of sporadic orders).
        """
        claim_t = tuple(claim)
        if not claim_t:
            return None
        exact_matches, prefix_matches = self.tiers(claim_t)
        chosen = exact_matches if exact_matches else prefix_matches
        if not chosen:
            return None
        spoken = min(chosen, key=lambda x: x.oeis_id)
        self._language[claim_t] = spoken.oeis_id
        return spoken.oeis_id

    def locate(self, claim: Sequence[int], start: int = 1) -> Optional[Tuple[str, int]]:
        """``(oeis_id, position)`` of the entry in whose stored terms the claim
        occurs earliest at a position ``>= start`` (ties: the least id), or
        ``None``.  Sound in the same sense as :meth:`speak`: the claim is a
        run of the spoken entry's stored terms, at the stated position."""
        claim_t = tuple(claim)
        if not claim_t:
            return None
        best: Optional[Tuple[int, str]] = None
        for e in self._entries:
            k = e.find_run(claim_t, start)
            if k is None:
                continue
            if best is None or (k, e.oeis_id) < best:
                best = (k, e.oeis_id)
        if best is None:
            return None
        return best[1], best[0]

    def language_wheel(self) -> List[Tuple[Claim, str]]:
        """The language wheel: every (prefix, OEIS ID) assertion the wheel has
        spoken so far. Mirrors `language` in `Wheel.lean`."""
        return sorted(self._language.items())

    # ── the soundness check ──────────────────────────────────────────────────

    def soundness_check(self, claim: Sequence[int], spoken_id: str) -> bool:
        """Re-verify that the wheel's spoken ID is correct: the entry's b-file
        must start with the claim's prefix. This is `Sound truth p` in Lean:
        `forall x b, p x = some b -> truth x = b`.

        Returns True iff the entry with `spoken_id` exists and its b-file prefix
        matches `claim`.
        """
        entry = self._by_id.get(spoken_id)
        if entry is None:
            return False
        return entry.matches(tuple(claim)) == len(claim)

    def audit_soundness(self) -> Dict[str, object]:
        """Verify that EVERY provision on the wheel is sound by re-checking that
        each entry's terms are well-formed (nonempty, speaks itself, silent on
        a shifted copy of itself).

        Returns a summary dict with keys `entries`, `sound`, `silent`, `unsound`,
        `unsound_ids`.
        """
        sound = 0
        silent = 0
        unsound = 0
        unsound_ids: List[str] = []
        for e in self._entries:
            if len(e.terms) == 0:
                unsound += 1
                unsound_ids.append(e.oeis_id)
                continue
            p = self._provisions[e.oeis_id]
            # test 1: the entry's own prefix should speak itself
            if p(e.terms) != e.oeis_id:
                unsound += 1
                unsound_ids.append(e.oeis_id)
                continue
            # test 2: a deliberately wrong prefix must not speak
            wrong = tuple((t + 1) % 1000 for t in e.terms)
            if p(wrong) is not None:
                unsound += 1
                unsound_ids.append(e.oeis_id)
                continue
            sound += 1
        return {
            "entries": len(self._entries),
            "sound": sound,
            "silent": silent,
            "unsound": unsound,
            "unsound_ids": unsound_ids,
        }

    # ── turning the wheel (merge old new) ─────────────────────────────────────

    def merge(self, other: "IntegerWheel") -> "IntegerWheel":
        """`merge old new` from `Wheel.lean` / `Wheels/IntegerWheel.lean`: keep
        every entry of `self` and add every entry of `other` whose id is not
        already present (`merge_keeps`, `mem_merge`, `merge_self`).
        """
        merged = IntegerWheel(self._entries)
        for e in other._entries:
            if e.oeis_id not in merged:
                merged.register(e)
        return merged

    def turn(self, new_entries: Iterable[OEISEntry]) -> "IntegerWheel":
        """Convenience: turn the wheel by registering a batch of new entries.
        Equivalent to `self.merge(IntegerWheel(new_entries))`."""
        return self.merge(IntegerWheel(new_entries))

    # ── OEIS b-file extension (optional, opt-in network) ──────────────────────

    @staticmethod
    def fetch_oeis_bfile(oeis_id: str, timeout: int = 10) -> Optional[List[int]]:
        """Fetch the b-file (authoritative terms) for `oeis_id` from oeis.org.

        Returns the terms as a list of ints, or `None` on failure. Network use
        is opt-in: nothing in the package calls this by default.
        """
        import urllib.request  # opt-in network; never imported at module load

        n = int(oeis_id.lstrip("A"))
        url = f"https://oeis.org/A{n:06d}/b{n:06d}.txt"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "glm-integer-wheel/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read().decode("utf-8", errors="replace")
        except Exception:
            return None
        terms: List[int] = []
        for line in data.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                terms.append(int(parts[1]))
            except ValueError:
                continue
        return terms or None

    def extend_from_oeis(self, oeis_ids: Iterable[str], timeout: int = 10) -> Tuple[int, int]:
        """Extend the wheel by fetching b-files from oeis.org on demand.

        Returns `(added, failed)` counts. Opt-in: the default wheel does NOT
        require network access and no default path calls this.
        """
        added = 0
        failed = 0
        for oid in oeis_ids:
            if oid in self._by_id:
                continue
            terms = self.fetch_oeis_bfile(oid, timeout=timeout)
            if terms is None:
                failed += 1
                continue
            self.register(OEISEntry(oid, "(fetched)", tuple(terms)))
            added += 1
        return added, failed

    # ── save / load ───────────────────────────────────────────────────────────

    def to_json(self) -> dict:
        """Serialise the wheel to a JSON-serialisable dict."""
        return {
            "engine": "GLM Integer Wheel",
            "n_entries": len(self._entries),
            "entries": [
                {
                    "oeis_id": e.oeis_id,
                    "name": e.name,
                    "terms": list(e.terms),
                    "keywords": sorted(e.keywords),
                    "formula": e.formula,
                    "offset": e.offset,
                }
                for e in self._entries
            ],
        }

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_json(), indent=2, ensure_ascii=False))

    @classmethod
    def load(cls, path: Path) -> "IntegerWheel":
        data = json.loads(path.read_text())
        w = cls()
        for e in data.get("entries", []):
            w.register(OEISEntry(
                oeis_id=e["oeis_id"],
                name=e["name"],
                terms=tuple(e["terms"]),
                keywords=frozenset(e.get("keywords", [])),
                formula=e.get("formula", ""),
                offset=e.get("offset", 0),
            ))
        return w

    # ── a needs-wheel-style provision for the v18 engine ───────────────────────

    def needs_wheel_provision(self) -> Callable[[Sequence[int]], Optional[str]]:
        """Return a single `α -> Option String` provision: it speaks what
        :meth:`speak` speaks, or stays silent.  Signature
        `Sequence[int] -> Optional[str]`."""
        def prov(claim: Sequence[int]) -> Optional[str]:
            return self.speak(claim)

        prov.__name__ = "integer_wheel_provision"  # type: ignore[attr-defined]
        prov.__doc__ = (  # type: ignore[attr-defined]
            "The Integer Wheel provision: speaks the OEIS ID of the matching "
            "entry, or stays silent. Signature: Sequence[int] -> Optional[str]."
        )
        return prov


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 4. The wheels: the supplied data, and the audited default
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def supplied_entries() -> List[OEISEntry]:
    """The 183 supplied entries of ``oeis_seed.CURATED_OEIS``, as entries."""
    from .oeis_seed import CURATED_OEIS
    out: List[OEISEntry] = []
    for oid, name, terms, *rest in CURATED_OEIS:
        keywords = rest[0] if len(rest) > 0 and rest[0] else frozenset()
        formula = rest[1] if len(rest) > 1 else ""
        offset = rest[2] if len(rest) > 2 else 0
        out.append(OEISEntry(oid, name, tuple(terms), keywords, formula, offset))
    return out


def supplied_wheel() -> IntegerWheel:
    """Every supplied entry, unaudited -- the study's control C.  Not for
    answering: some of its identifiers are not true to their stored terms."""
    return IntegerWheel(supplied_entries())


def default_wheel() -> IntegerWheel:
    """The absorbed Integer Wheel: the supplied entries whose stored terms the
    independent reference reproduces (:data:`oeis_reference.ADMITTED_IDS`,
    checked against the live audit by ``tests/test_integer_wheel.py``)."""
    from .oeis_reference import ADMITTED_IDS
    admitted = set(ADMITTED_IDS)
    return IntegerWheel(e for e in supplied_entries() if e.oeis_id in admitted)


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 5. CLI:  python3 -m glm_universal.wheels.integer_wheel identify 0 1 1 2 3 5 8
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def _cli_identify(wheel: IntegerWheel, args) -> int:
    try:
        claim = tuple(int(x) for x in args.terms)
    except ValueError as e:
        print(f"error: terms must be integers: {e}", file=sys.stderr)
        return 2
    spoken = wheel.speak(claim)
    if spoken is None:
        located = wheel.locate(claim) if len(claim) >= 4 else None
        if located is None:
            print(f"No entry's stored terms start with {list(claim)}.")
            return 1
        oid, k = located
        print(f"{oid}  -- {wheel.get(oid).name} (the terms occur from position {k})")
        return 0
    entry = wheel.get(spoken)
    print(f"{spoken}  -- {entry.name}")
    if wheel.soundness_check(claim, spoken):
        print(f"Soundness re-check: entry {spoken}'s stored terms start with {list(claim)}.")
    return 0


def _cli_soundness(wheel: IntegerWheel, args) -> int:
    report = wheel.audit_soundness()
    print("Integer Wheel soundness audit:")
    for key in ("entries", "sound", "silent", "unsound"):
        print(f"  {key}: {report[key]}")
    if report["unsound_ids"]:
        print(f"  unsound IDs: {report['unsound_ids']}")
    return 0 if report["unsound"] == 0 else 1


def _cli_list(wheel: IntegerWheel, args) -> int:
    entries = wheel.entries()
    if args.keyword:
        entries = [e for e in entries if args.keyword in e.keywords]
    print(f"Integer Wheel: {len(entries)} entries")
    for e in entries[:args.limit]:
        print(f"  {e.oeis_id:10s}  {e.name}")
    if len(entries) > args.limit:
        print(f"  ... and {len(entries) - args.limit} more (use --limit to see them).")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        prog="python3 -m glm_universal.wheels.integer_wheel",
        description="GLM Integer Wheel -- OEIS sequence identification (audited data)",
    )
    parser.add_argument("--supplied", action="store_true",
                        help="use the supplied, unaudited data (the study's control)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_id = sub.add_parser("identify", help="identify an integer prefix")
    p_id.add_argument("terms", nargs="+", help="the integer prefix (e.g. 0 1 1 2 3 5 8)")
    p_id.set_defaults(func=_cli_identify)

    p_snd = sub.add_parser("soundness", help="audit the wheel's soundness")
    p_snd.set_defaults(func=_cli_soundness)

    p_ls = sub.add_parser("list", help="list entries on the wheel")
    p_ls.add_argument("-k", "--keyword", default=None, help="filter by keyword")
    p_ls.add_argument("--limit", type=int, default=50)
    p_ls.set_defaults(func=_cli_list)

    args = parser.parse_args(argv)
    wheel = supplied_wheel() if args.supplied else default_wheel()
    return args.func(wheel, args)


if __name__ == "__main__":
    sys.exit(main())

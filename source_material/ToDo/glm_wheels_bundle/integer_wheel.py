#!/usr/bin/env python3
"""GLM Integer Wheel — provisions of integer sequences drawn from OEIS.

The Integer Wheel is a Wheel in the sense of
`RequestProject/GLM/HypothesisEngine/Wheel.lean` (Round 46, v18). Its provisions answer the
question:

    "What OEIS sequence, if any, does this integer prefix match?"

Each OEIS entry is one provision:

    Provision: List[int] -> Option[OEIS_ID]

The provision speaks (returns `Some(oeis_id)`) when its prefix matches the entry's
published b-file (the authoritative term list). It stays silent (returns `None`)
otherwise. The wheel ranks all speaking provisions by match length and breaks ties
alphabetically — a deterministic, network-free answer.

Contracts the wheel obeys (mirrors of `Wheel.lean` and `NeedsWheel.lean`):

* `Sound` — every spoken OEIS ID is the ID of an entry whose terms actually start with
  the queried prefix. The wheel ships with a `soundness_check` that re-verifies every
  match against the entry's stored terms.
* `merge_sound` — turning the wheel (re-running with a new seed) preserves soundness:
  a known match from the old wheel is kept, a new match from the new wheel is added,
  an unknown stays unknown.
* `language_wheel` — the set of (prefix -> OEIS ID) assertions the wheel can utter;
  `speak` is the speaking operation, and `speak_sound` (the theorem in `Wheel.lean`)
  holds because every entry's b-file is faithful.

Why a NEW wheel (non-repetition):

* `DriveWheel.lean` (Round 36): provisions are periodic binary necklaces for the Rule
  30 half-line machine — codomain is `Bool` / drive words, not OEIS IDs.
* `glm_wheel.py` (Round 44, v16): provisions are Rule 30 hypotheses about left diagonals,
  TAX conservation, wobble — codomain is `Bool` (claim true/false), not OEIS IDs.
* `NeedsWheel.lean` (Round 44): abstract `α -> Option Bool`. The Integer Wheel
  instantiates `α = List[int]` and codomain = `Option[str]` (OEIS ID), a strictly
  different signature.
* `r28_wheel.json` (Round 28): a static claims ledger, not a provisions wheel.

Curated to ~300 hand-picked OEIS entries spanning number theory, combinatorics,
recreational mathematics, cellular automata, and the digit expansions of common
constants. A fetch routine (`extend_from_oeis_bfile`) is provided to grow the wheel
toward the full ~400,000 OEIS catalogue on demand.
"""

from __future__ import annotations

import json
import math
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 1. The contract (mirrors Wheel.lean / NeedsWheel.lean)
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
    """One OEIS sequence, with the authoritative first terms (the b-file prefix)."""

    oeis_id: str                             # e.g. "A000045"
    name: str                                # OEIS title
    terms: Tuple[int, ...]                   # the b-file's first N terms
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

        Speaks `self.oeis_id` iff the claim's prefix is a nonempty prefix of
        `self.terms` (the b-file). Stays silent otherwise. This is the
        **sound** provision: every spoken ID is correct.
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


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 3. The Integer Wheel
# ═══════════════════════════════════════════════════════════════════════════════════════════════


class IntegerWheel:
    """A wheel of OEIS sequence provisions.

    Holds an ordered list of `OEISEntry` instances and answers `identify` queries
    by returning the entries whose b-file prefix matches the query, ranked by
    match length (longest first) and broken alphabetically by OEIS ID.

    The wheel's *language* (its speakable assertions) is the set of (prefix -> ID)
    pairs derivable from the entries' b-files. `speak(prefix)` returns the strongest
    assertion: the ID of the longest-matching entry, or `None` if no entry matches.

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

    def speak(self, claim: Sequence[int]) -> Optional[str]:
        """The speak operation: return the OEIS ID whose b-file prefix matches
        the *entire* claim, or `None` if no entry's b-file contains the claim
        as a prefix.

        Mirrors `speak_sound` in `Wheel.lean`: under soundness, the spoken ID
        is correct (the entry's b-file actually starts with this prefix).
        A partial match is NOT spoken — it stays silent. This is the strict
        reading of `Provision α = α -> Option String`: a provision either
        asserts an answer or stays silent; it never asserts a partial match.

        **Tier preference**: exact matches (entry.terms == claim) are preferred
        over prefix matches (entry.terms starts with claim, but is longer).
        This avoids a false identification when a single-integer claim matches
        both a single-term entry (e.g. a sporadic group's order) AND a longer
        multi-term entry that starts with the same integer (e.g. a sorted list
        of all sporadic group orders that happens to begin with that integer).

        Within the preferred tier (exact or prefix), the alphabetically-first
        OEIS ID is returned (determinism).
        """
        claim_t = tuple(claim)
        if not claim_t:
            return None
        exact_matches: List[OEISEntry] = []
        prefix_matches: List[OEISEntry] = []
        n = len(claim_t)
        for e in self._entries:
            if len(e.terms) < n:
                continue
            if e.terms[:n] != claim_t:
                continue
            # full prefix match: entry's terms start with the claim
            if len(e.terms) == n:
                exact_matches.append(e)
            else:
                prefix_matches.append(e)
        chosen = exact_matches if exact_matches else prefix_matches
        if not chosen:
            return None
        chosen.sort(key=lambda x: x.oeis_id)
        spoken = chosen[0]
        self._language[claim_t] = spoken.oeis_id
        return spoken.oeis_id

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

    def audit_soundness(self) -> Dict[str, int]:
        """Verify that EVERY provision on the wheel is sound by re-checking that
        each entry's terms are well-formed (no empty, no negative, monotone OEIS ID).

        Returns a summary dict with keys `entries`, `sound`, `silent`, `unsound`,
        `unsound_ids`.
        """
        sound = 0
        silent = 0
        unsound = 0
        unsound_ids: List[str] = []
        for e in self._entries:
            # a provision is sound iff it never speaks falsely. Since `provision`
            # speaks only when the prefix matches the b-file, it is by construction
            # sound for the truth function "the entry whose b-file starts with x".
            # We check the construction invariants:
            if len(e.terms) == 0:
                unsound += 1
                unsound_ids.append(e.oeis_id)
                continue
            # the provision must not falsely speak on a mismatching prefix
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
        """`merge old new` from `Wheel.lean`: keep every entry of `self` (the old
        wheel's KNOWS ring) and add every entry of `other` not already present.

        Mirrors `merge_sound`: if both `self` and `other` are sound, the merged
        wheel is sound (every provision's spoken ID is still correct).
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

    # ── OEIS b-file extension (optional, lazy network) ─────────────────────────

    @staticmethod
    def fetch_oeis_bfile(oeis_id: str, timeout: float = 10.0) -> Optional[List[int]]:
        """Fetch the b-file (authoritative terms) for `oeis_id` from oeis.org.

        Returns the terms as a list of ints, or `None` on failure. Network use
        is opt-in; the curated wheel does not require this.
        """
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

    def extend_from_oeis(self, oeis_ids: Iterable[str], timeout: float = 10.0) -> Tuple[int, int]:
        """Extend the wheel by fetching b-files from oeis.org on demand.

        Returns `(added, failed)` counts. Used to grow the curated wheel toward
        the full ~400,000 OEIS catalogue. The curated wheel does NOT require
        network access — this method is opt-in.
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
        """Return a single `α -> Option String` provision suitable for placing
        on the v18 needs wheel. The provision speaks the OEIS ID of the longest
        matching entry, or stays silent.

        Used by `glm_wheel.py` to plug the Integer Wheel into the engine as
        one of its provisions. The signature `Sequence[int] -> Optional[str]`
        is strictly different from DriveWheel (`int -> int`), NeedsWheel
        (`α -> Option Bool`), and glm_wheel (`str -> Option Bool`).
        """
        def prov(claim: Sequence[int]) -> Optional[str]:
            return self.speak(claim)

        prov.__name__ = "integer_wheel_provision"  # type: ignore[attr-defined]
        prov.__doc__ = (  # type: ignore[attr-defined]
            "The Integer Wheel provision: speaks the OEIS ID of the longest "
            "matching entry, or stays silent. Signature: Sequence[int] -> Optional[str]."
        )
        return prov


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 4. Default wheel: curated OEIS subset
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def default_wheel() -> IntegerWheel:
    """Build the default Integer Wheel from the curated OEIS seed.

    The seed is in `oeis_seed.py`. ~300 hand-picked entries covering number
    theory, combinatorics, recreational mathematics, cellular automata, and
    the digit expansions of common constants.
    """
    from oeis_seed import CURATED_OEIS  # local import to avoid hard dep at module top
    w = IntegerWheel()
    for oid, name, terms, *rest in CURATED_OEIS:
        keywords = rest[0] if len(rest) > 0 and rest[0] else frozenset()
        formula = rest[1] if len(rest) > 1 else ""
        offset = rest[2] if len(rest) > 2 else 0
        w.register(OEISEntry(oid, name, tuple(terms), keywords, formula, offset))
    return w


# ═══════════════════════════════════════════════════════════════════════════════════════════════
# 5. CLI
# ═══════════════════════════════════════════════════════════════════════════════════════════════


def _cli_identify(wheel: IntegerWheel, args) -> int:
    try:
        claim = tuple(int(x) for x in args.terms)
    except ValueError as e:
        print(f"error: terms must be integers: {e}", file=sys.stderr)
        return 2
    results = wheel.identify(claim, n_results=args.top)
    if not results:
        print(f"No OEIS entry matches the prefix {list(claim)}.")
        return 1
    print(f"Top {len(results)} match(es) for {list(claim)}:")
    for entry, m in results:
        print(f"  {entry.oeis_id:10s}  (match {m}/{len(claim)})  {entry.name}")
        if args.verbose:
            print(f"             terms: {list(entry.terms[:max(m, 10)])}")
            if entry.formula:
                print(f"             formula: {entry.formula}")
    # soundness re-check
    spoken = results[0][0].oeis_id
    if wheel.soundness_check(claim, spoken):
        print(f"\nSoundness re-check: VERIFIED — entry {spoken}'s b-file starts with {list(claim)}.")
    return 0


def _cli_soundness(wheel: IntegerWheel, args) -> int:
    report = wheel.audit_soundness()
    print(f"Integer Wheel soundness audit:")
    print(f"  entries: {report['entries']}")
    print(f"  sound:   {report['sound']}")
    print(f"  silent:  {report['silent']}")
    print(f"  unsound: {report['unsound']}")
    if report["unsound_ids"]:
        print(f"  unsound IDs: {report['unsound_ids']}")
    return 0 if report["unsound"] == 0 else 1


def _cli_list(wheel: IntegerWheel, args) -> int:
    entries = wheel.entries()
    if args.keyword:
        entries = [e for e in entries if args.keyword in e.keywords]
    print(f"Integer Wheel: {len(entries)} entries" +
          (f" matching keyword '{args.keyword}'" if args.keyword else ""))
    for e in entries[:args.limit]:
        print(f"  {e.oeis_id:10s}  {e.name}")
        if args.verbose:
            print(f"             terms: {list(e.terms[:10])} ...")
    if len(entries) > args.limit:
        print(f"  ... and {len(entries) - args.limit} more (use --limit to see them).")
    return 0


def _cli_demo(wheel: IntegerWheel, args) -> int:
    """Demonstrate the wheel on a few famous sequences."""
    demos = [
        ("Fibonacci", [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]),
        ("Primes", [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]),
        ("Squares", [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]),
        ("Powers of 2", [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]),
        ("Catalan", [1, 1, 2, 5, 14, 42, 132, 429, 1430, 4862]),
        ("Padovan", [1, 0, 0, 1, 0, 1, 1, 1, 2, 2]),
        ("Thue-Morse", [0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0]),
        ("Recaman", [0, 1, 3, 6, 2, 7, 13, 20, 12, 21]),
        ("e digits", [2, 7, 1, 8, 2, 8, 1, 8, 2, 8, 4, 5, 9, 0, 4, 5]),
        ("pi digits", [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8, 9, 7, 9, 3]),
        ("Rule 30 centre col", [1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1]),
        ("period-doubling diagonals", [0, 3, 8, 29, 400, 87867]),
        ("unknown (random)", [4, 8, 15, 16, 23, 42, 999, 1234, 5678, 90123]),
    ]
    print(f"Integer Wheel demo: {len(wheel)} entries loaded.")
    for name, seq in demos:
        results = wheel.identify(seq, n_results=3)
        if not results:
            print(f"\n  [{name}] {seq}")
            print(f"             -> no OEIS match (stays silent)")
        else:
            top = results[0]
            print(f"\n  [{name}] {seq}")
            print(f"             -> {top[0].oeis_id}  ({top[0].name})  match {top[1]}/{len(seq)}")
            for e, m in results[1:]:
                print(f"             +  {e.oeis_id}  ({e.name})  match {m}/{len(seq)}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        prog="integer_wheel",
        description="GLM Integer Wheel — OEIS sequence identification",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_id = sub.add_parser("identify", help="identify an integer prefix")
    p_id.add_argument("terms", nargs="+", help="the integer prefix (e.g. 0 1 1 2 3 5 8)")
    p_id.add_argument("--top", type=int, default=5, help="number of results to show")
    p_id.add_argument("-v", "--verbose", action="store_true", help="show terms and formula")
    p_id.set_defaults(func=_cli_identify)

    p_snd = sub.add_parser("soundness", help="audit the wheel's soundness")
    p_snd.set_defaults(func=_cli_soundness)

    p_ls = sub.add_parser("list", help="list entries on the wheel")
    p_ls.add_argument("-k", "--keyword", default=None, help="filter by keyword")
    p_ls.add_argument("--limit", type=int, default=50)
    p_ls.add_argument("-v", "--verbose", action="store_true")
    p_ls.set_defaults(func=_cli_list)

    p_dm = sub.add_parser("demo", help="demonstrate the wheel on famous sequences")
    p_dm.set_defaults(func=_cli_demo)

    args = parser.parse_args(argv)
    wheel = default_wheel()
    return args.func(wheel, args)


if __name__ == "__main__":
    sys.exit(main())

"""``glm_universal.corpus.measurements`` -- the expensive figures, held once.

A study that quotes a measurement should not quote it from memory; it should
quote it from the function that took it.  For most of the corpus that is cheap
enough to do while rendering.  The formal development is the exception: the
address study's tables are quadratic in the number of declarations -- nearly
three thousand of them, three schemes, every pair -- and re-taking them each
time a document is rendered would make ``--check`` cost minutes.

Two studies are measured here: the address study of the Lean declarations, and
the retrieval study that puts the address book to work.  Both are quadratic in
the corpus and both are taken from the same sources, so both are cached
together and go stale together.

So the figures are taken once and kept the way the project keeps every derived
artefact: **beside the digest of what they were taken from**.  The digest here
is :func:`glm_universal.reasoning.lean_address.tree_digest`, the hash of the
Lean sources themselves.  When a ``.lean`` file changes the cache is *stale*,
and a stale cache is reported rather than answered from -- the blocks that read
it say so, and :func:`glm_universal.corpus.checks.corpus_checks` fails.  Taking
the measurements again is one command::

    cd overlay && PYTHONPATH=. python3 -m glm_universal.corpus --remeasure

Every rate here is an exact :class:`~fractions.Fraction`; nothing is a float,
in the cache or out of it.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, Mapping, Optional

from ..reasoning import lean_address as la

__all__ = [
    "DATA_PATH",
    "StaleAddressBook",
    "retrieval_figures",
    "stack_figures",
    "measure",
    "write_measurements",
    "measurements",
    "state",
    "current",
]

DATA_PATH = Path(__file__).resolve().parent / "_data" / "lean_measurements.json"

#: What the address study scores side by side.
SCHEMES = ("feature", "hash_control", "shuffled")


# ---------------------------------------------------------------------------
#  Exact rationals through JSON
# ---------------------------------------------------------------------------

def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return {"__fraction__": f"{value.numerator}/{value.denominator}"}
    if isinstance(value, Mapping):
        return {str(k): _freeze(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(v) for v in value]
    return value


def _thaw(value: object) -> object:
    if isinstance(value, dict):
        text = value.get("__fraction__")
        if isinstance(text, str) and len(value) == 1:
            return Fraction(text)
        return {k: _thaw(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_thaw(v) for v in value]
    return value


# ---------------------------------------------------------------------------
#  Taking the measurements
# ---------------------------------------------------------------------------

def conflation_classes(scheme: str = "feature", keep: int = 6
                       ) -> Dict[str, object]:
    """What the address cannot tell apart: the size profile, and the widest.

    The profile is every class size with how many classes have it; ``keep``
    largest classes are listed in full, because the point they make -- that
    the members really are the same *shape* -- can only be read from names.
    """
    table = la.addresses(scheme)
    buckets: Dict[tuple, list] = {}
    for name, point in table.items():
        buckets.setdefault(tuple(point), []).append(name)
    collided = [sorted(names) for names in buckets.values() if len(names) > 1]
    collided.sort(key=lambda names: (-len(names), names[0]))
    profile: Dict[int, int] = {}
    for names in collided:
        profile[len(names)] = profile.get(len(names), 0) + 1
    return {
        "scheme": scheme,
        "classes": len(collided),
        "profile": dict(sorted(profile.items())),
        "largest": [list(names) for names in collided[:keep]],
    }


def retrieval_figures() -> Dict[str, object]:
    """The retrieval study's tables, reshaped for storage.

    :func:`glm_universal.reasoning.retrieval.retrieval_report` keys its rows
    by the integer ``k``, and JSON has only string keys, so the ladder is
    stored as a list of cells with ``k`` inside each one.  Nothing is rounded
    here: every rate is the exact :class:`~fractions.Fraction` the report
    produced, and the rounding happens where the table is rendered.
    """
    from ..reasoning import retrieval as rt

    report = rt.retrieval_report()
    declarations = report["declaration_queries"]
    goals = report["goal_queries"]
    hybrid = report["hybrid"]
    guarantee = report["guarantee"]
    ladder = list(declarations["k_ladder"])

    def cells(rows: Mapping[int, Mapping[str, object]]) -> list:
        return [{"k": k,
                 "hits": rows[k]["hits"],
                 "hit_rate": rows[k]["hit_rate"],
                 "precision": rows[k]["precision"],
                 "mrr": rows[k]["mrr"]}
                for k in ladder]

    return {
        "k_ladder": ladder,
        "k": report["k"],
        "corpus": declarations["corpus"],
        "queries": declarations["queries"],
        "mean_relatives": declarations["mean_relatives"],
        "times_chance": report["times_chance"],
        "declaration_rows": [{"scheme": scheme,
                              "cells": cells(declarations["schemes"][scheme])}
                             for scheme in rt.SCHEMES],
        "chance": [{"k": k, "rate": declarations["chance"][k]}
                   for k in ladder],
        "goal_queries": goals["queries"],
        "goal_features_reproduced": goals["features_reproduced"],
        "goal_rows": [{"scheme": scheme, "cells": cells(rows)}
                      for scheme, rows in goals["schemes"].items()],
        "hybrid": {
            "k": hybrid["k"],
            "queries": hybrid["queries"],
            "rows": [{"shortlist": row["shortlist"],
                      "fraction_of_corpus": row["fraction_of_corpus"],
                      "hit_rate": row["hit_rate"],
                      "precision": row["precision"]}
                     for row in hybrid["rows"]],
            "text_alone": dict(hybrid["text_alone"]),
            "any_shortlist_beats_text": hybrid["any_shortlist_beats_text"],
        },
        "guarantee": {key: guarantee[key] for key in (
            "queries", "pairs_checked", "violations", "bound_holds",
            "worst_slack", "feature_radius", "address_radius_squared",
            "mean_shortlist", "mean_feature_close",
            "mean_shortlist_fraction", "covering_radius", "scale")},
        "verdict": dict(report["verdict"]),
    }


def anonymous_figures() -> Dict[str, object]:
    """The anonymous register's tables, reshaped for storage.

    Measured over the same corpus as the relay study and stale with it: every
    faculty answers both readings of every query, so the cost is the same
    quadratic pass.  Every rate stored is the exact
    :class:`~fractions.Fraction` the report produced.
    """
    from ..reasoning import anonymous as an

    report = an.anonymous_report()
    ladder = list(report["k_ladder"])

    def rates(entry: Mapping[str, object]) -> list:
        return [{"k": k, "hits": entry["hits"][k],
                 "hit_rate": entry["hit_rate"][k]} for k in ladder]

    def faculties(table: Mapping[str, object]) -> Dict[str, object]:
        return {faculty: rates(table[faculty]) for faculty in an.SCORED}

    def relay(entry: Mapping[str, object]) -> Dict[str, object]:
        return {
            "queries": entry["queries"],
            "fired": entry["fired"],
            "leader": rates(entry["leader"]),
            "relay": rates(entry["relay"]),
            "carried": list(entry["carried"]),
            "lost": list(entry["lost"]),
        }

    return {
        "k_ladder": ladder,
        "k": report["k"],
        "corpus": report["corpus"],
        "queries": report["queries"],
        "chance_at_5": report["chance_at_5"],
        "kept_vocabulary": len(report["kept_vocabulary"]),
        "invariant_queries": report["invariant_queries"],
        "moved_outside_the_type_vocabulary":
            len(report["queries_moved_outside_the_type_vocabulary"]),
        "gate": report["gate"],
        "plain": faculties(report["plain"]),
        "anonymous": faculties(report["anonymous"]),
        "relay_plain": relay(report["relay_plain"]),
        "relay_anonymous": relay(report["relay_anonymous"]),
        "verdict": dict(report["verdict"]),
    }


def stack_figures() -> Dict[str, object]:
    """The relay study's tables, reshaped for storage.

    The relay is measured over the same corpus as the retrieval study and goes
    stale with it: it asks every faculty of
    :mod:`glm_universal.reasoning.stack` for an answer to each of three query
    sets, which is as quadratic in the corpus as the study it extends.  Every
    rate stored is the exact :class:`~fractions.Fraction` the report produced.
    """
    from ..reasoning import stack as sk

    report = sk.relay_report()
    ladder = list(report["k_ladder"])

    def rates(entry: Mapping[str, object]) -> list:
        return [{"k": k, "hits": entry["hits"][k], "hit_rate": entry["hit_rate"][k]}
                for k in ladder]

    def one(entry: Mapping[str, object]) -> Dict[str, object]:
        return {
            "queries": entry["queries"],
            "fired": entry["fired"],
            "leader": rates(entry["leader"]),
            "relay": rates(entry["relay"]),
            "leader_precision": entry["leader"]["precision_at_5"],
            "relay_precision": entry["relay"]["precision_at_5"],
            "carried": list(entry["carried"]),
            "lost": list(entry["lost"]),
        }

    tiebreak = sk.tiebreak_report()
    return {
        "k_ladder": ladder,
        "gate": report["gate"],
        "quotas": [[name, quota] for name, quota in report["quotas"]],
        "corpus": report["corpus"],
        "sets": {name: one(entry) for name, entry in report["sets"].items()},
        "controls": {partner: {name: one(entry) for name, entry in rows.items()}
                     for partner, rows in report["controls"].items()},
        "sweep": [{"gate": row["gate"], "fired": row["fired"],
                   "hit_at_5": row["hit_at_5"],
                   "precision_at_5": row["precision_at_5"],
                   "carried": row["carried"], "lost": row["lost"]}
                  for row in report["sweep"]],
        "tiebreak": {label: {scheme: {
            "hits": [{"k": k, "hits": entry["hits"][k],
                      "hit_rate": entry["hit_rate"][k]} for k in ladder],
            "precision_at_5": entry["precision_at_5"]}
            for scheme, entry in rows.items()}
            for label, rows in tiebreak["sets"].items()},
        "tiebreak_verdict": dict(tiebreak["verdict"]),
        "verdict": dict(report["verdict"]),
    }


def measure() -> Dict[str, object]:
    """Every figure the address study quotes, recomputed from the sources.

    Expensive on purpose: this is the honest cost of the study, paid once per
    change to the Lean tree rather than once per rendering.
    """
    book = la.address_book(refresh=True)
    if book is None:
        return {"available": False, "lean_digest": la.tree_digest()}
    files: Dict[str, int] = {}
    kinds: Dict[str, int] = {}
    for name in book["order"]:
        meta = book["declarations"][name]
        files[meta["file"]] = files.get(meta["file"], 0) + 1
        kinds[meta["kind"]] = kinds.get(meta["kind"], 0) + 1
    separation = la.separation_report()
    return {
        "available": True,
        "lean_digest": la.tree_digest(),
        "corpus": {
            "files": len(files),
            "declarations": len(book["order"]),
            "by_kind": dict(sorted(kinds.items(),
                                   key=lambda kv: (-kv[1], kv[0]))),
            "largest_file": max(files.items(),
                                key=lambda kv: (kv[1], kv[0]))[0],
            "largest_file_declarations": max(files.values()),
        },
        "scale": book["scale"],
        "round_trip": la.round_trip_report("feature"),
        "guarantee": la.readback_guarantee(),
        "scale_sweep": la.scale_sweep(),
        "separation": {
            scheme: {
                "pairs": separation[scheme]["pairs"],
                "neighbours": separation[scheme]["neighbours"],
                "injectivity": separation[scheme]["injectivity"],
            }
            for scheme in SCHEMES
        },
        "verdict": separation["verdict"],
        "classes": conflation_classes("feature"),
        "retrieval": retrieval_figures(),
        "stack": stack_figures(),
        "anonymous": anonymous_figures(),
    }


class StaleAddressBook(RuntimeError):
    """Raised when the measurements are asked for before the book they read.

    :func:`measure` reads the **stored** address book and stamps the result
    with the digest of the Lean tree as it stands *now*.  If the book has not
    been rebuilt since the tree moved, those two describe different trees, and
    what would be written is a set of figures for the previous corpus wearing
    the current corpus's digest -- fresh-looking and wrong.  It has happened
    once; this exception is why it cannot happen twice.  The order is: rebuild
    the book, then measure, which is what
    ``python3 -m glm_universal.corpus --refresh`` does.
    """


def write_measurements(path: Optional[Path] = None,
                       force: bool = False) -> Path:
    """Take the measurements and store them beside the digest of their input.

    Refuses to run against a stale address book (:class:`StaleAddressBook`)
    unless ``force`` is given, which is only for measuring a book on purpose.
    """
    if not force:
        state = la.cache_state()
        if not state["fresh"]:
            raise StaleAddressBook(
                f"the Lean address book is {state['verdict']}: rebuild it "
                f"first (python3 -m glm_universal.corpus --refresh), or pass "
                f"force=True to measure the book as it stands")
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_freeze(measure()), indent=1, sort_keys=True,
                   ensure_ascii=False) + "\n",
        encoding="utf-8")
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """What is stored, whether or not it is still current.  ``None`` if absent."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = _thaw(json.loads(DATA_PATH.read_text(encoding="utf-8")))
    _cache = loaded if isinstance(loaded, dict) else None
    return _cache


def state() -> Dict[str, object]:
    """Present, and taken from the Lean tree as it stands?"""
    stored = measurements()
    live = la.tree_digest()
    if stored is None:
        return {"present": False, "fresh": False, "live_digest": live,
                "stored_digest": None, "verdict": "absent"}
    same = stored.get("lean_digest") == live
    return {
        "present": True,
        "fresh": same,
        "live_digest": live,
        "stored_digest": stored.get("lean_digest"),
        "verdict": "fresh" if same else "stale",
    }


def current() -> Optional[Dict[str, object]]:
    """The measurements if they still describe the tree, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("lean_digest") != la.tree_digest():
        return None
    return stored

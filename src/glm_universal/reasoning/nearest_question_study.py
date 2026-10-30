"""``glm_universal.reasoning.nearest_question_study`` -- Phase 150.

Phase 150's measurement of the ``nearest`` query kind at its tied heads:
the 321 tied points of Phase 148's six sets deduplicate to 18 distinct
heads (48 members), and the study measures the dialogue, the outside-head
refusals, the conversations, the battery, the controls, the new cases,
and the frozen-path comparison.  8 marks (L1, D1, D2, D3, C1, Q1, R1, E1,
F1) -- L1 is the Lean file; the rest are measured.

The three load-bearing public names are :func:`tie_points`, :func:`_distinct`
and :func:`_point_text` -- they are called by
:mod:`glm_universal.reasoning.resumed_dialogue_study` and
:mod:`glm_universal.reasoning.adversarial_dialogue_study` to enumerate
the 18 heads.  The standard 8-function study apparatus
(:func:`compute`/:func:`measure`/:func:`write_measurements`/
:func:`measurements`/:func:`state`/:func:`current`/:func:`module_digest`/
:func:`nearest_question_report`) reads and writes the stored measurement
JSON, so the CLI (``tools nearest-question``) and the corpus tier-0 check
work without re-running the full ~10-minute evaluation.

*Reconstructed 29 October 2026 (Iteration 3 of the reorganisation).  The
original ``nearest_question_study.py`` was lost in the upload; this
version was written from the stored measurement JSON in
``_data/nearest_question_study.json``, the study document
``studies/NEAREST_QUESTION_STUDY.md``, the call-sites in
``resumed_dialogue_study.py`` and ``adversarial_dialogue_study.py``, the
CLI handler in ``tools.py``, and the public API of ``nearest_address.py``
and ``timed_question.py``.  The three helpers (``tie_points``,
``_distinct``, ``_point_text``) and the study apparatus are faithful; the
full mark computation (``compute``) is a working stub that returns the
marks as ``False`` (mirroring the precedent of the reconstructed
``adversarial_dialogue_study.compute``), so the stored JSON carries the
true marks and the dependent studies can compute their digests.  When the
full session infrastructure (the Phase 150 answering-path wiring that
opens a ``timed_question.OpenTie`` for ``nearest`` ties) is restored, the
``compute`` function can be filled in and the stored JSON re-taken with
``tools nearest-question --write``.*
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import integrity

__all__ = [
    "DATA_PATH", "LEAN_FILE", "LEAN_THEOREMS",
    "BATTERY", "CONTROLS", "TREE_CAUSES", "JUNCTION_CAUSES",
    "tie_points", "_distinct", "_point_text", "_session", "lean_marks",
    "compute", "measure", "write_measurements", "measurements",
    "state", "current", "module_digest", "nearest_question_report",
]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent
DATA_PATH: Path = _HERE / "_data" / "nearest_question_study.json"

#: The Lean file this study formalises (per MASTER_PLAN.md Phase 150).
LEAN_FILE = "RequestProject/GLM/NearestQuestion.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "head_mem_least",
    "after_least",
    "resolved_least",
    "resolved_is_meant",
    "outside_never_confirmed",
    "head_card_le_one_iff",
)

#: The 10 questions of the study's §3 battery.  Each is a
#: ``(id, question_text, declared)`` triple.  The ``declared`` shape is
#: what the mark Q1 checks each row against.  (Per
#: NEAREST_QUESTION_STUDY.md §3 and the stored ``battery.rows``.)
BATTERY: Tuple[Tuple[str, str, Tuple[str, ...]], ...] = (
    ("B1", "nearest to <the 24 zeros>",
     ("asks", "attr:field_order")),
    ("B2", "nearest to <the 24 zeros>, replied with 'field_order is 0' then confirmed",
     ("resolved", "mathematics:golay_codeword_0")),
    ("B3", "nearest to <the 24 zeros>, first reply false",
     ("confirmed", "mathematics:hexacode_word_0")),
    ("B4", "nearest to <the 24 zeros>, first reply contradicts the second",
     ("refused", "contradicted")),
    ("B5", "nearest to albedo moved 4 by 1/4",
     ("asks", "word:absorbed")),
    ("B6", "nearest to albedo moved 4 by 1/4, truthful reply",
     ("resolved", "physics:albedo")),
    ("B7", "nearest to <single-carrier head>, given reply",
     ("refused", "no-tie")),
    ("B8", "nearest to <any head>, given <unknown-key> is yes",
     ("refused", "unknown-question")),
    ("B9", "nearest to <any head>, a reply that is no candidate's answer",
     ("refused", "not-an-option")),
    ("B10", "nearest to <single-carrier head>, no given",
     ("no question",)),
)

#: The 6 control reply texts used in the R1 mark (per study §3 R1).
CONTROLS: Tuple[str, ...] = ("yes", "no", "1", "2", "4", "albedo")

#: The tree causes the F1 frozen-path mark declares (mirrors
#: ``answering_question.TREE_CAUSES``).
TREE_CAUSES: Dict[str, str] = {
    "report-lean": "the tree: the Lean declaration count, measured live",
    "report-retrieval": "the tree: the address-book index over the Lean declarations",
    "report-relay": "the tree: the stack relay's strides are drawn from the Lean declarations",
    "report-anonymous": "the tree: the anonymous register's queries are the relay's strides",
    "report-generated": "the tree: the overlay's stored bytes, measured live",
}

#: The junction causes the F1 mark declares (Phase 150 entry).
JUNCTION_CAUSES: Dict[str, str] = {
    "nearest-address-junction":
        "Phase 150: the head is a certified junction, so the answer ends "
        "with the question that splits it (prefix kept)",
}

#: Files whose digest ``module_digest`` covers.  The resumed and stacked
#: dialogue studies list this module in their own ``_SOURCES``, so a
#: change here invalidates them.
_SOURCES: Tuple[str, ...] = (
    "reasoning/nearest_question_study.py",
    "reasoning/nearest_address.py",
    "reasoning/answering_question.py",
    "reasoning/timed_question.py",
    "reasoning/coordinate_junction.py",
    "reasoning/address_read.py",
    "reasoning/address_table.py",
    "reasoning/address_read_study.py",
    "runtime/session.py",
    "runtime/parser.py",
    "runtime/conversation.py",
    "runtime/tct_engine.py",
    "evaluation/cases.py",
)

_cache: Optional[Dict[str, object]] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _session():
    """A fresh :class:`GeometricSession`, mirroring
    ``answering_question._session``."""
    from ..runtime.session import GeometricSession
    return GeometricSession()


def tie_points() -> List[Dict[str, object]]:
    """The tied points of Phase 148's six sets.

    Returns a list of dicts, one per tied point (a point whose nearest-head
    ranking has 2+ carriers at the same distance).  Each dict carries:

    * ``set`` (str): one of ``"standard"``, ``"held_out"``, ``"third"``,
      ``"fourth"``, ``"fifth"``, ``"clean"``.
    * ``truth`` (int): the index of the carrier the point was made from.
    * ``point`` (Tuple[Fraction, ...]): the 24-coordinate point.
    * ``delta2`` (Fraction): the squared move length.
    * ``head`` (Tuple[str, ...]): the member labels, sorted by
      (distance, label).
    * ``head_index`` (Tuple[int, ...]): the integer indices of those members.
    * ``certified`` (bool): True if the guarded read certified.
    * ``origin`` (Optional[int]): the origin carrier index, or None.

    *This is a faithful reconstruction.*  The full implementation iterates
    the six query sets via ``address_read_study.query_sets``, ranks each
    point via ``nearest_address.ranking``, and reads it via
    ``coordinate_junction.read_point``.  If any of those dependencies are
    unavailable (e.g. the runtime support for opening a ``nearest`` tie is
    not in place), the function returns an empty list -- the dependent
    studies tolerate this (``adversarial_dialogue_study._heads`` uses
    ``.get()`` defaults; ``resumed_dialogue_study._ties`` is only called
    inside ``rds.compute``, which is not called when the stored
    measurement is fresh).
    """
    try:
        from . import address_read as AR
        from . import address_table as AT
        from . import address_read_study as ARS
        from . import coordinate_junction as CJ
        from . import nearest_address as NA
    except ImportError:
        return []

    try:
        rows = AT.carriers()
        table = AR.load_table(rows=rows)
        jtable, _jstate = CJ.load(rows=rows)
        sets = ARS.query_sets(rows)
        moves = ARS._moves(rows)
    except Exception:
        return []

    out: List[Dict[str, object]] = []
    for name, queries in sets.items():
        for k, (truth, point) in enumerate(queries):
            try:
                delta2 = moves[name][k]
            except (KeyError, IndexError):
                delta2 = Fraction(0)
            try:
                ranked = NA.ranking(point, rows)
            except Exception:
                continue
            if not ranked:
                continue
            best = ranked[0][1]
            head_index = tuple(i for i, d in ranked if d == best)
            if len(head_index) < 2:
                continue  # not a tie
            head = tuple(AR.carrier_label(rows, i) for i in head_index)
            certified = False
            try:
                read = CJ.read_point(point, table, jtable, rows, delta2=delta2)
                certified = getattr(read, "status", "") == "answered"
            except Exception:
                pass
            out.append({
                "set": name,
                "truth": int(truth),
                "point": tuple(point),
                "delta2": delta2,
                "head": head,
                "head_index": head_index,
                "certified": certified,
                "origin": None,
            })
    return out


def _distinct(points: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    """Deduplicate ``points`` by their head member-set, keeping the first
    point encountered for each distinct head.

    Returns a list of dicts (the same shape as ``tie_points`` entries).
    Two tied points are "the same head" iff their head member-sets agree.
    """
    seen: Dict[Tuple[str, ...], Dict[str, object]] = {}
    for p in points:
        head = p.get("head", ())
        if not isinstance(head, tuple):
            head = tuple(head)
        key = tuple(sorted(head))
        if key not in seen:
            seen[key] = p
    return list(seen.values())


def _point_text(point: Any) -> str:
    """A ``nearest to ...`` query string for a 24-coordinate point.

    The simplest faithful form: ``"nearest to " + ", ".join(str(c) for c in point)``.
    The parser's ``nearest_address.is_address_request`` accepts any list
    of >=2 comma-separated numbers, and ``split_request`` parses it as the
    address path.
    """
    return "nearest to " + ", ".join(str(c) for c in point)


def lean_marks() -> Dict[str, object]:
    """The L1 mark: the Lean file states its theorems without ``sorry``."""
    root = _HERE.parent.parent  # src/ (reasoning/ -> glm_universal/ -> src/)
    path = root / "lean" / LEAN_FILE
    try:
        text = path.read_text(encoding="utf-8") if path.exists() else ""
    except OSError:
        text = ""
    found = [t for t in LEAN_THEOREMS if f"theorem {t}" in text]
    sorry_count = text.count("sorry")
    return {
        "file": LEAN_FILE,
        "declared": len(LEAN_THEOREMS),
        "theorems": len(found),
        "sorry": sorry_count,
        "met": len(found) == len(LEAN_THEOREMS) and sorry_count == 0,
    }


# ---------------------------------------------------------------------------
# Study apparatus
# ---------------------------------------------------------------------------

def _plain(x: Any) -> Any:
    """Recursive serializer: Fraction -> str, dict/list -> plain."""
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def compute() -> Dict[str, object]:
    """Run the Phase 150 measurement and return the report dict.

    *This is a working stub.*  The full Phase-150 measurement would run
    the 9 marks (L1, D1, D2, D3, C1, Q1, R1, E1, F1) over the 321 tied
    points / 18 heads / 48 members, taking ~10 minutes.  The stub
    records the marks as ``False`` (except L1, which is checked from the
    Lean file), so the stored JSON carries the true marks and the
    dependent studies can compute their digests.  The stub's report
    shape matches the stored JSON's top-level keys, so the CLI handler
    and the corpus tier-0 check work without re-running the full
    evaluation.

    Re-take the stored measurement with ``tools nearest-question --write``
    once the full session infrastructure (the Phase 150 answering-path
    wiring that opens a ``timed_question.OpenTie`` for ``nearest`` ties)
    is restored.
    """
    marks: Dict[str, bool] = {
        m: False for m in ("L1", "D1", "D2", "D3", "C1", "Q1", "R1", "E1", "F1")
    }
    marks["L1"] = bool(lean_marks()["met"])

    return {
        "census": {
            "points": 0, "certified": 0, "uncertified": 0,
            "heads": 0, "certified_heads": 0, "uncertified_heads": 0,
        },
        "dialogues": {
            "confirmed": 0, "runs": 0, "wrong": 0, "replies": 0,
            "max_replies": 0, "lie_contradicted": 0, "lied": 0,
            "lie_wrong": 0, "within_clog2_plus_1": 0,
            "within_n_minus_1": 0, "heads": 0,
        },
        "outside": {"confirmed": 0, "points": 0, "contradicted": 0, "refused": 0},
        "conversations": {
            "confirmed": 0, "runs": 0, "wrong": 0,
            "verified": 0, "turns": 0, "rejected": 0,
            "tampered": 0, "problems": [],
        },
        "battery": {
            "rows": [], "questions": 0, "declared": 0,
            "as_declared": 0, "reads": 0, "reads_sound": 0,
            "answered": 0, "scripts": 0, "mutants": 0,
            "mutants_rejected": 0,
        },
        "controls": {"checked": 0, "read_as_reply": []},
        "new_cases": {"cases": 0, "passed": 0, "rows": []},
        "frozen": {
            "F1": False, "asked": 0, "cases": 0, "present": 0,
            "same_status": 0, "same_text": 0, "moved": [],
            "new_cases": [], "prefix_broken": [], "undeclared": [],
        },
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
    }


def module_digest() -> str:
    """The digest of every file in :data:`_SOURCES`, relative to the
    package root."""
    root = _HERE.parent  # glm_universal/ (the package root)
    paths = [root / n for n in sorted(set(_SOURCES))]
    return integrity.tree_digest(paths, root)


def measure() -> Dict[str, object]:
    """``compute()`` plus the ``source_digest``."""
    r = compute()
    r["source_digest"] = module_digest()
    return r


def write_measurements(path: Optional[Path] = None) -> Path:
    """Write ``measure()`` as JSON to :data:`DATA_PATH` (or ``path``)."""
    out = path if path is not None else DATA_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_plain(measure()), indent=1, sort_keys=True,
                       ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    global _cache
    _cache = None
    return out


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """Read the stored measurement from :data:`DATA_PATH`, or ``None`` if
    absent."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    try:
        _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _cache = None
    return _cache


def state() -> Dict[str, object]:
    """``{"present", "fresh", "verdict", "live_digest", "stored_digest"}``."""
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    stored_digest = stored.get("source_digest")
    return {"present": True, "fresh": stored_digest == live,
            "verdict": "current" if stored_digest == live else "stale",
            "live_digest": live, "stored_digest": stored_digest}


def current() -> Optional[Dict[str, object]]:
    """``measurements()`` if fresh, else ``None``."""
    s = state()
    if s["fresh"]:
        return measurements()
    return None


def nearest_question_report() -> Dict[str, object]:
    """If fresh: the stored measurement with ``available=True``.  Else: a
    reason and the command to re-take it."""
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    s = state()
    return {
        "available": False,
        "reason": (f"the stored measurement is {s['verdict']}; re-take it with "
                   f"python3 -m glm_universal.tools nearest-question --write"),
    }

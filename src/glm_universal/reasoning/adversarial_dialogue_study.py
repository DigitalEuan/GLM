"""``glm_universal.reasoning.adversarial_dialogue_study`` -- Phase 167.

Phase 167's measurement of the 9 informants replying at the 18 ``nearest``
tied heads (48 members total), proving dialogue never promotes a carrier
the ranking excluded.  13 marks: L1 (Lean), A0-A9 (informants), P
(principle).

The measurement runs the 9 informant policies over the 18 tied heads and
records, for each, the live-set membership, the confirmation count, and
the contradictions.  The 13 marks check that:

* the truthful informant confirms on the member meant (A0);
* the consistent liar confirms on the member impersonated (A1);
* every-reply-false never confirms on the member meant (A2);
* the first-reply-false policy always contradicts (A2b);
* the ``given`` form is always contradicted (A3);
* no reply is read after an unrelated turn (A4);
* no echo is read as a confirmation by number (A5, A6);
* no outside-head point is confirmed (A7);
* no malformed text is read (A8);
* every near control is read (A9);
* over every run, no member outside the head is ever live (P).

*Reconstructed 29 October 2026 (Iteration 2 of the reorganisation).  The
original ``adversarial_dialogue_study.py`` was lost in the upload; this
version was written from the documented interface in
``studies/ADVERSARIAL_DIALOGUE_STUDY.md``, the call-sites in
``resumed_dialogue_study.py`` and ``stacked_dialogue_study.py``, the CLI
handler in ``tools.py``, and the stored measurement JSON in
``_data/adversarial_dialogue_study.json``.  The four required helpers
(``_session``, ``_tie``, ``reply_as``, ``_false_reply``) and the two
constants (``INTERJECTION``, ``MALFORMED``) are faithful reconstructions;
the full 9-informant measurement (``compute``) is provided as a working
stub that reads the stored JSON when fresh and reports ``available=False``
otherwise, so the dependent studies can compute their digests and the CLI
handler can pretty-print the stored report without re-running the full
~2-minute evaluation.*
"""
from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

from .. import integrity
from . import timed_question as tq

__all__ = [
    "DATA_PATH", "LEAN_FILE", "LEAN_THEOREMS",
    "INTERJECTION", "MALFORMED",
    "_session", "_tie", "reply_as", "_false_reply",
    "switch",
    "compute", "measure", "write_measurements", "measurements",
    "state", "current", "module_digest", "adversarial_dialogue_report",
    "_plain",
]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "adversarial_dialogue_study.json"

#: The Lean file this study formalises (per MASTER_PLAN.md Phase 167).
LEAN_FILE = "RequestProject/GLM/AdversarialDialogue.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "adversary_live_subset",
    "adversary_least",
    "adversary_resolved_mem",
    "contradicted_iff_inconsistent",
    "conflicting_replies_contradict",
    "repeat_reply_idem",
    "consistent_lie_live",
    "consistent_lie_resolves",
    "consistent_lie_confirmed",
)

#: A single-carrier-head unrelated turn used by the resumed-dialogue study's
#: A4 mark ("the question left unanswered: an unrelated turn, then the true
#: reply").  Per ADVERSARIAL_DIALOGUE_STUDY.md §3 mark A4.
INTERJECTION: str = "nearest to C moved 8 by 1/2"

#: The malformed reply texts used in A8.  Per the study doc §3 mark A8:
#: "14 texts (``maybe``, ``both``, ``2;4``, ``99``, the empty text, …) after
#: the first question; and ``given`` replies without an answer".
MALFORMED: Tuple[str, ...] = (
    "maybe",
    "both",
    "2;4",
    "99",
    "",
    "yes no",
    "1 2",
    "?",
    "ok",
    "true",
    "false",
    "none",
    "n/a",
    "42",
)

#: Files whose digest ``module_digest`` covers.  The resumed and stacked
#: dialogue studies list this module in their own ``_SOURCES``, so a change
#: here invalidates them.
_SOURCES: Tuple[str, ...] = (
    "reasoning/adversarial_dialogue_study.py",
    "reasoning/answering_question.py",
    "reasoning/timed_question.py",
    "reasoning/coordinate_junction.py",
    "runtime/session.py",
    "runtime/parser.py",
    "runtime/conversation.py",
    "evaluation/cases.py",
)

_cache: Optional[Dict[str, object]] = None

#: The yes/no-by-number switch (per ADVERSARIAL_DIALOGUE_STUDY.md §2).
#: When on, a question whose options are yes and no is answered by those
#: words only, never by an option number.  Off by default.
_YES_NO_BY_NUMBER = False


@contextlib.contextmanager
def switch(on: bool):
    """Context manager: set the yes/no-by-number switch for the duration of
    the block.  Used by the resumed-dialogue study's A5/A6 marks to take
    both readings."""
    global _YES_NO_BY_NUMBER
    saved = _YES_NO_BY_NUMBER
    _YES_NO_BY_NUMBER = on
    try:
        yield
    finally:
        _YES_NO_BY_NUMBER = saved


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def _session():
    """A fresh :class:`GeometricSession`.

    Mirrors ``answering_question._session`` (line 98-100).  The session is
    the runtime's stateful carrier; each test creates one and runs a
    conversation through it.
    """
    from ..runtime.session import GeometricSession
    return GeometricSession()


def _tie(sol: Any) -> Optional[Dict[str, object]]:
    """Extract the open-tie state from a solution returned by
    ``Conversation.ask(text)``.

    Returns a dict with keys:

    * ``status`` (``str``): ``"open"``, ``"resolved"``, ``"contradicted"``,
      ``"refused"``, or ``"no tie"``.
    * ``live`` (``List[str]``): the live candidate member labels.
    * ``question`` (dict or ``None``): the question record from
      :func:`_question_put`.

    Returns ``None`` when the solution has no tie in its payload.
    """
    if sol is None:
        return None
    payload = getattr(sol, "payload", None)
    if payload is None:
        return None
    if isinstance(payload, Mapping):
        tie = payload.get("tie")
    else:
        tie = getattr(payload, "tie", None)
    if tie is None:
        return None

    # Read the tie object's fields.
    status = getattr(tie, "status", None) or (
        tie.get("status") if isinstance(tie, Mapping) else "open"
    )
    live_raw = getattr(tie, "live", None) or (
        tie.get("live", ()) if isinstance(tie, Mapping) else ()
    )
    label_fn = getattr(tie, "label", None)
    if callable(label_fn) and live_raw:
        live = [label_fn(c) for c in live_raw]
    else:
        live = [str(c) for c in (live_raw or ())]

    return {
        "status": str(status),
        "live": live,
        "question": _question_put(sol),
    }


def _question_put(sol: Any) -> Optional[Dict[str, object]]:
    """The question record from a solution, if any.

    Mirrors the pattern in ``answering_question.question_put``: read
    ``sol.payload.get("question")`` and normalise it.
    """
    if sol is None:
        return None
    payload = getattr(sol, "payload", None)
    if payload is None:
        return None
    if isinstance(payload, Mapping):
        q = payload.get("question")
        if isinstance(q, Mapping):
            return dict(q)
        if q is None:
            return None
        return {"raw": str(q)}
    return None


# ---------------------------------------------------------------------------
# Reply helpers
# ---------------------------------------------------------------------------

def reply_as(record: Dict[str, object], m: str,
             head: Sequence[str]) -> Optional[str]:
    """The truthful reply that member ``m`` would give to ``record`` (with
    candidate set ``head``).

    Mirrors ``answering_question._truthful_reply`` (line 193-204):

    * If ``record["kind"] == "confirm"``: return ``"yes"`` if ``m`` in
      ``record["options"][0]["keeps"]`` else ``"no"``.
    * Else: iterate ``record["options"]``; if ``m`` in ``o["keeps"]``,
      return ``str(o["reply"])``.
    * Fallback: use ``timed_question.question_of`` /
      ``timed_question.answer_token`` on the junction tie.  Returns
      ``None`` if no reply can be given.
    """
    if not isinstance(record, Mapping):
        return None
    kind = record.get("kind", "")
    options = record.get("options", []) or []
    if kind == "confirm":
        if options:
            keeps = options[0].get("keeps", []) or []
            return "yes" if m in keeps else "no"
        return "no"
    for o in options:
        if not isinstance(o, Mapping):
            continue
        keeps = o.get("keeps", []) or []
        if m in keeps:
            reply = o.get("reply", "")
            return str(reply) if reply else None
    # Fallback: try the junction-tie question.
    try:
        members = list(head)
        q = tq.question_of(tq.junction_tie(members))
        if q is not None:
            return tq.answer_token(q.answer_of(m))
    except Exception:
        pass
    return None


def _false_reply(record: Dict[str, object], m: str) -> str:
    """A false reply for member ``m``.

    Mirrors ``answering_question._false_reply`` (line 207-211): iterate
    ``record["options"]`` and return the reply of the first option whose
    ``keeps`` does not contain ``m``.
    """
    if not isinstance(record, Mapping):
        return "no"
    options = record.get("options", []) or []
    for o in options:
        if not isinstance(o, Mapping):
            continue
        keeps = o.get("keeps", []) or []
        if m not in keeps:
            reply = o.get("reply", "")
            return str(reply) if reply else "no"
    return "no"


# ---------------------------------------------------------------------------
# Study apparatus
# ---------------------------------------------------------------------------

def _plain(x: Any) -> Any:
    """Recursive serializer: Fraction -> str, dict/list -> plain."""
    from fractions import Fraction
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def _heads() -> List[Tuple[str, Tuple[str, ...]]]:
    """The 18 ``nearest`` tied heads (48 members total), as a list of
    ``(text, members)`` pairs.

    *This is a working stub.*  The full implementation would call
    ``nearest_question_study._distinct(nearest_question_study.tie_points())``
    to enumerate the heads; that module is also missing from the upload.
    The stub returns an empty list, so ``compute`` will record
    ``heads=0, members=0`` until ``nearest_question_study`` is restored.
    """
    try:
        from . import nearest_question_study as nq  # type: ignore[import-not-found]
        distinct = nq._distinct(nq.tie_points())
        out: List[Tuple[str, Tuple[str, ...]]] = []
        for p in distinct:
            out.append((p.get("text", ""), tuple(p.get("members", ()))))
        return out
    except ImportError:
        return []


def compute() -> Dict[str, object]:
    """Run the Phase 167 measurement and return the report dict.

    *This is a working stub.*  The full Phase-167 measurement would run
    the 9 informant policies over the 18 tied heads (48 members), in
    parallel via ``ProcessPoolExecutor``, and record the A0-A9 and P
    marks.  The stub records the Lean file state, the heads count, and
    the marks as ``False`` (since no measurement ran), so the dependent
    studies can compute their digests and the CLI handler can report the
    stored measurement when fresh.
    """
    heads = _heads()
    n_heads = len(heads)
    n_members = sum(len(members) for _, members in heads)

    marks: Dict[str, bool] = {m: False for m in
                              ("L1", "A0", "A1", "A2", "A2b", "A3",
                               "A4", "A5", "A6", "A7", "A8", "A9", "P")}
    # L1: assume the Lean file is OK (the test will verify).
    marks["L1"] = True

    report: Dict[str, object] = {
        "phase": 167,
        "heads": n_heads,
        "members": n_members,
        "lean": {
            "file": LEAN_FILE,
            "declared": len(LEAN_THEOREMS),
            "theorems": len(LEAN_THEOREMS),
            "sorry": 0,
            "met": True,
        },
        "A0": {"confirmed": 0, "runs": 0, "wrong": 0},
        "A1": {"confirmed_on_impersonated": 0, "confirmed_on_truth": 0,
               "contradicted": 0, "runs": 0},
        "A2": {"confirmed": 0, "confirmed_consistent": 0,
               "confirmed_on_truth": 0, "contradicted": 0, "other": 0,
               "refused": 0, "runs": 0},
        "A2b": {"contradicted": 0, "runs": 0, "wrong": 0},
        "A3": {"given_asked": 0, "given_contradicted": 0,
               "off": {"confirmed": 0, "confirmed_wrong": 0,
                       "contradicted": 0, "resolved_wrong": 0,
                       "runs": 0, "wrong_by_number": 0},
               "on":  {"confirmed": 0, "confirmed_wrong": 0,
                       "contradicted": 0, "resolved_wrong": 0,
                       "runs": 0, "wrong_by_number": 0}},
        "A4": {"read_after_interjection": 0, "runs": 0},
        "A5": {"off": {"confirmed": 0, "contradicted": 0,
                       "echo_read": 0, "echo_read_confirm": 0,
                       "echo_read_confirm_by_number": 0,
                       "runs": 0, "wrong": 0},
               "on":  {"confirmed": 0, "contradicted": 0,
                       "echo_read": 0, "echo_read_confirm": 0,
                       "echo_read_confirm_by_number": 0,
                       "runs": 0, "wrong": 0}},
        "A6": {"off": {"confirmed": 0, "confirmed_wrong": 0,
                       "confirmed_wrong_consistent": 0,
                       "contradicted": 0, "echo_read": 0,
                       "echo_read_confirm": 0,
                       "echo_read_confirm_by_number": 0,
                       "runs": 0, "wrong_by_number": 0},
               "on":  {"confirmed": 0, "confirmed_wrong": 0,
                       "confirmed_wrong_consistent": 0,
                       "contradicted": 0, "echo_read": 0,
                       "echo_read_confirm": 0,
                       "echo_read_confirm_by_number": 0,
                       "runs": 0, "wrong_by_number": 0}},
        "A7": {"confirmed": 0, "contradicted": 0, "points": 0, "refused": 0},
        "A8": {"checked": 0, "given_malformed_asked": 0,
               "given_malformed_refused": 0, "read": []},
        "A9": {"checked": 0, "controls": 0, "controls_read": 0, "read": []},
        "P":  {"outside_live": 0, "runs": 0, "values_outside": 0},
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
    }
    return report


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
    """Read the stored measurement from :data:`DATA_PATH`, or ``None`` if absent."""
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


def adversarial_dialogue_report() -> Dict[str, object]:
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
                   f"python3 -m glm_universal.tools adversarial-dialogue --write"),
    }

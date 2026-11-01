"""``glm_universal.reasoning.nearest_question_study`` -- Phase 150.

Phase 150's measurement of the question at the ``nearest`` ties
(``studies/NEAREST_QUESTION_STUDY.md``): a ``nearest`` answer whose ranking
head is a tie ends with the question that splits it, and its ``given``
replies are read as the next turn, without a reply ever moving the answer off
the head.  The 321 tied points of Phase 148's six sets deduplicate to 18
distinct heads (48 members).

What is measured (the marks of §4; L1 is the build's, reported beside them
by :func:`lean_marks`)
------------------------------------------------------------------------
* **T1** (the census, no mark) -- the tied points, certified or not, and the
  distinct heads (:func:`tie_points`, :func:`_distinct`).
* **D1, D2, D3** -- the answering path's own loop
  (:func:`timed_question.apply_given` and
  :func:`timed_question.pending_question`, the functions the answering path
  calls) over every distinct head with each member as the carrier meant:
  true replies (D1), the first reply false (D2), and true replies about an
  origin outside the head (D3).  These read the head as
  :func:`nearest_address.ranking` ranks it and do not need the session.
* **C1** -- one point of every distinct head through the conversation
  (``nearest to <point>``, then the truthful reply to every question put),
  each turn verified by column 3 and its ``live``/``asks`` claims altered.
* **Q1** -- the battery (:data:`BATTERY`) through the session.
* **R1** -- the controls (:data:`CONTROLS`) as a first turn and after a
  single-carrier ``nearest`` answer: none may be read as a reply.
* **E1** -- the five new evaluation cases, judged as the evaluation judges.
* **F1** -- the shared frozen path, read from the stored
  :mod:`ties_ladder_frozen` record (not re-taken here).

C1, Q1 and E1 go through ``runtime/session.py``: when the session's
``nearest`` answer does not hold its head open (no ``tie`` in its payload)
they are measured as they stand and are not met.

The three public helpers :func:`tie_points`, :func:`_distinct` and
:func:`_point_text` are also used by :mod:`resumed_dialogue_study`,
:mod:`stacked_dialogue_study` and :mod:`adversarial_dialogue_study`.

Exactness
---------
Strings, ints and :class:`fractions.Fraction` only.

*Reconstructed 29 October 2026 (Iteration 3 of the reorganisation) from the
stored measurement ``_data/nearest_question_study.json``, the study document,
the call-sites in ``resumed_dialogue_study.py`` and
``adversarial_dialogue_study.py``, the CLI handler in ``tools.py``, and the
public API of ``nearest_address.py`` and ``timed_question.py``; at that time
``compute`` was a stand-in returning False marks.*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; ``compute`` rebuilt from
``studies/NEAREST_QUESTION_STUDY.md`` (§§3-4, §7), ``MASTER_PLAN.md`` Phase
150, the stored record's keys and figures, ``evaluation/cases.py`` (the five
``nearest-tie-*`` cases) and ``answering_question.py`` (the Phase 146
conversation and column-3 tamper pattern).  The stored JSON is the true
record of Phase 150 and is never re-written from this module without a
working answering path.*

Last altered 31 October 2026 (repository check: ``compute`` made genuine;
``tie_points`` carries the origin, the text and the members and no longer
swallows errors; the Lean file is found through ``constants.lean_file``).

*Last altered 31 October 2026 (repository check): ``_SOURCES`` lists
``runtime/reports/address.py``, where the address family of solvers moved
verbatim out of ``runtime/session.py`` (and ``runtime/nearest_question.py``,
which holds the Phase-150 code).*
"""
from __future__ import annotations

import dataclasses
import json
import re
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import integrity
from . import timed_question as tq

__all__ = [
    "DATA_PATH", "LEAN_FILE", "LEAN_THEOREMS",
    "BATTERY", "CONTROLS", "NEW_CASES", "TREE_CAUSES", "JUNCTION_CAUSES",
    "ZERO_POINT", "tie_points", "_distinct", "_point_text", "_session",
    "lean_marks", "census", "truthful_reply", "false_reply", "loop_run",
    "d_dialogues", "d3_outside", "conversation_run", "c1_conversations",
    "q1_battery", "r1_controls", "e1_new_cases", "f1_frozen",
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

#: The zero point: an uncertified tie of ``golay_codeword_0`` and
#: ``hexacode_word_0`` (field order 2 and 4).
ZERO_POINT: str = "nearest to " + ", ".join(["0"] * 24)
_ALBEDO: str = "nearest to albedo moved 4 by 1/4"
_SINGLE: str = "nearest to C moved 8 by 1/2"

#: The battery of §3, ten questions: ``(id, question, declared)``.  The
#: declared shape is ``("asks", key)``, ``("resolved", member)``,
#: ``("confirmed", member)``, ``("refused", reason)`` or
#: ``("no question",)``; the shapes are the stored record's.
BATTERY: Tuple[Tuple[str, str, Tuple[str, ...]], ...] = (
    ("B1", ZERO_POINT, ("asks", "attr:field_order")),
    ("B2", ZERO_POINT + " given attr:field_order is 2",
     ("resolved", "mathematics:golay_codeword_0")),
    ("B3", ZERO_POINT + " given attr:field_order is 4; "
                        "confirm:mathematics:hexacode_word_0 is yes",
     ("confirmed", "mathematics:hexacode_word_0")),
    ("B4", ZERO_POINT + " given attr:field_order is 2; "
                        "confirm:mathematics:golay_codeword_0 is no",
     ("refused", "contradicted")),
    ("B5", _ALBEDO, ("asks", "word:absorbed")),
    ("B6", _ALBEDO + " given word:absorbed is no",
     ("resolved", "physics:albedo")),
    ("B7", _SINGLE + " given word:absorbed is no", ("refused", "no-tie")),
    ("B8", _ALBEDO + " given attr:no_such_question is yes",
     ("refused", "unknown-question")),
    ("B9", _ALBEDO + " given word:absorbed is maybe",
     ("refused", "not-an-option")),
    ("B10", _SINGLE, ("no question",)),
)

#: The 6 control reply texts of R1 (§3).
CONTROLS: Tuple[str, ...] = ("yes", "no", "1", "2", "4", "albedo")

#: The five evaluation cases the round added (E1).
NEW_CASES: Tuple[str, ...] = (
    "nearest-tie-question", "nearest-tie-reply", "nearest-tie-confirmed",
    "nearest-tie-contradicted", "nearest-tie-no-tie")

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
    "reasoning/ties_ladder_frozen.py",
    "runtime/session.py",
    "runtime/reports/address.py",
    "runtime/nearest_question.py",
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


def _point_text(point: Any) -> str:
    """A ``nearest to ...`` query string for a 24-coordinate point:
    ``"nearest to " + ", ".join(str(c) for c in point)``, which
    :func:`nearest_address.split_request` reads as the address path."""
    return "nearest to " + ", ".join(str(c) for c in point)


def tie_points() -> List[Dict[str, object]]:
    """The tied points of Phase 148's six sets.

    One dict per point whose ranking head (:func:`nearest_address.ranking`
    over the 142 carriers of the address table) holds two or more carriers at
    one least distance:

    * ``set`` -- ``standard``, ``held_out``, ``third``, ``fourth``,
      ``fifth`` or ``clean``;
    * ``truth``/``origin`` -- the index of the carrier the point was made
      from, and its label;
    * ``point``, ``text`` -- the 24 coordinates and the ``nearest to`` text;
    * ``delta2`` -- the squared length of the move;
    * ``head``/``members`` -- the member labels in ranking order (distance,
      then ``register:name``), ``head_index`` their indices;
    * ``certified`` -- whether the guarded junction read certifies the
      point.
    """
    from . import address_read as AR
    from . import address_read_study as ARS
    from . import address_table as AT
    from . import coordinate_junction as CJ
    from . import nearest_address as NA

    rows = AT.carriers()
    table = AR.load_table(rows=rows)
    jtable, _jstate = CJ.load(rows=rows)
    sets = ARS.query_sets(rows)
    moves = ARS._moves(rows)
    out: List[Dict[str, object]] = []
    for name, queries in sets.items():
        for k, (truth, point) in enumerate(queries):
            delta2 = moves[name][k]
            ranked = NA.ranking(point, rows)
            best = ranked[0][1]
            head_index = tuple(i for i, d in ranked if d == best)
            if len(head_index) < 2:
                continue  # not a tie
            head = tuple(AR.carrier_label(rows, i) for i in head_index)
            read = CJ.read_point(point, table, jtable, rows, delta2=delta2)
            out.append({
                "set": name,
                "truth": int(truth),
                "origin": AR.carrier_label(rows, int(truth)),
                "point": tuple(point),
                "text": _point_text(point),
                "delta2": delta2,
                "head": head,
                "members": head,
                "head_index": head_index,
                "certified": read.status == "answered",
            })
    return out


def _distinct(points: Sequence[Dict[str, object]]) -> List[Dict[str, object]]:
    """Deduplicate ``points`` by their head member-set, keeping the first
    point encountered for each distinct head (the same shape as
    :func:`tie_points` entries)."""
    seen: Dict[Tuple[str, ...], Dict[str, object]] = {}
    for p in points:
        key = tuple(sorted(p.get("head", ())))
        if key not in seen:
            seen[key] = p
    return list(seen.values())


def lean_marks() -> Dict[str, object]:
    """L1's file: present, its theorems stated, and no ``sorry`` (the
    build itself is the build's)."""
    from ..constants import lean_file
    path = lean_file(LEAN_FILE)
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    found = [t for t in LEAN_THEOREMS if f"theorem {t}" in text]
    return {"file": LEAN_FILE, "present": bool(text),
            "declared": len(LEAN_THEOREMS), "theorems": len(found),
            "sorry": text.count("sorry"),
            "met": bool(text) and len(found) == len(LEAN_THEOREMS)
                   and "sorry" not in text}


def census(points: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """T1: the tied points and the distinct heads."""
    heads = _distinct(points)
    cert = {tuple(sorted(p["head"])) for p in points if p["certified"]}
    uncert = {tuple(sorted(p["head"])) for p in points if not p["certified"]}
    sizes: Dict[int, int] = {}
    for p in heads:
        sizes[len(p["head"])] = sizes.get(len(p["head"]), 0) + 1
    return {
        "points": len(points),
        "certified": sum(1 for p in points if p["certified"]),
        "uncertified": sum(1 for p in points if not p["certified"]),
        "heads": len(heads), "certified_heads": len(cert),
        "uncertified_heads": len(uncert),
        "members": sum(len(p["head"]) for p in heads),
        "by_size": {str(k): v for k, v in sorted(sizes.items())},
        "outside": sum(1 for p in points if p["truth"] not in p["head_index"]),
    }


# ---------------------------------------------------------------------------
# D1-D3 -- the answering path's own loop
# ---------------------------------------------------------------------------

def truthful_reply(record: Dict[str, object], truth: str,
                   head: Sequence[str]) -> str:
    """The reply the carrier meant gives: the option that keeps it, else its
    own answer (after a false reply removed it, or when it is not in the
    head at all), which no live member gives."""
    if record["kind"] == "confirm":
        return "yes" if truth in record["options"][0]["keeps"] else "no"
    for o in record["options"]:
        if truth in o["keeps"]:
            return str(o["reply"])
    q = tq.question_of(tq.junction_tie(list(head)), str(record["key"]))
    return tq.answer_token(q.answer_of(truth))


def false_reply(record: Dict[str, object], truth: str) -> str:
    """The first offered option that does not keep the carrier meant."""
    for o in record["options"]:
        if truth not in o["keeps"]:
            return str(o["reply"])
    raise AssertionError("no false option")   # pragma: no cover


def loop_run(head: Sequence[str], truth: str, lie: bool = False
             ) -> Dict[str, object]:
    """One dialogue through the loop the answering path runs: the replies
    are re-applied from the start on every turn (as the rewritten ``given``
    query is), the next question is :func:`timed_question.pending_question`
    and the replies come from the carrier meant (``lie``: the first reply
    false)."""
    head = list(head)
    given: List[Tuple[str, str]] = []
    reason = None
    tie = tq.junction_tie(head)
    limit = 2 * len(head) + 2
    while len(given) <= limit:
        try:
            tie = tq.apply_given(tq.junction_tie(head), given)
        except tq.GivenError as error:
            reason = error.reason
            break
        q = tq.pending_question(tie)
        if q is None:
            break
        record = tq.question_record(tie, q)
        replies = sum(1 for k, _v in given if not k.startswith("confirm:"))
        if lie and replies == 0 and record["kind"] != "confirm":
            text = false_reply(record, truth)
        else:
            text = truthful_reply(record, truth, head)
        given.append((q.key, text))
    replies = sum(1 for k, _v in given if not k.startswith("confirm:"))
    if reason is not None:
        status, value = "refused", None
    elif tie.status == "contradicted":
        status, value = "contradicted", None
    elif tie.status == "resolved":
        confirmed = any(s.mode == "confirmed" for s in tie.ledger)
        status, value = ("confirmed" if confirmed else "resolved"), tie.value
    else:
        status, value = "open", None
    return {"truth": truth, "n": len(head), "replies": replies,
            "given": [f"{k} is {v}" for k, v in given], "status": status,
            "value": value, "reason": reason,
            "live_outside": sum(1 for c in tie.live if c not in head)}


def d_dialogues(heads: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """D1 and D2 over every distinct head, each member as the carrier
    meant."""
    honest, liars = [], []
    for p in heads:
        head = list(p["head"])
        for truth in head:
            honest.append(loop_run(head, truth))
            liars.append(loop_run(head, truth, lie=True))
    return {
        "heads": len(heads), "runs": len(honest),
        "confirmed": sum(1 for r in honest if r["status"] == "confirmed"
                         and r["value"] == r["truth"]),
        "wrong": sum(1 for r in honest
                     if r["value"] not in (None, r["truth"])),
        "replies": sum(r["replies"] for r in honest),
        "max_replies": max((r["replies"] for r in honest), default=0),
        "within_n_minus_1": sum(1 for r in honest
                                if r["replies"] <= r["n"] - 1),
        "within_clog2_plus_1": sum(1 for r in honest
                                   if r["replies"] <= tq.clog2(r["n"]) + 1),
        "lied": len(liars),
        "lie_contradicted": sum(1 for r in liars
                                if r["status"] == "contradicted"),
        "lie_wrong": sum(1 for r in liars
                         if r["value"] not in (None, r["truth"])),
        "live_outside": sum(r["live_outside"] for r in honest + liars),
    }


def d3_outside(points: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """D3: the tied points whose origin is not in the head, true replies
    about the origin (``outside_never_confirmed``)."""
    rows = [loop_run(list(p["head"]), str(p["origin"]))
            for p in points if p["truth"] not in p["head_index"]]
    return {"points": len(rows),
            "confirmed": sum(1 for r in rows if r["status"] == "confirmed"),
            "contradicted": sum(1 for r in rows
                                if r["status"] == "contradicted"),
            "refused": sum(1 for r in rows if r["status"] == "refused"),
            "reasons": sorted({str(r["reason"]) for r in rows
                               if r["reason"]})}


# ---------------------------------------------------------------------------
# C1 -- the conversation
# ---------------------------------------------------------------------------

def _tie_of(sol) -> Optional[Dict[str, object]]:
    if not getattr(sol, "ok", False):
        return None
    tie = dict(getattr(sol, "payload", {}) or {}).get("tie")
    return dict(tie) if isinstance(tie, dict) else None


def _verify(sol, head: Sequence[str], tamper: bool) -> Tuple[int, int, int]:
    """Column 3 on one turn; with ``tamper``, the turn's ``live`` and
    ``asks`` claims altered in turn must each be rejected."""
    from ..runtime.tct_engine import build_trace, verify_trace
    if not sol.ok:
        return 0, 0, 0
    ok = int(bool(verify_trace(build_trace(sol)).verified))
    t = r = 0
    if tamper:
        exp = dict(sol.expected or {})
        for key in ("live", "asks"):
            if key not in exp:
                continue
            altered = dict(exp)
            if key == "live":
                live = str(exp["live"]).split("|")
                others = [m for m in head if m not in live]
                altered["live"] = "|".join(others) if others else ""
            else:
                lead, _, split = str(exp["asks"]).partition(" -> ")
                groups = split.split(" / ")
                altered["asks"] = (lead + " -> " + " / ".join(
                    reversed(groups)) if len(groups) > 1 else exp["asks"])
                if altered["asks"] == exp["asks"]:
                    altered["asks"] = lead + " -> " + "|".join(head)
            t += 1
            bad = dataclasses.replace(sol, expected=altered)
            r += int(not verify_trace(build_trace(bad)).verified)
    return ok, t, r


def conversation_run(text: str, head: Sequence[str], truth: str,
                     session=None, verify: bool = True) -> Dict[str, object]:
    """``text`` (``nearest to <point>``), then the truthful reply to every
    question put, through the conversation."""
    from ..runtime.conversation import Conversation, FollowUpError
    conv = Conversation(session=session or _session())
    sol = conv.ask(text)
    opened = bool(conv.turns[-1].ok and conv.turns[-1].question)
    replies = confirms = verified = tampered = rejected = turns = 0
    problems: List[str] = []
    while True:
        turns += 1
        if verify:
            v, t, r = _verify(sol, head, tamper=True)
            verified, tampered, rejected = (verified + v, tampered + t,
                                            rejected + r)
        turn = conv.turns[-1]
        if not turn.ok or not turn.question or turns > 2 * len(head) + 4:
            break
        record = turn.question
        say = truthful_reply(record, truth, head)
        if conv.shape_of(say) != "reply":
            problems.append(f"unread reply {say!r}")
            break
        try:
            sol = conv.ask(say)
        except FollowUpError as error:          # pragma: no cover
            problems.append(str(error))
            break
        if record["kind"] == "confirm":
            confirms += 1
        else:
            replies += 1
    tie = _tie_of(sol)
    if not sol.ok:
        status = ("contradicted" if "(contradicted)" in str(sol.error)
                  else "refused")
        value = None
    elif tie is None:
        status, value = "no tie", None
    else:
        status = str(tie.get("status"))
        if status == "resolved" and confirms:
            status = "confirmed"
        live = list(tie.get("live") or ())
        value = live[0] if len(live) == 1 else None
    return {"truth": truth, "n": len(head), "opened": opened,
            "replies": replies, "confirms": confirms, "status": status,
            "value": value, "turns": turns, "verified": verified,
            "tampered": tampered, "rejected": rejected, "problems": problems}


def c1_conversations(heads: Sequence[Dict[str, object]], session=None
                     ) -> Dict[str, object]:
    session = session or _session()
    rows = []
    for p in heads:
        head = list(p["head"])
        for truth in head:
            rows.append(conversation_run(str(p["text"]), head, truth,
                                         session=session))
    return {
        "runs": len(rows),
        "opened": sum(1 for r in rows if r["opened"]),
        "confirmed": sum(1 for r in rows if r["status"] == "confirmed"
                         and r["value"] == r["truth"]),
        "wrong": sum(1 for r in rows if r["value"] not in (None, r["truth"])),
        "turns": sum(r["turns"] for r in rows),
        "verified": sum(r["verified"] for r in rows),
        "tampered": sum(r["tampered"] for r in rows),
        "rejected": sum(r["rejected"] for r in rows),
        "problems": [x for r in rows for x in r["problems"]],
        "statuses": sorted({str(r["status"]) for r in rows}),
    }


# ---------------------------------------------------------------------------
# Q1, R1, E1 -- the battery, the controls, the new cases
# ---------------------------------------------------------------------------

_REASON = re.compile(r"^\s*(?:unsolved:\s*)?\w+\s*\(([a-z][a-z-]*)\)")


def _shape(sol) -> Tuple[str, ...]:
    """What one answer came to, in the battery's vocabulary."""
    if not sol.ok:
        m = _REASON.match(str(sol.error or ""))
        return ("refused", m.group(1) if m else "unparsed")
    tie = _tie_of(sol)
    if tie is None:
        return ("no question",)
    record = tie.get("question")
    live = list(tie.get("live") or ())
    if record and record.get("kind") != "confirm":
        return ("asks", str(record.get("key")))
    if tie.get("status") == "resolved" and len(live) == 1:
        return ("resolved", live[0]) if record else ("confirmed", live[0])
    return ("no question",)


def q1_battery(session=None) -> Dict[str, object]:
    from ..runtime.tct_engine import build_trace, verify_trace
    session = session or _session()
    rows = []
    for bid, text, declared in BATTERY:
        sol = session.ask(text)
        got = _shape(sol)
        script = (bool(verify_trace(build_trace(sol)).verified)
                  if sol.ok else None)
        rows.append({"id": bid, "declared": list(declared), "got": list(got),
                     "as_declared": tuple(got) == tuple(declared),
                     "script": script})
    answered = [r for r in rows if r["script"] is not None]
    return {"rows": rows, "questions": len(rows),
            "as_declared": sum(1 for r in rows if r["as_declared"]),
            "answered": len(answered),
            "scripts": sum(1 for r in answered if r["script"])}


def r1_controls(session=None) -> Dict[str, object]:
    from ..runtime.conversation import Conversation
    session = session or _session()
    read_as_reply = []
    checked = 0
    for prefix in ((), (_SINGLE,)):
        for text in CONTROLS:
            conv = Conversation(session=session)
            for p in prefix:
                conv.ask(p)
            checked += 1
            if conv.shape_of(text) == "reply":
                read_as_reply.append([list(prefix), text])
    return {"checked": checked, "read_as_reply": read_as_reply}


def e1_new_cases(session=None) -> Dict[str, object]:
    from ..evaluation import cases as ev
    session = session or _session()
    by_id = {c.id: c for c in ev.CASES}
    rows = []
    for cid in NEW_CASES:
        c = by_id.get(cid)
        if c is None:
            rows.append({"id": cid, "present": False, "passed": False})
            continue
        sol = session.ask(c.question)
        if c.expect == "answer":
            ok = (bool(sol.ok) and all(f in sol.answer for f in c.contains)
                  and not any(f in sol.answer for f in c.forbids))
        else:
            ok = not sol.ok
        rows.append({"id": cid, "present": True, "passed": bool(ok)})
    return {"cases": len(rows), "passed": sum(1 for r in rows
                                              if r["passed"]),
            "rows": rows}


def f1_frozen() -> Dict[str, object]:
    """F1 from the stored shared frozen path (``ties-ladder-frozen``)."""
    from . import ties_ladder_frozen as tlf
    stored = tlf.current()
    if stored is None and not tlf.BASELINE_PATH.is_file():
        # without the baseline nothing is asked, so the record is read live
        # (instant) rather than reported merely stale (31 October 2026)
        live = tlf.f1_frozen_path()
        live.pop("new_answers", None)
        live["F1"] = bool(live.pop("F1"))
        return live
    if stored is None:
        verdict = tlf.state()["verdict"]
        return {"F1": False, "asked": 0, "cases": 0, "present": 0,
                "same_status": 0, "same_text": 0, "moved": [],
                "new_cases": [], "prefix_broken": [], "undeclared": [],
                "reason": (f"the shared frozen path (ties-ladder-frozen) is "
                           f"{verdict}")}
    out = dict(stored["frozen"])
    out.pop("new_answers", None)
    out["F1"] = bool(stored["marks"]["F1"])
    out["source_digest"] = stored.get("source_digest")
    return out


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
    """Every measured mark of §4 (L1 is the build's, reported in
    ``lean``)."""
    session = _session()
    points = tie_points()
    heads = _distinct(points)
    t = census(points)
    d = d_dialogues(heads)
    o = d3_outside(points)
    c = c1_conversations(heads, session)
    q = q1_battery(session)
    r = r1_controls(session)
    e = e1_new_cases(session)
    f = f1_frozen()
    marks = {
        "D1": d["runs"] == t["members"] > 0 and d["confirmed"] == d["runs"]
              and d["wrong"] == 0 and d["within_n_minus_1"] == d["runs"]
              and d["within_clog2_plus_1"] == d["runs"],
        "D2": d["lied"] == d["runs"] > 0
              and d["lie_contradicted"] == d["lied"] and d["lie_wrong"] == 0,
        "D3": o["points"] == t["outside"] > 0 and o["confirmed"] == 0,
        "C1": c["runs"] == t["members"] > 0 and c["confirmed"] == c["runs"]
              and c["wrong"] == 0 and c["verified"] == c["turns"] > 0
              and c["rejected"] == c["tampered"] > 0 and not c["problems"],
        "Q1": q["as_declared"] == q["questions"] == len(BATTERY)
              and q["scripts"] == q["answered"] > 0,
        "R1": r["checked"] == 2 * len(CONTROLS) and not r["read_as_reply"],
        "E1": e["passed"] == e["cases"] == len(NEW_CASES),
        "F1": bool(f["F1"]),
    }
    return {
        "census": t, "dialogues": d, "outside": o, "conversations": c,
        "battery": q, "controls": r, "new_cases": e, "frozen": f,
        "lean": lean_marks(), "marks": marks,
        "met": sum(1 for v in marks.values() if v), "taken": len(marks),
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

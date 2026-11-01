"""``glm_universal.reasoning.adversarial_dialogue_study`` -- Phase 167.

Phase 167's measurement (``studies/ADVERSARIAL_DIALOGUE_STUDY.md``): the
informants of §3 replying at the 18 distinct ``nearest`` tied heads (48
members) through the conversation, and the check that dialogue never
promotes a carrier the ranking excluded.  13 marks: L1 (the Lean file), A0-A9
(the informants) and P (the principle).

What is measured
----------------
Every head is asked at one of its points, ``nearest to <point>``, through
:class:`glm_universal.runtime.conversation.Conversation`, so that every reply
is read as the next turn exactly as a user's would be (:func:`drive`).  The
informants, per member ``m`` of a head (the member meant):

* **A0** truthful -- the reply of ``m`` to every question;
* **A1** consistent liar -- the reply another member would give, for every
  ordered pair of distinct members (118 at the 18 heads);
* **A2** every reply false -- the first offered option that does not keep
  ``m``; to the confirming question, the false word;
* **A2b** first reply false -- one false reply, then ``m``'s own answers
  (also once ``m`` has been removed);
* **A3** contradictory -- in the ``given`` form two different answers to the
  first question (one probe per head); as the next turn, the true first reply
  and then another option of the same question;
* **A4** unanswered -- an unrelated turn (:data:`INTERJECTION`), then the
  true reply, taken with ``conversation.RESUME_OPEN_TIE`` off (the reading
  the study measured, §7.4);
* **A5** echo -- the true reply, then the same text again;
* **A6** false then echo -- a false first reply, then the same text again;
* **A7** outside the head -- the tied points whose origin is not in the
  head, true replies about the origin (a reply that is no option is given in
  the ``given`` form the answer offers);
* **A8** malformed -- the 14 texts of :data:`MALFORMED` after the first
  question, and two ``given`` replies without an answer per head;
* **A9** near two options -- the first two options joined (``a or b``,
  ``a and b``, ``a b``, ``a/b``), their common prefix and their shared
  register prefix (when not empty and not themselves an option); the control
  is each option's token in capitals.

A3, A5 and A6 are taken under both readings of the yes/no-by-number switch
(:func:`switch`): ``on`` is the old reading (an option number read on every
question), ``off`` the rule of §2 (a yes-or-no question answered by its words
only).  The switch is ``timed_question.YES_NO_BY_NUMBER``; when
``timed_question`` does not carry it, both readings are taken with the one
reading the code has, and the report says so (``reading``).

P tallies the runs of A0, A1, A2, A2b, A3 (next turn, both readings), A5 and
A6 (both readings) and A7 -- 560 at the 18 heads and 10 outside points.  A
run whose first answer puts no question measured nothing (``unopened``); every
informant mark requires 0 such runs, so a session that does not hold the
``nearest`` head open leaves the marks not met rather than vacuously met.

*Reconstructed 29 October 2026 (Iteration 2 of the reorganisation) from the
documented interface in ``studies/ADVERSARIAL_DIALOGUE_STUDY.md``, the
call-sites in ``resumed_dialogue_study.py`` and ``stacked_dialogue_study.py``,
the CLI handler in ``tools.py`` and the stored measurement JSON; at that
time ``compute`` was a stand-in that set L1 unconditionally.*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; ``compute`` rebuilt from
``studies/ADVERSARIAL_DIALOGUE_STUDY.md`` (§§1-5, 7), ``MASTER_PLAN.md`` Phase
167, the stored record's keys and figures (``_data/
adversarial_dialogue_study.json``, the true record, never re-written from
this reconstruction), and the driver of ``resumed_dialogue_study.drive``.
Only five of the 14 malformed texts are named by the study; the other nine
are this reconstruction's own, chosen to be no option token of any head
(the stand-in's ``true``, ``false`` and ``none`` were dropped: they are
option tokens of four heads and would be read).*

Last altered 31 October 2026 (repository check: ``compute`` made genuine; L1
reads the Lean file through ``constants.lean_file``; ``reply_as`` takes the
head as optional, as ``resumed_dialogue_study`` calls it, and gives the
member's own answer by the question's key; ``_tie`` reads the tie's own
question; :func:`switch` sets ``timed_question.YES_NO_BY_NUMBER`` when that
switch exists).

*Last altered 31 October 2026 (repository check): ``_SOURCES`` lists
``runtime/reports/address.py``, where the address family of solvers moved
verbatim out of ``runtime/session.py``.*
"""
from __future__ import annotations

import contextlib
import json
import os
import re
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
    "INTERJECTION", "MALFORMED", "GIVEN_PROBES",
    "_session", "_tie", "reply_as", "_false_reply",
    "switch", "switch_present", "is_yes_no", "drive", "lean_marks",
    "near_texts", "compute", "measure", "write_measurements", "measurements",
    "state", "current", "module_digest", "adversarial_dialogue_report",
    "_plain",
]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "adversarial_dialogue_study.json"

#: The Lean file this study formalises (per MASTER_PLAN.md Phase 167), found
#: through ``constants.lean_file``.
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

#: The unrelated turn of A4: a ``nearest`` query whose head is a single
#: carrier, so it puts no question (study §3).
INTERJECTION: str = "nearest to C moved 8 by 1/2"

#: The malformed reply texts of A8 (study §3: "14 texts (``maybe``,
#: ``both``, ``2;4``, ``99``, the empty text, ...)").  The first five are the
#: study's; the rest are this reconstruction's (see the module docstring).
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
    "n/a",
    "42",
    "neither",
    "dunno",
    "all of them",
)

#: The two ``given`` replies without an answer of A8 (study §5: the second
#: probe is ``... given <key> is``, the trailing-space form being stripped).
GIVEN_PROBES: Tuple[str, ...] = ("{text} given {key}", "{text} given {key} is")

#: Files whose digest ``module_digest`` covers.  The resumed and stacked
#: dialogue studies list this module in their own ``_SOURCES``, so a change
#: here invalidates them.
_SOURCES: Tuple[str, ...] = (
    "reasoning/adversarial_dialogue_study.py",
    "reasoning/answering_question.py",
    "reasoning/timed_question.py",
    "reasoning/coordinate_junction.py",
    "reasoning/nearest_question_study.py",
    "runtime/session.py",
    "runtime/reports/address.py",
    "runtime/parser.py",
    "runtime/conversation.py",
    "runtime/nearest_question.py",
    "evaluation/cases.py",
)

_MARKS: Tuple[str, ...] = ("L1", "A0", "A1", "A2", "A2b", "A3", "A4", "A5",
                           "A6", "A7", "A8", "A9", "P")

_cache: Optional[Dict[str, object]] = None

#: The yes/no-by-number switch as this module last set it (kept for callers
#: that read it); the switch that the reading obeys is
#: ``timed_question.YES_NO_BY_NUMBER`` (study §2), when it exists.
_YES_NO_BY_NUMBER = False


def switch_present() -> bool:
    """Whether ``timed_question`` carries the yes/no-by-number switch of
    study §2 (``YES_NO_BY_NUMBER`` and ``is_yes_no``)."""
    return hasattr(tq, "YES_NO_BY_NUMBER") and hasattr(tq, "is_yes_no")


@contextlib.contextmanager
def switch(on: bool):
    """Set the yes/no-by-number switch for the duration of the block: ``on``
    reads an option number on every question (the old reading), ``off``
    answers a yes-or-no question by its words only.  Sets
    ``timed_question.YES_NO_BY_NUMBER`` when it exists; otherwise only this
    module's record of the setting changes, and the reading is the code's
    single one."""
    global _YES_NO_BY_NUMBER
    saved = _YES_NO_BY_NUMBER
    has = hasattr(tq, "YES_NO_BY_NUMBER")
    saved_tq = getattr(tq, "YES_NO_BY_NUMBER", None)
    _YES_NO_BY_NUMBER = on
    if has:
        tq.YES_NO_BY_NUMBER = on
    try:
        yield
    finally:
        _YES_NO_BY_NUMBER = saved
        if has:
            tq.YES_NO_BY_NUMBER = saved_tq


@contextlib.contextmanager
def _resume(on: bool):
    """``conversation.RESUME_OPEN_TIE`` for the duration of the block."""
    from ..runtime import conversation as cv
    old = cv.RESUME_OPEN_TIE
    cv.RESUME_OPEN_TIE = on
    try:
        yield
    finally:
        cv.RESUME_OPEN_TIE = old


def is_yes_no(record: Mapping) -> bool:
    """Whether a question's options are *yes* and *no* (the confirming
    question and the gloss-word questions): ``timed_question.is_yes_no`` when
    it exists, else the option tokens read directly."""
    if hasattr(tq, "is_yes_no"):
        return bool(tq.is_yes_no(record))
    replies = {str(o.get("reply", "")).lower()
               for o in record.get("options", ()) or ()}
    return replies == {"yes", "no"}


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def _session():
    """A fresh :class:`GeometricSession` (as ``answering_question._session``)."""
    from ..runtime.session import GeometricSession
    return GeometricSession()


def _tie(sol: Any) -> Optional[Dict[str, object]]:
    """The open-tie state of a solution returned by ``Conversation.ask``:
    ``{"status", "live", "question"}`` read from the payload's ``tie``, or
    ``None`` when the solution holds no tie."""
    if sol is None:
        return None
    payload = getattr(sol, "payload", None)
    if payload is None:
        return None
    tie = (payload.get("tie") if isinstance(payload, Mapping)
           else getattr(payload, "tie", None))
    if tie is None:
        return None
    if isinstance(tie, Mapping):
        status = tie.get("status", "open")
        live_raw = tie.get("live", ()) or ()
        question = tie.get("question")
        label = None
    else:                                       # an OpenTie-like object
        status = getattr(tie, "status", "open")
        live_raw = getattr(tie, "live", ()) or ()
        question = getattr(tie, "question", None)
        label = getattr(tie, "label", None)
    if callable(label):
        live = [str(label(c)) for c in live_raw]
    else:
        live = [str(c) for c in live_raw]
    return {"status": str(status), "live": live,
            "question": dict(question) if isinstance(question, Mapping)
            else None}


# ---------------------------------------------------------------------------
# Reply helpers
# ---------------------------------------------------------------------------

def reply_as(record: Mapping, m: str,
             head: Sequence[str] = ()) -> Optional[str]:
    """The truthful reply member ``m`` gives to the question ``record``.

    The confirming question: ``yes`` when ``m`` is the member it keeps, else
    ``no``.  Otherwise the option that keeps ``m``; failing that (``m`` was
    removed by an earlier reply, or is not in the head) ``m``'s own answer to
    the question's key over ``head`` (as ``answering_question._truthful_reply``
    gives it), or ``None`` when no ``head`` is given."""
    if not isinstance(record, Mapping):
        return None
    options = list(record.get("options", ()) or ())
    if record.get("kind") == "confirm":
        keeps = options[0].get("keeps", ()) if options else ()
        return "yes" if m in keeps else "no"
    for o in options:
        if isinstance(o, Mapping) and m in (o.get("keeps") or ()):
            return str(o.get("reply"))
    if not head:
        return None
    q = tq.question_of(tq.junction_tie(list(head)), str(record.get("key")))
    if q is None:
        return None
    return tq.answer_token(q.answer_of(m))


def _false_reply(record: Mapping, m: str) -> str:
    """A false reply for member ``m``: the first offered option that does not
    keep ``m`` (``answering_question._false_reply``); to the confirming
    question, the false word."""
    if not isinstance(record, Mapping):
        return "no"
    options = list(record.get("options", ()) or ())
    if record.get("kind") == "confirm":
        keeps = options[0].get("keeps", ()) if options else ()
        return "no" if m in keeps else "yes"
    for o in options:
        if isinstance(o, Mapping) and m not in (o.get("keeps") or ()):
            return str(o.get("reply"))
    return "no"


# ---------------------------------------------------------------------------
# The driver
# ---------------------------------------------------------------------------

Policy = Callable[[Mapping, int], Optional[str]]

_REASON = re.compile(r"\(([a-z][a-z-]*)\)")


def drive(text: str, head: Sequence[str], policy: Policy, session=None,
          interject: Sequence[str] = (), at: Optional[int] = None,
          given_form: bool = False, max_turns: int = 12
          ) -> Dict[str, object]:
    """``text``, then the reply ``policy`` gives to each question left open,
    through the conversation.

    Before the reply numbered ``at`` the turns ``interject`` are asked.  A
    reply the conversation does not read ends the run; with ``given_form``
    it is first asked in the ``given`` form the answer offers (``... given
    <key> is <reply>``).  Returns the final status (``confirmed``,
    ``resolved``, ``open``, ``contradicted``, ``refused`` or ``no tie``), the
    member it ends on, every reply read (its question record, the token read
    and whether it was read by an option number), the texts not read, and
    how many members outside ``head`` were ever live."""
    from ..runtime.conversation import (Conversation, FollowUpError,
                                        reply_rewrite)
    head = tuple(head)
    conv = Conversation(session=session if session is not None
                        else _session())
    sol = conv.ask(text)
    first = conv.turns[-1]
    opened = bool(first.ok and first.question)
    tie = _tie(sol)
    outside: set = set()

    def note(got: Optional[Dict[str, object]]) -> None:
        if got:
            outside.update(x for x in got["live"] if x not in head)

    note(tie)
    reads: List[Dict[str, object]] = []
    unread: List[str] = []
    confirmed = False
    for n in range(max_turns):
        turn = conv.open_tie()
        if turn is None:
            break
        record = turn.question
        if at is not None and n == at:
            for t in interject:
                conv.ask(t)
        say = policy(record, n)
        if say is None:
            break
        if conv.shape_of(say) != "reply":
            unread.append(say)
            if given_form and say.strip():
                sol = conv.ask(reply_rewrite(turn.asked, record, say.strip()))
                got = _tie(sol)
                if got:
                    tie = got
                    note(got)
            break
        try:
            sol = conv.ask(say)
        except FollowUpError:                   # pragma: no cover -- guarded
            unread.append(say)
            break
        binding = conv.turns[-1].binding
        rec = (conv.turns[binding.antecedent_turn].question
               if binding is not None else record)
        token = binding.name if binding is not None else None
        said = say.strip().rstrip("?.!").strip()
        by_number = bool(token is not None and said.isdigit()
                         and str(token).lower() != said.lower())
        reads.append({"n": n, "said": say, "token": token,
                      "key": rec.get("key"), "kind": rec.get("kind"),
                      "yes_no": is_yes_no(rec), "by_number": by_number,
                      "record": rec})
        if rec.get("kind") == "confirm":
            confirmed = True
        got = _tie(sol)
        if got:
            tie = got
            note(got)
        if not sol.ok:
            break
    reason = None
    if not sol.ok:
        error = str(sol.error)
        status = "contradicted" if "(contradicted)" in error else "refused"
        found = _REASON.search(error)
        reason = found.group(1) if found else None
        value = None
    elif tie is None:
        status, value = "no tie", None
    else:
        status = tie["status"]
        live = list(tie["live"])
        if status == "resolved" and confirmed and not tie.get("question"):
            status = "confirmed"
        value = (live[0] if status in ("resolved", "confirmed")
                 and len(live) == 1 else None)
    return {"opened": opened, "status": status, "value": value,
            "reason": reason, "outside": len(outside), "reads": reads,
            "unread": unread}


def _true_of(run: Mapping, v: str, head: Sequence[str]) -> bool:
    """Whether every reply read in ``run`` is true of member ``v``."""
    return all(reply_as(r["record"], v, head) == r["token"]
               for r in run["reads"])


def _wrong_by_number(run: Mapping, m: str) -> bool:
    """The run ends on a member other than ``m`` and some reply was read by
    its number on a yes-or-no question."""
    return (run["value"] not in (None, m)
            and any(r["by_number"] and r["yes_no"] for r in run["reads"]))


# ---------------------------------------------------------------------------
# The informants
# ---------------------------------------------------------------------------

def _truthful(m: str, head: Sequence[str]) -> Policy:
    return lambda record, n: reply_as(record, m, head)


def _every_false(m: str) -> Policy:
    return lambda record, n: _false_reply(record, m)


def _first_false(m: str, head: Sequence[str]) -> Policy:
    def pol(record, n):
        if n == 0 and record.get("kind") != "confirm":
            return _false_reply(record, m)
        return reply_as(record, m, head)
    return pol


def _contradictory(m: str, head: Sequence[str]) -> Policy:
    """The true first reply, then another option of the same question."""
    first: Dict[str, object] = {}

    def pol(record, n):
        if n == 0:
            say = reply_as(record, m, head)
            first.update(record=record, say=say)
            return say
        if n == 1:
            for o in first["record"].get("options", ()):
                if str(o.get("reply")) != first["say"]:
                    return str(o.get("reply"))
        return None
    return pol


def _echo(first_reply: Callable[[Mapping], Optional[str]]) -> Policy:
    """A first reply, then the same text again at the next turn."""
    said: Dict[str, Optional[str]] = {}

    def pol(record, n):
        if n == 0:
            said["text"] = first_reply(record)
            return said["text"]
        if n == 1:
            return said.get("text")
        return None
    return pol


def near_texts(record: Mapping) -> List[str]:
    """A9's texts for one question: its first two options joined four ways,
    their common prefix and their shared register prefix -- each only when
    not empty and not itself an option token."""
    options = [str(o.get("reply")) for o in record.get("options", ())]
    if len(options) < 2:
        return []
    a, b = options[0], options[1]
    out = [f"{a} or {b}", f"{a} and {b}", f"{a} {b}", f"{a}/{b}"]
    tokens = {t.lower() for t in options}
    extra: List[str] = []
    prefix = os.path.commonprefix([a, b]).strip()
    if prefix:
        extra.append(prefix)
    if ":" in a and ":" in b and a.split(":", 1)[0] == b.split(":", 1)[0]:
        extra.append(a.split(":", 1)[0])
    for t in extra:
        if t.lower() not in tokens and t not in out:
            out.append(t)
    return out


# ---------------------------------------------------------------------------
# The measurement, one head (or one outside point) at a time
# ---------------------------------------------------------------------------

def _zero() -> Dict[str, object]:
    reading_a3 = {"confirmed": 0, "confirmed_wrong": 0, "contradicted": 0,
                  "resolved_wrong": 0, "runs": 0, "wrong_by_number": 0}
    reading_a5 = {"confirmed": 0, "contradicted": 0, "echo_read": 0,
                  "echo_read_confirm": 0, "echo_read_confirm_by_number": 0,
                  "runs": 0, "wrong": 0}
    reading_a6 = {"confirmed": 0, "confirmed_wrong": 0,
                  "confirmed_wrong_consistent": 0, "contradicted": 0,
                  "echo_read": 0, "echo_read_confirm": 0,
                  "echo_read_confirm_by_number": 0, "runs": 0,
                  "wrong_by_number": 0}
    return {
        "A0": {"confirmed": 0, "runs": 0, "wrong": 0},
        "A1": {"confirmed_on_impersonated": 0, "confirmed_on_truth": 0,
               "contradicted": 0, "runs": 0},
        "A2": {"confirmed": 0, "confirmed_consistent": 0,
               "confirmed_on_truth": 0, "contradicted": 0, "other": 0,
               "refused": 0, "runs": 0},
        "A2b": {"contradicted": 0, "runs": 0, "wrong": 0},
        "A3": {"given_asked": 0, "given_contradicted": 0,
               "off": dict(reading_a3), "on": dict(reading_a3)},
        "A4": {"read_after_interjection": 0, "runs": 0},
        "A5": {"off": dict(reading_a5), "on": dict(reading_a5)},
        "A6": {"off": dict(reading_a6), "on": dict(reading_a6)},
        "A7": {"confirmed": 0, "contradicted": 0, "points": 0, "refused": 0,
               "reasons": []},
        "A8": {"checked": 0, "given_malformed_asked": 0,
               "given_malformed_refused": 0, "read": []},
        "A9": {"checked": 0, "controls": 0, "controls_read": 0, "read": []},
        "P": {"outside_live": 0, "runs": 0, "values_outside": 0},
        "unopened": 0,
    }


def _merge(a: Dict[str, object], b: Mapping) -> Dict[str, object]:
    """Sum two tallies of :func:`_zero`'s shape (lists are concatenated)."""
    for k, v in b.items():
        if isinstance(v, Mapping):
            _merge(a[k], v)
        elif isinstance(v, list):
            a[k] = list(a[k]) + list(v)
        else:
            a[k] = a[k] + v
    return a


def _tally_p(out: Dict[str, object], run: Mapping,
             head: Sequence[str]) -> None:
    out["P"]["runs"] += 1
    out["P"]["outside_live"] += run["outside"]
    out["P"]["values_outside"] += int(run["value"] is not None
                                      and run["value"] not in head)
    out["unopened"] += int(not run["opened"])


def _head_task(args: Tuple[str, Tuple[str, ...]]) -> Dict[str, object]:
    """Every informant of §3 at one head (A7 excepted)."""
    from ..runtime.conversation import Conversation
    text, head = args
    head = tuple(head)
    session = _session()
    out = _zero()

    def run(policy: Policy, **kw) -> Dict[str, object]:
        return drive(text, head, policy, session=session, **kw)

    for m in head:
        # A0 -- truthful
        r = run(_truthful(m, head))
        _tally_p(out, r, head)
        a = out["A0"]
        a["runs"] += 1
        a["confirmed"] += int(r["status"] == "confirmed" and r["value"] == m)
        a["wrong"] += int(r["value"] not in (None, m))
        # A1 -- consistent liar, every other member impersonated
        for other in head:
            if other == m:
                continue
            r = run(_truthful(other, head))
            _tally_p(out, r, head)
            a = out["A1"]
            a["runs"] += 1
            a["confirmed_on_impersonated"] += int(
                r["status"] == "confirmed" and r["value"] == other)
            a["confirmed_on_truth"] += int(r["status"] == "confirmed"
                                           and r["value"] == m)
            a["contradicted"] += int(r["status"] == "contradicted")
        # A2 -- every reply false
        r = run(_every_false(m))
        _tally_p(out, r, head)
        a = out["A2"]
        a["runs"] += 1
        if r["status"] == "confirmed":
            a["confirmed"] += 1
            a["confirmed_on_truth"] += int(r["value"] == m)
            a["confirmed_consistent"] += int(_true_of(r, r["value"], head))
        elif r["status"] == "contradicted":
            a["contradicted"] += 1
        elif r["status"] == "refused":
            a["refused"] += 1
        else:
            a["other"] += 1
        # A2b -- first reply false
        r = run(_first_false(m, head))
        _tally_p(out, r, head)
        a = out["A2b"]
        a["runs"] += 1
        a["contradicted"] += int(r["status"] == "contradicted")
        a["wrong"] += int(r["value"] not in (None, m))
        # A3 (next turn), A5, A6 -- under both readings
        for reading, on in (("off", False), ("on", True)):
            with switch(on):
                r = run(_contradictory(m, head))
                _tally_p(out, r, head)
                a = out["A3"][reading]
                a["runs"] += 1
                a["confirmed"] += int(r["status"] == "confirmed")
                a["confirmed_wrong"] += int(r["status"] == "confirmed"
                                            and r["value"] != m)
                a["contradicted"] += int(r["status"] == "contradicted")
                a["resolved_wrong"] += int(r["status"] == "resolved"
                                           and r["value"] not in (None, m))
                a["wrong_by_number"] += int(_wrong_by_number(r, m))

                r = run(_echo(lambda rec: reply_as(rec, m, head)))
                _tally_p(out, r, head)
                a = out["A5"][reading]
                echo = [x for x in r["reads"] if x["n"] == 1]
                a["runs"] += 1
                a["confirmed"] += int(r["status"] == "confirmed")
                a["contradicted"] += int(r["status"] == "contradicted")
                a["echo_read"] += len(echo)
                a["echo_read_confirm"] += sum(
                    1 for x in echo if x["kind"] == "confirm")
                a["echo_read_confirm_by_number"] += sum(
                    1 for x in echo if x["kind"] == "confirm"
                    and x["by_number"])
                a["wrong"] += int(r["value"] not in (None, m))

                r = run(_echo(lambda rec: _false_reply(rec, m)))
                _tally_p(out, r, head)
                a = out["A6"][reading]
                echo = [x for x in r["reads"] if x["n"] == 1]
                a["runs"] += 1
                a["confirmed"] += int(r["status"] == "confirmed")
                wrong = r["status"] == "confirmed" and r["value"] != m
                a["confirmed_wrong"] += int(wrong)
                a["confirmed_wrong_consistent"] += int(
                    wrong and _true_of(r, r["value"], head))
                a["contradicted"] += int(r["status"] == "contradicted")
                a["echo_read"] += len(echo)
                a["echo_read_confirm"] += sum(
                    1 for x in echo if x["kind"] == "confirm")
                a["echo_read_confirm_by_number"] += sum(
                    1 for x in echo if x["kind"] == "confirm"
                    and x["by_number"])
                a["wrong_by_number"] += int(_wrong_by_number(r, m))
        # A4 -- an unrelated turn, then the true reply (no resuming)
        with _resume(False):
            r = run(_truthful(m, head), interject=(INTERJECTION,), at=0)
        out["unopened"] += int(not r["opened"])
        out["A4"]["runs"] += 1
        out["A4"]["read_after_interjection"] += sum(
            1 for x in r["reads"] if x["n"] == 0)

    # the first question, for A3's given form, A8 and A9
    conv = Conversation(session=session)
    conv.ask(text)
    turn = conv.open_tie()
    if turn is None:
        out["unopened"] += 1
        return out
    record = turn.question
    key = str(record["key"])
    replies = [str(o["reply"]) for o in record["options"]]
    # A3 -- the given form: two different answers to the first question
    if len(replies) >= 2:
        sol = session.ask(f"{text} given {key} is {replies[0]}; "
                          f"{key} is {replies[1]}")
        out["A3"]["given_asked"] += 1
        out["A3"]["given_contradicted"] += int(
            not sol.ok and "(contradicted)" in str(sol.error))
    # A8 -- malformed texts, and given replies without an answer
    for say in MALFORMED:
        out["A8"]["checked"] += 1
        if conv.shape_of(say) == "reply":
            out["A8"]["read"].append({"head": list(head), "text": say})
    for probe in GIVEN_PROBES:
        sol = session.ask(probe.format(text=text, key=key))
        out["A8"]["given_malformed_asked"] += 1
        out["A8"]["given_malformed_refused"] += int(
            not sol.ok and "(malformed-reply)" in str(sol.error))
    # A9 -- near two options, and the capitalised controls
    for say in near_texts(record):
        out["A9"]["checked"] += 1
        if conv.shape_of(say) == "reply":
            out["A9"]["read"].append({"head": list(head), "text": say})
    for token in replies:
        out["A9"]["controls"] += 1
        out["A9"]["controls_read"] += int(
            conv.shape_of(token.upper()) == "reply")
    return out


def _outside_task(args: Tuple[str, Tuple[str, ...], str]
                  ) -> Dict[str, object]:
    """A7 at one tied point whose origin is not in the head."""
    text, head, origin = args
    head = tuple(head)
    out = _zero()
    r = drive(text, head, _truthful(origin, head), session=_session(),
              given_form=True)
    _tally_p(out, r, head)
    a = out["A7"]
    a["points"] += 1
    a["confirmed"] += int(r["status"] == "confirmed")
    a["contradicted"] += int(r["status"] == "contradicted")
    a["refused"] += int(r["status"] == "refused")
    if r["reason"] and r["status"] == "refused":
        a["reasons"].append(r["reason"])
    return out


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


def lean_marks() -> Dict[str, object]:
    """L1's file, found through ``constants.lean_file``: present, its nine
    theorems stated and no ``sorry`` (the build itself is the build's).  A
    missing file is reported, and the mark is not met."""
    from ..constants import lean_file
    path = lean_file(LEAN_FILE)
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    found = [t for t in LEAN_THEOREMS
             if re.search(rf"\btheorem\s+{re.escape(t)}\b", text)]
    return {"file": LEAN_FILE, "present": bool(text),
            "declared": len(LEAN_THEOREMS), "theorems": len(found),
            "sorry": len(re.findall(r"\bsorry\b", text)),
            "met": bool(text) and len(found) == len(LEAN_THEOREMS)
                   and re.search(r"\bsorry\b", text) is None}


def _heads() -> List[Tuple[str, Tuple[str, ...]]]:
    """The 18 distinct ``nearest`` tied heads, as ``(text, members)``."""
    from . import nearest_question_study as nq
    return [(str(p["text"]), tuple(p["members"]))
            for p in nq._distinct(nq.tie_points())]


def _marks(r: Mapping, lean: Mapping) -> Dict[str, bool]:
    reached = r["unopened"] == 0
    a3, a5, a6 = r["A3"], r["A5"], r["A6"]
    return {
        "L1": bool(lean["met"]),
        "A0": reached and r["A0"]["runs"] > 0
              and r["A0"]["confirmed"] == r["A0"]["runs"]
              and r["A0"]["wrong"] == 0,
        "A1": reached and r["A1"]["runs"] > 0
              and r["A1"]["confirmed_on_impersonated"] == r["A1"]["runs"],
        "A2": reached and r["A2"]["runs"] > 0
              and r["A2"]["confirmed_on_truth"] == 0
              and r["A2"]["confirmed_consistent"] == r["A2"]["confirmed"],
        "A2b": reached and r["A2b"]["runs"] > 0
               and r["A2b"]["contradicted"] == r["A2b"]["runs"]
               and r["A2b"]["wrong"] == 0,
        "A3": reached and a3["given_asked"] > 0
              and a3["given_contradicted"] == a3["given_asked"]
              and a3["off"]["runs"] > 0
              and a3["off"]["confirmed_wrong"] == 0
              and a3["off"]["wrong_by_number"] == 0,
        "A4": reached and r["A4"]["runs"] > 0
              and r["A4"]["read_after_interjection"] == 0,
        "A5": reached and a5["off"]["runs"] > 0
              and a5["off"]["echo_read_confirm_by_number"] == 0,
        "A6": reached and a6["off"]["runs"] > 0
              and a6["off"]["wrong_by_number"] == 0
              and a6["off"]["confirmed_wrong_consistent"]
              == a6["off"]["confirmed_wrong"],
        "A7": reached and r["A7"]["points"] > 0
              and r["A7"]["confirmed"] == 0,
        "A8": reached and r["A8"]["checked"] > 0 and not r["A8"]["read"]
              and r["A8"]["given_malformed_asked"] > 0
              and r["A8"]["given_malformed_refused"]
              == r["A8"]["given_malformed_asked"],
        "A9": reached and r["A9"]["checked"] > 0 and not r["A9"]["read"]
              and r["A9"]["controls"] > 0
              and r["A9"]["controls_read"] == r["A9"]["controls"],
        "P": reached and r["P"]["runs"] > 0
             and r["P"]["outside_live"] == 0
             and r["P"]["values_outside"] == 0,
    }


def compute(workers: Optional[int] = None) -> Dict[str, object]:
    """Run the Phase 167 measurement and return the report dict.

    The heads and the outside points come from
    :func:`nearest_question_study.tie_points` (about a minute and a half);
    the informants then run one head per task, ``workers`` processes at a
    time (default: up to 4)."""
    from concurrent.futures import ProcessPoolExecutor
    from . import nearest_question_study as nq
    points = nq.tie_points()
    heads = [(str(p["text"]), tuple(p["members"]))
             for p in nq._distinct(points)]
    outside = [(str(p["text"]), tuple(p["members"]), str(p["origin"]))
               for p in points if p["truth"] not in p["head_index"]]
    if workers is None:
        workers = max(1, min(4, os.cpu_count() or 1))
    total = _zero()
    if workers <= 1:
        parts = [_head_task(h) for h in heads] + \
                [_outside_task(o) for o in outside]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            parts = list(pool.map(_head_task, heads)) + \
                    list(pool.map(_outside_task, outside))
    for part in parts:
        _merge(total, part)
    total["A7"]["reasons"] = sorted(set(total["A7"]["reasons"]))
    lean = lean_marks()
    marks = _marks(total, lean)
    report: Dict[str, object] = dict(total)
    report.update({
        "phase": 167,
        "heads": len(heads),
        "members": sum(len(h) for _t, h in heads),
        "lean": lean,
        "reading": {
            "switch": "timed_question.YES_NO_BY_NUMBER",
            "switch_present": switch_present(),
            "note": ("on: an option number read on every question; off: a "
                     "yes-or-no question answered by its words only"
                     if switch_present() else
                     "timed_question carries no YES_NO_BY_NUMBER switch: "
                     "both readings were taken with the code's one reading "
                     "(an option number read on every question)"),
        },
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
    })
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

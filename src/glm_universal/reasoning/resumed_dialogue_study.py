"""``glm_universal.reasoning.resumed_dialogue_study`` -- the marks of
``studies/RESUMED_DIALOGUE_STUDY.md`` (Phase 172).

*Created 20 October 2026.  Last altered 20 October 2026 (Phase 173: taken
with ``conversation.OPEN_TIE_STACK`` off, the reading it measured -- the
stack of Phase 173 is measured by ``stacked_dialogue_study``).*

What is measured
----------------
Until this round a reply was read only when the turn just before it had put
the question: Phase 167's informant A4 (an unrelated turn, then the true
reply) had 0 of 48 replies read.  Since this round the conversation keeps the
question open across turns that leave it alone
(:meth:`glm_universal.runtime.conversation.Conversation.open_tie`, switch
``RESUME_OPEN_TIE``).  The marks, declared with this module before the first
run:

* **L1** ``ResumedDialogue.lean`` states its 10 theorems, with no ``sorry``;
* **R0** the control: with the switch off, 0 replies read after an unrelated
  turn, at the ``nearest`` heads and at the ``locate`` junctions;
* **R1** with it on, a truthful reply after 1, 2 or 3 unrelated turns (one of
  them a refusal) is read every time, and every run ends exactly as the
  uninterrupted run ends -- same status, same member;
* **R2** the same for the consistent liar and the first-false informant of
  Phase 167, one unrelated turn before the first reply: every run ends as its
  uninterrupted counterpart;
* **R3** a question is answered once: when a dialogue has ended (no question
  open), an unrelated turn, then each reply of the dialogue said again -- 0
  read;
* **R4** the newest question supersedes: a first tie's question, an unrelated
  turn, a second tie's question, then the first tie's reply -- 0 bound to the
  first tie's turn;
* **R5** no whole query is taken for a reply: with a question open behind an
  unrelated turn, every question of the end-to-end evaluation set is tried --
  0 read as a reply;
* **R6** the ``locate`` junctions (Phase 146), which no adversarial battery
  had reached (Phase 167, section 7.4): truthful informants confirmed on the
  member meant, consistent liars on the member impersonated, a first false
  reply contradicted, 0 malformed texts read;
* **P** over every run, 0 members outside the head ever live and 0 values
  outside it (``GLM.ResumedDialogue.resumed_least``).

Exactness
---------
Strings and integers only.
"""

from __future__ import annotations

import contextlib
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .. import integrity
from . import adversarial_dialogue_study as ad
from . import timed_question as tq

__all__ = [
    "DATA_PATH", "LEAN_FILE", "LEAN_THEOREMS", "INTERJECTIONS", "switch",
    "drive", "compute", "measure", "write_measurements", "measurements",
    "state", "current", "resumed_dialogue_report",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH: Path = _HERE / "_data" / "resumed_dialogue_study.json"

LEAN_FILE = "RequestProject/GLM/ResumedDialogue.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "foldl_strip", "run_unrelated", "run_strip", "resumed_live_eq",
    "resumed_least", "old_rule_drops", "resumed_reads", "reply_closes",
    "newest_supersedes", "agrees_without_unrelated")

#: The unrelated turns, in the order they are interposed: a ``nearest``
#: answer that puts no question (Phase 167's A4 turn), a ``describe`` answer,
#: and a refusal.
INTERJECTIONS: Tuple[str, ...] = (
    ad.INTERJECTION, "describe carbon", "describe no_such_carrier_here")

_SOURCES: Tuple[str, ...] = (
    "reasoning/resumed_dialogue_study.py",
    "reasoning/adversarial_dialogue_study.py",
    "reasoning/nearest_question_study.py",
    "reasoning/answering_question.py",
    "reasoning/timed_question.py",
    "reasoning/coordinate_junction.py",
    "runtime/session.py",
    "runtime/parser.py",
    "runtime/conversation.py",
    "evaluation/cases.py",
)


@contextlib.contextmanager
def switch(resume: bool):
    """Keep a question open across unrelated turns (``True``, the default
    since Phase 172) or read only the previous turn's (``False``)."""
    from ..runtime import conversation as cv
    old = cv.RESUME_OPEN_TIE
    cv.RESUME_OPEN_TIE = resume
    try:
        yield
    finally:
        cv.RESUME_OPEN_TIE = old


@contextlib.contextmanager
def phase172():
    """The reading this study measured: one open question, no stack (Phase
    173's ``OPEN_TIE_STACK`` off)."""
    from ..runtime import conversation as cv
    old = cv.OPEN_TIE_STACK
    cv.OPEN_TIE_STACK = False
    try:
        yield
    finally:
        cv.OPEN_TIE_STACK = old


Policy = Callable[[Dict[str, object], int], Optional[str]]


def drive(text: str, head: Sequence[str], policy: Policy,
          interject: Sequence[str] = (), at: int = 0, max_turns: int = 12
          ) -> Dict[str, object]:
    """``text``, then the reply ``policy`` gives to each question left open,
    through the conversation; before the reply numbered ``at`` the turns
    ``interject`` are asked.  A reply not read ends the run."""
    from ..runtime.conversation import Conversation, FollowUpError
    head = tuple(head)
    conv = Conversation(session=ad._session())
    sol = conv.ask(text)
    tie = ad._tie(sol)
    outside = 0
    said: List[Tuple[str, bool, str]] = []
    confirmed = False
    unread = 0
    for n in range(max_turns):
        turn = conv.open_tie()
        if turn is None:
            break
        record = turn.question
        if n == at:
            for t in interject:
                conv.ask(t)
        say = policy(record, n)
        if say is None:
            break
        read = conv.shape_of(say) == "reply"
        said.append((say, read, str(record["kind"])))
        if not read:
            unread += 1
            break
        try:
            sol = conv.ask(say)
        except FollowUpError:                     # pragma: no cover
            break
        if record["kind"] == "confirm":
            confirmed = True
        got = ad._tie(sol)
        if got:
            tie = got
            outside += sum(1 for m in got["live"] if m not in head)
    if not sol.ok:
        status = ("contradicted" if "(contradicted)" in str(sol.error)
                  else "refused")
        value = None
    elif tie is None:
        status, value = "no tie", None
    else:
        status = tie["status"]
        if status == "resolved" and not tie.get("question") and confirmed:
            status = "confirmed"
        value = tie["live"][0] if len(tie["live"]) == 1 else None
        if status == "contradicted":
            value = None
    return {"status": status, "value": value, "outside": outside,
            "said": [s for s, _r, _k in said], "unread": unread,
            "conversation": conv}


def _plain(run: Dict[str, object]) -> Dict[str, object]:
    return {k: v for k, v in run.items() if k != "conversation"}


# ── the informants (Phase 167's, keyed by the reply's number) ─────────────

def _truthful(m: str, head: Sequence[str]) -> Policy:
    return lambda record, n: ad.reply_as(record, m, head)


def _liar(other: str) -> Policy:
    return lambda record, n: ad.reply_as(record, other)


def _first_false(m: str, head: Sequence[str]) -> Policy:
    def pol(record, n):
        if n == 0 and record["kind"] != "confirm":
            return ad._false_reply(record, m)
        return ad.reply_as(record, m, head)
    return pol


def _same(a: Dict[str, object], b: Dict[str, object]) -> bool:
    return a["status"] == b["status"] and a["value"] == b["value"]


# ── one tie, every reading ────────────────────────────────────────────────

def _tie_runs(args: Tuple[str, str, Tuple[str, ...], Tuple[str, ...]]
             ) -> Dict[str, object]:
    """Every reading over one tie.  ``source`` is ``nearest`` or ``locate``;
    ``texts`` gives, per member, the text that opens its dialogue (one point
    for a ``nearest`` head, ``locate <member>`` for a junction)."""
    source, _label, head, texts = args
    out: Dict[str, object] = {"source": source, "head": list(head),
                              "runs": 0, "outside": 0, "values_outside": 0}
    r0 = {"asked": 0, "read": 0}
    r1 = {"asked": 0, "read": 0, "same": 0}
    r2 = {"asked": 0, "same": 0, "liar_same": 0, "liar": 0,
          "first_false_same": 0, "first_false": 0}
    r3 = {"asked": 0, "read": 0}
    r6 = {"truthful": 0, "truthful_confirmed": 0, "liar": 0,
          "liar_confirmed": 0, "first_false": 0, "first_false_contradicted": 0,
          "malformed": 0, "malformed_read": 0}

    def tally(run, member_head=head):
        out["runs"] += 1
        out["outside"] += run["outside"]
        if run["value"] is not None and run["value"] not in member_head:
            out["values_outside"] += 1

    for m, text in zip(head, texts):
        base = drive(text, head, _truthful(m, head))
        tally(base)
        # R0, the control: the old reading drops the reply
        with switch(False):
            off = drive(text, head, _truthful(m, head),
                        interject=INTERJECTIONS[:1])
        tally(off)
        r0["asked"] += 1
        r0["read"] += int(bool(off["said"]) and off["unread"] == 0)
        # R1: 1, 2, 3 unrelated turns
        for k in (1, 2, 3):
            run = drive(text, head, _truthful(m, head),
                        interject=INTERJECTIONS[:k])
            tally(run)
            r1["asked"] += 1
            r1["read"] += int(run["unread"] == 0 and bool(run["said"]))
            r1["same"] += int(_same(run, base))
        # R2: the liar and the first false reply, interrupted once
        for other in head:
            if other == m:
                continue
            plain = drive(text, head, _liar(other))
            run = drive(text, head, _liar(other), interject=INTERJECTIONS[:1])
            tally(plain)
            tally(run)
            r2["liar"] += 1
            r2["liar_same"] += int(_same(run, plain))
            if source == "locate":
                r6["liar"] += 1
                r6["liar_confirmed"] += int(plain["status"] == "confirmed"
                                            and plain["value"] == other)
        plain = drive(text, head, _first_false(m, head))
        run = drive(text, head, _first_false(m, head),
                    interject=INTERJECTIONS[:1])
        tally(plain)
        tally(run)
        r2["first_false"] += 1
        r2["first_false_same"] += int(_same(run, plain))
        # R3: the dialogue over, an unrelated turn, then every reply again
        conv = base["conversation"]
        if conv.open_tie() is None:
            conv.ask(INTERJECTIONS[0])
            for say in base["said"]:
                r3["asked"] += 1
                r3["read"] += int(conv.shape_of(say) == "reply")
        if source == "locate":
            r6["truthful"] += 1
            r6["truthful_confirmed"] += int(base["status"] == "confirmed"
                                            and base["value"] == m)
            r6["first_false"] += 1
            r6["first_false_contradicted"] += int(
                plain["status"] == "contradicted")
            from ..runtime.conversation import Conversation
            c = Conversation(session=ad._session())
            c.ask(text)
            for say in ad.MALFORMED:
                r6["malformed"] += 1
                r6["malformed_read"] += int(c.shape_of(say) == "reply")
    r2["asked"] = r2["liar"] + r2["first_false"]
    r2["same"] = r2["liar_same"] + r2["first_false_same"]
    out.update(R0=r0, R1=r1, R2=r2, R3=r3, R6=r6)
    return out


def tie_runs(args):
    """:func:`_tie_runs` under the reading of Phase 172 (:func:`phase172`)."""
    with phase172():
        return _tie_runs(args)


def _supersede_runs(args: Tuple[str, Tuple[str, ...], str, str]
                   ) -> Dict[str, int]:
    """R4: the first tie's question, an unrelated turn, the second tie's
    question, then the first tie's true first reply."""
    from ..runtime.conversation import Conversation
    text1, head1, member, text2 = args
    conv = Conversation(session=ad._session())
    conv.ask(text1)
    first = conv.open_tie()
    if first is None:
        return {"asked": 0, "to_first": 0, "read": 0}
    say = ad.reply_as(first.question, member, head1)
    conv.ask(INTERJECTIONS[0])
    conv.ask(text2)
    if conv.open_tie() is None or say is None:
        return {"asked": 0, "to_first": 0, "read": 0}
    read = conv.shape_of(say) == "reply"
    to_first = 0
    if read:
        binding = conv.resolve(say)
        to_first = int(binding.antecedent_turn == first.index)
    return {"asked": 1, "to_first": to_first, "read": int(read)}


def supersede_runs(args):
    """:func:`_supersede_runs` under the reading of Phase 172
    (:func:`phase172`)."""
    with phase172():
        return _supersede_runs(args)


def _hijack_control(args: Tuple[str, Tuple[str, ...]]) -> Dict[str, object]:
    """R5: a question left open behind an unrelated turn, then every question
    of the evaluation set tried as the next text."""
    from ..evaluation.cases import CASES
    from ..runtime.conversation import Conversation
    text, _head = args
    conv = Conversation(session=ad._session())
    conv.ask(text)
    conv.ask(INTERJECTIONS[0])
    if conv.open_tie() is None:
        return {"tried": 0, "read": []}
    read = [c.question for c in CASES if conv.shape_of(c.question) == "reply"]
    return {"tried": len(CASES), "read": read}


def hijack_control(args):
    """:func:`_hijack_control` under the reading of Phase 172
    (:func:`phase172`)."""
    with phase172():
        return _hijack_control(args)


# ── the marks ─────────────────────────────────────────────────────────────

def lean_marks() -> Dict[str, object]:
    root = Path(__file__).resolve().parents[2]
    path = root / "lean" / LEAN_FILE
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    found = [t for t in LEAN_THEOREMS if f"theorem {t}" in text]
    return {"file": LEAN_FILE, "declared": len(LEAN_THEOREMS),
            "theorems": len(found), "sorry": text.count("sorry"),
            "met": len(found) == len(LEAN_THEOREMS) and "sorry" not in text}


def _jobs() -> int:
    return max(1, min(8, int(os.environ.get("GLM_RESUMED_JOBS",
                                            os.cpu_count() or 1))))


def _ties() -> List[Tuple[str, str, Tuple[str, ...], Tuple[str, ...]]]:
    from . import answering_question as aq
    from . import nearest_question_study as nq
    heads = nq._distinct(nq.tie_points())
    out = []
    for p in heads:
        text = nq._point_text(p["point"])
        head = tuple(p["head"])
        out.append(("nearest", text, head, tuple(text for _ in head)))
    for members in aq.sample_junctions(ad._session()):
        out.append(("locate", members[0], tuple(members),
                    tuple(f"locate {m}" for m in members)))
    return out


def compute() -> Dict[str, object]:
    ties = _ties()
    near = [t for t in ties if t[0] == "nearest"]
    sup_args = []
    for i, t in enumerate(near):
        nxt = near[(i + 1) % len(near)]
        for m in t[2]:
            sup_args.append((t[3][0], t[2], m, nxt[3][0]))
    hij_args = [(t[3][0], t[2]) for t in ties]
    jobs = _jobs()
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            per_tie = list(pool.map(tie_runs, ties))
            sup = list(pool.map(supersede_runs, sup_args))
            hij = list(pool.map(hijack_control, hij_args))
    else:
        per_tie = [tie_runs(a) for a in ties]
        sup = [supersede_runs(a) for a in sup_args]
        hij = [hijack_control(a) for a in hij_args]

    def total(key: str, rows=per_tie) -> Dict[str, int]:
        keys = rows[0][key].keys()
        return {k: sum(r[key][k] for r in rows) for k in keys}

    by_source = {s: [r for r in per_tie if r["source"] == s]
                 for s in ("nearest", "locate")}
    report: Dict[str, object] = {
        "ties": {s: len(rs) for s, rs in by_source.items()},
        "members": {s: sum(len(r["head"]) for r in rs)
                    for s, rs in by_source.items()},
        "lean": lean_marks(),
        "R0": {s: total("R0", rs) for s, rs in by_source.items()},
        "R1": {s: total("R1", rs) for s, rs in by_source.items()},
        "R2": {s: total("R2", rs) for s, rs in by_source.items()},
        "R3": total("R3"),
        "R4": {k: sum(r[k] for r in sup) for k in ("asked", "read",
                                                   "to_first")},
        "R5": {"tried": sum(h["tried"] for h in hij),
               "read": sorted({q for h in hij for q in h["read"]})},
        "R6": total("R6", by_source["locate"]),
        "P": {"runs": sum(r["runs"] for r in per_tie),
              "outside_live": sum(r["outside"] for r in per_tie),
              "values_outside": sum(r["values_outside"] for r in per_tie)},
    }
    report["marks"] = _marks(report)
    report["met"] = sum(1 for v in report["marks"].values() if v)
    report["taken"] = len(report["marks"])
    return report


def _marks(r: Dict[str, object]) -> Dict[str, bool]:
    r1 = [r["R1"][s] for s in ("nearest", "locate")]
    r2 = [r["R2"][s] for s in ("nearest", "locate")]
    r6 = r["R6"]
    return {
        "L1": r["lean"]["met"],
        "R0": all(r["R0"][s]["read"] == 0 < r["R0"][s]["asked"]
                  for s in ("nearest", "locate")),
        "R1": all(x["read"] == x["asked"] == x["same"] > 0 for x in r1),
        "R2": all(x["same"] == x["asked"] > 0 for x in r2),
        "R3": r["R3"]["asked"] > 0 and r["R3"]["read"] == 0,
        "R4": r["R4"]["asked"] > 0 and r["R4"]["to_first"] == 0,
        "R5": r["R5"]["tried"] > 0 and not r["R5"]["read"],
        "R6": (r6["truthful_confirmed"] == r6["truthful"] > 0
               and r6["liar_confirmed"] == r6["liar"] > 0
               and r6["first_false_contradicted"] == r6["first_false"] > 0
               and r6["malformed_read"] == 0 < r6["malformed"]),
        "P": r["P"]["outside_live"] == 0 and r["P"]["values_outside"] == 0,
    }


# ── the cache, guarded by a digest ────────────────────────────────────────

def module_digest() -> str:
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / n for n in sorted(set(_SOURCES))],
                                 root)


def measure() -> Dict[str, object]:
    report = compute()
    report["source_digest"] = module_digest()
    return report


def write_measurements(path: Optional[Path] = None) -> Path:
    target = Path(path) if path is not None else DATA_PATH
    target.write_text(json.dumps(measure(), indent=1, sort_keys=True,
                                 ensure_ascii=False) + "\n",
                      encoding="utf-8")
    global _cache
    _cache = None
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return _cache


def state() -> Dict[str, object]:
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    fresh = stored.get("source_digest") == live
    return {"present": True, "fresh": fresh,
            "verdict": "current" if fresh else "stale",
            "live_digest": live, "stored_digest": stored.get("source_digest")}


def current() -> Optional[Dict[str, object]]:
    return measurements() if state()["fresh"] else None


def resumed_dialogue_report() -> Dict[str, object]:
    """The stored marks, or why there are none."""
    stored = current()
    if stored is None:
        return {"available": False, "reason": (
            f"the stored measurement is {state()['verdict']}; re-take it "
            f"with python3 -m glm_universal.tools resumed-dialogue --write")}
    return dict(stored, available=True)

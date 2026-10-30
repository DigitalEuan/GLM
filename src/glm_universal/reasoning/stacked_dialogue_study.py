"""``glm_universal.reasoning.stacked_dialogue_study`` -- the marks of
``studies/STACKED_DIALOGUE_STUDY.md`` (Phase 173).

*Created 20 October 2026.*

What is measured
----------------
Since Phase 172 a question stays open across turns that leave it alone, but
only the newest question can be answered: a second question closes the first
for good (Phase 172's R4), and a question stays open however many unrelated
turns pass.  Since this round the open questions form a stack, newest first
(:meth:`glm_universal.runtime.conversation.Conversation.open_ties`, switch
``OPEN_TIE_STACK``): a reply is read against the newest open question it
fits, or against the turn it names (``turn N: <reply>``); it closes that
question only; and a question closes after ``OPEN_TIE_WINDOW`` (5) unrelated
turns.  The marks, declared with this module before the first run:

* **L1** ``StackedDialogue.lean`` states its 16 theorems, with no ``sorry``;
* **S0** the control: with the stack off (the reading of Phase 172), two ties
  opened one after the other, then the first tie's true reply -- 0 read
  against the first tie;
* **S1** with it on, the same two ties answered in turn, the first then the
  second, by truthful informants (a reply that also fits a newer open
  question is said ``turn N: <reply>``): every reply bound to its own tie's
  turn, the second tie still open when the first ends, and both dialogues
  ending exactly as each ends alone -- same status, same member;
* **S2** the newest wins when it fits: a plain reply to the first tie that is
  also one of the second tie's options is bound to the second, and the
  binding names the first among the other turns it fits, every time;
* **S3** a named reply is read against the turn it names, and only while that
  question is open: ``turn N: <reply>`` bound to turn N every time; the same
  reply naming a turn that put no question, or a question already answered,
  read 0 times;
* **S4** the window: a reply after 5 unrelated turns is read every time, and
  after 6, 0 times;
* **S5** no whole query is taken for a reply: with two questions open behind
  an unrelated turn, every question of the end-to-end evaluation set is
  tried -- 0 read as a reply;
* **P** over every run, 0 members outside the head ever live and 0 values
  outside it (``GLM.StackedDialogue.stacked_least``).

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
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from . import adversarial_dialogue_study as ad
from . import resumed_dialogue_study as rds
from . import timed_question as tq

__all__ = [
    "DATA_PATH", "LEAN_FILE", "LEAN_THEOREMS", "stack", "answer_dialogue",
    "compute", "measure", "write_measurements", "measurements", "state",
    "current", "stacked_dialogue_report",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH: Path = _HERE / "_data" / "stacked_dialogue_study.json"

LEAN_FILE = "RequestProject/GLM/StackedDialogue.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "bound_fits", "bound_newest", "findIdx_bound", "findIdx_of_bound",
    "reply_reads", "reply_erases", "reply_closes_one", "unfit_unread",
    "newest_fit_agrees", "unrelated_within_window", "age_mem",
    "age_iter_ge", "window_closes", "stacked_least", "older_answered",
    "resumed_rule_loses")

_SOURCES: Tuple[str, ...] = (
    "reasoning/stacked_dialogue_study.py",
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
def stack(on: bool):
    """Keep several questions open (``True``, the default since Phase 173)
    or only the newest (``False``, the reading of Phase 172)."""
    from ..runtime import conversation as cv
    old = cv.OPEN_TIE_STACK
    cv.OPEN_TIE_STACK = on
    try:
        yield
    finally:
        cv.OPEN_TIE_STACK = old


def _unrelated(k: int) -> List[str]:
    """``k`` unrelated turns, cycling through Phase 172's interjections."""
    return [rds.INTERJECTIONS[i % len(rds.INTERJECTIONS)] for i in range(k)]


def answer_dialogue(conv, index: int, sol, head: Sequence[str], policy,
                    max_turns: int = 12) -> Dict[str, object]:
    """Answer, through ``conv``, the dialogue whose open question turn
    ``index`` holds, until it ends; ``sol`` is the answer that put it.  A
    reply that a newer open question would also take is said with the turn
    it answers (``turn N: <reply>``).  Ends as
    :func:`resumed_dialogue_study.drive` ends, with the same status."""
    head = tuple(head)
    tie = ad._tie(sol)
    outside = 0
    confirmed = False
    out = {"replies": 0, "addressed": 0, "misbound": 0, "unread": 0}
    for _n in range(max_turns):
        ties = conv.open_ties()
        if index not in [t.index for t in ties]:
            break
        record = conv.turns[index].question
        say = policy(record, _n)
        if say is None:
            break
        newer = [t for t in ties if t.index != index
                 and ties.index(t) < [x.index for x in ties].index(index)]
        if any(tq.match_reply(t.question, say) is not None for t in newer):
            say = f"turn {index}: {say}"
            out["addressed"] += 1
        if conv.shape_of(say) != "reply":
            out["unread"] += 1
            break
        sol = conv.ask(say)
        out["replies"] += 1
        last = conv.turns[-1]
        if last.binding is None or last.binding.antecedent_turn != index:
            out["misbound"] += 1
        if record["kind"] == "confirm":
            confirmed = True
        got = ad._tie(sol)
        if got:
            tie = got
            outside += sum(1 for m in got["live"] if m not in head)
        if last.ok and last.question:
            index = last.index
        else:
            break
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
    out.update(status=status, value=value, outside=outside)
    return out


def _same(a: Dict[str, object], b: Dict[str, object]) -> bool:
    return a["status"] == b["status"] and a["value"] == b["value"]


Tie = Tuple[str, str, Tuple[str, ...], Tuple[str, ...]]


def pair_runs(args: Tuple[Tie, Tie]) -> Dict[str, object]:
    """Every reading over one ordered pair of ties: the first opened, then
    the second, then each answered."""
    from ..runtime.conversation import Conversation
    (src_a, _la, head_a, texts_a), (src_b, _lb, head_b, texts_b) = args
    out: Dict[str, object] = {"runs": 0, "outside": 0, "values_outside": 0}
    s0 = {"asked": 0, "to_first": 0}
    s1 = {"asked": 0, "same_first": 0, "same_second": 0, "misbound": 0,
          "second_open": 0, "addressed": 0, "replies": 0}
    s2 = {"fit_both": 0, "to_newest": 0, "names_first": 0}
    s3 = {"asked": 0, "to_named": 0, "no_question": 0, "no_question_read": 0,
          "answered": 0, "answered_read": 0}
    s5 = {"tried": 0, "read": []}

    def tally(run, head):
        out["runs"] += 1
        out["outside"] += run["outside"]
        if run["value"] is not None and run["value"] not in head:
            out["values_outside"] += 1

    mb = head_b[0]
    with stack(True):
        base_b = rds.drive(texts_b[0], head_b, rds._truthful(mb, head_b))
    for k, (m, text_a) in enumerate(zip(head_a, texts_a)):
        text_b = texts_b[k % len(texts_b)]
        mb = head_b[k % len(head_b)]
        with stack(True):
            base_a = rds.drive(text_a, head_a, rds._truthful(m, head_a))
            base_b = rds.drive(text_b, head_b, rds._truthful(mb, head_b))
        tally(base_a, head_a)
        tally(base_b, head_b)
        # S0, the control: the reading of Phase 172
        with stack(False):
            conv = Conversation(session=ad._session())
            conv.ask(text_a)
            first = conv.open_tie()
            conv.ask(text_b)
            if first is not None and conv.open_tie() is not None:
                say = ad.reply_as(first.question, m, head_a)
                if say is not None:
                    s0["asked"] += 1
                    if conv.shape_of(say) == "reply":
                        s0["to_first"] += int(
                            conv.resolve(say).antecedent_turn == first.index)
        with stack(True):
            # S1: both dialogues, interleaved
            conv = Conversation(session=ad._session())
            sol_a = conv.ask(text_a)
            ia = conv.open_tie()
            sol_b = conv.ask(text_b)
            ib = conv.open_tie()
            if ia is None or ib is None or ia.index == ib.index:
                continue
            # S2 and S3 on the first reply, before anything is answered
            say = ad.reply_as(ia.question, m, head_a)
            if say is not None:
                if tq.match_reply(ib.question, say) is not None:
                    s2["fit_both"] += 1
                    b = conv.resolve(say)
                    s2["to_newest"] += int(b.antecedent_turn == ib.index)
                    s2["names_first"] += int(ia.index in b.also)
                s3["asked"] += 1
                named = f"turn {ia.index}: {say}"
                if conv.shape_of(named) == "reply":
                    s3["to_named"] += int(
                        conv.resolve(named).antecedent_turn == ia.index)
                s3["no_question"] += 1
                s3["no_question_read"] += int(
                    conv.shape_of(f"turn {ib.index + 7}: {say}") == "reply")
            # S5: two questions open behind an unrelated turn
            if k == 0:
                from ..evaluation.cases import CASES
                probe = Conversation(session=ad._session())
                probe.ask(text_a)
                probe.ask(text_b)
                probe.ask(rds.INTERJECTIONS[0])
                if len(probe.open_ties()) == 2:
                    s5["tried"] += len(CASES)
                    s5["read"] += [c.question for c in CASES
                                   if probe.shape_of(c.question) == "reply"]
            run_a = answer_dialogue(conv, ia.index, sol_a, head_a,
                                    rds._truthful(m, head_a))
            open_b = [t for t in conv.open_ties() if t.index == ib.index]
            run_b = answer_dialogue(conv, ib.index, sol_b, head_b,
                                    rds._truthful(mb, head_b))
            tally(run_a, head_a)
            tally(run_b, head_b)
            s1["asked"] += 1
            s1["same_first"] += int(_same(run_a, base_a))
            s1["same_second"] += int(_same(run_b, base_b))
            s1["misbound"] += run_a["misbound"] + run_b["misbound"]
            s1["second_open"] += int(bool(open_b))
            s1["addressed"] += run_a["addressed"] + run_b["addressed"]
            s1["replies"] += run_a["replies"] + run_b["replies"]
            # S3: a question already answered cannot be named
            if say is not None and ia.index not in [
                    t.index for t in conv.open_ties()]:
                s3["answered"] += 1
                s3["answered_read"] += int(
                    conv.shape_of(f"turn {ia.index}: {say}") == "reply")
    s5["read"] = sorted(set(s5["read"]))
    out.update(S0=s0, S1=s1, S2=s2, S3=s3, S5=s5)
    return out


def window_runs(args: Tie) -> Dict[str, int]:
    """S4: one tie's question, then ``W`` (and ``W + 1``) unrelated turns,
    then its true first reply."""
    from ..runtime import conversation as cv
    from ..runtime.conversation import Conversation
    _src, _label, head, texts = args
    m, text = head[0], texts[0]
    out = {"inside": 0, "inside_read": 0, "past": 0, "past_read": 0,
           "past_named": 0}
    with stack(True):
        conv = Conversation(session=ad._session())
        conv.ask(text)
        first = conv.open_tie()
        if first is None:
            return out
        say = ad.reply_as(first.question, m, head)
        if say is None:
            return out
        for t in _unrelated(cv.OPEN_TIE_WINDOW):
            conv.ask(t)
        out["inside"] = 1
        out["inside_read"] = int(conv.shape_of(say) == "reply")
        conv.ask(_unrelated(cv.OPEN_TIE_WINDOW + 1)[-1])
        out["past"] = 1
        out["past_read"] = int(conv.shape_of(say) == "reply")
        # observed, not a mark (added after the first take): the late reply
        # is said to be late -- the window-closed question it would answer
        out["past_named"] = int(conv.expired_fit(say) == (first.index,))
    return out


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
    return max(1, min(8, int(os.environ.get("GLM_STACKED_JOBS",
                                            os.cpu_count() or 1))))


def compute() -> Dict[str, object]:
    ties = rds._ties()
    pairs = [(t, ties[(i + 1) % len(ties)]) for i, t in enumerate(ties)]
    jobs = _jobs()
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            per_pair = list(pool.map(pair_runs, pairs))
            win = list(pool.map(window_runs, ties))
    else:
        per_pair = [pair_runs(p) for p in pairs]
        win = [window_runs(t) for t in ties]

    def total(key: str) -> Dict[str, int]:
        keys = [k for k in per_pair[0][key] if k != "read"]
        return {k: sum(r[key][k] for r in per_pair) for k in keys}

    report: Dict[str, object] = {
        "ties": len(ties), "pairs": len(pairs),
        "lean": lean_marks(),
        "S0": total("S0"), "S1": total("S1"), "S2": total("S2"),
        "S3": total("S3"),
        "S4": {k: sum(w[k] for w in win) for k in win[0]},
        "S5": {"tried": sum(r["S5"]["tried"] for r in per_pair),
               "read": sorted({q for r in per_pair for q in r["S5"]["read"]})},
        "P": {"runs": sum(r["runs"] for r in per_pair),
              "outside_live": sum(r["outside"] for r in per_pair),
              "values_outside": sum(r["values_outside"] for r in per_pair)},
    }
    report["marks"] = _marks(report)
    report["met"] = sum(1 for v in report["marks"].values() if v)
    report["taken"] = len(report["marks"])
    return report


def _marks(r: Dict[str, object]) -> Dict[str, bool]:
    s1, s2, s3, s4 = r["S1"], r["S2"], r["S3"], r["S4"]
    return {
        "L1": r["lean"]["met"],
        "S0": r["S0"]["asked"] > 0 and r["S0"]["to_first"] == 0,
        "S1": (s1["asked"] > 0 and s1["same_first"] == s1["asked"]
               and s1["same_second"] == s1["asked"]
               and s1["second_open"] == s1["asked"] and s1["misbound"] == 0),
        "S2": s2["to_newest"] == s2["names_first"] == s2["fit_both"],
        "S3": (s3["to_named"] == s3["asked"] > 0
               and s3["no_question_read"] == 0 < s3["no_question"]
               and s3["answered_read"] == 0),
        "S4": (s4["inside_read"] == s4["inside"] > 0
               and s4["past_read"] == 0 < s4["past"]),
        "S5": r["S5"]["tried"] > 0 and not r["S5"]["read"],
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


def stacked_dialogue_report() -> Dict[str, object]:
    """The stored marks, or why there are none."""
    stored = current()
    if stored is None:
        return {"available": False, "reason": (
            f"the stored measurement is {state()['verdict']}; re-take it "
            f"with python3 -m glm_universal.tools stacked-dialogue --write")}
    return dict(stored, available=True)

"""``glm_universal.reasoning.answering_question`` -- the question in the
answering path (Phase 146).

``studies/ANSWERING_QUESTION_STUDY.md`` pre-registered ten marks; this module
measures them.  The round put Phase 145's question into the ``locate`` answer
itself: a junction answer ends with the question that would split it, the
request grammar takes replies (``locate albedo given word:absorbed is no``), and
the conversation reads a reply to the question the previous turn put as its
next turn (the ``reply`` shape of :mod:`..runtime.conversation`).

What is measured
----------------
* **F1** the frozen path: every evaluation case recorded before the answering
  path moved (``_data/answering_question_baseline.json``) asked again.
* **E1** the new evaluation cases.
* **C1, C2, C3, T1** the 13 dialogues of the 142-carrier sample, one per
  member of the three junctions ``locate`` answers, run as conversations with
  a truthful replier (C1), each turn verified by column 3 (C2) and with its
  claims altered (T1); and with a replier that lies once (C3).
* **Q1** the answering path's own loop (:func:`timed_question.pending_question`,
  :func:`timed_question.apply_given`) on Phase 145's 387 full-register runs.
* **R1** a reply is read only where a question was put: the conversation and
  discourse reports against the ones taken before the round
  (``_data/answering_question_discourse_before.json``), and six controls.
* **D1** ``GLM.py --converse`` on the declared dialogue.

F1 asks 198 questions and R1 re-takes two reports, about twenty minutes in
all, so the measurement is stored beside the digest of its sources
(``tools answering-question --write``) and read from there.

Exactness
---------
Strings, ints and :class:`fractions.Fraction` only.
"""

from __future__ import annotations

import dataclasses
import io
import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from . import timed_question as tq

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "BASELINE_PATH", "DISCOURSE_BEFORE_PATH",
    "DATA_PATH", "TREE_CAUSES", "JUNCTION_CASES", "CONTROLS",
    "sample_junctions", "conversation_run", "f1_frozen_path",
    "c_dialogues", "q1_loop", "r1_controls", "r1_reports", "d1_converse",
    "measure", "write_measurements", "measurements", "state",
    "answering_question_report",
]

LEAN_FILE = tq.ANSWER_LEAN_FILE
LEAN_THEOREMS = tq.ANSWER_LEAN_THEOREMS

_HERE = Path(__file__).resolve().parent
BASELINE_PATH: Path = _HERE / "_data" / "answering_question_baseline.json"
DISCOURSE_BEFORE_PATH: Path = (_HERE / "_data"
                               / "answering_question_discourse_before.json")
DATA_PATH: Path = _HERE / "_data" / "answering_question.json"

#: Cases whose text is a figure the tree measures of itself: the Lean
#: declaration count and what is drawn from it (the new Lean file moves it).
TREE_CAUSES: Dict[str, str] = {
    "report-lean": "the Lean declaration count, measured live",
    "report-retrieval": "the address-book index over the Lean declarations",
    "report-relay": "the stack relay's strides are drawn from the Lean "
                    "declarations",
    "report-anonymous": "the anonymous register's queries are the relay's "
                        "strides",
    "report-generated": "the overlay's stored bytes, measured live",
}

#: The junction answers of ``locate``: the round's own cause.
JUNCTION_CASES: Tuple[str, ...] = ("locate-junction", "locate-junction-moved")

#: Texts that are options of some question, as a first turn or after a turn
#: that put none: none may be read as a reply.
CONTROLS: Tuple[str, ...] = ("yes", "no", "1", "2", "albedo", "dB")

_SOURCES: Tuple[str, ...] = (
    "reasoning/answering_question.py",
    "reasoning/timed_question.py",
    "reasoning/_data/answering_question_baseline.json",
    "reasoning/_data/answering_question_discourse_before.json",
    "runtime/session.py",
    "runtime/conversation.py",
    "runtime/discourse.py",
    "runtime/tct_engine.py",
    "evaluation/cases.py",
)


def _session():
    from ..runtime.session import GeometricSession
    return GeometricSession()


# ═════════════════════════════════════════════════════════════════════════
# F1 -- the frozen path
# ═════════════════════════════════════════════════════════════════════════

def f1_frozen_path(session=None) -> Dict[str, object]:
    """Every case of the baseline asked again: present, same status, and the
    cause of every moved text."""
    from ..evaluation import cases as ev
    session = session or _session()
    questions = {c.id: c.question for c in ev.CASES}
    before = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))["before"]
    rows = []
    for b in before:
        cid = str(b["id"])
        if cid not in questions:
            rows.append({"id": cid, "present": False, "same_status": False,
                         "same_text": False, "cause": "absent"})
            continue
        after = session.ask(questions[cid])
        same_text = after.answer == b["answer"]
        if same_text:
            cause = None
        elif cid in JUNCTION_CASES and after.answer.startswith(b["answer"]):
            cause = "this round: the junction answer ends with its question"
        elif cid in TREE_CAUSES:
            cause = "the tree: " + TREE_CAUSES[cid]
        else:
            cause = "undeclared"
        rows.append({"id": cid, "present": True,
                     "same_status": bool(after.ok) == bool(b["ok"]),
                     "same_text": same_text, "cause": cause})
    new = sorted(set(questions) - {str(b["id"]) for b in before})
    moved = [r for r in rows if r["present"] and not r["same_text"]]
    return {"cases": len(rows),
            "present": sum(r["present"] for r in rows),
            "same_status": sum(r["same_status"] for r in rows),
            "same_text": sum(r["present"] and r["same_text"] for r in rows),
            "moved": [{"id": r["id"], "cause": r["cause"]} for r in moved],
            "undeclared": [r["id"] for r in moved
                           if r["cause"] == "undeclared"],
            "new_cases": new}


def e1_new_cases(session=None) -> Dict[str, object]:
    """The evaluation cases this round adds, judged as the evaluation judges
    them (answered with every pinned fragment, or refused)."""
    from ..evaluation import cases as ev
    session = session or _session()
    out = []
    for c in ev.CASES:
        if not c.id.startswith("locate-reply"):
            continue
        sol = session.ask(c.question)
        if c.expect == "answer":
            ok = (bool(sol.ok) and all(f in sol.answer for f in c.contains)
                  and not any(f in sol.answer for f in c.forbids))
        else:
            ok = not sol.ok
        out.append({"id": c.id, "as_declared": ok})
    return {"cases": len(out), "as_declared": sum(r["as_declared"]
                                                  for r in out),
            "rows": out}


# ═════════════════════════════════════════════════════════════════════════
# C1-C3, T1 -- the dialogues of the sample
# ═════════════════════════════════════════════════════════════════════════

def sample_junctions(session=None) -> List[Tuple[str, ...]]:
    """The junctions of the 142-carrier sample that ``locate`` answers, each
    in carrier order."""
    from . import address_read as adr
    from . import address_table as adt
    session = session or _session()
    rows = adt.carriers()
    groups: Dict[Tuple[Fraction, ...], List[str]] = {}
    for i, row in enumerate(rows):
        key = tuple(Fraction(x) for x in row[2])
        groups.setdefault(key, []).append(adr.carrier_label(rows, i))
    out = []
    for members in groups.values():
        if len(members) < 2:
            continue
        sol = session.ask(f"locate {members[0]}")
        if sol.ok and tuple(sol.payload.get("junction") or ()) == \
                tuple(members):
            out.append(tuple(members))
    return out


def _truthful_reply(record, truth: str, members: Sequence[str]) -> str:
    """The reply the carrier meant gives: the option that keeps it, else
    (after a false reply removed it) its own answer, which no live member
    gives."""
    if record["kind"] == "confirm":
        keeps = record["options"][0]["keeps"]
        return "yes" if truth in keeps else "no"
    for o in record["options"]:
        if truth in o["keeps"]:
            return str(o["reply"])
    q = tq.question_of(tq.junction_tie(members), record["key"])
    return tq.answer_token(q.answer_of(truth))


def _false_reply(record, truth: str) -> str:
    for o in record["options"]:
        if truth not in o["keeps"]:
            return str(o["reply"])
    raise AssertionError("no false option")   # pragma: no cover


def conversation_run(members: Sequence[str], truth: str, lie: bool = False,
                     session=None, verify: bool = False,
                     tamper: bool = False) -> Dict[str, object]:
    """One dialogue: ``locate <truth>``, then a reply to every question put
    until none is.  ``lie`` makes the reply to the first question false."""
    from ..runtime.conversation import Conversation, FollowUpError
    conv = Conversation(session=session or _session())
    texts = [f"locate {truth}"]
    sol = conv.ask(texts[0])
    replies = confirms = verified = tampered = rejected = 0
    reasons: List[str] = []
    while True:
        if verify:
            v, t, r = _verify(sol, tamper)
            verified += v
            tampered += t
            rejected += r
        turn = conv.turns[-1]
        if not turn.ok or not turn.question:
            break
        record = turn.question
        if lie and replies == 0 and record["kind"] != "confirm":
            text = _false_reply(record, truth)
        else:
            text = _truthful_reply(record, truth, members)
        if conv.shape_of(text) != "reply":
            reasons.append(f"unread reply {text!r}")
            break
        try:
            sol = conv.ask(text)
        except FollowUpError as error:          # pragma: no cover
            reasons.append(str(error))
            break
        texts.append(text)
        if record["kind"] == "confirm":
            confirms += 1
        else:
            replies += 1
    last = conv.turns[-1]
    tie = dict(sol.payload).get("tie") if sol.ok else None
    if not sol.ok:
        status = ("contradicted" if "(contradicted)" in str(sol.error)
                  else "refused")
        value = None
    else:
        status = tie["status"] if tie else "no tie"
        if status == "resolved" and confirms:
            status = "confirmed"
        value = tie["live"][0] if tie and len(tie["live"]) == 1 else None
    return {"truth": truth, "n": len(members), "texts": texts,
            "asked": last.asked, "replies": replies, "confirms": confirms,
            "status": status, "value": value, "turns": len(conv.turns),
            "verified": verified, "tampered": tampered, "rejected": rejected,
            "problems": reasons}


def _verify(sol, tamper: bool) -> Tuple[int, int, int]:
    """Column 3 on one turn; with ``tamper``, each claim of this round
    altered in turn must be rejected."""
    from ..runtime.tct_engine import build_trace, verify_trace
    if not sol.ok:
        return 0, 0, 0
    ok = int(bool(verify_trace(build_trace(sol)).verified))
    t = r = 0
    if tamper:
        exp = dict(sol.expected)
        members = list(dict(sol.payload).get("junction") or ())
        for key in ("live", "asks"):
            if key not in exp:
                continue
            altered = dict(exp)
            if key == "live":
                others = [m for m in members if m not in
                          exp["live"].split("|")]
                altered["live"] = (others[0] if others else "")
            else:
                head, _, split = exp["asks"].partition(" -> ")
                groups = split.split(" / ")
                altered["asks"] = head + " -> " + " / ".join(
                    reversed(groups)) if len(groups) > 1 else exp["asks"]
                if altered["asks"] == exp["asks"]:
                    altered["asks"] = head + " -> " + "|".join(members)
            t += 1
            bad = dataclasses.replace(sol, expected=altered)
            r += int(not verify_trace(build_trace(bad)).verified)
    return ok, t, r


def c_dialogues(session=None, verify: bool = True) -> Dict[str, object]:
    """C1-C3 and T1 over the sample's answered junctions."""
    session = session or _session()
    junctions = sample_junctions(session)
    honest, liars = [], []
    for members in junctions:
        for truth in members:
            honest.append(conversation_run(members, truth, session=session,
                                           verify=verify, tamper=verify))
            liars.append(conversation_run(members, truth, lie=True,
                                          session=session))
    c1_ok = [r for r in honest if r["status"] == "confirmed"
             and r["value"] == r["truth"] and not r["problems"]]
    within = [r for r in honest if r["replies"] <= r["n"] - 1
              and r["replies"] <= tq.clog2(r["n"]) + 1]
    turns = sum(r["turns"] for r in honest)
    return {
        "junctions": [list(j) for j in junctions],
        "runs": len(honest),
        "c1": {"confirmed_on_truth": len(c1_ok),
               "wrong": sum(1 for r in honest if r["value"] not in
                            (None, r["truth"])),
               "within_bounds": len(within),
               "replies": [r["replies"] for r in honest],
               "replies_total": sum(r["replies"] for r in honest)},
        "c2": {"turns": turns, "verified": sum(r["verified"]
                                               for r in honest)},
        "t1": {"altered": sum(r["tampered"] for r in honest),
               "rejected": sum(r["rejected"] for r in honest)},
        "c3": {"runs": len(liars),
               "contradicted": sum(r["status"] == "contradicted"
                                   for r in liars),
               "ended_wrong": sum(1 for r in liars if r["value"] not in
                                  (None, r["truth"])),
               "replies": [r["replies"] for r in liars]},
        "rows": honest,
    }


# ═════════════════════════════════════════════════════════════════════════
# Q1 -- the answering path's loop on the full registers
# ═════════════════════════════════════════════════════════════════════════

def q1_loop(junctions=None) -> Dict[str, object]:
    """Phase 145's 387 runs, through ``pending_question`` and
    ``apply_given`` (the functions ``_locate_question`` calls) instead of
    ``resolve``: the replies are re-applied from the start on every turn,
    as the rewritten query is."""
    junctions = junctions if junctions is not None else \
        tq.register_junctions()
    runs = resolved = wrong = within = 0
    total = 0
    for members in junctions:
        for truth in members:
            runs += 1
            given: List[Tuple[str, str]] = []
            while True:
                tie = tq.apply_given(tq.junction_tie(members), given)
                q = tq.pending_question(tie)
                if q is None or q.kind == "confirm":
                    break
                given.append((q.key, tq.answer_token(q.answer_of(truth))))
            replies = len(given)
            total += replies
            if tie.status == "resolved":
                resolved += 1
                wrong += tie.value != truth
            within += replies <= len(members) - 1
    return {"junctions": len(junctions), "runs": runs, "resolved": resolved,
            "wrong": wrong, "within_n_minus_1": within,
            "questions_total": total, "phase_145_total": 1280}


# ═════════════════════════════════════════════════════════════════════════
# R1 -- a reply only where a question was put
# ═════════════════════════════════════════════════════════════════════════

def r1_controls(session=None) -> Dict[str, object]:
    from ..runtime.conversation import Conversation
    session = session or _session()
    read_as_reply = []
    checked = 0
    for prefix in ((), ("describe carbon",)):
        for text in CONTROLS:
            conv = Conversation(session=session)
            for p in prefix:
                conv.ask(p)
            checked += 1
            if conv.shape_of(text) == "reply":
                read_as_reply.append((prefix, text))
    return {"checked": checked, "read_as_reply": read_as_reply}


def r1_reports() -> Dict[str, object]:
    """The conversation and discourse reports, against the ones taken on
    the tree before the round; every differing path is listed."""
    from ..runtime.conversation import conversation_report
    from ..runtime.discourse_report import discourse_report
    after = json.loads(json.dumps(
        {"conversation": conversation_report(),
         "discourse": discourse_report(census=True)},
        default=str, sort_keys=True))
    before = json.loads(DISCOURSE_BEFORE_PATH.read_text(encoding="utf-8"))
    diffs: List[Dict[str, object]] = []

    def walk(x, y, path):
        if type(x) is not type(y):
            diffs.append({"path": path, "before": repr(x)[:80],
                          "after": repr(y)[:80]})
        elif isinstance(x, dict):
            for k in sorted(set(x) | set(y)):
                if k not in x or k not in y:
                    diffs.append({"path": f"{path}/{k}", "before":
                                  "absent" if k not in x else "present",
                                  "after": "absent" if k not in y
                                  else "present"})
                else:
                    walk(x[k], y[k], f"{path}/{k}")
        elif isinstance(x, list):
            if len(x) != len(y):
                diffs.append({"path": path, "before": len(x),
                              "after": len(y)})
            else:
                for i, (u, v) in enumerate(zip(x, y)):
                    walk(u, v, f"{path}/{i}")
        elif x != y:
            diffs.append({"path": path, "before": repr(x)[:80],
                          "after": repr(y)[:80]})

    walk(before, after, "")
    return {"differences": diffs}


# ═════════════════════════════════════════════════════════════════════════
# D1 -- the command line
# ═════════════════════════════════════════════════════════════════════════

def d1_converse() -> Dict[str, object]:
    import importlib.util
    path = _HERE.parents[1] / "GLM.py"
    spec = importlib.util.spec_from_file_location("_glm_cli_146", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    buf = io.StringIO()
    code = mod.main(["--converse", "locate albedo", "--converse", "no",
                     "--converse", "yes"], out=buf)
    text = buf.getvalue()
    lines = text.splitlines()
    ok = (code == 0
          and sum(1 for ln in lines if ln.startswith("ASKS")) == 2
          and sum(1 for ln in lines if ln.startswith("BOUND   reply")) == 2
          and lines[-1].startswith("ANSWER")
          and "it is physics:albedo" in lines[-1]
          and "the confirming reply agrees" in lines[-1])
    return {"exit": code, "as_declared": ok,
            "lines": [ln[:160] for ln in lines]}


# ═════════════════════════════════════════════════════════════════════════
# The measurement, stored beside its digest
# ═════════════════════════════════════════════════════════════════════════

def module_digest() -> str:
    root = _HERE.parent
    return integrity.tree_digest([root / name for name in _SOURCES], root)


def measure() -> Dict[str, object]:
    session = _session()
    return {"f1": f1_frozen_path(session), "e1": e1_new_cases(session),
            "c": c_dialogues(session), "q1": q1_loop(),
            "r1": {"controls": r1_controls(session),
                   "reports": r1_reports()},
            "d1": d1_converse(), "source_digest": module_digest()}


def write_measurements(path: Optional[Path] = None) -> Path:
    target = Path(path) if path is not None else DATA_PATH
    target.write_text(json.dumps(measure(), indent=1, sort_keys=True,
                                 default=str) + "\n", encoding="utf-8")
    return target


def measurements() -> Optional[Dict[str, object]]:
    if not DATA_PATH.exists():
        return None
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def state() -> Dict[str, object]:
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent"}
    same = stored.get("source_digest") == live
    return {"present": True, "fresh": same,
            "verdict": "fresh" if same else "stale"}


def answering_question_report() -> Dict[str, object]:
    """Every mark of ``studies/ANSWERING_QUESTION_STUDY.md`` from the stored
    measurement (L1 is pinned by the build)."""
    data = measurements()
    if data is None or data.get("source_digest") != module_digest():
        return {"available": False, "reason": (
            "the measurement is absent or stale; re-take it with "
            "python3 -m glm_universal.tools answering-question --write")}
    f1, e1, c, q1, r1, d1 = (data["f1"], data["e1"], data["c"], data["q1"],
                             data["r1"], data["d1"])
    tree = {"the tree: " + v for v in TREE_CAUSES.values()}
    marks = {
        "F1": (f1["present"] == f1["cases"] == f1["same_status"]
               and not f1["undeclared"]
               and all(m["cause"].startswith("this round")
                       or m["cause"] in tree for m in f1["moved"])),
        "E1": e1["cases"] > 0 and e1["as_declared"] == e1["cases"],
        "C1": (c["c1"]["confirmed_on_truth"] == c["runs"] == 13
               and c["c1"]["wrong"] == 0
               and c["c1"]["within_bounds"] == c["runs"]),
        "C2": c["c2"]["verified"] == c["c2"]["turns"] > 0,
        "C3": (c["c3"]["contradicted"] == c["c3"]["runs"] > 0
               and c["c3"]["ended_wrong"] == 0),
        "Q1": (q1["resolved"] == q1["runs"] == 387 and q1["wrong"] == 0
               and q1["within_n_minus_1"] == q1["runs"]
               and q1["questions_total"] == q1["phase_145_total"]),
        "R1": (not r1["controls"]["read_as_reply"]
               and not r1["reports"]["differences"]),
        "T1": c["t1"]["rejected"] == c["t1"]["altered"] > 0,
        "D1": bool(d1["as_declared"]),
    }
    return {"available": True, "lean_file": LEAN_FILE,
            "lean_theorems": list(LEAN_THEOREMS), "f1": f1, "e1": e1,
            "c1": c["c1"], "c2": c["c2"], "c3": c["c3"], "t1": c["t1"],
            "q1": q1, "r1": r1, "d1": d1, "marks": marks,
            "met": sum(marks.values()) + 1, "taken": len(marks) + 1}

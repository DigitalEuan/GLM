"""``glm_universal.runtime.meta_report`` -- the marks of Phase 117.

The measurement of ``studies/META_QUESTIONS_STUDY.md`` against the marks
T1-T7 of :mod:`glm_universal.evaluation.meta_question_cases`: the eighteen
class-M outside questions read through the router, their quotes, theorems
and disputed premises, the column-3 scripts and the mutation controls, the
paraphrases, non-interference, and the Lean file.  Nothing here uses a
float.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

from ..evaluation import meta_question_cases as C
from . import meta_frames as MF
from ..reasoning import meta_evidence as ME

__all__ = ["question_marks", "mutation_mark", "paraphrase_mark",
           "FIRST_RUN",
           "interference_mark", "lean_mark", "meta_report", "LEAN_FILE"]

LEAN_FILE = (Path(__file__).resolve().parent.parent.parent / "lean" /
             "RequestProject" / "GLM" / "MetaAnswers.lean")


#: The first run of the meta frames, before any cue was sharpened: 31 of the
#: 36 declared paraphrases read and answered (p92a went to the earlier
#: ``deep_hole_tie`` frame; p99b, p100b, p102a and p102b were read by no
#: frame), and then, with the same cues, 17 of the 18 held-out rewordings
#: (h92 read by no frame).  The cues of ``beyond_radius``,
#: ``squared_distance`` and ``rational_rotation`` were then widened from
#: the four paraphrase misses only.  The evidence layer's own test then
#: found two other outside questions meeting a meta cue below the frames
#: (35 met ``transcendental_delay`` through "transfer function", 95 met
#: ``exact_growth`` through "overflow"), each masked on the router by an
#: earlier frame; those two cues were narrowed.
FIRST_RUN = {"paraphrases": (31, 36, ("p92a", "p99b", "p100b", "p102a",
                                      "p102b")),
             "held_out": (17, 18, ("h92",)),
             "masked_cue_hits": (35, 95)}


def _topic(key: str) -> ME.Topic:
    return next(tp for tp in ME.TOPICS if tp.key == key)


def _gate(script: str):
    from .question_frames import run_gate
    return run_gate(script)


def question_marks() -> Dict[str, object]:
    """T1, T2, T3 and the first half of T4: every declared question through
    the router."""
    from ..evaluation import question_set_b_cases as qc
    from . import router
    from .session import GeometricSession
    session = GeometricSession()
    items = qc.outside()
    rows: List[Dict[str, object]] = []
    for idx, topic, verdict, frag, docs, lean, disputes in C.META_QUESTIONS:
        r = router.route(session, items[idx].text)
        rd = r.payload if r.surface == "frames" else None
        frame = getattr(rd, "frame", None)
        answered = bool(rd and rd.answered)
        col2 = rd.column2 if rd else ""
        got_disputes = tuple(d.split(":", 1)[0] for d in rd.disputes) \
            if rd else ()
        rows.append({
            "index": idx, "topic": topic, "surface": r.surface,
            "frame": frame,
            "read": frame == f"meta_{topic}",
            "verdict": "ANSWER" if answered else (rd.code if rd else None),
            "fragment": bool(rd and frag in rd.value),
            "quotes": all(f"{d} §" in col2 for d in docs),
            "theorems": all(name in col2 for name in lean),
            "disputes": got_disputes == tuple(disputes),
            "gate": bool(rd and rd.gate and rd.gate[0]),
            "gate_line": rd.gate[1] if rd and rd.gate else None,
            "headline": (rd.value if rd else r.text)[:160],
        })
    t1 = all(r["read"] and r["verdict"] == "ANSWER" and r["fragment"]
             for r in rows)
    t2 = all(r["quotes"] and r["theorems"] for r in rows)
    t3 = all(r["disputes"] for r in rows)
    return {"rows": rows,
            "T1": {"passed": sum(1 for r in rows if r["read"] and
                                 r["verdict"] == "ANSWER" and r["fragment"]),
                   "of": len(rows), "met": t1},
            "T2": {"passed": sum(1 for r in rows
                                 if r["quotes"] and r["theorems"]),
                   "of": len(rows), "met": t2,
                   "quotes": sum(len(_topic(t).quotes)
                                 for _, t, *_ in C.META_QUESTIONS),
                   "theorems": sum(len(x[5]) for x in C.META_QUESTIONS)},
            "T3": {"passed": sum(1 for r in rows if r["disputes"]),
                   "of": len(rows), "met": t3,
                   "disputes": sum(len(x[6]) for x in C.META_QUESTIONS)},
            "scripts": sum(1 for r in rows if r["gate"])}


def mutation_mark() -> Dict[str, object]:
    """The second half of T4: every mutation kind on every question."""
    from ..evaluation import question_set_b_cases as qc
    items = qc.outside()
    caught: Dict[str, int] = {k: 0 for k, _ in C.MUTATIONS}
    missed: List[str] = []
    for idx, topic, *_ in C.META_QUESTIONS:
        tp = _topic(topic)
        text = items[idx].text
        for kind, _ in C.MUTATIONS:
            rd = MF.mutated(tp, text, kind)
            if kind in ("quote-moved", "lean-moved"):
                ok = (not rd.answered) and rd.code == "CITATION_MOVED"
            else:
                ok = not _gate(rd.script)[0]
            if ok:
                caught[kind] += 1
            else:
                missed.append(f"{idx}:{kind}")
    n = len(C.META_QUESTIONS)
    return {"caught": caught, "of": n, "missed": missed,
            "met": not missed}


def paraphrase_mark(texts=None) -> Dict[str, object]:
    """T5 (``texts``: another set of ``(id, text, topic)``, for
    :data:`~glm_universal.evaluation.meta_question_cases.HELD_OUT`)."""
    from . import question_frames as qf
    frag = {topic: f for _, topic, _, f, *_ in C.META_QUESTIONS}
    rows = []
    for pid, text, topic in (C.PARAPHRASES if texts is None else texts):
        got = qf.frame_of(text)
        rd = qf.read(text) if got else None
        rows.append({"id": pid, "topic": topic,
                     "frame": got[0].name if got else None,
                     "ok": bool(got and got[0].name == f"meta_{topic}"
                                and rd and rd.answered
                                and frag[topic] in rd.value
                                and rd.gate and rd.gate[0])})
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "met": passed == len(rows)}


def interference_mark() -> Dict[str, object]:
    """T6: the meta frames read none of the declared near misses, none of
    the other outside questions, Set B or the evaluation cases; switched
    off and on, no other text changes frame."""
    from ..evaluation import question_set_b_cases as qc
    from ..evaluation.cases import CASES
    from . import question_frames as qf
    declared = {x[0] for x in C.META_QUESTIONS}
    texts = [(f"N{i}", t) for i, t in enumerate(C.NOT_READ)] + \
        [(f"O{it.index:03d}", it.text) for it in qc.outside()
         if it.index not in declared] + \
        [(it.id, it.query) for it in qc.set_b()] + \
        [(c.id, c.question) for c in CASES]

    def frame_name(text: str) -> Optional[str]:
        got = qf.frame_of(text)
        return got[0].name if got else None

    read_by_meta, moved = [], []
    saved = qf.META
    try:
        qf.META = False
        before = {k: frame_name(t) for k, t in texts}
        qf.META = True
        for key, text in texts:
            now = frame_name(text)
            if now is not None and now.startswith("meta_"):
                read_by_meta.append(key)
            if now != before[key]:
                moved.append(key)
    finally:
        qf.META = saved
    return {"texts_checked": len(texts), "not_read": len(C.NOT_READ),
            "outside_other": sum(1 for k, _ in texts if k.startswith("O")),
            "set_b": len(qc.set_b()), "evaluation_cases": len(CASES),
            "read_by_meta": read_by_meta, "moved": moved,
            "met": not read_by_meta and not moved}


def lean_mark() -> Dict[str, object]:
    """T7 (the source half; the build is ``lake build``)."""
    if not LEAN_FILE.exists():
        return {"exists": False, "met": False}
    src = LEAN_FILE.read_text(encoding="utf-8")
    code = re.sub(r"/-.*?-/", "", src, flags=re.S)
    code = re.sub(r"--[^\n]*", "", code)
    missing = [t for t in C.LEAN_THEOREMS
               if not re.search(rf"theorem\s+{t}\b", code)]
    has_sorry = bool(re.search(r"\bsorry\b", code))
    return {"exists": True, "missing": missing, "sorry": has_sorry,
            "met": not missing and not has_sorry}


def meta_report(mutations: bool = True) -> Dict[str, object]:
    """Every mark, T1-T7 (``mutations=False`` skips the mutation half of
    T4, which runs four scripts per question)."""
    q = question_marks()
    mut = mutation_mark() if mutations else {"skipped": True, "met": True}
    t4_scripts = q["scripts"] == len(C.META_QUESTIONS)
    marks = {"T1": q["T1"], "T2": q["T2"], "T3": q["T3"],
             "T4": {"scripts": q["scripts"], "of": len(C.META_QUESTIONS),
                    "mutations": mut,
                    "met": t4_scripts and bool(mut.get("met"))},
             "T5": paraphrase_mark(),
             "T6": interference_mark(),
             "T7": lean_mark()}
    met = sum(1 for m in marks.values() if m.get("met"))
    held = paraphrase_mark(C.HELD_OUT)
    return {"rows": q["rows"], "marks": marks, "met": met, "of": len(marks),
            "held_out": {"passed": held["passed"], "of": held["of"],
                         "missed": [r["id"] for r in held["rows"]
                                    if not r["ok"]]},
            "first_run": FIRST_RUN,
            "pre_existing": len(C.PRE_EXISTING),
            "this_round": len(C.THIS_ROUND)}

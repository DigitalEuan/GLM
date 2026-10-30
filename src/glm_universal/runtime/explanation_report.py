"""``glm_universal.runtime.explanation_report`` -- the marks of Phase 120.

The measurement of ``studies/EXPLANATION_ANCHOR_STUDY.md`` against the marks
E1-E10 of :mod:`glm_universal.evaluation.explanation_cases`: the 35 outside
questions read through the router, their register anchors, the accounts
refused, the column-3 scripts and the controls, the disputed premises, the
paraphrases, non-interference, the nuclide register's read-back, the Lean
file and the three questions Phase 107 left refused.  Nothing here uses a
float.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional

from ..evaluation import explanation_cases as C
from . import explanation_frames as XF
from ..reasoning import explanation_anchors as EA

__all__ = ["question_marks", "mutation_mark", "paraphrase_mark",
           "interference_mark", "held_out_mark", "register_mark", "lean_mark",
           "explanation_report", "LEAN_FILE", "REGISTER_MARKERS"]

LEAN_FILE = (Path(__file__).resolve().parent.parent.parent / "lean" /
             "RequestProject" / "GLM" / "ExplanationAnchors.lean")

#: What column 2 and the backing must name for each declared register.
REGISTER_MARKERS: Dict[str, tuple] = {
    "elements": ("element",),
    "nuclides": ("AME2020", "NUBASE2020"),
    "proof_search": ("proof_search",),
    "integer_decision": ("integer_decision",),
    "none": ("no register row",),
}


def _topic(key: str) -> EA.Topic:
    return next(tp for tp in EA.TOPICS if tp.key == key)


def _gate(script: str):
    from .question_frames import run_gate
    return run_gate(script)


def question_marks() -> Dict[str, object]:
    """E1, E2, E3, E5 and the first half of E4: every declared question
    through the router."""
    from ..evaluation import question_set_b_cases as qc
    from . import router
    from .session import GeometricSession
    session = GeometricSession()
    items = {it.index: it for it in qc.outside()}
    rows: List[Dict[str, object]] = []
    for idx, topic, scope, frag, regs, disputes in C.EXPLANATION_QUESTIONS:
        r = router.route(session, items[idx].text)
        rd = r.payload if r.surface == "frames" else None
        frame = getattr(rd, "frame", None)
        answered = bool(rd and rd.answered)
        value = rd.value if rd else ""
        where = (rd.column2 + " " + rd.backing) if rd else ""
        refused_part = "refused EXPLANATION" in value
        got = tuple(rd.disputes) if rd else ()
        rows.append({
            "index": idx, "topic": topic, "scope": scope,
            "surface": r.surface, "frame": frame,
            "read": frame == f"explain_{topic}",
            "answered": answered,
            "fragment": bool(rd and frag in value),
            "scope_ok": refused_part == (scope == "ANCHORED"),
            "registers_ok": all(any(m in where for m in REGISTER_MARKERS[g])
                                for g in regs),
            "disputes_ok": len(got) == len(disputes) and all(
                any(d in x for x in got) for d in disputes),
            "gate": bool(rd and rd.gate and rd.gate[0]),
            "gate_line": rd.gate[1] if rd and rd.gate else None,
            "headline": (value or r.text)[:160],
        })

    def count(key: str) -> int:
        return sum(1 for r in rows if r[key])
    e1 = [r for r in rows if r["read"] and r["answered"] and r["fragment"]]
    return {"rows": rows,
            "E1": {"passed": len(e1), "of": len(rows),
                   "met": len(e1) == len(rows)},
            "E2": {"passed": count("scope_ok"), "of": len(rows),
                   "full": sum(1 for r in rows if r["scope"] == "FULL"),
                   "met": count("scope_ok") == len(rows)},
            "E3": {"passed": count("registers_ok"), "of": len(rows),
                   "reading_a_register": sum(
                       1 for x in C.EXPLANATION_QUESTIONS
                       if x[4] != ("none",)),
                   "met": count("registers_ok") == len(rows)},
            "E5": {"passed": count("disputes_ok"), "of": len(rows),
                   "disputes": sum(len(x[5]) for x in
                                   C.EXPLANATION_QUESTIONS),
                   "met": count("disputes_ok") == len(rows)},
            "scripts": count("gate")}


def mutation_mark() -> Dict[str, object]:
    """The second half of E4: every control that applies, on every
    question."""
    caught: Dict[str, int] = {k: 0 for k, _ in C.MUTATIONS}
    applies: Dict[str, int] = {k: 0 for k, _ in C.MUTATIONS}
    missed: List[str] = []
    for idx, topic, *_ in C.EXPLANATION_QUESTIONS:
        tp = _topic(topic)
        for kind, _ in C.MUTATIONS:
            rd = XF.mutated(tp, kind)
            if rd is None:
                continue
            applies[kind] += 1
            if not _gate(rd.script)[0]:
                caught[kind] += 1
            else:
                missed.append(f"{idx}:{kind}")
    return {"caught": caught, "applies": applies, "missed": missed,
            "met": not missed}


def paraphrase_mark() -> Dict[str, object]:
    """E6: one rewording per question."""
    from . import question_frames as qf
    frag = {topic: f for _, topic, _, f, *_ in C.EXPLANATION_QUESTIONS}
    rows = []
    for pid, text, topic in C.PARAPHRASES:
        got = qf.frame_of(text)
        rd = qf.read(text) if got else None
        rows.append({"id": pid, "topic": topic,
                     "frame": got[0].name if got else None,
                     "ok": bool(got and got[0].name == f"explain_{topic}"
                                and rd and rd.answered
                                and frag[topic] in rd.value
                                and rd.gate and rd.gate[0])})
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "missed": [r["id"] for r in rows if not r["ok"]],
            "met": passed >= 32}


def held_out_mark() -> Dict[str, object]:
    """The held-out rewordings: written after the first run and before any
    cue change.  Reported as measured; not a mark."""
    from . import question_frames as qf
    frag = {topic: f for _, topic, _, f, *_ in C.EXPLANATION_QUESTIONS}
    rows = []
    for hid, text, topic in C.HELD_OUT:
        got = qf.frame_of(text)
        rd = qf.read(text) if got else None
        rows.append({"id": hid, "topic": topic,
                     "frame": got[0].name if got else None,
                     "ok": bool(got and got[0].name == f"explain_{topic}"
                                and rd and rd.answered
                                and frag[topic] in rd.value
                                and rd.gate and rd.gate[0])})
    passed = sum(1 for r in rows if r["ok"])
    return {"rows": rows, "passed": passed, "of": len(rows),
            "missed": [r["id"] for r in rows if not r["ok"]],
            "wrong_frame": [r["id"] for r in rows
                            if r["frame"] is not None and not
                            r["frame"] == f"explain_{r['topic']}"]}


def interference_mark() -> Dict[str, object]:
    """E7: the explanation frames read none of the declared near misses,
    none of the other outside questions, Set B or the evaluation cases;
    switched off and on, no other text changes frame."""
    from ..evaluation import question_set_b_cases as qc
    from ..evaluation.cases import CASES
    from . import question_frames as qf
    declared = {x[0] for x in C.EXPLANATION_QUESTIONS}
    texts = [(f"N{i}", t) for i, t in enumerate(C.NOT_READ)] + \
        [(f"O{it.index:03d}", it.text) for it in qc.outside()
         if it.index not in declared] + \
        [(it.id, it.query) for it in qc.set_b()] + \
        [(c.id, c.question) for c in CASES]

    def frame_name(text: str) -> Optional[str]:
        got = qf.frame_of(text)
        return got[0].name if got else None

    read_by_new, moved = [], []
    saved = qf.EXPLANATIONS
    try:
        qf.EXPLANATIONS = False
        before = {k: frame_name(t) for k, t in texts}
        qf.EXPLANATIONS = True
        for key, text in texts:
            now = frame_name(text)
            if now is not None and now.startswith("explain_"):
                read_by_new.append(key)
            if now != before[key]:
                moved.append(key)
    finally:
        qf.EXPLANATIONS = saved
    return {"texts_checked": len(texts), "not_read": len(C.NOT_READ),
            "outside_other": sum(1 for it in qc.outside()
                                 if it.index not in declared),
            "set_b": len(qc.set_b()), "evaluation_cases": len(CASES),
            "read_by_explanation": read_by_new, "moved": moved,
            "met": not read_by_new and not moved}


def _round_trip(text: str) -> bool:
    neg = text.startswith("-")
    body = text[1:] if neg else text
    d = len(body.split(".", 1)[1]) if "." in body else 0
    return EA.rnd(Fraction(text), d) == ("-" if neg and Fraction(text) != 0
                                         else "") + body


def register_mark() -> Dict[str, object]:
    """E8: the nuclide register's read-back checks."""
    from ..data_objects import nuclides as N
    reg = N.register()
    srcs = N.sources()
    digest_ok = len(srcs) == 2 and all(
        re.fullmatch(r"[0-9a-f]{64}", s.get("raw_sha256", "")) for s in srcs)
    texts = [v.mass_excess_text for v in reg.values() if v.mass_excess_text]
    bad = [t for t in texts if not _round_trip(t)]
    deut = EA.rnd(N.binding(1, 2), 3)
    measured = [(N.binding_per_nucleon(z, a), z, a) for (z, a), v
                in reg.items() if a > 1 and v.mass_excess_text
                and not v.estimated]
    peak = max(measured)
    stable = sum(1 for v in reg.values() if v.half_life == "stbl")
    checks = {
        "raw-digest": digest_ok,
        "round-trip": not bad,
        "deuteron": deut == "2224.566",
        "peak": (peak[1], peak[2]) == (28, 62),
        "stable-count": 250 <= stable <= 260,
    }
    return {"checks": checks, "ground_states": len(reg),
            "mass_excesses": len(texts),
            "measured": len(measured), "stable": stable,
            "peak": f"{peak[2]}{N.nuclide(peak[1], peak[2]).symbol}",
            "peak_keV": EA.rnd(peak[0], 3), "deuteron_keV": deut,
            "round_trip_failures": bad[:5],
            "met": all(checks.values())}


def lean_mark() -> Dict[str, object]:
    """E9 (the source half; the build is ``lake build``)."""
    if not LEAN_FILE.exists():
        return {"exists": False, "met": False}
    src = LEAN_FILE.read_text(encoding="utf-8")
    code = re.sub(r"/-.*?-/", "", src, flags=re.S)
    code = re.sub(r"--[^\n]*", "", code)
    missing = [t for t in C.LEAN_THEOREMS
               if not re.search(rf"theorem\s+{t}\b", code)]
    has_sorry = bool(re.search(r"\bsorry\b", code))
    return {"exists": True, "missing": missing, "sorry": has_sorry,
            "theorems": len(C.LEAN_THEOREMS),
            "met": not missing and not has_sorry}


def explanation_report(mutations: bool = True) -> Dict[str, object]:
    """Every mark, E1-E10 (``mutations=False`` skips the control half of
    E4)."""
    q = question_marks()
    mut = mutation_mark() if mutations else {"skipped": True, "met": True}
    inter = interference_mark()
    rows = q["rows"]
    prev = [r for r in rows if r["index"] in C.PREVIOUSLY_REFUSED]
    e10 = all(r["read"] and r["answered"] and r["gate"] for r in prev) \
        and not inter["moved"]
    marks = {"E1": q["E1"], "E2": q["E2"], "E3": q["E3"],
             "E4": {"scripts": q["scripts"], "of": len(rows),
                    "mutations": mut,
                    "met": q["scripts"] == len(rows)
                    and bool(mut.get("met"))},
             "E5": q["E5"],
             "E6": paraphrase_mark(),
             "E7": inter,
             "E8": register_mark(),
             "E9": lean_mark(),
             "E10": {"answered": [r["index"] for r in prev
                                  if r["answered"]],
                     "of": list(C.PREVIOUSLY_REFUSED),
                     "others_moved": inter["moved"], "met": e10}}
    met = sum(1 for m in marks.values() if m.get("met"))
    return {"rows": rows, "marks": marks, "met": met, "of": len(marks),
            "held_out": held_out_mark()}

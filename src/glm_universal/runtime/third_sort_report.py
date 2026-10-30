"""``glm_universal.runtime.third_sort_report`` -- the marks of Phase 94.

The measurement of round 7 of the order of work, the third sort
(``studies/THIRD_SORT_STUDY.md``), against the marks T1-T6 and D1-D4 declared
before any code at the head of
:mod:`glm_universal.evaluation.third_sort_cases`.  Kept in the runtime layer
because the column-3 scripts are run in fresh interpreters
(:func:`glm_universal.runtime.python_tct.run_column3`).
"""

from __future__ import annotations

from typing import Dict, List

from ..evaluation import python_speech_cases as pc
from ..evaluation import third_sort_cases as C
from ..reasoning import python_speech as sp
from ..reasoning import reverse_tct as rt
from ..reasoning import reverse_tct_script as rts
from ..reasoning import reverse_tct_seq as rs
from .python_tct import run_column3
from .tct_engine import package_root

__all__ = ["cpython_value", "say_marks", "dialect_inside", "battery",
           "no_regression", "dialect_marks", "third_sort_report"]


def cpython_value(src: str):
    """CPython's value of ``src`` under the dialect's prelude."""
    return sp._cpython_reference(src)[1]


def _agrees(mine, ref) -> bool:
    """The third sort's value (or truth) against CPython's."""
    if isinstance(ref, bool):
        return mine is ref
    try:
        want = rs.evaluate(rs.value_term(ref), {})
    except rt.ReverseRefusal:
        return False
    if type(want) is not type(mine):
        return False
    return rs._equal(mine, want)


def say_marks(run_scripts: bool = True) -> Dict[str, object]:
    """T1 (sentences and values), T2 (refusals), T3's first half (read back)
    and T4 (scripts and mutants)."""
    root = str(package_root())
    t1_wrong: List[str] = []
    read_back = 0
    verified = caught = mutants = 0
    failed: List[str] = []
    for cid, src, want in C.SAY_CASES:
        a = rt.say(src)
        ok = a.answered and a.sentence == want
        if ok:
            c = a.certificate
            ref = cpython_value(src)
            mine = c["truth"] if "truth" in c else rs.evaluate(
                rs._dec(c["value"]), {})
            ok = _agrees(mine, ref)
        if not ok:
            t1_wrong.append(cid)
        try:
            read_back += rs.read(want) == rs.from_source(src)
        except rt.ReverseRefusal:
            pass
        if run_scripts and a.answered:
            if run_column3(rts.render_script(a, root))["verified"]:
                verified += 1
            else:
                failed.append(cid)
            bad = rts.mutated_script(a, root)
            if bad is not None:
                mutants += 1
                caught += not run_column3(bad)["verified"]
    refusals = [(cid, rt.say(src).refusal, want)
                for cid, src, want in C.SAY_REFUSALS]
    unreadable = 0
    for _, s in C.READ_REFUSALS:
        try:
            rs.read(s)
        except rt.ReverseRefusal as exc:
            unreadable += exc.name == "UNREADABLE"
    n = len(C.SAY_CASES)
    return {
        "T1": {"cases": n, "right": n - len(t1_wrong), "wrong_ids": t1_wrong,
               "passed": not t1_wrong},
        "T2": {"refusals": len(refusals),
               "right": sum(g == w for _, g, w in refusals),
               "wrong_ids": [c for c, g, w in refusals if g != w],
               "unreadable": unreadable, "read_refusals": len(C.READ_REFUSALS),
               "passed": all(g == w for _, g, w in refusals)
               and unreadable == len(C.READ_REFUSALS)},
        "read_back": {"right": read_back, "of": n},
        "T4": {"ran": run_scripts, "scripts": verified + len(failed),
               "verified": verified, "failed": failed, "mutants": mutants,
               "caught": caught,
               "passed": (not run_scripts) or (verified == n and not failed
                                               and caught == mutants == n)},
    }


def battery() -> Dict[str, int]:
    """T3's second half: every battery term reads back, no two share a
    sentence."""
    terms = rs.battery_terms(C.SEQ_BATTERY_ATOMS)
    sentences = [rs.realise(t) for t in terms]
    back = sum(1 for t, s in zip(terms, sentences) if rs.read(s) == t)
    return {"terms": len(terms), "read_back": back,
            "distinct_sentences": len(set(sentences))}


def dialect_inside() -> Dict[str, object]:
    """T5: the Phase 64 programs on strings, tuples and ranges."""
    cases = dict(pc.VALUE_CASES)
    rows = []
    for cid in C.DIALECT_INSIDE + tuple(c for c, _ in C.DIALECT_OUTSIDE):
        src = cases[cid]
        try:
            obj = rs.from_source(src)
        except rt.ReverseRefusal as exc:
            rows.append({"id": cid, "inside": False, "refusal": exc.name})
            continue
        back = rs.read(rs.realise(obj))
        ref = cpython_value(src)
        p = sp.speak(src)
        ns = sp._cpython_reference(src)[0]
        try:
            mine = rs.value_of(back)
            ok = (back == obj and _agrees(mine, ref) and p.answered
                  and ns["same"](eval(p.value_literal, ns), ref))
        except rt.ReverseRefusal:
            ok = False
        rows.append({"id": cid, "inside": True, "agrees": ok})
    inside = [r["id"] for r in rows if r["inside"]]
    agree = [r["id"] for r in rows if r.get("agrees")]
    return {"declared": len(C.DIALECT_INSIDE), "inside": len(inside),
            "agree": len(agree), "rows": rows,
            "outside": [r["id"] for r in rows if not r["inside"]],
            "passed": set(agree) == set(C.DIALECT_INSIDE)
            and not (set(inside) - set(C.DIALECT_INSIDE))}


def no_regression() -> Dict[str, object]:
    """T6: every earlier declared ``say:`` case and refusal as declared."""
    from ..evaluation import reverse_tct_cases as C1
    from ..evaluation import reverse_tct_two_cases as C2
    sup = {(k, cid): want for k, cid, want in C2.SUPERSEDED}
    rows = []
    for cid, src, want in C1.SAY_CASES:
        rows.append((f"67:{cid}", rt.say(src).sentence, want))
    for cid, src, want in C1.SAY_REFUSALS:
        a = rt.say(src)
        rows.append((f"67-refusal:{cid}", a.sentence if a.answered
                     else a.refusal, sup.get(("SAY_REFUSALS", cid), want)))
    for cid, src, want in C2.SAY_CASES:
        rows.append((f"68:{cid}", rt.say(src).sentence, want))
    for cid, src, want in C2.SAY_REFUSALS:
        rows.append((f"68-refusal:{cid}", rt.say(src).refusal, want))
    # Later rounds that moved an earlier declared case on the record: Phase 95
    # (IMPERATIVE_GRAMMAR_STUDY.md, mark I7, not met) reads ``a, b = b, 1``
    # and names the real fault, so its refusal is now UNBOUND.  Reported,
    # not hidden: it is listed under ``moved_later``.
    later = {"68-refusal:unpack-self": "UNBOUND"}
    moved_later = [cid for cid, got, want in rows
                   if cid in later and got != want and got == later[cid]]
    moved = [cid for cid, got, want in rows
             if got != want and cid not in moved_later]
    inside = 0
    for _, src in pc.VALUE_CASES:
        try:
            obj = rt.from_source(src)
        except rt.ReverseRefusal:
            continue
        if not rt._variables(obj) or obj[0] == "prog":
            inside += 1
    return {"cases": len(rows), "moved": moved, "moved_later": moved_later,
            "w2_inside": inside, "passed": not moved}


def dialect_marks(run_scripts: bool = True) -> Dict[str, object]:
    """D1-D4: the widened dialect against CPython."""
    groups = (("string", C.STRING_METHOD_CASES), ("list", C.LIST_CASES),
              ("dict", C.DICT_CASES))
    d1 = {}
    wrong: List[str] = []
    refused: List[str] = []
    verified = caught = 0
    failed: List[str] = []
    total = 0
    for name, cases in groups:
        right = 0
        for cid, src in cases:
            total += 1
            p = sp.speak(src)
            ns, ref = sp._cpython_reference(src)
            if not p.answered:
                refused.append(f"{name}:{cid}")
                continue
            if ns["same"](eval(p.value_literal, ns), ref):
                right += 1
            else:
                wrong.append(f"{name}:{cid}")
                continue
            if run_scripts:
                if sp.verify_payload(p)["verified"]:
                    verified += 1
                else:
                    failed.append(f"{name}:{cid}")
                caught += not sp.verify_payload(
                    p, sp.mutated_script(p))["verified"]
        d1[name] = {"cases": len(cases), "right": right}
    refusals = [(cid, sp.speak(src), want)
                for cid, src, want in C.DIALECT_REFUSALS]
    d2_wrong = [cid for cid, p, want in refusals
                if p.answered or p.refusal != want]
    superseded = []
    for cid, src, _old in C.SUPERSEDED_REFUSALS:
        p = sp.speak(src)
        ns, ref = sp._cpython_reference(src)
        superseded.append(p.answered and ns["same"](eval(p.value_literal, ns),
                                                   ref))
    kept = [cid for cid, src, want in pc.REFUSAL_CASES
            if sp.speak(src).refusal != want]
    values_moved = []
    for cid, src in pc.VALUE_CASES:
        p = sp.speak(src)
        ns, ref = sp._cpython_reference(src)
        if not (p.answered and ns["same"](eval(p.value_literal, ns), ref)):
            values_moved.append(cid)
    bat = sp.differential_battery()
    right = sum(v["right"] for v in d1.values())
    return {
        "D1": dict(d1, total=total, right=right, wrong_ids=wrong,
                   refused_ids=refused, passed=right == total),
        "D2": {"refusals": len(refusals),
               "right": len(refusals) - len(d2_wrong), "wrong_ids": d2_wrong,
               "superseded_answered": sum(superseded),
               "superseded": len(superseded),
               "phase64_kept": len(pc.REFUSAL_CASES) - len(kept),
               "phase64_in_force": len(pc.REFUSAL_CASES),
               "phase64_moved": kept,
               "passed": not d2_wrong and all(superseded) and not kept},
        "D3": {"ran": run_scripts, "verified": verified, "failed": failed,
               "caught": caught,
               "passed": (not run_scripts) or (verified == right
                                               and caught == right)},
        "D4": {"values": len(pc.VALUE_CASES), "values_moved": values_moved,
               "battery_total": bat["total"],
               "battery_answered": bat["answered"],
               "battery_wrong": bat["wrong"],
               "passed": not values_moved and bat["wrong"] == 0},
    }


def third_sort_report(run_scripts: bool = True) -> Dict[str, object]:
    """Every mark of the study's §2."""
    say = say_marks(run_scripts)
    bat = battery()
    t3_ok = (say["read_back"]["right"] == say["read_back"]["of"]
             and bat["read_back"] == bat["terms"]
             and bat["distinct_sentences"] == bat["terms"])
    marks = {
        "T1": say["T1"], "T2": say["T2"],
        "T3": {"read_back": say["read_back"], "battery": bat,
               "passed": t3_ok},
        "T4": say["T4"], "T5": dialect_inside(), "T6": no_regression(),
    }
    marks.update(dialect_marks(run_scripts))
    return {"marks": marks,
            "met": sorted(k for k, v in marks.items() if v["passed"]),
            "not_met": sorted(k for k, v in marks.items()
                              if not v["passed"])}

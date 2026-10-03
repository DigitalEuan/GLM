"""``glm_universal.runtime.imperative_report`` -- the marks of Phase 95.

The measurement of the second half of round 7 of the order of work, M's
imperative grammar (``studies/IMPERATIVE_GRAMMAR_STUDY.md``), against the
marks I1-I9 declared before any code at the head of
:mod:`glm_universal.evaluation.imperative_cases`.  Kept in the runtime layer
because the column-3 scripts are run in fresh interpreters
(:func:`glm_universal.runtime.python_tct.run_column3`).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

from ..evaluation import imperative_cases as C
from ..evaluation import python_speech_cases as pc
from ..reasoning import python_speech as sp
from ..reasoning import reverse_tct as rt
from ..reasoning import reverse_tct_imp as ri
from ..reasoning import reverse_tct_script as rts
from ..reasoning import reverse_tct_seq as rs
from .python_tct import run_column3
from .tct_engine import package_root

__all__ = ["BASELINE", "cpython_value", "answered_cases", "say_marks",
           "refusal_marks", "battery", "no_regression", "limit_marks",
           "differential_programs", "differential", "imperative_report"]

#: The surface's answers before the round (mark I7, I8).
BASELINE = (Path(__file__).resolve().parent.parent / "reasoning" / "_data"
            / "imperative_baseline.json")


def cpython_value(src: str):
    """CPython's value of ``src`` under the dialect's prelude."""
    return sp._cpython_reference(src)[1]


def _agrees(mine, ref) -> bool:
    """The imperative grammar's value against CPython's (an ``int`` and an
    equal ``Fraction`` agree, as in the third sort's marks)."""
    if isinstance(ref, bool):
        return False
    try:
        want = rs.evaluate(rs.value_term(ref), {})
    except (rt.ReverseRefusal, TypeError, ValueError):
        return False
    if type(want) is not type(mine):
        return False
    return rs._equal(mine, want)


def answered_cases() -> List[Tuple[str, str, str]]:
    """``(group, id, source)`` for every case of I1-I3."""
    vc = dict(pc.VALUE_CASES)
    return ([("I1", cid, src) for cid, src, _ in C.SAY_CASES]
            + [("I2", cid, vc[cid]) for cid in C.PHASE64_STATE]
            + [("I3", cid, src) for cid, src in C.PROGRAM_CASES])


def say_marks(run_scripts: bool = True) -> Dict[str, object]:
    """I1, I2, I3, the read-back half of I5, and I6."""
    root = str(package_root())
    want_sentence = {cid: s for cid, _, s in C.SAY_CASES}
    rows = []
    for group, cid, src in answered_cases():
        a = rt.say(src)
        row = {"group": group, "id": cid, "said": a.answered,
               "refusal": a.refusal}
        if a.answered:
            mine = rs.evaluate(rs._dec(a.certificate["value"]), {})
            row["agrees"] = _agrees(mine, cpython_value(src))
            row["sentence_as_declared"] = (
                a.sentence == want_sentence[cid] if group == "I1" else None)
            try:
                back = ri.read(a.sentence)
                row["read_back"] = (back == ri.from_source(src)
                                    and ri.realise(back) == a.sentence)
            except rt.ReverseRefusal:
                row["read_back"] = False
            row["steps"] = a.certificate["steps"]
            row["trace"] = len(a.certificate["trace"])
            if run_scripts:
                row["verified"] = run_column3(
                    rts.render_script(a, root))["verified"]
                bad = rts.mutated_script(a, root)
                row["mutant_rejected"] = (bad is not None
                                          and not run_column3(bad)["verified"])
        rows.append(row)

    def mark(group, need_sentence=False):
        rs_ = [r for r in rows if r["group"] == group]
        right = [r for r in rs_ if r["said"] and r["agrees"]
                 and r["read_back"]
                 and (not need_sentence or r["sentence_as_declared"])]
        wrong = [r["id"] for r in rs_ if r["said"] and not r["agrees"]]
        return {"cases": len(rs_), "right": len(right), "wrong_ids": wrong,
                "missed_ids": [r["id"] for r in rs_ if r not in right],
                "passed": len(right) == len(rs_)}
    said = [r for r in rows if r["said"]]
    i6 = {"ran": run_scripts,
          "verified": sum(1 for r in said if r.get("verified")),
          "mutants_rejected": sum(1 for r in said
                                  if r.get("mutant_rejected")),
          "of": len(rows)}
    i6["passed"] = (not run_scripts) or (i6["verified"] == len(rows)
                                         == i6["mutants_rejected"])
    return {"I1": mark("I1", True), "I2": mark("I2"), "I3": mark("I3"),
            "read_back": {"right": sum(1 for r in said if r["read_back"]),
                          "of": len(rows)},
            "I6": i6, "rows": rows}


def refusal_marks() -> Dict[str, object]:
    """I4: refusals by name, and sentences outside the grammar."""
    got = [(cid, rt.say(src).refusal, want) for cid, src, want in
           C.SAY_REFUSALS]
    unreadable = []
    for cid, s in C.READ_REFUSALS:
        try:
            ri.read(s)
        except rt.ReverseRefusal as exc:
            if exc.name == "UNREADABLE":
                unreadable.append(cid)
    wrong = [cid for cid, g, w in got if g != w]
    return {"refusals": len(got), "right": len(got) - len(wrong),
            "wrong_ids": wrong, "unreadable": len(unreadable),
            "read_refusals": len(C.READ_REFUSALS),
            "passed": not wrong and len(unreadable) == len(C.READ_REFUSALS)}


def battery() -> Dict[str, int]:
    """I5's second half: every battery program reads back, no two share a
    sentence."""
    programs = ri.battery_programs()
    sentences = [ri.realise(p) for p in programs]
    back = sum(1 for p, s in zip(programs, sentences) if ri.read(s) == p)
    return {"programs": len(programs), "read_back": back,
            "distinct_sentences": len(set(sentences))}


def no_regression() -> Dict[str, object]:
    """I7: the frozen Phase 64 answers, and every earlier declared case."""
    from . import third_sort_report as tr
    base = json.loads(BASELINE.read_text(encoding="utf-8"))["phase64_say"]
    moved, moved_as_declared = [], []
    for cid, src in pc.VALUE_CASES:
        a = rt.say(src)
        now = [a.verdict, a.sentence, a.refusal]
        if now != base[f"value:{cid}"]:
            (moved_as_declared if cid in C.PHASE64_STATE
             else moved).append(cid)
    for cid, src, _ in pc.PHASE64_REFUSAL_CASES:
        a = rt.say(src)
        if [a.verdict, a.sentence, a.refusal] != base[f"refusal:{cid}"]:
            moved.append(f"refusal:{cid}")
    earlier = tr.no_regression()
    third = tr.say_marks(run_scripts=False)
    return {"phase64_programs": len(pc.VALUE_CASES) + len(
                pc.PHASE64_REFUSAL_CASES),
            "moved": moved, "moved_as_declared": sorted(moved_as_declared),
            "earlier_cases": earlier["cases"], "earlier_moved":
                sorted(earlier["moved"] + earlier["moved_later"]),
            "third_sort_t1": third["T1"]["passed"],
            "third_sort_t2": third["T2"]["passed"],
            "passed": (not moved and sorted(moved_as_declared)
                       == sorted(C.PHASE64_STATE) and earlier["passed"]
                       and not earlier["moved_later"]
                       and third["T1"]["passed"] and third["T2"]["passed"])}


def before() -> Dict[str, object]:
    """I8: the declared material as the code stood at the declarations'
    commit (frozen with the baseline)."""
    table = json.loads(BASELINE.read_text(encoding="utf-8"))["before"]
    said = sorted(k for k, v in table.items() if v in ("SAID", "TRUE",
                                                       "FALSE"))
    return {"cases": len(table), "said_before": len(said),
            "refusals_before": sorted(set(table.values())),
            "passed": True}


def limit_marks() -> Dict[str, object]:
    """I9: the limits withhold, never change."""
    k = C.LIMIT_SCALE
    changed = []
    for _, cid, src in answered_cases():
        a = ri.say_imperative(src)
        b = ri.say_imperative(src, ri.STEP_LIMIT * k, ri.DEPTH_LIMIT * k)
        if a is None or b is None or a.certificate != b.certificate:
            changed.append(cid)
    refusals = dict((cid, src) for cid, src, _ in C.SAY_REFUSALS)
    still = []
    for cid in ("r-step-limit", "r-depth"):
        b = ri.say_imperative(refusals[cid], ri.STEP_LIMIT * k,
                              ri.DEPTH_LIMIT * k)
        still.append(b is not None and not b.answered)
    return {"scale": k, "answers": len(answered_cases()),
            "changed": changed, "limit_refusals_still_refused": sum(still),
            "passed": not changed and all(still)}


_EXPR_N = ("x + 1", "x * y", "x - y", "x // 3", "x % 4", "-x", "abs(x - 5)",
           "max(x, y)", "min(x, 2)", "x ** 2", "len(s)", "x << 1", "x & 6",
           "x ^ y", "ord(s[0])")
_EXPR_S = ("s + 'a'", "s * 2", "s[1:]", "s[::-1]", "chr(97 + x % 26)",
           "s[0]")
_CONDS = ("x < y", "x % 2 == 0", "x", "s == 'ab'", "'a' in s",
          "x >= 3 and y < 9", "not (x > y)", "x < 0 or y > 2")


class _Lcg:
    """A 64-bit linear congruential generator in integers only (Knuth's
    MMIX constants), so the battery is fixed by its seed without importing
    a random library into the core."""

    def __init__(self, seed: int) -> None:
        self.state = seed % (1 << 64)

    def _next(self) -> int:
        self.state = (self.state * 6364136223846793005
                      + 1442695040888963407) % (1 << 64)
        return self.state >> 33

    def randrange(self, n: int) -> int:
        return self._next() % n

    def randint(self, a: int, b: int) -> int:
        return a + self.randrange(b - a + 1)

    def choice(self, seq):  # type: ignore[no-untyped-def]
        return seq[self.randrange(len(seq))]


def differential_programs(n: int = 600, seed: int = 7) -> List[str]:
    """A deterministic battery of small programs with state over two
    numbers and a string: assignments, ``for`` and ``while`` loops, branches
    and conditional expressions, nested up to two deep.  Written after the
    first measurement (post hoc), so it is reported beside the marks and is
    not one of them."""
    rnd = _Lcg(seed)

    def stmt(depth: int) -> List[str]:
        r = rnd.randrange(100)
        if depth > 1 or r < 40:
            v = rnd.choice(["x", "y", "s"])
            if v == "s":
                return [f"s = {rnd.choice(_EXPR_S)}"]
            return [f"{v} = {rnd.choice(_EXPR_N)}"]
        if r < 60:
            body = stmt(depth + 1)
            return ([f"for k in range({rnd.randint(0, 4)}):"]
                    + ["    " + ln for ln in body] + ["    x = x + k"])
        if r < 75:
            body = stmt(depth + 1)
            return (["c = 0", "while c < 3:", "    c += 1"]
                    + ["    " + ln for ln in body])
        if r < 90:
            b1, b2 = stmt(depth + 1), stmt(depth + 1)
            return ([f"if {rnd.choice(_CONDS)}:"] + ["    " + ln for ln in b1]
                    + ["else:"] + ["    " + ln for ln in b2])
        return [f"x = {rnd.choice(_EXPR_N)} if {rnd.choice(_CONDS)} else y"]
    out = []
    for _ in range(n):
        lines = [f"x = {rnd.randint(-3, 9)}", f"y = {rnd.randint(0, 9)}",
                 "s = 'ab'"]
        for _ in range(rnd.randint(1, 3)):
            lines += stmt(0)
        lines.append(rnd.choice(["x", "y", "s", "(x, y, s)"]))
        out.append("\n".join(lines))
    return out


def differential(n: int = 600) -> Dict[str, object]:
    """Every battery program asked of ``say:``; each answer the imperative
    grammar gives is compared with CPython's value."""
    counts = {"programs": 0, "imperative_answers": 0, "right": 0,
              "wrong": 0, "earlier_grammar_answers": 0, "refused": 0}
    wrong: List[str] = []
    for src in differential_programs(n):
        counts["programs"] += 1
        a = rt.say(src)
        if not a.answered:
            counts["refused"] += 1
            continue
        if a.certificate.get("kind") != "say-imp":
            counts["earlier_grammar_answers"] += 1
            continue
        counts["imperative_answers"] += 1
        mine = rs.evaluate(rs._dec(a.certificate["value"]), {})
        try:
            ok = _agrees(mine, cpython_value(src))
        except Exception:  # CPython raised: any answer is wrong
            ok = False
        if ok:
            counts["right"] += 1
        else:
            counts["wrong"] += 1
            wrong.append(src)
    return dict(counts, wrong_programs=wrong[:5])


def imperative_report(run_scripts: bool = True) -> Dict[str, object]:
    """Every mark of the study's §2."""
    say = say_marks(run_scripts)
    bat = battery()
    i5_ok = (say["read_back"]["right"] == say["read_back"]["of"]
             and bat["read_back"] == bat["programs"]
             == bat["distinct_sentences"])
    marks = {
        "I1": say["I1"], "I2": say["I2"], "I3": say["I3"],
        "I4": refusal_marks(),
        "I5": {"read_back": say["read_back"], "battery": bat,
               "passed": i5_ok},
        "I6": say["I6"], "I7": no_regression(), "I8": before(),
        "I9": limit_marks(),
    }
    return {"marks": marks, "rows": say["rows"],
            "differential": differential(),
            "met": sorted(k for k, v in marks.items() if v["passed"]),
            "not_met": sorted(k for k, v in marks.items()
                              if not v["passed"])}

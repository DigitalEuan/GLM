"""``glm_universal.runtime.stepwise_four`` -- the measurement of round four
of the stepwise planner: folds with a hole.

``studies/HOLE_FOLDS_STUDY.md`` (Phase 85) declares eight marks over the
corpus of :mod:`glm_universal.evaluation.stepwise_four_cases`; this module
takes the seven that are measured (the eighth is the Lean file,
``RequestProject/GLM/HoleBounds.lean``).  The frames themselves live where
they run: :mod:`glm_universal.runtime.stepwise` (``_fold4_readings``,
``_build_fold4``) and :mod:`glm_universal.reasoning.stepwise_script`
(``fold_value``, the templates, and the column-3 script's own
``order_fold``).

One control and one census:

* **Round three's reader** -- the same modules with
  :data:`glm_universal.runtime.stepwise.ROUND_FOUR` switched off: what the
  corpus met before this round (marks H1-H4).
* **Completions** -- every bounded answer checked against completions of its
  holes, the two extreme ones among them, and every order refusal of the
  corpus shown to move by at least a million between its two extreme
  completions (mark H5).  The fills come from a fixed linear congruential
  sequence, so the census is the same on every run.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import router
from . import stepwise as sw
from . import stepwise_three as st3
from ..reasoning import stepwise_script as ss

__all__ = ["round_three_reader", "orders_report", "bounded_report",
           "ranks_report", "present_report", "follow_ups_report",
           "completed_value", "completions_report", "answered_chains",
           "scripts_report", "interference_report", "stepwise_four_report"]

#: How far outside the present readings the extreme completions of H5 put
#: the holes of an order refusal.
FAR = Fraction(10 ** 6)


class round_three_reader:
    """The stepwise planner as round three left it: round four switched off.

    Used as ``with round_three_reader(): ...``; the flag is restored."""

    def __enter__(self):
        self._saved = sw.ROUND_FOUR
        sw.ROUND_FOUR = False
        return self

    def __exit__(self, *exc) -> bool:
        sw.ROUND_FOUR = self._saved
        return False


def _verdict(a) -> Tuple[str, ...]:
    return sw._verdict_of(a)


def _ok(got, want) -> bool:
    return tuple(got[:len(want)]) == tuple(want)


def _rows(session, cases) -> Dict[str, object]:
    rows = []
    for cid, q, want in cases:
        a = sw.answer(session, q)
        with round_three_reader():
            before = sw.answer(session, q)
            routed_before = router.route(session, q)
        routed = router.route(session, q)
        got = _verdict(a)
        rows.append({"id": cid, "want": list(want), "got": list(got),
                     "ok": _ok(got, want),
                     "round_three": list(_verdict(before)),
                     "machine_before": routed_before.text if
                     routed_before.answered else None,
                     "machine_now": routed.text if routed.answered else None,
                     "machine_by": getattr(routed.solution, "kind", None)
                     if routed.answered else None})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "wrong": sum(1 for r in rows
                         if r["got"][0] == "ANSWER" and not r["ok"]),
            "answered": sum(1 for r in rows if r["got"][0] == "ANSWER"),
            "round_three_answers": sum(1 for r in rows
                                       if r["round_three"][0] == "ANSWER"),
            "machine_answered_before": sum(1 for r in rows
                                           if r["machine_before"] is not None),
            "machine_answers_now": sum(1 for r in rows
                                       if r["machine_now"] is not None),
            "rows": rows}


def orders_report(session) -> Dict[str, object]:
    """Mark H1: the order folds."""
    from ..evaluation.stepwise_four_cases import ORDER_CASES
    return _rows(session, ORDER_CASES)


def bounded_report(session) -> Dict[str, object]:
    """Mark H2: the median over a column with holes."""
    from ..evaluation.stepwise_four_cases import BOUNDED_CASES
    return _rows(session, BOUNDED_CASES)


def ranks_report(session) -> Dict[str, object]:
    """Mark H3: the rank of a row."""
    from ..evaluation.stepwise_four_cases import RANK_CASES
    return _rows(session, RANK_CASES)


def _fold_step(chain):
    return next((s for s in reversed(chain.steps) if s.op == "fold"), None)


def _register_holes(session, detail) -> List[str]:
    from . import declared_frames as df
    fs = session.field_surface
    table = fs.table_by_name(df.ELEMENT_TABLE).rows()
    return [k for k, _n in df.members(fs, detail["set"])
            if table[k].get(detail["field"]) is None]


def present_report(session) -> Dict[str, object]:
    """Mark H4: the present-rows question, with the missing rows named."""
    from ..evaluation.stepwise_four_cases import PRESENT_CASES
    out = _rows(session, PRESENT_CASES)
    named = []
    for cid, q, _want in PRESENT_CASES:
        a = sw.answer(session, q)
        if not a.answered:
            continue
        step = _fold_step(a.chain)
        holes = _register_holes(session, step.detail)
        line = ss.sentence(step)
        ok = (step.detail.get("present") is True
              and list(step.detail["missing"]) == holes
              and all(k in line for k in holes))
        named.append({"id": cid, "missing": holes, "ok": ok})
    out["named"] = named
    out["named_ok"] = sum(r["ok"] for r in named)
    return out


def follow_ups_report(session) -> Dict[str, object]:
    from ..evaluation.stepwise_four_cases import FOLLOW_UP_CASES
    rows = []
    for cid, first, second, want in FOLLOW_UP_CASES:
        conv = sw.StepwiseConversation(session)
        conv.ask(first)
        a = conv.ask(second)
        got = _verdict(a)
        rows.append({"id": cid, "want": list(want), "got": list(got),
                     "ok": _ok(got, want)})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "rows": rows}


# ---------------------------------------------------------------------------
# the completions (mark H5)
# ---------------------------------------------------------------------------

def completed_value(fn: str, column: Sequence[Fraction],
                    x: Optional[Fraction] = None) -> Fraction:
    """The fold of a complete column, computed directly: the median (the
    mean of the two middle values for an even count), the ends, or the rank
    of ``x``, largest first."""
    p = sorted(column)
    if fn == "max":
        return p[-1]
    if fn == "min":
        return p[0]
    if fn == "rank":
        return Fraction(1 + sum(1 for v in p if v > x))
    n = len(p)
    if n % 2:
        return p[n // 2]
    return (p[n // 2 - 1] + p[n // 2]) / 2


def _fills(seed: int):
    """A fixed linear congruential sequence (Numerical Recipes constants)."""
    state = seed & 0xFFFFFFFF
    while True:
        state = (1664525 * state + 1013904223) & 0xFFFFFFFF
        yield state


def _interval(value) -> Tuple[Fraction, Fraction]:
    if isinstance(value, Fraction):
        return value, value
    lo, hi = str(value)[len("between "):].split(" and ")
    return ss.parse_value(lo), ss.parse_value(hi)


def _fold_inputs(session, detail):
    """The present readings of a fold's column, the number of holes, and
    the ranked row's reading."""
    from . import declared_frames as df
    fs = session.field_surface
    table = fs.table_by_name(df.ELEMENT_TABLE).rows()
    vals, holes, x = [], 0, None
    for k, _n in df.members(fs, detail["set"]):
        v = table[k].get(detail["field"])
        if v is None:
            holes += 1
            continue
        vals.append(Fraction(v))
        if k == detail.get("row"):
            x = Fraction(v)
    return vals, holes, x


def completions_report(session, per_answer: Optional[int] = None
                       ) -> Dict[str, object]:
    """Mark H5: every bounded answer against completions of its holes, and
    every order refusal of the corpus against its two extreme completions."""
    from ..evaluation import stepwise_four_cases as C
    per_answer = per_answer or C.COMPLETIONS_PER_ANSWER
    bounded, refusals = [], []
    for cid, q, want in C.ORDER_CASES + C.BOUNDED_CASES + C.RANK_CASES:
        a = sw.answer(session, q)
        if a.answered:
            step = _fold_step(a.chain)
            if step is None or not step.detail.get("bounded"):
                continue
            vals, holes, x = _fold_inputs(session, step.detail)
            lo, hi = _interval(step.value)
            fn = step.detail["fn"]
            least, most = min(vals), max(vals)
            span = most - least + 1
            gen = _fills(sum(map(ord, cid)))
            seen, inside = set(), 0
            low_fill = completed_value(fn, vals + [least - span] * holes, x)
            high_fill = completed_value(fn, vals + [most + span] * holes, x)
            columns = [vals + [least - span] * holes,
                       vals + [most + span] * holes]
            while len(columns) < per_answer:
                fill = [least - span + Fraction(next(gen) % 10 ** 6, 10 ** 6)
                        * 3 * span for _ in range(holes)]
                columns.append(vals + fill)
            for col in columns:
                got = completed_value(fn, col, x)
                seen.add(got)
                inside += lo <= got <= hi
            bounded.append({"id": cid, "fn": fn, "holes": holes,
                            "interval": [ss.render_value(lo),
                                         ss.render_value(hi)],
                            "completions": len(columns), "inside": inside,
                            "low_attained": low_fill == lo,
                            "high_attained": high_fill == hi,
                            "distinct_values": len(seen),
                            "ok": inside == len(columns) and low_fill == lo
                            and high_fill == hi})
        elif a.refusal == "COLUMN_HOLE":
            tree = next(t for seg in sw.split_then(q)
                        for t in sw.segment_readings(seg)
                        if isinstance(t, tuple))
            fold = _find_fold4(tree)
            if fold is None:
                continue
            from . import declared_frames as df
            detail = {"set": fold[2],
                      "field": df.resolve_field(session.field_surface,
                                                fold[3])}
            vals, holes, x = _fold_inputs(session, detail)
            fn = fold[1]
            low = completed_value(fn, vals + [min(vals) - FAR] * holes, x)
            high = completed_value(fn, vals + [max(vals) + FAR] * holes, x)
            refusals.append({"id": cid, "fn": fn, "holes": holes,
                             "low": ss.render_value(low),
                             "high": ss.render_value(high),
                             "moved": ss.render_value(high - low),
                             "ok": high - low >= FAR})
    return {"bounded": bounded, "refusals": refusals,
            "per_answer": per_answer,
            "met": bool(bounded) and all(r["ok"] for r in bounded)
            and bool(refusals) and all(r["ok"] for r in refusals)}


def _find_fold4(t):
    if not isinstance(t, tuple):
        return None
    if t and t[0] == "fold4":
        return t
    for x in t[1:]:
        got = _find_fold4(x)
        if got is not None:
            return got
    return None


# ---------------------------------------------------------------------------
# the scripts (mark H6)
# ---------------------------------------------------------------------------

def answered_chains(session) -> List[Tuple[str, object]]:
    """Every answered chain of the round-four corpus, with its case id."""
    from ..evaluation import stepwise_four_cases as C
    out = []
    for cid, q, _want in (C.ORDER_CASES + C.BOUNDED_CASES + C.RANK_CASES
                          + C.PRESENT_CASES):
        a = sw.answer(session, q)
        if a.answered:
            out.append((cid, a.chain))
    for cid, first, second, _ in C.FOLLOW_UP_CASES:
        conv = sw.StepwiseConversation(session)
        conv.ask(first)
        a = conv.ask(second)
        if a.answered:
            out.append((cid, a.chain))
    return out


def scripts_report(session, limit: Optional[int] = None) -> Dict[str, object]:
    """Every answered chain's column-3 script in a fresh ``python3 -I``, and
    every mutation of each."""
    import re
    from .python_tct import run_column3
    from .tct_engine import package_root
    root = str(package_root())
    chains = answered_chains(session)
    if limit is not None:
        chains = chains[:limit]
    verified, failed, aligned, steps = 0, [], 0, 0
    caught = {k: 0 for k in ss.MUTATION_KINDS}
    built = {k: 0 for k in ss.MUTATION_KINDS}
    escaped: List[str] = []
    for cid, chain in chains:
        got = run_column3(ss.render_script(chain, root))
        steps += len(chain.steps)
        m = re.search(r"ALIGNED (\d+) of (\d+)", got["stdout"])
        aligned += int(m.group(1)) if m else 0
        if got["verified"]:
            verified += 1
        else:
            failed.append(cid)
        for kind, data in ss.mutants(chain).items():
            built[kind] += 1
            bad = run_column3(ss.render_script(chain, root, data))
            if bad["verified"]:
                escaped.append(f"{cid}:{kind}")
            else:
                caught[kind] += 1
    return {"chains": len(chains), "verified": verified, "failed": failed,
            "steps": steps, "aligned": aligned, "mutants": built,
            "caught": caught, "escaped": escaped}


# ---------------------------------------------------------------------------
# non-interference (mark H7)
# ---------------------------------------------------------------------------

def interference_report(session) -> Dict[str, object]:
    """Round three's corpus through the round-four module (its marks V1-V5
    re-taken without scripts), and through it rounds one and two and the
    router's declared sets."""
    three = {
        "comparatives": st3.comparatives_report(session),
        "counts": st3.counts_report(session),
        "prefixes": st3.prefixes_report(session),
        "folds": st3.folds_report(session),
        "follow_ups": st3.follow_ups_report(session),
    }
    controls = st3.controls_report(session)
    below = st3.interference_report(session)
    held_three = all(v["met"] == v["cases"] for v in three.values()) and \
        controls["met"]
    return {"round_three": {k: {"cases": v["cases"], "met": v["met"]}
                            for k, v in three.items()},
            "round_three_controls_met": controls["met"],
            "round_three_held": held_three,
            "round_two_held": below["round_two_held"],
            "round_one_held": below["round_one_held"],
            "router_read": below["router_read"],
            "router_questions": below["router_questions"],
            "turned_into_answers": below["turned_into_answers"],
            "declared_refusals_answered": below["declared_refusals_answered"]}


def stepwise_four_report(scripts: bool = True) -> Dict[str, object]:
    """The whole measurement of ``studies/HOLE_FOLDS_STUDY.md``."""
    from .session import GeometricSession
    session = GeometricSession()
    report: Dict[str, object] = {
        "orders": orders_report(session),
        "bounded": bounded_report(session),
        "ranks": ranks_report(session),
        "present": present_report(session),
        "follow_ups": follow_ups_report(session),
        "completions": completions_report(session),
        "interference": interference_report(session),
        "study": "studies/HOLE_FOLDS_STUDY.md",
        "lean_file": "RequestProject/GLM/HoleBounds.lean",
    }
    if scripts:
        report["scripts"] = scripts_report(session)
    return report

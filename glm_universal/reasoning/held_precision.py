"""``glm_universal.reasoning.held_precision`` -- a register value's stated
precision, carried through a derivation.

Why this module exists
----------------------
The stepwise planner feeds register values into the formula wheels (Phase 73)
as the exact rationals the register holds.  A melting point held as ``1811``
is a reading at the unit: it stands for anything in ``[1810.5, 1811.5]``
(:meth:`glm_universal.reasoning.intervals.Interval.as_held`).  An answer
derived from it was stated as if exact.  This module states what the answer
is at the precision the register holds (``studies/HELD_PRECISION_STUDY.md``,
candidate O6).

The object
----------
Every wheel step is a monomial in its inputs (an axiom ``c1 prod x^a =
c2 prod y^b`` solved for a variable of power +-1); a step into or out of SI
multiplies by an exact positive factor; a leaf is a given, a measured amount
or a register lookup.  So the answer of a goal or narrative chain is one
monomial ``C * prod leaf_k ** e_k`` in its leaves, with integer exponents
(:func:`composite`).  Over a box of positive leaf intervals it is monotone in
every leaf, so its range is exact and attained at two corners
(:func:`answer_interval`) -- each leaf at its low or high end by the sign of
its exponent.  A leaf of exponent 0 has cancelled and its precision does not
reach the answer.  ``RequestProject/GLM/HeldPrecision.lean`` proves the
corner bound, and that step-by-step interval arithmetic -- the control
(:func:`stepwise_interval`) -- can be strictly wider.

A register lookup is read at its stated precision; a given or a measured
amount is the number the question states, and is exact.

Exact ``Fraction`` arithmetic throughout (D7); only the standard library, the
interval module and the chain's own step type are read.
"""

from __future__ import annotations

import itertools
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .intervals import Interval

__all__ = ["LEAF_OPS", "composite", "leaf_intervals", "answer_interval",
           "stepwise_interval", "chain_precision", "precision_note",
           "evaluate_at", "held_precision_report", "unchanged", "LEAN_FILE",
           "LEAN_THEOREMS", "STATED_ORIGINS"]

#: Steps whose value is read rather than computed.
LEAF_OPS = ("given", "measured", "lookup", "literal", "constant")

Mono = Tuple[Fraction, Dict[int, int]]

#: The origins of a wheel step whose value the chain states as asked for (a
#: stitched step is an intermediate the question did not ask for).
STATED_ORIGINS = ("asked", "deferred", "moved earlier")


class NotMonomial(ValueError):
    """A chain whose answer is not one monomial in its leaves."""


def _axiom_monomial(step, inputs: Mapping[str, Mono]) -> Mono:
    """The solved variable of an axiom step as a monomial of its inputs'
    composites."""
    lhs, rhs = step.detail["sides"]
    v = step.detail["solved_for"]
    own = other = None
    k = 0
    for side, rest in ((lhs, rhs), (rhs, lhs)):
        for name, e in side[1]:
            if name == v:
                own, other, k = side, rest, int(e)
    if own is None or k not in (1, -1):
        raise NotMonomial(f"step {step.index}: {v} has power {k}")
    coef = (Fraction(other[0]) / Fraction(own[0])) ** k
    exps: Dict[int, int] = {}
    for sign, side in ((1, other), (-1, own)):
        for name, e in side[1]:
            if name == v:
                continue
            c, ex = inputs[name]
            power = sign * int(e) * k
            coef *= c ** power
            for leaf, p in ex.items():
                exps[leaf] = exps.get(leaf, 0) + p * power
    return coef, {leaf: p for leaf, p in exps.items() if p}


def composite(steps: Sequence) -> Mono:
    """The answer of a chain as ``(C, {leaf index: exponent})``.

    Raises :class:`NotMonomial` for a chain with a step that is not a leaf,
    an SI conversion or a wheel axiom (a composition's sum, say).
    """
    monos: Dict[int, Mono] = {}
    for s in steps:
        if s.op in LEAF_OPS:
            if not isinstance(s.value, Fraction):
                raise NotMonomial(f"step {s.index} is not a number")
            monos[s.index] = (Fraction(1), {s.index: 1})
        elif s.op == "si":
            if Fraction(s.detail.get("offset", "0")) != 0:
                raise NotMonomial(f"step {s.index} adds an offset "
                                  f"(a temperature level)")
            c, ex = monos[s.inputs[0]]
            monos[s.index] = (c * Fraction(s.detail["factor"]), dict(ex))
        elif s.op == "unit_out":
            c, ex = monos[s.inputs[0]]
            monos[s.index] = (c / Fraction(s.detail["factor"]), dict(ex))
        elif s.op == "axiom":
            named = {name: monos[j] for name, j in s.detail["names"]}
            monos[s.index] = _axiom_monomial(s, named)
        else:
            raise NotMonomial(f"step {s.index} is a {s.op} step")
    return monos[steps[-1].index]


def leaf_intervals(steps: Sequence) -> Dict[int, Interval]:
    """Every leaf read at its precision: a lookup at the places the register
    wrote it, a given or a measured amount as the exact number stated."""
    out: Dict[int, Interval] = {}
    for s in steps:
        if s.op in LEAF_OPS and isinstance(s.value, Fraction):
            if s.op == "lookup":
                out[s.index] = Interval.as_held(s.value, s.label)
            else:
                out[s.index] = Interval(s.value, s.value, s.label)
    return out


def _mono_value(mono: Mono, point: Mapping[int, Fraction]) -> Fraction:
    c, ex = mono
    out = c
    for leaf, e in ex.items():
        out *= point[leaf] ** e
    return out


def answer_interval(steps: Sequence) -> Optional[Tuple[Fraction, Fraction]]:
    """The exact range of the answer over the held box, or ``None`` when a
    leaf that reaches the answer is not strictly positive (the corner argument
    needs positive leaves)."""
    c, ex = composite(steps)
    box = leaf_intervals(steps)
    if any(box[leaf].lo <= 0 for leaf in ex):
        return None
    lo_pt = {leaf: (box[leaf].lo if (e > 0) == (c > 0) else box[leaf].hi)
             for leaf, e in ex.items()}
    hi_pt = {leaf: (box[leaf].hi if (e > 0) == (c > 0) else box[leaf].lo)
             for leaf, e in ex.items()}
    a, b = _mono_value((c, ex), lo_pt), _mono_value((c, ex), hi_pt)
    return (min(a, b), max(a, b))


def evaluate_at(steps: Sequence, point: Mapping[int, Fraction]) -> Fraction:
    """The chain's answer recomputed through its own steps with the leaves
    set to ``point`` (leaves not in ``point`` keep their values)."""
    vals: Dict[int, Fraction] = {}
    for s in steps:
        if s.op in LEAF_OPS:
            vals[s.index] = point.get(s.index, s.value)
        elif s.op == "si":
            vals[s.index] = vals[s.inputs[0]] * Fraction(s.detail["factor"])
        elif s.op == "unit_out":
            vals[s.index] = vals[s.inputs[0]] / Fraction(s.detail["factor"])
        elif s.op == "axiom":
            named = {name: (Fraction(1), {j: 1}) for name, j in s.detail["names"]}
            vals[s.index] = _mono_value(_axiom_monomial(s, named), vals)
        else:
            raise NotMonomial(f"step {s.index} is a {s.op} step")
    return vals[steps[-1].index]


def stepwise_interval(steps: Sequence) -> Optional[Tuple[Fraction, Fraction]]:
    """The control: each step's interval from its inputs' intervals alone
    (the corners of that one step), as naive interval arithmetic does."""
    box = leaf_intervals(steps)
    iv: Dict[int, Tuple[Fraction, Fraction]] = {}
    for s in steps:
        if s.op in LEAF_OPS:
            iv[s.index] = (box[s.index].lo, box[s.index].hi)
        elif s.op in ("si", "unit_out"):
            f = Fraction(s.detail["factor"])
            a, b = iv[s.inputs[0]]
            a, b = (a * f, b * f) if s.op == "si" else (a / f, b / f)
            iv[s.index] = (min(a, b), max(a, b))
        elif s.op == "axiom":
            names = [(name, j) for name, j in s.detail["names"]]
            if any(iv[j][0] <= 0 for _n, j in names):
                return None
            local = {name: (Fraction(1), {j: 1}) for name, j in names}
            mono = _axiom_monomial(s, local)
            corners = [_mono_value(mono, dict(zip([j for _n, j in names], pt)))
                       for pt in itertools.product(*[iv[j] for _n, j in names])]
            iv[s.index] = (min(corners), max(corners))
        else:
            return None
    return iv[steps[-1].index]


def _render(q: Fraction) -> str:
    """An integer, a terminating decimal written out, or ``n/d``."""
    if q.denominator == 1:
        return str(q.numerator)
    d, places = q.denominator, 0
    while d % 10 == 0 or d % 2 == 0 or d % 5 == 0:
        if d % 10 == 0:
            d //= 10
        elif d % 2 == 0:
            d //= 2
        else:
            d //= 5
        places += 1
    if d != 1 or places > 30:
        return f"{q.numerator}/{q.denominator}"
    scaled = q * 10 ** places
    while scaled.denominator != 1:
        places += 1
        scaled = q * 10 ** places
    sign = "-" if scaled < 0 else ""
    digits = str(abs(scaled.numerator)).rjust(places + 1, "0")
    text = f"{digits[:-places]}.{digits[-places:]}".rstrip("0").rstrip(".")
    return sign + text


def _target(steps: Sequence, k: int) -> Optional[Dict[str, object]]:
    """The precision of the value of step ``k`` (1-based) of a chain."""
    prefix = [s for s in steps if s.index <= k]
    c, ex = composite(prefix)
    box = answer_interval(prefix)
    return {"label": prefix[-1].label, "value": prefix[-1].value,
            "coefficient": c, "exponents": dict(ex), "interval": box,
            "exact": box is not None and box[0] == box[1],
            "cancelled": [s.label for s in prefix
                          if s.op == "lookup" and s.index not in ex],
            "naive": stepwise_interval(prefix)}


def chain_precision(steps: Sequence) -> Optional[Dict[str, object]]:
    """What the held precision does to a chain's stated values; ``None`` when
    the chain reads no register value or is not monomial in its leaves.

    Every value the chain states -- each step asked for, and the answer -- is
    given its exact interval; the answer's is ``interval``.
    """
    lookups = [s for s in steps if s.op == "lookup"]
    if not lookups:
        return None
    try:
        converted = {s.inputs[0] for s in steps if s.op == "unit_out"}
        stated = [s.index for s in steps
                  if (s.op == "unit_out" or (
                      s.op == "axiom" and s.origin in STATED_ORIGINS))
                  and s.index not in converted]
        last = steps[-1].index
        if last not in stated:
            stated.append(last)
        targets = [_target(steps, k) for k in sorted(set(stated))]
    except (NotMonomial, KeyError):
        return None
    box = leaf_intervals(steps)
    held = [(s.label, _render(s.value), _render(box[s.index].lo),
             _render(box[s.index].hi)) for s in lookups]
    answer = next(t for t in targets if t["label"] == steps[-1].label
                  and t["value"] == steps[-1].value)
    out = {"answer": steps[-1].value, "held": held, "targets": targets,
           "interval": answer["interval"], "exact": answer["exact"],
           "cancelled": answer["cancelled"],
           "coefficient": answer["coefficient"],
           "exponents": answer["exponents"], "naive": answer["naive"]}
    out["note"] = precision_note(out)
    return out


def precision_note(p: Mapping[str, object]) -> str:
    """The note a chain carries: each held value, then each stated value's
    interval (or that it is exact because the held values cancel)."""
    held = "; ".join(f"{label} is held as {v}, read as [{lo}, {hi}]"
                     for label, v, lo, hi in p["held"])
    parts = []
    for t in p["targets"]:
        box = t["interval"]
        if box is None:
            parts.append(f"{t['label']}: not carried (a leaf is not positive)")
        elif t["exact"]:
            parts.append(f"{t['label']} = {_render(t['value'])} is exact at "
                         f"any held value in range ({', '.join(t['cancelled'])} "
                         f"cancels)")
        else:
            lo, hi = box
            parts.append(f"{t['label']} lies in [{_render(lo)}, "
                         f"{_render(hi)}] (width {_render(hi - lo)})")
    return f"precision: {held}; so " + "; ".join(parts)


# ===========================================================================
# THE MEASUREMENT OF THE STUDY
# ===========================================================================

def _corpus_questions() -> List[str]:
    from ..evaluation import stepwise_cases as a, stepwise_two_cases as b
    out: List[str] = []
    for mod in (a, b):
        for name in ("COMPOSITION_CASES", "GOAL_CASES", "FRAME_CASES",
                     "UNIT_CASES", "REGISTER_CASES", "NARRATIVE_CASES"):
            for case in getattr(mod, name, ()):
                out.append(case[1])
    return list(dict.fromkeys(out))


def _grid_ok(steps, box) -> bool:
    lk = leaf_intervals(steps)
    leaves = [i for i, iv in lk.items() if iv.lo != iv.hi]
    lo, hi = box
    for pt in itertools.product(*[(lk[i].lo, (lk[i].lo + lk[i].hi) / 2,
                                   lk[i].hi) for i in leaves]):
        v = evaluate_at(steps, dict(zip(leaves, pt)))
        if not lo <= v <= hi:
            return False
    return True


def _corners_attained(steps, box) -> bool:
    lk = leaf_intervals(steps)
    leaves = [i for i, iv in lk.items() if iv.lo != iv.hi]
    values = {evaluate_at(steps, dict(zip(leaves, pt)))
              for pt in itertools.product(*[(lk[i].lo, lk[i].hi)
                                            for i in leaves])}
    return box[0] in values and box[1] in values


LEAN_FILE = "RequestProject/GLM/HeldPrecision.lean"
LEAN_THEOREMS = ("monomial_corner_bounds", "scaled_corner_bounds", "corner_mem",
                 "stepwise_strictly_wider")


def _lean_has(names: Sequence[str]) -> bool:
    import re
    from pathlib import Path
    path = Path(__file__).resolve().parents[2] / "glm_lean" / LEAN_FILE
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return "sorry" not in text and all(
        re.search(rf"\btheorem {n}\b", text) for n in names)


def _verdicts(session, questions: Sequence[str]) -> List[Tuple[str, str]]:
    from ..runtime import stepwise as sw
    return [(a.verdict, a.value) for a in (sw.answer(session, q)
                                           for q in questions)]


def unchanged(session=None) -> Dict[str, object]:
    """Mark H4: every verdict and value of the stepwise corpora, with the
    precision note switched off and on."""
    import sys
    from ..runtime.session import GeometricSession
    session = session or GeometricSession()
    questions = _corpus_questions()
    on = _verdicts(session, questions)
    module = sys.modules[__name__]
    saved = module.chain_precision
    module.chain_precision = lambda steps: None      # type: ignore[assignment]
    try:
        off = _verdicts(session, questions)
    finally:
        module.chain_precision = saved               # type: ignore[assignment]
    return {"questions": len(questions), "same": on == off}


def held_precision_report() -> Dict[str, object]:
    """Every measurement of ``studies/HELD_PRECISION_STUDY.md`` and its marks."""
    from ..runtime import stepwise as sw
    from ..runtime.session import GeometricSession
    session = GeometricSession()
    rows = []
    for q in _corpus_questions():
        a = sw.answer(session, q)
        if not a.answered or a.chain.kind not in ("goal", "narrative"):
            continue
        steps = a.chain.steps
        reads = any(s.op == "lookup" for s in steps)
        notes = [n for n in a.chain.notes if n.startswith("precision: ")]
        row = {"question": q, "value": a.value, "reads_register": reads,
               "noted": bool(notes)}
        p = chain_precision(steps)
        if p is not None and p["interval"] is not None:
            box = p["interval"]
            row.update({
                "interval": [_render(box[0]), _render(box[1])],
                "exact": p["exact"], "cancelled": p["cancelled"],
                "composite_equals_answer": (
                    _mono_value((p["coefficient"], p["exponents"]),
                                {i: s.value for s in steps for i in [s.index]
                                 if s.op in LEAF_OPS}) == steps[-1].value),
                "corners_attained": _corners_attained(steps, box),
                "grid_inside": _grid_ok(steps, box),
                "naive": [_render(p["naive"][0]), _render(p["naive"][1])]
                if p["naive"] else None,
                "naive_wider": bool(p["naive"]) and
                (p["naive"][1] - p["naive"][0]) > (box[1] - box[0]),
                "note": p["note"]})
        rows.append(row)
    with_reg = [r for r in rows if r["reads_register"]]
    same = unchanged(session)
    marks = {
        "H1": all(r["noted"] == r["reads_register"] for r in rows),
        "H2": all(r.get("composite_equals_answer") and r.get("corners_attained")
                  and r.get("grid_inside") for r in with_reg),
        "H3": (sum(1 for r in with_reg if r.get("exact")) >= 1
               and sum(1 for r in with_reg if r.get("naive_wider")) >= 1),
        "H4": same["same"],
        "H5": _lean_has(LEAN_THEOREMS),
    }
    return {"chains": len(rows), "with_register": len(with_reg),
            "exact": sum(1 for r in with_reg if r.get("exact")),
            "naive_wider": sum(1 for r in with_reg if r.get("naive_wider")),
            "corpus_questions": same["questions"],
            "rows": rows, "marks": marks}

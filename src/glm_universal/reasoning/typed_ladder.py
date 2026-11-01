"""``glm_universal.reasoning.typed_ladder`` -- the typed planner and the
session's field answers through the batch machine (Phase 153).

*Created 31 October 2026.*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/CARRIED_READ_STUDY.md
(§0, marks T1, T2, S1, S2) and MASTER_PLAN.md (Phase 153).*

* **A typed plan as a chain.**  An answered ``arith``, ``gcd``, ``lcm``,
  ``prime`` or ``convert`` plan of the typed planner
  (:mod:`glm_universal.runtime.semantic_plan`) is said as a stepwise chain
  -- the numbers read from the question, the operation computed -- and run
  through :func:`planner_ladder.check_chain` in its reading mode
  (:func:`plan_check`).  A plan the machine disagrees with is to be refused
  as ``MACHINE_DRIFT``.
* **A field answer as one read.**  A ``field`` answer whose value is a
  scalar of a register table is one register read (:func:`field_check`);
  the machine must find it in its own copy of the register.

The gates themselves belong to the answering path
(``runtime/semantic_plan.ask_planned`` and ``runtime/session._solve_field``);
this module is what they call, and what the measurement calls directly.

Exactness
---------
Integers, :class:`fractions.Fraction` and strings only.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Tuple

__all__ = ["KINDS", "REFUSAL", "ON", "plan_chain", "plan_check",
           "field_chain", "field_check", "field_lie", "typed_lie"]

#: The switch of this round's two answering-path gates (the typed planner's
#: and the field answers').  The gates read it; the frozen-path baseline is
#: taken with it off.  (The gates themselves live in ``runtime/`` and were
#: lost in the October 2026 reorganisation; see the module docstring.)
ON: bool = True

#: The plan kinds said as chains.
KINDS: Tuple[str, ...] = ("arith", "convert", "gcd", "lcm", "prime")

#: The refusal a gate gives when the machine disagrees.
REFUSAL: str = "MACHINE_DRIFT"

_ARITH = {"+": "add", "-": "sub", "*": "mul", "/": "div"}


def _parse(value: str) -> object:
    from .stepwise_script import parse_value
    return parse_value(str(value).strip())


def plan_chain(planned) -> Optional[object]:
    """The stepwise chain of an answered typed plan of :data:`KINDS`, or
    ``None`` for any other plan."""
    from .stepwise_script import Chain, Step
    if planned is None or planned.verdict != "answered" or \
            planned.chosen is None:
        return None
    o = planned.chosen
    kind = o.plan.compute
    if kind not in KINDS:
        return None
    args = tuple(o.plan.args)
    steps: List[object] = []

    def lit(v: Fraction) -> int:
        v = Fraction(v)
        s = Step(len(steps) + 1, "literal", (), v, _text(v), {}, "asked")
        steps.append(s)
        return s.index

    def add(op: str, ins: Tuple[int, ...], value: object,
            detail: Optional[Dict[str, object]] = None) -> int:
        s = Step(len(steps) + 1, op, ins, value, f"{op} of steps", 
                 dict(detail or {}), "asked")
        steps.append(s)
        return s.index

    claim = _parse(o.value)
    if kind == "arith":
        op, a, b = args
        i, j = lit(a), lit(b)
        add(_ARITH[str(op)], (i, j), claim)
    elif kind == "convert":
        amount, src, dst = args
        i = lit(amount)
        add("si", (i,), claim, {"factor": _text(Fraction(src.factor) /
                                                 Fraction(dst.factor)),
                                "kind": "unit", "from": src.name,
                                "quantity": src.quantity})
    elif kind in ("gcd", "lcm"):
        vals = [Fraction(v) for v in args]
        if len(vals) < 2:
            return None
        acc = lit(vals[0])
        run = vals[0]
        from math import gcd
        for v in vals[1:]:
            j = lit(v)
            a, b = int(run), int(v)
            g = gcd(a, b)
            run = Fraction(g if kind == "gcd" else
                           (abs(a * b) // g if g else 0))
            acc = add(kind, (acc, j), run)
        if run != claim:
            steps[-1] = Step(steps[-1].index, kind, steps[-1].inputs, claim,
                             steps[-1].label, {}, "asked")
    elif kind == "prime":
        (x,) = args
        i = lit(x)
        add("prime", (i,), claim)
    return Chain(planned.text, tuple(steps), "typed")


def _text(v: Fraction) -> str:
    return str(v.numerator) if v.denominator == 1 else \
        f"{v.numerator}/{v.denominator}"


def plan_check(planned, say: bool = False) -> Optional[Dict[str, object]]:
    """The machine's verdict on an answered typed plan of :data:`KINDS`
    (``None`` for another plan): :func:`planner_ladder.check_chain` in the
    reading mode, with ``refusal`` set to :data:`REFUSAL` when not
    admitted."""
    from . import planner_ladder as pl
    chain = plan_chain(planned)
    if chain is None:
        return None
    c = pl.check_chain(chain, say=say, read=True)
    c["refusal"] = "" if c["admitted"] else REFUSAL
    c["chain"] = chain
    c["last_computed"] = bool(c["computed"]) and \
        c["computed"][-1] == len(chain.steps)
    return c


def typed_lie(chain):
    """The chain with its claim (the last step) altered."""
    from . import planner_ladder as pl
    last = chain.steps[-1]
    lie = pl.value_lie(last)
    return None if lie is None else pl.lie_chain(chain, last.index, lie)


# ---------------------------------------------------------------------------
# the field answers
# ---------------------------------------------------------------------------

def field_lie(value: object) -> object:
    """A field value altered: a number raised by one, a truth value flipped,
    any other text with ``x`` appended (still a sayable value, never the
    register's)."""
    if isinstance(value, bool):
        return str(not value)
    if isinstance(value, int):
        return Fraction(value + 1)
    if isinstance(value, Fraction):
        return value + 1
    text = str(value)
    if text in ("True", "False"):
        return "False" if text == "True" else "True"
    return text + "x"


def field_chain(held) -> Optional[object]:
    """One register read: the chain of a field answer (``FieldValue``) whose
    value is a scalar a register line can carry, else ``None``."""
    from . import register_files as rf
    from .stepwise_script import Chain, Step
    v = held.value
    if isinstance(v, bool):
        v = str(v)
    elif isinstance(v, int):
        v = Fraction(v)
    if rf.entry_line(held.row, held.field, v) is None:
        return None
    step = Step(1, "lookup", (), v, f"{held.field} of {held.row}",
                {"table": held.table, "row": held.row, "field": held.field,
                 "question": f"field {held.field} of {held.row}"}, "asked")
    return Chain(f"field {held.field} of {held.row}", (step,), "field")


def field_check(held, files=None, value: object = None
                ) -> Optional[Dict[str, object]]:
    """The machine's read of a field answer: admitted when ``FIND`` finds it
    in the register file.  ``value`` replaces the answered value (a lie);
    ``files`` are the register files (built when ``None``)."""
    from . import planner_ladder as pl
    from . import register_files as rf
    chain = field_chain(held)
    if chain is None:
        return None
    if value is not None:
        chain = pl.lie_chain(chain, 1, value)
    if files is None:
        files = rf.register_files()["files"]
    path = rf.table_path(held.table)
    seed = {path: files[path]} if path in files else {}
    c = pl.check_chain(chain, say=False, read=True, files=seed)
    c["refusal"] = "" if c["admitted"] else REFUSAL
    return c

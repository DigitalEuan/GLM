"""``glm_universal.reasoning.stepwise_script`` -- the three columns of a chain.

A **chain** is the stepwise planner's answer (Phase 72,
``studies/STEPWISE_PLANNER_STUDY.md``): a list of :class:`Step` whose inputs
point only backwards, each carrying its own three columns.

* **Column 1** of a step is one sentence of a declared template
  (:func:`sentence`), which :func:`read_sentence` reads back.
* **Column 2** is one exact equation ``sₖ = … = v`` (:func:`equation`), which
  :func:`read_equation` reads back.
* **Column 3** is the chain's script (:func:`render_script`), run by the
  runtime in a fresh ``python3 -I``.  For every step it reads both columns
  back with its **own** readers and requires them to name the same operation,
  inputs and value as the recorded step (``ALIGNED``), then recomputes the
  value with its own exact arithmetic -- re-reading the register for a
  looked-up step, re-parsing the question for a given, substituting into the
  wheel's own axiom for an axiom step.  Then it checks the links (every input
  an earlier step) and the answer sentence, and prints ``VERIFIED True`` only
  if everything holds.

:func:`step_check` is the same per-step check in-process: the runtime admits a
step into a chain only when it passes (the *step gate*).  :func:`mutants`
builds the four declared mutations of a chain (a consistent lie in one value,
column 1 alone altered, two dependent steps swapped, the answer altered) that
the script must reject.

This module starts no process (the reasoning layer never does); the runtime
runs the script.  Exact throughout: ``int`` and ``Fraction``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = ["Step", "Chain", "ARITH", "render_value", "parse_value",
           "sentence", "equation", "read_sentence", "read_equation",
           "answer_sentence", "recompute", "step_check", "chain_check",
           "chain_data", "render_script", "mutants", "MUTATION_KINDS",
           "prime_factor"]

#: The four binary arithmetic operations and their symbols.
ARITH: Dict[str, str] = {"add": "+", "sub": "-", "mul": "*", "div": "/"}

_ARITH_WORDS: Dict[str, Tuple[str, str]] = {
    "add": ("adding", "and"), "sub": ("subtracting", "from"),
    "mul": ("multiplying", "by"), "div": ("dividing", "by"),
}

#: The mutation kinds: the four of mark S5, then ``read-lie``, which the
#: round added beyond its declaration, then ``unit-lie`` (round two, mark
#: T5): a conversion step's factor altered, both columns re-rendered.
MUTATION_KINDS: Tuple[str, ...] = ("value-lie", "column-1", "reorder",
                                   "answer", "read-lie", "unit-lie",
                                   "member-lie", "word-lie", "hole-lie")

#: The words column 1 writes a fold with (round three, Phase 84).
FOLD_WORDS: Dict[str, str] = {"sum": "sum", "mean": "mean",
                              "odd": "count of odd values",
                              "even": "count of even values",
                              # round four (Phase 85): the order folds
                              "median": "median", "max": "largest value",
                              "min": "smallest value"}

#: The order folds of round four (Phase 85, ``studies/HOLE_FOLDS_STUDY.md``):
#: the ones a hole bounds rather than frees.
ORDER_FOLDS: Tuple[str, ...] = ("median", "max", "min", "rank")


def fold_words(d: Mapping[str, object]) -> str:
    """The words column 1 writes a fold with; a rank names its row."""
    if d["fn"] == "rank":
        return f"rank of {d['row']} (largest first)"
    return FOLD_WORDS[str(d["fn"])]


def fold_scope(d: Mapping[str, object]) -> str:
    """What column 1 adds after the set: the present rows with the missing
    ones named, or the holes a bounded answer ranges over (round four)."""
    missing = ", ".join(d.get("missing", ())) or "none"
    if d.get("present"):
        return f" that have a reading (missing: {missing})"
    if d.get("bounded"):
        return (f" with {len(d['missing'])} missing ({missing}), bounded "
                f"over every completion")
    return ""


def fold_tag(d: Mapping[str, object]) -> str:
    """What column 2 adds inside the fold's brackets (round four)."""
    out = ""
    if d["fn"] == "rank":
        out += f"; row {d['row']}"
    missing = ", ".join(d.get("missing", ())) or "none"
    if d.get("present"):
        out += f"; present, missing {missing}"
    elif d.get("bounded"):
        out += f"; holes {missing}"
    return out


def _between(lo: Fraction, hi: Fraction) -> object:
    return lo if lo == hi else \
        f"between {render_value(lo)} and {render_value(hi)}"


def fold_value(fn: str, vals: Sequence[Fraction], holes: int = 0,
               x: Optional[Fraction] = None) -> object:
    """A fold's value over the readings that are present, with ``holes``
    readings missing: exact when ``holes`` is 0; for the median and the rank
    the interval every completion lands in (a single value when it closes),
    by the rule of ``GLM.HoleBounds``; ``None`` when a side is left open.
    Sums, means and parity counts have no bound under a hole (``None``)."""
    vals = [Fraction(v) for v in vals]
    if fn in ("sum", "mean", "odd", "even") and holes:
        return None
    if fn == "sum":
        return sum(vals, Fraction(0))
    if fn == "mean":
        return sum(vals, Fraction(0)) / len(vals) if vals else None
    if fn in ("odd", "even"):
        want = 1 if fn == "odd" else 0
        return Fraction(sum(1 for v in vals if v.numerator % 2 == want))
    if fn == "rank":
        if x is None:
            return None
        r = 1 + sum(1 for v in vals if v > x)
        return _between(Fraction(r), Fraction(r + holes))
    if fn in ("max", "min"):
        if holes or not vals:
            return None
        return max(vals) if fn == "max" else min(vals)
    if fn == "median":
        p = sorted(vals)
        n = len(p) + holes
        if n == 0:
            return None
        ks = [n // 2] if n % 2 else [n // 2 - 1, n // 2]
        if any(k - holes < 0 or k >= len(p) for k in ks):
            return None
        lo = sum((p[k - holes] for k in ks), Fraction(0)) / len(ks)
        hi = sum((p[k] for k in ks), Fraction(0)) / len(ks)
        return _between(lo, hi)
    return None


# ===========================================================================
# 1.  STEPS AND CHAINS
# ===========================================================================

@dataclass(frozen=True)
class Step:
    """One step of a chain.

    ``op`` is one of ``literal``, ``lookup``, ``planned``, ``given``,
    ``add``, ``sub``, ``mul``, ``div``, ``pow``, ``gcd``, ``lcm``, ``prime``,
    ``compare``, ``larger``, ``axiom``, and (round two, Phase 73)
    ``measured`` (a given as written, in a unit), ``si`` (a value carried
    into SI by a declared unit or scale), ``unit_out`` (an SI value stated in
    a unit asked for), ``parity`` and ``mean``, and (round three, Phase 84)
    ``comparative`` (the row a declared comparative names) and ``fold`` (a
    sum, mean or parity count over a declared set).  ``inputs`` are 1-based indices of
    earlier steps.  ``value`` is a ``Fraction`` for a number, or a string for
    a verdict (``prime`` / ``not prime``, ``True`` / ``False``, or the
    winning label of ``larger``).  ``detail`` holds what the op needs to be
    re-derived (the table, row and field of a lookup; the axiom, wheel and
    variable map of an axiom step).  ``origin`` is ``asked``, ``stitched``,
    ``deferred``, ``given`` or ``follow-up``.
    """

    index: int
    op: str
    inputs: Tuple[int, ...]
    value: object
    label: str
    detail: Mapping[str, object] = field(default_factory=dict)
    origin: str = "asked"

    @property
    def numeric(self) -> bool:
        return isinstance(self.value, Fraction)

    def as_dict(self) -> Dict[str, object]:
        return {"index": self.index, "op": self.op,
                "inputs": list(self.inputs),
                "value": render_value(self.value), "label": self.label,
                "detail": {k: _jsonable(v) for k, v in self.detail.items()},
                "origin": self.origin}


@dataclass(frozen=True)
class Chain:
    """A chain of steps, the question it answers, and the answer."""

    question: str
    steps: Tuple[Step, ...]
    kind: str                      # composition | goal | narrative
    notes: Tuple[str, ...] = ()

    @property
    def answer(self) -> object:
        return self.steps[-1].value if self.steps else None

    def column1(self) -> Tuple[str, ...]:
        return tuple(sentence(s) for s in self.steps) + (
            answer_sentence(self),)

    def column2(self) -> Tuple[str, ...]:
        return tuple(equation(s, self.steps) for s in self.steps)


def _jsonable(v: object) -> object:
    if isinstance(v, Fraction):
        return render_value(v)
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    return v


def render_value(v: object) -> str:
    """A value as both columns write it: ``n`` or ``n/d`` for a number."""
    if isinstance(v, Fraction):
        return str(v.numerator) if v.denominator == 1 else \
            f"{v.numerator}/{v.denominator}"
    if isinstance(v, int) and not isinstance(v, bool):
        return str(v)
    return str(v)


def parse_value(s: str) -> object:
    """The inverse of :func:`render_value`: a number when it reads as one."""
    if re.fullmatch(r"-?\d+", s):
        return Fraction(int(s))
    if re.fullmatch(r"-?\d+/\d+", s):
        n, d = s.split("/")
        return Fraction(int(n), int(d))
    return s


def prime_factor(n: int) -> Optional[int]:
    """The least prime factor of ``n`` when ``n`` is composite, else None."""
    if n < 4:
        return None
    if n % 2 == 0:
        return 2
    f = 3
    while f * f <= n:
        if n % f == 0:
            return f
        f += 2
    return None


# ===========================================================================
# 2.  COLUMN 1 AND COLUMN 2 -- THE DECLARED TEMPLATES
# ===========================================================================

def sentence(s: Step) -> str:
    """Column 1 of one step: a sentence of the op's declared template."""
    k, v = s.index, render_value(s.value)
    i = s.inputs
    if s.op == "literal":
        return f"Step {k}: the number {v}."
    if s.op == "constant":
        return f"Step {k}: {s.label} is {v}, a defined constant of the SI."
    if s.op == "lookup":
        d = s.detail
        return (f"Step {k}: {s.label} is {v}, held by the {d['table']} "
                f"table as {d['field']} of {d['row']}.")
    if s.op == "planned":
        return (f"Step {k}: {s.label} is {v}, computed by the planner's "
                f"{s.detail['computation']} plan.")
    if s.op == "given":
        return f"Step {k}: {s.label} is given as {v}."
    if s.op == "measured":
        return f"Step {k}: {s.label} is given as {v}, in {s.detail['unit']}."
    if s.op == "si":
        return f"Step {k}: step {i[0]}, carried into SI units, is {v}."
    if s.op == "unit_out":
        return (f"Step {k}: step {i[0]}, stated in {s.detail['unit']}, is "
                f"{v}.")
    if s.op == "parity":
        return f"Step {k}: that step {i[0]} is {s.detail['asked']} is {v}."
    if s.op == "mean":
        ins = ", ".join(f"step {j}" for j in i[:-1]) + f" and step {i[-1]}"
        return f"Step {k}: the mean of {ins} is {v}."
    if s.op == "comparative":
        a, b = s.detail["rows"]
        return (f"Step {k}: of {a} and {b}, the {s.detail['word']} by step "
                f"{i[0]} and step {i[1]} is {v}.")
    if s.op == "fold":
        d = s.detail
        ins = ", ".join(f"step {j}" for j in i[:-1])
        ins = f"{ins} and step {i[-1]}" if ins else f"step {i[-1]}"
        return (f"Step {k}: the {fold_words(d)} of {d['field']} over "
                f"the {d['set']}{fold_scope(d)}, from {ins}, is {v}.")
    if s.op in ARITH:
        verb, joint = _ARITH_WORDS[s.op]
        a, b = (i[1], i[0]) if s.op == "sub" else (i[0], i[1])
        return f"Step {k}: {verb} step {a} {joint} step {b} gives {v}."
    if s.op == "pow":
        return (f"Step {k}: raising step {i[0]} to the power "
                f"{s.detail['exponent']} gives {v}.")
    if s.op in ("gcd", "lcm"):
        name = ("greatest common divisor" if s.op == "gcd"
                else "least common multiple")
        return f"Step {k}: the {name} of step {i[0]} and step {i[1]} is {v}."
    if s.op == "prime":
        return f"Step {k}: step {i[0]} is {v}."
    if s.op == "compare":
        return (f"Step {k}: that step {i[0]} is {s.detail['relation']} than "
                f"step {i[1]} is {v}.")
    if s.op == "larger":
        return (f"Step {k}: the {s.detail['relation']} of step {i[0]} and "
                f"step {i[1]} is {v}.")
    if s.op == "axiom":
        d = s.detail
        ins = " and ".join(f"step {j}" for j in i)
        return (f"Step {k}: {s.label} is {v}, by {d['axiom']} in "
                f"{d['wheel']}, from {ins}.")
    raise ValueError(f"no template for {s.op!r}")


def _ref(steps: Sequence[Step], j: int) -> str:
    return render_value(steps[j - 1].value)


def equation(s: Step, steps: Sequence[Step]) -> str:
    """Column 2 of one step: ``sₖ = <form over earlier steps> = <values> =
    <value>``."""
    k, v = s.index, render_value(s.value)
    i = s.inputs
    if s.op == "literal":
        return f"s{k} = {v}"
    if s.op == "lookup":
        d = s.detail
        return f"s{k} = {d['table']}[{d['row']}].{d['field']} = {v}"
    if s.op == "planned":
        return f"s{k} = plan[{s.detail['computation']}] = {v}"
    if s.op == "given":
        return f"s{k} = {s.detail['name']} = {v} (given)"
    if s.op == "measured":
        return (f"s{k} = {s.detail['name']} = {v} in {s.detail['unit']} "
                f"(given)")
    if s.op == "constant":
        return f"s{k} = const[{s.detail['name']}] = {v}"
    if s.op == "si":
        f = s.detail["factor"]
        o = s.detail.get("offset")
        if o is not None:
            return (f"s{k} = s{i[0]} * {f} + {o} [{s.detail['from']} -> SI, "
                    f"{s.detail['reading']}] = ({_ref(steps, i[0])}) * {f} + "
                    f"{o} = {v}")
        return (f"s{k} = s{i[0]} * {f} [{s.detail['from']} -> SI] = "
                f"({_ref(steps, i[0])}) * {f} = {v}")
    if s.op == "unit_out":
        f = s.detail["factor"]
        return (f"s{k} = s{i[0]} / {f} [SI -> {s.detail['unit']}] = "
                f"({_ref(steps, i[0])}) / {f} = {v}")
    if s.op == "parity":
        n = int(_ref(steps, i[0]))
        a = s.detail["asked"]
        return (f"s{k} = {a}?(s{i[0]}) = {a}?({n}) = {v}; {n} = 2 x "
                f"{n // 2} + {n % 2}")
    if s.op == "mean":
        refs = ", ".join(f"s{j}" for j in i)
        vals = " + ".join(f"({_ref(steps, j)})" for j in i)
        return f"s{k} = mean({refs}) = ({vals}) / {len(i)} = {v}"
    if s.op == "comparative":
        d = s.detail
        return (f"s{k} = {d['word']}(s{i[0]}, s{i[1]}) [{d['phrase']}, "
                f"{d['symbol']}] = {d['word']}({_ref(steps, i[0])}, "
                f"{_ref(steps, i[1])}) = {v}")
    if s.op == "fold":
        d = s.detail
        refs = ", ".join(f"s{j}" for j in i)
        return (f"s{k} = {d['fn']}[{d['set']}.{d['field']}{fold_tag(d)}]"
                f"({refs}) = {v}")
    if s.op in ARITH:
        o = ARITH[s.op]
        return (f"s{k} = s{i[0]} {o} s{i[1]} = ({_ref(steps, i[0])}) {o} "
                f"({_ref(steps, i[1])}) = {v}")
    if s.op == "pow":
        e = s.detail["exponent"]
        return f"s{k} = s{i[0]} ^ {e} = ({_ref(steps, i[0])}) ^ {e} = {v}"
    if s.op in ("gcd", "lcm"):
        return (f"s{k} = {s.op}(s{i[0]}, s{i[1]}) = {s.op}("
                f"{_ref(steps, i[0])}, {_ref(steps, i[1])}) = {v}")
    if s.op == "prime":
        n = _ref(steps, i[0])
        tail = ""
        if s.value == "not prime" and "factor" in s.detail:
            f = int(s.detail["factor"])
            tail = f"; {n} = {f} x {int(n) // f}"
        return f"s{k} = prime?(s{i[0]}) = prime?({n}) = {v}{tail}"
    if s.op == "compare":
        sym = s.detail["symbol"]
        return (f"s{k} = [s{i[0]} {sym} s{i[1]}] = [{_ref(steps, i[0])} "
                f"{sym} {_ref(steps, i[1])}] = {v}")
    if s.op == "larger":
        fn = "argmax" if s.detail["relation"] == "larger" else "argmin"
        return (f"s{k} = {fn}(s{i[0]}, s{i[1]}) = {fn}({_ref(steps, i[0])}, "
                f"{_ref(steps, i[1])}) = {v}")
    if s.op == "axiom":
        d = s.detail
        env = ", ".join(f"{name}=s{j}" for name, j in d["names"])
        return (f"s{k} = {d['solved']} [{env}] = {v}   "
                f"[{d['wheel']}: {d['axiom']}]")
    raise ValueError(f"no equation for {s.op!r}")


def answer_sentence(chain: Chain) -> str:
    """The last line of column 1: the answer, in words."""
    if not chain.steps:
        return "Answer: none."
    return f"Answer: {render_value(chain.answer)}."


# ===========================================================================
# 3.  THE READERS -- COLUMN 1 AND COLUMN 2 BACK TO (op, inputs, value)
# ===========================================================================

_VAL = r"(-?\d+(?:/\d+)?|prime|not prime|True|False|.+?)"


def read_sentence(text: str) -> Optional[Tuple[int, str, Tuple[int, ...],
                                              str]]:
    """``(index, op, inputs, value)`` read from a column-1 sentence."""
    pats = [
        (r"Step (\d+): the number " + _VAL + r"\.", "literal", 0),
        (r"Step (\d+): .+ is " + _VAL + r", a defined constant of the SI\.",
         "constant", 0),
        (r"Step (\d+): .+ is " + _VAL + r", held by the .+ table as .+\.",
         "lookup", 0),
        (r"Step (\d+): .+ is " + _VAL + r", computed by the planner's .+ "
         r"plan\.", "planned", 0),
        (r"Step (\d+): .+ is given as (-?\d+(?:/\d+)?), in .+\.", "measured",
         0),
        (r"Step (\d+): .+ is given as " + _VAL + r"\.", "given", 0),
        (r"Step (\d+): step (\d+), carried into SI units, is " + _VAL + r"\.",
         "si", 1),
        (r"Step (\d+): step (\d+), stated in .+, is " + _VAL + r"\.",
         "unit_out", 1),
        (r"Step (\d+): that step (\d+) is (?:odd|even) is (True|False)\.",
         "parity", 1),
        (r"Step (\d+): adding step (\d+) and step (\d+) gives " + _VAL +
         r"\.", "add", 2),
        (r"Step (\d+): subtracting step (\d+) from step (\d+) gives " + _VAL
         + r"\.", "sub", -2),
        (r"Step (\d+): multiplying step (\d+) by step (\d+) gives " + _VAL
         + r"\.", "mul", 2),
        (r"Step (\d+): dividing step (\d+) by step (\d+) gives " + _VAL +
         r"\.", "div", 2),
        (r"Step (\d+): raising step (\d+) to the power -?\d+ gives " + _VAL
         + r"\.", "pow", 1),
        (r"Step (\d+): the greatest common divisor of step (\d+) and step "
         r"(\d+) is " + _VAL + r"\.", "gcd", 2),
        (r"Step (\d+): the least common multiple of step (\d+) and step "
         r"(\d+) is " + _VAL + r"\.", "lcm", 2),
        (r"Step (\d+): that step (\d+) is \w+ than step (\d+) is " + _VAL +
         r"\.", "compare", 2),
        (r"Step (\d+): the (?:larger|smaller) of step (\d+) and step (\d+) "
         r"is " + _VAL + r"\.", "larger", 2),
        (r"Step (\d+): step (\d+) is " + _VAL + r"\.", "prime", 1),
    ]
    mf = re.fullmatch(r"Step (\d+): the (?:sum|mean|count of odd values|count "
                      r"of even values|median|largest value|smallest value|"
                      r"rank of \S+ \(largest first\)) of \S+ over the .+, "
                      r"from ((?:step \d+)"
                      r"(?:(?:, | and )step \d+)*), is " + _VAL + r"\.", text)
    if mf:
        ins = tuple(int(x) for x in re.findall(r"step (\d+)", mf.group(2)))
        return int(mf.group(1)), "fold", ins, mf.group(3)
    mc = re.fullmatch(r"Step (\d+): of .+ and .+, the \w+ by step (\d+) and "
                      r"step (\d+) is " + _VAL + r"\.", text)
    if mc:
        return (int(mc.group(1)), "comparative",
                (int(mc.group(2)), int(mc.group(3))), mc.group(4))
    mm = re.fullmatch(r"Step (\d+): the mean of ((?:step \d+)(?:(?:, | and )"
                      r"step \d+)+) is " + _VAL + r"\.", text)
    if mm:
        ins = tuple(int(x) for x in re.findall(r"step (\d+)", mm.group(2)))
        return int(mm.group(1)), "mean", ins, mm.group(3)
    for pat, op, n in pats:
        m = re.fullmatch(pat, text)
        if not m:
            continue
        g = m.groups()
        idx = int(g[0])
        count = abs(n)
        ins = tuple(int(x) for x in g[1:1 + count])
        if n < 0:
            ins = tuple(reversed(ins))
        return idx, op, ins, g[1 + count]
    m = re.fullmatch(r"Step (\d+): .+ is " + _VAL + r", by .+ in ([WC]\d+), "
                     r"from ((?:step \d+(?: and )?)+)\.", text)
    if m:
        ins = tuple(int(x) for x in re.findall(r"step (\d+)", m.group(4)))
        return int(m.group(1)), "axiom", ins, m.group(2)
    return None


def read_equation(text: str) -> Optional[Tuple[int, str, Tuple[int, ...],
                                              str]]:
    """``(index, op, inputs, value)`` read from a column-2 equation."""
    m = re.fullmatch(r"s(\d+) = (.+)", text)
    if not m:
        return None
    k, rest = int(m.group(1)), m.group(2)
    m2 = re.fullmatch(r"(?:sum|mean|odd|even|median|max|min|rank)\[[^\]]+\]"
                      r"\(((?:s\d+)(?:, s\d+)*)\) = (.+)", rest)
    if m2:
        ins = tuple(int(x) for x in re.findall(r"s(\d+)", m2.group(1)))
        return k, "fold", ins, m2.group(2)
    m2 = re.fullmatch(r"\w+\(s(\d+), s(\d+)\) \[.+, [<>]\] = \w+\(.+?\) = "
                      r"(.+)", rest)
    if m2:
        return k, "comparative", (int(m2.group(1)), int(m2.group(2))), \
            m2.group(3)
    m2 = re.fullmatch(r"s(\d+) \* \S+(?: \+ \S+)? \[.+ -> SI(?:, \w+)?\] = "
                      r"\(.+\) \* \S+(?: \+ \S+)? = (.+)", rest)
    if m2:
        return k, "si", (int(m2.group(1)),), m2.group(2)
    m2 = re.fullmatch(r"const\[\w+\] = (.+)", rest)
    if m2:
        return k, "constant", (), m2.group(1)
    m2 = re.fullmatch(r"s(\d+) / \S+ \[SI -> .+\] = \(.+\) / \S+ = (.+)",
                      rest)
    if m2:
        return k, "unit_out", (int(m2.group(1)),), m2.group(2)
    m2 = re.fullmatch(r"(?:odd|even)\?\(s(\d+)\) = (?:odd|even)\?\(.+?\) = "
                      r"(True|False)(?:; .+)?", rest)
    if m2:
        return k, "parity", (int(m2.group(1)),), m2.group(2)
    m2 = re.fullmatch(r"mean\(((?:s\d+)(?:, s\d+)+)\) = \(.+\) / \d+ = (.+)",
                      rest)
    if m2:
        ins = tuple(int(x) for x in re.findall(r"s(\d+)", m2.group(1)))
        return k, "mean", ins, m2.group(2)
    m2 = re.fullmatch(r".+ = (-?\d+(?:/\d+)?) in .+ \(given\)", rest)
    if m2:
        return k, "measured", (), m2.group(1)
    m2 = re.fullmatch(r"s(\d+) ([-+*/]) s(\d+) = \(.+\) [-+*/] \(.+\) = "
                      r"(.+)", rest)
    if m2:
        op = {v: k2 for k2, v in ARITH.items()}[m2.group(2)]
        return k, op, (int(m2.group(1)), int(m2.group(3))), m2.group(4)
    m2 = re.fullmatch(r"s(\d+) \^ -?\d+ = \(.+\) \^ -?\d+ = (.+)", rest)
    if m2:
        return k, "pow", (int(m2.group(1)),), m2.group(2)
    m2 = re.fullmatch(r"(gcd|lcm)\(s(\d+), s(\d+)\) = \w+\(.+\) = (.+)",
                      rest)
    if m2:
        return k, m2.group(1), (int(m2.group(2)), int(m2.group(3))), \
            m2.group(4)
    m2 = re.fullmatch(r"prime\?\(s(\d+)\) = prime\?\(.+?\) = (prime|not "
                      r"prime)(?:; .+)?", rest)
    if m2:
        return k, "prime", (int(m2.group(1)),), m2.group(2)
    m2 = re.fullmatch(r"\[s(\d+) \S+ s(\d+)\] = \[.+\] = (True|False)", rest)
    if m2:
        return k, "compare", (int(m2.group(1)), int(m2.group(2))), \
            m2.group(3)
    m2 = re.fullmatch(r"arg(?:max|min)\(s(\d+), s(\d+)\) = arg(?:max|min)"
                      r"\(.+?\) = (.+)", rest)
    if m2:
        return k, "larger", (int(m2.group(1)), int(m2.group(2))), \
            m2.group(3)
    m2 = re.fullmatch(r".+ \[(.*)\] = (.+?)   \[[WC]\d+: .+\]", rest)
    if m2:
        ins = tuple(int(x) for x in re.findall(r"=s(\d+)", m2.group(1)))
        return k, "axiom", ins, m2.group(2)
    m2 = re.fullmatch(r".+ = (.+) \(given\)", rest)
    if m2:
        return k, "given", (), m2.group(1)
    m2 = re.fullmatch(r"plan\[.+\] = (.+)", rest)
    if m2:
        return k, "planned", (), m2.group(1)
    m2 = re.fullmatch(r"\w+\[.+\]\.\w+ = (.+)", rest)
    if m2:
        return k, "lookup", (), m2.group(1)
    if re.fullmatch(r"-?\d+(?:/\d+)?", rest):
        return k, "literal", (), rest
    return None


# ===========================================================================
# 4.  RECOMPUTATION AND THE STEP GATE (in-process)
# ===========================================================================

def _gcd(a: int, b: int) -> int:
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def recompute(s: Step, steps: Sequence[Step]) -> object:
    """The value of a computed step from its inputs, exactly; ``None`` for a
    step whose value is read rather than computed (literal, lookup, planned,
    given)."""
    vals = [steps[j - 1].value for j in s.inputs]
    if s.op in ARITH:
        a, b = vals
        if s.op == "add":
            return a + b
        if s.op == "sub":
            return a - b
        if s.op == "mul":
            return a * b
        return a / b
    if s.op == "pow":
        return vals[0] ** int(s.detail["exponent"])
    if s.op == "si":
        return vals[0] * Fraction(s.detail["factor"]) + Fraction(
            s.detail.get("offset", "0"))
    if s.op == "constant":
        from ..runtime.measurands import DEFINED_CONSTANTS
        got = DEFINED_CONSTANTS.get(s.detail.get("name"))
        return got[0] if got else None
    if s.op == "unit_out":
        return vals[0] / Fraction(s.detail["factor"])
    if s.op == "parity":
        n = int(vals[0])
        return str((n % 2 == 1) == (s.detail["asked"] == "odd"))
    if s.op == "mean":
        return sum(vals, Fraction(0)) / len(vals)
    if s.op in ("gcd", "lcm"):
        a, b = int(vals[0]), int(vals[1])
        g = _gcd(a, b)
        return Fraction(g if s.op == "gcd" else (abs(a * b) // g if g else 0))
    if s.op == "prime":
        n = int(vals[0])
        return "prime" if n >= 2 and prime_factor(n) is None else "not prime"
    if s.op == "compare":
        a, b = vals
        return str({">": a > b, "<": a < b, "=": a == b}[s.detail["symbol"]])
    if s.op == "comparative":
        a, b = vals
        ra, rb = s.detail["rows"]
        if a == b:
            return "equal"
        return ra if (a > b) == (s.detail["symbol"] == ">") else rb
    if s.op == "fold":
        d = s.detail
        fn = d["fn"]
        if fn in ORDER_FOLDS or d.get("present") or d.get("bounded"):
            x = None
            if fn == "rank":
                x = next((steps[j - 1].value for j in s.inputs
                          if steps[j - 1].detail.get("row") == d["row"]),
                         None)
            holes = len(d.get("missing", ())) if d.get("bounded") else 0
            return fold_value(fn, vals, holes, x)
        if fn == "sum":
            return sum(vals, Fraction(0))
        if fn == "mean":
            return sum(vals, Fraction(0)) / len(vals)
        want = 1 if fn == "odd" else 0
        return Fraction(sum(1 for v in vals if int(v) % 2 == want))
    if s.op == "larger":
        a, b = vals
        la, lb = steps[s.inputs[0] - 1].label, steps[s.inputs[1] - 1].label
        if a == b:
            return "equal"
        want_a = (a > b) == (s.detail["relation"] == "larger")
        return la if want_a else lb
    if s.op == "axiom":
        env = {name: steps[j - 1].value for name, j in s.detail["names"]}
        env[s.detail["solved_for"]] = s.value
        lhs, rhs = s.detail["sides"]
        return s.value if _side(lhs, env) == _side(rhs, env) else None
    return None


def _side(side, env) -> Fraction:
    """``coefficient * prod(name ** power)`` of one side of an axiom."""
    coef, powers = side
    out = Fraction(coef)
    for name, e in powers:
        out *= Fraction(env[name]) ** int(e)
    return out


def step_check(s: Step, steps: Sequence[Step]) -> Tuple[bool, str]:
    """The step gate: both columns read back to this step, the inputs are
    earlier steps, and a computed value recomputes."""
    if s.index < 1 or s.index > len(steps) or steps[s.index - 1] is not s \
            and steps[s.index - 1] != s:
        return False, "index out of place"
    if any(j < 1 or j >= s.index for j in s.inputs):
        return False, "an input is not an earlier step"
    want = (s.index, s.op, tuple(s.inputs), render_value(s.value))
    r1 = read_sentence(sentence(s))
    if r1 != want:
        return False, f"column 1 reads back as {r1}, not {want}"
    r2 = read_equation(equation(s, steps))
    if r2 != want:
        return False, f"column 2 reads back as {r2}, not {want}"
    got = recompute(s, steps)
    if s.op in ("literal", "lookup", "planned", "given", "measured"):
        return True, "read, not computed"
    if got is None or render_value(got) != render_value(s.value):
        return False, f"recomputes as {got}, not {render_value(s.value)}"
    return True, "aligned and recomputed"


def chain_check(chain: Chain) -> Tuple[bool, List[str]]:
    """Every step through the gate, in order."""
    notes = []
    for s in chain.steps:
        ok, why = step_check(s, chain.steps)
        notes.append(f"step {s.index}: {why}")
        if not ok:
            return False, notes
    return True, notes


# ===========================================================================
# 5.  COLUMN 3 -- THE CHAIN'S SCRIPT
# ===========================================================================

def chain_data(chain: Chain) -> Dict[str, object]:
    """What the script is given: the question, every step's record and both
    of its columns, and the answer sentence."""
    return {
        "question": chain.question, "kind": chain.kind,
        "steps": [dict(s.as_dict(), column1=sentence(s),
                       column2=equation(s, chain.steps))
                  for s in chain.steps],
        "answer": answer_sentence(chain),
    }


_SCRIPT = r'''"""Column 3 of a stepwise planner answer -- generated.

For every step: read column 1 and column 2 back with this script's own
readers, require both to name the recorded operation, inputs and value
(ALIGNED), and recompute the value with this script's own exact arithmetic --
re-reading the register for a looked-up step, re-parsing the question for a
given, substituting into the wheel's declared axiom for an axiom step.  Then
the links and the answer sentence.  Prints VERIFIED True only if all hold.
"""
import json
import re
import sys
from fractions import Fraction

sys.path.insert(0, @@ROOT@@)

DATA = json.loads(@@DATA@@)
VAL = r"(-?\d+(?:/\d+)?|prime|not prime|True|False|.+?)"


def num(s):
    return Fraction(s.strip())


def show(v):
    if isinstance(v, Fraction):
        return str(v.numerator) if v.denominator == 1 else "%d/%d" % (
            v.numerator, v.denominator)
    return str(v)


def read1(t):
    pats = [
        (r"Step (\d+): the number " + VAL + r"\.", "literal", 0),
        (r"Step (\d+): .+ is " + VAL + r", a defined constant of the SI\.",
         "constant", 0),
        (r"Step (\d+): .+ is " + VAL + r", held by the .+ table as .+\.",
         "lookup", 0),
        (r"Step (\d+): .+ is " + VAL + r", computed by the planner's .+ "
         r"plan\.", "planned", 0),
        (r"Step (\d+): .+ is given as (-?\d+(?:/\d+)?), in .+\.", "measured",
         0),
        (r"Step (\d+): .+ is given as " + VAL + r"\.", "given", 0),
        (r"Step (\d+): step (\d+), carried into SI units, is " + VAL + r"\.",
         "si", 1),
        (r"Step (\d+): step (\d+), stated in .+, is " + VAL + r"\.",
         "unit_out", 1),
        (r"Step (\d+): that step (\d+) is (?:odd|even) is (True|False)\.",
         "parity", 1),
        (r"Step (\d+): adding step (\d+) and step (\d+) gives " + VAL +
         r"\.", "add", 2),
        (r"Step (\d+): subtracting step (\d+) from step (\d+) gives " + VAL +
         r"\.", "sub", -2),
        (r"Step (\d+): multiplying step (\d+) by step (\d+) gives " + VAL +
         r"\.", "mul", 2),
        (r"Step (\d+): dividing step (\d+) by step (\d+) gives " + VAL +
         r"\.", "div", 2),
        (r"Step (\d+): raising step (\d+) to the power -?\d+ gives " + VAL +
         r"\.", "pow", 1),
        (r"Step (\d+): the greatest common divisor of step (\d+) and step "
         r"(\d+) is " + VAL + r"\.", "gcd", 2),
        (r"Step (\d+): the least common multiple of step (\d+) and step "
         r"(\d+) is " + VAL + r"\.", "lcm", 2),
        (r"Step (\d+): that step (\d+) is \w+ than step (\d+) is " + VAL +
         r"\.", "compare", 2),
        (r"Step (\d+): the (?:larger|smaller) of step (\d+) and step (\d+) "
         r"is " + VAL + r"\.", "larger", 2),
        (r"Step (\d+): step (\d+) is " + VAL + r"\.", "prime", 1),
    ]
    m = re.fullmatch(r"Step (\d+): the (?:sum|mean|count of odd values|count "
                     r"of even values|median|largest value|smallest value|"
                     r"rank of \S+ \(largest first\)) of \S+ over the .+, "
                     r"from ((?:step \d+)"
                     r"(?:(?:, | and )step \d+)*), is " + VAL + r"\.", t)
    if m:
        return [int(m.group(1)), "fold",
                [int(x) for x in re.findall(r"step (\d+)", m.group(2))],
                m.group(3)]
    m = re.fullmatch(r"Step (\d+): of .+ and .+, the \w+ by step (\d+) and "
                     r"step (\d+) is " + VAL + r"\.", t)
    if m:
        return [int(m.group(1)), "comparative",
                [int(m.group(2)), int(m.group(3))], m.group(4)]
    m = re.fullmatch(r"Step (\d+): the mean of ((?:step \d+)(?:(?:, | and )"
                     r"step \d+)+) is " + VAL + r"\.", t)
    if m:
        return [int(m.group(1)), "mean",
                [int(x) for x in re.findall(r"step (\d+)", m.group(2))],
                m.group(3)]
    for pat, op, n in pats:
        m = re.fullmatch(pat, t)
        if m:
            g = m.groups()
            ins = [int(x) for x in g[1:1 + abs(n)]]
            if n < 0:
                ins.reverse()
            return [int(g[0]), op, ins, g[1 + abs(n)]]
    m = re.fullmatch(r"Step (\d+): .+ is " + VAL + r", by .+ in ([WC]\d+), "
                     r"from ((?:step \d+(?: and )?)+)\.", t)
    if m:
        return [int(m.group(1)), "axiom",
                [int(x) for x in re.findall(r"step (\d+)", m.group(4))],
                m.group(2)]
    return None


def read2(t):
    m = re.fullmatch(r"s(\d+) = (.+)", t)
    if not m:
        return None
    k, rest = int(m.group(1)), m.group(2)
    m2 = re.fullmatch(r"(?:sum|mean|odd|even|median|max|min|rank)\[[^\]]+\]"
                      r"\(((?:s\d+)(?:, s\d+)*)\) = (.+)", rest)
    if m2:
        return [k, "fold", [int(x) for x in re.findall(r"s(\d+)",
                                                       m2.group(1))],
                m2.group(2)]
    m2 = re.fullmatch(r"\w+\(s(\d+), s(\d+)\) \[.+, [<>]\] = \w+\(.+?\) = "
                      r"(.+)", rest)
    if m2:
        return [k, "comparative", [int(m2.group(1)), int(m2.group(2))],
                m2.group(3)]
    tries = [
        (r"s(\d+) \* \S+(?: \+ \S+)? \[.+ -> SI(?:, \w+)?\] = \(.+\) \* "
         r"\S+(?: \+ \S+)? = (.+)", "si"),
        (r"const\[\w+\] = (.+)", "constant"),
        (r"s(\d+) / \S+ \[SI -> .+\] = \(.+\) / \S+ = (.+)", "unit_out"),
        (r"(?:odd|even)\?\(s(\d+)\) = (?:odd|even)\?\(.+?\) = (True|False)"
         r"(?:; .+)?", "parity"),
        (r"mean\(((?:s\d+)(?:, s\d+)+)\) = \(.+\) / \d+ = (.+)", "mean"),
        (r".+ = (-?\d+(?:/\d+)?) in .+ \(given\)", "measured"),
        (r"s(\d+) ([-+*/]) s(\d+) = \(.+\) [-+*/] \(.+\) = (.+)", "arith"),
        (r"s(\d+) \^ -?\d+ = \(.+\) \^ -?\d+ = (.+)", "pow"),
        (r"(gcd|lcm)\(s(\d+), s(\d+)\) = \w+\(.+\) = (.+)", "gl"),
        (r"prime\?\(s(\d+)\) = prime\?\(.+?\) = (prime|not prime)"
         r"(?:; .+)?", "prime"),
        (r"\[s(\d+) \S+ s(\d+)\] = \[.+\] = (True|False)", "compare"),
        (r"arg(?:max|min)\(s(\d+), s(\d+)\) = arg(?:max|min)\(.+?\) = (.+)",
         "larger"),
        (r".+ \[(.*)\] = (.+?)   \[[WC]\d+: .+\]", "axiom"),
        (r".+ = (.+) \(given\)", "given"),
        (r"plan\[.+\] = (.+)", "planned"),
        (r"\w+\[.+\]\.\w+ = (.+)", "lookup"),
        (r"(-?\d+(?:/\d+)?)", "literal"),
    ]
    for pat, what in tries:
        m2 = re.fullmatch(pat, rest)
        if not m2:
            continue
        g = m2.groups()
        if what == "arith":
            op = {"+": "add", "-": "sub", "*": "mul", "/": "div"}[g[1]]
            return [k, op, [int(g[0]), int(g[2])], g[3]]
        if what in ("pow", "si", "unit_out", "parity"):
            return [k, what, [int(g[0])], g[1]]
        if what == "mean":
            return [k, "mean", [int(x) for x in re.findall(r"s(\d+)", g[0])],
                    g[1]]
        if what == "gl":
            return [k, g[0], [int(g[1]), int(g[2])], g[3]]
        if what == "prime":
            return [k, "prime", [int(g[0])], g[1]]
        if what in ("compare", "larger"):
            return [k, what, [int(g[0]), int(g[1])], g[2]]
        if what == "axiom":
            return [k, "axiom", [int(x) for x in re.findall(r"=s(\d+)",
                                                            g[0])], g[1]]
        return [k, what, [], g[0]]
    return None


def least_factor(n):
    if n < 4:
        return None
    f = 2
    while f * f <= n:
        if n % f == 0:
            return f
        f += 1
    return None


def gcd(a, b):
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def as_int(v):
    assert isinstance(v, Fraction) and v.denominator == 1, "not an integer"
    return v.numerator


def givens(question):
    """name -> (amount as written, unit phrase or ""), re-read from the
    question itself, item by item."""
    body = re.split(r",? (?:what is|what's|find|compute|calculate|"
                    r"determine) ", question.lower().strip().rstrip("?!. "),
                    maxsplit=1)[0]
    body = re.sub(r"^(?:given|if|suppose|let) ", "", body)
    out = {}
    for item in re.split(r",\s*(?:and\s+)?|\s+and\s+", body):
        m = re.fullmatch(r"(?:the )?([a-z][a-z ]*?)\s*=\s*(-?\d+(?:/\d+)?"
                         r"(?:\.\d+)?)(?: ([a-z][a-z ]*))?", item.strip())
        if m:
            out[m.group(1).strip().replace(" ", "_")] = (
                num(m.group(2)), (m.group(3) or "").strip())
    return out


def asked_units(question):
    """The unit phrases the question asks its targets in."""
    rest = re.split(r",? (?:what is|what's|find|compute|calculate|"
                    r"determine) ", question.lower().strip().rstrip("?!. "),
                    maxsplit=1)
    return re.findall(r" in ([a-z][a-z ]*?)(?=,| then |$)",
                      rest[1]) if len(rest) > 1 else []


def unit_factor(kind, source, quantity):
    """The exact SI factor of a unit phrase or a register scale, from the
    declared tables, with the dimension checked against the quantity."""
    from glm_universal.runtime import quantity_units as qu
    if kind == "unit":
        read = qu.read_unit(source)
        factor, dim = read.factor, read.dimension
    elif kind == "measurand":
        from glm_universal.runtime import measurand_register as mreg
        from glm_universal.reasoning.units import parse_unit
        row = mreg.measurand_of(source)
        assert row is not None and row.factor is not None, \
            "not a declared measurand reading"
        factor = row.factor
        dim = tuple(parse_unit(row.symbol, steradian=False)[:7])
    else:
        factor, dim, _q = qu.scale_into_si(source)
    assert tuple(dim) == qu.quantity_dimension(quantity), \
        "the unit is not of the quantity's dimension"
    return factor


SESSION = []


def register(table, row, field):
    if not SESSION:
        from glm_universal.runtime.session import GeometricSession
        SESSION.append(GeometricSession())
    v = SESSION[0].field_surface.field(field, row)
    assert v.table == table, "the register holds it in another table"
    return Fraction(v.value)


def session_surface():
    if not SESSION:
        from glm_universal.runtime.session import GeometricSession
        SESSION.append(GeometricSession())
    return SESSION[0].field_surface


def declared_comparative(word, symbol):
    """The declared table's reading of a comparative word, checked against
    the recorded direction."""
    from glm_universal.runtime import declared_frames as df
    assert word in df.COMPARATIVES, "not a declared comparative"
    phrase, sym, _gloss = df.COMPARATIVES[word]
    assert sym == symbol, "the recorded direction is not the declared one"
    return phrase


def input_of_row(step_no, phrase, row_name):
    """An input step is the declared column of the row the question names."""
    src = DATA["steps"][step_no - 1]
    assert src["op"] == "lookup", "a comparative input that is not looked up"
    assert src["label"] == "the %s of %s" % (phrase, row_name), \
        "the input is not the declared column of the row named"
    held = session_surface().field(src["detail"]["field"], row_name)
    assert held.row == src["detail"]["row"], \
        "the row named is not the row looked up"


def side(s, env):
    coef, powers = s
    out = num(coef)
    for name, e in powers:
        out *= env[name] ** int(e)
    return out


def between(lo, hi):
    return lo if lo == hi else "between %s and %s" % (show(lo), show(hi))


def order_fold(fn, v, holes, x):
    """This script's own fold over the present readings with ``holes``
    missing: the k-th smallest of the completed column lies between the
    (k - holes)-th and the k-th smallest present reading; a rank between
    the present rank and that plus ``holes``."""
    if fn in ("sum", "mean", "odd", "even"):
        assert holes == 0, "a sum, mean or count has no bound under a hole"
        total = Fraction(0)
        for y in v:
            total += y
        if fn == "sum":
            return total
        if fn == "mean":
            assert v, "a mean over no rows"
            return total / len(v)
        parity = 1 if fn == "odd" else 0
        return Fraction(sum(1 for y in v if as_int(y) % 2 == parity))
    if fn == "rank":
        above = 0
        for y in v:
            if y > x:
                above += 1
        return between(Fraction(1 + above), Fraction(1 + above + holes))
    assert v, "an order fold over no rows"
    p = sorted(v)
    if fn in ("max", "min"):
        assert holes == 0, "an end of a column with a hole is unbounded"
        return p[-1] if fn == "max" else p[0]
    n = len(p) + holes
    mids = [n // 2] if n % 2 == 1 else [n // 2 - 1, n // 2]
    for k in mids:
        assert k - holes >= 0 and k < len(p), "a side left open by the holes"
    lo = Fraction(0)
    hi = Fraction(0)
    for k in mids:
        lo += p[k - holes]
        hi += p[k]
    return between(lo / len(mids), hi / len(mids))


def value_of(step, done):
    op, d = step["op"], step["detail"]
    v = [done[j] for j in step["inputs"]]
    if op == "literal":
        return num(step["value"])
    if op == "lookup":
        return register(d["table"], d["row"], d["field"])
    if op == "planned":
        r = d.get("recompute")
        assert r, "a planned step with nothing to recompute"
        if r[0] == "convert":
            return num(r[1]) * num(r[2]) / num(r[3])
        a, b = num(r[2]), num(r[3])
        return {"+": a + b, "-": a - b, "*": a * b,
                "/": a / b if b else None}[r[1]]
    if op == "given":
        amount, unit = givens(DATA["question"])[d["name"]]
        assert unit == "", "the question states a unit for this given"
        return amount
    if op == "measured":
        amount, unit = givens(DATA["question"])[d["name"]]
        assert unit == d["unit"], "the question states another unit"
        return amount
    if op == "constant":
        from glm_universal.runtime.measurands import DEFINED_CONSTANTS
        assert d["name"] in DEFINED_CONSTANTS, "not a defined constant"
        return DEFINED_CONSTANTS[d["name"]][0]
    if op == "si" and "offset" in d:
        from glm_universal.runtime import measurands as ms
        src = DATA["steps"][step["inputs"][0] - 1]
        assert src["detail"].get("unit") == d["from"], \
            "the conversion is not of the given's unit"
        assert d["quantity"] == ms.TEMPERATURE, "an offset on a non-temperature"
        want = "difference" if ms.difference_name(src["detail"]["name"]) \
            else "level"
        assert d["reading"] == want, "the reading is not the name's kind"
        f, o, _src = ms.offset_reading(d["from"], d["reading"])
        assert show(f) == d["factor"] and show(o) == d["offset"], \
            "the recorded conversion is not the table's"
        return v[0] * f + o
    if op == "si":
        f = unit_factor(d["kind"], d["from"], d["quantity"])
        assert show(f) == d["factor"], "the recorded factor is not the table's"
        src = DATA["steps"][step["inputs"][0] - 1]
        if d["kind"] == "unit":
            assert src["detail"].get("unit") == d["from"], \
                "the conversion is not of the given's unit"
        else:
            assert src["op"] == "lookup" and "%s:%s" % (
                src["detail"]["table"], src["detail"]["field"]) == d["from"], \
                "the conversion is not of the register entry's scale"
        return v[0] * f
    if op == "unit_out":
        assert d["unit"] in asked_units(DATA["question"]), \
            "the question does not ask for this unit"
        f = unit_factor("unit", d["unit"], d["quantity"])
        assert show(f) == d["factor"], "the recorded factor is not the table's"
        return v[0] / f
    if op == "parity":
        n = as_int(v[0])
        return str((n % 2 == 1) == (d["asked"] == "odd"))
    if op == "mean":
        assert len(v) >= 2, "a mean of fewer than two items"
        total = Fraction(0)
        for x in v:
            total += x
        return total / len(v)
    if op == "add":
        return v[0] + v[1]
    if op == "sub":
        return v[0] - v[1]
    if op == "mul":
        return v[0] * v[1]
    if op == "div":
        assert v[1] != 0, "division by zero"
        return v[0] / v[1]
    if op == "pow":
        return v[0] ** int(d["exponent"])
    if op == "gcd":
        return Fraction(gcd(as_int(v[0]), as_int(v[1])))
    if op == "lcm":
        a, b = as_int(v[0]), as_int(v[1])
        return Fraction(abs(a * b) // gcd(a, b))
    if op == "prime":
        n = as_int(v[0])
        f = least_factor(n)
        if n >= 2 and f is None:
            return "prime"
        if "factor" in d:
            assert int(d["factor"]) == f or n % int(d["factor"]) == 0
        return "not prime"
    if op == "compare":
        from glm_universal.runtime import declared_frames as df
        if d["relation"] in df.COMPARATIVES:
            declared_comparative(d["relation"], d["symbol"])
        return str({">": v[0] > v[1], "<": v[0] < v[1],
                    "=": v[0] == v[1]}[d["symbol"]])
    if op == "comparative":
        phrase = declared_comparative(d["word"], d["symbol"])
        assert phrase == d["phrase"], "the recorded column is not declared"
        for j, row_name in zip(step["inputs"], d["rows"]):
            input_of_row(j, phrase, row_name)
        if v[0] == v[1]:
            return "equal"
        first = (v[0] > v[1]) == (d["symbol"] == ">")
        return d["rows"][0] if first else d["rows"][1]
    if op == "fold":
        from glm_universal.runtime import declared_frames as df
        want = df.DECLARED_SETS[d["set"]]
        held = session_surface().table_by_name(d["table"]).rows()
        rows = [k for k, r in held.items()
                if want is None or r.get("group_block") == want]
        holes = [k for k in rows if held[k].get(d["field"]) is None]
        if d.get("present") or d.get("bounded"):
            assert list(d["missing"]) == holes, \
                "the recorded missing rows are not the register's"
            assert d.get("present") or holes, "a bounded fold with no hole"
            rows = [k for k in rows if k not in holes]
        srcs = [DATA["steps"][j - 1] for j in step["inputs"]]
        assert all(x["op"] == "lookup" and x["detail"]["field"] == d["field"]
                   and x["detail"]["table"] == d["table"] for x in srcs), \
            "a fold input that is not the column looked up"
        assert [x["detail"]["row"] for x in srcs] == rows, \
            "the inputs are not exactly the members of the set"
        if d["fn"] in ("median", "max", "min", "rank") or d.get("present"):
            x = None
            if d["fn"] == "rank":
                assert d["row"] in rows, "the ranked row is not a present member"
                x = v[[s["detail"]["row"] for s in srcs].index(d["row"])]
            return order_fold(d["fn"], v,
                              len(holes) if d.get("bounded") else 0, x)
        total = Fraction(0)
        for x in v:
            total += x
        if d["fn"] == "sum":
            return total
        if d["fn"] == "mean":
            return total / len(v)
        parity = 1 if d["fn"] == "odd" else 0
        return Fraction(sum(1 for x in v if as_int(x) % 2 == parity))
    if op == "larger":
        if v[0] == v[1]:
            return "equal"
        labels = [DATA["steps"][j - 1]["label"] for j in step["inputs"]]
        first = (v[0] > v[1]) == (d["relation"] == "larger")
        return labels[0] if first else labels[1]
    if op == "axiom":
        from glm_universal.engineering import wheels
        from glm_universal.runtime import measurand_register as mreg
        found = [w for w in wheels.WHEELS if w.id == d["wheel"]]
        wheel = found[0] if found else mreg.law_of_id(d["wheel"])
        assert wheel is not None, "neither a wheel nor a declared law"
        assert d["axiom"] in wheel.axioms, "not an axiom of the wheel"
        lhs, rhs = wheels.parse_equation(d["axiom"])
        mine = [[show(lhs.coefficient), [[n, show(e)] for n, e in
                                          lhs.powers]],
                [show(rhs.coefficient), [[n, show(e)] for n, e in
                                          rhs.powers]]]
        assert mine == d["sides"], "the recorded sides are not the axiom's"
        env = {name: done[j] for name, j in d["names"]}
        env[d["solved_for"]] = num(step["value"])
        assert side(d["sides"][0], env) == side(d["sides"][1], env), \
            "the axiom does not hold at these values"
        return num(step["value"])
    raise AssertionError("unknown op " + op)


ok = True
done = {}
for pos, step in enumerate(DATA["steps"], 1):
    want = [step["index"], step["op"], step["inputs"], step["value"]]
    try:
        assert step["index"] == pos, "step out of place"
        assert all(1 <= j < pos for j in step["inputs"]), \
            "an input is not an earlier step"
        assert read1(step["column1"]) == want, "column 1 does not read back"
        assert read2(step["column2"]) == want, "column 2 does not read back"
        got = value_of(step, done)
        assert show(got) == step["value"], "recomputed %s, claimed %s" % (
            show(got), step["value"])
        done[pos] = got
        print("STEP %d ALIGNED True" % pos)
    except Exception as exc:
        print("STEP %d ALIGNED False: %s" % (pos, exc))
        ok = False
        break
if ok:
    last = DATA["steps"][-1]["value"] if DATA["steps"] else "none"
    if DATA["answer"] != "Answer: %s." % last:
        print("ANSWER does not match the last step")
        ok = False
print("ALIGNED %d of %d" % (len(done), len(DATA["steps"])))
print("VERIFIED", ok)
'''


def render_script(chain: Chain, root: str,
                  data: Optional[Dict[str, object]] = None) -> str:
    """The chain's column-3 script; ``data`` overrides the chain's own
    record (the mutations use it)."""
    d = chain_data(chain) if data is None else data
    return (_SCRIPT.replace("@@ROOT@@", repr(root))
            .replace("@@DATA@@", repr(json.dumps(d, sort_keys=True))))


# ===========================================================================
# 6.  THE FOUR MUTATIONS OF MARK S5
# ===========================================================================

def _lie(v: object) -> object:
    if isinstance(v, Fraction):
        return v + 1
    flips = {"prime": "not prime", "not prime": "prime", "True": "False",
             "False": "True"}
    return flips.get(str(v), str(v) + " (altered)")


_READ_OPS = ("literal", "lookup", "planned", "given", "measured",
             "constant")


def _lied(chain: Chain, target: Step) -> Dict[str, object]:
    steps = list(chain.steps)
    lied = replace(target, value=_lie(target.value))
    new = [lied if s is target else s for s in steps]
    data = chain_data(chain)
    data["steps"][target.index - 1] = dict(
        lied.as_dict(), column1=sentence(lied), column2=equation(lied, new))
    return data


def mutants(chain: Chain) -> Dict[str, Dict[str, object]]:
    """``kind -> data`` for each declared mutation that applies to the
    chain.  Every one is consistent within itself where it can be, so only
    the script's recomputation, alignment or link check can reject it."""
    out: Dict[str, Dict[str, object]] = {}
    steps = list(chain.steps)
    if not steps:
        return out
    # value-lie: the last computed step (the first read step when nothing
    # is computed), re-rendered in both columns so they still agree.
    computed = [s for s in steps if s.op not in _READ_OPS]
    target = computed[-1] if computed else steps[0]
    out["value-lie"] = _lied(chain, target)
    # read-lie (beyond the four declared kinds): the first read step -- a
    # register entry, a planner computation or a given -- lied about.
    read = [s for s in steps if s.op in _READ_OPS and s.op != "literal"]
    if read:
        out["read-lie"] = _lied(chain, read[0])
    # column-1: the sentence alone says another value.
    data = chain_data(chain)
    s = data["steps"][-1]
    s["column1"] = sentence(replace(steps[-1], value=_lie(steps[-1].value)))
    out["column-1"] = data
    # reorder: the last step with an input moved in front of that input,
    # renumbered, so it reads a step that comes after it.
    dep = next((s for s in reversed(steps) if s.inputs), None)
    if dep is not None:
        j = dep.inputs[0]
        order = [x for x in steps if x is not dep]
        order.insert(j - 1, dep)
        renum = {x.index: n for n, x in enumerate(order, 1)}
        moved = [replace(x, index=renum[x.index],
                         inputs=tuple(renum[i] for i in x.inputs))
                 for x in order]
        c2 = Chain(chain.question, tuple(moved), chain.kind)
        out["reorder"] = chain_data(c2)
    # answer: the answer sentence alone altered.
    data = chain_data(chain)
    data["answer"] = f"Answer: {render_value(_lie(chain.answer))}."
    out["answer"] = data
    # unit-lie (round two): the first conversion step claims a factor ten
    # times the table's, its value and both columns re-rendered to agree.
    conv = next((s for s in steps if s.op in ("si", "unit_out")), None)
    if conv is not None:
        f = Fraction(conv.detail["factor"]) * 10
        base = steps[conv.inputs[0] - 1].value
        value = (base * f + Fraction(conv.detail.get("offset", "0"))
                 if conv.op == "si" else base / f)
        lied = replace(conv, value=value,
                       detail=dict(conv.detail, factor=render_value(f)))
        new = [lied if x is conv else x for x in steps]
        data = chain_data(chain)
        data["steps"][conv.index - 1] = dict(
            lied.as_dict(), column1=sentence(lied),
            column2=equation(lied, new))
        out["unit-lie"] = data
    # member-lie (round three): a fold short of its last member, its value
    # and both columns re-rendered to agree.
    fold = next((x for x in steps if x.op == "fold"), None)
    if fold is not None and len(fold.inputs) > 1:
        short = replace(fold, inputs=fold.inputs[:-1])
        short = replace(short, value=recompute(short, steps))
        new = [short if x is fold else x for x in steps]
        data = chain_data(chain)
        data["steps"][fold.index - 1] = dict(
            short.as_dict(), column1=sentence(short),
            column2=equation(short, new))
        out["member-lie"] = data
    # hole-lie (round four): a present-rows or bounded fold's recorded
    # missing rows short of one, its value and both columns re-rendered.
    hole = next((x for x in steps if x.op == "fold"
                 and (x.detail.get("present") or x.detail.get("bounded"))
                 and x.detail.get("missing")), None)
    if hole is not None:
        lied = replace(hole, detail=dict(
            hole.detail, missing=list(hole.detail["missing"])[:-1]))
        again = recompute(lied, steps)
        lied = replace(lied, value=again if again is not None else hole.value)
        new = [lied if x is hole else x for x in steps]
        data = chain_data(chain)
        data["steps"][hole.index - 1] = dict(
            lied.as_dict(), column1=sentence(lied),
            column2=equation(lied, new))
        out["hole-lie"] = data
    # word-lie (round three): a declared comparative's direction reversed,
    # its value and both columns re-rendered to agree.
    from ..runtime.declared_frames import COMPARATIVES
    word = next((x for x in steps if x.op == "comparative" or (
        x.op == "compare" and x.detail.get("relation") in COMPARATIVES)),
        None)
    if word is not None:
        flip = {">": "<", "<": ">"}[word.detail["symbol"]]
        lied = replace(word, detail=dict(word.detail, symbol=flip))
        lied = replace(lied, value=recompute(lied, steps))
        new = [lied if x is word else x for x in steps]
        data = chain_data(chain)
        data["steps"][word.index - 1] = dict(
            lied.as_dict(), column1=sentence(lied),
            column2=equation(lied, new))
        out["word-lie"] = data
    return out

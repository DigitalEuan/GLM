"""``glm_universal.runtime.stepwise`` -- the typed planner as the executive of
a chain of steps.

Why this module exists
----------------------
The typed planner (:mod:`glm_universal.runtime.semantic_plan`) answers one
question with one plan.  It holds the atomic number of iron and it decides
primality, yet *is the atomic number of iron prime?* is refused, because
that is two steps.  The same for a sum or ratio of register values, a gcd of
two looked-up numbers, and every engineering question whose givens are not
one axiom away from the target: *given voltage = 12 and resistance = 4, what
is the power?* needs the current first, and nobody asked for it.

This module makes the planner the executive of a **chain**
(``studies/STEPWISE_PLANNER_STUDY.md``, Phase 72):

* **Composition.**  A compound question is read at its operator words,
  function forms, predicates and ``then``; every bracketing is a *reading*;
  every part that is not a number is asked of the planner, one question at a
  time.  A reading is licensed when every step of it is, and the answer is
  given only when every licensed reading agrees -- the planner's own rule,
  lifted from plans to readings.
* **Goals and stitching.**  ``given A = x and B = y, what is T`` is read over
  the axioms of the ten formula wheels, split per wheel except across a
  declared junction.  Every derivation from the givens to the target is
  computed, searching backwards from the target through every axiom that
  contains it; the answer is given only when the givens are consistent and
  every derivation in every licensed reading agrees.  The smallest
  derivation is presented, and its steps that nobody asked for are marked
  *stitched*.
* **Narratives.**  ``given …, find A, then B``: a step that cannot be taken
  yet is deferred, later steps are taken first, deferred steps are retried
  after every step, and a step nothing reaches in one axiom step is stitched
  from the derivation search.
* **Follow-ups.**  ``then …`` extends the last chain with *it* bound to its
  answer; ``why?`` replays it.  A chain is kept under the SHA-256 of the
  conversation before it and compared verbatim before reuse.

Every step carries its own three columns
(:mod:`glm_universal.reasoning.stepwise_script`) and is admitted to a chain
only through the step gate; the chain's column-3 script re-checks every step
in a fresh interpreter.

Conservative: the router consults this module only when the planner (and the
grammar behind it) refused, so an answer the planner gave is never changed
(``GLM.StepwisePlanner.fallback_conservative``).  Exact and float-free.
"""

from __future__ import annotations

import itertools
import json
import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..evaluation.stepwise_cases import MAX_DERIVATIONS, MAX_OPERATORS
from ..integrity import sha256_hex
from ..reasoning import stepwise_script as ss
from ..reasoning.stepwise_script import Chain, Step

__all__ = ["StepAnswer", "Refused", "reads", "answer", "compose", "goal",
           "StepwiseConversation", "chain_solution", "stepwise_report",
           "PRECEDENCE"]


class Refused(Exception):
    """A reading, a step or a question declined, with a named reason."""

    def __init__(self, name: str, reason: str):
        super().__init__(f"{name}: {reason}")
        self.name = name
        self.reason = reason


#: When no reading is licensed, the refusal reported is the first of these
#: that some reading met: the most specific reason wins.
PRECEDENCE: Tuple[str, ...] = (
    "INCONSISTENT_GIVENS", "DERIVATIONS_DISAGREE", "DIVISION_BY_ZERO",
    "NOT_AN_INTEGER", "DIFFERENCE_REVERSED", "PRECISION_OVERLAP",
    "NOT_A_NUMBER", "TOO_MANY_READINGS", "UNKNOWN_QUANTITY", "NO_DERIVATION",
    "UNKNOWN_STEP",
)

#: Round two (Phase 73, ``studies/STEPWISE_TWO_STUDY.md``): the frames the
#: leaves lacked (*how many more*, parity, averages), givens with units, and
#: register values fed to the wheels.  Switched off only by the round's own
#: control, which measures what round one's reader does with the corpus.
ROUND_TWO = True


@dataclass
class StepAnswer:
    """The stepwise planner's verdict on one text."""

    text: str
    verdict: str                     # answered | ambiguous | refused | unread
    chain: Optional[Chain] = None
    refusal: str = ""
    reason: str = ""
    readings: Tuple[Tuple[str, str], ...] = ()
    trials: int = 0

    @property
    def answered(self) -> bool:
        return self.verdict == "answered"

    @property
    def value(self) -> str:
        return ss.render_value(self.chain.answer) if self.chain else ""

    def summary(self) -> str:
        if self.verdict == "answered":
            return f"{self.value}  [{len(self.chain.steps)} steps]"
        if self.verdict == "ambiguous":
            return f"refused: AMBIGUOUS: {self.reason}"
        return f"refused: {self.refusal}: {self.reason}"

    def as_dict(self) -> Dict[str, object]:
        return {"text": self.text, "verdict": self.verdict,
                "value": self.value, "refusal": self.refusal,
                "reason": self.reason, "readings": list(self.readings),
                "steps": [s.as_dict() for s in self.chain.steps]
                if self.chain else [],
                "column1": list(self.chain.column1()) if self.chain else [],
                "column2": list(self.chain.column2()) if self.chain else []}


def _refusal(text: str, failures: Sequence[Refused],
             trials: int = 0) -> StepAnswer:
    names = [f.name for f in failures]
    for name in PRECEDENCE:
        if name in names:
            f = failures[names.index(name)]
            return StepAnswer(text, "refused", refusal=name, reason=f.reason,
                              trials=trials)
    return StepAnswer(text, "refused", refusal="UNKNOWN_STEP",
                      reason="no reading", trials=trials)


# ===========================================================================
# 1.  THE CHAIN BUILDER -- every step through the gate
# ===========================================================================

class Builder:
    """Appends steps to a chain, each admitted only through the step gate."""

    def __init__(self, prefix: Sequence[Step] = ()):
        self.steps: List[Step] = list(prefix)

    def add(self, op: str, inputs: Sequence[int], value: object, label: str,
            detail: Optional[Mapping[str, object]] = None,
            origin: str = "asked") -> int:
        s = Step(len(self.steps) + 1, op, tuple(inputs), value, label,
                 dict(detail or {}), origin)
        self.steps.append(s)
        ok, why = ss.step_check(s, self.steps)
        if not ok:                                   # pragma: no cover
            self.steps.pop()
            raise Refused("UNKNOWN_STEP", f"step gate: {why}")
        return s.index

    def value(self, index: int) -> object:
        return self.steps[index - 1].value


# ===========================================================================
# 2.  COMPOSITION -- readings of a compound question
# ===========================================================================

_OPERATORS: Tuple[Tuple[str, str], ...] = (
    (" plus ", "add"), (" + ", "add"), (" minus ", "sub"), (" - ", "sub"),
    (" times ", "mul"), (" multiplied by ", "mul"), (" * ", "mul"),
    (" divided by ", "div"), (" / ", "div"),
)

_LARGER = {"larger": ">", "greater": ">", "bigger": ">", "higher": ">",
           "more": ">", "smaller": "<", "less": "<", "lower": "<",
           "fewer": "<"}

_REFERENTS = ("it", "that", "this", "the result", "the answer")

_LEADS = re.compile(r"^(?:what is|what's|whats|compute|calculate|find|"
                    r"evaluate|tell me)\s+")

_FUNCTIONS = {"gcd": "gcd", "greatest common divisor": "gcd",
              "highest common factor": "gcd", "hcf": "gcd", "lcm": "lcm",
              "least common multiple": "lcm", "lowest common multiple": "lcm",
              "sum": "add", "product": "mul"}


def _positions(span: str, needle: str) -> List[int]:
    out, start = [], 0
    while True:
        i = span.find(needle, start)
        if i < 0:
            return out
        out.append(i)
        start = i + 1


def _operator_splits(span: str) -> List[Tuple[int, str, str]]:
    """Every top-level operator occurrence: ``(position, needle, op)``."""
    out = []
    for needle, op in _OPERATORS:
        for i in _positions(span, needle):
            out.append((i, needle, op))
    return sorted(out)


def _strip_the(span: str) -> str:
    return re.sub(r"^the\s+", "", span.strip())


def _singular_phrase(words: str) -> Optional[str]:
    """``atomic numbers`` -> ``atomic number``; None when not plural."""
    parts = words.split()
    if not parts or not parts[-1].endswith("s") or len(parts[-1]) < 3:
        return None
    last = parts[-1]
    last = last[:-3] + "y" if last.endswith("ies") else last[:-1]
    return " ".join(parts[:-1] + [last])


def _split_list(rest: str) -> List[str]:
    items = re.split(r",\s*(?:and\s+)?|\s+and\s+", rest)
    return [x.strip() for x in items if x.strip()]


def expression_readings(span: str, depth: int = 0) -> List[tuple]:
    """Every reading of ``span`` as an expression tree.

    Trees: ``("num", q)``, ``("it",)``, ``("leaf", phrase)``,
    ``("bin", op, a, b)``, ``("pow", a, e)``, ``("fn", op, a, b)``.
    """
    span = span.strip()
    if depth > 12 or not span:
        return []
    out: List[tuple] = []
    from .semantic_plan import parse_number
    n = parse_number(span)
    if n is not None:
        return [("num", n)]
    if span in _REFERENTS:
        return [("it",)]
    ops = _operator_splits(span)
    if len(ops) > MAX_OPERATORS:
        raise Refused("TOO_MANY_READINGS",
                      f"{len(ops)} operator words; at most {MAX_OPERATORS} "
                      f"are bracketed every way")
    for i, needle, op in ops:
        left, right = span[:i], span[i + len(needle):]
        for a in expression_readings(left, depth + 1):
            for b in expression_readings(right, depth + 1):
                out.append(("bin", op, a, b))
    function = _function_readings(span, depth)
    out.extend(function)
    if not ops and not function:
        out.append(("leaf", span))
    return out


def _function_readings(span: str, depth: int) -> List[tuple]:
    out: List[tuple] = []
    s = _strip_the(span)
    fnames = "|".join(sorted(map(re.escape, _FUNCTIONS), key=len,
                             reverse=True))
    m = re.fullmatch(rf"({fnames}) of (.+)", s)
    if m:
        op = _FUNCTIONS[m.group(1)]
        rest = m.group(2)
        # the distributive plural: the sum of the atomic numbers of a and b
        mp = re.fullmatch(r"(?:the )?(.+?) of (.+)", rest)
        if mp:
            single = _singular_phrase(mp.group(1))
            items = _split_list(mp.group(2))
            if single and len(items) >= 2:
                leaves = [("leaf", f"the {single} of {x}") for x in items]
                tree = leaves[0]
                for leaf in leaves[1:]:
                    tree = ("fn" if op in ("gcd", "lcm") else "bin", op,
                            tree, leaf)
                out.append(tree)
        for i in _positions(rest, " and "):
            for a in expression_readings(rest[:i], depth + 1):
                for b in expression_readings(rest[i + 5:], depth + 1):
                    out.append(("fn" if op in ("gcd", "lcm") else "bin", op,
                                a, b))
    m = re.fullmatch(r"(?:average|mean|arithmetic mean) of (.+)", s)
    if m and ROUND_TWO:
        out.extend(_mean_readings(m.group(1), depth))
    m = re.fullmatch(r"difference between (.+)", s)
    if m:
        rest = m.group(1)
        for i in _positions(rest, " and "):
            for a in expression_readings(rest[:i], depth + 1):
                for b in expression_readings(rest[i + 5:], depth + 1):
                    out.append(("bin", "sub", a, b))
    m = re.fullmatch(r"(?:ratio|quotient) of (.+)", s)
    if m:
        rest = m.group(1)
        for i in _positions(rest, " to "):
            for a in expression_readings(rest[:i], depth + 1):
                for b in expression_readings(rest[i + 4:], depth + 1):
                    out.append(("bin", "div", a, b))
    m = re.fullmatch(r"(square|cube) of (.+)", s)
    if m:
        e = 2 if m.group(1) == "square" else 3
        out += [("pow", a, e) for a in expression_readings(m.group(2),
                                                           depth + 1)]
    m = re.fullmatch(r"(.+) (squared|cubed)", span)
    if m:
        e = 2 if m.group(2) == "squared" else 3
        out += [("pow", a, e) for a in expression_readings(m.group(1),
                                                           depth + 1)]
    m = re.fullmatch(r"(.+) to the power (?:of )?(-?\d+)", span)
    if m:
        out += [("pow", a, int(m.group(2)))
                for a in expression_readings(m.group(1), depth + 1)]
    m = re.fullmatch(r"twice (.+)", span)
    if m:
        out += [("bin", "mul", ("num", Fraction(2)), a)
                for a in expression_readings(m.group(1), depth + 1)]
    m = re.fullmatch(r"half (?:of )?(.+)", span)
    if m:
        out += [("bin", "div", a, ("num", Fraction(2)))
                for a in expression_readings(m.group(1), depth + 1)]
    return out


#: The comparative a reversed difference is reported with.
_OPPOSITE = {"more": "less", "larger": "smaller", "greater": "smaller",
             "bigger": "smaller", "higher": "lower", "lower": "higher",
             "smaller": "larger", "less": "more"}


def _mean_readings(rest: str, depth: int) -> List[tuple]:
    """*The average of A, B and C*, and the distributive plural *the average
    of the Xs of A, B and C*: one mean over every item (round two)."""
    mp = re.fullmatch(r"(?:the )?(.+?) of (.+)", rest)
    if mp:
        single = _singular_phrase(mp.group(1))
        items = _split_list(mp.group(2))
        if single and len(items) >= 2:
            return [("mean",) + tuple(("leaf", f"the {single} of {x}")
                                      for x in items)]
    items = _split_list(rest)
    if len(items) < 2:
        return []
    per = [expression_readings(x, depth + 1) for x in items]
    if any(not p for p in per):
        return []
    return [("mean",) + combo for combo in itertools.product(*per)][:64]


def _difference_readings(seg: str) -> Optional[List[tuple]]:
    """*How many more X does A have than B* and *how much larger (higher,
    lower …) is A than B* (round two); None when neither form reads."""
    from ..evaluation.stepwise_two_cases import COUNT_NOUNS
    m = re.fullmatch(r"how many more (\w+) does (.+) have than (.+)", seg)
    if m:
        noun = m.group(1)
        if noun not in COUNT_NOUNS:
            raise Refused("UNKNOWN_STEP",
                          f"no declared count noun {noun!r}: the frame counts "
                          f"{', '.join(sorted(COUNT_NOUNS))}")
        field = COUNT_NOUNS[noun]
        return [("more", "more", ("leaf", f"the {field} of {m.group(2)}"),
                 ("leaf", f"the {field} of {m.group(3)}"), noun)]
    m = re.fullmatch(r"how much (more|larger|greater|bigger|higher|lower|"
                     r"smaller|less) is (.+)", seg)
    if not m:
        return None
    way = "less" if m.group(1) in ("lower", "smaller", "less") else "more"
    body, out = m.group(2), []
    for i in _positions(body, " than "):
        for a in expression_readings(body[:i]):
            for b in expression_readings(body[i + 6:]):
                out.append(("more", way, a, b, m.group(1)))
    return out


def segment_readings(seg: str) -> List[tuple]:
    """Every reading of one ``then``-segment: a predicate, a verb form over
    *it*, or an expression."""
    seg = _LEADS.sub("", seg.strip())
    out: List[tuple] = []
    if ROUND_TWO:
        m = re.fullmatch(r"is (.+?) (?:an? )?(odd|even)(?: number)?", seg)
        if m:
            return [("parity", m.group(2), a)
                    for a in expression_readings(m.group(1))]
        diff = _difference_readings(seg)
        if diff is not None:
            return diff
    m = re.fullmatch(r"is (.+) (?:a )?prime(?: number)?", seg)
    if m:
        return [("prime", a) for a in expression_readings(m.group(1))]
    if seg.startswith("is "):
        body = seg[3:]
        for word, sym in _LARGER.items():
            needle = f" {word} than "
            for i in _positions(body, needle):
                rel = "larger" if sym == ">" else "smaller"
                for a in expression_readings(body[:i]):
                    for b in expression_readings(body[i + len(needle):]):
                        out.append(("cmp", sym, rel, a, b))
        if out:
            return out
    m = re.fullmatch(r"which is (?:the )?(\w+),? (.+)", seg)
    if m and m.group(1) in _LARGER:
        rel = "larger" if _LARGER[m.group(1)] == ">" else "smaller"
        rest = m.group(2)
        for i in _positions(rest, " or "):
            for a in expression_readings(rest[:i]):
                for b in expression_readings(rest[i + 4:]):
                    out.append(("larger", rel, a, b))
        return out
    verbs = (
        (r"divide (.+) by (.+)", lambda a, b: ("bin", "div", a, b)),
        (r"multiply (.+) by (.+)", lambda a, b: ("bin", "mul", a, b)),
        (r"add (.+) to (.+)", lambda a, b: ("bin", "add", b, a)),
        (r"subtract (.+) from (.+)", lambda a, b: ("bin", "sub", b, a)),
    )
    for pat, make in verbs:
        m = re.fullmatch(pat, seg)
        if m:
            for a in expression_readings(m.group(1)):
                for b in expression_readings(m.group(2)):
                    out.append(make(a, b))
            return out
    m = re.fullmatch(r"(square|cube|double|halve|negate) (.+)", seg)
    if m:
        verb = m.group(1)
        for a in expression_readings(m.group(2)):
            if verb in ("square", "cube"):
                out.append(("pow", a, 2 if verb == "square" else 3))
            elif verb == "double":
                out.append(("bin", "mul", a, ("num", Fraction(2))))
            elif verb == "halve":
                out.append(("bin", "div", a, ("num", Fraction(2))))
            else:
                out.append(("bin", "sub", ("num", Fraction(0)), a))
        return out
    return expression_readings(seg)


def _has_structure(tree: tuple) -> bool:
    """Whether a reading does more than ask the planner one question."""
    return tree[0] not in ("leaf", "num", "it")


def _uses_it(tree: tuple) -> bool:
    if tree[0] == "it":
        return True
    return any(_uses_it(t) for t in tree[1:] if isinstance(t, tuple))


def split_then(text: str) -> List[str]:
    """A question's ``then``-segments."""
    from .semantic_plan import clean
    t = clean(text)
    return [s.strip() for s in re.split(r",?\s*(?:and\s+)?then\s+", t)
            if s.strip()]


# ---------------------------------------------------------------------------
# asking the planner for one part
# ---------------------------------------------------------------------------

class Leaves:
    """The planner's answers to the parts, asked once each."""

    def __init__(self, session):
        self.session = session
        self.cache: Dict[str, object] = {}
        self.trials = 0

    def question(self, phrase: str) -> str:
        if re.match(r"(?:convert|how|what|which|is)\b", phrase):
            return phrase
        return f"what is {phrase}"

    def get(self, phrase: str):
        """``(op, value, detail)`` for a part, or raises :class:`Refused`."""
        if phrase in self.cache:
            got = self.cache[phrase]
            if isinstance(got, Refused):
                raise got
            return got
        try:
            got = self._ask(phrase)
        except Refused as r:
            self.cache[phrase] = r
            raise
        self.cache[phrase] = got
        return got

    def _ask(self, phrase: str):
        from . import semantic_plan as sp
        q = self.question(phrase)
        self.trials += 1
        planned = sp.plan_question(self.session, q)
        if planned.verdict != "answered" or planned.chosen is None:
            why = planned.reason or "no frame read it"
            raise Refused("UNKNOWN_STEP",
                          f"the planner does not answer {q!r} ({why})")
        o = planned.chosen
        exp = o.expected
        if o.plan.intent == "field" and "field" in exp and "row" in exp:
            from .fields import FieldError
            try:
                held = self.session.field_surface.field(exp["field"],
                                                        exp["row"])
            except FieldError as e:
                raise Refused("UNKNOWN_STEP", str(e))
            v = held.value
            if isinstance(v, bool) or not isinstance(v, (int, Fraction)):
                raise Refused("NOT_A_NUMBER",
                              f"{phrase!r} is {v!r}, which is not a number")
            return ("lookup", Fraction(v),
                    {"table": held.table, "row": held.row,
                     "field": exp["field"], "question": q})
        if o.plan.compute == "convert":
            amount, src, dst = o.plan.args
            value = Fraction(amount) * src.factor / dst.factor
            return ("planned", value,
                    {"computation": "convert", "question": q,
                     "recompute": ["convert", ss.render_value(Fraction(
                         amount)), ss.render_value(src.factor),
                         ss.render_value(dst.factor)]})
        if o.plan.compute == "arith":
            op, a, b = o.plan.args
            value = ss.parse_value(o.value)
            if not isinstance(value, Fraction):
                raise Refused("NOT_A_NUMBER", f"{phrase!r} gave {o.value!r}")
            return ("planned", value,
                    {"computation": "arith", "question": q,
                     "recompute": ["arith", op, ss.render_value(Fraction(a)),
                                   ss.render_value(Fraction(b))]})
        v = ss.parse_value(str(o.value).split(" ")[0])
        if isinstance(v, Fraction):
            raise Refused("UNKNOWN_STEP",
                          f"the planner answers {q!r} by a computation this "
                          f"chain cannot re-derive")
        raise Refused("NOT_A_NUMBER",
                      f"{phrase!r} is {o.value!r}, which is not a number")


def _as_int(v: object, what: str) -> int:
    if not isinstance(v, Fraction):
        raise Refused("NOT_A_NUMBER", f"{what} is {v!r}, not a number")
    if v.denominator != 1:
        raise Refused("NOT_AN_INTEGER",
                      f"{what} is {ss.render_value(v)}, not an integer")
    return v.numerator


def _number(b: Builder, index: int, what: str) -> Fraction:
    v = b.value(index)
    if not isinstance(v, Fraction):
        raise Refused("NOT_A_NUMBER",
                      f"{what} (step {index}) is {v!r}, a verdict and not a "
                      f"number")
    return v


def _held_overlap(session, b: Builder, i: int, j: int) -> str:
    """Two looked-up values whose stated precision overlaps cannot be
    ordered (the ordering frame's rule, round two of the cognition study)."""
    from .semantic_plan import _held_interval
    si, sj = b.steps[i - 1], b.steps[j - 1]
    if si.op != "lookup" or sj.op != "lookup":
        return ""
    try:
        vi = session.field_surface.field(si.detail["field"], si.detail["row"])
        vj = session.field_surface.field(sj.detail["field"], sj.detail["row"])
    except Exception:                                # pragma: no cover
        return ""
    ii, ij = _held_interval(vi.value), _held_interval(vj.value)
    if ii is None or ij is None or not ii.overlaps(ij):
        return ""
    return (f"{si.label} and {sj.label} overlap at their stated precision, "
            f"so either order is possible")


def _build(tree: tuple, b: Builder, leaves: Leaves, it: Optional[int],
           session) -> int:
    """Append the steps of ``tree``; return the index of its value."""
    kind = tree[0]
    if kind == "num":
        return b.add("literal", (), tree[1], ss.render_value(tree[1]))
    if kind == "it":
        if it is None:
            raise Refused("UNKNOWN_STEP", "'it' refers to nothing yet")
        return it
    if kind == "leaf":
        op, value, detail = leaves.get(tree[1])
        return b.add(op, (), value, tree[1], detail)
    if kind == "bin":
        _, op, ta, tb = tree
        i = _build(ta, b, leaves, it, session)
        j = _build(tb, b, leaves, it, session)
        x, y = _number(b, i, "the left side"), _number(b, j, "the right side")
        if op == "div" and y == 0:
            raise Refused("DIVISION_BY_ZERO",
                          f"step {j} is 0, and a quotient by 0 is undefined")
        value = {"add": x + y, "sub": x - y, "mul": x * y,
                 "div": x / y if y else None}[op]
        return b.add(op, (i, j), value, f"step {i} {ss.ARITH[op]} step {j}")
    if kind == "pow":
        _, ta, e = tree
        i = _build(ta, b, leaves, it, session)
        x = _number(b, i, "the base")
        if x == 0 and e < 0:
            raise Refused("DIVISION_BY_ZERO", "0 to a negative power")
        return b.add("pow", (i,), x ** e, f"step {i} ^ {e}",
                     {"exponent": e})
    if kind == "fn":
        _, op, ta, tb = tree
        i = _build(ta, b, leaves, it, session)
        j = _build(tb, b, leaves, it, session)
        x = _as_int(b.value(i), f"step {i}")
        y = _as_int(b.value(j), f"step {j}")
        g = ss._gcd(x, y)
        value = Fraction(g if op == "gcd" else (abs(x * y) // g if g else 0))
        return b.add(op, (i, j), value, f"{op}(step {i}, step {j})")
    if kind == "prime":
        i = _build(tree[1], b, leaves, it, session)
        n = _as_int(b.value(i), f"step {i}")
        if n > 10 ** 12:
            raise Refused("UNKNOWN_STEP", f"{n} is above the primality limit")
        f = ss.prime_factor(n)
        value = "prime" if n >= 2 and f is None else "not prime"
        detail = {"factor": f} if f is not None else {}
        return b.add("prime", (i,), value, f"prime?(step {i})", detail)
    if kind == "parity":
        i = _build(tree[2], b, leaves, it, session)
        n = _as_int(b.value(i), f"step {i}")
        value = str((n % 2 == 1) == (tree[1] == "odd"))
        return b.add("parity", (i,), value, f"{tree[1]}?(step {i})",
                     {"asked": tree[1]})
    if kind == "mean":
        idx = [_build(t, b, leaves, it, session) for t in tree[1:]]
        vals = [_number(b, i, f"item {n + 1}") for n, i in enumerate(idx)]
        return b.add("mean", tuple(idx), sum(vals, Fraction(0)) / len(vals),
                     "mean(" + ", ".join(f"step {i}" for i in idx) + ")")
    if kind == "more":
        _, way, ta, tb, word = tree
        i = _build(ta, b, leaves, it, session)
        j = _build(tb, b, leaves, it, session)
        x, y = _number(b, i, "the first"), _number(b, j, "the second")
        hi, lo = (i, j) if way == "more" else (j, i)
        d = b.value(hi) - b.value(lo)
        if d < 0:
            la, lb = b.steps[i - 1].label, b.steps[j - 1].label
            by = ss.render_value(abs(d))
            if word in _OPPOSITE:
                how = f"the first is {_OPPOSITE[word]} by {by}, not {word}"
            else:
                how = f"that is {by} fewer {word}, not more"
            raise Refused("DIFFERENCE_REVERSED",
                          f"{la} is {ss.render_value(x)} and {lb} is "
                          f"{ss.render_value(y)}: {how}, so the question's "
                          f"order is reversed")
        return b.add("sub", (hi, lo), d, f"step {hi} - step {lo}")
    if kind in ("cmp", "larger"):
        if kind == "cmp":
            _, sym, rel, ta, tb = tree
        else:
            _, rel, ta, tb = tree
            sym = ">" if rel == "larger" else "<"
        i = _build(ta, b, leaves, it, session)
        j = _build(tb, b, leaves, it, session)
        x, y = _number(b, i, "the first"), _number(b, j, "the second")
        overlap = _held_overlap(session, b, i, j)
        if overlap and x != y:
            raise Refused("PRECISION_OVERLAP", overlap)
        if kind == "cmp":
            value = str(x > y if sym == ">" else x < y)
            return b.add("compare", (i, j), value, f"step {i} {sym} step {j}",
                         {"symbol": sym, "relation": rel})
        if x == y:
            value = "equal"
        else:
            first = (x > y) == (rel == "larger")
            value = b.steps[i - 1].label if first else b.steps[j - 1].label
        return b.add("larger", (i, j), value, f"{rel} of steps {i}, {j}",
                     {"relation": rel})
    raise Refused("UNKNOWN_STEP", f"no step for {kind}")  # pragma: no cover


def _describe(tree: tuple) -> str:
    k = tree[0]
    if k == "num":
        return ss.render_value(tree[1])
    if k == "it":
        return "it"
    if k == "leaf":
        return f"[{tree[1]}]"
    if k == "bin":
        return f"({_describe(tree[2])} {ss.ARITH[tree[1]]} " \
               f"{_describe(tree[3])})"
    if k == "pow":
        return f"({_describe(tree[1])} ^ {tree[2]})"
    if k == "fn":
        return f"{tree[1]}({_describe(tree[2])}, {_describe(tree[3])})"
    if k == "prime":
        return f"prime?({_describe(tree[1])})"
    if k == "cmp":
        return f"[{_describe(tree[3])} {tree[1]} {_describe(tree[4])}]"
    if k == "larger":
        return f"{tree[1]}({_describe(tree[2])}, {_describe(tree[3])})"
    if k == "parity":
        return f"{tree[1]}?({_describe(tree[2])})"
    if k == "mean":
        return "mean(" + ", ".join(_describe(t) for t in tree[1:]) + ")"
    if k == "more":
        return f"{tree[1]}({_describe(tree[2])} - {_describe(tree[3])})"
    return str(tree)                                  # pragma: no cover


def compose(session, text: str, prefix: Sequence[Step] = (),
            leaves: Optional[Leaves] = None) -> StepAnswer:
    """The composition mode: every reading of every ``then``-segment, the
    agreement rule over readings, and the chain of the first licensed one.

    ``prefix`` is a chain to continue (a follow-up), whose last step is what
    *it* names in the first segment."""
    segments = split_then(text)
    leaves = leaves or Leaves(session)
    if not segments:
        return StepAnswer(text, "unread")
    try:
        per_segment = [segment_readings(s) for s in segments]
    except Refused as r:
        return StepAnswer(text, "refused", refusal=r.name, reason=r.reason)
    if not any(per_segment):
        return StepAnswer(text, "unread")
    structured = (len(segments) > 1 or bool(prefix)
                  or any(_has_structure(t) for t in per_segment[0]))
    if not structured:
        return StepAnswer(text, "unread")
    if not prefix and any(_uses_it(t) for t in per_segment[0]):
        return StepAnswer(text, "unread")
    if any(not rs for rs in per_segment):
        return StepAnswer(text, "unread")
    combos = list(itertools.product(*per_segment))
    if len(combos) > 64:
        return StepAnswer(text, "refused", refusal="TOO_MANY_READINGS",
                          reason=f"{len(combos)} readings of the whole "
                                 f"question; at most 64 are run")
    licensed: List[Tuple[str, Chain]] = []
    failures: List[Refused] = []
    for combo in combos:
        b = Builder(prefix)
        it = len(prefix) if prefix else None
        try:
            for tree in combo:
                it = _build(tree, b, leaves, it, session)
            if it != len(b.steps):
                # the answer is an earlier step (a bare "it"): repeat nothing
                raise Refused("UNKNOWN_STEP", "the last segment adds no step")
        except Refused as r:
            failures.append(r)
            continue
        desc = " then ".join(_describe(t) for t in combo)
        licensed.append((desc, Chain(text, tuple(b.steps), "composition")))
    if not licensed:
        return _refusal(text, failures, leaves.trials)
    values = list(dict.fromkeys(ss.render_value(c.answer)
                                for _, c in licensed))
    readings = tuple((d, ss.render_value(c.answer)) for d, c in licensed)
    if len(values) > 1:
        return StepAnswer(text, "ambiguous", readings=readings,
                          reason=f"{len(values)} licensed readings disagree: "
                          + "; ".join(f"{d} -> {v}" for d, v in readings),
                          trials=leaves.trials)
    return StepAnswer(text, "answered", chain=licensed[0][1],
                      readings=readings, trials=leaves.trials)


# ===========================================================================
# 3.  GOALS -- derivations over the split union of the formula wheels
# ===========================================================================

@dataclass(frozen=True)
class Axiom:
    """One wheel axiom over split labels."""

    wheel: str
    text: str
    labels: Tuple[Tuple[str, str], ...]          # base name -> label
    exps: Tuple[Tuple[str, int], ...]            # label -> net exponent
    k: Fraction                                  # prod(label^exp) = k
    sides: Tuple[object, ...]

    def label_of(self, base: str) -> str:
        return dict(self.labels)[base]

    def base_of(self, label: str) -> str:
        return {v: b for b, v in self.labels}[label]


_AXIOMS: List[Axiom] = []


def axioms() -> List[Axiom]:
    """Every axiom of every wheel, over the junction-split labels."""
    if _AXIOMS:
        return _AXIOMS
    from ..engineering import union as un
    from ..engineering import wheels as wh
    classes = un._classes()
    for w in wh.WHEELS:
        for a in w.axioms:
            lhs, rhs = wh.parse_equation(a)
            exps: Dict[str, Fraction] = {}
            for name, e in lhs.powers:
                exps[name] = exps.get(name, Fraction(0)) + e
            for name, e in rhs.powers:
                exps[name] = exps.get(name, Fraction(0)) - e
            if any(e.denominator != 1 for e in exps.values()):
                continue                              # pragma: no cover
            names = sorted({n for n, _ in lhs.powers + rhs.powers})
            labels = tuple((n, un._label(n, classes[(w.id, n)]))
                           for n in names)
            lab = dict(labels)
            sides = (
                [ss.render_value(lhs.coefficient),
                 [[n, ss.render_value(e)] for n, e in lhs.powers]],
                [ss.render_value(rhs.coefficient),
                 [[n, ss.render_value(e)] for n, e in rhs.powers]])
            _AXIOMS.append(Axiom(
                w.id, a, labels,
                tuple((lab[n], int(e)) for n, e in sorted(exps.items())
                      if e),
                rhs.coefficient / lhs.coefficient, sides))
    return _AXIOMS


def copies(name: str) -> Tuple[str, ...]:
    from ..engineering import union as un
    return un.copies_of(name)


def _solve(ax: Axiom, label: str, env: Mapping[str, Fraction]) -> Fraction:
    """The value of ``label`` from the axiom, the others read from ``env``;
    the caller has checked every other value is non-zero."""
    e = dict(ax.exps)
    rest = Fraction(1)
    for other, eo in ax.exps:
        if other != label:
            rest *= env[other] ** eo
    x_to_e = ax.k / rest
    return x_to_e if e[label] == 1 else 1 / x_to_e


def solved_form(ax: Axiom, base: str) -> str:
    """``base = <monomial in the other names>`` rendered."""
    label = ax.label_of(base)
    e = dict(ax.exps)[label]
    coef = ax.k ** e
    num, den = [], []
    for other, eo in ax.exps:
        if other == label:
            continue
        p = -eo * e
        name = ax.base_of(other)
        term = name if abs(p) == 1 else f"{name}^{abs(p)}"
        (num if p > 0 else den).append(term)
    parts = []
    if coef != 1 or not num:
        parts.append(ss.render_value(coef))
    parts += num
    out = " * ".join(parts)
    if den:
        out += " / " + (den[0] if len(den) == 1 else
                        "(" + " * ".join(den) + ")")
    return out


@dataclass(frozen=True)
class Tree:
    """One derivation: a given, or an axiom solved for a label."""

    label: str
    value: Fraction
    axiom: Optional[Axiom] = None
    children: Tuple["Tree", ...] = ()

    @property
    def size(self) -> int:
        return (1 if self.axiom else 0) + sum(c.size for c in self.children)


class Deriver:
    """All derivation trees of a label from a set of known labels."""

    def __init__(self, known: Mapping[str, Fraction]):
        self.known = dict(known)
        self.memo: Dict[Tuple[str, frozenset], List[Tree]] = {}
        self.zero_blocked = False
        self.root_blocked: List[str] = []
        self.count = 0

    def trees(self, label: str, forbidden: frozenset = frozenset()
              ) -> List[Tree]:
        if label in self.known:
            return [Tree(label, self.known[label])]
        key = (label, forbidden)
        if key in self.memo:
            return self.memo[key]
        self.memo[key] = []
        out: List[Tree] = []
        inner = forbidden | {label}
        for ax in axioms():
            e = dict(ax.exps)
            if label not in e:
                continue
            if abs(e[label]) != 1:
                self.root_blocked.append(f"{ax.text} would need a root to "
                                         f"give {ax.base_of(label)}")
                continue
            others = [o for o, _ in ax.exps if o != label]
            if any(o in inner for o in others):
                continue
            options = [self.trees(o, inner) for o in others]
            if any(not opt for opt in options):
                continue
            for combo in itertools.product(*options):
                env = {t.label: t.value for t in combo}
                if any(v == 0 for v in env.values()):
                    self.zero_blocked = True
                    continue
                out.append(Tree(label, _solve(ax, label, env), ax,
                                tuple(combo)))
                self.count += 1
                if self.count > MAX_DERIVATIONS:
                    raise Refused("TOO_MANY_READINGS",
                                  f"more than {MAX_DERIVATIONS} derivations")
        self.memo[key] = out
        return out


_GOAL = re.compile(r"^(?:given|if|suppose|let)\s+(.+?),?\s+(what is|what's|"
                   r"find|compute|calculate|determine)\s+(.+)$")
_ASSIGN = re.compile(r"(?:the\s+)?([a-z][a-z ]*?)\s*=\s*(-?\d+(?:/\d+)?"
                     r"(?:\.\d+)?)")


def parse_goal(text: str) -> Optional[Tuple[List[Tuple[str, Fraction]],
                                            List[str], str]]:
    """``(givens, targets, verb)`` of a goal question, or None."""
    from .semantic_plan import clean, parse_number
    t = clean(text)
    m = _GOAL.match(t)
    if not m:
        return None
    body, verb, rest = m.group(1), m.group(2), m.group(3)
    items = [x for x in re.split(r",\s*(?:and\s+)?|\s+and\s+", body)
             if x.strip()]
    givens: List[Tuple[str, Fraction]] = []
    for item in items:
        a = _ASSIGN.fullmatch(item.strip())
        if not a:
            return None
        v = parse_number(a.group(2))
        if v is None:
            return None
        givens.append((a.group(1).strip().replace(" ", "_"), v))
    targets = []
    for part in re.split(r",?\s*(?:and\s+)?then\s+|,\s*|\s+and\s+", rest):
        part = _strip_the(part.strip())
        if part:
            targets.append(part.replace(" ", "_"))
    if not givens or not targets:
        return None
    return givens, targets, verb


_ITEM = re.compile(r"(?:the\s+)?([a-z][a-z ]*?)\s*=\s*(.+)")
_AMOUNT = re.compile(r"(-?\d+(?:/\d+)?(?:\.\d+)?)(?:\s+([a-z][a-z ]*))?")


def parse_goal_two(text: str):
    """Round two's reading of a goal question: ``(givens, targets, verb,
    features)``, or None.

    A given is ``(name, spec)`` with ``spec`` one of ``("num", q)``,
    ``("unit", q, unit phrase)`` or ``("register", phrase)``; ``name`` is
    None for a bare register phrase (*given the melting point of iron and
    …*), whose name is the quantity its declared scale measures.  A target
    is ``(name, unit phrase or None)``.  ``features`` names what round one
    could not read; when it is empty the question is round one's."""
    from .semantic_plan import clean, parse_number
    t = clean(text)
    m = _GOAL.match(t)
    if not m:
        return None
    body, verb, rest = m.group(1), m.group(2), m.group(3)
    items = [x.strip() for x in re.split(r",\s*(?:and\s+)?|\s+and\s+", body)
             if x.strip()]
    givens: List[tuple] = []
    features: List[str] = []
    for item in items:
        a = _ITEM.fullmatch(item)
        if a:
            name = a.group(1).strip().replace(" ", "_")
            rhs = a.group(2).strip()
            am = _AMOUNT.fullmatch(rhs)
            if am:
                v = parse_number(am.group(1))
                if v is None:
                    return None
                if am.group(2):
                    givens.append((name, ("unit", v, am.group(2).strip())))
                    features.append("unit")
                else:
                    givens.append((name, ("num", v)))
                continue
            if re.match(r"-?\d", rhs):
                return None
            givens.append((name, ("register", rhs)))
            features.append("register")
            continue
        if not item.startswith("the "):
            return None
        givens.append((None, ("register", item)))
        features.append("register")
    targets: List[tuple] = []
    for part in re.split(r",?\s*(?:and\s+)?then\s+|,\s*|\s+and\s+", rest):
        part = _strip_the(part.strip())
        if not part:
            continue
        um = re.fullmatch(r"(.+?) in ([a-z][a-z ]*)", part)
        if um:
            targets.append((um.group(1).strip().replace(" ", "_"),
                            um.group(2).strip()))
            features.append("target unit")
        else:
            targets.append((part.replace(" ", "_"), None))
    if not givens or not targets:
        return None
    return givens, targets, verb, tuple(dict.fromkeys(features))


def goal_two(session, text: str, parsed=None) -> StepAnswer:
    """Round two of the goal mode: givens with units and register values
    carried into SI, targets stated in a unit asked for, then round one's
    derivation, vetoes and narrative over the SI values."""
    from . import quantity_units as qu
    parsed = parsed or parse_goal_two(text)
    if parsed is None:
        return StepAnswer(text, "unread")
    givens, targets, verb, _features = parsed
    leaves = Leaves(session)
    sourced: List[tuple] = []
    try:
        for name, spec in givens:
            if name is not None and not copies(name):
                raise Refused("UNKNOWN_QUANTITY",
                              f"{name} is named in no formula wheel")
            if spec[0] == "num":
                sourced.append((name, spec[1], None))
                continue
            if spec[0] == "unit":
                _, amount, unit = spec
                read = qu.read_unit(unit)
                qu.check_dimension(name, read.dimension,
                                   f"{ss.render_value(amount)} {unit}")
                sourced.append((name, amount * read.factor,
                                {"kind": "unit", "amount": amount,
                                 "unit": read.phrase,
                                 "factor": read.factor}))
                continue
            phrase = spec[1]
            op, value, detail = leaves.get(phrase)
            if op != "lookup":
                raise qu.UnitRefused(
                    "SCALE_UNDECLARED",
                    f"{phrase!r} is computed by the planner, not held by the "
                    f"register on a declared scale")
            scale = f"{detail['table']}:{detail['field']}"
            factor, dim, quantity = qu.scale_into_si(scale)
            if name is None:
                name = quantity.replace(" ", "_")
                if not copies(name):
                    raise Refused("UNKNOWN_QUANTITY",
                                  f"{phrase} is a {quantity} by the declared "
                                  f"scale table, and no wheel names a "
                                  f"quantity {quantity!r}; the reader does "
                                  f"not guess which wheel quantity is meant")
            qu.check_dimension(name, dim, f"{phrase} ({scale})")
            sourced.append((name, value * factor,
                            {"kind": "scale", "value": value,
                             "phrase": phrase, "detail": detail,
                             "scale": scale, "factor": factor}))
        names, outs = [], {}
        for tname, unit in targets:
            if not copies(tname):
                raise Refused("UNKNOWN_QUANTITY",
                              f"{tname} is named in no formula wheel")
            names.append(tname)
            if unit:
                read = qu.read_unit(unit)
                qu.check_dimension(tname, read.dimension,
                                   f"the unit asked for, {unit}")
                outs[tname] = (read.phrase, read.factor)
    except (Refused, qu.UnitRefused) as r:
        return StepAnswer(text, "refused", refusal=r.name, reason=r.reason,
                          trials=leaves.trials)
    return _goal_core(text, sourced, names, verb, outs)


def _reading_verdict(givens: Mapping[str, Fraction],
                     targets: Sequence[str]):
    """One reading: consistency, then every derivation of every target.

    Returns ``("ok", {target: value}, deriver)`` or ``(name, reason, None)``.
    """
    for g, v in givens.items():
        others = {k: x for k, x in givens.items() if k != g}
        d = Deriver(others)
        for t in d.trees(g):
            if t.value != v:
                return ("INCONSISTENT_GIVENS",
                        f"{g.split('@')[0]} is given as "
                        f"{ss.render_value(v)} but the other givens give "
                        f"{ss.render_value(t.value)} by "
                        + "; ".join(_axioms_used(t)), None)
    d = Deriver(givens)
    values: Dict[str, Fraction] = {}
    for target in targets:
        trees = d.trees(target)
        if not trees:
            if d.zero_blocked:
                return ("DIVISION_BY_ZERO",
                        f"every way to {target.split('@')[0]} solves an "
                        f"axiom through a value of 0", None)
            why = ""
            if d.root_blocked:
                why = " (" + "; ".join(dict.fromkeys(d.root_blocked)) + ")"
            return ("NO_DERIVATION",
                    f"no chain of axiom steps reaches "
                    f"{target.split('@')[0]} from the givens{why}", None)
        vals = list(dict.fromkeys(t.value for t in trees))
        if len(vals) > 1:
            return ("DERIVATIONS_DISAGREE",
                    f"{len(trees)} derivations of {target.split('@')[0]} "
                    f"give {', '.join(map(ss.render_value, vals))}", None)
        values[target] = vals[0]
    return ("ok", values, d)


def _axioms_used(t: Tree) -> List[str]:
    out = [f"{t.axiom.wheel}: {t.axiom.text}"] if t.axiom else []
    for c in t.children:
        out += _axioms_used(c)
    return list(dict.fromkeys(out))


def _one_step(label: str, known: Mapping[str, Fraction]
              ) -> Optional[Tuple[Axiom, Fraction]]:
    """The first axiom that gives ``label`` in one step from ``known``."""
    for ax in axioms():
        e = dict(ax.exps)
        if abs(e.get(label, 0)) != 1:
            continue
        others = [o for o, _ in ax.exps if o != label]
        if all(o in known and known[o] != 0 for o in others):
            return ax, _solve(ax, label, known)
    return None


def _narrative(text: str, kind: str, givens: Sequence[tuple],
               targets: Sequence[Tuple[str, str]],
               values: Mapping[str, Fraction],
               outs: Optional[Mapping[str, tuple]] = None
               ) -> Tuple[Chain, List[str], List[str]]:
    """The chain of one licensed reading: givens, then the asked targets in
    the order they can be taken, deferring and stitching.

    ``givens`` is ``(base, label, value)`` or ``(base, label, value,
    source)``, the source (round two) saying how a given written with a unit
    or read from the register was carried into SI; ``targets`` is ``(base,
    label)`` in the order asked, and ``outs`` maps a target label to the
    ``(unit, factor)`` its answer is stated in.  Returns the chain, the order
    the targets were taken in, and the stitched quantities."""
    b = Builder()
    at: Dict[str, int] = {}
    known: Dict[str, Fraction] = {}
    for g in givens:
        base, label, v = g[:3]
        source = g[3] if len(g) > 3 else None
        at[label] = _given_steps(b, base, v, source)
        known[label] = v
    pending = [t for t in targets if t[1] not in known]
    taken: List[str] = []
    stitched: List[str] = []
    notes: List[str] = []

    def take(label: str, base: str, ax: Axiom, value: Fraction,
             origin: str) -> None:
        names = [(ax.base_of(o), at[o]) for o, _ in ax.exps if o != label]
        at[label] = b.add(
            "axiom", tuple(i for _, i in names), value, base,
            {"wheel": ax.wheel, "axiom": ax.text, "solved_for": base,
             "names": [[n, i] for n, i in names],
             "solved": solved_form(ax, base),
             "sides": ax.sides, "label": label}, origin=origin)
        known[label] = value

    waited: set = set()
    while pending:
        progress = False
        for pos, (base, label) in enumerate(pending):
            got = _one_step(label, known)
            if got is None:
                continue
            ax, value = got
            if label in values and value != values[label]:
                raise Refused("DERIVATIONS_DISAGREE",
                              f"{base} is {ss.render_value(value)} here and "
                              f"{ss.render_value(values[label])} by another "
                              f"derivation")
            origin = "deferred" if base in waited else "asked"
            if pos > 0:
                origin = "moved earlier"
                waited.update(p[0] for p in pending[:pos])
                notes.append(f"{base} was asked after "
                             f"{', '.join(p[0] for p in pending[:pos])}, "
                             f"and was taken first because it could be")
            take(label, base, ax, value, origin)
            taken.append(base)
            pending.pop(pos)
            progress = True
            break
        if progress:
            continue
        # nothing moves: stitch the first pending target from the search
        base, label = pending[0]
        trees = Deriver(known).trees(label)
        if not trees:                                  # pragma: no cover
            raise Refused("NO_DERIVATION", f"nothing reaches {base}")
        best = min(trees, key=lambda t: t.size)

        def place(t: Tree, top: bool) -> None:
            if t.label in known:
                return
            for c in t.children:
                place(c, False)
            if top:
                return
            nb = t.axiom.base_of(t.label)
            take(t.label, nb, t.axiom, t.value, "stitched")
            stitched.append(nb)
            notes.append(f"{nb} was not asked for; it was stitched in "
                         f"because {base} needs it")
        place(best, True)
        if _one_step(label, known) is None:            # pragma: no cover
            raise Refused("NO_DERIVATION", f"stitching did not reach {base}")
    for base, label in targets:
        if outs and label in outs:
            unit, factor = outs[label]
            b.add("unit_out", (at[label],), known[label] / factor, base,
                  {"unit": unit, "factor": ss.render_value(factor),
                   "quantity": base}, origin="asked")
    chain = Chain(text, tuple(b.steps), kind, tuple(notes))
    return chain, taken, stitched


def _given_steps(b: Builder, base: str, v: Fraction,
                 source: Optional[Mapping[str, object]]) -> int:
    """The steps of one given: the number as given (round one), or the
    amount as written then its conversion into SI, or the register entry
    then its conversion into SI (round two).  Returns the SI step."""
    if source is None:
        return b.add("given", (), v, base, {"name": base}, origin="given")
    if source["kind"] == "unit":
        i = b.add("measured", (), source["amount"], base,
                  {"name": base, "unit": source["unit"]}, origin="given")
        frm = source["unit"]
    else:
        i = b.add("lookup", (), source["value"], source["phrase"],
                  source["detail"], origin="given")
        frm = source["scale"]
    return b.add("si", (i,), v, base,
                 {"from": frm, "kind": source["kind"],
                  "factor": ss.render_value(source["factor"]),
                  "quantity": base}, origin="given")


def goal(session, text: str) -> StepAnswer:
    """The goal and narrative modes over the formula wheels."""
    parsed = parse_goal(text)
    if parsed is None:
        return StepAnswer(text, "unread")
    givens, targets, verb = parsed
    unknown = [n for n, _ in givens if not copies(n)] + \
        [t for t in targets if not copies(t)]
    if unknown:
        return StepAnswer(text, "refused", refusal="UNKNOWN_QUANTITY",
                          reason=f"{', '.join(unknown)} is named in no "
                                 f"formula wheel")
    return _goal_core(text, [(n, v, None) for n, v in givens], targets, verb)


def _goal_core(text: str, sourced: Sequence[tuple], targets: Sequence[str],
               verb: str, outs: Optional[Mapping[str, tuple]] = None
               ) -> StepAnswer:
    """Every reading over the split union, the vetoes, and the chain of the
    licensed one.  ``sourced`` is ``(name, SI value, source)``; ``outs``
    maps a target name to the ``(unit, factor)`` its answer is stated in."""
    givens = [(n, v) for n, v, _ in sourced]
    sources = [src for _, _, src in sourced]
    kind = "narrative" if verb == "find" else "goal"
    choice_lists = [copies(n) for n, _ in givens] + \
        [copies(t) for t in targets]
    readings = list(itertools.product(*choice_lists))
    failures: List[Refused] = []
    licensed: List[Tuple[Tuple[str, ...], Dict[str, Fraction]]] = []
    for reading in readings:
        g_labels = reading[:len(givens)]
        t_labels = reading[len(givens):]
        if len(set(g_labels)) != len(g_labels):
            continue
        gmap = {lab: v for lab, (_, v) in zip(g_labels, givens)}
        try:
            name, got, _d = _reading_verdict(gmap, t_labels)
        except Refused as r:
            failures.append(r)
            continue
        if name == "INCONSISTENT_GIVENS":
            return StepAnswer(text, "refused", refusal=name, reason=got,
                              trials=len(readings))
        if name != "ok":
            failures.append(Refused(name, got))
            continue
        licensed.append((reading, got))
    if not licensed:
        return _refusal(text, failures, len(readings))
    def verdict_of(reading, vals):
        return tuple(ss.render_value(vals[lab])
                     for lab in reading[len(givens):])
    distinct = list(dict.fromkeys(verdict_of(r, v) for r, v in licensed))
    described = tuple(
        (", ".join(reading[len(givens):]) + " from " +
         ", ".join(reading[:len(givens)]), " ; ".join(verdict_of(reading,
                                                               vals)))
        for reading, vals in licensed)
    if len(distinct) > 1:
        return StepAnswer(text, "ambiguous", readings=described,
                          reason=f"{len(distinct)} licensed readings "
                          f"disagree: " + "; ".join(f"{d} -> {v}"
                                                    for d, v in described),
                          trials=len(readings))
    reading, vals = licensed[0]
    g_labels = reading[:len(givens)]
    t_labels = reading[len(givens):]
    used = _used_givens(g_labels, givens, t_labels)
    out_labels = {lab: outs[t] for t, lab in zip(targets, t_labels)
                  if outs and t in outs}
    try:
        chain, taken, stitched = _narrative(
            text, kind, [(n, lab, v, src) for lab, (n, v), src
                         in zip(g_labels, givens, sources) if lab in used],
            list(zip(targets, t_labels)), vals, out_labels)
    except Refused as r:
        return StepAnswer(text, "refused", refusal=r.name, reason=r.reason)
    notes = chain.notes + (f"taken in the order {', '.join(taken)}",
                           f"stitched: {', '.join(stitched) or 'nothing'}")
    chain = Chain(chain.question, chain.steps, chain.kind, notes)
    return StepAnswer(text, "answered", chain=chain, readings=described,
                      trials=len(readings))


def _used_givens(g_labels, givens, t_labels) -> set:
    """The givens some smallest derivation of a target reads, in order."""
    gmap = {lab: v for lab, (_, v) in zip(g_labels, givens)}
    d = Deriver(gmap)
    used: set = set()

    def walk(t: Tree) -> None:
        if t.axiom is None:
            used.add(t.label)
        for c in t.children:
            walk(c)
    for lab in t_labels:
        trees = d.trees(lab)
        if trees:
            walk(min(trees, key=lambda t: t.size))
    return used


def taken_order(a: StepAnswer) -> Tuple[str, ...]:
    for n in (a.chain.notes if a.chain else ()):
        if n.startswith("taken in the order "):
            return tuple(x for x in n[len("taken in the order "):]
                         .split(", ") if x)
    return ()


def stitched_of(a: StepAnswer) -> Tuple[str, ...]:
    if not a.chain:
        return ()
    return tuple(s.label for s in a.chain.steps if s.origin == "stitched")


# ===========================================================================
# 4.  THE ENTRY POINT, AND FOLLOW-UPS
# ===========================================================================

def _round_two_goal(text: str):
    """Round two's parse of ``text`` when it uses a round-two feature."""
    if not ROUND_TWO:
        return None
    parsed = parse_goal_two(text)
    return parsed if parsed is not None and parsed[3] else None


def reads(text: str) -> bool:
    """Whether the stepwise layer could read ``text`` (cheap: no planner
    call)."""
    if parse_goal(text) is not None or _round_two_goal(text) is not None:
        return True
    try:
        segs = split_then(text)
        per = [segment_readings(s) for s in segs]
    except Refused:
        return True
    return bool(segs) and (len(segs) > 1 or any(_has_structure(t)
                                                for t in per[0]))


def answer(session, text: str) -> StepAnswer:
    """The stepwise verdict on ``text``: goal mode when it reads as a goal,
    composition otherwise; ``unread`` when neither reads it."""
    two = _round_two_goal(text)
    if two is not None:
        return goal_two(session, text, two)
    if parse_goal(text) is not None:
        return goal(session, text)
    return compose(session, text)


class StepwiseConversation:
    """Turns, and the chain of each, kept under the digest of the
    conversation before it."""

    def __init__(self, session):
        self.session = session
        self.turns: List[str] = []
        self.store: Dict[str, Tuple[Tuple[str, ...], StepAnswer]] = {}

    @staticmethod
    def key(turns: Sequence[str]) -> str:
        return sha256_hex(json.dumps(list(turns)).encode("utf-8"))

    def last(self) -> Optional[StepAnswer]:
        got = self.store.get(self.key(self.turns))
        if got is None or list(got[0]) != list(self.turns):
            return None
        return got[1]

    def ask(self, text: str) -> StepAnswer:
        from .semantic_plan import clean
        t = clean(text)
        prev = self.last()
        if t in ("why", "why so", "show the steps", "how") and prev:
            a = StepAnswer(text, prev.verdict, chain=prev.chain,
                           refusal=prev.refusal, reason=prev.reason,
                           readings=prev.readings, trials=0)
        elif t.startswith("then ") and prev is not None:
            if prev.chain is None:
                a = StepAnswer(text, "refused", refusal="UNKNOWN_STEP",
                               reason="the last turn left no chain")
            else:
                a = compose(self.session, t[5:], prefix=prev.chain.steps)
                if a.chain is not None:
                    steps = tuple(
                        s if s.index <= len(prev.chain.steps) else
                        Step(s.index, s.op, s.inputs, s.value, s.label,
                             s.detail, "follow-up") for s in a.chain.steps)
                    a.chain = Chain(prev.chain.question + " ; " + text,
                                    steps, a.chain.kind)
        else:
            a = answer(self.session, text)
        self.turns.append(text)
        self.store[self.key(self.turns)] = (tuple(self.turns), a)
        return a


# ===========================================================================
# 5.  THE SOLUTION THE ROUTER RETURNS
# ===========================================================================

def chain_solution(a: StepAnswer):
    """A :class:`~glm_universal.runtime.solution.Solution` of a stepwise
    verdict: one :class:`Step` per chain step with both columns."""
    from .parser import Query
    from .solution import Solution, Step as SolStep
    query = Query(raw=a.text, normalised=a.text.strip(), kind="stepwise",
                  rule="stepwise", trace=("stepwise: read by the planner "
                                          "as a chain",))
    if a.answered:
        steps = tuple(SolStep(f"step-{s.index}-{s.origin}",
                              ss.sentence(s), ss.equation(s, a.chain.steps))
                      for s in a.chain.steps)
        steps += (SolStep("answer", ss.answer_sentence(a.chain),
                          f"answer = s{len(a.chain.steps)}"),)
        return Solution(query=query, kind="stepwise", answer=a.value,
                        steps=steps, ok=True,
                        expected={"value": a.value, "faculty": "derive",
                                  "steps": str(len(a.chain.steps))},
                        payload={"stepwise": a.as_dict(),
                                 "faculty": "derive"})
    body = a.summary()
    return Solution(query=query, kind="stepwise", answer=body, ok=False,
                    error=body, steps=(SolStep("refused", body, body),),
                    payload={"stepwise": a.as_dict(), "faculty": "refusal"})


# ===========================================================================
# 6.  THE MEASUREMENT OF THE STUDY'S §2
# ===========================================================================

def _verdict_of(a: StepAnswer) -> Tuple[str, ...]:
    if a.verdict == "answered":
        return ("ANSWER", a.value)
    if a.verdict == "ambiguous":
        return ("AMBIGUOUS",)
    if a.verdict == "refused":
        return ("REFUSED", a.refusal)
    return ("UNREAD",)


def _matches(got: Tuple[str, ...], want: Tuple[str, ...]) -> bool:
    return got[:len(want)] == want


def composition_report(session) -> Dict[str, object]:
    from ..evaluation.stepwise_cases import COMPOSITION_CASES
    from . import semantic_plan as sp
    rows, bare = [], 0
    for cid, q, want in COMPOSITION_CASES:
        a = answer(session, q)
        got = _verdict_of(a)
        bare += bool(sp.ask_planned(session, q).ok)
        rows.append({"id": cid, "want": list(want), "got": list(got),
                     "ok": _matches(got, want), "trials": a.trials})
    wrong = sum(1 for r in rows if r["got"][0] == "ANSWER" and not r["ok"])
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "wrong": wrong, "bare_planner_answers": bare, "rows": rows}


def goals_report(session) -> Dict[str, object]:
    from ..evaluation.stepwise_cases import GOAL_CASES
    rows = []
    for cid, q, want, stitch in GOAL_CASES:
        a = answer(session, q)
        got = _verdict_of(a)
        ok = _matches(got, want) and (not a.answered
                                      or stitched_of(a) == stitch)
        rows.append({"id": cid, "want": list(want), "got": list(got),
                     "stitched": list(stitched_of(a)),
                     "want_stitched": list(stitch), "ok": ok})
    wrong = sum(1 for r in rows if r["got"][0] == "ANSWER" and not r["ok"])
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "wrong": wrong, "rows": rows}


def first_found(text: str, split: bool = True) -> Optional[str]:
    """The control of mark S3: the first derivation found, in declaration
    order, with no consistency check and no agreement over derivations or
    readings; ``split=False`` also shares every name across every wheel."""
    parsed = parse_goal(text)
    if parsed is None:
        return None
    givens, targets, _ = parsed
    if split:
        lists = [copies(n) or (n,) for n, _ in givens] + \
            [copies(t) or (t,) for t in targets]
    else:
        lists = [(n,) for n, _ in givens] + [(t,) for t in targets]
    saved = list(_AXIOMS)
    try:
        if not split:
            _AXIOMS.clear()
            _AXIOMS.extend(_naive_axioms())
        for reading in itertools.product(*lists):
            gl = reading[:len(givens)]
            gmap = {lab: v for lab, (_, v) in zip(gl, givens)}
            try:
                trees = Deriver(gmap).trees(reading[len(givens)])
            except Refused:
                continue
            if trees:
                return ss.render_value(trees[0].value)
        return None
    finally:
        _AXIOMS.clear()
        _AXIOMS.extend(saved)


def _naive_axioms() -> List[Axiom]:
    out = []
    for ax in axioms():
        labels = tuple((b, b) for b, _ in ax.labels)
        exps = tuple((ax.base_of(l), e) for l, e in ax.exps)
        out.append(Axiom(ax.wheel, ax.text, labels, exps, ax.k, ax.sides))
    return out


def controls_report(session) -> Dict[str, object]:
    from ..evaluation.stepwise_cases import GOAL_CASES
    rows = []
    for cid, q, want, _ in GOAL_CASES:
        a = answer(session, q)
        rows.append({"id": cid, "stepwise": list(_verdict_of(a)),
                     "first_found": first_found(q, True),
                     "naive_union": first_found(q, False)})
    refused = [r for r in rows if r["stepwise"][0] != "ANSWER"]
    return {
        "first_found_answers_refused": sum(
            1 for r in refused if r["first_found"] is not None),
        "naive_answers_ambiguous": sum(
            1 for r in rows if r["stepwise"][0] == "AMBIGUOUS"
            and r["naive_union"] is not None),
        "rows": rows,
    }


def narratives_report(session) -> Dict[str, object]:
    from ..evaluation.stepwise_cases import NARRATIVE_CASES
    rows = []
    for cid, q, want, values, order, stitch in NARRATIVE_CASES:
        a = answer(session, q)
        got = _verdict_of(a)
        vals = {}
        if a.chain:
            for s in a.chain.steps:
                if s.op == "axiom" and s.origin != "stitched":
                    vals[s.label] = ss.render_value(s.value)
        ok = got[0] == want[0] and (want[0] != "REFUSED" or got == want)
        if want[0] == "ANSWER":
            ok = ok and vals == values and taken_order(a) == order and \
                stitched_of(a) == stitch
        rows.append({"id": cid, "got": list(got), "values": vals,
                     "order": list(taken_order(a)),
                     "stitched": list(stitched_of(a)), "ok": ok})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "rows": rows}


def follow_ups_report(session) -> Dict[str, object]:
    from ..evaluation.stepwise_cases import FOLLOW_UP_CASES
    rows = []
    for cid, first, second, want in FOLLOW_UP_CASES:
        conv = StepwiseConversation(session)
        conv.ask(first)
        a = conv.ask(second)
        # the exact key: a different history must not reuse the chain
        other = StepwiseConversation(session)
        other.turns = [first + " "]
        other.store = dict(conv.store)
        leak = other.last() is not None
        got = _verdict_of(a)
        rows.append({"id": cid, "want": list(want), "got": list(got),
                     "ok": _matches(got, want) and not leak,
                     "leak": leak})
    return {"cases": len(rows), "met": sum(r["ok"] for r in rows),
            "rows": rows}


def answered_chains(session) -> List[Tuple[str, Chain]]:
    """Every answered chain of the declared corpus, with its case id."""
    from ..evaluation import stepwise_cases as C
    out: List[Tuple[str, Chain]] = []
    for cid, q, *_ in (C.COMPOSITION_CASES + C.GOAL_CASES
                       + C.NARRATIVE_CASES):
        a = answer(session, q)
        if a.answered:
            out.append((cid, a.chain))
    for cid, first, second, _ in C.FOLLOW_UP_CASES:
        conv = StepwiseConversation(session)
        conv.ask(first)
        a = conv.ask(second)
        if a.answered:
            out.append((cid, a.chain))
    return out


def scripts_report(session) -> Dict[str, object]:
    """Mark S5: every answered chain's script in a fresh ``python3 -I``, and
    the four mutations of each."""
    from .python_tct import run_column3
    from .tct_engine import package_root
    root = str(package_root())
    verified, failed, aligned_lines, steps = 0, [], 0, 0
    caught: Dict[str, int] = {k: 0 for k in ss.MUTATION_KINDS}
    built: Dict[str, int] = {k: 0 for k in ss.MUTATION_KINDS}
    escaped: List[str] = []
    for cid, chain in answered_chains(session):
        got = run_column3(ss.render_script(chain, root))
        steps += len(chain.steps)
        m = re.search(r"ALIGNED (\d+) of (\d+)", got["stdout"])
        aligned_lines += int(m.group(1)) if m else 0
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
    return {"chains": verified + len(failed), "verified": verified,
            "failed": failed, "steps": steps, "aligned": aligned_lines,
            "mutants": built,
            "caught": caught, "escaped": escaped}


def interference_report(session) -> Dict[str, object]:
    """Mark S6: what the stepwise layer does to the router's declared sets.

    The router consults it only after a planner refusal, so an answered
    verdict cannot change (``GLM.StepwisePlanner.fallback_conservative``).
    What remains to count is the declared questions it *reads* at all, and
    among them the ones the planner refuses and it would answer."""
    from . import router
    from ..evaluation.cases import CASES
    declared_refusals = {c.question for c in CASES if c.expect == "refusal"}
    sets = router._declared_sets()
    rows = []
    for name in ("contract", "engineering", "cognition"):
        for q in sets[name]:
            if router.reader_of(q) != "planner":
                continue
            a = answer(session, q)
            if a.verdict == "unread":
                continue
            planner_ok = bool(session.ask_planned(q).ok)
            rows.append({"set": name, "question": q,
                         "stepwise": list(_verdict_of(a)),
                         "planner_answers": planner_ok,
                         "declared_refusal": q in declared_refusals})
    changed = [r for r in rows if not r["planner_answers"]
               and r["stepwise"][0] == "ANSWER"]
    return {"questions": sum(1 for n in ("contract", "engineering",
                                         "cognition")
                             for q in sets[n]),
            "read": len(rows), "rows": rows,
            "turned_into_answers": [r["question"] for r in changed],
            "declared_refusals_answered": [r["question"] for r in changed
                                           if r["declared_refusal"]]}


def stepwise_report(scripts: bool = True) -> Dict[str, object]:
    """The whole measurement of ``studies/STEPWISE_PLANNER_STUDY.md``."""
    from .session import GeometricSession
    session = GeometricSession()
    report: Dict[str, object] = {
        "composition": composition_report(session),
        "goals": goals_report(session),
        "controls": controls_report(session),
        "narratives": narratives_report(session),
        "follow_ups": follow_ups_report(session),
        "interference": interference_report(session),
        "study": "studies/STEPWISE_PLANNER_STUDY.md",
        "lean_file": "RequestProject/GLM/StepwisePlanner.lean",
    }
    if scripts:
        report["scripts"] = scripts_report(session)
    return report

"""``glm_universal.reasoning.carried_read`` -- the machine reads what it
carries (Phase 153): the reading mode of :func:`planner_ladder.check_chain`.

*Created 31 October 2026.*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/CARRIED_READ_STUDY.md,
MASTER_PLAN.md (Phase 153), RequestProject/GLM/CarriedRead.lean and the
callers in reasoning/tool_machine.py.*

What changes in the reading mode
--------------------------------
Phase 151 carried every value that came from outside the machine.  Here:

* a ``lookup`` step's file is written only when
  ``FIND "@row.field=value;" < reg/<table>.txt`` succeeds (the register
  files of :mod:`register_files`); otherwise the run stops with exit code 2;
* a ``given``, ``measured`` or ``literal`` step's file only when
  ``@number=value;`` is a line of :data:`QUESTION_FILE`, the question's own
  numbers (:func:`question_numbers`) -- **membership**, so a lie that is
  another number of the same question is not seen (``find_iff_mem``);
* ``gcd``, ``lcm``, ``parity``, ``prime`` (up to :data:`PRIME_LIMIT`, by
  trial division in a loop), ``larger``, ``comparative`` and the exact folds
  ``even``, ``odd``, ``max``, ``min`` are computed (:func:`compute`).

The found line goes to the output stream, which becomes the run's read log,
never to a file: column 3's reader does not read a line with two
redirections (``studies/CARRIED_READ_STUDY.md`` §0).

**Number words as junctions.**  The question is read as the planner reads it
(``semantic_plan.clean``: spelled-out integers as digits), and the words of
:data:`NUMBER_JUNCTIONS` are identified with their numbers -- the stepwise
grammar's own (*twice*, *double*, *half*, *halve*, *negate*) and a declared
list beyond them.  Widening it is adding a row.

Exactness
---------
Integers, :class:`fractions.Fraction` and strings only.
"""

from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from . import register_files as rf

__all__ = [
    "QUESTION_FILE", "NUMBER_JUNCTIONS", "PRIME_LIMIT", "question_numbers",
    "question_file", "seed_files", "read_lines", "compute", "needle",
]

#: The machine's copy of the question's numbers.
QUESTION_FILE: str = "q.txt"

#: Number words identified with numbers (the junction rule: two names are
#: one only where a declared junction identifies them).  The first five are
#: the stepwise grammar's own (``negate`` is ``0 - x``, so its number is 0).
NUMBER_JUNCTIONS: Tuple[Tuple[str, Fraction], ...] = (
    ("twice", Fraction(2)), ("double", Fraction(2)), ("half", Fraction(2)),
    ("halve", Fraction(2)), ("negate", Fraction(0)),
    ("triple", Fraction(3)), ("thrice", Fraction(3)),
    ("a dozen", Fraction(12)), ("a score", Fraction(20)),
    ("a quarter", Fraction(4)), ("a third", Fraction(3)),
    ("square", Fraction(2)), ("cube", Fraction(3)),
)

#: ``prime`` is computed up to here (trial division in a loop); above it the
#: step stays carried.
PRIME_LIMIT: int = 10 ** 8

_NUMBER = re.compile(r"(?<![\w.])-?\d+(?:/\d+)?(?:\.\d+)?")


def question_numbers(text: str) -> List[Fraction]:
    """The numbers of a question, as the planner reads it, in order and
    without repetition."""
    from ..runtime.semantic_plan import clean, parse_number
    out: List[Fraction] = []
    for part in str(text).split(" ; "):
        t = clean(part)
        for m in _NUMBER.finditer(t):
            v = parse_number(m.group(0))
            if v is not None and v not in out:
                out.append(v)
            if v is not None and v < 0 and -v not in out:
                out.append(-v)
        for word, v in NUMBER_JUNCTIONS:
            if re.search(r"\b" + re.escape(word) + r"\b", t) and v not in out:
                out.append(v)
    return out


def _text(v: Fraction) -> str:
    return str(v.numerator) if v.denominator == 1 else \
        f"{v.numerator}/{v.denominator}"


def needle(v: Fraction) -> str:
    return f"@number={_text(Fraction(v))};"


def question_file(text: str) -> Tuple[str, ...]:
    """The lines of :data:`QUESTION_FILE`."""
    return tuple(needle(v) for v in question_numbers(text))


def seed_files(chain, session=None) -> Dict[str, Tuple[str, ...]]:
    """The seed files of a chain: the register files of the tables its
    lookups read, and the question's numbers."""
    files: Dict[str, Tuple[str, ...]] = {QUESTION_FILE:
                                         question_file(chain.question)}
    want = {rf.table_path(str(s.detail.get("table")))
            for s in chain.steps if s.op == "lookup"}
    want |= {rf.table_path(str(s.detail.get("table")))
             for s in chain.steps if s.op == "fold" and s.detail.get("table")}
    if want:
        allf = rf.register_files(session)["files"]
        for p in sorted(want):
            if p in allf:
                files[p] = allf[p]
    return files


def read_lines(b, s, seed: Mapping[str, Sequence[str]]) -> Optional[str]:
    """The read of a step whose value comes from outside the machine:
    ``"read:register"``, ``"read:question"``, or ``None`` when the step is
    not read (it is then computed or carried).  The lines stop the run with
    exit code 2 when the machine does not find the value."""
    v = s.value
    if s.op == "lookup":
        d = s.detail
        path = rf.table_path(str(d.get("table")))
        line = rf.entry_line(str(d.get("row")), str(d.get("field")), v)
        if line is None or path not in seed:
            return None
        b.lines.append(f"REM step {s.index}: read from the register")
        b.lines.append(f'FIND "{line}" < {path} || EXIT /B 2')
        return "read:register"
    if s.op in ("given", "measured", "literal"):
        if not isinstance(v, Fraction) or QUESTION_FILE not in seed:
            return None
        b.lines.append(f"REM step {s.index}: read from the question")
        b.lines.append(f'FIND "{needle(v)}" < {QUESTION_FILE} || EXIT /B 2')
        return "read:question"
    return None


# ---------------------------------------------------------------------------
# the steps the reading mode computes
# ---------------------------------------------------------------------------

def _int(b, t: str) -> None:
    b.lines.append(f"IF %{t}D% NEQ 1 EXIT /B 2")


def _euclid(b, a: str, c: str, out: str) -> None:
    """``out`` = gcd(|aN|, |cN|) by a loop."""
    top = b.label("GCD")
    b.lines += [f"SET /A EA={a}N", "IF %EA% LSS 0 SET /A EA=0-EA",
                f"SET /A EB={c}N", "IF %EB% LSS 0 SET /A EB=0-EB",
                f":{top}", f"IF %EB% EQU 0 GOTO {top}D",
                "SET /A ET=EA-(EA/EB)*EB", "SET /A EA=EB", "SET /A EB=ET",
                f"GOTO {top}", f":{top}D", f"SET /A {out}=EA"]


def _sayable(text: str) -> bool:
    return bool(text.strip()) and text == text.strip() and \
        not (set(text) & set('<>|&%"^'))


def _literal(x):
    import ast
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except (ValueError, SyntaxError):
            return x
    return x


def compute(b, s, steps, pairs: Mapping[int, str],
            verdicts: Mapping[int, bool]) -> Optional[str]:
    """Lines computing a step of the reading mode; ``"number"`` (left in
    ``V<k>``, not yet reduced), ``"verdict"`` (in ``S<k>``), or ``None`` when
    the step is not one of them.  Raises :class:`tool_machine.Unsaid` when
    it is one of them but its inputs are not held."""
    from .tool_machine import Unsaid
    k = s.index
    op = s.op
    ins = tuple(int(j) for j in s.inputs)

    def num(j: int) -> str:
        if j not in pairs:
            raise Unsaid("an input the machine does not hold as a number")
        return pairs[j]

    if op in ("gcd", "lcm"):
        a, c = num(ins[0]), num(ins[1])
        _int(b, a)
        _int(b, c)
        _euclid(b, a, c, "EG")
        if op == "gcd":
            b.set_pair(f"V{k}", "EG", "1")
        else:
            b.lines += [f"SET /A EL={a}N*{c}N", "IF %EL% LSS 0 SET /A EL=0-EL",
                        "SET /A EM=EG", "IF %EM% EQU 0 SET /A EM=1",
                        "SET /A EL=EL/EM"]
            b.set_pair(f"V{k}", "EL", "1")
        return "number"
    if op == "parity":
        a = num(ins[0])
        _int(b, a)
        odd = s.detail.get("asked") == "odd"
        b.lines += [f"SET /A XP={a}N-({a}N/2)*2",
                    f"SET S{k}={'False' if odd else 'True'}",
                    f"IF %XP% NEQ 0 SET S{k}={'True' if odd else 'False'}"]
        return "verdict"
    if op == "prime":
        n = steps[ins[0] - 1].value
        if not isinstance(n, Fraction) or n.denominator != 1 or \
                n > PRIME_LIMIT or "certificate" in s.detail:
            raise Unsaid("past the trial-division bound")
        a = num(ins[0])
        _int(b, a)
        top = b.label("PRIME")
        b.lines += [f"SET /A PN={a}N", f"SET S{k}=not prime",
                    f"IF %PN% LSS 2 GOTO {top}D", "SET /A PF=2",
                    f":{top}", "SET /A PQ=PF*PF",
                    f"IF %PQ% GTR %PN% GOTO {top}Y",
                    "SET /A PR=PN-(PN/PF)*PF", f"IF %PR% EQU 0 GOTO {top}D",
                    "SET /A PF=PF+1", f"GOTO {top}", f":{top}Y",
                    f"SET S{k}=prime", f":{top}D"]
        return "verdict"
    if op in ("larger", "comparative"):
        a, c = num(ins[0]), num(ins[1])
        if op == "larger":
            la, lb = steps[ins[0] - 1].label, steps[ins[1] - 1].label
            first_if_greater = s.detail.get("relation") == "larger"
        else:
            rows = _literal(s.detail.get("rows"))
            la, lb = str(rows[0]), str(rows[1])
            first_if_greater = s.detail.get("symbol") == ">"
        if not (_sayable(la) and _sayable(lb)):
            raise Unsaid("a label GLM-BAT cannot carry")
        hi, lo = (la, lb) if first_if_greater else (lb, la)
        b.lines += [f"SET /A XL={a}N*{c}D-{c}N*{a}D", f"SET S{k}=equal",
                    f"IF %XL% GTR 0 SET S{k}={hi}",
                    f"IF %XL% LSS 0 SET S{k}={lo}"]
        return "verdict"
    if op == "fold":
        d = s.detail
        fn = d.get("fn")
        exact = not d.get("bounds") and str(d.get("bounded")) != "True" \
            and str(d.get("present")) != "True"
        if not exact or fn not in ("even", "odd", "max", "min"):
            return None
        if fn in ("even", "odd"):
            want = 1 if fn == "odd" else 0
            b.lines.append("SET /A XN=0")
            for j in ins:
                t = num(j)
                _int(b, t)
                b.lines += [f"SET /A XP={t}N-({t}N/2)*2",
                            "IF %XP% LSS 0 SET /A XP=0-XP",
                            f"IF %XP% EQU {want} SET /A XN=XN+1"]
            b.set_pair(f"V{k}", "XN", "1")
            return "number"
        first = num(ins[0])
        b.set_pair("XM", f"{first}N", f"{first}D")
        test = "GTR" if fn == "max" else "LSS"
        for j in ins[1:]:
            t = num(j)
            b.lines += [f"SET /A XS={t}N*XMD-XMN*{t}D",
                        f"IF %XS% {test} 0 SET /A XMN={t}N",
                        f"IF %XS% {test} 0 SET /A XMD={t}D"]
        b.set_pair(f"V{k}", "XMN", "XMD")
        return "number"
    return None

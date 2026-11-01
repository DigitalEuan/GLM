"""``glm_universal.reasoning.planner_ladder`` -- the chain of the stepwise
planner said as a GLM-BAT program and run by the batch machine (Phase 151).

*Created 31 October 2026.*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/PLANNER_LADDER_STUDY.md,
studies/CARRIED_READ_STUDY.md, studies/PI_MACHINE_STUDY.md, MASTER_PLAN.md
(Phases 151, 153, 160, 163, 166), RequestProject/GLM/PlannerLadder.lean, the
callers in GLM.py, reasoning/tool_machine.py and reasoning/pi_machine_study.py,
and tests/README.md.  The program's exact line forms, and therefore its line
and step counts, are this reconstruction's own.*

What a chain becomes
--------------------
Every step of an answered chain (:class:`stepwise_script.Chain`) is said as
GLM-BAT lines (``studies/PLANNER_LADDER_STUDY.md`` §0).  ``SET /A`` is
integer arithmetic, so a rational value is held as a numerator and a nonzero
denominator, the pair ``V<k>N``/``V<k>D`` of step ``k``
(``GLM.PlannerLadder.Rep``); a verdict (a string) is held as ``S<k>``.

* A step the machine can compute -- the four operations, powers, means and
  sums, unit conversions, a formula-wheel axiom, a comparison -- is
  **computed** from the machine's own earlier values and reduced by Euclid's
  algorithm (the ``:NORM`` subroutine, a loop).
* A step whose value comes from outside the machine is **carried**: written
  into the program as data.
* In the **reading mode** (Phase 153, :mod:`carried_read`) a ``lookup`` step
  is a register read (``FIND "@row.field=value;" < reg/<table>.txt``), a
  ``given``, ``measured`` or ``literal`` step a read of the question's own
  numbers in ``q.txt``, and ``gcd``, ``lcm``, ``parity``, ``prime``,
  ``larger``, ``comparative`` and the folds ``even``, ``odd``, ``max``,
  ``min`` are computed.  With :data:`fold_machine.ON` the order folds are
  computed by counting (Phase 160); with :data:`tool_machine.ON` the tool
  answers, conversions, ``choose``, ``first`` and the axioms' powers are
  worked out by the machine (Phase 163).

Each step writes ``s<k>.txt``.  **Drift** is the planner's claims (one file
per step, the desired state) against what the machine leaves
(:func:`batch_machine.drift`).  The **gated** program checks each computed
step by cross-multiplication (``rep_check_iff``) and exits 1 at the first
mismatch; it is the first stage of a pipeline whose second stage promotes the
last file, with rollback on (``rollback_journal``,
``promoted_iff_no_drift``).  A chain is **admitted** when the run halts with
exit code 0, leaves no drift and the pipeline promotes.

Exactness
---------
Integers, :class:`fractions.Fraction`, strings and booleans only.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field, replace
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from . import batch_machine as bm

__all__ = [
    "BUDGET", "LEAN_FILE", "LEAN_THEOREMS", "Carry", "Builder", "Ladder",
    "chain_program", "check_chain", "describe", "column3_scripts",
    "run_pipeline", "lie_chain", "value_lie", "NORM_LINES", "file_of",
    "step_inputs", "REFUSAL", "gate", "column3_mutants",
]

#: The refusal of a chain the machine disagrees with (Phase 151).
REFUSAL: str = "MACHINE_DRIFT"

#: The stage budget of the machine's runs here (Phase 160: the gated
#: pipeline runs under the same budget as the run it gates).
BUDGET: int = 200_000

LEAN_FILE: str = "PlannerLadder.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "rep_int", "rep_add", "rep_sub", "rep_mul", "rep_div", "rep_check_iff",
    "machine_eq_honest", "drift_eq_lies", "no_drift_iff", "writeAll_append",
    "rollback_journal", "promoted_iff_no_drift")

#: Characters a GLM-BAT line cannot carry inside a value.
_UNSAYABLE = set('<>|&%"^')


class Carry(Exception):
    """The step is not computed here; it is carried as data."""


# ---------------------------------------------------------------------------
# the subroutine every program ends with
# ---------------------------------------------------------------------------

#: Euclid's algorithm on ``RN/RD``: the sign moved to the numerator, both
#: divided by their greatest common divisor (``GLM.PlannerLadder.Rep``).
NORM_LINES: Tuple[str, ...] = (
    ":NORM",
    "IF %RD% LSS 0 SET /A RN=0-RN",
    "IF %RD% LSS 0 SET /A RD=0-RD",
    "SET /A GA=RN",
    "IF %GA% LSS 0 SET /A GA=0-GA",
    "SET /A GB=RD",
    ":NORML",
    "IF %GB% EQU 0 GOTO NORMD",
    "SET /A GT=GA-(GA/GB)*GB",
    "SET /A GA=GB",
    "SET /A GB=GT",
    "GOTO NORML",
    ":NORMD",
    "IF %GA% EQU 0 EXIT /B 0",
    "SET /A RN=RN/GA",
    "SET /A RD=RD/GA",
    "EXIT /B 0",
)


def file_of(k: int) -> str:
    """The file step ``k`` writes."""
    return f"s{k}.txt"


def _sayable(text: str) -> bool:
    return bool(text.strip()) and text == text.strip() and \
        not (set(text) & _UNSAYABLE)


def _render(v: object) -> str:
    from .stepwise_script import render_value
    return render_value(v)


def _literal(x) -> object:
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except (ValueError, SyntaxError):
            return x
    return x


def step_inputs(step) -> Tuple[int, ...]:
    return tuple(int(j) for j in step.inputs)


# ---------------------------------------------------------------------------
# the program builder (also used by tool_machine, fold_machine, carried_read)
# ---------------------------------------------------------------------------

class Builder:
    """The lines of one program, with fresh pair names and the subroutines
    it used.  A *pair* ``t`` is two variables ``tN``/``tD``."""

    def __init__(self) -> None:
        self.lines: List[str] = []
        self._n = 0
        self._labels = 0
        self.tool_subs: set = set()
        self.subs: set = set()

    def pair(self) -> str:
        self._n += 1
        return f"T{self._n}"

    def label(self, stem: str) -> str:
        self._labels += 1
        return f"{stem}{self._labels}"

    def set_pair(self, t: str, n: str, d: str) -> None:
        self.lines.append(f"SET /A {t}N={n}")
        self.lines.append(f"SET /A {t}D={d}")

    def const(self, v: Fraction) -> str:
        v = Fraction(v)
        t = self.pair()
        self.set_pair(t, str(v.numerator), str(v.denominator))
        return t

    def norm(self, t: str) -> None:
        self.lines += [f"SET /A RN={t}N", f"SET /A RD={t}D", "CALL :NORM",
                       f"SET /A {t}N=RN", f"SET /A {t}D=RD"]
        self.subs.add("NORM")

    def add(self, a: str, c: str, sign: str = "+") -> str:
        t = self.pair()
        self.set_pair(t, f"{a}N*{c}D{sign}{c}N*{a}D", f"{a}D*{c}D")
        self.norm(t)
        return t

    def mul(self, a: str, c: str) -> str:
        t = self.pair()
        self.set_pair(t, f"{a}N*{c}N", f"{a}D*{c}D")
        self.norm(t)
        return t

    def div(self, a: str, c: str) -> str:
        t = self.pair()
        self.lines.append(f"IF %{c}N% EQU 0 EXIT /B 2")
        self.set_pair(t, f"{a}N*{c}D", f"{a}D*{c}N")
        self.norm(t)
        return t

    def inv(self, a: str) -> str:
        t = self.pair()
        self.lines.append(f"IF %{a}N% EQU 0 EXIT /B 2")
        self.set_pair(t, f"{a}D", f"{a}N")
        self.norm(t)
        return t

    def powi(self, a: str, e: int) -> str:
        """``a ** e`` by a counted loop of multiplications."""
        if e < 0:
            return self.inv(self.powi(a, -e))
        t = self.pair()
        self.set_pair(t, "1", "1")
        if e:
            top = self.label("POW")
            k, done = f"PK{top[3:]}", f"{top}D"
            self.lines += [f"SET /A {k}=0", f":{top}",
                           f"IF %{k}% GEQ {e} GOTO {done}",
                           f"SET /A {t}N={t}N*{a}N", f"SET /A {t}D={t}D*{a}D",
                           f"SET /A {k}={k}+1", f"GOTO {top}", f":{done}"]
        self.norm(t)
        return t

    def scale(self, a: str, f: Fraction, off: Fraction) -> str:
        """``a * f + off`` (a unit or scale conversion)."""
        f, off = Fraction(f), Fraction(off)
        t = self.pair()
        self.set_pair(
            t, f"{a}N*{f.numerator * off.denominator}+"
               f"({off.numerator * f.denominator})*{a}D",
            f"{a}D*{f.denominator * off.denominator}")
        self.norm(t)
        return t

    def sign(self, a: str, c: str, var: str) -> None:
        """``var`` gets the sign carrier ``aN*cD - cN*aD`` (denominators are
        kept positive by ``:NORM``)."""
        self.lines.append(f"SET /A {var}={a}N*{c}D-{c}N*{a}D")


# ---------------------------------------------------------------------------
# the program of a chain
# ---------------------------------------------------------------------------

@dataclass
class Ladder:
    """A chain said as GLM-BAT, its run, its drift and its pipeline."""

    question: str
    lines: Tuple[str, ...]
    gated: Tuple[str, ...]
    kinds: Dict[int, str]
    seed: Dict[str, Tuple[str, ...]]
    desired: Dict[str, Tuple[str, ...]]
    read: bool = False
    run: Optional[bm.Run] = None
    drift: Tuple[str, ...] = ()
    pipeline: Dict[str, object] = field(default_factory=dict)
    said: Optional[bool] = None
    error: str = ""

    @property
    def last(self) -> str:
        return file_of(len(self.kinds))

    def indices(self, *kinds: str) -> Tuple[int, ...]:
        return tuple(k for k, v in sorted(self.kinds.items()) if v in kinds)


def _number_pair(b: Builder, k: int, v: Fraction) -> str:
    t = f"V{k}"
    b.set_pair(t, str(v.numerator), str(v.denominator))
    return t


def _write_number(b: Builder, k: int, t: str) -> None:
    b.lines += [f"SET W=%{t}N%", f"IF %{t}D% NEQ 1 SET W=%{t}N%/%{t}D%",
                f"ECHO %W%> {file_of(k)}"]


def _write_text(b: Builder, k: int) -> None:
    b.lines.append(f"ECHO %S{k}%> {file_of(k)}")


def _gate(b: Builder, k: int, claim: object) -> None:
    """The gated program's check of a computed step against its claim."""
    if isinstance(claim, Fraction):
        p, q = claim.numerator, claim.denominator
        b.lines += [f"SET /A XG=V{k}N*{q}-V{k}D*({p})",
                    "IF %XG% NEQ 0 EXIT /B 1"]
    else:
        b.lines.append(f'IF NOT "%S{k}%"=="{_render(claim)}" EXIT /B 1')


def _axiom_parts(step):
    d = step.detail
    names = {str(n): int(j) for n, j in _literal(d.get("names", ()))}
    sides = _literal(d.get("sides"))
    x = str(d.get("solved_for"))
    if not isinstance(sides, (list, tuple)) or len(sides) != 2:
        raise Carry("an axiom without sides")
    parsed = []
    for coef, powers in sides:
        parsed.append((Fraction(str(coef)),
                       [(str(n), int(str(e))) for n, e in powers]))
    return x, names, parsed


def _axiom(b: Builder, step, names_pairs: Mapping[int, str],
           roots: bool) -> str:
    """The solved variable of a formula-wheel axiom, from the machine's own
    values of the others.  With ``roots`` (Phase 163, the tool machine) an
    axiom's ``^`` is read as the power it means, and a power of the solved
    variable is undone by a root the program offers and the machine checks
    by raising it to the power; without it an axiom with a power other than
    one stays carried."""
    x, names, sides = _axiom_parts(step)
    where = [i for i, (_c, ps) in enumerate(sides) if any(n == x for n, _ in
                                                          ps)]
    if len(where) != 1:
        raise Carry("the solved variable is not on exactly one side")
    i = where[0]
    coef_x, pows_x = sides[i]
    coef_o, pows_o = sides[1 - i]
    p = sum(e for n, e in pows_x if n == x)
    if p == 0:
        raise Carry("the solved variable cancels")
    if abs(p) != 1 and not roots:
        raise Carry("a power the machine does not undo")
    if not roots and any(abs(e) > 1 for _c, ps in sides for _n, e in ps):
        # an axiom's ``^`` is read as the power it means only by the tool
        # machine (Phase 163); before it the step is carried -- the seven
        # axiom steps of CARRIED_READ_STUDY.md §7.2
        raise Carry("a power (^) the machine does not read")
    acc = b.const(coef_o / coef_x)
    terms = [(n, e, True) for n, e in pows_o] + \
        [(n, e, False) for n, e in pows_x if n != x]
    for n, e, upper in terms:
        j = names.get(n)
        if j is None or j not in names_pairs:
            raise Carry("an input the machine does not hold as a number")
        term = b.powi(names_pairs[j], e) if e != 1 else names_pairs[j]
        acc = b.mul(acc, term) if upper else b.div(acc, term)
    if p == 1:
        return acc
    if p == -1:
        return b.inv(acc)
    # x ** p = acc: the root offered as a witness, checked by the power
    value = step.value
    if not isinstance(value, Fraction):
        raise Carry("a root of a value that is not a number")
    w = b.const(value)
    chk = b.powi(w, p)
    b.lines += [f"SET /A XR={chk}N*{acc}D-{acc}N*{chk}D",
                "IF %XR% NEQ 0 EXIT /B 2"]
    return w


_COMPUTED_ALWAYS = ("add", "sub", "mul", "div", "pow", "mean", "si",
                    "unit_out", "compare", "axiom")


def _compute(b: Builder, s, steps, pairs: Dict[int, str],
             verdicts: Dict[int, bool], read: bool,
             files: Mapping[str, Sequence[str]]) -> str:
    """Lines computing step ``s``; returns ``"number"`` (the value is left in
    the pair ``V<k>``) or ``"verdict"`` (in ``S<k>``).  Raises :class:`Carry`
    (or :class:`tool_machine.Unsaid`) when the step is carried."""
    from . import tool_machine as tm
    from . import fold_machine as fm
    k = s.index
    ins = step_inputs(s)
    op = s.op

    def num(j: int) -> str:
        if j not in pairs:
            raise Carry("an input the machine does not hold as a number")
        return pairs[j]

    def finish(t: str) -> str:
        b.set_pair(f"V{k}", f"{t}N", f"{t}D")
        b.norm(f"V{k}")
        return "number"

    if op in ("add", "sub"):
        return finish(b.add(num(ins[0]), num(ins[1]),
                            "+" if op == "add" else "-"))
    if op == "mul":
        return finish(b.mul(num(ins[0]), num(ins[1])))
    if op == "div":
        return finish(b.div(num(ins[0]), num(ins[1])))
    if op == "pow":
        return finish(b.powi(num(ins[0]), int(s.detail["exponent"])))
    if read and fm.ON and op == "fold" and s.detail.get("missing") and \
            fm.handles(s):
        # a fold with declared holes: the fold machine reads every hole as
        # an absence before it counts (Phase 160)
        got = fm.compute(b, s, steps, pairs, files)
        if got == "number":
            b.norm(f"V{k}")
        return got
    if op == "mean" or (op == "fold" and s.detail.get("fn") in ("sum", "mean")
                        and _exact_fold(s)):
        acc = b.const(Fraction(0))
        for j in ins:
            acc = b.add(acc, num(j))
        if op == "mean" or s.detail.get("fn") == "mean":
            acc = b.div(acc, b.const(Fraction(len(ins))))
        return finish(acc)
    if op == "si":
        return finish(b.scale(num(ins[0]), Fraction(str(s.detail["factor"])),
                              Fraction(str(s.detail.get("offset", "0")))))
    if op == "unit_out":
        return finish(b.scale(num(ins[0]),
                              1 / Fraction(str(s.detail["factor"])),
                              Fraction(0)))
    if op == "compare":
        sym = s.detail["symbol"]
        b.sign(num(ins[0]), num(ins[1]), "XC")
        test = {">": "GTR", "<": "LSS", "=": "EQU"}[sym]
        b.lines += [f"SET S{k}=False", f"IF %XC% {test} 0 SET S{k}=True"]
        return "verdict"
    if op == "axiom":
        return finish(_axiom(b, s, pairs, roots=tm.ON and read))
    if read:
        from . import carried_read as cr
        got = cr.compute(b, s, steps, pairs, verdicts)
        if got is not None:
            if got == "number":
                b.norm(f"V{k}")
            return got
        if fm.ON and op == "fold":
            got = fm.compute(b, s, steps, pairs, files)
            if got == "number":
                b.norm(f"V{k}")
            return got
        if tm.ON:
            if op == "planned" and tm.handles(s):
                r = tm._recompute(s)
                if r is not None and r[0] == "verdict":
                    tm.verdict(b, s, steps, pairs, files)
                    return "verdict"
                return finish(tm.numeric(b, s, steps, pairs, files))
            if op in ("choose", "first"):
                for j in (ins[:1] if op == "choose" else ins[:-1]):
                    if not verdicts.get(j):
                        raise Carry("a test the machine does not hold")
                return finish(tm.choose_or_first(b, s, steps, pairs))
    raise Carry(op)


def _exact_fold(s) -> bool:
    d = s.detail
    if d.get("bounds") or str(d.get("bounded")) == "True":
        return False
    return isinstance(s.value, Fraction)


def chain_program(chain, read: bool = False,
                  files: Optional[Mapping[str, Sequence[str]]] = None,
                  gate: bool = False
                  ) -> Tuple[List[str], Dict[int, str], Dict[str, Tuple[str, ...]]]:
    """``(lines, kinds, seed files)`` of a chain.  ``kinds[k]`` is
    ``computed``, ``read:register``, ``read:question`` or ``carried``.
    With ``gate`` every computed step is checked against the planner's claim
    (exit 1 at the first mismatch).  ``files`` are the seed files (in the
    reading mode the register files and ``q.txt``; built when ``None``)."""
    from . import tool_machine as tm
    steps = chain.steps
    b = Builder()
    if read:
        from . import carried_read as cr
        seed = dict(cr.seed_files(chain) if files is None else files)
    else:
        seed = dict(files or {})
    kinds: Dict[int, str] = {}
    pairs: Dict[int, str] = {}
    verdicts: Dict[int, bool] = {}
    b.lines.append(f"REM the stepwise chain, {len(steps)} steps, said as "
                   "GLM-BAT (GLM.PlannerLadder)")
    for s in steps:
        k = s.index
        numeric = isinstance(s.value, Fraction)
        text = None if numeric else _render(s.value)
        if text is not None and not _sayable(text):
            raise bm.BatchError("SYNTAX", f"step {k}: a value GLM-BAT cannot "
                                          f"carry: {text!r}")
        mark = len(b.lines)
        kind = None
        if read:
            from . import carried_read as cr
            got = cr.read_lines(b, s, seed)
            if got is not None:
                kind = got
                if numeric:
                    _number_pair(b, k, s.value)
                else:
                    b.lines.append(f"SET S{k}={text}")
        if kind is None:
            try:
                b.lines.append(f"REM step {k}: {s.op}, computed")
                res = _compute(b, s, steps, pairs, verdicts, read, seed)
                if (res == "number") != numeric:
                    raise Carry("the machine's kind differs from the claim's")
                kind = "computed"
            except (Carry, tm.Unsaid, KeyError, ValueError, TypeError,
                    IndexError, ZeroDivisionError):
                del b.lines[mark:]
                kind = "carried"
                b.lines.append(f"REM step {k}: {s.op}, carried as data")
                if numeric:
                    _number_pair(b, k, s.value)
                else:
                    b.lines.append(f"SET S{k}={text}")
        kinds[k] = kind
        if numeric:
            pairs[k] = f"V{k}"
            _write_number(b, k, f"V{k}")
        else:
            verdicts[k] = kind == "computed" or kind.startswith("read")
            _write_text(b, k)
        if gate and kind == "computed":
            _gate(b, k, s.value)
    b.lines.append("EXIT /B 0")
    if "NORM" in b.subs:
        b.lines.extend(NORM_LINES)
    b.lines.extend(tm.subroutines(b))
    from . import fold_machine as fm
    b.lines.extend(fm.subroutines(b))
    lines = [bm.render_line(bm.parse_line(x)) for x in b.lines]
    return lines, kinds, seed


# ---------------------------------------------------------------------------
# running it
# ---------------------------------------------------------------------------

def _run(lines: Sequence[str], files: Mapping[str, Sequence[str]]) -> bm.Run:
    return bm.run_program(bm.parse_program(list(lines)), None, files, (),
                          budget=BUDGET, inert=False, jump=False)


def run_pipeline(stages: Sequence[Tuple[str, Sequence[str]]],
                 files: Mapping[str, Sequence[str]],
                 rollback: bool = True) -> Dict[str, object]:
    """:func:`batch_machine.run_pipeline` with this module's stage budget
    (Phase 160): stop at the first stage whose exit code is not 0; with
    ``rollback`` a failed pipeline restores the files it started from."""
    start = {k: tuple(v) for k, v in files.items()}
    current: Dict[str, Tuple[str, ...]] = dict(start)
    dirs: Tuple[str, ...] = ()
    passed: List[str] = []
    failed: Optional[str] = None
    for name, lines in stages:
        r = bm.run_program(bm.parse_program(list(lines)), None, current, dirs,
                           budget=BUDGET, inert=False, jump=False)
        if not r.halted:
            failed = name
            break
        current, dirs = r.files, r.dirs
        if r.exit_code != 0:
            failed = name
            break
        passed.append(name)
    promoted = failed is None
    if not promoted and rollback:
        current, dirs = dict(start), ()
    return {"promoted": promoted, "passed": passed, "failed_at": failed,
            "files": current, "dirs": dirs}


def _stages(ladder: Ladder) -> List[Tuple[str, List[str]]]:
    return [("check", list(ladder.gated)),
            ("promote", [f"COPY {ladder.last} answer.txt"])]


def _say(lines: Sequence[str]) -> bool:
    from . import batch_speech as bs
    english = " ".join(bs.say_program(bm.parse_program(list(lines))))
    try:
        back = bs.read_english(english)
    except bm.BatchError:
        return False
    return list(back) == list(lines)


def build(chain, read: bool = False,
          files: Optional[Mapping[str, Sequence[str]]] = None,
          say: bool = True) -> Ladder:
    """The ladder of a chain: said, run, drift and the gated pipeline."""
    desired = {file_of(s.index): (_render(s.value),) for s in chain.steps}
    try:
        lines, kinds, seed = chain_program(chain, read, files)
        gated, _k, _s = chain_program(chain, read, seed, gate=True)
    except bm.BatchError as e:
        return Ladder(chain.question, (), (), {}, dict(files or {}), desired,
                      read, error=str(e))
    lad = Ladder(chain.question, tuple(lines), tuple(gated), kinds,
                 {k: tuple(v) for k, v in seed.items()}, desired, read)
    if say:
        lad.said = _say(lines)
    try:
        lad.run = _run(lines, lad.seed)
    except bm.BatchError as e:
        lad.error = str(e)
        return lad
    lad.drift = bm.drift(desired, lad.run.files)
    try:
        lad.pipeline = run_pipeline(_stages(lad), lad.seed)
    except bm.BatchError as e:
        lad.error = str(e)
    return lad


def check_chain(chain, say: bool = True, read: bool = False,
                files: Optional[Mapping[str, Sequence[str]]] = None,
                ladder: bool = False) -> Dict[str, object]:
    """The machine's verdict on a chain.

    ``status``/``exit`` of the run, ``machine_steps``, ``lines``, ``said``
    (the program said as English reads back to the identical lines; ``None``
    when not asked), ``drift`` and ``first_drift``, ``promoted`` (the gated
    pipeline), ``rolled_back`` (a failed pipeline left exactly the seed
    files), the step indices ``computed``, ``read_register``,
    ``read_question`` and ``carried``, and ``admitted``: halted with exit
    code 0, no drift and promoted.  ``ladder=True`` adds the
    :class:`Ladder` itself under ``"ladder"``."""
    lad = build(chain, read, files, say)
    run = lad.run
    pipe = lad.pipeline
    status = run.status if run is not None else "refused"
    out: Dict[str, object] = {
        "status": status,
        "exit": run.exit_code if run is not None else None,
        "machine_steps": run.steps if run is not None else 0,
        "lines": len(lad.lines),
        "said": lad.said,
        "drift": list(lad.drift),
        "first_drift": _first_drift(lad.drift),
        "promoted": bool(pipe.get("promoted")),
        "failed_at": pipe.get("failed_at"),
        "rolled_back": (not pipe.get("promoted")) and bool(pipe) and
        {k: tuple(v) for k, v in pipe.get("files", {}).items()} == lad.seed,
        "computed": list(lad.indices("computed")),
        "read_register": list(lad.indices("read:register")),
        "read_question": list(lad.indices("read:question")),
        "carried": list(lad.indices("carried")),
        "error": lad.error,
    }
    out["admitted"] = (status == "halted" and out["exit"] == 0 and
                       not lad.drift and out["promoted"] and not lad.error)
    if ladder:
        out["ladder"] = lad
    return out


def gate(chain, read: bool = False,
         files: Optional[Mapping[str, Sequence[str]]] = None
         ) -> Dict[str, object]:
    """The gate the answering path puts on an answered chain
    (``stepwise._ladder_gate``, Phases 151 and 153): the chain is kept only
    when the machine's run halts with exit code 0, leaves no drift and the
    gated pipeline promotes; otherwise ``refusal`` is :data:`REFUSAL` and
    ``reason`` says where the machine disagrees.  ``ladder`` is what goes to
    the steps and the payload (never to the answer text)."""
    c = check_chain(chain, say=False, read=read, files=files, ladder=True)
    if c["admitted"]:
        reason = ""
    else:
        parts = []
        if c["error"]:
            parts.append(str(c["error"]))
        if c["status"] != "halted" or c["exit"] != 0:
            parts.append(f"the run {c['status']} with exit code {c['exit']}")
        if c["first_drift"] is not None:
            parts.append(f"the first drift is step {c['first_drift']}")
        elif c["drift"]:
            parts.append("drift: " + ", ".join(c["drift"]))
        if not c["promoted"]:
            parts.append(f"the gated pipeline did not promote (failed at "
                         f"{c['failed_at']}; rolled back)")
        reason = "the batch machine disagrees with the chain: " + \
            "; ".join(parts)
    return {"admitted": c["admitted"],
            "refusal": "" if c["admitted"] else REFUSAL,
            "reason": reason, "ladder": c["ladder"], "check": c}


def _first_drift(drift: Sequence[str]) -> Optional[int]:
    ks = sorted(int(p[1:-4]) for p in drift if re.fullmatch(r"s\d+\.txt", p))
    return ks[0] if ks else None


# ---------------------------------------------------------------------------
# what GLM.py prints, and column 3
# ---------------------------------------------------------------------------

def describe(ladder) -> Dict[str, str]:
    """The ladder in words: the program line, its lines, the drift and the
    pipeline (``GLM.py``'s ``MACHINE`` block)."""
    if isinstance(ladder, Mapping):
        ladder = ladder.get("ladder", ladder)
    run = ladder.run
    kinds = list(ladder.kinds.values())
    counts = ", ".join(f"{kinds.count(k)} {k.split(':')[-1] if ':' in k else k}"
                       for k in ("computed", "read:register",
                                 "read:question", "carried")
                       if kinds.count(k))
    if run is None:
        head = f"GLM-BAT: not run ({ladder.error or 'not said'})"
    else:
        head = (f"GLM-BAT: {len(ladder.lines)} lines, {run.steps} machine "
                f"steps, {run.status} with exit code {run.exit_code} "
                f"({counts})")
    drift = "drift: none" if not ladder.drift else \
        "drift: " + ", ".join(ladder.drift)
    p = ladder.pipeline
    pipe = ("pipeline: promoted" if p.get("promoted") else
            f"pipeline: not promoted (failed at {p.get('failed_at')}; "
            f"rolled back)") if p else "pipeline: not run"
    return {"program": head, "program_lines": "\n".join(ladder.lines),
            "drift": drift, "pipeline": pipe}


def column3_scripts(chain, ladder) -> Dict[str, Tuple[str, Dict[str, object]]]:
    """The two column-3 scripts of a ladder: the run claim and the pipeline
    claim, each re-derived by GLM-BAT's second interpreter given the same
    seed files (``batch_speech.CHECKER``)."""
    from . import batch_speech as bs
    if isinstance(ladder, Mapping):
        ladder = ladder.get("ladder", ladder)
    run = ladder.run
    claim = {"kind": "run", "out": list(run.out), "err": list(run.err),
             "exit": run.exit_code, "steps": run.steps,
             "files": {k: list(v) for k, v in sorted(run.files.items())},
             "dirs": list(run.dirs), "values": {}}
    p = ladder.pipeline
    pclaim = {"kind": "pipeline",
              "stages": [[n, list(x)] for n, x in _stages(ladder)],
              "rollback": True, "promoted": bool(p.get("promoted")),
              "failed_at": p.get("failed_at"),
              "files": {k: list(v) for k, v in
                        sorted(p.get("files", {}).items())}}
    return {
        "run": (bs.column3_script(list(ladder.lines), claim, {},
                                  ladder.seed), claim),
        "pipeline": (bs.column3_script([], pclaim, {}, ladder.seed), pclaim),
    }


def column3_mutants(ladder) -> Dict[str, Tuple[str, Dict[str, object]]]:
    """The two declared mutants: the run claim with its last file altered,
    the pipeline claim with its promotion flipped."""
    from . import batch_speech as bs
    scripts = column3_scripts(None, ladder)
    claim = json.loads(json.dumps(scripts["run"][1]))
    last = ladder.last
    claim["files"][last] = [x + "0" for x in claim["files"].get(last, [])] \
        or ["0"]
    pclaim = json.loads(json.dumps(scripts["pipeline"][1]))
    pclaim["promoted"] = not pclaim["promoted"]
    return {
        "run": (bs.column3_script(list(ladder.lines), claim, {},
                                  ladder.seed), claim),
        "pipeline": (bs.column3_script([], pclaim, {}, ladder.seed), pclaim),
    }


# ---------------------------------------------------------------------------
# lies
# ---------------------------------------------------------------------------

_FLIP = {"True": "False", "False": "True", "prime": "not prime",
         "not prime": "prime"}


def value_lie(step) -> Optional[object]:
    """A step's claim altered: a number raised by one, a verdict flipped, a
    row swapped for the other row of a comparison; ``None`` when there is no
    declared alteration."""
    v = step.value
    if isinstance(v, Fraction):
        return v + 1
    t = _render(v)
    if t in _FLIP:
        return _FLIP[t]
    rows = _literal(step.detail.get("rows")) if hasattr(step, "detail") \
        else None
    if isinstance(rows, (list, tuple)) and len(rows) == 2:
        if t == rows[0]:
            return str(rows[1])
        if t == rows[1]:
            return str(rows[0])
        return str(rows[0])
    return None


def lie_chain(chain, k: int, value: object):
    """The chain with the claim of step ``k`` replaced (the downstream claims
    left honest)."""
    from .stepwise_script import Chain
    steps = tuple(replace(s, value=value) if s.index == k else s
                  for s in chain.steps)
    return Chain(chain.question, steps, chain.kind, chain.notes)

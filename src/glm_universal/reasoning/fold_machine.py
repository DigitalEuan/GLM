"""``glm_universal.reasoning.fold_machine`` -- the machine sorts (Phase 160).

*Created 31 October 2026.*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from MASTER_PLAN.md (Phase 160), the
row of tests/README.md for test_fold_machine.py, the handler ``_fold_machine``
of tools.py, studies/CARRIED_READ_STUDY.md §7.2 and the docstring of
reasoning/tool_machine.py.  studies/FOLD_MACHINE_STUDY.md was lost; nothing
here relies on a figure only that document held.*

Phase 153 left 48 folds of the stepwise planner's answered chains carried:
the order folds (median, quartiles, the ``k``-th largest or smallest), ranks,
top rows and the folds bounded by holes.  This module has GLM-BAT compute
each of them **by counting**, in the reading mode of
:func:`planner_ladder.chain_program`:

* **An order statistic as the reading whose window holds the position.**
  For the reading ``x`` at a position ``q`` of the sorted readings the
  window is ``L = #{readings < x}``, ``E = #{readings <= x}``; ``x`` is the
  ``q``-th smallest exactly when ``L <= q < E``
  (``GLM.FoldMachine.kth_window``, ``window_unique``).  The program
  *offers* the reading (a witness the machine does not trust) and the
  machine counts both windows and stops (exit 2) unless the position is in
  it.  :data:`WITNESS_SHIFT` rotates the offered witnesses, so a measurement
  can check that a wrong witness stops the run and never writes a wrong
  value.
* **A rank** is ``1 + #{readings > x}``, counted.
* **The top rows**: each row's stable position (rows before it, ties in the
  register's order: ``stablePos_lt``, ``stablePos_tie``) counted; a tie
  across the boundary of the top stops the run (the planner refuses it).
* **Holes read as absences.**  A row the fold declares missing must have no
  entry: ``FIND "@row.field=" < reg/<table>.txt`` must fail
  (``hole_needle_iff``); a declared hole with a reading stops the run.
* **Bounds**: a fold over a column with holes is the interval every
  completion lands in (``GLM.HoleBounds``), its two ends counted the same
  way; sums, means and parity counts with a declared range by the range.

Exactness
---------
Integers, :class:`fractions.Fraction` and strings only.
"""

from __future__ import annotations

import ast
import re
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = ["ON", "WITNESS_SHIFT", "LEAN_FILE", "LEAN_THEOREMS", "compute",
           "subroutines", "window", "stable_positions", "handles"]

#: The round's switch: off carries the folds as Phase 153 did.
ON: bool = True

#: Rotation of the offered witnesses (0: the honest witness).
WITNESS_SHIFT: int = 0

LEAN_FILE: str = "FoldMachine.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "kth_lt_iff", "kth_eq_iff", "kth_window", "window_unique",
    "stablePos_lt", "stablePos_strict", "stablePos_tie",
    "stablePos_injective", "hole_needle_iff", "absent_iff")


def _literal(x):
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except (ValueError, SyntaxError):
            return x
    return x


def _true(x) -> bool:
    return str(x) == "True" or x is True


def window(values: Sequence[Fraction], x: Fraction) -> Tuple[int, int]:
    """``(L, E)``: the readings below ``x`` and at most ``x``."""
    return (sum(1 for v in values if v < x), sum(1 for v in values if v <= x))


def stable_positions(values: Sequence[Fraction], symbol: str) -> List[int]:
    """Each reading's stable position, first by value (``>``: largest
    first), ties in the given order."""
    out = []
    for j, v in enumerate(values):
        before = sum(1 for i, w in enumerate(values)
                     if (w > v if symbol == ">" else w < v)
                     or (w == v and i < j))
        out.append(before)
    return out


def handles(step) -> bool:
    """Is ``step`` a fold this module computes (switch on)?"""
    if not ON or step.op != "fold":
        return False
    d = step.detail
    fn = str(d.get("fn"))
    from .stepwise_script import is_order
    return fn in ("rank", "top") or is_order(fn) or bool(d.get("bounds")) or \
        _true(d.get("present")) or _true(d.get("bounded"))


def subroutines(b) -> List[str]:
    return []


# ---------------------------------------------------------------------------
# lines
# ---------------------------------------------------------------------------

def _count(b, ins: Sequence[int], pairs: Mapping[int, str], w: str,
           low: str, high: str) -> None:
    """``low`` = readings below the pair ``w``, ``high`` = at most it."""
    b.lines += [f"SET /A {low}=0", f"SET /A {high}=0"]
    for j in ins:
        t = pairs[j]
        b.lines += [f"SET /A OX={t}N*{w}D-{w}N*{t}D",
                    f"IF %OX% LSS 0 SET /A {low}={low}+1",
                    f"IF %OX% LEQ 0 SET /A {high}={high}+1"]


def _witness(b, ins: Sequence[int], pairs: Mapping[int, str],
             order: Sequence[int], q: int) -> str:
    """The reading at sorted position ``q``: offered, then checked by its
    window.  Returns the pair holding it."""
    m = len(order)
    j = order[(q + WITNESS_SHIFT) % m]
    t = b.pair()
    b.set_pair(t, f"{pairs[j]}N", f"{pairs[j]}D")
    _count(b, ins, pairs, t, "OL", "OE")
    b.lines += [f"IF %OL% GTR {q} EXIT /B 2", f"IF %OE% LEQ {q} EXIT /B 2"]
    return t


def _absent(b, table: str, field: str, missing: Sequence[str],
            files: Mapping[str, Sequence[str]]) -> None:
    from . import register_files as rf
    from .tool_machine import Unsaid
    path = rf.table_path(table)
    if path not in files:
        raise Unsaid("the register file is not given to the machine")
    for row in missing:
        if not (rf.key_ok(str(row)) and rf.key_ok(str(field))):
            raise Unsaid("a hole GLM-BAT cannot name")
        b.lines.append(f'FIND "@{row}.{field}=" < {path} && EXIT /B 2')


def _avg(b, ps: Sequence[str]) -> str:
    acc = ps[0]
    for p in ps[1:]:
        acc = b.add(acc, p)
    if len(ps) > 1:
        acc = b.div(acc, b.const(Fraction(len(ps))))
    return acc


def _value(b, k: int, lo: str, hi: str, claim) -> str:
    """Write the fold's value: one number when the ends meet, else
    ``between lo and hi``; the claim's kind decides which is honest, and
    the other stops the run."""
    if isinstance(claim, Fraction):
        b.lines += [f"SET /A OZ={lo}N*{hi}D-{hi}N*{lo}D",
                    "IF %OZ% NEQ 0 EXIT /B 2"]
        b.set_pair(f"V{k}", f"{lo}N", f"{lo}D")
        return "number"
    b.norm(lo)
    b.norm(hi)
    b.lines += [f"SET /A OZ={lo}N*{hi}D-{hi}N*{lo}D",
                "IF %OZ% EQU 0 EXIT /B 2",
                f"SET WA=%{lo}N%", f"IF %{lo}D% NEQ 1 SET WA=%{lo}N%/%{lo}D%",
                f"SET WB=%{hi}N%", f"IF %{hi}D% NEQ 1 SET WB=%{hi}N%/%{hi}D%",
                f"SET S{k}=between %WA% and %WB%"]
    return "verdict"


def _stop(b, claim) -> str:
    """An impossible shape: the machine stops (exit 2) and writes nothing.
    Returns the claim's kind, so the step counts as computed, not carried."""
    b.lines.append("EXIT /B 2")
    return "number" if isinstance(claim, Fraction) else "verdict"


def compute(b, s, steps, pairs: Mapping[int, str],
            files: Mapping[str, Sequence[str]]) -> str:
    """Lines computing a fold by counting; ``"number"`` (``V<k>``) or
    ``"verdict"`` (``S<k>``, a text value).  Raises
    :class:`tool_machine.Unsaid` when the fold is not one this module
    computes or its inputs are not held."""
    from .tool_machine import Unsaid
    from .stepwise_script import order_positions, is_order
    if not handles(s):
        raise Unsaid("not a fold the machine sorts")
    d = s.detail
    k = s.index
    fn = str(d.get("fn"))
    ins = tuple(int(j) for j in s.inputs)
    if any(j not in pairs for j in ins) or not ins:
        raise Unsaid("a reading the machine does not hold as a number")
    vals = [steps[j - 1].value for j in ins]
    missing = [str(x) for x in (_literal(d.get("missing", ())) or ())]
    bounded = _true(d.get("bounded"))
    holes = len(missing) if bounded else 0
    if missing and (bounded or _true(d.get("present"))):
        _absent(b, str(d.get("table")), str(d.get("field")), missing, files)
    claim = s.value
    if d.get("bounds"):
        rng = _literal(d.get("range"))
        if fn in ("odd", "even"):
            want = 1 if fn == "odd" else 0
            b.lines.append("SET /A XN=0")
            for j in ins:
                t = pairs[j]
                b.lines += [f"IF %{t}D% NEQ 1 EXIT /B 2",
                            f"SET /A XP={t}N-({t}N/2)*2",
                            "IF %XP% LSS 0 SET /A XP=0-XP",
                            f"IF %XP% EQU {want} SET /A XN=XN+1"]
            lo, hi = b.pair(), b.pair()
            b.set_pair(lo, "XN", "1")
            b.set_pair(hi, f"XN+{holes}", "1")
            return _value(b, k, lo, hi, claim)
        if fn in ("sum", "mean") and (isinstance(rng, (list, tuple))
                                       or holes == 0):
            r0, r1 = (Fraction(str(x)) for x in rng) \
                if isinstance(rng, (list, tuple)) else (Fraction(0),
                                                         Fraction(0))
            total = b.const(Fraction(0))
            for j in ins:
                total = b.add(total, pairs[j])
            lo = b.add(total, b.const(holes * r0))
            hi = b.add(total, b.const(holes * r1))
            if fn == "mean":
                n = b.const(Fraction(len(ins) + holes))
                lo, hi = b.div(lo, n), b.div(hi, n)
            return _value(b, k, lo, hi, claim)
        if fn in ("sum", "mean"):
            # a hole with no declared range: no bound exists -- stop
            return _stop(b, claim)
        raise Unsaid("a bound the machine does not count")
    if fn == "top":
        if bounded:
            raise Unsaid("top rows over holes")
        kk = int(str(d.get("k")))
        symbol = str(d.get("symbol"))
        names = _literal(d.get("names"))
        rows = [steps[j - 1].detail.get("row") for j in ins]
        if not isinstance(names, Mapping):
            raise Unsaid("top rows")
        if kk < 1 or kk > len(ins):
            return _stop(b, claim)
        texts = [str(names.get(r, "")) for r in rows]
        if any(not t or set(t) & set('<>|&%"^') or t != t.strip()
               for t in texts):
            raise Unsaid("a row name GLM-BAT cannot carry")
        test = "GTR" if symbol == ">" else "LSS"
        # the program offers the rows of the top, in order; the machine
        # counts each one's stable position (rows first by value, ties in
        # the register's order) and checks it is the place offered
        pos = stable_positions(vals, symbol)
        order = [a for _p, a in sorted((p, a) for a, p in enumerate(pos))]
        n = len(ins)
        names_out = []
        for p in range(kk):
            a = order[(p + WITNESS_SHIFT) % n]
            ta = pairs[ins[a]]
            b.lines.append("SET /A OP=0")
            for c, jc in enumerate(ins):
                if c == a:
                    continue
                tc = pairs[jc]
                b.lines.append(f"SET /A OX={tc}N*{ta}D-{ta}N*{tc}D")
                b.lines.append(f"IF %OX% {test} 0 SET /A OP=OP+1")
                if c < a:
                    b.lines.append("IF %OX% EQU 0 SET /A OP=OP+1")
            b.lines.append(f"IF %OP% NEQ {p} EXIT /B 2")
            names_out.append(texts[a])
            if p == kk - 1 and kk < n:
                # no tie across the boundary: exactly k rows at least as
                # far up as the last row of the top
                b.lines.append("SET /A OQ=0")
                for c, jc in enumerate(ins):
                    tc = pairs[jc]
                    b.lines += [f"SET /A OX={tc}N*{ta}D-{ta}N*{tc}D",
                                f"IF %OX% {test} 0 SET /A OQ=OQ+1",
                                "IF %OX% EQU 0 SET /A OQ=OQ+1"]
                b.lines.append(f"IF %OQ% NEQ {kk} EXIT /B 2")
        b.lines.append(f"SET S{k}={', '.join(names_out)}")
        return "verdict"
    if fn == "rank":
        row = d.get("row")
        own = next((j for j in ins if steps[j - 1].detail.get("row") == row),
                   None)
        if own is None:
            raise Unsaid("the ranked row has no reading")
        t = pairs[own]
        b.lines.append("SET /A OR=1")
        for j in ins:
            u = pairs[j]
            b.lines += [f"SET /A OX={u}N*{t}D-{t}N*{u}D",
                        "IF %OX% GTR 0 SET /A OR=OR+1"]
        lo, hi = b.pair(), b.pair()
        b.set_pair(lo, "OR", "1")
        b.set_pair(hi, f"OR+{holes}", "1")
        return _value(b, k, lo, hi, claim)
    if is_order(fn):
        n = len(ins) + holes
        ks = order_positions(fn, n)
        if ks is None or any(q - holes < 0 or q >= len(ins) for q in ks):
            # an impossible shape (a position past the readings) stops the
            # machine; it is never carried (the amendment M4')
            return _stop(b, claim)
        order = sorted(range(len(ins)), key=lambda i: vals[i])
        order = [ins[i] for i in order]
        lows = [_witness(b, ins, pairs, order, q - holes) for q in ks]
        highs = [_witness(b, ins, pairs, order, q) for q in ks] \
            if holes else lows
        return _value(b, k, _avg(b, lows), _avg(b, highs), claim)
    if fn in ("sum", "mean", "odd", "even") and not bounded:
        if fn in ("odd", "even"):
            want = 1 if fn == "odd" else 0
            b.lines.append("SET /A XN=0")
            for j in ins:
                t = pairs[j]
                b.lines += [f"IF %{t}D% NEQ 1 EXIT /B 2",
                            f"SET /A XP={t}N-({t}N/2)*2",
                            "IF %XP% LSS 0 SET /A XP=0-XP",
                            f"IF %XP% EQU {want} SET /A XN=XN+1"]
            b.set_pair(f"V{k}", "XN", "1")
            return "number"
        total = b.const(Fraction(0))
        for j in ins:
            total = b.add(total, pairs[j])
        if fn == "mean":
            total = b.div(total, b.const(Fraction(len(ins))))
        b.set_pair(f"V{k}", f"{total}N", f"{total}D")
        return "number"
    raise Unsaid("a fold the machine does not sort")

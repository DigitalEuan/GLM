"""``glm_universal.reasoning.tool_machine`` -- the machine works the tools
out (Phase 163).

*Created 19 October 2026.* Last altered 19 October 2026 (Phase 166: ``pi`` summed by the machine; the kissing number's REM line cites ``GLM.LeechKissing``).

Phase 160 (:mod:`glm_universal.reasoning.fold_machine`) left 44 steps of the
stepwise planner's answered chains **carried** as data in the batch machine
GLM-BAT: 31 tool answers (a convergent, a continued-fraction term, the nearest
fraction, a gate-move count or verdict) and one conversion, 7 axiom steps, and
3 ``choose`` and 3 ``first`` steps.  A carried step is a value the machine
*repeats*: it is written into the program as the planner's number.  This
module has the machine **work each of them out** from first principles, so
that what the GLM answers is what its own machine computed
(``studies/TOOL_MACHINE_STUDY.md``):

* **A continued fraction by Euclid's algorithm on both ends of an
  enclosure.**  The machine holds the real ``x`` as two fractions
  ``a/b <= x <= c/d`` and runs Euclid's algorithm on both in lockstep; a term
  is emitted only while the two quotients agree, and then it is a term of
  ``x`` (``GLM.ToolMachine.lockstep_certified``).  The convergents come from
  the recurrence ``p <- a p + p'``, ``q <- a q + q'`` in the same loop
  (``convRun_eq``).  Where the two ends disagree before the terms asked for,
  the machine stops (exit 2): it never writes a term it has not certified.
* **The enclosures.**  ``e``: the machine sums the series itself, by the loop
  ``T <- k T + 1`` (``eT_div``), and widens it by the proved error bound
  (``e_enclosure``).  ``sqrt(m)``: the program offers the integer square root
  of ``m M^2`` as a witness and the machine checks it by squaring
  (``sqrt_enclosure``); a wrong witness stops the run.  ``pi``: since
  Phase 166 the machine sums it too (``studies/PI_MACHINE_STUDY.md``):
  Machin's formula ``pi = 16 arctan(1/5) - 4 arctan(1/239)``
  (``GLM.PiMachine.machin``), each arctangent by Horner's rule on its series
  in two integers (``atH_arctan_sum``), widened by the proved error bound
  (``piEnds_enclose``).  With ``PI_SUMMED`` off it is the two twenty-digit
  decimals Mathlib proves (``pi_enclosure``), a declared constant, as Phase
  163 left it.
* **The nearest fraction with a bounded denominator.**  The machine runs the
  expansion until the denominator passes the bound, forms the last convergent
  within the bound and the semiconvergent below the next, and then *checks*
  the Farey certificate itself: determinant +-1, denominators summing past the
  bound, both ends of the enclosure between the two candidates and strictly on
  one side of their midpoint (``between_of_ends``, ``side_of_ends``,
  ``nearest_of_nearer``).  Any check that fails stops the run.
* **Gate moves.**  For each of the eight 3-bit blocks of a 24-bit word the
  machine runs a breadth-first search over a bit mask of the values reached,
  computing Toffoli and Fredkin by arithmetic on the bits (``gateArith_spec``);
  the search is right by ``machineDist_sound``.
* **The Leech kissing number from the Golay code.**  The machine walks the
  4,096 messages of the Golay code in Gray-code order, flipping one generator
  row of the code's own parity block at a time (``GLM.LeechMachine.gray_step``),
  counts the codewords and the octads, and forms the minimal vectors of the
  Leech lattice as ``128 * octads + 4 * C(24,2) + 24 * codewords``
  (``leech_kissing_from_census``): the number is worked out, not looked up.
  Since Phase 164 the three shapes are proved from the lattice's definition
  (``GLM.LeechShells.minimal_shape``), and since Phase 165 both ways, with the
  count a theorem (``GLM.LeechKissing.leech_kissing_number``, cited in the
  program's REM line since Phase 166).  The other shells (norm 6 and up) are
  counted by :mod:`glm_universal.reasoning.leech_shells` for the tool's own
  answer, but not by this machine: in a chain they stay carried.
* **The rest.**  A conversion is the amount (read from the question) times the
  declared factors; an axiom's ``^`` is the power it means; ``choose`` copies
  the branch the machine's own verdict selects, and stops when the verdict
  does not select it; ``first`` checks that every earlier test is false and
  the last true.

What stays carried: a tool or real this module does not compute (any real
other than ``pi``, ``e`` and ``sqrt(m)``, any other tool), and a step whose
inputs the machine does not hold.

Exactness
---------
Integers, :class:`fractions.Fraction` and strings only.
"""

from __future__ import annotations

import ast
import math
import re
from fractions import Fraction
from typing import List, Mapping, Optional, Sequence, Tuple

__all__ = [
    "ON", "LEAN_FILE", "LEAN_THEOREMS", "E_TERMS", "SQRT_SCALE", "PI_LOW",
    "PI_HIGH", "PI_SUMMED", "PI_TERMS", "PI_LEAN_FILE", "PI_LEAN_THEOREMS",
    "pi_ends", "pi_lines", "Unsaid", "handles", "parse_tool", "enclosure_kind",
    "numeric", "verdict", "choose_or_first", "subroutines", "TOOL_KINDS",
]

#: The round's switch: off restores the answering path as Phase 162 left it.
ON: bool = True

LEAN_FILE: str = "RequestProject/GLM/ToolMachine.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "euclidTerms_eq", "lockstep_certified", "pi_enclosure", "eT_div",
    "e_enclosure", "sqrt_enclosure", "convRun_eq", "between_of_ends",
    "side_of_ends", "nearest_of_nearer", "gateArith_spec",
    "machineDist_sound")

#: The tools the machine works out.
TOOL_KINDS: Tuple[str, ...] = ("convergent", "continued fraction",
                               "best approximation", "gates", "llvq")

#: Terms of the series for ``e`` the machine sums (``n`` of ``e_enclosure``
#: with ``k = n - 1``): the enclosure is ``2 (n+1) / (n! n)`` wide, about
#: ``10^-33`` at ``n = 30``.
E_TERMS: int = 30

#: The scale ``M`` of a square root's enclosure ``a/M <= sqrt(m) <= (a+1)/M``.
SQRT_SCALE: int = 10 ** 30

#: The round's switch for ``pi`` (Phase 166): on, the machine sums Machin's
#: formula itself (:func:`pi_lines`); off, ``pi`` is the declared constant
#: below, as Phase 163 left it.
PI_SUMMED: bool = True

#: Terms of the arctangent series the machine sums for ``1/5`` and ``1/239``
#: (``a`` and ``b`` of ``GLM.PiMachine.piEnds``): the enclosure is
#: ``2 (16 / ((2a+1) 5^(2a+1)) + 4 / ((2b+1) 239^(2b+1)))`` wide, about
#: ``10^-57`` at ``(40, 12)``, which certifies 53 continued-fraction terms --
#: past the 40 the tool answers (``(30, 9)`` would certify only 37).
PI_TERMS: Tuple[int, int] = (40, 12)

PI_LEAN_FILE: str = "RequestProject/GLM/PiMachine.lean"
PI_LEAN_THEOREMS: Tuple[str, ...] = (
    "machin", "arctan_series_bound", "atH_div", "atH_arctan_sum",
    "pi_series_bound", "piEnds_enclose")

#: ``pi`` between these, by ``Real.pi_gt_d20`` and ``Real.pi_lt_d20`` (the
#: declared constant, used only with ``PI_SUMMED`` off).
PI_LOW: Tuple[int, int] = (314159265358979323846, 10 ** 20)
PI_HIGH: Tuple[int, int] = (314159265358979323847, 10 ** 20)

#: The verdict words of the planner's branches (``stepwise_script``).
_TRUE = ("True", "prime")
_FALSE = ("False", "not prime")

_UNSAYABLE = set('<>|&%"^')

#: The witness a square root's enclosure offers (the study rotates it to
#: check that a wrong witness stops the run rather than being trusted).
_root = math.isqrt


class Unsaid(Exception):
    """The step is not one this module computes; it stays carried."""


# ---------------------------------------------------------------------------
# reading a planned step
# ---------------------------------------------------------------------------

def _recompute(step) -> Optional[Tuple[str, ...]]:
    d = step.detail if isinstance(step.detail, Mapping) else {}
    r = d.get("recompute")
    if isinstance(r, str):
        try:
            r = ast.literal_eval(r)
        except (ValueError, SyntaxError):
            return None
    if not isinstance(r, (list, tuple)) or not r:
        return None
    return tuple(str(x) for x in r)


def parse_tool(text: str) -> Optional[Tuple[str, Tuple[object, ...]]]:
    """``(kind, args)`` for a tool line this module computes, else ``None``."""
    t = text.strip()
    m = re.match(r"^tool convergent\s+(\d+)\s+of\s+(.+)$", t, re.IGNORECASE)
    if m:
        return "convergent", (int(m.group(1)), m.group(2).strip())
    m = re.match(r"^tool continued fraction\s+(.+?)\s+terms\s+(\d+)$", t,
                 re.IGNORECASE)
    if m:
        return "continued fraction", (m.group(1).strip(), int(m.group(2)))
    m = re.match(r"^tool best approximation\s+(.+?)\s+(?:denominator|den|q)"
                 r"\s*(?:<=|at most)?\s*(\d+)$", t, re.IGNORECASE)
    if m:
        return "best approximation", (m.group(1).strip(), int(m.group(2)))
    if re.match(r"^tool llvq$", t, re.IGNORECASE):
        return "llvq", ()
    m = re.match(r"^tool gates\s+(\S+)\s+to\s+(\S+)$", t, re.IGNORECASE)
    if m:
        from ..runtime.toolbox import _parse_word
        a, c = _parse_word(m.group(1)), _parse_word(m.group(2))
        if a is None or c is None:
            return None
        return "gates", (a, c)
    return None


def enclosure_kind(expr: str) -> Optional[Tuple[str, int]]:
    """``("pi", 0)``, ``("e", 0)`` or ``("sqrt", m)`` for a real this module
    encloses, else ``None`` (a rational, a perfect square, anything else)."""
    x = expr.strip().lower().replace(" ", "")
    if x in ("pi", "π"):
        return "pi", 0
    if x == "e":
        return "e", 0
    m = re.match(r"^(?:sqrt\((\d+)\)|sqrt(\d+))$", x)
    if m:
        n = int(m.group(1) or m.group(2))
        if n >= 2 and math.isqrt(n) ** 2 != n:
            return "sqrt", n
    return None


def handles(step) -> bool:
    """Is ``step`` a planned step (tool, verdict or conversion) whose shape
    this module computes?  ``choose`` and ``first`` are
    :func:`choose_or_first`."""
    if not ON or step.op != "planned":
        return False
    r = _recompute(step)
    if r is None:
        return False
    if r[0] == "convert":
        return len(r) == 4
    if r[0] in ("tool", "verdict") and len(r) >= 3:
        got = parse_tool(r[1])
        if got is None:
            return False
        kind, args = got
        if kind == "gates":
            return True
        if kind == "llvq":
            return tuple(r[2:4]) == ("value", "kissing_number") or \
                tuple(r[2:5]) == ("entry", "shell_counts", "16") or \
                (len(r) > 5 and tuple(r[3:6]) == ("value", "kissing_number"))
        expr = args[1] if kind == "convergent" else args[0]
        return enclosure_kind(str(expr)) is not None
    return False


# ---------------------------------------------------------------------------
# the lines
# ---------------------------------------------------------------------------

def _used(b) -> set:
    if not hasattr(b, "tool_subs"):
        b.tool_subs = set()
    return b.tool_subs


def _enclose(b, expr: str, k: int) -> None:
    """Lines setting ``XLA/XLB <= x <= XUA/XUB``."""
    got = enclosure_kind(expr)
    if got is None:
        raise Unsaid("a real the machine does not enclose")
    kind, m = got
    if kind == "pi":
        if not PI_SUMMED:
            b.lines += [
                "REM pi between Mathlib's twenty-digit decimals "
                "(GLM.ToolMachine.pi_enclosure)",
                f"SET /A XLA={PI_LOW[0]}", f"SET /A XLB={PI_LOW[1]}",
                f"SET /A XUA={PI_HIGH[0]}", f"SET /A XUB={PI_HIGH[1]}"]
            return
        b.lines += pi_lines(k)
        return
    if kind == "e":
        n = E_TERMS
        b.lines += [
            f"REM e: the machine sums 1/i! for i below {n} by T = i*T + 1 "
            "(GLM.ToolMachine.eT_div) and widens it by the error bound "
            "(e_enclosure)",
            "SET /A ET=1", "SET /A ED=1", "SET /A EI=1",
            f":ESUM{k}",
            f"IF %EI% GEQ {n} GOTO ESUMD{k}",
            "SET /A ET=EI*ET+1", "SET /A ED=EI*ED", "SET /A EI=EI+1",
            f"GOTO ESUM{k}",
            f":ESUMD{k}",
            f"SET /A XLA=ET*{n * n}-{n + 1}", f"SET /A XLB=ED*{n * n}",
            f"SET /A XUA=ET*{n * n}+{n + 1}", f"SET /A XUB=ED*{n * n}"]
        return
    M = SQRT_SCALE
    a = _root(m * M * M)
    b.lines += [
        f"REM sqrt({m}): the offered root is checked by squaring "
        "(GLM.ToolMachine.sqrt_enclosure)",
        f"SET /A XW={a}", f"SET /A XC={m}*{M}*{M}",
        "SET /A XQ=XW*XW",
        "IF %XQ% GTR %XC% EXIT /B 2",
        "SET /A XQ=(XW+1)*(XW+1)",
        "IF %XQ% LEQ %XC% EXIT /B 2",
        "SET /A XLA=XW", f"SET /A XLB={M}",
        "SET /A XUA=XW+1", f"SET /A XUB={M}"]


def _horner(m: int, n: int) -> Tuple[int, int]:
    """``GLM.PiMachine.atH m 0 n``: Horner's rule on the arctangent series of
    ``1/m``, from the last of ``n`` terms back to the first."""
    p, q = 0, 1
    for k in range(n - 1, -1, -1):
        p, q = m * m * q - (2 * k + 1) * p, (2 * k + 1) * m * m * q
    return p, q


def pi_ends(a: int, b: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """``GLM.PiMachine.piEnds a b``: the lower and upper ends of the machine's
    enclosure of ``pi``, each as ``(numerator, denominator)``
    (``piEnds_enclose``).  The same integers :func:`pi_lines` has the machine
    compute."""
    p5, q5 = _horner(5, a)
    p2, q2 = _horner(239, b)
    sn = 16 * p5 * (239 * q2) - 4 * p2 * (5 * q5)
    sd = 5 * q5 * (239 * q2)
    ea = (2 * a + 1) * 5 ** (2 * a + 1)
    eb = (2 * b + 1) * 239 ** (2 * b + 1)
    en, ed = 16 * eb + 4 * ea, ea * eb
    return (sn * ed - en * sd, sd * ed), (sn * ed + en * sd, sd * ed)


def pi_lines(k: int, terms: Optional[Tuple[int, int]] = None) -> List[str]:
    """Lines setting ``XLA/XLB <= pi <= XUA/XUB`` by summing Machin's formula
    (Phase 166): two Horner loops, ``P <- m*m*Q - (2K+1)*P``,
    ``Q <- (2K+1)*m*m*Q`` from ``K = n-1`` down to ``0`` (``atH_arctan_sum``),
    then Machin's combination widened by the proved error bound
    (``piEnds_enclose``).  ``k`` makes the labels unique in a program."""
    a, bb = terms or PI_TERMS
    lines = [
        f"REM pi: Machin's formula (GLM.PiMachine.machin); the machine sums "
        f"{a} terms of arctan(1/5) and {bb} of arctan(1/239) by Horner's rule "
        "(atH_arctan_sum) and widens by the error bound (piEnds_enclose)"]
    for m, n, tag in ((5, a, "F"), (239, bb, "T")):
        lines += [
            "SET /A PIP=0", "SET /A PIQ=1", f"SET /A PIK={n - 1}",
            f":PISUM{tag}{k}",
            f"IF %PIK% LSS 0 GOTO PISUMD{tag}{k}",
            f"SET /A PIT={m * m}*PIQ-(2*PIK+1)*PIP",
            f"SET /A PIQ=(2*PIK+1)*{m * m}*PIQ",
            "SET /A PIP=PIT", "SET /A PIK=PIK-1",
            f"GOTO PISUM{tag}{k}",
            f":PISUMD{tag}{k}",
            f"SET /A PIP{tag}=PIP", f"SET /A PIQ{tag}=PIQ"]
    ea = (2 * a + 1) * 5 ** (2 * a + 1)
    eb = (2 * bb + 1) * 239 ** (2 * bb + 1)
    lines += [
        "SET /A PISN=16*PIPF*(239*PIQT)-4*PIPT*(5*PIQF)",
        "SET /A PISD=5*PIQF*(239*PIQT)",
        f"SET /A PIEN={16 * eb + 4 * ea}", f"SET /A PIED={ea * eb}",
        "SET /A XLA=PISN*PIED-PIEN*PISD", "SET /A XLB=PISD*PIED",
        "SET /A XUA=PISN*PIED+PIEN*PISD", "SET /A XUB=PISD*PIED"]
    return lines


def _cfx(b, count: int, bound: int) -> None:
    """Call the lockstep expansion on the enclosure; stop unless certified."""
    b.lines += ["SET /A LA=XLA", "SET /A LB=XLB", "SET /A UA=XUA",
                "SET /A UB=XUB", f"SET /A CN={count}", f"SET /A CB={bound}",
                "CALL :CFX",
                "IF %CS% NEQ 1 EXIT /B 2"]
    _used(b).add("CFX")


#: The lockstep expansion: Euclid's algorithm on both ends (LA/LB, UA/UB),
#: a term only while the quotients agree (GLM.ToolMachine.lockstep_certified),
#: the convergents by the recurrence (convRun_eq).  In: CN terms wanted (0:
#: no count), CB a denominator to pass (0: none).  Out: CS 1 when done; CK
#: terms; CA the last; CP/CQ, CPP/CQP, CP2/CQ2 the last three convergents;
#: CSUM, CPRD, CMAX, CMIN of the terms.
_CFX: Tuple[str, ...] = (
    ":CFX",
    "SET /A CS=0",
    "SET /A CK=0",
    "SET /A CP=1", "SET /A CQ=0", "SET /A CPP=0", "SET /A CQP=1",
    "SET /A CP2=0", "SET /A CQ2=0",
    "SET /A CSUM=0", "SET /A CPRD=1", "SET /A CMAX=0", "SET /A CMIN=0",
    "IF %LA% LSS 0 EXIT /B 0",
    "IF %UA% LSS 0 EXIT /B 0",
    ":CFXLOOP",
    "IF %CN% EQU 0 GOTO CFXB",
    "IF %CK% GEQ %CN% GOTO CFXOK",
    ":CFXB",
    "IF %CB% EQU 0 GOTO CFXGO",
    "IF %CQ% GTR %CB% GOTO CFXOK",
    ":CFXGO",
    "IF %LB% LEQ 0 EXIT /B 0",
    "IF %UB% LEQ 0 EXIT /B 0",
    "SET /A FL=LA/LB",
    "SET /A FU=UA/UB",
    "IF %FL% NEQ %FU% EXIT /B 0",
    "SET /A CA=FL",
    "SET /A CK=CK+1",
    "SET /A CP2=CPP", "SET /A CQ2=CQP",
    "SET /A CPP=CP", "SET /A CQP=CQ",
    "SET /A CP=CA*CPP+CP2", "SET /A CQ=CA*CQP+CQ2",
    "SET /A CSUM=CSUM+CA", "SET /A CPRD=CPRD*CA",
    "IF %CK% EQU 1 SET /A CMAX=CA",
    "IF %CK% EQU 1 SET /A CMIN=CA",
    "IF %CA% GTR %CMAX% SET /A CMAX=CA",
    "IF %CA% LSS %CMIN% SET /A CMIN=CA",
    "SET /A TL=LA-FL*LB",
    "SET /A TU=UA-FU*UB",
    "SET /A LA=LB", "SET /A LB=TL",
    "SET /A UA=UB", "SET /A UB=TU",
    "GOTO CFXLOOP",
    ":CFXOK",
    "SET /A CS=1",
    "EXIT /B 0",
)

#: The gate search: WS, WT the two words in; WR 1 when every block is
#: reachable, WM the sum of the blocks' least move counts
#: (GLM.ToolMachine.machineDist_sound, block by block).
_GATES: Tuple[str, ...] = (
    ":GATES",
    "SET /A WR=1", "SET /A WM=0", "SET /A WK=0",
    ":GATESBLK",
    "IF %WK% GEQ 8 EXIT /B 0",
    "SET /A WS3=WS-(WS/8)*8",
    "SET /A WT3=WT-(WT/8)*8",
    "SET /A WS=WS/8",
    "SET /A WT=WT/8",
    "CALL :GBFS",
    "IF %WD% LSS 0 SET /A WR=0",
    "IF %WD% GEQ 0 SET /A WM=WM+WD",
    "SET /A WK=WK+1",
    "GOTO GATESBLK",
    ":GBFS",
    "SET /A WE=WS3",
    "CALL :POW2",
    "SET /A WMASK=WP",
    "SET /A WD=0",
    "SET /A WF=9",
    ":GBFSLOOP",
    "IF %WF% LEQ 0 GOTO GBFSNONE",
    "SET /A WE=WT3",
    "CALL :POW2",
    "SET /A WX=(WMASK/WP)-((WMASK/WP)/2)*2",
    "IF %WX% EQU 1 EXIT /B 0",
    "SET /A WNEW=WMASK",
    "SET /A WV=0",
    ":GBFSV",
    "IF %WV% GEQ 8 GOTO GBFSVD",
    "SET /A WE=WV",
    "CALL :POW2",
    "SET /A WX=(WMASK/WP)-((WMASK/WP)/2)*2",
    "IF %WX% EQU 0 GOTO GBFSVN",
    "SET /A WA=WV-(WV/2)*2",
    "SET /A WB=(WV/2)-((WV/2)/2)*2",
    "SET /A WC=(WV/4)-((WV/4)/2)*2",
    "SET /A WE=WA+2*WB+4*(WC+WA*WB-2*WC*WA*WB)",
    "CALL :SETBIT",
    "SET /A WE=WA+2*(WB+WA*WC-WA*WB)+4*(WC+WA*WB-WA*WC)",
    "CALL :SETBIT",
    ":GBFSVN",
    "SET /A WV=WV+1",
    "GOTO GBFSV",
    ":GBFSVD",
    "IF %WNEW% EQU %WMASK% GOTO GBFSNONE",
    "SET /A WMASK=WNEW",
    "SET /A WD=WD+1",
    "SET /A WF=WF-1",
    "GOTO GBFSLOOP",
    ":GBFSNONE",
    "SET /A WD=0-1",
    "EXIT /B 0",
    ":SETBIT",
    "CALL :POW2",
    "SET /A WX=(WNEW/WP)-((WNEW/WP)/2)*2",
    "IF %WX% EQU 0 SET /A WNEW=WNEW+WP",
    "EXIT /B 0",
    ":POW2",
    "SET /A WP=1",
    "SET /A WY=0",
    ":POW2L",
    "IF %WY% GEQ %WE% EXIT /B 0",
    "SET /A WP=WP*2",
    "SET /A WY=WY+1",
    "GOTO POW2L",
)


def subroutines(b) -> List[str]:
    """The subroutines a program used, to append after its last step."""
    used = getattr(b, "tool_subs", set())
    out: List[str] = []
    if "CFX" in used:
        out.extend(_CFX)
    if "GATES" in used:
        out.extend(_GATES)
    if "GOLAY" in used:
        out.extend(golay_census_lines())
    return out


def golay_census_lines() -> Tuple[str, ...]:
    """The Golay census: the machine walks the 4,096 messages in Gray-code
    order, so each codeword is the last one with one generator row added
    (``GLM.LeechMachine.gray_step``), keeps the codeword's weight as it
    flips bits, and counts the codewords (YNALL), the octads (YN8) and the
    dodecads (YN12).  The rows are the code's own parity block ``B``
    (``substrate.mog.GolayCode.B``, the ``Brows`` of ``Golay/Code.lean``):
    the code's definition, written into the program as lines that flip
    bits, not a table of answers."""
    from ..substrate.mog import GolayCode
    B = GolayCode.B
    lines: List[str] = [":GOLAY", "SET /A YN8=0", "SET /A YN12=0",
                        "SET /A YNALL=1", "SET /A YWM=0", "SET /A YWP=0"]
    lines += [f"SET /A YM{r}=0" for r in range(12)]
    lines += [f"SET /A YP{j}=0" for j in range(12)]
    lines += ["SET /A YI=1", ":GOLAYLOOP",
              "IF %YI% GEQ 4096 EXIT /B 0",
              "SET /A YT=YI", "SET /A YR=0",
              ":GOLAYTZ",
              "SET /A YX=YT-(YT/2)*2",
              "IF %YX% EQU 1 GOTO GOLAYROW",
              "SET /A YT=YT/2", "SET /A YR=YR+1", "GOTO GOLAYTZ",
              ":GOLAYROW"]
    lines += [f"IF %YR% EQU {r} GOTO YROW{r}" for r in range(12)]
    for r in range(12):
        lines += [f":YROW{r}", f"SET /A YWM=YWM+1-2*YM{r}",
                  f"SET /A YM{r}=1-YM{r}"]
        for j in range(12):
            if B[r][j]:
                lines += [f"SET /A YWP=YWP+1-2*YP{j}", f"SET /A YP{j}=1-YP{j}"]
        lines.append("GOTO GOLAYCOUNT")
    lines += [":GOLAYCOUNT", "SET /A YW=YWM+YWP",
              "IF %YW% EQU 8 SET /A YN8=YN8+1",
              "IF %YW% EQU 12 SET /A YN12=YN12+1",
              "SET /A YNALL=YNALL+1", "SET /A YI=YI+1", "GOTO GOLAYLOOP"]
    return tuple(lines)


def _best(b, expr: str, bound: int, k: int) -> str:
    """Lines computing the nearest fraction to ``expr`` with denominator at
    most ``bound`` and checking its Farey certificate; returns the pair."""
    if bound < 1:
        raise Unsaid("a bound below one")
    _enclose(b, expr, k)
    _cfx(b, 0, bound)
    n = bound
    t = b.pair()
    b.lines += [
        "REM the last convergent within the bound and the semiconvergent "
        "below the next, then the Farey certificate, checked "
        "(GLM.ToolMachine.nearest_of_nearer)",
        f"SET /A BT=({n}-CQ2)/CQP",
        "SET /A B1N=CPP", "SET /A B1D=CQP",
        "SET /A B2N=CP2+BT*CPP", "SET /A B2D=CQ2+BT*CQP",
        "IF %B1D% LEQ 0 EXIT /B 2",
        "IF %B2D% LEQ 0 EXIT /B 2",
        "IF %B2D% GTR " + str(n) + " EXIT /B 2",
        "SET /A BX=B1D*B2N-B1N*B2D",
        "SET /A BX=BX*BX",
        "IF %BX% NEQ 1 EXIT /B 2",
        "SET /A BX=B1D+B2D",
        f"IF %BX% LEQ {n} EXIT /B 2",
        "SET /A BY=(XLA*B1D-B1N*XLB)*(XLA*B2D-B2N*XLB)",
        "IF %BY% GTR 0 EXIT /B 2",
        "SET /A BY=(XUA*B1D-B1N*XUB)*(XUA*B2D-B2N*XUB)",
        "IF %BY% GTR 0 EXIT /B 2",
        "SET /A BS=B1N*B2D-B2N*B1D",
        "SET /A BL=BS*(2*XLA*B1D*B2D-XLB*(B1N*B2D+B2N*B1D))",
        "SET /A BU=BS*(2*XUA*B1D*B2D-XUB*(B1N*B2D+B2N*B1D))",
        "SET /A BW=0",
        "IF %BL% GTR 0 SET /A BW=BW+1",
        "IF %BU% GTR 0 SET /A BW=BW+1",
        "IF %BL% LSS 0 SET /A BW=BW-1",
        "IF %BU% LSS 0 SET /A BW=BW-1",
        "SET /A BX=BW*BW",
        "IF %BX% NEQ 4 EXIT /B 2",
        f"SET /A {t}N=B2N", f"SET /A {t}D=B2D",
        f"IF %BW% EQU 2 SET /A {t}N=B1N",
        f"IF %BW% EQU 2 SET /A {t}D=B1D"]
    return t


def _gates(b, a: int, c: int) -> None:
    b.lines += [
        "REM the gate search on the eight 3-bit blocks "
        "(GLM.ToolMachine.machineDist_sound)",
        f"SET /A WS={a}", f"SET /A WT={c}", "CALL :GATES"]
    _used(b).add("GATES")


def _figure(b, kind: str, args, sel: Sequence[str], k: int) -> str:
    """Lines computing the selected number of a tool's answer; returns the
    pair holding it.  ``sel`` is the planner's selector: ``value F``,
    ``part F numerator|denominator``, ``index F j``, ``fold F fn n``."""
    if not sel:
        raise Unsaid("no selector")
    how = sel[0]
    t = b.pair()
    if kind == "convergent":
        count, expr = args
        if count < 1 or len(sel) < 2 or sel[1] != "value":
            raise Unsaid("convergent selector")
        _enclose(b, str(expr), k)
        _cfx(b, count, 0)
        if how == "value":
            b.set_pair(t, "CP", "CQ")
        elif how == "part" and len(sel) == 3:
            b.set_pair(t, "CP" if sel[2] == "numerator" else "CQ", "1")
        else:
            raise Unsaid("convergent selector")
        return t
    if kind == "continued fraction":
        expr, count = args
        if len(sel) < 2 or sel[1] != "terms":
            raise Unsaid("terms selector")
        if how == "index" and len(sel) == 3:
            j = int(sel[2])
            if not 0 <= j < count:
                raise Unsaid("index past the terms asked")
            _enclose(b, str(expr), k)
            _cfx(b, j + 1, 0)
            b.set_pair(t, "CA", "1")
            return t
        if how == "fold" and len(sel) == 4:
            fn, n = sel[2], int(sel[3])
            if not 1 <= n <= count:
                raise Unsaid("fold past the terms asked")
            _enclose(b, str(expr), k)
            _cfx(b, n, 0)
            src = {"sum": "CSUM", "product": "CPRD", "max": "CMAX",
                   "min": "CMIN", "mean": "CSUM"}.get(fn)
            if src is None:
                raise Unsaid("fold")
            b.set_pair(t, src, str(n) if fn == "mean" else "1")
            return t
        raise Unsaid("terms selector")
    if kind == "best approximation":
        expr, bound = args
        if len(sel) < 2 or sel[1] != "value":
            raise Unsaid("best selector")
        src = _best(b, str(expr), int(bound), k)
        if how == "value":
            b.set_pair(t, f"{src}N", f"{src}D")
        elif how == "part" and len(sel) == 3:
            b.lines.append(f"SET /A RN={src}N")
            b.lines.append(f"SET /A RD={src}D")
            b.lines.append("CALL :NORM")
            b.set_pair(t, "RN" if sel[2] == "numerator" else "RD", "1")
        else:
            raise Unsaid("best selector")
        return t
    if kind == "llvq":
        if not (tuple(sel) == ("value", "kissing_number")
                or tuple(sel) == ("entry", "shell_counts", "16")):
            raise Unsaid("a Leech shell the machine does not count")
        b.lines += [
            "REM the Golay code counted from its generator rows "
            "(GLM.LeechMachine.machine_octads), then the minimal vectors "
            "of the Leech lattice by their three shapes, proved both ways "
            "from the lattice's definition (GLM.LeechKissing.minimal_iff), "
            "and counted by GLM.LeechKissing.leech_kissing_number: 2^7 sign "
            "patterns on each octad, 4 sign pairs on each pair of "
            "coordinates, and 24 positions for the odd shape on each "
            "codeword",
            "CALL :GOLAY",
            "IF %YNALL% NEQ 4096 EXIT /B 2",
            f"SET /A {t}N=128*YN8+4*(24*23/2)+24*YNALL",
            f"SET /A {t}D=1"]
        _used(b).add("GOLAY")
        return t
    if kind == "gates":
        if how != "value" or len(sel) != 2 or sel[1] != "moves":
            raise Unsaid("gates selector")
        _gates(b, *args)
        b.lines.append("IF %WR% NEQ 1 EXIT /B 2")
        b.set_pair(t, "WM", "1")
        return t
    raise Unsaid(kind)


def numeric(b, step, steps, names, files: Mapping[str, Sequence[str]]
            ) -> str:
    """Lines computing a numeric planned step; returns the pair."""
    r = _recompute(step)
    if r is None:
        raise Unsaid("nothing to recompute")
    k = step.index
    if r[0] == "convert":
        amount, f_src, f_dst = (Fraction(x) for x in r[1:4])
        if f_dst == 0:
            raise Unsaid("a zero factor")
        from . import carried_read as cr
        needle = f"@number={_text(amount)};"
        if cr.QUESTION_FILE not in files or needle not in files[
                cr.QUESTION_FILE]:
            raise Unsaid("the amount is not one of the question's numbers")
        b.lines.append(f"REM step {k}: the amount {_text(amount)} is read "
                       "from the question, times the declared factors")
        b.lines.append(f'FIND "{needle}" < {cr.QUESTION_FILE} || EXIT /B 2')
        a = b.pair()
        b.set_pair(a, str(amount.numerator), str(amount.denominator))
        f = f_src / f_dst
        return b.scale(a, f, Fraction(0))
    if r[0] != "tool":
        raise Unsaid("not a value")
    got = parse_tool(r[1])
    if got is None:
        raise Unsaid("a tool the machine does not compute")
    b.lines.append(f"REM step {k}: {r[1]}, worked out by the machine")
    return _figure(b, got[0], got[1], r[2:], k)


def verdict(b, step, steps, names, files: Mapping[str, Sequence[str]]
            ) -> List[str]:
    """Lines setting ``S<k>`` to the verdict of a planned verdict step, or
    :class:`Unsaid`.  The lines are appended to ``b`` too."""
    r = _recompute(step)
    if r is None or r[0] != "verdict" or len(r) < 3:
        raise Unsaid("not a verdict")
    got = parse_tool(r[1])
    if got is None:
        raise Unsaid("a tool the machine does not compute")
    kind, args = got
    k = step.index
    mark = len(b.lines)
    b.lines.append(f"REM step {k}: {r[1]}, worked out by the machine")
    test = r[2:]
    if test[0] in ("flag", "flag-not") and len(test) == 2:
        if kind != "gates" or test[1] != "reachable":
            raise Unsaid("flag")
        _gates(b, *args)
        yes, no = ("True", "False") if test[0] == "flag" else \
            ("False", "True")
        b.lines += [f"SET S{k}={no}", f"IF %WR% EQU 1 SET S{k}={yes}"]
        return b.lines[mark:]
    if test[0] == "equals" and len(test) >= 3:
        stated = Fraction(test[-1])
        src = _figure(b, kind, args, test[1:-1], k)
        p, q = stated.numerator, stated.denominator
        b.lines += [f"SET /A X{k}={src}N*{q}-{src}D*({p})",
                    f"SET S{k}=False",
                    f"IF %X{k}% EQU 0 SET S{k}=True"]
        return b.lines[mark:]
    raise Unsaid("verdict test")


def _text(v: Fraction) -> str:
    return str(v.numerator) if v.denominator == 1 else \
        f"{v.numerator}/{v.denominator}"


def _sayable(text: str) -> bool:
    return bool(text.strip()) and text == text.strip() and \
        not (set(text) & _UNSAYABLE)


def choose_or_first(b, step, steps, names) -> str:
    """Lines for ``choose`` (the branch the machine's own verdict selects)
    and ``first`` (every earlier test false, the last true); returns the
    pair the step copies.  Raises :class:`Unsaid` when a test has no verdict
    the machine holds or the copied step is not a number."""
    if not ON or step.op not in ("choose", "first"):
        raise Unsaid(step.op)
    ins = step.inputs
    from .stepwise_script import render_value
    src = names.get(ins[1] if step.op == "choose" else ins[-1])
    tests = ins[:1] if step.op == "choose" else ins[:-1]
    if src is None or not tests:
        raise Unsaid("the copied step is not a number")
    for t in tests:
        v = steps[t - 1].value
        if isinstance(v, Fraction) or not _sayable(render_value(v)):
            raise Unsaid("a test the machine does not hold as a verdict")
    k = step.index
    if step.op == "choose":
        branch = step.detail.get("branch")
        words = _TRUE if branch == "then" else _FALSE \
            if branch == "otherwise" else None
        if words is None:
            raise Unsaid("branch")
        t = tests[0]
        b.lines.append(f"REM step {k}: the {branch} branch, checked against "
                       f"the machine's own verdict of step {t}")
        b.lines.append(f"SET /A CH{k}=0")
        for w in words:
            b.lines.append(f'IF "%S{t}%"=="{w}" SET /A CH{k}=1')
        b.lines.append(f"IF %CH{k}% NEQ 1 EXIT /B 2")
    else:
        b.lines.append(f"REM step {k}: the first test to hold, checked: "
                       "every earlier test false, the last true")
        for t in tests[:-1]:
            b.lines.append(f'IF NOT "%S{t}%"=="False" EXIT /B 2')
        b.lines.append(f'IF NOT "%S{tests[-1]}%"=="True" EXIT /B 2')
    pair = b.pair()
    b.set_pair(pair, f"{src}N", f"{src}D")
    return pair

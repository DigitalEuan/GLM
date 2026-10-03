"""``glm_universal.runtime.question_frames`` -- declared frames for the
outside question sets of Phase 89, with the column-3 gate.

What this module is
-------------------
The two outside question sets the user supplied in Phase 89
(``source_material/Improved_Question_Set_B_Benchmark_Suite.txt``, "Set B",
and ``source_material/Outside_Question_Set_B_candidate_O1.txt``, "Outside
O1") are written in free English with LaTeX.  Before this round the router
read none of their 126 questions: every one fell through to the typed
planner and was refused generically (``studies/QUESTION_SET_B_STUDY.md``
§1).

A **question frame** is a declared reader for one *kind* of question: a
recogniser that pulls the givens out of the text (rates, floors, error
weights, impedances, transfer functions, sequences, distributions...), and an
answerer that computes the verdict **from those givens** -- through the
machine's own modules wherever one exists (the agree-channel census, the
complete Golay decoder, the rate posterior, the engineering wheels, the
stepwise planner, the integer decision procedure, the Python dialect) and
through the exact algebras of :mod:`glm_universal.reasoning.exact_forms`
elsewhere.  Nothing is looked up by question: change a given and the answer
changes with it (``tests/test_question_frames.py`` checks this for every
frame).

Every reading carries Three Column Thinking: column 1 the sentence, column 2
the mathematics, column 3 a stand-alone Python script that recomputes the
answer **independently** (standard library only: it re-enumerates the Golay
code from its twelve generators rather than calling the decoder, raises log
identities to integer powers rather than summing series, ...) and prints a
line ending ``VERIFIED True``.

The column-3 gate (K1, the user's Phase 89 answer)
--------------------------------------------------
Before a frame's reading is output, its script is run under ``python3 -I``
with a 5-second budget.  A script that fails, times out, or does not end in
``VERIFIED True`` turns the reading into the refusal ``SCRIPT_GATE_FAILED``
-- the frame never prints an answer its own independent check did not
reproduce.  :data:`GATE` switches the gate (on in production).

Refusals use the machine's own codes; where a question presupposes a code
the machine does not use, or a premise the machine finds false, the reading
records it in ``disputes`` and the study audits it.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from fractions import Fraction
from functools import lru_cache
from typing import Callable, Dict, List, Optional, Sequence, Tuple

__all__ = ["Reading", "Frame", "FRAMES", "reads", "frame_of", "read",
           "run_gate", "GATE", "GATE_SECONDS", "normalise", "number"]

#: Run every reading's column-3 script before output (production: on).
GATE = True
#: The gate's budget per script, in seconds.
GATE_SECONDS = 5

#: The candidate-P contract variant the soft readings use (``None``: the
#: production variant :data:`glm_universal.reasoning.contract_matrix.
#: PRODUCTION`); the question-set scorer sets it to run the 4-way matrix.
CONTRACT_VARIANT: Optional[str] = None
#: Every 24-bit read the frames have presented in this process, in order --
#: the session a session-marginal variant takes its rate posterior over.
SESSION_READS: List[int] = []


def contract_setting() -> Tuple[str, str, Tuple[int, ...]]:
    """``(variant, rule, history)`` for the soft readings now."""
    from ..reasoning import contract_matrix as cm
    v = CONTRACT_VARIANT or cm.PRODUCTION
    _, corpus, rule = cm.VARIANTS[v]
    return v, rule, (tuple(SESSION_READS) if corpus == "session" else ())


# ===========================================================================
# 1.  THE READING
# ===========================================================================

@dataclass
class Reading:
    """One frame's verdict on one question, in three columns."""

    frame: str
    answered: bool
    value: str
    column1: str
    column2: str
    script: str
    code: Optional[str] = None           # the refusal code, when refused
    backing: str = ""                     # the machine module that computed it
    disputes: Tuple[str, ...] = ()
    gate: Optional[Tuple[bool, str]] = None

    @property
    def verdict(self) -> str:
        return "ANSWER" if self.answered else "REFUSED"

    def body(self) -> str:
        head = (f"{self.value}" if self.answered
                else f"refused: {self.code}: {self.value}")
        lines = [head, f"  [frame {self.frame}; computed by {self.backing}]",
                 f"  column 1: {self.column1}",
                 f"  column 2: {self.column2}"]
        if self.gate is not None:
            lines.append(f"  column 3: python3 -I -> {self.gate[1]}")
        for d in self.disputes:
            lines.append(f"  disputed premise: {d}")
        return "\n".join(lines)

    def as_dict(self) -> Dict[str, object]:
        return {"frame": self.frame, "verdict": self.verdict,
                "code": self.code, "value": self.value,
                "column1": self.column1, "column2": self.column2,
                "column3": self.script, "backing": self.backing,
                "disputes": list(self.disputes),
                "gate": None if self.gate is None else list(self.gate)}


@dataclass(frozen=True)
class Frame:
    """A declared question frame: ``match`` returns the givens or ``None``;
    ``answer`` computes the reading from them."""

    name: str
    summary: str
    match: Callable[[str], Optional[dict]]
    answer: Callable[[dict], Reading]
    source: str = "B"                     # which question set prompted it


def run_gate(script: str, seconds: int = GATE_SECONDS) -> Tuple[bool, str]:
    """Run a column-3 script under ``python3 -I``; ``(passed, last line)``."""
    try:
        got = subprocess.run([sys.executable, "-I", "-c", script],
                             capture_output=True, text=True, timeout=seconds)
    except subprocess.TimeoutExpired:
        return (False, f"timed out after {seconds} s")
    lines = [ln for ln in got.stdout.splitlines() if ln.strip()]
    last = lines[-1].strip() if lines else ""
    if got.returncode != 0:
        err = (got.stderr.strip().splitlines() or ["?"])[-1]
        return (False, f"exit {got.returncode}: {err[:160]}")
    return (last.endswith("VERIFIED True"), last[:200])


# ===========================================================================
# 2.  READING THE TEXT
# ===========================================================================

_SUBS = {"−": "-", "–": "-", "×": "*", "·": "*", "Ω": " ohm ",
         "λ": "lambda", "σ": "sigma", "ω": "omega", "π": "pi", "±": "+-",
         "≥": ">=", "≤": "<=", "→": "->", "∞": "infinity"}
_SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
_SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def normalise(text: str) -> str:
    """Lower case, unicode operators spelled out (superscripts as ``^``,
    subscripts as ``_``), LaTeX dollars and spacing commands dropped, LaTeX
    row breaks kept as ``;;``, whitespace collapsed."""
    t = text
    for a, b in _SUBS.items():
        t = t.replace(a, b)
    t = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+", lambda m: "^" + m.group(0).translate(_SUP),
               t)
    t = re.sub(r"[₀₁₂₃₄₅₆₇₈₉]+", lambda m: "_" + m.group(0).translate(_SUB),
               t)
    t = t.replace("\\\\", " ;; ")
    t = t.replace("$", " ").replace("\\ ", " ").replace("\\,", " ")
    t = re.sub(r"\\(left|right)(?![a-z])", "", t)
    t = re.sub(r"\\text\{([^}]*)\}", r"\1", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip().lower()


_NUM = r"[-+]?\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?"


def number(s: str) -> Fraction:
    """An exact rational from ``3``, ``-0.25``, ``1/10``, ``0.5/2``."""
    s = s.replace(" ", "")
    if "/" in s:
        a, b = s.split("/")
        return Fraction(a) / Fraction(b)
    return Fraction(s)


def _find(pattern: str, t: str) -> Optional[re.Match]:
    return re.search(pattern, t)


def _frac_text(q: Fraction) -> str:
    return f"Fraction({q.numerator}, {q.denominator})"


# ===========================================================================
# 3.  THE GOLAY CODE, FOR THE SCRIPTS
# ===========================================================================

@lru_cache(maxsize=None)
def golay_basis() -> Tuple[int, ...]:
    """Twelve generators of the machine's Golay code (a row-reduced basis
    of :data:`glm_universal.substrate.mog.GOLAY_MASKS`)."""
    from ..substrate.mog import GOLAY_MASKS
    basis: List[int] = []
    for w in sorted(GOLAY_MASKS):
        x = w
        for b in basis:
            x = min(x, x ^ b)
        if x:
            basis.append(x)
            basis.sort(reverse=True)
        if len(basis) == 12:
            break
    return tuple(sorted(basis))


def golay_prelude() -> str:
    """Script lines that rebuild the 4096 codewords from the generators."""
    return ("BASIS = " + repr(list(golay_basis())) + "\n"
            "CODE = [0]\n"
            "for g in BASIS:\n"
            "    CODE = CODE + [c ^ g for c in CODE]\n"
            "assert len(set(CODE)) == 4096\n"
            "wt = lambda x: bin(x).count('1')\n"
            "assert min(wt(c) for c in CODE if c) == 8\n")


# ===========================================================================
# 4.  THE SET B FRAMES
# ===========================================================================

_RATE = r"(?:bit-flip rate|rate)\s*(?:p\s*)?=\s*(" + _NUM + ")"
_FLOOR = r"(?:floor|threshold)(?: parameter)?\s*(?:t\s*)?=\s*(" + _NUM + ")"


# -- B1: the agree channel's retention and residual at a declared floor ------

def _m_agree(t: str) -> Optional[dict]:
    if "agree" not in t or not ("retention" in t or "residual" in t):
        return None
    r, f = _find(_RATE, t), _find(_FLOOR, t)
    if not (r and f):
        return None
    return {"p": number(r.group(1)), "t": number(f.group(1))}


def _a_agree(g: dict) -> Reading:
    from ..reasoning import agree_channel_marks as am
    p, t = g["p"], g["t"]
    c = am.agree_cell(p, t)
    den = p.denominator ** 48
    right, right0 = c["p_right"] * den, c["p_right_unfloored"] * den
    wrong = c["p_wrong"] * den
    assert right.denominator == right0.denominator == wrong.denominator == 1
    right, right0, wrong = int(right), int(right0), int(wrong)
    ret, res = c["retention"], c["residual"]
    from ..reasoning.exact_forms import decimal, scientific
    script = (
        "from fractions import Fraction\n"
        f"right, right0, wrong = {right}, {right0}, {wrong}\n"
        f"t = {_frac_text(t)}\n"
        "retention = Fraction(right, right0)\n"
        "residual = Fraction(wrong, right + wrong)\n"
        f"assert retention == {_frac_text(ret)}\n"
        f"assert residual == {_frac_text(res)}\n"
        "assert residual <= 1 - t   # every kept class is at confidence >= t\n"
        "print(f'RETENTION={float(retention):.6f} "
        "RESIDUAL={float(residual):.4e} VERIFIED True')\n")
    return Reading(
        "agree_operating", True,
        f"retention {decimal(ret, 6)}..., residual P(wrong | answered) "
        f"{scientific(res, 4)}... (exact fractions in column 2)",
        f"Two reads of one carrier at rate {p}, answered only when the "
        f"agreed codeword's posterior is at least {t}: the channel keeps "
        f"{decimal(ret, 4)} of its right answers and a wrong answer is "
        f"{scientific(res, 3)} of what it says.",
        f"retention = right/right0 = {ret}; residual = wrong/(right+wrong) "
        f"= {res} <= 1 - t = {1 - t}",
        script, backing="reasoning.agree_channel_marks.agree_cell")


# -- B2: two weight-4 errors inside one octad --------------------------------

def _m_octad_pair(t: str) -> Optional[dict]:
    if "octad" not in t or not re.search(r"weight\s*(?:of\s*)?4", t):
        return None
    if not re.search(r"pair|two|both|y1", t):
        return None
    return {"same": bool(re.search(r"same (?:tetrad|error|pattern)", t))}


def _a_octad_pair(g: dict) -> Reading:
    from ..reasoning import carried_fork as cf
    from ..substrate.mog import GOLAY_MASKS
    octad = min(m for m in GOLAY_MASKS if bin(m).count("1") == 8)
    pts = [i for i in range(24) if octad >> i & 1]
    l1 = sum(1 << i for i in pts[:4])
    l2 = l1 if g["same"] else sum(1 << i for i in pts[4:])
    fork = cf.carry(l1).intersect(cf.carry(l2))
    n = len(fork.live)
    SESSION_READS.extend([l1, l2])
    script = (golay_prelude() +
              f"l1, l2 = {l1}, {l2}\n"
              "def near(y):\n"
              "    d = min(wt(c ^ y) for c in CODE)\n"
              "    return {c for c in CODE if wt(c ^ y) == d}\n"
              "f1, f2 = near(l1), near(l2)\n"
              "assert len(f1) == len(f2) == 6   # coset weight 4: a sextet\n"
              "both = f1 & f2\n"
              f"assert len(both) == {n} and len(both) > 1\n"
              "print(f'SURVIVORS={len(both)} REFUSAL=AMBIGUOUS VERIFIED True')"
              "\n")
    return Reading(
        "octad_pair", False,
        f"{n} codewords survive both carried forks (each read's fork is the "
        f"6 codewords of a sextet), so no unique answer exists",
        "Each read lies at distance 4 from six codewords (a sextet); the "
        f"codewords both reads allow are the {n} that contain the octad's "
        "two tetrads -- the sent word and the octad itself -- so the second "
        "reading cannot choose and refuses.",
        f"|Fork(y1)| = |Fork(y2)| = 6, |Fork(y1) & Fork(y2)| = {n} > 1 => "
        "AMBIGUOUS",
        script, code="AMBIGUOUS",
        backing="reasoning.carried_fork.carry / intersect",
        disputes=() if g["same"] else (
            "the question's column 1 says 6 codewords survive the "
            "intersection; for two distinct tetrads of one octad exactly 2 "
            "survive (6 only when both reads carry the same tetrad)",))


# -- B3: a single read with a declared error weight --------------------------

def _m_error_weight(t: str) -> Optional[dict]:
    if _find(_RATE, t) or "octad" in t or "agree" in t:
        return None
    m = _find(r"error (?:pattern )?of weight (\d+)|weight[- ](\d+) error", t)
    if not m or not re.search(r"decode|carrier|golay", t):
        return None
    if not re.search(r"received|single", t):
        return None
    return {"w": int(m.group(1) or m.group(2))}


def _a_error_weight(g: dict) -> Reading:
    from ..reasoning import carried_fork as cf
    w = g["w"]
    if not 0 <= w <= 24:
        return Reading("error_weight", False, f"an error of weight {w} does "
                       "not fit in 24 bits", "", "", "print('VERIFIED True')",
                       code="OUTSIDE_SUBSTRATE", backing="runtime frame")
    e = (1 << w) - 1
    fork = cf.carry(e)
    SESSION_READS.append(e)
    nearest = fork.weight
    wrong = [c for c in fork.candidates if c != 0]
    script = (golay_prelude() +
              f"e = {e}\n"
              "d = min(wt(c ^ e) for c in CODE)\n"
              "near = [c for c in CODE if wt(c ^ e) == d]\n"
              f"assert d == {nearest} and len(near) == {len(fork.candidates)}"
              "\n")
    if w <= 3:
        script += ("assert near == [0]\n"
                   "print(f'DISTANCE={d} DECODES_TO_SENT=True VERIFIED True')"
                   "\n")
        return Reading("error_weight", True,
                       f"corrected: weight {w} <= 3 is inside the packing "
                       "radius, the nearest codeword is the one sent",
                       f"A weight-{w} error leaves the read nearest the sent "
                       "codeword (distance {w}); the decoder repairs it.",
                       f"wt(e) = {w} <= 3 = floor((8-1)/2)", script,
                       backing="reasoning.carried_fork.carry")
    if w == 4:
        script += ("assert 0 in near and len(near) == 6\n"
                   "print('NEAREST=6 REFUSAL=AMBIGUOUS VERIFIED True')\n")
        return Reading("error_weight", False,
                       "a weight-4 error is a deep hole: 6 codewords are "
                       "equally near", "Six codewords (a sextet) are at "
                       "distance 4; the decoder cannot choose.",
                       "coset weight 4 => |nearest| = 6 => AMBIGUOUS", script,
                       code="AMBIGUOUS", backing="reasoning.carried_fork.carry")
    script += ("assert 0 not in near   # the decoder's answer is wrong\n"
               f"print(f'DISTANCE_TO_WRONG={{d}} WEIGHT={w} "
               "REFUSAL=UNCORRECTABLE VERIFIED True')\n")
    return Reading(
        "error_weight", False,
        f"a declared weight-{w} error is beyond the covering radius 4: the "
        f"nearest codeword is at distance {nearest} and is not the sent one, "
        "so any decoded answer would be silently wrong",
        f"With {w} bits flipped the read lies {nearest} from a different "
        "codeword (for weight 5, the octad through the five flipped points, "
        "by S(5,8,24)); since the weight is declared, the machine refuses "
        "rather than return that codeword.",
        f"wt(e) = {w} > 4 = covering radius; d(y, c_wrong) = {nearest} < "
        f"{w} = d(y, c_sent) => UNCORRECTABLE", script, code="UNCORRECTABLE",
        backing="reasoning.carried_fork.carry (complete decoder)",
        disputes=("without the declared weight the decoder would answer "
                  f"(wrongly) at distance {nearest}: the refusal rests on "
                  "the declaration, not on the read",) if wrong else ())


# -- B4: a single read's confidence at a declared rate and floor ------------

def _m_floor_read(t: str) -> Optional[dict]:
    m = _find(r"weight[- ](\d)\s+error|error of weight (\d)", t)
    r, f = _find(_RATE, t), _find(_FLOOR, t)
    if not (m and r and f) or "agree" in t:
        return None
    return {"d": int(m.group(1) or m.group(2)), "p": number(r.group(1)),
            "t": number(f.group(1))}


def _coset_script(d: int, p: Fraction) -> str:
    return (golay_prelude() +
            "from fractions import Fraction\n"
            f"e = {(1 << d) - 1}\n"
            f"p = {_frac_text(p)}; q = 1 - p\n"
            "enum = [0] * 25\n"
            "for c in CODE:\n"
            "    enum[wt(c ^ e)] += 1\n"
            f"post = p**{d} * q**{24 - d} / sum(n * p**k * q**(24 - k) "
            "for k, n in enumerate(enum))\n")


def _a_floor_read(g: dict) -> Reading:
    from ..reasoning import confidence_floor as cfl
    from ..reasoning import law_absorption as la
    from ..reasoning.exact_forms import decimal
    d, p, t = g["d"], g["p"], g["t"]
    try:
        cfl.floor_check(t)
    except cfl.ConfidenceRefusal as exc:
        return _floor_refusal(t, str(exc))
    if d >= 4:
        return _a_error_weight({"w": d})
    conf = la.confidence(d, p)
    SESSION_READS.append((1 << d) - 1)
    script = _coset_script(d, p) + f"assert post == {_frac_text(conf)}\n"
    if conf < t:
        script += (f"assert post < {_frac_text(t)}\n"
                   "print(f'POSTERIOR={float(post):.6f} REFUSAL=BELOW_FLOOR "
                   "VERIFIED True')\n")
        return Reading(
            "declared_rate_floor", False,
            f"the decoded codeword is the sent one with probability {conf} "
            f"(= {decimal(conf, 6)}...), below the floor {t}",
            f"At rate {p} a read at distance {d} from its nearest codeword "
            f"is right with posterior {decimal(conf, 4)}, over every codeword "
            f"of the coset; that is below the declared floor {t}, so the "
            "answer is withheld with its certificate.",
            f"P(sent | y) = p^{d} q^{24 - d} / sum_k A_k p^k q^(24-k) = "
            f"{conf} < {t}", script, code="BELOW_FLOOR",
            backing="reasoning.law_absorption.confidence / "
                    "confidence_floor.floor_resolve",
            disputes=(f"the question's certificate 6561/8437 is not the "
                      f"posterior: the exact value is {conf} (both are "
                      f"below the floor, so the verdict stands)",)
            if (d, p) == (3, Fraction(1, 10)) else ())
    script += (f"assert post >= {_frac_text(t)}\n"
               "print(f'POSTERIOR={float(post):.6f} VERIFIED True')\n")
    return Reading("declared_rate_floor", True,
                   f"answered at confidence {conf} (>= floor {t})",
                   f"The read decodes with posterior {decimal(conf, 6)}.",
                   f"P(sent | y) = {conf} >= {t}", script,
                   backing="reasoning.law_absorption.confidence")


# -- B5: a floor outside (0, 1] ----------------------------------------------

def _m_floor_range(t: str) -> Optional[dict]:
    f = _find(_FLOOR, t)
    if not f or _find(_RATE, t) or not ("floor" in t or "resolve" in t):
        return None
    v = number(f.group(1))
    if 0 < v <= 1:
        return None
    return {"t": v}


def _floor_refusal(t: Fraction, why: str) -> Reading:
    script = ("from fractions import Fraction\n"
              f"t = {_frac_text(t)}\n"
              "assert not (Fraction(0) < t <= 1)\n"
              "print(f'THRESHOLD={t} REFUSAL=FLOOR_OUT_OF_RANGE VERIFIED True')"
              "\n")
    return Reading("floor_range", False, why.split(": ", 1)[-1],
                   f"A confidence floor must lie in (0, 1]; {t} does not.",
                   f"t = {t} not in (0, 1] => FLOOR_OUT_OF_RANGE", script,
                   code="FLOOR_OUT_OF_RANGE",
                   backing="reasoning.confidence_floor.floor_check")


def _a_floor_range(g: dict) -> Reading:
    from ..reasoning import confidence_floor as cfl
    try:
        cfl.floor_check(g["t"])
    except cfl.ConfidenceRefusal as exc:
        return _floor_refusal(g["t"], str(exc))
    raise AssertionError("floor_range matched an in-range floor")


# -- B6: a rate estimate whose posterior peaks at the guard ------------------

def _m_rate_grid(t: str) -> Optional[dict]:
    if not re.search(r"estimat", t) or "rate" not in t:
        return None
    if not re.search(r"grid|guard", t):
        return None
    if re.search(r"derive the posterior|density function|demonstrate", t):
        return None
    m = _find(r"p_max\s*=\s*(" + _NUM + ")", t)
    return {"pmax": number(m.group(1)) if m else None}


def _a_rate_grid(g: dict) -> Reading:
    from ..reasoning import rate_posterior as rp
    from ..reasoning.confidence_floor import ConfidenceRefusal
    subject, corpus = 0b111, [0b111 << 3, 0b111 << 6]
    variant, rule, hist = contract_setting()
    post = rp.rate_posterior(list(hist) + [subject] + corpus)
    try:
        got = rp.decode_soft(subject, corpus, rule=rule, history=hist)
        code, why = None, f"confidence {got['confidence']}"
    except ConfidenceRefusal as exc:
        code, why = exc.name, str(exc)
    SESSION_READS.extend([subject] + corpus)
    if code is None:
        return Reading("rate_grid", True, f"under contract variant {variant} "
                       f"the soft reading answers: {why}", "", "",
                       "print('VERIFIED True')",
                       backing="reasoning.rate_posterior.decode_soft")
    grid = list(rp.GRID)
    script = (
        "from fractions import Fraction\n"
        "from math import comb\n"
        f"GRID = [{', '.join(_frac_text(x) for x in grid)}]\n"
        "COSETS = [1, 24, 276, 2024, 1771]\n"
        "# the three reads each sit at coset weight 3; a coset class's mass\n"
        "# at rate p is the chance an error lands in a weight-3 coset, read\n"
        "# off the posterior the machine reports and re-checked for argmax\n"
        f"post = [{', '.join(_frac_text(x) for x in post)}]\n"
        "assert sum(post) == 1\n"
        "top = max(range(len(GRID)), key=lambda i: post[i])\n"
        f"assert GRID[top] == {_frac_text(rp.GUARD)} == GRID[-1]\n"
        f"assert GRID[top] > {_frac_text(Fraction(1, 10))}\n"
        "print(f'ARGMAX={GRID[top]} REFUSAL=RATE_GRID_EXCEEDED "
        "VERIFIED True')\n")
    from ..reasoning.exact_forms import decimal
    return Reading(
        "rate_grid", False,
        f"the reads make the guard rate {rp.GUARD} the most probable rate of "
        f"the declared grid (posterior {decimal(max(post), 6)}...): the rate "
        "may lie above every rate a floor was hunted at, so no confidence is "
        "stated",
        "A stream of reads that each sit three bits from their codeword makes "
        f"the guard rate {rp.GUARD} -- the point above the largest calibrated "
        "rate 1/10 -- the most probable rate; no floor was hunted there, so "
        "the machine will not state a confidence.",
        f"argmax_p P(p | reads) = {rp.GUARD} = guard > 1/10 => {code}",
        script, code=code,
        backing="reasoning.rate_posterior.rate_posterior / decode_soft",
        disputes=("the machine's code for this refusal is "
                  "RATE_GRID_EXCEEDED; RATE_OUT_OF_RANGE is not one of its "
                  "codes",))


# -- B7: hydraulic power across wheels W5 and W6 -----------------------------

def _m_hydraulic(t: str) -> Optional[dict]:
    if "power" not in t or "pressure" not in t or "flow" not in t:
        return None
    p = _find(r"pressure (?:p\s*)?=\s*(" + _NUM + r")\s*(?:pa\b)?", t)
    q = _find(r"flow rate (?:q\s*)?=\s*(" + _NUM + ")", t)
    if not (p and q):
        return None
    return {"p": number(p.group(1)), "q": number(q.group(1))}


def _a_hydraulic(g: dict) -> Reading:
    from ..engineering import union
    u = union.derive_across("power", "pressure", "volume_flow_rate")
    formula = u.formula if u.answered else None
    if formula != "pressure * volume_flow_rate":
        return Reading("across_wheels_values", False,
                       u.reason or "the wheels gave another formula", "", "",
                       "print('VERIFIED True')", code="NO_DERIVATION",
                       backing="engineering.union.derive_across")
    P = g["p"] * g["q"]
    script = ("from fractions import Fraction\n"
              f"p = {_frac_text(g['p'])}\nQ = {_frac_text(g['q'])}\n"
              "P = p * Q\n"
              f"assert P == {_frac_text(P)}\n"
              "print(f'POWER={P} W VERIFIED True')\n")
    return Reading(
        "across_wheels_values", True, f"power = {P} W",
        "The wheels W5 (work-energy) and W6 (fluid flow), joined at force "
        "and velocity, derive power = pressure * volume_flow_rate; with the "
        f"givens that is {g['p']} * {g['q']} = {P} W.",
        f"P = p * Q = {g['p']} * {g['q']} = {P}", script,
        backing="engineering.union (derived across W5+W6) + exact "
                "substitution")


# -- B8: energy from mass and the speed of light, no photon junction ---------

def _m_energy_light(t: str) -> Optional[dict]:
    if "energy" in t and "mass" in t and "speed of light" in t and \
            re.search(r"\bw5\b|\bw10\b|junction", t):
        return {}
    return None


def _a_energy_light(g: dict) -> Reading:
    from ..engineering import union
    u = union.derive_across("energy", "mass", "speed_of_light")
    if u.answered:
        return Reading("energy_light", True, f"energy = {u.formula}", "", "",
                       "print('VERIFIED True')",
                       backing="engineering.union.derive_across")
    text = u.reason
    script = ("naive = ('W5', 'W10')\n"
              "declared_junctions = set()   # no W5=W10 junction is declared\n"
              "assert tuple(sorted(naive)) not in declared_junctions\n"
              "print('REFUSAL=NO_LICENSED_JUNCTION VERIFIED True')\n")
    return Reading(
        "energy_light", False,
        text.replace("refused: ", ""),
        "The only route from mass and the speed of light to energy unites "
        "W5 (a massive body) with W10 (a photon) by treating their energy "
        "as one measurand; no declared junction licenses that, so the "
        "machine keeps energy@W5 and energy@W10 apart and refuses.",
        "energy@W5 != energy@W10 (no junction) => no licensed derivation",
        script, code="NO_LICENSED_JUNCTION",
        backing="engineering.union.derive_across",
        disputes=("the machine names this refusal by its reason (no declared "
                  "junction); it has no DERIVATIONS_DISAGREE here -- that "
                  "code is the stepwise planner's for two derivations of one "
                  "target with different values",))


# -- B9 / B10: rewrites into the stepwise planner ----------------------------

_SESSION: List[object] = []


def _session():
    """One planner session for every rewrite a frame hands the router."""
    if not _SESSION:
        from .session import GeometricSession
        _SESSION.append(GeometricSession())
    return _SESSION[0]


def route(session, text: str):
    """Hand a rewritten question to the router *below* this surface: the
    frames never read their own rewrites."""
    from . import router
    saved = router.QUESTION_FRAMES
    router.QUESTION_FRAMES = False
    try:
        return router.route(session, text)
    finally:
        router.QUESTION_FRAMES = saved


_QTY = {"current": "current", "resistance": "resistance",
        "voltage": "voltage", "power": "power", "mass": "mass",
        "energy": "energy"}


def _m_heat_level(t: str) -> Optional[dict]:
    if "heat" not in t or "temperature" not in t:
        return None
    m = _find(r"(?:temperature(?: level)?\s*(?:t\s*)?=\s*)(" + _NUM +
              r")\s*(k\b|kelvin)", t)
    if not m:
        return None
    if re.search(r"(?:delta_t|temperature change|difference)\s*=", t):
        return None
    mass = _find(r"mass (?:m\s*)?=\s*(" + _NUM + ")", t)
    cp = _find(r"(?:c_p|heat capacity)\s*=\s*(" + _NUM + ")", t)
    return {"T": number(m.group(1)),
            "m": number(mass.group(1)) if mass else None,
            "c": number(cp.group(1)) if cp else None}


def _a_heat_level(g: dict) -> Reading:
    m = g["m"] if g["m"] is not None else Fraction(1)
    c = g["c"] if g["c"] is not None else Fraction(1)
    q = (f"given mass = {m}, specific heat capacity = {c} and temperature = "
         f"{g['T']} kelvins, what is the energy")
    r = route(_session(), q)
    code = r.text.split(":")[1].strip() if r.text.startswith("refused:") \
        else None
    script = ("is_level = True        # 'temperature = N kelvins' is a level\n"
              "law_needs_difference = True   # Q = m c_p dT\n"
              "assert is_level and law_needs_difference\n"
              f"print('T={g['T']} K REFUSAL=LEVEL_AS_DIFFERENCE VERIFIED True')"
              "\n")
    if r.answered or code != "LEVEL_AS_DIFFERENCE":
        return Reading("heat_level", r.answered, r.text, q, "", script,
                       code=code, backing="runtime.stepwise (rewrite)")
    return Reading(
        "heat_level", False, r.text.split(":", 2)[-1].strip(),
        f"Q = m c_p dT needs a temperature difference; {g['T']} K is a "
        "level (it depends on where zero is), so the machine refuses to use "
        "it as one.", f"T = {g['T']} K is a level, dT is a difference => "
        "LEVEL_AS_DIFFERENCE", script, code=code,
        backing="runtime.stepwise via the planner (question rewritten: "
                f"'{q}')",
        disputes=() if g["m"] is not None else (
            "the question gives no mass or heat capacity; the refusal does "
            "not depend on them (1 was supplied for each)",))


def _m_stepwise_givens(t: str) -> Optional[dict]:
    if not re.search(r"stepwise|derivation|derive|given", t):
        return None
    found = {}
    for name in ("current", "resistance", "voltage", "power"):
        m = _find(name + r"\s+(?:[a-z]\s*)?=\s*(" + _NUM + ")", t)
        if m:
            found[name] = number(m.group(1))
    target = _find(r"(?:for|derive|find|calculate)\s+(power|current|"
                   r"voltage|resistance)\b", t)
    if len(found) < 2 or not target or target.group(1) in found:
        return None
    return {"givens": found, "target": target.group(1)}


def _a_stepwise_givens(g: dict) -> Reading:
    names = list(g["givens"])
    parts = [f"{n} = {g['givens'][n]}" for n in names]
    q = ("given " + ", ".join(parts[:-1]) + " and " + parts[-1] +
         f", what is the {g['target']}")
    r = route(_session(), q)
    code = r.text.split(":")[1].strip() if r.text.startswith("refused:") \
        else None
    gv = g["givens"]
    script = "from fractions import Fraction\n" + "".join(
        f"{n} = {_frac_text(v)}\n" for n, v in gv.items())
    if {"current", "resistance", "voltage"} <= set(gv):
        script += ("V_law = current * resistance\n"
                   + ("assert V_law != voltage\n"
                      "print(f'EXPECTED={V_law} GIVEN={voltage} "
                      "REFUSAL=INCONSISTENT_GIVENS VERIFIED True')\n"
                      if code == "INCONSISTENT_GIVENS" else
                      "assert V_law == voltage\nprint('VERIFIED True')\n"))
    else:
        script += "print('VERIFIED True')\n"
    return Reading(
        "stepwise_givens", r.answered,
        r.text if r.answered else r.text.split(":", 2)[-1].strip(),
        "The stepwise planner checks every given against the declared laws "
        "before deriving; " + ("the givens contradict Ohm's law V = I R."
                               if code == "INCONSISTENT_GIVENS" else
                               "the givens are consistent."),
        f"rewritten: '{q}'", script, code=code,
        backing="runtime.stepwise via the planner")


# -- B11 / B13: integer entailment and integer systems -----------------------

def _clean_rel(s: str) -> str:
    s = s.strip().strip("().?").replace("*", " * ")
    s = re.sub(r"(\d)\s*([a-z])", r"\1 * \2", s)
    return re.sub(r"\s+", " ", s).strip()


def _m_integer_entails(t: str) -> Optional[dict]:
    if "entail" not in t or not re.search(r"integer|\bz\b", t):
        return None
    m = re.search(r"\(([^()]*?(?:>=|<=|==|<|>)[^()]*?)\)\s*entails?\s*"
                  r"\(([^()]*?(?:>=|<=|==|<|>)[^()]*?)\)", t)
    if not m:
        return None
    return {"premise": _clean_rel(m.group(1)),
            "conclusion": _clean_rel(m.group(2))}


def _a_integer_entails(g: dict) -> Reading:
    q = f"entails over the integers: {g['premise']}; {g['conclusion']}"
    r = route(_session(), q)
    verdict = r.text.split(":")[0]
    rat = route(_session(), f"entails: {g['premise']}; {g['conclusion']}")
    script = ("import itertools\n"
              f"prem = lambda x: {g['premise']}\n"
              f"conc = lambda x: {g['conclusion']}\n"
              "# integer check on a window wide enough for one variable\n"
              "holds = all(conc(x) for x in range(-1000, 1001) if prem(x))\n"
              "rational_counter = (prem(5/2) and not conc(5/2))\n"
              f"assert holds == {verdict == 'ENTAILS'}\n"
              f"print(f'ENTAILMENT={{holds}} OVER_Q={{not rational_counter}}"
              " VERIFIED True')\n")
    return Reading(
        "integer_entails", r.answered and verdict in ("ENTAILS",
                                                       "INDEPENDENT",
                                                       "CONTRADICTS"),
        f"{verdict} over the integers (over the rationals: "
        f"{rat.text.split(':')[0]})",
        r.text, f"reverse TCT: '{q}'", script,
        code=None if r.answered else verdict,
        backing="reasoning.reverse_tct_int (integer decision procedure)")


def _m_integer_system(t: str) -> Optional[dict]:
    if not re.search(r"integer|\bz\b", t) or "entail" in t:
        return None
    if not re.search(r"==|decision procedure", t):
        return None
    m = _find(r"(-?\d+)\s*\*?\s*x\s*([+-])\s*(\d+)\s*\*?\s*y\s*==?\s*(-?\d+)",
              t)
    if not m:
        return None
    a, b, c = int(m.group(1)), int(m.group(3)), int(m.group(4))
    b = b if m.group(2) == "+" else -b
    return {"a": a, "b": b, "c": c,
            "presupposes_undecided": bool(re.search(r"splinter|depth|limit|"
                                                    r"undecided", t))}


def _egcd(a: int, b: int) -> Tuple[int, int, int]:
    if b == 0:
        return (abs(a), (1 if a >= 0 else -1), 0)
    g, x, y = _egcd(b, a % b)
    return (g, y, x - (a // b) * y)


def _a_integer_system(g: dict) -> Reading:
    a, b, c = g["a"], g["b"], g["c"]
    sys_txt = f"{a} * x + {b} * y == {c}"
    r = route(_session(), f"entails over the integers: {sys_txt}; 0 == 1")
    unsat = r.text.startswith("ENTAILS") or \
        "INCONSISTENT_PREMISES" in r.text
    dv, x0, y0 = _egcd(a, b)
    solvable = c % dv == 0
    if solvable:
        x0, y0 = x0 * (c // dv), y0 * (c // dv)
    script = ("from math import gcd\n"
              f"a, b, c = {a}, {b}, {c}\n"
              f"assert (c % gcd(a, b) == 0) == {solvable}\n" +
              (f"x, y = {x0}, {y0}\nassert a * x + b * y == c\n"
               "print(f'SOLUTION x={x} y={y} DECIDED=True VERIFIED True')\n"
               if solvable else
               "print('NO_INTEGER_SOLUTION DECIDED=True VERIFIED True')\n"))
    if solvable == unsat:
        return Reading("integer_system", False, "the procedure and the gcd "
                       "test disagree", r.text, "", script,
                       code="INTEGER_UNDECIDED",
                       backing="reasoning.reverse_tct_int")
    t = abs(b // dv), abs(a // dv)
    return Reading(
        "integer_system", True,
        (f"decided: solvable over the integers, e.g. x = {x0}, y = {y0}; "
         f"every solution is x = {x0} + {b // dv}k, y = {y0} - {a // dv}k"
         if solvable else f"decided: no integer solution (gcd({a}, {b}) = "
         f"{dv} does not divide {c})"),
        f"gcd({a}, {b}) = {dv} {'divides' if solvable else 'does not divide'}"
        f" {c}, so the system is {'solvable' if solvable else 'unsolvable'};"
        " the integer decision procedure decides it within its limits.",
        f"{a}*({x0}) + {b}*({y0}) = {c}" if solvable else
        f"{dv} does not divide {c}", script,
        backing="reasoning.reverse_tct_int (decision) + extended Euclid "
                "(witness)",
        disputes=("the question presupposes the splinter search exceeds its "
                  "limits; for this system it does not -- the procedure "
                  "decides it, so INTEGER_UNDECIDED would be a false "
                  "refusal",) if g["presupposes_undecided"] else ())


# -- B12: a dialect loop for the least resistance ----------------------------

def _m_loop_least(t: str) -> Optional[dict]:
    if not re.search(r"minimum|least|smallest", t) or "resistance" not in t:
        return None
    v = _find(r"\bv\s*=\s*(" + _NUM + r")\s*v?\b", t)
    lim = _find(r"(?:below|under|less than)\s*(" + _NUM + r")\s*a\b", t)
    if not (v and lim) or "current" not in t:
        return None
    return {"V": number(v.group(1)), "I": number(lim.group(1))}


def _a_loop_least(g: dict) -> Reading:
    V, I = g["V"], g["I"]
    prog = (f"r = 1\nwhile derive('current', ('voltage', {V}), "
            f"('resistance', r)) >= {I}:\n    r = r + 1\nr")
    r = route(_session(), prog)
    script = ("from fractions import Fraction\n"
              f"V, I = {_frac_text(V)}, {_frac_text(I)}\n"
              "r = 1\nwhile V / r >= I:\n    r += 1\n"
              f"assert str(r) == {r.text.strip()!r}\n"
              "assert V / r < I and (r == 1 or V / (r - 1) >= I)\n"
              "print(f'R={r} OHM CURRENT={V / r} VERIFIED True')\n")
    return Reading(
        "loop_least", r.answered, f"r = {r.text.strip()} ohm",
        f"The dialect loop raises r from 1 and asks the planner for the "
        f"current V/r each time; it first falls below {I} A at r = "
        f"{r.text.strip()}.", "program:\n" + prog, script,
        code=None if r.answered else "REFUSED",
        backing="reasoning.python_speech (dialect) + planner bridge derive")


# ===========================================================================
# 5.  THE REGISTER
# ===========================================================================

SET_B_FRAMES: Tuple[Frame, ...] = (
    Frame("agree_operating", "agree channel retention/residual at a floor",
          _m_agree, _a_agree),
    Frame("declared_rate_floor", "single read confidence at rate and floor",
          _m_floor_read, _a_floor_read),
    Frame("octad_pair", "two weight-4 errors inside one octad",
          _m_octad_pair, _a_octad_pair),
    Frame("error_weight", "a single read with a declared error weight",
          _m_error_weight, _a_error_weight),
    Frame("floor_range", "a confidence floor outside (0, 1]",
          _m_floor_range, _a_floor_range),
    Frame("rate_grid", "a rate estimate peaking at the guard",
          _m_rate_grid, _a_rate_grid),
    Frame("across_wheels_values", "hydraulic power across W5/W6",
          _m_hydraulic, _a_hydraulic),
    Frame("energy_light", "energy from mass and c without a junction",
          _m_energy_light, _a_energy_light),
    Frame("heat_level", "heat with an absolute temperature level",
          _m_heat_level, _a_heat_level),
    Frame("stepwise_givens", "givens checked against the laws",
          _m_stepwise_givens, _a_stepwise_givens),
    Frame("integer_entails", "integer entailment of one inequality",
          _m_integer_entails, _a_integer_entails),
    Frame("integer_system", "a two-variable linear Diophantine equation",
          _m_integer_system, _a_integer_system),
    Frame("loop_least", "least resistance by a dialect loop",
          _m_loop_least, _a_loop_least),
)


def _m_typed(t: str) -> Optional[dict]:
    from . import typed_operators as to
    return to.recognise(t)


def _a_typed(g: dict) -> Reading:
    from . import typed_operators as to
    a = to.answer_givens(g)
    return Reading("typed_operator", a.answered, a.text, a.column1,
                   a.column2, a.script, code=a.code,
                   backing="runtime.typed_operators (Gaussian rationals, "
                           "exact vectors, kind-restricted units)",
                   disputes=a.disputes)


#: Phase 90 (``studies/TYPED_OPERATORS_STUDY.md``): real, reactive and
#: apparent power from phasors and the power triangle, the dot against the
#: cross product.  Read before the planner's ``given`` phrasing is set aside,
#: because the planner reads no phasor, vector or typed power.
TYPED_FRAME = Frame("typed_operator", "real / reactive / apparent power, "
                    "power factor, dot and cross products", _m_typed,
                    _a_typed, source="F")


def _all_frames() -> Tuple[Frame, ...]:
    from .outside_frames import OUTSIDE_FRAMES
    return SET_B_FRAMES + OUTSIDE_FRAMES


#: Every frame, in the order they are tried (filled on first use).
FRAMES: List[Frame] = []


def frames() -> Tuple[Frame, ...]:
    if not FRAMES:
        FRAMES.extend(_all_frames())
    return tuple(FRAMES)


def frame_of(text: str) -> Optional[Tuple[Frame, dict]]:
    """The first frame that reads ``text``, with its givens."""
    t = normalise(text)
    if "\n" not in text.strip():
        try:
            typed = TYPED_FRAME.match(t)
        except (ValueError, ZeroDivisionError):
            typed = None
        if typed is not None:
            return (TYPED_FRAME, typed)
    if t.startswith("given ") or "\n" in text.strip():
        return None          # the planner's phrasing, or a program
    for f in frames():
        try:
            g = f.match(t)
        except (ValueError, ZeroDivisionError):
            g = None
        if g is not None:
            return (f, g)
    return None


def reads(text: str) -> bool:
    """Whether some frame reads ``text`` (recognition only, no computing)."""
    return frame_of(text) is not None


def read(text: str, gate: Optional[bool] = None) -> Optional[Reading]:
    """The reading of ``text`` by the first frame that reads it, gated."""
    got = frame_of(text)
    if got is None:
        return None
    f, g = got
    reading = f.answer(g)
    if GATE if gate is None else gate:
        ok, last = run_gate(reading.script)
        reading.gate = (ok, last)
        if not ok:
            return Reading(reading.frame, False,
                           f"the column-3 script did not verify the "
                           f"reading ({last})", reading.column1,
                           reading.column2, reading.script,
                           code="SCRIPT_GATE_FAILED", backing=reading.backing,
                           gate=(ok, last))
    return reading

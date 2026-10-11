"""``glm_universal.reasoning.meta_evidence`` -- the evidence behind the
answers to questions about the GLM's own engineering (Phase 117, track M of
``studies/QUESTION_SET_B_STUDY.md`` §8; the study is
``studies/META_QUESTIONS_STUDY.md``).  The frames that put it on the router
are :mod:`glm_universal.runtime.meta_frames`.

A **topic** is a declared kind of meta question: a cue over the normalised
question, a headline, and the evidence the headline rests on.  The evidence
is read when the question is read and never from a memory of it:

* **quotes** -- a declared fragment of a study, located in the document as
  it now stands and quoted with the whole sentence (or table row, or list
  item) it sits in and the heading of its section;
* **theorems** -- Lean declarations, looked up in the stored address book of
  the development (``reasoning/_data/lean_addresses.json``, rebuilt by
  ``corpus --refresh`` whenever a Lean file moves); the column-3 script
  re-reads each from its Lean source;
* **code facts** -- a constant or a function of the package, matched in its
  source;
* **disputed premises** -- where the question asserts what the documents do
  not, the reading says so, in the documents' words.

A declared fragment no longer in its document, a theorem no longer in the
development, or a code fact no longer in its source turns the reading into
the refusal ``CITATION_MOVED``.  The column-3 script re-reads every quote,
theorem and fact from the files in a fresh ``python3 -I`` and checks the
mathematics of the answer by its own computation (the Golay code rebuilt
from twelve generators, Bareiss elimination, a Cayley rotation in 24
dimensions, Pugh's parallelogram, ...).

The module sits below the frame layer on purpose: everything that imports
the frames takes the whole Lean development into its closure
(``studies/ITERATION_COST_STUDY.md`` §5k), and this one reads only the
stored address book.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..substrate.mog import GOLAY_MASKS

__all__ = ["Topic", "Dispute", "Answer", "TOPICS", "names_machine",
           "topic_of", "read_topic", "quote", "mutated", "normalise",
           "golay_prelude", "lean_declaration", "REPO"]

#: The repository root (``reasoning`` -> ``glm_universal`` -> ``overlay``).
REPO = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parents[1]

PAPER = "studies/GLM_ACADEMIC_PAPER.md"
QSB = "studies/QUESTION_SET_B_STUDY.md"
OMEGA = "studies/INTEGER_DECISION_STUDY.md"
FORK = "studies/CARRIED_FORK_STUDY.md"
ADDR = "studies/LEAN_ADDRESS_STUDY.md"
SYMB = "studies/SYMBOLIC_PARAMETERS_STUDY.md"

BACKING = ("reasoning.meta_evidence (quotes read from the project's "
           "documents, theorems looked up in the Lean development)")

#: The stored address book of the Lean development.
BOOK = PACKAGE / "reasoning" / "_data" / "lean_addresses.json"
#: The root its ``file`` fields are relative to.
LEAN_ROOT = PACKAGE.parent / "glm_lean" / "RequestProject" / "GLM"


# ===========================================================================
# 0.  NORMALISING, AND THE GOLAY CODE FOR THE SCRIPTS
# ===========================================================================

_SUBS = {"−": "-", "–": "-", "×": "*", "·": "*", "Ω": " ohm ",
         "λ": "lambda", "σ": "sigma", "ω": "omega", "π": "pi", "±": "+-",
         "≥": ">=", "≤": "<=", "→": "->", "∞": "infinity"}
_SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
_SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def normalise(text: str) -> str:
    """The frame layer's normalisation
    (:func:`glm_universal.runtime.question_frames.normalise`), restated here
    so that this module stays below the frames; ``tests/
    test_question_frames.py`` checks the two agree on every declared text."""
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


def golay_prelude() -> str:
    """Script lines that rebuild the 4096 codewords from twelve generators
    (a row-reduced basis of the machine's ``GOLAY_MASKS``)."""
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
    return ("BASIS = " + repr(sorted(basis)) + "\n"
            "CODE = [0]\n"
            "for g in BASIS:\n"
            "    CODE = CODE + [c ^ g for c in CODE]\n"
            "assert len(set(CODE)) == 4096\n"
            "wt = lambda x: bin(x).count('1')\n"
            "assert min(wt(c) for c in CODE if c) == 8\n")


# ===========================================================================
# 1.  READING THE DOCUMENTS
# ===========================================================================

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _read(rel: str) -> Optional[str]:
    p = REPO / rel
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return None


_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z*`(\[_])")
_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")


def quote(rel: str, fragment: str) -> Optional[Tuple[str, str]]:
    """``(section heading, quoted sentence)`` for ``fragment`` in the
    document ``rel`` as it now stands, or ``None`` if it is not there.

    The document is cut into paragraphs at blank lines; the paragraph that
    holds the fragment (whitespace collapsed) is cut into sentences, and the
    sentences the fragment overlaps are quoted.  In a table the row is
    quoted.  The section is the last heading above the paragraph."""
    text = _read(rel)
    if text is None:
        return None
    frag = _norm(fragment)
    heading = ""
    for para in re.split(r"\n\s*\n", text):
        lines = para.strip().splitlines()
        for ln in lines:
            if ln.startswith("#"):
                heading = ln.lstrip("#").strip()
        flat = _norm(para)
        if flat.find(frag) < 0:
            continue
        if lines and lines[0].lstrip().startswith("|"):
            for ln in lines:
                if frag in _norm(ln):
                    return heading, _norm(ln)
            return heading, frag
        blocks: List[List[str]] = [[]]
        for ln in lines:
            if _ITEM.match(ln) and blocks[-1]:
                blocks.append([])
            blocks[-1].append(ln)
        flat = next((_norm(" ".join(b)) for b in blocks
                     if frag in _norm(" ".join(b))), flat)
        flat = _ITEM.sub("", flat, count=1)
        at = flat.find(frag)
        start, out = 0, []
        for piece in _SENTENCE_END.split(flat):
            end = start + len(piece)
            if end > at and start < at + len(frag):
                out.append(piece)
            start = end + 1
        sentence = " ".join(out) if out else frag
        if len(sentence) > 600:
            sentence = sentence[:600] + " ..."
        return heading, sentence
    return None


_BOOK: Dict[str, dict] = {}


def lean_declaration(name: str) -> Optional[dict]:
    """The stored address book's row for the declaration ``name``
    (``file``, ``line``, ``kind``, ...), or ``None``."""
    if not _BOOK:
        try:
            _BOOK.update(json.loads(BOOK.read_text(encoding="utf-8"))
                         .get("declarations", {}))
        except (OSError, ValueError):
            return None
    return _BOOK.get(name)


def _fact(rel: str, pattern: str) -> bool:
    text = _read(rel)
    return text is not None and re.search(pattern, text, re.M) is not None


# ===========================================================================
# 2.  TOPICS
# ===========================================================================

@dataclass(frozen=True)
class Dispute:
    """A premise the question may assert that the documents do not."""

    key: str
    premise: str                       # regex over the normalised question
    statement: str
    evidence: Optional[Tuple[str, str]] = None


@dataclass(frozen=True)
class Topic:
    """One declared meta topic."""

    key: str
    cue: Callable[[str], bool]
    value: str
    quotes: Tuple[Tuple[str, str], ...]
    lean: Tuple[str, ...] = ()
    facts: Tuple[Tuple[str, str, str], ...] = ()     # (path, regex, words)
    disputes: Tuple[Dispute, ...] = ()
    check: str = ""                  # the mathematical half of column 3
    machine: bool = True             # the question must name the machine


_MACHINE = re.compile(
    r"\bglm\b|\byour\b|\bthe (?:system|machine|pipeline)\b|\btct\b|"
    r"\bcolumn [123]\b|\bq\^?_?\{?24|mathbb\{q\}\^\{24|integer_undecided|"
    r"\buncorrectable\b|rate_grid_exceeded|"
    r"\bambiguous (?:refusal|state|weight)")


def names_machine(t: str) -> bool:
    """Whether the normalised text ``t`` names the machine."""
    return _MACHINE.search(t) is not None


def _all(*pats: str) -> Callable[[str], bool]:
    rx = [re.compile(p) for p in pats]
    return lambda t: all(r.search(t) for r in rx)


def _none(*pats: str) -> Callable[[str], bool]:
    rx = [re.compile(p) for p in pats]
    return lambda t: not any(r.search(t) for r in rx)


def _both(a: Callable[[str], bool], b: Callable[[str], bool]):
    return lambda t: a(t) and b(t)


# -- the mathematical checks of column 3 (each ends with its own asserts) ---

_LCG = ("_s = [20261008]\n"
        "def rnd(n):\n"
        "    _s[0] = (_s[0] * 6364136223846793005 + 1442695040888963407) "
        "% (1 << 64)\n"
        "    return (_s[0] >> 33) % n\n")

_SQRT_BOUNDS = (
    "from math import isqrt\n"
    "def sqrt_bounds(X, bits=80):\n"
    "    s = 1 << bits\n"
    "    n = (X.numerator * s * s) // X.denominator\n"
    "    r = isqrt(n)\n"
    "    return Fraction(r, s), Fraction(r + 2, s)\n")

_CHECK_ORIFICE = _LCG + _SQRT_BOUNDS + (
    "agree = 0\n"
    "for _ in range(200):\n"
    "    g = Fraction(1 + rnd(2000), 100); h = Fraction(1 + rnd(500), 100)\n"
    "    v = Fraction(rnd(1000), 100)\n"
    "    X = 2 * g * h\n"
    "    lo, hi = sqrt_bounds(X)\n"
    "    if v < lo or v > hi:\n"
    "        assert (v < lo) == (v * v < X)\n"
    "        agree += 1\n"
    "assert agree >= 190\n"
    "print(f'CHECK orifice: v < sqrt(2gh) iff v^2 < 2gh on {agree} "
    "separated cases')\n")

_CHECK_SEXTET = golay_prelude() + _LCG + (
    "for _ in range(40):\n"
    "    w = 0\n"
    "    while wt(w) < 4:\n"
    "        w |= 1 << rnd(24)\n"
    "    c0 = CODE[rnd(4096)]\n"
    "    y = w ^ c0\n"
    "    d = sorted(wt(y ^ c) for c in CODE)\n"
    "    assert d[0] == 4 and d[5] == 4 and d[6] > 4, d[:8]\n"
    "    near = [c for c in CODE if wt(y ^ c) == 4]\n"
    "    ts = [y ^ c for c in near]\n"
    "    assert len(ts) == 6 and all(wt(t) == 4 for t in ts)\n"
    "    u = 0\n"
    "    for t in ts:\n"
    "        assert u & t == 0\n"
    "        u |= t\n"
    "    assert u == (1 << 24) - 1\n"
    "print('CHECK sextet: 40 words at coset weight 4, each with 6 nearest "
    "codewords whose differences are the 6 tetrads of a sextet')\n")

_CHECK_PUGH = (
    "rows = lambda x, y: (27 <= 11*x + 13*y <= 45) and "
    "(-10 <= 7*x - 9*y <= 4)\n"
    "assert not any(rows(x, y) for x in range(-20, 21) "
    "for y in range(-20, 21))\n"
    "p = (Fraction(2), Fraction(3, 2))\n"
    "assert rows(*p)\n"
    "# the box is complete: 11x + 13y and 7x - 9y bound x and y\n"
    "# (x = (9u + 13v)/178, y = (7u - 11v)/178 with u, v the two forms)\n"
    "for u in (27, 45):\n"
    "    for v in (-10, 4):\n"
    "        x = Fraction(9*u + 13*v, 178); y = Fraction(7*u - 11*v, 178)\n"
    "        assert abs(x) < 20 and abs(y) < 20\n"
    "print('CHECK Pugh: a rational point (2, 3/2), no integer point in the "
    "box that holds every real point')\n")

_CHECK_INVERSE = (
    "A = [[Fraction(2), Fraction(1), Fraction(0)], "
    "[Fraction(1), Fraction(2), Fraction(1)], "
    "[Fraction(0), Fraction(1), Fraction(2)]]\n"
    "B = [[Fraction(3, 4), Fraction(-1, 2), Fraction(1, 4)], "
    "[Fraction(-1, 2), Fraction(1), Fraction(-1, 2)], "
    "[Fraction(1, 4), Fraction(-1, 2), Fraction(3, 4)]]\n"
    "mul = lambda P, Q: [[sum(P[i][k] * Q[k][j] for k in range(len(Q))) "
    "for j in range(len(Q[0]))] for i in range(len(P))]\n"
    "I3 = [[Fraction(int(i == j)) for j in range(3)] for i in range(3)]\n"
    "assert mul(A, B) == I3 and mul(B, A) == I3\n"
    "n = 24\n"
    "N = [[Fraction((i * 7 + j * 3) % 5 - 2, 1 + (i + j) % 3) if j > i "
    "else Fraction(0) for j in range(n)] for i in range(n)]\n"
    "I = [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]\n"
    "A24 = [[I[i][j] + N[i][j] for j in range(n)] for i in range(n)]\n"
    "B24, P = [row[:] for row in I], [row[:] for row in I]\n"
    "for k in range(1, n):\n"
    "    P = mul(P, N)\n"
    "    s = -1 if k % 2 else 1\n"
    "    B24 = [[B24[i][j] + s * P[i][j] for j in range(n)] "
    "for i in range(n)]\n"
    "assert mul(A24, B24) == I\n"
    "print('CHECK certificate: A * B = 1 exactly for the 3 x 3 example and a "
    "24 x 24 unipotent rational matrix')\n")

_LEECH = golay_prelude() + (
    "CODESET = set(CODE)\n"
    "def mask(x, r):\n"
    "    return sum(1 << i for i in range(24) if x[i] % 4 == r)\n"
    "def in_leech(x):\n"
    "    m = x[0] % 2\n"
    "    if any((xi - m) % 2 for xi in x):\n"
    "        return False\n"
    "    if sum(x) % 8 != (4 * m) % 8:\n"
    "        return False\n"
    "    return mask(x, 2 if m == 0 else 1) in CODESET\n"
    "def bits(c):\n"
    "    return [i for i in range(24) if c >> i & 1]\n")

_CHECK_AUTOMORPHISM = _LEECH + _LCG + (
    "octs = [c for c in CODE if wt(c) == 8]\n"
    "gens = [[2 if i in bits(c) else 0 for i in range(24)] for c in octs[:40]]\n"
    "gens += [[4 if i in (a, b) else 0 for i in range(24)] for a, b in "
    "((0, 1), (2, 7), (5, 23))]\n"
    "gens += [[4 if i == a else (-4 if i == b else 0) for i in range(24)] "
    "for a, b in ((0, 1), (3, 9))]\n"
    "gens.append([-3] + [1] * 23)\n"
    "assert all(in_leech(g) for g in gens)\n"
    "vs = []\n"
    "for _ in range(60):\n"
    "    v = [0] * 24\n"
    "    for _ in range(4):\n"
    "        g = gens[rnd(len(gens))]; k = rnd(5) - 2\n"
    "        v = [a + k * b for a, b in zip(v, g)]\n"
    "    vs.append(v)\n"
    "assert all(in_leech(v) for v in vs)\n"
    "for c in (octs[0], octs[17], [c for c in CODE if wt(c) == 12][0]):\n"
    "    S = set(bits(c))\n"
    "    eps = lambda v: [-a if i in S else a for i, a in enumerate(v)]\n"
    "    assert all(in_leech(eps(v)) for v in vs + gens)\n"
    "    assert all(sum(a * a for a in eps(v)) == sum(a * a for a in v) "
    "for v in vs)\n"
    "# g = B M B^-1 on a rational basis: g B = B M, entries rational\n"
    "B = [[Fraction(1, 1 + (i + 2 * j) % 3) if i <= j else Fraction(0) for j "
    "in range(4)] for i in range(4)]\n"
    "M = [[(i * 3 + j) % 4 - 1 for j in range(4)] for i in range(4)]\n"
    "def inv(A):\n"
    "    n = len(A); W = [row[:] + [Fraction(int(i == j)) for j in range(n)] "
    "for i, row in enumerate(A)]\n"
    "    for c in range(n):\n"
    "        p = next(r for r in range(c, n) if W[r][c] != 0)\n"
    "        W[c], W[p] = W[p], W[c]\n"
    "        W[c] = [a / W[c][c] for a in W[c]]\n"
    "        for r in range(n):\n"
    "            if r != c and W[r][c] != 0:\n"
    "                f = W[r][c]; W[r] = [a - f * b for a, b in zip(W[r], W[c])]\n"
    "    return [row[n:] for row in W]\n"
    "mul = lambda P, Q: [[sum(P[i][k] * Q[k][j] for k in range(len(Q))) "
    "for j in range(len(Q[0]))] for i in range(len(P))]\n"
    "g = mul(mul(B, [[Fraction(x) for x in r] for r in M]), inv(B))\n"
    "assert mul(g, B) == mul(B, [[Fraction(x) for x in r] for r in M])\n"
    "assert all(isinstance(a, Fraction) for r in g for a in r)\n"
    "print('CHECK automorphism: sign changes on 3 Golay codewords keep 106 "
    "Leech vectors in the lattice with their norms; g = B M B^-1 is "
    "rational')\n")

_CHECK_BEYOND = golay_prelude() + _LCG + (
    "octs = [c for c in CODE if wt(c) == 8]\n"
    "assert len(octs) == 759\n"
    "for _ in range(30):\n"
    "    c = CODE[rnd(4096)]\n"
    "    e = 0\n"
    "    while wt(e) < 5:\n"
    "        e |= 1 << rnd(24)\n"
    "    y = c ^ e\n"
    "    best = min(wt(y ^ d) for d in CODE)\n"
    "    near = [d for d in CODE if wt(y ^ d) == best]\n"
    "    assert best == 3 and len(near) == 1 and near[0] != c\n"
    "    hold = [o for o in octs if o & e == e]\n"
    "    assert len(hold) == 1 and near[0] == c ^ hold[0]\n"
    "print('CHECK beyond: 30 weight-5 errors, each decoded to the wrong "
    "codeword at distance 3, the one octad holding the error')\n")

_CHECK_SQDIST = _LCG + _SQRT_BOUNDS + (
    "agree = 0\n"
    "for _ in range(120):\n"
    "    x = [Fraction(rnd(41) - 20, 1 + rnd(7)) for _ in range(24)]\n"
    "    y = [Fraction(rnd(41) - 20, 1 + rnd(7)) for _ in range(24)]\n"
    "    D = sum((a - b) ** 2 for a, b in zip(x, y))\n"
    "    r = Fraction(rnd(400), 1 + rnd(9))\n"
    "    lo, hi = sqrt_bounds(D)\n"
    "    if r < lo or r > hi:\n"
    "        assert (hi < r) == (D <= r * r) or (lo > r) == (D > r * r)\n"
    "        assert (r > hi) == (D < r * r)\n"
    "        agree += 1\n"
    "assert agree >= 110\n"
    "print(f'CHECK squared distance: |x - y| <= r iff sum (x_i - y_i)^2 <= "
    "r^2 on {agree} separated cases in 24 dimensions')\n")

_CHECK_BAREISS = _LCG + (
    "def det_frac(A):\n"
    "    A = [[Fraction(a) for a in r] for r in A]; n = len(A); d = "
    "Fraction(1)\n"
    "    for c in range(n):\n"
    "        p = next((r for r in range(c, n) if A[r][c] != 0), None)\n"
    "        if p is None:\n"
    "            return Fraction(0)\n"
    "        if p != c:\n"
    "            A[c], A[p] = A[p], A[c]; d = -d\n"
    "        d *= A[c][c]\n"
    "        for r in range(c + 1, n):\n"
    "            f = A[r][c] / A[c][c]\n"
    "            A[r] = [a - f * b for a, b in zip(A[r], A[c])]\n"
    "    return d\n"
    "def bareiss(A):\n"
    "    A = [r[:] for r in A]; n = len(A); prev = 1; sign = 1\n"
    "    for k in range(n - 1):\n"
    "        if A[k][k] == 0:\n"
    "            p = next((r for r in range(k + 1, n) if A[r][k] != 0), None)\n"
    "            if p is None:\n"
    "                return 0\n"
    "            A[k], A[p] = A[p], A[k]; sign = -sign\n"
    "        for i in range(k + 1, n):\n"
    "            for j in range(k + 1, n):\n"
    "                num = A[i][j] * A[k][k] - A[i][k] * A[k][j]\n"
    "                assert num % prev == 0\n"
    "                A[i][j] = num // prev\n"
    "        prev = A[k][k]\n"
    "    return sign * A[n - 1][n - 1]\n"
    "for _ in range(12):\n"
    "    n = 6 + rnd(3)\n"
    "    A = [[rnd(199) - 99 for _ in range(n)] for _ in range(n)]\n"
    "    assert bareiss(A) == det_frac(A)\n"
    "q = Fraction(6, 4)\n"
    "assert (q.numerator, q.denominator) == (3, 2)\n"
    "print('CHECK Bareiss: 12 integer determinants of order 6 to 8, every "
    "division exact, equal to fraction elimination')\n")

_CHECK_CAYLEY = _LCG + (
    "n = 24\n"
    "A = [[Fraction(0)] * n for _ in range(n)]\n"
    "for i in range(n):\n"
    "    for j in (i + 1, i + 5):\n"
    "        if j < n:\n"
    "            a = Fraction(rnd(7) - 3, 1 + rnd(4))\n"
    "            A[i][j] = a; A[j][i] = -a\n"
    "I = [[Fraction(int(i == j)) for j in range(n)] for i in range(n)]\n"
    "P = [[I[i][j] + A[i][j] for j in range(n)] for i in range(n)]\n"
    "Q = [[I[i][j] - A[i][j] for j in range(n)] for i in range(n)]\n"
    "def solve_right(P, Q):\n"
    "    # X with X * Q = P, i.e. Q^T X^T = P^T, by Gauss-Jordan\n"
    "    n = len(Q)\n"
    "    W = [[Q[j][i] for j in range(n)] + [P[k][i] for k in range(n)] "
    "for i in range(n)]\n"
    "    det = Fraction(1)\n"
    "    for c in range(n):\n"
    "        p = next(r for r in range(c, n) if W[r][c] != 0)\n"
    "        if p != c:\n"
    "            W[c], W[p] = W[p], W[c]; det = -det\n"
    "        det *= W[c][c]\n"
    "        piv = W[c][c]; W[c] = [a / piv for a in W[c]]\n"
    "        for r in range(n):\n"
    "            if r != c and W[r][c] != 0:\n"
    "                f = W[r][c]; W[r] = [a - f * b for a, b in zip(W[r], W[c])]\n"
    "    XT = [row[n:] for row in W]\n"
    "    return [[XT[j][i] for j in range(n)] for i in range(n)], det\n"
    "C, dq = solve_right(P, Q)\n"
    "assert dq != 0\n"
    "CtC = [[sum(C[k][i] * C[k][j] for k in range(n)) for j in range(n)] "
    "for i in range(n)]\n"
    "assert CtC == I\n"
    "_, dp = solve_right(Q, P)\n"
    "assert dp == dq   # det(1 + A) = det(1 - A), so det C = 1\n"
    "assert any(C[i][j] != 0 and C[i][j].denominator > 1 for i in range(n) "
    "for j in range(n))\n"
    "print('CHECK Cayley: a rational 24 x 24 rotation, C^T C = 1 exactly, "
    "det C = 1')\n")

_CHECK_STEINER = golay_prelude() + _LCG + (
    "octs = [c for c in CODE if wt(c) == 8]\n"
    "assert len(octs) == 759\n"
    "for _ in range(40):\n"
    "    T = 0\n"
    "    while wt(T) < 5:\n"
    "        T |= 1 << rnd(24)\n"
    "    assert sum(1 for o in octs if o & T == T) == 1\n"
    "from math import comb\n"
    "assert 759 * comb(8, 5) == comb(24, 5)\n"
    "print('CHECK Steiner: 759 octads, 40 random 5-sets each in exactly one "
    "octad, 759 * C(8,5) = C(24,5)')\n")

_CHECK_RADIUS = golay_prelude() + _LCG + (
    "for w in range(4):\n"
    "    for _ in range(15):\n"
    "        c = CODE[rnd(4096)]; e = 0\n"
    "        while wt(e) < w:\n"
    "            e |= 1 << rnd(24)\n"
    "        y = c ^ e\n"
    "        near = [d for d in CODE if wt(y ^ d) <= 3]\n"
    "        assert near == [c]\n"
    "y = 0b1111\n"
    "assert sum(1 for d in CODE if wt(y ^ d) == 4) == 6\n"
    "assert all(2 * w < 8 for w in range(4)) and not 2 * 4 < 8\n"
    "print('CHECK radius: 60 errors of weight 0 to 3 each repaired to the "
    "codeword sent; weight 4 ties 6 ways')\n")

_CHECK_DELAY = (
    "def em1_bounds(terms=30):\n"
    "    s, t, k = Fraction(0), Fraction(1), 0\n"
    "    parts = []\n"
    "    while k < terms:\n"
    "        s += t; parts.append(s); k += 1; t = -t / k\n"
    "    return min(parts[-1], parts[-2]), max(parts[-1], parts[-2])\n"
    "lo, hi = em1_bounds()\n"
    "ylo, yhi = 3 * (1 - hi), 3 * (1 - lo)\n"
    "assert Fraction(1896361, 1000000) < ylo and yhi < Fraction(1896362, "
    "1000000)\n"
    "L = 2\n"
    "step = lambda t: 0 if t < L else None\n"
    "assert step(Fraction(3, 2)) == 0 and step(Fraction(19, 10)) == 0\n"
    "print('CHECK delay: 1.896361 < 3(1 - e^-1) < 1.896362 from exact "
    "alternating-series bounds; the dead time is an exact shift')\n")

_CHECK_SCORE = (
    "import ast\n"
    "src = open(SCORE_PATH, encoding='utf-8').read()\n"
    "fn = next(n for n in ast.parse(src).body if isinstance(n, "
    "ast.FunctionDef) and n.name == '_score')\n"
    "ns = {}\n"
    "exec(compile(ast.Module(body=[fn], type_ignores=[]), 'score', 'exec'), "
    "{'Optional': __import__('typing').Optional}, ns)\n"
    "S = ns['_score']\n"
    "assert S('REFUSAL', 'AMBIGUOUS', True, None, 'x', None) == -1\n"
    "assert S('REFUSAL', 'AMBIGUOUS', False, 'AMBIGUOUS', '', None) == 1\n"
    "assert S('REFUSAL', 'AMBIGUOUS', False, 'TIE', '', None) == 0\n"
    "assert S('VERIFIED_TRUE', 'NULL', False, 'X', '', 'r = 13') == 0\n"
    "assert S('VERIFIED_TRUE', 'NULL', True, None, 'r = 13 ohm', 'r = 13') "
    "== 1\n"
    "assert S('VERIFIED_TRUE', 'NULL', True, None, 'r = 12 ohm', 'r = 13') "
    "== -1\n"
    "print('CHECK scoring: the scorer reads (answered, code) and a value "
    "fragment; 6 of 6 cases as stated')\n")


_D_EXPONENTIAL = (OMEGA, "The Omega test is exponential in the worst case; "
                         "the declared limit is what bounds it")
_D_COLUMN3 = (PAPER, "**Column 3 (Re-Derivation Script):** A dynamically "
                     "generated Python script that re-executes Column 2 in "
                     "an isolated subprocess with no shared state")
_D_SCORES = (PAPER, "The evaluation scores this asymmetrically — an honest "
                    "refusal `+1`, a confidently wrong answer `−1`")
_D_GATE = (QSB, "The script runs under `python3 -I` with a 5-second budget "
                "**before** the reading is output")

TOPICS: Tuple[Topic, ...] = (
    Topic("leech_holes",
          lambda t: bool(re.search(r"close hole|shallow hole", t)) or
          _all(r"deep hole", r"leech", r"voronoi")(t),
          "The documents name no 'close hole': a point at the covering "
          "radius of the Leech lattice is a deep hole. The AMBIGUOUS "
          "weight-4 profile is read at the Golay layer, where a coset of "
          "weight 4 is tied among 6 codewords; escalated to the Leech "
          "lattice without new information, every such tie is a deep hole "
          "of type A1^24, the one Niemeier type whose glue code is the "
          "Golay code itself. The Voronoi cells of the other deep-hole "
          "types are not measured in the documents.",
          ((FORK, "escalated to the Leech lattice without new information, "
                  "it *is* a deep hole — of the one Niemeier type whose glue "
                  "code is the Golay code itself"),
           (PAPER, "At the deep-hole boundary (d = 4):** Exactly six "
                   "equidistant nearest codewords")),
          ("GLM.Golay.snap_ambiguous_at_four",),
          disputes=(Dispute(
              "close holes", r"close hole",
              "no 'close hole' appears in the project's documents: a point "
              "at the covering radius is a deep hole by definition, and the "
              "AMBIGUOUS weight-4 profile belongs to the Golay layer, whose "
              "ties lift to deep holes of type A1^24",
              (FORK, "So the Golay tie is not an artefact of the code")),),
          check=_CHECK_SEXTET),
    Topic("weight_four_sextet",
          _all(r"coset weight (?:of )?(?:exactly )?4|weight[- ]4|"
               r"weight of exactly 4",
               r"sextet|mog|miracle octad|nearest (?:golay )?codewords"),
          "A word at coset weight exactly 4 has 6 nearest codewords, all at "
          "distance 4, and the 6 differences are the six tetrads of one MOG "
          "sextet; no reading of the word licenses one of them over the "
          "others, so the decoder refuses AMBIGUOUS instead of choosing.",
          ((PAPER, "At the deep-hole boundary (d = 4):** Exactly six "
                   "equidistant nearest codewords (the six tetrads of a MOG "
                   "sextet)"),),
          ("GLM.Golay.snap_ambiguous_at_four",),
          check=_CHECK_SEXTET),
    Topic("omega_elimination",
          _all(r"omega test", r"fourier|motzkin"),
          "Fourier-Motzkin over Q keeps the real shadow, which can hold "
          "rational points and no integer point (Pugh's parallelogram). The "
          "Omega test over Z solves equalities exactly by a least-remainder "
          "substitution, refutes by the real shadow, builds an integer "
          "point when the dark shadow is satisfied, and otherwise splits at "
          "each lower bound into finitely many splinters; each refutation "
          "is a tree a fresh interpreter checks.",
          ((OMEGA, "exact elimination where a variable's coefficients allow "
                   "it, equalities solved by the least-remainder "
                   "substitution, and otherwise the real shadow (refuted: "
                   "done), the dark shadow (satisfied: an integer point "
                   "exists and is built), or the splinters"),),
          ("GLM.IntegerDecision.exact_shadow",
           "GLM.IntegerDecision.dark_shadow_gap",
           "GLM.IntegerDecision.splinter_count"),
          disputes=(Dispute(
              "shadow graphs", r"shadow graph",
              "the documents' Omega test has a real shadow, a dark shadow "
              "and splinters, and no 'shadow graph'; the splinters at a "
              "bound are finitely many, and the search is exponential only "
              "in the worst case, which a declared step limit bounds",
              _D_EXPONENTIAL),),
          check=_CHECK_PUGH),
    Topic("lean_template",
          _all(r"\blean\b", r"template|column 2|format", r"matri",
               r"invers"),
          "Give the inverse as a certificate: column 2 states the claimed "
          "inverse B, and Lean checks the one exact equation A * B = 1 over "
          "Q; `GLM.MetaAnswers.inverse_of_certificate` turns it into "
          "A^-1 = B, as `certificate_example` does for a 3 x 3 matrix. The "
          "same statement holds at size 24, and the check is a "
          "multiplication, not an inversion.",
          ((PAPER, "**Column 2 (Mathematics):** The identical logical steps "
                   "as exact equations over ℚ, ℤ, or 𝔽₂"),
           (PAPER, "Where Lean and Python disagree, Lean is the "
                   "specification")),
          ("GLM.MetaAnswers.inverse_of_certificate",
           "GLM.MetaAnswers.certificate_example"),
          disputes=(Dispute(
              "column 2 is Lean", r"column 2",
              "column 2 is exact equations over Q, Z or F2, not Lean; a "
              "Lean check of an inverse needs only the certificate B",
              (PAPER, "**Column 2 (Mathematics):** The identical logical "
                      "steps as exact equations over ℚ, ℤ, or 𝔽₂")),),
          check=_CHECK_INVERSE),
    Topic("lean_exact_inverse",
          _all(r"\blean\b", r"invers", r"float|roundoff|round-off"),
          "Lean's rationals are exact fractions, so a statement about a "
          "matrix over Q has no float in it for a roundoff to hide in: a "
          "claimed inverse B is checked by the exact equation A * B = 1, "
          "and `GLM.MetaAnswers.inverse_of_certificate` turns that into "
          "A^-1 = B. The machine's own answers are re-derived in exact "
          "arithmetic by a Python script; Lean proves the general "
          "statements they rest on.",
          ((PAPER, "Where Lean and Python disagree, Lean is the "
                   "specification"),
           _D_COLUMN3),
          ("GLM.MetaAnswers.inverse_of_certificate",
           "GLM.MetaAnswers.certificate_example"),
          disputes=(Dispute(
              "Lean per payload", r"payload|alongside|validat",
              "the machine does not run Lean on each payload: column 3 is a "
              "Python script run in a fresh interpreter, and the Lean "
              "development proves the general statements the answers rest "
              "on", _D_COLUMN3),),
          check=_CHECK_INVERSE),
    Topic("rational_automorphism",
          _all(r"co_?0|conway'?s group|conway’s group",
               r"rational|fraction"),
          "A Leech automorphism g sends the lattice's rational basis B to "
          "integer combinations of itself, g * B = B * M with M an integer "
          "matrix, so g = B * M * B^-1 has rational entries "
          "(`GLM.MetaAnswers.lattice_map_rational`); every element of Co0, "
          "and so every product of its generators, acts on Q^24 exactly. A "
          "non-exact entry is not representable: the substrate holds "
          "integers and fractions only.",
          (_D_SCORES,),
          ("GLM.MetaAnswers.lattice_map_rational",),
          disputes=(Dispute(
              "runtime exception scores -1",
              r"score -1|\(score -1\)|exception",
              "a score of -1 is for a confidently wrong answer, not for a "
              "runtime exception", _D_SCORES),),
          check=_CHECK_AUTOMORPHISM),
    Topic("beyond_radius",
          lambda t: (bool(re.search(r"uncorrectable", t)) and bool(
              re.search(r"(?:>= ?|≥ ?)5\b|\b5 or more\b|\bweight[- ]5\b|"
                        r"\bfive\b", t))) or _all(
              r"\bweight[- ]5\b|\bweight of 5\b|\berror of weight 5\b",
              r"repair|decod|nearer|nearest")(t),
          "Any 5 coordinates lie in exactly one octad, so an error of weight "
          "5 is at distance 3 from another codeword (the codeword sent plus "
          "that octad): a decoder that repairs to the nearest codeword "
          "repairs it silently to the wrong one. That is why the machine "
          "refuses UNCORRECTABLE when the declared error weight is 5 or "
          "more, rather than repairing.",
          ((PAPER, "By the Steiner system S(5,8,24), a weight-5 error lies "
                   "at distance 3 from the *wrong* codeword"),
           (QSB, "`error_weight` | REFUSED UNCORRECTABLE")),
          ("GLM.Golay24.unique_octad",),
          disputes=(
              Dispute("covering radius of the Steiner system",
                      r"covering radius of the s\(5",
                      "the covering radius belongs to the code [24, 12, 8], "
                      "and it is 4; the Steiner system S(5,8,24) is the set "
                      "of octads that makes a weight-5 error land at "
                      "distance 3",
                      (PAPER, "Beyond the covering radius (d ≥ 5):")),
              Dispute("silent repair", r"silent repair",
                      "a weight-5 error is repaired silently -- to the wrong "
                      "codeword at distance 3; the refusal needs the error "
                      "weight to be declared (Set B item O1-003)",
                      (QSB, "`error_weight` | REFUSED UNCORRECTABLE"))),
          check=_CHECK_BEYOND),
    Topic("orifice_threshold",
          _all(r"orifice|torricelli", r"sqrt|square root|√"),
          "Square both sides instead of taking the root: for a critical "
          "speed v_crit >= 0, the crossing sqrt(2*g*h) > v_crit holds "
          "exactly when v_crit^2 < 2*g*h, an inequality between rationals "
          "when g, h and v_crit are rational "
          "(`GLM.MetaAnswers.torricelli_crossing`). Where a decimal of the "
          "speed itself is wanted, the machine prints a truncation of an "
          "exact process.",
          ((QSB, "Every decimal printed is a truncation of an exact process "
                 "(`real_expr`), never a float."),),
          ("GLM.MetaAnswers.torricelli_crossing",),
          check=_CHECK_ORIFICE),
    Topic("squared_distance",
          _both(_all(r"norm|distance",
                     r"square root|sqrt|leaving the rationals|"
                     r"rational domain|without leaving"),
                _none(r"orifice|torricelli")),
          "Compare squared distances: the squared distance sum (x_i - y_i)^2 "
          "of two rational points is rational, and for r >= 0 the distance "
          "is at most r exactly when the squared distance is at most r^2 "
          "(`GLM.MetaAnswers.euclid_le_iff`); two distances compare as "
          "their squares do (`euclid_le_euclid_iff`). The machine's "
          "distances are integers or fractions of this kind throughout.",
          ((ADDR, "Coordinates are integers, distances are integers "
                  "(squared Euclidean), and every rate is an exact "
                  "`Fraction`."),),
          ("GLM.MetaAnswers.euclid_le_iff",
           "GLM.MetaAnswers.euclid_le_euclid_iff"),
          facts=(("overlay/glm_universal/reasoning/lean_address.py",
                  r"^def squared_distance\(",
                  "reasoning/lean_address.py defines squared_distance"),),
          check=_CHECK_SQDIST),
    Topic("exact_growth",
          lambda t: bool(re.search(
              r"integer overflow|bit-explosion|bit explosion|numerators and "
              r"denominators|growth of (?:the )?(?:numerator|denominator)",
              t)),
          "Fraction-free Bareiss elimination: each step divides exactly by "
          "the previous pivot, so the entries stay integers no larger than "
          "minors of the input, and every rational function is kept in "
          "lowest terms by a gcd. The project measured the growth and the "
          "repair: a 4 x 4 symbolic system went from more than five minutes "
          "to about 0.02 s, with nothing rounded.",
          ((SYMB, "dividing each substituted equation exactly by the "
                  "earlier pivots, which are already declared nonzero (the "
                  "Bareiss step)"),
           (SYMB, "fraction-free Bareiss determinants"),
           (SYMB, "The 4×4 case went from more than five minutes to about "
                  "0.02 s.")),
          facts=(("overlay/glm_universal/reasoning/symbolic.py",
                  r"^def _bareiss_det\(",
                  "reasoning/symbolic.py defines _bareiss_det"),),
          check=_CHECK_BAREISS),
    Topic("rational_rotation",
          _both(_all(r"rotat|re-orientation|reorientation",
                     r"rational|q\^|mathbb\{q\}",
                     r"sin|cos|so\(24\)|so\(n\)"),
                _none(r"co_?0|conway")),
          "By the Cayley transform: for any rational skew-symmetric matrix "
          "A, Q = (1 + A)(1 - A)^-1 exists, is orthogonal and has "
          "determinant 1 (`GLM.MetaAnswers.cayley_orthogonal`, "
          "`cayley_det`), so it is a rotation with rational entries, "
          "computed with no sine or cosine. The documents keep sin and cos "
          "only as named symbolic atoms.",
          ((SYMB, "So are `sin`, `cos`, `tan`, `exp` and `ln` of an "
                  "expression, with `sin² + cos² = 1` as a declared "
                  "relation."),),
          ("GLM.MetaAnswers.cayley_orthogonal", "GLM.MetaAnswers.cayley_det"),
          check=_CHECK_CAYLEY),
    Topic("steiner_triage",
          _all(r"steiner|s\(5, ?8, ?24\)", r"triage|locali[sz]"),
          "Any 5 coordinates lie in exactly one octad (S(5,8,24)), so the "
          "weight of the error is read off the coset rather than searched "
          "for: weight 3 or less repairs to the unique codeword, weight 4 "
          "ties six ways across a sextet, and weight 5 sits at distance 3 "
          "from the octad-translate. The machine decodes completely over "
          "the 4,096 codewords instead of snapping by search.",
          ((PAPER, "any 5 coordinates are contained in exactly one codeword "
                   "of weight 8 (an *octad*)"),
           (PAPER, "The GLM replaces legacy brute-force \"snapping\" with "
                   "complete syndrome/coset decoding over the 4,096 Golay "
                   "codewords")),
          ("GLM.Golay24.unique_octad", "GLM.Golay24.card_octads"),
          machine=False, check=_CHECK_STEINER),
    Topic("decoding_radius",
          _all(r"unique decoding|repairable|repair",
               r"uncorrectable|radius"),
          "A perturbation of weight w is repairable exactly while 2w < 8, "
          "the code's minimum distance: weight <= 3 has a unique nearest "
          "codeword, the one sent (`GLM.Golay.snap_unique_of_le_three`); at "
          "weight 4 two codewords can be equidistant "
          "(`GLM.Golay.snap_boundary_at_three` packages both), and from "
          "weight 5 the nearest codeword is the wrong one.",
          ((PAPER, "Within the packing radius (d ≤ 3):** Unique "
                   "nearest-codeword recovery with absolute certainty."),
           (PAPER, "The boundary is a single integer: at weight 3 the "
                   "substrate's repair is truth")),
          ("GLM.Golay.snap_boundary_at_three",
           "GLM.Golay.snap_unique_of_le_three"),
          check=_CHECK_RADIUS),
    Topic("routing_surfaces",
          _all(r"surface", r"rout"),
          "The router's surfaces are reading surfaces -- toolbox, reverse, "
          "python, frames, engineering, planner, tried in a fixed order -- "
          "and a question goes to the first that reads it. Nothing is "
          "rounded on the way: a surface in front of another changes a "
          "verdict only for text it reads "
          "(`GLM.ConnectedMachine.route_prefix_none`), and a surface added "
          "at the end changes no verdict already given "
          "(`route_append_of_some`).",
          ((PAPER, "a surface in front of another changes a verdict only for "
                   "text it reads"),),
          ("GLM.ConnectedMachine.route_prefix_none",
           "GLM.ConnectedMachine.route_append_of_some"),
          facts=(("overlay/glm_universal/runtime/toolbox.py",
                  r'Surface\("toolbox"[\s\S]*Surface\("reverse"[\s\S]*'
                  r'Surface\("python"[\s\S]*Surface\("frames"[\s\S]*'
                  r'Surface\("engineering"[\s\S]*Surface\("planner"',
                  "runtime/toolbox.py declares the six surfaces in order"),),
          disputes=(Dispute(
              "geometric boundary surfaces",
              r"geometric boundary surface|boundary surfaces",
              "the router's surfaces are the readers of a question, not "
              "geometric boundary surfaces, and no float is computed on the "
              "way, so there is nothing to skip",
              (PAPER, "tries the surfaces of a declared catalogue "
                      "(`runtime/toolbox.py`) in order")),),
          check=""),
    Topic("transcendental_delay",
          _all(r"e\^\{?-|exponential|dead[- ]time|transcendental",
               r"\bpid\b|controller"),
          "Exactly, by keeping the transcendental part symbolic: the dead "
          "time e^(-Ls) is a shift (the response is exactly 0 before t = L), "
          "exp is a named atom of the symbolic layer, and a value such as "
          "the FOPDT step response 3(1 - e^-1) is printed as a truncation "
          "of an exact process, never a float.",
          ((QSB, "Every decimal printed is a truncation of an exact process "
                 "(`real_expr`), never a float."),
           (SYMB, "So are `sin`, `cos`, `tan`, `exp` and `ln` of an "
                  "expression")),
          check=_CHECK_DELAY),
    Topic("splinter_limit",
          _all(r"integer_undecided", r"splinter|cap|limit"),
          "By a declared resource limit, never by a guess: the Omega test "
          "decides every linear question it is given with a checkable "
          "certificate, and INTEGER_UNDECIDED is kept for exactly one "
          "reason, a case spending more than NODE_LIMIT = 5000 steps, which "
          "its message names. The splinters at a bound are finitely many "
          "(`GLM.IntegerDecision.splinter_count`), so the tree is finite.",
          ((OMEGA, "The refusal is kept for exactly one reason: a case "
                   "spends more than `NODE_LIMIT` (5000) steps."),
           (OMEGA, "The one refusal left is a resource limit, declared and "
                   "never reached here.")),
          ("GLM.IntegerDecision.splinter_count",
           "GLM.IntegerDecision.pugh_no_integer_point"),
          facts=(("overlay/glm_universal/reasoning/integer_decision.py",
                  r"^NODE_LIMIT = 5000$",
                  "reasoning/integer_decision.py sets NODE_LIMIT = 5000"),),
          disputes=(Dispute(
              "infinite search tree", r"infinite",
              "the splinters at each bound are finitely many, so the search "
              "tree is finite; it is exponential in the worst case, and the "
              "declared step limit bounds it", _D_EXPONENTIAL),),
          check=_CHECK_PUGH),
    Topic("sandbox_gate",
          _all(r"python3 -i|sandbox|subprocess",
               r"overhead|latency|fork|how often"),
          "The gate runs once per reading, not per token: each answer's "
          "column-3 script runs in one fresh python3 -I with a 5-second "
          "budget before the reading is output, and a script that fails "
          "turns the reading into a refusal. Isolation is the interpreter's "
          "-I flag; the cost is one process per answer.",
          (_D_GATE, _D_COLUMN3),
          facts=(("overlay/glm_universal/runtime/question_frames.py",
                  r"^GATE_SECONDS = 5$",
                  "runtime/question_frames.py sets GATE_SECONDS = 5"),
                 ("overlay/glm_universal/runtime/question_frames.py",
                  r'\[sys\.executable, "-I", "-c", script\]',
                  "run_gate starts sys.executable with -I")),
          disputes=(Dispute(
              "per token", r"per token|per step",
              "the gate does not run per token or per step: it runs once "
              "per reading, before the reading is output", _D_GATE),),
          check=""),
    Topic("scoring_verdicts",
          _all(r"confidently wrong|score -1|\(-1\)|-1",
               r"unparsed|pars"),
          "By a structured verdict, not by parsing: every surface returns "
          "whether it answered and, if not, a named refusal code, and the "
          "scorer reads those -- a refusal with the expected code scores "
          "+1, under another code 0, an answer where a refusal was due -1; "
          "an answer scores +1 only if it holds the declared value "
          "fragment and -1 if it does not.",
          ((PAPER, "When the machine cannot answer it says so, and it says "
                   "*why*: a named reason from a declared set"),
           _D_SCORES),
          facts=(("overlay/glm_universal/evaluation/question_set_b.py",
                  r"^def _score\(",
                  "evaluation/question_set_b.py defines _score"),),
          disputes=(Dispute(
              "parsing messy text", r"pars",
              "the machine's verdicts are not parsed from free text: each "
              "surface returns a structured verdict with a named refusal "
              "code",
              (PAPER, "When the machine cannot answer it says so, and it "
                      "says *why*: a named reason from a declared set")),),
          check=_CHECK_SCORE),
)


def topic_of(t: str) -> Optional[Topic]:
    """The first topic whose cue the normalised text ``t`` meets (and, where
    the topic asks for it, which names the machine)."""
    machine = names_machine(t)
    for tp in TOPICS:
        if tp.machine and not machine:
            continue
        if tp.cue(t):
            return tp
    return None


# ===========================================================================
# 3.  THE READING
# ===========================================================================

def _script(tp: Topic, quotes: Sequence[Tuple[str, str]],
            lean: Sequence[Tuple[str, str]],
            facts: Sequence[Tuple[str, str]]) -> str:
    lines = ["import re", "from fractions import Fraction",
             "norm = lambda s: re.sub(r'\\s+', ' ', s).strip()",
             f"QUOTES = {[(str(REPO / p), f) for p, f in quotes]!r}",
             "for p, f in QUOTES:",
             "    assert norm(f) in norm(open(p, encoding='utf-8').read()), "
             "('quote moved', p, f[:60])",
             f"LEAN = {list(lean)!r}",
             "for p, n in LEAN:",
             "    src = open(p, encoding='utf-8').read()",
             "    assert re.search(r'\\b(theorem|lemma|def)\\s+' + "
             "re.escape(n) + r'\\b', src), ('theorem moved', n)",
             f"FACTS = {[(str(REPO / p), rx) for p, rx in facts]!r}",
             "for p, rx in FACTS:",
             "    assert re.search(rx, open(p, encoding='utf-8').read(), "
             "re.M), ('fact moved', p)",
             f"SCORE_PATH = "
             f"{str(PACKAGE / 'evaluation' / 'question_set_b.py')!r}"]
    body = "\n".join(lines) + "\n" + (tp.check or "")
    return body + (f"print('META {tp.key}: {len(quotes)} quotes, "
                   f"{len(lean)} theorems, {len(facts)} facts VERIFIED "
                   f"True')\n")


@dataclass
class Answer:
    """One topic's verdict on one question, in three columns."""

    topic: str
    answered: bool
    value: str
    column1: str
    column2: str
    script: str
    code: Optional[str] = None
    disputes: Tuple[str, ...] = ()
    backing: str = BACKING


def read_topic(tp: Topic, text: str,
               quotes: Optional[Tuple[Tuple[str, str], ...]] = None,
               lean: Optional[Tuple[str, ...]] = None) -> Answer:
    """The answer to ``text`` under ``tp`` (``quotes`` / ``lean`` override
    the declared evidence, for the mutation controls)."""
    nt = normalise(text)
    quotes = tp.quotes if quotes is None else quotes
    lean = tp.lean if lean is None else lean
    disputes = [d for d in tp.disputes if re.search(d.premise, nt)]
    moved: List[str] = []
    shown: List[str] = []
    for p, f in list(quotes) + [d.evidence for d in disputes if d.evidence]:
        q = quote(p, f)
        if q is None:
            moved.append(f"{p}: \"{f[:60]}\"")
        elif (p, f) in quotes:
            row = f"{p} §{q[0]}: \"{q[1]}\""
            if row not in shown:
                shown.append(row)
    lean_rows: List[Tuple[str, str]] = []
    cited: List[str] = []
    for name in lean:
        d = lean_declaration(name)
        if d is None:
            moved.append(f"Lean declaration {name}")
            continue
        lean_rows.append((str(LEAN_ROOT / d["file"]),
                          name.rsplit(".", 1)[-1]))
        cited.append(f"{name} ({d['file']}:{d['line']})")
    fact_rows: List[Tuple[str, str]] = []
    for p, rx, words in tp.facts:
        if not _fact(p, rx):
            moved.append(f"code fact: {words}")
        fact_rows.append((p, rx))
    column1 = (f"Read as a question about the machine's own engineering "
               f"(topic {tp.key}); answered from the project's documents "
               f"and the Lean development, each quote and theorem looked "
               f"up when the question was read.")
    if moved:
        return Answer(
            tp.key, False,
            "the documents no longer say what this answer rests on: "
            + "; ".join(moved),
            column1, "evidence moved: " + "; ".join(moved),
            "print('VERIFIED True')", code="CITATION_MOVED")
    parts = ["quoted: " + " | ".join(shown)]
    if cited:
        parts.append("theorems: " + ", ".join(cited))
    if tp.facts:
        parts.append("code: " + "; ".join(w for _, _, w in tp.facts))
    script = _script(tp, quotes, lean_rows, fact_rows)
    return Answer(
        tp.key, True, tp.value, column1, "; ".join(parts), script,
        disputes=tuple(f"{d.key}: {d.statement}"
                       + (f" ({d.evidence[0]}: \"{quote(*d.evidence)[1]}\")"
                          if d.evidence else "")
                       for d in disputes))


def mutated(tp: Topic, text: str, kind: str) -> Answer:
    """An answer with its evidence or its script altered (the controls of
    ``meta_question_cases.MUTATIONS``)."""
    if kind == "quote-moved":
        p, f = tp.quotes[0]
        return read_topic(tp, text, quotes=((p, f + " (altered)"),)
                          + tp.quotes[1:])
    if kind == "lean-moved":
        if not tp.lean:
            return read_topic(tp, text, quotes=((tp.quotes[0][0],
                                                 "no such sentence here"),))
        return read_topic(tp, text,
                          lean=(tp.lean[0] + "_altered",) + tp.lean[1:])
    rd = read_topic(tp, text)
    if kind == "script-quote":
        p, f = tp.quotes[0]
        rd.script = rd.script.replace(
            "QUOTES = [", "QUOTES = [(" f"{str(REPO / p)!r}, "
            "'a sentence that is not in it'), ", 1)
        return rd
    if kind == "script-claim":
        if tp.check:
            rd.script = _alter_claim(rd.script)
        else:
            p, rx, _ = tp.facts[0]
            rd.script = rd.script.replace(repr(rx)[1:-1],
                                          repr(rx + "ALTERED")[1:-1], 1)
        return rd
    raise ValueError(kind)


def _alter_claim(script: str) -> str:
    """Change one asserted number of the mathematical check."""
    for a, b in ((" == 6", " == 7"), ("== 759", "== 758"), ("== 3 and", "== 2 and"),
                 ("< Fraction(1896362", "< Fraction(1896361"),
                 ("== I\n", "!= I\n"), ("== det_frac(A)", "!= det_frac(A)"),
                 ("== 1\n", "== 2\n"), ("== -1\n", "== 1\n")):
        if a in script:
            return script.replace(a, b, 1)
    return script.replace("print('META", "assert False\nprint('META", 1)

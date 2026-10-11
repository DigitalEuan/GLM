"""``glm_universal.reasoning.info_inequality`` -- linear information
inequalities decided with a certificate either way (Phase 107,
``studies/DERIVATION_TWO_STUDY.md``).

Why it exists
-------------
Three questions of the outside set (52, 54 and the information-theory half
of track P) ask for a *proof* of an inequality between entropies and mutual
informations.  Every such inequality that is linear in the joint entropies
``h(S) = H(X_S)`` of ``n`` variables is a statement about the cone of
entropy vectors, and the classical way to prove one (Yeung's framework) is a
**Shannon-type certificate**: the claim, written as ``c . h >= 0``, is a
nonnegative combination of the *elemental* inequalities

* ``H(X_i | X_rest) >= 0`` and
* ``I(X_i ; X_j | X_K) >= 0`` for ``K`` a subset of the other variables,

plus rational multiples of the givens (``g . h = 0``).  Finding the
coefficients is a linear feasibility problem, solved here exactly with
:class:`fractions.Fraction` by a two-phase simplex method under Bland's rule.

When no certificate exists the claim is not implied by the Shannon
inequalities, and the machine looks for a **distribution** that violates
it: each variable a GF(2)-linear function of independent fair bits, so that
every joint entropy is an integer number of bits (the rank of the stacked
forms) and the violation is exact.  For three variables and givens that are
themselves Shannon-nonnegative (independences, Markov conditions,
functional dependences) this is complete: the closure of the entropic cone
is the Shannon cone, every extreme ray of the Shannon cone is the entropy
vector of such a distribution, and the givens cut out a face whose extreme
rays are among them.  For four variables a claim may be neither certified
nor refuted that way -- the Zhang-Yeung inequality is true and has no
Shannon certificate, Ingleton's is false for some distributions and true
for every linear one -- and the machine refuses it ``NOT_SHANNON``,
undecided, rather than guess.

Syntax
------
``GIVEN, GIVEN |- CLAIM``; each side a sum of rational multiples of
``H(A,B|C,D)``, ``I(A,B;C|D)`` and numbers, compared by ``>=``, ``<=`` or
``=``.  Variable names are identifiers.  Integers and ``Fraction`` only
(D7).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations, product
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = ["InequalityError", "MAX_VARIABLES", "Linear", "parse_problem",
           "elementals", "elemental_text", "simplex_feasible", "Verdict",
           "decide", "linear_distribution_entropies", "rank_gf2",
           "show_linear", "candidate_distributions"]

#: Refused beyond this many variables.
MAX_VARIABLES = 4


class InequalityError(Exception):
    """A refusal, with the machine's code."""

    def __init__(self, code: str, why: str):
        super().__init__(f"{code}: {why}")
        self.code = code
        self.why = why


# ===========================================================================
# 1.  LINEAR FORMS IN THE JOINT ENTROPIES
# ===========================================================================

#: A linear form: ``{frozenset of variable names: coefficient}``; the empty
#: set carries the constant term (``h(empty) = 0``, so a constant is a
#: number).
Linear = Dict[frozenset, Fraction]


def _add(a: Linear, b: Linear, k: Fraction = Fraction(1)) -> Linear:
    out = dict(a)
    for s, c in b.items():
        out[s] = out.get(s, Fraction(0)) + k * c
        if out[s] == 0:
            del out[s]
    return out


def _H(s: Sequence[str], cond: Sequence[str] = ()) -> Linear:
    a, c = frozenset(s) | frozenset(cond), frozenset(cond)
    out: Linear = {}
    if a:
        out = _add(out, {a: Fraction(1)})
    if c:
        out = _add(out, {c: Fraction(-1)})
    return out


def _I(a: Sequence[str], b: Sequence[str], cond: Sequence[str] = ()) -> Linear:
    A, B, C = frozenset(a), frozenset(b), frozenset(cond)
    out: Linear = {}
    for s, k in ((A | C, 1), (B | C, 1), (A | B | C, -1), (C, -1)):
        if s:
            out = _add(out, {s: Fraction(k)})
    return out


_TOKEN = re.compile(r"\s*(?:(\d+(?:/\d+)?)|([A-Za-z_][A-Za-z0-9_]*)|"
                    r"(>=|<=|=|\||;|,|\(|\)|\+|-|\*))")


def _tokens(text: str) -> List[str]:
    out, pos = [], 0
    text = text.replace("≥", ">=").replace("≤", "<=").replace("−", "-")
    while pos < len(text):
        if text[pos:].strip() == "":
            break
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise InequalityError("UNREADABLE",
                                  f"cannot read {text[pos:pos + 12]!r}")
        out.append(next(g for g in m.groups() if g is not None))
        pos = m.end()
    return out


class _Reader:
    def __init__(self, toks: List[str]):
        self.t, self.i = toks, 0

    def peek(self) -> Optional[str]:
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self, want: Optional[str] = None) -> str:
        tok = self.peek()
        if tok is None or (want is not None and tok != want):
            raise InequalityError("UNREADABLE",
                                  f"expected {want or 'more'}, got {tok!r}")
        self.i += 1
        return tok

    def names(self, stop: Sequence[str]) -> List[str]:
        out = [self.name()]
        while self.peek() == ",":
            self.take(",")
            out.append(self.name())
        if self.peek() not in stop:
            raise InequalityError("UNREADABLE",
                                  f"expected one of {list(stop)}, got "
                                  f"{self.peek()!r}")
        return out

    def name(self) -> str:
        tok = self.take()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tok):
            raise InequalityError("UNREADABLE", f"{tok!r} is not a variable")
        return tok

    def atom(self) -> Linear:
        tok = self.take()
        if tok == "H" and self.peek() == "(":
            self.take("(")
            a = self.names(("|", ")"))
            c: List[str] = []
            if self.peek() == "|":
                self.take("|")
                c = self.names((")",))
            self.take(")")
            return _H(a, c)
        if tok == "I" and self.peek() == "(":
            self.take("(")
            a = self.names((";",))
            self.take(";")
            b = self.names(("|", ")"))
            c = []
            if self.peek() == "|":
                self.take("|")
                c = self.names((")",))
            self.take(")")
            return _I(a, b, c)
        if tok == "(":
            e = self.expr()
            self.take(")")
            return e
        raise InequalityError("UNREADABLE", f"unexpected {tok!r}")

    def term(self) -> Linear:
        tok = self.peek()
        if tok is not None and re.fullmatch(r"\d+(?:/\d+)?", tok):
            self.take()
            k = Fraction(tok)
            if self.peek() == "*":
                self.take("*")
                return {s: k * c for s, c in self.atom().items()}
            return {frozenset(): k} if k else {}
        return self.atom()

    def expr(self) -> Linear:
        sign = Fraction(1)
        if self.peek() == "-":
            self.take("-")
            sign = Fraction(-1)
        out = _add({}, self.term(), sign)
        while self.peek() in ("+", "-"):
            k = Fraction(1) if self.take() == "+" else Fraction(-1)
            out = _add(out, self.term(), k)
        return out


def _relation(text: str) -> Tuple[Linear, str, Linear]:
    toks = _tokens(text)
    r = _Reader(toks)
    lhs = r.expr()
    op = r.take()
    if op not in (">=", "<=", "="):
        raise InequalityError("UNREADABLE", f"expected >=, <= or =, got {op!r}")
    rhs = r.expr()
    if r.peek() is not None:
        raise InequalityError("UNREADABLE", f"trailing {r.peek()!r}")
    return lhs, op, rhs


def _split_givens(text: str) -> List[str]:
    out, depth, cur = [], 0, ""
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return [g.strip() for g in out if g.strip()]


@dataclass
class Problem:
    names: Tuple[str, ...]
    givens: List[Linear]            # each g . h = 0
    given_texts: List[str]
    claims: List[Linear]            # each c . h >= 0 (two for an equality)
    claim_text: str
    op: str
    lhs: Linear
    rhs: Linear


def parse_problem(text: str, max_variables: int = MAX_VARIABLES) -> Problem:
    """``GIVENS |- CLAIM`` read into linear forms (refused past
    ``max_variables``; Phase 119's five-variable layer passes 5)."""
    if "|-" not in text:
        raise InequalityError("UNREADABLE", "write GIVENS |- CLAIM")
    left, right = text.split("|-", 1)
    givens, gtexts = [], []
    for g in _split_givens(left):
        lhs, op, rhs = _relation(g)
        if op != "=":
            raise InequalityError("UNREADABLE",
                                  f"a given must be an equality: {g!r}")
        givens.append(_add(lhs, rhs, Fraction(-1)))
        gtexts.append(g)
    lhs, op, rhs = _relation(right.strip())
    diff = _add(lhs, rhs, Fraction(-1))
    claims = {">=": [diff], "<=": [{s: -c for s, c in diff.items()}],
              "=": [diff, {s: -c for s, c in diff.items()}]}[op]
    names: List[str] = []
    for form in givens + [lhs, rhs]:
        for s in sorted(form, key=lambda x: sorted(x)):
            for v in sorted(s):
                if v not in names:
                    names.append(v)
    names = _order(text, names)
    if len(names) > max_variables:
        raise InequalityError("TOO_MANY_VARIABLES",
                              f"{len(names)} variables; the exact search is "
                              f"declared for at most {max_variables}")
    return Problem(tuple(names), givens, gtexts, claims, right.strip(), op,
                   lhs, rhs)


def _order(text: str, names: List[str]) -> List[str]:
    pos = {n: (m.start() if (m := re.search(rf"\b{re.escape(n)}\b", text))
               else 0) for n in names}
    return sorted(names, key=lambda n: (pos[n], n))


# ===========================================================================
# 2.  THE ELEMENTAL INEQUALITIES
# ===========================================================================

#: ``("H", i)`` is ``H(X_i | rest)``; ``("I", i, j, K)`` is
#: ``I(X_i; X_j | X_K)``.
Elemental = tuple


def elementals(names: Sequence[str]) -> List[Elemental]:
    n = len(names)
    out: List[Elemental] = [("H", i) for i in range(n)]
    for i, j in combinations(range(n), 2):
        rest = [k for k in range(n) if k not in (i, j)]
        for r in range(len(rest) + 1):
            for K in combinations(rest, r):
                out.append(("I", i, j, K))
    return out


def elemental_form(e: Elemental, names: Sequence[str]) -> Linear:
    if e[0] == "H":
        rest = [names[k] for k in range(len(names)) if k != e[1]]
        return _H([names[e[1]]], rest)
    _, i, j, K = e
    return _I([names[i]], [names[j]], [names[k] for k in K])


def elemental_text(e: Elemental, names: Sequence[str]) -> str:
    if e[0] == "H":
        rest = [names[k] for k in range(len(names)) if k != e[1]]
        return f"H({names[e[1]]}|{','.join(rest)})" if rest else \
            f"H({names[e[1]]})"
    _, i, j, K = e
    cond = ",".join(names[k] for k in K)
    return f"I({names[i]};{names[j]}" + (f"|{cond})" if cond else ")")


def _coords(names: Sequence[str]) -> List[frozenset]:
    n = len(names)
    return [frozenset(names[k] for k in range(n) if m >> k & 1)
            for m in range(1, 1 << n)]


# ===========================================================================
# 3.  EXACT LINEAR FEASIBILITY
# ===========================================================================

def simplex_feasible(A: List[List[Fraction]], b: List[Fraction]
                     ) -> Optional[List[Fraction]]:
    """A vertex ``x >= 0`` with ``A x = b``, or ``None`` when there is none.

    Phase one of the simplex method on ``A x + s = b`` (rows sign-flipped
    so that ``b >= 0``), with Bland's rule, so it terminates; exact."""
    m, n = len(A), len(A[0]) if A else 0
    rows = []
    for i in range(m):
        sgn = -1 if b[i] < 0 else 1
        rows.append([sgn * a for a in A[i]] +
                    [Fraction(1) if k == i else Fraction(0)
                     for k in range(m)] + [sgn * b[i]])
    basis = [n + i for i in range(m)]
    # objective: minimise the sum of artificials -> reduced costs
    width = n + m

    def reduced() -> List[Fraction]:
        cost = [Fraction(0)] * width
        for k in range(n, width):
            cost[k] = Fraction(1)
        red = list(cost)
        for i, bv in enumerate(basis):
            cb = cost[bv]
            if cb:
                for k in range(width):
                    red[k] -= cb * rows[i][k]
        return red

    while True:
        red = reduced()
        enter = next((k for k in range(width) if red[k] < 0), None)
        if enter is None:
            break
        ratios = [(rows[i][-1] / rows[i][enter], basis[i], i)
                  for i in range(m) if rows[i][enter] > 0]
        if not ratios:                       # unbounded: cannot happen here
            break
        _, _, piv = min(ratios)
        pv = rows[piv][enter]
        rows[piv] = [x / pv for x in rows[piv]]
        for i in range(m):
            if i != piv and rows[i][enter]:
                f = rows[i][enter]
                rows[i] = [x - f * y for x, y in zip(rows[i], rows[piv])]
        basis[piv] = enter
    x = [Fraction(0)] * width
    for i, bv in enumerate(basis):
        x[bv] = rows[i][-1]
    if any(x[k] != 0 for k in range(n, width)):
        return None
    return x[:n]


def _certificate(problem: Problem, claim: Linear
                 ) -> Optional[Tuple[List[Tuple[Elemental, Fraction]],
                                     List[Tuple[int, Fraction]]]]:
    names = problem.names
    coords = _coords(names)
    els = elementals(names)
    cols: List[Linear] = [elemental_form(e, names) for e in els]
    for g in problem.givens:
        cols.append(g)
        cols.append({s: -c for s, c in g.items()})
    if claim.get(frozenset(), 0):
        const = claim[frozenset()]
        if const < 0:
            return None
    A = [[col.get(s, Fraction(0)) for col in cols] for s in coords]
    b = [claim.get(s, Fraction(0)) for s in coords]
    x = simplex_feasible(A, b)
    if x is None:
        return None
    lam = [(e, x[k]) for k, e in enumerate(els) if x[k]]
    mu = []
    for j in range(len(problem.givens)):
        v = x[len(els) + 2 * j] - x[len(els) + 2 * j + 1]
        if v:
            mu.append((j, v))
    return lam, mu


# ===========================================================================
# 4.  LINEAR DISTRIBUTIONS
# ===========================================================================

def rank_gf2(vectors: Sequence[int]) -> int:
    basis: List[int] = []
    for v in vectors:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def linear_distribution_entropies(forms: Sequence[Sequence[int]],
                                  names: Sequence[str]) -> Dict[frozenset, int]:
    """``H(X_S)`` in bits for variables that are the given GF(2)-linear forms
    (bit masks) of independent fair bits: the rank of the stacked forms."""
    out = {}
    for s in _coords(names):
        vecs = [f for k, nm in enumerate(names) if nm in s for f in forms[k]]
        out[s] = rank_gf2(vecs)
    return out


def candidate_distributions(n: int) -> List[Tuple[int, Tuple[Tuple[int, ...],
                                                               ...]]]:
    """``(bits, forms per variable)``: every variable one linear form (or
    constant) of up to three fair bits, then every variable up to two forms
    of two bits.  For three variables the first family already contains
    every extreme ray of the Shannon cone."""
    out = []
    seen = set()
    for k in (1, 2, 3):
        for choice in product(range(1 << k), repeat=n):
            forms = tuple((c,) if c else () for c in choice)
            if forms not in seen:
                seen.add(forms)
                out.append((k, forms))
    if n >= 4:
        two = [()] + [(a,) for a in range(1, 4)] + \
              [(a, b) for a in range(1, 4) for b in range(a + 1, 4)]
        for choice in product(two, repeat=n):
            if choice not in seen:
                seen.add(choice)
                out.append((2, choice))
    return out


def show_linear(forms: Sequence[Sequence[int]], names: Sequence[str],
                bits: int) -> str:
    def form(f: int) -> str:
        terms = [f"u{k + 1}" for k in range(bits) if f >> k & 1]
        return " xor ".join(terms)
    parts = []
    for nm, fs in zip(names, forms):
        if not fs:
            parts.append(f"{nm} = 0")
        elif len(fs) == 1:
            parts.append(f"{nm} = {form(fs[0])}")
        else:
            parts.append(f"{nm} = (" + ", ".join(form(f) for f in fs) + ")")
    return ("; ".join(parts) +
            f" (u1..u{bits} independent fair bits)")


def _value(form: Linear, h: Dict[frozenset, int]) -> Fraction:
    return sum((c * (h[s] if s else 1) for s, c in form.items()), Fraction(0))


# ===========================================================================
# 5.  THE DECISION
# ===========================================================================

@dataclass
class Verdict:
    kind: str                          # proved | NOT_VALID | NOT_SHANNON
    problem: Problem
    certificates: List[Tuple[List[Tuple[Elemental, Fraction]],
                             List[Tuple[int, Fraction]]]] = field(
                                 default_factory=list)
    distribution: Optional[Tuple[int, Tuple[Tuple[int, ...], ...]]] = None
    entropies: Optional[Dict[frozenset, int]] = None
    violated: Optional[int] = None     # which claim (0, or 1 for <= of =)
    complete: bool = False             # the NOT_VALID search was complete
    polymatroid: Optional[Dict[frozenset, Fraction]] = None

    def lines(self) -> List[str]:
        """The certificate as identities ``claim = sum of terms``."""
        out = []
        names = self.problem.names
        for k, (lam, mu) in enumerate(self.certificates):
            terms = []
            for e, c in lam:
                terms.append((c, elemental_text(e, names)))
            for j, c in mu:
                terms.append((c, "[" + _given_lhs(self.problem.given_texts[j])
                              + "]"))
            side = _claim_side(self.problem, k)
            out.append(f"{side} = " + _signed(terms))
        return out


def _signed(terms: List[Tuple[Fraction, str]]) -> str:
    if not terms:
        return "0"
    out = ""
    for k, (c, t) in enumerate(terms):
        neg = c < 0
        a = -c if neg else c
        body = t if a == 1 else f"{a}*{t}"
        if k == 0:
            out = ("-" if neg else "") + body
        else:
            out += (" - " if neg else " + ") + body
    return out


def _coef(c: Fraction) -> str:
    return "" if c == 1 else (f"({c})*" if c.denominator != 1 or c < 0
                               else f"{c}*")


def _given_lhs(g: str) -> str:
    lhs, rhs = g.split("=", 1)
    return lhs.strip() if rhs.strip() in ("0", "") else \
        f"{lhs.strip()} - ({rhs.strip()})"


def _claim_side(p: Problem, k: int) -> str:
    left, right = _split_rel(p.claim_text)
    if p.op == ">=" or (p.op == "=" and k == 0):
        a, b = left, right
    else:
        a, b = right, left
    if b.strip() == "0":
        return a
    return f"{a} - ({b})" if re.search(r"[+-]", b) else f"{a} - {b}"


def _split_rel(text: str) -> Tuple[str, str]:
    for op in (">=", "<=", "="):
        if op in text:
            a, b = text.split(op, 1)
            return a.strip(), b.strip()
    return text, "0"


def _givens_nonnegative(problem: Problem) -> bool:
    """Every given ``g = 0`` has ``g >= 0`` Shannon-provable (so the givens
    cut out a face of the cone)."""
    bare = Problem(problem.names, [], [], [], "", ">=", {}, {})
    for g in problem.givens:
        if _certificate(bare, g) is None:
            return False
    return True


def decide(problem: Problem) -> Verdict:
    certs = []
    for k, claim in enumerate(problem.claims):
        cert = _certificate(problem, claim)
        if cert is None:
            found = _counterexample(problem, k)
            if found is not None:
                dist, h = found
                complete = len(problem.names) <= 3 and \
                    _givens_nonnegative(problem)
                return Verdict("NOT_VALID", problem, certs, dist, h, k,
                               complete)
            return Verdict("NOT_SHANNON", problem, certs, violated=k,
                           polymatroid=polymatroid_witness(problem, k))
        certs.append(cert)
    return Verdict("proved", problem, certs)


def polymatroid_witness(problem: Problem, k: int
                        ) -> Optional[Dict[frozenset, Fraction]]:
    """A vector ``h`` meeting every elemental inequality and every given,
    with ``c . h = -1``: by Farkas' lemma it exists exactly when the claim
    has no Shannon-type certificate, and it is the checkable witness of
    that absence (a polymatroid, not necessarily a distribution)."""
    names = problem.names
    coords = _coords(names)
    nc = len(coords)
    els = [elemental_form(e, names) for e in elementals(names)]
    ne = len(els)
    width = 2 * nc + ne
    A: List[List[Fraction]] = []
    b: List[Fraction] = []

    def row(form: Linear, slack: Optional[int]) -> List[Fraction]:
        r = [Fraction(0)] * width
        for i, s in enumerate(coords):
            c = form.get(s, Fraction(0))
            r[i], r[nc + i] = c, -c
        if slack is not None:
            r[2 * nc + slack] = Fraction(-1)
        return r
    for i, e in enumerate(els):
        A.append(row(e, i))
        b.append(Fraction(0))
    for g in problem.givens:
        A.append(row(g, None))
        b.append(Fraction(0))
    A.append(row(problem.claims[k], None))
    b.append(Fraction(-1) - problem.claims[k].get(frozenset(), Fraction(0)))
    x = simplex_feasible(A, b)
    if x is None:
        return None
    return {s: x[i] - x[nc + i] for i, s in enumerate(coords)}


def _counterexample(problem: Problem, k: int):
    names = problem.names
    claim = problem.claims[k]
    for bits, forms in candidate_distributions(len(names)):
        h = linear_distribution_entropies(forms, names)
        if all(_value(g, h) == 0 for g in problem.givens) and \
                _value(claim, h) < 0:
            return (bits, forms), h
    return None

"""``glm_universal.reasoning.non_shannon`` -- information inequalities past
the Shannon cone (Phase 118, ``studies/DERIVATION_THREE_STUDY.md``).

Why it exists
-------------
Phase 107's :mod:`~glm_universal.reasoning.info_inequality` decides a linear
claim in the joint entropies of up to four variables three ways: a
Shannon-type certificate, a counterexample made of GF(2)-linear functions of
fair bits, or ``NOT_SHANNON`` -- undecided, because no Shannon certificate
exists (a polymatroid witness shows it) and no linear distribution violates
the claim.  Both of the declared four-variable claims of that round landed
there: the Zhang-Yeung inequality, which is true, and Ingleton's, which is
false for entropy and true for every linear distribution.

This module takes a ``NOT_SHANNON`` claim two steps further.

1. **A non-Shannon certificate.**  The claim is tested against the cone cut
   out by the elemental inequalities *and* the twelve instances of the
   Zhang-Yeung inequality on the four variables
   (``ZY(a, b; c, d) = I(a;b) + I(a;c,d) + 3 I(c;d|a) + I(c;d|b) - 2 I(c;d)
   >= 0`` for each ordered pair ``a, b`` and the other two as ``c, d``),
   by the same exact simplex.  Each instance is itself certified by the copy
   lemma: a fifth variable ``R``, a copy of ``c`` over ``{a, d}`` (the same
   joint law with every subset of ``{a, d}``, and ``I(R; b, c | a, d) =
   0``), turns the instance into a Shannon-type identity over five
   variables, eleven elemental terms plus multiples of the copy conditions
   (found once by the simplex and relabelled).  Verdict
   ``proved_non_shannon``.  What is *not* re-derived is the copy lemma
   itself -- that every law of four variables has such a fifth variable,
   ``p(a, b, c, d) p(r | a, d)`` -- which the reading names.
2. **An entropic counterexample.**  A pool of laws with rational
   probabilities on four binary variables -- a curated head (the four-atom
   law ``1/3, 1/3, 1/6, 1/6`` on ``0000, 1111, 1010, 1001`` that breaks
   Ingleton) and a deterministic sweep of small supports and weights -- is
   screened in integer fixed point, and a candidate is then decided **exactly**:
   every joint entropy is a rational combination of ``log2`` of primes, and
   the sign of such a combination is the comparison of two integers.
   Verdict ``NOT_VALID_ENTROPIC``.

Otherwise the claim stays ``NOT_SHANNON``, undecided -- now meaning that
neither a Shannon nor a Zhang-Yeung certificate exists and no law in the
pool violates it.

Integers and ``Fraction`` only (D7): the screen is integer fixed point and
only chooses which candidates to decide exactly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from fractions import Fraction
from functools import lru_cache
from itertools import combinations, permutations, product
from typing import Dict, List, Optional, Sequence, Tuple

from . import info_inequality as II

__all__ = ["ZY_TEXT", "zy_form", "zy_instances", "copy_conditions",
           "zy_copy_certificate", "zy_certificate_text", "Beyond", "decide_beyond", "law_pool",
           "log_entropies", "lf_value", "lf_sign", "factor_log2",
           "INGLETON_LAW"]

#: The canonical instance, as the reading prints it.
ZY_TEXT = ("2*I(c;d) <= I(a;b) + I(a;c,d) + 3*I(c;d|a) + I(c;d|b)")

#: ``(atoms, weights)``: the four-atom law that breaks Ingleton.
INGLETON_LAW: Tuple[Tuple[Tuple[int, ...], ...], Tuple[Fraction, ...]] = (
    ((0, 0, 0, 0), (1, 1, 1, 1), (1, 0, 1, 0), (1, 0, 0, 1)),
    (Fraction(1, 3), Fraction(1, 3), Fraction(1, 6), Fraction(1, 6)))


# ===========================================================================
# 1.  THE ZHANG-YEUNG INSTANCES AND THEIR COPY CERTIFICATES
# ===========================================================================

def zy_form(a: str, b: str, c: str, d: str) -> II.Linear:
    """``ZY(a, b; c, d)`` as a linear form, ``>= 0``."""
    out: II.Linear = {}
    for form, k in ((II._I([a], [b]), 1), (II._I([a], [c, d]), 1),
                    (II._I([c], [d], [a]), 3), (II._I([c], [d], [b]), 1),
                    (II._I([c], [d]), -2)):
        out = II._add(out, form, Fraction(k))
    return out


def zy_instances(names: Sequence[str]) -> List[Tuple[Tuple[str, str, str,
                                                             str], II.Linear]]:
    """The twelve instances on four variables (symmetric in ``c, d``)."""
    out = []
    for a, b in permutations(names, 2):
        c, d = [x for x in names if x not in (a, b)]
        out.append(((a, b, c, d), zy_form(a, b, c, d)))
    return out


def copy_conditions(a: str, b: str, c: str, d: str, r: str = "R"
                    ) -> List[Tuple[str, II.Linear]]:
    """``R`` a copy of ``c`` over ``{a, d}``: ``(text, form = 0)``."""
    out = []
    for S in ((), (d,), (a,), (a, d)):
        lhs = II._H([r] + list(S))
        rhs = II._H([c] + list(S))
        out.append((f"H({','.join([r] + list(S))}) = "
                    f"H({','.join([c] + list(S))})",
                    II._add(lhs, rhs, Fraction(-1))))
    out.append((f"I({r};{b},{c}|{a},{d}) = 0", II._I([r], [b, c], [a, d])))
    return out


@lru_cache(maxsize=1)
def _canonical_copy_certificate():
    names = ("a", "b", "c", "d", "R")
    conds = copy_conditions("a", "b", "c", "d")
    form = zy_form("a", "b", "c", "d")
    pr = II.Problem(names, [g for _, g in conds], [t for t, _ in conds],
                    [form], ZY_TEXT, ">=", {}, {})
    cert = II._certificate(pr, form)
    if cert is None:                                   # pragma: no cover
        raise RuntimeError("the copy certificate of Zhang-Yeung was not found")
    return cert


def zy_copy_certificate(a: str, b: str, c: str, d: str
                        ) -> Tuple[List[Tuple[tuple, Fraction]],
                                   List[Tuple[int, Fraction]]]:
    """The five-variable certificate of ``ZY(a, b; c, d)``, relabelled:
    ``(elementals over (a, b, c, d, R) with coefficients, [(index into
    copy_conditions(a, b, c, d), coefficient)])``.  The elemental indices
    refer to positions in ``(a, b, c, d, R)``, so one certificate serves
    every instance."""
    lam, mu = _canonical_copy_certificate()
    return list(lam), list(mu)


def zy_certificate_text(a: str, b: str, c: str, d: str) -> str:
    """``ZY(a,b;c,d) = sum of elementals + multiples of the copy
    conditions``, over ``(a, b, c, d, R)``."""
    lam, mu = zy_copy_certificate(a, b, c, d)
    names = five_names(a, b, c, d)
    conds = copy_conditions(a, b, c, d)
    terms = [(k, II.elemental_text(e, names)) for e, k in lam]
    def cond(t: str) -> str:
        return t[:-4] if t.endswith(" = 0") else t.replace(" = ", " - ")
    terms += [(k, "[" + cond(conds[j][0]) + "]") for j, k in mu]
    return f"ZY({a},{b};{c},{d}) = " + II._signed(terms)


def five_names(a: str, b: str, c: str, d: str) -> Tuple[str, ...]:
    return (a, b, c, d, "R")


# ===========================================================================
# 2.  EXACT ENTROPIES OF RATIONAL LAWS
# ===========================================================================

LogForm = Dict[int, Fraction]          # {prime: coefficient of log2(prime)}


def _factor(n: int) -> Dict[int, int]:
    out: Dict[int, int] = {}
    p = 2
    while p * p <= n:
        while n % p == 0:
            out[p] = out.get(p, 0) + 1
            n //= p
        p += 1
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


def factor_log2(q: Fraction) -> LogForm:
    q = Fraction(q)
    out: Dict[int, Fraction] = {}
    for p, e in _factor(q.numerator).items():
        out[p] = out.get(p, Fraction(0)) + e
    for p, e in _factor(q.denominator).items():
        out[p] = out.get(p, Fraction(0)) - e
    return {p: e for p, e in out.items() if e}


def _lf_add(a: LogForm, b: LogForm, k: Fraction = Fraction(1)) -> LogForm:
    out = dict(a)
    for p, e in b.items():
        out[p] = out.get(p, Fraction(0)) + k * e
        if out[p] == 0:
            del out[p]
    return out


def log_entropies(atoms: Sequence[Sequence[int]], weights: Sequence[Fraction],
                  names: Sequence[str]) -> Dict[frozenset, LogForm]:
    """Every joint entropy (bits) of a law on tuples, exactly."""
    out: Dict[frozenset, LogForm] = {}
    n = len(names)
    for r in range(1, n + 1):
        for S in combinations(range(n), r):
            marg: Dict[tuple, Fraction] = {}
            for x, w in zip(atoms, weights):
                key = tuple(x[k] for k in S)
                marg[key] = marg.get(key, Fraction(0)) + w
            h: LogForm = {}
            for w in marg.values():
                if w:
                    h = _lf_add(h, factor_log2(w), -w)
            out[frozenset(names[k] for k in S)] = h
    return out


def lf_value(form: II.Linear, h: Dict[frozenset, LogForm]) -> LogForm:
    """The claim's value at an exact entropy vector; a constant ``c`` is
    ``c`` bits, ``c * log2(2)``."""
    out: LogForm = {}
    for s, c in form.items():
        out = _lf_add(out, h[s] if s else {2: Fraction(1)}, c)
    return out


def lf_sign(f: LogForm) -> int:
    """The sign of ``sum e_p log2 p``, decided by comparing two integers."""
    f = {p: e for p, e in f.items() if e}
    if not f:
        return 0
    den = 1
    for e in f.values():
        den = den * e.denominator // math.gcd(den, e.denominator)
    pos = neg = 1
    for p, e in f.items():
        n = int(e * den)
        if n > 0:
            pos *= p ** n
        else:
            neg *= p ** (-n)
    return (pos > neg) - (pos < neg)


def lf_text(f: LogForm) -> str:
    terms = []
    for p in sorted(f):
        e = f[p]
        if p == 2:
            terms.append(f"{e}")
        else:
            terms.append(f"{e}*log2({p})")
    return " + ".join(terms).replace("+ -", "- ") if terms else "0"


#: Fractional bits of the fixed-point screen.
FX_BITS = 48


@lru_cache(maxsize=None)
def log2_fixed(n: int, bits: int = FX_BITS) -> int:
    """``log2(n) * 2**bits`` for a positive integer ``n``, rounded down to an
    integer, computed with integers only: the integer part is the bit length,
    and each fractional bit is read by squaring the mantissa (kept to
    ``bits + 32`` bits).  The error is below ``2**-(bits - 1)``, which is all
    the screen needs -- every verdict is decided exactly afterwards."""
    if n <= 0:
        raise ValueError("log2_fixed needs a positive integer")
    e = n.bit_length() - 1
    prec = bits + 32
    x = (n << prec) >> e                # mantissa in [2**prec, 2**(prec + 1))
    two = 2 << prec
    frac = 0
    for _ in range(bits):
        x = (x * x) >> prec
        frac <<= 1
        if x >= two:
            x >>= 1
            frac |= 1
    return (e << bits) | frac


def _fixed_entropies(atoms, weights, n) -> Dict[int, int]:
    """Every joint entropy, in bits times ``2**FX_BITS``, as an integer
    (screen only; within a few units of the last place)."""
    out = {}
    for mask in range(1, 1 << n):
        idx = [k for k in range(n) if mask >> k & 1]
        marg: Dict[tuple, Fraction] = {}
        for x, w in zip(atoms, weights):
            key = tuple(x[k] for k in idx)
            marg[key] = marg.get(key, Fraction(0)) + w
        total = 0
        for w in marg.values():
            if w:
                a, b = w.numerator, w.denominator
                total -= (a * (log2_fixed(a) - log2_fixed(b))) // b
        out[mask] = total
    return out


@lru_cache(maxsize=4)
def law_pool(n: int = 4) -> Tuple[Tuple[Tuple[Tuple[int, ...], ...],
                                        Tuple[Fraction, ...]], ...]:
    """The search pool: the curated head, then every support of three or
    four binary tuples with weights ``w/6`` (at most 2 per denominator
    pattern ...) taken in a fixed order.  Deterministic."""
    pts = list(product((0, 1), repeat=n))
    out = []
    seen = set()
    if n == 4:
        out.append(INGLETON_LAW)
        seen.add(INGLETON_LAW)
    weight_sets = []
    for den in (3, 4, 5, 6):
        for k in (3, 4):
            for ws in product(range(1, den), repeat=k):
                if sum(ws) == den:
                    weight_sets.append(tuple(Fraction(w, den) for w in ws))
    for k in (3, 4):
        for sup in combinations(pts, k):
            for ws in weight_sets:
                if len(ws) != k:
                    continue
                law = (tuple(sup), ws)
                if law not in seen:
                    seen.add(law)
                    out.append(law)
    return tuple(out)


# ===========================================================================
# 3.  THE DECISION PAST THE SHANNON CONE
# ===========================================================================

@dataclass
class Beyond:
    kind: str            # proved_non_shannon | NOT_VALID_ENTROPIC | NOT_SHANNON
    problem: II.Problem
    #: per claim: (elementals, givens, ZY instances with coefficients)
    certificates: List[Tuple[List[Tuple[tuple, Fraction]],
                             List[Tuple[int, Fraction]],
                             List[Tuple[Tuple[str, str, str, str], Fraction]]]
                       ] = field(default_factory=list)
    law: Optional[Tuple[Tuple[Tuple[int, ...], ...], Tuple[Fraction, ...]]] = None
    entropies: Optional[Dict[frozenset, LogForm]] = None
    violated: Optional[int] = None
    violation: Optional[LogForm] = None    # claim value (< 0) at the law
    polymatroid: Optional[Dict[frozenset, Fraction]] = None
    searched: int = 0

    def instances(self) -> List[Tuple[str, str, str, str]]:
        seen = []
        for _, _, nu in self.certificates:
            for inst, _ in nu:
                if inst not in seen:
                    seen.append(inst)
        return seen

    def lines(self) -> List[str]:
        names = self.problem.names
        out = []
        for k, (lam, mu, nu) in enumerate(self.certificates):
            terms = [(c, II.elemental_text(e, names)) for e, c in lam]
            terms += [(c, "[" + II._given_lhs(self.problem.given_texts[j]) +
                       "]") for j, c in mu]
            terms += [(c, "ZY(" + ",".join(inst[:2]) + ";" +
                       ",".join(inst[2:]) + ")") for inst, c in nu]
            out.append(f"{II._claim_side(self.problem, k)} = " +
                       II._signed(terms))
        return out


def _zy_certificate(problem: II.Problem, claim: II.Linear):
    names = problem.names
    if len(names) != 4:
        return None
    coords = II._coords(names)
    els = II.elementals(names)
    insts = zy_instances(names)
    cols: List[II.Linear] = [II.elemental_form(e, names) for e in els]
    for g in problem.givens:
        cols.append(g)
        cols.append({s: -c for s, c in g.items()})
    cols += [f for _, f in insts]
    if claim.get(frozenset(), 0) < 0:
        return None
    A = [[col.get(s, Fraction(0)) for col in cols] for s in coords]
    b = [claim.get(s, Fraction(0)) for s in coords]
    x = II.simplex_feasible(A, b)
    if x is None:
        return None
    ne, ng = len(els), len(problem.givens)
    lam = [(e, x[k]) for k, e in enumerate(els) if x[k]]
    mu = []
    for j in range(ng):
        v = x[ne + 2 * j] - x[ne + 2 * j + 1]
        if v:
            mu.append((j, v))
    base = ne + 2 * ng
    nu = [(inst, x[base + i]) for i, (inst, _) in enumerate(insts)
          if x[base + i]]
    return lam, mu, nu


@lru_cache(maxsize=4)
def _pool_vectors(n: int) -> Tuple[Tuple[int, ...], ...]:
    """Fixed-point entropy vectors of the pool, indexed by bit mask minus
    one (screen only)."""
    out = []
    for atoms, weights in law_pool(n):
        hf = _fixed_entropies(atoms, weights, n)
        out.append(tuple(hf[m] for m in range(1, 1 << n)))
    return tuple(out)


def _fixed_coeffs(form: II.Linear, names: Sequence[str]
                  ) -> Tuple[int, List[Tuple[int, int]], int]:
    """The form with its coefficients scaled to integers:
    ``(constant * 2**FX_BITS, [(mask - 1, coefficient)], scale)``, so that
    the screened value is ``(constant + sum c * vec[i]) / (scale *
    2**FX_BITS)`` bits."""
    scale = 1
    for c in form.values():
        scale = scale * c.denominator // math.gcd(scale, c.denominator)
    const, terms = 0, []
    for s, c in form.items():
        k = int(c * scale)
        if not s:
            const += k << FX_BITS
        else:
            terms.append((sum(1 << names.index(v) for v in s) - 1, k))
    return const, terms, scale


def screen_value(coeffs, vec) -> Fraction:
    """The screened value of a form at a fixed-point entropy vector, in
    bits (approximate: within ``2**-40`` per unit of coefficient)."""
    const, terms, scale = coeffs
    return Fraction(const + sum(c * vec[i] for i, c in terms),
                    scale << FX_BITS)


#: The screen's tolerances, in bits: a claim must be below ``-CLAIM_TOL`` to
#: be decided exactly, and a given within ``GIVEN_TOL`` of zero.
CLAIM_TOL = Fraction(1, 10 ** 9)
GIVEN_TOL = Fraction(1, 10 ** 6)


def _scaled_tol(tol: Fraction, scale: int) -> int:
    """A tolerance in bits as an integer in the screen's units (rounded
    down)."""
    t = tol * (scale << FX_BITS)
    return t.numerator // t.denominator


def _entropic_counterexample(problem: II.Problem, k: int):
    names = problem.names
    n = len(names)
    claim = _fixed_coeffs(problem.claims[k], names)
    givens = [_fixed_coeffs(g, names) for g in problem.givens]
    pool = law_pool(n)
    count = 0
    c0, cterms, cscale = claim
    ctol = _scaled_tol(CLAIM_TOL, cscale)
    gtols = [(g0, gt, _scaled_tol(GIVEN_TOL, gs)) for g0, gt, gs in givens]
    for idx, vec in enumerate(_pool_vectors(n)):
        count += 1
        if c0 + sum(c * vec[i] for i, c in cterms) > -ctol:
            continue
        if any(abs(g0 + sum(c * vec[i] for i, c in gt)) > tol
               for g0, gt, tol in gtols):
            continue
        atoms, weights = pool[idx]
        h = log_entropies(atoms, weights, names)
        if any(lf_sign(lf_value(g, h)) != 0 for g in problem.givens):
            continue
        v = lf_value(problem.claims[k], h)
        if lf_sign(v) < 0:
            return (atoms, weights), h, v, count
    return None, None, None, count


def decide_beyond(problem: II.Problem,
                  shannon: Optional[II.Verdict] = None) -> Beyond:
    """Take a claim past the Shannon cone.  ``shannon`` is Phase 107's
    verdict, if already computed; it must be ``NOT_SHANNON``."""
    v = shannon or II.decide(problem)
    if v.kind != "NOT_SHANNON":
        raise ValueError("decide_beyond is for NOT_SHANNON claims only")
    certs = []
    searched = 0
    for k, claim in enumerate(problem.claims):
        cert = _zy_certificate(problem, claim)
        if cert is not None:
            certs.append(cert)
            continue
        law, h, val, count = _entropic_counterexample(problem, k)
        searched += count
        if law is not None:
            return Beyond("NOT_VALID_ENTROPIC", problem, certs, law, h, k,
                          val, searched=searched)
        return Beyond("NOT_SHANNON", problem, certs, violated=k,
                      polymatroid=v.polymatroid, searched=searched)
    return Beyond("proved_non_shannon", problem, certs)


def law_text(law, names: Sequence[str]) -> str:
    atoms, weights = law
    parts = [f"P({''.join(map(str, x))}) = {w}" for x, w in zip(atoms, weights)]
    return (f"({','.join(names)}) with " + ", ".join(parts))

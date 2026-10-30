"""``glm_universal.runtime.derivation_three_scripts`` -- the column-3 scripts
of Phase 118 (``studies/DERIVATION_THREE_STUDY.md``).

Every script is stand-alone standard-library Python that shares no code with
the layer it checks (``reasoning.non_shannon``, ``reasoning.hamming_rd``,
``reasoning.robin``): it carries its own reader, its own algebra and its own
check, and its last line ends ``VERIFIED True`` only when every check holds.
The entropy reader and the logarithm forms are the text of Phase 107's
scripts (:mod:`glm_universal.runtime.derivation_two_scripts`), which are
themselves stand-alone.

* a non-Shannon certificate: the claim re-read, every elemental inequality
  and every Zhang-Yeung instance re-built from its definition, the
  four-variable certificate re-summed; then for every instance used, the
  copy conditions re-built from their definition and the five-variable
  certificate re-summed;
* an entropic counterexample: every marginal of the law re-summed, every
  joint entropy written as a rational combination of ``log2`` of primes,
  every given checked to vanish exactly, and the claim's value compared
  with zero by comparing two integers;
* a rate-distortion function on the whole range: the pieces re-derived from
  the sorted source, and at rational distortions inside every piece the
  test channel re-built (a channel, the source marginal, distortion exactly
  ``D``), its mutual information and the dual bound written as sums of
  logarithms and compared with the claim, the dual constraints checked
  exactly;
* a Robin eigenvalue problem: ``pi`` re-enclosed by Machin's formula,
  ``sin``, ``cos``, ``sinh`` and ``cosh`` re-enclosed by their series with
  the remainder bounded, every claimed root enclosure checked to lie in its
  interval with a certified sign change, and every printed eigenvalue
  re-rounded from the enclosure.

No float anywhere (D7).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from . import derivation_two_scripts as DS

__all__ = ["beyond_script", "rd_full_script", "robin_script"]


def _q(x) -> str:
    x = Fraction(x)
    return f"F({x.numerator}, {x.denominator})"


def _lf(form: Dict[int, Fraction]) -> str:
    return "{" + ", ".join(f"{p}: {_q(e)}" for p, e in sorted(form.items())) \
        + "}"


# ===========================================================================
# 1.  PAST THE SHANNON CONE
# ===========================================================================

_ZY = r'''
def ZY(a, b, c, d):
    out = {}
    for form, k in ((I([a], [b]), 1), (I([a], [c, d]), 1),
                    (I([c], [d], [a]), 3), (I([c], [d], [b]), 1),
                    (I([c], [d]), -2)):
        out = vec_add(out, form, k)
    return out

def copy_conditions(a, b, c, d, r='R'):
    out = []
    for S in ((), (d,), (a,), (a, d)):
        out.append(vec_add(H([r] + list(S)), H([c] + list(S)), -1))
    out.append(I([r], [b, c], [a, d]))
    return out
'''

_PRIMES = r'''
def factor(n):
    out, p = {}, 2
    while p * p <= n:
        while n % p == 0:
            out[p] = out.get(p, 0) + 1; n //= p
        p += 1
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out

def log2form(q):
    q = F(q); assert q > 0
    out = {}
    for p, e in factor(q.numerator).items():
        out[p] = out.get(p, 0) + e
    for p, e in factor(q.denominator).items():
        out[p] = out.get(p, 0) - e
    return {p: F(e) for p, e in out.items() if e}

def lf_add(a, b, k=1):
    out = dict(a)
    for p, e in b.items():
        out[p] = out.get(p, 0) + k * e
        if out[p] == 0:
            del out[p]
    return out

def lf_sign(f):
    f = {p: e for p, e in f.items() if e}
    if not f:
        return 0
    den = 1
    for e in f.values():
        den = den * e.denominator // gcd(den, e.denominator)
    pos = neg = 1
    for p, e in f.items():
        n = int(e * den)
        if n > 0:
            pos *= p ** n
        else:
            neg *= p ** (-n)
    return (pos > neg) - (pos < neg)
'''


def beyond_script(names: Sequence[str], givens: Sequence[str], claim: str,
                  kind: str, certificates=(), zy_certificates=(),
                  law=None, violated: Optional[int] = None,
                  claimed_value: Optional[Dict[int, Fraction]] = None,
                  label: str = "BEYOND-SHANNON") -> str:
    """``certificates``: per claim ``(lam, mu, nu)``; ``zy_certificates``:
    ``[(instance, lam5)]`` with ``lam5`` the five-variable elementals over
    ``instance + ('R',)`` and the copy-condition coefficients
    ``[(index, coefficient)]``."""
    lines = [DS._ENTROPY_READER, "from math import gcd", _ZY, _PRIMES,
             f"NAMES = {list(names)!r}",
             f"GIVENS = givens_of({list(givens)!r})",
             f"CLAIMS = claims_of({claim!r})"]
    if kind == "proved_non_shannon":
        def el(e):
            return list(e[:3]) + [list(e[3])] if e[0] == "I" else list(e)
        body = []
        for lam, mu, nu in certificates:
            body.append(
                "([" + ", ".join(f"({el(e)!r}, {_q(c)})" for e, c in lam) +
                "], [" + ", ".join(f"({j}, {_q(c)})" for j, c in mu) +
                "], [" + ", ".join(f"({list(i)!r}, {_q(c)})" for i, c in nu) +
                "])")
        zys = []
        for inst, lam5, conds in zy_certificates:
            zys.append(
                f"({list(inst)!r}, [" +
                ", ".join(f"({el(e)!r}, {_q(c)})" for e, c in lam5) + "], [" +
                ", ".join(f"({j}, {_q(c)})" for j, c in conds) + "])")
        lines += [
            f"CERTS = [{', '.join(body)}]",
            f"ZY_CERTS = [{', '.join(zys)}]",
            r'''
assert len(CERTS) == len(CLAIMS)
used = set()
for claim, (lam, mu, nu) in zip(CLAIMS, CERTS):
    total = {}
    for e, c in lam:
        assert c > 0
        total = vec_add(total, elemental_vec(tuple(e), NAMES), c)
    for j, c in mu:
        total = vec_add(total, GIVENS[j], c)
    for inst, c in nu:
        assert c > 0 and sorted(inst) == sorted(NAMES)
        total = vec_add(total, ZY(*inst), c)
        used.add(tuple(inst))
    assert claim.get(frozenset(), F(0)) >= 0
    body = {s: c for s, c in claim.items() if s}
    assert total == body, ('certificate does not sum to the claim', total, body)
done = set()
for inst, lam5, conds in ZY_CERTS:
    names5 = list(inst) + ['R']
    total = {}
    for e, c in lam5:
        assert c > 0
        total = vec_add(total, elemental_vec(tuple(e), names5), c)
    cc = copy_conditions(*inst)
    for j, c in conds:
        total = vec_add(total, cc[j], c)
    assert total == ZY(*inst), ('copy certificate does not sum', inst)
    done.add(tuple(inst))
assert used <= done, 'an instance without its copy certificate'
''',
            f"print('{label}: certificate over the elemental and Zhang-Yeung "
            f"inequalities re-summed, every instance re-derived from one copy "
            f"VERIFIED True')",
        ]
    elif kind == "NOT_VALID_ENTROPIC":
        atoms, weights = law
        lines += [
            f"ATOMS = {[list(a) for a in atoms]!r}",
            "WEIGHTS = [" + ", ".join(_q(w) for w in weights) + "]",
            f"CLAIMED = {_lf(claimed_value)}",
            r'''
assert sum(WEIGHTS) == 1 and all(w > 0 for w in WEIGHTS)
h = {}
for r in range(1, len(NAMES) + 1):
    for S in combinations(range(len(NAMES)), r):
        marg = {}
        for x, w in zip(ATOMS, WEIGHTS):
            key = tuple(x[k] for k in S)
            marg[key] = marg.get(key, 0) + w
        e = {}
        for w in marg.values():
            e = lf_add(e, log2form(w), -w)
        h[frozenset(NAMES[k] for k in S)] = e
def lval(form):
    out = {}
    for s, c in form.items():
        out = lf_add(out, h[s] if s else {2: F(1)}, c)
    return out
for g in GIVENS:
    assert lf_sign(lval(g)) == 0, 'a given fails'
''',
            f"v = lval(CLAIMS[{violated}])",
            "assert v == CLAIMED, ('claimed value', v)",
            "assert lf_sign(v) < 0, 'not violated'",
            f"print('{label}: the law violates the claim (its value is a "
            f"negative sum of logarithms, decided by two integers) "
            f"VERIFIED True')",
        ]
    else:                                              # pragma: no cover
        raise ValueError(kind)
    return "\n".join(lines) + "\n"


# ===========================================================================
# 2.  RATE DISTORTION ON THE WHOLE RANGE
# ===========================================================================

def rd_full_script(probs: Sequence[Fraction],
                   pieces: Sequence[Tuple[Fraction, Fraction, int]],
                   mutate: bool = False,
                   label: str = "RATE-DISTORTION") -> str:
    lines = [_PRIMES.replace("def lf_sign", "def _unused_sign"),
             "from fractions import Fraction as F", "from math import gcd",
             "P = [" + ", ".join(_q(x) for x in probs) + "]",
             "PIECES = [" + ", ".join(f"({_q(a)}, {_q(b)}, {k})"
                                      for a, b, k in pieces) + "]",
             f"MUTANT = {mutate!r}",
             r'''
M = len(P)
assert sum(P) == 1 and all(x > 0 for x in P)
order = sorted(range(M), key=lambda i: (-P[i], i))
S = [P[i] for i in order]
# the pieces, re-derived: k letters on [1 - P_k + (k-1) p_{k+1}, 1 - P_k + (k-1) p_k]
mine = []
for k in range(M, 1, -1):
    Pk = sum(S[:k])
    nxt = S[k] if k < M else F(0)
    lo, hi = 1 - Pk + (k - 1) * nxt, 1 - Pk + (k - 1) * S[k - 1]
    if hi > lo:
        mine.append((lo, hi, k))
assert mine == list(PIECES), ('pieces', mine)
assert PIECES[0][0] == 0 and PIECES[-1][1] == 1 - S[0]
for (a, b, k), (c, d, j) in zip(PIECES, PIECES[1:]):
    assert b == c, 'the pieces do not tile'
checked = 0
for lo, hi, k in PIECES:
    top = order[:k]
    Pk = sum(S[:k])
    for t in (1, 2, 3):
        D = lo + (hi - lo) * F(t, 4)
        T = D - (1 - Pk)
        lam = 1 - D
        beta = T / ((k - 1) * lam)
        assert 0 < beta < 1
        q = [((P[j] / lam - beta) / (1 - beta) if j in top else F(0)) for j in range(M)]
        assert all(x >= 0 for x in q) and sum(q) == 1
        J = [[(lam * q[j] * (1 if x == j else beta)) if x in top else P[x] * q[j]
              for j in range(M)] for x in range(M)]
        assert all(v >= 0 for row in J for v in row)
        assert [sum(row) for row in J] == P, 'source marginal'
        assert [sum(J[x][j] for x in range(M)) for j in range(M)] == q
        assert sum(J[x][j] for x in range(M) for j in range(M) if x != j) == D
        I = {}
        for x in range(M):
            for j in range(M):
                if J[x][j]:
                    I = lf_add(I, log2form(J[x][j] / (P[x] * q[j])), J[x][j])
        claim = {}
        for x in S[:k]:
            claim = lf_add(claim, log2form(x), -x)
        claim = lf_add(claim, log2form(lam), lam)
        claim = lf_add(claim, log2form(T / (k - 1)), T)
        if MUTANT:
            claim = lf_add(claim, {2: D})
        assert I == claim, ('I(X;Xh) != R(D)', D)
        # the dual point: beta = e^{-s}, mu(x) = lam/p_x on the top k, 1/beta off it
        mu = [lam / P[x] if x in top else 1 / beta for x in range(M)]
        for y in range(M):
            tot = sum(P[x] * mu[x] * (1 if x == y else beta) for x in range(M))
            assert tot <= 1, ('dual infeasible', y)
            if y in top:
                assert tot == 1
        dual = {}
        for x in range(M):
            dual = lf_add(dual, log2form(mu[x]), P[x])
        dual = lf_add(dual, log2form(beta), D)
        assert dual == I, 'the dual bound does not meet the channel'
        checked += 1
print(''' + repr(label) + ''', checked, 'rational distortions: test channel and dual bound meet the claimed R(D) exactly VERIFIED True')
''']
    return "\n".join(lines) + "\n"


# ===========================================================================
# 3.  ROBIN EIGENVALUES
# ===========================================================================

_TRIG = r'''
from fractions import Fraction as F

def atan_inv(n, terms):
    """arctan(1/n) between two rationals (alternating series)"""
    s, x, sign = F(0), F(1, n), 1
    for k in range(terms):
        s += sign * x ** (2 * k + 1) / (2 * k + 1); sign = -sign
    nxt = x ** (2 * terms + 1) / (2 * terms + 1)
    return (s, s + nxt) if sign > 0 else (s - nxt, s)

a_lo, a_hi = atan_inv(5, 40)
b_lo, b_hi = atan_inv(239, 15)
PI_LO, PI_HI = 16 * a_lo - 4 * b_hi, 16 * a_hi - 4 * b_lo
assert PI_LO < PI_HI and PI_HI - PI_LO < F(1, 10 ** 40)

def sincos(x):
    x = F(x); ax = abs(x); s = c = F(0); term = F(1); n = 0
    while True:
        if n % 4 == 0: c += term
        elif n % 4 == 1: s += term
        elif n % 4 == 2: c -= term
        else: s -= term
        n += 1; term = term * x / n
        if n > ax + 2 and abs(term) < F(1, 2 ** 90): break
    r = abs(term)
    return (s - r, s + r), (c - r, c + r)

def sinhcosh(x):
    x = F(x); assert x >= 0; s = c = F(0); term = F(1); n = 0
    while True:
        if n % 2 == 0: c += term
        else: s += term
        n += 1; term = term * x / n
        if n > 2 * x + 2 and term < F(1, 2 ** 90): break
    r = term / (1 - x / (n + 1))
    return (s, s + r), (c, c + r)

def scale(iv, k):
    a, b = iv[0] * k, iv[1] * k
    return (a, b) if a <= b else (b, a)

def sign_f(fam, h, L, k):
    if fam in ('D', 'N'):
        sn, cs = sincos(k * L)
        a, b = (scale(cs, k), scale(sn, h)) if fam == 'D' else (scale(sn, -k), scale(cs, h))
    else:
        sn, cs = sinhcosh(k * L)
        a, b = (scale(cs, k), scale(sn, h)) if fam == 'Dneg' else (scale(sn, k), scale(cs, h))
    lo, hi = a[0] + b[0], a[1] + b[1]
    return 1 if lo > 0 else (-1 if hi < 0 else 0)

def rnd(x, places=6):
    s = 10 ** places; n = x * s
    q = (n.numerator * 2 + n.denominator) // (2 * n.denominator)
    sg = '-' if q < 0 else ''; q = abs(q)
    return f"{sg}{q // s}.{q % s:0{places}d}"
'''


def robin_script(family: str, h: Fraction, L: Optional[Fraction],
                 interval_mults: Sequence[Tuple[Fraction, Fraction]],
                 roots: Sequence[Tuple[Fraction, Fraction]],
                 claimed: Sequence[str],
                 negative: Optional[Tuple[Fraction, Fraction]],
                 negative_claim: Optional[str], case: str,
                 label: str = "ROBIN") -> str:
    """``interval_mults``: the ``n``-th interval as multiples ``(a, b)`` of
    ``pi/L`` (``a = 0`` for an interval starting at 0); ``claimed``: the
    printed eigenvalues; on a symbolic interval (``L`` None) the sign
    pattern is spot-checked at ``L = 1/2, 1, 3``."""
    lines = [_TRIG,
             f"FAM, H, CASE = {family!r}, {_q(h)}, {case!r}",
             f"MULTS = [" + ", ".join(f"({_q(a)}, {_q(b)})"
                                       for a, b in interval_mults) + "]"]
    if L is None:
        lines += [r'''
# a symbolic length: the sign change on each declared interval, at sample L
for L in (F(1, 2), F(1), F(3)):
    for a, b in MULTS:
        lo = a * PI_HI / L + F(1, 10 ** 20) if a > 0 else F(1, 10 ** 3)
        hi = b * PI_LO / L - F(1, 10 ** 20)
        sa, sb = sign_f(FAM, H, L, lo), sign_f(FAM, H, L, hi)
        assert sa != 0 and sb != 0 and sa != sb, ('no sign change', L, a, b)
''', f"print({label!r}, 'one root in each declared interval at L = 1/2, 1, 3 "
     f"(sign changes certified) VERIFIED True')"]
        return "\n".join(lines) + "\n"
    lines += [
        f"L = {_q(L)}",
        "ROOTS = [" + ", ".join(f"({_q(a)}, {_q(b)})" for a, b in roots) + "]",
        f"CLAIMED = {list(claimed)!r}",
        "NEG = " + (f"({_q(negative[0])}, {_q(negative[1])})" if negative
                    else "None"),
        f"NEG_CLAIM = {negative_claim!r}",
        r'''
assert len(ROOTS) == len(CLAIMED) == len(MULTS)
for (lo, hi), (a, b), text in zip(ROOTS, MULTS, CLAIMED):
    assert lo < hi
    assert lo > a * PI_HI / L or (a == 0 and lo > 0), 'below its interval'
    assert hi < b * PI_LO / L, 'above its interval'
    sa, sb = sign_f(FAM, H, L, lo), sign_f(FAM, H, L, hi)
    assert sa != 0 and sb != 0 and sa != sb, 'no certified sign change'
    assert rnd(lo * lo) == rnd(hi * hi) == text, ('eigenvalue', text)
# the negative eigenvalue: present exactly in the declared cases
if FAM == 'D':
    want_neg = H * L < -1
else:
    want_neg = H < 0
assert want_neg == (NEG is not None)
if NEG is not None:
    mu_lo, mu_hi = NEG                # mu = sqrt(-lambda) between two rationals
    fam = 'Dneg' if FAM == 'D' else 'Nneg'
    assert 0 < mu_lo < mu_hi
    sa, sb = sign_f(fam, H, L, mu_lo), sign_f(fam, H, L, mu_hi)
    assert sa != 0 and sb != 0 and sa != sb, 'no sign change for mu'
    assert rnd(-mu_hi * mu_hi) == rnd(-mu_lo * mu_lo) == NEG_CLAIM, ('negative eigenvalue', NEG_CLAIM)
''',
        f"print({label!r}, len(ROOTS), 'eigenvalues enclosed with certified "
        f"sign changes in their intervals VERIFIED True')"]
    return "\n".join(lines) + "\n"

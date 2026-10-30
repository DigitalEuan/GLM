"""``glm_universal.runtime.derivation_two_scripts`` -- the column-3 scripts
of Phase 107's derivations (``studies/DERIVATION_TWO_STUDY.md``).

Every script is stand-alone standard-library Python that shares no code
with the layer it checks (``reasoning.info_inequality``,
``reasoning.coding_theory``, ``reasoning.maxent``, ``reasoning.spectral``,
``reasoning.fft_derivation``): it carries its own reader, its own algebra
and its own check, and its last line is ``VERIFIED True`` only when every
check holds.

* an information inequality: the claim re-read from its text, every
  elemental inequality re-built from its definition and the certificate
  re-summed exactly; a refuting distribution re-enumerated over its fair
  bits, every joint law re-counted and every entropy read as ``log2`` of a
  uniform support; a polymatroid witness re-checked against every elemental
  inequality, re-generated here;
* a code: the Kraft sum re-summed, two parsings re-concatenated, the
  dangling-suffix closure re-computed, a prefix code re-checked;
* a rate-distortion function: the backward test channel re-built at
  rational distortions, its marginal and its distortion re-computed, and
  ``I(X; Xh)`` compared with the claim as an exact combination of
  logarithms of primes;
* a maximum-entropy density: normalisation, moments and entropy re-derived
  from the Gaussian and exponential integrals in exact form;
* an eigenvalue problem: each claimed eigenvalue tied to its eigenfunction's
  frequency, the boundary conditions and the normalisation evaluated at
  rational multiples of ``pi``, and the determinant's zero set re-derived;
* a transmission coefficient: the matching conditions re-solved at rational
  points with exact complex arithmetic;
* an FFT: the flow graph re-applied to symbolic inputs in ``Z[W]/(W^{N/2} +
  1)`` and compared with the DFT entry by entry;
* a rate posterior: the Beta integral re-computed by binomial expansion and
  the grid posterior re-normalised.

No float anywhere (D7).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = ["inequality_script", "code_script", "prefix_script",
           "kraft_refusal_script", "rd_script", "maxent_script",
           "eigen_script", "scattering_script", "fft_script",
           "posterior_script", "proof_core_script"]


def _q(x) -> str:
    x = Fraction(x)
    return f"F({x.numerator}, {x.denominator})"


# ===========================================================================
# 1.  INFORMATION INEQUALITIES
# ===========================================================================

_ENTROPY_READER = r'''
from fractions import Fraction as F
import re
from itertools import combinations, product

TOK = re.compile(r"\s*(\d+(?:/\d+)?|[A-Za-z_]\w*|>=|<=|=|\||;|,|\(|\)|\+|-|\*)")

def toks(s):
    out, i = [], 0
    while i < len(s):
        if not s[i:].strip():
            break
        m = TOK.match(s, i)
        assert m and m.end() > i, 'unreadable'
        out.append(m.group(1)); i = m.end()
    return out

def vec_add(a, b, k=1):
    out = dict(a)
    for s, c in b.items():
        out[s] = out.get(s, 0) + k * c
        if out[s] == 0:
            del out[s]
    return out

def ent(sets):
    """sum of k * h(S) over (S, k)"""
    out = {}
    for s, k in sets:
        if s:
            out = vec_add(out, {frozenset(s): F(k)})
    return out

def H(a, c=()):
    return ent([(set(a) | set(c), 1), (set(c), -1)])

def I(a, b, c=()):
    A, B, C = set(a), set(b), set(c)
    return ent([(A | C, 1), (B | C, 1), (A | B | C, -1), (C, -1)])

def read(text):
    t = toks(text); pos = [0]
    def peek():
        return t[pos[0]] if pos[0] < len(t) else None
    def take(w=None):
        x = peek(); assert x is not None and (w is None or x == w), (w, x)
        pos[0] += 1; return x
    def names(stop):
        out = [take()]
        while peek() == ',':
            take(','); out.append(take())
        assert peek() in stop
        return out
    def atom():
        x = take()
        if x == 'H':
            take('('); a = names(('|', ')')); c = []
            if peek() == '|':
                take('|'); c = names((')',))
            take(')'); return H(a, c)
        if x == 'I':
            take('('); a = names((';',)); take(';'); b = names(('|', ')')); c = []
            if peek() == '|':
                take('|'); c = names((')',))
            take(')'); return I(a, b, c)
        if x == '(':
            e = expr(); take(')'); return e
        raise AssertionError(x)
    def term():
        x = peek()
        if x is not None and re.fullmatch(r"\d+(?:/\d+)?", x):
            take(); k = F(x)
            if peek() == '*':
                take('*'); return {s: k * c for s, c in atom().items()}
            return {frozenset(): k} if k else {}
        return atom()
    def expr():
        sign = 1
        if peek() == '-':
            take('-'); sign = -1
        out = vec_add({}, term(), sign)
        while peek() in ('+', '-'):
            k = 1 if take() == '+' else -1
            out = vec_add(out, term(), k)
        return out
    lhs = expr(); op = take(); rhs = expr()
    assert peek() is None and op in ('>=', '<=', '=')
    return lhs, op, rhs

def value(form, h):
    return sum((c * (h[s] if s else 1) for s, c in form.items()), F(0))

def elemental_vec(e, names):
    if e[0] == 'H':
        i = e[1]
        return H([names[i]], [names[k] for k in range(len(names)) if k != i])
    _, i, j, K = e
    assert i != j and i not in K and j not in K
    return I([names[i]], [names[j]], [names[k] for k in K])

def all_elementals(names):
    n = len(names)
    out = [('H', i) for i in range(n)]
    for i, j in combinations(range(n), 2):
        rest = [k for k in range(n) if k not in (i, j)]
        for r in range(len(rest) + 1):
            for K in combinations(rest, r):
                out.append(('I', i, j, list(K)))
    return out

def claims_of(claim_text):
    lhs, op, rhs = read(claim_text)
    d = vec_add(lhs, rhs, -1)
    neg = {s: -c for s, c in d.items()}
    return {'>=': [d], '<=': [neg], '=': [d, neg]}[op]

def givens_of(texts):
    out = []
    for g in texts:
        lhs, op, rhs = read(g)
        assert op == '='
        out.append(vec_add(lhs, rhs, -1))
    return out
'''


def inequality_script(names: Sequence[str], givens: Sequence[str],
                      claim: str, verdict: str, certificates,
                      distribution=None, violated: Optional[int] = None,
                      claimed_value=None, polymatroid=None,
                      label: str = "INEQUALITY") -> str:
    lines = [_ENTROPY_READER,
             f"NAMES = {list(names)!r}",
             f"GIVENS = givens_of({list(givens)!r})",
             f"CLAIMS = claims_of({claim!r})"]
    if verdict == "proved":
        certs = []
        for lam, mu in certificates:
            certs.append(([(list(e[:3]) + [list(e[3])] if e[0] == "I"
                            else list(e), _q(c)) for e, c in lam],
                          [(j, _q(c)) for j, c in mu]))
        body = ", ".join(
            "([" + ", ".join(f"({e!r}, {c})" for e, c in lam) + "], [" +
            ", ".join(f"({j}, {c})" for j, c in mu) + "])"
            for lam, mu in certs)
        lines += [
            f"CERTS = [{body}]",
            "assert len(CERTS) == len(CLAIMS)",
            "for claim, (lam, mu) in zip(CLAIMS, CERTS):",
            "    total = {}",
            "    for e, c in lam:",
            "        assert c > 0, 'a negative elemental coefficient'",
            "        total = vec_add(total, elemental_vec(tuple(e), NAMES), c)",
            "    for j, c in mu:",
            "        total = vec_add(total, GIVENS[j], c)",
            "    const = claim.get(frozenset(), F(0))",
            "    assert const >= 0",
            "    body = {s: c for s, c in claim.items() if s}",
            "    assert total == body, ('certificate does not sum to the claim', total, body)",
            f"print('{label}: Shannon-type certificate re-summed VERIFIED True')",
        ]
    elif verdict == "NOT_VALID":
        bits, forms = distribution
        lines += [
            f"BITS = {bits}",
            f"FORMS = {[list(f) for f in forms]!r}",
            "def outcome(u, fs):",
            "    return tuple(bin(f & u).count('1') % 2 for f in fs)",
            "h = {}",
            "for r in range(1, len(NAMES) + 1):",
            "    for S in combinations(range(len(NAMES)), r):",
            "        counts = {}",
            "        for u in range(1 << BITS):",
            "            key = tuple(outcome(u, FORMS[k]) for k in S)",
            "            counts[key] = counts.get(key, 0) + 1",
            "        sizes = set(counts.values())",
            "        assert len(sizes) == 1, 'not uniform'",
            "        support = len(counts)",
            "        assert support & (support - 1) == 0",
            "        h[frozenset(NAMES[k] for k in S)] = F(support.bit_length() - 1)",
            "for g in GIVENS:",
            "    assert value(g, h) == 0, 'a given fails'",
            f"v = value(CLAIMS[{violated}], h)",
            f"assert v == {_q(claimed_value)} and v < 0, ('claimed violation', v)",
            f"print('{label}: distribution violates the claim by', -v, 'bits VERIFIED True')",
        ]
    else:
        pm = {"".join(sorted(s)): v for s, v in polymatroid.items()}
        lines += [
            "PM = {" + ", ".join(f"{k!r}: {_q(v)}" for k, v in pm.items()) +
            "}",
            "h = {frozenset(k): v for k, v in PM.items()}",
            "for r in range(1, len(NAMES) + 1):",
            "    for S in combinations(NAMES, r):",
            "        h.setdefault(frozenset(S), None)",
            "assert all(h[frozenset(S)] is not None for r in range(1, len(NAMES) + 1) "
            "for S in combinations(NAMES, r))",
            "for e in all_elementals(NAMES):",
            "    assert value(elemental_vec(e, NAMES), h) >= 0, e",
            "for g in GIVENS:",
            "    assert value(g, h) == 0",
            f"v = value(CLAIMS[{violated}], h)",
            f"assert v == {_q(claimed_value)} and v < 0",
            f"print('REFUSED NOT_SHANNON: a polymatroid meets every elemental "
            f"inequality and violates the claim, so no Shannon-type proof "
            f"exists VERIFIED True')",
        ]
    return "\n".join(lines) + "\n"


# ===========================================================================
# 2.  CODES
# ===========================================================================

def code_script(words: Sequence[str], d: int, unique: bool,
                prefix_free: bool, kraft, ambiguous, prefix_code,
                label: str = "CODE") -> str:
    lines = [
        "from fractions import Fraction as F",
        f"W = {list(words)!r}",
        f"D = {d}",
        f"assert len({{ch for w in W for ch in w}}) <= D",
        "K = sum((F(1, D ** len(w)) for w in W), F(0))",
        f"assert K == {_q(kraft)}, ('Kraft', K)",
        "pf = len(set(W)) == len(W) and not any(a != b and b.startswith(a) "
        "for a in W for b in W)",
        f"assert pf == {prefix_free!r}",
    ]
    if not unique:
        s, p1, p2 = ambiguous
        lines += [
            f"S, P1, P2 = {s!r}, {list(p1)!r}, {list(p2)!r}",
            "assert all(w in W for w in P1 + P2)",
            "assert ''.join(P1) == S == ''.join(P2) and P1 != P2",
            f"print('{label}: not uniquely decodable --', S, '=', '.'.join(P1), "
            f"'=', '.'.join(P2), 'VERIFIED True')",
        ]
    else:
        lines += [
            "# dangling suffixes, closed under both directions of overlap",
            "dang = {b[len(a):] for a in W for b in W if a != b and b.startswith(a)}",
            "frontier = set(dang)",
            "while frontier:",
            "    new = set()",
            "    for x in frontier:",
            "        for c in W:",
            "            if c.startswith(x) and c != x: new.add(c[len(x):])",
            "            if x.startswith(c) and c != x: new.add(x[len(c):])",
            "    frontier = new - dang",
            "    dang |= new",
            "assert len(set(W)) == len(W)",
            "assert not (dang & set(W)), 'a codeword dangles'",
            "assert K <= 1",
            f"PC = {list(prefix_code)!r}",
            "assert sorted(map(len, PC)) == sorted(map(len, W))",
            "assert not any(a != b and b.startswith(a) for a in PC for b in PC)",
            "assert len(set(PC)) == len(PC)",
            f"print('{label}: uniquely decodable, Kraft sum', K, '<= 1, prefix "
            f"code with the same lengths VERIFIED True')",
        ]
    return "\n".join(lines) + "\n"


def prefix_script(lengths: Sequence[int], d: int, code: Sequence[str],
                  label: str = "PREFIX") -> str:
    return "\n".join([
        "from fractions import Fraction as F",
        f"L, D, C = {list(lengths)!r}, {d}, {list(code)!r}",
        "assert [len(c) for c in C] == L",
        "assert all(0 <= int(ch, 36) < D for c in C for ch in c)",
        "assert len(set(C)) == len(C)",
        "assert not any(a != b and b.startswith(a) for a in C for b in C)",
        "K = sum((F(1, D ** n) for n in L), F(0))",
        "assert K <= 1",
        f"print('{label}: prefix-free with lengths', L, 'Kraft sum', K, "
        f"'VERIFIED True')",
    ]) + "\n"


def kraft_refusal_script(lengths: Sequence[int], d: int) -> str:
    return "\n".join([
        "from fractions import Fraction as F",
        f"L, D = {list(lengths)!r}, {d}",
        "K = sum((F(1, D ** n) for n in L), F(0))",
        "assert K > 1",
        "print('REFUSED KRAFT_VIOLATED: Kraft sum', K, '> 1 VERIFIED True')",
    ]) + "\n"


# ===========================================================================
# 3.  RATE DISTORTION
# ===========================================================================

_LOGFORM = r'''
from fractions import Fraction as F

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
    """log2 of a positive rational as {prime: exponent}"""
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

def entropy(ps):
    out = {}
    for x in ps:
        if x:
            out = lf_add(out, log2form(x), -F(x))
    return out

def ln_bounds(x, terms=60):
    """rational bounds on ln(x), x > 0, by the atanh series"""
    x = F(x); y = (x - 1) / (x + 1); s = F(0); yk = y
    for k in range(terms):
        s += yk / (2 * k + 1); yk *= y * y
    s *= 2
    err = 2 * abs(yk) / (1 - y * y) / (2 * terms + 1)
    return s - err, s + err

def lf_bounds(form):
    lo2, hi2 = ln_bounds(2)
    lo = hi = F(0)
    for p, e in form.items():
        a, b = ln_bounds(p)
        a, b = a / hi2, b / lo2
        if a < 0:
            a, b = b, a
        lo += min(e * a, e * b); hi += max(e * a, e * b)
    return lo, hi
'''


def rd_script(m: int, probs: Optional[Sequence[Fraction]],
              samples: Sequence[Tuple[Sequence[Fraction], Fraction]],
              penalty: Fraction, tight_end_of, zero_of, gap: bool,
              label: str = "RATE-DISTORTION", mutate: bool = False) -> str:
    """``samples``: ``(source probabilities, tight end)`` pairs (several for
    a source in a letter); the claim ``R(D) = H(X) - H(D) - D*log2(m-1)``
    checked at rational ``D`` in each tight range."""
    lines = [_LOGFORM, f"M = {m}", f"GAP = {gap!r}",
             f"PENALTY_CLAIM = {_q(penalty)}  # coefficient of D*log2(M-1)",
             f"MUTANT = {mutate!r}",
             "SAMPLES = [" + ", ".join(
                 "([" + ", ".join(_q(x) for x in ps) + f"], {_q(te)}, "
                 f"{_q(z)})" for ps, te, z in samples) + "]",
             r'''
checked = 0
for P, TIGHT, ZERO in SAMPLES:
    assert sum(P) == 1 and all(x > 0 for x in P)
    assert TIGHT == (M - 1) * min(P), 'tight end'
    assert ZERO == 1 - max(P), 'zero point'
    for j in range(0, 5):
        D = TIGHT * F(j, 5) if TIGHT > 0 else F(0)
        if D >= 1 - F(1, M):
            continue
        a = D / (M - 1)
        q = [(x - a) / (1 - M * a) for x in P]
        assert all(x >= 0 for x in q) and sum(q) == 1
        # joint law P(xh, x) = q[xh] * W(x | xh)
        W = lambda x, xh: (1 - D) if x == xh else a
        marg = [sum(q[xh] * W(x, xh) for xh in range(M)) for x in range(M)]
        assert marg == list(P), 'marginal'
        dist = sum(q[xh] * W(x, xh) for xh in range(M) for x in range(M) if x != xh)
        assert dist == D, 'distortion'
        # I(X; Xh) = H(X) - H(X | Xh); each row of W is (1-D, a, ..., a)
        hx = entropy(P)
        hcond = {}
        for xh in range(M):
            hcond = lf_add(hcond, entropy([W(x, xh) for x in range(M)]), q[xh])
        I = lf_add(hx, hcond, -1)
        claim = lf_add(lf_add(hx, entropy([D, 1 - D]), -1),
                       log2form(M - 1) if M > 2 else {}, -PENALTY_CLAIM * D)
        if MUTANT:
            claim = lf_add(claim, {2: D + 1})
        assert I == claim, ('I(X;Xh) != R(D)', I, claim)
        checked += 1
    # at the tight end some q vanishes: the channel stops existing there
    a = TIGHT / (M - 1)
    if TIGHT < 1 - F(1, M):
        q = [(x - a) / (1 - M * a) for x in P]
        assert min(q) == 0
        if GAP:
            D2 = (TIGHT + ZERO) / 2
            a2 = D2 / (M - 1)
            assert min((x - a2) / (1 - M * a2) for x in P) < 0, 'gap'
    # from ZERO on: send the most probable symbol, distortion 1 - max P, I = 0
    assert 1 - max(P) == ZERO
# the step H(Z) <= H(D) + D log2(M-1) for P(Z != 0) = d <= D needs the bound
# increasing on [0, 1 - 1/M]: checked on a grid with rational log bounds
prev = None
for j in range(0, 9):
    d = (1 - F(1, M)) * F(j, 10)
    f = lf_add(entropy([d, 1 - d]), log2form(M - 1) if M > 2 else {}, d)
    lo, hi = lf_bounds(f)
    if prev is not None:
        assert lo > prev, 'not increasing'
    prev = hi
print(''' + repr(label) + ''', checked, 'rational distortions: I(X;Xh) = R(D) exactly VERIFIED True')
''']
    return "\n".join(lines) + "\n"


# ===========================================================================
# 4.  MAXIMUM ENTROPY
# ===========================================================================

def maxent_script(family: str, samples: Sequence[Dict[str, Fraction]],
                  multipliers: Dict[str, str], entropy_rational: Fraction,
                  label: str = "MAXENT") -> str:
    """``multipliers``: Python expressions in the parameters for ``l1``,
    ``l2`` and the rational part ``l0r`` of ``l0``; ``entropy_rational`` the
    claim's rational part (``1/2`` for the Gaussian, ``1`` for the
    exponential, ``0`` for the uniform)."""
    return "\n".join([
        "from fractions import Fraction as F",
        f"FAMILY = {family!r}",
        "SAMPLES = [" + ", ".join(
            "{" + ", ".join(f"{k!r}: {_q(v)}" for k, v in s.items()) + "}"
            for s in samples) + "]",
        f"L1 = {multipliers.get('l1', '0')!r}",
        f"L2 = {multipliers.get('l2', '0')!r}",
        f"L0R = {multipliers.get('l0r', '0')!r}",
        f"HR = {_q(entropy_rational)}",
        r'''
def ev(expr, env):
    import re
    expr = re.sub(r"(?<![\w.])(\d+)", r"F(\1)", expr.replace('^', '**'))
    return F(eval(expr, {'F': F}, dict(env)))

for env in SAMPLES:
    if FAMILY == 'gaussian':
        mu, var = env['mu'], env['var']
        l1, l2, l0r = ev(L1, env), ev(L2, env), ev(L0R, env)
        a, b = -l2, l1
        assert a > 0, 'not integrable'
        # int exp(l0r - (1/2) ln(2 pi var) - a x^2 + b x) dx
        #   = exp(l0r + b^2/(4a)) * sqrt(pi/a) / sqrt(2 pi var)
        assert l0r + b * b / (4 * a) == 0, 'normalising exponent'
        assert 1 / a == 2 * var, 'normalising root'
        assert b / (2 * a) == mu, 'mean'
        assert 1 / (2 * a) + b * b / (4 * a * a) == var + mu * mu, 'second moment'
        # h = -l0 - l1 E X - l2 E X^2 = (1/2) ln(2 pi var) + rational part
        hr = -l0r - l1 * mu - l2 * (var + mu * mu)
        assert hr == HR, ('entropy', hr)
    elif FAMILY == 'exponential':
        mu = env['mu']
        l1 = ev(L1, env)
        assert l1 < 0, 'not integrable'
        # int_0^inf exp(-ln(mu) + l1 x) dx = (1/mu) * (1/(-l1)) = 1
        assert (1 / mu) * (1 / (-l1)) == 1, 'normalisation'
        assert -1 / l1 == mu, 'mean'
        hr = -l1 * mu          # h = ln(mu) + rational part
        assert hr == HR, ('entropy', hr)
    else:
        w = env['width']
        assert w > 0
        assert (1 / w) * w == 1, 'normalisation'
        assert HR == 0         # h = ln(width) exactly
print(''' + repr(label) + ''', len(SAMPLES), 'parameter points: normalised, constraints met, entropy as claimed VERIFIED True')
'''])


# ===========================================================================
# 5.  EIGENVALUE PROBLEMS
# ===========================================================================

def eigen_script(kinds: Tuple[str, str], eigenvalue: str, length: str,
                 fn: str, amp2: Tuple[Fraction, int], indices: Sequence[int],
                 zero_eigen: bool, freq_of_index: Tuple[Fraction, Fraction],
                 label: str = "EIGEN") -> str:
    """``eigenvalue``: the claimed formula in ``n`` (or ``m``), ``pi`` and the
    length symbol; ``fn``: ``sin``/``cos``/``exp``; ``amp2``: the claimed
    squared amplitude as ``(c, e)`` meaning ``c * L^e``; ``freq_of_index``:
    ``(a, b)`` with ``k L = (a*n + b) pi`` for the claimed eigenfunction."""
    return "\n".join([
        "from fractions import Fraction as F",
        f"KINDS = {tuple(kinds)!r}",
        f"LAM = {eigenvalue!r}",
        f"LSYM = {length!r}",
        f"FN = {fn!r}",
        f"AMP2 = ({_q(amp2[0])}, {amp2[1]})",
        f"IDX = {list(indices)!r}",
        f"ZERO = {zero_eigen!r}",
        f"FREQ = ({_q(freq_of_index[0])}, {_q(freq_of_index[1])})",
        r'''
class Mono:
    """c * pi^a * L^b with c rational"""
    def __init__(self, c, a=0, b=0):
        self.c, self.a, self.b = F(c), a, b
    def _m(o):
        return o if isinstance(o, Mono) else Mono(o)
    def __mul__(s, o):
        o = Mono._m(o); return Mono(s.c * o.c, s.a + o.a, s.b + o.b)
    __rmul__ = __mul__
    def __truediv__(s, o):
        o = Mono._m(o); return Mono(s.c / o.c, s.a - o.a, s.b - o.b)
    def __rtruediv__(s, o):
        return Mono._m(o) / s
    def __pow__(s, k):
        return Mono(s.c ** k, s.a * k, s.b * k)
    def __add__(s, o):
        o = Mono._m(o)
        if s.c == 0: return o
        if o.c == 0: return s
        assert (s.a, s.b) == (o.a, o.b), 'not a monomial'
        return Mono(s.c + o.c, s.a, s.b)
    __radd__ = __add__
    def __sub__(s, o):
        return s + Mono._m(o) * -1
    def __rsub__(s, o):
        return Mono._m(o) - s
    def __neg__(s):
        return s * -1

PI_TABLE = {0: (0, 1), 1: (1, 0), 2: (0, -1), 3: (-1, 0)}   # quarter turns
def sincos(q):
    """sin and cos of q*pi for q a multiple of 1/2"""
    t = q * 2
    assert t.denominator == 1
    return PI_TABLE[int(t) % 4]

def lam_of(i):
    env = {'pi': Mono(1, 1, 0), LSYM: Mono(1, 0, 1), 'n': i, 'm': i}
    if LSYM == '2*pi':
        env = {'pi': Mono(1, 1, 0), 'n': i, 'm': i}
    v = eval(LAM.replace('^', '**'), {}, env)
    return Mono._m(v)

def theta_of(i):
    """k L / pi for index i (for the ring, L = 2 pi and k L = 2 pi m)"""
    return FREQ[0] * i + FREQ[1]

checked = 0
for i in IDX:
    th = theta_of(i)          # k L = th * pi
    lam = lam_of(i)
    # lambda = k^2 = (th pi / L)^2
    if LSYM == '2*pi':
        want = Mono(th * th / 4)
    else:
        want = Mono(th * th, 2, -2)
    assert (lam.c, lam.a, lam.b) == (want.c, want.a, want.b), ('lambda', i)
    s, c = sincos(th)
    if KINDS == ('P', 'P'):
        assert (s, c) == (0, 1), 'periodicity'
        # |exp(i k x)|^2 = 1, so int_0^L = L and AMP2 * L = 1
        assert AMP2 == (1, -1)
    else:
        # boundary values of sin(kx) / cos(kx) and their derivatives
        y0, dy0 = (0, 1) if FN == 'sin' else (1, 0)
        yL, dyL = (s, c) if FN == 'sin' else (c, -s)
        for kind, (v, dv) in zip(KINDS, ((y0, dy0), (yL, dyL))):
            assert (v if kind == 'D' else dv) == 0, ('condition', kind, i)
        # int_0^L sin^2(kx) dx = L/2 - sin(2kL)/(4k), likewise cos^2
        s2, _ = sincos(2 * th)
        assert s2 == 0
        assert AMP2 == (2, -1), 'amplitude'
    checked += 1
# the determinant for lambda = k^2 over (cos kx, sin kx), at theta = kL
def row(kind, end, th):
    if not end:
        return (1, 0) if kind == 'D' else (0, 1)    # k factored out
    s, c = sincos(th)
    return (c, s) if kind == 'D' else (-s, c)
if KINDS != ('P', 'P'):
    det = lambda th: (lambda a, b: a[0] * b[1] - a[1] * b[0])(
        row(KINDS[0], False, th), row(KINDS[1], True, th))
    for i in IDX:
        assert det(theta_of(i)) == 0
        assert det(theta_of(i) + F(1, 2)) != 0, 'a zero between eigenvalues'
    if ZERO:
        assert KINDS == ('N', 'N')
else:
    for i in IDX:
        th = theta_of(i)
        s, c = sincos(th)
        assert (1 - c) ** 2 + s ** 2 == 0
        s2, c2 = sincos(th + 1)
        assert (1 - c2) ** 2 + s2 ** 2 != 0
print(''' + repr(label) + ''', checked, 'eigenpairs: lambda = k^2, conditions, normalisation VERIFIED True')
'''])


# ===========================================================================
# 6.  SCATTERING
# ===========================================================================

def scattering_script(kind: str, claim_py: str, energy_py: Optional[str],
                      label: str = "TRANSMISSION") -> str:
    """``kind``: ``delta`` | ``step`` | ``step+delta`` | ``below``;
    ``claim_py`` the claimed ``T`` in ``k1, k2, g`` (or ``k, g``);
    ``energy_py`` the claimed ``T`` in ``m, E, hbar, a`` (delta only)."""
    return "\n".join([
        "from fractions import Fraction as F",
        f"KIND = {kind!r}",
        f"CLAIM = {claim_py!r}",
        f"ENERGY = {energy_py!r}",
        r'''
class C:
    def __init__(s, re, im=0):
        s.re, s.im = F(re), F(im)
    def __add__(s, o): return C(s.re + o.re, s.im + o.im)
    def __sub__(s, o): return C(s.re - o.re, s.im - o.im)
    def __mul__(s, o): return C(s.re * o.re - s.im * o.im, s.re * o.im + s.im * o.re)
    def __truediv__(s, o):
        n = o.re * o.re + o.im * o.im
        p = s * C(o.re, -o.im)
        return C(p.re / n, p.im / n)
    def n2(s): return s.re * s.re + s.im * s.im

def solve(k1, k2, g, below):
    # psi = e^{i k1 x} + r e^{-i k1 x} (x < 0); t e^{i k2 x} or t e^{-k2 x}
    # continuity: 1 + r = t; jump: t*D2 - i k1 (1 - r) = g t
    D2 = C(-k2) if below else C(0, k2)
    # r - t = -1 ; i k1 r + (D2 - g) t = i k1
    a11, a12, b1 = C(1), C(-1), C(-1)
    a21, a22, b2 = C(0, k1), D2 - C(g), C(0, k1)
    det = a11 * a22 - a12 * a21
    r = (b1 * a22 - a12 * b2) / det
    t = (a11 * b2 - b1 * a21) / det
    # the conditions hold
    assert (C(1) + r - t).n2() == 0
    assert (t * D2 - C(0, k1) * (C(1) - r) - C(g) * t).n2() == 0
    return r, t

def ev(expr, env):
    import re
    expr = re.sub(r"(?<![\w.])(\d+)", r"F(\1)", expr.replace('^', '**'))
    return F(eval(expr, {'F': F}, dict(env)))

points = [(F(3, 2), F(5, 7), F(2, 3)), (F(4), F(1, 3), F(-5, 2)),
          (F(7, 5), F(9, 4), F(1, 9)), (F(1), F(1), F(3))]
for k1, k2, g in points:
    if KIND == 'delta':
        k2 = k1
    if KIND == 'step':
        g = F(0)
    below = KIND == 'below'
    r, t = solve(k1, k2, 0 if below else g, below)
    if below:
        T = F(0)
        assert r.n2() == 1, '|r|^2 = 1 below the step'
    else:
        T = (k2 / k1) * t.n2() if KIND != 'delta' else t.n2()
        assert r.n2() + T == 1, 'R + T = 1'
    env = {'k1': k1, 'k2': k2, 'k': k1, 'g': g}
    assert ev(CLAIM, env) == T, ('claim', k1, k2, g)
    if ENERGY:
        # choose m, hbar and E so that k = sqrt(2 m E)/hbar is k1
        m, hbar, a = F(2), F(1, 3), F(5, 7) + k1
        E = hbar * hbar * k1 * k1 / (2 * m)
        gg = 2 * m * a / (hbar * hbar)
        r2, t2 = solve(k1, k1, gg, False)
        assert ev(ENERGY, {'m': m, 'E': E, 'hbar': hbar, 'a': a}) == t2.n2()
print(''' + repr(label) + ''', 'matching conditions re-solved at', len(points), 'rational points VERIFIED True')
'''])


# ===========================================================================
# 7.  FFT
# ===========================================================================

def fft_script(n: int, kind: str, butterflies: Sequence[Tuple[int, int, int,
                                                               int]],
               input_order: Sequence[int], output_order: Sequence[int],
               stages: int, nontrivial: int, label: str = "FFT") -> str:
    return "\n".join([
        f"N, KIND, STAGES, NONTRIVIAL = {n}, {kind!r}, {stages}, {nontrivial}",
        f"FLY = {list(map(tuple, butterflies))!r}",
        f"IN, OUT = {list(input_order)!r}, {list(output_order)!r}",
        r'''
H = N // 2
def w(e):
    """W^e in Z[W]/(W^H + 1) as a coefficient list"""
    e %= N
    v = [0] * H
    if e < H: v[e] = 1
    else: v[e - H] = -1
    return v
def add(a, b): return [x + y for x, y in zip(a, b)]
def sub(a, b): return [x - y for x, y in zip(a, b)]
def mul(a, b):
    out = [0] * H
    for i, x in enumerate(a):
        if x:
            for j, y in enumerate(b):
                if y:
                    k = i + j
                    if k < H: out[k] += x * y
                    else: out[k - H] -= x * y
    return out
# slot s holds, for each input n, a ring coefficient
slots = [[w(0) if IN[s] == m else [0] * H for m in range(N)] for s in range(N)]
assert sorted(IN) == list(range(N)) and sorted(OUT) == list(range(N))
assert len(FLY) == H * STAGES and (1 << STAGES) == N
assert sum(1 for f in FLY if f[3] % N) == NONTRIVIAL
for stage in range(1, STAGES + 1):
    for st, top, bot, e in FLY:
        if st != stage: continue
        a, b = slots[top], slots[bot]
        if KIND == 'dif':
            slots[top] = [add(x, y) for x, y in zip(a, b)]
            slots[bot] = [mul(sub(x, y), w(e)) for x, y in zip(a, b)]
        else:
            wb = [mul(y, w(e)) for y in b]
            slots[top] = [add(x, y) for x, y in zip(a, wb)]
            slots[bot] = [sub(x, y) for x, y in zip(a, wb)]
for s in range(N):
    k = OUT[s]
    for m in range(N):
        assert slots[s][m] == w(m * k), ('slot', s, 'input', m)
print(''' + repr(label) + ''', N, 'points: every output equals the DFT in Z[W]/(W^N/2 + 1) VERIFIED True')
'''])


# ===========================================================================
# 8.  THE RATE POSTERIOR
# ===========================================================================

def posterior_script(cases: Sequence[Tuple[int, int, int]],
                     grid: Optional[Sequence[Fraction]], peak, guard,
                     label: str = "POSTERIOR") -> str:
    """``cases``: ``(k, n, claimed constant)``."""
    return "\n".join([
        "from fractions import Fraction as F",
        "from math import comb",
        f"CASES = {list(cases)!r}",
        "GRID = " + ("None" if grid is None else
                     "[" + ", ".join(_q(g) for g in grid) + "]"),
        f"PEAK = {('None' if peak is None else _q(peak))}",
        f"GUARD = {('None' if guard is None else _q(guard))}",
        r'''
def f(p, k, n):
    return p ** k * (1 - p) ** (n - k)
for k, n, const in CASES:
    # int_0^1 p^k (1-p)^(n-k) dp by the binomial expansion of (1-p)^(n-k)
    integral = sum(F(comb(n - k, j) * (-1) ** j, k + j + 1) for j in range(n - k + 1))
    assert integral * const == 1, ('normalising constant', k, n)
    # increasing below k/n and decreasing above, at rational points
    mode = F(k, n)
    pts = [mode * F(j, 8) for j in range(9)]
    assert all(f(a, k, n) < f(b, k, n) for a, b in zip(pts, pts[1:])) or k == 0
    up = [mode + (1 - mode) * F(j, 8) for j in range(9)]
    assert all(f(a, k, n) > f(b, k, n) for a, b in zip(up, up[1:])) or k == n
if GRID is not None:
    k, n, _ = CASES[0]
    lik = [f(p, k, n) for p in GRID]
    tot = sum(lik)
    post = [x / tot for x in lik]
    assert sum(post) == 1
    top = max(post)
    assert GRID[post.index(top)] == PEAK, 'grid peak'
print(''' + repr(label) + ''', len(CASES), 'cases: Beta integral exact, monotone either side of k/n VERIFIED True')
'''])


# ===========================================================================
# 9.  A PROPOSITIONAL CORE
# ===========================================================================

def proof_core_script(premises: Sequence[str], goal: str,
                      label: str = "CORE") -> str:
    """A truth-table check that the premises entail the goal (the
    propositional core of a proof whose substance is a Lean theorem)."""
    return "\n".join([
        "from itertools import product",
        "import re",
        f"PREM, GOAL = {list(premises)!r}, {goal!r}",
        r'''
def parse(s):
    t = re.findall(r'<->|->|[~&|()]|[A-Za-z_]\w*', s); pos = [0]
    def peek(): return t[pos[0]] if pos[0] < len(t) else None
    def take():
        pos[0] += 1; return t[pos[0] - 1]
    def iff():
        a = imp()
        while peek() == '<->':
            take(); b = imp(); a = ('iff', a, b)
        return a
    def imp():
        a = dis()
        if peek() == '->':
            take(); return ('imp', a, imp())
        return a
    def dis():
        a = con()
        while peek() == '|':
            take(); a = ('or', a, con())
        return a
    def con():
        a = una()
        while peek() == '&':
            take(); a = ('and', a, una())
        return a
    def una():
        x = take()
        if x == '~': return ('not', una())
        if x == '(':
            a = iff(); assert take() == ')'; return a
        return ('atom', x)
    f = iff(); assert peek() is None; return f
def ev(f, env):
    k = f[0]
    if k == 'atom': return env[f[1]]
    if k == 'not': return not ev(f[1], env)
    a, b = ev(f[1], env), ev(f[2], env)
    return {'and': a and b, 'or': a or b, 'imp': (not a) or b, 'iff': a == b}[k]
atoms = sorted(set(re.findall(r'[A-Za-z_]\w*', ' '.join(PREM + [GOAL]))) - {'false', 'true'})
for vals in product([False, True], repeat=len(atoms)):
    env = dict(zip(atoms, vals)); env.update(false=False, true=True)
    if all(ev(parse(p), env) for p in PREM):
        assert ev(parse(GOAL), env), env
print(''' + repr(label) + ''', 'premises entail the goal over', len(atoms), 'atoms VERIFIED True')
'''])

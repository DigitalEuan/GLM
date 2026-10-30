"""``glm_universal.runtime.derivation_scripts`` -- the column-3 scripts of
Phase 106's derivations (``studies/DERIVATION_STUDY.md``).

Every script is stand-alone standard-library Python that shares no code
with :mod:`glm_universal.reasoning.derivation` or
:mod:`glm_universal.reasoning.proof_search`: it reads the *texts* -- the
Lagrangian, the model, the flux law, the sequent -- with Python's own
``ast`` parser, differentiates them with its own tree differentiator, and
checks the claimed answer exactly at rational points:

* a trigonometric atom is evaluated at an angle whose sine and cosine are
  rational (a Pythagorean point of the unit circle), and an integer
  combination of such angles by complex multiplication, so nothing is
  approximated;
* a logarithm of a letter is a free rational value, the same at every
  occurrence (an identity in the logarithms holds for every such value);
* a square root is only ever taken of a rational square;
* a squared frequency with a square root in it is evaluated in the
  quadratic field of that root;
* a proof is re-checked rule by rule against the rules of G4ip, re-written
  here, and the sequent's truth table is re-enumerated.

The last line is ``VERIFIED True`` when every check holds.  No float is
used anywhere (D7).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = ["CALC", "motion_script", "transfer_script", "profile_script",
           "proof_script"]

#: The tree calculus every script carries.
CALC = r'''
from fractions import Fraction as F
import ast

class Seed:
    def __init__(self, s):
        self.s = s
    def nxt(self):
        self.s = (self.s * 6364136223846793005 + 1442695040888963407) % (1 << 64)
        return self.s >> 33
    def frac(self):
        return F(self.nxt() % 89 + 2, self.nxt() % 13 + 3)

ANGLES = [(F(3, 5), F(4, 5)), (F(5, 13), F(12, 13)), (F(8, 17), F(15, 17)),
          (F(7, 25), F(24, 25)), (F(-3, 5), F(4, 5)), (F(20, 29), F(-21, 29)),
          (F(12, 37), F(35, 37)), (F(-9, 41), F(-40, 41))]

def tree(text):
    text = text.strip().replace('^', '**')
    return conv(ast.parse(text, mode='eval').body)

def conv(n):
    if isinstance(n, ast.Constant):
        return ('num', F(n.value))
    if isinstance(n, ast.Name):
        return ('var', n.id)
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
        return ('neg', conv(n.operand))
    if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.UAdd):
        return conv(n.operand)
    if isinstance(n, ast.BinOp):
        op = {ast.Add: 'add', ast.Sub: 'sub', ast.Mult: 'mul',
              ast.Div: 'div', ast.Pow: 'pow'}[type(n.op)]
        a, b = conv(n.left), conv(n.right)
        if op == 'pow':
            e = value(b, {})
            return ('pow', a, e)
        return (op, a, b)
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
        return ('call', n.func.id, conv(n.args[0]))
    raise ValueError('unreadable')

def names(t, out=None):
    out = set() if out is None else out
    if t[0] == 'var':
        out.add(t[1])
    elif t[0] in ('add', 'sub', 'mul', 'div'):
        names(t[1], out); names(t[2], out)
    elif t[0] in ('neg', 'pow'):
        names(t[1], out)
    elif t[0] == 'call':
        names(t[2], out)
    return out

def trig_names(t, out=None, inside=False):
    out = set() if out is None else out
    if t[0] == 'var' and inside:
        out.add(t[1])
    elif t[0] in ('add', 'sub', 'mul', 'div'):
        trig_names(t[1], out, inside); trig_names(t[2], out, inside)
    elif t[0] in ('neg', 'pow'):
        trig_names(t[1], out, inside)
    elif t[0] == 'call':
        trig_names(t[2], out, inside or t[1] in ('sin', 'cos'))
    return out

def plain_names(t, out=None):
    out = set() if out is None else out
    if t[0] == 'var':
        out.add(t[1])
    elif t[0] in ('add', 'sub', 'mul', 'div'):
        plain_names(t[1], out); plain_names(t[2], out)
    elif t[0] in ('neg', 'pow'):
        plain_names(t[1], out)
    elif t[0] == 'call' and t[1] not in ('sin', 'cos'):
        plain_names(t[2], out)
    return out

ZERO, ONE = ('num', F(0)), ('num', F(1))

def add(a, b):
    if a == ZERO: return b
    if b == ZERO: return a
    return ('add', a, b)

def sub(a, b):
    if b == ZERO: return a
    return ('sub', a, b)

def mul(a, b):
    if a == ZERO or b == ZERO: return ZERO
    if a == ONE: return b
    if b == ONE: return a
    return ('mul', a, b)

def d(t, v):
    k = t[0]
    if k == 'num':
        return ZERO
    if k == 'var':
        return ONE if t[1] == v else ZERO
    if k == 'neg':
        x = d(t[1], v)
        return ZERO if x == ZERO else ('neg', x)
    if k == 'add':
        return add(d(t[1], v), d(t[2], v))
    if k == 'sub':
        return sub(d(t[1], v), d(t[2], v))
    if k == 'mul':
        return add(mul(d(t[1], v), t[2]), mul(t[1], d(t[2], v)))
    if k == 'div':
        num = sub(mul(d(t[1], v), t[2]), mul(t[1], d(t[2], v)))
        return ZERO if num == ZERO else ('div', num, ('pow', t[2], F(2)))
    if k == 'pow':
        x = d(t[1], v)
        if x == ZERO: return ZERO
        return mul(mul(('num', t[2]), ('pow', t[1], t[2] - 1)), x)
    if k == 'call':
        f, a = t[1], t[2]
        x = d(a, v)
        if x == ZERO: return ZERO
        if f == 'sin': return mul(('call', 'cos', a), x)
        if f == 'cos': return mul(('neg', ('call', 'sin', a)), x)
        if f == 'exp': return mul(t, x)
        if f == 'ln': return ('div', x, a)
        if f == 'sqrt': return ('div', x, ('mul', ('num', F(2)), t))
    raise ValueError('no derivative')

def linear_form(t):
    k = t[0]
    if k == 'var':
        return {t[1]: F(1)}
    if k == 'num':
        if t[1] != 0: raise ValueError('a trigonometric argument with a constant')
        return {}
    if k == 'neg':
        return {x: -c for x, c in linear_form(t[1]).items()}
    if k in ('add', 'sub'):
        a, b = linear_form(t[1]), linear_form(t[2])
        s = -1 if k == 'sub' else 1
        out = dict(a)
        for x, c in b.items():
            out[x] = out.get(x, 0) + s * c
        return out
    if k == 'mul':
        for i, j in ((1, 2), (2, 1)):
            if t[i][0] == 'num':
                return {x: c * t[i][1] for x, c in linear_form(t[j]).items()}
    raise ValueError('a trigonometric argument that is not an integer combination')

def cmul(a, b):
    return (a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0])

def angle(lf, env):
    z = (F(1), F(0))
    for x, c in lf.items():
        if c.denominator != 1: raise ValueError('a fractional multiple of an angle')
        base = env['@' + x]
        n = int(c)
        if n < 0:
            base, n = (base[0], -base[1]), -n
        for _ in range(n):
            z = cmul(z, base)
    return z

def isqrt_frac(q):
    if q < 0: raise ValueError('a negative square root')
    def r(n):
        lo, hi = 0, n + 1
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            if mid * mid <= n: lo = mid
            else: hi = mid
        if lo * lo != n: raise ValueError('not a square')
        return lo
    return F(r(q.numerator), r(q.denominator))

def log_of(t, env):
    k = t[0]
    if k == 'var':
        return env['ln:' + t[1]]
    if k == 'num':
        if t[1] == 1: return F(0)
        if t[1] <= 0: raise ValueError('a logarithm of a non-positive number')
        return env.setdefault('ln#' + str(t[1]), F(7, 3) + t[1])
    if k == 'mul': return log_of(t[1], env) + log_of(t[2], env)
    if k == 'div': return log_of(t[1], env) - log_of(t[2], env)
    if k == 'pow': return t[2] * log_of(t[1], env)
    raise ValueError('a logarithm of a sum')

def value(t, env):
    k = t[0]
    if k == 'num': return t[1]
    if k == 'var': return env[t[1]]
    if k == 'neg': return -value(t[1], env)
    if k == 'add': return value(t[1], env) + value(t[2], env)
    if k == 'sub': return value(t[1], env) - value(t[2], env)
    if k == 'mul': return value(t[1], env) * value(t[2], env)
    if k == 'div':
        b = value(t[2], env)
        if b == 0: raise ZeroDivisionError('division by zero')
        return value(t[1], env) / b
    if k == 'pow':
        e = t[2]
        b = value(t[1], env)
        if e.denominator == 1: return b ** int(e)
        if e.denominator == 2: return isqrt_frac(b) ** e.numerator
        raise ValueError('a fractional power')
    if k == 'call':
        f, a = t[1], t[2]
        if f in ('sin', 'cos'):
            z = angle(linear_form(a), env)
            return z[1] if f == 'sin' else z[0]
        if f == 'sqrt': return isqrt_frac(value(a, env))
        if f == 'ln': return log_of(a, env)
    raise ValueError('cannot evaluate ' + repr(k))
'''


def _frac_src(x) -> str:
    x = Fraction(x)
    return f"F({x.numerator}, {x.denominator})"


def _q(x) -> str:
    return repr(x)


def motion_script(lagrangian: str, coords: Sequence[str],
                  equations: Sequence[str], linear: Optional[Sequence[str]],
                  frequencies: Optional[Sequence[str]], label: str,
                  divisors: Optional[Sequence[str]] = None,
                  freq_algs: Optional[Dict[str, tuple]] = None,
                  cubic: Optional[Sequence[str]] = None,
                  positive: bool = False) -> str:
    """Check ``equations`` (each ``E = 0`` as ``E``), each multiplied by the
    divisor the answer states, proportional to the Euler-Lagrange
    expressions of ``lagrangian`` (a constant, nonzero ratio, the divisor
    nonzero at every point used); ``linear`` proportional to
    their linear parts at the origin; ``frequencies`` roots of
    ``det(K - w2 M)``.  ``freq_algs`` (Phase 108) names the algebraic
    numbers a frequency holds, ``alias -> (monic m from the constant term
    up, lo, hi)``: the script checks by Sturm's theorem that ``(lo, hi)``
    holds one root of ``m`` and the determinant in ``Q[t]/m``.  ``cubic``
    (sharpening pass) is a characteristic cubic answered stepwise,
    ``[c0, c1, c2, c3]`` in ``w2``: the script checks it proportional to
    its own ``det(K - w2 M)`` and, by Sturm's theorem, that it has three
    distinct real roots (``positive``: all in ``(0, B]``) at every point.
    Phase 109: ``cubic`` may be of any degree ``n`` (a stepwise answer for
    ``n`` degrees of freedom); the script then counts ``n`` roots, and for a
    quartic also checks that the resolvent cubic has three roots ``> 0``."""
    algs = {k: ([_frac_src(c) for c in m], _frac_src(lo), _frac_src(hi))
            for k, (m, lo, hi) in (freq_algs or {}).items()}
    algs_src = "{" + ", ".join(f"{k!r}: ([{', '.join(m)}], {lo}, {hi})"
                               for k, (m, lo, hi) in algs.items()) + "}"
    return CALC + f'''
L = tree({_q(lagrangian)})
COORDS = {_q(list(coords))}
CLAIMS = {_q(list(equations))}
DIVISORS = {_q(list(divisors) if divisors is not None else ["1"] * len(equations))}
LINEAR = {_q(list(linear) if linear is not None else None)}
FREQS = {_q(list(frequencies) if frequencies is not None else None)}
FREQ_ALGS = {algs_src}
CUBIC = {_q(list(cubic) if cubic is not None else None)}
POSITIVE = {positive!r}

def ddt(t):
    out = ZERO
    for q in COORDS:
        out = add(out, mul(d(t, q), ('var', q + '_dot')))
        out = add(out, mul(d(t, q + '_dot'), ('var', q + '_ddot')))
    return out

EL = [sub(ddt(d(L, q + '_dot')), d(L, q)) for q in COORDS]
DYN = set()
for q in COORDS:
    DYN |= {{q, q + '_dot', q + '_ddot'}}
ALL = set(names(L))
for c in CLAIMS + DIVISORS + (LINEAR or []) + (FREQS or []) + (CUBIC or []):
    ALL |= names(tree(c))
PARAMS = sorted(ALL - DYN - {{'w2'}} - set(FREQ_ALGS))

def proportional(claim, mine, dyn_env, seeds=(1, 2)):
    ok = True
    for s0 in seeds:
        rng = Seed(1000 + s0)
        params = {{p: rng.frac() for p in PARAMS}}
        ratio = None
        hits = 0
        for k in range(6):
            env = dict(params)
            env.update(dyn_env(rng, k))
            try:
                a, b = value(claim, env), value(mine, env)
            except ZeroDivisionError:
                continue
            if claim[0] == 'mul' and value(claim[2], env) == 0:
                continue
            if b == 0:
                if a != 0: return False
                continue
            hits += 1
            r = a / b
            if r == 0 or (ratio is not None and r != ratio):
                return False
            ratio = r
        ok = ok and hits >= 3
    return ok

TRIG = set()
PLAIN = set()
for t in [L] + [tree(c) for c in CLAIMS]:
    TRIG |= trig_names(t)
    PLAIN |= plain_names(t)
clash = TRIG & PLAIN & set(COORDS)
assert not clash, 'a coordinate both inside and outside a sine'

def full_env(rng, k):
    env = {{}}
    for i, q in enumerate(COORDS):
        env['@' + q] = ANGLES[(k + 3 * i) % len(ANGLES)]
        env[q] = rng.frac()
        env[q + '_dot'] = rng.frac() - 3
        env[q + '_ddot'] = rng.frac() - 5
    return env

checks = []
for c, dv, e in zip(CLAIMS, DIVISORS, EL):
    checks.append(proportional(('mul', tree(c), tree(dv)), e, full_env))

if LINEAR is not None:
    zero = {{}}
    for q in COORDS:
        zero['@' + q] = (F(1), F(0))
        zero[q] = zero[q + '_dot'] = zero[q + '_ddot'] = F(0)
    lin_parts = []
    for e in EL:
        lin_parts.append([(v, d(e, v)) for q in COORDS
                          for v in (q, q + '_dot', q + '_ddot')])
    def lin_value(i, env, params):
        z = dict(params); z.update(zero)
        e0 = value(EL[i], z)
        assert e0 == 0, 'the origin is not an equilibrium'
        return sum(value(dv, z) * env[v] for v, dv in lin_parts[i])
    def lin_env(rng, k):
        env = {{}}
        for q in COORDS:
            env[q] = rng.frac() - 4
            env[q + '_dot'] = rng.frac() - 3
            env[q + '_ddot'] = rng.frac() - 5
        return env
    for i, c in enumerate(LINEAR):
        ct = tree(c)
        ok = True
        for s0 in (1, 2):
            rng = Seed(2000 + s0)
            params = {{p: rng.frac() for p in PARAMS}}
            ratio = None
            for k in range(5):
                env = dict(params); env.update(lin_env(rng, k))
                a = value(ct, env)
                b = lin_value(i, env, params)
                if b == 0:
                    ok = ok and a == 0
                    continue
                r = a / b
                if r == 0 or (ratio is not None and r != ratio):
                    ok = False
                ratio = r
        checks.append(ok)

class Q2:
    D = None
    def __init__(self, a, b=F(0)):
        self.a, self.b = F(a), F(b)
    def __add__(self, o):
        o = o if isinstance(o, Q2) else Q2(o)
        return Q2(self.a + o.a, self.b + o.b)
    def __sub__(self, o):
        o = o if isinstance(o, Q2) else Q2(o)
        return Q2(self.a - o.a, self.b - o.b)
    def __neg__(self):
        return Q2(-self.a, -self.b)
    def __mul__(self, o):
        o = o if isinstance(o, Q2) else Q2(o)
        dd = Q2.D or 0
        return Q2(self.a * o.a + dd * self.b * o.b, self.a * o.b + self.b * o.a)
    def __truediv__(self, o):
        o = o if isinstance(o, Q2) else Q2(o)
        dd = Q2.D or 0
        n = o.a * o.a - dd * o.b * o.b
        if n == 0: raise ZeroDivisionError('division by zero')
        return self * Q2(o.a / n, -o.b / n)
    def __pow__(self, e):
        out = Q2(1)
        for _ in range(int(e)):
            out = out * self
        return out
    def zero(self):
        return self.a == 0 and self.b == 0

def qvalue(t, env):
    k = t[0]
    if k == 'num': return Q2(t[1])
    if k == 'var': return Q2(env[t[1]])
    if k == 'neg': return -qvalue(t[1], env)
    if k == 'add': return qvalue(t[1], env) + qvalue(t[2], env)
    if k == 'sub': return qvalue(t[1], env) - qvalue(t[2], env)
    if k == 'mul': return qvalue(t[1], env) * qvalue(t[2], env)
    if k == 'div': return qvalue(t[1], env) / qvalue(t[2], env)
    if k == 'pow':
        if t[2].denominator == 2 and t[1][0] == 'num':
            return root(t[1][1]) ** t[2].numerator
        if t[2].denominator == 2:
            return root(rational(t[1], env)) ** t[2].numerator
        return qvalue(t[1], env) ** t[2]
    if k == 'call' and t[1] == 'sqrt' and t[2][0] == 'num':
        return root(t[2][1])
    if k == 'call' and t[1] == 'sqrt':
        # a square root of an expression in the letters: at a rational
        # point its radicand is a rational number (sharpening pass: a
        # double pendulum with unequal masses printed sqrt(...letters...))
        return root(rational(t[2], env))
    raise ValueError('a frequency outside one quadratic field')

def rational(t, env):
    v = qvalue(t, env)
    if v.b != 0:
        raise ValueError('a radicand outside the rationals')
    if v.a < 0:
        raise ValueError('a negative radicand')
    return v.a

def root(c):
    try:
        return Q2(isqrt_frac(c))
    except ValueError:
        if Q2.D is not None and Q2.D != c:
            raise ValueError('two different square roots')
        Q2.D = c
        return Q2(0, 1)

def qdet(A):
    if len(A) == 1: return A[0][0]
    total = Q2(0)
    for j in range(len(A)):
        minor = [row[:j] + row[j + 1:] for row in A[1:]]
        term = A[0][j] * qdet(minor)
        total = total + term if j % 2 == 0 else total - term
    return total

class QA:
    """Q[t]/MOD, MOD monic (Phase 108: a frequency holding an algebraic
    number)."""
    MOD = None
    def __init__(self, cs):
        self.c = QA.norm([F(x) for x in cs])
    @staticmethod
    def norm(cs):
        m = QA.MOD
        cs = list(cs)
        while len(cs) >= len(m):
            top = cs.pop()
            s = len(cs) - (len(m) - 1)
            for i, y in enumerate(m[:-1]):
                cs[s + i] -= top * y
        while cs and cs[-1] == 0:
            cs.pop()
        return cs
    def __add__(self, o):
        o = o if isinstance(o, QA) else QA([o])
        n = max(len(self.c), len(o.c))
        return QA([(self.c[i] if i < len(self.c) else 0) +
                   (o.c[i] if i < len(o.c) else 0) for i in range(n)])
    def __neg__(self):
        return QA([-x for x in self.c])
    def __sub__(self, o):
        o = o if isinstance(o, QA) else QA([o])
        return self + (-o)
    def __mul__(self, o):
        o = o if isinstance(o, QA) else QA([o])
        out = [F(0)] * (len(self.c) + len(o.c))
        for i, x in enumerate(self.c):
            for j, y in enumerate(o.c):
                out[i + j] += x * y
        return QA(out)
    def __truediv__(self, o):
        o = o if isinstance(o, QA) else QA([o])
        if len(o.c) > 1:
            raise ValueError('division by an algebraic number')
        if not o.c:
            raise ZeroDivisionError('division by zero')
        return QA([x / o.c[0] for x in self.c])
    def __pow__(self, e):
        out = QA([1])
        for _ in range(int(e)):
            out = out * self
        return out
    def zero(self):
        return not self.c

def avalue(t, env):
    k = t[0]
    if k == 'num': return QA([t[1]])
    if k == 'var':
        if t[1] in FREQ_ALGS: return QA([0, 1])
        return QA([env[t[1]]])
    if k == 'neg': return -avalue(t[1], env)
    if k == 'add': return avalue(t[1], env) + avalue(t[2], env)
    if k == 'sub': return avalue(t[1], env) - avalue(t[2], env)
    if k == 'mul': return avalue(t[1], env) * avalue(t[2], env)
    if k == 'div': return avalue(t[1], env) / avalue(t[2], env)
    if k == 'pow' and t[2].denominator == 1:
        return avalue(t[1], env) ** t[2]
    raise ValueError('a frequency outside one algebraic field')

def sturm_count(m, lo, hi):
    def ev1(p, x):
        v = F(0)
        for c in reversed(p):
            v = v * x + c
        return v
    def rem(a, b):
        a = list(a)
        while len(a) >= len(b) and a:
            c = a[-1] / b[-1]
            s = len(a) - len(b)
            for i, y in enumerate(b):
                a[s + i] -= c * y
            while a and a[-1] == 0:
                a.pop()
        return a
    chain = [list(m), [i * m[i] for i in range(1, len(m))]]
    while True:
        r = rem(chain[-2], chain[-1])
        if not r:
            break
        chain.append([-c for c in r])
    def var(x):
        s = [ev1(p, x) for p in chain]
        s = [v for v in s if v != 0]
        return sum(1 for a, b in zip(s, s[1:]) if (a > 0) != (b > 0))
    return var(lo) - var(hi)

def alg_det_zero(f, held, K, M, params):
    if len(held) != 1:
        return False
    m, lo, hi = FREQ_ALGS[next(iter(held))]
    if sturm_count(m, lo, hi) != 1:
        return False
    QA.MOD = list(m)
    w = avalue(tree(f), params)
    A = [[QA([K[i][j]]) - w * QA([M[i][j]]) for j in range(len(COORDS))]
         for i in range(len(COORDS))]
    return qdet_a(A).zero()

def qdet_a(A):
    if len(A) == 1: return A[0][0]
    total = QA([0])
    for j in range(len(A)):
        minor = [row[:j] + row[j + 1:] for row in A[1:]]
        term = A[0][j] * qdet_a(minor)
        total = total + term if j % 2 == 0 else total - term
    return total

if FREQS is not None:
    for s0 in (1, 2):
        rng = Seed(3000 + s0)
        params = {{p: rng.frac() for p in PARAMS}}
        z = dict(params)
        for q in COORDS:
            z['@' + q] = (F(1), F(0))
            z[q] = z[q + '_dot'] = z[q + '_ddot'] = F(0)
        M = [[value(d(e, q + '_ddot'), z) for q in COORDS] for e in EL]
        K = [[value(d(e, q), z) for q in COORDS] for e in EL]
        V = [[value(d(e, q + '_dot'), z) for q in COORDS] for e in EL]
        assert all(x == 0 for row in V for x in row), 'damping at the origin'
        for f in FREQS:
            held = names(tree(f)) & set(FREQ_ALGS)
            if held:
                checks.append(alg_det_zero(f, held, K, M, params))
                continue
            Q2.D = None
            w = qvalue(tree(f), params)
            A = [[Q2(K[i][j]) - w * Q2(M[i][j]) for j in range(len(COORDS))]
                 for i in range(len(COORDS))]
            checks.append(qdet(A).zero())
    checks.append(len(set(FREQS)) == len(FREQS))

if CUBIC is not None:
    for s0 in (1, 2, 3):
        rng = Seed(4000 + s0)
        params = {{p: rng.frac() for p in PARAMS}}
        z = dict(params)
        for q in COORDS:
            z['@' + q] = (F(1), F(0))
            z[q] = z[q + '_dot'] = z[q + '_ddot'] = F(0)
        M = [[value(d(e, q + '_ddot'), z) for q in COORDS] for e in EL]
        K = [[value(d(e, q), z) for q in COORDS] for e in EL]
        cs = [value(tree(c), params) for c in CUBIC]
        deg = len(cs) - 1
        ratio = None
        good = cs[deg] != 0
        points = [F(0), F(1), F(-2), F(5, 3), F(7)]
        points += [F(k + 3, 2) for k in range(deg + 2 - len(points))]
        for w in points:
            A = [[Q2(K[i][j]) - Q2(w) * Q2(M[i][j]) for j in range(len(COORDS))]
                 for i in range(len(COORDS))]
            a = qdet(A).a
            b = F(0)
            for c in reversed(cs):
                b = b * w + c
            if b == 0:
                good = good and a == 0
                continue
            r = a / b
            if r == 0 or (ratio is not None and r != ratio):
                good = False
            ratio = r
        bound = 1 + sum(abs(c / cs[deg]) for c in cs[:deg]) if cs[deg] else F(1)
        lo = F(0) if POSITIVE else -bound
        good = good and sturm_count(cs, lo, bound) == deg
        if deg == 4 and good:
            # Phase 109: the quartic's resolvent cubic has its three roots
            # real and >= 0, the fact the stepwise answer's step 2 uses
            a4, b3, c2, d1, e0 = cs[4], cs[3], cs[2], cs[1], cs[0]
            p = (8 * a4 * c2 - 3 * b3 ** 2) / (8 * a4 ** 2)
            q = (b3 ** 3 - 4 * a4 * b3 * c2 + 8 * a4 ** 2 * d1) / (8 * a4 ** 3)
            r = (16 * a4 * b3 ** 2 * c2 - 64 * a4 ** 2 * b3 * d1
                 - 3 * b3 ** 4 + 256 * a4 ** 3 * e0) / (256 * a4 ** 4)
            res = [-q * q, p * p - 4 * r, 2 * p, F(1)]
            rb = 1 + sum(abs(c) for c in res[:3])
            if q != 0:
                good = good and sturm_count(res, F(0), rb) == 3
        checks.append(good)

ok = all(checks)
print({_q(label)}, len(checks), 'checks')
print('VERIFIED', ok)
'''


def transfer_script(equations: Sequence[str], inputs: Sequence[str],
                    outputs: Sequence[str], unknowns: Sequence[str],
                    claims: Dict[Tuple[str, str], str], label: str) -> str:
    """Check every claimed ``output/input`` against the model linearised and
    transformed by the script itself, at rational points."""
    return CALC + f'''
import re
EQS = {_q(list(equations))}
INPUTS = {_q(list(inputs))}
UNKNOWNS = {_q(list(unknowns))}
CLAIMS = {_q({f"{y}|{u}": v for (y, u), v in claims.items()})}

def prep(t):
    t = re.sub(r'd2\\(\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*\\)\\s*/\\s*dt2', r'\\1__dd', t)
    t = re.sub(r'd\\(\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*\\)\\s*/\\s*dt', r'\\1__d', t)
    a, b = t.split('=')
    return ('sub', tree(a), tree(b))

G = [prep(e) for e in EQS]
DYN = list(UNKNOWNS) + list(INPUTS)
ALL = set()
for g in G:
    ALL |= names(g)
for c in CLAIMS.values():
    ALL |= names(tree(c))
PARAMS = sorted(n for n in ALL if n not in DYN and n != 's' and
                not n.endswith('__d') and not n.endswith('__dd'))

def solve(A, b):
    n = len(A)
    M = [row[:] + [x] for row, x in zip(A, b)]
    for c in range(n):
        p = next(i for i in range(c, n) if M[i][c] != 0)
        M[c], M[p] = M[p], M[c]
        for i in range(n):
            if i != c and M[i][c] != 0:
                f = M[i][c] / M[c][c]
                M[i] = [x - f * y for x, y in zip(M[i], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]

checks = []
for s0 in range(1, 4):
    rng = Seed(4000 + s0)
    env = {{}}
    for p in PARAMS:
        r = rng.frac()
        env[p] = r * r            # squares: a square root of a letter is exact
    ss = dict(env)
    for v in DYN:
        if v + '_s' not in env:
            r = rng.frac()
            env[v + '_s'] = r * r
        ss[v] = env[v + '_s']
        ss[v + '__d'] = ss[v + '__dd'] = F(0)
    s = rng.frac() - 2
    env['s'] = s
    A = []
    cols = []
    for g in G:
        row = []
        for v in UNKNOWNS:
            c0 = value(d(g, v), ss)
            c1 = value(d(g, v + '__d'), ss)
            c2 = value(d(g, v + '__dd'), ss)
            row.append(c0 + c1 * s + c2 * s * s)
        A.append(row)
        cols.append([value(d(g, u), ss) for u in INPUTS])
    for j, u in enumerate(INPUTS):
        x = solve(A, [-c[j] for c in cols])
        for key, claim in CLAIMS.items():
            y, uu = key.split('|')
            if uu != u: continue
            checks.append(value(tree(claim), env) == x[UNKNOWNS.index(y)])

ok = bool(checks) and all(checks)
print({_q(label)}, len(checks), 'checks')
print('VERIFIED', ok)
'''


def profile_script(y: str, x: str, flux: str, source: str,
                   conditions: Sequence[str], claim: str, label: str,
                   extra: Sequence[Tuple[str, str, str]] = ()) -> str:
    """Check ``d/dx(flux * d(claim)/dx) = source`` identically and every
    boundary condition; ``extra`` are further ``(unknown, claim, conditions
    joined by ';')`` triples read with the same law (a second track)."""
    return CALC + f'''
import re
X = {_q(x)}
P, G = tree({_q(flux)}), tree({_q(source)})
TRACKS = [({_q(y)}, {_q(claim)}, {_q(list(conditions))})] + [
    (yy, c, conds.split(';')) for yy, c, conds in {_q(list(extra))}]

checks = []
for Y, claim, conds in TRACKS:
    yt = tree(claim)
    law = sub(d(mul(P, d(yt, X)), X), G)
    ALL = names(yt) | names(P) | names(G)
    for c in conds:
        for side in c.split('='):
            for w in re.findall(r'[A-Za-z_][A-Za-z0-9_]*', side):
                if w not in ('d', 'bounded', 'at'):
                    ALL.add(w)
    ALL.discard(Y)
    for s0 in range(1, 4):
        rng = Seed(5000 + s0)
        env = {{n: rng.frac() for n in ALL}}
        for n in ALL:
            env['ln:' + n] = rng.frac() - 7
        checks.append(value(law, env) == 0)
        for c in conds:
            c = c.strip()
            m = re.fullmatch(Y + r'\\s+bounded\\s+at\\s+0', c)
            if m:
                e0 = dict(env); e0[X] = F(0)
                try:
                    value(yt, e0)
                    checks.append(True)
                except (ZeroDivisionError, KeyError, ValueError):
                    checks.append(False)
                continue
            m = re.fullmatch(r'd\\(' + Y + r'\\)/d' + X + r'\\((.+)\\)\\s*=\\s*(.+)', c)
            target = yt
            if m:
                target = d(yt, X)
            else:
                m = re.fullmatch(Y + r'\\((.+)\\)\\s*=\\s*(.+)', c)
            at, want = tree(m.group(1)), tree(m.group(2))
            e1 = dict(env)
            e1[X] = value(at, env)
            if at[0] == 'var':
                e1['ln:' + X] = env['ln:' + at[1]]
            elif at[0] == 'num' and at[1] == 1:
                e1['ln:' + X] = F(0)
            checks.append(value(target, e1) == value(want, env))

ok = all(checks)
print({_q(label)}, len(checks), 'checks')
print('VERIFIED', ok)
'''


def proof_script(premises: Sequence, goal, verdict: str, proof,
                 valuation: Optional[Dict[str, bool]],
                 excluded: Sequence[str], kripke, label: str) -> str:
    """Re-check the verdict: a G4ip proof rule by rule (from the declared
    excluded-middle instances for a classical verdict), the truth table, a
    falsifying valuation, a Kripke countermodel."""

    def enc(p):
        if p is None:
            return None
        return (p.rule, list(p.context), p.goal, p.principal,
                [enc(q) for q in p.premises])

    return f'''
from itertools import product
PREMISES = {_q(list(premises))}
GOAL = {_q(goal)}
VERDICT = {_q(verdict)}
PROOF = {_q(enc(proof))}
VALUATION = {_q(valuation)}
EXCLUDED = {_q(list(excluded))}
KRIPKE = {_q(kripke)}
BOT = ('bot',)

def imp(a, b):
    return ('imp', a, b)

def atoms(fs):
    out = []
    def walk(f):
        if f[0] == 'atom':
            if f[1] not in out: out.append(f[1])
        elif f[0] != 'bot':
            walk(f[1]); walk(f[2])
    for f in fs: walk(f)
    return out

def holds(f, v):
    if f[0] == 'atom': return v[f[1]]
    if f[0] == 'bot': return False
    a, b = holds(f[1], v), holds(f[2], v)
    if f[0] == 'imp': return (not a) or b
    if f[0] == 'and': return a and b
    return a or b

def tautology(prem, goal):
    names = atoms(list(prem) + [goal])
    for bits in product((False, True), repeat=len(names)):
        v = dict(zip(names, bits))
        if all(holds(p, v) for p in prem) and not holds(goal, v):
            return False
    return True

def same(a, b):
    return sorted(map(repr, a)) == sorted(map(repr, b))

def minus(ctx, f):
    out = list(ctx)
    out.remove(f)
    return out

def premises_of(rule, ctx, g, f):
    if rule == 'L-false': return [] if BOT in ctx else None
    if rule == 'axiom': return [] if g[0] == 'atom' and g in ctx else None
    if rule in ('R->', 'R&', 'R|1', 'R|2'):
        if f != g: return None
        if rule == 'R->' and g[0] == 'imp': return [(ctx + [g[1]], g[2])]
        if rule == 'R&' and g[0] == 'and': return [(ctx, g[1]), (ctx, g[2])]
        if rule == 'R|1' and g[0] == 'or': return [(ctx, g[1])]
        if rule == 'R|2' and g[0] == 'or': return [(ctx, g[2])]
        return None
    if f not in ctx: return None
    rest = minus(ctx, f)
    if rule == 'L&' and f[0] == 'and': return [(rest + [f[1], f[2]], g)]
    if rule == 'L|' and f[0] == 'or': return [(rest + [f[1]], g), (rest + [f[2]], g)]
    if f[0] != 'imp': return None
    a, b = f[1], f[2]
    if rule == 'L-false->' and a == BOT: return [(rest, g)]
    if rule == 'L0->' and a[0] == 'atom' and a in rest: return [(rest + [b], g)]
    if rule == 'L&->' and a[0] == 'and': return [(rest + [imp(a[1], imp(a[2], b))], g)]
    if rule == 'L|->' and a[0] == 'or': return [(rest + [imp(a[1], b), imp(a[2], b)], g)]
    if rule == 'L->->' and a[0] == 'imp':
        return [(rest + [imp(a[2], b)], imp(a[1], a[2])), (rest + [b], g)]
    return None

def check(node):
    rule, ctx, g, f, kids = node
    want = premises_of(rule, list(ctx), g, f)
    if want is None or len(want) != len(kids): return False
    for (c, gg), k in zip(want, kids):
        if not same(c, k[1]) or k[2] != gg or not check(k): return False
    return True

def forces(w, f, up, val):
    if f[0] == 'atom': return f[1] in val[w]
    if f[0] == 'bot': return False
    if f[0] == 'and': return forces(w, f[1], up, val) and forces(w, f[2], up, val)
    if f[0] == 'or': return forces(w, f[1], up, val) or forces(w, f[2], up, val)
    return all((not forces(u, f[1], up, val)) or forces(u, f[2], up, val) for u in up[w])

checks = []
if VERDICT in ('intuitionistic', 'classical'):
    lem = [('or', ('atom', a), imp(('atom', a), BOT)) for a in EXCLUDED]
    if VERDICT == 'intuitionistic':
        checks.append(not EXCLUDED)
    checks.append(PROOF is not None and same(PROOF[1], lem + PREMISES)
                  and PROOF[2] == GOAL and check(PROOF))
    checks.append(tautology(PREMISES, GOAL))
    if VERDICT == 'classical' and KRIPKE is not None:
        up, val = KRIPKE
        up = {{int(k): v for k, v in up.items()}}
        val = {{int(k): set(v) for k, v in val.items()}}
        refl = all(w in up[w] for w in up)
        trans = all(x in up[w] for w in up for u in up[w] for x in up[u])
        mono = all(val[w] <= val[u] for w in up for u in up[w])
        checks.append(refl and trans and mono and
                      all(forces(0, p, up, val) for p in PREMISES) and
                      not forces(0, GOAL, up, val))
else:
    v = VALUATION
    checks.append(v is not None and all(holds(p, v) for p in PREMISES)
                  and not holds(GOAL, v))
ok = all(checks)
print({_q(label)}, VERDICT, len(checks), 'checks')
print('VERIFIED', ok)
'''

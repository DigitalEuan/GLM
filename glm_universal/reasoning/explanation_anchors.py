"""``glm_universal.reasoning.explanation_anchors`` -- the outside questions
that ask *why*, answered where a register or an exact derivation decides
them (Phase 120, track E of ``studies/QUESTION_SET_B_STUDY.md`` §8; the study
is ``studies/EXPLANATION_ANCHOR_STUDY.md``).

What it does
------------
Each declared **topic** reads one outside question (or a rewording of it) by
its cue words and answers in three parts:

* **anchors** -- values read from a register *when the question is read*
  (the element register, ``data_objects/elements.py``; the nuclide register,
  ``data_objects/nuclides.py``, frozen from AME2020 and NUBASE2020; the
  propositional prover, ``reasoning/proof_search.py``; the integer
  procedure's node budget, ``reasoning/integer_decision.py``), and
  quantities computed from them exactly -- a Q-value from two mass excesses,
  a molar volume from a weight and a density, a Slater charge from a
  configuration, an s-process path from half-lives;
* **derivations** -- closed statements computed and gated here, with the
  theorem that proves them in ``RequestProject/GLM/ExplanationAnchors.lean``
  (or an earlier Lean file) named in the answer;
* **the account refused** -- what the question asks that is a causal or
  philosophical account rather than a value is written into the answer as
  ``refused EXPLANATION``, with what it would need.  A topic declared
  ``FULL`` decides every part of its question and writes no such line.

Every answer carries a column-3 script that embeds the register rows it
read (as the register prints them) and the claims it makes, re-derives each
claim from the rows with code written independently of this module, and
prints ``VERIFIED True`` only if every claim is recomputed exactly.  Two
controls are applied by :func:`mutated`: an altered headline claim
(``script-claim``) and an altered register row (``register-row``); each must
make the script print ``VERIFIED False``.

No float is constructed (D7): square roots, cube roots, logarithms,
exponentials, pi and the sine integral are all enclosed between rationals
by integer arithmetic, and a decimal is written only from such an enclosure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction as F
from math import isqrt
from typing import Callable, Dict, List, Optional, Sequence, Tuple

__all__ = ["Answer", "Topic", "TOPICS", "topic_of", "read_topic", "mutated",
           "LEAN_FILE", "MUTATION_KINDS", "rnd", "sqrt_bounds", "ln_bounds",
           "exp_bounds", "pi_bounds", "gibbs_bounds", "slater_zeff",
           "madelung", "parse_configuration", "s_process", "TOPIC_KEYS"]

LEAN_FILE = "RequestProject/GLM/ExplanationAnchors.lean"
MUTATION_KINDS = ("script-claim", "register-row")

#: CODATA 2018 fine-structure constant, exact as printed.
ALPHA = F(1) / F("137.035999084")
#: CODATA 2018 hbar c in MeV fm, exact as printed.
HBARC = F("197.3269804")
#: SI 2019 exact constants: Boltzmann (J/K) and the elementary charge (C).
K_B = F(1380649, 10 ** 29)
Q_E = F(1602176634, 10 ** 28)


# ===========================================================================
# 1.  EXACT ENCLOSURES
# ===========================================================================

def rnd(x: F, d: int) -> str:
    """``x`` rounded half away from zero to ``d`` decimals, as text."""
    sgn = "-" if x < 0 else ""
    x = abs(x)
    s = 10 ** d
    n = (x * s * 2 + 1) // 2
    ip, fp = divmod(int(n), s)
    return f"{sgn}{ip}" + (f".{fp:0{d}d}" if d else "")


def sqrt_bounds(x: F, d: int = 12) -> Tuple[F, F]:
    """``lo <= sqrt(x) <= hi`` with ``hi - lo = 10^-d``."""
    s = 10 ** d
    r = isqrt(int(x * s * s))
    return F(r, s), F(r + 1, s)


def cbrt_bounds(x: F, d: int = 12) -> Tuple[F, F]:
    s = 10 ** d
    n = int(x * s ** 3)
    lo, hi = 0, 1
    while hi ** 3 <= n:
        hi *= 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if mid ** 3 <= n:
            lo = mid
        else:
            hi = mid
    return F(lo, s), F(lo + 1, s)


def _down(x: F, d: int) -> F:
    s = 10 ** d
    return F((x.numerator * s) // x.denominator, s)


def _up(x: F, d: int) -> F:
    s = 10 ** d
    return F(-((-x.numerator * s) // x.denominator), s)


def _atanh_bounds(z: F, terms: int = 60) -> Tuple[F, F]:
    """``atanh(z)`` for ``0 <= z <= 1/3``: partial sums rounded outward at
    ``10^-70`` (so the numbers stay short), and the remainder."""
    lo = hi = F(0)
    z2 = z * z
    plo = phi = z
    for j in range(terms):
        lo += _down(plo / (2 * j + 1), 70)
        hi += _up(phi / (2 * j + 1), 70)
        plo, phi = _down(plo * z2, 70), _up(phi * z2, 70)
    rem = _up(phi / ((2 * terms + 1) * (1 - z2)), 70)
    return lo, hi + rem


def ln_bounds(x: F) -> Tuple[F, F]:
    """``lo <= ln(x) <= hi`` for rational ``x > 0``."""
    if x <= 0:
        raise ValueError("ln of a non-positive number")
    k = 0
    m = x
    while m >= 2:
        m /= 2
        k += 1
    while m < 1:
        m *= 2
        k -= 1
    l2lo, l2hi = _atanh_bounds(F(1, 3))
    l2lo, l2hi = 2 * l2lo, 2 * l2hi
    mlo, mhi = _atanh_bounds((m - 1) / (m + 1))
    mlo, mhi = 2 * mlo, 2 * mhi
    if k >= 0:
        return k * l2lo + mlo, k * l2hi + mhi
    return k * l2hi + mlo, k * l2lo + mhi


def exp_bounds(x: F) -> Tuple[F, F]:
    """``lo <= e^x <= hi`` for rational ``x``."""
    s = 0
    y = x
    while abs(y) > F(1, 8):
        y /= 2
        s += 1
    lo = F(0)
    t = F(1)
    for j in range(1, 30):
        lo += t
        t = t * y / j
    # |remainder| <= 2 |t| for |y| <= 1/8
    hi = lo + 2 * abs(t)
    lo = lo - 2 * abs(t)
    for _ in range(s):
        lo, hi = lo * lo, hi * hi
    return lo, hi


def pi_bounds() -> Tuple[F, F]:
    """Machin: ``pi = 16 atan(1/5) - 4 atan(1/239)``, enclosed and rounded
    outward to ``10^-16``."""
    def atan(z: F, n: int) -> Tuple[F, F]:
        s, p = F(0), z
        for j in range(n):
            s += (-1) ** j * p / (2 * j + 1)
            p *= z * z
        e = p / (2 * n + 1)
        return (s - e, s + e)
    a5 = atan(F(1, 5), 14)
    a239 = atan(F(1, 239), 5)
    return (_down(16 * a5[0] - 4 * a239[1], 16),
            _up(16 * a5[1] - 4 * a239[0], 16))


def _si(x: F, n: int = 26) -> Tuple[F, F]:
    """The sine integral ``Si(x)`` for ``0 < x <= 4``, alternating series."""
    s = F(0)
    for k in range(n):
        s += F((-1) ** k) * x ** (2 * k + 1) / ((2 * k + 1) * _fact(2 * k + 1))
    e = x ** (2 * n + 1) / ((2 * n + 1) * _fact(2 * n + 1))
    return s - e, s + e


def _fact(n: int) -> int:
    out = 1
    for i in range(2, n + 1):
        out *= i
    return out


def gibbs_bounds() -> Tuple[F, F]:
    """``Si(pi)/pi - 1/2``: the Gibbs overshoot as a fraction of the jump.
    ``Si`` is increasing on ``[0, pi]``, so it is enclosed through pi's
    enclosure."""
    plo, phi = pi_bounds()
    slo = _down(_si(plo)[0], 24)
    shi = _up(_si(phi)[1], 24)
    return _down(slo / phi - F(1, 2), 24), _up(shi / plo - F(1, 2), 24)


def _log10_bounds(x: F) -> Tuple[F, F]:
    a, b = ln_bounds(x)
    c, d = ln_bounds(F(10))
    if x >= 1:
        return a / d, b / c
    return a / c, b / d


def sci(lo: F, hi: F, sig: int = 3) -> str:
    """A value enclosed in ``[lo, hi]`` written as ``m x 10^e``, when both
    ends agree to ``sig`` significant figures (else both are written)."""
    def one(x: F) -> Tuple[str, int]:
        e = 0
        while x >= 10:
            x /= 10
            e += 1
        while x < 1:
            x *= 10
            e -= 1
        return rnd(x, sig - 1), e
    a, b = one(lo), one(hi)
    if a == b:
        return f"{a[0]} x 10^{a[1]}"
    return f"between {a[0]} x 10^{a[1]} and {b[0]} x 10^{b[1]}"


# ===========================================================================
# 2.  CONFIGURATIONS
# ===========================================================================

_L = {"s": 0, "p": 1, "d": 2, "f": 3}
_CAP = {"s": 2, "p": 6, "d": 10, "f": 14}


def madelung_order() -> List[Tuple[int, str]]:
    shells = [(n, l) for n in range(1, 8) for l in "spdf" if _L[l] < n]
    return sorted(shells, key=lambda t: (t[0] + _L[t[1]], t[0]))


def madelung(z: int) -> Dict[str, int]:
    """The Madelung (n + l, then n) filling of ``z`` electrons."""
    out: Dict[str, int] = {}
    left = z
    for n, l in madelung_order():
        if left <= 0:
            break
        k = min(_CAP[l], left)
        out[f"{n}{l}"] = k
        left -= k
    return out


_CORES = {"He": 2, "Ne": 10, "Ar": 18, "Kr": 36, "Xe": 54, "Rn": 86}


def parse_configuration(text: str) -> Dict[str, int]:
    """Subshell occupations from a register configuration
    (``[Xe]6s2 4f14 5d6``); the noble-gas core is its own filling."""
    t = text.replace("(predicted)", "").strip()
    out: Dict[str, int] = {}
    m = re.match(r"\[(\w+)\]", t)
    if m:
        out.update(madelung(_CORES[m.group(1)]))
        t = t[m.end():]
    for n, l, k in re.findall(r"(\d)([spdf])(\d+)", t):
        out[f"{n}{l}"] = out.get(f"{n}{l}", 0) + int(k)
    return {k: v for k, v in out.items() if v}


def slater_zeff(z: int, occ: Dict[str, int], shell: str) -> F:
    """Slater's rules for one electron of ``shell`` (an ``s`` or ``p``
    subshell): 0.35 per other electron of the same ``n`` (s, p group),
    0.85 per electron of ``n - 1``, 1.00 per electron deeper."""
    n = int(shell[0])
    sigma = F(0)
    for sub, k in occ.items():
        m, l = int(sub[0]), sub[1]
        if m == n and l in "sp":
            sigma += F(35, 100) * k
        elif m == n - 1:
            sigma += F(85, 100) * k
        elif m < n - 1:
            sigma += k
        elif m == n and l in "df":
            pass                      # same n, d or f: does not shield s, p
    sigma -= F(35, 100)               # the electron itself
    return z - sigma


# ===========================================================================
# 3.  THE S-PROCESS PATH
# ===========================================================================

_YEAR_S = F(3652422, 10000) * 86400
#: Effectively stable: printed 'stbl' or a half-life of at least 10^9 years.
STABLE_YEARS = 10 ** 9
#: The neutron-capture time the path is read against: one year.
CAPTURE_YEARS = 1


def _bminus(decay: str) -> bool:
    return re.search(r"(?<![0-9])B-", decay) is not None


def _node(z: int, a: int) -> Optional[Tuple[int, Optional[F], bool]]:
    """``(effectively_stable, half_life_s, has_beta_minus)`` or ``None``."""
    from ..data_objects import nuclides as N
    nu = N.register().get((z, a))
    if nu is None:
        return None
    if nu.half_life == "stbl":
        return (1, None, False)
    t = N.half_life_seconds(z, a)
    if t is None and nu.half_life.startswith(">"):
        try:
            t = N.dec(nu.half_life[1:]) * (
                N._UNIT_SECONDS.get(nu.unit, F(0)))
        except ValueError:
            t = None
    stable = t is not None and t >= STABLE_YEARS * _YEAR_S
    return (1 if stable else 0, t, _bminus(nu.decay))


def s_process(start: Tuple[int, int] = (26, 56), stop_z: int = 52
              ) -> Tuple[List[Tuple[int, int]], Dict[str, list]]:
    """The s-process path from ``start``: capture a neutron while the
    nucleus is effectively stable or lives longer than a year, beta-decay
    when it has a beta-minus mode and lives less; every node read is
    returned as a row ``"Z,A" -> [stable, half_life_s or None, beta_minus]``."""
    path = [start]
    rows: Dict[str, list] = {}
    z, a = start
    while z <= stop_z:
        nd = _node(z, a)
        if nd is None:
            break
        rows[f"{z},{a}"] = [nd[0], None if nd[1] is None else str(nd[1]),
                            1 if nd[2] else 0]
        stable, t, bm = nd
        long_lived = stable or t is None or t > CAPTURE_YEARS * _YEAR_S
        if long_lived:
            a += 1
        elif bm:
            z += 1
        else:
            z -= 1
        path.append((z, a))
        if len(path) > 400:
            break
    return path, rows


# ===========================================================================
# 4.  ANSWERS AND THEIR SCRIPTS
# ===========================================================================

@dataclass
class Answer:
    topic: str
    answered: bool
    value: str
    column1: str
    column2: str
    script: str
    scope: str = "ANCHORED"
    code: Optional[str] = None
    backing: str = ""
    disputes: Tuple[str, ...] = ()
    rows: Tuple[str, ...] = ()          # register rows read, by name
    lean: Tuple[str, ...] = ()          # Lean declarations cited


@dataclass
class Built:
    """What a topic computes: the answer's parts and its script's inputs."""

    derived: str
    account: str                        # '' for a FULL topic
    rows: Dict[str, object]
    claims: Dict[str, object]
    check: str
    headline: str                       # the claim the script-claim control alters
    key_row: Optional[str] = None       # the row the register-row control alters
    column1: str = ""
    backing: str = ""
    disputes: Tuple[str, ...] = ()
    lean: Tuple[str, ...] = ()
    row_names: Tuple[str, ...] = ()
    #: How the register-row control alters the rows (default: the key row
    #: through :func:`_alter`).
    row_mutation: Optional[Callable[[Dict[str, object]], None]] = None


#: Shared helpers of the column-3 scripts, written apart from the module.
SCRIPT_HEAD = r'''from fractions import Fraction as F
from math import isqrt
import re
def sq_lo_hi(x, d=12):
    s = 10 ** d; r = isqrt(int(x * s * s)); return F(r, s), F(r + 1, s)
def cb_lo_hi(x, d=12):
    s = 10 ** d; n = int(x * s ** 3); lo, hi = 0, 1
    while hi ** 3 <= n: hi *= 2
    while hi - lo > 1:
        m = (lo + hi) // 2
        if m ** 3 <= n: lo = m
        else: hi = m
    return F(lo, s), F(lo + 1, s)
def dn(x, d): s = 10 ** d; return F((x.numerator * s) // x.denominator, s)
def up(x, d): s = 10 ** d; return F(-((-x.numerator * s) // x.denominator), s)
def at(z, n=60):
    lo = hi = F(0); z2 = z * z; a = b = z
    for j in range(n):
        lo += dn(a / (2 * j + 1), 70); hi += up(b / (2 * j + 1), 70)
        a, b = dn(a * z2, 70), up(b * z2, 70)
    return lo, hi + up(b / ((2 * n + 1) * (1 - z2)), 70)
def ln_lo_hi(x):
    k, m = 0, F(x)
    while m >= 2: m /= 2; k += 1
    while m < 1: m *= 2; k -= 1
    a, b = at(F(1, 3)); c, d = at((m - 1) / (m + 1))
    a, b, c, d = 2 * a, 2 * b, 2 * c, 2 * d
    return (k * a + c, k * b + d) if k >= 0 else (k * b + c, k * a + d)
def ex_lo_hi(x):
    s, y = 0, F(x)
    while abs(y) > F(1, 8): y /= 2; s += 1
    v, t = F(0), F(1)
    for j in range(1, 30):
        v += t; t = t * y / j
    lo, hi = v - 2 * abs(t), v + 2 * abs(t)
    for _ in range(s): lo, hi = lo * lo, hi * hi
    return lo, hi
def rd(x, d):
    sg = '-' if x < 0 else ''; x = abs(x); s = 10 ** d
    n = (x * s * 2 + 1) // 2; i, f = divmod(int(n), s)
    return sg + str(i) + ('.' + str(f).zfill(d) if d else '')
ok = True
'''


def script_of(rows: Dict[str, object], claims: Dict[str, object],
              check: str) -> str:
    return (SCRIPT_HEAD + f"ROWS = {rows!r}\nCLAIMS = {claims!r}\n" + check
            + "\nprint('VERIFIED', bool(ok))\n")


def _deep(v: object) -> object:
    if isinstance(v, dict):
        return {k: _deep(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_deep(x) for x in v]
    return v


def _set(path: Sequence, value_of: Callable[[object], object]
         ) -> Callable[[Dict[str, object]], None]:
    """A register-row control that alters one nested cell."""
    def go(rows: Dict[str, object]) -> None:
        cur = rows
        for k in path[:-1]:
            cur = cur[k]
        cur[path[-1]] = value_of(cur[path[-1]])
    return go


def _alter(v: object) -> object:
    if isinstance(v, bool):
        return not v
    if isinstance(v, int):
        return v + 1
    if isinstance(v, str):
        try:
            return str(F(v) + F(1, 7))
        except (ValueError, ZeroDivisionError):
            return v + " MUTATED"
    if isinstance(v, list):
        return [_alter(v[0])] + list(v[1:]) if v else ["MUTATED"]
    if isinstance(v, dict):
        k = sorted(v)[0]
        out = dict(v)
        out[k] = _alter(v[k])
        return out
    return "MUTATED"


# ===========================================================================
# 5.  REGISTER ACCESS
# ===========================================================================

def _el(sym: str):
    from ..data_objects import elements as E
    return E.element_by_symbol(sym)


def _els():
    from ..data_objects import elements as E
    return E.load_element_register()


def _s(x: Optional[F]) -> Optional[str]:
    return None if x is None else str(x)


def _me(z: int, a: int) -> str:
    from ..data_objects import nuclides as N
    nu = N.nuclide(z, a)
    if nu.mass_excess_text is None:
        raise KeyError(nu.name)
    return nu.mass_excess_text


def _nname(z: int, a: int) -> str:
    from ..data_objects import nuclides as N
    return N.nuclide(z, a).name


# ===========================================================================
# 6.  THE TOPICS
# ===========================================================================

def _t_rlc() -> Built:
    samples = []
    for R, L, C in ((F(1), F(1, 10), F(1, 1000)), (F(5), F(2), F(3, 7)),
                    (F(1, 2), F(1, 1000), F(1, 10 ** 6))):
        # omega with omega^2 L C > 1: start at the first rational above
        w0 = F(isqrt(int(1 / (L * C))) + 1)
        samples.append([str(R), str(L), str(C),
                        [str(w0 * F(10 + k, 10)) for k in range(6)]])
    check = r'''
for R, L, C, ws in CLAIMS['samples']:
    R, L, C = F(R), F(L), F(C)
    prev = None
    for w in ws:
        w = F(w)
        ok = ok and w * w * L * C > 1
        X = w * L - 1 / (w * C)
        ok = ok and X > 0
        Z2 = R * R + X * X
        ok = ok and (prev is None or Z2 > prev)
        prev = Z2
ok = ok and CLAIMS['behaviour'] == 'inductive'
'''
    derived = (
        "above resonance (omega^2 L C > 1) the reactance X = omega L - "
        "1/(omega C) is positive and strictly increasing, so |Z| = "
        "sqrt(R^2 + X^2) rises from its minimum R at resonance and the "
        "circuit is inductive: the current lags the voltage by arctan(X/R) "
        "> 0. Proved for every R, L, C > 0 in " + LEAN_FILE +
        " (reactance_pos_above_resonance, impedance_sq_strictMonoOn); "
        "checked on three circuits at six frequencies each")
    return Built(derived, "", {}, {"behaviour": "inductive",
                                   "samples": samples}, check, "behaviour",
                 column1="series RLC: |Z| and the sign of X above resonance",
                 backing="exact rationals + Lean theorem",
                 lean=("reactance_pos_above_resonance",
                       "impedance_sq_strictMonoOn"))


def _t_quasi_fermi() -> Built:
    T = F(300)
    V = F(6, 10)
    x = V * Q_E / (K_B * T)
    lo, hi = exp_bounds(x)
    claims = {"form": "E_Fn - E_Fp = qV", "V": str(V), "T": str(T),
              "kB": str(K_B), "q": str(Q_E), "ratio": sci(lo, hi)}
    check = r'''
x = F(CLAIMS['V']) * F(CLAIMS['q']) / (F(CLAIMS['kB']) * F(CLAIMS['T']))
lo, hi = ex_lo_hi(x)
def sc(v):
    e = 0
    while v >= 10: v /= 10; e += 1
    while v < 1: v *= 10; e -= 1
    return rd(v, 2) + ' x 10^' + str(e)
ok = ok and sc(lo) == sc(hi) and CLAIMS['ratio'] == sc(lo)
# exponents add: n = ni e^((EFn-Ei)/kT), p = ni e^((Ei-EFp)/kT)
EFn, Ei, EFp = F(7, 10), F(1, 10), F(1, 10) - F(CLAIMS['V'])
ok = ok and (EFn - Ei) + (Ei - EFp) == EFn - EFp
ok = ok and CLAIMS['form'] == 'E_Fn - E_Fp = qV'
'''
    derived = (
        "with n = n_i exp((E_Fn - E_i)/kT) and p = n_i exp((E_i - E_Fp)/kT), "
        "n p = n_i^2 exp((E_Fn - E_Fp)/kT); where the quasi-Fermi levels "
        "stay flat across the depletion region, E_Fn - E_Fp = qV_a, so "
        "n p = n_i^2 exp(qV_a/kT) at every point of it (the law of the "
        "junction). At V_a = 0.6 V and T = 300 K, qV_a/kT = " +
        rnd(x, 3) + " and n p / n_i^2 = " + claims["ratio"])
    account = ("the physical mechanism -- why the quasi-Fermi levels stay "
               "flat across the depletion region under low-level injection "
               "and how high injection and series resistance bend them; it "
               "needs a transport model, not a register")
    return Built(derived, account, {}, claims, check, "ratio",
                 column1="quasi-Fermi level separation across a forward-"
                         "biased junction",
                 backing="exact exponential enclosure")


def _t_stork() -> Built:
    syms = ("C", "H", "N", "O", "Br")
    rows = {s: str(_el(s).atomic_weight_u) for s in syms}
    steps = [
        ({"C": 6, "H": 10, "O": 1}, {"C": 4, "H": 9, "N": 1}, "->",
         {"C": 10, "H": 17, "N": 1}, {"H": 2, "O": 1}),
        ({"C": 10, "H": 17, "N": 1}, {"C": 3, "H": 5, "Br": 1}, "->",
         {"C": 13, "H": 22, "N": 1, "Br": 1}, {}),
        ({"C": 13, "H": 22, "N": 1, "Br": 1}, {"H": 2, "O": 1}, "->",
         {"C": 9, "H": 14, "O": 1}, {"C": 4, "H": 10, "N": 1, "Br": 1}),
    ]
    prod = {"C": 9, "H": 14, "O": 1}
    m = sum((F(rows[s]) * k for s, k in prod.items()), F(0))
    claims = {"product": "C9H14O", "molar_mass": rnd(m, 2),
              "steps": [[a, b, c, d] for a, b, _, c, d in steps]}
    check = r'''
for a, b, c, d in CLAIMS['steps']:
    for s in set(a) | set(b) | set(c) | set(d):
        ok = ok and a.get(s, 0) + b.get(s, 0) == c.get(s, 0) + d.get(s, 0)
p = CLAIMS['steps'][-1][2]
ok = ok and CLAIMS['product'] == 'C' + str(p['C']) + 'H' + str(p['H']) + 'O'
m = sum(F(ROWS[s]) * k for s, k in p.items())
ok = ok and rd(m, 2) == CLAIMS['molar_mass']
'''
    derived = (
        "the sequence read as declared (the Stork enamine alkylation): "
        "cyclohexanone C6H10O + pyrrolidine C4H9N -> enamine C10H17N + H2O; "
        "enamine + allyl bromide C3H5Br -> iminium bromide C13H22NBr; "
        "iminium + H2O -> 2-allylcyclohexanone C9H14O + pyrrolidinium "
        "bromide C4H10NBr. Each step balances atom for atom (checked), and "
        "the product's molar mass from the register's atomic weights is " +
        claims["molar_mass"] + " g/mol")
    account = ("the product's identity and regiochemistry (C-alkylation at "
               "the alpha carbon through the enamine) are taken as declared, "
               "not derived; the step-by-step mechanism is an account of "
               "electron flow the registers do not hold")
    return Built(derived, account, rows, claims, check, "molar_mass",
                 key_row="C", column1="the Stork enamine sequence: balance "
                                     "and molar mass",
                 backing="element register (atomic weights)",
                 row_names=tuple(f"element {s}: atomic weight" for s in syms))


def _t_derivative_kick() -> Built:
    K, tau = F(2), F(1, 10)
    ws = [F(1), F(10), F(100), F(1000), F(10 ** 6)]
    claims = {"bound": str(K / tau), "K": str(K), "tau": str(tau),
              "omegas": [str(w) for w in ws], "form": "Kd/tau_f",
              "area": str(K)}
    check = r'''
K, tau = F(CLAIMS['K']), F(CLAIMS['tau'])
ok = ok and F(CLAIMS['bound']) == K / tau
for w in CLAIMS['omegas']:
    w = F(w)
    g2 = K * K * w * w / (1 + w * w * tau * tau)
    ok = ok and g2 < (K / tau) ** 2
    ok = ok and (K * w) ** 2 >= g2
# the filtered kick (K dr/tau) e^(-t/tau) integrates to K dr (dr = 1)
ok = ok and F(CLAIMS['area']) == (K / tau) * tau
ok = ok and CLAIMS['form'] == 'Kd/tau_f'
'''
    derived = (
        "a pure derivative D(s) = Kd s has gain |D(j omega)| = Kd omega, "
        "unbounded, so measurement noise is amplified without limit and the "
        "transfer function is improper (not realisable on its own). A "
        "setpoint step of size dr in e = r - y makes the derivative term an "
        "impulse Kd dr delta(t): the derivative kick. The filtered "
        "derivative Kd s/(1 + tau_f s) has |gain|^2 = Kd^2 omega^2/(1 + "
        "omega^2 tau_f^2) < (Kd/tau_f)^2 at every omega (" + LEAN_FILE +
        ", filtered_derivative_gain_lt; pure_derivative_unbounded), and "
        "turns the kick into (Kd dr/tau_f) e^(-t/tau_f): a finite peak "
        "Kd dr/tau_f with the same area Kd dr. Taking the derivative of the "
        "measurement, -Kd dy/dt, instead of the error removes the kick, "
        "since y does not jump. Checked at Kd = 2, tau_f = 1/10: every gain "
        "below Kd/tau_f = 20")
    return Built(derived, "", {}, claims, check, "bound",
                 column1="pure against filtered derivative action",
                 backing="exact rationals + Lean theorem",
                 lean=("filtered_derivative_gain_lt",
                       "pure_derivative_unbounded"))


def _t_window() -> Built:
    glo, ghi = gibbs_bounds()
    dlo, dhi = _log10_bounds(glo)
    elo, ehi = _log10_bounds(ghi)
    claims = {"gibbs": rnd(glo, 5), "gibbs_lo": rnd(glo, 12),
              "gibbs_hi": rnd(ghi, 12),
              "floor_dB": rnd(20 * dlo, 2)}
    check = r'''
def at_s(z, n):
    s, p = F(0), z
    for j in range(n):
        s += (-1) ** j * p / (2 * j + 1); p *= z * z
    e = p / (2 * n + 1); return s - e, s + e
a, b = at_s(F(1, 5), 14), at_s(F(1, 239), 5)
plo, phi = dn(16 * a[0] - 4 * b[1], 16), up(16 * a[1] - 4 * b[0], 16)
def si(x, n=26):
    s = F(0)
    for k in range(n):
        f = 1
        for i in range(2, 2 * k + 2): f *= i
        s += F((-1) ** k) * x ** (2 * k + 1) / ((2 * k + 1) * f)
    f = 1
    for i in range(2, 2 * n + 2): f *= i
    e = x ** (2 * n + 1) / ((2 * n + 1) * f)
    return s - e, s + e
glo = dn(dn(si(plo)[0], 24) / phi - F(1, 2), 24)
ghi = up(up(si(phi)[1], 24) / plo - F(1, 2), 24)
ok = ok and rd(glo, 12) == CLAIMS['gibbs_lo'] and rd(ghi, 12) == CLAIMS['gibbs_hi']
ok = ok and rd(glo, 5) == CLAIMS['gibbs'] == rd(ghi, 5)
l1, l2 = ln_lo_hi(glo); t1, t2 = ln_lo_hi(F(10))
ok = ok and rd(20 * l1 / t1, 2) == CLAIMS['floor_dB']
'''
    derived = (
        "truncating the ideal response with a rectangular window gives the "
        "least-squares best length-N approximation, but its ripple does not "
        "shrink with N: at a jump the overshoot tends to Si(pi)/pi - 1/2 = " +
        claims["gibbs"] + " of the jump (Gibbs; enclosed exactly here), a "
        "stopband floor of 20 log10(" + claims["gibbs"] + ") = " +
        claims["floor_dB"] + " dB at every length, while only the transition "
        "width (about the main-lobe width 4 pi/N) narrows as N grows. A "
        "tapered window such as Kaiser's lowers the ripple and widens the "
        "main lobe; Kaiser's design formulas for beta and N are empirical "
        "and are quoted by no register here")
    account = ("the design trade-off beyond these two figures (the Kaiser "
               "window's ripple and transition width as functions of beta "
               "rest on empirical fits, not a derivation)")
    return Built(derived, account, {}, claims, check, "gibbs",
                 column1="rectangular against Kaiser windows: the ripple "
                         "that does not shrink",
                 backing="exact enclosures of pi and Si(pi)")


def _t_he_be() -> Built:
    ies = {e.symbol: str(e.ionization_energy_eV) for e in _els()
           if e.ionization_energy_eV is not None}
    he, be = _el("He"), _el("Be")
    top = max(ies, key=lambda s: F(ies[s]))
    claims = {"max_symbol": top, "max_ie": rnd(F(ies[top]), 3),
              "count": len(ies), "be_ie": rnd(F(ies["Be"]), 3),
              "be_en": str(be.electronegativity_pauling),
              "he_en": None if he.electronegativity_pauling is None else
              str(he.electronegativity_pauling)}
    check = r'''
top = max(ROWS, key=lambda s: F(ROWS[s]))
ok = ok and top == CLAIMS['max_symbol'] == 'He'
ok = ok and rd(F(ROWS[top]), 3) == CLAIMS['max_ie']
ok = ok and len(ROWS) == CLAIMS['count']
ok = ok and rd(F(ROWS['Be']), 3) == CLAIMS['be_ie']
'''
    derived = (
        "helium's first ionisation energy, " + claims["max_ie"] + " eV, is "
        "the largest of the " + str(claims["count"]) + " the element register "
        "measures; beryllium's is " + claims["be_ie"] + " eV, and beryllium "
        "has a Pauling electronegativity of " + rnd(F(claims["be_en"]), 2) +
        " where helium has none (the register is silent: helium forms no "
        "bond to measure one from). Both have a filled s shell ([He]2s2 and "
        "1s2 in the register)")
    account = ("why beryllium's filled 2s shell bonds -- the near-degeneracy "
               "of 2s and 2p and the promotion and hybridisation it allows, "
               "against helium's 1s with no n = 1 p shell -- is an orbital "
               "account; the register holds no 2s-2p gap")
    return Built(derived, account, ies, claims, check, "max_ie",
                 key_row="He", column1="helium against beryllium: ionisation "
                                       "and electronegativity",
                 backing="element register (ionisation energies)",
                 row_names=("element register: first ionisation energy, "
                            f"{len(ies)} elements",))


_P6 = ("Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg")


def _t_osmium() -> Built:
    dens = {e.symbol: str(e.density_g_per_cm3) for e in _els()
            if e.density_g_per_cm3 is not None}
    rows = {"density": dens,
            "weight": {s: str(_el(s).atomic_weight_u) for s in _P6}}
    vm = {s: F(rows["weight"][s]) / F(dens[s]) for s in _P6}
    top = max(dens, key=lambda s: F(dens[s]))
    vmin = min(vm, key=lambda s: vm[s])
    claims = {"densest": top, "min_volume": vmin,
              "vm": {s: rnd(vm[s], 3) for s in _P6},
              "mass_ratio": rnd(F(rows["weight"]["Ir"]) /
                                F(rows["weight"]["Os"]), 4),
              "volume_ratio": rnd(vm["Ir"] / vm["Os"], 4)}
    check = r'''
d, w = ROWS['density'], ROWS['weight']
ok = ok and max(d, key=lambda s: F(d[s])) == CLAIMS['densest'] == 'Os'
vm = {s: F(w[s]) / F(d[s]) for s in w}
ok = ok and min(vm, key=lambda s: vm[s]) == CLAIMS['min_volume'] == 'Os'
ok = ok and all(rd(vm[s], 3) == CLAIMS['vm'][s] for s in w)
ok = ok and rd(F(w['Ir']) / F(w['Os']), 4) == CLAIMS['mass_ratio']
ok = ok and rd(vm['Ir'] / vm['Os'], 4) == CLAIMS['volume_ratio']
'''
    derived = (
        "density is molar mass over molar volume, rho = M / V_m. In the "
        "register osmium is the densest of " + str(len(dens)) + " elements "
        "(22.57 g/cm^3), and in period 6 (Hf to Hg) it has the smallest "
        "molar volume: " + ", ".join(f"{s} {claims['vm'][s]}" for s in _P6)
        + " cm^3/mol. From Os to Ir the mass rises by a factor " +
        claims["mass_ratio"] + " but the molar volume by " +
        claims["volume_ratio"] + ", so the density falls; after Os the "
        "volume grows faster than the mass all the way to Hg")
    account = ("why the molar volume is least at osmium -- the filling of "
               "the 5d bonding states near half filling and the metallic "
               "bonding that follows -- is a band-structure account the "
               "register does not hold")
    return Built(derived, account, rows, claims, check, "volume_ratio",
                 key_row="density", row_mutation=_set(["density", "Os"], _alter),
                 column1="the density peak at osmium: "
                                            "mass against molar volume",
                 backing="element register (densities, atomic weights)",
                 row_names=("element register: densities and period-6 "
                            "atomic weights",))


def _t_fluorine() -> Built:
    ens = {e.symbol: str(e.electronegativity_pauling) for e in _els()
           if e.electronegativity_pauling is not None}
    f = _el("F")
    top = max(ens, key=lambda s: F(ens[s]))
    claims = {"top": top, "en": rnd(F(ens[top]), 2), "count": len(ens),
              "above_f": [s for s in ens if F(ens[s]) > F(ens["F"])],
              "o_in_of2": 2, "ie": rnd(f.ionization_energy_eV, 3),
              "ea": rnd(f.electron_affinity_eV, 3)}
    check = r'''
top = max(ROWS, key=lambda s: F(ROWS[s]))
ok = ok and top == CLAIMS['top'] == 'F' and rd(F(ROWS['F']), 2) == CLAIMS['en']
ok = ok and [s for s in ROWS if F(ROWS[s]) > F(ROWS['F'])] == CLAIMS['above_f'] == []
ok = ok and len(ROWS) == CLAIMS['count']
# OF2: F takes the electrons of both O-F bonds, O is +2
ok = ok and F(ROWS['F']) > F(ROWS['O']) and 2 * 1 == CLAIMS['o_in_of2']
'''
    derived = (
        "an oxidation state assigns each bond's electrons to the more "
        "electronegative partner. Fluorine's Pauling electronegativity, " +
        claims["en"] + ", is the largest of the " + str(claims["count"]) +
        " in the register and no element exceeds it, so in every compound "
        "fluorine takes the bonding electrons and is -1; only in F2 (equal "
        "partners) is it 0. The same rule gives oxygen +2 in OF2, since "
        "fluorine outranks oxygen. Fluorine's first ionisation energy is " +
        claims["ie"] + " eV and its electron affinity " + claims["ea"] +
        " eV")
    account = ("why fluorine's electronegativity is the largest -- its small "
               "radius, the high effective charge on its 2p shell and the "
               "absence of a low-lying d shell -- is an atomic-structure "
               "account; the register holds the value, not its cause")
    return Built(derived, account, ens, claims, check, "en", key_row="F",
                 column1="fluorine's single oxidation state from the "
                         "electronegativity order",
                 backing="element register (electronegativities)",
                 row_names=("element register: Pauling electronegativity, "
                            f"{len(ens)} elements",))


_G14 = ("C", "Si", "Ge", "Sn", "Pb")


def _t_group14() -> Built:
    rows = {s: {"valence": _el(s).valence_electrons,
                "ie": str(_el(s).ionization_energy_eV),
                "en": str(_el(s).electronegativity_pauling),
                "config": _el(s).electron_configuration} for s in _G14}
    claims = {"valence": 4, "ie": [rnd(F(rows[s]["ie"]), 3) for s in _G14],
              "inversion": "Pb"}
    check = r'''
ok = ok and all(ROWS[s]['valence'] == CLAIMS['valence'] for s in ROWS)
syms = ['C', 'Si', 'Ge', 'Sn', 'Pb']
ok = ok and [rd(F(ROWS[s]['ie']), 3) for s in syms] == CLAIMS['ie']
ups = [syms[i + 1] for i in range(4) if F(ROWS[syms[i + 1]]['ie']) > F(ROWS[syms[i]]['ie'])]
ok = ok and ups == [CLAIMS['inversion']]
for s in syms:
    ns = re.findall(r'(\d)s2', ROWS[s]['config']); np_ = re.findall(r'(\d)p2', ROWS[s]['config'])
    ok = ok and bool(ns) and bool(np_) and ns[-1] == np_[-1]
'''
    derived = (
        "the register confirms the premise: carbon, silicon, germanium, tin "
        "and lead each have 4 valence electrons (ns2 np2, derived from the "
        "register's configurations). Their first ionisation energies, " +
        ", ".join(f"{s} {v}" for s, v in zip(_G14, claims["ie"])) + " eV, "
        "fall down the group except from tin to lead, where they rise")
    account = ("the insulator-to-metal transition itself -- the band gap "
               "closing as the s-p bonding-antibonding splitting shrinks "
               "with bond length -- needs band gaps and band structures, "
               "which no register here holds")
    return Built(derived, account, rows, claims, check, "valence",
                 key_row="Sn", row_mutation=_set(["Sn", "ie"], _alter),
                 column1="group 14: what the register holds "
                                       "about the premise",
                 backing="element register (configurations, ionisation "
                         "energies)",
                 row_names=tuple(f"element {s}" for s in _G14))


def _t_gold_mercury() -> Built:
    au, hg = _el("Au"), _el("Hg")
    rows = {"Au": {"z": 79, "mp": str(au.melting_point_K),
                   "ie": str(au.ionization_energy_eV),
                   "state": au.standard_state},
            "Hg": {"z": 80, "mp": str(hg.melting_point_K),
                   "ie": str(hg.ionization_energy_eV),
                   "state": hg.standard_state},
            "alpha_inv": "137.035999084"}
    out = {}
    for s in ("Au", "Hg"):
        lo, hi = sqrt_bounds(1 - (rows[s]["z"] * ALPHA) ** 2)
        out[s] = (lo, hi)
    claims = {"Au": rnd(out["Au"][0], 4), "Hg": rnd(out["Hg"][0], 4),
              "v_over_c_Au": rnd(79 * ALPHA, 4),
              "hg_liquid": F(rows["Hg"]["mp"]) < F("273.15")}
    check = r'''
al = 1 / F(ROWS['alpha_inv'])
for s in ('Au', 'Hg'):
    lo, hi = sq_lo_hi(1 - (ROWS[s]['z'] * al) ** 2)
    ok = ok and rd(lo, 4) == rd(hi, 4) == CLAIMS[s]
ok = ok and rd(79 * al, 4) == CLAIMS['v_over_c_Au']
ok = ok and (F(ROWS['Hg']['mp']) < F('273.15')) == CLAIMS['hg_liquid'] == True
ok = ok and F(ROWS['Hg']['ie']) > F(ROWS['Au']['ie'])
'''
    derived = (
        "for a 1s electron v/c is about Z alpha: " + claims["v_over_c_Au"] +
        " for gold, so the relativistic factor sqrt(1 - (Z alpha)^2) is " +
        claims["Au"] + " for gold and " + claims["Hg"] + " for mercury -- "
        "the Bohr radius of the s shells shrinks by close to a fifth, and "
        "the outer 6s contracts and is stabilised with them. The register "
        "agrees with the consequences it can see: mercury melts at " +
        rnd(F(rows["Hg"]["mp"]), 2) + " K (below 273.15 K; its standard "
        "state is " + rows["Hg"]["state"] + "), and its first ionisation "
        "energy, " + rnd(F(rows["Hg"]["ie"]), 3) + " eV, exceeds gold's " +
        rnd(F(rows["Au"]["ie"]), 3) + " eV")
    account = ("how the contraction makes gold yellow (the 5d-6s gap moved "
               "into the visible) and mercury's bonding weak needs orbital "
               "energies from a relativistic calculation, which no register "
               "here holds")
    return Built(derived, account, rows, claims, check, "Au", key_row="Hg", row_mutation=_set(["Hg", "z"], _alter),
                 column1="the size of the relativistic contraction at Z = 79 "
                         "and 80",
                 backing="exact square-root enclosure + element register",
                 row_names=("element Au", "element Hg",
                            "CODATA 2018 fine-structure constant"))


def _t_technetium() -> Built:
    from ..data_objects import nuclides as N
    reg = N.register()
    rows = {}
    for nu in N.isotopes(43):
        A = nu.a
        if nu.estimated or nu.mass_excess_text is None:
            continue
        if all((z, A) in reg and reg[(z, A)].mass_excess_text
               for z in (42, 44)):
            rows[str(A)] = [reg[(42, A)].mass_excess_text,
                            nu.mass_excess_text,
                            reg[(44, A)].mass_excess_text]
    margins = {A: max(F(t) - F(m), F(t) - F(r))
               for A, (m, t, r) in rows.items()}
    weakest = min(margins, key=lambda A: margins[A])
    stable_tc = [nu.name for nu in N.isotopes(43) if nu.half_life == "stbl"]
    claims = {"count": len(rows), "all_heavier": all(v > 0 for v in
                                                     margins.values()),
              "weakest": weakest, "margin": rnd(margins[weakest], 1),
              "stable": stable_tc}
    check = r'''
mg = {A: max(F(t) - F(m), F(t) - F(r)) for A, (m, t, r) in ROWS.items()}
ok = ok and len(ROWS) == CLAIMS['count']
ok = ok and all(v > 0 for v in mg.values()) == CLAIMS['all_heavier'] == True
w = min(mg, key=lambda A: mg[A])
ok = ok and w == CLAIMS['weakest'] and rd(mg[w], 1) == CLAIMS['margin']
ok = ok and CLAIMS['stable'] == []
'''
    derived = (
        "every one of the " + str(claims["count"]) + " technetium isotopes "
        "whose mass AME2020 measured is heavier than its molybdenum isobar "
        "(so it can capture an electron) or its ruthenium isobar (so it can "
        "beta-decay): a decay is open for every one of them (" + LEAN_FILE +
        ", technetium_unstable). The narrowest margin is 99Tc -> 99Ru, " +
        claims["margin"] + " keV; NUBASE2020 prints no technetium ground "
        "state as stable")
    account = ("why the valley of stability skips Z = 43 -- Mattauch's isobar "
               "rule and the pairing term in the shell model -- is an account "
               "of the masses; the register gives the masses and the "
               "energetics they decide, not the cause")
    return Built(derived, account, rows, claims, check, "margin",
                 key_row="99", row_mutation=_set(["99", 1],
                                                 lambda v: str(F(v) - 1)),
                 column1="technetium: an open decay for every "
                                       "isotope, from the masses",
                 backing="nuclide register (AME2020, NUBASE2020) + Lean "
                         "certificate",
                 lean=("technetium_unstable",),
                 row_names=("AME2020 mass excesses of Mo, Tc, Ru isobars, "
                            f"{len(rows)} mass numbers",))


def _t_fluoride() -> Built:
    rows = {s: str(_el(s).atomic_weight_u) for s in ("Ta", "W", "F")}
    mt = F(rows["Ta"]) + 5 * F(rows["F"])
    mw = F(rows["W"]) + 6 * F(rows["F"])
    claims = {"TaF5": rnd(mt, 2), "WF6": rnd(mw, 2), "dipole_WF6": "0",
              "dipole_TaF5": "0"}
    check = r'''
ok = ok and rd(F(ROWS['Ta']) + 5 * F(ROWS['F']), 2) == CLAIMS['TaF5']
ok = ok and rd(F(ROWS['W']) + 6 * F(ROWS['F']), 2) == CLAIMS['WF6']
ok = ok and F(CLAIMS['WF6']) > F(CLAIMS['TaF5'])
# octahedral bonds: +-e_x, +-e_y, +-e_z sum to zero
v = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
ok = ok and all(sum(x[i] for x in v) == 0 for i in range(3)) and CLAIMS['dipole_WF6'] == '0'
# trigonal bipyramid: equatorial at 0, 120, 240 degrees (cos 1, -1/2, -1/2;
# sin 0, +r, -r) and axial +-e_z
cx = F(1) - F(1, 2) - F(1, 2)
ok = ok and cx == 0 and CLAIMS['dipole_TaF5'] == '0'
'''
    derived = (
        "from the register's atomic weights M(TaF5) = " + claims["TaF5"] +
        " g/mol and M(WF6) = " + claims["WF6"] + " g/mol: the heavier "
        "molecule is the more volatile (boiling at 17 C against TaF5 "
        "melting at 95 C, as the question gives), so molar mass does not "
        "decide the order. Nor does polarity: both monomers have zero "
        "dipole by symmetry (six octahedral bonds cancel; so do the three "
        "equatorial and two axial bonds of a trigonal bipyramid)")
    account = ("the account of the inversion -- WF6's six-coordinate metal "
               "is saturated while TaF5 completes its coordination by "
               "fluorine bridges and associates into oligomers in the "
               "condensed phase -- is structural chemistry no register here "
               "holds")
    return Built(derived, account, rows, claims, check, "WF6", key_row="W",
                 column1="TaF5 against WF6: mass and polarity ruled out",
                 backing="element register (atomic weights)",
                 row_names=("element Ta", "element W", "element F"))


def _t_lanthanide() -> Built:
    syms = {"Al": "3p", "Ga": "4p", "Zr": "5s", "Hf": "6s"}
    rows = {s: {"z": _el(s).z, "config": _el(s).electron_configuration,
                "ie": str(_el(s).ionization_energy_eV),
                "radius": str(_el(s).atomic_radius_pm)} for s in syms}
    z = {s: slater_zeff(rows[s]["z"], parse_configuration(rows[s]["config"]),
                        syms[s]) for s in syms}
    claims = {s: rnd(z[s], 2) for s in syms}
    check = r'''
CORE = {'He': 2, 'Ne': 10, 'Ar': 18, 'Kr': 36, 'Xe': 54, 'Rn': 86}
def fill(n):
    order = sorted([(a, b) for a in range(1, 8) for b in 'spdf' if 'spdf'.index(b) < a],
                   key=lambda t: (t[0] + 'spdf'.index(t[1]), t[0]))
    out = {}
    for a, b in order:
        if n <= 0: break
        k = min({'s': 2, 'p': 6, 'd': 10, 'f': 14}[b], n); out[str(a) + b] = k; n -= k
    return out
def occ(c):
    m = re.match(r'\[(\w+)\]', c); o = {}
    if m: o.update(fill(CORE[m.group(1)])); c = c[m.end():]
    for a, b, k in re.findall(r'(\d)([spdf])(\d+)', c):
        o[a + b] = o.get(a + b, 0) + int(k)
    return o
def zeff(Z, o, sh):
    n = int(sh[0]); sg = -F(35, 100)
    for k, v in o.items():
        m = int(k[0])
        if m == n and k[1] in 'sp': sg += F(35, 100) * v
        elif m == n - 1: sg += F(85, 100) * v
        elif m < n - 1: sg += v
    return Z - sg
for s, sh in (('Al', '3p'), ('Ga', '4p'), ('Zr', '5s'), ('Hf', '6s')):
    ok = ok and rd(zeff(ROWS[s]['z'], occ(ROWS[s]['config']), sh), 2) == CLAIMS[s]
ok = ok and F(ROWS['Ga']['ie']) > F(ROWS['Al']['ie']) and F(ROWS['Hf']['ie']) > F(ROWS['Zr']['ie'])
'''
    derived = (
        "Slater's rules, applied to the register's configurations, give the "
        "outer electron the same effective charge in zirconium (5s) and "
        "hafnium (6s): " + claims["Zr"] + " and " + claims["Hf"] + " -- the "
        "32 protons added between them are matched by the 4f and 5s5p5d "
        "electrons inserted under the valence shell. The same count across "
        "the 3d block gives aluminium (3p) " + claims["Al"] + " and gallium "
        "(4p) " + claims["Ga"] + ", so gallium's valence shell is held more "
        "tightly than aluminium's. The register's first ionisation energies "
        "show both: Ga " + rnd(F(rows["Ga"]["ie"]), 3) + " eV > Al " +
        rnd(F(rows["Al"]["ie"]), 3) + " eV, and Hf " +
        rnd(F(rows["Hf"]["ie"]), 3) + " eV > Zr " +
        rnd(F(rows["Zr"]["ie"]), 3) + " eV, although each is one shell "
        "further out. Slater's screening constants are empirical, and the "
        "register holds no ionic radii (its PubChem radii, Zr " +
        rnd(F(rows["Zr"]["radius"]), 0) + " and Hf " +
        rnd(F(rows["Hf"]["radius"]), 0) + " pm, are not the ionic radii the "
        "question quotes)")
    account = ("why 4f and 3d electrons screen poorly -- the shape of their "
               "radial distributions -- is an orbital account beyond "
               "Slater's counting")
    return Built(derived, account, rows, claims, check, "Hf", key_row="Hf", row_mutation=_set(["Hf", "z"], _alter),
                 column1="the lanthanide and 3d contractions in effective "
                         "charge",
                 backing="element register (configurations) + Slater's "
                         "rules",
                 row_names=tuple(f"element {s}" for s in syms))


def _t_actinide() -> Built:
    lan = [e for e in _els() if 57 <= e.z <= 71]
    act = [e for e in _els() if 89 <= e.z <= 103]
    rows = {e.symbol: [e.z, e.electron_configuration] for e in lan + act}
    dev_a = [e.symbol for e in act
             if parse_configuration(e.electron_configuration) != madelung(e.z)]
    dev_l = [e.symbol for e in lan
             if parse_configuration(e.electron_configuration) != madelung(e.z)]
    claims = {"actinides": dev_a, "lanthanides": dev_l}
    check = r'''
CORE = {'He': 2, 'Ne': 10, 'Ar': 18, 'Kr': 36, 'Xe': 54, 'Rn': 86}
def fill(n):
    order = sorted([(a, b) for a in range(1, 8) for b in 'spdf' if 'spdf'.index(b) < a],
                   key=lambda t: (t[0] + 'spdf'.index(t[1]), t[0]))
    out = {}
    for a, b in order:
        if n <= 0: break
        k = min({'s': 2, 'p': 6, 'd': 10, 'f': 14}[b], n); out[str(a) + b] = k; n -= k
    return out
def occ(c):
    c = c.replace('(predicted)', '')
    m = re.match(r'\s*\[(\w+)\]', c); o = {}
    if m: o.update(fill(CORE[m.group(1)])); c = c[m.end():]
    for a, b, k in re.findall(r'(\d)([spdf])(\d+)', c):
        o[a + b] = o.get(a + b, 0) + int(k)
    return {k: v for k, v in o.items() if v}
da = [s for s, (z, c) in ROWS.items() if 89 <= z <= 103 and occ(c) != fill(z)]
dl = [s for s, (z, c) in ROWS.items() if 57 <= z <= 71 and occ(c) != fill(z)]
ok = ok and da == CLAIMS['actinides'] and dl == CLAIMS['lanthanides']
ok = ok and len(da) == 6 and len(dl) == 3
'''
    derived = (
        "against the Madelung (n + l) filling, the register's ground-state "
        "configurations differ for " + str(len(dev_a)) + " of the 15 "
        "actinides (" + ", ".join(dev_a) + ") and " + str(len(dev_l)) +
        " of the 15 lanthanides (" + ", ".join(dev_l) + "): in the early "
        "actinides a 6d electron replaces a 5f one, so the order of the 5f "
        "and 6d levels changes inside the series -- the premise of any "
        "electron-counting rule, a fixed order of levels, fails twice as "
        "often in the 5f row as in the 4f row")
    account = ("the energetic account of the 5f, 6d, 7s and 7p shifts "
               "(relativistic stabilisation of 7s and 7p1/2, destabilisation "
               "of 5f and 6d) needs orbital energies no register here holds")
    return Built(derived, account, rows, claims, check, "actinides",
                 key_row="Pu", row_mutation=_set(["Pu", 1],
                                                 lambda v: "[Rn]7s2 5f5 6d1"),
                 column1="actinides against the Madelung "
                                      "filling",
                 backing="element register (configurations)",
                 row_names=("element register: configurations, La-Lu and "
                            "Ac-Lr",))


def _t_oganesson() -> Built:
    og = _el("Og")
    rows = {"Og": {"z": 118, "config": og.electron_configuration,
                   "state": og.standard_state,
                   "ie": _s(og.ionization_energy_eV),
                   "ea": _s(og.electron_affinity_eV)},
            "Xe": {"z": 54}, "alpha_inv": "137.035999084"}
    za2 = (118 * ALPHA) ** 2
    s1 = sqrt_bounds(1 - za2)[0]
    s3 = sqrt_bounds(4 - za2)[0]
    sx = sqrt_bounds(1 - (54 * ALPHA) ** 2)[0]
    claims = {"za2": rnd(za2, 4), "j12": rnd(s1, 3), "j32": rnd(s3, 3),
              "xe": rnd(sx, 3)}
    check = r'''
al = 1 / F(ROWS['alpha_inv'])
z2 = (ROWS['Og']['z'] * al) ** 2
ok = ok and rd(z2, 4) == CLAIMS['za2']
ok = ok and rd(sq_lo_hi(1 - z2)[0], 3) == CLAIMS['j12']
ok = ok and rd(sq_lo_hi(4 - z2)[0], 3) == CLAIMS['j32']
ok = ok and rd(sq_lo_hi(1 - (ROWS['Xe']['z'] * al) ** 2)[0], 3) == CLAIMS['xe']
ok = ok and ROWS['Og']['ie'] is None and '(predicted)' in ROWS['Og']['config']
'''
    derived = (
        "at Z = 118, (Z alpha)^2 = " + claims["za2"] + ". In the Dirac "
        "equation the radial exponent is sqrt(kappa^2 - (Z alpha)^2): for "
        "s1/2 and p1/2 (|kappa| = 1) it is " + claims["j12"] + " (xenon: " +
        claims["xe"] + "), for p3/2 (|kappa| = 2) it is " + claims["j32"] +
        " -- the 7p shell splits, and 7p1/2 contracts like an s shell while "
        "7p3/2 does not: the spin-orbit splitting is of the order of the "
        "shell spacing. The register has only a predicted configuration for "
        "oganesson (" + og.electron_configuration + ") and no measured "
        "ionisation energy, electron affinity or density")
    account = ("how the smeared shell structure makes oganesson polarisable, "
               "semiconducting and able to bind an electron needs "
               "relativistic many-electron calculations, which no register "
               "here holds")
    dispute = ("the element register (PubChem) records oganesson's standard "
               "state as '" + og.standard_state + "', not a semiconductor or "
               "metal at room temperature; the register does not decide "
               "between the two predictions")
    return Built(derived, account, rows, claims, check, "j12", key_row="Og", row_mutation=_set(["Og", "z"], _alter),
                 column1="the Dirac exponents at Z = 118",
                 backing="exact square-root enclosure + element register",
                 disputes=(dispute,) if og.standard_state ==
                 "Expected to be a Gas" else (),
                 row_names=("element Og", "CODATA 2018 fine-structure "
                                          "constant"))


def _t_deuteron() -> Built:
    from ..data_objects import nuclides as N
    rows = {"n": _me(0, 1), "1H": _me(1, 1), "2H": _me(1, 2),
            "2He": N.register().get((2, 2)) is not None,
            "2n": N.register().get((0, 2)) is not None}
    b = F(rows["n"]) + F(rows["1H"]) - F(rows["2H"])
    claims = {"B": rnd(b, 3), "channels": [[1, 0], [0, 1]],
              "absent": ["2He", "2n"]}
    check = r'''
b = F(ROWS['n']) + F(ROWS['1H']) - F(ROWS['2H'])
ok = ok and rd(b, 3) == CLAIMS['B'] and b > 0
ch = [[S, T] for S in (0, 1) for T in (0, 1) if (0 + S + T) % 2 == 1]
ok = ok and sorted(ch) == sorted(CLAIMS['channels'])
ok = ok and not ROWS['2He'] and not ROWS['2n'] and CLAIMS['absent'] == ['2He', '2n']
'''
    derived = (
        "from AME2020, B(2H) = Delta(n) + Delta(1H) - Delta(2H) = " +
        claims["B"] + " keV; neither table holds a ground state of 2He or "
        "of two neutrons. Two nucleons in an s-wave (L = 0) must be "
        "antisymmetric overall, (-1)^(L+S+T) = -1, which leaves exactly "
        "(S, T) = (1, 0) and (0, 1) (" + LEAN_FILE + ", "
        "nucleon_pair_channels). Two protons or two neutrons have T = 1, so "
        "the Pauli principle puts them in the spin singlet S = 0 "
        "(identical_pair_singlet): the spin-triplet channel the deuteron "
        "binds in is closed to them, before any Coulomb repulsion")
    account = ("why the singlet channel itself is just unbound -- the spin "
               "dependence of the nuclear force and the depth of its "
               "potential -- needs a nucleon-nucleon potential, not a "
               "register")
    return Built(derived, account, rows, claims, check, "B", key_row="2H",
                 column1="the deuteron's binding and the channels open to "
                         "pp and nn",
                 backing="nuclide register (AME2020) + Lean theorem",
                 lean=("nucleon_pair_channels", "identical_pair_singlet"),
                 row_names=("AME2020 n", "AME2020 1H", "AME2020 2H",
                            "AME2020/NUBASE2020: 2He, 2n (absent)"))


def _t_mirror() -> Built:
    rows = {"n": _me(0, 1), "1H": _me(1, 1), "11B": _me(5, 11),
            "11C": _me(6, 11), "alpha_inv": "137.035999084",
            "hbarc": "197.3269804"}
    db = (F(rows["11C"]) - F(rows["11B"])) + (F(rows["n"]) - F(rows["1H"]))
    ahc = HBARC / F(rows["alpha_inv"])
    c3 = cbrt_bounds(F(11))
    ec = F(3, 5) * ahc * (6 * 5 - 5 * 4) / (F(12, 10) * c3[0])
    r0 = F(3, 5) * ahc * 10 / (db / 1000 * c3[0])
    claims = {"dB": rnd(db, 3), "coulomb_r12": rnd(ec, 2),
              "r0_match": rnd(r0, 3)}
    check = r'''
db = (F(ROWS['11C']) - F(ROWS['11B'])) + (F(ROWS['n']) - F(ROWS['1H']))
ok = ok and rd(db, 3) == CLAIMS['dB']
ahc = F(ROWS['hbarc']) / F(ROWS['alpha_inv'])
c = cb_lo_hi(F(11))
e1 = F(3, 5) * ahc * 10 / (F(12, 10) * c[0]); e2 = F(3, 5) * ahc * 10 / (F(12, 10) * c[1])
ok = ok and rd(e1, 2) == rd(e2, 2) == CLAIMS['coulomb_r12']
r1 = F(3, 5) * ahc * 10 / (db / 1000 * c[0]); r2 = F(3, 5) * ahc * 10 / (db / 1000 * c[1])
ok = ok and rd(r1, 3) == rd(r2, 3) == CLAIMS['r0_match']
'''
    derived = (
        "from AME2020, B(11B) - B(11C) = (Delta(11C) - Delta(11B)) + "
        "(Delta(n) - Delta(1H)) = " + claims["dB"] + " keV. A uniformly "
        "charged sphere of radius r0 A^(1/3) has Coulomb energy (3/5) Z(Z-1) "
        "e^2/(4 pi eps0 R); the difference between Z = 6 and Z = 5 at "
        "A = 11, with e^2/(4 pi eps0) = hbar c alpha, is " +
        claims["coulomb_r12"] + " MeV at r0 = 1.2 fm and equals the measured "
        "gap at r0 = " + claims["r0_match"] + " fm: the gap is the Coulomb "
        "energy of the sixth proton, to the accuracy of the uniform-sphere "
        "picture")
    account = ("the remaining corrections (the exchange term, the "
               "electromagnetic spin-orbit term, the Thomas-Ehrman shift) "
               "are quantum-mechanical accounts no register here computes")
    return Built(derived, account, rows, claims, check, "dB", key_row="11C",
                 column1="the 11B-11C binding gap against the Coulomb "
                         "energy",
                 backing="nuclide register (AME2020) + exact cube-root "
                         "enclosure",
                 row_names=("AME2020 n", "AME2020 1H", "AME2020 11B",
                            "AME2020 11C", "CODATA 2018 alpha, hbar c"))


def _t_lead() -> Built:
    rows = {"n": _me(0, 1), "1H": _me(1, 1)}
    for a in (205, 206, 207, 208, 209):
        rows[f"{a}Pb"] = _me(82, a)

    def B(a: int) -> F:
        return 82 * F(rows["1H"]) + (a - 82) * F(rows["n"]) - \
            F(rows[f"{a}Pb"])
    ba = {a: B(a) / a for a in (206, 207, 208)}
    claims = {"BA": {str(a): rnd(ba[a], 2) for a in ba},
              "Sn208": rnd(B(208) - B(207), 1),
              "Sn209": rnd(B(209) - B(208), 1),
              "Sn209_full": rnd(B(209) - B(208), 3),
              "lowest_BA": "208"}
    check = r'''
def B(a):
    return 82 * F(ROWS['1H']) + (a - 82) * F(ROWS['n']) - F(ROWS[str(a) + 'Pb'])
ba = {a: B(a) / a for a in (206, 207, 208)}
ok = ok and all(rd(ba[a], 2) == CLAIMS['BA'][str(a)] for a in ba)
ok = ok and str(min(ba, key=lambda a: ba[a])) == CLAIMS['lowest_BA']
ok = ok and rd(B(208) - B(207), 1) == CLAIMS['Sn208'] and rd(B(209) - B(208), 1) == CLAIMS['Sn209']
ok = ok and rd(B(209) - B(208), 3) == CLAIMS['Sn209_full']
'''
    derived = (
        "lead-208 has Z = 82 and N = 126, both closed shells. AME2020 shows "
        "the closure where it is: the neutron separation energy falls from "
        "S_n(208Pb) = " + claims["Sn208"] + " keV to S_n(209Pb) = " +
        claims["Sn209"] + " keV (" + claims["Sn209_full"] + "), the 127th "
        "neutron being bound by about half as much as the 126th")
    account = ("the shell model's account of the closure and the neutron "
               "skin (the excess neutrons forming a surface layer, a radius "
               "difference no register here holds) are not derived")
    dispute = ("lead-208's binding energy per nucleon is not exceptionally "
               "high against its neighbours: AME2020 gives " +
               claims["BA"]["208"] + " keV for 208Pb, below 207Pb (" +
               claims["BA"]["207"] + ") and 206Pb (" + claims["BA"]["206"] +
               "); the shell closure shows in the separation energies")
    return Built(derived, account, rows, claims, check, "Sn209",
                 key_row="209Pb", column1="lead-208: where the shell closure "
                                          "shows in the masses",
                 backing="nuclide register (AME2020)",
                 disputes=(dispute,) if ba[208] < ba[207] else (),
                 row_names=("AME2020 n", "AME2020 1H",
                            "AME2020 205Pb-209Pb"))


def _t_be8() -> Built:
    from ..data_objects import nuclides as N
    rows = {"8Be": _me(4, 8), "4He": _me(2, 4),
            "8Be_half_life": N.nuclide(4, 8).half_life + " " +
            N.nuclide(4, 8).unit}
    q = F(rows["8Be"]) - 2 * F(rows["4He"])
    claims = {"Q": rnd(q, 3), "unbound": q > 0}
    check = r'''
q = F(ROWS['8Be']) - 2 * F(ROWS['4He'])
ok = ok and rd(q, 3) == CLAIMS['Q'] and (q > 0) == CLAIMS['unbound'] == True
'''
    derived = (
        "from AME2020, Q(8Be -> 2 alpha) = Delta(8Be) - 2 Delta(4He) = " +
        claims["Q"] + " keV > 0: the ground state of beryllium-8 lies above "
        "two separated alpha particles, so it is unbound and decays to "
        "them (" + LEAN_FILE + ", be8_unbound); NUBASE2020 gives its "
        "half-life as " + rows["8Be_half_life"])
    account = ("why two alpha particles do not bind -- the alpha particle's "
               "own saturation and the weakness of the residual force "
               "between two of them against their Coulomb repulsion -- is a "
               "cluster-model account, not a register value")
    return Built(derived, account, rows, claims, check, "Q", key_row="8Be",
                 column1="beryllium-8 against two alpha particles",
                 backing="nuclide register (AME2020, NUBASE2020) + Lean "
                         "certificate",
                 lean=("be8_unbound",),
                 row_names=("AME2020 8Be", "AME2020 4He",
                            "NUBASE2020 8Be half-life"))


def _t_double_beta() -> Built:
    rows = {"76Ge": _me(32, 76), "76Se": _me(34, 76)}
    q = F(rows["76Ge"]) - F(rows["76Se"])
    claims = {"Q": rnd(q, 3), "dL_2nu": 0, "dL_0nu": 2}
    check = r'''
q = F(ROWS['76Ge']) - F(ROWS['76Se'])
ok = ok and rd(q, 3) == CLAIMS['Q'] and q > 0
# lepton numbers: e- = +1, antineutrino = -1
ok = ok and 2 * (+1) + 2 * (-1) == CLAIMS['dL_2nu'] and 2 * (+1) == CLAIMS['dL_0nu']
'''
    derived = (
        "energy conservation (nuclear recoil neglected) gives T1 + T2 = Q - "
        "E(nu1) - E(nu2) for the summed kinetic energy of the two electrons. "
        "In two-neutrino decay the antineutrinos carry a varying share, so "
        "the summed spectrum is a continuum from 0 to Q; in neutrinoless "
        "decay nothing else carries energy, so it is a single line at Q. "
        "For 76Ge -> 76Se, AME2020 gives Q_bb = Delta(76Ge) - Delta(76Se) = " +
        claims["Q"] + " keV, where the line would sit. Counting lepton "
        "number (+1 per electron, -1 per antineutrino): 2nu-bb changes it by "
        "2 - 2 = 0, 0nu-bb by +2 -- a line at Q_bb is a process that "
        "violates lepton number by two units")
    return Built(derived, "", rows, claims, check, "Q", key_row="76Ge",
                 column1="the summed electron spectrum and lepton number in "
                         "double beta decay",
                 backing="nuclide register (AME2020)",
                 row_names=("AME2020 76Ge", "AME2020 76Se"))


def _t_gdr() -> Built:
    sj = -F(1, 3)
    gt = (F(2, 3) - 1) / 2
    claims = {"SJ": str(sj), "GT": str(gt)}
    check = r'''
R = F(1, 3)                         # R ~ A^(1/3)
sj = -R                              # omega ~ 1/R
gt = (2 * R - 1) / 2                 # omega ~ sqrt(k/m), k ~ R^2, m ~ A
ok = ok and str(sj) == CLAIMS['SJ'] == '-1/3' and str(gt) == CLAIMS['GT'] == '-1/6'
'''
    derived = (
        "in the liquid-drop picture the protons oscillate against the "
        "neutrons. With R = r0 A^(1/3): if the two fluids interpenetrate "
        "and the restoring force is a density wave inside a fixed sphere "
        "(Steinwedel-Jensen), the frequency goes as 1/R, i.e. as A^(-1/3); "
        "if two rigid spheres slide against each other and the restoring "
        "energy grows with the surface, k ~ R^2 against a mass ~ A "
        "(Goldhaber-Teller), the frequency goes as sqrt(A^(2/3)/A) = "
        "A^(-1/6). Measured resonances of heavy nuclei follow the "
        "A^(-1/3) law more closely")
    account = ("the microscopic origin of the restoring force (the symmetry "
               "energy) and which picture holds where are accounts, not "
               "derivations; the last sentence is quoted, not measured here")
    return Built(derived, account, {}, claims, check, "SJ",
                 column1="the mass-number scaling of the giant dipole "
                         "resonance",
                 backing="exponent arithmetic")


def _t_island() -> Built:
    from ..data_objects import nuclides as N
    fl = N.isotopes(114)
    rows = {nu.name: [nu.a, nu.half_life, nu.unit,
                      1 if nu.estimated else 0] for nu in fl}
    measured = [nu for nu in fl if nu.half_life and "#" not in nu.half_life
                and nu.half_life not in ("p-unst",)]
    top = max(measured, key=lambda nu: nu.a)
    claims = {"top": top.name, "N": top.a - 114, "short": 184 - (top.a - 114),
              "masses_measured": sum(1 for nu in fl if not nu.estimated)}
    check = r'''
m = [(v[0], k) for k, v in ROWS.items() if v[1] and '#' not in v[1] and v[1] != 'p-unst']
a, name = max(m)
ok = ok and name == CLAIMS['top'] and a - 114 == CLAIMS['N'] and 184 - (a - 114) == CLAIMS['short']
ok = ok and sum(1 for v in ROWS.values() if not v[3]) == CLAIMS['masses_measured']
'''
    derived = (
        "NUBASE2020 holds " + str(len(fl)) + " isotopes of element 114; the "
        "most neutron-rich with a measured half-life is " + top.name +
        " (" + top.half_life + " " + top.unit + "), N = " + str(claims["N"]) +
        ", " + str(claims["short"]) + " neutrons short of N = 184, and "
        "AME2020 has a measured mass for " + str(claims["masses_measured"]) +
        " of them: the predicted island lies beyond every nucleus the "
        "tables measure")
    account = ("how shell-correction energies raise the fission barrier "
               "where the liquid-drop barrier vanishes needs a "
               "Strutinsky-type calculation, which nothing here performs")
    return Built(derived, account, rows, claims, check, "N",
                 key_row=top.name, column1="element 114: how far the "
                                           "measured nuclei reach",
                 backing="nuclide register (NUBASE2020, AME2020)",
                 row_names=("NUBASE2020 isotopes of Z = 114",))


def _t_s_r() -> Built:
    from ..data_objects import nuclides as N
    path, rows = s_process()
    sn = [nu.a for nu in N.isotopes(50) if _node(50, nu.a) and
          _node(50, nu.a)[0]]
    iso = {}
    for a in sn:
        for z in range(44, 50):
            nd = _node(z, a)
            iso[f"{z},{a}"] = None if nd is None else nd[0]
    on_s = sorted({a for z, a in path if z == 50 and a in sn})
    first = next(i for i, (z, a) in enumerate(path) if z == 50)
    last = max(i for i, (z, a) in enumerate(path) if z == 50)

    def nm(i: int) -> str:
        return _nname(*path[i])
    entry = " -> ".join(nm(i) for i in range(max(0, first - 2), first + 1))
    exit_t = N.nuclide(*path[last])
    cls = {}
    for a in sn:
        shielded = any(iso.get(f"{z},{a}") for z in range(44, 50))
        s = a in on_s
        r = not shielded
        cls[str(a)] = ("s+r" if s and r else "s-only" if s else
                       "r-only" if r else "p-only")
    claims = {"on_s": on_s, "classes": cls,
              "path_len": len(path)}
    rows_all = {"path_nodes": rows, "isobars": iso, "stable_sn": sn,
                "capture_years": CAPTURE_YEARS, "stable_years": STABLE_YEARS}
    check = r'''
Y = F(3652422, 10000) * 86400
P, I = ROWS['path_nodes'], ROWS['isobars']
z, a, n = 26, 56, 1
seen = []
while z <= 52 and ('%d,%d' % (z, a)) in P:
    st, t, bm = P['%d,%d' % (z, a)]
    seen.append((z, a))
    if st or t is None or F(t) > ROWS['capture_years'] * Y: a += 1
    elif bm: z += 1
    else: z -= 1
    n += 1
ok = ok and n == CLAIMS['path_len']
on = sorted({a for z, a in seen if z == 50 and a in ROWS['stable_sn']})
ok = ok and on == CLAIMS['on_s']
for a in ROWS['stable_sn']:
    sh = any(I.get('%d,%d' % (z, a)) for z in range(44, 50))
    s, r = a in on, not sh
    c = 's+r' if s and r else 's-only' if s else 'r-only' if r else 'p-only'
    ok = ok and CLAIMS['classes'][str(a)] == c
ok = ok and CLAIMS['classes'].get('124') == 'r-only' and CLAIMS['classes'].get('112') == 'p-only'
'''
    derived = (
        "the s-process path read from NUBASE2020 half-lives (start at 56Fe; "
        "capture while a nucleus is stable or lives longer than a year, "
        "beta-decay when it lives less) enters tin through " + entry +
        " and leaves it at " + exit_t.name + " (" + exit_t.half_life + " " +
        exit_t.unit + ") for antimony, so the s-process makes the stable "
        "tin isotopes " + ", ".join(str(a) for a in on_s) +
        ". The r-process makes the stable isobars its beta-decay chains "
        "reach first from the neutron-rich side: a tin isotope is shielded "
        "when a lighter-Z isobar is stable. Result for the stable tin "
        "isotopes: " + "; ".join(f"Sn-{a}: {c}" for a, c in cls.items()) +
        ". So Sn-124 is r-only (124Sn is beyond 121Sn, where the s-path "
        "leaves, and nothing shields it), and Sn-112 is p-only, bypassed by "
        "both (112Cd shields it from the r-chains and the s-path never "
        "reaches it)")
    account = ("the astrophysical conditions (neutron densities near 10^8 "
               "per cm^3 at about 3 x 10^8 K for the s-process, above 10^20 "
               "per cm^3 for the r-process) are quoted, not derived; the "
               "one-year capture time is the reading's declared parameter")
    return Built(derived, account, rows_all, claims, check, "classes",
                 key_row="isobars", row_mutation=_set(["isobars", "48,124"],
                                                      lambda v: 1),
                 column1="the tin isotopes classified by "
                                            "the s-path and r-shielding",
                 backing="nuclide register (NUBASE2020 half-lives and decay "
                         "modes)",
                 row_names=(f"NUBASE2020: {len(rows)} nuclei on the s-path "
                            "from 56Fe", "NUBASE2020: isobars of the stable "
                                         "tin isotopes, Z = 44-49"))


def _t_lithium() -> Built:
    from ..data_objects import nuclides as N
    rows = {"7Be": _me(4, 7), "7Li": _me(3, 7),
            "t_half_s": str(N.half_life_seconds(4, 7)),
            "t_half": N.nuclide(4, 7).half_life + " " + N.nuclide(4, 7).unit}
    q = F(rows["7Be"]) - F(rows["7Li"])
    claims = {"Q": rnd(q, 3), "t_s": rows["t_half_s"]}
    check = r'''
q = F(ROWS['7Be']) - F(ROWS['7Li'])
ok = ok and rd(q, 3) == CLAIMS['Q'] and q > 0
ok = ok and F(ROWS['t_half_s']) == F(5322, 100) * 86400 == F(CLAIMS['t_s'])
'''
    derived = (
        "primordial lithium-7 is made mostly as beryllium-7 (3He + 4He -> "
        "7Be + gamma) and becomes lithium-7 by electron capture: AME2020 "
        "gives Q_EC = Delta(7Be) - Delta(7Li) = " + claims["Q"] + " keV, and "
        "NUBASE2020 a half-life of " + rows["t_half"] + " (" +
        rows["t_half_s"] + " s), far longer than the minutes of "
        "nucleosynthesis: beryllium-7 survives it and decays afterwards, "
        "so the predicted lithium-7 is set by the 7Be produced")
    account = ("the size of the mismatch and the hypotheses that would "
               "remove it (nuclear rates, stellar depletion, new physics) "
               "are accounts and observations no register here holds")
    return Built(derived, account, rows, claims, check, "Q", key_row="7Be",
                 column1="the beryllium-7 route to primordial lithium-7",
                 backing="nuclide register (AME2020, NUBASE2020)",
                 row_names=("AME2020 7Be", "AME2020 7Li",
                            "NUBASE2020 7Be half-life"))


def _t_hoyle() -> Built:
    rows = {"4He": _me(2, 4), "12C": _me(6, 12), "8Be": _me(4, 8),
            "hoyle_keV": "7654.07", "kB_eV_per_K": str(K_B / Q_E)}
    thr = 3 * F(rows["4He"]) - F(rows["12C"])
    be = F(rows["8Be"]) - 2 * F(rows["4He"])
    er = F(rows["hoyle_keV"]) - thr
    kt = F(rows["kB_eV_per_K"]) * 10 ** 8 / 1000          # keV at 1e8 K
    claims = {"threshold": rnd(thr, 2), "threshold_full": rnd(thr, 4),
              "be_alpha": rnd(thr - be, 2), "E_R": rnd(er, 2),
              "kT": rnd(kt, 3), "slope": rnd(1 / kt, 4)}
    check = r'''
thr = 3 * F(ROWS['4He']) - F(ROWS['12C'])
ok = ok and rd(thr, 2) == CLAIMS['threshold'] and rd(thr, 4) == CLAIMS['threshold_full']
be = F(ROWS['8Be']) - 2 * F(ROWS['4He'])
ok = ok and rd(thr - be, 2) == CLAIMS['be_alpha']
er = F(ROWS['hoyle_keV']) - thr
ok = ok and rd(er, 2) == CLAIMS['E_R']
kt = F(ROWS['kB_eV_per_K']) * 10 ** 8 / 1000
ok = ok and rd(kt, 3) == CLAIMS['kT'] and rd(1 / kt, 4) == CLAIMS['slope']
'''
    derived = (
        "from AME2020 the three-alpha threshold in carbon-12 is 3 Delta(4He) "
        "- Delta(12C) = " + claims["threshold"] + " keV (" +
        claims["threshold_full"] + "), and 8Be + alpha lies at " +
        claims["be_alpha"] + " keV. The Hoyle state, at 7654.07 keV (quoted "
        "from the level tables; no register here holds excited states), "
        "therefore sits " + claims["E_R"] + " keV above three alphas: a "
        "resonance the colliding 8Be + alpha can enter at stellar energies. "
        "A resonant rate goes as exp(-E_R/kT); at 10^8 K, kT = " +
        claims["kT"] + " keV, so d ln(rate)/dE_R = -1/kT = -" +
        claims["slope"] + " per keV: every keV the level moves changes the "
        "carbon yield by about 12 per cent")
    account = ("how a few-percent change in the strong force moves the Hoyle "
               "level needs a nuclear structure calculation, which nothing "
               "here performs")
    return Built(derived, account, rows, claims, check, "threshold",
                 key_row="4He", column1="the Hoyle resonance against the "
                                        "three-alpha threshold",
                 backing="nuclide register (AME2020)",
                 row_names=("AME2020 4He", "AME2020 12C", "AME2020 8Be",
                            "Hoyle state energy (quoted)",
                            "SI 2019 k_B and e"))


def _ps():
    from . import proof_search as P
    return P


def _t_material() -> Built:
    P = _ps()
    tt = [[p, q, (not p) or q, (not p) or q] for p in (False, True)
          for q in (False, True)]
    v = P.decide([], P.parse_formula("(p -> q) <-> (~p | q)"))
    claims = {"kind": v.kind, "table": tt, "strict": "fails",
              "model": {"w0": [0, 0], "w1": [1, 0]}}
    check = r'''
for p, q, a, b in CLAIMS['table']:
    ok = ok and a == ((not p) or q) and b == ((not p) or q) and a == b
ok = ok and len(CLAIMS['table']) == 4
ok = ok and CLAIMS['kind'] == 'classical'
w0, w1 = CLAIMS['model']['w0'], CLAIMS['model']['w1']
material = (not w0[0]) or w0[1]
strict = all((not w[0]) or w[1] for w in (w0, w1))
ok = ok and material and not strict and CLAIMS['strict'] == 'fails'
'''
    derived = (
        "P -> Q and ~P | Q agree on all four rows of the truth table, and a "
        "false antecedent makes P -> Q true whatever Q is; the equivalence "
        "is a classical tautology but not an intuitionistic one (the "
        "machine's prover: " + v.kind + "). Strict implication asks P -> Q "
        "at every accessible world: in the two-world model w0 (P false, Q "
        "false), w1 (P true, Q false), material implication holds at w0 and "
        "strict implication fails (" + LEAN_FILE + ", "
        "strict_implication_fails) -- the moon-and-Paris conditional is "
        "materially true and strictly false")
    account = ("the philosophical case against material implication as a "
               "model of natural-language 'if', and relevant logic's "
               "variable-sharing requirement, are accounts, not "
               "derivations")
    return Built(derived, account, {}, claims, check, "strict",
                 column1="material against strict implication",
                 backing="reasoning.proof_search + Lean theorem",
                 lean=("strict_implication_fails",))


def _t_soundness() -> Built:
    P = _ps()
    lem = P.decide([], P.parse_formula("p | ~p"))
    g4 = P.prove_intuitionistic([], P.parse_formula("p | ~p"))
    claims = {"lem_kind": lem.kind, "g4ip_proves_lem": g4 is not None,
              "lem_tautology": P.truth_table([], P.parse_formula("p | ~p"))
              is None, "verdict": "sound but not complete"}
    check = r'''
ok = ok and all((not p) or True for p in (False, True))
ok = ok and all((p or (not p)) for p in (False, True)) == CLAIMS['lem_tautology'] == True
ok = ok and CLAIMS['g4ip_proves_lem'] is False and CLAIMS['lem_kind'] == 'classical'
ok = ok and CLAIMS['verdict'] == 'sound but not complete'
'''
    derived = (
        "soundness is: every provable formula is valid; completeness: every "
        "valid formula is provable. The machine's own prover gives an "
        "example of the first without the second: the intuitionistic "
        "calculus G4ip is sound for classical truth tables (every rule is "
        "proved sound in RequestProject/GLM/Derivations.lean) but p | ~p, a "
        "classical tautology, has no G4ip proof -- read as a calculus for "
        "classical logic it is sound but not complete. The opposite, "
        "complete but unsound, is the calculus that proves every formula")
    account = ("why full second-order logic with standard semantics has no "
               "complete proof system (it would follow from Goedel's "
               "incompleteness theorem, which is not in the Lean "
               "development) is not derived")
    return Built(derived, account, {}, claims, check, "verdict",
                 column1="soundness against completeness, with the "
                         "machine's prover as the example",
                 backing="reasoning.proof_search")


def _t_intuitionistic() -> Built:
    P = _ps()
    lem = P.decide([], P.parse_formula("p | ~p"))
    dne = P.decide([], P.parse_formula("~~p -> p"))
    nnl = P.decide([], P.parse_formula("~~(p | ~p)"))
    claims = {"lem": lem.kind, "dne": dne.kind, "nn_lem": nnl.kind,
              "chain": {"em": [1, 1], "dne": [2, 1]}}
    check = r'''
ok = ok and CLAIMS['lem'] == 'classical' and CLAIMS['dne'] == 'classical' and CLAIMS['nn_lem'] == 'intuitionistic'
# the three-element chain 0 < 1 < 2: a -> b = 2 if a <= b else b; ~a = a -> 0
imp = lambda a, b: 2 if a <= b else b
neg = lambda a: imp(a, 0)
a = 1
ok = ok and max(a, neg(a)) == CLAIMS['chain']['em'][0] and max(a, neg(a)) != 2
ok = ok and imp(neg(neg(a)), a) == CLAIMS['chain']['dne'][1] and imp(neg(neg(a)), a) != 2
ok = ok and all(neg(neg(max(x, neg(x)))) == 2 for x in (0, 1, 2))
'''
    derived = (
        "the machine's prover (G4ip, complete for intuitionistic "
        "propositional logic) finds no constructive proof of p | ~p (" +
        lem.kind + ": a Kripke model refutes it) nor of ~~p -> p (" +
        dne.kind + "), and does find one of ~~(p | ~p) (" + nnl.kind +
        "). In the three-element Heyting chain 0 < a < 1 the middle element "
        "has a | ~a = a, not 1, and ~~a -> a = a, not 1, while ~~(x | ~x) = "
        "1 for every x (" + LEAN_FILE + ", chain_em_fails, chain_dne_fails, "
        "chain_nn_em)")
    account = ("the philosophical underpinning -- truth as provability, and "
               "a disjunction asserted only with a proof of one side -- is "
               "an account, not a derivation")
    return Built(derived, account, {}, claims, check, "nn_lem",
                 column1="excluded middle and double negation, "
                         "intuitionistically",
                 backing="reasoning.proof_search + Lean theorem",
                 lean=("chain_em_fails", "chain_dne_fails", "chain_nn_em"))


def _t_skolem() -> Built:
    claims = {"statement": "countable elementary substructure",
              "card": "aleph0"}
    check = r'''
ok = ok and CLAIMS['statement'] == 'countable elementary substructure' and CLAIMS['card'] == 'aleph0'
'''
    derived = (
        "downward Loewenheim-Skolem: every infinite structure in a countable "
        "language has a countable elementary substructure (" + LEAN_FILE +
        ", countable_elementary_substructure, from Mathlib's "
        "exists_elementarySubstructure_card_eq). So if ZFC, a countable "
        "first-order theory, has a model, it has a countable one; the "
        "sentence 'some set is uncountable' holds there because it is "
        "elementary")
    account = ("the resolution -- 'uncountable' inside the model means no "
               "bijection with omega exists in the model, which is "
               "consistent with one existing outside it -- is an account of "
               "relativised notions; the Lean development does not formalise "
               "ZFC's models")
    return Built(derived, account, {}, claims, check, "statement",
                 column1="the Skolem paradox: the theorem it rests on",
                 backing="Lean theorem (Mathlib)",
                 lean=("countable_elementary_substructure",))


def _t_fuzzy() -> Built:
    a = F(7, 10)
    claims = {"fuzzy_and": str(min(a, a)), "fuzzy_or": str(max(a, a)),
              "fuzzy_a_not_a": str(min(a, 1 - a)),
              "prob_and": [str(max(F(0), a + a - 1)), str(min(a, a))],
              "prob_or": [str(max(a, a)), str(min(F(1), a + a))],
              "prob_a_not_a": "0"}
    check = r'''
a = F(7, 10)
ok = ok and F(CLAIMS['fuzzy_and']) == min(a, a) and F(CLAIMS['fuzzy_a_not_a']) == min(a, 1 - a)
ok = ok and [F(x) for x in CLAIMS['prob_and']] == [F(2, 5), F(7, 10)]
ok = ok and [F(x) for x in CLAIMS['prob_or']] == [F(7, 10), F(1)]
# both ends attained: cells (AB, A~B, ~AB, ~A~B)
for p in ([F(7, 10), 0, 0, F(3, 10)], [F(2, 5), F(3, 10), F(3, 10), 0]):
    ok = ok and sum(p) == 1 and p[0] + p[1] == a and p[0] + p[2] == a
ok = ok and CLAIMS['prob_a_not_a'] == '0'
'''
    derived = (
        "fuzzy logic is truth-functional: with membership 7/10, 'A and B' "
        "is min = " + claims["fuzzy_and"] + ", 'A or B' max = " +
        claims["fuzzy_or"] + ", and even 'A and not A' is min(7/10, 3/10) = "
        + claims["fuzzy_a_not_a"] + ". Probability is not: with P(A) = P(B) "
        "= 7/10, P(A and B) can be anything in [2/5, 7/10] and P(A or B) "
        "anything in [7/10, 1] (Frechet; both ends attained), and P(A and "
        "not A) = 0 always (" + LEAN_FILE + ", frechet_lower, "
        "not_truth_functional)")
    account = ("the semantic difference itself -- degree of truth of a vague "
               "predicate against uncertainty about a crisp one -- is an "
               "account, not a derivation")
    return Built(derived, account, {}, claims, check, "prob_and",
                 column1="fuzzy against probabilistic conjunction",
                 backing="exact rationals + Lean theorem",
                 lean=("frechet_lower", "not_truth_functional"))


def _t_godel() -> Built:
    P = _ps()
    v = P.decide([P.parse_formula("false")], P.parse_formula("c"))
    claims = {"explosion": v.kind, "verdict": "proves every sentence"}
    check = r'''
ok = ok and CLAIMS['explosion'] == 'intuitionistic'
# truth table: false |- c is valid (no valuation makes the premise true)
ok = ok and all(not False or c for c in (False, True))
ok = ok and CLAIMS['verdict'] == 'proves every sentence'
'''
    derived = (
        "an inconsistent theory proves every sentence: false |- C has a "
        "proof (the machine's prover: " + v.kind + "), and semantically a "
        "first-order theory with no model entails every sentence (" +
        LEAN_FILE + ", inconsistent_proves_all). So 'T proves Con(T)' "
        "cannot certify T: every inconsistent T proves it too, and by "
        "Goedel's second theorem no consistent T of the required strength "
        "does -- a theory announcing its own consistency is either "
        "inconsistent or not that strong")
    account = ("the mechanics of Con(PA) -- the arithmetisation of syntax "
               "and the derivability conditions behind the second theorem "
               "-- are not in the Lean development and are not derived")
    return Built(derived, account, {}, claims, check, "verdict",
                 column1="why a proof of one's own consistency certifies "
                         "nothing",
                 backing="reasoning.proof_search + Lean theorem",
                 lean=("inconsistent_proves_all",))


def _t_lindstrom() -> Built:
    claims = {"loses": "compactness"}
    check = r'''
ok = ok and CLAIMS['loses'] == 'compactness'
'''
    derived = (
        "first-order logic has compactness (Mathlib: "
        "isSatisfiable_iff_isFinitelySatisfiable) and the downward "
        "Loewenheim-Skolem property (Mathlib: "
        "exists_elementarySubstructure_card_eq), and so a first-order "
        "theory with arbitrarily large finite models has an infinite one "
        "(RequestProject/GLM/DerivationsTwo.lean, "
        "infinite_model_of_large_finite_models): 'the domain is finite' is "
        "not first-order. A logic that can say it -- second-order logic, or "
        "L_{omega_1, omega} with its countable disjunctions -- therefore "
        "loses compactness, and second-order logic also loses downward "
        "Loewenheim-Skolem, since it can pin down the reals up to "
        "isomorphism")
    account = ("Lindstroem's theorem itself -- that no proper extension "
               "keeps both properties -- is not in the Lean development and "
               "is not derived")
    return Built(derived, account, {}, claims, check, "loses",
                 column1="what extending first-order logic costs",
                 backing="Lean theorems (Mathlib, DerivationsTwo.lean)",
                 lean=("infinite_model_of_large_finite_models",))


def _cstr_F(y: F, p: Dict[str, F]) -> Tuple[F, F]:
    r = p["Da0"] * y * y / (1 - y)
    lo, hi = ln_bounds(r)
    T_hi, T_lo = p["ER"] / lo, p["ER"] / hi
    k = 1 + p["kappa"]
    return (k * (T_lo - p["T0"]) - p["J"] * (1 - y),
            k * (T_hi - p["T0"]) - p["J"] * (1 - y))


def _t_cstr() -> Built:
    p = {"Da0": F(10 ** 10), "ER": F(8000), "T0": F(300), "J": F(250),
         "kappa": F(1)}
    ys = [F(1, 10), F(2, 5), F(4, 5), F(99, 100)]
    signs = []
    for y in ys:
        lo, hi = _cstr_F(y, p)
        signs.append(1 if lo > 0 else -1 if hi < 0 else 0)
    changes = sum(1 for i in range(3) if signs[i] * signs[i + 1] < 0)
    claims = {"params": {k: str(v) for k, v in p.items()},
              "points": [str(y) for y in ys], "signs": signs,
              "changes": changes}
    check = r'''
p = {k: F(v) for k, v in CLAIMS['params'].items()}
sg = []
for y in CLAIMS['points']:
    y = F(y)
    r = p['Da0'] * y * y / (1 - y)
    lo, hi = ln_lo_hi(r)
    k = 1 + p['kappa']
    a = k * (p['ER'] / hi - p['T0']) - p['J'] * (1 - y)
    b = k * (p['ER'] / lo - p['T0']) - p['J'] * (1 - y)
    sg.append(1 if a > 0 else -1 if b < 0 else 0)
ok = ok and sg == CLAIMS['signs'] and 0 not in sg
ok = ok and sum(1 for i in range(3) if sg[i] * sg[i + 1] < 0) == CLAIMS['changes'] == 3
'''
    derived = (
        "steady state, with rate r = k(T) C_A^2 per volume (2 A consumed "
        "per B), k(T) = k0 exp(-E/RT): material, 0 = q (C_A0 - C_A) - 2 V "
        "k(T) C_A^2; energy, 0 = rho c_p q (T0 - T) + (-dH) V k(T) C_A^2 - "
        "U A (T - T_c). With y = C_A/C_A0, Da0 = 2 V k0 C_A0/q, J = (-dH) "
        "C_A0/(2 rho c_p) and kappa = U A/(rho c_p q), T_c = T0: the "
        "material balance gives T(y) = (E/R)/ln(Da0 y^2/(1 - y)) and the "
        "energy balance becomes F(y) = (1 + kappa)(T(y) - T0) - J (1 - y) = "
        "0 -- heat removed against heat generated, an S-shaped generation "
        "curve against a straight removal line, which can cross it three "
        "times. Instance Da0 = 10^10, E/R = 8000 K, T0 = 300 K, J = 250 K, "
        "kappa = 1: F has signs " + str(signs) + " at y = 1/10, 2/5, 4/5, "
        "99/100 (each enclosed exactly, logarithms by rational bounds), so "
        "at least three steady states lie in the three intervals between "
        "them -- the low-conversion (extinguished), middle and "
        "high-conversion (ignited) states")
    account = ("the stability of each state (the middle one unstable, from "
               "the slopes at the crossings) and the ignition and extinction "
               "turning points as parameters move are a phase-portrait "
               "account; the slopes are not certified here")
    return Built(derived, account, {}, claims, check, "changes",
                 column1="a non-isothermal CSTR: the balances and a certified "
                         "case of multiplicity",
                 backing="exact logarithm enclosures")


def _mpc_solve() -> Tuple[Tuple[F, F], F, List[Tuple[F, F, F]]]:
    """Exact active-set enumeration of min (u0-3)^2 + (u0+u1-3)^2 over
    the box |u| <= 2 (a convex QP: the least feasible stationary point of
    a face is the optimum)."""
    lo, hi = F(-2), F(2)
    cands = []
    for f0 in ("free", lo, hi):
        for f1 in ("free", lo, hi):
            if f0 == "free" and f1 == "free":
                u0, u1 = F(3), F(0)
            elif f0 == "free":
                u1 = f1
                u0 = (6 - u1) / 2           # d/du0 = 2(u0-3) + 2(u0+u1-3)
            elif f1 == "free":
                u0 = f0
                u1 = 3 - u0
            else:
                u0, u1 = f0, f1
            if lo <= u0 <= hi and lo <= u1 <= hi:
                cands.append((u0, u1, (u0 - 3) ** 2 + (u0 + u1 - 3) ** 2))
    best = min(cands, key=lambda c: c[2])
    return (best[0], best[1]), best[2], cands


def _t_mpc() -> Built:
    (u0, u1), j, _ = _mpc_solve()
    claims = {"u0": str(u0), "u1": str(u1), "J": str(j),
              "clipped": ["2", "0"], "J_clipped": "2"}
    check = r'''
u, v = F(CLAIMS['u0']), F(CLAIMS['u1'])
J = lambda a, b: (a - 3) ** 2 + (a + b - 3) ** 2
ok = ok and -2 <= u <= 2 and -2 <= v <= 2 and J(u, v) == F(CLAIMS['J'])
# KKT for the convex cost: gradient (2(u-3) + 2(u+v-3), 2(u+v-3)); a free
# coordinate needs a zero component, one at its upper bound a non-positive one
g0, g1 = 2 * (u - 3) + 2 * (u + v - 3), 2 * (u + v - 3)
ok = ok and ((-2 < u < 2 and g0 == 0) or (u == 2 and g0 <= 0) or (u == -2 and g0 >= 0))
ok = ok and ((-2 < v < 2 and g1 == 0) or (v == 2 and g1 <= 0) or (v == -2 and g1 >= 0))
grid = [F(k, 10) for k in range(-20, 21)]
ok = ok and min(J(a, b) for a in grid for b in grid) == J(u, v)
cu, cv = [F(x) for x in CLAIMS['clipped']]
ok = ok and J(cu, cv) == F(CLAIMS['J_clipped']) > J(u, v)
'''
    derived = (
        "linear MPC solves at every sample k: minimise J = sum_{i=1}^{P} "
        "(y(k+i|k) - r(k+i))^T Q (y(k+i|k) - r(k+i)) + sum_{j=0}^{M-1} "
        "du(k+j)^T R du(k+j) over the moves du(k), ..., du(k+M-1), subject "
        "to the model's predictions, u_min <= u(k+j) <= u_max (valve "
        "saturation), du_min <= du(k+j) <= du_max, y_min <= y(k+i|k) <= "
        "y_max, and u held after the control horizon M; Q weights the "
        "tracking error, R suppresses moves; the first move is applied and "
        "the problem re-solved (receding horizon). A PID meets a limit by "
        "clipping its output after the fact; MPC puts the limit inside the "
        "optimisation. Instance: y(k+1) = y(k) + u(k), y(0) = 0, r = 3, "
        "P = M = 2, Q = 1, R = 0, |u| <= 2. The unconstrained optimum is "
        "(3, 0); clipped to (2, 0) it costs 2; the constrained optimum, by "
        "exact active-set enumeration, is u0 = " + claims["u0"] + ", u1 = " +
        claims["u1"] + " with cost " + claims["J"] + " (" + LEAN_FILE +
        ", mpc_instance_optimal, mpc_clipped_worse): the optimiser moves "
        "the second input to make up for the saturated first")
    account = ("the comparison with cascade control and the practice of "
               "tuning Q, R, P and M are accounts of engineering practice, "
               "not derivations")
    return Built(derived, account, {}, claims, check, "u1",
                 column1="MPC: the cost function and a constrained step "
                         "solved exactly",
                 backing="exact active-set enumeration + Lean theorem",
                 lean=("mpc_instance_optimal", "mpc_clipped_worse"))


def _t_tarski() -> Built:
    from . import integer_decision as ID
    rows = {"NODE_LIMIT": ID.NODE_LIMIT}
    claims = {"candidates": ["1", "-1", "2", "-2"], "rational_root": False,
              "sign_change": ["1", "2"], "node_limit": ID.NODE_LIMIT}
    check = r'''
ok = ok and all(F(c) ** 2 != 2 for c in CLAIMS['candidates']) and CLAIMS['rational_root'] is False
a, b = [F(x) for x in CLAIMS['sign_change']]
ok = ok and a * a - 2 < 0 < b * b - 2
ok = ok and ROWS['NODE_LIMIT'] == CLAIMS['node_limit']
'''
    derived = (
        "Tarski-Seidenberg decides the first-order theory of the real field, "
        "and its answers do not transfer to Q or Z: x^2 = 2 has a real "
        "solution (x^2 - 2 changes sign between 1 and 2) and no rational one "
        "(by the rational root test the only candidates are +-1, +-2, and "
        "none works) (" + LEAN_FILE + ", real_root_no_rational_root). Over Z "
        "the question is Hilbert's tenth problem, which has no algorithm "
        "(Matiyasevich); its key step, that exponentiation is Diophantine, "
        "is in Mathlib (Dioph.pow_dioph), the undecidability itself is not")
    account = ("why a particular LTI verification query becomes a "
               "multivariate Diophantine problem is an account of that "
               "translation, not derived here")
    dispute = ("the machine's INTEGER_UNDECIDED is not forced by "
               "Matiyasevich's theorem: it is the node budget of its Omega "
               "test (NODE_LIMIT = " + str(ID.NODE_LIMIT) + " search steps, "
               "reasoning/integer_decision.py) on linear integer constraints "
               "-- Presburger arithmetic, which is decidable -- and a "
               "nonlinear Diophantine query is not read by that procedure "
               "at all")
    return Built(derived, account, rows, claims, check, "rational_root",
                 key_row="NODE_LIMIT",
                 column1="real decisions against rational and integer ones",
                 backing="exact rationals + Lean theorem + "
                         "reasoning.integer_decision",
                 disputes=(dispute,), lean=("real_root_no_rational_root",),
                 row_names=("reasoning.integer_decision.NODE_LIMIT",))


# ===========================================================================
# 7.  TOPIC TABLE, READING, CONTROLS
# ===========================================================================

def _cues(*groups: Sequence[str], exclude: Sequence[str] = ()
          ) -> Callable[[str], bool]:
    def match(t: str) -> bool:
        if any(x in t for x in exclude):
            return False
        return all(any(w in t for w in g) for g in groups)
    return match


@dataclass(frozen=True)
class Topic:
    key: str
    index: int
    scope: str
    match: Callable[[str], bool]
    build: Callable[[], Built] = field(repr=False)


TOPICS: Tuple[Topic, ...] = (
    Topic("rlc_resonance", 0, "FULL",
          _cues(["rlc"], ["resonan"], ["impedance"]), _t_rlc),
    Topic("quasi_fermi", 4, "ANCHORED",
          _cues(["quasi-fermi", "quasi fermi"], ["junction", "diode"]),
          _t_quasi_fermi),
    Topic("stork_enamine", 23, "ANCHORED",
          _cues(["cyclohexanone"], ["pyrrolidine"]), _t_stork),
    Topic("derivative_kick", 32, "FULL",
          _cues(["derivative"], ["kick"]), _t_derivative_kick),
    Topic("window_tradeoff", 43, "ANCHORED",
          _cues(["kaiser"], ["rectangular"], ["window"]), _t_window),
    Topic("helium_beryllium", 60, "ANCHORED",
          _cues(["helium"], ["beryllium"], ["inert", "bond", "compound"],
                exclude=["beryllium-8"]), _t_he_be),
    Topic("osmium_density", 61, "ANCHORED",
          _cues(["osmium"], ["densit"], ["why", "explain", "peak", "paradox"]),
          _t_osmium),
    Topic("fluorine_oxidation", 62, "ANCHORED",
          _cues(["fluorine"], ["oxidation"]), _t_fluorine),
    Topic("group14_conductivity", 63, "ANCHORED",
          _cues(["group 14"], ["insulator", "semiconductor", "metal"]),
          _t_group14),
    Topic("gold_mercury", 64, "ANCHORED",
          _cues(["gold"], ["mercury"], ["relativ"]), _t_gold_mercury),
    Topic("technetium", 65, "ANCHORED",
          _cues(["technetium"], ["stable"]), _t_technetium),
    Topic("fluoride_volatility", 66, "ANCHORED",
          _cues(["taf_5", "taf5", "tantalum pentafluoride"],
                ["wf_6", "wf6", "tungsten hexafluoride"]), _t_fluoride),
    Topic("lanthanide_contraction", 67, "ANCHORED",
          _cues(["hafnium"], ["zirconium"]), _t_lanthanide),
    Topic("actinide_counting", 68, "ANCHORED",
          _cues(["actinide"], ["5f"], ["6d"]), _t_actinide),
    Topic("oganesson", 69, "ANCHORED",
          _cues(["oganesson"], ["relativ", "spin-orbit", "noble gas"]),
          _t_oganesson),
    Topic("deuteron", 70, "ANCHORED",
          _cues(["deuteron"], ["diproton", "dineutron"]), _t_deuteron),
    Topic("mirror_nuclei", 71, "ANCHORED",
          _cues(["mirror"], ["carbon-11", "boron-11"]), _t_mirror),
    Topic("lead208", 72, "ANCHORED",
          _cues(["lead-208", "208pb", "^{208}pb"]), _t_lead),
    Topic("beryllium8", 73, "ANCHORED",
          _cues(["beryllium-8"], ["alpha"]), _t_be8),
    Topic("double_beta", 74, "FULL",
          _cues(["double-beta", "double beta"], ["neutrino"]),
          _t_double_beta),
    Topic("giant_dipole", 75, "ANCHORED",
          _cues(["giant dipole"]), _t_gdr),
    Topic("island_stability", 76, "ANCHORED",
          _cues(["island of stability"]), _t_island),
    Topic("s_r_process", 77, "ANCHORED",
          _cues(["r-process"], ["s-process", "neutron capture"]), _t_s_r),
    Topic("lithium_problem", 78, "ANCHORED",
          _cues(["lithium"], ["nucleosynthesis"]), _t_lithium),
    Topic("hoyle_state", 79, "ANCHORED",
          _cues(["hoyle"]), _t_hoyle),
    Topic("material_implication", 80, "ANCHORED",
          _cues(["material implication"]), _t_material),
    Topic("soundness_completeness", 82, "ANCHORED",
          _cues(["soundness"], ["completeness"]), _t_soundness),
    Topic("intuitionistic_lem", 83, "ANCHORED",
          _cues(["intuitionistic"], ["excluded middle"]), _t_intuitionistic),
    Topic("skolem_paradox", 84, "ANCHORED",
          _cues(["skolem paradox"]), _t_skolem),
    Topic("fuzzy_probability", 87, "ANCHORED",
          _cues(["fuzzy"], ["probabilit"]), _t_fuzzy),
    Topic("godel_second", 88, "ANCHORED",
          _cues(["con(pa)"], ["consisten"]), _t_godel),
    Topic("lindstrom", 89, "ANCHORED",
          _cues(["lindstr"]), _t_lindstrom),
    Topic("cstr_multiplicity", 29, "ANCHORED",
          _cues(["cstr"], ["multiple steady states", "ignition",
                           "multiplicity"]), _t_cstr),
    Topic("mpc_constraints", 39, "ANCHORED",
          _cues(["model predictive control", "mpc"], ["constraint"]),
          _t_mpc),
    Topic("tarski_diophantine", 96, "ANCHORED",
          _cues(["tarski"], ["diophantine"]), _t_tarski),
)

TOPIC_KEYS: Tuple[str, ...] = tuple(t.key for t in TOPICS)


def topic_of(text: str) -> Optional[Topic]:
    """The topic whose cues the (normalised) text meets, or ``None``."""
    t = text.lower()
    for tp in TOPICS:
        if tp.match(t):
            return tp
    return None


def _answer(tp: Topic, b: Built, script: str) -> Answer:
    value = b.derived
    if tp.scope == "ANCHORED" and b.account:
        value = value + ". " + "refused EXPLANATION: " + b.account
    col2 = ("rows read: " + "; ".join(b.row_names) if b.row_names
            else "no register row: a derivation")
    if b.lean:
        col2 += "; Lean: " + ", ".join(b.lean)
    return Answer(tp.key, True, value, b.column1, col2, script,
                  scope=tp.scope, backing=b.backing, disputes=b.disputes,
                  rows=b.row_names, lean=b.lean)


def read_topic(tp: Topic, text: str = "") -> Answer:
    """The answer of ``tp`` (``text`` is the question as read; the topics
    answer the declared question, so it is not re-parsed)."""
    b = tp.build()
    return _answer(tp, b, script_of(b.rows, b.claims, b.check))


def mutated(tp: Topic, kind: str) -> Optional[Answer]:
    """The answer with one control applied; ``None`` when the control does
    not apply (``register-row`` on an answer that reads no register)."""
    b = tp.build()
    rows, claims = dict(b.rows), dict(b.claims)
    if kind == "script-claim":
        claims[b.headline] = _alter(claims[b.headline])
    elif kind == "register-row":
        if not b.key_row or b.key_row not in rows:
            return None
        rows = _deep(rows)
        if b.row_mutation is not None:
            b.row_mutation(rows)
        else:
            rows[b.key_row] = _alter(rows[b.key_row])
    else:
        raise ValueError(kind)
    return _answer(tp, b, script_of(rows, claims, b.check))

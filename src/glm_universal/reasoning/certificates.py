"""``glm_universal.reasoning.certificates`` -- derivations that carry their proof.

What this module is
-------------------
Experiment X7 of ``studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md``. It comes from
the supplied list's item *prioritise absent derivations*: build operations
whose answers no register holds, and make every answer checkable.

Three operations, each returning a **certificate** alongside the answer. The
certificate is data a separate checker can verify without trusting the
procedure that produced it:

``bezout(a, b)``
    ``g = gcd(a, b)`` with integers ``x, y`` such that ``a x + b y = g``. The
    certificate is the triple ``(g, x, y)`` and the check is two divisions and
    one multiply-add. ``GLM.SubstrateCognition.bezout_certificate_sound``
    proves that a triple which passes the check names the gcd.
``solve_linear(a, b, c)``
    every integer solution of ``a x + b y = c``, or an **impossibility
    certificate** saying ``gcd(a, b)`` does not divide ``c``.
    ``GLM.SubstrateCognition.no_solution_of_not_dvd`` proves that such a
    certificate really excludes every pair, and
    ``GLM.SubstrateCognition.linear_solutions_complete`` that the family
    returned is all of them.
``factorise(n, bound)``
    the prime factorisation of ``n``, found by trial division up to ``bound``.
    Every factor must be certified prime, either by trial division below its
    square root or because nothing below the bound divides it and it is below
    ``bound**2``. If a cofactor cannot be certified within the bound, the
    operation **refuses**, and the refusal names the bound. It never guesses
    that a large cofactor is prime.

Everything is exact integer arithmetic (D7), with no randomness and no
probabilistic primality test. A certificate that fails its own check raises,
so a wrong answer cannot leave this module silently.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = [
    "FACTOR_BOUND", "CertificateRefusal", "Bezout", "LinearSolution",
    "Factorisation", "bezout", "check_bezout", "solve_linear",
    "check_linear", "factorise", "check_factorisation", "render_bezout",
    "render_linear",
    "render_factorisation", "Recognition", "simplest_in",
    "recognise_decimal", "check_recognition", "render_recognition",
    "refusal_recognition", "stream_interval", "recognise_stream",
    "MonomialDerivation", "derive_monomial", "check_monomial",
    "render_monomial", "certificates_report",
]

#: The trial-division bound: primes up to this are tried, so a cofactor below
#: its square is certified prime when nothing up to the bound divides it.
FACTOR_BOUND: int = 1_000_000


class CertificateRefusal(ValueError):
    """Raised when an operation declines, with the reason as its message."""


# ===========================================================================
# 1.  BEZOUT
# ===========================================================================

@dataclass(frozen=True)
class Bezout:
    """``g = gcd(a, b) = a*x + b*y``, with ``g >= 0``."""

    a: int
    b: int
    g: int
    x: int
    y: int


def _check_int(value, where: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{where}: expected an int, got {type(value)!r}")
    return value


def bezout(a: int, b: int) -> Bezout:
    """The extended Euclidean algorithm, with its certificate checked."""
    a = _check_int(a, "bezout")
    b = _check_int(b, "bezout")
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
    g, x, y = old_r, old_s, old_t
    if g < 0:
        g, x, y = -g, -x, -y
    out = Bezout(a, b, g, x, y)
    if not check_bezout(out):                       # pragma: no cover
        raise AssertionError(f"bezout: certificate failed for {a}, {b}")
    return out


def check_bezout(cert: Bezout) -> bool:
    """The independent check: ``a x + b y = g``, ``g | a``, ``g | b``, ``g >= 0``.

    This is exactly the hypothesis of
    ``GLM.SubstrateCognition.bezout_certificate_sound``, which concludes
    ``g = gcd(a, b)``.
    """
    a, b, g = cert.a, cert.b, cert.g
    if g < 0 or a * cert.x + b * cert.y != g:
        return False
    if g == 0:
        return a == 0 and b == 0
    return a % g == 0 and b % g == 0


# ===========================================================================
# 2.  LINEAR DIOPHANTINE EQUATIONS IN TWO UNKNOWNS
# ===========================================================================

@dataclass(frozen=True)
class LinearSolution:
    """The solution set of ``a x + b y = c`` over the integers.

    ``kind`` is ``"family"`` (``x = x0 + sx*k``, ``y = y0 + sy*k``),
    ``"everything"`` (``a = b = c = 0``), or ``"none"``, in which case
    ``g`` does not divide ``c`` and that is the certificate.
    """

    a: int
    b: int
    c: int
    g: int
    kind: str
    x0: int = 0
    y0: int = 0
    sx: int = 0
    sy: int = 0


def solve_linear(a: int, b: int, c: int) -> LinearSolution:
    """Every integer solution of ``a x + b y = c``, or why there is none."""
    for v in (a, b, c):
        _check_int(v, "solve_linear")
    cert = bezout(a, b)
    g = cert.g
    if g == 0:
        kind = "everything" if c == 0 else "none"
        return LinearSolution(a, b, c, 0, kind)
    if c % g != 0:
        return LinearSolution(a, b, c, g, "none")
    scale = c // g
    x, y = cert.x * scale, cert.y * scale
    sx, sy = b // g, -(a // g)
    if sx < 0 or (sx == 0 and sy < 0):
        sx, sy = -sx, -sy
    if sx != 0:
        k = -(x // sx)              # smallest k with x + sx*k >= 0
        x, y = x + sx * k, y + sy * k
    else:
        # b = 0: x is fixed; y is free, and the family steps in y alone.
        k = -(y // sy)
        x, y = x + sx * k, y + sy * k
    out = LinearSolution(a, b, c, g, "family", x, y, sx, sy)
    if not check_linear(out):                       # pragma: no cover
        raise AssertionError(f"solve_linear: certificate failed for "
                             f"{a}, {b}, {c}")
    return out


def check_linear(sol: LinearSolution) -> bool:
    """The independent check of a solution set.

    ``family``: the particular pair solves the equation, and the step
    ``(sx, sy)`` is ``(b/g, -a/g)`` up to sign, so it stays inside the
    solution set. That it reaches every solution is
    ``GLM.SubstrateCognition.linear_solutions_complete``.
    ``none``: ``g = gcd(a, b)`` and ``g`` does not divide ``c``
    (``GLM.SubstrateCognition.no_solution_of_not_dvd``). ``everything``:
    ``a = b = c = 0``.
    """
    a, b, c, g = sol.a, sol.b, sol.c, sol.g
    if sol.kind == "everything":
        return a == 0 and b == 0 and c == 0
    if not check_bezout(bezout(a, b)) or bezout(a, b).g != g:
        return False
    if sol.kind == "none":
        return (c != 0) if g == 0 else (c % g != 0)
    if sol.kind != "family" or g == 0:
        return False
    if a * sol.x0 + b * sol.y0 != c:
        return False
    if a * sol.sx + b * sol.sy != 0:
        return False
    return {(sol.sx, sol.sy), (-sol.sx, -sol.sy)} == {
        (b // g, -(a // g)), (-(b // g), a // g)}


def _paren(value: int) -> str:
    return f"({value})" if value < 0 else f"{value}"


def _term(value: int, step: int) -> str:
    if step == 0:
        return f"{value}"
    sign = "+" if step > 0 else "-"
    return f"{value} {sign} {abs(step)}k"


def render_bezout(cert: Bezout) -> str:
    """Bezout's identity for ``a, b``, certificate included."""
    return (f"gcd({cert.a}, {cert.b}) = {cert.g} = {cert.a}*{_paren(cert.x)} "
            f"+ {cert.b}*{_paren(cert.y)} -- certificate: the combination "
            f"evaluates to {cert.g}, and {cert.g} divides both {cert.a} and "
            f"{cert.b}, so it is the greatest common divisor")


def render_linear(sol: LinearSolution) -> str:
    """The solution set in words, certificate included."""
    eq = f"{sol.a}x + {sol.b}y = {sol.c}".replace("+ -", "- ")
    if sol.kind == "everything":
        return (f"{eq}: every integer pair (x, y) is a solution, since both "
                f"coefficients and the right-hand side are 0")
    if sol.kind == "none":
        return (f"{eq} has no integer solution -- certificate: "
                f"gcd({sol.a}, {sol.b}) = {sol.g} does not divide {sol.c}, "
                f"and a*x + b*y is always a multiple of the gcd")
    return (f"{eq}: x = {_term(sol.x0, sol.sx)}, y = {_term(sol.y0, sol.sy)} "
            f"for every integer k -- certificate: gcd({sol.a}, {sol.b}) = "
            f"{sol.g} divides {sol.c}, {sol.a}*{_paren(sol.x0)} + "
            f"{_paren(sol.b)}*{_paren(sol.y0)} = "
            f"{sol.c}, and the step ({sol.sx}, {sol.sy}) is ({sol.b}/{sol.g}, "
            f"-{sol.a}/{sol.g}) up to sign")


# ===========================================================================
# 3.  FACTORISATION WITHIN A STATED BOUND
# ===========================================================================

@dataclass(frozen=True)
class Factorisation:
    """``n = prod p**e``, every ``p`` certified prime within ``bound``."""

    n: int
    factors: Tuple[Tuple[int, int], ...]
    bound: int


def factorise(n: int, bound: int = FACTOR_BOUND) -> Factorisation:
    """Trial division up to ``bound``; refuse what cannot be certified."""
    n = _check_int(n, "factorise")
    if n < 1:
        raise CertificateRefusal(f"factorise: {n} is not a positive integer")
    rest = n
    found: Dict[int, int] = {}
    p = 2
    while p <= bound and p * p <= rest:
        while rest % p == 0:
            found[p] = found.get(p, 0) + 1
            rest //= p
        p += 1 if p == 2 else 2
    if rest > 1:
        # Nothing up to min(bound, sqrt(rest)) divides rest.  It is prime if
        # the search reached its square root, i.e. if p*p > rest.
        if p * p <= rest:
            raise CertificateRefusal(
                f"factorise: after trial division up to {bound}, a cofactor "
                f"of {len(str(rest))} digits remains and cannot be certified "
                f"prime or composite within the bound")
        found[rest] = found.get(rest, 0) + 1
    out = Factorisation(n, tuple(sorted(found.items())), bound)
    if not check_factorisation(out):                # pragma: no cover
        raise AssertionError(f"factorise: certificate failed for {n}")
    return out


def _is_prime_by_trial(p: int) -> bool:
    if p < 2:
        return False
    d = 2
    while d * d <= p:
        if p % d == 0:
            return False
        d += 1 if d == 2 else 2
    return True


def check_factorisation(f: Factorisation) -> bool:
    """The product is ``n`` and every listed factor is prime by trial."""
    product = 1
    for p, e in f.factors:
        if e < 1 or not _is_prime_by_trial(p):
            return False
        product *= p ** e
    return product == f.n


def render_factorisation(f: Factorisation) -> str:
    """Ascending prime powers joined by ``" * "``, certificate included."""
    if f.n == 1:
        return "1 has no prime factors (the empty product)"
    if f.factors == ((f.n, 1),):
        return (f"{f.n} is prime -- certificate: no integer from 2 to "
                f"floor(sqrt({f.n})) divides it")
    body = " * ".join(f"{p}^{e}" if e > 1 else f"{p}" for p, e in f.factors)
    return (f"{f.n} = {body} -- certificate: the product multiplies back to "
            f"{f.n} and each factor is prime by trial division")


# ===========================================================================
# 4.  RATIONAL RECOGNITION (round two, Y2)
# ===========================================================================

@dataclass(frozen=True)
class Recognition:
    """The simplest fraction in a closed interval, and how far it is unique.

    ``fraction`` is the least-denominator fraction in ``[lo, hi]``.  Any
    other fraction in the interval has a denominator of at least
    ``rival_bound`` (``GLM.SubstrateCognition.farey_rival_bound``): two
    distinct fractions ``p/q`` and ``r/s`` differ by at least ``1/(q s)``.
    ``significant`` is the declared answering rule of the study, ``2 q^2 w <=
    1``: the nearest rival's denominator is at least twice the answer's.
    """

    text: str
    lo: Fraction
    hi: Fraction
    fraction: Fraction
    rival_bound: Fraction
    significant: bool


def simplest_in(lo: Fraction, hi: Fraction) -> Fraction:
    """The simplest fraction in the closed interval ``[lo, hi]``.

    "Simplest" is the Stern--Brocot sense: least denominator, and least
    numerator in absolute value among those, which is a single fraction.
    The classic continued-fraction recursion: an integer in the interval is
    the answer; otherwise both ends share an integer part ``f``, and the
    answer is ``f + 1/y`` for the simplest ``y`` in
    ``[1/(hi - f), 1/(lo - f)]``.  Exact; no float.
    """
    if lo > hi:
        raise ValueError("simplest_in: empty interval")
    if lo <= 0 <= hi:
        return Fraction(0)
    if hi < 0:
        return -simplest_in(-hi, -lo)
    f = lo.numerator // lo.denominator                  # floor(lo)
    if f == lo:
        return Fraction(f)
    if f + 1 <= hi:
        return Fraction(f + 1)
    return f + 1 / simplest_in(1 / (hi - f), 1 / (lo - f))


def _decimal_interval(text: str) -> Tuple[Fraction, Fraction, Fraction]:
    """``(value, lo, hi)`` for a decimal read at the places it is written to."""
    body = text.strip()
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", body):
        raise CertificateRefusal(f"{text!r} is not a decimal numeral")
    places = len(body.split(".")[1]) if "." in body else 0
    value = Fraction(body)
    half = Fraction(1, 2 * 10 ** places)
    return value, value - half, value + half


def recognise_decimal(text: str) -> Recognition:
    """The simplest fraction that rounds to a quoted decimal, certified."""
    _value, lo, hi = _decimal_interval(text)
    frac = simplest_in(lo, hi)
    width = hi - lo
    q = frac.denominator
    out = Recognition(text.strip(), lo, hi, frac, 1 / (q * width),
                      2 * q * q * width <= 1)
    if not check_recognition(out):                   # pragma: no cover
        raise AssertionError(f"recognise_decimal: certificate failed for "
                             f"{text!r}")
    return out


def check_recognition(r: Recognition) -> bool:
    """The independent check: the fraction lies in the interval, and no
    fraction of smaller denominator does (a scan over every smaller one)."""
    if not r.lo <= r.fraction <= r.hi:
        return False
    for s in range(1, r.fraction.denominator):
        k = -((-r.lo.numerator * s) // r.lo.denominator)   # ceil(lo * s)
        if Fraction(k, s) <= r.hi:
            return False
    return r.rival_bound == 1 / (r.fraction.denominator * (r.hi - r.lo))


def render_recognition(r: Recognition) -> str:
    """The recognised fraction with its uniqueness certificate."""
    frac = f"{r.fraction.numerator}/{r.fraction.denominator}"
    bound = _rival_denominator(r)
    return (f"{frac} is the simplest fraction that rounds to {r.text} -- "
            f"certificate: {r.text} as written stands for [{_dec(r.lo)}, "
            f"{_dec(r.hi)}], {frac} lies in it and no fraction with a smaller "
            f"denominator does, and any other fraction in it has a "
            f"denominator of at least {bound}")


def _rival_denominator(r: Recognition) -> int:
    """The least denominator any other fraction in the interval can have.

    At least ``ceil(rival_bound)`` by the Farey bound, and more than the
    answer's own, since two fractions of the least denominator cannot share
    an interval without a simpler one between them.
    """
    ceiling = -((-r.rival_bound.numerator) // r.rival_bound.denominator)
    return max(ceiling, r.fraction.denominator + 1)


def refusal_recognition(r: Recognition) -> str:
    """Why a recognition is refused: the rivals are too close in size."""
    frac = f"{r.fraction.numerator}/{r.fraction.denominator}"
    bound = _rival_denominator(r)
    return (f"{r.text} is too coarse to single out a fraction: the simplest "
            f"that rounds to it is {frac}, but the certificate only rules out "
            f"rivals with a denominator below {bound}, and the declared rule "
            f"asks that it rule out every rival below twice "
            f"{r.fraction.denominator}")


def _dec(x: Fraction) -> str:
    """A terminating decimal written out exactly."""
    sign = "-" if x < 0 else ""
    x = abs(x)
    whole = x.numerator // x.denominator
    rest = x - whole
    digits = ""
    while rest and len(digits) < 40:
        rest *= 10
        d = rest.numerator // rest.denominator
        digits += str(d)
        rest -= d
    return f"{sign}{whole}" + (f".{digits}" if digits else "")


def stream_interval(bits: Sequence[int]) -> Tuple[Fraction, Fraction]:
    """What ``N`` delta-sigma ticks say about the input ``t`` in ``[0, 1)``.

    The ones-count after ``n`` ticks is exactly ``floor(n t)``
    (``GLM.Info.dsOnes_eq_floor``), so ``t`` lies in
    ``[S_n / n, (S_n + 1) / n)`` for every ``n``.  Returns the intersection's
    closed hull ``[lo, hi]``; the true ``hi`` is excluded.
    """
    lo, hi = Fraction(0), Fraction(1)
    ones = 0
    for n, b in enumerate(bits, start=1):
        ones += b
        lo = max(lo, Fraction(ones, n))
        hi = min(hi, Fraction(ones + 1, n))
    return lo, hi


def recognise_stream(bits: Sequence[int], max_den: int) -> Tuple[str, Fraction]:
    """``("rational", p/q)`` or ``("excluded", simplest)`` from a window.

    ``rational``: the simplest fraction consistent with the window has a
    denominator at most ``max_den``, and when the window's width is below
    ``1 / max_den**2`` it is the only such fraction.  ``excluded``: no
    fraction of denominator at most ``max_den`` is consistent with the
    window, which is certain whatever the width.
    """
    lo, hi = stream_interval(bits)
    frac = simplest_in(lo, hi)
    if frac == hi and frac != lo:
        # hi itself is excluded (the window is half-open at the top)
        frac = simplest_in(lo, hi - Fraction(1, 10 ** 60))
    if frac.denominator <= max_den:
        return "rational", frac
    return "excluded", frac


# ===========================================================================
# 5.  DIMENSIONAL DERIVATION (round two, Y3)
# ===========================================================================

@dataclass(frozen=True)
class MonomialDerivation:
    """``target = k * prod given_i ** e_i``, or why no such law is fixed.

    ``kind`` is ``unique`` (``exponents`` set), ``impossible`` (``witness``
    ``y`` over the base axes with ``y . column_i = 0`` for every given
    quantity and ``y . target = gap != 0``) or ``undetermined``
    (``exponents`` one solution, ``free`` a dimensionless combination of the
    given quantities that can be added to it).
    """

    target: str
    given: Tuple[str, ...]
    axes: Tuple[str, ...]
    columns: Tuple[Tuple[Fraction, ...], ...]
    target_vector: Tuple[Fraction, ...]
    kind: str
    exponents: Tuple[Fraction, ...] = ()
    witness: Tuple[Fraction, ...] = ()
    gap: Fraction = Fraction(0)
    free: Tuple[Fraction, ...] = ()


def derive_monomial(target: str, target_vector: Sequence[Fraction],
                    given: Sequence[Tuple[str, Sequence[Fraction]]],
                    axes: Sequence[str]) -> MonomialDerivation:
    """Solve ``sum e_i column_i = target`` exactly, with its certificate."""
    m, n = len(axes), len(given)
    if n == 0:
        raise CertificateRefusal("derive_monomial: no quantities given")
    cols = tuple(tuple(Fraction(x) for x in vec) for _name, vec in given)
    t = tuple(Fraction(x) for x in target_vector)
    if any(len(c) != m for c in cols) or len(t) != m:
        raise ValueError("derive_monomial: every vector needs one entry per "
                         "axis")
    # Augmented rows [M | t | I_m]: the identity block records which
    # combination of the original rows each reduced row is.
    rows = [[cols[j][i] for j in range(n)] + [t[i]]
            + [Fraction(int(i == k)) for k in range(m)] for i in range(m)]
    pivots: List[int] = []
    r = 0
    for c in range(n):
        piv = next((i for i in range(r, m) if rows[i][c] != 0), None)
        if piv is None:
            continue
        rows[r], rows[piv] = rows[piv], rows[r]
        pv = rows[r][c]
        rows[r] = [x / pv for x in rows[r]]
        for i in range(m):
            if i != r and rows[i][c] != 0:
                f = rows[i][c]
                rows[i] = [a - f * b for a, b in zip(rows[i], rows[r])]
        pivots.append(c)
        r += 1
        if r == m:
            break
    names = tuple(name for name, _vec in given)
    for i in range(r, m):
        if rows[i][n] != 0:
            y = tuple(rows[i][n + 1:])
            out = MonomialDerivation(target, names, tuple(axes), cols, t,
                                     "impossible", witness=y,
                                     gap=rows[i][n])
            if not check_monomial(out):              # pragma: no cover
                raise AssertionError("derive_monomial: bad witness")
            return out
    e = [Fraction(0)] * n
    for i, c in enumerate(pivots):
        e[c] = rows[i][n]
    if len(pivots) == n:
        out = MonomialDerivation(target, names, tuple(axes), cols, t,
                                 "unique", exponents=tuple(e))
    else:
        free_col = next(c for c in range(n) if c not in pivots)
        z = [Fraction(0)] * n
        z[free_col] = Fraction(1)
        for i, c in enumerate(pivots):
            z[c] = -rows[i][free_col]
        out = MonomialDerivation(target, names, tuple(axes), cols, t,
                                 "undetermined", exponents=tuple(e),
                                 free=tuple(z))
    if not check_monomial(out):                      # pragma: no cover
        raise AssertionError("derive_monomial: certificate failed")
    return out


def _combine(cols: Sequence[Sequence[Fraction]],
             e: Sequence[Fraction]) -> Tuple[Fraction, ...]:
    m = len(cols[0]) if cols else 0
    return tuple(sum((e[j] * cols[j][i] for j in range(len(cols))),
                     Fraction(0)) for i in range(m))


def _rank(cols: Sequence[Sequence[Fraction]]) -> int:
    rows = [list(c) for c in cols]
    rank, width = 0, len(rows[0]) if rows else 0
    for c in range(width):
        piv = next((i for i in range(rank, len(rows)) if rows[i][c] != 0),
                   None)
        if piv is None:
            continue
        rows[rank], rows[piv] = rows[piv], rows[rank]
        for i in range(len(rows)):
            if i != rank and rows[i][c] != 0:
                f = rows[i][c] / rows[rank][c]
                rows[i] = [a - f * b for a, b in zip(rows[i], rows[rank])]
        rank += 1
    return rank


def check_monomial(d: MonomialDerivation) -> bool:
    """The independent check of a derivation.

    ``unique``: the exponents reproduce the target exactly and the columns
    are independent (rank = number of quantities), which is the hypothesis
    of ``GLM.SubstrateCognition.monomial_unique``.  ``impossible``: the
    witness annihilates every column and not the target
    (``GLM.SubstrateCognition.monomial_impossible``).  ``undetermined``: the
    exponents solve, and the free vector is a non-zero solution of the
    homogeneous system (``GLM.SubstrateCognition.monomial_undetermined``).
    """
    cols, t = d.columns, d.target_vector
    if d.kind == "impossible":
        y = d.witness
        if any(sum((a * b for a, b in zip(y, c)), Fraction(0)) != 0
               for c in cols):
            return False
        return sum((a * b for a, b in zip(y, t)), Fraction(0)) == d.gap != 0
    if _combine(cols, d.exponents) != t:
        return False
    if d.kind == "unique":
        return _rank(cols) == len(cols)
    if d.kind == "undetermined":
        return any(d.free) and not any(_combine(cols, d.free))
    return False


def _power(name: str, e: Fraction) -> str:
    return f"{name}^{e}"


def render_monomial(d: MonomialDerivation) -> str:
    """The law, or the certified 'no', in words."""
    given = ", ".join(d.given[:-1]) + (" and " if len(d.given) > 1 else "") \
        + d.given[-1]
    basis = "the extended ten-axis" if len(d.axes) == 10 else "the SI seven-axis"
    if d.kind == "unique":
        law = " * ".join(_power(n, e) for n, e in zip(d.given, d.exponents))
        return (f"{d.target} = k * {law}, for a dimensionless constant k that "
                f"dimensions cannot fix -- certificate: on {basis} basis the "
                f"exponents reproduce the dimensions of {d.target} exactly, "
                f"and the dimensions of {given} are independent, so no other "
                f"exponents do; this assumes {d.target} depends on {given} "
                f"alone")
    if d.kind == "impossible":
        comb = " + ".join(f"{c}*{a}" for a, c in zip(d.axes, d.witness)
                          if c != 0)
        return (f"no product of powers of {given} has the dimensions of "
                f"{d.target} -- certificate: the combination {comb} of base "
                f"exponents is 0 for every one of {given} and {d.gap} for "
                f"{d.target}, and a product of powers keeps it 0")
    group = " * ".join(_power(n, e) for n, e in zip(d.given, d.free) if e != 0)
    return (f"{d.target} is not fixed by {given}: {group} is dimensionless, "
            f"so any function of it can multiply the law")


# ===========================================================================
# 6.  REPORT
# ===========================================================================

def certificates_report() -> Dict[str, object]:
    """A handful of worked certificates, each re-checked independently."""
    rows: List[Dict[str, object]] = []
    for a, b, c in ((12, 18, 30), (6, 9, 5), (7, 5, 1), (0, 0, 0),
                    (3, -9, 6), (240, 46, 2)):
        sol = solve_linear(a, b, c)
        rows.append({"equation": (a, b, c), "kind": sol.kind,
                     "checked": check_linear(sol),
                     "rendered": render_linear(sol)})
    facts: List[Dict[str, object]] = []
    for n in (360, 97, 1, 600851475143):
        f = factorise(n)
        facts.append({"n": n, "checked": check_factorisation(f),
                      "rendered": render_factorisation(f)})
    refused: Optional[str] = None
    try:
        factorise(998244359987710471)
    except CertificateRefusal as why:
        refused = str(why)
    return {"linear": tuple(rows), "factorisations": tuple(facts),
            "refused_past_bound": refused,
            "all_checked": all(r["checked"] for r in rows)
            and all(f["checked"] for f in facts)}

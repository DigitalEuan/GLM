"""``glm_universal.reasoning.frame_plane`` -- ``tool frame`` in 1+2
dimensions: an operator on exact rational states ``(E, px, py)`` inferred
from example pairs, with the Thomas--Wigner rotation read off exactly
(Phase 178, second part).

*Created 22 October 2026. Last altered 22 October 2026 (Phase 181: the
improper families times a change of units, ``UNITS_OF``,
``PHASE_179_FAMILIES``; before it Phase 179: the improper families,
``improper_split``, ``PHASE_178_FAMILIES``).*

Where it comes from
-------------------
``tool frame`` (:mod:`glm_universal.reasoning.frame_operators`, Phase 177)
infers an operator on 2-vectors ``(E, p)``.  Its study left the widening to
1+2 dimensions open (``STATUS.md`` §2.1 item 10): boosts along any axis and
spatial rotations, where two boosts along different axes compose to a boost
*times a rotation* (Thomas--Wigner), and compositions of a boost with a
rotation, which the 1+1 tool refuses as outside its families.  This module is
that widening.  It keeps the three layers of the 1+1 tool.

1. **The invariant layer.**  Each pair set is read for the Gram matrices of
   its inputs and outputs under the Minkowski form ``E E' - px px' - py py'``
   and under the spatial form: a Lorentz map keeps the Minkowski Gram matrix
   (``GLM.LorentzPlane.minkowski_preserved``), a rotation keeps ``E`` and the
   spatial one, a change of units multiplies the Minkowski one by ``s^2``.  A
   family whose invariant fails is never fitted.
2. **The fit.**  A family is *completed* from the pairs when they determine
   it: three independent inputs fix any linear map; two fix a proper
   orthochronous Lorentz map too, once the Minkowski cross product of the
   inputs is sent to that of the outputs; one pair with a spatial part fixes
   a rotation; any pair fixes a change of units.  A Lorentz map is split into
   the pure boost to its image of the rest state times a rotation
   (``GLM.LorentzPlane.thomas_wigner``): the rotation is the Wigner rotation,
   exact and rational.
3. **The gate.**  Every family not ruled out gives the query an output -- its
   completion's, or, when it is not determined but the query lies in the span
   of the demonstration inputs, the output linearity forces.  The query is
   answered only when all of them agree and one is **tested**: completed from
   all pairs but one, it predicts the one left out (the span rule of
   ``FRAME_OPERATOR_STUDY.md`` §8).  A query outside the span of the
   demonstration inputs is answered only when those inputs span all three
   dimensions (the span guard, added after the first measurement).  Otherwise
   the refusal says why and names an input outside the span of the
   demonstrations to ask about.

The families
------------
``identity``; ``units`` (every component times ``s > 0``); ``rotation`` of
the spatial plane by a rational point of the unit circle; ``boost`` (a pure
boost along any direction: a symmetric Lorentz map); ``lorentz`` (any proper
orthochronous Lorentz map: a boost times a rotation, which is what two
boosts along different axes give); ``lorentz_units`` (a Lorentz map times a
change of units).

Improper maps (Phase 179)
-------------------------
Phase 178 refused every improper map as outside its families.  Phase 179
(``studies/IMPROPER_FRAME_STUDY.md``) declares the other three components of
the Lorentz group as families, beside the proper orthochronous ``lorentz``:
``reflection`` (``E`` kept, the spatial plane reflected in a line: the
improper counterpart of ``rotation``); ``lorentz_parity`` (determinant
``-1``, time kept: a Lorentz map times the reflection ``py -> -py``);
``lorentz_time`` (determinant ``-1``, time reversed: a Lorentz map times
``E -> -E``); ``lorentz_pt`` (determinant ``1``, time reversed).  The four
exhaust the group (``GLM.LorentzImproper.lorentz_four_components``), and an
answer from an improper family is split as ``B . P^a . T^b`` with ``B``
proper orthochronous (:func:`improper_split`), ``B`` then split by Wigner.
Two inputs fix each component, since a Lorentz map ``M`` sends the
Minkowski cross product ``n`` of two inputs to ``det(M)`` times that of their
outputs.  But two inputs never fix *which* component: ``M`` times the
reflection in their plane agrees with ``M`` on both and lies in another
component (``GLM.LorentzImproper.plane_partner``), which is the span guard's
reason, now proved.

Improper maps times a change of units (Phase 181)
-------------------------------------------------
Phase 179 left one improper case refused: an improper Lorentz map times a
change of units.  Phase 181 (``studies/IMPROPER_UNITS_STUDY.md``) declares
``lorentz_parity_units``, ``lorentz_time_units`` and ``lorentz_pt_units``
beside ``lorentz_units``.  Each is completed as ``lorentz_units`` is: the
Minkowski Gram matrix of the outputs must be ``k`` times that of the inputs
with ``k`` a positive rational square ``s^2``; the outputs divided by ``s`` are
completed in the matching component; the answer is ``s`` times it.  The change
of units divides out (``GLM.LorentzUnits.conformal_split``), the component is
read from the sign of the determinant and of the time--time entry, which the
positive scale keeps (``conformal_det_sign``, ``conformal_time_sign``), and
the eight families -- four components, each with or without units -- exhaust
the maps that keep the form up to a positive square (``conformal_eight``).
Two inputs still never fix the component (``scaled_plane_partner``).  An
answer from a units family names its component and its scale.

Exactness
---------
``Fraction`` throughout (D7).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = [
    "LEAN_FILE", "LEAN_THEOREMS", "FAMILIES", "State3", "Mat", "mink",
    "boost_x", "boost_y", "rot", "boost_to", "matmul", "matvec", "is_lorentz",
    "wigner", "solve", "first_fit", "parse_state3", "plane_text",
    "LEAN_FILE_IMPROPER", "LEAN_THEOREMS_IMPROPER", "COMPONENTS", "PARITY",
    "TIME_REV", "component", "improper_split", "reflect",
    "PHASE_178_FAMILIES", "PHASE_179_FAMILIES", "UNITS_OF",
    "LEAN_FILE_UNITS", "LEAN_THEOREMS_UNITS",
]

LEAN_FILE = "RequestProject/GLM/LorentzPlane.lean"
LEAN_THEOREMS: Tuple[str, ...] = (
    "boostX_lorentz", "boostY_lorentz", "rot_lorentz", "lorentz_mul",
    "minkowski_preserved", "boostTo_symm", "boostTo_rest", "boostTo_lorentz",
    "thomas_eq", "thomas_lorentz", "thomas_not_symm", "thomas_wigner",
    "thomas_rotation_ne_one")

LEAN_FILE_IMPROPER = "RequestProject/GLM/LorentzImproper.lean"
LEAN_THEOREMS_IMPROPER: Tuple[str, ...] = (
    "parity_lorentz", "det_parity", "timeRev_lorentz", "det_timeRev",
    "timeRev_flips_time", "reflect_eq", "reflect_lorentz", "det_reflect",
    "det_eta", "lorentz_det_sq", "lorentz_time_sq", "lorentz_time_ne_zero",
    "lorentz_four_components", "householder_lorentz", "householder_det",
    "householder_fixes", "householder_flips", "plane_partner",
    "reflection_agrees_on_plane")

LEAN_FILE_UNITS = "RequestProject/GLM/LorentzUnits.lean"
LEAN_THEOREMS_UNITS: Tuple[str, ...] = (
    "smul_lorentz_conformal", "conformal_ratio", "conformal_split",
    "det_smul_three", "conformal_det_sign", "conformal_time_sign",
    "conformal_eight", "scaled_plane_partner", "two_parity_conformal")

FAMILIES: Tuple[str, ...] = ("identity", "units", "rotation", "boost",
                             "lorentz", "lorentz_units", "reflection",
                             "lorentz_parity", "lorentz_time", "lorentz_pt",
                             "lorentz_parity_units", "lorentz_time_units",
                             "lorentz_pt_units")

# A units family and the component its Lorentz factor lies in.
UNITS_OF: Dict[str, str] = {
    "lorentz_units": "lorentz", "lorentz_parity_units": "lorentz_parity",
    "lorentz_time_units": "lorentz_time", "lorentz_pt_units": "lorentz_pt"}

# The four components of the Lorentz group: (determinant, keeps time).
COMPONENTS: Dict[str, Tuple[int, bool]] = {
    "lorentz": (1, True), "lorentz_parity": (-1, True),
    "lorentz_time": (-1, False), "lorentz_pt": (1, False)}

F = Fraction
State3 = Tuple[Fraction, Fraction, Fraction]
Mat = Tuple[Tuple[Fraction, ...], ...]
Pairs = Sequence[Tuple[State3, State3]]

ETA: Mat = ((F(1), F(0), F(0)), (F(0), F(-1), F(0)), (F(0), F(0), F(-1)))
IDENT: Mat = ((F(1), F(0), F(0)), (F(0), F(1), F(0)), (F(0), F(0), F(1)))
PARITY: Mat = ((F(1), F(0), F(0)), (F(0), F(1), F(0)), (F(0), F(0), F(-1)))
TIME_REV: Mat = ((F(-1), F(0), F(0)), (F(0), F(1), F(0)), (F(0), F(0), F(1)))


# ── exact 3x3 arithmetic ──────────────────────────────────────────────────

def matmul(a: Mat, b: Mat) -> Mat:
    return tuple(tuple(sum((a[i][k] * b[k][j] for k in range(3)), F(0))
                       for j in range(3)) for i in range(3))


def matvec(a: Mat, v: State3) -> State3:
    return tuple(sum((a[i][k] * v[k] for k in range(3)), F(0))
                 for i in range(3))


def transpose(a: Mat) -> Mat:
    return tuple(tuple(a[j][i] for j in range(3)) for i in range(3))


def det(a: Mat) -> Fraction:
    return (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
            - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
            + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))


def inverse(a: Mat) -> Optional[Mat]:
    d = det(a)
    if d == 0:
        return None
    cof = [[(a[(j + 1) % 3][(i + 1) % 3] * a[(j + 2) % 3][(i + 2) % 3]
             - a[(j + 1) % 3][(i + 2) % 3] * a[(j + 2) % 3][(i + 1) % 3])
            for j in range(3)] for i in range(3)]
    return tuple(tuple(cof[i][j] / d for j in range(3)) for i in range(3))


def columns(vs: Sequence[State3]) -> Mat:
    return tuple(tuple(v[i] for v in vs) for i in range(3))


def mink(a: State3, b: State3) -> Fraction:
    return a[0] * b[0] - a[1] * b[1] - a[2] * b[2]


def spatial(a: State3, b: State3) -> Fraction:
    return a[1] * b[1] + a[2] * b[2]


def cross_eta(a: State3, b: State3) -> State3:
    """``eta (a x b)``: Minkowski-orthogonal to both ``a`` and ``b``."""
    c = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
         a[0] * b[1] - a[1] * b[0])
    return (c[0], -c[1], -c[2])


def rank(vs: Sequence[State3]) -> int:
    rows = [list(v) for v in vs]
    r, col = 0, 0
    while r < len(rows) and col < 3:
        piv = next((i for i in range(r, len(rows)) if rows[i][col] != 0), None)
        if piv is None:
            col += 1
            continue
        rows[r], rows[piv] = rows[piv], rows[r]
        for i in range(len(rows)):
            if i != r and rows[i][col] != 0:
                f = rows[i][col] / rows[r][col]
                rows[i] = [x - f * y for x, y in zip(rows[i], rows[r])]
        r += 1
        col += 1
    return r


def _combination(basis: Sequence[State3], q: State3
                 ) -> Optional[List[Fraction]]:
    """Coefficients ``c`` with ``sum c_i basis_i = q``, or ``None``."""
    n = len(basis)
    rows = [[basis[j][i] for j in range(n)] + [q[i]] for i in range(3)]
    pivots, r = [], 0
    for col in range(n):
        piv = next((i for i in range(r, 3) if rows[i][col] != 0), None)
        if piv is None:
            continue
        rows[r], rows[piv] = rows[piv], rows[r]
        pv = rows[r][col]
        rows[r] = [x / pv for x in rows[r]]
        for i in range(3):
            if i != r and rows[i][col] != 0:
                f = rows[i][col]
                rows[i] = [x - f * y for x, y in zip(rows[i], rows[r])]
        pivots.append(col)
        r += 1
    if any(rows[i][n] != 0 for i in range(r, 3)):
        return None
    c = [F(0)] * n
    for i, col in enumerate(pivots):
        c[col] = rows[i][n]
    return c


def _independent(pairs: Pairs) -> List[Tuple[State3, State3]]:
    basis: List[Tuple[State3, State3]] = []
    for x, y in pairs:
        if rank([b for b, _ in basis] + [x]) > len(basis):
            basis.append((x, y))
    return basis


def linear_consistent(pairs: Pairs) -> bool:
    """Whether some linear map sends every input to its output."""
    basis = _independent(pairs)
    for x, y in pairs:
        c = _combination([b for b, _ in basis], x)
        out = tuple(sum((ci * by[k] for ci, (_, by) in zip(c, basis)), F(0))
                    for k in range(3))
        if out != y:
            return False
    return True


def in_span_output(pairs: Pairs, q: State3) -> Optional[State3]:
    """The output linearity forces on ``q``, if ``q`` is in the span."""
    basis = _independent(pairs)
    c = _combination([b for b, _ in basis], q)
    if c is None:
        return None
    return tuple(sum((ci * by[k] for ci, (_, by) in zip(c, basis)), F(0))
                 for k in range(3))


# ── the families' matrices ────────────────────────────────────────────────

def _ca(u: Fraction) -> Fraction:
    return (1 + u * u) / (1 - u * u)


def _sb(u: Fraction) -> Fraction:
    return 2 * u / (1 - u * u)


def boost_x(u: Fraction) -> Mat:
    a, b = _ca(u), _sb(u)
    return ((a, -b, F(0)), (-b, a, F(0)), (F(0), F(0), F(1)))


def boost_y(u: Fraction) -> Mat:
    a, b = _ca(u), _sb(u)
    return ((a, F(0), -b), (F(0), F(1), F(0)), (-b, F(0), a))


def rot(c: Fraction, s: Fraction) -> Mat:
    return ((F(1), F(0), F(0)), (F(0), c, -s), (F(0), s, c))


def boost_to(g: State3) -> Mat:
    """The pure boost taking the rest state to ``g`` (``mink(g, g) = 1``)."""
    g0, g1, g2 = g
    d = 1 + g0
    return ((g0, g1, g2), (g1, 1 + g1 * g1 / d, g1 * g2 / d),
            (g2, g1 * g2 / d, 1 + g2 * g2 / d))


def is_lorentz(m: Mat) -> bool:
    """Proper orthochronous Lorentz: ``m^T eta m = eta``, ``det 1``,
    ``m_00 > 0``."""
    return (matmul(matmul(transpose(m), ETA), m) == ETA and det(m) == 1
            and m[0][0] > 0)


def reflect(c: Fraction, s: Fraction) -> Mat:
    """``rot(c, s) . PARITY``: the spatial plane reflected in a line."""
    return ((F(1), F(0), F(0)), (F(0), c, s), (F(0), s, -c))


def is_lorentz_any(m: Mat) -> bool:
    """Any Lorentz map: ``m^T eta m = eta``."""
    return matmul(matmul(transpose(m), ETA), m) == ETA


def component(m: Mat) -> Optional[str]:
    """Which of the four components of the Lorentz group ``m`` lies in, or
    ``None`` when it is not a Lorentz map."""
    if not is_lorentz_any(m):
        return None
    d, ortho = det(m), m[0][0] > 0
    for name, (dd, oo) in COMPONENTS.items():
        if dd == d and oo == ortho:
            return name
    return None


def improper_split(m: Mat) -> Tuple[Mat, int, int]:
    """``m = B . PARITY^a . TIME_REV^b`` with ``B`` proper orthochronous
    (``GLM.LorentzImproper.lorentz_four_components``)."""
    b = 1 if m[0][0] < 0 else 0
    m1 = matmul(m, TIME_REV) if b else m
    a = 1 if det(m1) < 0 else 0
    m2 = matmul(m1, PARITY) if a else m1
    return m2, a, b


def is_rotation(m: Mat) -> bool:
    return (m[0] == (F(1), F(0), F(0)) and m[1][0] == 0 and m[2][0] == 0
            and is_lorentz(m))


def is_symmetric(m: Mat) -> bool:
    return transpose(m) == m


def wigner(m: Mat) -> Tuple[Mat, Tuple[Fraction, Fraction]]:
    """``m = boost_to(m e0) . rot(c, s)``: the pure boost and the Wigner
    rotation ``(c, s)`` of a Lorentz map (``GLM.LorentzPlane.thomas_wigner``)."""
    g = (m[0][0], m[1][0], m[2][0])
    b = boost_to(g)
    r = matmul(inverse(b), m)
    return b, (r[1][1], r[2][1])


def _sqrt(q: Fraction) -> Optional[Fraction]:
    if q < 0:
        return None
    from math import isqrt
    n, d = q.numerator, q.denominator
    rn, rd = isqrt(n), isqrt(d)
    return F(rn, rd) if rn * rn == n and rd * rd == d else None


# ── completing a family from pairs ────────────────────────────────────────

def _complete_linear(pairs: Pairs) -> Optional[Mat]:
    """The linear map three independent inputs fix, or ``None``."""
    basis = _independent(pairs)
    if len(basis) < 3:
        return None
    xin = inverse(columns([x for x, _ in basis]))
    return matmul(columns([y for _, y in basis]), xin)


def _complete_lorentz(pairs: Pairs, name: str = "lorentz") -> Optional[Mat]:
    """The Lorentz map of the component ``name`` the pairs fix, or ``None``.
    With two inputs, ``M n = det(M) fn`` for the Minkowski cross products
    ``n`` of the inputs and ``fn`` of the outputs."""
    d, ortho = COMPONENTS[name]
    m = _complete_linear(pairs)
    if m is None:
        basis = _independent(pairs)
        if len(basis) != 2:
            return None
        (a, fa), (b, fb) = basis
        n, fn = cross_eta(a, b), cross_eta(fa, fb)
        if mink(n, n) == 0:
            return None
        xin = inverse(columns([a, b, n]))
        if xin is None:
            return None
        m = matmul(columns([fa, fb, tuple(d * v for v in fn)]), xin)
    return m if component(m) == name else None


def _units_scale(pairs: Pairs) -> Optional[Fraction]:
    s = None
    for x, y in pairs:
        for xi, yi in zip(x, y):
            if xi != 0:
                s = yi / xi
                break
        if s is not None:
            break
    if s is None or s <= 0:
        return None
    return s if all(tuple(s * v for v in x) == y for x, y in pairs) else None


def complete(family: str, pairs: Pairs) -> Tuple[str, Optional[Mat]]:
    """``("fits", M)``, ``("free", None)`` (not ruled out, not determined)
    or ``("out", None)`` for one family."""
    if not pairs or not linear_consistent(pairs):
        return "out", None
    if family == "identity":
        return ("fits", IDENT) if all(x == y for x, y in pairs) else ("out", None)
    if family == "units":
        s = _units_scale(pairs)
        if s is None:
            return "out", None
        return "fits", tuple(tuple(s if i == j else F(0) for j in range(3))
                             for i in range(3))
    gram_in = [[mink(a, b) for b, _ in pairs] for a, _ in pairs]
    gram_out = [[mink(fa, fb) for _, fb in pairs] for _, fa in pairs]
    if family == "rotation":
        if any(x[0] != y[0] for x, y in pairs):
            return "out", None
        if [[spatial(a, b) for b, _ in pairs] for a, _ in pairs] != \
                [[spatial(fa, fb) for _, fb in pairs] for _, fa in pairs]:
            return "out", None
        for x, y in pairs:
            z = x[1] * x[1] + x[2] * x[2]
            if z:
                c = (y[1] * x[1] + y[2] * x[2]) / z
                s = (y[2] * x[1] - y[1] * x[2]) / z
                m = rot(c, s)
                ok = c * c + s * s == 1 and all(matvec(m, a) == b
                                                for a, b in pairs)
                return ("fits", m) if ok else ("out", None)
        return "free", None
    if family == "reflection":
        if any(x[0] != y[0] for x, y in pairs):
            return "out", None
        if [[spatial(a, b) for b, _ in pairs] for a, _ in pairs] != \
                [[spatial(fa, fb) for _, fb in pairs] for _, fa in pairs]:
            return "out", None
        for x, y in pairs:
            z = x[1] * x[1] + x[2] * x[2]
            if z:
                c = (x[1] * y[1] - x[2] * y[2]) / z
                s = (x[2] * y[1] + x[1] * y[2]) / z
                m = reflect(c, s)
                ok = c * c + s * s == 1 and all(matvec(m, a) == b
                                                for a, b in pairs)
                return ("fits", m) if ok else ("out", None)
        return "free", None
    if family in ("boost",) + tuple(COMPONENTS):
        if gram_out != gram_in:
            return "out", None
        name = "lorentz" if family == "boost" else family
        ortho = COMPONENTS[name][1]
        m = _complete_lorentz(pairs, name)
        if m is None:
            basis = [b for b, _ in _independent(pairs)]
            determined = len(basis) == 3 or (
                len(basis) == 2 and mink(cross_eta(*basis),
                                         cross_eta(*basis)) != 0)
            if determined:
                return "out", None       # determined, and not Lorentz
            if any(x[0] > 0 and mink(x, x) > 0 and (y[0] > 0) != ortho
                   for x, y in pairs):
                return "out", None       # the wrong direction of time
            return "free", None
        if not all(matvec(m, a) == b for a, b in pairs):
            return "out", None
        if family == "boost" and not is_symmetric(m):
            return "out", None
        return "fits", m
    if family in UNITS_OF:
        ratio = None
        for i in range(len(pairs)):
            for j in range(len(pairs)):
                if gram_in[i][j] != 0:
                    ratio = gram_out[i][j] / gram_in[i][j]
                    break
            if ratio is not None:
                break
        if ratio is None:
            return "free", None
        if ratio <= 0:
            return "out", None
        if any(gram_out[i][j] != ratio * gram_in[i][j]
               for i in range(len(pairs)) for j in range(len(pairs))):
            return "out", None
        s = _sqrt(ratio)
        if s is None:
            return "out", None
        scaled = [(x, tuple(v / s for v in y)) for x, y in pairs]
        st, m = complete(UNITS_OF[family], scaled)
        if st != "fits":
            return st, None
        return "fits", tuple(tuple(s * v for v in row) for row in m)
    raise KeyError(family)


def _tested(family: str, pairs: Pairs) -> bool:
    """Leave-one-out: completed from the other pairs, the family predicts
    the one left out; or the pair lies in the span of the others and the
    output linearity forces is its output (a linear test)."""
    for i in range(len(pairs)):
        rest = list(pairs[:i]) + list(pairs[i + 1:])
        if not rest:
            continue
        st, m = complete(family, rest)
        x, y = pairs[i]
        if st == "fits" and matvec(m, x) == y:
            return True
        if st != "out" and in_span_output(rest, x) == y:
            return True
    return False


# ── the gate ──────────────────────────────────────────────────────────────

ASK_POOL: Tuple[State3, ...] = tuple(
    (F(e), F(px), F(py)) for e, px, py in
    ((2, 1, 0), (2, 0, 1), (3, 1, 1), (1, 0, 0), (3, 2, 1), (3, 1, 2),
     (5, 3, 0), (5, 0, 3)))


def ask_input(pairs: Pairs) -> Optional[State3]:
    """A massive state outside the span of the demonstration inputs."""
    xs = [x for x, _ in pairs]
    for c in ASK_POOL:
        if rank(xs + [c]) > rank(xs):
            return c
    return None


PHASE_178_FAMILIES: Tuple[str, ...] = FAMILIES[:6]
PHASE_179_FAMILIES: Tuple[str, ...] = FAMILIES[:10]


def solve(pairs: Pairs, query: State3, gate: bool = True,
          families: Sequence[str] = FAMILIES) -> Dict[str, object]:
    """Every family's reading, and the verdict.  ``gate=False`` is the
    first-fit control: the first family not ruled out answers.
    ``families=PHASE_178_FAMILIES`` is the family set before Phase 179,
    ``PHASE_179_FAMILIES`` the set before Phase 181."""
    rows: Dict[str, Dict[str, object]] = {}
    span_out = in_span_output(pairs, query) if pairs else None
    for f in families:
        st, m = complete(f, pairs)
        out = None
        if st == "fits":
            out = matvec(m, query)
        elif st == "free":
            out = span_out
        rows[f] = {"status": st, "matrix": m, "output": out}
    live = [f for f in families if rows[f]["status"] != "out"]
    base = {"families": rows, "live": live, "rank": len(_independent(pairs)),
            "in_span": span_out is not None}
    if not live:
        return dict(base, status="unfit", answer=None)
    if not gate:
        o = rows[live[0]]["output"]
        return dict(base, status="answered" if o is not None else "free",
                    answer=o, by=live[0])
    # The span guard (added after the first take): a query outside the span
    # of the demonstration inputs is answered only from inputs that span all
    # three dimensions.  Otherwise every family's answer there is its own
    # extrapolation into a direction no demonstration reached, and a map
    # outside the families that agrees with one of them on the inputs' plane
    # (a reflection, a shear) is not told apart -- the 1+2 form of the
    # evidence guard of FRAME_OPERATOR_STUDY.md section 7.2.
    if span_out is None and base["rank"] < 3:
        return dict(base, status="outside_span", answer=None,
                    ask=ask_input(pairs))
    outs = [rows[f]["output"] for f in live]
    if any(o is None for o in outs):
        return dict(base, status="free", answer=None, ask=ask_input(pairs))
    if len(set(outs)) > 1:
        return dict(base, status="ambiguous", answer=None,
                    ask=ask_input(pairs))
    tested = [f for f in live if _tested(f, pairs)]
    base["tested"] = tested
    if not tested:
        return dict(base, status="untested", answer=None,
                    candidate=outs[0], ask=ask_input(pairs))
    out = dict(base, status="answered", answer=outs[0])
    m = rows["lorentz"]["matrix"] if "lorentz" in rows else None
    if m is not None and rows["lorentz"]["status"] == "fits":
        b, (c, s) = wigner(m)
        out["wigner"] = (c, s)
        out["boost_image_of_rest"] = (m[0][0], m[1][0], m[2][0])
        out["pure_boost"] = is_symmetric(m)
    for name in ("lorentz_parity", "lorentz_time", "lorentz_pt",
                 "lorentz_parity_units", "lorentz_time_units",
                 "lorentz_pt_units"):
        if name in rows and rows[name]["status"] == "fits":
            mm = rows[name]["matrix"]
            if name in UNITS_OF:
                if "component" in out:
                    continue      # a scale-1 fit: the component is named
                sc = _sqrt(mink(matvec(mm, (F(1), F(0), F(0))),
                                matvec(mm, (F(1), F(0), F(0)))))
                if not sc:
                    continue
                out["scale"] = sc
                mm = tuple(tuple(v / sc for v in row) for row in mm)
                name = UNITS_OF[name]
            bb, a, t = improper_split(mm)
            _b, (c, s) = wigner(bb)
            out["component"] = name
            out["split"] = {"parity": a, "time_reversal": t,
                            "boost_image_of_rest": (bb[0][0], bb[1][0],
                                                    bb[2][0]),
                            "wigner": (c, s)}
    return out


def first_fit(pairs: Pairs, query: State3) -> Dict[str, object]:
    return solve(pairs, query, gate=False)


# ── the tool's text ───────────────────────────────────────────────────────

def parse_state3(text: str) -> Optional[State3]:
    parts = [p.strip() for p in text.strip().split(",")]
    if len(parts) != 3:
        return None
    try:
        return tuple(F(p) for p in parts)
    except (ValueError, ZeroDivisionError):
        return None


def state_text(q: Optional[State3]) -> str:
    return "(none)" if q is None else ",".join(str(v) for v in q)


def _reading(pairs: Pairs) -> str:
    gin = [[mink(a, b) for b, _ in pairs] for a, _ in pairs]
    gout = [[mink(fa, fb) for _, fb in pairs] for _, fa in pairs]
    bits = ["the Minkowski Gram matrix of the inputs is kept"
            if gin == gout else "the Minkowski Gram matrix is not kept"]
    if all(x[0] == y[0] for x, y in pairs):
        bits.append("E is kept")
    bits.append(f"the inputs span {len(_independent(pairs))} of 3 dimensions")
    return "; ".join(bits)


def _mirror(live: Sequence[str]) -> str:
    """At a rank-2 refusal: say when a proper and an improper family both
    survive, the case ``GLM.LorentzImproper.plane_partner`` proves cannot be
    told apart off the inputs' plane."""
    proper = [f for f in live if f in ("identity", "rotation", "boost",
                                       "lorentz", "lorentz_pt")]
    improper = [f for f in live if f in ("reflection", "lorentz_parity",
                                         "lorentz_time")]
    if not proper or not improper:
        return ""
    return (f"; {proper[-1]} and {improper[-1]} both fit, and a map and its "
            f"reflection in the inputs' plane agree on every demonstration "
            f"(GLM.LorentzImproper.plane_partner)")


def plane_text(pairs: Pairs, query: State3) -> Tuple[bool, str, Dict[str, object]]:
    """``tool frame`` on 3-vectors: solve and say it in words."""
    r = solve(pairs, query)
    reading = _reading(pairs)
    live = r["live"]
    fig: Dict[str, object] = {"status": r["status"], "dimensions": "1+2",
                              "live": list(live), "rank": r["rank"]}
    if r["status"] == "answered":
        ans = r["answer"]
        fig["answer"] = state_text(ans)
        fig["tested"] = list(r["tested"])
        extra = ""
        if "wigner" in r:
            c, s = r["wigner"]
            fig["wigner"] = f"{c},{s}"
            fig["pure_boost"] = r["pure_boost"]
            extra = (f"; as a Lorentz map it is the pure boost taking rest to "
                     f"{state_text(r['boost_image_of_rest'])} times a rotation "
                     f"by ({c}, {s})"
                     + (" -- the identity, so a pure boost" if (c, s) ==
                        (1, 0) else
                        " -- a Wigner rotation, so not a pure boost "
                        "(GLM.LorentzPlane.thomas_wigner)"))
        if "component" in r:
            sp = r["split"]
            c, s = sp["wigner"]
            fig["component"] = r["component"]
            factors = (["the reflection py -> -py"] if sp["parity"] else []) \
                + (["time reversal E -> -E"] if sp["time_reversal"] else [])
            if "scale" in r:
                fig["scale"] = str(r["scale"])
                extra += (f"; it is {r['scale']} times a Lorentz map, a "
                          f"change of units (GLM.LorentzUnits.conformal_split)")
            extra += (f"; it is an improper Lorentz map ({r['component']}): "
                      f"{', then '.join(reversed(factors))}, then the proper "
                      f"map taking rest to "
                      f"{state_text(sp['boost_image_of_rest'])} with rotation "
                      f"({c}, {s}) "
                      f"(GLM.LorentzImproper.lorentz_four_components)")
        return True, (f"frame (1+2): {state_text(ans)}, given by every family "
                      f"not ruled out ({', '.join(live)}), "
                      f"{', '.join(r['tested'])} tested by a pair it was not "
                      f"fitted to{extra}; invariant layer: {reading}; "
                      f"E^2-px^2-py^2 of the answer is {mink(ans, ans)} "
                      f"against {mink(query, query)} for the query"), fig
    ask = r.get("ask")
    fig["ask"] = None if ask is None else state_text(ask)
    tail = ("" if ask is None else
            f"; to settle it, give the output for {state_text(ask)}")
    if r["status"] == "unfit":
        return False, (f"frame (1+2): refused -- no family fits all "
                       f"{len(pairs)} pairs (identity, units, rotation, boost,"
                       f" Lorentz, Lorentz times units, reflection, and the "
                       f"three improper Lorentz components, each also times "
                       f"units); invariant "
                       f"layer: "
                       f"{reading}"), fig
    if r["status"] == "untested":
        return False, (f"frame (1+2): refused -- the families not ruled out "
                       f"({', '.join(live)}) agree on "
                       f"{state_text(r['candidate'])}, but none is tested by a "
                       f"pair it was not fitted to; invariant layer: "
                       f"{reading}{tail}"), fig
    if r["status"] == "outside_span":
        return False, (f"frame (1+2): refused -- the query lies outside the "
                       f"span of the demonstration inputs, which reach only "
                       f"{r['rank']} of 3 dimensions, so any answer there is "
                       f"a family's extrapolation into a direction no "
                       f"demonstration tested (families not ruled out: "
                       f"{', '.join(live)}){_mirror(live)}; invariant layer: "
                       f"{reading}{tail}"), fig
    if r["status"] == "free":
        free = [f for f in live if r["families"][f]["output"] is None]
        return False, (f"frame (1+2): refused -- {', '.join(free)} "
                       f"{'is' if len(free) == 1 else 'are'} not determined by "
                       f"the pairs and the query lies outside the span of "
                       f"their inputs, so a parameter is free; invariant "
                       f"layer: {reading}{tail}"), fig
    said = "; ".join(f"{f} gives {state_text(r['families'][f]['output'])}"
                     for f in live)
    return False, (f"frame (1+2): refused -- the families that fit disagree: "
                   f"{said}; invariant layer: {reading}{tail}"), fig


def parse_plane_task(arg: str):
    """``E,px,py -> E,px,py ; ... ? E,px,py``, or ``None`` if the text is not
    a task on 3-vectors."""
    if "?" not in arg:
        return None
    left, qtext = arg.rsplit("?", 1)
    query = parse_state3(qtext)
    if query is None:
        return None
    pairs = []
    for part in [p for p in left.split(";") if p.strip()]:
        if "->" not in part:
            return None
        a, b = part.split("->", 1)
        x, y = parse_state3(a), parse_state3(b)
        if x is None or y is None:
            return None
        pairs.append((x, y))
    return (pairs, query) if pairs else None

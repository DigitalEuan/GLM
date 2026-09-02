"""The 24D Leech lattice and the Monster index space ``Lambda / 2 Lambda``.

The Monster does not act on the Leech lattice.  It acts on structures built on
the quotient ``Lambda / 2 Lambda``, and that quotient is where a concept
carried by a lattice point becomes a Monster-theoretic object.  Everything in
GLM-3+ above the substrate is indexed by what is built here.

Conventions
-----------
The lattice is used in the ``x sqrt(8)`` **integer model**: all coordinates are
integers and the minimal norm is ``32`` rather than ``4``.  In this model

    q(lambda) = (lambda . lambda) / 16   (mod 2)      the quadratic form
    B(lambda, mu) = (lambda . mu) / 8    (mod 2)      its polar form

are both well defined on classes -- checked in :func:`leech2_report`, not
assumed.  The scaled *rational* inner product of the unscaled lattice is
available as :func:`rational_inner` for callers that need the true geometry.

What is computed here (never quoted)
------------------------------------
* a Z-basis of ``Lambda`` in Hermite normal form, from an explicit generating
  set whose every member is checked against the defining congruences;
* the class map ``Lambda -> Lambda/2Lambda`` (a 24-bit integer per class) and
  its section back to a 0/1-coordinate representative;
* the F_2 quadratic form and its **Witt decomposition into 12 hyperbolic
  planes**, giving the plus-type singular count
  ``2^23 + 2^11 = 8,390,656`` in closed form;
* the 196,560 minimal vectors and hence the **98,280 type-2 classes** -- the
  ``2A`` axes visible inside the ``2B`` centraliser.  Type-2 detection is a
  table lookup against this exhaustively enumerated set, so a positive answer
  is a proof and a negative answer is a proof;
* the class census ``1 + 98,280 + 8,386,560 + 8,292,375 = 2^24``, with the
  type-3 and type-4 counts taken from the theta series of ``Lambda``, itself
  computed from ``E_4^3 - 720 Delta``.

Ported and refined from ``glm_lean/glm2/glm2_lattice.py`` and
``glm_lean/glm3/glm3_leech2.py``.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, FrozenSet, Iterator, List, Optional, Sequence, Tuple

from .linalg import (det_int, f2_independent, hermite_normal_form, popcount,
                     solve_upper_triangular)
from .mog import GOLAY_SET, OCTAD_MASKS

__all__ = [
    "DIM", "MIN_NORM2", "KISSING", "N_CLASSES", "SCALE", "INDEX_IN_Z24",
    "Vec",
    "norm2", "inner", "rational_inner", "rational_norm2",
    "in_leech", "LEECH_BASIS", "basis_determinant",
    "from_coords", "to_coords",
    "class_of", "class_vector", "representative",
    "q_form", "b_form", "q_coefficients", "b_coefficients",
    "witt_decomposition", "singular_class_count", "form_is_plus_type",
    "minimal_vectors", "type2_class_table", "type2_classes",
    "type2_table_cache_state",
    "is_type2_class", "is_2a_axis", "axis_of_class",
    "pair_invariant", "pair_census",
    "theta_series", "type_census",
    "leech2_report",
]

DIM = 24
MIN_NORM2 = 32            # minimal squared norm in the x sqrt(8) model
KISSING = 196560
N_CLASSES = 1 << 24
SCALE = 8                 # (integer-model inner product) / SCALE = true one
INDEX_IN_Z24 = 1 << 36    # [Z^24 : Lambda] in the x sqrt(8) integer model

Vec = Tuple[int, ...]


# ===========================================================================
# 1.  EXACT ARITHMETIC
# ===========================================================================

def norm2(x: Sequence[int]) -> int:
    """Squared norm in the integer model (minimal vectors have norm 32)."""
    return sum(int(v) * int(v) for v in x)


def inner(x: Sequence[int], y: Sequence[int]) -> int:
    """Inner product in the integer model."""
    return sum(int(a) * int(b) for a, b in zip(x, y))


def rational_inner(x: Sequence[int], y: Sequence[int]) -> Fraction:
    """The **true** Leech inner product as an exact rational.

    The integer model scales the lattice by ``sqrt(8)``, so the geometric
    inner product is the integer one divided by ``SCALE = 8``.  Returned as a
    :class:`~fractions.Fraction` so that no rounding ever occurs.
    """
    return Fraction(inner(x, y), SCALE)


def rational_norm2(x: Sequence[int]) -> Fraction:
    """The true squared norm as an exact rational (minimal vectors give 4)."""
    return Fraction(norm2(x), SCALE)


def in_leech(x: Sequence[int]) -> bool:
    """The defining congruences of ``Lambda``, executed exactly.

    A vector of 24 integers lies in ``Lambda`` iff all coordinates share a
    parity ``m``, the set ``{i : x_i = m + 2 (mod 4)}`` is a Golay codeword,
    and ``sum(x) = 4m (mod 8)``.
    """
    if len(x) != DIM:
        return False
    if any(not isinstance(v, int) for v in x):
        return False
    m = x[0] & 1
    if any((v & 1) != m for v in x):
        return False
    mask = 0
    target = (m + 2) % 4
    for i, v in enumerate(x):
        if v % 4 == target:
            mask |= 1 << i
    if mask not in GOLAY_SET:
        return False
    return sum(x) % 8 == (4 * m) % 8


def _generating_set() -> List[List[int]]:
    """An explicit generating set of ``Lambda``, each member verified.

    The 276 vectors ``4(e_i + e_j)``, the 759 vectors ``2 * 1_O`` for octads
    ``O``, and the odd vector ``(-3, 1, 1, ..., 1)``.
    """
    gens: List[List[int]] = []
    for i in range(DIM):
        for j in range(i + 1, DIM):
            v = [0] * DIM
            v[i] = v[j] = 4
            gens.append(v)
    for mask in OCTAD_MASKS:
        gens.append([2 if (mask >> i) & 1 else 0 for i in range(DIM)])
    odd = [1] * DIM
    odd[0] = -3
    gens.append(odd)
    bad = [v for v in gens if not in_leech(v)]
    if bad:
        raise AssertionError(f"{len(bad)} generators are not in Lambda")
    return gens


#: A Z-basis of ``Lambda`` in row-style Hermite normal form (upper triangular).
LEECH_BASIS: Tuple[Vec, ...] = tuple(
    tuple(row) for row in hermite_normal_form(_generating_set(), DIM))

#: Precomputed pivot columns of the basis, for a fast exact coordinate solve.
_PIVOT_COL: Tuple[int, ...] = tuple(
    next(j for j in range(DIM) if LEECH_BASIS[i][j] != 0) for i in range(DIM))
_PIVOT_VAL: Tuple[int, ...] = tuple(
    LEECH_BASIS[i][_PIVOT_COL[i]] for i in range(DIM))
_ROW_SUPPORT: Tuple[Tuple[Tuple[int, int], ...], ...] = tuple(
    tuple((j, LEECH_BASIS[i][j]) for j in range(DIM) if LEECH_BASIS[i][j])
    for i in range(DIM))


def basis_determinant() -> int:
    """``det(LEECH_BASIS)``.

    ``Lambda`` is unimodular, but the ``x sqrt(8)`` integer model scales it by
    ``sqrt(8)`` in 24 dimensions, so the determinant of the integral basis is
    ``8^(24/2) = 2^36 = INDEX_IN_Z24``, the index ``[Z^24 : Lambda]``.
    """
    return det_int([list(r) for r in LEECH_BASIS])


def from_coords(u: Sequence[int]) -> Vec:
    """The lattice point with coordinates ``u`` in :data:`LEECH_BASIS`."""
    if len(u) != DIM:
        raise ValueError("from_coords: 24 coordinates required")
    out = [0] * DIM
    for ui, support in zip(u, _ROW_SUPPORT):
        if ui:
            for j, val in support:
                out[j] += ui * val
    return tuple(out)


def to_coords(x: Sequence[int]) -> Optional[List[int]]:
    """Coordinates of a lattice point in :data:`LEECH_BASIS`, else ``None``.

    Back-substitution against the upper-triangular basis; returns ``None``
    exactly when ``x`` is not in ``Lambda``, so this doubles as an exact
    membership test.
    """
    if len(x) != DIM:
        return None
    rhs = [int(v) for v in x]
    u = [0] * DIM
    for i in range(DIM):
        pc = _PIVOT_COL[i]
        piv = _PIVOT_VAL[i]
        r = rhs[pc]
        if r % piv:
            return None
        q = r // piv
        u[i] = q
        if q:
            for j, val in _ROW_SUPPORT[i]:
                rhs[j] -= q * val
    return u if not any(rhs) else None


def _coords_or_raise(x: Sequence[int], where: str) -> List[int]:
    u = to_coords(x)
    if u is None:
        raise ValueError(f"{where}: the point is not in Lambda")
    return u


# ===========================================================================
# 2.  CLASSES IN Lambda / 2 Lambda
# ===========================================================================

def class_of(x: Sequence[int]) -> int:
    """The class of a lattice point in ``Lambda/2Lambda`` as a 24-bit int.

    The coordinates of ``x`` in :data:`LEECH_BASIS`, reduced mod 2.
    """
    u = _coords_or_raise(x, "class_of")
    out = 0
    for i, c in enumerate(u):
        if c & 1:
            out |= 1 << i
    return out


def class_vector(cls: int) -> List[int]:
    """The class as a list of 24 bits (coordinates in the Leech basis)."""
    return [(cls >> i) & 1 for i in range(DIM)]


def representative(cls: int) -> Vec:
    """The lattice point with 0/1 basis coordinates representing the class."""
    return from_coords(class_vector(cls))


# ===========================================================================
# 3.  THE F_2 QUADRATIC SPACE
# ===========================================================================

def q_coefficients() -> Tuple[int, ...]:
    """``q(e_i)`` for the 24 basis classes: ``norm2 / 16`` mod 2."""
    return tuple((norm2(r) // 16) % 2 for r in LEECH_BASIS)


def b_coefficients() -> Tuple[Tuple[int, ...], ...]:
    """``B(e_i, e_j) = (e_i . e_j) / 8`` mod 2."""
    return tuple(
        tuple((inner(LEECH_BASIS[i], LEECH_BASIS[j]) // 8) % 2
              for j in range(DIM))
        for i in range(DIM))


_QC: Tuple[int, ...] = q_coefficients()
_BC: Tuple[Tuple[int, ...], ...] = b_coefficients()


def q_form(cls: int) -> int:
    """``q(class)`` in F_2, from the coefficient table.

    ``q(u) = sum_i q_i u_i + sum_{i<j} B_ij u_i u_j``; agrees with
    ``norm2(representative) / 16 (mod 2)`` -- checked in the report.
    """
    bits = [i for i in range(DIM) if (cls >> i) & 1]
    total = 0
    for a, i in enumerate(bits):
        total ^= _QC[i]
        for j in bits[a + 1:]:
            total ^= _BC[i][j]
    return total & 1


def b_form(u: int, v: int) -> int:
    """The polar form ``B(u, v)`` in F_2."""
    total = 0
    for i in range(DIM):
        if (u >> i) & 1:
            row = _BC[i]
            for j in range(DIM):
                if (v >> j) & 1:
                    total ^= row[j]
    return total & 1


def witt_decomposition() -> Dict[str, object]:
    """Decompose ``(Lambda/2Lambda, q)`` into 2-dimensional planes.

    Symplectic Gram-Schmidt.  Each plane is recorded as hyperbolic (contains
    a nonzero singular vector) or anisotropic.  A nondegenerate F_2 quadratic
    space of dimension ``2m`` is of plus type iff the number of anisotropic
    planes is even, and then its singular vectors (including 0) number
    ``2^(2m-1) + 2^(m-1)``.
    """
    basis = [1 << i for i in range(DIM)]
    planes: List[Tuple[int, int, bool]] = []
    while basis:
        u = basis[0]
        partner: Optional[int] = None
        for cand in basis[1:]:
            if b_form(u, cand):
                partner = cand
                break
        if partner is None:
            for a in range(len(basis)):
                for b in range(a + 1, len(basis)):
                    cand = basis[a] ^ basis[b]
                    if b_form(u, cand):
                        partner = cand
                        break
                if partner is not None:
                    break
        if partner is None:
            raise AssertionError("degenerate form: no hyperbolic partner")
        v = partner
        hyperbolic = not (q_form(u) == 1 and q_form(v) == 1)
        planes.append((u, v, hyperbolic))
        rest = []
        for w in basis:
            if w in (u, v):
                continue
            w2 = w
            if b_form(w2, v):
                w2 ^= u
            if b_form(w2, u):
                w2 ^= v
            if w2:
                rest.append(w2)
        basis = f2_independent(rest)
    anisotropic = sum(1 for (_, _, h) in planes if not h)
    m = len(planes)
    plus = anisotropic % 2 == 0
    return {
        "planes": m,
        "anisotropic_planes": anisotropic,
        "hyperbolic_planes": m - anisotropic,
        "plus_type": plus,
        "singular_count": (1 << (2 * m - 1)) + ((1 if plus else -1) << (m - 1)),
        "expected_plus_singular": (1 << 23) + (1 << 11),
    }


def singular_class_count() -> int:
    """Number of singular classes, in closed form from the Witt data."""
    return int(witt_decomposition()["singular_count"])


def form_is_plus_type() -> bool:
    """Whether the F_2 quadratic form on ``Lambda/2Lambda`` is of plus type."""
    return bool(witt_decomposition()["plus_type"])


# ===========================================================================
# 4.  MINIMAL VECTORS AND 2A AXIS DETECTION
# ===========================================================================

def minimal_vectors() -> Iterator[Vec]:
    """Stream all 196,560 minimal vectors (squared norm 32).

    Three shapes: ``(+-4)^2 0^22``; ``(+-2)^8`` on an octad with an even
    number of minus signs; ``(-+3, +-1^23)`` driven by a Golay codeword.
    """
    for i in range(DIM):
        for j in range(i + 1, DIM):
            for si in (4, -4):
                for sj in (4, -4):
                    v = [0] * DIM
                    v[i], v[j] = si, sj
                    yield tuple(v)
    for mask in OCTAD_MASKS:
        pos = [i for i in range(DIM) if (mask >> i) & 1]
        for signs in range(256):
            if popcount(signs) & 1:
                continue
            v = [0] * DIM
            for k, p in enumerate(pos):
                v[p] = -2 if (signs >> k) & 1 else 2
            yield tuple(v)
    for i in range(DIM):
        for c in sorted(GOLAY_SET):
            v = [(-1 if (c >> j) & 1 else 1) for j in range(DIM)]
            v[i] = 3 if (c >> i) & 1 else -3
            yield tuple(v)


_TYPE2_TABLE: Optional[Dict[int, Vec]] = None
_TYPE2_SET: Optional[FrozenSet[int]] = None

#: Bumped when the stored shape below changes, so an artefact written by an
#: older version is *absent* rather than misread.
_TYPE2_CACHE_SCHEMA = 1


def _type2_cache_inputs() -> Tuple[object, ...]:
    """The sources the table is a function of: this module and what it reads.

    :func:`minimal_vectors` is driven by ``mog``'s Golay set and octad masks
    and by ``linalg``'s basis reduction, so those two are inputs as much as
    this file is.  Nothing else enters the derivation.
    """
    from pathlib import Path

    here = Path(__file__).resolve().parent
    return tuple(here / name
                 for name in ("leech2.py", "linalg.py", "mog.py"))


def _type2_store():
    """The digest-keyed artefact holding the table."""
    from ..derived import DerivedStore

    return DerivedStore("leech2_type2_table", _type2_cache_inputs,
                        schema=_TYPE2_CACHE_SCHEMA)


def _encode_type2(table: Dict[int, Vec]) -> Dict[str, object]:
    """Pack the table into two base64 blocks.

    98,280 entries as JSON objects would be a thirty-megabyte file that takes
    longer to parse than the enumeration takes to run, which would defeat the
    point.  A class is a 24-bit integer, so four bytes hold it exactly; a
    minimal vector's coordinates all lie in ``[-4, 4]``, so one signed byte
    holds each.  Both packings are exact -- no value is approximated or
    truncated -- and the reader checks the lengths it gets back.
    """
    import base64
    from array import array

    classes = sorted(table)
    keys = array("I", classes)
    coords = bytearray()
    for cls in classes:
        coords.extend(x & 0xFF for x in table[cls])
    return {
        "count": len(classes),
        "classes": base64.b64encode(keys.tobytes()).decode("ascii"),
        "vectors": base64.b64encode(bytes(coords)).decode("ascii"),
    }


def _decode_type2(payload: object) -> Optional[Dict[int, Vec]]:
    """Unpack :func:`_encode_type2`, or ``None`` if the block is not usable.

    A stored artefact is read back only when it has exactly the shape and the
    counts the enumeration would have produced; anything else is treated as
    absent, so a damaged file costs a recomputation and never an answer.
    """
    import base64
    from array import array

    if not isinstance(payload, dict):
        return None
    try:
        count = int(payload["count"])
        keys = array("I")
        keys.frombytes(base64.b64decode(payload["classes"]))
        coords = base64.b64decode(payload["vectors"])
    except (KeyError, TypeError, ValueError):
        return None
    if count != KISSING // 2 or len(keys) != count:
        return None
    if len(coords) != count * DIM:
        return None
    table: Dict[int, Vec] = {}
    for index, cls in enumerate(keys):
        block = coords[index * DIM:(index + 1) * DIM]
        table[cls] = tuple(b - 256 if b > 127 else b for b in block)
    return table if len(table) == count else None


def type2_table_cache_state() -> Dict[str, object]:
    """Whether the stored table still describes the sources it came from.

    The same three-way answer the Lean address book gives -- ``absent``,
    ``stale`` or ``fresh``, with both digests shown.  A stale artefact is
    never answered from; it is a signal to enumerate again.
    """
    return _type2_store().state()


def type2_class_table() -> Dict[int, Vec]:
    """Every type-2 class, with one of its two minimal vectors.

    Streaming the 196,560 minimal vectors and reducing each mod ``2 Lambda``
    must produce exactly 98,280 distinct classes, each hit exactly twice (a
    type-2 class is the pair ``{+-lambda}``).  That is asserted here, so the
    table is self-validating.  Built once and cached for the process.

    Across processes it is cached the way the Lean address book is: stored
    beside the SHA-256 digest of the three modules it is derived from, read
    back only while that digest holds, and enumerated again the moment it
    moves.  A stale artefact is never answered from.
    """
    global _TYPE2_TABLE, _TYPE2_SET
    if _TYPE2_TABLE is not None:
        return _TYPE2_TABLE
    stored = _decode_type2(_type2_store().read_fresh())
    if stored is not None:
        _TYPE2_TABLE = stored
        _TYPE2_SET = frozenset(stored)
        return stored
    table: Dict[int, Vec] = {}
    counts: Dict[int, int] = {}
    total = 0
    for v in minimal_vectors():
        total += 1
        if norm2(v) != MIN_NORM2:
            raise AssertionError("minimal_vectors yielded a non-minimal vector")
        c = class_of(v)
        counts[c] = counts.get(c, 0) + 1
        if c not in table:
            table[c] = v
    if total != KISSING:
        raise AssertionError(f"expected {KISSING} minimal vectors, got {total}")
    if any(k != 2 for k in counts.values()):
        raise AssertionError("a type-2 class did not contain exactly +-v")
    if len(table) != KISSING // 2:
        raise AssertionError(f"expected {KISSING // 2} type-2 classes")
    _TYPE2_TABLE = table
    _TYPE2_SET = frozenset(table)
    try:
        _type2_store().write(_encode_type2(table))
    except OSError:  # pragma: no cover - a read-only checkout still works
        pass
    return table


def type2_classes() -> FrozenSet[int]:
    """The 98,280 type-2 classes as a frozen set of 24-bit integers."""
    if _TYPE2_SET is None:
        type2_class_table()
    assert _TYPE2_SET is not None
    return _TYPE2_SET


def is_type2_class(cls: int) -> bool:
    """Whether a class is of type 2, by lookup against the complete table.

    Both answers are proofs: the table is the exhaustive image of the 196,560
    minimal vectors under the class map.
    """
    if not 0 <= cls < N_CLASSES:
        raise ValueError("is_type2_class: class must be a 24-bit integer")
    return cls in type2_classes()


def is_2a_axis(x: Sequence[int]) -> bool:
    """Whether a lattice point carries a ``2A`` axis.

    The 98,280 type-2 classes of ``Lambda/2Lambda`` index the ``2A``
    involutions visible inside the ``2B`` centraliser, and hence the middle
    piece of the Griess ledger.  ``x`` must lie in ``Lambda``.
    """
    return is_type2_class(class_of(x))


def axis_of_class(cls: int) -> Tuple[Vec, Vec]:
    """The pair ``{+lambda, -lambda}`` of minimal vectors of a type-2 class."""
    table = type2_class_table()
    if cls not in table:
        raise ValueError("axis_of_class: class is not of type 2")
    v = table[cls]
    return v, tuple(-a for a in v)


def pair_invariant(v: Sequence[int], w: Sequence[int]) -> int:
    """``|v . w| / 8`` for two minimal vectors.

    The complete invariant of a pair of type-2 classes under ``Co_0``, taking
    the values 4 (same class), 2, 1, 0.  Well defined on classes because a
    class is ``{+-v}``.
    """
    return abs(inner(v, w)) // 8


def pair_census(v: Optional[Sequence[int]] = None) -> Dict[int, int]:
    """Distribution of the 196,560 minimal vectors against a fixed one.

    Comes out as ``{4: 2, 2: 9200, 1: 94208, 0: 93150}`` -- the classical
    Leech distribution, and the reason the Monster's ``2A`` axes have only
    four mutual positions.
    """
    if v is None:
        v = next(iter(minimal_vectors()))
    out: Dict[int, int] = {}
    for w in minimal_vectors():
        k = pair_invariant(v, w)
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


# ===========================================================================
# 5.  THE THETA SERIES AND THE CLASS CENSUS
# ===========================================================================

def _sigma3(n: int) -> int:
    return sum(d ** 3 for d in range(1, n + 1) if n % d == 0)


def theta_series(order: int = 5) -> List[int]:
    """Theta series of ``Lambda`` as ``E_4^3 - 720 Delta``, exactly.

    Coefficient ``n`` counts vectors of squared norm ``8n`` in the integer
    model: ``[1, 0, 196560, 16773120, 398034000, ...]``.
    """
    e4 = [0] * (order + 1)
    e4[0] = 1
    for n in range(1, order + 1):
        e4[n] = 240 * _sigma3(n)

    def mul(a: List[int], b: List[int]) -> List[int]:
        out = [0] * (order + 1)
        for i, ai in enumerate(a):
            if ai:
                for j, bj in enumerate(b):
                    if i + j <= order and bj:
                        out[i + j] += ai * bj
        return out

    e4_3 = mul(mul(e4, e4), e4)
    prod = [0] * (order + 1)
    prod[0] = 1
    for n in range(1, order + 1):
        factor = [0] * (order + 1)
        factor[0] = 1
        factor[n] = -1
        for _ in range(24):
            prod = mul(prod, factor)
    delta = [0] * (order + 1)
    for n in range(order):
        delta[n + 1] = prod[n]
    return [e4_3[n] - 720 * delta[n] for n in range(order + 1)]


def type_census() -> Dict[str, object]:
    """The class census, derived from the theta series rather than quoted.

    ``type 2 classes = N(32)/2``, ``type 3 = N(48)/2``, ``type 4 = N(64)/48``
    (a type-4 class is a coordinate frame of 48 vectors).  The total must be
    ``2^24``, and the singular / nonsingular split must match plus type.
    """
    theta = theta_series(order=5)
    n2, n3, n4 = theta[2], theta[3], theta[4]
    c2, c3, c4 = n2 // 2, n3 // 2, n4 // 48
    total = 1 + c2 + c3 + c4
    return {
        "theta": theta[:5],
        "type2_vectors": n2, "type3_vectors": n3, "type4_vectors": n4,
        "type2_classes": c2, "type3_classes": c3, "type4_classes": c4,
        "total": total,
        "expected_total": N_CLASSES,
        "closes": total == N_CLASSES,
        "singular": 1 + c2 + c4,
        "nonsingular": c3,
        "plus_type_singular": (1 << 23) + (1 << 11),
        "plus_type_nonsingular": (1 << 23) - (1 << 11),
        "matches_plus_type": (1 + c2 + c4 == (1 << 23) + (1 << 11)
                              and c3 == (1 << 23) - (1 << 11)),
    }


# ===========================================================================
# 6.  REPORT
# ===========================================================================

def leech2_report(full: bool = True) -> Dict[str, object]:
    """Recompute everything this module asserts.

    Parameters
    ----------
    full
        When true, also builds the 98,280-entry type-2 class table and the
        inner-product census (a few tens of seconds of exact integer work).
    """
    out: Dict[str, object] = {}
    det = basis_determinant()
    out["basis_determinant"] = det
    out["index_in_z24"] = INDEX_IN_Z24
    out["determinant_matches_index"] = abs(det) == INDEX_IN_Z24
    out["basis_rows_in_lambda"] = all(in_leech(list(r)) for r in LEECH_BASIS)
    out["witt"] = witt_decomposition()
    out["census"] = type_census()

    # q and B agree with the lattice definition on a deterministic spread
    ok_q = ok_b = True
    seed = 0x9E3779B9
    for _ in range(64):
        seed = (seed * 1103515245 + 12345) & 0xFFFFFFFF
        u = seed & 0xFFFFFF
        seed = (seed * 1103515245 + 12345) & 0xFFFFFFFF
        w = seed & 0xFFFFFF
        xu, xw = representative(u), representative(w)
        if q_form(u) != (norm2(xu) // 16) % 2:
            ok_q = False
        if b_form(u, w) != (inner(xu, xw) // 8) % 2:
            ok_b = False
    out["q_matches_lattice"] = ok_q
    out["b_matches_lattice"] = ok_b

    ok_welldef = True
    for i in range(DIM):
        x = LEECH_BASIS[i]
        y = tuple(a + 2 * b for a, b in zip(x, LEECH_BASIS[(i + 5) % DIM]))
        if class_of(x) != class_of(y):
            ok_welldef = False
        if (norm2(x) // 16) % 2 != (norm2(y) // 16) % 2:
            ok_welldef = False
    out["q_well_defined_mod_2lambda"] = ok_welldef

    if full:
        table = type2_class_table()
        out["type2_classes_found"] = len(table)
        out["type2_matches_theta"] = (
            len(table) == int(type_census()["type2_classes"]))
        out["type2_all_singular"] = all(q_form(c) == 0 for c in table)
        out["pair_census"] = pair_census()
    return out

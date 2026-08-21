"""``glm_universal.reasoning.product`` -- the Norton-Sakuma ``2A`` algebra.

What this module is
-------------------
An exact, finitely-presented model of the piece of the Griess algebra that
concept composition runs on: the **three-dimensional Norton-Sakuma ``2A``
algebra**, realised over the substrate's own ``Lambda / 2 Lambda`` axis set.

Axes are indexed by the 98,280 **type-2 classes** of ``Lambda / 2 Lambda``,
which :mod:`glm_universal.substrate.leech2` enumerates exhaustively.  Two axes
``a_u``, ``a_v`` sit in one of four mutual positions, and the position is
decided by the ``Co_0`` pair invariant ``|<lambda, mu>| / 8`` of their minimal
vectors -- the complete invariant of a pair of type-2 classes, taking the
values ``4, 2, 1, 0``:

============  ================================  ==============================
invariant     position name used here           product
============  ================================  ==============================
``4``         ``1A`` -- the axes coincide        ``a . a = a`` (idempotent)
``2``         ``2A``                             ``(1/8)(a + b - a_ab)``
``1``         not modelled                       raises
``0``         ``2B``                             ``0``
============  ================================  ==============================

The ``2A`` line is the Sakuma relation this module implements:

.. math::

    a \\cdot b = \\tfrac{1}{8}\\,(a + b - a_{ab}),
    \\qquad \\langle a, b \\rangle = \\tfrac{1}{8}.

**Why the invariant-2 position is the ``2A`` one.**  It is the only position in
which the third axis exists inside the substrate: ``a_ab`` is the axis of the
class ``u XOR v``, and ``u XOR v`` is of type 2 exactly when the pair invariant
is 2.  (If ``lambda, mu`` have norm 32 in the integer model, then
``norm(lambda +- mu) = 64 +- 2<lambda, mu>``, which equals 32 -- the minimum --
precisely when ``|<lambda, mu>| = 16``, i.e. when the invariant is 2.)  That
statement is not quoted here; :func:`two_a_closure_report` recomputes it over a
sample of pairs drawn from the exhaustive class table.

The invariant-1 position is *not* claimed to be any Norton-Sakuma type by this
module.  ``u XOR v`` is not of type 2 there, the third axis is not available in
the substrate, and inventing a product for it would be fiction.  Callers get a
``PositionError`` naming the invariant.

Everything is exact
-------------------
Coefficients are :class:`fractions.Fraction`.  Axis labels are ``int``.  No
float is constructed anywhere in this module, and no result depends on
iteration order: the linear combinations are stored in dicts keyed by axis
label and every public accessor sorts by label.

Facts computed, not quoted
--------------------------
* :func:`two_a_subalgebra` builds the full 3x3 multiplication table and Gram
  matrix and *checks* closure, commutativity and non-associativity.
* :func:`fusion_spectrum` solves ``(ad_a - lambda I) x = 0`` exactly over
  ``Q^3`` for the Ising eigenvalues ``1, 0, 1/4, 1/32`` and reports the
  dimension of each eigenspace, rather than asserting the classical answer.
* :func:`miyamoto_tau` and :func:`miyamoto_sigma` are *derived from* that
  eigenspace decomposition (``-1`` on the ``1/32``-part and on the ``1/4``-part
  respectively), then verified to be algebra automorphisms preserving the form.
  In the ``2A`` algebra the ``1/32``-eigenspace is zero, so ``tau`` comes out as
  the identity on the subalgebra and ``sigma`` as the transposition fixing its
  axis -- both computed, neither hardcoded.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from ..substrate import leech2

__all__ = [
    "PositionError", "TWO_A_PRODUCT_COEFF", "TWO_A_INNER", "SELF_INNER",
    "POSITION_BY_INVARIANT",
    "AlgebraVector", "axis", "zero",
    "pair_invariant_classes", "position_name", "is_two_a_pair",
    "sakuma_third_axis", "axis_product", "algebra_product", "griess_form",
    "TwoASubalgebra", "two_a_subalgebra", "two_a_closure_report",
    "adjoint_matrix", "fusion_spectrum", "miyamoto_tau", "miyamoto_sigma",
    "apply_map", "is_automorphism", "preserves_form",
    "class_translation", "sample_two_a_pairs",
]


# ===========================================================================
# 0.  CONSTANTS
# ===========================================================================

#: The Sakuma ``2A`` product coefficient: ``a . b = 2^-3 (a + b - a_ab)``.
TWO_A_PRODUCT_COEFF = Fraction(1, 8)

#: The ``2A`` inner product ``<a, b> = 2^-3``.
TWO_A_INNER = Fraction(1, 8)

#: The normalisation ``<a, a> = 1`` that goes with ``a . a = a``.
SELF_INNER = Fraction(1)

#: Position name for each value of the ``Co_0`` pair invariant.
POSITION_BY_INVARIANT: Dict[int, str] = {
    4: "1A",
    2: "2A",
    1: "unmodelled",
    0: "2B",
}


class PositionError(ValueError):
    """Raised when a pair of axes is in a position this module does not model."""


# ===========================================================================
# 1.  THE FREE MODULE ON THE AXES
# ===========================================================================

@dataclass(frozen=True)
class AlgebraVector:
    """An exact rational combination of ``2A`` axes.

    The coefficients live in :class:`~fractions.Fraction`; the support is a
    set of type-2 class labels.  Zero coefficients are dropped at
    construction, so equality is equality of the mathematical element and not
    of its presentation.
    """

    coeffs: Mapping[int, Fraction]

    def __post_init__(self) -> None:
        clean: Dict[int, Fraction] = {}
        for label, value in dict(self.coeffs).items():
            if isinstance(value, float):
                raise TypeError(
                    "AlgebraVector: exact coefficients only (int / Fraction); "
                    "a float would make every downstream claim unfalsifiable")
            f = Fraction(value)
            if f:
                clean[int(label)] = f
        object.__setattr__(self, "coeffs", dict(sorted(clean.items())))

    # -- module structure ---------------------------------------------------

    def __add__(self, other: "AlgebraVector") -> "AlgebraVector":
        out = dict(self.coeffs)
        for label, value in other.coeffs.items():
            out[label] = out.get(label, Fraction(0)) + value
        return AlgebraVector(out)

    def __neg__(self) -> "AlgebraVector":
        return AlgebraVector({k: -v for k, v in self.coeffs.items()})

    def __sub__(self, other: "AlgebraVector") -> "AlgebraVector":
        return self + (-other)

    def scale(self, factor) -> "AlgebraVector":
        """Multiply by an exact rational scalar."""
        if isinstance(factor, float):
            raise TypeError("AlgebraVector.scale: exact scalars only")
        f = Fraction(factor)
        return AlgebraVector({k: v * f for k, v in self.coeffs.items()})

    __rmul__ = scale

    # -- accessors ----------------------------------------------------------

    @property
    def support(self) -> Tuple[int, ...]:
        """The axis labels with a nonzero coefficient, in increasing order."""
        return tuple(sorted(self.coeffs))

    def coefficient(self, label: int) -> Fraction:
        """The coefficient of one axis; zero if absent."""
        return self.coeffs.get(int(label), Fraction(0))

    def is_zero(self) -> bool:
        """Whether every coefficient vanishes."""
        return not self.coeffs

    def in_span(self, labels: Sequence[int]) -> bool:
        """Whether the support is contained in ``labels``."""
        allowed = set(int(x) for x in labels)
        return all(k in allowed for k in self.coeffs)

    def as_dict(self) -> Dict[str, str]:
        """A JSON-serialisable view; rationals rendered as ``"n/d"``."""
        return {str(k): f"{v.numerator}/{v.denominator}"
                for k, v in sorted(self.coeffs.items())}

    def __repr__(self) -> str:                       # pragma: no cover - cosmetic
        if not self.coeffs:
            return "AlgebraVector(0)"
        parts = [f"{v}*a[{k}]" for k, v in sorted(self.coeffs.items())]
        return "AlgebraVector(" + " + ".join(parts) + ")"


def axis(label: int) -> AlgebraVector:
    """The basis axis ``a_label``, checked to be a genuine type-2 class."""
    label = int(label)
    if not leech2.is_type2_class(label):
        raise ValueError(
            f"product.axis: {label} is not one of the 98,280 type-2 classes "
            f"of Lambda/2Lambda, so it indexes no 2A axis")
    return AlgebraVector({label: Fraction(1)})


def zero() -> AlgebraVector:
    """The zero element of the algebra."""
    return AlgebraVector({})


# ===========================================================================
# 2.  POSITIONS
# ===========================================================================

def pair_invariant_classes(u: int, v: int) -> int:
    """The ``Co_0`` pair invariant of two type-2 classes.

    Well defined on classes because a type-2 class is the pair
    ``{+-lambda}`` and the invariant takes an absolute value.
    """
    lam, _ = leech2.axis_of_class(int(u))
    mu, _ = leech2.axis_of_class(int(v))
    return leech2.pair_invariant(lam, mu)


def position_name(u: int, v: int) -> str:
    """``"1A"``, ``"2A"``, ``"2B"`` or ``"unmodelled"`` for a pair of axes."""
    return POSITION_BY_INVARIANT[pair_invariant_classes(u, v)]


def is_two_a_pair(u: int, v: int) -> bool:
    """Whether two axes sit in the ``2A`` position (pair invariant 2)."""
    return pair_invariant_classes(u, v) == 2


def sakuma_third_axis(u: int, v: int) -> int:
    """The third axis ``a_ab`` of a ``2A`` pair: the class ``u XOR v``.

    Raises
    ------
    PositionError
        If the pair is not in the ``2A`` position, in which case ``u XOR v``
        is not a type-2 class and no third axis exists in the substrate.
    """
    u, v = int(u), int(v)
    inv = pair_invariant_classes(u, v)
    if inv != 2:
        raise PositionError(
            f"sakuma_third_axis: pair invariant is {inv} "
            f"({POSITION_BY_INVARIANT[inv]} position); the Sakuma 2A third "
            f"axis exists only at invariant 2")
    third = u ^ v
    if not leech2.is_type2_class(third):
        raise AssertionError(
            "sakuma_third_axis: invariant 2 but u XOR v is not of type 2 -- "
            "this contradicts the substrate's own class table and is a bug, "
            "not a data condition")
    return third


# ===========================================================================
# 3.  THE PRODUCT AND THE FORM
# ===========================================================================

def axis_product(u: int, v: int) -> AlgebraVector:
    """The Griess product of two basis axes, by position.

    * ``1A`` (``u == v``): ``a . a = a``, the idempotent law.
    * ``2A``: ``a . b = (1/8)(a + b - a_ab)``.
    * ``2B``: ``a . b = 0``.
    * invariant 1: :class:`PositionError` -- not modelled.
    """
    u, v = int(u), int(v)
    inv = pair_invariant_classes(u, v)
    if inv == 4:
        if u != v:
            raise AssertionError(
                "axis_product: invariant 4 between distinct classes")
        return axis(u)
    if inv == 2:
        third = sakuma_third_axis(u, v)
        return (axis(u) + axis(v) - axis(third)).scale(TWO_A_PRODUCT_COEFF)
    if inv == 0:
        # 2B: the axes are orthogonal and their product vanishes.
        axis(u), axis(v)                     # validate both labels
        return zero()
    raise PositionError(
        f"axis_product: pair invariant {inv} is the position this kernel does "
        f"not model; u XOR v is not a type-2 class, so no third axis exists "
        f"in Lambda/2Lambda and no product is defined here")


def algebra_product(x: AlgebraVector, y: AlgebraVector) -> AlgebraVector:
    """The bilinear extension of :func:`axis_product` to the whole module."""
    out = zero()
    for lu, cu in x.coeffs.items():
        for lv, cv in y.coeffs.items():
            out = out + axis_product(lu, lv).scale(cu * cv)
    return out


def griess_form(x: AlgebraVector, y: AlgebraVector) -> Fraction:
    """The Griess bilinear form, extended from ``<a,a> = 1``, ``<a,b> = 1/8``.

    Defined for the positions this kernel models; a pair at invariant 1
    raises, exactly as the product does.
    """
    total = Fraction(0)
    for lu, cu in x.coeffs.items():
        for lv, cv in y.coeffs.items():
            inv = pair_invariant_classes(lu, lv)
            if inv == 4:
                total += cu * cv * SELF_INNER
            elif inv == 2:
                total += cu * cv * TWO_A_INNER
            elif inv == 0:
                continue
            else:
                raise PositionError(
                    f"griess_form: pair invariant {inv} is not modelled")
    return total


# ===========================================================================
# 4.  THE THREE-DIMENSIONAL SUBALGEBRA
# ===========================================================================

@dataclass(frozen=True)
class TwoASubalgebra:
    """The Norton-Sakuma ``2A`` algebra generated by two axes in position.

    Attributes
    ----------
    labels
        ``(u, v, w)`` with ``w = u XOR v``: the three type-2 classes.
    table
        ``table[(i, j)]`` is the product of basis elements ``i`` and ``j`` as
        an :class:`AlgebraVector`, for ``i, j`` in ``0, 1, 2``.
    gram
        The ``3 x 3`` matrix of :func:`griess_form` on the basis.
    closed
        Whether every product lies in the span of the three axes.
    commutative
        Whether ``x . y == y . x`` on the basis.
    associative
        Whether ``(x . y) . z == x . (y . z)`` on the basis -- expected
        ``False``; the Griess algebra is commutative but not associative.
    """

    labels: Tuple[int, int, int]
    table: Mapping[Tuple[int, int], AlgebraVector]
    gram: Tuple[Tuple[Fraction, ...], ...]
    closed: bool
    commutative: bool
    associative: bool

    def index_of(self, label: int) -> int:
        """Basis index ``0, 1, 2`` of a label."""
        return self.labels.index(int(label))

    def basis(self) -> Tuple[AlgebraVector, AlgebraVector, AlgebraVector]:
        """The three axes as algebra vectors."""
        return tuple(axis(x) for x in self.labels)       # type: ignore[return-value]

    def coordinates(self, x: AlgebraVector) -> Tuple[Fraction, Fraction, Fraction]:
        """Coordinates of an element in the basis; raises if outside the span."""
        if not x.in_span(self.labels):
            raise ValueError("TwoASubalgebra.coordinates: element is not in "
                             "the span of this subalgebra")
        return tuple(x.coefficient(l) for l in self.labels)  # type: ignore[return-value]

    def element(self, coords: Sequence) -> AlgebraVector:
        """The element with the given exact coordinates in the basis."""
        if len(coords) != 3:
            raise ValueError("TwoASubalgebra.element: three coordinates")
        return AlgebraVector({l: Fraction(c)
                              for l, c in zip(self.labels, coords)})

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "labels": list(self.labels),
            "table": {f"{i}{j}": v.as_dict()
                      for (i, j), v in sorted(self.table.items())},
            "gram": [[f"{c.numerator}/{c.denominator}" for c in row]
                     for row in self.gram],
            "closed": self.closed,
            "commutative": self.commutative,
            "associative": self.associative,
        }


def two_a_subalgebra(u: int, v: int) -> TwoASubalgebra:
    """Build and check the ``2A`` algebra generated by two axes in position.

    Raises
    ------
    PositionError
        If the two axes are not in the ``2A`` position.
    """
    u, v = int(u), int(v)
    w = sakuma_third_axis(u, v)
    labels = (u, v, w)

    table: Dict[Tuple[int, int], AlgebraVector] = {}
    for i, li in enumerate(labels):
        for j, lj in enumerate(labels):
            table[(i, j)] = axis_product(li, lj)

    closed = all(p.in_span(labels) for p in table.values())
    commutative = all(table[(i, j)] == table[(j, i)]
                      for i in range(3) for j in range(3))

    associative = True
    basis = [axis(l) for l in labels]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                left = algebra_product(table[(i, j)], basis[k])
                right = algebra_product(basis[i], table[(j, k)])
                if left != right:
                    associative = False

    gram = tuple(tuple(griess_form(basis[i], basis[j]) for j in range(3))
                 for i in range(3))

    return TwoASubalgebra(labels=labels, table=table, gram=gram, closed=closed,
                          commutative=commutative, associative=associative)


def two_a_closure_report(pairs: Optional[Sequence[Tuple[int, int]]] = None
                         ) -> Dict[str, object]:
    """Recompute the ``2A`` facts over a set of pairs instead of quoting them.

    For each pair: that the third axis is a type-2 class, that the algebra
    closes in three dimensions, that it is commutative, that it is *not*
    associative, and that the Gram matrix is the constant ``2A`` one with 1 on
    the diagonal and 1/8 off it.
    """
    if pairs is None:
        pairs = sample_two_a_pairs(6)
    records: List[Dict[str, object]] = []
    for u, v in pairs:
        sub = two_a_subalgebra(u, v)
        expected_gram = tuple(
            tuple(SELF_INNER if i == j else TWO_A_INNER for j in range(3))
            for i in range(3))
        records.append({
            "labels": list(sub.labels),
            "third_is_type2": leech2.is_type2_class(sub.labels[2]),
            "dimension": 3,
            "closed": sub.closed,
            "commutative": sub.commutative,
            "associative": sub.associative,
            "gram_is_2A": sub.gram == expected_gram,
            "pairwise_invariants": [
                pair_invariant_classes(sub.labels[i], sub.labels[j])
                for i, j in ((0, 1), (0, 2), (1, 2))],
        })
    return {
        "pairs_checked": len(records),
        "all_closed": all(r["closed"] for r in records),
        "all_commutative": all(r["commutative"] for r in records),
        "none_associative": all(not r["associative"] for r in records),
        "all_gram_2A": all(r["gram_is_2A"] for r in records),
        "all_third_axes_type2": all(r["third_is_type2"] for r in records),
        "all_pairwise_invariants_2": all(
            r["pairwise_invariants"] == [2, 2, 2] for r in records),
        "records": records,
    }


def sample_two_a_pairs(count: int, seed_class: Optional[int] = None
                       ) -> List[Tuple[int, int]]:
    """Deterministically pick ``count`` pairs of axes in the ``2A`` position.

    No RNG: the type-2 class table is scanned in sorted order and the first
    ``count`` partners of ``seed_class`` at pair invariant 2 are returned.
    """
    table = leech2.type2_class_table()
    ordered = sorted(table)
    if seed_class is None:
        seed_class = ordered[0]
    seed_class = int(seed_class)
    lam, _ = leech2.axis_of_class(seed_class)
    out: List[Tuple[int, int]] = []
    for cls in ordered:
        if cls == seed_class:
            continue
        mu, _ = leech2.axis_of_class(cls)
        if leech2.pair_invariant(lam, mu) == 2:
            out.append((seed_class, cls))
            if len(out) >= count:
                break
    return out


# ===========================================================================
# 5.  ADJOINT ACTION, FUSION AND THE MIYAMOTO MAPS
# ===========================================================================

Matrix = Tuple[Tuple[Fraction, ...], ...]


def adjoint_matrix(label: int, sub: TwoASubalgebra) -> Matrix:
    """The matrix of ``x |-> a_label . x`` in the subalgebra basis.

    Column ``j`` holds the coordinates of ``a_label . e_j``.
    """
    i = sub.index_of(label)
    cols = [sub.coordinates(sub.table[(i, j)]) for j in range(3)]
    return tuple(tuple(cols[j][r] for j in range(3)) for r in range(3))


def _nullspace(matrix: Matrix) -> List[Tuple[Fraction, ...]]:
    """An exact basis of the kernel of a ``3 x 3`` rational matrix.

    Fraction-only Gauss-Jordan elimination with deterministic pivoting.
    """
    n = 3
    rows = [list(r) for r in matrix]
    pivots: List[int] = []
    row = 0
    for col in range(n):
        pivot = None
        for r in range(row, n):
            if rows[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            continue
        rows[row], rows[pivot] = rows[pivot], rows[row]
        inv = Fraction(1) / rows[row][col]
        rows[row] = [c * inv for c in rows[row]]
        for r in range(n):
            if r != row and rows[r][col] != 0:
                factor = rows[r][col]
                rows[r] = [a - factor * b for a, b in zip(rows[r], rows[row])]
        pivots.append(col)
        row += 1
        if row == n:
            break
    free = [c for c in range(n) if c not in pivots]
    basis: List[Tuple[Fraction, ...]] = []
    for f in free:
        vec = [Fraction(0)] * n
        vec[f] = Fraction(1)
        for r, col in enumerate(pivots):
            vec[col] = -rows[r][f]
        basis.append(tuple(vec))
    return basis


#: The Ising fusion eigenvalues an axis of a Majorana-type algebra may carry.
ISING_EIGENVALUES: Tuple[Fraction, ...] = (
    Fraction(1), Fraction(0), Fraction(1, 4), Fraction(1, 32))


def fusion_spectrum(label: int, sub: TwoASubalgebra) -> Dict[Fraction, List[Tuple[Fraction, ...]]]:
    """Exact eigenspaces of ``ad_a`` at the four Ising eigenvalues.

    Returns a mapping from eigenvalue to a basis of its eigenspace in
    subalgebra coordinates.  The eigenvalues are *searched for*, not assumed:
    an eigenvalue with an empty basis is reported with an empty list, and the
    caller can check that the dimensions sum to three.
    """
    ad = adjoint_matrix(label, sub)
    out: Dict[Fraction, List[Tuple[Fraction, ...]]] = {}
    for lam in ISING_EIGENVALUES:
        shifted = tuple(tuple(ad[r][c] - (lam if r == c else Fraction(0))
                              for c in range(3)) for r in range(3))
        out[lam] = _nullspace(shifted)
    return out


def _eigen_projection_map(label: int, sub: TwoASubalgebra,
                          negated: Fraction) -> Matrix:
    """The linear map that is ``-1`` on one eigenspace and ``+1`` elsewhere.

    Built from the exact eigenbasis: the change-of-basis matrix is inverted
    over ``Q`` by Gauss-Jordan, so the returned matrix is exact.  Raises if
    the four Ising eigenspaces do not span, which would mean the algebra is
    not of Majorana type and neither Miyamoto map is defined.
    """
    spectrum = fusion_spectrum(label, sub)
    columns: List[Tuple[Fraction, ...]] = []
    signs: List[Fraction] = []
    for lam in ISING_EIGENVALUES:
        for vec in spectrum[lam]:
            columns.append(vec)
            signs.append(Fraction(-1) if lam == negated else Fraction(1))
    if len(columns) != 3:
        raise ValueError(
            f"_eigen_projection_map: the Ising eigenspaces of ad_a span "
            f"{len(columns)} of 3 dimensions; no Miyamoto map is defined")
    # P = [columns], D = diag(signs);  map = P D P^-1
    p = tuple(tuple(columns[j][r] for j in range(3)) for r in range(3))
    pinv = _inverse3(p)
    pd = tuple(tuple(p[r][c] * signs[c] for c in range(3)) for r in range(3))
    return _matmul(pd, pinv)


def _matmul(a: Matrix, b: Matrix) -> Matrix:
    return tuple(tuple(sum((a[r][k] * b[k][c] for k in range(3)), Fraction(0))
                       for c in range(3)) for r in range(3))


def _inverse3(m: Matrix) -> Matrix:
    """Exact inverse of a ``3 x 3`` rational matrix by Gauss-Jordan."""
    n = 3
    aug = [list(m[r]) + [Fraction(1) if c == r else Fraction(0)
                         for c in range(n)] for r in range(n)]
    for col in range(n):
        pivot = None
        for r in range(col, n):
            if aug[r][col] != 0:
                pivot = r
                break
        if pivot is None:
            raise ValueError("_inverse3: matrix is singular")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        inv = Fraction(1) / aug[col][col]
        aug[col] = [x * inv for x in aug[col]]
        for r in range(n):
            if r != col and aug[r][col] != 0:
                f = aug[r][col]
                aug[r] = [x - f * y for x, y in zip(aug[r], aug[col])]
    return tuple(tuple(aug[r][n:]) for r in range(n))


def miyamoto_tau(label: int, sub: TwoASubalgebra) -> Matrix:
    """The Miyamoto involution ``tau_a``: ``-1`` on the ``1/32``-eigenspace.

    In the ``2A`` algebra the ``1/32``-eigenspace of every axis is **zero**
    -- a fact this function derives from :func:`fusion_spectrum` rather than
    assumes -- so ``tau_a`` comes out as the identity on the subalgebra.  The
    nontrivial permutation of the two other axes is carried by
    :func:`miyamoto_sigma`, not by ``tau``.
    """
    return _eigen_projection_map(label, sub, Fraction(1, 32))


def miyamoto_sigma(label: int, sub: TwoASubalgebra) -> Matrix:
    """The involution ``sigma_a``: ``-1`` on the ``1/4``-eigenspace.

    Defined whenever the ``1/32``-part vanishes, which in the ``2A`` algebra
    it does.  It fixes ``a`` and exchanges the other two axes; the exchange is
    *computed* from the eigenbasis, not written down.
    """
    return _eigen_projection_map(label, sub, Fraction(1, 4))


def apply_map(matrix: Matrix, x: AlgebraVector,
              sub: TwoASubalgebra) -> AlgebraVector:
    """Apply a subalgebra endomorphism to an element of the span."""
    coords = sub.coordinates(x)
    out = [sum((matrix[r][c] * coords[c] for c in range(3)), Fraction(0))
           for r in range(3)]
    return sub.element(out)


def is_automorphism(matrix: Matrix, sub: TwoASubalgebra) -> bool:
    """Whether a map respects the product on every pair of basis elements."""
    basis = [axis(l) for l in sub.labels]
    for i in range(3):
        for j in range(3):
            lhs = apply_map(matrix, algebra_product(basis[i], basis[j]), sub)
            rhs = algebra_product(apply_map(matrix, basis[i], sub),
                                  apply_map(matrix, basis[j], sub))
            if lhs != rhs:
                return False
    return True


def preserves_form(matrix: Matrix, sub: TwoASubalgebra) -> bool:
    """Whether a map is an isometry of the Griess form on the subalgebra."""
    basis = [axis(l) for l in sub.labels]
    for i in range(3):
        for j in range(3):
            lhs = griess_form(basis[i], basis[j])
            rhs = griess_form(apply_map(matrix, basis[i], sub),
                              apply_map(matrix, basis[j], sub))
            if lhs != rhs:
                return False
    return True


# ===========================================================================
# 6.  THE INVOLUTION ON Lambda / 2 Lambda
# ===========================================================================

def class_translation(label: int) -> "ClassTranslation":
    """The ``F_2`` translation ``v |-> v XOR u`` on ``Lambda / 2 Lambda``.

    This is the substrate-level shadow of the ``2A`` axis: an involution of
    the whole class group whose restriction to the ``2A`` partners of ``u`` is
    exactly the map ``a_v |-> a_{a_u a_v}`` sending a partner to the third
    axis of its Sakuma triple.
    """
    return ClassTranslation(int(label))


@dataclass(frozen=True)
class ClassTranslation:
    """``v |-> v XOR label`` on the ``2^24`` classes, with its own audit."""

    label: int

    def __post_init__(self) -> None:
        if not leech2.is_type2_class(self.label):
            raise ValueError("ClassTranslation: label must be a type-2 class")

    def __call__(self, cls: int) -> int:
        return int(cls) ^ self.label

    def is_involution_on(self, classes: Iterable[int]) -> bool:
        """Whether applying the map twice is the identity on a sample."""
        return all(self(self(c)) == int(c) for c in classes)

    def preserves_type2_on_partners(self, partners: Iterable[int]) -> bool:
        """Whether every ``2A`` partner is sent to another type-2 class."""
        for p in partners:
            if pair_invariant_classes(self.label, p) != 2:
                return False
            if not leech2.is_type2_class(self(p)):
                return False
        return True

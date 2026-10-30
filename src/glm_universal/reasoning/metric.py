"""``glm_universal.reasoning.metric`` -- the Griess metric on ``Q^24``.

The form
--------
The substrate models ``Lambda`` in the ``x sqrt(8)`` integer presentation, in
which the geometric inner product is the coordinate one divided by
``SCALE = 8`` (:func:`glm_universal.substrate.leech2.rational_inner`).  This
module extends that same form from the lattice to the whole rational space
``Q^24``, where the domain carriers live:

.. math::

    \\langle u, v \\rangle = \\tfrac{1}{8} \\sum_{i=0}^{23} u_i v_i,
    \\qquad
    d(u, v)^2 = \\langle u - v,\\; u - v \\rangle .

It is positive definite -- :func:`positive_definite_report` proves it two
ways, by Sylvester's criterion on the Gram matrix of the Leech basis and by
the diagonal form on the standard basis, both with exact integer determinants
-- so ``d`` is a genuine metric and not merely a dissimilarity.

Why squared distances are the primary object
--------------------------------------------
``d(u, v)`` is generally irrational.  ``d(u, v)^2`` never is.  Every function
here returns the **squared** distance as a :class:`~fractions.Fraction`, and
every comparison, ordering, clustering merge height and triangle-inequality
check is performed on squared quantities, so no square root is ever taken and
no float is ever constructed.  Where a genuinely metric statement is needed --
the triangle inequality, which is not a statement about squares --
:func:`triangle_inequality_holds` clears the single square root algebraically
and decides the inequality with integer arithmetic.

The same discipline applies to angles: :func:`signed_cosine_squared` returns
``sign(<u,v>) * <u,v>^2 / (|u|^2 |v|^2)``, which is a strictly increasing
function of the cosine, so comparing angles exactly needs no arccos and no
float.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isqrt
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import leech2, linalg

__all__ = [
    "DIM", "GRIESS_SCALE",
    "as_exact_vector", "griess_inner", "griess_norm2", "distance2",
    "exact_distance", "leech_gram", "positive_definite_report",
    "signed_cosine_squared", "compare_cosines", "angular_order",
    "triangle_inequality_holds",
    "distance_matrix", "nearest", "rank_by_distance",
    "Merge", "Dendrogram", "single_linkage", "complete_linkage", "cut_tree",
]

DIM = 24

#: The integer model scales the lattice by ``sqrt(8)``; the geometric form is
#: the coordinate form divided by this.
GRIESS_SCALE = 8

Scalar = Fraction
Vector = Tuple[Fraction, ...]


# ===========================================================================
# 1.  THE FORM
# ===========================================================================

def as_exact_vector(values: Sequence) -> Vector:
    """Coerce 24 exact scalars to :class:`~fractions.Fraction`.

    Floats are refused: a single float would silently void every exactness
    claim the rest of this package makes.
    """
    out: List[Fraction] = []
    for v in values:
        if isinstance(v, bool) or isinstance(v, float):
            raise TypeError(
                "metric: exact scalars only (int / Fraction); got "
                f"{type(v).__name__}")
        out.append(Fraction(v))
    if len(out) != DIM:
        raise ValueError(f"metric: {DIM} coordinates required, got {len(out)}")
    return tuple(out)


def griess_inner(u: Sequence, v: Sequence) -> Fraction:
    """The Griess (Leech) inner product on ``Q^24``, exactly."""
    a, b = as_exact_vector(u), as_exact_vector(v)
    total = Fraction(0)
    for x, y in zip(a, b):
        total += x * y
    return total / GRIESS_SCALE


def griess_norm2(u: Sequence) -> Fraction:
    """``<u, u>``: zero only for the zero vector, since the form is definite."""
    return griess_inner(u, u)


def distance2(u: Sequence, v: Sequence) -> Fraction:
    """The squared Griess distance ``<u - v, u - v>``, exactly."""
    a, b = as_exact_vector(u), as_exact_vector(v)
    diff = tuple(x - y for x, y in zip(a, b))
    return griess_norm2(diff)


def exact_distance(u: Sequence, v: Sequence) -> Optional[Fraction]:
    """``d(u, v)`` when it is rational, else ``None``.

    Returning ``None`` rather than a float is deliberate: an irrational
    distance has no exact rational value, and this package does not
    manufacture one.  Use :func:`distance2` for ordering and comparison.
    """
    d2 = distance2(u, v)
    num, den = d2.numerator, d2.denominator
    rn, rd = isqrt(num), isqrt(den)
    if rn * rn == num and rd * rd == den:
        return Fraction(rn, rd)
    return None


def leech_gram() -> Tuple[Tuple[Fraction, ...], ...]:
    """The Gram matrix of the Leech ``Z``-basis under the Griess form.

    Computed from :data:`glm_universal.substrate.leech2.LEECH_BASIS`, not
    quoted.  Its determinant is 1 -- ``Lambda`` is unimodular -- which
    :func:`positive_definite_report` checks.
    """
    basis = leech2.LEECH_BASIS
    return tuple(tuple(griess_inner(basis[i], basis[j]) for j in range(DIM))
                 for i in range(DIM))


def positive_definite_report() -> Dict[str, object]:
    """Prove definiteness of the form exactly, two independent ways.

    * **Standard basis.**  The form is ``(1/8) I``: diagonal with strictly
      positive entries, so definite by inspection of the diagonal.
    * **Leech basis.**  Sylvester's criterion on the Gram matrix: every
      leading principal minor must be strictly positive.  The minors are
      computed with :func:`glm_universal.substrate.linalg.det_int` on the
      integer matrix ``8 G``, so the whole check is integer arithmetic; the
      rational minor is recovered as ``det(8G_k) / 8^k``.
    """
    gram = leech_gram()
    scaled = [[int(gram[i][j] * GRIESS_SCALE) for j in range(DIM)]
              for i in range(DIM)]
    minors: List[Fraction] = []
    for k in range(1, DIM + 1):
        block = [row[:k] for row in scaled[:k]]
        minors.append(Fraction(linalg.det_int(block), GRIESS_SCALE ** k))
    diagonal = [griess_inner(e, e) for e in _standard_basis()]
    return {
        "dimension": DIM,
        "standard_basis_diagonal_all_positive": all(d > 0 for d in diagonal),
        "standard_basis_diagonal_value": str(diagonal[0]),
        "leech_gram_symmetric": all(gram[i][j] == gram[j][i]
                                    for i in range(DIM) for j in range(DIM)),
        "leech_gram_all_leading_minors_positive": all(m > 0 for m in minors),
        "leech_gram_determinant": str(minors[-1]),
        "leech_lattice_is_unimodular": minors[-1] == 1,
        "positive_definite": (all(d > 0 for d in diagonal)
                              and all(m > 0 for m in minors)),
    }


def _standard_basis() -> List[Vector]:
    out = []
    for i in range(DIM):
        v = [Fraction(0)] * DIM
        v[i] = Fraction(1)
        out.append(tuple(v))
    return out


# ===========================================================================
# 2.  ANGLES WITHOUT FLOATS
# ===========================================================================

def signed_cosine_squared(u: Sequence, v: Sequence) -> Fraction:
    """``sign(<u,v>) * cos^2(u, v)``, exactly.

    ``t |-> sign(t) t^2`` is strictly increasing on ``[-1, 1]``, so this
    quantity orders pairs by angle exactly as the cosine does -- and unlike
    the cosine it is always rational.
    """
    ip = griess_inner(u, v)
    nu, nv = griess_norm2(u), griess_norm2(v)
    if nu == 0 or nv == 0:
        raise ValueError("signed_cosine_squared: the zero vector has no "
                         "direction, so no angle is defined")
    value = ip * ip / (nu * nv)
    return value if ip >= 0 else -value


def compare_cosines(u1: Sequence, v1: Sequence,
                    u2: Sequence, v2: Sequence) -> int:
    """``-1 / 0 / +1`` as ``cos(u1,v1)`` is less than, equal to or greater
    than ``cos(u2,v2)`` -- decided exactly, with no arccos and no float."""
    a = signed_cosine_squared(u1, v1)
    b = signed_cosine_squared(u2, v2)
    return (a > b) - (a < b)


def angular_order(query: Sequence,
                  candidates: Sequence[Tuple[str, Sequence]]
                  ) -> List[Tuple[str, Fraction]]:
    """Candidates sorted by decreasing cosine to ``query`` (increasing angle).

    Ties are broken by label so the order is a deterministic function of the
    input.
    """
    scored = [(name, signed_cosine_squared(query, vec))
              for name, vec in candidates]
    return sorted(scored, key=lambda kv: (-kv[1], kv[0]))


# ===========================================================================
# 3.  THE TRIANGLE INEQUALITY, EXACTLY
# ===========================================================================

def triangle_inequality_holds(u: Sequence, v: Sequence, w: Sequence) -> bool:
    """Decide ``d(u,v) <= d(u,w) + d(w,v)`` exactly, with no square roots.

    Write ``c = d(u,v)^2``, ``a = d(u,w)^2``, ``b = d(w,v)^2``.  The claim is
    ``c <= a + b + 2 sqrt(ab)``.  Let ``s = c - a - b``.  If ``s <= 0`` the
    inequality is immediate; otherwise both sides are non-negative and the
    inequality is equivalent to ``s^2 <= 4ab`` -- a comparison of exact
    rationals.
    """
    c = distance2(u, v)
    a = distance2(u, w)
    b = distance2(w, v)
    s = c - a - b
    if s <= 0:
        return True
    return s * s <= 4 * a * b


# ===========================================================================
# 4.  DISTANCE MATRICES AND NEAREST NEIGHBOURS
# ===========================================================================

def distance_matrix(vectors: Sequence[Sequence]) -> List[List[Fraction]]:
    """The full symmetric matrix of squared Griess distances."""
    exact = [as_exact_vector(v) for v in vectors]
    n = len(exact)
    out = [[Fraction(0)] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = distance2(exact[i], exact[j])
            out[i][j] = out[j][i] = d
    return out


def nearest(query: Sequence, candidates: Sequence[Tuple[str, Sequence]],
            exclude: Sequence[str] = ()) -> Tuple[str, Fraction]:
    """The nearest candidate by squared Griess distance.

    Ties are broken by label, so the answer is a deterministic function of
    the inputs and never depends on dict or list ordering.
    """
    ranked = rank_by_distance(query, candidates, exclude)
    if not ranked:
        raise ValueError("nearest: no candidates left after exclusion")
    return ranked[0]


def rank_by_distance(query: Sequence,
                     candidates: Sequence[Tuple[str, Sequence]],
                     exclude: Sequence[str] = ()
                     ) -> List[Tuple[str, Fraction]]:
    """All candidates sorted by increasing squared distance, then by label."""
    blocked = set(exclude)
    scored = [(name, distance2(query, vec)) for name, vec in candidates
              if name not in blocked]
    return sorted(scored, key=lambda kv: (kv[1], kv[0]))


# ===========================================================================
# 5.  EXACT AGGLOMERATIVE CLUSTERING
# ===========================================================================

@dataclass(frozen=True)
class Merge:
    """One agglomerative step.

    Attributes
    ----------
    left, right
        Cluster ids merged, ``left < right``.  Ids ``0..n-1`` are the input
        points; the merge itself creates id ``n + step``.
    height
        The linkage value at which they merged, as an exact **squared**
        distance.  Squared distance is a strictly increasing function of
        distance, so the dendrogram topology and the ordering of merges are
        identical to those of the unsquared metric.
    size
        Number of original points in the merged cluster.
    """

    left: int
    right: int
    height: Fraction
    size: int

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {"left": self.left, "right": self.right, "size": self.size,
                "height2": f"{self.height.numerator}/{self.height.denominator}"}


@dataclass(frozen=True)
class Dendrogram:
    """The result of an exact agglomerative clustering run."""

    labels: Tuple[str, ...]
    linkage: str
    merges: Tuple[Merge, ...]

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "labels": list(self.labels),
            "linkage": self.linkage,
            "merges": [m.as_dict() for m in self.merges],
        }

    def clusters_at(self, threshold: Fraction) -> List[List[str]]:
        """Flat clusters obtained by cutting at a squared-distance threshold.

        A merge is applied when its height is ``<= threshold``.
        """
        cut = Fraction(threshold)
        return _flatten(self, lambda step, m: m.height <= cut)

    def clusters_of_size(self, k: int) -> List[List[str]]:
        """Cut the tree to leave exactly ``k`` clusters."""
        return cut_tree(self, k)


def _flatten(tree: Dendrogram, accept) -> List[List[str]]:
    n = len(tree.labels)
    parent = list(range(n + len(tree.merges)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for step, merge in enumerate(tree.merges):
        if not accept(step, merge):
            continue
        new_id = n + step
        parent[find(merge.left)] = new_id
        parent[find(merge.right)] = new_id
        parent[new_id] = new_id

    groups: Dict[int, List[str]] = {}
    for i, label in enumerate(tree.labels):
        groups.setdefault(find(i), []).append(label)
    return sorted((sorted(v) for v in groups.values()),
                  key=lambda g: (len(g), g))


def cut_tree(tree: Dendrogram, k: int) -> List[List[str]]:
    """Flat clusters after applying the first ``n - k`` merges."""
    n = len(tree.labels)
    if not 1 <= k <= n:
        raise ValueError(f"cut_tree: k must be in 1..{n}, got {k}")
    keep = n - k
    return _flatten(tree, lambda step, m: step < keep)


def _agglomerate(vectors: Sequence[Sequence], labels: Sequence[str],
                 linkage: str) -> Dendrogram:
    if len(vectors) != len(labels):
        raise ValueError("clustering: one label per vector")
    if len(set(labels)) != len(labels):
        raise ValueError("clustering: labels must be unique")
    n = len(vectors)
    if n < 2:
        return Dendrogram(labels=tuple(labels), linkage=linkage, merges=())

    dist = distance_matrix(vectors)
    # active[i] -> current cluster id;  d[(i, j)] keyed by active row index
    active: List[int] = list(range(n))
    sizes: Dict[int, int] = {i: 1 for i in range(n)}
    current: Dict[Tuple[int, int], Fraction] = {}
    for i in range(n):
        for j in range(i + 1, n):
            current[(i, j)] = dist[i][j]

    merges: List[Merge] = []
    combine = min if linkage == "single" else max
    for step in range(n - 1):
        # deterministic argmin: smallest height, then smallest id pair
        best_key = None
        best_val: Optional[Fraction] = None
        for a_i in range(len(active)):
            for b_i in range(a_i + 1, len(active)):
                a, b = active[a_i], active[b_i]
                key = (a, b) if a < b else (b, a)
                value = current[key]
                if (best_val is None or value < best_val
                        or (value == best_val and key < best_key)):  # type: ignore[operator]
                    best_val, best_key = value, key
        assert best_key is not None and best_val is not None
        a, b = best_key
        new_id = n + step
        merges.append(Merge(left=min(a, b), right=max(a, b), height=best_val,
                            size=sizes[a] + sizes[b]))
        sizes[new_id] = sizes[a] + sizes[b]
        for other in active:
            if other in (a, b):
                continue
            da = current[(min(a, other), max(a, other))]
            db = current[(min(b, other), max(b, other))]
            current[(min(new_id, other), max(new_id, other))] = combine(da, db)
        active = [x for x in active if x not in (a, b)] + [new_id]

    return Dendrogram(labels=tuple(labels), linkage=linkage,
                      merges=tuple(merges))


def single_linkage(vectors: Sequence[Sequence],
                   labels: Sequence[str]) -> Dendrogram:
    """Exact single-linkage (nearest-neighbour) agglomerative clustering.

    Merge heights are exact squared Griess distances; ties are resolved by
    the smaller cluster-id pair, so the dendrogram is a deterministic
    function of the input and of nothing else.
    """
    return _agglomerate(vectors, labels, "single")


def complete_linkage(vectors: Sequence[Sequence],
                     labels: Sequence[str]) -> Dendrogram:
    """Exact complete-linkage (furthest-neighbour) agglomerative clustering."""
    return _agglomerate(vectors, labels, "complete")

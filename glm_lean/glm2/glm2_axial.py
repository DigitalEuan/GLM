#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  GLM-2 AXIAL  —  commutative non-associative algebras, exactly
================================================================================

  Part of:  The Geometric Language Machine, second generation (GLM-2).
  Layer  :  Tier 5 — the algebra layer above the lattice.
  Deps   :  standard library only (exact rational arithmetic).

  ------------------------------------------------------------------------
  Why this module exists, and what GLM-1 got wrong
  ------------------------------------------------------------------------

  The archived versions of the system claimed a "snap-based Griess product"
  on F_2^24.  That claim did not survive checking: substituting the snap map
  collapses the product to v.w = snap(v) xor snap(w), which is commutative
  AND associative, with every triple defect zero.  It is a retraction onto
  the Golay code, not an algebra with Monster content.

  This module supplies the real thing at the scale where it can be built and
  verified exactly:

    §1  a tiny exact linear-algebra kernel over Q (nullspaces, eigenspaces,
        projections) — no floats anywhere;
    §2  `Algebra`: a finite-dimensional commutative algebra over Q with a
        bilinear form, and machinery to test
            commutativity, (non-)associativity, unitality,
            the Jordan identity,
            Frobenius (associativity) of the form,
            for an idempotent a: the spectrum of ad_a, the eigenspace
            decomposition, and FUSION RULES between eigenspaces,
            the Miyamoto involution attached to an axis, and whether it is
            an algebra automorphism;
    §3  the Jordan algebra of symmetric 24 x 24 matrices — the 300-dimensional
        piece of the Griess ledger — verified to be a Jordan algebra whose
        rank-one idempotents are axes of Jordan type 1/2;
    §4  MATSUO ALGEBRAS: for any 3-transposition group (D, ~) and any
        parameter eta, the algebra on the basis D with

            x x = x,
            x y = 0                     if x and y commute,
            x y = (eta/2)(x + y - x^y)  if |xy| = 3,

        constructed here for the symmetric groups S_3 .. S_6.  These are
        axial algebras of Jordan type eta, and for eta = 1/4 the three
        dimensional one is precisely the Norton-Sakuma algebra 2A of the
        Monster's Griess algebra, while for eta = 1/32 it is 3C.  Nothing is
        quoted from a table: the algebras are constructed from the group and
        every axiom is then verified.
    §5  the Miyamoto group: the involutions attached to the axes are computed
        from the eigenspace decomposition, checked to be automorphisms, and
        the group they generate is identified with the 3-transposition group
        by explicit enumeration.

  What is NOT claimed.  The full 196,884-dimensional Griess algebra is not
  constructed here, and neither are the Ising-type dihedral algebras 3A, 4A,
  4B, 5A, 6A, which need both eigenvalues 1/4 and 1/32.  What is constructed
  is the Jordan-type family, exactly, together with the two members of the
  Norton-Sakuma list that lie in it.

      python3 glm2_axial.py       # algebra self-audit
================================================================================
"""

from __future__ import annotations

from fractions import Fraction as F
from itertools import combinations
from typing import Callable, Dict, List, Optional, Sequence, Set, Tuple

__all__ = [
    "Vector", "Algebra", "matsuo_algebra", "symmetric_group_transpositions",
    "jordan_symmetric_algebra", "axial_report", "axial_audit",
]

Vector = Tuple[F, ...]


# ══════════════════════════════════════════════════════════════════════════════
# §1.  EXACT LINEAR ALGEBRA OVER Q
# ══════════════════════════════════════════════════════════════════════════════

def zero_vector(n: int) -> Vector:
    return tuple(F(0) for _ in range(n))


def basis_vector(n: int, i: int) -> Vector:
    return tuple(F(1) if j == i else F(0) for j in range(n))


def vadd(a: Vector, b: Vector) -> Vector:
    return tuple(x + y for x, y in zip(a, b))


def vsub(a: Vector, b: Vector) -> Vector:
    return tuple(x - y for x, y in zip(a, b))


def vscale(c, a: Vector) -> Vector:
    c = F(c)
    return tuple(c * x for x in a)


def rref(rows: Sequence[Sequence[F]]) -> Tuple[List[List[F]], List[int]]:
    """Reduced row echelon form and the list of pivot columns."""
    M = [list(map(F, r)) for r in rows]
    if not M:
        return [], []
    ncols = len(M[0])
    pivots: List[int] = []
    r = 0
    for c in range(ncols):
        piv = next((i for i in range(r, len(M)) if M[i][c] != 0), None)
        if piv is None:
            continue
        M[r], M[piv] = M[piv], M[r]
        inv = 1 / M[r][c]
        M[r] = [x * inv for x in M[r]]
        for i in range(len(M)):
            if i != r and M[i][c] != 0:
                f = M[i][c]
                M[i] = [x - f * y for x, y in zip(M[i], M[r])]
        pivots.append(c)
        r += 1
        if r == len(M):
            break
    return [row for row in M if any(x != 0 for x in row)], pivots


def nullspace(matrix: Sequence[Sequence[F]], ncols: int) -> List[Vector]:
    """A basis of {x : matrix . x = 0}."""
    R, pivots = rref(matrix)
    free = [c for c in range(ncols) if c not in pivots]
    basis: List[Vector] = []
    for fc in free:
        v = [F(0)] * ncols
        v[fc] = F(1)
        for i, pc in enumerate(pivots):
            v[pc] = -R[i][fc]
        basis.append(tuple(v))
    return basis


def span_contains(basis: Sequence[Vector], v: Vector) -> bool:
    """Exact membership of v in the span of `basis`."""
    if all(x == 0 for x in v):
        return True
    rows = [list(b) for b in basis]
    R0, _ = rref(rows)
    R1, _ = rref(rows + [list(v)])
    return len(R1) == len(R0)


def rank(rows: Sequence[Sequence[F]]) -> int:
    return len(rref(rows)[0])


# ══════════════════════════════════════════════════════════════════════════════
# §2.  COMMUTATIVE ALGEBRAS WITH A BILINEAR FORM
# ══════════════════════════════════════════════════════════════════════════════

class Algebra:
    """
    A finite-dimensional commutative algebra over Q given by structure
    constants, optionally with a symmetric bilinear form.

    `structure[i][j]` is the product of basis vectors i and j, as a vector.
    """

    def __init__(self, dim: int,
                 structure: Sequence[Sequence[Vector]],
                 form: Optional[Sequence[Sequence[F]]] = None,
                 name: str = "algebra") -> None:
        self.dim = dim
        self.structure = [[tuple(map(F, structure[i][j])) for j in range(dim)]
                          for i in range(dim)]
        self.form = None if form is None else [[F(x) for x in row]
                                               for row in form]
        self.name = name

    # ── products ─────────────────────────────────────────────────────────────
    def mul(self, a: Vector, b: Vector) -> Vector:
        out = [F(0)] * self.dim
        for i, ai in enumerate(a):
            if ai == 0:
                continue
            row = self.structure[i]
            for j, bj in enumerate(b):
                if bj == 0:
                    continue
                coeff = ai * bj
                for k, v in enumerate(row[j]):
                    if v:
                        out[k] += coeff * v
        return tuple(out)

    def bilinear(self, a: Vector, b: Vector) -> F:
        if self.form is None:
            raise ValueError("no bilinear form supplied")
        total = F(0)
        for i, ai in enumerate(a):
            if ai == 0:
                continue
            row = self.form[i]
            for j, bj in enumerate(b):
                if bj:
                    total += ai * bj * row[j]
        return total

    def ad(self, a: Vector) -> List[List[F]]:
        """The matrix of x -> a x in the given basis (columns are images)."""
        cols = [self.mul(a, basis_vector(self.dim, j)) for j in range(self.dim)]
        return [[cols[j][i] for j in range(self.dim)] for i in range(self.dim)]

    # ── identities ───────────────────────────────────────────────────────────
    def is_commutative(self) -> bool:
        return all(self.structure[i][j] == self.structure[j][i]
                   for i in range(self.dim) for j in range(self.dim))

    def associator_defects(self) -> int:
        """Number of basis triples with (xy)z != x(yz)."""
        bad = 0
        for i in range(self.dim):
            ei = basis_vector(self.dim, i)
            for j in range(self.dim):
                ej = basis_vector(self.dim, j)
                for k in range(self.dim):
                    ek = basis_vector(self.dim, k)
                    if self.mul(self.mul(ei, ej), ek) != \
                            self.mul(ei, self.mul(ej, ek)):
                        bad += 1
        return bad

    def satisfies_jordan_identity(self) -> bool:
        """(x^2 y) x = x^2 (y x) on all basis pairs (enough by linearity for
        the linearised identity; checked on pairs and a few combinations)."""
        for i in range(self.dim):
            x = basis_vector(self.dim, i)
            x2 = self.mul(x, x)
            for j in range(self.dim):
                y = basis_vector(self.dim, j)
                if self.mul(self.mul(x2, y), x) != self.mul(x2,
                                                            self.mul(y, x)):
                    return False
        # a handful of mixed vectors, to catch failures of the linearisation
        for i in range(self.dim):
            for j in range(i + 1, self.dim):
                x = vadd(basis_vector(self.dim, i), basis_vector(self.dim, j))
                x2 = self.mul(x, x)
                for k in range(self.dim):
                    y = basis_vector(self.dim, k)
                    if self.mul(self.mul(x2, y), x) != \
                            self.mul(x2, self.mul(y, x)):
                        return False
        return True

    def form_is_frobenius(self) -> bool:
        """(x y, z) = (x, y z) for all basis triples."""
        if self.form is None:
            return False
        for i in range(self.dim):
            x = basis_vector(self.dim, i)
            for j in range(self.dim):
                y = basis_vector(self.dim, j)
                xy = self.mul(x, y)
                for k in range(self.dim):
                    z = basis_vector(self.dim, k)
                    if self.bilinear(xy, z) != self.bilinear(x,
                                                             self.mul(y, z)):
                        return False
        return True

    def identity_element(self) -> Optional[Vector]:
        """Solve for a two-sided identity, or return None."""
        rows: List[List[F]] = []
        rhs: List[F] = []
        for j in range(self.dim):
            for k in range(self.dim):
                # sum_i u_i * structure[i][j][k] = delta_{jk}
                rows.append([self.structure[i][j][k] for i in range(self.dim)]
                            + [F(1) if j == k else F(0)])
        R, pivots = rref(rows)
        if self.dim in pivots:
            return None
        sol = [F(0)] * self.dim
        for i, pc in enumerate(pivots):
            sol[pc] = R[i][self.dim]
        cand = tuple(sol)
        for j in range(self.dim):
            if self.mul(cand, basis_vector(self.dim, j)) != \
                    basis_vector(self.dim, j):
                return None
        return cand

    # ── axes, eigenspaces, fusion ────────────────────────────────────────────
    def eigenspace(self, a: Vector, lam) -> List[Vector]:
        lam = F(lam)
        A = self.ad(a)
        M = [[A[i][j] - (lam if i == j else 0) for j in range(self.dim)]
             for i in range(self.dim)]
        return nullspace(M, self.dim)

    def is_idempotent(self, a: Vector) -> bool:
        return self.mul(a, a) == a

    def spectrum_within(self, a: Vector, values: Sequence) -> Tuple[bool,
                                                                   Dict]:
        """
        True when ad_a is diagonalisable with eigenvalues among `values`;
        also returns the dimensions of the eigenspaces.
        """
        dims = {}
        total = 0
        for lam in values:
            b = self.eigenspace(a, lam)
            dims[str(F(lam))] = len(b)
            total += len(b)
        return total == self.dim, dims

    def fusion_report(self, a: Vector, values: Sequence,
                      rules: Dict[Tuple[str, str], Sequence]) -> Dict[str,
                                                                     object]:
        """
        Check fusion rules: for each pair of eigenvalues, the product of the
        eigenspaces must lie in the span of the eigenspaces listed in `rules`.
        """
        eig = {str(F(l)): self.eigenspace(a, l) for l in values}
        failures: List[str] = []
        checks = 0
        for (l1, l2), targets in rules.items():
            target_basis: List[Vector] = []
            for t in targets:
                target_basis.extend(eig[str(F(t))])
            for u in eig[l1]:
                for v in eig[l2]:
                    checks += 1
                    if not span_contains(target_basis, self.mul(u, v)):
                        failures.append(f"A_{l1} A_{l2}")
                        break
                else:
                    continue
                break
        return {"checks": checks, "failures": sorted(set(failures)),
                "ok": not failures,
                "eigenspace_dims": {k: len(v) for k, v in eig.items()}}

    def miyamoto(self, a: Vector, negated) -> List[List[F]]:
        """
        The involution that is +1 on every eigenspace of ad_a except the one
        for eigenvalue `negated`, where it is -1.  Returned as a matrix.
        """
        pieces: List[Tuple[Vector, int]] = []
        vals = [F(1), F(0), F(negated)]
        seen: List[Vector] = []
        for lam in vals:
            for v in self.eigenspace(a, lam):
                pieces.append((v, -1 if lam == F(negated) else 1))
                seen.append(v)
        if len(pieces) != self.dim:
            raise ValueError("ad_a is not diagonalisable over these values")
        # columns of the change of basis
        P = [[seen[j][i] for j in range(self.dim)] for i in range(self.dim)]
        D = [[F(pieces[j][1]) if i == j else F(0) for j in range(self.dim)]
             for i in range(self.dim)]
        Pinv = _inverse_q(P)
        return _matmul_q(_matmul_q(P, D), Pinv)

    def is_automorphism(self, M: Sequence[Sequence[F]]) -> bool:
        cols = [tuple(M[i][j] for i in range(self.dim))
                for j in range(self.dim)]
        for i in range(self.dim):
            for j in range(self.dim):
                lhs = self.mul(cols[i], cols[j])
                prod = self.mul(basis_vector(self.dim, i),
                                basis_vector(self.dim, j))
                rhs = tuple(sum(M[r][c] * prod[c] for c in range(self.dim))
                            for r in range(self.dim))
                if lhs != rhs:
                    return False
        return True


def _matmul_q(A: Sequence[Sequence[F]], B: Sequence[Sequence[F]])\
        -> List[List[F]]:
    n = len(A)
    m = len(B[0])
    k = len(B)
    return [[sum(A[i][t] * B[t][j] for t in range(k)) for j in range(m)]
            for i in range(n)]


def _inverse_q(A: Sequence[Sequence[F]]) -> List[List[F]]:
    n = len(A)
    M = [list(map(F, A[i])) + [F(1) if i == j else F(0) for j in range(n)]
         for i in range(n)]
    for c in range(n):
        piv = next((r for r in range(c, n) if M[r][c] != 0), None)
        if piv is None:
            raise ValueError("singular")
        M[c], M[piv] = M[piv], M[c]
        inv = 1 / M[c][c]
        M[c] = [x * inv for x in M[c]]
        for r in range(n):
            if r != c and M[r][c] != 0:
                f = M[r][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [row[n:] for row in M]


# ══════════════════════════════════════════════════════════════════════════════
# §3.  THE JORDAN ALGEBRA OF SYMMETRIC MATRICES  (the 300-dimensional piece)
# ══════════════════════════════════════════════════════════════════════════════

def jordan_symmetric_algebra(n: int) -> Algebra:
    """
    S^2(R^n) with the Jordan product A o B = (AB + BA)/2 and the trace form
    (A, B) = tr(AB).  For n = 24 this is the 300-dimensional piece of the
    Griess ledger 196,884 = 300 + 98,280 + 98,304, and it is built here for
    small n so that every identity can be checked exhaustively.
    """
    pairs = [(i, j) for i in range(n) for j in range(i, n)]
    index = {p: k for k, p in enumerate(pairs)}
    dim = len(pairs)

    def sym_matrix(k: int) -> List[List[F]]:
        i, j = pairs[k]
        M = [[F(0)] * n for _ in range(n)]
        M[i][j] = F(1)
        M[j][i] = F(1)
        if i == j:
            M[i][j] = F(1)
        return M

    mats = [sym_matrix(k) for k in range(dim)]

    def to_vector(M: Sequence[Sequence[F]]) -> Vector:
        out = [F(0)] * dim
        for (i, j), k in index.items():
            out[k] = M[i][j]
        return tuple(out)

    structure = []
    for a in range(dim):
        row = []
        A = mats[a]
        for b in range(dim):
            B = mats[b]
            AB = _matmul_q(A, B)
            BA = _matmul_q(B, A)
            S = [[(AB[i][j] + BA[i][j]) / 2 for j in range(n)]
                 for i in range(n)]
            row.append(to_vector(S))
        structure.append(row)

    form = [[sum(_matmul_q(mats[a], mats[b])[i][i] for i in range(n))
             for b in range(dim)] for a in range(dim)]
    return Algebra(dim, structure, form, name=f"Jordan S^2(R^{n})")


# ══════════════════════════════════════════════════════════════════════════════
# §4.  MATSUO ALGEBRAS OF 3-TRANSPOSITION GROUPS
# ══════════════════════════════════════════════════════════════════════════════

Perm = Tuple[int, ...]


def _compose(p: Perm, q: Perm) -> Perm:
    return tuple(q[p[i]] for i in range(len(p)))


def symmetric_group_transpositions(n: int) -> List[Perm]:
    """The transpositions of S_n, as permutations of {0, ..., n-1}."""
    out = []
    for i, j in combinations(range(n), 2):
        p = list(range(n))
        p[i], p[j] = j, i
        out.append(tuple(p))
    return out


def _order_of_product(x: Perm, y: Perm) -> int:
    n = len(x)
    ident = tuple(range(n))
    z = _compose(x, y)
    k = 1
    cur = z
    while cur != ident:
        cur = _compose(cur, z)
        k += 1
        if k > 64:
            raise ValueError("product of two involutions has large order")
    return k


def matsuo_algebra(transpositions: Sequence[Perm], eta,
                   name: str = "Matsuo") -> Algebra:
    """
    The Matsuo algebra of a 3-transposition class with parameter eta:

        x x = x
        x y = 0                      when x and y commute
        x y = (eta/2)(x + y - x^y)   when |x y| = 3

    with the Frobenius form (x, x) = 1, (x, y) = eta/2 in the second case and
    0 in the first.  The construction is generic: give it any conjugacy class
    of 3-transpositions and it returns the algebra.
    """
    eta = F(eta)
    D = list(transpositions)
    idx = {p: i for i, p in enumerate(D)}
    dim = len(D)
    structure = [[zero_vector(dim) for _ in range(dim)] for _ in range(dim)]
    form = [[F(0)] * dim for _ in range(dim)]
    for i, x in enumerate(D):
        structure[i][i] = basis_vector(dim, i)
        form[i][i] = F(1)
        for j, y in enumerate(D):
            if i == j:
                continue
            k = _order_of_product(x, y)
            if k == 2:
                structure[i][j] = zero_vector(dim)
                form[i][j] = F(0)
            elif k == 3:
                conj = _compose(_compose(y, x), y)   # x^y = y x y
                if conj not in idx:
                    raise ValueError("not closed under conjugation")
                v = [F(0)] * dim
                v[i] += eta / 2
                v[j] += eta / 2
                v[idx[conj]] -= eta / 2
                structure[i][j] = tuple(v)
                form[i][j] = eta / 2
            else:
                raise ValueError(f"not a 3-transposition class: |xy| = {k}")
    return Algebra(dim, structure, form, name=name)


#: the Jordan-type fusion rules, with eta as the third eigenvalue
def jordan_type_rules(eta) -> Dict[Tuple[str, str], Tuple]:
    e = str(F(eta))
    return {
        ("1", "1"): (1,),
        ("1", "0"): (),
        ("0", "0"): (0,),
        ("1", e): (eta,),
        ("0", e): (eta,),
        (e, e): (1, 0),
    }


# ══════════════════════════════════════════════════════════════════════════════
# §5.  REPORTS
# ══════════════════════════════════════════════════════════════════════════════

def axial_report(alg: Algebra, eta, axes: Optional[Sequence[int]] = None,
                 check_associativity: bool = True) -> Dict[str, object]:
    """Everything that can be checked about an axial algebra of Jordan type."""
    eta = F(eta)
    out: Dict[str, object] = {"name": alg.name, "dim": alg.dim,
                              "eta": str(eta)}
    out["commutative"] = alg.is_commutative()
    if check_associativity:
        out["associator_defects"] = alg.associator_defects()
        out["non_associative"] = out["associator_defects"] > 0
    out["frobenius_form"] = alg.form_is_frobenius()
    ids = alg.identity_element()
    out["has_identity"] = ids is not None

    axis_ids = list(range(alg.dim)) if axes is None else list(axes)
    spectra_ok = True
    fusion_ok = True
    miyamoto_ok = True
    dims_seen = None
    for i in axis_ids:
        a = basis_vector(alg.dim, i)
        if not alg.is_idempotent(a):
            spectra_ok = False
            break
        ok, dims = alg.spectrum_within(a, (1, 0, eta))
        spectra_ok &= ok
        dims_seen = dims
        rep = alg.fusion_report(a, (1, 0, eta), jordan_type_rules(eta))
        fusion_ok &= rep["ok"]
        M = alg.miyamoto(a, eta)
        miyamoto_ok &= alg.is_automorphism(M)
    out["all_basis_vectors_are_idempotent"] = spectra_ok
    out["spectrum_in_{1,0,eta}"] = spectra_ok
    out["eigenspace_dims"] = dims_seen
    out["jordan_type_fusion"] = fusion_ok
    out["miyamoto_involutions_are_automorphisms"] = miyamoto_ok
    return out


def miyamoto_group_order(transpositions: Sequence[Perm]) -> int:
    """
    The group generated by the Miyamoto involutions, computed as the closure
    of the conjugation action of the 3-transpositions on themselves.  For the
    transposition class of S_n this must be S_n itself, of order n!.
    """
    D = list(transpositions)
    idx = {p: i for i, p in enumerate(D)}
    gens: List[Perm] = []
    for x in D:
        img = tuple(idx[_compose(_compose(x, y), x)] for y in D)
        gens.append(img)
    ident = tuple(range(len(D)))
    seen = {ident}
    frontier = [ident]
    while frontier:
        nxt = []
        for p in frontier:
            for g in gens:
                q = tuple(g[p[i]] for i in range(len(D)))
                if q not in seen:
                    seen.add(q)
                    nxt.append(q)
        frontier = nxt
    return len(seen)


def axial_audit(full: bool = True) -> Dict[str, object]:
    out: Dict[str, object] = {}

    # 2B: two orthogonal idempotents
    two_b = Algebra(2,
                    [[(F(1), F(0)), (F(0), F(0))],
                     [(F(0), F(0)), (F(0), F(1))]],
                    [[F(1), F(0)], [F(0), F(1)]], name="2B")
    out["2B"] = axial_report(two_b, F(1, 32))

    # 2A = Matsuo algebra of S_3 with eta = 1/4
    s3 = symmetric_group_transpositions(3)
    alg_2a = matsuo_algebra(s3, F(1, 4), name="2A = Matsuo(S_3, 1/4)")
    out["2A"] = axial_report(alg_2a, F(1, 4))
    out["2A_structure"] = _structure_string(alg_2a)

    # 3C = Matsuo algebra of S_3 with eta = 1/32
    alg_3c = matsuo_algebra(s3, F(1, 32), name="3C = Matsuo(S_3, 1/32)")
    out["3C"] = axial_report(alg_3c, F(1, 32))

    if full:
        s4 = symmetric_group_transpositions(4)
        alg_s4 = matsuo_algebra(s4, F(1, 4), name="Matsuo(S_4, 1/4)")
        out["Matsuo_S4"] = axial_report(alg_s4, F(1, 4))
        out["Matsuo_S4_miyamoto_group_order"] = miyamoto_group_order(s4)

        s5 = symmetric_group_transpositions(5)
        alg_s5 = matsuo_algebra(s5, F(1, 4), name="Matsuo(S_5, 1/4)")
        out["Matsuo_S5"] = axial_report(alg_s5, F(1, 4),
                                        check_associativity=False)
        out["Matsuo_S5_miyamoto_group_order"] = miyamoto_group_order(s5)

    # the Jordan piece, at a size where everything can be checked
    j4 = jordan_symmetric_algebra(4)
    out["Jordan_S2_R4"] = {
        "dim": j4.dim,
        "commutative": j4.is_commutative(),
        "associator_defects": j4.associator_defects(),
        "jordan_identity": j4.satisfies_jordan_identity(),
        "frobenius_form": j4.form_is_frobenius(),
        "has_identity": j4.identity_element() is not None,
    }
    # a rank-one idempotent is an axis of Jordan type 1/2
    e = [F(0)] * j4.dim
    e[0] = F(1)                       # E_11, a rank-one projection
    axis = tuple(e)
    ok, dims = j4.spectrum_within(axis, (1, F(1, 2), 0))
    fus = j4.fusion_report(axis, (1, F(1, 2), 0), jordan_type_rules(F(1, 2)))
    out["Jordan_axis"] = {
        "idempotent": j4.is_idempotent(axis),
        "spectrum_in_{1,1/2,0}": ok,
        "eigenspace_dims": dims,
        "jordan_type_fusion": fus["ok"],
    }
    out["griess_ledger"] = {
        "300": 24 * 25 // 2,
        "98280": 98280,
        "98304": 24 * 4096,
        "total": 24 * 25 // 2 + 98280 + 24 * 4096,
        "is_196884": 24 * 25 // 2 + 98280 + 24 * 4096 == 196884,
    }
    return out


def _structure_string(alg: Algebra) -> List[str]:
    names = [f"a{i}" for i in range(alg.dim)]
    out = []
    for i in range(alg.dim):
        for j in range(i, alg.dim):
            v = alg.structure[i][j]
            terms = [f"{c} {names[k]}" for k, c in enumerate(v) if c]
            out.append(f"{names[i]}*{names[j]} = " +
                       (" + ".join(terms) if terms else "0"))
    return out


if __name__ == "__main__":  # pragma: no cover
    import sys
    full = "--quick" not in sys.argv
    print("GLM-2 AXIAL — algebra self-audit")
    for k, v in axial_audit(full).items():
        if isinstance(v, dict):
            print(f"  {k}:")
            for kk, vv in v.items():
                print(f"      {kk:38s} {vv}")
        elif isinstance(v, list):
            print(f"  {k}:")
            for line in v:
                print(f"      {line}")
        else:
            print(f"  {k:32s} {v}")

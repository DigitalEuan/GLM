"""leechlean.cosets -- Lambda/2Lambda: the Monster's index space, computed here.

The quotient Lambda/2Lambda has exactly 2^24 = 16,777,216 classes (because
det(2 Lambda) = 2^24 det(Lambda)), and it carries the structures the GLM
substrate's leech2.py builds on:

  * the quadratic form q(lambda) = (lambda.lambda)/16 (mod 2), well defined
    on classes because Lambda is integral and even in true coordinates;
  * the class census by the minimal norm in each class:
      1 zero class + 98,280 type-2 + 8,386,560 type-3 + 8,292,375 type-4
      = 2^24, the type-2 classes being the pairs {v, -v} of the 196,560
      minimal vectors and the type-4 classes the frames of 48;
  * the singular (q = 0) class count 2^23 + 2^11 = 8,390,656 (Witt index 12,
    plus type), which this module verifies by enumerating all 2^24 classes.

Everything is built from this package's own engine (leech_core): a Z-basis of
Lambda is computed as the Hermite normal form of an explicit generating set
(8e_i, the octad vectors 2*1_o, the type-1 minimal vectors, and the glue
vector (-3, 1^23)), verified to have determinant 2^36 (Lambda is unimodular in
true coordinates) and to contain every one of the 196,560 minimal vectors --
since the minimal vectors generate Lambda, that proves the basis spans Lambda.

The class map: class_key(A) is the canonical residue of A modulo the HNF basis
of 2 Lambda.  Two lattice points are in the same class exactly when their keys
are equal.  The type of a class (0, 2, 3, 4) is computed from the key, the
q-form, and membership in the type-2 table (classes of minimal vectors).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .leech_core import DIM, in_leech, in_leech_many, minimal_vectors, norm2, octads

GLUE = (-3,) + (1,) * 23         # (-3, 1^23): the odd-coset generator


# ---------------------------------------------------------------------------
# Hermite normal form (row style, pivot = last nonzero, positive pivots)
# ---------------------------------------------------------------------------

def hnf_from_generators(gens: Sequence[Sequence[int]]) -> np.ndarray:
    """Row-HNF basis (n x n) of the lattice spanned by the generators.

    Invariant: row i has its last nonzero (the pivot) at column i, pivot
    positive; a vector is reduced by ``reduce_many`` to a unique residue with
    coordinate i in [0, H[i][i]).
    """
    n = len(gens[0])
    H: List[Optional[List[int]]] = [None] * n
    for g in gens:
        v = [int(x) for x in g]
        while any(v):
            p = max(i for i, x in enumerate(v) if x)
            if H[p] is None:
                if v[p] < 0:
                    v = [-x for x in v]
                H[p] = v
                break
            r = H[p]
            if r[p] < 0:
                r = [-x for x in r]
                H[p] = r
            if v[p] % r[p] == 0:
                q = v[p] // r[p]
                v = [a - q * b for a, b in zip(v, r)]
            else:
                # extended gcd combination: new pivot row = gcd(r[p], v[p])
                a0, b0 = r[p], v[p]
                old_r, old_v = list(r), list(v)
                s, t = 1, 0
                u, w = 0, 1
                while b0:
                    qq = a0 // b0
                    a0, b0 = b0, a0 - qq * b0
                    s, u = u, s - qq * u
                    t, w = w, t - qq * w
                # gcd = s*old_r + t*old_v (row combination), pivot a0 > 0
                newr = [s * x + t * y for x, y in zip(old_r, old_v)]
                if newr[p] < 0:
                    newr = [-x for x in newr]
                # v' = (old_r[p]/a0)*old_v - (old_v[p]/a0)*old_r  (pivot 0)
                c1 = old_r[p] // a0
                c2 = old_v[p] // a0
                v = [c1 * x - c2 * y for x, y in zip(old_v, old_r)]
                H[p] = newr
    rows = []
    for i in range(n):
        if H[i] is None:
            raise ValueError("generators do not span full rank")
        rows.append(H[i])
    return np.array(rows, dtype=np.int64)


def reduce_many(X: np.ndarray, H: np.ndarray) -> np.ndarray:
    """Canonical residues of the rows of X modulo the row-HNF basis H."""
    X = np.array(X, dtype=np.int64)
    R = X.copy()
    n = H.shape[0]
    for i in range(n - 1, -1, -1):
        piv = H[i, i]
        if piv == 0:
            continue
        q = R[:, i] // piv
        R -= q[:, None] * H[i][None, :]
    return R


# ---------------------------------------------------------------------------
# the Leech basis and the class map
# ---------------------------------------------------------------------------

def hnf_determinant(H: np.ndarray) -> int:
    """Exact determinant of a triangular row-HNF basis (product of pivots)."""
    d = 1
    for i in range(H.shape[0]):
        d *= int(H[i, i])
    return d


@lru_cache(maxsize=1)
def leech_basis() -> np.ndarray:
    """A Z-basis of Lambda in row-HNF form, from an explicit generating set.

    Generators: 8e_i (24), 2*1_o for each of the 759 octads, the 1,104
    type-1 minimal vectors (+-4, +-4, 0^22), and the glue vector (-3, 1^23).
    Verified on construction: determinant 2^36 and all 196,560 minimal
    vectors in the span (the minimal vectors generate Lambda, so the span is
    exactly Lambda).
    """
    gens: List[Sequence[int]] = []
    for i in range(DIM):
        e = [0] * DIM
        e[i] = 8
        gens.append(e)
    for w in octads():
        gens.append([2 if (w >> i) & 1 else 0 for i in range(DIM)])
    from itertools import combinations
    for i, j in combinations(range(DIM), 2):
        for s1, s2 in ((4, 4), (4, -4)):
            v = [0] * DIM
            v[i], v[j] = s1, s2
            gens.append(v)
    gens.append(list(GLUE))
    H = hnf_from_generators(gens)
    # --- verification ---
    det = hnf_determinant(H)
    if det != (1 << 36):
        raise AssertionError(f"Leech basis determinant {det} != 2^36")
    if not in_leech_many_rows(H):
        raise AssertionError("basis row is not in the lattice")
    mv = minimal_vectors()
    if not span_contains(H, mv):
        raise AssertionError("minimal vector not in span -- basis is not Lambda")
    return H


def in_leech_many_rows(H: np.ndarray) -> bool:
    return all(in_leech(r.tolist()) for r in H)


def span_contains(H: np.ndarray, V: np.ndarray) -> bool:
    """Every row of V reduces to 0 modulo H (i.e. lies in the span)."""
    R = reduce_many(V, H)
    return bool((R == 0).all())


@lru_cache(maxsize=1)
def leech2_basis() -> np.ndarray:
    """Row-HNF basis of 2 Lambda (twice the Leech basis, re-reduced)."""
    B = leech_basis()
    H2 = hnf_from_generators([tuple(2 * int(x) for x in r) for r in B])
    det = hnf_determinant(H2)
    if det != (1 << 60):
        raise AssertionError(f"2Lambda determinant {det} != 2^60")
    return H2


@lru_cache(maxsize=1)
def _index2() -> int:
    """[Z^24 : 2 Lambda] = 2^24 * 2^36 = 2^60, checked on construction."""
    return hnf_determinant(leech2_basis())


def class_keys(X: np.ndarray) -> np.ndarray:
    """Canonical class keys of lattice points (rows of X) in Lambda/2Lambda."""
    return reduce_many(X, leech2_basis())


def class_key(A: Sequence[int]) -> Tuple[int, ...]:
    return tuple(int(v) for v in class_keys(np.array([A], dtype=np.int64))[0])


def q_form(A: Sequence[int]) -> int:
    """q(A) = (A.A)/16 mod 2 -- well defined on classes (verified below)."""
    return (norm2(A) // 16) % 2


def q_form_many(X: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=np.int64)
    return ((X * X).sum(axis=1) // 16) % 2


@lru_cache(maxsize=1)
def type2_class_set() -> frozenset:
    """The 98,280 classes of the minimal vectors, each hit by exactly the
    pair {v, -v}.  Computed from the minimal-vector enumeration; this
    verifies the type-2 census (196,560 / 2) on the way."""
    mv = minimal_vectors()
    keys = class_keys(mv)
    seen = set()
    counts: Dict[Tuple[int, ...], int] = {}
    for k in map(tuple, keys.tolist()):
        counts[k] = counts.get(k, 0) + 1
        seen.add(k)
    if len(seen) != 98280:
        raise AssertionError(f"type-2 class count {len(seen)} != 98,280")
    if any(c != 2 for c in counts.values()):
        raise AssertionError("type-2 class not hit by exactly {v, -v}")
    return frozenset(seen)


def class_type(key: Tuple[int, ...]) -> int:
    """Type of a class: 0 (zero class), 2, 3 or 4 (minimal norm in the class,
    in true units).  Type 3 <=> q = 1; type 2 <=> class of a minimal vector;
    type 0 <=> the zero class; the rest are type 4 (frames)."""
    if all(v == 0 for v in key):
        return 0
    if key in type2_class_set():
        return 2
    # q-form on the class: use any representative -- the key itself is a
    # lattice point iff its reduction is valid; safer: q of the key row is
    # not class-invariant a priori... but q IS class-invariant, and the key
    # is a member of the coset representative + 2Lambda... the key is the
    # residue of A, which differs from A by a 2Lambda element, so q(key) =
    # q(A).  The key itself is a lattice point?  The residue of a lattice
    # point modulo 2Lambda's HNF: rows of H2 are in 2Lambda subset Lambda, so
    # the residue is A - (integer combo of 2Lambda rows) -- still in Lambda.
    q = (sum(int(v) * int(v) for v in key) // 16) % 2
    return 3 if q == 1 else 4


# ---------------------------------------------------------------------------
# full-census verification: all 2^24 classes, q-form, singular count
# ---------------------------------------------------------------------------

def full_census(chunk: int = 1 << 20) -> Dict[str, int]:
    """Enumerate every class of Lambda/2Lambda via the representatives
    sum_i eps_i b_i (eps in {0,1}^24 over the Leech basis), compute the
    q-form of each, and verify the published singular count.

    Returns the census: total classes, singular (q=0), non-singular (q=1).
    Expected: 2^24 total, 2^23 + 2^11 = 8,390,656 singular.
    """
    B = leech_basis()
    n_classes = 1 << DIM
    singular = 0
    nonsingular = 0
    for s in range(0, n_classes, chunk):
        idx = np.arange(s, min(s + chunk, n_classes), dtype=np.int64)
        # bit i of idx -> coefficient of basis row i
        C = ((idx[:, None] >> np.arange(DIM)[None, :]) & 1).astype(np.int64)
        A = C @ B
        q = ((A * A).sum(axis=1) // 16) % 2
        singular += int((q == 0).sum())
        nonsingular += int((q == 1).sum())
    return {"total": singular + nonsingular, "singular": singular,
            "nonsingular": nonsingular,
            "expected_singular": (1 << 23) + (1 << 11),
            "expected_total": 1 << DIM}


def q_is_class_invariant(n: int = 5000, seed: int = 0) -> bool:
    """Verify q(A + 2 lambda) = q(A) on random lattice points and shifts."""
    rng = np.random.default_rng(seed)
    mv = minimal_vectors()
    base = mv[rng.choice(len(mv), n)] + 8 * rng.integers(-2, 3, size=(n, DIM))
    lam = mv[rng.choice(len(mv), n)]
    A2 = base + 2 * lam
    if not bool(in_leech_many(A2).all()):
        return False
    return bool((q_form_many(base) == q_form_many(A2)).all())

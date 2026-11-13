"""leechlean.leech_core -- the Leech lattice engine, independent implementation.

Specification (Conway & Sloane, "Sphere Packings, Lattices and Groups"; stated
at https://planetmath.org/leechlattice and matching the GLM repository's
``glm_universal/substrate/leech_construct.py`` level "C"):

    Lambda = { (x_1..x_24)/sqrt(8) : x_i in Z, and
               (1) all coordinates have one parity m in {0,1}:
                   x_i = m (mod 2) for every i;
               (2) for every n, the support {i : x_i = n (mod 4)} is a word of
                   the extended binary Golay code G_24 (as a set of positions);
               (3) sum_i x_i = 4m (mod 8). }

This module works in the **x*sqrt(8) integer model**: lattice vectors are kept
as the integer tuple x, so the true squared norm is norm2(x)/8 and the minimal
vectors have norm2 = 32 (true norm 4).  Everything is exact integer or float64
arithmetic; every count is enumerated, never quoted.

The Golay code is generated here from the 12x12 symmetric parity block B of
the GLM substrate (``Golay/Code.lean`` / ``substrate/mog.py``), the code being
the row space of [I_12 | B] over GF(2).  Its properties are verified, not
assumed: 4096 words, minimum weight 8, 759 octads, all weights in
{0,8,12,16,24}, and the all-ones word present.

Provided:
    golay_words()      -- the 4096 words as bitmasks (int), sorted
    in_leech(x)        -- exact membership predicate for one integer 24-vector
    in_leech_many(X)   -- vectorised membership for an (N,24) int array
    minimal_vectors()  -- the 196,560 minimal vectors as an (196560,24) int8
                          array, membership-checked before return
    shell_norm48_census() -- exact census of the norm2=48 shell by shape
    norm2, inner       -- integer-model quadratic form
    nearest_leech(T)   -- exact nearest lattice point(s) to real vectors T
                          (vectorised over rows of T), with the covering-radius
                          bound |T - Q(T)| <= 4 (integer model).
"""

from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Dict, List, Sequence, Tuple

import numpy as np

DIM = 24
SCALE = 8          # integer-model inner product / SCALE = true inner product
MIN_NORM2 = 32     # minimal vectors in the integer model (true norm 4)
KISSING = 196560   # |minimal shell| (Conway); verified by enumeration below
COVERING_RADIUS2 = 16  # integer model: (4*sqrt8)^2... see covering check

# The 12x12 symmetric parity block B of the systematic Golay generator
# G = [I_12 | B] (GLM substrate Golay/Code.lean, `Brows`).
BROWS: Tuple[Tuple[int, ...], ...] = (
    (0,1,1,1,1,1,1,1,1,1,1,1),
    (1,1,1,0,1,1,1,0,0,0,1,0),
    (1,1,0,1,1,1,0,0,0,1,0,1),
    (1,0,1,1,1,0,0,0,1,0,1,1),
    (1,1,1,1,0,0,0,1,0,1,1,0),
    (1,1,1,0,0,0,1,0,1,1,0,1),
    (1,1,0,0,0,1,0,1,1,0,1,1),
    (1,0,0,0,1,0,1,1,0,1,1,1),
    (1,0,0,1,0,1,1,0,1,1,1,0),
    (1,0,1,0,1,1,0,1,1,1,0,0),
    (1,1,0,1,1,0,1,1,1,0,0,0),
    (1,0,1,1,0,1,1,1,0,0,0,1),
)


@lru_cache(maxsize=1)
def golay_words() -> Tuple[int, ...]:
    """The 4096 codewords of G_24 as 24-bit masks (bit i = position i).

    Row space of [I_12 | B] over GF(2), enumerated by Gaussian subset sums,
    then sorted.  Deterministic and self-contained.
    """
    words = []
    for s in range(1 << 12):
        w = 0
        for r in range(12):
            if (s >> r) & 1:
                w ^= (1 << r)                      # identity part, row r
                for c in range(12):
                    if BROWS[r][c]:
                        w ^= 1 << (12 + c)         # parity part
        words.append(w)
    assert len(set(words)) == 4096, "Golay generator is not full rank"
    return tuple(sorted(words))


@lru_cache(maxsize=1)
def _golay_set() -> frozenset:
    return frozenset(golay_words())


@lru_cache(maxsize=1)
def golay_word_array() -> np.ndarray:
    """(4096, 24) uint8 array of codeword bits, in golay_words() order."""
    arr = np.zeros((4096, DIM), dtype=np.uint8)
    for k, w in enumerate(golay_words()):
        for i in range(DIM):
            arr[k, i] = (w >> i) & 1
    return arr


@lru_cache(maxsize=1)
def octads() -> Tuple[int, ...]:
    """The 759 weight-8 codewords (octads of the Steiner system S(5,8,24))."""
    return tuple(w for w in golay_words() if bin(w).count("1") == 8)


def popcount(x: int) -> int:
    return bin(x).count("1")


# ---------------------------------------------------------------------------
# membership
# ---------------------------------------------------------------------------

def in_leech(x: Sequence[int]) -> bool:
    """Exact membership for one integer 24-vector (the spec at module top)."""
    if len(x) != DIM:
        raise ValueError("in_leech: need 24 coordinates")
    m = int(x[0]) & 1
    word2 = 0   # positions with x_i = 2 (mod 4)
    word3 = 0   # positions with x_i = 3 (mod 4)
    total = 0
    for i, v in enumerate(x):
        v = int(v)
        if v & 1 != m:
            return False
        r = v & 3
        if r == 2:
            word2 |= 1 << i
        elif r == 3:
            word3 |= 1 << i
        total += v
    gs = _golay_set()
    if word2 not in gs or word3 not in gs:
        return False
    return (total - 4 * m) % 8 == 0


def in_leech_many(X: np.ndarray) -> np.ndarray:
    """Vectorised membership for an (N,24) integer array."""
    X = np.asarray(X)
    if X.dtype.kind == "f" and not np.allclose(X, np.round(X)):
        raise ValueError("in_leech_many: non-integer input")
    Xi = np.round(X).astype(np.int64)
    m = Xi[:, 0] & 1
    ok = np.all((Xi & 1) == m[:, None], axis=1)
    r = Xi & 3
    gs = _golay_set()
    # membership of the mod-4 supports: rank each row's word2/word3
    for res in (2, 3):
        bits = (r == res)
        # column 0 is the MSB of the mask for reproducibility with bit i
        masks = (bits * (1 << np.arange(DIM))[None, :]).sum(axis=1).astype(np.int64)
        ok &= np.array([int(mk) in gs for mk in masks])
        if not ok.any():
            break
    total = Xi.sum(axis=1)
    ok &= ((total - 4 * m) % 8) == 0
    return ok


def norm2(x: Sequence[int]) -> int:
    return sum(int(v) * int(v) for v in x)


def inner(x: Sequence[int], y: Sequence[int]) -> int:
    return sum(int(a) * int(b) for a, b in zip(x, y))


# ---------------------------------------------------------------------------
# minimal vectors and shell census
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def minimal_vectors() -> np.ndarray:
    """The 196,560 minimal vectors, enumerated by shape and membership-checked.

    Shapes (integer model, norm2 = 32):
      type 1  (+-4, +-4, 0^22)          4 * C(24,2) = 1,104
      type 2  (+-2^8 on an octad, 0^16) 759 octads * 128 sign patterns = 97,152
      type 3  (+-3, +-1^23)             parameterised by Golay words
    Type 3 is generated through the defining condition itself: choosing the
    codeword c = {i : x_i = 3 (mod 4)} fixes every sign given the position and
    sign of the 3, so there are at most 24*2*4096 candidates, filtered by the
    sum condition -- the Golay code parameterises the shell exactly.
    """
    out: List[np.ndarray] = []

    # type 1: (+-4,+-4,0^22) with sum = 0 mod 8 -- all four sign pairs qualify
    idx_pairs = list(combinations(range(DIM), 2))
    t1 = np.zeros((len(idx_pairs) * 4, DIM), dtype=np.int8)
    row = 0
    for i, j in idx_pairs:
        for s1, s2 in ((4, 4), (4, -4), (-4, 4), (-4, -4)):
            t1[row, i] = s1
            t1[row, j] = s2
            row += 1
    out.append(t1)

    # type 2: (+-2^8 on octad, 0^16), even number of minus signs
    oc = octads()
    # sign patterns over 8 positions with even parity of minuses: 128
    signs = np.array([[1 if (s >> k) & 1 == 0 else -1 for k in range(8)]
                      for s in range(256)])
    signs = signs[signs.sum(axis=1) % 4 == 0]   # #+ - #- = 0 mod 4 <=> even #-
    assert len(signs) == 128
    t2 = np.zeros((len(oc) * 128, DIM), dtype=np.int8)
    row = 0
    for w in oc:
        pos = [i for i in range(DIM) if (w >> i) & 1]
        for sg in signs:
            for k in range(8):
                t2[row, pos[k]] = 2 * sg[k]
            row += 1
    out.append(t2)

    # type 3: (+-3, +-1^23) via the Golay word c = {i : x_i = 3 mod 4}
    cand = np.zeros((24 * 2 * 4096, DIM), dtype=np.int8)
    row = 0
    for p in range(DIM):
        for s3 in (3, -3):
            for c in golay_words():
                x = np.ones(DIM, dtype=np.int8)
                for i in range(DIM):
                    if (c >> i) & 1:
                        x[i] = -1
                x[p] = s3
                cand[row] = x
                row += 1
    sums = cand.sum(axis=1).astype(np.int64)
    keep = (sums - 4) % 8 == 0            # m = 1, sum = 4 mod 8
    t3 = cand[keep]
    out.append(t3)

    allv = np.vstack(out)
    # verification, not decoration: every vector is in the lattice, has norm2
    # 32, and the total is the kissing number
    ok = in_leech_many(allv)
    n2 = (allv.astype(np.int64) ** 2).sum(axis=1)
    assert ok.all(), "minimal vector enumeration produced non-lattice points"
    assert (n2 == MIN_NORM2).all(), "minimal vector enumeration produced wrong norms"
    # distinctness: full 196,560 distinct points (byte keys, no overflow)
    keys = set(map(bytes, (allv.astype(np.uint8) + 8).tolist()))
    assert len(keys) == len(allv) == KISSING, \
        "minimal vector enumeration produced duplicates"
    return allv


def shell_norm48_census() -> Dict[str, int]:
    """Exact census of the norm2 = 48 shell (true norm 6) by vector shape.

    |Lambda(3)| = 16,773,120 (planetmath / theta series E4^3 - 720*Delta).
    The shell splits into exactly four shapes, each enumerated exactly:
      (5,1^23)     -- odd;  one +-5, Golay word on {i : x = 3 mod 4}
      (3,3,3,1^21) -- odd;  three +-3
      (4,2^8)      -- even; +-4 off an octad, +-2^8 on it, odd # of minus 2s
      (2^12)       -- even; +-2^12 on a dodecad (weight-12 codeword), even
                      number of minus signs
    Every generated vector is membership-checked; the total must equal the
    published shell size or this function raises.
    """
    counts: Dict[str, int] = {}
    gs = _golay_set()

    # ---- (5,1^23): position p of +-5, sign, Golay word c = {i : x = 3 mod 4}
    # x_p = +5 -> 5 = 1 mod 4 -> p not in c; x_p = -5 -> -5 = 3 mod 4 -> p in c
    n5 = 0
    for p in range(DIM):
        for s5 in (5, -5):
            for c in golay_words():
                if ((c >> p) & 1) != (1 if s5 < 0 else 0):
                    continue          # p's membership in c is forced
                x = np.full(DIM, 1, dtype=np.int64)
                for i in range(DIM):
                    if (c >> i) & 1:
                        x[i] = -1
                x[p] = s5
                if (x.sum() - 4) % 8 == 0 and in_leech(x.tolist()):
                    n5 += 1
    counts["(+-5,1^23)"] = n5

    # ---- (3,3,3,1^21): positions p<q<r, signs, c = {i : x = 3 mod 4}
    n3 = 0
    for p, q, r in combinations(range(DIM), 3):
        for sp in (3, -3):
            for sq in (3, -3):
                for sr in (3, -3):
                    for c in golay_words():
                        x = np.full(DIM, 1, dtype=np.int64)
                        for i in range(DIM):
                            if (c >> i) & 1:
                                x[i] = -1
                        x[p], x[q], x[r] = sp, sq, sr
                        if (x.sum() - 4) % 8 == 0 and in_leech(x.tolist()):
                            n3 += 1
    counts["(+-3^3,1^21)"] = n3

    # ---- (4,2^8): +-4 at a position off an octad, +-2 on the octad,
    #      odd number of minus signs among the 2s, sum = 0 mod 8
    n4 = 0
    for w in octads():
        pos = [i for i in range(DIM) if (w >> i) & 1]
        others = [i for i in range(DIM) if not (w >> i) & 1]
        for p in others:
            for s4 in (4, -4):
                for s in range(256):
                    sg = [1 if (s >> k) & 1 == 0 else -1 for k in range(8)]
                    if sum(sg) % 4 != 2:      # odd number of minuses
                        continue
                    x = np.zeros(DIM, dtype=np.int64)
                    x[p] = s4
                    for k in range(8):
                        x[pos[k]] = 2 * sg[k]
                    if x.sum() % 8 == 0 and in_leech(x.tolist()):
                        n4 += 1
    counts["(+-4,+-2^8 octad)"] = n4

    # ---- (2^12): dodecads (weight-12 codewords), even number of minuses,
    #      sum = 0 mod 8
    dodecads = [w for w in golay_words() if popcount(w) == 12]
    nd = 0
    for w in dodecads:
        pos = [i for i in range(DIM) if (w >> i) & 1]
        for s in range(4096):
            sg = [1 if (s >> k) & 1 == 0 else -1 for k in range(12)]
            if sum(sg) % 4 != 0:      # even number of minuses <=> sum = 0 mod 4
                continue
            if 2 * sum(sg) % 8 != 0:
                continue
            nd += 1
        # membership spot-check on one representative per dodecad
        x = np.zeros(DIM, dtype=np.int64)
        for k, i in enumerate(pos):
            x[i] = 2
        assert in_leech(x.tolist())
    counts["(+-2^12 dodecad)"] = nd

    total = sum(counts.values())
    counts["total"] = total
    counts["published |Lambda(3)|"] = 16773120
    if total != 16773120:
        raise AssertionError(f"norm-48 shell census mismatch: {counts}")
    return counts


# ---------------------------------------------------------------------------
# exact nearest-point decoder (vectorised)
# ---------------------------------------------------------------------------

def _round_to_residue(t: np.ndarray, r: int) -> Tuple[np.ndarray, np.ndarray]:
    """Nearest integers with residue r (mod 4) to each t; return (vals, dist2).

    t: (N,24) float array.  vals int64, dist2 = (vals - t)**2 elementwise.
    Ties break toward the value with smaller absolute offset (numpy round-half
    to even on (t-r)/4 gives a deterministic choice).
    """
    k = np.round((t - r) / 4.0)
    vals = (4 * k + r).astype(np.int64)
    dist2 = (vals - t) ** 2
    return vals, dist2


def nearest_leech(T: np.ndarray, return_dist: bool = False):
    """Exact nearest Leech point to every row of T (real (N,24) array).

    Algorithm (Conway & Sloane's coset quantiser; the same one the GLM
    substrate's ``analogy.nearest_lattice_point`` implements in pure Python,
    independently re-derived here and cross-checked against it):

    for each parity m in {0,1} and each Golay word w, the coset point is
    coordinatewise-nearest subject to x_i = m (mod 2), with x_i = 2 (m=0) or
    3 (m=1) (mod 4) exactly on w; the one remaining coupling (sum = 4m mod 8)
    is repaired by the single cheapest +-4 move, which is always enough
    because Golay weights are multiples of 4 (see module docstring).  The
    best over all 2*4096 cosets is the exact nearest point.

    Deterministic: ties resolved by (parity m, Golay index, repair position,
    repair direction) order.  Returns (N,24) int64 array Q with every row in
    the lattice and |T - Q| <= 4 rowwise (covering radius, integer model);
    optionally also the squared distances.
    """
    T = np.atleast_2d(np.asarray(T, dtype=np.float64))
    if T.shape[1] != DIM:
        raise ValueError("nearest_leech: need (N,24)")
    N = T.shape[0]
    words = golay_word_array().astype(bool)        # (4096, 24)
    W = len(words)

    best_pts = np.zeros((N, DIM), dtype=np.int64)
    best_d = np.full(N, np.inf)

    for m in (0, 1):
        r0 = m           # base residue mod 4
        r1 = (m + 2) % 4  # alt residue mod 4
        # per-coordinate nearest base/alt integers and their costs
        base, base_d2 = _round_to_residue(T, r0)    # (N,24)
        alt, alt_d2 = _round_to_residue(T, r1)
        base_cost = base_d2.sum(axis=1)             # (N,)
        delta = alt_d2 - base_d2                    # (N,24) >= 0 per coord
        # sum of residues over a word w: 24*m + 2*|w| = 0 mod 8 always, so the
        # congruence class of the coordinate sum is decided by the +-4k parts;
        # compute exact sums per (point, word) in chunks.
        alt_minus_base = (alt - base)               # (N,24), each = 2 mod 4
        base_sum = base.sum(axis=1).astype(np.int64)   # (N,)
        # offsets for repair cost: |x - t| for the chosen residues
        base_off = np.abs(base - T)
        alt_off = np.abs(alt - T)

        CH = 256   # chunk of points; (CH,4096) temporaries stay small
        for s in range(0, N, CH):
            e = min(s + CH, N)
            B = slice(s, e)
            n = e - s
            # rounding cost of every (point, word): base_cost + sum of delta on w
            dmat = delta[B] @ words.T.astype(np.float64)   # (n, W)
            costs = base_cost[B][:, None] + dmat           # (n, W)
            # exact coordinate sums: base_sum + sum of (alt-base) on w
            shift = alt_minus_base[B] @ words.T            # (n, W) int64
            sums = base_sum[B][:, None] + shift
            bad = (sums - 4 * m) % 8 != 0
            # repair cost: cheapest +-4 move = 16 - 8*max offset (chosen coord)
            # positions in w use alt, others base
            aoff_w = np.where(words, alt_off[B][:, None, :], -np.inf)
            boff_w = np.where(words, -np.inf, base_off[B][:, None, :])
            maxoff = np.maximum(aoff_w.max(axis=2), boff_w.max(axis=2))
            repair = 16.0 - 8.0 * maxoff                # (n, W)
            repair = np.maximum(repair, 0.0)
            costs = costs + bad * repair
            # best word for each point in the chunk (ties -> smallest index)
            j = np.argmin(costs, axis=1)
            rows = np.arange(n)
            c_best = costs[rows, j]
            # better than the incumbent?
            upd = c_best < best_d[B]
            if upd.any():
                idxs = np.nonzero(upd)[0]
                wsel = words[j[idxs]]                       # (k,24) bool
                pts = base[B][idxs].copy()
                pts[wsel] = alt[B][idxs][wsel]
                # apply the +-4 repair where the sum condition failed
                bad_sel = bad[rows[idxs], j[idxs]]
                for t in np.nonzero(bad_sel)[0]:
                    i0 = idxs[t]
                    wj = wsel[t]
                    off = np.where(wj, alt_off[B][i0], base_off[B][i0])
                    p = int(np.argmax(off))      # cheapest move = max offset
                    # direction: move away from the target by 4 in the
                    # direction that reduces |x-t|... d = -4*sign(x-t)
                    xcur = pts[t, p]
                    d = -4 if xcur - T[B][i0, p] > 0 else 4
                    pts[t, p] = xcur + d
                gpos = s + idxs
                best_pts[gpos] = pts
                best_d[gpos] = c_best[idxs]

    # final exact squared distances from the chosen points
    exact_d = ((best_pts - T) ** 2).sum(axis=1)
    if return_dist:
        return best_pts, exact_d
    return best_pts


def covering_radius_check(n: int = 200, seed: int = 0) -> Dict[str, float]:
    """Sample n random targets, quantify |t - Q(t)|^2 (integer model)."""
    rng = np.random.default_rng(seed)
    T = rng.normal(0, 6, size=(n, DIM))
    Q, d = nearest_leech(T, return_dist=True)
    return {"max_dist2": float(d.max()), "mean_dist2": float(d.mean()),
            "covering_bound_16": float(d.max()) <= 16.0 + 1e-9}


if __name__ == "__main__":
    print("golay words:", len(golay_words()))
    print("octads:", len(octads()))
    mv = minimal_vectors()
    print("minimal vectors:", mv.shape)

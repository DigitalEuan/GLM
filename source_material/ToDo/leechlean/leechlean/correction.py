"""leechlean.correction -- corrupted address streams and their correction.

The claim under test (the owner's direction): mapping part addresses into
Lambda/2Lambda coset classes would let a corrupted address stream be
corrected the way the Golay code corrects bit errors.

Made concrete, three layers of defence are measured:

  1. **the lattice layer** -- a corrupted point is pulled back to the lattice
     by the exact nearest-point decoder.  The Leech packing (minimal distance
     sqrt(32), integer model) corrects any corruption of norm < sqrt(32)/2.
     The construction's own congruences act as parity checks: the sieve
     (:func:`sieve_report`) names the first failed condition -- parity (mod
     2), the Golay condition (mod 4 support), or the coordinate sum (mod 8).
  2. **the syndrome layer** -- the class of the received point in
     Lambda/2Lambda.  Every error e with e in 2 Lambda leaves the class
     untouched; but the shortest nonzero vector of 2 Lambda has integer-model
     norm sqrt(128), so **every smaller error changes the class and is
     detected**.  The type of the changed class (2, 3 or 4) lower-bounds the
     error norm by 4, 6 or 8 true units.
  3. **the codebook layer** -- the received lattice point is matched to the
     nearest codebook address (injective: 39,992 parts, 39,992 addresses).
     Correction succeeds up to half the codebook's minimum pairwise distance,
     which is measured, not assumed.

Decoders compared in the experiments:
  * ``two_stage``  -- nearest Leech point, then nearest codebook address;
  * ``class_assisted`` -- nearest Leech point, then the Lambda/2Lambda class:
    if exactly one codebook part lives in that class, it is the answer (a
    table lookup); otherwise the nearest among the class's parts (or, if the
    class is empty, the global nearest);
  * ``raw``        -- nearest codebook address directly on the corrupted
    point (no lattice stage) -- the control that isolates what the lattice
    contributes.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np
from scipy.spatial import cKDTree

from . import cosets as CS
from .leech_core import _golay_set, in_leech, in_leech_many, minimal_vectors, nearest_leech

Addr = Tuple[int, ...]


class CodebookIndex:
    """The codebook as a geometric + coset index for decoding."""

    def __init__(self, addresses: Dict[str, Addr]):
        self.keys = sorted(addresses)
        self.pts = np.array([addresses[k] for k in self.keys], dtype=np.int64)
        self.kdt = cKDTree(self.pts.astype(np.float64))
        key_of_pos = {tuple(p): i for i, p in enumerate(self.pts)}
        self.pos = [key_of_pos[tuple(p)] for p in self.pts]
        # class -> part positions
        cls = CS.class_keys(self.pts)
        self.class_of: List[Tuple[int, ...]] = [tuple(v) for v in cls.tolist()]
        self.in_class: Dict[Tuple[int, ...], List[int]] = {}
        for i, c in enumerate(self.class_of):
            self.in_class.setdefault(c, []).append(i)
        # pairwise min distance (the codebook's packing radius).  NOTE:
        # kdt.query returns distances, not squared distances.
        d, _ = self.kdt.query(self.pts.astype(np.float64), k=2)
        self.min_dist = float(d[:, 1].min())
        self.min_dist2 = float(self.min_dist ** 2)

    def n(self) -> int:
        return len(self.keys)

    def nearest(self, X: np.ndarray) -> np.ndarray:
        """Positions of nearest codebook points to each row of X."""
        _, idx = self.kdt.query(np.asarray(X, dtype=np.float64), k=1)
        return np.asarray(idx)


# ---------------------------------------------------------------------------
# corruption models
# ---------------------------------------------------------------------------

def corrupt(A: np.ndarray, model: str, rng: np.random.Generator,
            p: float = 0.1, k: int = 1, burst_len: int = 20) -> np.ndarray:
    """Corrupt an address stream (rows = ticks) under a noise model.

    jitter : each coordinate shifted by a uniform draw from {-1,0,1} with
             probability p per coordinate (usually leaves the lattice);
    flip_k : one uniformly chosen coordinate shifted by +-k (k integer);
    slip   : with probability p per tick, a random *minimal vector* of the
             lattice is added -- the stream stays on the lattice, the address
             becomes a different, perfectly valid lattice point;
    burst  : with probability p per tick a burst of ``burst_len`` ticks all
             receive the same random vector with coordinates uniform in
             [-2, 2].
    """
    A = np.asarray(A, dtype=np.int64)
    X = A.copy()
    n = len(X)
    if model == "jitter":
        m = rng.random((n, 24)) < p
        delta = rng.integers(-1, 2, size=(n, 24))
        X += m * delta
    elif model == "flip_k":
        # corrupt every tick in this model (the parameter is k)
        cols = rng.integers(0, 24, size=n)
        signs = rng.choice([-1, 1], size=n)
        X[np.arange(n), cols] += signs * k
    elif model == "slip":
        mv = minimal_vectors()
        hits = rng.random(n) < p
        idx = rng.integers(0, len(mv), size=n)
        X[hits] += mv[idx[hits]]
    elif model == "burst":
        t = 0
        while t < n:
            if rng.random() < p:
                v = rng.integers(-2, 3, size=24)
                X[t:t + burst_len] += v
                t += burst_len
            else:
                t += 1
    else:
        raise ValueError(model)
    return X


# ---------------------------------------------------------------------------
# the sieve: which congruence does a corrupted point break first?
# ---------------------------------------------------------------------------

def sieve_report(X: np.ndarray) -> Dict[str, int]:
    """First failing Leech congruence per point (the Golay-style syndrome).

    mod2       -- coordinates do not share one parity;
    mod4-golay -- the set of positions congruent to 2 (even case) or 3 (odd
                 case) mod 4 is not a Golay codeword;
    mod8-sum   -- the coordinate sum is wrong mod 8;
    clean      -- the point is in the lattice.
    """
    X = np.asarray(X, dtype=np.int64)
    out = {"mod2": 0, "mod4-golay": 0, "mod8-sum": 0, "clean": 0}
    gs = _golay_set()
    for x in X:
        par = x & 1
        if not ((par == par[0]).all()):
            out["mod2"] += 1
            continue
        m = int(par[0])
        r = x & 3
        ok = True
        for res in (2, 3):
            mask = 0
            for i in np.nonzero(r == res)[0]:
                mask |= 1 << int(i)
            if mask not in gs:
                ok = False
                break
        if not ok:
            out["mod4-golay"] += 1
            continue
        if (int(x.sum()) - 4 * m) % 8 != 0:
            out["mod8-sum"] += 1
            continue
        out["clean"] += 1
    return out


# ---------------------------------------------------------------------------
# decoders
# ---------------------------------------------------------------------------

def decode_stream(X: np.ndarray, cb: CodebookIndex, mode: str = "two_stage",
                  L: np.ndarray = None) -> Tuple[np.ndarray, Dict[str, int]]:
    """Decode a corrupted stream; returns (positions, stats).

    ``L`` may carry the precomputed nearest-Leech points of X (shared across
    decoder modes and the syndrome analysis to avoid recomputation).

    Stats: lattice_in (points already on the lattice), quant_moved (points
    the lattice stage had to move), class_unique (resolved by class lookup
    alone), class_empty (class holds no codebook part -- the syndrome flags
    a foreign address).
    """
    X = np.asarray(X, dtype=np.int64)
    on = in_leech_many(X)
    if L is None:
        L = nearest_leech(X.astype(np.float64))
    stats = {"lattice_in": int(on.sum()), "n": len(X)}
    if mode == "raw":
        return cb.nearest(X), stats
    stats["quant_moved"] = int((~(L == X).all(axis=1)).sum())
    if mode == "class_assisted":
        keys = [tuple(v) for v in CS.class_keys(L).tolist()]
        out = np.zeros(len(X), dtype=np.int64)
        n_uniq = n_empty = 0
        # group by class to query once per class
        by_cls: Dict[Tuple[int, ...], List[int]] = {}
        for i, c in enumerate(keys):
            by_cls.setdefault(c, []).append(i)
        for c, rows in by_cls.items():
            cand = cb.in_class.get(c)
            if cand is None:
                n_empty += len(rows)
                out[rows] = cb.nearest(L[rows])
            elif len(cand) == 1:
                n_uniq += len(rows)
                out[rows] = cand[0]
            else:
                cand_pts = cb.pts[cand].astype(np.float64)
                d = ((L[rows][:, None, :] - cand_pts[None, :, :]) ** 2).sum(axis=2)
                out[rows] = [cand[j] for j in d.argmin(axis=1)]
        stats["class_unique"] = n_uniq
        stats["class_empty"] = n_empty
        return out, stats
    return cb.nearest(L), stats


def syndrome_analysis(X_true: np.ndarray, X_recv: np.ndarray,
                      cb: CodebookIndex, L: np.ndarray = None
                      ) -> Dict[str, object]:
    """Class-syndrome analysis of a corrupted stream against the truth.

    For each tick: the received point is quantised to the lattice; the class
    difference (received class - true class) is a coset of Lambda/2Lambda;
    its type lower-bounds the error norm.  class_preserving errors must have
    integer-model norm >= sqrt(128) (the minimum of 2 Lambda) -- verified.
    """
    if L is None:
        L = nearest_leech(np.asarray(X_recv, dtype=np.float64))
    kT = CS.class_keys(np.asarray(X_true, dtype=np.int64))
    kR = CS.class_keys(L)
    same = (kT == kR).all(axis=1)
    types = []
    min_norm2_same_nonzero = []
    for i in np.nonzero(same)[0]:
        d = L[i] - X_true[i]
        n2 = int((d * d).sum())
        if n2 > 0:
            min_norm2_same_nonzero.append(n2)
    for i in np.nonzero(~same)[0][:4000]:
        # difference of classes: representative difference vector
        d = L[i] - X_true[i]
        # d is a lattice vector (difference of lattice points); its class:
        types.append(CS.class_type(CS.class_key(d.tolist())))
    # detection: a corrupted tick is detected when the received point is off
    # the lattice (sieve) or its class differs from the true address's class
    X_recv = np.asarray(X_recv, dtype=np.int64)
    X_true = np.asarray(X_true, dtype=np.int64)
    corrupted = ~(X_recv == X_true).all(axis=1)
    off = ~in_leech_many(X_recv)
    detected = corrupted & (off | ~same)
    from collections import Counter
    return {
        "n": len(X_true),
        "n_corrupted": int(corrupted.sum()),
        "n_detected": int(detected.sum()),
        "detection_rate": float(detected.sum() / corrupted.sum())
        if corrupted.any() else None,
        "false_alarms": int((~corrupted & (off | ~same)).sum()),
        "class_preserving": int(same.sum()),
        "class_changing": int((~same).sum()),
        "min_nonzero_norm2_class_preserving":
            min(min_norm2_same_nonzero) if min_norm2_same_nonzero else None,
        "bound_128_respected":
            (min(min_norm2_same_nonzero) >= 128)
            if min_norm2_same_nonzero else True,
        "error_class_types": dict(Counter(types)),
    }

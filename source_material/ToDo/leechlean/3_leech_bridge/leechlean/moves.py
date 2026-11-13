"""leechlean.moves -- the happening between addresses.

A move is the transition from one addressed part to the next: d = B - A for
consecutive Leech addresses A, B.  Moves are lattice vectors, so the
happening between parts is *algebraic*, not mere geometry:

  * moves compose by addition (d1 after d2 is d1 + d2, again in Lambda) --
    the tick stream is a walk in the Cayley graph of (Lambda, +);
  * the class map kappa: Lambda -> Lambda/2Lambda is a homomorphism, so
    every journey projects to a walk on the finite index space Lambda/2Lambda
    (order 2^24), where moves 'multiply' by F2 addition -- the user's
    multiplication indexed for 24-dimensional movement, made literal;
  * Lambda/2Lambda carries the natural scalar product <x,y> mod 2 (well
    defined because Lambda is doubly even and unimodular) and the type map
    type(kappa) in {0, 2, 3, 4} (minimal squared norm in the class: 0 the
    zero class, 2 the 98,280 minimal-vector classes, 3 norm-6 classes,
    4 the rest) -- the same structures the Griess algebra is graded by:
    Conway's monster algebra decomposes as 300 + 98,280 + 98,304 with the
    98,280 piece indexed by the type-2 classes and the 98,304 piece by the
    Golay-code/Parker-loop index set times the 24 coordinates (Conway 1985;
    Hoehn 2025, arXiv:2508.01037; Seysen 2022, arXiv:2203.04223).

This module implements the computable fragment: move extraction and
repertoire statistics, composition closure, the class map, class pairing
(verified well defined), and the group-algebra convolution over move
classes.  The full 196,884-dimensional Griess product is NOT implemented --
it needs Conway's product tables and the Parker loop cocycle -- and the
reports say so explicitly.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np

from .cosets import class_key, class_type, q_form
from .leech_core import inner, norm2

MoveKey = Tuple[int, ...]


def move_vector(A: Sequence[int], B: Sequence[int]) -> np.ndarray:
    return np.asarray(B, dtype=np.int64) - np.asarray(A, dtype=np.int64)


def move_key(d: Sequence[int]) -> MoveKey:
    return tuple(int(v) for v in d)


class MoveAlgebra:
    """The observed moves of a corpus (or of any set of edges between
    addressed parts) with their algebra: counts, norms, Lambda/2Lambda
    classes, types, composition closure, and class convolution."""

    def __init__(self):
        self.counts: Counter = Counter()          # move vector -> count
        self.file_counts: Counter = Counter()     # move -> number of files
        self.by_file: Dict[str, Counter] = {}     # file -> its move counts
        self.moves_by_file: Dict[str, List[MoveKey]] = {}  # file -> order

    # ------------------------------------------------------------------
    def add_stream(self, addresses: Sequence[Sequence[int]], rel: str) -> None:
        """All moves of one address stream, in order."""
        A = np.asarray(addresses, dtype=np.int64)
        if len(A) < 2:
            return
        D = (A[1:] - A[:-1]).tolist()
        seq = [move_key(d) for d in D]
        cf = Counter(seq)
        for k in cf:
            self.file_counts[k] += 1
        self.counts.update(cf)
        self.by_file[rel] = cf
        self.moves_by_file[rel] = seq

    # ------------------------------------------------------------------
    def norm2(self, k: MoveKey) -> int:
        return int(np.dot(np.array(k), np.array(k)))

    def class_of(self, k: MoveKey) -> Tuple[int, ...]:
        return class_key(k)

    def type_of(self, k: MoveKey) -> int:
        return class_type(self.class_of(k))

    def stats(self) -> Dict[str, object]:
        ks = list(self.counts)
        norms = np.array([self.norm2(k) for k in ks])
        types = Counter(self.type_of(k) for k in ks)
        total = sum(self.counts.values())
        top = self.counts.most_common(50)
        top_cover = 0.0
        acc = 0
        for i in range(50):
            if i < len(top):
                acc += top[i][1]
        return {
            "distinct_moves": len(ks),
            "total_moves": total,
            "norm2_mean": float(norms.mean()) if len(norms) else 0.0,
            "norm2_median": float(np.median(norms)) if len(norms) else 0.0,
            "type_census_distinct": dict(types),
            "type_census_weighted": {
                t: sum(c for k, c in self.counts.items()
                       if self.type_of(k) == t) for t in types},
            "top50_share": acc / total if total else 0.0,
            "top5": [{"move": list(k), "count": c,
                      "norm2": self.norm2(k), "type": self.type_of(k)}
                     for k, c in top[:5]],
        }

    # ------------------------------------------------------------------
    def closure(self, seed: int = 0) -> Dict[str, object]:
        """Composition closure of the repertoire: for consecutive move
        pairs actually observed in streams, how often is the composed move
        d1 + d2 itself an observed move -- corpus-wide, within the same
        file, and against a null of random repertoire pairs (moves drawn
        independently by count weight, same number of pairs)."""
        pairs = in_corpus = same_file = 0
        for rel, seq in self.moves_by_file.items():
            here = self.by_file[rel]
            for k1, k2 in zip(seq, seq[1:]):
                comp = tuple(x + y for x, y in zip(k1, k2))
                pairs += 1
                if comp in self.counts:
                    in_corpus += 1
                if comp in here:
                    same_file += 1
        rng = np.random.default_rng(seed)
        ks = list(self.counts)
        w = np.array([self.counts[k] for k in ks], dtype=float)
        w /= w.sum()
        null_n = min(pairs, 500000)
        idx = rng.choice(len(ks), size=(2, null_n), p=w)
        null_hits = sum(
            1 for i, j in zip(idx[0], idx[1])
            if tuple(x + y for x, y in zip(ks[i], ks[j])) in self.counts)
        return {
            "consecutive_pairs": pairs,
            "composed_in_repertoire": in_corpus,
            "in_repertoire_rate": in_corpus / pairs if pairs else 0.0,
            "same_file_rate": same_file / pairs if pairs else 0.0,
            "null_rate": null_hits / null_n if null_n else 0.0,
            "null_n": null_n,
        }

    # ------------------------------------------------------------------
    @staticmethod
    def class_pairing(k1: Tuple[int, ...], k2: Tuple[int, ...]) -> int:
        """The natural scalar product on Lambda/2Lambda: <x, y> mod 2 for
        any representatives.  Well defined because Lambda is doubly even
        (all pairings even) and unimodular (nondegenerate).  Verified
        numerically by verify_pairing()."""
        return inner(list(k1), list(k2)) % 2

    @staticmethod
    def verify_pairing(n: int = 2000, seed: int = 0) -> bool:
        """class_pairing must not depend on the representative: pair two
        random lattice points, then shift both by random 2Lambda elements
        and re-pair.  (Representatives must be lattice points -- random
        integer vectors are not -- so both sides are built from the Leech
        and 2Lambda bases.)"""
        from .cosets import leech_basis, leech2_basis
        rng = np.random.default_rng(seed)
        H = leech_basis()
        H2 = leech2_basis()
        for _ in range(n):
            a = tuple(int(v) for v in rng.integers(-2, 3, H.shape[0]) @ H)
            b = tuple(int(v) for v in rng.integers(-2, 3, H.shape[0]) @ H)
            p = MoveAlgebra.class_pairing(a, b)
            for _try in range(4):
                o1 = tuple(int(v) for v in
                           rng.integers(-2, 3, H2.shape[0]) @ H2)
                o2 = tuple(int(v) for v in
                           rng.integers(-2, 3, H2.shape[0]) @ H2)
                if MoveAlgebra.class_pairing(
                        tuple(x + y for x, y in zip(a, o1)),
                        tuple(x + y for x, y in zip(b, o2))) != p:
                    return False
        return True

    # ------------------------------------------------------------------
    def class_convolution(self, c1: Tuple[int, ...], c2: Tuple[int, ...]
                          ) -> Tuple[int, ...]:
        """Multiplication in the group algebra R[Lambda/2Lambda]: classes
        compose by the group law of Lambda/2Lambda -- reduction of the sum
        of representatives.  (Keys are canonical coset representatives, not
        F2 vectors, so composition is reduce(c1 + c2); under any F2 basis of
        the quotient this is coordinate-wise XOR.)  This is the index-space
        shadow of move composition d1 + d2."""
        return class_key([a + b for a, b in zip(c1, c2)])

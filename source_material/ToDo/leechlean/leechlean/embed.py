"""leechlean.embed -- the 24-channel direction of every part.

Channels 0-7 are the syntactic role mix of the part's occurrences (from
:mod:`leechlean.parts_stats`).  Channels 8-23 are a 16-dimensional
**distributional embedding**: positive-PMI co-occurrence counts of the part
with the 2048 most frequent structural tokens inside a +-8 structural-token
window, projected onto the top 16 principal components (computed
deterministically by a dense symmetric eigendecomposition of the 2048x2048
Gram matrix -- no randomised solver).

Parts with no co-occurrence row at all (unique comment texts, which the
window never sees because comments are not structural tokens; some unique
strings) have no usage statistics to average.  Their embedding block is a
deterministic pseudorandom unit vector derived from SHA-256 of the part key,
flagged as ``identity_directed`` and reported as such: usage geometry cannot
separate what occurs once.

The final direction is the normalised concatenation of the two unit blocks,
so role and co-occurrence contribute equally.
"""

from __future__ import annotations

import hashlib
from bisect import bisect_left
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import scipy.sparse as sp

from .lean_parts import FileRecord, structural
from .parts_stats import Inventory, N_CHANNELS, ROLE_CHANNELS

CTX_VOCAB = 2048
WINDOW = 8
EMBED_DIM = 16


@dataclass
class Directions:
    table: Dict[str, np.ndarray]          # part key -> (24,) unit direction
    identity_directed: List[str]          # parts whose embedding block is hashed
    svd_variance: float                   # fraction of PPMI mass in 16 dims
    ctx_vocab: List[str]


def build_directions(inv: Inventory) -> Directions:
    files = inv.files
    # ---- context vocabulary: top CTX_VOCAB structural token keys ---------
    from collections import Counter
    sc = Counter()
    for rec in files:
        for _, t in structural(rec.toks):
            sc[t.key] += 1
    ctx_vocab = [k for k, _ in sc.most_common(CTX_VOCAB)]
    col = {k: j for j, k in enumerate(ctx_vocab)}
    C = len(ctx_vocab)

    # ---- co-occurrence rows for token and bigram parts -------------------
    parts = sorted(inv.counts)                       # deterministic order
    row_of = {k: i for i, k in enumerate(parts)}
    P = len(parts)
    rows: List[np.ndarray] = []
    cols: List[np.ndarray] = []
    for rec in files:
        st = structural(rec.toks)
        st_idx = [idx for idx, _ in st]
        n = len(st)
        if n == 0:
            continue
        tok_row = np.array([row_of.get(t.key, -1) for _, t in st], dtype=np.int32)
        ctx_col = np.array([col.get(t.key, -1) for _, t in st], dtype=np.int32)
        # token-part rows: pair (i, i+d) both structural, d = 1..WINDOW
        for d in range(1, WINDOW + 1):
            a, b = tok_row[:-d], ctx_col[d:]
            m = (a >= 0) & (b >= 0)
            rows.append(a[m]); cols.append(b[m])
            a2, b2 = tok_row[d:], ctx_col[:-d]
            m2 = (a2 >= 0) & (b2 >= 0)
            rows.append(a2[m2]); cols.append(b2[m2])
        # bigram rows: the pair (i, i+1) as a part; its context is every
        # structural position within +-WINDOW of the pair, excluding the pair
        br = np.full(n - 1, -1, dtype=np.int32)
        for i in range(n - 1):
            bk = f"b:{st[i][1].key}|{st[i + 1][1].key}"
            r = row_of.get(bk, -1)
            if r >= 0:
                br[i] = r
        for d in range(2, WINDOW + 1):
            # context after the pair: position i+1+d pairs with bigram i
            L = max(0, n - 1 - d)
            a, b = br[:L], ctx_col[1 + d:1 + d + L]
            m = (a >= 0) & (b >= 0)
            rows.append(a[m]); cols.append(b[m])
            # context before the pair: position i-d pairs with bigram i
            a2, b2 = br[d:d + L], ctx_col[:L]
            m2 = (a2 >= 0) & (b2 >= 0)
            rows.append(a2[m2]); cols.append(b2[m2])
        # comment and string parts: context = the structural tokens around
        # each occurrence (their usage geometry is where they sit, even though
        # they are not structural themselves)
        for i, t in enumerate(rec.toks):
            if t.kind not in ("comment", "str"):
                continue
            r0 = row_of.get(t.key, -1)
            if r0 < 0:
                continue
            lo = bisect_left(st_idx, i)      # structural positions around i
            for j in range(max(0, lo - WINDOW), min(len(st), lo + WINDOW)):
                cj = col.get(st[j][1].key, -1)
                if cj >= 0:
                    rows.append(np.array([r0], dtype=np.int32))
                    cols.append(np.array([cj], dtype=np.int32))

    # frames: context = the declaration's structural tokens
    from .lean_parts import DECL_KW, decl_frames
    for rec in files:
        st = structural(rec.toks)
        starts = [k for k, (_, t) in enumerate(st)
                  if t.kind == "kw" and t.text in DECL_KW and t.col == 0]
        fr_keys = decl_frames(rec.toks)
        for fj, k in enumerate(starts):
            end = starts[fj + 1] if fj + 1 < len(starts) else len(st)
            key = fr_keys[fj] if fj < len(fr_keys) else None
            if key is None:
                continue
            br = row_of.get(key, -1)
            if br < 0:
                continue
            cc = [col.get(st[j][1].key, -1) for j in range(k, end)]
            cc = [c for c in cc if c >= 0]
            if cc:
                rows.append(np.full(len(cc), br, dtype=np.int32))
                cols.append(np.array(cc, dtype=np.int32))

    if rows:
        R = np.concatenate(rows).astype(np.int32, copy=False)
        Cc = np.concatenate(cols).astype(np.int32, copy=False)
        M = sp.coo_matrix((np.ones(len(R), dtype=np.float32), (R, Cc)),
                          shape=(P, C)).tocsr()
        M.sum_duplicates()
    else:
        M = sp.csr_matrix((P, C), dtype=np.float32)

    # ---- PPMI (vectorised) ------------------------------------------------
    total = M.sum()
    row_sum = np.asarray(M.sum(axis=1)).ravel()
    col_sum = np.asarray(M.sum(axis=0)).ravel()
    Mcoo = M.tocoo()
    r, c, v = Mcoo.row, Mcoo.col, Mcoo.data.astype(np.float64)
    with np.errstate(divide="ignore"):
        pmi = np.log(v * total) - np.log(row_sum[r]) - np.log(col_sum[c])
    mask = pmi > 0
    if mask.any():
        Mp = sp.coo_matrix((pmi[mask].astype(np.float32),
                            (r[mask], c[mask])), shape=(P, C)).tocsr()
    else:
        Mp = sp.csr_matrix((P, C), dtype=np.float32)

    # ---- deterministic SVD via the Gram matrix ----------------------------
    G = (Mp.T @ Mp).toarray().astype(np.float64)     # C x C
    w, V = np.linalg.eigh(G)                         # ascending
    order = np.argsort(w)[::-1][:EMBED_DIM]
    V = V[:, order]                                  # C x 16
    w = w[order]
    # sign convention: the largest-magnitude entry of each column is positive
    for j in range(EMBED_DIM):
        if V[np.argmax(np.abs(V[:, j])), j] < 0:
            V[:, j] = -V[:, j]
    E = (Mp @ V)                                     # P x 16 dense (P*16)
    gram_total = float((G * G).sum())
    svd_var = float((w[:EMBED_DIM] ** 2).sum() / gram_total) if gram_total > 0 else 0.0

    # ---- assemble directions ----------------------------------------------
    table: Dict[str, np.ndarray] = {}
    identity: List[str] = []
    enorm = np.linalg.norm(E, axis=1)
    for i, k in enumerate(parts):
        role = inv.profiles.get(k)
        if role is None:
            role = np.zeros(len(ROLE_CHANNELS), dtype=np.int64)
        rn = np.linalg.norm(role)
        role_u = role / rn if rn > 0 else np.zeros(len(ROLE_CHANNELS))
        if enorm[i] > 1e-12:
            emb_u = E[i] / enorm[i]
        else:
            emb_u = _identity_direction(k)
            identity.append(k)
        d = np.concatenate([role_u, emb_u])
        n = np.linalg.norm(d)
        table[k] = d / n if n > 0 else _identity_direction24(k)
    return Directions(table=table, identity_directed=identity,
                      svd_variance=svd_var, ctx_vocab=ctx_vocab)


def _identity_direction(k: str) -> np.ndarray:
    """Deterministic pseudorandom unit 16-vector from the part key."""
    h = hashlib.sha256(k.encode("utf-8")).digest()
    v = np.array([b / 255.0 - 0.5 for b in h[:EMBED_DIM]], dtype=np.float64)
    n = np.linalg.norm(v)
    return v / n if n > 0 else np.zeros(EMBED_DIM)


def _identity_direction24(k: str) -> np.ndarray:
    v = np.concatenate([np.zeros(8), _identity_direction(k)])
    return v

"""leechlean.fingerprint -- files as points of the lattice, and what that
geometry recovers.

The **fingerprint** of a file is the endpoint of its work integral,
F = sum_t A(t): a single Leech lattice point (the walk ends on the lattice).
The **centroid** c = F / n is its direction; both are measured against the
ground truth of the repository's subproject structure (the directory a file
lives in).

Three evaluations, each with controls:

  1. PCA scatter of centroids, coloured by subproject -- the visual question:
     do same-project files land near each other?
  2. leave-one-out nearest-centroid classification by subproject on the
     full 24-dim centroid space;
  3. the same classification on a control where the address of every part is
     permuted across parts (geometry destroyed, energies kept) and on a
     random-label control -- the amount by which the real geometry beats
     them is what the addressing adds.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np

from .addressing import Addressing


def fingerprints(addr: Addressing) -> Tuple[np.ndarray, np.ndarray, List[str], List[str]]:
    """Return (F, centroids, rels, modules): F are lattice-point endpoints."""
    F = np.zeros((len(addr.inv.files), 24), dtype=np.int64)
    rels, mods = [], []
    for i, rec in enumerate(addr.inv.files):
        A = np.array([addr.addresses[t.key] for t in rec.toks], dtype=np.int64)
        F[i] = A.sum(axis=0)
        rels.append(rec.rel)
        mods.append(rec.module)
    n = np.array([[len(addr.inv.files[i].toks)] for i in range(len(addr.inv.files))],
                 dtype=np.float64)
    cent = F / np.maximum(n, 1)
    return F, cent, rels, mods


def pca(X: np.ndarray, k: int = 2) -> np.ndarray:
    Xc = X - X.mean(axis=0)
    # deterministic SVD
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    return Xc @ Vt[:k].T, S


def leave_one_out_centroid(X: np.ndarray, labels: List[str]) -> float:
    """Fraction of files correctly classified by nearest class centroid."""
    lab = np.array(labels)
    classes = sorted(set(labels))
    correct = 0
    for i in range(len(X)):
        d = np.zeros(len(classes))
        for j, c in enumerate(classes):
            m = (lab == c) & (np.arange(len(X)) != i)
            if m.sum() == 0:
                d[j] = np.inf
                continue
            cen = X[m].mean(axis=0)
            d[j] = ((X[i] - cen) ** 2).sum()
        if classes[int(np.argmin(d))] == labels[i]:
            correct += 1
    return correct / len(X)


def purity_kmeans(X: np.ndarray, labels: List[str], k: int,
                  rng: np.random.Generator, iters: int = 60) -> float:
    """k-means clustering purity (best label per cluster, standard metric)."""
    lab = np.array(labels)
    # normalise scales
    mu, sd = X.mean(axis=0), X.std(axis=0) + 1e-12
    Z = (X - mu) / sd
    C = Z[rng.choice(len(Z), k, replace=False)]
    for _ in range(iters):
        D = ((Z[:, None, :] - C[None, :, :]) ** 2).sum(axis=2)
        a = D.argmin(axis=1)
        for j in range(k):
            if (a == j).any():
                C[j] = Z[a == j].mean(axis=0)
    purity = 0.0
    for j in range(k):
        m = a == j
        if m.any():
            vals, cnts = np.unique(lab[m], return_counts=True)
            purity += cnts.max()
    return purity / len(Z)


def permuted_address_control(addr: Addressing, rng: np.random.Generator,
                             X: np.ndarray) -> np.ndarray:
    """Control: parts keep their energies, addresses permuted across parts."""
    keys = list(addr.addresses)
    pts = [addr.addresses[k] for k in keys]
    perm = rng.permutation(len(pts))
    mapping = {k: pts[perm[i]] for i, k in enumerate(keys)}
    Xc = np.zeros_like(X)
    for i, rec in enumerate(addr.inv.files):
        s = np.zeros(24, dtype=np.int64)
        for t in rec.toks:
            s += np.array(mapping[t.key], dtype=np.int64)
        Xc[i] = s / max(len(rec.toks), 1)
    return Xc

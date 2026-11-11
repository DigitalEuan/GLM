"""leechlean.dynamics -- the path of a file through the lattice over ticks.

A file's address stream is read as a process in time: **tick** t is the
t-th token, and two readings are computed:

  * the **carrier state** X(t) = A(t): at tick t the carrier sits at the
    address of the part being written;
  * the **work integral** W(t) = sum_{i<=t} A(i): the running sum of the
    addresses the file has consumed.  Because the Leech lattice is a group,
    every W(t) is again a lattice point -- the walk never leaves the lattice
    (verified, not assumed).

Measured per file (all against a shuffled-token control that keeps the
address multiset and destroys the order):

  * total energy: sum of |A(t)|^2 / 8 (the file's information content in
    lattice units);
  * path length: sum of |A(t+1) - A(t)|^2 (does real Lean order visit
    nearby addresses consecutively?);
  * displacement: |W(t)|^2 at the end (how far the file travels from the
    origin -- cancellation vs accumulation of its parts).
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np

from .addressing import Addressing

Addr = Tuple[int, ...]


def address_matrix(addr: Addressing, stream: Sequence[Addr]) -> np.ndarray:
    return np.array(stream, dtype=np.int64)


def walk_stats(A: np.ndarray, rng: np.random.Generator) -> Dict[str, float]:
    """Geometry of one address stream + its shuffled control."""
    n = len(A)
    E = float((A * A).sum() / 8.0)                     # total energy
    if n >= 2:
        steps = A[1:] - A[:-1]
        path2 = float((steps * steps).sum())
    else:
        path2 = 0.0
    W = A.cumsum(axis=0)
    disp2 = float((W[-1] * W[-1]).sum()) if n else 0.0
    # shuffled control: same multiset of addresses, random order
    S = A[rng.permutation(n)]
    ssteps = S[1:] - S[:-1] if n >= 2 else np.zeros((0, 24))
    return {
        "ticks": n,
        "energy": E,
        "energy_per_tick": E / n if n else 0.0,
        "path2": path2,
        "path2_shuffled": float((ssteps * ssteps).sum()),
        "displacement2": disp2,
        "mean_step2": path2 / (n - 1) if n >= 2 else 0.0,
        "mean_step2_shuffled": float((ssteps * ssteps).mean()) if n >= 2 else 0.0,
    }


def file_walk(addr: Addressing, rec_index: int,
              rng: np.random.Generator) -> Dict[str, float]:
    rec = addr.inv.files[rec_index]
    A = np.array([addr.addresses[t.key] for t in rec.toks], dtype=np.int64)
    st = walk_stats(A, rng)
    st["rel"] = rec.rel
    st["module"] = rec.module
    return st


def work_integral(A: np.ndarray) -> np.ndarray:
    """W(t): the running sum, one lattice point per tick."""
    return A.cumsum(axis=0)


def energy_series(A: np.ndarray) -> np.ndarray:
    """Per-tick address energy |A(t)|^2 / 8 (surprisal in lattice units)."""
    return (A * A).sum(axis=1) / 8.0


def on_lattice_check(W: np.ndarray, in_leech) -> bool:
    return bool(in_leech(W).all())

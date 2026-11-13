"""leechlean.addressing -- every part gets a Leech lattice address.

The concept under test (the owner's idea, made concrete):

  * a part's **direction** in the lattice is its context: the 24-channel
    profile of where and with what it occurs (8 syntactic roles + 16 landmark
    co-occurrences), L2-normalised;
  * a part's **energy** is its information content: E(p) = -log2 f(p) bits of
    surprisal.  The address target is

        T(p) = sqrt(32 * E(p)) * u(p)          (integer model, x*sqrt(8))

    so the *true* squared norm of the target is |T|^2 / 8 = 4 * E(p):
    **one bit of surprisal is four units of Leech energy, and the minimal
    shell (energy 4) is the one-bit sphere**.  Common parts sit near the
    origin, rare parts far out along their context direction;
  * the **address** A(p) is the exact nearest Leech point to T(p)
    (:func:`leechlean.leech_core.nearest_leech`), so everything the lattice
    is (its minimal norm, its shells, its Conway symmetry) becomes part of
    the addressing;
  * parts whose targets quantise to the same lattice point **collide**; the
    codebook records a disambiguating ordinal for each.  The collision count
    is the measured resolution of the addressing, reported honestly.

Decoding is exact by construction: the codebook maps address -> ordered part
list, and the codec emits the ordinal only when a cell holds several parts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np

from .embed import Directions, _identity_direction
from .leech_core import DIM, in_leech_many, nearest_leech, norm2
from .parts_stats import Inventory

BITS_PER_SHELL = 4      # true lattice energy per bit of surprisal (see above)
DISPLACE_STEP = 0.15    # radial quantum for collision displacement
DISPLACE_CAP = 2.5      # cap on the radial displacement factor


@dataclass
class Addressing:
    inv: Inventory
    targets: Dict[str, np.ndarray]          # part key -> (24,) float target
    addresses: Dict[str, Tuple[int, ...]]   # part key -> lattice point
    ordinals: Dict[str, int]                # part key -> index in its cell
    cells: Dict[Tuple[int, ...], List[str]]  # lattice point -> ordered parts
    quant_err2: Dict[str, float]            # part key -> |T - A|^2
    displaced: Dict[str, float]             # part key -> displacement factor
    stats: Dict[str, object]


def assign_addresses(inv: Inventory, dirs: Directions,
                     chunk: int = 512) -> Addressing:
    """Quantise every part's target to the lattice; build the codebook.

    Parts are placed in deterministic rank order (descending count, then key)
    by **first fit over radial multiples**: a part whose cell is already taken
    steps outward along its own direction through the multiples
    ``1 + DISPLACE_STEP * j`` (j = 0, 1, 2, ...).  A part that would pass
    ``DISPLACE_CAP`` is re-directed once by identity (a deterministic hash
    direction, locked for the rest of the run) and restarts at radius 1.
    The occupied-cell check makes the codebook injective by construction --
    every address names exactly one part -- and the commoner part of a pair
    always keeps the geometric cell (it comes first in rank order).
    """
    keys = sorted(inv.counts, key=lambda k: (-inv.counts[k], k))
    radius = {k: _target_radius(inv, k) for k in keys}
    idx_all = {k: i for i, k in enumerate(keys)}

    A = np.zeros((len(keys), DIM), dtype=np.int64)
    err2 = np.zeros(len(keys))
    addresses: Dict[str, Tuple[int, ...]] = {}
    quant: Dict[str, float] = {}
    occupied: set = set()
    displaced: Dict[str, float] = {k: 1.0 for k in keys}
    identity_forced: List[str] = []
    j_of: Dict[str, int] = {k: 0 for k in keys}    # displacement step index

    # wave 0: every part at radius 1.0; losers step out in later waves
    pending = list(keys)
    for wave in range(40):
        if not pending:
            break
        T = np.zeros((len(pending), DIM), dtype=np.float64)
        for i, k in enumerate(pending):
            T[i] = radius[k] * displaced[k] * dirs.table[k]
        Q, qe = _quantize_all(T, chunk)
        still: List[str] = []
        for i, k in enumerate(pending):
            pt = tuple(int(v) for v in Q[i])
            if pt not in occupied:
                occupied.add(pt)
                addresses[k] = pt
                quant[k] = float(qe[i])
                A[idx_all[k]] = Q[i]
                err2[idx_all[k]] = qe[i]
            else:
                j_of[k] += 1
                if 1.0 + DISPLACE_STEP * j_of[k] > DISPLACE_CAP and \
                        k not in identity_forced:
                    identity_forced.append(k)
                    d24 = np.concatenate([dirs.table[k][:8],
                                          _identity_direction(k)])
                    dirs.table[k] = d24 / np.linalg.norm(d24)
                    j_of[k] = 0
                displaced[k] = 1.0 + DISPLACE_STEP * j_of[k]
                still.append(k)
        pending = still
    assert not pending, "address placement did not terminate"

    ok = in_leech_many(A)
    assert ok.all(), "address assignment produced non-lattice points"
    assert err2.max() <= 16.0 + 1e-9, "quantisation exceeded covering radius"
    assert len(addresses) == len(keys) == len(occupied), "codebook not injective"

    # cells are singletons by construction; keep the map for the codec API
    cells: Dict[Tuple[int, ...], List[str]] = {pt: [k] for k, pt in addresses.items()}
    ordinals: Dict[str, int] = {k: 0 for k in keys}

    E = np.array([inv.energy(k) for k in keys])
    lattice_E = np.array([norm2(addresses[k]) / 8.0 for k in keys])
    n_displ = sum(1 for k in keys if displaced[k] > 1.0 + 1e-12)
    hist: Dict[int, int] = {}
    for k in keys:
        sh = int(round(norm2(addresses[k]) / 8.0))
        hist[sh] = hist.get(sh, 0) + 1
    mask = lattice_E >= 4
    r_all = _pearson(lattice_E, 4.0 * E)
    r_res = _pearson(lattice_E[mask], 4.0 * E[mask])
    keep = np.array([displaced[k] <= 1.0 + 1e-12 for k in keys])
    r_clean = _pearson(lattice_E[keep], 4.0 * E[keep])

    stats = {
        "n_parts": len(keys),
        "n_cells": len(cells),
        "n_collisions": 0,
        "n_displaced": n_displ,
        "n_identity_forced": len(identity_forced),
        "max_quant_err2": float(err2.max()),
        "mean_quant_err2": float(err2.mean()),
        "energy_correlation_all": r_all,
        "energy_correlation_resolvable": r_res,
        "energy_correlation_undisplaced": r_clean,
        "n_below_min_shell": int((~mask).sum()),
        "shell_histogram": dict(sorted(hist.items())),
        "bits_per_shell": BITS_PER_SHELL,
        "svd_variance": dirs.svd_variance,
        "n_identity_directed": len(dirs.identity_directed),
    }
    return Addressing(inv=inv,
                      targets={k: radius[k] * dirs.table[k] for k in keys},
                      addresses=addresses, ordinals=ordinals, cells=cells,
                      quant_err2=quant, displaced=displaced, stats=stats)


def _quantize_all(T: np.ndarray, chunk: int) -> Tuple[np.ndarray, np.ndarray]:
    A = np.zeros((len(T), DIM), dtype=np.int64)
    err2 = np.zeros(len(T))
    for s in range(0, len(T), chunk):
        e = min(s + chunk, len(T))
        Q, d = nearest_leech(T[s:e], return_dist=True)
        A[s:e] = Q
        err2[s:e] = d
    return A, err2


def _target_radius(inv: Inventory, key: str) -> float:
    """|T| = sqrt(32 * E): one bit of surprisal = 4 units of true energy."""
    return math.sqrt(BITS_PER_SHELL * 8.0 * inv.energy(key))


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if len(a) < 2:
        return float("nan")
    ca, cb = a - a.mean(), b - b.mean()
    denom = math.sqrt((ca * ca).sum() * (cb * cb).sum())
    return float((ca * cb).sum() / denom) if denom > 0 else float("nan")


def address_energy(pt: Sequence[int]) -> int:
    """True lattice energy (squared norm) of an address: |x|^2 / 8."""
    return norm2(pt) // 8


def describe_address(addr: Addressing, key: str) -> str:
    """Read an address back as a sentence: its energy and direction."""
    from .parts_stats import ROLE_CHANNELS
    pt = addr.addresses[key]
    E_l = norm2(pt) // 8
    u = addr.inv.direction(key)
    roles = np.array(ROLE_CHANNELS)[u[:8] > 0].tolist()
    return (f"{key}: lattice energy {E_l} (surprisal "
            f"{addr.inv.energy(key):.2f} bits x {BITS_PER_SHELL}), "
            f"roles {roles or ['-']}")

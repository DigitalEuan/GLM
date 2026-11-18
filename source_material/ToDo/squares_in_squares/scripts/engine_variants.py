#!/usr/bin/env python3
r"""engine_variants.py — RECONSTRUCTION, not the original.

Imported by `boundary_demo.py`, `fine_probe.py`, `lattice_scan.py`,
`p2_seed_polish.py` and `soft_relax.py`. **Absent from this tree and from the
repository's git history** (`git log --all -- '*engine_variants*'` returns
nothing), so it is rebuilt to the calls used:

    finalize_gate(state_or_q, n=None)  -> dict with ok / L / worst_pen
    lattice_seed(n, L)                 -> q, the axis-aligned lattice seed
    transduce(...)                     -> passed through to lattice_seed

`finalize_gate` is deliberately a thin wrapper over `packlib.finalize`/`verify`,
because the project's gate must be the only authority: a reconstruction that
invented its own geometry test would be exactly the failure this project has
already paid for twice.
"""
from __future__ import annotations

import numpy as np

import packlib as P


def _as_state(x, n=None):
    """Accept a state list or a packed [X; Y; TH] array."""
    a = np.asarray(x, float)
    if a.ndim == 2 and a.shape[1] == 3:
        return [(float(u), float(v), float(w)) for u, v, w in a]
    if a.ndim == 1:
        n = n or a.size // 3
        return [(float(a[i]), float(a[n + i]), float(a[2 * n + i]))
                for i in range(n)]
    raise ValueError("cannot read a state from this object")


def finalize_gate(state_or_q, n=None) -> dict:
    """Gate through packlib. Returns ok, L, worst_pen."""
    st = _as_state(state_or_q, n)
    r = P.verify(st)
    return {"ok": bool(r["ok"]), "L": float(r["L"]),
            "worst_pen": float(r["worst_pen"]), "state": st}


def lattice_seed(n: int, L: float):
    """Axis-aligned lattice of n unit squares inside side L (packed rows)."""
    k = max(1, int(np.ceil(np.sqrt(n))))
    X = np.empty(n); Y = np.empty(n); TH = np.zeros(n)
    for i in range(n):
        X[i] = (i % k) + 0.5
        Y[i] = (i // k) + 0.5
    # squeeze/centre into the box
    sx = L / max(k, 1e-9)
    X *= sx; Y *= sx
    return np.concatenate([X, Y, TH])


def transduce(q, *a, **kw):
    """Compatibility shim: the original transduced a seed between variants."""
    return np.asarray(q, float).copy()


if __name__ == "__main__":
    from cent_discovery import rsa_seed
    rng = np.random.RandomState(0)
    print("engine_variants reconstruction smoke:")
    print("  lattice_seed(5, 3.0) ok:", finalize_gate(lattice_seed(5, 3.0), 5)["ok"])
    print("  rsa_seed gate:", finalize_gate(rsa_seed(5, 3.2, rng), 5))

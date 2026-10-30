"""Compute the Boolean derivative and cone separation structure of a(n).

Per Qwen.ai's Round 5 guidance: the combinatorial tracking of near-top
monomials is a trap. Instead, use Boolean derivatives and cone
separation to abstract away the lower-degree bulk.

Key computations:
  1. For n=1..6, compute a(n)(0), a(n)(1), a(n)(-1) — the center
     column at three spatial positions — to verify the spatial
     shifting of the top monomial.

  2. For n=1..6, compute the Boolean derivative
     ∂a(n)(0)/∂x_n — the derivative with respect to the RIGHTMOST
     variable in the light cone. This isolates the right-cone
     nonlinearity.

  3. For n=1..6, compute the Boolean derivative
     ∂a(n)(0)/∂x_{-n} — the derivative with respect to the LEFTMOST
     variable. This should be ZERO or low-degree (since the left
     term L is purely linear and the leftmost variable doesn't
     participate in the nonlinear C·R term).

  4. Analyze the cone separation: split the ANF of a(n)(0) into
     monomials that contain left-cone variables (x_{-n}, x_{-(n-1)})
     vs monomials that don't. The top monomial should be in the
     "pure right-cone" part.

The key hypothesis (to test): the degree growth is driven ENTIRELY
by the right-cone nonlinearity. The left-cone variables enter
linearly and don't affect the top-degree monomial. This is the
"cone separation" structural invariant.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

try:
    from numba import njit
    NUMBA = True
except ImportError:
    NUMBA = False
    def njit(*args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            return args[0]
        def deco(f): return f
        return deco

DATA = Path("/home/z/my-project/data")


@njit(cache=True)
def rule30_eval_at_position(init_bits: int, width: int, n_steps: int,
                             target_col: int) -> int:
    """Evaluate a(n_steps) at column position `target_col`, where the
    initial row of width=2n+1 cells is given by `init_bits` (bit i is
    column i - n). Returns 0 or 1.

    target_col is relative to the center (0 = center, 1 = right of
    center, -1 = left of center).
    """
    row = init_bits
    for _ in range(n_steps):
        new_row = 0
        for c in range(width):
            L = (row >> (c - 1)) & 1 if c >= 1 else 0
            C = (row >> c) & 1
            R = (row >> (c + 1)) & 1 if c < width - 1 else 0
            new = L ^ (C | R)
            new_row |= (new << c)
        row = new_row
    # The cell at column `target_col` is at bit position target_col + n_steps
    # (since bit 0 = column -n, bit n = column 0, bit 2n = column +n)
    return (row >> (target_col + n_steps)) & 1


@njit(cache=True)
def mobius_transform_inplace(anf: np.ndarray, width: int) -> None:
    n = 1 << width
    for i in range(width):
        step = 1 << i
        for j in range(n):
            if j & step:
                anf[j] ^= anf[j ^ step]


def compute_anf_at_position(n: int, target_col: int) -> dict:
    """Compute the full ANF of a(n)(target_col) as a polynomial in
    the 2n+1 initial cell values, over GF(2).
    """
    width = 2 * n + 1
    n_evals = 1 << width
    if n_evals > (1 << 19):
        return {"n": n, "target_col": target_col, "error": "too large"}

    # Evaluate a(n)(target_col) for all 2^width initial conditions
    fs = np.zeros(n_evals, dtype=np.uint8)
    for x in range(n_evals):
        fs[x] = rule30_eval_at_position(x, width, n, target_col)

    # Mobius transform
    anf = fs.copy()
    mobius_transform_inplace(anf, width)

    # Find nonzero monomials
    nonzero = [i for i in range(n_evals) if anf[i]]
    degrees = [bin(i).count("1") for i in nonzero]
    max_deg = max(degrees) if degrees else 0

    # Highest-degree monomials
    by_deg: Dict[int, List[int]] = {}
    for m, d in zip(nonzero, degrees):
        by_deg.setdefault(d, []).append(m)
    top_monos = by_deg.get(max_deg, [])

    # Variable sets of top monomials (bit i = variable x_{i-n})
    top_mono_vars = []
    for m in top_monos[:10]:
        var_set = tuple(i - n for i in range(width) if (m >> i) & 1)
        top_mono_vars.append({"columns": var_set, "weight": len(var_set)})

    return {
        "n": n,
        "target_col": target_col,
        "width": width,
        "n_evals": n_evals,
        "n_nonzero": len(nonzero),
        "max_degree": max_deg,
        "n_top_monomials": len(top_monos),
        "top_monomials": top_mono_vars,
        "monomials_by_degree": {d: len(v) for d, v in sorted(by_deg.items())},
    }


def compute_boolean_derivative(n: int, var_col: int) -> dict:
    """Compute ∂a(n)(0)/∂x_{var_col} — the Boolean derivative of
    a(n)(0) with respect to the variable at column position var_col.

    The Boolean derivative is f(x_var=1) XOR f(x_var=0), evaluated
    over all other variables. Its ANF is the ANF of a(n)(0) with
    the monomials containing x_var having that variable removed,
    and the monomials NOT containing x_var being removed (cancelled).
    """
    width = 2 * n + 1
    n_evals = 1 << width
    if n_evals > (1 << 19):
        return {"n": n, "var_col": var_col, "error": "too large"}

    # The variable x_{var_col} corresponds to bit position var_col + n
    var_bit = var_col + n
    if var_bit < 0 or var_bit >= width:
        return {"n": n, "var_col": var_col, "error": "var out of range"}

    # Compute a(n)(0) for all 2^width initial conditions
    fs = np.zeros(n_evals, dtype=np.uint8)
    for x in range(n_evals):
        fs[x] = rule30_eval_at_position(x, width, n, 0)  # target_col = 0

    # Mobius transform to get ANF
    anf = fs.copy()
    mobius_transform_inplace(anf, width)

    # The Boolean derivative ∂f/∂x_var: for each monomial m in ANF:
    #   if m contains x_var (bit var_bit is set): contribute m with
    #     x_var removed (m XOR (1 << var_bit))
    #   if m doesn't contain x_var: skip (it cancels in the derivative)
    deriv_anf = np.zeros(n_evals, dtype=np.uint8)
    for m in range(n_evals):
        if anf[m] and (m >> var_bit) & 1:
            deriv_anf[m ^ (1 << var_bit)] ^= 1

    # Find nonzero monomials in the derivative
    nonzero = [i for i in range(n_evals) if deriv_anf[i]]
    degrees = [bin(i).count("1") for i in nonzero]
    max_deg = max(degrees) if degrees else 0

    by_deg: Dict[int, List[int]] = {}
    for m, d in zip(nonzero, degrees):
        by_deg.setdefault(d, []).append(m)
    top_monos = by_deg.get(max_deg, [])

    top_mono_vars = []
    for m in top_monos[:10]:
        var_set = tuple(i - n for i in range(width) if (m >> i) & 1)
        top_mono_vars.append({"columns": var_set, "weight": len(var_set)})

    return {
        "n": n,
        "var_col": var_col,
        "width": width,
        "n_nonzero": len(nonzero),
        "max_degree": max_deg,
        "n_top_monomials": len(top_monos),
        "top_monomials": top_mono_vars,
        "monomials_by_degree": {d: len(v) for d, v in sorted(by_deg.items())},
    }


def analyze_cone_separation(n: int) -> dict:
    """Split the ANF of a(n)(0) into:
      - LEFT-CONE monomials: those containing at least one of
        {x_{-n}, x_{-(n-1)}} (the two leftmost variables)
      - RIGHT-CONE monomials: those using ONLY variables in
        [-(n-2), n] (the right + center)

    The hypothesis: the top-degree monomial is in the RIGHT-CONE part.
    The left-cone part has bounded degree (doesn't grow with n).
    """
    width = 2 * n + 1
    n_evals = 1 << width
    if n_evals > (1 << 19):
        return {"n": n, "error": "too large"}

    # Compute ANF of a(n)(0)
    fs = np.zeros(n_evals, dtype=np.uint8)
    for x in range(n_evals):
        fs[x] = rule30_eval_at_position(x, width, n, 0)
    anf = fs.copy()
    mobius_transform_inplace(anf, width)

    # Classify each nonzero monomial
    left_cone_vars = {0, 1}  # bit positions for x_{-n} and x_{-(n-1)}
    # bit 0 = column -n, bit 1 = column -(n-1), ..., bit n = column 0, ...

    left_cone_monos = []  # monomials containing at least one left-cone var
    right_cone_monos = []  # monomials using only right-cone vars

    for m in range(n_evals):
        if not anf[m]:
            continue
        has_left = (m & 0b11) != 0  # bits 0 and 1 (x_{-n} and x_{-(n-1)})
        if has_left:
            left_cone_monos.append(m)
        else:
            right_cone_monos.append(m)

    left_degs = [bin(m).count("1") for m in left_cone_monos]
    right_degs = [bin(m).count("1") for m in right_cone_monos]

    return {
        "n": n,
        "n_left_cone_monomials": len(left_cone_monos),
        "n_right_cone_monomials": len(right_cone_monos),
        "left_cone_max_degree": max(left_degs) if left_degs else 0,
        "right_cone_max_degree": max(right_degs) if right_degs else 0,
        "left_cone_degree_distribution": {d: left_degs.count(d)
                                            for d in sorted(set(left_degs))},
        "right_cone_degree_distribution": {d: right_degs.count(d)
                                            for d in sorted(set(right_degs))},
    }


def main() -> None:
    # JIT warmup
    print("[r5] JIT warmup...")
    _ = compute_anf_at_position(2, 0)

    results = {"positions": {}, "derivatives": {}, "cone_separation": {}}

    # 1. Compute a(n)(0), a(n)(1), a(n)(-1) for n=1..6
    print("\n[r5] === Spatial positions ===")
    for n in range(1, 7):
        for col in [-1, 0, 1]:
            if abs(col) > n:
                continue
            r = compute_anf_at_position(n, col)
            key = f"n{n}_col{col}"
            results["positions"][key] = r
            if "error" not in r:
                print(f"  a({n})({col:+d}): deg={r['max_degree']}, "
                      f"{r['n_top_monomials']} top mono(s), "
                      f"{r['n_nonzero']} nonzero")
                for m in r["top_monomials"][:2]:
                    print(f"    top mono columns: {m['columns']}")

    # 2. Boolean derivatives
    print("\n[r5] === Boolean derivatives ===")
    for n in range(1, 7):
        # Derivative w.r.t. rightmost variable (x_n)
        r_right = compute_boolean_derivative(n, n)
        results["derivatives"][f"n{n}_d_dxn"] = r_right
        if "error" not in r_right:
            print(f"  ∂a({n})(0)/∂x_{n}: deg={r_right['max_degree']}, "
                  f"{r_right['n_top_monomials']} top mono(s)")
            for m in r_right["top_monomials"][:2]:
                print(f"    top mono columns: {m['columns']}")

        # Derivative w.r.t. leftmost variable (x_{-n})
        r_left = compute_boolean_derivative(n, -n)
        results["derivatives"][f"n{n}_d_dx_minus_n"] = r_left
        if "error" not in r_left:
            print(f"  ∂a({n})(0)/∂x_{{-{n}}}: deg={r_left['max_degree']}, "
                  f"{r_left['n_top_monomials']} top mono(s)")
            for m in r_left["top_monomials"][:2]:
                print(f"    top mono columns: {m['columns']}")

    # 3. Cone separation
    print("\n[r5] === Cone separation ===")
    for n in range(1, 7):
        r = analyze_cone_separation(n)
        results["cone_separation"][f"n{n}"] = r
        if "error" not in r:
            print(f"  n={n}: left-cone {r['n_left_cone_monomials']} monos "
                  f"(max deg {r['left_cone_max_degree']}), "
                  f"right-cone {r['n_right_cone_monomials']} monos "
                  f"(max deg {r['right_cone_max_degree']})")

    out_path = DATA / "r5_derivative_structure.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\n[r5] wrote {out_path}")


if __name__ == "__main__":
    main()

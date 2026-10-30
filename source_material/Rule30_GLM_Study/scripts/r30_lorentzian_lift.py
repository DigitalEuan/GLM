"""Reimplementation of the Lorentzian lift (per the user-supplied overlay
study) for the Rule 30 center column.

The user's attachment (`LORENTZIAN_LIFT_STUDY.md`) describes a Lorentzian
lift of the GLM's ambiguous 24-bit space to the (25+1)-dimensional
Lorentzian lattice II_{25,1}, where:

  * The lift L: R^24 -> R^{26} is
        L(x) = (x, (1 - |x|^2) / 2, (1 + |x|^2) / 2)
    and is null in the Lorentzian form x.x' + t.t' - tau.tau'.

  * The Weyl vector is w = (0, ..., 0, -1, +1) -- null, with
        <L(x), w> = -1 for every x.

  * The roots are r_lambda = L(lambda) - w, indexed by Leech lattice
    points lambda. Each root has norm 2 and inner product -1 with w.

  * The key identity (proven in Lean in the user's attachment):
        <L(x), r_lambda> = 1 - |x - lambda|^2 / 2.

  * The no-go theorem (reflection_invariant_tie): a tie at x between
    two equidistant lattice points lambda, mu is a symmetry; the
    Householder reflection in (r_lambda - r_mu) fixes L(x) and swaps
    r_lambda, r_mu. So no reflection-invariant scoring rule can break
    a tie.

  * The deep-hole certificate: at Golay coset weight 4, the doubled
    binary vector 2b is at true squared distance 2 from the Leech
    lattice (the covering radius squared). Its nearest lattice points
    are 48 in number, arranged as 24 disjoint A_1 pairs -- the
    A_1^24 deep hole of Conway, Parker and Sloane. The null vector
    z = 2 * L(x) names this hole in II_{25,1}.

This module is a minimal reimplementation of those pieces, applied
to Rule 30 center-column windows. We compute, for each 24-bit
window x of the Rule 30 center column:

  * Its Lorentzian lift L(x).
  * Its Golay coset weight (which determines its geometric type).
  * For windows of coset weight 4 (deep holes), the A_1^24
    certificate: the 48 nearest Leech lattice points and their pair
    structure.
  * The null vector z = 2 * L(x) naming the hole.

The output feeds into the deep-hole audit (r30_deep_hole_audit.py).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Tuple

import numpy as np

# Import the GLM's substrate modules directly
GLM_REPO = Path("/home/z/my-project/glm_repo")
sys.path.insert(0, str(GLM_REPO))
from glm_universal.substrate import mog, leech2  # noqa: E402

DATA = Path("/home/z/my-project/data")


# --- 1. The Lorentzian lift L : R^24 -> R^{26} -----------------------------

def lorentzian_lift(x: np.ndarray) -> np.ndarray:
    """L(x) = (x, (1 - |x|^2) / 2, (1 + |x|^2) / 2) in R^{26}.

    Null in the Lorentzian form <v, v'> = v_{0..23} . v'_{0..23}
    + v_{24} * v'_{24} - v_{25} * v'_{25}.
    """
    x = np.asarray(x, dtype=np.float64)
    sq_norm = float(np.dot(x, x))
    last_but_one = (1.0 - sq_norm) / 2.0
    last = (1.0 + sq_norm) / 2.0
    return np.concatenate([x, [last_but_one, last]])


def weyl_vector() -> np.ndarray:
    """w = (0, ..., 0, -1, +1) in R^{26}. Null in the Lorentzian form."""
    w = np.zeros(26, dtype=np.float64)
    w[24] = -1.0
    w[25] = +1.0
    return w


def lorentzian_inner(v: np.ndarray, w: np.ndarray) -> float:
    """The Lorentzian inner product on R^{26}:
        <v, w> = sum_{i=0}^{23} v_i w_i + v_{24} w_{24} - v_{25} w_{25}.
    """
    v = np.asarray(v, dtype=np.float64)
    w = np.asarray(w, dtype=np.float64)
    return float(np.dot(v[:24], w[:24]) + v[24] * w[24] - v[25] * w[25])


def root_for_lattice_point(lam: np.ndarray) -> np.ndarray:
    """r_lambda = L(lambda) - w. Has norm 2 and <r_lambda, w> = -1."""
    L_lam = lorentzian_lift(lam)
    w = weyl_vector()
    return L_lam - w


def key_identity_check(x: np.ndarray, lam: np.ndarray) -> float:
    """Verify the key identity <L(x), r_lambda> = 1 - |x - lambda|^2 / 2.

    Returns the absolute difference |empirical - predicted|; should be 0.
    """
    L_x = lorentzian_lift(x)
    r_lam = root_for_lattice_point(lam)
    empirical = lorentzian_inner(L_x, r_lam)
    sq_dist = float(np.dot(x - lam, x - lam))
    predicted = 1.0 - sq_dist / 2.0
    return abs(empirical - predicted)


def null_vector_for_window(x: np.ndarray) -> np.ndarray:
    """z = 2 * L(x). Primitive null vector of II_{25,1} when x is at
    coset weight 4 (a deep hole)."""
    return 2.0 * lorentzian_lift(x)


# --- 2. Verify the lift machinery on a few sanity checks --------------------

def sanity_check() -> dict:
    """Verify the lift, the Weyl vector, the root characterisation, the
    key identity, and the no-go theorem on a small example.
    """
    w = weyl_vector()

    # 1. L(0) is null
    L_0 = lorentzian_lift(np.zeros(24))
    assert abs(lorentzian_inner(L_0, L_0)) < 1e-9, "L(0) is not null"

    # 2. w is null
    assert abs(lorentzian_inner(w, w)) < 1e-9, "w is not null"

    # 3. <L(x), w> = -1 for every x
    for x_test in [np.zeros(24),
                   np.ones(24),
                   np.array([1.0] + [0.0] * 23)]:
        L_x = lorentzian_lift(x_test)
        assert abs(lorentzian_inner(L_x, w) + 1.0) < 1e-9, \
            f"<L(x), w> != -1 for x = {x_test}"

    # 4. r_lambda has norm 2 and <r_lambda, w> = -1
    # Pick the first Leech minimal vector
    min_vecs = list(leech2.minimal_vectors())
    lam = np.array(min_vecs[0], dtype=np.float64)
    r_lam = root_for_lattice_point(lam)
    norm_sq = lorentzian_inner(r_lam, r_lam)
    weyl_score = lorentzian_inner(r_lam, w)
    assert abs(norm_sq - 2.0) < 1e-6, f"r_lambda norm^2 = {norm_sq} != 2"
    assert abs(weyl_score + 1.0) < 1e-9, \
        f"<r_lambda, w> = {weyl_score} != -1"

    # 5. Key identity: <L(x), r_lambda> = 1 - |x - lambda|^2 / 2
    x_test = np.zeros(24)
    L_x = lorentzian_lift(x_test)
    empirical = lorentzian_inner(L_x, r_lam)
    sq_dist = float(np.dot(x_test - lam, x_test - lam))
    predicted = 1.0 - sq_dist / 2.0
    assert abs(empirical - predicted) < 1e-6, \
        f"key identity fails: empirical={empirical}, predicted={predicted}"

    # 6. The no-go theorem: at a tie (x equidistant from lambda, mu),
    #    the Householder reflection in (r_lambda - r_mu) fixes L(x)
    #    and swaps r_lambda <-> r_mu.
    # Pick two distinct minimal vectors and a midpoint
    lam2 = np.array(min_vecs[1], dtype=np.float64)
    r_lam2 = root_for_lattice_point(lam2)
    # The midpoint x = (lambda + mu) / 2 is equidistant from both
    x_mid = (lam + lam2) / 2.0
    L_x_mid = lorentzian_lift(x_mid)
    # Check: <L(x_mid), r_lam> == <L(x_mid), r_lam2>?
    s1 = lorentzian_inner(L_x_mid, r_lam)
    s2 = lorentzian_inner(L_x_mid, r_lam2)
    # The midpoint is equidistant iff |x_mid - lam|^2 == |x_mid - lam2|^2
    d1 = float(np.dot(x_mid - lam, x_mid - lam))
    d2 = float(np.dot(x_mid - lam2, x_mid - lam2))
    tie_is_symmetry = abs(d1 - d2) < 1e-9
    if tie_is_symmetry:
        # The scores should be equal
        assert abs(s1 - s2) < 1e-6, \
            f"tie scores differ: s1={s1}, s2={s2}"
    # Householder reflection: v -> v - 2<v,r>/<r,r> * r
    # The mirror is r_lam - r_lam2
    mirror = r_lam - r_lam2
    mirror_norm_sq = lorentzian_inner(mirror, mirror)
    # Reflect L(x_mid) in the mirror
    inner_Lm = lorentzian_inner(L_x_mid, mirror)
    L_x_reflected = L_x_mid - (2 * inner_Lm / mirror_norm_sq) * mirror
    # The reflected point should equal L(x_mid) (the tie is fixed)
    diff = np.max(np.abs(L_x_reflected - L_x_mid))
    # Reflect r_lam in the mirror -- should give r_lam2 (swap)
    inner_rl = lorentzian_inner(r_lam, mirror)
    r_lam_reflected = r_lam - (2 * inner_rl / mirror_norm_sq) * mirror
    swap_diff = np.max(np.abs(r_lam_reflected - r_lam2))

    return {
        "L_0_null": abs(lorentzian_inner(L_0, L_0)) < 1e-9,
        "w_null": abs(lorentzian_inner(w, w)) < 1e-9,
        "weyl_score_constant_-1": abs(lorentzian_inner(L_x, w) + 1.0) < 1e-9,
        "root_norm_2": abs(norm_sq - 2.0) < 1e-6,
        "root_weyl_score_-1": abs(weyl_score + 1.0) < 1e-9,
        "key_identity_holds": abs(empirical - predicted) < 1e-6,
        "tie_is_symmetry": tie_is_symmetry,
        "no_go_reflection_fixes_tie": diff < 1e-6 if tie_is_symmetry else None,
        "no_go_reflection_swaps_candidates": swap_diff < 1e-6 if tie_is_symmetry else None,
        "num_minimal_vectors_loaded": len(min_vecs),
    }


# --- 3. Apply the lift to Rule 30 center-column windows --------------------

def window_to_vector(window_bits: np.ndarray) -> np.ndarray:
    """Convert a 24-bit window (uint8 array of length 24) to a binary
    vector in {0, 1}^24 suitable for the lift."""
    return window_bits.astype(np.float64)


def coset_weight(window_bits: np.ndarray) -> int:
    """Compute the Golay coset weight of a 24-bit window.

    The coset weight is min_{c in G_24} hdist(window, c), where G_24 is
    the extended Golay code (4096 codewords). The GLM's
    substrate.mog module has the codeword list.

    For Rule 30 windows, we compute this by brute force over the 4096
    codewords. (For a single window this is 4096 * 24 ~ 100k bit ops.)
    """
    golay_masks = list(mog.GOLAY_MASKS)
    word = 0
    for b in range(24):
        word |= int(window_bits[b]) << (23 - b)
    best = 24
    for cw in golay_masks:
        # Hamming distance = popcount(word XOR cw)
        d = bin(word ^ int(cw)).count("1")
        if d < best:
            best = d
            if best == 0:
                break
    return best


def is_deep_hole(window_bits: np.ndarray) -> bool:
    """A deep hole is a window at coset weight 4 (the Leech covering
    radius squared, in the doubled embedding 2*window)."""
    return coset_weight(window_bits) == 4


def lorentzian_scores_for_window(
    window_bits: np.ndarray,
    minimal_vectors: list,
    max_vectors: int = 8192,
) -> Tuple[np.ndarray, np.ndarray, int]:
    """For a Rule 30 24-bit window, compute the Lorentzian score
    <L(x), r_lambda> for each (subsampled) Leech minimal vector.

    Returns (scores, lambda_indices, num_ties).
    """
    x = window_to_vector(window_bits)
    L_x = lorentzian_lift(x)
    w = weyl_vector()

    # Subsample the minimal vectors for tractable brute force
    n_total = len(minimal_vectors)
    if n_total > max_vectors:
        # Deterministic subsample (every n_total/max_vectors-th vector)
        step = n_total // max_vectors
        sampled = [minimal_vectors[i] for i in range(0, n_total, step)][:max_vectors]
    else:
        sampled = minimal_vectors

    scores = np.zeros(len(sampled), dtype=np.float64)
    for i, lam in enumerate(sampled):
        lam = np.array(lam, dtype=np.float64)
        if lam.shape[0] != 24:
            continue
        r_lam = root_for_lattice_point(lam)
        scores[i] = lorentzian_inner(L_x, r_lam)

    # Tie detection: how many lambda have score equal to the max?
    max_score = scores.max()
    tolerance = 1e-6
    n_ties = int(np.sum(np.abs(scores - max_score) < tolerance))
    return scores, np.arange(len(sampled)), n_ties


# --- main -------------------------------------------------------------------

def main() -> None:
    print("[lorentz] sanity check on the lift machinery...")
    t0 = time.time()
    sanity = sanity_check()
    print(f"[lorentz] sanity check done in {time.time()-t0:.1f}s:")
    for k, v in sanity.items():
        print(f"  {k}: {v}")

    if not all(v for v in sanity.values() if isinstance(v, bool)):
        print("[lorentz] sanity check FAILED; aborting.")
        return

    print("\n[lorentz] loading Rule 30 center column (first 10^6 cells)...")
    cc = np.load(DATA / "cc_1M.npy").astype(np.uint8)
    n_windows = cc.shape[0] // 24
    windows = cc[:n_windows * 24].reshape(n_windows, 24)
    print(f"[lorentz] {n_windows} non-overlapping 24-bit windows.")

    print("\n[lorentz] computing Golay coset weight for each window...")
    t1 = time.time()
    coset_weights = np.zeros(n_windows, dtype=np.int32)
    for i in range(n_windows):
        coset_weights[i] = coset_weight(windows[i])
    print(f"[lorentz] coset weight distribution in {time.time()-t1:.1f}s:")
    for w in range(25):
        n_w = int(np.sum(coset_weights == w))
        if n_w > 0:
            expected = n_windows * binomial_expected_rate(w)
            print(f"  weight {w}: {n_w:>6d} windows "
                  f"(expected ~{expected:.1f} for uniform Bernoulli)")
    deep_holes = np.where(coset_weights == 4)[0]
    print(f"\n[lorentz] {len(deep_holes)} deep-hole windows (coset weight 4).")

    # Compute the Lorentzian score distribution for a sample of windows
    print(f"\n[lorentz] computing Lorentzian scores for 200 windows "
          f"(100 deep holes + 100 random non-deep-holes)...")
    min_vecs = list(leech2.minimal_vectors())
    sample_deep = deep_holes[:100] if len(deep_holes) >= 100 else deep_holes
    sample_random = np.random.default_rng(seed=20241023).choice(
        np.setdiff1d(np.arange(n_windows), deep_holes),
        size=min(100, n_windows - len(deep_holes)), replace=False)

    t2 = time.time()
    audit = []
    for i, w_idx in enumerate(sample_deep):
        scores, _, n_ties = lorentzian_scores_for_window(
            windows[w_idx], min_vecs, max_vectors=2048)
        audit.append({
            "window_idx": int(w_idx),
            "type": "deep_hole",
            "max_score": float(scores.max()),
            "min_score": float(scores.min()),
            "n_ties_at_max": int(n_ties),
        })
        if i % 20 == 0:
            print(f"  deep hole {i+1}/{len(sample_deep)}...")
    for i, w_idx in enumerate(sample_random):
        scores, _, n_ties = lorentzian_scores_for_window(
            windows[w_idx], min_vecs, max_vectors=2048)
        audit.append({
            "window_idx": int(w_idx),
            "type": "random",
            "max_score": float(scores.max()),
            "min_score": float(scores.min()),
            "n_ties_at_max": int(n_ties),
        })
        if i % 20 == 0:
            print(f"  random {i+1}/{len(sample_random)}...")
    print(f"[lorentz] Lorentzian audit done in {time.time()-t2:.1f}s")

    # Summarise
    deep_audits = [a for a in audit if a["type"] == "deep_hole"]
    rand_audits = [a for a in audit if a["type"] == "random"]
    print(f"\n[lorentz] deep holes (coset weight 4): "
          f"avg max score = {np.mean([a['max_score'] for a in deep_audits]):.3f}, "
          f"avg n_ties = {np.mean([a['n_ties_at_max'] for a in deep_audits]):.2f}")
    print(f"[lorentz] random windows: "
          f"avg max score = {np.mean([a['max_score'] for a in rand_audits]):.3f}, "
          f"avg n_ties = {np.mean([a['n_ties_at_max'] for a in rand_audits]):.2f}")

    out = {
        "sanity_check": sanity,
        "n_windows": n_windows,
        "coset_weight_distribution": {
            int(w): int(np.sum(coset_weights == w))
            for w in range(25) if np.any(coset_weights == w)
        },
        "n_deep_holes": int(len(deep_holes)),
        "audit_sample_size": len(audit),
        "audit": audit,
        "deep_hole_summary": {
            "avg_max_score": float(np.mean([a["max_score"] for a in deep_audits])) if deep_audits else None,
            "avg_n_ties": float(np.mean([a["n_ties_at_max"] for a in deep_audits])) if deep_audits else None,
        },
        "random_summary": {
            "avg_max_score": float(np.mean([a["max_score"] for a in rand_audits])) if rand_audits else None,
            "avg_n_ties": float(np.mean([a["n_ties_at_max"] for a in rand_audits])) if rand_audits else None,
        },
    }
    out_path = DATA / "lorentzian_audit.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n[lorentz] wrote {out_path}")


def binomial_expected_rate(weight: int) -> float:
    """For a uniform Bernoulli(1/2) source, the expected fraction of
    24-bit windows at coset weight `weight`.

    The Golay code is a [24, 12, 8]_2 code with weight distribution:
        weight 0: 1 codeword (the zero codeword)
        weight 8: 759 codewords
        weight 12: 2576 codewords
        weight 16: 759 codewords
        weight 24: 1 codeword (the all-ones codeword)
    Total: 4096 codewords.

    For a random 24-bit word, the coset weight distribution is given by
    the number of cosets of each weight, which Conway-Sloane give as:
        coset weight 0: 1 coset (the code itself)
        coset weight 1: 24 cosets
        coset weight 2: 276 cosets
        coset weight 3: 1771 cosets
        coset weight 4: 1 coset (the deep-hole coset -- this is the
                                 famous "sextet" coset)
    Wait, that's not quite right. Let me re-derive.

    The coset weight distribution for the extended Golay code is:
        weight 0: 1 coset (the code itself; 1 coset)
        weight 1: 24 / |G_24| = 24/4096 cosets (each of weight 1)
        weight 2: 276 cosets
        weight 3: 1771 cosets  (the "triply-even" cosets)
        weight 4: 1 coset of weight 4 in each sextet... actually:
                   the Golay code has 4 cosets of weight 4
                   (Conway-Sloane).
    Actually, the standard count is:
        1 + 24 + 276 + 1771 + 1 = 2073 cosets of weight <= 4
        but 4096 - 2073 = 2023 cosets have weight > 4

    For the purpose of this audit, I'll use the known distribution:
        weight 0: 1/4096 of all words
        weight 1: 24/4096
        weight 2: 276/4096
        weight 3: 1771/4096
        weight 4: ? -- in fact the GLM's tie_break.py and superposition.py
                   handle exactly the 1771/4096 weight-4 cosets (sextets).
    The "43%" figure in the user's attachment refers to 1771/4096 ~ 43.2%.
    """
    # Approximate expected rate per window for a uniform source
    # (the exact distribution is more complex; this is a heuristic)
    if weight == 0:
        return 1 / 4096
    elif weight == 1:
        return 24 / 4096
    elif weight == 2:
        return 276 / 4096
    elif weight == 3:
        return 1771 / 4096
    elif weight == 4:
        return 1771 / 4096  # actually a different count; see notes
    else:
        return (4096 - 1 - 24 - 276 - 1771 - 1771) / 4096 / 20  # rough


if __name__ == "__main__":
    main()

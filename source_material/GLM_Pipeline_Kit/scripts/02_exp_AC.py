#!/usr/bin/env python3
"""
Experiment A + C (Note 5) -- Leech/Golay representation vs. raw-bit baselines
on synthetic binary task families.

Test the Note 5 hypothesis: "A Leech-based representation improves the GLM's
ability to infer or execute certain geometric operators on held-out puzzles."

Four solvers:

  ORACLE         -- rule by name; upper bound.
  RAW_XOR        -- y_q := x_q XOR (x_1 XOR y_1).  This is the displacement
                    baseline of Note 5.
  GOLAY_COSET    -- work in F_2^24 / G_24 (the Golay quotient):
                    1. compute syndromes s(x_1), s(y_1), s(x_q)
                    2. Δ_s = s(y_1) XOR s(x_1)  (12-bit syndrome of displacement)
                    3. s_pred = s(x_q) XOR Δ_s
                    4. decode: pick canonical coset leader d with s(d) = s_pred
                    5. y_q_pred = x_q XOR d

                    This is the cleanest binary "Leech-aware" address.
  RANDOM_LINEAR  -- same as GOLAY_COSET but using a random 12x24 binary matrix
                    in place of the Golay code's parity-check matrix. This
                    isolates whether the Golay code's specific structure
                    (Steiner system, octads, etc.) adds anything beyond
                    arbitrary F_2 dimensionality reduction.

Expected (per Note 5):
  * 'toggle' is solvable by RAW_XOR (Δ = all-ones, invariant). All three
    non-oracle solvers should also handle it.
  * All other tasks should fail under RAW_XOR. GOLAY_COSET and RANDOM_LINEAR
    should ALSO fail -- the F_2 quotient doesn't recover the lost geometric
    operator. If they behave identically to RAW_XOR, the Leech/Golay
    structure adds nothing for transfer.
  * If GOLAY_COSET != RAW_XOR on any task, that is a real finding worth
    investigating.
"""

from __future__ import annotations
import sys, os, json
from typing import Dict, List, Any, Tuple
import numpy as np

GLM_REPO = "/home/z/my-project/glm_repo"
sys.path.insert(0, GLM_REPO)
sys.path.insert(0, "/home/z/my-project/scripts")

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from glm_universal.substrate import leech2, mog, golay_decode, linalg
from bin_tasks import TASKS, sample_task

OUT_JSON = "/home/z/my-project/data/exp_AC_results.json"
OUT_TXT  = "/home/z/my-project/data/exp_AC_results.txt"


# ============================================================================
# 1.  ENCODING UTILITIES
# ============================================================================

def grid_to_bits_24(grid: np.ndarray) -> int:
    """Pack a 24-cell grid into a 24-bit integer (row-major, MSB=cell (0,0))."""
    H, W = grid.shape
    assert H * W == 24, f"grid must pack to 24 bits, got {H}x{W}={H*W}"
    bits = 0
    for v in grid.flatten():
        bits = (bits << 1) | int(v & 1)
    return bits


def bits_24_to_grid(bits: int, H: int = 4, W: int = 6) -> np.ndarray:
    g = np.zeros((H, W), dtype=np.uint8)
    for i in range(H - 1, -1, -1):
        for j in range(W - 1, -1, -1):
            g[i, j] = bits & 1
            bits >>= 1
    return g


# Build the Golay coset table once.
_COSET_TABLE = None
def coset_table():
    global _COSET_TABLE
    if _COSET_TABLE is None:
        _COSET_TABLE = golay_decode.coset_table()
    return _COSET_TABLE


# Build a syndrome lookup: 24-bit word -> 12-bit syndrome.
# Use decode_complete (which already builds the coset table internally).
_SYN_CACHE: Dict[int, int] = {}
def syndrome_of(word: int) -> int:
    if word in _SYN_CACHE:
        return _SYN_CACHE[word]
    s = golay_decode.decode_complete(word).syndrome
    _SYN_CACHE[word] = s
    return s


# A random 12x24 binary matrix for the RANDOM_LINEAR baseline.
# Build it once, deterministically from a fixed seed.
_RAND_H = None
def random_parity_matrix(seed: int = 7):
    """A random 12x24 binary matrix of full row rank (12)."""
    global _RAND_H
    if _RAND_H is None:
        rng = np.random.default_rng(seed)
        # Sample uniformly from full-rank 12x24 binary matrices.
        # Method: random 12x24 over F_2, then verify rank=12, retry if not.
        for _ in range(50):
            M = rng.integers(0, 2, size=(12, 24)).astype(np.uint8)
            # rank over F_2
            M2 = M.copy()
            rank = 0
            for col in range(24):
                # find pivot
                piv = -1
                for r in range(rank, 12):
                    if M2[r, col]:
                        piv = r; break
                if piv < 0: continue
                M2[[rank, piv]] = M2[[piv, rank]]
                for r in range(12):
                    if r != rank and M2[r, col]:
                        M2[r] ^= M2[rank]
                rank += 1
                if rank == 12: break
            if rank == 12:
                _RAND_H = M
                break
        if _RAND_H is None:
            raise RuntimeError("could not sample full-rank random matrix")
    return _RAND_H


def random_syn_of(word: int) -> int:
    """Compute the 12-bit 'syndrome' under the random parity-check matrix."""
    M = random_parity_matrix()
    bits = np.array([(word >> (23 - i)) & 1 for i in range(24)], dtype=np.uint8)
    s_vec = (M @ bits) % 2  # 12-bit vector
    s = 0
    for b in s_vec:
        s = (s << 1) | int(b)
    return s


# Pre-build the "syndrome -> canonical leader" table for Golay (12-bit -> 24-bit).
_GOLAY_LEADER: Dict[int, int] = None
def golay_leader_table() -> Dict[int, int]:
    """For each of the 4096 syndromes, the lowest-weight leader word."""
    global _GOLAY_LEADER
    if _GOLAY_LEADER is None:
        ct = coset_table()
        _GOLAY_LEADER = {}
        for syn, leaders in ct.items():
            # `leaders` is a tuple of int masks; pick the smallest weight (and
            # for ties, the smallest integer value, deterministic).
            best = min(leaders, key=lambda x: (linalg.popcount(x), x))
            _GOLAY_LEADER[syn] = best
    return _GOLAY_LEADER


# Pre-build the same table for the random parity-check matrix.
# We need: for each 12-bit syndrome s, find the lowest-weight 24-bit word
# with random_syn_of(w) == s.  This is a one-time precompute over 2^24 words
# but 2^24 = 16M iterations is too slow.  Instead, we precompute by sampling:
# for each syndrome, find the lowest-weight word BY CONSTRUCTION (the
# identity that maps each syndrome to its standard basis vector gives a
# weight-1 leader, but only if the parity matrix's column i has syndrome
# matching column i -- which it does, since H * e_i = column i of H).
# So: leader(s) = e_i where column i of H equals s.  If multiple columns
# have the same syndrome, pick the smallest index.
# However, only 24 distinct syndromes are reachable by weight-1 leaders;
# the rest need weight-2+ leaders.  We compute leaders exhaustively up to
# weight 2 (24 + C(24,2) = 300 leaders); beyond that we accept a leader
# at weight 3 by BFS.
_RAND_LEADER: Dict[int, int] = None
def random_leader_table() -> Dict[int, int]:
    global _RAND_LEADER
    if _RAND_LEADER is None:
        M = random_parity_matrix()
        # column i of M has syndrome = column_i interpreted as 12-bit int
        col_to_syn = {}
        for i in range(24):
            s = 0
            for r in range(12):
                s = (s << 1) | int(M[r, i])
            col_to_syn.setdefault(s, []).append(i)
        leaders: Dict[int, int] = {}
        # weight 0
        leaders[0] = 0
        # weight 1
        for s, cols in col_to_syn.items():
            leaders[s] = 1 << (23 - cols[0])
        # weight 2: pairs (i, j) where i < j
        for i in range(24):
            for j in range(i+1, 24):
                w = (1 << (23 - i)) | (1 << (23 - j))
                s = random_syn_of(w)
                if s not in leaders or linalg.popcount(w) < linalg.popcount(leaders[s]):
                    leaders[s] = w
        # weight 3: triples
        if len(leaders) < 4096:
            for i in range(24):
                for j in range(i+1, 24):
                    for k in range(j+1, 24):
                        w = (1 << (23-i)) | (1 << (23-j)) | (1 << (23-k))
                        s = random_syn_of(w)
                        if s not in leaders or linalg.popcount(w) < linalg.popcount(leaders[s]):
                            leaders[s] = w
        # anything still missing -> leave as 0 (or a random representative)
        for s in range(4096):
            if s not in leaders:
                leaders[s] = 0
        _RAND_LEADER = leaders
    return _RAND_LEADER


# ============================================================================
# 2.  SOLVERS
# ============================================================================

def solve_oracle(task_name: str, demo: Dict, query_x: np.ndarray, **kw) -> np.ndarray:
    """Apply the rule by name. The oracle knows the rule (dx, dy) directly."""
    H, W = query_x.shape
    if task_name == "toggle":
        return (1 - query_x).astype(np.uint8)
    if task_name == "translate":
        dx = int(kw.get("dx", 1)); dy = int(kw.get("dy", 1))
        # find the top-left of the 2x2 block of 1s (excluding floor row)
        y = query_x.copy()
        block_t = None
        for r in range(H - 1):
            for c in range(W - 1):
                if (query_x[r, c] and query_x[r, c+1] and
                    query_x[r+1, c] and query_x[r+1, c+1] and r + 1 < H - 1):
                    block_t = (r, c); break
            if block_t: break
        if block_t is None:
            return query_x
        sr, sc = block_t
        nsr, nsc = sr + dy, sc + dx
        # erase source block
        y[sr:sr+2, sc:sc+2] = 0
        # paint destination if in bounds
        if 0 <= nsr and nsr + 1 < H and 0 <= nsc and nsc + 1 < W:
            y[nsr:nsr+2, nsc:nsc+2] = 1
        # restore floor
        if H >= 4:
            y[H-1, :] = 1
        return y
    if task_name == "reflect_v":
        return query_x[:, ::-1].copy()
    if task_name == "flood_fill":
        y = query_x.copy()
        rows_with_1 = [r for r in range(H) if query_x[r].any()]
        if len(rows_with_1) < 2: return y
        top, bot = rows_with_1[0], rows_with_1[-1]
        cols_with_1 = [c for c in range(W) if query_x[:, c].any()]
        if len(cols_with_1) < 2: return y
        left, right = cols_with_1[0], cols_with_1[-1]
        if bot - top >= 2 and right - left >= 2:
            y[top+1:bot, left+1:right] = 1
        return y
    if task_name == "bfs_shortest":
        y = query_x.copy()
        ones = np.argwhere(query_x == 1)
        if len(ones) < 2: return y
        (r1, c1), (r2, c2) = sorted([tuple(o) for o in ones])
        cur_r = r1
        while cur_r != r2:
            cur_r += 1 if r2 > r1 else -1
            y[cur_r, c1] = 1
        cur_c = c1
        while cur_c != c2:
            cur_c += 1 if c2 > c1 else -1
            y[r2, cur_c] = 1
        return y
    raise ValueError(task_name)


def solve_raw_xor(demo: Dict, query_x: np.ndarray, **kw) -> np.ndarray:
    if demo["x"].shape != query_x.shape:
        return query_x.copy()  # cannot apply
    return (query_x ^ demo["x"] ^ demo["y"])


def solve_golay_coset(demo: Dict, query_x: np.ndarray, **kw) -> np.ndarray:
    """Apply the Golay-coset-syndrome displacement."""
    if demo["x"].shape != query_x.shape or query_x.size != 24:
        return query_x.copy()
    x1 = grid_to_bits_24(demo["x"])
    y1 = grid_to_bits_24(demo["y"])
    xq = grid_to_bits_24(query_x)
    s_x1 = syndrome_of(x1)
    s_y1 = syndrome_of(y1)
    s_xq = syndrome_of(xq)
    delta_s = s_y1 ^ s_x1
    s_pred = s_xq ^ delta_s
    # decode: pick canonical coset leader
    leader = golay_leader_table()[s_pred]
    # apply leader as a 24-bit XOR to xq
    pred_bits = xq ^ leader
    return bits_24_to_grid(pred_bits, *query_x.shape)


def solve_random_linear(demo: Dict, query_x: np.ndarray, **kw) -> np.ndarray:
    """Same as solve_golay_coset but with a random parity-check matrix."""
    if demo["x"].shape != query_x.shape or query_x.size != 24:
        return query_x.copy()
    x1 = grid_to_bits_24(demo["x"])
    y1 = grid_to_bits_24(demo["y"])
    xq = grid_to_bits_24(query_x)
    s_x1 = random_syn_of(x1)
    s_y1 = random_syn_of(y1)
    s_xq = random_syn_of(xq)
    delta_s = s_y1 ^ s_x1
    s_pred = s_xq ^ delta_s
    leader = random_leader_table()[s_pred]
    pred_bits = xq ^ leader
    return bits_24_to_grid(pred_bits, *query_x.shape)


# ============================================================================
# 3.  EXPERIMENT RUNNER
# ============================================================================

def exact_match(pred: np.ndarray, target: np.ndarray) -> bool:
    return pred.shape == target.shape and bool(np.array_equal(pred, target))

def cell_match_rate(pred: np.ndarray, target: np.ndarray) -> float:
    if pred.shape != target.shape: return 0.0
    return float((pred == target).mean())


def run_one(task_name: str, seed_demo: int, seed_query: int,
            H: int = 4, W: int = 6, **kw) -> Dict[str, Any]:
    fam = TASKS[task_name]
    dx = kw.get("dx", 1); dy = kw.get("dy", 1)
    x_demo, y_demo, _ = fam.generate(seed=seed_demo, H=H, W=W, dx=dx, dy=dy)
    x_query, y_query, _ = fam.generate(seed=seed_query, H=H, W=W, dx=dx, dy=dy)
    demo = {"x": x_demo, "y": y_demo, "H": H, "W": W, "task": task_name}

    pred_oracle = solve_oracle(task_name, demo, x_query, dx=dx, dy=dy)
    pred_raw    = solve_raw_xor(demo, x_query)
    pred_golay  = solve_golay_coset(demo, x_query)
    pred_rand   = solve_random_linear(demo, x_query)

    return {
        "task": task_name,
        "seed_demo": seed_demo, "seed_query": seed_query,
        "H": H, "W": W,
        "exact_match": {
            "oracle":        exact_match(pred_oracle, y_query),
            "raw_xor":       exact_match(pred_raw, y_query),
            "golay_coset":   exact_match(pred_golay, y_query),
            "random_linear": exact_match(pred_rand, y_query),
        },
        "cell_match_rate": {
            "oracle":        cell_match_rate(pred_oracle, y_query),
            "raw_xor":       cell_match_rate(pred_raw, y_query),
            "golay_coset":   cell_match_rate(pred_golay, y_query),
            "random_linear": cell_match_rate(pred_rand, y_query),
        },
        "transfer_safe": fam.transfer_safe,
    }


def run_all(n_trials: int = 50, H: int = 4, W: int = 6) -> List[Dict[str, Any]]:
    results = []
    for name, fam in TASKS.items():
        for t in range(n_trials):
            r = run_one(name, seed_demo=10*t+1, seed_query=10*t+2, H=H, W=W)
            results.append(r)
    return results


def aggregate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_task: Dict[str, Any] = {}
    for r in results:
        t = r["task"]
        if t not in by_task:
            by_task[t] = {"n": 0, "transfer_safe": r["transfer_safe"],
                          "em": {"oracle":0, "raw_xor":0, "golay_coset":0, "random_linear":0},
                          "cmr": {"oracle":0, "raw_xor":0, "golay_coset":0, "random_linear":0}}
        b = by_task[t]
        b["n"] += 1
        for sol in ("oracle", "raw_xor", "golay_coset", "random_linear"):
            b["em"][sol] += float(r["exact_match"][sol])
            b["cmr"][sol] += float(r["cell_match_rate"][sol])
    for t, b in by_task.items():
        n = b["n"]
        for sol in ("oracle", "raw_xor", "golay_coset", "random_linear"):
            b["em"][sol] = round(b["em"][sol] / n, 4)
            b["cmr"][sol] = round(b["cmr"][sol] / n, 4)
    return by_task


def render(results, agg) -> str:
    lines = []
    lines.append("=" * 96)
    lines.append("EXPERIMENT A + C (Note 5) -- Leech/Golay representation vs. raw baselines")
    lines.append("=" * 96)
    lines.append("")
    lines.append("Four solvers on 5 synthetic binary task families, 50 trials each, 4x6 grids (24 bits).")
    lines.append("")
    lines.append("Solvers:")
    lines.append("  oracle         -- rule by name (upper bound)")
    lines.append("  raw_xor        -- y_q := x_q XOR (x_1 XOR y_1)  [displacement baseline]")
    lines.append("  golay_coset    -- work in F_2^24/G_24, transfer the syndrome of the displacement,")
    lines.append("                    decode via the canonical coset leader")
    lines.append("  random_linear  -- same as golay_coset but with a random 12x24 parity matrix")
    lines.append("                    (isolates whether Golay's structure adds anything beyond F_2)")
    lines.append("")
    lines.append("Hypothesis (Note 5):")
    lines.append("  * 'toggle' has invariant displacement, so raw_xor, golay_coset, and random_linear")
    lines.append("    should ALL succeed on toggle.")
    lines.append("  * The other four tasks have non-invariant displacements, so raw_xor should fail.")
    lines.append("  * If golay_coset == raw_xor on the non-toggle tasks, the Leech/Golay binary quotient")
    lines.append("    adds no transfer power. If golay_coset > raw_xor, that is a real finding.")
    lines.append("  * random_linear tests whether any benefit comes from the Golay code specifically")
    lines.append("    vs. an arbitrary F_2 linear projection. If golay_coset == random_linear, the")
    lines.append("    Golay code's Steiner structure provides no extra benefit here.")
    lines.append("")
    lines.append("-" * 96)
    head = f"{'Task':<14}{'transfers?':<12}{'oracle EM':<12}{'raw_xor EM':<14}{'golay EM':<14}{'random EM':<14}"
    lines.append(head)
    sub  = f"{'':14}{'':12}{'oracle CMR':<12}{'raw_xor CMR':<14}{'golay CMR':<14}{'random CMR':<14}"
    lines.append(sub)
    lines.append("-" * 96)
    for t, b in agg.items():
        lines.append(f"{t:<14}{'yes' if b['transfer_safe'] else 'no':<12}"
                     f"{b['em']['oracle']:<12.3f}{b['em']['raw_xor']:<14.3f}"
                     f"{b['em']['golay_coset']:<14.3f}{b['em']['random_linear']:<14.3f}")
        lines.append(f"{'':14}{'':12}"
                     f"{b['cmr']['oracle']:<12.3f}{b['cmr']['raw_xor']:<14.3f}"
                     f"{b['cmr']['golay_coset']:<14.3f}{b['cmr']['random_linear']:<14.3f}")
    lines.append("-" * 96)
    lines.append("")
    # Verdict
    lines.append("Verdict:")
    n_total = len(results)
    same_raw_golay = sum(1 for r in results
                         if r["exact_match"]["raw_xor"] == r["exact_match"]["golay_coset"])
    same_golay_rand = sum(1 for r in results
                         if r["exact_match"]["golay_coset"] == r["exact_match"]["random_linear"])
    lines.append(f"  trials where raw_xor EM == golay_coset EM   : {same_raw_golay}/{n_total}")
    lines.append(f"  trials where golay_coset EM == random EM   : {same_golay_rand}/{n_total}")
    return "\n".join(lines)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Precomputing Golay coset table + random-linear leader table...")
    _ = coset_table()
    _ = golay_leader_table()
    _ = random_parity_matrix()
    _ = random_leader_table()
    print("Running 50 trials per task family on 4x6 grids...")
    results = run_all(n_trials=50, H=4, W=6)
    agg = aggregate(results)
    txt = render(results, agg)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    with open(OUT_JSON, "w") as f:
        json.dump({"results": results, "aggregate": agg}, f, indent=2, default=str)
    print(txt)
    print(f"\nWrote: {OUT_JSON}")
    print(f"Wrote: {OUT_TXT}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Experiment B (Notes 1-2) -- Trace supervision vs. final-answer-only.

A cleaner, smaller, faster-to-converge design than the first attempt:
  - 2-step recurrent update (T=2), not 4
  - Linear recurrence with sigmoid readout only (much easier to train)
  - State dim = 32
  - Straight-through estimator on inference, soft sigmoid in training
  - XOR task encoding (constant for toggle, varies for others)

Two regimes:
  FINAL_ONLY : minimize BCE(R(b_T), y) only.
  TRACE      : minimize Σ_t BCE(R(b_t), u_t)  -- supervised at every step.

The two regimes use the SAME architecture, the SAME data, the SAME optimizer;
the only difference is the loss. So any difference in final accuracy is
attributable to the trace-supervision signal, not capacity.

If TRACE > FINAL_ONLY on multi-step tasks (translate, bfs_shortest), the
hypothesis of Note 2 is supported.
If TRACE == FINAL_ONLY, trace supervision provides no benefit at this scale.
"""

from __future__ import annotations
import sys, os, json, math
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

GLM_REPO = "/home/z/my-project/glm_repo"
sys.path.insert(0, GLM_REPO)
sys.path.insert(0, "/home/z/my-project/scripts")

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from bin_tasks import TASKS, sample_task

OUT_JSON = "/home/z/my-project/data/exp_B_results.json"
OUT_TXT  = "/home/z/my-project/data/exp_B_results.txt"


# ============================================================================
# 1.  TINY BINARY RECURRENT GLM  (T=2, linear recurrence, sigmoid readout)
# ============================================================================

def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))

def tanh(x):
    return np.tanh(np.clip(x, -30, 30))

def tanh_prime_from_value(t):
    """Derivative of tanh given t = tanh(x)."""
    return 1 - t * t


class TinyBinaryGLM:
    """T=2 binary recurrent GLM with tanh recurrence + sigmoid readout.

    b_0 = E(x_q)            -- encoder (first 24 cells = x_q)
    b_1 = tanh(W_1 b_0 + U_1 z + c_1)
    b_2 = tanh(W_2 b_1 + U_2 z + c_2)
    r_t = sigmoid(R b_{t+1} + d)  for t in [0, 1, ..., T-1]

    tanh bounds the state to [-1, 1] so it cannot blow up.
    Inference: r_t_hard = (r_t > 0.5).
    """

    def __init__(self, state_dim: int = 32, n_steps: int = 2, seed: int = 0):
        self.N = state_dim
        self.T = n_steps
        rng = np.random.default_rng(seed)
        sd = 1.0 / math.sqrt(max(state_dim, 24))
        # Per-step update params
        self.W = [rng.normal(0, sd, size=(state_dim, state_dim)).astype(np.float32)
                  for _ in range(n_steps)]
        self.U = [rng.normal(0, sd, size=(state_dim, 24)).astype(np.float32)
                  for _ in range(n_steps)]
        self.c = [np.zeros(state_dim, dtype=np.float32) for _ in range(n_steps)]
        # Readout (shared across steps to allow trace supervision)
        self.R = rng.normal(0, sd, size=(24, state_dim)).astype(np.float32)
        self.d = np.zeros(24, dtype=np.float32)
        self.seed = seed

    def forward(self, x_q_flat: np.ndarray, z: np.ndarray):
        """Returns (bs, rs) where bs = [b_0, b_1, ..., b_T] (states, T+1 of them)
        and rs = [r_0, r_1, ..., r_{T-1}] (readouts at each step after applying update).
        Convention: r_t is the readout computed FROM b_{t+1} (the post-update state at step t).
        So r_0 = R(b_1) + d, r_1 = R(b_2) + d, ..., r_{T-1} = R(b_T) + d.
        The trace targets u_0, u_1, ..., u_{T-1} align with these readouts.
        """
        b = np.zeros(self.N, dtype=np.float32)
        b[:24] = x_q_flat
        bs = [b.copy()]
        rs = []
        for t in range(self.T):
            a_b = self.W[t] @ b + self.U[t] @ z + self.c[t]
            b_new = tanh(a_b)
            r = sigmoid(self.R @ b_new + self.d)
            bs.append(b_new.copy())
            rs.append(r)
            b = b_new
        return bs, rs

    def predict(self, x_q_flat: np.ndarray, z: np.ndarray, hard: bool = True):
        _, rs = self.forward(x_q_flat, z)
        if hard:
            return [(r > 0.5).astype(np.float32) for r in rs]
        return rs


# ============================================================================
# 2.  TRAINING LOOP (manual backprop, simple because the recurrence is linear)
# ============================================================================

def bce(p, t, eps=1e-7):
    p = np.clip(p, eps, 1 - eps)
    return float(-np.mean(t * np.log(p) + (1 - t) * np.log1p(-p)))


def bce_grad_from_logits(a_r, t):
    """dL/da_r where r = sigmoid(a_r), L = mean BCE. Form: (r - t) / N."""
    r = sigmoid(a_r)
    return (r - t) / r.size


def train(model: TinyBinaryGLM, train_data: List[Dict], val_data: List[Dict],
          epochs: int = 200, lr: float = 0.5, trace: bool = False,
          lambda_trace: float = 1.0, verbose: bool = False) -> Dict[str, Any]:
    T = model.T
    history = {"train_loss": [], "val_em": [], "val_imr": []}
    for epoch in range(epochs):
        rng = np.random.default_rng(epoch + 17 * model.seed)
        order = rng.permutation(len(train_data))
        total_loss = 0.0
        for idx in order:
            ex = train_data[idx]
            x_q = ex["x_q_flat"]; z = ex["z"]; y = ex["y_flat"]
            bs, rs = model.forward(x_q, z)
            # Pre-sigmoid readout activations at each step
            # (recompute to keep grad chain clean; cheap because T is small)
            a_rs = [model.R @ bs[t+1] + model.d for t in range(T)]

            # --- Build gradients ---
            # Always supervise the final step r_{T-1} against y
            g_a_r_final = bce_grad_from_logits(a_rs[T-1], y)
            # Readout grads (shared R, d)
            g_R = np.outer(g_a_r_final, bs[T]).copy()
            g_d = g_a_r_final.copy()
            # Trace supervision: at each step k, supervise r_k against u_k
            if trace:
                for k in range(T):
                    if k == T - 1:
                        continue  # already done above
                    if k >= len(ex.get("trace_flats", [])):
                        continue
                    u_k = ex["trace_flats"][k]
                    if u_k is None:
                        continue
                    g_a_r_k = bce_grad_from_logits(a_rs[k], u_k) * lambda_trace
                    g_R += np.outer(g_a_r_k, bs[k+1])
                    g_d += g_a_r_k
            # Backprop g_a_r_final to b_T (which is bs[T])
            # Note: readout r = sigmoid(R b + d), so dL/db_T = R^T @ g_a_r_final
            g_b_T = model.R.T @ g_a_r_final
            # The recurrence uses tanh: b_{t+1} = tanh(W_t b_t + U_t z + c_t)
            # d b_{t+1} / d (pre-activation) = tanh_prime(b_{t+1}) = 1 - b_{t+1}^2
            g_W = [np.zeros_like(W) for W in model.W]
            g_U = [np.zeros_like(U) for U in model.U]
            g_c = [np.zeros_like(c) for c in model.c]
            g_b = g_b_T  # gradient w.r.t. bs[T]
            for t in range(T - 1, -1, -1):
                # bs[t+1] = tanh(W[t] bs[t] + U[t] z + c[t])
                g_a_b = g_b * tanh_prime_from_value(bs[t+1])
                g_W[t] += np.outer(g_a_b, bs[t])
                g_U[t] += np.outer(g_a_b, z)
                g_c[t] += g_a_b
                # If trace supervised at step t, also add the trace grad to b_{t+1}
                if trace and t < len(ex.get("trace_flats", [])) and ex["trace_flats"][t] is not None and t != T-1:
                    g_b_trace = model.R.T @ bce_grad_from_logits(a_rs[t], ex["trace_flats"][t]) * lambda_trace
                    g_a_b_trace = g_b_trace * tanh_prime_from_value(bs[t+1])
                    g_W[t] += np.outer(g_a_b_trace, bs[t])
                    g_U[t] += np.outer(g_a_b_trace, z)
                    g_c[t] += g_a_b_trace
                    g_b = model.W[t].T @ (g_a_b + g_a_b_trace)
                else:
                    g_b = model.W[t].T @ g_a_b
            # Apply SGD update
            model.R -= lr * g_R
            model.d -= lr * g_d
            for t in range(T):
                model.W[t] -= lr * g_W[t]
                model.U[t] -= lr * g_U[t]
                model.c[t] -= lr * g_c[t]
            total_loss += bce(rs[T-1], y)
        history["train_loss"].append(total_loss / len(train_data))
        em, imr = evaluate(model, val_data)
        history["val_em"].append(em)
        history["val_imr"].append(imr)
        if verbose and (epoch % 20 == 0 or epoch == epochs - 1):
            print(f"  epoch {epoch:3d}  loss={history['train_loss'][-1]:.4f}  "
                  f"val_em={em:.3f}  val_imr={imr:.3f}")
    return history


def evaluate(model: TinyBinaryGLM, val: List[Dict]) -> Tuple[float, float]:
    em = 0; imr_sum = 0; imr_n = 0
    for ex in val:
        reads = model.predict(ex["x_q_flat"], ex["z"], hard=True)
        pred = reads[-1].reshape(ex["y_shape"])
        if np.array_equal(pred, ex["y"]):
            em += 1
        if "trace_grids" in ex and ex["trace_grids"]:
            for k, t_grid in enumerate(ex["trace_grids"]):
                if k >= len(reads): break
                p_grid = reads[k].reshape(ex["y_shape"])
                imr_sum += float((p_grid == t_grid).mean())
                imr_n += 1
    return em / max(1, len(val)), imr_sum / max(1, imr_n)


# ============================================================================
# 3.  DATA
# ============================================================================

def make_dataset(task_name: str, n_train: int, n_val: int, H: int = 4, W: int = 6,
                 seed_offset: int = 0, **kw):
    fam = TASKS[task_name]
    dx = kw.get("dx", 1); dy = kw.get("dy", 1)
    out = []
    for i in range(n_train + n_val):
        seed = seed_offset + i
        x1, y1, _ = fam.generate(seed=seed, H=H, W=W, dx=dx, dy=dy)
        x2, y2, trace2 = fam.generate(seed=seed + 10000, H=H, W=W, dx=dx, dy=dy)
        z = (y1 ^ x1).astype(np.float32).flatten()  # XOR displacement
        out.append({
            "x_q_flat": x2.flatten().astype(np.float32),
            "y_flat":   y2.flatten().astype(np.float32),
            "y_shape":  (H, W),
            "y":        y2.astype(np.uint8),
            "z":        z.astype(np.float32),
            "trace_flats": [t.flatten().astype(np.float32)
                             for (_, t) in trace2],
            "trace_grids": [t for (_, t) in trace2],
        })
    return out[:n_train], out[n_train:]


def run_one_setting(task_name: str, trace: bool, seed: int,
                    n_train: int = 500, n_val: int = 100,
                    epochs: int = 60, lr: float = 0.5, **kw):
    train_data, val_data = make_dataset(task_name, n_train, n_val,
                                         seed_offset=seed*1000, **kw)
    model = TinyBinaryGLM(state_dim=32, n_steps=2, seed=seed)
    history = train(model, train_data, val_data, epochs=epochs, lr=lr,
                    trace=trace, lambda_trace=1.0, verbose=False)
    return {
        "task": task_name, "trace": trace, "seed": seed,
        "final_val_em": history["val_em"][-1],
        "best_val_em": max(history["val_em"]),
        "epoch_at_best": int(np.argmax(history["val_em"])),
        "final_val_imr": history["val_imr"][-1],
        "best_val_imr": max(history["val_imr"]),
        "train_loss_curve": history["train_loss"],
        "val_em_curve": history["val_em"],
    }


def run_all(n_seeds: int = 3, epochs: int = 60, n_train: int = 500,
            n_val: int = 100):
    out = {"results": []}
    tasks = ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]
    for task_name in tasks:
        for trace in [False, True]:
            for seed in range(n_seeds):
                print(f"  {task_name:14s} trace={trace} seed={seed} ...", end=" ", flush=True)
                r = run_one_setting(task_name, trace=trace, seed=seed,
                                    n_train=n_train, n_val=n_val, epochs=epochs,
                                    dx=1, dy=1, lr=0.5)
                print(f"final_em={r['final_val_em']:.3f} best_em={r['best_val_em']:.3f}")
                out["results"].append(r)
    return out


def aggregate(results: List[Dict]) -> Dict[str, Any]:
    by = {}
    for r in results:
        key = (r["task"], r["trace"])
        if key not in by:
            by[key] = {"final_em": [], "best_em": [], "final_imr": [], "best_imr": [],
                        "epoch_at_best": []}
        b = by[key]
        b["final_em"].append(r["final_val_em"])
        b["best_em"].append(r["best_val_em"])
        b["final_imr"].append(r["final_val_imr"])
        b["best_imr"].append(r["best_val_imr"])
        b["epoch_at_best"].append(r["epoch_at_best"])
    return {f"{k[0]}|trace={k[1]}": {
        "final_em_mean": float(np.mean(v["final_em"])),
        "final_em_std":  float(np.std(v["final_em"])),
        "best_em_mean":  float(np.mean(v["best_em"])),
        "best_em_std":   float(np.std(v["best_em"])),
        "final_imr_mean": float(np.mean(v["final_imr"])),
        "best_imr_mean":  float(np.mean(v["best_imr"])),
        "epoch_at_best_mean": float(np.mean(v["epoch_at_best"])),
        "n_seeds": len(v["final_em"]),
    } for k, v in by.items()}


def render(results: Dict, agg: Dict) -> str:
    lines = []
    lines.append("=" * 96)
    lines.append("EXPERIMENT B (Notes 1-2) -- Trace supervision vs. final-answer-only")
    lines.append("=" * 96)
    lines.append("")
    lines.append("Tiny binary recurrent GLM (T=2, linear recurrence, sigmoid readout):")
    lines.append("  z_D = A(D)       -- task encoder = y1 XOR x1 (the F_2 displacement)")
    lines.append("  b_0 = E(x_q)    -- binary encoder (query flattened into first 24 of 32 cells)")
    lines.append("  b_t+1 = F_θ(b_t, z_D) = W_t b_t + U_t z + c_t  (linear, per-step)")
    lines.append("  r_t = sigmoid(R b_t + d)  (shared readout)")
    lines.append("")
    lines.append("Training:")
    lines.append("  FINAL_ONLY : minimize BCE(r_{T-1}, y) only.")
    lines.append("  TRACE      : minimize Σ_t BCE(r_t, u_t) at every step (λ_trace = 1.0).")
    lines.append("  Same architecture, same data, same optimizer; only the loss differs.")
    lines.append("")
    lines.append(f"3 seeds, 500 train / 100 val per seed, 60 epochs, 4x6 grids, lr=0.5.")
    lines.append("")
    lines.append("-" * 96)
    lines.append(f"{'Task':<14}{'Regime':<14}{'best EM (mean ± std)':<26}{'final EM':<14}{'best IMR':<14}{'epoch@best':<12}")
    lines.append("-" * 96)
    for task_name in ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]:
        for trace in [False, True]:
            k = f"{task_name}|trace={trace}"
            if k not in agg: continue
            b = agg[k]
            regime = "TRACE" if trace else "FINAL_ONLY"
            lines.append(f"{task_name:<14}{regime:<14}"
                         f"{b['best_em_mean']:.3f} ± {b['best_em_std']:.3f}        "
                         f"{b['final_em_mean']:<14.3f}{b['best_imr_mean']:<14.3f}"
                         f"{b['epoch_at_best_mean']:<12.1f}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("Verdict (TRACE best EM - FINAL_ONLY best EM, per task):")
    for task_name in ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]:
        k_no = f"{task_name}|trace=False"
        k_yes = f"{task_name}|trace=True"
        if k_no in agg and k_yes in agg:
            d = agg[k_yes]["best_em_mean"] - agg[k_no]["best_em_mean"]
            sign = "+" if d >= 0 else ""
            lines.append(f"  {task_name:14s}: {sign}{d:.3f} EM (mean of {agg[k_no]['n_seeds']} seeds)")
    return "\n".join(lines)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Running Experiment B: trace vs. final-only, 5 tasks x 2 regimes x 3 seeds ...")
    results = run_all(n_seeds=3, epochs=60, n_train=500, n_val=100)
    agg = aggregate(results["results"])
    txt = render(results, agg)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    with open(OUT_JSON, "w") as f:
        json.dump({"results": results, "aggregate": agg}, f, indent=2, default=str)
    print()
    print(txt)
    print(f"\nWrote: {OUT_JSON}")
    print(f"Wrote: {OUT_TXT}")


if __name__ == "__main__":
    main()

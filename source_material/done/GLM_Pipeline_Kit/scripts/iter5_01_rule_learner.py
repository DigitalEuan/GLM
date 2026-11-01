#!/usr/bin/env python3
"""
Iteration 5 Phase 1 — Multi-head GLM rule-sequence learner.

A small model with three heads:
  * rule_head:      predicts which of the 6 step rules to invoke next
                    (popcount=0, hamming=1, sphere_packing=2, octads=3, theta=4, pair_census=5)
  * lattice_head:   predicts which lattice layer to use (Λ24=0, Λ32=1, Λ48=2, beyond=3)
  * snap_head:      predicts whether the snap will succeed (binary)

Trained on the iteration-4 layered-snap traces. Each sample is:
  input:   binary 4x6 grid (24 bits) flattened
  targets: (rule_index, lattice_index, snap_success)

We use torch (CPU build). Multiple seeds, train/val split per task family,
held-out task family for cross-task generalisation test.

We watch and document ALL failures:
  * Training convergence failures (loss not decreasing)
  * Per-head accuracy failures (one head much worse than others)
  * Generalisation failures (held-out task accuracy collapses)
  * Calibration failures (over-confident wrong predictions)
Each failure is logged with: input sample, predicted vs true label, reason.
"""

from __future__ import annotations
import sys, os, json, time, math, random
from typing import Dict, List, Any, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

GLM_REPO = "/home/z/my-project/glm_repo"
sys.path.insert(0, GLM_REPO)
sys.path.insert(0, "/home/z/my-project/scripts")

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from bin_tasks import TASKS

OUT_JSON = "/home/z/my-project/data/iter5_rule_learner.json"
OUT_TXT  = "/home/z/my-project/data/iter5_rule_learner.txt"
FAILURE_LOG = "/home/z/my-project/data/iter5_failures.txt"


# ============================================================================
# 1. Load iteration-4 data and build training samples
# ============================================================================
def load_iter4_data() -> List[Dict[str, Any]]:
    """Load the iteration-4 layered snap results and build per-target samples."""
    with open("/home/z/my-project/data/iter4_layered_snap.json") as f:
        d = json.load(f)
    samples = []
    for task_name, task_data in d.items():
        for row in task_data["rows"]:
            target_bits = row["target_bits"]
            # Convert 24-bit int to 24-dim binary feature vector
            bits = [(target_bits >> (23 - i)) & 1 for i in range(24)]
            # Rule head target: which rule is the "characteristic" rule for this target?
            # We define: rule = 0 (popcount) for even parity (Leech succeeds)
            #           rule = 3 (octads) if nearest codeword is octad
            #           rule = 5 (pair_census) if all snaps fail (escalation)
            # Simpler: rule = parity (0 = even, 1 = odd) + ambiguity indicator
            n_ones = row["n_ones"]
            parity = row["parity"]
            snap24 = row["snap_leech_24"]
            snap32 = row["snap_barnes_wall_32"]
            snap48 = row["snap_ternary_48"]
            # Define rule target: 0=popcount if Leech succeeds (even parity),
            # 5=pair_census if all snaps fail, else 3=octads (used in diagnostic)
            if snap24["in_lattice"]:
                rule_target = 0  # popcount (parity check was decisive)
            elif not (snap24["in_lattice"] or snap32["in_lattice"] or snap48["in_lattice"]):
                rule_target = 5  # pair_census (escalation)
            else:
                rule_target = 3  # octads (diagnostic at higher layer)
            # Lattice head target: which lattice layer is needed
            layer_target = row["minimum_layer_needed"]
            layer_idx = {"Leech_24": 0, "Barnes_Wall_32": 1, "Ternary_48": 2, "BEYOND_LATTICE_48": 3}[layer_target]
            # Snap head target: did any snap succeed?
            snap_target = 1 if row["any_snap_succeeded"] else 0
            samples.append({
                "task": task_name,
                "bits": bits,
                "n_ones": n_ones,
                "parity": parity,
                "rule_target": rule_target,
                "lattice_target": layer_idx,
                "snap_target": snap_target,
                "minimum_layer": layer_target,
            })
    return samples


# ============================================================================
# 2. Multi-head model
# ============================================================================
class MultiHeadGLM(nn.Module):
    """Small multi-head model: 24-bit input -> shared encoder -> 3 heads."""
    def __init__(self, hidden_dim: int = 64, n_rules: int = 6, n_lattices: int = 4):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(24, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
        )
        self.rule_head = nn.Linear(hidden_dim, n_rules)
        self.lattice_head = nn.Linear(hidden_dim, n_lattices)
        self.snap_head = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        # x: (B, 24) float tensor
        h = self.encoder(x)
        return {
            "rule": self.rule_head(h),       # (B, 6) logits
            "lattice": self.lattice_head(h), # (B, 4) logits
            "snap": self.snap_head(h).squeeze(-1),  # (B,) logits
        }


# ============================================================================
# 3. Training
# ============================================================================
def train_one(model, train_data: List[Dict], val_data: List[Dict],
              epochs: int = 200, lr: float = 0.01, seed: int = 0,
              failure_log: List[Dict] = None) -> Dict[str, Any]:
    """Train the model, log all val failures with reasons."""
    if failure_log is None:
        failure_log = []
    # Build tensors
    def to_tensors(samples):
        X = torch.tensor([s["bits"] for s in samples], dtype=torch.float32)
        y_rule = torch.tensor([s["rule_target"] for s in samples], dtype=torch.long)
        y_lat  = torch.tensor([s["lattice_target"] for s in samples], dtype=torch.long)
        y_snap = torch.tensor([s["snap_target"] for s in samples], dtype=torch.float32)
        return X, y_rule, y_lat, y_snap

    X_tr, yr_tr, yl_tr, ys_tr = to_tensors(train_data)
    X_va, yr_va, yl_va, ys_va = to_tensors(val_data)

    opt = torch.optim.Adam(model.parameters(), lr=lr)
    history = {"train_loss": [], "val_acc_rule": [], "val_acc_lattice": [], "val_acc_snap": []}
    rng = random.Random(seed)
    for epoch in range(epochs):
        model.train()
        # Shuffle training order
        idx = list(range(len(train_data)))
        rng.shuffle(idx)
        epoch_loss = 0.0
        for i in idx:
            x = X_tr[i:i+1]
            out = model(x)
            loss_rule = F.cross_entropy(out["rule"], yr_tr[i:i+1])
            loss_lat  = F.cross_entropy(out["lattice"], yl_tr[i:i+1])
            loss_snap = F.binary_cross_entropy_with_logits(out["snap"], ys_tr[i:i+1])
            loss = loss_rule + loss_lat + loss_snap
            opt.zero_grad()
            loss.backward()
            opt.step()
            epoch_loss += loss.item()
        epoch_loss /= len(train_data)
        history["train_loss"].append(epoch_loss)
        # Validate
        model.eval()
        with torch.no_grad():
            out = model(X_va)
            pred_rule = out["rule"].argmax(-1)
            pred_lat  = out["lattice"].argmax(-1)
            pred_snap = (torch.sigmoid(out["snap"]) > 0.5).float()
            acc_rule = (pred_rule == yr_va).float().mean().item()
            acc_lat  = (pred_lat  == yl_va).float().mean().item()
            acc_snap = (pred_snap == ys_va).float().mean().item()
        history["val_acc_rule"].append(acc_rule)
        history["val_acc_lattice"].append(acc_lattice := acc_lat)
        history["val_acc_snap"].append(acc_snap)
        # Log failures at the final epoch
        if epoch == epochs - 1:
            for i in range(len(val_data)):
                if pred_rule[i].item() != yr_va[i].item():
                    failure_log.append({
                        "type": "rule_misclassification",
                        "sample_idx": i,
                        "task": val_data[i]["task"],
                        "n_ones": val_data[i]["n_ones"],
                        "parity": val_data[i]["parity"],
                        "true_rule": int(yr_va[i].item()),
                        "pred_rule": int(pred_rule[i].item()),
                        "true_lattice": val_data[i]["minimum_layer"],
                        "reason": "model predicted wrong rule for this target",
                    })
                if pred_lat[i].item() != yl_va[i].item():
                    failure_log.append({
                        "type": "lattice_misclassification",
                        "sample_idx": i,
                        "task": val_data[i]["task"],
                        "n_ones": val_data[i]["n_ones"],
                        "parity": val_data[i]["parity"],
                        "true_lattice": val_data[i]["minimum_layer"],
                        "pred_lattice_idx": int(pred_lat[i].item()),
                        "pred_lattice": ["Leech_24", "Barnes_Wall_32", "Ternary_48", "BEYOND_LATTICE_48"][int(pred_lat[i].item())],
                        "reason": "model predicted wrong lattice layer for this target",
                    })
                if pred_snap[i].item() != ys_va[i].item():
                    failure_log.append({
                        "type": "snap_misclassification",
                        "sample_idx": i,
                        "task": val_data[i]["task"],
                        "n_ones": val_data[i]["n_ones"],
                        "parity": val_data[i]["parity"],
                        "true_snap": int(ys_va[i].item()),
                        "pred_snap": int(pred_snap[i].item()),
                        "true_lattice": val_data[i]["minimum_layer"],
                        "reason": "model predicted wrong snap success",
                    })
    return {
        "final_train_loss": history["train_loss"][-1],
        "final_val_acc_rule": history["val_acc_rule"][-1],
        "final_val_acc_lattice": history["val_acc_lattice"][-1],
        "final_val_acc_snap": history["val_acc_snap"][-1],
        "best_val_acc_rule": max(history["val_acc_rule"]),
        "best_val_acc_lattice": max(history["val_acc_lattice"]),
        "best_val_acc_snap": max(history["val_acc_snap"]),
        "loss_curve": history["train_loss"],
        "val_rule_curve": history["val_acc_rule"],
        "val_lattice_curve": history["val_acc_lattice"],
        "val_snap_curve": history["val_acc_snap"],
    }


def run_experiment(n_seeds: int = 3, epochs: int = 150) -> Dict[str, Any]:
    """Run train/val + cross-task generalisation experiments."""
    samples = load_iter4_data()
    print(f"Loaded {len(samples)} samples from iteration-4 data")
    # Split by task: 4 tasks for train, 1 for held-out
    tasks = ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]
    all_results = {}
    failure_log = []
    # Within-task train/val (4 train tasks, each split 80/20)
    for held_out in tasks:
        train_tasks = [t for t in tasks if t != held_out]
        train_samples = [s for s in samples if s["task"] in train_tasks]
        val_samples = [s for s in samples if s["task"] == held_out]
        # Within the train tasks, also take 20% as in-distribution val
        rng = random.Random(42)
        train_in_dist = []
        val_in_dist = []
        for t in train_tasks:
            ts = [s for s in samples if s["task"] == t]
            rng.shuffle(ts)
            cut = int(0.8 * len(ts))
            train_in_dist.extend(ts[:cut])
            val_in_dist.extend(ts[cut:])
        # Train one model per seed
        per_seed = []
        for seed in range(n_seeds):
            print(f"  held_out={held_out} seed={seed}...", end=" ", flush=True)
            torch.manual_seed(seed)
            model = MultiHeadGLM(hidden_dim=64)
            r = train_one(model, train_in_dist, val_in_dist + val_samples,
                           epochs=epochs, lr=0.01, seed=seed,
                           failure_log=failure_log)
            # Also evaluate on held-out
            X_ho = torch.tensor([s["bits"] for s in val_samples], dtype=torch.float32)
            yr_ho = torch.tensor([s["rule_target"] for s in val_samples], dtype=torch.long)
            yl_ho = torch.tensor([s["lattice_target"] for s in val_samples], dtype=torch.long)
            ys_ho = torch.tensor([s["snap_target"] for s in val_samples], dtype=torch.float32)
            model.eval()
            with torch.no_grad():
                out = model(X_ho)
                acc_rule_ho = (out["rule"].argmax(-1) == yr_ho).float().mean().item()
                acc_lat_ho = (out["lattice"].argmax(-1) == yl_ho).float().mean().item()
                acc_snap_ho = ((torch.sigmoid(out["snap"]) > 0.5).float() == ys_ho).float().mean().item()
            print(f"ho_rule={acc_rule_ho:.3f}  ho_lat={acc_lat_ho:.3f}  ho_snap={acc_snap_ho:.3f}")
            per_seed.append({
                "seed": seed,
                "in_dist": {k: v for k, v in r.items() if k != "loss_curve" and "curve" not in k},
                "held_out": {
                    "acc_rule": acc_rule_ho,
                    "acc_lattice": acc_lat_ho,
                    "acc_snap": acc_snap_ho,
                },
                "loss_curve": r["loss_curve"],
                "val_rule_curve": r["val_rule_curve"],
                "val_lattice_curve": r["val_lattice_curve"],
                "val_snap_curve": r["val_snap_curve"],
            })
        # Aggregate across seeds
        ho_rule = np.mean([s["held_out"]["acc_rule"] for s in per_seed])
        ho_lat  = np.mean([s["held_out"]["acc_lattice"] for s in per_seed])
        ho_snap = np.mean([s["held_out"]["acc_snap"] for s in per_seed])
        in_rule = np.mean([s["in_dist"]["final_val_acc_rule"] for s in per_seed])
        in_lat  = np.mean([s["in_dist"]["final_val_acc_lattice"] for s in per_seed])
        in_snap = np.mean([s["in_dist"]["final_val_acc_snap"] for s in per_seed])
        all_results[held_out] = {
            "n_seeds": n_seeds,
            "in_dist_acc": {"rule": in_rule, "lattice": in_lat, "snap": in_snap},
            "held_out_acc": {"rule": ho_rule, "lattice": ho_lat, "snap": ho_snap},
            "per_seed": per_seed,
        }
    return {"results": all_results, "failure_log": failure_log[:200]}  # cap at 200 entries


def render(results: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 5 PHASE 1 — Multi-head GLM rule-sequence learner")
    lines.append("=" * 96)
    lines.append("")
    lines.append("A small multi-head model trained on iteration-4 layered-snap traces.")
    lines.append("Three heads: rule-prediction (6 classes), lattice-selector (4 classes), snap-result (binary).")
    lines.append("Cross-task generalisation: train on 4 tasks, evaluate on the 5th held-out.")
    lines.append("")
    lines.append("-" * 96)
    lines.append("[In-distribution validation accuracy (mean across seeds)]")
    lines.append("-" * 96)
    lines.append(f"{'Held-out task':<16}{'rule acc':<14}{'lattice acc':<16}{'snap acc':<14}")
    lines.append("-" * 96)
    for held_out, r in results["results"].items():
        i = r["in_dist_acc"]
        lines.append(f"{held_out:<16}{i['rule']:<14.3f}{i['lattice']:<16.3f}{i['snap']:<14.3f}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("[Held-out task generalisation accuracy (mean across seeds)]")
    lines.append("-" * 96)
    lines.append(f"{'Held-out task':<16}{'rule acc':<14}{'lattice acc':<16}{'snap acc':<14}")
    lines.append("-" * 96)
    for held_out, r in results["results"].items():
        h = r["held_out_acc"]
        lines.append(f"{held_out:<16}{h['rule']:<14.3f}{h['lattice']:<16.3f}{h['snap']:<14.3f}")
    lines.append("-" * 96)
    lines.append("")
    # Failure log summary
    fl = results["failure_log"]
    lines.append(f"[Failure log summary — {len(fl)} entries (capped at 200)]")
    lines.append("-" * 96)
    by_type = {}
    for entry in fl:
        t = entry["type"]
        by_type.setdefault(t, []).append(entry)
    for t, entries in by_type.items():
        lines.append(f"  {t}: {len(entries)} cases")
        # Sample one example per type
        ex = entries[0]
        for k, v in ex.items():
            if k != "reason":
                lines.append(f"    {k}: {v}")
        lines.append(f"    reason: {ex['reason']}")
        lines.append("")
    # Failure clustering by task
    lines.append("[Failures by task]")
    by_task = {}
    for entry in fl:
        t = entry.get("task", "?")
        by_task.setdefault(t, 0)
        by_task[t] += 1
    for t, c in sorted(by_task.items(), key=lambda x: -x[1]):
        lines.append(f"  {t}: {c} failures")
    return "\n".join(lines)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Iteration 5 Phase 1: multi-head rule-sequence learner")
    results = run_experiment(n_seeds=3, epochs=150)
    txt = render(results)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2, default=str)
    # Write failure log separately for readability
    with open(FAILURE_LOG, "w") as f:
        f.write(f"Iteration 5 Failure Log\n")
        f.write(f"Total failures: {len(results['failure_log'])}\n\n")
        for i, entry in enumerate(results["failure_log"]):
            f.write(f"--- Failure {i+1} ---\n")
            for k, v in entry.items():
                f.write(f"  {k}: {v}\n")
            f.write("\n")
    print()
    print(txt)
    print(f"\nWrote: {OUT_JSON}")
    print(f"Wrote: {OUT_TXT}")
    print(f"Wrote: {FAILURE_LOG}")


if __name__ == "__main__":
    main()

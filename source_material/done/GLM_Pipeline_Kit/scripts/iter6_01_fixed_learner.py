#!/usr/bin/env python3
"""
Iteration 6 Phase 1 — Apply the 3 development escalation requirements from
iteration 5's failure log:
  (i)   Explicit parity feature (sum of bits mod 2) as 25th input dimension
  (ii)  Class-balanced loss (weight each class by 1/frequency)
  (iii) Richer encoder (4 layers instead of 2)

Plus: track ambiguity/superposition. When the model's top-2 predictions are
within a confidence gap, log it as "superposition held" rather than forcing
a single answer. The GLM holds these until future info clarifies.

Compare to iteration-5 baseline. Target: in-dist accuracy 80% → 95%.
"""

from __future__ import annotations
import sys, os, json, math, random
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

OUT_JSON = "/home/z/my-project/data/iter6_fixed_learner.json"
OUT_TXT  = "/home/z/my-project/data/iter6_fixed_learner.txt"


def load_iter4_data() -> List[Dict[str, Any]]:
    """Load the iteration-4 layered snap results and build per-target samples."""
    with open("/home/z/my-project/data/iter4_layered_snap.json") as f:
        d = json.load(f)
    samples = []
    for task_name, task_data in d.items():
        for row in task_data["rows"]:
            target_bits = row["target_bits"]
            bits = [(target_bits >> (23 - i)) & 1 for i in range(24)]
            n_ones = row["n_ones"]
            parity = row["parity"]
            snap24 = row["snap_leech_24"]
            snap32 = row["snap_barnes_wall_32"]
            snap48 = row["snap_ternary_48"]
            if snap24["in_lattice"]:
                rule_target = 0
            elif not (snap24["in_lattice"] or snap32["in_lattice"] or snap48["in_lattice"]):
                rule_target = 5
            else:
                rule_target = 3
            layer_target = row["minimum_layer_needed"]
            layer_idx = {"Leech_24": 0, "Barnes_Wall_32": 1, "Ternary_48": 2, "BEYOND_LATTICE_48": 3}[layer_target]
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
# 2. Improved multi-head model: 25 inputs (24 bits + 1 parity), 4-layer encoder
# ============================================================================
class ImprovedMultiHeadGLM(nn.Module):
    """Three improvements over iteration 5's model:
    (i)   25 inputs: 24 binary bits + 1 parity feature (sum mod 2)
    (ii)  Richer encoder: 4 layers (was 2), each 64-dim, with tanh
    (iii) Class-balanced loss (applied externally in the training loop)

    Plus: the snap head has an additional "ambiguity" output, predicting
    whether the snap is decisive (single lattice) or ambiguous (multiple
    lattices equally valid). This is the superposition signal.
    """
    def __init__(self, hidden_dim: int = 64, n_rules: int = 6, n_lattices: int = 4):
        super().__init__()
        # Encoder: 25 -> 64 -> 64 -> 64 -> 64 (4 layers, deeper than before)
        self.encoder = nn.Sequential(
            nn.Linear(25, hidden_dim),           # layer 1: 25 -> 64 (with parity feature)
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),   # layer 2
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),   # layer 3
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),   # layer 4
            nn.Tanh(),
        )
        self.rule_head = nn.Linear(hidden_dim, n_rules)
        self.lattice_head = nn.Linear(hidden_dim, n_lattices)
        self.snap_head = nn.Linear(hidden_dim, 1)
        # New: ambiguity head — predicts P(superposition held | input)
        # i.e., P(more than one lattice layer is equally valid)
        self.ambiguity_head = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        # x: (B, 25) — 24 bits + 1 parity bit
        h = self.encoder(x)
        return {
            "rule": self.rule_head(h),
            "lattice": self.lattice_head(h),
            "snap": self.snap_head(h).squeeze(-1),
            "ambiguity": self.ambiguity_head(h).squeeze(-1),
        }


def features_with_parity(samples: List[Dict]) -> torch.Tensor:
    """Build the 25-dim feature vector: 24 bits + 1 parity bit."""
    bits = [s["bits"] for s in samples]
    parity = [[sum(b) % 2] for b in bits]
    X = torch.tensor([b + p for b, p in zip(bits, parity)], dtype=torch.float32)
    return X


def class_balanced_weights(targets: torch.Tensor, n_classes: int) -> torch.Tensor:
    """Compute class-balanced weights: weight_c = N / (n_classes * count_c)."""
    counts = torch.bincount(targets, minlength=n_classes).float()
    counts = torch.clamp(counts, min=1.0)  # avoid division by zero
    weights = len(targets) / (n_classes * counts)
    return weights


def train_one(model, train_data: List[Dict], val_data: List[Dict],
              epochs: int = 200, lr: float = 0.01, seed: int = 0,
              failure_log: List[Dict] = None,
              superposition_log: List[Dict] = None,
              confidence_gap: float = 0.1) -> Dict[str, Any]:
    """Train with class-balanced loss + ambiguity tracking."""
    if failure_log is None: failure_log = []
    if superposition_log is None: superposition_log = []

    X_tr = features_with_parity(train_data)
    yr_tr = torch.tensor([s["rule_target"] for s in train_data], dtype=torch.long)
    yl_tr = torch.tensor([s["lattice_target"] for s in train_data], dtype=torch.long)
    ys_tr = torch.tensor([s["snap_target"] for s in train_data], dtype=torch.float32)
    # Ambiguity target: 1 if the sample hit the parity wall (snap_leech_24 failed
    # but other snaps succeeded). The model should learn to predict this
    # superposition.
    ya_tr = torch.tensor(
        [1.0 if (not s["snap_target"] == 1 and s["lattice_target"] >= 1) else 0.0
         for s in train_data], dtype=torch.float32)
    # Actually: ambiguity = 1 if more than one snap succeeds (true superposition)
    # For our data, ambiguity = 1 if (snap24 failed but snap32 and snap48 both succeed)
    # since both higher layers independently resolve the parity wall
    ya_tr = torch.tensor(
        [1.0 if (s["lattice_target"] >= 1) else 0.0
         for s in train_data], dtype=torch.float32)

    X_va = features_with_parity(val_data)
    yr_va = torch.tensor([s["rule_target"] for s in val_data], dtype=torch.long)
    yl_va = torch.tensor([s["lattice_target"] for s in val_data], dtype=torch.long)
    ys_va = torch.tensor([s["snap_target"] for s in val_data], dtype=torch.float32)
    ya_va = torch.tensor(
        [1.0 if (s["lattice_target"] >= 1) else 0.0
         for s in val_data], dtype=torch.float32)

    # Class-balanced weights for the rule and lattice heads
    rule_w = class_balanced_weights(yr_tr, n_classes=6)
    lat_w  = class_balanced_weights(yl_tr, n_classes=4)

    opt = torch.optim.Adam(model.parameters(), lr=lr)
    history = {"train_loss": [], "val_acc_rule": [], "val_acc_lattice": [],
                "val_acc_snap": [], "val_acc_ambiguity": [], "val_superposition_rate": []}
    rng = random.Random(seed)
    for epoch in range(epochs):
        model.train()
        idx = list(range(len(train_data)))
        rng.shuffle(idx)
        epoch_loss = 0.0
        for i in idx:
            x = X_tr[i:i+1]
            out = model(x)
            # Class-balanced CE for rule and lattice heads
            loss_rule = F.cross_entropy(out["rule"], yr_tr[i:i+1], weight=rule_w)
            loss_lat  = F.cross_entropy(out["lattice"], yl_tr[i:i+1], weight=lat_w)
            loss_snap = F.binary_cross_entropy_with_logits(out["snap"], ys_tr[i:i+1])
            loss_amb  = F.binary_cross_entropy_with_logits(out["ambiguity"], ya_tr[i:i+1])
            loss = loss_rule + loss_lat + loss_snap + 0.5 * loss_amb  # weight ambiguity lower
            opt.zero_grad()
            loss.backward()
            opt.step()
            epoch_loss += loss.item()
        epoch_loss /= len(train_data)
        history["train_loss"].append(epoch_loss)
        model.eval()
        with torch.no_grad():
            out = model(X_va)
            pred_rule = out["rule"].argmax(-1)
            pred_lat  = out["lattice"].argmax(-1)
            pred_snap = (torch.sigmoid(out["snap"]) > 0.5).float()
            pred_amb  = (torch.sigmoid(out["ambiguity"]) > 0.5).float()
            acc_rule = (pred_rule == yr_va).float().mean().item()
            acc_lat  = (pred_lat  == yl_va).float().mean().item()
            acc_snap = (pred_snap == ys_va).float().mean().item()
            acc_amb  = (pred_amb  == ya_va).float().mean().item()
            # Superposition tracking: when the top-2 lattice predictions are
            # within `confidence_gap` in softmax probability, log as superposition.
            lattice_probs = F.softmax(out["lattice"], dim=-1)
            top2 = lattice_probs.topk(2, dim=-1).values
            superposition_mask = (top2[:, 0] - top2[:, 1]) < confidence_gap
            superposition_rate = superposition_mask.float().mean().item()
        history["val_acc_rule"].append(acc_rule)
        history["val_acc_lattice"].append(acc_lat)
        history["val_acc_snap"].append(acc_snap)
        history["val_acc_ambiguity"].append(acc_amb)
        history["val_superposition_rate"].append(superposition_rate)
        # Log failures and superpositions at the final epoch
        if epoch == epochs - 1:
            for i in range(len(val_data)):
                # Superposition: top-2 within gap
                if superposition_mask[i]:
                    top2_idx = lattice_probs[i].topk(2).indices.tolist()
                    superposition_log.append({
                        "type": "lattice_superposition",
                        "sample_idx": i,
                        "task": val_data[i]["task"],
                        "n_ones": val_data[i]["n_ones"],
                        "parity": val_data[i]["parity"],
                        "true_lattice": val_data[i]["minimum_layer"],
                        "top1_lattice": ["Leech_24", "Barnes_Wall_32", "Ternary_48", "BEYOND_LATTICE_48"][top2_idx[0]],
                        "top2_lattice": ["Leech_24", "Barnes_Wall_32", "Ternary_48", "BEYOND_LATTICE_48"][top2_idx[1]],
                        "top1_prob": float(lattice_probs[i][top2_idx[0]].item()),
                        "top2_prob": float(lattice_probs[i][top2_idx[1]].item()),
                        "reason": "model holds multiple lattice predictions as superposition (awaiting clarification)",
                    })
                # Failures (only when no superposition held)
                if not superposition_mask[i]:
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
                            "reason": "model predicted wrong rule (no superposition held)",
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
                            "reason": "model predicted wrong lattice layer (no superposition held)",
                        })
    return {
        "final_train_loss": history["train_loss"][-1],
        "final_val_acc_rule": history["val_acc_rule"][-1],
        "final_val_acc_lattice": history["val_acc_lattice"][-1],
        "final_val_acc_snap": history["val_acc_snap"][-1],
        "final_val_acc_ambiguity": history["val_acc_ambiguity"][-1],
        "final_superposition_rate": history["val_superposition_rate"][-1],
        "best_val_acc_rule": max(history["val_acc_rule"]),
        "best_val_acc_lattice": max(history["val_acc_lattice"]),
        "best_val_acc_snap": max(history["val_acc_snap"]),
        "loss_curve": history["train_loss"],
        "val_rule_curve": history["val_acc_rule"],
        "val_lattice_curve": history["val_acc_lattice"],
        "val_snap_curve": history["val_acc_snap"],
        "val_ambiguity_curve": history["val_acc_ambiguity"],
        "val_superposition_curve": history["val_superposition_rate"],
    }


def run_experiment(n_seeds: int = 3, epochs: int = 200) -> Dict[str, Any]:
    samples = load_iter4_data()
    tasks = ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]
    all_results = {}
    failure_log = []
    superposition_log = []
    for held_out in tasks:
        train_tasks = [t for t in tasks if t != held_out]
        rng = random.Random(42)
        train_in_dist = []
        val_in_dist = []
        for t in train_tasks:
            ts = [s for s in samples if s["task"] == t]
            rng.shuffle(ts)
            cut = int(0.8 * len(ts))
            train_in_dist.extend(ts[:cut])
            val_in_dist.extend(ts[cut:])
        val_samples = [s for s in samples if s["task"] == held_out]
        per_seed = []
        for seed in range(n_seeds):
            print(f"  held_out={held_out} seed={seed}...", end=" ", flush=True)
            torch.manual_seed(seed)
            model = ImprovedMultiHeadGLM(hidden_dim=64)
            r = train_one(model, train_in_dist, val_in_dist + val_samples,
                           epochs=epochs, lr=0.01, seed=seed,
                           failure_log=failure_log,
                           superposition_log=superposition_log,
                           confidence_gap=0.1)
            X_ho = features_with_parity(val_samples)
            yr_ho = torch.tensor([s["rule_target"] for s in val_samples], dtype=torch.long)
            yl_ho = torch.tensor([s["lattice_target"] for s in val_samples], dtype=torch.long)
            ys_ho = torch.tensor([s["snap_target"] for s in val_samples], dtype=torch.float32)
            ya_ho = torch.tensor(
                [1.0 if (s["lattice_target"] >= 1) else 0.0 for s in val_samples],
                dtype=torch.float32)
            model.eval()
            with torch.no_grad():
                out = model(X_ho)
                acc_rule_ho = (out["rule"].argmax(-1) == yr_ho).float().mean().item()
                acc_lat_ho = (out["lattice"].argmax(-1) == yl_ho).float().mean().item()
                acc_snap_ho = ((torch.sigmoid(out["snap"]) > 0.5).float() == ys_ho).float().mean().item()
                acc_amb_ho = ((torch.sigmoid(out["ambiguity"]) > 0.5).float() == ya_ho).float().mean().item()
                # Superposition rate on held-out
                lp = F.softmax(out["lattice"], dim=-1)
                top2 = lp.topk(2, dim=-1).values
                ho_superposition_rate = ((top2[:, 0] - top2[:, 1]) < 0.1).float().mean().item()
            print(f"ho_rule={acc_rule_ho:.3f}  ho_lat={acc_lat_ho:.3f}  "
                  f"ho_snap={acc_snap_ho:.3f}  ho_amb={acc_amb_ho:.3f}  "
                  f"ho_superpos={ho_superposition_rate:.3f}")
            per_seed.append({
                "seed": seed,
                "in_dist": {k: v for k, v in r.items() if k != "loss_curve" and "curve" not in k},
                "held_out": {
                    "acc_rule": acc_rule_ho, "acc_lattice": acc_lat_ho,
                    "acc_snap": acc_snap_ho, "acc_ambiguity": acc_amb_ho,
                    "superposition_rate": ho_superposition_rate,
                },
                "loss_curve": r["loss_curve"],
                "val_rule_curve": r["val_rule_curve"],
                "val_lattice_curve": r["val_lattice_curve"],
                "val_snap_curve": r["val_snap_curve"],
                "val_ambiguity_curve": r["val_ambiguity_curve"],
                "val_superposition_curve": r["val_superposition_curve"],
            })
        in_rule = np.mean([s["in_dist"]["final_val_acc_rule"] for s in per_seed])
        in_lat  = np.mean([s["in_dist"]["final_val_acc_lattice"] for s in per_seed])
        in_snap = np.mean([s["in_dist"]["final_val_acc_snap"] for s in per_seed])
        in_amb  = np.mean([s["in_dist"]["final_val_acc_ambiguity"] for s in per_seed])
        in_super = np.mean([s["in_dist"]["final_superposition_rate"] for s in per_seed])
        ho_rule = np.mean([s["held_out"]["acc_rule"] for s in per_seed])
        ho_lat  = np.mean([s["held_out"]["acc_lattice"] for s in per_seed])
        ho_snap = np.mean([s["held_out"]["acc_snap"] for s in per_seed])
        ho_amb  = np.mean([s["held_out"]["acc_ambiguity"] for s in per_seed])
        ho_super = np.mean([s["held_out"]["superposition_rate"] for s in per_seed])
        all_results[held_out] = {
            "n_seeds": n_seeds,
            "in_dist_acc": {"rule": in_rule, "lattice": in_lat, "snap": in_snap,
                              "ambiguity": in_amb, "superposition_rate": in_super},
            "held_out_acc": {"rule": ho_rule, "lattice": ho_lat, "snap": ho_snap,
                              "ambiguity": ho_amb, "superposition_rate": ho_super},
            "per_seed": per_seed,
        }
    return {"results": all_results,
             "failure_log": failure_log[:200],
             "superposition_log": superposition_log[:200]}


def render(results: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 6 PHASE 1 — Fixed learner (3 dev escalation requirements applied)")
    lines.append("=" * 96)
    lines.append("")
    lines.append("Three improvements over iteration 5's baseline:")
    lines.append("  (i)   25-input encoder (24 bits + 1 explicit parity feature = sum mod 2)")
    lines.append("  (ii)  Class-balanced cross-entropy loss (weight_c = N / (n_classes * count_c))")
    lines.append("  (iii) 4-layer encoder (was 2), each 64-dim, with tanh nonlinearity")
    lines.append("Plus: ambiguity head + superposition tracking (per user's input that")
    lines.append("the GLM can hold superpositions until future info clarifies).")
    lines.append("")
    lines.append("-" * 96)
    lines.append("[In-distribution accuracy (mean across 3 seeds) — comparison vs iteration 5]")
    lines.append("-" * 96)
    lines.append(f"{'Held-out':<14}{'rule (i5/i6)':<22}{'lattice (i5/i6)':<26}{'snap (i5/i6)':<22}{'superpos':<12}")
    lines.append("-" * 96)
    # Iteration 5 baseline numbers
    iter5_baseline = {
        "toggle":       {"rule": 0.741, "lattice": 0.741, "snap": 1.000},
        "translate":    {"rule": 0.826, "lattice": 0.826, "snap": 1.000},
        "reflect_v":    {"rule": 0.737, "lattice": 0.737, "snap": 1.000},
        "flood_fill":   {"rule": 0.870, "lattice": 0.870, "snap": 1.000},
        "bfs_shortest": {"rule": 0.670, "lattice": 0.670, "snap": 0.989},
    }
    for held_out, r in results["results"].items():
        i = r["in_dist_acc"]
        b = iter5_baseline[held_out]
        lines.append(f"{held_out:<14}"
                     f"{b['rule']:.3f} → {i['rule']:.3f}      "
                     f"{b['lattice']:.3f} → {i['lattice']:.3f}        "
                     f"{b['snap']:.3f} → {i['snap']:.3f}      "
                     f"{i['superposition_rate']:<12.3f}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("[Held-out cross-task accuracy (mean across 3 seeds)]")
    lines.append("-" * 96)
    lines.append(f"{'Held-out':<14}{'rule (i5/i6)':<22}{'lattice (i5/i6)':<26}{'snap (i5/i6)':<22}{'superpos':<12}")
    lines.append("-" * 96)
    iter5_held = {
        "toggle":       {"rule": 0.627, "lattice": 0.627, "snap": 1.000},
        "translate":    {"rule": 0.873, "lattice": 0.873, "snap": 1.000},
        "reflect_v":    {"rule": 0.653, "lattice": 0.653, "snap": 1.000},
        "flood_fill":   {"rule": 0.967, "lattice": 0.967, "snap": 1.000},
        "bfs_shortest": {"rule": 0.600, "lattice": 0.600, "snap": 0.980},
    }
    for held_out, r in results["results"].items():
        h = r["held_out_acc"]
        b = iter5_held[held_out]
        lines.append(f"{held_out:<14}"
                     f"{b['rule']:.3f} → {h['rule']:.3f}      "
                     f"{b['lattice']:.3f} → {h['lattice']:.3f}        "
                     f"{b['snap']:.3f} → {h['snap']:.3f}      "
                     f"{h['superposition_rate']:<12.3f}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("[Failure log + superposition log summary]")
    lines.append("-" * 96)
    fl = results["failure_log"]
    sl = results["superposition_log"]
    lines.append(f"  Total failures (capped 200): {len(fl)}")
    lines.append(f"  Total superpositions held (capped 200): {len(sl)}")
    by_type_fl = {}
    for entry in fl:
        t = entry["type"]
        by_type_fl[t] = by_type_fl.get(t, 0) + 1
    for t, c in by_type_fl.items():
        lines.append(f"    failure: {t}: {c}")
    by_type_sl = {}
    for entry in sl:
        t = entry["type"]
        by_type_sl[t] = by_type_sl.get(t, 0) + 1
    for t, c in by_type_sl.items():
        lines.append(f"    superposition: {t}: {c}")
    lines.append("")
    lines.append("[Failures by task]")
    by_task = {}
    for entry in fl:
        t = entry.get("task", "?")
        by_task[t] = by_task.get(t, 0) + 1
    for t, c in sorted(by_task.items(), key=lambda x: -x[1]):
        lines.append(f"  {t}: {c} failures")
    lines.append("")
    lines.append("[Superpositions by task]")
    by_task_s = {}
    for entry in sl:
        t = entry.get("task", "?")
        by_task_s[t] = by_task_s.get(t, 0) + 1
    for t, c in sorted(by_task_s.items(), key=lambda x: -x[1]):
        lines.append(f"  {t}: {c} superpositions held")
    return "\n".join(lines)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Iteration 6 Phase 1: fixed learner (parity feature + balanced loss + 4-layer encoder)")
    results = run_experiment(n_seeds=3, epochs=200)
    txt = render(results)
    with open(OUT_TXT, "w") as f:
        f.write(txt)
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print()
    print(txt)
    print(f"\nWrote: {OUT_JSON}")
    print(f"Wrote: {OUT_TXT}")


if __name__ == "__main__":
    main()

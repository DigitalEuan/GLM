#!/usr/bin/env python3
"""
Iteration 9 Phase 1 — Junction-aware rule-learner.

Per rec #1: replace the per-target 4-class lattice head with a 17-class
junction head. Each junction corresponds to a (parity, task) combination.
The model learns to predict the junction, which determines the lattice choice.

This should:
  * Reduce training burden (17 classes vs 250 per-target decisions)
  * Improve generalisation (especially on bfs_shortest, where iteration 7's
    learner failed because the F_2 superposition signal was uninformative)
  * Operationalise the user's insight: "many things are practically the same
    operation"
"""

from __future__ import annotations
import sys, os, json, time, random
from fractions import Fraction
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

from glm_universal.substrate import leech2, mog, golay_decode, linalg
from glm_universal.substrate import superposition as sup_mod
from bin_tasks import TASKS

OUT_JSON = "/home/z/my-project/data/iter9_junction_learner.json"
OUT_TXT  = "/home/z/my-project/data/iter9_junction_learner.txt"


# ============================================================================
# 1. Build junction labels for each sample
# ============================================================================
def grid_to_bits_24(grid: np.ndarray) -> int:
    bits = 0
    for v in grid.flatten():
        bits = (bits << 1) | int(v & 1)
    return bits

def leech_class_as_coord_int(bits: int) -> int:
    """Compute the Leech class (mod 2Λ) as an integer, if possible."""
    bits_list = [(bits >> (23 - i)) & 1 for i in range(24)]
    t_principal = tuple(4 * b for b in bits_list)
    try:
        if leech2.in_leech(t_principal):
            return leech2.class_of(t_principal)
    except Exception:
        pass
    # Fallback: use the binary target itself as the "class"
    return bits


def load_data_with_junction_labels() -> Tuple[List[Dict], Dict[int, int]]:
    """Load iteration-4 data, augmented with substrate superposition features
    AND junction labels.
    
    Returns (samples, junction_label_map) where junction_label_map maps
    Leech-class -> junction_index (0..N-1).
    """
    with open("/home/z/my-project/data/iter4_layered_snap.json") as f:
        d = json.load(f)
    samples = []
    # First pass: collect all Leech classes
    leech_classes = []
    for task_name, task_data in d.items():
        for row in task_data["rows"]:
            target_bits = row["target_bits"]
            cls = leech_class_as_coord_int(target_bits)
            leech_classes.append(cls)
    # Build junction label map (class -> junction index, only for classes with 2+ carriers)
    from collections import Counter
    class_counts = Counter(leech_classes)
    # All unique classes get a junction index; those with 2+ are "real" junctions
    unique_classes = sorted(set(leech_classes))
    junction_label_map = {cls: i for i, cls in enumerate(unique_classes)}
    n_junctions = len(unique_classes)
    print(f"  Found {n_junctions} unique Leech classes (= junction labels)")
    multi_carrier_junctions = sum(1 for c, n in class_counts.items() if n > 1)
    print(f"  Of these, {multi_carrier_junctions} have 2+ carriers (true junctions)")
    # Second pass: build samples
    for task_name, task_data in d.items():
        for row in task_data["rows"]:
            target_bits = row["target_bits"]
            bits = [(target_bits >> (23 - i)) & 1 for i in range(24)]
            n_ones = row["n_ones"]
            parity = row["parity"]
            snap24 = row["snap_leech_24"]
            snap32 = row["snap_barnes_wall_32"]
            snap48 = row["snap_ternary_48"]
            sup = sup_mod.superpose(target_bits)
            cls = leech_class_as_coord_int(target_bits)
            junction_label = junction_label_map[cls]
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
                "target_bits": target_bits,
                "sup_dimension": sup.dimension,
                "sup_ambiguous": int(sup.ambiguous),
                "sup_weight": sup.weight,
                "rule_target": rule_target,
                "lattice_target": layer_idx,
                "snap_target": snap_target,
                "junction_label": junction_label,  # NEW: junction class
                "minimum_layer": layer_target,
                "leech_class": cls,
            })
    return samples, junction_label_map


# ============================================================================
# 2. Junction-aware model
# ============================================================================
class JunctionAwareGLM(nn.Module):
    """Iteration 9 model: 27 inputs (24 bits + parity + sup_dim + sup_amb),
    4-layer encoder, 4 heads:
      * rule head (6 classes) — same as iteration 7
      * junction head (N classes, one per Leech class) — NEW
      * snap head (binary) — same
      * ambiguity head (binary) — same
    
    The junction head replaces the lattice head. Predicting the junction
    implicitly determines the lattice choice (via a junction->lattice lookup).
    """
    def __init__(self, hidden_dim=64, n_rules=6, n_junctions=17):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(27, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
        )
        self.rule_head = nn.Linear(hidden_dim, n_rules)
        self.junction_head = nn.Linear(hidden_dim, n_junctions)
        self.snap_head = nn.Linear(hidden_dim, 1)
        self.ambiguity_head = nn.Linear(hidden_dim, 1)
    
    def forward(self, x):
        h = self.encoder(x)
        return {
            "rule": self.rule_head(h),
            "junction": self.junction_head(h),
            "snap": self.snap_head(h).squeeze(-1),
            "ambiguity": self.ambiguity_head(h).squeeze(-1),
        }


def features_with_substrate(samples: List[Dict]) -> torch.Tensor:
    bits = [s["bits"] for s in samples]
    parity = [[sum(b) % 2] for b in bits]
    sup_dim = [[s["sup_dimension"] / 6.0] for s in samples]
    sup_amb = [[s["sup_ambiguous"]] for s in samples]
    return torch.tensor([b + p + sd + sa for b, p, sd, sa in
                          zip(bits, parity, sup_dim, sup_amb)], dtype=torch.float32)


def class_balanced_weights(targets: torch.Tensor, n_classes: int) -> torch.Tensor:
    counts = torch.bincount(targets, minlength=n_classes).float()
    counts = torch.clamp(counts, min=1.0)
    return len(targets) / (n_classes * counts)


def train_one(model, train_data, val_data, n_junctions, epochs=100, lr=0.005, seed=0,
              failure_log=None) -> Dict[str, Any]:
    """Train with junction head + 3 other heads. Mini-batch SGD."""
    if failure_log is None: failure_log = []
    X_tr = features_with_substrate(train_data)
    yr_tr = torch.tensor([s["rule_target"] for s in train_data], dtype=torch.long)
    yj_tr = torch.tensor([s["junction_label"] for s in train_data], dtype=torch.long)
    ys_tr = torch.tensor([s["snap_target"] for s in train_data], dtype=torch.float32)
    ya_tr = torch.tensor([1.0 if (s["lattice_target"] >= 1) else 0.0 for s in train_data], dtype=torch.float32)
    X_va = features_with_substrate(val_data)
    yr_va = torch.tensor([s["rule_target"] for s in val_data], dtype=torch.long)
    yj_va = torch.tensor([s["junction_label"] for s in val_data], dtype=torch.long)
    ys_va = torch.tensor([s["snap_target"] for s in val_data], dtype=torch.float32)
    ya_va = torch.tensor([1.0 if (s["lattice_target"] >= 1) else 0.0 for s in val_data], dtype=torch.float32)
    rule_w = class_balanced_weights(yr_tr, 6)
    jct_w = class_balanced_weights(yj_tr, n_junctions)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    history = {"train_loss": [], "val_acc_rule": [], "val_acc_junction": [],
                "val_acc_snap": [], "val_acc_ambiguity": [],
                "val_junction_to_lattice_acc": []}
    rng = np.random.default_rng(seed)
    n_train = len(train_data)
    batch_size = 32
    for epoch in range(epochs):
        model.train()
        idx = rng.permutation(n_train)
        epoch_loss = 0.0
        for b_start in range(0, n_train, batch_size):
            b_idx = idx[b_start:b_start + batch_size]
            x = X_tr[b_idx]
            out = model(x)
            loss_rule = F.cross_entropy(out["rule"], yr_tr[b_idx], weight=rule_w)
            loss_jct  = F.cross_entropy(out["junction"], yj_tr[b_idx], weight=jct_w)
            loss_snap = F.binary_cross_entropy_with_logits(out["snap"], ys_tr[b_idx])
            loss_amb  = F.binary_cross_entropy_with_logits(out["ambiguity"], ya_tr[b_idx])
            loss = loss_rule + loss_jct + loss_snap + 0.5 * loss_amb
            opt.zero_grad(); loss.backward(); opt.step()
            epoch_loss += loss.item() * len(b_idx)
        epoch_loss /= n_train
        history["train_loss"].append(epoch_loss)
        model.eval()
        with torch.no_grad():
            out = model(X_va)
            pred_rule = out["rule"].argmax(-1)
            pred_jct  = out["junction"].argmax(-1)
            pred_snap = (torch.sigmoid(out["snap"]) > 0.5).float()
            pred_amb  = (torch.sigmoid(out["ambiguity"]) > 0.5).float()
            acc_rule = (pred_rule == yr_va).float().mean().item()
            acc_jct  = (pred_jct  == yj_va).float().mean().item()
            acc_snap = (pred_snap == ys_va).float().mean().item()
            acc_amb  = (pred_amb  == ya_va).float().mean().item()
            # Junction-to-lattice accuracy: map predicted junction to lattice
            # via the train_data's junction->lattice mapping (majority vote)
            jct_to_lattice = {}
            for s in train_data:
                j = s["junction_label"]
                l = s["lattice_target"]
                jct_to_lattice.setdefault(j, []).append(l)
            jct_to_lattice_majority = {j: max(set(ls), key=ls.count)
                                         for j, ls in jct_to_lattice.items()}
            # For each val sample, predict lattice via junction
            val_jcts = [val_data[i].get("junction_label", 0) for i in range(len(val_data))]
            # If val jct is unseen in train, fall back to 0 (Leech_24)
            pred_lattice_via_jct = torch.tensor(
                [jct_to_lattice_majority.get(pred_jct[i].item(), 0) for i in range(len(val_data))],
                dtype=torch.long)
            true_lattice = torch.tensor([s["lattice_target"] for s in val_data], dtype=torch.long)
            jct_to_lattice_acc = (pred_lattice_via_jct == true_lattice).float().mean().item()
        history["val_acc_rule"].append(acc_rule)
        history["val_acc_junction"].append(acc_jct)
        history["val_acc_snap"].append(acc_snap)
        history["val_acc_ambiguity"].append(acc_amb)
        history["val_junction_to_lattice_acc"].append(jct_to_lattice_acc)
        if epoch == epochs - 1:
            for i in range(len(val_data)):
                if pred_jct[i].item() != yj_va[i].item():
                    failure_log.append({
                        "type": "junction_misclassification",
                        "sample_idx": i, "task": val_data[i]["task"],
                        "n_ones": val_data[i]["n_ones"],
                        "parity": val_data[i]["parity"],
                        "true_junction": int(yj_va[i].item()),
                        "pred_junction": int(pred_jct[i].item()),
                        "true_lattice": val_data[i]["minimum_layer"],
                    })
    return {
        "final_train_loss": history["train_loss"][-1],
        "final_val_acc_rule": history["val_acc_rule"][-1],
        "final_val_acc_junction": history["val_acc_junction"][-1],
        "final_val_acc_snap": history["val_acc_snap"][-1],
        "final_val_acc_ambiguity": history["val_acc_ambiguity"][-1],
        "final_val_junction_to_lattice_acc": history["val_junction_to_lattice_acc"][-1],
        "best_val_acc_junction": max(history["val_acc_junction"]),
        "best_junction_to_lattice_acc": max(history["val_junction_to_lattice_acc"]),
        "loss_curve": history["train_loss"],
        "val_junction_curve": history["val_acc_junction"],
        "val_junction_to_lattice_curve": history["val_junction_to_lattice_acc"],
    }


def run_experiment(n_seeds=2, epochs=100) -> Dict[str, Any]:
    samples, junction_label_map = load_data_with_junction_labels()
    n_junctions = len(junction_label_map)
    tasks = ["toggle", "translate", "reflect_v", "flood_fill", "bfs_shortest"]
    all_results = {}
    failure_log = []
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
        # For held-out, junction labels may not be in train. We need to remap
        # unseen junctions to a "unknown" class. Build the full junction space.
        all_junctions = sorted(set(s["junction_label"] for s in samples))
        # For held-out, remap junction labels: if not in train, set to -1 (unknown)
        train_junctions = set(s["junction_label"] for s in train_in_dist)
        # For evaluation: junction accuracy only on seen classes; for unseen,
        # report as "unseen" (separate metric)
        per_seed = []
        for seed in range(n_seeds):
            print(f"  held_out={held_out} seed={seed}...", end=" ", flush=True)
            torch.manual_seed(seed)
            model = JunctionAwareGLM(hidden_dim=64, n_junctions=n_junctions)
            r = train_one(model, train_in_dist, val_in_dist + val_samples,
                           n_junctions=n_junctions, epochs=epochs, lr=0.005, seed=seed,
                           failure_log=failure_log)
            # Evaluate on held-out
            X_ho = features_with_substrate(val_samples)
            yj_ho = torch.tensor([s["junction_label"] for s in val_samples], dtype=torch.long)
            ys_ho = torch.tensor([s["snap_target"] for s in val_samples], dtype=torch.float32)
            ya_ho = torch.tensor([1.0 if (s["lattice_target"] >= 1) else 0.0 for s in val_samples], dtype=torch.float32)
            model.eval()
            with torch.no_grad():
                out = model(X_ho)
                acc_jct_ho = (out["junction"].argmax(-1) == yj_ho).float().mean().item()
                acc_snap_ho = ((torch.sigmoid(out["snap"]) > 0.5).float() == ys_ho).float().mean().item()
                acc_amb_ho = ((torch.sigmoid(out["ambiguity"]) > 0.5).float() == ya_ho).float().mean().item()
                # Junction-to-lattice accuracy on held-out
                jct_to_lattice = {}
                for s in train_in_dist:
                    j = s["junction_label"]
                    l = s["lattice_target"]
                    jct_to_lattice.setdefault(j, []).append(l)
                jct_to_lattice_majority = {j: max(set(ls), key=ls.count)
                                             for j, ls in jct_to_lattice.items()}
                pred_jcts = out["junction"].argmax(-1)
                pred_lattices = [jct_to_lattice_majority.get(pred_jcts[i].item(), 0) for i in range(len(val_samples))]
                true_lattices = [s["lattice_target"] for s in val_samples]
                jct_to_lat_ho = sum(1 for p, t in zip(pred_lattices, true_lattices) if p == t) / len(val_samples)
            print(f"ho_jct={acc_jct_ho:.3f}  ho_jct_to_lat={jct_to_lat_ho:.3f}  "
                  f"ho_snap={acc_snap_ho:.3f}  ho_amb={acc_amb_ho:.3f}")
            per_seed.append({
                "seed": seed,
                "in_dist": {k: v for k, v in r.items() if "curve" not in k},
                "held_out": {
                    "acc_junction": acc_jct_ho,
                    "junction_to_lattice_acc": jct_to_lat_ho,
                    "acc_snap": acc_snap_ho,
                    "acc_ambiguity": acc_amb_ho,
                },
                "loss_curve": r["loss_curve"],
                "val_junction_curve": r["val_junction_curve"],
                "val_junction_to_lattice_curve": r["val_junction_to_lattice_curve"],
            })
        # Aggregate
        in_jct  = np.mean([s["in_dist"]["final_val_acc_junction"] for s in per_seed])
        in_jtl  = np.mean([s["in_dist"]["final_val_junction_to_lattice_acc"] for s in per_seed])
        in_snap = np.mean([s["in_dist"]["final_val_acc_snap"] for s in per_seed])
        in_amb  = np.mean([s["in_dist"]["final_val_acc_ambiguity"] for s in per_seed])
        ho_jct  = np.mean([s["held_out"]["acc_junction"] for s in per_seed])
        ho_jtl  = np.mean([s["held_out"]["junction_to_lattice_acc"] for s in per_seed])
        ho_snap = np.mean([s["held_out"]["acc_snap"] for s in per_seed])
        ho_amb  = np.mean([s["held_out"]["acc_ambiguity"] for s in per_seed])
        all_results[held_out] = {
            "n_seeds": n_seeds,
            "n_junctions_total": n_junctions,
            "in_dist_acc": {"junction": in_jct, "junction_to_lattice": in_jtl,
                              "snap": in_snap, "ambiguity": in_amb},
            "held_out_acc": {"junction": ho_jct, "junction_to_lattice": ho_jtl,
                              "snap": ho_snap, "ambiguity": ho_amb},
            "per_seed": per_seed,
        }
    return {"results": all_results,
             "failure_log": failure_log[:300],
             "n_junctions_total": n_junctions}


def render(results: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 9 PHASE 1 — Junction-aware rule-learner")
    lines.append("=" * 96)
    lines.append("")
    lines.append("Per rec #1: replace the 4-class lattice head with a junction-class head.")
    lines.append(f"Total junctions (unique Leech classes): {results['n_junctions_total']}")
    lines.append("")
    lines.append("-" * 96)
    lines.append("[In-distribution accuracy (mean across seeds) — comparison vs iter 7]")
    lines.append("-" * 96)
    iter7_baseline_in = {
        "toggle":       {"lattice": 0.974, "snap": 1.000, "ambiguity": 1.000},
        "translate":    {"lattice": 1.000, "snap": 1.000, "ambiguity": 0.996},
        "reflect_v":    {"lattice": 0.996, "snap": 1.000, "ambiguity": 1.000},
        "flood_fill":   {"lattice": 0.996, "snap": 1.000, "ambiguity": 1.000},
        "bfs_shortest": {"lattice": 0.878, "snap": 1.000, "ambiguity": 0.974},
    }
    lines.append(f"{'Held-out':<14}{'i7 lattice':<14}{'i9 jct→lat':<16}"
                 f"{'i9 junction':<16}{'i9 snap':<12}{'i9 amb':<12}")
    lines.append("-" * 96)
    for held_out, r in results["results"].items():
        i = r["in_dist_acc"]
        b = iter7_baseline_in[held_out]
        lines.append(f"{held_out:<14}"
                     f"{b['lattice']:<14.3f}"
                     f"{i['junction_to_lattice']:<16.3f}"
                     f"{i['junction']:<16.3f}"
                     f"{i['snap']:<12.3f}{i['ambiguity']:<12.3f}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("[Held-out cross-task accuracy (mean across seeds)]")
    lines.append("-" * 96)
    iter7_baseline_ho = {
        "toggle":       {"lattice": 0.953, "snap": 1.000, "ambiguity": 1.000},
        "translate":    {"lattice": 1.000, "snap": 1.000, "ambiguity": 1.000},
        "reflect_v":    {"lattice": 1.000, "snap": 1.000, "ambiguity": 1.000},
        "flood_fill":   {"lattice": 1.000, "snap": 1.000, "ambiguity": 1.000},
        "bfs_shortest": {"lattice": 0.793, "snap": 1.000, "ambiguity": 0.953},
    }
    lines.append(f"{'Held-out':<14}{'i7 lattice':<14}{'i9 jct→lat':<16}"
                 f"{'i9 junction':<16}{'i9 snap':<12}{'i9 amb':<12}")
    lines.append("-" * 96)
    for held_out, r in results["results"].items():
        h = r["held_out_acc"]
        b = iter7_baseline_ho[held_out]
        lines.append(f"{held_out:<14}"
                     f"{b['lattice']:<14.3f}"
                     f"{h['junction_to_lattice']:<16.3f}"
                     f"{h['junction']:<16.3f}"
                     f"{h['snap']:<12.3f}{h['ambiguity']:<12.3f}")
    lines.append("-" * 96)
    lines.append("")
    # Failure log
    fl = results["failure_log"]
    lines.append(f"[Failure log: {len(fl)} junction misclassifications (capped 300)]")
    lines.append("-" * 96)
    by_task = {}
    for e in fl:
        t = e.get("task", "?")
        by_task[t] = by_task.get(t, 0) + 1
    for t, c in sorted(by_task.items(), key=lambda x: -x[1]):
        lines.append(f"  {t}: {c} failures")
    return "\n".join(lines)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Iteration 9 Phase 1: junction-aware rule-learner")
    results = run_experiment(n_seeds=2, epochs=100)
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

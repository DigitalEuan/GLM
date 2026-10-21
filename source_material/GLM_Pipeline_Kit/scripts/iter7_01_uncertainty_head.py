#!/usr/bin/env python3
"""
Iteration 7 Phase 1 — Uncertainty head via the substrate's superposition.py.

Per the user's input: "have a look for superposition in the existing GLM
repository and also the reasoning/ folder/modules - much of what we need is
likely already built there."

YES IT IS. The substrate exposes a full superposition framework:
  * superpose(mask) -> Superposition (the F2-level list-decoding)
  * Superposition.dimension (1 to 6 candidates)
  * Superposition.ambiguous (coset weight 4 = deep hole)
  * collapse(superposition, context) -> Collapse (collapsed / superposed / refuted)
  * bundle_rational(candidates) -> invertible rational hypervector
  * sextet_cycle_reading(mask) -> the "wiggle" trajectory

For each binary target, we:
  1. Compute sup = superpose(target_bits) — the substrate's F2-level superposition
  2. Feed sup.dimension and sup.ambiguous to the rule-learner as additional inputs
  3. The model's uncertainty head now predicts P(lattice escalation needed | F2 state)

Compare to iteration 6's fixed learner. The hypothesis: substrate-aware features
should let the model detect WHEN to escalate (deep hole) without having to learn
the parity / coset-weight signal from scratch.

Also: demonstrate the collapse() lifecycle on a few samples. The GLM holds the
superposition until a context predicate collapses it (or refutes it, or holds it).
"""

from __future__ import annotations
import sys, os, json, math, random
from fractions import Fraction
from typing import Dict, List, Any, Tuple, Callable
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

GLM_REPO = "/home/z/my-project/glm_repo"
sys.path.insert(0, GLM_REPO)
sys.path.insert(0, "/home/z/my-project/scripts")

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from glm_universal.substrate import superposition as sup_mod
from glm_universal.substrate import leech2, mog, golay_decode, linalg
from bin_tasks import TASKS

OUT_JSON = "/home/z/my-project/data/iter7_uncertainty_head.json"
OUT_TXT  = "/home/z/my-project/data/iter7_uncertainty_head.txt"


# ============================================================================
# 1. Load iteration-4 data and compute superposition features for each sample
# ============================================================================
def load_data_with_superposition() -> List[Dict[str, Any]]:
    """Load iteration-4 layered snap results, augmented with F2 superposition features."""
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
            # Compute the substrate's F2-level superposition
            sup = sup_mod.superpose(target_bits)
            sup_dim = sup.dimension  # 1 to 6
            sup_ambiguous = sup.ambiguous  # True if coset weight 4
            sup_weight = sup.weight  # coset weight 0..4
            # Rule/lattice/snap targets (same as iteration 6)
            if snap24["in_lattice"]:
                rule_target = 0
            elif not (snap24["in_lattice"] or snap32["in_lattice"] or snap48["in_lattice"]):
                rule_target = 5
            else:
                rule_target = 3
            layer_target = row["minimum_layer_needed"]
            layer_idx = {"Leech_24": 0, "Barnes_Wall_32": 1, "Ternary_48": 2, "BEYOND_LATTICE_48": 3}[layer_target]
            snap_target = 1 if row["any_snap_succeeded"] else 0
            # NEW: ambiguity target = whether F2 superposition is ambiguous (deep hole)
            ambiguity_target = 1 if sup_ambiguous else 0
            # NEW: lattice escalation target = whether snap_leech_24 fails
            escalation_target = 1 if (not snap24["in_lattice"]) else 0
            samples.append({
                "task": task_name,
                "bits": bits,
                "n_ones": n_ones,
                "parity": parity,
                "target_bits": target_bits,
                # Substrate superposition features (FREE — computed by the substrate)
                "sup_dimension": sup_dim,
                "sup_ambiguous": int(sup_ambiguous),
                "sup_weight": sup_weight,
                # Targets
                "rule_target": rule_target,
                "lattice_target": layer_idx,
                "snap_target": snap_target,
                "ambiguity_target": ambiguity_target,
                "escalation_target": escalation_target,
                "minimum_layer": layer_target,
            })
    return samples


# ============================================================================
# 2. Substrate-aware multi-head model
# ============================================================================
class SubstrateAwareGLM(nn.Module):
    """Iteration 7 model: 27 inputs = 24 bits + parity + sup_dimension + sup_ambiguous.
    4-layer encoder. 5 heads:
      * rule head (6 classes)
      * lattice head (4 classes)
      * snap head (binary)
      * ambiguity head (binary: is F2 superposition ambiguous?)
      * escalation head (binary: does snap_leech_24 fail?)
    """
    def __init__(self, hidden_dim: int = 64, n_rules: int = 6, n_lattices: int = 4):
        super().__init__()
        # 24 bits + 1 parity + 1 sup_dimension + 1 sup_ambiguous = 27 inputs
        self.encoder = nn.Sequential(
            nn.Linear(27, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim), nn.Tanh(),
        )
        self.rule_head = nn.Linear(hidden_dim, n_rules)
        self.lattice_head = nn.Linear(hidden_dim, n_lattices)
        self.snap_head = nn.Linear(hidden_dim, 1)
        self.ambiguity_head = nn.Linear(hidden_dim, 1)
        self.escalation_head = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        # x: (B, 27)
        h = self.encoder(x)
        return {
            "rule": self.rule_head(h),
            "lattice": self.lattice_head(h),
            "snap": self.snap_head(h).squeeze(-1),
            "ambiguity": self.ambiguity_head(h).squeeze(-1),
            "escalation": self.escalation_head(h).squeeze(-1),
        }


def features_with_substrate(samples: List[Dict]) -> torch.Tensor:
    """27-dim features: 24 bits + 1 parity + 1 sup_dim + 1 sup_amb."""
    bits = [s["bits"] for s in samples]
    parity = [[sum(b) % 2] for b in bits]
    sup_dim = [[s["sup_dimension"]] for s in samples]
    sup_amb = [[s["sup_ambiguous"]] for s in samples]
    # Normalise sup_dim to [0, 1] (max is 6)
    sup_dim_norm = [[d[0] / 6.0] for d in sup_dim]
    X = torch.tensor([b + p + sdn + sa for b, p, sdn, sa in
                       zip(bits, parity, sup_dim_norm, sup_amb)], dtype=torch.float32)
    return X


def class_balanced_weights(targets: torch.Tensor, n_classes: int) -> torch.Tensor:
    counts = torch.bincount(targets, minlength=n_classes).float()
    counts = torch.clamp(counts, min=1.0)
    return len(targets) / (n_classes * counts)


def train_one(model, train_data, val_data, epochs=100, lr=0.005, seed=0,
              failure_log=None, superposition_log=None,
              confidence_gap=0.05) -> Dict[str, Any]:
    """Train with substrate-aware features and 5-head loss. Mini-batch SGD."""
    if failure_log is None: failure_log = []
    if superposition_log is None: superposition_log = []

    X_tr = features_with_substrate(train_data)
    yr_tr = torch.tensor([s["rule_target"] for s in train_data], dtype=torch.long)
    yl_tr = torch.tensor([s["lattice_target"] for s in train_data], dtype=torch.long)
    ys_tr = torch.tensor([s["snap_target"] for s in train_data], dtype=torch.float32)
    ya_tr = torch.tensor([s["ambiguity_target"] for s in train_data], dtype=torch.float32)
    ye_tr = torch.tensor([s["escalation_target"] for s in train_data], dtype=torch.float32)

    X_va = features_with_substrate(val_data)
    yr_va = torch.tensor([s["rule_target"] for s in val_data], dtype=torch.long)
    yl_va = torch.tensor([s["lattice_target"] for s in val_data], dtype=torch.long)
    ys_va = torch.tensor([s["snap_target"] for s in val_data], dtype=torch.float32)
    ya_va = torch.tensor([s["ambiguity_target"] for s in val_data], dtype=torch.float32)
    ye_va = torch.tensor([s["escalation_target"] for s in val_data], dtype=torch.float32)

    rule_w = class_balanced_weights(yr_tr, 6)
    lat_w  = class_balanced_weights(yl_tr, 4)

    opt = torch.optim.Adam(model.parameters(), lr=lr)
    history = {"train_loss": [], "val_acc_rule": [], "val_acc_lattice": [],
                "val_acc_snap": [], "val_acc_ambiguity": [], "val_acc_escalation": [],
                "val_superposition_rate": []}
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
            loss_lat  = F.cross_entropy(out["lattice"], yl_tr[b_idx], weight=lat_w)
            loss_snap = F.binary_cross_entropy_with_logits(out["snap"], ys_tr[b_idx])
            loss_amb  = F.binary_cross_entropy_with_logits(out["ambiguity"], ya_tr[b_idx])
            loss_esc  = F.binary_cross_entropy_with_logits(out["escalation"], ye_tr[b_idx])
            loss = loss_rule + loss_lat + loss_snap + 0.5 * loss_amb + 0.5 * loss_esc
            opt.zero_grad(); loss.backward(); opt.step()
            epoch_loss += loss.item() * len(b_idx)
        epoch_loss /= n_train
        history["train_loss"].append(epoch_loss)
        model.eval()
        with torch.no_grad():
            out = model(X_va)
            pred_rule = out["rule"].argmax(-1)
            pred_lat  = out["lattice"].argmax(-1)
            pred_snap = (torch.sigmoid(out["snap"]) > 0.5).float()
            pred_amb  = (torch.sigmoid(out["ambiguity"]) > 0.5).float()
            pred_esc  = (torch.sigmoid(out["escalation"]) > 0.5).float()
            acc_rule = (pred_rule == yr_va).float().mean().item()
            acc_lat  = (pred_lat  == yl_va).float().mean().item()
            acc_snap = (pred_snap == ys_va).float().mean().item()
            acc_amb  = (pred_amb  == ya_va).float().mean().item()
            acc_esc  = (pred_esc  == ye_va).float().mean().item()
            lp = F.softmax(out["lattice"], dim=-1)
            top2 = lp.topk(2, dim=-1).values
            sup_mask = (top2[:, 0] - top2[:, 1]) < confidence_gap
            sup_rate = sup_mask.float().mean().item()
        history["val_acc_rule"].append(acc_rule)
        history["val_acc_lattice"].append(acc_lat)
        history["val_acc_snap"].append(acc_snap)
        history["val_acc_ambiguity"].append(acc_amb)
        history["val_acc_escalation"].append(acc_esc)
        history["val_superposition_rate"].append(sup_rate)
        if epoch == epochs - 1:
            for i in range(len(val_data)):
                if sup_mask[i]:
                    top2_idx = lp[i].topk(2).indices.tolist()
                    superposition_log.append({
                        "type": "lattice_superposition",
                        "sample_idx": i,
                        "task": val_data[i]["task"],
                        "n_ones": val_data[i]["n_ones"],
                        "parity": val_data[i]["parity"],
                        "sup_dimension": val_data[i]["sup_dimension"],
                        "sup_ambiguous": val_data[i]["sup_ambiguous"],
                        "true_lattice": val_data[i]["minimum_layer"],
                        "top1_lattice": ["Leech_24", "Barnes_Wall_32", "Ternary_48", "BEYOND"][top2_idx[0]],
                        "top2_lattice": ["Leech_24", "Barnes_Wall_32", "Ternary_48", "BEYOND"][top2_idx[1]],
                        "top1_prob": float(lp[i][top2_idx[0]].item()),
                        "top2_prob": float(lp[i][top2_idx[1]].item()),
                        "reason": "model holds multiple lattice predictions (awaiting clarification)",
                    })
                if not sup_mask[i]:
                    if pred_lat[i].item() != yl_va[i].item():
                        failure_log.append({
                            "type": "lattice_misclassification",
                            "sample_idx": i, "task": val_data[i]["task"],
                            "n_ones": val_data[i]["n_ones"],
                            "parity": val_data[i]["parity"],
                            "sup_dimension": val_data[i]["sup_dimension"],
                            "sup_ambiguous": val_data[i]["sup_ambiguous"],
                            "true_lattice": val_data[i]["minimum_layer"],
                            "pred_lattice_idx": int(pred_lat[i].item()),
                            "reason": "model predicted wrong lattice (no superposition held)",
                        })
    return {
        "final_train_loss": history["train_loss"][-1],
        "final_val_acc_rule": history["val_acc_rule"][-1],
        "final_val_acc_lattice": history["val_acc_lattice"][-1],
        "final_val_acc_snap": history["val_acc_snap"][-1],
        "final_val_acc_ambiguity": history["val_acc_ambiguity"][-1],
        "final_val_acc_escalation": history["val_acc_escalation"][-1],
        "final_superposition_rate": history["val_superposition_rate"][-1],
        "best_val_acc_rule": max(history["val_acc_rule"]),
        "best_val_acc_lattice": max(history["val_acc_lattice"]),
        "best_val_acc_ambiguity": max(history["val_acc_ambiguity"]),
        "best_val_acc_escalation": max(history["val_acc_escalation"]),
        "loss_curve": history["train_loss"],
        "val_rule_curve": history["val_acc_rule"],
        "val_lattice_curve": history["val_acc_lattice"],
        "val_ambiguity_curve": history["val_acc_ambiguity"],
        "val_escalation_curve": history["val_acc_escalation"],
        "val_superposition_curve": history["val_superposition_rate"],
    }


def run_experiment(n_seeds=2, epochs=100) -> Dict[str, Any]:
    samples = load_data_with_superposition()
    print(f"Loaded {len(samples)} samples (augmented with superposition features)")
    # Print superposition distribution
    sup_amb_count = sum(1 for s in samples if s["sup_ambiguous"])
    print(f"  F2 superposition ambiguous: {sup_amb_count}/{len(samples)} ({100*sup_amb_count/len(samples):.1f}%)")
    sup_dims = [s["sup_dimension"] for s in samples]
    print(f"  sup_dimension distribution: {dict((d, sup_dims.count(d)) for d in set(sup_dims))}")
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
            model = SubstrateAwareGLM(hidden_dim=64)
            r = train_one(model, train_in_dist, val_in_dist + val_samples,
                           epochs=epochs, lr=0.01, seed=seed,
                           failure_log=failure_log,
                           superposition_log=superposition_log,
                           confidence_gap=0.05)
            X_ho = features_with_substrate(val_samples)
            yr_ho = torch.tensor([s["rule_target"] for s in val_samples], dtype=torch.long)
            yl_ho = torch.tensor([s["lattice_target"] for s in val_samples], dtype=torch.long)
            ys_ho = torch.tensor([s["snap_target"] for s in val_samples], dtype=torch.float32)
            ya_ho = torch.tensor([s["ambiguity_target"] for s in val_samples], dtype=torch.float32)
            ye_ho = torch.tensor([s["escalation_target"] for s in val_samples], dtype=torch.float32)
            model.eval()
            with torch.no_grad():
                out = model(X_ho)
                acc_rule_ho = (out["rule"].argmax(-1) == yr_ho).float().mean().item()
                acc_lat_ho = (out["lattice"].argmax(-1) == yl_ho).float().mean().item()
                acc_snap_ho = ((torch.sigmoid(out["snap"]) > 0.5).float() == ys_ho).float().mean().item()
                acc_amb_ho = ((torch.sigmoid(out["ambiguity"]) > 0.5).float() == ya_ho).float().mean().item()
                acc_esc_ho = ((torch.sigmoid(out["escalation"]) > 0.5).float() == ye_ho).float().mean().item()
                lp = F.softmax(out["lattice"], dim=-1)
                top2 = lp.topk(2, dim=-1).values
                ho_sup_rate = ((top2[:, 0] - top2[:, 1]) < 0.05).float().mean().item()
            print(f"ho_rule={acc_rule_ho:.3f}  ho_lat={acc_lat_ho:.3f}  "
                  f"ho_amb={acc_amb_ho:.3f}  ho_esc={acc_esc_ho:.3f}  "
                  f"ho_sup={ho_sup_rate:.3f}")
            per_seed.append({
                "seed": seed,
                "in_dist": {k: v for k, v in r.items() if "curve" not in k},
                "held_out": {
                    "acc_rule": acc_rule_ho, "acc_lattice": acc_lat_ho,
                    "acc_snap": acc_snap_ho, "acc_ambiguity": acc_amb_ho,
                    "acc_escalation": acc_esc_ho, "superposition_rate": ho_sup_rate,
                },
                "loss_curve": r["loss_curve"],
                "val_lattice_curve": r["val_lattice_curve"],
                "val_ambiguity_curve": r["val_ambiguity_curve"],
                "val_superposition_curve": r["val_superposition_curve"],
            })
        in_rule = np.mean([s["in_dist"]["final_val_acc_rule"] for s in per_seed])
        in_lat  = np.mean([s["in_dist"]["final_val_acc_lattice"] for s in per_seed])
        in_snap = np.mean([s["in_dist"]["final_val_acc_snap"] for s in per_seed])
        in_amb  = np.mean([s["in_dist"]["final_val_acc_ambiguity"] for s in per_seed])
        in_esc  = np.mean([s["in_dist"]["final_val_acc_escalation"] for s in per_seed])
        in_sup  = np.mean([s["in_dist"]["final_superposition_rate"] for s in per_seed])
        ho_rule = np.mean([s["held_out"]["acc_rule"] for s in per_seed])
        ho_lat  = np.mean([s["held_out"]["acc_lattice"] for s in per_seed])
        ho_snap = np.mean([s["held_out"]["acc_snap"] for s in per_seed])
        ho_amb  = np.mean([s["held_out"]["acc_ambiguity"] for s in per_seed])
        ho_esc  = np.mean([s["held_out"]["acc_escalation"] for s in per_seed])
        ho_sup  = np.mean([s["held_out"]["superposition_rate"] for s in per_seed])
        all_results[held_out] = {
            "n_seeds": n_seeds,
            "in_dist_acc": {"rule": in_rule, "lattice": in_lat, "snap": in_snap,
                              "ambiguity": in_amb, "escalation": in_esc,
                              "superposition_rate": in_sup},
            "held_out_acc": {"rule": ho_rule, "lattice": ho_lat, "snap": ho_snap,
                              "ambiguity": ho_amb, "escalation": ho_esc,
                              "superposition_rate": ho_sup},
            "per_seed": per_seed,
        }
    return {"results": all_results,
             "failure_log": failure_log[:300],
             "superposition_log": superposition_log[:300]}


# ============================================================================
# 3. Demonstrate the collapse() lifecycle on a few samples
# ============================================================================
def demonstrate_collapse_lifecycle():
    """Run the substrate's collapse() on a few sample targets to show the
    full superposition lifecycle: hold -> collapse (or refute)."""
    print("\n=== Collapse lifecycle demonstration ===")
    from bin_tasks import sample_task
    demos = []
    for task_name in ["toggle", "translate"]:
        for seed in [1, 2, 3]:
            x, _, _ = sample_task(task_name, seed=seed, H=4, W=6, dx=1, dy=1)
            bits = 0
            for v in x.flatten():
                bits = (bits << 1) | int(v & 1)
            sup = sup_mod.superpose(bits)
            if sup.ambiguous:
                # Demonstrate 3 collapse scenarios
                chosen = sup.candidates[0]
                # Context 1: pick the chosen codeword -> collapsed
                c1 = sup_mod.collapse(sup, lambda c: c == chosen)
                # Context 2: pick all codewords with weight <= 12 -> superposed
                c2 = sup_mod.collapse(sup, lambda c: linalg.popcount(c) <= 12)
                # Context 3: pick codewords with weight == 1 -> refuted (no weight-1 codewords)
                c3 = sup_mod.collapse(sup, lambda c: linalg.popcount(c) == 1)
                demos.append({
                    "task": task_name, "seed": seed,
                    "target_bits": bits, "n_ones": sup.weight,
                    "sup_dimension": sup.dimension,
                    "candidates_count": len(sup.candidates),
                    "collapse_scenarios": [
                        {"context": "pick_chosen", "status": c1.status, "value": c1.value},
                        {"context": "weight_le_12", "status": c2.status, "survivors": len(c2.after)},
                        {"context": "weight_eq_1", "status": c3.status, "survivors": len(c3.after)},
                    ],
                })
                print(f"  {task_name}/seed{seed}: dim={sup.dimension}, "
                      f"collapse[chosen]={c1.status}, collapse[w<=12]={c2.status}, "
                      f"collapse[w==1]={c3.status}")
    return demos


# ============================================================================
# 4. Render + main
# ============================================================================
def render(results: Dict[str, Any]) -> str:
    lines = []
    lines.append("=" * 96)
    lines.append("ITERATION 7 PHASE 1 — Uncertainty head via substrate's superposition.py")
    lines.append("=" * 96)
    lines.append("")
    lines.append("Per user input: 'have a look for superposition in the existing GLM repository —")
    lines.append("much of what we need is likely already built there.'")
    lines.append("")
    lines.append("YES. The substrate exposes superpose(), collapse(sup, context),")
    lines.append("bundle_rational(), and sextet_cycle_reading(). We use these DIRECTLY:")
    lines.append("  * superpose(target_bits) -> Superposition (F2-level list decoding)")
    lines.append("  * sup.dimension (1 to 6 candidates) — fed to the model as a feature")
    lines.append("  * sup.ambiguous (coset weight 4 = deep hole) — fed to the model as a feature")
    lines.append("  * collapse(sup, context) — demonstrated on a few samples")
    lines.append("")
    lines.append("Model: 27-input encoder (24 bits + parity + sup_dim + sup_amb), 4 layers,")
    lines.append("5 heads: rule + lattice + snap + ambiguity + escalation.")
    lines.append("")
    lines.append("-" * 96)
    lines.append("[In-distribution accuracy (mean across 3 seeds) — comparison vs iteration 6]")
    lines.append("-" * 96)
    iter6_baseline = {
        "toggle":       {"rule": 0.756, "lattice": 0.756, "snap": 1.000},
        "translate":    {"rule": 0.978, "lattice": 0.978, "snap": 1.000},
        "reflect_v":    {"rule": 0.844, "lattice": 0.844, "snap": 1.000},
        "flood_fill":   {"rule": 0.970, "lattice": 0.970, "snap": 1.000},
        "bfs_shortest": {"rule": 0.974, "lattice": 0.974, "snap": 1.000},
    }
    lines.append(f"{'Held-out':<14}{'lattice (i6/i7)':<22}{'ambiguity':<14}{'escalation':<14}{'superpos rate':<16}")
    lines.append("-" * 96)
    for held_out, r in results["results"].items():
        i = r["in_dist_acc"]
        b = iter6_baseline[held_out]
        lines.append(f"{held_out:<14}"
                     f"{b['lattice']:.3f} → {i['lattice']:.3f}      "
                     f"{i['ambiguity']:<14.3f}{i['escalation']:<14.3f}"
                     f"{i['superposition_rate']:<16.3f}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("[Held-out cross-task accuracy (mean across 3 seeds)]")
    lines.append("-" * 96)
    iter6_held = {
        "toggle":       {"rule": 0.613, "lattice": 0.613, "snap": 1.000},
        "translate":    {"rule": 1.000, "lattice": 1.000, "snap": 1.000},
        "reflect_v":    {"rule": 0.747, "lattice": 0.747, "snap": 1.000},
        "flood_fill":   {"rule": 1.000, "lattice": 1.000, "snap": 1.000},
        "bfs_shortest": {"rule": 0.987, "lattice": 0.987, "snap": 1.000},
    }
    lines.append(f"{'Held-out':<14}{'lattice (i6/i7)':<22}{'ambiguity':<14}{'escalation':<14}{'superpos rate':<16}")
    lines.append("-" * 96)
    for held_out, r in results["results"].items():
        h = r["held_out_acc"]
        b = iter6_held[held_out]
        lines.append(f"{held_out:<14}"
                     f"{b['lattice']:.3f} → {h['lattice']:.3f}      "
                     f"{h['ambiguity']:<14.3f}{h['escalation']:<14.3f}"
                     f"{h['superposition_rate']:<16.3f}")
    lines.append("-" * 96)
    lines.append("")
    lines.append("[Failure + superposition log summary]")
    lines.append("-" * 96)
    fl = results["failure_log"]
    sl = results["superposition_log"]
    lines.append(f"  Total failures (capped 300): {len(fl)}")
    lines.append(f"  Total superpositions held (capped 300): {len(sl)}")
    by_type_fl = {}
    for e in fl:
        by_type_fl[e["type"]] = by_type_fl.get(e["type"], 0) + 1
    for t, c in by_type_fl.items():
        lines.append(f"    failure: {t}: {c}")
    by_type_sl = {}
    for e in sl:
        by_type_sl[e["type"]] = by_type_sl.get(e["type"], 0) + 1
    for t, c in by_type_sl.items():
        lines.append(f"    superposition: {t}: {c}")
    lines.append("")
    lines.append("[Failures by task]")
    by_task = {}
    for e in fl:
        t = e.get("task", "?")
        by_task[t] = by_task.get(t, 0) + 1
    for t, c in sorted(by_task.items(), key=lambda x: -x[1]):
        lines.append(f"  {t}: {c} failures")
    lines.append("")
    lines.append("[Superpositions by task]")
    by_task_s = {}
    for e in sl:
        t = e.get("task", "?")
        by_task_s[t] = by_task_s.get(t, 0) + 1
    for t, c in sorted(by_task_s.items(), key=lambda x: -x[1]):
        lines.append(f"  {t}: {c} superpositions held")
    return "\n".join(lines)


def main():
    os.makedirs("/home/z/my-project/data", exist_ok=True)
    print("Iteration 7 Phase 1: uncertainty head via substrate's superposition.py")
    results = run_experiment(n_seeds=3, epochs=200)
    # Demonstrate the collapse lifecycle
    demos = demonstrate_collapse_lifecycle()
    results["collapse_demos"] = demos
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

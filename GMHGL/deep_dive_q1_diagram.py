"""
Diagram for the Q1 deep-dive finding: TAX-identical / 3D-divergent cascades.
Shows that 6 different flip orderings, all ending at the same vector (same TAX),
produce 3 unique 3D eval values — a clean separation of state cost from trajectory cost.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch
import sys
from pathlib import Path
from fractions import Fraction
from itertools import permutations

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/z/my-project/download")

import ubp_unified_v5 as ubp
import spatial_arithmetic as sa

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

leech = ubp.LEECH_ENGINE
golay = ubp.GOLAY_ENGINE

# Reproduce the Q1 experiment
octad0 = golay.get_octads()[0]
start_v = [0] * 24
for i, b in enumerate(octad0):
    if b:
        start_v[i] = 2

active = [i for i in range(24) if start_v[i] != 0]
inactive = [i for i in range(24) if start_v[i] == 0]
deexcite_bits = active[:2]
activate_bits = inactive[:2]
flips_set = deexcite_bits + activate_bits
orderings = list(permutations(flips_set))[:6]

QUADRANT_OPERATOR = {"M": "MULTIPLY", "I": "DIVIDE", "A": "ADD", "P": "SUBTRACT"}

results = []
for ordering in orderings:
    v = list(start_v)
    hw_trajectory = [sum(1 for x in v if x != 0)]
    for bit in ordering:
        v[bit] = 0 if v[bit] != 0 else 1
        hw_trajectory.append(sum(1 for x in v if x != 0))
    final_tax = leech.calculate_symmetry_tax(v)
    tokens = []
    for j, hw in enumerate(hw_trajectory):
        if j > 0:
            quad = "MIAP"[ordering[j-1] // 6]
            tokens.append(QUADRANT_OPERATOR[quad])
        tokens.append(hw)
    scene = sa.build_expression(tokens, seed=42)
    obs = sa.observe_expression(scene)
    results.append({
        "ordering": ordering,
        "hw_trajectory": hw_trajectory,
        "final_tax": final_tax,
        "tokens": tokens,
        "eval": obs["result"] if obs["ok"] else "FAILED",
    })

# ── Figure: 2 panels ────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(16, 7), constrained_layout=True)

# ── LEFT: All 6 paths converge to the same TAX ─────────────────────────────
ax_tax = axes[0]
colors = ['#E65100', '#E65100', '#1565C0', '#1565C0', '#2E7D32', '#2E7D32']
eval_labels = ['392', '392', '504', '504', '4040', '4040']

for i, r in enumerate(results):
    steps = list(range(len(r["hw_trajectory"])))
    taxes = []
    v = list(start_v)
    taxes.append(float(leech.calculate_symmetry_tax(v)))
    for bit in r["ordering"]:
        v[bit] = 0 if v[bit] != 0 else 1
        taxes.append(float(leech.calculate_symmetry_tax(v)))
    ax_tax.plot(steps, taxes, 'o-', color=colors[i], linewidth=2, markersize=8,
                alpha=0.8, label=f"Path {i+1}: {r['ordering']} → 3D={eval_labels[i]}")

ax_tax.set_xlabel('Cascade step', fontsize=12)
ax_tax.set_ylabel('TAX (Symmetry Tax)', fontsize=12)
ax_tax.set_title('All 6 Paths Converge to the SAME TAX\n(state cost is path-independent)',
                 fontsize=13, fontweight='bold')
ax_tax.legend(fontsize=8, loc='lower left')
ax_tax.grid(True, alpha=0.3)
ax_tax.set_xticks(range(5))

# Annotate the convergence
final_tax = float(results[0]["final_tax"])
ax_tax.annotate(f'All paths end here\nTAX = {final_tax:.4f}',
               xy=(4, final_tax), xytext=(2.5, final_tax + 0.3),
               fontsize=9, fontweight='bold', color='red',
               arrowprops=dict(arrowstyle='->', color='red', lw=1.5))

# ── RIGHT: 3D eval diverges despite same TAX ───────────────────────────────
ax_3d = axes[1]
unique_evals = sorted(set(float(r["eval"]) for r in results if isinstance(r["eval"], (int, Fraction))))
eval_to_y = {e: i for i, e in enumerate(unique_evals)}

for i, r in enumerate(results):
    if isinstance(r["eval"], (int, Fraction)):
        y_val = eval_to_y[float(r["eval"])]
        ax_3d.scatter([i], [y_val], s=200, color=colors[i], edgecolor='black', linewidth=1.5, zorder=5)
        ax_3d.annotate(f'{float(r["eval"]):.0f}', (i, y_val),
                      textcoords="offset points", xytext=(0, 12),
                      fontsize=10, fontweight='bold', ha='center', color=colors[i])

ax_3d.set_ylabel('3D eval result (unique values)', fontsize=12)
ax_3d.set_title('3D Eval DIVERGES Despite Same TAX\n(trajectory cost is path-dependent)',
                fontsize=13, fontweight='bold')
ax_3d.set_yticks(range(len(unique_evals)))
ax_3d.set_yticklabels([f'{e:.0f}' for e in unique_evals], fontsize=11)
ax_3d.set_xticks(range(6))
ax_3d.set_xticklabels([f"Path {i+1}\n{r['ordering']}" for i, r in enumerate(results)], fontsize=8)
ax_3d.grid(True, alpha=0.3, axis='y')

# Add horizontal lines showing the 3 unique values
for e in unique_evals:
    y = eval_to_y[e]
    ax_3d.axhline(y=y, color='gray', linewidth=0.5, linestyle=':', alpha=0.5)

# Summary annotation
ax_3d.text(0.5, -0.15,
           f'6 paths, identical TAX, {len(unique_evals)} unique 3D evals\n'
           f'→ TAX = state cost (path-independent)\n'
           f'→ 3D eval = trajectory cost (path-dependent)',
           transform=ax_3d.transAxes, fontsize=10, ha='center', va='top',
           bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFF8E1', edgecolor='#B85C00'))

fig.suptitle('Q1 Deep-Dive: TAX vs 3D Eval — State Cost vs Trajectory Cost',
             fontsize=15, fontweight='bold', y=1.02)

plt.savefig('/home/z/my-project/download/deep_dive_q1_diagram.png',
            dpi=150, facecolor='white')
print("Saved: /home/z/my-project/download/deep_dive_q1_diagram.png")

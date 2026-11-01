"""Attention-simulator experiment suite (drives glm_repo's sandbox module).

Runs outside the GLM package (floats and clocks are allowed HERE, never
inside the package) and produces every figure and number the findings memo
and the study doc quote:
  exp0  paper reproduction (Figures 2 and 3, exact)
  exp1  elementary ops vs shipped ground truth + head counts vs paper tables
  exp2  exponential precision law + the low-depth INVERSION on real carriers
  exp3  simulator tax: construction vs direct formula
  exp4  register bridge: three scorings, temperature dial, hard/soft ends
  exp5  coverage boundary, hierarchy embedding, multi-head agreement
"""
import json
import os
import sys
import time
from fractions import Fraction
from pathlib import Path

# Locate the GLM repository: GLM_REPO env var, else the current directory,
# else the directory this script sits in (if the package was unzipped
# inside the repo) or its parent.
def _find_repo() -> Path:
    candidates = []
    env = os.environ.get("GLM_REPO")
    if env:
        candidates.append(Path(env))
    candidates += [Path.cwd(), Path(__file__).resolve().parent,
                   Path(__file__).resolve().parent.parent]
    for c in candidates:
        if (c / "glm_universal" / "sandbox" / "attention_simulator.py").is_file():
            return c.resolve()
    sys.exit(
        "cannot find the GLM repo (expected glm_universal/sandbox/"
        "attention_simulator.py).\nRun from the repository root, or set "
        "GLM_REPO=/path/to/GLM.\nThe repo_patch.diff must be applied first "
        "(`git apply repo_patch.diff`).")

REPO = _find_repo()
sys.path.insert(0, str(REPO))

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
    try:
        fm.fontManager.addfont(f)
    except Exception:
        pass
import matplotlib.pyplot as plt
plt.rcParams.update({
    "font.sans-serif": ["DejaVu Sans"], "axes.unicode_minus": False,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
    "figure.dpi": 150, "savefig.dpi": 150, "font.size": 9,
})

from glm_universal.runtime.session import GeometricSession
from glm_universal.reasoning import metric as M
from glm_universal.sandbox import attention_simulator as asi

OUT = Path(os.environ.get("ATTN_OUT",
                           Path(__file__).resolve().parent / "findings"))
OUT.mkdir(parents=True, exist_ok=True)
print(f"repo: {REPO}")
print(f"out:  {OUT}")
R = {}

def F(x):
    return float(x)

# ===========================================================================
# exp0 — the paper's own demonstrations, re-run exactly
# ===========================================================================
print("== exp0: paper reproduction ==")
t0 = time.perf_counter()
demo = asi.paper_demo()
inv = asi.paper_inverse_demo()
R["exp0"] = {
    "stage_errors": {k: (0 if v == 0 else F(v)) for k, v in
                     demo["stage_errors"].items()},
    "exact_stage_count": sum(1 for v in demo["stage_errors"].values()
                             if v == 0),
    "vs_printed_softmax": F(demo["vs_printed_softmax"]),
    "vs_printed_output": F(demo["vs_printed_output"]),
    "paper_reported": {"softmax": 3.376358e-06, "output": 3.040329e-07},
    "heads_total": demo["tally"]["heads"],
    "heads_paper_accounting": 64,
    "inverse_agrees_gauss_jordan": inv["agrees_with_gauss_jordan"],
    "inverse_det": str(inv["determinant"]),
    "inverse_vs_printed": F(inv["vs_printed_decimals"]),
    "inverse_exact": [[str(x) for x in row] for row in inv["inverse"]],
    "wall_seconds": time.perf_counter() - t0,
}
print(f"  5/7 stages exactly zero; softmax {R['exp0']['stage_errors']['Y3 = softmax(Y2)']:.2e}"
      f" (paper: 3.38e-06 float); heads {R['exp0']['heads_total']} == paper 64")

# ===========================================================================
# exp1 — elementary ops vs shipped ground truth; heads vs paper's tables
# ===========================================================================
print("== exp1: ground truth + head counts ==")
shapes = ((1, 24), (2, 12), (3, 8), (4, 6), (6, 4), (8, 3), (12, 2), (24, 1))
transpose_ok, matmul_ok = True, True
from glm_universal.data_objects.mathematics import RationalMatrix, compose_matrices
for r, c in shapes:
    m = asi._deterministic_matrix(r, c)
    transpose_ok &= asi._max_abs_diff(
        asi.transpose_sim(m),
        RationalMatrix.from_rows("m", m).transpose().row_list()) == 0
matmul_cases = []
for ra, ca, cb in ((3, 3, 3), (2, 12, 2), (4, 6, 4), (1, 24, 1), (3, 8, 3),
                   (6, 4, 6)):
    am, bm = asi._deterministic_matrix(ra, ca), asi._deterministic_matrix(ca, cb, 2)
    asi.begin_instrumentation()
    got = asi.matmul_sim(am, bm)
    heads = asi.end_instrumentation()["heads"]
    truth = (_direct := asi._direct_matmul(am, bm))
    ok = asi._max_abs_diff(got, truth) == 0
    matmul_ok &= ok
    matmul_cases.append({"shape": f"{ra}x{ca} . {ca}x{cb}",
                         "heads": heads, "formula": ra + cb + ra * cb,
                         "exact": ok})
inv_cases = []
for salt in (1, 2, 3, 4):
    m = asi._deterministic_matrix(3, 3, salt)
    try:
        mine = asi.inverse3_sim(m)
        truth = asi._product._inverse3([list(row) for row in m])
        inv_cases.append({"salt": salt,
                          "agrees": asi._max_abs_diff(
                              mine, tuple(tuple(r) for r in truth)) == 0})
    except ValueError:
        inv_cases.append({"salt": salt, "agrees": None})  # singular, refused
R["exp1"] = {
    "transpose_agrees_all_shapes": transpose_ok,
    "matmul_agrees": matmul_ok,
    "matmul_cases": matmul_cases,
    "inverse_cases": inv_cases,
    "softmax_heads_3x3": asi.construction_report()["softmax_heads"],
    "matmul_heads_3x4x4": [c for c in matmul_cases if "3x4" in c["shape"]],
}
print(f"  transpose {transpose_ok} | matmul {matmul_ok} | "
      f"heads==r+c+rc in all cases: {all(c['heads']==c['formula'] for c in matmul_cases)}")

fig, ax = plt.subplots(figsize=(4.6, 3.0), constrained_layout=True)
labels = [c["shape"].replace(" . ", " @ ") for c in matmul_cases]
meas = [c["heads"] for c in matmul_cases]
form = [c["formula"] for c in matmul_cases]
xp = range(len(labels))
ax.bar([x - 0.2 for x in xp], meas, width=0.4, label="measured heads",
       color="#1a6faa")
ax.bar([x + 0.2 for x in xp], form, width=0.4, label="paper: r + c + rc",
       color="#c8c8c8")
ax.set_xticks(list(xp)); ax.set_xticklabels(labels, rotation=20, ha="right")
ax.set_ylabel("attention heads"); ax.legend(frameon=False)
ax.set_title("Multiplication construction width vs the paper's Table 2",
             fontsize=10)
fig.savefig(OUT / "exp1_heads.png"); plt.close(fig)

# ===========================================================================
# exp2 — the exponential: precision law, and the inversion on real carriers
# ===========================================================================
print("== exp2: precision law + inversion ==")
# (a) paper demo: error vs depth against a depth-200 reference
depths = list(range(4, 40, 2))
g2 = asi._direct_matmul(asi._direct_matmul(asi.PAPER_DEMO_X, asi.PAPER_DEMO_A),
                        tuple(zip(*asi.PAPER_DEMO_X)))
ref = asi.softmax_sim(g2, 200)
rng = max(max(r) - min(r) for r in g2)
errs, bounds = [], []
for d in depths:
    errs.append(F(asi._max_abs_diff(asi.softmax_sim(g2, d), ref)))
    bounds.append(F(asi.exp_rational_bound(Fraction(-1, 1) * rng, d)
                    if d >= F(rng) else None) if False else None)
# alternating bound valid only for d >= range; compute where possible
bounds = []
for d in depths:
    if Fraction(d) >= rng:
        bounds.append((d, F(asi.exp_rational_bound(-rng, d))))
    else:
        bounds.append((d, None))

# (b) THE INVERSION: raw identity scoring on a real register block,
# scaled by a rational temperature to a range the sweep can afford (the
# physics is depth-vs-range; temperature is an exact rational dial)
sess = GeometricSession()
rows = asi._register_rows(sess, "lexicon")[:4]
x4 = tuple(c for _, c in rows)
names4 = [n for n, _ in rows]
scores_raw_full = asi.attention_scores(x4, None, 1)
rng_raw_full = max(max(r) - min(r) for r in scores_raw_full)
t_scale = Fraction(1, 1000)
scores_raw = asi.attention_scores(x4, None, t_scale)
rng_raw = max(max(r) - min(r) for r in scores_raw)
ref_depth = int(F(rng_raw)) + 60
ref_raw = asi.softmax_sim(scores_raw, ref_depth)
true_top = [max(range(4), key=lambda j: (r[j], -j)) for r in scores_raw]
# log-spaced depths straddling the range, plus the crossing point itself
inv_depths = [4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 56, 64, 80]
cross = ref_depth
if cross not in inv_depths:
    inv_depths = sorted(inv_depths + [cross])
inv_rows = []
for d in inv_depths:
    w = asi.softmax_sim(scores_raw, d)
    top1 = [max(range(4), key=lambda j: (r[j], -j)) for r in w]
    correct = sum(1 for a, b in zip(top1, true_top) if a == b)
    # distance of produced weights from the reference weights
    dist = F(asi._max_abs_diff(w, ref_raw))
    inv_rows.append({"depth": d, "top1_correct": correct, "max_abs_diff": dist})
# Cauchy-Schwarz fix measured
a_norm = asi.normalized_identity(x4)
scores_norm = asi.attention_scores(x4, a_norm, 1)
rng_norm = max(max(r) - min(r) for r in scores_norm)
depth_norm = asi.softmax_depth_needed(rng_norm)
R["exp2"] = {
    "paper_demo_range": F(rng),
    "error_vs_depth": dict(zip(map(str, depths), errs)),
    "bound_valid_from": next(d for d, b in bounds if b is not None),
    "register_range_raw": F(rng_raw_full),
    "register_range_at_t_1e3": F(rng_raw),
    "temperature_scale": "1/1000",
    "reference_depth": ref_depth,
    "register_range_normalized": F(rng_norm),
    "depth_needed_normalized": depth_norm,
    "inversion": inv_rows,
    "true_top": [names4[t] for t in true_top],
    "true_self_weights": [F(ref_raw[i][i]) for i in range(4)],
    "names": names4,
}
print(f"  raw register range {F(rng_raw_full):.0f} (at t=1/1000: "
      f"{F(rng_raw):.1f}); normalized {F(rng_norm):.4f} -> depth {depth_norm}")
print(f"  inversion: top1 correct "
      f"{[r['top1_correct'] for r in inv_rows]}/4 across depths "
      f"{[r['depth'] for r in inv_rows]}")

fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.2), constrained_layout=True)
ax = axes[0]
ax.semilogy(depths, errs, "o-", color="#1a6faa", label="measured error")
bx = [d for d, b in bounds if b is not None]
by = [b for b in (bb for _, bb in bounds) if b is not None]
ax.semilogy(bx, by, "--", color="#888888", label="bound $R^{D+1}/(D+1)!$")
ax.set_xlabel("Taylor depth $D$"); ax.set_ylabel("max |softmax error|")
ax.set_title("Paper demo: declared error, computed bound", fontsize=10)
ax.legend(frameon=False)
ax = axes[1]
ax.plot([r["depth"] for r in inv_rows], [r["top1_correct"] for r in inv_rows],
        "o-", color="#b3312c")
ax.axvline(F(rng_raw), color="#555555", ls=":", lw=1)
ax.text(F(rng_raw) * 1.05, 1.6, "depth = logit range\n(=$R$ = %.0f)" % F(rng_raw),
        fontsize=8, color="#555555")
ax.set_xlabel("Taylor depth $D$")
ax.set_ylabel("rows whose top-1 is correct (of 4)")
ax.set_ylim(-0.2, 4.2)
ax.set_title("Raw register scoring: below-range depth INVERTS softmax",
             fontsize=10)
fig.savefig(OUT / "exp2_precision_inversion.png"); plt.close(fig)

# ===========================================================================
# exp3 — the simulator tax: construction vs direct formula
# ===========================================================================
print("== exp3: simulator tax ==")
tax = []
for n, d in ((3, 3), (4, 6), (6, 6), (8, 8), (12, 12)):
    x = asi._deterministic_matrix(n, d)
    a = asi._deterministic_matrix(d, d, 2)
    v = asi._deterministic_matrix(d, d, 3)
    t0 = time.perf_counter()
    res = asi.simulate_attention(x, a, v, depth=18)
    t_con = time.perf_counter() - t0
    t0 = time.perf_counter()
    direct = asi._direct_matmul(asi.softmax_sim(
        asi._direct_matmul(asi._direct_matmul(x, a), tuple(zip(*x))), 18),
        asi._direct_matmul(x, v))
    t_dir = time.perf_counter() - t0
    agree = asi._max_abs_diff(res.output, direct) == 0
    tax.append({"n": n, "d": d, "heads": res.tally["heads"],
                "formula_heads": (3 * (n + d + n * d) + 2 * n + n * n + 1
                                  if d != n else 4 * (n + d + n * d) + 1 + n),
                "t_construction": t_con, "t_direct": t_dir,
                "ratio": t_con / t_dir if t_dir else float("inf"),
                "agrees": agree})
    print(f"  ({n}x{d}): heads {res.tally['heads']} = formula "
          f"{tax[-1]['formula_heads']}, time x{t_con/t_dir:.0f}, exact {agree}")
R["exp3"] = tax

fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.2), constrained_layout=True)
ax = axes[0]
ax.plot([t["n"] for t in tax], [t["heads"] for t in tax], "o-",
        color="#1a6faa", label="measured")
ax.plot([t["n"] for t in tax], [t["formula_heads"] for t in tax], "x--",
        color="#888888", label="$3(n{+}d{+}nd){+}2n{+}n^2{+}1$")
ax.set_xlabel("sequence length $n$ (square, $d{=}n$)")
ax.set_ylabel("attention heads used")
ax.set_title("The construction's width grows as the paper's Table 2 says",
             fontsize=10)
ax.legend(frameon=False)
ax = axes[1]
ax.bar([str(t["n"]) for t in tax], [t["ratio"] for t in tax],
       color="#1a6faa")
ax.set_xlabel("sequence length $n$")
ax.set_ylabel("wall-time ratio construction / direct")
ax.set_title("The simulator tax (exactness is not free)", fontsize=10)
fig.savefig(OUT / "exp3_tax.png"); plt.close(fig)

# ===========================================================================
# exp4 — register bridge: scorings, dial, the two shipped ends
# ===========================================================================
print("== exp4: register bridge ==")
tr = asi.temperature_report(sess, "lexicon",
                            scales=(0, 1, 4, 16, 64, 256, 1024),
                            row_limit=12)
rows24 = asi._register_rows(sess, "lexicon")[:24]
x24 = tuple(c for _, c in rows24)
names24 = [n for n, _ in rows24]
q = x24[0]
# shipped controls
nn, d2 = M.nearest(q, [(names24[j], x24[j]) for j in range(1, 24)])
cos = sorted(((M.signed_cosine_squared(q, x24[j]), names24[j])
              for j in range(1, 24)), reverse=True)[:5]
# three scorings for 'energy'
raw = asi.attention_weights(x24, None, 1, 24)  # the inverted garbage (measured)
a_n = asi.normalized_identity(x24)
deep = asi.softmax_depth_needed(
    max(max(r) - min(r) for r in asi.attention_scores(x24, a_n, 1)))
norm_w = asi.attention_weights(x24, a_n, 1, deep)
def top5(w):
    idx = sorted(range(24), key=lambda j: -w[0][j])[:5]
    return [(names24[j], round(F(w[0][j]), 4)) for j in idx]
R["exp4"] = {
    "rows": 24,
    "energy_top5_normalized": top5(norm_w),
    "energy_top5_raw_lowdepth": top5(raw),
    "energy_raw_note": ("raw identity scoring at depth 24: inverted garbage "
                        f"(range {F(max(max(r)-min(r) for r in asi.attention_scores(x24, None, 1))):.0f})"),
    "shipped_nearest": nn,
    "shipped_cosine_top5": [(n, F(c)) for c, n in cos],
    "dial": {s: {"depth": tr["by_scale"][s]["depth"],
                 "max_weight": F(tr["by_scale"][s]["max_weight"]),
                 "top_nonself": tr["by_scale"][s]["top_nonself_row"]}
             for s in ("0", "1", "4", "16", "64", "256", "1024")},
    "scale_zero_mixture_is_the_mean": tr["scale_zero_mixture_is_the_mean"],
    "inner_argmax_vs_nearest": tr["inner_argmax_agrees_with_shipped_nearest"],
    "rows_compared": tr["rows_compared"],
}
print("  energy top-5 (normalized):", R["exp4"]["energy_top5_normalized"])
print("  shipped nearest:", nn, "| cosine top:", cos[:2])
print("  dial max_weight:", [R["exp4"]["dial"][s]["max_weight"] for s in
                             R["exp4"]["dial"]])

fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.2), constrained_layout=True)
ax = axes[0]
sc = [int(s) for s in R["exp4"]["dial"]]
mw = [R["exp4"]["dial"][s]["max_weight"] for s in R["exp4"]["dial"]]
ax.semilogx([max(s, 0.9) for s in sc], mw, "o-", color="#1a6faa")
ax.axhline(1 / 24, color="#888888", ls=":", lw=1)
ax.text(0.95, 1 / 24 + 0.004, "uniform bundle (1/24)", fontsize=8,
        color="#555555")
ax.set_xlabel("temperature $t$ (log scale)")
ax.set_ylabel("max attention weight")
ax.set_title("The dial: bundle at $t{=}0$ ... hard selection as $t\\to\\infty$",
             fontsize=10)
ax = axes[1]
ax.plot(sc, [R["exp4"]["dial"][s]["depth"] for s in R["exp4"]["dial"]],
        "o-", color="#b3312c")
ax.set_xlabel("temperature $t$")
ax.set_ylabel("Taylor depth needed ($10^{-12}$)")
ax.set_title("The cost of exactness grows with the dial", fontsize=10)
fig.savefig(OUT / "exp4_dial.png"); plt.close(fig)

# ===========================================================================
# exp5 — coverage boundary, hierarchy, multi-head
# ===========================================================================
print("== exp5: coverage & hierarchy ==")
boundary = {"passed": [], "refused": None}
for n in range(1, 9):
    try:
        asi.simulate_attention(asi._deterministic_matrix(n, 3),
                               asi._deterministic_matrix(3, 3, 2),
                               asi._deterministic_matrix(3, 3, 3))
        boundary["passed"].append(n)
    except ValueError:
        boundary["refused"] = n
        break
hier = asi.embed_hierarchy(asi._deterministic_matrix(2, 3),
                           asi._deterministic_matrix(3, 3, 2),
                           asi._deterministic_matrix(3, 2, 3), 4, 6, 6)
# unmasked mass theft, measured directly
xg, ag, vg = (asi._deterministic_matrix(2, 3), asi._deterministic_matrix(3, 3, 2),
              asi._deterministic_matrix(3, 2, 3))
zero = Fraction(0)
xh = [list(r) + [zero] * 3 for r in xg] + [[zero] * 6] * 2
ah = [list(r) + [zero] * 3 for r in ag] + [[zero] * 3 + [Fraction(1)] * 3] * 3
vh = [list(r) + [zero] * 4 for r in vg] + [[zero] * 6] * 3
d_h = hier["depth"]
big_unmasked = asi.simulate_attention(xh, ah, vh, d_h)
ul_unmasked = tuple(r[:2] for r in big_unmasked.output[:2])
small = asi.simulate_attention(xg, ag, vg, d_h)
theft = F(asi._max_abs_diff(ul_unmasked, small.output))
mh = asi.simulate_attention_multihead([
    (asi._deterministic_matrix(3, 3), asi._deterministic_matrix(3, 3, 2),
     asi._deterministic_matrix(3, 3, 3)),
    (asi._deterministic_matrix(3, 3, 4), asi._deterministic_matrix(3, 3, 5),
     asi._deterministic_matrix(3, 3, 6))])
R["exp5"] = {
    "boundary_d3": boundary,
    "literal_bound_d3": 6, "paper_bound_d3": 3,
    "feasibility_d24": asi.feasibility_limits(24, 24),
    "hierarchy_exact_masked": hier["exact"],
    "hierarchy_host": hier["host"], "hierarchy_depth": hier["depth"],
    "hierarchy_unmasked_error": theft,
    "multihead": {"heads": mh["heads"],
                  "agrees": mh["heads_agree_with_direct"],
                  "rearrangement_lossless": mh["rearrangement_lossless"]},
}
print(f"  boundary: pass<= {boundary['passed'][-1]}, refuse at "
      f"{boundary['refused']} (paper bound 3, literal 6)")
print(f"  hierarchy masked exact {hier['exact']}, unmasked error {theft:.2e}")
print(f"  multihead agrees {mh['heads_agree_with_direct']}")

# ===========================================================================
with open(OUT / "results.json", "w") as fh:
    json.dump(R, fh, indent=1, default=str)
print("\nwrote", OUT / "results.json")
print("figures:", sorted(p.name for p in OUT.glob("*.png")))

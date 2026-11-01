"""Aggregation-bench experiment suite (drives the repo's sandbox module).

Runs OUTSIDE the GLM package (floats and clocks are allowed HERE, never
inside the package) and produces every figure and number the findings memo
and the study doc quote:

  exp0   validity + shipped endpoints (the dial identities)
  bench  the analogy ground truth: 15 methods x 2 read-outs x 35 items
         (inside bench_report, with the pre-registered winner)
  exp3   the depth audit + the fixed-depth inversion control
  exp4   the dial: every knob swept (max weight, effective support)
  exp5   cost: declared depth, weight bits, mixture bits, wall time
  exp6   winner deep-dive: per-item table, control vs winner vs best-soft
  charts the five figures

By default every stage runs in one shot.  Because the whole suite can
outrun a single session on a slow machine, the suite is also *resumable*:
after every stage the full results state is checkpointed to
``findings/checkpoint.pkl`` and ``findings/results.json`` is refreshed, and
re-invoking the script resumes at the first stage not yet done.  Set
``AGG_STAGES=exp0,bench`` to run a subset explicitly, ``AGG_RESUME=0`` to
start over, and ``AGG_OUT=/path`` to redirect the findings directory.
"""
import json
import os
import pickle
import sys
import time
from fractions import Fraction
from pathlib import Path

# The bench's exact weights can carry thousands of digits (a measured cost,
# recorded as weight_bits in the report; the strings are the honest record).
if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)


def _find_repo() -> Path:
    candidates = []
    env = os.environ.get("GLM_REPO")
    if env:
        candidates.append(Path(env))
    candidates += [Path.cwd(), Path(__file__).resolve().parent,
                   Path(__file__).resolve().parent.parent]
    for c in candidates:
        if (c / "glm_universal" / "sandbox" / "aggregation_bench.py").is_file():
            return c.resolve()
    sys.exit("cannot find the GLM repo (expected glm_universal/sandbox/"
             "aggregation_bench.py). Run from the repository root, or set "
             "GLM_REPO=/path/to/GLM. repo_patch.diff must be applied first.")


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
from glm_universal.sandbox import aggregation_bench as ab

OUT = Path(os.environ.get("AGG_OUT",
                           Path(__file__).resolve().parent / "findings"))
OUT.mkdir(parents=True, exist_ok=True)
print(f"repo: {REPO}")
print(f"out:  {OUT}")
R = {}

FAMILY_COLOR = {  # score space, not provenance
    "inner-product": "#c0392b", "distance": "#1f618d",
    "cosine": "#7d3c98", "rank": "#7f8c8d", "uniform": "#117a65",
}


def family_of(name):
    if name in ("attention_raw", "attention_cs", "linear_attention",
                "power_attention", "sparse_topk", "pade_softmax"):
        return "inner-product"
    if name in ("nearest_weights", "idw", "rbf", "neighbor_mean",
                "exact_bridge", "range_softmax"):
        return "distance"
    if name == "cosine_softmax":
        return "cosine"
    if name == "rank_borda":
        return "rank"
    return "uniform"


def J(x):
    if isinstance(x, Fraction):
        return f"{x.numerator}/{x.denominator}"
    if isinstance(x, dict):
        return {str(k): J(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [J(v) for v in x]
    return x


def F(x):
    return float(x)


# ---------------------------------------------------------------------------
# staging machinery
# ---------------------------------------------------------------------------
STAGES_ENV = os.environ.get("AGG_STAGES", "all").strip()
CKPT = OUT / "checkpoint.pkl"
_state = {"done": [], "R": {}, "live": {}}
if CKPT.is_file() and os.environ.get("AGG_RESUME", "1") == "1":
    with open(CKPT, "rb") as fh:
        _state = pickle.load(fh)
    R.update(_state["R"])
    if _state["done"]:
        print(f"resumed: already done {_state['done']}")

_SESS = None


def _sess():
    global _SESS
    if _SESS is None:
        _SESS = GeometricSession()
    return _SESS


def _want(tag):
    if tag in _state["done"]:
        return False
    if STAGES_ENV == "all":
        return True
    return tag in [t.strip() for t in STAGES_ENV.split(",") if t.strip()]


def _done(tag, **live_objs):
    _state["done"].append(tag)
    _state["R"] = dict(R)
    _state["live"].update(live_objs)
    with open(CKPT, "wb") as fh:
        pickle.dump(_state, fh)
    with open(OUT / "results.json", "w") as fh:
        json.dump(J(R), fh, indent=1, default=str)
    print(f"[checkpoint: {tag} done]")


# live objects, when their stages ran in an earlier invocation
bench = _state["live"].get("bench")
audit = _state["live"].get("audit")
dial = _state["live"].get("dial")
timing = _state["live"].get("timing")

# ===========================================================================
# exp0 -- validity and the shipped endpoints
# ===========================================================================
if _want("exp0"):
    print("== exp0: validity + endpoints ==")
    t0 = time.perf_counter()
    R["exp0"] = J(ab.validity_report())
    R["exp0"]["wall_seconds"] = time.perf_counter() - t0
    print(f"  all_valid={R['exp0']['all_valid']}"
          f"  all_endpoints_hold={R['exp0']['all_endpoints_hold']}")
    for note in R["exp0"]["notes"]:
        print(f"  note: {note}")
    _done("exp0")

# ===========================================================================
# bench -- the analogy ground truth + norm probe + cost + winner
# ===========================================================================
if _want("bench"):
    print("== bench: analogy ground truth + norm probe + cost + winner ==")
    sess = _sess()
    t0 = time.perf_counter()
    bench = ab.bench_report(sess)
    R["bench_wall_seconds"] = time.perf_counter() - t0
    R["bench"] = J(bench)
    methods = bench["methods"]
    nearest_total = bench["nearest_argmax_total"]
    print(f"  control (nearest_weights) argmax total: {nearest_total}")
    rows_print = []
    for name in ab.METHOD_NAMES:
        e = methods[name]
        am = e["analogy_argmax"]["score"]
        mx = e["analogy_mixture"]["score"]
        rows_print.append(
            f"  {name:18s} {e['exactness']} {e['category']:10s} "
            f"argmax={str(am):>6s} mixture={str(mx):>6s} "
            f"norm={str(e['norm']['top1_semantic']):>4s} "
            f"giant={str(e['norm']['top1_giant_capture']):>4s} "
            f"bits={e.get('weight_bits')}")
    print("\n".join(rows_print))
    print(f"  eligible: {bench['eligible']}")
    print(f"  WINNER: {bench['winner']} (incumbent="
          f"{bench['winner_is_incumbent']})")
    print(f"  BEST SOFT: {bench['best_soft_method']}")
    for nm in bench["near_misses"][:8]:
        print(f"    near-miss {nm['method']}: {nm['failed']}")
    _done("bench", bench=bench)

# ===========================================================================
# exp3 -- depth audit + inversion control
# ===========================================================================
if _want("exp3"):
    print("== exp3: depth audit + inversion control ==")
    t0 = time.perf_counter()
    audit = ab.depth_audit(_sess())
    R["exp3"] = J(audit)
    R["exp3"]["wall_seconds"] = time.perf_counter() - t0
    for name, entry in audit["entries"].items():
        if entry.get("range") is not None or entry.get("validity_bound"):
            rng = entry.get("range")
            print(f"  {name:18s} range={F(rng) if rng is not None else '-':>10.3g}"
                  f"  depth={entry.get('depth')}  feasible={entry.get('feasible')}"
                  + (f"  validity={F(entry['validity_bound']):.3g}"
                     if entry.get("validity_bound") else "")
                  + (f"  pade_disagree={F(entry['max_weight_disagreement_vs_4x_reference']):.2e}"
                     if entry.get("max_weight_disagreement_vs_4x_reference")
                     is not None else ""))
    inv = audit["inversion_control"]
    print(f"  inversion control (t=1/1000): top1_correct by depth "
          f"{[(c['depth'], c['top1_correct']) for c in inv['depths']]}")
    print(f"  reproduced={inv['reproduced']}")
    _done("exp3", audit=audit)

# ===========================================================================
# exp4 -- the dial
# ===========================================================================
if _want("exp4"):
    print("== exp4: the dial ==")
    t0 = time.perf_counter()
    dial = ab.dial_report(_sess())
    R["exp4"] = J(dial)
    R["exp4"]["wall_seconds"] = time.perf_counter() - t0
    for name, d in dial["dials"].items():
        pts = []
        for c in d["curve"]:
            if "refusal" in c:
                pts.append(f"{c['value']}:refused")
            else:
                pts.append(f"{c['value']}:ipr={F(c['ipr']):.3g}")
        print(f"  {name:18s} ({d['param']})  " + "  ".join(pts))
    _done("exp4", dial=dial)

# ===========================================================================
# exp5 -- wall time (harness clocks; bits/depth came with the bench)
# ===========================================================================
if _want("exp5"):
    print("== exp5: wall time per method (lexicon register) ==")
    rows_reg, query_reg = ab._register_rows(_sess(), "lexicon")
    timing = {}
    for name in ab.METHOD_NAMES:
        t0 = time.perf_counter()
        try:
            ab.METHODS[name].weights(query_reg, rows_reg)
            timing[name] = {"seconds": time.perf_counter() - t0, "at": "default"}
        except (ab.RefusalError, ValueError) as exc:
            if "t" in ab.METHODS[name].defaults:
                t0 = time.perf_counter()
                try:
                    ab.METHODS[name].weights(query_reg, rows_reg,
                                             t=Fraction(1, 1000))
                    timing[name] = {"seconds": time.perf_counter() - t0,
                                    "at": "t=1/1000 (default refused)",
                                    "default_refusal": str(exc)[:90]}
                    continue
                except (ab.RefusalError, ValueError):
                    pass
            timing[name] = {"seconds": None, "at": "refused",
                            "refusal": str(exc)[:90]}
    R["exp5_timing"] = {k: J(v) for k, v in timing.items()}
    for name, t in timing.items():
        sec = f"{t['seconds']:.3f}s" if t["seconds"] is not None else "refused"
        print(f"  {name:18s} {sec:10s} {t['at']}")
    _done("exp5", timing=timing)

# ===========================================================================
# exp6 -- winner deep-dive: per-item table
# ===========================================================================
if _want("exp6"):
    print("== exp6: winner deep-dive ==")
    best_soft = (bench or {}).get("best_soft_method")
    focus = [n for n in ("nearest_weights", best_soft,
                         "idw", "neighbor_mean") if n]
    R["exp6"] = R.get("exp6", {})
    for name in dict.fromkeys(focus):
        r = ab.analogy_suite(_sess(), name, "mixture")
        R["exp6"][name] = J(r)
        diff = sum(1 for it in r["items"]
                   if it.get("observed") is not None
                   and it.get("passed") is not None and not it["passed"])
        print(f"  {name:18s} mixture total="
              f"{r['total']['passed']}/{r['total']['total']} "
              f"wrong={diff}")
    _done("exp6")

# ===========================================================================
# charts
# ===========================================================================
if _want("charts"):
    print("== charts ==")
    assert bench is not None, "charts needs the bench stage (run AGG_STAGES=all or bench first)"
    methods = bench["methods"]
    nearest_total = bench["nearest_argmax_total"]
    names = list(ab.METHOD_NAMES)
    y = list(range(len(names)))

    # chart 1: analogy accuracy, both read-outs
    fig, ax = plt.subplots(figsize=(9.2, 4.6), constrained_layout=True)
    am = [F(methods[n]["analogy_argmax"]["score"] or 0) for n in names]
    mx = [F(methods[n]["analogy_mixture"]["score"] or 0) for n in names]
    ax.barh([v + 0.2 for v in y], am, height=0.38,
            color="#1f618d", label="argmax read-out (selection)")
    ax.barh([v - 0.2 for v in y], mx, height=0.38,
            color="#e59866", label="mixture read-out (decoded)")
    ax.axvline(F(nearest_total), color="k", lw=1.0, ls="--",
               label=f"shipped selector control ({F(nearest_total):.2f})")
    for i, n in enumerate(names):
        if n == bench["winner"]:
            ax.text(-0.012, i, "*", va="center", ha="right", fontsize=13,
                    color="#b7950b", transform=ax.get_yaxis_transform())
        if n == bench["best_soft_method"]:
            ax.text(-0.012, i, "o", va="center", ha="right", fontsize=11,
                    color="#b7950b", transform=ax.get_yaxis_transform())
    ax.set_yticks(y)
    ax.set_yticklabels([f"{n} ({ab.METHODS[n].exactness})" for n in names],
                       fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("fraction of 35 ground-truth analogy items correct")
    ax.set_title("The pile on the analogy ground truth\n"
                 "* pre-registered winner   o best soft method")
    ax.legend(loc="lower right", fontsize=8)
    fig.savefig(OUT / "exp1_analogy.png")
    plt.close(fig)

    # chart 2: the norm probe
    fig, ax = plt.subplots(figsize=(9.2, 4.4), constrained_layout=True)
    sem = [F(methods[n]["norm"]["top1_semantic"]) for n in names]
    gia = [F(methods[n]["norm"]["top1_giant_capture"]) for n in names]
    ax.barh([v + 0.2 for v in y], sem, height=0.38, color="#1e8449",
            label="top-1 = semantic direction (recovery)")
    ax.barh([v - 0.2 for v in y], gia, height=0.38, color="#c0392b",
            label="top-1 = giant decoy (capture)")
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("fraction of 8 planted queries")
    ax.set_title("The norm-domination probe: meaning or mass?\n"
                 "eight orthogonal directions, radii 1-512, four giants at 10^6")
    ax.legend(loc="lower right", fontsize=8)
    fig.savefig(OUT / "exp2_norm.png")
    plt.close(fig)

    assert audit is not None, "charts needs the exp3 stage"
    inv = audit["inversion_control"]

    # chart 3: depth vs range + the inversion control
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 4.2),
                                   constrained_layout=True)
    for name, entry in audit["entries"].items():
        if entry.get("range") is None:
            continue
        feasible = entry.get("feasible")
        ax1.plot(F(entry["range"]), entry.get("depth", 512) if not feasible
                 else entry["depth"], "o", ms=7,
                 color=FAMILY_COLOR[family_of(name)],
                 markeredgecolor="k" if not feasible else "none", mew=1.2,
                 label=None)
        ax1.annotate(name, (F(entry["range"]), entry.get("depth", 512)),
                     fontsize=7, xytext=(4, 3), textcoords="offset points")
    ax1.set_xlabel("measured exponent range (lexicon register)")
    ax1.set_ylabel("computed depth (target 1e-30, budget 512)")
    ax1.set_title("exactness priced in depth")
    ax1.axhline(512, color="#c0392b", lw=0.8, ls="--")
    ax1.text(0.02, 520, "declared budget", color="#c0392b", fontsize=7)
    depths = [c["depth"] for c in inv["depths"]]
    corr = [c["top1_correct"] for c in inv["depths"]]
    ax2.plot(depths, corr, "o-", color="#c0392b", ms=4)
    ax2.set_xlabel("FIXED Taylor depth (not computed)")
    ax2.set_ylabel("top-1 correct (of 4)")
    ax2.set_title("the inversion control: depth < range\ninverts the softmax")
    ax2.set_ylim(-0.2, 4.4)
    fig.savefig(OUT / "exp3_depth_inversion.png")
    plt.close(fig)

    assert dial is not None, "charts needs the exp4 stage"

    # chart 4: the dial -- effective support vs knob
    fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.6),
                             constrained_layout=True)
    shown = 0
    for name, d in dial["dials"].items():
        xs, ys = [], []
        for c in d["curve"]:
            if "refusal" in c:
                continue
            xs.append(F(c["value"]))
            ys.append(F(c["ipr"]))
        if not xs:
            continue
        axp = axes[shown % 3]
        axp.plot(xs, ys, "o-", ms=4, color=FAMILY_COLOR[family_of(name)],
                 label=name)
        axp.set_xscale("log")
        axp.set_title({"t": "temperature knobs", "p": "power family",
                       "k": "neighborhood / sparsity",
                       "alpha": "Shepard exponent",
                       "lam": "the exact bridge"}.get(d["param"], d["param"]),
                      fontsize=9)
        axp.set_xlabel(d["param"])
        axp.legend(fontsize=7)
        shown += 1
    for axp in axes:
        axp.set_yscale("log")
        axp.set_ylabel("effective support (1/sum w^2)")
    fig.suptitle("Every dial, swept: effective support between 1 (hard) "
                 "and n (bundle)", fontsize=10)
    fig.savefig(OUT / "exp4_dial.png")
    plt.close(fig)

    # chart 5: cost vs payoff
    fig, ax = plt.subplots(figsize=(8.6, 4.6), constrained_layout=True)
    for name in names:
        e = methods[name]
        bits = e.get("weight_bits")
        score = e["analogy_mixture"]["score"]
        if bits is None or score is None:
            continue
        ax.scatter(F(bits), F(score), s=64,
                   color=FAMILY_COLOR[family_of(name)],
                   marker={"E0": "o", "E1": "^", "E2": "s"}[e["exactness"]],
                   edgecolors="k", linewidths=0.5, zorder=3)
        ax.annotate(f"{name}({e['exactness']})", (F(bits), F(score)),
                    fontsize=6.5, xytext=(5, 4), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_xlabel("weight bits (exactness priced in integer growth)")
    ax.set_ylabel("mixture read-out score (35 items)")
    ax.set_title("The substrate's trade: exactness cost vs semantic payoff\n"
                 "o E0 exact   ^ E1 declared depth   square E2 Pade")
    fig.savefig(OUT / "exp5_cost_payoff.png")
    plt.close(fig)

    figures = ["exp1_analogy.png", "exp2_norm.png",
               "exp3_depth_inversion.png", "exp4_dial.png",
               "exp5_cost_payoff.png"]
    R["figures"] = figures
    _done("charts")

# ===========================================================================
# final meta
# ===========================================================================
if _want("final") and bench is not None:
    R["meta"] = {
        "repo": str(REPO), "methods": len(ab.METHOD_NAMES),
        "winner": bench["winner"],
        "winner_is_incumbent": bench["winner_is_incumbent"],
        "best_soft_method": bench["best_soft_method"],
        "nearest_argmax_total": J(bench["nearest_argmax_total"]),
    }
    with open(OUT / "results.json", "w") as fh:
        json.dump(J(R), fh, indent=1, default=str)
    _done("final")
    print(f"wrote {OUT / 'results.json'}")
    print(f"figures: {R.get('figures')}")
    print(f"bench wall seconds: {R.get('bench_wall_seconds'):.0f}")

print(f"stages complete: {_state['done']}")

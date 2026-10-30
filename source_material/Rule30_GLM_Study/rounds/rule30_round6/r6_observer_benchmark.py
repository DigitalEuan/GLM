"""Round 6: frozen observer benchmark (feedback #3, section 3).

Every predictor is causal: it guesses bit t from bits < t.  Predictors with
trainable tables are fitted on the TRAIN segment and then FROZEN; accuracy is
reported on two later, disjoint TEST segments.  Each sequence is labelled with
what is *proved* about it in the Lean package, so that "no pattern found at
this budget" is never confused with "pattern excluded by proof".

Predictor classes (the rule-space ladder of `RuleSpace.lean`):
  const-1, const-0                 one-rule spaces            (P2 = typicality for const-1)
  lag-p, 1 <= p <= 64              lag rules                  (P1 = escape from all lag rules)
  ctx-k, 1 <= k <= 16 (frozen)     finite-state, 2^k states   (SeedFSTypical = typicality here)
  golay-24 (GLM substrate)         finite-state, 2^23 states: guess the bit that puts the last
                                   24 bits closer to the binary Golay code (GLM coset weight)
  wobble-arrow                     counter rule (unbounded state): guess 1 iff D(t) <= 0
  online-ctx-12                    counter rule: context table keeps updating on test data

Output: r6_observer_benchmark.json and r6_observer_benchmark.md
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import r6_common as C

HERE = Path(__file__).resolve().parent
import os
# unzip glm_repo.zip somewhere and point GLM_OVERLAY at its  directory
GLM_OVERLAY = Path(os.environ.get("GLM_OVERLAY", "/tmp/glm/glm_repo/overlay"))


def load_golay_coset_weight():
    """Import the GLM substrate's Golay decoder without running the GLM package __init__
    (the uploaded archive lacks the runtime front-end modules parser/session/tct_engine)."""
    import importlib
    import types
    root = GLM_OVERLAY / "glm_universal"
    if not root.exists():
        return None
    pkg = types.ModuleType("glm_universal")
    pkg.__path__ = [str(root)]
    sys.modules.setdefault("glm_universal", pkg)
    mod = importlib.import_module("glm_universal.substrate.golay_decode")
    return mod.coset_weight


def accuracy(hits: int, n: int) -> dict:
    z = (hits - n / 2) / math.sqrt(n / 4) if n else 0.0
    return {"hits": hits, "n": n, "acc": round(hits / n, 6) if n else None, "z": round(z, 3)}


def eval_static(seq, pred_fn, lo, hi):
    hits = 0
    for t in range(lo, hi):
        hits += pred_fn(seq, t) == seq[t]
    return hits


def train_ctx(seq, k, lo, hi):
    table = {}
    for t in range(max(lo, k), hi):
        ctx = tuple(seq[t - k:t])
        c = table.setdefault(ctx, [0, 0])
        c[seq[t]] += 1
    return {ctx: (1 if c[1] >= c[0] else 0) for ctx, c in table.items()}


def run_sequence(name, seq, golay_cw, budgets):
    N = len(seq)
    tr = (0, N // 2)
    te = [(N // 2, (3 * N) // 4), ((3 * N) // 4, N)]
    res = {}

    def record(label, cls, states, fn_list):
        res[label] = {"class": cls, "states": states,
                      "test": [accuracy(h, hi - lo) for h, (lo, hi) in zip(fn_list, te)]}

    record("const-1", "one-rule", 1, [eval_static(seq, lambda s, t: 1, lo, hi) for lo, hi in te])
    record("const-0", "one-rule", 1, [eval_static(seq, lambda s, t: 0, lo, hi) for lo, hi in te])
    for p in range(1, budgets["lag"] + 1):
        record(f"lag-{p}", "lag", p,
               [eval_static(seq, lambda s, t, p=p: s[t - p], lo, hi) for lo, hi in te])
    for k in range(1, budgets["ctx"] + 1):
        tab = train_ctx(seq, k, *tr)
        record(f"ctx-{k}", "finite-state", 2 ** k,
               [eval_static(seq, lambda s, t, k=k, tab=tab: tab.get(tuple(s[t - k:t]), 1), lo, hi)
                for lo, hi in te])
    if golay_cw is not None:
        def golay_pred(s, t):
            w = 0
            for b in s[t - 23:t]:
                w = (w << 1) | b
            w1, w0 = golay_cw((w << 1) | 1), golay_cw(w << 1)
            return 1 if w1 <= w0 else 0
        record("golay-24", "finite-state (GLM substrate)", 2 ** 23,
               [eval_static(seq, golay_pred, lo, hi) for lo, hi in te])
    # wobble arrow (counter rule)
    D = [0]
    for b in seq:
        D.append(D[-1] + (1 if b else -1))
    record("wobble-arrow", "counter", "unbounded",
           [eval_static(seq, lambda s, t: 1 if D[t] <= 0 else 0, lo, hi) for lo, hi in te])
    # online context-12 (keeps learning on test data)
    k = 12
    counts = {}
    hits_seg = []
    for t in range(k, N):
        ctx = tuple(seq[t - k:t])
        c = counts.setdefault(ctx, [0, 0])
        guess = 1 if c[1] >= c[0] else 0
        if t == te[0][0] or t == te[1][0]:
            hits_seg.append(0)
        if t >= te[0][0]:
            hits_seg[-1] += guess == seq[t]
        c[seq[t]] += 1
    record("online-ctx-12", "counter", "unbounded", hits_seg)

    best = max(((lab, r["test"][1]["acc"]) for lab, r in res.items()), key=lambda x: x[1])
    worst_lag = max(((lab, r["test"][1]["acc"]) for lab, r in res.items()
                     if r["class"] == "lag"), key=lambda x: x[1])
    return {"name": name, "N": N, "train": tr, "test": te, "predictors": res,
            "best_on_test2": best, "best_lag_on_test2": worst_lag}


PROOF_LABELS = {
    "rule30-centre": "OPEN: P1 and P2 unproved. Lean proves only finite facts (no eventual period "
                     "p <= 1000 starting <= 1000; exact wobble values to 10^6) and the equivalences "
                     "P1 <=> escape from lag rules <=> escape from finite-state rules.",
    "periodic-7": "FORMAL (trivial): eventually periodic, captured by lag-7.",
    "biased-1/3": "FORMAL: frequency 1/3 (Lean `exists_row_with_biased_column` uses this column).",
    "champernowne": "Known theorem (not in this package): normal in base 2.",
    "sha256-counter": "A fixed rule (hash in counter mode); nothing proved here.",
    "rightwhite-row-periodic": "FORMAL: a right-white Rule 30 row with centre column 1,0,1,0,... "
                               "(`exists_row_with_periodic_column`); captured by lag-2.",
    "rightwhite-row-biased": "FORMAL: a right-white Rule 30 row with centre column of frequency 1/3 "
                             "(`exists_row_with_biased_column`).",
}


def main():
    t0 = time.time()
    golay_cw = load_golay_coset_weight()
    N_long = 1 << 17
    N_short = 4096
    print("generating sequences ...", flush=True)
    seqs = {
        "rule30-centre": C.centre_column(N_long),
        "periodic-7": C.periodic(N_long),
        "biased-1/3": C.biased_third(N_long),
        "champernowne": C.champernowne_binary(N_long),
        "sha256-counter": C.sha256_stream(N_long),
    }
    print("building right-white rows by column inversion ...", flush=True)
    row_p = C.column_inverse_row([1 - (t % 2) for t in range(N_short)])
    row_b = C.column_inverse_row([1 if t % 3 == 0 else 0 for t in range(N_short)])
    col_p = C.column_of_row(row_p, N_short)
    col_b = C.column_of_row(row_b, N_short)
    assert col_p == [1 - (t % 2) for t in range(N_short)]
    assert col_b == [1 if t % 3 == 0 else 0 for t in range(N_short)]
    seqs["rightwhite-row-periodic"] = col_p
    seqs["rightwhite-row-biased"] = col_b
    # the rows themselves look 'noisy': report their densities
    dens_p = sum(row_p.values()) / len(row_p)
    dens_b = sum(row_b.values()) / len(row_b)
    budgets = {"lag": 64, "ctx": 16}
    out = {"budgets": budgets, "golay_observer_available": golay_cw is not None,
           "rightwhite_row_densities": {"periodic": dens_p, "biased": dens_b},
           "results": {}}
    for name, s in seqs.items():
        print("evaluating", name, len(s), flush=True)
        r = run_sequence(name, s, golay_cw, budgets)
        r["proof_label"] = PROOF_LABELS[name]
        out["results"][name] = r
        # short-horizon version of the centre column for a like-for-like comparison
    out["results"]["rule30-centre-4096"] = run_sequence("rule30-centre-4096",
                                                         seqs["rule30-centre"][:N_short],
                                                         golay_cw, budgets)
    out["results"]["rule30-centre-4096"]["proof_label"] = PROOF_LABELS["rule30-centre"]
    out["seconds"] = round(time.time() - t0, 1)
    (HERE / "r6_observer_benchmark.json").write_text(json.dumps(out, indent=1))
    lines = ["# Round 6 observer benchmark (frozen predictors, disjoint test segments)", "",
             "Evidence class of every number below: **EMP** (finite computation outside Lean).",
             "A high accuracy is a *captured pattern*; an accuracy near 1/2 is only "
             "*no pattern found at this budget*, never a proof of escape.", "",
             "| sequence | N | best predictor (test 2) | acc | best lag | acc | const-1 acc | "
             "golay-24 acc | wobble-arrow acc | proof status |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in out["results"].items():
        P = r["predictors"]
        g = P.get("golay-24", {"test": [{}, {"acc": None}]})["test"][1]["acc"]
        lines.append(f"| {name} | {r['N']} | {r['best_on_test2'][0]} | {r['best_on_test2'][1]} | "
                     f"{r['best_lag_on_test2'][0]} | {r['best_lag_on_test2'][1]} | "
                     f"{P['const-1']['test'][1]['acc']} | {g} | "
                     f"{P['wobble-arrow']['test'][1]['acc']} | {r['proof_label']} |")
    lines += ["", f"Right-white rows built by column inversion have black-cell density "
              f"{dens_p:.3f} (periodic column) and {dens_b:.3f} (biased column): the rows look "
              "like noise while their centre columns are captured by tiny rules.", "",
              f"Budgets: lag p <= {budgets['lag']}, context order k <= {budgets['ctx']}. "
              f"Run time {out['seconds']} s."]
    (HERE / "r6_observer_benchmark.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

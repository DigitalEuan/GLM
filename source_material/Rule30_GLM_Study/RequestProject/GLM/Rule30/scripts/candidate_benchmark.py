#!/usr/bin/env python3
"""Round 27 (GLM prototype, outside Lean): measuring candidate generation (To Do 18).

The Round 26 loop (`conjecture_loop.py`) mixed candidates supplied by the developers with
candidates the loop produced.  This harness separates them and measures strategies under one
budget and one counterexample interface.

* **Candidate record** -- every candidate carries: statement, exact quantifiers, origin
  (supplied / generated / repaired / analogy), target implication, smallest known counterexample,
  tested range, formal status, and verification cost (machine steps simulated).
* **Frozen grammar** -- four families over the driven half-line machine of a drive word:
    LIN(a,b)    every code of length d first fails by a*d + b
    AMORT(c,e)  alive codes of length d at time d-1+m are at most 2^(d-1+e-floor(m/c))
    WS(b)       Lmax(d+2) <= Lmax(d) + b           (width step)
    RANK(i,c)   potential i of ProofRoutesData.rankPot drops over every surviving post-edge
                window of c steps
  Each family implies the target for its word by a Lean theorem (`halfLineDies_of_linear`,
  `halfLineDies_of_amortized`, `wordDies_of_widthStep`, `wordDies_of_ranking`), recorded as the
  candidate's target implication.  No candidate is *proved* by this script: survival at range D
  is evidence only (`ConjectureLoop.no_finite_confirmation`).
* **Strategies**, same budget (number of oracle calls) and same oracle:
    enumerate   fixed lexicographic order over the grammar
    repair      counterexample-guided: on failure, move the parameter just far enough to absorb
                the counterexample (the smallest repair), then re-test
    glm         plug-in for GLM-guided selection: a JSON file of proposals (statement keys in the
                grammar), consumed in order; NOT run here -- the GLM is not part of this package
* **Tasks**: training word `10` (period 2); held-out words `100`, `110` (period 3) and `1000`,
  `1100`, `1110` (period 4).  Candidates surviving training are re-tested on held-out words.

Metrics per strategy: invalid claims rejected (with smallest counterexample), candidates
surviving at the range, surviving candidates whose target implication is proved in Lean, tightest
survivor per family, transfer rate to held-out words, total oracle work (elementary checks).

Usage: python3 candidate_benchmark.py [D] [BUDGET] [--glm proposals.json]   (defaults 18, 60)
"""
import json, sys

COST = [0]
def step(b, S): COST[0] += 1; return (S >> 1) ^ (S | ((S << 1) | b))
def drive(p, k): return lambda t: (k >> (t % p)) & 1

def life(S, bd, cap=10**4):
    t = 0
    while t < cap:
        if bd(t) and (S & 1) == bd(t + 1): return t
        S = step(bd(t), S); t += 1
    return None

class Task:
    """lives of all codes alive at the edge, lengths 1..D, for one drive word"""
    def __init__(self, name, p, k, D):
        self.name, self.bd, self.D = name, drive(p, k), D
        self.lives = {}
        for d in range(1, D + 1):
            out = []
            def pf(P, kk):
                X = P
                for t in range(kk):
                    if self.bd(t) and (X & 1) == self.bd(t + 1): return True
                    X = step(self.bd(t), X)
                return False
            def dfs(kk, P):
                if pf(P, kk): return
                if kk == d - 1: out.append(P | (1 << kk)); return
                dfs(kk + 1, P); dfs(kk + 1, P | (1 << kk))
            dfs(0, 0)
            self.lives[d] = {S: life(S, self.bd) for S in out}
        self.lmax = {d: max(v.values()) if v else d - 2 for d, v in self.lives.items()}

POT = [
    lambda X, t: X.bit_length(),
    lambda X, t: bin(X).count('1'),
    lambda X, t: bin(X ^ (X >> 1)).count('1'),
    lambda X, t: next(i for i in range(X.bit_length() + 1) if not (X >> i) & 1),
    lambda X, t: next(i for i in range(X.bit_length() + 1) if not (X >> i) & 1 and not (X >> (i + 1)) & 1),
    lambda X, t: X.bit_length() - bin(X).count('1'),
    lambda X, t: bin(X % (1 << max(X.bit_length() - t, 0))).count('1'),
    lambda X, t: next(n for n in range(1, X.bit_length() + 2) if ((X >> n) & 1) == ((X >> (n - 1)) & 1)),
]

WORK = [0]

def oracle(cand, task):
    """returns (holds_on_range, smallest_counterexample, repair_hint); WORK counts the
    elementary checks performed (one per length, per (length, time) pair, or per machine step)"""
    fam, a, b = cand
    if fam == "LIN":
        for d in range(1, task.D + 1):
            WORK[0] += 1
            if task.lmax[d] + 1 > a * d + b:          # first failure time must be <= a*d+b
                return False, (d, task.lmax[d]), task.lmax[d] + 1 - a * d
        return True, None, None
    if fam == "AMORT":
        c, e = a, b
        for d in range(1, task.D + 1):
            for m in range(0, task.lmax[d] - d + 3):
                WORK[0] += len(task.lives[d])
                n = sum(1 for L in task.lives[d].values() if L >= d - 1 + m)
                if n * 2 ** (m // c) > 2 ** (d - 1 + e):
                    need = 0
                    while n * 2 ** (m // c) > 2 ** (d - 1 + e + need): need += 1
                    return False, (d, m, n), e + need
        return True, None, None
    if fam == "WS":
        for d in range(1, task.D - 1):
            WORK[0] += 1
            if task.lmax[d + 2] > task.lmax[d] + b:
                return False, (d, task.lmax[d], task.lmax[d + 2]), task.lmax[d + 2] - task.lmax[d]
        return True, None, None
    if fam == "RANK":
        i, c = a, b
        windows = 0
        for d in range(1, task.D + 1):
            for S, L in sorted(task.lives[d].items()):
                X = S; tr = []
                for t in range(L + 1): tr.append(X); X = step(task.bd(t), X)
                WORK[0] += L + 1
                for t in range(d - 1, L - c + 1):
                    windows += 1
                    if POT[i](tr[t + c], t + c) >= POT[i](tr[t], t):
                        return False, (d, S, t), None
        return True, ("vacuous: no surviving window of this length in range" if windows == 0 else None), None

LEAN_IMPLIES = {"LIN": "halfLineDies_of_linear", "AMORT": "halfLineDies_of_amortized",
                "WS": "wordDies_of_widthStep", "RANK": "wordDies_of_ranking"}

def statement(c):
    f, a, b = c
    return {"LIN": f"forall d S (len S = d): first failure <= {a}*d + {b}",
            "AMORT": f"forall d m: #alive(d, d-1+m) * 2^floor(m/{a}) <= 2^(d-1+{b})",
            "WS": f"forall d: Lmax(d+2) <= Lmax(d) + {b}",
            "RANK": f"potential {a} drops over every surviving post-edge window of {b} steps"}[f]

GRAMMAR = ([("LIN", a, b) for a in range(1, 7) for b in range(0, 41, 4)] +
           [("AMORT", c, e) for c in range(1, 7) for e in range(0, 4)] +
           [("WS", 0, b) for b in range(0, 41, 2)] +
           [("RANK", i, c) for i in range(8) for c in (1, 2, 4, 8)])
SUPPLIED = [("LIN", 2, 9), ("AMORT", 4, 1), ("WS", 0, 12), ("RANK", 1, 2)]   # developer seeds

def record(c, origin, task, ok, cex, cost):
    return {"statement": statement(c), "key": list(c), "origin": origin,
            "quantifiers": "for all code lengths d >= 1 and codes of length d" if c[0] != "WS" else "for all d >= 1",
            "target": f"WordDies({task.name}) via {LEAN_IMPLIES[c[0]]}",
            "smallest_counterexample": cex, "tested_range": f"d <= {task.D}",
            "formal_status": "refuted (finite counterexample)" if not ok else
                ("OPEN (vacuous on the range)" if cex else "OPEN (survives the range; not proved)"),
            "cost_work": cost}

def run(strategy, task, budget, proposals=None):
    recs, tried = [], set()
    queue = list(SUPPLIED) if strategy != "glm" else []
    origin = {c: "supplied" for c in queue}
    if strategy == "enumerate":
        for c in GRAMMAR: origin.setdefault(c, "generated"); queue.append(c)
    elif strategy == "glm":
        for c in proposals or []: c = tuple(c); origin.setdefault(c, "generated"); queue.append(c)
    calls = 0
    while queue and calls < budget:
        c = queue.pop(0)
        if c in tried: continue
        tried.add(c); calls += 1
        before = WORK[0]
        ok, cex, hint = oracle(c, task)
        recs.append(record(c, origin.get(c, "generated"), task, ok, cex, WORK[0] - before))
        if strategy == "repair" and not ok:
            f, a, b = c
            if f in ("LIN", "WS", "AMORT") and hint is not None:
                r = (f, a, max(hint, b + 1))
            elif f == "RANK":
                r = (f, (a + 1) % 8, b) if a < 7 else (f, 0, b * 2)
            else:
                r = None
            if r and r not in tried:
                origin.setdefault(r, "repaired"); queue.insert(0, r)
        if strategy == "repair" and not queue:
            # exhausted repairs: fall back to the next grammar element not yet tried
            nxt = next((g for g in GRAMMAR if g not in tried), None)
            if nxt: origin.setdefault(nxt, "generated"); queue.append(nxt)
    return recs

def summarize(name, recs, held):
    surv = [r for r in recs if r["formal_status"].startswith("OPEN")]
    rej = [r for r in recs if r["formal_status"].startswith("refuted")]
    # non-dominated survivors: no other survivor of the same family is at least as strong
    def stronger(x, y):
        return x[0] == y[0] and x != y and (
            (x[0] in ("LIN", "AMORT") and x[1] <= y[1] and x[2] <= y[2]) or
            (x[0] == "WS" and x[2] <= y[2]) or (x[0] == "RANK" and x[1] == y[1] and x[2] <= y[2]))
    keys = [tuple(r["key"]) for r in surv if "vacuous" not in r["formal_status"]]
    vac = [tuple(r["key"]) for r in surv if "vacuous" in r["formal_status"]]
    frontier = [k for k in keys if not any(stronger(o, k) for o in keys)]
    tight = {}
    for r in surv:
        f, a, b = r["key"]
        if f in ("LIN", "AMORT"): tight[(f, a)] = min(tight.get((f, a), 10**9), b)
        if f == "WS": tight[("WS",)] = min(tight.get(("WS",), 10**9), b)
    transfer = []
    for r in surv:
        c = tuple(r["key"])
        res = [oracle(c, t)[0] for t in held]
        transfer.append(all(res))
    cost = sum(r["cost_work"] for r in recs)
    by_origin = {}
    for r in surv: by_origin[r["origin"]] = by_origin.get(r["origin"], 0) + 1
    print(f"\n[{name}] oracle calls={len(recs)} rejected={len(rej)} surviving={len(surv)} "
          f"(by origin {by_origin}) non-dominated={len(frontier)} "
          f"transfer-to-held-out={sum(transfer)}/{len(transfer)} work={cost}")
    print("   non-dominated survivors (each implies the target by a Lean theorem; none proved):",
          sorted(frontier))
    if vac: print("   vacuous survivors (untested at this range, no credit):", sorted(vac))
    print("   tightest survivors:", {k: v for k, v in sorted(tight.items())})
    for r in rej[:5]:
        print("   rejected:", r["statement"], "| origin", r["origin"], "| cex", r["smallest_counterexample"])

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    D = int(args[0]) if args else 18
    budget = int(args[1]) if len(args) > 1 else 60
    proposals = None
    if "--glm" in sys.argv:
        proposals = json.load(open(sys.argv[sys.argv.index("--glm") + 1]))
    train = Task("word 10", 2, 1, D)
    held = [Task("word 100", 3, 1, D), Task("word 110", 3, 3, D),
            Task("word 1000", 4, 1, D), Task("word 1100", 4, 3, D), Task("word 1110", 4, 7, D)]
    print(f"training task: drive word 10, d <= {D}; held-out: words 100, 110, 1000, 1100, 1110")
    print("Lmax (training):", [train.lmax[d] for d in range(1, D + 1)])
    for strat in ("enumerate", "repair") + (("glm",) if proposals is not None else ()):
        recs = run(strat, train, budget, proposals)
        summarize(strat, recs, held)
        with open(f"candidate_records_{strat}.json", "w") as fh:
            json.dump(recs, fh, indent=1)
    if proposals is None:
        print("\n[glm] not run: pass --glm proposals.json (a list of [family, a, b]) to measure "
              "GLM-guided selection under the same budget and oracle.")

if __name__ == "__main__":
    main()

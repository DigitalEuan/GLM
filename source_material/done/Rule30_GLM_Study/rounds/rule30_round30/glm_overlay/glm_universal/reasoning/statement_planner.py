"""``glm_universal.reasoning.statement_planner`` -- Round 30, stage 4: the planner over
*statements* (To Do 25, closing the generation gap of To Do 18).

The grid planner searches chains of steps with a fitted last step and answers under the
agreement rule.  The same machinery generates candidate **statements** for the Rule 30 study:

=====================  ==========================  ==========================================
grid planner           statement planner           Lean
=====================  ==========================  ==========================================
state (a grid)         a statement family member   ``HalfLineLinear p a b``,
                       ``LIN(p, a, .)``,           ``AmortizedHalving p c e``
                       ``AMORT(p, c, .)``
fixed step             ``steeper`` (a+1 / c+1),    weakening; ``halfLineLinear_of_amortized``
                       ``implies`` (AMORT -> LIN), (a proved implication); analogy is a
                       ``analogy`` (p -> p+1)      proposal only (``analogy_transport_unsound``)
fitted finisher        the least offset that       ``Conjecture.narrow`` (the least surviving
                       survives every training     parameter; ``narrow_le_of_holds``: never
                       level (``narrow``)          above a true one)
demonstrations         levels d <= D_train         the finite checks ``prefixCheck``,
                                                   ``amortCheck`` (``native_decide``)
merging (signature)    equal verdicts on every     ``Conjecture.Junction``
                       probe level (a junction)
hard gate              the level checks; the       ``PipelineData.lean``: survival to ``D`` (CERT)
                       final frontier is           and refutation of offset - 1 (a witness,
                       certified in Lean           FORMAL), so every fitted offset is sharp
=====================  ==========================  ==========================================

Run as a script it writes ``statement_frontier.json`` (read by ``emit_lean.py``) and prints the
frontier per period, the Occam measurement for statements (does the offset fitted on ``D_train``
levels survive the held-out levels?), and the comparison with the Round 27 strategies under the
same oracle and budget (``candidate_benchmark.py``).
"""
from __future__ import annotations

import json
import os
import sys
from typing import Dict, List, Optional, Tuple

try:  # inside the GLM
    from . import candidate_benchmark as cb
except ImportError:  # stand-alone (study folder)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import candidate_benchmark as cb  # type: ignore  # noqa: E402


class PeriodData:
    """The level data of one period: for every non-zero drive word ``k < 2^p`` and code length
    ``d <= D``, the lives of the codes alive at the edge (``candidate_benchmark.Task``)."""

    def __init__(self, p: int, D: int):
        self.p, self.D = p, D
        self.tasks = {k: cb.Task("p%d k%d" % (p, k), p, k, D) for k in range(1, 2 ** p)}

    def lmax(self, d: int) -> Tuple[int, int, Optional[int]]:
        """The longest life at length ``d`` over all words: (life, word, code)."""
        best = (d - 2, 0, None)
        for k, t in self.tasks.items():
            for S, L in t.lives[d].items():
                if L is not None and (L, -k, -S) > (best[0], -best[1], -(best[2] or 0)):
                    best = (L, k, S)
        return best

    # ---- the fitted finishers ----------------------------------------------------------------

    def fit_lin(self, a: int, D: int):
        """Least ``b`` with every code of every length ``d <= D`` failing before ``a d + b``;
        and the witness refuting ``b - 1`` (word, length, code, life), if ``b > 0``."""
        b, wit = 0, None
        for d in range(1, D + 1):
            L, k, S = self.lmax(d)
            need = L + 1 - a * d
            if need > b and S is not None:
                b, wit = need, (k, d, S, L)
        return b, wit

    def lin_holds(self, a: int, b: int, D: int) -> bool:
        return all(self.lmax(d)[0] + 1 <= a * d + b for d in range(1, D + 1))

    def alive(self, k: int, d: int, m: int) -> int:
        return sum(1 for L in self.tasks[k].lives[d].values() if L >= d - 1 + m)

    def fit_amort(self, c: int, D: int):
        """Least ``e`` with ``#alive(d, d-1+m) * 2^(m/c) <= 2^(d-1+e)`` for every word,
        ``d <= D`` and ``m``; and the witness (word, d, m, count) refuting ``e - 1``."""
        e, wit = 0, None
        for k, t in self.tasks.items():
            for d in range(1, D + 1):
                top = max([L for L in t.lives[d].values()] + [d - 2])
                for m in range(0, top - d + 3):
                    n = self.alive(k, d, m)
                    while n * 2 ** (m // c) > 2 ** (d - 1 + e):
                        e += 1
                        wit = (k, d, m, n)
        return e, wit

    def amort_holds(self, c: int, e: int, D: int) -> bool:
        for k, t in self.tasks.items():
            for d in range(1, D + 1):
                top = max([L for L in t.lives[d].values()] + [d - 2])
                for m in range(0, top - d + 3):
                    if self.alive(k, d, m) * 2 ** (m // c) > 2 ** (d - 1 + e):
                        return False
        return True


# ---------------------------------------------------------------------------------------------
# the planner over statements
# ---------------------------------------------------------------------------------------------

STEP_WEIGHT = {"steeper": 1, "implies": 1, "analogy": 2}


def expand(state):
    fam, p, x = state
    out = [("steeper", (fam, p, x + 1))]
    if fam == "AMORT":
        out.append(("implies", ("LIN", p, x + 1)))
    if p < 4:
        out.append(("analogy", (fam, p + 1, x)))
    return out


def plan_statements(data: Dict[int, PeriodData], D_train: Dict[int, int], max_depth=6,
                    max_slope=6):
    """Breadth-first over chains of structural steps from the seeds ``LIN(2, 1, .)`` and
    ``AMORT(2, 1, .)``; every state gets its fitted offset on the training levels; states whose
    fitted statement was already reached (the same statement, i.e. the same verdicts on every
    level) are merged.  Returns hypotheses ``(depth, weight, chain, statement, witness)``."""
    seeds = [("LIN", 2, 1), ("AMORT", 2, 1)]
    layer = {s: () for s in seeds}
    seen = set(layer)
    hyps = []
    for depth in range(0, max_depth + 1):
        for state, chain in sorted(layer.items()):
            fam, p, x = state
            if x > max_slope:
                continue
            Dt = D_train[p]
            if fam == "LIN":
                off, wit = data[p].fit_lin(x, Dt)
            else:
                off, wit = data[p].fit_amort(x, min(Dt, AMORT_D))
            wt = sum(STEP_WEIGHT[s] for s in chain)
            hyps.append(dict(depth=depth, weight=wt + x + off, chain=list(chain),
                             statement=(fam, p, x, off), witness=wit))
            # derived statement through a proved implication
            if fam == "AMORT":
                hyps.append(dict(depth=depth + 1, weight=wt + 1 + (x + 1) + x * off,
                                 chain=list(chain) + ["implies(derived)"],
                                 statement=("LIN", p, x + 1, x * off), witness=None,
                                 derived_from=(fam, p, x, off)))
        nxt = {}
        for state, chain in layer.items():
            for sname, s2 in expand(state):
                if s2 in seen or s2[2] > max_slope:
                    continue
                seen.add(s2)
                nxt[s2] = chain + (sname,)
        layer = nxt
        if not layer:
            break
    hyps.sort(key=lambda h: (h["depth"], h["weight"], h["statement"]))
    return hyps


def frontier(hyps, fam, p):
    """Non-dominated statements of one family and period (smaller slope and offset are
    stronger)."""
    st = sorted({h["statement"] for h in hyps if h["statement"][0] == fam and
                 h["statement"][1] == p})
    return [s for s in st if not any(o != s and o[2] <= s[2] and o[3] <= s[3] for o in st)]


AMORT_D = 12  # AMORT levels are certified in Lean up to d = 12 (``amortCheck``)


# ---------------------------------------------------------------------------------------------
# the comparison with Round 27 (same oracle, same budget)
# ---------------------------------------------------------------------------------------------

def planner_strategy(task, budget):
    """The statement planner run against the Round 27 per-word oracle: structural chains from
    the seeds, each fitted offset found by counterexample-guided narrowing (every oracle call
    counted), tiers by cost.  Returns the records in the Round 27 format."""
    recs, tried, calls = [], set(), [0]

    def test(c, origin):
        if c in tried or calls[0] >= budget:
            return None
        tried.add(c)
        calls[0] += 1
        before = cb.WORK[0]
        ok, cex, hint = cb.oracle(c, task)
        recs.append(cb.record(c, origin, task, ok, cex, cb.WORK[0] - before))
        return ok, hint

    def fit(fam, x):
        b, origin = 0, "generated"
        while calls[0] < budget:
            r = test((fam, x, b), origin)
            if r is None:
                return None
            ok, hint = r
            if ok:
                return b
            b, origin = max(hint if hint is not None else b + 1, b + 1), "repaired"
        return None

    # tier order: depth (number of structural steps) then cost; WS fitted once (one state)
    order = [("LIN", 1), ("AMORT", 1), ("WS", 0), ("LIN", 2), ("AMORT", 2), ("LIN", 3),
             ("AMORT", 3), ("LIN", 4), ("AMORT", 4), ("LIN", 5), ("AMORT", 5), ("LIN", 6),
             ("AMORT", 6)]
    for fam, x in order:
        b = fit(fam, x)
        if fam == "AMORT" and b is not None:
            test(("LIN", x + 1, x * b), "derived")  # halfLineLinear_of_amortized
        if calls[0] >= budget:
            break
    return recs


# ---------------------------------------------------------------------------------------------

def main():
    D = {2: 20, 3: 18, 4: 16}
    data = {p: PeriodData(p, D[p]) for p in (2, 3, 4)}
    out = dict(levels=D, amort_levels=AMORT_D)
    print("level data: period 2 to d = %d, period 3 to d = %d, period 4 to d = %d" % (
        D[2], D[3], D[4]))
    for p in (2, 3, 4):
        print("   Lmax(p=%d): %s" % (p, [data[p].lmax(d)[0] for d in range(1, D[p] + 1)]))

    # 1. plan on all levels: the frontier to certify
    hyps = plan_statements(data, D)
    print("\n1. Statements generated by the planner (fitted on all levels; tier order):")
    for h in hyps[:40]:
        f, p, x, off = h["statement"]
        print("   depth %d cost %3d  %-5s p=%d %s=%d offset=%-3d  via %s" % (
            h["depth"], h["weight"], f, p, "a" if f == "LIN" else "c", x, off,
            " -> ".join(h["chain"]) or "(seed)"))
    fr = {}
    for p in (2, 3, 4):
        for fam in ("LIN", "AMORT"):
            fr[(fam, p)] = frontier([h for h in hyps if "derived_from" not in h], fam, p)
            print("   frontier %s p=%d: %s" % (fam, p, [s[2:] for s in fr[(fam, p)]]))
    wits = {}
    for h in hyps:
        if "derived_from" in h:
            continue
        f, p, x, off = h["statement"]
        wits[str(h["statement"])] = h["witness"]
    out["statements"] = [dict(statement=h["statement"], chain=h["chain"],
                              witness=h["witness"], depth=h["depth"], cost=h["weight"],
                              derived_from=h.get("derived_from")) for h in hyps]

    # 2. Occam for statements: fit on fewer levels, test on the rest
    print("\n2. Occam for statements: the offset fitted on d <= D_train, tested on the held-out "
          "levels d <= D (EMP)")
    occ = {}
    for p in (2, 3, 4):
        for Dt in range(6, D[p] + 1, 2):
            fails, n = 0, 0
            for a in range(1, 7):
                b, _ = data[p].fit_lin(a, Dt)
                n += 1
                if not data[p].lin_holds(a, b, D[p]):
                    fails += 1
            occ[(p, Dt)] = (fails, n)
        print("   LIN p=%d: fitted offsets that fail later, by D_train: %s" % (
            p, ", ".join("%d: %d/%d" % (Dt, *occ[(p, Dt)]) for Dt in range(6, D[p] + 1, 2))))
    out["occam"] = {"%d,%d" % k: v for k, v in occ.items()}

    # 3. Round 27 comparison (word 10, d <= 18, budget 60 oracle calls)
    print("\n3. Generation measured against Round 27 (same oracle, same budget of 60 calls):")
    train = cb.Task("word 10", 2, 1, 18)
    held = [cb.Task("word 100", 3, 1, 18), cb.Task("word 110", 3, 3, 18),
            cb.Task("word 1000", 4, 1, 18), cb.Task("word 1100", 4, 3, 18),
            cb.Task("word 1110", 4, 7, 18)]
    for strat in ("enumerate", "repair"):
        cb.summarize(strat, cb.run(strat, train, 60), held)
    precs = planner_strategy(train, 60)
    cb.summarize("statement planner (Round 30)", precs, held)
    props = [r["key"] for r in precs if r["formal_status"].startswith("OPEN")]
    json.dump(props, open(os.path.join(os.getcwd(), "proposals.json"), "w"))
    print("   proposals.json written (%d surviving statements): the GLM plug-in of Round 27 "
          "(`candidate_benchmark.py --glm proposals.json`) now has something to run" % len(props))
    cb.summarize("glm plug-in (proposals re-tested)", cb.run("glm", train, 60, props), held)

    out["frontier"] = {"%s,%d" % k: v for k, v in fr.items()}
    json.dump(out, open(os.path.join(os.getcwd(), "statement_frontier.json"), "w"), indent=1)
    print("\nstatement_frontier.json written")


if __name__ == "__main__":
    main()

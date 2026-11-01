#!/usr/bin/env python3
"""Round 41 — the v11 self-dialogue on Rule 30 and on the eight Round 39 benchmarks.

Rule 30: the core lifts statements about the left diagonals from D < 400 only.  The dialogue then
decides by itself what to run: it extends every survivor (doubling, up to D < 131072), reads each
counterexample by mining a law for the failing event with a fixed library of local predicates,
narrows refuted bounds, and answers "what does it imply?" only from checked edges.

Benchmarks: the eight problems of `../rule30_round39/general_benchmarks.py`, run unchanged; the
dialogue is then run on each resulting core.

Exact arithmetic only.  Run: python3 run_round41.py [--quick]   (about a minute; --quick caps
Rule 30 at D < 16384).  Writes r41_dialogue.md and r41_dialogue.json.
"""

from __future__ import annotations

import json
import sys
import time
from math import lcm
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "rule30_round39"))
sys.path.insert(0, str(HERE.parent / "rule30_round38"))

import hypothesis_engine as he  # noqa: E402  (exact observatory, Round 38)
import general_benchmarks as gb  # noqa: E402  (Round 39 benchmarks)
from glm_hypothesis_core import Core, Family  # noqa: E402
from glm_dialogue import Dialogue, Knowledge, PuzzleConfig  # noqa: E402

KNOW = Knowledge.load(HERE / "knowledge.json")


# ════════════════════════════════════════════════════════════════════════════════════════════
# Rule 30
# ════════════════════════════════════════════════════════════════════════════════════════════

def rule30(budget: int, pre_cap: int = 16000):
    pre = he.left_profile(pre_cap, pmax=64, want_pre=True).pre  # exact preperiods, D < pre_cap

    def observe(hi):
        p = he.left_profile(hi, pmax=64)
        assert p.settled_at is not None
        out, Q = {}, 1
        for D in range(hi):
            Q = lcm(Q, p.lp[D])  # the period of the band 0..D
            out[D] = {"white": p.white[D], "lp": p.lp[D], "Q": Q, "odd": p.parity[D] == 1,
                      "pat": p.pattern[D], "pre": pre[D] if D < pre_cap else None}
        return out

    core = Core(Family("Rule 30 left diagonals", observe))
    lifts = core.lift(range(0, 400), keys=["white", "lp"])
    for h in lifts:
        h.meta["tags"] = {"rule30.white_set"} if h.meta["key"] == "white" else \
            {"rule30.period_bound"}
    core.add("for D ≥ 20 the preperiod of left diagonal D exceeds D",
             test=lambda r, D: D < 20 or r[D]["pre"] > D, origin="given (Round 38 survivor)",
             dev=range(0, 400), meta={"key": "pre", "tags": {"rule30.transient_at_read"}})
    cen = core.add("the centre column is not eventually periodic (Problem 1)",
                   test=lambda r, k: True, origin="given (prize question)",
                   evidence_class="Pi2", meta={"tags": {"rule30.centre_aperiodic"}})
    cen.status = "open"
    P = {
        "white(D-1)": lambda r, D: r[D - 1]["white"],
        "white(D-2)": lambda r, D: r[D - 2]["white"],
        "odd(D-1)": lambda r, D: r[D - 1]["odd"],
        "odd(D-2)": lambda r, D: r[D - 2]["odd"],
        "odd(D-3)": lambda r, D: r[D - 3]["odd"],
        "pattern(D-2) = pattern(D-1)": lambda r, D: r[D - 2]["pat"] == r[D - 1]["pat"],
        "lp(D-1) = lp(D-2)": lambda r, D: r[D - 1]["lp"] == r[D - 2]["lp"],
        "D even": lambda r, D: D % 2 == 0,
    }
    E = {"white": ("white(D)", lambda r, D: r[D]["white"]),
         "lp": ("Q(D) ≠ Q(D−1), where Q(D) = lcm of the periods of diagonals 0..D",
                lambda r, D: r[D]["Q"] != r[D - 1]["Q"])}
    cfg = PuzzleConfig("Rule 30 left diagonals", budget=budget, caps={"pre": pre_cap},
                       predicates=P, events=E, mine_from=3, max_turns=30)
    d = Dialogue(core, cfg, KNOW)
    d.run()
    return core, d


# ════════════════════════════════════════════════════════════════════════════════════════════
# the eight benchmarks
# ════════════════════════════════════════════════════════════════════════════════════════════

def _primes(lo, hi):
    return [n for n in range(max(lo, 2), hi) if gb.is_prime(n)]


BENCH_CFG = {
    "Euler n²+n+41": dict(budget=80000),
    "Fermat numbers": dict(budget=10),
    "primes as a²+b²": dict(budget=120000, domain=_primes),
    "circle regions (Moser)": dict(budget=13),
    "Josephus": dict(budget=3000),
    "Collatz": dict(budget=400000),
    "gcd(n¹⁷+9,(n+1)¹⁷+9)": dict(budget=200000),
    "16-bit midpoint": dict(budget=80000),
}


def bench_tagger(name):
    def tag(h):
        t = set()
        key = h.meta.get("key")
        if h.origin == "lift" and h.meta.get("kind") == "always" and h.status == "survives":
            t.add("survives-sampled")
        if name.startswith("Euler") and h.origin == "residue-law":
            t |= {"euler.residue_law", "proved:euler.residue_law"}
        if name.startswith("primes") and h.origin == "residue-law":
            t |= {"two_squares.residue_law", "proved:two_squares.residue_law"}
        if name.startswith("Fermat") and key == "coprime_to_earlier":
            t |= {"fermat.coprime", "proved:fermat.coprime"}
        if name.startswith("Josephus") and h.meta.get("kind") == "template":
            t |= {"josephus.template", "proved:josephus.template"}
        if name.startswith("16-bit"):
            if key == "fixed_in_range":
                t |= {"midpoint.fixed", "proved:midpoint.fixed"}
            if h.origin == "mechanism":
                conj = " ∧ ".join(h.meta["conj"])
                t |= {f"midpoint.law:{conj}"}
                if conj == "overflow":
                    t |= {"midpoint.law", "proved:midpoint.law"}
        if name.startswith("Collatz") and key == "reaches1":
            t.add("collatz.reaches1")
        if name.startswith("circle") and h.meta.get("kind") == "poly":
            t.add("moser.poly")
        return t
    return tag


def benchmarks():
    out = []
    for name, fn in gb.BENCHES:
        core, res = fn(lambda *a: None)
        c = BENCH_CFG[name]
        cfg = PuzzleConfig(name, budget=c["budget"], domain=c.get("domain"),
                           tagger=bench_tagger(name), max_turns=12)
        d = Dialogue(core, cfg, KNOW)
        d.run()
        out.append((name, core, d))
    return out


# ════════════════════════════════════════════════════════════════════════════════════════════

def main():
    quick = "--quick" in sys.argv
    T0 = time.time()
    core, d = rule30(budget=16384 if quick else 131072)
    t_r30 = time.time() - T0
    benches = benchmarks()
    t_all = time.time() - T0
    dialogues = [("Rule 30 left diagonals", core, d)] + benches
    lines = ["# Round 41 — v11 self-dialogue transcripts (generated by `run_round41.py`)", "",
             "Every line is one utterance; the tag in brackets is its provenance (`record`: read "
             "from the hypothesis record; `computed`: produced by an action run during the "
             "dialogue; `lean:` / `ledger:`: a checked implication or fact). Numbers of 3 or more "
             "digits are checked against what was computed in this run and the ledger; a line "
             "that fails is marked UNGROUNDED.", ""]
    summary = []
    for name, c, dd in dialogues:
        lines.append(dd.markdown(name))
        bad = sum(1 for t in dd.turns if t["ungrounded_numbers"])
        summary.append({"puzzle": name, "utterances": len(dd.turns), "actions": dd.actions,
                        "hypotheses": len(c.hyps), "ungrounded": bad,
                        "statuses": {s: sum(1 for h in c.hyps if h.status == s)
                                     for s in sorted({h.status for h in c.hyps})}})
    lines += ["## Summary", "", "| puzzle | utterances | actions run | hypotheses | ungrounded |",
              "|---|---|---|---|---|"]
    for s in summary:
        lines.append(f"| {s['puzzle']} | {s['utterances']} | {s['actions']} | "
                     f"{s['hypotheses']} | {s['ungrounded']} |")
    lines += ["", f"Wall-clock: Rule 30 {t_r30:.1f} s, total {t_all:.1f} s "
                  f"({'quick' if quick else 'full'})."]
    stem = "r41_dialogue_quick" if quick else "r41_dialogue"
    (HERE / f"{stem}.md").write_text("\n".join(lines) + "\n")
    (HERE / f"{stem}.json").write_text(json.dumps(
        {"summary": summary,
         "dialogues": {n: {"turns": dd.turns, "hypotheses": c.table()} for n, c, dd in dialogues}},
        indent=1, default=str))
    for s in summary:
        print(s)
    print(f"total {t_all:.1f} s")


if __name__ == "__main__":
    main()

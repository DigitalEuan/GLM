"""``glm_universal.reasoning.theorem_wheel_round28`` -- bring the GLM's Rule 30 theorem wheel up
to date with the Lean package (Rounds 17-28), declare the Problem 3 vocabulary, and read the
whole evidence ledger as carriers.

Why
---
Up to Round 16 the wheel's vocabulary was typed in by hand (``theorem_wheel.py``,
``theorem_wheel_round13.py``, ``theorem_wheel_round16.py``).  Rounds 17-27 were done in Lean only,
so the GLM still answered "what is the narrowest open rung of Problem 1?" with the Round 12
answer (``SeedAPBalanced``).  This module

1. adds the statements and spokes of Rounds 21-28 (the half-line machine, the amortised halving
   target, the tuning excess, the Hankel form, the four proof routes, local-rule induction);
2. declares the Problem 3 vocabulary (To Do 8): ``P3Eventual -> P3`` and the negative control
   "the light-cone map is a different function";
3. reads ``_data/r28_wheel.json`` (the Lean package's ``glm/r28_wheel.json``, written by
   ``scripts/ledger_check.py --wheel``; ``setup_round28.sh`` copies it when ``PKG`` is set, and a
   three-row sample is used otherwise)
   so that every ledger row -- id, claim, evidence class, status, Lean names, axioms -- is a
   carrier the GLM can cite (To Do 6).  ``ledger(query)`` looks rows up by id or words.

Every spoke names its Lean theorem; the wheel still chains declared spokes only and cannot
invent one.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Tuple

try:  # inside the GLM repository
    from glm_universal.reasoning import theorem_wheel as tw
    from glm_universal.reasoning import theorem_wheel_round16 as tw16
except ImportError:  # standalone
    import theorem_wheel as tw  # type: ignore
    import theorem_wheel_round16 as tw16  # type: ignore

S, Spoke, NI = tw.Statement, tw.Spoke, tw.NonImplication

NEW_STATEMENTS = (
    # Problem 1: the half-line machine (Rounds 21-27)
    S("HalfLineDiesAll", "for every period p >= 1, every non-white p-periodic drive kills every "
      "finite left half-line code (the one-sided target)", "OPEN", "half-line machine"),
    S("HalfLineDies1", "period 1: the constant black drive kills every code by time d + 2",
      "FORMAL", "half-line machine", ("P1",)),
    S("HalfLineDies2", "period 2: the drive 1,0 kills every finite half-line code (the only "
      "word that matters, halfLineDies_two_iff)", "OPEN", "half-line machine"),
    S("PeriodTwoHalfLineLinear", "every half-line code of d cells fails the alternating test by "
      "time 2d + 8 (certified to d = 36)", "OPEN", "half-line machine"),
    S("AmortizedHalving241", "m steps after the edge at most 2^d / 2^floor(m/4) codes of length d "
      "are alive (Round27Open; certified d <= 12)", "OPEN", "half-line machine"),
    S("PreEdgeIndependent", "the tests before the edge are exactly independent: 2^(k - blacks k) "
      "codes survive them", "FORMAL", "half-line machine", ("P1",)),
    S("StateNeverRepeats", "the half-line state grows by one cell per step, so no state repeats "
      "and cycle certificates are vacuous", "FORMAL", "half-line machine", ("P1",)),
    S("ProofRoutes4", "individual termination, a state ranking, the population bound or width "
      "induction: each one would give the period-2 rung", "OPEN", "half-line machine"),
    S("ProgressMeasuresRefuted", "all 8 declared progress measures fail on every window <= 20; "
      "width steps <= 17 fail", "CERT", "half-line machine", ("P1",)),
    # Problem 1: tuning and Hankel (Rounds 23-26)
    S("TuneExcessLog", "the longest echo after n notes is at most 2 log2 n + 2 (certified "
      "n <= 131072, sharp offset)", "OPEN", "tuning by ear"),
    S("TuneCostUnbounded", "the periodic tuning loop never settles (unbounded tune cost)",
      "OPEN", "tuning by ear"),
    S("HankelInfinitelyOften", "infinitely many Hankel determinants of the centre column are "
      "non-zero", "OPEN", "power-series ladder"),
    # Problem 3 vocabulary (To Do 8)
    S("P3Eventual", "computing a(n) needs time >= eps * n for all large n (eventual form)",
      "OPEN", "machine model"),
    S("LightConeCircuitBound", "every fan-in-2 circuit for the light-cone map "
      "(x_-t..x_t) -> a(t)(0) is large (certified t <= 6; conditional in general)", "CERT",
      "machine model", ()),
    # induction (Round 10 / 28): the discipline behind tool induce and tool arc
    S("LocalRuleDeterminacy", "for any grid and any reader, all surviving local rules agree on a "
      "query iff every key it needs was seen; a clash refutes the reader for good", "FORMAL",
      "induction (ARC)"),
)

NEW_SPOKES = (
    Spoke(("HalfLineDiesAll",), "P1", "problem1_of_halfLineDies", "HalfLineMachine.lean"),
    Spoke(("HalfLineDies2",), "LeftWhiteAperiodic2", "leftWhiteAperiodic_of_halfLineDies",
          "HalfLineMachine.lean"),
    Spoke(("PeriodTwoHalfLineLinear",), "LeftWhiteAperiodic2",
          "leftWhiteAperiodic_two_of_halfLineLinear", "PeriodTwoHalfLineData.lean"),
    Spoke(("AmortizedHalving241",), "HalfLineDies2", "halfLineDies_of_amortized",
          "AmortizedHalving.lean"),
    Spoke(("ProofRoutes4",), "HalfLineDies2", "halfLineDies_two_of_routes", "ProofRoutes.lean"),
    Spoke(("TuneExcessLog",), "P1", "problem1_of_tuneExcessLog", "TuningByEar.lean"),
    Spoke(("P1",), "TuneCostUnbounded", "problem1_iff_tuneCost_unbounded", "TuningByEar.lean",
          iff=True),
    Spoke(("P1",), "HankelInfinitelyOften", "problem1IffHankelInfinitelyOften",
          "HankelKronecker.lean", iff=True),
    Spoke(("P3Eventual",), "P3", "problem3_of_eventual", "Problem3Quantifiers.lean"),
)

NEW_NON_IMPLICATIONS = (
    NI("LightConeCircuitBound", "P3", "(definitional) MachineModel.Problem3 vs MachineModel.centreWindow",
       "the light-cone map has 2t+1 input bits; Problem 3 is about computing a(n) from the "
       "binary digits of n: a different function"),
    NI("StateNeverRepeats", "HalfLineDies2", "window_not_closed",
       "a growing state gives no cycle, so a cycle search proves nothing; the prefix tree is the "
       "sound finite object"),
    NI("FinitePrefix", "HalfLineDies2", "no_finite_certificate_problem1",
       "certificates to d = 36 cover finitely many codes; the rung is about all d"),
)

NEW_FACT_LEAN = {
    "HalfLineDies1": "halfLineDies_one, constDrive_dies",
    "PreEdgeIndependent": "survivors_card",
    "StateNeverRepeats": "halfStateD_width, halfStateD_strictMono, window_not_closed",
    "ProgressMeasuresRefuted": "ProofRoutesData (Round 27)",
    "LightConeCircuitBound": "circuit_size_ge, circuit_size_ge_le_6",
    "LocalRuleDeterminacy": "GLM.LocalRule.determined_iff_seen, answer_determined_iff_covered, "
                            "survivor_correct, clash_refutes",
}

NEW_EVIDENCE = {
    "PeriodTwoHalfLineLinear": ("CERT prefix search to d = 36 (PrefixSearchData)",
                                "EMP prefix_search.c to d = 46"),
    "AmortizedHalving241": ("CERT d <= 12 (Round27Open; smallest unresolved d = 13)",
                            "EMP stable to d = 17 (conjecture_loop_output.txt)"),
    "TuneExcessLog": ("CERT tuneExcessLog_upto_131072", "EMP to 10^6"),
    "HalfLineDies2": ("CERT exact longest lives for d <= 32 (lmaxTwo_spec)",
                      "EMP Round 28 inner_survivors.py: long survivors do not carry one long "
                      "inner alternation (min stretch 7..14 while post-edge life grows to 20)"),
}

_STD = ("propext", "Classical.choice", "Quot.sound")
NEW_AXIOMS = {
    "problem1_of_halfLineDies": _STD, "leftWhiteAperiodic_of_halfLineDies": _STD,
    "halfLineDies_of_amortized": _STD, "halfLineDies_two_of_routes": _STD,
    "problem1_of_tuneExcessLog": _STD, "problem1_iff_tuneCost_unbounded": _STD,
    "problem1IffHankelInfinitelyOften": _STD, "problem3_of_eventual": _STD,
}

#: The narrowest open rung of each problem, as recorded in AUDIT.md section 3.1 (Round 28).
NARROWEST = {
    "P1": ("AmortizedHalving241", "HalfLineDies2", "PeriodTwoHalfLineLinear"),
    "P2": ("SeedAPBalanced", "SqrtWobble"),
    "P3": ("P3Eventual",),
}


def extend() -> None:
    """Add Rounds 13, 16 and 28 to the wheel (idempotent)."""
    tw16.extend()
    for s in NEW_STATEMENTS:
        tw.STATEMENTS[s.name] = s
    have = {(sp.premises, sp.conclusion, sp.lean) for sp in tw.SPOKES}
    tw.SPOKES = tw.SPOKES + tuple(sp for sp in NEW_SPOKES
                                  if (sp.premises, sp.conclusion, sp.lean) not in have)
    haveni = {(n.premise, n.conclusion) for n in tw.NON_IMPLICATIONS}
    tw.NON_IMPLICATIONS = tw.NON_IMPLICATIONS + tuple(
        n for n in NEW_NON_IMPLICATIONS if (n.premise, n.conclusion) not in haveni)
    tw.FACT_LEAN.update(NEW_FACT_LEAN)
    for k, v in NEW_EVIDENCE.items():
        tw.EVIDENCE[k] = v
    tw.AXIOM_FOOTPRINT.update(NEW_AXIOMS)


# ---------------------------------------------------------------------------------------------
# The ledger as carriers (To Do 6)
# ---------------------------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
WHEEL_JSON = os.path.join(_HERE, "_data", "r28_wheel.json")
#: A three-row sample, used only when the full ledger export has not been installed.
WHEEL_SAMPLE = os.path.join(_HERE, "_data", "r28_wheel_sample.json")


def carriers_source() -> str:
    return WHEEL_JSON if os.path.exists(WHEEL_JSON) else WHEEL_SAMPLE


def carriers(path: Optional[str] = None) -> List[Dict[str, object]]:
    p = path or carriers_source()
    if not os.path.exists(p):
        return []
    with open(p) as f:
        data = json.load(f)
    return data.get("carriers", data) if isinstance(data, dict) else data


def ledger(query: str, path: Optional[str] = None, limit: int = 8) -> List[Dict[str, object]]:
    """Ledger rows whose id equals ``query`` or whose claim contains every word of it."""
    rows = carriers(path)
    q = query.strip().lower()
    exact = [r for r in rows if str(r.get("id", "")).lower() == q]
    if exact:
        return exact
    words = [w for w in q.split() if len(w) > 2]
    hits = [r for r in rows if all(w in (str(r.get("claim", "")) + " " +
                                         " ".join(r.get("lean", []) or [])).lower()
                                   for w in words)]
    return hits[:limit]


def narrowest_text(target: str) -> str:
    extend()
    lines = []
    for name in NARROWEST.get(target, ()):
        st = tw.STATEMENTS.get(name)
        if st is None:
            continue
        lines.append(f"  {name} [{st.status}]: {st.text}")
        for e in tw.EVIDENCE.get(name, ()):
            lines.append(f"    evidence: {e}")
    return "\n".join(lines)


def theorem28_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool theorem`` with the Round 28 vocabulary: ``ledger QUERY``, ``narrowest P1|P2|P3``,
    else the Round 12 commands over the extended wheel."""
    extend()
    a = arg.strip()
    if a.startswith("ledger"):
        rows = ledger(a[len("ledger"):])
        if not rows:
            return False, "no ledger row matches (is _data/r28_wheel.json installed?)", {
                "status": "none"}
        out = [f"{r['id']} [{r.get('class')}, {r.get('status')}] {r.get('claim')} "
               f"| Lean: {'; '.join(r.get('lean', []) or []) or '-'}" for r in rows]
        return True, "\n".join(out), {"status": "rows", "count": len(rows)}
    if a.startswith("narrowest"):
        t = a.split()[-1].upper()
        txt = narrowest_text(t)
        return bool(txt), f"narrowest open rungs of {t} (AUDIT 3.1):\n" + txt, {"target": t}
    return tw.theorem_text(arg)


def discuss28_text(question: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool discuss`` over the extended wheel: the structured reading of Round 16, then the
    narrowest open rungs recorded by the Lean package."""
    extend()
    ok, text, info = tw16.discuss_structured(question)
    tgt = None
    r = info.get("reading") if isinstance(info, dict) else None
    if r is not None and getattr(r, "target", None) in NARROWEST:
        tgt = r.target
    elif isinstance(info, dict) and info.get("target") in NARROWEST:
        tgt = info["target"]
    if tgt:
        text += "\nROUND 28 NARROWEST OPEN RUNGS (Lean package, AUDIT 3.1)\n" + narrowest_text(tgt)
    return ok, text, info

"""``glm_universal.reasoning.theorem_wheel_round13`` -- Round 13 additions to the Rule 30 theorem
wheel, and the *vocabulary audit*.

Round 12's wheel (``theorem_wheel.py``) is extended in place by ``extend()`` with the Round 13
statements and spokes (Lean package ``RequestProject/GLM/Rule30``, files ``LeftWhiteLift.lean``,
``LeftWhiteCompactness.lean``, ``RunBoundData.lean``, ``ChemistryLab.lean``):

* the **stack lift**: ``LeftWhiteAperiodicAll`` (no column of any left-white row is eventually
  periodic) ``=> P1``; it is equivalent to ``RunBoundsAll`` (a run bound for every period);
* the **propose-and-check loop**: ``P1 <=> EveryProposalRefuted``;
* proved facts: ``LeftWhiteStride1`` (period 1 for every left-white row), ``LoopHorizon1`` (the
  loop's horizon 4N + 6 for period 1), the certificates ``RunBound2Small``,
  ``RunBoundSmallPeriods`` and ``NoConservationLaw6`` (the chemistry lab).

``vocabulary_audit(target)`` answers "what does the GLM need to answer this question?": which
words it has, whether it can *state* the question, whether a chain of proved spokes *answers* it,
and, if not, exactly what is missing and what kind of object it is (a single theorem, or an
infinite family that needs a uniform argument).  Everything is retrieval over declared
statements; nothing is invented.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

try:  # inside the GLM repository
    from glm_universal.reasoning import theorem_wheel as tw
except ImportError:  # standalone, from the study folder
    import os
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(here, "..", "..", "..", "..", "rule30_round12", "glm_overlay",
                                    "glm_universal", "reasoning"))
    import theorem_wheel as tw  # type: ignore

S, Spoke = tw.Statement, tw.Spoke

NEW_STATEMENTS = (
    S("LeftWhiteAperiodicAll", "for every period p >= 1, no column of any left-white row (white "
      "left of a black cell) is eventually p-periodic", "OPEN", "stack lift (every row)"),
    S("RunBoundsAll", "for every period p >= 1 there is a run bound B_p: a column at distance d from "
      "the edge of a left-white row stays p-periodic for at most B_p(d) steps", "OPEN",
      "stack lift (every row)"),
    S("LeftWhiteAperiodic2", "no column of any left-white row is eventually 2-periodic (the next "
      "rung after period 1)", "OPEN", "stack lift (every row)"),
    S("EveryProposalRefuted", "every proposal 'the centre column has period p from time N' is "
      "eventually refuted by an observation", "OPEN", "propose-and-check loop"),
    S("LeftWhiteStride1", "no column of any left-white row is eventually constant", "FORMAL",
      "stack lift (every row)", ("P1",)),
    S("LoopHorizon1", "the proposal 'constant from time N' is refuted by time 4N + 6", "FORMAL",
      "propose-and-check loop", ("P1",)),
    S("RunBound2Small", "period-2 run bounds 1,7,6,5,5,8,9,9 for distances d <= 7, exact, for every "
      "left-white row", "CERT", "stack lift (every row)", ("P1",)),
    S("RunBoundSmallPeriods", "exact run bounds for periods 3..6 at distances d <= 4, for every "
      "left-white row", "CERT", "stack lift (every row)", ("P1",)),
    S("NoConservationLaw6", "the seed run has no non-trivial additive conserved quantity of range "
      "<= 6", "CERT", "chemistry lab"),
)

NEW_SPOKES = (
    Spoke(("LeftWhiteAperiodicAll",), "P1", "problem1_of_leftWhiteAperiodicAll",
          "LeftWhiteCompactness.lean"),
    Spoke(("LeftWhiteAperiodicAll",), "RunBoundsAll", "leftWhiteAperiodicAll_iff_runBoundsAll",
          "LeftWhiteCompactness.lean", iff=True),
    Spoke(("P1",), "EveryProposalRefuted", "problem1_iff_every_proposal_refuted",
          "LeftWhiteLift.lean", iff=True),
)

NEW_FACT_LEAN = {
    "LeftWhiteStride1": "leftWhiteAperiodic_one",
    "LoopHorizon1": "refutation_horizon_one",
    "RunBound2Small": "runBound_two_upTo_seven, runBound_two_sharp",
    "RunBoundSmallPeriods": "runBound_small_periods",
    "NoConservationLaw6": "seed_run_no_conservation_law",
}

NEW_EVIDENCE = {
    "LeftWhiteAperiodicAll": (
        "CERT runBound_two_upTo_seven / runBound_small_periods: exact run bounds, all left-white rows",
        "EMP r13_periodic_runs: exact longest runs for p <= 6 at d <= 7-9; the period-2 search "
        "relaxation dies within about 1.6 d + 4 steps for every d <= 24"),
    "LeftWhiteAperiodic2": (
        "CERT runBound_two_upTo_seven (d <= 7, sharp: runBound_two_sharp)",
        "EMP r13_periodic_runs dfs: no alternating column survives beyond 38 steps for d <= 24"),
}

_STD = ("propext", "Classical.choice", "Quot.sound")
_CMP = ("propext", "Classical.choice", "Lean.ofReduceBool", "Lean.trustCompiler", "Quot.sound")
#: ``#print axioms`` output, RequestProject/GLM/Rule30/scripts/theorem_wheel_axioms.lean (Round 13).
NEW_AXIOMS = {
    "problem1_of_leftWhiteAperiodicAll": ("propext", "Quot.sound"),
    "leftWhiteAperiodicAll_iff_runBoundsAll": _STD,
    "problem1_iff_every_proposal_refuted": _STD, "leftWhiteAperiodic_one": _STD,
    "refutation_horizon_one": _STD, "runBound_two_upTo_seven": _CMP, "runBound_two_sharp": _CMP,
    "runBound_small_periods": _CMP, "seed_run_no_conservation_law": _CMP,
}


def extend() -> None:
    """Add the Round 13 vocabulary to the wheel (idempotent)."""
    for s in NEW_STATEMENTS:
        tw.STATEMENTS[s.name] = s
    have = {(sp.premises, sp.conclusion, sp.lean) for sp in tw.SPOKES}
    tw.SPOKES = tw.SPOKES + tuple(sp for sp in NEW_SPOKES
                                  if (sp.premises, sp.conclusion, sp.lean) not in have)
    tw.FACT_LEAN.update(NEW_FACT_LEAN)
    for k, v in NEW_EVIDENCE.items():
        tw.EVIDENCE[k] = v
    tw.AXIOM_FOOTPRINT.update(NEW_AXIOMS)


#: What kind of object each open sufficient statement is (the shape of the missing proof).
SHAPE: Dict[str, str] = {
    "SeedFSTypical": "one theorem about the seed, quantified over every finite-state observer",
    "SeedAPBalanced": "one theorem about the seed, quantified over every progression (p, r)",
    "SqrtWobble": "one quantitative theorem about the seed (stronger than the target)",
    "NoResonance": "one theorem about the seed, quantified over every lag p",
    "OtherColumnPeriodic": "one theorem about a column c != 0 (expected to fail: off-centre columns "
                           "look as irregular as the centre in all data so far)",
    "LeftWhiteAperiodicAll": "an infinite family over periods p, about every left-white row; "
                             "p = 1 is proved, so it needs a uniform argument (an induction on p "
                             "or a single invariant), not more data",
    "RunBoundsAll": "the same family in quantitative form (a horizon B_p(d) for each p)",
}

#: What each target needs beyond the wheel (stated plainly).
NEEDS: Dict[str, Tuple[str, ...]] = {
    "P1": ("a proof of any one sufficient statement, or of a new spoke from a proved fact into P1",
           "the narrowest rung of the stack lift that is not yet proved: LeftWhiteAperiodic2 "
           "(evidence: CERT for d <= 7, EMP for d <= 24); a proof of it, uniform in d, would be "
           "the period-2 case of Problem 1 (and more)",
           "a 'for every p' word: the wheel can hold the family as one statement, but it cannot "
           "prove a family; that needs an induction step, which is a new theorem"),
    "P2": ("a proof of SeedAPBalanced, SeedFSTypical or SqrtWobble for the seed (each implies P2)",
           "no counting argument of small range can supply it: the seed run has no non-trivial "
           "conserved quantity of range <= 6 (NoConservationLaw6, the chemistry lab), and the "
           "persistent arrow carries no information (exists_balanced_persistent_arrow)",
           "a normalisation word (D/sqrt N) to compare wobble readings on one scale (Round 12)"),
    "P3": ("a machine model in the vocabulary (Problem3 is stated for Turing machines in "
           "MachineModel.lean) and a lower-bound technique for one explicit sequence on that "
           "model; no method is currently known that proves a lower bound of this kind for a "
           "sequence like this one, so this is beyond the reach of the wheel",
           "the proved facts (DegreeFormula, WholeCone) are about the n-step map, not about the "
           "sequence n -> a(n); they cannot reach P3 (map_properties_cannot_decide_periodicity is "
           "the analogous block for P1)"),
}


def vocabulary_audit(target: str) -> str:
    extend()
    st = tw.STATEMENTS[target]
    out: List[str] = [f"VOCABULARY AUDIT  {target}: {st.text}"]
    out.append(f"  can the GLM STATE it?   yes: declared statement {target} (a Lean definition, "
               f"a complete description of the question)")
    g = tw.gap(target)
    out.append(f"  can the GLM ANSWER it?  {'yes' if g['closed'] else 'no'}: the "
               f"{len(g['facts'])} proved facts {'reach' if g['closed'] else 'do not reach'} "
               f"{target} through the {len(tw.SPOKES)} declared spokes")
    eq = tw.equivalents(target)
    if eq:
        out.append(f"  equivalent words (restatements, same difficulty): {', '.join(eq)}")
    suff = tw.weakest_first(tw.sufficient_open(target))
    if suff:
        out.append("  missing pieces (any one would answer it), weakest first:")
        for n, stronger in suff:
            shape = SHAPE.get(n, "")
            out.append(f"    {n}: {tw.STATEMENTS[n].text}")
            if shape:
                out.append(f"      shape: {shape}")
    else:
        out.append("  missing pieces: no sufficient statement is declared")
    if g["nearest"]:
        out.append(f"  nearest proved facts: {', '.join(g['nearest'])}")
    out.append("  what it needs:")
    for line in NEEDS.get(target, ()):
        out.append(f"    - {line}")
    return "\n".join(out)

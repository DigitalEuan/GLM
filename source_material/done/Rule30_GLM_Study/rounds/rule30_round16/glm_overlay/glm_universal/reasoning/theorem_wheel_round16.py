"""``glm_universal.reasoning.theorem_wheel_round16`` -- Round 16 additions to the Rule 30 theorem
wheel: new spokes, and a **structured reading** of questions for ``discuss``.

Why a structured reading
------------------------
Round 12's router (``theorem_wheel._target_of``) takes the *first* keyword pattern that matches.
So "is the wobble bounded over a period of time?" goes to Problem 1 (it says "period"), and "how
long does the frequency take to settle?" can go to Problem 3 ("time").  The reading below parses
the question into four slots and routes on the structure, not on the first keyword:

* **property** -- periodicity, frequency/balance, wobble accumulator, computation cost,
  algebraic degree (map), cone geometry;
* **claim form** -- bound, limit, equivalence, existence, value;
* **object** -- centre column, other column, left-white rows, the n-step map, the diagram;
* **rung** -- a named sub-statement (e.g. period 2 -> ``LeftWhiteAperiodic2``).

Rules: cost words count only when attached to a computing verb ("time to compute", "running
time"), never "over time"; a bound or limit on the wobble or the frequency routes to Problem 2
whatever context words appear; questions about the n-step map are flagged with the E2 block;
cone/triangle/angle questions go to the proved geometry, not to a prize target.  If two targets
remain close, the reading is **ambiguous** and ``discuss_structured`` asks instead of guessing.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

try:  # inside the GLM repository
    from glm_universal.reasoning import theorem_wheel as tw
    from glm_universal.reasoning import theorem_wheel_round13 as tw13
except ImportError:  # standalone, from the study folder
    import os
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.join(here, "..", "..", "..", "..")
    sys.path.insert(0, os.path.join(root, "rule30_round12", "glm_overlay", "glm_universal",
                                    "reasoning"))
    sys.path.insert(0, os.path.join(root, "rule30_round13", "glm_overlay", "glm_universal",
                                    "reasoning"))
    import theorem_wheel as tw  # type: ignore
    import theorem_wheel_round13 as tw13  # type: ignore

S, Spoke = tw.Statement, tw.Spoke

# ---------------------------------------------------------------------------------------------
# 1.  Round 16 vocabulary
# ---------------------------------------------------------------------------------------------

NEW_STATEMENTS = (
    S("TopMonomialUnique", "for every n >= 3 the only top-degree monomial of a(n)(c) is "
      "x_{c+2-n}...x_{c+n}; its weight 2n - 2 grows by exactly 2 per step", "FORMAL",
      "algebraic (ANF)"),
    S("RunBound2Upto16", "period-2 run bounds 1,7,6,5,5,8,9,9,16,15,14,13,14,16,19,21,25 for "
      "distances d <= 16, exact, for every left-white row", "CERT", "stack lift (every row)",
      ("P1",)),
    S("PeriodTwoLinearBound", "a column at distance d from the edge of a left-white row stays "
      "2-periodic for at most 2d + 7 steps", "OPEN", "stack lift (every row)"),
    S("InfluenceConeChiral", "a one-cell change always reaches (n, j + n) (rigid right side); the "
      "left side can move at speed 1 or 0", "FORMAL", "cone geometry"),
    S("LatticeConeFraction", "a lattice light cone fills exactly 1/(2k) of all directions of "
      "k-dimensional space-time (1/4 for Rule 30, 1/6 for 2D rules)", "FORMAL", "cone geometry"),
    S("NormalisedWobble", "over all words of length N, D(N)^2 has mean exactly N and "
      "z = D/sqrt(N) has mean square exactly 1", "FORMAL", "continuous wobble"),
)

NEW_SPOKES = (
    Spoke(("PeriodTwoLinearBound",), "LeftWhiteAperiodic2", "leftWhiteAperiodic_two_of_linearBound",
          "RunBoundSearch.lean"),
)

NEW_FACT_LEAN = {
    "TopMonomialUnique": "topMonomial_unique, topMonomial_unique_at, topDegree_weight_growth",
    "RunBound2Upto16": "runBound_two_upTo_sixteen, runBound_two_witness",
    "InfluenceConeChiral": "influence_right_ray, influence_left_ray_fast, influence_left_ray_stalls",
    "LatticeConeFraction": "axisCone_fraction, lightCone_ball_fraction, lightCone_cube_fraction",
    "NormalisedWobble": "sum_wordWobble_sq, mean_sq_zScore, card_large_zScore_le",
}

NEW_EVIDENCE = {
    "LeftWhiteAperiodic2": (
        "CERT runBound_two_upTo_sixteen (d <= 16, exact; witnesses runBound_two_witness)",
        "EMP r16_period_runs: exact values continue 35,34,33,32,31,31,30,34 for d = 19..26; the run "
        "ends on a few 'barrier' diagonals: d + run = 8, 24, 41, 54, 55, 60 in blocks"),
    "PeriodTwoLinearBound": (
        "CERT runBoundTwoExt_le_linear (d <= 16)", "EMP r16_period_runs (d <= 26)"),
}

_STD = ("propext", "Classical.choice", "Quot.sound")
_CMP = ("propext", "Classical.choice", "Lean.ofReduceBool", "Lean.trustCompiler", "Quot.sound")
#: ``#print axioms`` output (RequestProject/GLM/Rule30/scripts/theorem_wheel_axioms.lean, Round 16).
NEW_AXIOMS = {
    "topMonomial_unique": _STD, "topMonomial_unique_at": _STD, "topDegree_weight_growth": _STD,
    "runBound_two_upTo_sixteen": _CMP, "runBound_two_witness": _CMP,
    "leftWhiteAperiodic_two_of_linearBound": ("propext", "Quot.sound"),
    "influence_right_ray": _STD, "influence_left_ray_fast": ("propext", "Quot.sound"),
    "influence_left_ray_stalls": _STD, "axisCone_fraction": _STD,
    "lightCone_ball_fraction": _STD, "lightCone_cube_fraction": _STD,
    "sum_wordWobble_sq": _STD, "mean_sq_zScore": _STD, "card_large_zScore_le": _STD,
}


def extend() -> None:
    """Add the Round 13 and Round 16 vocabulary to the wheel (idempotent)."""
    tw13.extend()
    for s in NEW_STATEMENTS:
        tw.STATEMENTS[s.name] = s
    have = {(sp.premises, sp.conclusion, sp.lean) for sp in tw.SPOKES}
    tw.SPOKES = tw.SPOKES + tuple(sp for sp in NEW_SPOKES
                                  if (sp.premises, sp.conclusion, sp.lean) not in have)
    tw.FACT_LEAN.update(NEW_FACT_LEAN)
    for k, v in NEW_EVIDENCE.items():
        tw.EVIDENCE[k] = v
    tw.AXIOM_FOOTPRINT.update(NEW_AXIOMS)

# ---------------------------------------------------------------------------------------------
# 2.  Structured reading
# ---------------------------------------------------------------------------------------------

#: (slot, value, pattern, weight).  Patterns are matched on word boundaries.
_FEATURES: Tuple[Tuple[str, str, str, int], ...] = (
    # property -> which target it speaks about
    ("property", "periodicity", r"periodic\w*|period(?:s)?\b|repeat\w*|cycl\w*|alternat\w*|"
     r"eventually constant", 3),
    ("property", "frequency", r"frequenc\w*|balanc\w*|half|proportion|density|ratio of (?:black|"
     r"ones)|equally|normal(?:ity)?\b|bias\w*", 3),
    ("property", "wobble", r"wobble|accumulator|d\(n\)|deviation|drift", 3),
    ("property", "cost", r"running time|time to compute|steps to compute|comput\w* (?:a\(n\)|the "
     r"n-?th|cell)|computational|complexity|algorithm|shortcut|faster than|predict the n-?th|"
     r"cost", 3),
    ("property", "degree", r"anf|degree|monomial|polynomial|weight growth|n-step map", 2),
    ("property", "geometry", r"cone|triangle|angle|degrees|slice|sphere|circle|light ?cone", 2),
    # claim form
    ("form", "bound", r"bound\w*|at most|at least|<=|>=|o\(|grow\w*|sqrt", 1),
    ("form", "limit", r"limit|tend\w*|converg\w*|asymptot\w*|eventually|in the long run|"
     r"settle\w*", 1),
    ("form", "equivalence", r"equivalent|iff|if and only if|same as", 1),
    ("form", "existence", r"is there|exists?|some\b", 1),
    # object
    ("object", "centre", r"cent(?:re|er) column|centre|center|a\(n\)", 1),
    ("object", "column", r"column [-+]?\d+|other column|neighbou?r column", 1),
    ("object", "leftwhite", r"left-?white|every row|all rows", 1),
    ("object", "map", r"n-step map|initial row|all initial|as a function of the row", 1),
)

_PROPERTY_TARGET = {"periodicity": "P1", "frequency": "P2", "wobble": "P2", "cost": "P3"}

_RUNGS: Tuple[Tuple[str, str, str], ...] = (
    (r"period(?:-| )?(?:2|two)\b|alternat\w*", "P1", "LeftWhiteAperiodic2"),
    (r"period(?:-| )?(?:1|one)\b|eventually constant", "P1", "LeftWhiteStride1"),
    (r"sqrt|square root|d\(n\)\s*/\s*sqrt|normalis\w*|normaliz\w*|z-?score", "P2", "SqrtWobble"),
)


_RUNG_TARGET = {rung: target for _, target, rung in _RUNGS}


@dataclass
class Reading:
    question: str
    slots: Dict[str, List[str]] = field(default_factory=dict)
    scores: Dict[str, int] = field(default_factory=dict)
    target: Optional[str] = None
    rung: Optional[str] = None
    ambiguous: bool = False
    notes: List[str] = field(default_factory=list)

    def summary(self) -> str:
        sl = "; ".join(f"{k}={','.join(v)}" for k, v in sorted(self.slots.items()))
        sc = ", ".join(f"{k}:{v}" for k, v in sorted(self.scores.items()))
        t = "AMBIGUOUS" if self.ambiguous else (self.target or "none")
        return f"READING  {sl or 'no slots'} | scores {sc or '-'} | target {t}" + (
            f" | rung {self.rung}" if self.rung else "")


def read(question: str) -> Reading:
    q = " " + question.lower() + " "
    r = Reading(question)
    for slot, value, pat, w in _FEATURES:
        hits = re.findall(r"(?<![\w])(?:" + pat + r")(?![\w])", q)
        if hits:
            r.slots.setdefault(slot, []).append(value)
            t = _PROPERTY_TARGET.get(value) if slot == "property" else None
            if t:
                r.scores[t] = r.scores.get(t, 0) + w * len(hits)
    props = r.slots.get("property", [])
    forms = r.slots.get("form", [])
    # structural rule: a bound/limit on the wobble or the frequency is a Problem 2 question
    if ("wobble" in props or "frequency" in props) and ({"bound", "limit"} & set(forms)):
        r.scores["P2"] = r.scores.get("P2", 0) + 4
        r.notes.append("a bound or limit on the wobble/frequency: routed to Problem 2")
    # 'period of time' / 'over time' are context, not periodicity or cost
    if re.search(r"period of time|over time|in time", q) and "periodicity" in props:
        r.scores["P1"] = max(0, r.scores.get("P1", 0) - 3)
        r.notes.append("'period of time' read as context, not as periodicity")
    for pat, target, rung in _RUNGS:
        if re.search(pat, q):
            r.scores[target] = r.scores.get(target, 0) + 2
            r.rung = r.rung or rung
    if "map" in r.slots.get("object", []) or "degree" in props:
        r.notes.append("the n-step map is a property of all rows: it cannot decide the seed's "
                       "column (E2, map_properties_cannot_decide_periodicity)")
    if "geometry" in props and not r.scores:
        r.target = "GEOMETRY"
        r.notes.append("geometry question: see InfluenceConeChiral and LatticeConeFraction")
        return r
    ranked = sorted(r.scores.items(), key=lambda kv: -kv[1])
    ranked = [kv for kv in ranked if kv[1] > 0]
    if not ranked:
        return r
    if len(ranked) > 1 and 4 * ranked[1][1] >= 3 * ranked[0][1]:
        r.ambiguous = True
        r.notes.append("two targets are close: " + ", ".join(f"{k} ({v})" for k, v in ranked))
        return r
    r.target = ranked[0][0]
    if r.rung and _RUNG_TARGET.get(r.rung) != r.target:
        r.rung = None
    return r


_CANON = {"P1": "problem 1", "P2": "problem 2", "P3": "problem 3"}


def discuss_structured(question: str) -> Tuple[bool, str, Dict[str, object]]:
    """``tool discuss`` with the structured reading in front of the Round 12 pipeline."""
    extend()
    r = read(question)
    head = [r.summary()] + [f"  note: {n}" for n in r.notes]
    if r.ambiguous:
        return False, "\n".join(head + ["refused to guess: please say which problem you mean "
                                        "(1 periodicity, 2 frequency/wobble, 3 cost)"]), {
            "status": "ambiguous", "reading": r}
    if r.target == "GEOMETRY":
        lines = head + [f"  {n}: {tw.STATEMENTS[n].text} [{tw.FACT_LEAN[n]}]"
                        for n in ("InfluenceConeChiral", "LatticeConeFraction")]
        return True, "\n".join(lines), {"status": "geometry", "reading": r}
    if r.target is None:
        ok, text, info = tw.discuss_text(question)
        return ok, "\n".join(head + [text]), dict(info, reading=r)
    ok, text, info = tw.discuss_text(_CANON[r.target])
    if r.rung and r.rung in tw.STATEMENTS:
        st = tw.STATEMENTS[r.rung]
        head.append(f"  rung {r.rung}: {st.text} [{st.status}]")
        for e in tw.EVIDENCE.get(r.rung, ()):
            head.append(f"    evidence: {e}")
    return ok, "\n".join(head + [text]), dict(info, reading=r)

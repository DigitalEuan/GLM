"""``glm_universal.reasoning.theorem_wheel_round37`` -- bring the GLM's Rule 30 theorem wheel up to
Round 37 of the Lean package: the drive wheel (Round 36) as an **instantiation rule over hubs**,
the exact cost of a turn and the observer's best phase (Round 37, To Do 40), and the one-run hub
family (Round 37, To Do 39).

Why
---
Asked in Round 37 before this overlay (``rule30_round37/glm_consult_before_output.txt``), the GLM
refused ``derive WheelDies => HalfLineDies5`` (no statement), could not map a word to its hub, and
``tool next`` proposed periods and To Do items, never hubs (alignment 0/11).

What this module adds
---------------------
1. Statements ``WheelDies``, ``HubsOfDivisors<p>`` (p = 2..8: every hub of every divisor of ``p``
   kills every half-line), ``HalfLineDies5..8``, the best-phase targets ``PhaseTwo01Slack3``,
   ``PhaseThree010Slack5``, ``PhaseThree101Slack2``, the family targets ``OneRunFamilyDies`` and
   the proved facts ``TurnCostExact``, ``BestPhaseSuffices``, ``OneRunBand``.
2. The **hub rule** (``hub_spokes``): ``HubsOfDivisors<p> <=> HalfLineDies<p>`` for every declared
   ``p``, citing ``halfLineDies_iff_wheel``, and ``WheelDies => HubsOfDivisors<p>`` (a hub of a
   divisor is a hub).  Like the divisor rule it declares spokes from one proved schema.
3. The Round 37 spokes, each citing its Lean theorem, and the ledger rows C343-C350.

The wheel still chains declared spokes only.  ``NOT DERIVABLE`` is not a refutation.
"""
from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Tuple

try:  # inside the GLM repository
    from glm_universal.reasoning import theorem_wheel as tw
    from glm_universal.reasoning import theorem_wheel_round33 as tw33
    from glm_universal.reasoning import theorem_wheel_round34 as tw34
except ImportError:  # standalone
    import theorem_wheel as tw  # type: ignore
    import theorem_wheel_round33 as tw33  # type: ignore
    import theorem_wheel_round34 as tw34  # type: ignore

S, Spoke = tw.Statement, tw.Spoke

LENS = "drive wheel (hubs)"
PERIODS = range(2, 9)

NEW_STATEMENTS = (
    S("WheelDies", "every hub (primitive least turn, Lyndon word) of every period kills every "
      "non-empty half-line; equivalently every periodic drive with a black cell does",
      "OPEN", LENS),
    *(S(f"HalfLineDies{p}", f"every non-empty half-line dies under every non-white drive word "
        f"of period {p}", "OPEN", "half-line machine") for p in range(5, 9)),
    *(S(f"HubsOfDivisors{p}", f"every hub of every divisor of {p} kills every non-empty "
        f"half-line (the hub form of HalfLineDies{p})", "OPEN", LENS) for p in PERIODS),
    S("TurnCostExact", "the exact cost of a turn of the wheel: starting the clock m steps later "
      "costs m plus the tests skipped; between phases a and b (a + m = b mod p) the slack of "
      "phase a is at most the slack of phase b plus m plus the tests of phase a in its first m "
      "times; some pair of phases attains it in 66 of the 69 wheels of period 2..8 (EMP)", "FORMAL", LENS, ("P1",)),
    S("BestPhaseSuffices", "the observer's best phase: a slack at any one phase of every wheel "
      "gives the per-period law and the full wheel; the observer may read each wheel from the "
      "phase where it is cheapest", "FORMAL", LENS, ("P1",)),
    S("PhaseTwo01Slack3", "period 2 read from its best phase 01 (black at odd times): every code "
      "of length d fails within d + 3 tests (CERT d <= 40; slack 2 false for all d)", "OPEN",
      LENS),
    S("PhaseThree010Slack5", "period 3 phase 010: every code of length d fails within d + 5 tests "
      "(CERT d <= 32; slack 4 false for all d)", "OPEN", LENS),
    S("PhaseThree101Slack2", "period 3 phase 101: every code of length d fails within d + 2 tests "
      "(CERT d <= 32; slack 1 false for all d)", "OPEN", LENS),
    S("OneRunFamilyDies", "every hub 1^(q-1)0 (one black run per period), q >= 2, kills every "
      "non-empty half-line; contains period 2", "OPEN", LENS),
    S("OneRunBand", "uniformly in q and d: every code of length d <= q - 4 fails within d + 2 "
      "tests of the hub 1^(q-1)0, and each 1^(q-1)0 is a hub", "FORMAL", LENS,
      ("OneRunFamilyDies",)),
)

NEW_SPOKES = (
    Spoke(("WheelDies",), "HalfLineDiesAll", "wheelDies_iff", "DriveWheel.lean", iff=True),
    Spoke(("WheelDies",), "P1", "problem1_of_wheelDies", "DriveWheel.lean"),
    Spoke(("PhaseTwo01Slack3",), "TestCountLinear2", "testCountLinear_two_of_phase",
          "TurnCost.lean"),
    Spoke(("PhaseThree010Slack5", "PhaseThree101Slack2"), "TestCountLinear3",
          "testCountLinear_three_of_phases", "TurnCost.lean"),
    Spoke(("OneRunFamilyDies",), "HalfLineDies2", "halfLineDies_two_of_oneRunFamily",
          "OneRunFamily.lean"),
    Spoke(("WheelDies",), "OneRunFamilyDies", "oneRunFamilyDiesFrom_of_wheelDies",
          "OneRunFamily.lean"),
)

HUB_RULE = "(hub rule)"


def hub_spokes() -> Tuple[Spoke, ...]:
    """The hub rule: ``HubsOfDivisors<p> <=> HalfLineDies<p>`` (``halfLineDies_iff_wheel``) and
    ``WheelDies => HubsOfDivisors<p>`` for every declared ``p``."""
    out = []
    for p in PERIODS:
        h, d = f"HubsOfDivisors{p}", f"HalfLineDies{p}"
        if h in tw.STATEMENTS and d in tw.STATEMENTS:
            out.append(Spoke((h,), d, f"halfLineDies_iff_wheel {HUB_RULE}", "DriveWheel.lean",
                             iff=True))
            out.append(Spoke(("WheelDies",), h, f"wheelDies_iff {HUB_RULE}", "DriveWheel.lean"))
    return tuple(out)


NEW_FACT_LEAN = {
    "TurnCostExact": "TurnCost.testSlack_of_shift_count, testSlack_phase_transfer, "
                     "testSlackUpTo_phase_transfer, testSlack_wheelTurn_transfer; attained: "
                     "TurnCostData.not_phaseTwo10_four, not_phaseThree100_seven",
    "BestPhaseSuffices": "TurnCost.testCountLinear_of_phases, wheelDies_of_phases, "
                         "wordDies_of_phase, testCountLinear_two_of_phase, "
                         "testCountLinear_three_of_phases",
    "OneRunBand": "OneRunFamily.wheelRep_oneRun, failsWithinTests_of_initial_blackRun, oneRun_band, "
                  "oneRunDies_iff_long",
}

NEW_EVIDENCE = {
    "PhaseTwo01Slack3": ("CERT d <= 40 (TurnCostData.phaseTwo01_slack); slack 2 false for all d "
                         "(not_phaseTwo01_two)", "EMP slack 3 on d <= 34 (rule30_round37)"),
    "PhaseThree010Slack5": ("CERT d <= 32 (TurnCostData.phaseThree010_slack); slack 4 false for "
                            "all d (not_phaseThree010_four)",),
    "PhaseThree101Slack2": ("CERT d <= 32 (TurnCostData.phaseThree101_slack); slack 1 false for "
                            "all d (not_phaseThree101_one)",),
    "OneRunFamilyDies": ("FORMAL band d <= q - 4 for every q (oneRun_band)",
                         "EMP slack <= 7 for q = 2..20 on d <= 30 "
                         "(rule30_round37/one_run_family37_output.txt)"),
    "TurnCostExact": ("EMP the bound holds on all 2876 ordered phase pairs of the wheels of period "
                      "<= 8 on d <= 28; some pair attains it in 66 of 69 wheels; from the best phase alone it "
                      "predicts 84 of the 401 other phases exactly (rule30_round37/)",),
    "WheelDies": ("CERT every hub of period <= 8 on d <= 24 (DriveWheelData.wheelTable_sound)",),
}

_STD = ("propext", "Classical.choice", "Quot.sound")
NEW_AXIOMS = {n: _STD for n in (
    "halfLineDies_iff_wheel", "wheelDies_iff", "problem1_of_wheelDies",
    "testSlack_of_shift_count", "testSlack_phase_transfer", "testCountLinear_of_phases",
    "testCountLinear_two_of_phase", "testCountLinear_three_of_phases", "wheelRep_oneRun",
    "oneRun_band", "oneRunDies_iff_long", "halfLineDies_two_of_oneRunFamily",
    "oneRunFamilyDiesFrom_of_wheelDies")}


def extend() -> None:
    """Add Round 37 to the wheel (idempotent)."""
    tw34.extend()
    for s in NEW_STATEMENTS:
        tw.STATEMENTS[s.name] = s
    have = {(sp.premises, sp.conclusion, sp.lean) for sp in tw.SPOKES}
    extra = NEW_SPOKES + hub_spokes() + tw34.divisor_spokes() + tw33.instantiation_spokes()
    for sp in extra:
        key = (sp.premises, sp.conclusion, sp.lean)
        if key not in have:
            tw.SPOKES = tw.SPOKES + (sp,)
            have.add(key)
    tw.FACT_LEAN.update(NEW_FACT_LEAN)
    for k, v in NEW_EVIDENCE.items():
        tw.EVIDENCE[k] = v
    tw.AXIOM_FOOTPRINT.update(NEW_AXIOMS)


_HERE = os.path.dirname(os.path.abspath(__file__))
ROWS37 = os.path.join(_HERE, "_data", "r37_rows.json")


def carriers() -> List[Dict[str, object]]:
    rows = list(tw34.carriers())
    ids = {r.get("id") for r in rows}
    if os.path.exists(ROWS37):
        rows += [r for r in json.load(open(ROWS37)) if r.get("id") not in ids]
    return rows


_SYN = {"turn": {"turn", "phase", "rotation", "rotate"}, "cost": {"cost", "price", "slack"},
        "hub": {"hub", "hubs", "lyndon", "necklace", "spoke"},
        "best": {"best", "cheapest", "least", "perspective", "observer"}}


def lens_reader37(question: str, min_hits: int = 2) -> List[Tuple[int, str]]:
    extend()
    q = {tw33._stem(w) for w in tw33._words(question)}
    for key, syn in _SYN.items():
        if q & syn:
            q |= syn | {key}
    q |= set(re.findall(r"\d+", question))
    out = []
    for s in NEW_STATEMENTS:
        name_words = re.findall(r"[A-Z][a-z0-9]*|[0-9]+", s.name)
        bag = {tw33._stem(w) for w in tw33._words(" ".join(name_words) + " " + s.text + " " +
                                                  tw.FACT_LEAN.get(s.name, "") + " " + s.lens)}
        hits = len(q & bag)
        if hits >= min_hits:
            out.append((hits, s.name))
    out.sort(key=lambda h: (-h[0], h[1]))
    return out


def theorem37_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    extend()
    a = arg.strip()
    if a.startswith("ledger"):
        q = a[len("ledger"):].strip().lower()
        rows = [r for r in carriers() if str(r.get("id", "")).lower() == q] or [
            r for r in carriers()
            if all(w in (str(r.get("claim", "")) + " " + " ".join(r.get("lean", []) or [])).lower()
                   for w in q.split() if len(w) > 2)][:8]
        if not rows:
            return False, "no ledger row matches", {"status": "none"}
        out = [f"{r['id']} [{r.get('class')}, {r.get('status')}] {r.get('claim')} "
               f"| Lean: {'; '.join(r.get('lean', []) or []) or '-'}" for r in rows]
        return True, "\n".join(out), {"status": "rows", "count": len(rows)}
    ok, text, info = tw34.theorem34_text(arg)
    m = re.fullmatch(r"derive\s+(\w+)\s*=>\s*HalfLineDies(\d+)", a)
    if ok and m and int(m.group(2)) >= 1:
        text += "\n" + hub_form_line(int(m.group(2)))
    return ok, text, info


def hub_form_line(p: int) -> str:
    """The hub reading of ``HalfLineDies<p>`` (``halfLineDies_iff_wheel``)."""
    try:
        from glm_universal.reasoning import hub_index as hx
    except ImportError:  # standalone
        import hub_index as hx  # type: ignore
    need = sum(len(hx.hubs(q)) for q in hx.divisors(p))
    return (f"HUB FORM  HalfLineDies{p} <=> every hub of every divisor of {p} kills "
            f"[halfLineDies_iff_wheel]: {need} hubs (periods {hx.divisors(p)}) instead of "
            f"{2 ** p - 1} words; each proved hub also fills every multiple period")


def discuss37_text(question: str) -> Tuple[bool, str, Dict[str, object]]:
    extend()
    ok, text, info = tw34.discuss34_text(question)
    hits = lens_reader37(question)
    if not hits:
        return ok, text, info
    lines = [text, "ROUND 37 LENSES (drive wheel, turn cost, best phase, hub family; Lean package)"]
    for _, name in hits[:4]:
        lines += tw33._describe(name)
    return True, "\n".join(lines), dict(info if isinstance(info, dict) else {},
                                        lens37_hits=[n for _, n in hits])

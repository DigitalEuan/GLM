#!/usr/bin/env python3
"""Round 37: build the GLM data files of the Round 37 overlay (exact integers only).

* ``_data/r37_hubs.json`` -- one record per hub of period <= 8:
  the Lean-certified slack on code lengths d <= 24 (``DriveWheelData.wheelTable``, Round 36, CERT),
  the measured slack of every phase (``wheel_phases37.py``, EMP; d <= 34 for p <= 4, d <= 30 for
  p = 5, 6, d <= 28 for p = 7, 8), the best phase, and the Round 37 Lean results for the hubs of
  periods 2 and 3 (``TurnCostData``).
* ``_data/r37_todo.json`` -- the To Do list of ``AUDIT.md`` at Round 37 (for ``tool next``).
* ``_data/r37_rows.json`` -- ledger rows C343-C350 (also in the Lean package's ``claims.csv``).

Run from ``rule30_round37/``: ``python3 make_r37_data.py``.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "glm_overlay", "glm_universal", "reasoning", "_data")

#: DriveWheelData.wheelTable (Round 36): (p, hub, slack on d <= 24), certified by wheelTable_check
WHEEL_TABLE = [
    (1, 1, 2), (2, 1, 5), (3, 1, 8), (3, 3, 3), (4, 1, 3), (4, 3, 2), (4, 7, 5),
    (5, 1, 4), (5, 3, 3), (5, 5, 1), (5, 7, 4), (5, 11, 4), (5, 15, 4),
    (6, 1, 2), (6, 3, 4), (6, 5, 3), (6, 7, 3), (6, 11, 3), (6, 13, 5), (6, 15, 5), (6, 23, 7),
    (6, 31, 4),
    (7, 1, 1), (7, 3, 4), (7, 5, 4), (7, 7, 5), (7, 9, 3), (7, 11, 5), (7, 13, 8), (7, 15, 7),
    (7, 19, 4), (7, 21, 4), (7, 23, 4), (7, 27, 8), (7, 29, 4), (7, 31, 3), (7, 43, 5), (7, 47, 5),
    (7, 55, 6), (7, 63, 6),
    (8, 1, 2), (8, 3, 3), (8, 5, 3), (8, 7, 2), (8, 9, 4), (8, 11, 9), (8, 13, 4), (8, 15, 7),
    (8, 19, 3), (8, 21, 4), (8, 23, 2), (8, 25, 2), (8, 27, 7), (8, 29, 6), (8, 31, 2), (8, 37, 3),
    (8, 39, 4), (8, 43, 6), (8, 45, 4), (8, 47, 8), (8, 53, 3), (8, 55, 4), (8, 59, 3), (8, 61, 3),
    (8, 63, 5), (8, 87, 5), (8, 91, 11), (8, 95, 3), (8, 111, 3), (8, 127, 3)]

EMP_FILES = [("wheel_phases37_p4_d34.json", range(1, 5)), ("wheel_phases37_p6_d30.json", range(5, 7)),
             ("wheel_phases37_p8_d28.json", range(7, 9))]

LEAN_EXTRA = {
    "2,1": ["TurnCostData.phaseTwo01_slack: the best phase 01 (word 2) has slack 3 on d <= 40 (CERT); "
            "not_phaseTwo01_two: slack 2 false for all d; not_phaseTwo10_four: the hub phase 10 "
            "needs 5 = 3 + turn cost 2",
            "TurnCost.testCountLinear_two_of_phase: TestSlack (driveN 2 2) 3 -> TestCountLinear 2 5 "
            "(all d; the optimal period-2 slack from one phase)",
            "OneRunFamily: the hub 10 is the case q = 2 of the family 1^(q-1)0 "
            "(halfLineDies_two_of_oneRunFamily)"],
    "3,1": ["TurnCostData.phaseThree010_slack: best phase 010 (word 2) slack 5 on d <= 32 (CERT); "
            "not_phaseThree010_four; not_phaseThree100_seven: the hub phase 100 needs 8 = 5 + 3",
            "TurnCost.testCountLinear_three_of_phases: phases 010 (slack 5) and 101 (slack 2) -> "
            "TestCountLinear 3 8 (all d)"],
    "3,3": ["TurnCostData.phaseThree101_slack: best phase 101 (word 5) slack 2 on d <= 32 (CERT); "
            "not_phaseThree101_one",
            "OneRunFamily.wheelRep_oneRun: 110 is the q = 3 member of the hub family 1^(q-1)0"],
}


#: the Round 37 To Do list (AUDIT.md section 4), open items only plus the three items of this round
TODO = {
    "round": 37,
    "frontier": "GLM.Rule30.TurnCostData.frontier_round37",
    "narrowest": ["PhaseTwo01Slack3", "HalfLineDies2", "TestCountLinear2"],
    "hub_first": True,
    "items": [
        {"id": 39, "title": "A uniform proof for an infinite family of hubs", "kind": "Lean",
         "status": "partly R37", "bears_on": "OneRunFamilyDies",
         "target": "OneRunFamilyDiesFrom q0: every hub 1^(q-1)0, q >= q0, kills every half-line; "
                   "the band d <= q - 4 is proved (oneRun_band), codes of length d >= q - 3 remain "
                   "(oneRunDies_iff_long); q0 = 2 contains HalfLineDies 2",
         "finite_step": "compute the exact survivor sets of the hubs 1^(q-1)0 after the first two "
                        "runs for q <= 24 and look for a q-uniform description (To Do 43)",
         "script": "python3 rule30_round37/one_run_family37.py 20 30", "cost": 3},
        {"id": 40, "title": "The cost of a turn", "kind": "EMP -> Lean", "status": "done R37",
         "bears_on": "TestCountLinear2",
         "target": "exact cost m + tests skipped (testSlack_phase_transfer); attained by some phase pair "
                   "in 66 of 69 wheels",
         "finite_step": None, "cost": 1},
        {"id": 41, "title": "Index the half-line family by hubs", "kind": "GLM",
         "status": "done R37", "bears_on": None, "target": "tool hub, tool hubs, hub-first tool next",
         "finite_step": None, "cost": 1},
        {"id": 42, "title": "Period 2 from its best phase", "kind": "Lean", "status": "open",
         "bears_on": "PhaseTwo01Slack3",
         "target": "TestSlack (driveN 2 2) 3 for all d (phase 01: black at odd times); gives the "
                   "optimal TestCountLinear 2 5 (testCountLinear_two_of_phase)",
         "finite_step": "measure the window distribution of the surviving codes at each test of "
                        "the phase 01 (each test is one window read, blackRun_word with r = 1; "
                        "To Do 38 at the best phase)",
         "script": "python3 rule30_round37/wheel_phases37.py 2 34", "cost": 2},
        {"id": 43, "title": "The one-run family beyond the band", "kind": "EMP -> Lean",
         "status": "open", "bears_on": "OneRunFamilyDies",
         "target": "for every q, the codes of length q - 3 <= d <= 2q fail within d + c tests of "
                   "1^(q-1)0 for a fixed c (measured: c = 7 suffices for q <= 20, d <= 30)",
         "finite_step": "exact survivor sets after runs 0 and 1 for q <= 24",
         "script": "python3 rule30_round37/one_run_family37.py 20 30", "cost": 3},
        {"id": 44, "title": "The GLM proposes spokes", "kind": "GLM", "status": "open",
         "bears_on": None,
         "target": "the GLM reads proved spokes but proposes none; measure how many of a round's "
                   "new spokes it could have proposed beforehand (Round 37: none; it has no proposal step)",
         "finite_step": None,
         "ask": "which kind of proposal should count: a statement with a Lean stub, or a stated "
                "implication between existing wheel statements?", "cost": 3},
        {"id": 29, "title": "The sideways reader for period 2", "kind": "Lean",
         "status": "partly R33", "bears_on": "HalfLineDies2",
         "target": "an invariant of the sideways map, preserved for admissible inputs, that "
                   "excludes finite rows",
         "finite_step": "search low-degree Boolean invariants of consecutive column pairs",
         "script": "python3 scripts/sideways_period_two.py", "cost": 3},
        {"id": 38, "title": "Window distribution after the edge", "kind": "Lean", "status": "open",
         "bears_on": "TestCountLinear2",
         "target": "at most a fraction theta < 1 of the survivors show a run's word, amortised",
         "finite_step": "exact window counts after the edge for the best phases (periods 2, 3)",
         "script": "python3 rule30_round37/wheel_phases37.py 3 30", "cost": 3},
        {"id": 35, "title": "Does period 4 have a finite slack?", "kind": "EMP -> Lean",
         "status": "partly R35", "bears_on": "TestCountLinear4",
         "target": "TestCountLinear 4 7 for all d", "finite_step": None, "cost": 4},
    ],
}

#: ledger rows of Round 37 (same text as claims.csv C343-C350)
ROWS = [
    {"id": "C343", "class": "FORMAL", "status": "proved",
     "claim": "The exact cost of a turn: starting the clock m steps later costs m plus the tests "
              "skipped; between phases a and b of a wheel (a + m = b mod p) slack(a) <= slack(b) + "
              "m + testsBefore(phase a, m); also on finite ranges",
     "lean": ["TurnCost.testSlack_of_shift_exact", "testSlack_of_shift_count",
              "testSlackUpTo_of_shift_count", "testSlack_phase_transfer",
              "testSlackUpTo_phase_transfer", "testSlack_wheelTurn_transfer"]},
    {"id": "C344", "class": "FORMAL", "status": "proved",
     "claim": "The observer's best phase: a slack at any one phase of every wheel gives the "
              "per-period law (slack c + 2(p - 1)) and WheelDies; period 2 from the phase 01 with "
              "slack 3 and period 3 from the phases 010 (slack 5) and 101 (slack 2) give the "
              "optimal laws TestCountLinear 2 5 and TestCountLinear 3 8",
     "lean": ["TurnCost.wordDies_of_phase", "testCountLinear_of_phases", "wheelDies_of_phases",
              "testCountLinear_two_of_phase", "testCountLinear_three_of_phases"]},
    {"id": "C345", "class": "CERT", "status": "proved",
     "claim": "Best phases certified: phase 01 slack 3 on d <= 40 (2 false for all d), the hub "
              "phase 10 needs 5; phase 010 slack 5 and phase 101 slack 2 on d <= 32 (4 and 1 false "
              "for all d), the hub phase 100 needs 8: the gaps equal the proved turn cost",
     "lean": ["TurnCostData.phaseTwo01_slack", "not_phaseTwo01_two", "not_phaseTwo10_four",
              "phaseThree010_slack", "phaseThree101_slack", "not_phaseThree100_seven",
              "frontier_round37"]},
    {"id": "C346", "class": "EMP", "status": "measured",
     "claim": "Per-phase slack of every wheel of period <= 8 on d <= 28: worst phase per period "
              "2, 5, 8, 5, 6, 11, 12, 14; best phase per wheel at most 2, 3, 5, 3, 3, 5, 5, 6; the "
              "proved turn cost holds on all 2876 ordered phase pairs, some pair attains it in 66 of the "
              "69 wheels with more than one phase, and from the best phase alone it predicts 84 of "
              "the 401 other phases exactly",
     "lean": []},
    {"id": "C347", "class": "FORMAL", "status": "proved",
     "claim": "The one-run family 1^(q-1)0: a hub for every q >= 2; every code of length "
              "d <= q - 4 fails within d + 2 tests (uniform in q and d); the hub kills iff it "
              "kills the codes of length >= q - 3; the whole family contains HalfLineDies 2",
     "lean": ["OneRunFamily.wheelRep_oneRun", "failsWithinTests_of_initial_blackRun",
              "oneRun_band", "oneRunDies_iff_long", "halfLineDies_two_of_oneRunFamily",
              "oneRunFamilyDiesFrom_of_wheelDies"]},
    {"id": "C348", "class": "EMP", "status": "measured",
     "claim": "The one-run family measured: slack at most 7 for q = 2..20 on d <= 30; the band "
              "bound (excess <= 2 on d <= q - 4) holds on the range",
     "lean": []},
    {"id": "C349", "class": "OPEN", "status": "open",
     "claim": "OneRunFamilyDiesFrom q0 (To Do 39) and TestSlack (driveN 2 2) 3 for all d "
              "(To Do 42) are open targets",
     "lean": ["OneRunFamily.OneRunFamilyDiesFrom", "OneRunFamilyDies"]},
    {"id": "C350", "class": "EMP", "status": "measured",
     "claim": "GLM indexed by hubs (Round 37 overlay): hub index exact on all 8178 non-white words "
              "of period <= 12; consultation 0/11 before, 11/11 after (development questions)",
     "lean": []},
]


def main():
    emp = {}
    for fname, periods in EMP_FILES:
        data = json.load(open(os.path.join(HERE, fname)))
        for w in data["wheels"]:
            if w["p"] in periods:
                emp[(w["p"], w["hub"])] = (w, data["D"])
    hubs = {}
    for p, j, c in WHEEL_TABLE:
        w, D = emp[(p, j)]
        ps = w["phase_slacks"]
        best = min(range(p), key=lambda s: (ps[s], s))
        key = f"{p},{j}"
        rec = {"p": p, "hub": j, "cert_slack": c, "cert_range": 24,
               "cert_lean": "DriveWheelData.wheelTable_sound", "phase_slacks": ps,
               "best_phase": best, "emp_range": D}
        if p >= 4 and j == 2 ** (p - 1) - 1:
            band = (f"; oneRun_band: every code of length d <= {p - 4} fails within d + 2 tests"
                    if p >= 5 else "; the band d <= q - 4 is empty for q = 4")
            rec.setdefault("lean_extra", []).append(
                f"OneRunFamily.wheelRep_oneRun: the q = {p} member of the hub family 1^(q-1)0"
                + band)
        if key in LEAN_EXTRA:
            rec["lean_extra"] = LEAN_EXTRA[key] + rec.get("lean_extra", [])
        hubs[key] = rec
    os.makedirs(DATA, exist_ok=True)
    json.dump({"round": 37, "hubs": hubs}, open(os.path.join(DATA, "r37_hubs.json"), "w"), indent=1)
    print(f"r37_hubs.json: {len(hubs)} hubs")
    json.dump(TODO, open(os.path.join(DATA, "r37_todo.json"), "w"), indent=1)
    print(f"r37_todo.json: {len(TODO['items'])} items")
    json.dump(ROWS, open(os.path.join(DATA, "r37_rows.json"), "w"), indent=1)
    print(f"r37_rows.json: {len(ROWS)} rows")


if __name__ == "__main__":
    main()

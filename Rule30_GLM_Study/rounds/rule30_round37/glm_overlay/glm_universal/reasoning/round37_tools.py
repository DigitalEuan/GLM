"""``glm_universal.reasoning.round37_tools`` -- Round 37 of the Rule 30 study: ``tool next``
proposes **hubs** (To Do 41), and ``tool requirements`` states the exact improvement requirements.

``tool next``
-------------
The planner's licensing rule of Round 33 (finite step first, narrowest rung first, cheapest first),
applied first to the **hubs** and then to the To Do list (``_data/r37_todo.json``).  A hub is
licensed when it has a finite, checkable next step (a per-phase certificate or measurement).  Hubs
are ranked by period (the smallest open period is the narrowest rung: every proof for a hub of
period ``q`` fills every multiple period), then by the slack of their best phase (cheapest first).
Each pick names the hub's best phase, the Lean statement to prove, the proved implication it would
feed, and the command of the next finite step.

``tool requirements``
---------------------
The exact list of what is still required, each with its Lean statement, what is already proved or
certified, and the measured numbers, in four groups: Problem 1 through the wheel, the per-period
laws through the best phase, the hub family of To Do 39, and the GLM itself.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple

try:
    from glm_universal.reasoning import hub_index as hx
    from glm_universal.reasoning import next_step as nxs
except ImportError:  # standalone
    import hub_index as hx  # type: ignore
    import next_step as nxs  # type: ignore

_HERE = os.path.dirname(os.path.abspath(__file__))
TODO37 = os.path.join(_HERE, "_data", "r37_todo.json")

#: hubs with a proved implication from their best phase(s) to an optimal per-period law
PHASE_SPOKES = {
    (2, 1): ("PhaseTwo01Slack3", "TestSlack (driveN 2 2) 3",
             "testCountLinear_two_of_phase: TestSlack (driveN 2 2) 3 -> TestCountLinear 2 5"),
    (3, 1): ("PhaseThree010Slack5", "TestSlack (driveN 3 2) 5",
             "testCountLinear_three_of_phases (with phase 101 of hub 3) -> TestCountLinear 3 8"),
    (3, 3): ("PhaseThree101Slack2", "TestSlack (driveN 3 5) 2",
             "testCountLinear_three_of_phases (with phase 010 of hub 1) -> TestCountLinear 3 8"),
}


def hub_picks(n: int) -> List[dict]:
    table = hx.load_table()
    picks = []
    for key, rec in table.items():
        q, j = rec["p"], rec["hub"]
        if q == 1:
            continue  # proved for every d (halfLineDies_one)
        ps = rec.get("phase_slacks") or []
        best = rec.get("best_phase", 0)
        picks.append({"q": q, "hub": j, "best": best, "best_slack": ps[best] if ps else None,
                      "worst": max(ps) if ps else None, "rec": rec})
    picks.sort(key=lambda h: (h["q"], h["best_slack"] if h["best_slack"] is not None else 99,
                              h["hub"]))
    return picks[:n]


def next_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    a = (arg or "").strip()
    n = int(a) if a.isdigit() else 3
    try:
        data = json.load(open(TODO37))
    except (OSError, ValueError) as e:
        return False, f"next: Round 37 To Do data missing ({e})", {}
    picks = hub_picks(n)
    out = [f"NEXT (Round {data['round']}; frontier {data['frontier']}; the unit of work is a HUB: "
           f"one proof per hub fills its whole wheel and every multiple period "
           f"[halfLineDies_iff_wheel])"]
    for r, h in enumerate(picks, 1):
        q, j, b = h["q"], h["hub"], h["best"]
        word_b = hx.word_str(q, hx.turn(q, j, b))
        sp = PHASE_SPOKES.get((q, j))
        target = (sp[1] if sp else f"TestSlack (driveN {q} {hx.turn(q, j, b)}) "
                  f"{h['best_slack']}  (best phase), or WordDies (driveN {q} {j})")
        out += [f"HUB PICK {r}: period {q} hub {j} [{hx.word_str(q, j)}], best phase {b} "
                f"[{word_b}] slack {h['best_slack']} (worst phase {h['worst']}; EMP d <= "
                f"{h['rec']['emp_range']})",
                "  COLUMN 1 — LANGUAGE",
                f"    Take this hub now: it belongs to "
                f"{'the smallest open period' if q == picks[0]['q'] else 'the next open period'} "
                f"({q}), and it is cheapest when read from phase {b}; one proof here fills its "
                f"{q} phases and every multiple period.",
                "  COLUMN 2 — MATHEMATICS",
                f"    target: {target} for all d",
                f"    feeds: {sp[2] if sp else 'testCountLinear_of_phases (one phase per wheel)'}",
                "    turn cost to every other phase: testSlack_phase_transfer (proved; attained by some "
                "phase pair in 66 of 69 wheels, EMP)",
                "  COLUMN 3 — SCRIPT",
                f"    python3 rule30_round37/wheel_phases37.py {q} 34   # the per-phase slacks of "
                f"every wheel up to period {q}"]
    ok, text, info = _todo_text(data, 3)
    out.append(text)
    return True, "\n".join(out), {"hub_picks": [(h["q"], h["hub"]) for h in picks],
                                  "todo": info}


def _todo_text(data: dict, n: int) -> Tuple[bool, str, Dict[str, object]]:
    licensed, asked, refused = nxs.rank(data)
    out = ["TO DO (after the hubs; planner's licensing rule)"]
    for rnk, it in enumerate(licensed[:n], 1):
        out.append(f"  PICK {rnk}: To Do {it['id']} — {it['title']} [{it['kind']}, {it['status']}]: "
                   f"{it['finite_step']}  | {it.get('script', '')}")
    for it in asked:
        out.append(f"  ASK  To Do {it['id']} — {it['title']}: {it['ask']}")
    for it in refused:
        out.append(f"  REFUSED  To Do {it['id']} — {it['title']}: no finite step is licensed "
                   f"(target: {it['target']}); it needs an idea, not more search")
    return True, "\n".join(out), {"picks": [i["id"] for i in licensed[:n]]}


def _per_period_rows() -> List[str]:
    table = hx.load_table()
    rows = []
    for p in range(1, 9):
        recs = [r for r in table.values() if p % r["p"] == 0]
        worst = max(max(r["phase_slacks"]) for r in recs)
        best = max(min(r["phase_slacks"]) for r in recs)
        hub_r36 = max(r["cert_slack"] for r in recs) + 2 * (p - 1)
        rng = max(r["emp_range"] for r in recs if r["p"] == p)
        rows.append(f"    period {p} (d <= {rng}): {len(recs)} hubs of its divisors (not "
                    f"{2 ** p - 1} words); per-period slack (worst phase) {worst}; best-phase "
                    f"slack (worst wheel) {best}; Round 36 route (hub CERT d <= 24 + 2(p-1)) "
                    f"{hub_r36}")
    return rows


def requirements_text(arg: str) -> Tuple[bool, str, Dict[str, object]]:
    lines = ["REQUIREMENTS (Round 37): what is still needed, exactly, with what is already in hand",
             "REQUIREMENT R1 — Problem 1 through the wheel",
             "    need: WheelDies (every hub kills every non-empty half-line), for all code lengths d",
             "    in hand: WheelDies <-> HalfLineDies p for every p (wheelDies_iff) -> Problem 1 "
             "(problem1_of_wheelDies); period 1 proved (halfLineDies_one); every hub of period <= 8 "
             "certified on d <= 24 (DriveWheelData.wheelTable_sound)",
             "    gap: no finite range decides it (no_finite_certificate_problem1); a proof uniform "
             "in d is required for each hub of period >= 2",
             "REQUIREMENT R2 — per-period laws from the observer's best phase",
             "    need (narrowest): TestSlack (driveN 2 2) 3 for all d  -> TestCountLinear 2 5 "
             "(testCountLinear_two_of_phase) -> HalfLineDies 2",
             "    in hand: CERT d <= 40 (phaseTwo01_slack); slack 2 false (not_phaseTwo01_two); the "
             "hub phase needs exactly 5 = 3 + turn cost 2",
             "    period 3: TestSlack (driveN 3 2) 5 and TestSlack (driveN 3 5) 2 -> TestCountLinear 3 "
             "8 (testCountLinear_three_of_phases); CERT d <= 32 for both",
             "    measured slacks per period (EMP; exact search):"] + _per_period_rows() + [
             "REQUIREMENT R3 — the hub family 1^(q-1)0 (To Do 39)",
             "    need: OneRunFamilyDiesFrom q0 for some q0 (q0 = 2 contains HalfLineDies 2: "
             "halfLineDies_two_of_oneRunFamily)",
             "    in hand: every 1^(q-1)0 is a hub (wheelRep_oneRun); codes of length d <= q - 4 "
             "fail within d + 2 tests, uniformly in q and d (oneRun_band); only codes of length "
             "d >= q - 3 remain (oneRunDies_iff_long)",
             "    measured: slack <= 7 for q = 2..20 on d <= 30 (EMP); a uniform slack c for the "
             "band q - 3 <= d <= 2q would be the next uniform step (To Do 43)",
             "REQUIREMENT R4 — the GLM",
             "    in hand: hub index exact on all non-white words of period <= 12 (8178 words); "
             "tool next proposes hubs; the wheel derives HalfLineDies p from WheelDies through "
             "HubsOfDivisors p",
             "    gap: the GLM reads proved spokes but proposes none (To Do 44); it cannot prove a "
             "statement uniform in d; its consultation questions are development questions, not "
             "held out"]
    return True, "\n".join(lines), {"status": "requirements"}

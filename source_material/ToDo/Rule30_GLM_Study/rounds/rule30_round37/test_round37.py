#!/usr/bin/env python3
"""Round 37 self-test.  Run from the directory holding ``GLM.py`` after ``setup_round37.sh``.
Prints ``round 37: all checks pass`` or the first failure."""
import json
import os
import subprocess
import sys

from glm_universal.reasoning import hub_index as hx
from glm_universal.reasoning import theorem_wheel_round37 as tw37

HERE = os.path.dirname(os.path.abspath(__file__))


def ask(q):
    r = subprocess.run([sys.executable, "GLM.py", "-q", q], capture_output=True, text=True)
    return r.stdout


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        sys.exit(1)


def main():
    # the hub index is exactly the Lean reduction exists_wheelRep, on every word of period <= 12
    bad = 0
    total = 0
    for p in range(1, 13):
        for k in range(1, 2 ** p):
            total += 1
            q, j, s = hx.to_hub(p, k)
            ok = p % q == 0 and hx.is_hub(q, j) and all(
                hx.drive(q, j, t) == hx.drive(p, k, t + s) for t in range(2 * p))
            bad += not ok
    check(f"hub index exact on all {total} non-white words of period <= 12", bad == 0 and
          total == 8178)
    check("hub counts match DriveWheelData.wheelReps_count",
          [len(hx.hubs(p)) for p in range(1, 13)] == [1, 1, 2, 3, 6, 9, 18, 30, 56, 99, 186, 335])
    # the exact turn cost, as in TurnCostData (attained cases)
    check("turn cost 10 <- 01 is 2 (5 = 3 + 2)", hx.turn_cost(2, 1, 0, 1) == 2)
    check("turn cost 100 <- 010 is 3 (8 = 5 + 3)", hx.turn_cost(3, 1, 0, 2) == 3)
    # the measured per-phase table never contradicts the proved turn cost
    for f in ("wheel_phases37_p8_d28.json", "wheel_phases37_p6_d30.json",
              "wheel_phases37_p4_d34.json"):
        path = os.path.join(HERE, f)
        if os.path.exists(path):
            check(f"{f}: 0 violations of testSlackUpTo_phase_transfer",
                  json.load(open(path))["violations"] == 0)
    # the wheel
    tw37.extend()
    a = ask("tool theorem derive WheelDies => HalfLineDies5")
    check("tool theorem derives HalfLineDies5 from WheelDies by the hub rule",
          "halfLineDies_iff_wheel" in a)
    a = ask("tool theorem derive PhaseTwo01Slack3 => TestCountLinear2")
    check("tool theorem: best phase 01 gives TestCountLinear2", "testCountLinear_two_of_phase" in a)
    a = ask("tool theorem derive HalfLineDies2 => OneRunFamilyDies")
    check("tool theorem does not derive the family from period 2", "NOT DERIVABLE" in a)
    a = ask("tool theorem derive HalfLineDies4 => HalfLineDies2")
    check("regression: the divisor rule still answers", "halfLineDies_of_dvd" in a)
    a = ask("tool hub 4 14")
    check("tool hub 4 14 -> period 4 hub 7", "period 4 hub 7" in a)
    a = ask("tool hub 6 42")
    check("tool hub 6 42 -> period 2 hub 1", "period 2 hub 1" in a)
    a = ask("tool hubs 8")
    check("tool hubs 8 -> 30 hubs", "30 hubs" in a)
    a = ask("tool next")
    check("tool next proposes a hub first", "HUB PICK 1: period 2 hub 1" in a)
    a = ask("tool requirements")
    check("tool requirements answers", "REQUIREMENT R1" in a and "REQUIREMENT R4" in a)
    a = ask("tool slack 2 1 12")
    check("regression: tool slack still answers", "COLUMN 3" in a)
    print("round 37: all checks pass")


if __name__ == "__main__":
    main()

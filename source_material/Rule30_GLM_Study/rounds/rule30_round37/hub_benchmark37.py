#!/usr/bin/env python3
"""Round 37, To Do 41: measured effect of indexing the half-line family by hubs.

Exact integers for every computed value; floats only for wall-clock time.  Run from the directory
holding GLM.py after setup_round37.sh (it imports the installed hub index), with the exact search
binary ``test_slack34`` in the current directory or given as the first argument:

    PYTHONPATH=. python3 rule30_round37/hub_benchmark37.py [./test_slack34] > rule30_round37/hub_benchmark37_output.txt

Measures
1. correctness of the hub index (every non-white word of period <= 12);
2. work: searches needed to cover every word of periods 1..P (words vs hubs), and the wall-clock
   time of the exact search over all words vs over the hubs only (p <= 7, d <= 20);
3. slack bounds, on the same measured range (EMP, from wheel_phases37_*.json):
   true per-period slack (worst phase) vs the Round 36 route (hub slack + 2(p - 1)) vs the Round 37
   route (best phase + exact turn cost, testSlack_phase_transfer); and how often the Round 37
   prediction is attained exactly.
"""
import json
import os
import subprocess
import sys
import time

from glm_universal.reasoning import hub_index as hx

HERE = os.path.dirname(os.path.abspath(__file__))


def emp_wheels():
    out = {}
    for fname, periods in (("wheel_phases37_p4_d34.json", range(1, 5)),
                           ("wheel_phases37_p6_d30.json", range(5, 7)),
                           ("wheel_phases37_p8_d28.json", range(7, 9))):
        data = json.load(open(os.path.join(HERE, fname)))
        for w in data["wheels"]:
            if w["p"] in periods:
                out[(w["p"], w["hub"])] = (w["phase_slacks"], data["D"])
    return out


def main():
    binary = sys.argv[1] if len(sys.argv) > 1 else "./test_slack34"
    print("# Round 37 hub benchmark (To Do 41)")
    # 1. correctness
    total = bad = 0
    for p in range(1, 13):
        for k in range(1, 2 ** p):
            total += 1
            q, j, s = hx.to_hub(p, k)
            bad += not (p % q == 0 and hx.is_hub(q, j) and
                        all(hx.drive(q, j, t) == hx.drive(p, k, t + s) for t in range(2 * p)))
    print(f"1. hub index: {total - bad}/{total} words of period <= 12 mapped to a hub with "
          f"driveN q j t = driveN p k (t + s) (the statement of exists_wheelRep)")
    # 2. work
    print("2. work to cover every word of periods 1..P")
    for P in (4, 8, 12):
        words = sum(2 ** p - 1 for p in range(1, P + 1))
        hubs = sum(len(hx.hubs(p)) for p in range(1, P + 1))
        print(f"   P = {P}: {words} words, {hubs} hubs ({words // hubs}x fewer searches, "
              f"rounded down)")
    D = 20
    t0 = time.perf_counter()
    for p in range(1, 8):
        for k in range(1, 2 ** p):
            subprocess.run([binary, str(p), str(k), "1", str(D)], capture_output=True, check=True)
    t_words = time.perf_counter() - t0
    t0 = time.perf_counter()
    for p in range(1, 8):
        for k in hx.hubs(p):
            subprocess.run([binary, str(p), str(k), "1", str(D)], capture_output=True, check=True)
    t_hubs = time.perf_counter() - t0
    print(f"   exact search, periods 1..7, d <= {D}: all {sum(2 ** p - 1 for p in range(1, 8))} "
          f"words {t_words:.2f} s; the {sum(len(hx.hubs(p)) for p in range(1, 8))} hubs "
          f"{t_hubs:.2f} s (wall clock)")
    # 3. slack bounds on the measured range
    W = emp_wheels()
    print("3. per-period slack on the measured range (EMP): true (worst phase) | Round 36 route "
          "(hub-phase slack + 2(p-1)) | Round 37 route (best phase + exact turn cost)")
    attained = phases = exact_wheels = 0
    for p in range(1, 9):
        recs = [(q, j) for (q, j) in W if p % q == 0]
        true = max(max(W[w][0]) for w in recs)
        r36 = max(W[w][0][0] + 2 * (p - 1) for w in recs)
        r37 = 0
        for (q, j) in recs:
            ps = W[(q, j)][0]
            b = min(range(q), key=lambda s: (ps[s], s))
            # a word of period p that is a turn of hub j of period q: the transfer within the
            # q-wheel (the drive is the same function)
            pred = [ps[b] + (hx.turn_cost(q, j, a, b) if a != b else 0) for a in range(q)]
            r37 = max(r37, max(pred))
            if q == p:
                phases += q
                hit = sum(1 for a in range(q) if pred[a] == ps[a])
                attained += hit
                exact_wheels += hit == q
        rng = max(W[w][1] for w in recs if w[0] == p)
        print(f"   period {p} (d <= {rng}): true {true} | Round 36 route {r36} | Round 37 route "
              f"{r37}")
    nw = len(W)
    print(f"   the Round 37 prediction (best phase + exact cost) equals the measured slack at "
          f"{attained} of {phases} phases; at every phase in {exact_wheels} of {nw} wheels")


if __name__ == "__main__":
    main()

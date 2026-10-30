#!/usr/bin/env python3
"""Round 37, To Do 40: the cost of a turn, measured exactly on every wheel.

Exact integer arithmetic only (no floats, no hashing, no randomness).

For every hub (primitive least turn, ``WheelRep`` in DriveWheel.lean) of period p <= PMAX and
every phase s (the turn ``wheelTurn p hub s``: the same drive read s steps later), this runs the
exact observer-clock excess search ``test_slack34`` (Round 34) for code lengths 1 <= d <= D and
records

    E_s(d) = max over codes S of length d of (failing test number) - d,
    slack_s = max_{d <= D} E_s(d)   (TestSlackUpTo holds with slack c iff slack_s <= c).

Per wheel it reports the phase of least and of greatest slack, the spread, and checks every
pair of phases against the proved turn cost (Round 37, ``testSlack_of_turn_count``):

    slack(phase a) <= slack(phase b) + m + (tests of phase a in its first m times),
    m = (b - a) mod p,

on the finite range in the form the Lean finite-range lemma gives it
(``testSlackUpTo_of_turn_count``): phase b certified on d <= D + m gives phase a on d <= D.
So the check uses E_b on d <= D and E_a on d <= D - m.

Usage: python3 wheel_phases37.py PMAX D [binary] > wheel_phases37_output.txt
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor


def turn(p, k, s):
    """wheelTurn p k s: bit i of the new word is bit (i + s) mod p of the old one."""
    return sum(((k >> ((i + s) % p)) & 1) << i for i in range(p))


def is_hub(p, k):
    if not (0 < k < 2 ** p):
        return False
    ts = [turn(p, k, s) for s in range(p)]
    return all(k <= t for t in ts) and all(ts[s] != k for s in range(1, p))


def hubs(p):
    return [k for k in range(1, 2 ** p) if is_hub(p, k)]


def tests_before(p, k, m):
    return sum((k >> (t % p)) & 1 for t in range(m))


def run(binary, p, k, D):
    out = subprocess.run([binary, str(p), str(k), "1", str(D)], capture_output=True, text=True,
                         check=True).stdout
    E = {}
    for line in out.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        d, e, nmax, wit = line.split()
        E[int(d)] = (int(e), int(nmax), int(wit, 16))
    return E


def main():
    pmax = int(sys.argv[1])
    D = int(sys.argv[2])
    binary = sys.argv[3] if len(sys.argv) > 3 else "./test_slack34"
    jobs = []
    for p in range(1, pmax + 1):
        for h in hubs(p):
            for s in range(p):
                jobs.append((p, h, s, turn(p, h, s)))
    with ThreadPoolExecutor(max_workers=16) as ex:
        res = list(ex.map(lambda j: run(binary, j[0], j[3], D), jobs))
    table = {}
    for (p, h, s, k), E in zip(jobs, res):
        table.setdefault((p, h), []).append((s, k, E))

    print(f"# Round 37, To Do 40: per-phase observer-clock slack of every wheel, p <= {pmax}, "
          f"d <= {D} (EMP, exact search)")
    print("# columns: p hub phase word slack(d<=D) argmax_d  | per wheel: least/greatest phase")
    summary = []
    violations = 0
    checked = 0
    for (p, h), rows in sorted(table.items()):
        sl = {s: max(E[d][0] for d in E) for s, k, E in rows}
        arg = {s: max(E, key=lambda d: (E[d][0], d)) for s, k, E in rows}
        words = {s: k for s, k, E in rows}
        Es = {s: E for s, k, E in rows}
        for s in range(p):
            w = "".join(str((words[s] >> i) & 1) for i in range(p))
            print(f"{p} {h} {s} {words[s]} [{w}] {sl[s]} {arg[s]}")
        lo = min(sl, key=lambda s: (sl[s], s))
        hi = max(sl, key=lambda s: (sl[s], -s))
        # bound check on the finite range
        worst_gap = None
        for a in range(p):
            for b in range(p):
                if a == b:
                    continue
                m = (b - a) % p
                cost = m + tests_before(p, words[a], m)
                if D - m < 1:
                    continue
                la = max(Es[a][d][0] for d in Es[a] if d <= D - m)
                lb = max(Es[b][d][0] for d in Es[b] if d <= D)
                checked += 1
                if la > lb + cost:
                    violations += 1
                gap = lb + cost - la
                if worst_gap is None or gap < worst_gap[0]:
                    worst_gap = (gap, a, b, cost)
        hub_slack = sl[0]
        summary.append({"p": p, "hub": h, "hub_slack": hub_slack, "least": sl[lo],
                        "least_phase": lo, "least_word": words[lo], "greatest": sl[hi],
                        "greatest_phase": hi, "greatest_word": words[hi],
                        "spread": sl[hi] - sl[lo], "phase_slacks": [sl[s] for s in range(p)],
                        "tightest_turn_gap": worst_gap[0] if worst_gap else None})
        print(f"WHEEL p={p} hub={h}: hub slack {hub_slack}; least {sl[lo]} at phase {lo} "
              f"(word {words[lo]}); greatest {sl[hi]} at phase {hi} (word {words[hi]}); "
              f"spread {sl[hi] - sl[lo]}; tightest turn-cost gap "
              f"{worst_gap[0] if worst_gap else '-'}")
    print(f"# turn-cost bound checked on {checked} ordered phase pairs: {violations} violations")
    per_period = {}
    for w in summary:
        q = per_period.setdefault(w["p"], {"wheels": 0, "hub_is_least": 0, "hub_is_greatest": 0,
                                           "max_spread": 0, "per_period_slack": 0,
                                           "max_least": 0})
        q["wheels"] += 1
        q["hub_is_least"] += w["hub_slack"] == w["least"]
        q["hub_is_greatest"] += w["hub_slack"] == w["greatest"]
        q["max_spread"] = max(q["max_spread"], w["spread"])
        q["per_period_slack"] = max(q["per_period_slack"], w["greatest"])
        q["max_least"] = max(q["max_least"], w["least"])
    print("# per period: wheels, hub attains least, hub attains greatest, max spread, "
          "per-period slack (max over all phases), max over wheels of least-phase slack, "
          "turn bound 2(p-1)")
    for p, q in sorted(per_period.items()):
        print(f"PERIOD {p}: wheels {q['wheels']}, hub least {q['hub_is_least']}, hub greatest "
              f"{q['hub_is_greatest']}, max spread {q['max_spread']}, per-period slack "
              f"{q['per_period_slack']}, best-phase slack {q['max_least']}, 2(p-1) = {2 * (p - 1)}")
    json.dump({"pmax": pmax, "D": D, "wheels": summary, "per_period": per_period,
               "checked": checked, "violations": violations},
              open(f"wheel_phases37_p{pmax}_d{D}.json", "w"), indent=1)


if __name__ == "__main__":
    main()

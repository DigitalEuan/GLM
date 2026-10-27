#!/usr/bin/env python3
"""Round 37, To Do 39: the hubs 1^(q-1)0 (word 2^(q-1) - 1, one black run per period), measured.

Exact integer arithmetic only.  For q = 2..QMAX and code lengths 1 <= d <= D it runs the exact
observer-clock excess search ``test_slack34`` (Round 34, study folder ``rule30_round34/``) and
reports

* the slack on d <= D (max excess) and where it is attained;
* the band check: the proved bound ``OneRunFamily.oneRun_band`` says every code of length
  d <= q - 4 fails within d + 2 tests, i.e. excess <= 2 there; the script confirms it on the range;
* the largest excess outside the band (the part that is still open for every q).

Usage: python3 one_run_family37.py QMAX D [binary] > one_run_family37_output.txt
Round 37 run (study folder rule30_round37/): QMAX = 20, D = 30; largest slack 7 (q = 13).
"""
import subprocess
import sys


def main():
    qmax, D = int(sys.argv[1]), int(sys.argv[2])
    binary = sys.argv[3] if len(sys.argv) > 3 else "./test_slack34"
    print(f"# Round 37, To Do 39: hubs 1^(q-1)0, q = 2..{qmax}, d <= {D} (EMP, exact search)")
    print("# q word slack argmax_d | band d<=q-4: max excess (proved <= 2) | outside band: max excess")
    worst = 0
    for q in range(2, qmax + 1):
        k = 2 ** (q - 1) - 1
        out = subprocess.run([binary, str(q), str(k), "1", str(D)], capture_output=True,
                             text=True, check=True).stdout
        E = {}
        for line in out.splitlines():
            if line.startswith("#") or not line.strip():
                continue
            d, e, _, _ = line.split()
            E[int(d)] = int(e)
        sl = max(E.values())
        arg = max(E, key=lambda d: (E[d], d))
        band = [E[d] for d in E if d <= q - 4]
        rest = [E[d] for d in E if d > q - 4]
        bmax = max(band) if band else None
        rmax = max(rest) if rest else None
        worst = max(worst, sl)
        ok = bmax is None or bmax <= 2
        print(f"q={q} word={k} slack={sl} at d={arg} | band max {bmax} "
              f"({'consistent' if ok else 'VIOLATION'}) | outside band max {rmax}")
    print(f"# largest slack over the family on this range: {worst}")


if __name__ == "__main__":
    main()

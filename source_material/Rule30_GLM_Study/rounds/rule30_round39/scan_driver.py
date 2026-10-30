#!/usr/bin/env python3
"""Round 39 — follow Rule 30's left side past diagonal 87867 with the proved laws.

1. Read the exact eventual patterns of diagonals 87867 and 87868 from the automaton
   (`regime_scan.emit`; F is checked against the automaton at 87869).
2. Iterate F in C (`regime_scan.c`) until the next eventually white diagonal w.
3. At w the law leaves one bit open (the post-white diagonal is u or not-u, where
   u(t+1) = A(t) xor u(t), A = the pattern outside w).  The automaton cannot be run that far, so
   the driver follows BOTH branches, to the next white diagonal of each.  If the outer parity at
   a white diagonal is odd, the following diagonal is the first one with the doubled period
   (`ldiag_doubles`).

Everything is exact.  The steps rely on proved laws (Lean: `one_bit_reset`,
`ldiag_evPer_of_not_white`, `white_iff_coincide`, `one_bit_white_period`, `ldiag_doubles`); the
only unproved ingredient is the correctness of this code, so the results are labelled `EMP`
(exact computation, not machine-checked).

Run: python3 scan_driver.py   (compiles regime_scan.c with gcc; minutes to hours)
Writes regime_branches.json.
"""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from regime_scan import emit  # noqa: E402

MAX_STEPS = 300_000_000_000


def run_leg(Q: int, A: int, B: int, start: int) -> dict:
    out = subprocess.run([str(HERE / "regime_scan"), str(Q), format(A, "x"), format(B, "x"),
                          str(start), str(MAX_STEPS)], capture_output=True, text=True,
                         check=True).stdout.split()
    if out[0] == "WHITE":
        return {"white": int(out[1]), "outer_parity": int(out[3]), "outer": int(out[5], 16),
                "steps": int(out[7])}
    return {"white": None, "raw": " ".join(out)}


def post_white(A: int, Q: int) -> tuple:
    u, x = 0, 0
    for t in range(Q):
        u |= x << t
        x ^= (A >> t) & 1
    assert x == 0, "odd parity: the post-white diagonal is anti-periodic (period doubles)"
    return u, u ^ ((1 << Q) - 1)


def main(depth: int = 1):
    subprocess.run(["gcc", "-O3", "-o", str(HERE / "regime_scan"), str(HERE / "regime_scan.c")],
                   check=True)
    Q, A, B, start = 32, *[int(v, 16) for v in emit(87867, 32)], 87867
    first = run_leg(Q, A, B, start)
    print("first leg:", first, flush=True)
    tree = {"start": start, "Q": Q, "first": first, "branches": []}
    frontier = [(first, [])]
    for _ in range(depth):
        nxt = []
        jobs = []
        for node, path in frontier:
            if node.get("white") is None or node["outer_parity"] == 1:
                continue
            for bit, u in enumerate(post_white(node["outer"], Q)):
                jobs.append((path + [bit], node["white"], u))
        with ThreadPoolExecutor(max_workers=8) as ex:
            res = list(ex.map(lambda j: run_leg(Q, 0, j[2], j[1]), jobs))
        for (path, w, u), r in zip(jobs, res):
            rec = {"open_bits": path, "after_white": w, "post_white_pattern": format(u, "x"),
                   **{k: (format(v, "x") if k == "outer" else v) for k, v in r.items()}}
            print("branch:", rec, flush=True)
            tree["branches"].append(rec)
            nxt.append((r, path))
        frontier = nxt
    first["outer"] = format(first["outer"], "x") if first.get("outer") is not None else None
    (HERE / "regime_branches.json").write_text(json.dumps(tree, indent=1))
    return tree


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1)

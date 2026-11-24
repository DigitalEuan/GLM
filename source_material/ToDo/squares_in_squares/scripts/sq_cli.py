#!/usr/bin/env python3
r"""sq_cli.py — one command line for the Squares in Squares instruments.

    python3 scripts/sq_cli.py settle 5 2+1/2r2 --width 8
    python3 scripts/sq_cli.py row 23 --cap 150
    python3 scripts/sq_cli.py verify 10
    python3 scripts/sq_cli.py audit

`settle` runs the forward anchor settler at a target side; `row` points it at one
row of the table (the target side is that row's grid side, ceil(sqrt n)) and
classifies the stall honestly; `verify` reconstructs a certified row as an anchor
chain; `audit` runs the bytecode float audit over the verifier modules.

Sides are written exactly: `3`, `2+1/2r2` (2 + 1/2 sqrt 2), `7/2+1/2r7`.
Nothing here computes geometry with floats — the settler is exact in Q(sqrt d).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "..", "..", "..", "src"))

import anchor_chain as A                                          # noqa: E402
import sqscore as SQ                                              # noqa: E402


def parse_side(text: str, field):
    """`3`, `2+1/2r2`, `7/2-1/4r7` -> an exact field element."""
    s = text.replace(" ", "").replace("\u221a", "r")
    out = field.zero
    i = 0
    sign = 1
    if s and s[0] in "+-":
        sign = -1 if s[0] == "-" else 1
        i = 1
    while i < len(s):
        j = i
        while j < len(s) and s[j] not in "+-":
            j += 1
        term = s[i:j]
        if term:
            if "r" in term:
                coef, _, d = term.partition("r")
                if d and int(d) != field.d:
                    raise SystemExit(f"side mentions sqrt {d}, field is sqrt {field.d}")
                coef = coef or "1"
                if coef.endswith("*"):
                    coef = coef[:-1]
                out = out + field.q(0, F(coef)) * sign
            else:
                out = out + field.q(F(term) * sign)
        sign = -1 if (j < len(s) and s[j] == "-") else 1
        i = j + 1
    return out


def cmd_settle(argv):
    n, side = int(argv[0]), argv[1]
    opts = dict(zip(argv[2::2], argv[3::2]))
    width = int(opts.get("--width", 8)) if "--width" in opts else 8
    cap = int(opts["--cap"]) if "--cap" in opts else None
    mode = opts.get("--mode", "closure")
    field = A.FIELDS[2]
    L = parse_side(side, field)
    A.STATS.update({k: 0 for k in A.STATS})
    A._OVERLAP.clear()
    prog = opts.get("--progress")
    got = A.settle(n, L, field, mode=mode, top=width, node_cap=cap,
                   progress=prog)
    span = A.bbox(got["placed"])[1] if got["placed"] else None
    print(f"settle n={n} L={L} mode={mode} width={width}: "
          f"{len(got['placed'])}/{n} ({got['why']})")
    print(f"  nodes {got['nodes']} states {got['states']} refusals "
          f"{got['refusals']} exhausted {got['exhausted']}")
    print(f"  span {span}" + (f"  (target {L})" if span is not None else ""))
    print(f"  {A.STATS}")
    return 0


def cmd_row(argv):
    n = int(argv[0])
    opts = dict(zip(argv[1::2], argv[2::2]))
    width = int(opts.get("--width", 8)) if "--width" in opts else 8
    cap = int(opts["--cap"]) if "--cap" in opts else 200
    seconds = int(opts.get("--seconds", 120)) if "--seconds" in opts else 120
    per = SQ.load()
    k = SQ.grid(n)
    beaten = SQ.extent(per[n]) < k - F(1, 10 ** 12)
    field = A.FIELDS[2]
    L = field.q(k)
    print(f"row n={n}: grid side k={k}, delivered {SQ.extent(per[n])}, "
          f"{'BEATEN' if beaten else 'unbeaten'}", flush=True)
    print(f"  budget {seconds}s (width {width}, cap {cap}); partial progress "
          f"is checkpointed, so a timeout still reports the deepest placement",
          flush=True)

    prog = os.path.join(ROOT, "workspace/push", f"row{n}_progress.json")
    if os.path.exists(prog):
        os.remove(prog)
    cmd = [sys.executable, os.path.abspath(__file__), "settle", str(n), side_text(L),
           "--width", str(width), "--cap", str(cap), "--progress", prog]
    timed_out = False
    try:
        subprocess.run(cmd, timeout=seconds, check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        timed_out = True
    if os.path.exists(prog):
        cells, nodes, states = A.read_progress(prog, field)
    else:
        cells, nodes, states = [], 0, 0
    print(f"  best effort: {len(cells)}/{n} cells placed; nodes {nodes} states {states}",
          flush=True)
    if cells:
        print(f"  exact span of the partial pose: {A.bbox(cells)[1]} "
              f"(target {L}); overlaps {len(A.overlaps(cells))}", flush=True)
    if len(cells) >= n:
        verdict = "settled within budget"
    else:
        avail = A.lattice_candidates(field, cells, L, field.zero)
        if not avail:
            verdict = ("no determined anchor exists at the deepest state — the "
                       "grammar lacks a command for this position")
        else:
            verdict = (f"{'time budget' if timed_out else 'node cap'} reached: "
                       f"{len(avail)} determined anchors still available at the "
                       f"deepest state")
    print(f"  verdict: {verdict}")
    rec = {"n": n, "k": k, "beaten": beaten, "seconds": seconds,
           "timed_out": timed_out, "settled": len(cells), "nodes": nodes,
           "states": states, "verdict": verdict}
    out = os.path.join(ROOT, f"workspace/push/gridrow{n}.json")
    json.dump(rec, open(out, "w"), indent=1)
    print(f"  wrote {out}")
    return 0


def side_text(L):
    """An exact field element back to the CLI's own side syntax."""
    a, b = L.a, L.b
    if not b:
        return str(a)
    if not a:
        return f"{b}r{b.denominator and L.d}"
    return f"{a}{'+' if b > 0 else '-'}{abs(b)}r{L.d}"


def cmd_verify(argv):
    n = int(argv[0])
    built = A.build(n)
    print(f"n={n} ({built['field']}): side {built['side']}, "
          f"anchors {len(built['notes'])}, overlaps {len(built['violations'])}")
    for note in built["notes"]:
        print(f"  s{note['step']:>2d} {note['command']:<15s} cell "
              f"{note['cell']:>2d} {note['why']}")
    return 0


def cmd_audit(argv):
    import exact_field as EF
    mods = [A, EF]
    total, bad = 0, []
    for m in mods:
        checked, offenders, _ = EF.audit_module(m, exempt=EF.AUDIT_EXEMPT)
        total += checked
        bad += offenders
        print(f"  {m.__name__}: {checked} decision functions, {len(offenders)} "
              f"naming float")
    print(f"audit: {total} functions, {len(bad)} offenders")
    return 0 if not bad else 1


COMMANDS = {"settle": cmd_settle, "row": cmd_row, "verify": cmd_verify,
            "audit": cmd_audit}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd = COMMANDS.get(argv[0])
    if cmd is None:
        print(f"unknown command {argv[0]!r}; try --help")
        return 2
    return cmd(argv[1:])


if __name__ == "__main__":
    sys.exit(main())

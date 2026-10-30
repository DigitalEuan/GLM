#!/usr/bin/env python3
"""Round 28 benchmark: does the Rule 30 work measurably change the GLM's puzzle and reasoning
abilities?  Run it from the directory holding ``GLM.py`` (``PYTHONPATH=.``), once on a checkout
set up to Round 16 ("before") and once after ``setup_round28.sh`` ("after").

Four measurements, all through the GLM's own ``run_tool`` entry point:

A. **Stored ARC tasks** -- ``tool arc NAME`` for the 50 tasks in ``arc_agi_17/data/training``:
   RIGHT / WRONG / REFUSED.
B. **Local-rule puzzles** -- generated here with a fixed linear congruential generator (no
   randomness, reproducible), posed as ``tool induce IN -> OUT ; IN -> OUT ; IN -> OUT ? QUERY``
   (three demonstrations) and scored against the generator's answer.
   B1 (development): 9 families x 12 instances; seven are local rules, two are CONTROLS that are
   not local (mirror, recolour-the-most-frequent-colour).  These were used while building the
   reader ladder, so B1 is NOT a held-out score.
   B2 (held-out): 7 further families x 12 instances with fresh seeds, written after the ladder was
   frozen and scored once; five local, two CONTROLS (rotate 180, flip rows).
C. **Rule 30 knowledge alignment** -- 10 declared questions whose correct answer is fixed by the
   Lean package (AUDIT 3.1, the ledger); each asks whether the GLM's reply names the right
   statement.  This measures whether the GLM's knowledge is up to date, not its reasoning power.
D. **Regression** -- the Round 11 reasoning suite (claims: frame / held-out / refuse); the
   score must not drop.

Usage::

    PYTHONPATH=. python3 r28_benchmark.py [--json out.json]
"""
from __future__ import annotations

import glob
import json
import os
import sys
from typing import Callable, Dict, List, Tuple

sys.path.insert(0, os.getcwd())
from glm_universal.runtime.toolbox import run_tool  # noqa: E402

Grid = List[List[int]]

# ---------------------------------------------------------------------------------------------
# B. the generator
# ---------------------------------------------------------------------------------------------


class LCG:
    def __init__(self, seed: int):
        self.s = seed & 0xFFFFFFFF

    def next(self, n: int) -> int:
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return (self.s >> 8) % n


def rand_grid(g: LCG, colours: List[int], density: int = 40) -> Grid:
    h, w = 5 + g.next(4), 5 + g.next(4)
    return [[colours[1 + g.next(len(colours) - 1)] if g.next(100) < density else 0
             for _ in range(w)] for _ in range(h)]


def at(a: Grid, r: int, c: int) -> int:
    return a[r][c] if 0 <= r < len(a) and 0 <= c < len(a[0]) else -1


def ray(a: Grid, r: int, c: int, dr: int, dc: int) -> int:
    r, c = r + dr, c + dc
    while 0 <= r < len(a) and 0 <= c < len(a[0]):
        if a[r][c]:
            return a[r][c]
        r, c = r + dr, c + dc
    return -1


def fam_recolour(a):
    m = {0: 0, 1: 4, 2: 7, 3: 1}
    return [[m[v] for v in row] for row in a]


def fam_interior(a):
    return [[5 if v and all(at(a, r + dr, c + dc) > 0 for dr, dc in ((1, 0), (-1, 0), (0, 1),
                                                                     (0, -1))) else v
             for c, v in enumerate(row)] for r, row in enumerate(a)]


def fam_life(a):
    out = []
    for r, row in enumerate(a):
        o = []
        for c, v in enumerate(row):
            n = sum(1 for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                    if (dr or dc) and at(a, r + dr, c + dc) > 0)
            o.append(3 if (v and n in (2, 3)) or (not v and n == 3) else 0)
        out.append(o)
    return out


def fam_rule30(a):
    """Rule 30 read horizontally: each cell becomes L xor (C or R) of its row (off-grid white)."""
    b = lambda x: 1 if x > 0 else 0
    return [[(b(at(a, r, c - 1)) ^ (b(v) | b(at(a, r, c + 1)))) for c, v in enumerate(row)]
            for r, row in enumerate(a)]


def fam_shadow(a):
    """A background cell takes the colour of the first coloured cell above it."""
    return [[v if v else max(ray(a, r, c, -1, 0), 0) for c, v in enumerate(row)]
            for r, row in enumerate(a)]


def fam_between(a):
    out = []
    for r, row in enumerate(a):
        o = []
        for c, v in enumerate(row):
            w, e = ray(a, r, c, 0, -1), ray(a, r, c, 0, 1)
            o.append(v if v or w < 0 or w != e else w)
        out.append(o)
    return out


def fam_shift(a):
    return [[max(at(a, r, c - 1), 0) for c in range(len(row))] for r, row in enumerate(a)]


def fam_mirror(a):  # CONTROL: not local
    return [list(reversed(row)) for row in a]


def fam_majority(a):  # CONTROL: not local
    cnt: Dict[int, int] = {}
    for row in a:
        for v in row:
            if v:
                cnt[v] = cnt.get(v, 0) + 1
    top = max(sorted(cnt), key=lambda k: cnt[k]) if cnt else 0
    return [[8 if v == top and v else v for v in row] for row in a]


FAMILIES: List[Tuple[str, Callable[[Grid], Grid], List[int], int, bool]] = [
    # name, rule, colours, density, local?
    ("recolour", fam_recolour, [0, 1, 2, 3], 50, True),
    ("interior", fam_interior, [0, 2, 6], 70, True),
    ("life", fam_life, [0, 3], 40, True),
    ("rule30-rows", fam_rule30, [0, 1], 45, True),
    ("shadow", fam_shadow, [0, 1, 2, 4], 15, True),
    ("between", fam_between, [0, 3, 7], 20, True),
    ("shift", fam_shift, [0, 2, 5, 9], 40, True),
    ("CONTROL-mirror", fam_mirror, [0, 1, 2, 4], 40, False),
    ("CONTROL-majority", fam_majority, [0, 1, 2, 4], 40, False),
]
# Held-out families: written after the reader ladder was frozen (Round 28, ladder v2), scored
# once, with fresh seeds.  None of them was used to choose a reader.
def fam_col_rule30(a):
    """Rule 30 read down the column: each cell becomes N xor (C or S)."""
    b = lambda x: 1 if x > 0 else 0
    return [[(b(at(a, r - 1, c)) ^ (b(v) | b(at(a, r + 1, c)))) for c, v in enumerate(row)]
            for r, row in enumerate(a)]


def fam_erase_isolated(a):
    return [[0 if v and not any(at(a, r + dr, c + dc) > 0 for dr in (-1, 0, 1)
                                for dc in (-1, 0, 1) if dr or dc) else v
             for c, v in enumerate(row)] for r, row in enumerate(a)]


def fam_count_colour(a):
    """A background cell shows how many of its 4 neighbours are coloured (0 stays 0)."""
    return [[v if v else sum(1 for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                             if at(a, r + dr, c + dc) > 0)
             for c, v in enumerate(row)] for r, row in enumerate(a)]


def fam_shadow_left(a):
    return [[v if v else max(ray(a, r, c, 0, -1), 0) for c, v in enumerate(row)]
            for r, row in enumerate(a)]


def fam_vertical_between(a):
    out = []
    for r, row in enumerate(a):
        o = []
        for c, v in enumerate(row):
            n, s_ = ray(a, r, c, -1, 0), ray(a, r, c, 1, 0)
            o.append(v if v or n < 0 or n != s_ else n)
        out.append(o)
    return out


def fam_rotate180(a):  # CONTROL: not local
    return [list(reversed(row)) for row in reversed(a)]


def fam_flip_rows(a):  # CONTROL: not local
    return list(reversed([list(row) for row in a]))


HELDOUT: List[Tuple[str, Callable[[Grid], Grid], List[int], int, bool]] = [
    ("col-rule30", fam_col_rule30, [0, 1], 45, True),
    ("erase-isolated", fam_erase_isolated, [0, 2, 6], 25, True),
    ("count-colour", fam_count_colour, [0, 5, 6, 7], 30, True),
    ("shadow-left", fam_shadow_left, [0, 3, 8], 15, True),
    ("vertical-between", fam_vertical_between, [0, 2, 9], 20, True),
    ("CONTROL-rotate180", fam_rotate180, [0, 1, 2, 4], 40, False),
    ("CONTROL-flip-rows", fam_flip_rows, [0, 1, 2, 4], 40, False),
]


INSTANCES = 12


def grid_text(a: Grid) -> str:
    return " / ".join("".join(str(v) for v in row) for row in a)


def parse_answer(text: str):
    """The answer grid printed by tool induce (last ``digits / digits`` group), if any."""
    import re
    m = re.findall(r"((?:\d+ / )+\d+)", text)
    if not m:
        return None
    return [[int(ch) for ch in row.strip()] for row in m[-1].split("/")]


def bench_synthetic(families=None, seed_base: int = 0) -> Dict[str, Dict[str, int]]:
    res: Dict[str, Dict[str, int]] = {}
    for fi, (name, f, cols, dens, _local) in enumerate(families or FAMILIES):
        tally = {"right": 0, "wrong": 0, "refused": 0}
        for i in range(INSTANCES):
            g = LCG(seed_base + 1000 * fi + i + 1)
            demos = [rand_grid(g, cols, dens) for _ in range(3)]
            query = rand_grid(g, cols, dens)
            arg = " ; ".join(grid_text(d) + " -> " + grid_text(f(d)) for d in demos)
            arg += " ? " + grid_text(query)
            r = run_tool("tool induce " + arg)
            ans = parse_answer(r.text) if r.ok else None
            if not r.ok or ans is None:
                tally["refused"] += 1
            elif ans == f(query):
                tally["right"] += 1
            else:
                tally["wrong"] += 1
        res[name] = tally
    return res


# ---------------------------------------------------------------------------------------------
# A. stored ARC
# ---------------------------------------------------------------------------------------------

def bench_arc() -> Dict[str, object]:
    files = sorted(glob.glob("arc_agi_17/data/training/*.json"))
    tally = {"right": 0, "wrong": 0, "refused": 0}
    right = []
    for f in files:
        name = os.path.basename(f)[:-5]
        r = run_tool("tool arc " + name)
        st = (r.figures or {}).get("status")
        if st == "right" or (r.ok and "RIGHT" in r.text):
            tally["right"] += 1
            right.append(name)
        elif st == "wrong" or "WRONG" in r.text:
            tally["wrong"] += 1
        else:
            tally["refused"] += 1
    return dict(tally, solved=right, tasks=len(files))


# ---------------------------------------------------------------------------------------------
# C. knowledge alignment (expected answers fixed by the Lean package)
# ---------------------------------------------------------------------------------------------

ALIGNMENT = [
    ("tool theorem narrowest P1", ["AmortizedHalving241"]),
    ("tool discuss what is the narrowest open case of problem 1 for period 2?",
     ["HalfLineDies2"]),
    ("tool theorem derive HalfLineDiesAll => P1", ["DERIVED"]),
    ("tool theorem derive AmortizedHalving241 => LeftWhiteAperiodic2", ["DERIVED"]),
    ("tool theorem derive P3Eventual => P3", ["DERIVED"]),
    ("tool theorem derive LightConeCircuitBound => P3", ["=/=>"]),
    ("tool theorem derive TuneExcessLog => P1", ["DERIVED"]),
    ("tool theorem derive P1 => HankelInfinitelyOften", ["DERIVED"]),
    ("tool theorem ledger C276", ["C276"]),
    ("tool theorem derive StateNeverRepeats => HalfLineDies2", ["=/=>"]),
]


def bench_alignment() -> Dict[str, object]:
    passed = []
    for q, needles in ALIGNMENT:
        try:
            r = run_tool(q)
            text = r.text
        except Exception as e:  # noqa: BLE001
            text = "error: %s" % e
        passed.append(all(n in text for n in needles))
    return {"passed": sum(passed), "total": len(ALIGNMENT), "per_question": passed}


# ---------------------------------------------------------------------------------------------
# D. regression: the Round 11 claim suite
# ---------------------------------------------------------------------------------------------

def bench_r11() -> str:
    import subprocess
    p = subprocess.run([sys.executable, "rule30_round11/r11_benchmark.py"], capture_output=True,
                       text=True, env=dict(os.environ, PYTHONPATH="."))
    lines = [l for l in p.stdout.splitlines() if l.startswith("SCORE")]
    return lines[-1] if lines else "not run (%s)" % p.stderr.strip().splitlines()[-1:]


def main() -> None:
    rep = {"arc": bench_arc(), "synthetic": bench_synthetic(),
           "heldout": bench_synthetic(HELDOUT, seed_base=50000),
           "alignment": bench_alignment(), "r11": bench_r11()}
    a = rep["arc"]
    print("A. stored ARC tasks (%d): RIGHT %d  WRONG %d  REFUSED %d  solved=%s" % (
        a["tasks"], a["right"], a["wrong"], a["refused"], a["solved"]))
    for key, title in (("synthetic", "B1. development local-rule puzzles"),
                       ("heldout", "B2. held-out local-rule puzzles (fresh families and seeds)")):
        print("%s (%d instances per family)" % (title, INSTANCES))
        tot = {"right": 0, "wrong": 0, "refused": 0}
        for name, t in rep[key].items():
            print("   %-18s RIGHT %2d  WRONG %2d  REFUSED %2d" % (name, t["right"], t["wrong"],
                                                                t["refused"]))
            for k in tot:
                tot[k] += t[k]
        print("   %-18s RIGHT %2d  WRONG %2d  REFUSED %2d" % ("TOTAL", tot["right"],
                                                            tot["wrong"], tot["refused"]))
    al = rep["alignment"]
    print("C. Rule 30 knowledge alignment: %d / %d  %s" % (al["passed"], al["total"],
                                                        al["per_question"]))
    print("D. Round 11 claim suite: %s" % rep["r11"])
    if "--json" in sys.argv:
        json.dump(rep, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)


if __name__ == "__main__":
    main()

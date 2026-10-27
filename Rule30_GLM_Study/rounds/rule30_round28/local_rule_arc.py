"""Round 28 (Rule 30 study): local-rule induction on ARC grids, with sound refusal.

Purpose
-------
The Rule 30 study's induction results (Lean: ``WheelInduction.lean`` for 1-D wheels and, from
Round 28, ``LocalRuleInduction.lean`` for any grid and any neighbourhood reader) say:

* a local rule reproduces the demonstrations  iff  it agrees with them on every neighbourhood
  key the demonstrations show (``reproduces_iff_agrees``);
* every rule that reproduces the demonstrations gives the same answer on a query  iff  every key
  the query needs has been seen (``determined_iff_covered``);
* a reader that is too coarse is refuted by a clash (two equal keys, two different outputs),
  and a refuted reader stays refuted when more demonstrations arrive (``clash_refutes``);
  a reader is never *confirmed* by finite data (``TuningByEar.lean``).

This script turns those facts into an ARC solver and **measures** it on the 50 ARC tasks stored
in the GLM archive (``overlay/arc_agi_17/data/training``).  It is the GLM-side
"does the Rule 30 work help ARC?" measurement of Round 28.  Test outputs are used for scoring
only, never for choosing.

Readers (observers), in ladder order (coarse first; the ladder is fixed in advance)
-------------------------------------------------------------------------------------
``cell``                    the cell's own colour (a colour map);
``row3`` / ``col3``         the Rule 30 wheel neighbourhood (west, centre, east), and the same
                            read down the column;
``tot4`` / ``tot8``         totalistic: the cell and how many of its 4 / 8 neighbours are coloured;
``blind-*``                 colour-blind versions of vn1, rays4, moore1, rays8 (the key keeps only
                            background / coloured / off-grid; the output may copy a colour);
``mask4``, ``mask8``        the cell's colour and the shape of its neighbourhood;
``between``                 is the cell between two equal colours, vertically / horizontally;
``raymask4``, ``raymask8``  which directions see a coloured cell;
``vn1``, ``moore1``         the cell and its 4 / 8 neighbours, with colours;
``rays4``, ``rays8``        the first colour seen looking in 4 / 8 directions (the observer's
                            *read direction*: "Y reads from here, towards there");
``rowcol``                  the sets of colours in the cell's row and column;
``mask5x5``, ``moore2``     the 5x5 block.
An output is recorded as every encoding that produces it (the absolute colour, or "copy slot i"
of the reader); a cell is answered only if every surviving encoding gives the same colour.

Modes
-----
``ladder``    answer with the first reader that is consistent on the demonstrations and covers
              every query key; otherwise refuse.
``guess``     UNSOUND control: the first consistent reader, with unseen keys copied from the
              input and ambiguous keys resolved by a fixed order.  It is reported only to
              measure what the refusal rule (``determined_iff_covered``) prevents.
``listened``  as ``ladder``, but the reader must also predict every demonstration exactly from
              the others (leave-one-out) before it may answer: the "tuning by ear" listening
              test.  Higher precision, fewer answers.

Implementation: ``glm_overlay/glm_universal/reasoning/local_rule_induction.py`` (this
script only drives it).

Usage::

    python3 local_rule_arc.py [ARC_DIR] [--json out.json]

Exact arithmetic only; no randomness.  Output of the default run: ``local_rule_arc_output.txt``.
"""
import glob
import json
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "glm_overlay", "glm_universal", "reasoning"))
from local_rule_induction import DEFAULT_DIR, solve  # noqa: E402

def run(arc_dir: str) -> Dict[str, object]:
    files = sorted(glob.glob(os.path.join(arc_dir, "*.json")))
    report: Dict[str, object] = {"tasks": len(files), "modes": {}}
    for mode in ("ladder", "listened", "guess"):
        right, wrong, refused = [], [], []
        per = {}
        for f in files:
            task = json.load(open(f))
            name = os.path.basename(f)[:-5]
            ans, why = solve(task, mode)
            if ans is None:
                refused.append(name)
                per[name] = ("REFUSE", why)
                continue
            ok = all(a == p["output"] for a, p in zip(ans, task["test"]))
            (right if ok else wrong).append(name)
            per[name] = ("RIGHT" if ok else "WRONG", why)
        report["modes"][mode] = {"right": right, "wrong": wrong, "refused": len(refused),
                                 "per_task": per}
    return report


def main(argv: List[str]) -> None:
    out_json = None
    if "--json" in argv:
        i = argv.index("--json")
        out_json = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    arc_dir = argv[0] if argv else DEFAULT_DIR
    rep = run(arc_dir)
    print("Local-rule induction on %d stored ARC tasks" % rep["tasks"])
    for mode, m in rep["modes"].items():
        print("\nmode %-9s RIGHT %2d  WRONG %2d  REFUSED %2d" % (
            mode, len(m["right"]), len(m["wrong"]), m["refused"]))
        for name, (v, why) in sorted(m["per_task"].items()):
            if v != "REFUSE":
                print("   %-10s %-5s reader=%s" % (name, v, why))
    if out_json:
        json.dump(rep, open(out_json, "w"), indent=1, default=list)


if __name__ == "__main__":
    main(sys.argv[1:])

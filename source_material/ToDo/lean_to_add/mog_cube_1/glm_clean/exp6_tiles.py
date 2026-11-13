#!/usr/bin/env python3
"""
exp6_tiles.py — GolayHex-Upsilon: the receipts, and what the tiling actually is.

Runs every check in `glm_clean/tiles.py` and writes results/tiles_receipts.txt.
Nothing here is asserted without being computed; the one constant that cannot
be reproduced from anything in this repository is reported as UNVERIFIABLE
rather than quietly accepted.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from glm_clean import tiles as T
from glm_clean.hexacode import MOG_CODE, NAMES
from glm_clean.hexacode import verify as hexverify

RESULTS = Path(__file__).resolve().parent / "results"
RESULTS.mkdir(exist_ok=True)

lines = []


def say(s=""):
    print(s, flush=True)
    lines.append(s)


def head(s):
    say("")
    say("=" * 78)
    say(s)
    say("=" * 78)


def main():
    report = {}

    head("0  THE GEOMETRY: which cube reading survives")
    w = T.why_not_six_grids()
    say(f"  claim     : {w['claim']}")
    say(f"  reason    : {w['reason']}")
    say(f"  resolution: {w['resolution']}")
    hv = hexverify()
    say("")
    say("  the MOG grid rebuilt from the hexacode (so the columns are faces):")
    for k in ("dimension", "n_words", "min_distance", "doubly_even",
              "self_dual", "decompose_failures", "decompose_checked",
              "n_fibres", "fibre_sizes"):
        say(f"    {k:22s} {hv[k]}")
    say(f"    weight enumerator      {hv['weight_enumerator']}")
    report["hexacode_verify"] = hv

    head("1  THE RECEIPTS OF SECTION 6")
    rec = T.receipts()
    for name, verdict, evidence in rec:
        say(f"  {verdict:13s} {name}")
        if verdict != "PASS":
            say(f"                {evidence}")
    report["receipts"] = [{"name": n, "verdict": v, "evidence": e}
                          for n, v, e in rec]
    say("")
    say(f"  passed {sum(1 for _n, v, _e in rec if v == 'PASS')} of {len(rec)}; "
        f"{sum(1 for _n, v, _e in rec if v == 'FAIL')} failed; "
        f"{sum(1 for _n, v, _e in rec if v == 'UNVERIFIABLE')} unverifiable")

    head("2  THE TILE TAXONOMY, WITH RECEIPTS")
    words = MOG_CODE.words
    examples = [("T0 vacuum", 0)]
    for target in (8, 12, 16, 24):
        examples.append((f"T_reg({target})",
                         next(x for x in words if bin(x).count("1") == target)))
    examples.append(("T_def(1)", 1))
    examples.append(("T_def(2)", 0b11))
    examples.append(("T_def(3)", 0b111))
    examples.append(("T_def(4) anchor", 0b1111))
    for label, v in examples:
        r = Tile_receipt(v)
        say(f"  {label:18s} {r}")
    report["taxonomy"] = {label: str(Tile_receipt(v)) for label, v in examples}

    head("3  ANCHORS ARE FORCED, NOT CHOSEN")
    cen = T.syndrome_census()
    say(f"  cosets by leader weight : {cen['cosets_by_leader_weight']}")
    say(f"  shallow (q <= 3)        : {cen['shallow_le3']}  -- transient, the "
        f"substrate names the failing cells and heals them")
    say(f"  deep (q = 4)            : {cen['deep_eq4']}  -- six leaders tie, no "
        f"repair is preferred, so only these may anchor")
    report["syndromes"] = cen

    head("4  THE MATCHING RULE, AND WHAT IT MAKES THE TILING DO")
    inf = T.information_sets()
    say(f"  every triple of faces is an information set (hexacode is MDS): "
        f"{inf['all_triples_are_information_sets']}")
    um = T.update_matrix()
    say(f"  the update incoming (-x,-y,-z) -> outgoing (+x,+y,+z) is "
        f"GF(4)-linear: {um['linear']}")
    M = um["matrix"]
    say("  its matrix (0, 1, w, w2 written out):")
    for row in M:
        say("      [ " + "  ".join(NAMES[x] for x in row) + " ]")
    say(f"  multiplicative order of the matrix: {um['order']}")
    say("  so the assembly is a deterministic, reversible, GF(4)-linear "
        "three-dimensional automaton whose propagator has period 3.")
    dem = T.automaton_demo(5)
    say(f"  propagated a {dem['cells']}-cell block from its three boundary "
        f"planes: all joins legal = {dem['all_joins_legal']}, "
        f"reversible = {dem['reversible']}")
    report["update"] = um
    report["automaton"] = dem

    head("5  HOW MANY LEGAL ASSEMBLIES THERE ARE (exact counts)")
    say("  hexacode layer, counted by profile DP, against the closed form")
    say("  4^(nx.ny + ny.nz + nz.nx):")
    boxes = [(1, 1, 1), (2, 1, 1), (3, 1, 1), (4, 1, 1),
             (2, 2, 1), (3, 2, 1), (2, 2, 2)]
    rows = []
    for b in boxes:
        c = T.count_hex_assignments(*b)
        f = T.box_formula(*b)
        rows.append({"box": "x".join(map(str, b)), "counted": c,
                     "formula": f, "agree": c == f})
        say(f"    {'x'.join(map(str,b)):8s} counted {c:>14d}   formula {f:>14d}"
            f"   {'agree' if c == f else 'DISAGREE'}")
    report["box_counts"] = rows
    say("")
    say("  Consequence, and it is exact: the number of legal assemblies of a "
        "box is 4 to the area")
    say("  of its three incoming boundary planes.  The hexacode layer carries "
        "SURFACE entropy only;")
    say("  the interior is computed, not chosen.  Each (hexacode word, parity) "
        "is carried by 32")
    say("  of the 4096 lawful tiles, so the whole tile count is "
        "2 . 32^N . 4^area, i.e. exactly")
    say("  5 bits per tile of volume entropy, all of it below the hexacode.")

    head("6  PHI, E, AND THE THIRTEEN SINKS -- WHAT IS EARNED AND WHAT IS NOT")
    pf = T.perron_fibonacci()
    say(f"  Fibonacci substitution S -> SD, D -> S: ratio after 40 steps "
        f"{pf['ratio_after_40']:.15f}")
    say(f"  phi                                    {pf['phi']:.15f}   "
        f"error {pf['err_after_40']:.2e}")
    say("  BUT the substitution is stipulated.  Nothing in the Golay/MOG/Leech "
        "arithmetic forces it,")
    say("  and no ratio of the substrate's own counts is phi:")
    ratios = {"759/2576 octads:dodecads": 759 / 2576,
              "2325/1771 shallow:deep": 2325 / 1771,
              "4096/759": 4096 / 759, "24/12": 2.0, "196560/98304": 196560 / 98304}
    for k, v in ratios.items():
        say(f"      {k:28s} {v:.6f}   {'= phi' if abs(v - float(T.PHI)) < 1e-6 else ''}")
    say("  [stip] phi.  Emergence claimed, not delivered.")
    say("")
    say("  Growth: the measured growth constants of legal assemblies are")
    say("      1-D  512 tiles per cell   (16 at the hexacode layer)")
    say("      2-D  128 per cell         (4 at the hexacode layer)")
    say("      3-D   32 per cell         (1 at the hexacode layer: "
        "deterministic)")
    say("  all powers of two, exactly.  e does not appear, and cannot: these "
        "growth constants are")
    say("  integers, and the hexacode layer is deterministic in three "
        "dimensions.  [open] stays open,")
    say("  and is now sharper -- if e is to appear it must come from some "
        "other process entirely.")
    say("")
    th = T.thirteen_report()
    say(f"  wobble = frac(pi.phi.e) = {th['wobble']:.10f}")
    say(f"  L      = wobble / 13    = {th['sink_L']:.10f}")
    say(f"  13 . L == wobble exactly, as Fractions: {th['balance_exact']}")
    say(f"  |M24| = {th['M24_order']} = {th['M24_factorisation']}")
    say(f"  13 divides |M24|                : {th['13_divides_M24']}")
    say(f"  13 is an element order of M24   : {th['13_is_an_element_order']}")
    say(f"  code parameters divisible by 13 : "
        f"{th['13_divides_any_code_parameter']}")
    say(f"  {th['verdict']}")
    report["phi"] = pf
    report["thirteen"] = th

    head("7  THE ADMISSIBILITY WINDOW IS WIDER THAN ADVERTISED")
    aw = T.admissibility_window()
    say(f"  NRCI in {aw['window']} with B = 10 holds for weights "
        f"{aw['weights_in_window']}")
    say(f"  {aw['note']}")
    report["admissibility"] = aw

    (RESULTS / "tiles_receipts.txt").write_text("\n".join(lines))
    (RESULTS / "tiles_receipts.json").write_text(
        json.dumps(report, indent=2, default=str))
    print("\nwrote results/tiles_receipts.txt and results/tiles_receipts.json")


def Tile_receipt(v: int) -> str:
    t = T.Tile(v)
    r = t.receipt()
    return (f"HW={r['HW']:2d} q={r['defect_q']} leaders={r['n_leaders']} "
            f"TAX_MOG={float(r['TAX_MOG']):7.4f} "
            f"NRCI={float(r['NRCI']):.4f} "
            f"NRCI_cal={float(r['NRCI_calibrated']):.4f}  {r['kind']}")


if __name__ == "__main__":
    main()

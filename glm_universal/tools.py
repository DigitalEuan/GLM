"""Command line for the project's study instruments.

The six core sub-packages are libraries, not programs: they are audited for
purity by :func:`glm_universal.reasoning.blueprint.ubp_source_audit` and the
audit is easiest to trust when the core imports nothing but exact arithmetic.
Argument parsing, process exit codes and the standard streams therefore live
here, one module above the core, next to :mod:`glm_universal.figures`.

::

    PYTHONPATH=. python3 -m glm_universal.tools lean-address
    PYTHONPATH=. python3 -m glm_universal.tools lean-address --write
    PYTHONPATH=. python3 -m glm_universal.tools lean-address --speak NAME
    PYTHONPATH=. python3 -m glm_universal.tools pipeline
    PYTHONPATH=. python3 -m glm_universal.tools directives
    PYTHONPATH=. python3 -m glm_universal.tools signoff

Exit codes: ``0`` if what was asked for holds, ``1`` if a report found a
defect, ``2`` if the arguments were not understood.
"""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from typing import Optional, Sequence

from .reasoning import directives as drc
from .reasoning import lean_address as lad
from .reasoning import pipeline as ppl
from .reasoning import deep_hole_classifier as dhc
from .reasoning import deep_hole_escalation as esc
from .reasoning import deep_hole_failures as dhf
from .reasoning import configuration_queries as cfq
from .reasoning import empty_rungs as emr
from .reasoning import norm256_hex as n256
from .reasoning import cell_guard as cgd
from .reasoning import placement_guard as plg
from .reasoning import probe_budget as prb
from .reasoning import patience_census as pcs
from .reasoning import frozen_path as frp
from .reasoning import hole_census as hcs
from .reasoning import lattice_completion as ltc
from .reasoning import cumulativity as cml
from .reasoning import ladder_escalation as lesc
from .reasoning import query_escalation as qesc
from .reasoning import review_sweep as rvs
from .reasoning import stray_blind as sbl
from .reasoning import share_ensemble as shens
from .reasoning import share_separation as shsep
from .reasoning import configuration_reading as confr
from .reasoning import wobble_landscape as wls
from .signoff import checks as chk
from .signoff import ledger as sgn

__all__ = ["main", "run"]


def _per_mille(value: Fraction) -> str:
    """A rational as parts per thousand, rounded to the nearest integer.

    The package constructs no floats, so a proportion is printed rather than
    converted.
    """
    scaled = value * 1000
    return f"{(scaled.numerator + scaled.denominator // 2) // scaled.denominator}/1000"


# ---------------------------------------------------------------------------
#  lean-address
# ---------------------------------------------------------------------------

def _lean_address(args: argparse.Namespace) -> int:
    if args.write:
        path = lad.write_address_book()
        state = lad.cache_state()
        print(f"wrote {path}")
        print(f"digest {state['live_digest']}")
        print(f"declarations {len(lad.address_book(refresh=True)['order'])}")
        return 0

    if args.speak:
        spoken = lad.speak(args.speak)
        if not spoken.get("found"):
            print(f"no declaration named {args.speak!r}")
            return 1
        print(json.dumps(spoken, indent=2, default=str, sort_keys=True)
              if args.json else spoken["sentence"])
        if not args.json:
            print(f"address {list(spoken['address'])}")
            for neighbour in spoken["neighbours"]:
                print(f"  near {neighbour['name']} "
                      f"(d^2 = {neighbour['squared_distance']})")
        return 0

    state = lad.cache_state()
    if args.json:
        print(json.dumps(lad.lean_address_report(), indent=2, default=str,
                         sort_keys=True))
        return 0 if state["fresh"] else 1
    print(f"cache: {state['verdict']}")
    if not state["present"]:
        print("run with --write to build the address book")
        return 1
    report = lad.lean_address_report()
    corpus = report["corpus"]
    print(f"{corpus['declarations']} declarations in {corpus['files']} files")
    rt = report["round_trip"]
    print(f"round trip exact: {rt['exact']}/{rt['checked']}")
    for scheme in lad.SCHEMES:
        n = report["separation"][scheme]["neighbours"]
        print(f"{scheme:>12}: nearest neighbour same file "
              f"{n['same_file_nearest']}/{n['declarations']} "
              f"(chance {_per_mille(n['same_file_chance'])})")
    return 0 if state["fresh"] else 1


# ---------------------------------------------------------------------------
#  pipeline
# ---------------------------------------------------------------------------

def _pipeline(args: argparse.Namespace) -> int:
    report = ppl.pipeline_report()
    if args.json:
        print(json.dumps(report, indent=2, default=str, sort_keys=True))
        return 0
    width = max(len(r["key"]) for r in report["rows"])
    print(f"{'row':<{width}}  " + "  ".join(s[:4] for s in ppl.STAGES)
          + "   next")
    for r in report["rows"]:
        marks = "  ".join(" ok " if r["stages"][s] else " -- "
                          for s in ppl.STAGES)
        print(f"{r['key']:<{width}}  {marks}   {r['first_missing'] or ''}")
    print()
    print(f"{report['complete']} of {report['count']} rows complete")
    for stage, keys in report["blocked_at"].items():
        print(f"blocked at {stage}: {', '.join(keys)}")
    if args.commands:
        print()
        for command in report["verify_commands"]:
            print(command)
    return 0


# ---------------------------------------------------------------------------
#  directives
# ---------------------------------------------------------------------------

def _directives(args: argparse.Namespace) -> int:
    report = drc.directives_report()
    if args.json:
        print(json.dumps(report, indent=2, default=str, sort_keys=True))
        return 0 if report["sound"] else 1
    for row in report["rows"]:
        mark = "ok" if row["state"]["all_resolved"] else "??"
        print(f"{row['key']}  {mark}  {row['rule'][:64]}")
    print()
    print(f"{report['instrumented']} of {report['count']} directives have "
          f"every named instrument present")
    for defect in report["defects"]:
        print(f"defect: {defect}")
    return 0 if report["sound"] else 1


# ---------------------------------------------------------------------------
#  signoff
# ---------------------------------------------------------------------------

def _whole_seconds(value: Fraction) -> int:
    """An exact rational of seconds, rounded to the nearest whole one.

    No float is constructed: the package's arithmetic is exact throughout
    (directive **D7**), and printing is no exception.
    """
    return (value.numerator + value.denominator // 2) // value.denominator


def _signoff(args: argparse.Namespace) -> int:
    """What the ledger currently covers, without running anything.

    The full command line of the ledger is ``python -m glm_universal.signoff``;
    this is the read-only summary, kept here beside the other instruments so
    that one command answers "what is checked, and how old is the check?".
    """
    tests = sgn.verify()
    instruments = chk.verify_checks()
    saving = sgn.predicted_saving()
    check_saving = chk.predicted_check_saving()
    report = {
        "schema": tests["schema"],
        "interpreter": tests["interpreter"],
        "tests": tests,
        "instruments": instruments,
        "seconds_signed_off": (saving["seconds_saved"]
                               + check_saving["seconds_saved"]),
        "seconds_to_run": (saving["seconds_to_run"]
                           + check_saving["seconds_to_run"]),
        "all_signed": tests["all_signed"] and instruments["all_signed"],
    }
    if args.json:
        print(json.dumps(report, indent=2, default=str, sort_keys=True))
        return 0 if report["all_signed"] else 1
    print(f"schema {report['schema']}, {report['interpreter']}")
    print(f"test files:  {tests['signed']} of {tests['units']} signed off")
    print(f"instruments: {instruments['signed']} of {instruments['units']} "
          f"signed off")
    for label, group in (("tests", tests), ("instruments", instruments)):
        for state in ("new", "changed", "failed"):
            if group[state]:
                print(f"  {label} {state}: {', '.join(group[state])}")
    print(f"{_whole_seconds(report['seconds_signed_off'])}s of work is covered "
          f"by a signature that still holds; "
          f"{_whole_seconds(report['seconds_to_run'])}s would have to run")
    return 0 if report["all_signed"] else 1


# ---------------------------------------------------------------------------
#  landscape
# ---------------------------------------------------------------------------

def _landscape(args: argparse.Namespace) -> int:
    """The pre-registered wobble landscape, and its measurement cache."""
    if args.write:
        path = wls.write_measurements()
        print(f"wrote {path}")
        print(f"digest {wls.module_digest()}")
        return 0
    condition = wls.state()
    report = wls.landscape_report()
    primary = report["primary"]["primary_null"]
    gate = report["gate"]
    if args.json:
        print(json.dumps({
            "cache": condition["verdict"],
            "statistic": str(report["primary"]["statistic"]),
            "tail": str(primary["tail"]),
            "null": primary["name"],
            "score": gate["score_rounded"],
            "verdict": gate["verdict"],
            "enumerate": gate["enumerate"],
        }, indent=1, sort_keys=True))
        return 0 if condition["fresh"] else 1
    print(f"cache             {condition['verdict']}")
    print(f"statistic         S(alpha) = "
          f"{report['primary']['statistic_rounded']}")
    print(f"null              {primary['name']}")
    print(f"tail              {primary['tail']} "
          f"({primary['at_least_as_extreme']} of {primary['members']})")
    print(f"bit score         {gate['score_rounded']} "
          f"({gate['verdict']}); enumerate: {gate['enumerate']}")
    return 0 if condition["fresh"] else 1


# ---------------------------------------------------------------------------
#  deepholes
# ---------------------------------------------------------------------------

def _deepholes(args: argparse.Namespace) -> int:
    """The pre-registered deep-hole classifier, and its measurement cache.

    ``--write`` re-takes the measurement, which is a quarter of an hour of
    exact decoding; without it the stored one is read and its freshness
    reported, never silently recomputed.
    """
    if args.write:
        path = dhc.write_measurements()
        print(f"wrote {path}")
        print(f"digest {dhc.module_digest()}")
        return 0
    condition = dhc.state()
    report = dhc.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    run = report["run"]
    method = run["method"]
    gate = report["gate"]
    if args.json:
        print(json.dumps({
            "cache": condition["verdict"],
            "types": report["table"]["size"],
            "queries": method["queries"],
            "correct": method["correct"],
            "baseline": run["baseline"]["correct"],
            "digest": run["digest"]["correct"],
            "reshuffle": run["reshuffle"]["correct"],
            "score": gate["score_rounded"],
            "sanity_holds": gate["sanity_holds"],
            "verdict": gate["verdict"],
        }, indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    print(f"types reached     {report['table']['size']} of "
          f"{report['catalogue_size']}")
    print(f"method            {method['correct']} of {method['queries']} "
          f"queries")
    print(f"vertex count      {run['baseline']['correct']} "
          f"(digest {run['digest']['correct']}, reshuffle "
          f"{run['reshuffle']['correct']})")
    print(f"sanity holds      {gate['sanity_holds']}")
    print(f"bit score         {gate['score_rounded']} "
          f"({gate['verdict']})")
    return 0


# ---------------------------------------------------------------------------
#  stray-blind
# ---------------------------------------------------------------------------

def _stray_blind(args: argparse.Namespace) -> int:
    """Lattice item 10: which pairs a distance-only reading must conflate.

    ``--write`` re-takes the census over the ladder's own ensembles (a
    quarter of an hour of exact decoding); without it the stored census is
    read and its freshness reported, never silently recomputed.
    """
    if args.write:
        path = sbl.write_measurements()
        print(f"wrote {path}")
        print(f"digest {sbl.module_digest()}")
        return 0
    condition = sbl.state()
    report = sbl.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    if args.json:
        print(json.dumps({
            "cache": condition["verdict"],
            "agree_everywhere": report["agree_everywhere"],
            "common_radius_everywhere": report["common_radius_everywhere"],
            "rows": [{"starts": row["starts"],
                      "radius": str(row["radius"]),
                      "predicted": [list(pair) for pair in row["predicted"]],
                      "measured": [list(pair) for pair in row["measured"]],
                      "stray_free": list(row["stray_free"])}
                     for row in report["rows"]],
        }, indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    print(f"theorem           {report['lean']}")
    print(f"one radius        {report['common_radius_everywhere']}")
    print(f"predicted = measured at every size: {report['agree_everywhere']}")
    for row in report["rows"]:
        pairs = ", ".join("/".join(pair) for pair in row["measured"]) or "none"
        print(f"  {row['starts']:>4} starts   radius {row['radius']}   "
              f"conflated {pairs}   stray-free "
              f"{', '.join(row['stray_free']) or 'none'}")
    return 0


# ---------------------------------------------------------------------------
#  share-ensemble / share-separation
# ---------------------------------------------------------------------------

def _share_ensemble(args: argparse.Namespace) -> int:
    """Lattice item 6: the ladder's ensembles extended to 30720 starts.

    ``--write`` re-takes them (614,400 exact decodes, on every core); without
    it the stored ensembles' freshness is reported, never recomputed.
    """
    if args.write:
        path = shens.write_measurements(jobs=args.jobs)
        print(f"wrote {path}")
        print(f"digest {shens.module_digest()}")
        return 0
    condition = shens.state()
    print(f"cache             {condition['verdict']}")
    print(f"sizes             {', '.join(str(n) for n in shens.SIZES)}")
    return 0 if condition["fresh"] else 1


def _share_separation(args: argparse.Namespace) -> int:
    """Lattice item 6: the separation criterion for the share-carrying rungs,
    read off the stored ensembles."""
    report = shsep.share_separation_report()
    if not report["available"]:
        print(report["reason"])
        return 1
    if args.json:
        print(json.dumps({
            "marks": report["marks"], "marks_met": report["marks_met"],
            "best_share_cell": {k: str(v) for k, v in
                                report["best_share_cell"].items()},
            "first_below_one": (None if report["first_below_one"] is None
                                else {k: str(v) for k, v in
                                      report["first_below_one"].items()}),
            "cells": [{"layer": c["layer"], "starts": c["starts"],
                       "q0": c["q0"], "spread": str(c["spread"]),
                       "separation": str(c["separation"]),
                       "ratio": None if c["ratio"] is None else str(c["ratio"]),
                       "locally_certified": c["locally_certified"]}
                      for c in report["cells"]],
        }, indent=1, sort_keys=True))
        return 0
    print(f"theorem           {report['lean']}")
    print(f"reproduced        {report['reproduced_cells']} of "
          f"{report['ladder_cells']} ladder cells")
    print(f"bound holds       {report['bound_holds']} of "
          f"{report['bound_instances']}")
    for c in report["cells"]:
        ratio = "n/a" if c["ratio"] is None else esc.rounded(c["ratio"], 4)
        print(f"  {c['layer']:<9}{c['starts']:>6}  Q0 {c['q0']:>2}/{c['gate']}"
              f"  W {esc.rounded(c['spread'], 4)}"
              f"  B {esc.rounded(c['separation'], 4)}  rho {ratio}"
              f"  per-hole {c['locally_certified']}/{c['gate']}")
    print("marks             " + ", ".join(
        f"{k} {'met' if v else 'missed'}" for k, v in report["marks"].items()))
    return 0


# ---------------------------------------------------------------------------
#  configuration-reading
# ---------------------------------------------------------------------------

def _configuration_reading(args: argparse.Namespace) -> int:
    """Lattice item 6, the 28-vertex pair: the configuration reading ``L5``,
    read off the stored ensembles (Phase 122)."""
    report = confr.configuration_report()
    if not report["available"]:
        print(report["reason"])
        return 1
    if args.json:
        print(json.dumps({
            "marks": report["marks"], "marks_met": report["marks_met"],
            "first_below_one": report["first_below_one"],
            "cells": [{"starts": c["starts"], "q0": c["q0"],
                       "spread": str(c["spread"]),
                       "separation": str(c["separation"]),
                       "closest_pair": list(c["closest_pair"] or ()),
                       "ratio": None if c["ratio"] is None else str(c["ratio"]),
                       "locally_certified": c["locally_certified"],
                       "pair_distance": str(c["pair_distance"])}
                      for c in report["cells"]],
        }, indent=1, sort_keys=True))
        return 0
    print(f"theorem           {report['lean']}")
    print(f"control           {report['control_holds']} of "
          f"{len(report['control'])} (hole, seed) diagrams read as declared")
    print(f"bound holds       {report['bound_holds']} of "
          f"{report['bound_instances']}")
    closest = report["uniform_closest"]
    print(f"uniform limit     closest {closest['pair'][0]}/{closest['pair'][1]} "
          f"at {closest['distance']}; 28-vertex pair at "
          f"{report['uniform_pair']['distance']}")
    for c in report["cells"]:
        ratio = "n/a" if c["ratio"] is None else esc.rounded(c["ratio"], 4)
        print(f"  L5 {c['starts']:>6}  Q0 {c['q0']:>2}/{c['gate']}"
              f"  W {esc.rounded(c['spread'], 4)}"
              f"  B {esc.rounded(c['separation'], 4)}  rho {ratio}"
              f"  per-hole {c['locally_certified']}/{c['gate']}"
              f"  E6^4/D6^4 {esc.rounded(c['pair_distance'], 4)}")
    print("marks             " + ", ".join(
        f"{k} {'met' if v else 'missed'}" for k, v in report["marks"].items()))
    return 0


# ---------------------------------------------------------------------------
#  escalation
# ---------------------------------------------------------------------------

def _escalation(args: argparse.Namespace) -> int:
    """The deep-hole ladder, and its measurement cache.

    ``--write`` re-takes the measurement, which is a quarter of an hour of
    exact decoding; without it the stored one is read and its freshness
    reported, never silently recomputed.
    """
    if args.write:
        path = esc.write_measurements()
        print(f"wrote {path}")
        print(f"digest {esc.module_digest()}")
        return 0
    condition = esc.state()
    report = esc.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    tree = report["decision"]
    best = tree["best"]
    if args.json:
        print(json.dumps({
            "cache": condition["verdict"],
            "verdict": tree["verdict"],
            "reproduces": tree["reproduces"],
            "gate": tree["gate"],
            "best_layer": best["layer"],
            "best_starts": best["starts"],
            "best_q0": best["q0"],
            "cells": [{"layer": cell["layer"], "starts": cell["starts"],
                       "q0": cell["q0"],
                       "ratio": (esc.rounded(cell["ratio"], 4)
                                 if cell["ratio"] is not None else None)}
                      for cell in report["cells"]],
        }, indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    print(f"verdict           {tree['verdict']}")
    print(f"bottom rung       {tree['bottom']['q0']} of {tree['gate']} "
          f"(reproduces the first round: {tree['reproduces']})")
    for cell in report["cells"]:
        ratio = (esc.rounded(cell["ratio"], 4)
                 if cell["ratio"] is not None else "n/a")
        print(f"  {cell['layer']:<9} {cell['starts']:>4} starts   "
              f"Q0 {cell['q0']:>2} of {cell['gate']:<2}  rho {ratio}")
    print(f"best cell         {best['layer']} at {best['starts']} starts, "
          f"Q0 {best['q0']} of {tree['gate']}")
    return 0


# ---------------------------------------------------------------------------
#  failures
# ---------------------------------------------------------------------------

def _failures(args: argparse.Namespace) -> int:
    """The four failures of the escalated reading, and the stalled ratio.

    ``--write`` re-takes the measurement, which runs every declared ensemble
    once; without it the stored one is read and its freshness reported.
    """
    if args.write:
        path = dhf.write_measurements()
        print(f"wrote {path}")
        print(f"digest {dhf.module_digest()}")
        return 0
    condition = dhf.state()
    report = dhf.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    check = report["reproduction"]
    spread = report["spread"]
    if args.json:
        print(json.dumps({
            "cache": condition["verdict"],
            "reproduces": check["reproduces"],
            "correct": check["correct"],
            "queries": check["queries"],
            "counts": dict(report["counts"]),
            "worst_type": spread["worst_type"],
            "rho_seed": dhf.rounded(spread["rho_seed"], 4),
            "rho_all": dhf.rounded(spread["rho_all"], 4),
            "same_mechanism": report["same_mechanism"],
            "best_deletion": dhf.rounded(
                report["leave_out"]["best_two"]["ratio"], 4),
        }, indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    print(f"reproduces        {check['correct']} of {check['queries']} "
          f"({check['reproduces']})")
    for row in report["failures"]:
        print(f"  {row['query']:<28} truth {row['truth']:<10} named "
              f"{str(row['named']):<10} rank {row['own_rank']}  margin "
              f"{dhf.rounded(row['margin'], 4)}")
    print(f"worst spread      {spread['worst_type']} at "
          f"{dhf.rounded(spread['worst_spread'], 4)}")
    print(f"rho               {dhf.rounded(spread['rho_seed'], 4)} (seed), "
          f"{dhf.rounded(spread['rho_all'], 4)} (all perturbations)")
    print(f"same mechanism    {report['same_mechanism']}")
    return 0


# ---------------------------------------------------------------------------
#  the lattice round (Phase 123)
# ---------------------------------------------------------------------------

def _plain(value: object) -> object:
    """Fractions as strings, so a report prints as JSON."""
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def _hole_census(args: argparse.Namespace) -> int:
    """All 23 Niemeier types: the census, the control and the L5 cells.

    ``--write`` re-takes the census and the ensembles (long); without it the
    stored one is read and its freshness reported.
    """
    if args.write:
        path = hcs.write_measurements(jobs=args.jobs)
        print(f"wrote {path}")
        print(f"digest {hcs.module_digest()}")
        return 0
    condition = hcs.state()
    report = ltc.hole_census_report()
    if not report["available"]:
        print(f"cache             {condition['verdict']}")
        print(report["reason"])
        return 1
    if args.json:
        print(json.dumps(_plain({
            "cache": condition["verdict"],
            "types_reached": report["types_reached"],
            "catalogue": report["catalogue"],
            "by_stage": report["by_stage"],
            "unreached": report["unreached"],
            "control_holds": report["control_holds"],
            "cells": [{k: c[k] for k in ("starts", "q0", "gate", "ratio",
                                          "locally_certified")}
                      for c in report["cells"]],
            "marks": report["marks"],
        }), indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    print(f"types reached     {report['types_reached']} of "
          f"{report['catalogue']}  by stage {report['by_stage']}")
    print(f"control           {report['control_holds']} of "
          f"{len(report['control'])} hold")
    for c in report["cells"]:
        print(f"  n={c['starts']:<5} Q0 {c['q0']}/{c['gate']}  ratio "
              f"{c['ratio']}  per-hole {c['locally_certified']}")
    print(f"marks             {report['marks']}")
    return 0


def _patience_census(args: argparse.Namespace) -> int:
    """The post-hoc follow-up of the hole census (Phase 123): the three
    centres the census left uncertified, re-read with a longer patience.

    ``--write`` re-takes it (long); without it the stored one is read.
    """
    if args.write:
        path = pcs.write_measurements(jobs=args.jobs)
        print(f"wrote {path}")
        print(f"digest {pcs.module_digest()}")
        return 0
    condition = pcs.state()
    report = ltc.hole_census_report()
    post_hoc = report.get("post_hoc", {}) if report["available"] else {}
    if not post_hoc.get("available"):
        print(f"cache             {condition['verdict']}")
        print(post_hoc.get("reason", report.get("reason", "")))
        return 1
    top = post_hoc["cells"][-1]
    if args.json:
        print(json.dumps(_plain({
            "cache": condition["verdict"],
            "probes": post_hoc["probes"], "patience": post_hoc["patience"],
            "entries": [{k: e[k] for k in ("type", "certified", "vertex_count",
                                           "starts_run")}
                        for e in post_hoc["entries"]],
            "types_reached": post_hoc["types_reached"],
            "control_holds": post_hoc["control_holds"],
            "top": {k: top[k] for k in ("starts", "q0", "gate", "ratio",
                                        "locally_certified")},
            "marks": post_hoc["marks"],
        }), indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}  (post hoc)")
    print(f"probes, patience  {post_hoc['probes']}, {post_hoc['patience']}")
    for e in post_hoc["entries"]:
        print(f"  {e['type']}: certified {e['certified']}, "
              f"{e['vertex_count']} vertices after {e['starts_run']} starts")
    print(f"types reached     {post_hoc['types_reached']}")
    print(f"control           {post_hoc['control_holds']} of "
          f"{len(post_hoc['control'])} hold")
    print(f"at {top['starts']} starts  Q0 {top['q0']}/{top['gate']}  ratio "
          f"{top['ratio']}  per-hole {top['locally_certified']}")
    return 0


def _probe_budget(args: argparse.Namespace) -> int:
    """The certifying reading's stopping rule (Phase 124): no barren stop and
    a proved budget, on the 23 references and the held-out walks."""
    if args.write:
        path = prb.write_measurements(jobs=args.jobs)
        print(f"wrote {path}")
        print(f"digest {prb.module_digest()}")
        return 0
    condition = prb.state()
    report = prb.probe_budget_report()
    if not report["available"]:
        print(f"cache             {condition['verdict']}")
        print(report["reason"])
        return 1
    if args.json:
        print(json.dumps(_plain({k: v for k, v in report.items()
                                 if k not in ("references", "shares")}),
                         indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    print(f"budget            {report['budget']} starts, no barren stop")
    print(f"shares            k * min share >= 1/2 at every hole and seed: "
          f"{report['shares']['holds']} (least {report['shares']['least']})")
    print(f"references        {report['references_certified']} of "
          f"{len(report['references'])} certified as recorded")
    print(f"held-out walks    {report['reached']} of {report['walks']} reach "
          f"a deep hole; the rule certifies {report['rule_certified']}, the "
          f"census convention {report['census_certified']}")
    print(f"starts            median {report['median_starts']}, max "
          f"{report['max_starts']}")
    print(f"marks             {report['marks']}")
    return 0


def _ops_ladder(args: argparse.Namespace) -> int:
    """The operations ladder and GLM-BAT (Phase 125): the declared battery,
    the marks, hypothesis H, and the post-hoc agreement of the two
    interpreters."""
    from .reasoning import operations as ops
    report = ops.operations_report(scripts=not args.fast)
    agreement = ops.interpreter_agreement() if args.agreement else None
    if args.json:
        out = {"marks": report["marks"], "hypothesis_H":
               report["hypothesis_H"], "certificates": report["certificates"],
               "projection": {k: v for k, v in
                              report["ladder"]["projection"].items()
                              if k != "inverted"},
               "carrier": report["ladder"]["carrier"]}
        if agreement is not None:
            out["agreement"] = agreement
        print(json.dumps(_plain(out), indent=1, sort_keys=True))
        return 0
    lad, mac, eng, que = (report["ladder"], report["machine"],
                          report["english"], report["questions"])
    note, car, proj = lad["note"], lad["carrier"], lad["projection"]
    print(f"register          {note['terms']} terms (the note holds "
          f"{note['terms_in_note']}), {len(note['layering_violations'])} "
          f"layering violations, {len(note['ungrounded'])} ungrounded, "
          f"{len(note['idle_primitives'])} idle primitives")
    print(f"carrier           {car['round_trips']} round trips, "
          f"{car['distinct']} distinct; {car['distinct_ground_sets']} "
          f"distinct ground sets")
    print(f"machine battery   {mac['as_declared']} of {mac['runs']} as "
          f"declared, {mac['wrong']} wrong")
    print(f"language          {eng['read_back']} of {eng['lines_said']} lines "
          f"read back; {eng['programs_as_declared']} of 6 English programs")
    print(f"questions         {que['as_declared']} of {que['questions']} as "
          f"declared, {que['wrong']} wrong")
    c = report["certificates"]
    print(f"column 3          {c['verified']} of {c['scripts']} scripts "
          f"verify; {c['rejected']} of {c['mutations']} mutations rejected")
    print(f"relations         {lad['relations']}")
    print(f"cross-overs       {sum(r['resolves'] for r in lad['crossovers'])} "
          f"of {len(lad['crossovers'])} resolve")
    print(f"hypothesis H      {proj['monotone']} of {proj['edges']} edges "
          f"monotone ({proj['share']}, threshold {proj['threshold']}): "
          f"{'holds' if proj['holds'] else 'missed'}")
    if agreement is not None:
        print(f"agreement         {agreement['agree']} of "
              f"{agreement['programs'] - agreement['undecided']} decided "
              f"generated programs ({agreement['halted']} halted, "
              f"{agreement['never']} never, {agreement['undecided']} "
              f"undecided); {agreement['lines_read_back']} of "
              f"{agreement['lines']} lines read back")
    print(f"marks             {report['marks']}")
    return 0 if all(report["marks"].values()) else 1


def _inert_counter(args: argparse.Namespace) -> int:
    """Inert variables (Phase 126): the battery, the questions, column 3, the
    non-interference on Phase 125 and the soundness control."""
    from .reasoning import inert_counter as ic
    report = ic.inert_counter_report()
    if args.json:
        out = {k: v for k, v in report.items()
               if k not in ("battery", "questions")}
        print(json.dumps(_plain(out), indent=1, sort_keys=True))
        return 0
    bat, que, cer = report["battery"], report["questions"], report["certificates"]
    ni, snd = report["noninterference"], report["soundness"]
    for row in bat["rows"]:
        print(f"{row['id']:<4} {'as declared' if row['as_declared'] else 'WRONG':<12}"
              f" {row['got']}")
    print(f"battery           {bat['programs'] - bat['wrong']} of "
          f"{bat['programs']} as declared")
    print(f"questions         {que['questions'] - que['wrong']} of "
          f"{que['questions']} as declared")
    print(f"column 3          {cer['verified']} of {cer['scripts']} scripts "
          f"verify; {cer['rejected']} of {cer['mutations']} mutations rejected")
    print(f"phase 125         {ni['runs'] - ni['machine_wrong']} of "
          f"{ni['runs']} runs, {ni['questions'] - ni['questions_wrong']} of "
          f"{ni['questions']} questions, {ni['english']} of 6 English "
          f"programs; generated: {ni['generated_kept']} kept, "
          f"{ni['generated_changed']} changed, "
          f"{ni['generated_newly_certified']} newly certified, "
          f"{ni['generated_still_undecided']} still undecided")
    print(f"soundness         {len(snd['certified'])} certified, "
          f"{len(snd['halted_within_long_budget'])} halt within "
          f"{ic.LONG_BUDGET} steps; N3 halts after {snd['n3_steps']} steps "
          f"and is {'refused' if snd['n3_refused'] else 'NOT refused'}")
    print(f"marks             {report['marks']}")
    return 0 if all(report["marks"].values()) else 1


def _shortest_tag(args: argparse.Namespace) -> int:
    """The shortest tag (Phase 135): the proved floors, the census of the
    constructions, and the search on the gap of
    ``studies/SHORTEST_TAG_STUDY.md``."""
    from .reasoning import shortest_tag as stg
    report = stg.shortest_tag_report(moves=args.moves)
    if args.json:
        print(json.dumps(_plain(report), indent=1, sort_keys=True))
        return 0
    s2, s3, s4, s5 = (report[k] for k in ("S2", "S3", "S4", "S5"))
    print(f"floor, any tag    D=1: {report['floor_general'][1]}, "
          f"D=3: {report['floor_general'][3]}, D=5: {report['floor_general'][5]} bits")
    print(f"floor, built on 7 D=1: {report['floor_built'][1]}, "
          f"D=3: {report['floor_built'][3]}, D=5: {report['floor_built'][5]} bits")
    print(f"constructions     least octad weight {s2['min_weight']} at "
          f"{s2['lengths']} bits")
    print(f"7-bit kernel      {s3['kernel']} codewords, {s3['kernel_octads']} "
          f"octads, at most {s3['most_avoiding_one_coordinate']} avoid a "
          f"coordinate (cap 24)")
    print(f"7-bit values      {s4['values']} of 127 taken by octads, "
          f"multiplicities {s4['multiplicities']}")
    for key, v in s5["control"].items():
        print(f"control {key:<9} found by {v['found']} of {v['of']} seeds, "
              f"ranks {v['ranks']}")
    for key, v in s5["gap"].items():
        print(f"gap     {key:<9} least deficit {v}")
    print(f"marks             {report['marks']}")
    return 0 if all(report["marks"].values()) else 1


def _connected_two(args: argparse.Namespace) -> int:
    """The second connected-machine round (Phase 136): the wiring census, the
    stream tools against independent references, non-interference, the
    phrased and tool batteries -- the marks of
    ``studies/CONNECTED_MACHINE_TWO_STUDY.md``."""
    from .evaluation import connected_two_cases as c2
    report = c2.measure()
    if args.json:
        print(json.dumps(_plain(report), indent=1, sort_keys=True))
        return 0
    m = report["marks"]
    w = m["W1"]["census"]
    print(f"W1 wiring         {w['reached']} of {w['reasoning']} reasoning "
          f"modules reached, {len(w['declared'])} declared, undeclared "
          f"{w['undeclared']}, stale {w['stale_declarations']}")
    print(f"W2 Lean           {m['W2']['file']}: missing {m['W2']['missing']}, "
          f"sorry {m['W2']['sorry']}")
    print(f"W3 cf             {m['W3']['surds_agree']} of {m['W3']['surds']} "
          f"surds agree; pi {m['W3']['pi']}, e {m['W3']['e']}, "
          f"phi {m['W3']['phi']}")
    print(f"W4 mobius         {m['W4']['agree']} of {m['W4']['cases']} agree "
          f"with the quadratic recurrence, {m['W4']['direct_agree']} with "
          "the direct expansion")
    for r in m["W5"]["rows"]:
        print(f"W5 rational       {r['text']}: {r['emitted']} term(s) "
              f"emitted, sound {r['sound']}, complete {r['complete']}")
    print(f"W6 interference   {m['W6']['matched']} of "
          f"{m['W6']['declared_texts']} declared texts match an opening")
    print(f"W7 phrased        {m['W7']['as_declared']} of "
          f"{m['W7']['questions']} as declared ({m['W7']['answered']} "
          "answered)")
    print(f"W8 tools          {m['W8']['tool_as_declared']} of "
          f"{m['W8']['tool_cases']} as declared; gate certificate equals "
          f"search on {m['W8']['gate_agree']} of {m['W8']['gate_pairs']}")
    print(f"marks met         {report['met']} of {report['taken']}")
    return 0 if report["met"] == report["taken"] else 1


def _tool_verdicts(args: argparse.Namespace) -> int:
    """The tool-verdicts round (Phase 138): a tool's yes/no answer as a
    planner step, conditionals, the unrolled search, the Farey certificate --
    the marks of ``studies/TOOL_VERDICTS_STUDY.md``."""
    from .evaluation import tool_verdicts_cases as tvd
    report = tvd.measure(scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(_plain(report), indent=1, sort_keys=True))
        return 0
    m = report["marks"]
    print(f"T1 Lean           {m['T1']['file']}: missing {m['T1']['missing']}, "
          f"sorry {m['T1']['sorry']}")
    print(f"T2 verdicts       {m['T2']['as_expected']} of "
          f"{m['T2']['questions']} held-out questions as expected")
    t3 = m["T3"]
    if t3.get("skipped"):
        print("T3 column 3       skipped (--no-scripts)")
    else:
        print(f"T3 column 3       {t3['verified']} of {t3['chains']} chains "
              f"verified; {t3['caught']} of {t3['mutants']} mutants caught")
    print(f"T4 rewordings     {m['T4']['right']} of {m['T4']['questions']} "
          f"right, {m['T4']['read']} read, {len(m['T4']['wrong'])} wrong; "
          f"Phase 137 misses now right {m['T4']['phase137_now_right']} of "
          f"{m['T4']['phase137_misses']}")
    print(f"T5 interference   {len(m['T5']['matched'])} of "
          f"{m['T5']['declared_texts']} declared texts read; "
          f"{len(m['T5']['moved'])} of {m['T5']['corpus']} stepwise cases "
          "moved")
    print(f"T6 certificate    {m['T6']['grid_agree']} of {m['T6']['grid']} "
          f"grid cases agree with the exhaustive search; "
          f"{m['T6']['large_certified']} of {m['T6']['large']} bounds up to "
          "10^60 certified")
    print(f"marks met         {report['met']} of {report['taken']}")
    return 0 if report["met"] == report["taken"] else 1


def _tool_values(args: argparse.Namespace) -> int:
    """The tool-values round (Phase 137): a tool's number composed by the
    stepwise planner, the convergent and best-approximation tools against
    independent references, non-interference, the held-out rewordings -- the
    marks of ``studies/TOOL_VALUES_STUDY.md``."""
    from .evaluation import tool_values_cases as tvc
    report = tvc.measure(scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(_plain(report), indent=1, sort_keys=True))
        return 0
    m = report["marks"]
    print(f"V1 Lean           {m['V1']['file']}: missing {m['V1']['missing']}, "
          f"sorry {m['V1']['sorry']}")
    print(f"V2 composed       {m['V2']['as_declared']} of "
          f"{m['V2']['questions']} as declared ({m['V2']['answered']} "
          "answered)")
    v3 = m["V3"]
    if v3.get("skipped"):
        print("V3 column 3       skipped (--no-scripts)")
    else:
        print(f"V3 column 3       {v3['verified']} of {v3['chains']} chains "
              f"verified; {v3['caught']} of {v3['mutants']} mutants caught")
    print(f"V4 convergents    {m['V4']['surd_agree']} of "
          f"{m['V4']['surd_cases']} surd cases and {m['V4']['pi_agree']} of "
          f"{m['V4']['pi_cases']} pi cases agree with the references")
    print(f"V5 nearest        {m['V5']['agree']} of {m['V5']['cases']} agree "
          "with the exhaustive search")
    print(f"V6 interference   {m['V6']['matched']} of "
          f"{m['V6']['declared_texts']} declared texts read; "
          f"{len(m['V6']['moved'])} of {m['V6']['corpus']} stepwise cases "
          "moved")
    print(f"V7 single         {m['V7']['as_declared']} of "
          f"{m['V7']['questions']} as declared")
    print(f"V8 held out       {m['V8']['read']} of {m['V8']['questions']} "
          f"read, {m['V8']['right']} right, {len(m['V8']['wrong'])} wrong; "
          f"{m['V8']['rederived']} of {m['V8']['corrected']} corrected "
          "sheet values re-derived")
    print(f"marks met         {report['met']} of {report['taken']}")
    return 0 if report["met"] == report["taken"] else 1


def _protected_tag(args: argparse.Namespace) -> int:
    """The protected tag and the carrier read (Phase 134): the tied battery
    through the eleven- and fifteen-bit tags, the seven-bit control, three
    flips past the radius, heavy corruption, and the marks of
    ``studies/PROTECTED_TAG_STUDY.md``."""
    from .reasoning import carrier_read as crd
    report = crd.protected_tag_report()
    if args.json:
        print(json.dumps(_plain(report), indent=1, sort_keys=True))
        return 0
    p2, p3, p4, p5, p6 = (report[k] for k in ("P2", "P3", "P4", "P5", "P6"))
    print(f"octad tag weight  least {p2['min_weight_7']} (7 bits), "
          f"{p2['min_weight_11']} (11 bits), {p2['min_weight_15']} (15 bits)")
    for key, label in (("tag15_radius2", "15-bit, radius 2"),
                       ("tag11_radius1", "11-bit, radius 1")):
        t = p3[key]
        print(f"{label:<18}{t['resolved']} of {p3['reads']} tied reads "
              f"resolved, {t['wrong']} wrong")
    t = p4["tag7_one_flip"]
    print(f"7-bit, one flip   {t['wrong']} wrong, {t['contradicted']} "
          f"contradicted")
    for key in ("radius2", "radius1"):
        t, h = p5[key], p5["post_hoc_consecutive"][key]
        print(f"3 flips, {key:<9}{t['wrong']} wrong as declared; "
              f"{h['wrong']} wrong with consecutive flips (post hoc)")
    print(f"heavy, 5-7 flips  decoder alone {p6['wrong_decoder_alone']} "
          f"wrong; intact 7-bit tag {p6['wrong_tag7_intact']}; 15-bit tag "
          f"{p6['wrong_tag15_radius2']}")
    print(f"marks             {report['marks']}")
    return 0 if all(report["marks"].values()) else 1


def _designed_substrate(args: argparse.Namespace) -> int:
    """The designed substrate, brought in (Phase 133): the sender-tag and
    soft-certificate fork stages, the designed alternatives, the floor and
    the marks of ``studies/DESIGNED_SUBSTRATE_STUDY.md``."""
    from .reasoning import designed_substrate as dsub
    report = dsub.designed_substrate_report()
    if args.json:
        print(json.dumps(_plain(report), indent=1, sort_keys=True))
        return 0
    s2, s4, s5 = report["S2"], report["S4"], report["S5"]
    bad = s2["corrupted_tag"]
    print(f"sender tag        {s2['resolved']} of {s2['reads']} weight-4 reads "
          f"resolved, {s2['wrong']} wrong ({s2['tag_bits_per_carrier']} bits "
          f"per carrier; the hard word alone resolves "
          f"{s2['hard_word_alone_resolved']})")
    print(f"corrupted tag     {bad['contradicted']} contradicted, "
          f"{bad['wrong']} wrong")
    print(f"soft, K4b         {s4['resolved']} of {s4['reads']} resolved, "
          f"{s4['contradicted']} refused (truth within radius on "
          f"{s4['truth_within_radius']})")
    print(f"soft, gentle G    {s5['resolved']} of {s5['reads']} resolved, "
          f"{s5['wrong']} wrong")
    for row in report["S6"]["rows"]:
        print(f"extension {row['lambda']:<5}   {row['silent']} silent "
              f"weight-4 miscorrections")
    print(f"GLM code          {report['S6']['golay']['silent']} silent")
    s7 = report["S7"]
    print(f"floor             {s7['received_at_distance_four']} received "
          f"words at distance 4 (floor {s7['floor']}); snap on the probe "
          f"{s7['snap_right']} (declared {s7['one_sixth']})")
    print(f"marks             {report['marks']}")
    return 0 if not report["not_met"] else 1


def _affine_output(args: argparse.Namespace) -> int:
    """Passes that print a counter, long output and the diagnosis of a
    refusal (Phase 132): the batteries, the questions, column 3, the
    non-interference and the soundness control."""
    from .reasoning import affine_output as ao
    report = ao.affine_output_report()
    if args.json:
        out = {k: v for k, v in report.items()
               if k not in ("battery", "questions")}
        print(json.dumps(_plain(out), indent=1, sort_keys=True))
        return 0
    for row in report["battery"]["rows"]:
        print(f"{row['id']:<4} {'as declared' if row['as_declared'] else 'WRONG'}"
              f"  {row['got']}")
    for row in report["diagnosis"]["rows"]:
        print(f"{row['id']:<4} {'as declared' if row['as_declared'] else 'WRONG'}"
              f"  {row['got']}")
    que, cer = report["questions"], report["certificates"]
    print(f"questions         {que['questions'] - que['wrong']} of "
          f"{que['questions']} as declared; missed {que['missed']}")
    print(f"NRCI (diagnosis)  {report['diagnosis']['nrci']}")
    print(f"closed forms      {report['prediction']['held']} of "
          f"{report['prediction']['variables']} predict the next visits")
    print(f"column 3          {cer['verified']} of {cer['scripts']} verify; "
          f"{cer['rejected']} of {cer['mutations']} mutations rejected; "
          f"P2 script {cer['p2_script_bytes']} bytes (claim "
          f"{cer['p2_claim_bytes']}, checker {cer['checker_bytes']})")
    ni, snd = report["noninterference"], report["soundness"]
    print(f"non-interference  battery {ni['battery_kept']}/{ni['battery_total']}"
          f", questions {ni['questions_kept']}/{ni['questions_total']}, "
          f"generated {ni['generated_kept']}/300")
    print(f"soundness         {len(snd['halts_agree'])} halts agree, "
          f"{len(snd['halts_disagree'])} disagree; controls {snd['controls']}")
    print(f"marks             {report['marks']}")
    return 0 if all(report["marks"].values()) else 1


def _constant_bound(args: argparse.Namespace) -> int:
    """Constant bounds and repeated output (Phase 131): the battery, the
    questions, column 3, the non-interference on Phases 125, 126 and 130 and
    the soundness control."""
    from .reasoning import constant_bound as cb
    report = cb.constant_bound_report()
    if args.json:
        out = {k: v for k, v in report.items()
               if k not in ("battery", "questions")}
        print(json.dumps(_plain(out), indent=1, sort_keys=True))
        return 0
    bat, que, cer = report["battery"], report["questions"], report["certificates"]
    ni, snd = report["noninterference"], report["soundness"]
    for row in bat["rows"]:
        label = ("as declared" if row["as_declared"] else
                 "JUMPS DIFFER" if row["as_declared_but_jumps"] else "WRONG")
        print(f"{row['id']:<4} {label:<13} {row['got']}")
    print(f"battery           {bat['programs'] - bat['wrong']} of "
          f"{bat['programs']} as declared; "
          f"{bat['programs'] - bat['wrong_apart_from_jumps']} as declared "
          f"apart from the pass jumped")
    print(f"questions         {que['questions'] - que['wrong']} of "
          f"{que['questions']} as declared")
    print(f"column 3          {cer['verified']} of {cer['scripts']} scripts "
          f"verify; {cer['rejected']} of {cer['mutations']} mutations rejected")
    print(f"phases 125-130    {ni['runs'] - ni['machine_wrong']} of "
          f"{ni['runs']} runs, {ni['questions'] - ni['questions_wrong']} of "
          f"{ni['questions']} questions, {ni['english']} of 6 English "
          f"programs; Phases 126 and 130: {ni['battery_kept']} of "
          f"{ni['battery_total']} programs and {ni['questions_kept']} of "
          f"{ni['questions_total']} questions kept; L10, L11 as K1, K2: "
          f"{ni['l10_l11_as_k1_k2']}; generated: {ni['generated_kept']} kept, "
          f"{ni['generated_changed']} changed, {ni['generated_new_jumps']} "
          f"with new jumps")
    print(f"soundness         halts agreeing with a plain run: "
          f"{', '.join(snd['halts_agree'])} (disagreeing: "
          f"{len(snd['halts_disagree'])}); never, holding: "
          f"{', '.join(snd['never_hold'])} (halting: {len(snd['never_halt'])});"
          f" refused controls, plainly: {snd['controls']}")
    print(f"marks             {report['marks']}")
    return 0 if all(report["marks"].values()) else 1


def _counter_lasso(args: argparse.Namespace) -> int:
    """Counter lassos (Phase 130): the battery, the questions, column 3, the
    non-interference on Phases 125 and 126 and the soundness control."""
    from .reasoning import counter_lasso as cl
    report = cl.counter_lasso_report()
    if args.json:
        out = {k: v for k, v in report.items()
               if k not in ("battery", "questions")}
        print(json.dumps(_plain(out), indent=1, sort_keys=True))
        return 0
    bat, que, cer = report["battery"], report["questions"], report["certificates"]
    ni, snd = report["noninterference"], report["soundness"]
    for row in bat["rows"]:
        print(f"{row['id']:<4} {'as declared' if row['as_declared'] else 'WRONG':<12}"
              f" {row['got']}")
    print(f"battery           {bat['programs'] - bat['wrong']} of "
          f"{bat['programs']} as declared")
    print(f"questions         {que['questions'] - que['wrong']} of "
          f"{que['questions']} as declared")
    print(f"column 3          {cer['verified']} of {cer['scripts']} scripts "
          f"verify; {cer['rejected']} of {cer['mutations']} mutations rejected")
    print(f"phases 125, 126   {ni['runs'] - ni['machine_wrong']} of "
          f"{ni['runs']} runs, {ni['questions'] - ni['questions_wrong']} of "
          f"{ni['questions']} questions, {ni['english']} of 6 English "
          f"programs; Phase 126: {ni['inert_kept']} of {ni['inert_total']} "
          f"programs and {ni['inert_questions_kept']} of "
          f"{ni['inert_questions']} questions kept; generated: "
          f"{ni['generated_kept']} kept, {ni['generated_changed']} changed, "
          f"{ni['generated_newly_decided']} newly decided "
          f"{list(ni['generated_newly_decided_ids'])}, "
          f"{ni['generated_still_undecided']} still undecided")
    print(f"soundness         halts agreeing with a plain run of up to "
          f"{cl.LONG_BUDGET} steps: {', '.join(snd['halts_agree'])} "
          f"(disagreeing: {len(snd['halts_disagree'])}); never, holding for "
          f"{cl.NEVER_BUDGET} plain steps: {', '.join(snd['never_hold'])} "
          f"(halting: {len(snd['never_halt'])}); refused controls, plainly: "
          f"{snd['controls']}")
    print(f"marks             {report['marks']}")
    return 0 if all(report["marks"].values()) else 1


def _configuration_classifier(args: argparse.Namespace) -> int:
    """The L5 answer rule over the 44 deep-hole queries, with absences."""
    if args.write:
        path = cfq.write_measurements()
        print(f"wrote {path}")
        print(f"digest {cfq.module_digest()}")
        return 0
    condition = cfq.state()
    report = ltc.lattice_completion_report()["classifier"]
    if not report["available"]:
        print(f"cache             {condition['verdict']}")
        print(report["reason"])
        return 1
    ten = {k: v for k, v in report["ten"].items() if k != "rows"}
    wide = (None if report["twenty_three"] is None else
            {k: v for k, v in report["twenty_three"].items() if k != "rows"})
    if args.json:
        print(json.dumps(_plain({"cache": condition["verdict"], "ten": ten,
                                 "twenty_three": wide,
                                 "marks": report["marks"]}),
                         indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    print(f"ten references    {ten['correct']} correct, {ten['wrong']} wrong, "
          f"{ten['refused']} refused of {ten['queries']} (joint "
          f"{ten['joint_correct']})")
    print(f"absences          {ten['absences']} of {ten['absence_slots']}, "
          f"{ten['false_absences']} false")
    if wide is not None:
        print(f"23 references     {wide['correct']} correct, {wide['wrong']} "
              f"wrong, {wide['refused']} refused")
    print(f"marks             {report['marks']}")
    return 0


def _frozen_path(args: argparse.Namespace) -> int:
    """The lattice round's frozen-path comparison (mark B5)."""
    if args.write:
        path = frp.write_measurements()
        print(f"wrote {path}")
        print(f"digest {frp.module_digest()}")
        return 0
    condition = frp.state()
    report = frp.frozen_path_report()
    if not report["available"]:
        print(f"cache             {condition['verdict']}")
        print(report["reason"])
        return 1
    if args.json:
        print(json.dumps(_plain(report), indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    print(f"cases             {report['present']} of {report['cases']} present")
    print(f"same status       {report['same_status']} of {report['cases']}")
    print(f"same text         {report['same_text']} of {report['present']}")
    for row in report["moved"]:
        print(f"  moved           {row['id']}: {row['cause']}")
    print(f"new cases         {', '.join(report['new_cases']) or 'none'}")
    print(f"B5                {report['holds']}")
    return 0 if report["holds"] else 1


def _empty_rungs(args: argparse.Namespace) -> int:
    """The norm-2 and norm-256 candidates and the declared filling."""
    if args.write:
        path = emr.write_measurements()
        print(f"wrote {path}")
        print(f"digest {emr.module_digest()}")
        return 0
    condition = emr.state()
    report = emr.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    filling = report["filling"]
    trials = [{"norm": t["norm"], "candidate": t["candidate"],
               "kept": t["kept"], "retired": t["retired"]}
              for t in filling["trials"]]
    final = {k: report["final"][k] for k in ("correct", "wrong", "refused")
             if k in report["final"]}
    if args.json:
        print(json.dumps(_plain({"cache": condition["verdict"],
                                 "reproduces": report["reproduces"],
                                 "filled": filling["filled"],
                                 "trials": trials, "final": final,
                                 "marks": report["marks"]}),
                         indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    print(f"reproduces        {report['reproduces']}")
    for t in trials:
        print(f"  norm {t['norm']:<4} {t['candidate']:<8} kept {t['kept']}")
    print(f"filled            {filling['filled']}")
    print(f"final ladder      {final}")
    print(f"marks             {report['marks']}")
    return 0


def _norm256_hex(args: argparse.Namespace) -> int:
    """Norm 256 and the hex colour (Phase 127): the three candidates, the
    filling, the held-out set and the hex shortcut."""
    if args.write:
        path = n256.write_measurements()
        print(f"wrote {path}")
        print(f"digest {n256.module_digest()}")
        return 0
    condition = n256.state()
    report = n256.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    filling, held, short = (report["filling"], report["held_out"],
                            report["shortcut"])
    trials = [{"candidate": t["candidate"], "kept": t["kept"],
               "wrong": t["row"]["wrong"], "correct": t["row"]["correct"],
               "unique_correct": t["row"]["unique_correct"]}
              for t in filling["trials"]]
    if args.json:
        print(json.dumps(_plain({"cache": condition["verdict"],
                                 "kept": filling["kept"], "trials": trials,
                                 "marks": report["marks"]}),
                         indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    for t in trials:
        print(f"  {t['candidate']:<5} correct {t['correct']:<4} wrong "
              f"{t['wrong']:<3} unique {t['unique_correct']:<3} kept {t['kept']}")
    print(f"kept              {filling['kept']}")
    for key in ("correct", "wrong", "refused"):
        print(f"  568 queries     {key:<8} {report['final'][key]}")
    for key, row in held["alone"].items():
        print(f"  held out {key:<5} correct {row['correct']:<4} wrong "
              f"{row['wrong']}")
    print(f"held-out ladder   correct {held['final']['correct']} wrong "
          f"{held['final']['wrong']} (base: {held['base']['correct']} / "
          f"{held['base']['wrong']})")
    print(f"hex shortcut      W has {short['colours']} colours; "
          f"{short['agree']} of {short['points']} agree")
    print(f"marks             {report['marks']}")
    return 0


def _cell_guard(args: argparse.Namespace) -> int:
    """The cell guard (Phase 128): the ladder's answers certified to be the
    nearest carrier, on three query sets, beside the union retirement."""
    if args.write:
        path = cgd.write_measurements()
        print(f"wrote {path}")
        print(f"digest {cgd.module_digest()}")
        return 0
    condition = cgd.state()
    report = cgd.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    rows = {name: {"plain_correct": r["plain"]["correct"],
                   "plain_wrong": r["plain"]["wrong"],
                   "guarded_correct": r["guarded"]["correct"],
                   "guarded_wrong": r["guarded"]["wrong"],
                   "nearest": r["nearest"]}
            for name, r in report["read"].items()}
    union = {"ladder": report["union"]["ladder"],
             "third_correct": report["union_third"]["correct"],
             "third_wrong": report["union_third"]["wrong"]}
    if args.json:
        print(json.dumps(_plain({"cache": condition["verdict"], "sets": rows,
                                 "union": union, "marks": report["marks"]}),
                         indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    for name, r in rows.items():
        print(f"  {name:<9} ladder {r['plain_correct']:>3} correct "
              f"{r['plain_wrong']:>2} wrong   guarded {r['guarded_correct']:>3}"
              f" correct {r['guarded_wrong']:>2} wrong   nearest carrier "
              f"{r['nearest']['correct']} / {r['nearest']['wrong']} wrong / "
              f"{r['nearest']['tie']} tie")
    print(f"union retirement  {' '.join(union['ladder'])}: third set "
          f"{union['third_correct']} correct {union['third_wrong']} wrong")
    print(f"marks             {report['marks']}")
    return 0


def _placement_guard(args: argparse.Namespace) -> int:
    """The placement guard (Phase 129): the cell guard with a radius read
    from the carriers, on four query sets, beside the union retirement."""
    if args.write:
        path = plg.write_measurements()
        print(f"wrote {path}")
        print(f"digest {plg.module_digest()}")
        return 0
    condition = plg.state()
    report = plg.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    rows = {name: {kind: [r[kind]["correct"], r[kind]["wrong"]]
                   for kind in ("plain", "cell", "placed")}
            for name, r in report["read"].items()}
    union = {"ladder": report["union"]["ladder"],
             "fourth_correct": report["union_fourth"]["correct"],
             "fourth_wrong": report["union_fourth"]["wrong"]}
    if args.json:
        print(json.dumps(_plain({"cache": condition["verdict"], "sets": rows,
                                 "union": union, "marks": report["marks"]}),
                         indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    for name, r in rows.items():
        print(f"  {name:<9} ladder {r['plain'][0]:>3}/{r['plain'][1]:<2} "
              f"cell guard {r['cell'][0]:>3}/{r['cell'][1]:<2} "
              f"placement guard {r['placed'][0]:>3}/{r['placed'][1]:<2}"
              f" (correct/wrong)")
    print(f"union retirement  {' '.join(union['ladder'])}: fourth set "
          f"{union['fourth_correct']} correct {union['fourth_wrong']} wrong")
    print(f"marks             {report['marks']}")
    return 0


# ---------------------------------------------------------------------------
#  cumulativity
# ---------------------------------------------------------------------------

def _cumulativity(args: argparse.Namespace) -> int:
    """The refinement check every declared layer family has to pass."""
    report = cml.cumulativity_report()
    if args.json:
        print(json.dumps({
            "families": [{"key": row["key"], "shipped": row["shipped"],
                          "passes": row["passes"],
                          "defects": list(row["defects"])}
                         for row in report["families"]],
            "edges_checked": report["edges_checked"],
            "non_edges_checked": report["non_edges_checked"],
            "holds": report["holds"],
        }, indent=1, sort_keys=True))
        return 0 if report["holds"] else 1
    print(f"families          {report['count']} "
          f"({report['shipped']} shipped)")
    print(f"edges             {report['edges_checked']} checked, "
          f"{report['non_edges_checked']} declared non-edges")
    for row in report["families"]:
        state = "passes" if row["passes"] else "DEFECT"
        ships = "ships" if row["shipped"] else "not shipped"
        print(f"  {row['key']:<26} {state:<7} ({ships})")
        for defect in row["defects"]:
            print(f"    {defect}")
        for loss in row["conflations"]:
            if loss["count"]:
                print(f"    conflates {loss['count']} pair(s) at "
                      f"{loss['rung']} -- a resolution, not a defect")
    print(f"rule holds        {report['holds']}")
    return 0 if report["holds"] else 1


# ---------------------------------------------------------------------------
#  ladder
# ---------------------------------------------------------------------------

def _ladder(args: argparse.Namespace) -> int:
    """The construction ladder: every rung, and the escalation that walks it.

    ``--write`` re-takes the measurement, which is about a minute of exact
    decoding; without it the stored one is read and its freshness reported.
    """
    if args.write:
        path = lesc.write_measurements()
        print(f"wrote {path}")
        print(f"digest {lesc.module_digest()}")
        return 0
    condition = lesc.state()
    report = lesc.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    best = report["best_fixed_rung"]
    if args.json:
        print(json.dumps({"cache": condition["verdict"],
                          "carriers": report["carriers"],
                          "orders": report["orders"]["totals"],
                          "fixed_rungs": report["fixed_rungs"]["totals"],
                          "oracle": report["oracle"],
                          "order_cost": report["order_cost"],
                          "cheapest_order": report["cheapest_order"]},
                         indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    print(f"carriers          {report['carriers']} over "
          f"{len(report['registers'])} registers, "
          f"{len(report['perturbations'])} perturbations")
    print("order             correct  wrong  refused        work")
    for name, scores in report["orders"]["totals"].items():
        print(f"  {name:<15} {scores['correct']:>6} {scores['wrong']:>6} "
              f"{scores['refused']:>8} {scores['cost']:>11}")
    print("rung alone        correct  wrong  refused        work")
    for rung, scores in report["fixed_rungs"]["totals"].items():
        if rung == "oracle":
            continue
        print(f"  {rung:<15} {scores['correct']:>6} {scores['wrong']:>6} "
              f"{scores['refused']:>8} {scores['cost']:>11}")
    print(f"oracle            {report['oracle']}")
    print(f"best single rung  {best['rung']} at {best['correct']}")
    print(f"cheapest order    {report['cheapest_order']}")
    print(f"rungs disagree    {report['agreement']['rungs_disagree']}")
    before = report.get("before")
    if before is not None:
        scores = before["orders"]["totals"]["middle_out"]
        print(f"before ({before['ladder_length']} rungs)  "
              f"{scores['correct']} correct, {scores['wrong']} wrong, "
              f"{scores['refused']} refused")
    sweep = report.get("length_sweep")
    if sweep is not None:
        print("ladder length     rungs  correct  wrong  refused  "
              "disagree  order-independent")
        for row in sweep["rows"]:
            wrong = max(int(value) for value in row["wrong"].values())
            print(f"  {'':<13} {row['length']:>5} "
                  f"{row['correct']['middle_out']:>8} {wrong:>6} "
                  f"{row['refused']['middle_out']:>8} "
                  f"{row['rungs_disagree']:>9}  "
                  f"{'yes' if row['order_independent'] else 'NO'}")
        print(f"longest safe      {sweep['longest_safe']} rungs; "
              f"first broken {sweep['first_broken']}")
    return 0



# ---------------------------------------------------------------------------
#  normladder, operations, blockers
# ---------------------------------------------------------------------------

def _normladder(args: argparse.Namespace) -> int:
    """The norm-indexed family of rungs, and the escalation over it."""
    from .reasoning import norm_escalation as nesc
    if args.write:
        path = nesc.write_measurements()
        print(f"wrote {path}")
        print(f"digest {nesc.module_digest()}")
        return 0
    condition = nesc.state()
    report = nesc.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    if args.json:
        print(json.dumps({
            "cache": condition["verdict"],
            "declared": report["declared"]["orders"]["totals"],
            "repaired": report["repaired"]["orders"]["totals"],
            "repair": {"ladder": report["repair"]["ladder"],
                       "safe": report["repair"]["safe"],
                       "gaps": report["repair"]["gaps"]},
            "sweep": {"longest_safe": report["sweep"]["longest_safe"],
                      "first_broken": report["sweep"]["first_broken"]},
        }, indent=1, sort_keys=True))
        return 0
    family = report["family"]
    print(f"cache             {condition['verdict']}")
    print(f"family            {family['rung_count']} rungs, "
          f"{len(family['completeness']['norms'])} norms, "
          f"complete {family['completeness']['complete']}, "
          f"chain holds {family['chain']['holds']}")
    print("ladder                                    rungs  correct  wrong  "
          "refused  safe")
    for key, title in (("declared", "the full power-of-two family"),
                       ("repaired", "after the retirement rule"),
                       ("chain", "the same family through B"),
                       ("named_rungs", "the eleven named rungs")):
        totals = report[key]["orders"]["totals"]["middle_out"]
        safe = totals["wrong"] == 0
        print(f"  {title:<39} {len(report[key]['ladder']):>5} "
              f"{totals['correct']:>8} {totals['wrong']:>6} "
              f"{totals['refused']:>8}  {'yes' if safe else 'NO'}")
    repair = report["repair"]
    print(f"repaired ladder   {' '.join(repair['ladder'])}")
    print(f"norms left empty  {list(repair['gaps'])}")
    print("family length     rungs  correct  wrong  refused  safe")
    for row in report["sweep"]["rows"]:
        print(f"  {'':<13} {row['length']:>5} "
              f"{row['correct']['middle_out']:>8} "
              f"{max(row['wrong'].values()):>6} "
              f"{row['refused']['middle_out']:>8}  "
              f"{'yes' if row['safe'] else 'NO'}")
    print(f"longest safe      {report['sweep']['longest_safe']} rungs; "
          f"first unsafe {report['sweep']['first_broken']}")
    return 0


def _operations(args: argparse.Namespace) -> int:
    """Escalation applied to operations that are not retrieval."""
    from .reasoning import operation_escalation as oesc
    if args.write:
        path = oesc.write_measurements()
        print(f"wrote {path}")
        print(f"digest {oesc.module_digest()}")
        return 0
    condition = oesc.state()
    report = oesc.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    rows = list(report["operations"]) + [report["equation"]]
    if args.json:
        print(json.dumps({"cache": condition["verdict"],
                          "operations": {row["operation"]: row["escalation"]
                                         for row in rows},
                          "helped": report["helped"],
                          "no_gain": report["no_gain"],
                          "unsafe": report["unsafe"]},
                         indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    print("operation     queries  correct  wrong  refused  best rung  prior  "
          "control   gain")
    for row in rows:
        score = row["escalation"]
        print(f"  {row['operation']:<11} {score['queries']:>6} "
              f"{score['correct']:>8} {score['wrong']:>6} "
              f"{score['refused']:>8} "
              f"{row['best_rung_score']['correct']:>10} "
              f"{row['control_label_prior']['correct']:>6} "
              f"{row['control_substrate_removed']['correct']:>8} "
              f"{row['gain_over_best_rung']:>6}")
    print(f"helped            {', '.join(report['helped']) or 'none'}")
    print(f"no gain           {', '.join(report['no_gain']) or 'none'}")
    print(f"unsafe            {', '.join(report['unsafe']) or 'none'}")
    return 0


def _second_reading(args: argparse.Namespace) -> int:
    """A second reading required to agree before an operation answers."""
    from .reasoning import second_reading as sread
    if args.write:
        path = sread.write_measurements()
        print(f"wrote {path}")
        print(f"digest {sread.module_digest()}")
        return 0
    condition = sread.state()
    report = sread.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    marks = report["marks_report"]
    if args.json:
        print(json.dumps({
            "cache": condition["verdict"],
            "adopted": marks["adopted"],
            "shipped": marks["shipped"],
            "verdict": marks["verdict"],
            "program": {key: row["program"]
                        for key, row in marks["verdicts"].items()},
        }, indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    print("operation     reading   queries  correct  wrong  refused")
    for row in report["operations"]:
        for key in ("primary", "code", "margin"):
            score = row["readings"][key]
            print(f"  {row['operation']:<11} {key:<8} {score['queries']:>7} "
                  f"{score['correct']:>8} {score['wrong']:>6} "
                  f"{score['refused']:>8}")
    print("configuration   program correct  wrong  refused  given up  "
          "removed  matched  M1 M2 M3 M4")
    for key in sorted(marks["verdicts"]):
        row = marks["verdicts"][key]
        score = row["program"]
        flags = " ".join("y " if row[mark] else "n "
                         for mark in ("M1", "M2", "M3", "M4"))
        print(f"  {key:<14} {score['correct']:>14} {score['wrong']:>6} "
              f"{score['refused']:>8} {row['answers_given_up']:>9} "
              f"{row['wrongs_removed']:>8} "
              f"{row['matched_control_wrongs_removed']:>8}  {flags}")
    print(f"adopted           {', '.join(marks['adopted']) or 'none'}")
    print(f"shipped           {marks['shipped'] or 'none'}")
    return 0


def _blockers(args: argparse.Namespace) -> int:
    """What is between this system and fuller reasoning, measured."""
    from .reasoning import blockers as blk
    if args.write:
        path = blk.write_measurements()
        print(f"wrote {path}")
        print(f"digest {blk.module_digest()}")
        return 0
    condition = blk.state()
    report = blk.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    probe = report["probe"]
    if args.json:
        print(json.dumps({"cache": condition["verdict"],
                          "probe": probe["canonical"],
                          "passed": probe["passed"],
                          "figures": report["figures"]},
                         indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    print(f"probe             {probe['canonical']['correct']} correct, "
          f"{probe['canonical']['wrong']} wrong, "
          f"{probe['canonical']['refused']} refused of {probe['questions']}; "
          f"pass mark {probe['pass_mark']['correct_at_least']} -- "
          f"passed {probe['passed']}")
    print(f"paraphrase        {probe['stable']} of {probe['questions']} "
          f"score the same both ways")
    print("blocker                                            measurement")
    for blocker in report["blockers"]:
        measured = " and ".join(
            f"{name.strip()} = {report['figures'].get(name.strip())}"
            for name in str(blocker["measurement"]).split(" and "))
        print(f"  {blocker['key']:<16} {measured}")
    ledger = {}
    for row in report["ledger"]:
        ledger[row["class"]] = ledger.get(row["class"], 0) + 1
    print("faculty ledger    " + ", ".join(f"{count} {name}"
                                           for name, count
                                           in sorted(ledger.items())))
    return 0


# ---------------------------------------------------------------------------
#  oracle
# ---------------------------------------------------------------------------

def _oracle(args) -> int:
    """Blocker 1's own experiment: the probe questions, hand-translated."""
    from .reasoning import probe_oracle as po
    report = po.oracle_report()
    if args.json:
        print(json.dumps({"counts": report["counts"],
                          "english_correct": report["english_correct"],
                          "parser_worth": report["parser_worth"],
                          "surface_worth": report["surface_worth"],
                          "witness_kinds": report["witness_kinds"]},
                         indent=1, sort_keys=True))
        return 0
    counts = report["counts"]
    print(f"questions         {report['questions']}")
    print(f"english           {report['english_correct']} correct as asked")
    print(f"translated        {counts['parsed']} parsed, "
          f"{counts['surface']} surface, {counts['absent']} absent")
    print(f"parser worth      {report['parser_worth']} questions")
    print(f"surface worth     {report['surface_worth']} questions")
    print("question         class     the query it should become")
    for row in report["rows"]:
        print(f"  {row['key']:<15} {row['class']:<8} "
              f"{row['query'] or '(not expressible)'}")
    return 0


# ---------------------------------------------------------------------------
#  fieldsurface
# ---------------------------------------------------------------------------

def _fieldsurface(args) -> int:
    """The field surface, measured against the prediction that bought it."""
    from .reasoning import field_surface as fs
    report = fs.surface_report()
    census = report["census"]
    if args.json:
        print(json.dumps({"before": report["before"],
                          "after": report["after"],
                          "moved": list(report["moved"]),
                          "predicted": report["predicted"],
                          "still_surface": list(report["still_surface"]),
                          "tables": census["tables"],
                          "rows": census["rows"],
                          "addressable_pairs": census["addressable_pairs"]},
                         indent=1, sort_keys=True))
        return 0
    before, after = report["before"], report["after"]
    print(f"held and unreachable  {len(report['surface_keys'])} questions")
    print(f"declared reachable    {report['predicted']} "
          f"(unreachable: {', '.join(report['declared_unreachable'])})")
    print(f"moved                 {report['moved_count']}")
    print(f"split before          {before['parsed']} parsed, "
          f"{before['surface']} surface, {before['absent']} absent")
    print(f"split after           {after['parsed']} parsed, "
          f"{after['surface']} surface, {after['absent']} absent")
    print(f"addressable           {census['tables']} tables, "
          f"{census['rows']} rows, "
          f"{census['addressable_pairs']} (row, field) pairs")
    print("question         before -> after   the field query it becomes")
    for row in report["rows"]:
        print(f"  {row['key']:<15} {row['before']} -> {row['after']:<8} "
              f"{row['query'] or '(not expressible)'}")
    print(report["caveat"])
    return 0


# ---------------------------------------------------------------------------
#  ordering
# ---------------------------------------------------------------------------

def _ordering(args) -> int:
    """The ordering operation: what it answers, what it refuses, what it
    closes of the probe the field surface left one question short."""
    from .reasoning import coordinate_order as cord
    report = cord.comparison_report()
    if args.json:
        print(json.dumps(
            {"answered": report["answered"],
             "refused": report["refused"],
             "declared": report["declared"],
             "as_declared": report["as_declared"],
             "refusal_reasons": list(report["refusal_reasons"]),
             "moved": list(report["moved"]),
             "before": report["before"],
             "after": report["after"],
             "surface_parsed": report["surface_parsed"],
             "surface_keys": report["surface_keys"]},
            indent=1, sort_keys=True))
        return 0
    before, after = report["before"], report["after"]
    print(f"declared comparisons  {report['declared']}")
    print(f"answered / refused    {report['answered']} / {report['refused']} "
          f"({', '.join(report['refusal_reasons'])})")
    print(f"as declared           {report['as_declared']} of "
          f"{report['declared']}")
    print(f"probe before          {before['parsed']} parsed, "
          f"{before['surface']} surface, {before['absent']} absent")
    print(f"probe after           {after['parsed']} parsed, "
          f"{after['surface']} surface, {after['absent']} absent")
    print("comparison         outcome          as declared")
    for row in report["rows"]:
        print(f"  {row['key']:<18} {row['outcome']:<16} "
              f"{'yes' if row['as_declared'] else 'NO'}")
    print(report["caveat"])
    return 0


# ---------------------------------------------------------------------------
#  conversation
# ---------------------------------------------------------------------------

def _conversation(args) -> int:
    """The conversation layer: which follow-ups bind to which antecedent,
    which refuse, and what the two controls do on the same set."""
    from .runtime import conversation as cv
    report = cv.conversation_report()
    if args.json:
        print(json.dumps(
            {"declared": report["declared"],
             "answered": report["answered"],
             "refused": report["refused"],
             "as_declared": report["as_declared"],
             "refusal_reasons": list(report["refusal_reasons"]),
             "reasons_declared": report["reasons_declared"],
             "alone_answered": report["alone_answered"],
             "control_rows": report["control_rows"],
             "control_wrong": report["control_wrong"]},
            indent=1, sort_keys=True))
        return 0
    print(f"declared follow-ups   {report['declared']}")
    print(f"answered / refused    {report['answered']} / {report['refused']} "
          f"({', '.join(report['refusal_reasons'])})")
    print(f"as declared           {report['as_declared']} of "
          f"{report['declared']}")
    print(f"no-context control    {report['alone_answered']} answered of "
          f"{report['declared']}")
    print(f"recency control       differs on {report['control_wrong']} of "
          f"{report['control_rows']}")
    print("follow-up                  outcome                as declared")
    for row in report["rows"]:
        print(f"  {row['key']:<26} {str(row['outcome']):<22} "
              f"{'yes' if row['as_declared'] else 'NO'}")
    print(report["caveat"])
    return 0


# ---------------------------------------------------------------------------
#  binding
# ---------------------------------------------------------------------------

def _binding(args) -> int:
    """Role-filler binding: what a bound relation gives back, what it refuses,
    and what the nearest-mask control says instead."""
    from .reasoning import role_binding as rb
    report = rb.binding_report()
    fibres, product = report["fibres"], report["product"]
    if args.json:
        print(json.dumps(
            {"roles": report["roles"],
             "declared": report["declared"],
             "recovered": report["recovered"],
             "refused": report["refused"],
             "as_declared": report["as_declared"],
             "refusal_reasons": list(report["refusal_reasons"]),
             "control_rows": report["control_rows"],
             "control_wrong": report["control_wrong"],
             "carriers": fibres["carriers"],
             "nameable": fibres["recoverable"],
             "ambiguous": fibres["ambiguous"],
             "largest_fibre": fibres["largest_fibre"],
             "product_recoverable": product["recoverable"]},
            indent=1, sort_keys=True))
        return 0
    print(f"declared bindings     {report['declared']} over "
          f"{report['roles']} roles")
    print(f"named / refused       {report['recovered']} / "
          f"{report['refused']} "
          f"({', '.join(report['refusal_reasons'])})")
    print(f"as declared           {report['as_declared']} of "
          f"{report['declared']}")
    print(f"nameable carriers     {fibres['recoverable']} of "
          f"{fibres['carriers']}, worst fibre {fibres['largest_fibre']} "
          f"in {fibres['largest_fibre_domain']}")
    print(f"product binding       recoverable from "
          f"{product['recoverable']} of {product['carriers']} known sides")
    print(f"nearest-mask control  names another carrier on "
          f"{report['control_wrong']} of {report['control_rows']}")
    print("binding                outcome              as declared")
    for row in report["rows"]:
        print(f"  {row['key']:<22} {str(row['outcome']):<20} "
              f"{'yes' if row['as_declared'] else 'NO'}")
    print(report["caveat"])
    return 0


# ---------------------------------------------------------------------------
#  extremum
# ---------------------------------------------------------------------------

def _extremum(args) -> int:
    """The extremum operation: which columns it folds, which it refuses, and
    under which of its four named reasons."""
    from .reasoning import column_extremum as cx
    report = cx.extremum_report()
    if args.json:
        print(json.dumps(
            {"declared": report["declared"],
             "answered": report["answered"],
             "refused": report["refused"],
             "as_declared": report["as_declared"],
             "refusal_reasons": list(report["refusal_reasons"]),
             "reasons_declared": report["reasons_declared"],
             "ties": report["ties"]},
            indent=1, sort_keys=True))
        return 0
    print(f"declared columns      {report['declared']}")
    print(f"answered / refused    {report['answered']} / {report['refused']} "
          f"({', '.join(report['refusal_reasons'])})")
    print(f"as declared           {report['as_declared']} of "
          f"{report['declared']}")
    print(f"ties reported         {report['ties']}")
    print("column             outcome          as declared")
    for row in report["rows"]:
        print(f"  {row['key']:<18} {row['outcome']:<16} "
              f"{'yes' if row['as_declared'] else 'NO'}")
    print(report["caveat"])
    return 0


# ---------------------------------------------------------------------------
#  engineering
# ---------------------------------------------------------------------------

def _engineering(args) -> int:
    """Formula wheels, Smith chart, analogies, delta-sigma, and the
    engineering questions -- each producer's own figures, never pooled."""
    from .engineering import study
    report = study.engineering_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    w, s, a, d, lang = (report["wheels"], report["smith"], report["analogy"],
                        report["delta_sigma"], report["language"])
    print(f"wheels            {w['wheels']} wheels, {w['cases']} cases: "
          f"reference {w['reference_si_agree']}/{w['reference_explicit_agree']}"
          f", register SI7 {w['register_si7_agree']} EXT10 "
          f"{w['register_ext10_agree']} of {w['register_held']} held, "
          f"derivable {w['derivable_agree']}")
    print(f"                  Ohm wheel spokes {w['ohm_wheel_spokes']}, all "
          f"wheels {w['spokes_all_wheels']}, union flips {w['union_flips']}")
    print(f"smith             {s['passed']}/{s['checks']} checks; match "
          f"worst |Gamma|^2 {s['match']['worst_gamma2']} (bypass "
          f"{s['match']['bypass_gamma2']})")
    for name in ("force-voltage", "force-current"):
        r = a[name]
        print(f"analogy           {name}: e->m {r['electrical_to_mechanical']}"
              f"/{r['axioms'][0]}, m->e {r['mechanical_to_electrical']}/"
              f"{r['axioms'][1]}")
    print(f"                  scrambled control {a['scrambled-control']}, "
          f"degeneracy {a['degeneracy']}")
    print(f"delta-sigma       {d['passed']}/6 checks; gains "
          f"{d['gains_db_floor']}")
    print(f"language          {lang['total']} of {lang['questions']} "
          f"(baseline {lang['baseline']})")
    print(f"                  stress now {lang['stress_now']['counts']}, "
          f"first run {lang['stress_first_run']}")
    return 0


# ---------------------------------------------------------------------------
#  cognition
# ---------------------------------------------------------------------------

def _python_speech(args) -> int:
    """The Python-speech study: P1-P6 against the marks declared before the
    measuring module existed, and the post-hoc differential battery."""
    from .reasoning import python_speech as sp
    report = sp.python_speech_report(run_scripts=not args.no_scripts)
    battery = sp.differential_battery()
    if args.json:
        slim = {k: {kk: vv for kk, vv in v.items() if kk != "programs"}
                for k, v in report["marks"].items()}
        print(json.dumps({"marks": slim, "battery": battery}, indent=1,
                         sort_keys=True, default=str))
        return 0
    for key, mark in report["marks"].items():
        state = "met" if mark["passed"] else "not met"
        detail = {k: v for k, v in mark.items()
                  if k not in ("passed", "programs", "faculty")}
        print(f"{key}  pass mark {state:<8} faculty {mark['faculty']:<8} "
              f"{detail}")
    print(f"battery: {battery['total']} expressions, {battery['answered']} "
          f"answered, {battery['wrong']} wrong")
    return 0 if not report["not_met"] else 1


def _connected(args) -> int:
    """The connected machine: C1-C4 and U1-U3 against the marks declared in
    ``studies/CONNECTED_MACHINE_STUDY.md`` before the router existed."""
    from .engineering import union as un
    from .evaluation.connected_cases import UNION_LABELS
    from .runtime import router
    report = router.connected_report(run_engineering=True)
    import time
    report["tools_census"] = router.tools_census(clock=time.monotonic_ns)
    if not args.quick:
        report["union"] = un.union_census(UNION_LABELS)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for name, counts in report["reads"].items():
        print(f"reads  {name:<12} " + "  ".join(
            f"{k} {v}" for k, v in counts.items()))
    py = report["python"]
    print(f"C2 python   values {py['values_ok']}/{py['values']}  refusals "
          f"{py['refusals_ok']}/{py['refusals']}")
    print(f"C2 engineering {report['engineering']}")
    tc = report["tools_census"]
    print(f"C4 tools    {tc['passed']}/{tc['total']} answered with the "
          f"declared fragment inside 60 s")
    if "union" in report:
        u = report["union"]
        print(f"U1 naive    {u['naive_new']} new derivations, "
              f"{u['naive_right']} right, {u['naive_wrong']} wrong")
        print(f"U2 licensed {u['licensed_answered']} answered, "
              f"{u['licensed_wrong']} wrong, {u['licensed_refused']} refused")
        print(f"U3 in-wheel {u['in_wheel_agree']}/{u['in_wheel']} agree")
    return 0


def _reverse_tct(args) -> int:
    """Reverse Three Column Thinking: V1-V8 against the marks declared in
    ``studies/REVERSE_TCT_STUDY.md`` before the module existed."""
    from .reasoning import reverse_tct_script as rs
    from .runtime import python_tct as pt
    if args.three:
        return _reverse_tct_three(args)
    if args.two:
        return _reverse_tct_two(args)
    report = rs.reverse_report()
    if not args.quick:
        report["scripts"] = pt.reverse_scripts()
        report["control"] = {k: v for k, v in pt.reverse_control().items()
                             if k != "rows"}
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    b = report["battery"]
    print(f"V1  battery {b['terms']} terms, round trips {b['round_trips']}")
    print(f"V2  collisions {b['collisions']} (infix control "
          f"{b['infix_collisions']})")
    s = report["say"]
    print(f"V1  say {s['sentences']}/{s['of']} word for word, refusals "
          f"{s['refusals']}/{s['refusals_of']}, unreadable "
          f"{s['unreadable']}/{s['unreadable_of']}")
    for key in ("entails", "solve", "bounds", "equivalent", "negate"):
        r = report[key]
        print(f"    {key:<10} right {r['right']}/{r['of']}  wrong {r['wrong']}")
    para = report["paraphrase"]
    print(f"V6  paraphrases certified {para['all_certified']}, at least two "
          f"each {para['all_at_least_two']}")
    d = report["dialect"]
    print(f"V8  dialect programs inside the fragment {d['inside']}/{d['of']},"
          f" agreeing {d['agree']}")
    if "scripts" in report:
        sc = report["scripts"]
        print(f"V3  scripts VERIFIED {sc['verified']}/{sc['scripts']}, "
              f"mutants caught {sc['caught']}/{sc['mutants']}")
        c = report["control"]
        print(f"V4  default path without the surface: correct "
              f"{c['control_correct']}/{c['questions']}; reverse surface "
              f"{c['reverse_correct']}/{c['questions']}")
    return 0


def _reverse_tct_two(args) -> int:
    """Reverse TCT round two (Phase 68): W1-W8 against the marks declared in
    ``studies/REVERSE_TCT_STUDY.md`` §7 before any round-two code."""
    from .reasoning import reverse_tct_script as rs
    from .runtime import python_tct as pt
    from .runtime import reverse_relay as rr
    report = rs.reverse_two_report(batteries=not args.quick)
    report["relay"] = rr.relay_report()
    if not args.quick:
        report["scripts_two"] = pt.reverse_two_scripts()
        report["scripts_phase67"] = pt.reverse_scripts()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for key in ("wide_battery", "mask_battery"):
        if key in report:
            b = report[key]
            print(f"W1  {key:<13} {b['terms']} terms, round trips "
                  f"{b['round_trips']}, collisions {b['collisions']}")
    s, r, u = report["say"], report["say_refusals"], report["unreadable"]
    print(f"W1  say {s['right']}/{s['of']} word for word, refusals "
          f"{r['right']}/{r['of']}, unreadable {u['right']}/{u['of']}")
    d = report["dialect"]
    print(f"W2  dialect programs inside {d['inside']}/{d['of']}, agreeing "
          f"{d['agree']} (declared list {d['listed_inside']}/{d['listed']})")
    n = report["negate"]
    print(f"W3  negate right {n['right']}/{n['of']}")
    if "negation_battery" in report:
        nb = report["negation_battery"]
        print(f"W3  CNF battery {nb['statements']}: answered "
              f"{nb['answered']}, double negation certified "
              f"{nb['double_negation_certified']}, grid-exact "
              f"{nb['grid_exact']}")
    for key in ("entails", "bounds", "equivalent"):
        x = report[key]
        print(f"W4  {key:<10} right {x['right']}/{x['of']}  wrong "
              f"{x['wrong']}")
    rl = report["relay"]
    print(f"W6  relay right {rl['right']}/{rl['cases']}; handoffs "
          f"{rl['handoffs_ok']}/{rl['handoffs']} agree or consistent, "
          f"disagree {rl['disagrees']}, questions read back "
          f"{rl['questions_read_back']}")
    ca, cb = rl["control_verbatim"], rl["control_chain"]
    print(f"W6  control A (sentences verbatim) answered "
          f"{ca['answered']}/{ca['sentences']}; control B (planner chained "
          f"to itself) recovered {cb['recovered']}/{cb['values']}")
    p = report["phase67"]
    print(f"W8  Phase 67 cases right {p['right']}/{p['of']} "
          f"({p['superseded']} superseded)")
    for key in ("scripts_two", "scripts_phase67"):
        if key in report:
            sc = report[key]
            print(f"W5  {key:<15} VERIFIED {sc['verified']}/{sc['scripts']}"
                  f", mutants caught {sc['caught']}/{sc['mutants']}")
    return 0


def _reverse_tct_three(args) -> int:
    """Reverse TCT round three (Phase 69), the integer sort: X1-X5 against
    the marks declared in ``studies/REVERSE_TCT_STUDY.md`` §10 before any
    round-three code."""
    from .reasoning import reverse_tct_int as ri
    from .runtime import python_tct as pt
    report = ri.int_report(with_battery=not args.quick)
    if not args.quick:
        report["scripts"] = pt.reverse_int_scripts()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for key, mark in (("entails", "X1"), ("bounds", "X2")):
        x = report[key]
        print(f"{mark}  {key:<8} right {x['right']}/{x['of']}  wrong "
              f"{len(x['wrong'])}")
    if "scripts" in report:
        sc = report["scripts"]
        print(f"X3  scripts VERIFIED {sc['verified']}/{sc['scripts']}, "
              f"mutants caught {sc['caught']}/{sc['mutants']}")
    if "battery" in report:
        for key in ("entails", "bounds"):
            b = report["battery"][key]
            print(f"X4  battery {key:<8} {b['questions']} questions, "
                  f"answered {b['answered']}, undecided {b['undecided']}, "
                  f"disagreements {len(b['disagree'])}")
    for key in ("entails", "bounds"):
        c = report["control"][key]
        print(f"X5  control over Q, {key:<8} refused NOT_POLYNOMIAL "
              f"{c['not_polynomial']}/{c['of']}, other answer "
              f"{len(c['different'])}, same {c['same']}")
    return 0


def _integer_decision(args) -> int:
    """The complete integer decision (Phase 79): the Omega test behind round
    three's ``INTEGER_UNDECIDED``, against the marks declared in
    ``studies/INTEGER_DECISION_STUDY.md`` before any code of the round."""
    from .reasoning import integer_decision as idc
    from .reasoning import reverse_tct_int as ri
    from .runtime import python_tct as pt
    from .runtime.tct_engine import package_root
    report = idc.decision_report(with_battery=not args.quick)
    root = str(package_root())
    verified = caught = scripts = mutants = 0
    for cid, a, _ in idc.decision_answers():
        scripts += 1
        verified += bool(pt.run_column3(ri.render_script(a, root))
                         ["verified"])
        bad = ri.mutated_script(a, root)
        if bad is not None:
            mutants += 1
            caught += not pt.run_column3(bad)["verified"]
    report["Z4"] = {"scripts": scripts, "verified": verified,
                    "mutants": mutants, "caught": caught}
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    z1 = report["Z1"]
    print(f"Z1  round three: entails {z1['entails_right']}/"
          f"{z1['entails_of']}, bounds {z1['bounds_right']}/{z1['bounds_of']}"
          f", Omega trees in its certificates {z1['omega_certificates']}")
    z2 = report["Z2"]
    print(f"Z2  declared corpus: right {z2['right']}/{z2['of']}, wrong "
          f"{len(z2['wrong'])}, refused {len(z2['refused'])} "
          f"(round three refused {z2['undecided_before']} INTEGER_UNDECIDED)")
    if "Z3" in report:
        for key in ("entails", "bounds"):
            now, then = report["Z3"]["now"][key], \
                report["Z3"]["round_three"][key]
            print(f"Z3  battery {key:<8} agree {now['agree']}/"
                  f"{now['questions']}, undecided {now['undecided']} (round "
                  f"three: {then['undecided']}), decided by an Omega tree "
                  f"{now['omega']}")
    z4 = report["Z4"]
    print(f"Z4  scripts VERIFIED {z4['verified']}/{z4['scripts']}, mutants "
          f"caught {z4['caught']}/{z4['mutants']}")
    z5 = report["Z5"]
    print(f"Z5  limit {z5['node_limit']} steps (declared "
          f"{z5['declared_limit']}); undecided now "
          f"{z5.get('undecided_now', 'not measured (--quick)')}")
    return 0


def _native_parity(args) -> int:
    """Native parity (Phase 70): the ledger of native/standard pairs and the
    refinements, against the marks declared in
    ``studies/NATIVE_PARITY_STUDY.md`` before the module existed."""
    from .reasoning import native_parity as npar
    if args.write:
        target = npar.write_measurements()
        print(f"wrote {target}")
        print(f"native parity: {npar.state()['verdict']}")
        return 0
    report = npar.current() if not args.live else None
    if report is None:
        report = npar.native_parity_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for row in report["ledger"]["rows"]:
        print(f"ledger  {row['class']:<24} {row['target']:<9} {row['task']}")
    for label in ("declarations", "goals"):
        for scheme, row in report[label]["schemes"].items():
            hits = row["hits"]
            print(f"T1 {label:<12} {scheme:<9} hits "
                  + " ".join(f"{hits[k]:>3}" for k in sorted(hits, key=int))
                  + f"  MRR@10 {_per_mille(Fraction(row['mrr_at_10']))}")
    docs = report["documents"]
    if docs.get("answered"):
        for scheme, row in docs["schemes"].items():
            print(f"T2 documents   {scheme:<15} hits {row['hits']:>3} of "
                  f"{docs['queries']}  precision@5 "
                  f"{_per_mille(Fraction(row['precision_at_5']))}")
    for scheme, row in report["controller"]["scorers"].items():
        print(f"T3 controller  {scheme:<9} solved {row['solved']} minimal "
              f"{row['minimal']} verified {row['verified']} proposals "
              f"{row['proposals']}")
    for mark, met in report["marks"].items():
        print(f"{mark:<11} {'met' if met else 'NOT met'}")
    return 0


def _law_register(args) -> int:
    """The UBP law register re-read (Phase 74), against the marks declared in
    ``studies/LAW_REGISTER_STUDY.md`` before the module existed."""
    from .reasoning import law_register as lr
    if args.law:
        print(json.dumps(lr.admit(args.law), indent=1, sort_keys=True, default=str))
        return 0
    report = lr.law_register_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    print("exact rows:   " + ", ".join(f"{n} {k}" for k, n in report["exact"]["census"].items()))
    print("numeric rows: " + ", ".join(f"{n} {k}" for k, n in report["numeric"]["census"].items()))
    for t in report["numeric"]["templates"]:
        print(f"  {t['key']:<12} {t['quantity']:<24} error {t['error_pct']:>7}%  "
              f"members {t['members']:>6}  p {t['p_decimal']}  "
              f"{'admitted' if t['admitted'] else 'refused'}")
    for r in report["refusal_price"]:
        print(f"p={r['p']:<6} right {r['right']} refused {r['refused']} wrong {r['wrong']}"
              f"  withheld {r['wrong_withheld']} per given up {r['right_given_up']}")
    for mark, met in report["marks"].items():
        print(f"{mark:<4} {'met' if met else 'NOT met'}")
    return 0


def _law_absorption(args) -> int:
    """The UBP laws absorbed (Phase 75): one fate per law, the substrate
    facts the absorbed laws became, against the marks declared in
    ``studies/LAW_ABSORPTION_STUDY.md`` before the module existed."""
    from .reasoning import law_absorption as la
    if args.law:
        print(json.dumps(la.tool_summary(args.law), indent=1, sort_keys=True,
                         default=str))
        return 0
    report = la.law_absorption_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    print("fates: " + ", ".join(f"{n} {k}" for k, n in report["census"].items()))
    for law, (fate, said, keys) in report["table"].items():
        if fate != "retired":
            print(f"  {law:<28} {fate:<12} {', '.join(keys)}")
    print(f"declared questions: {report['declared_ok']} of "
          f"{report['declared_total']} as declared, "
          f"{report['declared_wrong']} wrong")
    for t in report["retests"]:
        print(f"  retest {t['law']:<16} {t['quantity']:<26} error "
              f"{t['error_pct']:>7}%  members {t['members']:>6}  p "
              f"{t['p_decimal']}  {'admitted' if t['admitted'] else 'refused'}")
    for mark, met in report["marks"].items():
        print(f"{mark:<4} {'met' if met else 'NOT met'}")
    return 0


def _decoder_confidence(args) -> int:
    """Decoder confidence (Phase 77): the absorbed confidence law attached to
    the decoder's own readings, against the marks declared in
    ``studies/DECODER_CONFIDENCE_STUDY.md`` before the module existed."""
    from fractions import Fraction
    from .reasoning import decoder_confidence_marks as dcm
    from .reasoning.coherence import decimal_str

    def d7(value) -> str:
        return decimal_str(Fraction(value), 7)

    report = dcm.decoder_confidence_report(full=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    c1 = report["C1"]
    print(f"decoder: {c1['reads_checked']} reads checked, "
          f"{c1['disagreements']} disagreements; coset weight 4 refused TIE "
          f"on {c1['tie_refused']} of {c1['tie_reads']}")
    for d, row in c1["confidence_by_weight"].items():
        print(f"  coset weight {d}: " + ", ".join(
            f"{rate}: {d7(v)}" for rate, v in row.items()))
    print("context stage (resolved forks, least confidence, proved floor, "
          "below 99%):")
    for r in report["C2"]["rows"]:
        print(f"  k={r['k']:<3} rate {str(r['rate']):<6} {r['resolved']:>7}  "
              f"{d7(r['least'])}  {d7(r['bound'])}  "
              f"{r['below_99']}")
    print("second reading (answered, wrong, least confidence):")
    for r in report["C3"]["rows"]:
        print(f"  rate {str(r['rate']):<6} {r['answered']} {r['wrong']} "
              f"{d7(r['least'])}")
    print(f"runtime programs as declared: {report['C4']['as_declared']} of "
          f"{report['C4']['programs']}")
    for mark, met in report["marks"].items():
        print(f"{mark:<4} {'met' if met else 'NOT met'}")
    return 0


def _confidence_floor(args) -> int:
    """The confidence floor (Phase 80): a grid of thresholds hunted over the
    exact channel census, against the marks declared in
    ``studies/CONFIDENCE_FLOOR_STUDY.md`` before the module existed."""
    from fractions import Fraction
    from .reasoning import confidence_floor_marks as cfm
    from .reasoning.coherence import decimal_str

    def d(value, places: int = 6) -> str:
        return decimal_str(Fraction(value), places)

    report = cfm.confidence_floor_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    print("unfloored readings (P(right), P(wrong), P(wrong | answered), "
          "least confidence):")
    for r in report["unfloored"]:
        print(f"  {r['reading']:<8} rate {str(r['rate']):<7} "
              f"{d(r['p_right'], 9)}  {d(r['p_wrong'], 9)}  "
              f"{d(r['residual'], 9)}  {d(r['least_confidence'], 7)}")
    print("the hunt (rate, floor, works, least retention and where, "
          "greatest residual):")
    for r in report["F3"]["table"]:
        print(f"  {str(r['rate']):<7} {str(r['floor']):<11} "
              f"{'works' if r['works'] else 'no':<6} "
              f"{d(r['least_retention'], 4)} {r['least_retention_reading']:<8}"
              f" {d(r['greatest_residual'], 9)}")
    print("working threshold per rate: " + ", ".join(
        f"{p}: {w}" for p, w in report["F3"]["working"].items()))
    print("recommended reading per rate: " + ", ".join(
        f"{p}: {w}" for p, w in report["F3"]["recommended"].items()))
    print("not declared -- each reading on its own:")
    for reading, row in report["per_reading_working"].items():
        print(f"  {reading:<8} " + ", ".join(
            f"{p}: {w}" for p, w in row.items()))
    f4 = report["F4"]
    print(f"declared rate: overdeclared broken in {f4['overdeclared_broken']} "
          f"of {f4['cells']} cells, underdeclared in "
          f"{f4['underdeclared_broken']}")
    print(f"runtime programs as declared: {report['F5']['as_declared']} of "
          f"{report['F5']['programs']}")
    for mark, met in report["marks"].items():
        print(f"{mark:<4} {'met' if met else 'NOT met'}")
    return 0


def _agree_channel(args) -> int:
    """The second reading's channel (Phase 81): an exact census over every
    pair of reads, and ``agree`` in the confidence-floor hunt, against the
    marks declared in ``studies/AGREE_CHANNEL_STUDY.md`` before the module
    existed."""
    from fractions import Fraction
    from .reasoning import agree_channel_marks as acm
    from .reasoning.coherence import decimal_str

    def d(value, places: int = 6) -> str:
        return decimal_str(Fraction(value), places)

    report = acm.agree_channel_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    g1, g2, g4 = report["G1"], report["G2"], report["G4"]
    print(f"census: {g1['pairs']} resolved pairs (expected "
          f"{g1['pairs_expected']}), {g1['groups']} groups; second routes "
          f"{'agree' if g1['routes_agree'] else 'DISAGREE'}; runtime stride "
          f"{g1['checked']} checked, {g1['disagreements']} disagreements")
    print(f"class collapse: {g2['keys']} keys, {g2['keys_split']} split; the "
          f"coarser key splits {g2['coarse_split']} of {g2['coarse_keys']}")
    print("unfloored (reading, rate, P(right), P(wrong), P(refused), "
          "P(wrong | answered)):")
    for r in report["G5"]["rows"]:
        print(f"  agree    {str(r['rate']):<7} {d(r['agree_right'], 9)}  "
              f"{d(r['agree_wrong'], 12)}  {d(r['agree_refused'], 9)}  "
              f"{d(r['agree'], 12)}")
        print(f"  decoder  {str(r['rate']):<7} {d(r['decoder_right'], 9)}  "
              f"{d(r['decoder_wrong'], 12)}  {'':<11}  {d(r['decoder'], 12)}")
    print("agree's floors (rate, floor, works, retention, residual, wrong "
          "removed):")
    for r in g4["agree_table"]:
        print(f"  {str(r['rate']):<7} {str(r['floor']):<11} "
              f"{'works' if r['works'] else 'no':<6} {d(r['retention'], 4)} "
              f"{d(r['residual'], 12)} {d(r['wrong_removed'], 4)}")
    print("working threshold, seven readings: " + ", ".join(
        f"{p}: {w}" for p, w in g4["working_seven"].items()))
    print("working threshold, agree alone: " + ", ".join(
        f"{p}: {w}" for p, w in g4["working_agree"].items()))
    g6 = report["G6"]
    print(f"declared rate: overdeclared broken in {g6['overdeclared_broken']}"
          f" of {g6['cells']} cells, underdeclared in "
          f"{g6['underdeclared_broken']}")
    print(f"runtime programs as computed: {report['G7']['as_computed']} of "
          f"{report['G7']['programs']}")
    for mark, met in report["marks"].items():
        print(f"{mark:<4} {'met' if met else 'NOT met'}")
    return 0


def _rate_posterior(args) -> int:
    """The rate from the machine's own reads (Phase 82): an exact posterior
    over a declared grid of rates, the soft reading's marginal confidence,
    and its operating characteristics over every count vector, against the
    marks declared in ``studies/RATE_POSTERIOR_STUDY.md`` before the module
    existed."""
    from fractions import Fraction
    from .reasoning import rate_posterior_marks as rpm
    from .reasoning.coherence import decimal_str

    def d(value, places: int = 6) -> str:
        return decimal_str(Fraction(value), places)

    if getattr(args, "repairs", False):
        table = rpm.repair_table()
        print(f"the repairs of Phase 82's section 3 (Phase 86): "
              f"{table['cells_each']} fixed-rate cells each")
        for row in table["rows"]:
            ret = ", ".join(f"{k} {d(v, 4)}"
                            for k, v in row["retention"].items())
            print(f"  {row['repair']:<22} broken {row['broken']:>2} "
                  f"(on grid {row['on_grid']}, at 1/5 {row['at_one_fifth']}); "
                  f"identity {'holds' if row['identity_holds'] else 'FAILS'}; "
                  f"retention n=20: {ret}")
        return 0
    report = rpm.rate_posterior_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    j2, j3 = report["J2"], report["J3"]
    print(f"promise under the prior: {j2['broken']} broken of {j2['cells']} "
          f"cells")
    print(f"fixed-rate table: {j3['cells']} cells, {j3['broken']} broken "
          f"({j3['grid_broken']} on the grid)")
    for r in j3["broken_rows"]:
        if r["on_grid"]:
            print(f"  on grid: rate {r['rate']}, n {r['n']}, floor "
                  f"{r['floor']}: residual {d(r['residual'], 8)}")
    print("identifiability (smallest n, P(argmax = truth) >= 9/10): " +
          ", ".join(f"{p}: {n if n is not None else '>20'}"
                    for p, n in report["J5"]["smallest_n"].items()))
    j7 = report["J7"]
    print(f"refusals are evidence: prior mean {d(j7['prior_mean'], 4)}, "
          f"after a TIE {d(j7['after_tie'], 4)}, after a contradicted pair "
          f"{d(j7['after_contradicted_pair'], 4)}")
    print(f"runtime programs as computed: {report['J8']['as_computed']} of "
          f"{report['J8']['programs']}")
    for mark, met in report["marks"].items():
        print(f"{mark:<4} {'met' if met else 'NOT met'}")
    return 0


def _contract_matrix(args) -> int:
    """Candidate P's two contract changes tested four ways (Phase 89): the
    control, the upper-credible rate rule alone, the session-marginal
    confidence alone, and both -- exact retention, soft-floor breaks and
    residual bounds in two frames (``studies/CONTRACT_MATRIX_STUDY.md``)."""
    from fractions import Fraction
    from .reasoning import contract_matrix as cm
    from .reasoning.coherence import decimal_str

    def d(value, places: int = 4) -> str:
        return decimal_str(Fraction(value), places)

    m = cm.matrix()
    if args.json:
        print(json.dumps(m, indent=1, sort_keys=True, default=str))
        return 0
    print(f"the 4-way matrix: {m['cells_each']} fixed-rate cells per variant "
          f"and frame; sessions {', '.join(str(s) for s in m['sessions'])}")
    for r in m["rows"]:
        one = r["frame_one"]
        ret = ", ".join(f"{k} {d(v)}" for k, v in r["retention"].items())
        lo, hi = r["calibration_excess"]
        print(f"{r['variant']}  {r['label']}")
        print(f"   frame I  (a call with its own corpus): broken "
              f"{one['broken']} (on grid {one['on_grid']}, at 1/5 "
              f"{one['at_one_fifth']}); worst residual/(1-t) "
              f"{d(one['worst_factor'], 2)}")
        print(f"   frame II (a session of plain calls):  broken "
              f"{r['broken']} (on grid {r['on_grid']}, at 1/5 "
              f"{r['at_one_fifth']}); worst residual/(1-t) "
              f"{d(r['worst_factor'], 2)}, on grid "
              f"{d(r['worst_grid_factor'], 4)}")
        print(f"   retention S=20: {ret}; mean on grid "
              f"{d(r['mean_grid_retention'])}")
        print(f"   prior promise broken {r['prior_broken']} of "
              f"{r['prior_cells']} (worst {d(r['worst_prior_factor'])}); "
              f"printed-confidence excess at most {d(hi, 8)}")
    print(f"qualified: {', '.join(m['qualified']) or 'none'}; production: "
          f"{m['production']}")
    return 0


def _question_set_b(args) -> int:
    """The two outside question sets of Phase 89 through the router: Set B
    scored by protocol and by audit, Outside O1 classed into the Capability
    Failure Matrix, and the four candidate-P variants re-run on every framed
    question (``studies/QUESTION_SET_B_STUDY.md``)."""
    from .evaluation import question_set_b as qb
    rep = qb.report(variants=not args.no_variants)
    if args.json:
        print(json.dumps(rep, indent=1, sort_keys=True, default=str))
        return 0
    b = rep["set_b"]
    print(f"Set B (14): protocol {b['protocol']:+d} ({b['plus']} right, "
          f"{b['minus']} confidently wrong); audited {b['audited']:+d} "
          f"({b['audited_plus']} right, {b['audited_minus']} wrong)")
    for r in b["rows"]:
        print(f"  {r['id']} {r['surface']:<9} {r['frame'] or '-':<20} "
              f"{'ANSWER' if r['answered'] else 'REFUSED ' + str(r['code'])}"
              f"  protocol {r['protocol']:+d} audited {r['audited_score']:+d}")
    o = rep["outside"]
    print(f"Outside O1 (112): score {o['score']:+d}; framed and correct "
          f"{o['framed_correct']}; confidently wrong {o['wrong']}")
    print(f"  boundary classes: {o['classes']}")
    for sec, c in o["by_section"].items():
        print(f"  {sec[:44]:<44} {c}")
    if "variants" in rep:
        v = rep["variants"]
        print(f"candidate P on the {v['items']} framed questions:")
        for name, row in v["variants"].items():
            print(f"  {name}: answered {row['answered']}, refused "
                  f"{row['refused']} {row['codes']}")
        print(f"  verdicts differing from A: {v['differ_from_A']}")
    return 0


def _law_triage(args) -> int:
    """The 106 unresolved laws triaged (Phase 83): one fate per law under the
    service rule of ``studies/LAW_TRIAGE_STUDY.md``, the declared checks
    computed from the substrate."""
    from .reasoning import law_triage as lt
    if args.law:
        print(json.dumps(lt.fate_of(args.law), indent=1))
        return 0
    import pathlib
    import zipfile
    raw = None
    archive = pathlib.Path(__file__).resolve().parents[2] / lt.ZIP_PATH
    if archive.exists():
        raw = zipfile.ZipFile(archive).read(lt.KB_MEMBER)
    report = lt.law_triage_report(raw)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    print(f"laws: {report['laws']}; fates: " + ", ".join(
        f"{k} {v}" for k, v in report["counts"].items()))
    print("retired by reason: " + ", ".join(
        f"{k} {v}" for k, v in report["reasons"].items()))
    for law, c in report["checks"].items():
        print(f"  {law:<34} {c['outcome']:<15} "
              f"{'as declared' if c['as_declared'] else 'NOT as declared'}")
    for mark, met in report["marks"].items():
        print(f"{mark:<4} {'met' if met else 'NOT met'}")
    return 0


def _held_precision(args) -> int:
    """Held precision (Phase 76): a register value's stated precision carried
    through a stepwise derivation, against the marks declared in
    ``studies/HELD_PRECISION_STUDY.md`` before the module existed."""
    from .reasoning import held_precision as hp
    report = hp.held_precision_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    print(f"goal and narrative chains: {report['chains']}, reading a register "
          f"value: {report['with_register']}, exact because a held value "
          f"cancels: {report['exact']}, step-by-step interval wider: "
          f"{report['naive_wider']}")
    for r in report["rows"]:
        if r["reads_register"]:
            print(f"  {r['value']:<18} {r.get('interval')}  naive "
                  f"{r.get('naive')}")
    for mark, met in report["marks"].items():
        print(f"{mark:<4} {'met' if met else 'NOT met'}")
    return 0


def _native_words(args) -> int:
    """Native words (Phase 71): word overlap computed on Golay words of the
    tokens, against the marks declared in ``studies/NATIVE_WORDS_STUDY.md``
    before the module existed."""
    from .reasoning import native_words as nwd
    if args.write:
        target = nwd.write_measurements()
        print(f"wrote {target}")
        print(f"native words: {nwd.state()['verdict']}")
        return 0
    report = nwd.current() if not args.live else None
    if report is None:
        report = nwd.native_words_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for label in ("declarations", "goals"):
        for scheme, row in report["lean"][label]["schemes"].items():
            hits = row["hits"]
            print(f"lean {label:<12} {scheme:<12} hits "
                  + " ".join(f"{hits[k]:>3}" for k in sorted(hits, key=int))
                  + f"  MRR@10 {_per_mille(Fraction(row['mrr_at_10']))}")
    docs = report["documents"]
    if docs.get("answered"):
        for scheme, row in docs["schemes"].items():
            print(f"documents {scheme:<12} hits {row['hits']:>3} of "
                  f"{docs['queries']}  precision@5 "
                  f"{_per_mille(Fraction(row['precision_at_5']))}")
    for mark, met in report["marks"].items():
        print(f"{mark:<4} {'met' if met else 'NOT met'}")
    return 0


def _corpus_resample(args) -> int:
    """The declared resampling (Phase 100): every sub-corpus that drops one
    Lean file and every stride offset, against the rule declared in
    ``studies/CORPUS_RESAMPLE_STUDY.md`` before the module existed."""
    from .reasoning import corpus_resample as crs
    if args.write:
        target = crs.write_measurements()
        print(f"wrote {target}")
        print(f"corpus resample: {crs.state()['verdict']}")
        return 0
    report = crs.current() if not args.live else None
    if report is None:
        report = crs.corpus_resample_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    print(f"census {report['census']} queries over {report['pool']} "
          f"declarations; {report['files']} file drops; strides "
          f"{report['strides']}")
    for rid, block in report["verdicts"].items():
        for mode, v in block.items():
            d = v["discordance"]
            print(f"{rid} {mode:<12} {v['verdict']:<16} file drops "
                  f"{_per_mille(Fraction(v['share_file_drops']))}  offsets "
                  f"{_per_mille(Fraction(v['share_offsets']))}  census "
                  f"{d['first_only']}:{d['second_only']}")
    for mark, met in report["marks"].items():
        print(f"{mark:<4} {'met' if met else 'NOT met'}")
    return 0


def _ast_index_freeze() -> int:
    """Take the AST index snapshot (Phase 105): every admitted
    statement-level expression of ``overlay/glm_universal`` (``live``) and
    of ``source_material/GLM-main.zip`` (``archive``), in that order, files
    sorted, sites by line and column."""
    import zipfile
    from pathlib import Path
    from .reasoning import ast_index as ai
    root = Path(__file__).resolve().parents[2]
    rows = []
    files = {"live": {"read": 0, "skipped": 0},
             "archive": {"read": 0, "skipped": 0}}
    live = sorted(p for p in (root / "overlay" / "glm_universal").rglob("*.py")
                  if "__pycache__" not in p.parts and "_derived" not in p.parts)
    for path in live:
        got = ai.sites_of_source(path.read_text(encoding="utf-8"))
        name = path.relative_to(root).as_posix()
        files["live"]["read" if got is not None else "skipped"] += 1
        rows.extend(["live", name, ln, col, text] for ln, col, text in got or ())
    with zipfile.ZipFile(root / "source_material" / "GLM-main.zip") as z:
        for name in sorted(n for n in z.namelist() if n.endswith(".py")):
            src = z.read(name).decode("utf-8", errors="replace")
            got = ai.sites_of_source(src)
            files["archive"]["read" if got is not None else "skipped"] += 1
            rows.extend(["archive", name, ln, col, text]
                        for ln, col, text in got or ())
    target = ai.write_snapshot(rows, files)
    print(f"froze {target}")
    print(f"snapshot: {ai.frozen_state()}")
    return 0


def _ast_index(args) -> int:
    """The AST address as a retrieval key (Phase 105), on the frozen index
    declared in ``studies/AST_INDEX_STUDY.md``."""
    if args.freeze:
        return _ast_index_freeze()
    from .runtime import ast_index_report as air
    if args.write:
        target = air.write_measurements()
        print(f"wrote {target}")
        return 0
    if args.ask:
        from .runtime import ast_index_frames as aif
        from .runtime import question_frames as qf
        reading = qf.read(args.ask)
        print(reading.body() if reading is not None else "no frame reads it")
        return 0
    report = air.current() if not args.live else None
    if report is None:
        report = air.ast_index_report(run_scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    print(air.summary_text(report))
    return 0


def _document_tree(args) -> int:
    """The document tree as a third native book (Phase 102), on the frozen
    corpus declared in ``studies/DOCUMENT_TREE_STUDY.md``."""
    from .reasoning import document_tree as dtr
    if args.freeze:
        target = dtr.freeze()
        print(f"froze {target}")
        print(f"snapshot: {dtr.frozen_state()}")
        return 0
    if args.write:
        target = dtr.write_measurements()
        print(f"wrote {target}")
        print(f"document tree: {dtr.state()['verdict']}")
        return 0
    report = dtr.current() if not args.live else None
    if report is None:
        report = dtr.document_tree_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    print(f"{report['units']} census queries over {report['documents']} "
          f"documents (snapshot {str(report['snapshot_digest'])[:12]})")
    for rid, line in dtr.RANKINGS:
        row = report["census"][rid]
        print(f"  {rid:16} hit@1 {row['hit@1']:5}  hit@5 {row['hit@5']:5}  "
              f"relatives@5 {row['relatives@5']:5}   {line}")
    for name, mark in report["marks"].items():
        print(f"  {name}: {mark['outcome']}")
    return 0


def _citation_scope(args) -> int:
    """Citations read in Lean's scope (Phase 101): both citation readers
    against the elaborator, the type-word repair, and the Lean-corpus
    retrieval figures re-taken beside the legacy record, against the marks
    declared in ``studies/CITATION_SCOPE_STUDY.md``."""
    from .reasoning import citation_reference as cr
    from .reasoning import citation_scope as cs
    if args.reference:
        target = cr.write_reference()
        print(f"wrote {target}")
    if args.write:
        target = cs.write_measurements()
        print(f"wrote {target}")
        print(f"citation scope: {cs.state()['verdict']}")
        return 0
    report = cs.current() if not args.live else None
    if report is None:
        report = cs.citation_scope_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    print(f"reference: {report['reference']['verdict']} "
          f"({report['constants']} constants)")
    for reader in ("legacy", "scoped"):
        a = report["audit"][reader]
        if not a:
            continue
        print(f"{reader:<7} edges {a['edges']:>6}  precision "
              f"{_per_mille(Fraction(a['precision']))}  visible recall "
              f"{_per_mille(Fraction(a['recall_visible']))}  one-letter "
              f"{a['one_letter_edges']} ({a['one_letter_unconfirmed']} "
              f"unconfirmed)")
    w = report["type_words"]
    print(f"type words: {w['moved_legacy']} of {w['queries']} goals moved "
          f"before, {w['moved_repaired']} after")
    old, new = report["legacy"], report["headline"]
    for mode in ("decl", "goal"):
        for scheme, row in new[mode]["hits"].items():
            before = old[mode]["hits"].get(scheme) if old else None
            print(f"{mode:<4} {scheme:<9} " + "  ".join(
                f"@{k} {row[k]:>3}" + (f" (was {before[k]})" if before else "")
                for k in sorted(row)))
    for mark, met in report["marks"].items():
        print(f"{mark:<4} {'met' if met else 'NOT met'}")
    return 0


def _dependency(args) -> int:
    """What a Lean result rests on (Phase 101): the declared questions, the
    column-3 gates and their mutations, and the named refusals, against the
    marks of ``studies/CITATION_SCOPE_STUDY.md`` §2.1."""
    from .runtime import dependency_report as dr
    report = dr.dependency_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    print(f"reference: {report['reference']}")
    for row in report["declared"]:
        print(f"{'ok ' if row['got'] == row['declared'] else 'BAD'} "
              f"gate {row['gate']!s:<5} mutation rejected "
              f"{row['mutation_rejected']!s:<5} {row['question']}")
    first = report["as_declared"]
    print(f"as declared: {first['right']} right, {first['wrong']} wrong, "
          f"{first['refused']} refused {first['codes']}")
    for row in report["refusals"]:
        print(f"refusal {row['expected']:<20} got {row['got']}")
    for mark, met in report["marks"].items():
        print(f"{mark:<16} {'met' if met else 'NOT met'}")
    return 0


def _stepwise(args) -> int:
    """The stepwise planner (Phase 72): S1-S7 against the marks declared in
    ``studies/STEPWISE_PLANNER_STUDY.md`` before the module existed."""
    from .runtime import stepwise as sw
    report = sw.stepwise_report(scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for key in ("composition", "goals", "narratives", "follow_ups"):
        r = report[key]
        print(f"{key:<12} {r['met']} of {r['cases']} as declared")
    c = report["composition"]
    print(f"composition  wrong {c['wrong']}; the bare planner answers "
          f"{c['bare_planner_answers']} of {c['cases']}")
    k = report["controls"]
    print(f"controls     first-found answers {k['first_found_answers_refused']}"
          f" refused goal cases; naive union answers "
          f"{k['naive_answers_ambiguous']} ambiguous")
    i = report["interference"]
    print(f"interference {i['read']} of {i['questions']} declared questions "
          f"read; turned into answers: {len(i['turned_into_answers'])}")
    if "scripts" in report:
        s = report["scripts"]
        print(f"scripts      {s['verified']} of {s['chains']} verified, "
              f"{s['aligned']} of {s['steps']} steps aligned")
        for kind, n in s["mutants"].items():
            print(f"  mutation {kind:<10} caught {s['caught'][kind]} of {n}")
    return 0


def _stepwise_two(args) -> int:
    """The stepwise planner, round two (Phase 73): T1-T7 against the marks
    declared in ``studies/STEPWISE_TWO_STUDY.md`` before any code."""
    from .runtime import stepwise_two as st
    report = st.stepwise_two_report(scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for key in ("frames", "units", "register"):
        r = report[key]
        print(f"{key:<12} {r['met']} of {r['cases']} as declared, wrong "
              f"{r['wrong']}; round one's reader answers "
              f"{r['round_one_answers']}")
    k = report["controls"]
    print(f"controls     strip-the-units wrong on {len(k['naive_wrong'])} "
          f"answered cases, answers {len(k['naive_answers_unit_refusals'])} "
          f"unit refusals")
    for key in ("narratives", "follow_ups"):
        r = report[key]
        print(f"{key:<12} {r['met']} of {r['cases']} as declared")
    i = report["interference"]
    print(f"interference round one held: {i['round_one_held']}; "
          f"{i['router_read']} of {i['router_questions']} router questions "
          f"read; turned into answers: {len(i['turned_into_answers'])}")
    if "scripts" in report:
        s = report["scripts"]
        print(f"scripts      {s['verified']} of {s['chains']} verified, "
              f"{s['aligned']} of {s['steps']} steps aligned")
        for kind, n in s["mutants"].items():
            print(f"  mutation {kind:<10} caught {s['caught'][kind]} of {n}")
    return 0


def _stepwise_three(args) -> int:
    """The stepwise planner, round three (Phase 84): V1-V7 against the marks
    declared in ``studies/STEPWISE_THREE_STUDY.md`` before any code."""
    from .runtime import stepwise_three as st
    report = st.stepwise_three_report(scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for key in ("comparatives", "counts", "prefixes", "folds"):
        r = report[key]
        print(f"{key:<13} {r['met']} of {r['cases']} as declared, wrong "
              f"{r['wrong']}; round two's reader answers "
              f"{r['round_two_answers']}")
    k = report["controls"]
    p = k["partition"]
    print(f"controls      present-rows answers "
          f"{len(k['present_rows_answers'])} of {k['holes']} holes; "
          f"partition {p['agree']} of {p['columns']} columns agree, "
          f"{p['rows_in_classes']} of {p['rows']} rows in a class")
    r = report["follow_ups"]
    print(f"follow_ups    {r['met']} of {r['cases']} as declared")
    i = report["interference"]
    print(f"interference  round one held: {i['round_one_held']}; round two "
          f"held: {i['round_two_held']}; {i['router_read']} of "
          f"{i['router_questions']} router questions read; turned into "
          f"answers: {len(i['turned_into_answers'])}")
    if "scripts" in report:
        s = report["scripts"]
        print(f"scripts       {s['verified']} of {s['chains']} verified, "
              f"{s['aligned']} of {s['steps']} steps aligned")
        for kind, n in s["mutants"].items():
            print(f"  mutation {kind:<10} caught {s['caught'][kind]} of {n}")
    return 0


def _stepwise_five(args) -> int:
    """The stepwise planner, round five (Phase 91): frames generated from a
    declaration, and the widenings as entries in it, D1-D8 against the marks
    declared in ``studies/DECLARED_FRAMES_STUDY.md`` before any code."""
    from .runtime import stepwise_five as s5
    report = s5.stepwise_five_report(scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    g = report["generated"]
    print(f"generated     {g['identical']} of {g['texts']} texts read alike "
          f"by the generated and the hand-written readers "
          f"({g['fold_texts']} with a fold); emptied declaration reads "
          f"{g['emptied_fold_reads']} folds")
    for key in ("orders", "superlatives", "bounds", "classes", "prefixes",
                "molecules"):
        r = report[key]
        print(f"{key:<13} {r['met']} of {r['cases']} as declared, wrong "
              f"{r['wrong']}; round four's reader answers "
              f"{r['round_four_answers']}; the machine answered "
              f"{r['machine_answered_before']} before and "
              f"{r['machine_answers_now']} now")
    w = report["widenings"]
    print(f"widenings     {w['hold']} of {w['cases']} get round four's verdict "
          f"with the round-five entries removed")
    r = report["follow_ups"]
    print(f"follow_ups    {r['met']} of {r['cases']} as declared")
    c = report["completions"]
    print(f"completions   {sum(x['ok'] for x in c['bounded'])} of "
          f"{len(c['bounded'])} bounded answers sound and sharp over "
          f"{c['per_answer']} completions each")
    i = report["interference"]
    print(f"interference  round four held {i['round_four_held']}, three "
          f"{i['round_three_held']}, two {i['round_two_held']}, one "
          f"{i['round_one_held']}; moves {i['moved']['met']} of "
          f"{i['moved']['cases']}; router rows changed "
          f"{len(i['router_rows_changed'])}")
    if "scripts" in report:
        s = report["scripts"]
        print(f"scripts       {s['verified']} of {s['chains']} verified, "
              f"{s['aligned']} of {s['steps']} steps aligned")
        for kind, n in s["mutants"].items():
            print(f"  mutation {kind:<10} caught {s['caught'][kind]} of {n}")
    return 0


def _stepwise_four(args) -> int:
    """The stepwise planner, round four (Phase 85): folds with a hole, H1-H7
    against the marks declared in ``studies/HOLE_FOLDS_STUDY.md`` before any
    code."""
    from .runtime import stepwise_four as s4
    report = s4.stepwise_four_report(scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for key in ("orders", "bounded", "ranks", "present"):
        r = report[key]
        print(f"{key:<13} {r['met']} of {r['cases']} as declared, wrong "
              f"{r['wrong']}; round three's reader answers "
              f"{r['round_three_answers']}; the machine answered "
              f"{r['machine_answered_before']} before and "
              f"{r['machine_answers_now']} now")
    p = report["present"]
    print(f"present       missing rows named in {p['named_ok']} of "
          f"{len(p['named'])} answered chains")
    r = report["follow_ups"]
    print(f"follow_ups    {r['met']} of {r['cases']} as declared")
    c = report["completions"]
    print(f"completions   {sum(x['ok'] for x in c['bounded'])} of "
          f"{len(c['bounded'])} bounded answers hold over every one of "
          f"{c['per_answer']} completions with both ends attained; "
          f"{sum(x['ok'] for x in c['refusals'])} of {len(c['refusals'])} "
          f"refusals move by at least a million")
    i = report["interference"]
    print(f"interference  round three held: {i['round_three_held']}; round "
          f"two held: {i['round_two_held']}; round one held: "
          f"{i['round_one_held']}; {i['router_read']} of "
          f"{i['router_questions']} router questions read; turned into "
          f"answers: {len(i['turned_into_answers'])}")
    if "scripts" in report:
        s = report["scripts"]
        print(f"scripts       {s['verified']} of {s['chains']} verified, "
              f"{s['aligned']} of {s['steps']} steps aligned")
        for kind, n in s["mutants"].items():
            print(f"  mutation {kind:<10} caught {s['caught'][kind]} of {n}")
    return 0


def _measurands(args) -> int:
    """Measurands (Phase 86): kinds of quantity in the stepwise planner, M1-M6
    against the marks declared in ``studies/MEASURANDS_STUDY.md`` before any
    code."""
    from .runtime import measurand_report as mr
    report = mr.measurand_report(scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for key in ("kinds", "temperatures", "constants"):
        r = report[key]
        print(f"{key:<13} {r['met']} of {r['cases']} as declared, wrong "
              f"{r['wrong']}; kinds off answers {r['kinds_off_answers']}; "
              f"the machine answered {r['machine_answered_before']} before "
              f"and {r['machine_answers_now']} now")
    c = report["control"]
    print(f"control       kinds off answers "
          f"{len(c['kind_refusals_answered'])} of the KIND_MISMATCH refusals "
          f"(" + ", ".join(f"{i} as {v}" for i, v in
                           c["kind_refusals_answered"]) + f"); "
          f"{len(c['refusals_answered'])} kind refusals answered in all; "
          f"{len(c['new_answers'])} answers are new")
    a = report["amendments"]
    print(f"amendments    {a['met']} of {a['cases']} earlier cases take the "
          f"amended verdict with the kinds on and the original with them off")
    i = report["interference"]
    print(f"interference  round four held: {i['round_four_held']}; round "
          f"three held: {i['round_three_held']}; round two held: "
          f"{i['round_two_held']}; round one held: {i['round_one_held']}; "
          f"{i['router_read']} of {i['router_questions']} router questions "
          f"read; turned into answers: {len(i['turned_into_answers'])}")
    if "scripts" in report:
        s = report["scripts"]
        print(f"scripts       {s['verified']} of {s['chains']} verified, "
              f"{s['aligned']} of {s['steps']} steps aligned")
        for kind, n in s["mutants"].items():
            print(f"  mutation {kind:<10} caught {s['caught'][kind]} of {n}")
    return 0


def _measurand_register(args) -> int:
    """The measurand register (Phase 87): register values read through their
    measurand, conversions through a stated efficiency and the elementary
    charge, R1-R7 against the marks declared in
    ``studies/MEASURAND_REGISTER_STUDY.md`` before any code."""
    from .runtime import measurand_register_report as rr
    report = rr.measurand_register_report(scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for key in ("register", "conversions", "charges"):
        r = report[key]
        print(f"{key:<12} {r['met']} of {r['cases']} as declared, wrong "
              f"{r['wrong']}; register off answers "
              f"{r['register_off_answers']}; the machine answered "
              f"{r['machine_answered_before']} before and "
              f"{r['machine_answers_now']} now")
    c = report["control"]
    print(f"control      naive answers {len(c['naive_wrong'])} conversion "
          f"cases wrongly (" + ", ".join(f"{i} as {v}" for i, v in
                                         c["naive_wrong"]) + f"), right "
          f"{len(c['naive_right'])}; unrestricted: "
          + ", ".join(f"{i} {v[0]}" for i, v in c["unrestricted"])
          + f"; met: {c['met']}")
    e = report["earlier"]
    print(f"earlier      Phase 86 held: {e['phase86_held']}; round four "
          f"held: {e['round_four_held']}; round three held: "
          f"{e['round_three_held']}; round two held: {e['round_two_held']}; "
          f"round one held: {e['round_one_held']}")
    k = report["census"]
    print(f"census       {k['same_kind']} of {k['related_pairs']} related "
          f"pairs of one kind; withdrawn {len(k['withdrawn'])}; "
          f"{k['registered']} of {k['scales']} scales registered")
    if "scripts" in report:
        s = report["scripts"]
        print(f"scripts      {s['verified']} of {s['chains']} verified, "
              f"{s['aligned']} of {s['steps']} steps aligned")
        for kind, n in s["mutants"].items():
            print(f"  mutation {kind:<10} caught {s['caught'][kind]} of {n}")
    return 0


def _celsius_register(args) -> int:
    """The Celsius register (Phase 99): the ITS-90 fixed points held in
    degrees Celsius, the scale table's offset row, and the planner reading a
    Celsius register value as a level, C1-C7 against the marks declared in
    ``studies/CELSIUS_REGISTER_STUDY.md`` before any code."""
    from .runtime import celsius_register_report as cr
    report = cr.celsius_register_report(scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    g = report["register"]
    print(f"register  {g['rows']} rows, exact {g['exact']}; the offset row "
          f"carries {g['carried_match']} of {g['rows']} onto ITS-90's kelvin "
          f"column; increasing {g['increasing']}; above absolute zero "
          f"{g['above_absolute_zero']}; met: {g['met']}")
    o = report["order"]
    print(f"order     {o['met']} of {o['cases']} as declared, wrong "
          f"{o['wrong']}")
    k = report["column"]
    print(f"column    {k['met']} of {k['cases']} as declared")
    p = report["planner"]
    print(f"planner   {p['met']} of {p['cases']} as declared, wrong "
          f"{p['wrong']}; the machine answered "
          f"{p['machine_answered_before']} before and "
          f"{p['machine_answers_now']} now")
    c = report["control"]
    print(f"control   offset dropped flips {', '.join(c['flips'])}; answers "
          f"{len(c['naive_planner_wrong'])} of "
          f"{c['naive_planner_declared']} planner cases wrongly; register "
          f"absent answers {c['register_absent_answers']}; met: {c['met']}")
    e = report["earlier"]
    print(f"earlier   scale table {e['scale_table']['as_declared']} of "
          f"{e['scale_table']['declared']}; ordering "
          f"{e['ordering']['as_declared']} of {e['ordering']['declared']}; "
          f"extremum {e['extremum']['as_declared']} of "
          f"{e['extremum']['declared']}; measurand register "
          f"{e['measurand_register']['met']} of "
          f"{e['measurand_register']['cases']}; met: {e['met']}")
    a = report["agreement"]
    print(f"agreement {a['within_rounding']} of {a['compared']} fixed points "
          f"within 0.005 K of the element register's melting point; outside: "
          + (", ".join(f"{n} by {g} K" for n, g in a["outside"]) or "none"))
    if "scripts" in report:
        s = report["scripts"]
        print(f"scripts   {s['verified']} of {s['chains']} verified, "
              f"{s['aligned']} of {s['steps']} steps aligned; offset lies "
              f"caught {s['offset_lies_caught']} of {s['offset_lies']}")
        for kind, n in s["mutants"].items():
            if n:
                print(f"  mutation {kind:<10} caught {s['caught'][kind]} "
                      f"of {n}")
    return 0


def _discourse_state(args) -> int:
    """Discourse state (Phase 92): a tie carried as a column, the fourth
    shape of follow-up and follow-ups bound on every surface, D1-D8 against
    the marks declared in ``studies/DISCOURSE_STATE_STUDY.md`` before any
    code."""
    from .runtime import discourse_report as dr
    report = dr.discourse_report(census=not args.no_census)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for key, g in report["groups"].items():
        print(f"{key:<8} {g['met']} of {g['cases']} as declared, wrong "
              f"{len(g['wrong'])}, refusals {g['refusals']}")
    c = report["control"]
    print(f"control  Phase 55's layer gives {len(c['base']['new_as_declared'])}"
          f" of the {c['base']['new_cases']} new-behaviour cases as declared;"
          f" first winner answers {c['first_winner']['answered']} of "
          f"{c['first_winner']['cases']} columns, dropping "
          f"{c['first_winner']['rows_dropped']} rows; recency differs on "
          f"{len(c['recency']['differs'])} of {c['recency']['cases']} prior "
          f"cases; the session alone answers "
          f"{len(c['session_alone']['answers_as_declared'])} of the surface "
          f"cases; carry off reverts {len(c['carry_off']['reverted'])} of "
          f"{c['carry_off']['ties']} ties")
    e = report["earlier"]
    print(f"earlier  {e['met_count']} of {e['cases']} of Phase 55's follow-ups"
          f" as declared now; moved {', '.join(e['moved']) or 'none'}")
    k = report["cells"]
    print(f"cells    {k['cells']} cells and {k['singles']} single answers, "
          f"{len(k['differ'])} differ from the text asked alone")
    if report["census"]:
        n = report["census"]
        print(f"census   {n['taken_count']} of {n['strings']} earlier strings "
              f"carry a new phrasing ({n['distinct_taken']} distinct), "
              f"{n['taken_answered_alone']} of them answered alone; "
              f"{n['released_count']} released")
    print("marks    " + ", ".join(f"{m} {'met' if v else 'MISSED'}"
                                  for m, v in report["marks"].items()
                                  if v is not None))
    return 0


def _imperative(args) -> int:
    """The imperative grammar (Phase 95): programs with state -- assignment,
    loops, branches, functions and ``match`` -- in the reverse grammar, I1-I9
    against the marks declared in ``studies/IMPERATIVE_GRAMMAR_STUDY.md``
    before any code."""
    from .runtime import imperative_report as ir
    report = ir.imperative_report(run_scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    m = report["marks"]
    for k in ("I1", "I2", "I3"):
        print(f"{k} said        {m[k]['right']} of {m[k]['cases']} said, read "
              f"back and equal to CPython; wrong {len(m[k]['wrong_ids'])}")
    print(f"I4 refusals   {m['I4']['right']} of {m['I4']['refusals']} by name; "
          f"{m['I4']['unreadable']} of {m['I4']['read_refusals']} sentences "
          "UNREADABLE")
    b = m["I5"]["battery"]
    print(f"I5 read back  {m['I5']['read_back']['right']} of "
          f"{m['I5']['read_back']['of']}; battery {b['read_back']} of "
          f"{b['programs']} programs, {b['distinct_sentences']} distinct "
          "sentences")
    print(f"I6 scripts    {m['I6']['verified']} of {m['I6']['of']} VERIFIED, "
          f"{m['I6']['mutants_rejected']} mutants rejected")
    print(f"I7 regression moved {m['I7']['moved']}; as declared "
          f"{len(m['I7']['moved_as_declared'])}; earlier declared cases moved "
          f"{m['I7']['earlier_moved']}")
    print(f"I8 before     {m['I8']['said_before']} of {m['I8']['cases']} said")
    print(f"I9 limits x{m['I9']['scale']}  {len(m['I9']['changed'])} of "
          f"{m['I9']['answers']} answers changed; "
          f"{m['I9']['limit_refusals_still_refused']} of 2 limit refusals "
          "still refused")
    d = report["differential"]
    print(f"post hoc      differential battery: {d['imperative_answers']} "
          f"imperative answers of {d['programs']} programs, {d['wrong']} "
          "wrong")
    print("met      " + ", ".join(report["met"]))
    print("not met  " + (", ".join(report["not_met"]) or "none"))
    return 0


def _third_sort(args) -> int:
    """The third sort (Phase 94): strings, tuples and ranges in the reverse
    grammar with count-first literals, and the dialect widened to string
    methods, lists and dicts -- T1-T6 and D1-D4 against the marks declared in
    ``studies/THIRD_SORT_STUDY.md`` before any code."""
    from .runtime import third_sort_report as tr
    report = tr.third_sort_report(run_scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    m = report["marks"]
    print(f"T1 say       {m['T1']['right']} of {m['T1']['cases']} sentences "
          f"and values as declared")
    print(f"T2 refusals  {m['T2']['right']} of {m['T2']['refusals']} by name; "
          f"{m['T2']['unreadable']} of {m['T2']['read_refusals']} sentences "
          "UNREADABLE")
    b = m["T3"]["battery"]
    print(f"T3 read back {m['T3']['read_back']['right']} of "
          f"{m['T3']['read_back']['of']}; battery {b['read_back']} of "
          f"{b['terms']} terms, {b['distinct_sentences']} distinct sentences")
    print(f"T4 scripts   {m['T4']['verified']} of {m['T4']['scripts']} "
          f"VERIFIED, {m['T4']['caught']} of {m['T4']['mutants']} mutants "
          "rejected")
    print(f"T5 dialect   {m['T5']['agree']} of {m['T5']['declared']} programs "
          f"inside and agreeing; outside {', '.join(m['T5']['outside'])}")
    print(f"T6 earlier   {m['T6']['cases']} say cases, moved "
          f"{', '.join(m['T6']['moved']) or 'none'}; W2 inside "
          f"{m['T6']['w2_inside']}")
    d1 = m["D1"]
    print(f"D1 values    {d1['right']} of {d1['total']} equal CPython "
          f"(strings {d1['string']['right']}, lists {d1['list']['right']}, "
          f"dicts {d1['dict']['right']})")
    print(f"D2 refusals  {m['D2']['right']} of {m['D2']['refusals']} by name; "
          f"{m['D2']['superseded_answered']} of {m['D2']['superseded']} "
          f"superseded answered; Phase 64 kept {m['D2']['phase64_kept']} of "
          f"{m['D2']['phase64_in_force']}")
    print(f"D3 scripts   {m['D3']['verified']} VERIFIED, {m['D3']['caught']} "
          "mutants rejected")
    print(f"D4 earlier   {len(m['D4']['values_moved'])} of "
          f"{m['D4']['values']} Phase 64 values moved; battery "
          f"{m['D4']['battery_wrong']} wrong of {m['D4']['battery_answered']} "
          "answered")
    print(f"met {', '.join(report['met'])}; not met "
          f"{', '.join(report['not_met']) or 'none'}")
    return 0 if not report["not_met"] else 1


def _register_world(args) -> int:
    """The register against the world (Phase 93): every element row, in the
    three fields an outside source holds, compared with the frozen CIAAW and
    NIST tables and never written; and the completion gate's nested holdout
    -- R1-R7 against the marks declared in
    ``studies/REGISTER_WORLD_STUDY.md`` before any code."""
    from .runtime import register_world_report as rr
    report = rr.register_world_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    w = report["world"]
    for source in w["sources"]:
        print(f"source   {source['file']}: {source['rows']} rows, "
              f"retrieved {source['retrieved']}, sha256 "
              f"{source['raw_sha256'][:16]}...")
    for field, counts in w["counts"].items():
        shown = ", ".join(f"{k} {v}" for k, v in counts.items() if v)
        print(f"{field:<24} {shown}")
    for field, rows in w["discrepant"].items():
        if rows:
            print(f"discrepant {field}: {', '.join(rows)}")
    m = w["molecules"]
    print(f"molecules {m['rows']}: " + ", ".join(
        f"{k} {v}" for k, v in m["counts"].items() if v))
    q = report["questions"]
    print(f"questions {q['met']} of {q['cases']} as declared, wrong "
          f"{q['wrong']}")
    a = report["audit"]
    print(f"audit    {a['caught']} of {a['injected']} injected errors "
          f"caught; {a['flagged']} of {a['honest']} world values flagged")
    e = report["earlier"]
    print(f"earlier  {e['correct']} of {e['cases']} interval questions "
          f"correct; moved {', '.join(e['moved']) or 'none'}")
    g = report["gate"]
    print(f"gate     demoted {', '.join(g['outcome']['demoted']) or 'none'};"
          f" narrowed " + (", ".join(f"{k} to the {v}" for k, v in
                                    g["outcome"]["narrowed"].items())
                           or "none")
          + f"; estimated {g['first_gate_estimated']} -> "
          f"{g['coverage']['estimated']} ({g['lost_cells']} lost)")
    print("marks    " + ", ".join(f"{k} {'met' if v else 'MISSED'}"
                                  for k, v in report["marks"].items()
                                  if v is not None))
    return 0


def _typed_operators(args) -> int:
    """Typed operators (Phase 90): real, reactive and apparent power and the
    power factor from phasors and the power triangle, the dot against the
    cross product, T1-T7 against the marks declared in
    ``studies/TYPED_OPERATORS_STUDY.md`` before any code."""
    from .runtime import typed_operators_report as tr
    report = tr.typed_operators_report(scripts=not args.no_scripts,
                                       route=not args.no_route)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for key, g in report["groups"].items():
        print(f"{key:<8} {g['met']} of {g['cases']} as declared, wrong "
              f"{len(g['wrong'])}; through the router as declared "
              f"{g['routed_before']} before and {g['routed_after']} now")
    c = report["control"]
    print(f"control  naive answers {c['naive_answers']}, wrongly "
          f"{c['naive_wrong']} (" + ", ".join(f"{i} as {v}" for i, v in
                                              c["wrong_ids"]) + ")")
    e = report["earlier"]
    print(f"earlier  {len(e['read'])} of {e['strings']} earlier questions "
          f"read by the typed reader")
    s = report["scripts"]
    if s:
        print(f"scripts  {s['verified']} of {s['scripts']} verified; "
              f"mutations caught {s['caught']} of {s['mutants']}")
    k = report["census"]
    print(f"census   {k['phasor_pairs']} phasor pairs, "
          f"{k['phasor_violations']} violations; {k['vector_pairs']} vector "
          f"pairs, {k['vector_violations']} violations")
    print("marks    " + " ".join(f"{m}={'met' if v else ('-' if v is None else 'NOT MET')}"
                                 for m, v in report["marks"].items()))
    return 0 if all(v is not False for v in report["marks"].values()) else 1


def _planner_loop(args) -> int:
    """The loop through the planner (Phase 88): ``derive``, ``ask`` and
    ``solve`` as dialect values, programs whose control flow is the loop,
    and questions about a Python expression through a frame, W1-W7 against
    the marks declared in ``studies/PLANNER_LOOP_STUDY.md`` before any
    code."""
    from .runtime import planner_loop_report as lr
    report = lr.planner_loop_report(scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for key in ("derive", "ask", "solve", "loop", "frames"):
        r = report[key]
        print(f"{key:<12} {r['met']} of {r['cases']} as declared, wrong "
              f"{r['wrong']}; the machine answered "
              f"{r['machine_answered_before']} before and "
              f"{r['machine_answers_now']} now")
    b = report["bridge_off"]
    print(f"bridge off   {b['answered']} of {b['bridge_cases']} bridge cases "
          f"answered; {b['refused_by_name']} refused by name "
          f"({b['unavailable']} BRIDGE_UNAVAILABLE)")
    c = report["census"]
    print(f"census       {len(c['moved'])} of {c['questions']} earlier "
          f"questions change surface")
    e = report["earlier"]
    print(f"earlier      dialect values moved {len(e['python_values_moved'])}"
          f", refusals moved {len(e['python_refusals_moved'])}, battery "
          f"wrong {e['battery_wrong']} of {e['battery_total']}; stepwise "
          f"earlier rounds held: {e['stepwise_earlier_held']}")
    m = report["machine"]
    print(f"machine      {m['answered_now']} of {m['answer_cases']} ANSWER "
          f"cases answered through the router (before: "
          f"{m['answered_before']})")
    g = report["paraphrases"]
    print(f"item 9       the router answers {g['answered']} of "
          f"{g['questions']} English paraphrases of the loop programs")
    if "scripts" in report:
        s = report["scripts"]
        print(f"scripts      {s['verified']} of {s['programs']} verified, "
              f"{s['sub_scripts']} sub-answer scripts re-run")
        for kind, n in s["mutants"].items():
            print(f"  mutation {kind:<10} caught {s['caught'][kind]} of {n}")
    return 0


def _carried_fork(args) -> int:
    """The carried fork: K1-K4 against the marks declared in
    ``studies/CARRIED_FORK_STUDY.md`` before the module existed."""
    from .reasoning import carried_fork as cf
    report = cf.carried_fork_report(full=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    k1, k2, k3, k4a, k4b = (report[k] for k in ("K1", "K2", "K3", "K4a",
                                               "K4b"))
    for row in k1["rows"]:
        print(f"K1  k={row['k']:<3} reads {row['reads']:>7}  answered "
              f"{row['answered']:>7}  wrong {row['wrong']}  open "
              f"{row['open']:>6}  open-world misreads "
              f"{row['hostile_answered_all_wrong']}/{row['hostile_reads']}")
    print(f"K2  double reads {k2['double_reads']}  answered {k2['answered']}"
          f"  wrong {k2['wrong']}  witness live {k2['witness_live']}")
    for row in k3["rows"]:
        print(f"K3  |U|={row['unsure_size']}  answered {row['answered']}/"
              f"{row['reads']}  wrong {row['wrong']}")
    print(f"K4a cosets {k4a['cosets']}  certified A_1^24 with 48 vertices "
          f"{k4a['certified_a1_24_with_48']}")
    print(f"K4b estimate right {k4b['estimate_right']}  wrong "
          f"{k4b['estimate_wrong']}  tied {k4b['estimate_tied']} of "
          f"{k4b['reads']}  (snap {k4b['snap_right']}, soft ML "
          f"{k4b['soft_ml_right']})")
    print(f"K4c certified cut answered {k4b['certified_cut_answered']}  "
          f"wrong {k4b['certified_cut_wrong']}")
    for key, ok in report["marks"].items():
        print(f"{key:<4} pass mark {'met' if ok else 'not met'}")
    return 0


def _second_view(args) -> int:
    """Second readings (Phase 96): the framed register against the marks
    V1-V9 declared in ``studies/SECOND_VIEW_STUDY.md`` before any code."""
    from .runtime import second_view_report as svr
    report = svr.second_view_full_report(full=not args.quick,
                                         run_scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    v1, v2, v3, v4, v5 = (report[k] for k in ("V1", "V2", "V3", "V4", "V5"))
    print(f"frames        {report['frames']}")
    print(f"V1  two views   reads {v1['reads']}  resolved {v1['resolved']}  "
          f"wrong {v1['wrong']}  live count off prediction {v1['mismatched']}"
          f"  open bursts {v1['open_bursts']}")
    print(f"V2  three views reads {v2['reads']}  resolved {v2['resolved']}  "
          f"wrong {v2['wrong']}")
    print(f"V3  single second frames: least open {v3['least_open']} "
          f"(k = 1..23: {sorted(v3['open_by_frame'].values())})")
    print(f"V4  X1 through the register: reads {v4['reads']}  resolved "
          f"{v4['resolved']}  wrong {v4['wrong']}")
    print(f"V5  weight <= 3: two {v5['two']['right']}/{v5['two']['reads']}  "
          f"three {v5['three']['right']}/{v5['three']['reads']}")
    for name, row in report["weight5"].items():
        print(f"    weight 5 ({name}): answered {row['answered']}  wrong "
              f"{row['wrong']}  open {row['open']}  contradicted "
              f"{row['contradicted']} of {row['reads']}")
    ph = report["post_hoc_x1_three"]
    print(f"    post hoc: X1 through three views, independent faults: "
          f"{ph['resolved']}/{ph['reads']} resolved, {ph['wrong']} wrong")
    for row in report["V6"]["rows"]:
        print(f"V6  k={row['k']:<3} reads {row['reads']:>7}  context alone "
              f"{row['context_answered']:>7}  composed {row['answered']:>7}  "
              f"wrong {row['wrong']}  open {row['open']} (predicted "
              f"{row['predicted_open']})")
    for name, row in report["V7"]["rows"].items():
        print(f"V7  {name:<5} reads {row['reads']:>6}  escalation = "
              f"intersection {row['equal']}  rate ranking = D ranking "
              f"{row['rate_equal']}  resolved beyond {row['gained']}")
    v8 = report["V8"]
    print(f"V8  dialect cases answered "
          f"{sum(1 for r in v8['cases'] if r['answered'])}/{len(v8['cases'])}"
          f"  refusals as declared "
          f"{sum(1 for r in v8['refusals'] if r['as_declared'])}/"
          f"{len(v8['refusals'])}")
    for key, ok in report["marks"].items():
        print(f"{key:<4} mark {'met' if ok else 'not met'}")
    return 0


def _nonlinear(args) -> int:
    """Nonlinear elimination (Phase 103): the marks E1-E7 declared in
    ``evaluation/nonlinear_cases.py`` before any code."""
    from .runtime import nonlinear_report as nr
    report = nr.nonlinear_report(run_scripts=not args.no_scripts,
                                 battery=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for r in report["systems"]:
        print(f"      {r['id']:<22} {r['layer']:<13} branches "
              f"{r['matched']}/{r['declared']} (machine {r['machine']})"
              f"{'' if r.get('gate', True) else '  GATE FAILED'}")
    e1, e2, e3 = report["E1"], report["E2"], report["E3"]
    print(f"E1  {e1['passed']}/{e1['of']} systems with exactly the declared "
          f"branches")
    print(f"E2  {e2['passed']}/{e2['of']} refusals by the declared code")
    if not e3.get("skipped"):
        print(f"E3  {e3['verified']}/{e3['answered']} scripts verify, "
              f"{e3['mutants_rejected']}/{e3['answered']} mutants rejected")
    e4 = report["E4"]
    print(f"E4  {e4['same']}/{e4['questions']} Phase 98 questions unchanged, "
          f"{e4['nonlinear_now_read']} NONLINEAR refusals now read, "
          f"{e4['changed_otherwise']} changed otherwise; Phase 98 refusals "
          f"with the layer off {e4['phase98_refusals']}")
    e5 = report["E5"]
    if not e5.get("skipped"):
        print(f"E5  planted battery: {e5['answered']}/{e5['systems']} "
              f"answered, planted point in {e5['planted']}, {e5['wrong']} "
              f"wrong; refused {e5['refused']}")
    e6 = report["E6"]
    print(f"E6  {e6['refused_nonlinear']}/{e6['of']} declared systems refused "
          f"NONLINEAR with the layer off")
    print(f"E7  Lean {report['E7']}")
    for key, ok in report["marks"].items():
        print(f"{key:<4} mark "
              f"{'met' if ok else ('skipped' if ok is None else 'not met')}")
    return 0


def _derivation(args) -> int:
    """Derivations and proofs (Phase 106): the marks R1-R9 declared in
    ``evaluation/derivation_cases.py`` before any code."""
    from .runtime import derivation_report as dr
    report = dr.derivation_report(run_scripts=not args.no_scripts,
                                  battery=200 if args.quick else None)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    m = report["marks"]
    for key in ("R1", "R2", "R3", "R4"):
        for r in m[key]["rows"]:
            flags = "" if r.get("gate", True) else "  GATE FAILED"
            if r.get("mutant_rejected") is False:
                flags += "  MUTANT ACCEPTED"
            print(f"      {key} {r['id']:<26} "
                  f"{'as declared' if r['as_declared'] else 'MISSED'}{flags}")
    names = {"R1": "proofs", "R2": "equations of motion",
             "R3": "transfer models", "R4": "profiles", "R5": "refusals"}
    for key in ("R1", "R2", "R3", "R4", "R5"):
        print(f"{key}  {m[key]['as_declared']}/{m[key]['of']} {names[key]} "
              f"as declared")
    if m["R6"].get("met") is not None:
        print(f"R6  {m['R6']['verified']}/{m['R6']['readings']} scripts "
              f"verify, {m['R6']['mutants_rejected']}/{m['R6']['readings']} "
              f"mutants rejected")
    b = m["R7"]
    print(f"R7  {b['formulas']} random formulas: {b['kinds']}; unsound "
          f"{b['unsound']}, gaps {b['gaps']}, script failures "
          f"{b['script_failures']}; classical with a Kripke countermodel "
          f"{b['classical_with_kripke']}")
    o = m["R8"]
    print(f"R8  outside class P: {o['answered']}/{o['of']} answered with "
          f"fragment and gate; {len(o['moved'])} of {o['texts_checked']} "
          f"other texts moved")
    print(f"R9  Lean {m['R9']}")
    for key, mk in m.items():
        print(f"{key:<4} mark {'met' if mk.get('met') else 'not met'}")
    print(f"{report['met']} of {report['of']} marks met")
    return 0


def _derivation_two(args) -> int:
    """The rest of track P (Phase 107): information inequalities, codes,
    rate distortion, maximum entropy, eigenvalue problems, transmission,
    the FFT and the rate posterior -- the marks Q1-Q11 declared in
    ``evaluation/derivation_two_cases.py`` before any code."""
    from .runtime import derivation_two_report as dr
    report = dr.derivation_two_report(run_scripts=not args.no_scripts,
                                      battery=100 if args.quick else None)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    m = report["marks"]
    for key in ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6"):
        for r in m[key]["rows"]:
            flags = "" if r.get("gate", True) else "  GATE FAILED"
            if r.get("mutant_rejected") is False:
                flags += "  MUTANT ACCEPTED"
            print(f"      {key} {r['id']:<28} "
                  f"{'as declared' if r['as_declared'] else 'MISSED'}{flags}")
    names = {"Q1": "information inequalities", "Q2": "codes",
             "Q3": "rate-distortion questions", "Q4": "maximum-entropy laws",
             "Q5": "eigenvalue problems",
             "Q6": "transmission, FFT and posterior questions",
             "Q7": "refusals"}
    for key in ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7"):
        print(f"{key}  {m[key]['as_declared']}/{m[key]['of']} {names[key]} "
              f"as declared")
    if m["Q8"].get("met") is not None:
        print(f"Q8  {m['Q8']['verified']}/{m['Q8']['readings']} scripts "
              f"verify, {m['Q8']['mutants_rejected']}/{m['Q8']['readings']} "
              f"mutants rejected")
    a, b = m["Q9"]["inequalities"], m["Q9"]["codes"]
    print(f"Q9  {a['inequalities']} random inequalities: {a['kinds']}; "
          f"unsound {a['unsound']}, undecided {a['undecided']}, script "
          f"failures {a['script_failures']}")
    print(f"    {b['codes']} random codes: {b['uniquely_decodable']} uniquely "
          f"decodable; disagreements {b['disagreements']}, Kraft violations "
          f"{b['kraft_violations']}, construction failures "
          f"{b['construction_failures']}")
    o = m["Q10"]
    print(f"Q10 outside: {o['answered']}/{o['of']} answered with fragment "
          f"and gate; still refused {o['stays_refused']}; "
          f"{len(o['moved'])} of {o['texts_checked']} other texts moved")
    print(f"Q11 Lean {m['Q11']}")
    for key, mk in m.items():
        print(f"{key:<4} mark {'met' if mk.get('met') else 'not met'}")
    print(f"{report['met']} of {report['of']} marks met")
    return 0


def _derivation_three(args) -> int:
    """Past the limits of the second derivation study (Phase 118):
    information inequalities past the Shannon cone, rate distortion past the
    tight range, Robin eigenvalue problems -- the marks N1-N10 declared in
    ``evaluation/derivation_three_cases.py`` before any code."""
    from .runtime import derivation_three_report as dr
    report = dr.derivation_three_report(battery=30 if args.quick else None,
                                        outside=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    m = report["marks"]
    for r in m["N5"]["rows"]:
        flags = "" if r["gate"] else "  GATE FAILED"
        if not r["mutant_rejected"]:
            flags += "  MUTANT ACCEPTED"
        print(f"      N5 {r['id']:<28} {'answered' if r['answered'] else 'refused ' + str(r['code'])}{flags}")
    names = {"N1": "information inequalities", "N2": "rate-distortion sources",
             "N3": "Robin problems"}
    for key in ("N1", "N2", "N3"):
        print(f"{key}  {m[key]['as_declared']}/{m[key]['of']} {names[key]} "
              f"as declared")
    n4 = m["N4"]
    print(f"N4  {n4['layer']['as_declared']}/{n4['layer']['of']} refusals as "
          f"declared at the layer, {n4['frames']['as_declared']}/"
          f"{n4['frames']['of']} through the frames")
    n5 = m["N5"]
    print(f"N5  {n5['verified']}/{n5['readings']} scripts verify, "
          f"{n5['mutants_rejected']}/{n5['readings']} mutants rejected")
    a = m["N6"]
    print(f"N6  {a['claims']} random claims: {a['kinds']}; unsound "
          f"{a['unsound']}, inconsistent {a['inconsistent']}, script failures "
          f"{a['script_failures']}, left NOT_SHANNON {a['undecided']}")
    b = m["N7"]
    print(f"N7  {b['sources']} random sources ({b['past_the_bound']} past the "
          f"bound): tiling {b['tiling_failures']}, discontinuities "
          f"{b['discontinuities']}, SLB mismatches {b['slb_mismatches']}, "
          f"below the bound {b['below_slb']}, script failures "
          f"{b['script_failures']}, Blahut-Arimoto failures "
          f"{b['blahut_arimoto_failures']} (worst {b['blahut_arimoto_worst']})")
    c = m["N8"]
    print(f"N8  {c['problems']} random Robin problems {c['cases']}: script "
          f"failures {c['script_failures']}, Newton outside "
          f"{c['newton_outside']}, negative eigenvalue wrong "
          f"{c['negative_wrong']}, interval failures {c['interval_failures']}")
    n9 = m["N9"]
    if n9.get("met") is not None:
        print(f"N9  Phase 107: {n9['phase_107']['met_marks']} of "
              f"{n9['phase_107']['of']} marks; "
              f"{len(n9['unmoved']['moved'])} of "
              f"{n9['unmoved']['texts_checked']} other texts moved "
              f"({n9['unmoved']['read_both_ways']} read both ways)")
    print(f"N10 Lean {m['N10']}")
    for key, mk in m.items():
        print(f"{key:<4} mark {'met' if mk.get('met') else 'not met'}")
    print(f"{report['met']} of {report['of']} marks met")
    return 0


def _derivation_four(args) -> int:
    """Past the limits of the third derivation study (Phase 119): chained
    copies past Zhang-Yeung and five-variable inequalities, rate distortion
    for any distortion matrix, Robin problems at both ends and with a
    symbolic coefficient -- the marks P1-P10 declared in
    ``evaluation/derivation_four_cases.py`` before any code."""
    from .runtime import derivation_four_report as dr
    report = dr.derivation_four_report(battery=10 if args.quick else None,
                                       outside=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    m = report["marks"]
    for r in m["P5"]["rows"]:
        flags = "" if r["gate"] else "  GATE FAILED"
        if not r["mutant_rejected"]:
            flags += "  MUTANT ACCEPTED"
        print(f"      P5 {r['id']:<34} {'answered' if r['answered'] else 'refused ' + str(r['code'])}{flags}")
    names = {"P1": "information inequalities", "P2": "rate-distortion sources",
             "P3": "Robin problems"}
    for key in ("P1", "P2", "P3"):
        print(f"{key}  {m[key]['as_declared']}/{m[key]['of']} {names[key]} "
              f"as declared")
    p4 = m["P4"]
    print(f"P4  {p4['layer']['as_declared']}/{p4['layer']['of']} refusals as "
          f"declared at the layer, {p4['frames']['as_declared']}/"
          f"{p4['frames']['of']} through the frames")
    p5 = m["P5"]
    print(f"P5  {p5['verified']}/{p5['readings']} scripts verify, "
          f"{p5['mutants_rejected']}/{p5['readings']} mutants rejected")
    a, b = m["P6"]["five"], m["P6"]["phase_118"]
    print(f"P6  {a['claims']} random five-variable claims: {a['kinds']}; "
          f"unsound {a['unsound']}, inconsistent {a['inconsistent']}, script "
          f"failures {a['script_failures']}; Phase 118's battery: "
          f"{b['decided_by_copies']} of its {len(b['not_shannon'])} "
          f"NOT_SHANNON claims decided by copies")
    c = m["P7"]
    print(f"P7  {c['sources']} random sources ({c['degenerate']} with D_min "
          f"= D_max, {c['hamming']} Hamming): failures {c['failures']}")
    d = m["P8"]
    print(f"P8  {d['problems']} random Robin problems: failures "
          f"{d['failures']}")
    p9 = m["P9"]
    if p9.get("met") is not None:
        print(f"P9  Phase 118: {p9['phase_118']['met_marks']} of "
              f"{p9['phase_118']['of']} marks; "
              f"{len(p9['unmoved']['moved'])} of "
              f"{p9['unmoved']['texts_checked']} other texts moved "
              f"({p9['unmoved']['read_both_ways']} read both ways)")
    print(f"P10 Lean {m['P10']}")
    for key, mk in m.items():
        print(f"{key:<4} mark {'met' if mk.get('met') else 'not met'}")
    print(f"{report['met']} of {report['of']} marks met")
    return 0


def _cubic_trig(args) -> int:
    """A cubic in letters with three real roots (Phase 108): the marks
    T1-T9 declared in ``evaluation/cubic_trig_cases.py`` before any code."""
    from .runtime import cubic_trig_report as ct
    report = ct.cubic_trig_report(run_scripts=not args.no_scripts,
                                  battery=not args.quick,
                                  outside=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    m = report["marks"]
    for key in ("T1", "T2"):
        for r in m[key]["rows"]:
            print(f"      {key} {r['id']:<30} "
                  f"{'ok' if r['ok'] else 'MISSED'}"
                  f"{'' if r.get('gate', True) else '  GATE FAILED'}")
            print(f"         {r['value'][:160]}")
    print(f"T1  {m['T1']['passed']}/{m['T1']['of']} homogeneous cubics with "
          f"exactly the declared branches")
    print(f"T2  {m['T2']['passed']}/{m['T2']['of']} Viete cubics with exactly "
          f"the declared branches, the condition and the form stated")
    if m["T3"].get("met") is not None:
        print(f"T3  {m['T3']['verified']}/{m['T3']['answered']} scripts "
              f"verify, {m['T3']['mutants_rejected']}/{m['T3']['answered']} "
              f"mutants rejected")
    for r in m["T4"]["rows"]:
        print(f"T4  {r['id']}: {r['matched']}/{r['declared']} squared "
              f"frequencies, gate {r['gate']}, mutant rejected "
              f"{r['mutant_rejected']}: {', '.join(r['frequencies'])}")
    t5 = m["T5"]
    print(f"T5  unchanged readings moved {len(t5['unchanged_moved'])}, "
          f"motion cases moved {len(t5['motion_moved'])}/"
          f"{t5['motion_checked']}; Phase 104 marks "
          f"{t5.get('phase104', 'skipped')}")
    for key, name in (("T6", "Viete"), ("T7", "homogeneous")):
        if not m[key].get("skipped"):
            print(f"{key}  {name} battery: {m[key]['passed']}/"
                  f"{m[key]['count']} (seed {m[key]['seed']})")
    print(f"T8  Lean {m['T8']}")
    if not m["T9"].get("skipped"):
        t9 = m["T9"]
        print(f"T9  {t9['texts_checked']} texts read with the switch off and "
              f"on: moved {t9['moved']} (allowed {t9['moved_allowed']})")
    print(f"{report['met']} of {report['of']} marks met")
    return 0


def _quintic_radical(args) -> int:
    """Factoring past degree 6 and roots with no expression in radicals
    (Phase 112): the marks R1-R7 of ``evaluation/quintic_radical_cases.py``."""
    from .runtime import quintic_radical_report as qr
    report = qr.quintic_radical_report(run_scripts=not args.no_scripts,
                                       battery=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    m = report["marks"]
    for r in m["R1"]["rows"]:
        print(f"      R1 {r['id']:<26} "
              f"{'ok' if r['ok'] else 'MISSED'}  "
              f"{r.get('branches', 0)}/{r['declared']} real roots")
    for r in m["R4"]["rows"]:
        print(f"      R4 {r['id']:<26} {'ok' if r['ok'] else 'MISSED'}  "
              f"reason {'given' if r['reason'] else 'not given'}")
    print(f"R1  {m['R1']['passed']}/{m['R1']['of']} high-degree questions "
          f"with the declared real roots, every bracket sound")
    print(f"R2  {m['R2']['passed']}/{m['R2']['of']} certificate questions "
          f"carry the radical-free statement")
    print(f"R3  {m['R3']['passed']}/{m['R3']['of']} controls do not")
    print(f"R4  {m['R4']['passed']}/{m['R4']['of']} letter questions "
          f"refused with the declared reason")
    if not m["R5"].get("skipped"):
        print(f"R5  planted battery: {m['R5']['answered']}/{m['R5']['of']} "
              f"answered, {m['R5']['wrong']} wrong")
    if not m["R6"].get("skipped"):
        print(f"R6  Zassenhaus = Kronecker on {m['R6']['agree']}/"
              f"{m['R6']['of']} polynomials of degree 4 to 6 "
              f"({m['R6']['split']} reducible)")
    print(f"R7  Lean {m['R7']}")
    print(f"{report['met']} of {report['of']} marks met")
    return 0


def _frobenius_radical(args) -> int:
    """Roots with no expression in radicals, read from one Frobenius element
    (Phase 113): the marks F1-F9 of
    ``evaluation/frobenius_radical_cases.py``."""
    from .runtime import frobenius_radical_report as fr
    report = fr.frobenius_radical_report(battery=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    m = report["marks"]
    for key in ("F1", "F2", "F3"):
        for r in m[key]["rows"]:
            print(f"      {key} {'ok' if r['ok'] else 'MISSED'}  "
                  f"{r['question'].split(':', 1)[1].strip()}")
    for r in m["F4"]["rows"]:
        print(f"      F4 {r['id']:<26} {'ok' if r['ok'] else 'MISSED'}  "
              f"reason {r['reason'] or 'none'}")
    print(f"F1  {m['F1']['passed']}/{m['F1']['of']} non-solvable questions "
          f"carry the Frobenius statement")
    print(f"F2  {m['F2']['passed']}/{m['F2']['of']} solvable controls carry "
          f"no radical-free statement")
    print(f"F3  {m['F3']['passed']}/{m['F3']['of']} declared limit "
          f"(composite degree) silent")
    print(f"F4  {m['F4']['passed']}/{m['F4']['of']} letter questions refused "
          f"with the declared reason")
    if not m["F5"].get("skipped"):
        print(f"F5  soundness battery: {m['F5']['certified']} of "
              f"{m['F5']['of']} solvable polynomials certified")
        print(f"F6  reach battery: {m['F6']['frobenius']}/{m['F6']['of']} "
              f"certified by Frobenius, {m['F6']['conjugation']} by "
              f"conjugation, all of those also by Frobenius: "
              f"{m['F6']['conjugation_also_frobenius'] == m['F6']['conjugation']}")
        print(f"F7  distinct-degree reading = complete factorisation on "
              f"{m['F7']['agree']}/{m['F7']['of']} (polynomial, prime) pairs; "
              f"shape test right on {m['F7']['shapes_ok']}/"
              f"{m['F7']['shapes']} cycle types")
    print(f"F8  Lean {m['F8']}")
    if not m["F9"].get("skipped"):
        print(f"F9  Phase 112 report: {m['F9']['met_of']}")
    print(f"{report['met']} of {report['of']} marks met")
    return 0


def _primitive_radical(args) -> int:
    """Roots with no expression in radicals in composite degree, read from
    two Frobenius elements, and on the ``modes.higher`` route (Phase 114):
    the marks P1-P10 of ``evaluation/primitive_radical_cases.py``."""
    from .runtime import primitive_radical_report as pr
    report = pr.primitive_radical_report(battery=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    m = report["marks"]
    for key in ("P1", "P2", "P3"):
        for r in m[key]["rows"]:
            print(f"      {key} {'ok' if r['ok'] else 'MISSED'}  "
                  f"{r['question'].split(':', 1)[1].strip()}")
    for r in m["P4"]["rows"]:
        print(f"      P4 {r['id']:<26} {'ok' if r['ok'] else 'MISSED'}  "
              f"reason {r['reason'] or 'none'}")
    for r in m["P9"]["rows"]:
        print(f"      P9 {'ok' if r['ok'] else 'MISSED'}  {r['question']}")
    print(f"P1  {m['P1']['passed']}/{m['P1']['of']} non-solvable questions "
          f"of composite degree carry the primitive statement")
    print(f"P2  {m['P2']['passed']}/{m['P2']['of']} solvable controls carry "
          f"no radical-free statement")
    print(f"P3  {m['P3']['passed']}/{m['P3']['of']} declared limit "
          f"(imprimitive, not solvable) silent")
    print(f"P4  {m['P4']['passed']}/{m['P4']['of']} letter questions with "
          f"the declared reason")
    if not m["P5"].get("skipped"):
        print(f"P5  soundness battery: {m['P5']['certified']} of "
              f"{m['P5']['of']} solvable polynomials certified")
        print(f"P6  reach battery: {m['P6']['certified']}/{m['P6']['of']} "
              f"certified ({m['P6']['by_degree']})")
    print(f"P7  shape tests right on {m['P7']['ok']}/{m['P7']['shapes']} "
          f"cycle types")
    print(f"P8  Lean {m['P8']}")
    print(f"P9  {m['P9']['passed']}/{m['P9']['of']} chain pendulums state "
          f"why their modes have no radical formula")
    if not m["P10"].get("skipped"):
        print(f"P10 Phase 113 report: {m['P10']['met_of']}")
    print(f"{report['met']} of {report['of']} marks met")
    return 0


def _composed_radical(args) -> int:
    """Roots with no expression in radicals through a composition
    ``g(h(x))`` (Phase 115): the marks C1-C8 of
    ``evaluation/composed_radical_cases.py``."""
    from .runtime import composed_radical_report as cr
    report = cr.composed_radical_report(battery=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    m = report["marks"]
    for key in ("C1", "C2"):
        for r in m[key]["rows"]:
            print(f"      {key} {'ok' if r['ok'] else 'MISSED'}  "
                  f"{r['question'].split(':', 1)[1].strip()}")
    for r in m["C3"]["rows"]:
        print(f"      C3 {r['id']:<28} {'ok' if r['ok'] else 'MISSED'}  "
              f"reason {r['reason'] or 'none'}")
    print(f"C1  {m['C1']['passed']}/{m['C1']['of']} compositions with a "
          f"non-solvable outer polynomial carry the composition statement")
    print(f"C2  {m['C2']['passed']}/{m['C2']['of']} solvable controls carry "
          f"no radical-free statement")
    print(f"C3  {m['C3']['passed']}/{m['C3']['of']} letter questions with "
          f"the declared reason")
    if not m["C4"].get("skipped"):
        print(f"C4  soundness battery: {m['C4']['certified']} of "
              f"{m['C4']['of']} solvable polynomials certified")
        print(f"C5  reach battery: {m['C5']['certified']}/{m['C5']['of']} "
              f"certified ({m['C5']['by_shape']})")
        print(f"C6  decompositions exact on {m['C6']['exact']}/"
              f"{m['C6']['of']} built compositions")
    print(f"C7  Lean {m['C7']}")
    if not m["C8"].get("skipped"):
        print(f"C8  Phase 114 report: {m['C8']['phase_114']}; Phase 112 "
              f"report: {m['C8']['phase_112']}")
    print(f"{report['met']} of {report['of']} marks met")
    return 0


def _meta_questions(args) -> int:
    """Questions about the GLM's own engineering, answered from the
    project's own documents (Phase 117, track M): the marks T1-T7 of
    ``evaluation/meta_question_cases.py``."""
    from .runtime import meta_report as mr
    report = mr.meta_report(mutations=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    m = report["marks"]
    for r in report["rows"]:
        print(f"      {r['index']:>3} {'ok' if r['read'] and r['fragment'] and r['gate'] else 'MISSED'}  "
              f"{r['topic']}: {r['headline'][:90]}")
    print(f"T1  {m['T1']['passed']}/{m['T1']['of']} class-M questions read by "
          f"their topic through the router and answered with the declared "
          f"fragment")
    print(f"T2  {m['T2']['passed']}/{m['T2']['of']} with every declared "
          f"quote ({m['T2']['quotes']}) and theorem ({m['T2']['theorems']}) "
          f"found at read time")
    print(f"T3  {m['T3']['passed']}/{m['T3']['of']} with exactly the "
          f"declared disputed premises ({m['T3']['disputes']})")
    mut = m["T4"]["mutations"]
    print(f"T4  {m['T4']['scripts']}/{m['T4']['of']} scripts VERIFIED; "
          + ("mutations skipped" if mut.get("skipped") else
             "mutations caught " + ", ".join(
                 f"{k} {v}/{mut['of']}" for k, v in mut["caught"].items())))
    print(f"T5  {m['T5']['passed']}/{m['T5']['of']} declared paraphrases; "
          f"held out {report['held_out']['passed']}/"
          f"{report['held_out']['of']} (missed: "
          f"{', '.join(report['held_out']['missed']) or 'none'})")
    print(f"T6  meta frames read {len(m['T6']['read_by_meta'])} of "
          f"{m['T6']['texts_checked']} other texts; {len(m['T6']['moved'])} "
          f"changed frame")
    print(f"T7  Lean file: missing {m['T7'].get('missing')}, sorry "
          f"{m['T7'].get('sorry')}")
    print(f"{report['met']} of {report['of']} marks met")
    return 0


def _explanations(args) -> int:
    """Outside questions that ask *why* (Phase 120, track E): answered
    where a register or an exact derivation decides them, the account
    refused EXPLANATION; the marks E1-E10 of
    ``evaluation/explanation_cases.py``."""
    from .runtime import explanation_report as er
    report = er.explanation_report(mutations=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    m = report["marks"]
    for r in report["rows"]:
        ok = r["read"] and r["answered"] and r["fragment"] and r["gate"]
        print(f"      {r['index']:>3} {'ok' if ok else 'MISSED'}  "
              f"{r['scope']:<8} {r['topic']}: {r['headline'][:80]}")
    print(f"E1  {m['E1']['passed']}/{m['E1']['of']} read by their topic "
          f"through the router and answered with the declared fragment")
    print(f"E2  {m['E2']['passed']}/{m['E2']['of']} with the declared scope "
          f"({m['E2']['full']} FULL, the rest refused EXPLANATION in part)")
    print(f"E3  {m['E3']['passed']}/{m['E3']['of']} naming their registers "
          f"({m['E3']['reading_a_register']} read a register)")
    mut = m["E4"]["mutations"]
    print(f"E4  {m['E4']['scripts']}/{m['E4']['of']} scripts VERIFIED; "
          + ("mutations skipped" if mut.get("skipped") else
             "mutations caught " + ", ".join(
                 f"{k} {mut['caught'][k]}/{mut['applies'][k]}"
                 for k in mut["caught"])))
    print(f"E5  {m['E5']['passed']}/{m['E5']['of']} with exactly the "
          f"declared disputed premises ({m['E5']['disputes']})")
    ho = report["held_out"]
    print(f"E6  {m['E6']['passed']}/{m['E6']['of']} declared paraphrases; "
          f"held out {ho['passed']}/{ho['of']} "
          f"({len(ho['wrong_frame'])} read by a wrong frame)")
    print(f"E7  explanation frames read {len(m['E7']['read_by_explanation'])}"
          f" of {m['E7']['texts_checked']} other texts; "
          f"{len(m['E7']['moved'])} changed frame")
    e8 = m["E8"]
    print(f"E8  nuclide register: {e8['ground_states']} ground states, "
          f"{e8['stable']} stable, peak {e8['peak']} {e8['peak_keV']} keV, "
          f"deuteron {e8['deuteron_keV']} keV; checks "
          + ", ".join(k for k, v in e8["checks"].items() if v))
    print(f"E9  Lean file: missing {m['E9'].get('missing')}, sorry "
          f"{m['E9'].get('sorry')}")
    print(f"E10 previously refused now answered: {m['E10']['answered']} of "
          f"{m['E10']['of']}")
    print(f"{report['met']} of {report['of']} marks met")
    return 0


def _primitive_degree(args) -> int:
    """Roots with no expression in radicals in a degree that is not a prime
    power, from one Frobenius element (Phase 116): the marks D1-D8 of
    ``evaluation/primitive_degree_cases.py``."""
    from .runtime import primitive_degree_report as pd
    report = pd.primitive_degree_report(battery=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    m = report["marks"]
    for key in ("D1", "D2"):
        for r in m[key]["rows"]:
            print(f"      {key} {'ok' if r['ok'] else 'MISSED'}  "
                  f"{r['question'].split(':', 1)[1].strip()}")
    print(f"D1  {m['D1']['passed']}/{m['D1']['of']} declared sextics (groups "
          f"PGL(2,5), PSL(2,5)) carry the new statement")
    print(f"D2  {m['D2']['passed']}/{m['D2']['of']} solvable controls carry "
          f"no radical-free statement")
    groups = m["D3"]["groups"]
    print("D3  " + "; ".join(
        f"{name}: order {g['order']}, transitive {g['transitive']}, (5, 1) "
        f"element {g['long_cycle']}, Jordan elements {len(g['jordan'])}"
        for name, g in groups.items()) +
        f"; Phase 114 silent on {m['D3']['phase_114_silent']} declared")
    if not m["D4"].get("skipped"):
        print(f"D4  soundness battery: {m['D4']['certified']} of "
              f"{m['D4']['of']} solvable polynomials certified")
        print(f"D5  reach battery: {m['D5']['certified']}/{m['D5']['of']} "
              f"Cayley sextics certified, {m['D5']['by_phase_114']} by "
              f"Phase 114")
        print(f"D6  degree gate: {m['D6']['range']}; fired on "
              f"{m['D6']['fired']} of {m['D6']['prime_power_degree_polys']} "
              f"polynomials of degree 8 or 9")
    print(f"D7  Lean {m['D7']}")
    if not m["D8"].get("skipped"):
        print(f"D8  Phase 115 report: {m['D8']['phase_115']}")
    print(f"{report['met']} of {report['of']} marks met")
    return 0


def _cubic_radical(args) -> int:
    """Cubics, nested square roots and the positive-root dual track
    (Phase 104): the marks K1-K9 declared in
    ``evaluation/cubic_radical_cases.py`` before any code."""
    from .runtime import cubic_radical_report as cr
    report = cr.cubic_radical_report(run_scripts=not args.no_scripts,
                                     battery=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for key in ("K1", "K2", "K5"):
        for r in report[key]["rows"]:
            print(f"      {key} {r.get('id', '?'):<26} "
                  f"{'ok' if r.get('ok', r.get('passed')) else 'MISSED'}"
                  f"{'' if r.get('gate', True) else '  GATE FAILED'}")
    k = report
    print(f"K1  {k['K1']['passed']}/{k['K1']['of']} algebraic systems with "
          f"exactly the declared branches")
    print(f"K2  {k['K2']['passed']}/{k['K2']['of']} radical systems with "
          f"exactly the declared branches")
    print(f"K3  {k['K3']['passed']}/{k['K3']['of']} refusals by the declared "
          f"code")
    if not k["K4"].get("skipped"):
        print(f"K4  {k['K4']['verified']}/{k['K4']['answered']} scripts "
              f"verify, {k['K4']['mutants_rejected']}/{k['K4']['answered']} "
              f"mutants rejected")
    print(f"K5  {k['K5']['passed']}/{k['K5']['of']} dual-track questions")
    k6 = k["K6"]
    print(f"K6  Phase 103 mode: systems {k6['phase103_systems']}, refusals "
          f"{k6['phase103_refusals']}; branch sets kept "
          f"{k6['phase103_branch_sets_kept']}; Phase 98 questions "
          f"{k6['phase98_same']}/{k6['phase98_questions']} the same, "
          f"{k6['phase98_moved_by_convention']} moved by the convention, "
          f"{k6['phase98_moved_otherwise']} moved otherwise")
    if not k["K7"].get("skipped"):
        for seed in sorted(x for x in k["K7"] if x != "met"):
            b = k["K7"][seed]
            print(f"K7  battery {seed}: {b['answered']}/{b['systems']} "
                  f"answered, planted point in {b['planted']}, {b['wrong']} "
                  f"wrong; independent count agrees {b['independent_agree']}, "
                  f"disagrees {b['independent_disagree']}")
    if not k["K8"].get("skipped"):
        print(f"K8  {k['K8']['passed']}/{k['K8']['of']} cubics "
              f"({k['K8']['three']} with three real roots)")
    print(f"K9  Lean {k['K9']}")
    if args.explore:
        ex = cr.exploration()
        print(f"post hoc: {ex['hard_answered']}/{len(ex['hard'])} harder "
              f"systems answered, {ex['hard_verified']} verified, "
              f"{ex['hard_mutants_rejected']} mutants rejected")
        rnd = ex["random"]
        print(f"post hoc: {rnd['pairs']} random conic pairs (seed "
              f"{rnd['seed']}): {rnd['readings']}; gate failures "
              f"{rnd['gate_failed']}; independent count agrees "
              f"{rnd['independent_agree']}, disagrees "
              f"{rnd['independent_disagree']}, undecided "
              f"{rnd['independent_undecided']}")
    for key, ok in report["marks"].items():
        print(f"{key:<4} mark "
              f"{'met' if ok else ('skipped' if ok is None else 'not met')}")
    return 0


def _symbolic(args) -> int:
    """Symbolic parameters (Phase 98): the marks S1-S8 declared in
    ``studies/SYMBOLIC_PARAMETERS_STUDY.md`` before any code."""
    from .runtime import symbolic_report as sr
    report = sr.symbolic_report(run_scripts=not args.no_scripts,
                                regression=not args.quick)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    s1 = report["S1"]
    print(f"S1  class-S outside questions {s1['correct']}/{s1['of']} "
          f"answered and verified, {s1['wrong']} wrong")
    for r in s1["rows"]:
        print(f"      O{r['index']:03d} {str(r['frame']):<20} "
              f"{'ok' if r['answered'] and r['gate'] and r['fragment'] else '--'}"
              f"  {r['headline'][:90]}")
    for key in ("S2", "S3", "S4"):
        print(f"{key}  {report[key]['passed']}/{report[key]['of']} as declared")
    s5 = report["S5"]
    if not s5.get("skipped"):
        print(f"S5  mutants rejected {s5['rejected']}/{s5['mutants']}")
    s6 = report["S6"]
    if not s6.get("skipped"):
        print(f"S6  framed outside {s6['framed_ok']}/{s6['framed_of']}, "
              f"Set B {s6['set_b_audited_plus']}/{s6['set_b_of']}, new frames "
              f"read {len(s6['new_frame_reads']['read_by_new'])} of "
              f"{s6['new_frame_reads']['texts']} earlier texts; outside "
              f"classes {s6['outside_classes']}")
    s7 = report["S7"]
    print(f"S7  {s7['headline']}")
    print(f"S8  Lean {report['S8']}")
    for key, ok in report["marks"].items():
        print(f"{key:<4} mark {'met' if ok else ('skipped' if ok is None else 'not met')}")
    if args.battery:
        b = sr.random_battery(run_scripts=not args.no_scripts)
        print(f"battery (post hoc, not a mark): {b['systems']} random linear "
              f"systems, {b['nonsingular']} nonsingular, {b['answered']} "
              f"answered, {b['answered_verified']} verified, "
              f"{b['answered_singular']} singular answered, "
              f"{b['refused_nonsingular']} nonsingular refused; refusals "
              f"{b['refusal_codes']}")
    return 0


def _unpacking(args) -> int:
    """Argument unpacking and the third view on demand (Phase 97): the marks
    U1-U5 and R1-R7 declared in ``studies/UNPACKING_RESCORE_STUDY.md``
    before any code."""
    from .runtime import unpacking_report as ur
    report = ur.unpacking_report(full=not args.quick,
                                 run_scripts=not args.no_scripts)
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    u1 = report["U1"]
    print(f"U1  re-scored {u1['case']['id']}: answered "
          f"{u1['case']['answered']}  equal {u1['case'].get('equal')}  "
          f"Phase 96 cases {u1['phase96_cases']}/6  refusals "
          f"{u1['phase96_refusals']}/3")
    for key in ("U2", "U3", "U4"):
        print(f"{key}  {report[key]['passed']}/{report[key]['of']} as declared")
    u5 = report["U5"]
    print(f"U5  earlier programs {u5['programs']}  moved {u5['moved']}  "
          f"moved as declared {u5['moved_as_declared']}  battery unchanged "
          f"{u5['battery'] == u5['battery_before']}")
    b = report["before"]
    print(f"    before the round: {b['answered_before']}/{b['programs']} "
          f"answered, refusals {b['refusals_before']}")
    r1, r2, r3 = report["R1"], report["R2"], report["R3"]
    print(f"R1  on demand: reads {r1['reads']}  same as three views "
          f"{r1['same_as_three']}  third view read {r1['third_reads']}  "
          f"views read {r1['views_read']} (three views: {3 * r1['reads']})")
    print(f"R2  weight <= 3: right {r2['right']}/{r2['reads']}  third view "
          f"read {r2['third_reads']}")
    print(f"R3  weight 5: wrong {r3['wrong']}  contradicted "
          f"{r3['contradicted']} of {r3['reads']}  same as two views "
          f"{r3['same_as_two']}")
    r4, r5, r6 = report["R4"], report["R5"], report["R6"]
    print(f"R4  independent, two views: reads {r4['reads']}  resolved "
          f"{r4['resolved']}  open {r4['open']}  wrong {r4['wrong']}  live "
          f"count off prediction {r4['mismatched']}")
    print(f"R5  independent, three views: reads {r5['reads']}  resolved "
          f"{r5['resolved']}  wrong {r5['wrong']}  off prediction "
          f"{r5['mismatched']}")
    print(f"R6  independent, on demand: same as three {r6['same_as_three']}"
          f"/{r6['reads']}  third view read {r6['third_reads']}")
    r7 = report["R7"]
    print(f"R7  {r7['first_errors']} first errors x {r7['frames']} frames: "
          f"open second errors {sorted({c for r in r7['rows'] for c in r['counts']})}"
          f" (declared {r7['declared']})")
    for key, ok in report["marks"].items():
        print(f"{key:<4} mark {'met' if ok else 'not met'}")
    return 0


def _cognition(args) -> int:
    """The substrate-native cognition experiments X1-X9 and Y1-Y5, each
    against its declared pass mark."""
    from .reasoning import substrate_cognition as sc
    if getattr(args, "contract", False):
        print(json.dumps(sc.planner_default_experiment(), indent=1,
                         sort_keys=True, default=str))
        return 0
    report = sc.cognition_report()
    if args.json:
        print(json.dumps(report, indent=1, sort_keys=True, default=str))
        return 0
    for key, run in report["experiments"].items():
        mark = "met" if run["passed"] else "not met"
        print(f"{key}  pass mark {mark:<8} faculty {run['faculty']:<8} "
              f"{run['pass_mark']}")
    print(f"moved: {report['moved']}")
    print(f"met but not wired: {report['met_but_unwired']}")
    return 0


# ---------------------------------------------------------------------------
#  plans
# ---------------------------------------------------------------------------

def _plans(args) -> int:
    """The typed planner on the probe and the held-out sets, both paths."""
    from .reasoning import typed_plans as tp
    if args.write:
        path = tp.write_measurements()
        print(f"wrote {path}")
        print(f"digest {tp.module_digest()}")
        return 0
    condition = tp.state()
    report = tp.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    if args.json:
        print(json.dumps({k: report[k] for k in (
            "tallies", "frozen_probe", "frozen_probe_bare", "probe_passed",
            "held_planned", "held_bare", "census", "gains",
            "stress_first_run", "wrong_total")}, indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    probe = report["frozen_probe"]
    print(f"frozen probe      {probe['correct']} correct, {probe['wrong']} "
          f"wrong, {probe['refused']} refused -- passed "
          f"{report['probe_passed']}")
    print("set                 path      correct wrong refused right-refusal")
    for name in report["sets"]:
        for path in ("bare", "planned"):
            t = report["tallies"][name][path]
            print(f"  {name:<18} {path:<8} {t['correct']:>7} {t['wrong']:>5} "
                  f"{t['refused']:>7} {t['correct-refusal']:>13}")
    print(f"gains             {report['gains']}")
    print(f"census            {report['census']}")
    print(report["verdict"])
    print(report["caveat"])
    return 0


# ---------------------------------------------------------------------------
#  scales
# ---------------------------------------------------------------------------

def _scales(args) -> int:
    """The declared conversion table: what it relates, and what it leaves
    refused."""
    from .reasoning import scale_conversion as sc
    report = sc.conversion_report()
    census = report["census"]
    if args.json:
        print(json.dumps(
            {"declared_rows": report["declared_rows"],
             "quantities": report["quantities"],
             "non_unit_factors": report["non_unit_factors"],
             "offsets": report["offsets"],
             "declared": report["declared"],
             "answered": report["answered"],
             "refused": report["refused"],
             "as_declared": report["as_declared"],
             "scales": census["scales"], "pairs": census["pairs"],
             "bridged": census["bridged"], "still_refused": census["refused"],
             "ordering_as_declared": report["ordering_as_declared"],
             "extremum_as_declared": report["extremum_as_declared"]},
            indent=1, sort_keys=True))
        return 0
    print(f"declared rows         {report['declared_rows']} over "
          f"{report['quantities']} quantities "
          f"({', '.join(report['quantity_names'])})")
    print(f"factors / offsets     {report['non_unit_factors']} rows carry a "
          f"factor other than 1; {report['offsets']} carry an offset")
    print(f"declared questions    {report['declared']}")
    print(f"answered / refused    {report['answered']} / {report['refused']}")
    print(f"as declared           {report['as_declared']} of "
          f"{report['declared']}")
    print(f"census                {census['bridged']} of {census['pairs']} "
          f"pairs of the {census['scales']} numeric scales are comparable; "
          f"{census['refused']} stay refused")
    print(f"unchanged underneath  ordering "
          f"{report['ordering_as_declared']} of "
          f"{report['ordering_declared']}, extremum "
          f"{report['extremum_as_declared']} of "
          f"{report['extremum_declared']}")
    print("question                 outcome            as declared")
    for row in report["rows"]:
        print(f"  {row['key']:<24} {str(row['outcome']):<18} "
              f"{'yes' if row['as_declared'] else 'NO'}")
    print(report["caveat"])
    return 0


# ---------------------------------------------------------------------------
#  queryesc
# ---------------------------------------------------------------------------

def _queryesc(args: argparse.Namespace) -> int:
    """The escalation loop: what it costs, and what it buys."""
    if args.write:
        path = qesc.write_measurements()
        print(f"wrote {path}")
        print(f"digest {qesc.module_digest()}")
        return 0
    condition = qesc.state()
    report = qesc.current()
    if report is None:
        print(f"cache             {condition['verdict']}")
        print("nothing is reported from a cache that does not describe the "
              "sources; re-take it with --write")
        return 1
    safety = report["safety"]
    utility = report["utility"]
    if args.json:
        print(json.dumps({"cache": condition["verdict"],
                          "safety_holds": safety["holds"],
                          "cases": safety["cases"],
                          "answered_directly": safety["answered_directly"],
                          "probes": utility["probes"],
                          "resolved_above_the_first_rung":
                              list(utility["resolved_above_the_first_rung"]),
                          "certified_absences":
                              list(utility["certified_absences"])},
                         indent=1, sort_keys=True))
        return 0
    print(f"cache             {condition['verdict']}")
    print(f"gate 1 (safety)   {safety['holds']} over {safety['cases']} cases")
    print(f"gate 2 (utility)  {utility['has_an_instance']}, "
          f"{len(utility['resolved_above_the_first_rung'])} of "
          f"{utility['probes']} probes resolve above the first rung")
    for row in report["probes"]:
        outcome = (f"answered at {row['layer']}" if row["answered"]
                   else f"refused at {row['layer']}")
        print(f"  {row['query']:<44} {outcome:<20} cost {row['cost']}")
    return 0



# ---------------------------------------------------------------------------
#  review sweep
# ---------------------------------------------------------------------------

def _review(args: argparse.Namespace) -> int:
    """The register of stalled results, ranked before any is re-read."""
    report = rvs.review_sweep_report()
    if args.json:
        print(json.dumps({
            "entries": [{"key": row["key"], "verdict": row["verdict"],
                         "supported": row["supported"],
                         "document": row["document"]}
                        for row in report["entries"]],
            "recoverable": list(report["recoverable"]),
            "defects": list(report["defects"]),
            "holds": report["holds"],
        }, indent=1, sort_keys=True))
        return 0 if report["holds"] else 1
    print(f"entries           {report['count']}")
    for row in report["entries"]:
        mark = "" if row["supported"] else "  (unsupported claim)"
        print(f"  {row['key']:<26} {row['verdict']:<16}{mark}")
        print(f"    read at       {row['reading']}")
        print(f"    next          {row['next_step']}")
    print(f"re-reading        licensed for "
          f"{', '.join(report['recoverable']) or 'nothing'}")
    for defect in report["defects"]:
        print(f"  DEFECT {defect}")
    print(f"register holds    {report['holds']}")
    return 0 if report["holds"] else 1

# ---------------------------------------------------------------------------
#  planner
# ---------------------------------------------------------------------------

def _planner(args: argparse.Namespace) -> int:
    """The reverse-call planner, in the sandbox: what it answers and refuses."""
    from .sandbox import planner as pl
    report = pl.planner_report()
    promotion = report["promotion"]
    fallback = report["fallback"]
    if args.json:
        print(json.dumps({"tools": len(report["tools"]),
                          "budget": report["budget"],
                          "tasks": len(report["tasks"]),
                          "answered": report["answered"],
                          "verified": report["verified"],
                          "beyond_the_runtime":
                              list(report["answered_beyond_the_runtime"]),
                          "fallback_safety": fallback["safety_holds"],
                          "fallback_utility": fallback["utility_holds"],
                          "ready": promotion["ready"]},
                         indent=1, sort_keys=True))
        return 0
    print(f"tools             {len(report['tools'])}, "
          f"budget {report['budget']}")
    for row in report["tasks"]:
        state = (f"answered by {row['tool']}" if row["answered"]
                 else f"refused ({row['refusal_tag']})")
        print(f"  {row['task']:<38} {state:<34} cost {row['cost']:>2} "
              f"checked {row['verified']}")
    print(f"answered          {report['answered']} of "
          f"{len(report['tasks'])}, {report['verified']} checked, "
          f"{len(report['answered_beyond_the_runtime'])} beyond the runtime")
    print(f"fallback          {fallback['cases']} evaluation cases, "
          f"{fallback['planner_consulted']} offered, "
          f"{len(fallback['gained'])} gained")
    print(f"  safety gate     {fallback['safety_holds']}")
    print(f"  utility gate    {fallback['utility_holds']}")
    for name, value in promotion["checks"].items():
        print(f"  {name:<46} {value}")
    print(f"ready to promote  {promotion['ready']}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m glm_universal.tools",
        description="Study instruments of the GLM overlay.")
    sub = parser.add_subparsers(dest="command")

    address = sub.add_parser(
        "lean-address", help="Leech addresses for the Lean declarations")
    address.add_argument("--write", action="store_true",
                         help="recompute and store the address book")
    address.add_argument("--speak", metavar="NAME",
                         help="say one declaration's address in words")
    address.add_argument("--json", action="store_true")
    address.set_defaults(handler=_lean_address)

    board = sub.add_parser("pipeline", help="study to test to implemented")
    board.add_argument("--commands", action="store_true",
                       help="also print the column-3 verification commands")
    board.add_argument("--json", action="store_true")
    board.set_defaults(handler=_pipeline)

    rules = sub.add_parser("directives", help="the project directives")
    rules.add_argument("--json", action="store_true")
    rules.set_defaults(handler=_directives)

    landscape = sub.add_parser(
        "landscape", help="the pre-registered wobble landscape study")
    landscape.add_argument("--write", action="store_true",
                           help="re-take the measurement cache")
    landscape.add_argument("--json", action="store_true")
    landscape.set_defaults(handler=_landscape)

    holes = sub.add_parser(
        "deepholes", help="the pre-registered deep-hole classifier study")
    holes.add_argument("--write", action="store_true",
                       help="re-take the measurement cache")
    holes.add_argument("--json", action="store_true")
    holes.set_defaults(handler=_deepholes)

    ladder = sub.add_parser(
        "escalation", help="the pre-registered deep-hole escalation ladder")
    ladder.add_argument("--write", action="store_true",
                        help="re-take the measurement cache")
    ladder.add_argument("--json", action="store_true")
    ladder.set_defaults(handler=_escalation)

    blind = sub.add_parser(
        "stray-blind",
        help="lattice item 10: the pairs a distance-only reading conflates")
    blind.add_argument("--write", action="store_true",
                       help="re-take the measurement cache")
    blind.add_argument("--json", action="store_true")
    blind.set_defaults(handler=_stray_blind)

    shares = sub.add_parser(
        "share-ensemble",
        help="lattice item 6: the ladder's ensembles to 30720 starts")
    shares.add_argument("--write", action="store_true",
                        help="re-take the measurement cache")
    shares.add_argument("--jobs", type=int, default=None)
    shares.set_defaults(handler=_share_ensemble)

    separation = sub.add_parser(
        "share-separation",
        help="lattice item 6: the criterion for the share-carrying rungs")
    separation.add_argument("--json", action="store_true")
    separation.set_defaults(handler=_share_separation)

    configuration = sub.add_parser(
        "configuration-reading",
        help="lattice item 6: the configuration reading for the 28-vertex pair")
    configuration.add_argument("--json", action="store_true")
    configuration.set_defaults(handler=_configuration_reading)

    four = sub.add_parser(
        "failures", help="the four failures and the spread that gates them")
    four.add_argument("--write", action="store_true",
                      help="re-take the measurement cache")
    four.add_argument("--json", action="store_true")
    four.set_defaults(handler=_failures)

    hcen = sub.add_parser(
        "hole-census", help="all 23 Niemeier types and the L5 cells")
    hcen.add_argument("--write", action="store_true",
                      help="re-take the measurement cache (long)")
    hcen.add_argument("--jobs", type=int, default=None)
    hcen.add_argument("--json", action="store_true")
    hcen.set_defaults(handler=_hole_census)

    pcen = sub.add_parser(
        "patience-census",
        help="the hole census's three uncertified centres, re-read post hoc")
    pcen.add_argument("--write", action="store_true",
                      help="re-take the measurement cache (long)")
    pcen.add_argument("--jobs", type=int, default=None)
    pcen.add_argument("--json", action="store_true")
    pcen.set_defaults(handler=_patience_census)

    prbg = sub.add_parser(
        "probe-budget",
        help="the certifying reading's stopping rule: no barren stop, a "
             "proved budget")
    prbg.add_argument("--write", action="store_true",
                      help="re-take the measurement cache (long)")
    prbg.add_argument("--jobs", type=int, default=None)
    prbg.add_argument("--json", action="store_true")
    prbg.set_defaults(handler=_probe_budget)

    opsp = sub.add_parser(
        "ops-ladder",
        help="the operations ladder and GLM-BAT: the declared battery, the "
             "marks and hypothesis H")
    opsp.add_argument("--fast", action="store_true",
                      help="skip the column-3 scripts and their mutations")
    opsp.add_argument("--agreement", action="store_true",
                      help="also run the post-hoc agreement of the two "
                           "interpreters on 300 generated programs")
    opsp.add_argument("--json", action="store_true")
    opsp.set_defaults(handler=_ops_ladder)

    inrt = sub.add_parser(
        "inert-counter",
        help="GLM-BAT's inert-variable certificate: the battery and the marks")
    inrt.add_argument("--json", action="store_true")
    inrt.set_defaults(handler=_inert_counter)

    clso = sub.add_parser(
        "counter-lasso",
        help="GLM-BAT's counter-lasso certificates: halting and "
             "non-termination past the budget; the battery and the marks")
    clso.add_argument("--json", action="store_true")
    clso.set_defaults(handler=_counter_lasso)

    cbnd = sub.add_parser(
        "constant-bound",
        help="GLM-BAT's constant bounds and repeated output: two more "
             "counter lassos; the battery and the marks")
    cbnd.add_argument("--json", action="store_true")
    cbnd.set_defaults(handler=_constant_bound)

    afo = sub.add_parser(
        "affine-output",
        help="GLM-BAT's passes that print a counter, long output in run "
             "form, and the diagnosis of a refusal; the batteries and the "
             "marks")
    afo.add_argument("--json", action="store_true")
    afo.set_defaults(handler=_affine_output)

    dsub = sub.add_parser(
        "designed-substrate",
        help="the owner's substrate study brought in: sender-tag and "
             "soft-certificate fork stages, designed alternatives, the "
             "negative-space floor; the marks")
    dsub.add_argument("--json", action="store_true")
    dsub.set_defaults(handler=_designed_substrate)

    ptag = sub.add_parser(
        "protected-tag",
        help="the sender tag with a code of its own and the carrier read: "
             "the tied battery, the seven-bit control, three flips past the "
             "radius, heavy corruption; the marks")
    ptag.add_argument("--json", action="store_true")
    ptag.set_defaults(handler=_protected_tag)

    stag = sub.add_parser(
        "shortest-tag",
        help="how many tag bits a tie needs: the proved floors, the "
             "constructions, the search on the gap; the marks")
    stag.add_argument("--moves", type=int, default=2_000_000)
    stag.add_argument("--json", action="store_true")
    stag.set_defaults(handler=_shortest_tag)

    ctwo = sub.add_parser(
        "connected-two",
        help="the second connected-machine round: the wiring census, the "
             "stream tools, the phrased and tool batteries; the marks")
    ctwo.add_argument("--json", action="store_true")
    ctwo.set_defaults(handler=_connected_two)

    tval = sub.add_parser(
        "tool-values",
        help="a tool's number composed by the stepwise planner; the "
             "convergent and best-approximation tools; the marks")
    tval.add_argument("--json", action="store_true")
    tval.add_argument("--no-scripts", action="store_true")
    tval.set_defaults(handler=_tool_values)

    tvrd = sub.add_parser(
        "tool-verdicts",
        help="a tool's yes/no answer as a planner step, conditionals and the "
             "unrolled search; the Farey certificate; the marks")
    tvrd.add_argument("--json", action="store_true")
    tvrd.add_argument("--no-scripts", action="store_true")
    tvrd.set_defaults(handler=_tool_verdicts)

    cfcl = sub.add_parser(
        "configuration-classifier",
        help="the L5 answer rule over the 44 deep-hole queries")
    cfcl.add_argument("--write", action="store_true",
                      help="re-take the measurement cache")
    cfcl.add_argument("--json", action="store_true")
    cfcl.set_defaults(handler=_configuration_classifier)

    frzp = sub.add_parser(
        "frozen-path",
        help="the lattice round's frozen-path comparison of the evaluation")
    frzp.add_argument("--write", action="store_true",
                      help="re-take the comparison (asks every case)")
    frzp.add_argument("--json", action="store_true")
    frzp.set_defaults(handler=_frozen_path)

    erun = sub.add_parser(
        "empty-rungs", help="the norm-2 and norm-256 rungs of the ladder")
    erun.add_argument("--write", action="store_true",
                      help="re-take the measurement cache")
    erun.add_argument("--json", action="store_true")
    erun.set_defaults(handler=_empty_rungs)

    n256p = sub.add_parser(
        "norm256-hex",
        help="norm 256 and the hex colour: the candidates and the shortcut")
    n256p.add_argument("--write", action="store_true",
                       help="re-take the measurement cache")
    n256p.add_argument("--json", action="store_true")
    n256p.set_defaults(handler=_norm256_hex)

    cgp = sub.add_parser(
        "cell-guard",
        help="the cell guard: ladder answers certified nearest, three sets")
    cgp.add_argument("--write", action="store_true",
                     help="re-take the measurement cache")
    cgp.add_argument("--json", action="store_true")
    cgp.set_defaults(handler=_cell_guard)

    plgp = sub.add_parser(
        "placement-guard",
        help="the placement guard: a radius read from the carriers, four sets")
    plgp.add_argument("--write", action="store_true",
                      help="re-take the measurement cache")
    plgp.add_argument("--json", action="store_true")
    plgp.set_defaults(handler=_placement_guard)

    cumul = sub.add_parser(
        "cumulativity", help="the refinement check every layer family passes")
    cumul.add_argument("--json", action="store_true")
    cumul.set_defaults(handler=_cumulativity)

    rungs = sub.add_parser(
        "ladder", help="the construction ladder and the middle-out escalation")
    rungs.add_argument("--write", action="store_true",
                       help="re-take the measurement cache")
    rungs.add_argument("--json", action="store_true")
    rungs.set_defaults(handler=_ladder)

    norms = sub.add_parser(
        "normladder",
        help="the power-of-two norm family and the escalation over it")
    norms.add_argument("--write", action="store_true",
                       help="re-take the measurement cache")
    norms.add_argument("--json", action="store_true")
    norms.set_defaults(handler=_normladder)

    ops = sub.add_parser(
        "operations", help="escalation applied to operations other than "
                           "retrieval")
    ops.add_argument("--write", action="store_true",
                     help="re-take the measurement cache")
    ops.add_argument("--json", action="store_true")
    ops.set_defaults(handler=_operations)

    second = sub.add_parser(
        "second-reading",
        help="a second reading required to agree before an operation answers")
    second.add_argument("--write", action="store_true",
                        help="re-take the measurement cache")
    second.add_argument("--json", action="store_true")
    second.set_defaults(handler=_second_reading)

    block = sub.add_parser(
        "blockers", help="what is between this system and fuller reasoning")
    block.add_argument("--write", action="store_true",
                       help="re-take the measurement cache")
    block.add_argument("--json", action="store_true")
    block.set_defaults(handler=_blockers)

    oracle = sub.add_parser(
        "oracle",
        help="the probe questions hand-translated into the query grammar")
    oracle.add_argument("--json", action="store_true")
    oracle.set_defaults(handler=_oracle)

    surface = sub.add_parser(
        "fieldsurface",
        help="what the field surface answers of the ten held and unreachable")
    surface.add_argument("--json", action="store_true")
    surface.set_defaults(handler=_fieldsurface)

    ordering = sub.add_parser(
        "ordering",
        help="one coordinate read off two rows and ordered, or refused")
    ordering.add_argument("--json", action="store_true")
    ordering.set_defaults(handler=_ordering)

    extremum = sub.add_parser(
        "extremum",
        help="one coordinate folded over every row of one table, or refused")
    extremum.add_argument("--json", action="store_true")
    extremum.set_defaults(handler=_extremum)

    engineering = sub.add_parser(
        "engineering",
        help="formula wheels, Smith chart, analogies, delta-sigma and the "
             "engineering questions")
    engineering.add_argument("--json", action="store_true")
    engineering.set_defaults(handler=_engineering)

    speech = sub.add_parser(
        "python-speech",
        help="the GLM speaking Python: exact evaluation, named refusals and "
             "Three Column payloads, against the declared pass marks")
    speech.add_argument("--json", action="store_true")
    speech.add_argument("--no-scripts", action="store_true",
                        help="skip running the column-3 scripts")
    speech.set_defaults(handler=_python_speech)

    connected = sub.add_parser(
        "connected",
        help="the connected machine: one question path to every surface, "
             "the eight unreached modules as tools, and derivation across "
             "a declared union of formula wheels")
    connected.add_argument("--json", action="store_true")
    connected.add_argument("--quick", action="store_true",
                           help="skip the union census (minutes of exact "
                                "linear algebra)")
    connected.set_defaults(handler=_connected)

    rev = sub.add_parser(
        "reverse-tct",
        help="reverse Three Column Thinking: the language column generated "
             "from the mathematics, against the declared pass marks")
    rev.add_argument("--json", action="store_true")
    rev.add_argument("--quick", action="store_true",
                     help="skip the column-3 scripts and the control")
    rev.add_argument("--two", action="store_true",
                     help="round two (Phase 68): the widened fragment, "
                          "disjunction and the planner relay")
    rev.add_argument("--three", action="store_true",
                     help="round three (Phase 69): the integer sort, with "
                          "floor quotient and remainder split into residue "
                          "cases")
    rev.set_defaults(handler=_reverse_tct)

    parity = sub.add_parser(
        "native-parity",
        help="where a standard method ties or narrowly beats a native one: "
             "the ledger, and the refined native methods against the marks")
    parity.add_argument("--json", action="store_true")
    parity.add_argument("--write", action="store_true",
                        help="re-take the measurements and store them beside "
                             "their digest")
    parity.add_argument("--live", action="store_true",
                        help="measure now instead of reading the stored "
                             "measurements")
    parity.set_defaults(handler=_native_parity)

    words = sub.add_parser(
        "native-words",
        help="word overlap computed on Golay words of the tokens, against "
             "the marks of the native-words study")
    words.add_argument("--json", action="store_true")
    words.add_argument("--write", action="store_true",
                       help="re-take the measurements and store them beside "
                            "their digest")
    words.add_argument("--live", action="store_true",
                       help="measure now instead of reading the stored "
                            "measurements")
    words.set_defaults(handler=_native_words)

    resample = sub.add_parser(
        "corpus-resample",
        help="the declared resampling of the Lean-corpus retrieval figures: "
             "every sub-corpus that drops one file and every stride offset")
    resample.add_argument("--json", action="store_true")
    resample.add_argument("--write", action="store_true",
                          help="re-take the measurements and store them "
                               "beside their digest")
    resample.add_argument("--live", action="store_true",
                          help="measure now instead of reading the stored "
                               "measurements")
    resample.set_defaults(handler=_corpus_resample)

    astx = sub.add_parser(
        "ast-index",
        help="the AST address as a retrieval key: where a structurally equal "
             "expression is computed, in the live code and the archive "
             "(Phase 105)")
    astx.add_argument("--json", action="store_true")
    astx.add_argument("--freeze", action="store_true",
                      help="take the snapshot of the two corpora (once)")
    astx.add_argument("--write", action="store_true",
                      help="re-take the measurement from the snapshot and "
                           "store it beside its digest")
    astx.add_argument("--live", action="store_true",
                      help="measure now instead of reading the stored "
                           "measurement")
    astx.add_argument("--no-scripts", action="store_true",
                      help="skip running the column-3 scripts and mutants")
    astx.add_argument("--ask", metavar="QUESTION", default=None,
                      help="ask the operation one question")
    astx.set_defaults(handler=_ast_index)

    tree = sub.add_parser(
        "document-tree",
        help="the document tree as a third native book for the documents, "
             "measured on a frozen copy of the corpus (Phase 102)")
    tree.add_argument("--json", action="store_true")
    tree.add_argument("--freeze", action="store_true",
                      help="take the snapshot of the written corpus (once)")
    tree.add_argument("--write", action="store_true",
                      help="re-take the measurement from the snapshot and "
                           "store it beside its digest")
    tree.add_argument("--live", action="store_true",
                      help="measure now instead of reading the stored "
                           "measurement")
    tree.set_defaults(handler=_document_tree)

    scope = sub.add_parser(
        "citation-scope",
        help="citations read in Lean's scope: both readers against the "
             "elaborator, the type-word repair, and the retrieval figures "
             "re-taken beside the legacy record")
    scope.add_argument("--json", action="store_true")
    scope.add_argument("--write", action="store_true",
                       help="re-take the measurement and store it beside "
                            "its digest")
    scope.add_argument("--reference", action="store_true",
                       help="re-take the elaborator's citation graph first "
                            "(needs the compiled library)")
    scope.add_argument("--live", action="store_true",
                       help="measure now instead of reading the stored "
                            "measurement")
    scope.set_defaults(handler=_citation_scope)

    dependency = sub.add_parser(
        "dependency",
        help="what a Lean result rests on: the declared dependency "
             "questions, their gates and mutations, and the refusals")
    dependency.add_argument("--json", action="store_true")
    dependency.set_defaults(handler=_dependency)

    laws = sub.add_parser(
        "law-register",
        help="the 65 retained UBP laws re-graded through the GLM, against the "
             "marks of the law-register study")
    laws.add_argument("--json", action="store_true")
    laws.add_argument("--law", default="", help="one law id: its verdict")
    laws.set_defaults(handler=_law_register)

    absorbed = sub.add_parser(
        "law-absorption",
        help="the 65 retained UBP laws, one fate each: absorbed as computed "
             "substrate facts, already GLM, retested, or retired")
    absorbed.add_argument("--json", action="store_true")
    absorbed.add_argument("--law", default="", help="one law id: its fate")
    absorbed.set_defaults(handler=_law_absorption)

    confident = sub.add_parser(
        "decoder-confidence",
        help="the probability that a decoding, a resolved fork or a second "
             "reading is the codeword sent, against the marks of the study")
    confident.add_argument("--json", action="store_true")
    confident.add_argument("--quick", action="store_true",
                           help="sample the context stage and the brute "
                                "checks")
    confident.set_defaults(handler=_decoder_confidence)

    floor = sub.add_parser(
        "confidence-floor",
        help="a grid of confidence floors hunted over the exact channel "
             "census, and the graded answer, against the marks of the study")
    floor.add_argument("--json", action="store_true")
    floor.set_defaults(handler=_confidence_floor)

    pair = sub.add_parser(
        "agree-channel",
        help="the second reading's exact channel census over every pair of "
             "reads, and agree in the confidence-floor hunt, against the "
             "marks of the study")
    pair.add_argument("--json", action="store_true")
    pair.set_defaults(handler=_agree_channel)

    soft = sub.add_parser(
        "rate-posterior",
        help="the bit-flip rate estimated from the reads: an exact posterior "
             "over a declared grid, the soft reading, and its operating "
             "characteristics, against the marks of the study")
    soft.add_argument("--json", action="store_true")
    soft.add_argument("--repairs", action="store_true",
                      help="measure the declared fixed-rate repairs instead "
                           "(Phase 86, about two minutes)")
    soft.set_defaults(handler=_rate_posterior)

    matrix = sub.add_parser(
        "contract-matrix",
        help="candidate P's two contract changes tested four ways: control, "
             "upper-credible rule, session-marginal confidence, both "
             "(Phase 89, about two minutes)")
    matrix.add_argument("--json", action="store_true")
    matrix.set_defaults(handler=_contract_matrix)

    qsb = sub.add_parser(
        "question-set-b",
        help="the two outside question sets through the router: Set B "
             "scored, Outside O1's Capability Failure Matrix, candidate P on "
             "the framed questions (Phase 89, about two minutes)")
    qsb.add_argument("--json", action="store_true")
    qsb.add_argument("--no-variants", action="store_true")
    qsb.set_defaults(handler=_question_set_b)

    triage = sub.add_parser(
        "law-triage",
        help="the 106 unresolved knowledge-base laws, one fate each under "
             "the service rule of the study")
    triage.add_argument("--json", action="store_true")
    triage.add_argument("--law", help="print one law's fate and reason")
    triage.set_defaults(handler=_law_triage)

    omega = sub.add_parser(
        "integer-decision",
        help="the complete integer decision (the Omega test) behind "
             "INTEGER_UNDECIDED, against the marks of the study")
    omega.add_argument("--json", action="store_true")
    omega.add_argument("--quick", action="store_true",
                       help="skip the declared battery (mark Z3)")
    omega.set_defaults(handler=_integer_decision)

    held = sub.add_parser(
        "held-precision",
        help="a register value's stated precision carried through a "
             "stepwise derivation, against the marks of the study")
    held.add_argument("--json", action="store_true")
    held.set_defaults(handler=_held_precision)

    steps = sub.add_parser(
        "stepwise",
        help="the stepwise planner: the planner as the executive of a "
             "chain of steps, against the marks of the stepwise study")
    steps.add_argument("--json", action="store_true")
    steps.add_argument("--no-scripts", action="store_true",
                       help="skip running the column-3 scripts (mark S5)")
    steps.set_defaults(handler=_stepwise)

    steps2 = sub.add_parser(
        "stepwise-two",
        help="the stepwise planner, round two: how many more, parity, "
             "averages, givens with units and register values in the "
             "wheels, against the marks of the round-two study")
    steps2.add_argument("--json", action="store_true")
    steps2.add_argument("--no-scripts", action="store_true",
                        help="skip running the column-3 scripts (mark T5)")
    steps2.set_defaults(handler=_stepwise_two)

    steps3 = sub.add_parser(
        "stepwise-three",
        help="the stepwise planner, round three: declared comparatives, "
             "further count nouns, tera and pico, and folds over a column, "
             "against the marks of the round-three study")
    steps3.add_argument("--json", action="store_true")
    steps3.add_argument("--no-scripts", action="store_true",
                        help="skip running the column-3 scripts (mark V6)")
    steps3.set_defaults(handler=_stepwise_three)

    steps4 = sub.add_parser(
        "stepwise-four",
        help="the stepwise planner, round four: the median, the ends and the "
             "rank of a column, bounded where it has holes, and the "
             "present-rows question, against the marks of the hole-folds "
             "study")
    steps4.add_argument("--json", action="store_true")
    steps4.add_argument("--no-scripts", action="store_true",
                        help="skip running the column-3 scripts (mark H6)")
    steps4.set_defaults(handler=_stepwise_four)

    steps5 = sub.add_parser(
        "stepwise-five",
        help="the stepwise planner, round five: fold frames generated from "
             "a declaration, and order statistics, superlatives, bounds, "
             "classes, prefixes and molecule comparatives as entries in it, "
             "against the marks of the declared-frames study")
    steps5.add_argument("--json", action="store_true")
    steps5.add_argument("--no-scripts", action="store_true",
                        help="skip running the column-3 scripts (mark D7)")
    steps5.set_defaults(handler=_stepwise_five)

    kinds = sub.add_parser(
        "measurands",
        help="kinds of quantity: special units kept to their kind, "
             "temperatures read as a level or a difference, and the SI's "
             "defining constants, against the marks of the measurands study")
    kinds.add_argument("--json", action="store_true")
    kinds.add_argument("--no-scripts", action="store_true",
                       help="skip running the column-3 scripts (mark M5)")
    kinds.set_defaults(handler=_measurands)

    mreg = sub.add_parser(
        "measurand-register",
        help="the measurand register: register values read through their "
             "measurand, conversions through a stated efficiency and the "
             "elementary charge, against the marks of the measurand-register "
             "study")
    mreg.add_argument("--json", action="store_true")
    mreg.add_argument("--no-scripts", action="store_true",
                      help="skip running the column-3 scripts (mark R6)")
    mreg.set_defaults(handler=_measurand_register)

    celsius = sub.add_parser(
        "celsius-register",
        help="the Celsius register: the ITS-90 fixed points held in degrees "
             "Celsius, the scale table's offset row and the planner reading "
             "a Celsius value as a level, against the marks of the "
             "celsius-register study")
    celsius.add_argument("--json", action="store_true")
    celsius.add_argument("--no-scripts", action="store_true",
                         help="skip running the column-3 scripts (mark C7)")
    celsius.set_defaults(handler=_celsius_register)

    loop = sub.add_parser(
        "planner-loop",
        help="the loop through the planner: derive, ask and solve as dialect "
             "values, programs whose control flow is the loop, and questions "
             "about a Python expression through a frame, against the marks "
             "of the planner-loop study")
    loop.add_argument("--json", action="store_true")
    loop.add_argument("--no-scripts", action="store_true",
                      help="skip running the column-3 scripts (mark W5)")
    loop.set_defaults(handler=_planner_loop)

    disc = sub.add_parser(
        "discourse-state",
        help="discourse state: a tie carried as a column, the fourth shape "
             "of follow-up and follow-ups bound on every surface, against "
             "the marks of the discourse-state study")
    disc.add_argument("--json", action="store_true")
    disc.add_argument("--no-census", action="store_true",
                      help="skip the shape census over the earlier corpora "
                           "(mark D8)")
    disc.set_defaults(handler=_discourse_state)

    imp = sub.add_parser(
        "imperative",
        help="the imperative grammar: programs with state (assignment, "
             "loops, branches, functions, match) in the reverse grammar, "
             "against the marks of the imperative-grammar study")
    imp.add_argument("--json", action="store_true")
    imp.add_argument("--no-scripts", action="store_true",
                     help="skip running the column-3 scripts (I6)")
    imp.set_defaults(handler=_imperative)

    third = sub.add_parser(
        "third-sort",
        help="the third sort: strings, tuples and ranges in the reverse "
             "grammar, and the dialect widened to string methods, lists and "
             "dicts, against the marks of the third-sort study")
    third.add_argument("--json", action="store_true")
    third.add_argument("--no-scripts", action="store_true",
                       help="skip running the column-3 scripts (T4, D3)")
    third.set_defaults(handler=_third_sort)

    world = sub.add_parser(
        "register-world",
        help="the register against the world: every element row against the "
             "frozen CIAAW and NIST tables, never written, and the completion "
             "gate's nested holdout, against the marks of the register-world "
             "study")
    world.add_argument("--json", action="store_true")
    world.set_defaults(handler=_register_world)

    typed = sub.add_parser(
        "typed-operators",
        help="typed operators: real, reactive and apparent power, the power "
             "factor, and the dot against the cross product, against the "
             "marks of the typed-operators study")
    typed.add_argument("--json", action="store_true")
    typed.add_argument("--no-scripts", action="store_true",
                       help="skip running the column-3 scripts (mark T6)")
    typed.add_argument("--no-route", action="store_true",
                       help="skip routing every case before and after")
    typed.set_defaults(handler=_typed_operators)

    fork = sub.add_parser(
        "carried-fork",
        help="the six deep-hole candidates carried until a later decision "
             "resolves them, against the declared pass marks")
    fork.add_argument("--json", action="store_true")
    fork.add_argument("--quick", action="store_true",
                      help="sample the hard-lift census and skip the full "
                           "Leech decoder")
    fork.set_defaults(handler=_carried_fork)

    views = sub.add_parser(
        "second-view",
        help="second readings: one carrier read through the framed "
             "register's views, against the marks of the second-view study")
    views.add_argument("--json", action="store_true")
    views.add_argument("--quick", action="store_true",
                       help="one probe codeword instead of 64; a sampled "
                            "composition and soft channel")
    views.add_argument("--no-scripts", action="store_true",
                       help="skip running the column-3 scripts (mark V8)")
    views.set_defaults(handler=_second_view)

    unpack = sub.add_parser(
        "unpacking",
        help="argument unpacking in the dialect and the framed register's "
             "third view on demand, against the marks of the unpacking study")
    unpack.add_argument("--json", action="store_true")
    unpack.add_argument("--quick", action="store_true",
                        help="one probe codeword instead of 64; two census "
                             "first errors instead of 24")
    unpack.add_argument("--no-scripts", action="store_true",
                        help="skip running the column-3 scripts")
    unpack.set_defaults(handler=_unpacking)

    nonl = sub.add_parser(
        "nonlinear",
        help="systems in letters that substitution cannot isolate: the "
             "branch layer against the marks of the nonlinear elimination "
             "study")
    nonl.add_argument("--json", action="store_true")
    nonl.add_argument("--quick", action="store_true",
                      help="skip the planted battery (E5)")
    nonl.add_argument("--no-scripts", action="store_true",
                      help="skip running the column-3 scripts and mutants")
    nonl.set_defaults(handler=_nonlinear)

    deriv = sub.add_parser(
        "derivation",
        help="derivations and proofs: propositional proof search, "
             "Euler-Lagrange, transfer functions and profiles, against the "
             "marks of the derivation study")
    deriv.add_argument("--json", action="store_true")
    deriv.add_argument("--quick", action="store_true",
                       help="a battery of 200 formulas instead of 2000")
    deriv.add_argument("--no-scripts", action="store_true",
                       help="skip running the column-3 scripts and mutants")
    deriv.set_defaults(handler=_derivation)

    deriv2 = sub.add_parser(
        "derivation-two",
        help="the rest of track P: information inequalities, codes, rate "
             "distortion, maximum entropy, eigenvalue problems, "
             "transmission, FFT and the rate posterior, against the marks "
             "of the second derivation study")
    deriv2.add_argument("--json", action="store_true")
    deriv2.add_argument("--quick", action="store_true",
                        help="batteries of 100 instead of 400 and 600")
    deriv2.add_argument("--no-scripts", action="store_true",
                        help="skip running the column-3 scripts and mutants")
    deriv2.set_defaults(handler=_derivation_two)

    deriv3 = sub.add_parser(
        "derivation-three",
        help="past the second derivation study's limits: inequalities past "
             "the Shannon cone, rate distortion past the tight range, Robin "
             "eigenvalue problems, against the marks of the third "
             "derivation study")
    deriv3.add_argument("--json", action="store_true")
    deriv3.add_argument("--quick", action="store_true",
                        help="batteries of 30, and no Phase 107 or "
                             "outside comparison")
    deriv3.set_defaults(handler=_derivation_three)

    deriv4 = sub.add_parser(
        "derivation-four",
        help="past the third derivation study's limits: chained copies and "
             "five-variable inequalities, rate distortion for any distortion "
             "matrix, Robin problems at both ends and with a symbolic "
             "coefficient, against the marks of the fourth derivation study")
    deriv4.add_argument("--json", action="store_true")
    deriv4.add_argument("--quick", action="store_true",
                        help="batteries of 10, and no Phase 118 or "
                             "outside comparison")
    deriv4.set_defaults(handler=_derivation_four)

    cubr = sub.add_parser(
        "cubic-radical",
        help="cubics, nested square roots and the positive-root dual track: "
             "the branch layer against the marks of the cubic radical study")
    cubr.add_argument("--json", action="store_true")
    cubr.add_argument("--quick", action="store_true",
                      help="skip the batteries (K7, K8)")
    cubr.add_argument("--explore", action="store_true",
                      help="also run the post hoc exploration (harder "
                           "systems, random conic pairs)")
    cubr.add_argument("--no-scripts", action="store_true",
                      help="skip running the column-3 scripts and mutants")
    cubr.set_defaults(handler=_cubic_radical)

    quir = sub.add_parser(
        "quintic-radical",
        help="factoring past degree 6 and roots with no expression in "
             "radicals: the branch layer against the marks of the quintic "
             "radical study")
    quir.add_argument("--json", action="store_true")
    quir.add_argument("--quick", action="store_true",
                      help="skip the batteries (R5, R6)")
    quir.add_argument("--no-scripts", action="store_true",
                      help="skip running the column-3 scripts")
    quir.set_defaults(handler=_quintic_radical)

    frob = sub.add_parser(
        "frobenius-radical",
        help="roots with no expression in radicals read from one Frobenius "
             "element: the branch layer against the marks of the Frobenius "
             "radical study")
    frob.add_argument("--json", action="store_true")
    frob.add_argument("--quick", action="store_true",
                      help="skip the batteries and the Phase 112 regression "
                           "(F5-F7, F9)")
    frob.set_defaults(handler=_frobenius_radical)

    prim = sub.add_parser(
        "primitive-radical",
        help="roots with no expression in radicals in composite degree, read "
             "from two Frobenius elements, and on the modes route: the marks "
             "of the primitive radical study")
    prim.add_argument("--json", action="store_true")
    prim.add_argument("--quick", action="store_true",
                      help="skip the batteries and the Phase 113 regression "
                           "(P5, P6, P10)")
    prim.set_defaults(handler=_primitive_radical)

    comp = sub.add_parser(
        "composed-radical",
        help="roots with no expression in radicals through a composition "
             "g(h(x)): the marks of the composed radical study")
    comp.add_argument("--json", action="store_true")
    comp.add_argument("--quick", action="store_true",
                      help="skip the batteries and the Phase 114 and 112 "
                           "regressions (C4-C6, C8)")
    comp.set_defaults(handler=_composed_radical)

    metq = sub.add_parser(
        "meta-questions",
        help="questions about the GLM's own engineering (scoring, the "
             "sandbox, Lean templates, the decoding radius, ...), answered "
             "from the project's own documents: the marks of the meta "
             "questions study")
    metq.add_argument("--json", action="store_true")
    metq.add_argument("--quick", action="store_true",
                      help="skip the mutation controls of T4")
    metq.set_defaults(handler=_meta_questions)

    expl = sub.add_parser(
        "explanations",
        help="outside questions that ask why (resonance, nuclear binding, "
             "periodic trends, logic): the part a register or an exact "
             "derivation decides, the account refused EXPLANATION; the "
             "marks of the explanation anchor study")
    expl.add_argument("--json", action="store_true")
    expl.add_argument("--quick", action="store_true",
                      help="skip the mutation controls of E4")
    expl.set_defaults(handler=_explanations)

    pdeg = sub.add_parser(
        "primitive-degree",
        help="roots with no expression in radicals in a degree that is not a "
             "prime power, from one Frobenius element (Galois: a solvable "
             "primitive group has prime-power degree): the marks of the "
             "primitive degree study")
    pdeg.add_argument("--json", action="store_true")
    pdeg.add_argument("--quick", action="store_true",
                      help="skip the batteries and the Phase 115 regression "
                           "(D4-D6, D8)")
    pdeg.set_defaults(handler=_primitive_degree)

    cubt = sub.add_parser(
        "cubic-trig",
        help="a cubic in letters with three real roots: the homogeneous "
             "route and Viete's trigonometric form against the marks of the "
             "cubic trig study")
    cubt.add_argument("--json", action="store_true")
    cubt.add_argument("--quick", action="store_true",
                      help="skip the batteries, the Phase 104 re-read and "
                           "the outside texts (T5 partly, T6, T7, T9)")
    cubt.add_argument("--no-scripts", action="store_true",
                      help="skip running the column-3 scripts and mutants")
    cubt.set_defaults(handler=_cubic_trig)

    symb = sub.add_parser(
        "symbolic",
        help="formulas in letters: the solve-symbolically operation and the "
             "class-S outside frames, against the marks of the symbolic "
             "parameters study")
    symb.add_argument("--json", action="store_true")
    symb.add_argument("--quick", action="store_true",
                      help="skip the regression mark (S6)")
    symb.add_argument("--no-scripts", action="store_true",
                      help="skip running the column-3 scripts and mutants")
    symb.add_argument("--battery", action="store_true",
                      help="also run the post-hoc random linear-system "
                           "battery (evidence, not a mark)")
    symb.set_defaults(handler=_symbolic)

    cognition = sub.add_parser(
        "cognition",
        help="the substrate-native cognition experiments, each against the "
             "pass mark declared before it ran")
    cognition.add_argument("--json", action="store_true")
    cognition.add_argument("--contract", action="store_true",
                           help="Y8: the 177 contract cases through the "
                                "grammar and through the planner (minutes)")
    cognition.set_defaults(handler=_cognition)

    plans = sub.add_parser(
        "plans",
        help="the typed planner on the frozen probe and the held-out sets, "
             "against the bare grammar")
    plans.add_argument("--write", action="store_true",
                       help="re-take the measurement cache")
    plans.add_argument("--json", action="store_true")
    plans.set_defaults(handler=_plans)

    scales = sub.add_parser(
        "scales",
        help="the declared table of conversions between scales, and the "
             "refusals it removes")
    scales.add_argument("--json", action="store_true")
    scales.set_defaults(handler=_scales)

    conversation = sub.add_parser(
        "conversation",
        help="the turn that refers back to an earlier turn, bound or refused")
    conversation.add_argument("--json", action="store_true")
    conversation.set_defaults(handler=_conversation)

    binding = sub.add_parser(
        "binding",
        help="a typed relation written as one word, and how much of it comes "
             "back")
    binding.add_argument("--json", action="store_true")
    binding.set_defaults(handler=_binding)

    loop = sub.add_parser(
        "queryesc", help="escalation as a step of the query loop")
    loop.add_argument("--write", action="store_true",
                      help="re-take the measurement cache")
    loop.add_argument("--json", action="store_true")
    loop.set_defaults(handler=_queryesc)

    sweep = sub.add_parser(
        "review", help="the register of stalled results, ranked for re-reading")
    sweep.add_argument("--json", action="store_true")
    sweep.set_defaults(handler=_review)

    sandbox = sub.add_parser(
        "planner", help="the reverse-call planner, in the sandbox")
    sandbox.add_argument("--json", action="store_true")
    sandbox.set_defaults(handler=_planner)

    ledger = sub.add_parser("signoff",
                            help="what the sign-off ledger currently covers")
    ledger.add_argument("--json", action="store_true")
    ledger.set_defaults(handler=_signoff)

    return parser


def run(argv: Optional[Sequence[str]] = None) -> int:
    """Run one subcommand and return its exit code."""
    parser = _parser()
    args = parser.parse_args(argv)
    if not getattr(args, "handler", None):
        parser.print_help()
        return 2
    return args.handler(args)


def main() -> int:  # pragma: no cover - thin wrapper around :func:`run`
    return run()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

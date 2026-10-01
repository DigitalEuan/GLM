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
from .reasoning import cumulativity as cml
from .reasoning import ladder_escalation as lesc
from .reasoning import query_escalation as qesc
from .reasoning import review_sweep as rvs
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

    four = sub.add_parser(
        "failures", help="the four failures and the spread that gates them")
    four.add_argument("--write", action="store_true",
                      help="re-take the measurement cache")
    four.add_argument("--json", action="store_true")
    four.set_defaults(handler=_failures)

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

    fork = sub.add_parser(
        "carried-fork",
        help="the six deep-hole candidates carried until a later decision "
             "resolves them, against the declared pass marks")
    fork.add_argument("--json", action="store_true")
    fork.add_argument("--quick", action="store_true",
                      help="sample the hard-lift census and skip the full "
                           "Leech decoder")
    fork.set_defaults(handler=_carried_fork)

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

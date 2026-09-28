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


# ---------------------------------------------------------------------------
#  lean-mirror
# ---------------------------------------------------------------------------

def _lean_mirror(args: argparse.Namespace) -> int:
    from .signoff import mirror as mir

    report = mir.mirror_report()
    if args.write:
        outcome = mir.write_mirror(report)
        for name in outcome["written"]:
            print(f"wrote   {name}")
        for name in outcome["removed"]:
            print(f"removed {name}")
        if not outcome["written"] and not outcome["removed"]:
            print("the mirror was already the source")
        print(f"{outcome['files']} files, "
              f"{'identical' if outcome['identical'] else 'STILL DIFFERENT'}")
        return 0 if outcome["identical"] else 1
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["identical"] else 1
    print(f"source  {report['source']}")
    print(f"mirror  {report['mirror']}")
    print(f"files   {report['files']}")
    for name in report["missing"]:
        print(f"  missing from the mirror: {name}")
    for name in report["extra"]:
        print(f"  in the mirror only:      {name}")
    for name in report["differing"]:
        print(f"  differs:                 {name}")
    print("identical" if report["identical"]
          else "run with --write to generate the mirror")
    return 0 if report["identical"] else 1


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

    mirror = sub.add_parser(
        "lean-mirror",
        help="the overlay's copy of the Lean tree, generated from the "
             "repository's")
    mirror.add_argument("--write", action="store_true",
                        help="bring the mirror to the source")
    mirror.add_argument("--json", action="store_true")
    mirror.set_defaults(handler=_lean_mirror)

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

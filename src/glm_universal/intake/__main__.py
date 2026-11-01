"""``python3 -m glm_universal.intake`` -- the intake pipeline's command line.

*Created 31 October 2026 (repository check; directive D22).*

    python3 -m glm_universal.intake status
    python3 -m glm_universal.intake check
    python3 -m glm_universal.intake show cent_compiler_v12
    python3 -m glm_universal.intake register source_material/new_note.md --kind "concept note"
    python3 -m glm_universal.intake scaffold new_note
    python3 -m glm_universal.intake advance new_note tested
    python3 -m glm_universal.intake retest cent_compiler_v12 --stale
    python3 -m glm_universal.intake accept new_note --criterion "..." --result "..." --mark S1
    python3 -m glm_universal.intake provisional new_note --decision "..." --wheel W99
    python3 -m glm_universal.intake absorb-staged cent_compiler_v12
    python3 -m glm_universal.intake absorb-ahead new_note --decision "..." \
        --standalone IntakeChecks/NewNote --check "..."
    python3 -m glm_universal.intake confirm-build new_note
    python3 -m glm_universal.intake close new_note --reason "..." --evidence SOME_STUDY

``check`` exits 1 when the ledger and the folders disagree or a record claims
a stage without its evidence; ``advance``, ``provisional`` and
``absorb-staged`` exit 1 when the gate refuses.

*Last altered 31 October 2026: ``absorb-staged``; it and ``advance`` run the
named tests again where their results are not current (``--no-run`` checks
the recorded results only); ``retest`` runs an item's tests and records the
results without moving it; ``accept`` records the acceptance decision the
``measured`` gate needs; ``provisional`` installs an item's staged code ahead of
the build record by the owner's decision (parts ``provisional``, the item in
the register of provisional families), and ``absorb-staged`` also confirms
provisional parts.*
*Last altered 1 November 2026 (Phase 186): ``absorb-ahead`` (absorb an item
ahead of the build record, on its measurements and a standalone Lean check,
by the owner's decision) and ``confirm-build`` (the build record confirms
it); both exit 1 when the gate refuses.*
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import actions, gates
from .ledger import KINDS, STAGE_NAMES, STAGES, Layout, LedgerError, load, record_by_id


def _cmd_status(args: argparse.Namespace) -> int:
    if args.json:
        print(json.dumps({"rows": actions.status_rows(), "report": actions.intake_report()},
                         indent=1))
    else:
        print(actions.status_table(width=args.width))
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    result = gates.check(load())
    if args.json:
        print(json.dumps(result, indent=1))
    else:
        for e in result["errors"]:
            print("ERROR  " + e)
        if not args.quiet:
            for w in result["warnings"]:
                print("note   " + w)
        print(f"{result['items']} records; {len(result['errors'])} error(s), "
              f"{len(result['warnings'])} note(s): " + ("OK" if result["ok"] else "FAILED"))
    return 0 if result["ok"] else 1


def _cmd_show(args: argparse.Namespace) -> int:
    import yaml
    lay = Layout.default()
    rec = record_by_id(load(lay), args.id)
    print(yaml.safe_dump(rec, sort_keys=False, allow_unicode=True, width=96).rstrip())
    problems = gates.evidence_problems(rec, lay)
    print()
    print(f"stage: {STAGE_NAMES.get(rec.get('stage'), rec.get('stage'))}; "
          + ("its evidence holds" if not problems else f"{len(problems)} gap(s):"))
    for p in problems:
        print("  " + p)
    nxt, lacking = actions.next_gate(rec, lay)
    if nxt:
        print(f"next gate, {STAGE_NAMES[nxt]}: "
              + ("ready" if not lacking else "lacks " + "; ".join(lacking)))
    return 0


def _cmd_register(args: argparse.Namespace) -> int:
    copy = True if args.copy else (False if args.move else None)
    rec = actions.register(args.path, item_id=args.id, kind=args.kind, offers=args.offers,
                           copy=copy)
    print(f"registered {rec['id']} at {rec['path']} (stage received); next: {rec['next_step']}")
    return 0


def _cmd_scaffold(args: argparse.Namespace) -> int:
    md, yml = actions.scaffold(args.id, study_id=args.study)
    print(f"drafted {md}\n        {yml}")
    return 0


def _cmd_advance(args: argparse.Namespace) -> int:
    report = actions.advance(args.id, args.stage, run=not args.no_run, timeout=args.timeout)
    for r in report["ran"]:
        print(f"  {r['result']:7} {r['test']}  ({r['detail']})")
    if report["ok"]:
        print(f"{args.id}: {STAGE_NAMES[report['from']]} -> {STAGE_NAMES[report['to']]}")
        return 0
    print(f"{args.id}: the gate for {STAGE_NAMES[report['to']]} refuses:")
    for p in report["problems"]:
        print("  " + p)
    return 1


def _cmd_absorb_staged(args: argparse.Namespace) -> int:
    report = actions.absorb_staged(args.id, run=not args.no_run, timeout=args.timeout)
    for r in report["ran"]:
        print(f"  {r['result']:7} {r['test']}  ({r['detail']})")
    if report["ok"]:
        print(f"{args.id}: staged and provisional parts absorbed; "
              f"{len(report['installed'])} file(s) installed")
        for rel in report["installed"]:
            print("  " + rel)
        return 0
    print(f"{args.id}: the gate for the staged and provisional parts refuses:")
    for p in report["problems"]:
        print("  " + p)
    return 1


def _cmd_provisional(args: argparse.Namespace) -> int:
    report = actions.provisional(args.id, args.decision, wheels=args.wheel or (),
                                 run=not args.no_run, timeout=args.timeout)
    for r in report["ran"]:
        print(f"  {r['result']:7} {r['test']}  ({r['detail']})")
    if report["ok"]:
        print(f"{args.id}: installed provisionally; {len(report['installed'])} file(s)")
        for rel in report["installed"]:
            print("  " + rel)
        return 0
    print(f"{args.id}: the provisional install refuses:")
    for p in report["problems"]:
        print("  " + p)
    return 1


def _cmd_absorb_ahead(args: argparse.Namespace) -> int:
    report = actions.absorb_ahead(args.id, args.decision, args.standalone or (), args.check,
                                  wheels=args.wheel or (), run=not args.no_run,
                                  timeout=args.timeout)
    for r in report["ran"]:
        print(f"  {r['result']:7} {r['test']}  ({r['detail']})")
    if report["ok"]:
        where = ("its staged and provisional parts; its open parts stay in ToDo/"
                 if report.get("partial") else "filed in done/")
        print(f"{args.id}: absorbed ahead of the build ({where}); "
              f"{len(report['installed'])} file(s) installed; the owner's "
              f"scripts/rebuild_lean.sh still has to confirm it (`confirm-build {args.id}`)")
        for rel in report["installed"]:
            print("  " + rel)
        return 0
    print(f"{args.id}: the absorption ahead of the build refuses:")
    for p in report["problems"]:
        print("  " + p)
    return 1


def _cmd_confirm_build(args: argparse.Namespace) -> int:
    report = actions.confirm_build(args.id)
    if report["ok"]:
        print(f"{args.id}: the build record confirms its Lean files; absorption confirmed")
        return 0
    print(f"{args.id}: the build record does not confirm it yet:")
    for p in report["problems"]:
        print("  " + p)
    return 1


def _cmd_retest(args: argparse.Namespace) -> int:
    report = actions.retest(args.id, only_stale=args.stale, timeout=args.timeout)
    for r in report["ran"]:
        print(f"  {r['result']:7} {r['test']}  ({r['detail']})")
    if not report["ran"]:
        print(f"{args.id}: every named test has a current pass; nothing to run")
        return 0
    failed = [r for r in report["ran"] if r["result"] != "pass"]
    print(f"{args.id}: {len(report['ran']) - len(failed)} of {len(report['ran'])} passed; "
          "results recorded")
    return 1 if failed else 0


def _cmd_accept(args: argparse.Namespace) -> int:
    rec = actions.accept(args.id, args.criterion, args.result, study=args.study,
                         marks=args.mark or ())
    acc = rec["acceptance"]
    print(f"{rec['id']}: acceptance recorded against {acc['study']} "
          f"(marks: {', '.join(acc['marks']) or 'none declared'}); next: "
          f"`advance {rec['id']} measured` once the earlier gates hold")
    return 0


def _cmd_close(args: argparse.Namespace) -> int:
    rec = actions.close(args.id, args.reason, args.evidence,
                        close_open_parts=args.close_open_parts)
    print(f"closed {rec['id']}; filed at {rec['path']}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python3 -m glm_universal.intake",
        description="The intake pipeline (directive D22): supplied material enters "
                    "source_material/ToDo/ and is absorbed only through its gates.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("status", help="the table of items and their stages")
    p.add_argument("--json", action="store_true")
    p.add_argument("--width", type=int, default=60, help="width of the next-step column")
    p.set_defaults(fn=_cmd_status)

    p = sub.add_parser("check", help="ledger <-> folders, and every stage's evidence")
    p.add_argument("--json", action="store_true")
    p.add_argument("--quiet", action="store_true", help="errors only")
    p.set_defaults(fn=_cmd_check)

    p = sub.add_parser("show", help="one record, its gaps and its next gate")
    p.add_argument("id")
    p.set_defaults(fn=_cmd_show)

    p = sub.add_parser("register", help="a new item -> ToDo/ and a ledger stub")
    p.add_argument("path")
    p.add_argument("--id")
    p.add_argument("--kind", choices=KINDS)
    p.add_argument("--offers", help="what the item claims or offers")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--copy", action="store_true", help="copy even a loose item")
    g.add_argument("--move", action="store_true", help="move even an outside item")
    p.set_defaults(fn=_cmd_register)

    p = sub.add_parser("scaffold", help="draft studies/<ID>_STUDY.md + .yaml for an item")
    p.add_argument("id")
    p.add_argument("--study", help="the study id (default <ID>_STUDY)")
    p.set_defaults(fn=_cmd_scaffold)

    p = sub.add_parser("advance", help="move an item on, after its gate passes")
    p.add_argument("id")
    p.add_argument("stage", help="one of: " + ", ".join(STAGES))
    p.add_argument("--no-run", action="store_true",
                   help="check the recorded evidence only; run no test and no lean_check")
    p.add_argument("--timeout", type=int, default=1800, help="seconds per test")
    p.set_defaults(fn=_cmd_advance)

    p = sub.add_parser("provisional",
                       help="install an item's staged code ahead of the build record, by "
                            "the owner's decision (marked provisional until absorbed)")
    p.add_argument("id")
    p.add_argument("--decision", required=True, help="the owner's decision, in the owner's words")
    p.add_argument("--wheel", action="append",
                   help="a wheel id an answer may name (repeatable)")
    p.add_argument("--no-run", action="store_true",
                   help="run no test; the recorded results must already be current")
    p.add_argument("--timeout", type=int, default=1800, help="seconds per test")
    p.set_defaults(fn=_cmd_provisional)

    p = sub.add_parser("absorb-staged",
                       help="absorb an item's staged and provisional parts (build record "
                            "needed); its open parts stay open")
    p.add_argument("id")
    p.add_argument("--no-run", action="store_true",
                   help="run no test; the recorded results must already be current")
    p.add_argument("--timeout", type=int, default=1800, help="seconds per test")
    p.set_defaults(fn=_cmd_absorb_staged)

    p = sub.add_parser("absorb-ahead",
                       help="absorb an item ahead of the build record, on its measurements and "
                            "a standalone Lean check, by the owner's decision")
    p.add_argument("id")
    p.add_argument("--decision", required=True, help="the owner's decision, in the owner's words")
    p.add_argument("--standalone", action="append", required=True,
                   help="a Lean file of the item checked on its own (repeatable)")
    p.add_argument("--check", required=True, help="how the standalone Lean check was made")
    p.add_argument("--wheel", action="append",
                   help="a wheel id an answer may name (repeatable)")
    p.add_argument("--no-run", action="store_true",
                   help="run no test; the recorded results must already be current")
    p.add_argument("--timeout", type=int, default=1800, help="seconds per test")
    p.set_defaults(fn=_cmd_absorb_ahead)

    p = sub.add_parser("confirm-build",
                       help="the build record confirms an item absorbed ahead of the build")
    p.add_argument("id")
    p.set_defaults(fn=_cmd_confirm_build)

    p = sub.add_parser("retest", help="run an item's named tests and record the results "
                                      "(the stage does not move)")
    p.add_argument("id")
    p.add_argument("--stale", action="store_true",
                   help="only the tests whose last result is not a current pass")
    p.add_argument("--timeout", type=int, default=1800, help="seconds per test")
    p.set_defaults(fn=_cmd_retest)

    p = sub.add_parser("accept", help="record the acceptance decision the measured gate needs")
    p.add_argument("id")
    p.add_argument("--criterion", required=True,
                   help="the criterion the study declared, quoted from it")
    p.add_argument("--result", required=True, help="the measured result, quoted from the study")
    p.add_argument("--mark", action="append",
                   help="a met mark that carries the help (repeatable; required when the "
                        "study declares marks)")
    p.add_argument("--study", help="the measured study (default: the one `measured` names)")
    p.set_defaults(fn=_cmd_accept)

    p = sub.add_parser("close", help="finish without absorption; filed in done/")
    p.add_argument("id")
    p.add_argument("--reason", required=True)
    p.add_argument("--evidence", action="append", required=True,
                   help="a study id or repository path (repeatable)")
    p.add_argument("--close-open-parts", action="store_true")
    p.set_defaults(fn=_cmd_close)

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except LedgerError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

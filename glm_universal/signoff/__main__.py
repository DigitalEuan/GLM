"""Command line for the sign-off ledger.

::

    PYTHONPATH=. python3 -m glm_universal.signoff --plan
    PYTHONPATH=. python3 -m glm_universal.signoff --run
    PYTHONPATH=. python3 -m glm_universal.signoff --only-stale --jobs 8
    PYTHONPATH=. python3 -m glm_universal.signoff --run-all
    PYTHONPATH=. python3 -m glm_universal.signoff --run-checks
    PYTHONPATH=. python3 -m glm_universal.signoff --run-checks-all
    PYTHONPATH=. python3 -m glm_universal.signoff --run-everything
    PYTHONPATH=. python3 -m glm_universal.signoff --release
    PYTHONPATH=. python3 -m glm_universal.signoff --verify
    PYTHONPATH=. python3 -m glm_universal.signoff --verify-release
    PYTHONPATH=. python3 -m glm_universal.signoff --closure test_wobble.py

``--run`` (equivalently ``--only-stale``) runs the stale *test files*;
``--run-checks`` runs the stale *instruments* (``lake build``, the evaluation,
the benchmarks, the probes, the figures check); ``--run-everything`` runs both.
The ``-all`` forms ignore the ledger, and ``--release`` is the round-close
check: every test file and every instrument, with the exhaustive cases on.

``--jobs N`` runs N units at once (default: one per core, capped at eight).
``--exhaustive`` turns the opt-in cases on for a run that is not ``--release``;
they are on automatically for any ``-all`` form.

A routine run signs a unit in ``fast`` mode.  ``--verify-release`` asks the
stricter question -- is every unit signed off *with the exhaustive cases run* --
and reports anything only signed fast as ``partial``.

Exit codes: ``0`` everything asked for succeeded, ``1`` a test failed or a
signature did not hold, ``2`` the arguments were not understood.
"""

from __future__ import annotations

import sys
from fractions import Fraction
from typing import Optional, Sequence

from . import checks as C
from . import ledger as L


def _seconds(value: Fraction) -> str:
    """An exact rational of seconds, to one decimal, without a float (D7)."""
    tenths = (value * 10).__round__()
    return f"{tenths // 10}.{tenths % 10}s"


def _percent(value: Fraction) -> str:
    """An exact rational of a whole, as a whole percentage, without a float."""
    return f"{(value * 100).__round__()}"


def _jobs(argv: Sequence[str]) -> int:
    """``--jobs N``, or one per core capped at eight."""
    if "--jobs" in argv:
        index = list(argv).index("--jobs")
        if index + 1 < len(argv):
            try:
                return max(1, int(argv[index + 1]))
            except ValueError:
                pass
    return L.DEFAULT_JOBS


def _print_plan(full: bool = False) -> int:
    rows = L.plan(full=full)
    saving = L.predicted_saving(rows)
    check_rows = C.check_plan()
    check_saving = C.predicted_check_saving(check_rows)
    width = max([len(u.name) for u in rows]
                + [len(u.name) for u in check_rows] + [10])

    print("test files")
    for unit in rows:
        mark = "signed" if not unit.stale else unit.state
        last = unit.last_seconds
        timing = _seconds(last) if last is not None else "  -  "
        print(f"  {unit.name:<{width}}  {mark:<8} {timing:>8}")
    print(f"  {saving['signed']} of {saving['units']} units signed off; "
          f"{saving['stale']} to run")
    print(f"  expected: {_seconds(saving['seconds_to_run'])} instead of "
          f"{_seconds(saving['seconds_full_run'])} "
          f"({_percent(saving['fraction_saved'])}% saved)")
    if saving["units_without_timing"]:
        print(f"  no recorded timing for: "
              f"{', '.join(saving['units_without_timing'])}")

    print()
    print("other instruments")
    for unit in check_rows:
        mark = "signed" if not unit.stale else unit.state
        last = unit.last_seconds
        timing = (_seconds(last) if last is not None
                  else f"~{unit.check.expected_seconds}s")
        print(f"  {unit.name:<{width}}  {mark:<8} {timing:>8}   "
              f"{unit.check.description}")
    print(f"  {check_saving['signed']} of {check_saving['units']} instruments "
          f"signed off; {check_saving['stale']} to run")
    print(f"  expected: {_seconds(check_saving['seconds_to_run'])} instead of "
          f"{_seconds(check_saving['seconds_full_run'])} "
          f"({_percent(check_saving['fraction_saved'])}% saved)")

    print()
    whole = saving["seconds_full_run"] + check_saving["seconds_full_run"]
    todo = saving["seconds_to_run"] + check_saving["seconds_to_run"]
    print(f"everything: {_seconds(todo)} to run instead of {_seconds(whole)}")
    return 0


def _print_verify(full: bool = False) -> int:
    report = L.verify(full=full)
    check_report = C.verify_checks()
    print(f"schema {report['schema']}, {report['interpreter']}")
    if full:
        print("asking the release question: signed with the exhaustive "
              "cases run")
    print(f"{report['signed']} of {report['units']} test files carry a "
          f"signature that still holds")
    for label in ("new", "changed", "failed", "partial"):
        names = report[label]
        if names:
            print(f"  {label}: {', '.join(names)}")
    print(f"{check_report['signed']} of {check_report['units']} instruments "
          f"carry a signature that still holds")
    for label in ("new", "changed", "failed"):
        names = check_report[label]
        if names:
            print(f"  {label}: {', '.join(names)}")
    return 0 if (report["all_signed"] and check_report["all_signed"]) else 1


def _run(all_units: bool, jobs: int = 1,
         exhaustive: Optional[bool] = None) -> int:
    before = L.predicted_saving()
    result = L.run_plan(all_units=all_units, jobs=jobs, exhaustive=exhaustive)
    for row in result["results"]:
        status = row.get("status", "?")
        print(f"{row['name']:<40} {status:<8} "
              f"{row.get('tests', 0):>5} tests "
              f"{_seconds(Fraction(int(row.get('milliseconds', 0)), 1000)):>8}")
        if status == "failed":
            print(row.get("output_tail", ""))
    print()
    print(f"ran {result['ran']} on {result['jobs']} job(s) in "
          f"{result['mode']} mode, skipped {result['skipped']}, "
          f"in {_seconds(result['seconds'])}")
    if not all_units:
        print(f"the ledger skipped an estimated "
              f"{_seconds(before['seconds_saved'])} of work")
    if result["failed"]:
        print(f"FAILED: {', '.join(result['failed'])}")
        return 1
    return 0


def _run_checks(all_units: bool, jobs: int = 1,
                exhaustive: Optional[bool] = None) -> int:
    before = C.predicted_check_saving()
    result = C.run_checks(all_units=all_units, jobs=jobs,
                          exhaustive=exhaustive)
    for row in result["results"]:
        status = row.get("status", "?")
        print(f"{row['name']:<24} {status:<8} rc={row.get('returncode')} "
              f"{_seconds(Fraction(int(row.get('milliseconds', 0)), 1000)):>8}")
        if status == "failed":
            print(row.get("output_tail", ""))
    print()
    print(f"ran {result['ran']}, skipped {result['skipped']}, "
          f"in {_seconds(result['seconds'])}")
    if not all_units:
        print(f"the ledger skipped an estimated "
              f"{_seconds(before['seconds_saved'])} of work")
    if result["failed"]:
        print(f"FAILED: {', '.join(result['failed'])}")
        return 1
    return 0


def _closure(name: str) -> int:
    matches = [p for p in L.test_units() if p.name == name or p.stem == name]
    if matches:
        path = matches[0]
        for entry in L.unit_closure(path):
            print(entry.relative_to(L.REPOSITORY_ROOT))
        print()
        print(f"digest {L.unit_digest(path)}")
        return 0
    check = C.checks_by_name().get(name)
    if check is not None:
        for entry in C.check_closure(check):
            print(entry.relative_to(L.REPOSITORY_ROOT))
        print()
        print(f"digest {C.check_digest(check)}")
        return 0
    print(f"no such test file or instrument: {name}")
    return 2


def main(argv: Sequence[str]) -> int:
    jobs = _jobs(argv)
    exhaustive = True if "--exhaustive" in argv else None
    if not argv or "--plan" in argv:
        return _print_plan(full="--release" in argv)
    if "--verify-release" in argv:
        return _print_verify(full=True)
    if "--verify" in argv:
        return _print_verify()
    if "--release" in argv:
        return (_run(all_units=True, jobs=jobs, exhaustive=True)
                | _run_checks(all_units=True, jobs=min(jobs, 3),
                              exhaustive=True))
    if "--run-everything" in argv:
        return (_run(all_units=False, jobs=jobs, exhaustive=exhaustive)
                | _run_checks(all_units=False, jobs=min(jobs, 3),
                              exhaustive=exhaustive))
    if "--run-checks-all" in argv:
        return _run_checks(all_units=True, jobs=min(jobs, 3))
    if "--run-checks" in argv:
        return _run_checks(all_units=False, jobs=min(jobs, 3),
                           exhaustive=exhaustive)
    if "--run-all" in argv:
        return _run(all_units=True, jobs=jobs)
    if "--run" in argv or "--only-stale" in argv:
        return _run(all_units=False, jobs=jobs, exhaustive=exhaustive)
    if "--closure" in argv:
        index = list(argv).index("--closure")
        if index + 1 >= len(argv):
            print("--closure needs a test file name")
            return 2
        return _closure(argv[index + 1])
    print(__doc__)
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))

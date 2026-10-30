"""Command line for the sign-off ledger.

*Last altered 20 October 2026 (Phase 174: stage 0 of the close re-takes the
answer censuses last, ``CENSUS_LAST``).*

::

    PYTHONPATH=. python3 -m glm_universal.signoff --plan
    PYTHONPATH=. python3 -m glm_universal.signoff --run
    PYTHONPATH=. python3 -m glm_universal.signoff --only-stale --jobs 8
    PYTHONPATH=. python3 -m glm_universal.signoff --run-all
    PYTHONPATH=. python3 -m glm_universal.signoff --run-checks
    PYTHONPATH=. python3 -m glm_universal.signoff --run-checks-all
    PYTHONPATH=. python3 -m glm_universal.signoff --run-everything
    PYTHONPATH=. python3 -m glm_universal.signoff --release
    PYTHONPATH=. python3 -m glm_universal.signoff --release --resume
    PYTHONPATH=. python3 -m glm_universal.signoff --close
    PYTHONPATH=. python3 -m glm_universal.signoff --verify
    PYTHONPATH=. python3 -m glm_universal.signoff --verify-release
    PYTHONPATH=. python3 -m glm_universal.signoff --closure test_wobble.py
    PYTHONPATH=. python3 -m glm_universal.signoff --why
    PYTHONPATH=. python3 -m glm_universal.signoff --impact ../STATUS.md

``--run`` (equivalently ``--only-stale``) runs the stale *test files*;
``--run-checks`` runs the stale *instruments* (``lake build``, the evaluation,
the benchmarks, the probes, the figures check); ``--run-everything`` runs both.
The ``-all`` forms ignore the ledger, and ``--release`` is the round-close
check: every test file and every instrument, with the exhaustive cases on.

``--release --resume`` asks the same question and pays only what is still
owed.  Signatures are written after each unit rather than at the end, so an
interrupted release keeps everything it earned; resuming runs the units the
*release* question calls stale -- unsigned, changed, failed, or signed only
with the exhaustive cases deselected -- and skips the rest.  It is the right
command after a release that ran out of time, and it is not a weaker gate:
what decides the round is ``--verify-release``, which re-checks every
signature and reports anything only signed fast as ``partial``.

``--close`` is how a round closes: the release question, paid
incrementally (``--release --resume``), then ``--verify-release``.  It runs
every unit and instrument whose closure moved since it was last signed with
the exhaustive cases on, and nothing else.  A from-scratch ``--release``,
which ignores the ledger, is only needed when the rule itself changes
(``signoff/rules.py``, whose schema bump invalidates every signature anyway)
or when a session wants to re-observe everything on purpose.

``--jobs N`` runs N units at once (default: one per core, capped at eight).
``--exhaustive`` turns the opt-in cases on for a run that is not ``--release``;
they are on automatically for any ``-all`` form.

A routine run signs a unit in ``fast`` mode.  ``--verify-release`` asks the
stricter question -- is every unit signed off *with the exhaustive cases run* --
and reports anything only signed fast as ``partial``.

``--why`` is ``--plan`` with the reason for each stale unit: which kind of
file moved -- code, data, documents, Lean, scaffolding -- rather than only
that something did.  ``--impact PATH`` asks the question the other way round
and *before* the edit: which units would an edit to that file make stale, and
how long did they last take.

Exit codes: ``0`` everything asked for succeeded, ``1`` a test failed or a
signature did not hold, ``2`` the arguments were not understood.
"""

from __future__ import annotations

import sys
from fractions import Fraction
from typing import Optional, Sequence, Set, Tuple

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


def _print_why() -> int:
    """The plan, with the reason each stale unit is going to run."""
    rows = L.plan()
    stale = [u for u in rows if u.stale]
    width = max([len(u.name) for u in stale] + [10])
    for unit in stale:
        last = unit.last_seconds
        timing = _seconds(last) if last is not None else "  -  "
        print(f"  {unit.name:<{width}} {timing:>8}   {L.reason(unit)}")
    print(f"{len(stale)} of {len(rows)} test files will run")
    if stale:
        kinds = {}
        for unit in stale:
            for group in L.stale_groups(unit):
                kinds[group] = kinds.get(group, 0) + 1
        if kinds:
            print("  by kind: " + ", ".join(
                f"{name} {count}" for name, count in sorted(kinds.items())))
    return 0


def _print_impact(target: str) -> int:
    """What an edit to one file would cost, before it is made."""
    report = L.impact(target)
    for name in report["units"]:
        print(f"  {name}")
    print(f"{report['count']} of {report['of']} test files reach "
          f"{report['target']}")
    print(f"  they last took {_seconds(report['seconds'])} in total")
    if report["without_timing"]:
        print(f"  no recorded timing for: "
              f"{', '.join(report['without_timing'])}")
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
         exhaustive: Optional[bool] = None,
         only: Optional[Sequence[str]] = None,
         exclude: Sequence[str] = ()) -> int:
    before = L.predicted_saving()
    result = L.run_plan(all_units=all_units, jobs=jobs, exhaustive=exhaustive,
                        only=only, exclude=exclude)
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
                exhaustive: Optional[bool] = None,
                names: Sequence[str] = (),
                exclude: Sequence[str] = ()) -> int:
    before = C.predicted_check_saving()
    result = C.run_checks(all_units=all_units, jobs=jobs,
                          exhaustive=exhaustive, names=names,
                          exclude=exclude)
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


#: How many times a close may go round stage 1 and the refresh before it
#: stops and says so.  One pass is the normal case; a second is needed only
#: when the refresh moved something a package unit reads (a figure the
#: session did not refresh before closing); a third would mean the refresh
#: is not converging, which is a defect to report, not to loop on.
_CLOSE_PASSES = 3


def _stale_names(exclude_units: Sequence[str] = (),
                 exclude_checks: Sequence[str] = (),
                 only_units: Optional[Sequence[str]] = None,
                 only_checks: Optional[Sequence[str]] = None) -> Tuple[str, ...]:
    """The units and instruments the release question calls stale."""
    out = []
    for unit in L.plan(full=True):
        if not unit.stale or unit.name in exclude_units:
            continue
        if only_units is not None and unit.name not in only_units:
            continue
        out.append(unit.name)
    for unit in C.check_plan():
        if not unit.stale or unit.name in exclude_checks:
            continue
        if only_checks is not None and unit.name not in only_checks:
            continue
        out.append(unit.name)
    return tuple(out)


def _refresh_corpus(attempts: int = 2) -> int:
    """``corpus --refresh``, in its own interpreter, from ````.

    A refresh can end ``not current`` with a block still stale that reads a
    block the same refresh wrote (seen in Phase 109: the corpus-address
    study's block after the digest blocks moved); a second refresh settles
    it.  So a refresh that does not end current is run once more before the
    close reports a defect -- a genuine defect fails both times.
    """
    import os
    import subprocess
    env = dict(os.environ)
    env["PYTHONPATH"] = str(L.PACKAGE_ROOT.parent) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    code = 0
    for attempt in range(1, attempts + 1):
        completed = subprocess.run(
            (sys.executable, "-m", "glm_universal.corpus", "--refresh"),
            cwd=str(L.PROJECT_ROOT), env=env, capture_output=True,
            text=True)
        tail = (completed.stdout + completed.stderr).strip().splitlines()[-12:]
        for line in tail:
            print(f"  {line}")
        code = completed.returncode
        if code == 0:
            break
        if attempt < attempts:
            print("  the refresh did not end current; refreshing once more")
    return code


def _stale_caches() -> Tuple[Tuple[str, str], ...]:
    """``(module, sub-command)`` for every stale measurement cache that has
    a re-taking command (:mod:`glm_universal.corpus.caches`)."""
    from ..corpus import caches as ca
    out = [(str(row["module"]), str(row["command"]))
           for row in ca.cache_states()
           if not row["fresh"] and row["command"]]
    # The elaborator's citation reference is guarded by the digest of the
    # Lean tree rather than by ``module_digest``/``current``, so the census
    # does not see it; a new Lean file made it stale and failed
    # test_citation_scope and test_proof_dependency inside the Phase 109
    # close.  Re-taking it needs the compiled library (``lake env lean``)
    # and costs about twenty seconds.
    try:
        from ..reasoning import citation_reference as cr
        # Forget the memoised reference first: stage 0 re-takes it in a
        # subprocess, and the memo of the census taken before that made the
        # re-taken reference read "still stale" (Phase 110's close).
        cr._cache = None
        if cr.state().get("verdict") == "stale":
            out.append(("citation_reference", REFERENCE_COMMAND))
    except Exception:  # pragma: no cover - a reference that cannot be read
        pass
    return tuple(out)


#: The sub-command (with its flag) that re-takes the citation reference.
REFERENCE_COMMAND = "citation-scope --reference"


#: The caches that record the system's answers and, since Phase 174, are
#: guarded by the stored measurements those answers quote
#: (``studies/QUOTED_MEASUREMENTS_STUDY.md``): re-taken last, in this order,
#: and again in the second pass if an earlier re-take staled them.
CENSUS_LAST: Tuple[str, ...] = ("evidence_model_study", "evidence_in_use_study")


def _retake_caches() -> int:
    """Stage 0 of the close: re-take every stale measurement cache.

    A cache is guarded by the digest of the sources it was taken from, and
    the unit that reads it fails while the digest has moved -- so a round
    that edits ``evaluation/cases.py`` or ``runtime/session.py`` made
    ``test_query_escalation`` fail *inside* the close, which then deferred
    the totals and the document checks, and the round paid a whole extra
    close after re-taking the cache by hand.  Re-taking first means the
    units that read a cache run once, against figures that are current.
    A cache that is still stale after its command ran is reported and left
    to fail its unit (which says why).  Two passes: one cache's figures may
    be read by another's measurement.
    """
    import os
    import subprocess
    env = dict(os.environ)
    env["PYTHONPATH"] = str(L.PACKAGE_ROOT.parent) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    status = 0
    tried: Set[str] = set()
    for _ in range(2):
        stale = [(m, c) for m, c in _stale_caches()
                 if m not in tried or m in CENSUS_LAST]
        stale.sort(key=lambda mc: (mc[0] in CENSUS_LAST,
                                   CENSUS_LAST.index(mc[0])
                                   if mc[0] in CENSUS_LAST else 0))
        if not stale:
            break
        for module, command in stale:
            tried.add(module)
            if module == "citation_reference":
                # the reference is read off the compiled library
                subprocess.run(("lake", "build"),
                               cwd=str(L.PROJECT_ROOT),
                               capture_output=True, text=True)
            argv = tuple(command.split()) if " " in command else \
                (command, "--write")
            print(f"  re-taking {module}: tools {' '.join(argv)}")
            done = subprocess.run(
                (sys.executable, "-m", "glm_universal.tools") + argv,
                cwd=str(L.PROJECT_ROOT), env=env, capture_output=True,
                text=True)
            if done.returncode != 0:
                status = 1
                tail = (done.stdout + done.stderr).strip().splitlines()[-6:]
                for line in tail:
                    print(f"    {line}")
    left = [m for m, _ in _stale_caches()]
    if left:
        print(f"  still stale after re-taking: {', '.join(left)}")
        status = 1
    return status


def _close(jobs: int, settle: bool = True, retake: bool = True) -> int:
    """Close the round in one command: package, refresh, document checks.

    The order is what removes the loop.  The suite totals are recorded from
    the *counted* units -- every unit except the document checks
    (``rules.DOCUMENT_CHECKS``) -- and the document checks are exactly what
    asks whether the documents quote those totals.  So:

    1. **the package** -- every stale unit and instrument except the
       document checks, with the exhaustive cases on.  If a counted unit
       fails, the totals cannot be recorded, and the document checks would
       only fail on figures that are about to move: they are *deferred*, not
       run, and the close says which units are owed.  Nothing earned is lost.
    2. **the refresh** -- ``corpus --refresh``, which writes the totals just
       recorded (and anything else stale) into ``FIGURES.md`` and the inline
       figures.  The package units are signed against the documents with
       the run-measured figures emptied, so this does not make them stale;
       if the refresh moved anything else they read, stage 1 runs again for
       just those.
    3. **the document checks** -- ``test_corpus``, ``test_figures`` and the
       ``figures`` instrument, now against documents that are current.

    Before all three, **stage 0** re-takes every stale measurement cache
    (:func:`_retake_caches`), so a unit that reads one does not fail stage 1
    on a digest the round moved and defer everything after it.

    Then ``--verify-release`` decides, as before.  ``settle=False``
    (``--no-refresh``) skips step 2 for a session that has just refreshed;
    ``retake=False`` (``--no-retake``) skips stage 0.
    """
    doc_units = tuple(L.DOCUMENT_CHECKS)
    doc_checks = tuple(C.DOCUMENT_INSTRUMENTS)
    status = 0
    if retake and _stale_caches():
        names = ", ".join(m for m, _ in _stale_caches())
        print(f"stage 0: re-taking the stale measurement caches ({names}) "
              f"before the units that read them run")
        if _retake_caches() != 0:
            print("a cache could not be re-taken (above); the units that "
                  "read it will fail in stage 1 and say why")
        print()
    for attempt in range(1, _CLOSE_PASSES + 1):
        print(f"stage 1, pass {attempt}: the package -- every stale unit and "
              f"instrument except the document checks "
              f"({', '.join(doc_units + doc_checks)})")
        status |= (_run(all_units=False, jobs=jobs, exhaustive=True,
                        exclude=doc_units)
                   | _run_checks(all_units=False, jobs=min(jobs, 3),
                                 exhaustive=True, exclude=doc_checks))
        owed = L.counted_failures()
        if owed:
            print()
            print(f"document checks deferred: the suite totals are recorded "
                  f"only once every counted unit has passed with the "
                  f"exhaustive cases on, and {len(owed)} has not: "
                  f"{', '.join(owed)}.")
            print("fix those and run --close again; it pays only for what is "
                  "still owed, then refreshes and runs the document checks.")
            print()
            return 1 | _print_verify(full=True)
        pending = _stale_names(only_units=doc_units, only_checks=doc_checks)
        if not pending:
            break
        if settle:
            print()
            print(f"stage 2: corpus --refresh, so the document checks "
                  f"({', '.join(pending)}) read the figures just recorded")
            if _refresh_corpus() != 0:
                print("the refresh found a defect in the documents (above); "
                      "fix it and run --close again")
                return 1 | _print_verify(full=True)
        moved = _stale_names(exclude_units=doc_units,
                             exclude_checks=doc_checks)
        if not moved:
            break
        print(f"the refresh moved what {len(moved)} package unit(s) read: "
              f"{', '.join(moved)}; running them again")
        if attempt == _CLOSE_PASSES:
            print(f"the close did not settle in {_CLOSE_PASSES} passes; "
                  f"report this -- the refresh is not converging")
            return 1 | _print_verify(full=True)
    pending = _stale_names(only_units=doc_units, only_checks=doc_checks)
    if pending:
        print()
        print(f"stage 3: the document checks ({', '.join(pending)})")
        status |= _run(all_units=False, jobs=jobs, exhaustive=True,
                       only=doc_units)
        instruments = [n for n in doc_checks if n in pending]
        if instruments:
            status |= _run_checks(all_units=False, jobs=min(jobs, 3),
                                  exhaustive=True, names=instruments)
    print()
    return status | _print_verify(full=True)


#: The commands that run test files (each under ``python3 -m pytest``).
_RUNS = ("--close", "--release", "--run-everything", "--run-all", "--run")


def _pytest_missing() -> bool:
    """Whether the test runner is absent from this interpreter.  pytest is
    not part of the standard library and is not installed in every
    environment the repository is opened in; without it every unit fails
    and the failure reads as a broken suite (Phase 107's first close)."""
    import importlib.util
    return importlib.util.find_spec("pytest") is None


def main(argv: Sequence[str]) -> int:
    if any(a in argv for a in _RUNS) and _pytest_missing():
        print("pytest is not installed in this environment, and every test "
              "file runs under it.  Install it first:\n"
              "    python3 -m pip install pytest\n"
              "then run the same command again.  (ITERATE.md §0)")
        return 2
    jobs = _jobs(argv)
    exhaustive = True if "--exhaustive" in argv else None
    if not argv or "--plan" in argv:
        return _print_plan(full="--release" in argv)
    if "--why" in argv:
        return _print_why()
    if "--impact" in argv:
        index = list(argv).index("--impact")
        if index + 1 >= len(argv):
            print("--impact needs a path")
            return 2
        return _print_impact(argv[index + 1])
    if "--verify-release" in argv:
        return _print_verify(full=True)
    if "--verify" in argv:
        return _print_verify()
    if "--close" in argv:
        print("closing: the release question, paying only what moved -- the "
              "package, then the refresh, then the document checks; "
              "--verify-release decides")
        return _close(jobs, settle="--no-refresh" not in argv,
                      retake="--no-retake" not in argv)
    if "--release" in argv:
        resume = "--resume" in argv
        if resume:
            print("resuming: running only what the release question calls "
                  "stale; --verify-release still decides the round")
        return (_run(all_units=not resume, jobs=jobs, exhaustive=True)
                | _run_checks(all_units=not resume, jobs=min(jobs, 3),
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

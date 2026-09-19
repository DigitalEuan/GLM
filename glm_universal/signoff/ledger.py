"""The sign-off ledger: the record of what has been run and what has not.

The *rule* -- what a unit depends on, what its digest covers and how it is run
-- is :mod:`glm_universal.signoff.rules`, and is in every unit's closure. This
module is the record kept under that rule: the plan, the stored book of
signatures, the parallel runner and the suite totals. Nothing here can change
what a test observes, which is exactly why it is *not* in the closure: a round
that improves this file's reporting costs no re-runs.

The names of the rule are re-exported below, so ``ledger.unit_closure`` and
``ledger.LEDGER_PATH`` still mean what they always did.
"""

from __future__ import annotations

import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .rules import (  # noqa: F401 - re-exported: the rule's names are the ledger's surface
    closure_groups,
    CLOSURE_GROUPS,
    code_store,
    counted_units,
    DEFAULT_JOBS,
    DOCUMENT_CHECKS,
    document_index,
    DOCUMENT_SUFFIXES,
    EXHAUSTIVE_ENV,
    file_digest,
    group_digests,
    interpreter_tag,
    lean_index,
    LEAN_MANIFEST_NAMES,
    LEAN_ROOTS,
    lean_sources,
    LEDGER_PATH,
    PACKAGE_ROOT,
    PROJECT_ROOT,
    referenced_documents,
    REPOSITORY_ROOT,
    run_environment,
    scaffolding_paths,
    SCHEMA,
    test_units,
    TESTS_DIR,
    TOTALS_PATH,
    tree_digest,
    unit_closure,
    unit_digest,
    units_touching,
    _hasher,
    _parse_pytest_summary,
    _run_one,
)

# ===========================================================================
#  The ledger
# ===========================================================================

@dataclass(frozen=True)
class Unit:
    """One test file's entry in the plan."""

    path: Path
    name: str
    digest: str
    #: "signed" | "changed" | "new" | "failed" | "partial"
    state: str
    recorded: Optional[Mapping[str, object]]

    @property
    def stale(self) -> bool:
        return self.state != "signed"

    @property
    def mode(self) -> Optional[str]:
        """``"full"`` or ``"fast"`` -- what the recorded run covered."""
        if not self.recorded:
            return None
        return str(self.recorded.get("mode", "fast"))

    @property
    def last_seconds(self) -> Optional[Fraction]:
        if not self.recorded:
            return None
        value = self.recorded.get("milliseconds")
        return Fraction(int(value), 1000) if value is not None else None


def load_ledger(path: Optional[Path] = None) -> Dict[str, object]:
    """The stored ledger, or an empty one."""
    target = Path(path) if path is not None else LEDGER_PATH
    if not target.is_file():
        return {"schema": SCHEMA, "python": interpreter_tag(), "units": {}}
    data = json.loads(target.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        return {"schema": SCHEMA, "python": interpreter_tag(), "units": {},
                "superseded_schema": data.get("schema")}
    return data


def save_ledger(ledger: Mapping[str, object],
                path: Optional[Path] = None) -> Path:
    """Write the ledger back, sorted so the diff is readable."""
    target = Path(path) if path is not None else LEDGER_PATH
    target.write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n",
                      encoding="utf-8")
    return target


def plan(ledger: Optional[Mapping[str, object]] = None,
         full: bool = False) -> Tuple[Unit, ...]:
    """What is signed off and what has to run, with the reason for each.

    ``full=True`` asks the release question rather than the routine one: a
    unit whose last passing run left the exhaustive cases deselected is
    reported ``"partial"``, so a release check runs it again with them on.
    """
    book = dict(ledger if ledger is not None else load_ledger())
    units = dict(book.get("units", {}))
    out: List[Unit] = []
    for path in test_units():
        name = path.name
        digest = unit_digest(path)
        recorded = units.get(name)
        if recorded is None:
            state = "new"
        elif recorded.get("status") != "passed":
            state = "failed"
        elif recorded.get("digest") != digest:
            state = "changed"
        elif full and recorded.get("mode", "fast") != "full":
            state = "partial"
        else:
            state = "signed"
        out.append(Unit(path=path, name=name, digest=digest, state=state,
                        recorded=recorded))
    return tuple(out)


def predicted_saving(units: Optional[Sequence[Unit]] = None
                     ) -> Dict[str, object]:
    """How much this ledger is expected to save, from recorded run times.

    Exact rationals of seconds, from the milliseconds each unit last took.  A
    unit that has never run contributes nothing to either side, and is counted
    separately so the estimate is never quietly optimistic.
    """
    rows = list(units if units is not None else plan())
    signed = [u for u in rows if not u.stale]
    stale = [u for u in rows if u.stale]
    known = lambda group: sum(  # noqa: E731 - a local alias reads better here
        (u.last_seconds for u in group if u.last_seconds is not None),
        Fraction(0))
    saved = known(signed)
    to_run = known(stale)
    unknown = [u.name for u in rows if u.last_seconds is None]
    total = saved + to_run
    return {
        "units": len(rows),
        "signed": len(signed),
        "stale": len(stale),
        "seconds_saved": saved,
        "seconds_to_run": to_run,
        "seconds_full_run": total,
        "fraction_saved": (saved / total) if total else Fraction(0),
        "units_without_timing": tuple(unknown),
    }


# ===========================================================================
#  Why, and what an edit would cost
# ===========================================================================

def stale_groups(unit: Unit) -> Tuple[str, ...]:
    """Which kinds of file moved since this unit was signed.

    Empty for a unit that is signed, that has never run, or that was signed
    before the group digests were recorded -- three cases a caller has to tell
    apart anyway, and :func:`reason` does.
    """
    if not unit.stale or not unit.recorded:
        return ()
    stored = unit.recorded.get("groups")
    if not isinstance(stored, Mapping) or not stored:
        return ()
    current = group_digests(unit.path)
    return tuple(name for name in CLOSURE_GROUPS
                 if stored.get(name) != current[name])


def reason(unit: Unit) -> str:
    """One line saying why a unit is going to run, or that it is not.

    A stale unit is worth a different amount of attention depending on what
    moved: ``documents`` almost always still passes and ``code`` may not, and
    the difference is free to report and expensive to guess.
    """
    if not unit.stale:
        return "signed"
    if unit.state == "new":
        return "never run"
    if unit.state == "failed":
        return "last run failed"
    if unit.state == "partial":
        return "signed fast; the release question needs the exhaustive cases"
    groups = stale_groups(unit)
    if not groups:
        return "changed; signed before the reason was recorded"
    return "changed: " + ", ".join(groups)


def impact(target: Path, ledger: Optional[Mapping[str, object]] = None
           ) -> Dict[str, object]:
    """What editing one file would cost, before it is edited.

    The units whose closure holds ``target``, and the seconds they took the
    last time they ran.  This is the question a session actually has --
    "can I touch this cheaply?" -- and it was previously answerable only by
    editing the file and reading the plan.
    """
    names = set(units_touching(Path(target)))
    rows = plan(ledger)
    hit = [u for u in rows if u.name in names]
    seconds = sum((u.last_seconds for u in hit
                   if u.last_seconds is not None), Fraction(0))
    return {
        "target": str(Path(target)),
        "units": tuple(sorted(names)),
        "count": len(names),
        "of": len(rows),
        "seconds": seconds,
        "without_timing": tuple(sorted(u.name for u in hit
                                       if u.last_seconds is None)),
    }


# ===========================================================================
#  Running
# ===========================================================================

def sign(unit: Unit, outcome: Mapping[str, object],
         ledger: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    """Record one outcome against the digest it was obtained at.

    A failure is recorded too -- with its status -- so that the unit stays
    stale until it passes.  Only ``status == "passed"`` counts as a signature.

    The five group digests are recorded beside the one that decides: they
    decide nothing, and they are what lets a later plan say *which kind* of
    file moved rather than only that something did.  Five hex strings per
    unit; an entry signed before they existed simply has none, and is
    reported as a change with no reason recorded.
    """
    book = ledger if ledger is not None else load_ledger()
    units = book.setdefault("units", {})
    units[unit.name] = {
        "digest": unit.digest,
        "groups": group_digests(unit.path),
        "status": outcome["status"],
        "tests": outcome.get("tests", 0),
        "subtests": outcome.get("subtests", 0),
        "failures": outcome.get("failures", 0),
        "milliseconds": outcome.get("milliseconds", 0),
        "mode": outcome.get("mode", "fast"),
        "signed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": interpreter_tag(),
    }
    book["python"] = interpreter_tag()
    book["schema"] = SCHEMA
    return book


def suite_totals(ledger: Optional[Mapping[str, object]] = None
                 ) -> Dict[str, object]:
    """What the last complete release run counted, or an empty record.

    The suite's headline figures -- how many test files, how many tests, how
    many subtests -- are a property of a *run*, not of the source, so they
    cannot be computed by reading the tree.  They are recorded here by the
    one run that covers everything: a release run in which every unit passed
    with the exhaustive cases on.  A routine run never overwrites them, so
    the number a document quotes is always the number a complete run produced
    and never a partial count from an afternoon's iteration.

    :mod:`glm_universal.figures` reads this, which is what lets one
    measurement feed every document that quotes it.

    **These three counts used to be a fixed point, and are not one now.**
    They were measured over the whole suite, which includes
    ``tests/test_figures.py``, which checks the documents that quote them --
    so the figure counted a test file whose own size depended on what the
    documents said, and a round that changed the *set* of documented
    sentences needed two complete runs to converge.  As of v1.12.0 the
    totals are measured over :func:`counted_units`, the suite minus that one
    file: every unit still has to pass before anything is recorded, but
    nothing the documentation says can move a number the documentation
    quotes, so a documentation round converges in one pass by construction.
    ``totals["excludes"]`` names what was left out, and the generated
    sentence in :mod:`glm_universal.figures` says so in words.
    """
    book = dict(ledger if ledger is not None else load_ledger())
    recorded = book.get("totals")
    if not isinstance(recorded, dict):
        return {}
    return dict(recorded)


def _record_totals(book: Dict[str, object], mode: str) -> Dict[str, object]:
    """Store the suite totals if the counted units all ran and passed.

    The condition is over :func:`counted_units` -- the suite minus the
    document check -- for the same reason the counts are.  Requiring the
    document check to pass as well would put the loop that
    :func:`counted_units` removes straight back: a round that *adds* a test
    file leaves the recorded ``N of M test files`` sentence one file short,
    which is precisely what ``tests/test_figures.py`` refuses, so the run
    that would have measured the new totals could never record them and no
    later run could either.  The totals do not depend on that file's result,
    and the run still reports itself failed, so nothing is signed off by
    this: what is recorded is a measurement the counted units actually
    produced, and the documents are then regenerated from it.
    """
    units = dict(book.get("units", {}))
    names = [p.name for p in counted_units()]
    if not names:
        return book
    entries = [units.get(name) for name in names]
    if any(entry is None or entry.get("status") != "passed"
           or entry.get("mode", "fast") != "full" for entry in entries):
        return book
    counted = [units[name] for name in names]
    counts = {
        "test_files": len(counted),
        "tests": sum(int(entry.get("tests", 0)) for entry in counted),
        "subtests": sum(int(entry.get("subtests", 0)) for entry in counted),
    }
    book["totals"] = {
        **counts,
        "excludes": list(DOCUMENT_CHECKS),
        "mode": mode,
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": interpreter_tag(),
    }
    _write_totals_sidecar(counts)
    return book


def _write_totals_sidecar(counts: Mapping[str, int],
                          path: Optional[Path] = None) -> None:
    """Keep :data:`TOTALS_PATH` equal to the counts, and touch it no further.

    Rewriting an identical file would move its digest under a checker that
    depends on it, so the write happens only when the content differs.
    """
    target = Path(path) if path is not None else TOTALS_PATH
    body = json.dumps(dict(counts), indent=2, sort_keys=True) + "\n"
    try:
        if target.read_text(encoding="utf-8") == body:
            return
    except OSError:
        pass
    target.write_text(body, encoding="utf-8")


def run_plan(all_units: bool = False, dry_run: bool = False,
             ledger_path: Optional[Path] = None,
             jobs: int = 1,
             exhaustive: Optional[bool] = None) -> Dict[str, object]:
    """Run the stale units (or all of them) and update the ledger.

    ``jobs`` runs that many test files at once.  Each one is a separate
    interpreter reading the same tree and writing nothing, so the only shared
    state is the ledger, which is written under a lock after each unit
    finishes -- an interrupted parallel run keeps every signature it earned.

    ``exhaustive`` turns the opt-in cases on; it defaults to ``all_units``, so
    a release check (``--run-all``) runs everything there is and a routine run
    does not.  What was covered is recorded with the signature.
    """
    if exhaustive is None:
        exhaustive = all_units
    book = load_ledger(ledger_path)
    rows = plan(book, full=exhaustive)
    chosen = list(rows) if all_units else [u for u in rows if u.stale]
    skipped = [u for u in rows if u not in chosen]
    results: List[Dict[str, object]] = []
    started = time.monotonic_ns()
    if dry_run:
        for unit in chosen:
            results.append({"name": unit.name, "status": "not run",
                            "state": unit.state})
        return {
            "ran": len(chosen),
            "skipped": len(skipped),
            "skipped_names": tuple(u.name for u in skipped),
            "failed": (),
            "jobs": jobs,
            "mode": "full" if exhaustive else "fast",
            "seconds": Fraction(0),
            "results": tuple(results),
        }

    lock = threading.Lock()

    def one(unit: Unit) -> Dict[str, object]:
        outcome = _run_one(unit.path, exhaustive=exhaustive)
        with lock:
            # written after every unit, not at the end: an interrupted run
            # must keep the signatures it has already earned (directive D1)
            sign(unit, outcome, book)
            save_ledger(book, ledger_path)
        return {"name": unit.name, "state": unit.state, **outcome}

    workers = max(1, int(jobs))
    if workers == 1 or len(chosen) <= 1:
        results = [one(unit) for unit in chosen]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(one, chosen))
    elapsed_ms = (time.monotonic_ns() - started) // 1_000_000
    if exhaustive:
        _record_totals(book, "full")
    save_ledger(book, ledger_path)
    return {
        "ran": len(chosen),
        "skipped": len(skipped),
        "skipped_names": tuple(u.name for u in skipped),
        "failed": tuple(r["name"] for r in results
                        if r.get("status") == "failed"),
        "jobs": workers,
        "mode": "full" if exhaustive else "fast",
        "seconds": Fraction(elapsed_ms, 1000),
        "results": tuple(results),
    }


def verify(ledger_path: Optional[Path] = None,
           full: bool = False) -> Dict[str, object]:
    """Re-check every signature without running anything.

    This is the honest counterpart of skipping: it says exactly which files are
    covered by a signature that still holds, and which are not.  Under
    ``full=True`` a unit last run without the exhaustive cases is reported
    ``partial`` rather than signed.
    """
    rows = plan(load_ledger(ledger_path), full=full)
    signed = [u.name for u in rows if u.state == "signed"]
    return {
        "units": len(rows),
        "signed": len(signed),
        "signed_names": tuple(signed),
        "new": tuple(u.name for u in rows if u.state == "new"),
        "changed": tuple(u.name for u in rows if u.state == "changed"),
        "failed": tuple(u.name for u in rows if u.state == "failed"),
        "partial": tuple(u.name for u in rows if u.state == "partial"),
        "all_signed": len(signed) == len(rows),
        "full": full,
        "interpreter": interpreter_tag(),
        "schema": SCHEMA,
    }

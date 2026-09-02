"""Sign-off for the instruments that are not pytest.

The test suite is not the only thing this project re-runs from scratch every
session.  ``lake build`` compiles the Lean development, the end-to-end
evaluation drives the CLI once per question in a fresh interpreter, the
benchmark suites and the capability probes each walk the whole package, and
the six example scripts are run to see that they still run.  Together they
cost more than the suite does, and every one of them is a *function of files
in this repository* -- so the same rule applies (directive **D4**): a result
may be reused exactly when a digest of everything it depended on still holds.

A **check** here is one such instrument: a name, a command, the directory it
runs in, and the closure of files its result depends on, computed the same way
:mod:`glm_universal.signoff.ledger` computes a test file's -- by walking
imports with :mod:`ast`, never by importing.

Both kinds of unit share one ledger file, under separate keys, so a single
``--verify`` says what is covered and what is not.

::

    cd overlay
    PYTHONPATH=. python3 -m glm_universal.signoff --plan          # both
    PYTHONPATH=. python3 -m glm_universal.signoff --run-checks    # stale ones
    PYTHONPATH=. python3 -m glm_universal.signoff --run-checks-all
"""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from . import ledger as L

__all__ = [
    "Check",
    "CHECKS",
    "CheckUnit",
    "check_closure",
    "check_digest",
    "check_plan",
    "checks_by_name",
    "run_checks",
    "verify_checks",
]


# ===========================================================================
#  The instruments
# ===========================================================================

@dataclass(frozen=True)
class Check:
    """One non-pytest instrument, and what its result depends on."""

    name: str
    description: str
    command: Tuple[str, ...]
    #: ``"overlay"`` or ``"repository"``.
    where: str = "overlay"
    #: Package modules whose import closure the result depends on.
    entry_points: Tuple[str, ...] = ()
    #: Extra files, relative to the repository root.
    extra: Tuple[str, ...] = ()
    #: True when the Lean development is part of the closure.
    lean: bool = False
    #: Return codes that count as success (``grep`` reports 1 for no match).
    ok_returncodes: Tuple[int, ...] = (0,)
    #: Roughly how long it takes, for the plan's estimate before a first run.
    expected_seconds: int = 60

    @property
    def cwd(self) -> Path:
        return (L.PROJECT_ROOT if self.where == "overlay"
                else L.REPOSITORY_ROOT)


#: Every instrument the project re-runs, in the order a release check runs
#: them: the specification first, then the package, then the front door.
CHECKS: Tuple[Check, ...] = (
    Check(
        name="lean-build",
        description="lake build over the Lean development",
        command=("lake", "build"),
        where="repository",
        lean=True,
        expected_seconds=120,
    ),
    Check(
        name="lean-sorry-free",
        description="no sorry or admit anywhere in RequestProject/GLM",
        command=("grep", "-rInw", "-e", "sorry", "-e", "admit",
                 "RequestProject/GLM"),
        where="repository",
        lean=True,
        ok_returncodes=(1,),
        expected_seconds=1,
    ),
    Check(
        name="lean-copies-identical",
        description="the repository and overlay copies of the Lean tree agree",
        # ``-x README.md``: the overlay copy carries the development's own
        # README and the repository copy does not, by design.  Every ``.lean``
        # file must match.
        command=("diff", "-r", "-x", "README.md", "RequestProject/GLM",
                 "overlay/glm_lean/RequestProject/GLM"),
        where="repository",
        lean=True,
        expected_seconds=1,
    ),
    Check(
        name="capabilities",
        description="the capability probes",
        command=(sys.executable, "-m", "glm_universal.capabilities"),
        entry_points=("capabilities/__main__.py",),
        expected_seconds=90,
    ),
    Check(
        name="benchmarks",
        description="the benchmark suites",
        command=(sys.executable, "-m", "glm_universal.benchmarks"),
        entry_points=("benchmarks/__main__.py",),
        expected_seconds=90,
    ),
    Check(
        name="evaluation",
        description="the end-to-end CLI evaluation, one interpreter per case",
        command=(sys.executable, "-m", "glm_universal.evaluation",
                 "--jobs", "8"),
        entry_points=("evaluation/__main__.py",),
        extra=("overlay/GLM.py",),
        expected_seconds=240,
    ),
    Check(
        name="figures",
        description="FIGURES.md matches a fresh computation",
        command=(sys.executable, "-m", "glm_universal.figures", "--check"),
        entry_points=("figures.py",),
        # ``.glm_suite_totals.json`` and not ``.glm_signoff.json``: the suite
        # totals are the one figure no amount of reading the sources produces,
        # so ``figures`` reads them from the sidecar a release run writes.  The
        # ledger itself moves whenever anything is signed, so depending on it
        # would leave this instrument permanently stale.
        extra=("overlay/FIGURES.md", "overlay/.glm_suite_totals.json"),
        expected_seconds=45,
    ),
)


def checks_by_name() -> Dict[str, Check]:
    """The instruments, keyed by name."""
    return {check.name: check for check in CHECKS}


# ===========================================================================
#  Closures and digests
# ===========================================================================

def check_closure(check: Check) -> Tuple[Path, ...]:
    """Every file this instrument's result depends on, sorted.

    The union of: the import closure of each entry point (which already draws
    in the data files, the documents those modules name, and the sign-off
    scaffolding), any extra files named outright, and -- for a Lean check --
    the whole Lean development and its build files.
    """
    out = set()
    for relative in check.entry_points:
        entry = L.PACKAGE_ROOT / relative
        if entry.is_file():
            out.update(L.unit_closure(entry))
    for relative in check.extra:
        candidate = L.REPOSITORY_ROOT / relative
        if candidate.is_file():
            out.add(candidate.resolve())
    if check.lean:
        out.update(L.lean_sources())
    out.update(p.resolve() for p in L.scaffolding_paths())
    # this module states what the instrument is, so it is part of every
    # instrument's closure (it is deliberately not part of a test file's)
    out.add(Path(__file__).resolve())
    return tuple(sorted(out))


def check_digest(check: Check) -> str:
    """The signature of an instrument: closure, schema, interpreter, command."""
    h = L._hasher()
    h.update(f"schema={L.SCHEMA}\0".encode("ascii"))
    h.update(f"python={L.interpreter_tag()}\0".encode("ascii"))
    h.update(("command=" + " ".join(check.command) + "\0").encode("utf-8"))
    h.update(L.tree_digest(check_closure(check),
                           root=L.REPOSITORY_ROOT).encode("ascii"))
    return h.hexdigest()


# ===========================================================================
#  The plan
# ===========================================================================

@dataclass(frozen=True)
class CheckUnit:
    """One instrument's entry in the plan."""

    check: Check
    digest: str
    state: str                       # signed | changed | new | failed
    recorded: Optional[Mapping[str, object]] = field(default=None)

    @property
    def name(self) -> str:
        return self.check.name

    @property
    def stale(self) -> bool:
        return self.state != "signed"

    @property
    def last_seconds(self) -> Optional[Fraction]:
        if not self.recorded:
            return None
        value = self.recorded.get("milliseconds")
        return Fraction(int(value), 1000) if value is not None else None


def check_plan(ledger: Optional[Mapping[str, object]] = None
               ) -> Tuple[CheckUnit, ...]:
    """What is signed off among the instruments, and what has to run."""
    book = dict(ledger if ledger is not None else L.load_ledger())
    recorded_all = dict(book.get("checks", {}))
    out: List[CheckUnit] = []
    for check in CHECKS:
        digest = check_digest(check)
        recorded = recorded_all.get(check.name)
        if recorded is None:
            state = "new"
        elif recorded.get("status") != "passed":
            state = "failed"
        elif recorded.get("digest") != digest:
            state = "changed"
        else:
            state = "signed"
        out.append(CheckUnit(check=check, digest=digest, state=state,
                             recorded=recorded))
    return tuple(out)


def _sign_check(unit: CheckUnit, outcome: Mapping[str, object],
                book: Dict[str, object]) -> Dict[str, object]:
    """Record one instrument's outcome against the digest it was run at."""
    checks = book.setdefault("checks", {})
    checks[unit.name] = {
        "digest": unit.digest,
        "status": outcome["status"],
        "returncode": outcome.get("returncode"),
        "milliseconds": outcome.get("milliseconds", 0),
        "signed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": L.interpreter_tag(),
        "output_tail": outcome.get("output_tail", ""),
    }
    book["schema"] = L.SCHEMA
    book["python"] = L.interpreter_tag()
    return book


def _run_one(check: Check, exhaustive: bool = False) -> Dict[str, object]:
    """Run one instrument and report what happened."""
    started = time.monotonic()
    completed = subprocess.run(list(check.command), cwd=str(check.cwd),
                               capture_output=True, text=True,
                               env=L.run_environment(exhaustive))
    elapsed = time.monotonic() - started
    ok = completed.returncode in check.ok_returncodes
    return {
        "status": "passed" if ok else "failed",
        "returncode": completed.returncode,
        "milliseconds": int(elapsed * 1000),
        "output_tail": (completed.stdout + completed.stderr)[-800:],
    }


def run_checks(all_units: bool = False, names: Sequence[str] = (),
               dry_run: bool = False,
               ledger_path: Optional[Path] = None,
               jobs: int = 1,
               exhaustive: Optional[bool] = None) -> Dict[str, object]:
    """Run the stale instruments (or all of them) and update the ledger.

    ``jobs`` runs that many instruments at once.  They are independent
    processes over a tree none of them writes to, and the ledger is written
    under a lock as each finishes.  ``lake build`` and the evaluation are
    themselves parallel, so more than a few jobs here buys little.
    """
    if exhaustive is None:
        exhaustive = all_units
    book = L.load_ledger(ledger_path)
    rows = check_plan(book)
    if names:
        wanted = set(names)
        chosen = [u for u in rows if u.name in wanted]
    elif all_units:
        chosen = list(rows)
    else:
        chosen = [u for u in rows if u.stale]
    skipped = [u for u in rows if u not in chosen]
    results: List[Dict[str, object]] = []
    started = time.monotonic()
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
            "seconds": Fraction(0),
            "results": tuple(results),
        }

    lock = threading.Lock()

    def one(unit: CheckUnit) -> Dict[str, object]:
        outcome = _run_one(unit.check, exhaustive=exhaustive)
        with lock:
            # written after every instrument, so an interrupted run keeps the
            # signatures it has already earned (directive D1)
            _sign_check(unit, outcome, book)
            L.save_ledger(book, ledger_path)
        return {"name": unit.name, "state": unit.state, **outcome}

    workers = max(1, int(jobs))
    if workers == 1 or len(chosen) <= 1:
        results = [one(unit) for unit in chosen]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(one, chosen))
    elapsed = time.monotonic() - started
    L.save_ledger(book, ledger_path)
    return {
        "ran": len(chosen),
        "skipped": len(skipped),
        "skipped_names": tuple(u.name for u in skipped),
        "failed": tuple(r["name"] for r in results
                        if r.get("status") == "failed"),
        "jobs": workers,
        "seconds": Fraction(int(elapsed * 1000), 1000),
        "results": tuple(results),
    }


def verify_checks(ledger_path: Optional[Path] = None) -> Dict[str, object]:
    """Re-check every instrument's signature without running anything."""
    rows = check_plan(L.load_ledger(ledger_path))
    signed = [u.name for u in rows if u.state == "signed"]
    return {
        "units": len(rows),
        "signed": len(signed),
        "signed_names": tuple(signed),
        "new": tuple(u.name for u in rows if u.state == "new"),
        "changed": tuple(u.name for u in rows if u.state == "changed"),
        "failed": tuple(u.name for u in rows if u.state == "failed"),
        "all_signed": len(signed) == len(rows),
        "interpreter": L.interpreter_tag(),
        "schema": L.SCHEMA,
    }


def predicted_check_saving(units: Optional[Sequence[CheckUnit]] = None
                           ) -> Dict[str, object]:
    """How much the ledger saves on the instruments, from recorded times.

    An instrument that has never run contributes its declared estimate, and is
    named separately so the figure is never quietly optimistic.
    """
    rows = list(units if units is not None else check_plan())
    signed = [u for u in rows if not u.stale]
    stale = [u for u in rows if u.stale]

    def total(group: Sequence[CheckUnit]) -> Fraction:
        out = Fraction(0)
        for unit in group:
            seconds = unit.last_seconds
            out += (seconds if seconds is not None
                    else Fraction(unit.check.expected_seconds))
        return out

    saved = total(signed)
    to_run = total(stale)
    whole = saved + to_run
    return {
        "units": len(rows),
        "signed": len(signed),
        "stale": len(stale),
        "seconds_saved": saved,
        "seconds_to_run": to_run,
        "seconds_full_run": whole,
        "fraction_saved": (saved / whole) if whole else Fraction(0),
        "units_without_timing": tuple(u.name for u in rows
                                      if u.last_seconds is None),
    }

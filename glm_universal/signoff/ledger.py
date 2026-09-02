"""The sign-off ledger: dependency closures, digests, and the run plan.

Every function here is pure except :func:`run_plan` and :func:`save_ledger`.
Nothing imports the modules it hashes -- the closure is computed from the
source with :mod:`ast`, so hashing a module cannot execute it.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from ..integrity import sha256_hex

#: The package root, ``.../overlay/glm_universal``.
PACKAGE_ROOT = Path(__file__).resolve().parent.parent

#: The directory holding the package, ``.../overlay``.
PROJECT_ROOT = PACKAGE_ROOT.parent

#: Where the ledger lives.  Beside the package, not inside it, because it is a
#: record of runs rather than part of the library.
LEDGER_PATH = PROJECT_ROOT / ".glm_signoff.json"

#: The suite totals, alone, in their own file.  The ledger changes whenever
#: anything is signed, so a document check that depended on the ledger would
#: be stale after every run and never reach a fixed point.  This sidecar holds
#: only the three counts, so it moves when the counts move and at no other
#: time, which is what lets ``figures`` depend on it.
TOTALS_PATH = PROJECT_ROOT / ".glm_suite_totals.json"

#: Bumped whenever the meaning of a digest changes.  A ledger written under an
#: older schema signs nothing.
SCHEMA = 3

TESTS_DIR = PACKAGE_ROOT / "tests"

#: The environment variable that turns the exhaustive cases on.  A unit run
#: without it is signed in ``"fast"`` mode and does not satisfy a release
#: check; see :mod:`glm_universal.signoff` and ``overlay/conftest.py``.
EXHAUSTIVE_ENV = "GLM_EXHAUSTIVE"

#: How many test files to run at once by default.  The suite is independent
#: per file, so this is close to free; capped so a large machine does not
#: start fifty interpreters that then contend for memory.
try:  # pragma: no cover - platform dependent
    DEFAULT_JOBS = max(1, min(8, len(os.sched_getaffinity(0))))
except AttributeError:  # pragma: no cover - not Linux
    DEFAULT_JOBS = max(1, min(8, os.cpu_count() or 1))


# ===========================================================================
#  Digests
# ===========================================================================

def _hasher():
    """An incremental SHA-256, borrowed from :mod:`glm_universal.integrity`.

    The digest itself is defined in one place; this is the streaming form of
    it, used where a digest is accumulated over many files.
    """
    import hashlib as _hashlib  # local: the core may not import hashlib at all

    return _hashlib.sha256()


#: Digests already computed in this process, keyed by path, modification time
#: and size.  A closure is walked once per unit and the units share most of
#: their files, so without this the plan hashes the same megabyte forty times.
#: The key includes the stamp, so an edit during a run is still seen.
_file_digest_cache: Dict[Tuple[str, int, int], str] = {}


def file_digest(path: Path) -> str:
    """SHA-256 of one file's bytes."""
    resolved = Path(path)
    try:
        stat = resolved.stat()
        key = (str(resolved), stat.st_mtime_ns, stat.st_size)
    except OSError:  # pragma: no cover - defensive
        return sha256_hex(resolved.read_bytes())
    cached = _file_digest_cache.get(key)
    if cached is None:
        cached = sha256_hex(resolved.read_bytes())
        _file_digest_cache[key] = cached
    return cached


def tree_digest(paths: Iterable[Path], root: Optional[Path] = None) -> str:
    """A canonical digest of a set of files.

    Sorted by path relative to ``root`` so the result does not depend on the
    order they were discovered in, and each path is hashed alongside its
    content so that a rename is a change.
    """
    base = root or PROJECT_ROOT
    entries = sorted({Path(p).resolve() for p in paths})
    h = _hasher()
    for path in entries:
        try:
            relative = path.relative_to(base)
        except ValueError:
            relative = path
        h.update(str(relative).encode("utf-8"))
        h.update(b"\0")
        h.update(file_digest(path).encode("ascii"))
        h.update(b"\0")
    return h.hexdigest()


def interpreter_tag() -> str:
    """The interpreter a signature is valid for."""
    return f"python{sys.version_info.major}.{sys.version_info.minor}." \
           f"{sys.version_info.micro}"


# ===========================================================================
#  Dependency closure
# ===========================================================================

def _module_path(dotted: str) -> Optional[Path]:
    """The file implementing ``glm_universal.a.b``, without importing it."""
    if dotted == "glm_universal":
        return PACKAGE_ROOT / "__init__.py"
    if not dotted.startswith("glm_universal."):
        return None
    parts = dotted.split(".")[1:]
    candidate = PACKAGE_ROOT.joinpath(*parts).with_suffix(".py")
    if candidate.is_file():
        return candidate
    package = PACKAGE_ROOT.joinpath(*parts) / "__init__.py"
    if package.is_file():
        return package
    return None


_imports_cache: Dict[Tuple[str, int], Set[str]] = {}


def _imports_of(path: Path) -> Set[str]:
    """The ``glm_universal`` modules one file imports, relative ones resolved."""
    try:
        key = (str(path), path.stat().st_mtime_ns)
    except OSError:  # pragma: no cover - defensive
        key = (str(path), 0)
    cached = _imports_cache.get(key)
    if cached is not None:
        return set(cached)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    # the dotted name of the module this file implements
    relative = path.resolve().relative_to(PACKAGE_ROOT)
    parts = list(relative.parts)
    if parts[-1] == "__init__.py":
        own = ["glm_universal"] + parts[:-1]
    else:
        own = ["glm_universal"] + parts[:-1] + [parts[-1][:-3]]
    found: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("glm_universal"):
                    found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # a relative import: climb ``level - 1`` packages from the
                # package containing this module
                base = own[:-1]
                climb = node.level - 1
                if climb:
                    base = base[:-climb] if climb <= len(base) else []
                prefix = ".".join(base + ([node.module] if node.module else []))
            else:
                prefix = node.module or ""
            if not prefix.startswith("glm_universal"):
                continue
            found.add(prefix)
            for alias in node.names:
                found.add(f"{prefix}.{alias.name}")
    _imports_cache[key] = set(found)
    return found


_scaffolding_cache: Optional[Tuple[Path, ...]] = None


def scaffolding_paths() -> Tuple[Path, ...]:
    """Files that belong in every closure: the harness itself.

    A change to the test package's ``__init__`` or to any ``conftest.py``
    changes how every test runs, so it must invalidate every signature.  The
    modules that *define the rule* are included too -- ``signoff/__init__.py``
    and this file: if what counts as a dependency changes, no old signature is
    trustworthy.

    Two files of this package are deliberately **not** here.  ``__main__.py``
    is a command line and ``checks.py`` describes the non-pytest instruments;
    neither can change what a test file observes, and including them would
    have meant that adding an instrument invalidated all fifty test units for
    nothing.  ``checks.py`` is of course in every *instrument's* closure, and a
    test file that imports either one picks it up as an ordinary import.
    """
    global _scaffolding_cache
    if _scaffolding_cache is not None:
        return _scaffolding_cache
    out: List[Path] = []
    init = TESTS_DIR / "__init__.py"
    if init.is_file():
        out.append(init)
    out.extend(sorted(PROJECT_ROOT.rglob("conftest.py")))
    for name in ("__init__.py", "ledger.py"):
        rule = PACKAGE_ROOT / "signoff" / name
        if rule.is_file():
            out.append(rule)
    _scaffolding_cache = tuple(out)
    return _scaffolding_cache


def _data_files_for(paths: Iterable[Path]) -> Tuple[Path, ...]:
    """Frozen data files reachable from a set of modules.

    Any ``_data`` directory sitting beside a module in the closure is hashed
    whole.  Coarse on purpose: over-hashing costs a re-run, under-hashing costs
    a wrong answer.
    """
    directories = set()
    for path in paths:
        candidate = Path(path).resolve().parent / "_data"
        if candidate.is_dir():
            directories.add(candidate)
    out: List[Path] = []
    for directory in sorted(directories):
        out.extend(sorted(p for p in directory.rglob("*") if p.is_file()))
    return tuple(out)


# ---------------------------------------------------------------------------
#  Documents and Lean sources
# ---------------------------------------------------------------------------
#
#  A test file's result can depend on a file that is not Python at all.
#  ``tests/test_figures.py`` reads ``STATUS.md`` and ``MASTER_PLAN.md`` and
#  fails when a count in them goes stale; ``reasoning/pipeline.py`` reads the
#  study documents and the Lean sources to decide which stage each study has
#  reached; ``reasoning/lean_address.py`` reads every ``.lean`` file in the
#  development.  None of that is an import, so none of it was in the closure,
#  and a signature that ignores it is wrong in the one direction that matters:
#  it would keep a document check signed off after the document changed.
#
#  The dependency is *computed*, as everything here is.  Each module in the
#  closure is parsed and its string constants are read; a constant naming a
#  document (``"MASTER_PLAN.md"``) pulls that document in, and a constant
#  naming a Lean file or a ``*.lean`` glob pulls in the whole Lean development.
#  Over-hashing is deliberate (directive D4): resolving by name pulls in every
#  file of that name, and one ``.lean`` mention pulls in all of them, because a
#  needless re-run is cheap and a missed one is a wrong answer.

#: The repository root -- the directory holding ``overlay/``.
REPOSITORY_ROOT = PROJECT_ROOT.parent

#: Non-source files that can be a dependency, by suffix.
DOCUMENT_SUFFIXES = (".md", ".txt")

#: Where the Lean development lives: the repository copy and the overlay's.
LEAN_ROOTS = (REPOSITORY_ROOT / "RequestProject", PROJECT_ROOT / "glm_lean")

#: Build files that decide what ``lake build`` does.
LEAN_MANIFEST_NAMES = ("lakefile.toml", "lean-toolchain", "lake-manifest.json")

_SKIP_DIRECTORIES = frozenset({".git", ".lake", "__pycache__", ".pytest_cache",
                               "node_modules", ".ipynb_checkpoints"})

#: Nothing this large is a document; the repository also holds archives.
_MAX_DOCUMENT_BYTES = 4 * 1024 * 1024


def _walk(root: Path, suffixes: Sequence[str]) -> List[Path]:
    """Files under ``root`` with one of ``suffixes``, skipping caches."""
    out: List[Path] = []
    if not root.is_dir():
        return out
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir())
        except OSError:  # pragma: no cover - defensive
            continue
        for entry in entries:
            if entry.is_dir():
                if entry.name not in _SKIP_DIRECTORIES:
                    stack.append(entry)
            elif entry.suffix in suffixes:
                out.append(entry)
    return sorted(out)


_document_index_cache: Optional[Dict[str, Tuple[Path, ...]]] = None


def document_index() -> Dict[str, Tuple[Path, ...]]:
    """Every document in the repository, indexed by file name.

    A module names a document the way a reader does -- ``"STATUS.md"`` -- so
    the index is by base name, and a name that occurs more than once (several
    ``README.md``) maps to all of them.
    """
    global _document_index_cache
    if _document_index_cache is not None:
        return _document_index_cache
    index: Dict[str, List[Path]] = {}
    for path in _walk(REPOSITORY_ROOT, DOCUMENT_SUFFIXES):
        try:
            if path.stat().st_size > _MAX_DOCUMENT_BYTES:
                continue
        except OSError:  # pragma: no cover - defensive
            continue
        index.setdefault(path.name, []).append(path.resolve())
    _document_index_cache = {name: tuple(sorted(paths))
                             for name, paths in index.items()}
    return _document_index_cache


_lean_sources_cache: Optional[Tuple[Path, ...]] = None


def lean_sources() -> Tuple[Path, ...]:
    """The Lean development: every ``.lean`` file, and the build files.

    Both copies -- the repository's ``RequestProject/`` and the overlay's
    ``glm_lean/`` -- are included, because the tests that read Lean read one or
    the other and the two are meant to stay identical.
    """
    global _lean_sources_cache
    if _lean_sources_cache is not None:
        return _lean_sources_cache
    out: List[Path] = []
    for root in LEAN_ROOTS:
        out.extend(_walk(root, (".lean",)))
    for name in LEAN_MANIFEST_NAMES:
        candidate = REPOSITORY_ROOT / name
        if candidate.is_file():
            out.append(candidate)
    _lean_sources_cache = tuple(sorted(p.resolve() for p in out))
    return _lean_sources_cache


_constants_cache: Dict[Tuple[str, int], Tuple[str, ...]] = {}


def _string_constants(path: Path) -> Tuple[str, ...]:
    """Every string literal in a source file, without importing it."""
    try:
        key = (str(path), path.stat().st_mtime_ns)
    except OSError:  # pragma: no cover - defensive
        key = (str(path), 0)
    cached = _constants_cache.get(key)
    if cached is not None:
        return cached
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError, OSError):  # pragma: no cover
        _constants_cache[key] = ()
        return ()
    found = {node.value for node in ast.walk(tree)
             if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    out = tuple(sorted(found))
    _constants_cache[key] = out
    return out


def referenced_documents(paths: Iterable[Path]) -> Tuple[Path, ...]:
    """Documents and Lean sources named by the string constants of ``paths``.

    A docstring that merely *mentions* a document counts the same as a line
    that opens one: the parse does not distinguish them, and neither does this.
    That is the safe direction.
    """
    index = document_index()
    out: Set[Path] = set()
    wants_lean = False
    for path in paths:
        source = Path(path)
        if source.suffix != ".py":
            continue
        for constant in _string_constants(source):
            for token in constant.replace("\\", "/").split():
                name = token.rsplit("/", 1)[-1].strip("'\"()[],;:`")
                if name.endswith(".lean"):
                    wants_lean = True
                elif name in index:
                    out.update(index[name])
    if wants_lean:
        out.update(lean_sources())
    return tuple(sorted(out))


def unit_closure(test_path: Path) -> Tuple[Path, ...]:
    """Every file a test file's result depends on, sorted.

    Computed by walking imports from the test file through the package, then
    adding the data files, the documents and Lean sources those modules name,
    and the scaffolding.
    """
    test_path = Path(test_path).resolve()
    seen: Set[Path] = {test_path}
    frontier: List[Path] = [test_path]
    while frontier:
        current = frontier.pop()
        try:
            imports = _imports_of(current)
        except (SyntaxError, UnicodeDecodeError):  # pragma: no cover - defensive
            continue
        for dotted in imports:
            resolved = _module_path(dotted)
            if resolved is None:
                # ``from x import name`` where ``name`` is not a module
                continue
            resolved = resolved.resolve()
            if resolved not in seen:
                seen.add(resolved)
                frontier.append(resolved)
    seen.update(p.resolve() for p in _data_files_for(seen))
    seen.update(p.resolve() for p in referenced_documents(tuple(seen)))
    seen.update(p.resolve() for p in scaffolding_paths())
    return tuple(sorted(seen))


def unit_digest(test_path: Path) -> str:
    """The signature of a test file: its closure, the schema, the interpreter."""
    closure = unit_closure(test_path)
    h = _hasher()
    h.update(f"schema={SCHEMA}\0".encode("ascii"))
    h.update(f"python={interpreter_tag()}\0".encode("ascii"))
    h.update(tree_digest(closure).encode("ascii"))
    return h.hexdigest()


def test_units() -> Tuple[Path, ...]:
    """Every test file of the suite, in a stable order."""
    if not TESTS_DIR.is_dir():
        return ()
    return tuple(sorted(TESTS_DIR.glob("test_*.py")))


#: The test files whose subject is the documentation, excluded from the
#: recorded suite totals.  See :func:`counted_units` for why.
DOCUMENT_CHECKS: Tuple[str, ...] = ("test_figures.py",)


def counted_units() -> Tuple[Path, ...]:
    """The units the recorded totals are measured over: the suite, minus
    the file that checks the documents.

    Every unit is *run* -- nothing here excuses a test -- but
    ``tests/test_figures.py`` is not *counted*, and that one subtraction is
    what makes the totals reachable in a single pass.

    The reason is a loop.  The totals below are quoted in the documents;
    ``test_figures.py`` checks the documents; so its own number of checks
    depends on what the documents say, and what the documents say depends on
    the totals.  Rewriting a digit inside a sentence that already exists left
    the number of checks alone and converged in one run, but *adding* a
    documented sentence -- a new document, a phrase appearing, a skipped test
    now running -- moved this file's subtest count, which moved the totals,
    which were themselves quoted, and that needed a second complete run to
    certify what the first one learned.

    Excluding the document check removes the loop by construction rather than
    by care: nothing the documentation says can move a number the
    documentation quotes, because the file that reads the documentation is not
    in the count.  What the totals now state is the suite's coverage of the
    *package*, which is the figure a reader wanted from them anyway, and the
    generated sentence says which file was left out.
    """
    excluded = set(DOCUMENT_CHECKS)
    return tuple(p for p in test_units() if p.name not in excluded)


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
#  Running
# ===========================================================================

def _parse_pytest_summary(text: str) -> Dict[str, int]:
    """Counts out of pytest's last line: passed, failed, errors, subtests."""
    out = {"passed": 0, "failed": 0, "errors": 0, "subtests": 0}
    for line in reversed(text.strip().splitlines()):
        if " passed" in line or " failed" in line or " error" in line:
            words = line.replace("=", " ").split()
            for index, word in enumerate(words):
                if not word.isdigit():
                    continue
                count = int(word)
                label = words[index + 1] if index + 1 < len(words) else ""
                if label.startswith("subtest"):
                    # ``24 passed, 33 subtests passed in 1.52s``
                    out["subtests"] += count
                elif label.startswith("passed"):
                    if index + 2 < len(words) and words[index + 2].startswith(
                            "subtest"):
                        out["subtests"] += count
                    else:
                        out["passed"] += count
                elif label.startswith("failed"):
                    out["failed"] += count
                elif label.startswith("error"):
                    out["errors"] += count
            break
    return out


def run_environment(exhaustive: bool) -> Dict[str, str]:
    """The environment a unit runs in: this one, plus the exhaustive switch."""
    env = dict(os.environ)
    if exhaustive:
        env[EXHAUSTIVE_ENV] = "1"
    else:
        env.pop(EXHAUSTIVE_ENV, None)
    return env


def _run_one(path: Path, quiet: bool = True,
             exhaustive: bool = False) -> Dict[str, object]:
    """Run one test file under pytest and report what happened."""
    started = time.monotonic()
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", str(path), "-q", "--no-header"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
        env=run_environment(exhaustive))
    elapsed = time.monotonic() - started
    summary = _parse_pytest_summary(completed.stdout + completed.stderr)
    if not quiet:
        print(completed.stdout[-2000:])
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "milliseconds": int(elapsed * 1000),
        "tests": summary["passed"],
        "failures": summary["failed"] + summary["errors"],
        "subtests": summary["subtests"],
        "mode": "full" if exhaustive else "fast",
        "output_tail": (completed.stdout + completed.stderr)[-800:],
    }


def sign(unit: Unit, outcome: Mapping[str, object],
         ledger: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    """Record one outcome against the digest it was obtained at.

    A failure is recorded too -- with its status -- so that the unit stays
    stale until it passes.  Only ``status == "passed"`` counts as a signature.
    """
    book = ledger if ledger is not None else load_ledger()
    units = book.setdefault("units", {})
    units[unit.name] = {
        "digest": unit.digest,
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
    elapsed = time.monotonic() - started
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
        "seconds": Fraction(int(elapsed * 1000), 1000),
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

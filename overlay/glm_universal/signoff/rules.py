"""What a signature *means*: the closure, the digest, and how a unit is run.

This module is the rule. :mod:`glm_universal.signoff.ledger` is the record —
the plan, the runner, the stored book of signatures and the suite totals — and
that split is not cosmetic. Every unit's closure contains the files that
*define* what a dependency is, because if the rule changes no old signature is
trustworthy; so whatever lives here invalidates the whole suite when it is
edited. Reporting, planning and command-line prose change far more often than
the rule does, and before the split they sat in the same file and cost a full
re-run every time. Keeping them out of this module is what makes a round that
improves the *reporting* cost nothing.

What belongs here, and nowhere else:

* the digest of a file and of a set of files, and the interpreter tag;
* the dependency closure — imports, frozen data, the documents and Lean
  sources a module names, and the scaffolding;
* the signature of a unit computed from that closure;
* how a unit is actually run, since a test run under a different command or a
  different environment is a different observation.

Everything here is pure except :func:`run_one`. Nothing imports the modules it
hashes — the closure is computed from the source with :mod:`ast`, so hashing a
module cannot execute it.
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

    The modules that *define the rule* are included too -- ``__init__.py`` of
    this package and ``rules.py``, this file: if what counts as a dependency,
    what a digest covers, or how a unit is run changes, no old signature is
    trustworthy.

    Three files of this package are deliberately **not** here. ``ledger.py``
    is the record -- the plan, the runner's bookkeeping, the stored
    signatures and the suite totals -- ``__main__.py`` is a command line, and
    ``checks.py`` describes the non-pytest instruments; none of them can
    change what a test file observes, and including them would have meant
    that improving a *report* invalidated all 96 test units for nothing.
    ``checks.py`` is of course in every *instrument's* closure, and a test
    file that imports any of them picks it up as an ordinary import.
    """
    global _scaffolding_cache
    if _scaffolding_cache is not None:
        return _scaffolding_cache
    out: List[Path] = []
    init = TESTS_DIR / "__init__.py"
    if init.is_file():
        out.append(init)
    out.extend(sorted(PROJECT_ROOT.rglob("conftest.py")))
    for name in ("__init__.py", "rules.py"):
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
#  naming a Lean file pulls that file in -- in both copies, since the two are
#  meant to be identical.  Over-hashing is still the safe direction (directive
#  D4): resolving by name pulls in every file of that name, a ``*.lean`` glob
#  or a name the development does not hold pulls in the whole development, and
#  the Lean instruments hash it whole regardless.
#
#  Naming *one* file used to pull in *all* of them, and that single line was
#  what stopped the ledger being incremental in practice: a docstring in
#  ``reasoning/wobble.py`` mentioning ``Sturmian.lean`` put all 235 Lean files
#  into the closure of every unit that reaches it, so editing any Lean file
#  re-ran almost the whole suite.  A named file is now hashed as itself.

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


_lean_index_cache: Optional[Dict[str, Tuple[Path, ...]]] = None

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


def _path_in_repository(token: str) -> Optional[Path]:
    """``token`` read as a path from the repository root, if it is one.

    Only a token with a directory in it is tried: a bare ``"README.md"`` is a
    name, not a path, and resolving it against the root would silently mean
    the root's own copy.
    """
    if "/" not in token or token.startswith("/") or ".." in token:
        return None
    for root in (REPOSITORY_ROOT, PROJECT_ROOT):
        candidate = root / token
        try:
            if candidate.is_file():
                return candidate.resolve()
        except OSError:  # pragma: no cover - defensive
            continue
    return None


def lean_index() -> Dict[str, Tuple[Path, ...]]:
    """The Lean development indexed by file name, both copies under each name.

    A module names a Lean file the way a reader does -- ``"Sturmian.lean"``,
    or ``"Semantics/Meaning.lean"`` -- so the index is by base name and each
    name maps to the repository's copy and the overlay's mirror of it.
    """
    global _lean_index_cache
    if _lean_index_cache is not None:
        return _lean_index_cache
    index: Dict[str, List[Path]] = {}
    for path in lean_sources():
        if path.suffix == ".lean":
            index.setdefault(path.name, []).append(path)
    _lean_index_cache = {name: tuple(sorted(paths))
                         for name, paths in index.items()}
    return _lean_index_cache


def referenced_documents(paths: Iterable[Path]) -> Tuple[Path, ...]:
    """Documents and Lean sources named by the string constants of ``paths``.

    A docstring that merely *mentions* a document counts the same as a line
    that opens one: the parse does not distinguish them, and neither does this.
    That is the safe direction.

    A Lean file is resolved to itself, in both copies.  A ``*.lean`` glob --
    what a module that walks the development writes -- and a Lean name the
    development does not hold both pull in the whole development, because
    neither can be resolved to a particular file.
    """
    index = document_index()
    lean = lean_index()
    out: Set[Path] = set()
    wants_lean = False
    for path in paths:
        source = Path(path)
        if source.suffix != ".py":
            continue
        for constant in _string_constants(source):
            for token in constant.replace("\\", "/").split():
                cleaned = token.strip("'\"()[],;:`")
                name = cleaned.rsplit("/", 1)[-1]
                if name.endswith(".lean"):
                    #  Both copies, whether the token was a bare name or a
                    #  path: the mirror is generated from the repository copy
                    #  and a test may read either, so a dependency on one is
                    #  a dependency on both.
                    if name in lean:
                        out.update(lean[name])
                    else:
                        wants_lean = True
                elif name in index:
                    #  A document token written as a path --
                    #  ``"studies/RECIPE_STUDY.md"``,
                    #  ``"glm_universal/tests/README.md"`` -- names one file,
                    #  and resolving it as a path is exact where resolving it
                    #  by base name would pull in every file of that name.
                    #  Fifteen READMEs share a name, so that distinction is
                    #  most of what a document edit costs.
                    exact = _path_in_repository(cleaned)
                    if exact is not None:
                        out.add(exact)
                    else:
                        out.update(index[name])
    if wants_lean:
        out.update(lean_sources())
    return tuple(sorted(out))


def unit_closure(test_path: Path, include_documents: bool = True
                 ) -> Tuple[Path, ...]:
    """Every file a test file's result depends on, sorted.

    Computed by walking imports from the test file through the package, then
    adding the data files, the documents and Lean sources those modules name,
    and the scaffolding.

    ``include_documents=False`` drops the documents and the Lean sources from
    the closure, leaving the code and the frozen data.  A *test* is never
    closed that way -- a test that reads a document depends on it -- but a
    **derivation** that reads no document is keyed more tightly without it,
    which is what :func:`code_store` asks for: editing
    a study should not invalidate a cache the study cannot reach.
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
    if include_documents:
        seen.update(p.resolve() for p in referenced_documents(tuple(seen)))
    seen.update(p.resolve() for p in scaffolding_paths())
    return tuple(sorted(seen))


def code_store(name: str, module_file: str, schema: int = 1,
               root: Optional[Path] = None):
    """A derived store keyed on the **import closure of one module**, code only.

    The inputs are computed rather than listed: every module of this package
    that ``module_file`` reaches, transitively, plus the frozen data those
    modules read, taken from :func:`unit_closure` with the documents left out.
    So a derivation stored this way is reused exactly when none of the code or
    data it could have read has changed, and recomputed on the first byte that
    moves -- the sign-off discipline, applied to a report instead of to a test.

    This factory lives here rather than in :mod:`glm_universal.derived`
    because it is the *ledger's* notion of a closure; keeping it here also
    keeps the document closure of a unit that imports ``derived`` free of the
    documents this module's prose names.
    """
    from ..derived import DerivedStore

    def inputs() -> Iterable[Path]:
        return unit_closure(Path(module_file), include_documents=False)

    return DerivedStore(name, inputs, schema=schema, root=root)


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
    started = time.monotonic_ns()
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", str(path), "-q", "--no-header"],
        cwd=str(PROJECT_ROOT), capture_output=True, text=True,
        env=run_environment(exhaustive))
    elapsed_ms = (time.monotonic_ns() - started) // 1_000_000
    summary = _parse_pytest_summary(completed.stdout + completed.stderr)
    if not quiet:
        print(completed.stdout[-2000:])
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "milliseconds": elapsed_ms,
        "tests": summary["passed"],
        "failures": summary["failed"] + summary["errors"],
        "subtests": summary["subtests"],
        "mode": "full" if exhaustive else "fast",
        "output_tail": (completed.stdout + completed.stderr)[-800:],
    }


# ===========================================================================
#  Why a unit is stale, and what an edit would cost
# ===========================================================================
#
#  A digest answers "has anything moved?" and nothing else.  That is the right
#  question for correctness and the wrong one for a session: told that 75 of
#  96 units are stale, the only thing left to do is run them.  Two cheaper
#  questions are answerable from the same closure.
#
#  The first is asked *afterwards*: which **kind** of file moved.  The closure
#  splits into five disjoint groups, a digest is kept per group, and the plan
#  reports the groups that no longer match.  "documents" means a prose edit
#  and the unit will pass; "code" means it might not.
#
#  The second is asked *before* the edit: :func:`units_touching` inverts the
#  closure relation and says which units an edit to one file would invalidate,
#  so the cost of touching ``PROJECT_DIRECTIVES.md`` is known without touching
#  it.  Both are directive D15 applied to the gate itself: report the cost
#  rather than pay it silently.

#: The kinds of file a closure holds, in the order a member is classified.
#: The order is a priority: the scaffolding is scaffolding even when it is
#: also imported, and the group a file lands in never depends on which unit
#: is being reported.
CLOSURE_GROUPS: Tuple[str, ...] = ("scaffolding", "data", "documents", "lean",
                                   "code")


def closure_groups(test_path: Path, include_documents: bool = True
                   ) -> Dict[str, Tuple[Path, ...]]:
    """The closure of one unit, split into the five kinds of file it holds.

    The groups are disjoint and their union is exactly
    :func:`unit_closure` of the same unit, which is what makes a per-group
    digest a decomposition of the unit's signature rather than a second
    opinion about it.
    """
    members = set(unit_closure(test_path, include_documents=include_documents))
    scaffolding = {p.resolve() for p in scaffolding_paths()} & members
    remaining = members - scaffolding
    data = {p for p in remaining if "_data" in p.parts}
    remaining -= data
    lean = {p for p in remaining if p.suffix == ".lean"}
    remaining -= lean
    documents = {p for p in remaining if p.suffix != ".py"}
    code = remaining - documents
    groups = {"scaffolding": scaffolding, "data": data,
              "documents": documents, "lean": lean, "code": code}
    return {name: tuple(sorted(groups[name])) for name in CLOSURE_GROUPS}


def group_digests(test_path: Path) -> Dict[str, str]:
    """A digest per closure group, recorded beside a signature.

    Cheap — five hex strings per unit — and it is the whole of the "why": a
    stale unit is reported against the groups whose digest moved.
    """
    return {name: tree_digest(paths)
            for name, paths in closure_groups(test_path).items()}


def units_touching(target: Path,
                   units: Optional[Sequence[Path]] = None) -> Tuple[str, ...]:
    """The test units an edit to ``target`` would make stale.

    Exact rather than estimated: it is the same closure the signature is taken
    over, inverted.  A file no unit reaches returns the empty tuple, which is
    the honest answer that an edit to it costs nothing to re-verify.
    """
    resolved = Path(target).resolve()
    out: List[str] = []
    for unit in (units if units is not None else test_units()):
        if resolved in set(unit_closure(unit)):
            out.append(Path(unit).name)
    return tuple(out)

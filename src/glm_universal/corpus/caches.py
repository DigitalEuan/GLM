"""``glm_universal.corpus.caches`` -- every stored measurement, and whether it
still describes the code it was taken from.

The study modules, and one report module, keep a **measurement cache**: a JSON
file of figures that cost minutes to take, stored beside the digest of the
sources they were taken from, with a ``current()`` that returns the figures
when the digest still holds and ``None`` when it does not.  That is the right
discipline -- a stale measurement is refused rather than quoted -- but it was
only *discovered* by whatever happened to read it.  A round could change a
module, pass ``corpus --check`` in half a minute, and learn twenty minutes
later, from a failing end-to-end evaluation, that a cache it had never heard
of needed re-taking.

This module makes the census cheap and total: which caches exist, which are
current, and the exact command that re-takes each stale one.  ``--check`` runs
it and names them, in the same breath as everything else it names, and still
never pays for one (directive **D16**: report the cost, do not pay it inside a
check).

A cache whose figures are taken over the project's own corpus (the native
parity and native words studies) is current while its *code* is unchanged;
that the corpus has moved since is reported as a note, never as a failure,
because the corpus includes the documents that report the figures and gating
on it made every round's write-up invalidate its own measurements.

Both halves are **computed, not listed**:

* the caches are found by reading the sources of ``glm_universal/reasoning``
  for a module that defines both ``module_digest`` and ``current`` -- a module
  that grows a cache is in the census the moment it does;
* the command that re-takes each one is read out of ``glm_universal/tools.py``
  by resolving its top-level aliases and finding the sub-command whose handler
  calls ``<alias>.write_measurements()``.

So a new study with a cache, or a renamed sub-command, cannot leave a stale
figure with no way to find it.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
from typing import Dict, Optional, Tuple

#: ``.../glm_universal``.
PACKAGE_ROOT = Path(__file__).resolve().parent.parent

REASONING = PACKAGE_ROOT / "reasoning"

RUNTIME = PACKAGE_ROOT / "runtime"

#: Where a measurement cache may live: the study modules, then the report
#: modules.
CACHE_DIRECTORIES = (REASONING, RUNTIME)

#: The names a module may give the digest its stored figures are held to.
DIGESTS = frozenset({"module_digest", "source_digest"})

TOOLS = PACKAGE_ROOT / "tools.py"

__all__ = [
    "cache_census",
    "cache_states",
    "cached_modules",
    "commands_by_module",
    "module_path",
]


def _qualifies(path: Path) -> bool:
    """Does the source at ``path`` define a cache: a digest and ``current``?"""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):  # pragma: no cover - defensive
        return False
    names = {node.name for node in tree.body
             if isinstance(node, ast.FunctionDef)}
    return "current" in names and bool(names & DIGESTS)


def cached_modules() -> Tuple[str, ...]:
    """The modules that hold a measurement cache, by module name.

    A module qualifies when its source defines ``current`` (the figures, or
    ``None`` when the digest has moved) and a digest of what the figures were
    taken from (``module_digest``, or ``source_digest`` in a report module).
    Read with :mod:`ast`: nothing is imported to decide whether it belongs
    here.  A study module in ``reasoning`` is named by its stem; a report
    module in ``runtime`` by ``runtime.<stem>`` -- the AST index report of
    Phase 105 lives there, and the census missed it until Phase 115, so a
    change to a module it digests left it stale through the close's stage 0.
    """
    out = []
    for directory in CACHE_DIRECTORIES:
        for path in sorted(directory.glob("*.py")):
            if path.name.startswith("_") or not _qualifies(path):
                continue
            out.append(path.stem if directory == REASONING
                       else f"{directory.name}.{path.stem}")
    return tuple(out)


def module_path(name: str) -> Path:
    """The source file of a cached module named as :func:`cached_modules`
    names it."""
    if "." in name:
        package, stem = name.split(".", 1)
        return PACKAGE_ROOT / package / f"{stem}.py"
    return REASONING / f"{name}.py"


def _aliases_in(nodes) -> Dict[str, str]:
    """``qesc -> query_escalation`` for every alias of a study module.

    Half the handlers import their study at the top of the file and half
    inside the function, so both are read: a mapping built from only one of
    the two silently loses four of the ten caches.
    """
    aliases: Dict[str, str] = {}
    for node in nodes:
        if not isinstance(node, ast.ImportFrom):
            continue
        source = node.module or ""
        if source.endswith("reasoning"):
            prefix = ""
        elif source.endswith("runtime"):
            prefix = "runtime."
        else:
            continue
        for alias in node.names:
            aliases[alias.asname or alias.name] = prefix + alias.name
    return aliases


def _tools_aliases(tree: ast.Module) -> Dict[str, str]:
    """The aliases bound at the top level of ``tools.py``."""
    return _aliases_in(tree.body)


def _writer_handlers(tree: ast.Module, aliases: Dict[str, str]
                     ) -> Dict[str, str]:
    """``_queryesc -> query_escalation``: the handler that re-takes a cache."""
    out: Dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        local = dict(aliases)
        local.update(_aliases_in(ast.walk(node)))
        for inner in ast.walk(node):
            if (isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Attribute)
                    and inner.func.attr == "write_measurements"
                    and isinstance(inner.func.value, ast.Name)):
                module = local.get(inner.func.value.id)
                if module is not None:
                    out[node.name] = module
    return out


def _subcommands(tree: ast.Module) -> Dict[str, str]:
    """``_queryesc -> "queryesc"``: the sub-command each handler serves.

    Read off the two statements the parser is built with -- an
    ``add_parser("name")`` assigned to a variable, and a ``set_defaults`` on
    that variable naming the handler.
    """
    parser_names: Dict[str, str] = {}
    out: Dict[str, str] = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "add_parser"
                and node.value.args
                and isinstance(node.value.args[0], ast.Constant)):
            parser_names[node.targets[0].id] = str(node.value.args[0].value)
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "set_defaults"
                and isinstance(node.func.value, ast.Name)):
            for keyword in node.keywords:
                if keyword.arg == "handler" and isinstance(keyword.value,
                                                           ast.Name):
                    name = parser_names.get(node.func.value.id)
                    if name is not None:
                        out[keyword.value.id] = name
    return out


def commands_by_module() -> Dict[str, str]:
    """``query_escalation -> "queryesc"``: how each cache is re-taken."""
    tree = ast.parse(TOOLS.read_text(encoding="utf-8"), filename=str(TOOLS))
    aliases = _tools_aliases(tree)
    handlers = _writer_handlers(tree, aliases)
    commands = _subcommands(tree)
    return {module: commands[handler]
            for handler, module in handlers.items() if handler in commands}


def cache_states() -> Tuple[Dict[str, object], ...]:
    """One row per cache: is it current, and what re-takes it if it is not.

    ``current()`` is a read and a digest, not a measurement, so the whole
    census costs a fraction of a second.
    """
    commands = commands_by_module()
    rows = []
    for name in cached_modules():
        module = importlib.import_module(
            f"glm_universal.{name}" if "." in name
            else f"glm_universal.reasoning.{name}")
        # Read the file again rather than the module's memo: stage 0 of the
        # close re-takes a cache in a subprocess, and a census taken before
        # it had memoised the stale figures, so the re-taken cache was
        # reported "still stale" (Phase 109's close; fixed in Phase 110).
        reread = getattr(module, "measurements", None)
        if callable(reread):
            try:
                reread(refresh=True)
            except Exception:  # pragma: no cover - a cache that cannot be read
                pass
        try:
            fresh = module.current() is not None
        except Exception:  # pragma: no cover - a cache that cannot be read
            fresh = False
        command = commands.get(name)
        drift_of = getattr(module, "corpus_drift", None)
        try:
            drift = bool(drift_of()) if callable(drift_of) else False
        except Exception:  # pragma: no cover - a cache that cannot be read
            drift = False
        rows.append({
            "module": name,
            "fresh": fresh,
            "drift": drift,
            "command": command,
            "retake": (f"PYTHONPATH=. python3 -m glm_universal.tools "
                       f"{command} --write" if command else None),
        })
    return tuple(rows)


def cache_census() -> Dict[str, object]:
    """The census: how many caches, how many current, and which are not."""
    rows = cache_states()
    stale = tuple(row for row in rows if not row["fresh"])
    unreachable = tuple(row["module"] for row in rows
                        if row["command"] is None)
    return {
        "caches": len(rows),
        "fresh": len(rows) - len(stale),
        "stale": tuple(row["module"] for row in stale),
        "commands": tuple(row["retake"] for row in stale
                          if row["retake"] is not None),
        "without_a_command": unreachable,
        "holds": not stale and not unreachable,
        "rows": rows,
    }


def describe(census: Optional[Dict[str, object]] = None) -> Tuple[str, ...]:
    """The census as lines a command line can print."""
    report = census if census is not None else cache_census()
    lines = []
    for row in report["rows"]:
        if not row["fresh"]:
            retake = row["retake"] or "(no command re-takes it)"
            lines.append(f"measurement cache: {row['module']} is stale -- "
                         f"re-take it with `{retake}`")
    for row in report["rows"]:
        if row["fresh"] and row.get("drift"):
            retake = row["retake"] or "(no command re-takes it)"
            lines.append(f"note: measurement cache {row['module']} was taken "
                         f"over an earlier corpus -- current, not a failure; "
                         f"re-take it with `{retake}` only when the round "
                         f"wants fresh figures")
    for name in report["without_a_command"]:
        lines.append(f"measurement cache: {name} has no re-taking command "
                     f"in tools.py")
    return tuple(lines)

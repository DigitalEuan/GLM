"""``glm_universal.corpus.caches`` -- every stored measurement, and whether it
still describes the code it was taken from.

Ten study modules keep a **measurement cache**: a JSON file of figures that
cost minutes to take, stored beside the digest of the sources they were taken
from, with a ``current()`` that returns the figures when the digest still
holds and ``None`` when it does not.  That is the right discipline -- a stale
measurement is refused rather than quoted -- but it was only *discovered* by
whatever happened to read it.  A round could change a module, pass
``corpus --check`` in half a minute, and learn twenty minutes later, from a
failing end-to-end evaluation, that a cache it had never heard of needed
re-taking.

This module makes the census cheap and total: which caches exist, which are
current, and the exact command that re-takes each stale one.  ``--check`` runs
it and names them, in the same breath as everything else it names, and still
never pays for one (directive **D16**: report the cost, do not pay it inside a
check).

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

#: ``.../overlay/glm_universal``.
PACKAGE_ROOT = Path(__file__).resolve().parent.parent

REASONING = PACKAGE_ROOT / "reasoning"

TOOLS = PACKAGE_ROOT / "tools.py"

__all__ = [
    "cache_census",
    "cache_states",
    "cached_modules",
    "commands_by_module",
]


def cached_modules() -> Tuple[str, ...]:
    """The reasoning modules that hold a measurement cache, by module name.

    A module qualifies when its source defines both ``module_digest`` (the
    digest of what the figures were taken from) and ``current`` (the figures,
    or ``None`` when the digest has moved).  Read with :mod:`ast`: nothing is
    imported to decide whether it belongs here.
    """
    out = []
    for path in sorted(REASONING.glob("*.py")):
        if path.name.startswith("_"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError):  # pragma: no cover - defensive
            continue
        names = {node.name for node in tree.body
                 if isinstance(node, ast.FunctionDef)}
        if {"module_digest", "current"} <= names:
            out.append(path.stem)
    return tuple(out)


def _aliases_in(nodes) -> Dict[str, str]:
    """``qesc -> query_escalation`` for every alias of a study module.

    Half the handlers import their study at the top of the file and half
    inside the function, so both are read: a mapping built from only one of
    the two silently loses four of the ten caches.
    """
    aliases: Dict[str, str] = {}
    for node in nodes:
        if isinstance(node, ast.ImportFrom) and (node.module or "").endswith(
                "reasoning"):
            for alias in node.names:
                aliases[alias.asname or alias.name] = alias.name
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
        module = importlib.import_module(f"glm_universal.reasoning.{name}")
        try:
            fresh = module.current() is not None
        except Exception:  # pragma: no cover - a cache that cannot be read
            fresh = False
        command = commands.get(name)
        rows.append({
            "module": name,
            "fresh": fresh,
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
    for name in report["without_a_command"]:
        lines.append(f"measurement cache: {name} has no re-taking command "
                     f"in tools.py")
    return tuple(lines)

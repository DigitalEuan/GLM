#!/usr/bin/env python3
"""
The wiring audit — what is tested but not reached
=================================================

A standalone reading of the tree, not a measurement of the machine.  It
answers one question that no gate in the repository asks:

    *Which parts of the system have been written, tested and written up,
    but are not reached by anything the machine actually runs?*

It is deliberately outside ``glm_universal``.  Wiring is a property of the
package, so a module inside the package would make itself part of its own
answer, and — because a new module moves the module count, the blast-radius
table and the corpus digest — a one-off reading would cost a round.

Four readings, each independent
-------------------------------

1. **Reasoning modules no entry point imports.**  Build the import graph of
   the package, take the closure from every non-test entry point (the
   runtime, the CLI, the evaluation harness, the corpus and figure layers,
   the examples, the capability and benchmark surfaces), and report the
   ``reasoning/`` modules outside it.  A module reached only by its own test
   file is tested and not used.

   A second closure is taken that also follows module names appearing inside
   *string literals* of reached modules.  The receipt bodies in
   ``runtime/tct_engine.py`` are Python source emitted as text, so a module
   named only there is genuinely re-run — but only when a reader recomputes a
   receipt, never on the machine's own path.

2. **Sandbox occupants and their promotion checklists.**  Directive D14 keeps
   unpromoted work in ``glm_universal/sandbox/`` behind a *computed*
   checklist.  This reads each occupant's ``promotion_checklist()`` and
   reports which lines are false — that is the remaining implementation work,
   stated by the code rather than by prose.

3. **Figure keys registered and never quoted.**  Directive D6 requires every
   quoted figure to be generated.  The converse is not required and not
   checked: a key can be registered, recomputed on every release, and quoted
   in no document.  Those are measurements the machine takes and no reader
   sees.

4. **Lean files cited nowhere.**  Under D8 the Lean file is the
   specification, so a Lean module named in no document and no Python source
   is a specification with no reader.

Run it from the repository root::

    python3 studies/scripts/wiring_audit.py

It reads only; it writes nothing and imports nothing from the package except
the three sandbox occupants and the figure registry.
"""

from __future__ import annotations

import ast
import collections
import os
import re
import sys
from typing import Dict, Iterable, List, Sequence, Set, Tuple

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OVERLAY = os.path.join(REPO, "overlay")
PACKAGE = os.path.join(OVERLAY, "glm_universal")

#: Sub-packages the machine itself runs from.  ``reasoning`` is deliberately
#: absent: a reasoning module reached only by another reasoning module that
#: nothing runs is still unreached.
ENTRY_PACKAGES = (
    "benchmarks",
    "capabilities",
    "corpus",
    "data_objects",
    "derived",
    "evaluation",
    "examples",
    "figures",
    "integrity",
    "language",
    "migration",
    "recipe",
    "runtime",
    "semantics",
    "signoff",
    "substrate",
    "tools",
)

SKIP_DIRS = ("__pycache__", "_derived", "_data")

_STRING_REF = re.compile(
    r"glm_universal\.reasoning\.(\w+)|from glm_universal\.reasoning import (\w+)"
)


def _modules() -> Dict[str, str]:
    """Every module of the package, as ``dotted name -> path``."""
    found: Dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(PACKAGE):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            path = os.path.join(dirpath, filename)
            rel = os.path.relpath(path, PACKAGE)
            name = "glm_universal." + rel[: -len(".py")].replace(os.sep, ".")
            if name.endswith(".__init__"):
                name = name[: -len(".__init__")]
            found[name] = path
    return found


def _import_graph(
    modules: Dict[str, str], source: Dict[str, str]
) -> Dict[str, Set[str]]:
    """Targets each module imports, absolute and relative alike."""
    graph: Dict[str, Set[str]] = collections.defaultdict(set)
    for name, path in modules.items():
        tree = ast.parse(source[name])
        package = name if os.path.basename(path) == "__init__.py" else name.rsplit(".", 1)[0]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    graph[name].add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    base = package
                    for _ in range(node.level - 1):
                        base = base.rsplit(".", 1)[0]
                    target = base + ("." + node.module if node.module else "")
                else:
                    target = node.module or ""
                graph[name].add(target)
                for alias in node.names:
                    graph[name].add(target + "." + alias.name)
    return graph


def _is_entry(name: str) -> bool:
    parts = name.split(".")
    return len(parts) > 1 and parts[1] in ENTRY_PACKAGES


def _closure(
    start: Iterable[str],
    modules: Dict[str, str],
    graph: Dict[str, Set[str]],
    extra=None,
) -> Set[str]:
    seen: Set[str] = set()
    stack: List[str] = list(start)
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        targets = set(graph.get(name, ()))
        if extra is not None:
            targets |= extra(name)
        for target in targets:
            if target in modules and target not in seen:
                stack.append(target)
    return seen


def _string_refs(source: str) -> Set[str]:
    return {
        "glm_universal.reasoning." + (a or b) for a, b in _STRING_REF.findall(source)
    }


def reasoning_reach() -> dict:
    """Reading 1 — reasoning modules outside the closure of the entry points."""
    modules = _modules()
    source = {
        name: open(path, encoding="utf-8").read() for name, path in modules.items()
    }
    graph = _import_graph(modules, source)
    entries = [name for name in modules if _is_entry(name)]

    imported = _closure(entries, modules, graph)
    recomputed = _closure(
        entries,
        modules,
        graph,
        extra=lambda name: (
            set() if name.startswith("glm_universal.tests") else _string_refs(source[name])
        ),
    )

    reasoning = sorted(
        name
        for name in modules
        if name.startswith("glm_universal.reasoning.") and name.count(".") == 2
    )
    tests = {n: s for n, s in source.items() if n.startswith("glm_universal.tests")}

    def has_test(short: str) -> bool:
        return any(re.search(r"\b" + short + r"\b", s) for s in tests.values())

    rows: List[Tuple[str, str, bool]] = []
    for name in reasoning:
        if name in imported:
            continue
        short = name.rsplit(".", 1)[1]
        how = "a recompute script only" if name in recomputed else "nothing but its tests"
        rows.append((short, how, has_test(short)))

    return {
        "modules": len(reasoning),
        "imported": len([n for n in reasoning if n in imported]),
        "unreached": rows,
    }


def sandbox_state() -> List[Tuple[str, bool, Sequence[str]]]:
    """Reading 2 — each sandbox occupant's computed promotion checklist."""
    sys.path.insert(0, OVERLAY)
    from glm_universal.sandbox import lean_generation, memory_split, planner  # noqa: E402

    rows: List[Tuple[str, bool, Sequence[str]]] = []
    for module in (planner, memory_split, lean_generation):
        report = module.promotion_checklist()
        checks = report["checks"]
        failing = tuple(name for name in report["order"] if not checks[name])
        rows.append((module.__name__.rsplit(".", 1)[1], bool(report["ready"]), failing))
    return rows


def figure_reach() -> dict:
    """Reading 3 — figure keys registered and never quoted in a document."""
    sys.path.insert(0, OVERLAY)
    from glm_universal.corpus import render  # noqa: E402

    registered = set(render.FIGURES)
    quoted: Set[str] = set()
    for dirpath, dirnames, filenames in os.walk(REPO):
        dirnames[:] = [
            d for d in dirnames if d not in (".git", "source_material", "__pycache__")
        ]
        for filename in filenames:
            if not filename.endswith(".md"):
                continue
            text = open(
                os.path.join(dirpath, filename), encoding="utf-8", errors="ignore"
            ).read()
            quoted |= set(re.findall(r"<!--figure:([a-z0-9-]+)-->", text))
    return {
        "registered": len(registered),
        "quoted": len(registered & quoted),
        "never_quoted": sorted(registered - quoted),
        "quoted_unregistered": sorted(quoted - registered),
    }


def lean_reach() -> dict:
    """Reading 4 — Lean modules named in no document and no Python source."""
    lean_root = os.path.join(REPO, "RequestProject")
    files: List[str] = []
    for dirpath, dirnames, filenames in os.walk(lean_root):
        dirnames[:] = [d for d in dirnames if d not in (".lake", "build")]
        files.extend(f[: -len(".lean")] for f in filenames if f.endswith(".lean"))

    prose: List[str] = []
    for dirpath, dirnames, filenames in os.walk(REPO):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in (".git", "source_material", "__pycache__", ".lake", "build")
        ]
        for filename in filenames:
            if filename.endswith(".md") or filename.endswith(".py"):
                prose.append(
                    open(
                        os.path.join(dirpath, filename), encoding="utf-8", errors="ignore"
                    ).read()
                )
    blob = "\n".join(prose)
    uncited = sorted({f for f in files if not re.search(r"\b" + f + r"\b", blob)})
    return {"files": len(files), "uncited": uncited}


def main() -> None:
    reach = reasoning_reach()
    print("1. reasoning modules")
    print(
        "   %d modules, %d reached by import from an entry point, %d not"
        % (reach["modules"], reach["imported"], len(reach["unreached"]))
    )
    for short, how, tested in reach["unreached"]:
        print(
            "     %-16s reached by %-22s tested: %s"
            % (short, how, "yes" if tested else "no")
        )

    print("2. sandbox occupants")
    for name, ready, failing in sandbox_state():
        print("     %-16s ready: %-5s failing: %s" % (name, ready, ", ".join(failing)))

    figures = figure_reach()
    print("3. figure keys")
    print(
        "   %d registered, %d quoted, %d never quoted"
        % (figures["registered"], figures["quoted"], len(figures["never_quoted"]))
    )
    for key in figures["never_quoted"]:
        print("     " + key)
    if figures["quoted_unregistered"]:
        print("   quoted but not registered: " + ", ".join(figures["quoted_unregistered"]))

    lean = lean_reach()
    print("4. Lean files")
    print(
        "   %d files, %d named in no document and no Python source"
        % (lean["files"], len(lean["uncited"]))
    )
    for name in lean["uncited"]:
        print("     " + name)


if __name__ == "__main__":
    main()

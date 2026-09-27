"""``glm_universal.sandbox`` -- work that is not part of the shipped runtime yet.

A module lives here when it is worth running and not yet worth relying on.  The
rule of the directory is the whole of it:

* nothing the shipped package *computes with* may import from
  ``glm_universal.sandbox`` -- no runtime, reasoning, semantics or data module
  may depend on anything here, so removing this directory cannot change a
  single answer the system gives.  The declared exceptions are the
  documentation and instrument layers, and nothing else:
  :mod:`glm_universal.corpus.render` and :mod:`glm_universal.corpus.cost`
  import the planner lazily, inside the block that reports on it, because a
  study of the sandbox has to be able to recompute what it says about it, and
  ``glm_universal.tools`` runs it as a study instrument.  Those exceptions are
  checked in ``tests/test_sandbox_planner.py`` rather than trusted;
* everything here obeys the project's exactness rules anyway -- integers and
  :class:`~fractions.Fraction`, no random source, no digest that carries
  meaning -- because a sandbox that is allowed to cheat teaches nothing;
* each module here carries a **promotion checklist**, computed rather than
  asserted, saying exactly what would have to hold for it to be moved into the
  package proper.

There are three occupants:

* :mod:`glm_universal.sandbox.planner`, the reverse-call planner -- a
  problem-driven front end that inspects a problem and selects tools by
  precondition, rather than dispatching on a query kind decided before the
  problem is read;
* :mod:`glm_universal.sandbox.memory_split`, the supplied four-register memory
  split run over the conversation layer's own declared follow-ups and scored
  against licensing;
* :mod:`glm_universal.sandbox.lean_generation`, the supplied carrier-to-Lean
  generator with the real round trip in place of the supplied check.

:func:`occupancy_report` answers the directory's own question -- who lives
here, whose checklist says ready, and how many shipped modules import them --
by reading the checklists and the package's imports rather than by assertion.
"""

from __future__ import annotations

import ast
import os
from typing import Dict, Tuple

__all__ = ["planner", "memory_split", "lean_generation", "occupancy_report",
           "importing_modules", "computing_importers", "OCCUPANTS",
           "DECLARED_IMPORTERS", "COMPUTING_PACKAGES"]

#: The occupants, in the order they arrived.
OCCUPANTS: Tuple[str, ...] = ("planner", "memory_split", "lean_generation")

#: The declared exceptions to "nothing imports the sandbox": the documentation
#: layer, which has to be able to recompute what it reports, and the study
#: instrument that runs it.  The same three are pinned, and their laziness
#: checked, in ``tests/test_sandbox_planner.py``.
DECLARED_IMPORTERS: Tuple[str, ...] = ("corpus/cost.py", "corpus/render.py",
                                       "tools.py")

#: The sub-packages the system *computes answers with*.  No module of these
#: may import the sandbox under any exception.
COMPUTING_PACKAGES: Tuple[str, ...] = (
    "benchmarks", "capabilities", "data_objects", "evaluation", "language",
    "migration", "reasoning", "recipe", "runtime", "semantics", "substrate",
)

_PACKAGE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_PACKAGE)


def _package_sources() -> Tuple[str, ...]:
    """Every shipped ``.py`` of the package: not the sandbox, not the tests."""
    out = []
    for base, dirs, files in os.walk(_ROOT):
        dirs[:] = sorted(d for d in dirs
                         if d not in ("sandbox", "tests", "__pycache__"))
        for name in sorted(files):
            if name.endswith(".py"):
                out.append(os.path.relpath(os.path.join(base, name), _ROOT))
    return tuple(sorted(out))


def _imports_sandbox(path: str) -> bool:
    """Does this source name ``glm_universal.sandbox`` in an import?"""
    with open(os.path.join(_ROOT, path), "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[-1] == "sandbox"
                   or ".sandbox" in alias.name for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "sandbox" or module.endswith(".sandbox") \
                    or ".sandbox." in module or module.startswith("sandbox."):
                return True
            if any(alias.name == "sandbox" for alias in node.names):
                return True
    return False


def importing_modules() -> Tuple[str, ...]:
    """Shipped modules that import from here, declared exceptions aside."""
    declared = set(p.replace("/", os.sep) for p in DECLARED_IMPORTERS)
    return tuple(path for path in _package_sources()
                 if path not in declared and _imports_sandbox(path))


def computing_importers() -> Tuple[str, ...]:
    """Modules the system computes answers with that import from here.

    This one takes no exceptions: a documentation module may report on the
    sandbox, and a module that computes an answer may not read it at all.
    """
    return tuple(path for path in _package_sources()
                 if path.split(os.sep)[0] in COMPUTING_PACKAGES
                 and _imports_sandbox(path))


def occupancy_report() -> Dict[str, object]:
    """Who lives in the sandbox, which checklists pass, and who imports them.

    The three numbers the directory's own coarse read quotes -- how many
    modules are here, how many are ready to leave, and how many modules the
    system computes answers with import them -- are all computed: the first
    two from each occupant's ``promotion_checklist()``, the third from the
    package's import graph.
    """
    import importlib

    rows = []
    for name in OCCUPANTS:
        module = importlib.import_module(f"{__name__}.{name}")
        checklist = module.promotion_checklist()
        checks = checklist["checks"]
        rows.append({
            "module": name,
            "ready": bool(checklist["ready"]),
            "failing": tuple(key for key in checklist["order"]
                             if not checks[key]),
        })
    importers = importing_modules()
    computing = computing_importers()
    return {
        "occupants": tuple(rows),
        "modules": len(rows),
        "ready": sum(1 for row in rows if row["ready"]),
        "importers": importers,
        "importer_count": len(importers),
        "computing_importers": computing,
        "computing_importer_count": len(computing),
        "declared_importers": DECLARED_IMPORTERS,
        "rule": ("A module leaves the sandbox when its checklist is all true "
                 "and not before; nothing the system computes with may import "
                 "from here in the meantime."),
    }


def main() -> None:                                    # pragma: no cover
    report = occupancy_report()
    print(f"modules      {report['modules']}")
    print(f"ready        {report['ready']}")
    print(f"importers    {report['importer_count']} "
          f"({report['computing_importer_count']} that compute an answer)")
    for row in report["occupants"]:                    # type: ignore[union-attr]
        failing = ", ".join(row["failing"]) or "-"
        print(f"  {row['module']:<16} ready: {row['ready']!s:<5} "
              f"failing: {failing}")


if __name__ == "__main__":                             # pragma: no cover
    main()

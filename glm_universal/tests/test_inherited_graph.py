"""The inherited concept graph is evidence, and nothing else.

``glm_state.json`` -- 4,282 concepts and 4,015 CRG edges grown over 217
pipeline runs -- was audited in
:mod:`glm_universal.semantics.audit` and found to carry almost nothing about
its subjects.  The question the audit left open was what to *do* about that:
refine the graph until it earns its place, or delete it.

:func:`glm_universal.semantics.audit.retention_decision` records the answer --
demoted to evidence, kept but never consulted for an answer -- and this file
is what makes the second half of that sentence binding.  A decision recorded
only in prose is a decision that can be quietly reversed by an import; the
test below walks the imports.
"""

from __future__ import annotations

import ast
import os
import unittest
from typing import Dict, Set, Tuple

from glm_universal.semantics import audit

#: The module that reads the inherited state from disk.  Reaching it is the
#: thing being forbidden.
_STATE_MODULE = "glm_universal.migration.state"

#: ``glm_universal/`` on disk.
_PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _module_path(dotted: str) -> str:
    """The source file a dotted ``glm_universal.*`` name refers to."""
    relative = dotted.split(".")[1:]
    direct = os.path.join(_PACKAGE_ROOT, *relative) + ".py"
    if os.path.isfile(direct):
        return direct
    return os.path.join(_PACKAGE_ROOT, *relative, "__init__.py")


def _imports_of(dotted: str) -> Set[str]:
    """Every ``glm_universal.*`` module the source of ``dotted`` imports.

    Relative imports are resolved against the importing module's package, so
    ``from ..migration.state import load_state`` inside
    ``glm_universal.semantics.audit`` comes back as
    ``glm_universal.migration.state`` -- the name this file is looking for.
    """
    path = _module_path(dotted)
    if not os.path.isfile(path):
        return set()
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=path)
    package = dotted.rsplit(".", 1)[0] if not path.endswith("__init__.py") \
        else dotted
    out: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("glm_universal"):
                    out.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = package.split(".")
                base = ".".join(parts[:len(parts) - node.level + 1])
                prefix = f"{base}.{node.module}" if node.module else base
            else:
                prefix = node.module or ""
            if not prefix.startswith("glm_universal"):
                continue
            out.add(prefix)
            for alias in node.names:
                out.add(f"{prefix}.{alias.name}")
    return {name for name in out if os.path.isfile(_module_path(name))}


def _reachable(start: str) -> Tuple[Set[str], Dict[str, str]]:
    """Every module reachable from ``start``, with who imported each.

    A package's ``__init__`` is recorded but not expanded.  Importing
    ``glm_universal.data_objects`` runs an ``__init__`` that re-exports the
    whole package, and through the top-level ``__init__`` that eventually
    names every module there is -- so following those edges would make every
    module reach every other and the walk would measure nothing.  What it
    measures instead is the dependency an author wrote: which *modules* the
    answering path names, directly or through other modules.
    """
    seen = {start}
    via: Dict[str, str] = {}
    frontier = [start]
    while frontier:
        current = frontier.pop()
        if _module_path(current).endswith("__init__.py"):
            continue
        for name in _imports_of(current):
            if name in seen:
                continue
            seen.add(name)
            via[name] = current
            frontier.append(name)
    return seen, via


class TestTheDecisionIsRecorded(unittest.TestCase):

    def test_the_decision_names_both_halves(self):
        decision = audit.retention_decision()
        self.assertEqual(decision["decision"], "demoted to evidence")
        self.assertTrue(decision["kept"])
        self.assertFalse(decision["consulted_for_answers"])
        self.assertEqual(set(decision["rejected"]), {"refine", "delete"})

    def test_the_grounds_are_the_audit_and_not_a_memory(self):
        grounds = audit.retention_decision()["grounds"]
        concepts = audit.concept_grounding()
        plan = audit.purge_plan()
        self.assertEqual(grounds["concepts"], concepts["concepts"])
        self.assertEqual(grounds["concepts_grounded"], concepts["grounded"])
        self.assertEqual(grounds["edges_derivable"], plan["retained"])
        self.assertEqual(grounds["edges_dumped"], plan["dumped"])
        self.assertEqual(grounds["edges_derivable"] + grounds["edges_dumped"],
                         grounds["edges"])

    def test_the_replacement_is_larger_than_what_it_replaces(self):
        """The grounded graph is not a smaller, tidier version of the old one.

        It states more relations than the inherited graph had edges, and
        every one of them is re-derived; the point of the decision is that
        those two facts are compatible.
        """
        grounds = audit.retention_decision()["grounds"]
        self.assertGreater(grounds["replacement_edges"], grounds["edges"])

    def test_the_audit_report_carries_the_decision(self):
        self.assertEqual(audit.audit_report()["retention_decision"],
                         "demoted to evidence")


class TestTheAnsweringPathCannotReachIt(unittest.TestCase):

    def test_the_state_module_is_where_the_file_is_read(self):
        """The premise of the walk: this is the only door to the file."""
        self.assertIn(_STATE_MODULE, _imports_of(
            "glm_universal.semantics.audit"))

    def test_no_answering_module_reaches_the_inherited_state(self):
        for module in audit.ANSWERING_MODULES:
            with self.subTest(module=module):
                self.assertTrue(os.path.isfile(_module_path(module)),
                                f"{module} is not a module of the package")
                reachable, via = _reachable(module)
                if _STATE_MODULE not in reachable:
                    continue
                chain = [_STATE_MODULE]
                while chain[-1] in via:
                    chain.append(via[chain[-1]])
                self.fail(f"{module} can reach the inherited state through "
                          f"{' <- '.join(chain)}")

    def test_the_evidence_only_subjects_are_report_subjects(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        for subject in audit.EVIDENCE_ONLY_SUBJECTS:
            with self.subTest(subject=subject):
                self.assertIn(subject, REPORT_SUBJECTS)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

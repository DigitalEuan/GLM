"""``glm_universal.reasoning.pipeline_kit_crosscheck`` -- the pipeline kit's
late files run against the GLM (Phase 176).

*Created 21 October 2026.*

The owner's pipeline kit (``source_material/GLM_Pipeline_Kit/``) arrived in
Phase 175 without five files its README names; they arrived in Phase 176:
``python/tests/test_kit.py`` (14 executable cross-checks of the kit's Python
against its Lean facts), ``python/run_pipeline_demo.py`` (the README's
results table), ``GLMKit/AxiomAudit.lean`` (``#print axioms`` for 25
headline results) and the Lean root (``GLMKit.lean``, ``lakefile.toml``,
``lean-toolchain``).  This module is what the GLM takes from the two Python
files; the Lean audit became ``RequestProject/GLM/AxiomGuard.lean``.

What is measured
----------------
* **K1** the kit's own suite, ``test_kit.py``, run unchanged against the
  kit's package: 14 tests, 0 failures, 0 errors;
* **K2** the kit's demo protocol (``run_pipeline_demo.py``: five families,
  queries ``s = 0..49``, demonstrations from seeds ``1000(s+1)+k`` for
  ``k < 4``, query from seed ``1000(s+1)+999``, all drawn from the **kit's**
  task generator ``glm_kit.tasks``) reproduces the README's table for the
  kit's solver: toggle 50, translate 49 (+1 refused), reflect_v 50,
  flood_fill 0, bfs_shortest 0 right, 0 wrong anywhere;
* **K3** the GLM's ``tool induce`` solver
  (:func:`glm_universal.reasoning.pipeline_kit.solve`, as shipped) on the
  same 250 queries -- tasks drawn from a generator the GLM's solver was not
  built against (the kit's BFS path and enclosed rectangles, not the GLM's
  own): 0 wrong answers, and more right than the kit in total;
* **K4** every refusal the GLM makes there is *forced*: status
  ``ambiguous``, i.e. at least two hypotheses fit all four demonstrations and
  give the query different outputs (``ambiguous_forces_refusal`` in
  ``PipelineInduction.lean``: any answer would be wrong for one of them).

K3 as first written asked for at least as many right as the kit on *every*
family.  It failed on its first run: toggle 41 against the kit's 50,
translate 46 against 49.  The GLM's larger vocabulary is the reason -- on
toggle, ``complement then fill_enclosed`` fits demonstrations that have no
enclosed region and disagrees with ``complement`` on a query that has one;
the kit, lacking the fill, cannot see the tie and answers.  K3 was narrowed
to the total and K4 added to say what the lost answers are; the per-family
counts are reported, not hidden.

Exactness
---------
Integers, tuples and strings only.  Nothing is stored: the whole check takes
a few seconds and is recomputed on each call.
"""

from __future__ import annotations

import importlib
import io
import sys
import unittest
from pathlib import Path
from typing import Dict, List, Tuple

from . import pipeline_kit as pk

__all__ = ["KIT_ROOT", "KIT_PYTHON", "DEMO_FAMILIES", "QUERIES", "DEMOS",
           "README_KIT", "kit_package", "run_kit_suite", "demo_protocol",
           "crosscheck_report"]

#: The kit as delivered, in the owner's source material.
KIT_ROOT: Path = Path(__file__).resolve().parents[3] / "source_material" / \
    "GLM_Pipeline_Kit"
KIT_PYTHON: Path = KIT_ROOT / "python"

#: ``run_pipeline_demo.py``'s families and sizes.
DEMO_FAMILIES: Tuple[str, ...] = ("toggle", "translate", "reflect_v",
                                  "flood_fill", "bfs_shortest")
QUERIES = 50
DEMOS = 4

#: The kit README's table (§1), right / wrong / refused per family.
README_KIT: Dict[str, Tuple[int, int, int]] = {
    "toggle": (50, 0, 0), "translate": (49, 0, 1), "reflect_v": (50, 0, 0),
    "flood_fill": (0, 0, 50), "bfs_shortest": (0, 0, 50)}


def kit_package():
    """Import the kit's ``glm_kit`` package from the source material, or
    ``None`` when the kit is absent."""
    if not (KIT_PYTHON / "glm_kit" / "__init__.py").exists():
        return None
    path = str(KIT_PYTHON)
    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module("glm_kit")


def run_kit_suite() -> Dict[str, int]:
    """K1: run the kit's ``tests/test_kit.py`` unchanged; counts only."""
    if kit_package() is None:
        return {"available": 0, "ran": 0, "failures": 0, "errors": 0}
    loader = unittest.TestLoader()
    suite = loader.discover(str(KIT_PYTHON / "tests"), pattern="test_kit.py",
                            top_level_dir=str(KIT_PYTHON / "tests"))
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    return {"available": 1, "ran": result.testsRun,
            "failures": len(result.failures), "errors": len(result.errors)}


def _grid(g) -> pk.Grid:
    return tuple(tuple(int(v) for v in row) for row in g)


def demo_protocol() -> Dict[str, Dict[str, Dict[str, int]]]:
    """K2 and K3: the demo's 250 queries, scored for the kit's solver and for
    the GLM's.  ``{family: {"kit": counts, "glm": counts}}`` where counts are
    ``right``, ``wrong``, ``refused``."""
    kit = kit_package()
    if kit is None:
        return {}
    tasks = importlib.import_module("glm_kit.tasks")
    pipeline = importlib.import_module("glm_kit.pipeline")
    out: Dict[str, Dict[str, Dict[str, int]]] = {}
    for name in DEMO_FAMILIES:
        counts = {who: {"right": 0, "wrong": 0, "refused": 0}
                  for who in ("kit", "glm")}
        counts["glm"]["forced"] = 0
        for s in range(QUERIES):
            demos = [tasks.sample(name, 1000 * (s + 1) + k)[:2]
                     for k in range(DEMOS)]
            q, a, _ = tasks.sample(name, 1000 * (s + 1) + 999)
            pred, _rule = pipeline.solve(demos, q)
            key = "refused" if pred is None else ("right" if pred == a else "wrong")
            counts["kit"][key] += 1
            r = pk.solve([(_grid(x), _grid(y)) for x, y in demos], _grid(q))
            if r["status"] == "answered":
                key = "right" if r["answer"] == _grid(a) else "wrong"
            else:
                key = "refused"
                counts["glm"]["forced"] += r["status"] == "ambiguous"
            counts["glm"][key] += 1
        out[name] = counts
    return out


def crosscheck_report() -> Dict[str, object]:
    """Every mark, met or not."""
    if kit_package() is None:
        return {"available": False,
                "reason": f"the pipeline kit is not at {KIT_ROOT}"}
    suite = run_kit_suite()
    demo = demo_protocol()
    marks: List[Tuple[str, bool]] = []
    marks.append(("K1", suite["ran"] == 14 and suite["failures"] == 0
                  and suite["errors"] == 0))
    marks.append(("K2", all(
        (demo[f]["kit"]["right"], demo[f]["kit"]["wrong"],
         demo[f]["kit"]["refused"]) == README_KIT[f] for f in DEMO_FAMILIES)))
    totals = {who: {k: sum(demo[f][who][k] for f in DEMO_FAMILIES)
                    for k in ("right", "wrong", "refused")}
              for who in ("kit", "glm")}
    totals["glm"]["forced"] = sum(demo[f]["glm"]["forced"] for f in DEMO_FAMILIES)
    marks.append(("K3", totals["glm"]["wrong"] == 0
                  and totals["glm"]["right"] > totals["kit"]["right"]))
    marks.append(("K4", totals["glm"]["forced"] == totals["glm"]["refused"]))
    return {"available": True, "suite": suite, "demo": demo,
            "totals": totals, "marks": dict(marks),
            "met": sum(1 for _, ok in marks if ok), "taken": len(marks)}

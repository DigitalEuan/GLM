"""Tests for the pipeline kit's late files in the GLM (Phase 176).

*Created 21 October 2026.*

``reasoning/pipeline_kit_crosscheck.py`` declares the marks.  These tests pin:

* the five late files are where the owner asked (the kit folder in
  ``source_material/``), the kit's Lean root naming its seven files;
* **K1** the kit's own suite passes unchanged (14 tests);
* **K2** the kit's demo table is reproduced exactly;
* **K3** ``tool induce`` gives 0 wrong answers on the demo's 250 queries and
  more right than the kit; **K4** each of its refusals is forced.
"""

from __future__ import annotations

from glm_universal.reasoning import pipeline_kit_crosscheck as pkc


def test_late_files_are_in_the_kit_folder():
    for rel in ("python/tests/test_kit.py", "python/run_pipeline_demo.py",
                "GLMKit/AxiomAudit.lean", "GLMKit.lean", "lakefile.toml",
                "lean-toolchain"):
        assert (pkc.KIT_ROOT / rel).exists(), rel
    root = (pkc.KIT_ROOT / "GLMKit.lean").read_text(encoding="utf-8")
    for n in ("Golay", "Leech", "Lattices", "Fields", "Pless", "Analogy",
              "Permutation"):
        assert f"import GLMKit.{n}" in root, n
        assert (pkc.KIT_ROOT / "GLMKit" / f"{n}.lean").exists(), n


def test_kit_suite_passes_unchanged():
    s = pkc.run_kit_suite()
    assert s == {"available": 1, "ran": 14, "failures": 0, "errors": 0}


def test_crosscheck_marks():
    r = pkc.crosscheck_report()
    assert r["available"]
    for f, want in pkc.README_KIT.items():
        k = r["demo"][f]["kit"]
        assert (k["right"], k["wrong"], k["refused"]) == want, f
    assert r["totals"]["glm"]["wrong"] == 0
    assert r["totals"]["glm"]["right"] > r["totals"]["kit"]["right"]
    assert r["totals"]["glm"]["forced"] == r["totals"]["glm"]["refused"]
    # the kit's two open items, closed on the kit's own generator
    assert r["demo"]["flood_fill"]["glm"]["right"] >= 45
    assert r["demo"]["bfs_shortest"]["glm"]["right"] >= 45
    assert r["met"] == r["taken"] == 4

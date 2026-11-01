"""Tests for every Leech shell counted from the lattice's definition (Phase 164).

*Rebuilt 31 October 2026 (repository check).*  The original file was lost in
the October 2026 reorganisation; ``glm_universal/tests/README.md`` recorded
what its five tests pinned, and this file pins the same five things against
``reasoning/leech_shells.py`` and ``studies/LEECH_SHELLS_STUDY.md``:

* the **Lean file**: ``LeechShells.lean`` states the theorems the module
  names and has no ``sorry`` -- or, while the file is recorded missing in
  ``studies/_lean_files_needed.md``, that record stands;
* the **Golay weight census** walked from the generator rows is
  ``1, 759, 2576, 759, 1``;
* the **minimal shapes** step 2 finds agree with a direct membership test of
  the explicit minimal shell;
* the **Golay count and the theta series** (``E_4^3 - 720 Delta``, which
  knows nothing of the Golay code) agree for ``t = 0 .. 7``;
* the ``llvq`` **catalogue** is the derived one, its fifth shell
  34,417,656,000 (the stored table it replaced had 34,408,430,950).
"""

from __future__ import annotations

from glm_universal.constants import LEAN_FILES_NEEDED, lean_file
from glm_universal.lean_check import audited_or_held
from glm_universal.reasoning import leech_shells as ls


def test_lean_file_states_the_theorems_or_is_recorded_missing():
    path = lean_file("LeechShells.lean")
    if path.exists():
        text = path.read_text(encoding="utf-8")
        for name in ls.LEAN_THEOREMS:
            assert f"theorem {name}" in text, name
        assert "sorry" not in text
        # in the build tree: the axiom audit imports it
        assert audited_or_held("RequestProject.GLM.LeechShells")
    else:
        # lost in the reorganisation: the loss is recorded, not silent
        registry = LEAN_FILES_NEEDED.read_text(encoding="utf-8")
        assert "`LeechShells.lean`" in registry
    assert ls.LEAN_FILE.endswith("LeechShells.lean")


def test_weight_census_walked_from_the_generator():
    assert ls.weight_census() == {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1}


def test_minimal_shapes_agree_with_a_direct_membership_test():
    shapes = ls.minimal_shapes()
    # the even vectors on an octad (2^7 signs), the four signed pairs on the
    # zero word (C(24,2) * 4), the odd shape on every codeword (24 places)
    assert shapes["m=0 w=8"] == 128 and shapes["m=0 w=8 codewords"] == 759
    assert shapes["m=0 w=0"] == 4 * 276 and shapes["m=0 w=0 codewords"] == 1
    odd = sum(shapes[k] * shapes[k + " codewords"] for k in shapes
              if k.startswith("m=1") and not k.endswith("codewords"))
    assert odd == 24 * 4096
    total = sum(shapes[k] * shapes[k + " codewords"] for k in shapes
                if not k.endswith("codewords"))
    check = ls.minimal_shell_check()
    assert check["vectors"] == check["distinct"] == total == 196560
    assert check["in_lattice"] == check["norm_32"] == total


def test_golay_count_and_theta_series_agree():
    report = ls.shell_report(7)
    assert report["agree"]
    assert [r["golay"] for r in report["rows"]] == [
        1, 0, 196560, 16773120, 398034000, 4629381120, 34417656000,
        187489935360]


def test_llvq_catalogue_is_the_derived_one():
    from glm_universal.reasoning import llvq
    counts = [s["count"] for s in llvq.shell_summary()]
    derived = [c for _, c in ls.shells(len(counts) + 1) if c]
    assert counts[:len(derived)] == derived[:len(counts)]
    assert 34417656000 in counts
    assert 34408430950 not in counts

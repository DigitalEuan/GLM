"""Tests for the Leech kissing number from the lattice's definition (Phase 165).

*Rebuilt 31 October 2026 (repository check).*  The original file was lost in
the October 2026 reorganisation; ``glm_universal/tests/README.md`` recorded
what its four tests pinned, and this file pins the same four things against
``reasoning/leech_shells.py`` and ``studies/LEECH_KISSING_STUDY.md``:

* the **Lean file**: ``LeechKissing.lean`` states the theorems the module
  names and has no ``sorry`` -- or, while the file is recorded missing in
  ``studies/_lean_files_needed.md``, that record stands;
* the explicit **minimal shell** built from the three parameter families is
  196,560 distinct lattice vectors of squared length 32;
* the **split** ``759 * 128 + 276 * 4 + 4096 * 24``;
* the **controls**: an odd number of minus signs on an octad, and the wrong
  sign of the 3 in the odd shape, are rejected by the definition.
"""

from __future__ import annotations

from glm_universal.constants import LEAN_FILES_NEEDED, lean_file
from glm_universal.lean_check import audited_or_held
from glm_universal.reasoning import leech_shells as ls


def test_lean_file_states_the_theorems_or_is_recorded_missing():
    path = lean_file("LeechKissing.lean")
    if path.exists():
        text = path.read_text(encoding="utf-8")
        for name in ls.KISSING_LEAN_THEOREMS:
            assert f"theorem {name}" in text, name
        assert "sorry" not in text
        # in the build tree: the axiom audit imports it
        assert audited_or_held("RequestProject.GLM.LeechKissing")
    else:
        # lost in the reorganisation: the loss is recorded, not silent
        registry = LEAN_FILES_NEEDED.read_text(encoding="utf-8")
        assert "`LeechKissing.lean`" in registry
    assert ls.KISSING_LEAN_FILE.endswith("LeechKissing.lean")


def test_minimal_shell_is_196560_distinct_lattice_vectors_of_length_32():
    check = ls.minimal_shell_check()
    assert check == {"vectors": 196560, "distinct": 196560,
                     "in_lattice": 196560, "norm_32": 196560}


def test_the_split_over_the_three_families():
    vecs = ls.minimal_shell_vectors()
    even_octad = sum(1 for x in vecs if sorted(set(map(abs, x))) == [0, 2])
    pairs = sum(1 for x in vecs if sorted(set(map(abs, x))) == [0, 4])
    odd = sum(1 for x in vecs if all(v % 2 for v in x))
    assert (even_octad, pairs, odd) == (759 * 128, 276 * 4, 4096 * 24)
    assert even_octad + pairs + odd == 196560


def test_the_control_variants_are_rejected():
    codeset = set(ls._codewords())
    octad = next(c for c in codeset if bin(c).count("1") == 8)
    supp = [i for i in range(24) if octad >> i & 1]
    # an odd number of minus signs on an octad: the sum is 4 (mod 8), not 0
    x = [0] * 24
    for j, i in enumerate(supp):
        x[i] = -2 if j == 0 else 2
    assert not ls._is_leech(tuple(x), codeset)
    x[supp[1]] = -2          # two minus signs: in the lattice
    assert ls._is_leech(tuple(x), codeset)
    # the odd shape with the wrong sign of the 3: on the zero codeword every
    # coordinate is -1 and the 3 must be +3; -3 is rejected
    base = [-1] * 24
    good, bad = list(base), list(base)
    good[0], bad[0] = 3, -3
    assert ls._is_leech(tuple(good), codeset)
    assert not ls._is_leech(tuple(bad), codeset)

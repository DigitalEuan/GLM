"""Tests for the shortest tag (Phase 135).

``studies/SHORTEST_TAG_STUDY.md`` pre-registered six marks.  These tests pin:

* the **Lean file** (S1): it exists, states every theorem the module names,
  and has no ``sorry``;
* the **constructions** (S2): the 7-, 11- and 15-bit tags have least octad
  weight 1, 3, 5 at exactly the proved built-on-seven floor, and both
  protected tags are parities of the seven tag bits with the Lean file's
  selector rows;
* the **Plotkin step** (S3) on the seven-bit tag's kernel and the **onto**
  property (S4);
* the **search**: its deficit is exact on known tags, it is deterministic,
  and it finds the 11-bit construction's length again (S5's cheapest half).
  The full gap search (S6) takes minutes and is the tool's, not the suite's.
"""

from __future__ import annotations

from pathlib import Path

from glm_universal.reasoning import carrier_read as cr
from glm_universal.reasoning import designed_substrate as ds
from glm_universal.reasoning import shortest_tag as st

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "src" / "lean" / st.LEAN_FILE


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in st.LEAN_THEOREMS:
        assert f"theorem {name}" in text, name
    assert "sorry" not in text
    assert st.s1_lean()["passed"]


def test_the_floors():
    assert st.FLOOR_GENERAL == {1: 7, 3: 9, 5: 11}
    assert st.FLOOR_BUILT == {1: 7, 3: 11, 5: 15}
    for d in (1, 3, 5):
        assert st.FLOOR_GENERAL[d] == d + 6
        assert st.FLOOR_GENERAL[d] <= st.FLOOR_BUILT[d]


def test_s2_the_constructions_meet_the_built_floor():
    out = st.s2_constructions()
    assert out["passed"]
    assert out["min_weight"] == (1, 3, 5)
    assert out["lengths"] == (7, 11, 15)
    assert out["sel11"] == (1, 2, 4, 8, 16, 32, 64, 89, 107, 86, 44)
    assert out["sel15"] == (1, 2, 4, 8, 16, 32, 64, 11, 22, 44, 88, 59,
                            118, 103, 69)


def test_built_on_seven_rejects_a_foreign_mask():
    assert st.built_on_seven(ds.TAG_MASKS) == tuple(1 << j for j in range(7))
    foreign = ds.TAG_MASKS + (1,)
    assert st.built_on_seven(foreign) is None


def test_s3_the_plotkin_step_on_the_kernel():
    out = st.s3_kernel()
    assert out["passed"]
    assert out["kernel"] == 32
    assert out["kernel_octads"] == 0
    assert out["kernel_weights"] == [0, 12, 16]
    assert out["avoiding_coordinate_0"] == 16
    assert out["most_avoiding_one_coordinate"] == 16


def test_s4_the_seven_bit_tag_is_onto():
    out = st.s4_onto()
    assert out["passed"]
    assert out["values"] == 127
    assert not out["zero_taken"]
    assert out["multiplicities"] == [3, 6]
    assert sum(st.seven_bit_values().values()) == 759


def test_the_deficit_is_exact_on_known_tags():
    funcs = st._functionals()
    assert len(funcs) == 4095 and len(set(funcs)) == 4095
    # a low-coordinate mask m has hit-set funcs[m - 1]; reading the 15-bit
    # tag's functionals through them is not possible directly (its masks are
    # 24-bit), so check the deficit against the octad weights instead
    octs = st.octads()
    for masks, d in ((ds.TAG_MASKS, 1), (cr.TAG11_MASKS, 3),
                     (cr.TAG15_MASKS, 5)):
        hits = []
        for m in masks:
            h = 0
            for i, o in enumerate(octs):
                if bin(o & m).count("1") & 1:
                    h |= 1 << i
            hits.append(h)
        assert st.deficit(hits, d) == 0
        assert st.deficit(hits, d + 1) == sum(
            max(0, d + 1 - w) for w in st.tag_weights(masks))


def test_the_search_is_deterministic_and_finds_eleven_bits():
    a = st.local_search(11, 3, 200_000, seed=1)
    b = st.local_search(11, 3, 200_000, seed=1)
    assert a == b
    assert a["least_deficit"] == 0
    assert st.min_octad_weight(a["masks"]) >= 3
    assert st.functional_rank(a["masks"]) >= 7


def test_the_search_finds_seven_bits_at_once():
    out = st.local_search(7, 1, 10_000, seed=1)
    assert out["least_deficit"] == 0
    assert st.min_octad_weight(out["masks"]) >= 1
    assert st.functional_rank(out["masks"]) == 7

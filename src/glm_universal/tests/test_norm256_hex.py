"""Tests for ``reasoning/norm256_hex`` -- norm 256 and the hex colour
(Phase 127).

``studies/NORM_256_HEX_STUDY.md`` pre-registered three candidates for the
norm-256 rung, their order, a held-out query set and the marks.  These tests
pin:

* the **Lean file** -- its theorems, no ``sorry``, and the rotation it names
  (``hexP``, ``hexS``) equal to the one the module uses;
* the **rotation** -- a fixed-point-free involution that is a Golay
  automorphism, a sign set that is a dodecad transversal, ``hexRot`` squaring
  to ``-1`` and doubling norms under ``1 + hexRot``;
* the **candidates** -- the declared order, membership, the quantisers;
* the **hex shortcut** (X1, X2), recomputed live;
* the stored **measurement** -- the filling, the held-out set and the marks,
  read from the cache, which must describe the sources (D4).
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path

from glm_universal.reasoning import norm256_hex as nh
from glm_universal.substrate import construction_ladder as CL
from glm_universal.substrate import leech2 as L2
from glm_universal.substrate import mog

_ROOT = Path(__file__).resolve().parents[3]
_LEAN = _ROOT / "src" / "lean" / nh.LEAN_FILE


def test_the_lean_file_states_the_theorems_without_sorry():
    text = _LEAN.read_text(encoding="utf-8")
    for name in nh.LEAN_THEOREMS:
        assert re.search(rf"^theorem {name}\b", text, re.MULTILINE), name
    assert "sorry" not in text
    assert "axiom " not in text


def test_the_lean_rotation_is_the_module_rotation():
    text = _LEAN.read_text(encoding="utf-8")
    body = re.search(r"def hexP : Fin 24 → Fin 24 :=\s*!\[([^\]]*)\]", text)
    assert body is not None
    assert tuple(int(v) for v in body.group(1).split(",")) == nh.HEX_P
    assert re.search(rf"def hexS : ℕ := {nh.HEX_S}\b", text)


def test_the_rotation_is_a_golay_automorphism_squaring_to_minus_one():
    assert all(nh.HEX_P[nh.HEX_P[i]] == i and nh.HEX_P[i] != i
               for i in range(24))
    assert nh.HEX_S in mog.GOLAY_SET and bin(nh.HEX_S).count("1") == 12
    assert all(((nh.HEX_S >> i) & 1) + ((nh.HEX_S >> nh.HEX_P[i]) & 1) == 1
               for i in range(24))
    for word in mog.GOLAY_MASKS:
        image = sum(1 << nh.HEX_P[i] for i in range(24) if (word >> i) & 1)
        assert image in mog.GOLAY_SET
    x = tuple(range(1, 25))
    assert nh.hex_rot(nh.hex_rot(x)) == tuple(-v for v in x)
    plus = [a + b for a, b in zip(x, nh.hex_rot(x))]
    assert sum(v * v for v in plus) == 2 * sum(v * v for v in x)


def test_the_rotation_keeps_leech_basis_vectors_on_the_lattice():
    for row in L2.LEECH_BASIS:
        assert CL.in_rung(nh.hex_rot(row), "C")


def test_the_declared_order_is_densest_first_lattice_before_translate():
    assert nh.CANDIDATE_ORDER == ("R256", "16Z", "H16")
    kissing = [nh.CANDIDATES[k]["kissing"] for k in nh.CANDIDATE_ORDER]
    assert kissing == sorted(kissing, reverse=True)
    assert [nh.CANDIDATES[k]["lattice"] for k in nh.CANDIDATE_ORDER] == \
        [True, True, False]
    assert all(nh.rung_norm(k) == 256 for k in nh.CANDIDATE_ORDER)
    assert 256 not in {nh.rung_norm(r) for r in nh.BASE_LADDER}


def test_membership_and_the_hex_bucket_reading():
    assert nh.in_rung((16,) + (0,) * 23, "16Z")
    assert not nh.in_rung((8,) + (0,) * 23, "16Z")
    assert nh.in_rung((8,) * 24, "H16")
    # a value is read by its first hex digit: 0..15 -> bucket 0, centre 8
    assert nh.quantise((Fraction(15),) + (0,) * 23, "H16")[0] == 8
    assert nh.quantise((Fraction(16),) + (0,) * 23, "H16")[0] == 24
    assert nh.quantise((Fraction(-1, 8),) + (0,) * 23, "H16")[0] == -8
    y = [2 * v for v in L2.LEECH_BASIS[0]]
    p = tuple(a + b for a, b in zip(y, nh.hex_rot(y)))
    assert nh.in_rung(p, "R256")


def test_the_quantisers_land_on_their_rungs():
    for key in ("16Z", "H16"):
        assert nh.quantiser_check(key)["holds"]
    assert nh.quantiser_check("R256", vectors=20)["holds"]


def test_the_hex_shortcut():
    check = nh.shortcut_check(points=200)
    assert check["dimension"] == 12 and check["colours"] == 4096
    assert check["X1"] and check["X2"]
    assert all(re.fullmatch(r"#[0-9a-f]{6}", c)
               for c in check["basis_colours"])


def test_the_stored_measurement_describes_the_sources():
    assert nh.state()["verdict"] == "fresh"
    assert nh.current() is not None


def test_the_filling_keeps_the_hex_bucket_reading():
    report = nh.current()
    assert report is not None
    filling = report["filling"]
    assert filling["kept"] == "H16"
    rows = {t["candidate"]: t["row"] for t in filling["trials"]}
    assert rows["R256"]["wrong"] == 2 and rows["16Z"]["wrong"] == 4
    assert rows["H16"]["wrong"] == 0 and rows["H16"]["unique_correct"] == 0
    final = report["final"]
    assert (final["correct"], final["wrong"], final["refused"]) == (467, 0, 101)


def test_the_held_out_set_and_the_marks():
    report = nh.current()
    assert report is not None
    held = report["held_out"]
    assert held["queries"] == 568
    assert held["alone"]["H16"]["wrong"] == 0
    assert held["alone"]["R256"]["wrong"] == 3
    assert held["alone"]["16Z"]["wrong"] == 3
    assert held["final"]["wrong"] == 8 and held["base"]["wrong"] == 8
    assert held["final"]["correct"] == 440 and held["base"]["correct"] == 439
    assert report["marks"] == {"C1": True, "F1": True, "F2": True,
                               "H1": True, "H2": False, "X1": True,
                               "X2": True}

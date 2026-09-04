"""The retrieval round, pinned to the tree it describes.

``studies/RETRIEVED_LEAN_STUDY.md`` says which Lean files came back from the
supplied archive and how much each one contributes.  A study that states a
count is only as good as the thing that re-derives it, so this file re-derives
all of them:

* every file the study's table names exists in ``RequestProject/GLM/`` and is
  byte-identical to the overlay's mirror of it;
* every one of them carries the number of lines and the number of declarations
  the table states, counted by the address book's own parser -- so the table
  and ``LEAN_ADDRESS_STUDY.md`` cannot drift apart;
* no retrieved file carries a ``sorry`` or an ``admit``;
* every retrieved file is reachable from the address book, and the headline
  totals the study quotes (25 files, 7,230 lines, 854 declarations) are the
  sums of its own rows;
* the named theorems the study leans on are present under the names it uses.

The point of the last one is that a retrieval is worthless if the retrieved
statement is not the statement the archive made: the names below are the ones
the study's prose cites, and a rename that made the prose wrong would fail
here rather than go unnoticed.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from glm_universal.reasoning import lean_address as la

# overlay/glm_universal/tests -> the repository root.
REPO = Path(__file__).resolve().parents[3]
STUDY = REPO / "studies" / "RETRIEVED_LEAN_STUDY.md"
TREE = REPO / "RequestProject" / "GLM"
MIRROR = REPO / "overlay" / "glm_lean" / "RequestProject" / "GLM"

#: ``file -> (lines, declarations)``, as the study's section 2 table states it.
ROW = re.compile(r"^\|\s*`([A-Za-z0-9/]+\.lean)`\s*\|\s*([\d,]+)\s*\|\s*([\d,]+)\s*\|")

#: Theorems the study's prose cites by name, and the file each lives in.
CITED = {
    "Calibration.lean": ("substrate_c_is_circular",
                         "speed_not_from_action_and_energy", "octad_min_tax"),
    "AlignmentPoints.lean": ("gammaS_eq", "electronMass_error"),
    "FitCapacity.lean": ("fit_capacity",),
    "Packing.lean": ("perfect_triple_length", "even_distance_ambiguity"),
    "Triad.lean": ("tgic_counts_generic", "interaction_counts_differ",
                   "twentyfour_decompositions"),
    "SeedLayers.lean": ("transcendental_not_trace_of_finite_order",
                        "lattice_character_ne_pi", "phi_is_trace_of_order_ten",
                        "fibMat_eigenvector"),
    "StepCost.lean": ("nrci_gauge_independent", "total_const",
                      "shortcut_distortion"),
    "SpatialArithmetic.lean": ("nodeCount_roundtrip", "nodeCount_injective",
                               "dist_ge_clearance"),
    "ReasoningLoop.lean": ("solve_sound", "solve_eq_none_iff",
                           "gate_not_sufficient"),
    "Cube/Surface.lean": ("mog_card", "mog_min_weight"),
    "Cube/HexTiles.lean": ("hexacode_mds", "update_matrix_order_three",
                           "determined_by_boundary"),
    "Cube/Stabiliser.lean": ("stabiliser_card", "preserves_iff_tetrahedral"),
    "Cube/Tax.lean": ("covering_radius_le_four", "covering_radius_ge_four",
                      "repair_unique_of_le_three", "repair_ambiguous_at_four",
                      "and_is_priced"),
    "Cube/Three.lean": ("ruleA_code_is_not_golay",),
    "Shortcut/Decoder.lean": ("golay_covering_radius", "decode_isGolay",
                              "decode_dist_le_four", "substrate_snap_fails"),
    "Shortcut/Substrate.lean": ("legacySnap_even_weight",),
    "Shortcut/GrayCode.lean": ("d2_eq_pop_gray_xor", "d2_succ"),
    "Shortcut/Leech.lean": ("leech_min_norm", "golay_step_isLeech",
                            "golay_step_minimal_iff"),
    "Shortcut/Shortcut.lean": ("corrected_step_isLeech", "corrected_quantized"),
}

#: The totals section 3 states.
TOTAL_FILES = 25
TOTAL_LINES = 7230
TOTAL_DECLARATIONS = 854


def _table():
    """``[(file, lines, declarations)]`` read out of the study."""
    rows = []
    for line in STUDY.read_text(encoding="utf-8").splitlines():
        match = ROW.match(line)
        if match:
            rows.append((match.group(1),
                         int(match.group(2).replace(",", "")),
                         int(match.group(3).replace(",", ""))))
    return rows


class TestTheStudyDescribesTheTree(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rows = _table()

    def test_the_table_was_read(self):
        self.assertEqual(len(self.rows), TOTAL_FILES)
        self.assertEqual(len({name for name, _, _ in self.rows}), TOTAL_FILES)

    def test_every_named_file_exists_in_both_copies(self):
        for name, _, _ in self.rows:
            with self.subTest(file=name):
                source = TREE / name
                mirror = MIRROR / name
                self.assertTrue(source.is_file(), f"{name} is missing")
                self.assertTrue(mirror.is_file(),
                                f"{name} is missing from the overlay mirror")
                self.assertEqual(source.read_bytes(), mirror.read_bytes(),
                                 f"{name} differs between the two copies")

    def test_every_named_file_has_the_stated_length(self):
        for name, lines, _ in self.rows:
            with self.subTest(file=name):
                actual = len((TREE / name).read_text(
                    encoding="utf-8").splitlines())
                self.assertEqual(actual, lines,
                                 f"{name} is {actual} lines, table says {lines}")

    def test_no_retrieved_file_carries_a_sorry(self):
        banned = re.compile(r"\b(sorry|admit)\b")
        for name, _, _ in self.rows:
            with self.subTest(file=name):
                text = (TREE / name).read_text(encoding="utf-8")
                self.assertIsNone(banned.search(text),
                                  f"{name} carries a sorry or an admit")

    def test_the_totals_are_the_sums_of_the_rows(self):
        self.assertEqual(sum(lines for _, lines, _ in self.rows), TOTAL_LINES)
        self.assertEqual(sum(n for _, _, n in self.rows), TOTAL_DECLARATIONS)


class TestTheParserAgreesWithTheTable(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rows = _table()
        cls.by_file = {}
        for decl in la.declarations():
            cls.by_file.setdefault(decl.file, []).append(decl)

    def test_every_retrieved_file_contributes_the_stated_declarations(self):
        for name, _, count in self.rows:
            with self.subTest(file=name):
                found = len(self.by_file.get(name, ()))
                self.assertEqual(found, count,
                                 f"{name} parses to {found} declarations, "
                                 f"table says {count}")

    def test_the_retrieval_is_a_counted_share_of_the_current_corpus(self):
        """The retrieval is present in the corpus, and is a part of it.

        The earlier form of this check asserted that the corpus was exactly
        the retrieval plus the 1,270 declarations that preceded it.  That was
        true when the round closed and is not true now: the restoration round
        that followed added files of its own.  What remains checkable, and is
        checked here, is that every declaration the table counts is a
        declaration the address book actually holds for that file, and that
        the retrieval is a proper part of a corpus that has since grown.
        """
        retrieved = sum(count for _, _, count in self.rows)
        self.assertEqual(retrieved, TOTAL_DECLARATIONS)
        in_the_book = sum(len(self.by_file.get(name, ()))
                          for name, _, _ in self.rows)
        self.assertEqual(in_the_book, retrieved)
        self.assertGreater(len(la.declarations()), retrieved)

    def test_the_cited_theorems_exist_under_the_names_the_study_uses(self):
        for name, cited in CITED.items():
            declarations = {d.name.rsplit(".", 1)[-1]
                            for d in self.by_file.get(name, ())}
            for theorem in cited:
                with self.subTest(file=name, theorem=theorem):
                    self.assertIn(theorem, declarations,
                                  f"{name} no longer declares {theorem}, "
                                  f"which the study cites")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

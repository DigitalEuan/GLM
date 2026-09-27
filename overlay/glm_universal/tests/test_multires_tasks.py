"""Multi-resolution Leech addressing, and the two worked end-to-end tasks.

``reasoning/multires``
    The same 24 coordinates addressed at two resolutions.  *Bit level*: a MOG
    column's ``F_2^4`` value in ``GF(4) x Z_4`` fibre coordinates, and the
    local rank-4 Leech sub-lattice it sits in.  *Grid level*: a whole 2D grid
    carried into the 24 coordinates and read as a ten-plane Monster address.
    *Cross level*: inner and tensor products between the two, and the
    measurement of which readings survive rescaling.

``reasoning/tasks``
    Two tasks run through the whole pipeline rather than through a single
    mechanism: an ARC-style grid puzzle filtered at three resolutions, and a
    physics question that SI7 cannot answer.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import metric as ME
from glm_universal.reasoning import monster_stack as MS
from glm_universal.reasoning import multires as MR
from glm_universal.reasoning import tasks as TK
from glm_universal.runtime import tct_engine as tct
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


@pytest.fixture(scope="module")
def report():
    return MR.multires_report()


# ===========================================================================
# 1.  BIT-LEVEL MICRO-ADDRESSING
# ===========================================================================

class TestFibration:

    def test_the_map_is_a_bijection_onto_gf4_times_z4(self, report):
        fibration = report["fibration"]
        assert fibration["columns"] == 16
        assert fibration["distinct_images"] == 16
        assert fibration["bijective"] is True
        assert fibration["round_trip"] is True

    def test_every_fibre_has_four_elements(self, report):
        assert report["fibration"]["fibre_sizes"] == {0: 4, 1: 4, 2: 4, 3: 4}

    def test_the_kernel_is_klein_four_not_cyclic(self, report):
        fibration = report["fibration"]
        assert fibration["kernel_size"] == 4
        assert fibration["kernel_is_cyclic_of_order_4"] is False

    def test_round_trip_on_every_column_value(self):
        for value in range(16):
            digit, residue = MR.column_to_fibre(value)
            assert 0 <= digit < 4 and 0 <= residue < 4
            assert MR.fibre_to_column(digit, residue) == value

    def test_out_of_range_arguments_are_refused(self):
        with pytest.raises(ValueError):
            MR.column_to_fibre(16)
        with pytest.raises(ValueError):
            MR.fibre_to_column(4, 0)
        with pytest.raises(ValueError):
            MR.fibre_to_column(0, 4)


class TestColumnSublattices:

    def test_every_column_carries_a_rank_four_sublattice(self, report):
        assert len(report["columns"]) == 6
        for column in report["columns"]:
            assert len(column["coordinates"]) == 4
            assert column["projection_determinant"] == 8
            assert column["intersection_determinant"] == 512
            assert column["index"] == 64

    def test_the_index_measures_what_a_bit_level_reading_loses(self):
        row = MR.column_sublattice(0)
        assert row["index"] == (row["intersection_determinant"]
                                // row["projection_determinant"])
        assert row["index"] > 1

    def test_a_micro_address_names_its_cell_and_its_fibre(self):
        micro = MR.micro_address(0b1011, 0)
        assert 0 <= micro.row < 4
        assert 0 <= micro.col < 6
        assert micro.bit in (0, 1)
        assert MR.fibre_to_column(micro.gf4_digit,
                                  micro.z4_residue) == micro.column_value

    def test_an_out_of_range_coordinate_is_refused(self):
        with pytest.raises(ValueError):
            MR.micro_address(0, 24)


# ===========================================================================
# 2.  GRID-LEVEL MACRO-ADDRESSING
# ===========================================================================

class TestGridCarriers:

    def test_a_small_grid_is_carried_losslessly_in_frame_mode(self):
        grid = MR.SAMPLE_GRIDS["cross"]
        carrier = MR.grid_carrier(grid, mode="frame")
        assert len(carrier) == 24
        assert sum(1 for x in carrier if x) == sum(
            1 for row in grid for x in row if x)

    def test_the_census_carrier_is_twenty_four_exact_statistics(self):
        census = MR.grid_census(MR.SAMPLE_GRIDS["stripes"])
        assert len(census) == 24
        for value in census:
            assert isinstance(value, int)
            assert 0 <= value < 512

    def test_a_grid_has_a_ten_plane_address(self):
        address = MR.grid_address(MR.SAMPLE_GRIDS["cross"])
        assert address.depth == 10
        assert len(address.masks()) == 10

    def test_the_signature_is_made_of_exact_ratios(self):
        signature = MR.grid_signature(MR.SAMPLE_GRIDS["cross"])
        assert isinstance(signature["density"], Fraction)
        assert isinstance(signature["aspect_ratio"], Fraction)
        assert signature["rot180_symmetric"] is True

    def test_the_transformations_are_involutions_where_they_should_be(self):
        grid = MR.SAMPLE_GRIDS["corner"]
        assert MR.reflect_horizontal(MR.reflect_horizontal(grid)) == grid
        assert MR.reflect_vertical(MR.reflect_vertical(grid)) == grid
        assert MR.rotate180(MR.rotate180(grid)) == grid

    def test_upscaling_repeats_every_cell(self):
        grid = ((1, 2), (3, 4))
        assert MR.upscale(grid, 2) == ((1, 1, 2, 2), (1, 1, 2, 2),
                                       (3, 3, 4, 4), (3, 3, 4, 4))


# ===========================================================================
# 3.  CROSS-LEVEL INVARIANCE
# ===========================================================================

class TestCrossLevel:

    def test_the_inner_product_is_exact_or_absent(self, report):
        for column in report["cross_level"]["columns"]:
            inner = column["inner"]
            assert inner is None or isinstance(Fraction(inner), Fraction)

    def test_the_tensor_contracts_back_to_the_inner_product(self, report):
        for column in report["cross_level"]["columns"]:
            tensor = column["tensor"]
            if tensor.get("defined"):
                assert tensor["rank"] == 1
                assert tensor["contraction"] == column["inner"]

    def test_an_absent_axis_gives_no_product_rather_than_a_guess(self):
        grid = MR.SAMPLE_GRIDS["cross"]
        macro = MR.grid_address(grid).planes[0]
        micro = MR.micro_address(0, 0, repair=False)
        if micro.axis_class is None:
            assert MR.cross_inner(micro, macro) is None
            assert MR.cross_tensor(micro, macro)["defined"] is False

    def test_the_signature_survives_rescaling_and_the_address_does_not(
            self, report):
        rows = report["scale_invariance"]["rows"]
        assert rows
        assert all(row["signature_invariant"] for row in rows)
        assert not any(row["address_invariant"] for row in rows)

    def test_reflection_leaves_the_signature_alone(self):
        grid = MR.SAMPLE_GRIDS["corner"]
        assert (MR.grid_signature(MR.reflect_horizontal(grid))["density"]
                == MR.grid_signature(grid)["density"])

    def test_the_census_loses_information_and_a_witness_shows_it(self, report):
        collision = report["census_collision"]
        assert collision["found"] is True
        assert collision["first"] != collision["second"]
        assert collision["carriers_equal"] is True
        assert collision["frame_carriers_equal"] is False


# ===========================================================================
# 4.  THE GRID TASK
# ===========================================================================

class TestGridTask:

    def test_it_finds_the_rule_and_says_so(self):
        result = TK.grid_task()
        assert result["solved"] is True
        assert result["rule"] == "rotate180"

    def test_the_three_resolutions_prune_in_order(self):
        stages = {s["resolution"]: s for s in TK.grid_task()["stages"]}
        assert stages["signature"]["candidates_out"] == 5
        assert stages["address_plane0"]["candidates_out"] == 1
        assert stages["address_full"]["candidates_out"] == 1

    def test_the_coarse_resolution_is_blind_to_the_answer(self):
        stages = {s["resolution"]: s for s in TK.grid_task()["stages"]}
        assert stages["signature"]["pruned"] == []
        assert "reflect_horizontal" in stages["address_plane0"]["pruned"]

    def test_the_rule_reproduces_every_training_pair(self):
        assert TK.grid_task()["checks"]["training_reproduced"] is True

    def test_the_prediction_is_the_half_turn_of_the_test_grid(self):
        result = TK.grid_task()
        assert (tuple(tuple(row) for row in result["prediction"])
                == MR.rotate180(result["test"]))

    def test_the_prediction_moves_the_address_but_not_the_signature(self):
        checks = TK.grid_task()["checks"]
        assert checks["address_changed"] is True
        assert checks["signature_preserved"] is True


# ===========================================================================
# 5.  THE PHYSICS TASK
# ===========================================================================

class TestPhysicsTask:

    def test_si7_conflates_the_two_quantities(self):
        result = TK.physics_task()
        assert result["si7"]["equal"] is True
        assert result["si7"]["left"] == "L^2 M T^-2"

    def test_the_extended_basis_separates_them(self):
        result = TK.physics_task()
        assert result["ext10"]["equal"] is False

    def test_the_verifier_distinguishes_scalar_from_full_semantics(self):
        verdicts = TK.physics_task()["verifier"]
        assert verdicts["scalar"]["energy"] is True
        assert verdicts["scalar"]["torque"] is False
        assert verdicts["ranks"]["energy"] != verdicts["ranks"]["torque"]

    def test_the_escalation_names_a_layer_rather_than_dumping_an_object(self):
        escalation = TK.physics_task()["escalation"]
        assert isinstance(escalation["layer"], str)
        assert escalation["first_separating_layer"] in (
            escalation["layer_distances"].keys())
        assert "raw" not in escalation

    def test_the_facets_locate_the_difference(self):
        result = TK.physics_task()
        carrying = result["facets"]["carrying_the_difference"]
        assert carrying
        assert set(carrying) <= set(
            result["facets"]["distances"].keys())
        for name, value in result["facets"]["distances"].items():
            if name in carrying:
                assert Fraction(value) > 0
            else:
                assert Fraction(value) == 0

    def test_the_facet_distances_sum_to_the_griess_distance(self):
        from glm_universal import data_objects as do
        carriers = {}
        for obj in do.physics.physics_objects():
            if obj.name in ("energy", "torque"):
                carriers[obj.name] = ME.as_exact_vector(obj.carrier)
        total = ME.distance2(carriers["energy"], carriers["torque"])
        parts = TK.physics_task()["facets"]["distances"]
        assert sum(Fraction(v) for v in parts.values()) == total

    def test_the_address_difference_is_decoded_not_guessed(self):
        address = TK.physics_task()["address"]
        assert address["depth"] == 10
        assert address["first_differing_plane"] is not None
        assert address["golay"]["status"] in ("codeword", "corrected",
                                              "ambiguous")
        assert (bin(address["difference_mask"]).count("1")
                == address["difference_weight"])


# ===========================================================================
# 6.  RUNTIME WIRING
# ===========================================================================

class TestRuntimeWiring:

    def test_report_multiresolution_is_reachable(self, sess):
        solution = sess.ask("report multiresolution")
        assert solution.ok
        assert solution.expected["fibre_bijective"] == "True"
        assert solution.expected["signature_invariant_everywhere"] == "True"
        assert tct.verify_trace(tct.build_trace(solution)).verified

    def test_task_grid_is_reachable(self, sess):
        solution = sess.ask("task grid")
        assert solution.ok
        assert solution.kind == "task"
        assert solution.expected["rule"] == "rotate180"
        assert tct.verify_trace(tct.build_trace(solution)).verified

    def test_task_physics_is_reachable(self, sess):
        solution = sess.ask("task physics")
        assert solution.ok
        assert solution.kind == "task"
        assert solution.expected["si7_equal"] == "True"
        assert solution.expected["ext10_equal"] == "False"
        assert tct.verify_trace(tct.build_trace(solution)).verified

    def test_an_unknown_task_is_reported_not_guessed(self, sess):
        solution = sess.ask("task chemistry")
        assert solution.ok is False
        assert "unknown task" in (solution.error or "")

    def test_a_bare_task_lists_the_tasks(self, sess):
        solution = sess.ask("task")
        assert solution.ok is False
        assert "grid" in solution.answer and "physics" in solution.answer

    def test_the_monster_address_of_a_grid_matches_the_task_pipeline(self):
        grid = MR.SAMPLE_GRIDS["cross"]
        address = MR.grid_address(grid)
        direct = MS.monster_address(MR.grid_carrier(grid))
        assert address.masks() == direct.masks()

"""Tests for ``reasoning/pcgs`` -- the proof-carrying generative substrate.

The two source scripts (``source_material/pcgs_wider_landscape_v4.txt`` and
``source_material/pcgs_glm_integration.py``) assert a long list of properties of
generated objects and check them by printing.  Here each one is either *pinned
to a theorem* of ``RequestProject/GLM/PCGS.lean`` or explicitly labelled as a
test:

* ``bitsFor_spec`` / ``bitsFor_min`` / ``bitsFor_le_iff`` -- the information
  axis is the tight description bound (``TestInformationAxis``);
* ``Cost.plus_comm`` / ``plus_assoc`` / ``algebraicTotal_plus`` /
  ``algebraicTotal_scale`` -- the ledger algebra (``TestCostAlgebra``);
* ``rmWeight_of_ne_zero`` / ``rmWeight_of_zero`` / ``rm_min_distance`` -- the
  Reed-Muller weight distribution and minimum distance, checked against a full
  enumeration of the generated code (``TestReedMuller``);
* ``ntt_intt`` -- the transform round trip, checked for the definition *and* for
  the radix-2 algorithm, which is the transcription the theorem is carried
  across by (``TestTransform``);
* ``bitsErased_reversible`` / ``landauerEnergy_mono`` /
  ``landauerEnergy_le_of_le_log_two`` / ``ln2Lower_100_le_log_two`` -- the
  physical layer (``TestPhysicalLayer``);
* ``breakeven_iff`` / ``breakevenQueries_spec`` -- the caching decision
  (``TestCaching``).

Everything is exact: ``int`` and ``Fraction`` only, and no RNG.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from glm_universal.reasoning import pcgs
from glm_universal.substrate.mog import GOLAY_MASKS


@pytest.fixture(scope="module")
def report():
    return pcgs.pcgs_report()


class TestInformationAxis:
    """``bits_for`` against ``GLM.PCGS.bitsFor_spec`` and ``bitsFor_min``."""

    def test_bound_is_achievable_and_minimal(self, subtests):
        for n in range(0, 130):
            with subtests.test(n=n):
                bits = pcgs.bits_for(n)
                assert n <= 2**bits  # bitsFor_spec
                if bits:
                    assert n > 2 ** (bits - 1)  # bitsFor_min

    def test_powers_of_two_are_exact(self):
        for k in range(0, 12):
            assert pcgs.bits_for(2**k) == k  # bitsFor_two_pow

    def test_vector_bound_is_exact_and_float_free(self):
        # The source script fell back to math.log2 above 65,536 symbols.
        assert pcgs.bits_for_vector(2, 100000) == 100000
        assert pcgs.bits_for_vector(17, 4) == pcgs.bits_for(17**4)
        assert pcgs.bits_for_vector(3, 5) == pcgs.bits_for(243)
        assert pcgs.bits_for_vector(1, 10) == 0

    def test_syndrome_bits(self):
        assert pcgs.bits_for(2**12) == 12


class TestCostAlgebra:
    """The ledger is a commutative monoid with additive totals."""

    def _sample(self):
        return [
            pcgs.Cost(mul=3, add=5, info_bits=17),
            pcgs.Cost(sub=2, xor=7),
            pcgs.Cost(modinv=1, cmp=4, info_bits=3),
            pcgs.ZERO_COST,
        ]

    def test_commutative_and_associative(self, subtests):
        costs = self._sample()
        for a in costs:
            for b in costs:
                with subtests.test(a=a, b=b):
                    assert a.plus(b) == b.plus(a)  # Cost.plus_comm
                for c in costs:
                    assert a.plus(b).plus(c) == a.plus(b.plus(c))  # plus_assoc

    def test_zero_is_neutral(self):
        for cost in self._sample():
            assert cost.plus(pcgs.ZERO_COST) == cost
            assert pcgs.ZERO_COST.plus(cost) == cost

    def test_total_is_additive_and_scales(self, subtests):
        for cost in self._sample():
            for other in self._sample():
                with subtests.test(cost=cost, other=other):
                    assert (
                        cost.plus(other).algebraic_total()
                        == cost.algebraic_total() + other.algebraic_total()
                    )  # algebraicTotal_plus
            for k in range(0, 5):
                assert cost.scale(k).algebraic_total() == cost.algebraic_total() * k

    def test_scale_is_repeated_addition(self):
        cost = pcgs.Cost(mul=2, add=1, info_bits=4)
        total = pcgs.ZERO_COST
        for k in range(6):
            assert cost.scale(k) == total
            total = total.plus(cost)


class TestReedMuller:
    """The generated code has the weight distribution the theorem forces."""

    def test_weight_enumerator_matches_theorem(self, report, subtests):
        for row in report["codes"]["reed_muller"]:
            with subtests.test(m=row["m"]):
                assert row["matches_theorem"]
                assert row["minimum_distance"] == row["predicted_minimum_distance"]

    def test_every_codeword_has_a_forced_weight(self, subtests):
        # rmWeight_of_ne_zero: half the points; rmWeight_of_zero: 0 or 2**m.
        for m in (2, 3, 4, 5):
            code = pcgs.ReedMullerCode(m)
            for message in range(1 << code.k):
                with subtests.test(m=m, message=message):
                    weight = bin(code.encode(message)).count("1")
                    assert weight in (0, 1 << (m - 1), 1 << m)

    def test_minimum_distance_bound_holds_pairwise(self, subtests):
        # rm_min_distance, checked on every pair of the smaller codes.
        for m in (2, 3, 4):
            code = pcgs.ReedMullerCode(m)
            for u in range(1 << code.k):
                for v in range(u + 1, 1 << code.k):
                    with subtests.test(m=m, u=u, v=v):
                        differ = bin(code.encode(u) ^ code.encode(v)).count("1")
                        assert differ >= 1 << (m - 1)

    def test_certificates_check_out(self):
        code = pcgs.ReedMullerCode(4)
        word = code.encode(19)
        certificate = code.certificate(word)
        assert certificate is not None
        assert code.verify_certificate(word, certificate)
        assert code.certificate(1) is None  # weight-1 word is not a codeword

    def test_self_duality_claim_of_the_source_script_is_wrong(self):
        # The script says "RM(1,m) is self-dual iff m is odd"; only m = 3 is.
        assert pcgs.ReedMullerCode(3).is_self_dual()
        assert not pcgs.ReedMullerCode(5).is_self_dual()
        assert not pcgs.ReedMullerCode(2).is_self_dual()
        assert not pcgs.ReedMullerCode(4).is_self_dual()

    def test_description_is_smaller_than_the_extension(self, report, subtests):
        for row in report["codes"]["reed_muller"]:
            with subtests.test(m=row["m"]):
                assert row["description_bits"] < row["extension_bits"]


class TestGolayCrossCheck:
    """The generative account agrees with the substrate's own Golay code."""

    def test_regenerated_code_is_the_stored_one(self, report):
        cross = report["codes"]["golay_cross_check"]
        assert cross["sets_agree"]
        assert cross["regenerated_count"] == len(set(GOLAY_MASKS)) == 4096
        assert cross["weight_enumerator"] == cross["weight_enumerator_expected"]
        assert cross["minimum_distance"] == 8

    def test_generator_is_far_smaller_than_the_table(self, report):
        cross = report["codes"]["golay_cross_check"]
        assert cross["description_bits"] == 288  # twelve 24-bit rows, 36 bytes
        assert cross["extension_bits"] == 98304


class TestTransform:
    """The transform is generated from two integers, and it inverts."""

    def test_algorithm_matches_the_proved_definition(self, report):
        assert report["transform"]["algorithm_matches_definition"]

    def test_roundtrip(self, report):
        assert report["transform"]["roundtrip"]

    def test_convolution(self, report):
        assert report["transform"]["convolution_matches_schoolbook"]

    def test_root_has_the_right_order(self, report):
        assert report["transform"]["root_order"] == report["transform"]["length"]

    def test_measured_cost_equals_declared_cost(self, report):
        transform = report["transform"]
        for side in ("forward", "inverse"):
            measured = dict(transform[f"measured_{side}"])
            declared = dict(transform[f"declared_{side}"])
            measured.pop("info_bits")
            declared.pop("info_bits")
            assert measured == declared

    def test_a_larger_instance(self, subtests):
        ntt = pcgs.NumberTheoreticTransform(97, 8)
        assert ntt.root_order() == 8
        x = 1
        for trial in range(4):
            vector = []
            for _ in range(8):
                vector.append(x % 97)
                x = (11 * x + 7) % 97
            with subtests.test(trial=trial):
                spectrum = ntt.forward(vector)
                assert spectrum == ntt.forward_direct(vector)
                assert ntt.inverse(spectrum) == vector
                assert ntt.inverse_direct(ntt.forward_direct(vector)) == vector

    def test_twiddles_are_generated_not_stored(self):
        ntt = pcgs.NumberTheoreticTransform(97, 8)
        assert [ntt.twiddle(k) for k in range(8)] == [
            pow(ntt.w, k, 97) for k in range(8)
        ]
        assert ntt.twiddle(8) == 1
        assert ntt.description_bits() < ntt.table_bits()

    def test_bad_parameters_are_refused(self):
        with pytest.raises(ValueError):
            pcgs.NumberTheoreticTransform(16, 4)  # not prime
        with pytest.raises(ValueError):
            pcgs.NumberTheoreticTransform(17, 3)  # not a power of two
        with pytest.raises(ValueError):
            pcgs.NumberTheoreticTransform(17, 32)  # does not divide p - 1


class TestOperatorAndTransducer:
    """The two systems that stay tested rather than proved."""

    def test_stencil_agrees_with_the_matrix(self, report):
        assert report["operator"]["agrees_with_matrix"]
        assert report["operator"]["description_entries"] < report["operator"][
            "matrix_entries"
        ]

    def test_stencil_on_several_dimensions(self, subtests):
        for n in (1, 2, 5, 11):
            with subtests.test(n=n):
                operator = pcgs.SparseStencilOperator((-1, 2, -1), n)
                x = [Fraction(i + 1, 7) for i in range(n)]
                assert operator.apply(x) == operator.dense_apply(x)

    def test_transducer_agrees_with_recomputation(self, report):
        assert report["transducer"]["agrees_with_recomputation"]

    def test_transducer_state_is_two_numbers(self):
        transducer = pcgs.running_mean_transducer()
        state = transducer.final_state([1, 2, 3, 4])
        assert state == (Fraction(10), 4)
        assert transducer.run([2, 4])[-1] == Fraction(3)


class TestPhysicalLayer:
    """Landauer and CMOS, in exact Fractions."""

    def test_fast_bound_is_tight_and_below_log_two(self, subtests):
        layer = pcgs.PhysicalCostLayer
        # ln2Fast_le_log_two: every partial sum is a lower bound.
        for terms in (1, 2, 8, 30, 64):
            with subtests.test(terms=terms):
                value = layer.ln2_lower_fast(terms)
                # below log 2 (which Mathlib brackets at 0.69314718 03..08)
                assert value < Fraction(6931471808, 10**10)
                # and the tail bound closes the bracket from above
                assert value + layer.ln2_fast_tail_bound(terms) > Fraction(
                    6931471803, 10**10
                )
        near = layer.ln2_lower_fast(64)
        assert Fraction(6931471803, 10**10) < near < Fraction(6931471808, 10**10)

    def test_fast_bound_beats_the_alternating_one(self):
        layer = pcgs.PhysicalCostLayer
        assert layer.ln2_lower_fast(30) > layer.ln2_lower(100)

    def test_ln2_is_bracketed(self):
        lower = pcgs.PhysicalCostLayer.ln2_lower(100)
        upper = pcgs.PhysicalCostLayer.ln2_upper(101)
        assert lower < upper
        # 0.6931471803 < ln 2 < 0.6931471808 (Mathlib's decimal bounds)
        assert lower < Fraction(6931471803, 10**10)
        assert upper > Fraction(6931471808, 10**10)

    def test_lower_bound_is_a_lower_bound_at_every_even_length(self, subtests):
        for terms in range(2, 40, 2):
            with subtests.test(terms=terms):
                assert pcgs.PhysicalCostLayer.ln2_lower(terms) < Fraction(
                    6931471803, 10**10
                )

    def test_odd_and_even_lengths_are_refused_correctly(self):
        with pytest.raises(ValueError):
            pcgs.PhysicalCostLayer.ln2_lower(101)
        with pytest.raises(ValueError):
            pcgs.PhysicalCostLayer.ln2_upper(100)

    def test_reversible_step_erases_nothing(self):
        layer = pcgs.PhysicalCostLayer
        assert layer.bits_erased(3, 3) == 0  # bitsErased_reversible
        assert layer.bits_erased(3, 5) == 0
        assert layer.bits_erased(2, 1) == 1  # a NAND gate
        assert layer.landauer_energy(layer.bits_erased(3, 3)) == 0
        assert layer.is_reversible(3, 3)
        assert not layer.is_reversible(2, 1)

    def test_energy_is_monotone_in_bits(self, subtests):
        layer = pcgs.PhysicalCostLayer
        previous = Fraction(0)
        for bits in range(0, 20):
            with subtests.test(bits=bits):
                energy = layer.landauer_energy(bits)
                assert energy >= previous  # landauerEnergy_mono
                previous = energy

    def test_efficiency_is_undefined_without_operations(self):
        layer = pcgs.PhysicalCostLayer
        # The source script returned Fraction(0) here, conflating two cases.
        assert layer.thermodynamic_efficiency(8, 0) is None
        assert layer.thermodynamic_efficiency(0, 8) == 0

    def test_cmos_is_far_above_the_floor(self, report):
        # The practical electrical cost of one gate transition is four to five
        # orders of magnitude above the thermodynamic floor for one bit.
        layer = pcgs.PhysicalCostLayer
        ratio = layer.cmos_per_op() / layer.landauer_per_bit()
        assert 10**4 < ratio < 10**5
        assert report["physical"]["reversible_step_costs_nothing"]
        assert report["physical"]["efficiency_undefined_without_operations"]

    def test_everything_is_exact(self):
        layer = pcgs.PhysicalCostLayer
        for value in (
            layer.landauer_per_bit(),
            layer.cmos_per_op(),
            layer.landauer_energy(17),
            layer.cmos_energy(16),
        ):
            assert isinstance(value, Fraction)


class TestCaching:
    """Materialising is a decision with an exact threshold."""

    def test_threshold_is_exactly_where_the_trade_turns(self, subtests):
        for store in (1, 7, 24, 4096 * 24):
            for generate, lookup in ((12, 1), (5, 2), (2, 1)):
                threshold = pcgs.breakeven_queries(store, generate, lookup)
                with subtests.test(store=store, generate=generate, lookup=lookup):
                    assert pcgs.breakeven_holds(store, generate, lookup, threshold)
                    if threshold:
                        assert not pcgs.breakeven_holds(
                            store, generate, lookup, threshold - 1
                        )

    def test_equivalence_holds_at_every_query_count(self, subtests):
        for queries in range(0, 40):
            with subtests.test(queries=queries):
                # breakevenQueries_spec
                assert pcgs.breakeven_holds(30, 7, 2, queries) == (
                    pcgs.breakeven_queries(30, 7, 2) <= queries
                )

    def test_no_breakeven_when_lookup_is_not_cheaper(self):
        with pytest.raises(ValueError):
            pcgs.breakeven_queries(100, 3, 3)

    def test_table(self, report, subtests):
        for row in report["caching"]:
            with subtests.test(object=row["object"]):
                assert row["breakeven_queries"] > 0
                assert pcgs.breakeven_holds(
                    row["store_bits"],
                    row["generate_bits_per_query"],
                    row["lookup_bits_per_query"],
                    row["breakeven_queries"],
                )


class TestAdmission:
    """Every system states its evidence, and says what kind of evidence it is."""

    def test_all_six_criteria_are_addressed(self, subtests):
        for row in pcgs.admission_table():
            with subtests.test(system=row.system):
                assert row.admitted()
                assert row.evidence_kind in {
                    "proved",
                    "tested",
                    "checked transcription",
                }

    def test_report_counts(self, report):
        assert report["system_count"] == 6
        assert report["admitted_count"] == 6
        assert report["proved_count"] == 3

    def test_proved_rows_name_a_theorem(self, subtests):
        for row in pcgs.admission_table():
            if row.evidence_kind == "proved":
                with subtests.test(system=row.system):
                    assert "GLM." in row.evidence

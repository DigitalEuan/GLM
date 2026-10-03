"""Tests for round 6 of the order of work -- the register against the world
(Phase 93, ``studies/REGISTER_WORLD_STUDY.md``).

Every row of the element register, in the three fields an outside source
holds, is compared with the frozen CIAAW and NIST tables, and the register is
never written.  The completion gate reads the nested holdout.  The marks R1-R7
were declared before any code at the head of
``glm_universal/evaluation/register_world_cases.py``; R8 is
``RequestProject/GLM/RegisterWorld.lean``.

Seven things could go wrong, one class each:

* a cell could go undecided, or be decided twice (``TestEveryCellDecided``);
* the reading could mis-state what a verdict means (``TestTheReading``);
* the register could be written (``TestTheRegisterIsNotWritten``);
* an injected error could pass (``TestInjectedErrors``);
* a question could be answered other than as declared (``TestQuestions``);
* an earlier verdict could move without being declared (``TestEarlier``);
* and the completion gate could move more, or less, than it declared
  (``TestTheCompletionGate``).
"""

from __future__ import annotations

import inspect
import json
from fractions import Fraction

import pytest

from glm_universal.evaluation import register_world_cases as rc
from glm_universal.reasoning import element_completion as ec
from glm_universal.reasoning.intervals import Interval
from glm_universal.runtime import register_world as rw
from glm_universal.runtime import register_world_report as rr


@pytest.fixture(scope="module")
def report():
    return rr.register_world_report()


class TestEveryCellDecided:
    """R1: 354 cells, each with exactly one of the six verdicts."""

    def test_three_fields_of_118_rows(self, report):
        assert report["world"]["cells"] == 3 * 118
        assert report["world"]["accounted"]

    def test_counts_partition_each_field(self, report):
        for field, counts in report["world"]["counts"].items():
            assert set(counts) == set(rw.VERDICTS)
            assert sum(counts.values()) == 118, field

    def test_the_declared_discrepancies(self, report):
        d = report["world"]["discrepant"]
        assert d["atomic_weight_u"] == ()
        assert d["ionization_energy_eV"] == rc.IE_DISCREPANT
        assert d["electron_configuration"] == ("Lr",)

    def test_iron_is_located(self):
        """The planner's one wrong answer, found by the report."""
        cell = rw.cell("Fe", "atomic_weight_u")
        assert cell.verdict == "agrees_at_stated_precision"

    def test_the_sources_are_frozen_with_provenance(self):
        rows = {s["file"]: s for s in rw.sources()}
        assert rows["world_ciaaw_2024.json"]["rows"] == 118
        assert rows["world_nist_ie.json"]["rows"] == 108
        for s in rows.values():
            assert s["url"].startswith("https://")
            assert len(s["raw_sha256"]) == 64
            assert s["retrieved"]


class TestTheReading:
    """The verdicts mean what the declaration says."""

    W = Interval(Fraction("55.843"), Fraction("55.847"))

    def test_inside_agrees(self):
        assert rw.compare_number(Fraction("55.845"), self.W) == "agrees"

    def test_held_reading_meets(self):
        assert rw.compare_number(Fraction("55.84"), self.W) == \
            "agrees_at_stated_precision"

    def test_disjoint_is_discrepant(self):
        assert rw.compare_number(Fraction("55.9"), self.W) == "discrepant"

    def test_silences(self):
        assert rw.compare_number(None, None) == "both_silent"
        assert rw.compare_number(Fraction(1), None) == "world_silent"
        assert rw.compare_number(None, self.W) == "register_silent"

    def test_ciaaw_uncertainty_counts_last_places(self):
        w = rw.world_weights()["Fe"].interval
        assert (w.lo, w.hi) == (Fraction("55.843"), Fraction("55.847"))
        w = rw.world_weights()["F"].interval
        assert w.hi - w.lo == Fraction(10, 10 ** 9)

    def test_interval_weights_are_themselves(self):
        w = rw.world_weights()["Pb"].interval
        assert (w.lo, w.hi) == (Fraction("206.14"), Fraction("207.94"))

    def test_no_standard_weight_is_silent(self):
        assert rw.world_weights()["Tc"].interval is None

    def test_occupation_ignores_written_order(self):
        assert rw.occupation("[Ar]4s2 3d6") == rw.occupation("[Ar].3d6.4s2")
        assert rw.occupation("[Ar]3d5 4s1") == rw.occupation("[Ar].3d5.4s")

    def test_occupation_counts_electrons(self):
        for element in __import__(
                "glm_universal.data_objects.elements",
                fromlist=["x"]).load_element_register():
            occ = rw.occupation(element.electron_configuration)
            assert sum(occ.values()) == element.z, element.symbol

    def test_lawrencium_differs_in_one_electron(self):
        cell = rw.cell("Lr", "electron_configuration")
        assert cell.verdict == "discrepant"
        assert "6d 1 against 0" in cell.detail
        assert "7p 0 against 1" in cell.detail

    def test_undeclared_field_is_refused_by_name(self):
        with pytest.raises(rw.WorldRefusal) as why:
            rw.cell("C", "electronegativity_pauling")
        assert why.value.code == "STANDARD_UNDECLARED"


class TestTheRegisterIsNotWritten:
    """R2."""

    def test_digest_unchanged_over_the_whole_round(self, report):
        assert report["register"]["before"] == report["register"]["after"]
        assert report["marks"]["R2"]

    def test_the_module_opens_nothing_for_writing(self):
        source = inspect.getsource(rw)
        assert "write_text" not in source
        assert "write_bytes" not in source
        assert "open(" not in source


class TestInjectedErrors:
    """R4, and R5 for the molecules."""

    def test_every_injected_error_is_caught(self, report):
        a = report["audit"]
        assert a["injected"] > 0
        assert a["caught"] == a["injected"]

    def test_no_world_value_is_flagged(self, report):
        a = report["audit"]
        assert a["flagged"] == 0

    def test_every_molecule_is_decided(self, report):
        m = report["world"]["molecules"]
        assert m["rows"] == 51
        assert sum(m["counts"].values()) == 51
        assert report["marks"]["R5"]

    def test_a_molecule_sums_its_elements(self):
        row = rw.molecule_cell("water")
        lo, hi = row["world"]
        h = rw.world_weights()["H"].interval
        o = rw.world_weights()["O"].interval
        assert lo == 2 * h.lo + o.lo and hi == 2 * h.hi + o.hi


class TestQuestions:
    """R3: through the router, as ``GLM.py -q`` reads them."""

    def test_every_case_as_declared(self, report):
        q = report["questions"]
        assert q["cases"] == len(rc.ALL_CASES) == 24
        assert q["met"] == q["cases"]
        assert q["wrong"] == 0

    def test_refusals_name_their_code(self, report):
        for row in report["questions"]["rows"]:
            if not row["answered"]:
                assert any(code in row["text"] for code in rw.REFUSAL_CODES)

    @pytest.mark.parametrize("expected,answered,text,verdict", [
        ("yes", True, "yes, consistent", "met"),
        ("yes", True, "no, inconsistent", "wrong"),
        ("yes", False, "refused", "missed"),
        (("refuse", "WORLD_SILENT"), False, "WORLD_SILENT: x", "met"),
        (("refuse", "WORLD_SILENT"), True, "yes", "wrong"),
        (("list", ("Lr",)), True, "1: Lr -- each", "met"),
        (("list", ()), True, "none -- no row", "met"),
        (("list", ("Lr",)), True, "2: Lr, No -- each", "wrong"),
    ])
    def test_the_judge(self, expected, answered, text, verdict):
        assert rr.judge(expected, answered, text) == verdict


class TestEarlier:
    """R6: Phase 63's interval questions, with the one declared move."""

    def test_eight_of_eight_and_one_move(self, report):
        e = report["earlier"]
        assert e["correct"] == e["cases"] == 8
        assert e["moved"] == ("y1-gold-standard",)


class TestTheCompletionGate:
    """R7: the nested gate's declared outcome."""

    def test_the_declared_outcome(self, report):
        g = report["gate"]
        assert g["outcome"]["demoted"] == rc.COMPLETION_DEMOTED
        assert g["outcome"]["narrowed"] == rc.COMPLETION_NARROWED
        assert g["outcome"]["kept_unchanged"]

    def test_the_first_gate_is_kept_for_the_record(self):
        assert set(ec.first_gate_rules()) == \
            set(rc.COMPLETION_KEPT) | set(rc.COMPLETION_DEMOTED) \
            | set(rc.COMPLETION_NARROWED)

    def test_every_admitted_rule_passes_both_gates(self):
        table = ec.nested_gate_table()
        for field, rule in ec.admitted_rules().items():
            assert rule.admitted
            if rule.domain:
                rows = [d for d in table[field]["domains"]
                        if d["domain"] == rule.domain]
                assert rows and rows[0]["survives"]
                assert rows[0]["scored_folds"] >= ec.GATE_MINIMUM
            else:
                assert table[field]["every"]["survives"]

    def test_estimates_only_inside_the_domain(self):
        rule = ec.admitted_rules()["electron_affinity_eV"]
        for cell in ec.completed_table():
            if cell.field == "electron_affinity_eV" and \
                    cell.provenance == "estimated":
                assert ec.in_domain(cell.symbol, rule.domain)

    def test_no_covalent_radius_is_estimated(self):
        assert not any(c.field == "covalent_radius_pm"
                       and c.provenance == "estimated"
                       for c in ec.completed_table())

    def test_the_loss_is_exactly_the_two_fields(self, report):
        g = report["gate"]
        assert g["coverage"]["estimated"] + g["lost_cells"] == \
            g["first_gate_estimated"]
        assert g["safety"] and g["accounted"]

    def test_the_nested_figures_are_y5_s(self):
        """Moved, not changed: over every element the nested skill is the
        substrate-cognition study's Y5 figure."""
        table = ec.nested_gate_table()
        assert table["covalent_radius_pm"]["every"]["nested_skill_3dp"] == \
            Fraction(631, 1000)
        assert table["electron_affinity_eV"]["every"]["nested_skill_3dp"] \
            == Fraction(823, 1000)
        assert table["melting_point_K"]["every"]["nested_skill_3dp"] == \
            Fraction(263, 1000)

    def test_all_marks(self, report):
        assert all(v for v in report["marks"].values() if v is not None)


def test_the_report_serialises():
    assert json.dumps(rw.world_report(), default=str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

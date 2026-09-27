"""Tests for the two supplied pieces that stayed in the sandbox.

``sandbox/memory_split`` is the four-register memory of the supplied
conversational material; ``sandbox/lean_generation`` is its carrier-to-Lean
generator.  Neither is relied on, and directive **D14** keeps them isolated
until they earn their way out, so the tests that matter here are the negative
ones:

* **the walls** -- no shipped module imports either, so deleting the sandbox
  cannot change an answer.  Checked with :mod:`ast` over the sources rather
  than trusted;
* **the checklists** -- every promotion line is computed, ``ready`` is their
  conjunction, and each module stays where it is while a line is false.  A
  test that asserts the false line fails the moment somebody quietly relaxes
  it;
* **the two refuted claims** -- the supplied round-trip check passes for a
  generator that emits the empty string, and the real round trip fails on all
  twelve carriers the supplied file was generated from.

Directive D7 -- no float anywhere -- is checked statically.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from glm_universal.reasoning import exactness as ex
from glm_universal.reasoning import lean_address as la
from glm_universal.runtime.session import GeometricSession
from glm_universal.sandbox import lean_generation as LG
from glm_universal.sandbox import memory_split as MS

PACKAGE_ROOT = Path(MS.__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def session():
    return GeometricSession()


@pytest.fixture(scope="module")
def split(session):
    return MS.memory_split_report(session)


@pytest.fixture(scope="module")
def generation(session):
    return LG.lean_generation_report(session)


class TestTheWalls:

    def test_no_shipped_module_imports_the_sandbox(self, subtests):
        """The documentation layer is the one declared exception, and it
        imports lazily; nothing else may name the sandbox at all."""
        allowed = {"corpus/render.py", "corpus/cost.py", "tools.py"}
        for path in sorted(PACKAGE_ROOT.rglob("*.py")):
            relative = path.relative_to(PACKAGE_ROOT).as_posix()
            if relative.startswith(("sandbox/", "tests/")):
                continue
            with subtests.test(module=relative):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if not isinstance(node, (ast.Import, ast.ImportFrom)):
                        continue
                    if "sandbox" not in ast.unparse(node):
                        continue
                    #  Naming it at all is allowed only to the documentation
                    #  layer, and only from inside a function.
                    assert relative in allowed, relative
                    assert node not in tree.body, relative


class TestTheFourRegisterSplit:

    def test_the_four_registers_are_the_supplied_ones(self):
        assert MS.KINDS == ("episodic", "semantic", "procedural",
                            "preference")
        assert MS.DECAY["episodic"] is not None
        assert all(MS.DECAY[kind] is None for kind in MS.KINDS[1:])

    def test_every_score_is_an_exact_rational_in_the_unit_interval(
            self, subtests):
        memory = MS.Memory(turn=0, text="describe carbon",
                           concepts=("C",), intent="describe")
        for kind in MS.KINDS:
            register = MS.MemoryRegister(kind)
            register.add(memory)
            with subtests.test(register=kind):
                score = register.score(memory, 0, ("C",), "describe")
                assert 0 <= score <= 1
                assert not isinstance(score, float)

    def test_it_agrees_with_licensing_less_than_always(self, split):
        """The measurement the round was taken for: the split is not a second
        reading of the conversation, it is recency with a decay rate."""
        assert split["agreed"] < split["bound"]
        assert split["disagreed"] == split["bound"] - split["agreed"]

    def test_it_answers_where_the_shipped_layer_refuses(self, split):
        assert split["answered_a_refusal"] > 0

    def test_the_utility_line_of_the_checklist_is_false(self, split):
        """Answering a refusal by naming one of the candidates is choosing a
        member of the ambiguity, which is the thing the refusal is for."""
        checklist = split["checklist"]
        assert checklist["ready"] is False
        assert checklist["checks"][
            "answers_a_refusal_without_choosing_a_member_of_it"] is False
        assert checklist["gained_by_choosing"]

    def test_the_checklist_is_the_conjunction_of_its_lines(self, split):
        checklist = split["checklist"]
        assert checklist["ready"] == all(checklist["checks"].values())
        assert set(checklist["order"]) == set(checklist["checks"])


class TestTheLeanGenerator:

    def test_the_supplied_check_passes_for_a_generator_that_emits_nothing(
            self, generation):
        """The check never reads what was generated, so it is not a check."""
        supplied = generation["supplied_check"]
        assert supplied["passes_as_supplied"] == len(LG.SUPPLIED_NAMES)
        assert (supplied["passes_with_empty_generator"]
                == supplied["passes_as_supplied"])
        assert supplied["vacuous"] is True

    def test_the_real_round_trip_fails_on_every_carrier(self, generation,
                                                        subtests):
        for row in generation["rows"]:
            with subtests.test(name=row["name"]):
                assert not row["exact"]
        assert generation["round_tripped"] == 0

    def test_the_generated_source_is_one_declaration_the_reader_finds(
            self, generation):
        assert generation["parsed"] == generation["declarations"]

    def test_most_readings_are_not_readings_a_declaration_could_have(
            self, generation):
        """A kind code of 8, 16 or 20 names no declaration kind, and a
        negative quantifier count is not a count."""
        assert generation["in_range"] < generation["declarations"]

    def test_the_agreement_is_partial_rather_than_absent(self, generation):
        assert 0 < generation["least_agreement"] <= generation[
            "most_agreement"] < len(la.FEATURE_NAMES)

    def test_elaboration_is_reported_as_unmeasured_rather_than_assumed(
            self, generation):
        checklist = generation["checklist"]
        assert checklist["elaborates"] is None
        assert checklist["checks"]["every_declaration_elaborates"] is False
        assert checklist["ready"] is False

    def test_a_supplied_count_can_close_the_elaboration_line(self):
        """The line is computed from what a caller measured, not asserted."""
        rows = ()
        assert promoted(rows, elaborates=0) is False

    def test_the_twelve_names_are_the_supplied_ones(self):
        assert len(LG.SUPPLIED_NAMES) == 12
        assert LG.SUPPLIED_NAMES[0] == "energy"


def promoted(rows, elaborates=None, proved=None) -> bool:
    return bool(LG.promotion_checklist(rows, elaborates=elaborates,
                                       proved=proved)["ready"])


class TestTheDiscipline:

    def test_no_float_is_constructed(self, subtests):
        for module in (MS, LG):
            with subtests.test(module=module.__name__):
                assert ex.module_float_sites(Path(module.__file__)) == {}

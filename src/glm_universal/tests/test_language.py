"""Tests for ``glm_universal.language`` -- the question shape as an object.

:mod:`glm_universal.recipe` made a *domain* declarative.  This sub-package
does the same for the *question*: a shape is an opening, named slots and the
words that separate them, and one generic matcher reads any of them.

What is pinned here:

* the descriptions are well formed, and a malformed shape is refused
  (``TestTheDescriptions``);
* the matcher fills the slots left to right, at the earliest separator, and
  strips articles exactly where the shipped parser does
  (``TestTheMatcher``);
* a question of an undescribed kind, a missing separator and an empty
  required slot are all declined with the boundary named, and every boundary
  a description states has a witness that reaches it
  (``TestTheRefusalBoundary``);
* writing a question from a shape and matching it back returns the filling it
  was written from, over the whole generated corpus (``TestTheRoundTrip``);
* the claim the round exists for: over a corpus generated from the registers,
  the described shapes produce the *kind and the options* the hand-written
  parser produces, and no question of an undescribed kind is matched
  (``TestAgreementWithTheShippedParser``);
* with the whole thing reachable from the CLI (``TestTheRuntime``);
* what a question may carry *before* its opening is described too, as an
  ordered preamble that may be skipped, and skipping it changes nothing
  about what is then matched (``TestThePreamble``);
* the price of describing the preamble rather than letting the opening float
  free: a leading word the preamble does not admit is declined here and
  swallowed into a slot by the branches (``TestTheNarrowing``);
* the branches are *gone*: the parser reads the descriptions for every kind
  any family describes, and the deleted code is kept frozen in
  ``language.legacy`` only so the comparison has something to compare
  against (``TestTheBranchesAreGone``);
* a second shape family -- an operator that cuts the question in two, with
  the modifiers and trailing options a shape may hold beside its operands --
  describes three more kinds and is read off by the runtime
  (``TestTheInfixFamily``);
* a slot may hold a *list*, cut at two ranks of separators
  (``TestTheListSlot``);
* a third family whose operands are not text but matches of another
  described shape (``TestTheNestedFamily``);
* the one place a description reads a question its branch declined is
  declared, its cause measured, and every widened question accounted for by
  it (``TestTheWidening``);
* how much of the surface is described is counted rather than claimed
  (``TestTheCoverage``).

The machine-checked counterparts are in ``RequestProject/GLM/Question.lean``:
``matchPieces_rendered`` (writing and matching are inverse),
``matchPieces_required_nonempty`` (a match never leaves a required slot
empty), ``matchPieces_lit_none`` and ``matchPieces_no_separator`` (the two
refusals), and ``matchPieces_not_both`` (disjoint openings make the order the
shapes are tried in irrelevant).
"""

from __future__ import annotations

import pytest

from glm_universal import language as lang
from glm_universal.language import build, descriptions as D
from glm_universal.language import question as Q
from glm_universal.language import report as RP
from glm_universal.runtime.parser import KINDS, QueryError, parse_query
from glm_universal.runtime.session import GeometricSession


@pytest.fixture(scope="module")
def summary():
    return RP.language_report()


@pytest.fixture(scope="module")
def sess():
    return GeometricSession()


# ===========================================================================
# 1.  THE DESCRIPTIONS
# ===========================================================================

class TestTheDescriptions:
    """A shape says what it recognises, and says why it is one set."""

    def test_every_described_kind_is_a_runtime_kind(self):
        for spec in D.QUESTIONS:
            assert spec.kind in KINDS

    def test_every_shape_opens_with_a_phrasing(self):
        for spec in D.QUESTIONS:
            assert isinstance(spec.shape[0], Q.Phrasing)
            assert spec.opening.alternatives

    def test_every_phrasing_says_why_it_is_one_set(self):
        for spec in D.QUESTIONS:
            for phrasing in spec.phrasings:
                assert phrasing.why
                assert phrasing.is_judgement

    def test_every_slot_is_named_for_the_option_it_fills(self):
        """The mapping from a shape to a query is the identity, not a table."""
        wanted = {"derive": {"coordinate", "object", "domain"},
                  "measure": {"subject", "class"},
                  "task": {"task"},
                  "compare": {"values"}}
        for spec in D.QUESTIONS:
            assert {s.name for s in spec.slots} == wanted[spec.kind]

    def test_every_slot_carries_a_known_role(self):
        for spec in D.QUESTIONS:
            for slot in spec.slots:
                assert slot.role in Q.ROLES

    def test_a_shape_with_no_slot_is_refused(self):
        with pytest.raises(ValueError):
            Q.QuestionSpec(kind="derive", gloss="",
                           shape=(Q.phrasing("derive", why="x"),))

    def test_a_shape_that_does_not_open_with_a_phrasing_is_refused(self):
        with pytest.raises(ValueError):
            Q.QuestionSpec(kind="derive", gloss="",
                           shape=(Q.slot("object", "object"),))

    def test_adjacent_slots_are_refused(self):
        with pytest.raises(ValueError):
            Q.QuestionSpec(
                kind="derive", gloss="",
                shape=(Q.phrasing("derive", why="x"),
                       Q.slot("coordinate", "coordinate"),
                       Q.slot("object", "object")))

    def test_a_phrasing_must_say_why(self):
        with pytest.raises(ValueError):
            Q.phrasing("derive", why="")

    def test_a_duplicate_surface_form_is_refused(self):
        with pytest.raises(ValueError):
            Q.phrasing("derive", "derive", why="x")

    def test_an_unknown_role_is_refused(self):
        with pytest.raises(ValueError):
            Q.slot("object", "colour")

    def test_the_openings_are_disjoint(self, summary):
        assert summary["disjoint"]["clashes"] == ()
        assert summary["disjoint"]["disjoint"]

    def test_question_by_kind_names_the_described_kinds(self):
        assert D.question_by_kind("derive") is D.DERIVE_QUESTION
        with pytest.raises(KeyError):
            D.question_by_kind("analogy")


# ===========================================================================
# 2.  THE MATCHER
# ===========================================================================

class TestTheMatcher:
    """One walk over the tokens; no scoring, no regular expression."""

    def test_a_derivation_fills_both_slots(self):
        out = build.parse("derive span_ratio of tea")
        assert isinstance(out, build.Match)
        assert out.kind == "derive"
        assert build.options_of(out) == {"coordinate": "span_ratio",
                                         "object": "tea", "domain": ""}

    def test_the_domain_tail_is_optional_and_read_when_present(self):
        out = build.parse("derive tet_step of perfect_fifth in harmonics")
        assert build.options_of(out)["domain"] == "harmonics"

    def test_any_opening_and_any_separator_reach_the_same_query(self):
        first = build.options_of(build.parse("derive span_ratio of tea"))
        for question in ("what derives span_ratio for tea",
                         "which coordinate span_ratio on tea",
                         "derivation of span_ratio of tea",
                         "coordinate span_ratio for tea"):
            assert build.options_of(build.parse(question)) == first

    def test_a_slot_takes_the_earliest_separator(self):
        out = build.parse("measure hot in tea in stellar_surface")
        assert build.options_of(out) == {"subject": "hot",
                                         "class": "tea in stellar_surface"}

    def test_the_class_may_be_left_out(self):
        assert build.options_of(build.parse("measure hot")) == {
            "subject": "hot", "class": ""}

    def test_a_task_takes_the_rest_of_the_question(self):
        assert build.options_of(build.parse("task grid")) == {"task": "grid"}

    def test_the_head_slot_drops_a_leading_article(self):
        """The shipped parser strips articles from the body it splits."""
        out = build.parse("derive the span_ratio of tea")
        assert build.options_of(out)["coordinate"] == "span_ratio"

    def test_a_slot_after_a_separator_keeps_its_article(self):
        """And only from the body, which is why the object keeps them."""
        out = build.parse("derive span_ratio of the tea")
        assert build.options_of(out)["object"] == "the tea"
        assert parse_query("derive span_ratio of the tea").options["object"] \
            == "the tea"

    def test_matching_is_a_function_of_the_question(self):
        one = build.parse("measure hot in tea")
        two = build.parse("measure  HOT  in  Tea?")
        assert build.options_of(one) == build.options_of(two)

    def test_the_trace_names_every_decision(self):
        out = build.parse("derive span_ratio of tea")
        assert any("opening" in line for line in out.trace)
        assert any("coordinate" in line for line in out.trace)


# ===========================================================================
# 3.  THE REFUSAL BOUNDARY
# ===========================================================================

class TestTheRefusalBoundary:
    """A question the descriptions do not decide is declined, with a reason."""

    def test_an_undescribed_opening_is_declined(self):
        out = build.parse("report language")
        assert isinstance(out, build.Decline)
        assert out.boundary == "unrecognised_opening"
        assert "described openings" in out.reason

    def test_a_missing_separator_is_declined(self):
        out = build.parse("derive span_ratio")
        assert isinstance(out, build.Decline)
        assert out.boundary == "no_separator"
        assert out.kind == "derive"

    def test_an_empty_required_slot_is_declined(self):
        out = build.parse("derive of tea")
        assert isinstance(out, build.Decline)
        assert out.boundary == "empty_coordinate"

    def test_a_missing_object_is_declined(self):
        out = build.parse("derive span_ratio of")
        assert isinstance(out, build.Decline)
        assert out.boundary == "empty_object"

    def test_nothing_to_measure_is_declined(self):
        out = build.parse("measure")
        assert isinstance(out, build.Decline)
        assert out.boundary == "empty_subject"

    def test_every_named_boundary_has_a_witness(self, summary):
        audit = summary["refusals"]
        assert audit["undescribed"] == ()
        assert audit["wrong"] == ()
        assert audit["exact"]

    def test_a_declined_question_answers_nothing(self):
        row = RP.ask("derive span_ratio")
        assert row["matched"] is False
        assert row["answered"] is False
        assert row["boundary"] == "no_separator"


# ===========================================================================
# 4.  WRITING A QUESTION, AND READING IT BACK
# ===========================================================================

class TestTheRoundTrip:
    """Writing and matching are inverse on the questions a shape can write."""

    def test_the_whole_corpus_round_trips(self, summary):
        trips = summary["round_trip"]
        assert trips["broken"] == ()
        assert trips["checked"] == summary["agreement"]["corpus"]

    def test_rendering_writes_the_first_alternative_by_default(self):
        # Alternatives are held longest-first, so the default opening is
        # `derivation of` and the default separator is `for`.
        spec = D.DERIVE_QUESTION
        assert spec.render_question({"coordinate": "span_ratio",
                                     "object": "tea", "domain": ""}) == \
            "derivation of span_ratio for tea"

    def test_rendering_can_choose_the_alternative(self):
        spec = D.DERIVE_QUESTION
        written = spec.render_question(
            {"coordinate": "span_ratio", "object": "tea", "domain": ""},
            {0: 4, 2: 1})
        assert written == "derive span_ratio of tea"

    def test_a_required_slot_cannot_be_written_empty(self):
        with pytest.raises(ValueError):
            D.DERIVE_QUESTION.render_question({"coordinate": "", "object": "x",
                                               "domain": ""})


# ===========================================================================
# 5.  THE MEASUREMENT
# ===========================================================================

class TestAgreementWithTheShippedParser:
    """The claim the round exists for, measured question by question."""

    def test_the_corpus_is_generated_and_not_small(self, summary):
        assert summary["agreement"]["corpus"] >= 400

    def test_every_corpus_question_is_matched_and_agrees(self, summary):
        agreed = summary["agreement"]
        assert agreed["disagreed"] == ()
        assert agreed["declined"] == ()
        assert agreed["agreed"] == agreed["corpus"]

    def test_the_options_are_compared_and_not_only_the_kind(self):
        """A same-kind, different-options parse would fail this."""
        for _kind, question, _fills in build.corpus():
            mine = build.parse(question)
            theirs = parse_query(question)
            for key, value in build.options_of(mine).items():
                assert theirs.options.get(key) == value, question

    def test_no_question_of_an_undescribed_kind_is_matched(self, summary):
        assert summary["agreement"]["false_positives"] == ()
        assert summary["agreement"]["outside"] > 50

    def test_the_undescribed_kinds_are_named_rather_than_forgotten(self):
        share = RP.described_share()
        assert set(share["described"]) == set(D.DESCRIBED_KINDS)
        assert set(share["infix"]) == set(D.INFIX_KINDS)
        assert set(share["nested"]) == set(D.NESTED_KINDS)
        assert set(share["covered"]) == set(share["described"]) | set(
            share["infix"]) | set(share["nested"])
        assert not set(share["covered"]) & set(share["undescribed"])
        assert "comparative" in share["covered"]
        assert "report" in share["undescribed"]

    def test_a_described_question_answers_off_the_description(self):
        row = RP.ask("derive span_ratio of tea")
        assert row["answered"]
        assert row["answer"]["domain"] == "comparison"

    def test_a_measure_question_answers_off_the_measure_register(self):
        row = RP.ask("how much hot in tea")
        assert row["answered"]

    def test_the_verdict_is_described(self, summary):
        assert summary["verdict"]["verdict"] == "described"
        assert summary["verdict"]["kinds_described"] == len(D.QUESTIONS)


# ===========================================================================
# 6.  EXACTNESS
# ===========================================================================

class TestExactness:
    """Integer token counting, and nothing else."""

    def test_no_float_is_constructed_anywhere_in_a_match(self):
        out = build.parse("derive span_ratio of tea")
        for value in build.options_of(out).values():
            assert isinstance(value, str)

    def test_the_report_holds_no_float(self, summary):
        def walk(value):
            assert not isinstance(value, float)
            if isinstance(value, dict):
                for item in value.values():
                    walk(item)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    walk(item)
        walk(summary)

    def test_tokenising_drops_only_punctuation(self):
        assert Q.tokenise("Derive span_ratio, of: tea?") == (
            "derive", "span_ratio", "of", "tea")


# ===========================================================================
# 7.  THE RUNTIME
# ===========================================================================

class TestTheRuntime:
    """`report language` is a subject like any other."""

    def test_the_subject_is_registered(self):
        from glm_universal.runtime.session import REPORT_SUBJECTS
        assert "language" in REPORT_SUBJECTS

    def test_the_subject_answers(self, sess):
        solution = sess.solve(parse_query("report language"))
        assert "query kinds" in solution.answer
        assert solution.expected["verdict"] == "described"

    def test_the_subject_is_reachable_by_its_aliases(self, sess):
        for alias in ("report question shapes", "report surface language"):
            solution = sess.solve(parse_query(alias))
            assert solution.expected["verdict"] == "described"

    def test_the_third_column_recomputes_the_report(self, sess):
        solution = sess.solve(parse_query("report language"))
        assert solution.script_spec["template"] == "report_language"

    def test_the_package_exports_the_sub_package(self):
        import glm_universal
        assert "language" in glm_universal.__all__
        assert lang.QUESTIONS

    def test_a_malformed_question_is_refused_at_the_described_boundary(self):
        """The description now *is* the parser for this kind.

        `derive span_ratio` names no object, and the description refuses it
        at `no_separator`.  The runtime raises, as it always did -- but the
        refusal is now the described one rather than a hand-written check.
        """
        assert lang.parse("derive span_ratio").boundary == "no_separator"
        with pytest.raises(QueryError):
            parse_query("derive span_ratio")


# ===========================================================================
# 8.  THE PREAMBLE -- WHAT MAY COME BEFORE THE OPENING
# ===========================================================================

class TestThePreamble:
    """A described leading remainder, skipped as a described act."""

    def test_the_preamble_is_an_ordered_list_of_justified_pieces(self):
        for piece in D.STANDARD_PREAMBLE.pieces:
            assert piece.phrasing.alternatives
            assert piece.phrasing.why
        assert D.STANDARD_PREAMBLE.why

    def test_courtesy_repeats_and_the_interrogative_does_not(self):
        """The shipped parser strips fillers in a loop and an opener once."""
        courtesy, interrogative = D.STANDARD_PREAMBLE.pieces
        assert courtesy.repeatable
        assert not interrogative.repeatable
        tokens = Q.tokenise("please kindly could you what is measure hot")
        end, taken = D.STANDARD_PREAMBLE.skip(tokens)
        assert taken == ("please", "kindly", "could you", "what is")
        assert tokens[end] == "measure"

    def test_the_interrogative_may_not_precede_the_courtesy(self):
        """The order in the description is the order on the surface."""
        tokens = Q.tokenise("what is please measure hot")
        end, taken = D.STANDARD_PREAMBLE.skip(tokens)
        assert taken == ("what is",)
        assert tokens[end] == "please"

    def test_every_preamble_piece_is_counted_as_a_judgement(self):
        assert D.STANDARD_PREAMBLE.judgements == len(
            D.STANDARD_PREAMBLE.pieces)
        assert D.COURTESY_PREAMBLE.judgements == len(
            D.COURTESY_PREAMBLE.pieces)

    def test_skipping_a_described_preamble_leaves_the_match_unchanged(self):
        """The Lean counterpart is `GLM.Question.runPre_of_skipped`."""
        plain = lang.parse("measure hot in tea")
        for form in D.STANDARD_PREAMBLE.forms():
            decorated = lang.parse(form + " measure hot in tea")
            assert decorated.matched, form
            assert decorated.kind == plain.kind
            assert lang.options_of(decorated) == lang.options_of(plain)

    def test_an_undescribed_leading_word_is_still_declined(self):
        for stray, _why in build.STRAY_OPENINGS:
            out = lang.parse(stray + " measure hot in tea")
            assert not out.matched, stray
            assert out.boundary == "unrecognised_opening"

    def test_the_preamble_forms_are_reported_and_not_zero(self, summary):
        assert summary["surface"]["preamble_forms"] == sum(
            len(spec.preamble.forms()) for spec in D.QUESTIONS
            if spec.preamble is not None)
        assert summary["surface"]["preamble_forms"] > 0


# ===========================================================================
# 9.  THE NARROWING -- WHAT DESCRIBING THE PREAMBLE COSTS
# ===========================================================================

class TestTheNarrowing:
    """Describing the leading remainder is a commitment, and it is measured.

    Letting the opening float free would accept anything before it.  The
    description accepts only what it names, so it declines questions the
    branches answered -- and every one of those answers put the stray words
    inside an option, which is what makes the narrowing a repair.
    """

    def test_there_are_witnesses_and_each_says_why_it_is_stray(self):
        rows = build.narrowing()
        assert rows["witnesses"]
        for row in rows["witnesses"]:
            assert row["why"]

    def test_every_witness_is_declined_at_the_opening(self):
        rows = build.narrowing()
        for row in rows["witnesses"]:
            assert row["described"] == "unrecognised_opening", row["question"]

    def test_every_witness_is_misread_by_the_deleted_branches(self):
        rows = build.narrowing()
        for row in rows["witnesses"]:
            assert row["polluted"] or row["shipped_kind"] is None, (
                row["question"])

    def test_the_narrowing_is_exact_and_reported(self, summary):
        rows = build.narrowing()
        assert rows["exact"]
        assert rows["declined"] == rows["misread_by_the_parser"]
        assert summary["verdict"]["narrowing_witnesses"] == len(
            rows["witnesses"])


# ===========================================================================
# 10.  THE BRANCHES ARE GONE
# ===========================================================================

class TestTheBranchesAreGone:
    """The parser reads the descriptions; the old code is frozen elsewhere.

    A measurement against a parser that has itself become the descriptions
    would be vacuous, so the branches deleted from
    :mod:`glm_universal.runtime.parser` are kept verbatim in
    :mod:`glm_universal.language.legacy` and the agreement is measured
    against *those*.
    """

    #: The names of the deleted branches: each one was the whole of how a
    #: kind used to be recognised, and none of them may come back.
    DELETED = ("_COMPARATIVE_INFIX", "_COMPARATIVE_USE",
               "_split_comparative_use", "_match_comparative",
               "_COMPARE_RELATION", "SEMANTICS_KEYWORDS",
               "_detect_semantics", "_strip_semantics_qualifier")

    def test_the_parser_holds_no_branch_for_a_described_kind(self):
        import inspect
        from glm_universal.runtime import parser as P
        source = inspect.getsource(P)
        for kind in ("derive", "measure", "task"):
            assert 'kind == "%s"' % kind not in source, kind
        for name in self.DELETED:
            assert name not in source, name

    def test_the_deleted_branches_are_frozen_and_not_re_implemented(self):
        """Every deleted name lives in the frozen copy, and only there."""
        import inspect
        from glm_universal.language import legacy as L
        frozen = inspect.getsource(L)
        for name in self.DELETED:
            assert name in frozen, name

    def test_the_parser_dispatches_the_described_kinds_to_the_shapes(self):
        import inspect
        from glm_universal.runtime import parser as P
        source = inspect.getsource(P)
        assert "DESCRIBED_KINDS" in source
        assert "_described_query" in source

    def test_nothing_in_the_runtime_imports_the_frozen_copy(self):
        """Named in a docstring is fine; reached in code is not."""
        import ast
        import pathlib
        import glm_universal.runtime as R
        root = pathlib.Path(R.__file__).parent
        for path in sorted(root.rglob("*.py")):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    assert "legacy" not in (node.module or ""), path.name
                    for alias in node.names:
                        assert alias.name != "legacy_parse", path.name
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "legacy" not in alias.name, path.name
                elif isinstance(node, ast.Attribute):
                    assert node.attr != "legacy_parse", path.name

    def test_the_frozen_branches_still_read_the_corpus(self):
        for kind, question, _fills in build.corpus():
            read = build._shipped(question)
            assert read is not None, question
            assert read[0] == kind, question

    def test_the_live_parser_agrees_with_the_frozen_branches(self):
        for kind, question, _fills in build.corpus():
            live = parse_query(question)
            old = build._shipped(question)
            assert live.kind == old[0] == kind, question
            for key, value in old[1].items():
                assert live.options.get(key) == value, (question, key)

    def test_the_frozen_shaped_branches_read_the_infix_corpus(self):
        for kind, question, _fills in build.infix_corpus():
            read = lang.legacy_parse_shaped(question)
            assert read is not None, question
            assert read[0] == kind, question

    def test_the_evaluation_questions_of_these_kinds_still_parse(self):
        from glm_universal.evaluation.cases import CASES
        seen = 0
        for case in CASES:
            if case.kind not in D.DESCRIBED_KINDS or case.expect != "answer":
                continue
            seen += 1
            assert parse_query(case.question).kind == case.kind, case.question
        assert seen > 0

    def test_a_question_of_no_described_shape_is_left_to_the_parser(self):
        """Deleting the branches did not narrow the runtime's other kinds."""
        assert parse_query("report language").kind == "report"
        assert parse_query("nearest tea").kind == "nearest"


# ===========================================================================
# 11.  THE SECOND SHAPE FAMILY -- AN OPERATOR THAT CUTS THE QUESTION
# ===========================================================================

class TestTheInfixFamily:
    """`verify`, `analogy` and the relational `compare`, described.

    The question the last round left open was whether a *second* described
    shape covers more than one kind.  It covers three; the count is the
    answer, and what it does not cover is named in ``UNDESCRIBED_PARTS``.
    """

    def test_every_infix_kind_is_a_runtime_kind(self):
        for kind in D.INFIX_KINDS:
            assert kind in KINDS

    def test_the_families_overlap_only_where_a_kind_has_two_shapes(self):
        """``compare`` is described twice, and that is the finding.

        ``compare sqrt(2) and 1.5`` and ``is sqrt(2) greater than 7/5`` ask
        the same question in two shapes -- an opening with a list, and an
        operator between two notations -- so one kind is covered by two
        families.  It is the only overlap, and a second one appearing
        without a reason would fail here.
        """
        assert set(D.INFIX_KINDS) & set(D.DESCRIBED_KINDS) == {"compare"}
        assert not set(D.NESTED_KINDS) & set(D.INFIX_KINDS)
        assert not set(D.NESTED_KINDS) & set(D.DESCRIBED_KINDS)

    def test_every_operator_alternative_says_why_it_is_one_set(self):
        for spec in D.INFIX_QUESTIONS:
            assert spec.operator.alternatives
            assert spec.operator.why
            if spec.inner is not None:
                assert spec.inner.why

    def test_every_operand_carries_a_known_role(self):
        for spec in D.INFIX_QUESTIONS:
            for operand in spec.operands:
                assert operand.role in Q.ROLES

    def test_a_carried_operand_is_one_of_the_described_operands(self):
        for spec in D.INFIX_QUESTIONS:
            names = {operand.name for operand in spec.operands}
            assert set(spec.carried) <= names

    def test_an_equation_is_cut_at_its_operator(self):
        out = lang.parse_infix("verify sqrt(2) = 1", D.INFIX_QUESTIONS)
        assert out.matched and out.kind == "verify"
        assert out.fills == {"lhs": "sqrt(2)", "rhs": "1"}

    def test_the_opening_is_optional(self):
        with_verb = lang.parse_infix("check a = b", D.INFIX_QUESTIONS)
        without = lang.parse_infix("a = b", D.INFIX_QUESTIONS)
        assert with_verb.fills == without.fills == {"lhs": "a", "rhs": "b"}

    def test_an_analogy_is_cut_twice(self):
        out = lang.parse_infix("tea : cup :: coffee : ?", D.INFIX_QUESTIONS)
        assert out.matched and out.kind == "analogy"
        assert out.fills["a"] == "tea" and out.fills["c"] == "coffee"

    def test_the_hole_of_an_analogy_is_described_but_not_carried(self):
        spec = D.infix_by_kind("analogy")
        assert "d" in {operand.name for operand in spec.operands}
        assert "d" not in spec.carried

    def test_an_operator_alternative_may_carry_a_meaning(self):
        greater = lang.parse_infix("is tea bigger than cup",
                                   D.INFIX_QUESTIONS)
        less = lang.parse_infix("is tea smaller than cup", D.INFIX_QUESTIONS)
        assert greater.meaning == "greater"
        assert less.meaning == "less"
        assert greater.fills == less.fills

    def test_case_is_preserved_because_an_operand_is_a_notation(self):
        out = lang.parse_infix("verify Force = Mass * A", D.INFIX_QUESTIONS)
        assert out.fills["rhs"] == "Mass * A"

    def test_a_question_with_no_operator_is_declined(self):
        out = lang.parse_infix("measure hot in tea", D.INFIX_QUESTIONS)
        assert not out.matched
        assert out.boundary == "no_operator"

    def test_an_empty_operand_is_declined(self):
        out = lang.parse_infix("verify = 1", D.INFIX_QUESTIONS)
        assert not out.matched
        assert out.boundary == "empty_lhs"

    def test_every_named_infix_boundary_has_a_witness(self, summary):
        assert summary["infix"]["refusals"] > 0

    def test_the_infix_corpus_is_generated_and_not_small(self, summary):
        assert summary["infix_agreement"]["corpus"] > 100

    def test_every_infix_question_agrees_with_the_shipped_parser(self):
        for kind, question, _operands in build.infix_corpus():
            mine = lang.parse_infix(question, D.INFIX_QUESTIONS)
            theirs = parse_query(question)
            assert mine.matched, question
            assert mine.kind == theirs.kind == kind, question

    def test_a_modifier_directs_the_reading_without_being_an_operand(self):
        plain = lang.parse_infix("verify force = mass * acceleration",
                                 D.INFIX_QUESTIONS)
        head = lang.parse_infix("check tensor force = mass * acceleration",
                                D.INFIX_QUESTIONS)
        frame = lang.parse_infix(
            "verify force = mass * acceleration under tensor semantics",
            D.INFIX_QUESTIONS)
        assert plain.options["semantics"] == "scalar"
        assert head.options["semantics"] == frame.options["semantics"] \
            == "full"
        assert head.fills == frame.fills == plain.fills

    def test_a_modifier_inside_an_expression_is_left_alone(self):
        """Only the head and the trailing frame are directive positions."""
        out = lang.parse_infix("verify a = tensor_rank * b",
                               D.INFIX_QUESTIONS)
        assert out.fills["rhs"] == "tensor_rank * b"

    def test_a_trailing_option_narrows_without_moving_an_operand(self):
        plain = lang.parse_infix("hot : temperature :: fast : ?",
                                 D.INFIX_QUESTIONS)
        narrow = lang.parse_infix(
            "hot : temperature :: fast : ? in physics.dimension top 5",
            D.INFIX_QUESTIONS)
        assert narrow.options["subspace"] == "physics.dimension"
        assert narrow.options["limit"] == 5
        assert narrow.carried(D.infix_by_kind("analogy")) == plain.carried(
            D.infix_by_kind("analogy"))

    def test_a_closing_is_an_opening_written_after_the_question(self):
        opened = lang.parse_infix("verify force = mass * acceleration",
                                  D.INFIX_QUESTIONS)
        closed = lang.parse_infix("force = mass * acceleration holds",
                                  D.INFIX_QUESTIONS)
        assert closed.fills == opened.fills
        assert D.VERIFY_QUESTION.closing is not None
        assert D.VERIFY_QUESTION.closing.why

    def test_no_question_of_another_kind_is_cut(self, summary):
        assert summary["infix_agreement"]["false_positives"] == ()
        assert summary["infix_agreement"]["outside"] > 50

    def test_the_agreement_is_exact(self, summary):
        assert summary["infix_agreement"]["exact"]
        assert summary["infix_agreement"]["disagreed"] == ()

    def test_what_the_family_does_not_cover_is_named(self):
        parts = build.undescribed_parts()
        assert parts
        for part in parts:
            assert part["part"] and part["why"]

    def test_the_family_is_wired_into_the_runtime(self):
        """The infix kinds are read off the descriptions, not recognised."""
        import inspect
        from glm_universal.runtime import parser as P
        source = inspect.getsource(P)
        assert "_described_infix_query" in source
        for kind in D.INFIX_KINDS:
            assert parse_query(_INFIX_WITNESS[kind]).kind == kind, kind

    def test_the_verdict_counts_every_family(self, summary):
        verdict = summary["verdict"]
        assert verdict["shape_families"] == 3
        assert verdict["kinds_covered"] == len(
            set(D.DESCRIBED_KINDS) | set(D.INFIX_KINDS)
            | set(D.NESTED_KINDS))
        assert verdict["kinds_read_off"] == verdict["kinds_covered"]


#: One question per infix kind, used to show the runtime reads it off the
#: description rather than off a branch.
_INFIX_WITNESS = {
    "verify": "verify force = mass * acceleration",
    "analogy": "hot : temperature :: fast : ?",
    "compare": "is sqrt(2) greater than 7/5",
}


# ===========================================================================
# 12.  THE LIST SLOT
# ===========================================================================

class TestTheListSlot:
    """One hole, a sequence of fillings, and two ranks of separators.

    ``compare sqrt(2) and 1.5`` is a slot shape whose slot holds a *list*.
    The branch it replaces cut on a comma or an ``and`` first and reached
    for ``or`` / ``versus`` / ``vs`` only when that left one value, and the
    description says so with two ranks rather than one merged set.
    """

    def spec(self):
        return D.question_by_kind("compare")

    def test_the_list_is_cut_at_the_first_rank(self):
        out = build.parse("compare sqrt(2) and 1.5")
        assert out.matched
        assert out.fills["left"] == "sqrt(2)"
        assert out.fills["right"] == "1.5"

    def test_the_comma_is_a_separator_only_where_a_list_is_described(self):
        assert Q.tokenise("a, b") == ("a", "b")
        assert Q.tokenise("a, b", marks=True) == ("a", ",", "b")

    def test_the_second_rank_is_reached_only_when_the_first_leaves_one(self):
        out = build.parse("compare 1/3 versus 0.333")
        assert out.matched and out.fills["right"] == "0.333"

    def test_the_ranks_are_not_merged(self):
        """``x or y and z`` is two items, as the branch read it."""
        out = build.parse("compare x or y and z")
        assert out.matched
        assert out.fills["left"] == "x or y"
        assert out.fills["right"] == "z"
        assert lang.legacy_parse_shaped("compare x or y and z")[1]["left"] \
            == "x or y"

    def test_a_list_item_keeps_its_case(self):
        out = build.parse("compare Pb and Fe")
        assert out.matched
        assert (out.fills["left"], out.fills["right"]) == ("Pb", "Fe")

    def test_a_short_list_is_declined_at_its_own_boundary(self):
        out = build.parse("compare sqrt(2)")
        assert not out.matched
        assert out.boundary == "short_values"
        assert self.spec().refusal("short_values").raises

    def test_the_opening_that_was_written_is_carried(self):
        for question in ("compare 3 and 4", "which is bigger, 3 or 4"):
            out = build.parse(question)
            assert build.options_of(out)["relation"] == "compare"

    def test_every_separator_the_shape_admits_is_in_the_corpus(self):
        rows = [question for kind, question, _ in build.corpus()
                if kind == "compare"]
        for surface in self.spec().shape[1].separator_forms():
            assert any(surface in question for question in rows), surface


# ===========================================================================
# 13.  THE THIRD SHAPE FAMILY -- AN OPERATOR OVER TWO MATCHES
# ===========================================================================

class TestTheNestedFamily:
    """A comparative: an operator whose operands are themselves matches.

    Each side of ``is cold in stellar_surface hotter than hot in tea`` has
    to be a measured use, which is the *measure* shape -- so the nested
    description holds the shape its sides nest rather than a copy of it.
    """

    def spec(self):
        return D.nested_by_kind("comparative")

    def test_the_nested_kind_is_a_runtime_kind(self):
        for kind in D.NESTED_KINDS:
            assert kind in KINDS

    def test_the_sides_nest_a_described_shape_rather_than_copying_it(self):
        assert self.spec().side.shape is D.MEASURE_QUESTION

    def test_the_nesting_only_tightens(self):
        """A nested side can be harder to match, never easier."""
        side = self.spec().side
        nested = {piece.name: piece for piece in side.pieces
                  if isinstance(piece, Q.Slot)}
        for slot_ in D.MEASURE_QUESTION.slots:
            if slot_.name not in nested:
                continue
            tightened = nested[slot_.name]
            assert tightened.optional <= slot_.optional
            assert tightened.form in Q.FORMS

    def test_both_forms_of_the_operator_are_read(self):
        spec = self.spec()
        comparative = lang.match_nested(
            spec, "is hot in tea hotter than cold in tea")
        equative = lang.match_nested(
            spec, "is hot in tea as hot as cold in tea")
        assert comparative.matched and not comparative.equative
        assert equative.matched and equative.equative
        assert comparative.word == "hotter" and equative.word == "hot"

    def test_the_operator_is_open_because_the_register_decides(self):
        """A degree word the register has never seen still parses here."""
        out = lang.match_nested(
            self.spec(), "is squeakier in tea squeakier than dull in tea")
        assert out.matched and out.word == "squeakier"

    def test_a_side_that_is_not_a_use_is_declined_and_named(self):
        out = lang.match_nested(self.spec(),
                                "is sqrt(2) greater than 7/5")
        assert not out.matched
        assert out.boundary == "left_not_a_use"

    def test_a_side_with_no_class_is_declined(self):
        out = lang.match_nested(self.spec(),
                                "is hot hotter than cold in tea")
        assert not out.matched

    def test_the_runtime_reads_the_comparative_off_the_description(self):
        import inspect
        from glm_universal.runtime import parser as P
        assert "_described_nested_query" in inspect.getsource(P)
        query = parse_query("is hot in tea hotter than cold in tea")
        assert query.kind == "comparative"
        assert query.options["left_class"] == "tea"

    def test_the_nested_corpus_is_generated_and_not_small(self, summary):
        assert summary["nested_agreement"]["corpus"] > 100

    def test_the_nested_agreement_is_exact(self, summary):
        agreed = summary["nested_agreement"]
        assert agreed["disagreed"] == ()
        assert agreed["declined"] == ()
        assert agreed["false_positives"] == ()
        assert agreed["outside"] > 50

    def test_an_exact_real_comparison_is_not_read_as_a_comparative(self):
        assert parse_query("is sqrt(2) greater than 7/5").kind == "compare"


# ===========================================================================
# 14.  WHERE THE DESCRIPTION READS MORE THAN THE BRANCH DID
# ===========================================================================

class TestTheWidening:
    """Reuse has a price, and the price is measured.

    Nesting the measure shape means admitting every separator the measure
    shape admits.  The branch spelled its sides out again and listed four
    of the five, so questions written with ``relative to`` are read here
    and were unknown to it.  That is not a disagreement -- the branch gave
    no answer to differ from -- and it is not free either, so it is
    declared, and every widened question is accounted for by it.
    """

    def test_the_declared_witness_still_holds(self):
        audit = build.widening()
        assert audit["witnesses"] >= 1
        assert audit["holds"]
        for row in audit["rows"]:
            assert row["holds"], row["question"]
            assert row["shipped"] == "declined"
            assert row["why"]

    def test_the_cause_is_measured_rather_than_asserted(self):
        audit = build.widening()
        assert "relative to" in audit["refused"]
        assert "in" in audit["admitted"]

    def test_every_widened_question_is_accounted_for(self, summary):
        audit = build.widening()
        assert audit["unexplained"] == ()
        assert audit["measured"] == len(
            summary["nested_agreement"]["widened"])

    def test_a_widened_question_is_answered_and_was_not_before(self):
        question = "is hot relative to tea hotter than hot in tea"
        assert parse_query(question).kind == "comparative"
        assert lang.legacy_parse_shaped(question) is None


# ===========================================================================
# 15.  HOW MUCH OF THE SURFACE IS DESCRIBED
# ===========================================================================

class TestTheCoverage:
    """The count, not the claim."""

    def test_the_described_kinds_are_counted_against_the_runtime_kinds(self):
        covered = build.coverage()
        assert covered["kinds"] == len([k for k in KINDS if k != "unknown"])
        assert covered["described"] == len(covered["described_kinds"])
        assert covered["described"] + len(covered["undescribed_kinds"]) == \
            covered["kinds"]

    def test_what_is_not_described_is_named(self):
        covered = build.coverage()
        parts = build.undescribed_parts()
        assert covered["undescribed_kinds"]
        assert parts and all(part["part"] and part["why"] for part in parts)

    def test_every_described_kind_is_read_off_its_description(self):
        """No described kind still has a branch that recognises it."""
        import inspect
        from glm_universal.runtime import parser as P
        source = inspect.getsource(P)
        for name in TestTheBranchesAreGone.DELETED:
            assert name not in source

"""Tests for ``glm_universal.runtime`` and the ``GLM.py`` entry point.

Five concerns, in order:

1. **The parser** -- that classification is a deterministic function of the
   string, that every rule fires on the input it is meant to fire on and
   yields to the ones above it, and that a malformed query raises while an
   unrecognised one comes back with suggestions.
2. **The session** -- register loading and laziness, the spatial register's
   own geometry, concept resolution, one test per solver, and the property
   that two independently constructed sessions answer identically.
3. **Three Column Thinking** -- that columns 1 and 2 are aligned by
   construction, that every generated script is float-free by AST, that
   running column 3 in a fresh interpreter reproduces column 2, and -- the
   test that gives the other one its meaning -- that a *deliberately
   falsified* column 2 is caught rather than waved through.
4. **The CLI** -- batch, interactive, export, exit codes.
5. **Package-wide exactness** -- no float literal, no ``float()`` call, no
   RNG import anywhere in ``runtime/`` or ``GLM.py``.

Subprocess verification is the slow part; it is confined to the classes named
``...Subprocess`` so it is easy to deselect with ``-k``.
"""

from __future__ import annotations

import ast
import importlib.util
import io
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.reasoning import analogy as an
from glm_universal.runtime import parser as PA
from glm_universal.runtime import session as SE
from glm_universal.runtime import tct_engine as TE
from glm_universal.substrate import mog

RUNTIME_DIR = Path(SE.__file__).resolve().parent
REPO_ROOT = RUNTIME_DIR.parent.parent
GLM_PATH = REPO_ROOT / "GLM.py"


def _load_glm():
    """Import ``GLM.py`` by path; it is a script at the repo root, not a module."""
    spec = importlib.util.spec_from_file_location("glm_entry", GLM_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sess():
    """One session for the whole module -- loading the registers costs seconds."""
    return SE.GeometricSession()


@pytest.fixture(scope="module")
def glm():
    return _load_glm()


# ===========================================================================
# 1.  THE PARSER
# ===========================================================================

class TestNormalisation:

    def test_normalise_folds_case_space_and_punctuation(self):
        for surface in ("Speed of Light", "speed-of-light", "speed_of_light",
                        "  SPEED  OF  LIGHT  ", "speed.of.light"):
            assert PA.normalise(surface) == "speed_of_light"

    def test_normalise_of_empty_is_empty(self):
        assert PA.normalise("   ") == ""
        assert PA.normalise("!!!") == ""

    def test_tokenise_keeps_the_analogy_operator_whole(self):
        assert "::" in PA.tokenise("a : b :: c : ?")

    def test_tokenise_keeps_a_dotted_subspace_name_whole(self):
        assert "physics.dimension" in PA.tokenise("in physics.dimension")

    def test_levenshtein_is_a_metric_on_the_cases_we_rely_on(self):
        assert PA.levenshtein("abc", "abc") == 0
        assert PA.levenshtein("", "abc") == 3
        assert PA.levenshtein("abc", "") == 3
        assert PA.levenshtein("kitten", "sitting") == 3
        assert PA.levenshtein("a", "b") == PA.levenshtein("b", "a")

    def test_levenshtein_returns_an_int_not_a_ratio(self):
        assert isinstance(PA.levenshtein("carbon", "carbn"), int)


class TestStructuralSplitters:

    def test_split_analogy_returns_four_terms(self):
        assert PA.split_analogy("force : energy :: pressure : ?") == (
            "force", "energy", "pressure", "?")

    @pytest.mark.parametrize("bad", [
        "force : energy : pressure",          # no '::'
        "a :: b",                             # halves lack ':'
        "a : b :: c : d :: e : f",            # two '::'
        "a : b :: : ?",                       # empty operand
    ])
    def test_split_analogy_rejects_malformed_input(self, bad):
        with pytest.raises(PA.QueryError):
            PA.split_analogy(bad)

    def test_split_equation_splits_at_the_single_equals(self):
        assert PA.split_equation("force = mass * acceleration") == (
            "force", "mass * acceleration")

    @pytest.mark.parametrize("bad", ["force", "force =", "= mass",
                                     "a = b = c"])
    def test_split_equation_rejects_malformed_input(self, bad):
        with pytest.raises(PA.QueryError):
            PA.split_equation(bad)

    def test_comparison_operators_are_not_read_as_assignment(self):
        for text in ("a == b", "a != b", "a <= b", "a >= b"):
            assert PA._top_level_equals(text) == []


class TestClassification:

    def test_the_analogy_operator_wins_over_everything(self, sess):
        q = PA.parse_query("describe force : energy :: pressure : ?",
                           sess.index)
        assert q.kind == "analogy"
        assert q.rule == "analogy_operator"

    def test_an_equation_is_a_verify(self, sess):
        q = PA.parse_query("force = mass * acceleration", sess.index)
        assert q.kind == "verify"
        assert q.operands == ("force", "mass * acceleration")

    def test_a_verify_keyword_is_stripped_before_splitting(self, sess):
        q = PA.parse_query("verify force = mass * acceleration", sess.index)
        assert q.kind == "verify"
        assert q.operands[0] == "force"

    def test_semantics_defaults_to_scalar_and_says_so(self, sess):
        q = PA.parse_query("force = mass * acceleration", sess.index)
        assert q.options["semantics"] == "scalar"
        assert any("defaulted to 'scalar'" in line for line in q.trace)

    def test_a_semantics_keyword_overrides_the_default(self, sess):
        q = PA.parse_query("check tensor force = mass * acceleration",
                           sess.index)
        assert q.options["semantics"] == "full"

    def test_a_leading_semantics_qualifier_is_not_left_in_the_expression(
            self, sess):
        """Regression: 'tensor' directs the comparison, it is not a quantity."""
        q = PA.parse_query("check tensor force = mass * acceleration",
                           sess.index)
        assert q.operands == ("force", "mass * acceleration")
        assert sess.ask("check tensor force = mass * acceleration").ok

    def test_a_trailing_semantics_phrase_is_stripped(self, sess):
        q = PA.parse_query(
            "force = mass * acceleration under full semantics", sess.index)
        assert q.options["semantics"] == "full"
        assert q.operands == ("force", "mass * acceleration")

    def test_a_qualifier_inside_an_expression_is_left_alone(self, sess):
        """Deleting it mid-expression would change the equation being audited."""
        q = PA.parse_query("a = b * scalar * c", sess.index)
        assert q.operands == ("a", "b * scalar * c")

    def test_the_two_semantics_can_disagree_on_the_same_relation(self, sess):
        scalar = sess.ask("force = mass * acceleration")
        tensor = sess.ask("check tensor force = mass * acceleration")
        assert scalar.ok and tensor.ok
        assert scalar.payload["verdict"]["semantics"] == "scalar"
        assert tensor.payload["verdict"]["semantics"] == "full"

    def test_a_bare_concept_is_a_describe(self, sess):
        q = PA.parse_query("carbon", sess.index)
        assert (q.kind, q.domain, q.operands) == ("describe", "chemistry",
                                                  ("C",))
        assert q.rule == "bare_concept"

    def test_a_weak_opener_yields_to_a_specific_verb(self, sess):
        q = PA.parse_query("what is the nearest 3 to pressure", sess.index)
        assert q.kind == "nearest"
        assert q.operands == ("pressure",)
        assert q.options["limit"] == 3

    def test_a_weak_opener_alone_still_means_describe(self, sess):
        q = PA.parse_query("what is carbon", sess.index)
        assert (q.kind, q.operands) == ("describe", ("C",))

    def test_a_cluster_count_does_not_leak_into_the_operands(self, sess):
        q = PA.parse_query("cluster carbon, nitrogen and oxygen into 2",
                           sess.index)
        assert q.kind == "cluster"
        assert q.operands == ("C", "N", "O")
        assert q.options["k"] == 2

    def test_a_word_boundary_is_required_for_a_keyword(self, sess):
        # 'checksum' contains 'check' but must not classify as a verify.
        q = PA.parse_query("checksum", sess.index)
        assert q.kind != "verify"

    def test_an_unrecognised_query_is_returned_not_raised(self, sess):
        q = PA.parse_query("zzzz_not_a_concept_at_all", sess.index)
        assert q.kind == "unknown"
        assert q.rule == "unresolved"

    def test_a_near_miss_gets_suggestions(self, sess):
        q = PA.parse_query("carbn", sess.index)
        assert q.kind == "unknown"
        assert "carbon" in q.suggestions

    def test_a_chained_equality_is_rejected(self, sess):
        with pytest.raises(PA.QueryError):
            PA.parse_query("a = b = c", sess.index)

    def test_an_empty_query_is_rejected(self, sess):
        with pytest.raises(PA.QueryError):
            PA.parse_query("   ", sess.index)

    def test_parsing_is_a_pure_function_of_the_string(self, sess):
        first = PA.parse_query("cluster carbon, oxygen into 2", sess.index)
        second = PA.parse_query("cluster carbon, oxygen into 2", sess.index)
        assert first.as_dict() == second.as_dict()

    def test_the_parse_trace_records_every_decision(self, sess):
        q = PA.parse_query("force = mass * acceleration", sess.index)
        assert q.trace and all(isinstance(line, str) for line in q.trace)


class TestConceptIndex:

    def test_the_index_covers_every_register(self, sess):
        for domain in SE.DOMAINS:
            for obj in sess.register(domain):
                assert sess.index.lookup(obj.name, domain) == (domain,
                                                               obj.name)

    def test_an_element_resolves_by_symbol_and_by_name(self, sess):
        assert sess.index.lookup("C") == ("chemistry", "C")
        assert sess.index.lookup("carbon") == ("chemistry", "C")

    def test_a_domain_hint_restricts_resolution(self, sess):
        assert sess.index.lookup("carbon", "physics") is None
        assert sess.index.lookup("carbon", "chemistry") == ("chemistry", "C")

    def test_an_unknown_surface_form_resolves_to_none(self, sess):
        assert sess.index.lookup("definitely_not_a_concept") is None

    def test_ambiguity_is_broken_by_the_fixed_domain_priority(self):
        # Two registers, one shared name: physics must win by DOMAIN_PRIORITY.
        class Fake:
            def __init__(self, name):
                self.name = name
                self.attributes = {}
        index = PA.ConceptIndex.build({"chemistry": [Fake("energy")],
                                       "physics": [Fake("energy")]})
        assert index.is_ambiguous("energy")
        assert index.lookup("energy")[0] == "physics"
        assert PA.DOMAIN_PRIORITY.index("physics") < \
            PA.DOMAIN_PRIORITY.index("chemistry")

    def test_suggestions_are_sorted_and_bounded(self, sess):
        near = sess.index.suggest("carbn", limit=3)
        assert len(near) <= 3
        assert near == tuple(sorted(
            near, key=lambda a: (PA.levenshtein("carbn", a), a)))

    def test_an_empty_surface_form_suggests_nothing(self, sess):
        assert sess.index.suggest("") == ()


# ===========================================================================
# 2.  THE SESSION
# ===========================================================================

class TestSessionConfiguration:

    def test_an_unknown_domain_is_rejected(self):
        with pytest.raises(ValueError):
            SE.GeometricSession(domains=["astrology"])

    def test_an_unknown_basis_is_rejected(self):
        with pytest.raises(ValueError):
            SE.GeometricSession(basis="cgs")

    def test_registers_load_lazily(self):
        fresh = SE.GeometricSession()
        assert fresh.loaded_domains() == ()
        fresh.register("spatial")
        assert fresh.loaded_domains() == ("spatial",)

    def test_a_register_is_loaded_at_most_once(self):
        fresh = SE.GeometricSession()
        assert fresh.register("spatial") is fresh.register("spatial")

    def test_a_disabled_domain_cannot_be_loaded(self):
        limited = SE.GeometricSession(domains=["spatial"])
        with pytest.raises(SE.SolverError):
            limited.register("physics")

    def test_the_basis_can_be_switched_and_is_validated(self):
        fresh = SE.GeometricSession()
        assert fresh.basis == "EXT10"
        fresh.set_basis("SI7")
        assert fresh.basis == "SI7"
        with pytest.raises(ValueError):
            fresh.set_basis("nonsense")

    def test_the_register_sizes_are_the_documented_ones(self, sess):
        assert len(sess.register("physics")) == 660
        assert len(sess.register("chemistry")) == 118
        assert len(sess.register("spatial")) == 28

    def test_the_snapshot_is_json_serialisable(self, sess):
        json.dumps(sess.snapshot())


class TestSpatialRegister:

    def test_it_holds_the_documented_structures(self):
        objects = SE.spatial_objects()
        kinds = [o.attributes["kind"] for o in objects]
        assert kinds.count("tetrad") == 6
        assert kinds.count("frame_row") == 4
        assert kinds.count("octad") == 3 + 15
        assert len(objects) == 28

    def test_every_octad_is_a_golay_codeword_of_weight_eight(self):
        for obj in SE.spatial_objects():
            if obj.attributes["kind"] != "octad":
                continue
            mask = int(obj.attributes["mask"], 16)
            assert bin(mask).count("1") == 8
            assert mask in mog.GOLAY_SET

    def test_the_trio_bricks_partition_the_24_coordinates(self):
        bricks = [o for o in SE.spatial_objects()
                  if o.name.startswith("trio_brick_")]
        total = [0] * 24
        for brick in bricks:
            for i, bit in enumerate(brick.carrier):
                total[i] += int(bit)
        assert total == [1] * 24

    def test_the_sextet_tetrads_partition_the_24_coordinates(self):
        tetrads = [o for o in SE.spatial_objects()
                   if o.name.startswith("sextet_tetrad_")]
        total = [0] * 24
        for tetrad in tetrads:
            for i, bit in enumerate(tetrad.carrier):
                total[i] += int(bit)
        assert total == [1] * 24

    def test_the_carriers_round_trip_through_their_digit_stacks(self):
        for obj in SE.spatial_objects():
            assert obj.round_trip_ok(), obj.name

    def test_the_layout_names_mog_frame_cells(self):
        obj = SE.spatial_objects()[0]
        assert obj.layout[0].startswith("r")
        assert len(set(obj.layout)) == 24


class TestResolution:

    def test_resolve_finds_a_carrier_by_alias(self, sess):
        assert sess.resolve("carbon").name == "C"

    def test_resolve_reports_near_misses(self, sess):
        with pytest.raises(SE.SolverError) as exc:
            sess.resolve("carbn")
        assert "carbon" in str(exc.value)

    def test_resolve_respects_a_domain_hint(self, sess):
        with pytest.raises(SE.SolverError):
            sess.resolve("carbon", domain="physics")


class TestSolvers:

    def test_verify_accepts_a_true_relation(self, sess):
        sol = sess.ask("force = mass * acceleration")
        assert sol.ok and sol.kind == "verify"
        assert sol.expected["holds"] == "True"
        assert sol.expected["lhs_dimension"] == sol.expected["rhs_dimension"]

    def test_verify_rejects_a_false_relation_and_blames_facets(self, sess):
        sol = sess.ask("force = mass * velocity")
        assert sol.ok and sol.expected["holds"] == "False"
        assert sol.payload["verdict"]["failing_planes"]

    def test_verify_reports_an_unknown_concept_usefully(self, sess):
        sol = sess.ask("force = mass * zzzz_nope")
        assert not sol.ok
        assert "unknown concept" in sol.error

    def test_analogy_answers_in_the_default_subspace(self, sess):
        sol = sess.ask("force : energy :: pressure : ?")
        assert sol.ok and sol.kind == "analogy"
        assert sol.payload["subspace"] == "physics.dimension"
        assert sol.expected["answer"] in {o.name
                                          for o in sess.register("physics")}

    def test_analogy_reports_a_tie_rather_than_hiding_it(self, sess):
        sol = sess.ask("force : energy :: pressure : ?")
        tied = sol.payload["result"]["tied"]
        assert sol.expected["unique"] == str(len(tied) == 1)

    def test_analogy_rejects_an_unknown_subspace(self, sess):
        sol = sess.ask("force : energy :: pressure : ? in physics.nonsense")
        assert not sol.ok and "unknown subspace" in sol.error

    def test_analogy_needs_three_operands_from_one_domain(self, sess):
        sol = sess.ask("force : carbon :: pressure : ?")
        assert not sol.ok

    def test_describe_reports_a_lossless_stack(self, sess):
        sol = sess.ask("describe carbon")
        assert sol.ok and sol.expected["round_trip_ok"] == "True"
        assert int(sol.expected["depth"]) > 0

    def test_describe_of_a_spatial_carrier_finds_a_golay_codeword(self, sess):
        sol = sess.ask("describe trio_brick_0")
        assert sol.ok and sol.expected["is_golay_codeword"] == "True"

    def test_nearest_excludes_the_reference_and_honours_the_limit(self, sess):
        sol = sess.ask("nearest 4 to pressure")
        assert sol.ok and sol.kind == "nearest"
        names = eval(sol.expected["top_names"])  # a literal list of str
        assert len(names) == 4 and "pressure" not in names

    def test_nearest_distances_are_non_decreasing(self, sess):
        sol = sess.ask("nearest 5 to pressure")
        distances = [Fraction(s) for s in eval(sol.expected["top_distances2"])]
        assert distances == sorted(distances)

    def test_nearest_rejects_a_non_positive_limit(self, sess):
        sol = sess.ask("nearest 0 to pressure")
        assert not sol.ok

    def test_product_builds_a_checked_2a_triple(self, sess):
        sol = sess.ask("sakuma product")
        assert sol.ok and sol.kind == "product"
        assert sol.expected["position"] == "2A"
        u, v = int(sol.expected["u"]), int(sol.expected["v"])
        assert int(sol.expected["third_axis"]) == u ^ v

    def test_the_product_coefficients_are_the_sakuma_eighths(self, sess):
        sol = sess.ask("sakuma product")
        coeffs = dict(eval(sol.expected["coefficients"]))
        third = sol.expected["third_axis"]
        assert coeffs[sol.expected["u"]] == "1/8"
        assert coeffs[sol.expected["v"]] == "1/8"
        assert coeffs[third] == "-1/8"

    def test_product_refuses_a_non_type2_class(self, sess):
        sol = sess.ask("sakuma product 3 5")
        assert not sol.ok

    def test_cluster_partitions_the_named_carriers(self, sess):
        sol = sess.ask("cluster carbon, nitrogen, oxygen and helium into 2")
        assert sol.ok and sol.kind == "cluster"
        groups = eval(sol.expected["groups"])
        assert len(groups) == 2
        assert sorted(n for g in groups for n in g) == ["C", "He", "N", "O"]

    def test_cluster_merge_heights_are_exact_rationals(self, sess):
        sol = sess.ask("cluster carbon, nitrogen, oxygen into 2")
        for height in eval(sol.expected["merge_heights"]):
            assert Fraction(height) >= 0

    def test_cluster_refuses_a_cross_domain_mix(self, sess):
        sol = sess.ask("cluster carbon, force into 2")
        assert not sol.ok

    def test_cluster_refuses_a_single_carrier(self, sess):
        sol = sess.ask("cluster carbon into 1")
        assert not sol.ok

    def test_spatial_lays_a_carrier_out_on_the_mog_frame(self, sess):
        sol = sess.ask("mog grid of oxygen")
        assert sol.ok and sol.kind == "spatial"
        rows = eval(sol.expected["frame_rows"])
        assert len(rows) == 4 and all(len(r) == 6 for r in rows)
        assert sum(sum(r) for r in rows) == int(
            sol.expected["plane0_weight"])

    def test_spatial_brick_weights_sum_to_the_plane_weight(self, sess):
        sol = sess.ask("mog grid of oxygen")
        assert sum(eval(sol.expected["brick_weights"])) == int(
            sol.expected["plane0_weight"])

    def test_an_unrecognised_query_is_an_unsolved_solution(self, sess):
        sol = sess.ask("zzzz_not_a_concept_at_all")
        assert not sol.ok and sol.kind == "unknown"
        assert sol.steps  # it still explains itself


class TestHistoryAndDeterminism:

    def test_every_query_is_recorded_including_the_failures(self):
        fresh = SE.GeometricSession()
        fresh.ask("describe carbon")
        fresh.ask("zzzz_nope")
        assert [r.ok for r in fresh.history] == [True, False]
        assert [r.index for r in fresh.history] == [0, 1]

    def test_history_can_be_cleared_without_unloading_registers(self):
        fresh = SE.GeometricSession()
        fresh.ask("describe carbon")
        loaded = fresh.loaded_domains()
        fresh.clear_history()
        assert fresh.history == ()
        assert fresh.loaded_domains() == loaded

    def test_two_sessions_answer_a_query_identically(self):
        a = SE.GeometricSession().ask("force : energy :: pressure : ?")
        b = SE.GeometricSession().ask("force : energy :: pressure : ?")
        assert a.expected == b.expected
        assert [s.as_dict() for s in a.steps] == [s.as_dict() for s in b.steps]

    def test_asking_twice_in_one_session_gives_the_same_answer(self, sess):
        first = sess.ask("nearest 5 to pressure")
        second = sess.ask("nearest 5 to pressure")
        assert first.expected == second.expected

    def test_every_expected_value_is_a_string(self, sess):
        for text in ("force = mass * acceleration", "describe carbon",
                     "nearest 3 to pressure", "mog grid of oxygen"):
            sol = sess.ask(text)
            for key, value in sol.expected.items():
                assert isinstance(value, str), (text, key)

    def test_no_expected_value_is_a_float_repr(self, sess):
        sol = sess.ask("describe carbon")
        assert "/" in sol.expected["griess_norm2"]
        assert Fraction(sol.expected["griess_norm2"]) > 0


# ===========================================================================
# 3.  THREE COLUMN THINKING
# ===========================================================================

#: One query per solver kind.  Used both for the cheap structural checks and,
#: in the subprocess class below, for the full round trip.
KIND_QUERIES = [
    ("verify", "force = mass * acceleration"),
    ("analogy", "force : energy :: pressure : ?"),
    ("describe", "describe carbon"),
    ("nearest", "nearest 3 to pressure"),
    ("cluster", "cluster carbon, nitrogen and oxygen into 2"),
    ("spatial", "mog grid of oxygen"),
    ("product", "sakuma product"),
]


class TestTraceConstruction:

    @pytest.mark.parametrize("kind,text", KIND_QUERIES)
    def test_a_trace_is_built_for_every_kind(self, sess, kind, text):
        sol = sess.ask(text)
        assert sol.ok, sol.error
        trace = TE.build_trace(sol)
        assert trace.kind == kind
        assert trace.synchronized

    @pytest.mark.parametrize("kind,text", KIND_QUERIES)
    def test_columns_one_and_two_are_aligned(self, sess, kind, text):
        trace = TE.build_trace(sess.ask(text))
        assert len(trace.language) == len(trace.mathematics) == \
            len(trace.labels)
        assert all(line.strip() for line in trace.language)
        assert all(line.strip() for line in trace.mathematics)

    @pytest.mark.parametrize("kind,text", KIND_QUERIES)
    def test_every_generated_script_is_float_free(self, sess, kind, text):
        trace = TE.build_trace(sess.ask(text))
        ok, offenders = TE.script_is_exact(trace.script)
        assert ok, offenders

    @pytest.mark.parametrize("kind,text", KIND_QUERIES)
    def test_every_generated_script_parses(self, sess, kind, text):
        ast.parse(TE.build_trace(sess.ask(text)).script)

    @pytest.mark.parametrize("kind,text", KIND_QUERIES)
    def test_the_script_embeds_every_claim_of_column_two(self, sess, kind,
                                                         text):
        sol = sess.ask(text)
        trace = TE.build_trace(sol)
        for key in sol.expected:
            assert key in trace.script

    def test_script_is_exact_catches_a_float(self):
        ok, offenders = TE.script_is_exact("x = 1.5\n")
        assert not ok and "float literal" in offenders[0]

    def test_script_is_exact_catches_a_float_call(self):
        ok, offenders = TE.script_is_exact("x = float('1')\n")
        assert not ok and "float() call" in offenders[0]

    def test_script_is_exact_catches_an_rng_import(self):
        ok, offenders = TE.script_is_exact("import random\n")
        assert not ok and "random" in offenders[0]

    def test_script_is_exact_ignores_the_word_float_in_a_string(self):
        ok, _ = TE.script_is_exact("x = 'no float here'  # nor 1.5\n")
        assert ok

    def test_script_is_exact_reports_a_syntax_error(self):
        ok, offenders = TE.script_is_exact("def (:\n")
        assert not ok and "syntax error" in offenders[0]

    def test_rendering_refuses_an_unsolved_solution(self, sess):
        sol = sess.ask("zzzz_nope")
        with pytest.raises(TE.TCTError):
            TE.render_script(sol)

    def test_rendering_refuses_an_unknown_template(self, sess):
        sol = sess.ask("describe carbon")
        broken = SE.Solution(query=sol.query, kind=sol.kind,
                             answer=sol.answer, steps=sol.steps,
                             expected=sol.expected,
                             script_spec={"template": "no_such_template"})
        with pytest.raises(TE.TCTError):
            TE.render_script(broken)

    def test_a_trace_with_no_steps_is_refused(self, sess):
        sol = sess.ask("describe carbon")
        empty = SE.Solution(query=sol.query, kind=sol.kind, answer=sol.answer,
                            steps=(), expected=sol.expected,
                            script_spec=sol.script_spec)
        with pytest.raises(TE.TCTError):
            TE.build_trace(empty)

    def test_markdown_contains_all_three_columns(self, sess):
        trace = TE.build_trace(sess.ask("describe carbon"))
        text = TE.trace_to_markdown(trace)
        assert "Column 1 -- Language" in text
        assert "Column 2 -- Exact mathematics" in text
        assert "Column 3 -- executable script" in text

    def test_markdown_escapes_pipes_so_the_table_survives(self):
        assert TE._cell("a | b") == r"a \| b"

    def test_a_trace_is_json_serialisable(self, sess):
        trace = TE.build_trace(sess.ask("describe carbon"))
        json.dumps(trace.as_dict())

    def test_an_unverified_trace_does_not_claim_to_be_verified(self, sess):
        trace = TE.build_trace(sess.ask("describe carbon"))
        assert trace.verdict is None
        assert not trace.verified


class TestTraceVerificationSubprocess:
    """The slow class: each test starts a fresh interpreter."""

    @pytest.mark.parametrize("kind,text", KIND_QUERIES)
    def test_column_three_reproduces_column_two(self, sess, kind, text):
        trace = TE.verify_trace(TE.build_trace(sess.ask(text)), timeout=900)
        verdict = trace.verdict
        assert verdict.executed, verdict.stderr_tail
        assert verdict.returncode == 0, verdict.stderr_tail
        assert not verdict.mismatches, verdict.mismatches
        assert not verdict.missing_keys, verdict.missing_keys
        assert trace.verified

    def test_a_falsified_claim_is_caught(self, sess):
        """The test that gives the others their meaning.

        If column 2 is tampered with, the script must fail -- both by exit
        code and by the parent's own comparison.  Without this, a verifier
        that always said 'verified' would pass every other test here.
        """
        sol = sess.ask("describe carbon")
        tampered = dict(sol.expected)
        tampered["griess_norm2"] = "1/1"
        falsified = SE.Solution(
            query=sol.query, kind=sol.kind, answer=sol.answer,
            steps=sol.steps, expected=tampered,
            script_spec=sol.script_spec)
        trace = TE.verify_trace(TE.build_trace(falsified), timeout=300)
        assert trace.verdict.executed
        assert trace.verdict.returncode == 1
        assert not trace.verdict.matches_column2
        assert not trace.verified
        keys = [m[0] for m in trace.verdict.mismatches]
        assert keys == ["griess_norm2"]

    def test_a_missing_claim_is_caught(self, sess):
        """A claim the script never reports must not pass silently."""
        sol = sess.ask("describe carbon")
        extended = dict(sol.expected)
        extended["a_claim_no_script_computes"] = "42"
        widened = SE.Solution(
            query=sol.query, kind=sol.kind, answer=sol.answer,
            steps=sol.steps, expected=extended,
            script_spec=sol.script_spec)
        trace = TE.verify_trace(TE.build_trace(widened), timeout=300)
        assert trace.verdict.missing_keys == ("a_claim_no_script_computes",)
        assert not trace.verified

    def test_the_script_can_be_kept_for_inspection(self, sess, tmp_path):
        trace = TE.verify_trace(TE.build_trace(sess.ask("describe carbon")),
                                workdir=tmp_path, timeout=300)
        written = tmp_path / "tct_column3.py"
        assert written.exists()
        assert written.read_text(encoding="utf-8") == trace.script

    def test_a_timeout_is_reported_not_raised(self, sess):
        trace = TE.build_trace(sess.ask("sakuma product"))
        verdict = TE.verify_trace(trace, timeout=1).verdict
        # Either it finished inside the second or it timed out; both are
        # reported states, and neither raises.
        assert verdict.executed or "timed out" in verdict.stderr_tail

    def test_the_script_runs_from_any_working_directory(self, sess, tmp_path):
        """Column 3 must be self-contained -- it inserts its own sys.path."""
        trace = TE.build_trace(sess.ask("describe carbon"))
        assert str(TE.package_root()) in trace.script
        assert TE.verify_trace(trace, workdir=tmp_path, timeout=300).verified


# ===========================================================================
# 4.  THE CLI
# ===========================================================================

class TestCommandLine:

    def test_list_domains_prints_every_register(self, glm):
        out = io.StringIO()
        assert glm.main(["--list-domains"], out=out) == 0
        text = out.getvalue()
        for domain in SE.DOMAINS:
            assert domain in text
        assert "660" in text and "118" in text

    def test_a_batch_query_succeeds(self, glm):
        out = io.StringIO()
        code = glm.main(["-q", "force = mass * acceleration", "-c", "1,2"],
                        out=out)
        assert code == 0
        assert "holds under scalar semantics" in out.getvalue()

    def test_an_unsolved_batch_query_sets_exit_code_one(self, glm):
        out = io.StringIO()
        assert glm.main(["-q", "zzzz_nope"], out=out) == 1
        assert "UNSOLVED" in out.getvalue()

    def test_a_malformed_query_is_reported_not_crashed(self, glm):
        out = io.StringIO()
        assert glm.main(["-q", "a = b = c"], out=out) == 1
        assert "malformed" in out.getvalue()

    def test_bad_columns_are_a_usage_error(self, glm):
        out = io.StringIO()
        assert glm.main(["-q", "carbon", "-c", "9"], out=out) == 2
        assert glm.main(["-q", "carbon", "-c", "x"], out=out) == 2

    def test_no_arguments_prints_help_and_exits_two(self, glm):
        out = io.StringIO()
        assert glm.main([], out=out) == 2
        assert "usage" in out.getvalue().lower()

    def test_json_format_is_parseable(self, glm):
        out = io.StringIO()
        assert glm.main(["-q", "describe carbon", "-f", "json", "-c", "1,2"],
                        out=out) == 0
        payload = json.loads(out.getvalue())
        assert payload["kind"] == "describe"
        assert payload["column1_language"] and payload["column2_mathematics"]

    def test_markdown_format_renders_a_table(self, glm):
        out = io.StringIO()
        assert glm.main(["-q", "describe carbon", "-f", "markdown", "-c",
                         "1,2"], out=out) == 0
        assert "| # | Step |" in out.getvalue()

    def test_export_writes_markdown_json_and_python(self, glm, tmp_path):
        for suffix, probe in ((".md", "# Three Column Thinking"),
                              (".json", '"kind"'),
                              (".py", "import json")):
            target = tmp_path / f"trace{suffix}"
            out = io.StringIO()
            assert glm.main(["-q", "describe carbon", "--export-trace",
                             str(target), "-c", "1"], out=out) == 0
            assert target.exists()
            assert probe in target.read_text(encoding="utf-8")

    def test_export_of_several_traces_writes_them_all(self, glm, tmp_path):
        target = tmp_path / "all.json"
        out = io.StringIO()
        assert glm.main(["-q", "describe carbon", "-q", "describe oxygen",
                         "--export-trace", str(target), "-c", "1"],
                        out=out) == 0
        payload = json.loads(target.read_text(encoding="utf-8"))
        assert len(payload) == 2

    def test_a_query_file_is_read(self, glm, tmp_path):
        path = tmp_path / "queries.txt"
        path.write_text("# a comment\ndescribe carbon\n\ndescribe oxygen\n",
                        encoding="utf-8")
        out = io.StringIO()
        assert glm.main(["--query-file", str(path), "-c", "1"], out=out) == 0
        assert out.getvalue().count("QUERY") == 2

    def test_a_missing_query_file_is_a_usage_error(self, glm, tmp_path):
        out = io.StringIO()
        assert glm.main(["--query-file", str(tmp_path / "nope.txt")],
                        out=out) == 2

    def test_the_domain_flag_restricts_resolution(self, glm):
        out = io.StringIO()
        assert glm.main(["-q", "carbon", "-d", "physics"], out=out) == 1
        assert "UNSOLVED" in out.getvalue()

    def test_script_exactness_can_be_asserted_from_the_cli(self, glm):
        out = io.StringIO()
        assert glm.main(["-q", "describe carbon", "-q", "mog grid of oxygen",
                         "--check-script-exactness", "-c", "1"], out=out) == 0
        assert "construct no float" in out.getvalue()

    def test_interactive_reads_queries_from_a_stream(self, glm):
        source = io.StringIO("describe carbon\n:history\n:quit\n")
        out = io.StringIO()
        assert glm.main(["--interactive", "--no-banner", "-c", "1"],
                        out=out, source=source) == 0
        text = out.getvalue()
        assert "QUERY   describe carbon" in text
        assert "[0] ok  describe" in text

    def test_interactive_meta_commands_work(self, glm):
        source = io.StringIO(
            ":help\n:domains\n:basis SI7\n:columns 1\n:verify off\n"
            ":snapshot\n:nosuchcommand\n:quit\n")
        out = io.StringIO()
        assert glm.main(["--interactive", "--no-banner"], out=out,
                        source=source) == 0
        text = out.getvalue()
        assert "Meta-commands" in text
        assert "basis set to SI7" in text
        assert "unknown meta-command" in text
        json.loads(text[text.index("{"):text.index("}\n") + 1])

    def test_interactive_export_writes_the_last_trace(self, glm, tmp_path):
        target = tmp_path / "last.md"
        source = io.StringIO(f"describe carbon\n:export {target}\n:quit\n")
        out = io.StringIO()
        assert glm.main(["--interactive", "--no-banner", "-c", "1"],
                        out=out, source=source) == 0
        assert target.exists()

    def test_interactive_export_before_any_answer_is_refused(self, glm,
                                                             tmp_path):
        source = io.StringIO(f":export {tmp_path / 'x.md'}\n:quit\n")
        out = io.StringIO()
        glm.main(["--interactive", "--no-banner"], out=out, source=source)
        assert "nothing to export yet" in out.getvalue()

    def test_interactive_reports_an_unsolved_query_and_exits_one(self, glm):
        source = io.StringIO("zzzz_nope\n:quit\n")
        out = io.StringIO()
        assert glm.main(["--interactive", "--no-banner"], out=out,
                        source=source) == 1
        assert "UNSOLVED" in out.getvalue()

    def test_interactive_ignores_blank_lines_and_comments(self, glm):
        source = io.StringIO("\n# nothing here\n:quit\n")
        out = io.StringIO()
        assert glm.main(["--interactive", "--no-banner"], out=out,
                        source=source) == 0

    def test_interactive_stops_at_end_of_stream_without_quit(self, glm):
        source = io.StringIO("describe carbon\n")
        out = io.StringIO()
        assert glm.main(["--interactive", "--no-banner", "-c", "1"],
                        out=out, source=source) == 0


class TestCommandLineSubprocess:

    def test_verify_tct_from_the_cli_reports_a_verified_trace(self, glm):
        out = io.StringIO()
        code = glm.main(["-q", "describe carbon", "--verify-tct", "-c", "1"],
                        out=out)
        assert code == 0
        assert "VERIFIED          True" in out.getvalue()


# ===========================================================================
# 5.  PACKAGE-WIDE EXACTNESS AND DETERMINISM
# ===========================================================================

def _runtime_sources():
    return sorted(RUNTIME_DIR.glob("*.py")) + [GLM_PATH]


class TestExactness:

    def test_no_runtime_module_constructs_a_float(self):
        offenders = []
        for path in _runtime_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value,
                                                                 float):
                    offenders.append(f"{path.name}:{node.lineno} float "
                                     f"literal")
                if (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name)
                        and node.func.id == "float"):
                    offenders.append(f"{path.name}:{node.lineno} float() call")
        assert not offenders, offenders

    def test_no_runtime_module_imports_random(self):
        for path in _runtime_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name.split(".")[0] != "random", path.name
                elif isinstance(node, ast.ImportFrom):
                    assert (node.module or "").split(".")[0] != "random", \
                        path.name

    def test_only_the_standard_library_and_glm_universal_are_imported(self):
        allowed = {"argparse", "ast", "dataclasses", "fractions",
                   "functools", "importlib", "io", "itertools", "json",
                   "os", "pathlib", "re", "subprocess", "sys", "tempfile",
                   "typing", "glm_universal", "__future__"}
        for path in _runtime_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name.split(".")[0] for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [(node.module or "").split(".")[0]]
                for name in names:
                    assert name in allowed, f"{path.name} imports {name}"

    def test_no_runtime_module_reads_the_wall_clock(self):
        """A trace must be byte-identical between runs, so no timestamps."""
        for path in _runtime_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name.split(".")[0] not in ("time",
                                                                "datetime"), \
                            path.name

    def test_the_subspaces_the_session_defaults_to_all_exist(self):
        for domain, subspace in SE.DEFAULT_SUBSPACE.items():
            assert domain in SE.DOMAINS
            if subspace is not None:
                assert subspace in an.SUBSPACES

    def test_a_trace_is_byte_identical_across_two_sessions(self):
        texts = []
        for _ in range(2):
            fresh = SE.GeometricSession()
            trace = TE.build_trace(fresh.ask("mog grid of oxygen"))
            texts.append(TE.trace_to_markdown(trace))
        assert texts[0] == texts[1]

    def test_the_public_api_is_importable_from_the_package(self):
        import glm_universal
        assert hasattr(glm_universal, "runtime")
        for name in ("GeometricSession", "build_trace", "verify_trace",
                     "parse_query", "ConceptIndex", "ThreeColumnTrace"):
            assert hasattr(glm_universal.runtime, name)

    def test_the_one_shot_helper_returns_a_trace(self):
        import glm_universal.runtime as rt
        trace = rt.ask("describe carbon")
        assert isinstance(trace, TE.ThreeColumnTrace)
        assert trace.synchronized


class TestRegressionGuards:
    """Properties the earlier steps established, re-checked through the runtime."""

    def test_the_runtime_does_not_disturb_the_reasoning_kernel(self):
        from glm_universal.reasoning import verifier as ve
        report = ve.verifier_report()
        assert report == ve.verifier_report()

    def test_carriers_reached_through_the_session_still_round_trip(self, sess):
        for domain in ("chemistry", "spatial", "mathematics"):
            for obj in sess.register(domain):
                assert obj.round_trip_ok(), f"{domain}:{obj.name}"

    def test_the_session_reports_the_same_dimension_as_the_register(self,
                                                                    sess):
        from glm_universal import data_objects as do
        sol = sess.ask("force = mass * acceleration")
        quantity = do.quantity_by_name("force")
        assert sol.expected["lhs_dimension"] == quantity.dimension_string(
            "EXT10")

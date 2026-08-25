"""Tests for the semantic lexicon wiring in :mod:`glm_universal.runtime`.

As of v0.5.0 the ``lexicon`` register that :class:`GeometricSession` loads is
the meaning-based :class:`SemanticLexiconCodec`'s sample, not the legacy
index-based one.  These tests pin that wiring at the runtime level:

* the register reports the new size (40, not 10),
* every carrier in it has the semantic layout,
* ``describe`` of a lexicon-only concept produces a semantic detail,
* ``describe energy -d lexicon`` resolves to the semantic concept (while
  ``describe energy`` with no hint still resolves to physics, because
  DOMAIN_PRIORITY ranks physics first),
* the carrier-space product over lexicon carriers still produces a 2A
  triple (the substrate-level invariants survive the wiring change).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from glm_universal.data_objects import semantic_lexicon as sl
from glm_universal.runtime import session as SE
from glm_universal.runtime import tct_engine as TE


# Mirror the `glm` fixture from tests/test_runtime.py: import GLM.py by
# path so the same CLI surface the tests assume is available here too.
_RUNTIME_DIR = Path(SE.__file__).resolve().parent
REPO_ROOT = _RUNTIME_DIR.parent.parent
GLM_PATH = REPO_ROOT / "GLM.py"


def _load_glm():
    """Import ``GLM.py`` by path; it is a script at the repo root."""
    spec = importlib.util.spec_from_file_location("glm_entry", GLM_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sess():
    return SE.GeometricSession()


@pytest.fixture(scope="module")
def glm():
    return _load_glm()


# ===========================================================================
# 1.  REGISTER WIRING
# ===========================================================================

class TestLexiconRegisterIsSemantic:

    def test_the_lexicon_register_has_ninety_five_concepts(self, sess):
        register = sess.register("lexicon")
        # v0.5.1 grew the lexicon from 40 → 95 concepts across 10 topics.
        assert len(register) == 95

    def test_every_lexicon_carrier_uses_the_semantic_layout(self, sess):
        register = sess.register("lexicon")
        for obj in register:
            assert obj.layout == sl.SEMANTIC_LAYOUT, obj.name

    def test_every_lexicon_carrier_round_trips(self, sess):
        register = sess.register("lexicon")
        for obj in register:
            assert obj.round_trip_ok(), obj.name

    def test_the_session_holds_the_semantic_codec(self, sess):
        # Loading the lexicon register stores the codec on the session.
        sess.register("lexicon")
        assert isinstance(sess._lexicon_codec, sl.SemanticLexiconCodec)

    def test_the_legacy_lexicon_module_is_still_importable(self):
        """The legacy index-based codec is still available for comparison."""
        from glm_universal.data_objects import lexicon as legacy
        objs, _ = legacy.lexicon_objects()
        assert len(objs) == 10  # the legacy sample size, untouched


# ===========================================================================
# 2.  DESCRIBE RESOLUTION
# ===========================================================================

class TestDescribeResolution:

    def test_describe_gravity_resolves_to_lexicon(self, sess):
        """`gravity` is not in physics; the lexicon concept wins."""
        sol = sess.ask("describe gravity")
        assert sol.ok
        assert sol.expected["domain"] == "lexicon"

    def test_describe_water_resolves_to_molecules_and_says_so(self, sess):
        """`water` is in two registers as of v1.4.0, and the clash is reported.

        Before the molecules register existed, `water` named only a lexical
        concept.  It now also names a molecule, and DOMAIN_PRIORITY ranks a
        register of things ahead of the register of words -- the same rule
        that makes `describe energy` resolve to physics.  What matters is
        that the collision is *stated* in the trace rather than silently
        decided, and that the lexical concept stays reachable.
        """
        sol = sess.ask("describe water")
        assert sol.ok
        assert sol.expected["domain"] == "molecules"
        assert any("ambiguous across" in line and "lexicon" in line
                   for line in sol.query.trace)

    def test_describe_water_with_a_lexicon_hint_resolves_to_lexicon(self, sess):
        """The lexical concept is still reachable behind an explicit hint."""
        sol = sess.ask("describe water", domain="lexicon")
        assert sol.ok
        assert sol.expected["domain"] == "lexicon"
        assert "semantic lexical concept" in sol.steps[0].language

    def test_describe_atom_resolves_to_lexicon(self, sess):
        sol = sess.ask("describe atom")
        assert sol.ok
        assert sol.expected["domain"] == "lexicon"

    def test_describe_electron_resolves_to_lexicon_not_physics(self, sess):
        """Physics has `electron_rest_energy` and `electron_mass`, but not
        bare `electron`.  The lexicon concept wins."""
        sol = sess.ask("describe electron")
        assert sol.ok
        assert sol.expected["domain"] == "lexicon"

    def test_describe_energy_without_a_hint_resolves_to_physics(self, sess):
        """Physics's `energy` quantity wins over the lexicon concept
        because DOMAIN_PRIORITY ranks physics first."""
        sol = sess.ask("describe energy")
        assert sol.ok
        assert sol.expected["domain"] == "physics"

    def test_describe_energy_with_a_lexicon_hint_resolves_to_semantic(self, sess):
        """The semantic concept is reachable with an explicit domain hint."""
        sol = sess.ask("describe energy", domain="lexicon")
        assert sol.ok
        assert sol.expected["domain"] == "lexicon"
        # The semantic concept's carrier is non-integral (its primitives
        # are Fractions in [0, 1], so the denominator is 4 or 8).
        # The detail string mentions "semantic lexical concept".
        identity_step = sol.steps[0]
        assert "semantic lexical concept" in identity_step.language

    def test_describe_of_a_lexicon_concept_mentions_primitives_and_arity(self, sess):
        sol = sess.ask("describe gravity")
        identity_step = sol.steps[0]
        # The detail string should mention "noun" (POS), "arity 4", and
        # "without physical dimensions".
        assert "noun" in identity_step.language
        assert "arity" in identity_step.language
        assert "physical dimensions" in identity_step.language


# ===========================================================================
# 3.  CROSS-COLUMN COHERENCE
# ===========================================================================

class TestTCTCoherence:

    def test_describe_gravity_builds_a_synchronized_trace(self, sess):
        sol = sess.ask("describe gravity")
        trace = TE.build_trace(sol)
        assert trace.synchronized

    def test_describe_gravity_script_is_float_free(self, sess):
        sol = sess.ask("describe gravity")
        trace = TE.build_trace(sol)
        ok, offenders = TE.script_is_exact(trace.script)
        assert ok, offenders

    def test_describe_gravity_script_parses(self, sess):
        import ast
        sol = sess.ask("describe gravity")
        trace = TE.build_trace(sol)
        ast.parse(trace.script)

    def test_describe_gravity_script_runs_and_matches_column_two(self, sess):
        """Column 3 must run in a fresh interpreter and reproduce column 2."""
        sol = sess.ask("describe gravity")
        trace = TE.verify_trace(TE.build_trace(sol), timeout=300)
        assert trace.verdict.executed
        assert trace.verdict.returncode == 0, trace.verdict.stderr_tail
        assert not trace.verdict.mismatches, trace.verdict.mismatches
        assert trace.verified

    def test_describe_water_script_runs_and_matches_column_two(self, sess):
        sol = sess.ask("describe water")
        trace = TE.verify_trace(TE.build_trace(sol), timeout=300)
        assert trace.verified


# ===========================================================================
# 4.  THE CLI SURFACE
# ===========================================================================

class TestCLI:

    def test_list_domains_shows_the_lexicon_size(self, glm):
        import io
        out = io.StringIO()
        assert glm.main(["--list-domains"], out=out) == 0
        text = out.getvalue()
        # v0.5.1 grew the lexicon from 40 → 95 concepts.
        assert "95" in text

    def test_describe_gravity_via_the_cli(self, glm):
        import io
        out = io.StringIO()
        assert glm.main(["-q", "describe gravity", "-c", "1"], out=out) == 0
        text = out.getvalue()
        assert "gravity" in text
        assert "lexicon" in text

    def test_describe_energy_via_the_cli_resolves_to_physics(self, glm):
        import io
        out = io.StringIO()
        assert glm.main(["-q", "describe energy", "-c", "1"], out=out) == 0
        text = out.getvalue()
        assert "physics" in text

    def test_describe_energy_with_d_lexicon_via_the_cli(self, glm):
        import io
        out = io.StringIO()
        assert glm.main(["-q", "describe energy", "-d", "lexicon", "-c", "1"],
                        out=out) == 0
        text = out.getvalue()
        assert "lexicon" in text
        assert "semantic lexical concept" in text

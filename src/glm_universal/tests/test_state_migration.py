"""Tests for the literal migration of the repository's stored GLM state.

Four groups:

1. **Frames** -- the repository engine's Golay code is rebuilt from its own
   parity block and compared with the package's canonical one; the bit
   reversal is checked to be an involution; and the shipped
   ``LEGACY_TO_CORE`` permutation is measured to be *unsafe* for data already
   in the canonical frame, which is the finding the migration turns on.
2. **Carriers and records** -- masks, quadrant weights, roles, exact NRCI,
   the deterministic digest and the minting rule, on values computed here
   rather than quoted.
3. **The whole migration** -- on a small synthetic state whose answers can be
   read off by hand, and then on the real state if this checkout has it,
   including that the written payload contains no float and verifies from its
   carriers alone.
4. **The runtime surface** -- ``report state migration``, ``report concept
   store`` and ``task concepts`` solve, and their column-3 scripts reproduce
   column 2 in a fresh interpreter.
"""

from __future__ import annotations

import ast
import json
from fractions import Fraction
from pathlib import Path

import pytest

from glm_universal.migration import frames as FR
from glm_universal.migration import state as ST
from glm_universal.migration import store as SO
from glm_universal.reasoning import tasks as TK
from glm_universal.runtime import session as SE
from glm_universal.runtime import tct_engine as TE
from glm_universal.substrate import isomorphism as IS
from glm_universal.substrate.mog import GOLAY_MASKS, GOLAY_SET

HAS_SOURCE = ST.state_path() is not None
HAS_CANONICAL = ST.canonical_path().is_file()

needs_source = pytest.mark.skipif(not HAS_SOURCE,
                                  reason="no glm_state.json in this checkout")
needs_canonical = pytest.mark.skipif(
    not HAS_CANONICAL, reason="no glm_state_canonical.json in this checkout")


MIGRATION_DIR = Path(FR.__file__).resolve().parent


class TestPurity:
    """The migration package is exact, deterministic and standard library."""

    def test_no_float_literal_and_no_float_call(self) -> None:
        offenders = []
        for path in sorted(MIGRATION_DIR.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(
                        node.value, float):
                    offenders.append(f"{path.name}:{node.lineno} float")
                if (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name)
                        and node.func.id == "float"):
                    offenders.append(f"{path.name}:{node.lineno} float()")
        assert not offenders, offenders

    def test_only_the_standard_library_is_imported(self) -> None:
        allowed = {"__future__", "fractions", "json", "pathlib", "typing"}
        for path in sorted(MIGRATION_DIR.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert alias.name.split(".")[0] in allowed, \
                            f"{path.name}: {alias.name}"
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    root = (node.module or "").split(".")[0]
                    assert root in allowed, f"{path.name}: {node.module}"


# ===========================================================================
# 1.  FRAMES
# ===========================================================================

class TestFrames:

    def test_the_engine_code_is_a_24_12_8_code(self) -> None:
        code = FR.engine_code()
        assert len(code) == 4096
        weights = sorted({bin(word).count("1") for word in code})
        assert weights == [0, 8, 12, 16, 24]

    def test_the_engine_frame_is_the_canonical_frame(self) -> None:
        audit = FR.frame_audit()
        assert audit["frames_coincide"] is True
        assert audit["shared_codewords"] == 4096
        assert audit["correct_bridge"] == "identity"

    def test_the_generator_rows_are_codewords(self) -> None:
        for row in FR.engine_generator():
            assert row in GOLAY_SET

    def test_legacy_to_core_is_unsafe_for_this_data(self) -> None:
        damage = FR.permutation_damage_report()
        assert damage["is_automorphism"] is False
        assert damage["safe_for_engine_frame_data"] is False
        assert damage["codewords_leaving_the_code"] == 4088
        assert damage["codewords_staying"] == 8

    def test_bit_reversal_is_an_involution(self) -> None:
        assert FR.BIT_REVERSAL == tuple(23 - i for i in range(24))
        for word in (0, 1, 0xFFFFFF, 0x801806, 12345):
            assert FR.reverse_bits(FR.reverse_bits(word)) == word

    def test_reversal_preserves_weight(self) -> None:
        for word in (0, 1, 0x0F0F0F, 0x801806, 0xABCDEF):
            assert (bin(FR.reverse_bits(word)).count("1")
                    == bin(word).count("1"))

    def test_a_word_that_is_not_24_bits_is_refused(self) -> None:
        with pytest.raises(ValueError):
            FR.reverse_bits(1 << 24)
        with pytest.raises(TypeError):
            FR.reverse_bits("0")  # type: ignore[arg-type]

    def test_address_audit_reads_the_convention_off_the_data(self) -> None:
        # A codeword written MSB-first is only a codeword after reversal,
        # unless it happens to be reversal-symmetric; take one that is not.
        codeword = next(word for word in GOLAY_MASKS
                        if FR.reverse_bits(word) not in GOLAY_SET)
        stored = FR.mask_to_address(codeword)
        audit = FR.address_audit([stored])
        assert audit["codewords_read_msb_first"] == 1
        assert audit["codewords_read_lsb_first"] == 0
        assert audit["bit_reversal_required"] is True

    @needs_source
    def test_every_stored_address_is_a_codeword_after_reversal(self) -> None:
        addresses = [value for _task, value in ST.load_addresses()]
        assert addresses
        audit = FR.address_audit(addresses)
        assert audit["all_codewords_after_reversal"] is True
        assert audit["codewords_read_lsb_first"] == 0


# ===========================================================================
# 2.  CARRIERS AND RECORDS
# ===========================================================================

class TestCarriers:

    def test_mask_and_vector_round_trip(self) -> None:
        vector = [1, 0, 1, 1] + [0] * 20
        mask = ST.mask_of_vector(vector)
        assert mask == 0b1101
        assert list(ST.vector_of_mask(mask)) == vector

    def test_a_short_vector_is_refused(self) -> None:
        with pytest.raises(ValueError):
            ST.mask_of_vector([1, 0, 1])

    def test_quadrant_weights_are_the_four_sextet_sums(self) -> None:
        mask = ST.mask_of_vector([1] * 6 + [0] * 6 + [1, 1] + [0] * 10)
        assert ST.quadrant_weights(mask) == (6, 0, 2, 0)

    def test_role_follows_the_dominant_quadrant(self) -> None:
        assert ST.role_of(ST.mask_of_vector([1] * 6 + [0] * 18)) == "NOUN"
        assert ST.role_of(
            ST.mask_of_vector([0] * 6 + [1] * 6 + [0] * 12)) == "ADJECTIVE"
        assert ST.role_of(
            ST.mask_of_vector([0] * 12 + [1] * 6 + [0] * 6)) == "VERB"
        assert ST.role_of(
            ST.mask_of_vector([0] * 18 + [1] * 6)) == "OPERATOR"

    def test_nrci_is_exact_and_decreasing_in_weight(self) -> None:
        assert ST.exact_nrci(0) == 1
        values = [ST.exact_nrci(w) for w in range(25)]
        assert all(isinstance(v, Fraction) for v in values)
        assert all(a > b for a, b in zip(values, values[1:]))

    def test_nrci_matches_the_formula(self) -> None:
        from glm_universal.reasoning.coherence import Y
        assert ST.exact_nrci(8) == Fraction(10) / (10 + 8 * Y + Fraction(1))

    def test_the_two_rationals_for_y_disagree_below_1e15(self) -> None:
        assert ST.y_disagreement() > 0
        assert ST.y_disagreement() < Fraction(1, 10 ** 15)

    def test_the_digest_is_deterministic_and_not_pythons_hash(self) -> None:
        assert ST.fnv1a64("entropy") == ST.fnv1a64("entropy")
        assert ST.fnv1a64("") == 0xCBF29CE484222325
        assert ST.fnv1a64("a") != ST.fnv1a64("b")

    def test_minting_gives_a_codeword_and_avoids_collisions(self) -> None:
        first = ST.minted_mask("entropy")
        assert first in GOLAY_SET
        assert ST.minted_mask("entropy") == first
        second = ST.minted_mask("entropy", taken=[first])
        assert second != first and second in GOLAY_SET

    def test_a_migrated_concept_recomputes_its_own_fields(self) -> None:
        vector = [1, 1, 0, 1] + [0] * 20
        record = {"vector": vector, "role": "NOUN", "lingo_term": "X",
                  "quadrant_weights": [3, 0, 0, 0], "nrci": 0.5}
        out = ST.migrate_concept("x", record)
        assert out["mask"] == ST.mask_of_vector(vector)
        assert out["weight"] == 3
        assert out["quadrant_weights"] == [3, 0, 0, 0]
        assert out["role"] == "NOUN"
        assert out["provenance"] == "imported"
        assert Fraction(*out["nrci"]) == ST.exact_nrci(3)
        assert Fraction(*out["nrci_stored"]) == Fraction(0.5)
        assert out["decode"]["status"] in ("codeword", "corrected",
                                           "ambiguous")


# ===========================================================================
# 3.  THE WHOLE MIGRATION
# ===========================================================================

def _tiny_state() -> dict:
    """Two concepts, three edges: one good, one dangling, one nameless."""
    return {
        "concepts": {
            "alpha": {"vector": [1] * 8 + [0] * 16, "role": "NOUN",
                      "lingo_term": "A", "quadrant_weights": [6, 2, 0, 0],
                      "nrci": 0.5},
            "beta": {"vector": [0] * 16 + [1] * 8, "role": "OPERATOR",
                     "lingo_term": "B", "quadrant_weights": [0, 0, 2, 6],
                     "nrci": 0.5},
        },
        "crg_edges": [
            {"src": "alpha", "label": "relates", "dst": "beta"},
            {"src": "alpha", "label": "relates", "dst": "gamma"},
            {"src": "alpha", "label": "relates", "dst": None},
        ],
        "run_history": [{"run_number": 1}],
        "last_updated": "2026-08-22T00:00:00",
    }


class TestMigrateState:

    def test_minting_repairs_referential_integrity(self) -> None:
        out = ST.migrate_state(_tiny_state(), mint_missing=True)
        checks = out["checks"]
        assert checks["concepts_imported"] == 2
        assert checks["concepts_minted"] == 1
        assert checks["edges_migrated"] == 2
        assert checks["edges_dropped"] == 1
        assert checks["referentially_intact"] is True
        minted = [c for c in out["concepts"] if c["provenance"] == "minted"]
        assert [c["name"] for c in minted] == ["gamma"]

    def test_without_minting_the_dangling_edge_is_dropped(self) -> None:
        out = ST.migrate_state(_tiny_state(), mint_missing=False)
        checks = out["checks"]
        assert checks["concepts_minted"] == 0
        assert checks["edges_migrated"] == 1
        assert checks["edges_dropped"] == 2
        assert checks["referentially_intact"] is True

    def test_addresses_migrate_by_reversal(self) -> None:
        codeword = next(word for word in GOLAY_MASKS
                        if FR.reverse_bits(word) not in GOLAY_SET)
        stored = FR.mask_to_address(codeword)
        out = ST.migrate_state(_tiny_state(), addresses=(("t", stored),))
        colour = out["hexcolours"][0]
        assert colour["mask"] == codeword
        assert colour["is_codeword"] is True
        assert out["checks"]["addresses_that_are_codewords"] == 1

    def test_faces_report_their_unresolved_vertices(self) -> None:
        out = ST.migrate_state(_tiny_state(), faces=(("alpha", "beta"),
                                                     ("alpha", "delta")),
                               mint_missing=False)
        assert out["faces"][0]["resolved"] is True
        assert out["faces"][1]["unresolved"] == ["delta"]
        assert out["checks"]["faces_resolved"] == 1

    def test_the_payload_holds_no_float(self) -> None:
        out = ST.migrate_state(_tiny_state())
        assert "e+" not in json.dumps(out)
        for concept in out["concepts"]:
            for value in concept.values():
                assert not isinstance(value, float)

    def test_a_migrated_payload_verifies_from_its_carriers(self) -> None:
        out = ST.migrate_state(_tiny_state())
        verification = ST.verify_canonical(out)
        assert verification["fields_recomputed_and_agreeing"] is True
        assert verification["referentially_intact"] is True
        assert verification["floats_in_payload"] == 0


@needs_source
class TestTheRealState:

    def test_the_source_migrates_with_the_expected_shape(self) -> None:
        payload = ST.canonical_payload()
        checks = payload["checks"]
        assert checks["concepts_imported"] == 4282
        assert checks["edges_migrated"] + checks["edges_dropped"] == 4015
        assert checks["masks_distinct"] is True
        assert checks["referentially_intact"] is True
        assert checks["roles_agree"] == checks["concepts_total"]
        assert (checks["quadrant_weights_agree"]
                == checks["concepts_total"])

    def test_most_carriers_are_not_codewords(self) -> None:
        payload = ST.canonical_payload()
        checks = payload["checks"]
        assert checks["carriers_that_are_codewords"] < checks[
            "concepts_total"] // 2
        assert checks["decode_ambiguous"] > 0
        assert (checks["decode_codeword"] + checks["decode_corrected"]
                + checks["decode_ambiguous"] == checks["concepts_total"])

    def test_nrci_agrees_with_the_stored_float_to_within_a_millionth(
            self) -> None:
        payload = ST.canonical_payload()
        worst = Fraction(*payload["checks"]["worst_nrci_gap"])
        assert 0 < worst < Fraction(1, 10 ** 6)

    def test_migration_is_deterministic(self) -> None:
        assert (ST.canonical_payload()["checks"]
                == ST.canonical_payload()["checks"])


@needs_canonical
class TestTheWrittenFile:

    def test_it_verifies_from_its_carriers_alone(self) -> None:
        payload = ST.load_canonical()
        verification = ST.verify_canonical(payload)
        assert verification["format"] == ST.FORMAT
        assert verification["fields_recomputed_and_agreeing"] is True
        assert verification["masks_distinct"] is True
        assert verification["referentially_intact"] is True
        assert verification["addresses_round_trip"] is True
        assert verification["floats_in_payload"] == 0

    @needs_source
    def test_the_source_still_reproduces_it(self) -> None:
        report = ST.state_migration_report()
        assert report["available"] is True
        assert report["source_reproduces_the_file"] is True


# ===========================================================================
# 3b.  THE HEXCOLOUR ADDRESSES
# ===========================================================================

class TestHexcolourConverters:
    """The address layer on its own, before any stored data is involved."""

    def test_a_hexcolour_round_trips_every_mask_it_can_name(self) -> None:
        for mask in (0, 1, 0xABCDEF, 0xFFFFFF, 0x800001):
            colour = IS.mask_to_hexcolour(mask)
            assert colour.startswith("#") and len(colour) == 7
            assert IS.hexcolour_to_mask(colour) == mask

    def test_the_hash_is_optional_and_case_is_not_significant(self) -> None:
        assert IS.hexcolour_to_mask("#AbCdEf") == IS.hexcolour_to_mask(
            "abcdef") == 0xABCDEF

    def test_a_malformed_address_raises(self) -> None:
        for bad in ("#abcde", "abcdefg", "zzzzzz", ""):
            with pytest.raises(ValueError):
                IS.hexcolour_to_mask(bad)
        with pytest.raises(TypeError):
            IS.hexcolour_to_mask(0xABCDEF)  # type: ignore[arg-type]

    def test_migrating_an_address_permutes_the_coordinates_it_names(
            self) -> None:
        for mask in (0, 1, 0xABCDEF, 0xFFFFFF):
            colour = IS.mask_to_hexcolour(mask)
            assert (IS.hexcolour_to_mask(IS.migrate_hexcolour(colour))
                    == IS.to_core_mask(mask))

    def test_migration_preserves_weight(self) -> None:
        for mask in (1, 0xABCDEF, 0x0F0F0F, 0xFFFFFF):
            moved = IS.hexcolour_to_mask(
                IS.migrate_hexcolour(IS.mask_to_hexcolour(mask)))
            assert bin(moved).count("1") == bin(mask).count("1")


@needs_canonical
class TestHexcolourAudit:
    """And the same questions asked of the shipped data.

    ``Endianness.lean`` is the machine-checked half: bit reversal is a
    coordinate permutation, hence an isometry, so the MSB-first reading the
    stored addresses turn out to need costs no guarantee.
    """

    def test_the_audit_is_available_and_faithful(self) -> None:
        audit = ST.hexcolour_audit()
        assert audit["available"] is True
        assert audit["faithful"] is True

    def test_every_concept_has_its_own_address(self) -> None:
        audit = ST.hexcolour_audit()
        assert audit["concepts"] > 4000
        assert audit["distinct"] == audit["concepts"]
        assert audit["collisions"] == 0

    def test_nothing_fails_to_read_back(self) -> None:
        audit = ST.hexcolour_audit()
        assert audit["round_trip_failures"] == 0
        assert audit["recomputed_disagreements"] == 0
        assert audit["migration_mismatches"] == 0

    def test_the_legacy_per_task_table_is_all_codewords(self) -> None:
        audit = ST.hexcolour_audit()
        assert audit["legacy_addresses"] > 0
        assert audit["legacy_codewords"] == audit["legacy_addresses"]
        assert audit["legacy_distinct"] == audit["legacy_addresses"]
        assert audit["legacy_round_trip_failures"] == 0

    def test_the_audit_is_recomputed_from_the_payload_it_is_given(
            self) -> None:
        payload = ST.load_canonical()
        assert ST.hexcolour_audit(payload) == ST.hexcolour_audit()

    def test_a_corrupted_address_is_caught(self) -> None:
        payload = ST.load_canonical()
        broken = dict(payload)
        concepts = [dict(c) for c in payload["concepts"]]
        concepts[0]["hexcolour"] = IS.mask_to_hexcolour(
            concepts[0]["mask"] ^ 1)
        broken["concepts"] = concepts
        audit = ST.hexcolour_audit(broken)
        assert audit["round_trip_failures"] == 1
        assert audit["recomputed_disagreements"] == 1
        assert audit["faithful"] is False

    def test_the_report_carries_the_audit(self) -> None:
        report = ST.state_migration_report()
        assert report["hexcolours"] == ST.hexcolour_audit()


@needs_canonical
class TestHexcolourLookup:
    """An address is a key: the store is reachable through it."""

    def test_a_concept_is_recovered_from_its_address_alone(self) -> None:
        store = SO.ConceptStore.load()
        for name in ("energy", "entropy", "grid", "colour"):
            assert store.by_hexcolour(store.hexcolour(name)) == name

    def test_every_concept_round_trips_through_its_address(self) -> None:
        store = SO.ConceptStore.load()
        assert store.addresses_are_distinct() is True
        for name in store.names:
            assert store.by_hexcolour(store.hexcolour(name)) == name

    def test_the_hash_and_the_case_are_not_significant(self) -> None:
        store = SO.ConceptStore.load()
        colour = store.hexcolour("energy")
        assert store.by_hexcolour(colour.lstrip("#").upper()) == "energy"

    def test_an_address_no_concept_carries_raises(self) -> None:
        store = SO.ConceptStore.load()
        used = {store.hexcolour(name) for name in store.names}
        free = next(c for c in (IS.mask_to_hexcolour(m)
                                for m in range(0x1000000))
                    if c not in used)
        with pytest.raises(KeyError):
            store.by_hexcolour(free)

    def test_the_address_agrees_with_the_carrier(self) -> None:
        store = SO.ConceptStore.load()
        for name in store.names:
            assert (IS.hexcolour_to_mask(store.hexcolour(name))
                    == int(store.concept(name)["mask"]))


# ===========================================================================
# 4.  THE STORE AND THE RUNTIME SURFACE
# ===========================================================================

@needs_canonical
class TestStore:

    def test_the_store_loads_and_indexes(self) -> None:
        store = SO.ConceptStore.load()
        assert store is not None
        assert len(store) > 4000
        assert store.has("energy") and store.has("entropy")

    def test_a_path_is_a_chain_of_real_edges(self) -> None:
        store = SO.ConceptStore.load()
        path = store.path("entropy", "energy")
        assert path
        assert path[0][0] == "entropy" and path[-1][2] == "energy"
        for left, _label, right in path:
            assert store.has(left) and store.has(right)

    def test_excluding_proposals_can_change_the_path(self) -> None:
        store = SO.ConceptStore.load()
        every = store.path("grid", "colour")
        asserted = store.path("grid", "colour",
                              exclude_labels=("auto_proposed",))
        assert every is not None and asserted is not None
        assert all(step[1] != "auto_proposed" for step in asserted)
        assert any(step[1] == "auto_proposed" for step in every)

    def test_a_path_to_itself_is_empty(self) -> None:
        store = SO.ConceptStore.load()
        assert store.path("energy", "energy") == ()

    def test_an_unknown_name_raises(self) -> None:
        store = SO.ConceptStore.load()
        with pytest.raises(KeyError):
            store.concept("not-a-concept-in-this-store")

    def test_hamming_neighbours_are_sorted_by_distance(self) -> None:
        store = SO.ConceptStore.load()
        neighbours = store.hamming_neighbours("energy", 5)
        distances = [d for _name, d in neighbours]
        assert distances == sorted(distances)

    def test_the_store_report_counts_proposals_separately(self) -> None:
        report = SO.store_report()
        assert report["available"] is True
        assert (report["asserted_edges"] + report["auto_proposed_edges"]
                == report["edges"])
        assert report["minted_concepts"] > 0


@needs_canonical
class TestRuntimeSurface:

    def test_the_new_subjects_are_advertised(self) -> None:
        assert "state migration" in SE.REPORT_SUBJECTS
        assert "concept store" in SE.REPORT_SUBJECTS
        assert "concepts" in SE.TASKS

    def test_report_state_migration_solves(self) -> None:
        session = SE.GeometricSession()
        solution = session.ask("report state migration")
        assert solution.ok
        assert solution.expected["frames_coincide"] == "True"
        assert solution.expected["bit_reversal_required"] == "True"
        assert solution.expected["referentially_intact"] == "True"
        assert solution.expected["floats_in_payload"] == "0"

    def test_report_concept_store_solves(self) -> None:
        session = SE.GeometricSession()
        solution = session.ask("report concept store")
        assert solution.ok
        assert int(solution.expected["edges"]) > 4000

    def test_task_concepts_is_discriminating(self) -> None:
        session = SE.GeometricSession()
        solution = session.ask("task concepts")
        assert solution.ok
        assert solution.expected["law_holds"] == "True"
        assert solution.expected["control_fails"] == "True"
        assert solution.expected["discriminating"] == "True"

    def test_the_generated_scripts_are_float_free(self) -> None:
        session = SE.GeometricSession()
        for query in ("report state migration", "report concept store",
                      "task concepts"):
            script = TE.render_script(session.ask(query))
            ok, offenders = TE.script_is_exact(script)
            assert ok, (query, offenders)

    def test_the_scripts_reproduce_column_two(self) -> None:
        session = SE.GeometricSession()
        for query in ("report state migration", "report concept store",
                      "task concepts"):
            trace = TE.verify_trace(TE.build_trace(session.ask(query)),
                                    timeout=900)
            assert trace.verdict.executed, (query,
                                            trace.verdict.stderr_tail)
            assert trace.verdict.verified, (query,
                                            trace.verdict.mismatches)

    def test_the_concept_task_agrees_with_the_module(self) -> None:
        result = TK.concept_task()
        session = SE.GeometricSession()
        solution = session.ask("task concepts")
        assert solution.expected["asserted_steps"] == str(
            len(result["asserted_path"]))

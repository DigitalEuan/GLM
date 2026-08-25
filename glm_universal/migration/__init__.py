"""``glm_universal.migration`` -- bringing the repository's stored data in.

Three modules:

* :mod:`~glm_universal.migration.frames` settles, by computation, which Golay
  frame and which bit order the repository's persisted data is written in.
  The findings: concept vectors are already in the package's canonical frame
  (so the bridge is the identity, and the shipped ``LEGACY_TO_CORE``
  permutation must *not* be applied to them), while stored integer addresses
  are MSB-first and need the bit reversal.
* :mod:`~glm_universal.migration.state` performs the migration of the
  persistent GLM state -- concepts, CRG edges, hexcolour addresses and
  simplicial faces -- into exact, audited, referentially intact canonical
  form, and verifies the result from the carriers alone.
* :mod:`~glm_universal.migration.store` is the consumer: it indexes the
  canonical payload and answers questions of it -- labelled paths through the
  concept-relation graph, Hamming neighbourhoods in the substrate, and the
  cross-links where a CRG concept is also a register carrier.

Reachable from the runtime as ``report state migration``, ``report concept
store`` and ``task concepts``.
"""

from __future__ import annotations

from .frames import (BIT_REVERSAL, ENGINE_B, address_audit, address_to_mask,
                     engine_code, engine_generator, frame_audit, frame_report,
                     mask_to_address, permutation_damage_report, reverse_bits)
from .state import (FORMAT, GRAMMAR_ROLE, QUADRANT_RANGES, Y_PIPELINE,
                    canonical_path, canonical_payload, decode_record,
                    exact_nrci, fnv1a64, hexcolour_of_mask, load_addresses,
                    load_canonical, load_faces, load_state, mask_of_vector,
                    migrate_concept, migrate_state, mint_concept,
                    minted_mask, quadrant_weights, repository_root, role_of,
                    state_migration_report, state_path, vector_of_mask,
                    verify_canonical, write_canonical, y_disagreement)
from .store import ConceptStore, store_report

__all__ = [
    # frames
    "BIT_REVERSAL", "ENGINE_B", "address_audit", "address_to_mask",
    "engine_code", "engine_generator", "frame_audit", "frame_report",
    "mask_to_address", "permutation_damage_report", "reverse_bits",
    # state
    "FORMAT", "GRAMMAR_ROLE", "QUADRANT_RANGES", "Y_PIPELINE",
    "canonical_path", "canonical_payload", "decode_record", "exact_nrci",
    "fnv1a64", "hexcolour_of_mask", "load_addresses", "load_canonical",
    "load_faces", "load_state", "mask_of_vector", "migrate_concept",
    "migrate_state", "mint_concept", "minted_mask", "quadrant_weights",
    "repository_root", "role_of", "state_migration_report", "state_path",
    "vector_of_mask", "verify_canonical", "write_canonical",
    "y_disagreement",
    # store
    "ConceptStore", "store_report",
]

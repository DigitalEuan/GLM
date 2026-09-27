"""``glm_universal.migration.state`` -- the literal migration of the GLM state.

What this migrates
------------------
The persistent state the ARC pipelines have been growing for 217 runs:

* ``arc_agi_17/results/glm_state.json`` -- **4,282 concepts** (each a name, a
  24-bit vector, a grammatical role, a Lingo term, four quadrant weights and
  an NRCI) and **4,015 CRG edges** (``src``, ``label``, ``dst``);
* ``arc_agi_17/results/hexcolour_addresses.json`` -- the persistent lattice
  addresses of solved tasks, stored as integers;
* ``arc_agi_17/results/simplicial_faces.json`` -- the 3-element faces over
  concept names.

and rewrites them in the canonical form this package can actually reason
with: exact rationals, package coordinate order, and an audited decoding
attached to every carrier.

What the migration is, exactly
------------------------------
It is **not** a coordinate permutation.
:mod:`glm_universal.migration.frames` establishes by computation that the
frame the repository's ``GolayCodeEngine`` writes in *is* this package's
canonical frame, so the bridge for concept vectors is the identity, and the
one real coordinate correction is the **bit reversal** for stored integer
addresses, which the addresses themselves confirm.  Applying the shipped
``LEGACY_TO_CORE`` permutation to this data would corrupt it, and
:func:`~glm_universal.migration.frames.permutation_damage_report` says by how
much.

The substantive work is therefore making the information *usable* and saying
exactly where it is *not* accurate:

* **Every carrier gets an audited decoding.**  A concept vector is a received
  word, not a codeword: only 65 of the 4,282 are codewords.  Each one is
  decoded by the complete decoder, and carries its status --
  ``unique`` with the codeword and the distance, or ``ambiguous`` with the
  number of equally near codewords and no answer at all.  Nothing is snapped
  silently.
* **NRCI becomes exact.**  The stored value is a float from
  ``10/(10 + w*Y + w/8)``.  Here it is a :class:`~fractions.Fraction`
  computed from the package's exact ``Y``, the stored float is kept beside it
  as the exact rational that float really is, and the gap between them is
  measured rather than rounded away.  Nothing in the output is a float.
* **Referential integrity is repaired, visibly.**  1,993 of the 4,015 edges
  name an endpoint that has no concept record -- 399 distinct names the CRG
  expansion introduced and never gave a carrier.  With
  ``mint_missing=True`` (the default) each is given a deterministic carrier
  of its own, marked ``provenance="minted"`` so it can never be mistaken for
  imported data; with ``mint_missing=False`` those edges are dropped and
  counted.  Either way the result has no dangling edge.
* **Roles and quadrant weights are recomputed** from the vector rather than
  copied, so the output cannot disagree with itself.

Reproducing it
--------------
``migrate_state(load_state())`` returns the whole payload;
:func:`write_canonical` writes it to
``arc_agi_17/results/glm_state_canonical.json``; :func:`verify_canonical`
re-derives every field of a written payload from the masks alone and reports
what it found, so the shipped file can be checked without the source; and
:func:`state_migration_report` is the summary the runtime serves as
``report state migration``.

Exactness: no float is constructed here, and none is written.  Determinism:
no randomness, no hashing library, no dependence on dictionary order for any
reported number.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from ..reasoning.coherence import Y
from ..substrate.golay_decode import decode_complete
from ..substrate.mog import GOLAY_MASKS, GOLAY_SET
from .frames import (BIT_REVERSAL, DIM, address_audit, address_to_mask,
                     frame_audit, mask_to_address, permutation_damage_report)

__all__ = [
    "FORMAT", "QUADRANT_RANGES", "GRAMMAR_ROLE", "Y_PIPELINE",
    "repository_root", "state_path", "addresses_path", "faces_path",
    "canonical_path", "load_state", "load_addresses", "load_faces",
    "mask_of_vector", "vector_of_mask", "quadrant_weights", "role_of",
    "exact_nrci", "hexcolour_of_mask", "fnv1a64", "minted_mask",
    "decode_record", "migrate_concept", "mint_concept", "migrate_state",
    "canonical_payload", "write_canonical", "load_canonical",
    "verify_canonical", "hexcolour_audit", "state_migration_report",
]

#: The format tag written into every canonical payload.
FORMAT = "glm_universal.migration/1"

#: The four quadrants of a 24-coordinate vector, as the pipelines slice them.
QUADRANT_RANGES: Tuple[Tuple[int, int], ...] = ((0, 6), (6, 12),
                                                (12, 18), (18, 24))

#: Dominant quadrant -> grammatical role, as the pipelines assign it.
GRAMMAR_ROLE: Tuple[str, ...] = ("NOUN", "ADJECTIVE", "VERB", "OPERATOR")

#: The rational the pipelines used for the read quantum, transcribed from
#: ``Y_CONST = 0.2646754304045269672`` in ``arc_v17_2_pipeline.py``.  The
#: package's own :data:`~glm_universal.reasoning.coherence.Y` is a different
#: rational approximation of the same irrational 1/(pi + 2/pi); the two
#: differ, exactly, by :func:`y_disagreement`.
Y_PIPELINE = Fraction(2646754304045269672, 10 ** 19)


def y_disagreement() -> Fraction:
    """How far the pipeline's Y is from the package's Y, exactly."""
    return abs(Y - Y_PIPELINE)


# ===========================================================================
# 1.  WHERE THE DATA IS
# ===========================================================================

def repository_root() -> Path:
    """The directory the package sits in -- the repository root.

    ``glm_universal/migration/state.py`` -> ``glm_universal`` -> root.
    """
    return Path(__file__).resolve().parent.parent.parent


def _find(relative: str) -> Optional[Path]:
    candidates = [repository_root() / relative, Path.cwd() / relative]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def state_path() -> Optional[Path]:
    """The persistent GLM state, if this checkout has it."""
    return _find("arc_agi_17/results/glm_state.json")


def addresses_path() -> Optional[Path]:
    """The persistent hexcolour addresses, if this checkout has them."""
    return _find("arc_agi_17/results/hexcolour_addresses.json")


def faces_path() -> Optional[Path]:
    """The simplicial faces, if this checkout has them."""
    return _find("arc_agi_17/results/simplicial_faces.json")


def canonical_path() -> Path:
    """Where the migrated state is written."""
    return repository_root() / "arc_agi_17/results/glm_state_canonical.json"


def _read_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_state(path: Optional[Path] = None) -> Optional[Dict[str, object]]:
    """The raw state as written by the pipelines, or ``None`` if absent."""
    target = path or state_path()
    if target is None:
        return None
    payload = _read_json(Path(target))
    if not isinstance(payload, dict):
        raise ValueError(f"load_state: {target} is not an object")
    return payload


def load_addresses(path: Optional[Path] = None) -> Tuple[Tuple[str, int], ...]:
    """The stored ``(task, address)`` pairs, sorted by task."""
    target = path or addresses_path()
    if target is None:
        return ()
    payload = _read_json(Path(target))
    if not isinstance(payload, dict):
        raise ValueError(f"load_addresses: {target} is not an object")
    addresses = payload.get("addresses", {})
    if not isinstance(addresses, dict):
        raise ValueError(f"load_addresses: {target} has no address table")
    return tuple(sorted((str(task), int(value))
                        for task, value in addresses.items()))


def load_faces(path: Optional[Path] = None) -> Tuple[Tuple[str, ...], ...]:
    """The stored simplicial faces, each a tuple of concept names."""
    target = path or faces_path()
    if target is None:
        return ()
    payload = _read_json(Path(target))
    if not isinstance(payload, dict):
        raise ValueError(f"load_faces: {target} is not an object")
    faces = payload.get("faces", [])
    return tuple(tuple(str(name) for name in face) for face in faces)


# ===========================================================================
# 2.  CARRIERS
# ===========================================================================

def mask_of_vector(vector: Sequence[int]) -> int:
    """A 24-entry 0/1 list as a coordinate mask, bit *i* = coordinate *i*."""
    if len(vector) != DIM:
        raise ValueError(f"mask_of_vector: expected {DIM} bits, "
                         f"got {len(vector)}")
    mask = 0
    for index, bit in enumerate(vector):
        if bit not in (0, 1):
            raise ValueError(f"mask_of_vector: {bit!r} is not a bit")
        if bit:
            mask |= 1 << index
    return mask


def vector_of_mask(mask: int) -> Tuple[int, ...]:
    """The inverse of :func:`mask_of_vector`."""
    return tuple((mask >> i) & 1 for i in range(DIM))


def quadrant_weights(mask: int) -> Tuple[int, ...]:
    """The four quadrant weights of a carrier, recomputed from its mask."""
    bits = vector_of_mask(mask)
    return tuple(sum(bits[start:end]) for start, end in QUADRANT_RANGES)


def role_of(mask: int) -> str:
    """The grammatical role the pipelines derive from a carrier's geometry."""
    weights = quadrant_weights(mask)
    return GRAMMAR_ROLE[weights.index(max(weights))]


def exact_nrci(weight: int, y: Fraction = Y) -> Fraction:
    """``10 / (10 + w*Y + w/8)`` as an exact rational.

    This is the pipelines' NRCI: ten over ten plus the symmetry tax of a
    weight-``w`` binary carrier, ``TAX = w*Y + ||v||^2/8`` with
    ``||v||^2 = w``.
    """
    if not isinstance(weight, int) or isinstance(weight, bool):
        raise TypeError("exact_nrci: weight must be an int")
    if not 0 <= weight <= DIM:
        raise ValueError(f"exact_nrci: weight {weight} out of range")
    return Fraction(10) / (10 + weight * y + Fraction(weight, 8))


def hexcolour_of_mask(mask: int) -> str:
    """The six-hex-digit address of a mask, in package coordinate order."""
    return "#" + format(mask, "06x")


def fnv1a64(text: str) -> int:
    """A 64-bit FNV-1a digest of ``text``.

    Deterministic across interpreters and runs, which Python's built-in
    ``hash`` is not -- the pipelines used ``hash(word) & 0xFFF`` to seed a
    carrier, so their Lingo carriers cannot be reproduced from the source.
    Minted carriers here can.
    """
    digest = 0xCBF29CE484222325
    for byte in text.encode("utf-8"):
        digest ^= byte
        digest = (digest * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return digest


def minted_mask(name: str, taken: Sequence[int] = ()) -> int:
    """A deterministic Golay codeword for a name that has no carrier.

    The digest picks a codeword out of the 4,096; if that one is already in
    use the next index is tried, in order, so the choice is a function of the
    name and the set of carriers already present and of nothing else.
    """
    used = set(taken)
    start = fnv1a64(name) % len(GOLAY_MASKS)
    for offset in range(len(GOLAY_MASKS)):
        candidate = GOLAY_MASKS[(start + offset) % len(GOLAY_MASKS)]
        if candidate not in used:
            return candidate
    raise ValueError("minted_mask: every codeword is taken")


def decode_record(mask: int) -> Dict[str, object]:
    """The audited decoding of a carrier, with its honesty flags."""
    decoding = decode_complete(mask)
    return {
        "status": decoding.status,
        "distance": decoding.weight,
        "nearest": decoding.corrected,
        "candidates": len(decoding.candidates),
        "guaranteed": decoding.guaranteed,
        "is_codeword": mask in GOLAY_SET,
    }


# ===========================================================================
# 3.  MIGRATING A RECORD
# ===========================================================================

def _fraction_pair(value: Fraction) -> List[int]:
    return [value.numerator, value.denominator]


def migrate_concept(name: str, record: Mapping[str, object]
                    ) -> Dict[str, object]:
    """One stored concept in canonical form."""
    vector = record.get("vector")
    if not isinstance(vector, list):
        raise ValueError(f"migrate_concept: {name!r} has no vector")
    mask = mask_of_vector(vector)
    weight = bin(mask).count("1")
    weights = quadrant_weights(mask)
    exact = exact_nrci(weight)
    stored = record.get("nrci")
    stored_exact = Fraction(stored) if stored is not None else None
    out: Dict[str, object] = {
        "name": name,
        "mask": mask,
        "weight": weight,
        "quadrant_weights": list(weights),
        "role": role_of(mask),
        "role_stored": record.get("role"),
        "lingo_term": record.get("lingo_term"),
        "hexcolour": hexcolour_of_mask(mask),
        "address": mask_to_address(mask),
        "nrci": _fraction_pair(exact),
        "nrci_stored": (_fraction_pair(stored_exact)
                        if stored_exact is not None else None),
        "nrci_gap": (_fraction_pair(abs(exact - stored_exact))
                     if stored_exact is not None else None),
        "quadrant_weights_stored_agree":
            list(record.get("quadrant_weights", [])) == list(weights),
        "decode": decode_record(mask),
        "provenance": "imported",
    }
    return out


def mint_concept(name: str, taken: Sequence[int]) -> Dict[str, object]:
    """A carrier for an edge endpoint that the state never gave one."""
    mask = minted_mask(name, taken)
    weight = bin(mask).count("1")
    return {
        "name": name,
        "mask": mask,
        "weight": weight,
        "quadrant_weights": list(quadrant_weights(mask)),
        "role": role_of(mask),
        "role_stored": None,
        "lingo_term": None,
        "hexcolour": hexcolour_of_mask(mask),
        "address": mask_to_address(mask),
        "nrci": _fraction_pair(exact_nrci(weight)),
        "nrci_stored": None,
        "nrci_gap": None,
        "quadrant_weights_stored_agree": True,
        "decode": decode_record(mask),
        "provenance": "minted",
    }


# ===========================================================================
# 4.  MIGRATING THE WHOLE STATE
# ===========================================================================

def migrate_state(state: Mapping[str, object],
                  addresses: Sequence[Tuple[str, int]] = (),
                  faces: Sequence[Sequence[str]] = (),
                  mint_missing: bool = True) -> Dict[str, object]:
    """Migrate concepts, edges, addresses and faces in one call.

    Returns the canonical payload: the migrated tables, the frame audit that
    justifies the coordinate reading, and the checks that decide whether the
    result is usable.
    """
    raw_concepts = state.get("concepts", {})
    if not isinstance(raw_concepts, dict):
        raise ValueError("migrate_state: 'concepts' is not an object")
    raw_edges = state.get("crg_edges", [])
    if not isinstance(raw_edges, list):
        raise ValueError("migrate_state: 'crg_edges' is not a list")

    concepts: List[Dict[str, object]] = []
    by_name: Dict[str, Dict[str, object]] = {}
    for name in raw_concepts:
        record = raw_concepts[name]
        if not isinstance(record, dict):
            raise ValueError(f"migrate_state: concept {name!r} is not an "
                             f"object")
        migrated = migrate_concept(str(name), record)
        concepts.append(migrated)
        by_name[str(name)] = migrated
    imported_count = len(concepts)

    # Edge endpoints with no concept record.
    unresolved: List[str] = []
    nameless = 0
    for edge in raw_edges:
        for end in ("src", "dst"):
            value = edge.get(end)
            if value is None:
                nameless += 1
                continue
            if str(value) not in by_name:
                unresolved.append(str(value))
    missing = sorted(set(unresolved))

    minted: List[Dict[str, object]] = []
    if mint_missing:
        taken = [int(c["mask"]) for c in concepts]
        for name in missing:
            record = mint_concept(name, taken)
            taken.append(int(record["mask"]))
            minted.append(record)
            concepts.append(record)
            by_name[name] = record

    edges: List[Dict[str, object]] = []
    dropped: List[Dict[str, object]] = []
    for edge in raw_edges:
        src, dst = edge.get("src"), edge.get("dst")
        label = edge.get("label")
        record = {"src": src, "label": label, "dst": dst}
        if (src is None or dst is None
                or str(src) not in by_name or str(dst) not in by_name):
            dropped.append(record)
            continue
        edges.append({"src": str(src), "label": str(label),
                      "dst": str(dst)})

    colours: List[Dict[str, object]] = []
    for task, address in addresses:
        mask = address_to_mask(int(address))
        colours.append({
            "task": task,
            "address": int(address),
            "mask": mask,
            "hexcolour": hexcolour_of_mask(mask),
            "is_codeword": mask in GOLAY_SET,
            "decode": decode_record(mask),
        })

    face_records: List[Dict[str, object]] = []
    for face in faces:
        vertices = [str(name) for name in face]
        face_records.append({
            "vertices": vertices,
            "resolved": all(name in by_name for name in vertices),
            "unresolved": [name for name in vertices if name not in by_name],
        })

    masks = [int(c["mask"]) for c in concepts]
    gaps = [Fraction(*c["nrci_gap"]) for c in concepts  # type: ignore[misc]
            if c["nrci_gap"] is not None]
    worst = max(gaps) if gaps else Fraction(0)
    roles_agree = sum(1 for c in concepts
                      if c["role_stored"] in (None, c["role"]))
    ambiguous = sum(1 for c in concepts
                    if c["decode"]["status"] == "ambiguous")  # type: ignore
    corrected = sum(1 for c in concepts
                    if c["decode"]["status"] == "corrected")  # type: ignore
    exact = sum(1 for c in concepts
                if c["decode"]["status"] == "codeword")  # type: ignore

    checks = {
        "concepts_imported": imported_count,
        "concepts_minted": len(minted),
        "concepts_total": len(concepts),
        "masks_distinct": len(set(masks)) == len(masks),
        "edges_migrated": len(edges),
        "edges_dropped": len(dropped),
        "edges_nameless_endpoints": nameless,
        "endpoints_without_a_carrier": len(missing),
        "referentially_intact": all(edge["src"] in by_name
                                    and edge["dst"] in by_name
                                    for edge in edges),
        "quadrant_weights_agree":
            sum(1 for c in concepts if c["quadrant_weights_stored_agree"]),
        "roles_agree": roles_agree,
        "carriers_that_are_codewords":
            sum(1 for m in masks if m in GOLAY_SET),
        "decode_codeword": exact,
        "decode_corrected": corrected,
        "decode_ambiguous": ambiguous,
        "decode_guaranteed":
            sum(1 for c in concepts
                if c["decode"]["guaranteed"]),  # type: ignore[index]
        "worst_nrci_gap": _fraction_pair(worst),
        "nrci_gaps_measured": len(gaps),
        "addresses": len(colours),
        "addresses_that_are_codewords":
            sum(1 for c in colours if c["is_codeword"]),
        "faces": len(face_records),
        "faces_resolved": sum(1 for f in face_records if f["resolved"]),
    }

    return {
        "format": FORMAT,
        "source": {
            "concepts": imported_count,
            "crg_edges": len(raw_edges),
            "runs": len(state.get("run_history", []) or []),
            "last_updated": state.get("last_updated"),
        },
        "frame": {
            "vectors": frame_audit(),
            "addresses": (address_audit([a for _, a in addresses])
                          if addresses else None),
            "permutation_damage": permutation_damage_report(),
            "bit_reversal": list(BIT_REVERSAL),
        },
        "y": {
            "package": _fraction_pair(Y),
            "pipeline": _fraction_pair(Y_PIPELINE),
            "disagreement": _fraction_pair(y_disagreement()),
        },
        "concepts": concepts,
        "edges": edges,
        "dropped_edges": dropped,
        "hexcolours": colours,
        "faces": face_records,
        "checks": checks,
    }


def canonical_payload(mint_missing: bool = True
                      ) -> Optional[Dict[str, object]]:
    """Migrate whatever of the state this checkout has, or ``None``."""
    state = load_state()
    if state is None:
        return None
    return migrate_state(state, load_addresses(), load_faces(),
                         mint_missing=mint_missing)


def write_canonical(path: Optional[Path] = None,
                    mint_missing: bool = True) -> Optional[Path]:
    """Write the migrated state; returns the path, or ``None`` if no source."""
    payload = canonical_payload(mint_missing=mint_missing)
    if payload is None:
        return None
    target = Path(path or canonical_path())
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1, sort_keys=False)
        handle.write("\n")
    return target


def load_canonical(path: Optional[Path] = None
                   ) -> Optional[Dict[str, object]]:
    """The migrated state as written, or ``None`` if it has not been written."""
    target = Path(path or canonical_path())
    if not target.is_file():
        return None
    payload = _read_json(target)
    if not isinstance(payload, dict):
        raise ValueError(f"load_canonical: {target} is not an object")
    return payload


# ===========================================================================
# 5.  VERIFYING A WRITTEN PAYLOAD
# ===========================================================================

def verify_canonical(payload: Mapping[str, object]) -> Dict[str, object]:
    """Re-derive every field of a payload from its masks alone.

    This is what makes the migrated file trustworthy without the source: the
    carriers are the only input, and everything else -- weights, quadrant
    weights, roles, hexcolours, addresses, NRCI, decode status -- is
    recomputed and compared.  No float is constructed.
    """
    concepts = payload.get("concepts", [])
    edges = payload.get("edges", [])
    colours = payload.get("hexcolours", [])
    faces = payload.get("faces", [])
    if not isinstance(concepts, list) or not isinstance(edges, list):
        raise ValueError("verify_canonical: malformed payload")

    names = {str(c["name"]) for c in concepts}
    bad_fields: List[str] = []
    floats = 0
    for concept in concepts:
        mask = int(concept["mask"])
        weight = bin(mask).count("1")
        if weight != int(concept["weight"]):
            bad_fields.append(f"{concept['name']}: weight")
        if list(quadrant_weights(mask)) != list(concept["quadrant_weights"]):
            bad_fields.append(f"{concept['name']}: quadrant weights")
        if role_of(mask) != concept["role"]:
            bad_fields.append(f"{concept['name']}: role")
        if hexcolour_of_mask(mask) != concept["hexcolour"]:
            bad_fields.append(f"{concept['name']}: hexcolour")
        if mask_to_address(mask) != int(concept["address"]):
            bad_fields.append(f"{concept['name']}: address")
        if Fraction(*concept["nrci"]) != exact_nrci(weight):
            bad_fields.append(f"{concept['name']}: nrci")
        if decode_record(mask) != concept["decode"]:
            bad_fields.append(f"{concept['name']}: decode")
        for value in concept.values():
            if isinstance(value, float):
                floats += 1

    dangling = [edge for edge in edges
                if str(edge["src"]) not in names
                or str(edge["dst"]) not in names]
    address_ok = all(address_to_mask(int(c["address"])) == int(c["mask"])
                     for c in colours)
    faces_ok = all(f["resolved"] == all(v in names for v in f["vertices"])
                   for f in faces)
    masks = [int(c["mask"]) for c in concepts]
    return {
        "format": payload.get("format"),
        "concepts": len(concepts),
        "edges": len(edges),
        "fields_recomputed_and_agreeing": not bad_fields,
        "disagreements": bad_fields[:10],
        "masks_distinct": len(set(masks)) == len(masks),
        "referentially_intact": not dangling,
        "dangling_edges": len(dangling),
        "addresses_round_trip": address_ok,
        "faces_consistent": faces_ok,
        "floats_in_payload": floats,
        "frames_coincide": bool(
            payload.get("frame", {}).get("vectors", {})  # type: ignore
            .get("frames_coincide")),
    }


# ===========================================================================
# 6.  THE HEXCOLOUR LAYER, AUDITED
# ===========================================================================

def hexcolour_audit(payload: Optional[Mapping[str, object]] = None
                    ) -> Dict[str, object]:
    """Are the hexcolour addresses actually carrying anything?

    A hexcolour is the six-hex-digit rendering of a 24-bit mask -- one hex
    digit per four coordinates -- so it is an *address*, in the sense of D3:
    it fixes the carrier exactly and means nothing beyond it.  The question
    this answers is whether the layer is doing that job on the shipped data
    rather than merely existing, and every number below is measured here:

    * ``concepts`` / ``distinct`` -- how many migrated concepts carry an
      address, and how many distinct addresses those are.  Equality is the
      claim that the rendering loses nothing.
    * ``round_trip_failures`` -- concepts whose address does not read back to
      its own mask through the public converters in
      :mod:`glm_universal.substrate.isomorphism`.
    * ``recomputed_disagreements`` -- concepts whose stored address is not the
      one the mask produces, which is what
      :func:`verify_canonical` refuses to let happen.
    * ``migration_mismatches`` -- addresses for which permuting the coordinate
      set and re-rendering disagrees with rendering and then migrating, i.e.
      whether the address layer commutes with the legacy-to-core relabelling.
    * ``legacy_*`` -- the same questions for the separate per-task address
      table the supplied ARC pipeline left behind.
    """
    from ..substrate.isomorphism import (hexcolour_to_mask, mask_to_hexcolour,
                                         migrate_hexcolour, to_core_mask)

    if payload is None:
        loaded = load_canonical()
        payload = loaded if loaded is not None else canonical_payload()
    if payload is None:
        return {"available": False}

    concepts = list(payload.get("concepts", []))  # type: ignore[arg-type]
    colours = [str(c["hexcolour"]) for c in concepts]
    masks = [int(c["mask"]) for c in concepts]
    round_trip = sum(1 for colour, mask in zip(colours, masks)
                     if hexcolour_to_mask(colour) != mask)
    recomputed = sum(1 for colour, mask in zip(colours, masks)
                     if mask_to_hexcolour(mask) != colour)
    migrated = sum(1 for colour, mask in zip(colours, masks)
                   if hexcolour_to_mask(migrate_hexcolour(colour))
                   != to_core_mask(mask))

    legacy = list(payload.get("hexcolours", []))  # type: ignore[arg-type]
    legacy_colours = [str(r["hexcolour"]) for r in legacy]
    legacy_masks = [int(r["mask"]) for r in legacy]
    legacy_round_trip = sum(1 for colour, mask in zip(legacy_colours,
                                                      legacy_masks)
                            if hexcolour_to_mask(colour) != mask)
    return {
        "available": True,
        "concepts": len(concepts),
        "distinct": len(set(colours)),
        "collisions": len(colours) - len(set(colours)),
        "round_trip_failures": round_trip,
        "recomputed_disagreements": recomputed,
        "migration_mismatches": migrated,
        "legacy_addresses": len(legacy),
        "legacy_codewords": sum(1 for r in legacy if bool(r["is_codeword"])),
        "legacy_distinct": len(set(legacy_colours)),
        "legacy_round_trip_failures": legacy_round_trip,
        "faithful": (round_trip == 0 and recomputed == 0
                     and migrated == 0 and legacy_round_trip == 0
                     and len(set(colours)) == len(colours)),
    }


# ===========================================================================
# 7.  THE REPORT
# ===========================================================================

def state_migration_report() -> Dict[str, object]:
    """Everything the migration claims, recomputed.

    Prefers the migrated file if it has been written -- that is the artefact
    the rest of the system consumes -- and falls back to migrating the source
    in memory.  When both are present the two are compared, so the shipped
    file cannot drift from the source it came from.
    """
    written = load_canonical()
    payload = written if written is not None else canonical_payload()
    if payload is None:
        return {
            "available": False,
            "reading": ("neither the migrated state nor the source state is "
                        "present in this checkout"),
        }
    verification = verify_canonical(payload)
    fresh = canonical_payload() if written is not None else None
    reproduces = (None if fresh is None
                  else fresh["checks"] == payload["checks"])
    checks = dict(payload["checks"])  # type: ignore[arg-type]
    frame = payload["frame"]  # type: ignore[index]
    return {
        "available": True,
        "written": written is not None,
        "source_present": state_path() is not None,
        "source_reproduces_the_file": reproduces,
        "checks": checks,
        "verification": verification,
        "hexcolours": hexcolour_audit(payload),
        "frame": {
            "frames_coincide": frame["vectors"]["frames_coincide"],
            "shared_codewords": frame["vectors"]["shared_codewords"],
            "correct_bridge": frame["vectors"]["correct_bridge"],
            "addresses": frame["addresses"],
            "permutation_damage":
                frame["permutation_damage"]["codewords_leaving_the_code"],
        },
        "y": payload["y"],
        "reading": ("the stored state is already in the canonical Golay "
                    "frame; the only coordinate correction it needs is the "
                    "bit reversal of stored integer addresses, and the work "
                    "of the migration is exactness, audited decoding and "
                    "referential integrity"),
    }

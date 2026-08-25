"""``glm_universal.substrate.isomorphism`` -- the legacy-to-core migration.

Why this module exists
----------------------
The project's earlier work used a **legacy** Golay code whose coordinates are
a permutation of this package's canonical one.  The two codes share only 8 of
their 4,096 codewords, so a legacy carrier read in canonical coordinates is
not merely mislabelled -- it is a different codeword, and decoding it in the
wrong frame corrupts it silently.  The relating permutation was derived from
the Steiner system ``S(5, 8, 24)`` formed by each code's 759 octads:

    ``LEGACY_TO_CORE = (0,1,2,3,4,5,7,16,8,19,22,9,13,12,10,18,14,15,21,6,11,
    20,23,17)``

This module makes that permutation the *only* sanctioned bridge between the
two frames, and gives the migration a single entry point.

What it provides
----------------
**Permutation algebra.**  :func:`invert_permutation`,
:func:`compose_permutations`, :func:`permute_mask` (24-bit masks),
:func:`permute_vector` (24-coordinate carriers) and :func:`permute_indices`,
each checking its argument rather than trusting it.

**The legacy frame, reconstructed.**  :func:`legacy_code` is the image of the
canonical Golay code under ``CORE_TO_LEGACY``.  It is a genuine ``[24, 12, 8]``
code with the same weight distribution, it is *not* the canonical code
(:func:`shared_codewords` counts the 8 words they have in common), and
:func:`is_golay_automorphism` reports -- with a witness -- that the
permutation is therefore not an automorphism of the canonical code.  That is
the point: it is an isomorphism between two different codes.

**Why a permutation and not any linear isomorphism.**  A permutation of
coordinates preserves Hamming weight and Hamming distance
(:func:`isometry_report` checks this exhaustively on a spanning set and on a
sweep of error patterns), so it commutes with nearest-codeword decoding.  A
general linear isomorphism between the two codes also exists but scrambles
distance, and therefore cannot be wrapped around a decoder.  Only the
permutation may be.

**Decoding legacy data correctly.**  :func:`decode_legacy` routes a legacy
word through the canonical frame, decodes it with the audited complete
decoder of :mod:`glm_universal.substrate.golay_decode`, and brings the answer
back.  :func:`legacy_decoder_comparison` measures the difference against
snapping inside the legacy frame: over the same sweep, every silently broken
tie becomes an explicit ``"ambiguous"`` status.

**Bulk migration.**  :class:`MigrationSpec` names which fields of a record
hold masks, carriers or hexcolour addresses; :func:`migrate_record` and
:func:`migrate_records` apply the permutation to exactly those fields and
leave everything else -- identifiers, labels, edge endpoints -- untouched.
:func:`migrate_dataset` migrates concepts, edges and hexcolour addresses
together and checks the result: bijectivity, round trip, weight preservation,
and referential integrity of the edge endpoints.

Hexcolour addresses
-------------------
A persistent lattice address is written as six hexadecimal digits, which is
exactly a 24-bit mask.  :func:`hexcolour_to_mask` and :func:`mask_to_hexcolour`
convert, and :func:`migrate_hexcolour` permutes in between, so an address
migrates as the coordinate set it denotes rather than as a string.

Status of the data migration
----------------------------
The concept, CRG-edge and hexcolour tables that this machinery is meant to
carry across are not part of this package; :func:`migrate_dataset` is written
against their shape, and :func:`migration_report` exercises the whole path on
a dataset built from the package's own structures (the 759 octads as
concepts, their overlaps as edges, and a set of hexcolour addresses) so that
the migration is tested rather than merely declared.

Exact integer arithmetic throughout; no randomness, standard library only.
"""

from __future__ import annotations

from fractions import Fraction
from typing import (Dict, Iterable, List, Mapping, Optional, Sequence, Tuple)

from .golay_decode import Decoding, decode_complete
from .mog import GOLAY_MASKS, GOLAY_SET

__all__ = [
    "DIM", "LEGACY_TO_CORE", "CORE_TO_LEGACY", "MigrationSpec",
    "CONCEPT_SPEC", "EDGE_SPEC", "HEXCOLOUR_SPEC",
    "is_permutation", "invert_permutation", "compose_permutations",
    "permute_mask", "permute_vector", "permute_indices",
    "to_core_mask", "to_legacy_mask", "to_core_vector", "to_legacy_vector",
    "hexcolour_to_mask", "mask_to_hexcolour", "migrate_hexcolour",
    "legacy_code", "shared_codewords", "weight_distribution",
    "is_golay_automorphism", "isometry_report", "code_report",
    "decode_legacy", "legacy_snap_in_legacy_frame",
    "legacy_decoder_comparison",
    "migrate_record", "migrate_records", "migrate_dataset",
    "sample_dataset", "migration_report",
]

#: The number of coordinates.  Everything here is a permutation of these.
DIM = 24

#: The derived coordinate permutation taking a **legacy** coordinate index to
#: its **canonical** one.  Read it as ``core_index = LEGACY_TO_CORE[legacy_
#: index]``.
LEGACY_TO_CORE: Tuple[int, ...] = (
    0, 1, 2, 3, 4, 5, 7, 16, 8, 19, 22, 9,
    13, 12, 10, 18, 14, 15, 21, 6, 11, 20, 23, 17,
)


def is_permutation(perm: Sequence[int], size: int = DIM) -> bool:
    """Whether ``perm`` is a permutation of ``range(size)``."""
    return (len(perm) == size
            and all(isinstance(x, int) and not isinstance(x, bool)
                    for x in perm)
            and sorted(perm) == list(range(size)))


def _check_permutation(perm: Sequence[int], where: str) -> Tuple[int, ...]:
    if not is_permutation(perm):
        raise ValueError(f"{where}: not a permutation of range({DIM})")
    return tuple(perm)


def invert_permutation(perm: Sequence[int]) -> Tuple[int, ...]:
    """The inverse permutation."""
    p = _check_permutation(perm, "invert_permutation")
    out = [0] * DIM
    for i, target in enumerate(p):
        out[target] = i
    return tuple(out)


def compose_permutations(first: Sequence[int],
                         second: Sequence[int]) -> Tuple[int, ...]:
    """``second`` after ``first``: ``compose(f, s)[i] == s[f[i]]``."""
    f = _check_permutation(first, "compose_permutations")
    s = _check_permutation(second, "compose_permutations")
    return tuple(s[f[i]] for i in range(DIM))


#: The inverse bridge: ``legacy_index = CORE_TO_LEGACY[core_index]``.
CORE_TO_LEGACY: Tuple[int, ...] = invert_permutation(LEGACY_TO_CORE)


# ===========================================================================
# 1.  APPLYING A PERMUTATION
# ===========================================================================

def _check_mask(mask: int, where: str) -> int:
    if not isinstance(mask, int) or isinstance(mask, bool):
        raise TypeError(f"{where}: mask must be an int, got {type(mask)}")
    if not 0 <= mask < (1 << DIM):
        raise ValueError(f"{where}: mask {mask} is not a {DIM}-bit word")
    return mask


def permute_mask(mask: int, perm: Sequence[int] = LEGACY_TO_CORE) -> int:
    """Move the bit at coordinate ``i`` to coordinate ``perm[i]``."""
    p = _check_permutation(perm, "permute_mask")
    m = _check_mask(mask, "permute_mask")
    out = 0
    for i in range(DIM):
        if (m >> i) & 1:
            out |= 1 << p[i]
    return out


def permute_vector(vector: Sequence,
                   perm: Sequence[int] = LEGACY_TO_CORE) -> Tuple:
    """Move coordinate ``i`` of a 24-vector to position ``perm[i]``.

    Entries are copied, never coerced: an ``int`` stays an ``int`` and a
    :class:`~fractions.Fraction` stays a ``Fraction``.  A ``float`` is
    refused, as everywhere in this package.
    """
    p = _check_permutation(perm, "permute_vector")
    if len(vector) != DIM:
        raise ValueError(f"permute_vector: expected {DIM} coordinates, "
                         f"got {len(vector)}")
    for entry in vector:
        if isinstance(entry, float):
            raise TypeError("permute_vector: refusing a float coordinate")
    out: List[object] = [0] * DIM
    for i, entry in enumerate(vector):
        out[p[i]] = entry
    return tuple(out)


def permute_indices(indices: Iterable[int],
                    perm: Sequence[int] = LEGACY_TO_CORE) -> Tuple[int, ...]:
    """Relabel a set of coordinate indices, returned sorted."""
    p = _check_permutation(perm, "permute_indices")
    out = []
    for i in indices:
        if not isinstance(i, int) or isinstance(i, bool):
            raise TypeError("permute_indices: indices must be ints")
        if not 0 <= i < DIM:
            raise ValueError(f"permute_indices: index {i} out of range")
        out.append(p[i])
    return tuple(sorted(out))


def to_core_mask(mask: int) -> int:
    """A legacy 24-bit word read in canonical coordinates."""
    return permute_mask(mask, LEGACY_TO_CORE)


def to_legacy_mask(mask: int) -> int:
    """A canonical 24-bit word read back in legacy coordinates."""
    return permute_mask(mask, CORE_TO_LEGACY)


def to_core_vector(vector: Sequence) -> Tuple:
    """A legacy 24-coordinate carrier read in canonical coordinates."""
    return permute_vector(vector, LEGACY_TO_CORE)


def to_legacy_vector(vector: Sequence) -> Tuple:
    """A canonical carrier read back in legacy coordinates."""
    return permute_vector(vector, CORE_TO_LEGACY)


# ===========================================================================
# 2.  HEXCOLOUR ADDRESSES
# ===========================================================================

def hexcolour_to_mask(colour: str) -> int:
    """``"#a1b2c3"`` or ``"a1b2c3"`` -> the 24-bit mask it denotes."""
    if not isinstance(colour, str):
        raise TypeError(f"hexcolour_to_mask: expected a string, "
                        f"got {type(colour)}")
    text = colour.strip()
    if text.startswith("#"):
        text = text[1:]
    if len(text) != 6:
        raise ValueError(f"hexcolour_to_mask: {colour!r} is not six hex "
                         f"digits")
    try:
        return int(text, 16)
    except ValueError as exc:
        raise ValueError(f"hexcolour_to_mask: {colour!r} is not "
                         f"hexadecimal") from exc


def mask_to_hexcolour(mask: int, hashed: bool = True) -> str:
    """The six-hex-digit address of a 24-bit mask."""
    m = _check_mask(mask, "mask_to_hexcolour")
    return ("#" if hashed else "") + format(m, "06x")


def migrate_hexcolour(colour: str,
                      perm: Sequence[int] = LEGACY_TO_CORE) -> str:
    """Permute the coordinate set a hexcolour address denotes."""
    hashed = isinstance(colour, str) and colour.strip().startswith("#")
    return mask_to_hexcolour(permute_mask(hexcolour_to_mask(colour), perm),
                             hashed=hashed)


# ===========================================================================
# 3.  THE TWO CODES
# ===========================================================================

_LEGACY_CODE: Optional[Tuple[int, ...]] = None


def legacy_code() -> Tuple[int, ...]:
    """The legacy Golay code: the canonical code read in legacy coordinates.

    Sorted, 4,096 words.  By construction ``to_core_mask`` maps it onto
    :data:`~glm_universal.substrate.mog.GOLAY_SET`.
    """
    global _LEGACY_CODE
    if _LEGACY_CODE is None:
        _LEGACY_CODE = tuple(sorted(to_legacy_mask(c) for c in GOLAY_MASKS))
    return _LEGACY_CODE


def shared_codewords() -> Tuple[int, ...]:
    """The words the two codes have in common, sorted."""
    return tuple(sorted(set(legacy_code()) & set(GOLAY_SET)))


def weight_distribution(words: Iterable[int]) -> Dict[int, int]:
    """How many words of each Hamming weight."""
    out: Dict[int, int] = {}
    for word in words:
        w = bin(_check_mask(word, "weight_distribution")).count("1")
        out[w] = out.get(w, 0) + 1
    return dict(sorted(out.items()))


def is_golay_automorphism(perm: Sequence[int] = LEGACY_TO_CORE
                          ) -> Dict[str, object]:
    """Whether ``perm`` maps the canonical code onto itself.

    For :data:`LEGACY_TO_CORE` the answer is ``False``, and that is correct:
    it is an isomorphism between two *different* codes, so it necessarily
    moves canonical codewords off the canonical code.  A witness is returned.
    """
    p = _check_permutation(perm, "is_golay_automorphism")
    escaped = [c for c in GOLAY_MASKS if permute_mask(c, p) not in GOLAY_SET]
    witness = None
    if escaped:
        c = min(escaped)
        witness = {
            "codeword": c,
            "image": permute_mask(c, p),
            "image_weight": bin(permute_mask(c, p)).count("1"),
            "image_is_a_codeword": False,
        }
    return {
        "is_automorphism": not escaped,
        "codewords": len(GOLAY_MASKS),
        "codewords_leaving_the_code": len(escaped),
        "witness": witness,
    }


def isometry_report(perm: Sequence[int] = LEGACY_TO_CORE,
                    sweep: int = 24) -> Dict[str, object]:
    """That a coordinate permutation preserves weight and distance.

    Weight preservation is checked on every canonical codeword; distance
    preservation on the codewords against a sweep of single-coordinate error
    patterns, which is what makes the map safe to wrap around a decoder.
    """
    p = _check_permutation(perm, "isometry_report")
    weight_ok = True
    for c in GOLAY_MASKS:
        if bin(c).count("1") != bin(permute_mask(c, p)).count("1"):
            weight_ok = False
            break
    distance_ok = True
    checked = 0
    for c in GOLAY_MASKS[:64]:
        for i in range(min(sweep, DIM)):
            other = c ^ (1 << i)
            before = bin(c ^ other).count("1")
            after = bin(permute_mask(c, p) ^ permute_mask(other, p)).count("1")
            checked += 1
            if before != after:
                distance_ok = False
    return {
        "is_permutation": True,
        "weight_preserving": weight_ok,
        "codewords_checked": len(GOLAY_MASKS),
        "distance_preserving": distance_ok,
        "pairs_checked": checked,
        "commutes_with_decoding": weight_ok and distance_ok,
    }


def code_report() -> Dict[str, object]:
    """The two codes side by side."""
    legacy = legacy_code()
    shared = shared_codewords()
    wd_core = weight_distribution(GOLAY_MASKS)
    wd_legacy = weight_distribution(legacy)
    return {
        "core_codewords": len(GOLAY_MASKS),
        "legacy_codewords": len(legacy),
        "legacy_is_distinct": set(legacy) != set(GOLAY_SET),
        "shared_codewords": len(shared),
        "shared": list(shared),
        "weight_distribution_core": wd_core,
        "weight_distribution_legacy": wd_legacy,
        "weight_distributions_agree": wd_core == wd_legacy,
        "minimum_distance": min(w for w in wd_core if w > 0),
        "octads_core": wd_core.get(8, 0),
        "octads_legacy": wd_legacy.get(8, 0),
        "automorphism": is_golay_automorphism(),
        "isometry": isometry_report(),
    }


# ===========================================================================
# 4.  DECODING LEGACY DATA
# ===========================================================================

def decode_legacy(mask: int) -> Dict[str, object]:
    """Decode a legacy word by routing it through the canonical frame.

    Permute into canonical coordinates, decode with the complete decoder,
    permute the answer back.  Because the bridge is an isometry this is
    exactly nearest-codeword decoding in the legacy code -- with every tie
    reported rather than broken.
    """
    core = to_core_mask(mask)
    decoding: Decoding = decode_complete(core)
    corrected = (to_legacy_mask(decoding.corrected)
                 if decoding.corrected is not None else None)
    return {
        "received": mask,
        "core_word": core,
        "weight": decoding.weight,
        "status": decoding.status,
        "guaranteed": decoding.guaranteed,
        "corrected": corrected,
        "candidates": tuple(sorted(to_legacy_mask(c)
                                   for c in decoding.candidates)),
        "leaders": tuple(sorted(to_legacy_mask(e)
                                for e in decoding.leaders)),
    }


def legacy_snap_in_legacy_frame(mask: int) -> Tuple[int, int, int]:
    """The retired behaviour: scan the legacy code, keep the first nearest.

    Returns ``(codeword, distance, tied)`` where ``tied`` counts how many
    codewords were equally near.  Kept only so that
    :func:`legacy_decoder_comparison` can measure what it used to hide.
    """
    _check_mask(mask, "legacy_snap_in_legacy_frame")
    best_word, best_dist, tied = 0, DIM + 1, 0
    for word in legacy_code():
        d = bin(mask ^ word).count("1")
        if d < best_dist:
            best_dist, best_word, tied = d, word, 1
        elif d == best_dist:
            tied += 1
    return best_word, best_dist, tied


def legacy_decoder_comparison(max_weight: int = 5,
                              per_weight: int = 24) -> Dict[str, object]:
    """Snapping inside the legacy frame against the routed complete decoder.

    For each error weight, error patterns are taken in sorted order (never at
    random) and added to legacy codewords.  The two decoders are compared on
    recovery of the truth, and on whether a tie was broken silently.
    """
    legacy = legacy_code()
    rows = []
    for weight in range(max_weight + 1):
        patterns = _error_patterns(weight, per_weight)
        snap_recovered = snap_silent_ties = 0
        routed_recovered = routed_flagged = routed_miscorrected = 0
        sampled = 0
        for index, error in enumerate(patterns):
            truth = legacy[(index * 37) % len(legacy)]
            received = truth ^ error
            sampled += 1
            word, _dist, tied = legacy_snap_in_legacy_frame(received)
            if word == truth:
                snap_recovered += 1
            if tied > 1:
                snap_silent_ties += 1
            routed = decode_legacy(received)
            if routed["status"] == "ambiguous":
                routed_flagged += 1
            elif routed["corrected"] == truth:
                routed_recovered += 1
            else:
                routed_miscorrected += 1
        rows.append({
            "weight": weight,
            "sampled": sampled,
            "snap_recovered": snap_recovered,
            "snap_silent_ties": snap_silent_ties,
            "routed_recovered": routed_recovered,
            "routed_flagged_ambiguous": routed_flagged,
            "routed_miscorrected": routed_miscorrected,
        })
    silent = sum(row["snap_silent_ties"] for row in rows)
    flagged = sum(row["routed_flagged_ambiguous"] for row in rows)
    return {
        "rows": rows,
        "snap_silent_ties_total": silent,
        "routed_flagged_total": flagged,
        "every_silent_tie_is_now_flagged": silent == flagged,
        "guaranteed_below_packing_radius": all(
            row["routed_recovered"] == row["sampled"]
            for row in rows if row["weight"] <= 3),
        "note": ("weight-5 miscorrection survives in both columns and is not "
                 "a decoder defect: every 5-subset lies in a unique octad, so "
                 "the nearest codeword is unique, confident and wrong"),
    }


def _error_patterns(weight: int, count: int) -> Tuple[int, ...]:
    """The first ``count`` error patterns of a given weight, in sorted order."""
    if weight == 0:
        return (0,)
    out: List[int] = []
    for mask in range(1 << DIM):
        if bin(mask).count("1") == weight:
            out.append(mask)
            if len(out) >= count:
                break
        if mask > (1 << 16) and len(out) >= count:
            break
    return tuple(out)


# ===========================================================================
# 5.  BULK MIGRATION
# ===========================================================================

class MigrationSpec:
    """Which fields of a record hold coordinates, and in what shape.

    A record is a plain mapping.  Only the named fields are touched; every
    other key is copied through unchanged, so identifiers, labels, weights
    and provenance survive the migration untouched.
    """

    def __init__(self,
                 mask_fields: Sequence[str] = (),
                 vector_fields: Sequence[str] = (),
                 hexcolour_fields: Sequence[str] = (),
                 index_fields: Sequence[str] = (),
                 name: str = "record") -> None:
        self.mask_fields = tuple(mask_fields)
        self.vector_fields = tuple(vector_fields)
        self.hexcolour_fields = tuple(hexcolour_fields)
        self.index_fields = tuple(index_fields)
        self.name = name

    @property
    def fields(self) -> Tuple[str, ...]:
        """Every field this spec migrates."""
        return (self.mask_fields + self.vector_fields
                + self.hexcolour_fields + self.index_fields)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (f"MigrationSpec(name={self.name!r}, "
                f"fields={list(self.fields)})")


#: A concept carries a 24-bit mask, a 24-coordinate carrier, and optionally a
#: persistent hexcolour address.
CONCEPT_SPEC = MigrationSpec(mask_fields=("mask",),
                             vector_fields=("carrier",),
                             hexcolour_fields=("hexcolour",),
                             name="concept")

#: A CRG edge names two concepts by identifier -- which the permutation does
#: **not** touch -- and may carry a mask of the coordinates it acts on.
EDGE_SPEC = MigrationSpec(mask_fields=("mask",),
                          index_fields=("coordinates",),
                          name="edge")

#: A persistent address is just its colour.
HEXCOLOUR_SPEC = MigrationSpec(hexcolour_fields=("colour",),
                               name="hexcolour")


def migrate_record(record: Mapping[str, object], spec: MigrationSpec,
                   perm: Sequence[int] = LEGACY_TO_CORE
                   ) -> Dict[str, object]:
    """Permute the coordinate-bearing fields of one record."""
    out: Dict[str, object] = dict(record)
    for field in spec.mask_fields:
        if field in out and out[field] is not None:
            out[field] = permute_mask(int(out[field]), perm)  # type: ignore
    for field in spec.vector_fields:
        if field in out and out[field] is not None:
            out[field] = permute_vector(out[field], perm)  # type: ignore
    for field in spec.hexcolour_fields:
        if field in out and out[field] is not None:
            out[field] = migrate_hexcolour(str(out[field]), perm)
    for field in spec.index_fields:
        if field in out and out[field] is not None:
            out[field] = permute_indices(out[field], perm)  # type: ignore
    return out


def migrate_records(records: Sequence[Mapping[str, object]],
                    spec: MigrationSpec,
                    perm: Sequence[int] = LEGACY_TO_CORE
                    ) -> Tuple[Dict[str, object], ...]:
    """Permute a whole table, preserving order."""
    return tuple(migrate_record(r, spec, perm) for r in records)


def migrate_dataset(concepts: Sequence[Mapping[str, object]] = (),
                    edges: Sequence[Mapping[str, object]] = (),
                    hexcolours: Sequence[Mapping[str, object]] = (),
                    perm: Sequence[int] = LEGACY_TO_CORE
                    ) -> Dict[str, object]:
    """Migrate concepts, CRG edges and hexcolour addresses in one call.

    Returns the migrated tables together with the checks that decide whether
    the migration was lossless: every coordinate-bearing field round-trips
    under the inverse permutation, Hamming weights are unchanged, and every
    edge endpoint still names a concept that exists.
    """
    inverse = invert_permutation(perm)
    new_concepts = migrate_records(concepts, CONCEPT_SPEC, perm)
    new_edges = migrate_records(edges, EDGE_SPEC, perm)
    new_colours = migrate_records(hexcolours, HEXCOLOUR_SPEC, perm)

    round_trip = (
        migrate_records(new_concepts, CONCEPT_SPEC, inverse)
        == tuple(dict(r) for r in concepts)
        and migrate_records(new_edges, EDGE_SPEC, inverse)
        == tuple(dict(r) for r in edges)
        and migrate_records(new_colours, HEXCOLOUR_SPEC, inverse)
        == tuple(dict(r) for r in hexcolours))

    weights_preserved = True
    for before, after in zip(concepts, new_concepts):
        if "mask" in before and before["mask"] is not None:
            if (bin(int(before["mask"])).count("1")  # type: ignore
                    != bin(int(after["mask"])).count("1")):  # type: ignore
                weights_preserved = False
        if "carrier" in before and before["carrier"] is not None:
            if (sorted(map(str, before["carrier"]))  # type: ignore
                    != sorted(map(str, after["carrier"]))):  # type: ignore
                weights_preserved = False

    identifiers = {r.get("id") for r in new_concepts}
    dangling = [r for r in new_edges
                if r.get("source") not in identifiers
                or r.get("target") not in identifiers]

    masks = [r["mask"] for r in new_concepts if r.get("mask") is not None]
    return {
        "concepts": new_concepts,
        "edges": new_edges,
        "hexcolours": new_colours,
        "checks": {
            "concepts": len(new_concepts),
            "edges": len(new_edges),
            "hexcolours": len(new_colours),
            "round_trip": round_trip,
            "weights_preserved": weights_preserved,
            "masks_still_distinct": len(set(masks)) == len(masks),
            "dangling_edges": len(dangling),
            "referentially_intact": not dangling,
        },
    }


# ===========================================================================
# 6.  A DATASET TO EXERCISE IT ON, AND THE REPORT
# ===========================================================================

def sample_dataset(concept_count: int = 64, edge_count: int = 96,
                   colour_count: int = 66) -> Dict[str, object]:
    """A dataset in the shape of the real one, built from the octads.

    Concepts are octads of the legacy code (mask, carrier and hexcolour
    address); edges join consecutive concepts and carry the coordinates the
    two share; hexcolour addresses are taken from the legacy code in order.
    Deterministic: no randomness anywhere.
    """
    legacy = legacy_code()
    octads = [c for c in legacy if bin(c).count("1") == 8][:concept_count]
    concepts = []
    for index, mask in enumerate(octads):
        carrier = tuple(Fraction((mask >> i) & 1) for i in range(DIM))
        concepts.append({
            "id": f"c{index:04d}",
            "label": f"octad-{index}",
            "mask": mask,
            "carrier": carrier,
            "hexcolour": mask_to_hexcolour(mask),
        })
    edges = []
    for index in range(min(edge_count, max(0, len(concepts) - 1))):
        left, right = concepts[index], concepts[index + 1]
        overlap = int(left["mask"]) & int(right["mask"])  # type: ignore
        edges.append({
            "id": f"e{index:04d}",
            "source": left["id"],
            "target": right["id"],
            "mask": overlap,
            "coordinates": tuple(i for i in range(DIM)
                                 if (overlap >> i) & 1),
            "weight": bin(overlap).count("1"),
        })
    colours = [{"id": f"h{index:04d}",
                "colour": mask_to_hexcolour(legacy[index * 17 % len(legacy)])}
               for index in range(colour_count)]
    return {"concepts": tuple(concepts), "edges": tuple(edges),
            "hexcolours": tuple(colours)}


def migration_report() -> Dict[str, object]:
    """Everything this module claims, recomputed."""
    data = sample_dataset()
    migrated = migrate_dataset(data["concepts"], data["edges"],  # type: ignore
                               data["hexcolours"])  # type: ignore
    codes = code_report()
    comparison = legacy_decoder_comparison()
    return {
        "permutation": list(LEGACY_TO_CORE),
        "inverse": list(CORE_TO_LEGACY),
        "is_permutation": is_permutation(LEGACY_TO_CORE),
        "involution": LEGACY_TO_CORE == CORE_TO_LEGACY,
        "fixed_points": [i for i in range(DIM) if LEGACY_TO_CORE[i] == i],
        "codes": codes,
        "decoder": comparison,
        "dataset": migrated["checks"],
        "reading": ("the bridge is a coordinate permutation, so it preserves "
                    "Hamming weight and distance and may be wrapped around "
                    "the decoder; it is not an automorphism of the canonical "
                    "code, because the two codes it relates are different"),
    }

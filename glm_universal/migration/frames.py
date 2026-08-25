"""``glm_universal.migration.frames`` -- which Golay frame the stored data is in.

Why this module exists
----------------------
The package can only read a stored 24-bit word if it knows two things about
it: **which Golay frame** its coordinates are numbered in, and **which end of
the integer** coordinate 0 sits at.  Guessing either one silently corrupts
the data -- the word still decodes, it just decodes to the wrong codeword --
so both are settled here by computation, once, against the code that actually
wrote the data.

What the repository actually writes
-----------------------------------
Two answers, and they are not the same answer:

* **Concept vectors** (``glm_state.json``) are stored as a list of 24 bits,
  ``vector[i]`` being coordinate *i*.  There is no endianness question for a
  list, and the frame is the one of ``GolayCodeEngine`` in
  ``GMHGL/ubp_unified_v5.py``, whose parity block is reproduced here as
  :data:`ENGINE_B`.  :func:`engine_code` builds that code, and
  :func:`frame_audit` reports the finding: it is **the same 4,096 words** as
  this package's canonical :data:`~glm_universal.substrate.mog.GOLAY_SET`.
  The correct coordinate bridge for concept vectors is therefore the
  **identity**, and applying
  :data:`~glm_universal.substrate.isomorphism.LEGACY_TO_CORE` to them would
  *introduce* the corruption it was written to prevent.  See
  :func:`permutation_damage_report`, which counts the damage exactly.

* **Hexcolour addresses** (``hexcolour_addresses.json``) are stored as a
  plain integer built by ``GLM01_substrate.vector_to_hex_int`` and
  ``arc_v18_pipeline.HexColourAddress.compute_address``, both of which put
  coordinate *i* at bit ``23 - i``.  That is the opposite bit order from the
  package, where coordinate *i* is bit *i*.  The bridge is therefore the
  **bit reversal** :data:`BIT_REVERSAL`, and :func:`address_audit` shows why
  this is not a matter of taste: read with the reversal, every stored address
  is a Golay codeword; read without it, none of them is.

Both findings are recomputed by :func:`frame_report`, never quoted.

Exactness: integer arithmetic only, standard library only, no randomness.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Sequence, Tuple

from ..substrate.isomorphism import (CORE_TO_LEGACY, LEGACY_TO_CORE, DIM,
                                     permute_mask)
from ..substrate.mog import GOLAY_MASKS, GOLAY_SET

__all__ = [
    "DIM", "ENGINE_B", "engine_generator", "engine_code", "frame_audit",
    "BIT_REVERSAL", "reverse_bits", "address_to_mask", "mask_to_address",
    "address_audit", "permutation_damage_report", "frame_report",
]


# ===========================================================================
# 1.  THE FRAME THE REPOSITORY'S ENGINE USES
# ===========================================================================

#: The 12x12 parity block of ``GolayCodeEngine`` in ``ubp_unified_v5.py``,
#: transcribed verbatim.  The engine builds ``G = [I12 | B]`` from it, and
#: every concept vector in ``glm_state.json`` that was produced by
#: ``golay.encode`` is a row-combination of that ``G``.
ENGINE_B: Tuple[Tuple[int, ...], ...] = (
    (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
    (1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0),
    (1, 1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1),
    (1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1),
    (1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0),
    (1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1),
    (1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1),
    (1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1),
    (1, 0, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0),
    (1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0),
    (1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0),
    (1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 1),
)


def engine_generator() -> Tuple[int, ...]:
    """The twelve rows of ``G = [I12 | B]``, each as a 24-bit mask.

    Bit *i* of the mask is coordinate *i* of the row, which is the
    package's convention and the convention of the engine's own
    ``encode`` (it returns a list indexed by coordinate).
    """
    rows: List[int] = []
    for i in range(12):
        bits = [1 if i == j else 0 for j in range(12)] + list(ENGINE_B[i])
        mask = 0
        for index, bit in enumerate(bits):
            if bit:
                mask |= 1 << index
        rows.append(mask)
    return tuple(rows)


def engine_code() -> Tuple[int, ...]:
    """All 4,096 codewords of the repository engine's Golay code, sorted."""
    rows = engine_generator()
    words: List[int] = []
    for message in range(1 << 12):
        mask = 0
        for i in range(12):
            if (message >> i) & 1:
                mask ^= rows[i]
        words.append(mask)
    return tuple(sorted(words))


def _weight_distribution(words: Iterable[int]) -> Dict[int, int]:
    out: Dict[int, int] = {}
    for word in words:
        weight = bin(word).count("1")
        out[weight] = out.get(weight, 0) + 1
    return dict(sorted(out.items()))


def frame_audit() -> Dict[str, object]:
    """Compare the engine's code with the package's canonical one.

    The answer -- computed, not asserted -- is that they are the *same set of
    words*.  The stored concept vectors therefore need no coordinate
    permutation at all: the identity is the correct bridge.
    """
    engine = engine_code()
    engine_set = set(engine)
    canonical = set(GOLAY_SET)
    shared = engine_set & canonical
    return {
        "engine_codewords": len(engine_set),
        "canonical_codewords": len(canonical),
        "shared_codewords": len(shared),
        "frames_coincide": engine_set == canonical,
        "engine_weight_distribution": _weight_distribution(engine),
        "canonical_weight_distribution": _weight_distribution(canonical),
        "correct_bridge": "identity",
        "reading": ("the repository's GolayCodeEngine and this package's "
                    "canonical Golay code are the same 4,096 words under the "
                    "same coordinate numbering, so concept vectors migrate "
                    "by the identity permutation"),
    }


def permutation_damage_report(perm: Sequence[int] = LEGACY_TO_CORE
                              ) -> Dict[str, object]:
    """What applying ``perm`` to engine-frame data would cost.

    ``LEGACY_TO_CORE`` is the bridge between the canonical code and a
    *different* equivalent code.  Applied to data that is already in the
    canonical frame it is not a repair but an injury, and this counts it:
    how many codewords stop being codewords.
    """
    canonical = set(GOLAY_SET)
    moved = [permute_mask(word, perm) for word in GOLAY_MASKS]
    escaped = [word for word in moved if word not in canonical]
    return {
        "permutation": list(perm),
        "codewords": len(GOLAY_MASKS),
        "codewords_leaving_the_code": len(escaped),
        "codewords_staying": len(GOLAY_MASKS) - len(escaped),
        "is_automorphism": not escaped,
        "safe_for_engine_frame_data": not escaped,
        "reading": ("applying this permutation to data already in the "
                    "canonical frame moves most words off the code, so it "
                    "must not be applied to the repository's stored "
                    "concept vectors"),
    }


# ===========================================================================
# 2.  BIT ORDER
# ===========================================================================

#: Coordinate *i* of a stored integer address sits at bit ``23 - i``.  As a
#: permutation of coordinates this is its own inverse.
BIT_REVERSAL: Tuple[int, ...] = tuple(DIM - 1 - i for i in range(DIM))


def reverse_bits(word: int) -> int:
    """Reverse the 24 bits of ``word``."""
    if not isinstance(word, int) or isinstance(word, bool):
        raise TypeError(f"reverse_bits: expected an int, got {type(word)}")
    if not 0 <= word < (1 << DIM):
        raise ValueError(f"reverse_bits: {word} is not a 24-bit word")
    out = 0
    for i in range(DIM):
        if (word >> i) & 1:
            out |= 1 << (DIM - 1 - i)
    return out


def address_to_mask(address: int) -> int:
    """A stored MSB-first hexcolour address as a package coordinate mask."""
    return reverse_bits(address)


def mask_to_address(mask: int) -> int:
    """A package coordinate mask written back as a stored address."""
    return reverse_bits(mask)


def address_audit(addresses: Sequence[int]) -> Dict[str, object]:
    """Decide the bit order of stored addresses from the addresses alone.

    ``compute_address`` snaps every address to a Golay codeword before
    storing it, so "is it a codeword?" is a test the data itself answers.
    Read MSB-first (reversed) they all are; read LSB-first none is.
    """
    canonical = set(GOLAY_SET)
    values = [int(a) for a in addresses]
    for value in values:
        if not 0 <= value < (1 << DIM):
            raise ValueError(f"address_audit: {value} is not a 24-bit word")
    as_is = sum(1 for a in values if a in canonical)
    reversed_ = sum(1 for a in values if reverse_bits(a) in canonical)
    return {
        "addresses": len(values),
        "codewords_read_lsb_first": as_is,
        "codewords_read_msb_first": reversed_,
        "bit_reversal_required": reversed_ > as_is,
        "all_codewords_after_reversal": (bool(values)
                                         and reversed_ == len(values)),
        "reading": ("the writer stored coordinate i at bit 23-i and snapped "
                    "to a codeword before writing, so reading an address "
                    "without reversing it lands off the code"),
    }


# ===========================================================================
# 3.  THE REPORT
# ===========================================================================

def frame_report(addresses: Sequence[int] = ()) -> Dict[str, object]:
    """Everything this module claims, recomputed."""
    return {
        "vectors": frame_audit(),
        "permutation_damage": permutation_damage_report(),
        "addresses": address_audit(addresses) if addresses else None,
        "bit_reversal": list(BIT_REVERSAL),
        "legacy_to_core": list(LEGACY_TO_CORE),
        "core_to_legacy": list(CORE_TO_LEGACY),
    }

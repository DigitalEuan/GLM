#!/usr/bin/env python3
"""Exact Golay/MOG/Leech-24 coordinate investigation.
The 4 x 6 grid in this module is an explicit *observer layout*: row-major bit
indices 0..23.  It is useful for displaying the extended binary Golay code,
but no claim is made that this coordinate order is Curtis's canonical printed
labelling.  A different MOG convention is represented by a 24-coordinate
permutation.
All Leech coordinates below are integral coordinates scaled globally by
1/sqrt(8).  Keeping the integer numerator makes squared norms exact: a
numerator with squared norm 32 has actual squared norm 4.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from itertools import combinations
from typing import Dict, Iterable, Iterator, List, Sequence, Tuple
from tgic_v3 import get_all_codewords, get_golay_engine, get_octads
ROWS = 4
COLUMNS = 6
LAYER_NAMES = ("Mirrors", "Information", "Activation", "Potential")
LAYER_MEANINGS = (

"colour fingerprint",

"position topology",

"spatial context",

"relational fingerprint",
)
@dataclass(frozen=True)
class CoordinateAddress:

    """A stable address for one of the 24 binary/Euclidean coordinates."""

    bit: int

    row: int

    column: int

    layer: str

    meaning: str
def address(bit: int) -> CoordinateAddress:

    """Convert bit 0..23 to the user's row-major 4 x 6 layer address."""

    if type(bit) is not int or not 0 <= bit < 24:

    raise ValueError("bit address must be an integer in 0..23")

    row, column = divmod(bit, COLUMNS)

    return CoordinateAddress(bit, row, column, LAYER_NAMES[row], LAYER_MEANINGS[row])
def bit_at(row: int, column: int) -> int:

    """Inverse of :func:`address` for a row and column."""

    if type(row) is not int or not 0 <= row < ROWS:

    raise ValueError("row must be an integer in 0..3")

    if type(column) is not int or not 0 <= column < COLUMNS:

    raise ValueError("column must be an integer in 0..5")

    return row * COLUMNS + column
    def _validate_bits(bits: Sequence[int]) -> Tuple[int, ...]:

    if len(bits) != 24 or any(type(x) is not int or x not in (0, 1) for x in bits):

    raise ValueError("a word must contain exactly 24 integer bits")

    return tuple(bits)
def grid(bits: Sequence[int]) -> Tuple[Tuple[int, ...], ...]:

    """Display a word through the explicit row-major 4 x 6 observer lens."""

    word = _validate_bits(bits)

    return tuple(tuple(word[r * 6:(r + 1) * 6]) for r in range(4))
def layer_values(bits: Sequence[int]) -> Dict[str, Tuple[int, ...]]:

    """Return the four named six-coordinate payloads without changing them."""

    rows = grid(bits)

    return {name: rows[r] for r, name in enumerate(LAYER_NAMES)}
def is_leech_numerator(point: Sequence[int]) -> bool:

    """Test the standard Golay congruence description of the Leech lattice.

    The represented point is ``point / sqrt(8)``.  Membership requires:

    all coordinates have one parity; coordinates congruent to 2 or 3 modulo 4

    form a Golay codeword; and ``sum(point) = 4*point[0] (mod 8)``.

    """

    if len(point) != 24 or any(type(x) is not int for x in point):

    return False

    if any((x - point[0]) % 2 for x in point):

    return False

    residue_word = [int(x % 4 in (2, 3)) for x in point]

    if not get_golay_engine().syndrome(residue_word) == [0] * 12:

    return False

    return (sum(point) - 4 * point[0]) % 8 == 0
def norm_sq_numerator(point: Sequence[int]) -> int:

    """Squared norm before the global 1/sqrt(8) scale."""

    if len(point) != 24 or any(type(x) is not int for x in point):

    raise ValueError("a Leech numerator must contain 24 integers")

    return sum(x * x for x in point)
def minimal_vectors() -> Iterator[Tuple[int, ...]]:

    """Generate all 196,560 minimal Leech vectors, with no floating point.

    The three standard numerator shapes are ``(±4,±4,0^22)``,

    ``(±2^8,0^16)`` on octads with an even number of minus signs, and

    ``(∓3,±1^23)`` whose sign pattern is a Golay codeword.

    """

# 276 supports times four sign choices = 1,104.

    for i, j in combinations(range(24), 2):

    for si in (-4, 4):

    for sj in (-4, 4):

    point = [0] * 24

    point[i], point[j] = si, sj

    yield tuple(point)

# 759 octads times 128 even sign patterns = 97,152.

    for octad in get_octads():

    support = [i for i, b in enumerate(octad) if b]

    for mask in range(256):

    if mask.bit_count() % 2:

    continue

    point = [0] * 24

    for k, i in enumerate(support):

    point[i] = -2 if (mask >> k) & 1 else 2

    yield tuple(point)

# 4,096 codewords times 24 distinguished coordinates = 98,304.

    for codeword in get_all_codewords():

    signs = [-1 if b else 1 for b in codeword]

    for distinguished in range(24):

    point = signs.copy()

    point[distinguished] = -3 * signs[distinguished]

    yield tuple(point)
def octad_incidence_report() -> Dict[str, object]:

    """Compute coordinate/pair incidence and layer-intersection statistics."""

    octads = get_octads()

    coordinate_counts = [0] * 24

    pair_counts: Counter[Tuple[int, int]] = Counter()

    layer_profiles: Counter[Tuple[int, int, int, int]] = Counter()

    for word in octads:

    support = [i for i, bit in enumerate(word) if bit]

    for i in support:

    coordinate_counts[i] += 1

    for pair in combinations(support, 2):

    pair_counts[pair] += 1

    layer_profiles[tuple(sum(word[r * 6:(r + 1) * 6]) for r in range(4))] += 1

    return {

    "octads": len(octads),

    "coordinate_incidence": coordinate_counts,

    "coordinate_incidence_values": dict(sorted(Counter(coordinate_counts).items())),

    "pair_incidence_values": dict(sorted(Counter(pair_counts.values()).items())),

    "layer_intersection_profiles": {

    "-".join(map(str, profile)): count

    for profile, count in sorted(layer_profiles.items())

    },

    }
def correction_report() -> Dict[str, object]:

    """Check every weight-at-most-three error around the zero codeword."""

    engine = get_golay_engine()

    counts: Dict[int, int] = {}

    failures: Dict[int, int] = {}

    zero = [0] * 24

    for weight in range(4):

    total = failed = 0

    for positions in combinations(range(24), weight):

    received = zero.copy()

    for i in positions:

    received[i] = 1

    corrected, metadata = engine.snap_to_codeword(received)

    total += 1

    failed += corrected != zero or not metadata["correctable"]

    counts[weight] = total

    failures[weight] = failed

    return {

    "tested_error_patterns_by_weight": counts,

    "failures_by_weight": failures,

    "reason_zero_word_suffices": "linearity makes every codeword translate the same error test",

    "guaranteed_unique_radius": 3,

    "covering_radius": 4,

    "distance_four_note": "the 1,771 deep-hole cosets each have six nearest codewords",

    }
def build_report(check_all_minimal_vectors: bool = True) -> Dict[str, object]:

    """Build the reproducible investigation report."""

    octads = octad_incidence_report()

    minimal_count = membership_failures = wrong_norm = duplicate_count = 0

    seen = set()

    type_counts = Counter()

    if check_all_minimal_vectors:

    for point in minimal_vectors():

    minimal_count += 1

    seen.add(point)

    membership_failures += not is_leech_numerator(point)

    wrong_norm += norm_sq_numerator(point) != 32

    zeros = point.count(0)

    type_counts[{22: "pair_4", 16: "octad_2", 0: "odd_3_1"}[zeros]] += 1

    duplicate_count = minimal_count - len(seen)

    return {

    "coordinate_system": {

    "grid": "4 rows x 6 columns, row-major",

    "addresses": [asdict(address(i)) for i in range(24)],

    "warning": (

    "This is an explicit coordinate lens. Calling it a canonical Curtis MOG requires "

    "publishing and validating the coordinate permutation/hexacode convention."

    ),

    },

    "golay": {

    "parameters": "extended binary Golay [24,12,8]",

    "codewords": len(get_all_codewords()),

    "weight_distribution": dict(sorted(Counter(map(sum, get_all_codewords())).items())),

    "error_correction": correction_report(),

    "octad_design": octads,

    },

    "leech": {

    "scale": "integer numerator divided by sqrt(8)",

    "minimal_vector_count": minimal_count if check_all_minimal_vectors else None,

    "minimal_type_counts": dict(type_counts),

    "distinct_minimal_vectors": len(seen) if check_all_minimal_vectors else None,

    "duplicate_count": duplicate_count if check_all_minimal_vectors else None,

    "membership_failures": membership_failures if check_all_minimal_vectors else None,

    "wrong_numerator_norm_count": wrong_norm if check_all_minimal_vectors else None,

    "minimal_numerator_norm_sq": 32,

    "minimal_actual_norm_sq": 4,

    },

    "interpretation": {

    "bit_address": "one coordinate slot shared by binary words and 24D Euclidean vectors",

    "not_a_lattice_point": "an isolated bit or unit coordinate vector is not itself a Leech point",

    "intrinsic_local_structure": (

    "each coordinate lies in 253 Golay octads; each coordinate pair lies in 77 octads"

    ),

    "payload_layers": (

    "the four six-bit meanings are application metadata; Golay parity checks couple all layers"

    ),

    },

    }
def run_self_tests() -> Dict[str, object]:

    for i in range(24):

    a = address(i)

    assert bit_at(a.row, a.column) == i

    alternating = tuple(i % 2 for i in range(24))

    assert grid(alternating) == tuple(tuple(alternating[6 * r:6 * r + 6]) for r in range(4))

    report = build_report(check_all_minimal_vectors=True)

    assert report["golay"]["weight_distribution"] == {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1}

    design = report["golay"]["octad_design"]

    assert design["coordinate_incidence_values"] == {253: 24}

    assert design["pair_incidence_values"] == {77: 276}

    assert report["golay"]["error_correction"]["failures_by_weight"] == {0: 0, 1: 0, 2: 0, 3: 0}

    leech = report["leech"]

    assert leech["minimal_type_counts"] == {"pair_4": 1104, "octad_2": 97152, "odd_3_1": 98304}

    assert leech["minimal_vector_count"] == leech["distinct_minimal_vectors"] == 196560

    assert leech["membership_failures"] == leech["wrong_numerator_norm_count"] == 0

    return report
def main() -> None:

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument("--self-test", action="store_true", help="run all exact finite checks")

    parser.add_argument("--json", metavar="PATH", help="write the report as JSON")

    args = parser.parse_args()

    report = run_self_tests() if args.self_test else build_report()

    if args.json:

    with open(args.json, "w", encoding="utf-8") as handle:

    json.dump(report, handle, indent=2, sort_keys=True)

    handle.write("\n")

    print(json.dumps(report, indent=2, sort_keys=True))
    if __name__ == "__main__":

    main()
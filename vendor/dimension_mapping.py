#!/usr/bin/env python3
"""Reproducible dimension map for the extended binary Golay code.

"Dimension" here means the number of retained binary coordinates.  Every lens
is an explicitly named map; no output is presented as a physical measurement.
Physical words may be useful analogies, but the computed objects are finite
coding-theory and Boolean-algebra quantities.

The exhaustive parts cover all 4096 codewords, all 4096 syndrome classes, and
all ordered pairs in each prefix image.  Coordinate-subset sampling is kept
separate because there are C(24,n) possible lenses at dimension n.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict
from fractions import Fraction
from itertools import combinations
from math import comb
from typing import Dict, Iterable, List, Sequence, Tuple

from dimension_projection import (
    DEFAULT_DIMENSIONS,
    analyze_prefix_ladder,
    coordinate_subset_sensitivity,
)
from tgic_v3 import get_all_codewords, get_golay_engine


def _mask(bits: Sequence[int]) -> int:
    return sum(bit << i for i, bit in enumerate(bits))


def boolean_closure(image: Iterable[int]) -> Dict[str, object]:
    """Exhaustively count ordered-pair closure under AND, OR, and XOR."""
    values = tuple(sorted(image))
    members = set(values)
    counts = {"and": 0, "or": 0, "xor": 0}
    intersection_weights: Counter[int] = Counter()
    for a in values:
        for b in values:
            avb, aob, axb = a & b, a | b, a ^ b
            counts["and"] += avb in members
            counts["or"] += aob in members
            counts["xor"] += axb in members
            intersection_weights[avb.bit_count()] += 1
    total = len(values) ** 2
    return {
        "ordered_pairs": total,
        "closed_pairs": counts,
        "closure_rates": {name: count / total for name, count in counts.items()},
        "and_result_weight_distribution": dict(sorted(intersection_weights.items())),
    }


def exact_boolean_map(dimensions: Sequence[int] = DEFAULT_DIMENSIONS) -> Dict[str, object]:
    """Exhaustive Boolean-operation map for each prefix projection."""
    codewords = get_all_codewords()
    rows = []
    for n in dimensions:
        image = {_mask(word[:n]) for word in codewords}
        rows.append({"dimension": n, "image_size": len(image), **boolean_closure(image)})
    return {"pair_convention": "all ordered pairs, including equal pairs", "rows": rows}


def _syndrome_columns() -> Tuple[int, ...]:
    engine = get_golay_engine()
    return tuple(_mask(column) for column in engine._H_cols)


def exact_coset_map() -> Dict[str, object]:
    """Map exact nearest-codeword and deterministic descent data by syndrome.

    Two vectors with the same syndrome differ by a codeword, so nearest-codeword
    distance and the syndrome-weight descent trajectory depend only on one of
    the 4096 syndromes.  This is exhaustive over all 2^24 vectors by cosets.
    """
    columns = _syndrome_columns()

    # Count all minimum-weight error patterns through covering radius four.
    error_counts: List[Counter[int]] = [Counter() for _ in range(5)]
    error_counts[0][0] = 1
    for weight in range(1, 5):
        for positions in combinations(range(24), weight):
            syndrome = 0
            for position in positions:
                syndrome ^= columns[position]
            error_counts[weight][syndrome] += 1

    nearest_distance: Counter[int] = Counter()
    nearest_multiplicity: Counter[int] = Counter()
    missing = []
    for syndrome in range(1 << 12):
        found = False
        for weight, counts in enumerate(error_counts):
            if counts[syndrome]:
                nearest_distance[weight] += 1
                nearest_multiplicity[counts[syndrome]] += 1
                found = True
                break
        if not found:
            missing.append(syndrome)
    if missing:
        raise AssertionError("covering-radius enumeration left syndrome classes unmapped")

    # Greedy rule: among one-bit flips giving the lowest syndrome weight, use
    # the lowest coordinate index.  Require a strict decrease.
    step_distribution: Counter[int] = Counter()
    final_distribution: Counter[int] = Counter()
    for initial in range(1 << 12):
        syndrome = initial
        steps = 0
        while syndrome:
            current_weight = syndrome.bit_count()
            candidates = [
                ((syndrome ^ column).bit_count(), index, syndrome ^ column)
                for index, column in enumerate(columns)
            ]
            next_weight, _, next_syndrome = min(candidates)
            if next_weight >= current_weight:
                break
            syndrome = next_syndrome
            steps += 1
        step_distribution[steps] += 1
        final_distribution[syndrome] += 1

    reached = final_distribution.get(0, 0)
    total_steps = sum(steps * count for steps, count in step_distribution.items())
    return {
        "scope": "all 4096 cosets; therefore all 2^24 vectors modulo codeword translation",
        "nearest_codeword_distance_by_coset": dict(sorted(nearest_distance.items())),
        "nearest_codeword_multiplicity_by_coset": dict(sorted(nearest_multiplicity.items())),
        "covering_radius": max(nearest_distance),
        "greedy_rule": "strictly lower syndrome weight; tie-break by lowest coordinate index",
        "greedy_steps_by_coset": dict(sorted(step_distribution.items())),
        "greedy_reached_code_cosets": reached,
        "greedy_stuck_nonzero_cosets": (1 << 12) - reached,
        "greedy_max_steps": max(step_distribution),
        "greedy_mean_steps": float(Fraction(total_steps, 1 << 12)),
        "greedy_mean_steps_exact": str(Fraction(total_steps, 1 << 12)),
    }


def quadrant_map() -> Dict[str, object]:
    """Compare the fixed 3x8 block lens with its exact ambient-cube null."""
    labels = tuple(a + b + c for a in "LH" for b in "LH" for c in "LH")
    observed: Counter[str] = Counter()
    for word in get_all_codewords():
        blocks = [sum(word[start:start + 8]) for start in (0, 8, 16)]
        observed["".join("H" if value >= 4 else "L" for value in blocks)] += 1

    high_count = sum(comb(8, k) for k in range(4, 9))  # 163
    low_count = (1 << 8) - high_count                  # 93
    # Exact counts among all 2^24 ambient words, avoiding any random control.
    ambient = {
        label: high_count ** label.count("H") * low_count ** label.count("L")
        for label in labels
    }
    expected = {label: Fraction(4096 * count, 1 << 24) for label, count in ambient.items()}
    chi_square = sum(
        Fraction((observed[label] * expected[label].denominator - expected[label].numerator) ** 2,
                 expected[label].numerator * expected[label].denominator)
        for label in labels
    )
    return {
        "lens": "ordered blocks [0,8), [8,16), [16,24); H means block weight >= 4",
        "high_block_probability": "163/256",
        "low_block_probability": "93/256",
        "codeword_counts": dict(sorted(observed.items())),
        "ambient_cube_counts": dict(sorted(ambient.items())),
        "expected_codeword_counts_under_ambient_null": {
            label: str(expected[label]) for label in labels
        },
        "pearson_chi_square_exact": str(chi_square),
        "pearson_chi_square": float(chi_square),
        "interpretation": (
            "This measures departure from the exact ambient distribution for one fixed "
            "block lens. It is not evidence of spontaneous physical symmetry breaking."
        ),
    }


def symmetry_map() -> Dict[str, object]:
    """State and check concrete symmetries rather than using an undefined label."""
    codewords = get_all_codewords()
    members = {tuple(word) for word in codewords}

    def preserves(permutation: Sequence[int]) -> bool:
        return all(tuple(word[permutation[i]] for i in range(24)) in members for word in codewords)

    identity = tuple(range(24))
    half_swap = tuple(range(12, 24)) + tuple(range(12))
    coordinate_swap_0_1 = list(identity)
    coordinate_swap_0_1[0], coordinate_swap_0_1[1] = 1, 0
    return {
        "ambient_symmetry": "all coordinate permutations preserve Hamming distance on GF(2)^24",
        "code_symmetry": "a coordinate permutation is a code symmetry iff it maps all codewords to codewords",
        "observer_lens_symmetry": (
            "a displayed statistic retains only those code symmetries that also preserve its selected "
            "coordinates, ordering, blocks, thresholds, and any rendering transform"
        ),
        "checked_permutations": {
            "identity": preserves(identity),
            "swap_systematic_and_parity_halves": preserves(half_swap),
            "swap_coordinates_0_and_1": preserves(coordinate_swap_0_1),
        },
        "rendering_note": (
            "Orthographic and perspective rendering alter a visual presentation, not the binary code. "
            "If used analytically, the camera/projection matrix must be published as part of the lens."
        ),
    }


def build_map(subset_samples: int = 20, seed: int = 0xD1A) -> Dict[str, object]:
    prefixes = [asdict(report) for report in analyze_prefix_ladder()]
    sensitivities = [
        coordinate_subset_sensitivity(n, subset_samples, seed + n)
        for n in (8, 10, 12, 14, 16)
    ]
    return {
        "stance": (
            "A finite mathematical model is being explored. Model quantities are not asserted to be "
            "physical mass, energy, gravity, or reality itself."
        ),
        "terminology": {
            "dimension": "number of retained coordinates (ambient dimension)",
            "rank": "binary linear dimension of the projected image",
            "lens": "the fully specified coordinate selection or later display transform",
        },
        "prefix_projections": prefixes,
        "boolean_operations": exact_boolean_map(),
        "cosets_and_descent": exact_coset_map(),
        "fixed_block_observer": quadrant_map(),
        "symmetry": symmetry_map(),
        "coordinate_subset_sensitivity": sensitivities,
        "scope_notes": {
            "exhaustive": "codewords, prefix-image ordered pairs, and syndrome cosets",
            "sampled": (
                "coordinate-subset sensitivity only; each selected subset is measured exactly and "
                "the seed and coordinates are recorded"
            ),
        },
    }


def run_self_tests() -> Dict[str, object]:
    result = build_map(subset_samples=2)
    cosets = result["cosets_and_descent"]
    assert cosets["nearest_codeword_distance_by_coset"] == {0: 1, 1: 24, 2: 276, 3: 2024, 4: 1771}
    assert cosets["nearest_codeword_multiplicity_by_coset"] == {1: 2325, 6: 1771}
    assert cosets["greedy_reached_code_cosets"] == 4096
    assert cosets["greedy_max_steps"] == 6
    rows = result["boolean_operations"]["rows"]
    assert all(row["closure_rates"]["xor"] == 1.0 for row in rows)
    assert rows[-1]["closed_pairs"]["and"] == 115648
    assert result["symmetry"]["checked_permutations"] == {
        "identity": True,
        "swap_systematic_and_parity_halves": True,
        "swap_coordinates_0_and_1": False,
    }
    return {"status": "ok", "cosets": 4096, "prefix_dimensions": len(rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="dimension_mapping_results.json")
    parser.add_argument("--subset-samples", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0xD1A)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.subset_samples < 1:
        parser.error("--subset-samples must be positive")
    if args.self_test:
        print("self-tests:", run_self_tests())
    result = build_map(args.subset_samples, args.seed)
    with open(args.json, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print("wrote", args.json)
    print("nearest distances:", result["cosets_and_descent"]["nearest_codeword_distance_by_coset"])
    print("greedy steps:", result["cosets_and_descent"]["greedy_steps_by_coset"])


if __name__ == "__main__":
    main()

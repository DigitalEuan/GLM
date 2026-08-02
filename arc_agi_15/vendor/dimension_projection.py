#!/usr/bin/env python3
"""Exact audit tools for coordinate projections of the extended binary Golay code.

A projection onto coordinates ``S`` is the puncturing map

    pi_S : GF(2)^24 -> GF(2)^|S|,   x |-> (x_i)_(i in S).

This module measures the finite combinatorics of that map.  It deliberately
avoids physical terminology: a discontinuity in a derived statistic is not, by
itself, evidence of a physical phase transition.

The default ladder uses the first n coordinates, matching the historical
study.  Results for n <= 12 are especially easy to misread: when the projection
has rank n, its image is the entire n-cube, so its AND-closure is exactly 1 for
the tautological reason that the image contains every n-bit vector.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass
from math import comb
from itertools import combinations
from typing import Dict, Iterable, List, Sequence, Tuple

from tgic_v3 import get_all_codewords

N_COORDINATES = 24
DEFAULT_DIMENSIONS = tuple(range(4, 25, 2))


def _validate_coordinates(coordinates: Sequence[int]) -> Tuple[int, ...]:
    if not coordinates:
        raise ValueError("coordinates must be non-empty")
    if any(type(i) is not int for i in coordinates):
        raise TypeError("coordinates must contain integers")
    result = tuple(coordinates)
    if len(set(result)) != len(result):
        raise ValueError("coordinates must be distinct")
    if any(i < 0 or i >= N_COORDINATES for i in result):
        raise ValueError("coordinates must lie in [0, 23]")
    return result


def bits_to_mask(bits: Sequence[int]) -> int:
    """Pack a binary sequence into a non-negative integer."""
    mask = 0
    for i, bit in enumerate(bits):
        if type(bit) is not int or bit not in (0, 1):
            raise ValueError("bits must contain only integer 0 or 1")
        mask |= bit << i
    return mask


def project_mask(word: Sequence[int], coordinates: Sequence[int]) -> int:
    """Project one 24-bit word onto an ordered coordinate list."""
    coords = _validate_coordinates(coordinates)
    if len(word) != N_COORDINATES:
        raise ValueError("word must have length 24")
    return bits_to_mask([word[i] for i in coords])


def projected_image(codewords: Iterable[Sequence[int]], coordinates: Sequence[int]) -> frozenset[int]:
    """Return the distinct projected words as packed integers."""
    coords = _validate_coordinates(coordinates)
    return frozenset(project_mask(word, coords) for word in codewords)


def gf2_rank(values: Iterable[int]) -> int:
    """Rank of packed binary row vectors, by deterministic GF(2) elimination."""
    basis: Dict[int, int] = {}
    for value in values:
        x = value
        while x:
            pivot = x.bit_length() - 1
            if pivot in basis:
                x ^= basis[pivot]
            else:
                basis[pivot] = x
                break
    return len(basis)


def minimum_nonzero_weight(image: Iterable[int]) -> int | None:
    """Minimum Hamming weight among nonzero image vectors; None for {0}."""
    weights = [x.bit_count() for x in image if x]
    return min(weights) if weights else None


def weight_distribution(image: Iterable[int]) -> Dict[int, int]:
    distribution: Dict[int, int] = {}
    for x in image:
        weight = x.bit_count()
        distribution[weight] = distribution.get(weight, 0) + 1
    return dict(sorted(distribution.items()))


def exact_and_closure(image: Iterable[int]) -> Tuple[int, int]:
    """Count ordered pairs (a,b) whose bitwise AND remains in the image.

    Ordered pairs, including a=b, make the denominator exactly |image|^2 and
    avoid sampling noise.  This convention is stated explicitly because the
    older study sampled unordered distinct pairs, producing unstable values.
    """
    values = tuple(sorted(image))
    members = set(values)
    closed = sum(1 for a in values for b in values if (a & b) in members)
    return closed, len(values) ** 2


@dataclass(frozen=True)
class ProjectionReport:
    coordinates: Tuple[int, ...]
    ambient_dimension: int
    image_size: int
    rank: int
    kernel_dimension: int
    fiber_size: int
    is_surjective: bool
    minimum_distance: int | None
    and_closed_pairs: int
    and_total_pairs: int
    and_closure_rate: float
    weight_distribution: Dict[int, int]


def analyze_projection(
    codewords: Sequence[Sequence[int]], coordinates: Sequence[int]
) -> ProjectionReport:
    """Compute exact invariants for one coordinate projection."""
    coords = _validate_coordinates(coordinates)
    image = projected_image(codewords, coords)
    rank = gf2_rank(image)
    if len(image) != 1 << rank:
        raise AssertionError("projected image was expected to be a binary linear space")
    if len(codewords) % len(image):
        raise AssertionError("fibers of a linear projection must have equal size")
    closed, total = exact_and_closure(image)
    return ProjectionReport(
        coordinates=coords,
        ambient_dimension=len(coords),
        image_size=len(image),
        rank=rank,
        kernel_dimension=12 - rank,
        fiber_size=len(codewords) // len(image),
        is_surjective=len(image) == 1 << len(coords),
        minimum_distance=minimum_nonzero_weight(image),
        and_closed_pairs=closed,
        and_total_pairs=total,
        and_closure_rate=closed / total,
        weight_distribution=weight_distribution(image),
    )


def analyze_prefix_ladder(
    dimensions: Sequence[int] = DEFAULT_DIMENSIONS,
) -> List[ProjectionReport]:
    """Analyze projections onto coordinates [0,n), exactly and reproducibly."""
    codewords = get_all_codewords()
    if any(type(n) is not int or n < 1 or n > N_COORDINATES for n in dimensions):
        raise ValueError("dimensions must be integers in [1, 24]")
    return [analyze_projection(codewords, tuple(range(n))) for n in dimensions]


def coordinate_subset_sensitivity(
    dimension: int, samples: int = 12, seed: int = 0xD1A,
) -> Dict[str, object]:
    """Compare deterministic random coordinate subsets at one dimension.

    These are exact measurements for each selected subset, not a claim about
    the distribution over all coordinate subsets.
    """
    if type(dimension) is not int or not 1 <= dimension <= N_COORDINATES:
        raise ValueError("dimension must lie in [1, 24]")
    if type(samples) is not int or samples < 1:
        raise ValueError("samples must be positive")
    subset_count = comb(N_COORDINATES, dimension)
    rng = random.Random(seed)
    if samples >= subset_count:
        selected = list(combinations(range(N_COORDINATES), dimension))
    else:
        # Rejection sampling avoids materializing as many as C(24, 12) tuples.
        chosen = set()
        while len(chosen) < samples:
            chosen.add(tuple(sorted(rng.sample(range(N_COORDINATES), dimension))))
        selected = sorted(chosen)
    reports = [analyze_projection(get_all_codewords(), subset) for subset in selected]
    rates = [report.and_closure_rate for report in reports]
    ranks = [report.rank for report in reports]
    return {
        "dimension": dimension,
        "sample_count": len(reports),
        "seed": seed,
        "all_subsets_enumerated": len(selected) == subset_count,
        "rank_values": sorted(set(ranks)),
        "and_closure_min": min(rates),
        "and_closure_max": max(rates),
        "reports": [asdict(report) for report in reports],
    }


def run_self_tests() -> Dict[str, object]:
    codewords = get_all_codewords()
    assert len(codewords) == 4096

    full = analyze_projection(codewords, tuple(range(24)))
    assert full.image_size == 4096
    assert full.rank == 12 and full.kernel_dimension == 0 and full.fiber_size == 1
    assert full.minimum_distance == 8

    # For every prefix through dimension 12, rank=n implies image=GF(2)^n.
    small = [analyze_projection(codewords, tuple(range(n))) for n in range(1, 13)]
    assert all(r.rank == r.ambient_dimension for r in small)
    assert all(r.is_surjective and r.and_closure_rate == 1.0 for r in small)

    # Projection commutes with XOR and cannot increase Hamming weight.
    coords = (0, 3, 7, 11, 18)
    for a, b in zip(codewords[:32], codewords[32:64]):
        pa = project_mask(a, coords)
        pb = project_mask(b, coords)
        px = project_mask([x ^ y for x, y in zip(a, b)], coords)
        assert px == pa ^ pb
        assert pa.bit_count() <= sum(a)

    # Known extended Golay distribution and validation checks.
    assert full.weight_distribution == {0: 1, 8: 759, 12: 2576, 16: 759, 24: 1}
    for bad in ((), (0, 0), (-1,), (24,)):
        try:
            analyze_projection(codewords, bad)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError(f"invalid coordinates accepted: {bad}")

    return {
        "codewords": len(codewords),
        "full_rank": full.rank,
        "full_minimum_distance": full.minimum_distance,
        "surjective_prefixes": [r.ambient_dimension for r in small],
    }


def _jsonable_report(report: ProjectionReport) -> Dict[str, object]:
    data = asdict(report)
    data["coordinates"] = list(report.coordinates)
    data["weight_distribution"] = {
        str(k): v for k, v in report.weight_distribution.items()
    }
    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", metavar="PATH", help="write the exact prefix ladder to JSON")
    parser.add_argument("--self-test", action="store_true", help="run deterministic assertions")
    args = parser.parse_args()

    if args.self_test:
        print("self-tests:", run_self_tests())

    reports = analyze_prefix_ladder()
    print(" n  rank  |image|  fiber  surjective  d_min  exact AND closure")
    print("--  ----  -------  -----  ----------  -----  -----------------")
    for r in reports:
        d_min = "-" if r.minimum_distance is None else str(r.minimum_distance)
        print(
            f"{r.ambient_dimension:2d}  {r.rank:4d}  {r.image_size:7d}  "
            f"{r.fiber_size:5d}  {str(r.is_surjective):>10}  {d_min:>5}  "
            f"{r.and_closure_rate:.9f}"
        )

    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump({"prefix_projections": [_jsonable_report(r) for r in reports]}, handle, indent=2)
            handle.write("\n")
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()

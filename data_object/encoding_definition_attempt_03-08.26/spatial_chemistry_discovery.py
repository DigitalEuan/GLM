#!/usr/bin/env python3
"""Third-round search for spatial, pairwise, and discrete-time chemical signal.

This is an empirical representation test, not a simulation of chemistry.  It
uses broad, independently recorded element labels as immediate verification
endpoints and keeps every data-derived layout selection inside the training
portion of a leave-elements-out split.
"""
from __future__ import annotations

import csv
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import golay_mog_experiments as base
from spatial_arithmetic import circumradius, node_count

ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results/spatial_discovery.json"
PAIR_CSV = ROOT / "results/spatial_pair_metrics.csv"
SEED = 20260802
RANDOM_LAYOUTS = 128


def rows() -> list[dict[str, str]]:
    base.read_and_normalize()
    with base.PROCESSED.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def orderings(table: list[dict[str, str]]) -> dict[str, list[int]]:
    """Predeclared subject traversals; group order is an explicit positive control."""
    atomic = list(range(1, 119))
    lookup = {int(row["AtomicNumber"]): row for row in table}
    return {
        "atomic_number": atomic,
        "period_then_group": sorted(atomic, key=lambda z: (base.period_of(z), base.group_of(z), z)),
        "group_then_period_positive_control": sorted(atomic, key=lambda z: (base.group_of(z), base.period_of(z), z)),
        "electron_configuration_lexical": sorted(atomic, key=lambda z: (lookup[z]["ElectronConfiguration"], z)),
        "seeded_random_negative_control": random.Random(SEED).sample(atomic, len(atomic)),
    }


def transition_audit(sequence: list[int]) -> dict[str, object]:
    """Measure one tick as a transition between adjacent subjects in a traversal."""
    gray_words = [base.gray12(rank) for rank in range(1, 119)]
    codewords = [base.golay_encode(word) for word in gray_words]
    message_delta = [sum(a != b for a, b in zip(gray_words[i], gray_words[i + 1])) for i in range(117)]
    golay_delta = [sum(a != b for a, b in zip(codewords[i], codewords[i + 1])) for i in range(117)]
    flip_counts = [0] * 12
    for left, right in zip(gray_words, gray_words[1:]):
        for bit, (a, b) in enumerate(zip(left, right)):
            flip_counts[bit] += a != b
    probabilities = [count / 117 for count in flip_counts if count]
    entropy = -sum(p * math.log2(p) for p in probabilities)
    consecutive = list(zip(sequence, sequence[1:]))
    return {
        "ticks": 117,
        "message_hamming_distribution": dict(sorted(Counter(message_delta).items())),
        "golay_burst_distribution": dict(sorted(Counter(golay_delta).items())),
        "message_bit_flip_counts": flip_counts,
        "flip_bit_entropy_bits": entropy,
        "adjacent_same_group_fraction": statistics.fmean(base.group_of(a) == base.group_of(b) for a, b in consecutive),
        "adjacent_same_period_fraction": statistics.fmean(base.period_of(a) == base.period_of(b) for a, b in consecutive),
    }


def blast_audit() -> dict[str, object]:
    """Exact change caused by toggling each systematic message coordinate.

    Golay encoding is linear, so these masks are independent of the starting
    element.  The source row is the MOG row containing that message coordinate.
    """
    zero = base.golay_encode([0] * 12)
    inverse = {coordinate: cell for cell, coordinate in enumerate(base.MOG_GRID_BITS)}
    records = []
    by_row: dict[int, list[int]] = defaultdict(list)
    for bit in range(12):
        message = [0] * 12
        message[bit] = 1
        delta = [a ^ b for a, b in zip(zero, base.golay_encode(message))]
        grid = base.mog_bits(delta)
        source_row = inverse[bit] // 6
        radius = sum(delta)
        by_row[source_row].append(radius)
        records.append({
            "message_bit": bit,
            "source_mog_cell": inverse[bit],
            "source_mog_row": source_row,
            "total_changed_code_bits": radius,
            "changed_bits_by_destination_row": [sum(grid[6*r:6*r+6]) for r in range(4)],
        })
    return {
        "definition": "Hamming support of the re-encoded Golay codeword after one message-bit toggle",
        "per_message_bit": records,
        "source_row_radius_multisets": {str(row): sorted(values) for row, values in sorted(by_row.items())},
        "warning": "This convention does not reproduce a 7-11/7/1/1 row rule. A direct toggle of a stored codeword cell changes one bit; a message toggle followed by re-encoding changes 8 or 12. The claimed rule therefore needs its exact update operation and MOG convention specified before it can be tested as the same quantity.",
    }


def random_layouts() -> list[tuple[int, ...]]:
    rng = random.Random(SEED + 31)
    layouts = [tuple(base.MOG_GRID_BITS)]
    for _ in range(RANDOM_LAYOUTS):
        permutation = list(range(24))
        rng.shuffle(permutation)
        layouts.append(tuple(permutation))
    return layouts


def vector(z: int, kind: str, permutation: tuple[int, ...] | None = None) -> list[float]:
    message = base.gray12(z)
    codeword = base.golay_encode(message)
    if kind == "atomic_number":
        return [z / 118.0]
    if kind == "gray_message":
        return [float(x) for x in message]
    if kind == "golay_hamming":
        return [float(x) for x in codeword]
    if kind == "spatial_arithmetic":
        count = node_count(z)
        return [count / node_count(118), circumradius(count) / circumradius(node_count(118))]
    if kind == "mog_geometry":
        assert permutation is not None
        grid = base.mog_bits(codeword, permutation)
        return base.geometry_features(grid, "stacked")
    raise ValueError(kind)


def standardized_vectors(zs: list[int], kind: str, permutation: tuple[int, ...] | None = None) -> dict[int, list[float]]:
    raw = {z: vector(z, kind, permutation) for z in zs}
    width = len(next(iter(raw.values())))
    means = [statistics.fmean(raw[z][j] for z in zs) for j in range(width)]
    scales = [max(statistics.pstdev(raw[z][j] for z in zs), 1e-9) for j in range(width)]
    return {z: [(value - means[j]) / scales[j] for j, value in enumerate(raw[z])] for z in zs}


def pair_scores(zs: list[int], kind: str, permutation: tuple[int, ...] | None = None) -> dict[tuple[int, int], float]:
    vectors = standardized_vectors(zs, kind, permutation)
    return {(a, b): -math.dist(vectors[a], vectors[b]) for index, a in enumerate(zs) for b in zs[index + 1:]}


def auc(labels: list[bool], scores: list[float]) -> float:
    """ROC AUC with half credit for ties, via average ranks."""
    ordered = sorted(zip(scores, labels), key=lambda item: item[0])
    positive_count = sum(labels)
    negative_count = len(labels) - positive_count
    if not positive_count or not negative_count:
        raise ValueError("AUC requires both classes")
    positive_rank_sum = 0.0
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end][0] == ordered[start][0]:
            end += 1
        average_rank = ((start + 1) + end) / 2
        positive_rank_sum += average_rank * sum(label for _, label in ordered[start:end])
        start = end
    wins = positive_rank_sum - positive_count * (positive_count + 1) / 2
    return wins / (positive_count * negative_count)


def relation_auc(zs: list[int], labels: dict[int, str], kind: str,
                 permutation: tuple[int, ...] | None = None) -> float:
    scores = pair_scores(zs, kind, permutation)
    pairs = list(scores)
    return auc([labels[a] == labels[b] for a, b in pairs], [scores[pair] for pair in pairs])


def pair_experiment(table: list[dict[str, str]]) -> list[dict[str, object]]:
    """Nested layout selection: select only on training elements, score test-test pairs."""
    zs = list(range(1, 119))
    layouts = random_layouts()
    relations = {
        "same_group_block": {int(row["AtomicNumber"]): row["GroupBlock"] for row in table},
        "same_standard_state": {int(row["AtomicNumber"]): row["StandardState"] for row in table},
    }
    output: list[dict[str, object]] = []
    for relation, labels in relations.items():
        for fold in range(5):
            test = [z for z in zs if z % 5 == fold]
            train = [z for z in zs if z % 5 != fold]
            train_layout_auc = [relation_auc(train, labels, "mog_geometry", layout) for layout in layouts]
            best_index = max(range(len(layouts)), key=train_layout_auc.__getitem__)
            configs: list[tuple[str, str, tuple[int, ...] | None]] = [
                ("atomic_number", "atomic_number", None),
                ("gray_message", "gray_message", None),
                ("golay_hamming", "golay_hamming", None),
                ("spatial_arithmetic", "spatial_arithmetic", None),
                ("fixed_mog_geometry", "mog_geometry", layouts[0]),
                ("training_selected_mog_geometry", "mog_geometry", layouts[best_index]),
            ]
            for name, kind, layout in configs:
                output.append({
                    "relation": relation,
                    "fold": fold,
                    "test_elements": len(test),
                    "configuration": name,
                    "test_auc": relation_auc(test, labels, kind, layout),
                    "selected_layout_index": best_index if name.startswith("training_selected") else "",
                    "selected_train_auc": train_layout_auc[best_index] if name.startswith("training_selected") else "",
                })
    return output


def summarize_pair(records: list[dict[str, object]]) -> dict[str, dict[str, float]]:
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for record in records:
        grouped[(str(record["relation"]), str(record["configuration"]))].append(float(record["test_auc"]))
    return {
        relation: {
            config: statistics.fmean(values)
            for (rel, config), values in grouped.items() if rel == relation
        }
        for relation in sorted({key[0] for key in grouped})
    }


def run() -> dict[str, object]:
    table = rows()
    temporal = {name: transition_audit(sequence) for name, sequence in orderings(table).items()}
    pair_records = pair_experiment(table)
    PAIR_CSV.parent.mkdir(exist_ok=True)
    with PAIR_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pair_records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(pair_records)
    result = {
        "schema_version": 1,
        "seed": SEED,
        "random_layout_candidates_per_fold_including_fixed": RANDOM_LAYOUTS + 1,
        "clock_definition": "one discrete tick is one transition between adjacent subjects in a declared traversal; no physical time unit is inferred",
        "blast": blast_audit(),
        "temporal_orderings": temporal,
        "pairwise_heldout_auc": summarize_pair(pair_records),
        "interpretation": "AUC 0.5 is chance and 1.0 is perfect ranking. Endpoints are broad similarity relations, not bond energies, reaction outcomes, or causal interactions. A selected layout has evidence of reusable signal only if its held-out AUC consistently exceeds both ordinary baselines and the fixed/random-layout controls.",
    }
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

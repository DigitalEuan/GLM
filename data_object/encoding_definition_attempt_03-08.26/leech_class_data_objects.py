#!/usr/bin/env python3
"""Leech-class Data Object v3 and leakage-controlled relationship experiment.

The three classical shape families are enumerated exactly in the integer model
(where Euclidean coordinates are divided by sqrt(8)).  Element measurements
remain typed and lossless; Leech vectors are addresses, not compressed values.
The empirical section asks whether superposing measured numeric channels at
fixed addresses improves held-out element relationships over the same raw data
or over random address assignments.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import statistics
from collections import Counter
from pathlib import Path

import golay_mog_experiments as base
import gray_leech_data_objects as v2
from spatial_chemistry_discovery import auc

ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT / "schemas/element_data_object_v3.json"
OBJECTS = ROOT / "data/objects/elements_v3.jsonl"
AUDIT = ROOT / "results/leech_class_audit.json"
METRICS = ROOT / "results/leech_class_relationships.csv"
REPORT_DATA = ROOT / "results/leech_class_relationships.json"
SEED = 20260802

NUMERIC_FEATURES = (
    "AtomicMass", "Electronegativity", "AtomicRadius", "IonizationEnergy",
    "ElectronAffinity", "MeltingPoint", "BoilingPoint", "Density",
)
ALL_CHANNELS = tuple(v2.CHANNEL_CELLS)


def golay_words() -> list[list[int]]:
    return [base.golay_encode([(message >> bit) & 1 for bit in range(12)])
            for message in range(4096)]


def class_a_vectors() -> list[tuple[int, ...]]:
    """All (±4, ±4, 0^22) vectors."""
    out = []
    for i in range(24):
        for j in range(i + 1, 24):
            for si in (-4, 4):
                for sj in (-4, 4):
                    vector = [0] * 24
                    vector[i], vector[j] = si, sj
                    out.append(tuple(vector))
    return out


def class_b_vectors(words: list[list[int]] | None = None) -> list[tuple[int, ...]]:
    """All (±2^8,0^16) vectors on Golay octads with even sign parity."""
    words = golay_words() if words is None else words
    octads = [word for word in words if sum(word) == 8]
    out = []
    for word in octads:
        support = [i for i, bit in enumerate(word) if bit]
        for mask in range(256):
            if mask.bit_count() % 2:
                continue
            vector = [0] * 24
            for position, coordinate in enumerate(support):
                vector[coordinate] = -2 if (mask >> position) & 1 else 2
            out.append(tuple(vector))
    return out


def class_c_vectors(words: list[list[int]] | None = None) -> list[tuple[int, ...]]:
    """All Golay-controlled (±3,±1^23) vectors.

    A codeword selects sign flips and the distinguished coordinate has the
    opposite sign.  The all-zero word therefore gives (-3,1^23); the all-one
    word supplies its negative.
    """
    words = golay_words() if words is None else words
    out = []
    for distinguished in range(24):
        for word in words:
            vector = [-1 if bit else 1 for bit in word]
            vector[distinguished] *= -3
            out.append(tuple(vector))
    return out


def inventory() -> dict[str, list[tuple[int, ...]]]:
    words = golay_words()
    return {
        "A": class_a_vectors(),
        "B": class_b_vectors(words),
        "C": class_c_vectors(words),
    }


def stable_addresses(vectors: dict[str, list[tuple[int, ...]]]) -> dict[str, dict[str, int]]:
    """Assign distinct deterministic addresses to every semantic channel."""
    result: dict[str, dict[str, int]] = {}
    for family, family_vectors in vectors.items():
        used: set[int] = set()
        result[family] = {}
        for channel in ALL_CHANNELS:
            digest = hashlib.sha256(f"Leech-v3:{family}:{channel}".encode()).digest()
            index = int.from_bytes(digest[:8], "big") % len(family_vectors)
            while index in used:
                index = (index + 1) % len(family_vectors)
            used.add(index)
            result[family][channel] = index
    return result


def exact_audit(vectors: dict[str, list[tuple[int, ...]]]) -> dict[str, object]:
    words = golay_words()
    weights = Counter(sum(word) for word in words)
    expected = {"A": 1104, "B": 97152, "C": 98304}
    return {
        "integer_coordinate_scale": "divide coordinates by sqrt(8)",
        "golay_word_count": len(words),
        "golay_weight_distribution": dict(sorted(weights.items())),
        "octad_count": weights[8],
        "class_counts": {family: len(items) for family, items in vectors.items()},
        "expected_class_counts": expected,
        "total_count": sum(map(len, vectors.values())),
        "all_vectors_distinct_within_class": {
            family: len(set(items)) == len(items) for family, items in vectors.items()
        },
        "classes_pairwise_disjoint": not (
            set(vectors["A"]) & set(vectors["B"]) or
            set(vectors["A"]) & set(vectors["C"]) or
            set(vectors["B"]) & set(vectors["C"])
        ),
        "squared_norms_integer_scale": {
            family: sorted({sum(x*x for x in vector) for vector in items})
            for family, items in vectors.items()
        },
        "squared_norms_leech_scale": {
            family: sorted({sum(x*x for x in vector) / 8 for vector in items})
            for family, items in vectors.items()
        },
        "construction_notes": {
            "A": "all coordinate pairs and four sign choices",
            "B": "759 weight-8 extended-Golay supports and 128 even-parity sign choices",
            "C": "24 distinguished coordinates and all 4096 extended-Golay codewords controlling signs",
        },
    }


def load_rows() -> list[dict[str, str]]:
    base.read_and_normalize()
    with base.PROCESSED.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def numeric(row: dict[str, str], field: str) -> float | None:
    try:
        return float(row[field]) if row[field] != "" else None
    except ValueError:
        return None


def folds(rows: list[dict[str, str]]):
    for period in range(1, 8):
        train = [row for row in rows if int(row["Period"]) != period]
        test = [row for row in rows if int(row["Period"]) == period]
        yield period, train, test


def standardized(train: list[dict[str, str]], test: list[dict[str, str]]) -> dict[int, list[float]]:
    means, scales = [], []
    for field in NUMERIC_FEATURES:
        observed = [value for row in train if (value := numeric(row, field)) is not None]
        mean = statistics.fmean(observed)
        means.append(mean)
        scales.append(max(statistics.pstdev(observed), 1e-12))
    result = {}
    for row in train + test:
        values = []
        for field, mean, scale in zip(NUMERIC_FEATURES, means, scales):
            value = numeric(row, field)
            values.append(((mean if value is None else value) - mean) / scale)
        result[int(row["AtomicNumber"])] = values
    return result


def embedded(values: list[float], addresses: list[tuple[int, ...]]) -> list[float]:
    return [sum(value * address[k] for value, address in zip(values, addresses))
            for k in range(24)]


def pair_auc(test: list[dict[str, str]], representations: dict[int, list[float]], label: str) -> float | None:
    pairs, labels, scores = [], [], []
    for i, left in enumerate(test):
        for right in test[i + 1:]:
            a, b = int(left["AtomicNumber"]), int(right["AtomicNumber"])
            pairs.append((a, b))
            labels.append(left[label] == right[label])
            scores.append(-math.dist(representations[a], representations[b]))
    if not any(labels) or all(labels):
        return None
    return auc(labels, scores)


def relationship_experiment(rows: list[dict[str, str]], vectors: dict[str, list[tuple[int, ...]]],
                            address_ids: dict[str, dict[str, int]]) -> list[dict[str, object]]:
    """Leave-one-period-out pair AUC; preprocessing uses training elements only."""
    records: list[dict[str, object]] = []
    rng = random.Random(SEED)
    assignments: dict[str, list[tuple[str, list[tuple[int, ...]]]]] = {"raw": [("fixed", [])]}
    for family, items in vectors.items():
        fixed = [items[address_ids[family][field]] for field in NUMERIC_FEATURES]
        choices = [("fixed", fixed)]
        for seed_index in range(16):
            choices.append((f"random_{seed_index:02d}", rng.sample(items, len(NUMERIC_FEATURES))))
        assignments[family] = choices
    for period, train, test in folds(rows):
        values = standardized(train, test)
        for family, variants in assignments.items():
            for variant, addresses in variants:
                representations = values if family == "raw" else {
                    z: embedded(vector, addresses) for z, vector in values.items()
                }
                for endpoint in ("GroupBlock", "StandardState"):
                    score = pair_auc(test, representations, endpoint)
                    if score is not None:
                        records.append({"held_out_period": period, "endpoint": endpoint,
                                        "family": family, "assignment": variant, "auc": score,
                                        "test_elements": len(test)})
    return records


def summarize(records: list[dict[str, object]]) -> dict[str, object]:
    groups: dict[tuple[str, str, str], list[float]] = {}
    for record in records:
        key = (str(record["endpoint"]), str(record["family"]),
               "fixed" if record["assignment"] == "fixed" else "random_controls")
        groups.setdefault(key, []).append(float(record["auc"]))
    summary = []
    for (endpoint, family, assignment), scores in sorted(groups.items()):
        summary.append({"endpoint": endpoint, "family": family, "assignment_group": assignment,
                        "fold_records": len(scores), "mean_auc": statistics.fmean(scores),
                        "min_auc": min(scores), "max_auc": max(scores)})
    return {
        "validation": "leave-one-period-out; train-only mean imputation and standardization; test-test pairs",
        "input_features": list(NUMERIC_FEATURES),
        "missing_values": "training mean, represented as zero after standardization",
        "summary": summary,
        "interpretation_guardrail": "The fixed address assignment was declared by a stable hash, not learned. Random assignments are norm-matched controls. Labels are not input features, but melting/boiling point is physically close to standard state, so that endpoint is a consistency check rather than an independent discovery.",
    }


def write_outputs() -> None:
    vectors = inventory()
    addresses = stable_addresses(vectors)
    audit = exact_audit(vectors)
    rows = load_rows()
    records = relationship_experiment(rows, vectors, addresses)
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Element Data Object v3: three Leech minimal-vector classes",
        "schema_version": 3,
        "extends": "element_data_object_v2.json",
        "semantics": "Measurements remain typed values. A/B/C vectors are exact geometric addresses; they do not replace units, conditions, uncertainty, or provenance.",
        "class_resolvers": {
            "A": "lexicographic coordinate-pair order, signs (-4,-4),(-4,4),(4,-4),(4,4)",
            "B": "Golay octads in message order; even-parity 8-bit sign masks in integer order",
            "C": "distinguished coordinate 0..23; Golay message 0..4095 controls sign flips; distinguished sign reversed and magnitude 3",
        },
        "class_counts": {family: len(items) for family, items in vectors.items()},
        "channel_address_ids": addresses,
        "resolved_channel_addresses_integer_scale": {
            family: {field: list(vectors[family][index]) for field, index in mapping.items()}
            for family, mapping in addresses.items()
        },
        "source": "data/raw/pubchem_periodic_table.csv; details in data/SOURCES.md",
    }
    SCHEMA.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    with OBJECTS.open("w", encoding="utf-8") as handle:
        for row in rows:
            channels = {}
            for field in ALL_CHANNELS:
                value = v2.parse_value(field, row[field])
                channels[field] = {
                    "value": value, "missing": value is None, "unit": v2.UNITS.get(field),
                    "uncertainty": None, "conditions": None,
                    "leech_addresses": {family: {"class": family, "index": addresses[family][field]}
                                        for family in ("A", "B", "C")},
                    "provenance": {"dataset": "PubChem Periodic Table snapshot", "field": field},
                }
            z = int(row["AtomicNumber"])
            message = v2.gray_message12(z)
            handle.write(json.dumps({
                "schema_version": 3,
                "subject": {"kind": "chemical_element", "atomic_number": z,
                            "symbol": row["Symbol"], "name": row["Name"]},
                "identity": {"gray_integer": v2.gray_encode(z), "message_bits": message,
                             "golay_codeword": base.golay_encode(message)},
                "channels": channels,
            }, separators=(",", ":")) + "\n")
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    with METRICS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader(); writer.writerows(records)
    REPORT_DATA.write_text(json.dumps(summarize(records), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_outputs()
    print(AUDIT.read_text(), end="")

#!/usr/bin/env python3
"""Predeclared A/B/C interaction test on gas-phase diatomic D0 values.

The endpoint and operators are fixed in this source before model fitting:
A = additive/co-presence, B = absolute contrast, C = Hadamard coupling.
Every validation fold withholds every molecule containing one test element.
"""
from __future__ import annotations

import csv
import json
import math
import random
import statistics
from pathlib import Path

import golay_mog_experiments as base
import leech_class_data_objects as leech

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data/processed/diatomic_dissociation_0k.csv"
METRICS = ROOT / "results/diatomic_complete_element_holdout.csv"
PREDICTIONS = ROOT / "results/diatomic_predictions.csv"
SUMMARY = ROOT / "results/diatomic_interaction_summary.json"
SEED = 20260803
RIDGE_LAMBDA = 10.0

# Declared before fitting. Their meanings do not depend on the measured D0 values.
def operator_a(left: list[float], right: list[float]) -> list[float]:
    """Additive/co-presence operator A: symmetric coordinate sum."""
    return [x + y for x, y in zip(left, right)]


def operator_b(left: list[float], right: list[float]) -> list[float]:
    """Contrast operator B: symmetric coordinatewise absolute difference."""
    return [abs(x - y) for x, y in zip(left, right)]


def operator_c(left: list[float], right: list[float]) -> list[float]:
    """Coupling operator C: symmetric coordinatewise product."""
    return [x * y for x, y in zip(left, right)]


OPERATORS = {"A": operator_a, "B": operator_b, "C": operator_c}


def load_endpoint() -> list[dict[str, object]]:
    with DATA.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [{**row, "value_kJ_mol": float(row["value_kJ_mol"]),
             "uncertainty_kJ_mol": (float(row["uncertainty_kJ_mol"])
                                      if row["uncertainty_kJ_mol"] else None)} for row in rows]


def load_elements() -> tuple[dict[str, dict[str, str]], dict[str, int]]:
    rows = leech.load_rows()
    return ({row["Symbol"]: row for row in rows},
            {row["Symbol"]: int(row["AtomicNumber"]) for row in rows})


def training_scaler(train_species: list[dict[str, object]], elements: dict[str, dict[str, str]]):
    """Fit imputation and scaling on elements appearing in training molecules only."""
    symbols = sorted({str(row[key]) for row in train_species for key in ("element_a", "element_b")})
    means, scales = [], []
    for field in leech.NUMERIC_FEATURES:
        values = [leech.numeric(elements[s], field) for s in symbols]
        observed = [x for x in values if x is not None]
        mean = statistics.fmean(observed)
        means.append(mean)
        scales.append(max(statistics.pstdev(observed), 1e-12))

    def transform(symbol: str) -> list[float]:
        out = []
        for field, mean, scale in zip(leech.NUMERIC_FEATURES, means, scales):
            value = leech.numeric(elements[symbol], field)
            out.append(((mean if value is None else value) - mean) / scale)
        return out
    return transform


def pair_features(left: list[float], right: list[float], operator: str) -> list[float]:
    return OPERATORS[operator](left, right)


def ridge_predict(train_x: list[list[float]], train_y: list[float], test_x: list[list[float]]) -> list[float]:
    model = base.ridge_fit(train_x, train_y, RIDGE_LAMBDA)
    weights, means, scales = model
    return [weights[0] + sum(weights[j + 1] * ((x[j] - means[j]) / scales[j])
                             for j in range(len(x))) for x in test_x]


def run_experiment() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    species = load_endpoint()
    elements, atomic_numbers = load_elements()
    vectors = leech.inventory()
    ids = leech.stable_addresses(vectors)
    fixed_addresses = {family: [vectors[family][ids[family][field]]
                                for field in leech.NUMERIC_FEATURES]
                       for family in "ABC"}
    rng = random.Random(SEED)
    random_addresses = {
        family: [rng.sample(vectors[family], len(leech.NUMERIC_FEATURES))
                 for _ in range(16)] for family in "ABC"
    }
    held_out = sorted({str(row[k]) for row in species for k in ("element_a", "element_b")},
                      key=atomic_numbers.get)
    predictions: list[dict[str, object]] = []
    metrics: list[dict[str, object]] = []

    for symbol in held_out:
        train = [r for r in species if symbol not in (r["element_a"], r["element_b"])]
        test = [r for r in species if symbol in (r["element_a"], r["element_b"])]
        transform = training_scaler(train, elements)

        def raw(row):
            return transform(str(row["element_a"])), transform(str(row["element_b"]))

        configs: dict[str, tuple[str, str | None, int | None]] = {
            "mean_only": ("mean", None, None),
            "atomic_number_ABC": ("z", None, None),
            "raw_properties_ABC": ("raw", None, None),
            "fixed_A": ("fixed", "A", None), "fixed_B": ("fixed", "B", None),
            "fixed_C": ("fixed", "C", None), "fixed_ABC": ("fixed_all", None, None),
        }
        for family in "ABC":
            for index in range(16):
                configs[f"random_{family}_{index:02d}"] = ("random", family, index)

        def describe(row, kind, family, index):
            left, right = raw(row)
            if kind == "mean": return [0.0]
            if kind == "z":
                zl, zr = float(atomic_numbers[str(row["element_a"])]), float(atomic_numbers[str(row["element_b"])])
                l, r = [zl, zl*zl, zl*zl*zl], [zr, zr*zr, zr*zr*zr]
                return operator_a(l, r) + operator_b(l, r) + operator_c(l, r)
            if kind == "raw":
                return operator_a(left, right) + operator_b(left, right) + operator_c(left, right)
            if kind in ("fixed", "random"):
                addresses = fixed_addresses[family] if kind == "fixed" else random_addresses[family][index]
                l, r = leech.embedded(left, addresses), leech.embedded(right, addresses)
                return OPERATORS[family](l, r)
            if kind == "fixed_all":
                out = []
                for fam in "ABC":
                    addresses = fixed_addresses[fam]
                    out += OPERATORS[fam](leech.embedded(left, addresses), leech.embedded(right, addresses))
                return out
            raise ValueError(kind)

        train_y = [float(r["value_kJ_mol"]) for r in train]
        for config, (kind, family, index) in configs.items():
            train_x = [describe(r, kind, family, index) for r in train]
            test_x = [describe(r, kind, family, index) for r in test]
            predicted = ([statistics.fmean(train_y)] * len(test) if kind == "mean"
                         else ridge_predict(train_x, train_y, test_x))
            errors = []
            for row, estimate in zip(test, predicted):
                error = estimate - float(row["value_kJ_mol"])
                errors.append(error)
                predictions.append({"held_out_element": symbol, "species": row["species"],
                                    "configuration": config, "observed_kJ_mol": row["value_kJ_mol"],
                                    "predicted_kJ_mol": estimate, "error_kJ_mol": error})
            metrics.append({"held_out_element": symbol, "configuration": config,
                            "train_species": len(train), "test_species": len(test),
                            "mae_kJ_mol": statistics.fmean(abs(e) for e in errors),
                            "rmse_kJ_mol": math.sqrt(statistics.fmean(e*e for e in errors))})
    return metrics, predictions


def summarize(metrics: list[dict[str, object]], predictions: list[dict[str, object]]) -> dict[str, object]:
    fixed_names = ["mean_only", "atomic_number_ABC", "raw_properties_ABC",
                   "fixed_A", "fixed_B", "fixed_C", "fixed_ABC"]
    rows = []
    for name in fixed_names:
        selected = [r for r in metrics if r["configuration"] == name]
        rows.append({"configuration": name, "element_folds": len(selected),
                     "macro_element_mae_kJ_mol": statistics.fmean(float(r["mae_kJ_mol"]) for r in selected),
                     "macro_element_rmse_kJ_mol": statistics.fmean(float(r["rmse_kJ_mol"]) for r in selected)})
    random_summary = []
    for family in "ABC":
        seed_means = []
        for i in range(16):
            name = f"random_{family}_{i:02d}"
            seed_means.append(statistics.fmean(float(r["mae_kJ_mol"]) for r in metrics
                                               if r["configuration"] == name))
        random_summary.append({"family": family, "assignments": 16,
                               "mean_macro_mae_kJ_mol": statistics.fmean(seed_means),
                               "min_macro_mae_kJ_mol": min(seed_means),
                               "max_macro_mae_kJ_mol": max(seed_means)})
    endpoint = load_endpoint()
    return {
        "endpoint": {"name": "gas-phase diatomic D0", "temperature_K": 0,
                     "unit": "kJ mol-1", "charge": "neutral only",
                     "electronic_state": "CCCBDB state 1/configuration 1 ground-state record",
                     "species_records": len(endpoint),
                     "records_with_reported_uncertainty": sum(r["uncertainty_kJ_mol"] is not None for r in endpoint),
                     "elements": len({str(r[k]) for r in endpoint for k in ("element_a", "element_b")})},
        "validation": "complete-element holdout: all species containing the test element excluded from training; preprocessing refit per fold",
        "predeclared_operators": {"A": "coordinate sum", "B": "absolute coordinate difference", "C": "coordinatewise product"},
        "model": {"type": "ridge regression", "lambda": RIDGE_LAMBDA, "selection": "fixed, no endpoint-driven tuning"},
        "fixed_results": rows, "random_address_controls": random_summary,
        "guardrails": ["Atomic descriptors are measured side channels, not inferred from Golay geometry.",
                       "The small, uneven dataset supports a pilot comparison, not chemical deployment.",
                       "Missing source uncertainty is explicit and is not converted to zero."],
    }


def write_outputs() -> None:
    metrics, predictions = run_experiment()
    for path, records in ((METRICS, metrics), (PREDICTIONS, predictions)):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]))
            writer.writeheader(); writer.writerows(records)
    SUMMARY.write_text(json.dumps(summarize(metrics, predictions), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_outputs()
    print(SUMMARY.read_text(), end="")

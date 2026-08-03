#!/usr/bin/env python3
"""UBP/GLM ontology experiment on the retained diatomic endpoint.

ARISTOTLE EXPERIMENTAL CONTRIBUTION: this module turns the supplied UBP
v5.4.1 vocabulary into predeclared, testable descriptors.  It does not treat
TAX, NRCI, MOG roles, or the 0.500 horizon as established chemical laws.
Every validation fold completely withholds one element and refits all
preprocessing on the remaining species.
"""
from __future__ import annotations

import csv
import json
import math
import random
import statistics
from fractions import Fraction
from pathlib import Path

import diatomic_interaction_experiment as diatomic
import golay_mog_experiments as base
import leech_class_data_objects as leech
import ubp_unified_v5 as ubp

ROOT = Path(__file__).resolve().parent
METRICS = ROOT / "results/ubp_element_mog_holdout.csv"
PREDICTIONS = ROOT / "results/ubp_element_mog_predictions.csv"
SUMMARY = ROOT / "results/ubp_element_mog_summary.json"
SEED = 20260803
RANDOM_LAYOUTS = 16

# The imported implementation defines TAX = weight*Y + norm²/8.  For binary
# vectors norm²=weight, so TAX and NRCI contain exactly one degree of freedom.
Y = ubp.LEECH_ENGINE.Y


def element_codeword(z: int) -> list[int]:
    """The established v4 identity route: atomic number -> Gray12 -> Golay24."""
    return base.golay_encode(base.gray12(z))


def permuted_mog(word: list[int], permutation: tuple[int, ...]) -> list[int]:
    return [word[i] for i in permutation]


def tax_nrci(word: list[int]) -> tuple[float, float]:
    tax = ubp.LEECH_ENGINE.calculate_symmetry_tax(word)
    nrci = Fraction(10, 1) / (Fraction(10, 1) + tax)
    return float(tax), float(nrci)


def word_descriptor(word: list[int], permutation: tuple[int, ...]) -> list[float]:
    """Transparent UBP state descriptor, including deliberately redundant metrics."""
    mog = permuted_mog(word, permutation)
    rows = [sum(mog[6*r:6*r+6]) for r in range(4)]
    cols = [sum(mog[c::6]) for c in range(6)]
    # A linear-codeword XOR is itself a Golay word, so its Hexacode shadow is valid.
    hex_symbols, column_patterns = ubp.GOLAY_ENGINE.mog_decompose(word)
    hex_counts = [hex_symbols.count(symbol) for symbol in range(4)]
    pattern_weights = [int(pattern).bit_count() for pattern in column_patterns]
    weight = sum(word)
    tax, nrci = tax_nrci(word)
    return [float(weight), tax, nrci, *map(float, rows), *map(float, cols),
            *map(float, hex_counts), *map(float, pattern_weights)]


def pair_ubp_descriptor(z_left: int, z_right: int,
                        permutation: tuple[int, ...]) -> list[float]:
    left, right = element_codeword(z_left), element_codeword(z_right)
    transition = [a ^ b for a, b in zip(left, right)]
    dl = word_descriptor(left, permutation)
    dr = word_descriptor(right, permutation)
    dt = word_descriptor(transition, permutation)
    # Symmetric A/B/C participant composition plus the transition trajectory.
    return (diatomic.operator_a(dl, dr) + diatomic.operator_b(dl, dr) +
            diatomic.operator_c(dl, dr) + dt)


def invariant_descriptor(z_left: int, z_right: int) -> list[float]:
    """Permutation-invariant UBP quantities only: weight, TAX, and NRCI."""
    left, right = element_codeword(z_left), element_codeword(z_right)
    transition = [a ^ b for a, b in zip(left, right)]
    dl, dr, dt = list(tax_nrci(left)), list(tax_nrci(right)), list(tax_nrci(transition))
    dl.insert(0, float(sum(left))); dr.insert(0, float(sum(right)))
    return diatomic.operator_a(dl, dr) + diatomic.operator_b(dl, dr) + diatomic.operator_c(dl, dr) + dt


def run_experiment() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    species = diatomic.load_endpoint()
    elements, atomic_numbers = diatomic.load_elements()
    held_out = sorted({str(row[k]) for row in species for k in ("element_a", "element_b")},
                      key=atomic_numbers.get)
    rng = random.Random(SEED)
    random_permutations = [tuple(rng.sample(range(24), 24)) for _ in range(RANDOM_LAYOUTS)]
    fixed = tuple(base.MOG_GRID_BITS)
    metrics: list[dict[str, object]] = []
    predictions: list[dict[str, object]] = []

    for symbol in held_out:
        train = [r for r in species if symbol not in (r["element_a"], r["element_b"])]
        test = [r for r in species if symbol in (r["element_a"], r["element_b"])]
        transform = diatomic.training_scaler(train, elements)

        def raw_features(row: dict[str, object]) -> list[float]:
            left = transform(str(row["element_a"])); right = transform(str(row["element_b"]))
            return diatomic.operator_a(left, right) + diatomic.operator_b(left, right) + diatomic.operator_c(left, right)

        configurations: dict[str, object] = {
            "mean_only": None,
            "raw_properties_ABC": raw_features,
            "ubp_invariants": lambda row: invariant_descriptor(
                atomic_numbers[str(row["element_a"])], atomic_numbers[str(row["element_b"])]),
            "ubp_fixed_mog_hex": lambda row: pair_ubp_descriptor(
                atomic_numbers[str(row["element_a"])], atomic_numbers[str(row["element_b"])], fixed),
            "raw_plus_ubp_fixed": lambda row: raw_features(row) + pair_ubp_descriptor(
                atomic_numbers[str(row["element_a"])], atomic_numbers[str(row["element_b"])], fixed),
        }
        for i, permutation in enumerate(random_permutations):
            configurations[f"ubp_random_mog_{i:02d}"] = lambda row, p=permutation: pair_ubp_descriptor(
                atomic_numbers[str(row["element_a"])], atomic_numbers[str(row["element_b"])], p)

        train_y = [float(r["value_kJ_mol"]) for r in train]
        for name, descriptor in configurations.items():
            if descriptor is None:
                estimates = [statistics.fmean(train_y)] * len(test)
            else:
                train_x = [descriptor(r) for r in train]
                test_x = [descriptor(r) for r in test]
                estimates = diatomic.ridge_predict(train_x, train_y, test_x)
            errors = []
            for row, estimate in zip(test, estimates):
                error = estimate - float(row["value_kJ_mol"]); errors.append(error)
                predictions.append({"held_out_element": symbol, "species": row["species"],
                                    "configuration": name, "observed_kJ_mol": row["value_kJ_mol"],
                                    "predicted_kJ_mol": estimate, "error_kJ_mol": error})
            metrics.append({"held_out_element": symbol, "configuration": name,
                            "train_species": len(train), "test_species": len(test),
                            "mae_kJ_mol": statistics.fmean(abs(e) for e in errors),
                            "rmse_kJ_mol": math.sqrt(statistics.fmean(e*e for e in errors))})
    return metrics, predictions


def summarize(metrics: list[dict[str, object]]) -> dict[str, object]:
    def macro(name: str, metric: str = "mae_kJ_mol") -> float:
        return statistics.fmean(float(r[metric]) for r in metrics if r["configuration"] == name)
    principal = ["mean_only", "raw_properties_ABC", "ubp_invariants",
                 "ubp_fixed_mog_hex", "raw_plus_ubp_fixed"]
    random_mae = [macro(f"ubp_random_mog_{i:02d}") for i in range(RANDOM_LAYOUTS)]
    words = [element_codeword(z) for z in range(1, 119)]
    grammar_failures = sum(ubp.GOLAY_ENGINE.mog_decompose(word)[0]
                           not in set(ubp.GolayCodeEngine.build_hexacode()) for word in words)
    tax_identity_failures = sum(
        ubp.LEECH_ENGINE.calculate_symmetry_tax(word)
        != Fraction(sum(word), 1) * (Y + Fraction(1, 8))
        for word in words
    )
    horizons = sum(tax_nrci(word)[1] > 0.5 for word in words)
    return {
        "contribution_note": "ARISTOTLE EXPERIMENTAL CONTRIBUTION: operationalization, validation design, analysis, and report; supplied UBP v5.4.1 formulas are retained unchanged.",
        "endpoint": "52 neutral gas-phase diatomic D0 records at 0 K; 19 complete-element holdout folds",
        "predeclared_pipeline": "atomic number -> Gray12 -> Golay24 -> fixed MOG/Hexacode; symmetric A/B/C participant composition plus XOR transition",
        "fixed_results": [{"configuration": name, "macro_element_mae_kJ_mol": macro(name),
                           "macro_element_rmse_kJ_mol": macro(name, "rmse_kJ_mol")} for name in principal],
        "random_mog_controls": {"layouts": RANDOM_LAYOUTS, "mean_macro_mae_kJ_mol": statistics.fmean(random_mae),
                                "min_macro_mae_kJ_mol": min(random_mae), "max_macro_mae_kJ_mol": max(random_mae)},
        "exact_audits": {"element_identity_words": 118, "invalid_hexacode_shadows": grammar_failures,
                         "binary_tax_identity_failures": tax_identity_failures,
                         "element_identity_nrci_above_0_5": horizons,
                         "tax_identity": "for binary v, TAX(v) = weight(v) * (Y + 1/8); NRCI is therefore a monotone transform of weight"},
        "interpretive_guardrails": [
            "TAX and NRCI are evaluated as supplied engineered scores, not assumed physical energy or chemical coherence.",
            "The 0.500 threshold is audited rather than used to select models or labels.",
            "Fixed MOG performance must be compared with identical random-coordinate controls.",
            "A valid Hexacode shadow is guaranteed by the chosen Golay encoding and is not by itself evidence of chemistry.",
        ],
    }


def write_outputs() -> None:
    metrics, predictions = run_experiment()
    for path, records in ((METRICS, metrics), (PREDICTIONS, predictions)):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)
    SUMMARY.write_text(json.dumps(summarize(metrics), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_outputs()
    print(SUMMARY.read_text(), end="")

#!/usr/bin/env python3
"""Fundamental-first UBP audit and standardized knowledge-base element pilot.

This module treats UBP scores and particle formulae as hypotheses to audit.  It
uses exact Fractions wherever supplied, distinguishes formula inputs from
independent validation targets, and does not interpret a 3D visualization as
the 24-dimensional Leech lattice itself.
"""
from __future__ import annotations

import csv
import json
import math
import re
import statistics
from fractions import Fraction
from pathlib import Path
from typing import Callable

import diatomic_interaction_experiment as diatomic
import ubp_unified_v5 as ubp

ROOT = Path(__file__).resolve().parent
KB_PATH = ROOT / "ubp_system_kb.json"
ELEMENTS_OUT = ROOT / "data/processed/ubp_kb_elements_standardized.csv"
PHYSICS_OUT = ROOT / "results/ubp_particle_formula_audit.csv"
HOLDOUT_OUT = ROOT / "results/ubp_kb_element_holdout.csv"
SUMMARY_OUT = ROOT / "results/ubp_fundamental_kb_summary.json"
DEFAULT_ABSOLUTE_NRCI_THRESHOLD = 0.7
DEFAULT_RELATIVE_RETENTION = 0.7

CHEMICAL_CLASSES = (
    "ALKALI_METAL", "ALKALINE_EARTH", "TRANSITION_METAL", "POST_TRANSITION_METAL",
    "METALLOID", "NONMETAL", "HALOGEN", "NOBLE_GAS", "LANTHANIDE", "ACTINIDE",
)
# Only categories whose stored tensor length exactly matches the parameter table
# are eligible.  This prevents shifted positional labels from looking valid.
CORE_CHANNELS = {
    "atomic_mass": ("M_Mass", "M"),
    "boiling_point": ("M_Thermal", "BP"),
    "melting_point": ("M_Thermal", "MP"),
    "atomic_number": ("M_Count", "Z"),
    "density": ("I_Density", "Rho"),
}
MODEL_CHANNELS = ("atomic_mass", "boiling_point", "melting_point", "density")


def _fraction(value: object) -> Fraction | None:
    """Parse a KB rational; its declared null token is kept as missing."""
    if value in (None, "", 0):
        return None
    return Fraction(str(value))


def _chemical_class(tags: list[str]) -> str:
    return next((tag for tag in CHEMICAL_CLASSES if tag in tags), "OTHER_OR_UNSPECIFIED")


def load_standardized_elements() -> tuple[list[dict[str, object]], dict[str, object]]:
    raw = json.loads(KB_PATH.read_text(encoding="utf-8"))
    fields = raw["_fields"]
    params = raw["_params"]
    field_index = {name: i for i, name in enumerate(fields)}
    category_names = list(params)
    category_index = {name: i for i, name in enumerate(category_names)}
    eligible: dict[str, bool] = {}
    observed_lengths: dict[str, list[int]] = {}
    entries = [e for e in raw["entries"].values() if "ELEMENT" in e[field_index["tags"]]]
    for category, names in params.items():
        ci = category_index[category]
        lengths = sorted({len(e[field_index["mog_tensor"]][ci])
                          if isinstance(e[field_index["mog_tensor"]][ci], list) else 0
                          for e in entries})
        observed_lengths[category] = lengths
        eligible[category] = lengths == [len(names)]

    rows: list[dict[str, object]] = []
    for entry in entries:
        record = dict(zip(fields, entry))
        match = re.fullmatch(r"ELEM_([A-Za-z]+)_(\d{3})", str(record["ubp_id"]))
        if not match:
            raise ValueError(f"unrecognized element id {record['ubp_id']}")
        symbol, id_z = match.group(1), int(match.group(2))
        tags = list(record["tags"])
        period_tag = next((x for x in tags if x.startswith("PERIOD_")), "PERIOD_UNKNOWN")
        row: dict[str, object] = {
            "ubp_id": record["ubp_id"], "symbol": symbol, "id_atomic_number": id_z,
            "period": period_tag, "chemical_class": _chemical_class(tags),
            "lexicon": record["lexicon"], "vector_weight": sum(record["vector"]),
            "nrci": float(record["nrci_val"]), "tax_exact": record["tax_str"],
        }
        tensor = record["mog_tensor"]
        for output_name, (category, parameter) in CORE_CHANNELS.items():
            if not eligible[category]:
                row[output_name] = None
                continue
            ci = category_index[category]
            pi = params[category].index(parameter)
            row[output_name] = _fraction(tensor[ci][pi])
        if row["atomic_number"] is None or int(row["atomic_number"]) != id_z:
            raise ValueError(f"atomic-number mismatch for {record['ubp_id']}")
        rows.append(row)
    rows.sort(key=lambda r: int(r["id_atomic_number"]))

    completeness = {
        name: {
            "observed": sum(r[name] is not None for r in rows),
            "missing": sum(r[name] is None for r in rows),
            "unit": "not declared in ubp_system_kb.json",
            "uncertainty_available": False,
            "per_value_provenance_available": False,
        } for name in CORE_CHANNELS
    }
    schema_audit = {
        "element_entries": len(rows), "field_called_math_by_user": "mog_tensor",
        "null_token": raw["_null_token"], "category_declared_lengths": {k: len(v) for k, v in params.items()},
        "category_observed_lengths": observed_lengths,
        "positionally_safe_categories": sorted(k for k, ok in eligible.items() if ok),
        "positionally_unsafe_categories": sorted(k for k, ok in eligible.items() if not ok),
        "core_channel_completeness": completeness,
        "guardrail": "Channels in a category whose tensor length differs from its parameter table are not named positionally.",
    }
    return rows, schema_audit


def write_standardized(rows: list[dict[str, object]]) -> None:
    fields = ["ubp_id", "symbol", "id_atomic_number", "period", "chemical_class", "lexicon",
              "vector_weight", "nrci", "tax_exact", *CORE_CHANNELS]
    with ELEMENTS_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (str(row[k]) if isinstance(row.get(k), Fraction) else row.get(k)) for k in fields})


def peer_coherence(rows: list[dict[str, object]]) -> dict[str, object]:
    def grouped(field: str) -> list[dict[str, object]]:
        groups: dict[str, list[float]] = {}
        for row in rows:
            groups.setdefault(str(row[field]), []).append(float(row["nrci"]))
        out = []
        for name, values in sorted(groups.items()):
            median = statistics.median(values)
            out.append({"group": name, "elements": len(values), "median_nrci": median,
                        "min_nrci": min(values), "max_nrci": max(values),
                        "absolute_pass_0_7": sum(x >= DEFAULT_ABSOLUTE_NRCI_THRESHOLD for x in values),
                        "relative_pass_0_7_of_peer_median": sum(
                            x >= DEFAULT_RELATIVE_RETENTION * median for x in values)})
        return out
    return {
        "absolute_threshold": DEFAULT_ABSOLUTE_NRCI_THRESHOLD,
        "absolute_pass_elements": sum(float(r["nrci"]) >= DEFAULT_ABSOLUTE_NRCI_THRESHOLD for r in rows),
        "relative_rule": "NRCI(subject) >= 0.7 * median NRCI of its declared peer group",
        "period_groups": grouped("period"), "chemical_class_groups": grouped("chemical_class"),
        "interpretation": "Absolute and peer-relative results are reported separately; the peer rule is a scale comparison, not an externally calibrated physical law.",
    }


def constants_audit() -> dict[str, object]:
    constants = ubp.UBPUltimateSubstrate.get_v6_constants()
    reference = {"PI": math.pi, "PHI": (1 + math.sqrt(5)) / 2, "E": math.e}
    errors = {k: abs(float(constants[k]) - v) for k, v in reference.items()}
    return {
        "precision_terms": constants["precision_terms"],
        "exact_fractions": {k: str(v) for k, v in constants.items() if isinstance(v, Fraction)},
        "reference_absolute_errors": errors,
        "dependency_graph": {
            "Y_INV": "PI + 2/PI", "Y": "1/Y_INV", "Y_CONST": "1/(Y_INV + 2/Y_INV)",
            "MONAD": "PI * PHI * E", "WOBBLE": "fractional_part(MONAD)", "SINK_L": "WOBBLE / 13",
        },
        "scope": "These are exact rational approximations generated from finite continued fractions; exactness of the Fraction is not exact equality to irrational pi, phi, or e.",
    }


def particle_formula_audit() -> tuple[list[dict[str, object]], dict[str, object]]:
    canonical = ubp.PARTICLE_PHYSICS.get_canonical_phi_predictions()
    ultimate = ubp.PARTICLE_PHYSICS.get_ultimate_predictions()
    rows: list[dict[str, object]] = []
    for suite, data in (("canonical_phi", canonical), ("ultimate_atlas", ultimate)):
        for name, item in data.items():
            if not isinstance(item, dict) or "error_percent" not in item:
                continue
            rows.append({"suite": suite, "quantity": name, "prediction": item.get("val"),
                         "target": item.get("target"), "error_percent": item["error_percent"],
                         "lens": item.get("lens", ""),
                         "validation_status": "formula reproduction; not held-out"})
    with PHYSICS_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    canonical_errors = [float(x["error_percent"]) for x in canonical.values()]
    ultimate_rows = [x for x in rows if x["suite"] == "ultimate_atlas"]
    return rows, {
        "canonical_formulae": len(canonical_errors),
        "canonical_below_0_1_percent": sum(x < 0.1 for x in canonical_errors),
        "canonical_below_1_percent": sum(x < 1 for x in canonical_errors),
        "canonical_at_or_above_100_percent": sum(x >= 100 for x in canonical_errors),
        "ultimate_formulae": len(ultimate_rows),
        "ultimate_mean_reported_error_percent": statistics.fmean(float(x["error_percent"]) for x in ultimate_rows),
        "independence_audit": [
            "The implementation contains target-scale constants and hand-selected integer/rational coefficients.",
            "The electron target sets m_e_target and propagates into several mass formulae.",
            "Xicc++ is an explicit anchor: its prediction equals a hard-coded target by construction.",
            "m_Z and other empirical scales occur as constants in downstream formulae.",
            "Therefore numerical agreement here is in-sample formula reproduction, not a prospective prediction test.",
        ],
    }


def _fit_transform(train: list[dict[str, object]], lookup: dict[str, dict[str, object]]) -> Callable[[str], list[float]]:
    symbols = sorted({str(r[k]) for r in train for k in ("element_a", "element_b")})
    means, scales = [], []
    for field in MODEL_CHANNELS:
        values = [float(lookup[s][field]) for s in symbols if lookup[s][field] is not None]
        means.append(statistics.fmean(values)); scales.append(max(statistics.pstdev(values), 1e-12))
    def transform(symbol: str) -> list[float]:
        row = lookup[symbol]
        return [((means[i] if row[field] is None else float(row[field])) - means[i]) / scales[i]
                for i, field in enumerate(MODEL_CHANNELS)]
    return transform


def kb_holdout(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, object]]:
    species = diatomic.load_endpoint(); lookup = {str(r["symbol"]): r for r in rows}
    _, atomic_numbers = diatomic.load_elements()
    held = sorted({str(r[k]) for r in species for k in ("element_a", "element_b")}, key=atomic_numbers.get)
    metrics: list[dict[str, object]] = []
    for symbol in held:
        train = [r for r in species if symbol not in (r["element_a"], r["element_b"])]
        test = [r for r in species if symbol in (r["element_a"], r["element_b"])]
        transform = _fit_transform(train, lookup)
        y = [float(r["value_kJ_mol"]) for r in train]
        configs: dict[str, Callable[[dict[str, object]], list[float]] | None] = {
            "mean_only": None,
            "kb_math_standardized_ABC": lambda r: (
                diatomic.operator_a(transform(str(r["element_a"])), transform(str(r["element_b"]))) +
                diatomic.operator_b(transform(str(r["element_a"])), transform(str(r["element_b"]))) +
                diatomic.operator_c(transform(str(r["element_a"])), transform(str(r["element_b"])))),
            "kb_math_Y_twin_ABC": lambda r: _twin_pair_descriptor(
                transform(str(r["element_a"])), transform(str(r["element_b"])))
        }
        for name, descriptor in configs.items():
            predicted = ([statistics.fmean(y)] * len(test) if descriptor is None else
                         diatomic.ridge_predict([descriptor(r) for r in train], y, [descriptor(r) for r in test]))
            errors = [p - float(r["value_kJ_mol"]) for p, r in zip(predicted, test)]
            metrics.append({"held_out_element": symbol, "configuration": name,
                            "train_species": len(train), "test_species": len(test),
                            "mae_kJ_mol": statistics.fmean(abs(e) for e in errors),
                            "rmse_kJ_mol": math.sqrt(statistics.fmean(e*e for e in errors))})
    with HOLDOUT_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metrics[0])); writer.writeheader(); writer.writerows(metrics)
    names = sorted({str(r["configuration"]) for r in metrics})
    return metrics, {name: {
        "macro_element_mae_kJ_mol": statistics.fmean(float(r["mae_kJ_mol"]) for r in metrics if r["configuration"] == name),
        "macro_element_rmse_kJ_mol": statistics.fmean(float(r["rmse_kJ_mol"]) for r in metrics if r["configuration"] == name),
    } for name in names}


def _twin_pair_descriptor(left: list[float], right: list[float]) -> list[float]:
    """Declared Y-twin view: concatenate x and Y*x before symmetric A/B/C."""
    y = float(ubp.LEECH_ENGINE.Y)
    left_twin = left + [y * x for x in left]
    right_twin = right + [y * x for x in right]
    return (diatomic.operator_a(left_twin, right_twin) +
            diatomic.operator_b(left_twin, right_twin) +
            diatomic.operator_c(left_twin, right_twin))


def write_outputs() -> None:
    rows, schema = load_standardized_elements(); write_standardized(rows)
    _, physics = particle_formula_audit(); _, holdout = kb_holdout(rows)
    summary = {
        "contribution_note": "Experimental audit and operationalization; supplied UBP formulae and source KB are unchanged.",
        "fundamental_constants": constants_audit(), "particle_formula_audit": physics,
        "kb_schema_audit": schema, "coherence": peer_coherence(rows),
        "diatomic_holdout": {
            "endpoint": "52 neutral gas-phase diatomic D0 records at 0 K; 19 complete-element holdouts",
            "channels": list(MODEL_CHANNELS), "results": holdout,
            "Y_twin_definition": "T_Y(x) = (x, Y*x); this is a declared virtual-twin feature map, not an inferred physical dimension.",
        },
        "geometry_model": {
            "MOG": "a 4x6 coordinate view/permutation of 24 coordinates",
            "Leech": "an exact 24-dimensional lattice; no canonical lossless map to 3D is asserted",
            "3D": "a visualization or task-specific projection requiring an explicit projection matrix and distortion audit",
            "Monster": "related to Leech/Conway mathematics through additional constructions; not modeled here as extra Euclidean coordinates",
            "physical_channels": "typed measured attributes attached to the subject; they are not silently identified with geometric axes",
        },
    }
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_outputs()
    print(SUMMARY_OUT.read_text(), end="")

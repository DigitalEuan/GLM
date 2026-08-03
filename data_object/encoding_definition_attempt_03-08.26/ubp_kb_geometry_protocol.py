#!/usr/bin/env python3
"""Typed KB channel completion, Golay-octad zones, and an audited 24→3 view.

This module never invents missing metrology.  It preserves each KB rational and
fills metadata slots with explicit ``not_reported``/``unresolved`` states.  Its
3-D map is a declared visualization of the 24 fixed Leech address vectors, not
an identification of three-space with the Leech lattice.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import golay_mog_experiments as golay
import ubp_fundamental_kb_experiment as fundamental
from gray_leech_data_objects import leech_addresses

ROOT = Path(__file__).resolve().parent
TYPED_OUT = ROOT / "data/processed/ubp_kb_elements_typed_long.csv"
OCTAD_OUT = ROOT / "results/ubp_mog_octad_zones.json"
PROJECTION_OUT = ROOT / "results/leech_24d_to_3d_projection.json"
PROTOCOL_OUT = ROOT / "results/prospective_particle_protocol.json"
SUMMARY_OUT = ROOT / "results/ubp_kb_geometry_protocol_summary.json"

# Metadata are an audit result, not a retrofit claim about the source KB.
CHANNEL_METADATA = {
    "atomic_mass": {
        "unit": "u (inferred convention; not declared by KB)",
        "condition": "not_reported", "uncertainty": "not_reported",
        "source": "ubp_system_kb.json; upstream per-value source not_reported",
        "status": "unit_inferred_source_unresolved",
    },
    "boiling_point": {
        "unit": "K (inferred convention; not declared by KB)",
        "condition": "pressure/phase convention not_reported", "uncertainty": "not_reported",
        "source": "ubp_system_kb.json; upstream per-value source not_reported",
        "status": "unit_inferred_conditions_unresolved",
    },
    "melting_point": {
        "unit": "K (inferred convention; not declared by KB)",
        "condition": "pressure/allotrope convention not_reported", "uncertainty": "not_reported",
        "source": "ubp_system_kb.json; upstream per-value source not_reported",
        "status": "unit_inferred_conditions_unresolved",
    },
    "atomic_number": {
        "unit": "1 (count)", "condition": "chemical-element identity",
        "uncertainty": "exact", "source": "KB element identifier and M_Count.Z agree",
        "status": "ontology_derived_exact",
    },
    "density": {
        "unit": "unresolved: values appear to mix gas and condensed-phase conventions",
        "condition": "temperature/pressure/phase not_reported", "uncertainty": "not_reported",
        "source": "ubp_system_kb.json; upstream per-value source not_reported",
        "status": "unit_and_conditions_unresolved",
    },
}

# In the fixed 4×6 MOG, each adjacent pair of columns is an actual Golay octad.
# These are coordinate regions only; they do not repair unrelated tensor arrays.
MOG_OCTAD_ZONE_COLUMNS = ((0, 1), (2, 3), (4, 5))

# Three mutually orthogonal ±1 Walsh rows.  P = SIGNS/sqrt(24).
PROJECTION_SIGNS = (
    (1,) * 12 + (-1,) * 12,
    tuple(1 if (i // 6) % 2 == 0 else -1 for i in range(24)),
    tuple(1 if (i // 3) % 2 == 0 else -1 for i in range(24)),
)


def write_typed_channels() -> dict[str, object]:
    rows, audit = fundamental.load_standardized_elements()
    fields = ("ubp_id", "symbol", "atomic_number_identity", "channel", "value_exact",
              "unit", "condition", "uncertainty", "source", "status")
    with TYPED_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            for channel in fundamental.CORE_CHANNELS:
                writer.writerow({
                    "ubp_id": row["ubp_id"], "symbol": row["symbol"],
                    "atomic_number_identity": row["id_atomic_number"], "channel": channel,
                    "value_exact": str(row[channel]), **CHANNEL_METADATA[channel],
                })
    return {
        "records": len(rows) * len(fundamental.CORE_CHANNELS),
        "elements": len(rows), "channels_per_element": len(fundamental.CORE_CHANNELS),
        "lossless_value_policy": "value_exact is the unchanged rational string from the standardized KB extraction",
        "metrology_policy": "unknown metadata are explicit; inferred units are labelled and are not represented as source declarations",
        "density_warning": CHANNEL_METADATA["density"]["unit"],
        "positional_guardrail": audit["guardrail"],
    }


def octad_zone_audit() -> dict[str, object]:
    all_codewords = {tuple(golay.golay_encode([(message >> i) & 1 for i in range(12)]))
                     for message in range(4096)}
    zones = []
    covered = []
    for index, columns in enumerate(MOG_OCTAD_ZONE_COLUMNS, 1):
        coordinates = [golay.MOG_GRID_BITS[row * 6 + column]
                       for row in range(4) for column in columns]
        word = [0] * 24
        for coordinate in coordinates:
            word[coordinate] = 1
        is_octad = tuple(word) in all_codewords and sum(word) == 8
        zones.append({"zone": f"octad_zone_{index}", "columns": list(columns),
                      "coordinates": coordinates, "is_golay_octad": is_octad})
        covered.extend(coordinates)
    result = {
        "convention": "fixed MOG_GRID_BITS 4x6 row-major display",
        "zones": zones, "partition_all_24_coordinates": sorted(covered) == list(range(24)),
        "scope": "Zones provide named regions for 24-coordinate MOG data only. They cannot assign names to mismatched KB tensor categories.",
        "tensor_decoding_rule": "Decode a category positionally iff every observed tensor length equals its declared parameter count.",
    }
    OCTAD_OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def _project(vector: list[int]) -> list[float]:
    scale = math.sqrt(24.0)
    return [sum(sign * value for sign, value in zip(row, vector)) / scale
            for row in PROJECTION_SIGNS]


def _distance_audit(vectors: list[list[int]], projected: list[list[float]]) -> dict[str, object]:
    pairs = []
    nearest_24, nearest_3 = set(), set()
    for i in range(len(vectors)):
        d24 = [(math.dist(vectors[i], vectors[j]), j) for j in range(len(vectors)) if i != j]
        d3 = [(math.dist(projected[i], projected[j]), j) for j in range(len(vectors)) if i != j]
        m24, m3 = min(x[0] for x in d24), min(x[0] for x in d3)
        nearest_24.update((i, j) for d, j in d24 if abs(d - m24) < 1e-12)
        nearest_3.update((i, j) for d, j in d3 if abs(d - m3) < 1e-12)
        for j in range(i):
            original = math.dist(vectors[i], vectors[j])
            view = math.dist(projected[i], projected[j])
            pairs.append((original, view, abs(view - original) / original))
    retained = nearest_24 & nearest_3
    dot = sum(a*b for a, b, _ in pairs)
    aa = sum(a*a for a, _, _ in pairs); bb = sum(b*b for _, b, _ in pairs)
    return {
        "pair_count": len(pairs),
        "mean_relative_distance_error": sum(e for _, _, e in pairs) / len(pairs),
        "max_relative_distance_error": max(e for _, _, e in pairs),
        "distance_cosine_similarity": dot / math.sqrt(aa * bb) if bb else 0.0,
        "directed_nearest_neighbor_edges_24d": len(nearest_24),
        "directed_nearest_neighbor_edges_3d": len(nearest_3),
        "directed_nearest_neighbor_recall": len(retained) / len(nearest_24),
        "projected_point_collisions": len(projected) - len({tuple(round(x, 12) for x in p) for p in projected}),
    }


def projection_audit() -> dict[str, object]:
    # The established 24 address vectors are integer-scale; retain that scale in both spaces.
    vectors = [list(v) for v in leech_addresses()]
    projected = [_project(v) for v in vectors]
    gram = [[sum(PROJECTION_SIGNS[i][k] * PROJECTION_SIGNS[j][k] for k in range(24))
             for j in range(3)] for i in range(3)]
    result = {
        "purpose": "human-viewing baseline for the 24 fixed Leech address vectors",
        "matrix_definition": "P[r,c] = projection_signs[r,c] / sqrt(24)",
        "projection_signs": [list(row) for row in PROJECTION_SIGNS],
        "row_gram_before_dividing_by_24": gram,
        "matrix_rank": 3,
        "inverse": None,
        "reconstruction": "orthogonal projection x_hat = P^T P x; not an inverse on R^24",
        "information_loss": "kernel dimension 21 by rank-nullity",
        "symmetry_claim": "No Leech-lattice symmetry preservation is claimed; only the displayed row orthonormality is exact.",
        "address_count": len(vectors),
        "projected_coordinates": projected,
        "distance_and_neighborhood_audit": _distance_audit(vectors, projected),
    }
    PROJECTION_OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def prospective_particle_protocol() -> dict[str, object]:
    result = {
        "status": "protocol_only_not_a_prospective_result",
        "reason": "The supplied particle targets and fitted formulae have already been inspected; they cannot become an unseen locked test set retroactively.",
        "subject_class": "dimensionless particle-property ratios, separated by observable type",
        "grammar": {
            "dimensionless_substrate_symbols": ["Y", "Y_INV", "MONAD", "WOBBLE", "SINK_L", "13", "24", "29"],
            "allowed_expression": "signed products of predeclared symbols with integer exponents in [-3,3] and at most four factors",
            "coefficient_rule": "coefficients restricted to reduced p/q with |p|<=24 and 1<=q<=24; enumerate lexicographically",
            "selection_rule": "minimize training log-relative error, then expression length, then lexicographic order",
            "dimensional_rule": "compare dimensionless ratios only; a dimensionful prediction must name an independently supplied unit-bearing anchor",
        },
        "data_split_rule": "Timestamped measurements published after protocol freeze form the locked test set; no coefficient or grammar revision after unblinding.",
        "baselines": [
            "training geometric mean within observable class",
            "dimensional-analysis-only anchor prediction",
            "parameter-count-matched random-symbol grammar",
        ],
        "metrics": ["log-relative error", "median absolute relative error", "coverage if uncertainty intervals are available"],
        "lightspeed_synthesis_interpretation": {
            "electron_mass_residual": "an in-sample residual worth recording, not evidence of a QED correction without a frozen prediction",
            "muon_ratio": "reported null-model result is prior evidence only and must be replicated prospectively",
            "defined_SI_constants": "c, h, e, k_B and cesium frequency are unit anchors, not independently predicted measurements in SI",
        },
        "freeze_requirements": ["versioned protocol hash", "training table with provenance and units", "locked target manifest", "one final evaluation"],
    }
    PROTOCOL_OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def write_outputs() -> None:
    typed = write_typed_channels()
    octads = octad_zone_audit()
    projection = projection_audit()
    particle = prospective_particle_protocol()
    summary = {
        "typed_kb": typed,
        "octad_zones": {"all_three_are_octads": all(z["is_golay_octad"] for z in octads["zones"]),
                         "partition": octads["partition_all_24_coordinates"]},
        "projection": projection["distance_and_neighborhood_audit"],
        "particle": {"status": particle["status"]},
    }
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_outputs()
    print(SUMMARY_OUT.read_text(), end="")

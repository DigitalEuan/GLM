#!/usr/bin/env python3
"""Generate v4 element knowledge objects with explicit multi-grid 3D organization."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import golay_mog_experiments as base
import gray_leech_data_objects as v2
import leech_class_data_objects as v3

ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT / "schemas/element_data_object_v4.json"
OBJECTS = ROOT / "data/objects/elements_v4.jsonl"
AUDIT = ROOT / "results/structured_element_audit.json"

# A 4x6 MOG has 24 cells. Occupancies use the first 19 cells in this fixed order.
ORBITALS = tuple(f"{n}{kind}" for n in range(1, 8) for kind in "spdf" if
                 (kind == "s" or (kind == "p" and n >= 2) or
                  (kind == "d" and n >= 3) or (kind == "f" and n >= 4)))
ORBITALS = tuple(o for o in ORBITALS if o in
                 "1s 2s 2p 3s 3p 3d 4s 4p 4d 4f 5s 5p 5d 5f 6s 6p 6d 7s 7p".split())
CORE_Z = {"He": 2, "Ne": 10, "Ar": 18, "Kr": 36, "Xe": 54, "Rn": 86}


def row_major_cell(coordinate: int) -> dict[str, int]:
    """Return declared 3D pose for a cyclic coordinate in a 4x6 MOG layer."""
    cell = next(i for i in range(24) if int(base.MOG_GRID_BITS[i]) == coordinate)
    return {"coordinate": coordinate, "row": cell // 6, "column": cell % 6}


def parse_configuration(text: str, configurations: dict[str, str]) -> dict[str, int]:
    clean = re.sub(r"\([^)]*\)", "", text)
    occupancy: dict[str, int] = {}
    core = re.search(r"\[([A-Z][a-z]?)\]", clean)
    if core:
        core_symbol = core.group(1)
        occupancy.update(parse_configuration(configurations[core_symbol], configurations))
        clean = clean.replace(core.group(0), "")
    for n, kind, count in re.findall(r"([1-7])([spdf])(\d+)", clean):
        occupancy[n + kind] = int(count)
    return occupancy


def schema_document() -> dict[str, object]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "element_data_object_v4.json",
        "title": "Structured Element Knowledge Object v4",
        "type": "object",
        "required": ["schema_version", "subject", "identity_integrity", "electronic_ground_state",
                     "observations", "spatial_views", "state_boundary"],
        "properties": {
            "schema_version": {"const": 4},
            "subject": {"type": "object", "required": ["kind", "atomic_number", "symbol", "name"],
                        "properties": {"kind": {"const": "chemical_element"},
                                       "atomic_number": {"type": "integer", "minimum": 1, "maximum": 118},
                                       "symbol": {"type": "string"}, "name": {"type": "string"}}},
            "identity_integrity": {"type": "object"},
            "electronic_ground_state": {"type": "object"},
            "observations": {"type": "object"},
            "spatial_views": {"type": "array", "minItems": 9},
            "state_boundary": {"type": "object"}
        },
        "additionalProperties": False,
        "design_contract": {
            "identity": "Atomic number identifies an element; Golay/MOG is an integrity and coordinate view, not chemical content.",
            "state": "Isotopes, ions, excited states, phases, molecules, and events require separate linked objects.",
            "measurements": "Values retain units, missingness, conditions, uncertainty, and provenance.",
            "geometry": "Each 4x6 layer has an explicit frame and z coordinate; 24D Leech addresses remain separate exact views because projecting them to 3D is lossy."
        },
        "orbital_cell_order": list(ORBITALS),
    }


def build_objects() -> list[dict[str, object]]:
    rows = v3.load_rows()
    configurations = {row["Symbol"]: row["ElectronConfiguration"] for row in rows}
    vectors = v3.inventory()
    addresses = v3.stable_addresses(vectors)
    objects = []
    for row in rows:
        z = int(row["AtomicNumber"])
        message = v2.gray_message12(z)
        codeword = base.golay_encode(message)
        occupancy = parse_configuration(row["ElectronConfiguration"], configurations)
        channels = {}
        for field in v3.ALL_CHANNELS:
            value = v2.parse_value(field, row[field])
            channels[field] = {
                "value": value, "unit": v2.UNITS.get(field), "missing": value is None,
                "uncertainty": None, "conditions": None,
                "provenance": {"dataset": "PubChem Periodic Table snapshot", "field": field},
                "exact_leech_addresses": {family: {"class": family, "index": addresses[family][field]}
                                          for family in "ABC"},
            }
        views = [{
            "view_id": "identity_golay", "layer_kind": "MOG_4x6", "z": 0,
            "frame": {"origin": [0, 0, 0], "axes": ["column", "row", "layer"], "cell_spacing": 1},
            "cells": [{**row_major_cell(i), "value": codeword[i], "meaning": "Golay code bit"}
                      for i in range(24)]
        }]
        for shell in range(1, 8):
            cells = []
            for coordinate, orbital in enumerate(ORBITALS):
                if int(orbital[0]) == shell:
                    cells.append({**row_major_cell(coordinate), "orbital": orbital,
                                  "electrons": occupancy.get(orbital, 0)})
            views.append({"view_id": f"electron_shell_{shell}", "layer_kind": "MOG_4x6",
                          "z": shell, "frame": {"origin": [0, 0, shell],
                          "axes": ["column", "row", "layer"], "cell_spacing": 1}, "cells": cells})
        observation_cells = []
        for coordinate, field in enumerate(v3.ALL_CHANNELS):
            observation_cells.append({**row_major_cell(coordinate), "channel_ref": field,
                                      "missing": channels[field]["missing"]})
        views.append({"view_id": "observed_channels", "layer_kind": "MOG_4x6", "z": 8,
                      "frame": {"origin": [0, 0, 8], "axes": ["column", "row", "layer"],
                                "cell_spacing": 1}, "cells": observation_cells})
        objects.append({
            "schema_version": 4,
            "subject": {"kind": "chemical_element", "atomic_number": z,
                        "symbol": row["Symbol"], "name": row["Name"]},
            "identity_integrity": {"canonical_key": f"element:{z}", "gray_integer": v2.gray_encode(z),
                                   "message_bits": message, "golay_codeword": codeword,
                                   "mog_convention": "cyclic-coordinate map from element_data_object_v2"},
            "electronic_ground_state": {"source_text": row["ElectronConfiguration"],
                                        "orbital_occupancies": occupancy,
                                        "electron_count": sum(occupancy.values()),
                                        "charge": 0, "state_scope": "reported neutral ground configuration"},
            "observations": channels,
            "spatial_views": views,
            "state_boundary": {
                "not_embodied_as_this_element_object": ["specific isotope", "ion", "excited state",
                                                         "phase sample", "molecule", "interaction event"],
                "link_policy": "Create a typed state/species/event object referencing canonical_key; never overwrite the element identity."
            }
        })
    return objects


def audit(objects: list[dict[str, object]]) -> dict[str, object]:
    return {
        "object_count": len(objects),
        "unique_canonical_keys": len({o["identity_integrity"]["canonical_key"] for o in objects}),
        "atomic_numbers": [o["subject"]["atomic_number"] for o in objects],
        "electron_count_matches_atomic_number": all(
            o["electronic_ground_state"]["electron_count"] == o["subject"]["atomic_number"] for o in objects),
        "views_per_object": sorted({len(o["spatial_views"]) for o in objects}),
        "view_z_layers": sorted({v["z"] for o in objects for v in o["spatial_views"]}),
        "all_golay_words_even_weight": all(sum(o["identity_integrity"]["golay_codeword"]) % 2 == 0
                                            for o in objects),
        "every_observation_has_three_exact_addresses": all(
            set(c["exact_leech_addresses"]) == {"A", "B", "C"}
            for o in objects for c in o["observations"].values()),
        "interpretation": "The nine 3D MOG layers organize identity, seven electronic shells, and observed channels. They are views over typed records, not a claim that Euclidean proximity is a law of chemistry."
    }


def write_outputs() -> None:
    objects = build_objects()
    SCHEMA.write_text(json.dumps(schema_document(), indent=2) + "\n", encoding="utf-8")
    with OBJECTS.open("w", encoding="utf-8") as handle:
        for obj in objects:
            handle.write(json.dumps(obj, separators=(",", ":")) + "\n")
    AUDIT.write_text(json.dumps(audit(objects), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_outputs()
    print(AUDIT.read_text(), end="")

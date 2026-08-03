#!/usr/bin/env python3
"""Second-round Gray/Golay/MOG data-object experiment.

The exact 24-bit word is an identity and integrity layer.  Measurements remain
lossless typed channels; each channel is attached to one MOG cell and therefore
to a fixed 24-dimensional Leech-lattice minimal-vector address.  This avoids
pretending that finitely many bits can losslessly contain arbitrary values,
units, uncertainty, conditions, and provenance.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path

import golay_mog_experiments as base

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data/objects/elements.jsonl"
SCHEMA = ROOT / "schemas/element_data_object_v2.json"
RESULT = ROOT / "results/gray_leech_audit.json"

UNITS = {
    "AtomicMass": "u", "Electronegativity": "dimensionless",
    "AtomicRadius": "pm", "IonizationEnergy": "eV",
    "ElectronAffinity": "eV", "MeltingPoint": "K",
    "BoilingPoint": "K", "Density": "g/cm^3",
}
# Stable semantic dimensions.  Empty cells are reserved for future channels;
# changing this map requires a new schema version.
CHANNEL_CELLS = {
    "AtomicMass": 0, "ElectronConfiguration": 1,
    "Electronegativity": 2, "AtomicRadius": 3,
    "IonizationEnergy": 4, "ElectronAffinity": 5,
    "OxidationStates": 6, "StandardState": 7,
    "MeltingPoint": 8, "BoilingPoint": 9, "Density": 10,
    "GroupBlock": 11, "YearDiscovered": 12, "Period": 13, "Group": 14,
    "CPKHexColor": 15,
}


def gray_encode(n: int) -> int:
    if n < 0:
        raise ValueError("Gray code is defined here only for nonnegative integers")
    return n ^ (n >> 1)


def gray_decode(g: int) -> int:
    if g < 0:
        raise ValueError("Gray code is defined here only for nonnegative integers")
    n = 0
    while g:
        n ^= g
        g >>= 1
    return n


def gray_message12(z: int) -> list[int]:
    if not 1 <= z <= 118:
        raise ValueError("atomic number must be 1..118")
    g = gray_encode(z)
    return [(g >> i) & 1 for i in range(12)]


def leech_addresses() -> list[list[int]]:
    """Twenty-four distinct minimal-vector addresses in integer Leech scale.

    In the common integer-coordinate model, vectors of shape (±4, ±4, 0^22)
    are minimal Leech vectors (Euclidean coordinates are divided by sqrt(8)).
    The first 23 form a star through coordinate 23; the final sign change makes
    the address matrix full rank.  Integer scale is stored for exactness.
    """
    out = []
    for i in range(23):
        v = [0] * 24
        v[i] = v[23] = 4
        out.append(v)
    v = [0] * 24
    v[0], v[23] = 4, -4
    out.append(v)
    return out


def hamming(a: list[int], b: list[int]) -> int:
    return sum(x != y for x, y in zip(a, b))


def parse_value(field: str, raw: str):
    if raw == "":
        return None
    if field in UNITS or field in ("YearDiscovered", "Period", "Group"):
        try:
            return float(raw)
        except ValueError:
            pass
    return raw


def exact_audit() -> dict:
    addrs = leech_addresses()
    msgs = [gray_message12(z) for z in range(1, 119)]
    words = [base.golay_encode(m) for m in msgs]
    binary = [base.message12(z) for z in range(1, 119)]
    binary_words = [base.golay_encode(m) for m in binary]
    return {
        "schema_version": 2,
        "element_count": 118,
        "gray_round_trips": sum(gray_decode(gray_encode(z)) == z for z in range(1, 119)),
        "distinct_gray_messages": len({tuple(x) for x in msgs}),
        "distinct_golay_words": len({tuple(x) for x in words}),
        "consecutive_message_hamming": {
            "binary_mean": statistics.fmean(hamming(binary[i], binary[i + 1]) for i in range(117)),
            "gray_mean": statistics.fmean(hamming(msgs[i], msgs[i + 1]) for i in range(117)),
            "gray_min": min(hamming(msgs[i], msgs[i + 1]) for i in range(117)),
            "gray_max": max(hamming(msgs[i], msgs[i + 1]) for i in range(117)),
        },
        "consecutive_golay_hamming": {
            "binary_mean": statistics.fmean(hamming(binary_words[i], binary_words[i + 1]) for i in range(117)),
            "gray_mean": statistics.fmean(hamming(words[i], words[i + 1]) for i in range(117)),
            "gray_min": min(hamming(words[i], words[i + 1]) for i in range(117)),
            "gray_max": max(hamming(words[i], words[i + 1]) for i in range(117)),
        },
        "address_count": len(addrs),
        "distinct_addresses": len({tuple(v) for v in addrs}),
        "address_squared_norm_integer_scale": sorted({sum(x * x for x in v) for v in addrs}),
        "address_squared_norm_leech_scale": sorted({sum(x * x for x in v) / 8 for v in addrs}),
        "address_matrix_full_rank": matrix_rank([[float(x) for x in v] for v in addrs]) == 24,
        "mog_is_permutation": sorted(base.MOG_GRID_BITS) == list(range(24)),
        "note": "Gray locality is exact before Golay encoding. The error-correcting map necessarily expands distinct messages to distance at least 8; it does not preserve one-bit adjacency."
    }


def matrix_rank(a: list[list[float]], eps: float = 1e-9) -> int:
    a = [r[:] for r in a]
    rows, cols, rank = len(a), len(a[0]), 0
    for c in range(cols):
        pivot = next((r for r in range(rank, rows) if abs(a[r][c]) > eps), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        q = a[rank][c]
        a[rank] = [x / q for x in a[rank]]
        for r in range(rows):
            if r != rank:
                q = a[r][c]
                a[r] = [x - q * y for x, y in zip(a[r], a[rank])]
        rank += 1
    return rank


def build() -> None:
    rows = base.read_and_normalize()
    # Re-read generated rows so Period and Group are included.
    with base.PROCESSED.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    addrs = leech_addresses()
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Element Data Object v2",
        "schema_version": 2,
        "identity_rule": "12-bit reflected Gray code of atomic number, then systematic extended binary Golay [24,12,8]",
        "bit_order": "least-significant first before MOG permutation",
        "mog_grid_bits": list(base.MOG_GRID_BITS),
        "leech_address_model": {
            "description": "24 fixed minimal vectors in the integer-coordinate model; divide coordinates by sqrt(8)",
            "addresses_integer_scale": addrs,
            "squared_norm_after_scaling": 4,
        },
        "channel_cells": CHANNEL_CELLS,
        "units": UNITS,
        "source": "data/raw/pubchem_periodic_table.csv; details and checksum in data/SOURCES.md",
        "semantics": "The codeword identifies the subject. Typed channels carry observations without lossy bit packing. A channel's cell/address supplies a geometric semantic coordinate, not a physical causal claim.",
    }
    SCHEMA.parent.mkdir(parents=True, exist_ok=True)
    SCHEMA.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for row in rows:
            z = int(row["AtomicNumber"])
            msg = gray_message12(z)
            cw = base.golay_encode(msg)
            channels = {}
            for field, cell in CHANNEL_CELLS.items():
                value = parse_value(field, row[field])
                channels[field] = {
                    "value": value,
                    "missing": value is None,
                    "unit": UNITS.get(field),
                    "uncertainty": None,
                    "conditions": None,
                    "provenance": {"dataset": "PubChem Periodic Table snapshot", "field": field},
                    "mog_cell": cell,
                    "leech_address": cell,
                }
            obj = {
                "schema_version": 2,
                "subject": {"kind": "chemical_element", "atomic_number": z,
                            "symbol": row["Symbol"], "name": row["Name"]},
                "identity": {"gray_integer": gray_encode(z), "message_bits": msg,
                             "golay_codeword": cw, "mog_grid": base.mog_bits(cw)},
                "channels": channels,
                "provenance": {"dataset": "PubChem Periodic Table snapshot", "source_record_atomic_number": z},
            }
            f.write(json.dumps(obj, separators=(",", ":")) + "\n")
    RESULT.parent.mkdir(exist_ok=True)
    RESULT.write_text(json.dumps(exact_audit(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
    print(RESULT.read_text(), end="")

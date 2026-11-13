#!/usr/bin/env python3
"""D2 ablation gate: regenerate the Δ cards and reproduce their certificates.

Run without pytest: ``python3 tests/test_ablation.py``.

The gate deletes every generated card, rebuilds it from its principle plus the
declared executable operator chain, swaps the rebuilt registry into the live
retrieval/validation path, and checks that the four exact sum/difference
certificates are byte-for-byte identical to the pre-ablation certificates.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import transfer_engine  # noqa: E402
from cent_compiler import transfer_validation  # noqa: E402
from cent_compiler.mapping import MAPPING_OPERATORS  # noqa: E402
from cent_compiler.mechanisms import (  # noqa: E402
    GENERATED_MECHANISM_CARDS,
    INTERPRETATIONS,
    MECHANISM_BY_ID,
    MECHANISM_CARDS,
    _BASE_MECHANISM_CARDS,
    generate_mechanism_card,
)

PASS = 0
FAIL = 0


def expect(condition: bool, message: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ok   {message}")
    else:
        FAIL += 1
        print(f"  FAIL {message}")


def _rebuild_registry() -> tuple:
    generated_ids = {card.id for card in GENERATED_MECHANISM_CARDS}
    remaining = tuple(
        card for card in MECHANISM_CARDS if card.id not in generated_ids
    )
    regenerated = tuple(
        generate_mechanism_card(interpretation)
        for interpretation in INTERPRETATIONS
    )
    return (*remaining[:3], *regenerated, *remaining[3:])


def _certificate_signature(mechanism: str, operation: str) -> dict:
    payload = transfer_validation.validate_transfer(
        operation, mechanism_id=mechanism
    )
    return {
        "ok": payload["ok"],
        "status": payload["status"],
        "certificate": payload["certificate"],
        "metrics": payload["metrics"],
        "vectors": payload["vectors"],
        "validated_candidate": payload["validated_candidate"],
    }


def main() -> int:
    print("=" * 78)
    print("D2 ABLATION GATE — GENERATED Δ CARDS AND CERTIFICATE PARITY")
    print("=" * 78)

    generated_ids = {card.id for card in GENERATED_MECHANISM_CARDS}
    base_ids = [card.id for card in _BASE_MECHANISM_CARDS]
    live_ids = [card.id for card in MECHANISM_CARDS]

    expect(
        generated_ids
        == {"opamp-summing", "fluid-continuity", "log-domain-arithmetic"}
        and not generated_ids & set(base_ids)
        and len(base_ids) == 8
        and len(live_ids) == 10,
        "the hand-authored registry has eight principles and the live registry adds three generated cards",
    )
    expect(
        live_ids[:3] == ["delta-sigma-error-feedback", "log-domain-sqrt", "kcl-conservation"]
        and live_ids[3:6]
        == ["opamp-summing", "fluid-continuity", "log-domain-arithmetic"]
        and live_ids[6:]
        == [
            "cam-profile",
            "orifice-pressure-flow",
            "pll-phase-tracking",
            "threshold-comparator",
        ]
        and MECHANISM_BY_ID["threshold-comparator"].supported_operations
        == ("sign",),
        "generated cards occupy the original op-amp and fluid positions",
    )
    expect(
        all(
            MECHANISM_BY_ID[card_id].principle_id
            == ("transcendental-identity" if card_id == "log-domain-arithmetic" else "kcl-conservation")
            for card_id in generated_ids
        )
        and MECHANISM_BY_ID["fluid-continuity"].operators
        == ("effort-flow-duality", "composition")
        and MECHANISM_BY_ID["opamp-summing"].operators
        == ("scale-offset", "composition")
        and MECHANISM_BY_ID["log-domain-arithmetic"].operators
        == ("composition",),
        "all generated cards name their principle and executable operator chain",
    )

    rebuilt = _rebuild_registry()
    expect(
        [card.as_dict() for card in rebuilt]
        == [card.as_dict() for card in MECHANISM_CARDS],
        "deleting and regenerating both generated cards reconstructs the live registry exactly",
    )

    bad_calls = 0
    good_calls = 0
    for operator in MAPPING_OPERATORS:
        if operator.check({}):
            bad_calls += 1
        try:
            operator.apply({})
        except ValueError:
            good_calls += 1
        else:
            bad_calls += 1
    expect(
        bad_calls == 0 and good_calls == len(MAPPING_OPERATORS),
        "every mapping operator refuses an unmet precondition instead of applying",
    )

    models = {
        "identity": {"operation": "sum"},
        "scale-offset": {
            "scale": 2,
            "offset": 0,
            "target_units": "normalized voltage",
            "target_carrier": "normalized voltage",
        },
        "effort-flow-duality": {
            "target_domain": "fluidics",
            "target_carrier": "normalized volumetric flow",
            "duality": {
                "source_effort": "voltage",
                "source_flow": "current",
                "target_effort": "pressure",
                "target_flow": "volumetric flow",
            },
        },
        "state-transform": {"stateful": True, "state": 3},
        "sampling-quantization": {
            "primitive_chain": ("quantize",),
            "levels": 8,
        },
        "feedback-equivalence": {"feedback": True},
        "composition": {"primitive_chain": ("sum", "neg")},
    }
    applied = 0
    for operator in MAPPING_OPERATORS:
        model = models[operator.id]
        if operator.check(model):
            applied += int(bool(operator.apply(model)))
    expect(
        applied == len(MAPPING_OPERATORS),
        "every mapping operator checks and applies a declared model",
    )

    # Build all four certificates before the registry is replaced.
    baseline_keys = (
        ("fluid-continuity", "sum"),
        ("fluid-continuity", "difference"),
        ("opamp-summing", "sum"),
        ("opamp-summing", "difference"),
    )
    baseline = {
        key: _certificate_signature(*key)
        for key in baseline_keys
    }

    original_cards = transfer_engine.MECHANISM_CARDS
    original_engine_by_id = transfer_engine.MECHANISM_BY_ID
    original_validation_by_id = transfer_validation.MECHANISM_BY_ID
    try:
        transfer_engine.MECHANISM_CARDS = rebuilt
        transfer_engine.MECHANISM_BY_ID = {
            card.id: card for card in rebuilt
        }
        transfer_validation.MECHANISM_BY_ID = transfer_engine.MECHANISM_BY_ID
        rebuilt_payloads = {
            key: _certificate_signature(*key)
            for key in baseline_keys
        }
    finally:
        transfer_engine.MECHANISM_CARDS = original_cards
        transfer_engine.MECHANISM_BY_ID = original_engine_by_id
        transfer_validation.MECHANISM_BY_ID = original_validation_by_id

    for key in baseline_keys:
        expect(
            baseline[key] == rebuilt_payloads[key],
            f"rebuilt {key[0]} {key[1]} certificate is identical to the pre-ablation certificate",
        )

    expect(
        all(payload["certificate"]["status"] == "pass" for payload in baseline.values())
        and all(payload["ok"] for payload in baseline.values()),
        "all four regenerated routings still pass their fixed vectors",
    )

    print()
    print(f"ABLATION: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

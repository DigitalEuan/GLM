#!/usr/bin/env python3
"""D5 gate: generated negatives, witness pairs and derived obligations."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import refutation
from cent_compiler.transfer_evaluation import NEGATIVE_CONTROLS

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


def _rejects(callable_) -> bool:
    try:
        callable_()
    except (KeyError, ValueError):
        return True
    return False


def main() -> int:
    print("=" * 78)
    print("D5 TIER-D REFUTATION GATE")
    print("=" * 78)

    ledger = refutation.build_ledger()
    summary = ledger.get("summary") or {}
    expect(
        ledger.get("schema") == "cent-tier-d-ledger/1"
        and ledger.get("generator") == "tier-d-witness-search"
        and ledger.get("ok") is True,
        "the Tier-D ledger is built from declared instances and witness pairs",
    )
    expect(
        summary.get("instances") == 13
        and summary.get("generated_negatives") == 8
        and summary.get("hand_declared_negatives") == len(NEGATIVE_CONTROLS) == 6
        and summary.get("exceeds_hand_declared") is True,
        "generated negatives exceed the six hand-declared negatives (8 > 6)",
    )

    witnesses = ledger.get("negatives") or []
    expect(
        len(witnesses) == 8
        and len({witness.get("id") for witness in witnesses}) == 8
        and all(witness.get("schema") == "cent-tier-d-witness/1" for witness in witnesses),
        "every generated negative has a unique witness record",
    )
    expect(
        all(
            witness.get("signature")
            and (witness.get("witness") or {}).get("left")
            != (witness.get("witness") or {}).get("right")
            and (witness.get("witness") or {}).get("left_value")
            != (witness.get("witness") or {}).get("right_value")
            and (witness.get("witness") or {}).get("probe")
            for witness in witnesses
        ),
        "each witness pair shares a signature and differs on a named observable",
    )
    expect(
        all("map through" in witness.get("conclusion", "") for witness in witnesses),
        "each witness states the signature-only map refutation, not a global impossibility",
    )

    q_witness = next(
        witness for witness in witnesses if witness.get("retire_lead") == "nematic-q-tensor-bounding-box"
    )
    q_body = q_witness.get("witness") or {}
    expect(
        q_body.get("left_value") == "2/1"
        and q_body.get("right_value") == "66/25"
        and q_body.get("probe") == "area"
        and "q-invariant:S=1" in q_witness.get("signature")
        and "q-invariant:tr(Q^2)=2/1" in q_witness.get("signature")
        and "q-invariant:det(Q)=-1/1" in q_witness.get("signature"),
        "the Q-tensor witness reproduces the exact scalar-invariant/orientation separation",
    )
    recorded = json.loads(
        (ROOT / "docs/hypothesis-resolutions/nematic-q-tensor-bounding-box.json").read_text()
    )
    expect(
        ledger.get("retired_leads")
        == [
            {
                "lead_id": "nematic-q-tensor-bounding-box",
                "decision": "retire",
                "witness": q_witness.get("id"),
                "reason": q_witness.get("conclusion"),
            }
        ]
        and recorded.get("status") == "retired"
        and recorded.get("decision") == "retire",
        "the recorded Q-tensor retirement is reproduced from its witness pair",
    )

    carry_witness = next(
        witness for witness in witnesses if "two-tick" in witness.get("id", "")
    )
    carry_body = carry_witness.get("witness") or {}
    expect(
        carry_body.get("probe") == "code@1/2"
        and carry_body.get("left_value") == "1,1,1,0,0,0"
        and carry_body.get("right_value") == "0,1,0,1,0,1",
        "the carry witness preserves the exact two-tick versus one-tick code difference",
    )
    junction_witnesses = [
        witness for witness in witnesses if "kcl-conservation" in witness.get("id", "")
    ]
    expect(
        len(junction_witnesses) == 2
        and {witness["witness"]["right"] for witness in junction_witnesses}
        == {"opamp-summing", "fluid-continuity"}
        and any(
            witness["witness"]["left_value"] == "current"
            and witness["witness"]["right_value"] == "voltage"
            for witness in junction_witnesses
        ),
        "the junction witnesses separate current, voltage and flow carriers",
    )
    expect(
        any(
            witness["witness"]["probe"] == "operation"
            and witness["witness"]["left_value"] == "sqrt"
            and witness["witness"]["right_value"] == "arithmetic"
            for witness in witnesses
        )
        and any(
            witness["witness"]["probe"] == "law"
            and witness["witness"]["left_value"] == "a*b"
            and witness["witness"]["right_value"] == "a/b"
            for witness in witnesses
        ),
        "the log-domain and exact-arithmetic witnesses separate their required laws",
    )

    obligations = ledger.get("obligations") or []
    contract_obligations = [
        obligation for obligation in obligations if obligation.get("kind") in {"bounded-state", "mean-reconstruction"}
    ]
    witness_obligations = [
        obligation for obligation in obligations if obligation.get("kind") == "observable-separation"
    ]
    expect(
        len(contract_obligations) == 2
        and all(obligation.get("authored") is False for obligation in contract_obligations)
        and any(
            "signature.outputs.code" in obligation.get("derived_from", "")
            and "bounded sequence" in obligation.get("derived_from", "")
            for obligation in contract_obligations
        ),
        "the bounded-state and mean-reconstruction obligations are derived from the contract",
    )
    expect(
        len(witness_obligations) == len(witnesses)
        and all(obligation.get("authored") is False for obligation in witness_obligations)
        and all(
            any(
                witness.get("id") in obligation.get("derived_from", "")
                for witness in witnesses
            )
            for obligation in witness_obligations
        ),
        "every witness derives its own observable-separation test obligation",
    )
    expect(
        summary.get("derived_obligations") == 10
        and summary.get("authored_obligations") == 0
        and all(obligation.get("authored") is False for obligation in obligations),
        "at least one test obligation is derived rather than authored (all ten are derived)",
    )

    same_observable = (
        refutation.WitnessInstance(
            "left",
            "probe",
            ("shared:true",),
            {"value": "1/2"},
            ("test",),
        ),
        refutation.WitnessInstance(
            "right",
            "probe",
            ("shared:true",),
            {"value": "1/2"},
            ("test",),
        ),
    )
    separated = (
        refutation.WitnessInstance(
            "left",
            "probe",
            ("shared:true",),
            {"value": "1/2"},
            ("test",),
        ),
        refutation.WitnessInstance(
            "right",
            "probe",
            ("shared:true",),
            {"value": "1/3"},
            ("test",),
        ),
    )
    expect(
        refutation.generate_witnesses(same_observable) == ()
        and len(refutation.generate_witnesses(separated)) == 1,
        "the search refuses equal observables and emits a witness only on a real separation",
    )
    def duplicate_ids() -> None:
        refutation.generate_witnesses(
            (
                refutation.WitnessInstance(
                    "same", "probe", ("shared:true",), {"value": "1"}, ("test",)
                ),
                refutation.WitnessInstance(
                    "same", "probe", ("shared:true",), {"value": "2"}, ("test",)
                ),
            )
        )

    expect(
        _rejects(duplicate_ids),
        "the witness corpus refuses duplicate instance ids",
    )
    expect(
        _rejects(lambda: refutation.derive_contract_obligations("no_such_operation")),
        "obligation derivation refuses an unknown operation contract",
    )

    cli = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "refute", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    cli_payload = json.loads(cli.stdout) if cli.returncode == 0 else {}
    expect(
        cli.returncode == 0
        and cli_payload.get("schema") == "cent-tier-d-ledger/1"
        and cli_payload.get("ok") is True
        and len(cli_payload.get("negatives") or ()) == 8,
        "cent refute emits the Tier-D ledger",
    )

    with tempfile.TemporaryDirectory() as tmp:
        target = pathlib.Path(tmp) / "negatives.json"
        write_cli = subprocess.run(
            [sys.executable, str(ROOT / "cent"), "refute", "--write", str(target), "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        expect(
            write_cli.returncode == 0
            and target.is_file()
            and json.loads(target.read_text()).get("schema") == "cent-tier-d-ledger/1",
            "cent refute writes a portable ledger artifact",
        )

    demo = subprocess.run(
        [sys.executable, str(ROOT / "review" / "refuter_demo.py"), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    demo_payload = json.loads(demo.stdout) if demo.returncode == 0 else {}
    expect(
        demo.returncode == 0
        and demo_payload.get("summary", {}).get("generated_negatives") == 8,
        "the review/refuter_demo.py working specification runs the same search",
    )

    print()
    print(f"{PASS}/{PASS + FAIL} checks passed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

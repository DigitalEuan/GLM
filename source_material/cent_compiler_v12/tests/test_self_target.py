#!/usr/bin/env python3
"""D4 gate: the compiler as a measured target.

Run without pytest: ``python3 tests/test_self_target.py``.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import proposals as proposal_module
from cent_compiler import self_target
from cent_compiler.exact import CentError
from cent_compiler.proposals import REVIEW_STATES
from cent_compiler.quantized_carry_floor import (
    CONTRACT,
    check_contract,
    floor_carry_sequence,
    line_walk,
)
from cent_compiler.self_oracle import certify

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
    except (CentError, ValueError):
        return True
    return False


def main() -> int:
    print("=" * 78)
    print("D4 SELF-TARGET UTILITY GATE")
    print("=" * 78)

    contract = check_contract(max_dx=16)
    expect(
        CONTRACT["id"] == "quantized_carry_floor"
        and "one tick" in CONTRACT["timing"]
        and CONTRACT["provenance"] == "docs/evidence/bresenham/check.py",
        "the Bresenham proof declares the one-tick floor contract it actually satisfies",
    )
    expect(
        contract["ok"]
        and contract["trials"] == 152
        and contract["passed"] == 152
        and contract["failed"] == 0,
        "the promoted floor contract agrees with every one-tick walk (152/152)",
    )
    expect(
        floor_carry_sequence(Fraction(1, 2), 6) == line_walk(6, 3)
        and line_walk(6, 3) == (0, 1, 0, 1, 0, 1)
        and floor_carry_sequence(Fraction(1), 3) == (1, 1, 1),
        "the floor contract is the exact one-tick walk, not the existing two-tick code",
    )
    expect(
        _rejects(lambda: floor_carry_sequence(Fraction(3, 2), 4))
        and _rejects(lambda: floor_carry_sequence(Fraction(-1, 2), 4)),
        "the floor contract refuses inputs outside its declared domain",
    )

    carry = self_target.measure_carry_agreement()
    expect(
        carry["baseline_value"] == "32/152"
        and carry["candidate_value"] == "152/152"
        and carry["ok"],
        "the one-tick contract beats the existing two-tick target (32/152 -> 152/152)",
    )
    expect(
        len(carry["mismatches"]) == 120
        and all(row["candidate"] == row["oracle"] for row in carry["mismatches"]),
        "every carry mismatch belongs to the baseline, not the promoted contract",
    )

    runtime = self_target.measure_runtime_faults()
    static_hits = sum(row["static_topology_audit"] for row in runtime["rows"])
    semantic = [row for row in runtime["rows"] if row["kind"] == "semantic"]
    expect(
        runtime["trials"] == 12
        and runtime["baseline_value"] == "4/12"
        and runtime["candidate_value"] == "12/12"
        and runtime["ok"],
        "runtime invariants lift injected-fault detection from 4/12 to 12/12",
    )
    expect(
        static_hits == 4
        and len(semantic) == 8
        and all(not row["static_topology_audit"] for row in semantic)
        and all(row["runtime_invariant"] for row in semantic),
        "the static topology audit misses every semantic fault; the runtime check catches all eight",
    )
    expect(
        all(row["oracle_confirmed"] for row in runtime["rows"])
        and len({row["fault"] for row in runtime["rows"]}) == 12,
        "the independent oracle confirms all twelve injected faults are genuine",
    )
    ledger = self_target.build_ledger()
    expect(
        ledger["schema"] == "cent-utility-ledger/1"
        and ledger["ok"]
        and ledger["summary"] == {"records": 2, "adopted": 2, "reverted": 0, "certified": 2},
        "cent-self builds two adopted, certified cent-utility/1 records",
    )
    required = {
        "schema",
        "target_subsystem",
        "baseline_command",
        "candidate_command",
        "metric",
        "baseline_value",
        "candidate_value",
        "delta",
        "trials",
        "seed",
        "independent_oracle",
        "adoption_state",
        "rollback",
    }
    expect(
        all(required.issubset(record) for record in ledger["records"])
        and all(record["schema"] == "cent-utility/1" for record in ledger["records"]),
        "each record carries every field the directive requires",
    )
    expect(
        all(
            record["certificate"]["status"] == "pass"
            and record["certificate"]["candidate_on_certificate_path"] is False
            and record["certificate"]["oracle"] == "cent-utility-oracle/1"
            for record in ledger["records"]
        ),
        "R5: the independent oracle issues the certificate off the candidate path",
    )
    expect(
        ledger["records"][0]["baseline_value"] == "32/152"
        and ledger["records"][0]["candidate_value"] == "152/152"
        and ledger["records"][0]["delta"] == "120/152"
        and ledger["records"][1]["baseline_value"] == "4/12"
        and ledger["records"][1]["candidate_value"] == "12/12"
        and ledger["records"][1]["delta"] == "8/12",
        "the adopted deltas are the measured non-zero deltas, not asserted constants",
    )

    carry_rollback = self_target.rollback(self_target.CARRY_ID)
    runtime_rollback = self_target.rollback(self_target.RUNTIME_ID)
    expect(
        carry_rollback["adoption_state"] == "reverted"
        and carry_rollback["rollback_applied"] is True
        and carry_rollback["rollback_evidence"]["verified"] is True
        and carry_rollback["rollback_evidence"]["restored_value"] == "32/152",
        "the carry transfer has a working rollback to the two-tick baseline",
    )
    expect(
        runtime_rollback["adoption_state"] == "reverted"
        and runtime_rollback["rollback_applied"] is True
        and runtime_rollback["rollback_evidence"]["verified"] is True
        and runtime_rollback["rollback_evidence"]["restored_value"] == "4/12",
        "the runtime transfer has a working rollback to static topology audit",
    )
    expect(
        self_target.adopt(self_target.RUNTIME_ID)["adoption_state"] == "adopted"
        and self_target.adopt(self_target.CARRY_ID)["adoption_state"] == "adopted",
        "both transfers can be re-adopted after rollback",
    )

    record = ledger["records"][1]
    bad_delta = dict(record, delta="9/12")
    expect(
        _rejects(lambda: self_target.UtilityRecord(
            id="bad",
            title="bad",
            target_subsystem="bad",
            baseline_command="a",
            candidate_command="b",
            metric="m",
            baseline_value="4/12",
            candidate_value="12/12",
            delta="9/12",
            trials=12,
            seed=0,
            independent_oracle="oracle",
            adoption_state="adopted",
            rollback="revert",
            rollback_evidence={"verified": True},
        ))
        and _rejects(lambda: self_target.UtilityRecord(
            id="bad",
            title="bad",
            target_subsystem="bad",
            baseline_command="a",
            candidate_command="b",
            metric="m",
            baseline_value="4/12",
            candidate_value="12/12",
            delta="8/12",
            trials=12,
            seed=0,
            independent_oracle="oracle",
            adoption_state="claimed",
            rollback="revert",
            rollback_evidence={"verified": True},
        )),
        "utility records refuse a bad delta and an unknown adoption state",
    )
    expect(
        certify(
            bad_delta,
            {
                "faults_confirmed": True,
                "rollback_verified": True,
                "candidate_detects_all": True,
            },
        )["status"] == "gap",
        "the oracle refuses a certificate whose delta does not match its values",
    )

    review_help = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "review", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    self_cli = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "self", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    alias_cli = subprocess.run(
        [sys.executable, str(ROOT / "cent-self"), "--record", self_target.RUNTIME_ID, "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    baseline_cli = subprocess.run(
        [sys.executable, str(ROOT / "cent-self"), "--baseline", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    self_payload = json.loads(self_cli.stdout) if self_cli.returncode == 0 else {}
    alias_payload = json.loads(alias_cli.stdout) if alias_cli.returncode == 0 else {}
    baseline_payload = (
        json.loads(baseline_cli.stdout) if baseline_cli.returncode == 0 else {}
    )
    with tempfile.TemporaryDirectory() as tmp:
        bundle = proposal_module.build_bundle("sqrt")
        proposal_module.write_bundle(bundle, pathlib.Path(tmp) / "proposals")
        proposal_id = bundle["proposals"][0]["id"]
        adopted_event = proposal_module.record_review(
            pathlib.Path(tmp) / "proposals",
            proposal_id,
            state="adopted",
            reviewer="self-gate",
            note="Utility record adopted after the declared measurement.",
        )
        reverted_event = proposal_module.record_review(
            pathlib.Path(tmp) / "proposals",
            proposal_id,
            state="reverted",
            reviewer="self-gate",
            note="Rollback exercised; proposal returns to unreviewed evidence.",
        )
        review_history = (reverted_event.get("event") or {}).get("sequence")
    expect(
        {"adopted", "reverted"}.issubset(REVIEW_STATES)
        and "adopted" in review_help.stdout
        and "reverted" in review_help.stdout
        and adopted_event.get("state") == "adopted"
        and reverted_event.get("prior_state") == "adopted"
        and reverted_event.get("state") == "reverted"
        and review_history == 2,
        "the durable review ledger records adopted and reverted decisions",
    )
    expect(
        self_cli.returncode == 0
        and self_payload.get("ok") is True
        and len(self_payload.get("records") or ()) == 2
        and alias_cli.returncode == 0
        and alias_payload.get("id") == self_target.RUNTIME_ID
        and alias_payload.get("schema") == "cent-utility/1"
        and baseline_cli.returncode == 0
        and baseline_payload.get("schema") == "cent-utility-baseline/1"
        and [row.get("value") for row in baseline_payload.get("records") or ()]
        == ["32/152", "4/12"],
        "cent self, cent-self and the baseline command all emit their measurements",
    )

    with tempfile.TemporaryDirectory() as tmp:
        written = pathlib.Path(tmp) / "utility.json"
        write_cli = subprocess.run(
            [sys.executable, str(ROOT / "cent-self"), "--write", str(written), "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        expect(
            write_cli.returncode == 0
            and written.is_file()
            and json.loads(written.read_text())["schema"] == "cent-utility-ledger/1",
            "cent-self writes a portable cent-utility-ledger/1 artifact",
        )

    print()
    print(f"{PASS}/{PASS + FAIL} checks passed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

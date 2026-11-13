#!/usr/bin/env python3
"""Regression checks for the hypothesis-to-mechanism promotion gate.

Run without pytest: ``python3 tests/test_hypothesis_promotion.py``.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import promotion, transfer_validation  # noqa: E402

PASS = 0
FAIL = 0
LEAD = "bresenham-quantized-carry"
MECHANISM = "delta-sigma-error-feedback"
OPERATION = "quantized_carry"
TARGET = "glm-reference"


def expect(condition: bool, message: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ok   {message}")
    else:
        FAIL += 1
        print(f"  FAIL {message}")


def _review_payload(digest: str, **overrides) -> dict:
    payload = {
        "schema": promotion.REVIEW_SCHEMA,
        "lead_id": LEAD,
        "operation": OPERATION,
        "mechanism": MECHANISM,
        "target": TARGET,
        "state": "accepted",
        "reviewer": "reviewer-a",
        "note": "Declared card, contract and reference target test accepted.",
        "reviewed_at": "2026-11-13T00:00:00Z",
        "certificate_sha256": digest,
    }
    payload.update(overrides)
    return payload


def _refused(call, text: str) -> tuple[bool, str]:
    try:
        call()
    except (KeyError, OSError, ValueError) as exc:
        return text in str(exc), str(exc)
    return False, "no exception"


def main() -> int:
    print("=" * 78)
    print("HYPOTHESIS PROMOTION GATE")
    print("=" * 78)

    certificate = transfer_validation.validate_transfer(
        OPERATION, mechanism_id=MECHANISM
    )
    expect(
        certificate.get("status") == "pass"
        and (certificate.get("certificate") or {}).get("schema")
        == transfer_validation.CERTIFICATE_SCHEMA
        and len(certificate.get("vectors") or ()) == 3,
        "the declared reference target test passes its fixed vectors",
    )

    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        certificate_path = root / "target-certificate.json"
        certificate_path.write_text(json.dumps(certificate), encoding="utf-8")
        digest = hashlib.sha256(certificate_path.read_bytes()).hexdigest()
        review_path = root / "promotion-review.json"
        review_path.write_text(
            json.dumps(_review_payload(digest)), encoding="utf-8"
        )

        promoted = promotion.build_promotion(
            LEAD, MECHANISM, certificate_path, review_path
        )
        bundle = promoted.get("proposal_bundle") or {}
        proposals = bundle.get("proposals") or ()
        proposal = proposals[0] if proposals else {}
        expect(
            promoted.get("schema") == promotion.SCHEMA
            and promoted.get("status") == "pass"
            and promoted.get("gate") == "pass"
            and promoted.get("lead", {}).get("id") == LEAD
            and promoted.get("mechanism", {}).get("id") == MECHANISM
            and promoted.get("operation", {}).get("id") == OPERATION,
            "a declared lead/card/contract selection reaches the gate",
        )
        expect(
            len(proposals) == 1
            and proposal.get("mechanism", {}).get("id") == MECHANISM
            and proposal.get("operation", {}).get("id") == OPERATION
            and promoted.get("proposal_ids") == [proposal.get("id")],
            "the gate creates one proposal for the selected mechanism only",
        )
        expect(
            [check.get("status") for check in promoted.get("checks") or ()]
            == ["pass"] * 6
            and promoted.get("mechanism", {}).get("overlap")
            == ["accum", "delay", "quantize"],
            "all six gate checks pass with the declared structural overlap",
        )
        expect(
            proposal.get("status") == "unvalidated"
            and (proposal.get("review") or {}).get("state") == "unreviewed"
            and (proposal.get("promotion") or {}).get("gate") == "pass"
            and (bundle.get("promotion") or {}).get("gate") == "pass",
            "promotion admits the proposal without validating it or pre-reviewing it",
        )
        expect(
            promoted.get("target_test", {}).get("sha256") == digest
            and promoted.get("review", {}).get("certificate_sha256") == digest
            and promoted.get("target_test", {}).get("evidence_level")
            == "target-simulated",
            "the gate pins the target certificate digest and evidence level",
        )

        written = promotion.write_promotion(promoted, root / "out")
        out = root / "out"
        manifest = json.loads((out / "promotion.json").read_text())
        expect(
            {"promotion.json", "promotion.md"} <= {path.name for path in written}
            and (out / "proposals" / "index.json").exists()
            and (out / "proposals" / (proposal.get("id", "") + ".json")).exists()
            and manifest.get("artifacts", {}).get("promotion.md") == "promotion.md",
            "the promotion output contains the manifest and proposal bundle",
        )

        cli = subprocess.run(
            [
                sys.executable,
                str(ROOT / "cent"),
                "hypothesis",
                "--promote",
                LEAD,
                "--mechanism",
                MECHANISM,
                "--certificate",
                str(certificate_path),
                "--review",
                str(review_path),
                "--out",
                str(root / "cli-out"),
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
        cli_payload = json.loads(cli.stdout) if cli.returncode == 0 else {}
        expect(
            cli.returncode == 0
            and cli_payload.get("schema") == promotion.SCHEMA
            and (root / "cli-out" / "promotion.json").exists()
            and (root / "cli-out" / "proposals" / "index.json").exists(),
            "the hypothesis promotion CLI writes the same gated artifacts",
        )

        unsupported = _refused(
            lambda: promotion.build_promotion(
                LEAD, "kcl-conservation", certificate_path, review_path
            ),
            "does not declare support",
        )
        expect(
            unsupported[0],
            "a declared card that does not support the operation is refused",
        )

        sqrt_certificate = transfer_validation.validate_transfer("sqrt")
        sqrt_path = root / "sqrt-certificate.json"
        sqrt_path.write_text(json.dumps(sqrt_certificate), encoding="utf-8")
        wrong_operation = _refused(
            lambda: promotion.build_promotion(
                LEAD, MECHANISM, sqrt_path, review_path
            ),
            "does not match",
        )
        expect(
            wrong_operation[0],
            "a target certificate for another operation is refused",
        )

        bad_digest = root / "bad-digest-review.json"
        bad_digest.write_text(
            json.dumps(_review_payload("0" * 64)), encoding="utf-8"
        )
        bad_review = _refused(
            lambda: promotion.build_promotion(
                LEAD, MECHANISM, certificate_path, bad_digest
            ),
            "certificate_sha256",
        )
        expect(bad_review[0], "a review that does not pin the certificate is refused")

        rejected_path = root / "rejected-review.json"
        rejected_path.write_text(
            json.dumps(_review_payload(digest, state="rejected")),
            encoding="utf-8",
        )
        rejected = _refused(
            lambda: promotion.build_promotion(
                LEAD, MECHANISM, certificate_path, rejected_path
            ),
            "state must be one of",
        )
        expect(rejected[0], "a non-accepted review is refused")

        no_contract = _refused(
            lambda: promotion.build_promotion(
                "nematic-q-tensor-bounding-box",
                "kcl-conservation",
                certificate_path,
                review_path,
            ),
            "unknown operation contract",
        )
        expect(
            no_contract[0],
            "a lead whose operation has no production contract is refused",
        )

        missing_args = subprocess.run(
            [
                sys.executable,
                str(ROOT / "cent"),
                "hypothesis",
                "--promote",
                LEAD,
                "--mechanism",
                MECHANISM,
                "--certificate",
                str(certificate_path),
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        expect(
            missing_args.returncode == 2 and "--review" in missing_args.stderr,
            "the CLI refuses a promotion request without a review artifact",
        )

    print("\n" + "=" * 78)
    if FAIL:
        print(f"HYPOTHESIS PROMOTION: {PASS}/{PASS + FAIL} checks passed, {FAIL} failed")
        return 1
    print(f"HYPOTHESIS PROMOTION: {PASS}/{PASS + FAIL} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

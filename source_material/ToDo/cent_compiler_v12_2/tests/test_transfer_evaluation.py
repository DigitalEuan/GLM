#!/usr/bin/env python3
"""G5b tests for the declared transfer-retrieval evaluation corpus.

Run without pytest: ``python3 tests/test_transfer_evaluation.py``.

These checks measure retrieval against declared mechanism support and negative
controls.  They do not turn declared support into independent ground truth or a
target-validation claim.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import transfer_evaluation as evaluation  # noqa: E402
from cent_compiler.mechanisms import MECHANISM_CARDS  # noqa: E402
from cent_compiler.transfer_engine import OPERATION_BY_ID  # noqa: E402

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


def _no_floats(value) -> bool:
    if isinstance(value, float):
        return False
    if isinstance(value, dict):
        return all(_no_floats(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_no_floats(item) for item in value)
    return True


def main() -> int:
    print("=" * 78)
    print("TRANSFER RETRIEVAL EVALUATION (G5b)")
    print("=" * 78)

    evaluation.validate_corpus()
    positive_operations = {case.operation for case in evaluation.POSITIVE_CASES}
    expect(
        len(evaluation.POSITIVE_CASES) == 4
        and len(evaluation.NEGATIVE_CONTROLS) == 5
        and len(evaluation.UNADAPTED_CASES) == 6
        and len(evaluation.REFUSED_CASES) == 3
        and len(
            {
                case.id
                for case in (
                    *evaluation.POSITIVE_CASES,
                    *evaluation.NEGATIVE_CONTROLS,
                    *evaluation.UNADAPTED_CASES,
                    *evaluation.REFUSED_CASES,
                )
            }
        )
        == 18,
        "the corpus declares four known-valid, five negative, six unadapted and three refused cases",
    )

    declared_support = {
        operation: {
            card.id
            for card in MECHANISM_CARDS
            if operation in card.supported_operations
        }
        for operation in positive_operations
    }
    expect(
        all(
            set(case.expected_mechanisms) == declared_support[case.operation]
            for case in evaluation.POSITIVE_CASES
        )
        and positive_operations == {"sqrt", "sum", "difference", "quantized_carry"},
        "known-valid expectations equal the declared production card support",
    )

    payload = evaluation.evaluate_corpus()
    metrics = payload["metrics"]
    expect(
        payload["ok"] is True
        and payload["schema"] == "cent-transfer-evaluation/1"
        and payload["algorithm"] == "declared-mechanism-corpus/1"
        and metrics["candidate_recall"] == "10/10"
        and metrics["case_recall"] == "4/4"
        and metrics["false_positive_rate"] == "0/5"
        and metrics["negative_control_pass_rate"] == "5/5"
        and metrics["target_pass_rate"] == "8/8"
        and metrics["artifact_count"] == 8
        and metrics["unadapted_candidates"] == 2
        and metrics["unadapted_refusals"] == 2
        and metrics["unadapted_refusal_failures"] == []
        and metrics["retrieval_evidence_completeness"] == "10/10"
        and metrics["target_evidence_completeness"] == "8/8",
        "the evaluation reports recall, false positives, target pass rate and evidence completeness",
    )

    expect(
        all(case["passed"] for case in payload["known_valid"])
        and [case["operation"] for case in payload["known_valid"]]
        == ["sqrt", "sum", "difference", "quantized_carry"]
        and all(
            not case["missing"] and not case["unexpected"]
            for case in payload["known_valid"]
        ),
        "all known-valid cases retrieve exactly their declared mechanisms",
    )

    negative = {case["operation"]: case for case in payload["known_invalid"]}
    expect(
        all(case["passed"] for case in payload["known_invalid"])
        and negative["mult"]["retrieved"] == []
        and negative["log"]["retrieved"] == []
        and negative["exp"]["retrieved"] == []
        and "delta-sigma-error-feedback" not in negative["sqrt"]["retrieved"]
        and negative["quantized_carry"]["retrieved"]
        == ["delta-sigma-error-feedback"],
        "negative controls reject shared-primitive and stateful/feedback lookalikes",
    )

    expect(
        all(case["passed"] for case in payload["unadapted"])
        and {case["operation"] for case in payload["unadapted"]}
        == {"mult", "div", "exp", "log", "reciprocal", "sign"}
        and all(not case["retrieved"] for case in payload["unadapted"]),
        "the six zero-mechanism operations remain explicitly unretrieved",
    )

    refused = {case["operation"]: case for case in payload["refused"]}
    expect(
        all(case["passed"] for case in payload["refused"])
        and set(refused) == {"griess_product", "matrix_vector_product", "track_phase"}
        and all(
            "unknown operation contract" in case["detail"]
            for case in payload["refused"]
        ),
        "unknown operations and a mechanism-only operation are refused, not silently mapped",
    )

    expect(
        len(payload["targets"]) == 8
        and all(row["status"] == "pass" for row in payload["targets"])
        and {
            (row["operation"], row["mechanism"]) for row in payload["targets"]
        }
        == {
            ("sqrt", "log-domain-sqrt"),
            ("sum", "kcl-conservation"),
            ("sum", "fluid-continuity"),
            ("difference", "kcl-conservation"),
            ("difference", "fluid-continuity"),
            ("difference", "opamp-summing"),
            ("sum", "opamp-summing"),
            ("quantized_carry", "delta-sigma-error-feedback"),
        }
        and all(
            row["certificate"] == "pass"
            and row["evidence_level"] == "target-simulated"
            and row["tests"]
            and row["artifact"]
            for row in payload["targets"]
        ),
        "the eight reference adapter pairs pass with target-simulated evidence"
    )

    expect(
        {
            (row["operation"], row["mechanism"])
            for row in payload["unadapted_candidates"]
        }
        == {
            ("sqrt", "cam-profile"),
            ("sqrt", "orifice-pressure-flow"),
        }
        and {
            (row["operation"], row["mechanism"])
            for row in payload["unadapted_refusals"]
        }
        == {
            ("sqrt", "cam-profile"),
            ("sqrt", "orifice-pressure-flow"),
        }
        and all(
            row["rationale"] and row["required_evidence"]
            for row in payload["unadapted_refusals"]
        )
        and all(row["gaps"] for row in payload["unadapted_candidates"])
        and all(
            (row["operation"], row["mechanism"])
            not in {
                (target["operation"], target["mechanism"])
                for target in payload["targets"]
            }
            for row in payload["unadapted_candidates"]
        ),
        "supported-but-untargeted candidates are counted as unadapted with explicit gaps",
    )

    expect(
        metrics["false_positive_candidates"] == []
        and metrics["unlabelled_candidates"] == []
        and metrics["missing_candidates"] == []
        and metrics["negative_control_failures"] == 0
        and metrics["unadapted_retrievals"] == 0
        and all(check["status"] == "pass" for check in payload["checks"]),
        "no candidate is unlabelled and every declared evaluation check passes",
    )

    expect(
        _no_floats(payload)
        and isinstance(metrics["candidate_recall"], str)
        and isinstance(metrics["false_positive_rate"], str)
        and json.loads(json.dumps(payload)) == payload,
        "the evaluation payload is JSON-safe and keeps rates as exact strings",
    )

    cli = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "evaluate", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    cli_payload = json.loads(cli.stdout) if cli.returncode == 0 else {}
    certificate = cli_payload.get("output_certificate") or {}
    expect(
        cli.returncode == 0
        and cli_payload.get("schema") == evaluation.EVALUATION_SCHEMA
        and cli_payload.get("ok") is True
        and certificate.get("subject_schema") == evaluation.EVALUATION_SCHEMA
        and certificate.get("status") == "partial",
        "the evaluation CLI emits the payload and a partial certificate for declared gaps",
    )

    human = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "evaluate"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    expect(
        human.returncode == 0
        and "TRANSFER RETRIEVAL EVALUATION" in human.stdout
        and "Known-valid cases" in human.stdout
        and "Negative controls" in human.stdout
        and "candidate_recall: 10/10" in human.stdout
        and "false_positive_rate: 0/5" in human.stdout
        and "Remaining gaps" in human.stdout
        and "Unadapted candidate refusals" in human.stdout,
        "the human evaluation report shows cases, refusal records, metrics and gaps",
    )

    expect(
        (OPERATION_BY_ID["sqrt"].id, OPERATION_BY_ID["quantized_carry"].id)
        == ("sqrt", "quantized_carry")
        and all(case.operation in OPERATION_BY_ID for case in evaluation.UNADAPTED_CASES)
        and all(case.operation not in OPERATION_BY_ID for case in evaluation.REFUSED_CASES),
        "the corpus keeps production, unadapted and refused operations distinct",
    )

    print("\n" + "=" * 78)
    print(f"TRANSFER RETRIEVAL EVALUATION: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

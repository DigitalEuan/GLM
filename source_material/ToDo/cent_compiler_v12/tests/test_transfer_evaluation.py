#!/usr/bin/env python3
"""D1 tests for provenance-labelled transfer retrieval.

Run without pytest: ``python3 tests/test_transfer_evaluation.py``.

These checks measure the top-three structural ranking against written labels.
They do not turn those labels into independent external truth or a target
validation claim.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import transfer_evaluation as evaluation  # noqa: E402
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
    print("TRANSFER RETRIEVAL EVALUATION (D1)")
    print("=" * 78)

    evaluation.validate_corpus()
    expect(
        len(evaluation.POSITIVE_CASES) == 10
        and len(evaluation.NEGATIVE_CONTROLS) == 6
        and len(evaluation.UNADAPTED_CASES) == 0
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
        == 19,
        "the corpus declares nine positives, six negative controls, one unadapted and three refused cases",
    )

    hypothesis = evaluation.PositiveCase(
        id="exp-provenance-hypothesis",
        operation="exp",
        expected_mechanisms=("log-domain-sqrt",),
        rationale="The log-domain law states the exponential junction computes exp.",
        provenance=("cent_compiler/mechanisms.py",),
    )
    hypothesis.validate()
    expect(
        "log-domain-sqrt" in evaluation.MECHANISM_BY_ID
        and "exp" not in evaluation.MECHANISM_BY_ID["log-domain-sqrt"].supported_operations
        and all(
            set(case.expected_mechanisms)
            <= {card.id for card in evaluation.MECHANISM_BY_ID.values()}
            for case in evaluation.POSITIVE_CASES
        ),
        "positive labels can be authored from provenance without being derived from supported_operations",
    )

    payload = evaluation.evaluate_corpus()
    metrics = payload["metrics"]
    expect(
        payload["ok"] is True
        and payload["certified"] is False
        and payload["schema"] == "cent-transfer-evaluation/2"
        and payload["algorithm"] == "provenance-labelled-top3/1",
        "the D1 payload runs and honestly reports that it is not certified",
    )

    expect(
        metrics["candidate_recall"] == "17/20"
        and metrics["case_recall"] == "7/10"
        and metrics["false_positive_rate"] == "1/6"
        and metrics["negative_control_pass_rate"] == "5/6"
        and metrics["target_pass_rate"] == "16/18"
        and metrics["artifact_count"] == 16
        and metrics["unadapted_candidates"] == 2
        and metrics["unadapted_retrievals"] == 0
        and metrics["unadapted_refusal_failures"] == []
        and metrics["retrieval_evidence_completeness"] == "17/20"
        and metrics["target_evidence_completeness"] == "16/18",
        "the baseline reports the honest D1 recall, negative-control and evidence numbers",
    )

    known = {case["operation"]: case for case in payload["known_valid"]}
    expect(
        known["sqrt"]["missing"] == ["orifice-pressure-flow"]
        and known["sqrt"]["unlabelled"] == ["fluid-continuity"]
        and known["sum"]["missing"] == ["rheology-continuity"]
        and known["difference"]["missing"] == ["rheology-continuity"]
        and not known["sum"]["passed"]
        and known["quantized_carry"]["passed"]
        and known["quantized_carry"]["unlabelled"] == []
        and known["quantized_carry"]["retrieved"]
        == [
            "delta-sigma-error-feedback",
            "mechanics-noise-shaping",
            "rotational-w4-noise-shaping",
        ]
        and all(
            known[op]["passed"]
            for op in ("exp", "log", "mult", "div", "reciprocal", "sign")
        ),
        "top-three retrieval exposes the sqrt misses and the carry extras instead of hiding them",
    )

    negative = {case["id"]: case for case in payload["known_invalid"]}
    expect(
        negative["mult-not-fluid-continuity"]["forbidden_hits"]
        == ["fluid-continuity"]
        and negative["quantized-carry-not-pll"]["forbidden_hits"] == []
        and not negative["mult-not-fluid-continuity"]["passed"]
        and negative["quantized-carry-not-pll"]["passed"]
        and negative["log-not-cam-profile"]["passed"]
        and negative["exp-not-cam-profile"]["passed"]
        and negative["sqrt-not-delta-sigma"]["passed"]
        and negative["mult-not-orifice"]["passed"],
        "negative controls fail only on explicit forbidden hits, not on unlabelled candidates",
    )

    expect(
        payload["unadapted"] == []
        and metrics["unadapted_operations"] == 0
        and metrics["unadapted_retrievals"] == 0,
        "every declared operation now has a mechanism and an executable target adapter",
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
        len(payload["targets"]) == 18
        and all(
            row["status"] == "pass"
            for row in payload["targets"]
            if row["mechanism"] != "rheology-continuity"
        )
        and all(
            row["status"] == "fail"
            for row in payload["targets"]
            if row["mechanism"] == "rheology-continuity"
        )
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
            ("sum", "rheology-continuity"),
            ("difference", "rheology-continuity"),
            ("quantized_carry", "delta-sigma-error-feedback"),
            ("quantized_carry", "mechanics-noise-shaping"),
            ("quantized_carry", "rotational-w4-noise-shaping"),
            ("exp", "log-domain-arithmetic"),
            ("log", "log-domain-arithmetic"),
            ("mult", "log-domain-arithmetic"),
            ("div", "log-domain-arithmetic"),
            ("reciprocal", "log-domain-arithmetic"),
            ("sign", "threshold-comparator"),
        }
        and all(
            row["certificate"] == "pass"
            and row["evidence_level"] == "target-simulated"
            and row["tests"]
            and row["artifact"]
            for row in payload["targets"]
            if row["mechanism"] != "rheology-continuity"
        ),
        "sixteen reference adapter pairs pass target-simulated; rheology ranks "
        "4th behind three equal-scoring junction cards and is a reported miss",
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
        ),
        "the two supported-but-untargeted sqrt candidates keep explicit refusal records",
    )

    expect(
        metrics["triage_candidates"]
        == [
            "div/fluid-continuity",
            "div/kcl-conservation",
            "exp/fluid-continuity",
            "exp/log-domain-sqrt",
            "log/fluid-continuity",
            "log/log-domain-sqrt",
            "mult/fluid-continuity",
            "mult/kcl-conservation",
            "reciprocal/fluid-continuity",
            "reciprocal/kcl-conservation",
            "sign/fluid-continuity",
            "sign/kcl-conservation",
            "sqrt/fluid-continuity",
        ]
        and metrics["false_positive_candidates"]
        == ["mult/fluid-continuity"]
        and metrics["missing_candidates"]
        == [
            "sqrt/orifice-pressure-flow",
            "sum/rheology-continuity",
            "difference/rheology-continuity",
        ],
        "unlabelled candidates enter triage while only forbidden hits are false positives",
    )

    expect(
        any(check["status"] == "gap" for check in payload["checks"])
        and not any(check["name"] == "no unlabelled false positives" for check in payload["checks"])
        and any(check["name"] == "unlabelled-candidate triage" for check in payload["checks"]),
        "the check report records the triage queue instead of calling every extra candidate an error",
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
        and cli_payload.get("certified") is False
        and certificate.get("subject_schema") == evaluation.EVALUATION_SCHEMA
        and certificate.get("status") == "partial",
        "the evaluation CLI emits the uncertified payload and a partial certificate",
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
        and "candidate_recall: 17/20" in human.stdout
        and "false_positive_rate: 1/6" in human.stdout
        and "unlabelled (triage)" in human.stdout
        and "Remaining gaps" in human.stdout
        and "Unadapted candidate refusals" in human.stdout,
        "the human report shows the honest baseline, triage and refusal records",
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

#!/usr/bin/env python3
"""R3 sabotage gate for the D1 retrieval evaluation.

Run without pytest: ``python3 tests/test_evaluation_sabotage.py``.

A headline metric is void if replacing the component it purports to measure with
a constant leaves it unchanged.  D1's candidate set is the top-three structural
ranking, so a constant score must change the retrieved set, the recall, the
negative-control outcome and the triage queue.
"""
from __future__ import annotations

import pathlib
import sys
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import transfer_evaluation as evaluation  # noqa: E402
from cent_compiler.transfer_engine import (  # noqa: E402
    MECHANISM_CARDS,
    RetrievalMatch,
    retrieve,
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


def _constant_score(_operation, _card):
    return RetrievalMatch(score=0, reasons=("sabotaged constant score",))


def main() -> int:
    print("=" * 78)
    print("TRANSFER RETRIEVAL EVALUATION — SABOTAGE GATE")
    print("=" * 78)

    baseline = evaluation.evaluate_corpus()
    with patch("cent_compiler.transfer_engine._score", side_effect=_constant_score):
        sabotaged = evaluation.evaluate_corpus()

    base_metrics = baseline["metrics"]
    bad_metrics = sabotaged["metrics"]

    expect(
        base_metrics["candidate_recall"] == "17/20"
        and bad_metrics["candidate_recall"] == "4/20",
        "constant scoring drops candidate recall from 17/20 to 4/20",
    )
    expect(
        base_metrics["case_recall"] == "7/10"
        and bad_metrics["case_recall"] == "0/10",
        "constant scoring drops known-valid case recall from 7/10 to 0/10",
    )
    expect(
        base_metrics["false_positive_rate"] == "1/6"
        and bad_metrics["false_positive_rate"] == "4/6",
        "constant scoring worsens the negative-control false-positive rate",
    )
    expect(
        base_metrics["target_pass_rate"] == "16/18"
        and bad_metrics["target_pass_rate"] == "3/18",
        "constant scoring also removes executable target candidates",
    )
    expect(
        len(base_metrics["triage_candidates"]) < len(bad_metrics["triage_candidates"])
        and base_metrics["triage_candidates"] != bad_metrics["triage_candidates"],
        "constant scoring changes the triage queue",
    )

    base_failures = {
        case["id"] for case in baseline["known_invalid"] if not case["passed"]
    }
    bad_failures = {
        case["id"] for case in sabotaged["known_invalid"] if not case["passed"]
    }
    expect(
        base_failures == {"mult-not-fluid-continuity"}
        and bad_failures
        and len(bad_failures) > len(base_failures)
        and "exp-not-log-domain-sqrt" not in bad_failures,
        "at least one explicit negative control fires under sabotage, while the old inverted exp label is gone",
    )

    operation, _target, candidates, matches = retrieve("mult")
    expect(
        bool(candidates)
        and len(candidates) == 3
        and all(candidate.mechanism in {card.id for card in MECHANISM_CARDS} for candidate in candidates)
        and all(
            "declared_support" in matches[candidate.id]
            for candidate in candidates
        )
        and any(
            matches[candidate.id]["declared_support"] is False
            for candidate in candidates
        ),
        "retrieval scores cards that do not declare support and marks them as hypotheses",
    )

    expect(
        any(check["name"] == "unlabelled-candidate triage" for check in sabotaged["checks"])
        and sabotaged["certified"] is False,
        "the sabotaged run still reports triage and refuses certification",
    )

    declared = {
        operation: {
            card.id
            for card in MECHANISM_CARDS
            if operation in card.supported_operations
        }
        for operation in ("sqrt", "sum", "difference", "quantized_carry")
    }
    expect(
        declared["sqrt"] == {"cam-profile", "log-domain-sqrt", "orifice-pressure-flow"}
        and declared["sum"]
        == {
            "fluid-continuity",
            "kcl-conservation",
            "opamp-summing",
            "rheology-continuity",
        }
        and set(base_metrics["triage_candidates"]) != set(),
        "supported_operations remains available as validation metadata, not as the candidate filter",
    )

    print("\n" + "=" * 78)
    print(f"TRANSFER EVALUATION SABOTAGE: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

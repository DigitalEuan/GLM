#!/usr/bin/env python3
"""Run the GLM formula-wheel and Smith Chart studies as one evidence suite.

The components remain mathematically separate:

* formula wheel: grounding, dimensions, and monomial derivability;
* Smith Chart: normalized complex immittance and reflection geometry.

The suite joins their evidence documents without claiming that a dimensional
match verifies RF physics or that Smith geometry demonstrates a lattice
advantage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

import glm_formula_wheel_study_v2 as formula_study
import glm_smith_chart_study as smith_study


def combined_document(angle_policy: str) -> dict:
    wheels, formula_results = formula_study.run_study(angle_policy)
    smith_results = smith_study.run_study()
    formula_document = formula_study.result_document(
        wheels, formula_results, angle_policy)
    smith_document = smith_study.result_document(smith_results)
    protocol = {
        "formula_protocol_sha256": formula_document["protocol_sha256"],
        "smith_protocol_sha256": smith_document["protocol_sha256"],
        "angle_policy": angle_policy,
    }
    suite_hash = hashlib.sha256(
        json.dumps(protocol, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "schema": "glm.formula-wheel-suite.v1",
        "suite_protocol_sha256": suite_hash,
        "architecture": [
            "EquationClaim -> FormulaWheelEvidence",
            "ImpedanceClaim + FormulaWheelEvidence -> dimensionless z",
            "dimensionless z -> SmithChartEvidence",
            "evidence documents -> GLM comparison/evaluation layer",
        ],
        "formula_wheel": formula_document,
        "smith_chart": smith_document,
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--angle-policy", choices=("si", "explicit"), default="si")
    parser.add_argument("--json-out", type=Path,
                        default=Path("glm_formula_wheel_suite_results.json"))
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    document = combined_document(args.angle_policy)
    args.json_out.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    formula_score = document["formula_wheel"]["score"]
    smith_score = document["smith_chart"]["score"]
    print("GLM FORMULA-WHEEL EVIDENCE SUITE")
    print("=" * 72)
    print(f"Suite protocol SHA-256: {document['suite_protocol_sha256']}")
    print("Formula dimensional outcomes: " +
          "/".join(map(str, formula_score["dimensional_expected_outcome_accuracy"])))
    print("Formula derivation outcomes: " +
          "/".join(map(str, formula_score["derivation_expected_outcome_accuracy"])))
    print(f"Smith Chart outcomes: {smith_score['correct']}/{smith_score['total']}")
    errors = formula_score["execution_errors"] + smith_score["execution_errors"]
    print(f"Execution errors: {errors}")
    print(f"Results written to: {args.json_out}")
    formula_ok = all(
        pair[0] == pair[1] for pair in (
            formula_score["dimensional_expected_outcome_accuracy"],
            formula_score["derivation_expected_outcome_accuracy"],
        ))
    smith_ok = smith_score["correct"] == smith_score["total"]
    return 1 if args.strict and (not formula_ok or not smith_ok or errors) else 0


if __name__ == "__main__":
    sys.exit(main())

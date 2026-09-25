#!/usr/bin/env python3
"""Aggregate independent GLM engineering evidence capabilities.

This runner does not merge their mathematics:

* formula-wheel study: dimensional grounding and monomial derivability;
* Smith Chart study: normalized complex immittance geometry;
* delta-sigma study: sampled nonlinear audio dynamics and spectral metrics.

Keeping the evidence producers separate prevents success in one domain from
being counted as evidence for another while still producing one versioned
document for a GLM Evidence Blackboard.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional, Sequence

import glm_delta_sigma_audio_study as audio
import glm_formula_wheel_study_v2 as formula
import glm_smith_chart_study as smith


def build_document(args: argparse.Namespace) -> dict:
    wheels, formula_results = formula.run_study(args.angle_policy)
    formula_document = formula.result_document(
        wheels, formula_results, args.angle_policy)
    smith_results = smith.run_study()
    smith_document = smith.result_document(smith_results)
    audio_results, _ = audio.run_study(
        args.fs_audio, args.osr, args.duration_s, args.audio_band_hz)
    audio_checks = audio.preregistered_checks(audio_results)
    audio_document = {
        "schema": "glm.delta-sigma-audio-study.v1",
        "configuration": {
            "audio_sample_rate_hz": args.fs_audio,
            "oversampling_ratio": args.osr,
            "duration_s": args.duration_s,
            "audio_band_hz": args.audio_band_hz,
        },
        "preregistered_checks": audio_checks,
        "score": {"passed": sum(audio_checks.values()),
                  "total": len(audio_checks)},
        "results": [asdict(result) for result in audio_results],
    }
    component_hashes = {
        "formula": formula_document["protocol_sha256"],
        "smith": smith_document["protocol_sha256"],
        "audio_configuration": audio_document["configuration"],
    }
    suite_hash = hashlib.sha256(
        json.dumps(component_hashes, sort_keys=True).encode()).hexdigest()
    return {
        "schema": "glm.multidomain-engineering-evidence.v1",
        "suite_protocol_sha256": suite_hash,
        "separation_principle": (
            "Scores are reported per capability and are never pooled into a "
            "single scientific-validity percentage."),
        "capabilities": {
            "formula_wheel": formula_document,
            "smith_chart": smith_document,
            "delta_sigma_audio": audio_document,
        },
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--angle-policy", choices=("si", "explicit"), default="si")
    parser.add_argument("--fs-audio", type=float, default=48000.0)
    parser.add_argument("--osr", type=int, default=64)
    parser.add_argument("--duration-s", type=float, default=0.20)
    parser.add_argument("--audio-band-hz", type=float, default=20000.0)
    parser.add_argument("--json-out", type=Path,
                        default=Path("glm_multidomain_evidence_results.json"))
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if (args.fs_audio <= 0 or args.osr < 2 or args.duration_s <= 0 or
            not 0 < args.audio_band_hz < args.fs_audio / 2):
        print("ERROR: invalid audio configuration", file=sys.stderr)
        return 2
    document = build_document(args)
    args.json_out.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    capabilities = document["capabilities"]
    formula_score = capabilities["formula_wheel"]["score"]
    smith_score = capabilities["smith_chart"]["score"]
    audio_score = capabilities["delta_sigma_audio"]["score"]
    print("GLM MULTIDOMAIN ENGINEERING EVIDENCE")
    print("=" * 72)
    print("Formula dimensional outcomes: " + "/".join(map(
        str, formula_score["dimensional_expected_outcome_accuracy"])))
    print("Formula derivation outcomes: " + "/".join(map(
        str, formula_score["derivation_expected_outcome_accuracy"])))
    print(f"Smith Chart outcomes: {smith_score['correct']}/{smith_score['total']}")
    print(f"Delta-sigma checks: {audio_score['passed']}/{audio_score['total']}")
    print("Scores remain separate; they are not pooled into one validity score.")
    print(f"Evidence: {args.json_out}")
    passed = (
        all(pair[0] == pair[1] for pair in (
            formula_score["dimensional_expected_outcome_accuracy"],
            formula_score["derivation_expected_outcome_accuracy"])) and
        smith_score["correct"] == smith_score["total"] and
        audio_score["passed"] == audio_score["total"])
    return 1 if args.strict and not passed else 0


if __name__ == "__main__":
    sys.exit(main())

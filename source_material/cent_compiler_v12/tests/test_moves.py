#!/usr/bin/env python3
"""Focused tests for the declared move-corpus audit.

Run without pytest: ``python3 tests/test_moves.py``.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import leech_class, move_corpus  # noqa: E402

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


def main() -> int:
    print("=" * 78)
    print("MOVE CORPUS")
    print("=" * 78)

    fixture = {
        "schema": move_corpus.SCHEMA,
        "provenance": "synthetic test fixture, not Leech data",
        "moves": {
            "a": {"vector": [1, 0], "weight": "1"},
            "b": {"vector": [0, 1], "weight": "1"},
            "c": {"vector": [1, 1], "weight": "1"},
        },
        "sequences": [
            ["a", "b", "a", "c", "a", "b"],
            ["a", "a"],
        ],
    }
    report = move_corpus.analyze(fixture)
    expect(
        report["schema"] == move_corpus.REPORT_SCHEMA
        and report["status"] == "ok"
        and report["counts"]["sequences"] == 2
        and report["counts"]["move_occurrences"] == 8
        and report["counts"]["transitions"] == 6
        and report["counts"]["used_moves"] == 3
        and report["counts"]["vector_dimension"] == 2,
        "the corpus audit counts sequences, moves, transitions and dimension",
    )
    rows = {row["current"]: row for row in report["top1"]["rows"]}
    expect(
        report["top1"]["accuracy"] == "2/3"
        and report["top1"]["percent"] == "66.67%"
        and report["top1"]["tied_current_states"] == 0
        and rows["a"]["prediction"] == "b"
        and rows["a"]["total"] == 4
        and rows["a"]["correct"] == 2
        and rows["b"]["total"] == 1
        and rows["b"]["correct"] == 1,
        "the in-sample bigram top-1 baseline is exact and deterministic",
    )
    stats = report["return_stats"]
    expect(
        stats is not None
        and stats["median_net_squared_norm"] == "29/2"
        and stats["mean_net_squared_norm"] == "29/2"
        and stats["mean_move_squared_norm"] == "9/8"
        and stats["sequences"][0]["net"] == [4, 3]
        and stats["sequences"][0]["squared_norm"] == 25
        and stats["sequences"][1]["squared_norm"] == 4,
        "return displacements and squared norms are computed from integer vectors",
    )

    partial = {
        "schema": move_corpus.SCHEMA,
        "moves": {
            "a": {"vector": [1, 0]},
            "b": {},
        },
        "sequences": [["a", "b"]],
    }
    partial_report = move_corpus.analyze(partial)
    expect(
        partial_report["status"] == "partial"
        and partial_report["return_stats"] is None
        and any(
            "integer vector" in gap for gap in partial_report["gaps"]
        ),
        "missing vectors leave displacement unavailable instead of invented",
    )

    loo_fixture = {
        "schema": move_corpus.SCHEMA,
        "moves": {
            "a": {"vector": [1, 0]},
            "b": {"vector": [0, 1]},
            "c": {"vector": [1, 1]},
        },
        "sequences": [
            ["a", "a", "a"],
            ["b", "b", "a"],
        ],
    }
    study_holdout = move_corpus.analyze(loo_fixture, holdout="study")["holdout"]
    strict_holdout = move_corpus.analyze(loo_fixture, holdout="strict")["holdout"]
    expect(
        study_holdout["protocol"] == "study-actual-pair"
        and study_holdout["accuracy"] == "0/1"
        and study_holdout["no_prediction"] == 2
        and strict_holdout["protocol"] == "strict-file"
        and strict_holdout["accuracy"] == "0/1"
        and strict_holdout["no_prediction"] == 4,
        "study and strict holdout protocols are separate and exact",
    )

    invalid = {
        "schema": move_corpus.SCHEMA,
        "moves": {"a": {}, "b": {}},
        "sequences": [["a", "z"]],
    }
    invalid_error = ""
    try:
        move_corpus.analyze(invalid)
    except move_corpus.MoveCorpusError as exc:
        invalid_error = str(exc)
    expect(
        "undeclared move" in invalid_error and "z" in invalid_error,
        "an undeclared sequence move is rejected",
    )

    cli_payload = {}
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "corpus.json"
        path.write_text(json.dumps(loo_fixture), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "cent"),
                "moves",
                str(path),
                "--holdout",
                "study",
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            try:
                cli_payload = json.loads(result.stdout)
            except json.JSONDecodeError:
                cli_payload = {}
    expect(
        result.returncode == 0
        and cli_payload.get("ok") is True
        and cli_payload.get("schema") == move_corpus.REPORT_SCHEMA
        and (cli_payload.get("report") or {}).get("holdout", {}).get(
            "no_prediction"
        )
        == 2,
        "CLI moves emits the exact corpus report",
    )

    basis = [[2, 0], [0, 2]]
    expect(
        leech_class.basis_coords([2, 2], basis) == (1, 1)
        and leech_class.class_word([2, 2], basis) == 3
        and leech_class.xor_compose(1, 2) == 3
        and leech_class.f2_rank([0, 1, 2, 3]) == 2,
        "class words are exact parity coordinates and compose by XOR",
    )
    class_moves = {
        "a": {"vector": [0, 0]},
        "b": {"vector": [2, 0]},
        "c": {"vector": [0, 2]},
        "d": {"vector": [2, 2]},
    }
    class_report = leech_class.audit(
        basis, class_moves, composition_samples=4, provenance="synthetic fixture"
    )
    expect(
        class_report["status"] == "ok"
        and class_report["basis_determinant"] == 4
        and class_report["moves_decoded"] == 4
        and class_report["distinct_class_words"] == 4
        and class_report["class_space_size"] == 4
        and class_report["observed_class_fraction"] == "1/1"
        and class_report["f2_rank"] == 2
        and class_report["zero_class_moves"] == 1
        and class_report["composition"]["passed"] == 4,
        "the class audit reports exact counts, rank and sampled composition",
    )
    invalid_class_error = ""
    try:
        leech_class.class_word([1, 0], basis)
    except leech_class.LeechClassError as exc:
        invalid_class_error = str(exc)
    expect(
        "not in the declared lattice" in invalid_class_error,
        "a vector outside the declared lattice is rejected",
    )

    class_cli_payload = {}
    with tempfile.TemporaryDirectory() as directory:
        basis_path = pathlib.Path(directory) / "basis.json"
        corpus_path = pathlib.Path(directory) / "class-corpus.json"
        basis_path.write_text(json.dumps(basis), encoding="utf-8")
        corpus_path.write_text(
            json.dumps(
                {
                    "schema": move_corpus.SCHEMA,
                    "provenance": "synthetic class fixture",
                    "moves": class_moves,
                    "sequences": [["a", "b", "c", "d"]],
                }
            ),
            encoding="utf-8",
        )
        class_cli = subprocess.run(
            [
                sys.executable,
                str(ROOT / "cent"),
                "leech-class",
                "--basis",
                str(basis_path),
                "--corpus",
                str(corpus_path),
                "--samples",
                "4",
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if class_cli.returncode == 0:
            try:
                class_cli_payload = json.loads(class_cli.stdout)
            except json.JSONDecodeError:
                class_cli_payload = {}
    expect(
        class_cli.returncode == 0
        and class_cli_payload.get("schema") == leech_class.SCHEMA
        and (class_cli_payload.get("report") or {}).get("distinct_class_words") == 4
        and (class_cli_payload.get("output_certificate") or {}).get("subject_schema")
        == leech_class.SCHEMA,
        "CLI leech-class emits the exact report and certificate",
    )

    print()
    print("=" * 78)
    print(f"MOVE CORPUS: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

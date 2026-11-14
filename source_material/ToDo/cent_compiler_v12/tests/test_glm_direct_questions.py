#!/usr/bin/env python3
"""Direct GLM question audit.

These questions are deliberately narrow:

* resolving ties in Leech calculations;
* travelling lattice paths efficiently;
* XOR in a 24D lattice;
* optimal 2D square packing for n squares;
* answering Rule 30 questions directly.

The first three have narrow working facilities in the repository. They are not
general Leech tie resolvers, path planners or physical compiler operations.
Square packing now has a declared W36/W37 pressure-settling **candidate**; it
is an exact fixed-container feasibility probe, not an optimality proof. Rule 30
has no declared adapter.

Run without pytest: ``python3 tests/test_glm_direct_questions.py``.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import leech_class, move_corpus, packing  # noqa: E402

PASS = 0
FAIL = 0

DIRECT_QUERIES = [
    ("leech-tie", "resolve ties in Leech lattice calculations", "gap"),
    ("lattice-path", "travel lattice paths efficiently", "gap"),
    ("lattice-xor-24d", "compute XOR in a 24D lattice", "gap"),
    ("square-packing", "find an optimal 2D square packing for n squares", "method"),
    ("rule30-direct", "answer a Rule 30 question directly", "gap"),
]


def expect(condition: bool, message: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ok   {message}")
    else:
        FAIL += 1
        print(f"  FAIL {message}")


def vector_24(axis: int, value: int = 1) -> list[int]:
    result = [0] * 24
    result[axis] = value
    return result


def main() -> int:
    print("=" * 78)
    print("GLM DIRECT QUESTIONS")
    print("=" * 78)

    matrix = subprocess.run(
        [sys.executable, str(ROOT / "cent"), "matrix", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    matrix_payload = json.loads(matrix.stdout) if matrix.returncode == 0 else {}
    operations = set(matrix_payload.get("operations") or [])
    packing_rows = [
        row for row in matrix_payload.get("rows", ())
        if row.get("operation") == "packing"
    ]
    expect(
        matrix.returncode == 0
        and "packing" in operations
        and not operations & {"xor", "tie", "path", "rule30"}
        and len(packing_rows) == 1
        and packing_rows[0].get("evidence") == "declared-analogy"
        and "optimality" in packing_rows[0].get("first_gap", ""),
        "the matrix exposes packing as a declared analogy and leaves the other primitives out",
    )

    for query_id, query, expected in DIRECT_QUERIES:
        result = subprocess.run(
            [sys.executable, str(ROOT / "cent"), "discover", query, "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        payload = json.loads(result.stdout) if result.returncode == 0 else {}
        if expected == "gap":
            expect(
                result.returncode == 0
                and payload.get("matched") is False
                and payload.get("methods") == []
                and payload.get("output_certificate", {}).get("status") == "gap",
                f"{query_id}: {query} still has no declared method",
            )
        else:
            method = (payload.get("methods") or [{}])[0]
            probe = method.get("route_simulation") or {}
            expect(
                result.returncode == 0
                and payload.get("matched") is True
                and payload.get("problem", {}).get("object") == "packing"
                and method.get("name") == "Pressure Settling Engine — W36/W37 relaxation"
                and method.get("primitive") == "packing"
                and method.get("route") == "declared-analogy"
                and probe.get("passed") is True
                and probe.get("optimal") is False
                and method.get("wheel_scan", {}).get("wheels_scanned") == 40
                and method.get("wheel_scan", {}).get("selected") == ["W36", "W37"]
                and any("optimality" in gap for gap in method.get("gaps", ())),
                f"{query_id}: packing proposes the pressure-settling candidate without an optimality claim",
            )

    tie_fixture = {
        "schema": move_corpus.SCHEMA,
        "provenance": "synthetic tie fixture; not Leech geometry",
        "moves": {"a": {}, "b": {}, "c": {}},
        "sequences": [["a", "b"], ["a", "c"]],
    }
    tie_report = move_corpus.analyze(tie_fixture)
    tie_row = tie_report["top1"]["rows"][0]
    expect(
        tie_report["top1"]["tied_current_states"] == 1
        and tie_row["current"] == "a"
        and tie_row["ties"] == ["b", "c"]
        and tie_row["prediction"] == "b"
        and tie_report["top1"]["accuracy"] == "1/2",
        "the only tie-break is lexical move-id tie-breaking, not a Leech resolver",
    )

    path_fixture = {
        "schema": move_corpus.SCHEMA,
        "provenance": "synthetic 24D path fixture; not Leech geometry",
        "moves": {
            "e0": {"vector": vector_24(0)},
            "e1": {"vector": vector_24(1)},
        },
        "sequences": [["e0", "e1", "e0"]],
    }
    path_report = move_corpus.analyze(path_fixture)
    displacement = path_report["return_stats"]["sequences"][0]
    expect(
        path_report["return_stats"]["dimension"] == 24
        and displacement["net"] == [2, 1] + [0] * 22
        and displacement["squared_norm"] == 5,
        "the narrow facility accounts for a 24D path net displacement, not efficient travel",
    )

    basis = [[2 if row == column else 0 for column in range(24)] for row in range(24)]
    combined = [left + right for left, right in zip(vector_24(0, 2), vector_24(1, 2))]
    class_moves = {
        "a": {"vector": vector_24(0, 2)},
        "b": {"vector": vector_24(1, 2)},
        "c": {"vector": combined},
    }
    expect(
        leech_class.basis_coords(vector_24(0, 2), basis) == (1,) + (0,) * 23
        and leech_class.class_word(vector_24(0, 2), basis) == 1
        and leech_class.class_word(vector_24(1, 2), basis) == 2
        and leech_class.class_word(combined, basis) == 3
        and leech_class.xor_compose(1, 2) == 3
        and leech_class.f2_rank([0, 1, 2, 3]) == 2,
        "the 24D class-word facility computes exact parity and XOR",
    )

    class_report = leech_class.audit(
        basis,
        class_moves,
        composition_samples=4,
        provenance="synthetic 24D fixture; not the Leech lattice",
    )
    expect(
        class_report["status"] == "ok"
        and class_report["dimension"] == 24
        and class_report["basis_determinant"] == 1 << 24
        and class_report["distinct_class_words"] == 3
        and class_report["f2_rank"] == 2
        and class_report["composition"]["passed"] == 4,
        "the 24D class audit is a working index utility, not a compiler method",
    )

    probe = packing.settle(2, side=3, iterations=8)
    expect(
        probe["schema"] == "cent-packing/1"
        and probe["initial"]["energy"] == "1"
        and probe["final"]["energy"] == "0"
        and probe["initial"]["max_penetration"] == "1"
        and probe["final"]["max_penetration"] == "0"
        and probe["passed"] is True
        and probe["optimal"] is False
        and "no global optimality" in probe["optimality_gap"],
        "the exact pressure-settling probe resolves overlap but does not claim optimality",
    )

    cli = subprocess.run(
        [
            sys.executable, str(ROOT / "cent"), "packing",
            "--n", "2", "--side", "3", "--iterations", "8", "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    cli_payload = json.loads(cli.stdout) if cli.returncode == 0 else {}
    expect(
        cli.returncode == 0
        and cli_payload.get("schema") == "cent-packing/1"
        and cli_payload.get("final", {}).get("energy") == "0"
        and cli_payload.get("optimal") is False
        and (cli_payload.get("output_certificate") or {}).get("subject_schema")
        == "cent-packing/1",
        "the packing CLI runs the exact probe and carries its certificate",
    )

    print()
    print("=" * 78)
    print(f"GLM DIRECT QUESTIONS: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

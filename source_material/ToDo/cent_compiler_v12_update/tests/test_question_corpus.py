#!/usr/bin/env python3
"""Canonical regression for the fixed GLM/cent question corpus.

Every corpus entry runs one declared ``cent`` CLI command with ``--json`` and
checks its exit code, JSON fields, lengths or refusal diagnostics.  The corpus
is an evidence and reproducibility aid; it is not a benchmark score and does not
claim a GLM result.

Run without pytest: ``python3 tests/test_question_corpus.py``.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CORPUS = ROOT / "tests" / "fixtures" / "glm_cent_questions.json"
ALLOWED_COMMANDS = {
    "assemble",
    "axioms",
    "compile",
    "derive",
    "discover",
    "matrix",
    "physical",
}
ALLOWED_EXPECT_KEYS = {
    "exit",
    "json",
    "fields",
    "length_eq",
    "length_gte",
    "stderr_contains",
}

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


def lookup(payload, path: str):
    value = payload
    for part in path.split("."):
        if isinstance(value, list):
            value = value[int(part)]
        elif isinstance(value, dict):
            value = value[part]
        else:
            raise KeyError(path)
    return value


def run_question(item: dict) -> list[str]:
    failures: list[str] = []
    expected = item["expect"]
    command = [sys.executable, str(ROOT / "cent"), *item["argv"]]
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != expected["exit"]:
        failures.append(
            f"exit {result.returncode}, expected {expected['exit']}"
        )

    payload = None
    if expected["json"]:
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            failures.append(f"stdout is not JSON: {exc}")
    elif result.stdout.strip():
        failures.append("stdout must be empty for a non-JSON refusal")

    if payload is not None:
        for path, wanted in expected.get("fields", {}).items():
            try:
                actual = lookup(payload, path)
            except (KeyError, IndexError, ValueError):
                failures.append(f"missing field {path}")
                continue
            if actual != wanted:
                failures.append(f"{path}={actual!r}, expected {wanted!r}")

        for path, wanted in expected.get("length_eq", {}).items():
            try:
                actual = len(lookup(payload, path))
            except (KeyError, IndexError, TypeError, ValueError):
                failures.append(f"missing or unmeasurable length {path}")
                continue
            if actual != wanted:
                failures.append(f"len({path})={actual}, expected {wanted}")

        for path, wanted in expected.get("length_gte", {}).items():
            try:
                actual = len(lookup(payload, path))
            except (KeyError, IndexError, TypeError, ValueError):
                failures.append(f"missing or unmeasurable length {path}")
                continue
            if actual < wanted:
                failures.append(f"len({path})={actual}, expected >= {wanted}")

    for text in expected.get("stderr_contains", []):
        if text not in result.stderr:
            failures.append(f"stderr is missing {text!r}")

    return failures


def main() -> int:
    print("=" * 78)
    print("QUESTION CORPUS")
    print("=" * 78)

    try:
        corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  FAIL cannot load corpus: {type(exc).__name__}: {exc}")
        print()
        print("=" * 78)
        print("QUESTION CORPUS: 0/1 checks passed")
        print("=" * 78)
        return 1

    questions = corpus.get("questions", [])
    ids = [item.get("id") for item in questions]
    expect(
        corpus.get("schema") == "cent-question-corpus/1"
        and len(questions) == 13
        and len(set(ids)) == 13
        and all(isinstance(question_id, str) and question_id for question_id in ids),
        "the corpus declares 13 uniquely identified questions",
    )

    well_formed = []
    for item in questions:
        expected = item.get("expect", {})
        well_formed.append(
            isinstance(item.get("question"), str)
            and bool(item["question"])
            and isinstance(item.get("argv"), list)
            and len(item["argv"]) >= 2
            and item["argv"][0] in ALLOWED_COMMANDS
            and item["argv"][-1] == "--json"
            and set(expected) <= ALLOWED_EXPECT_KEYS
            and isinstance(expected.get("exit"), int)
            and isinstance(expected.get("json"), bool)
        )
    expect(
        len(well_formed) == 13 and all(well_formed),
        "every question uses a declared cent command, --json and a known expectation shape",
    )

    expect(
        sum(1 for item in questions if item["expect"]["exit"] != 0) == 2,
        "the corpus pins two explicit refusals",
    )

    for item in questions:
        failures = run_question(item)
        detail = "" if not failures else " — " + "; ".join(failures)
        expect(not failures, f"{item['id']}: {item['question']}{detail}")

    print()
    print("=" * 78)
    print(f"QUESTION CORPUS: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""D6 gate: frozen retrodictive holdout, dated labels and honest misses."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cent_compiler import holdout

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
    except (KeyError, ValueError):
        return True
    return False


def main() -> int:
    print("=" * 78)
    print("D6 RETRODICTIVE HOLDOUT GATE")
    print("=" * 78)

    ledger = holdout.build_ledger()
    metrics = ledger.get("metrics") or {}
    frozen = ledger.get("frozen_library") or []
    cases = ledger.get("cases") or []
    results = ledger.get("results") or []
    excluded = ledger.get("excluded") or []

    expect(
        ledger.get("schema") == "cent-retrodictive-holdout/1"
        and ledger.get("cutoff_year") == 1940
        and ledger.get("ok") is True,
        "the holdout freezes the library at 1940 and reports a complete ledger",
    )
    expect(
        len(frozen) == 5
        and len({mechanism.get("id") for mechanism in frozen}) == 5
        and all(
            mechanism.get("source_year") is None
            or mechanism.get("source_year") < ledger["cutoff_year"]
            for mechanism in frozen
        ),
        "all five frozen mechanisms are dated before the cutoff or explicitly undated",
    )
    expect(
        all(
            mechanism.get("signature")
            and mechanism.get("citation")
            and mechanism.get("source_date")
            for mechanism in frozen
        ),
        "every frozen mechanism carries a signature, source date and citation",
    )
    expect(
        len(cases) == 5
        and len({case.get("id") for case in cases}) == 5
        and all(case.get("target_year") > ledger["cutoff_year"] for case in cases),
        "all five evaluated targets were published after the cutoff",
    )
    expect(
        all(
            case.get("expected_mechanism")
            in {mechanism.get("id") for mechanism in frozen}
            for case in cases
        ),
        "every expected mechanism belongs to the frozen library",
    )
    expect(
        all(
            case.get("citation")
            and case.get("provenance")
            and case.get("required_observable")
            and case.get("target_signature")
            for case in cases
        ),
        "every case has provenance, a required observable and a target signature",
    )
    expect(
        len(excluded) == 1
        and excluded[0].get("id") == "bresenham-delta-sigma"
        and excluded[0].get("status") == "excluded"
        and "1965" in excluded[0].get("reason", "")
        and "cutoff" in excluded[0].get("reason", ""),
        "Bresenham is excluded because its source postdates 1940, not counted as a hit",
    )

    expect(
        metrics.get("cases") == 5
        and metrics.get("recalled") == 5
        and metrics.get("recall") == "5/5"
        and metrics.get("candidate_recall") == 1.0
        and metrics.get("misses") == [],
        "the measured recall is 5/5 with no hidden misses",
    )
    expect(
        all(
            result.get("passed") is True
            and result.get("expected_rank") == 1
            and (result.get("expected_score") or 0) > 0
            for result in results
        ),
        "each historical target retrieves its expected mechanism at rank one",
    )
    expect(
        metrics.get("false_positive_candidates")
        == ["resistor-network-random-walk/kinetic-theory"]
        and metrics.get("false_positive_cases") == ["resistor-network-random-walk"]
        and metrics.get("false_positive_rate") == "1/15",
        "the declared target constraints expose one measured false-positive candidate",
    )
    expect(
        any(
            result.get("false_positives") == ["kinetic-theory"]
            and any(
                row.get("mechanism") == "kinetic-theory"
                and row.get("false_positive") is True
                for row in result.get("retrieved") or []
            )
            for result in results
            if result.get("id") == "resistor-network-random-walk"
        ),
        "the false positive is retained in the retrieved candidates rather than filtered out",
    )
    expect(
        all(
            result.get("unlabelled") == [
                row["mechanism"]
                for row in result.get("retrieved") or []
                if row["mechanism"] != result.get("expected_mechanism")
                and not row.get("false_positive")
            ]
            for result in results
        ),
        "unexpected but unrefuted candidates remain in the separate triage queue",
    )

    expect(
        all(
            result.get("status") == "post-cutoff"
            and result.get("target_operation")
            for result in results
        ),
        "the ledger distinguishes post-cutoff target evidence from frozen sources",
    )
    negative = ledger.get("negative_controls") or []
    expect(
        len(negative) == 1
        and negative[0].get("id") == "rsa-modular-exponentiation"
        and negative[0].get("status") == "negative-control"
        and negative[0].get("expected_mechanism") is None
        and negative[0].get("required_primitive") == "mod"
        and negative[0].get("target_year") == 1978
        and all(
            "mod" not in (mechanism.get("signature") or {}).get("primitive_chain", [])
            for mechanism in frozen
        ),
        "the pre-registered RSA control has no licensed frozen source",
    )
    expect(
        metrics.get("negative_controls") == 1
        and metrics.get("negative_control_outcome") == "no_licensed_source"
        and metrics.get("negative_control_no_licensed_source") is True
        and metrics.get("negative_control_misses")
        == [
            "rsa-modular-exponentiation: required primitive 'mod' is absent from every frozen source"
        ]
        and negative[0].get("coverage_miss") is True,
        "the negative control records a coverage miss instead of hiding it",
    )
    expect(
        metrics.get("negative_control_false_positive_candidates") == []
        and metrics.get("negative_control_false_positive_rate") == "0/0"
        and negative[0].get("false_positives") == []
        and negative[0].get("retrieved") == [],
        "the absent required primitive suppresses structural candidates instead of reporting false positives",
    )
    expect(
        "NEGATIVE CONTROL rsa-modular-exponentiation: no_licensed_source"
        in holdout.render_ledger(ledger)
        and "no licensed source: no frozen source contains the required primitive"
        in holdout.render_ledger(ledger),
        "the text rendering states that no licensed source exists",
    )
    expect(
        any(
            "separate hand-declared holdout library" in gap
            for gap in ledger.get("gaps") or []
        )
        and any(
            "five evaluated cases" in gap for gap in ledger.get("gaps") or []
        ),
        "the ledger states its hand-declared and small-corpus limitations",
    )
    expect(
        "D6 RETRODICTIVE HOLDOUT" in holdout.render_ledger(ledger)
        and "EXCLUDED bresenham-delta-sigma" in holdout.render_ledger(ledger)
        and "recall: 5/5" in holdout.render_ledger(ledger),
        "the text rendering shows the cutoff, recall and excluded candidate",
    )

    expect(
        _rejects(
            lambda: holdout.HoldoutCase(
                id="bad-target",
                target_domain="test",
                target_operation="test",
                target_year=1940,
                expected_mechanism="random-walk",
                target_signature=holdout._cases()[0].target_signature,
                required_observable="test",
                forbidden_traits={},
                citation="test",
                provenance="test",
            )
        ),
        "a target at or before the cutoff is rejected",
    )
    expect(
        _rejects(
            lambda: holdout.FrozenMechanism(
                id="late-source",
                name="late source",
                source_domain="test",
                source_year=1940,
                source_date="1940",
                signature=holdout._frozen_mechanisms()[0].signature,
                citation="test",
            )
        ),
        "a frozen mechanism at or after the cutoff is rejected",
    )
    for bad_limit in (0, -1, True, 1.5):
        expect(
            _rejects(lambda bad_limit=bad_limit: holdout.build_ledger(limit=bad_limit)),
            f"invalid retrieval limit {bad_limit!r} is rejected",
        )

    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / "holdout.json"
        written = holdout.write_ledger(str(path))
        stored = json.loads(path.read_text())
        expect(
            written == str(path)
            and stored.get("schema") == "cent-retrodictive-holdout/1"
            and (stored.get("metrics") or {}).get("recall") == "5/5",
            "the portable holdout ledger round-trips through JSON",
        )

    cli = subprocess.run(
        [sys.executable, "cent", "holdout", "--json", "--limit", "1"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    cli_payload = json.loads(cli.stdout) if cli.returncode == 0 else {}
    expect(
        cli.returncode == 0
        and cli_payload.get("schema") == "cent-retrodictive-holdout/1"
        and (cli_payload.get("metrics") or {}).get("recall") == "5/5"
        and len((cli_payload.get("results") or [{}])[0].get("retrieved") or []) == 1,
        "the CLI exposes the frozen holdout and honours the candidate limit",
    )

    print()
    print("=" * 78)
    print(f"RESULT: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Canonical regression for the 22 show-work proposals.

The manual ``tests/show_work.py`` audit runs every proposal through the full
decompose → enumerate → rank → escalate → emit pipeline.  This suite makes that
audit part of the gate without treating a proposal or a generated netlist as a
fabricated device.

The audit is generated in a temporary directory and compared byte-for-byte with
the checked-in ``examples/proposal_*.cir`` files.  A template change therefore
requires a deliberate example regeneration; the gate itself does not rewrite
the repository.

Run without pytest: ``python3 tests/test_proposals.py``.
"""
from __future__ import annotations

import contextlib
import io
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(TESTS))

import show_work  # noqa: E402
import test_applications  # noqa: E402

PASS = 0
FAIL = 0

# Pinned independently of the proposal tuple so a changed template assignment
# cannot silently rewrite the expected artifact set.
EXPECTED_CIR_FILES = {
    "01": "proposal_01_multiplier.cir",
    "02": "proposal_02_opamp_sqrt.cir",
    "03": "proposal_03_multiplier.cir",
    "04": "proposal_04_opamp_sqrt.cir",
    "05": "proposal_05_divider.cir",
    "06": "proposal_06_rc_integrator.cir",
    "07": "proposal_07_divider.cir",
    "08": "proposal_08_diode_exp.cir",
    "09": "proposal_09_log_amp.cir",
    "10": "proposal_10_clipper.cir",
    "11": "proposal_11_multiplier.cir",
    "12": "proposal_12_opamp_sqrt.cir",
    "13": "proposal_13_multiplier.cir",
    "14": "proposal_14_divider.cir",
    "15": "proposal_15_divider.cir",
    "16": "proposal_16_divider.cir",
    "17": "proposal_17_divider.cir",
    "18": "proposal_18_divider.cir",
    "19": "proposal_19_divider.cir",
    "20": "proposal_20_multiplier.cir",
    "21": "proposal_21_multiplier.cir",
    "22": "proposal_22_clipper.cir",
}


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
    print("PROPOSAL PIPELINE")
    print("=" * 78)

    captured = io.StringIO()
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            original_examples_dir = show_work.EXAMPLES_DIR
            show_work.EXAMPLES_DIR = tmpdir
            try:
                show_work.results.clear()
                show_work.cir_files_written.clear()
                test_applications.results.clear()
                with contextlib.redirect_stdout(captured):
                    show_work.main()
            finally:
                show_work.EXAMPLES_DIR = original_examples_dir

            output = captured.getvalue()
            proposal_ids = [proposal[0] for proposal in show_work.PROPOSALS]
            expect(
                len(show_work.PROPOSALS) == 22
                and len(set(proposal_ids)) == 22
                and proposal_ids == [f"{index:02d}" for index in range(1, 23)],
                "the audit declares 22 unique proposals in order",
            )

            statuses = [row[2] for row in show_work.results]
            expect(
                len(show_work.results) == 22
                and statuses.count("PASS") == 22
                and not [status for status in statuses if status != "PASS"],
                "all 22 proposals pass the full pipeline",
            )

            written = [
                pathlib.Path(path).resolve() for path in show_work.cir_files_written
            ]
            expect(
                len(written) == 22
                and len(set(written)) == 22
                and all(
                    path.parent == pathlib.Path(tmpdir).resolve() for path in written
                ),
                "the audit writes 22 distinct netlists into the temporary directory",
            )

            expected_names = set(EXPECTED_CIR_FILES.values())
            expected_paths = {
                (pathlib.Path(tmpdir) / name).resolve() for name in expected_names
            }
            checked_in_names = {
                path.name
                for path in (ROOT / "examples").glob("proposal_*.cir")
                if path.is_file()
            }
            expect(
                set(written) == expected_paths
                and {path.name for path in written} == expected_names
                and checked_in_names == expected_names,
                "the generated and checked-in netlist filenames match the pinned set",
            )

            valid_files = []
            for path in sorted(written):
                generated = path.read_text(encoding="utf-8")
                checked_in = ROOT / "examples" / path.name
                if not checked_in.is_file():
                    valid_files.append(False)
                    continue
                committed = checked_in.read_text(encoding="utf-8")
                valid_files.append(
                    generated.startswith("*")
                    and generated.rstrip().endswith(".END")
                    and "No SPICE template" not in generated
                    and len(generated.splitlines()) >= 5
                    and generated == committed
                )
            expect(
                len(valid_files) == 22 and all(valid_files),
                "every generated netlist is SPICE-shaped and byte-identical to examples/",
            )

            expect(
                "PASS: 22/22" in output
                and ".cir files written: 22" in output
                and "Original suite: 6/7 PASS" in output,
                "the audit summary preserves 22/22 and the separate 6/7 comparison",
            )

            app_statuses = [row[3] for row in test_applications.results]
            expect(
                len(test_applications.results) == 7
                and app_statuses.count("PASS") == 6
                and app_statuses.count("DIMENSIONAL CHECK") == 1
                and test_applications.results[6][0].startswith("07")
                and test_applications.results[6][3] == "DIMENSIONAL CHECK",
                "the original seven-proposal suite stays 6 PASS + 1 dimensional check",
            )

            expect(
                "ERROR" not in output and "DECOMPOSE FAIL" not in output,
                "the proposal audit reports no decomposition or netlist-generation errors",
            )
    except Exception as exc:  # pragma: no cover - failure diagnostics
        print(f"  FAIL proposal audit raised: {type(exc).__name__}: {exc}")
        tail = captured.getvalue().splitlines()[-12:]
        for line in tail:
            print(f"       {line}")
        print()
        print("=" * 78)
        print("PROPOSAL PIPELINE: 0/1 checks passed")
        print("=" * 78)
        return 1

    print()
    print("=" * 78)
    print(f"PROPOSAL PIPELINE: {PASS}/{PASS + FAIL} checks passed")
    print("=" * 78)
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

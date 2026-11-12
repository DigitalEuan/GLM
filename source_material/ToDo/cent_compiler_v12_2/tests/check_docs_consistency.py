#!/usr/bin/env python3
"""Preflight checks for README package-layout and test-count claims.

``run_all.py`` calls :func:`check_readme_consistency` with the actual counts
parsed from each suite.  The same module can be run directly to check that every
path shown in the README package tree exists.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Mapping, Sequence

TREE_LINE = re.compile(
    r"^(?P<prefix>[│ ]*)(?P<branch>├── |└── )(?P<name>.+)$"
)


def _package_section(readme: str) -> str:
    if "## Package Layout" not in readme:
        raise ValueError("README has no Package Layout section")
    section = readme.split("## Package Layout", 1)[1]
    section = section.split("### Exact-core additions", 1)[0]
    match = re.search(r"```\n(.*?)```", section, re.DOTALL)
    if not match:
        raise ValueError("README Package Layout has no fenced tree")
    return match.group(1)


def package_layout_paths(root: Path) -> list[Path]:
    """Return every path claimed by the README package tree."""
    lines = _package_section((root / "README.md").read_text()).splitlines()
    stack: dict[int, Path] = {}
    paths: list[Path] = []
    for line in lines:
        stripped = line.strip()
        if stripped == "cent_compiler_v12/":
            stack[0] = root
            continue
        match = TREE_LINE.match(line)
        if not match:
            continue
        depth = len(match.group("prefix")) // 4 + 1
        parent = stack.get(depth - 1)
        if parent is None:
            raise ValueError(f"README tree has no parent at depth {depth}: {line!r}")
        name = match.group("name").split(" #", 1)[0].strip()
        if not name:
            continue
        path = parent / name
        paths.append(path)
        stack[depth] = path
    if not stack:
        raise ValueError("README package tree has no root")
    return paths


def check_layout(root: Path) -> list[str]:
    problems = []
    for path in package_layout_paths(root):
        if not path.exists():
            problems.append(f"README package path does not exist: {path.relative_to(root)}")
    return problems


def _readme_test_claims(readme: str) -> tuple[int, int, int]:
    total = re.search(r"\| Tests passing \| (\d+)/(\d+) ", readme)
    ui = re.search(r"test_ui\.py\s+#\s+(\d+) console UI checks", readme)
    if not total:
        raise ValueError("README has no 'Tests passing | N/N' claim")
    if not ui:
        raise ValueError("README has no test_ui console-check count")
    return int(total.group(1)), int(total.group(2)), int(ui.group(1))


def _readme_module_claim(readme: str) -> int:
    match = re.search(r"\| Python modules \| (\d+) \|", readme)
    if not match:
        raise ValueError("README has no Python-module count")
    return int(match.group(1))


def _module_count(root: Path) -> int:
    return len(list((root / "cent_compiler").glob("*.py")))


def check_readme_consistency(
    root: Path,
    suite_counts: Mapping[str, tuple[int, int]],
) -> list[str]:
    """Check the package tree and the total/test_ui count claims.

    ``suite_counts`` maps each suite filename to its observed
    ``(passed, total)`` pair from the just-finished gate.
    """
    problems = check_layout(root)
    readme = (root / "README.md").read_text()
    try:
        claimed_passed, claimed_total, claimed_ui = _readme_test_claims(readme)
        claimed_modules = _readme_module_claim(readme)
    except ValueError as exc:
        return problems + [str(exc)]

    actual_modules = _module_count(root)
    if claimed_modules != actual_modules:
        problems.append(
            "README module count disagrees: "
            f"README={claimed_modules}, observed={actual_modules}"
        )

    if "test_ui.py" not in suite_counts:
        problems.append("README consistency: test_ui.py produced no check count")
    else:
        ui_passed, ui_total = suite_counts["test_ui.py"]
        if claimed_ui != ui_total or ui_passed != ui_total:
            problems.append(
                "README test_ui count disagrees: "
                f"README={claimed_ui}, observed={ui_passed}/{ui_total}"
            )

    actual_passed = sum(passed for passed, _ in suite_counts.values())
    actual_total = sum(total for _, total in suite_counts.values())
    if (claimed_passed, claimed_total) != (actual_passed, actual_total):
        problems.append(
            "README total disagrees: "
            f"README={claimed_passed}/{claimed_total}, "
            f"observed={actual_passed}/{actual_total}"
        )
    if actual_passed != actual_total:
        problems.append(
            f"observed suite checks are not all passing: {actual_passed}/{actual_total}"
        )
    return problems


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    problems = check_layout(root)
    try:
        claimed_modules = _readme_module_claim((root / "README.md").read_text())
    except ValueError as exc:
        problems.append(str(exc))
    else:
        actual_modules = _module_count(root)
        if claimed_modules != actual_modules:
            problems.append(
                "README module count disagrees: "
                f"README={claimed_modules}, observed={actual_modules}"
            )
    if problems:
        print("README LAYOUT: FAIL")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("README LAYOUT: OK (package-tree paths and module count)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Pytest configuration for the overlay: the exhaustive opt-in.

A handful of cases in this suite do not *sample* a property, they *certify*
it: the 98,280-class type-2 table, the two study ledgers that chase eight
constants for ten thousand exact ticks each, the grounded semantic graph built
from scratch, the full capability sweep, the benchmark suites run end to end,
and the searches over ``2**24`` binary codewords in
``glm_universal/tests/test_lattice_high.py`` that were already opt-in before
this file existed.  Between them they are most of the suite's wall clock.

They are marked ``@pytest.mark.exhaustive`` and are **deselected by default**.
Turning them on is one switch, and there are two spellings of it:

* ``--exhaustive`` on the pytest command line, and
* ``GLM_EXHAUSTIVE=1`` in the environment, which is how
  :mod:`glm_universal.signoff` turns them on for a whole run.

The rule the project keeps is that *nothing only runs on demand*: every
``-all`` form of the sign-off runner, and ``--release`` in particular, sets
``GLM_EXHAUSTIVE=1``, and the ledger records which mode a unit was signed in,
so a signature earned without them does not satisfy ``--verify-release``.  A
routine round is fast because it defers these cases, never because it drops
them.

A deselected case is reported as skipped with the reason, not silently
omitted, so a bare ``pytest`` run says how much it did not do.
"""

from __future__ import annotations

import os

import pytest

#: Set this to any non-empty value to run the exhaustive cases.
EXHAUSTIVE_ENV = "GLM_EXHAUSTIVE"

SKIP_REASON = (
    "exhaustive: certifies rather than samples; run it with --exhaustive, "
    f"with {EXHAUSTIVE_ENV}=1, or through "
    "`python3 -m glm_universal.signoff --release`"
)


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--exhaustive", action="store_true", default=False,
        help="run the exhaustive searches and full sweeps as well "
             "(equivalently: %s=1)" % EXHAUSTIVE_ENV,
    )


def pytest_configure(config) -> None:
    config.addinivalue_line(
        "markers",
        "exhaustive: a search or sweep that certifies rather than samples. "
        "Deselected unless --exhaustive or %s=1; always run at round close."
        % EXHAUSTIVE_ENV,
    )


def exhaustive_enabled(config=None) -> bool:
    """Whether the exhaustive cases are switched on for this run."""
    if os.environ.get(EXHAUSTIVE_ENV, "").strip() not in ("", "0", "false"):
        return True
    if config is not None:
        try:
            return bool(config.getoption("--exhaustive"))
        except ValueError:  # pragma: no cover - option not registered
            return False
    return False


def pytest_collection_modifyitems(config, items) -> None:
    if exhaustive_enabled(config):
        return
    skip = pytest.mark.skip(reason=SKIP_REASON)
    for item in items:
        if item.get_closest_marker("exhaustive") is not None:
            item.add_marker(skip)

"""STAND-IN for ``glm_universal/evaluation/harness.py`` (Round 11, not the owner's module).

Why it exists: ``glm_universal/evaluation/__init__.py`` imports five names from
``.harness``.  Python runs that ``__init__`` whenever *any* ``glm_universal.evaluation.*``
submodule is imported -- e.g. ``runtime/stepwise.py`` imports
``evaluation.stepwise_cases`` -- so without a ``harness`` module the stepwise planner,
``engineering/speak`` and therefore ``GLM.py --ask`` cannot even be imported.

The ``harness.py`` attached in Round 11 is byte-identical to
``capabilities/harness.py`` (the capability-probe harness), not the evaluation harness.

This stand-in defines the imported names so that the *answering* path imports.  It does
NOT score anything: every scoring entry point raises ``NotImplementedError`` naming the
missing file.  Replace it with the real ``evaluation/harness.py`` from the working tree.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI_PATH = os.path.join(os.path.dirname(PACKAGE_ROOT), "GLM.py")

_MISSING = ("evaluation/harness.py is not in this checkout (Round 11 stand-in); "
            "the evaluation scorer cannot run. Copy the real module from the GLM tree.")


@dataclass
class CaseResult:
    case: Any = None
    status: str = "not-run"
    output: str = ""
    detail: Dict[str, Any] = field(default_factory=dict)


def run_case(*_a, **_k):
    raise NotImplementedError(_MISSING)


def run_all(*_a, **_k):
    raise NotImplementedError(_MISSING)


def evaluation_report(*_a, **_k):
    raise NotImplementedError(_MISSING)


def format_report(*_a, **_k):
    raise NotImplementedError(_MISSING)


def write_json(*_a, **_k):
    raise NotImplementedError(_MISSING)

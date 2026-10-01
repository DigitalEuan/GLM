"""``glm_universal.evaluation`` -- what the machine can actually do, measured.

The capability probes ask *where does the machine stop?* and the benchmark
suites score bodies of curated tasks.  Neither drives the thing a user
actually touches.  This sub-package does: a fixed set of questions across
every query kind and every report subject, each with an expected answer or an
expected refusal, each run through ``GLM.py`` in a fresh interpreter and
scored automatically.

    PYTHONPATH=. python3 -m glm_universal.evaluation

A refusal that was expected counts as a pass; a refusal that was not counts as
a gap; a confident answer where the honest answer is a refusal, or an answer
that contradicts the ground truth, counts as a *worse* failure than either.
Every failure is reported with the exact point at which it stops, and every
expected refusal is classified as a **boundary** (a theorem or a deliberate
limit of the register: crossing it is not possible) or a **gap** (a missing
implementation: crossing it is a work item).

The write-up of a full run is ``CAPABILITY_ASSESSMENT.md`` at the top of the
repository.
"""

from .cases import CASES, EvalCase, cases_by_kind
from .harness import (CaseResult, evaluation_report, format_report, run_all,
                      run_case)

__all__ = [
    "CASES", "EvalCase", "cases_by_kind",
    "CaseResult", "run_case", "run_all", "evaluation_report", "format_report",
]

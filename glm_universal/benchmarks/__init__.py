"""`glm_universal.benchmarks` — task suites and scoring.

Importing this package registers every suite in :mod:`.suites`, so the
registry is populated before the first call to :func:`run_all`.

```python
from glm_universal import benchmarks as bm

bm.suite_names()                      # ('analogy_chemistry', ...)
bm.run_suite("golay_correction")      # one SuiteScore
bm.benchmark_report()                 # every score, claim and finding
bm.write_results()                    # the same, written into results/
```

From the command line:

```bash
PYTHONPATH=. python3 -m glm_universal.benchmarks            # run and print
PYTHONPATH=. python3 -m glm_universal.benchmarks --write    # and write results/
PYTHONPATH=. python3 GLM.py -q "report benchmarks" -c 1     # through the runtime
```

The rules the harness enforces are in :mod:`.harness`: a declared evidence
tier before any score, exact rational arithmetic, and findings — including
null and negative results — reported beside the numbers rather than in place
of them.
"""

from __future__ import annotations

from .harness import (EvidenceTier, Finding, Suite, SuiteScore, TaskOutcome,
                      benchmark_report, frac_str, get_suite, register,
                      results_dir, run_all, run_suite, suite_names,
                      write_results)
from . import suites  # noqa: F401  -- imported for its registrations
from .suites import (CHEMISTRY_ANALOGIES, PHYSICS_ANALOGIES,
                     PHYSICS_EQUATIONS_FALSE, PHYSICS_EQUATIONS_TRUE,
                     SEMANTIC_ANALOGIES)

__all__ = [
    "EvidenceTier", "Finding", "Suite", "SuiteScore", "TaskOutcome",
    "benchmark_report", "frac_str", "get_suite", "register", "results_dir",
    "run_all", "run_suite", "suite_names", "write_results",
    "CHEMISTRY_ANALOGIES", "PHYSICS_ANALOGIES", "PHYSICS_EQUATIONS_FALSE",
    "PHYSICS_EQUATIONS_TRUE", "SEMANTIC_ANALOGIES",
]

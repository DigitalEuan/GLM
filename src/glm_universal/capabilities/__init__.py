"""``glm_universal.capabilities`` -- what the machine can do, and where it stops.

The rest of the test suite asks whether the machine still behaves as it did.
This package asks the other question: *what can it do at all?*  A probe states
a capability in a user's words, puts it to the real code, and reports either
that it holds -- with how far it was pushed -- or that it breaks, with the
place it stops stated exactly.

```python
from glm_universal import capabilities as cap

cap.probe_names()                    # every declared capability
cap.run_probe("real_equality_is_decidable")
cap.capability_report()              # all of them, grouped by area
```

From the command line:

```bash
PYTHONPATH=. python3 -m glm_universal.capabilities
PYTHONPATH=. python3 GLM.py -q "report capabilities" -c 1
```

A probe that comes back ``breaks`` is not a failure.  Several of the
boundaries here are theorems -- the Golay repair radius, the undecidability of
equality between two processes, the convex hull that bounds what the 24-D
dynamic carrier can reach -- and will never move.  The others are the work
list.
"""

from __future__ import annotations

from .harness import (AREAS, Outcome, Probe, breaks, capability_report,
                      get_probe, holds, probe, probe_names, register,
                      run_all, run_probe)
from . import probes  # noqa: F401  -- imported for its registrations
from . import probes_language  # noqa: F401  -- likewise
from .probes import ALL_PROBE_NAMES
from .probes_language import LANGUAGE_PROBE_NAMES

__all__ = [
    "AREAS", "Outcome", "Probe", "breaks", "capability_report", "get_probe",
    "holds", "probe", "probe_names", "register", "run_all", "run_probe",
    "ALL_PROBE_NAMES", "LANGUAGE_PROBE_NAMES",
]

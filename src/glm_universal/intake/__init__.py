"""``glm_universal.intake`` -- the intake pipeline for supplied material (directive D22).

*Created 31 October 2026 (repository check; directive D22).*

New material enters through ``source_material/ToDo/`` and is absorbed only
through the pipeline's gates: a study, tests, Lean written and then verified
by a passing build, and measured help.  An item whose intake is finished -- absorbed, or closed with a recorded
reason -- is filed under ``source_material/done/``.  The ledger
``source_material/INTAKE.yaml`` holds one record per item.

``python3 -m glm_universal.intake``:

=========================  ================================================
``status``                 the table of items and their stages
``check``                  ledger <-> folders, and every stage's evidence
``show <id>``              one record
``register <path>``        a new item -> ``ToDo/`` and a ledger stub
``scaffold <id>``          a draft study pair from the house template
``advance <id> <stage>``   move an item on, after its gate passes
``provisional <id>``       install an item's staged code ahead of the build
                           record, by the owner's decision (``--decision``);
                           its parts become ``provisional`` and answers that
                           rest on it say so
``absorb-staged <id>``     absorb an item's staged and provisional parts (same
                           gate as ``absorbed``); its open parts stay open
``close <id> --reason``    finish without absorption; filed in ``done/``
=========================  ================================================

:mod:`.ledger` reads and writes the ledger, :mod:`.gates` holds the evidence
each stage needs and :mod:`.actions` does what the commands do.  Every path
comes from :mod:`glm_universal.constants`; ``lake build`` itself runs on the
owner's machine (``scripts/rebuild_lean.sh``).  The pipeline checks the
build's inputs with ``python3 -m glm_universal.lean_check`` (stage ``Lean
written``, a preliminary gate) and promotes an item to ``Lean verified`` only
on the build record that script writes after a passing build, matched file by
file against the named Lean files and everything they import.

*Last altered 31 October 2026: the ``Lean written`` / ``Lean verified`` split;
then ``provisional``, for the owner's decision to keep the new wheels
installed, marked provisional, until the Lean build confirms them.*
"""
from __future__ import annotations

from .ledger import (  # noqa: F401
    KINDS, SCHEMA, STAGE_NAMES, STAGES, Layout, LedgerError, load, save,
)
from .gates import check, evidence_problems, lean_state  # noqa: F401
from .actions import (  # noqa: F401
    absorb_staged, advance, close, intake_report, provisional, register, scaffold, status_rows,
    status_table,
)

__all__ = [
    "KINDS", "SCHEMA", "STAGE_NAMES", "STAGES", "Layout", "LedgerError", "load",
    "save", "check", "evidence_problems", "lean_state", "advance", "absorb_staged", "close",
    "provisional",
    "intake_report", "register", "scaffold", "status_rows", "status_table",
]

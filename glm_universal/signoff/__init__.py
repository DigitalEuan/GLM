"""``glm_universal.signoff`` -- run only what has changed, and prove the rest is unchanged.

The whole test suite takes about a quarter of an hour.  Most iterations touch
one module.  Re-running everything is the safe thing to do and the slow thing
to do, and the usual escape -- "I'm fairly sure that part is fine" -- is not a
verification, it is a guess.

This package makes the guess into a check.  A test file is **signed off** when
it has passed and nothing it depends on has changed since, where *depends on*
is computed, not declared: the test file itself, every module of this package
it imports, transitively, every frozen data file those modules read, the
package's test scaffolding, and the interpreter version.  All of that is
reduced to one SHA-256 digest.  If the digest matches the one recorded when the
file passed, the result still holds and the file does not need running.  If a
single byte anywhere in that closure differs, the digest differs, and the file
is run again.

That is the *only* thing a digest is used for here.  A digest is an integrity
statement -- "this is the same bytes I checked" -- and never an encoding of
meaning; see directive **D3** of ``PROJECT_DIRECTIVES.md``, and
:mod:`glm_universal.reasoning.lean_address`, where the difference is measured
rather than asserted.

What it is careful about
------------------------
* **A failure is never signed off.**  Only a unit that passed is recorded, and
  a recorded failure keeps the unit stale until it passes.
* **The scaffolding is in every closure.**  ``tests/__init__.py`` and any
  ``conftest.py`` go into every unit's digest, so a change to the harness
  invalidates the whole ledger rather than being missed.
* **The interpreter is in the digest.**  A ledger written under one Python
  version signs nothing under another.
* **Data files count.**  Every file under a ``_data`` directory reachable from
  the closure is hashed, so a regenerated table invalidates whatever reads it.
* **Documents count too.**  A module that names a document -- ``STATUS.md``,
  ``MASTER_PLAN.md`` -- has that document in its closure, and one that names a
  ``.lean`` file has the whole Lean development in its closure.  Editing a
  document therefore makes exactly the units that read it stale, which is what
  keeps the drift checks honest while the documents are being written.
* **The other instruments are signed off the same way.**  ``lake build``, the
  end-to-end evaluation, the benchmarks, the probes and the figures check are
  units too; see :mod:`glm_universal.signoff.checks`.
* **Nothing is skipped silently.**  ``--plan`` prints what will be skipped and
  why before anything runs, and ``--verify`` re-checks every signature without
  running a test.
* **The full run stays available.**  ``--run-all`` ignores the ledger
  completely, and is what a release check does.

Typical use::

    cd overlay
    PYTHONPATH=. python3 -m glm_universal.signoff --plan     # what would run
    PYTHONPATH=. python3 -m glm_universal.signoff --run      # run the stale ones
    PYTHONPATH=. python3 -m glm_universal.signoff --verify   # re-check signatures
    PYTHONPATH=. python3 -m glm_universal.signoff --run-all  # ignore the ledger
    PYTHONPATH=. python3 -m glm_universal.signoff --run-checks    # the rest
    PYTHONPATH=. python3 -m glm_universal.signoff --run-everything

The ledger is ``overlay/.glm_signoff.json``, committed with the code, so the
saving carries between sessions rather than being rebuilt every time.
"""

from __future__ import annotations

from .checks import (
    CHECKS,
    Check,
    CheckUnit,
    check_closure,
    check_digest,
    check_plan,
    checks_by_name,
    predicted_check_saving,
    run_checks,
    verify_checks,
)
from .ledger import (
    LEDGER_PATH,
    SCHEMA,
    Unit,
    document_index,
    file_digest,
    interpreter_tag,
    lean_sources,
    load_ledger,
    plan,
    predicted_saving,
    referenced_documents,
    run_plan,
    save_ledger,
    scaffolding_paths,
    sign,
    test_units,
    tree_digest,
    unit_closure,
    unit_digest,
    verify,
)

__all__ = [
    "CHECKS",
    "Check",
    "CheckUnit",
    "LEDGER_PATH",
    "SCHEMA",
    "Unit",
    "check_closure",
    "check_digest",
    "check_plan",
    "checks_by_name",
    "document_index",
    "file_digest",
    "interpreter_tag",
    "lean_sources",
    "load_ledger",
    "plan",
    "predicted_check_saving",
    "predicted_saving",
    "referenced_documents",
    "run_checks",
    "run_plan",
    "save_ledger",
    "scaffolding_paths",
    "sign",
    "test_units",
    "tree_digest",
    "unit_closure",
    "unit_digest",
    "verify",
    "verify_checks",
]

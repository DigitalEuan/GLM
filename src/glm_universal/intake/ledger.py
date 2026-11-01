"""``glm_universal.intake.ledger`` -- the intake ledger and the folders it describes.

*Created 31 October 2026 (repository check; directive D22).*
*Last altered 31 October 2026: the stage ``lean_written`` (the static check)
split from ``lean_verified`` (a passing build record), the field
``lean_build``, and the part status ``staged``; the fields ``acceptance``
and ``legacy_absorption``, and the header's account of test fingerprints and
of the test runner where pytest is absent; then the part status
``provisional`` and the register of provisional wheel families
(:attr:`Layout.provisional`, :func:`load_provisional`,
:func:`save_provisional`), for the owner's decision of the same day to keep
the new wheels installed, marked provisional, until the Lean build confirms
them.*
*Last altered 1 November 2026 (Phase 186): absorption ahead of the build -- the
field ``ahead_of_build`` (:data:`AHEAD_FIELD`) and the register state
:data:`AHEAD_STATE` -- for the owner's decision of that day: "Absorb the ones
that measurably help now, based on your measurements and standalone Lean
check; record that my own rebuild_lean.sh run still has to confirm them".*

Everything the owner supplies arrives in ``source_material/``.  An item -- a
folder or a loose file -- is filed under ``source_material/ToDo/`` while its
intake is open and under ``source_material/done/`` once it is finished:
absorbed into the GLM through every gate, or closed with a recorded reason.
The ledger ``source_material/INTAKE.yaml`` holds one record per item.  This
module reads and writes it, and names the folders (every path comes from
:mod:`glm_universal.constants`, directive D21; a :class:`Layout` can be
re-rooted so the tests run on a scratch tree).

**The stages.**  An item moves along one line, and a stage is only reached
with its evidence (checked by :mod:`glm_universal.intake.gates`):

=================  ==========================================================
``received``       the item is in ``ToDo/`` and has a record
``triaged``        its kind and what it claims or offers are written down
``study_drafted``  a study pair ``studies/<ID>_STUDY.md`` + ``.yaml`` exists
``tested``         named tests exist, and their dated results are recorded
``lean_written``   named Lean files are in the build tree, imported by the
                   axiom audit, and the static check passes (no build yet)
``lean_verified``  a passing build record (``scripts/rebuild_lean.sh``) in
                   which each named Lean file and every file it imports is
                   byte for byte the current file
``measured``       a study records a deciding figure for the help it gives
``absorbed``       the modules it became exist and are tested; ``done/``
``closed``         finished without absorption, with a reason and evidence;
                   ``done/``
=================  ==========================================================

A record's ``stage`` is the stage of the item's *open* work.  Parts of an item
that were taken earlier are listed under ``parts`` (status ``absorbed`` or
``closed``) with where they went, so an item whose first parts are absorbed
but whose others are untouched stays in ``ToDo/`` at the stage of the rest.
A part may also be ``staged`` (its code waits in the item's ``staged/``
folder for the build record) or ``provisional`` (its code is installed in the
package ahead of the build record by an owner's decision, recorded in the
register :attr:`Layout.provisional`); both are open work and keep the item in
``ToDo/``.

**Absorbed ahead of the build.**  By an owner's decision an item that has
passed every gate but the build record -- tests current, Lean written and
statically checked, a closed study and an acceptance decision -- may be
absorbed now, on its measurements and a standalone Lean check: the record
keeps ``ahead_of_build`` (the decision, its date, the Lean files checked on
their own, how they were checked) in place of ``lean_build``, the item is
filed in ``done/``, and its entry in the register :attr:`Layout.provisional`
takes the state :data:`AHEAD_STATE`, so the answers that rest on it still say
that the owner's build has to confirm it.  ``confirm-build`` ends the state
when the build record verifies the item's Lean files.

Nothing here constructs a float or imports a digest.
"""
from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .. import constants as C

__all__ = [
    "SCHEMA", "STAGES", "STAGE_NAMES", "TERMINAL", "KINDS", "PART_STATUSES",
    "FIELD_ORDER", "Layout", "today", "stage_key", "stage_index",
    "load", "save", "record_by_id", "item_location", "folder_items",
    "LedgerError", "UNFINISHED_PART_STATUSES", "PROVISIONAL_SCHEMA", "load_provisional",
    "save_provisional", "AHEAD_FIELD", "AHEAD_STATE",
]

#: The ledger's schema tag.
SCHEMA = "glm-intake-ledger/v1"

#: The stages, in order.  ``closed`` is the other way out.
STAGES: Tuple[str, ...] = (
    "received", "triaged", "study_drafted", "tested", "lean_written",
    "lean_verified", "measured", "absorbed",
)
TERMINAL: Tuple[str, ...] = ("absorbed", "closed")

#: How each stage is written in prose and in the status table.
STAGE_NAMES: Dict[str, str] = {
    "received": "received",
    "triaged": "triaged",
    "study_drafted": "study drafted",
    "tested": "tested",
    "lean_written": "Lean written",
    "lean_verified": "Lean verified",
    "measured": "measured",
    "absorbed": "absorbed",
    "closed": "closed",
}

#: What an item can be.
KINDS: Tuple[str, ...] = ("full study", "code", "concept note", "data", "Lean", "plan")

#: The fate of a part of an item.  ``staged``: the part's code waits in the
#: item's ``staged/`` folder for the build record; absorption installs it and
#: the part becomes ``absorbed``.  ``provisional``: the part's code is already
#: installed in the package, ahead of the build record, by an owner's decision
#: recorded in the register of provisional families (:attr:`Layout.provisional`);
#: answers that rest on it say so, and absorption on a verifying build record
#: makes it ``absorbed`` and removes the register entry.
PART_STATUSES: Tuple[str, ...] = ("absorbed", "closed", "open", "provisional", "staged")

#: The part statuses that are still open work (none may stand in ``done/``).
UNFINISHED_PART_STATUSES: Tuple[str, ...] = ("open", "provisional", "staged")

#: The schema of the register of provisional families.
PROVISIONAL_SCHEMA = "glm-provisional-wheels/v1"

#: The record field of an item absorbed ahead of the build by an owner's
#: decision: ``{decision, date, standalone, check, confirm}`` (see the module
#: docstring).  It stands in for ``lean_build`` until ``confirm-build``.
AHEAD_FIELD = "ahead_of_build"

#: The ``state`` of a register entry whose item is absorbed ahead of the build
#: (an entry without ``state`` is ``provisional``).
AHEAD_STATE = "absorbed ahead of the build"

#: The fields of a record, in the order they are written.
FIELD_ORDER: Tuple[str, ...] = (
    "id", "path", "local_only", "kind", "offers", "stage", "studies", "tests",
    "test_results", "lean", "lean_check", "lean_build", "ahead_of_build", "lean_obligations",
    "measured",
    "acceptance", "legacy_absorption", "absorbed_into", "installed", "parts", "wheels", "closed_reason", "evidence",
    "last_action", "next_step",
)


class LedgerError(Exception):
    """The ledger cannot be read or an action on it is refused."""


@dataclass(frozen=True)
class Layout:
    """Where the intake pipeline looks.  :meth:`default` is the repository;
    :meth:`under` builds the same shape below another root (for tests)."""

    root: Path
    material: Path
    todo: Path
    done: Path
    ledger: Path
    studies: Path
    package: Path
    lean_source: Path
    lean_library: str
    lean_holding: Path
    lean_audit: Path
    lean_needed: Path
    lean_evidence: Path

    @classmethod
    def default(cls) -> "Layout":
        return cls(
            root=C.REPOSITORY_ROOT, material=C.SOURCE_MATERIAL_DIR,
            todo=C.SOURCE_TODO_DIR, done=C.SOURCE_DONE_DIR,
            ledger=C.INTAKE_LEDGER, studies=C.STUDIES_DIR,
            package=C.PACKAGE_ROOT, lean_source=C.LEAN_SOURCE_DIR,
            lean_library=C.LEAN_LIBRARY, lean_holding=C.LEAN_HOLDING_DIR,
            lean_audit=C.LEAN_AUDIT_FILE, lean_needed=C.LEAN_FILES_NEEDED,
            lean_evidence=C.LEAN_BUILD_EVIDENCE,
        )

    @classmethod
    def under(cls, root: Path) -> "Layout":
        """The repository's shape, re-rooted at ``root``: every path keeps its
        position relative to the repository root."""
        d = cls.default()
        r = Path(root)

        def move(p: Path) -> Path:
            return r / p.relative_to(d.root)

        return replace(
            d, root=r, material=move(d.material), todo=move(d.todo),
            done=move(d.done), ledger=move(d.ledger), studies=move(d.studies),
            package=move(d.package), lean_source=move(d.lean_source),
            lean_holding=move(d.lean_holding), lean_audit=move(d.lean_audit),
            lean_needed=move(d.lean_needed), lean_evidence=move(d.lean_evidence),
        )

    @property
    def lean_glm(self) -> Path:
        """``src/lean/RequestProject/GLM`` (or its re-rooted twin)."""
        return self.lean_source / self.lean_library / "GLM"

    @property
    def provisional(self) -> Path:
        """The register of wheel families installed provisionally,
        ``src/glm_universal/wheels/_data/provisional.json`` (or its re-rooted
        twin); :data:`glm_universal.wheels.PROVISIONAL_REGISTER` reads it."""
        return self.package / "wheels" / "_data" / "provisional.json"


def today(day: Optional[datetime.date] = None) -> str:
    """A date in the repository's form, ``31 October 2026`` (directive D17)."""
    d = day or datetime.date.today()
    return f"{d.day} {d.strftime('%B')} {d.year}"


def stage_key(text: str) -> str:
    """The canonical key of a stage written any reasonable way
    (``"Lean verified"``, ``"lean-verified"``, ``"LEAN_VERIFIED"``)."""
    key = text.strip().lower().replace("-", "_").replace(" ", "_")
    if key not in STAGES and key != "closed":
        raise LedgerError(f"unknown stage {text!r}; the stages are "
                          + ", ".join(STAGE_NAMES[s] for s in STAGES) + ", closed")
    return key


def stage_index(stage: str) -> int:
    """Position on the line (``closed`` is past every stage)."""
    return len(STAGES) if stage == "closed" else STAGES.index(stage)


def _yaml():
    try:
        import yaml  # PyYAML, as corpus/study_ledger.py uses it
    except ImportError as exc:  # pragma: no cover - environment
        raise LedgerError("PyYAML is needed to read the intake ledger") from exc
    return yaml


def load(layout: Optional[Layout] = None) -> Dict[str, Any]:
    """The ledger as a mapping (``schema``, ``created``, ``last_altered``,
    ``items``).  A missing ledger is an empty one."""
    lay = layout or Layout.default()
    if not lay.ledger.is_file():
        return {"schema": SCHEMA, "created": today(), "last_altered": today(), "items": []}
    data = _yaml().safe_load(lay.ledger.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise LedgerError(f"{lay.ledger} is not a mapping")
    data.setdefault("items", [])
    if not isinstance(data["items"], list):
        raise LedgerError(f"{lay.ledger}: 'items' is not a list")
    return data


_HEADER = """\
# source_material/INTAKE.yaml -- the intake ledger (directive D22)
#
# Created 31 October 2026 (repository check).  One record per supplied item
# (a folder or a loose file directly under source_material/ToDo/ or
# source_material/done/).  Read and written by `python3 -m glm_universal.intake`;
# `python3 -m glm_universal.intake check` fails when this file and the folders
# disagree, or when a record claims a stage without its evidence.
#
# Stages, in order: received -> triaged -> study_drafted -> tested ->
# lean_written -> lean_verified -> measured -> absorbed (filed in done/), or
# closed with a reason (filed in done/).  lean_written: the Lean files are in
# the build tree and the audit and the static check passes; lean_verified:
# the owner's build record scripts/logs/lean_build_evidence.json (written by
# scripts/rebuild_lean.sh after a passing build) matches those files and
# everything they import, and lean_build records which build that was.  `stage` is the stage of the item's open work;
# parts taken earlier are listed under `parts` with where they went.  A part's
# status is absorbed, closed, open, staged (its code waits in the item's
# staged/ folder for the build record) or provisional (its code is installed
# in the package ahead of the build record by the owner's decision, recorded
# in src/glm_universal/wheels/_data/provisional.json; answers resting on it say
# so; absorption on a verifying build record makes it absorbed and removes the
# register entry).  staged, provisional and open parts keep an item in ToDo/.
# ahead_of_build (added 1 November 2026) marks an item absorbed ahead of the
# build by the owner's decision, on its measurements and a standalone Lean
# check -- {decision, date, standalone (the Lean files checked on their own),
# check (how), confirm} -- in place of lean_build; its register entry has the
# state "absorbed ahead of the build", and `python3 -m glm_universal.intake
# confirm-build <id>` replaces the field by lean_build once the build record
# of scripts/rebuild_lean.sh verifies the item's Lean files.
#
# Field guide: tests are package-relative (`tests/test_x.py`, run with pytest,
# or where it is not installed with `python3 -m
# glm_universal.intake.fallback_tests`, which never passes a file in which no
# test ran), `item:<path> [args]` (a script inside the item, run
# with python3 in a scratch copy of the item; `item:` alone runs a single-file
# item), `call:<module>.<function>` (a study's recompute function, called in
# a fresh interpreter) or `staged:<path>` (a test run against the item's
# staged/ code in a scratch overlay of the package); test_results holds
# {test, result, detail, date, fingerprint} entries, newest last (a detail is
# written by the intake -- the exit code, what it means and, for a package
# test, the counts -- and never copies what the test printed): `tested`
# needs the last result of every named test to be `pass`, and a promotion
# accepts only a pass whose fingerprint is that of the code as it now stands
# (the package, the item and its staged files), running any other again;
# lean names are relative to src/lean/RequestProject/GLM; absorbed_into names
# modules relative to src/glm_universal (`reasoning/pcgs`); measured starts
# with the id of the closed, finished study whose deciding figure records the
# measurement; acceptance is the decision against that study's declared
# criterion -- {study, criterion, result (both quoted from the study), marks
# (met marks that carry the help), decision: accept, date} -- written by
# `python3 -m glm_universal.intake accept` and required by every promotion to
# measured or beyond; legacy_absorption marks a record absorbed by an earlier
# round, before acceptance decisions were recorded (done/ and absorbed only;
# no promotion accepts it); local_only marks a file kept on the owner's
# machine and out of version control (*.zip, *.pdf).
"""


def _ordered(rec: Mapping[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in FIELD_ORDER:
        if k in rec and rec[k] not in (None, [], ""):
            out[k] = rec[k]
    for k in rec:  # unknown fields are kept, after the known ones
        if k not in out and k not in FIELD_ORDER:
            out[k] = rec[k]
    return out


def save(data: Mapping[str, Any], layout: Optional[Layout] = None,
         day: Optional[datetime.date] = None) -> Path:
    """Write the ledger (header, then the mapping with each record's fields in
    :data:`FIELD_ORDER`), stamping ``last_altered``."""
    lay = layout or Layout.default()
    body = {
        "schema": SCHEMA,
        "created": data.get("created") or today(day),
        "last_altered": today(day),
        "items": [_ordered(r) for r in data.get("items", [])],
    }
    text = _HEADER + "\n" + _yaml().safe_dump(
        body, sort_keys=False, allow_unicode=True, width=96, default_flow_style=False)
    lay.ledger.parent.mkdir(parents=True, exist_ok=True)
    lay.ledger.write_text(text, encoding="utf-8")
    return lay.ledger


_PROVISIONAL_ABOUT = (
    "Wheel families installed in src/glm_universal/wheels/ ahead of their Lean build, by "
    "the owner's decision of 31 October 2026 ('keep them in the wheels folder now, clearly "
    "marked provisional until my Lean build log confirms them'). Each entry is an intake "
    "item of source_material/INTAKE.yaml whose parts are recorded 'provisional'. Answers "
    "that rest on these wheels say so (glm_universal.wheels.provisional_status). Written "
    "by the intake: `python3 -m glm_universal.intake advance <item> absorbed` (or "
    "`absorb-staged <item>`) removes an item's entry once the build record of "
    "scripts/rebuild_lean.sh verifies its Lean files; `python3 -m glm_universal.intake "
    "check` requires this file and the ledger to agree. Created 31 October 2026 "
    "(repository check). Since 1 November 2026 an entry may also have the state 'absorbed "
    "ahead of the build': the owner's decision of that day ('Absorb the ones that measurably "
    "help now, based on your measurements and standalone Lean check; record that my own "
    "rebuild_lean.sh run still has to confirm them') absorbed the item on its measurements "
    "and a standalone Lean check; answers resting on it say that the owner's build still has "
    "to confirm it, and `python3 -m glm_universal.intake confirm-build <item>` removes the "
    "entry once the build record verifies the item's Lean files.")


def load_provisional(layout: Optional[Layout] = None) -> Dict[str, Dict[str, Any]]:
    """The register of provisional families, by intake item id (empty when
    the register is absent).  Raises :class:`LedgerError` when it is not
    readable JSON of the right shape."""
    lay = layout or Layout.default()
    if not lay.provisional.is_file():
        return {}
    try:
        data = json.loads(lay.provisional.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise LedgerError(f"{lay.provisional} is not JSON: {exc}") from exc
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, dict) or not all(isinstance(v, dict) for v in items.values()):
        raise LedgerError(f"{lay.provisional}: 'items' is not a mapping of records")
    return {str(k): dict(v) for k, v in items.items()}


def save_provisional(items: Mapping[str, Mapping[str, Any]],
                     layout: Optional[Layout] = None) -> Path:
    """Write the register of provisional families (sorted keys, one space
    indent, as every stored JSON of the package)."""
    lay = layout or Layout.default()
    body = {"about": _PROVISIONAL_ABOUT, "schema": PROVISIONAL_SCHEMA,
            "items": {k: dict(v) for k, v in items.items()}}
    lay.provisional.parent.mkdir(parents=True, exist_ok=True)
    lay.provisional.write_text(json.dumps(body, indent=1, sort_keys=True, ensure_ascii=False)
                               + "\n", encoding="utf-8")
    return lay.provisional


def record_by_id(data: Mapping[str, Any], item_id: str) -> Dict[str, Any]:
    for rec in data.get("items", []):
        if rec.get("id") == item_id:
            return rec
    raise LedgerError(f"no intake record has id {item_id!r}")


def item_location(path: str, layout: Optional[Layout] = None) -> Path:
    """The file-system path of a record's ``path`` (``ToDo/x`` or ``done/x``)."""
    lay = layout or Layout.default()
    return lay.material / path


#: Files of the two folders that are not items.
NOT_ITEMS = frozenset({"README.md", "__pycache__", ".DS_Store"})


def folder_items(layout: Optional[Layout] = None) -> Dict[str, Path]:
    """Every item filed in ``ToDo/`` and ``done/``: ``{"ToDo/x": path, ...}``."""
    lay = layout or Layout.default()
    out: Dict[str, Path] = {}
    for folder, name in ((lay.todo, "ToDo"), (lay.done, "done")):
        if not folder.is_dir():
            continue
        for p in sorted(folder.iterdir()):
            if p.name in NOT_ITEMS or p.name.startswith("."):
                continue
            out[f"{name}/{p.name}"] = p
    return out


def loose_items(layout: Optional[Layout] = None) -> List[Path]:
    """Anything directly under ``source_material/`` that is neither a filing
    folder, the ledger nor the README: material not yet registered."""
    lay = layout or Layout.default()
    allowed = {lay.todo.name, lay.done.name, lay.ledger.name, "README.md", "__pycache__"}
    if not lay.material.is_dir():
        return []
    return [p for p in sorted(lay.material.iterdir())
            if p.name not in allowed and not p.name.startswith(".")]


def as_list(value: Any) -> List[Any]:
    """A record field read as a list (a lone string becomes one element)."""
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def iter_records(data: Mapping[str, Any]) -> Sequence[Dict[str, Any]]:
    return list(data.get("items", []))

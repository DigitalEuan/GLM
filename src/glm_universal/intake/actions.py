"""``glm_universal.intake.actions`` -- what the intake commands do.

*Created 31 October 2026 (repository check; directive D22).*
*Last altered 31 October 2026: ``lean_written`` runs the static check;
``lean_verified`` and every later promotion need the current build record;
staged code, its overlay and ``absorb_staged``; every test result records the
fingerprint of the code it ran against, a promotion re-runs any test whose
result is not current, and absorption (``absorbed``, ``absorb-staged``)
re-runs every named test immediately before installing anything; ``accept``
records the acceptance decision the ``measured`` gate needs; then
``provisional`` (install an item's staged code ahead of the build record, by
the owner's decision, its parts recorded ``provisional`` and the item entered
in the register of provisional families), and absorption that confirms
provisional parts and removes the register entry; a test result's ``detail``
is written by :func:`describe_exit` (exit code, its meaning, the counts of a
package test) and never copies what the test printed.*
*Last altered 1 November 2026 (Phase 186): ``absorb_ahead`` (absorb an item
ahead of the build record, on its measurements and a standalone Lean check,
by the owner's decision of that day) and ``confirm_build`` (the build record
confirms such an absorption).*

Each action reads the ledger, acts, and writes the ledger back with the day's
date in ``last_action``.  An action that would break a rule is refused with a
:class:`~glm_universal.intake.ledger.LedgerError` and changes nothing; a gate
that fails during :func:`advance` still records the test results it took
(a failed run is a result), but the stage does not move.

``register``  a new item: moved (or copied) into ``ToDo/``, with a stub record
              at ``received``.
``scaffold``  a draft study pair ``studies/<ID>_STUDY.md`` + ``.yaml`` in the
              house shape: the Tier-0 block, the questions, the marks declared
              before the code, the Lean obligations.  Never overwrites.
``advance``   the item moves on only when every stage it passes through has
              its evidence (:mod:`.gates`).  Passing ``tested`` runs the named
              tests, and any later promotion runs again each test whose last
              result is not a pass taken against the code as it now stands
              (:func:`gates.test_fingerprint`); promotion to ``absorbed``
              runs them all again before installing; passing ``lean_written`` runs
              ``python3 -m glm_universal.lean_check`` (static, preliminary);
              promotion to ``lean_verified`` or beyond needs the current build
              record of ``scripts/rebuild_lean.sh`` (``lake build`` itself is
              the owner's) to verify the named Lean files and every file they
              import, and records that build in ``lean_build``; reaching
              ``absorbed`` files the item in ``done/``.
``absorb-staged``  an item's ``staged`` and ``provisional`` parts only, on
              the same evidence as ``absorbed`` (the build record and a fresh
              run of every named test included), while its other parts stay
              open; the item stays in ``ToDo/``.
``provisional``  the owner's decision to install an item's staged code before
              the build record: the item must stand at ``lean_written`` or
              beyond with every named test passing on a fresh run; the staged
              files are installed, every module they make must exist and have
              a test, the parts become ``provisional`` and the item is entered
              in the register of provisional families with the decision's
              words and date (answers resting on that code say so).  The item
              stays in ``ToDo/``; absorption on a verifying build record ends
              the provisional status.
``absorb-ahead``  the owner's decision of 1 November 2026 ("Absorb the ones
              that measurably help now, based on your measurements and
              standalone Lean check; record that my own rebuild_lean.sh run
              still has to confirm them"): an item at ``lean_written`` or
              beyond whose every gate up to ``measured`` holds with current
              tests -- the build record replaced by the ``ahead_of_build``
              record (the decision, the Lean files checked on their own,
              how) -- is absorbed now: staged code installed, its staged and
              provisional parts ``absorbed``, and its register entry put in
              the state ``absorbed ahead of the build`` so the answers
              resting on it still say the owner's build has to confirm it.
              With no open part the item is filed in ``done/``; with open
              parts it stays in ``ToDo/`` at its stage.
``confirm-build``  the build record of ``scripts/rebuild_lean.sh`` verifies the
              Lean files of an item absorbed ahead of the build:
              ``ahead_of_build`` becomes ``lean_build`` and the register entry
              goes.
``retest``    run an item's named tests again (all, or only those whose last
              result is not a current pass) and record the results; the stage
              does not move.
``accept``    the acceptance decision of a measured item: the criterion the
              study declared and the result it measured, each quoted from
              the study, the met marks that carry the help, and ``accept``;
              refused unless the block passes the ``measured`` gate
              (:func:`gates.measurement_problems`).  An item that fails its
              criterion is closed instead.
``close``     finished without absorption: a reason and evidence that exists;
              filed in ``done/``.

Code prepared for the package but not yet absorbed waits in the item's
``staged/`` folder; ``staged:<path>`` tests run it in a scratch overlay of the
package (:func:`staged_overlay`), and reaching ``absorbed`` installs it
(:func:`install_staged`), recording the paths in ``installed``.

Item tests run on a scratch copy of the item, so a supplied item stays
byte-identical however its scripts write.  Nothing here constructs a float.
"""
from __future__ import annotations

import datetime
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from .. import constants as C
from . import gates
from .ledger import (
    AHEAD_FIELD, AHEAD_STATE, KINDS, STAGE_NAMES, STAGES, TERMINAL, Layout, LedgerError, as_list,
    folder_items, item_location, load, load_provisional, loose_items, record_by_id, save,
    save_provisional, stage_index, stage_key, today,
)

__all__ = [
    "item_id_for", "study_id_for", "status_rows", "status_table",
    "intake_report", "register", "scaffold", "advance", "retest", "accept", "close",
    "run_test", "run_lean_check", "next_gate", "staged_overlay", "install_staged",
    "absorb_staged", "provisional", "absorb_ahead", "confirm_build",
]

#: A test runner: ``(ref, command, cwd, env, timeout) -> (result, detail)``
#: where ``result`` is ``pass``, ``fail``, ``timeout`` or ``error``.
Runner = Callable[[str, List[str], Path, Dict[str, str], int], Tuple[str, str]]
#: A Lean check: ``(layout, timeout) -> (ok, detail)``.
LeanChecker = Callable[[Layout, int], Tuple[bool, str]]


# ---------------------------------------------------------------------------
# Names
# ---------------------------------------------------------------------------

def item_id_for(name: str) -> str:
    """The record id of an item named ``name``: the file's stem (a folder's
    name), with every character other than a letter, digit or ``_`` turned
    into ``_``."""
    stem = Path(name).name
    if "." in stem and not stem.startswith("."):
        stem = stem.rsplit(".", 1)[0]
    out = re.sub(r"[^A-Za-z0-9_]+", "_", stem).strip("_")
    return out or "item"


def study_id_for(item_id: str) -> str:
    """The id of the study an item's intake drafts: ``cent_compiler_v12`` ->
    ``CENT_COMPILER_V12_STUDY``."""
    base = re.sub(r"[^A-Za-z0-9]+", "_", item_id).strip("_").upper()
    if base.endswith("_STUDY"):
        base = base[: -len("_STUDY")]
    return base + "_STUDY"


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

def status_rows(data: Optional[Mapping[str, Any]] = None,
                layout: Optional[Layout] = None) -> List[Dict[str, Any]]:
    """One row per record: id, folder, kind, stage, open evidence problems,
    the next step."""
    lay = layout or Layout.default()
    data = data if data is not None else load(lay)
    rows = []
    for rec in data.get("items", []):
        path = str(rec.get("path") or "")
        rows.append({
            "id": rec.get("id", "?"),
            "folder": path.split("/", 1)[0],
            "kind": rec.get("kind") or "-",
            "stage": rec.get("stage") or "received",
            "problems": len(gates.evidence_problems(rec, lay)),
            "next_step": str(rec.get("next_step") or "").strip(),
            "local_only": bool(rec.get("local_only")),
        })
    order = {"ToDo": 0, "done": 1}
    rows.sort(key=lambda r: (order.get(r["folder"], 2), stage_index(r["stage"])
                             if r["stage"] in STAGES or r["stage"] == "closed" else 99,
                             r["id"].lower()))
    return rows


def status_table(data: Optional[Mapping[str, Any]] = None,
                 layout: Optional[Layout] = None, width: int = 60) -> str:
    """The status table as text, with the count of items at each stage."""
    rows = status_rows(data, layout)
    head = ("id", "folder", "kind", "stage", "gaps", "next step")
    table = [head] + [(
        r["id"] + (" (local)" if r["local_only"] else ""), r["folder"], r["kind"],
        STAGE_NAMES.get(r["stage"], r["stage"]), str(r["problems"]),
        (r["next_step"][: width - 1] + "…") if len(r["next_step"]) > width else r["next_step"],
    ) for r in rows]
    widths = [max(len(row[i]) for row in table) for i in range(len(head) - 1)]
    lines = []
    for n, row in enumerate(table):
        lines.append("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row[:-1]))
                     + "  " + row[-1])
        if n == 0:
            lines.append("  ".join("-" * w for w in widths) + "  " + "-" * 9)
    counts: Dict[str, int] = {}
    for r in rows:
        counts[r["stage"]] = counts.get(r["stage"], 0) + 1
    summary = ", ".join(f"{STAGE_NAMES[s]} {counts[s]}" for s in (*STAGES, "closed")
                        if counts.get(s))
    lines.append("")
    lines.append(f"{len(rows)} items: " + summary)
    return "\n".join(lines)


def intake_report(layout: Optional[Layout] = None) -> Dict[str, Any]:
    """The intake ledger's figures, recomputed from the ledger and the
    folders: items per folder and per stage, parts absorbed, staged and
    provisional, items in the register of provisional families, files
    waiting in ``staged/`` folders, whether the owner's build record exists,
    acceptance decisions recorded, records absorbed before such decisions
    were recorded, open items whose test results are not current, wheels
    surveyed and their Lean obligations, and whether
    :func:`gates.check` passes."""
    lay = layout or Layout.default()
    data = load(lay)
    result = gates.check(data, lay)
    by_stage: Dict[str, int] = {s: 0 for s in (*STAGES, "closed")}
    by_folder = {"ToDo": 0, "done": 0}
    wheels = obligations = parts_absorbed = parts_staged = parts_provisional = staged = 0
    accepted = legacy = stale_items = 0
    for rec in data.get("items", []):
        accepted += isinstance(rec.get("acceptance"), Mapping)
        legacy += gates.is_legacy_absorption(rec)
        if (str(rec.get("path") or "").startswith("ToDo/")
                and rec.get("stage") not in TERMINAL and rec.get("stage") in STAGES
                and stage_index(rec["stage"]) >= stage_index("tested")
                and gates.stale_results(rec, lay)):
            stale_items += 1
        staged += len(gates.staged_files(rec, lay))
        parts_staged += sum(1 for p in as_list(rec.get("parts"))
                            if isinstance(p, Mapping) and p.get("status") == "staged")
        parts_provisional += sum(1 for p in as_list(rec.get("parts"))
                                 if isinstance(p, Mapping) and p.get("status") == "provisional")
        by_stage[rec.get("stage", "received")] = by_stage.get(rec.get("stage", "received"), 0) + 1
        folder = str(rec.get("path") or "").split("/", 1)[0]
        by_folder[folder] = by_folder.get(folder, 0) + 1
        for w in as_list(rec.get("wheels")):
            if isinstance(w, Mapping):
                wheels += 1
                obligations += len(as_list(w.get("lean_obligations")))
        parts_absorbed += sum(1 for p in as_list(rec.get("parts"))
                              if isinstance(p, Mapping) and p.get("status") == "absorbed")
    return {
        "items": len(data.get("items", [])),
        "todo": by_folder.get("ToDo", 0),
        "done": by_folder.get("done", 0),
        "by_stage": by_stage,
        "parts_absorbed": parts_absorbed,
        "parts_staged": parts_staged,
        "parts_provisional": parts_provisional,
        "provisional_items": len(gates.load_provisional_quiet(lay)),
        "staged_files": staged,
        "build_record": lay.lean_evidence.is_file(),
        "acceptances": accepted,
        "legacy_absorptions": legacy,
        "items_with_stale_results": stale_items,
        "wheels_surveyed": wheels,
        "lean_obligations": obligations,
        "filed": len(folder_items(lay)),
        "loose": len(loose_items(lay)),
        "check_ok": result["ok"],
        "errors": len(result["errors"]),
        "warnings": len(result["warnings"]),
    }


def next_gate(rec: Mapping[str, Any], layout: Optional[Layout] = None) -> Tuple[str, List[str]]:
    """The next stage of an open record and what its gate still lacks
    (``("", [])`` for a finished record)."""
    lay = layout or Layout.default()
    stage = rec.get("stage") or "received"
    if stage in TERMINAL:
        return "", []
    nxt = STAGES[stage_index(stage) + 1]
    return nxt, gates.stage_problems(rec, nxt, lay)


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------

def _stamp(rec: Dict[str, Any], what: str, day: Optional[datetime.date]) -> None:
    rec["last_action"] = f"{today(day)}: {what}"


def register(path: str, layout: Optional[Layout] = None, *, item_id: Optional[str] = None,
             kind: Optional[str] = None, offers: Optional[str] = None,
             day: Optional[datetime.date] = None, copy: Optional[bool] = None) -> Dict[str, Any]:
    """File a new item in ``ToDo/`` and add its stub record at ``received``.

    ``path`` is the new material: loose under ``source_material/`` (it is
    moved) or anywhere else (it is copied, unless ``copy=False``).  The id is
    :func:`item_id_for` of its name unless given; ``kind`` and ``offers`` may
    be given now or written at triage."""
    lay = layout or Layout.default()
    src = Path(path)
    if not src.is_absolute():
        cand = [lay.root / src, Path.cwd() / src]
        src = next((c for c in cand if c.exists()), cand[0])
    if not src.exists():
        raise LedgerError(f"{path} does not exist")
    src = src.resolve()
    for folder in (lay.todo, lay.done):
        if folder.resolve() in src.parents or src == folder.resolve():
            raise LedgerError(f"{path} is already filed under {folder.name}/")
    if kind is not None and kind not in KINDS:
        raise LedgerError(f"kind {kind!r} is not one of {', '.join(KINDS)}")
    data = load(lay)
    rid = item_id or item_id_for(src.name)
    ids = {r.get("id") for r in data.get("items", [])}
    if rid in ids:
        raise LedgerError(f"id {rid} is taken; give another with --id")
    for folder in (lay.todo, lay.done):
        if (folder / src.name).exists():
            raise LedgerError(f"{folder.name}/{src.name} already exists")
    lay.todo.mkdir(parents=True, exist_ok=True)
    dest = lay.todo / src.name
    loose = src.parent == lay.material.resolve()
    do_copy = (not loose) if copy is None else copy
    if do_copy:
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)
    else:
        shutil.move(str(src), str(dest))
    rec: Dict[str, Any] = {
        "id": rid,
        "path": f"ToDo/{src.name}",
        "kind": kind or "",
        "offers": offers or "",
        "stage": "received",
        "next_step": "triage: write kind, offers (what it claims or offers) and the next step, "
                     "then `advance " + rid + " triaged`",
    }
    if dest.suffix.lower() in (".zip", ".pdf"):
        rec["local_only"] = True
    _stamp(rec, ("copied" if do_copy else "moved") + f" into ToDo/ and registered", day)
    data.setdefault("items", []).append(rec)
    save(data, lay, day)
    return rec


# ---------------------------------------------------------------------------
# scaffold
# ---------------------------------------------------------------------------

_TIER0_FOOTER = ("*Tier 0 is a coarse read of what follows, never a claim of its own: the "
                 "verdict and the figure above are grounded in the body below, and "
                 "`glm_universal.corpus.checks.tier_report` fails if they stop being.*")

_DRAFT_VERDICT = "Not yet measured: this is a draft pre-registration written at intake."


def _item_listing(item: Path, limit: int = 40) -> List[str]:
    if not item.exists():
        return ["(not in this checkout)"]
    if item.is_file():
        return [item.name]
    files = sorted(str(p.relative_to(item)) for p in item.rglob("*")
                   if p.is_file() and "__pycache__" not in p.parts)
    return files[:limit] + ([f"... and {len(files) - limit} more"] if len(files) > limit else [])


def _study_markdown(rec: Mapping[str, Any], sid: str, layout: Layout, day: Optional[datetime.date]) -> str:
    rid = rec["id"]
    path = rec.get("path", "")
    offers = str(rec.get("offers") or "TO WRITE: what the item claims or offers.").strip()
    kind = rec.get("kind") or "not yet triaged"
    item = item_location(path, layout) if path else None
    tests = as_list(rec.get("tests"))
    lean = as_list(rec.get("lean"))
    obligations: List[str] = []
    for w in as_list(rec.get("wheels")):
        if isinstance(w, Mapping):
            for ob in as_list(w.get("lean_obligations")):
                obligations.append(f"{w.get('name', 'wheel')}: {ob}")
    for ob in as_list(rec.get("lean_obligations")):
        obligations.append(str(ob))
    parts = [p for p in as_list(rec.get("parts")) if isinstance(p, Mapping)]
    title = rid.replace("_", " ")
    L: List[str] = []
    L.append(f"# {title} — intake study (draft)")
    L.append("")
    L.append("## Tier 0 — the coarse read")
    L.append("")
    L.append(f"**Question.** Does the supplied item `{rid}` help the GLM as it offers, "
             f"once its tests pass, its finite claims are proved in Lean and its help is measured?")
    L.append("")
    L.append(f"**Verdict.** {_DRAFT_VERDICT}")
    L.append("")
    L.append("**Deciding figure.** None yet: no mark has been taken.")
    L.append("")
    L.append(f"**Recomputed by.** {_NO_FUNCTION}")
    L.append("")
    L.append(_TIER0_FOOTER)
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"*Created {today(day)} by `python3 -m glm_universal.intake scaffold {rid}` "
             "(directive D22). Every passage still marked as to be written is filled in, "
             "and the marks of §3 fixed, before any code of the round exists; the intake's "
             "measured gate refuses the study while any is left.*")
    L.append("")
    L.append("## 0. What this document is")
    L.append("")
    L.append(f"A **pre-registration** for the intake of one supplied item. {_DRAFT_VERDICT} "
             "No mark has been taken, and no module of the round exists.")
    L.append("")
    L.append(f"The item is [`source_material/{path}`](../source_material/{path}) "
             f"(kind: {kind}); its record is `{rid}` in "
             "[`source_material/INTAKE.yaml`](../source_material/INTAKE.yaml), "
             f"where it stands at *{STAGE_NAMES.get(rec.get('stage', 'received'), rec.get('stage'))}*.")
    L.append("")
    L.append("## 1. What the item offers, and what is taken from it")
    L.append("")
    L.append(offers)
    L.append("")
    if parts:
        L.append("Parts recorded at intake:")
        L.append("")
        for p in parts:
            where = ", ".join(as_list(p.get("studies")) + as_list(p.get("absorbed_into")))
            L.append(f"* {p.get('part')} — {p.get('status')}" + (f" ({where})" if where else ""))
        L.append("")
    L.append("TO WRITE: which parts this round takes, which it leaves, and why.")
    L.append("")
    L.append("## 2. The questions")
    L.append("")
    L.append("* **Q1.** Do the item's own tests pass where it stands"
             + (f" ({', '.join(f'`{t}`' for t in tests)})" if tests else "") + "?")
    L.append("* **Q2.** Are its finite and arithmetical claims proved in Lean (§5)?")
    L.append("* **Q3.** Does taking it into the GLM help, on a figure measured against the "
             "GLM without it?")
    L.append("* TO WRITE: the item's own questions.")
    L.append("")
    L.append("## 3. The marks, declared before the code")
    L.append("")
    L.append("| Mark | What is measured | Met when |")
    L.append("|---|---|---|")
    L.append("| I1 | the item's named tests | every named test passes (`intake advance "
             f"{rid} tested`) |")
    L.append("| I2 | the Lean obligations of §5 | every file is in the build, imported by "
             "`AxiomAuditAll.lean`, and the build record of `scripts/rebuild_lean.sh` "
             "(a passing `lake build`) matches it and every file it imports |")
    L.append("| I3 | the help it gives | TO WRITE: the figure, its control and the bar, fixed now |")
    L.append("| I4 | no regression | the package's tests pass after absorption |")
    L.append("")
    L.append("## 4. Controls")
    L.append("")
    L.append("TO WRITE: the GLM without the item, on the same frozen inputs; a shuffled or "
             "ablated variant of the item where one makes sense.")
    L.append("")
    L.append("## 5. Lean obligations")
    L.append("")
    if lean or obligations:
        for n in lean:
            state, module = gates.lean_state(n, layout)
            L.append(f"* `{module}` — {state}")
        for ob in obligations:
            L.append(f"* {ob}")
    else:
        L.append("TO WRITE: the finite claims a Lean file must prove before absorption.")
    L.append("")
    L.append("## 6. What this round does not do")
    L.append("")
    L.append("TO WRITE.")
    L.append("")
    L.append("## 7. Files")
    L.append("")
    L.append(f"* The item, `source_material/{path}`:")
    for f in _item_listing(item) if item is not None else []:
        L.append(f"  * `{f}`")
    L.append("* The intake record: `source_material/INTAKE.yaml`, id "
             f"`{rid}`.")
    L.append("")
    L.append("## 8. The measurement")
    L.append("")
    L.append("Not yet taken.")
    L.append("")
    return "\n".join(L)


_NO_FUNCTION = "(hand-written argument; nothing to recompute)"


def manifest_text(md_path: Path, day: Optional[datetime.date] = None) -> str:
    """The ``.yaml`` manifest of a study ``.md``, in the shape
    ``python3 -m glm_universal.corpus.study_manifest --sync`` writes it (its
    derivation is used when it can be imported; a minimal manifest that the
    next ``--sync`` completes otherwise)."""
    stamp = today(day)
    try:
        from ..corpus import study_manifest as sm
        t = sm.tree()
        parsed = sm.parse_document(md_path, t)
        fields = dict(parsed.fields)
        own = fields.get("phase") or 0
        preds: List[str] = []
        related: List[str] = []
        for target in parsed.links:
            other = 0
            y = md_path.parent / f"{target}.yaml"
            if y.is_file():
                try:
                    other = int((sm._load_yaml(y.read_text(encoding="utf-8")) or {}).get("phase") or 0)
                except Exception:  # pragma: no cover - a malformed neighbour
                    other = 0
            (preds if own > 0 and 0 < other < own else related).append(target)
        fields["predecessors"] = sorted(preds)
        fields["related"] = sorted(related)
        fields["successors"] = []
        merged = sm.merged_manifest(fields, None)
        return sm._render(merged, stamp)
    except Exception:
        text = md_path.read_text(encoding="utf-8")

        def field(label: str) -> str:
            m = re.search(r"\*\*" + re.escape(label) + r"\*\*\s*(.+)", text)
            return m.group(1).strip() if m else ""

        title = next((m.group(1) for m in [re.search(r"^#\s+(.*\S)", text, re.M)] if m), md_path.stem)
        data = {
            "schema": "glm-study-manifest/v1", "id": md_path.stem, "title": title,
            "phase": 0, "status": "open", "question": field("Question."),
            "verdict": field("Verdict."), "deciding_figure": field("Deciding figure."),
            "recomputed_by": field("Recomputed by."),
            "file_refs": {"prose": md_path.name, "code": [], "lean": [], "test": [], "wheel": []},
        }
        import yaml  # PyYAML
        return ("# GLM study manifest (glm-study-manifest/v1)\n"
                f"# Created {stamp} by the intake scaffold; complete it with\n"
                "# `python3 -m glm_universal.corpus.study_manifest --sync`.\n\n"
                + yaml.safe_dump(data, sort_keys=True, allow_unicode=True, width=100))


def scaffold(item_id: str, layout: Optional[Layout] = None, *, study_id: Optional[str] = None,
             day: Optional[datetime.date] = None) -> Tuple[Path, Path]:
    """Draft ``studies/<ID>_STUDY.md`` and its ``.yaml`` for an item, name the
    study in the record, and move the record to ``study_drafted`` when every
    earlier gate holds.  Refuses to overwrite an existing study."""
    lay = layout or Layout.default()
    data = load(lay)
    rec = record_by_id(data, item_id)
    if rec.get("stage") in TERMINAL:
        raise LedgerError(f"{item_id} is {rec.get('stage')}; its intake is finished")
    sid = study_id or study_id_for(item_id)
    md = lay.studies / f"{sid}.md"
    yml = lay.studies / f"{sid}.yaml"
    for p in (md, yml):
        if p.exists():
            raise LedgerError(f"{p.relative_to(lay.root)} exists; the scaffold never overwrites")
    lay.studies.mkdir(parents=True, exist_ok=True)
    md.write_text(_study_markdown(rec, sid, lay, day), encoding="utf-8")
    yml.write_text(manifest_text(md, day), encoding="utf-8")
    studies = as_list(rec.get("studies"))
    if sid not in studies:
        rec["studies"] = studies + [sid]
    moved = ""
    if stage_index(rec.get("stage") or "received") < stage_index("study_drafted") \
            and not gates.evidence_problems(rec, lay, "study_drafted"):
        rec["stage"] = "study_drafted"
        moved = "; stage study drafted"
    rec["next_step"] = (f"fill in studies/{sid}.md (every TO WRITE) and fix its marks before "
                        "any code; then name the tests and `advance " + item_id + " tested`")
    _stamp(rec, f"scaffolded studies/{sid}.md + .yaml{moved}", day)
    save(data, lay, day)
    return md, yml


# ---------------------------------------------------------------------------
# Running the instruments
# ---------------------------------------------------------------------------

#: What an exit code means, by the kind of command that returned it.  The
#: ``detail`` of a test result is written from these words (and, for a package
#: test, the counts of the closing tally); nothing the command printed is
#: copied into the ledger -- run the test again to see its output.
_EXIT_MEANING: Dict[str, Dict[int, str]] = {
    "fallback": {0: "every collected test ran and passed (without pytest)",
                 1: "a test or a setup/teardown hook failed (without pytest)",
                 2: "the file did not import, or a test in it needs pytest (fixtures or "
                    "parameters); nothing was counted as passed",
                 5: "no test ran in the file: nothing was collected, or every test was skipped"},
    "pytest": {0: "every collected test passed (pytest)",
               1: "a test failed (pytest)",
               2: "pytest was interrupted",
               3: "pytest stopped on an internal error",
               4: "pytest was called wrongly",
               5: "pytest collected no test"},
    "call": {0: "the function returned and no check in its result reads False",
             1: "the function raised, or a check in its result reads False"},
    "script": {0: "the script ran to completion"},
    "lean_check": {0: "the static Lean check passed",
                   1: "the static Lean check reported problems "
                      "(python3 -m glm_universal.lean_check lists them)"},
}

_TALLY = re.compile(r"(\d+) passed, (\d+) failed(?: \(including (\d+) failing setup/teardown "
                    r"hook\(s\)\))?, (\d+) skipped of (\d+) collected")
_PYTEST_COUNT = re.compile(r"(\d+) (passed|failed|skipped|errors?)\b")


def command_kind(command: Sequence[str]) -> str:
    """``fallback``, ``pytest``, ``call``, ``lean_check`` or ``script``, read
    from the words after the interpreter (``-m <module>`` or ``-c``)."""
    words = list(command)[1:3]
    if words[:1] == ["-c"]:
        return "call"
    if words[:1] == ["-m"] and len(words) == 2:
        return {"glm_universal.intake.fallback_tests": "fallback", "pytest": "pytest",
                "glm_universal.lean_check": "lean_check"}.get(words[1], "script")
    return "script"


def _counts(kind: str, output: str) -> str:
    """The closing tally of a package test as new words built from its
    integers (``3 passed, 0 failed, 0 skipped of 3 collected``), or ''."""
    if kind == "fallback":
        found = _TALLY.findall(output)
        if not found:
            return ""
        passed, failed, hooks, skipped, total = found[-1]
        hook_words = f" ({hooks} of them setup/teardown hooks)" if hooks else ""
        return (f"{int(passed)} passed, {int(failed)} failed{hook_words}, "
                f"{int(skipped)} skipped of {int(total)} collected")
    if kind == "pytest":
        lines = [ln for ln in output.splitlines() if " in " in ln and _PYTEST_COUNT.search(ln)]
        if not lines:
            return ""
        return ", ".join(f"{int(n)} {word}" for n, word in _PYTEST_COUNT.findall(lines[-1]))
    return ""


def describe_exit(kind: str, returncode: int, output: str = "") -> Tuple[str, str]:
    """``(result, detail)`` for a finished command: ``pass`` on exit 0, else
    ``fail``; the detail is a sentence of this module's own (the exit code,
    what it means for this kind of command and, for a package test, the
    counts), never text the command printed."""
    result = "pass" if returncode == 0 else "fail"
    meaning = _EXIT_MEANING.get(kind, {}).get(returncode)
    if meaning is None:
        meaning = "the command ended without success" if returncode else "the command succeeded"
    counts = _counts(kind, output)
    word = "passed" if result == "pass" else "failed"
    return result, f"{word} (exit {returncode}): {meaning}" + (f"; {counts}" if counts else "")


def _subprocess_runner(ref: str, command: List[str], cwd: Path, env: Dict[str, str],
                       timeout: int) -> Tuple[str, str]:
    """Run a command and describe its outcome with :func:`describe_exit`."""
    try:
        p = subprocess.run(command, cwd=str(cwd), env=env, capture_output=True,
                           text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return "timeout", f"no result within {timeout} s"
    except OSError as exc:
        return "error", f"could not start ({type(exc).__name__})"
    return describe_exit(command_kind(command), p.returncode, p.stdout + "\n" + p.stderr)


def _pytest_available() -> bool:
    return importlib.util.find_spec("pytest") is not None


def _package_test_command(path: Path, layout: Layout) -> List[str]:
    """pytest where it is installed (its exit 5, nothing collected, is a
    failure like any other non-zero exit); otherwise the package's own
    fallback runner, :mod:`glm_universal.intake.fallback_tests`, which runs
    ``TestCase`` tests and plain test functions, refuses a test that needs a
    pytest fixture, and fails a file in which nothing ran (``python3 -m
    unittest`` would pass a file of plain test functions having run none)."""
    if _pytest_available():
        return [sys.executable, "-m", "pytest", "-q", str(path)]
    return [sys.executable, "-m", "glm_universal.intake.fallback_tests", str(path)]


def _env(extra: Sequence[Path]) -> Dict[str, str]:
    env = dict(os.environ)
    paths = [str(p) for p in extra] + [str(C.PACKAGE_ROOT.parent)]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("MPLBACKEND", "Agg")
    return env


def run_test(ref: str, rec: Mapping[str, Any], layout: Layout, *, timeout: int = 1800,
             runner: Optional[Runner] = None) -> Tuple[str, str]:
    """Run one named test and return ``(result, detail)``.

    ``tests/test_x.py`` runs with pytest from the repository root (where
    pytest is not installed, with :mod:`.fallback_tests`, which never passes
    a file in which no test ran).  ``item:<script> [args]`` runs ``python3 <script> args``
    in a scratch copy of the item, from the script's own folder.
    ``call:<module>.<function>`` calls a study's recompute function with no
    argument in a fresh interpreter; it passes when the call returns without
    raising and no top-level value of a returned mapping is ``False`` (a
    check that reads ``False`` fails the test)."""
    run = runner or _subprocess_runner
    ref = ref.strip()
    path = str(rec.get("path") or "")
    item = item_location(path, layout) if path else None
    if ref.startswith("call:"):
        dotted = ref[len("call:"):].strip()
        module, _, fn = dotted.rpartition(".")
        if not module:
            return "error", f"{dotted} is not module.function"
        code = (f"import sys\nimport {module} as _m\nr = _m.{fn}()\n"
                "bad = [str(k) for k, v in r.items() if v is False] if isinstance(r, dict) else []\n"
                "print('False at: ' + ', '.join(bad) if bad else 'returned; no check reads False')\n"
                "sys.exit(1 if bad else 0)\n")
        return run(ref, [sys.executable, "-c", code], layout.root, _env([]), timeout)
    if ref.startswith("item:"):
        if item is None or not item.exists():
            return "error", f"{path} is not in this checkout"
        words = ref[len("item:"):].split()
        rel, args = (words[0], words[1:]) if words else ("", [])
        with tempfile.TemporaryDirectory(prefix="glm-intake-") as tmp:
            scratch = Path(tmp) / item.name
            ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".lake")
            if item.is_dir():
                shutil.copytree(item, scratch, ignore=ignore)
                script = scratch / rel if rel not in ("", ".") else None
                root = scratch
            else:
                shutil.copy2(item, scratch)
                script = scratch if rel in ("", ".") else Path(tmp) / rel
                root = Path(tmp)
            if script is None or not script.exists():
                return "error", f"{ref}: no such script in the item"
            cwd = script.parent
            return run(ref, [sys.executable, str(script), *args], cwd,
                       _env([cwd, root] if cwd != root else [root]), timeout)
    if ref.startswith("staged:"):
        rel = ref[len("staged:"):].strip().split(" ", 1)[0]
        source = gates.staged_test_path(ref, rec, layout)
        if source is None or not source.is_file():
            return "error", f"{ref}: neither staged in the item nor in the repository"
        with tempfile.TemporaryDirectory(prefix="glm-intake-staged-") as tmp:
            top = staged_overlay(rec, layout, Path(tmp))
            target = top / rel
            if not target.is_file():
                return "error", f"{ref}: {rel} is not below the package"
            return run(ref, _package_test_command(target, layout), top,
                       _env([top / layout.package.parent.relative_to(layout.root)]), timeout)
    target = gates.test_path(ref, item, layout)
    if target is None or not target.is_file():
        return "error", f"{ref} does not exist"
    return run(ref, _package_test_command(target, layout), layout.root, _env([]), timeout)


def staged_overlay(rec: Mapping[str, Any], layout: Layout, tmp: Path) -> Path:
    """A scratch view of the repository with an item's staged files in place,
    for running tests against code that is not yet absorbed.  Below ``tmp``
    every top-level entry of the repository is a symbolic link, except the
    package: its folders are real, its ``.py`` files are copies (so a module
    that finds the repository from its own ``__file__`` -- ``constants``
    among them -- finds the scratch view) and every other file is a link to
    the repository's.  The staged files are then copied in at their paths.
    Nothing in the repository is written by building the view.  Returns
    ``tmp``."""
    staged = gates.staged_root(rec, layout)
    files = gates.staged_files(rec, layout)
    pkg_rel = layout.package.relative_to(layout.root)

    def link_all(real: Path, fake: Path, keep: Path) -> None:
        # Link every entry of ``real`` into ``fake`` except the one on the way
        # to the package, which is descended into.
        fake.mkdir(parents=True, exist_ok=True)
        for child in sorted(real.iterdir()):
            if child.name == "__pycache__":
                continue
            if child == keep or keep.is_relative_to(child):
                if child == keep:
                    copy_package(child, fake / child.name)
                else:
                    link_all(child, fake / child.name, keep)
            else:
                (fake / child.name).symlink_to(child)

    def copy_package(real: Path, fake: Path) -> None:
        fake.mkdir(parents=True, exist_ok=True)
        for child in sorted(real.iterdir()):
            if child.name == "__pycache__":
                continue
            if child.is_dir() and not child.is_symlink():
                copy_package(child, fake / child.name)
            elif child.suffix == ".py":
                shutil.copy2(child, fake / child.name)
            else:
                (fake / child.name).symlink_to(child)

    link_all(layout.root, tmp, layout.root / pkg_rel)
    for rel in files:
        dest = tmp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_symlink() or dest.exists():
            dest.unlink()
        shutil.copy2(staged / rel, dest)
    return tmp


def install_staged(rec: Mapping[str, Any], layout: Layout) -> Tuple[List[str], List[str]]:
    """Copy an item's staged files into the repository.  Returns ``(installed,
    problems)``; a file that would overwrite different bytes is not copied and
    is a problem.  :func:`uninstall` reverses a partial install."""
    staged = gates.staged_root(rec, layout)
    installed: List[str] = []
    problems: List[str] = []
    for rel in gates.staged_files(rec, layout):
        src, dest = staged / rel, layout.root / rel
        if dest.exists():
            if dest.read_bytes() != src.read_bytes():
                problems.append(f"[absorbed] staged {rel} would overwrite a different file")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        installed.append(rel)
    return installed, problems


def uninstall(installed: Sequence[str], layout: Layout) -> None:
    for rel in installed:
        (layout.root / rel).unlink(missing_ok=True)


def run_lean_check(layout: Layout, timeout: int = 900) -> Tuple[bool, str]:
    """``python3 -m glm_universal.lean_check`` (read-only: no ``--write-audit``)."""
    result, detail = _subprocess_runner(
        "lean_check", [sys.executable, "-m", "glm_universal.lean_check"], layout.root,
        _env([]), timeout)
    return result == "pass", detail


# ---------------------------------------------------------------------------
# advance
# ---------------------------------------------------------------------------

def _move_to_done(rec: Dict[str, Any], layout: Layout) -> None:
    path = str(rec.get("path") or "")
    name = path.split("/", 1)[1] if "/" in path else path
    src = item_location(path, layout)
    dest = layout.done / name
    if path.startswith("done/"):
        return
    if dest.exists():
        raise LedgerError(f"done/{name} already exists")
    if src.exists():
        layout.done.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
    elif not rec.get("local_only"):
        raise LedgerError(f"{path} does not exist")
    rec["path"] = f"done/{name}"


def _run_tests(rec: Dict[str, Any], layout: Layout, refs: Sequence[str], *,
               day: Optional[datetime.date], timeout: int,
               runner: Optional[Runner]) -> List[Dict[str, Any]]:
    """Run the named tests and append their results, each with the
    fingerprint of the code it ran against (taken before the run)."""
    fp = gates.test_fingerprint(rec, layout)
    results = as_list(rec.get("test_results"))
    ran: List[Dict[str, Any]] = []
    for ref in refs:
        result, detail = run_test(ref, rec, layout, timeout=timeout, runner=runner)
        entry = {"test": ref, "result": result, "detail": detail, "date": today(day),
                 "fingerprint": fp}
        results.append(entry)
        ran.append(entry)
    rec["test_results"] = results
    return ran


def _build_entry(rec: Mapping[str, Any], layout: Layout) -> str:
    """The ``lean_build`` entry: which build record verified the item."""
    from .. import lean_check
    ev = lean_check.load_build_evidence(layout.lean_evidence) or {}
    modules = [gates.lean_state(str(n), layout)[1] for n in as_list(rec.get("lean"))]
    closure = lean_check.import_closure(
        modules, lean_check.scan_tree(layout.lean_source, layout.lean_library))
    try:
        where = str(layout.lean_evidence.relative_to(layout.root))
    except ValueError:
        where = str(layout.lean_evidence)
    return (f"{ev.get('date', 'undated')} ({ev.get('timestamp', '')}): lake build passed with the "
            f"axiom audit; {len(modules)} named file(s) and {len(closure)} file(s) in their import "
            f"closure match {where} (log {ev.get('log') or 'not named'})")


def advance(item_id: str, stage: str, layout: Optional[Layout] = None, *,
            day: Optional[datetime.date] = None, run: bool = True, timeout: int = 1800,
            runner: Optional[Runner] = None,
            lean_checker: Optional[LeanChecker] = None) -> Dict[str, Any]:
    """Move an item on to ``stage`` if every stage it passes through has its
    evidence.  Returns ``{"ok", "from", "to", "ran", "problems"}``; the record
    changes only when ``ok`` (test results are recorded either way)."""
    lay = layout or Layout.default()
    data = load(lay)
    rec = record_by_id(data, item_id)
    target = stage_key(stage)
    if target == "closed":
        raise LedgerError("an item is closed with `close <id> --reason ... --evidence ...`")
    current = rec.get("stage") or "received"
    if current in TERMINAL:
        raise LedgerError(f"{item_id} is {current}; its intake is finished")
    if stage_index(target) <= stage_index(current):
        raise LedgerError(f"{item_id} is already at {STAGE_NAMES[current]}")
    through = STAGES[stage_index(current) + 1: stage_index(target) + 1]
    report: Dict[str, Any] = {"id": item_id, "from": current, "to": target, "ran": [],
                              "problems": [], "ok": False}
    tests = [str(x).strip() for x in as_list(rec.get("tests"))]
    if run and ("tested" in through or target == "absorbed"):
        # Passing tested runs every named test; absorption runs them all again
        # immediately before anything is installed.
        report["ran"] += _run_tests(rec, lay, tests, day=day, timeout=timeout, runner=runner)
    elif run and stage_index(target) > stage_index("tested"):
        # A later promotion runs again any test whose last result is not a
        # pass taken against the code as it now stands.
        stale = set(gates.stale_results(rec, lay))
        latest = gates.latest_results(rec)
        again = [t for t in tests
                 if t in stale or (latest.get(t) or {}).get("result") != "pass"]
        if again:
            report["ran"] += _run_tests(rec, lay, again, day=day, timeout=timeout,
                                        runner=runner)
    if run and "lean_written" in through:
        ok, detail = (lean_checker or run_lean_check)(lay, min(timeout, 900))
        report["ran"].append({"test": "lean_check", "result": "pass" if ok else "fail",
                              "detail": detail, "date": today(day)})
        if not ok:
            report["problems"].append(f"[lean_written] python3 -m glm_universal.lean_check: {detail}")
        else:
            rec["lean_check"] = f"{today(day)}: OK"
    # Promotion to Lean verified or beyond re-reads the build record every
    # time: an item measured or absorbed later must still be verified by the
    # build of the files as they now stand.
    fresh = stage_index(target) >= stage_index("lean_verified")
    installed: List[str] = []
    open_first = target == "absorbed" and any(
        isinstance(p, Mapping) and p.get("status") == "open" for p in as_list(rec.get("parts")))
    if (target == "absorbed" and not open_first
            and not gates.evidence_problems(rec, lay, "measured", fresh=True, current=True)):
        # Every gate up to measured holds with a current build record and
        # current test results: install the staged code, then hold the
        # absorbed gate against the installed package (undone if anything
        # fails).  The results were just found current against the code being
        # installed, so the post-install check does not ask again (installing
        # moves the staged files, not their bytes).
        installed, clashes = install_staged(rec, lay)
        report["problems"] += clashes
        if not clashes:
            staged_dir = gates.staged_root(rec, lay)
            parked = Path(tempfile.mkdtemp(prefix="glm-intake-parked-"))
            if staged_dir is not None and staged_dir.is_dir():
                shutil.move(str(staged_dir), str(parked / gates.STAGED_DIR))
            report["problems"] += gates.evidence_problems(rec, lay, target, fresh=fresh)
            if report["problems"] and (parked / gates.STAGED_DIR).is_dir():
                shutil.move(str(parked / gates.STAGED_DIR), str(staged_dir))
            shutil.rmtree(parked, ignore_errors=True)
        if report["problems"]:
            uninstall(installed, lay)
            installed = []
    else:
        report["problems"] += gates.evidence_problems(rec, lay, target, fresh=fresh, current=True)
    if target == "absorbed":
        open_parts = [p for p in as_list(rec.get("parts"))
                      if isinstance(p, Mapping) and p.get("status") == "open"]
        if open_parts:
            report["problems"].append(f"[absorbed] {len(open_parts)} part(s) still open "
                                      "(close them, or take the staged parts alone with "
                                      "`absorb-staged <id>`)")
    if report["problems"]:
        if report["ran"]:
            _stamp(rec, f"gate for {STAGE_NAMES[target]} refused ({len(report['problems'])} "
                        "problem(s)); results recorded", day)
            save(data, lay, day)
        return report
    rec["stage"] = target
    if fresh:
        rec["lean_build"] = _build_entry(rec, lay)
    if installed:
        rec["installed"] = installed
    if target == "absorbed":
        _mark_parts_absorbed(rec, lay, day)
        _move_to_done(rec, lay)
        rec["next_step"] = ""
    _stamp(rec, f"advanced to {STAGE_NAMES[target]}", day)
    save(data, lay, day)
    report["ok"] = True
    return report


def _mark_parts_absorbed(rec: Dict[str, Any], layout: Layout,
                         day: Optional[datetime.date]) -> None:
    """``staged`` and ``provisional`` parts become ``absorbed`` (each note says
    how), and the item leaves the register of provisional families."""
    for part in as_list(rec.get("parts")):
        if not isinstance(part, dict) or part.get("status") not in ("staged", "provisional"):
            continue
        stamp = (f"installed from staged/ on {today(day)}" if part["status"] == "staged" else
                 f"provisional until {today(day)}, when the build record verified its Lean "
                 f"files and the item's tests passed again")
        part["status"] = "absorbed"
        note = str(part.get("note") or "").strip()
        part["note"] = f"{note}; {stamp}" if note else stamp
    register = load_provisional(layout)
    if rec.get("id") in register:
        del register[rec["id"]]
        save_provisional(register, layout)


def absorb_staged(item_id: str, layout: Optional[Layout] = None, *,
                  day: Optional[datetime.date] = None, run: bool = True, timeout: int = 1800,
                  runner: Optional[Runner] = None) -> Dict[str, Any]:
    """Absorb an item's ``staged`` and ``provisional`` parts while other parts
    stay open: every named test is run again against the code (unless ``run``
    is false, when the recorded results must already be current), and the
    item's whole evidence up to ``measured`` must hold with the current build
    record and current test results (the same gate as :func:`advance` to
    ``absorbed``, less the open parts); then the staged files are installed,
    every module a staged or provisional part names must exist and have a
    test, the parts become ``absorbed`` and the item leaves the register of
    provisional families.  The item stays in ``ToDo/`` at its stage.
    Anything wrong undoes the install.  Returns ``{"ok", "installed",
    "ran", "problems"}``."""
    lay = layout or Layout.default()
    data = load(lay)
    rec = record_by_id(data, item_id)
    report: Dict[str, Any] = {"id": item_id, "ok": False, "installed": [], "ran": [],
                              "problems": []}
    if rec.get("stage") in TERMINAL:
        raise LedgerError(f"{item_id} is {rec.get('stage')}; its intake is finished")
    parts = [p for p in as_list(rec.get("parts"))
             if isinstance(p, dict) and p.get("status") in ("staged", "provisional")]
    staged_parts = [p for p in parts if p.get("status") == "staged"]
    if not parts or (staged_parts and not gates.staged_files(rec, lay)):
        raise LedgerError(f"{item_id} has no provisional part and no staged part with staged files")
    if run:
        report["ran"] = _run_tests(rec, lay, [str(x).strip() for x in as_list(rec.get("tests"))],
                                   day=day, timeout=timeout, runner=runner)
    report["problems"] += gates.evidence_problems(rec, lay, "measured", fresh=True, current=True)
    if report["problems"]:
        if report["ran"]:
            _stamp(rec, f"staged parts refused ({len(report['problems'])} problem(s)); "
                        "results recorded", day)
            save(data, lay, day)
        return report
    installed, clashes = install_staged(rec, lay)
    report["problems"] += clashes
    staged_dir = gates.staged_root(rec, lay)
    parked = Path(tempfile.mkdtemp(prefix="glm-intake-parked-"))
    if not clashes:
        moved = staged_dir is not None and staged_dir.is_dir()
        if moved:
            shutil.move(str(staged_dir), str(parked / gates.STAGED_DIR))
        item = gates._item_path(rec, lay)
        tests = as_list(rec.get("tests"))
        for part in parts:
            for m in as_list(part.get("absorbed_into")):
                if gates.module_path(m, lay) is None:
                    report["problems"].append(f"[absorbed] {part['status']} part module {m} is "
                                              "not in the package")
                elif not gates._module_tested(m, tests, item, lay, rec):
                    report["problems"].append(f"[absorbed] module {m} has no test")
        if report["problems"] and moved:
            shutil.move(str(parked / gates.STAGED_DIR), str(staged_dir))
    shutil.rmtree(parked, ignore_errors=True)
    if report["problems"]:
        uninstall(installed, lay)
        return report
    rec["installed"] = as_list(rec.get("installed")) + installed
    rec["lean_build"] = _build_entry(rec, lay)
    _mark_parts_absorbed(rec, lay, day)
    _stamp(rec, f"staged and provisional parts absorbed ({len(parts)} part(s), "
                f"{len(installed)} file(s) installed)", day)
    save(data, lay, day)
    report.update(ok=True, installed=installed)
    return report


def provisional(item_id: str, decision: str, layout: Optional[Layout] = None, *,
                wheels: Sequence[str] = (), day: Optional[datetime.date] = None,
                run: bool = True, timeout: int = 1800,
                runner: Optional[Runner] = None) -> Dict[str, Any]:
    """Install an item's staged code ahead of the build record, by the
    owner's decision (``decision``, the owner's words; required).

    The item must stand at ``lean_written`` or beyond (not absorbed or
    closed) with staged parts that have staged files, and must not already be
    in the register of provisional families.  Every named test is run again
    (unless ``run`` is false, when the recorded results must already be
    current) and the item's evidence up to its stage must hold with current
    results; then the staged files are installed, every module a
    staged part names must exist in the package and have a test, the parts
    become ``provisional``, and the item is entered in the register with the
    decision, its date, the item's Lean files, the parts' modules, its first
    study and ``wheels`` (the wheel ids an answer may name).  Anything wrong
    undoes the install.  The item stays in ``ToDo/`` at its stage; absorption
    on a verifying build record ends the provisional status.  Returns
    ``{"ok", "installed", "ran", "problems"}``."""
    lay = layout or Layout.default()
    words = " ".join(str(decision or "").split())
    if not words:
        raise LedgerError("a provisional install needs the owner's decision, in the owner's "
                          "words (--decision \"...\")")
    data = load(lay)
    rec = record_by_id(data, item_id)
    stage = rec.get("stage") or "received"
    if stage in TERMINAL:
        raise LedgerError(f"{item_id} is {stage}; its intake is finished")
    if stage_index(stage) < stage_index("lean_written"):
        raise LedgerError(f"{item_id} is at {STAGE_NAMES[stage]}; code is installed "
                          "provisionally only at Lean written or beyond")
    register = load_provisional(lay)
    if item_id in register:
        raise LedgerError(f"{item_id} is already installed provisionally")
    parts = [p for p in as_list(rec.get("parts"))
             if isinstance(p, dict) and p.get("status") == "staged"]
    if not parts or not gates.staged_files(rec, lay):
        raise LedgerError(f"{item_id} has no staged part with staged files")
    report: Dict[str, Any] = {"id": item_id, "ok": False, "installed": [], "ran": [],
                              "problems": []}
    if run:
        report["ran"] = _run_tests(rec, lay, [str(x).strip() for x in as_list(rec.get("tests"))],
                                   day=day, timeout=timeout, runner=runner)
    report["problems"] += gates.evidence_problems(rec, lay, stage, current=True)
    if report["problems"]:
        if report["ran"]:
            _stamp(rec, f"provisional install refused ({len(report['problems'])} problem(s)); "
                        "results recorded", day)
            save(data, lay, day)
        return report
    installed, clashes = install_staged(rec, lay)
    report["problems"] += clashes
    staged_dir = gates.staged_root(rec, lay)
    parked = Path(tempfile.mkdtemp(prefix="glm-intake-parked-"))
    if not clashes and staged_dir is not None and staged_dir.is_dir():
        shutil.move(str(staged_dir), str(parked / gates.STAGED_DIR))
        item = gates._item_path(rec, lay)
        tests = as_list(rec.get("tests"))
        for part in parts:
            for m in as_list(part.get("absorbed_into")):
                if gates.module_path(m, lay) is None:
                    report["problems"].append(f"[provisional] staged part module {m} was not "
                                              "installed")
                elif not gates._module_tested(m, tests, item, lay, rec):
                    report["problems"].append(f"[provisional] module {m} has no test")
        if report["problems"]:
            shutil.move(str(parked / gates.STAGED_DIR), str(staged_dir))
    shutil.rmtree(parked, ignore_errors=True)
    if report["problems"]:
        uninstall(installed, lay)
        return report
    for part in parts:
        part["status"] = "provisional"
        note = str(part.get("note") or "").strip()
        stamp = (f"installed provisionally on {today(day)} by the owner's decision (register "
                 f"of provisional families); absorbed once the build record verifies the "
                 f"item's Lean files")
        part["note"] = f"{note}; {stamp}" if note else stamp
    rec["installed"] = as_list(rec.get("installed")) + installed
    studies = [str(x) for x in as_list(rec.get("studies"))]
    register[item_id] = {
        "date": today(day), "decision": words,
        "lean": sorted(str(n) for n in as_list(rec.get("lean"))),
        "modules": gates.provisional_modules(rec),
        "study": studies[0] if studies else "",
        "wheels": [str(w) for w in wheels],
    }
    save_provisional(register, lay)
    rec["next_step"] = (f"owner: run scripts/rebuild_lean.sh; when it passes, `python3 -m "
                        f"glm_universal.intake advance {item_id} measured` and then `advance "
                        f"{item_id} absorbed` (or `absorb-staged {item_id}` while other parts "
                        f"stay open) confirm the provisional parts")
    _stamp(rec, f"installed provisionally by the owner's decision ({len(installed)} file(s))",
           day)
    save(data, lay, day)
    report.update(ok=True, installed=installed)
    return report


def absorb_ahead(item_id: str, decision: str, standalone: Sequence[str], check: str,
                 layout: Optional[Layout] = None, *, wheels: Sequence[str] = (),
                 day: Optional[datetime.date] = None, run: bool = True, timeout: int = 1800,
                 runner: Optional[Runner] = None) -> Dict[str, Any]:
    """Absorb an item ahead of the build record, by the owner's decision
    (``decision``, the owner's words), on its measurements and a standalone
    Lean check (``standalone``: the item's Lean files checked on their own;
    ``check``: how).

    The item must stand at ``lean_written`` or beyond (not absorbed or
    closed).  Every named test is run again (unless ``run`` is false, when
    the recorded results must already be current); then every gate up to
    ``measured`` must hold with current results, the ``ahead_of_build``
    record standing in for the build record (:func:`gates.ahead_problems`),
    and the acceptance decision in place.  The staged files are installed
    and the ``absorbed`` gate must hold against the installed package
    (anything wrong undoes the install).  Then the record keeps
    ``ahead_of_build``, its staged and provisional parts become ``absorbed``,
    and its register entry takes the state ``absorbed ahead of the build``
    with the decision, its date, the item's Lean files, the modules absorbed
    now (each part's, or else the record's own) and ``wheels`` (default:
    those of a provisional entry it replaces).

    With no open part the whole item is absorbed: it moves to ``absorbed``
    and is filed in ``done/``.  With open parts (the pattern of
    :func:`absorb_staged`) only its staged and provisional parts are absorbed
    -- there must be at least one, and the ``absorbed`` gate is asked of
    their modules only -- and the item stays in ``ToDo/`` at its stage, its
    open parts still to be evaluated or closed.  Returns ``{"ok",
    "installed", "ran", "problems", "partial"}``."""
    lay = layout or Layout.default()
    words = " ".join(str(decision or "").split())
    how = " ".join(str(check or "").split())
    files = [str(n).strip() for n in standalone if str(n).strip()]
    if not words:
        raise LedgerError("an absorption ahead of the build needs the owner's decision, in the "
                          "owner's words (--decision \"...\")")
    if not files or not how:
        raise LedgerError("an absorption ahead of the build needs its standalone Lean check: "
                          "the Lean files checked (--standalone, repeatable) and how (--check)")
    data = load(lay)
    rec = record_by_id(data, item_id)
    stage = rec.get("stage") or "received"
    if stage in TERMINAL:
        raise LedgerError(f"{item_id} is {stage}; its intake is finished")
    if stage_index(stage) < stage_index("lean_written"):
        raise LedgerError(f"{item_id} is at {STAGE_NAMES[stage]}; an item is absorbed ahead of "
                          "the build only at Lean written or beyond")
    open_parts = [p for p in as_list(rec.get("parts"))
                  if isinstance(p, Mapping) and p.get("status") == "open"]
    ready_parts = [p for p in as_list(rec.get("parts"))
                   if isinstance(p, dict) and p.get("status") in ("staged", "provisional")]
    partial = bool(open_parts)
    if partial and not ready_parts:
        raise LedgerError(f"{item_id}: {len(open_parts)} part(s) still open ("
                          + ", ".join(str(p.get("part")) for p in open_parts)
                          + ") and no staged or provisional part to absorb ahead of the "
                          "build; stage their code or close them first")
    report: Dict[str, Any] = {"id": item_id, "ok": False, "installed": [], "ran": [],
                              "problems": [], "partial": partial}
    tests = [str(x).strip() for x in as_list(rec.get("tests"))]
    if run:
        report["ran"] = _run_tests(rec, lay, tests, day=day, timeout=timeout, runner=runner)
    ahead = {"decision": words, "date": today(day), "standalone": files, "check": how,
             "confirm": (f"scripts/rebuild_lean.sh, then `python3 -m glm_universal.intake "
                         f"confirm-build {item_id}`")}
    trial = dict(rec)
    trial[AHEAD_FIELD] = ahead
    report["problems"] += gates.evidence_problems(trial, lay, "measured", current=True)
    if report["problems"]:
        if report["ran"]:
            _stamp(rec, f"absorption ahead of the build refused ({len(report['problems'])} "
                        "problem(s)); results recorded", day)
            save(data, lay, day)
        return report
    installed, clashes = install_staged(rec, lay)
    report["problems"] += clashes
    staged_dir = gates.staged_root(rec, lay)
    parked = Path(tempfile.mkdtemp(prefix="glm-intake-parked-"))
    moved = False
    if not clashes:
        moved = staged_dir is not None and staged_dir.is_dir()
        if moved:
            shutil.move(str(staged_dir), str(parked / gates.STAGED_DIR))
        if partial:
            item = gates._item_path(rec, lay)
            tests = as_list(rec.get("tests"))
            for part in ready_parts:
                for m in as_list(part.get("absorbed_into")):
                    if gates.module_path(m, lay) is None:
                        report["problems"].append(f"[absorbed] {part['status']} part module "
                                                  f"{m} is not in the package")
                    elif not gates._module_tested(m, tests, item, lay, rec):
                        report["problems"].append(f"[absorbed] module {m} has no test")
        else:
            report["problems"] += [f"[absorbed] {p}" for p in
                                   gates.stage_problems(trial, "absorbed", lay)]
        if report["problems"] and moved:
            shutil.move(str(parked / gates.STAGED_DIR), str(staged_dir))
    shutil.rmtree(parked, ignore_errors=True)
    if report["problems"]:
        uninstall(installed, lay)
        return report
    modules = set()
    for part in as_list(rec.get("parts")):
        if not isinstance(part, dict) or part.get("status") not in ("staged", "provisional"):
            continue
        was = part["status"]
        part["status"] = "absorbed"
        modules.update(str(m) for m in as_list(part.get("absorbed_into")))
        stamp = (f"{'installed from staged/ and ' if was == 'staged' else ''}absorbed ahead of "
                 f"the build on {today(day)} by the owner's decision, on its measurements and a "
                 f"standalone Lean check; the owner's build has still to confirm it")
        note = str(part.get("note") or "").strip()
        part["note"] = f"{note}; {stamp}" if note else stamp
    if not modules:
        modules.update(str(m) for m in as_list(rec.get("absorbed_into")))
    register = load_provisional(lay)
    previous = register.get(item_id) or {}
    measured = str(rec.get("measured") or "").strip()
    studies = [str(x) for x in as_list(rec.get("studies"))]
    register[item_id] = {
        "state": AHEAD_STATE, "date": today(day), "decision": words,
        "lean": sorted(str(n) for n in as_list(rec.get("lean"))),
        "modules": sorted(modules), "standalone": files,
        "study": (gates._sid(re.split(r"[\s:§]", measured, 1)[0]) if measured
                  else studies[0] if studies else ""),
        "wheels": [str(w) for w in wheels] or list(previous.get("wheels") or []),
    }
    save_provisional(register, lay)
    rec[AHEAD_FIELD] = ahead
    if installed:
        rec["installed"] = as_list(rec.get("installed")) + installed
    confirm = (f"owner: run scripts/rebuild_lean.sh; when its build record verifies the Lean "
               f"files, `python3 -m glm_universal.intake confirm-build {item_id}`")
    if partial:
        rec["next_step"] = (confirm + "; the open part(s) ("
                            + ", ".join(str(p.get("part")) for p in open_parts)
                            + ") stay open: measure them or close them")
        _stamp(rec, f"staged and provisional parts absorbed ahead of the build by the owner's "
                    f"decision ({len(installed)} file(s) installed); "
                    f"{len(open_parts)} part(s) still open", day)
    else:
        rec["stage"] = "absorbed"
        _move_to_done(rec, lay)
        rec["next_step"] = confirm
        _stamp(rec, f"absorbed ahead of the build by the owner's decision ({len(installed)} "
                    f"file(s) installed); filed in done/", day)
    save(data, lay, day)
    report.update(ok=True, installed=installed)
    return report


def confirm_build(item_id: str, layout: Optional[Layout] = None, *,
                  day: Optional[datetime.date] = None) -> Dict[str, Any]:
    """The build record confirms an item absorbed ahead of the build: when
    ``scripts/logs/lean_build_evidence.json`` verifies the record's Lean files
    and every file they import (:func:`gates.build_problems`),
    ``ahead_of_build`` gives way to ``lean_build`` and the item leaves the
    register.  Returns ``{"ok", "problems"}``; nothing changes unless ``ok``."""
    lay = layout or Layout.default()
    data = load(lay)
    rec = record_by_id(data, item_id)
    ahead = rec.get(AHEAD_FIELD)
    if not ahead:
        raise LedgerError(f"{item_id} was not absorbed ahead of the build")
    lean = [str(n) for n in as_list(rec.get("lean"))]
    problems = gates.build_problems(lean, lay)
    if problems:
        return {"id": item_id, "ok": False, "problems": problems}
    since = ahead.get("date", "an unrecorded date") if isinstance(ahead, Mapping) else "?"
    rec["lean_build"] = (_build_entry(rec, lay) + f"; confirms the absorption ahead of the "
                         f"build of {since}")
    del rec[AHEAD_FIELD]
    for part in as_list(rec.get("parts")):
        if isinstance(part, dict) and "absorbed ahead of the build" in str(part.get("note") or ""):
            part["note"] = f"{part['note']}; confirmed by the build record on {today(day)}"
    register = load_provisional(lay)
    if register.get(item_id, {}).get("state") == AHEAD_STATE:
        del register[item_id]
        save_provisional(register, lay)
    open_parts = [p for p in as_list(rec.get("parts"))
                  if isinstance(p, Mapping) and p.get("status") == "open"]
    rec["next_step"] = ("the open part(s) (" + ", ".join(str(p.get("part")) for p in open_parts)
                        + ") stay open: measure them or close them") if open_parts else ""
    _stamp(rec, f"the build record confirmed the absorption ahead of the build of {since}", day)
    save(data, lay, day)
    return {"id": item_id, "ok": True, "problems": []}


# ---------------------------------------------------------------------------
# retest
# ---------------------------------------------------------------------------

def retest(item_id: str, layout: Optional[Layout] = None, *, only_stale: bool = False,
           day: Optional[datetime.date] = None, timeout: int = 1800,
           runner: Optional[Runner] = None) -> Dict[str, Any]:
    """Run an item's named tests (every one, or with ``only_stale`` those
    whose last result is not a pass taken against the code as it now stands)
    and record the results with their fingerprint.  The stage does not move.
    Returns ``{"id", "ran"}``."""
    lay = layout or Layout.default()
    data = load(lay)
    rec = record_by_id(data, item_id)
    if rec.get("stage") in TERMINAL:
        raise LedgerError(f"{item_id} is {rec.get('stage')}; its intake is finished")
    tests = [str(x).strip() for x in as_list(rec.get("tests"))]
    if not tests:
        raise LedgerError(f"{item_id} names no test")
    if only_stale:
        stale = set(gates.stale_results(rec, lay))
        latest = gates.latest_results(rec)
        tests = [t for t in tests
                 if t in stale or (latest.get(t) or {}).get("result") != "pass"]
    ran = _run_tests(rec, lay, tests, day=day, timeout=timeout, runner=runner) if tests else []
    if ran:
        passed = sum(1 for r in ran if r["result"] == "pass")
        _stamp(rec, f"tests run again: {passed} of {len(ran)} passed", day)
        save(data, lay, day)
    return {"id": item_id, "ran": ran}


# ---------------------------------------------------------------------------
# accept
# ---------------------------------------------------------------------------

def accept(item_id: str, criterion: str, result: str, layout: Optional[Layout] = None, *,
           study: Optional[str] = None, marks: Sequence[str] = (),
           day: Optional[datetime.date] = None) -> Dict[str, Any]:
    """Record ``acceptance`` on an item: the measured study (default: the one
    ``measured`` names, else the item's first study), the ``criterion`` it
    declared and the ``result`` it measured (each quoted from that study),
    the met ``marks`` that carry the help, and ``decision: accept``.  Sets
    ``measured`` to ``<study>: <result>`` when it is empty.  Refused (a
    :class:`LedgerError`, nothing written) unless the record would then pass
    the ``measured`` gate's own test (:func:`gates.measurement_problems`, as
    a promotion applies it): a draft or open study, a quotation the study
    does not contain or a mark it does not meet all refuse.  Returns the
    record."""
    lay = layout or Layout.default()
    data = load(lay)
    rec = record_by_id(data, item_id)
    if rec.get("stage") in TERMINAL:
        raise LedgerError(f"{item_id} is {rec.get('stage')}; its intake is finished")
    measured = str(rec.get("measured") or "").strip()
    cited = re.split(r"[\s:§]", measured, 1)[0] if measured else ""
    sid = study or cited or next((str(x) for x in as_list(rec.get("studies"))), "")
    if not sid:
        raise LedgerError(f"{item_id} names no study; pass --study")
    sid = gates._sid(sid)
    trial = dict(rec)
    if not measured:
        trial["measured"] = f"{sid}: {result.strip()}"
    elif gates._sid(cited) != sid:
        raise LedgerError(f"{item_id} records its measurement in {cited}, not {sid}")
    trial["acceptance"] = {
        "study": sid, "criterion": criterion.strip(), "result": result.strip(),
        "marks": [str(m).strip() for m in marks if str(m).strip()],
        "decision": gates.ACCEPT, "date": today(day),
    }
    problems = gates.measurement_problems(trial, lay, promotion=True)
    if problems:
        raise LedgerError("the acceptance would not pass the measured gate: " + "; ".join(problems))
    rec.clear()
    rec.update(trial)
    _stamp(rec, f"acceptance recorded against {sid}", day)
    save(data, lay, day)
    return rec


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------

def close(item_id: str, reason: str, evidence: Sequence[str], layout: Optional[Layout] = None, *,
          day: Optional[datetime.date] = None, close_open_parts: bool = False) -> Dict[str, Any]:
    """Finish an item without absorption: record the reason and the evidence
    (study ids or repository paths, each of which must exist), and file the
    item in ``done/``.  Open parts must be closed too (``close_open_parts``)."""
    lay = layout or Layout.default()
    data = load(lay)
    rec = record_by_id(data, item_id)
    if rec.get("stage") in TERMINAL:
        raise LedgerError(f"{item_id} is already {rec.get('stage')}")
    if not reason.strip():
        raise LedgerError("a closure needs a reason")
    ev = [e for e in evidence if e.strip()]
    if not ev:
        raise LedgerError("a closure needs evidence (a study id or a repository path)")
    trial = dict(rec, closed_reason=reason, evidence=ev, stage="closed")
    problems = gates.evidence_problems(trial, lay, "closed")
    if problems:
        raise LedgerError("refused: " + "; ".join(problems))
    parts = [p for p in as_list(rec.get("parts")) if isinstance(p, Mapping)]
    open_parts = [p for p in parts if p.get("status") == "open"]
    if open_parts and not close_open_parts:
        raise LedgerError(f"{len(open_parts)} part(s) are open: "
                          + ", ".join(str(p.get("part")) for p in open_parts)
                          + " (pass --close-open-parts to close them with this reason)")
    for p in open_parts:
        p["status"] = "closed"
        p["note"] = f"closed with the item, {today(day)}"
    rec["closed_reason"] = reason
    rec["evidence"] = ev
    rec["stage"] = "closed"
    rec["next_step"] = ""
    _move_to_done(rec, lay)
    _stamp(rec, "closed and filed in done/", day)
    save(data, lay, day)
    return rec

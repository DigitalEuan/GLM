"""``glm_universal.intake.gates`` -- the evidence each intake stage needs.

*Created 31 October 2026 (repository check; directive D22).*
*Last altered 31 October 2026: ``lean_written`` (static) split from
``lean_verified`` (the owner's build record, current for the named files and
their imports); staged code and ``staged`` parts; the study gate needs the
``.yaml`` manifest in step with the ``.md``; test results carry the
fingerprint of the code they ran against, and a promotion accepts only
current ones; ``measured`` needs a finished study and an ``acceptance``
decision against the study's own declared criterion; then ``provisional``
parts and the register of provisional families
(:func:`provisional_problems`).*
*Last altered 1 November 2026 (Phase 186): absorption ahead of the build --
``lean_verified`` is met, for a record that carries ``ahead_of_build``, by the
owner's decision and a standalone Lean check (:func:`ahead_problems`) until
the build record confirms it; the register's entries in the state
``absorbed ahead of the build`` are held to their records.*

A stage is reached only with its evidence, and the evidence accumulates: an
item at ``tested`` must also satisfy ``triaged`` and ``study_drafted``.  The
checks read files only; nothing is built or run here (running the named
tests and ``lean_check`` is :func:`glm_universal.intake.actions.advance`'s
job, and ``lake build`` is the owner's, through ``scripts/rebuild_lean.sh``).

=================  ==========================================================
stage              evidence that must exist
=================  ==========================================================
``received``       the item is where ``path`` says (or is ``local_only``)
``triaged``        a valid ``kind``, ``offers`` and ``next_step``
``study_drafted``  every named study is a pair: ``studies/<id>.md`` with a
                   tier-0 block and ``studies/<id>.yaml``, a manifest that
                   validates against ``glm-study-manifest/v1``, names the same
                   id and states the same question, verdict and deciding
                   figure as the ``.md`` (:func:`study_problems`)
``tested``         every named test exists, and its last recorded result in
                   ``test_results`` is ``pass`` (``staged:<path>`` names a test
                   run against the item's staged code, see below).  On a
                   promotion (``current``) the result must also carry the
                   fingerprint of the code as it now stands
                   (:func:`test_fingerprint`): a pass taken before the
                   package, the item or its staged files changed does not
                   count, and :func:`~glm_universal.intake.actions.advance`
                   runs such a test again
``lean_written``   every named Lean file is in the build tree and imported by
                   ``AxiomAuditAll.lean`` (held or missing files do not count);
                   the static check (``lean_check``) is a preliminary gate and
                   verifies nothing
``lean_verified``  promotion (``advance``) needs the current build record
                   ``scripts/logs/lean_build_evidence.json``: a passing build
                   with unchanged toolchain and Mathlib pins, each named file
                   imported by the audit, and each named file *and every file
                   it imports* byte for byte the file that was built
                   (:func:`glm_universal.lean_check.verification_problems`);
                   the record keeps which build that was in ``lean_build``.
                   :func:`check` re-reads the build record when it exists and
                   warns where a file changed after its verified build.  An
                   item absorbed ahead of the build by the owner's decision
                   carries ``ahead_of_build`` instead (:func:`ahead_problems`:
                   the decision, its date, how the Lean was checked, and the
                   Lean files checked on their own, each one of the record's
                   own and audited) until ``confirm-build``
``measured``       ``measured`` names a study that passes the study gate and
                   is finished: no draft text left (``TO WRITE``, the
                   scaffold's draft verdict or figure, outside code
                   quotes), a deciding figure
                   that is a measurement, and a manifest status of
                   ``closed`` (an ``open`` study is unanswered, a
                   ``negative`` one says the item does not help).  And the
                   record's ``acceptance`` decides it against the study's
                   declared criterion (:func:`measurement_problems`):
                   ``study`` (the measured study), ``criterion`` and
                   ``result`` (each quoted from that study), ``marks``
                   (required when the study declares marks: each must be
                   declared and met there, none missed) and ``decision``,
                   which must be ``accept``.  Every promotion requires it;
                   a ledger check accepts a record absorbed before 31
                   October 2026, when decisions began to be recorded, if it
                   says so in ``legacy_absorption`` (filed in ``done/`` at
                   ``absorbed`` only) and notes it
``absorbed``       every module in ``absorbed_into`` exists and has a test, and
                   nothing is left in the item's ``staged/`` folder
                   (absorption installs it into the package)
``closed``         a ``closed_reason`` and ``evidence`` that exists
=================  ==========================================================

**Staged code.**  An item whose code is prepared for the package but not yet
absorbed keeps it in ``<item>/staged/<path relative to the repository root>``
(below ``src/glm_universal/`` only).  Nothing in the package imports it; its
tests run in a scratch overlay of the package with the staged files in place
(``staged:<path>``), and ``advance <id> absorbed`` installs the files, after
every gate has passed with a current build record.  :func:`check` refuses a
staged file that would overwrite a different file already in the package.

**Provisional parts.**  By an owner's decision, code that has passed its
item's tests and stands at ``lean_written`` may be installed in the package
ahead of the build record: its parts are recorded ``provisional`` and the
item has an entry in the register of provisional families
(:attr:`~glm_universal.intake.ledger.Layout.provisional`,
``src/glm_universal/wheels/_data/provisional.json``), which the answers that
rest on that code read.  :func:`provisional_problems` holds the two together:
a provisional part needs its item in ``ToDo/`` at ``lean_written`` or beyond
(never absorbed or closed), its modules in the package with a test, and a
register entry with the owner's decision; the entry's modules must be exactly
those of the item's provisional parts and its Lean files the item's own; an
entry needs a record with a provisional part.  Absorption on a verifying build
record makes the parts ``absorbed`` and removes the entry.

**Absorbed ahead of the build.**  By the owner's decision of 1 November 2026
an item may be absorbed on its measurements and a standalone Lean check before
the build record exists (:func:`~glm_universal.intake.actions.absorb_ahead`):
its record carries ``ahead_of_build`` and stands at ``absorbed`` in ``done/``
(or, when parts of it are still open, stays in ``ToDo/`` at ``lean_written``
or beyond with its staged and provisional parts ``absorbed``), and its
register entry has the state ``absorbed ahead of the build`` (the
modules named there are the record's absorbed modules, its Lean files the
record's own).  :func:`check` notes every such item until ``confirm-build``
replaces ``ahead_of_build`` by ``lean_build``.

:func:`check` adds the ledger-wide rules: one record per filed item, nothing
loose under ``source_material/``, ``done/`` holds only absorbed or closed
items and ``ToDo/`` none, no ``open``, ``staged`` or ``provisional`` part in
``done/``, the register of provisional families in step with the ledger, and every Lean file a
record cites (in ``lean``, ``parts`` or ``wheels``) is audited, held in
``src/lean/awaiting_recovery/`` or recorded missing in
``studies/_lean_files_needed.md``.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .. import lean_check
from ..integrity import file_digest, sha256_hex
from .ledger import (
    AHEAD_FIELD, AHEAD_STATE, KINDS, PART_STATUSES, STAGES, UNFINISHED_PART_STATUSES, Layout,
    LedgerError, as_list, folder_items, item_location, load_provisional, loose_items,
    stage_index,
)

__all__ = [
    "lean_state", "test_path", "module_path", "study_exists", "stage_problems",
    "evidence_problems", "check", "deciding_figure", "latest_results",
    "build_problems", "STAGED_DIR", "staged_root", "staged_files", "staged_test_path",
    "staged_module_path", "study_problems", "measurement_problems", "test_fingerprint",
    "stale_results", "DRAFT_MARKERS", "LEGACY_FIELD", "is_legacy_absorption",
    "provisional_modules", "provisional_problems", "ahead_problems", "absorbed_modules",
]

_GLM_PREFIX = "RequestProject.GLM."
TERMINAL_STAGES = ("absorbed", "closed")


# ---------------------------------------------------------------------------
# Locating evidence
# ---------------------------------------------------------------------------

def study_exists(study_id: str, layout: Layout) -> bool:
    sid = study_id.strip()
    if sid.endswith(".md"):
        sid = sid[:-3]
    return (layout.studies / f"{sid}.md").is_file()


def deciding_figure(study_id: str, layout: Layout) -> str:
    """The Tier-0 ``**Deciding figure.**`` text of a study, or ``""``."""
    sid = study_id.strip()[:-3] if study_id.strip().endswith(".md") else study_id.strip()
    p = layout.studies / f"{sid}.md"
    if not p.is_file():
        return ""
    m = re.search(r"\*\*Deciding figure\.\*\*\s*(.+)", p.read_text(encoding="utf-8"))
    return m.group(1).strip() if m else ""


def _sid(study_id: str) -> str:
    sid = study_id.strip()
    for suffix in (".md", ".yaml"):
        if sid.endswith(suffix):
            sid = sid[: -len(suffix)]
    return sid


def _norm(text: str) -> str:
    """Text compared as words: figure markers, links, emphasis and code marks
    removed, case and runs of white space folded."""
    s = re.sub(r"<!--/?figure[^>]*-->", "", str(text))
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"[*_`]+", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def _tier0(sid: str, layout: Layout):
    """The tier-0 block of ``studies/<sid>.md`` (``None`` when it has none)."""
    from ..corpus import inventory as inv
    p = layout.studies / f"{sid}.md"
    sections = inv._split_sections(f"studies/{p.name}", p.read_text(encoding="utf-8"))
    return inv._parse_tier0(sections)[0]


def _manifest(sid: str, layout: Layout) -> Tuple[Optional[Dict[str, Any]], str]:
    """``(manifest, why_not)`` of ``studies/<sid>.yaml``."""
    p = layout.studies / f"{sid}.yaml"
    if not p.is_file():
        return None, f"studies/{sid}.yaml (its manifest) does not exist"
    try:
        import yaml  # PyYAML
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as exc:  # a manifest that does not parse
        return None, f"studies/{sid}.yaml does not parse: {exc}"
    if not isinstance(data, dict):
        return None, f"studies/{sid}.yaml is not a mapping"
    return data, ""


def study_problems(study_id: str, layout: Layout) -> List[str]:
    """Why a named study is not a usable pair (``[]`` when it is): the
    ``.md`` with its tier-0 block, and the ``.yaml`` manifest the GLM reads,
    valid against ``glm-study-manifest/v1``, with the same id, and stating
    the same question, verdict and deciding figure as the ``.md``.  (The
    whole derived manifest is held to its ``.md`` by
    ``python3 -m glm_universal.corpus.study_manifest --check``; this gate
    holds the tier-0 claims, which are what the intake reads.)"""
    sid = _sid(study_id)
    if not (layout.studies / f"{sid}.md").is_file():
        return [f"study {sid}: studies/{sid}.md does not exist"]
    out: List[str] = []
    tier0 = _tier0(sid, layout)
    if tier0 is None:
        out.append(f"study {sid}: studies/{sid}.md has no tier-0 block")
    data, why = _manifest(sid, layout)
    if data is None:
        out.append(f"study {sid}: {why} (write it with `python3 -m "
                   f"glm_universal.corpus.study_manifest --sync`)")
        return out
    from ..corpus import yaml as yml
    errors = yml.validate(data)
    if errors:
        out.append(f"study {sid}: studies/{sid}.yaml does not validate: "
                   + "; ".join(errors[:3]) + (" ..." if len(errors) > 3 else ""))
    if data.get("id") != sid:
        out.append(f"study {sid}: studies/{sid}.yaml names id {data.get('id')!r}")
    if tier0 is not None:
        for key, value in (("question", tier0.question), ("verdict", tier0.verdict),
                           ("deciding_figure", tier0.figure)):
            if _norm(data.get(key) or "") != _norm(value):
                out.append(f"study {sid}: the manifest's {key} is not the .md's (run "
                           f"`python3 -m glm_universal.corpus.study_manifest --sync`)")
    return out


#: Text a scaffolded draft study carries until its round writes it.
DRAFT_MARKERS: Tuple[str, ...] = (
    "TO WRITE",
    "None yet: no mark has been taken",
    "Not yet measured: this is a draft pre-registration",
)

_PLACEHOLDER = re.compile(r"^\s*(?:none yet|not yet|to write|tbd|pending|n/?a)\b", re.I)

#: The decision that lets a measured item be absorbed.
ACCEPT = "accept"


#: The field that marks a record absorbed by a round before the intake
#: recorded acceptance decisions (31 October 2026).
LEGACY_FIELD = "legacy_absorption"


def is_legacy_absorption(rec: Mapping[str, Any]) -> bool:
    """``rec`` was absorbed before acceptance decisions were recorded: it is
    filed in ``done/`` at ``absorbed``, has no ``acceptance`` and says why in
    ``legacy_absorption``.  A ledger check accepts the study verdict cited in
    ``measured`` for such a record and notes it; no promotion ever does."""
    return (bool(str(rec.get(LEGACY_FIELD) or "").strip())
            and rec.get("stage") == "absorbed"
            and str(rec.get("path") or "").startswith("done/")
            and not isinstance(rec.get("acceptance"), Mapping))


def measurement_problems(rec: Mapping[str, Any], layout: Layout,
                         promotion: bool = False) -> List[str]:
    """Why ``rec`` is not measured and accepted (``[]`` when it is).

    The measurement must be finished -- the study named first in
    ``measured`` passes the study gate, carries no draft text, has a deciding
    figure that is a measurement and a manifest status of ``closed`` -- and
    the record's ``acceptance`` must decide it against the study's own
    declared criterion: ``criterion`` and ``result`` quoted from the study,
    the study's marks that carry the help named in ``marks`` and each met
    there (required when the study declares marks), and ``decision:
    accept``.  A draft, an absent result, a failed criterion or any other
    decision refuses.

    ``promotion`` is set by every promotion (``advance``, ``absorb-staged``):
    the ``acceptance`` block is then always required.  A ledger check
    (``promotion`` unset) accepts a record absorbed before acceptance
    decisions were recorded (:func:`is_legacy_absorption`) on the strength of
    its finished, closed study, and :func:`check` notes it."""
    m = str(rec.get("measured") or "").strip()
    if not m:
        return ["no measurement recorded"]
    sid = _sid(re.split(r"[\s:§]", m, 1)[0])
    problems = study_problems(sid, layout)
    if problems:
        return [f"measured cites {sid}: {p}" for p in problems]
    out: List[str] = []
    text = (layout.studies / f"{sid}.md").read_text(encoding="utf-8")
    # A marker quoted as code (a study that writes about the scaffold) is not
    # draft text; the scaffold writes its markers as plain prose.
    prose = re.sub(r"`[^`\n]*`", "", text)
    drafts = [d for d in DRAFT_MARKERS if d in prose]
    if drafts:
        out.append(f"{sid} is still a draft: it carries {drafts[0]!r}")
    figure = _tier0(sid, layout).figure
    if not _norm(figure) or _PLACEHOLDER.match(_norm(figure)):
        out.append(f"{sid} has no measured deciding figure ({figure!r})")
    data, _ = _manifest(sid, layout)
    status = (data or {}).get("status")
    if status == "open":
        out.append(f"{sid} is open: its verdict is not yet an answer")
    elif status == "negative":
        out.append(f"{sid} is negative: its verdict says the item does not help as "
                   "offered (close the item rather than absorb it)")
    elif status != "closed":
        out.append(f"{sid} has status {status!r}, not closed")
    acc = rec.get("acceptance")
    if not isinstance(acc, Mapping) and not promotion and is_legacy_absorption(rec):
        return out
    if not isinstance(acc, Mapping):
        out.append("no acceptance decision recorded (acceptance: study, criterion, result, "
                   "marks, decision -- the measurement decided against the study's declared "
                   "criterion)")
        return out
    if _sid(str(acc.get("study") or "")) != sid:
        out.append(f"acceptance names study {acc.get('study')!r}, not the measured {sid}")
    body = _norm(text)
    for key, what in (("criterion", "the criterion the study declared"),
                      ("result", "the measured result")):
        value = str(acc.get(key) or "").strip()
        if not value or _PLACEHOLDER.match(value):
            out.append(f"acceptance has no {key} ({what})")
        elif _norm(value) not in body:
            out.append(f"acceptance {key} is not stated in studies/{sid}.md (quote {what} "
                       "from the study)")
    marks = [str(x).strip() for x in as_list(acc.get("marks"))]
    declared = [str(x) for x in as_list(((data or {}).get("marks") or {}).get("declared"))]
    met = {str(x) for x in as_list(((data or {}).get("marks") or {}).get("met"))}
    missed = {str(x) for x in as_list(((data or {}).get("marks") or {}).get("missed"))}
    if declared and not marks:
        out.append(f"{sid} declares marks ({', '.join(declared)}); acceptance.marks must name "
                   "those that carry the help")
    for mk in marks:
        if mk not in declared:
            out.append(f"acceptance mark {mk} is not declared in {sid}")
        elif mk in missed or mk not in met:
            out.append(f"acceptance mark {mk} is not met in {sid}: the criterion failed")
    decision = str(acc.get("decision") or "").strip().lower()
    if decision != ACCEPT:
        out.append(f"acceptance decision is {decision or 'missing'!r}: absorption needs "
                   f"{ACCEPT!r} (an item that does not meet its criterion is closed)")
    return out


def _doc_exists(ref: str, layout: Layout) -> bool:
    """Evidence for a closure: a study id, or a repository-relative path,
    optionally followed by `` §...``."""
    target = ref.split(" §", 1)[0].strip()
    if study_exists(target, layout):
        return True
    return (layout.root / target).exists()


def test_path(ref: str, item: Optional[Path], layout: Layout) -> Optional[Path]:
    """Where a named test lives: ``tests/test_x.py`` below the package, or
    ``item:<path>`` below the item (``item:`` alone is a single-file item)."""
    ref = ref.strip()
    if ref.startswith("item:"):
        if item is None:
            return None
        rel = ref[len("item:"):].strip().split(" ", 1)[0]
        if rel in ("", "."):
            return item
        base = item if item.is_dir() else item.parent
        return base / rel
    return layout.package / ref.split(" ", 1)[0]


#: The folder inside an item that holds code prepared for the package but not
#: yet absorbed: ``<item>/staged/<path relative to the repository root>``.
STAGED_DIR = "staged"


def staged_root(rec: Mapping[str, Any], layout: Layout) -> Optional[Path]:
    """``<item>/staged`` of a folder item, or ``None``."""
    path = rec.get("path")
    item = item_location(path, layout) if isinstance(path, str) and path else None
    if item is None or not item.is_dir():
        return None
    return item / STAGED_DIR


def staged_files(rec: Mapping[str, Any], layout: Layout) -> List[str]:
    """The repository-relative paths of the files an item has staged (each is
    installed at that path when the item is absorbed)."""
    root = staged_root(rec, layout)
    if root is None or not root.is_dir():
        return []
    return sorted(str(p.relative_to(root)) for p in root.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")


def staged_test_path(ref: str, rec: Mapping[str, Any], layout: Layout) -> Optional[Path]:
    """Where a ``staged:<repository path>`` test lives: the item's staged copy
    when it has one, else the file in the repository (a live test run against
    the staged code)."""
    rel = ref[len("staged:"):].strip().split(" ", 1)[0]
    root = staged_root(rec, layout)
    if root is not None and (root / rel).is_file():
        return root / rel
    return layout.root / rel


def staged_module_path(name: str, rec: Mapping[str, Any], layout: Layout) -> Optional[Path]:
    """The staged copy of a module an item will install (``None`` when the
    item stages no such file)."""
    root = staged_root(rec, layout)
    if root is None:
        return None
    pkg = layout.package.relative_to(layout.root)
    n = name.strip()
    if n.startswith("glm_universal."):
        n = n[len("glm_universal."):].replace(".", "/")
    if n.endswith(".py"):
        n = n[:-3]
    base = root / pkg / n
    for cand in (base.with_suffix(".py"), base / "__init__.py"):
        if cand.is_file():
            return cand
    return None


#: Folders of the package that hold generated data, not code: a test result
#: is not tied to them (each cache is held to its own inputs by its digest).
_GENERATED_DIRS = ("_data", "_derived", "_knowledge_cache", "__pycache__")


def test_fingerprint(rec: Mapping[str, Any], layout: Layout) -> str:
    """The code a named test of ``rec`` runs against, as one digest: every
    file of the package (generated-data folders and bytecode left out) with
    the item's staged files in place at the paths they install to, and every
    file of the item outside ``staged/``.  A result recorded with another
    fingerprint was taken against other code."""
    files: Dict[str, Path] = {}
    if layout.package.is_dir():
        for p in layout.package.rglob("*"):
            rel = p.relative_to(layout.package)
            if (p.is_file() and p.suffix != ".pyc"
                    and not any(part in _GENERATED_DIRS for part in rel.parts)):
                files[str(p.relative_to(layout.root))] = p
    root = staged_root(rec, layout)
    for rel in staged_files(rec, layout):
        files[rel] = root / rel
    item = _item_path(rec, layout)
    if item is not None and item.is_file():
        files["<item>/" + item.name] = item
    elif item is not None and item.is_dir():
        for p in item.rglob("*"):
            rel = p.relative_to(item)
            if (p.is_file() and p.suffix != ".pyc" and "__pycache__" not in rel.parts
                    and rel.parts[0] != STAGED_DIR):
                files["<item>/" + str(rel)] = p
    joined = b"".join(label.encode("utf-8") + b"\0" + file_digest(files[label]).encode("ascii")
                      + b"\0" for label in sorted(files))
    return "sha256:" + sha256_hex(joined)


def stale_results(rec: Mapping[str, Any], layout: Layout,
                  fingerprint: Optional[str] = None) -> List[str]:
    """The named tests whose last recorded result is missing or was taken
    against other code than the code as it now stands."""
    fp = fingerprint or test_fingerprint(rec, layout)
    latest = latest_results(rec)
    return [t for t in (str(x).strip() for x in as_list(rec.get("tests")))
            if latest.get(t) is None or latest[t].get("fingerprint") != fp]


def module_path(name: str, layout: Layout) -> Optional[Path]:
    """The file of a module named ``reasoning/pcgs``, ``reasoning/pcgs.py`` or
    ``glm_universal.reasoning.pcgs`` (a package resolves to ``__init__.py``)."""
    n = name.strip()
    if n.startswith("glm_universal."):
        n = n[len("glm_universal."):].replace(".", "/")
    if n.endswith(".py"):
        n = n[:-3]
    base = layout.package / n
    for cand in (base.with_suffix(".py"), base / "__init__.py"):
        if cand.is_file():
            return cand
    return None


def _module_tested(name: str, tests: List[str], item: Optional[Path], layout: Layout,
                   rec: Optional[Mapping[str, Any]] = None) -> bool:
    """A module counts as tested when a named package test (or a ``staged:``
    test, staged or installed) mentions it, or a ``tests/test_<stem>.py``
    exists."""
    stem = Path(name.strip().replace(".", "/")).name
    if stem.endswith(".py"):
        stem = stem[:-3]
    if stem == "__init__":
        stem = Path(name).parent.name
    if (layout.package / "tests" / f"test_{stem}.py").is_file():
        return True
    for ref in tests:
        if ref.startswith(("item:", "call:")):
            continue
        p = (staged_test_path(ref, rec or {}, layout) if ref.startswith("staged:")
             else test_path(ref, item, layout))
        if p is not None and p.is_file() and re.search(rf"\b{re.escape(stem)}\b",
                                                       p.read_text(encoding="utf-8")):
            return True
    return False


def _lean_rel(name: str) -> str:
    n = name.strip()
    if n.startswith(_GLM_PREFIX):
        n = n[len(_GLM_PREFIX):].replace(".", "/") + ".lean"
    elif not n.endswith(".lean"):
        n = n.replace(".", "/") + ".lean"
    return n


def _audit_imports(layout: Layout) -> set:
    if not layout.lean_audit.is_file():
        return set()
    text = layout.lean_audit.read_text(encoding="utf-8")
    return set(re.findall(r"^\s*(?:public\s+)?import\s+(\S+)", text, re.M))


def lean_state(name: str, layout: Layout) -> Tuple[str, str]:
    """``(state, module)`` of a Lean file a record cites.  ``state`` is
    ``audited`` (in the tree and imported by the audit), ``unaudited`` (in the
    tree, not imported), ``held`` (in ``awaiting_recovery``), ``missing``
    (absent, recorded in ``_lean_files_needed.md``), ``absent`` (absent and
    unrecorded) or ``ambiguous`` (a bare name with several matches)."""
    rel = _lean_rel(name)
    tree = layout.lean_glm / rel
    held = layout.lean_holding / layout.lean_library / "GLM" / rel
    if not tree.is_file() and "/" not in rel:
        matches = sorted(layout.lean_glm.rglob(rel)) if layout.lean_glm.is_dir() else []
        if len(matches) > 1:
            return "ambiguous", ", ".join(str(m.relative_to(layout.lean_glm)) for m in matches)
        if len(matches) == 1:
            tree = matches[0]
            rel = str(tree.relative_to(layout.lean_glm))
    module = _GLM_PREFIX + rel[:-5].replace("/", ".")
    if tree.is_file():
        return ("audited" if module in _audit_imports(layout) else "unaudited"), module
    if held.is_file():
        return "held", module
    registry = layout.lean_needed.read_text(encoding="utf-8") if layout.lean_needed.is_file() else ""
    if f"`{Path(rel).name}`" in registry or f"`{rel}`" in registry:
        return "missing", module
    return "absent", module


def build_problems(names: List[str], layout: Layout) -> List[str]:
    """Why the named Lean files are not verified by the current build record
    (``[]`` when they are).  A name that is not in the build tree is reported
    with its state; the rest are checked against
    ``scripts/logs/lean_build_evidence.json`` with their whole import closure."""
    out: List[str] = []
    modules: List[str] = []
    for n in names:
        state, module = lean_state(n, layout)
        if state != "audited":
            out.append(f"Lean {n} is {state} ({module}), not audited in the build")
        else:
            modules.append(module)
    if modules:
        out += lean_check.verification_problems(
            modules, evidence_path=layout.lean_evidence, root=layout.lean_source,
            library=layout.lean_library, repo_root=layout.root)
    return out


# ---------------------------------------------------------------------------
# Stage evidence
# ---------------------------------------------------------------------------

def latest_results(rec: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    """The last recorded result of each test a record names: ``test_results``
    holds ``{test, result, detail, date}`` entries, appended in order."""
    latest: Dict[str, Mapping[str, Any]] = {}
    for r in as_list(rec.get("test_results")):
        if isinstance(r, Mapping) and r.get("test"):
            latest[str(r["test"]).strip()] = r
    return latest


def _item_path(rec: Mapping[str, Any], layout: Layout) -> Optional[Path]:
    path = rec.get("path")
    return item_location(path, layout) if isinstance(path, str) and path else None


def stage_problems(rec: Mapping[str, Any], stage: str, layout: Layout,
                   fresh: bool = False, current: bool = False) -> List[str]:
    """What is missing for ``rec`` to stand at ``stage`` itself (this stage's
    evidence only; :func:`evidence_problems` accumulates).

    ``fresh`` is set by :func:`~glm_universal.intake.actions.advance` when an
    item is promoted to ``lean_verified`` or beyond: the current build record
    must then verify the named Lean files and everything they import.  Without
    it (a ledger check) ``lean_verified`` needs the ``lean_build`` entry that
    such a promotion wrote.

    ``current`` is set on every promotion: each named test's last result must
    then carry the fingerprint of the code as it now stands
    (:func:`test_fingerprint`).  A ledger check leaves it unset and
    :func:`check` warns instead."""
    out: List[str] = []
    item = _item_path(rec, layout)
    if stage == "received":
        if item is None:
            out.append("no path")
        elif not item.exists() and not rec.get("local_only"):
            out.append(f"{rec.get('path')} does not exist")
    elif stage == "triaged":
        if rec.get("kind") not in KINDS:
            out.append(f"kind {rec.get('kind')!r} is not one of {', '.join(KINDS)}")
        if not str(rec.get("offers") or "").strip():
            out.append("offers (what it claims or offers) is empty")
        if not str(rec.get("next_step") or "").strip() and rec.get("stage") not in ("absorbed", "closed"):
            out.append("next_step is empty")
    elif stage == "study_drafted":
        studies = as_list(rec.get("studies"))
        if not studies:
            out.append("no study named")
        for s in studies:
            out += study_problems(str(s), layout)
    elif stage == "tested":
        tests = [str(t).strip() for t in as_list(rec.get("tests"))]
        if not tests:
            out.append("no test named")
        latest = latest_results(rec)
        fp = test_fingerprint(rec, layout) if current else ""
        for t in tests:
            if t.startswith("call:"):
                module = t[len("call:"):].strip().rpartition(".")[0]
                if not module or module_path(module, layout) is None:
                    out.append(f"test {t} names no module of the package")
            elif t.startswith("staged:"):
                p = staged_test_path(t, rec, layout)
                if p is None or not p.is_file():
                    out.append(f"test {t} is neither staged in the item nor in the repository")
            else:
                p = test_path(t, item, layout)
                if p is None or not p.exists():
                    if not (rec.get("local_only") and t.startswith("item:")):
                        out.append(f"test {t} does not exist")
            r = latest.get(t)
            if r is None:
                out.append(f"no recorded result for {t}")
            elif r.get("result") != "pass":
                out.append(f"{t}: last recorded result {r.get('result')} ({r.get('date', 'undated')})")
            elif current and r.get("fingerprint") != fp:
                out.append(f"{t}: its last pass ({r.get('date', 'undated')}) was taken against "
                           "other code (the package, the item or its staged files have changed "
                           "since, or the result predates fingerprints); run it again")
    elif stage == "lean_written":
        lean = as_list(rec.get("lean"))
        if not lean:
            out.append("no Lean file named")
        for n in lean:
            state, module = lean_state(n, layout)
            if state != "audited":
                out.append(f"Lean {n} is {state} ({module}), not audited in the build")
    elif stage == "lean_verified":
        lean = [str(n) for n in as_list(rec.get("lean"))]
        if not lean:
            out.append("no Lean file named")
        elif fresh:
            out += build_problems(lean, layout)
        elif rec.get(AHEAD_FIELD):
            out += ahead_problems(rec, layout)
        elif not str(rec.get("lean_build") or "").strip():
            out.append("no lean_build entry: the build that verified the named Lean files is not "
                       "recorded (promote with `advance <id> lean_verified` after "
                       "scripts/rebuild_lean.sh passes)")
    elif stage == "measured":
        out += measurement_problems(rec, layout, promotion=current)
    elif stage == "absorbed":
        mods = as_list(rec.get("absorbed_into"))
        if not mods:
            out.append("absorbed_into is empty")
        left = staged_files(rec, layout)
        if left:
            out.append(f"{len(left)} staged file(s) not installed (absorption installs "
                       f"{STAGED_DIR}/ into the package): {', '.join(left[:3])}"
                       + (" ..." if len(left) > 3 else ""))
        tests = as_list(rec.get("tests"))
        for m in mods:
            if module_path(m, layout) is None:
                out.append(f"absorbed module {m} does not exist")
            elif not _module_tested(m, tests, item, layout, rec):
                out.append(f"absorbed module {m} has no test")
    elif stage == "closed":
        if not str(rec.get("closed_reason") or "").strip():
            out.append("closed without a reason")
        ev = as_list(rec.get("evidence"))
        if not ev:
            out.append("closed without evidence")
        out += [f"evidence {e} does not exist" for e in ev if not _doc_exists(e, layout)]
    return out


def evidence_problems(rec: Mapping[str, Any], layout: Optional[Layout] = None,
                      stage: Optional[str] = None, fresh: bool = False,
                      current: bool = False) -> List[str]:
    """Everything missing for ``rec`` to stand at ``stage`` (default: its
    recorded stage), accumulating the earlier stages' evidence.  ``closed``
    needs ``received``, ``triaged`` and its own evidence only.  ``fresh`` and
    ``current`` are passed to :func:`stage_problems` (a promotion, not a
    check)."""
    lay = layout or Layout.default()
    target = stage or rec.get("stage") or "received"
    if target == "closed":
        needed = ["received", "triaged", "closed"]
    else:
        needed = list(STAGES[: stage_index(target) + 1])
    out: List[str] = []
    for s in needed:
        out += [f"[{s}] {p}" for p in stage_problems(rec, s, lay, fresh=fresh, current=current)]
    return out


# ---------------------------------------------------------------------------
# The whole ledger
# ---------------------------------------------------------------------------

def _cited_lean(rec: Mapping[str, Any]) -> List[str]:
    names = list(as_list(rec.get("lean")))
    for part in as_list(rec.get("parts")):
        if isinstance(part, Mapping):
            names += as_list(part.get("lean"))
    for wheel in as_list(rec.get("wheels")):
        if isinstance(wheel, Mapping):
            names += as_list(wheel.get("lean"))
    return names


def load_provisional_quiet(layout: Layout) -> Dict[str, Any]:
    """The register of provisional families, or an empty one when it cannot
    be read (:func:`provisional_problems` reports that)."""
    try:
        return load_provisional(layout)
    except LedgerError:
        return {}


def ahead_problems(rec: Mapping[str, Any], layout: Optional[Layout] = None) -> List[str]:
    """What is missing from ``rec``'s ``ahead_of_build`` record (the owner's
    decision to absorb it ahead of the build, on its measurements and a
    standalone Lean check): the decision, its date, how the Lean files were
    checked (``check``) and which (``standalone``), each one of the record's
    own Lean files and audited in the build tree."""
    lay = layout or Layout.default()
    entry = rec.get(AHEAD_FIELD)
    if not isinstance(entry, Mapping):
        return [f"{AHEAD_FIELD} is not a mapping (decision, date, standalone, check)"]
    out: List[str] = []
    for key, what in (("decision", "the owner's decision"), ("date", "its date"),
                      ("check", "how the standalone Lean check was made")):
        if not str(entry.get(key) or "").strip():
            out.append(f"{AHEAD_FIELD} has no {key} ({what})")
    standalone = [str(n) for n in as_list(entry.get("standalone"))]
    if not standalone:
        out.append(f"{AHEAD_FIELD} names no Lean file checked standalone")
    own = {str(n) for n in as_list(rec.get("lean"))}
    for n in standalone:
        if n not in own:
            out.append(f"{AHEAD_FIELD}: the standalone Lean {n} is not one of the record's "
                       f"Lean files (the owner's build must confirm it too)")
        state, module = lean_state(n, lay)
        if state != "audited":
            out.append(f"{AHEAD_FIELD}: the standalone Lean {n} is {state} ({module}), not "
                       f"audited in the build")
    return out


def absorbed_modules(rec: Mapping[str, Any]) -> List[str]:
    """The modules ``rec`` names in ``absorbed_into`` and in its absorbed
    parts, sorted, each once."""
    out = {str(m) for m in as_list(rec.get("absorbed_into"))}
    for part in as_list(rec.get("parts")):
        if isinstance(part, Mapping) and part.get("status") == "absorbed":
            out.update(str(m) for m in as_list(part.get("absorbed_into")))
    return sorted(out)


def provisional_modules(rec: Mapping[str, Any]) -> List[str]:
    """The modules of ``rec``'s ``provisional`` parts, sorted, each once."""
    out = set()
    for part in as_list(rec.get("parts")):
        if isinstance(part, Mapping) and part.get("status") == "provisional":
            out.update(str(m) for m in as_list(part.get("absorbed_into")))
    return sorted(out)


def provisional_problems(data: Mapping[str, Any], layout: Optional[Layout] = None) -> List[str]:
    """The ledger's ``provisional`` parts against the register of provisional
    families (see the module docstring): every problem as one line."""
    lay = layout or Layout.default()
    try:
        register = load_provisional(lay)
    except LedgerError as exc:
        return [str(exc)]
    out: List[str] = []
    by_id = {rec.get("id"): rec for rec in data.get("items", []) if rec.get("id")}
    for rid, rec in by_id.items():
        if rec.get(AHEAD_FIELD):
            out += _ahead_entry_problems(rid, rec, register.get(rid), lay)
        parts = [p for p in as_list(rec.get("parts"))
                 if isinstance(p, Mapping) and p.get("status") == "provisional"]
        if not parts:
            continue
        stage = rec.get("stage") or "received"
        folder = str(rec.get("path") or "").split("/", 1)[0]
        if stage in TERMINAL_STAGES or folder != "ToDo":
            out.append(f"{rid}: {len(parts)} provisional part(s) in a record at {stage} in "
                       f"{folder}/; a provisional part is open work (absorb it on a verifying "
                       f"build record, or record it otherwise)")
        elif stage not in STAGES or stage_index(stage) < stage_index("lean_written"):
            out.append(f"{rid}: {len(parts)} provisional part(s) at stage {stage}; code is "
                       f"installed provisionally only at Lean written or beyond (tests "
                       f"passing, Lean files written and statically checked)")
        item = _item_path(rec, lay)
        tests = as_list(rec.get("tests"))
        for part in parts:
            mods = as_list(part.get("absorbed_into"))
            for m in mods:
                if module_path(m, lay) is None:
                    out.append(f"{rid}: provisional part {part.get('part')!r} cites module {m}, "
                               f"which is not in the package")
                elif not _module_tested(m, tests, item, lay, rec):
                    out.append(f"{rid}: provisional module {m} has no test")
        entry = register.get(rid)
        if entry is None:
            out.append(f"{rid}: {len(parts)} provisional part(s) but no entry in the register of "
                       f"provisional families ({lay.provisional.relative_to(lay.root)})")
            continue
        if entry.get("state", "provisional") != "provisional":
            out.append(f"{rid}: {len(parts)} provisional part(s) but the register entry's state "
                       f"is {entry.get('state')!r}")
            continue
        if not str(entry.get("decision") or "").strip() or not str(entry.get("date") or "").strip():
            out.append(f"{rid}: the register entry has no decision or no date (the owner's "
                       f"decision to install provisionally, with its date)")
        listed = sorted(str(m) for m in as_list(entry.get("modules")))
        if listed != provisional_modules(rec):
            out.append(f"{rid}: the register lists modules {listed} but the provisional parts "
                       f"name {provisional_modules(rec)}")
        lean = sorted(str(n) for n in as_list(entry.get("lean")))
        if not lean or not set(lean) <= {str(n) for n in as_list(rec.get("lean"))}:
            out.append(f"{rid}: the register's Lean files {lean} are not the record's own "
                       f"({as_list(rec.get('lean'))})")
    for rid in register:
        rec = by_id.get(rid)
        if rec is None:
            out.append(f"the register of provisional families lists {rid}, which has no intake "
                       f"record")
        elif register[rid].get("state") == AHEAD_STATE:
            if not rec.get(AHEAD_FIELD):
                out.append(f"the register lists {rid} as {AHEAD_STATE}, but its record has no "
                           f"{AHEAD_FIELD} (confirm-build removes the entry)")
        elif not any(isinstance(p, Mapping) and p.get("status") == "provisional"
                     for p in as_list(rec.get("parts"))):
            out.append(f"the register of provisional families lists {rid}, which has no "
                       f"provisional part (absorption removes the entry)")
    return out


def _ahead_entry_problems(rid: str, rec: Mapping[str, Any], entry: Optional[Mapping[str, Any]],
                          lay: Layout) -> List[str]:
    """A record absorbed ahead of the build against its register entry."""
    out: List[str] = []
    stage = rec.get("stage") or "received"
    folder = str(rec.get("path") or "").split("/", 1)[0]
    open_parts = [p for p in as_list(rec.get("parts"))
                  if isinstance(p, Mapping) and p.get("status") == "open"]
    absorbed_parts = [p for p in as_list(rec.get("parts"))
                      if isinstance(p, Mapping) and p.get("status") == "absorbed"]
    if stage == "absorbed":
        pass
    elif open_parts and absorbed_parts and folder == "ToDo" and stage in STAGES \
            and stage_index(stage) >= stage_index("lean_written"):
        pass  # its staged and provisional parts absorbed ahead; open parts remain
    else:
        out.append(f"{rid}: {AHEAD_FIELD} at stage {stage}; an item is absorbed ahead of the "
                   f"build at absorbed, or -- its open parts still in ToDo/ -- with absorbed "
                   f"parts at Lean written or beyond (`absorb-ahead <id>`)")
    if entry is None:
        out.append(f"{rid}: absorbed ahead of the build but no entry in the register "
                   f"({lay.provisional.relative_to(lay.root)}): the answers resting on it must "
                   f"say that the owner's build has still to confirm it")
        return out
    if entry.get("state") != AHEAD_STATE:
        out.append(f"{rid}: absorbed ahead of the build but the register entry's state is "
                   f"{entry.get('state', 'provisional')!r}, not {AHEAD_STATE!r}")
    if not str(entry.get("decision") or "").strip() or not str(entry.get("date") or "").strip():
        out.append(f"{rid}: the register entry has no decision or no date")
    listed = sorted(str(m) for m in as_list(entry.get("modules")))
    own = absorbed_modules(rec)
    if not listed or not set(listed) <= set(own):
        out.append(f"{rid}: the register lists modules {listed}, not among the record's absorbed "
                   f"modules {own}")
    for m in listed:
        if module_path(m, lay) is None:
            out.append(f"{rid}: the register lists module {m}, which is not in the package")
    lean = sorted(str(n) for n in as_list(entry.get("lean")))
    if not lean or not set(lean) <= {str(n) for n in as_list(rec.get("lean"))}:
        out.append(f"{rid}: the register's Lean files {lean} are not the record's own "
                   f"({as_list(rec.get('lean'))})")
    return out


def check(data: Mapping[str, Any], layout: Optional[Layout] = None) -> Dict[str, Any]:
    """Ledger <-> folders consistency and every record's stage evidence.

    Returns ``{"ok": bool, "errors": [...], "warnings": [...], "items": n}``.
    """
    lay = layout or Layout.default()
    errors: List[str] = []
    warnings: List[str] = []
    records = list(data.get("items", []))
    legacy: List[str] = []
    seen_ids: Dict[str, int] = {}
    by_path: Dict[str, str] = {}
    for rec in records:
        rid = rec.get("id")
        if not rid:
            errors.append(f"a record has no id: {rec!r:.80}")
            continue
        seen_ids[rid] = seen_ids.get(rid, 0) + 1
        path = rec.get("path") or ""
        if path in by_path:
            errors.append(f"{rid}: path {path} is also the path of {by_path[path]}")
        by_path[path] = rid
        folder = path.split("/", 1)[0]
        if folder not in ("ToDo", "done") or "/" not in path:
            errors.append(f"{rid}: path {path!r} is not ToDo/<item> or done/<item>")
        stage = rec.get("stage")
        if stage not in STAGES and stage != "closed":
            errors.append(f"{rid}: unknown stage {stage!r}")
            continue
        parts = as_list(rec.get("parts"))
        for part in parts:
            if not isinstance(part, Mapping) or part.get("status") not in PART_STATUSES:
                errors.append(f"{rid}: a part has no valid status ({PART_STATUSES}): {part!r:.80}")
        open_parts = [p for p in parts if isinstance(p, Mapping)
                      and p.get("status") in UNFINISHED_PART_STATUSES]
        if folder == "done":
            if stage not in ("absorbed", "closed"):
                errors.append(f"{rid}: filed in done/ at stage {stage}; done/ holds absorbed or closed items")
            if open_parts:
                errors.append(f"{rid}: filed in done/ with {len(open_parts)} open, staged or "
                              f"provisional part(s)")
        staged_parts = [p for p in parts if isinstance(p, Mapping) and p.get("status") == "staged"]
        if staged_parts and not staged_files(rec, lay):
            errors.append(f"{rid}: {len(staged_parts)} part(s) marked staged but the item has no "
                          f"{STAGED_DIR}/ files")
        elif folder == "ToDo" and stage in ("absorbed", "closed"):
            errors.append(f"{rid}: {stage} but still in ToDo/ (file it in done/)")
        item = item_location(path, lay) if path else None
        if rec.get("local_only"):
            if item is not None and not item.exists():
                flat = lay.material / Path(path).name
                where = " (still at the flat location source_material/" + flat.name + ")" if flat.exists() else ""
                warnings.append(f"{rid}: local-only file not in this checkout{where}; "
                                f"on the owner's machine move it to source_material/{path}")
        for p in evidence_problems(rec, lay):
            errors.append(f"{rid}: {p}")
        if str(rec.get(LEGACY_FIELD) or "").strip():
            if not is_legacy_absorption(rec):
                errors.append(f"{rid}: {LEGACY_FIELD} is only for a record filed in done/ at "
                              "absorbed without an acceptance block (it cannot stand in for an "
                              "acceptance decision anywhere else)")
            else:
                legacy.append(rid)
        for rel in staged_files(rec, lay):
            target = lay.root / rel
            if not rel.startswith(str(lay.package.relative_to(lay.root)) + "/"):
                errors.append(f"{rid}: staged file {rel} is not below the package "
                              f"({lay.package.relative_to(lay.root)}/)")
            elif target.exists():
                src = staged_root(rec, lay) / rel
                if src.read_bytes() == target.read_bytes():
                    warnings.append(f"{rid}: staged file {rel} is already installed (same bytes)")
                else:
                    errors.append(f"{rid}: staged file {rel} differs from the file already "
                                  f"at that path; absorption would overwrite it")
        if (folder == "ToDo" and stage not in TERMINAL_STAGES
                and stage_index(stage) >= stage_index("tested")):
            stale = stale_results(rec, lay)
            if stale:
                warnings.append(f"{rid}: {len(stale)} test result(s) not taken against the code "
                                f"as it now stands ({', '.join(stale[:2])}"
                                + (" ..." if len(stale) > 2 else "")
                                + "); the next promotion runs them again")
        if (stage != "closed"
                and (stage_index(stage) >= stage_index("lean_verified") or rec.get(AHEAD_FIELD))
                and lay.lean_evidence.is_file() and as_list(rec.get("lean"))):
            found = build_problems([str(n) for n in as_list(rec.get("lean"))], lay)
            if rec.get(AHEAD_FIELD):
                if found:
                    warnings += [f"{rid}: absorbed ahead of the build; the build record does not "
                                 f"confirm it yet: {p}" for p in found]
                else:
                    warnings.append(f"{rid}: absorbed ahead of the build, and the build record "
                                    f"now verifies its Lean files: run `python3 -m "
                                    f"glm_universal.intake confirm-build {rid}`")
            else:
                for p in found:
                    warnings.append(f"{rid}: since its verified build: {p}")
        for n in _cited_lean(rec):
            state, module = lean_state(n, lay)
            if state in ("absent", "ambiguous", "unaudited"):
                errors.append(f"{rid}: cites Lean {n}: {state} ({module})")
            elif state in ("held", "missing"):
                warnings.append(f"{rid}: cites Lean {n}: {state}")
        for part in parts:
            if not isinstance(part, Mapping):
                continue
            for s in as_list(part.get("studies")):
                if not study_exists(s, lay):
                    errors.append(f"{rid}: part {part.get('part')!r} cites study {s}, which does not exist")
            for m in as_list(part.get("absorbed_into")):
                if part.get("status") == "staged":
                    if staged_module_path(m, rec, lay) is None:
                        errors.append(f"{rid}: staged part {part.get('part')!r} cites module {m}, "
                                      f"which the item does not stage")
                elif part.get("status") == "provisional":
                    pass  # provisional_problems, below
                elif module_path(m, lay) is None:
                    errors.append(f"{rid}: part {part.get('part')!r} cites module {m}, which does not exist")
    errors += provisional_problems(data, lay)
    register = load_provisional_quiet(lay)
    provisional = [rid for rid, e in register.items() if e.get("state") != AHEAD_STATE]
    ahead = [rid for rid, e in register.items() if e.get("state") == AHEAD_STATE]
    if provisional:
        warnings.append(f"{len(provisional)} item(s) installed provisionally, awaiting the "
                        f"build record of their Lean files: {', '.join(provisional)}")
    if ahead:
        warnings.append(f"{len(ahead)} item(s) absorbed ahead of the build by the owner's "
                        f"decision, on their measurements and a standalone Lean check; the "
                        f"owner's scripts/rebuild_lean.sh still has to confirm their Lean files "
                        f"(then `confirm-build <id>`): {', '.join(ahead)}")
    if legacy:
        warnings.append(f"{len(legacy)} record(s) absorbed before acceptance decisions were "
                        f"recorded ({LEGACY_FIELD}); their measurement is the closed study cited "
                        f"in measured: {', '.join(legacy[:4])}" + (" ..." if len(legacy) > 4 else ""))
    for rid, n in seen_ids.items():
        if n > 1:
            errors.append(f"id {rid} is used by {n} records")
    filed = folder_items(lay)
    for path in filed:
        if path not in by_path:
            errors.append(f"{path} is filed but has no intake record "
                          f"(add one to {lay.ledger.name})")
    for p in loose_items(lay):
        local = [r for r in records if r.get("local_only") and Path(r.get("path", "")).name == p.name]
        if local:
            continue  # reported above as a local-only file awaiting its move
        errors.append(f"source_material/{p.name} is loose: register it "
                      f"(`python3 -m glm_universal.intake register source_material/{p.name}`)")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "items": len(records)}

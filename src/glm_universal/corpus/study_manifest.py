"""``glm_universal.corpus.study_manifest`` -- the study manifests, derived
from their documents and the tree, and kept in step with them.

Each study is a pair: ``studies/X.md`` (the prose, with its tier-0 block) and
``studies/X.yaml`` (the manifest the GLM reads, schema
``glm-study-manifest/v1``, ``studies/_schema/study.schema.yaml``).  The
manifests were first written by a one-off converter that left most structured
fields empty and filled the file references badly (every code reference
lacked its ``.py`` and test and Lean names were mixed in).  Directive D10 says
a document is data; a manifest that a person has to keep in step by hand is a
stored table, and D20 says generate, don't store.  So every field that *can*
be read off the ``.md`` and the tree is derived here, and ``--check`` fails
when a manifest has drifted from what it would be derived as.

What is derived (all deterministic, from the ``.md`` and the tree only):

* ``id`` (the file stem), ``title`` (the ``#`` heading), ``sections``;
* ``question``, ``verdict``, ``deciding_figure``, ``recomputed_by`` -- the
  four tier-0 fields, parsed by :mod:`glm_universal.corpus.inventory` exactly
  as the corpus check parses them;
* ``last_altered`` -- the latest ``Last altered <date>`` stamp of the ``.md``,
  else its ``Created <date>`` stamp;
* ``phase`` -- the study's own "pre-registration for Phase N", else the
  ``## Phase N`` record of ``MASTER_PLAN.md`` (or its archive) that names it
  as its study, else the phase the records most often write beside a link to
  it ("Phase N ([`X.md`](...))"), else ``0`` (unknown);
* ``status`` -- ``negative`` when the verdict answers "No" (or "not
  reproduced"), ``open`` when the phase record says open or the verdict says
  the answer is still to come, ``closed`` otherwise (a verdict is an answer);
* ``faculty`` (D15) -- the study's own "Faculty (D15)." line, else the
  "Faculties." paragraph of its phase record; ``unknown`` when neither says;
* ``marks`` -- ``declared`` from every table whose first column is
  ``mark``; ``met`` and ``missed`` from those tables' result columns and from
  sentences such as "**A1 met.**" or "R2, R3 missed" (the last statement of a
  mark wins, so a re-take overrides a first take); ``amended`` the primed
  marks (``F1′``);
* ``predecessors`` -- the studies the ``.md`` links to whose phase is
  strictly earlier (so the graph is acyclic by construction, as
  ``GLM.StudyLedger.no_cycle_of_phase_lt`` states); ``related`` -- the other
  linked studies; ``successors`` -- the inverse of ``predecessors``;
* ``directives`` -- directives the ``.md`` cites as "directive D7",
  "directives D3 and D7" or "(D7)" (a parenthesised name that is also one of
  the study's own marks is not counted), D1-D22 in the numbering of
  ``PROJECT_DIRECTIVES.md``;
* ``file_refs`` -- ``prose``; ``code``: package modules the ``.md`` cites
  (``reasoning/x.py``, ``glm_universal.reasoning.x.f``, a unique module name
  in backticks), relative to ``src/glm_universal``, existing files only;
  ``test``: cited test files that exist; ``lean``: cited Lean files that exist
  in the build tree or are held in ``src/lean/awaiting_recovery``
  (``lean_held`` lists the held ones); ``lean_missing``: cited Lean files that
  are recorded missing in ``studies/_lean_files_needed.md``; ``missing``:
  code and test files cited by a package path that do not exist.

Everything else (``controls``, ``perturbations``, ``layer``, ``junctions``,
``wobble_deps``, ``reversibility``, ``evidence``, ``follow_ups``,
``supersedes``, ``superseded_by``, ``file_refs.wheel``) is a judgement and is
kept exactly as written.  A derived field named in the manifest's
``hand_fields`` list is kept as written too; a name covers its sub-fields
(``marks`` keeps ``marks.declared``, ``marks.met``, ``marks.missed`` and
``marks.amended``) -- for a study whose document also tabulates a later
re-measurement that is not the study's own record.

Command line::

    PYTHONPATH=src python3 -m glm_universal.corpus.study_manifest --check
    PYTHONPATH=src python3 -m glm_universal.corpus.study_manifest --sync
    PYTHONPATH=src python3 -m glm_universal.corpus.study_manifest --defects
    PYTHONPATH=src python3 -m glm_universal.corpus.study_manifest --show ID

``--check`` exits 1 when any manifest is missing, drifted, orphaned or
schema-invalid; ``--sync`` rewrites only the manifests whose data moved.
Nothing else here writes.

*Created 31 October 2026 (repository check of the YAML study system).  Last
altered 31 October 2026: a ``hand_fields`` name covers its sub-fields; a prose
outcome written after a table keeps its place after the table's rows; a dotted
reference to a name a package's ``__init__.py`` defines or re-exports
(``glm_universal.wheels.provisional_status``) resolves to the package instead
of being listed as a missing module.*
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, \
    Set, Tuple

from .. import constants as C
from . import inventory as inv

__all__ = [
    "SCHEMA_NAME",
    "DERIVED_FIELDS",
    "KEPT_FIELDS",
    "Tree",
    "tree",
    "study_documents",
    "parse_document",
    "derive_all",
    "load_manifests",
    "manifest_paths",
    "merged_manifest",
    "drift",
    "sync",
    "manifest_report",
    "defect_counts",
    "main",
]

SCHEMA_NAME = "glm-study-manifest/v1"

#: The fields this module derives.  Dotted paths address nested keys.
DERIVED_FIELDS: Tuple[str, ...] = (
    "schema", "id", "title", "phase", "status", "question", "verdict",
    "deciding_figure", "recomputed_by", "last_altered", "faculty",
    "marks.declared", "marks.met", "marks.missed", "marks.amended",
    "predecessors", "successors", "related", "directives", "sections",
    "file_refs.prose", "file_refs.code", "file_refs.test", "file_refs.lean",
    "file_refs.lean_held", "file_refs.lean_missing", "file_refs.missing",
)

#: The judgement fields, kept exactly as written, with the value a new
#: manifest starts with.
KEPT_FIELDS: Dict[str, Any] = {
    "controls": [],
    "perturbations": [],
    "layer": {"primary": "", "resolutions_tried": [], "non_edges": [],
              "refinement_of": ""},
    "junctions": [],
    "wobble_deps": [],
    "reversibility": {"class": "unknown"},
    "evidence": [],
    "follow_ups": [],
    "supersedes": [],
    "superseded_by": "",
    "file_refs.wheel": [],
    "hand_fields": [],
}

#: The comment written above every manifest.  The date line is the day the
#: manifest's data last moved (D17); it is not part of what ``--check``
#: compares.
_HEADER = (
    "# GLM study manifest (glm-study-manifest/v1)\n"
    "# Derived from the paired .md and the tree by\n"
    "# `python3 -m glm_universal.corpus.study_manifest --sync`; the .md is the\n"
    "# prose, this YAML is the face the GLM reads.  Judgement fields (controls,\n"
    "# layer, junctions, wobble_deps, reversibility, evidence, follow_ups, ...)\n"
    "# are kept as written; a derived field listed in hand_fields is kept too.\n"
)

_MONTHS = ("January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December")


def _today_stamp() -> str:
    today = _dt.date.today()
    return f"{today.day} {_MONTHS[today.month - 1]} {today.year}"


# ===========================================================================
# YAML I/O (deterministic)
# ===========================================================================

def _pyyaml():
    import yaml as _yaml  # PyYAML; the manifests cannot be read without it
    return _yaml


def _load_yaml(text: str) -> Any:
    yaml = _pyyaml()
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    return yaml.load(text, Loader=loader)


def _dump_yaml(data: Mapping[str, Any]) -> str:
    yaml = _pyyaml()
    dumper = getattr(yaml, "CSafeDumper", yaml.SafeDumper)
    return yaml.dump(dict(data), Dumper=dumper, sort_keys=True,
                     allow_unicode=True, width=100, default_flow_style=False)


def manifest_paths() -> List[Path]:
    """Every ``studies/*.yaml`` manifest, sorted."""
    return sorted(C.STUDIES_DIR.glob("*.yaml"))


_MANIFEST_CACHE: Dict[str, Tuple[int, Dict[str, Any]]] = {}


def load_manifests(studies_dir: Optional[Path] = None
                   ) -> Dict[str, Dict[str, Any]]:
    """Every study manifest, keyed by its ``id`` -- the one loader the study
    ledger and the study index share.

    A file that does not parse, is not a mapping, or declares another schema
    is left out (``--check`` names it).  Parsed files are cached on their
    modification time, so repeated calls in one process cost a ``stat`` each.
    """
    folder = Path(studies_dir) if studies_dir is not None else C.STUDIES_DIR
    out: Dict[str, Dict[str, Any]] = {}
    try:
        _pyyaml()
    except ImportError:
        return out
    for path in sorted(folder.glob("*.yaml")):
        try:
            stamp = path.stat().st_mtime_ns
        except OSError:
            continue
        key = str(path)
        cached = _MANIFEST_CACHE.get(key)
        if cached is not None and cached[0] == stamp:
            data = cached[1]
        else:
            try:
                data = _load_yaml(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            _MANIFEST_CACHE[key] = (stamp, data)
        if data.get("schema") != SCHEMA_NAME or not isinstance(
                data.get("id"), str):
            continue
        out[data["id"]] = data
    return out


# ===========================================================================
# The tree: what exists, read once
# ===========================================================================

def _rel(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def _parse_missing_registry(text: str) -> Tuple[str, ...]:
    """The Lean file names of the *Missing files* table of
    ``studies/_lean_files_needed.md`` (first column, backticked)."""
    out: List[str] = []
    in_section = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_section = line.strip().lower() == "## missing files"
            continue
        if in_section and line.startswith("|"):
            first = line.strip("|").split("|")[0].strip()
            match = re.fullmatch(r"`([^`]+\.lean)`", first)
            if match:
                out.append(match.group(1))
    return tuple(out)


@dataclass
class Tree:
    """What the tree holds, for resolving the names a document cites."""

    modules: Set[str]                    # package-relative .py, tests excluded
    module_stems: Dict[str, List[str]]   # stem -> modules
    subpackages: Set[str]                # first path components that are dirs
    tests: Set[str]                      # file names in the tests folder
    lean: Dict[str, str]                 # GLM-relative stem path -> "build"|"held"
    lean_stems: Dict[str, List[str]]     # file stem -> GLM-relative stem paths
    lean_registry: Tuple[str, ...]       # recorded-missing names (X.lean or dir/X.lean)
    study_ids: Set[str]
    phase_records: Dict[int, "PhaseRecord"]
    phase_votes: Dict[str, Counter]
    #: package-relative ``__init__.py`` -> the names it defines or re-exports
    #: (so ``glm_universal.wheels.provisional_status`` resolves to the
    #: package rather than reading as a missing module ``wheels/provisional_status.py``)
    exports: Dict[str, Set[str]] = field(default_factory=dict)

    @property
    def registry_stems(self) -> Dict[str, str]:
        """Stem of each recorded-missing Lean file -> its name without .lean."""
        out: Dict[str, str] = {}
        for name in self.lean_registry:
            stem_path = name[:-len(".lean")]
            out[stem_path.rsplit("/", 1)[-1]] = stem_path
        return out


@dataclass
class PhaseRecord:
    """One ``## Phase N`` record of the plan."""

    phase: int
    status: str            # "closed", "open" or ""
    studies: List[str]     # the studies the record names as its study
    faculties: str         # the "Faculties." paragraph, or ""


_STUDY_LINK = re.compile(
    r"\[[^\]]*\]\((?:\.\./)?(?:studies/)?([A-Za-z0-9_]+)\.md(?:#[^)]*)?\)")
#: Words in the same sentence before a link that make it the record's own
#: study ("Study:", "the study is", "the pre-registration (...)").
_CUE_BEFORE = re.compile(r"(?i)\bstud(?:y|ies)\b|pre-?registration|"
                         r"pre-?registered|committed before|write-?ups?\b|"
                         r"what it settled|where it is")
#: Paragraphs of a record that talk about *other* rounds' studies.
_NOT_OWN = re.compile(r"(?i)^\W*(?:what it invalidated|left\b|answers moved|"
                      r"invalidated|the round before|before it)")
#: Words right after a link that do the same ("[X](...) is the study",
#: "[X](...) (marks L1, ...)", "[X](...) was written").
_CUE_AFTER = re.compile(r"(?i)^\W{0,6}(?:\(marks?\b|is the study|was written|"
                        r"§§?0|\(\d+ of \d+ marks)")
_PHASE_HEADING = re.compile(r"^#{2,4} Phase (\d+)\b")
_PHASE_LEAD = re.compile(r"^\*\*[^*]{0,40}?\bPhase (\d+)\*\*")


def _phase_records(study_ids: Set[str]) -> Tuple[Dict[int, PhaseRecord],
                                                 Dict[str, Counter]]:
    """Read the phase records and the "Phase N ([X.md](...))" votes.

    A record is a ``## Phase N`` section of the plan (or its archives), or a
    paragraph of the rounds archive led by ``**... Phase N**``.  In its first
    six paragraphs, a link to a study is the record's own study when the same
    sentence says so before it ("Study:", "the study is", "pre-registration")
    or the words after it do ("is the study", "(marks ...").
    """
    records: Dict[int, PhaseRecord] = {}
    votes: Dict[str, Counter] = {}
    plan_files = ("MASTER_PLAN.md", "archive/MASTER_PLAN_ARCHIVE.md",
                  "archive/STATUS_ROUNDS_ARCHIVE.md")
    vote_files = plan_files + ("STATUS.md", "SYSTEM.md",
                               "studies/GLM_ACADEMIC_PAPER.md")
    vote_pattern = re.compile(
        r"Phase (\d+)\s*\(\[`?(?:studies/)?([A-Za-z0-9_]+)\.md`?\]\(")
    for name in vote_files:
        path = C.REPOSITORY_ROOT / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for match in vote_pattern.finditer(text):
            sid = match.group(2)
            if sid in study_ids:
                votes.setdefault(sid, Counter())[int(match.group(1))] += 1
        #  "[X](...) is the study, ... and MASTER_PLAN.md Phase N the record"
        for match in re.finditer(
                r"\[`?(?:studies/)?([A-Za-z0-9_]+)\.md`?\]\([^)]*\) is the "
                r"study\b.{0,300}?\bPhase (\d+)\b", text, re.S):
            sid = match.group(1)
            if sid in study_ids:
                votes.setdefault(sid, Counter())[int(match.group(2))] += 3
        if name not in plan_files:
            continue
        current = 0
        depth = 0
        for paragraph in re.split(r"\n\s*\n", text):
            stripped = "\n".join(line for line in paragraph.splitlines()
                                 if line.strip() != "---").strip()
            if not stripped:
                continue
            heading = _PHASE_HEADING.match(stripped)
            lead = _PHASE_LEAD.match(stripped)
            if heading:
                current, depth = int(heading.group(1)), 0
                record = records.setdefault(current,
                                            PhaseRecord(current, "", [], ""))
                rest = stripped.split("\n", 1)
                if len(rest) == 1:
                    continue
                stripped = rest[1]
            elif lead:
                current, depth = int(lead.group(1)), 0
                records.setdefault(current, PhaseRecord(current, "", [], ""))
            elif re.match(r"^#{1,2} ", stripped):
                current = 0
                continue
            elif stripped.startswith("#"):
                #  A sub-heading of the record ("### 33.1 Pre-registered
                #  ..."): the record goes on, the heading line is context.
                if not current:
                    continue
            if not current:
                continue
            depth += 1
            record = records[current]
            status = re.search(r"\*\*Status:\s*([A-Za-z]+)", stripped)
            if status and not record.status:
                record.status = status.group(1).lower()
            fac = re.match(r"\*\*Facult(?:y|ies)[^*]*\*\*(.*)", stripped, re.S)
            if fac and not record.faculties:
                record.faculties = fac.group(1)
            if depth > 12 or _NOT_OWN.match(stripped):
                continue
            for link in _STUDY_LINK.finditer(stripped):
                sid = link.group(1)
                if sid not in study_ids or sid in record.studies:
                    continue
                before = stripped[max(0, link.start() - 250):link.start()]
                sentence = re.split(r"(?<=[.;])\s+(?=[A-Z*(])", before)[-1]
                after = stripped[link.end():link.end() + 40]
                if _CUE_BEFORE.search(sentence) or _CUE_AFTER.search(after):
                    record.studies.append(sid)
    return records, votes


_TREE_CACHE: Dict[str, Tree] = {}


def _module_exports(path: Path) -> Set[str]:
    """The top-level names a module defines, assigns, imports or lists in
    ``__all__`` (descending into top-level ``if`` / ``try`` blocks); empty
    when the file does not parse."""
    import ast
    try:
        module = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
        return set()
    names: Set[str] = set()

    def targets(node: "ast.AST") -> None:
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                targets(elt)

    def walk(body: Sequence["ast.stmt"]) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    targets(target)
                if any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets) \
                        and isinstance(node.value, (ast.List, ast.Tuple)):
                    names.update(e.value for e in node.value.elts
                                 if isinstance(e, ast.Constant) and isinstance(e.value, str))
            elif isinstance(node, ast.AnnAssign):
                targets(node.target)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if alias.name != "*":
                        names.add((alias.asname or alias.name).split(".")[0])
            elif isinstance(node, ast.If):
                walk(node.body)
                walk(node.orelse)
            elif isinstance(node, ast.Try):
                walk(node.body)
                for handler in node.handlers:
                    walk(handler.body)
                walk(node.orelse)
                walk(node.finalbody)

    walk(module.body)
    return names


def tree(refresh: bool = False) -> Tree:
    """The tree index (cached for the process; ``refresh`` rebuilds it)."""
    if not refresh and "tree" in _TREE_CACHE:
        return _TREE_CACHE["tree"]
    package = C.PACKAGE_ROOT
    modules: Set[str] = set()
    for path in package.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        rel = _rel(path, package)
        if rel.startswith("tests/"):
            continue
        modules.add(rel)
    stems: Dict[str, List[str]] = {}
    for rel in sorted(modules):
        stems.setdefault(rel.rsplit("/", 1)[-1][:-3], []).append(rel)
    subpackages = {p.name for p in package.iterdir()
                   if p.is_dir() and p.name not in ("__pycache__", "tests")}
    tests_dir = package / "tests"
    tests = {p.name for p in tests_dir.glob("*.py")} if tests_dir.is_dir() \
        else set()
    lean: Dict[str, str] = {}
    for kind, base in (("held", C.LEAN_HOLDING_DIR / C.LEAN_LIBRARY / "GLM"),
                       ("build", C.LEAN_GLM_DIR)):
        if not base.is_dir():
            continue
        for path in base.rglob("*.lean"):
            if ".lake" in path.parts:
                continue
            lean[_rel(path, base)[:-len(".lean")]] = kind
    lean_stems: Dict[str, List[str]] = {}
    for rel in sorted(lean):
        lean_stems.setdefault(rel.rsplit("/", 1)[-1], []).append(rel)
    registry: Tuple[str, ...] = ()
    if C.LEAN_FILES_NEEDED.is_file():
        registry = _parse_missing_registry(
            C.LEAN_FILES_NEEDED.read_text(encoding="utf-8"))
    study_ids = {p.stem for p in study_documents()}
    records, votes = _phase_records(study_ids)
    exports = {rel: _module_exports(package / rel) for rel in modules
               if rel.endswith("__init__.py")}
    built = Tree(modules=modules, module_stems=stems, subpackages=subpackages,
                 tests=tests, lean=lean, lean_stems=lean_stems,
                 lean_registry=registry, study_ids=study_ids,
                 phase_records=records, phase_votes=votes, exports=exports)
    _TREE_CACHE["tree"] = built
    return built


# ===========================================================================
# Reading one document
# ===========================================================================

def study_documents() -> List[Path]:
    """Every study document: a top-level ``studies/*.md`` with a tier-0
    block (``_``-prefixed registries excluded)."""
    out: List[Path] = []
    for path in sorted(C.STUDIES_DIR.glob("*.md")):
        if path.name.startswith("_"):
            continue
        text = path.read_text(encoding="utf-8")
        sections = inv._split_sections("studies/" + path.name, text)
        tier0, _span = inv._parse_tier0(sections)
        if tier0 is not None:
            out.append(path)
    return out


_DATE = r"(\d{1,2} (?:%s) \d{4})" % "|".join(_MONTHS)
_LAST_ALTERED = re.compile(r"Last altered\s+" + _DATE)
_CREATED = re.compile(r"Created\s+" + _DATE)


def _date_key(text: str) -> Tuple[int, int, int]:
    day, month, year = text.split()
    return (int(year), _MONTHS.index(month) + 1, int(day))


def _last_altered(text: str) -> str:
    altered = _LAST_ALTERED.findall(text)
    if altered:
        return max(altered, key=_date_key)
    created = _CREATED.findall(text)
    if created:
        return min(created, key=_date_key)
    return ""


def _strip_md(cell: str) -> str:
    return re.sub(r"[*`_]", "", cell).strip()


_MARK_ID = re.compile(r"^([A-Z][A-Z]?\d{0,2}[a-z]?)([′'])?$")


def _mark_ids(cell: str) -> List[str]:
    """Mark ids written in one table cell: ``**L1**``, ``F1′``, ``C1–C6``,
    ``R1, R2``.  Anything else gives nothing."""
    text = _strip_md(cell)
    out: List[str] = []
    for part in re.split(r"\s*(?:,|/|\band\b)\s*", text):
        part = part.strip()
        if not part:
            continue
        rng = re.fullmatch(r"([A-Z][A-Z]?)(\d{1,2})\s*[–-]\s*\1?(\d{1,2})", part)
        if rng:
            low, high = int(rng.group(2)), int(rng.group(3))
            if low < high <= low + 20:
                out.extend(f"{rng.group(1)}{n}" for n in range(low, high + 1))
                continue
        match = _MARK_ID.match(part)
        if not match:
            return []
        out.append(match.group(1) + ("′" if match.group(2) else ""))
    return out


@dataclass
class _Table:
    header: List[str]
    rows: List[List[str]]
    line: int


def _tables(lines: Sequence[str]) -> List[_Table]:
    out: List[_Table] = []
    index = 0
    fenced = False
    while index < len(lines):
        line = lines[index]
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if fenced or not line.lstrip().startswith("|"):
            index += 1
            continue
        start = index
        block: List[str] = []
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            block.append(lines[index].strip())
            index += 1
        cells = [[c.strip() for c in row.strip("|").split("|")]
                 for row in block]
        if len(cells) >= 2 and all(re.fullmatch(r":?-{2,}:?", c.replace(" ", ""))
                                   for c in cells[1] if c):
            out.append(_Table(cells[0], cells[2:], start))
    return out


_RESULT_COLUMNS = ("met", "met?", "outcome", "result", "results", "verdict",
                   "status", "outcome (measured)")


def _outcome_word(cell: str, yes_no: bool = False) -> Optional[str]:
    """``met``/``missed`` from a result cell; in a column headed ``met``,
    ``yes``/``no`` (and ``✓``/``✗``) say the same."""
    text = _strip_md(cell).lower().lstrip(" :—-")
    if yes_no:
        if re.match(r"(?:yes|✓|✔)\b", text) or text in ("✓", "✔"):
            return "met"
        if re.match(r"(?:no|✗|✘)\b", text) or text in ("✗", "✘"):
            return "missed"
    if text.startswith("met when") or text.startswith("met if"):
        return None
    if text.startswith("not met") or text.startswith("missed") \
            or text.startswith("not  met"):
        return "missed"
    if re.match(r"met\b", text):
        return "met"
    return None


def _marks(text: str, figure: str) -> Dict[str, List[str]]:
    """Declared, met, missed and amended marks, as the study tabulates them."""
    lines = text.splitlines()
    tables = _tables(lines)
    declared: List[str] = []
    amended: List[str] = []
    events: List[Tuple[int, str, str]] = []   # (position, mark, outcome)

    def note(mark: str) -> None:
        target = amended if mark.endswith("′") else declared
        if mark not in target:
            target.append(mark)

    for table in tables:
        head = [_strip_md(h).lower() for h in table.header]
        if not head or head[0] not in ("mark", "marks"):
            continue
        result_col = None
        for position, name in enumerate(head):
            if position and name in _RESULT_COLUMNS:
                result_col = position
        for offset, row in enumerate(table.rows):
            ids = _mark_ids(row[0]) if row else []
            if not ids:
                continue
            for mark in ids:
                note(mark)
            outcome = None
            if result_col is not None and result_col < len(row):
                outcome = _outcome_word(row[result_col],
                                        head[result_col] in ("met", "met?"))
            if outcome is None and result_col is None:
                for cell in row[1:]:
                    outcome = _outcome_word(cell)
                    if outcome:
                        break
            if outcome:
                for mark in ids:
                    events.append((table.line + 2 + offset, mark, outcome))
    #  Marks declared as bold paragraph leads: "**G1 — the census is right.**"
    for line in lines:
        lead = re.match(r"^\*\*([A-Z][A-Z]?\d{1,2}[a-z]?)([′'])?\s*[—–:-]", line)
        if lead:
            note(lead.group(1) + ("′" if lead.group(2) else ""))
    #  Tables whose first column is not "mark" but which carry a result
    #  column: a row whose first cell is, or starts with, a mark id
    #  ("| T1 say | ... | yes |").
    for table in tables:
        head = [_strip_md(h).lower() for h in table.header]
        if head and head[0] in ("mark", "marks"):
            continue
        result_col = None
        for position, name in enumerate(head):
            if position and name in _RESULT_COLUMNS:
                result_col = position
        for offset, row in enumerate(table.rows):
            ids = _mark_ids(row[0]) if row else []
            if not ids and row and result_col is not None:
                first = _strip_md(row[0]).split(" ", 1)[0]
                if re.fullmatch(r"[A-Z][A-Z]?\d{1,2}[a-z]?[′']?", first):
                    ids = [first.replace("'", "′")]
            if not ids or (result_col is None and not all(
                    i.rstrip("′") in declared for i in ids)):
                continue
            outcome = None
            if result_col is not None and result_col < len(row):
                outcome = _outcome_word(row[result_col],
                                        head[result_col] in ("met", "met?"))
            if outcome is None:
                for cell in reversed(row[1:]):
                    outcome = _outcome_word(cell)
                    if outcome:
                        break
            if outcome:
                for mark in ids:
                    note(mark)
                    events.append((table.line + 2 + offset, mark, outcome))
    #  The deciding figure's parenthesised mark list ("(L1, A1, ...)").
    for group in re.findall(r"marks?[^()]{0,40}\(([^)]*)\)", figure):
        ids = _mark_ids(group)
        for mark in ids:
            note(mark)
    if declared:
        bases = sorted({m for m in declared}, key=len, reverse=True)
        alt = "|".join(re.escape(m) for m in bases)
        one = rf"(?:{alt})(?:[′'])?"
        prose = re.compile(
            rf"(?<![A-Za-z0-9])((?:{one})(?:\s*(?:,|and|&)\s*(?:{one}))*)"
            rf"(?![A-Za-z0-9])\s*(?:\*\*)?\s*(?:,\s*)?"
            rf"(?:(?:is|are|was|were|now|both|all)\s+)*(?:\*\*)?\s*[:—-]?\s*"
            rf"(?:\*\*)?(met|missed|not met)\b(?!\s+when)")
        #  Prose is matched across line breaks ("**A2, A4 and\nO1 met**"),
        #  with table rows blanked so a declaration cell is never read as an
        #  outcome; positions are line numbers, as for the tables.
        #  A blanked row keeps its length (spaces), so an offset into
        #  ``prose_text`` is an offset into the document and the line number
        #  of a prose outcome after a table stays after the table's rows.
        prose_text = "\n".join(" " * len(line) if line.lstrip().startswith("|")
                                else line for line in lines)
        starts: List[int] = []
        position = 0
        for line in lines:
            starts.append(position)
            position += len(line) + 1
        import bisect
        for match in prose.finditer(prose_text):
            outcome = "missed" if match.group(2) != "met" else "met"
            number = bisect.bisect_right(starts, match.start(2)) - 1
            for mark in re.findall(one, match.group(1)):
                mark = mark.replace("'", "′")
                note(mark)
                events.append((number, mark, outcome))
    final: Dict[str, str] = {}
    for _pos, mark, outcome in sorted(events, key=lambda e: e[0]):
        final[mark] = outcome
    #  "10 of 10 marks" in the deciding figure, over exactly the declared
    #  marks, settles the ones the prose does not name one by one; so does
    #  "8 of 9 marks" when the one missed mark is named.
    tally = re.search(r"\b(\d+) of (\d+)(?: pre-registered| declared| measured)? "
                      r"marks\b", figure)
    if tally and declared:
        got, of = int(tally.group(1)), int(tally.group(2))
        missed_now = [m for m in declared if final.get(m) == "missed"]
        if of == len(declared) and got <= of and len(missed_now) == of - got:
            for mark in declared:
                final.setdefault(mark, "met")
    ordered = declared + amended
    return {
        "declared": declared,
        "met": [m for m in ordered if final.get(m) == "met"],
        "missed": [m for m in ordered if final.get(m) == "missed"],
        "amended": amended,
    }


_DIRECTIVE_WORD = re.compile(
    r"\b[Dd]irectives?\s+((?:\*\*)?D\d{1,2}(?:\*\*)?"
    r"(?:\s*(?:,|and|or|/|–|-|to)\s*(?:\*\*)?D\d{1,2}(?:\*\*)?)*)")
_DIRECTIVE_PAREN = re.compile(
    r"\(((?:D\d{1,2})(?:\s*(?:,|/|and)\s*D\d{1,2})*)\)")


def _directives(text: str, marks: Iterable[str]) -> List[str]:
    own_marks = {m.rstrip("′") for m in marks}
    found: Set[int] = set()
    for match in _DIRECTIVE_WORD.finditer(text):
        group = match.group(1).replace("*", "")
        for rng in re.finditer(r"D(\d{1,2})\s*(?:–|-|to)\s*D(\d{1,2})", group):
            low, high = int(rng.group(1)), int(rng.group(2))
            if low < high:
                found.update(range(low, high + 1))
        found.update(int(n) for n in re.findall(r"D(\d{1,2})", group))
    for match in _DIRECTIVE_PAREN.finditer(text):
        for name in re.findall(r"D\d{1,2}", match.group(1)):
            if name not in own_marks:
                found.add(int(name[1:]))
    return [f"D{n}" for n in sorted(found) if 1 <= n <= 22]


# --- file references -------------------------------------------------------

_PY_PATH = re.compile(r"(?<![\w./-])((?:\.\./)*(?:[\w.-]+/)*[\w-]+\.py)\b")
_DOTTED = re.compile(r"\bglm_universal((?:\.[A-Za-z_]\w*)+)")
_SUBPKG_REF = re.compile(r"(?<![\w./-])([a-z_]+)/([a-z_][a-z0-9_]*)\b(?!\.)")
_BACKTICK_NAME = re.compile(r"`([a-z][a-z0-9]*_[a-z0-9_]+)`")
_LEAN_PATH = re.compile(r"(?<![\w./-])((?:[\w.-]+/)*[A-Z][\w]*\.lean)\b")
_LEAN_MODULE = re.compile(r"\bRequestProject\.GLM((?:\.[A-Z]\w*)+)")
_GLM_NAMESPACE = re.compile(r"(?<![\w.])GLM((?:\.[A-Z][A-Za-z0-9]*)+)")


def _package_path(raw: str) -> str:
    """A cited ``.py`` path, normalised to be relative to the package."""
    path = raw
    while path.startswith("../"):
        path = path[3:]
    for prefix in ("src/glm_universal/", "overlay/glm_universal/",
                   "glm_universal/", "src/", "overlay/"):
        if path.startswith(prefix):
            path = path[len(prefix):]
    return path


def _file_refs(text: str, t: Tree) -> Dict[str, List[str]]:
    code: Set[str] = set()
    tests: Set[str] = set()
    missing: Set[str] = set()
    for match in _PY_PATH.finditer(text):
        path = _package_path(match.group(1))
        name = path.rsplit("/", 1)[-1]
        if path.startswith("tests/") or (name.startswith("test_")
                                         and "/" not in path):
            if name in t.tests:
                tests.add(name)
            elif path.startswith("tests/") or name.startswith("test_"):
                missing.add("tests/" + name)
            continue
        if "/" not in path:
            hits = t.module_stems.get(name[:-3], [])
            if len(hits) == 1:
                code.add(hits[0])
            continue
        if path in t.modules:
            code.add(path)
        elif path.split("/", 1)[0] in t.subpackages and "/_" not in path:
            missing.add(path)
    for match in _DOTTED.finditer(text):
        parts = match.group(1).strip(".").split(".")
        hit = None
        exported = False
        for cut in range(len(parts), 0, -1):
            candidate = "/".join(parts[:cut]) + ".py"
            if candidate in t.modules:
                hit = candidate
                break
            init = "/".join(parts[:cut]) + "/__init__.py"
            if init in t.modules and cut < len(parts):
                #  ``glm_universal.wheels.provisional_status``: a name the
                #  package's ``__init__.py`` defines or re-exports resolves to
                #  the package (which, like every ``__init__.py``, is not
                #  listed as code); a name it does not hold is a missing
                #  module of that package.
                exported = parts[cut] in t.exports.get(init, ())
                break
        if hit is not None:
            if not hit.endswith("__init__.py"):
                code.add(hit)
        elif exported:
            pass
        elif parts and parts[0] in t.subpackages and len(parts) >= 2 \
                and parts[0] != "tests":
            missing.add(f"{parts[0]}/{parts[1]}.py")
        elif parts and parts[0] == "tests" and len(parts) >= 2:
            name = parts[1] + ".py"
            (tests if name in t.tests else missing).add(
                name if name in t.tests else "tests/" + name)
    for match in _SUBPKG_REF.finditer(text):
        pkg, name = match.group(1), match.group(2)
        if pkg in t.subpackages and f"{pkg}/{name}.py" in t.modules:
            code.add(f"{pkg}/{name}.py")
    for match in _BACKTICK_NAME.finditer(text):
        hits = t.module_stems.get(match.group(1), [])
        if len(hits) == 1:
            code.add(hits[0])
    # Lean
    lean: Set[str] = set()
    lean_missing: Set[str] = set()
    registry = t.registry_stems

    def lean_ref(stem_path: str, explicit_file: bool) -> None:
        while stem_path.startswith("../"):
            stem_path = stem_path[3:]
        for prefix in ("src/lean/", "glm_lean/", "awaiting_recovery/",
                       "RequestProject/GLM/", "RequestProject/", "GLM/"):
            if stem_path.startswith(prefix):
                stem_path = stem_path[len(prefix):]
        if stem_path in t.lean:
            lean.add(stem_path)
            return
        stem = stem_path.rsplit("/", 1)[-1]
        if "/" not in stem_path:
            hits = t.lean_stems.get(stem, [])
            if len(hits) == 1:
                lean.add(hits[0])
                return
        if stem in registry and (explicit_file or "/" not in stem_path):
            lean_missing.add(registry[stem])

    for match in _LEAN_PATH.finditer(text):
        lean_ref(match.group(1)[:-len(".lean")], True)
    for match in _LEAN_MODULE.finditer(text):
        parts = match.group(1).strip(".").split(".")
        for cut in range(len(parts), 0, -1):
            candidate = "/".join(parts[:cut])
            if candidate in t.lean:
                lean.add(candidate)
                break
        else:
            lean_ref(parts[0], False)
    for match in _GLM_NAMESPACE.finditer(text):
        parts = match.group(1).strip(".").split(".")
        for cut in range(len(parts), 0, -1):
            candidate = "/".join(parts[:cut])
            if candidate in t.lean:
                lean.add(candidate)
                break
        else:
            if parts[0] in registry:
                lean_missing.add(registry[parts[0]])
    held = sorted(x for x in lean if t.lean.get(x) == "held")
    return {
        "code": sorted(code),
        "test": sorted(tests),
        "lean": sorted(lean),
        "lean_held": held,
        "lean_missing": sorted(lean_missing),
        "missing": sorted(missing - {"tests/" + x for x in tests}),
    }


# --- phase, status, faculty --------------------------------------------------

_OWN_PHASE = (
    re.compile(r"(?i)pre-?registration (?:for|of) Phase (\d+)"),
    re.compile(r"(?i)\bthis (?:round|study|phase),? (?:is )?Phase (\d+)\b"),
)


def _phase(sid: str, title: str, body: str, t: Tree) -> int:
    head = body[:6000]
    for pattern in _OWN_PHASE:
        match = pattern.search(head)
        if match:
            return int(match.group(1))
    match = re.search(r"\(Phase (\d+)\)\s*$", title)
    if match:
        return int(match.group(1))
    named = sorted(n for n, r in t.phase_records.items() if sid in r.studies)
    if named:
        return named[0]
    votes = t.phase_votes.get(sid)
    if votes:
        best = max(votes.values())
        return min(n for n, v in votes.items() if v == best)
    return 0


_FACULTY_WORDS = (
    ("derivation", re.compile(r"(?i)\*?\bderiv(?:e|ation)\b\*?\s*(?:[:(]|moved|gained)")),
    ("addressing", re.compile(r"(?i)\*?\baddress(?:ing)?\b\*?\s*(?:[:(]|moved|gained)")),
    ("refusal", re.compile(r"(?i)\*?\brefus(?:e|al)\b\*?\s*(?:[:(]|moved|gained)")),
)


def _faculty_of(paragraph: str) -> str:
    if not paragraph.strip():
        return ""
    lowered = paragraph.lower()
    if "cleaned up" in lowered or re.search(
            r"none of derivation, addressing or refusal moved", lowered):
        return "maintenance"
    first: Tuple[int, str] = (len(paragraph) + 1, "")
    for name, pattern in _FACULTY_WORDS:
        match = pattern.search(paragraph)
        if match and match.start() < first[0]:
            first = (match.start(), name)
    return first[1]


def _faculty(body: str, phase: int, t: Tree) -> str:
    own = re.search(r"(?ms)\*\*Facult(?:y|ies)(?: \(D15\))?\.?\*\*(.*?)(?:\n\n|\Z)",
                    body)
    if own:
        found = _faculty_of(own.group(1))
        if found:
            return found
    record = t.phase_records.get(phase)
    if record is not None:
        found = _faculty_of(record.faculties)
        if found:
            return found
    return "unknown"


_OPEN_VERDICT = re.compile(r"^(?:not yet|pending|open\b|to be (?:measured|taken)|"
                           r"unmeasured|not measured)")


def _status(verdict: str, phase: int, t: Tree) -> str:
    """``negative`` when the verdict answers "No" (or "not reproduced");
    ``open`` when the phase record says open or the verdict says the answer
    is still to come; otherwise ``closed`` -- a tier-0 verdict is an
    answer."""
    plain = inv_normalise(verdict)
    if re.match(r"no\s*[.,;:—–-]", plain) or re.match(
            r"(?:the verdict:\s*)?not reproduced", plain):
        return "negative"
    record = t.phase_records.get(phase)
    if record is not None and record.status == "open":
        return "open"
    if _OPEN_VERDICT.match(plain):
        return "open"
    return "closed"


def inv_normalise(text: str) -> str:
    """Lower-case, emphasis and links removed (as ``checks.normalise``)."""
    without_links = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    without_emphasis = re.sub(r"[*_`]+", "", without_links)
    return re.sub(r"\s+", " ", without_emphasis).strip().lower()


# --- one document -------------------------------------------------------------

@dataclass
class Parsed:
    """What one ``.md`` says, before the graph is closed."""

    sid: str
    fields: Dict[str, Any]
    links: List[str]


def parse_document(path: Path, t: Optional[Tree] = None) -> Parsed:
    """Derive every per-document field of one study ``.md``."""
    t = t if t is not None else tree()
    rel = "studies/" + path.name
    text = path.read_text(encoding="utf-8")
    sections = inv._split_sections(rel, text)
    tier0, span = inv._parse_tier0(sections)
    if tier0 is None:
        raise ValueError(f"{rel} has no tier-0 block")
    title = path.stem
    for line in text.splitlines():
        match = re.match(r"^#\s+(.*\S)\s*$", line)
        if match:
            title = match.group(1)
            break
    lines = text.splitlines()
    body = "\n".join(lines[span[1]:]) if span[1] else text
    sid = path.stem
    marks = _marks(text, tier0.figure)
    phase = _phase(sid, title, body, t)
    links = [Path(x).stem for x in inv._links(text, rel)
             if x.startswith("studies/") and x.count("/") == 1]
    links = [x for x in dict.fromkeys(links) if x != sid and x in t.study_ids]
    #  The tier-0 footer names ``corpus.checks`` in every study; it is house
    #  style, not a citation, so it is left out of the file references.
    refs = _file_refs("\n".join(line for line in lines
                                if not line.startswith(inv.TIER0_FOOTER)), t)
    fields: Dict[str, Any] = {
        "schema": SCHEMA_NAME,
        "id": sid,
        "title": title,
        "phase": phase,
        "status": _status(tier0.verdict, phase, t),
        "question": tier0.question,
        "verdict": tier0.verdict,
        "deciding_figure": tier0.figure,
        "recomputed_by": tier0.recomputed,
        "last_altered": _last_altered(text),
        "faculty": _faculty(body, phase, t),
        "marks": marks,
        "directives": _directives(text, marks["declared"] + marks["amended"]),
        "sections": [{"heading": s.heading, "anchor": s.anchor}
                     for s in sections],
        "file_refs": dict(prose=path.name, **refs),
    }
    return Parsed(sid, fields, links)


def derive_all(t: Optional[Tree] = None) -> Dict[str, Dict[str, Any]]:
    """Every study's derived fields, with the link graph closed: the
    predecessors (linked, strictly earlier phase), the related studies (the
    other links) and the successors (the inverse)."""
    t = t if t is not None else tree()
    parsed = {p.stem: parse_document(p, t) for p in study_documents()}
    phases = {sid: p.fields["phase"] for sid, p in parsed.items()}
    successors: Dict[str, List[str]] = {sid: [] for sid in parsed}
    for sid, p in parsed.items():
        own = phases[sid]
        preds: List[str] = []
        related: List[str] = []
        for target in p.links:
            other = phases.get(target, 0)
            if own > 0 and other > 0 and other < own:
                preds.append(target)
            else:
                related.append(target)
        p.fields["predecessors"] = sorted(preds)
        p.fields["related"] = sorted(related)
        for target in preds:
            successors[target].append(sid)
    for sid, p in parsed.items():
        p.fields["successors"] = sorted(successors[sid])
    return {sid: p.fields for sid, p in parsed.items()}


# ===========================================================================
# Merging with what is written, drift, sync
# ===========================================================================

def _get(data: Mapping[str, Any], dotted: str) -> Tuple[bool, Any]:
    obj: Any = data
    for part in dotted.split("."):
        if not isinstance(obj, Mapping) or part not in obj:
            return False, None
        obj = obj[part]
    return True, obj


def _set(data: Dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    obj = data
    for part in parts[:-1]:
        nxt = obj.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            obj[part] = nxt
        obj = nxt
    obj[parts[-1]] = value


def merged_manifest(derived: Mapping[str, Any],
                    existing: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    """The manifest a study should have: the derived fields, the judgement
    fields as written (or their empty defaults), and any derived field named
    in ``hand_fields`` kept as written."""
    existing = existing or {}
    out: Dict[str, Any] = {}
    for dotted, default in KEPT_FIELDS.items():
        present, value = _get(existing, dotted)
        _set(out, dotted, json.loads(json.dumps(value if present else default)))
    hand = existing.get("hand_fields") if isinstance(
        existing.get("hand_fields"), list) else []
    for dotted in DERIVED_FIELDS:
        present, value = _get(derived, dotted)
        if dotted in hand or any(dotted.startswith(str(h) + ".")
                                 for h in hand):
            kept_present, kept = _get(existing, dotted)
            if kept_present:
                value, present = kept, True
        if present:
            _set(out, dotted, json.loads(json.dumps(value)))
    #  Unknown extra keys a person added are kept (the schema allows them).
    for key, value in existing.items():
        if key not in out:
            out[key] = value
    return out


def _render(data: Mapping[str, Any], stamp: str) -> str:
    return (_HEADER + f"# Last altered {stamp} (study_manifest --sync).\n\n"
            + _dump_yaml(data))


def _yaml_validate(data: Mapping[str, Any]) -> List[str]:
    from . import yaml as yml
    return yml.validate(data)


@dataclass
class Drift:
    """How the written manifests differ from the derived ones."""

    missing: List[str] = field(default_factory=list)     # .md without .yaml
    orphans: List[str] = field(default_factory=list)     # .yaml without study .md
    unreadable: List[str] = field(default_factory=list)
    drifted: Dict[str, List[str]] = field(default_factory=dict)  # id -> fields
    invalid: Dict[str, List[str]] = field(default_factory=dict)  # id -> errors
    expected: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @property
    def holds(self) -> bool:
        return not (self.missing or self.orphans or self.unreadable
                    or self.drifted or self.invalid)


def _differences(a: Any, b: Any, prefix: str = "") -> List[str]:
    if isinstance(a, Mapping) and isinstance(b, Mapping):
        out: List[str] = []
        for key in sorted(set(a) | set(b), key=str):
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in a or key not in b:
                out.append(path)
            else:
                out.extend(_differences(a[key], b[key], path))
        return out
    return [] if a == b else [prefix or "<root>"]


def drift(t: Optional[Tree] = None) -> Drift:
    """Compare every written manifest with the one :func:`merged_manifest`
    would write.  Reads only."""
    t = t if t is not None else tree()
    derived = derive_all(t)
    report = Drift()
    written: Dict[str, Dict[str, Any]] = {}
    for path in manifest_paths():
        try:
            data = _load_yaml(path.read_text(encoding="utf-8"))
        except Exception:
            report.unreadable.append(path.name)
            continue
        if not isinstance(data, dict):
            report.unreadable.append(path.name)
            continue
        written[path.stem] = data
        if path.stem not in derived:
            report.orphans.append(path.name)
    for sid, fields in sorted(derived.items()):
        existing = written.get(sid)
        expected = merged_manifest(fields, existing)
        report.expected[sid] = expected
        if existing is None:
            report.missing.append(sid)
            continue
        diffs = _differences(existing, expected)
        if diffs:
            report.drifted[sid] = diffs
        errors = _yaml_validate(existing)
        if errors:
            report.invalid[sid] = errors
    return report


def sync(write: bool = True, stamp: Optional[str] = None) -> Dict[str, Any]:
    """Write every manifest whose data differs from the derived one (and
    create the missing ones).  Unchanged files are not touched.  Refuses to
    write a manifest that would not validate."""
    t = tree(refresh=True)
    report = drift(t)
    stamp = stamp or _today_stamp()
    written: List[str] = []
    refused: Dict[str, List[str]] = {}
    for sid in sorted(set(report.missing) | set(report.drifted)
                      | set(report.invalid)):
        expected = report.expected[sid]
        errors = _yaml_validate(expected)
        if errors:
            refused[sid] = errors
            continue
        if write:
            (C.STUDIES_DIR / f"{sid}.yaml").write_text(
                _render(expected, stamp), encoding="utf-8")
        written.append(sid)
    return {"written" if write else "would_write": written,
            "refused": refused, "orphans": report.orphans,
            "unreadable": report.unreadable}


def manifest_report() -> Dict[str, Any]:
    """The gate check: every study ``.md`` has a manifest, every manifest
    validates against the schema and has not drifted from its ``.md``."""
    report = drift()
    return {
        "studies": len(report.expected),
        "missing": list(report.missing),
        "orphans": list(report.orphans),
        "unreadable": list(report.unreadable),
        "drifted": {k: v[:8] for k, v in report.drifted.items()},
        "invalid": dict(report.invalid),
        "holds": report.holds,
    }


def defect_counts(manifests: Optional[Mapping[str, Mapping[str, Any]]] = None
                  ) -> Dict[str, int]:
    """The file-reference defects of the written manifests: references that
    do not name an existing file of their kind."""
    manifests = manifests if manifests is not None else load_manifests()
    package = C.PACKAGE_ROOT
    counts = {"manifests": len(manifests), "code_refs": 0, "code_broken": 0,
              "test_refs": 0, "test_missing": 0,
              "manifests_with_missing_test": 0, "lean_refs": 0,
              "lean_unresolved": 0, "lean_held": 0}
    for data in manifests.values():
        refs = data.get("file_refs") or {}
        for ref in refs.get("code") or []:
            counts["code_refs"] += 1
            if not (package / ref).is_file() or not ref.endswith(".py"):
                counts["code_broken"] += 1
        bad = False
        for ref in refs.get("test") or []:
            counts["test_refs"] += 1
            if not (package / "tests" / ref).is_file():
                counts["test_missing"] += 1
                bad = True
        counts["manifests_with_missing_test"] += int(bad)
        for ref in refs.get("lean") or []:
            counts["lean_refs"] += 1
            path = C.lean_file(ref)
            if not path.is_file():
                counts["lean_unresolved"] += 1
            elif C.LEAN_HOLDING_DIR in path.parents:
                counts["lean_held"] += 1
    return counts


# ===========================================================================
# Command line
# ===========================================================================

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m glm_universal.corpus.study_manifest",
        description="Derive the study manifests from their .md and the tree.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true",
                       help="fail (exit 1) if any manifest is missing, "
                            "drifted, orphaned or schema-invalid")
    group.add_argument("--sync", action="store_true",
                       help="rewrite the manifests whose data moved")
    group.add_argument("--defects", action="store_true",
                       help="count the file-reference defects as written")
    group.add_argument("--show", metavar="ID",
                       help="print the manifest one study should have")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.sync:
        outcome = sync(write=True)
        if args.json:
            print(json.dumps(outcome, indent=1, sort_keys=True))
        else:
            print(f"wrote {len(outcome['written'])} manifest(s)")
            for sid in outcome["written"]:
                print(f"  {sid}.yaml")
            for sid, errors in outcome["refused"].items():
                print(f"  refused {sid}: {errors[:3]}")
            for name in outcome["orphans"]:
                print(f"  orphan (no study .md): {name}")
            for name in outcome["unreadable"]:
                print(f"  unreadable: {name}")
        return 0 if not outcome["refused"] else 1
    if args.defects:
        counts = defect_counts()
        print(json.dumps(counts, indent=1, sort_keys=True))
        return 0
    if args.show:
        report = drift()
        expected = report.expected.get(args.show)
        if expected is None:
            print(f"no study document {args.show}")
            return 1
        print(_dump_yaml(expected), end="")
        return 0
    report = drift()
    if args.json:
        print(json.dumps(manifest_report(), indent=1, sort_keys=True))
    else:
        print(f"{len(report.expected)} study documents, "
              f"{len(report.expected) - len(report.missing)} manifests")
        for sid in report.missing:
            print(f"  missing manifest: {sid}.yaml")
        for name in report.orphans:
            print(f"  orphan manifest (no study .md): {name}")
        for name in report.unreadable:
            print(f"  unreadable manifest: {name}")
        for sid, fields in sorted(report.drifted.items()):
            print(f"  drifted: {sid}: {', '.join(fields[:6])}"
                  + (" ..." if len(fields) > 6 else ""))
        for sid, errors in sorted(report.invalid.items()):
            print(f"  schema-invalid: {sid}: {errors[:3]}")
        print("current" if report.holds else "run --sync")
    return 0 if report.holds else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

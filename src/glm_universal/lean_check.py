"""``glm_universal.lean_check`` -- the Lean tree, checked without building it.

*Created 30 October 2026 (repository check; last altered 31 October 2026:
:func:`recorded_unavailable`; the record of a passing build,
:func:`write_build_evidence` and :func:`verification_problems`, which the
intake's Lean-verified gate reads).*  ``lake build`` is the real
check of the Lean development, and it needs Lean, Mathlib and a ``.lake``
folder.  This module answers the questions that can be answered from the
text alone, in a second, so that a broken tree is caught before a
forty-minute build is started (directive D16, the cheapest gate that could
fail):

1. **every import resolves** -- each ``RequestProject.*`` import names a file
   under ``src/lean/`` (``Mathlib``, ``Lean``, ``Std``, ``Init`` and ``Aesop``
   are external and are not checked);
2. **the module system is respected** -- a file that starts with ``module``
   imports only files that also start with ``module``, and ``public import``
   appears only in such files;
3. **no import cycle**;
4. **no ``sorry`` and no hand-written ``axiom``** outside comments;
5. **the whole-development audit names every file** --
   ``AxiomAuditAll.lean`` imports each Lean file of ``RequestProject`` (the
   audit's ``#guard_axioms_development`` only covers what it imports);
6. **no placeholder** -- a file with no declaration at all is reported (the
   twelve placeholders of the reorganisation were such files);
7. **no likely name clash** -- two files that declare the same fully
   qualified name cannot both be imported by the audit.  The scan follows
   ``namespace``/``section``/``end`` and skips ``private`` declarations, so it
   is an approximation; ``lake build`` is the authority.

Files held back from the build live in ``src/lean/awaiting_recovery/``
(outside the ``RequestProject`` glob of ``lakefile.toml``); they are listed,
with the missing file each waits for, but not checked.

Run::

    PYTHONPATH=src python3 -m glm_universal.lean_check            # report
    PYTHONPATH=src python3 -m glm_universal.lean_check --json     # machine-readable
    PYTHONPATH=src python3 -m glm_universal.lean_check --write-audit
        # rewrite the import list of AxiomAuditAll.lean from the tree

``scripts/rebuild_lean.sh`` ends by calling ``--write-build-evidence`` with
the exit codes of its static check, ``lake build`` and ``sorry`` scan; when
all three are 0 it writes ``scripts/logs/lean_build_evidence.json``, the
SHA-256 of every Lean file that was built and of the toolchain and Mathlib
pins.  A file is *verified* while it and every file it imports still match
that record (:func:`verification_problems`); the static check alone never
makes a file verified.

The exit status is 0 exactly when there is no error (warnings do not fail).
Every path comes from :mod:`glm_universal.constants` (directive D21).
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .constants import (
    LEAN_AUDIT_FILE,
    LEAN_BUILD_EVIDENCE,
    LEAN_BUILD_PINS,
    LEAN_EXTERNAL_PREFIXES,
    LEAN_HOLDING_DIR,
    LEAN_LIBRARY,
    LEAN_SOURCE_DIR,
    REPOSITORY_ROOT,
)

__all__ = [
    "LeanFile",
    "scan_tree",
    "check_tree",
    "audit_imports_text",
    "audited_or_held",
    "file_hashes",
    "import_closure",
    "write_build_evidence",
    "load_build_evidence",
    "verification_problems",
    "main",
]

_IMPORT = re.compile(r"^((?:public\s+|meta\s+|private\s+)*)import\s+(?:all\s+)?(\S+)", re.M)
_DECL = re.compile(
    r"^(?:@\[[^\]]*\]\s*)*"
    r"(?P<mods>(?:(?:private|protected|noncomputable|partial|unsafe|nonrec|public|scoped)\s+)*)"
    r"(?P<kind>theorem|lemma|def|abbrev|instance|structure|inductive|class|opaque|axiom)\s+"
    r"(?P<name>[^\s:({\[]+)?",
    re.M,
)
_NS = re.compile(r"^\s*(namespace|section|end|noncomputable section)\b\s*(\S*)", re.M)


def _strip_comments(text: str) -> str:
    """Remove ``--`` line comments and (nested) ``/- ... -/`` block comments,
    keeping line structure, and blank out string literals."""
    out = []
    i, n, depth = 0, len(text), 0
    in_str = False
    while i < n:
        c = text[i]
        if depth == 0 and not in_str and c == '"':
            in_str = True
            out.append(" ")
            i += 1
            continue
        if in_str:
            if c == "\\" and i + 1 < n:
                out.append("  ")
                i += 2
                continue
            if c == '"':
                in_str = False
            out.append("\n" if c == "\n" else " ")
            i += 1
            continue
        if text.startswith("/-", i):
            depth += 1
            out.append("  ")
            i += 2
            continue
        if depth and text.startswith("-/", i):
            depth -= 1
            out.append("  ")
            i += 2
            continue
        if depth:
            out.append("\n" if c == "\n" else " ")
            i += 1
            continue
        if text.startswith("--", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


@dataclass
class LeanFile:
    path: Path
    module: str
    is_module: bool
    imports: List[Tuple[str, bool]]          # (name, public?)
    declarations: List[str]                    # fully qualified, non-private
    sorry_lines: List[int]
    axiom_lines: List[int]
    n_declarations: int


def module_name(path: Path, root: Path = LEAN_SOURCE_DIR) -> str:
    return ".".join(path.relative_to(root).with_suffix("").parts)


def parse_file(path: Path, root: Path = LEAN_SOURCE_DIR) -> LeanFile:
    raw = path.read_text(encoding="utf-8", errors="replace")
    code = _strip_comments(raw)
    first = next((ln.strip() for ln in code.splitlines() if ln.strip()), "")
    is_module = first == "module"
    imports = [(m.group(2), bool(m.group(1) and "public" in m.group(1)))
               for m in _IMPORT.finditer(code)]
    # declarations with namespace tracking
    decls: List[str] = []
    n_decl = 0
    stack: List[Tuple[str, str]] = []  # (kind, name)
    events = []
    for m in _NS.finditer(code):
        events.append((m.start(), "ns", m.group(1), m.group(2)))
    for m in _DECL.finditer(code):
        events.append((m.start(), "decl", m))
    events.sort(key=lambda e: e[0])
    for ev in events:
        if ev[1] == "ns":
            kind, name = ev[2], ev[3]
            if kind == "namespace":
                stack.append(("namespace", name))
            elif kind in ("section", "noncomputable section"):
                stack.append(("section", name))
            elif kind == "end":
                if stack:
                    stack.pop()
            continue
        m = ev[2]
        n_decl += 1
        mods = m.group("mods") or ""
        name = m.group("name")
        if "private" in mods or not name or m.group("kind") == "instance":
            continue
        if name.startswith("_root_."):
            fq = name[len("_root_."):]
        else:
            ns = ".".join(s[1] for s in stack if s[0] == "namespace" and s[1])
            fq = f"{ns}.{name}" if ns else name
        decls.append(fq)
    lines = code.splitlines()
    sorry_lines = [i + 1 for i, ln in enumerate(lines) if re.search(r"\bsorry\b", ln)]
    axiom_lines = [i + 1 for i, ln in enumerate(lines) if re.match(r"\s*(private\s+)?axiom\s", ln)]
    return LeanFile(path, module_name(path, root), is_module, imports, decls,
                    sorry_lines, axiom_lines, n_decl)


def scan_tree(root: Path = LEAN_SOURCE_DIR, library: str = LEAN_LIBRARY) -> Dict[str, LeanFile]:
    files = {}
    for p in sorted((root / library).rglob("*.lean")):
        lf = parse_file(p, root)
        files[lf.module] = lf
    return files


def _external(name: str) -> bool:
    return name.split(".")[0] in LEAN_EXTERNAL_PREFIXES


@dataclass
class Report:
    files: int = 0
    module_files: int = 0
    declarations: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    held: List[Dict[str, object]] = field(default_factory=list)

    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> Dict[str, object]:
        return {
            "files": self.files, "module_files": self.module_files,
            "declarations": self.declarations, "errors": self.errors,
            "warnings": self.warnings, "held": self.held, "ok": self.ok(),
        }


def _cycles(files: Dict[str, LeanFile]) -> List[List[str]]:
    graph = {m: [i for i, _ in f.imports if i in files] for m, f in files.items()}
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {m: WHITE for m in graph}
    found: List[List[str]] = []
    sys.setrecursionlimit(max(10000, sys.getrecursionlimit()))

    def visit(m: str, path: List[str]) -> None:
        colour[m] = GREY
        path.append(m)
        for n in graph[m]:
            if colour[n] == GREY:
                found.append(path[path.index(n):] + [n])
            elif colour[n] == WHITE:
                visit(n, path)
        path.pop()
        colour[m] = BLACK

    for m in graph:
        if colour[m] == WHITE:
            visit(m, [])
    return found


def held_files(holding: Path = LEAN_HOLDING_DIR, root: Path = LEAN_SOURCE_DIR) -> List[Dict[str, object]]:
    """The files held back from the build, each with the imports it lacks."""
    out = []
    if not holding.is_dir():
        return out
    for p in sorted(holding.rglob("*.lean")):
        lf = parse_file(p, holding)
        lacking = []
        for name, _ in lf.imports:
            if _external(name):
                continue
            target = root / Path(*name.split(".")).with_suffix(".lean")
            held = holding / Path(*name.split(".")).with_suffix(".lean")
            if target.exists():
                if _is_placeholder(target):
                    lacking.append(name + " (placeholder)")
            elif held.exists():
                lacking.append(name + " (itself held)")
            else:
                lacking.append(name)
        out.append({"file": str(p.relative_to(holding)), "module": lf.module,
                    "lacks": lacking})
    return out


def _is_placeholder(path: Path) -> bool:
    return parse_file(path).n_declarations == 0


def check_tree(root: Path = LEAN_SOURCE_DIR, library: str = LEAN_LIBRARY,
               audit: Path = LEAN_AUDIT_FILE) -> Report:
    files = scan_tree(root, library)
    rep = Report(files=len(files),
                 module_files=sum(f.is_module for f in files.values()),
                 declarations=sum(f.n_declarations for f in files.values()))
    for m, f in files.items():
        rel = f.path.relative_to(root)
        for name, public in f.imports:
            if _external(name):
                continue
            if name not in files:
                rep.errors.append(f"{rel}: imports {name}, which is not a file of the tree")
                continue
            if f.is_module and not files[name].is_module:
                rep.errors.append(f"{rel}: a `module` file imports the non-module file {name}")
            if public and not f.is_module:
                rep.errors.append(f"{rel}: `public import` in a file that is not a `module`")
        for ln in f.sorry_lines:
            rep.errors.append(f"{rel}:{ln}: `sorry`")
        for ln in f.axiom_lines:
            rep.errors.append(f"{rel}:{ln}: hand-written `axiom`")
        if f.n_declarations == 0 and m != module_name(audit, root):
            # an import-only aggregator (e.g. Rule30.lean) is fine; a file with
            # neither declarations nor imports is a placeholder
            if not f.imports:
                rep.errors.append(f"{rel}: placeholder (no declaration and no import)")
    for cyc in _cycles(files):
        rep.errors.append("import cycle: " + " -> ".join(cyc))
    # the audit
    audit_mod = module_name(audit, root)
    if audit_mod not in files:
        rep.errors.append(f"{audit.relative_to(root)} is missing")
    else:
        imported = {n for n, _ in files[audit_mod].imports}
        missing = sorted(set(files) - imported - {audit_mod})
        for m in missing:
            rep.errors.append(f"{audit.relative_to(root)} does not import {m} "
                              "(run `python3 -m glm_universal.lean_check --write-audit`)")
    # likely clashes
    owner: Dict[str, str] = {}
    for m, f in files.items():
        for d in f.declarations:
            if d in owner and owner[d] != m:
                rep.warnings.append(f"declaration {d} in both {owner[d]} and {m}")
            else:
                owner[d] = m
    rep.held = held_files(root=root)
    return rep


def audited_or_held(module: str) -> bool:
    """Whether a Lean module is in one of the two accepted states.

    *Audited*: the file is in the build tree and ``AxiomAuditAll.lean``
    imports it, so ``lake build`` checks its axioms.  *Held*: the file is in
    ``src/lean/awaiting_recovery/`` and each project file it waits for is
    either missing from the tree and named in ``studies/_lean_files_needed.md``,
    or itself held.  Any other state -- a file in the tree the audit misses, a
    held file waiting for nothing, a missing file nobody has recorded -- is a
    defect.  ``module`` is ``RequestProject.GLM.X`` or a file name ``X.lean``.
    """
    from .constants import LEAN_FILES_NEEDED
    if module.endswith(".lean"):
        module = f"{LEAN_LIBRARY}.GLM." + module[:-5].replace("/", ".")
    rel = Path(*module.split(".")).with_suffix(".lean")
    built = LEAN_SOURCE_DIR / rel
    if built.is_file():
        audit = {n for n, _ in parse_file(LEAN_AUDIT_FILE).imports}
        return module in audit
    held = LEAN_HOLDING_DIR / rel
    if not held.is_file():
        return False
    registry = LEAN_FILES_NEEDED.read_text(encoding="utf-8") if LEAN_FILES_NEEDED.is_file() else ""
    for h in held_files():
        if h["module"] == module:
            waits = h["lacks"]
            if not waits:
                return False
            for w in waits:
                name = w.split(" ")[0]
                if "(itself held)" in w:
                    if not audited_or_held(name):
                        return False
                elif f"`{name.split('.')[-1]}.lean`" not in registry:
                    return False
            return True
    return False


def recorded_unavailable(name: str) -> bool:
    """Whether a Lean file is out of the build for a recorded reason.

    ``name`` is a path ending ``.lean`` (``RequestProject/GLM/X.lean`` or
    ``X.lean``) or a module (``RequestProject.GLM.X``).  True when the file
    is not in the build tree and is either named in
    ``studies/_lean_files_needed.md`` as missing, or held in
    ``src/lean/awaiting_recovery/`` in the accepted state of
    :func:`audited_or_held`.  A test whose Lean mark reads such a file
    accepts the mark unmet while this holds, and expects it met the day the
    file is back (31 October 2026, repository check).
    """
    from .constants import LEAN_FILES_NEEDED
    if name.endswith(".lean"):
        tail = name[:-5]
        if tail.startswith(f"{LEAN_LIBRARY}/"):
            tail = tail[len(LEAN_LIBRARY) + 1:]
        if tail.startswith("GLM/"):
            tail = tail[4:]
        module = f"{LEAN_LIBRARY}.GLM." + tail.replace("/", ".")
    else:
        module = name
    rel = Path(*module.split(".")).with_suffix(".lean")
    if (LEAN_SOURCE_DIR / rel).is_file():
        return False
    if (LEAN_HOLDING_DIR / rel).is_file():
        return audited_or_held(module)
    registry = (LEAN_FILES_NEEDED.read_text(encoding="utf-8")
                if LEAN_FILES_NEEDED.is_file() else "")
    return f"`{rel.name}`" in registry


def audit_imports_text(root: Path = LEAN_SOURCE_DIR, library: str = LEAN_LIBRARY,
                       audit: Path = LEAN_AUDIT_FILE) -> str:
    """The audit file with its import block regenerated from the tree.

    The guard (``AxiomGuard``) is imported first, then every other file in
    sorted order; everything after the import block is kept as it is."""
    files = scan_tree(root, library)
    audit_mod = module_name(audit, root)
    guard = f"{library}.GLM.AxiomGuard"
    names = sorted(m for m in files if m not in (audit_mod, guard))
    head = [f"import {guard}"] if guard in files else []
    head += [f"import {m}" for m in names]
    text = audit.read_text(encoding="utf-8")
    lines = text.splitlines()
    k = 0
    while k < len(lines) and (lines[k].startswith("import ") or not lines[k].strip()):
        k += 1
    rest = "\n".join(lines[k:])
    return "\n".join(head) + "\n\n" + rest + ("\n" if not rest.endswith("\n") else "")


# ---------------------------------------------------------------------------
# The record of a passing build (the intake's Lean-verified gate reads it)
# ---------------------------------------------------------------------------

EVIDENCE_SCHEMA = "glm-lean-build-evidence/v1"


def _sha256(path: Path) -> str:
    # The digest layer (D3: a digest is for integrity only -- here, whether a
    # Lean file is byte for byte the file a build verified).
    from .integrity import file_digest
    return file_digest(path)


def file_hashes(root: Path = LEAN_SOURCE_DIR, library: str = LEAN_LIBRARY) -> Dict[str, str]:
    """The SHA-256 of every Lean file of the library, keyed by module name
    (the library's own root file ``<library>.lean`` included when present)."""
    out = {module_name(p, root): _sha256(p)
           for p in sorted((root / library).rglob("*.lean"))}
    top = root / f"{library}.lean"
    if top.is_file():
        out[library] = _sha256(top)
    return out


def pin_hashes(repo_root: Path = REPOSITORY_ROOT) -> Dict[str, str]:
    """The SHA-256 of the toolchain and Mathlib pins (``""`` when absent)."""
    return {name: (_sha256(repo_root / name) if (repo_root / name).is_file() else "")
            for name in LEAN_BUILD_PINS}


def import_closure(modules, files: Dict[str, "LeanFile"]) -> List[str]:
    """``modules`` and every module of the development they import,
    transitively (external imports such as ``Mathlib`` are not followed; they
    are pinned by :data:`LEAN_BUILD_PINS`)."""
    seen: Set[str] = set()
    stack = [m for m in modules]
    while stack:
        m = stack.pop()
        if m in seen:
            continue
        seen.add(m)
        lf = files.get(m)
        if lf is None:
            continue
        stack.extend(name for name, _ in lf.imports
                     if not _external(name) and name not in seen)
    return sorted(seen)


def write_build_evidence(*, static_exit: int, build_exit: int, sorry_exit: int,
                         log: str = "", root: Path = LEAN_SOURCE_DIR,
                         library: str = LEAN_LIBRARY, audit: Path = LEAN_AUDIT_FILE,
                         repo_root: Path = REPOSITORY_ROOT,
                         out: Path = LEAN_BUILD_EVIDENCE,
                         now: Optional[datetime.datetime] = None) -> Tuple[bool, str]:
    """Record a passing build: written only when the static check, ``lake
    build`` (which elaborates ``AxiomAuditAll.lean``, whose guard fails on
    ``sorry`` or a non-standard axiom) and the ``sorry`` scan all exited 0.
    A failing run leaves any earlier record as it was: the files that record
    names still built then, and every file changed since no longer matches it.
    """
    exits = {"static": static_exit, "build": build_exit, "sorry": sorry_exit}
    failed = [k for k, v in exits.items() if v != 0]
    if failed:
        return False, ("not written: " + ", ".join(f"{k} exit {exits[k]}" for k in failed))
    when = now or datetime.datetime.now()
    audited = sorted(set(_IMPORT_NAMES.findall(_strip_comments(
        audit.read_text(encoding="utf-8"))))) if audit.is_file() else []
    hashes = file_hashes(root, library)
    data = {
        "schema": EVIDENCE_SCHEMA,
        "result": "pass",
        "date": f"{when.day} {when:%B %Y}",
        "timestamp": when.isoformat(timespec="seconds"),
        "log": log,
        "checks": exits,
        "pins": pin_hashes(repo_root),
        "audit_file": module_name(audit, root) if audit.is_file() else "",
        "audited": audited,
        "files": hashes,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return True, f"written: {len(hashes)} Lean files, {len(audited)} imported by the audit"


def load_build_evidence(path: Path = LEAN_BUILD_EVIDENCE) -> Optional[Dict[str, object]]:
    """The record of the last passing build, or ``None`` (absent or unreadable)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def verification_problems(modules, *, evidence: Optional[Dict[str, object]] = None,
                          evidence_path: Path = LEAN_BUILD_EVIDENCE,
                          root: Path = LEAN_SOURCE_DIR, library: str = LEAN_LIBRARY,
                          repo_root: Path = REPOSITORY_ROOT) -> List[str]:
    """Why ``modules`` are not verified by the current build record (``[]``
    when they are): the record must be a passing build, the toolchain and
    Mathlib pins unchanged, each module imported by the audit in that build,
    and each module *and every module it imports* byte for byte the file
    that was built."""
    ev = evidence if evidence is not None else load_build_evidence(evidence_path)
    try:
        where = str(evidence_path.relative_to(repo_root))
    except ValueError:
        where = str(evidence_path)
    if ev is None:
        return [f"no record of a passing Lean build ({where}); run scripts/rebuild_lean.sh"]
    if ev.get("schema") != EVIDENCE_SCHEMA or ev.get("result") != "pass":
        return [f"{where} is not the record of a passing build"]
    date = ev.get("date", "an undated build")
    problems: List[str] = []
    pins = ev.get("pins") or {}
    for name, digest in pin_hashes(repo_root).items():
        if pins.get(name) != digest:
            problems.append(f"{name} changed since the build of {date}")
    files = scan_tree(root, library)
    audited = set(ev.get("audited") or [])
    built = ev.get("files") or {}
    current = file_hashes(root, library)
    for m in modules:
        if m not in files:
            problems.append(f"{m} is not in the build tree")
        elif m not in audited:
            problems.append(f"{m} was not imported by the audit in the build of {date}")
    for m in import_closure(modules, files):
        if m not in current:
            continue
        if m not in built:
            problems.append(f"{m} was not part of the build of {date}")
        elif built[m] != current[m]:
            problems.append(f"{m} changed since the build of {date}")
    return problems


_IMPORT_NAMES = re.compile(r"^\s*(?:public\s+)?import\s+(\S+)", re.M)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m glm_universal.lean_check",
                                 description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("--write-audit", action="store_true",
                    help="rewrite the import list of AxiomAuditAll.lean from the tree")
    ap.add_argument("--write-build-evidence", action="store_true",
                    help="record a passing build (scripts/rebuild_lean.sh calls this "
                         "with the exit codes of its steps; nothing is written unless "
                         "all three are 0)")
    ap.add_argument("--static-exit", type=int, default=1)
    ap.add_argument("--build-exit", type=int, default=1)
    ap.add_argument("--sorry-exit", type=int, default=1)
    ap.add_argument("--log", default="")
    args = ap.parse_args(argv)
    if args.write_build_evidence:
        ok, detail = write_build_evidence(static_exit=args.static_exit,
                                          build_exit=args.build_exit,
                                          sorry_exit=args.sorry_exit, log=args.log)
        print(f"build record {LEAN_BUILD_EVIDENCE.name}: {detail}")
        return 0 if ok else 1
    if args.write_audit:
        LEAN_AUDIT_FILE.write_text(audit_imports_text(), encoding="utf-8")
    rep = check_tree()
    if args.json:
        print(json.dumps(rep.as_dict(), indent=2))
    else:
        print(f"Lean tree {LEAN_SOURCE_DIR}: {rep.files} files "
              f"({rep.module_files} `module` files), {rep.declarations} declarations")
        for e in rep.errors:
            print("  ERROR  ", e)
        for w in rep.warnings:
            print("  warning", w)
        if rep.held:
            print(f"  {len(rep.held)} file(s) held back in {LEAN_HOLDING_DIR.name}/:")
            for h in rep.held:
                print(f"    {h['file']}: waits for {', '.join(h['lacks']) or 'nothing (can return)'}")
        print("OK" if rep.ok() else f"{len(rep.errors)} error(s)")
    return 0 if rep.ok() else 1


if __name__ == "__main__":
    sys.exit(main())

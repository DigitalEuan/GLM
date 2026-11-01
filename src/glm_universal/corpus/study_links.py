"""``glm_universal.corpus.study_links`` -- the links of the study documents
(and, with ``--scope all``, of every written document), checked against the
tree and repointed when the file they name has moved.

The October 2026 reorganisation moved three things the documents link to: the
package went from ``glm_universal/`` to ``src/glm_universal/``, the Lean
development from ``glm_lean/`` to ``src/lean/`` (with files whose imports are
missing held in ``src/lean/awaiting_recovery/``), and the supplied material
from a flat ``source_material/`` into ``source_material/ToDo/`` (not yet taken
in) and ``source_material/done/`` (taken in).  A link written before the move
names a file that no longer exists there.  ``corpus --check`` counts a broken
link to a document as a failure of the coverage claim, and the study manifest
reads the links to find what a study cites, so a stale link is a wiring fault
twice over.

**Scope.**  ``studies`` (the default): every ``studies/*.md``.  ``all``:
every written document the corpus inventory knows
(:func:`glm_universal.corpus.inventory.document_paths` -- the top-level
documents, ``archive/``, ``studies/``, the package READMEs, the Lean-tree
READMEs), less the generated ones (:data:`glm_universal.corpus.render.GENERATED`,
which their generator rewrites).

The repair is deterministic and conservative.  A link is repointed only when
one rule below names a file (or folder) that exists, and the new target is
written relative to the document, with its ``#fragment`` and its ``%20``
spelling kept:

* ``glm_universal/<rest>`` -> :data:`constants.PACKAGE_ROOT` ``/<rest>``;
* ``glm_lean/<rest>`` -> :data:`constants.LEAN_ROOT` ``/<rest>``, else, for a
  Lean file, :func:`constants.lean_file` (which finds a held file);
* ``source_material/[done/|ToDo/]<rest>`` ->
  :func:`constants.source_material_item` ``(<rest>)`` (so a link follows an
  item when the intake re-files it from ``ToDo/`` to ``done/``);
* a document under ``src/`` whose link climbs to ``src/<rest>`` that is not
  there (one ``../`` short: the package and the Lean tree moved one level
  down, so the link was written one level higher) -> the repository root's
  ``<rest>`` when it exists (the package READMEs' ``../../README.md`` and
  ``../FIGURES.md``), else the three moves above applied to ``<rest>`` (a
  package README's ``../../glm_lean/...`` link);
* a document that is a copied README of a supplied package
  (:data:`PACKAGE_DOCUMENTS`, which also says where in the package the
  document sat) links relative to that package: a link into
  ``RequestProject/`` goes to the Lean tree and any other link to the package
  wherever it is filed; a link to a package folder's ``README.md`` that was
  not supplied goes to the folder itself.

A link to a package file recorded as never supplied (:data:`NOT_SUPPLIED`:
the package README names it, the supplied package does not hold it) cannot
be repointed; ``--fix`` keeps the link's text and drops the link
(``[`MERGE_INTO_GLM.md`](MERGE_INTO_GLM.md)`` becomes
```MERGE_INTO_GLM.md```), which is what a person would do.

Two kinds of absence are recorded rather than broken, and a link to them is
pointed at the place the record gives and then counted apart
(``recorded_absent``), not as broken:

* a Lean file listed in the *Missing files* table of
  :data:`constants.LEAN_FILES_NEEDED` (lost in the reorganisation, awaiting
  recovery) -- the link goes to its build-tree path, where it belongs;
* a supplied item the intake ledger (:data:`constants.INTAKE_LEDGER`) marks
  ``local_only`` (a ``*.pdf`` or ``*.zip`` kept on the owner's machine, out
  of version control) -- the link goes to the ledger's ``path``.

Anything else is left alone and reported (``unresolved``): the file is not in
the tree, and only a person can say whether to restore it or reword the
sentence.  Nothing here edits a document unless asked (``--fix``), and the
fix only replaces link targets (or, for a never-supplied file, drops the
link around its text): no date line is written for the author (D17 asks the
person or round that alters a document to stamp it).

Command line::

    python3 -m glm_universal.corpus.study_links                    # studies; exit 1 if any broken
    python3 -m glm_universal.corpus.study_links --fix              # repoint what the rules resolve
    python3 -m glm_universal.corpus.study_links --scope all        # every written document
    python3 -m glm_universal.corpus.study_links --scope all --fix
    python3 -m glm_universal.corpus.study_links --json

*Created 31 October 2026 (repository check of the YAML study system).  Last
altered 31 October 2026 (repository check): ``--scope all``, the rule for
documents under ``src/`` that climb one level short of the repository root,
package documents placed inside their package, and links to never-supplied
package files dropped by ``--fix``.*
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import quote, unquote

from .. import constants as C

__all__ = [
    "PACKAGE_DOCUMENTS",
    "NOT_SUPPLIED",
    "SCOPES",
    "Link",
    "study_documents",
    "scope_documents",
    "document_links",
    "repair_target",
    "broken_links",
    "links_report",
    "rewrite_text",
    "fix_links",
    "main",
]

#: A markdown link's target alone.
_LINK = re.compile(r"\]\(([^)\s]+)\)")

#: Written documents that are copied READMEs of a supplied package, with the
#: package and the folder of the package the document sat in: their relative
#: links were written against that place.  ``studies/RULE30_STUDY.md`` says
#: itself that it is "the one document to read first" of ``Rule30_GLM_Study``;
#: ``src/lean/RequestProject/GLM/Rule30/README.md`` is that package's
#: ``RequestProject/GLM/Rule30/README.md``.
PACKAGE_DOCUMENTS: Dict[str, Tuple[str, str]] = {
    "studies/RULE30_STUDY.md": ("Rule30_GLM_Study", ""),
    "src/lean/RequestProject/GLM/Rule30/README.md":
        ("Rule30_GLM_Study", "RequestProject/GLM/Rule30"),
}

#: Package files the package's own documents name but the supplied package
#: does not hold (package-relative paths).  Checked by hand on 31 October
#: 2026 against ``source_material/ToDo/Rule30_GLM_Study/`` and the Lean tree.
NOT_SUPPLIED: Dict[str, Tuple[str, ...]] = {
    "Rule30_GLM_Study": (
        "MERGE_INTO_GLM.md",
        "tools/STUDY_YAML.md",
        "tools/glm_study_yaml.py",
        "study/modules.yaml",
        "study/claims.yaml",
        "study/study_folders.yaml",
        "study/open_questions.yaml",
        "RequestProject/GLM/Rule30/DEVELOPMENT.md",
    ),
}

#: The scopes the command line accepts.
SCOPES: Tuple[str, ...] = ("studies", "all")

#: ``Link.recorded`` for a link to a never-supplied package file.
NOT_SUPPLIED_RECORD = "not-supplied"


def _lean_registry() -> Tuple[str, ...]:
    """Lean file names recorded missing in ``studies/_lean_files_needed.md``
    (the same reading :mod:`study_manifest` makes)."""
    from .study_manifest import _parse_missing_registry
    path = C.LEAN_FILES_NEEDED
    if not path.is_file():
        return ()
    return _parse_missing_registry(path.read_text(encoding="utf-8"))


def _local_only_items() -> Tuple[str, ...]:
    """The ``path`` of every intake-ledger record marked ``local_only``
    (relative to ``source_material/``).  A line reading of the ledger, so
    PyYAML is not needed."""
    path = C.INTAKE_LEDGER
    if not path.is_file():
        return ()
    out: List[str] = []
    record_path: Optional[str] = None
    local = False

    def close() -> None:
        if record_path and local:
            out.append(record_path)

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- "):
            close()
            record_path, local = None, False
        stripped = line.strip().lstrip("- ").strip()
        if stripped.startswith("path:") and line.startswith(("  ", "- ")):
            value = stripped[len("path:"):].strip().strip("'\"")
            if record_path is None:
                record_path = value
        elif stripped == "local_only: true":
            local = True
    close()
    return tuple(out)


def _recorded(rel: Optional[str]) -> str:
    """``"lean-missing"`` or ``"local-only"`` when the repository-relative
    path ``rel`` is a file recorded as absent from this checkout, else
    ``""``."""
    if not rel:
        return ""
    lean_prefix = C.LEAN_ROOT.relative_to(C.REPOSITORY_ROOT).as_posix() + "/"
    if rel.endswith(".lean") and rel.startswith(lean_prefix):
        if Path(rel).name in _lean_registry():
            return "lean-missing"
    source = C.SOURCE_MATERIAL_DIR.relative_to(C.REPOSITORY_ROOT).as_posix()
    if rel.startswith(source + "/"):
        if rel[len(source) + 1:] in _local_only_items():
            return "local-only"
    return ""


@dataclass(frozen=True)
class Link:
    """One relative link of a document that names a missing file."""

    document: str            # studies scope: file name; all: repo-relative path
    line: int                # 1-based line of the link
    target: str              # as written
    repair: Optional[str]    # the new target, relative to the document
    recorded: str = ""       # "lean-missing" / "local-only" / "not-supplied"


# ---------------------------------------------------------------------------
# Which documents
# ---------------------------------------------------------------------------

def study_documents(root: Optional[Path] = None) -> List[Path]:
    """Every ``studies/*.md`` (sorted), or every ``*.md`` directly in
    ``root``."""
    root = Path(root) if root is not None else C.STUDIES_DIR
    return sorted(root.glob("*.md"))


def scope_documents(scope: str = "studies",
                    root: Optional[Path] = None) -> List[Path]:
    """The documents of a scope.  ``root`` (a folder of ``*.md``, for tests)
    overrides the scope."""
    if root is not None or scope == "studies":
        return study_documents(root)
    if scope != "all":
        raise ValueError(f"unknown scope {scope!r}; one of {SCOPES}")
    from . import inventory as inv
    generated = set(inv.generated_paths())
    return [C.REPOSITORY_ROOT / rel for rel in inv.document_paths()
            if rel not in generated]


def _name(path: Path, scope: str, root: Optional[Path]) -> str:
    if root is not None or scope == "studies":
        return path.name
    return _repo_path(path) or path.name


def _repo_path(path: Path) -> Optional[str]:
    try:
        return Path(os.path.normpath(path)).relative_to(
            C.REPOSITORY_ROOT).as_posix()
    except ValueError:
        return None


def _is_relative(target: str) -> bool:
    return not (re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target)
                or target.startswith("#") or target.startswith("/"))


def document_links(path: Path) -> List[Tuple[int, str]]:
    """``(line, target)`` for every relative link of ``path``."""
    out: List[Tuple[int, str]] = []
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), 1):
        for match in _LINK.finditer(line):
            target = match.group(1)
            if _is_relative(target) and target.split("#")[0]:
                out.append((lineno, target))
    return out


def _exists(base: Path, target: str) -> bool:
    path = target.split("#")[0]
    return (base / unquote(path)).exists()


def _repo_relative(doc_dir: Path, path: str) -> Optional[str]:
    return _repo_path(doc_dir / unquote(path))


# ---------------------------------------------------------------------------
# The rules
# ---------------------------------------------------------------------------

def _package_relative(document: Path, path: str) -> Optional[Tuple[str, str]]:
    """``(package, package-relative path)`` of a link of a package document,
    or ``None`` (not a package document, or the link leaves the package)."""
    entry = PACKAGE_DOCUMENTS.get(_repo_path(document) or "")
    if entry is None:
        return None
    package, place = entry
    joined = os.path.normpath(os.path.join(place or ".", unquote(path)))
    if joined.startswith("..") or os.path.isabs(joined):
        return None
    return package, Path(joined).as_posix()


def _not_supplied(document: Path, path: str) -> bool:
    found = _package_relative(document, path)
    return found is not None and found[1] in NOT_SUPPLIED.get(found[0], ())


def _moved(rel: str) -> Iterable[Path]:
    """The three moves of the reorganisation, applied to a
    repository-relative path."""
    head, _, rest = rel.partition("/")
    if head == "glm_universal" and rest:
        yield C.PACKAGE_ROOT / rest
    elif head == "glm_lean" and rest:
        yield C.LEAN_ROOT / rest
        if rest.endswith(".lean"):
            yield C.lean_file(rest)
    elif head == "source_material" and rest:
        for prefix in ("done/", "ToDo/"):
            if rest.startswith(prefix):
                rest = rest[len(prefix):]
                break
        yield C.source_material_item(rest)
        for item in _local_only_items():
            if item.split("/", 1)[-1] == rest:
                yield C.SOURCE_MATERIAL_DIR / item


def _candidates(document: Path, path: str, rel: str) -> Iterable[Path]:
    """Where the file a link names may be now, in the order the module
    docstring gives (``path`` as written, ``rel`` resolved against the
    repository root)."""
    yield from _moved(rel)
    head, _, rest = rel.partition("/")
    doc_rel = _repo_path(document) or ""
    if doc_rel.startswith("src/") and head == "src" and rest:
        # The document moved one level down (glm_universal/ -> src/glm_universal/,
        # glm_lean/ -> src/lean/); the link was written one level higher.
        yield C.REPOSITORY_ROOT / rest
        yield from _moved(rest)
    found = _package_relative(document, path)
    if found is not None:
        package_name, pkg_rel = found
        package = C.source_material_item(package_name)
        in_lean = pkg_rel.startswith(C.LEAN_LIBRARY + "/")
        if in_lean:
            yield C.LEAN_ROOT / pkg_rel
        yield package / pkg_rel
        if Path(pkg_rel).name == "README.md":
            if in_lean:
                yield (C.LEAN_ROOT / pkg_rel).parent
            yield (package / pkg_rel).parent


def _relative(candidate: Path, doc_dir: Path, path: str,
              hash_: str, fragment: str) -> str:
    new = Path(os.path.relpath(candidate, doc_dir)).as_posix()
    if candidate.is_dir() and not new.endswith("/"):
        new += "/"
    if "%" in path:
        new = quote(new, safe="/._-~")
    return new + (hash_ + fragment if hash_ else "")


def repair_target(document: Path, target: str) -> Optional[str]:
    """The new target for a link of ``document`` naming a missing file, or
    ``None`` when no rule finds it (the target is returned unchanged if it
    already exists or is recorded absent).  A candidate that exists wins over
    one that is recorded absent."""
    doc_dir = document.parent
    if _exists(doc_dir, target):
        return target
    path, hash_, fragment = target.partition("#")
    rel = _repo_relative(doc_dir, path)
    if rel is None:
        return None
    if _recorded(rel):
        return target
    candidates = list(_candidates(document, path, rel))
    for candidate in candidates:
        if candidate.exists():
            return _relative(candidate, doc_dir, path, hash_, fragment)
    for candidate in candidates:
        if _recorded(_repo_path(candidate)):
            return _relative(candidate, doc_dir, path, hash_, fragment)
    return None


def broken_links(root: Optional[Path] = None, skip: Sequence[str] = (),
                 scope: str = "studies") -> List[Link]:
    """Every relative link of the scope's documents that names a missing
    file, with the repair the rules give (``None`` when unresolved) and, for
    a file recorded absent where the link points or never supplied, the
    record (``recorded``)."""
    out: List[Link] = []
    for doc in scope_documents(scope, root):
        name = _name(doc, scope, root)
        if name in skip or doc.name in skip:
            continue
        for lineno, target in document_links(doc):
            if _exists(doc.parent, target):
                continue
            path = target.split("#")[0]
            record = _recorded(_repo_relative(doc.parent, path))
            repair = repair_target(doc, target)
            if repair is None and _not_supplied(doc, path):
                record = NOT_SUPPLIED_RECORD
            out.append(Link(name, lineno, target, repair, record))
    return out


def links_report(root: Optional[Path] = None, skip: Sequence[str] = (),
                 scope: str = "studies") -> Dict[str, object]:
    """Counts and lists: ``broken`` (links naming a missing file that is not
    recorded absent where the link points), ``repairable`` (repointed, or
    for a never-supplied file unlinked, by ``--fix``), ``not_supplied``,
    ``unresolved`` (the ``(document, line, target)`` triples no rule
    finds), ``to_documents`` (broken links to a ``.md`` -- the ones
    ``corpus --check`` counts), ``recorded_absent`` (``(document, line,
    target, record)`` for links to a file recorded missing or local-only)
    and ``holds`` (nothing broken)."""
    links = broken_links(root, skip, scope)
    recorded = [(l.document, l.line, l.target, l.recorded) for l in links
                if l.recorded and l.recorded != NOT_SUPPLIED_RECORD]
    broken = [l for l in links
              if not l.recorded or l.recorded == NOT_SUPPLIED_RECORD]
    not_supplied = [(l.document, l.line, l.target) for l in broken
                    if l.recorded == NOT_SUPPLIED_RECORD]
    unresolved = [(l.document, l.line, l.target) for l in broken
                  if l.repair is None and not l.recorded]
    to_documents = [(l.document, l.line, l.target) for l in broken
                    if unquote(l.target.split("#")[0]).endswith(".md")]
    docs = scope_documents(scope, root)
    return {
        "scope": "folder" if root is not None else scope,
        "documents": len(docs),
        "links": sum(len(document_links(d)) for d in docs),
        "broken": len(broken),
        "repairable": len(broken) - len(unresolved),
        "not_supplied": not_supplied,
        "unresolved": unresolved,
        "to_documents": to_documents,
        "recorded_absent": recorded,
        "holds": not broken,
    }


def rewrite_text(text: str, links: Sequence[Link]
                 ) -> Tuple[str, List[Tuple[str, str]]]:
    """``text`` with each link of ``links`` repointed to its ``repair`` (or,
    for a never-supplied target, with the link dropped around its text), and
    the ``(old, new)`` targets changed (``new`` is ``""`` for a dropped
    link).  Only ``](old)`` -- or, for a dropped link, ``[text](old)`` -- is
    replaced, so the rest of the line is untouched."""
    pairs: List[Tuple[str, str]] = []
    for link in links:
        if link.recorded == NOT_SUPPLIED_RECORD:
            pattern = re.compile(r"\[([^\]]*)\]\(" + re.escape(link.target)
                                 + r"\)")
            text, count = pattern.subn(lambda m: m.group(1), text)
            if count:
                pairs.append((link.target, ""))
            continue
        if link.repair is None or link.repair == link.target:
            continue
        old, new = "](" + link.target + ")", "](" + link.repair + ")"
        if old in text:
            text = text.replace(old, new)
            pairs.append((link.target, link.repair))
    return text, sorted(set(pairs))


def fix_links(root: Optional[Path] = None, skip: Sequence[str] = (),
              scope: str = "studies") -> Dict[str, List[Tuple[str, str]]]:
    """Repoint every repairable broken link of the scope in place, and drop
    the link (not its text) around every never-supplied target
    (:func:`rewrite_text`); returns, per document changed, the ``(old,
    new)`` targets."""
    changed: Dict[str, List[Tuple[str, str]]] = {}
    by_doc: Dict[Path, List[Link]] = {}
    docs = {_name(d, scope, root): d for d in scope_documents(scope, root)}
    for link in broken_links(root, skip, scope):
        by_doc.setdefault(docs[link.document], []).append(link)
    for path, links in sorted(by_doc.items()):
        before = path.read_text(encoding="utf-8")
        after, pairs = rewrite_text(before, links)
        if pairs and after != before:
            path.write_text(after, encoding="utf-8")
            changed[_name(path, scope, root)] = pairs
    return changed


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    scope = "studies"
    if "--scope" in args:
        at = args.index("--scope")
        if at + 1 >= len(args) or args[at + 1] not in SCOPES:
            print(f"--scope takes one of: {', '.join(SCOPES)}")
            return 2
        scope = args[at + 1]
    if "--fix" in args:
        changed = fix_links(scope=scope)
        print(f"repointed links in {len(changed)} document(s)")
        for name, pairs in changed.items():
            dropped = sum(1 for _, new in pairs if not new)
            print(f"  {name}: {len(pairs)}"
                  + (f" ({dropped} dropped: never supplied)" if dropped else ""))
    report = links_report(scope=scope)
    if "--json" in args:
        print(json.dumps(report, indent=1, sort_keys=True))
    else:
        print(f"scope {scope}: {report['documents']} documents, "
              f"{report['links']} relative links, {report['broken']} broken "
              f"({report['repairable']} repairable, of them "
              f"{len(report['not_supplied'])} to a never-supplied file; "
              f"{len(report['unresolved'])} unresolved; "
              f"{len(report['to_documents'])} to a document); "
              f"{len(report['recorded_absent'])} to a file recorded absent")
        for doc, line, target, record in report["recorded_absent"]:
            print(f"  recorded absent ({record}): {doc}:{line} {target}")
        for doc, line, target in report["not_supplied"]:
            print(f"  never supplied (--fix drops the link): "
                  f"{doc}:{line} {target}")
        for doc, line, target in report["unresolved"]:
            print(f"  unresolved: {doc}:{line} {target}")
    return 0 if report["holds"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""``glm_universal.corpus.inventory`` -- the documents, as objects.

The corpus of prose is treated here exactly as the Lean development is treated
by :mod:`glm_universal.reasoning.lean_address`: a set of units with a stated
structure, enumerated by a rule rather than by a hand-kept list, and reduced to
a digest so that anything derived from it can be reported *stale* instead of
answered from.

Three rules, and nothing else, decide what this module says about a file.

**Which files are documents.**  Every Markdown file of the repository outside
``source_material/`` (which is what was supplied, not what was written here),
outside the caches, and outside the Lean build tree.  Nothing is listed by
hand, so a document cannot be forgotten by an index.

**Which documents are archive.**  A document is a *record of a round* -- not a
description of the state now -- exactly when its name ends ``_ARCHIVE.md``, or
it is the working note ``ARISTOTLE_SUMMARY.md``, or it lives under a directory
named ``archive``.  Everything else is *state*.  This is the rule the feedback
asked for in place of a judgement: a reader can tell which half a file is in
from its path, and so can a test.

**Which documents are generated.**  A document is generated exactly when
:mod:`glm_universal.corpus.render` holds a generator for its path.  There is no
list of "files that look generated"; the registry that writes them is the
definition.

Structure inside a document
---------------------------
A document is split at its ``##`` headings into :class:`Section` objects, and
the block whose heading begins *Tier 0* is parsed into a :class:`Tier0` -- the
question, the verdict, the single deciding figure, and the dotted name of the
function that recomputes it.  That is the coarse end of the delta-sigma
contract the project applies to its own prose: a reader who stops after tier 0
has a bounded reading, not a wrong one, and
:mod:`glm_universal.corpus.checks` is what holds the two ends together.

Nothing here constructs a float, and nothing here writes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..derived import memo
from .. import integrity

__all__ = [
    "REPOSITORY_ROOT",
    "Section",
    "Tier0",
    "Document",
    "document_paths",
    "documents",
    "document",
    "source_documents",
    "generated_paths",
    "state_documents",
    "archive_documents",
    "corpus_digest",
    "inventory_report",
    "is_archive_path",
    "TIER0_FIELDS",
    "NO_FUNCTION",
]

_HERE = Path(__file__).resolve()

#: The directory holding ``overlay/`` -- the repository root.
REPOSITORY_ROOT = _HERE.parent.parent.parent.parent

#: Directories never walked: caches, the Lean build tree, version control, and
#: ``source_material/``, which holds what was supplied rather than written.
SKIP_DIRECTORIES = frozenset({
    ".git", ".lake", ".pytest_cache", "__pycache__", "node_modules",
    "source_material", "lake-packages", ".ipynb_checkpoints",
})

#: A document larger than this is a data dump, not prose.
MAX_DOCUMENT_BYTES = 4 * 1024 * 1024


def is_archive_path(relative: str) -> bool:
    """Is this document a record of a round rather than the state now?

    The rule, and the whole of it: an ``_ARCHIVE.md`` suffix, the session
    working note, or a directory named ``archive`` anywhere in the path.
    """
    name = relative.rsplit("/", 1)[-1]
    if name.endswith("_ARCHIVE.md"):
        return True
    if name == "ARISTOTLE_SUMMARY.md":
        return True
    return "archive/" in relative.lower()


def generated_paths() -> Tuple[str, ...]:
    """The documents a generator writes.

    Imported here rather than at module scope because
    :mod:`glm_universal.corpus.render` reads the inventory to write them: the
    registry that emits a document is the definition of "generated", and this
    is the one direction the dependency may not be taken eagerly.
    """
    from . import render
    return tuple(sorted(render.GENERATED))


def is_generated(relative: str) -> bool:
    """Is this document written by a generator rather than by a person?"""
    return relative in generated_paths()


def document_paths(root: Optional[Path] = None) -> Tuple[str, ...]:
    """Every document of the repository, as ``/``-separated relative paths."""
    base = Path(root) if root is not None else REPOSITORY_ROOT
    out: List[str] = []
    stack = [base]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir())
        except OSError:  # pragma: no cover - defensive
            continue
        for entry in entries:
            if entry.is_dir():
                if entry.name not in SKIP_DIRECTORIES:
                    stack.append(entry)
                continue
            if entry.suffix != ".md":
                continue
            try:
                if entry.stat().st_size > MAX_DOCUMENT_BYTES:
                    continue
            except OSError:  # pragma: no cover - defensive
                continue
            out.append(entry.relative_to(base).as_posix())
    return tuple(sorted(out))


# ===========================================================================
#  Structure
# ===========================================================================

_H1 = re.compile(r"^#\s+(.*\S)\s*$")
_H2 = re.compile(r"^##\s+(.*\S)\s*$")
_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_FENCE = re.compile(r"^\s*```")

#: The four labelled fields of a tier-0 block, in the order they are written.
TIER0_FIELDS: Tuple[str, ...] = ("question", "verdict", "figure", "recomputed")

_FIELD_LABELS: Dict[str, str] = {
    "question": "Question.",
    "verdict": "Verdict.",
    "figure": "Deciding figure.",
    "recomputed": "Recomputed by.",
}

#: What a tier-0 block writes in ``Recomputed by`` when the document is an
#: argument rather than a measurement.  Stated, so that "no function" is a
#: declaration and not an omission.
NO_FUNCTION = "(hand-written argument; nothing to recompute)"


@dataclass(frozen=True)
class Section:
    """One ``##`` section of a document."""

    document: str          # relative path of the document
    heading: str           # the heading text, without the ``##``
    anchor: str            # GitHub-style anchor, for addressing
    start: int             # 1-based line of the heading
    end: int               # 1-based line after the section
    text: str              # the section body, heading included

    @property
    def unit(self) -> str:
        """The addressable name of this section: ``path#anchor``."""
        return f"{self.document}#{self.anchor}"

    @property
    def lines(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class Tier0:
    """The coarse read of a document: four fields, all required."""

    question: str
    verdict: str
    figure: str
    recomputed: str

    @property
    def has_function(self) -> bool:
        return self.recomputed != NO_FUNCTION and bool(self.recomputed)


@dataclass(frozen=True)
class Document:
    """One Markdown document of the repository."""

    path: str                       # relative, ``/``-separated
    title: str                      # the first ``#`` heading, or the file name
    text: str
    sections: Tuple[Section, ...]
    tier0: Optional[Tier0]
    tier0_lines: Tuple[int, int]    # 1-based span of the tier-0 block, or (0,0)
    links: Tuple[str, ...]          # repository documents this one links to
    archive: bool
    generated: bool

    @property
    def lines(self) -> int:
        return self.text.count("\n") + (0 if self.text.endswith("\n") else 1)

    @property
    def words(self) -> int:
        return len(self.text.split())

    @property
    def state(self) -> bool:
        return not self.archive


def _anchor(heading: str) -> str:
    """The GitHub-style anchor of a heading: lower case, hyphens, no punctuation."""
    cleaned = re.sub(r"[`*_\[\]()]", "", heading).strip().lower()
    cleaned = re.sub(r"[^a-z0-9\s-]", "", cleaned)
    return re.sub(r"\s+", "-", cleaned).strip("-") or "section"


def _split_sections(path: str, text: str) -> Tuple[Section, ...]:
    lines = text.splitlines()
    marks: List[Tuple[int, str]] = []
    fenced = False
    for index, line in enumerate(lines):
        if _FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = _H2.match(line)
        if match:
            marks.append((index, match.group(1)))
    out: List[Section] = []
    seen: Dict[str, int] = {}
    for position, (index, heading) in enumerate(marks):
        end = marks[position + 1][0] if position + 1 < len(marks) else len(lines)
        base = _anchor(heading)
        count = seen.get(base, 0)
        seen[base] = count + 1
        anchor = base if not count else f"{base}-{count}"
        out.append(Section(document=path, heading=heading, anchor=anchor,
                           start=index + 1, end=end + 1,
                           text="\n".join(lines[index:end])))
    return tuple(out)


#: The line that closes a tier-0 block.  The block is the heading, the four
#: fields and this note -- *not* the whole section down to the next heading,
#: because a document's own opening paragraphs often sit there and they are
#: exactly the text the verdict has to be grounded in.
TIER0_FOOTER = "*Tier 0 is a coarse read"


def _parse_tier0(sections: Tuple[Section, ...]) -> Tuple[Optional["Tier0"],
                                                         Tuple[int, int]]:
    for section in sections:
        if not section.heading.lower().startswith("tier 0"):
            continue
        lines = section.text.splitlines()
        found: Dict[str, str] = {}
        last = 0
        for offset, line in enumerate(lines):
            for field, label in _FIELD_LABELS.items():
                match = re.match(r"\*\*" + re.escape(label) + r"\*\*\s*(.+?)\s*$",
                                 line)
                if match:
                    found[field] = match.group(1).strip()
                    last = max(last, offset)
            if line.startswith(TIER0_FOOTER):
                last = max(last, offset)
        end = section.start + last + 1
        if len(found) == len(_FIELD_LABELS):
            return (Tier0(**found), (section.start, end))
        return (None, (section.start, end))
    return (None, (0, 0))


def _links(text: str, path: str) -> Tuple[str, ...]:
    """Repository Markdown files this document links to, as relative paths."""
    here = Path(path).parent
    out: List[str] = []
    for target in _LINK.findall(text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        clean = target.split("#", 1)[0]
        if not clean.endswith(".md"):
            continue
        joined = (here / clean).as_posix() if str(here) != "." else clean
        parts: List[str] = []
        for piece in joined.split("/"):
            if piece == "..":
                if parts:
                    parts.pop()
            elif piece not in (".", ""):
                parts.append(piece)
        out.append("/".join(parts))
    seen: List[str] = []
    for item in out:
        if item not in seen:
            seen.append(item)
    return tuple(seen)


def _read(path: str, root: Path) -> Document:
    text = (root / path).read_text(encoding="utf-8")
    sections = _split_sections(path, text)
    tier0, span = _parse_tier0(sections)
    title = path.rsplit("/", 1)[-1]
    for line in text.splitlines():
        match = _H1.match(line)
        if match:
            title = match.group(1)
            break
    return Document(path=path, title=title, text=text, sections=sections,
                    tier0=tier0, tier0_lines=span, links=_links(text, path),
                    archive=is_archive_path(path),
                    generated=is_generated(path))


@memo
def documents() -> Tuple[Document, ...]:
    """Every document, parsed, in path order."""
    root = REPOSITORY_ROOT
    return tuple(_read(path, root) for path in document_paths(root))


def document(path: str) -> Optional[Document]:
    """One document by relative path, or ``None``."""
    for item in documents():
        if item.path == path:
            return item
    return None


def source_documents() -> Tuple[Document, ...]:
    """Every document that is written rather than emitted.

    A generated document is an *output* of the corpus, so it is not part of
    the corpus a derived artefact is guarded against: were it included, the
    act of writing the digest would invalidate the digest.
    """
    return tuple(d for d in documents() if not d.generated)


def state_documents() -> Tuple[Document, ...]:
    """The documents that describe the system as it is."""
    return tuple(d for d in documents() if d.state)


def archive_documents() -> Tuple[Document, ...]:
    """The documents that record a round."""
    return tuple(d for d in documents() if d.archive)


def written_text(document: "Document") -> str:
    """A document with the bodies of its generated blocks and figures removed.

    What guards a derived artefact must be the *written* input, not the
    artefact's own output: a digest over the whole file would move every time
    a generated block was refreshed, so refreshing it would make it stale, and
    the cache would never settle.  Blanking the emitted bodies -- and only
    them -- is the fixed point.

    An inline figure is emitted output for exactly the same reason a block is,
    so its body is blanked here too; otherwise a sentence that says how many
    sections the corpus has would move the digest that decides what the
    sections are.
    """
    from . import render
    blank = lambda m: m.group("open") + m.group("close")  # noqa: E731
    return render._FIGURE.sub(blank, render._BLOCK.sub(blank, document.text))


def corpus_digest() -> str:
    """SHA-256 over the written corpus: the name and content of every document.

    The same canonical form the sign-off ledger and the Lean address book use
    -- path, NUL, digest of the content, NUL -- so that anything derived from
    the prose is guarded the way anything derived from the Lean tree is.  The
    content hashed is :func:`written_text`, and generated documents are not in
    the list at all: an output cannot be part of what licenses it.
    """
    outer_parts: List[str] = []
    for doc in source_documents():
        outer_parts.append(doc.path)
        outer_parts.append(integrity.sha256_hex(
            written_text(doc).encode("utf-8")))
    return integrity.sha256_hex("\0".join(outer_parts).encode("utf-8"))


def written_lines(document: "Document") -> int:
    """Lines of a document, not counting what a generator emitted into it."""
    text = written_text(document)
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def written_words(document: "Document") -> int:
    """Words of a document, not counting what a generator emitted into it.

    Everything the inventory counts is counted this way, and for one reason:
    a generated block that quoted a total including its own body would move
    that total every time it was refreshed.  Counting only what a person wrote
    makes the figure a fixed point, and it is also the figure a reader wants --
    how much of this was thought of rather than measured.
    """
    return len(written_text(document).split())


def inventory_report() -> Dict[str, object]:
    """What the corpus is, counted -- over what was written, not what was emitted."""
    docs = [d for d in documents() if not d.generated]
    state = [d for d in docs if d.state]
    archive = [d for d in docs if d.archive]
    with_tier0 = [d for d in state if d.tier0 is not None]
    return {
        "documents": len(docs),
        "state_documents": len(state),
        "archive_documents": len(archive),
        "lines": sum(written_lines(d) for d in docs),
        "state_lines": sum(written_lines(d) for d in state),
        "archive_lines": sum(written_lines(d) for d in archive),
        "words": sum(written_words(d) for d in docs),
        "state_words": sum(written_words(d) for d in state),
        "sections": sum(len(d.sections) for d in docs),
        "state_sections": sum(len(d.sections) for d in state),
        "tier0_present": len(with_tier0),
        "tier0_missing": tuple(d.path for d in state if d.tier0 is None),
        "tier0_words": sum(len((d.tier0.question + " " + d.tier0.verdict + " "
                                + d.tier0.figure).split())
                           for d in with_tier0 if d.tier0 is not None),
        "largest": tuple(sorted(((written_lines(d), d.path) for d in docs),
                                reverse=True)[:5]),
        "digest": corpus_digest(),
    }

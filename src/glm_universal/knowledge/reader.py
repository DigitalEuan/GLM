"""``glm_universal.knowledge.reader`` -- the corpus walk, by rule.

The walk that turns the repository's own files into the sentences and tokens
the knowledge model counts.  Every file is read into **folder → document →
paragraph → sentence → token**, each sentence carrying its address
(``document#pN.sM``) and its tier-0 mark.  Prose only:

* **Markdown** -- paragraphs separated by blank lines, fenced code blocks
  removed, headings kept as prose.  Sentences inside a Tier-0 block (the
  ``## Tier 0`` section closed by ``*Tier 0 is a coarse read``) carry
  ``tier0=True``.
* **Plain text** (``.txt``) -- paragraphs separated by blank lines.
* **Python** (``.py``) -- docstrings and ``#`` comments only, each block
  one paragraph.
* **Lean** (``.lean``) -- doc comments ``/-- … -/`` only, each block one
  paragraph.  ``--`` line comments and proof bodies are not read.
* **JSON** -- every string value (recursively) of at least five words.
* **CSV** -- every cell of at least five words.

Other extensions return ``None`` (the model drops them).  ZIP members are
walked as virtual files with paths ``archive.zip/member/relative/path``.

This module is the *only* one that touches file bytes; ``model`` counts
what it produces.  It is deterministic (no ``random``), exact (no floats),
and read-only.

*Reconstructed 29 October 2026 (Iteration 2 of the reorganisation).  The
original ``reader.py`` was lost in the upload; this version was written
from the documented interface in ``knowledge/README.md`` line 33, the
call-sites in ``knowledge/model.py``, the monkey-patch in
``tests/test_repository_hygiene.py``, the address shapes in
``reasoning/_data/evidence_model_study.json``, and the sibling modules
``word_address.py`` and ``corpus/inventory.py``.  It is a faithful
reconstruction of the documented behaviour; if a discrepancy with the
original is found, the original's behaviour is the spec.*
"""
from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import re
import tokenize
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Dict,
    FrozenSet,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
)

__all__ = [
    "Document",
    "Sentence",
    "Paragraph",
    "iter_sources",
    "read_bytes",
    "top_folder",
    "REPOSITORY_ROOT",
    "SKIP_DIRECTORIES",
    "SESSION_NOTES",
    "TIER0_FOOTER",
    "MIN_PROSE_WORDS",
]


# ---------------------------------------------------------------------------
# Paths and skip rules
# ---------------------------------------------------------------------------

#: The repository root.  ``knowledge/reader.py`` lives at
#: ``glm_universal/knowledge/reader.py`` -- three directories below the root
#: -- so three ``parent`` calls reach it (matching the convention in
#: ``corpus/inventory.py`` line 80).
_HERE = Path(__file__).resolve()
REPOSITORY_ROOT = _HERE.parent.parent.parent.parent

#: Directories never entered by the walk.  Mirrors ``corpus/inventory.py``'s
#: ``SKIP_DIRECTORIES`` minus the ones the reader *does* enter
#: (``source_material`` is walked, because the README's "supplied material"
#: clause and the evidence-model addresses reach into zip members).
SKIP_DIRECTORIES: FrozenSet[str] = frozenset({
    ".git",
    ".lake",
    "__pycache__",
    ".pytest_cache",
    "_knowledge_cache",   # the knowledge cache itself -- regenerated on demand
    "node_modules",
})

#: Files never read by the walk.  The session working note is the only one
#: (mirrors ``corpus/inventory.py`` line 92).
SESSION_NOTES: FrozenSet[str] = frozenset({"ARISTOTLE_SUMMARY.md"})

#: The footer that closes a Tier-0 block (mirrors ``corpus/inventory.py``
#: line 283).
TIER0_FOOTER = "*Tier 0 is a coarse read"

#: The minimum word count for a JSON string value or a CSV cell to count
#: as prose (per ``knowledge/README.md`` line 33).
MIN_PROSE_WORDS = 5

#: Maximum file size read (4 MB, mirroring ``signoff/rules.py`` line 569).
#: Files larger than this are skipped, matching the corpus's own limit.
_MAX_FILE_BYTES = 4 * 1024 * 1024


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Sentence:
    """A single prose sentence, with its address and tier-0 mark.

    ``tokens`` is a tuple of lower-cased tokens (no BOS/EOS; the model adds
    those).  ``address`` is ``f"{document_path}#p{p_idx}.s{s_idx}"`` --
    the witness string the corpus's ``define`` / ``continue_text`` answers
    quote.  ``folder`` is the immediate directory of the document (used by
    the friction studies' "directory reader").
    """
    tokens: Tuple[str, ...]
    address: str
    tier0: bool
    folder: str
    text: str = ""
    document: str = ""
    paragraph: int = 0


@dataclass(frozen=True)
class Paragraph:
    """A paragraph of a document: one or more sentences, with a tier-0 mark."""
    index: int
    sentences: Tuple[Sentence, ...]
    tier0: bool
    text: str


@dataclass(frozen=True)
class Document:
    """A file walked by the reader, with its sentences and digest.

    ``digest`` is ``sha256(data).hexdigest()`` -- the same value the model
    computes from the bytes ``iter_sources`` yields, so a cached ``Document``
    can be matched against a fresh read.
    """
    path: str
    digest: str
    sentences: Tuple[Sentence, ...]
    paragraphs: Tuple[Paragraph, ...] = ()
    tier0: bool = False
    archive: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

#: A fenced code block opening (``` or ~~~), possibly indented.
_FENCE = re.compile(r"^[ \t]*(```|~~~)")

#: A Markdown heading line.
_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")

#: A Tier-0 section heading (``## Tier 0 -- ...`` or ``## Tier 0 — ...``).
_TIER0_HEADING = re.compile(r"^##\s+Tier\s*0\b", re.IGNORECASE)

#: Sentence-end: a period, exclamation or question mark, optionally inside
#: quotes or brackets, followed by whitespace or end-of-line.  We split on
#: these so a paragraph becomes one or more sentences.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+|(?<=[.!?])$")

#: A token: a maximal run of letters (incl. underscore) or a single other
#: character.  This is the simple, deterministic tokeniser the corpus uses.
_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[^A-Za-z0-9_\s]")


def top_folder(path: str) -> str:
    """The top-level folder of a repository-relative path.

    ``"studies/A.md"`` -> ``"studies"``;
    ``"source_material/GLM-main.zip/GLM-main/foo.md"`` -> ``"source_material"``;
    ``"CAPABILITY_ASSESSMENT.md"`` -> ``"CAPABILITY_ASSESSMENT.md"`` (a
    root-level file: the filename itself is the "top folder").
    """
    return path.split("/", 1)[0]


def _immediate_folder(path: str) -> str:
    """The immediate directory of a path, or ``""`` for a root-level file.

    ``"studies/A.md"`` -> ``"studies"``;
    ``"source_material/GLM-main.zip/GLM-main/foo.md"`` ->
    ``"source_material/GLM-main.zip/GLM-main"``;
    ``"CAPABILITY_ASSESSMENT.md"`` -> ``""``.
    """
    if "/" not in path:
        return ""
    return path.rsplit("/", 1)[0]


def _tokenise(text: str) -> Tuple[str, ...]:
    """Lower-case, deterministic tokenisation, preserving order.

    Letters/underscore runs become one token; every other non-space
    character becomes its own token.  Whitespace is dropped.  Empty tokens
    are never produced.
    """
    out: List[str] = []
    for m in _TOKEN.finditer(text):
        tok = m.group(0).lower()
        if tok:
            out.append(tok)
    return tuple(out)


def _split_sentences(text: str) -> List[str]:
    """Split a paragraph's text into sentences on sentence-end punctuation.

    A sentence is the text from the last split point up to and including a
    ``.``, ``!`` or ``?`` (followed by whitespace or end-of-line).  Trailing
    text without a sentence-end becomes its own sentence.  Whitespace-only
    sentences are dropped.
    """
    text = text.strip()
    if not text:
        return []
    # Walk the regex, splitting after each sentence-end.
    out: List[str] = []
    start = 0
    for m in re.finditer(r"[.!?]+[\"'\)\]]*\s*", text):
        end = m.end()
        chunk = text[start:end].strip()
        if chunk:
            out.append(chunk)
        start = end
    tail = text[start:].strip()
    if tail:
        out.append(tail)
    return out


def _word_count(text: str) -> int:
    """Cheap word count by whitespace split."""
    return len(text.split())


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def _read_markdown(path: str, data: str) -> Optional[Document]:
    """Read a Markdown file: paragraphs separated by blank lines, fenced
    code blocks removed, headings kept as prose.  Tier-0 detection.

    Returns ``None`` if no prose survives.
    """
    lines = data.split("\n")
    paragraphs: List[Tuple[str, bool]] = []  # (text, tier0)
    in_fence = False
    in_tier0 = False
    buf: List[str] = []

    def _flush(tier0: bool) -> None:
        if buf:
            text = "\n".join(buf).strip()
            if text:
                paragraphs.append((text, tier0))
            buf.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        # Fence toggling.
        if _FENCE.match(line):
            in_fence = not in_fence
            i += 1
            continue
        if in_fence:
            i += 1
            continue
        # Tier-0 heading: enter the tier-0 block.
        if _TIER0_HEADING.match(line):
            _flush(in_tier0)
            in_tier0 = True
            # The heading text itself is prose.
            buf.append(_HEADING.sub(r"\2", line) if _HEADING.match(line) else line)
            i += 1
            continue
        # Tier-0 footer: leave the tier-0 block.
        if in_tier0 and line.startswith(TIER0_FOOTER):
            _flush(in_tier0)
            in_tier0 = False
            i += 1
            continue
        # Blank line: paragraph break.
        if not line.strip():
            _flush(in_tier0)
            i += 1
            continue
        # Heading line: starts a new paragraph (kept as prose).
        if _HEADING.match(line):
            _flush(in_tier0)
            buf.append(_HEADING.sub(r"\2", line))
            i += 1
            continue
        # Normal line: accumulate.
        buf.append(line)
        i += 1
    _flush(in_tier0)

    if not paragraphs:
        return None

    digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
    folder = _immediate_folder(path)
    sentences: List[Sentence] = []
    para_objs: List[Paragraph] = []
    for p_idx, (ptext, tier0) in enumerate(paragraphs):
        s_list = _split_sentences(ptext)
        s_objs: List[Sentence] = []
        for s_idx, stext in enumerate(s_list):
            toks = _tokenise(stext)
            if not toks:
                continue
            addr = f"{path}#p{p_idx}.s{s_idx}"
            s = Sentence(
                tokens=toks,
                address=addr,
                tier0=tier0,
                folder=folder,
                text=stext,
                document=path,
                paragraph=p_idx,
            )
            s_objs.append(s)
            sentences.append(s)
        if s_objs:
            para_objs.append(Paragraph(
                index=p_idx, sentences=tuple(s_objs), tier0=tier0, text=ptext,
            ))

    if not sentences:
        return None

    return Document(
        path=path,
        digest=digest,
        sentences=tuple(sentences),
        paragraphs=tuple(para_objs),
        tier0=any(p.tier0 for p in para_objs),
        archive=False,
    )


# ---------------------------------------------------------------------------
# Plain text
# ---------------------------------------------------------------------------

def _read_text(path: str, data: str) -> Optional[Document]:
    """Read a plain-text file: paragraphs separated by blank lines."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", data) if p.strip()]
    if not paragraphs:
        return None
    digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
    folder = _immediate_folder(path)
    sentences: List[Sentence] = []
    para_objs: List[Paragraph] = []
    for p_idx, ptext in enumerate(paragraphs):
        s_list = _split_sentences(ptext)
        s_objs: List[Sentence] = []
        for s_idx, stext in enumerate(s_list):
            toks = _tokenise(stext)
            if not toks:
                continue
            addr = f"{path}#p{p_idx}.s{s_idx}"
            s = Sentence(tokens=toks, address=addr, tier0=False,
                         folder=folder, text=stext, document=path, paragraph=p_idx)
            s_objs.append(s)
            sentences.append(s)
        if s_objs:
            para_objs.append(Paragraph(index=p_idx, sentences=tuple(s_objs),
                                       tier0=False, text=ptext))
    if not sentences:
        return None
    return Document(path=path, digest=digest, sentences=tuple(sentences),
                    paragraphs=tuple(para_objs), tier0=False, archive=False)


# ---------------------------------------------------------------------------
# Python (docstrings + comments only)
# ---------------------------------------------------------------------------

def _read_python(path: str, data: str) -> Optional[Document]:
    """Read a Python file: module/class/function docstrings and ``#`` comments
    only.  Each docstring or comment block becomes one paragraph.
    """
    paragraphs: List[str] = []

    # Docstrings via ast.
    try:
        tree = ast.parse(data)
    except SyntaxError:
        tree = None
    if tree is not None:
        for node in ast.walk(tree):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                paragraphs.append(doc)

    # Comments via tokenize.
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(data).readline))
    except (tokenize.TokenizeError, IndentationError):
        toks = []
    buf: List[str] = []
    for tok in toks:
        if tok.type == tokenize.COMMENT:
            # Strip the leading ``#`` and one space.
            text = tok.string[1:]
            if text.startswith(" "):
                text = text[1:]
            if text.strip():
                buf.append(text)
        else:
            if buf:
                paragraphs.append("\n".join(buf))
                buf.clear()
    if buf:
        paragraphs.append("\n".join(buf))

    if not paragraphs:
        return None

    digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
    folder = _immediate_folder(path)
    sentences: List[Sentence] = []
    para_objs: List[Paragraph] = []
    for p_idx, ptext in enumerate(paragraphs):
        s_list = _split_sentences(ptext)
        s_objs: List[Sentence] = []
        for s_idx, stext in enumerate(s_list):
            toks = _tokenise(stext)
            if not toks:
                continue
            addr = f"{path}#p{p_idx}.s{s_idx}"
            s = Sentence(tokens=toks, address=addr, tier0=False,
                         folder=folder, text=stext, document=path, paragraph=p_idx)
            s_objs.append(s)
            sentences.append(s)
        if s_objs:
            para_objs.append(Paragraph(index=p_idx, sentences=tuple(s_objs),
                                       tier0=False, text=ptext))
    if not sentences:
        return None
    return Document(path=path, digest=digest, sentences=tuple(sentences),
                    paragraphs=tuple(para_objs), tier0=False, archive=False)


# ---------------------------------------------------------------------------
# Lean (doc comments /-- … -/ only)
# ---------------------------------------------------------------------------

_LEAN_DOC_START = re.compile(r"^/-\s*$|^/-\s+\S")
_LEAN_DOC_END = "/-"

def _read_lean(path: str, data: str) -> Optional[Document]:
    """Read a Lean file: doc comments ``/-- … -/`` only, each block one
    paragraph.  ``--`` line comments and proof bodies are not read.
    """
    lines = data.split("\n")
    paragraphs: List[str] = []
    in_doc = False
    buf: List[str] = []
    for line in lines:
        if in_doc:
            if line.strip().startswith("-/"):
                in_doc = False
                if buf:
                    paragraphs.append("\n".join(buf))
                    buf.clear()
            else:
                # Strip a leading ``- `` if present (Lean doc comment marker).
                stripped = re.sub(r"^\s*-\s?", "", line)
                if stripped.strip():
                    buf.append(stripped)
        else:
            # Detect a doc-comment opener: ``/--`` possibly followed by text.
            # The opener may also be a single-line ``/-- text -/``.
            m = re.match(r"^/-\s?(.*)$", line)
            if m and "doc" in line[:4] or line.startswith("/--"):
                rest = m.group(1)
                # Check for a same-line closer.
                if rest.rstrip().endswith("-/"):
                    text = rest.rstrip()[:-2].strip()
                    if text:
                        paragraphs.append(text)
                else:
                    if rest.strip():
                        buf.append(rest.strip())
                    in_doc = True
    if buf:
        paragraphs.append("\n".join(buf))

    if not paragraphs:
        return None
    return _read_text_from_paragraphs(path, paragraphs, _immediate_folder(path),
                                      hashlib.sha256(data.encode("utf-8")).hexdigest())


def _read_text_from_paragraphs(path: str, paragraphs: List[str],
                                folder: str, digest: str) -> Optional[Document]:
    """Build a Document from a list of pre-extracted paragraph strings."""
    sentences: List[Sentence] = []
    para_objs: List[Paragraph] = []
    for p_idx, ptext in enumerate(paragraphs):
        s_list = _split_sentences(ptext)
        s_objs: List[Sentence] = []
        for s_idx, stext in enumerate(s_list):
            toks = _tokenise(stext)
            if not toks:
                continue
            addr = f"{path}#p{p_idx}.s{s_idx}"
            s = Sentence(tokens=toks, address=addr, tier0=False,
                         folder=folder, text=stext, document=path, paragraph=p_idx)
            s_objs.append(s)
            sentences.append(s)
        if s_objs:
            para_objs.append(Paragraph(index=p_idx, sentences=tuple(s_objs),
                                       tier0=False, text=ptext))
    if not sentences:
        return None
    return Document(path=path, digest=digest, sentences=tuple(sentences),
                    paragraphs=tuple(para_objs), tier0=False, archive=False)


# ---------------------------------------------------------------------------
# JSON (string values of at least MIN_PROSE_WORDS words)
# ---------------------------------------------------------------------------

def _collect_json_strings(obj, out: List[str]) -> None:
    """Recursively collect every string value (not keys) from a parsed JSON
    object.  Object keys are not prose."""
    if isinstance(obj, str):
        if _word_count(obj) >= MIN_PROSE_WORDS:
            out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_json_strings(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect_json_strings(v, out)


def _read_json(path: str, data: str) -> Optional[Document]:
    """Read a JSON file: every string value (recursively) of at least five
    words becomes one paragraph."""
    try:
        obj = json.loads(data)
    except json.JSONDecodeError:
        return None
    strings: List[str] = []
    _collect_json_strings(obj, strings)
    if not strings:
        return None
    digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
    return _read_text_from_paragraphs(path, strings, _immediate_folder(path), digest)


# ---------------------------------------------------------------------------
# CSV (cells of at least MIN_PROSE_WORDS words)
# ---------------------------------------------------------------------------

def _read_csv(path: str, data: str) -> Optional[Document]:
    """Read a CSV file: every cell of at least five words becomes one
    paragraph."""
    try:
        reader = csv.reader(io.StringIO(data))
    except csv.Error:
        return None
    cells: List[str] = []
    for row in reader:
        for cell in row:
            if _word_count(cell) >= MIN_PROSE_WORDS:
                cells.append(cell)
    if not cells:
        return None
    digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
    return _read_text_from_paragraphs(path, cells, _immediate_folder(path), digest)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

#: File-extension dispatch table.  Each entry is a function ``(path, text) ->
#: Optional[Document]``.  Extensions not listed return ``None``.
_READERS: Dict[str, callable] = {
    ".md": _read_markdown,
    ".markdown": _read_markdown,
    ".txt": _read_text,
    ".py": _read_python,
    ".lean": _read_lean,
    ".json": _read_json,
    ".csv": _read_csv,
}


def read_bytes(path: str, data: bytes) -> Optional[Document]:
    """Read ``data`` (the bytes of ``path``) into a :class:`Document`, or
    return ``None`` if the file yields no prose.

    ``data`` is decoded as UTF-8 with ``errors="replace"`` (the corpus has
    a few odd bytes from the supplied material).  The dispatch is on the
    file extension; unknown extensions return ``None``.
    """
    text = data.decode("utf-8", errors="replace")
    ext = Path(path).suffix.lower()
    reader = _READERS.get(ext)
    if reader is None:
        return None
    try:
        return reader(path, text)
    except Exception:
        # A malformed file is silently dropped, matching the model's
        # ``if document is not None and document.sentences:`` guard.
        return None


# ---------------------------------------------------------------------------
# The walk
# ---------------------------------------------------------------------------

def _walk_zip(zip_path: str, data: bytes) -> Iterator[Tuple[str, bytes]]:
    """Yield ``(member_path, member_bytes)`` for each member of a zip archive,
    with paths ``f"{zip_path}/{member_name}"``.  Nested zips are walked
    recursively."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except (zipfile.BadZipFile, OSError):
        return
    for info in zf.infolist():
        if info.is_dir():
            continue
        try:
            member_bytes = zf.read(info)
        except (zipfile.BadZipFile, OSError, RuntimeError):
            continue
        member_path = f"{zip_path}/{info.filename}"
        yield member_path, member_bytes
        # Recurse into nested zips.
        if info.filename.lower().endswith(".zip"):
            yield from _walk_zip(member_path, member_bytes)


def iter_sources(root: Optional[Path] = None) -> Iterator[Tuple[str, bytes]]:
    """Walk the repository, yielding ``(relative_posix_path, file_bytes)``
    pairs in sorted path order.

    * ``root`` defaults to :data:`REPOSITORY_ROOT`.
    * Directories in :data:`SKIP_DIRECTORIES` are never entered.
    * Files in :data:`SESSION_NOTES` are never yielded.
    * ZIP archives are descended into: each member is yielded as
      ``("archive.zip/member/relative/path", member_bytes)``.
    * Paths are POSIX-style (``/`` separators), relative to ``root``.
    * Files larger than :data:`_MAX_FILE_BYTES` are skipped.
    """
    if root is None:
        root = REPOSITORY_ROOT
    else:
        root = Path(root).resolve()

    paths: List[Tuple[str, Path]] = []
    for dirpath, dirnames, filenames in os.walk(root):  # type: ignore[name-defined]
        # Prune skipped directories in place.
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRECTORIES]
        for name in filenames:
            if name in SESSION_NOTES:
                continue
            full = Path(dirpath) / name
            try:
                rel = full.relative_to(root).as_posix()
            except ValueError:
                continue
            paths.append((rel, full))

    # Sort by relative path for stable, deterministic order.
    paths.sort(key=lambda p: p[0])

    for rel, full in paths:
        try:
            data = full.read_bytes()
        except OSError:
            continue
        if len(data) > _MAX_FILE_BYTES:
            continue
        yield rel, data
        # Walk zip archives as virtual files.
        if rel.lower().endswith(".zip"):
            yield from _walk_zip(rel, data)


# Late import to avoid the module-level cost when iter_sources is never
# called (it is the cold-start path).
import os  # noqa: E402  (intentional late import for the walk)

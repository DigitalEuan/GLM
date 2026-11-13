"""Address repository knowledge as parts, and stitch reading paths over them.

The method is borrowed from the adjacent ``leechlean`` study, without its
lattice geometry: a document is a sequence of recurring parts, every part has a
stable address, its context is its document/heading/links, and a brief is a
*stitch* of selected addresses rather than a new document that copies them.

Addresses are path+heading based (``kp-...``), so they survive edits to the
body.  A separate content hash detects when two documents repeat the same part.
The source Markdown remains canonical; this module stores no second copy.
"""

from __future__ import annotations

import hashlib
import posixpath
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA = "cent-knowledge-atlas/1"
STITCH_SCHEMA = "cent-knowledge-stitch/1"
ADDRESS_PREFIX = "kp-"
DEFAULT_LIMIT = 8
DEFAULT_MIN_CHARS = 180
EXCLUDED_DIRS = {".git", "__pycache__", "node_modules", "cent_out"}
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "what",
    "when", "where", "which", "who", "why", "with",
}

HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^(```|~~~)")


@dataclass(frozen=True)
class Part:
    """One addressed Markdown section."""

    address: str
    path: str
    heading: str
    level: int
    line: int
    end_line: int
    content_hash: str
    summary: str
    links: tuple[str, ...]
    words: int
    body: str

    def public(self, include_body: bool = False) -> dict[str, Any]:
        payload = {
            "address": self.address,
            "path": self.path,
            "heading": self.heading,
            "level": self.level,
            "line": self.line,
            "end_line": self.end_line,
            "content_hash": self.content_hash,
            "summary": self.summary,
            "links": list(self.links),
            "words": self.words,
        }
        if include_body:
            payload["body"] = self.body
        return payload


@dataclass
class Atlas:
    root: Path
    parts: list[Part]
    edges: list[dict[str, str]] = field(default_factory=list)
    _by_address: dict[str, Part] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._by_address = {part.address: part for part in self.parts}

    def get(self, address: str) -> Part | None:
        return self._by_address.get(address)

    def summary(self) -> dict[str, Any]:
        documents = {part.path for part in self.parts}
        groups = duplicate_groups(self)
        return {
            "documents": len(documents),
            "parts": len(self.parts),
            "words": sum(part.words for part in self.parts),
            "duplicate_groups": len(groups),
            "duplicate_parts": sum(group["count"] for group in groups),
        }

    def payload(self, include_body: bool = False) -> dict[str, Any]:
        return {
            "ok": True,
            "schema": SCHEMA,
            "root": ".",
            "summary": self.summary(),
            "parts": [part.public(include_body) for part in self.parts],
            "edges": list(self.edges),
            "claim": (
                "Addresses index the source documents; they do not duplicate or "
                "replace them. A stitch is a reading path, not a new authority."
            ),
        }


def _normal(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _content_hash(text: str) -> str:
    return hashlib.sha1(_normal(text).encode("utf-8")).hexdigest()[:16]


def _address(path: str, heading: str, level: int, occurrence: int) -> str:
    seed = f"{path}|{level}|{heading}|{occurrence}"
    return ADDRESS_PREFIX + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _summary(body: str, heading: str) -> str:
    in_code = False
    for raw in body.splitlines():
        line = raw.strip()
        if FENCE.match(line):
            in_code = not in_code
            continue
        if in_code or not line or line == heading:
            continue
        if line.startswith(("#", "|", "<!--", "```", "~~~", "    ")):
            continue
        line = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)
        line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"[`*_>#]", "", line).strip()
        if len(line) >= 24:
            return line[:197] + ("…" if len(line) > 197 else "")
    return ""


def _split(path: str, text: str) -> list[Part]:
    headings = list(HEADING.finditer(text))
    spans: list[tuple[int, int, str, int, int]] = []
    if not headings:
        spans.append((0, len(text), "(document)", 0, 1))
    else:
        if headings[0].start() > 0:
            spans.append((0, headings[0].start(), "(preamble)", 0, 1))
        for index, match in enumerate(headings):
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            line = text.count("\n", 0, match.start()) + 1
            spans.append((match.start(), end, match.group(2).strip(), len(match.group(1)), line))

    occurrences: dict[tuple[str, int], int] = {}
    parts: list[Part] = []
    for start, end, heading, level, line in spans:
        body = text[start:end].strip("\n")
        if len(body.strip()) < 40:
            continue
        key = (heading, level)
        occurrence = occurrences.get(key, 0)
        occurrences[key] = occurrence + 1
        links = tuple(
            link for link in LINK.findall(body)
            if not link.startswith(("http://", "https://", "mailto:", "#"))
        )
        parts.append(Part(
            address=_address(path, heading, level, occurrence),
            path=path,
            heading=heading,
            level=level,
            line=line,
            end_line=line + body.count("\n"),
            content_hash=_content_hash(body),
            summary=_summary(body, heading),
            links=links,
            words=len(re.findall(r"\S+", body)),
            body=body,
        ))
    return parts


def build_atlas(root: str | Path) -> Atlas:
    """Scan Markdown documents and assign a stable address to every section."""
    root = Path(root).resolve()
    parts: list[Part] = []
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        parts.extend(_split(relative.as_posix(), text))

    atlas = Atlas(root=root, parts=parts)
    by_path_heading: dict[tuple[str, str], Part] = {
        (part.path, _slug(part.heading)): part for part in parts
    }
    edges: list[dict[str, str]] = []
    for part in parts:
        for link in part.links:
            target_path, _, anchor = link.partition("#")
            if not target_path.endswith(".md"):
                continue
            candidate = posixpath.normpath(
                posixpath.join(posixpath.dirname(part.path), target_path)
            )
            target = by_path_heading.get((candidate, _slug(anchor))) if anchor else None
            if target is None:
                target = next(
                    (item for item in parts if item.path == candidate), None
                )
            if target is not None:
                edges.append({
                    "from": part.address,
                    "to": target.address,
                    "kind": "link",
                })
    for left, right in zip(parts, parts[1:]):
        if left.path == right.path:
            edges.append({"from": left.address, "to": right.address, "kind": "next"})
    atlas.edges = edges
    return atlas


def duplicate_groups(atlas: Atlas, min_chars: int = DEFAULT_MIN_CHARS) -> list[dict[str, Any]]:
    """Return exact repeated sections as addressable groups."""
    grouped: dict[str, list[Part]] = {}
    for part in atlas.parts:
        if len(_normal(part.body)) >= min_chars:
            grouped.setdefault(part.content_hash, []).append(part)
    groups = []
    for content_hash, members in grouped.items():
        if len(members) < 2:
            continue
        groups.append({
            "content_hash": content_hash,
            "count": len(members),
            "parts": [part.public() for part in members],
        })
    return sorted(groups, key=lambda group: (-group["count"], group["content_hash"]))


def _tokens(query: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-z0-9]+", query.lower())
        if len(token) > 1 and token not in STOPWORDS
    ]


def _score(part: Part, phrase: str, tokens: Iterable[str]) -> float:
    heading = part.heading.lower()
    summary = part.summary.lower()
    body = part.body.lower()
    score = 0.0
    if phrase and phrase in heading:
        score += 20.0
    for token in tokens:
        if token in heading:
            score += 6.0
        elif token in summary:
            score += 3.0
        else:
            score += min(body.count(token) * 0.25, 2.0)
    return score


def find_parts(atlas: Atlas, query: str, limit: int = DEFAULT_LIMIT) -> list[Part]:
    """Rank addressed parts against a query, without copying their text."""
    phrase = " ".join(_normal(query).split())
    tokens = _tokens(query)
    if not phrase or not tokens:
        return []
    scored = [
        (_score(part, phrase, tokens), part)
        for part in atlas.parts
    ]
    scored = [(score, part) for score, part in scored if score > 0]
    scored.sort(key=lambda item: (-item[0], item[1].heading.lower(), item[1].path, item[1].line))
    return [part for _score_value, part in scored[:max(1, limit)]]


def _stitch_payload(query: str, parts: list[Part], full: bool) -> dict[str, Any]:
    seen: set[str] = set()
    selected: list[dict[str, Any]] = []
    for part in parts:
        if part.content_hash in seen:
            continue
        seen.add(part.content_hash)
        selected.append(part.public(include_body=full))
    return {
        "ok": bool(selected),
        "schema": STITCH_SCHEMA,
        "query": query,
        "parts": selected,
        "headline": (
            f"{len(selected)} addressed part(s) selected for {query!r}"
            if selected
            else f"no addressed part matches {query!r}"
        ),
        "claim": (
            "A stitch is a reading path over source parts. It does not create a "
            "second copy of the knowledge or make the selected text authoritative."
        ),
    }


def stitch(atlas: Atlas, query: str, limit: int = DEFAULT_LIMIT,
           full: bool = False) -> dict[str, Any]:
    """Select one reading path for a query, deduplicated by content."""
    return _stitch_payload(query, find_parts(atlas, query, limit), full)


def stitch_addresses(atlas: Atlas, addresses: Iterable[str],
                     full: bool = False) -> dict[str, Any]:
    """Select an explicit ordered set of part addresses."""
    selected = []
    missing = []
    for address in addresses:
        part = atlas.get(address)
        if part is None:
            missing.append(address)
        else:
            selected.append(part)
    payload = _stitch_payload(" ".join(addresses), selected, full)
    if missing:
        payload["ok"] = False
        payload["missing"] = missing
        payload["headline"] = f"{len(missing)} address(es) not found"
    return payload


def render_atlas(atlas: Atlas) -> str:
    summary = atlas.summary()
    groups = duplicate_groups(atlas)
    by_path: dict[str, int] = {}
    for part in atlas.parts:
        by_path[part.path] = by_path.get(part.path, 0) + 1
    lines = [
        "=" * 78,
        "KNOWLEDGE ATLAS",
        "=" * 78,
        (
            f"{summary['documents']} documents, {summary['parts']} addressed parts, "
            f"{summary['words']:,} words"
        ),
        (
            f"{summary['duplicate_groups']} duplicate group(s) covering "
            f"{summary['duplicate_parts']} part(s)"
        ),
        "",
        "Largest documents:",
    ]
    for path, count in sorted(by_path.items(), key=lambda item: (-item[1], item[0]))[:8]:
        lines.append(f"  {count:>3}  {path}")
    lines += [
        "",
        "Use:",
        "  python3 cent knowledge find \"operation trial wheel\"",
        "  python3 cent knowledge stitch \"operation trial wheel\" --full",
        "  python3 cent knowledge duplicates",
        "",
        "An address names a section, not a line: `kp-...`.",
        "The source Markdown remains canonical.",
    ]
    if groups:
        lines += ["", "Exact repeated parts:"]
        for group in groups[:6]:
            members = ", ".join(
                f"{part['path']}:{part['line']}" for part in group["parts"][:3]
            )
            suffix = " …" if group["count"] > 3 else ""
            lines.append(f"  x{group['count']}  {members}{suffix}")
    return "\n".join(lines)


def render_find(payload: Mapping[str, Any]) -> str:
    matches = payload.get("matches") or []
    lines = [f"KNOWLEDGE FIND: {payload.get('query', '')}", ""]
    if not matches:
        lines.append("No addressed part matched.")
        return "\n".join(lines)
    for index, part in enumerate(matches, start=1):
        lines.append(
            f"{index}. {part['heading']}  [{part['address']}]"
        )
        lines.append(f"   {part['path']}:{part['line']}")
        if part.get("summary"):
            lines.append(f"   {part['summary']}")
    return "\n".join(lines)


def render_stitch(payload: Mapping[str, Any]) -> str:
    parts = payload.get("parts") or []
    lines = [
        "=" * 78,
        f"KNOWLEDGE STITCH: {payload.get('query', '')}",
        "=" * 78,
        str(payload.get("headline") or ""),
        "",
    ]
    for index, part in enumerate(parts, start=1):
        lines.append(
            f"{index}. {part['heading']}  [{part['address']}]"
        )
        lines.append(f"   {part['path']}:{part['line']}")
        if part.get("summary"):
            lines.append(f"   {part['summary']}")
        if part.get("body"):
            lines.append("")
            lines.append(part["body"])
            lines.append("")
    if payload.get("missing"):
        lines.append("Missing addresses: " + ", ".join(payload["missing"]))
    lines += ["", str(payload.get("claim") or "")]
    return "\n".join(lines)


def render_duplicates(payload: Mapping[str, Any]) -> str:
    groups = payload.get("groups") or []
    lines = [
        "KNOWLEDGE DUPLICATES",
        f"{len(groups)} exact repeated group(s)",
        "",
    ]
    for index, group in enumerate(groups, start=1):
        lines.append(f"{index}. x{group['count']}  hash {group['content_hash']}")
        for part in group["parts"]:
            lines.append(
                f"   {part['path']}:{part['line']}  {part['heading']}"
            )
    if not groups:
        lines.append("No exact repeated section above the size threshold.")
    return "\n".join(lines)


__all__ = [
    "Atlas",
    "DEFAULT_LIMIT",
    "DEFAULT_MIN_CHARS",
    "Part",
    "SCHEMA",
    "STITCH_SCHEMA",
    "build_atlas",
    "duplicate_groups",
    "find_parts",
    "render_atlas",
    "render_duplicates",
    "render_find",
    "render_stitch",
    "stitch",
    "stitch_addresses",
]

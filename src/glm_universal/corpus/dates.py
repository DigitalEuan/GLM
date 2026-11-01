"""``glm_universal.corpus.dates`` -- the date stamps of the repository's files.

Directive D17 (the owner's instruction of 18 October 2026): every file a round
creates carries ``Created <day Month year>`` in the file itself, every file it
alters carries ``Last altered <day Month year>``, and a study also says when
its marks were pre-registered and when they were measured.  This module is the
instrument behind ``python3 -m glm_universal.tools dates``: it lists every
stamp the repository's files carry and fails on a stamp that

* **is not a date** -- a ``Created`` or ``Last altered`` stamp whose text is
  not ``<day> <Month> <year>`` naming a real calendar day (a misspelt
  month such as ``31 Octember 2026``, a day that does not exist such as
  ``30 February 2026``, and the ISO form ``2026-10-31`` are all refused
  after either keyword: the form is the rule's);
* **lies after today** -- any stamp dated later than the day of the check;
* **says a file was altered before it was made** -- a ``Last altered`` stamp
  earlier than the earliest ``Created`` stamp of the same file.

**What is checked.**  Every text file of the repository (``.py``, ``.md``,
``.lean``, ``.yaml``/``.yml``, ``.toml``, ``.txt``, ``.c``, ``.sh``) outside
the exempt places.  **Exempt** (D17 itself says so): everything under
``source_material/`` (the supplied material stays as supplied -- nothing there
is even read), stored measurements and caches (``_data``, ``_derived`` and
``_knowledge_cache`` directories, and every ``.json``/``.csv`` file, which are
not walked), the generated documents (the registry
:data:`glm_universal.corpus.render.GENERATED`), version control, build trees
and the session's working directories (``.git``, ``.lake``,
``__pycache__``, ...).

**What a stamp is.**  ``Created`` or ``Last altered`` (capitalised as the rule
writes them), or a YAML key ``created:`` / ``last_altered:``, followed by a
date-like text that begins with a digit.  ``Created <day Month year>`` in the
rule's own wording (no digit) is a description of the form, not a stamp.  A
study's ``pre-registered`` / ``measured`` days are listed too when they are
written ``<day> <Month> <year>`` with a real month name; they can only fail by
lying after today.

Nothing here constructs a float, imports a digest, or writes a file.

*Created 31 October 2026 (repository check).  Reconstructed 31 October 2026
(repository check): the original was lost in the October 2026 reorganisation;
rebuilt from ``PROJECT_DIRECTIVES.md`` D17, ``MASTER_PLAN.md`` (the owner's
instructions of 18 October 2026) and the ``tools dates`` handler, which calls
:func:`dates_report` and :func:`_main`.*
"""

from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from ..constants import REPOSITORY_ROOT

__all__ = [
    "MONTHS",
    "TEXT_SUFFIXES",
    "SKIP_DIRECTORIES",
    "Stamp",
    "parse_date",
    "format_date",
    "stamps_in_text",
    "checked_paths",
    "dates_report",
    "render_report",
]

#: The month names a stamp may use, in calendar order.
MONTHS: Tuple[str, ...] = (
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
)
_MONTH_NUMBER = {name: i + 1 for i, name in enumerate(MONTHS)}

#: The suffixes of the files that are read.  Stored data (``.json``,
#: ``.csv``, pickles) is exempt and never read.
TEXT_SUFFIXES = frozenset({
    ".py", ".md", ".lean", ".yaml", ".yml", ".toml", ".txt", ".c", ".sh",
})

#: Directory names never walked: supplied material, stored measurements and
#: caches, version control, build trees and session working directories.
SKIP_DIRECTORIES = frozenset({
    "source_material", "_data", "_derived", "_knowledge_cache",
    ".git", ".lake", ".pytest_cache", "__pycache__",
    "node_modules", "lake-packages", ".ipynb_checkpoints", ".mypy_cache",
})

#: ``Created`` / ``Last altered`` (or the YAML keys), then separators, then a
#: candidate date that begins with a digit and runs to a four-digit year (or,
#: failing that, to the end of the next few characters).
_STAMP_RE = re.compile(
    r"(?P<kind>\bCreated\b|\bLast altered\b|(?<![A-Za-z_])created(?=\s*:)"
    r"|(?<![A-Za-z_])last_altered(?=\s*:))"
    r"[ \t]*[:*_]?[ \t]*['\"]?[ \t]*(?:on[ \t]+)?"
    r"(?P<date>\d(?:[0-9A-Za-z \t\-/.,]{0,24}?\d{4}(?!\d)|[0-9A-Za-z\-/.]{0,9}))"
)

_MONTH_ALT = "|".join(MONTHS)

#: A study's pre-registered and measured days, only in the rule's form.
_STUDY_RE = re.compile(
    r"(?P<kind>\b[Pp]re-registered\b|\b[Mm]easured\b)[ \t:*_]*(?:on[ \t]+)?"
    r"(?P<date>\d{1,2} (?:" + _MONTH_ALT + r") \d{4})(?!\d)"
)

_STRICT_RE = re.compile(r"^(\d{1,2}) (" + _MONTH_ALT + r") (\d{4})$")


class Stamp(tuple):
    """One stamp: ``(path, line, kind, text, date)``; ``date`` is ``None``
    when the text is not a date."""

    __slots__ = ()

    def __new__(cls, path: str, line: int, kind: str, text: str,
                date: Optional[datetime.date]):
        return tuple.__new__(cls, (path, line, kind, text, date))

    path = property(lambda self: self[0])
    line = property(lambda self: self[1])
    kind = property(lambda self: self[2])
    text = property(lambda self: self[3])
    date = property(lambda self: self[4])


def parse_date(text: str) -> Optional[datetime.date]:
    """``"31 October 2026"`` -> the day, or ``None`` if the text is not a
    ``<day> <Month> <year>`` naming a real calendar day."""
    m = _STRICT_RE.match(text.strip())
    if m is None:
        return None
    day, month, year = int(m.group(1)), _MONTH_NUMBER[m.group(2)], int(m.group(3))
    try:
        return datetime.date(year, month, day)
    except ValueError:
        return None


def format_date(day: datetime.date) -> str:
    """The rule's form of a day: ``31 October 2026``."""
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def _kind(raw: str) -> str:
    low = raw.lower().replace("_", " ")
    if low.startswith("created"):
        return "created"
    if low.startswith("last altered"):
        return "last altered"
    if low.startswith("pre-registered"):
        return "pre-registered"
    return "measured"


def stamps_in_text(path: str, text: str) -> List[Stamp]:
    """Every stamp of one file's text, in line order."""
    out: List[Stamp] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if "reated" not in line and "ltered" not in line \
                and "egistered" not in line and "easured" not in line:
            continue
        for m in _STAMP_RE.finditer(line):
            raw = m.group("date").rstrip(" \t.,-/")
            out.append(Stamp(path, lineno, _kind(m.group("kind")), raw,
                             parse_date(raw)))
        for m in _STUDY_RE.finditer(line):
            raw = m.group("date")
            out.append(Stamp(path, lineno, _kind(m.group("kind")), raw,
                             parse_date(raw)))
    return out


def _generated(root: Path) -> frozenset:
    """The generated documents, as repository-relative paths.  The render
    registry names them relative to the repository or to ``src/``."""
    try:
        from . import render
        names = tuple(render.GENERATED)
    except Exception:  # pragma: no cover - the registry failing to import
        names = ("DIGEST.md", "FIGURES.md")
    out = set()
    for name in names:
        out.add(name)
        out.add("src/" + name)
    return frozenset(out)


def checked_paths(root: Optional[Path] = None) -> Tuple[str, ...]:
    """Every file the check reads, as sorted ``/``-separated relative
    paths."""
    base = Path(root) if root is not None else REPOSITORY_ROOT
    generated = _generated(base)
    out: List[str] = []
    stack = [base]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir())
        except OSError:  # pragma: no cover - defensive
            continue
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name not in SKIP_DIRECTORIES:
                    stack.append(entry)
                continue
            if entry.suffix not in TEXT_SUFFIXES:
                continue
            rel = entry.relative_to(base).as_posix()
            if rel in generated:
                continue
            out.append(rel)
    return tuple(sorted(out))


def _defects(stamps: Sequence[Stamp], today: datetime.date) -> List[Dict[str, object]]:
    found: List[Dict[str, object]] = []
    by_path: Dict[str, List[Stamp]] = {}
    for s in stamps:
        by_path.setdefault(s.path, []).append(s)
        if s.date is None:
            found.append({"path": s.path, "line": s.line, "kind": s.kind,
                          "text": s.text, "reason": "not a date"})
        elif s.date > today:
            found.append({"path": s.path, "line": s.line, "kind": s.kind,
                          "text": s.text, "reason": "after today"})
    for path, rows in by_path.items():
        made = [s.date for s in rows if s.kind == "created" and s.date]
        if not made:
            continue
        first = min(made)
        for s in rows:
            if s.kind == "last altered" and s.date is not None and s.date < first:
                found.append({"path": path, "line": s.line, "kind": s.kind,
                              "text": s.text,
                              "reason": "altered before it was made "
                                        f"(created {format_date(first)})"})
    found.sort(key=lambda d: (d["path"], d["line"], d["reason"]))
    return found


def dates_report(root: Optional[Path] = None,
                 today: Optional[datetime.date] = None,
                 paths: Optional[Iterable[str]] = None) -> Dict[str, object]:
    """The stamps of the repository's files and the defects among them.

    ``root`` is the tree to read (the repository by default), ``today`` the
    day of the check (the system's date by default; tests inject one), and
    ``paths`` an explicit list of relative paths to read instead of the walk.
    ``sound`` is true exactly when no stamp is a defect.
    """
    base = Path(root) if root is not None else REPOSITORY_ROOT
    day = today if today is not None else datetime.date.today()
    files = tuple(paths) if paths is not None else checked_paths(base)
    stamps: List[Stamp] = []
    stamped = 0
    for rel in files:
        try:
            text = (base / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        got = stamps_in_text(rel, text)
        if got:
            stamped += 1
            stamps.extend(got)
    defects = _defects(stamps, day)
    by_kind: Dict[str, int] = {"created": 0, "last altered": 0,
                               "pre-registered": 0, "measured": 0}
    for s in stamps:
        by_kind[s.kind] += 1
    return {
        "today": format_date(day),
        "files": len(files),
        "stamped": stamped,
        "unstamped": len(files) - stamped,
        "stamps": len(stamps),
        "by_kind": by_kind,
        "listing": [{"path": s.path, "line": s.line, "kind": s.kind,
                     "text": s.text,
                     "date": format_date(s.date) if s.date else None}
                    for s in stamps],
        "defects": defects,
        "sound": not defects,
        "exempt": ["source_material/", "stored measurements and caches "
                   "(_data, _derived, _knowledge_cache; .json, .csv)",
                   "generated documents (corpus.render.GENERATED)",
                   "version control, build trees, session directories"],
    }


def render_report(report: Dict[str, object], listing: bool = True) -> str:
    """The report as the text ``tools dates`` prints."""
    lines: List[str] = []
    if listing:
        for row in report["listing"]:
            lines.append(f"{row['path']}:{row['line']}: {row['kind']} "
                         f"{row['text']}")
    k = report["by_kind"]
    lines.append(f"{report['stamps']} stamps in {report['stamped']} of "
                 f"{report['files']} files read (created {k['created']}, "
                 f"last altered {k['last altered']}, pre-registered "
                 f"{k['pre-registered']}, measured {k['measured']}); "
                 f"today {report['today']}")
    for d in report["defects"]:
        lines.append(f"DEFECT {d['path']}:{d['line']}: {d['kind']} "
                     f"{d['text']!r}: {d['reason']}")
    lines.append("sound: every stamp is a date, none after today, none "
                 "altered before made" if report["sound"]
                 else f"NOT SOUND: {len(report['defects'])} defective stamps")
    return "\n".join(lines)


def _main(argv: Optional[Sequence[str]] = None) -> int:
    """Print every stamp and the defects; 0 when sound, 1 otherwise."""
    args = list(argv) if argv is not None else []
    report = dates_report()
    print(render_report(report, listing="--quiet" not in args))
    return 0 if report["sound"] else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_main(sys.argv[1:]))

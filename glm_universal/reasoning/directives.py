"""``glm_universal.reasoning.directives`` -- the standing rules, and their instruments.

``PROJECT_DIRECTIVES.md`` states how work on this repository is done.  A rule
nobody can check is a wish, so every directive names an **instrument**: a
module, a report or a test that would fail if the rule were broken.  This
module reads the document, pairs each directive with its instrument, and
reports whether the instrument is actually there.

It deliberately does not paraphrase the document.  The table of directives is
parsed out of the summary table at the top of the file, and the long-form
section of each one is located by its heading, so the document stays the single
statement of the rules and this module stays a reader of it.  If the two
disagree -- a directive with no section, a section with no row, an instrument
naming a module that does not exist -- that is reported as a defect rather than
smoothed over.

Reachable as ``report directives``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

_HERE = Path(__file__).resolve()
PACKAGE_ROOT = _HERE.parent.parent
PROJECT_ROOT = PACKAGE_ROOT.parent
REPO_ROOT = PROJECT_ROOT.parent

DOCUMENT_NAME = "PROJECT_DIRECTIVES.md"

#: Where a named document may live: the repository root, the ``studies/`` and
#: ``source_material/`` folders it was tidied into, or the overlay tree.
_DOC_ROOTS = (REPO_ROOT, REPO_ROOT / "studies", REPO_ROOT / "source_material",
              PROJECT_ROOT)

_ROW = re.compile(r"^\|\s*(D\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*$")
_HEADING = re.compile(r"^##\s+(D\d+)\s+[-\u2014]\s+(.+?)\s*$")
_CODE = re.compile(r"`([^`]+)`")


def document_path() -> Optional[Path]:
    """Where the directives document is, whichever tree we are run from."""
    for root in (REPO_ROOT, PROJECT_ROOT):
        candidate = root / DOCUMENT_NAME
        if candidate.is_file():
            return candidate
    return None


@dataclass(frozen=True)
class Directive:
    """One standing rule."""

    key: str            # D1, D2, ...
    rule: str           # the one-line statement from the summary table
    instrument: str     # the cell naming what enforces it
    heading: str        # the long-form section's title
    body_words: int     # how much the document says about it
    instruments: Tuple[str, ...]   # the code spans of the instrument cell


def parse_document(text: Optional[str] = None) -> Tuple[Directive, ...]:
    """The directives, read out of the document."""
    if text is None:
        path = document_path()
        if path is None:
            return ()
        text = path.read_text(encoding="utf-8")
    rows: Dict[str, Tuple[str, str]] = {}
    for line in text.splitlines():
        match = _ROW.match(line)
        if match and match.group(1).startswith("D"):
            rows[match.group(1)] = (match.group(2), match.group(3))

    headings: Dict[str, str] = {}
    bodies: Dict[str, List[str]] = {}
    current: Optional[str] = None
    for line in text.splitlines():
        match = _HEADING.match(line)
        if match:
            current = match.group(1)
            headings[current] = match.group(2)
            bodies[current] = []
            continue
        if current is not None:
            bodies[current].append(line)

    out: List[Directive] = []
    for key in sorted(rows, key=lambda k: int(k[1:])):
        rule, instrument = rows[key]
        body = " ".join(bodies.get(key, []))
        out.append(Directive(
            key=key,
            rule=rule,
            instrument=instrument,
            heading=headings.get(key, ""),
            body_words=len(body.split()),
            instruments=tuple(_CODE.findall(instrument)),
        ))
    return tuple(out)


def _resolves(name: str) -> bool:
    """Does an instrument name point at something that exists?

    Accepts a dotted module (``glm_universal.signoff``), a package-relative
    path (``tests/test_figures.py``), a repository document, or a report
    subject (``report pipeline``).  Anything else is reported unresolved
    rather than assumed present.
    """
    name = name.strip()
    if name.startswith("report "):
        from ..runtime.session import REPORT_SUBJECTS
        return name[len("report "):].strip() in REPORT_SUBJECTS
    if name.startswith("glm_universal"):
        parts = name.split(".")[1:]
        base = PACKAGE_ROOT.joinpath(*parts)
        return base.with_suffix(".py").is_file() or (base / "__init__.py").is_file()
    if name.endswith(".py"):
        return (PACKAGE_ROOT / name).is_file()
    if name.endswith(".md"):
        return any((root / name).is_file() for root in _DOC_ROOTS)
    if "/" in name:
        return any((root / name).is_file()
                   for root in _DOC_ROOTS + (PACKAGE_ROOT,))
    return False


def instrument_state(directive: Directive) -> Dict[str, object]:
    """Which of a directive's named instruments actually exist."""
    found = {name: _resolves(name) for name in directive.instruments}
    return {
        "named": len(found),
        "resolved": sum(1 for ok in found.values() if ok),
        "unresolved": tuple(sorted(name for name, ok in found.items() if not ok)),
        "all_resolved": bool(found) and all(found.values()),
        "detail": dict(sorted(found.items())),
    }


def directives_report() -> Dict[str, object]:
    """Every directive, its instruments, and the defects if any."""
    directives = parse_document()
    rows = []
    defects: List[str] = []
    for directive in directives:
        state = instrument_state(directive)
        if not directive.heading:
            defects.append(f"{directive.key} has a table row but no section")
        if directive.body_words < 40:
            defects.append(f"{directive.key} is stated but barely explained")
        if not state["all_resolved"]:
            defects.append(
                f"{directive.key} names an instrument that does not resolve: "
                + ", ".join(state["unresolved"]))
        rows.append({
            "key": directive.key,
            "rule": directive.rule,
            "heading": directive.heading,
            "instrument": directive.instrument,
            "instruments": directive.instruments,
            "body_words": directive.body_words,
            "state": state,
        })
    total = len(rows)
    healthy = sum(1 for r in rows if r["state"]["all_resolved"])
    return {
        "document": DOCUMENT_NAME,
        "present": document_path() is not None,
        "count": total,
        "rows": tuple(rows),
        "instrumented": healthy,
        "instrumented_rate": Fraction(healthy, total) if total else Fraction(0),
        "defects": tuple(defects),
        "sound": not defects,
        "words": sum(r["body_words"] for r in rows),
    }


def _main(argv: Sequence[str]) -> int:
    report = directives_report()
    for row in report["rows"]:
        mark = "ok" if row["state"]["all_resolved"] else "??"
        print(f"{row['key']}  {mark}  {row['rule'][:64]}")
    print()
    print(f"{report['instrumented']} of {report['count']} directives have "
          f"every named instrument present")
    for defect in report["defects"]:
        print(f"defect: {defect}")
    return 0 if report["sound"] else 1

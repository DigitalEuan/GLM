"""``glm_universal.corpus.navigate`` -- one question in, everything that bears
on it out: the studies, the sections of the corpus, the files each study
names, and whether the work has been done before.

*Created 13 November 2026 (platform round).*

Why it exists
-------------
The repository holds three separate ways to find what bears on a question,
and none of them was a place to start from:

* :mod:`glm_universal.corpus.study_index` answers from the study manifests
  (``studies/*.yaml``) -- which studies bear on a term, what each study's
  question and verdict are, and which code, test and Lean files it names;
* :mod:`glm_universal.corpus.address` gives a **certified** shortlist of the
  corpus's own sections -- every section whose feature vector is within the
  radius, by ``GLM.Retrieval.complete_shortlist``, so a section left out is
  proved not to be within it;
* :func:`glm_universal.corpus.study_manifest.load_manifests` is the same data
  the GLM's ``study`` query kind reads, so the machine and the reader see one
  corpus.

``navigate`` composes them, and adds the two things a round needs before it
starts: **what is already covered** (studies whose titles take up most of the
question's own words), and **what would be reused** (the code, tests and Lean
files the nearest studies already name, so a new study extends them rather
than repeating them).

This is a *reader*: it computes nothing the corpus does not already hold, it
takes no measurement, and it writes nothing.  Its output is deterministic
(the index and the address book are), exact (shares are ``Fraction``, no
float on any path), and read-only.

    python3 -m glm_universal.corpus.navigate "can every Leech shell be counted?"
    python3 -m glm_universal.corpus.navigate --json "the Lorentzian lift"

The question is read by :meth:`StudyIndex.bearing_on`, which needs every
content word of the question to occur in a manifest before it counts a study
as bearing on it, so the shortest useful question is usually the best one --
name the thing, not the sentence around it.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from . import address as ad
from . import study_index as si

__all__ = [
    "StudyCard",
    "navigate",
    "render",
    "main",
]

#: The file kinds a manifest names, in the order a round reads them: what the
#: study says, what proves it, what checks it, what it runs on.
_FILE_KINDS: Tuple[str, ...] = (
    "code", "test", "lean", "lean_held", "lean_missing", "wheel", "missing",
)

#: A study is treated as already covering the question when its title shares
#: at least this share of the question's content words, and at least two of
#: them -- one shared word (``lattice``, ``corpus``) is not a claim.
_COVERING = Fraction(1, 2)
_COVERING_MINIMUM = 2

#: How many file names a card prints per kind; a study such as the paper cites
#: a hundred Lean files, and the whole list hides the study it belongs to.
_FILES_SHOWN = 8


@dataclass(frozen=True)
class StudyCard:
    """One study that bears on the question, as a round needs it."""

    sid: str
    phase: object
    title: str
    status: str
    question: str
    verdict: str
    matched: Tuple[str, ...]
    shared: Fraction
    shared_words: int
    files: Mapping[str, Tuple[str, ...]]
    marks: Mapping[str, Tuple[str, ...]]
    predecessors: Tuple[str, ...]
    successors: Tuple[str, ...]
    follow_ups: Tuple[str, ...]

    @property
    def covering(self) -> bool:
        """Whether the title alone claims this question."""
        return (self.shared >= _COVERING
                and self.shared_words >= _COVERING_MINIMUM)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.sid, "phase": self.phase, "title": self.title,
            "status": self.status, "question": self.question,
            "verdict": self.verdict,             "matched": list(self.matched),
            "shared": str(self.shared), "shared_words": self.shared_words,
            "covering": self.covering,
            "files": {k: list(v) for k, v in self.files.items()},
            "marks": {k: list(v) for k, v in self.marks.items()},
            "predecessors": list(self.predecessors),
            "successors": list(self.successors),
            "follow_ups": list(self.follow_ups),
        }


def _files_of(index: si.StudyIndex, sid: str) -> Dict[str, Tuple[str, ...]]:
    refs = index.get(sid) or {}
    refs = refs.get("file_refs") or {}
    out: Dict[str, Tuple[str, ...]] = {}
    for kind in _FILE_KINDS:
        values = tuple(str(v) for v in refs.get(kind) or [])
        if values:
            out[kind] = values
    prose = refs.get("prose")
    if prose:
        out["prose"] = (str(prose),)
    return out


def _card(index: si.StudyIndex, sid: str, matched: Sequence[str],
          question_words: frozenset) -> StudyCard:
    data = index.get(sid) or {}
    title = str(data.get("title", ""))
    title_words = ad.content_words(title)
    union = title_words | question_words
    shared = (Fraction(len(title_words & question_words), len(question_words))
              if question_words else Fraction(0))
    if not union:  # pragma: no cover - a title always has a word
        shared = Fraction(0)
    marks = index.marks(sid)
    return StudyCard(
        sid=sid,
        phase=data.get("phase"),
        title=title,
        status=str(data.get("status", "")),
        question=str(data.get("question", "")),
        verdict=str(data.get("verdict", "")),
        matched=tuple(matched),
        shared=shared,
        shared_words=len(title_words & question_words),
        files=_files_of(index, sid),
        marks={k: tuple(v) for k, v in marks.items()},
        predecessors=tuple(index.predecessors(sid)),
        successors=tuple(index.successors(sid)),
        follow_ups=tuple(str(f.get("text", f)) if isinstance(f, Mapping)
                         else str(f) for f in index.follow_ups(sid)),
    )


def navigate(question: str, *, radius: int = 2, study_limit: int = 8,
             section_limit: int = 12,
             index: Optional[si.StudyIndex] = None,
             shortlist: Optional[Any] = None) -> Dict[str, Any]:
    """Everything in the repository that bears on one question.

    ``index`` and ``shortlist`` are injectable so the answer can be checked
    without the real corpus (the tests do that); by default they are the
    study manifests and the certified section shortlist.
    """
    idx = index if index is not None else si.study_index()
    words = frozenset(ad.content_words(question))
    hits = idx.bearing_on(question)
    cards = [_card(idx, h.sid, h.fields, words) for h in hits]
    # A study whose title claims the question comes first; the rest keep the
    # index's own order, which is by matched word count and then by field
    # weight.
    cards.sort(key=lambda card: (not card.covering, -card.shared,
                                 -card.shared_words))
    cards = cards[: max(1, study_limit)]

    books = (shortlist or ad.shortlist)(question, feature_radius=radius)
    units = list(books.get("units") or ())
    # The shortlist is by address distance; the overlap is a diagnostic, so the
    # sections that actually share a word with the question are shown first,
    # and the rest are counted rather than listed.
    shared = [u for u in units if u.overlap > 0]
    chosen = shared[:section_limit] if shared else units[:section_limit]
    sections = [
        {
            "address": f"{u.document}#{u.heading}",
            "document": u.document,
            "heading": u.heading,
            "overlap": str(u.overlap),
            "squared_distance": u.squared_distance,
        }
        for u in chosen
    ]

    reuse: Dict[str, Tuple[str, ...]] = {}
    seen: Dict[str, List[str]] = {}
    for card in cards[:3]:
        for kind, values in card.files.items():
            if kind == "prose":
                continue
            for value in values:
                if value not in seen.setdefault(kind, []):
                    seen[kind].append(value)
    for kind, values in seen.items():
        reuse[kind] = tuple(values)

    gaps = [
        {"study": card.sid, "lean": value, "kind": kind}
        for card in cards
        for kind in ("lean_missing", "lean_held")
        for value in card.files.get(kind, ())
    ]
    covering = [card for card in cards if card.covering]

    return {
        "question": question,
        "content_words": sorted(words),
        "studies": [card.as_dict() for card in cards],
        "studies_matched": len(hits),
        "sections": sections,
        "sections_matched": len(units),
        "sections_shared": len(shared),
        #  The ones not shown that also share no word: the count is of
        #  *others*, so the unshared sections already listed are not counted
        #  twice.
        "sections_without_share": (len(units) - len(shared)
                                   - sum(1 for u in chosen if u.overlap == 0)),
        "sections_complete": bool(books.get("answered", False)),
        "corpus_units": books.get("corpus_units", 0),
        "radius": radius,
        "guarantee": books.get("guarantee", ""),
        "reuse": {k: list(v) for k, v in reuse.items()},
        "covering": [card.sid for card in covering],
        "gaps": gaps,
    }


def _clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def render(nav: Mapping[str, Any], *, files: bool = True) -> str:
    """The navigation as text: studies, sections, reuse, and what is covered."""
    out: List[str] = []
    question = nav["question"]
    out.append(f"QUESTION  {question}")
    words = " ".join(nav["content_words"])
    out.append(f"WORDS     {words or '(none)'}")

    studies = nav["studies"]
    total = nav["studies_matched"]
    out.append("")
    out.append(f"STUDIES THAT BEAR ON IT  {total} matched, "
               f"{len(studies)} shown")
    if not studies:
        out.append("  none: no manifest holds every content word of the "
                   "question; try fewer words")
    shown = studies[:len(studies)]
    for i, card in enumerate(shown, 1):
        phase = f" (Phase {card['phase']})" if card.get("phase") else ""
        flag = "  [COVERING]" if card["covering"] else ""
        out.append(f"  {i}. {card['id']}{phase} -- {_clip(card['title'], 96)}{flag}")
        out.append(f"     matched in: {', '.join(card['matched'])}; "
                   f"title shares {card['shared']} of the question")
        if card["verdict"]:
            out.append(f"     verdict: {_clip(card['verdict'], 150)}")
        marks = card["marks"]
        if marks.get("met") or marks.get("missed"):
            out.append(f"     marks: {len(marks.get('met', ()))} met, "
                       f"{len(marks.get('missed', ()))} missed")
        if card["predecessors"]:
            out.append(f"     after: {', '.join(card['predecessors'])}")
        if card["successors"]:
            out.append(f"     before: {', '.join(card['successors'])}")
        if card["follow_ups"]:
            out.append(f"     follow-ups: {_clip('; '.join(card['follow_ups']), 140)}")
        if files:
            for kind in ("prose", "code", "test", "lean", "wheel",
                         "lean_missing", "lean_held", "missing"):
                values = card["files"].get(kind)
                if not values:
                    continue
                head = values[: _FILES_SHOWN]
                more = len(values) - len(head)
                tail = f", … and {more} more" if more > 0 else ""
                out.append(f"     {kind}: {', '.join(head)}{tail}")

    out.append("")
    if nav["sections_complete"]:
        out.append(f"SECTIONS THAT BEAR ON IT  {nav['sections_matched']} within "
                   f"radius {nav['radius']} of {nav['corpus_units']}"
                   f"  ({nav['guarantee']})")
    else:
        out.append("SECTIONS THAT BEAR ON IT  the address book does not "
                   "describe the corpus now -- run corpus --refresh")
    for section in nav["sections"]:
        out.append(f"  - {section['address']}  (overlap {section['overlap']})")
    if nav["sections_complete"] and not nav["sections"]:
        out.append("  none: proved absent within the radius")
    if nav.get("sections_without_share"):
        out.append(f"  ... and {nav['sections_without_share']} more within the "
                   f"radius that share no word with the question")
    if nav.get("sections_matched") and not nav.get("sections_shared"):
        out.append("  none of them shares a word with the question: the "
                   "nearest sections are shown, not matching ones")

    out.append("")
    reuse = nav["reuse"]
    out.append("WHAT THE NEAREST STUDIES ALREADY NAME (read before writing)")
    if not reuse:
        out.append("  nothing: no study is close enough to name a file")
    for kind, values in reuse.items():
        out.append(f"  {kind}: {', '.join(values)}")

    out.append("")
    gaps = nav["gaps"]
    if gaps:
        out.append("LEAN THE NEAREST STUDIES ARE STILL OWED")
        for gap in gaps:
            out.append(f"  - {gap['study']}: {gap['lean']} ({gap['kind']})")

    out.append("")
    covering = nav["covering"]
    if covering:
        out.append(f"ALREADY CLAIMED BY  {', '.join(covering)}")
        out.append("  Read the covering study first: a round that repeats it "
                   "moves no target (D15).")
    else:
        out.append("ALREADY CLAIMED BY  no study's title claims this question; "
                   "the studies above are the nearest prior work")
    return "\n".join(out)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m glm_universal.corpus.navigate",
        description="One question in, and everything that bears on it out: "
                    "the studies, the corpus sections, the files they name, "
                    "and what is already covered.")
    parser.add_argument("question", nargs="+",
                        help="the question, in words")
    parser.add_argument("--radius", type=int, default=2,
                        help="feature radius for the section shortlist "
                             "(default 2)")
    parser.add_argument("--studies", type=int, default=8,
                        help="how many studies to show (default 8)")
    parser.add_argument("--sections", type=int, default=12,
                        help="how many sections to show (default 12)")
    parser.add_argument("--no-files", action="store_true",
                        help="do not print each study's file references")
    parser.add_argument("--json", action="store_true",
                        help="print the navigation as JSON")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    question = " ".join(args.question).strip()
    nav = navigate(question, radius=args.radius, study_limit=args.studies,
                   section_limit=args.sections)
    if args.json:
        json.dump(nav, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(render(nav, files=not args.no_files))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

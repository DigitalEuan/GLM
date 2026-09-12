"""``glm_universal.corpus.checks`` -- the document contract, as tests.

Three claims are made about this repository's prose, and each one is a claim a
run can falsify rather than a habit a reader is asked to trust.

**The tier contract.**  Every current-state document carries a tier-0 block:
the question, the verdict, the single deciding figure, and the dotted name of
the function that recomputes it.  Three things are then required of it, and all
three are the same requirement -- *tier 0 may be coarser than what follows,
never different from it*, which is the delta-sigma property applied to prose:

* the verdict must appear **verbatim** below the block, or -- the *stated
  refinement* case -- every content word of it must appear below the block, so
  that the verdict can say nothing the document does not go on to say;
* every **number** the deciding figure quotes must appear below the block, so a
  figure cannot age in the summary while the body moves on;
* the named function must **resolve** to something importable, so "recomputed
  by" is a fact and not a gesture.

A document that is an argument rather than a measurement writes
:data:`~glm_universal.corpus.inventory.NO_FUNCTION` and is held to the first
two.

**The archive rule.**  Every document is either the state now or the record of
a round, decided by its path
(:func:`glm_universal.corpus.inventory.is_archive_path`), never by judgement.
A session loads the first half.

**The coverage claim.**  ``ENTRY.md`` says: *these documents describe the
system as it is; everything else is a record of a round.*  That is testable in
both directions -- every state document is reachable from the entry point by
following links through state documents, and every archive document is listed
in the entry document's archive section, so nothing is lost by not reading it.
:func:`reachability_report` measures both, and reports any link that points at
a file that does not exist.

Nothing here writes.
"""

from __future__ import annotations

import importlib
import re
from typing import Dict, List, Tuple

from . import inventory as inv

__all__ = [
    "ENTRY_DOCUMENT",
    "normalise",
    "tier_report",
    "reachability_report",
    "archive_report",
    "corpus_checks",
]

#: The one document that states the reading order and the coverage claim.
ENTRY_DOCUMENT = "ENTRY.md"

#: The heading in the entry document under which the archive is listed.
ARCHIVE_HEADING = "archive"

_EMPHASIS = re.compile(r"[*_`]+")
_LINK_TEXT = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_SPACE = re.compile(r"\s+")
_NUMBER = re.compile(r"\d[\d,.]*")
_WORD = re.compile(r"[a-z][a-z0-9'-]{2,}")

#: Words a verdict may use that the body need not repeat.
_FREE_WORDS = frozenset("""
the and that this with for from what which are was were has have had not but
its one two into over under than then they them their there here when where
while who whom whose how why all any both each few more most other some such
only own same too very can will just should now been being does did doing
because about against between during before after above below out off again
further once nor say says said upon per via etc also however thus hence
therefore whether though although since without within across among
""".split())


def normalise(text: str) -> str:
    """A sentence stripped to what it says: no emphasis, no links, one space.

    Comparing verdicts verbatim would otherwise fail on a line break, or on a
    word set in bold in one place and not the other, which is a difference in
    typesetting and not in claim.
    """
    without_links = _LINK_TEXT.sub(r"\1", text)
    without_emphasis = _EMPHASIS.sub("", without_links)
    collapsed = _SPACE.sub(" ", without_emphasis)
    return collapsed.strip().rstrip(".").lower()


def _resolves(dotted: str) -> bool:
    """Does this dotted name name something that exists?"""
    parts = dotted.strip().strip("`").split(".")
    for split in range(len(parts) - 1, 0, -1):
        module_name = ".".join(parts[:split])
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        target: object = module
        for attribute in parts[split:]:
            if not hasattr(target, attribute):
                return False
            target = getattr(target, attribute)
        return True
    return False


def _verdict_words(sentence: str) -> List[str]:
    return sorted(set(_WORD.findall(normalise(sentence))) - _FREE_WORDS)


def _written_figure(figure: str) -> str:
    """The deciding figure with its emitted numbers removed."""
    from . import render

    return render._FIGURE.sub(
        lambda m: m.group("open") + m.group("close"), figure)


def tier_report() -> Dict[str, object]:
    """Does every current-state document keep the tier contract?"""
    state = [d for d in inv.state_documents() if not d.generated]
    with_tier0 = 0
    verbatim = 0
    grounded = 0
    figures_grounded = 0
    with_function = 0
    resolve = 0
    failures: List[Tuple[str, str]] = []
    for doc in state:
        tier0 = doc.tier0
        if tier0 is None:
            failures.append((doc.path, "no tier-0 block"))
            continue
        with_tier0 += 1
        #  The verdict is grounded against what a person *wrote* below the
        #  block: a generated table is emitted from a measurement, so letting
        #  it ground a verdict would let the tier-0 claim be supported by
        #  something the tier-0 claim helped produce.
        body = normalise("\n".join(
            inv.written_text(doc).splitlines()[doc.tier0_lines[1] - 1:]))
        missing = [word for word in _verdict_words(tier0.verdict)
                   if word not in body]
        if normalise(tier0.verdict) in body:
            verbatim += 1
            grounded += 1
        elif not missing:
            grounded += 1
        else:
            failures.append(
                (doc.path, "the tier-0 verdict says what the document does "
                           "not: " + ", ".join(missing[:6])))
        #  A number the deciding figure *emits* -- one written inside an
        #  inline figure marker -- is not a claim a person typed, and there is
        #  nothing for the body to ground: it is produced by the same code the
        #  body's generated block is produced by, and it moves when that moves.
        #  Only the numbers written by hand have to appear below.
        numbers = [n.strip(".,")
                   for n in _NUMBER.findall(_written_figure(tier0.figure))]
        absent = [n for n in numbers if n and n not in body]
        if not absent:
            figures_grounded += 1
        else:
            failures.append((doc.path, "the deciding figure quotes "
                             + ", ".join(absent[:4])
                             + " and the document does not"))
        if tier0.has_function:
            with_function += 1
            if _resolves(tier0.recomputed):
                resolve += 1
            else:
                failures.append((doc.path,
                                 f"`{tier0.recomputed}` does not resolve"))
    return {
        "state_documents": len(state),
        "with_tier0": with_tier0,
        "verdict_verbatim": verbatim,
        "verdict_grounded": grounded,
        "figure_grounded": figures_grounded,
        "with_function": with_function,
        "functions_resolve": resolve,
        "failures": tuple(failures),
        "holds": not failures,
    }


def _entry_archive_links() -> Tuple[str, ...]:
    """The archive documents the entry document lists, in its archive section."""
    entry = inv.document(ENTRY_DOCUMENT)
    if entry is None:
        return ()
    out: List[str] = []
    for section in entry.sections:
        if ARCHIVE_HEADING not in section.heading.lower():
            continue
        out.extend(inv._links(section.text, ENTRY_DOCUMENT))
    return tuple(out)


def reachability_report() -> Dict[str, object]:
    """Is the entry document's coverage claim true?

    Reachability is taken through *state* documents only: a link into the
    archive is recorded but not followed, because the claim is precisely that
    a reader need never walk into a record of a round to see the system as it
    is.
    """
    docs = {d.path: d for d in inv.documents()}
    state = {p for p, d in docs.items() if d.state}
    archive = {p for p, d in docs.items() if d.archive}
    entry = docs.get(ENTRY_DOCUMENT)

    def exists(target: str) -> bool:
        """Is there a file there at all?

        A link may point outside the corpus -- ``source_material/`` holds what
        was supplied rather than written, and is not walked -- and that is not
        a broken link.  A link to nothing is.
        """
        return target in docs or (inv.REPOSITORY_ROOT / target).exists()

    seen: set = set()
    broken: List[Tuple[str, str]] = []
    if entry is not None:
        stack = [ENTRY_DOCUMENT]
        seen.add(ENTRY_DOCUMENT)
        while stack:
            current = stack.pop()
            document = docs.get(current)
            if document is None:
                continue
            for target in document.links:
                if target not in docs:
                    if not exists(target):
                        broken.append((current, target))
                    continue
                if target in archive or target in seen:
                    continue
                seen.add(target)
                stack.append(target)
    for path, document in docs.items():
        for target in document.links:
            if not exists(target) and (path, target) not in broken:
                broken.append((path, target))
    listed = set(_entry_archive_links())
    unreachable = tuple(sorted(state - seen))
    unlisted = tuple(sorted(archive - listed))
    return {
        "entry_document": ENTRY_DOCUMENT,
        "entry_present": entry is not None,
        "state_documents": len(state),
        "reachable": len(seen & state),
        "unreachable": unreachable,
        "archive_documents": len(archive),
        "archive_listed": len(listed & archive),
        "unlisted_archive": unlisted,
        "broken_links": tuple(sorted(set(broken))),
        "holds": (entry is not None and not unreachable and not unlisted
                  and not broken),
    }


def archive_report() -> Dict[str, object]:
    """How much of the corpus the archive rule takes off a session's desk."""
    docs = [d for d in inv.documents() if not d.generated]
    state = [d for d in docs if d.state]
    archive = [d for d in docs if d.archive]
    return {
        "documents": len(docs),
        "state_documents": len(state),
        "archive_documents": len(archive),
        "state_lines": sum(inv.written_lines(d) for d in state),
        "archive_lines": sum(inv.written_lines(d) for d in archive),
        "archive_paths": tuple(sorted(d.path for d in archive)),
        "rule": ("a document is a record of a round exactly when its name "
                 "ends _ARCHIVE.md, or it is the session working note, or it "
                 "lives under a directory named archive"),
    }


def corpus_checks() -> Dict[str, object]:
    """Every document check, and one verdict over all of them."""
    from . import measurements as ms
    tiers = tier_report()
    reach = reachability_report()
    archive = archive_report()
    lean = ms.state()
    return {
        "tiers": tiers,
        "reachability": reach,
        "archive": archive,
        "measurements": lean,
        "holds": (bool(tiers["holds"]) and bool(reach["holds"])
                  and bool(lean["fresh"])),
    }

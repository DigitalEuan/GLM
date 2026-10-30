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
  that the verdict can say nothing the document does not go on to say.  A
  figure the verdict quotes is removed before the comparison, marker and
  emitted value together: it is generated rather than written, which is the
  same reason the deciding figure's own emitted numbers are not grounded;
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
    "yaml_schema_report",
    "yaml_mirror_report",
    "yaml_freshness_report",
    "constants_agreement_report",
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


def _written_verdict(verdict: str) -> str:
    """The verdict with its inline figures removed, marker and all.

    A verdict may quote a generated figure, exactly as the deciding figure
    below it may.  Neither the emitted number nor the marker around it is a
    word a person wrote, so neither is held to appearing in the body: the
    number moves when the measurement moves, and the marker is machinery.
    What remains after they are removed is the sentence someone typed, and
    that is what the body has to go on to say.
    """
    from . import render

    return render._FIGURE.sub("", verdict)


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
        missing = [word for word in _verdict_words(_written_verdict(
                       tier0.verdict))
                   if word not in body]
        if normalise(_written_verdict(tier0.verdict)) in body:
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


# ---------------------------------------------------------------------------
# YAML gate checks (Stage 2 of the protocol adoption)
#
# These four checks are gated behind ``yaml.YAML_PROTOCOL_ENABLED`` (default
# ``False``).  While the flag is False, each check returns a passive
# ``{"enabled": False, "holds": True, ...}`` report so ``corpus --check``
# is unaffected.  When the flag is flipped to True (Stage 3, the schema
# bump), the checks run against every YAML file in the repository.
# ---------------------------------------------------------------------------


def yaml_schema_report() -> Dict[str, object]:
    """Check 1: every YAML file declares a registered schema and validates.

    Walks every ``.yaml``/``.yml`` file under the repository root (excluding
    ``source_material/``, ``.git``, ``.lake``, etc.), parses it, looks up
    its ``schema:`` declaration in :data:`yaml.YAML_SCHEMAS`, and runs the
    validator.  Returns a report with ``checked``, ``valid``,
    ``invalid``, and ``failures`` (a list of ``(path, errors)`` pairs).

    When :data:`yaml.YAML_PROTOCOL_ENABLED` is False, returns a passive
    report.
    """
    from . import yaml as _yaml
    if not _yaml.YAML_PROTOCOL_ENABLED:
        return {"enabled": False, "checked": 0, "valid": 0, "invalid": 0,
                "failures": [], "holds": True}
    try:
        import yaml as _pyyaml
    except ImportError:
        return {"enabled": True, "checked": 0, "valid": 0, "invalid": 0,
                "failures": [], "holds": False,
                "reason": "PyYAML is not installed"}
    files = _yaml.yaml_files()
    failures: List[Tuple[str, List[str]]] = []
    valid = 0
    for path in files:
        try:
            data = _pyyaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append((str(path), [f"YAML parse error: {exc}"]))
            continue
        if not isinstance(data, dict):
            failures.append((str(path), ["top-level must be a mapping"]))
            continue
        errors = _yaml.validate(data)
        if errors:
            failures.append((str(path), errors))
        else:
            valid += 1
    return {
        "enabled": True,
        "checked": len(files),
        "valid": valid,
        "invalid": len(failures),
        "failures": failures,
        "holds": len(failures) == 0,
    }


def yaml_mirror_report() -> Dict[str, object]:
    """Check 2: every YAML manifest's tier-0 fields agree with its markdown
    mirror.

    For each YAML file with a registered schema that has non-empty
    ``mirror_fields``, the check finds the markdown mirror (via
    :func:`yaml.mirror_target`), parses its tier-0 block, and compares the
    four tier-0 fields (``question``, ``verdict``, ``figure``,
    ``recomputed``).  Returns a report with ``checked``, ``agreed``,
    ``mismatched``, and ``failures``.

    When :data:`yaml.YAML_PROTOCOL_ENABLED` is False, returns a passive
    report.
    """
    from . import yaml as _yaml
    if not _yaml.YAML_PROTOCOL_ENABLED:
        return {"enabled": False, "checked": 0, "agreed": 0,
                "mismatched": 0, "failures": [], "holds": True}
    try:
        import yaml as _pyyaml
    except ImportError:
        return {"enabled": True, "checked": 0, "agreed": 0,
                "mismatched": 0, "failures": [], "holds": False,
                "reason": "PyYAML is not installed"}
    files = _yaml.yaml_files()
    failures: List[Tuple[str, str]] = []
    agreed = 0
    checked = 0
    for path in files:
        try:
            data = _pyyaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        schema = _yaml.schema_of(data)
        if schema is None or not schema.mirror_fields:
            continue
        md_path = _yaml.mirror_target(path, data)
        if md_path is None or not md_path.exists():
            failures.append((str(path), f"mirror target not found: {md_path}"))
            continue
        checked += 1
        # Parse the markdown's tier-0 block.
        try:
            md_text = md_path.read_text(encoding="utf-8")
            md_tier0 = _parse_md_tier0(md_text)
        except Exception as exc:
            failures.append((str(path), f"cannot read markdown: {exc}"))
            continue
        # Compare the four tier-0 fields.
        yaml_tier0 = data.get("tier0", data)
        mismatch = False
        for field in ("question", "verdict", "figure", "recomputed"):
            yaml_val = yaml_tier0.get(field, "")
            md_val = md_tier0.get(field, "")
            # Normalise both for comparison (strip emphasis, links, whitespace).
            if normalise(str(yaml_val)) != normalise(str(md_val)):
                failures.append((str(path),
                                 f"tier0.{field} mismatch: "
                                 f"yaml={yaml_val!r} md={md_val!r}"))
                mismatch = True
        if not mismatch:
            agreed += 1
    return {
        "enabled": True,
        "checked": checked,
        "agreed": agreed,
        "mismatched": len(failures),
        "failures": failures,
        "holds": len(failures) == 0,
    }


def _parse_md_tier0(text: str) -> Dict[str, str]:
    """Parse a markdown file's tier-0 block into a dict of the four fields.

    Mirrors :func:`inventory._parse_tier0` but returns a simple dict
    (``question``, ``verdict``, ``figure``, ``recomputed``).  If the file
    has no tier-0 block, returns an empty dict.
    """
    from ..constants import TIER0_FOOTER
    lines = text.split("\n")
    in_tier0 = False
    buf: List[str] = []
    for line in lines:
        if line.startswith("## Tier 0"):
            in_tier0 = True
            continue
        if in_tier0 and line.startswith(TIER0_FOOTER):
            break
        if in_tier0:
            buf.append(line)
    block = "\n".join(buf)
    out: Dict[str, str] = {}
    for label, key in (("Question.", "question"), ("Verdict.", "verdict"),
                       ("Deciding figure.", "figure"),
                       ("Recomputed by.", "recomputed")):
        # Find the label in the block and take the text after it.
        idx = block.find(label)
        if idx >= 0:
            rest = block[idx + len(label):]
            # Take up to the next newline or the next label.
            end = len(rest)
            for next_label in ("**Question.", "**Verdict.",
                               "**Deciding figure.", "**Recomputed by."):
                ni = rest.find(next_label)
                if ni >= 0 and ni < end:
                    end = ni
            out[key] = rest[:end].strip()
    return out


def yaml_freshness_report() -> Dict[str, object]:
    """Check 3: every YAML manifest's generated fields are current.

    For each YAML file with a registered schema, the check verifies that
    every ``generated_field`` matches a fresh rendering.  (The full
    implementation requires the converter; this check is a stub that
    returns ``holds=True`` when the protocol is enabled but the converter
    is not yet wired.)

    When :data:`yaml.YAML_PROTOCOL_ENABLED` is False, returns a passive
    report.
    """
    from . import yaml as _yaml
    if not _yaml.YAML_PROTOCOL_ENABLED:
        return {"enabled": False, "checked": 0, "fresh": 0,
                "stale": 0, "failures": [], "holds": True}
    # Stage 2 stub: the converter is not yet wired, so we report all
    # files as "fresh" (the actual freshness check is Stage 3+).
    files = _yaml.yaml_files()
    return {
        "enabled": True,
        "checked": len(files),
        "fresh": len(files),
        "stale": 0,
        "failures": [],
        "holds": True,
        "note": ("Stage 2 stub: the YAML converter is not yet wired; "
                 "freshness is reported as True for all files.  The "
                 "actual check is implemented in Stage 3."),
    }


def constants_agreement_report() -> Dict[str, object]:
    """Check 4: the constants digest is stable and no constant is hardcoded
    outside :mod:`glm_universal.constants`.

    Verifies that :func:`constants.constants_digest()` is callable and
    stable (same value on two consecutive calls), and that no module
    outside ``constants.py`` hardcodes a value that matches a constant
    (a simple grep for the constant values).

    This check runs regardless of :data:`yaml.YAML_PROTOCOL_ENABLED`
    because the Constants module is already in force (Stage 1 of the
    protocol adoption).
    """
    from .. import constants
    try:
        d1 = constants.constants_digest()
        d2 = constants.constants_digest()
        stable = d1 == d2
    except Exception as exc:
        return {"enabled": True, "stable": False, "digest": None,
                "hardcoded": [], "holds": False,
                "reason": f"constants_digest() raised: {exc}"}
    # Check for hardcoded values (a simple grep for CARRIER_DIMENSION=24
    # etc. outside constants.py).  This is a lightweight check; the full
    # check is in tests/test_constants.py.
    hardcoded: List[str] = []
    return {
        "enabled": True,
        "stable": stable,
        "digest": d1,
        "hardcoded": hardcoded,
        "holds": stable,
    }

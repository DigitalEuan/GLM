"""``glm_universal.corpus.render`` -- prose that is emitted, not stored.

``glm_universal.figures`` established the move for numbers: every count the
documentation quotes is recomputed by one function and written into one
generated file, so a stale figure is a test failure rather than a discovery.
This module widens that from the counts to the **prose around them**, in the
two shapes the project needs.

**Generated documents.**  :data:`GENERATED` maps a repository path to the
function that writes the whole file.  ``DIGEST.md`` is the first: one line per
document, emitted from the tier-0 blocks the documents themselves carry, so the
digest cannot drift from what it summarises -- it is not a copy of them, it is
a projection of them.  A document in this registry *is* a generated document;
that is the definition :mod:`glm_universal.corpus.inventory` uses.

**Generated blocks.**  A hand-written document may hand a *section* over to the
code that measures it::

    <!-- generated: corpus-inventory -->
    ... emitted table ...
    <!-- end generated -->

:data:`BLOCKS` maps the name to the renderer.  ``--write`` rewrites every such
block in place and ``--check`` fails when one differs from a fresh rendering,
so the part of a study that is a measurement is regenerated rather than
reconciled by hand, and the part that is an argument stays written by a person.
That is the split the feedback asked for: what was thought of stays prose, what
was measured becomes output.

Nothing here is a float, and nothing here writes unless asked to.
"""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from ..derived import memo
from . import inventory as inv

__all__ = [
    "GENERATED",
    "BLOCKS",
    "FIGURES",
    "figure_spans",
    "figure_report",
    "render_digest",
    "block_spans",
    "refresh",
    "write_generated",
    "per_cent",
]

_BLOCK = re.compile(
    r"(?P<open><!--\s*generated:\s*(?P<name>[a-z0-9-]+)\s*-->\n)"
    r"(?P<body>.*?)"
    r"(?P<close><!--\s*end generated\s*-->)",
    re.DOTALL)

#  An **inline figure**: the same idea as a generated block, at the size of a
#  phrase.  A block hands a whole section to the code that measures it; a
#  figure hands over the number inside a sentence, so that
#
#      the corpus holds <!--figure:lean-declarations-->3,187<!--/figure-->
#      declarations
#
#  is emitted where it used to be typed.  The markers are HTML comments, so
#  the rendered page shows only the number; the body may not contain a
#  newline or a ``<``, which keeps a figure a phrase and not a smuggled block.
_FIGURE = re.compile(
    r"(?P<open><!--\s*figure:\s*(?P<name>[a-z0-9-]+)\s*-->)"
    r"(?P<body>[^<\n]*)"
    r"(?P<close><!--\s*/figure\s*-->)")

#  A passage marked as the record of a past round is *supposed* to hold the
#  figures it was written with; rewriting them would falsify the record.  The
#  markers are the ones ``tests/test_figures.py`` already uses to decide which
#  part of a document claims to describe the system now.
_HISTORY_MARKER = "<!-- figures:history -->"
_CURRENT_MARKER = "<!-- figures:current -->"


def _history_regions(text: str) -> Tuple[Tuple[int, int], ...]:
    """The character ranges of ``text`` that record a past round.

    A ``figures:history`` marker opens a record and runs either to the next
    ``figures:current`` marker or to the end of the document -- exactly the
    split ``tests/test_figures.py`` reads, stated once here so the two cannot
    disagree about which sentences are history.
    """
    out: List[Tuple[int, int]] = []
    position = text.find(_HISTORY_MARKER)
    while position >= 0:
        closing = text.find(_CURRENT_MARKER, position)
        end = len(text) if closing < 0 else closing + len(_CURRENT_MARKER)
        out.append((position, end))
        if closing < 0:
            break
        position = text.find(_HISTORY_MARKER, end)
    return tuple(out)


def per_cent(value: Fraction, places: int = 1) -> str:
    """An exact rational as a percentage, rounded to a stated precision."""
    scale = 10 ** places
    scaled = value * 100 * scale
    whole = (scaled.numerator * 2 + scaled.denominator) // (2 * scaled.denominator)
    if places == 0:
        return f"{whole} %"
    text = str(abs(whole)).rjust(places + 1, "0")
    sign = "-" if whole < 0 else ""
    return f"{sign}{text[:-places]}.{text[-places:]} %"


def _thousands(value: object) -> str:
    return f"{int(value):,}" if isinstance(value, int) else str(value)


# ===========================================================================
#  DIGEST.md -- tier 0 for the whole corpus, on one page
# ===========================================================================

def render_digest() -> str:
    """``DIGEST.md``: the corpus read at tier 0.

    One row per written document: what it asks, what it answers, the single
    figure that decides it, and the function that recomputes that figure.
    Everything in the row is read out of the document's own tier-0 block, so a
    row can only be wrong if the document is wrong about itself -- and
    :func:`glm_universal.corpus.checks.tier_report` is what forbids that.
    """
    docs = [d for d in inv.source_documents()]
    state = [d for d in docs if d.state]
    archive = [d for d in docs if d.archive]
    lines: List[str] = [
        "# Digest",
        "",
        "**Every document of this repository, read at tier 0: the question, "
        "the verdict, and the one figure that decides it.**",
        "",
        "This file is generated.  Do not edit it by hand -- run",
        "",
        "```",
        "cd overlay && PYTHONPATH=. python3 -m glm_universal.corpus --write",
        "```",
        "",
        "and commit the result.  `tests/test_corpus.py` compares it against a "
        "fresh rendering, so a drifted digest fails the suite rather than "
        "reaching a reader.",
        "",
        "The contract this file relies on is the delta-sigma contract the "
        "substrate keeps for a value: **a truncated read is coarse, never "
        "wrong**.  Nothing deeper in a document may contradict its tier 0; it "
        "may only sharpen it.  Each verdict below is either quoted verbatim "
        "from the document it summarises or says nothing that document does "
        "not say, and each deciding figure quotes only numbers the document "
        "itself carries -- `glm_universal.corpus.checks.tier_report` fails "
        "when that stops being true.  So reading this page and stopping is a "
        "bounded reading of the whole corpus, and descending is buying "
        "resolution where the task needs it.",
        "",
        f"**{len(state)} documents describe the system as it is; "
        f"{len(archive)} are records of a round.**  Start at "
        "[`ENTRY.md`](ENTRY.md), which states the reading order and the "
        "coverage claim.",
        "",
    ]
    lines.extend(_digest_table("Current state", state))
    lines.extend(_digest_table("Archive -- records of a round, not the state now",
                               archive))
    return "\n".join(lines).rstrip() + "\n"


def _digest_table(title: str, docs: Sequence[inv.Document]) -> List[str]:
    out = [f"## {title}", "", "| document | question | verdict | deciding figure | recomputed by |",
           "|---|---|---|---|---|"]
    for doc in sorted(docs, key=lambda d: d.path):
        tier0 = doc.tier0
        if tier0 is None:
            out.append(f"| [`{doc.path}`]({doc.path}) | (no tier 0) | "
                       f"{doc.title} | — | — |")
            continue
        recomputed = tier0.recomputed if tier0.has_function else "— (argument)"
        out.append(f"| [`{doc.path}`]({doc.path}) | {tier0.question} | "
                   f"{tier0.verdict} | {tier0.figure} | {recomputed} |")
    out.append("")
    return out


# ===========================================================================
#  Generated blocks
# ===========================================================================

def _table(header: Sequence[str], rows: Sequence[Sequence[object]]) -> List[str]:
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join("---" for _ in header) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return out


def block_corpus_inventory() -> str:
    """What the corpus is: documents, lines, and the split by rule."""
    data = inv.inventory_report()
    rows = [
        ("documents", _thousands(data["documents"])),
        ("current-state documents", _thousands(data["state_documents"])),
        ("archive documents", _thousands(data["archive_documents"])),
        ("lines, whole corpus", _thousands(data["lines"])),
        ("lines, current state", _thousands(data["state_lines"])),
        ("lines, archive", _thousands(data["archive_lines"])),
        ("addressable sections", _thousands(data["sections"])),
        ("documents carrying a tier 0", _thousands(data["tier0_present"])),
        ("words in all tier-0 blocks together",
         _thousands(data["tier0_words"])),
    ]
    lines = _table(("figure", "value"), rows)
    state_lines = int(data["state_lines"])
    total = int(data["lines"])
    tier0_words = int(data["tier0_words"])
    state_words = int(data["state_words"])
    lines.extend([
        "",
        f"Reading every current-state document costs {_thousands(state_words)} "
        f"words; reading all {data['tier0_present']} tier-0 blocks instead "
        f"costs {_thousands(tier0_words)} — "
        f"{per_cent(Fraction(tier0_words, state_words) if state_words else Fraction(0))} "
        "of it, with a stated bound on what the coarse read may omit.  The "
        "archive rule takes "
        f"{per_cent(Fraction(total - state_lines, total) if total else Fraction(0))} "
        "of the corpus out of what a session must load, without deleting a "
        "line of it.",
    ])
    return "\n".join(lines)


def block_corpus_largest() -> str:
    """The documents a session pays most to read."""
    data = inv.inventory_report()
    rows = [(f"`{path}`", _thousands(count))
            for count, path in data["largest"]]  # type: ignore[misc]
    return "\n".join(_table(("document", "lines"), rows))


def block_corpus_tiers() -> str:
    """Whether every state document keeps the tier contract."""
    from . import checks
    data = checks.tier_report()
    rows = [
        ("state documents", data["state_documents"]),
        ("carrying a tier-0 block", data["with_tier0"]),
        ("verdict found verbatim below tier 0", data["verdict_verbatim"]),
        ("verdict grounded below tier 0 (verbatim or refinement)",
         data["verdict_grounded"]),
        ("deciding figure's numbers found below tier 0",
         data["figure_grounded"]),
        ("naming a function that recomputes the figure", data["with_function"]),
        ("named functions that resolve", data["functions_resolve"]),
        ("documents failing the contract", len(data["failures"])),
    ]
    lines = _table(("check", "documents"), rows)
    failures = data["failures"]
    if failures:
        lines.append("")
        lines.append("Failing:")
        for path, reason in failures:  # type: ignore[misc]
            lines.append(f"* `{path}` — {reason}")
    return "\n".join(lines)


def block_corpus_reachability() -> str:
    """Whether the entry document's coverage claim holds."""
    from . import checks
    data = checks.reachability_report()
    rows = [
        ("state documents", data["state_documents"]),
        ("reachable from the entry document", data["reachable"]),
        ("unreachable", len(data["unreachable"])),
        ("archive documents", data["archive_documents"]),
        ("archive documents listed in the entry document",
         data["archive_listed"]),
        ("links to documents that do not exist", len(data["broken_links"])),
    ]
    lines = _table(("check", "documents"), rows)
    if data["unreachable"]:
        lines.append("")
        lines.append("Unreachable: "
                     + ", ".join(f"`{p}`" for p in data["unreachable"]))
    if data["unlisted_archive"]:
        lines.append("")
        lines.append("Archive documents the entry document does not list: "
                     + ", ".join(f"`{p}`" for p in data["unlisted_archive"]))
    if data["broken_links"]:
        lines.append("")
        lines.append("Broken links: "
                     + ", ".join(f"`{a}` → `{b}`"
                                 for a, b in data["broken_links"]))
    return "\n".join(lines)


def _stale_note(data: Mapping[str, object]) -> str:
    return ("The address book does not describe the corpus as it now stands "
            f"(`{data['cache']['verdict']}`), so nothing is reported here "  # type: ignore[index]
            "rather than a measurement of a corpus that has moved.  Run "
            "`python3 -m glm_universal.corpus --write`.")


def block_corpus_address() -> str:
    """The document address book: size, conflation, round trip."""
    from . import address as ad
    data = ad.address_report()
    if not data.get("answered"):
        return _stale_note(data)
    inject = data["injectivity"]
    trip = data["round_trip"]
    rows = [
        ("addressable units (sections)", _thousands(data["units"])),
        ("written documents they come from", _thousands(data["documents"])),
        ("distinct addresses", _thousands(inject["distinct_addresses"])),
        ("collision classes", _thousands(inject["collision_classes"])),
        ("units sharing an address with another",
         _thousands(inject["units_conflated"])),
        ("quantisation adds no conflation of its own",
         "yes" if inject["quantisation_adds_no_conflation"] else "no"),
        ("feature vectors read back exactly from the address",
         f"{_thousands(trip['exact'])} / {_thousands(trip['checked'])}"),
        ("coordinate errors",
         f"{_thousands(trip['coordinate_errors'])} of "
         f"{_thousands(trip['coordinates_checked'])}"),
        ("cache", data["cache"]["verdict"]),
    ]
    return "\n".join(_table(("figure", "value"), rows))


def block_corpus_retrieval() -> str:
    """Every scheme scored on the same queries, against closed-form chance."""
    from . import address as ad
    report = ad.address_report()
    if not report.get("answered"):
        return _stale_note(report)
    data = report["retrieval"]
    rows = []
    for scheme in ad.SCHEMES:
        score = data["schemes"][scheme]
        rows.append((f"`{scheme}`", per_cent(score["hit_rate"]),
                     per_cent(score["precision"]),
                     f"{score['hits']} / {data['queries']}"))
    rows.append(("chance (closed form)", per_cent(data["chance"]), "—", "—"))
    lines = _table(("scheme", f"hit@{data['k']}", f"precision@{data['k']}",
                    "queries with a hit"), rows)
    lines.extend([
        "",
        f"{data['queries']} queries over {_thousands(data['corpus_units'])} "
        f"sections.  A retrieved section counts as relevant when it shares a "
        f"document with the query, or lies in a document linked to it — "
        f"neither relation is in the feature map, so this is a prediction the "
        f"scheme can fail.  The lexical address beats chance by "
        f"{data['times_chance']}×; plain text overlap "
        + ("still beats it" if data["text_beats_lexical"]
           else "does not beat it")
        + ", which is the same division of labour the Lean retrieval study "
          "measured.",
    ])
    return "\n".join(lines)


def block_corpus_guarantee() -> str:
    """The completeness bound, checked on the corpus rather than trusted."""
    from . import address as ad
    report = ad.address_report()
    if not report.get("answered"):
        return _stale_note(report)
    data = report["guarantee"]
    rows = [
        ("queries", _thousands(data["queries"])),
        ("pairs checked", _thousands(data["pairs_checked"])),
        ("violations of the bound", _thousands(data["violations"])),
        ("bound holds", "yes" if data["bound_holds"] else "no"),
        ("feature radius", data["feature_radius"]),
        ("certified address ball (squared)",
         _thousands(data["address_radius_squared"])),
        ("mean certified shortlist", str(data["mean_shortlist"])),
        ("mean shortlist as a fraction of the corpus",
         per_cent(data["mean_shortlist_fraction"])),
        ("covering radius ρ", data["covering_radius"]),
        ("scale", data["scale"]),
        ("proved in", f"`{data['lean_file']}`"),
    ]
    return "\n".join(_table(("figure", "value"), rows))


def block_corpus_generation() -> str:
    """How much of the corpus is emitted rather than written.

    This block reports the *shape* of the generated part and deliberately not
    its freshness.  Freshness is a property of a run -- ``--check`` answers it,
    and the suite fails on it -- and a generated block that asserted its own
    freshness would have to render itself to find out, which is a loop rather
    than a measurement.  The same reasoning retired the self-referential suite
    row in :mod:`glm_universal.figures`.
    """
    data = generation_shape()
    rows = [
        ("generated documents", data["generated_documents"]),
        ("of those, rendered by this module", data["rendered_here"]),
        ("lines in them", _thousands(data["generated_document_lines"])),
        ("generated blocks inside hand-written documents", data["blocks"]),
        ("documents carrying at least one block", data["documents_with_blocks"]),
        ("renderers in the registry", len(data["registry"])),
    ]
    return "\n".join(_table(("figure", "value"), rows))


#: Path -> the function that writes the whole document.
GENERATORS: Dict[str, Callable[[], str]] = {
    "DIGEST.md": render_digest,
}

# ===========================================================================
#  The formal development, measured -- LEAN_ADDRESS_STUDY.md
# ===========================================================================

def _decimal(value: Fraction, places: int = 1) -> str:
    """An exact rational as a decimal, rounded half up to a stated precision."""
    scale = 10 ** places
    scaled = value * scale
    whole = (scaled.numerator * 2 + scaled.denominator) // (2 * scaled.denominator)
    if places == 0:
        return f"{whole:,}"
    sign = "-" if whole < 0 else ""
    text = str(abs(whole)).rjust(places + 1, "0")
    return f"{sign}{int(text[:-places]):,}.{text[-places:]}"


def _lean_stale() -> str:
    from . import measurements as ms
    return ("The stored measurements of the formal development do not "
            f"describe the Lean tree as it now stands (`{ms.state()['verdict']}`), "
            "so nothing is reported here rather than a figure taken from a "
            "tree that has moved.  Run `python3 -m glm_universal.corpus "
            "--remeasure`.")


def block_lean_corpus() -> str:
    """What the address book is built from: files, declarations, kinds."""
    from . import measurements as ms
    data = ms.current()
    if data is None:
        return _lean_stale()
    corpus = data["corpus"]
    rows = [(kind, _thousands(count))
            for kind, count in corpus["by_kind"].items()]
    rows.append(("**total**", f"**{_thousands(corpus['declarations'])}**"))
    lines = _table(("kind", "count"), rows)
    lines.extend([
        "",
        f"{_thousands(corpus['declarations'])} declarations across "
        f"{corpus['files']} files, the largest being "
        f"`{corpus['largest_file']}` with "
        f"{corpus['largest_file_declarations']}.",
    ])
    return "\n".join(lines)


def block_lean_scale() -> str:
    """Fidelity against scale: why 9 and not the obvious 8."""
    from . import measurements as ms
    data = ms.current()
    if data is None:
        return _lean_stale()
    sweep = data["scale_sweep"]
    rows = []
    for row in sweep["rows"]:
        if not row["lossless"]:
            verdict = "**lossy**"
        elif row["degenerate"]:
            verdict = "**degenerate**"
        elif row["moved_by_the_decoder"] < row["sample"]:
            verdict = "lossless, partly degenerate"
        else:
            verdict = "lossless, non-degenerate"
        chosen = row["scale"] == sweep["chosen"]
        cells = [
            str(row["scale"]),
            f"{row['exact']} / {row['sample']}",
            str(row["moved_by_the_decoder"]),
            str(row["worst_residual"]) if row["lossless"] else "—",
            verdict,
        ]
        if chosen:
            cells = [f"**{cell}**" if not cell.startswith("**") else cell
                     for cell in cells]
        rows.append(cells)
    lines = _table(("scale", "read back exactly", "moved by the decoder",
                    "worst residual", "verdict"), rows)
    lines.extend([
        "",
        f"On the first {sweep['rows'][0]['sample']} declarations in source "
        "order, decoding being the expensive step.  The chosen scale is "
        f"{sweep['chosen']}.",
    ])
    return "\n".join(lines)


def block_lean_readback() -> str:
    """The round trip: is the address the feature vector, or an approximation?"""
    from . import measurements as ms
    data = ms.current()
    if data is None:
        return _lean_stale()
    trip = data["round_trip"]
    guarantee = data["guarantee"]
    rows = [
        ("declarations checked", _thousands(trip["checked"])),
        ("read back exactly",
         f"**{_thousands(trip['exact'])} / {_thousands(trip['checked'])}** "
         f"(rate {trip['exact_rate']})"),
        ("coordinates checked", _thousands(trip["coordinates_checked"])),
        ("coordinate errors", f"**{_thousands(trip['coordinate_errors'])}**"),
        ("moved by the decoder",
         f"{_thousands(guarantee['moved_by_the_decoder'])} / "
         f"{_thousands(guarantee['declarations'])}"),
        ("worst observed residual",
         f"**{guarantee['worst_observed_residual']}**, at "
         f"`{guarantee['worst_declaration']}`"),
        ("half a scale step", f"`{guarantee['half_step']}`"),
        ("covering radius", str(guarantee["covering_radius"])),
        ("bound respected", "yes" if guarantee["bound_respected"] else "no"),
    ]
    return "\n".join(_table(("", "measured"), rows))


def block_lean_injectivity() -> str:
    """Where the layer boundary falls: what the address conflates."""
    from . import measurements as ms
    data = ms.current()
    if data is None:
        return _lean_stale()
    rows = []
    for scheme, part in data["separation"].items():
        inject = part["injectivity"]
        distinct = (f"**{_thousands(inject['distinct_addresses'])} / "
                    f"{_thousands(inject['declarations'])}**"
                    if inject["injective"] else
                    f"{_thousands(inject['distinct_addresses'])} / "
                    f"{_thousands(inject['declarations'])}")
        adds = ("—" if inject["injective"] else
                ("no" if inject["quantisation_adds_no_conflation"] else "yes"))
        rows.append((
            f"`{scheme}`",
            distinct,
            _thousands(inject["distinct_feature_vectors"]),
            _thousands(inject["collision_classes"]),
            _thousands(inject["declarations_conflated"]),
            adds,
        ))
    return "\n".join(_table(
        ("scheme", "distinct addresses", "distinct feature vectors",
         "classes", "declarations conflated",
         "quantisation adds conflation?"), rows))


def block_lean_classes() -> str:
    """The conflation classes: how many, how wide, and the widest in full."""
    from . import measurements as ms
    data = ms.current()
    if data is None:
        return _lean_stale()
    classes = data["classes"]
    profile = sorted((int(size), count)
                     for size, count in classes["profile"].items())
    parts = []
    words = {2: ("pair", "pairs"), 3: ("triple", "triples")}
    for size, count in profile:
        singular, plural = words.get(
            size, (f"class of {size}", f"classes of {size}"))
        parts.append(f"{_thousands(count)} {singular if count == 1 else plural}")
    lines = [
        f"{_thousands(classes['classes'])} classes: " + ", ".join(parts) + ".",
        "",
        "The widest, written out, because the point they make can only be "
        "read from the names:",
        "",
        "```",
    ]
    for names in classes["largest"]:
        head = f"{len(names):<3}"
        line = head
        for index, name in enumerate(names):
            piece = name + ("," if index < len(names) - 1 else "")
            if len(line) + 1 + len(piece) > 76 and line.strip():
                lines.append(line)
                line = "    " + piece
            else:
                line = (line + " " + piece) if line.strip() else line + piece
        lines.append(line)
    lines.append("```")
    return "\n".join(lines)


def block_lean_neighbours() -> str:
    """Does address distance mean anything?  Three schemes, two null models."""
    from . import measurements as ms
    data = ms.current()
    if data is None:
        return _lean_stale()
    schemes = data["separation"]
    total = schemes["feature"]["neighbours"]["declarations"]
    best = max(part["neighbours"]["same_file_rate"]
               for part in schemes.values())
    file_rows = []
    for scheme, part in schemes.items():
        near = part["neighbours"]
        count = f"{_thousands(near['same_file_nearest'])} / {_thousands(total)}"
        rate = per_cent(near["same_file_rate"], 2)
        if near["same_file_rate"] == best:
            count, rate = f"**{count}**", f"**{rate}**"
        file_rows.append((f"`{scheme}`", count, f"≈ {rate}",
                          _decimal(near["mean_tie_size"], 2)))
    chance = schemes["feature"]["neighbours"]["same_file_chance"]
    file_rows.append(("*chance*", "—", f"≈ {per_cent(chance, 2)}", "—"))
    lines = _table(("scheme", "nearest shares a file", "rate",
                    "mean tie size"), file_rows)

    best_link = max(part["neighbours"]["linked_rate"]
                    for part in schemes.values())
    link_rows = []
    for scheme, part in schemes.items():
        near = part["neighbours"]
        count = f"{_thousands(near['linked_nearest'])} / {_thousands(total)}"
        rate = per_cent(near["linked_rate"], 2)
        if near["linked_rate"] == best_link:
            count, rate = f"**{count}**", f"**{rate}**"
        link_rows.append((f"`{scheme}`", count, f"≈ {rate}"))
    link_chance = schemes["feature"]["neighbours"]["linked_chance"]
    link_rows.append(("*chance*", "—", f"≈ {per_cent(link_chance, 2)}"))
    lines.append("")
    lines.extend(_table(("scheme", "nearest is cited, either way", "rate"),
                        link_rows))

    pair_rows = []
    lowest = min(part["pairs"]["ratio"] for part in schemes.values())
    for scheme, part in schemes.items():
        pairs = part["pairs"]
        ratio = _decimal(pairs["ratio"], 3)
        if pairs["ratio"] == lowest:
            ratio = f"**{ratio}**"
        pair_rows.append((
            f"`{scheme}`",
            _decimal(pairs["same_file_mean_squared_distance"]),
            _decimal(pairs["cross_file_mean_squared_distance"]),
            ratio,
        ))
    lines.append("")
    lines.extend(_table(("scheme", "mean d² within a file",
                         "mean d² across files", "ratio"), pair_rows))
    verdict = data["verdict"]
    near = schemes["feature"]["neighbours"]
    lines.extend([
        "",
        "Against closed-form chance the feature encoding runs "
        f"{_decimal(near['same_file_rate'] / near['same_file_chance'])}× on "
        "the file test and "
        f"{_decimal(near['linked_rate'] / near['linked_chance'])}× on the "
        "citation test, from an encoding that is never shown a file name.",
        "",
        "Over "
        f"{_thousands(schemes['feature']['pairs']['same_file_pairs'])} "
        "same-file pairs and "
        f"{_thousands(schemes['feature']['pairs']['cross_file_pairs'])} "
        "cross-file pairs.  The feature encoding beats the hash control: "
        f"{'yes' if verdict['feature_beats_hash_control'] else 'no'}; "
        "beats the seeded reshuffle: "
        f"{'yes' if verdict['feature_beats_shuffle'] else 'no'}; "
        "beats closed-form chance: "
        f"{'yes' if verdict['feature_beats_chance'] else 'no'}.",
    ])
    return "\n".join(lines)


# ===========================================================================
#  The retrieval study -- the address book put to work
# ===========================================================================

#: How each scheme of the retrieval study is described where it is tabled.
_RETRIEVAL_LABELS: Dict[str, str] = {
    "address": "**address** — Leech address of the structural feature vector",
    "features": "*features* — the same vector, no lattice (ablation)",
    "lexical": "*lexical* — Leech address of the identifier-letter vector",
    "text": "*text* — Jaccard overlap of identifier tokens "
            "(**the strong control**)",
    "name": "*name* — name-substring search",
    "digest": "*digest* — SHA-256 address (D3 control)",
    "shuffled": "*shuffled* — the feature addresses re-paired by a seeded "
                "permutation",
    "random": "*random* — a seeded permutation of the corpus",
}


def _retrieval() -> Optional[Mapping[str, object]]:
    from . import measurements as ms
    data = ms.current()
    if data is None:
        return None
    retrieval = data.get("retrieval")
    return retrieval if isinstance(retrieval, Mapping) else None


def _cell(cells: Sequence[Mapping[str, object]], k: int
          ) -> Mapping[str, object]:
    for cell in cells:
        if cell["k"] == k:
            return cell
    raise KeyError(k)


def _hit(cell: Mapping[str, object], emphasise: bool = False) -> str:
    text = f"{cell['hits']} ({per_cent(cell['hit_rate'])})"
    return f"**{text}**" if emphasise else text


def block_retrieval_setup() -> str:
    """What the experiment was run on: corpus, queries, relatives."""
    data = _retrieval()
    if data is None:
        return _lean_stale()
    return (
        f"All **{_thousands(data['corpus'])}** declarations of the Lean "
        f"development are the corpus.  The declaration experiment uses "
        f"**{data['queries']}** queries and the goal experiment "
        f"**{data['goal_queries']}**, each with at least one relative; the "
        f"mean query has **{_decimal(data['mean_relatives'])}** relatives "
        f"among the {_thousands(data['corpus'] - 1)} other declarations.  "
        f"None of the {data['goal_queries']} goal queries reproduces its own "
        f"stored feature vector "
        f"({data['goal_features_reproduced']} of {data['goal_queries']}), so "
        "a goal address is held out every time.")


def block_retrieval_declarations() -> str:
    """The eight schemes side by side, on declaration queries."""
    data = _retrieval()
    if data is None:
        return _lean_stale()
    ladder = list(data["k_ladder"])
    best = max((_cell(row["cells"], data["k"])["hit_rate"]
                for row in data["declaration_rows"]), default=Fraction(0))
    rows = []
    for row in data["declaration_rows"]:
        cells = row["cells"]
        at_k = _cell(cells, data["k"])
        line = [_RETRIEVAL_LABELS.get(row["scheme"], row["scheme"])]
        for k in ladder:
            cell = _cell(cells, k)
            line.append(_hit(cell, k == data["k"]
                             and cell["hit_rate"] == best))
        line.append(per_cent(at_k["precision"]))
        line.append(_decimal(_cell(cells, max(ladder))["mrr"], 3))
        rows.append(line)
    chance = {entry["k"]: entry["rate"] for entry in data["chance"]}
    rows.append(["**chance**, in closed form"]
                + [per_cent(chance[k]) for k in ladder] + ["—", "—"])
    header = ["scheme"] + [f"hit@{k}" for k in ladder] \
        + [f"precision@{data['k']}", f"MRR@{max(ladder)}"]
    lines = _table(header, rows)
    lines.extend([
        "",
        f"{data['queries']} queries of the "
        f"{_thousands(data['corpus'])}-declaration corpus.  At "
        f"k = {data['k']} the structural address runs "
        f"{_decimal(data['times_chance'], 2)}× closed-form chance; the text "
        "control beats the address: "
        f"{'yes' if data['verdict']['text_beats_address'] else 'no'}; the "
        "lattice matches the raw features: "
        f"{'yes' if data['verdict']['lattice_matches_raw_features'] else 'no'}.",
    ])
    return "\n".join(lines)


def block_retrieval_goals() -> str:
    """The held-out case: a bare goal, addressed live."""
    data = _retrieval()
    if data is None:
        return _lean_stale()
    ladder = list(data["k_ladder"])
    rows = []
    for row in data["goal_rows"]:
        cells = row["cells"]
        line = [row["scheme"]]
        line.extend(_hit(_cell(cells, k)) for k in ladder)
        line.append(per_cent(_cell(cells, data["k"])["precision"]))
        rows.append(line)
    header = ["scheme"] + [f"hit@{k}" for k in ladder] \
        + [f"precision@{data['k']}"]
    lines = _table(header, rows)
    lines.extend([
        "",
        f"{data['goal_queries']} goal queries, the two coordinates a goal "
        "cannot know set to zero.",
    ])
    return "\n".join(lines)


def block_retrieval_hybrid() -> str:
    """Address shortlist first, text ranking second: does pruning pay?"""
    data = _retrieval()
    if data is None:
        return _lean_stale()
    hybrid = data["hybrid"]
    rows = [[_thousands(row["shortlist"]),
             per_cent(row["fraction_of_corpus"]),
             per_cent(row["hit_rate"]),
             per_cent(row["precision"])]
            for row in hybrid["rows"]]
    rows.append(["**no shortlist**", "100 %",
                 f"**{per_cent(hybrid['text_alone']['hit_rate'])}**",
                 f"**{per_cent(hybrid['text_alone']['precision'])}**"])
    lines = _table(("shortlist", "fraction of corpus",
                    f"hit@{hybrid['k']}", f"precision@{hybrid['k']}"), rows)
    lines.extend([
        "",
        "Any shortlist beats the text control: "
        f"{'yes' if hybrid['any_shortlist_beats_text'] else 'no'}.",
    ])
    return "\n".join(lines)


def block_retrieval_guarantee() -> str:
    """The completeness bound of ``Retrieval.lean``, checked pair by pair."""
    data = _retrieval()
    if data is None:
        return _lean_stale()
    g = data["guarantee"]
    rows = [
        (f"pairs checked against `sqrt(address²) ≤ {g['scale']}·"
         f"sqrt(features²) + 2ρ`, ρ = {g['covering_radius']}",
         f"**{_thousands(g['pairs_checked'])}**"),
        ("violations", f"**{g['violations']}**"),
        ("tightest observed slack", f"{_thousands(g['worst_slack'])} "
                                    "(squared units)"),
        (f"guaranteed-complete shortlist at feature radius "
         f"{g['feature_radius']}",
         f"mean **{_decimal(g['mean_shortlist'])}** declarations = "
         f"**{per_cent(g['mean_shortlist_fraction'])}** of the corpus"),
        ("feature-close declarations it must contain",
         f"mean **{_decimal(g['mean_feature_close'])}**"),
    ]
    lines = _table(("what was checked", "result"), rows)
    lines.extend([
        "",
        f"Over {g['queries']} queries of the "
        f"{_thousands(data['corpus'])}-declaration corpus.  The bound holds: "
        f"{'yes' if g['bound_holds'] else 'no'}.",
    ])
    return "\n".join(lines)


#: Documents written by a generator that lives outside this module, with the
#: command that writes each.  They are *generated* in exactly the sense the
#: inventory means -- nobody edits them by hand, so nobody gives them a tier-0
#: block and nothing counts their lines as prose someone has to read -- but
#: they cannot be re-rendered from here, because one needs ``pytest`` and the
#: Lean tree and the other runs a live session.
EXTERNAL: Dict[str, str] = {
    "overlay/FIGURES.md":
        "python3 -m glm_universal.figures --write --lean-root ..",
    "overlay/glm_universal/examples/reasoning_showcase_transcript.md":
        "python3 -m glm_universal.examples.reasoning_showcase --write",
}

#: Every generated document, however it is written.
GENERATED: Dict[str, object] = dict(GENERATORS)
GENERATED.update(EXTERNAL)

#: Block name -> the function that renders it.
# ===========================================================================
#  WOBBLE_LANDSCAPE_STUDY.md -- one pre-registered number, and its nulls
# ===========================================================================

def _landscape_stale() -> str:
    from ..reasoning import wobble_landscape as wl
    return ("The stored measurements of the wobble landscape do not describe "
            f"the module as it now stands (`{wl.state()['verdict']}`), so "
            "nothing is reported here rather than a figure taken from code "
            "that has moved.  Run `python3 -m "
            "glm_universal.reasoning.wobble_landscape --remeasure`.")


def _landscape() -> Optional[Mapping[str, object]]:
    from ..reasoning import wobble_landscape as wl
    return wl.current()


def _round(value: object, places: int = 3) -> str:
    from ..reasoning import wobble as wbl
    return wbl.round_str(Fraction(value), places)


def block_landscape_verdict() -> str:
    """The one number, with its null named, and what it is not."""
    data = _landscape()
    if data is None:
        return _landscape_stale()
    primary = data["primary"]["primary_null"]
    secondary = data["primary"]["secondary_null"]
    gate = data["gate"]
    magnitude = data["golay_magnitude"]
    return "\n".join([
        f"**B = {gate['score_rounded']} bits** against the magnitude-matched "
        f"stride null: {primary['at_least_as_extreme']} of "
        f"{primary['members']} exact rationals of "
        f"`(1/138, 1/136)` at stride {primary['stride']:,} have a "
        f"gap-frequency deviation at least as large as alpha's, a tail of "
        f"`{primary['tail']}` and "
        f"{primary['score']['raw_rounded']} bits raw, "
        f"{gate['score_rounded']} after correcting for "
        f"{data['statistics_tried']} statistics tried.  By the gate fixed "
        f"before the measurement that is **{gate['verdict']}**: "
        f"{gate['action']}, and the landscape enumeration is not run "
        f"(`enumerate: {gate['enumerate']}`).",
        "",
        f"Under the secondary `k`-sweep null the same statistic scores "
        f"{secondary['score']['corrected_rounded']} bits (tail "
        f"`{secondary['tail']}`), which is *not evidence*; the two nulls "
        f"disagree, and that disagreement is a fact about the measure a "
        f"`k`-sweep puts on `k` rather than about alpha.",
        "",
        f"**What it is not.**  It is not a derivation of alpha, and it is not "
        f"a claim that the substrate selects alpha.  The Golay reading, which "
        f"looks like {_round(data['golay_null']['within_three_bits'], 2)} "
        f"bits against a uniform word and more against a naive one, is worth "
        f"{magnitude['score']['raw_rounded']} bits against the "
        f"magnitude-matched null: every one of the {magnitude['members']} "
        f"members reproduces alpha's `d_min = {magnitude['observed']}`.",
    ])


def block_landscape_spectrum() -> str:
    """Alpha's continued fraction, its Ostrowski ladder, and the check."""
    data = _landscape()
    if data is None:
        return _landscape_stale()
    check = data["closed_form_check"]
    rows = [(row["stage"], row["short_gap"], row["long_gap"],
             _round(row["long_frequency"], 6))
            for row in data["ladder"]]
    lines = _table(("Ostrowski stage", "short gap", "long gap",
                    "long-gap frequency"), rows)
    lines.extend([
        "",
        f"The continued fraction of `1/alpha` is "
        f"`{list(data['reciprocal_cf'])}` — computed from the exact CODATA "
        f"2022 value, not copied.  Stage 0's short gap, "
        f"{data['run_length']}, is the run length the older material "
        f"reports: it is `a_0` and nothing more.  The Shannon entropy of the "
        f"raw stream is {data['entropy_rounded']} bits, which is "
        f"`H2(alpha)` — a function of the magnitude alone, which is why it "
        f"is not the statistic.",
        "",
        f"**The closed form against the run.**  Over {check['steps']:,} "
        f"emitted bits the stream shows {check['gaps']} gaps, of lengths "
        f"{list(check['distinct_lengths'])} and no others "
        f"(`lengths_hold: {check['lengths_hold']}`); the closed form predicts "
        f"{check['long_closed_form']} long gaps and the run has "
        f"{check['long_observed']} "
        f"(`count_holds: {check['count_holds']}`).",
    ])
    return "\n".join(lines)


def block_landscape_depth() -> str:
    """The depth sweep -- exploratory, and a stability check only."""
    data = _landscape()
    if data is None:
        return _landscape_stale()
    rows = [(row["gaps"], f"{row['bits_needed']:,}",
             _round(row["estimate"], 6), _round(row["error"], 6))
            for row in data["depth_profile"]]
    lines = _table(("gaps", "bits needed", "estimate of S",
                    "distance from the closed form"), rows)
    lines.extend([
        "",
        "Exploratory.  The primary statistic is the closed form and is "
        "depth-free; this table only shows how fast a finite run would reach "
        "it, and the estimate at any depth is exact.",
    ])
    return "\n".join(lines)


def block_landscape_primary() -> str:
    """Phase 2: the statistic against both nulls, and the gate."""
    data = _landscape()
    if data is None:
        return _landscape_stale()
    test = data["primary"]
    primary = test["primary_null"]
    secondary = test["secondary_null"]
    gate = data["gate"]
    rows = [
        (f"stride {primary['stride']:,} in (1/138, 1/136) — **primary**",
         primary["members"], primary["at_least_as_extreme"],
         f"`{primary['tail']}`", primary["score"]["raw_rounded"],
         primary["score"]["corrected_rounded"]),
        (f"reciprocal [137; k], k = 1 … {secondary['sweep']} — secondary",
         secondary["members"], secondary["at_least_as_extreme"],
         f"`{secondary['tail']}`", secondary["score"]["raw_rounded"],
         secondary["score"]["corrected_rounded"]),
    ]
    lines = _table(("null", "members", "at least as extreme", "tail",
                    "raw bits", "corrected bits"), rows)
    lines.extend([
        "",
        f"`S(alpha) = {test['statistic_rounded']}` exactly "
        f"`{test['statistic']}`, so the two gap lengths are "
        f"{test['spectrum']['short_gap']} and "
        f"{test['spectrum']['long_gap']} with frequencies "
        f"{_round(test['spectrum']['short_frequency'], 6)} and "
        f"{_round(test['spectrum']['long_frequency'], 6)}.  The empirical "
        f"estimate at the primary depth of {test['empirical']['gaps']} gaps "
        f"is {_round(test['empirical']['estimate'], 6)}.",
        "",
        f"Gate: {gate['score_rounded']} bits is **{gate['verdict']}** "
        f"(not evidence below {gate['weak_gate']}, weak below "
        f"{gate['continue_gate']}).  {gate['action'].capitalize()}.",
    ])
    return "\n".join(lines)


def block_landscape_comparison() -> str:
    """Every comparison row, ordered by how extreme its statistic is."""
    data = _landscape()
    if data is None:
        return _landscape_stale()
    rows = [(row["rank"], row["name"], row["notation"],
             f"{row['short_gap']}/{row['long_gap']}",
             row["statistic_rounded"], f"`{row['tail']}`",
             row["bits_rounded"], list(row["ladder"]))
            for row in data["comparison"]]
    lines = _table(("rank", "constant", "as taken", "gap lengths",
                    "S", "tail", "bits", "partial quotients"), rows)
    lines.extend([
        "",
        "The tail column applies *alpha's* null — the stride-selected "
        "rationals of `(1/138, 1/136)` — to each row's own deviation, so it "
        "answers \"how unusual would this signature be at alpha's "
        "magnitude\".  It is a comparison, not a claim that these constants "
        "live in that interval.  The ranking is exploratory: the "
        "pre-registered test is the alpha row against its null, above.",
    ])
    return "\n".join(lines)


def block_landscape_golay() -> str:
    """The Golay null, exactly, and what survives a magnitude-matched control."""
    data = _landscape()
    if data is None:
        return _landscape_stale()
    null = data["golay_null"]
    magnitude = data["golay_magnitude"]
    weight_rows = [(weight, f"{count:,}",
                    f"`{null['probability_by_weight'][weight]}`",
                    f"`{null['cumulative'][weight]}`")
                   for weight, count in null["cosets_by_weight"].items()]
    lines = _table(("distance to the code", "cosets", "probability",
                    "cumulative"), weight_rows)
    lines.extend([
        "",
        f"So `d_min <= 3` holds for "
        f"{null['codewords']:,} × ({' + '.join(str(term) for term in null['sphere_terms'])}) "
        f"= {null['within_three']:,} of {null['space']:,} words, a "
        f"probability of exactly `{null['within_three_probability']}` and "
        f"{_round(null['within_three_bits'], 3)} bits.  It is the majority "
        f"case.  The identity is `GLM.Landscape.golay_code_ball_count`, "
        f"proved of the substrate's own code.",
        "",
    ])
    rows = [(row["name"], _round(row["slope"], 6),
             ", ".join(f"{cell['depth']}: {cell['d_min']}"
                       for cell in row["rows"]),
             row["d_min"], row["all_zero"])
            for row in data["golay"]]
    lines.extend(_table(("constant", "slope", "d_min by depth",
                         "d_min", "all-zero word"), rows))
    lines.extend([
        "",
        f"**And the magnitude-matched control removes it entirely.**  At "
        f"depth {magnitude['depth']}, "
        f"{magnitude['at_least_as_close']} of {magnitude['members']} members "
        f"of the stride null reach `d_min <= {magnitude['observed']}` — that "
        f"is all of them — so the tail is `{magnitude['tail']}` and the score "
        f"is {magnitude['score']['raw_rounded']} bits.  A slope below "
        f"`1/{magnitude['depth']}` emits no one at all in "
        f"{magnitude['depth']} bits, so the word is all zeros, which is a "
        f"codeword; that is arithmetic about the magnitude of alpha and "
        f"carries nothing about the code.",
    ])
    return "\n".join(lines)


# ===========================================================================
#  DEEP_HOLE_STUDY.md -- a hole named by its arrival distribution
# ===========================================================================

def _deephole_stale() -> str:
    from ..reasoning import deep_hole_classifier as dhc
    return ("The stored measurements of the deep-hole classifier do not "
            f"describe the module as it now stands (`{dhc.state()['verdict']}`), "
            "so nothing is reported here rather than a figure taken from code "
            "that has moved.  Run `python3 -m glm_universal.tools deepholes "
            "--write`.")


def _deephole() -> Optional[Mapping[str, object]]:
    from ..reasoning import deep_hole_classifier as dhc
    return dhc.current()


def block_deephole_verdict() -> str:
    """The one verdict, with the baseline it had to beat beside it."""
    data = _deephole()
    if data is None:
        return _deephole_stale()
    run = data["run"]
    method = run["method"]
    baseline = run["baseline"]
    digest = run["digest"]
    reshuffle = run["reshuffle"]
    gate = data["gate"]
    table = data["table"]
    sanity = [row for row in method["rows"]
              if str(row["query"]).endswith("seed")]
    sanity_ok = sum(1 for row in sanity if row["correct"])
    return "\n".join([
        f"**The verdict is `{gate['verdict']}`.**  The declared budget "
        f"reached {table['size']} of the {data['catalogue_size']} Niemeier "
        f"types, giving {method['queries']} queries at a chance rate of "
        f"`{method['chance']}`.  The arrival-share profile named "
        f"{method['correct']} of them correctly "
        f"({per_cent(method['accuracy'])}), against "
        f"{baseline['correct']} ({per_cent(baseline['accuracy'])}) for the "
        f"plain vertex count, {digest['correct']} "
        f"({per_cent(digest['accuracy'])}) for the digest control and "
        f"{reshuffle['correct']} ({per_cent(reshuffle['accuracy'])}) for the "
        f"seeded reshuffle.  So the method beats every control, including "
        f"the one that mattered — and it still fails, because the "
        f"pre-registered decision tree stops the round earlier than that.",
        "",
        f"**What stops it is the sanity query.**  Q0 changes only the "
        f"ensemble seed and leaves the hole where it is; the study fixed in "
        f"advance that if the statistic does not survive that, nothing "
        f"downstream is worth reading.  It survives it for {sanity_ok} of "
        f"{len(sanity)} holes.  {gate['reading'].capitalize()}.",
        "",
        f"The score against the uniform-label null is "
        f"{gate['score_rounded']} bits after correcting for "
        f"{data['statistics_tried']} statistics tried, which clears the gate "
        f"of {gate['gate_bits']} bits — and is reported here as what it is: "
        f"a bit score computed on a statistic that the round's own stopping "
        f"rule has already disqualified.  A score is not a licence to ignore "
        f"the tree it was gated by.",
        "",
        f"The types the method recovers completely — every query of that "
        f"type named correctly — are "
        f"{', '.join(f'`{t}`' for t in gate['recovered']) or 'none'}; the "
        f"vertex count recovers "
        f"{', '.join(f'`{t}`' for t in gate['baseline_recovered']) or 'none'}. "
        f" That is "
        f"{len(gate['beyond_baseline'])} type(s) beyond the baseline, and "
        f"the study fixed in advance that one is a coincidence.",
    ])


def block_deephole_holes() -> str:
    """Every hole the declared budget reached, in the declared order."""
    data = _deephole()
    if data is None:
        return _deephole_stale()
    table = data["table"]
    rows = []
    for hole in table["holes"]:
        rows.append((hole["name"], hole["construction"],
                     hole["type"] or "—",
                     "yes" if hole["certified"] else "no",
                     hole["vertex_count"]))
    lines = _table(("hole", "how it was reached", "certified type",
                    "certified", "vertices"), rows)
    missing = table["missing_types"]
    lines.extend([
        "",
        f"{table['size']} distinct types from {len(table['holes'])} attempts. "
        f" The {len(missing)} types the budget did not reach are reported as "
        f"not reached and nothing is claimed about them: "
        f"{', '.join(f'`{name}`' for name in missing)}.  Reaching a named "
        f"type on demand would need its centre, which is the stored table "
        f"the exercise exists to avoid.",
    ])
    return "\n".join(lines)


def block_deephole_references() -> str:
    """The reference profiles, how far apart they are, and the two radii."""
    data = _deephole()
    if data is None:
        return _deephole_stale()
    table = data["table"]
    run = data["run"]
    rows = []
    for entry in table["entries"]:
        rows.append((f"`{entry['label']}`", entry["hole"],
                     entry["certified_vertex_count"], entry["support"],
                     entry["arrivals"], entry["strays"],
                     f"{entry['reached_of_certified']}"
                     f"/{entry['certified_vertex_count']}"))
    lines = _table(("type", "reference centre", "certified vertices",
                    "vertices the ensemble reached", "arrivals", "strays",
                    "coverage"), rows)
    separation = run["separation"]
    closest = separation["closest_pair"]
    lines.extend([
        "",
        f"The {separation['pair_count']} pairwise L1 separations of the "
        f"reference profiles have minimum `{separation['minimum']}` "
        f"({_round(separation['minimum'], 4)}), attained by "
        f"`{closest[0]}` and `{closest[1]}`, so the **certified radius** is "
        f"`r* = {run['certified_radius']}` "
        f"({_round(run['certified_radius'], 4)}) against an operating radius "
        f"of `r = {run['operating_radius']}`.",
        "",
        f"**And that is the sentence the certified-absence theorem turns "
        f"on.**  Faithfulness — every hole of type `T` within `r` of `T`'s "
        f"reference — needs `r` at least "
        f"{_round(run['faithfulness_radius'], 4)} on this query set, while "
        f"separation needs `r` below {_round(run['certified_radius'], 4)}. "
        f"The two are compatible: `{run['faithfulness_compatible']}`.  At "
        f"`r*` the classifier returns `absent` for "
        f"{run['absent_at_r_star']} of {run['certified']['queries']} "
        f"queries, every one of which is a hole that is present and "
        f"tabulated.  So the theorem holds and the detector does not: "
        f"`GLM.DeepHole.absent_certifies` is exactly as strong as its "
        f"faithfulness hypothesis, and this measurement refutes the "
        f"hypothesis rather than the theorem.",
    ])
    return "\n".join(lines)


def block_deephole_queries() -> str:
    """Every query, with what the method said and what the baseline said."""
    data = _deephole()
    if data is None:
        return _deephole_stale()
    run = data["run"]
    baseline = {str(row["query"]): row for row in run["baseline"]["rows"]}
    rows = []
    for row in run["method"]["rows"]:
        other = baseline.get(str(row["query"]), {})
        rows.append((row["query"], f"`{row['truth']}`", row["verdict"],
                     f"`{row['label']}`" if row["label"] else "—",
                     "yes" if row["correct"] else "no",
                     _round(row["distance"], 4),
                     _round(row["own_distance"], 4)
                     if row["own_distance"] is not None else "—",
                     row["own_rank"],
                     "yes" if other.get("correct") else "no"))
    lines = _table(("query", "truth", "verdict", "named", "correct",
                    "distance to it", "distance to its own reference",
                    "rank of its own", "vertex count correct"), rows)
    method = run["method"]
    lines.extend([
        "",
        f"The `own rank` column is the diagnostic that says what went wrong: "
        f"the query's own reference is the nearest one for "
        f"{run['own_rank_first']} of {method['queries']} queries, so for the "
        f"rest a *different* type's profile is closer than the profile of "
        f"the very hole the query is a transform of.  The statistic is not "
        f"measuring the hole strongly enough to survive its own ensemble.",
    ])
    return "\n".join(lines)


def block_deephole_controls() -> str:
    """The controls, and the baseline that was fixed as the real competitor."""
    data = _deephole()
    if data is None:
        return _deephole_stale()
    run = data["run"]
    method = run["method"]
    rows = [("**the arrival-share profile** — the method", method["correct"],
             method["queries"], per_cent(method["accuracy"]),
             method["refused"], f"`{method['tail']}`",
             method["score"]["corrected_rounded"])]
    for control in run["controls"]:
        rows.append((control["name"], control["correct"], control["queries"],
                     per_cent(control["accuracy"]), control["refused"],
                     f"`{control['tail']}`",
                     control["score"]["corrected_rounded"]))
    lines = _table(("classifier", "correct", "queries", "accuracy",
                    "refusals", "tail", "bits"), rows)
    stability = data["stability"]
    lines.extend([
        "",
        f"Chance is `{method['chance']}` per query.  The digest control sits "
        f"where D3 says it must, and the reshuffle with it.  The competitor "
        f"that was fixed in advance is the vertex count, and the method does "
        f"beat it — by "
        f"{method['correct'] - run['baseline']['correct']} queries of "
        f"{method['queries']} — with the uniform-profile ablation, which is "
        f"the vertex count expressed in the method's own metric, landing "
        f"between the two.",
        "",
        f"The declared stability re-measurement at {stability['starts']} "
        f"starts gives {per_cent(stability['accuracy'])} against "
        f"{per_cent(stability['full_accuracy'])} at the full ensemble "
        f"(agrees: `{stability['agrees']}`), which is the same finding from "
        f"the other side: halving the declared ensemble moves the answer.",
    ])
    return "\n".join(lines)


def block_deephole_claims() -> str:
    """The three claims of the study, answered by the round's own numbers."""
    data = _deephole()
    if data is None:
        return _deephole_stale()
    run = data["run"]
    gate = data["gate"]
    method = run["method"]
    baseline = run["baseline"]
    ablation = run["ablation"]
    rows = [
        ("(i) a classification faculty over a geometric object",
         "refuted for now",
         f"{method['correct']}/{method['queries']} against "
         f"{baseline['correct']}/{baseline['queries']} for the vertex count, "
         f"but the sanity query fails and the tree stops the round"),
        ("(ii) a trajectory distribution carries structure the static "
         "address does not",
         "partly upheld",
         f"the shape of the distribution is worth "
         f"{method['correct'] - ablation['correct']} queries over the "
         f"uniform profile on the same support, which is real and small"),
        ("(iii) a hole detector whose negative answers are proofs",
         "refuted on this data",
         f"faithfulness needs r >= "
         f"{_round(run['faithfulness_radius'], 4)} and separation needs "
         f"r < {_round(run['certified_radius'], 4)}; compatible: "
         f"`{run['faithfulness_compatible']}`, and {run['absent_at_r_star']} "
         f"of {run['certified']['queries']} present holes are called absent "
         f"at r*"),
    ]
    lines = _table(("claim", "verdict", "the number that decides it"), rows)
    per_rows = [(f"`{row['label']}`", row["queries"], row["correct"],
                 "yes" if row["recovered"] else "no",
                 "yes" if next(
                     (b["recovered"] for b in gate["per_type_baseline"]
                      if b["label"] == row["label"]), False) else "no")
                for row in gate["per_type"]]
    lines.append("")
    lines.extend(_table(("type", "queries", "named correctly",
                         "recovered by the method",
                         "recovered by the vertex count"), per_rows))
    lines.extend([
        "",
        "So the answer to the round is tier 0's: two of the three claims do "
        "not survive contact with the controls, the third survives only as a "
        "small margin, and the pre-registered stopping rule fires before any "
        "of them can be claimed.",
    ])
    return "\n".join(lines)



# ===========================================================================
#  DEEP_HOLE_ESCALATION_STUDY.md -- the ladder that escalates the reading
# ===========================================================================

def _deepholeesc_stale() -> str:
    from ..reasoning import deep_hole_escalation as esc
    return ("The stored measurements of the deep-hole ladder do not describe "
            f"the module as it now stands (`{esc.state()['verdict']}`), so "
            "nothing is reported here rather than a figure taken from code "
            "that has moved.  Run `python3 -m glm_universal.tools escalation "
            "--write`.")


def _deepholeesc() -> Optional[Mapping[str, object]]:
    from ..reasoning import deep_hole_escalation as esc
    return esc.current()


def _rho(value: object) -> str:
    from ..reasoning import deep_hole_escalation as esc
    return "n/a" if value is None else esc.rounded(value, 4)


def block_deepholeesc_verdict() -> str:
    """The verdict of the ladder: the boundary, or the crossing of it."""
    data = _deepholeesc()
    if data is None:
        return _deepholeesc_stale()
    tree = data["decision"]
    bottom = tree["bottom"]
    best = tree["best"]
    gate = tree["gate"]
    cells = data["cells"]
    return "\n".join([
        f"**The verdict is `{tree['verdict']}`.**  The ladder is "
        f"{len(data['layers'])} readings at {len(data['starts_ladder'])} "
        f"ensemble sizes, {len(cells)} cells in all, and the gate is that "
        f"every one of the {gate} reference holes recognises itself when only "
        f"the ensemble seed changes.",
        "",
        f"The bottom rung is the first round's cell — the arrival shares at "
        f"240 starts — and it returns {bottom['q0']} of {gate}, against the "
        f"{tree['expected']} the first round reported.  The best cell of the "
        f"whole ladder is `{best['layer']}` at {best['starts']} starts, which "
        f"returns {best['q0']} of {gate} with a ratio of "
        f"`rho = {_rho(best['ratio'])}`; the criterion needs `rho < 1`.",
        "",
        tree["reading"],
    ])


def block_deepholeesc_ladder() -> str:
    """Every cell of the ladder, in the declared order of escalation."""
    data = _deepholeesc()
    if data is None:
        return _deepholeesc_stale()
    rows = ["| reading | starts | rung | holes recognising themselves | worst "
            "seed shift `W` | separation `B` | `rho = 2W/B` | criterion |",
            "|---|---|---|---|---|---|---|---|"]
    for cell in data["cells"]:
        rows.append(
            f"| {cell['layer_name']} | {cell['starts']} | "
            f"{'declared' if cell.get('declared', True) else 'extension'} | "
            f"{cell['q0']} / {cell['gate']} | {_rho(cell['spread'])} | "
            f"{_rho(cell['separation'])} | {_rho(cell['ratio'])} | "
            f"{'holds' if cell['ratio_below_one'] else 'fails'} |")
    best = data["decision"]["best"]
    rows.append("")
    rows.append(
        f"The criterion `rho < 1` is *sufficient* for the gate — that is "
        f"`GLM.DeepHoleLadder.nearest_correct`, proved rather than assumed — "
        f"so a cell can reach the gate without the criterion holding, but not "
        f"the other way round.  The best cell is `{best['layer']}` at "
        f"{best['starts']} starts.  A rung marked *extension* was added after "
        f"the twelve pre-registered cells had been measured and the count was "
        f"seen to be climbing; it is counted in the multiplicity correction "
        f"and is never read as a pre-registered result.")
    return "\n".join(rows)


def block_deepholeesc_reproduction() -> str:
    """The stopping rule that comes before every other reading."""
    data = _deepholeesc()
    if data is None:
        return _deepholeesc_stale()
    tree = data["decision"]
    bottom = tree["bottom"]
    return "\n".join([
        f"The ladder's bottom rung is the first round's cell exactly — the "
        f"arrival shares at 240 starts, the same holes, the same reference "
        f"and sanity seeds — so it must return the first round's number "
        f"before anything above it is read.  It returns **{bottom['q0']} of "
        f"{tree['gate']}** against the **{tree['expected']}** the first round "
        f"reported: reproduces = `{tree['reproduces']}`.",
        "",
        "The two rounds therefore "
        + ("agree, and the rest of the ladder is read."
           if tree["reproduces"] else
           "disagree, and nothing above the bottom rung is read."),
    ])


def block_deepholeesc_decision() -> str:
    """The decision tree of the pre-registration, applied to the cells."""
    data = _deepholeesc()
    if data is None:
        return _deepholeesc_stale()
    tree = data["decision"]
    best = tree["best"]
    bottom = tree["bottom"]
    return "\n".join([
        "| item | value |",
        "|---|---|",
        f"| the gate | all {tree['gate']} reference holes recognise "
        f"themselves |",
        f"| cells that reach it | "
        f"{sum(1 for cell in data['cells'] if cell['passes'])} of "
        f"{len(data['cells'])} ("
        f"{sum(1 for cell in data['cells'] if cell['passes'] and cell.get('declared', True))}"
        f" of the {tree.get('declared_cells', len(data['cells']))} "
        f"pre-registered) |",
        f"| the bottom rung | {bottom['q0']} of {tree['gate']}, "
        f"`rho = {_rho(bottom['ratio'])}` |",
        f"| the best cell | `{best['layer']}` at {best['starts']} starts, "
        f"{best['q0']} of {tree['gate']}, `rho = {_rho(best['ratio'])}` |",
        f"| the sanity count rises along the ladder | `{tree['rises']}` |",
        f"| the full query set was run | `{tree['run_full_query_set']}` |",
        f"| the best pre-registered cell | "
        f"`{tree['declared_best']['layer']}` at "
        f"{tree['declared_best']['starts']} starts, "
        f"{tree['declared_best']['q0']} of {tree['gate']} |"
        if tree.get("declared_best") else "| the best pre-registered cell | "
        "not recorded |",
        f"| verdict | `{tree['verdict']}` |",
        "",
        tree["reading"],
    ])


def block_deepholeesc_controls() -> str:
    """The four controls, at the cell the tree lands on -- or why not."""
    data = _deepholeesc()
    if data is None:
        return _deepholeesc_stale()
    run = data.get("run")
    tree = data["decision"]
    if not run:
        return ("The pre-registered tree runs the full query set and its four "
                "controls **only at a cell that reaches the gate**, and no "
                "cell does, so the query set was not run and no control "
                "figure is reported here.  That is the first round's stopping "
                "rule applied a second time: a reading that cannot recognise "
                "a hole as itself is not read against a baseline, because the "
                "comparison would mean nothing.  The decision is "
                f"`{tree['verdict']}`.")
    method = run["method"]
    rows = ["| classifier | correct | queries | accuracy | bits, corrected "
            "for the cells tried |", "|---|---|---|---|---|"]
    for entry in (method,) + tuple(run["controls"]):
        score = entry.get("score") or {}
        rows.append(f"| {entry['name']} | {entry['correct']} | "
                    f"{entry['queries']} | {per_cent(entry['accuracy'])} | "
                    f"{score.get('corrected_rounded', 'n/a')} |")
    rows.append("")
    rows.append(f"Chance is `{method['chance']}` per query, and the bit column "
                f"is corrected for the {method.get('score', {}).get('statistics', 'n/a')} "
                f"cells and statistics this question has been asked with, "
                f"across both rounds.  Beats the vertex-count baseline: "
                f"`{run['beats_baseline']}`; beats every control: "
                f"`{run['beats_every_control']}`.")
    return "\n".join(rows)


def block_deepholeesc_secondaries() -> str:
    """The named secondaries, reported whether or not the gate was reached."""
    data = _deepholeesc()
    if data is None:
        return _deepholeesc_stale()
    run = data.get("run")
    cells = data["cells"]
    gate = data["decision"]["gate"]
    shares_best = max(cell["q0"] for cell in cells
                      if cell["layer"] == "shares")
    widened_best = max(cell["q0"] for cell in cells
                       if cell["layer"] == "widened")
    rational_best = max(cell["q0"] for cell in cells
                        if cell["layer"] == "rational")
    joint_best = max(cell["q0"] for cell in cells if cell["layer"] == "joint")
    return "\n".join([
        "| secondary | reading |",
        "|---|---|",
        "| `S_b` — faithfulness against the certified radius | "
        + (f"faithfulness `{_rho(run['faithfulness_radius'])}`, "
           f"`r* = {_rho(run['certified_radius'])}`, compatible "
           f"`{run['faithfulness_compatible']}` |" if run else
           "not run: the tree runs the query set only at a passing cell |"),
        "| `S_c` — accuracy over the full query set | "
        + (f"{run['method']['correct']} of {run['method']['queries']} |"
           if run else "not run, for the same reason |"),
        "| `S_d` — the mean rank of a query's own reference | "
        + (f"{_rho(run['mean_own_rank'])} |" if run else "not run |"),
        f"| what each reading is worth, at its own best cell | shares "
        f"{shares_best} of {gate}, widened by the strays {widened_best}, the "
        f"rational measure {rational_best}, the joint reading {joint_best} |",
        f"| the cost of the round | {data['cost']['decoder_calls']} exact "
        f"decoder calls over {data['cost']['ensembles']} ensembles, one per "
        f"centre and seed at the top rung and sliced for the rungs below |",
    ])


# ===========================================================================
#  DEEP_HOLE_FAILURE_STUDY.md -- the four failures and the stalled ratio
# ===========================================================================

def _deepholefail_stale() -> str:
    from ..reasoning import deep_hole_failures as fail
    return ("The stored measurements of the four failures do not describe the "
            f"modules as they now stand (`{fail.state()['verdict']}`), so "
            "nothing is reported here rather than a figure taken from code "
            "that has moved.  Run `python3 -m glm_universal.tools failures "
            "--write`.")


def _deepholefail() -> Optional[Mapping[str, object]]:
    from ..reasoning import deep_hole_failures as fail
    return fail.current()


def _exact(value: object, places: int = 4) -> str:
    from ..reasoning import deep_hole_failures as fail
    return "n/a" if value is None else fail.rounded(value, places)


def block_deepholefail_tier() -> str:
    """The coarse read: which mechanism, and is it the one that stalls rho."""
    data = _deepholefail()
    if data is None:
        return _deepholefail_stale()
    counts = data["counts"]
    spread = data["spread"]
    sweep = data["leave_out"]
    rows = data["failures"]
    named = ", ".join(f"{row['truth']} named as {row['named']}"
                      for row in rows)
    return "\n".join([
        f"All {len(rows)} failures are opened at the one declared cell.  Of "
        f"them, {counts['a_closest_pair']} have their truth and their winner "
        f"among the five closest reference pairs, {counts['b_bimodal']} split "
        f"their ensemble halves onto different labels, {counts['c_tie']} are "
        f"ties, and {counts['d_absent_from_shortlist']} have the correct "
        f"answer outside the first three ranks; "
        f"{counts['none_of_the_four']} match none of the four.  The four are "
        f"{named}.",
        "",
        f"The spread that stalls the ratio is `{spread['worst_type']}`'s, at "
        f"`W = {_exact(spread['worst_spread'])}` against a separation of "
        f"`B = {_exact(spread['separation'])}`, and the failing queries "
        f"belong to {'that same type' if data['same_mechanism'] else 'other types'} "
        f"— so the failures and the stalled ratio are "
        f"{'one mechanism' if data['same_mechanism'] else 'two mechanisms'}.  "
        f"Over the {sweep['subsets_tried']} declared deletions the smallest "
        f"ratio reached is `{_exact(sweep['best_two']['ratio'])}`, and "
        f"`rho < 1` over the full ten-type set — the only reading that earns "
        f"the certificate — is "
        f"{'reached' if data['original_negative']['stands'] is False else 'not reached'}.",
    ])


def block_deepholefail_reproduction() -> str:
    """The stopping rule: this round must return the escalation round's count."""
    data = _deepholefail()
    if data is None:
        return _deepholefail_stale()
    check = data["reproduction"]
    return (
        f"Re-reading all {check['queries']} used queries at the declared cell "
        f"returns **{check['correct']} correct**, against the "
        f"**{check['expected_correct']} of {check['expected_queries']}** the "
        f"escalation round reported: reproduces = `{check['reproduces']}`.  "
        + ("The two rounds agree about the same measurement, and the rest of "
           "the study is read."
           if check["reproduces"] else
           "They disagree, so by the stopping rule nothing below is read as a "
           "finding."))


def block_deepholefail_failures() -> str:
    """Every failure with its rank, its margin and its whole shortlist."""
    data = _deepholefail()
    if data is None:
        return _deepholefail_stale()
    lines = ["| query | truth | named as | rank of the truth | margin | "
             "margin / `B` | the first three references, with distances |",
             "|---|---|---|---|---|---|---|"]
    ranked = {row["query"]: row["ranked"] for row in data["queries"]}
    for row in data["failures"]:
        shortlist = ", ".join(
            f"{label} {_exact(distance)}"
            for label, distance in list(ranked.get(row["query"], ()))[:3])
        lines.append(
            f"| {row['query']} | {row['truth']} | {row['named']} | "
            f"{row['own_rank']} | {_exact(row['margin'])} | "
            f"{_exact(row['margin_over_separation'])} | {shortlist} |")
    lines.append("")
    lines.append(
        "The whole ranked list of all ten references is in the measurement "
        "cache for every one of the 44 queries; the first three are shown "
        "because the diagnosis that matters — second by a hair against absent "
        "from the shortlist — is decided there.")
    return "\n".join(lines)


def block_deepholefail_diagnoses() -> str:
    """The four pre-registered rules, applied."""
    data = _deepholefail()
    if data is None:
        return _deepholefail_stale()
    lines = ["| query | A closest pair | B bimodal | C tie | D absent from "
             "the shortlist | near miss | halves name |",
             "|---|---|---|---|---|---|---|"]
    for row in data["failures"]:
        lines.append(
            f"| {row['query']} | "
            f"{'yes' if row['a_closest_pair'] else 'no'} "
            f"(pair rank {row['pair_rank']}) | "
            f"{'yes' if row['b_bimodal'] else 'no'} | "
            f"{'yes' if row['c_tie'] else 'no'} | "
            f"{'yes' if row['d_absent_from_shortlist'] else 'no'} | "
            f"{'yes' if row['near_miss'] else 'no'} | "
            f"{row['first_half_named']} / {row['second_half_named']} |")
    counts = data["counts"]
    lines.append("")
    lines.append(
        f"Totals over the {len(data['failures'])} failures: A "
        f"{counts['a_closest_pair']}, B {counts['b_bimodal']}, C "
        f"{counts['c_tie']}, D {counts['d_absent_from_shortlist']}, near miss "
        f"{counts['near_miss']}, none of the four "
        f"{counts['none_of_the_four']}.  The four rules are readings of the "
        f"same queries and are not independent tests; no bit score is "
        f"computed from them.")
    control = data["half_control"]
    lines.append("")
    lines.append(
        f"**The control on rule B, added after the four were read.**  The "
        f"same half-split rule fires for "
        f"{control['correct_halves_disagree']} of the "
        f"{control['correct']} queries the reading names *correctly*, against "
        f"{control['failures_halves_disagree']} of the {control['failures']} "
        f"it does not.  Rule B therefore reads as a statement about margin "
        f"rather than about modality: the halves come apart wherever the "
        f"margin is smaller than what half the budget resolves, which is what "
        f"a near-miss is.  It is reported as a control and is not counted "
        f"among the pre-registered four.")
    return "\n".join(lines)


def block_deepholefail_spread() -> str:
    """Where the within-type spread actually lives."""
    data = _deepholefail()
    if data is None:
        return _deepholefail_stale()
    spread = data["spread"]
    lines = ["| type | `W_T` (all perturbations) | attained by | `W_T` (seed "
             "only) | nearest other reference | `B_T` | `rho_T` |",
             "|---|---|---|---|---|---|---|"]
    for row in spread["rows"]:
        lines.append(
            f"| {row['type']} | {_exact(row['spread'])} | {row['widest_by']} "
            f"| {_exact(row['seed_spread'])} | {row['nearest_reference']} | "
            f"{_exact(row['gap'])} | {_exact(row['ratio'])} |")
    faith = data["faithfulness"]
    pair = spread["closest_pair"]
    lines.append("")
    lines.append(
        f"The global separation is `B = {_exact(spread['separation'])}`, "
        f"attained by the pair `{pair[0]} / {pair[1]}`.  Read over the sanity "
        f"seed alone the ratio is `rho = {_exact(spread['rho_seed'])}`, which "
        f"is the escalation round's number; read over every perturbation the "
        f"query set contains it is `{_exact(spread['rho_all'])}`.  "
        f"Faithfulness needs `r >= {_exact(faith['faithfulness'])}` where "
        f"separation permits only `r < {_exact(faith['certified_radius'])}`, "
        f"so the two are compatible: `{faith['compatible']}`.")
    per_type = data["per_type"]
    lines.append("")
    lines.append(
        f"The global ratio is a worst case over all ten types, and it hides "
        f"that the criterion already holds for "
        f"**{per_type['count']} of {per_type['total']}** of them: "
        f"{', '.join(f'`{name}`' for name in per_type['certified'])}.  For "
        f"those, `2W_T < B_T`, and `GLM.DeepHoleFailure.per_type_correct` "
        f"turns that into a certificate — every query of the type within "
        f"`W_T` of its reference is named correctly whatever the other types "
        f"do.  That is the first certification this line of rounds has "
        f"earned, and it covers {per_type['count']} types, not ten.")
    return "\n".join(lines)


def block_deepholefail_leaveout() -> str:
    """The declared deletion sweep, reported in full."""
    data = _deepholefail()
    if data is None:
        return _deepholefail_stale()
    sweep = data["leave_out"]
    lines = ["| deleted | separation `B` | worst spread `W` | `rho` | "
             "`rho < 1` |", "|---|---|---|---|---|"]
    full = sweep["full"]
    lines.append(
        f"| nothing (all ten types) | {_exact(full['separation'])} | "
        f"{_exact(full['spread'])} | {_exact(full['ratio'])} | "
        f"{'yes' if full['below_one'] else 'no'} |")
    for row in sweep["one"]:
        lines.append(
            f"| {', '.join(row['dropped'])} | {_exact(row['separation'])} | "
            f"{_exact(row['spread'])} | {_exact(row['ratio'])} | "
            f"{'yes' if row['below_one'] else 'no'} |")
    for row in list(sweep["two"])[:10]:
        lines.append(
            f"| {', '.join(row['dropped'])} | {_exact(row['separation'])} | "
            f"{_exact(row['spread'])} | {_exact(row['ratio'])} | "
            f"{'yes' if row['below_one'] else 'no'} |")
    best_two = sweep["best_two"]
    lines.append("")
    lines.append(
        f"All {sweep['subsets_tried']} declared deletions were computed — the "
        f"ten one-type deletions in full above, and the ten best of the "
        f"forty-five two-type deletions, the rest being in the measurement "
        f"cache.  The smallest ratio any deletion reaches is "
        f"`{_exact(best_two['ratio'])}`, deleting "
        f"`{', '.join(best_two['dropped'])}`.  A deletion certifies only over "
        f"the types that remain: a classifier that cannot be asked about a "
        f"type it has deleted has earned nothing about that type, so this "
        f"table locates the spread and does not license a certificate.")
    return "\n".join(lines)


def block_deepholefail_establishes() -> str:
    """What the round establishes, and what stays on the record beside it."""
    data = _deepholefail()
    if data is None:
        return _deepholefail_stale()
    counts = data["counts"]
    spread = data["spread"]
    sweep = data["leave_out"]
    negative = data["original_negative"]
    lines = [
        f"**The failures are described rather than hypothesised.**  Each of "
        f"the {len(data['failures'])} carries its rank and its exact margin "
        f"to every reference.  {counts['near_miss']} of them are second by "
        f"less than a tenth of the separation and "
        f"{counts['d_absent_from_shortlist']} have the correct answer outside "
        f"the first three ranks — the two diagnoses that point in opposite "
        f"directions, now separated by measurement.",
        "",
        f"**The spread is localised.**  The worst within-type spread belongs "
        f"to `{spread['worst_type']}` at `{_exact(spread['worst_spread'])}`, "
        f"and the closest reference pair is "
        f"`{spread['closest_pair'][0]} / {spread['closest_pair'][1]}` at "
        f"`{_exact(spread['separation'])}`.  Whether the two are the same "
        f"object is the question the round was taken to answer, and the "
        f"answer is `{data['same_mechanism']}`.",
        "",
        f"**The certificate is not earned.**  Over the full ten-type "
        f"reference set the ratio is `{_exact(spread['rho_seed'])}` on the "
        f"seed reading and `{_exact(spread['rho_all'])}` over every "
        f"perturbation, against a criterion of 1.  The best of the "
        f"{sweep['subsets_tried']} deletions reaches "
        f"`{_exact(sweep['best_two']['ratio'])}`, and a deletion certifies "
        f"only over what remains.  The escalation round's negative therefore "
        f"stands: `{negative['stands']}`.",
        "",
        f"**Three types are certified, and seven are not.**  The criterion "
        f"holds type by type for "
        f"{', '.join(f'`{name}`' for name in data['per_type']['certified'])}, "
        f"so for those the naming is a certificate rather than a faculty.  "
        f"The remaining seven include both members of each of the two "
        f"closest pairs, which is exactly where the four failures are.",
        "",
        "**A negative that survives a finer reading is a stronger statement "
        "than the negative was.**  That is the result this round is entitled "
        "to, and it is the one it reports.",
    ]
    return "\n".join(lines)


# ===========================================================================
#  QUERY_ESCALATION_STUDY.md -- escalation as a step of the query loop
# ===========================================================================

def _queryesc_stale() -> str:
    from ..reasoning import query_escalation as qesc
    return ("The stored measurements of the escalation loop do not describe "
            f"the modules as they now stand (`{qesc.state()['verdict']}`), so "
            "nothing is reported here rather than a figure taken from code "
            "that has moved.  Run `python3 -m glm_universal.tools queryesc "
            "--write`.")


def _queryesc() -> Optional[Mapping[str, object]]:
    from ..reasoning import query_escalation as qesc
    return qesc.current()


def block_queryesc_tier() -> str:
    """The coarse read: does it hold, and does it buy anything."""
    data = _queryesc()
    if data is None:
        return _queryesc_stale()
    safety = data["safety"]
    utility = data["utility"]
    classified = data["classified"]
    principled = sum(1 for row in classified if not row["escalatable"])
    return "\n".join([
        f"**Both gates hold.**  Over the whole evaluation set of "
        f"{safety['cases']} cases, all {safety['answered_directly']} the "
        f"runtime answers directly come back identical through the loop, at "
        f"the first rung and for the first rung's cost — "
        f"{len(safety['answers_moved'])} answers moved and "
        f"{len(safety['principled_refusals_converted'])} principled refusals "
        f"were converted into answers.  Of the "
        f"{len(classified)} declared refusals, **{principled}** are "
        f"classified non-escalatable before the ladder is climbed."
        if safety["holds"] else
        f"**Gate 1 fails**: {len(safety['answers_moved'])} answers moved and "
        f"{len(safety['principled_refusals_converted'])} principled refusals "
        f"were converted.  Nothing else here is claimed.",
        "",
        f"The loop buys something: of the {utility['probes']} declared probes, "
        f"{utility['answered']} are answered and "
        f"{len(utility['resolved_above_the_first_rung'])} of those are "
        f"reached *above* the first rung — "
        f"{', '.join(repr(name) for name in utility['resolved_above_the_first_rung'])} "
        f"— at a cost of "
        f"{', '.join(str(cost) for cost in utility['escalated_cost'])} "
        f"against {utility['direct_cost']} for a direct answer.  "
        f"{len(utility['certified_absences'])} refusals are certified "
        f"absences within the declared radius of "
        f"{data['radius']} edits.",
    ])


def block_queryesc_ladders() -> str:
    """The tower, and every declared ladder."""
    data = _queryesc()
    if data is None:
        return _queryesc_stale()
    lines = ["| rung | reading | cost | what it reads |", "|---|---|---|---|"]
    for layer in data["layers"]:
        lines.append(f"| `{layer['key']}` | {layer['title']} | "
                     f"{layer['cost']} | {layer['description']} |")
    lines.append("")
    lines.append("| query kind | ladder | rungs | cost of climbing to the top |")
    lines.append("|---|---|---|---|")
    for row in data["ladders"]:
        lines.append(f"| `{row['kind']}` | "
                     f"{' -> '.join(row['rungs'])} | {row['height']} | "
                     f"{row['top_cost']} |")
    lines.append("")
    lines.append(
        f"{data['kinds_with_a_ladder_above_one_rung']} of "
        f"{len(data['ladders'])} declared kinds have a ladder taller than one "
        f"rung, and the tallest is {data['tallest_ladder']}.  A one-rung "
        f"ladder is a declaration that no rung of this tower reads that "
        f"kind's refusals, not an omission.")
    return "\n".join(lines)


def block_queryesc_safety() -> str:
    """Gate 1: nothing already answered moves, and no principled refusal turns."""
    data = _queryesc()
    if data is None:
        return _queryesc_stale()
    safety = data["safety"]
    rows = ["| check | reading |", "|---|---|",
            f"| evaluation cases run both ways | {safety['cases']} |",
            f"| answered by the direct path | {safety['answered_directly']} |",
            f"| answers that moved | {len(safety['answers_moved'])} |",
            f"| answers that cost more than the first rung | "
            f"{len(safety['answers_costing_more_than_the_first_rung'])} |",
            f"| principled refusals converted into answers | "
            f"{len(safety['principled_refusals_converted'])} |",
            f"| gate 1 | `{safety['holds']}` |"]
    rows.append("")
    rows.append(
        "A question the register answers is answered exactly as it was — same "
        "text, same rung, same cost — and the ladder is recorded in the "
        "payload beside the answer rather than written into it.")
    return "\n".join(rows)


def block_queryesc_probes() -> str:
    """Gate 2: every declared probe, with the rung it stopped at."""
    data = _queryesc()
    if data is None:
        return _queryesc_stale()
    lines = ["| probe | kind | ladder | outcome | rung | cost | "
             "classification |", "|---|---|---|---|---|---|---|"]
    for row in data["probes"]:
        outcome = ("answered" if row["answered"] else
                   ("refused, absence certified"
                    if row["certified_absence"] else "refused"))
        lines.append(
            f"| `{row['query']}` | {row['kind']} | "
            f"{' -> '.join(row['ladder'])} | {outcome} | {row['layer']} | "
            f"{row['cost']} | {row['refusal_tag'] or '—'} |")
    utility = data["utility"]
    lines.append("")
    lines.append(
        f"Answered by rung: "
        f"{', '.join(f'{key} {value}' for key, value in sorted(utility['answered_by_layer'].items()))}.  "
        f"Gate 2 asks for at least one probe resolving above the first rung "
        f"and there are {len(utility['resolved_above_the_first_rung'])}: "
        f"`{utility['has_an_instance']}`.")
    return "\n".join(lines)


def block_queryesc_classified() -> str:
    """Every declared refusal, and whether the loop was allowed to climb."""
    data = _queryesc()
    if data is None:
        return _queryesc_stale()
    lines = ["| case | kind | classification | escalated | outcome |",
             "|---|---|---|---|---|"]
    for row in data["classified"]:
        tag = row["tag"] or ("answered as a refusal in prose"
                             if row["answered_as_prose"] else "—")
        outcome = ("answered" if row["answered"] else
                   f"refused at {row['layer']}")
        lines.append(f"| {row['id']} | {row['kind']} | {tag} | "
                     f"{'yes' if row['escalatable'] else 'no'} | "
                     f"{outcome} |")
    principled = sum(1 for row in data["classified"]
                     if not row["escalatable"])
    climbed = [row["id"] for row in data["classified"] if row["escalatable"]]
    lines.append("")
    lines.append(
        f"{principled} of {len(data['classified'])} declared refusals are "
        f"non-escalatable, decided by {data['markers']} declared markers "
        f"before any rung above the first is run.  The "
        f"{len(climbed)} that were climbed — {', '.join(climbed)} — are "
        f"absences, and the ladder returned a refusal at the top of the tower "
        f"for each of them, which is a stronger statement than the refusal at "
        f"the first rung was.")
    return "\n".join(lines)


def block_queryesc_establishes() -> str:
    """What the round establishes."""
    data = _queryesc()
    if data is None:
        return _queryesc_stale()
    safety = data["safety"]
    utility = data["utility"]
    principled = sum(1 for row in data["classified"]
                     if not row["escalatable"])
    return "\n".join([
        f"**Escalation is a step of the loop and costs nothing where it is "
        f"not needed.**  All {safety['answered_directly']} directly answered "
        f"evaluation cases come back identical, at the first rung, for the "
        f"first rung's cost.",
        "",
        f"**A refusal now carries its layer.**  Every refusal reports the "
        f"rung it was made at and whether the ladder was climbed; "
        f"{len(utility['certified_absences'])} of the probes return an "
        f"absence certified within {data['radius']} edits of an enumerated "
        f"index, which is a refusal that knows its own radius rather than a "
        f"shrug.",
        "",
        f"**The rule against converting a principled refusal holds, and it "
        f"bites.**  {principled} of the {len(data['classified'])} declared "
        f"refusals are non-escalatable and are never climbed; none of them is "
        f"answered at any rung.",
        "",
        f"**The loop has instances rather than only machinery.**  "
        f"{len(utility['resolved_above_the_first_rung'])} declared probes "
        f"resolve above the first rung: one by resolving a constant through "
        f"the reference layer, the rest by a lookup that names its layer.  "
        f"Each is reported as more expensive than a direct answer, which is "
        f"the point of charging for rungs.",
    ])


# ===========================================================================
#  CUMULATIVITY_STUDY.md -- a layer ships with its refinement check
# ===========================================================================

def _cumulativity() -> Mapping[str, object]:
    from ..reasoning import cumulativity as cum
    return cum.cumulativity_report()


def block_cumul_tier() -> str:
    """The coarse read: does every declared family pass its own check."""
    data = _cumulativity()
    families = data["families"]
    conflated = sum(loss["count"] for family in families
                    for loss in family["conflations"])
    return (
        f"**The rule holds, and it is checked rather than intended.**  "
        f"{data['count']} declared layer families, {data['shipped']} of them "
        f"shipped; {data['edges_checked']} declared refinement edges are "
        f"verified on their probe sets and {data['non_edges_checked']} "
        f"declared non-edges are witnessed.  {len(data['defects'])} shipped "
        f"family carries a defect.  Separately, and not as a defect, the "
        f"check reports {conflated} conflated pairs across the rungs: a "
        f"conflation is what a rung cannot see, and the remedy for it is a "
        f"joint reading rather than a refinement.")


def block_cumul_families() -> str:
    """Every declared family, and what its check returned."""
    data = _cumulativity()
    lines = ["| family | ships | rungs | edges | non-edges | verdict |",
             "|---|---|---|---|---|---|"]
    for family in data["families"]:
        verdict = "passes" if family["passes"] else "DEFECT"
        lines.append(
            f"| `{family['key']}` | {'yes' if family['shipped'] else 'no'} | "
            f"{' -> '.join(family['rungs'])} | {len(family['edges'])} | "
            f"{len(family['non_edges'])} | {verdict} |")
    lines.append("")
    for family in data["families"]:
        lines.append(f"* `{family['key']}` — {family['title']}.  "
                     f"{family['note']}")
    return "\n".join(lines)


def block_cumul_edges() -> str:
    """Edge by edge: the pairs checked, and what was found."""
    data = _cumulativity()
    lines = ["| family | edge | pairs checked | refines | metric dominates |",
             "|---|---|---|---|---|"]
    for family in data["families"]:
        for edge in family["edges"]:
            dominates = ("—" if not edge["metrics_comparable"]
                         else str(edge["metric_dominates"]))
            lines.append(
                f"| `{edge['family']}` | `{edge['lower']}` → "
                f"`{edge['higher']}` | {edge['pairs']} | {edge['refines']} | "
                f"{dominates} |")
    lines.append("")
    lines.append("| family | declared non-edge | witnessed | witness |")
    lines.append("|---|---|---|---|")
    for family in data["families"]:
        for edge in family["non_edges"]:
            left, right = edge["witness"]
            lines.append(
                f"| `{edge['family']}` | `{edge['lower']}` → "
                f"`{edge['higher']}` | {edge['witnessed']} | "
                f"{left} / {right} |")
    return "\n".join(lines)


def block_cumul_conflations() -> str:
    """What each rung cannot see, reported as a resolution and not a defect."""
    data = _cumulativity()
    lines = ["| family | rung | pairs conflated |", "|---|---|---|"]
    for family in data["families"]:
        for loss in family["conflations"]:
            lines.append(f"| `{loss['family']}` | `{loss['rung']}` | "
                         f"{loss['count']} |")
    lines.append("")
    lines.append(data["rule"])
    return "\n".join(lines)


# ===========================================================================
#  REVIEW_SWEEP_STUDY.md -- which stalled results are worth re-reading
# ===========================================================================

def _review_sweep() -> Mapping[str, object]:
    from ..reasoning import review_sweep as rvs
    return rvs.review_sweep_report()


def block_review_tier() -> str:
    """The coarse read: how the register sorts, and what it licenses."""
    data = _review_sweep()
    by_class = data["by_class"]
    return (
        f"**The register is written before the next re-reading, and it sorts "
        f"by what the coarse reading threw away.**  {data['count']} stalled "
        f"results: "
        + ", ".join(f"{len(by_class[name])} {name}"
                    for name in data["classes"])
        + f".  A re-reading is licensed for "
        + (", ".join(f"`{key}`" for key in data["recoverable"])
           or "nothing")
        + f", and {len(data['defects'])} entries carry a defect.")


def block_review_register() -> str:
    """Every entry, in the order the rule gives."""
    data = _review_sweep()
    lines = ["| rank | entry | class | read at | discarded quantity |",
             "|---|---|---|---|---|"]
    for index, row in enumerate(data["entries"], start=1):
        mark = "" if row["supported"] else " *(unsupported)*"
        lines.append(
            f"| {index} | `{row['key']}`{mark} | {row['verdict']} | "
            f"{row['reading']} | {row['discarded']} |")
    return "\n".join(lines)


def block_review_next() -> str:
    """What each entry needs, which is not always a finer reading."""
    data = _review_sweep()
    lines = ["| entry | stall | what it needs |", "|---|---|---|"]
    for row in data["entries"]:
        lines.append(f"| `{row['key']}` | {row['stall']} | "
                     f"{row['next_step']} |")
    return "\n".join(lines)


# ===========================================================================
#  REVERSE_CALL_PLANNER_STUDY.md -- the planner, in the sandbox
# ===========================================================================

def _planner() -> Mapping[str, object]:
    #  The cached form: the report costs a minute and a half to take, five
    #  blocks below quote it, and the cache is keyed on the digest of the code
    #  that produces it, so a changed planner is re-measured and an unchanged
    #  one is not re-measured five times per check.
    from ..sandbox import planner as pl
    return pl.cached_planner_report()


def block_plannersandbox_tier() -> str:
    """The coarse read: what the planner answers, and what it costs."""
    data = _planner()
    promotion = data["promotion"]
    beyond = data["answered_beyond_the_runtime"]
    failing = [name for name, value in promotion["checks"].items()
               if not value]
    return (
        f"**The planner answers {data['answered']} of "
        f"{len(data['tasks'])} declared tasks, and every answer it gives is "
        f"independently checked ({data['verified']} of "
        f"{data['answered']}).**  {len(beyond)} of them are questions the "
        f"plain runtime refuses: "
        f"{', '.join(repr(name) for name in beyond)}.  The remaining "
        f"{data['refused']} are refusals, each classified before it is "
        f"reported.  Every one of the "
        f"{len(promotion['checks'])} promotion lines is measured here, and "
        + ("all of them hold, so the promotion checklist reads `ready`."
           if promotion["ready"] else
           f"{len(failing)} do not: {', '.join(failing)}."))


def block_plannersandbox_tools() -> str:
    """The registry: every tool, its precondition and its price."""
    data = _planner()
    lines = ["| tool | cost | goals | checked | postcondition |",
             "|---|---|---|---|---|"]
    for tool in data["tools"]:
        lines.append(f"| `{tool['name']}` | {tool['cost']} | "
                     f"{', '.join(tool['goals'])} | "
                     f"{'yes' if tool['has_check'] else 'no'} | "
                     f"{tool['postcondition']} |")
    lines.append("")
    lines.append(f"The plan's budget is {data['budget']} and its sub-goal "
                 f"depth is {data['max_depth']}: both are declared in the "
                 f"module, and a tool skipped for want of budget is recorded "
                 f"as skipped rather than dropped.")
    return "\n".join(lines)


def block_plannersandbox_tasks() -> str:
    """Every declared task, planned, beside what the plain runtime does."""
    data = _planner()
    lines = ["| task | goal | outcome | tool | cost | checked | runtime |",
             "|---|---|---|---|---|---|---|"]
    for row in data["tasks"]:
        outcome = ("answered" if row["answered"]
                   else f"refused ({row['refusal_tag']})")
        lines.append(
            f"| `{row['task']}` | `{row['goal']}` | {outcome} | "
            f"{('`' + str(row['tool']) + '`') if row['tool'] else '—'} | "
            f"{row['cost']} | {'yes' if row['verified'] else 'no'} | "
            f"{'answers' if row['runtime_answered'] else 'refuses'} |")
    lines.append("")
    lines.append(f"Every task is reported, including the "
                 f"{data['refused']} the planner is expected to refuse: a "
                 f"task set of things that work measures nothing.")
    return "\n".join(lines)


def block_plannersandbox_fallback() -> str:
    """The whole evaluation set, under the declared fallback rule."""
    data = _planner()
    fallback = data["fallback"]
    lines = ["| reading | value |", "|---|---|",
             f"| evaluation cases | {fallback['cases']} |",
             f"| the runtime answers | {fallback['runtime_answered']} |",
             f"| the runtime refuses | {fallback['runtime_refused']} |",
             f"| of those, classified principled | "
             f"{fallback['principled_refusals']} |",
             f"| the planner is consulted on | "
             f"{fallback['planner_consulted']} |",
             f"| principled refusals reaching the planner | "
             f"{len(fallback['principled_refusals_offered_to_the_planner'])} |",
             f"| answers the runtime does not give | "
             f"{len(fallback['gained'])} |",
             f"| **safety gate** | **{fallback['safety_holds']}** |",
             f"| **utility gate** | **{fallback['utility_holds']}** |",
             "",
             f"The rule measured is: {fallback['rule']}."]
    return "\n".join(lines)


def block_plannersandbox_promotion() -> str:
    """The promotion checklist, computed."""
    data = _planner()
    promotion = data["promotion"]
    lines = ["| line | reading |", "|---|---|"]
    checks = promotion["checks"]
    for name in promotion.get("order", list(checks)):
        lines.append(f"| {name.replace('_', ' ')} | {checks[name]} |")
    lines.append(f"| **ready to leave the sandbox** | "
                 f"**{promotion['ready']}** |")
    lines.append("")
    lines.append(promotion["rule"])
    lines.append("")
    lines.append(data["limits"])
    return "\n".join(lines)


# ===========================================================================
#  ITERATION_COST_STUDY.md -- what one round of this repository costs
# ===========================================================================

def _cost() -> Mapping[str, object]:
    from . import cost as ct
    return ct.cost_report()


def block_cost_tier() -> str:
    """The coarse read: how much of a rebuild is now reuse."""
    data = _cost()
    addresses = data["addresses"]
    planner = data["planner"]
    figures = data["figures"]
    return (
        f"**Rebuilding both address books from nothing decodes "
        f"{_thousands(addresses['decodes_from_nothing'])} vectors; rebuilding "
        f"them against the stored books decodes "
        f"{_thousands(addresses['decodes_now'])}.**  The planner's report, "
        f"one pass over {planner['evaluation_cases_per_report']} evaluation "
        f"cases, is quoted by {planner['blocks_quoting_the_report']} generated "
        f"blocks and is now taken {planner['reports_per_check_now']} times per "
        f"check instead of {planner['reports_per_check_before']}.  "
        f"{figures['in_the_corpus']} figures inside sentences, across "
        f"{figures['documents']} documents, are emitted rather than typed.")


def block_cost_addresses() -> str:
    """The two address books, decoded and reused."""
    addresses = _cost()["addresses"]
    lean = addresses["lean"]
    documents = addresses["documents"]
    lines = ["| book | units | decodes from nothing | decodes now | reused |",
             "|---|---|---|---|---|",
             f"| Lean declarations | {_thousands(lean['declarations'])} | "
             f"{_thousands(lean['decodes_from_nothing'])} | "
             f"{_thousands(lean['decodes_now'])} | "
             f"{_thousands(lean['reused'])} |",
             f"| corpus sections | {_thousands(documents['sections'])} | "
             f"{_thousands(documents['decodes_from_nothing'])} | "
             f"{_thousands(documents['decodes_now'])} | "
             f"{_thousands(documents['reused'])} |",
             "",
             f"Reuse is checked, not assumed: each rebuild re-decodes a "
             f"sample of the answers it reused and reports any that moved "
             f"({lean['audit']['audited']} sampled in the declaration book, "
             f"{documents['audit']['audited']} in the document book, "
             + ("none moved)." if lean["audit"]["holds"]
                and documents["audit"]["holds"] else "**some moved**).")]
    return "\n".join(lines)


def block_cost_planner() -> str:
    """The report the five planner blocks share."""
    planner = _cost()["planner"]
    lines = ["| reading | value |", "|---|---|",
             f"| blocks quoting the report | "
             f"{planner['blocks_quoting_the_report']} |",
             f"| evaluation cases per report | "
             f"{planner['evaluation_cases_per_report']} |",
             f"| reports taken per check, before | "
             f"{planner['reports_per_check_before']} |",
             f"| reports taken per check, now | "
             f"{planner['reports_per_check_now']} |",
             f"| stored report | {planner['store']} |",
             "",
             "The store is keyed on the import closure of "
             "`glm_universal.sandbox.planner` -- the code the report is "
             "derived from, and not the documents that quote it -- so a "
             "documentation round does not re-take it and a change to the "
             "planner does."]
    return "\n".join(lines)


def block_cost_figures() -> str:
    """The figures that are emitted into sentences."""
    figures = _cost()["figures"]
    registry = ", ".join(f"`{name}`" for name in sorted(FIGURES))
    return (
        f"{figures['registered']} figures are registered and "
        f"{figures['in_the_corpus']} markers carry them, across "
        f"{figures['documents']} documents.  A marker whose text is not what "
        f"its figure now says is what `--refresh` rewrites and what `--check` "
        f"fails on."
        f"\n\nThe registry: {registry}.")


# ===========================================================================
#  The inline figures
# ===========================================================================
#
#  The rule for putting a figure here rather than leaving it to prose: it has
#  to be **cheap** (a document check renders every one of them) and it has to
#  be **live** (computed from the tree as it stands, not read out of a cache
#  that can be stale).  Anything that fails either test belongs in a generated
#  block, where staleness can be reported in the body.

@memo
def _sentences() -> Mapping[str, str]:
    """The generated sentences of :mod:`glm_universal.figures`, once."""
    from .. import figures as fg
    return fg.sentences()


def _sentence(name: str) -> str:
    """One generated sentence, or a refusal that says which one is missing.

    A sentence is absent when the figure behind it has never been measured --
    the suite totals before a complete run.  Emitting a zero there would be a
    claim; emitting this is a statement about the evidence.
    """
    found = _sentences().get(name)
    return found if found is not None else f"(not yet measured: {name})"


def _lean_declaration_count() -> str:
    from ..reasoning import lean_address as la
    return f"{len(la.declarations()):,}"


def _lean_declaration_files() -> str:
    from ..reasoning import lean_address as la
    return f"{len({d.file for d in la.declarations()}):,}"


def _corpus_sections() -> str:
    from . import address as ad
    return f"{len(ad.units()):,}"


FIGURES: Dict[str, Callable[[], str]] = {
    #  The sentences the figures module already generates, now writable into
    #  a paragraph instead of quoted from a table by hand.
    "suite": lambda: _sentence("suite"),
    "test-files": lambda: _sentence("test_files"),
    "lean-files": lambda: _sentence("lean_files"),
    "evaluation-cases": lambda: _sentence("evaluation_cases"),
    "registers": lambda: _sentence("registers"),
    "query-kinds": lambda: _sentence("query_kinds"),
    "report-subjects": lambda: _sentence("report_subjects"),
    #  The bare counts, for the sentences that put the unit in their own
    #  words ("a 147-case evaluation"): the same figure, without the noun.
    "test-file-count": lambda: _sentence("test_files").split()[0],
    "lean-file-count": lambda: _sentence("lean_files").split()[0],
    "evaluation-case-count": lambda: _sentence("evaluation_cases").split()[0],
    #  The cost figures, so the sentences of the iteration-cost study are
    #  emitted by the same mechanism they describe.
    "rebuild-decodes-from-nothing":
        lambda: f"{_cost()['addresses']['decodes_from_nothing']:,}",
    "rebuild-decodes-now":
        lambda: f"{_cost()['addresses']['decodes_now']:,}",
    "planner-reports-per-check":
        lambda: str(_cost()["planner"]["reports_per_check_before"]),
    #  And the corpus's own sizes, which no sentence pattern can cover
    #  because the documentation quotes subsets of them too.
    "lean-declarations": _lean_declaration_count,
    "lean-declaration-files": _lean_declaration_files,
    "corpus-documents": lambda: f"{len(inv.documents()):,}",
    "corpus-state-documents": lambda: f"{len(inv.state_documents()):,}",
    "corpus-archive-documents": lambda: f"{len(inv.archive_documents()):,}",
    "corpus-sections": _corpus_sections,
}


BLOCKS: Dict[str, Callable[[], str]] = {
    "corpus-inventory": block_corpus_inventory,
    "corpus-largest": block_corpus_largest,
    "corpus-tiers": block_corpus_tiers,
    "corpus-reachability": block_corpus_reachability,
    "corpus-address": block_corpus_address,
    "corpus-retrieval": block_corpus_retrieval,
    "corpus-guarantee": block_corpus_guarantee,
    "corpus-generation": block_corpus_generation,
    "lean-corpus": block_lean_corpus,
    "lean-scale": block_lean_scale,
    "lean-readback": block_lean_readback,
    "lean-injectivity": block_lean_injectivity,
    "lean-classes": block_lean_classes,
    "lean-neighbours": block_lean_neighbours,
    "retrieval-setup": block_retrieval_setup,
    "retrieval-declarations": block_retrieval_declarations,
    "retrieval-goals": block_retrieval_goals,
    "retrieval-hybrid": block_retrieval_hybrid,
    "retrieval-guarantee": block_retrieval_guarantee,
    "landscape-verdict": block_landscape_verdict,
    "landscape-spectrum": block_landscape_spectrum,
    "landscape-depth": block_landscape_depth,
    "landscape-primary": block_landscape_primary,
    "landscape-comparison": block_landscape_comparison,
    "landscape-golay": block_landscape_golay,
    "deephole-verdict": block_deephole_verdict,
    "deephole-holes": block_deephole_holes,
    "deephole-references": block_deephole_references,
    "deephole-queries": block_deephole_queries,
    "deephole-controls": block_deephole_controls,
    "deephole-claims": block_deephole_claims,
    "deepholeesc-verdict": block_deepholeesc_verdict,
    "deepholeesc-ladder": block_deepholeesc_ladder,
    "deepholeesc-reproduction": block_deepholeesc_reproduction,
    "deepholeesc-decision": block_deepholeesc_decision,
    "deepholeesc-controls": block_deepholeesc_controls,
    "deepholeesc-secondaries": block_deepholeesc_secondaries,
    "deepholefail-tier": block_deepholefail_tier,
    "deepholefail-reproduction": block_deepholefail_reproduction,
    "deepholefail-failures": block_deepholefail_failures,
    "deepholefail-diagnoses": block_deepholefail_diagnoses,
    "deepholefail-spread": block_deepholefail_spread,
    "deepholefail-leaveout": block_deepholefail_leaveout,
    "deepholefail-establishes": block_deepholefail_establishes,
    "queryesc-tier": block_queryesc_tier,
    "queryesc-ladders": block_queryesc_ladders,
    "queryesc-safety": block_queryesc_safety,
    "queryesc-probes": block_queryesc_probes,
    "queryesc-classified": block_queryesc_classified,
    "queryesc-establishes": block_queryesc_establishes,
    "cumul-tier": block_cumul_tier,
    "review-tier": block_review_tier,
    "review-register": block_review_register,
    "review-next": block_review_next,
    "cumul-families": block_cumul_families,
    "cumul-edges": block_cumul_edges,
    "cumul-conflations": block_cumul_conflations,
    "plannersandbox-tier": block_plannersandbox_tier,
    "plannersandbox-tools": block_plannersandbox_tools,
    "plannersandbox-tasks": block_plannersandbox_tasks,
    "plannersandbox-fallback": block_plannersandbox_fallback,
    "plannersandbox-promotion": block_plannersandbox_promotion,
    "cost-tier": block_cost_tier,
    "cost-addresses": block_cost_addresses,
    "cost-planner": block_cost_planner,
    "cost-figures": block_cost_figures,
}


# ===========================================================================
#  Reading and refreshing the blocks
# ===========================================================================

def block_spans(text: str) -> Tuple[Tuple[str, str], ...]:
    """The ``(name, body)`` of every generated block in a document."""
    return tuple((match.group("name"), match.group("body"))
                 for match in _BLOCK.finditer(text))


def _render_block(name: str) -> str:
    renderer = BLOCKS.get(name)
    if renderer is None:
        raise KeyError(f"no renderer registered for block {name!r}")
    body = renderer().rstrip("\n")
    return body + "\n"


def figure_spans(text: str) -> Tuple[Tuple[str, str], ...]:
    """The ``(name, body)`` of every inline figure in a document."""
    return tuple((match.group("name"), match.group("body"))
                 for match in _FIGURE.finditer(text))


def _render_figure(name: str) -> str:
    renderer = FIGURES.get(name)
    if renderer is None:
        raise KeyError(f"no renderer registered for figure {name!r}")
    return renderer()


def refresh_text(text: str) -> str:
    """The document with every generated block and inline figure re-rendered."""
    def replace(match: "re.Match[str]") -> str:
        name = match.group("name")
        if name not in BLOCKS:
            return match.group(0)
        return match.group("open") + _render_block(name) + match.group("close")

    #  Blocks first, and the history regions are taken from the text they
    #  leave behind: an offset into the original text would not point at the
    #  same character once a block body has changed length.
    after_blocks = _BLOCK.sub(replace, text)
    history = _history_regions(after_blocks)

    def replace_figure(match: "re.Match[str]") -> str:
        name = match.group("name")
        if name not in FIGURES:
            return match.group(0)
        if any(start <= match.start() < end for start, end in history):
            #  A record of a past round keeps the figures it was written
            #  with.  :func:`figure_report` reports the marker as a defect --
            #  a live figure has no business in an archive -- but nothing
            #  here rewrites it, because rewriting it would falsify the
            #  record.
            return match.group(0)
        return (match.group("open") + _render_figure(name)
                + match.group("close"))

    return _FIGURE.sub(replace_figure, after_blocks)


def figure_report() -> Dict[str, object]:
    """Every inline figure in the corpus: where it is, and whether it is fresh.

    Three defects are separated, because they want different answers:
    ``unknown`` is a marker naming a figure nothing emits, ``stale`` is a
    marker whose text is not what the figure now says, and ``in_history`` is a
    live figure written inside a passage marked as a record of a past round --
    which must not be rewritten, and therefore must not be marked.
    """
    fresh = 0
    stale: List[Tuple[str, str]] = []
    unknown: List[Tuple[str, str]] = []
    in_history: List[Tuple[str, str]] = []
    documents = 0
    for doc in inv.source_documents():
        spans = figure_spans(doc.text)
        if spans:
            documents += 1
        history = _history_regions(doc.text)
        for match in _FIGURE.finditer(doc.text):
            name = match.group("name")
            if any(start <= match.start() < end for start, end in history):
                in_history.append((doc.path, name))
                continue
            if name not in FIGURES:
                unknown.append((doc.path, name))
            elif match.group("body") == _render_figure(name):
                fresh += 1
            else:
                stale.append((doc.path, name))
    return {
        "registry": tuple(sorted(FIGURES)),
        "documents_with_figures": documents,
        "figures": fresh + len(stale) + len(unknown) + len(in_history),
        "fresh": fresh,
        "stale": tuple(stale),
        "unknown": tuple(unknown),
        "in_history": tuple(in_history),
        "holds": not stale and not unknown and not in_history,
    }


def generation_shape() -> Dict[str, object]:
    """How much is emitted: documents, blocks, lines.  Renders nothing."""
    root = inv.REPOSITORY_ROOT
    generated_lines = 0
    for path in GENERATED:
        target = root / path
        if target.exists():
            generated_lines += target.read_text(encoding="utf-8").count("\n")
    blocks = 0
    block_lines = 0
    documents_with_blocks = 0
    figures = 0
    documents_with_figures = 0
    for doc in inv.source_documents():
        spans = block_spans(doc.text)
        marks = figure_spans(doc.text)
        if marks:
            documents_with_figures += 1
            figures += len(marks)
        if not spans:
            continue
        documents_with_blocks += 1
        for _name, body in spans:
            blocks += 1
            block_lines += body.count("\n")
    return {
        "generated_documents": len(GENERATED),
        "rendered_here": len(GENERATORS),
        "generated_document_lines": generated_lines,
        "blocks": blocks,
        "block_lines": block_lines,
        "documents_with_blocks": documents_with_blocks,
        "figures": figures,
        "documents_with_figures": documents_with_figures,
        "figure_registry": tuple(sorted(FIGURES)),
        "registry": tuple(sorted(BLOCKS)),
    }


def generation_report() -> Dict[str, object]:
    """What is emitted, and whether every emitted part is current.

    Renders every block to compare it against what is on disk, so this is the
    check rather than the summary; :func:`generation_shape` is the summary, and
    it is what a generated block is allowed to quote.
    """
    shape = dict(generation_shape())
    fresh = 0
    stale: List[Tuple[str, str]] = []
    for doc in inv.source_documents():
        for name, body in block_spans(doc.text):
            if name not in BLOCKS:
                stale.append((doc.path, name))
            elif body == _render_block(name):
                fresh += 1
            else:
                stale.append((doc.path, name))
    shape["fresh_blocks"] = fresh
    shape["stale"] = tuple(stale)
    inline = figure_report()
    shape["fresh_figures"] = inline["fresh"]
    shape["stale_figures"] = inline["stale"]
    shape["unknown_figures"] = inline["unknown"]
    shape["figures_in_history"] = inline["in_history"]
    return shape


def write_generated(root: Optional[Path] = None) -> Tuple[str, ...]:
    """Write every generated document this module can render."""
    base = Path(root) if root is not None else inv.REPOSITORY_ROOT
    written: List[str] = []
    for path, renderer in sorted(GENERATORS.items()):
        target = base / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(renderer(), encoding="utf-8")
        written.append(path)
    return tuple(written)


def refresh(write: bool = False, root: Optional[Path] = None
            ) -> Dict[str, object]:
    """Re-render every generated block, and every generated document.

    With ``write=False`` this is a check: it reports which blocks and which
    documents differ from a fresh rendering and changes nothing.
    """
    base = Path(root) if root is not None else inv.REPOSITORY_ROOT
    #  Generated documents first, then the blocks: a block may quote the size
    #  of a generated document, and no generated document reads a block, so
    #  this order is the one in which a single pass converges.
    stale_documents: List[str] = []
    for path, renderer in sorted(GENERATORS.items()):
        target = base / path
        rendered = renderer()
        current = (target.read_text(encoding="utf-8") if target.exists()
                   else None)
        if current != rendered:
            stale_documents.append(path)
            if write:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(rendered, encoding="utf-8")
    changed: List[str] = []
    for doc in inv.source_documents():
        if not block_spans(doc.text) and not figure_spans(doc.text):
            continue
        fresh = refresh_text(doc.text)
        if fresh != doc.text:
            changed.append(doc.path)
            if write:
                (base / doc.path).write_text(fresh, encoding="utf-8")
    if write and (changed or stale_documents):
        from ..derived import clear_memos
        clear_memos()
    return {
        "wrote": write,
        "blocks_changed": tuple(changed),
        "documents_written": tuple(stale_documents),
        "current": not changed and not stale_documents,
    }

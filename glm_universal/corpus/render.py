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


# ===========================================================================
#  STACK_RELAY_STUDY.md -- the faculties, and who carries whom
# ===========================================================================

#: How each query set of the relay study is described where it is tabled.
_STACK_SETS: Dict[str, str] = {
    "tuning": "tuning — the stride the gate was chosen on",
    "holdout": "holdout — a disjoint stride, never looked at while choosing",
    "goal": "goal — both strides again, asked as bare goals",
}


def _stack() -> Optional[Mapping[str, object]]:
    from . import measurements as ms
    data = ms.current()
    if data is None:
        return None
    stack = data.get("stack")
    return stack if isinstance(stack, Mapping) else None


def _stack_cell(cells: Sequence[Mapping[str, object]], k: int
                ) -> Mapping[str, object]:
    for cell in cells:
        if cell["k"] == k:
            return cell
    raise KeyError(k)


def block_stack_sets() -> str:
    """The leader alone against the relay, on all three query sets."""
    data = _stack()
    if data is None:
        return _lean_stale()
    ladder = list(data["k_ladder"])
    rows = []
    for name, entry in data["sets"].items():
        for who in ("leader", "relay"):
            label = ("text alone" if who == "leader" else "**the relay**")
            line = [_STACK_SETS.get(name, name), label,
                    entry["queries"]]
            for k in ladder:
                cell = _stack_cell(entry[who], k)
                text = f"{cell['hits']} ({per_cent(cell['hit_rate'])})"
                line.append(f"**{text}**" if who == "relay" else text)
            line.append(per_cent(entry[f"{who}_precision"]))
            rows.append(line)
    header = ["query set", "who answers", "queries"] \
        + [f"hit@{k}" for k in ladder] + ["precision@5"]
    lines = _table(header, rows)
    carried = sum(len(entry["carried"]) for entry in data["sets"].values())
    lost = sum(len(entry["lost"]) for entry in data["sets"].values())
    fired = sum(entry["fired"] for entry in data["sets"].values())
    queries = sum(entry["queries"] for entry in data["sets"].values())
    lines.extend([
        "",
        f"The gate is {data['gate']} and fires on {fired} of {queries} "
        f"queries.  Across the three sets the geometry carries **{carried}** "
        f"queries the text control misses at k = 5 and loses **{lost}**.  "
        "The relay "
        "beats the text control on every set: "
        f"{'yes' if data['verdict']['relay_beats_text_on_every_set'] else 'no'}"
        "; it is never below the text control at any k: "
        f"{'yes' if data['verdict']['relay_never_below_leader'] else 'no'}.",
    ])
    return "\n".join(lines)


def block_stack_carried() -> str:
    """Which queries the geometry carried, by name."""
    data = _stack()
    if data is None:
        return _lean_stale()
    rows = []
    for name, entry in data["sets"].items():
        rows.append([_STACK_SETS.get(name, name),
                     entry["fired"],
                     ", ".join(f"`{q}`" for q in entry["carried"]) or "—",
                     ", ".join(f"`{q}`" for q in entry["lost"]) or "none"])
    lines = _table(("query set", "gate fired", "carried by the geometry",
                    "lost"), rows)
    lines.extend([
        "",
        "A *carried* query is one the text control misses at k = 5 and the "
        "relay hits; a *lost* query is the reverse, which is the column the "
        "gate exists to keep empty.",
    ])
    return "\n".join(lines)


def block_stack_controls() -> str:
    """The same relay to a control partner: is the gain the geometry's?"""
    data = _stack()
    if data is None:
        return _lean_stale()
    rows = []
    for name, entry in data["sets"].items():
        line = [_STACK_SETS.get(name, name)]
        line.append(len(entry["carried"]))
        for partner in ("digest_random", "name"):
            control = data["controls"][partner][name]
            line.append(len(control["carried"]))
        rows.append(line)
    lines = _table(("query set", "carried by the two address books",
                    "carried by digest + reshuffle",
                    "carried by name search"), rows)
    lines.extend([
        "",
        "Over the three sets the geometry carries more than the "
        "digest-and-reshuffle control: "
        f"{'yes' if data['verdict']['geometry_carries_more_than_control'] else 'no'}"
        "; it never carries fewer on a set: "
        f"{'yes' if data['verdict']['geometry_never_carries_fewer_than_control'] else 'no'}"
        "; it carries more than the name search: "
        f"{'yes' if data['verdict']['geometry_carries_more_than_name'] else 'no'}.",
    ])
    return "\n".join(lines)


def block_stack_sweep() -> str:
    """The gate swept: a mechanism, or a fitted constant?"""
    data = _stack()
    if data is None:
        return _lean_stale()
    rows = [[str(row["gate"]), row["fired"], per_cent(row["hit_at_5"]),
             per_cent(row["precision_at_5"]), row["carried"], row["lost"]]
            for row in data["sweep"]]
    lines = _table(("gate", "queries it fires on", "hit@5", "precision@5",
                    "carried", "lost"), rows)
    lines.extend([
        "",
        "On the tuning set.  The gain is strict on "
        f"{data['verdict']['gain_strict_gates']} of the thresholds from "
        f"1/20 to 1/4, up to and including "
        f"{data['verdict']['gain_strict_to_gate']}; across the whole of that "
        "band the relay is never below the text control: "
        f"{'yes' if data['verdict']['gain_never_below_across_the_gate'] else 'no'}.",
    ])
    return "\n".join(lines)


# ===========================================================================
#  ANONYMOUS_REGISTER_STUDY.md -- the register only the address reads
# ===========================================================================

#: How each faculty is described where the anonymous register is tabled.
_ANON_FACULTIES: Dict[str, str] = {
    "text": "text — exact overlap of the identifiers",
    "lexical": "lexical — the identifier address book",
    "address": "**address — the structural address book**",
    "name": "name — substring search over the names",
    "digest": "digest — a control that knows nothing",
    "random": "random — a seeded permutation",
}


def _anonymous() -> Optional[Mapping[str, object]]:
    from . import measurements as ms
    data = ms.current()
    if data is None:
        return None
    found = data.get("anonymous")
    return found if isinstance(found, Mapping) else None


def block_anonymous_faculties() -> str:
    """Every faculty, read plainly and read with the names taken away."""
    data = _anonymous()
    if data is None:
        return _lean_stale()
    k = data["k"]
    rows = []
    for faculty, label in _ANON_FACULTIES.items():
        plain = _stack_cell(data["plain"][faculty], k)
        after = _stack_cell(data["anonymous"][faculty], k)
        rows.append([label,
                     f"{plain['hits']} ({per_cent(plain['hit_rate'])})",
                     f"{after['hits']} ({per_cent(after['hit_rate'])})"])
    lines = _table(("faculty", f"hit@{k}, names kept",
                    f"hit@{k}, names replaced"), rows)
    lines.extend([
        "",
        f"{data['queries']} queries over a corpus of {data['corpus']} "
        f"declarations; chance at k = {k} is "
        f"{per_cent(data['chance_at_5'])}.  The text search collapses: "
        f"{'yes' if data['verdict']['text_collapses_without_the_names'] else 'no'}"
        "; the identifier address book collapses with it: "
        f"{'yes' if data['verdict']['lexical_collapses_too'] else 'no'}"
        "; the structural address holds: "
        f"{'yes' if data['verdict']['address_holds'] else 'no'}"
        "; and it leads every other faculty in this register: "
        f"{'yes' if data['verdict']['address_is_the_clear_leader'] else 'no'}.",
    ])
    return "\n".join(lines)


def block_anonymous_invariance() -> str:
    """What a renaming can and cannot move in the shipped feature map."""
    data = _anonymous()
    if data is None:
        return _lean_stale()
    queries = data["queries"]
    invariant = data["invariant_queries"]
    rows = [
        ["queries whose syntax coordinates are untouched", invariant,
         f"{per_cent(Fraction(invariant, queries))} of {queries}"],
        ["queries where a type-word coordinate moves", queries - invariant,
         "the declaration's own name spells `Nat`, `Int`, `Rat`, `Set` or "
         "`Decidable`, and the shipped map counts those words wherever they "
         "occur"],
        ["queries where any other syntax coordinate moves",
         data["moved_outside_the_type_vocabulary"],
         "none, which is `GLM.Anonymous.features_anonymise` holding of the "
         "code"],
    ]
    lines = _table(("reading", "queries", "what it means"), rows)
    lines.extend([
        "",
        "The declared vocabulary a query keeps is "
        f"{data['kept_vocabulary']} words.  Placeholders fresh against the "
        "corpus: "
        f"{'yes' if data['verdict']['placeholders_are_fresh'] else 'no'}.",
    ])
    return "\n".join(lines)


def block_anonymous_relay() -> str:
    """The stack's own gate, unchanged, meeting the register."""
    data = _anonymous()
    if data is None:
        return _lean_stale()
    k = data["k"]
    rows = []
    for label, key in (("names kept", "relay_plain"),
                       ("names replaced", "relay_anonymous")):
        entry = data[key]
        leader = _stack_cell(entry["leader"], k)
        relayed = _stack_cell(entry["relay"], k)
        rows.append([label, entry["queries"], entry["fired"],
                     f"{leader['hits']} ({per_cent(leader['hit_rate'])})",
                     f"**{relayed['hits']} "
                     f"({per_cent(relayed['hit_rate'])})**"])
    lines = _table(("reading", "queries", "gate fires on",
                    f"text alone, hit@{k}", f"the relay, hit@{k}"), rows)
    lines.extend([
        "",
        f"The gate is {data['gate']}, the one the relay study already "
        "carries, not re-tuned for this register.  It hands over on most of "
        "the register: "
        f"{'yes' if data['verdict']['gate_hands_over'] else 'no'}"
        "; and the relay beats the text leader here: "
        f"{'yes' if data['verdict']['relay_beats_text_in_the_register'] else 'no'}.",
    ])
    return "\n".join(lines)


def block_anonymous_verdict() -> str:
    """Every pre-registered claim of the register, as it fell."""
    data = _anonymous()
    if data is None:
        return _lean_stale()
    rows = [[f"`{claim}`", "holds" if value else "**fails**"]
            for claim, value in data["verdict"].items()]
    return "\n".join(_table(("claim", "verdict"), rows))


def block_stack_tiebreak() -> str:
    """The other arrangement: the geometry inside the text layer's ties."""
    data = _stack()
    if data is None:
        return _lean_stale()
    ladder = list(data["k_ladder"])
    rows = []
    for label, schemes in data["tiebreak"].items():
        for scheme, entry in schemes.items():
            line = [label, scheme]
            for k in ladder:
                cell = _stack_cell(entry["hits"], k)
                line.append(f"{cell['hits']} ({per_cent(cell['hit_rate'])})")
            line.append(per_cent(entry["precision_at_5"]))
            rows.append(line)
    header = ["query set", "tie-break"] + [f"hit@{k}" for k in ladder] \
        + ["precision@5"]
    lines = _table(header, rows)
    verdict = data["tiebreak_verdict"]
    lines.extend([
        "",
        "Ranking by text overlap and breaking the many exact ties by address "
        "distance instead of by name.  It beats the shipped name tie-break on "
        f"hits: {'yes' if verdict['beats_name_tiebreak_on_hits'] else 'no'}; "
        "on precision: "
        f"{'yes' if verdict['beats_name_tiebreak_on_precision'] else 'no'}.",
    ])
    return "\n".join(lines)


def block_stack_vision() -> str:
    """The second register: the same relay over the ARC grids."""
    from ..reasoning import vision_stack as vs
    data = vs.vision_report()
    rows = [
        ("puzzles", _thousands(data["puzzles"])),
        ("candidates proposed", _thousands(data["proposed"])),
        ("candidates surviving the look", _thousands(data["survived"])),
        ("share the cheap filter removes before the gate",
         f"**{per_cent(data['filter_saving'])}**"),
        ("puzzles the leading faculty solves alone",
         _thousands(data["leader_solves"])),
        ("puzzles the relay solves", f"**{_thousands(data['relay_solves'])}**"),
        ("solved rules that also produce the held-out test output",
         _thousands(len(data["test_solved"]))),
        ("queries the gate fired on", _thousands(data["gate_fired"])),
    ]
    lines = _table(("what was measured", "result"), rows)
    carry = "; ".join(
        f"**{faculty}** — {', '.join('`' + name + '`' for name in names)}"
        for faculty, names in data["carry"].items())
    lines.extend([
        "",
        f"Who carried what: {carry}.  More than one faculty carries a "
        f"puzzle: {'yes' if data['verdict']['more_than_one_faculty_carries'] else 'no'}; "
        "the relay is never behind the leading faculty: "
        f"{'yes' if data['verdict']['relay_never_behind_leader'] else 'no'}.",
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
#  NOW_RECEIPT_STUDY.md -- what a delta-sigma accumulator actually records
# ===========================================================================

def _now() -> Mapping[str, object]:
    #  Cached on the digest of the module: the report carries one timing, and
    #  a timing re-measured on every document check would drift the blocks for
    #  no reason.  `corpus --refresh` re-takes it when the code moves.
    from ..reasoning import now_receipt as nrc
    return nrc.cached_now_receipt_report()


def block_now_tier() -> str:
    """The coarse read: what the receipt holds, and what it cannot."""
    data = _now()
    levels = data["levels"]
    collisions = data["collisions"]
    shortcut = data["shortcut"]
    first = shortcut["rows"][0]
    return (
        f"**The accumulator is exactly the fractional part of the integral of "
        f"its input, and that is all it is.**  Over {levels['cases']} runs of "
        f"the supplied demonstrations the state recovers the emitted count "
        f"{levels['level_2_recovered_the_count']} times out of "
        f"{levels['cases']} — and so does the target and the tick count with "
        f"the state withheld, {levels['level_0_predicted_the_count']} times "
        f"out of {levels['cases']}, so the receipt adds nothing to what the "
        f"program already says.  Enumerated exhaustively, "
        f"{collisions['histories']:,} histories leave "
        f"{collisions['distinct_receipts']} distinct receipts, the largest "
        f"class holding {collisions['largest_receipt_class']:,} of them.  The "
        f"same identity is what makes the shipped modulator cheap: at the "
        f"{shortcut['shipped_tick_count']} ticks the `real` query kind runs, "
        f"the average costs {first['average_closed_us']} µs read off the "
        f"target against {first['average_loop_us']} µs run as a loop, with "
        f"identical output.")


def block_now_levels() -> str:
    """The supplied recovery ladder, with the control it omits."""
    data = _now()["levels"]
    lines = ["| target | ticks | ones | level 2: from the state | "
             "level 0: from the target alone | state denominator (bits) |",
             "|---|---:|---:|---:|---:|---:|"]
    for row in data["rows"]:
        lines.append(
            f"| `{row['target']}` | {row['ticks']:,} | {row['count']:,} | "
            f"{row['level_2_recovered']:,} | {row['level_0_predicted']:,} | "
            f"{row['state_denominator_bits']} |")
    lines.append("")
    lines.append(
        f"Every row recovers the count both ways, so the state is not what "
        f"recovers it: {data['level_0_predicted_the_count']} of "
        f"{data['cases']} are right with the state withheld.  The state's "
        f"denominator never exceeds the target's: "
        f"{data['denominator_never_exceeds_the_target']}.")
    return "\n".join(lines)


def block_now_capacity() -> str:
    """How many receipts a run can leave, against how long it runs."""
    data = _now()["capacity"]
    horizons = data["horizons"]
    header = " | ".join(f"{value:,} ticks" for value in horizons)
    lines = [f"| grid | target | {header} | bound | bits |",
             "|---|---|" + "---:|" * len(horizons) + "---:|---:|"]
    for row in data["rows"]:
        counts = " | ".join(str(reading["distinct"])
                            for reading in row["distinct_states"])
        lines.append(f"| 1/{row['grid']} | `{row['target']}` | {counts} | "
                     f"{row['bound']} | {row['bits']} |")
    lines.append("")
    lines.append(
        "The count of distinct receipts saturates at the grid and stays "
        "there: running for a thousand times as long adds none. "
        "`GLM.NowReceipt.acc_mem_grid` is the statement and "
        "`GLM.NowReceipt.receipt_pigeonhole` the consequence.")
    return "\n".join(lines)


def block_now_collisions() -> str:
    """Every schedule of the enumerated space, grouped by its receipt."""
    data = _now()["collisions"]
    witness = data["witness"]
    return (
        f"| reading | value |\n|---|---|\n"
        f"| alphabet | {', '.join('`' + value + '`' for value in data['alphabet'])} |\n"
        f"| schedule length | {data['length']} |\n"
        f"| histories enumerated | {data['histories']:,} |\n"
        f"| distinct receipts | {data['distinct_receipts']} |\n"
        f"| largest class of histories sharing one | "
        f"{data['largest_receipt_class']:,} |\n"
        f"| distinct (receipt, count) pairs | "
        f"{data['distinct_receipt_and_count']} |\n"
        f"| largest class sharing one of those | "
        f"{data['largest_receipt_and_count_class']:,} |\n"
        f"| the receipt identifies the history | "
        f"{data['receipt_is_injective']} |\n\n"
        f"The first colliding pair the enumeration meets is "
        f"`({', '.join(witness[0])})` and `({', '.join(witness[1])})`.")


def block_now_dimensions() -> str:
    """The seven dimensions, and how many of them are free."""
    data = _now()["dimensions"]
    return (
        f"| reading | value |\n|---|---|\n"
        f"| dimensions claimed | {data['claimed_dimensions']} |\n"
        f"| free readings | {data['independent_readings']} "
        f"({', '.join(data['free_dimensions'])}) |\n"
        f"| labels | {', '.join(data['labelled_dimensions'])} |\n"
        f"| determined by the composition | "
        f"{', '.join(data['determined_by_the_composition'])} |\n"
        f"| determined by the coordinate | "
        f"{', '.join(data['determined_by_the_coordinate'])} |\n"
        f"| carrier pairs built to share a coordinate | "
        f"{data['pairs_with_the_same_coordinate']} |\n"
        f"| entropy reading agrees on every pair | "
        f"{data['entropy_agrees_on_every_pair']} |\n"
        f"| tax differs on | {data['tax_differs_on']} of them |\n"
        f"| compositions sharing one coordinate | "
        f"{data['fibre_of_one_coordinate']:,} on the "
        f"{data['grid_values_per_coordinate']}-value grid |")


def block_now_float() -> str:
    """The float control: the comparative claim, run."""
    data = _now()["float_control"]
    lines = ["| ticks | exact ones | float ones | recovered from the float state |",
             "|---:|---:|---:|---:|"]
    for row in data["rows"]:
        lines.append(f"| {row['ticks']:,} | {row['exact_count']:,} | "
                     f"{row['float_count']:,} | "
                     f"{row['recovered_from_the_float_state']:,} |")
    lines.append("")
    divergence = data["first_bit_divergence"]
    lines.append(
        f"Over {data['horizon']:,} ticks the two loops emit the same bit at "
        f"every tick ("
        + ("no divergence" if divergence is None
           else f"first divergence at tick {divergence:,}")
        + f"), and the supplied recovery holds from the float state as well "
          f"as from the exact one: {data['float_recovery_always_holds']}.  "
          f"What exactness buys is the bound, not this horizon.")
    return "\n".join(lines)


def block_now_shortcut() -> str:
    """The loop against the closed form, on the shipped path."""
    data = _now()["shortcut"]
    lines = ["| ticks | average: loop | average: read off | bits: loop | "
             "bits: read off |", "|---:|---:|---:|---:|---:|"]
    for row in data["rows"]:
        lines.append(
            f"| {row['ticks']:,} | {row['average_loop_us']} µs | "
            f"{row['average_closed_us']} µs | {row['bits_loop_us']} µs | "
            f"{row['bits_closed_us']} µs |")
    lines.append("")
    lines.append(
        f"Identical output on every case measured: {data['identical_output']}. "
        f"The shipped `real` query kind runs {data['shipped_tick_count']} "
        f"ticks per question, which is the first row.  The theorems are "
        + ", ".join(f"`{name}`" for name in data["theorems"]) + ".")
    return "\n".join(lines)


def block_now_tasks() -> str:
    """The declared task set: answered, or refused with a witness."""
    data = _now()["tasks"]
    lines = ["| task | outcome |", "|---|---|"]
    for name in data["answered"]:
        lines.append(f"| {name} | answered |")
    for row in data["refusals"]:
        lines.append(f"| {row['task']} | refused — {row['reason']} |")
    lines.append("")
    lines.append(
        f"The supplied recipe answers all {data['supplied_recipe_answers']}, "
        f"so it is wrong on {data['supplied_recipe_wrong_answers']}: the four "
        f"questions whose answer the receipt does not determine.  Refusing "
        f"those four removes {data['wrong_answers_removed']} wrong answers at "
        f"a cost of {data['refusals_paid']} refusals, and every refusal "
        f"carries the colliding pair that justifies it "
        f"({data['every_refusal_carries_a_witness']}).")
    return "\n".join(lines)


def block_now_claims() -> str:
    """Every claim of the supplied studies, and how it fell."""
    data = _now()["claims"]
    lines = ["| claim of the supplied studies | verdict | settled by |",
             "|---|---|---|"]
    for row in data:
        lines.append(f"| {row['claim']} | **{row['verdict']}** | "
                     f"`{row['settled_by']}` |")
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
def _package_figures() -> Mapping[str, object]:
    """The package's own counts -- sub-packages, modules, kinds -- once."""
    from .. import figures as fg
    return fg.package_figures()


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


def _repo_storage() -> Mapping[str, object]:
    """The overlay's own stored bytes, split into cache and primary data.

    Cheap (one ``stat`` per artefact) and live (taken from the tree as it
    stands), so it meets the rule for an inline figure: the storage side of
    the generate-rather-than-store ledger can be written into a sentence
    instead of typed out and left to age.
    """
    from ..reasoning import generative as gn
    return gn.repo_storage_report()


def _normesc_figure(which: str, field: str) -> str:
    """One count of one reading of the norm-family measurement."""
    data = _norm()
    if data is None:
        return "stale"
    totals = data[which]["orders"]["totals"]["middle_out"]
    if field == "queries":
        return _thousands(int(totals["correct"]) + int(totals["wrong"])
                          + int(totals["refused"]))
    return _thousands(totals[field])


def _normesc_rungs(which: str) -> str:
    data = _norm()
    return "stale" if data is None else _thousands(len(data[which]["ladder"]))


def _normesc_sweep(field: str) -> str:
    data = _norm()
    return "stale" if data is None else _thousands(data["sweep"][field])


def _normfamily_count(field: str) -> str:
    data = _norm()
    if data is None:
        return "stale"
    family = data["family"]
    if field == "norms":
        return _thousands(len(family["completeness"]["norms"]))
    return _thousands(family[field])


def _opesc_figure(field: str) -> str:
    data = _opesc()
    if data is None:
        return "stale"
    rows = list(data["operations"]) + [data["equation"]]
    if field == "count":
        return _thousands(len(rows))
    program = [row for row in rows if row["operation"] == "program"][0]
    if field == "program_correct":
        return _thousands(program["escalation"]["correct"])
    if field == "program_wrong":
        return _thousands(program["escalation"]["wrong"])
    return _thousands(program["escalation"]["queries"])


def _secondread_figure(field: str) -> str:
    from ..reasoning import second_reading as sr
    data = sr.current()
    if data is None:
        return "stale"
    marks = data["marks_report"]
    if field == "adopted":
        return _thousands(len(marks["adopted"]))
    if field == "configurations":
        return _thousands(len(marks["verdicts"]))
    if field == "shipped":
        return str(marks["shipped"] or "none")
    shipped = marks["shipped"]
    if shipped is None:
        return "none"
    row = marks["verdicts"][shipped]
    if field == "program_correct":
        return _thousands(row["program"]["correct"])
    if field == "program_wrong":
        return _thousands(row["program"]["wrong"])
    if field == "program_refused":
        return _thousands(row["program"]["refused"])
    if field == "given_up":
        return _thousands(row["answers_given_up"])
    return _thousands(row["matched_control_wrongs_removed"])


_oracle_cache: Optional[Mapping[str, object]] = None


def _oracle() -> Mapping[str, object]:
    """The hand-translation experiment, run once per process.

    It keeps no measurement cache because it needs none: the twenty
    translations are asked of a live session in a few seconds, so every
    document that quotes it quotes what the solvers do now.
    """
    global _oracle_cache
    if _oracle_cache is None:
        from ..reasoning import probe_oracle as po
        _oracle_cache = po.oracle_report()
    return _oracle_cache


def _oracle_figure(field: str) -> str:
    data = _oracle()
    if field in ("parsed", "surface", "absent"):
        return _thousands(data["counts"][field])          # type: ignore[index]
    if field == "questions":
        return _thousands(data["questions"])
    if field == "english":
        return _thousands(data["english_correct"])
    return _thousands(data["parser_worth"])


def block_oracle_split() -> str:
    """What hand-translation is worth, and what it is not."""
    data = _oracle()
    counts = data["counts"]                               # type: ignore[index]
    rows = [
        ("`parsed`", counts["parsed"],
         "a query in the existing grammar answers it, with the declared "
         "fragment in the declared field"),
        ("`surface`", counts["surface"],
         "no query answers it and a shipped register or function holds it: "
         "the fact is here, and no query kind returns it"),
        ("`absent`", counts["absent"],
         "nothing here holds it, and the refusal is the right answer"),
    ]
    lines = _table(("class", "questions", "what it means"), rows)
    kinds = ", ".join(
        f"{count} `{kind}`"
        for kind, count in sorted(data["witness_kinds"].items())   # type: ignore[union-attr]
        if count)
    moved = ", ".join(f"`{key}`"
                      for key in data["moved_by_translation"])     # type: ignore[union-attr]
    lines.extend([
        "",
        str(data["verdict"]),
        "",
        f"The questions the translation moves are {moved}.  What holds the "
        f"`surface` class: {kinds}.",
        "",
        str(data["reading"]),
    ])
    return "\n".join(lines)


def block_oracle_table() -> str:
    """Every question, its translation, and where the answer actually is."""
    data = _oracle()
    rows = []
    for row in data["rows"]:                              # type: ignore[union-attr]
        query = f"`{row['query']}`" if row["query"] else "*not expressible*"
        held = (f"`{row['witness']}` ({row['witness_kind']})"
                if row["witness"] else "--")
        rows.append((row["domain"], f"*{row['question']}*", query,
                     f"`{row['class']}`", f"`{row['asked']['kind']}`", held))
    return "\n".join(_table(
        ("domain", "question", "the query it should become", "class",
         "kind returned", "what holds the answer"), rows))


_fieldsurface_cache: Optional[Mapping[str, object]] = None


def _fieldsurface() -> Mapping[str, object]:
    """What the field surface was worth, run once per process.

    Like the oracle it keeps no measurement cache: both translation tables
    are asked of a live session in seconds, so a document that quotes this
    quotes what the solvers do now.
    """
    global _fieldsurface_cache
    if _fieldsurface_cache is None:
        from ..reasoning import field_surface as fs
        _fieldsurface_cache = fs.surface_report()
    return _fieldsurface_cache


def _fieldsurface_figure(field: str) -> str:
    data = _fieldsurface()
    census = data["census"]                               # type: ignore[index]
    if field == "moved":
        return _thousands(data["moved_count"])
    if field == "predicted":
        return _thousands(data["predicted"])
    if field == "held":
        return _thousands(len(data["surface_keys"]))      # type: ignore[arg-type]
    if field in ("parsed-after", "surface-after"):
        return _thousands(data["after"][field.split("-")[0]])   # type: ignore[index]
    if field in ("parsed-before", "surface-before"):
        return _thousands(data["before"][field.split("-")[0]])  # type: ignore[index]
    if field == "tables":
        return _thousands(census["tables"])               # type: ignore[index]
    if field == "rows":
        return _thousands(census["rows"])                 # type: ignore[index]
    if field == "fields":
        return _thousands(census["distinct_fields"])      # type: ignore[index]
    return _thousands(census["addressable_pairs"])        # type: ignore[index]


def block_fieldsurface_split() -> str:
    """The twenty questions before the surface and after it."""
    data = _fieldsurface()
    before = data["before"]                               # type: ignore[index]
    after = data["after"]                                 # type: ignore[index]
    rows = [(f"`{name}`", before[name], after[name],
             _thousands(after[name] - before[name]) if after[name] >= before[name]
             else str(after[name] - before[name]))
            for name in ("parsed", "surface", "absent")]
    lines = _table(("class", "before the surface", "after it", "change"), rows)
    lines.extend([
        "",
        str(data["verdict"]),
        "",
        str(data["caveat"]),
    ])
    return "\n".join(lines)


def block_fieldsurface_questions() -> str:
    """The ten held-and-unreachable questions, one row each."""
    data = _fieldsurface()
    rows = []
    for row in data["rows"]:                              # type: ignore[union-attr]
        query = f"`{row['query']}`" if row["query"] else "*not expressible*"
        rows.append((f"`{row['key']}`", f"*{row['question']}*", query,
                     f"`{row['before']}`", f"`{row['after']}`",
                     f"`{row['kind']}`"))
    return "\n".join(_table(
        ("question", "asked in English", "the field query it becomes",
         "before", "after", "kind returned"), rows))


_ordering_cache: Optional[Mapping[str, object]] = None


def _ordering() -> Mapping[str, object]:
    """What the ordering operation answers and refuses, run once per process.

    Like the oracle and the field surface it keeps no measurement cache: the
    declared comparisons and both translation tables are asked of a live
    session in seconds, so a document that quotes this quotes what the
    solvers do now.
    """
    global _ordering_cache
    if _ordering_cache is None:
        from ..reasoning import coordinate_order as cord
        _ordering_cache = cord.comparison_report()
    return _ordering_cache


def _ordering_figure(field: str) -> str:
    data = _ordering()
    if field in ("declared", "answered", "refused", "as-declared"):
        return _thousands(data[field.replace("-", "_")])   # type: ignore[index]
    if field == "reasons":
        return _thousands(len(data["refusal_reasons"]))    # type: ignore[arg-type]
    if field in ("parsed-after", "surface-after"):
        return _thousands(data["after"][field.split("-")[0]])   # type: ignore[index]
    if field in ("parsed-before", "surface-before"):
        return _thousands(data["before"][field.split("-")[0]])  # type: ignore[index]
    if field == "held":
        return _thousands(data["surface_keys"])            # type: ignore[index]
    return _thousands(data["surface_parsed"])              # type: ignore[index]


def block_ordering_declared() -> str:
    """The declared comparison set: what was predicted, and what happened."""
    data = _ordering()
    rows = []
    for row in data["rows"]:                              # type: ignore[union-attr]
        rows.append((f"`{row['key']}`", f"`{row['field']}`",
                     f"`{row['left']}` / `{row['right']}`",
                     f"`{row['expected']}`", f"`{row['outcome']}`",
                     "yes" if row["as_declared"] else "**no**"))
    lines = _table(
        ("comparison", "coordinate", "rows", "declared", "outcome",
         "as declared"), rows)
    lines.extend([
        "",
        str(data["verdict"]),
        "",
        str(data["caveat"]),
    ])
    return "\n".join(lines)


def block_ordering_split() -> str:
    """The twenty probe questions before the operation and after it."""
    data = _ordering()
    before = data["before"]                               # type: ignore[index]
    after = data["after"]                                 # type: ignore[index]
    rows = [(f"`{name}`", before[name], after[name],
             _thousands(after[name] - before[name])
             if after[name] >= before[name]
             else str(after[name] - before[name]))
            for name in ("parsed", "surface", "absent")]
    lines = _table(
        ("class", "before the operation", "after it", "change"), rows)
    lines.extend([
        "",
        f"{_thousands(data['surface_parsed'])} of the "   # type: ignore[index]
        f"{_thousands(data['surface_keys'])} questions the oracle called "
        f"held and unreachable are now parsed; the one the field surface "
        f"declared unreachable is the one this operation closes.",
    ])
    return "\n".join(lines)


_extremum_cache: Optional[Mapping[str, object]] = None


def _extremum() -> Mapping[str, object]:
    """What the extremum operation folds and refuses, run once per process.

    Like the ordering measurement beside it, it keeps no cache on disk: the
    declared columns are read off a live session in seconds, so a document
    that quotes this quotes what the operation does now.
    """
    global _extremum_cache
    if _extremum_cache is None:
        from ..reasoning import column_extremum as cx
        _extremum_cache = cx.extremum_report()
    return _extremum_cache


def _extremum_figure(field: str) -> str:
    data = _extremum()
    if field in ("declared", "answered", "refused", "as-declared", "ties"):
        return _thousands(data[field.replace("-", "_")])   # type: ignore[index]
    if field == "reasons":
        return _thousands(len(data["refusal_reasons"]))    # type: ignore[arg-type]
    return _thousands(data["reasons_declared"])            # type: ignore[index]


def block_extremum_declared() -> str:
    """The declared column set: what was predicted, and what happened."""
    data = _extremum()
    rows = []
    for row in data["rows"]:                              # type: ignore[union-attr]
        winners = row.get("winners", ())
        named = ("--" if not winners
                 else (f"{len(winners)} rows" if len(winners) > 1
                       else f"`{winners[0]}`"))
        rows.append((f"`{row['key']}`", f"`{row['end']}`",
                     f"`{row['field']}`", f"`{row['table']}`",
                     f"`{row['expected']}`", f"`{row['outcome']}`", named,
                     "yes" if row["as_declared"] else "**no**"))
    lines = _table(
        ("column", "end", "coordinate", "table", "declared", "outcome",
         "rows at the end", "as declared"), rows)
    lines.extend([
        "",
        str(data["verdict"]),
        "",
        str(data["caveat"]),
    ])
    return "\n".join(lines)


_scales_cache: Optional[Mapping[str, object]] = None


def _scales() -> Mapping[str, object]:
    """What the declared conversion table relates, run once per process.

    Like the two measurements above it, it keeps no cache on disk: the
    declared questions are run against a live session in seconds, so a
    document that quotes this quotes what the table does now.
    """
    global _scales_cache
    if _scales_cache is None:
        from ..reasoning import scale_conversion as sc
        _scales_cache = sc.conversion_report()
    return _scales_cache


def _scales_figure(field: str) -> str:
    data = _scales()
    census = data["census"]                               # type: ignore[index]
    if field in ("declared", "answered", "refused", "as-declared",
                 "declared-rows", "quantities", "offsets"):
        return _thousands(data[field.replace("-", "_")])  # type: ignore[index]
    if field in ("scales", "pairs", "bridged"):
        return _thousands(census[field])                  # type: ignore[index]
    return _thousands(census["refused"])                  # type: ignore[index]


def block_scales_table() -> str:
    """The declared table itself: one row per scale, with its source."""
    data = _scales()
    rows = [(f"`{row['scale']}`", row["quantity"], f"`{row['unit']}`",
             f"`{row['factor']}`", f"`{row['offset']}`", row["source"])
            for row in data["table"]]                     # type: ignore[union-attr]
    lines = _table(
        ("scale", "quantity", "unit", "factor", "offset", "declared from"),
        rows)
    census = data["census"]                               # type: ignore[index]
    lines.extend([
        "",
        f"{_thousands(data['declared_rows'])} rows over "     # type: ignore[index]
        f"{_thousands(data['quantities'])} quantities, "      # type: ignore[index]
        f"{_thousands(data['non_unit_factors'])} of them with a factor "  # type: ignore[index]
        f"other than 1 and {_thousands(data['offsets'])} with an offset.  "  # type: ignore[index]
        f"Of the {_thousands(census['pairs'])} pairs of the "  # type: ignore[index]
        f"{_thousands(census['scales'])} numeric scales the field surface "  # type: ignore[index]
        f"holds, the table relates {_thousands(census['bridged'])} and "  # type: ignore[index]
        f"leaves {_thousands(census['refused'])} refused.",   # type: ignore[index]
    ])
    return "\n".join(lines)


def block_scales_declared() -> str:
    """The declared question set: what was predicted, and what happened."""
    data = _scales()
    rows = []
    for row in data["rows"]:                              # type: ignore[union-attr]
        operands = row["operands"]
        if row["kind"] == "order":
            asked = (f"`{operands[0]}` of `{operands[1]}` against "
                     f"`{operands[2]}` of `{operands[3]}`")
        else:
            asked = f"largest `{operands[0]}`" + (
                f" in `{operands[1]}`" if operands[1] else "")
        rows.append((f"`{row['key']}`", asked, f"`{row['expected']}`",
                     f"`{row['outcome']}`",
                     f"`{row.get('unit', '')}`" if row.get("unit") else "--",
                     "yes" if row["as_declared"] else "**no**"))
    lines = _table(
        ("question", "asked as", "declared", "outcome", "compared in",
         "as declared"), rows)
    lines.extend([
        "",
        str(data["verdict"]),
        "",
        str(data["caveat"]),
    ])
    return "\n".join(lines)


_conversation_cache: Optional[Mapping[str, object]] = None


def _conversation() -> Mapping[str, object]:
    """What the conversation layer binds and refuses, run once per process.

    Like the two measurements above it, it keeps no cache on disk: the
    declared follow-ups are run against a live session in about ten seconds,
    so a document that quotes this quotes what the operation does now.
    """
    global _conversation_cache
    if _conversation_cache is None:
        from ..runtime import conversation as cv
        _conversation_cache = cv.conversation_report()
    return _conversation_cache


def _conversation_figure(field: str) -> str:
    data = _conversation()
    if field == "reasons":
        return _thousands(len(data["refusal_reasons"]))    # type: ignore[arg-type]
    return _thousands(data[field.replace("-", "_")])       # type: ignore[index]


_binding_cache: Optional[Mapping[str, object]] = None


def _binding() -> Mapping[str, object]:
    """What a bound relation gives back, run once per process."""
    global _binding_cache
    if _binding_cache is None:
        from ..reasoning import role_binding as rb
        _binding_cache = rb.binding_report()
    return _binding_cache


def _binding_figure(field: str) -> str:
    data = _binding()
    fibres = data["fibres"]                               # type: ignore[index]
    product = data["product"]                             # type: ignore[index]
    if field in ("carriers", "recoverable", "ambiguous", "largest-fibre",
                 "readings", "control-wrong"):
        return _thousands(fibres[field.replace("-", "_")])  # type: ignore[index]
    if field == "product-recoverable":
        return _thousands(product["recoverable"])         # type: ignore[index]
    if field == "product-zero":
        return _thousands(product["with_zero_coordinate"])  # type: ignore[index]
    if field == "reasons":
        return _thousands(len(data["refusal_reasons"]))   # type: ignore[arg-type]
    return _thousands(data[field.replace("-", "_")])      # type: ignore[index]


def block_binding_declared() -> str:
    """The declared bindings: what was predicted, and what came back."""
    data = _binding()
    rows = []
    for row in data["rows"]:                              # type: ignore[union-attr]
        rows.append((f"`{row['key']}`", f"`{row['role']}`",
                     f"`{row['a']}` / `{row['b']}`", f"`{row['domain']}`",
                     f"`{row['expected']}`", f"`{row['outcome']}`",
                     f"`{row['control']}`" if row["control"] else "--",
                     "yes" if row["as_declared"] else "**no**"))
    lines = _table(
        ("binding", "role", "known / filler", "register", "declared",
         "outcome", "nearest-mask control", "as declared"), rows)
    lines.extend(["", str(data["verdict"]), "", str(data["caveat"])])
    return "\n".join(lines)


def block_binding_fibres() -> str:
    """The parity fibres of every register the session loads."""
    fibres = _binding()["fibres"]                         # type: ignore[index]
    rows = [(f"`{row['domain']}`", _thousands(row["carriers"]),
             _thousands(row["readings"]), _thousands(row["recoverable"]),
             _thousands(row["largest_fibre"]))
            for row in fibres["rows"]]                    # type: ignore[index]
    rows.append(("**all**", _thousands(fibres["carriers"]),   # type: ignore[index]
                 _thousands(fibres["readings"]),             # type: ignore[index]
                 _thousands(fibres["recoverable"]),          # type: ignore[index]
                 _thousands(fibres["largest_fibre"])))       # type: ignore[index]
    return "\n".join(_table(
        ("register", "carriers", "distinct readings", "nameable",
         "largest fibre"), rows))


_planstore_cache: Optional[Mapping[str, object]] = None


def _planstore() -> Mapping[str, object]:
    """What the plan store replays, run once per process."""
    global _planstore_cache
    if _planstore_cache is None:
        from ..runtime import plan_store as ps
        _planstore_cache = ps.plan_store_report()
    return _planstore_cache


def _planstore_figure(field: str) -> str:
    return _thousands(_planstore()[field.replace("-", "_")])  # type: ignore[index]


def block_planstore_declared() -> str:
    """The declared follow-ups, replayed: what each cost and what came back."""
    data = _planstore()
    rows = [(f"`{row['key']}`", f"`{row['text']}`", f"`{row['outcome']}`",
             "yes" if row["refused"] else "no",
             _thousands(row["trials_first"]),
             _thousands(row["trials_replayed"]),
             "yes" if row["replays"] else "**no**",
             f"`{row['coarse_outcome']}`")
            for row in data["rows"]]                      # type: ignore[union-attr]
    lines = _table(
        ("follow-up", "the turn asked", "outcome", "a refusal",
         "trials first", "trials replayed", "replayed",
         "coarse-key control"), rows)
    lines.extend(["", str(data["verdict"]), "", str(data["caveat"])])
    return "\n".join(lines)


def block_conversation_declared() -> str:
    """The declared follow-up set: what was predicted, and what happened."""
    data = _conversation()
    rows = []
    for row in data["rows"]:                              # type: ignore[union-attr]
        script = row["script"]                            # type: ignore[index]
        rows.append((f"`{row['key']}`",
                     f"`{script[-1]}`",
                     _thousands(len(script) - 1),
                     f"`{row['expected']}`", f"`{row['outcome']}`",
                     f"`{row['control_recency']}`",
                     "yes" if row["as_declared"] else "**no**"))
    lines = _table(
        ("follow-up", "the turn asked", "turns before it", "declared",
         "outcome", "recency control", "as declared"), rows)
    lines.extend([
        "",
        str(data["verdict"]),
        "",
        str(data["caveat"]),
    ])
    return "\n".join(lines)


def block_fieldsurface_tables() -> str:
    """What the surface addresses: every declared table, with its size."""
    data = _fieldsurface()
    census = data["census"]                               # type: ignore[index]
    rows = [(f"`{entry['table']}`", f"`{entry['kind']}`",
             _thousands(entry["rows"]), _thousands(entry["fields"]),
             entry["gloss"])
            for entry in census["per_table"]]             # type: ignore[index]
    lines = _table(("table", "kind", "rows", "distinct fields", "what it is"),
                   rows)
    lines.extend([
        "",
        f"{_thousands(census['tables'])} tables, "        # type: ignore[index]
        f"{_thousands(census['rows'])} rows and "         # type: ignore[index]
        f"{_thousands(census['addressable_pairs'])} addressable "
        f"(row, field) pairs over "
        f"{_thousands(census['distinct_fields'])} distinct field names.",
    ])
    return "\n".join(lines)


def _probe_figure(field: str) -> str:
    data = _blockers()
    if data is None:
        return "stale"
    probe = data["probe"]
    if field in ("correct", "wrong", "refused"):
        return _thousands(probe["canonical"][field])
    if field == "questions":
        return _thousands(probe["questions"])
    if field == "pass_mark":
        return _thousands(probe["pass_mark"]["correct_at_least"])
    if field == "lexicon_held":
        return _thousands(data["lexicon"]["in_lexicon"])
    if field == "lexicon_words":
        return _thousands(data["lexicon"]["content_words"])
    return _thousands(sum(1 for row in data["ledger"]
                          if row["class"] == "derived"))



FIGURES: Dict[str, Callable[[], str]] = {
    #  The norm family and the escalation over it, so the sentences of
    #  NORM_FAMILY_STUDY.md quote the measurement rather than a memory of it.
    "normesc-correct": lambda: _normesc_figure("repaired", "correct"),
    "normesc-wrong": lambda: _normesc_figure("repaired", "wrong"),
    "normesc-refused": lambda: _normesc_figure("repaired", "refused"),
    "normesc-queries": lambda: _normesc_figure("repaired", "queries"),
    "normesc-rungs": lambda: _normesc_rungs("repaired"),
    "normesc-family-correct": lambda: _normesc_figure("declared", "correct"),
    "normesc-family-wrong": lambda: _normesc_figure("declared", "wrong"),
    "normesc-family-rungs": lambda: _normesc_rungs("declared"),
    "normesc-named-correct": lambda: _normesc_figure("named_rungs", "correct"),
    "normesc-named-rungs": lambda: _normesc_rungs("named_rungs"),
    "normesc-longest-safe": lambda: _normesc_sweep("longest_safe"),
    "normesc-first-broken": lambda: _normesc_sweep("first_broken"),
    "normfamily-rung-count": lambda: _normfamily_count("rung_count"),
    "normfamily-norms": lambda: _normfamily_count("norms"),
    #  The escalated operations.
    "opesc-count": lambda: _opesc_figure("count"),
    "opesc-program-correct": lambda: _opesc_figure("program_correct"),
    "opesc-program-wrong": lambda: _opesc_figure("program_wrong"),
    "opesc-program-queries": lambda: _opesc_figure("program_queries"),
    #  The second reading, its guards and the marks they are held to.
    "secondread-program-correct": lambda: _secondread_figure("program_correct"),
    "secondread-program-wrong": lambda: _secondread_figure("program_wrong"),
    "secondread-program-refused":
        lambda: _secondread_figure("program_refused"),
    "secondread-given-up": lambda: _secondread_figure("given_up"),
    "secondread-matched-removes":
        lambda: _secondread_figure("matched_removes"),
    "secondread-adopted": lambda: _secondread_figure("adopted"),
    "secondread-configurations":
        lambda: _secondread_figure("configurations"),
    "secondread-shipped": lambda: _secondread_figure("shipped"),
    #  The blockers study and its pre-registered probe.
    "probe-correct": lambda: _probe_figure("correct"),
    "probe-wrong": lambda: _probe_figure("wrong"),
    "probe-refused": lambda: _probe_figure("refused"),
    "probe-questions": lambda: _probe_figure("questions"),
    "probe-pass-mark": lambda: _probe_figure("pass_mark"),
    "probe-lexicon-held": lambda: _probe_figure("lexicon_held"),
    "probe-lexicon-words": lambda: _probe_figure("lexicon_words"),
    "probe-derived": lambda: _probe_figure("derived"),
    #  The hand-translation experiment against blocker 1.
    "oracle-parsed": lambda: _oracle_figure("parsed"),
    "oracle-surface": lambda: _oracle_figure("surface"),
    "oracle-absent": lambda: _oracle_figure("absent"),
    "oracle-questions": lambda: _oracle_figure("questions"),
    "oracle-english": lambda: _oracle_figure("english"),
    "oracle-parser-worth": lambda: _oracle_figure("parser_worth"),
    #  The field surface built against that prediction, and what it moved.
    "fieldsurface-moved": lambda: _fieldsurface_figure("moved"),
    "fieldsurface-predicted": lambda: _fieldsurface_figure("predicted"),
    "fieldsurface-held": lambda: _fieldsurface_figure("held"),
    "fieldsurface-parsed-before": lambda: _fieldsurface_figure("parsed-before"),
    "fieldsurface-parsed-after": lambda: _fieldsurface_figure("parsed-after"),
    "fieldsurface-surface-before":
        lambda: _fieldsurface_figure("surface-before"),
    "fieldsurface-surface-after": lambda: _fieldsurface_figure("surface-after"),
    "fieldsurface-tables": lambda: _fieldsurface_figure("tables"),
    "fieldsurface-rows": lambda: _fieldsurface_figure("rows"),
    "fieldsurface-fields": lambda: _fieldsurface_figure("fields"),
    "fieldsurface-pairs": lambda: _fieldsurface_figure("pairs"),
    "ordering-declared-count": lambda: _ordering_figure("declared"),
    "ordering-answered": lambda: _ordering_figure("answered"),
    "ordering-refused": lambda: _ordering_figure("refused"),
    "ordering-as-declared": lambda: _ordering_figure("as-declared"),
    "ordering-reasons": lambda: _ordering_figure("reasons"),
    "ordering-held": lambda: _ordering_figure("held"),
    "ordering-surface-parsed": lambda: _ordering_figure("surface-parsed"),
    "ordering-parsed-before": lambda: _ordering_figure("parsed-before"),
    "ordering-parsed-after": lambda: _ordering_figure("parsed-after"),
    "ordering-surface-before": lambda: _ordering_figure("surface-before"),
    "ordering-surface-after": lambda: _ordering_figure("surface-after"),
    "scales-rows": lambda: _scales_figure("declared-rows"),
    "scales-quantities": lambda: _scales_figure("quantities"),
    "scales-declared": lambda: _scales_figure("declared"),
    "scales-as-declared": lambda: _scales_figure("as-declared"),
    "scales-answered": lambda: _scales_figure("answered"),
    "scales-refused": lambda: _scales_figure("refused"),
    "scales-numeric": lambda: _scales_figure("scales"),
    "scales-pairs": lambda: _scales_figure("pairs"),
    "scales-bridged": lambda: _scales_figure("bridged"),
    "scales-still-refused": lambda: _scales_figure("still-refused"),
    "extremum-declared-count": lambda: _extremum_figure("declared"),
    "extremum-answered": lambda: _extremum_figure("answered"),
    "extremum-refused": lambda: _extremum_figure("refused"),
    "extremum-as-declared": lambda: _extremum_figure("as-declared"),
    "extremum-reasons": lambda: _extremum_figure("reasons"),
    "extremum-reasons-declared": lambda: _extremum_figure(
        "reasons-declared"),
    "extremum-ties": lambda: _extremum_figure("ties"),
    "binding-declared-count": lambda: _binding_figure("declared"),
    "binding-roles": lambda: _binding_figure("roles"),
    "binding-recovered": lambda: _binding_figure("recovered"),
    "binding-refused": lambda: _binding_figure("refused"),
    "binding-as-declared": lambda: _binding_figure("as-declared"),
    "binding-reasons": lambda: _binding_figure("reasons"),
    "binding-carriers": lambda: _binding_figure("carriers"),
    "binding-nameable": lambda: _binding_figure("recoverable"),
    "binding-ambiguous": lambda: _binding_figure("ambiguous"),
    "binding-readings": lambda: _binding_figure("readings"),
    "binding-largest-fibre": lambda: _binding_figure("largest-fibre"),
    "binding-control-wrong": lambda: _binding_figure("control-wrong"),
    "binding-product-recoverable":
        lambda: _binding_figure("product-recoverable"),
    "binding-product-zero": lambda: _binding_figure("product-zero"),
    "planstore-declared-count": lambda: _planstore_figure("declared"),
    "planstore-replayed": lambda: _planstore_figure("replayed"),
    "planstore-refusals": lambda: _planstore_figure("refusals"),
    "planstore-refusals-replayed":
        lambda: _planstore_figure("refusals-replayed"),
    "planstore-trials-first": lambda: _planstore_figure("trials-first"),
    "planstore-trials-replayed":
        lambda: _planstore_figure("trials-replayed"),
    "planstore-worst-case": lambda: _planstore_figure("worst-case-trials"),
    "planstore-coarse-wrong": lambda: _planstore_figure("coarse-wrong"),
    "conversation-declared-count": lambda: _conversation_figure("declared"),
    "conversation-answered": lambda: _conversation_figure("answered"),
    "conversation-refused": lambda: _conversation_figure("refused"),
    "conversation-as-declared": lambda: _conversation_figure("as-declared"),
    "conversation-reasons": lambda: _conversation_figure("reasons"),
    "conversation-alone": lambda: _conversation_figure("alone-answered"),
    "conversation-control-rows": lambda: _conversation_figure(
        "control-rows"),
    "conversation-control-wrong": lambda: _conversation_figure(
        "control-wrong"),
    #  The sentences the figures module already generates, now writable into
    #  a paragraph instead of quoted from a table by hand.
    "suite": lambda: _sentence("suite"),
    "test-files": lambda: _sentence("test_files"),
    "lean-files": lambda: _sentence("lean_files"),
    "directives": lambda: _sentence("directives"),
    "evaluation-cases": lambda: _sentence("evaluation_cases"),
    "registers": lambda: _sentence("registers"),
    "query-kinds": lambda: _sentence("query_kinds"),
    "report-subjects": lambda: _sentence("report_subjects"),
    #  The bare module counts, so a README that names a sub-package's size
    #  cannot age: the figure is read off the tree, like every other.
    "reasoning-modules": lambda: _thousands(
        _package_figures()["modules_by_subpackage"]["reasoning"]),
    #  The bare counts, for the sentences that put the unit in their own
    #  words ("a 147-case evaluation"): the same figure, without the noun.
    "test-file-count": lambda: _sentence("test_files").split()[0],
    "lean-file-count": lambda: _sentence("lean_files").split()[0],
    "directive-count": lambda: _sentence("directives").split()[0],
    "evaluation-case-count": lambda: _sentence("evaluation_cases").split()[0],
    #  The cost figures, so the sentences of the iteration-cost study are
    #  emitted by the same mechanism they describe.
    "rebuild-decodes-from-nothing":
        lambda: f"{_cost()['addresses']['decodes_from_nothing']:,}",
    "rebuild-decodes-now":
        lambda: f"{_cost()['addresses']['decodes_now']:,}",
    "planner-reports-per-check":
        lambda: str(_cost()["planner"]["reports_per_check_before"]),
    #  The storage side of the generate-rather-than-store ledger: what the
    #  overlay keeps on disk, and how much of it is a cache of something it
    #  can recompute.
    "repo-stored-bytes":
        lambda: f"{int(_repo_storage()['total_bytes']):,}",
    "repo-cache-bytes":
        lambda: f"{int(_repo_storage()['generated_bytes']):,}",
    "repo-primary-bytes":
        lambda: f"{int(_repo_storage()['primary_bytes']):,}",
    "repo-cache-share":
        lambda: per_cent(Fraction(_repo_storage()['generated_fraction'])),
    #  And the corpus's own sizes, which no sentence pattern can cover
    #  because the documentation quotes subsets of them too.
    "lean-declarations": _lean_declaration_count,
    "lean-declaration-files": _lean_declaration_files,
    #  Counted over the *written* corpus, which is what ``inventory_report``
    #  counts and what the inventory table of CORPUS_ADDRESS_STUDY.md shows:
    #  a generated document is an output of the corpus rather than part of
    #  it, so counting it here would put two registered measurements of "how
    #  many documents" three apart.
    "corpus-documents": lambda: f"{len(inv.source_documents()):,}",
    "corpus-state-documents":
        lambda: f"{len([d for d in inv.source_documents() if d.state]):,}",
    "corpus-archive-documents":
        lambda: f"{len([d for d in inv.source_documents() if d.archive]):,}",
    "corpus-sections": _corpus_sections,
}



# ===========================================================================
#  NORM_FAMILY_STUDY.md -- the ladder as a power-of-two family
# ===========================================================================

def _norm_stale() -> str:
    from ..reasoning import norm_escalation as ne
    return ("The stored measurements of the norm family do not describe the "
            f"modules as they now stand (`{ne.state()['verdict']}`), so "
            "nothing is reported here rather than a figure taken from code "
            "that has moved.  Run `python3 -m glm_universal.tools normladder "
            "--write`.")


def _norm() -> Optional[Mapping[str, object]]:
    from ..reasoning import norm_escalation as ne
    return ne.current()


def block_normfamily_rungs() -> str:
    """Every rung of the family, indexed by minimum squared norm."""
    data = _norm()
    if data is None:
        return _norm_stale()
    family = data["family"]
    rows = []
    for row in family["rows"]:
        entries = row["rungs"]
        rows.append((
            _thousands(row["norm"]),
            ", ".join(f"`{entry['rung']}`" for entry in entries),
            f"`{row['densest']}`",
            _thousands(entries[0]["kissing"]),
            f"2^{entries[0]['covolume_log2']}",
            f"`{row['chain']}`",
        ))
    lines = _table(("min. norm", "rungs generated at it", "densest",
                    "its kissing number", "its covolume", "chain rung"), rows)
    completeness = family["completeness"]
    lines.extend([
        "",
        f"{_thousands(family['rung_count'])} rungs are generated in all, and "
        f"every one of the {len(completeness['norms'])} powers of two from "
        f"{_thousands(completeness['norms'][0])} to "
        f"{_thousands(completeness['norms'][-1])} carries at least one: "
        f"gaps = `{list(completeness['gaps'])}`, complete = "
        f"`{completeness['complete']}`.  Each rung's declared minimum norm "
        f"and kissing number is checked against its own generated theta "
        f"series rather than printed beside it — all agree = "
        f"`{family['series_all_agree']}`.",
    ])
    return "\n".join(lines)


def block_normfamily_scaling() -> str:
    """Why the family needs two constructions interleaved."""
    data = _norm()
    if data is None:
        return _norm_stale()
    rule = data["family"]["scaling_rule"]
    rows = [(f"`{row['base']}` → `{row['doubled']}`",
             f"{_thousands(row['norm'][0])} → {_thousands(row['norm'][1])}",
             f"2^{row['covolume_log2'][0]} → 2^{row['covolume_log2'][1]}",
             f"{_thousands(row['kissing'][0])} → {_thousands(row['kissing'][1])}")
            for row in rule["rows"]]
    lines = _table(("doubling", "minimum norm", "covolume", "kissing number"),
                   rows)
    lines.extend([
        "",
        f"Norm × 4 in every case = `{rule['norm_times_four']}`; covolume × "
        f"2^24 = `{rule['covolume_plus_24']}`; kissing number unchanged = "
        f"`{rule['kissing_unchanged']}`.  "
        f"{str(rule['consequence'])[0].upper()}{str(rule['consequence'])[1:]}.  "
        f"The same "
        f"arithmetic is proved in Lean as `{rule['lean']}`.",
    ])
    return "\n".join(lines)


def block_normfamily_chain() -> str:
    """The tower: one rung per power of two, each inside the one below."""
    data = _norm()
    if data is None:
        return _norm_stale()
    chain = data["family"]["chain"]
    rows = [(f"`{step['coarser']}` ⊆ `{step['finer']}`",
             f"{_thousands(step['norms'][0])} ⊂ {_thousands(step['norms'][1])}",
             f"`{step['derived']}`",
             f"{step['points_checked']} / {step['misses']}",
             f"`{step['holds']}`")
            for step in chain["steps"]]
    lines = _table(("step", "norms", "derived", "points tried / missed",
                    "holds"), rows)
    lines.extend([
        "",
        f"The chain is {len(chain['chain'])} rungs — "
        + " ⊂ ".join(f"`{key}`" for key in reversed(chain["chain"]))
        + f" — and every step holds = `{chain['holds']}`.  The Lean proofs "
        f"are `{chain['lean']}`.",
    ])
    return "\n".join(lines)


def block_normesc_measurement() -> str:
    """The re-taken escalation measurement over the norm-indexed rungs."""
    data = _norm()
    if data is None:
        return _norm_stale()
    rows = []
    for key, title in (("declared", "the full power-of-two family"),
                       ("repaired", "the family after the declared "
                                    "retirement rule"),
                       ("chain", "the same family through `B` (a chain)"),
                       ("named_rungs", "the eleven named construction "
                                       "rungs (the recorded before)")):
        report = data[key]
        totals = report["orders"]["totals"]["middle_out"]
        safety = report.get("safety")
        rows.append((
            title,
            len(report["ladder"]),
            _thousands(totals["correct"]),
            _thousands(totals["wrong"]),
            _thousands(totals["refused"]),
            f"`{'yes' if (safety or {}).get('safe', totals['wrong'] == 0) else 'NO'}`",
            _thousands(report["oracle"]),
            f"`{report['orders']['totals']['middle_out']['correct'] == report['oracle']}`",
        ))
    lines = _table(("reading", "rungs", "correct", "wrong", "refused",
                    "refuses rather than answers wrongly", "oracle",
                    "matches oracle"), rows)
    declared = data["declared"]
    repaired = data["repaired"]
    lines.extend([
        "",
        f"All three visiting orders return the same answers in every row — "
        f"the rungs never name different carriers "
        f"(`rungs_disagree = {repaired['agreement']['rungs_disagree']}`) — so "
        f"the order is a cost decision, which is "
        f"`GLM.ConstructionLadder.firstNamed_order_independent`.  The best "
        f"single rung of the repaired ladder is "
        f"`{repaired['best_fixed_rung']['rung']}` at "
        f"{_thousands(repaired['best_fixed_rung']['correct'])} correct, so "
        f"escalation is worth "
        f"+{_thousands(repaired['orders']['totals']['middle_out']['correct'] - repaired['best_fixed_rung']['correct'])} "
        f"queries over it.  The full family answers "
        f"{_thousands(declared['orders']['totals']['middle_out']['correct'])} "
        f"— more than the repaired ladder — and is reported as a **failure** "
        f"anyway, because "
        f"{_thousands(declared['orders']['totals']['middle_out']['wrong'])} "
        f"of those queries is answered wrongly.",
    ])
    return "\n".join(lines)


def block_normesc_audit() -> str:
    """What each rung contributes, and which the rule retires."""
    data = _norm()
    if data is None:
        return _norm_stale()
    declared = data["declared"]
    rows = [(f"`{row['rung']}`", _thousands(row["minimum_norm"]),
             _thousands(row["correct"]), _thousands(row["wrong"]),
             _thousands(row["refused"]), _thousands(row["unique_correct"]),
             _thousands(row["disagrees"]))
            for row in declared["rung_audit"]]
    lines = _table(("rung", "min. norm", "correct", "wrong", "refused",
                    "only rung to answer it", "disagreements"), rows)
    repair = data["repair"]
    lines.extend(["", f"**The retirement rule, declared before it was run:** "
                      f"{declared['retirement']['rule']}.", ""])
    for index, round_ in enumerate(repair["history"], start=1):
        for move in round_["moves"]:
            replacement = (f"replaced by `{move['replaced_by']}`, the next "
                           f"rung the family generates at norm "
                           f"{_thousands(move['norm'])}"
                           if move["replaced_by"] else
                           f"dropped: the family has no other untried rung at "
                           f"norm {_thousands(move['norm'])}")
            lines.append(f"* round {index}: `{move['retired']}` retired — "
                         f"{move['why']}; {replacement}.")
    lines.extend([
        "",
        f"After {repair['rounds']} round(s) the ladder is "
        + " ".join(f"`{key}`" for key in repair["ladder"])
        + f", safe = `{repair['safe']}`, with the norms "
        f"`{list(repair['gaps'])}` left empty — the price of the rule, "
        f"stated rather than hidden.",
    ])
    return "\n".join(lines)


def block_normesc_sweep() -> str:
    """The length sweep: where the family stops being safe."""
    data = _norm()
    if data is None:
        return _norm_stale()
    sweep = data["sweep"]
    rows = [(_thousands(row["length"]), _thousands(row["highest_norm"]),
             _thousands(row["correct"]["middle_out"]),
             _thousands(max(row["wrong"].values())),
             _thousands(row["refused"]["middle_out"]),
             _thousands(row["rungs_disagree"]),
             "yes" if row["order_independent"] else "NO",
             "yes" if row["safe"] else "**NO**")
            for row in sweep["rows"]]
    lines = _table(("rungs", "highest norm", "correct", "wrong", "refused",
                    "rungs disagree", "order-independent",
                    "refuses rather than answers wrongly"), rows)
    lines.extend([
        "",
        f"The longest safe family on this sample is "
        f"**{sweep['longest_safe']} rungs** at "
        f"{_thousands(sweep['best_correct'])} correct; the first unsafe one "
        f"is **{sweep['first_broken']} rungs**.  The break is not the "
        f"order-independence theorem failing — the rungs still agree — it is "
        f"a rung whose cell holds exactly one carrier and the wrong one, so "
        f"the ladder answers where it should have refused.",
    ])
    return "\n".join(lines)


# ===========================================================================
#  OPERATION_ESCALATION_STUDY.md -- faculties other than retrieval
# ===========================================================================

def _opesc_stale() -> str:
    from ..reasoning import operation_escalation as oe
    return ("The stored measurements of the escalated operations do not "
            f"describe the modules as they now stand (`{oe.state()['verdict']}`), "
            "so nothing is reported here.  Run `python3 -m "
            "glm_universal.tools operations --write`.")


def _opesc() -> Optional[Mapping[str, object]]:
    from ..reasoning import operation_escalation as oe
    return oe.current()


def block_opesc_operations() -> str:
    """Every operation, escalated, against its controls."""
    data = _opesc()
    if data is None:
        return _opesc_stale()
    rows = []
    for row in list(data["operations"]) + [data["equation"]]:
        score = row["escalation"]
        rows.append((
            f"`{row['operation']}`",
            _thousands(row["queries"]),
            _thousands(score["correct"]),
            _thousands(score["wrong"]),
            _thousands(score["refused"]),
            f"`{row['best_rung']}` at {_thousands(row['best_rung_score']['correct'])}",
            _thousands(row["control_label_prior"]["correct"]),
            _thousands(row["control_substrate_removed"]["correct"]),
            f"+{_thousands(row['gain_over_best_rung'])}",
        ))
    lines = _table(("operation", "queries", "correct", "wrong", "refused",
                    "best single rung", "label-prior control",
                    "substrate-removed control", "gain over the best rung"),
                   rows)
    lines.extend([
        "",
        f"The refusal contract is the same for all of them: "
        f"{data['contract']}",
        "",
        f"Operations helped by escalation: "
        + ", ".join(f"`{key}`" for key in data["helped"])
        + (f".  Operations that gain nothing: "
           + ", ".join(f"`{key}`" for key in data["no_gain"]) + "."
           if data["no_gain"] else ".  No operation gained nothing.")
        + (f"  Operations that lose the refusal property: "
           + ", ".join(f"`{key}`" for key in data["unsafe"])
           + " — reported as a failure, not a footnote."
           if data["unsafe"] else "  Every operation refuses rather than "
                                  "answering wrongly."),
    ])
    return "\n".join(lines)


def block_opesc_equation() -> str:
    """Equation checking: the one operation that derives rather than reads."""
    data = _opesc()
    if data is None:
        return _opesc_stale()
    row = data["equation"]
    score = row["escalation"]
    lines = [
        f"**{row['title']}**  {row['question']}.",
        "",
        f"The case set is {_thousands(row['cases'])} declared triples — "
        f"{_thousands(row['true_cases'])} that hold and "
        f"{_thousands(row['false_cases'])} that do not — each asked at the "
        f"four declared perturbations, so {_thousands(row['queries'])} "
        f"queries.  {row['contract']}",
        "",
    ]
    lines.extend(_table(
        ("reading", "correct", "wrong", "refused"),
        [("escalation over the ladder", _thousands(score["correct"]),
          _thousands(score["wrong"]), _thousands(score["refused"])),
         (f"best single rung (`{row['best_rung']}`)",
          _thousands(row["best_rung_score"]["correct"]),
          _thousands(row["best_rung_score"]["wrong"]),
          _thousands(row["best_rung_score"]["refused"])),
         ("answer the majority class, never refuse",
          _thousands(row["control_label_prior"]["correct"]),
          _thousands(row["control_label_prior"]["wrong"]),
          _thousands(row["control_label_prior"]["refused"])),
         ("substrate removed (digest cells)",
          _thousands(row["control_substrate_removed"]["correct"]),
          _thousands(row["control_substrate_removed"]["wrong"]),
          _thousands(row["control_substrate_removed"]["refused"]))]))
    lines.extend([
        "",
        f"{row['derivation'].capitalize()}.  The prior control is the sharp "
        f"one here: the classes are balanced, so guessing scores "
        f"{_thousands(row['control_label_prior']['correct'])} of "
        f"{_thousands(row['queries'])} and the escalation's "
        f"{_thousands(score['correct'])} is "
        f"+{_thousands(row['gain_over_prior'])} on it.",
    ])
    return "\n".join(lines)


# ===========================================================================
#  SECOND_READING_STUDY.md -- a second reading before answering
# ===========================================================================

def _secondread_stale() -> str:
    from ..reasoning import second_reading as sr
    return ("The stored measurements of the second-reading study do not "
            f"describe the modules as they now stand (`{sr.state()['verdict']}`), "
            "so nothing is reported here.  Run `python3 -m "
            "glm_universal.tools second-reading --write`.")


def _secondread() -> Optional[Mapping[str, object]]:
    from ..reasoning import second_reading as sr
    return sr.current()


def block_secondread_operations() -> str:
    """Each reading on its own, before any guard is applied."""
    data = _secondread()
    if data is None:
        return _secondread_stale()
    rows = []
    for row in data["operations"]:
        readings = row["readings"]
        for key, title in (("primary", "the escalated ladder"),
                           ("code", "the code layer"),
                           ("margin", "the metric layer")):
            score = readings[key]
            rows.append((
                f"`{row['operation']}`" if key == "primary" else "",
                title,
                _thousands(score["queries"]),
                _thousands(score["correct"]),
                _thousands(score["wrong"]),
                _thousands(score["refused"]),
            ))
    lines = _table(("operation", "reading", "queries", "correct", "wrong",
                    "refused"), rows)
    unsafe = [row["operation"] for row in data["operations"]
              if row["readings"]["primary"]["wrong"] > 0]
    unsafe_second = [f"`{row['operation']}`/{key}"
                     for row in data["operations"]
                     for key in ("code", "margin")
                     if row["readings"][key]["wrong"] > 0]
    lines.extend([
        "",
        "Read alone, before any guard: the primary reading is the one the "
        "previous round shipped, and the two second readings are declared in "
        "§2.",
        "",
        ("Operations the primary answers wrongly: "
         + ", ".join(f"`{key}`" for key in unsafe) + "."
         if unsafe else "The primary reading answers nothing wrongly here.")
        + ("  Second readings that answer wrongly: "
           + ", ".join(unsafe_second) + "."
           if unsafe_second else "  Neither second reading answers anything "
                                 "wrongly on any operation."),
    ])
    return "\n".join(lines)


def block_secondread_marks() -> str:
    """The six guarded configurations against the four declared marks."""
    data = _secondread()
    if data is None:
        return _secondread_stale()
    marks = data["marks_report"]
    rows = []
    for key in sorted(marks["verdicts"]):
        row = marks["verdicts"][key]
        score = row["program"]
        rows.append((
            f"`{key}`",
            _thousands(score["correct"]),
            _thousands(score["wrong"]),
            _thousands(score["refused"]),
            "yes" if row["M1"] else "no",
            "yes" if row["M2"] else "no",
            "yes" if row["M3"] else "no",
            "yes" if row["M4"] else "no",
            "**adopted**" if row["adopted"] else "not adopted",
        ))
    lines = _table(("configuration", "program correct", "program wrong",
                    "program refused", "M1", "M2", "M3", "M4", "verdict"),
                   rows)
    lines.extend([
        "",
        "The marks are those of §4, fixed before the measurement: "
        + "; ".join(f"**{key}** {text}"
                    for key, text in sorted(marks["marks"].items()))
        + ".",
        "",
        f"{marks['verdict'].capitalize()}.",
    ])
    damaged = [(key, marks["verdicts"][key]["damage"])
               for key in sorted(marks["verdicts"])
               if marks["verdicts"][key]["damage"]]
    if damaged:
        lines.extend([
            "",
            "What the configurations that fail M4 cost elsewhere: "
            + "; ".join(f"`{key}` — " + ", ".join(items)
                        for key, items in damaged) + ".",
        ])
    return "\n".join(lines)


def block_secondread_controls() -> str:
    """The two controls, on the operation the round is about."""
    data = _secondread()
    if data is None:
        return _secondread_stale()
    program = [row for row in data["operations"]
               if row["operation"] == "program"][0]
    rows = []
    for key in sorted(program["configurations"]):
        configuration = program["configurations"][key]
        matched = configuration["control_matched_refusal"]
        reshuffled = configuration["control_reshuffled"]
        rows.append((
            f"`{key}`",
            _thousands(configuration["answers_given_up"]),
            _thousands(configuration["wrongs_removed"]),
            _thousands(configuration["control_matched_wrongs_removed"]),
            f"{_thousands(matched['correct'])} / "
            f"{_thousands(matched['wrong'])}",
            f"{_thousands(reshuffled['correct'])} / "
            f"{_thousands(reshuffled['wrong'])}",
        ))
    lines = _table(("configuration", "answers given up", "wrong answers "
                    "removed", "matched refusal removes",
                    "matched refusal correct / wrong",
                    "reshuffled-label guard correct / wrong"), rows)
    readings = program["readings"]
    lines.extend([
        "",
        f"Control B read alone on the same operation: the code layer with its "
        f"labels reshuffled answers {_thousands(readings['code_reshuffled']['correct'])} "
        f"correctly and {_thousands(readings['code_reshuffled']['wrong'])} "
        f"wrongly, and the metric layer reshuffled "
        f"{_thousands(readings['margin_reshuffled']['correct'])} correctly "
        f"and {_thousands(readings['margin_reshuffled']['wrong'])} wrongly — "
        f"which is what a second opinion looks like when the relation between "
        f"the geometry and the label has been destroyed.",
    ])
    return "\n".join(lines)


# ===========================================================================
#  BLOCKERS_STUDY.md -- what is between this and fuller reasoning
# ===========================================================================

def _blockers_stale() -> str:
    from ..reasoning import blockers as bl
    return ("The stored measurements of the blockers study do not describe "
            f"the modules as they now stand (`{bl.state()['verdict']}`), so "
            "nothing is reported here.  Run `python3 -m glm_universal.tools "
            "blockers --write`.")


def _blockers() -> Optional[Mapping[str, object]]:
    from ..reasoning import blockers as bl
    return bl.current()


def block_blockers_probe() -> str:
    """The pre-registered probe, question by question."""
    data = _blockers()
    if data is None:
        return _blockers_stale()
    probe = data["probe"]
    rows = [(row["domain"], f"*{row['question']}*", f"`{row['expect']}`",
             f"`{row['canonical']['verdict']}`",
             f"`{row['paraphrased']['verdict']}`",
             f"`{row['canonical']['kind']}`")
            for row in probe["rows"]]
    lines = _table(("domain", "question", "a right answer contains",
                    "canonical", "paraphrased", "query kind"), rows)
    mark = probe["pass_mark"]
    lines.extend([
        "",
        f"**Declared before the run:** the probe passes if at least "
        f"{mark['correct_at_least']} of {mark['of']} canonical askings are "
        f"correct with at most {mark['wrong_at_most']} wrong.",
        "",
        f"**What happened:** {probe['canonical']['correct']} correct, "
        f"{probe['canonical']['wrong']} wrong, "
        f"{probe['canonical']['refused']} refused — "
        f"**passed = `{probe['passed']}`**.  In paraphrase: "
        f"{probe['paraphrased']['correct']} correct, "
        f"{probe['paraphrased']['wrong']} wrong, "
        f"{probe['paraphrased']['refused']} refused, with "
        f"{probe['stable']} of {probe['questions']} questions scoring the "
        f"same both ways.  {data['unrecognised']} of the canonical askings "
        f"were not recognised as any query kind at all.",
        "",
        probe["reading"],
    ])
    return "\n".join(lines)


def block_blockers_table() -> str:
    """Each blocker, its measurement, and the smallest experiment."""
    data = _blockers()
    if data is None:
        return _blockers_stale()
    figures = data["figures"]
    rows = []
    for blocker in data["blockers"]:
        measured = " and ".join(
            f"`{name.strip()}` = {figures.get(name.strip())}"
            for name in str(blocker["measurement"]).split(" and "))
        rows.append((f"**{blocker['title']}**", blocker["statement"],
                     measured, blocker["experiment"]))
    return "\n".join(_table(
        ("blocker", "what it means", "the measurement that demonstrates it",
         "the smallest experiment that would remove it"), rows))


def block_blockers_ledger() -> str:
    """Table lookup, geometric addressing and derivation, kept apart."""
    data = _blockers()
    if data is None:
        return _blockers_stale()
    rows = [(row["result"], f"`{row['class']}`", row["why"],
             f"`{row['measured_in']}`")
            for row in data["ledger"]]
    lines = _table(("measured result", "what it is", "why it is that",
                    "measured in"), rows)
    counts = {}
    for row in data["ledger"]:
        counts[row["class"]] = counts.get(row["class"], 0) + 1
    lines.extend([
        "",
        "Of the measured results of this round, "
        + ", ".join(f"{count} are `{name}`"
                    for name, count in sorted(counts.items()))
        + ".  " + str(data["claim"]),
    ])
    return "\n".join(lines)


def block_blockers_python() -> str:
    """The smallest experiment for the program-text blocker, run."""
    data = _blockers()
    if data is None:
        return _blockers_stale()
    python = data["python"]
    lexicon = data["lexicon"]
    chance = Fraction(str(python["chance"]["__fraction__"])
                      if isinstance(python["chance"], dict)
                      else str(python["chance"]))
    rate = Fraction(str(python["rate"]["__fraction__"])
                    if isinstance(python["rate"], dict)
                    else str(python["rate"]))
    lines = _table(
        ("reading", "nearest neighbour shares a module", "of", "rate"),
        [("24 syntax counts, quantised to the nearest point of rung `A`",
          _thousands(python["nearest_shares_module"]),
          _thousands(python["functions"]), per_cent(rate)),
         ("a digest of the function's own name, quantised the same way",
          _thousands(python["digest_control"]),
          _thousands(python["functions"]),
          per_cent(Fraction(python["digest_control"], python["functions"]))),
         ("chance — two functions drawn at random",
          "—", _thousands(python["functions"]), per_cent(chance))])
    lines.extend([
        "",
        f"{_thousands(python['functions'])} functions over "
        f"{_thousands(python['modules'])} modules, addressed by "
        f"{len(python['features'])} counts of syntax and nothing else — no "
        f"name, no module, no path.  {python['reading']}.",
        "",
        f"Beside it, the vocabulary measurement: of the "
        f"{_thousands(lexicon['content_words'])} content words the probe "
        f"uses, the lexicon holds {_thousands(lexicon['in_lexicon'])} and "
        f"does not hold {_thousands(lexicon['out_of_lexicon'])} — a coverage "
        f"of {per_cent(Fraction(lexicon['in_lexicon'], lexicon['content_words']))} "
        f"against a lexicon of {_thousands(lexicon['lexicon_size'])} words.",
    ])
    return "\n".join(lines)


def block_blockers_vocabulary() -> str:
    """The vocabulary blocker's own experiment, run and read by its rule."""
    data = _blockers()
    if data is None:
        return _blockers_stale()
    experiment = data["vocabulary"]
    lexicon = data["lexicon"]
    before = experiment["score_before"]
    after = experiment["score_after"]
    baseline = experiment["baseline"]

    def _fraction(value) -> Fraction:
        if isinstance(value, dict):
            return Fraction(str(value["__fraction__"]))
        return Fraction(str(value))

    rows = [
        ("content words of the probe the register holds",
         f"{baseline['in_lexicon']} of {baseline['content_words']}",
         f"{lexicon['in_lexicon']} of {lexicon['content_words']}",
         per_cent(_fraction(experiment["coverage_after"]))),
        ("the same, after the declared surface forms",
         f"{baseline['in_lexicon']} of {baseline['content_words']}",
         f"{lexicon['in_lexicon_with_forms']} of "
         f"{lexicon['content_words']}",
         per_cent(_fraction(experiment["coverage_after_with_forms"]))),
        ("concepts in the register",
         _thousands(baseline["lexicon_size"]),
         _thousands(lexicon["lexicon_size"]),
         f"+{_thousands(experiment['words_added'])}"),
        ("the probe, canonical askings: correct",
         _thousands(before["correct"]), _thousands(after["correct"]), "—"),
        ("the probe, canonical askings: wrong",
         _thousands(before["wrong"]), _thousands(after["wrong"]), "—"),
        ("the probe, canonical askings: refused",
         _thousands(before["refused"]), _thousands(after["refused"]), "—"),
    ]
    lines = _table(("measurement", "before the words were added", "after",
                    "change"), rows)
    lines.extend([
        "",
        f"**Declared before the words were written:** "
        f"{experiment['prediction']}.",
        "",
        f"**How the outcome is read, also declared first:** "
        f"{experiment['reading']}.",
        "",
        f"**What happened:** {_thousands(experiment['words_added'])} concepts "
        f"and {_thousands(lexicon['declared_forms'])} declared surface forms "
        f"were added; the strict coverage of the probe's content words rose "
        f"from {baseline['in_lexicon']} of {baseline['content_words']} to "
        f"{lexicon['in_lexicon']} of {lexicon['content_words']}, and every "
        f"remaining word is an inflection the declared forms resolve. The "
        f"probe's canonical score moved by "
        f"{_thousands(experiment['score_moved_by'])} askings — "
        f"**prediction held = `{experiment['prediction_held']}`**.",
        "",
        str(experiment["verdict"]) + ".",
    ])
    return "\n".join(lines)


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
    "stack-sets": block_stack_sets,
    "stack-carried": block_stack_carried,
    "stack-controls": block_stack_controls,
    "stack-sweep": block_stack_sweep,
    "stack-tiebreak": block_stack_tiebreak,
    "stack-vision": block_stack_vision,
    "anonymous-faculties": block_anonymous_faculties,
    "anonymous-invariance": block_anonymous_invariance,
    "anonymous-relay": block_anonymous_relay,
    "anonymous-verdict": block_anonymous_verdict,
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
    "now-tier": block_now_tier,
    "now-levels": block_now_levels,
    "now-capacity": block_now_capacity,
    "now-collisions": block_now_collisions,
    "now-dimensions": block_now_dimensions,
    "now-float": block_now_float,
    "now-shortcut": block_now_shortcut,
    "now-tasks": block_now_tasks,
    "now-claims": block_now_claims,
    "cost-tier": block_cost_tier,
    "cost-addresses": block_cost_addresses,
    "cost-planner": block_cost_planner,
    "normfamily-rungs": block_normfamily_rungs,
    "normfamily-scaling": block_normfamily_scaling,
    "normfamily-chain": block_normfamily_chain,
    "normesc-measurement": block_normesc_measurement,
    "normesc-audit": block_normesc_audit,
    "normesc-sweep": block_normesc_sweep,
    "opesc-operations": block_opesc_operations,
    "opesc-equation": block_opesc_equation,
    "secondread-operations": block_secondread_operations,
    "secondread-marks": block_secondread_marks,
    "secondread-controls": block_secondread_controls,
    "blockers-probe": block_blockers_probe,
    "blockers-table": block_blockers_table,
    "blockers-ledger": block_blockers_ledger,
    "blockers-python": block_blockers_python,
    "blockers-vocabulary": block_blockers_vocabulary,
    "oracle-split": block_oracle_split,
    "oracle-table": block_oracle_table,
    "fieldsurface-split": block_fieldsurface_split,
    "fieldsurface-questions": block_fieldsurface_questions,
    "fieldsurface-tables": block_fieldsurface_tables,
    "ordering-declared": block_ordering_declared,
    "ordering-split": block_ordering_split,
    "extremum-declared": block_extremum_declared,
    "scales-table": block_scales_table,
    "scales-declared": block_scales_declared,
    "conversation-declared": block_conversation_declared,
    "binding-declared": block_binding_declared,
    "binding-fibres": block_binding_fibres,
    "planstore-declared": block_planstore_declared,
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

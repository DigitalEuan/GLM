"""``glm_universal.corpus.cost`` -- what one iteration of this repository costs.

Why this module exists
----------------------
Everything this project claims is recomputed from the tree, which is the
property that keeps it honest and the property that makes it expensive.  Adding
one Lean file invalidates the address book; the address book invalidates the
measurement cache; the measurements move the study blocks; the study blocks
move figures quoted in prose; the prose quotes the suite counts.  Each link is
individually sensible, and the chain is where the wall clock goes.

The answer this module takes is the one the rest of the package takes to any
other cost: **measure it, in exact integers, and let a document quote the
measurement rather than an impression.**  What is counted here is *work
avoided*, not seconds -- a timing is a fact about a machine, and the same round
on another machine would make the document wrong.  A decode either happens or
it does not.

What is counted
---------------
``address_book_cost``
    The two address books.  Rebuilding one decodes once per distinct vector;
    rebuilding it against the stored book decodes only the vectors that are
    new.  Both numbers are reported, so the saving is a ratio of counts.

``planner_cost``
    The reverse-call planner's report is quoted by five generated blocks and
    costs one pass over the whole evaluation set to take.  It is now taken once
    per change to the code that produces it, rather than once per block per
    check.

``figure_cost``
    How many figures inside sentences are emitted rather than typed, and in how
    many documents -- the hand-reconciliation this round retired.

Nothing here is a float, nothing here writes, and nothing here decodes: the
"from nothing" figure is the number of *distinct* vectors, which is counted
rather than paid for.
"""

from __future__ import annotations

from typing import Dict, Tuple

from ..derived import memo
from ..reasoning import lean_address as la
from . import address as ad

__all__ = [
    "PLANNER_BLOCKS",
    "address_book_cost",
    "planner_cost",
    "figure_cost",
    "cost_report",
]

#: The generated blocks that quote the planner's report.  Declared here rather
#: than discovered, because what it measures is a property of the study's
#: layout and a renderer that stopped quoting the report should move this line.
PLANNER_BLOCKS: Tuple[str, ...] = (
    "plannersandbox-tier",
    "plannersandbox-tools",
    "plannersandbox-tasks",
    "plannersandbox-fallback",
    "plannersandbox-promotion",
)


@memo
def address_book_cost() -> Dict[str, object]:
    """Decodes a rebuild of each address book needs now, and from nothing."""
    lean_table = la.feature_table()
    lean_distinct = (len({tuple(v) for v in lean_table.values()})
                     + len({la.name_hash_vector(name) for name in lean_table}))
    _book, lean_report = la.compute_address_book(reuse=True, audit=4)

    document_table = ad.vector_table()
    document_distinct = sum(
        len({tuple(entry[scheme]) for entry in document_table.values()})
        for scheme in ("lexical", "structural"))
    _document_book, document_report = ad.compute_address_book(reuse=True,
                                                              audit=4)
    return {
        "lean": {
            "declarations": lean_report["declarations"],
            "decodes_from_nothing": lean_distinct,
            "decodes_now": lean_report["decoded"],
            "reused": lean_report["reused"],
            "audit": lean_report["audit"],
        },
        "documents": {
            "sections": document_report["units"],
            "decodes_from_nothing": document_distinct,
            "decodes_now": document_report["decoded"],
            "reused": document_report["reused"],
            "audit": document_report["audit"],
        },
        "decodes_from_nothing": lean_distinct + document_distinct,
        "decodes_now": lean_report["decoded"] + document_report["decoded"],
    }


@memo
def planner_cost() -> Dict[str, object]:
    """How many times a document check takes the planner's report."""
    from ..sandbox import planner as pl

    state = pl.report_cache_state()
    return {
        "blocks_quoting_the_report": len(PLANNER_BLOCKS),
        "blocks": PLANNER_BLOCKS,
        "reports_per_check_before": len(PLANNER_BLOCKS),
        "reports_per_check_now": 0 if state["fresh"] else 1,
        "store": state["verdict"],
        "evaluation_cases_per_report": _evaluation_cases(),
    }


def _evaluation_cases() -> int:
    from ..evaluation import cases as ev

    return len(ev.CASES)


@memo
def figure_cost() -> Dict[str, object]:
    """How much of the prose's arithmetic is emitted rather than typed.

    Markers are *counted* here and not *rendered*: three of the figures are
    read out of this module, so rendering one from inside the cost report
    would ask the cost report for itself.  Whether each marker is at the value
    its figure now has is a different question, and
    :func:`glm_universal.corpus.render.figure_report` is where it is asked.
    """
    from . import inventory as inv
    from . import render as rd

    markers = 0
    documents = 0
    for document in inv.source_documents():
        spans = rd.figure_spans(document.text)
        if spans:
            documents += 1
            markers += len(spans)
    return {
        "registered": len(rd.FIGURES),
        "in_the_corpus": markers,
        "documents": documents,
    }


@memo
def cost_report() -> Dict[str, object]:
    """The three costs, and whether both caches are in the reused state."""
    addresses = address_book_cost()
    planner = planner_cost()
    figures = figure_cost()
    return {
        "addresses": addresses,
        "planner": planner,
        "figures": figures,
        "settled": (addresses["decodes_now"] == 0
                    and planner["reports_per_check_now"] == 0),
    }

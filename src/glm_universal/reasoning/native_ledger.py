"""``glm_universal.reasoning.native_ledger`` -- the native/standard ledger.

The declared half of Phase 70's native-parity instrument
(``studies/NATIVE_PARITY_STUDY.md``): the ledger of every native/standard pair
an earlier study measured, the read-back check of the stored structural
addresses, and the toolbox's one-line view of both.  Split out of
:mod:`glm_universal.reasoning.native_parity` in Phase 114 so that the toolbox
does not reach the document corpus: the measurements over the documents, and
the cache that stores them, stay in ``native_parity``, which re-exports every
name here unchanged.

Every figure is an integer or a :class:`~fractions.Fraction` (D7).  The Lean
half is ``RequestProject/GLM/NativeParity.lean``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from ..derived import memo
from . import lean_address as la
from . import retrieval as rt

__all__ = ["LedgerRow", "LEDGER", "CLASSES", "ledger_report",
           "exactness_report", "tool_summary"]

STUDY = "studies/NATIVE_PARITY_STUDY.md"
LEAN_FILE = "RequestProject/GLM/NativeParity.lean"


# ===========================================================================
#  The ledger
# ===========================================================================

#: The four classes a pair can fall in, in the order of the owner's concern.
CLASSES: Tuple[str, ...] = ("native ahead", "parity", "standard narrowly ahead",
                            "standard far ahead")


@dataclass(frozen=True)
class LedgerRow:
    """One measured native/standard pair, as its study recorded it."""

    task: str
    native: str
    standard: str
    figure: str
    klass: str
    target: str          # "T1" / "T2" / "T3" or "recorded"
    study: str
    recomputed_by: str

    def as_json(self) -> Dict[str, str]:
        return {"task": self.task, "native": self.native,
                "standard": self.standard, "figure": self.figure,
                "class": self.klass, "target": self.target,
                "study": self.study, "recomputed_by": self.recomputed_by}


LEDGER: Tuple[LedgerRow, ...] = (
    LedgerRow("Lean-corpus retrieval, declaration queries",
              "Leech address of the structural vector",
              "the raw structural vector",
              "hit@1/3/5/10 38/61/75/93 against 37/61/74/96",
              "parity", "T1", "studies/ADDRESS_RETRIEVAL_STUDY.md",
              "glm_universal.reasoning.retrieval.declaration_query_report"),
    LedgerRow("document-corpus retrieval, section queries",
              "Leech address of the lexical vector",
              "the raw lexical vector",
              "hit@5 14 against 16 of 60",
              "standard narrowly ahead", "T2",
              "studies/CORPUS_ADDRESS_STUDY.md",
              "glm_universal.corpus.address.retrieval_report"),
    LedgerRow("dimensional-derivation controller",
              "Leech-address scorer at scale 9",
              "the exact move count",
              "solved 18 against 24 of 24 (the undecoded carrier: 17)",
              "standard far ahead", "T3", "studies/CONTROLLER_STUDY.md",
              "glm_universal.reasoning.controller.controller_report"),
    LedgerRow("Lean-corpus retrieval, identifiers",
              "Leech address of the identifier-letter vector",
              "Jaccard overlap of identifier tokens",
              "hit@5 134 against 171 of 209",
              "standard far ahead", "recorded",
              "studies/ADDRESS_RETRIEVAL_STUDY.md",
              "glm_universal.reasoning.retrieval.declaration_query_report"),
    LedgerRow("document-corpus retrieval, words",
              "lexical Leech address", "Jaccard overlap of words",
              "hit@5 14 against 42 of 60",
              "standard far ahead", "recorded",
              "studies/CORPUS_ADDRESS_STUDY.md",
              "glm_universal.corpus.address.retrieval_report"),
    LedgerRow("exact ties of the text ranking",
              "break by Leech-address distance", "break by name",
              "hit@5 374 against 367 (holdout), 387 against 379 (tuning)",
              "native ahead", "recorded", "studies/STACK_RELAY_STUDY.md",
              "glm_universal.reasoning.stack.tiebreak_report"),
    LedgerRow("soft read at the Golay deep hole",
              "the carried fork's escalated Leech estimate",
              "unconstrained soft decoding over 4,096 codewords",
              "right on 512 against 480 of 768",
              "native ahead", "recorded", "studies/CARRIED_FORK_STUDY.md",
              "glm_universal.reasoning.carried_fork.carried_fork_report"),
    LedgerRow("sentences for terms", "the prefix-first grammar",
              "the natural infix realiser",
              "0 against 5,684 sentences with two readings",
              "native ahead", "recorded", "studies/REVERSE_TCT_STUDY.md",
              "glm_universal.reasoning.reverse_tct_script.reverse_report"),
)


def ledger_report() -> Dict[str, object]:
    """The ledger, with the count in each class."""
    counts = {klass: sum(1 for row in LEDGER if row.klass == klass)
              for klass in CLASSES}
    return {"rows": tuple(row.as_json() for row in LEDGER),
            "counts": counts,
            "targets": tuple(row.target for row in LEDGER
                             if row.target != "recorded")}


# ===========================================================================
#  The read-back check, and the toolbox's view
# ===========================================================================

@memo
def exactness_report() -> Dict[str, object]:
    """N3: the read-back of every stored structural address is its features."""
    book = la.address_book()
    if book is None:
        return {"checked": 0, "exact": 0, "failures": 0, "met": False}
    table = rt._point_table("address")
    checked = exact = 0
    worst = 0
    for name in book["order"]:
        point = table.get(name)
        if point is None:
            continue
        checked += 1
        if rt.readback(point) == tuple(book["features"][name]):
            exact += 1
        worst = max(worst, la.describe_address(point)["max_residual"])
    return {"checked": checked, "exact": exact, "failures": checked - exact,
            "max_residual": worst, "covering_radius": la.COVERING_RADIUS,
            "met": checked > 0 and exact == checked}


def tool_summary() -> Dict[str, object]:
    """The ledger and the one-line verdict of each target, for the toolbox.

    The census-sized measurements stay in the study; the tool reports the
    ledger and the read-back check, which cost a fraction of a second.
    """
    ledger = ledger_report()
    exact = exactness_report()
    return {"counts": ledger["counts"], "targets": ledger["targets"],
            "readback_checked": exact["checked"],
            "readback_exact": exact["exact"]}

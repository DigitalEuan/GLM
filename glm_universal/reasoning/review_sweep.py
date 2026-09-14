"""``glm_universal.reasoning.review_sweep`` -- which stalled results are worth
re-reading, decided before any of them is re-read.

The rule this module is the instrument for
------------------------------------------
Directive D13 permits an escalated re-reading and then constrains it, and its
second practice clause is the one nothing implemented until now:

    Rank candidates for re-reading by whether there is an **identifiable
    discarded quantity** at the coarse reading, not by how disappointing the
    original result was.  Where nothing was discarded, escalation has nothing
    to recover.

That clause is the whole difference between escalation and shopping.  A stalled
result is disappointing whatever caused it, so ranking by disappointment sorts
the register by nothing at all; ranking by *what the reading threw away* sorts
it by whether a finer reading could possibly help.  The register below applies
the clause to every stalled result the repository currently carries, and it is
written **before** the next re-reading rather than after it.

What is declared, and what is measured
--------------------------------------
Declared: the entries.  Which results are stalled, what each stall is, at which
reading it was taken, and -- the judgement the clause asks for -- whether a
quantity identifiable *at that reading* was discarded, together with what it is
and where it would be recovered.  That association cannot be derived from the
tree, because it is the reading of the round.

Measured, on every call:

* that each entry's **study document exists** and is not a stub, so an entry
  cannot cite a document that was never written;
* that each entry's **module exists and exposes the attribute** it names as the
  place the discarded quantity is, or would be, reported.  An entry claiming a
  discarded quantity it cannot point at is reported as **unsupported**, and the
  register does not rank it above one that names nothing;
* the **ranking** itself, which is a function of those measurements and the
  declared class rather than of a hand-written order.

Four classes, and what each one licenses
----------------------------------------
``recoverable``
    A quantity was discarded at the coarse reading and the register can point
    at where it is.  These rank first: escalation has something to recover, and
    a declared ladder can be climbed for it.

``recovered``
    The same, and the re-reading has already been taken.  Kept in the register
    with the reading that resolved it, because a register that drops its
    successes stops being evidence that the rule works.

``no-discard``
    Nothing was discarded: the stall is in the signal, not in the reading.
    Escalation is *not* licensed, and the entry names what would be needed
    instead -- new data, a new pre-registration, or a proof.

``needs-a-theorem``
    The stall is a statement the measurement cannot settle at any resolution,
    so the work is a proof rather than a reading.

Exactness
---------
Integers and strings only: the register counts entries and reads the tree.  No
float, no random source, no digest.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

__all__ = [
    "Entry", "REGISTER", "CLASSES", "entry_report", "review_sweep_report",
    "ranked", "recoverable", "entry_by_key",
]


# ═════════════════════════════════════════════════════════════════════════
# 1.  WHAT AN ENTRY IS
# ═════════════════════════════════════════════════════════════════════════

#: The four classes, in the order they rank.  The order is the rule: an entry
#: with something to recover is worth re-reading before one without.
CLASSES: Tuple[str, ...] = ("recoverable", "recovered", "needs-a-theorem",
                            "no-discard")


@dataclass(frozen=True)
class Entry:
    """One stalled result, and the D13 judgement about re-reading it."""

    key: str
    #: What stalled, in one sentence.
    stall: str
    #: The study that reports it.
    document: str
    #: The reading the stall was taken at.
    reading: str
    #: ``recoverable`` | ``recovered`` | ``needs-a-theorem`` | ``no-discard``
    verdict: str
    #: The quantity the coarse reading discarded, or why nothing was.
    discarded: str
    #: Where that quantity is, or would be, reported: ``module``/``attribute``.
    module: Optional[str] = None
    attribute: Optional[str] = None
    #: What re-reading it would cost, or what is needed instead.
    next_step: str = ""


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE REGISTER
# ═════════════════════════════════════════════════════════════════════════

REGISTER: Tuple[Entry, ...] = (
    Entry(
        key="deep-hole-separation",
        stall=("the separation criterion rho = 2W/B < 1 is unmet: rho falls "
               "from 3.90 to 2.5943 across the declared ladder and never "
               "crosses 1, so the reading that names 40 of 44 holes still "
               "certifies no absence"),
        document="DEEP_HOLE_FAILURE_STUDY.md",
        reading="the joint rung at 1920 starts -- the top of the declared ladder",
        verdict="no-discard",
        discarded=("nothing identifiable.  The joint rung already carries "
                   "both the stray spectrum and the exact measure, and the "
                   "failure round located the stall in the within-type spread "
                   "of D_6^4 (W = 0.0659 against B = 0.0358), which is a "
                   "property of the ensemble rather than of what the reading "
                   "throws away.  The declared 55-subset deletion sweep gets "
                   "no lower than 1.4784, and a deletion cannot certify the "
                   "types it deleted"),
        module="glm_universal.reasoning.deep_hole_failures",
        attribute="spread",
        next_step=("not a re-reading.  Either a bound proved for every "
                   "reading of this family, or a different ensemble -- which "
                   "is new data and a new pre-registration, not a rung"),
    ),
    Entry(
        key="deep-hole-per-type",
        stall=("the global criterion is a worst case over ten types, so it "
               "says nothing about a type that is well separated from its own "
               "neighbours"),
        document="DEEP_HOLE_FAILURE_STUDY.md",
        reading="the same single cell, read type by type instead of globally",
        verdict="recovered",
        discarded=("the per-type spreads, which the global maximum discards "
                   "by construction.  Recovered by reporting the criterion "
                   "type by type: three of the ten types satisfy it, and "
                   "`GLM.DeepHoleFailure.per_type_correct` makes that a "
                   "certificate for those types"),
        module="glm_universal.reasoning.deep_hole_failures",
        attribute="per_type_criterion",
        next_step=("done, and labelled in the study as added after the "
                   "numbers were seen"),
    ),
    Entry(
        key="rational-conflation",
        stall=("read alone, the exact rational rung conflates A_1^24 with "
               "A_2^12: neither hole emits a stray, so the whole measure is "
               "one atom"),
        document="CUMULATIVITY_STUDY.md",
        reading="L3, the exact measure of distances, read alone",
        verdict="recovered",
        discarded=("the arrival shares -- which vertex each start arrived at. "
                   "Recovered by the join rather than by refining L3, which "
                   "is the declared non-edge of the deep-hole family and, in "
                   "general form, `GLM.Info.Layer.factored_conflates` with "
                   "`join_separates`"),
        module="glm_universal.reasoning.cumulativity",
        attribute="conflations",
        next_step=("the reading is repaired; what is still wanted is the "
                   "characterisation -- which pairs *any* stray-blind reading "
                   "must conflate -- and that is a theorem, not a rung"),
    ),
    Entry(
        key="niemeier-unreached-types",
        stall=("the ensemble reaches 10 of the 23 Niemeier root systems from "
               "the 14 declared centres; 13 are reported as unreached and "
               "nothing is claimed about them"),
        document="DEEP_HOLE_STUDY.md",
        reading="the declared centre set of the first deep-hole round",
        verdict="no-discard",
        discarded=("nothing.  A type no walk arrives at is absent from the "
                   "record at every rung: there is no quantity in the "
                   "measurement for a finer reading to recover"),
        module="glm_universal.reasoning.deep_hole_classifier",
        attribute="transforms",
        next_step=("new centres, and therefore a new pre-registration: the "
                   "centre set is part of what the first study fixed"),
    ),
    Entry(
        key="retrieval-hit-at-5",
        stall=("retrieval by lattice address reaches hit@5 39.1 % against "
               "6.3 % chance, and the plain text control reaches 85.0 % on "
               "the same 207 queries"),
        document="ADDRESS_RETRIEVAL_STUDY.md",
        reading="the 24-count feature map, quantised to a Leech point",
        verdict="recoverable",
        discarded=("the identity of the terms.  The feature map reduces a "
                   "declaration to twenty four structural counts, and two "
                   "declarations with the same counts and disjoint "
                   "vocabularies are one address -- which is exactly what the "
                   "text control keeps and what the lexical address recovers "
                   "part of (66.7 %)"),
        module="glm_universal.reasoning.lean_address",
        attribute="lean_address_report",
        next_step=("a declared joint reading of the lattice address with a "
                   "term reading, priced as a rung and measured on the same "
                   "207 queries against both controls"),
    ),
    Entry(
        key="planner-utility",
        stall=("the reverse-call planner's utility gate is false: of the four "
               "refusals the fallback rule offers it, it correctly refuses "
               "all four, so it would add nothing to the shipped system"),
        document="REVERSE_CALL_PLANNER_STUDY.md",
        reading=("the whole evaluation set under the declared fallback "
                 "rule"),
        verdict="no-discard",
        discarded=("nothing.  Every question in the evaluation set that the "
                   "runtime refuses is a question that ought to be refused, "
                   "so the set contains no headroom for the planner; the five "
                   "gains on the declared task set are all off-set"),
        module="glm_universal.sandbox.planner",
        attribute="fallback_reading",
        next_step=("evaluation cases of the shapes the planner answers and "
                   "the runtime does not -- new cases, declared before they "
                   "are run, not a finer reading of the present ones"),
    ),
    Entry(
        key="describable-coverage",
        stall=("three of the eight registers are described, and seven of the "
               "twenty answerable query kinds"),
        document="LANGUAGE_STUDY.md",
        reading="the three declared shape families",
        verdict="no-discard",
        discarded=("nothing.  The thirteen remaining query kinds are not "
                   "shapes of any family; forcing them would make the "
                   "coverage figure meaningless, which is the language "
                   "layer's own stopping rule"),
        module="glm_universal.language",
        attribute="__name__",
        next_step=("a fourth shape family would be new work with its own "
                   "pre-registration; the measured verdict is that the layer "
                   "has reached where it should stop"),
    ),
    Entry(
        key="faithfulness-radius",
        stall=("faithfulness and the certified radius are incompatible: a "
               "query needs a radius of 0.0659 where separation permits only "
               "0.0179, so `absent_certifies` cannot be instantiated"),
        document="DEEP_HOLE_FAILURE_STUDY.md",
        reading="the joint rung at 1920 starts",
        verdict="needs-a-theorem",
        discarded=("nothing at the reading.  The two radii are measured from "
                   "the same table, and the shortfall is a fact about the "
                   "table rather than about what the reading kept"),
        module="glm_universal.reasoning.deep_hole_failures",
        attribute="faithfulness",
        next_step=("either the per-type certificate extended to more types, "
                   "or a proof that no reading of this family separates the "
                   "table by more than its within-type spread"),
    ),
)


def entry_by_key(key: str) -> Entry:
    """One entry by its key."""
    for entry in REGISTER:
        if entry.key == key:
            return entry
    raise KeyError(f"no review-sweep entry named {key!r}")


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE CHECKS
# ═════════════════════════════════════════════════════════════════════════

_HERE = Path(__file__).resolve()
PACKAGE_ROOT = _HERE.parent.parent
REPO_ROOT = PACKAGE_ROOT.parent.parent

#: A document shorter than this is a stub rather than a study.  The same
#: figure the pipeline board uses, so the two agree about what counts.
STUB_BYTES: int = 2000


def _document_path(name: str) -> Optional[Path]:
    for root in (REPO_ROOT, REPO_ROOT / "studies", PACKAGE_ROOT.parent):
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def _attribute_resolves(entry: Entry) -> bool:
    if not entry.module or not entry.attribute:
        return False
    try:
        module = importlib.import_module(entry.module)
    except ImportError:                         # pragma: no cover - defensive
        return False
    return hasattr(module, entry.attribute)


def entry_report(entry: Entry) -> Dict[str, object]:
    """One entry, with everything about it that can be read off the tree."""
    document = _document_path(entry.document)
    document_bytes = document.stat().st_size if document else 0
    resolves = _attribute_resolves(entry)
    claims_a_discard = entry.verdict in ("recoverable", "recovered")
    return {
        "key": entry.key,
        "stall": entry.stall,
        "document": entry.document,
        "document_found": bool(document),
        "document_bytes": document_bytes,
        "document_is_a_study": bool(document) and document_bytes >= STUB_BYTES,
        "reading": entry.reading,
        "verdict": entry.verdict,
        "discarded": entry.discarded,
        "module": entry.module,
        "attribute": entry.attribute,
        "attribute_resolves": resolves,
        "claims_a_discarded_quantity": claims_a_discard,
        #  An entry may only rank as recoverable if it can point at the
        #  quantity it says was discarded.
        "supported": resolves if claims_a_discard else True,
        "next_step": entry.next_step,
    }


def _rank_key(row: Dict[str, object]) -> Tuple[int, int, str]:
    verdict = str(row["verdict"])
    order = CLASSES.index(verdict) if verdict in CLASSES else len(CLASSES)
    # an unsupported claim does not outrank an honest "nothing was discarded"
    penalty = 0 if row["supported"] else 1
    return (order + penalty * len(CLASSES), 0, str(row["key"]))


def ranked() -> Tuple[Dict[str, object], ...]:
    """Every entry, ordered by the rule rather than by hand."""
    rows = [entry_report(entry) for entry in REGISTER]
    rows.sort(key=_rank_key)
    return tuple(rows)


def recoverable() -> Tuple[str, ...]:
    """The entries a declared re-reading is licensed for, in order."""
    return tuple(str(row["key"]) for row in ranked()
                 if row["verdict"] == "recoverable" and row["supported"])


# ═════════════════════════════════════════════════════════════════════════
# 4.  THE REPORT
# ═════════════════════════════════════════════════════════════════════════

def review_sweep_report() -> Dict[str, object]:
    """The register, recomputed: nothing here is quoted from a document."""
    rows = ranked()
    by_class: Dict[str, List[str]] = {}
    for row in rows:
        by_class.setdefault(str(row["verdict"]), []).append(str(row["key"]))
    defects: List[str] = []
    for row in rows:
        if not row["document_is_a_study"]:
            defects.append(f"{row['key']}: cites {row['document']}, which is "
                           f"absent or a stub")
        if row["claims_a_discarded_quantity"] and not row["attribute_resolves"]:
            defects.append(f"{row['key']}: claims a discarded quantity and "
                           f"names no attribute that reports it")
    return {
        "entries": rows,
        "count": len(rows),
        "classes": CLASSES,
        "by_class": {name: tuple(by_class.get(name, ())) for name in CLASSES},
        "recoverable": recoverable(),
        "licensed_for_re_reading": len(recoverable()),
        "defects": tuple(defects),
        "holds": not defects,
        "rule": ("A stalled result is ranked for re-reading by whether a "
                 "quantity identifiable at the coarse reading was discarded, "
                 "not by how disappointing it was.  Where nothing was "
                 "discarded, escalation is not licensed and the entry names "
                 "what is needed instead."),
        "limits": ("The class of an entry is a judgement, declared here and "
                   "open to being wrong; what is measured is that the "
                   "document exists, that a claimed discarded quantity has "
                   "somewhere it is reported, and that the order follows the "
                   "rule.  The register is written before the next "
                   "re-reading, which is the only time it can constrain one."),
    }


if __name__ == "__main__":                      # pragma: no cover
    report = review_sweep_report()
    print(f"entries        {report['count']}")
    for row in report["entries"]:               # type: ignore[union-attr]
        mark = "" if row["supported"] else "  (unsupported)"
        print(f"  {row['key']:<26} {row['verdict']:<16}{mark}")
    print(f"re-reading licensed for: "
          f"{', '.join(report['recoverable']) or 'nothing'}")
    print(f"holds          {report['holds']}")

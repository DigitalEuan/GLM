"""``glm_universal.reasoning.native_parity`` -- keep the native method, refine it.

The owner's instruction (Phase 70)
----------------------------------
*Where a "standard" method is equal to or only slightly better than a
Golay-Leech or 24D or other "native" GLM method, retain the native method and
see if it can be refined to match or beat the standard method.*

This module is that round's instrument.  It holds two things.

**The ledger** (:data:`LEDGER`): every native/standard pair an earlier study
measured, with the figure that study recorded and the class it falls in --
native ahead, parity, standard narrowly ahead, standard far ahead.  The rows
are declared, not recomputed here: each names the study and the report that
recomputes it.

**The refinements** (:func:`native_parity_report`), measured on the probe sets
the earlier studies used:

``T1``  Lean-corpus retrieval.  A scale-9 Leech address is ``9f + e``: the
        read-back ``f`` (the features, by ``GLM.Address.readback_unique``) and
        a residue ``e`` with every ``|e_i| <= 4``.  The shipped ranking used the
        raw distance, which mixes the two; the standard ranking uses ``f`` and
        breaks ties by name.  The refined native ranking reads both layers,
        coarse first -- read-back distance, then Leech distance, then name.
``T2``  The same refinement over the document corpus's lexical book, and the
        live document ranking (word overlap) with its exact ties broken by the
        lexical Leech distance instead of the alphabet.
``T3``  The controller's scorer read back to its carrier, measured in the
        metric ``GLM.Controller.minimal_length_eq_l1`` proves is the move count.

Every figure is an integer or a :class:`~fractions.Fraction` (D7).  The
declarations were committed before this module existed
(``studies/NATIVE_PARITY_STUDY.md`` §2); the Lean half is
``RequestProject/GLM/NativeParity.lean``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ..derived import memo
from .. import integrity
from . import controller as ctl
from . import lean_address as la
from . import retrieval as rt

__all__ = [
    "LedgerRow", "LEDGER", "CLASSES", "ledger_report", "exactness_report",
    "declaration_report", "goal_report", "document_report",
    "controller_parity_report", "native_parity_report", "tool_summary",
    "module_digest", "measure", "write_measurements", "measurements", "state",
    "current", "DATA_PATH",
]

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
#  T1 -- the Lean corpus
# ===========================================================================

def _tally(rows: Sequence[Tuple[Sequence[rt.Candidate], frozenset]]
           ) -> Dict[str, object]:
    """Hits at every k of the ladder, precision@5 and MRR@10."""
    ladder = rt.K_LADDER
    hits = {k: 0 for k in ladder}
    found5 = 0
    rr = Fraction(0)
    for found, relevant in rows:
        for k in ladder:
            hit, got, _ = rt._score(found, relevant, k)
            hits[k] += hit
            if k == 5:
                found5 += got
        rr += rt._score(found, relevant, max(ladder))[2]
    count = len(rows)
    return {"queries": count, "hits": hits,
            "precision_at_5": Fraction(found5, 5 * count) if count else Fraction(0),
            "mrr_at_10": rr / count if count else Fraction(0)}


#: The rankings T1 scores: the two refined native ones, the shipped native
#: one, the standard one, and the like-for-like standard for round two.
T1_SCHEMES: Tuple[str, ...] = ("native", "native2", "address", "features",
                               "features2")


def _hits_at_least(a: Dict[str, object], b: Dict[str, object]) -> bool:
    """``a`` has at least ``b``'s hits at every k of the ladder."""
    return all(a["hits"][k] >= b["hits"][k] for k in rt.K_LADDER)


def _at_least(a: Dict[str, object], b: Dict[str, object]) -> bool:
    """``a`` has at least ``b``'s hits at every k, and at least its MRR@10."""
    return (all(a["hits"][k] >= b["hits"][k] for k in rt.K_LADDER)
            and a["mrr_at_10"] >= b["mrr_at_10"])


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


@memo
def declaration_report() -> Dict[str, object]:
    """N1: the 209 declaration queries, four rankings side by side."""
    names = rt.query_sample(rt.SAMPLE)
    top = max(rt.K_LADDER)
    address = rt._point_table("address")
    features = rt._point_table("features")
    lexical = rt._point_table("lexical")
    lexical_raw = rt.lexical_table()
    rows: Dict[str, List] = {scheme: [] for scheme in T1_SCHEMES}
    for name in names:
        relevant = rt.relatives(name)
        point = address.get(name)
        if point is None:
            continue
        rows["native"].append((rt.rank_by_native(point, top, name), relevant))
        rows["native2"].append((rt.rank_by_native2(point, lexical[name], top,
                                                   name), relevant))
        rows["features2"].append((rt.rank_by_features2(
            features[name], lexical_raw[name], top, name), relevant))
        rows["address"].append((rt.rank_by_point(address, point, top, name),
                                relevant))
        rows["features"].append((rt.rank_by_point(features, features[name],
                                                  top, name), relevant))
    out = {scheme: _tally(r) for scheme, r in rows.items()}
    return {"schemes": out,
            "met_against_features": _at_least(out["native"], out["features"]),
            "met_against_address": _at_least(out["native"], out["address"]),
            "native2_against_features": _at_least(out["native2"],
                                                  out["features"]),
            "native2_like_for_like": _hits_at_least(out["native2"],
                                                    out["features2"])}


@memo
def goal_report() -> Dict[str, object]:
    """N2 (and N3's goal half): the 102 goal queries, addressed live."""
    names = rt.query_sample(rt.GOAL_SAMPLE)
    top = max(rt.K_LADDER)
    decls = {d.name: d for d in la.declarations()}
    address = rt._point_table("address")
    features = rt._point_table("features")
    exact_lexical_goal: List[str] = []
    rows: Dict[str, List] = {scheme: [] for scheme in T1_SCHEMES}
    exact = 0
    for name in names:
        relevant = rt.relatives(name)
        text = rt.strip_declaration_head(decls[name].statement)
        vector = rt.goal_features(text, exclude=name)
        point = la.quantise(vector)
        lexical_vec = rt.lexical_vector(text)
        lexical_point = la.quantise(lexical_vec)
        if rt.readback(point) == tuple(vector):
            exact += 1
        if rt.readback(lexical_point) == tuple(lexical_vec):
            exact_lexical_goal.append(name)
        rows["native"].append((rt.rank_by_native(point, top, name), relevant))
        rows["native2"].append((rt.rank_by_native2(point, lexical_point, top,
                                                   name), relevant))
        rows["features2"].append((rt.rank_by_features2(vector, lexical_vec,
                                                       top, name), relevant))
        rows["address"].append((rt.rank_by_point(address, point, top, name),
                                relevant))
        rows["features"].append((rt.rank_by_point(features, vector, top, name),
                                 relevant))
    out = {scheme: _tally(r) for scheme, r in rows.items()}
    return {"schemes": out, "readback_exact": exact, "queries": len(names),
            "lexical_readback_exact": len(exact_lexical_goal),
            "native2_against_features": all(
                out["native2"]["hits"][k] >= out["features"]["hits"][k]
                for k in rt.K_LADDER),
            "native2_like_for_like": _hits_at_least(out["native2"],
                                                    out["features2"]),
            "met_against_features": all(
                out["native"]["hits"][k] >= out["features"]["hits"][k]
                for k in rt.K_LADDER),
            "met_against_address": all(
                out["native"]["hits"][k] >= out["address"]["hits"][k]
                for k in rt.K_LADDER)}


# ===========================================================================
#  T2 -- the document corpus
# ===========================================================================

#: The four document rankings T2 scores.
DOCUMENT_SCHEMES: Tuple[str, ...] = ("lexical", "lexical_raw", "lexical_native",
                                     "lexical_native2", "lexical_raw2",
                                     "text", "text_native")


@memo
def document_report() -> Dict[str, object]:
    """N4: the 60 section queries of the corpus address study."""
    # The corpus layer sits above the reasoning layer and imports it, so it is
    # read lazily here rather than at import time.
    from ..corpus import address as ad
    state = ad.cache_state()
    if not state["fresh"]:
        return {"answered": False, "cache": state,
                "reason": "the document address book is stale; run "
                          "python3 -m glm_universal.corpus --write"}
    names = ad.query_sample(60)
    k = 5
    scores: Dict[str, Dict[str, object]] = {}
    for scheme in DOCUMENT_SCHEMES:
        hits = 0
        precision = Fraction(0)
        for name in names:
            relevant = ad.relative_table()[name]
            found = ad.rank(ad._query_text(name), k=k, scheme=scheme,
                            exclude=name)
            good = sum(1 for item in found if item.name in relevant)
            hits += 1 if good else 0
            precision += Fraction(good, k)
        count = len(names)
        scores[scheme] = {"hits": hits,
                          "precision_at_5": precision / count if count
                          else Fraction(0)}
    vectors = ad.stored_vectors("lexical")
    readbacks = ad.native_readbacks()
    exact = sum(1 for name, vector in vectors.items()
                if readbacks.get(name) == tuple(vector))

    def at_least(a: str, b: str) -> bool:
        return (scores[a]["hits"] >= scores[b]["hits"]
                and scores[a]["precision_at_5"] >= scores[b]["precision_at_5"])

    return {"answered": True, "queries": len(names), "k": k,
            "units": len(ad.units()), "schemes": scores,
            "readback_checked": len(vectors), "readback_exact": exact,
            "met_native_vs_raw": at_least("lexical_native", "lexical_raw"),
            "met_live_ranking": at_least("text_native", "text"),
            "native2_against_raw": at_least("lexical_native2", "lexical_raw"),
            "native2_like_for_like": at_least("lexical_native2",
                                              "lexical_raw2")}


# ===========================================================================
#  T3 -- the controller
# ===========================================================================

#: The scorers T3 compares: the refined native one, the exact one, and the
#: two it refines.
CONTROLLER_SCORERS: Tuple[str, ...] = ("readback", "exponent", "address",
                                       "carrier")


@memo
def controller_parity_report() -> Dict[str, object]:
    """N5: the 24 reachable tasks under the read-back scorer."""
    targets = ctl.task_targets()
    reachable = [n for n in targets if ctl.classify_target(n)[0] is not None]
    rows: Dict[str, Dict[str, object]] = {}
    for scorer in CONTROLLER_SCORERS:
        solved = minimal = verified = proposals = 0
        for name in reachable:
            outcome = ctl.solve(name, scorer)
            proposals += outcome.get("proposals", 0)
            if outcome["answered"]:
                solved += 1
                minimal += 1 if outcome["minimal"] else 0
                verified += 1 if outcome["verified"] else 0
        count = len(reachable)
        rows[scorer] = {"solved": solved, "minimal": minimal,
                        "verified": verified, "proposals": proposals,
                        "mean_proposals": Fraction(proposals, count)
                        if count else Fraction(0)}
    ours, exact = rows["readback"], rows["exponent"]
    count = len(reachable)
    return {"tasks": count, "scorers": rows,
            "met": (ours["solved"] == count and ours["minimal"] == count
                    and ours["verified"] == count
                    and ours["mean_proposals"] == exact["mean_proposals"])}


# ===========================================================================
#  The whole report
# ===========================================================================

@memo
def native_parity_report() -> Dict[str, object]:
    """Every declared mark of the study, measured, with the verdict."""
    exact = exactness_report()
    decl = declaration_report()
    goal = goal_report()
    docs = document_report()
    control = controller_parity_report()
    marks = {
        "N1": bool(decl["met_against_features"]),
        "N1_address": bool(decl["met_against_address"]),
        "N2": bool(goal["met_against_features"]),
        "N3": bool(exact["met"]) and goal["readback_exact"] == goal["queries"],
        "N4a": bool(docs.get("met_native_vs_raw", False)),
        "N4b": bool(docs.get("met_live_ranking", False)),
        "N5": bool(control["met"]),
        "N6": bool(decl["native2_against_features"])
              and bool(goal["native2_against_features"]),
        "N7": bool(decl["native2_like_for_like"])
              and bool(goal["native2_like_for_like"]),
        "N8": bool(docs.get("native2_against_raw", False))
              and bool(docs.get("native2_like_for_like", False)),
    }
    return {"ledger": ledger_report(), "exactness": exact,
            "declarations": decl, "goals": goal, "documents": docs,
            "controller": control, "marks": marks,
            "all_met": all(marks.values()),
            "round_one": {m: marks[m] for m in ("N1", "N1_address", "N2", "N3",
                                                 "N4a", "N4b", "N5")},
            "round_two": {m: marks[m] for m in ("N6", "N7", "N8")},
            "study": STUDY, "lean_file": LEAN_FILE}


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


# ===========================================================================
#  The cache, guarded by a digest
# ===========================================================================

#: The report costs about a minute and a half -- 441 live Leech decodes for the
#: controller, and every declaration and section ranked four ways -- so it is
#: taken once and stored beside the digest of everything it reads.
DATA_PATH = Path(__file__).resolve().parent / "_data" / "native_parity.json"

_SOURCES: Tuple[str, ...] = (
    "reasoning/native_parity.py",
    "reasoning/retrieval.py",
    "reasoning/lean_address.py",
    "reasoning/controller.py",
    "reasoning/verifier.py",
    "corpus/address.py",
    "reasoning/_data/lean_addresses.json",
    "reasoning/_data/lean_lexical_addresses.json",
    "reasoning/_data/controller_addresses.json",
    "corpus/_data/document_addresses.json",
)


def module_digest() -> str:
    """One digest over the sources, the Lean tree and the written corpus.

    The Lean tree is in it because the declaration corpus *is* the Lean tree;
    the written corpus is in it because the document queries are its
    sections.  Either moving makes the stored figures stale.
    """
    from ..corpus import inventory as inv
    root = Path(__file__).resolve().parent.parent
    files = integrity.tree_digest([root / name for name in _SOURCES
                                   if (root / name).exists()], root)
    joined = "|".join((files, la.tree_digest(), inv.corpus_digest()))
    return integrity.sha256_hex(joined.encode("utf-8"))


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return {"__fraction__": f"{value.numerator}/{value.denominator}"}
    if isinstance(value, dict):
        return {str(key): _freeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(item) for item in value]
    return value


def _thaw(value: object) -> object:
    if isinstance(value, dict):
        text = value.get("__fraction__")
        if isinstance(text, str) and len(value) == 1:
            return Fraction(text)
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_thaw(item) for item in value]
    return value


def measure() -> Dict[str, object]:
    """The report, with the digest of what it was taken from beside it."""
    payload = dict(native_parity_report())
    payload["source_digest"] = module_digest()
    return payload


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the measurements and store them beside their digest."""
    global _cache
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_freeze(measure()), indent=1, sort_keys=True,
                   ensure_ascii=False) + "\n", encoding="utf-8")
    _cache = None
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """What is stored, whether or not it is still current."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    _cache = _thaw(loaded) if isinstance(loaded, dict) else None
    return _cache


def state() -> Dict[str, object]:
    """Present, and taken from the sources as they stand?"""
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "live_digest": live,
                "stored_digest": None, "verdict": "absent"}
    same = stored.get("source_digest") == live
    return {"present": True, "fresh": same, "live_digest": live,
            "stored_digest": stored.get("source_digest"),
            "verdict": "fresh" if same else "stale"}


def current() -> Optional[Dict[str, object]]:
    """The measurements if they still describe the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored

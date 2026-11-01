"""``glm_universal.knowledge.source_tiers`` -- the measurement of Phase 162.

``studies/SOURCE_TIERS_STUDY.md``: every corpus experiment read tier by tier,
and how the supplied tier should count.

* **The tiers** (:func:`tier_of`, by path alone): ``core`` (the documentation:
  written Markdown and text outside ``studies/``), ``code`` (Python),
  ``lean`` (Lean), ``studies`` (``studies/`` and the JSON and CSV reports the
  instruments emit), ``supplied`` (anything under ``archive/`` or
  ``source_material/``).  The **slices**: ``whole``, ``written`` (every tier
  but ``supplied``) and ``supplied``; the counted model is additive, so the
  slices are three readings of one model (``train_filter_add``).
* **Prediction by slice** on the held-out rule of Phase 154 (every fifth
  document of the sorted corpus), on the written and the supplied test (the
  novel held-out sentences of each slice): the backed-off accuracy and the
  K3' majority guard; each tier left out of the training documents in turn
  (written test), against a **size-matched pseudo-tier** -- a blind draw of as
  many training documents as the supplied tier holds, by the project's
  deterministic null permutation (label :data:`PSEUDO_LABEL`).
* **The four policies** for the supplied tier under the K3' guard: the whole
  corpus as it is (``whole``), the supplied tier ``excluded``, the written
  tier counted twice (``downweighted``, ``train_downweight``), the same with
  the guard's support counted unweighted (``downweighted_unweighted``, the
  amended T5'), and the ``confirmed`` reading -- the whole corpus's answer
  admitted only when the written tier has counted that word after that
  context (``confirm_some_iff``).
* **define, the glossary grade and word use by slice**: ``define`` on the
  corpus's bold terms (K8''s list) and the tier of each first answer; the
  context-ranked glossary grade (Phase 155); the number words' share of
  number-word neighbours under each slice's positional sets.

Marks.  The study's reconstruction (§5) records the subjects of T2, T4, T5,
T5' and T8 only; T1, T3, T6 and T7 were not recorded anywhere that survived,
and T8 (*no answer of the GLM moves*) needs the frozen-path comparison of the
evaluation, which this module does not run.  Those five are reported **not
met** with the reason in ``unmeasured`` -- a mark this module cannot measure
is never reported met.  L1 is read from the tree: ``SourceTiers.lean``
present and free of ``sorry``.

:func:`compute` takes the measurement (a few minutes).  Nothing here writes:
the stored measurement (``_data/source_tiers.json``) is written only by
``tools source-tiers --write``.

*Created 31 October 2026 (repository check).*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation (the 29 October placeholder returned the
report's shape only); rebuilt from studies/SOURCE_TIERS_STUDY.md (itself a
reconstruction from the round records), MASTER_PLAN.md Phase 162, the report
shape read by tools.py ``_source_tiers``, and the Phase 154/155 machinery
(knowledge/study.py, knowledge/glossary.py).  The tier boundaries, the
pseudo-tier label and the slice test sets are declared here; the original's
are not recorded.*

*Last altered 31 October 2026 (repository check): the Lean file's path is
stored relative to the repository root, not as an absolute path.*
"""
from __future__ import annotations

import dataclasses
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .. import constants, integrity
from . import model as mdl
from . import reader as rd

__all__ = [
    "DATA_PATH", "_SOURCES", "compute", "measure", "write_measurements",
    "measurements", "state", "current", "module_digest", "source_tiers_report",
    "TIERS", "SLICES", "POLICIES", "tier_of", "in_slice", "census",
    "guarded_scores", "PSEUDO_LABEL",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "source_tiers.json"

TIERS: Tuple[str, ...] = ("core", "code", "lean", "studies", "supplied")
SLICES: Tuple[str, ...] = ("whole", "written", "supplied")
POLICIES: Tuple[str, ...] = ("whole", "excluded", "downweighted",
                             "downweighted_unweighted", "confirmed")

#: The label of the deterministic draw of the size-matched pseudo-tier.
PSEUDO_LABEL = "glm-source-tiers-pseudo"

_SOURCES: Tuple[str, ...] = (
    "knowledge/source_tiers.py",
    "knowledge/model.py",
    "knowledge/reader.py",
    "knowledge/answer.py",
    "knowledge/glossary.py",
    "knowledge/study.py",
)

_cache: Optional[Dict[str, object]] = None


# ---------------------------------------------------------------------------
#  Tiers and slices
# ---------------------------------------------------------------------------

def tier_of(path: str) -> str:
    """The tier of a corpus path, by the path alone."""
    top = rd.top_folder(path)
    lower = path.lower()
    if top in ("archive", "source_material") or ".zip/" in lower:
        return "supplied"
    if lower.endswith(".lean"):
        return "lean"
    if lower.endswith(".py"):
        return "code"
    if top == "studies" or lower.endswith((".json", ".csv")):
        return "studies"
    return "core"


def in_slice(path: str, name: str) -> bool:
    if name == "whole":
        return True
    supplied = tier_of(path) == "supplied"
    return supplied if name == "supplied" else not supplied


def census(documents: Sequence[rd.Document]) -> Dict[str, Any]:
    """Documents, distinct sentences and their tokens, by tier."""
    from . import study as cks
    rows = {t: {"documents": 0, "sentences": 0, "tokens": 0} for t in TIERS}
    for d in documents:
        row = rows[tier_of(d.path)]
        row["documents"] += 1
        sents = cks.distinct_sentences([d])
        row["sentences"] += len(sents)
        row["tokens"] += sum(len(s) for s in sents)
    total = {k: sum(r[k] for r in rows.values()) for k in ("documents", "sentences", "tokens")}
    return {"tiers": rows, "total": total}


# ---------------------------------------------------------------------------
#  Scoring
# ---------------------------------------------------------------------------

def _majority(row: Optional[Mapping[str, int]], support: Optional[int] = None
              ) -> Optional[str]:
    """The K3' guard on a two-token row: seen at least three times (``support``
    if given, else the row's total), a unique maximum holding more than half."""
    if not row:
        return None
    total = sum(row.values())
    seen = total if support is None else support
    top = max(row.values())
    winners = [c for c, n in row.items() if n == top]
    if seen < 3 or len(winners) != 1 or 2 * top <= total:
        return None
    return winners[0]


def guarded_scores(models: Mapping[str, mdl.Model], sentences: Iterable[Tuple[str, ...]],
                   ) -> Dict[str, Dict[str, int]]:
    """The four policies (and the whole corpus) on ``sentences``.

    ``models`` holds ``whole``, ``written`` and ``supplied``, all trained on
    the same training documents.
    """
    whole, written, supplied = models["whole"], models["written"], models["supplied"]
    out = {p: {"answered": 0, "right": 0} for p in POLICIES}
    for toks in sentences:
        padded = (mdl.BOS, mdl.BOS) + tuple(toks) + (mdl.EOS,)
        for i in range(2, len(padded)):
            key = (padded[i - 2], padded[i - 1])
            truth = padded[i]
            w_row = whole.ctx2.get(key)
            wr_row = written.ctx2.get(key)
            s_row = supplied.ctx2.get(key)
            picks: Dict[str, Optional[str]] = {}
            picks["whole"] = _majority(w_row)
            picks["excluded"] = _majority(wr_row)
            doubled: Counter = Counter()
            if wr_row:
                for c, n in wr_row.items():
                    doubled[c] += 2 * n
            if s_row:
                doubled.update(s_row)
            picks["downweighted"] = _majority(doubled)
            picks["downweighted_unweighted"] = _majority(
                doubled, support=sum(w_row.values()) if w_row else 0)
            winner = picks["whole"]
            picks["confirmed"] = (winner if winner is not None and wr_row
                                  and wr_row.get(winner, 0) > 0 else None)
            for p, guess in picks.items():
                if guess is not None:
                    out[p]["answered"] += 1
                    out[p]["right"] += guess == truth
    return out


def _ratio(a: int, b: int) -> Fraction:
    return Fraction(a, b) if b else Fraction(0)


def _slice_knowledge(knowledge: mdl.Knowledge, name: str) -> mdl.Knowledge:
    """``knowledge`` with only the sentences of one slice (and their postings);
    ``define`` reads only those."""
    kept = tuple(s for s in knowledge.sentences if in_slice(s.document, name))
    postings: Dict[str, List[int]] = {}
    for sid, s in enumerate(kept):
        for t in set(s.tokens):
            postings.setdefault(t, []).append(sid)
    return dataclasses.replace(knowledge, sentences=kept,
                               postings={t: tuple(v) for t, v in postings.items()})


def _number_share(model: mdl.Model) -> Dict[str, Any]:
    """The number words' share of number-word neighbours under the slice's
    own positional sets (squared cosine, ties by count then spelling)."""
    from . import study as cks
    sets = mdl.positional_sets(model)
    words = set(cks.NUMBER_WORDS)
    hits = asked = 0
    for w in cks.NUMBER_WORDS:
        mine = sets.get(w)
        if not mine:
            continue
        asked += 1
        scored = []
        for other, feats in sets.items():
            if other == w:
                continue
            k = len(mine & feats)
            if k:
                scored.append((Fraction(k * k, len(mine) * len(feats)), other))
        scored.sort(key=lambda r: (-r[0], -model.unigram[r[1]], r[1]))
        hits += sum(1 for _, o in scored[:10] if o in words)
    return {"asked": asked, "hits": hits, "neighbours": 10 * len(cks.NUMBER_WORDS),
            "share": _ratio(hits, 10 * len(cks.NUMBER_WORDS))}


def _lean_state() -> Dict[str, Any]:
    path = constants.lean_file("SourceTiers.lean")
    #  Repository-relative, so the stored measurement does not depend on
    #  where the checkout lives.
    try:
        shown = path.relative_to(constants.REPOSITORY_ROOT).as_posix()
    except ValueError:
        shown = path.name
    if not path.is_file():
        return {"present": False, "path": shown, "sorry": None}
    text = path.read_text(encoding="utf-8", errors="replace")
    return {"present": True, "path": shown, "sorry": "sorry" in text}


# ---------------------------------------------------------------------------
#  The measurement
# ---------------------------------------------------------------------------

def compute(knowledge: Any = None) -> Dict[str, object]:
    """Take the Phase 162 measurement from the corpus as it now is."""
    from . import answer as ans
    from . import glossary as gl
    from . import study as cks
    knowledge = mdl.load() if knowledge is None else knowledge
    docs = list(knowledge.documents)
    train, held = cks.heldout_split(docs)
    known = {s.tokens for d in train for s in d.sentences}
    tests = {name: [t for t in cks.distinct_sentences(
                d for d in held if in_slice(d.path, name)) if t not in known]
             for name in ("written", "supplied")}
    models = {name: mdl.train([d for d in train if in_slice(d.path, name)],
                              with_window=False) for name in SLICES}
    by_slice: Dict[str, Dict[str, Any]] = {}
    for name in SLICES:
        by_slice[name] = {}
        for test, sents in tests.items():
            s = cks.prediction_stats(models[name], sents)
            by_slice[name][test] = {
                "positions": s["positions"], "right": s["right"],
                "accuracy": _ratio(s["right"], s["positions"]),
                "majority_answered": s["majority_answered"],
                "majority_right": s["majority_right"],
                "majority_precision": _ratio(s["majority_right"], s["majority_answered"])}
    left_out: Dict[str, Dict[str, Any]] = {}
    for tier in TIERS:
        part = [d for d in train if tier_of(d.path) != tier]
        s = cks.prediction_stats(mdl.train(part, with_window=False), tests["written"])
        left_out[tier] = {"written": {"documents_left_out": len(train) - len(part),
                                      "positions": s["positions"], "right": s["right"]}}
    n_supplied = sum(1 for d in train if tier_of(d.path) == "supplied")
    perm = integrity.seeded_permutation(len(train), PSEUDO_LABEL)
    drop = set(perm[:n_supplied])
    pseudo = [d for i, d in enumerate(train) if i not in drop]
    s = cks.prediction_stats(mdl.train(pseudo, with_window=False), tests["written"])
    control = {"written": {"documents_left_out": n_supplied,
                           "positions": s["positions"], "right": s["right"]}}
    policies: Dict[str, Any] = {}
    for test, sents in tests.items():
        scores = guarded_scores(models, sents)
        for p, row in scores.items():
            row["precision"] = _ratio(row["right"], row["answered"])
        policies[test] = {"positions": sum(len(t) + 1 for t in sents),
                          "policies": scores}
    terms = cks.bold_terms(knowledge)
    define: Dict[str, Any] = {}
    glossary: Dict[str, Any] = {}
    words: Dict[str, Any] = {}
    held_glossary = gl.hold_out(knowledge)
    for name in SLICES:
        k = _slice_knowledge(knowledge, name)
        answered, tiers = 0, Counter()
        for term in terms:
            got = ans.define(term, k)
            if got.get("ok"):
                answered += 1
                tiers[tier_of(got["address"].split("#", 1)[0])] += 1
        define[name] = {"terms": len(terms), "answered": answered,
                        "answer_tiers": {t: tiers[t] for t in TIERS if tiers[t]}}
        g = gl.grade_definitions(_slice_knowledge(held_glossary, name), "context")
        glossary[name] = {k2: g[k2] for k2 in ("terms", "answered", "agree",
                                                "agree_top", "total_grade",
                                                "control_total")}
        words[name] = _number_share(models[name])
    whole_w = by_slice["whole"]["written"]
    written_w = by_slice["written"]["written"]
    cost_supplied = whole_w["right"] - left_out["supplied"]["written"]["right"]
    cost_pseudo = whole_w["right"] - control["written"]["right"]
    pol = policies["written"]["policies"]
    lean = _lean_state()
    marks = {
        "L1": bool(lean["present"]) and lean["sorry"] is False,
        "T1": False,
        "T2": written_w["right"] >= whole_w["right"],
        "T3": False,
        "T4": cost_supplied < cost_pseudo,
        "T5": pol["confirmed"]["precision"] > pol["whole"]["precision"],
        "T6": False,
        "T7": False,
        "T8": False,
    }
    amended = {"T5'": pol["downweighted_unweighted"]["precision"] > pol["whole"]["precision"]}
    unmeasured = {
        "T1": "the subject of T1 was not recorded anywhere that survived (SOURCE_TIERS_STUDY.md §5)",
        "T3": "the subject of T3 was not recorded anywhere that survived (SOURCE_TIERS_STUDY.md §5)",
        "T6": "the subject of T6 was not recorded anywhere that survived (SOURCE_TIERS_STUDY.md §5)",
        "T7": "the subject of T7 was not recorded anywhere that survived (SOURCE_TIERS_STUDY.md §5)",
        "T8": "no answer of the GLM moves: needs the evaluation's frozen-path comparison, not run here",
    }
    return {
        "census": census(docs),
        "prediction": {"training_documents": len(train), "held_documents": len(held),
                       "test_sentences": {k2: len(v) for k2, v in tests.items()},
                       "by_slice": by_slice, "left_out": left_out,
                       "control": control, "policies": policies,
                       "cost": {"supplied": cost_supplied, "pseudo": cost_pseudo}},
        "define": define,
        "glossary": glossary,
        "words": words,
        "lean": lean,
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
        "unmeasured": unmeasured,
        "amended": amended,
        "amended_met": sum(1 for v in amended.values() if v),
        "amended_taken": len(amended),
    }


# ---------------------------------------------------------------------------
#  The stored measurement (written only by ``tools source-tiers --write``)
# ---------------------------------------------------------------------------

def _plain(x: Any) -> Any:
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def module_digest() -> str:
    root = _HERE.parent  # glm_universal/
    paths = [root / n for n in sorted(set(_SOURCES))]
    return integrity.tree_digest(paths, root)


def measure() -> Dict[str, object]:
    r = compute()
    r["source_digest"] = module_digest()
    return r


def write_measurements(path: Optional[Path] = None) -> Path:
    out = path if path is not None else DATA_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_plain(measure()), indent=1, sort_keys=True,
                      ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    global _cache
    _cache = None
    return out


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    try:
        _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _cache = None
    return _cache


def state() -> Dict[str, object]:
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    stored_digest = stored.get("source_digest")
    return {"present": True, "fresh": stored_digest == live,
            "verdict": "current" if stored_digest == live else "stale",
            "live_digest": live, "stored_digest": stored_digest}


def current() -> Optional[Dict[str, object]]:
    if state()["fresh"]:
        return measurements()
    return None


def source_tiers_report() -> Dict[str, object]:
    """If fresh: the stored measurement with ``available=True``.  Else: why
    not (absent or stale) and the command that re-takes it."""
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    verdict = state()["verdict"]
    return {
        "available": False,
        "verdict": verdict,
        "reasons": [(f"the stored measurement is {verdict}; re-take it with "
                     f"python3 -m glm_universal.tools source-tiers --write")],
    }

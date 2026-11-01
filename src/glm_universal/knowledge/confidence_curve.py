"""``glm_universal.knowledge.confidence_curve`` -- the measurement of Phase 168.

``studies/CONFIDENCE_CURVE_STUDY.md``: three operating modes of the counted
predictor declared before they are measured, and definitions that describe
their own quality.

* **The folds** (§1, :func:`fold_of`): a document's fold is the SHA-256 of its
  path modulo 5 (taken through ``glm_universal.integrity``).  Fold 4 is held
  out, fold 3 calibrates; folds 0-2 train the calibration model, folds 0-3
  the held-out model.  Positions are every token, and the end marker, of the
  novel sentences of the test fold.
* **The guards** (§2): ``(c, s)`` answers a position when the deciding context
  is the two-token one, its maximum is unique, it was seen at least ``c``
  times and the winner holds more than the share ``s`` of what followed --
  the 143 guards of :data:`COUNTS` x :data:`SHARES`.
* **The modes**, chosen on the calibration fold only (``u`` its unguarded
  accuracy): **sure**, the guard of greatest calibration coverage with
  precision at least ``3u``; **balanced**, at least ``3u/2``; ties to the
  higher precision, the smaller ``c``, the smaller ``s``.  **candidate**: the
  :data:`TOP` most frequent continuations (count, then spelling) of the
  two- or one-token context, a hit when the truth is among them.  The chosen
  guards are applied unchanged to the held-out fold, and to the order control
  (the held-out model's documents with every sentence's tokens sorted).
* **The definitions' quality** (§3, :func:`quality`): every context-ranked
  ``define`` answer carries its witness and address, the pattern and its
  strength (0 strongest), the source and the context support; it is
  **strong** when the strength is at most 2 and the support at least 2,
  otherwise **weak**; graded on the held-out glossary of Phase 155.

Marks C1-C6, D1, D2 (§4).  :func:`compute` takes the measurement (a few
minutes).  Nothing here writes: the stored measurement
(``_data/confidence_curve.json``) is written only by ``tools
confidence-curve --write``.

*Created 31 October 2026 (repository check).*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation (the 29 October placeholder returned the
report's shape only); rebuilt from studies/CONFIDENCE_CURVE_STUDY.md §§1-4
and 7, MASTER_PLAN.md Phase 168, the report shape read by tools.py
``_confidence_curve`` and the Phase 154/155 machinery (knowledge/study.py,
knowledge/answer.py, knowledge/glossary.py).*
"""
from __future__ import annotations

import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .. import integrity
from . import model as mdl
from . import reader as rd

__all__ = [
    "DATA_PATH", "_SOURCES", "compute", "measure", "write_measurements",
    "measurements", "state", "current", "module_digest", "confidence_curve_report",
    "TOP", "COUNTS", "SHARES", "GUARDS", "fold_of", "position_table",
    "guard_score", "choose", "quality",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "confidence_curve.json"

TOP: int = 3  # the candidate top-K

#: The guard grid (§2).
COUNTS: Tuple[int, ...] = (1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 25, 32)
SHARES: Tuple[Fraction, ...] = (
    Fraction(0), Fraction(1, 5), Fraction(1, 4), Fraction(1, 3), Fraction(2, 5),
    Fraction(1, 2), Fraction(3, 5), Fraction(2, 3), Fraction(3, 4), Fraction(4, 5),
    Fraction(9, 10))
GUARDS: Tuple[Tuple[int, Fraction], ...] = tuple((c, s) for c in COUNTS for s in SHARES)

FOLDS = 5
HELD_FOLD = 4
CALIBRATION_FOLD = 3

_SOURCES: Tuple[str, ...] = (
    "knowledge/confidence_curve.py",
    "knowledge/answer.py",
    "knowledge/glossary.py",
    "knowledge/model.py",
    "knowledge/reader.py",
    "knowledge/study.py",
)

_cache: Optional[Dict[str, object]] = None


def fold_of(path: str) -> int:
    """``sha256(path) mod 5``."""
    return int(integrity.sha256_hex(path.encode("utf-8")), 16) % FOLDS


def _ratio(a: int, b: int) -> Fraction:
    return Fraction(a, b) if b else Fraction(0)


# ---------------------------------------------------------------------------
#  Positions, guards and modes
# ---------------------------------------------------------------------------

def position_table(model: mdl.Model, sentences: Iterable[Tuple[str, ...]]
                   ) -> Dict[str, Any]:
    """One pass over the positions of ``sentences`` under ``model``.

    ``guarded``: a Counter of ``(total, top, right)`` over the positions whose
    deciding context is the two-token one with a unique maximum (every guard
    is a filter on it); ``positions``; ``unguarded_right`` (the backed-off
    model, a tie at the top broken by spelling, the most frequent token where
    no context was seen); ``candidate_covered`` and ``candidate_hits``.
    """
    from . import study as cks
    rows = cks._Rows(model)
    top3: Dict[Tuple[str, ...], Tuple[str, ...]] = {}

    def best3(key: Tuple[str, ...], row: Mapping[str, int]) -> Tuple[str, ...]:
        got = top3.get(key)
        if got is None:
            got = tuple(sorted(row, key=lambda c: (-row[c], c))[:TOP])
            top3[key] = got
        return got

    guarded: Counter = Counter()
    positions = right = covered = hits = 0
    for toks in sentences:
        padded = (mdl.BOS, mdl.BOS) + tuple(toks) + (mdl.EOS,)
        for i in range(2, len(padded)):
            truth = padded[i]
            positions += 1
            a, b = padded[i - 2], padded[i - 1]
            two = rows.two(a, b)
            if two is not None:
                total, top, ties, winner = two
                right += truth == winner
                if ties == 1:
                    guarded[(total, top, truth == winner)] += 1
                covered += 1
                hits += truth in best3((a, b), model.ctx2[(a, b)])
                continue
            one = rows.one(b)
            if one is not None:
                right += truth == one[3]
                covered += 1
                hits += truth in best3((b,), model.ctx1[b])
            else:
                right += truth == rows.most_frequent
    return {"positions": positions, "unguarded_right": right,
            "unguarded": _ratio(right, positions), "guarded": guarded,
            "candidate_covered": covered, "candidate_hits": hits}


def guard_score(table: Mapping[str, Any], guard: Tuple[int, Fraction]) -> Dict[str, Any]:
    """Precision and coverage of one guard on a position table."""
    c, s = guard
    answered = right = 0
    for (total, top, ok), n in table["guarded"].items():
        if total >= c and top * s.denominator > s.numerator * total:
            answered += n
            right += n * ok
    return {"answered": answered, "right": right,
            "precision": _ratio(right, answered),
            "coverage": _ratio(answered, table["positions"])}


def choose(table: Mapping[str, Any], bar: Fraction) -> Optional[Tuple[int, Fraction]]:
    """The guard of greatest coverage whose precision is at least ``bar``;
    ties to the higher precision, then the smaller ``c``, then the smaller
    ``s``.  ``None`` when no guard of the grid meets the bar."""
    best = None
    best_key = None
    for g in GUARDS:
        sc = guard_score(table, g)
        if sc["answered"] == 0 or sc["precision"] < bar:
            continue
        key = (-sc["coverage"], -sc["precision"], g[0], g[1])
        if best_key is None or key < best_key:
            best, best_key = g, key
    return best


# ---------------------------------------------------------------------------
#  The definitions' quality
# ---------------------------------------------------------------------------

def quality(answer: Mapping[str, Any]) -> Dict[str, Any]:
    """The quality description of a ``define`` answer (§3): witness and
    address, pattern and strength, source, context support, and the grade."""
    from . import answer as ans
    if not answer.get("ok"):
        return {"described": False}
    strength = int(answer["answers"][0]["strength"])
    support = int(answer["support"])
    return {"described": True, "witness": answer.get("text", ""),
            "address": answer["address"], "pattern": answer["pattern"],
            "strength": strength, "source": answer["source"],
            "support": support, "grade": ans.grade_of(strength, support)}


def _definitions(knowledge: mdl.Knowledge) -> Dict[str, Any]:
    from . import answer as ans
    from . import glossary as gl
    held = gl.hold_out(knowledge)
    out = {"terms": len(gl.GLOSSARY), "answered": 0, "described": 0,
           "strong": 0, "strong_agree": 0, "weak": 0, "weak_agree": 0, "rows": []}
    fields = ("address", "pattern", "strength", "source", "support", "grade")
    for term, gloss in gl.GLOSSARY:
        got = ans.define(term, held, ranking="context")
        if not got.get("ok"):
            out["rows"].append({"term": term, "refusal": got.get("refusal", "")})
            continue
        out["answered"] += 1
        q = quality(got)
        if q.get("described") and all(f in q for f in fields):
            out["described"] += 1
        run = ans.tokens_of(term)
        first = held.sentences[got["answers"][0]["sid"]].tokens
        agree = gl.agrees(first, ans.tokens_of(gloss), run)
        out[q["grade"]] += 1
        out[q["grade"] + "_agree"] += agree
        out["rows"].append({"term": term, "grade": q["grade"], "agrees": agree,
                            "address": q["address"], "pattern": q["pattern"],
                            "strength": q["strength"], "support": q["support"]})
    return out


# ---------------------------------------------------------------------------
#  The measurement
# ---------------------------------------------------------------------------

def compute(knowledge: Any = None) -> Dict[str, object]:
    """Take the Phase 168 measurement from the corpus as it now is."""
    from . import study as cks
    knowledge = mdl.load() if knowledge is None else knowledge
    docs = sorted(knowledge.documents, key=lambda d: d.path)
    folds = {d.path: fold_of(d.path) for d in docs}
    sizes = [sum(1 for d in docs if folds[d.path] == f) for f in range(FOLDS)]
    cal_train = [d for d in docs if folds[d.path] < CALIBRATION_FOLD]
    held_train = [d for d in docs if folds[d.path] < HELD_FOLD]

    def novel(fold: int, train: Sequence[rd.Document]) -> List[Tuple[str, ...]]:
        known = {s.tokens for d in train for s in d.sentences}
        return [t for t in cks.distinct_sentences(d for d in docs if folds[d.path] == fold)
                if t not in known]

    cal_sents = novel(CALIBRATION_FOLD, cal_train)
    held_sents = novel(HELD_FOLD, held_train)
    cal_model = mdl.train(cal_train, with_window=False)
    held_model = mdl.train(held_train, with_window=False)
    sorted_model = mdl.train(held_train, transform=mdl.sorted_tokens, with_window=False)
    cal = position_table(cal_model, cal_sents)
    held = position_table(held_model, held_sents)
    ctrl = position_table(sorted_model, held_sents)
    u = cal["unguarded"]
    modes: Dict[str, Any] = {}
    for name, factor in (("sure", Fraction(3)), ("balanced", Fraction(3, 2))):
        g = choose(cal, factor * u)
        if g is None:
            modes[name] = {"chosen": False, "bar": factor * u}
            continue
        modes[name] = {"chosen": True, "guard": (g[0], g[1]), "bar": factor * u,
                       "calibration": guard_score(cal, g),
                       "held": guard_score(held, g),
                       "control": guard_score(ctrl, g)}
    candidate = {
        "calibration": {"hit_rate": _ratio(cal["candidate_hits"], cal["candidate_covered"]),
                        "coverage": _ratio(cal["candidate_covered"], cal["positions"])},
        "held": {"hit_rate": _ratio(held["candidate_hits"], held["candidate_covered"]),
                 "coverage": _ratio(held["candidate_covered"], held["positions"])},
    }
    definitions = _definitions(knowledge)
    hu = held["unguarded"]
    sure, bal = modes["sure"], modes["balanced"]
    five = Fraction(5, 100)

    def transfers(m: Mapping[str, Any]) -> bool:
        if not m.get("chosen"):
            return False
        c, h = m["calibration"], m["held"]
        return (abs(h["precision"] - c["precision"]) <= five
                and abs(h["coverage"] - c["coverage"]) <= five)

    both = sure.get("chosen") and bal.get("chosen")
    marks = {
        "C1": transfers(sure) and transfers(bal),
        "C2": bool(bal.get("chosen")) and bal["held"]["precision"] >= Fraction(3, 2) * hu
              and bal["held"]["coverage"] >= Fraction(1, 5),
        "C3": bool(sure.get("chosen")) and sure["held"]["precision"] >= 3 * hu,
        "C4": candidate["held"]["hit_rate"] >= hu + Fraction(1, 10)
              and candidate["held"]["coverage"] >= Fraction(4, 5),
        "C5": bool(both) and sure["held"]["precision"] > bal["held"]["precision"] > hu
              and sure["held"]["coverage"] < bal["held"]["coverage"]
              < candidate["held"]["coverage"],
        "C6": bool(bal.get("chosen"))
              and bal["control"]["precision"] <= bal["held"]["precision"] - Fraction(1, 10),
        "D1": definitions["described"] == definitions["answered"] > 0,
        "D2": definitions["strong"] >= 3 and definitions["weak"] >= 3
              and _ratio(definitions["strong_agree"], definitions["strong"])
              > _ratio(definitions["weak_agree"], definitions["weak"]),
    }
    return {
        "folds": {"sizes": sizes, "documents": len(docs)},
        "calibration": {"positions": cal["positions"], "unguarded": cal["unguarded"],
                        "unguarded_right": cal["unguarded_right"]},
        "held": {"positions": held["positions"], "unguarded": held["unguarded"],
                 "unguarded_right": held["unguarded_right"]},
        "control": {"positions": ctrl["positions"], "unguarded": ctrl["unguarded"]},
        "phase154_guards": {"(2, 0)": guard_score(held, (2, Fraction(0))),
                            "(3, 1/2)": guard_score(held, (3, Fraction(1, 2)))},
        "modes": modes,
        "candidate": candidate,
        "definitions": definitions,
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
    }


# ---------------------------------------------------------------------------
#  The stored measurement (written only by ``tools confidence-curve --write``)
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


def confidence_curve_report() -> Dict[str, object]:
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
        "reason": (f"the stored measurement is {verdict}; re-take it with "
                   f"python3 -m glm_universal.tools confidence-curve --write"),
    }

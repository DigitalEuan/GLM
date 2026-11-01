"""``glm_universal.knowledge.friction_study`` -- Phase 156's marks and stored
measurements.

``studies/FRICTION_STUDY.md``: the survey of the evaluation's cases under
seven declared perturbations (F1-F4; amended F1′, F4′ with refusals read as
refusals), contact over the whole prompt (C1-C4; amended C1′ the tie-break,
C2′, C3′ the loaded score) and the stick-slip reading (S1-S4 over the top
folders; amended S1′-S4′ over the directories), and the four fix marks
(X1-X4) read from the settled survey and the frozen-path comparison when
they are stored.

* :func:`compute` takes the corpus measurement (the held-out sample of
  :mod:`glm_universal.knowledge.friction`, a few minutes) and reads the
  stored survey (``_data/friction_survey.json``, taken by
  :func:`write_survey`, ~25 minutes of ``GLM.py`` runs);
* :func:`write_measurements` stores the corpus measurement in
  ``_data/friction.json`` beside the digest of the code that took it;
* :func:`friction_report` reads both and derives every mark from the stored
  figures (a mark whose figures are not stored is reported missed, with the
  reason in ``unmeasured``).

Exact throughout (D7): every figure is an ``int``; every percentage bar is
compared by cross-multiplication.

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/FRICTION_STUDY.md
(§§2.1-2.5, §7), the CLI handler ``_friction`` in glm_universal/tools.py and
the friction modules it reads.*
"""
from __future__ import annotations

import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import integrity

__all__ = [
    "DATA_PATH", "SURVEY_PATH", "SETTLED_PATH", "FROZEN_PATH", "_SOURCES",
    "MARKS", "AMENDED", "FIXES", "MARGINS", "contact_measure",
    "continuation_measure", "stickslip_measure", "corpus_measure",
    "survey_marks", "corpus_marks", "fix_marks", "compute", "measure",
    "write_measurements", "write_survey", "measurements", "survey_stored",
    "state", "current", "module_digest", "friction_report",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "friction.json"
SURVEY_PATH = _HERE / "_data" / "friction_survey.json"
#: §2.5: the survey taken again after the fix, and the frozen-path comparison.
SETTLED_PATH = _HERE / "_data" / "friction_survey_settled.json"
FROZEN_PATH = _HERE / "_data" / "friction_frozen_path.json"

_SOURCES: Tuple[str, ...] = (
    "knowledge/friction_study.py",
    "knowledge/friction.py",
    "knowledge/friction_survey.py",
    "knowledge/model.py",
    "knowledge/reader.py",
)

MARKS: Tuple[str, ...] = ("F1", "F2", "F3", "F4", "C1", "C2", "C3", "C4",
                          "S1", "S2", "S3", "S4")
AMENDED: Tuple[str, ...] = ("F1′", "F4′", "C1′", "C2′", "C3′",
                            "S1′", "S2′", "S3′", "S4′")
FIXES: Tuple[str, ...] = ("X1", "X2", "X3", "X4")
#: The sticking reader's margins: the quarter reads the marks, an eighth and
#: a half are the curve beside it.
MARGINS: Tuple[Tuple[str, Fraction], ...] = (
    ("stick 1/8", Fraction(1, 8)), ("stick 1/4", Fraction(1, 4)),
    ("stick 1/2", Fraction(1, 2)))

_cache: Optional[Dict[str, object]] = None


def _plain(x: Any) -> Any:
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


# ===========================================================================
# 1.  THE CORPUS MEASUREMENT
# ===========================================================================

#: The predictors of §2.2 and §2.4, by name.
PREDICTORS: Tuple[str, ...] = ("patch", "contact", "control", "tiebreak",
                               "tiebreak_control", "loaded", "loaded_control")


def contact_measure(model, held: Sequence[Any]) -> Dict[str, Any]:
    """§2.2/§2.4: every predictor at every position of every held-out
    sentence; the mismatched controls take the prompt words from the next
    sampled sentence (the last from the first), cut to the same number of
    tokens."""
    from . import friction as fr
    n = len(held)
    correct = Counter()
    answered = Counter()
    wins = Counter()
    losses = Counter()
    positions = 0
    for i, s in enumerate(held):
        toks = s.tokens
        nxt = held[(i + 1) % n].tokens if n else ()

        def mismatched(j: int, _nxt=nxt) -> Tuple[str, ...]:
            return _nxt[:j]

        got = {
            "patch": fr.predict_positions(fr.patch_predict, model, toks),
            "contact": fr.predict_positions(fr.contact_predict, model, toks),
            "control": fr.predict_positions(fr.contact_predict, model, toks,
                                            mismatched),
            "tiebreak": fr.predict_positions(fr.tiebreak_predict, model, toks),
            "tiebreak_control": fr.predict_positions(fr.tiebreak_predict,
                                                     model, toks, mismatched),
            "loaded": fr.predict_positions(fr.loaded_predict, model, toks),
            "loaded_control": fr.predict_positions(fr.loaded_predict, model,
                                                   toks, mismatched),
        }
        positions += got["patch"]["positions"]
        for name, r in got.items():
            correct[name] += r["correct"]
            answered[name] += r["answered"]
            if name != "patch":
                if r["correct"] > got["patch"]["correct"]:
                    wins[name] += 1
                elif r["correct"] < got["patch"]["correct"]:
                    losses[name] += 1
    return {
        "sentences": n, "positions": positions,
        "correct": {p: correct[p] for p in PREDICTORS},
        "answered": {p: answered[p] for p in PREDICTORS},
        "wins": {p: wins[p] for p in PREDICTORS if p != "patch"},
        "losses": {p: losses[p] for p in PREDICTORS if p != "patch"},
    }


def continuation_measure(model, held: Sequence[Any],
                         predictors: Optional[Dict[str, Any]] = None
                         ) -> Dict[str, Any]:
    """§2.2's continuation: the first 3 tokens of each held-out sentence
    continued under each predictor for at most 12 tokens; summed overlap
    with tokens 3..14, distinct and most frequent non-empty continuations,
    the stops."""
    from . import friction as fr
    predictors = predictors or {"patch": fr.patch_predict,
                                "contact": fr.contact_predict,
                                "loaded": fr.loaded_predict}
    texts: Dict[str, Counter] = {k: Counter() for k in predictors}
    over = Counter()
    stops: Dict[str, Counter] = {k: Counter() for k in predictors}
    for s in held:
        toks = s.tokens
        prompt, truth = toks[:fr.PROMPT], toks[fr.PROMPT:fr.PROMPT + fr.MAX_TOKENS]
        for name, pred in predictors.items():
            c = fr.continuation(pred, model, prompt)
            texts[name][c["text"]] += 1
            over[name] += fr.overlap(c["tokens"], truth)
            stops[name][c["stop"]] += 1
    return _continuation_summary(texts, over, stops)


def _continuation_summary(texts: Dict[str, Counter], over: Counter,
                          stops: Dict[str, Counter]) -> Dict[str, Any]:
    most: Dict[str, List[Any]] = {}
    for name, tc in texts.items():
        nonempty = sorted(((n, t) for t, n in tc.items() if t),
                          key=lambda nt: (-nt[0], nt[1]))
        most[name] = [nonempty[0][1], nonempty[0][0]] if nonempty else ["", 0]
    return {
        "most_frequent": most,
        "overlap": {k: over[k] for k in texts},
        "distinct": {k: sum(1 for t in tc if t) for k, tc in texts.items()},
        "stops": {k: dict(sorted(v.items())) for k, v in stops.items()},
    }


def stickslip_measure(evidence, held: Sequence[Any]) -> Dict[str, Any]:
    """§2.3 at one scale: the frictionless reader and the sticking reader at
    each margin; switches, returns and final readings over the sentences
    read, and the sentences on which a sticking reader switched more than
    the frictionless one (S1 checks the quarter; it is proved it cannot)."""
    from . import friction as fr
    names = ["frictionless"] + [n for n, _m in MARGINS]
    totals = {n: Counter() for n in names}
    violations = {n: 0 for n, _m in MARGINS}
    read = 0
    for s in held:
        lead = fr.leaders(evidence, s)
        if not lead["steps"]:
            continue
        read += 1
        truth = lead["truth"]
        base = fr.reading_stats(lead["leaders"], truth)
        totals["frictionless"].update(base)
        for name, m in MARGINS:
            st = fr.reading_stats(fr.margin_reader(lead["steps"], m), truth)
            totals[name].update(st)
            if st["switches"] > base["switches"]:
                violations[name] += 1
    return {
        "scale": evidence.scale, "folders": evidence.size,
        "sentences": len(held), "read": read,
        "readers": {n: {k: totals[n][k] for k in
                        ("switches", "returns", "final_correct", "into_truth")}
                    for n in names},
        "violations": violations,
    }


def corpus_measure(knowledge=None) -> Dict[str, Any]:
    """The corpus half of Phase 156 (§§2.2-2.4) on the corpus as it now is."""
    from . import friction as fr
    from . import model as mdl
    knowledge = mdl.load() if knowledge is None else knowledge
    held = fr.sample(knowledge)
    model = fr.hold_out_model(knowledge, held)
    contact = contact_measure(model, held)
    contact["continuation"] = continuation_measure(model, held)
    return {
        "corpus": {"documents": len(knowledge.documents),
                   "sentences": len(knowledge.sentences),
                   "digest": knowledge.digest},
        "contact": contact,
        "stickslip": stickslip_measure(fr.FolderEvidence(knowledge, "top"),
                                       held),
        "directory": stickslip_measure(
            fr.FolderEvidence(knowledge, "directory"), held),
    }


# ===========================================================================
# 2.  THE MARKS, FROM THE STORED FIGURES
# ===========================================================================

def _at_most(part: int, whole: int, percent: int) -> bool:
    """``part <= percent% of whole``, in integers."""
    return part * 100 <= whole * percent


def _at_least(part: int, whole: int, percent: int) -> bool:
    return whole > 0 and part * 100 >= whole * percent


def survey_marks(sv: Optional[Dict[str, Any]]) -> Dict[str, bool]:
    """F1-F4 and F1′, F4′ from a stored survey (all missed without one)."""
    if not sv or not sv.get("by_perturbation"):
        return {m: False for m in ("F1", "F2", "F3", "F4", "F1′", "F4′")}
    from .friction_survey import SURFACE, LEXICAL
    bp, rs = sv["by_perturbation"], sv.get("rescored", sv["by_perturbation"])
    runs = sum(t["runs"] for t in bp.values())
    surface_runs = sum(bp[p]["runs"] for p in SURFACE)
    lexical_runs = sum(bp[p]["runs"] for p in LEXICAL)
    return {
        "F1": _at_most(sv["refusal_slips"], sv["refusal_runs"], 1),
        "F2": _at_least(sum(bp[p]["hold"] for p in SURFACE), surface_runs, 90),
        "F3": _at_least(sum(bp[p]["hold"] for p in LEXICAL), lexical_runs, 50),
        "F4": _at_most(sum(t["slip"] for t in bp.values()), runs, 2),
        "F1′": _at_most(sv["refusal_slips_rescored"], sv["refusal_runs"], 1),
        "F4′": _at_most(sum(t["slip"] for t in rs.values()), runs, 2),
    }


def _gain(co: Dict[str, Any], name: str) -> int:
    return co["correct"][name] - co["correct"]["patch"]


def _precision_at_least(co: Dict[str, Any], name: str) -> bool:
    c, a = co["correct"], co["answered"]
    return c[name] * a["patch"] >= c["patch"] * a[name]


def _stick_marks(st: Dict[str, Any]) -> Tuple[bool, bool, bool, bool]:
    fr_, sk = st["readers"]["frictionless"], st["readers"]["stick 1/4"]
    s1 = st["violations"]["stick 1/4"] == 0
    s2 = sk["switches"] * 10 <= fr_["switches"] * 7
    s3 = sk["final_correct"] * 100 >= fr_["final_correct"] * 100 - st["read"]
    s4 = sk["returns"] * 2 <= fr_["returns"]
    return s1, s2, s3, s4


def corpus_marks(corpus: Optional[Dict[str, Any]]) -> Dict[str, bool]:
    """C1-C4, S1-S4 and C1′-C3′, S1′-S4′ from the stored corpus figures."""
    names = ("C1", "C2", "C3", "C4", "S1", "S2", "S3", "S4",
             "C1′", "C2′", "C3′", "S1′", "S2′", "S3′", "S4′")
    if not corpus:
        return {m: False for m in names}
    co = corpus["contact"]
    cont = co["continuation"]
    g, gc = _gain(co, "contact"), _gain(co, "control")
    gt, gtc = _gain(co, "tiebreak"), _gain(co, "tiebreak_control")
    out = {
        "C1": g > 0 and co["wins"]["contact"] > co["losses"]["contact"],
        "C2": g > 0 and (gc <= 0 or g >= 2 * gc),
        "C3": _precision_at_least(co, "contact"),
        "C4": (cont["overlap"]["contact"] > cont["overlap"]["patch"]
               and cont["distinct"]["contact"] * 4
               >= cont["distinct"]["patch"] * 5),
        "C1′": gt > 0 and gt >= 2 * gtc,
        "C2′": (_gain(co, "loaded") > 0
                and co["wins"]["loaded"] > co["losses"]["loaded"]),
        "C3′": _precision_at_least(co, "loaded"),
    }
    out["S1"], out["S2"], out["S3"], out["S4"] = _stick_marks(corpus["stickslip"])
    out["S1′"], out["S2′"], out["S3′"], out["S4′"] = _stick_marks(
        corpus["directory"])
    return {m: bool(out[m]) for m in names}


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def fix_marks(survey: Optional[Dict[str, Any]],
              settled: Optional[Dict[str, Any]],
              frozen: Optional[Dict[str, Any]]) -> Dict[str, bool]:
    """X1-X4 (§2.5): the frozen path, and the settled survey against the
    survey before the edit; missed when either is not stored."""
    x1 = bool(frozen and frozen.get("cases") and not frozen.get("differ"))
    if not survey or not settled:
        return {"X1": x1, "X2": False, "X3": False, "X4": False}
    before = survey.get("rescored", survey["by_perturbation"])
    after = settled.get("rescored", settled["by_perturbation"])
    sp, tm = after["spaces"], after["tellme"]
    x4 = all(after[p]["slip"] <= before[p]["slip"]
             and after[p]["hold"] >= before[p]["hold"] for p in after)
    return {"X1": x1,
            "X2": _at_least(sp["hold"], sp["runs"], 98),
            "X3": _at_least(tm["hold"], tm["runs"], 90) and tm["slip"] == 0,
            "X4": x4}


# ===========================================================================
# 3.  THE STANDARD APPARATUS
# ===========================================================================

def survey_stored() -> Optional[Dict[str, Any]]:
    """The stored survey (``_data/friction_survey.json``), or ``None``."""
    return _read_json(SURVEY_PATH)


def _survey_summary(sv: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not sv:
        return {"cases": 0, "base_passing": 0, "by_perturbation": {},
                "available": False}
    out = {k: v for k, v in sv.items() if k != "runs"}
    out["available"] = True
    return out


def _assemble(corpus: Optional[Dict[str, Any]],
              sv: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    survey = survey_marks(sv)
    cm = corpus_marks(corpus)
    fixes = fix_marks(sv, _read_json(SETTLED_PATH), _read_json(FROZEN_PATH))
    marks = {m: survey.get(m, cm.get(m, False)) for m in MARKS}
    amended = {m: survey.get(m, cm.get(m, False)) for m in AMENDED}
    unmeasured: List[str] = []
    if not sv:
        unmeasured.append("F1-F4, F1′, F4′: the survey is not stored "
                          "(python3 -m glm_universal.tools friction --survey "
                          "--write)")
    if not (_read_json(SETTLED_PATH) and _read_json(FROZEN_PATH)):
        unmeasured.append("X1-X4: the settled survey and the frozen-path "
                          "comparison are not stored")
    return {
        "survey": _survey_summary(sv),
        "corpus": corpus or {},
        "marks": marks, "met": sum(marks.values()), "taken": len(marks),
        "amended": amended, "amended_met": sum(amended.values()),
        "amended_taken": len(amended),
        "fixes": fixes, "fixes_met": sum(fixes.values()),
        "fixes_taken": len(fixes),
        "unmeasured": unmeasured,
    }


def compute(knowledge: Any = None) -> Dict[str, object]:
    """Take the corpus measurement and read the stored survey; every mark."""
    return _assemble(corpus_measure(knowledge), survey_stored())


def module_digest() -> str:
    root = _HERE.parent  # glm_universal/
    paths = [root / n for n in sorted(set(_SOURCES))]
    return integrity.tree_digest(paths, root)


def measure() -> Dict[str, object]:
    """The corpus measurement beside the digest of the code that took it."""
    r: Dict[str, object] = {"corpus": corpus_measure()}
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


def write_survey(jobs: int = 8, path: Optional[Path] = None) -> Path:
    """Run the survey (§2.1, with the §2.4 re-scoring) and store it beside the
    digest of the code that took it (~25 minutes on eight jobs)."""
    from . import friction_survey as fsv
    out = path if path is not None else SURVEY_PATH
    data = fsv.survey(jobs=jobs)
    data["source_digest"] = module_digest()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_plain(data), indent=1, sort_keys=True,
                              ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    global _cache
    if _cache is not None and not refresh:
        return _cache
    _cache = _read_json(DATA_PATH)
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


def friction_report() -> Dict[str, object]:
    """Every mark, derived from the stored measurement and the stored survey;
    ``available=False`` with the re-take instruction when the corpus
    measurement is absent or stale."""
    stored = current()
    if stored is not None:
        out = _assemble(stored.get("corpus"), survey_stored())
        out["available"] = True
        out["source_digest"] = stored.get("source_digest")
        return out
    st = state()
    what = "absent" if not st["present"] else "stale (the code moved)"
    return {
        "available": False,
        "reasons": [f"the stored measurement is {what}; re-take it with "
                    f"python3 -m glm_universal.tools friction --write"],
    }

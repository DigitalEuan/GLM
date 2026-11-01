"""``glm_universal.knowledge.friction_two_study`` -- Phase 157's friction marks
and stored measurements.

``studies/FRICTION_TWO_STUDY.md``: the did-you-mean respelling read offline on
the typo questions (T1, T2; amended T1′, T2′ on the short-word perturbation;
shipped T1″, T2″ for ``loaded``), the survey after the round (T3, T5, H1),
the frozen path (T4, H2), worn contact (W1-W3) and the noise-set margin
(N1-N4).

* :func:`compute` takes the offline respelling (the vocabulary table of
  :mod:`glm_universal.runtime.respell`), the corpus measurements (wear and
  the margin, over Phase 156's held-out sample) and reads the stored survey
  (``_data/friction_two_survey.json``, :func:`write_survey`) and frozen-path
  comparison (``_data/friction_two_frozen.json``);
* :func:`friction_two_report` derives every mark from the stored figures; a
  mark whose figures are not stored is missed, with the reason in
  ``unmeasured``.

The typo questions are the evaluation questions the survey's ``typo``
perturbation applies to, each paired with its unperturbed original (the
truth): a respelling **restores** it when it gives the original back,
leaves it **unchanged** when it gives the perturbed text back, and turns it
into a **different** question otherwise.

Exact (D7): every figure is an ``int``; percentage bars by
cross-multiplication.

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/FRICTION_TWO_STUDY.md
(§§2.1-2.6, §7), the CLI handler ``_friction_two`` in glm_universal/tools.py,
runtime/respell.py and the friction modules.  The frozen-path rule "except
for lines whose difference is traced to the corpus the answer reads" is read
here as: a differing answer line is allowed only for a case of the evaluation
kind ``corpus``.*
"""
from __future__ import annotations

import json
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .. import integrity

__all__ = [
    "DATA_PATH", "SURVEY_PATH", "FROZEN_PATH", "_SOURCES", "MARKS", "AMENDED",
    "SHIPPED", "typo_pairs", "short_word_pairs", "respell_tally",
    "respell_measure", "wear_measure", "noise_measure", "corpus_measure",
    "frozen_compare", "compute", "measure", "write_measurements",
    "write_survey", "measurements", "state", "current", "module_digest",
    "friction_two_report",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "friction_two.json"
SURVEY_PATH = _HERE / "_data" / "friction_two_survey.json"
FROZEN_PATH = _HERE / "_data" / "friction_two_frozen.json"

_SOURCES: Tuple[str, ...] = (
    "knowledge/friction_two_study.py",
    "knowledge/friction_two.py",
    "knowledge/friction.py",
    "knowledge/friction_survey.py",
    "knowledge/model.py",
    "knowledge/reader.py",
    "runtime/respell.py",
)

MARKS: Tuple[str, ...] = ("T1", "T2", "T3", "T4", "T5", "H1", "H2",
                          "W1", "W2", "W3", "N1", "N2", "N3", "N4")
AMENDED: Tuple[str, ...] = ("T1′", "T2′")
SHIPPED: Tuple[str, ...] = ("T1″", "T2″")

#: The respelling's readings on the typo questions: the first measurement
#: (§2.1, ``amended=False``) under each mode, and the amended readings.
TYPO_READINGS: Tuple[Tuple[str, str, bool], ...] = (
    ("first_use", "use", False), ("first_spelling", "spelling", False),
    ("first_mismatched", "mismatched", False),
    ("use", "use", True), ("spelling", "spelling", True),
    ("mismatched", "mismatched", True), ("loaded", "loaded", True),
)
SHORT_READINGS: Tuple[str, ...] = ("use", "spelling", "mismatched", "loaded")

_cache: Optional[Dict[str, object]] = None


def _plain(x: Any) -> Any:
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# ===========================================================================
# 1.  THE DID-YOU-MEAN, OFFLINE
# ===========================================================================

def typo_pairs(questions: Optional[Sequence[str]] = None
               ) -> List[Tuple[str, str]]:
    """``(original, perturbed)`` for every evaluation question the survey's
    typo applies to (§2.1's 196)."""
    from . import friction_survey as fsv
    if questions is None:
        from ..evaluation.cases import CASES
        questions = [c.question for c in CASES]
    out = []
    for q in questions:
        moved = fsv._typo(q)
        if moved is not None:
            out.append((q, moved))
    return out


_LETTERS = re.compile(r"[A-Za-z]+")


def short_word_pairs(questions: Optional[Sequence[str]] = None, tbl=None
                     ) -> List[Tuple[str, str, str]]:
    """§2.5's T2′ perturbation: for every alphabetic word of 4 to 6 letters of
    every evaluation question, its second and third letters swapped, one
    moved question per word whose swap changes it and leaves it unknown:
    ``(original, moved, moved word)``."""
    from ..runtime import respell as rs
    tbl = rs.table() if tbl is None else tbl
    if questions is None:
        from ..evaluation.cases import CASES
        questions = [c.question for c in CASES]
    out = []
    for q in questions:
        for m in _LETTERS.finditer(q):
            w = m.group(0)
            if not 4 <= len(w) <= 6:
                continue
            moved = w[0] + w[2] + w[1] + w[3:]
            if moved == w or rs.known(moved, tbl):
                continue
            out.append((q, q[:m.start()] + moved + q[m.end():], moved))
    return out


def _grade(original: str, moved: str, got: str) -> str:
    if got == original:
        return "restored"
    if got == moved:
        return "unchanged"
    return "different"


def _company(text: str, tbl) -> List[str]:
    from ..runtime import respell as rs
    return [t.lower() for t in rs.tokens(text) if rs.known(t, tbl)]


def respell_tally(pairs: Sequence[Tuple[str, str]], mode: str,
                  amended: bool = True, tbl=None, reader=None
                  ) -> Dict[str, Any]:
    """Restored / different / unchanged over ``(original, moved)`` pairs under
    one reading; ``mismatched`` takes the company from the next pair's moved
    question (the last from the first).  ``reader(text, company)`` replaces
    the respelling (the sintered reading passes its own)."""
    from ..runtime import respell as rs
    tbl = rs.table() if tbl is None else tbl
    t = Counter()
    examples: List[List[str]] = []
    n = len(pairs)
    for i, (original, moved) in enumerate(pairs):
        company = None
        if mode == "mismatched":
            company = _company(pairs[(i + 1) % n][1], tbl)
        if reader is not None:
            got = reader(moved, company).text
        else:
            got = rs.respell(moved, mode=mode, company=company, tbl=tbl,
                             amended=amended).text
        g = _grade(original, moved, got)
        t[g] += 1
        if g == "different" and len(examples) < 20:
            examples.append([moved, got, original])
    return {"restored": t["restored"], "different": t["different"],
            "unchanged": t["unchanged"], "different_examples": examples}


def respell_measure(tbl=None) -> Dict[str, Any]:
    """§2.1, §2.5 and §2.6 offline: the typo questions under every reading,
    and the short-word perturbation under the amended readings."""
    from ..runtime import respell as rs
    tbl = rs.table() if tbl is None else tbl
    pairs = typo_pairs()
    shorts = short_word_pairs(tbl=tbl)
    short_pairs = [(o, m) for o, m, _w in shorts]
    ambiguous = sum(1 for _o, _m, w in shorts if len(rs.candidates(w, tbl)) > 1)
    return {
        "respell": {"questions": len(pairs),
                    "tally": {name: respell_tally(pairs, mode, amended, tbl)
                              for name, mode, amended in TYPO_READINGS}},
        "short_words": {"moved": len(short_pairs), "ambiguous": ambiguous,
                        "tally": {mode: respell_tally(short_pairs, mode, True,
                                                      tbl)
                                  for mode in SHORT_READINGS}},
        "table": {"present": tbl.present, "words": len(tbl.documents)},
    }


# ===========================================================================
# 2.  WEAR AND THE MARGIN
# ===========================================================================

def wear_measure(model, held: Sequence[Any]) -> Dict[str, Any]:
    """§2.3: the continuation under the patch, contact, worn contact, the
    loaded score and the loaded score worn, on Phase 156's prompts."""
    from . import friction as fr
    from . import friction_two as f2
    from .friction_study import _continuation_summary
    names = ("patch", "contact", "worn", "loaded", "loaded_worn")
    texts = {k: Counter() for k in names}
    over = Counter()
    stops = {k: Counter() for k in names}
    spent = Counter()
    for s in held:
        toks = s.tokens
        prompt, truth = toks[:fr.PROMPT], toks[fr.PROMPT:fr.PROMPT + fr.MAX_TOKENS]
        got = {
            "patch": fr.continuation(fr.patch_predict, model, prompt),
            "contact": fr.continuation(fr.contact_predict, model, prompt),
            "worn": f2.worn_continuation(model, prompt),
            "loaded": fr.continuation(fr.loaded_predict, model, prompt),
            "loaded_worn": f2.worn_continuation(model, prompt, load=fr.LOAD),
        }
        for name, c in got.items():
            texts[name][c["text"]] += 1
            over[name] += fr.overlap(c["tokens"], truth)
            stops[name][c["stop"]] += 1
            spent[name] += c["state"].get("touches", 0)
    out = _continuation_summary(texts, over, stops)
    out["touches_spent"] = {"worn": spent["worn"],
                            "loaded_worn": spent["loaded_worn"]}
    return out


def noise_measure(evidence, held: Sequence[Any]) -> Dict[str, Any]:
    """§2.4 on the directory reader: the frictionless reader, the fixed
    quarter of Phase 156 and the noise-set reader at ``r/16``, ``r/8`` (the
    marks) and ``r/4``; N1 counts the sentences on which ``r/8`` switched
    more than the leader."""
    from . import friction as fr
    from . import friction_two as f2
    readers = {"frictionless": lambda st: [l for _s, l in st],
               "stick 1/4": lambda st: fr.margin_reader(st, Fraction(1, 4))}
    for q in f2.NOISE_CURVE:
        readers[f"noise r/{q}"] = (lambda st, q=q: f2.noise_reader(st, q))
    totals = {n: Counter() for n in readers}
    violations = 0
    read = 0
    for s in held:
        lead = fr.leaders(evidence, s)
        if not lead["steps"]:
            continue
        read += 1
        got = {n: fr.reading_stats(r(lead["steps"]), lead["truth"])
               for n, r in readers.items()}
        for n, st in got.items():
            totals[n].update(st)
        if got[f"noise r/{f2.NOISE_SCALE}"]["switches"] > \
                got["frictionless"]["switches"]:
            violations += 1
    return {"scale": evidence.scale, "folders": evidence.size, "read": read,
            "readers": {n: {k: totals[n][k] for k in
                            ("switches", "returns", "final_correct",
                             "into_truth")} for n in readers},
            "violations": violations}


def corpus_measure(knowledge=None) -> Dict[str, Any]:
    """The offline respelling, wear and the margin, on the corpus as it is."""
    from . import friction as fr
    from . import model as mdl
    knowledge = mdl.load() if knowledge is None else knowledge
    held = fr.sample(knowledge)
    model = fr.hold_out_model(knowledge, held)
    out = respell_measure()
    out["corpus"] = {"documents": len(knowledge.documents),
                     "sentences": len(knowledge.sentences),
                     "digest": knowledge.digest}
    out["wear"] = wear_measure(model, held)
    out["noise"] = noise_measure(fr.FolderEvidence(knowledge, "directory"),
                                 held)
    return out


# ===========================================================================
# 3.  THE FROZEN PATH
# ===========================================================================

def frozen_compare(before: Mapping[str, Any], after: Mapping[str, Any],
                   corpus_kinds: Sequence[str] = ("corpus",)) -> Dict[str, Any]:
    """Two evaluation reports (``harness.evaluation_report``) compared case
    by case: passes before and after, the cases whose outcome differs, and
    the answer lines that differ (allowed only for cases of a corpus kind,
    whose answers read the corpus, which is the project's own text)."""
    b = {r["id"]: r for r in before.get("results", [])}
    a = {r["id"]: r for r in after.get("results", [])}
    common = [i for i in b if i in a]
    outcomes = [i for i in common if b[i]["outcome"] != a[i]["outcome"]]
    lines = [i for i in common if b[i]["outcome"] == a[i]["outcome"]
             and b[i].get("answer") != a[i].get("answer")]
    untraced = [i for i in lines if b[i].get("kind") not in corpus_kinds]
    return {
        "cases": len(common),
        "only_before": sorted(set(b) - set(a)),
        "only_after": sorted(set(a) - set(b)),
        "passed_before": sum(1 for i in common
                             if b[i]["outcome"] in ("correct",
                                                    "refused_as_expected")),
        "passed_after": sum(1 for i in common
                            if a[i]["outcome"] in ("correct",
                                                   "refused_as_expected")),
        "outcomes_differ": len(outcomes), "outcome_ids": outcomes,
        "lines_differ": [{"id": i, "before": b[i].get("answer"),
                          "after": a[i].get("answer"),
                          "kind": b[i].get("kind")} for i in lines],
        "lines_untraced": untraced,
    }


def _frozen_holds(fz: Optional[Mapping[str, Any]]) -> bool:
    return bool(fz and fz.get("cases") and fz.get("outcomes_differ") == 0
                and not fz.get("lines_untraced"))


# ===========================================================================
# 4.  THE MARKS, FROM THE STORED FIGURES
# ===========================================================================

def _restore_mark(t: Mapping[str, int], questions: int) -> bool:
    return (questions > 0 and t["restored"] * 100 >= questions * 85
            and t["different"] * 100 <= questions * 2)


def _marks(data: Optional[Dict[str, Any]], survey: Optional[Dict[str, Any]],
           frozen: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, bool]]:
    from .friction_study import SETTLED_PATH
    m: Dict[str, bool] = {k: False for k in MARKS + AMENDED + SHIPPED}
    if data:
        rs, sw = data["respell"], data["short_words"]
        q, tal, st = rs["questions"], rs["tally"], sw["tally"]
        m["T1"] = _restore_mark(tal["first_use"], q)
        m["T2"] = (tal["first_use"]["restored"] >= tal["first_spelling"]["restored"]
                   and tal["first_use"]["restored"]
                   > tal["first_mismatched"]["restored"])
        m["T1′"] = _restore_mark(tal["use"], q)
        m["T2′"] = (st["use"]["restored"] >= st["spelling"]["restored"]
                    and st["use"]["restored"] > st["mismatched"]["restored"])
        m["T1″"] = _restore_mark(tal["loaded"], q)
        m["T2″"] = (st["loaded"]["restored"] >= st["spelling"]["restored"]
                    and st["loaded"]["restored"] > st["mismatched"]["restored"])
        we, no = data["wear"], data["noise"]
        m["W1"] = (we["most_frequent"]["worn"][1] * 2
                   <= we["most_frequent"]["contact"][1])
        m["W2"] = we["overlap"]["worn"] >= we["overlap"]["contact"]
        m["W3"] = we["distinct"]["worn"] >= we["distinct"]["contact"]
        fr_, nz = no["readers"]["frictionless"], no["readers"]["noise r/8"]
        m["N1"] = no["violations"] == 0
        m["N2"] = nz["final_correct"] * 100 >= fr_["final_correct"] * 100 - no["read"]
        m["N3"] = nz["returns"] * 2 <= fr_["returns"]
        m["N4"] = nz["switches"] * 10 <= fr_["switches"] * 9
    if survey and survey.get("by_perturbation"):
        typo = survey["by_perturbation"]["typo"]
        m["T3"] = typo["hold"] >= 150 and typo["slip"] == 0
        m["H1"] = survey.get("errors", 1) == 0
        settled = _read_json(SETTLED_PATH)
        if settled and settled.get("by_perturbation"):
            sb = settled.get("rescored", settled["by_perturbation"])
            sa = survey["by_perturbation"]
            m["T5"] = all(sa[p]["slip"] <= sb[p]["slip"]
                          and sa[p]["hold"] >= sb[p]["hold"] for p in sa)
    if frozen:
        m["T4"] = _frozen_holds(frozen)
        m["H2"] = bool(frozen.get("cases")
                       and frozen.get("passed_before") == frozen.get("cases")
                       and frozen.get("passed_after") == frozen.get("cases"))
    return {"marks": {k: bool(m[k]) for k in MARKS},
            "amended": {k: bool(m[k]) for k in AMENDED},
            "shipped": {k: bool(m[k]) for k in SHIPPED}}


def _assemble(data: Optional[Dict[str, Any]],
              survey: Optional[Dict[str, Any]],
              frozen: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    got = _marks(data, survey, frozen)
    out: Dict[str, Any] = {"corpus": data or {}}
    if survey:
        out["survey"] = {k: v for k, v in survey.items() if k != "runs"}
    if frozen:
        out["frozen"] = frozen
    unmeasured = []
    if not survey:
        unmeasured.append("T3, T5, H1: the survey after the round is not "
                          "stored (python3 -m glm_universal.tools "
                          "friction-two --survey --write)")
    if not frozen:
        unmeasured.append("T4, H2: the frozen-path comparison "
                          "(_data/friction_two_frozen.json) is not stored")
    out.update(got)
    out["met"] = sum(got["marks"].values())
    out["taken"] = len(got["marks"])
    out["amended_met"] = sum(got["amended"].values())
    out["amended_taken"] = len(got["amended"])
    out["shipped_met"] = sum(got["shipped"].values())
    out["shipped_taken"] = len(got["shipped"])
    out["unmeasured"] = unmeasured
    return out


# ===========================================================================
# 5.  THE STANDARD APPARATUS
# ===========================================================================

def compute(knowledge: Any = None) -> Dict[str, object]:
    """Take the corpus measurement; read the stored survey and frozen path."""
    return _assemble(corpus_measure(knowledge), _read_json(SURVEY_PATH),
                     _read_json(FROZEN_PATH))


def module_digest() -> str:
    root = _HERE.parent  # glm_universal/
    paths = [root / n for n in sorted(set(_SOURCES))]
    return integrity.tree_digest(paths, root)


def measure() -> Dict[str, object]:
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
    """The survey after the round (Phase 156's survey, the harness as it now
    is), stored beside the digest of the code that took it."""
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


def friction_two_report() -> Dict[str, object]:
    """Every mark from the stored figures; ``available=False`` with the
    re-take instruction when the corpus measurement is absent or stale."""
    stored = current()
    if stored is not None:
        out = _assemble(stored.get("corpus"), _read_json(SURVEY_PATH),
                        _read_json(FROZEN_PATH))
        out["available"] = True
        out["source_digest"] = stored.get("source_digest")
        return out
    st = state()
    what = "absent" if not st["present"] else "stale (the code moved)"
    return {
        "available": False,
        "reasons": [f"the stored measurement is {what}; re-take it with "
                    f"python3 -m glm_universal.tools friction-two --write"],
    }

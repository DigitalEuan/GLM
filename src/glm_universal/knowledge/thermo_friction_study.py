"""``glm_universal.knowledge.thermo_friction_study`` -- Phase 159's marks and
stored measurements.

``studies/THERMO_FRICTION_STUDY.md``: the bimetallic governor (A1-A7), the
thermoelectric prompt anchor (B1-B6; amended B6′) and the sintered respelling
of the register vocabulary (C1-C6).  Sintering ships if and only if C1-C4 are
met (§2.3).

* :func:`compute` takes the corpus measurement (experiments A and B over
  Phase 156's held-out sample, experiment C over the respelling table and the
  register lexicon) and reads the stored blind-spot answer
  (``_data/thermo_friction_blind_spot.json``, :func:`write_blind_spot`) and
  the stored frozen-path comparison (``_data/thermo_friction_frozen.json``,
  :func:`write_frozen`);
* :func:`thermo_friction_report` derives every mark from the stored figures;
  a mark whose figures are not stored is missed, with the reason in
  ``unmeasured``.

Exact (D7): every figure is an ``int``; precision comparisons by
cross-multiplication.

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/THERMO_FRICTION_STUDY.md
(§§2.1-2.4, §7), the CLI handler ``_thermo_friction`` in
glm_universal/tools.py, runtime/respell.py, runtime/sinter.py and the
friction modules.*
"""
from __future__ import annotations

import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .. import integrity

__all__ = [
    "DATA_PATH", "BLIND_SPOT_PATH", "FROZEN_PATH", "EVAL_BEFORE_PATH",
    "BLIND_SPOT_QUESTION", "_SOURCES", "MARKS", "AMENDED", "GOVERNORS",
    "governor_measure", "anchor_measure", "recovery_set", "sinter_measure",
    "corpus_measure", "compute", "measure", "write_measurements",
    "write_blind_spot", "write_frozen", "measurements", "state", "current",
    "module_digest", "thermo_friction_report",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "thermo_friction.json"
BLIND_SPOT_PATH = _HERE / "_data" / "thermo_friction_blind_spot.json"
FROZEN_PATH = _HERE / "_data" / "thermo_friction_frozen.json"
#: The evaluation run taken before the round (§0), which ``--frozen`` reads.
EVAL_BEFORE_PATH = _HERE / "_data" / "thermo_friction_eval_before.json"

#: C5: the survey's blind spot (Phase 157 §7.2).
BLIND_SPOT_QUESTION = "gram : mass :: mlilisecond : ?"

_SOURCES: Tuple[str, ...] = (
    "knowledge/thermo_friction_study.py",
    "knowledge/thermo_friction.py",
    "knowledge/friction.py",
    "knowledge/friction_two.py",
    "knowledge/friction_survey.py",
    "knowledge/model.py",
    "knowledge/reader.py",
    "runtime/respell.py",
    "runtime/sinter.py",
)

MARKS: Tuple[str, ...] = ("A1", "A2", "A3", "A4", "A5", "A6", "A7",
                          "B1", "B2", "B3", "B4", "B5", "B6",
                          "C1", "C2", "C3", "C4", "C5", "C6")
AMENDED: Tuple[str, ...] = ("B6′",)
#: The continuations of experiment A, by name.
GOVERNORS: Tuple[str, ...] = ("patch", "contact", "static", "governor",
                              "contact_governor")

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
# A.  THE GOVERNOR
# ===========================================================================

def _choosers():
    from . import friction as fr
    from . import thermo_friction as tf
    return {
        "patch": tf.patch_chooser,
        "contact": lambda: fr.contact_predict,
        "static": tf.static_chooser,
        "governor": tf.governor_chooser,
        "contact_governor": tf.contact_governor_chooser,
    }


def governor_measure(model, held: Sequence[Any]) -> Dict[str, Any]:
    """§2.1: the five continuations on the held-out prompts (most frequent
    non-empty, summed overlap, distinct, stops), the quality of what the
    governor changed, the row tallies (A5: cold rows where the governor's
    choice is not the patch's; A7: stops), and position precision."""
    from . import friction as fr
    from .friction_study import _continuation_summary
    makers = _choosers()
    texts = {k: Counter() for k in GOVERNORS}
    over = Counter()
    stops = {k: Counter() for k in GOVERNORS}
    rows = Counter()
    undeclared = 0
    changed = changed_gov = changed_patch = 0
    for s in held:
        toks = s.tokens
        prompt, truth = toks[:fr.PROMPT], toks[fr.PROMPT:fr.PROMPT + fr.MAX_TOKENS]
        got = {}
        for name in GOVERNORS:
            c = fr.continuation(makers[name](), model, prompt)
            got[name] = c
            texts[name][c["text"]] += 1
            over[name] += fr.overlap(c["tokens"], truth)
            stops[name][c["stop"]] += 1
        g = got["governor"]
        for key in ("hot", "cold", "cold_disagree", "hot_repeating",
                    "cold_repeating", "moved"):
            rows[key] += g["state"].get(key, 0)
        if g["stop"] not in fr.STOPS or len(g["tokens"]) > fr.MAX_TOKENS:
            undeclared += 1
        if g["text"] != got["patch"]["text"]:
            changed += 1
            changed_gov += fr.overlap(g["tokens"], truth)
            changed_patch += fr.overlap(got["patch"]["tokens"], truth)
    out = _continuation_summary(texts, over, stops)
    out["rows"] = {k: rows[k] for k in ("hot", "cold", "cold_disagree",
                                        "hot_repeating", "cold_repeating",
                                        "moved")}
    out["undeclared_stops"] = undeclared
    out["changed"] = {"sentences": changed, "governor_overlap": changed_gov,
                      "patch_overlap": changed_patch}
    position = {}
    for name in GOVERNORS:
        c = Counter()
        for s in held:
            r = fr.predict_positions(makers[name](), model, s.tokens)
            c.update({k: r[k] for k in ("positions", "answered", "correct")})
        position[name] = {k: c[k] for k in ("positions", "answered", "correct")}
    out["position"] = position
    out["positions"] = position["patch"]["positions"]
    return out


# ===========================================================================
# B.  THE ANCHOR
# ===========================================================================

def anchor_measure(evidence, held: Sequence[Any]) -> Dict[str, Any]:
    """§2.2 and §2.4 on the directory reader: every reader's switches,
    returns, final readings (all and on the hot sentences) and switches
    into the truth; the hot steps; the B5 check; and, on the sentences whose
    last step is hot, which leader names the true directory."""
    from . import friction as fr
    from . import thermo_friction as tf
    n = len(held)
    folders = [evidence.folder(s) for s in held]
    prompts = [fr.content_words(s.tokens)[:tf.PROMPT_WORDS] for s in held]
    names = ("frictionless", "stick 1/4", "noise r/8", "anchor",
             "mismatched anchor", "other-directory anchor")
    totals = {k: Counter() for k in names}
    read = hot_sentences = steps = hot_steps = 0
    cold_off = agree_hot = 0
    last_hot = Counter()
    same_next = sum(1 for i in range(n) if folders[i] == folders[(i + 1) % n])
    for i, s in enumerate(held):
        other = None
        for d in range(1, n):
            j = (i + d) % n
            if folders[j] != folders[i]:
                other = j
                break
        others = {"mismatched anchor": prompts[(i + 1) % n] if n else [],
                  "other-directory anchor": prompts[other] if other is not None
                  else []}
        got = tf.anchor_readers(evidence, s, others)
        if not got["steps"]:
            continue
        read += 1
        steps += got["steps"]
        hot_steps += got["hot_steps"]
        cold_off += got["cold_off_leader"]
        agree_hot += got["agree_hot"]
        hot = got["hot_steps"] > 0
        hot_sentences += hot
        truth = got["truth"]
        for name in names:
            st = fr.reading_stats(got["readings"][name], truth)
            totals[name].update(st)
            if hot:
                totals[name]["hot_final_correct"] += st["final_correct"]
        if got["last_hot"]:
            last_hot["sentences"] += 1
            for side in ("prompt", "generated", "leader"):
                last_hot[side] += got["last"][side] == truth
    return {
        "scale": evidence.scale, "folders": evidence.size,
        "sentences": n, "read": read, "hot_sentences": hot_sentences,
        "steps": steps, "hot_steps": hot_steps,
        "same_directory_next": same_next,
        "cold_off_leader": cold_off, "agree_hot": agree_hot,
        "last_hot": {k: last_hot[k] for k in ("sentences", "prompt",
                                              "generated", "leader")},
        "readers": {k: {f: totals[k][f] for f in
                        ("switches", "returns", "final_correct",
                         "hot_final_correct", "into_truth")} for k in names},
    }


# ===========================================================================
# C.  SINTERING
# ===========================================================================

def recovery_set(lex=None, tbl=None) -> List[Tuple[str, str]]:
    """§2.3's recovery set: ``(entry, perturbed)`` for every lexicon entry the
    corpus vocabulary does not know, perturbed by the survey's typo, where the
    swap changes it and leaves it unknown to both vocabularies."""
    from ..runtime import respell as rs
    from ..runtime import sinter as sn
    from .friction_survey import _typo
    lex = sn.lexicon() if lex is None else lex
    tbl = rs.table() if tbl is None else tbl
    out = []
    for entry in sorted(lex):
        if rs.known(entry, tbl):
            continue
        moved = _typo(entry)
        if moved is None or rs.known(moved, tbl) or moved.lower() in lex:
            continue
        out.append((entry, moved))
    return out


def _protected_check(questions: Sequence[str], tbl, lex) -> Dict[str, int]:
    """C4: every protected token of every question, and each perturbed by
    the survey's typo, read by ``loaded`` and by the sintered reading."""
    from ..runtime import respell as rs
    from ..runtime import sinter as sn
    from .friction_survey import _typo
    tokens = perturbed = differ = 0
    for q in questions:
        toks = rs.tokens(q)
        for i, tok in enumerate(toks):
            if not sn.protected(tok):
                continue
            company = [t.lower() for j, t in enumerate(toks)
                       if j != i and rs.known(t, tbl)]
            for form in (tok, _typo(tok)):
                if form is None:
                    continue
                if form == tok:
                    tokens += 1
                else:
                    perturbed += 1
                solid = rs.respell_token(form, company, "loaded", tbl) or form
                sint = sn.sinter_token(form, company, tbl, lex) or form
                differ += solid != sint
    return {"tokens": tokens, "perturbed": perturbed, "differ": differ}


def sinter_measure(tbl=None, lex=None) -> Dict[str, Any]:
    """§2.3 offline: the recovery set, the typo and short-word questions of
    Phase 157, every lexicon entry as a one-token question, and the
    protected class -- each under ``loaded`` and the sintered reading."""
    from ..runtime import respell as rs
    from ..runtime import sinter as sn
    from . import friction_two_study as f2s
    tbl = rs.table() if tbl is None else tbl
    lex = sn.lexicon() if lex is None else lex

    def sintered(text, company=None):
        return sn.respell_sintered(text, tbl, lex, company)

    readers = {"loaded": None, "sintered": sintered}
    rec = recovery_set(lex, tbl)
    typos = f2s.typo_pairs()
    shorts = [(o, m) for o, m, _w in f2s.short_word_pairs(tbl=tbl)]
    out: Dict[str, Any] = {"recovery_set": len(rec), "recovery": {},
                           "typo": {}, "short_words": {},
                           "lexicon_changed": {}, "lexicon": len(lex)}
    for name, reader in readers.items():
        out["recovery"][name] = f2s.respell_tally(rec, "loaded", True, tbl,
                                                  reader)
        out["typo"][name] = f2s.respell_tally(typos, "loaded", True, tbl,
                                              reader)
        out["short_words"][name] = f2s.respell_tally(shorts, "loaded", True,
                                                     tbl, reader)
        changed = []
        for entry in sorted(lex):
            got = (rs.respell(entry, "loaded", tbl=tbl).text if reader is None
                   else reader(entry).text)
            if got != entry:
                changed.append([entry, got])
        out["lexicon_changed"][name] = len(changed)
        out.setdefault("lexicon_examples", {})[name] = changed[:20]
    out["typo_questions"] = len(typos)
    out["short_moved"] = len(shorts)
    from ..evaluation.cases import CASES
    out["protected"] = _protected_check([c.question for c in CASES], tbl, lex)
    return out


def corpus_measure(knowledge=None) -> Dict[str, Any]:
    """Experiments A, B and C on the corpus as it now is."""
    from . import friction as fr
    from . import model as mdl
    knowledge = mdl.load() if knowledge is None else knowledge
    held = fr.sample(knowledge)
    model = fr.hold_out_model(knowledge, held)
    return {
        "corpus": {"documents": len(knowledge.documents),
                   "sentences": len(knowledge.sentences),
                   "digest": knowledge.digest},
        "governor": governor_measure(model, held),
        "anchor": anchor_measure(fr.FolderEvidence(knowledge, "directory"),
                                 held),
        "sinter": sinter_measure(),
    }


# ===========================================================================
# THE MARKS, FROM THE STORED FIGURES
# ===========================================================================

def _prec_ge(a: Mapping[str, int], b: Mapping[str, int]) -> bool:
    """``correct_a / answered_a >= correct_b / answered_b``."""
    return a["correct"] * b["answered"] >= b["correct"] * a["answered"]


def _marks(data: Optional[Dict[str, Any]], blind: Optional[Dict[str, Any]],
           frozen: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    from .friction_two_study import _frozen_holds
    m = {k: False for k in MARKS + AMENDED}
    if data:
        gv, an, sn = data["governor"], data["anchor"], data["sinter"]
        mf, ov, ds, pos = (gv["most_frequent"], gv["overlap"], gv["distinct"],
                           gv["position"])
        m["A1"] = mf["governor"][1] * 2 <= mf["patch"][1]
        m["A2"] = ov["governor"] >= ov["patch"]
        m["A3"] = ds["governor"] >= ds["patch"]
        m["A4"] = (ov["governor"] >= ov["static"]
                   and _prec_ge(pos["governor"], pos["static"]))
        m["A5"] = gv["rows"]["cold_disagree"] == 0
        m["A6"] = _prec_ge(pos["governor"], pos["patch"])
        m["A7"] = gv["undeclared_stops"] == 0
        rd = an["readers"]
        f, a = rd["frictionless"], rd["anchor"]
        m["B1"] = a["hot_final_correct"] > f["hot_final_correct"]
        m["B2"] = a["final_correct"] * 100 >= f["final_correct"] * 100 - an["read"]
        m["B3"] = a["switches"] <= f["switches"] and a["returns"] <= f["returns"]
        m["B4"] = a["into_truth"] * 10 >= f["into_truth"] * 9
        m["B5"] = an["cold_off_leader"] == 0 and an["agree_hot"] == 0
        m["B6"] = rd["mismatched anchor"]["hot_final_correct"] < a["hot_final_correct"]
        m["B6′"] = (rd["other-directory anchor"]["hot_final_correct"]
                    < a["hot_final_correct"])
        rec, size = sn["recovery"]["sintered"], sn["recovery_set"]
        m["C1"] = (size > 0 and rec["restored"] * 100 >= size * 80
                   and rec["different"] * 100 <= size * 2)
        m["C2"] = all(sn[k]["sintered"]["restored"] >= sn[k]["loaded"]["restored"]
                      and sn[k]["sintered"]["different"]
                      <= sn[k]["loaded"]["different"]
                      for k in ("typo", "short_words"))
        m["C3"] = sn["lexicon_changed"]["sintered"] == 0
        m["C4"] = sn["protected"]["differ"] == 0
    if blind:
        m["C5"] = blind.get("exit") == 0 and bool(blind.get("answer"))
    if frozen:
        m["C6"] = _frozen_holds(frozen)
    return m


def _assemble(data: Optional[Dict[str, Any]], blind: Optional[Dict[str, Any]],
              frozen: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    m = _marks(data, blind, frozen)
    marks = {k: bool(m[k]) for k in MARKS}
    amended = {k: bool(m[k]) for k in AMENDED}
    out: Dict[str, Any] = {"corpus": data or {}}
    if blind:
        out["blind_spot"] = blind
    if frozen:
        out["frozen"] = frozen
    unmeasured = []
    if not blind:
        unmeasured.append("C5: the blind-spot answer is not stored "
                          "(python3 -m glm_universal.tools thermo-friction "
                          "--blind-spot)")
    if not frozen:
        unmeasured.append("C6: the frozen-path comparison is not stored "
                          "(--frozen PATH, against "
                          "_data/thermo_friction_eval_before.json)")
    out.update({"marks": marks, "met": sum(marks.values()),
                "taken": len(marks), "amended": amended,
                "amended_met": sum(amended.values()),
                "amended_taken": len(amended),
                "shipped": all(marks[k] for k in ("C1", "C2", "C3", "C4")),
                "unmeasured": unmeasured})
    return out


# ===========================================================================
# THE STANDARD APPARATUS
# ===========================================================================

def compute(knowledge: Any = None) -> Dict[str, object]:
    """Take the corpus measurement; read the stored blind spot and frozen
    path."""
    return _assemble(corpus_measure(knowledge), _read_json(BLIND_SPOT_PATH),
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


def write_blind_spot(path: Optional[Path] = None) -> Path:
    """Ask ``GLM.py`` the survey's blind-spot question (C5) and store the
    exit code and the answer it printed."""
    from .friction_survey import _cli_output
    code, stdout = _cli_output(BLIND_SPOT_QUESTION)
    lines = stdout.splitlines()
    answer = next((l[len("ANSWER"):].strip() for l in lines
                   if l.startswith("ANSWER")), "")
    respelt = next((l[len("RESPELT"):].strip() for l in lines
                    if l.startswith("RESPELT")), "")
    out = path if path is not None else BLIND_SPOT_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"question": BLIND_SPOT_QUESTION, "exit": code,
                               "answer": answer, "respelt": respelt},
                              indent=1, sort_keys=True, ensure_ascii=False)
                   + "\n", encoding="utf-8")
    return out


def write_frozen(report_path: Path, path: Optional[Path] = None) -> str:
    """Compare an evaluation report (``--json`` output) with the one taken
    before the round and store the comparison (C6).  Nothing is written when
    the evaluation before the round is not stored."""
    from .friction_two_study import frozen_compare
    before = _read_json(EVAL_BEFORE_PATH)
    if before is None:
        return (f"nothing: the evaluation before the round "
                f"({EVAL_BEFORE_PATH.name}) is not stored")
    after = json.loads(Path(report_path).read_text(encoding="utf-8"))
    out = path if path is not None else FROZEN_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(frozen_compare(before, after), indent=1,
                              sort_keys=True, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    return str(out)


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


def thermo_friction_report() -> Dict[str, object]:
    """Every mark from the stored figures; ``available=False`` with the
    re-take instruction when the corpus measurement is absent or stale."""
    stored = current()
    if stored is not None:
        out = _assemble(stored.get("corpus"), _read_json(BLIND_SPOT_PATH),
                        _read_json(FROZEN_PATH))
        out["available"] = True
        out["source_digest"] = stored.get("source_digest")
        return out
    st = state()
    what = "absent" if not st["present"] else "stale (the code moved)"
    return {
        "available": False,
        "reasons": [f"the stored measurement is {what}; re-take it with "
                    f"python3 -m glm_universal.tools thermo-friction --write"],
    }

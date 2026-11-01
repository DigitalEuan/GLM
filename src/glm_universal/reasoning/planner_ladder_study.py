"""``glm_universal.reasoning.planner_ladder_study`` -- the marks of
``studies/PLANNER_LADDER_STUDY.md`` (Phase 151): the chain of the stepwise
planner as a GLM-BAT program.

*Created 29 October 2026 (as a stub). Last altered 31 October 2026
(repository check: the measurement rebuilt; the stub returned every mark
False).*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from studies/PLANNER_LADDER_STUDY.md
(§§0-7), MASTER_PLAN.md (Phase 151), the handler ``_planner_ladder`` of
tools.py and tests/README.md.*

What is measured (``--write`` re-takes it; ``planner_ladder_report`` reads
the stored measurement when its digest is current)
--------------------------------------------------------------------------
The corpus (:func:`corpus_texts`) is the single-turn texts of the stepwise
planner's corpora of rounds one to five
(``runtime.stepwise_five.corpus_texts`` without the router's sets) and the
held-out texts of the tool verdicts (``tool_verdicts_cases.VERDICTS_HELD_OUT``);
the chains are the texts :func:`runtime.stepwise.answer` answers.  The
original list of 283 texts was lost with its baseline, so this corpus is a
reconstruction and its counts are reported as they come out.

* **P1** every chain said as GLM-BAT, read back from English to the
  identical lines, run to a halt with exit code 0.
* **P2** no chain drifts.  **P3** every gated pipeline promotes.
* **P4** every chain with a computed step, its last computed step raised by
  one (a verdict flipped): the drift is exactly that step, and the pipeline
  does not promote and leaves no file.
* **P5** both column-3 scripts of every chain verify; the run claim with its
  last file altered and the pipeline claim with its promotion flipped are
  rejected.
* **F1** and **F2** are frozen-path marks: every recorded text asked again
  through the router against the baseline taken before the round
  (``_data/planner_ladder_baseline.json``), and the evaluation's frozen path
  (``ties_ladder_frozen``).  The baseline was lost in the October 2026
  reorganisation (the answering-path gate, ``stepwise._ladder_gate``, was
  lost with it and has since been restored), and the shared baseline
  ``ties_ladder_frozen`` compares against was lost too (F2 is read from its
  stored record, which says so): both marks are reported **not met**, with
  the reason, never assumed.
* **L1** (reported beside the marks, as the study does): the Lean file is
  present, states the theorems of §1 and has no ``sorry``; the build itself
  (``lake build``) is not run here.
* The post-hoc reading of §7.2: a lie in the last carried numeric step.

Exactness
---------
Integers, :class:`fractions.Fraction`, strings, booleans.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .. import integrity

__all__ = [
    "DATA_PATH", "BASELINE_PATH", "_SOURCES", "compute", "measure",
    "write_measurements", "measurements", "state", "current",
    "module_digest", "planner_ladder_report", "corpus_texts", "answered",
    "lean_marks", "column3_counts", "JOBS",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "planner_ladder_study.json"
BASELINE_PATH = _HERE / "_data" / "planner_ladder_baseline.json"

#: Parallel column-3 scripts (each a ``python3 -I`` process).
JOBS: int = 4

_SOURCES: Tuple[str, ...] = (
    "reasoning/planner_ladder_study.py",
    "reasoning/planner_ladder.py",
    "reasoning/ties_ladder_frozen.py",
    "reasoning/carried_read.py",
    "reasoning/register_files.py",
    "reasoning/fold_machine.py",
    "reasoning/tool_machine.py",
    "reasoning/batch_machine.py",
    "reasoning/batch_speech.py",
    "reasoning/stepwise_script.py",
    "runtime/stepwise.py",
    "evaluation/stepwise_cases.py",
    "evaluation/stepwise_two_cases.py",
    "evaluation/stepwise_three_cases.py",
    "evaluation/stepwise_four_cases.py",
    "evaluation/stepwise_five_cases.py",
    "evaluation/tool_verdicts_cases.py",
)

_cache: Optional[Dict[str, object]] = None


def _plain(x: Any) -> Any:
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


# ---------------------------------------------------------------------------
# the corpus
# ---------------------------------------------------------------------------

def corpus_texts() -> List[Tuple[str, str]]:
    """``(source, text)``: the single-turn texts of the stepwise corpora of
    rounds one to five, then the tool verdicts' held-out texts."""
    from ..evaluation import (stepwise_cases, stepwise_two_cases,
                              stepwise_three_cases, stepwise_four_cases,
                              stepwise_five_cases, tool_verdicts_cases)
    out: List[Tuple[str, str]] = []
    seen = set()
    for mod in (stepwise_cases, stepwise_two_cases, stepwise_three_cases,
                stepwise_four_cases, stepwise_five_cases):
        name = mod.__name__.rsplit(".", 1)[1]
        for attr in sorted(dir(mod)):
            if not attr.endswith("_CASES"):
                continue
            for case in getattr(mod, attr):
                for item in case[1:]:
                    if isinstance(item, str) and " " in item and \
                            item not in seen:
                        seen.add(item)
                        out.append((name, item))
    for case in tool_verdicts_cases.VERDICTS_HELD_OUT:
        if case[1] not in seen:
            seen.add(case[1])
            out.append(("tool_verdicts_cases", case[1]))
    return out


def answered(session=None) -> List[Tuple[str, object]]:
    """``(text, chain)`` of every corpus text the stepwise planner answers."""
    from ..runtime import stepwise as sw
    if session is None:
        from ..runtime.session import GeometricSession
        session = GeometricSession()
    out = []
    for _src, text in corpus_texts():
        a = sw.answer(session, text)
        if a.answered:
            out.append((text, a.chain))
    return out


def lean_marks(name: str = "PlannerLadder.lean",
               theorems: Tuple[str, ...] = ()) -> Dict[str, object]:
    """The Lean file: present, the theorems stated, no ``sorry``.  The build
    is not run here; an absent file is not met."""
    from .. import constants
    from . import planner_ladder as pl
    theorems = theorems or pl.LEAN_THEOREMS
    path = constants.lean_file(name)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    stated = [n for n in theorems if f"theorem {n}" in text]
    return {"file": name, "present": bool(text), "theorems": len(stated),
            "declared": len(theorems),
            "missing": [n for n in theorems if n not in stated],
            "sorry": "sorry" in text,
            "met": bool(text) and len(stated) == len(theorems)
            and "sorry" not in text}


def column3_counts(items: List[Tuple[object, object]],
                   jobs: int = JOBS) -> Dict[str, object]:
    """Both column-3 scripts and both mutants of each ``(chain, ladder)``."""
    from . import batch_speech as bs
    from . import planner_ladder as pl
    work = []
    for chain, lad in items:
        sc = pl.column3_scripts(chain, lad)
        mu = pl.column3_mutants(lad)
        work.append((chain.question, sc["run"][0], sc["pipeline"][0],
                     mu["run"][0], mu["pipeline"][0]))

    def one(w):
        return (w[0],) + tuple(bs.run_script(s)[0] for s in w[1:])

    with ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
        res = list(ex.map(one, work))
    return {
        "scripts_run": sum(1 for r in res if r[1]),
        "scripts_pipeline": sum(1 for r in res if r[2]),
        "mutants": 2 * len(res),
        "mutants_rejected": sum((not r[3]) + (not r[4]) for r in res),
        "script_failures": [r[0] for r in res if not (r[1] and r[2])],
        "escaped": [r[0] for r in res if r[3] or r[4]],
    }


# ---------------------------------------------------------------------------
# the measurement
# ---------------------------------------------------------------------------


def f2_frozen() -> Dict[str, object]:
    """F2 from the stored shared frozen path (``tools ties-ladder-frozen``),
    as :func:`nearest_question_study.f1_frozen` reads it (31 October 2026)."""
    from . import ties_ladder_frozen as tlf
    stored = tlf.current()
    if stored is None and not tlf.BASELINE_PATH.is_file():
        # without the baseline nothing is asked, so the record is read live
        # (instant) rather than reported merely stale (31 October 2026)
        live = tlf.f1_frozen_path()
        live.pop("new_answers", None)
        live["F2"] = bool(live.pop("F1"))
        return live
    if stored is None:
        return {"F2": False,
                "reason": (f"the shared frozen path (ties-ladder-frozen) is "
                           f"{tlf.state()['verdict']}")}
    out = dict(stored["frozen"])
    out.pop("new_answers", None)
    out["F2"] = bool(stored["marks"]["F1"])
    return out


def _gate_present() -> bool:
    """Whether the stepwise answering path holds the ladder gate
    (``_ladder_gate`` in ``runtime/stepwise.py``), read off the tree as
    ``fold_machine_study.gate_present`` reads it.  *Added 31 October 2026
    (repository check): the note used to say the gate was absent after the
    gate had been restored.*"""
    p = Path(__file__).resolve().parent.parent / "runtime" / "stepwise.py"
    return p.exists() and "_ladder_gate" in p.read_text(encoding="utf-8")

def compute(scripts: bool = True) -> Dict[str, object]:
    from . import planner_ladder as pl
    chains = answered()
    m: Dict[str, object] = {
        "chains": len(chains), "said": 0, "halted": 0, "lines": 0,
        "machine_steps": 0, "no_drift": 0, "promoted": 0, "admitted": 0,
        "computed": 0, "carried": 0, "steps": 0,
        "lies": 0, "lies_found": 0, "lies_rolled_back": 0,
        "read_lies": 0, "read_lies_found_at_step": 0,
        "read_lies_downstream": 0, "read_lies_unseen": 0,
    }
    failures: List[str] = []
    lie_failures: List[str] = []
    items = []
    for text, chain in chains:
        c = pl.check_chain(chain, say=True, read=False, ladder=True)
        lad = c["ladder"]
        m["steps"] += len(chain.steps)
        m["said"] += bool(c["said"])
        m["halted"] += c["status"] == "halted" and c["exit"] == 0
        m["lines"] += c["lines"]
        m["machine_steps"] += c["machine_steps"]
        m["no_drift"] += not c["drift"]
        m["promoted"] += c["promoted"]
        m["admitted"] += c["admitted"]
        m["computed"] += len(c["computed"])
        m["carried"] += len(c["carried"])
        if not (c["admitted"] and c["said"]):
            failures.append(text)
        if lad.run is not None:
            items.append((chain, lad))
        # P4: the last computed step altered
        if c["computed"]:
            k = c["computed"][-1]
            lie = pl.value_lie(chain.steps[k - 1])
            if lie is not None:
                m["lies"] += 1
                d = pl.check_chain(pl.lie_chain(chain, k, lie), say=False,
                                   read=False)
                exact = d["drift"] == [pl.file_of(k)]
                m["lies_found"] += exact
                back = not d["promoted"] and d["rolled_back"]
                m["lies_rolled_back"] += back
                if not (exact and back):
                    lie_failures.append(text)
        # §7.2 post hoc: the last carried numeric step raised by one
        nums = [k for k in c["carried"]
                if isinstance(chain.steps[k - 1].value, Fraction)]
        if nums:
            k = nums[-1]
            m["read_lies"] += 1
            d = pl.check_chain(pl.lie_chain(chain, k, chain.steps[k - 1].value
                                            + 1), say=False, read=False)
            first = d["first_drift"]
            if first == k:
                m["read_lies_found_at_step"] += 1
            elif d["drift"]:
                m["read_lies_downstream"] += 1
            else:
                m["read_lies_unseen"] += 1
    m["failures"] = failures
    m["lie_failures"] = lie_failures
    m["max_lines"] = max((len(lad.lines) for _c, lad in items), default=0)
    if scripts:
        m.update(column3_counts(items))
    n = m["chains"]
    f2 = f2_frozen()
    marks = {
        "P1": n > 0 and m["said"] == n and m["halted"] == n,
        "P2": n > 0 and m["no_drift"] == n,
        "P3": n > 0 and m["promoted"] == n,
        "P4": m["lies"] > 0 and m["lies_found"] == m["lies"]
        and m["lies_rolled_back"] == m["lies"],
        "P5": scripts and m.get("scripts_run") == n
        and m.get("scripts_pipeline") == n
        and m.get("mutants_rejected") == m.get("mutants"),
        "F1": False,
        "F2": bool(f2["F2"]),
    }
    return {
        "machine": m,
        "corpus": {"texts": len(corpus_texts()), "chains": n},
        "frozen": {},
        "evaluation": f2,
        "frozen_note": (
            "F1 not measured: planner_ladder_baseline.json: baseline lost in "
            "the October 2026 reorganisation; a new baseline needs a "
            "frozen-path comparison before the answering path moves again"
            + (" (the answering-path gate, runtime/stepwise.py _ladder_gate, "
               "is present again)" if _gate_present() else
               " (and the answering-path gate, runtime/stepwise.py "
               "_ladder_gate, is absent, so no answer passes through the "
               "machine)")),
        "evaluation_note": (
            "F2 from the stored shared frozen path (ties-ladder-frozen): "
            + (f2.get("reason") or "read")),
        "lean": lean_marks(),
        "marks": marks,
        "met": sum(1 for v in marks.values() if v),
        "taken": len(marks),
    }


def module_digest() -> str:
    root = _HERE.parent
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


def planner_ladder_report() -> Dict[str, object]:
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    return {
        "available": False,
        "reason": ("the stored measurement is absent or stale; re-take it "
                   "with python3 -m glm_universal.tools planner-ladder "
                   "--write"),
    }

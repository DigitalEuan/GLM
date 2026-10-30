"""``glm_universal.reasoning.pipeline_ask_study`` -- the marks of
``studies/PIPELINE_ASK_STUDY.md`` (Phase 176).

*Created 21 October 2026.*

What is measured
----------------
Phase 175's protocol (fifteen families, fifty queries each, at two, three
and four demonstrations: 2,250 queries) is run with the solver as shipped.
Every query it refuses as ``ambiguous`` -- two fitting hypotheses disagree --
is handed to :func:`glm_universal.reasoning.pipeline_ask.ask_loop`, at most
three asks, the reply to each ask given by the family's true rule.  The marks
were declared before the first measurement:

* **A1** no wrong answer: after asking, 0 of the ambiguous refusals is
  answered wrongly;
* **A2** resolution: at least 80% of them are answered right within three
  asks;
* **A3** one ask mostly: of those answered right, at least half needed
  exactly one ask;
* **A4** the pool suffices: for at least 95% of them the declared pool holds
  a separating input, so the first ask can be made;
* **A5** every ask shrinks (``separating_strict_shrink``): after each reply
  the survivors are a strict subset of those before, new fitted hypotheses
  (an XOR mask, a learnt permutation) apart -- 0 exceptions;
* **A6** the choice earns its keep: the scored choice needs no more asks in
  total than the control that asks for the first separating input of the
  pool;
* **L** ``PipelineAsk.lean`` states its theorems with no ``sorry``;
* **T** the tool: ``tool induce``'s refusal of Phase 175's under-determined
  example names an input to ask about.

Exactness
---------
Integers, tuples and strings only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .. import integrity
from . import pipeline_ask as pa
from . import pipeline_kit as pk

__all__ = ["DATA_PATH", "QUERIES", "DEMOS", "MAX_ASKS", "compute", "measure",
           "write_measurements", "measurements", "state", "current",
           "pipeline_ask_report"]

_HERE = Path(__file__).resolve().parent
DATA_PATH: Path = _HERE / "_data" / "pipeline_ask_study.json"

QUERIES = 50
DEMOS = (2, 3, 4)
MAX_ASKS = 3

_SOURCES = (
    "reasoning/pipeline_ask_study.py",
    "reasoning/pipeline_ask.py",
    "reasoning/pipeline_kit.py",
)

TOOL_REFUSE = "tool induce 100/000/000 -> 001/000/000 ? 110/000/001"


def _fitted(name: str) -> bool:
    return name.endswith("xor_mask") or name == "learnt_permutation"


def _first_separating(pairs, query, live, exclude=()):
    """The control: the first input of the pool that separates."""
    banned = set(exclude)
    for x in pa.candidate_pool(pairs, query):
        if x in banned:
            continue
        outs = [hy(x) for hy in live]
        if all(o is not None for o in outs) and len(set(outs)) >= 2:
            return x
    return None


def _control_loop(pairs, query, oracle) -> Dict[str, object]:
    demos = list(pairs)
    asks = 0
    undefined: List = []
    r = pk.solve(demos, query)
    while r["status"] == "ambiguous" and asks < MAX_ASKS:
        live = pa.survivors(demos, query)
        x = _first_separating(demos, query, live, undefined)
        if x is None:
            break
        y = oracle(x)
        if y is None:
            undefined.append(x)
            continue
        demos.append((x, y))
        asks += 1
        r = pk.solve(demos, query)
    return {"status": r["status"], "answer": r.get("answer"), "asks": asks}


def _lean() -> Dict[str, object]:
    root = Path(__file__).resolve().parents[2] / "lean"
    text = (root / pa.LEAN_FILE).read_text(encoding="utf-8")
    found = [t for t in pa.LEAN_THEOREMS if f"theorem {t}" in text]
    return {"file": pa.LEAN_FILE, "declared": len(pa.LEAN_THEOREMS),
            "theorems": len(found), "sorry": text.count("sorry")}


def _tool() -> Dict[str, object]:
    from ..runtime.toolbox import run_tool
    r = run_tool(TOOL_REFUSE)
    return {"ok": r.ok, "status": r.figures.get("status"),
            "ask": r.figures.get("ask"),
            "names_input": "to settle it, give the output for" in r.text}


def compute() -> Dict[str, object]:
    fams: Dict[str, Dict[str, int]] = {}
    tot = {"queries": 0, "ambiguous": 0, "right": 0, "wrong": 0,
           "still_refused": 0, "no_separating_input": 0, "asks": 0,
           "one_ask": 0, "shrink_checked": 0, "shrink_exceptions": 0,
           "fitted_appearances": 0, "control_right": 0, "control_wrong": 0,
           "control_asks": 0}
    hist = {str(k): 0 for k in range(MAX_ASKS + 1)}
    for name in pk.FAMILIES:
        oracle = pa.true_rule(name)
        row = {"ambiguous": 0, "right": 0, "wrong": 0, "still_refused": 0}
        for n in DEMOS:
            for q in range(QUERIES):
                x, y = pk.sample(name, 1000 * q + 999)
                demos = [pk.sample(name, 1000 * q + i) for i in range(n)]
                tot["queries"] += 1
                r = pk.solve(demos, x)
                if r["status"] != "ambiguous":
                    continue
                row["ambiguous"] += 1
                tot["ambiguous"] += 1
                live = pa.survivors(demos, x)
                if pa.separating_input(demos, x, live) is None:
                    tot["no_separating_input"] += 1
                a = pa.ask_loop(demos, x, oracle, MAX_ASKS)
                k = len(a["asks"])
                tot["asks"] += k
                for step in a["asks"]:
                    before, after = set(step["before"]), set(step["after"])
                    tot["shrink_checked"] += 1
                    new = after - before
                    if any(not _fitted(h) for h in new) or not (before - after):
                        tot["shrink_exceptions"] += 1
                    elif new:
                        tot["fitted_appearances"] += 1
                if a["status"] == "answered":
                    if a["answer"] == y:
                        row["right"] += 1
                        tot["right"] += 1
                        hist[str(k)] += 1
                        tot["one_ask"] += k == 1
                    else:
                        row["wrong"] += 1
                        tot["wrong"] += 1
                else:
                    row["still_refused"] += 1
                    tot["still_refused"] += 1
                c = _control_loop(demos, x, oracle)
                tot["control_asks"] += c["asks"]
                if c["status"] == "answered":
                    if c["answer"] == y:
                        tot["control_right"] += 1
                    else:
                        tot["control_wrong"] += 1
        fams[name] = row
    report: Dict[str, object] = {
        "queries": QUERIES, "demos": list(DEMOS), "max_asks": MAX_ASKS,
        "families": fams, "totals": tot, "asks_histogram_right": hist,
        "lean": _lean(), "tool": _tool()}
    report["marks"] = _marks(report)
    report["met"] = sum(1 for v in report["marks"].values() if v)
    report["taken"] = len(report["marks"])
    return report


def _marks(r: Dict[str, object]) -> Dict[str, bool]:
    t = r["totals"]
    amb = t["ambiguous"]
    lean = r["lean"]
    return {
        "A1": amb > 0 and t["wrong"] == 0,
        "A2": amb > 0 and 5 * t["right"] >= 4 * amb,
        "A3": t["right"] > 0 and 2 * t["one_ask"] >= t["right"],
        "A4": amb > 0 and 20 * (amb - t["no_separating_input"]) >= 19 * amb,
        "A5": t["shrink_checked"] > 0 and t["shrink_exceptions"] == 0,
        "A6": t["asks"] <= t["control_asks"],
        "L": lean["theorems"] == lean["declared"] and lean["sorry"] == 0,
        "T": (not r["tool"]["ok"] and r["tool"]["status"] == "ambiguous"
              and r["tool"]["names_input"]),
    }


# ── the cache, guarded by a digest ────────────────────────────────────────

def module_digest() -> str:
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / n for n in sorted(set(_SOURCES))],
                                 root)


def measure() -> Dict[str, object]:
    report = compute()
    report["source_digest"] = module_digest()
    return report


def write_measurements(path: Optional[Path] = None) -> Path:
    target = Path(path) if path is not None else DATA_PATH
    target.write_text(json.dumps(measure(), indent=1, sort_keys=True,
                                 ensure_ascii=False) + "\n",
                      encoding="utf-8")
    global _cache
    _cache = None
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    _cache = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return _cache


def state() -> Dict[str, object]:
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent",
                "live_digest": live, "stored_digest": None}
    fresh = stored.get("source_digest") == live
    return {"present": True, "fresh": fresh,
            "verdict": "current" if fresh else "stale",
            "live_digest": live, "stored_digest": stored.get("source_digest")}


def current() -> Optional[Dict[str, object]]:
    return measurements() if state()["fresh"] else None


def pipeline_ask_report() -> Dict[str, object]:
    """The stored marks, or why there are none."""
    stored = current()
    if stored is None:
        return {"available": False, "reason": (
            f"the stored measurement is {state()['verdict']}; re-take it "
            f"with python3 -m glm_universal.tools pipeline-ask --write")}
    return dict(stored, available=True)

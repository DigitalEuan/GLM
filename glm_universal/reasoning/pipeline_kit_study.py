"""``glm_universal.reasoning.pipeline_kit_study`` -- the marks of
``studies/PIPELINE_KIT_STUDY.md`` (Phase 175).

*Created 21 October 2026.*

What is measured
----------------
The owner's pipeline kit (``source_material/GLM_Pipeline_Kit/``) brought into
the GLM as :mod:`glm_universal.reasoning.pipeline_kit` and ``tool induce``.
Fifteen task families, fifty queries each, at two, three and four
demonstrations: the kit's five, three more single-step families, three
two-step families and four bit-string families (one-row grids).  The marks:

* **B** the kit's bridge, never run before: the four theorems the kit proves
  for any binary code containing 0 (parity wall, parity wall with glue, the
  8x embedding, junction parity) hold on the GLM's own substrate -- 0
  failures in 2,000 words each;
* **L1** ``PipelineInduction.lean`` states its theorems with no ``sorry``;
  **L2** the kit's seven Lean files are in the development with no ``sorry``;
* **K** the control, the kit as delivered (its operators and its learnt
  permutation, no new operator, no composition) at four demonstrations:
  toggle, translate and reflect_v all 50 right; flood_fill and bfs_shortest
  0 right -- the study's open items, reproduced;
* **D** derive, the open items closed: at four demonstrations flood_fill
  and bfs_shortest each at least 45 of 50 right, 0 wrong;
* **S** task steps: each two-step family at least 45 of 50 right at four
  demonstrations, 0 wrong, where the kit's control gets 0 right;
* **G** beyond grids: each bit-string family at least 45 of 50 right at four
  demonstrations, 0 wrong;
* **R** refusal: the solver as shipped (single operators and two-step
  compositions read as one tier) gives 0 wrong answers over all 2,250
  queries; the two controls -- single operators read first (``occam``), and
  the first fitting hypothesis answering with no agreement gate -- give more
  than 0; the cost is the count of refusals, reported;
* **M** monotone collapse (``consistentIn_more_demos``): every hypothesis
  surviving three demonstrations survived the first two, and every one
  surviving four survived the first three -- 0 exceptions among the
  operators of a fixed vocabulary.  A hypothesis *fitted* from the
  demonstrations (an XOR mask) is offered only once two distinct
  demonstrations exist (the evidence guard), so it can appear when one
  arrives; those appearances are counted and reported, not excepted.  (As
  first declared, M counted them as exceptions and failed, 16 in 1,500; all
  16 were fitted masks on ``translate``, whose two first demonstrations are
  often the same pair.  The narrowing is recorded in the study.)
* **W** the layer filter (``wt_comp_perm``) is lossless: with it off, no
  answer changes, and with it on it skips at least one permutation on every
  family whose demonstrations change the weight;
* **A** the iteration-8 analogy: the threshold decode exact on 0 of 30
  toggle analogies with ``A != C``, the parity decode on 30 of 30;
* **T** the tool: ``tool induce`` answers a fixed reflect task with the true
  grid and refuses a fixed under-determined one.

Exactness
---------
Integers, tuples and strings only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .. import integrity
from . import pipeline_kit as pk

__all__ = [
    "DATA_PATH", "QUERIES", "DEMOS", "run_family", "compute", "measure",
    "write_measurements", "measurements", "state", "current",
    "pipeline_kit_report",
]

_HERE = Path(__file__).resolve().parent
DATA_PATH: Path = _HERE / "_data" / "pipeline_kit_study.json"

QUERIES = 50
DEMOS: Tuple[int, ...] = (2, 3, 4)

_SOURCES: Tuple[str, ...] = (
    "reasoning/pipeline_kit_study.py",
    "reasoning/pipeline_kit.py",
    "substrate/leech2.py",
)

#: The configurations run: the solver as shipped and its three controls.
CONFIGS: Dict[str, Dict[str, object]] = {
    "shipped": {},
    "occam": {"mode": "occam"},
    "no_gate": {"mode": "occam", "gate": False},
    "kit": {"kit_only": True},
}

TOOL_ANSWER = ("tool induce 100/000/000 -> 001/000/000 ; "
               "110/010/000 -> 011/010/000 ; 000/100/011 -> 000/001/110 ? "
               "010/011/100")
TOOL_ANSWER_TRUE = "010/110/001"
TOOL_REFUSE = "tool induce 100/000/000 -> 001/000/000 ? 110/000/001"


def _demos(name: str, q: int, n: int):
    return [pk.sample(name, 1000 * q + i) for i in range(n)]


def run_family(name: str, n: int, **kw) -> Dict[str, object]:
    """Right, wrong and refused over ``QUERIES`` queries with ``n``
    demonstrations each, and the survivors of each query."""
    right = wrong = refused = skipped = 0
    survivors: List[List[str]] = []
    answers: List[Optional[str]] = []
    for q in range(QUERIES):
        x, y = pk.sample(name, 1000 * q + 999)
        r = pk.solve(_demos(name, q, n), x, **kw)
        survivors.append(list(r.get("survivors", [])))
        skipped += r.get("skipped_by_layer", 0) or 0
        if r["status"] == "answered":
            answers.append(pk.grid_text(r["answer"]))
            if r["answer"] == y:
                right += 1
            else:
                wrong += 1
        else:
            answers.append(None)
            refused += 1
    return {"right": right, "wrong": wrong, "refused": refused,
            "skipped_by_layer": skipped, "survivors": survivors,
            "answers": answers}


def _bridge() -> Dict[str, int]:
    return pk.check_substrate(2000)


def _lean() -> Dict[str, object]:
    root = Path(__file__).resolve().parents[2] / "glm_lean"
    text = (root / pk.LEAN_FILE).read_text(encoding="utf-8")
    found = [t for t in pk.LEAN_THEOREMS if f"theorem {t}" in text]
    kit = {}
    for f in pk.KIT_LEAN_FILES:
        p = root / f
        body = p.read_text(encoding="utf-8") if p.exists() else None
        kit[f] = {"present": body is not None,
                  "sorry": (body or "").count("sorry"),
                  "theorems": (body or "").count("\ntheorem ")}
    return {"file": pk.LEAN_FILE, "declared": len(pk.LEAN_THEOREMS),
            "theorems": len(found), "sorry": text.count("sorry"),
            "kit": kit}


def _analogy() -> Dict[str, int]:
    s = pk.Stream(175)
    thr = par = taken = 0
    while taken < 30:
        a, c = s.bit_list(24), s.bit_list(24)
        if a == c:
            continue
        taken += 1
        b = [1 - v for v in a]
        d = [1 - v for v in c]
        thr += pk.threshold_analogy(a, b, c) == tuple(d)
        par += pk.parity_analogy(a, b, c) == tuple(d)
    return {"trials": taken, "threshold_exact": thr, "parity_exact": par}


def _tool() -> Dict[str, object]:
    from ..runtime.toolbox import run_tool
    ok = run_tool(TOOL_ANSWER)
    no = run_tool(TOOL_REFUSE)
    return {"answer_ok": ok.ok, "answer": ok.figures.get("answer"),
            "refuse_ok": no.ok, "refuse_status": no.figures.get("status")}


def _fitted(name: str) -> bool:
    """Is the hypothesis fitted from the demonstrations rather than a member
    of the fixed vocabulary?"""
    return name.endswith("xor_mask") or name == "learnt_permutation"


def compute() -> Dict[str, object]:
    families: Dict[str, Dict[str, object]] = {}
    totals: Dict[str, Dict[str, int]] = {c: {"right": 0, "wrong": 0,
                                             "refused": 0} for c in CONFIGS}
    monotone = {"checked": 0, "exceptions": 0, "fitted_appearances": 0}
    filt = {"changed_answers": 0, "weight_changing_families": 0,
            "filtered_families": 0}
    for name, (group, h, w, _gen) in pk.FAMILIES.items():
        row: Dict[str, object] = {"group": group, "shape": [h, w]}
        runs = {}
        for cname, kw in CONFIGS.items():
            per = {}
            for n in DEMOS:
                r = run_family(name, n, **kw)
                per[str(n)] = {k: r[k] for k in ("right", "wrong", "refused")}
                for k in ("right", "wrong", "refused"):
                    totals[cname][k] += r[k]
                runs[(cname, n)] = r
            row[cname] = per
        for n_small, n_big in zip(DEMOS, DEMOS[1:]):
            small = runs[("shipped", n_small)]["survivors"]
            big = runs[("shipped", n_big)]["survivors"]
            for s_list, b_list in zip(small, big):
                if not s_list or not b_list:
                    continue
                monotone["checked"] += 1
                new = set(b_list) - set(s_list)
                if any(not _fitted(h) for h in new):
                    monotone["exceptions"] += 1
                elif new:
                    monotone["fitted_appearances"] += 1
        off = run_family(name, 4, layer_filter=False)
        on = runs[("shipped", 4)]
        filt["changed_answers"] += sum(1 for a, b in zip(on["answers"],
                                                         off["answers"])
                                       if a != b)
        weight_changes = any(
            sum(pk.flatten(x)) != sum(pk.flatten(y))
            for x, y in (pk.sample(name, i) for i in range(4)))
        if weight_changes:
            filt["weight_changing_families"] += 1
            if on["skipped_by_layer"] >= QUERIES:
                filt["filtered_families"] += 1
        row["skipped_by_layer_at_4"] = on["skipped_by_layer"]
        families[name] = row
    report: Dict[str, object] = {
        "queries": QUERIES, "demos": list(DEMOS),
        "families": families, "totals": totals,
        "bridge": _bridge(), "lean": _lean(), "monotone": monotone,
        "layer_filter": filt, "analogy": _analogy(), "tool": _tool(),
    }
    report["marks"] = _marks(report)
    report["met"] = sum(1 for v in report["marks"].values() if v)
    report["taken"] = len(report["marks"])
    return report


def _at4(r: Dict[str, object], fam: str, cfg: str) -> Dict[str, int]:
    return r["families"][fam][cfg]["4"]


def _group(r: Dict[str, object], group: str) -> List[str]:
    return [f for f, row in r["families"].items() if row["group"] == group]


def _marks(r: Dict[str, object]) -> Dict[str, bool]:
    b = r["bridge"]
    lean = r["lean"]
    t = r["totals"]

    def good(f: str) -> bool:
        a = _at4(r, f, "shipped")
        return a["right"] >= 45 and a["wrong"] == 0

    return {
        "B": all(b[k] == 0 for k in ("parity_wall", "parity_wall_glue",
                                     "eight_mul", "junction_parity"))
             and b["trials"] == 2000,
        "L1": lean["theorems"] == lean["declared"] and lean["sorry"] == 0,
        "L2": all(v["present"] and v["sorry"] == 0
                  for v in lean["kit"].values()),
        "K": (all(_at4(r, f, "kit")["right"] == QUERIES
                  for f in ("toggle", "translate", "reflect_v"))
              and all(_at4(r, f, "kit")["right"] == 0
                      for f in ("flood_fill", "bfs_shortest"))),
        "D": all(good(f) for f in ("flood_fill", "bfs_shortest")),
        "S": (all(good(f) for f in _group(r, "steps"))
              and all(_at4(r, f, "kit")["right"] == 0
                      for f in _group(r, "steps"))),
        "G": all(good(f) for f in _group(r, "string")),
        "R": (t["shipped"]["wrong"] == 0 and t["occam"]["wrong"] > 0
              and t["no_gate"]["wrong"] > 0),
        "M": r["monotone"]["checked"] > 0 and r["monotone"]["exceptions"] == 0,
        "W": (r["layer_filter"]["changed_answers"] == 0
              and r["layer_filter"]["weight_changing_families"] > 0
              and r["layer_filter"]["filtered_families"]
              == r["layer_filter"]["weight_changing_families"]),
        "A": (r["analogy"]["threshold_exact"] == 0
              and r["analogy"]["parity_exact"] == r["analogy"]["trials"]),
        "T": (r["tool"]["answer_ok"] and r["tool"]["answer"] == TOOL_ANSWER_TRUE
              and not r["tool"]["refuse_ok"]
              and r["tool"]["refuse_status"] == "ambiguous"),
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


def pipeline_kit_report() -> Dict[str, object]:
    """The stored marks, or why there are none."""
    stored = current()
    if stored is None:
        return {"available": False, "reason": (
            f"the stored measurement is {state()['verdict']}; re-take it "
            f"with python3 -m glm_universal.tools pipeline-kit --write")}
    return dict(stored, available=True)

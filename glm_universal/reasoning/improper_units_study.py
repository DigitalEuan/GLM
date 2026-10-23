"""``glm_universal.reasoning.improper_units_study`` -- the marks of
``studies/IMPROPER_UNITS_STUDY.md`` (Phase 181): an improper Lorentz map
times a change of units as a declared family of ``tool frame`` in 1+2
dimensions.

*Created 22 October 2026.*

What is measured
----------------
Twenty task families on exact rational states ``(E, px, py)``, thirty
queries each at one, two, three and four demonstrations (2,400 queries),
made by the generator of the Phase 179 study
(:mod:`glm_universal.reasoning.improper_frame_study`) so the measurements are
comparable.

*Improper times units, now inside*: ``improper_units`` (a Lorentz map times
``py -> -py``, times a scale: the Phase 179 generator's outside family);
``reflect_units`` (the spatial plane reflected in a rational line, times a
scale); ``time_units`` (a Lorentz map times ``E -> -E``, times a scale);
``pt_units`` (times both, times a scale).
*Inside since Phases 178 and 179* (the regression set): the twelve
in-vocabulary families of the Phase 179 study.
*Outside*: ``shear``, ``squeeze``, ``swap`` (as in Phase 179) and
``anisotropic`` (``E`` doubled, ``px`` and ``py`` tripled: the Minkowski Gram
matrix is not a multiple of the inputs').

Solvers: **shipped** (all thirteen families); **Phase 179** (the ten
families before this round); **first fit** (the first family not ruled out
answers).

Marks (declared before the first measurement)
---------------------------------------------
* **U1** shipped: 0 wrong answers on the sixteen in-vocabulary families,
  every demonstration count;
* **U2** at three demonstrations, at least 95 % of the four new families'
  queries answered right;
* **U3** outside: 0 wrong answers at three or more demonstrations;
* **U4** nothing the Phase 179 family set answers changes: on every query of
  all twenty families, when the Phase 179 set answers, the shipped set gives
  the same answer;
* **U5** every answer to a new family's query at three or more
  demonstrations names the component of the true map's Lorentz factor and
  the true scale, and recomposes: ``s . B . P^a . T^b`` is the fitted map
  with ``B`` proper orthochronous;
* **U6** the gate earns its keep: the first-fit control gives at least one
  wrong answer on in-vocabulary queries;
* **L** ``LorentzUnits.lean`` states its theorems with no ``sorry``;
* **T** ``tool frame`` answers the three-pair task for twice the reflection
  ``py -> -py`` with ``6,2,-2``, naming ``lorentz_parity`` and the scale
  ``2``, and refuses its two-pair version, asking about ``2,0,1``.

Exactness
---------
``Fraction`` only.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .. import integrity
from . import frame_plane as fp
from . import frame_plane_study as fps
from . import improper_frame_study as ifs

__all__ = ["DATA_PATH", "QUERIES", "DEMOS", "NEW", "REGRESSION",
           "OUT_VOCAB", "compute", "measure", "write_measurements",
           "measurements", "state", "current", "improper_units_report"]

_HERE = Path(__file__).resolve().parent
DATA_PATH: Path = _HERE / "_data" / "improper_units_study.json"

QUERIES = 30
DEMOS = (1, 2, 3, 4)
F = Fraction

_SOURCES = (
    "reasoning/improper_units_study.py",
    "reasoning/improper_frame_study.py",
    "reasoning/frame_plane_study.py",
    "reasoning/frame_plane.py",
    "runtime/toolbox.py",
)

NEW: Tuple[str, ...] = ("improper_units", "reflect_units", "time_units",
                        "pt_units")
REGRESSION: Tuple[str, ...] = ifs.IMPROPER + ifs.PROPER
OUT_VOCAB: Tuple[str, ...] = ("shear", "squeeze", "swap", "anisotropic")

TRUE_COMPONENT = {"improper_units": "lorentz_parity",
                  "reflect_units": "lorentz_parity",
                  "time_units": "lorentz_time",
                  "pt_units": "lorentz_pt"}


def _scaled(sc: Fraction, m: fp.Mat) -> fp.Mat:
    return tuple(tuple(sc * v for v in row) for row in m)


def _matrix(name: str, rng: fps._Rng) -> Tuple[fp.Mat, Optional[Fraction]]:
    """The true map, and its scale for a new family."""
    if name == "improper_units":
        sc = fps._SCALES[rng.next(len(fps._SCALES))]
        return _scaled(sc, fp.matmul(ifs._lorentz(rng), fp.PARITY)), sc
    if name == "reflect_units":
        sc = fps._SCALES[rng.next(len(fps._SCALES))]
        return _scaled(sc, fp.reflect(*fps._turn(rng))), sc
    if name == "time_units":
        sc = fps._SCALES[rng.next(len(fps._SCALES))]
        return _scaled(sc, fp.matmul(ifs._lorentz(rng), fp.TIME_REV)), sc
    if name == "pt_units":
        sc = fps._SCALES[rng.next(len(fps._SCALES))]
        return _scaled(sc, fp.matmul(fp.matmul(ifs._lorentz(rng), fp.PARITY),
                                     fp.TIME_REV)), sc
    if name == "anisotropic":
        return ((F(2), F(0), F(0)), (F(0), F(3), F(0)),
                (F(0), F(0), F(3))), None
    return ifs._matrix(name, rng), None


def _task(name: str, seed: int, demos: int):
    rng = fps._Rng(seed * 7919 + sum(ord(c) for c in name) + 181)
    m, sc = _matrix(name, rng)
    xs: List[fp.State3] = []
    while len(xs) < demos + 1:
        x = fps._timelike(rng)
        if x not in xs:
            xs.append(x)
    pairs = [(x, fp.matvec(m, x)) for x in xs[:demos]]
    q = xs[demos]
    return pairs, (q, fp.matvec(m, q)), m, sc


def _blank() -> Dict[str, int]:
    return {"queries": 0, "right": 0, "wrong": 0, "refused": 0}


def _units_ok(r: Dict[str, object], fam: str, sc: Fraction) -> bool:
    """The answer names the true component and scale, and recomposes."""
    name = r.get("component")
    if name != TRUE_COMPONENT[fam] or r.get("scale") != sc:
        return False
    m = r["families"][name + "_units"]["matrix"]
    lorentz = _scaled(1 / sc, m)
    b, a, t = fp.improper_split(lorentz)
    back = b
    if a:
        back = fp.matmul(back, fp.PARITY)
    if t:
        back = fp.matmul(back, fp.TIME_REV)
    return (_scaled(sc, back) == m and fp.is_lorentz(b) and (a, t) == (
        r["split"]["parity"], r["split"]["time_reversal"]))


def synthetic() -> Dict[str, object]:
    solvers = ("shipped", "phase_179", "first_fit")
    sides = ("new", "regression", "out")
    totals = {s: {side: _blank() for side in sides} for s in solvers}
    fams = {f: {s: _blank() for s in solvers}
            for f in NEW + REGRESSION + OUT_VOCAB}
    by_demos = {str(d): {side: _blank() for side in sides} for d in DEMOS}
    named = {"answers": 0, "named_right": 0}
    changed: List[str] = []
    phase_179_answered = 0
    for fam in NEW + REGRESSION + OUT_VOCAB:
        side = ("new" if fam in NEW else
                "regression" if fam in REGRESSION else "out")
        for d in DEMOS:
            for q in range(QUERIES):
                pairs, (qx, qy), _m, sc = _task(fam, q + 1000 * d, d)
                res = {"shipped": fp.solve(pairs, qx),
                       "phase_179": fp.solve(
                           pairs, qx, families=fp.PHASE_179_FAMILIES),
                       "first_fit": fp.first_fit(pairs, qx)}
                for s, r in res.items():
                    g = fps._grade(r, qy)
                    totals[s][side]["queries"] += 1
                    totals[s][side][g] += 1
                    fams[fam][s]["queries"] += 1
                    fams[fam][s][g] += 1
                sh, old = res["shipped"], res["phase_179"]
                g = fps._grade(sh, qy)
                by_demos[str(d)][side]["queries"] += 1
                by_demos[str(d)][side][g] += 1
                if old["status"] == "answered":
                    phase_179_answered += 1
                    if sh["status"] != "answered" or \
                            sh["answer"] != old["answer"]:
                        changed.append(f"{fam}/{d}/{q}")
                if side == "new" and d >= 3 and g == "right":
                    named["answers"] += 1
                    named["named_right"] += _units_ok(sh, fam, sc)
    return {"totals": totals, "families": fams, "by_demos": by_demos,
            "named": named, "changed": changed,
            "phase_179_answered": phase_179_answered}


def _lean() -> Dict[str, object]:
    root = Path(__file__).resolve().parents[2] / "glm_lean"
    text = (root / fp.LEAN_FILE_UNITS).read_text(encoding="utf-8")
    found = [t for t in fp.LEAN_THEOREMS_UNITS if f"theorem {t}" in text]
    return {"declared": len(fp.LEAN_THEOREMS_UNITS),
            "theorems": len(found), "sorry": text.count("sorry")}


def _tool() -> Dict[str, object]:
    from ..runtime.toolbox import run_tool
    pairs = ["1,0,0 -> 2,0,0", "2,1,0 -> 4,2,0", "2,0,1 -> 4,0,-2"]
    r3 = run_tool(f"tool frame {' ; '.join(pairs)} ? 3,1,1")
    r2 = run_tool(f"tool frame {' ; '.join(pairs[:2])} ? 2,0,1")
    return {"answer_ok": r3.ok, "answer": r3.figures.get("answer"),
            "component": r3.figures.get("component"),
            "scale": r3.figures.get("scale"),
            "cites": "conformal_split" in r3.text,
            "refuse_ok": r2.ok, "ask": r2.figures.get("ask")}


def compute() -> Dict[str, object]:
    report = {"synthetic": synthetic(), "lean": _lean(), "tool": _tool(),
              "queries": QUERIES, "demos": list(DEMOS), "new": list(NEW),
              "regression": list(REGRESSION), "out_vocab": list(OUT_VOCAB)}
    marks = _marks(report)
    report["marks"] = marks
    report["met"] = sum(marks.values())
    report["taken"] = len(marks)
    return report


def _marks(r: Dict[str, object]) -> Dict[str, bool]:
    s = r["synthetic"]
    t = s["totals"]
    bd = s["by_demos"]
    n = s["named"]
    tool = r["tool"]
    in_wrong = t["shipped"]["new"]["wrong"] + t["shipped"]["regression"]["wrong"]
    in_q = t["shipped"]["new"]["queries"] + t["shipped"]["regression"]["queries"]
    three = bd["3"]["new"]
    out_wrong_ge3 = sum(bd[str(d)]["out"]["wrong"] for d in DEMOS if d >= 3)
    ff_wrong = (t["first_fit"]["new"]["wrong"]
                + t["first_fit"]["regression"]["wrong"])
    return {
        "U1": in_q > 0 and in_wrong == 0,
        "U2": three["queries"] > 0 and 100 * three["right"] >= 95 * three["queries"],
        "U3": out_wrong_ge3 == 0,
        "U4": s["phase_179_answered"] > 0 and not s["changed"],
        "U5": n["answers"] > 0 and n["named_right"] == n["answers"],
        "U6": ff_wrong > 0,
        "L": (r["lean"]["theorems"] == r["lean"]["declared"]
              and r["lean"]["sorry"] == 0),
        "T": (tool["answer_ok"] and tool["answer"] == "6,2,-2" and
              tool["component"] == "lorentz_parity" and tool["scale"] == "2"
              and tool["cites"] and not tool["refuse_ok"]
              and tool["ask"] == "2,0,1"),
    }


def _plain(x):
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {str(k): _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


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
    target.write_text(json.dumps(_plain(measure()), indent=1, sort_keys=True,
                                 ensure_ascii=False) + "\n", encoding="utf-8")
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


def improper_units_report() -> Dict[str, object]:
    """The stored marks, or why there are none."""
    stored = current()
    if stored is None:
        return {"available": False, "reason": (
            f"the stored measurement is {state()['verdict']}; re-take it "
            f"with python3 -m glm_universal.tools improper-units --write")}
    return dict(stored, available=True)

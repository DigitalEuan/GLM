"""``glm_universal.reasoning.improper_frame_study`` -- the marks of
``studies/IMPROPER_FRAME_STUDY.md`` (Phase 179): improper maps (reflections,
time reversal and their compositions with Lorentz maps) as declared families
of ``tool frame`` in 1+2 dimensions.

*Created 22 October 2026.*

What is measured
----------------
Sixteen task families on exact rational states ``(E, px, py)``, thirty
queries each at one, two, three and four demonstrations (1,920 queries),
made by the generator of the Phase 178 study
(:mod:`glm_universal.reasoning.frame_plane_study`) so the two measurements
are comparable.

*Improper, now inside*: ``reflect`` (``py -> -py``); ``reflect_line`` (the
spatial plane reflected in a rational line); ``time_reverse``
(``E -> -E``); ``lorentz_parity`` (a boost along a rotated axis times a
rotation, times ``py -> -py``); ``lorentz_time`` (the same times
``E -> -E``); ``lorentz_pt`` (times both).
*Proper, inside since Phase 178* (the regression set): ``identity``,
``rotation``, ``boost_x``, ``lorentz``, ``thomas``, ``lorentz_units``.
*Outside*: ``shear`` (``px' = px + k py``); ``squeeze`` (``px`` doubled,
``py`` halved: determinant 1, not Lorentz); ``improper_units`` (an improper
Lorentz map times a change of units, which no family declares);
``swap`` (``E`` and ``px`` exchanged: the Minkowski form negated on that
plane).

Solvers: **shipped** (all ten families, the gate with the span rule and span
guard); **Phase 178** (the same gate over the six families before this
round); **first fit** (the first family not ruled out answers).

Marks (declared before the first measurement)
---------------------------------------------
* **I1** shipped: 0 wrong answers on the twelve in-vocabulary families, every
  demonstration count;
* **I2** at three demonstrations, at least 95 % of the improper families'
  queries answered right;
* **I3** outside: 0 wrong answers at three or more demonstrations;
* **I4** nothing the Phase 178 family set answers changes: on every query of
  all sixteen families, when the Phase 178 set answers, the shipped set gives
  the same answer;
* **I5** every improper answer at three or more demonstrations names the
  component of the true map, and its split recomposes: ``B . P^a . T^b`` is
  the fitted map with ``B`` proper orthochronous;
* **I6** the gate earns its keep: the first-fit control gives at least one
  wrong answer on in-vocabulary queries;
* **L** ``LorentzImproper.lean`` states its theorems with no ``sorry``;
* **T** ``tool frame`` answers the three-pair reflection task with
  ``3,1,-1`` naming ``lorentz_parity``, and refuses its two-pair version,
  citing ``plane_partner`` and asking about ``2,0,1``.

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

__all__ = ["DATA_PATH", "QUERIES", "DEMOS", "IMPROPER", "PROPER",
           "OUT_VOCAB", "compute", "measure", "write_measurements",
           "measurements", "state", "current", "improper_frame_report"]

_HERE = Path(__file__).resolve().parent
DATA_PATH: Path = _HERE / "_data" / "improper_frame_study.json"

QUERIES = 30
DEMOS = (1, 2, 3, 4)
F = Fraction

_SOURCES = (
    "reasoning/improper_frame_study.py",
    "reasoning/frame_plane_study.py",
    "reasoning/frame_plane.py",
    "runtime/toolbox.py",
)

IMPROPER: Tuple[str, ...] = ("reflect", "reflect_line", "time_reverse",
                             "lorentz_parity", "lorentz_time", "lorentz_pt")
PROPER: Tuple[str, ...] = ("identity", "rotation", "boost_x", "lorentz",
                           "thomas", "lorentz_units")
OUT_VOCAB: Tuple[str, ...] = ("shear", "squeeze", "improper_units", "swap")

TRUE_COMPONENT = {"reflect": "lorentz_parity",
                  "reflect_line": "lorentz_parity",
                  "time_reverse": "lorentz_time",
                  "lorentz_parity": "lorentz_parity",
                  "lorentz_time": "lorentz_time",
                  "lorentz_pt": "lorentz_pt"}


def _lorentz(rng: fps._Rng) -> fp.Mat:
    c, s = fps._turn(rng)
    b = fp.matmul(fp.matmul(fp.rot(c, s), fp.boost_x(fps._u(rng))),
                  fp.rot(c, -s))
    return fp.matmul(b, fp.rot(*fps._turn(rng)))


def _matrix(name: str, rng: fps._Rng) -> fp.Mat:
    if name in ("identity", "rotation", "boost_x", "lorentz", "thomas",
                "lorentz_units", "shear"):
        return fps._matrix(name, rng)
    if name == "reflect":
        return fp.PARITY
    if name == "reflect_line":
        return fp.reflect(*fps._turn(rng))
    if name == "time_reverse":
        return fp.TIME_REV
    if name == "lorentz_parity":
        return fp.matmul(_lorentz(rng), fp.PARITY)
    if name == "lorentz_time":
        return fp.matmul(_lorentz(rng), fp.TIME_REV)
    if name == "lorentz_pt":
        return fp.matmul(fp.matmul(_lorentz(rng), fp.PARITY), fp.TIME_REV)
    if name == "squeeze":
        return ((F(1), F(0), F(0)), (F(0), F(2), F(0)), (F(0), F(0), F(1, 2)))
    if name == "improper_units":
        sc = fps._SCALES[rng.next(len(fps._SCALES))]
        m = fp.matmul(_lorentz(rng), fp.PARITY)
        return tuple(tuple(sc * v for v in row) for row in m)
    if name == "swap":
        return ((F(0), F(1), F(0)), (F(1), F(0), F(0)), (F(0), F(0), F(1)))
    raise KeyError(name)


def _task(name: str, seed: int, demos: int):
    rng = fps._Rng(seed * 7919 + sum(ord(c) for c in name) + 179)
    m = _matrix(name, rng)
    xs: List[fp.State3] = []
    while len(xs) < demos + 1:
        x = fps._timelike(rng)
        if x not in xs:
            xs.append(x)
    pairs = [(x, fp.matvec(m, x)) for x in xs[:demos]]
    q = xs[demos]
    return pairs, (q, fp.matvec(m, q)), m


def _blank() -> Dict[str, int]:
    return {"queries": 0, "right": 0, "wrong": 0, "refused": 0}


def _split_ok(r: Dict[str, object]) -> bool:
    name = r.get("component")
    if name is None:
        return False
    m = r["families"][name]["matrix"]
    b, a, t = fp.improper_split(m)
    back = b
    if a:
        back = fp.matmul(back, fp.PARITY)
    if t:
        back = fp.matmul(back, fp.TIME_REV)
    return back == m and fp.is_lorentz(b) and (a, t) == (
        r["split"]["parity"], r["split"]["time_reversal"])


def synthetic() -> Dict[str, object]:
    solvers = ("shipped", "phase_178", "first_fit")
    sides = ("improper", "proper", "out")
    totals = {s: {side: _blank() for side in sides} for s in solvers}
    fams = {f: {s: _blank() for s in solvers}
            for f in IMPROPER + PROPER + OUT_VOCAB}
    by_demos = {str(d): {side: _blank() for side in sides} for d in DEMOS}
    components = {"answers": 0, "named_right": 0, "split_ok": 0}
    changed: List[str] = []
    phase_178_answered = 0
    for fam in IMPROPER + PROPER + OUT_VOCAB:
        side = ("improper" if fam in IMPROPER else
                "proper" if fam in PROPER else "out")
        for d in DEMOS:
            for q in range(QUERIES):
                pairs, (qx, qy), _m = _task(fam, q + 1000 * d, d)
                res = {"shipped": fp.solve(pairs, qx),
                       "phase_178": fp.solve(
                           pairs, qx, families=fp.PHASE_178_FAMILIES),
                       "first_fit": fp.first_fit(pairs, qx)}
                for s, r in res.items():
                    g = fps._grade(r, qy)
                    totals[s][side]["queries"] += 1
                    totals[s][side][g] += 1
                    fams[fam][s]["queries"] += 1
                    fams[fam][s][g] += 1
                sh, old = res["shipped"], res["phase_178"]
                g = fps._grade(sh, qy)
                by_demos[str(d)][side]["queries"] += 1
                by_demos[str(d)][side][g] += 1
                if old["status"] == "answered":
                    phase_178_answered += 1
                    if sh["status"] != "answered" or \
                            sh["answer"] != old["answer"]:
                        changed.append(f"{fam}/{d}/{q}")
                if side == "improper" and d >= 3 and g == "right":
                    components["answers"] += 1
                    components["named_right"] += (
                        sh.get("component") == TRUE_COMPONENT[fam])
                    components["split_ok"] += _split_ok(sh)
    return {"totals": totals, "families": fams, "by_demos": by_demos,
            "components": components, "changed": changed,
            "phase_178_answered": phase_178_answered}


def _lean() -> Dict[str, object]:
    root = Path(__file__).resolve().parents[2] / "glm_lean"
    text = (root / fp.LEAN_FILE_IMPROPER).read_text(encoding="utf-8")
    found = [t for t in fp.LEAN_THEOREMS_IMPROPER if f"theorem {t}" in text]
    return {"declared": len(fp.LEAN_THEOREMS_IMPROPER),
            "theorems": len(found), "sorry": text.count("sorry")}


def _tool() -> Dict[str, object]:
    from ..runtime.toolbox import run_tool
    pairs = ["1,0,0 -> 1,0,0", "2,1,0 -> 2,1,0", "2,0,1 -> 2,0,-1"]
    r3 = run_tool(f"tool frame {' ; '.join(pairs)} ? 3,1,1")
    r2 = run_tool(f"tool frame {' ; '.join(pairs[:2])} ? 2,0,1")
    return {"answer_ok": r3.ok, "answer": r3.figures.get("answer"),
            "component": r3.figures.get("component"),
            "refuse_ok": r2.ok, "ask": r2.figures.get("ask"),
            "cites": "plane_partner" in r2.text}


def compute() -> Dict[str, object]:
    report = {"synthetic": synthetic(), "lean": _lean(), "tool": _tool(),
              "queries": QUERIES, "demos": list(DEMOS),
              "improper": list(IMPROPER), "proper": list(PROPER),
              "out_vocab": list(OUT_VOCAB)}
    marks = _marks(report)
    report["marks"] = marks
    report["met"] = sum(marks.values())
    report["taken"] = len(marks)
    return report


def _marks(r: Dict[str, object]) -> Dict[str, bool]:
    s = r["synthetic"]
    t = s["totals"]
    bd = s["by_demos"]
    c = s["components"]
    tool = r["tool"]
    in_wrong = t["shipped"]["improper"]["wrong"] + t["shipped"]["proper"]["wrong"]
    in_q = (t["shipped"]["improper"]["queries"]
            + t["shipped"]["proper"]["queries"])
    three = bd["3"]["improper"]
    out_wrong_ge3 = sum(bd[str(d)]["out"]["wrong"] for d in DEMOS if d >= 3)
    ff_wrong = (t["first_fit"]["improper"]["wrong"]
                + t["first_fit"]["proper"]["wrong"])
    return {
        "I1": in_q > 0 and in_wrong == 0,
        "I2": three["queries"] > 0 and 100 * three["right"] >= 95 * three["queries"],
        "I3": out_wrong_ge3 == 0,
        "I4": s["phase_178_answered"] > 0 and not s["changed"],
        "I5": (c["answers"] > 0 and c["named_right"] == c["answers"]
               and c["split_ok"] == c["answers"]),
        "I6": ff_wrong > 0,
        "L": (r["lean"]["theorems"] == r["lean"]["declared"]
              and r["lean"]["sorry"] == 0),
        "T": (tool["answer_ok"] and tool["answer"] == "3,1,-1" and
              tool["component"] == "lorentz_parity" and not tool["refuse_ok"]
              and tool["cites"] and tool["ask"] == "2,0,1"),
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


def improper_frame_report() -> Dict[str, object]:
    """The stored marks, or why there are none."""
    stored = current()
    if stored is None:
        return {"available": False, "reason": (
            f"the stored measurement is {state()['verdict']}; re-take it "
            f"with python3 -m glm_universal.tools improper-frame --write")}
    return dict(stored, available=True)

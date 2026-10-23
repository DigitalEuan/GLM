"""``glm_universal.reasoning.frame_operator_study`` -- the marks of
``studies/FRAME_OPERATOR_STUDY.md`` (Phase 177).

*Created 21 October 2026.*

What is measured
----------------
Two studies, as the review at the end of ``source_material/Lorentz
boosts.pdf`` proposes them, and the anchor ``kappa``.

**A. Exact integrity** of rational boosts over a declared grid: every
parameter ``u = m/n`` with ``1 <= n <= 12``, ``|m| < n``, applied to every
integer state with ``|E|, |p| <= 6``:

* **E1** ``E^2 - p^2`` preserved; **E2** ``B(-u) B(u) = id``; **E3**
  ``B(u) B(v) = B((u+v)/(1+uv))`` (``n <= 6`` for both); **E4** future
  timelike stays future timelike; **E5** the light-cone path (into
  ``(E+p, E-p)``, scale by ``1/k`` and ``k``, back) equals the matrix path;
  **E6** unit consistency: boosting in joules (``E``, ``pc``) and then
  converting to work units of ``kappa / N_A`` equals converting first; **E7**
  every rational boost ``a = (r + 1/r)/2``, ``b = (r - 1/r)/2`` built from an
  independent parameter ``r`` is ``B(b/(a+1))`` -- each with 0 failures.

**B. Operator inference** (``reasoning/frame_operators.py``): ten task
families -- eight inside the declared families (``identity``, ``swap``,
``parity``, ``units``, ``boost``, ``rotation``, ``boost_units``,
``rotation_units``), one composite that is (``boost_chain3``, three boosts
in turn), and two that are not (``boost_then_rotate``, ``shear``) -- thirty
queries each at one, two and three demonstrations, with timelike
demonstrations or with light-like ones all on the ray ``E = p``: 1,800
queries.  Parameters and states come from a fixed integer recurrence.
Solvers: **shipped** (all families, invariant filter, gate); **no filter**;
**occam** (fewest parameters first); **first fit** (the first fitting family
answers, a free parameter guessed); **linear** (a general 2x2 matrix).

* **F1** shipped: 0 wrong on the in-vocabulary families (nine), every
  condition;
* **F2** at two timelike demonstrations, at least 95 % of in-vocabulary
  queries answered right;
* **F3** after at most two asks, at least 90 % of the shipped refusals on
  in-vocabulary queries answered right, 0 wrong;
* **F4** the light-like confound: on one-ray light-like demonstrations, 0
  queries of ``boost``, ``units`` and ``boost_units`` answered; the first
  ask a massive state in every one; and 0 light-like pool inputs separate
  the fitted boost from the fitted change of units;
* **F5** composition: ``boost_chain3`` at two or more timelike
  demonstrations answered right every time, with the fitted Doppler factor
  the product of the three (``doppler_compose``);
* **F6** outside the vocabulary: 0 wrong answers at two or more
  demonstrations;
* **F7** the invariant filter is sound and saves work: the same status and
  answer on every query with and without it, and fewer fits tried;
* **F8** the gate earns its keep: the first-fit control gives at least one
  wrong answer on in-vocabulary queries;
* **K** the anchor: ``kappa = 190`` lies in the register's ``D0(Br2)``
  interval, every cell ratio over the anchor sweep is ``(24+T)/27``, and the
  refinement knobs order as Lean says (digit < uncertainty < tax rounding <
  quantity);
* **L** both Lean files state their theorems with no ``sorry``;
* **T** ``tool frame`` refuses one demonstration of a boost and names a
  massive state to ask about, answers two, and ``tool kappa`` answers.

Reported without a mark: the occam and linear controls, wrong answers
outside the vocabulary at one demonstration, and the bit length of exact
boost chains.

Exactness
---------
``Fraction`` and integers only.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .. import integrity
from . import frame_operators as fo
from . import kappa_anchor as ka

__all__ = ["DATA_PATH", "QUERIES", "DEMOS", "MAX_ASKS", "TASKS", "IN_VOCAB",
           "integrity_report", "compute", "measure", "write_measurements",
           "measurements", "state", "current", "frame_operator_report"]

_HERE = Path(__file__).resolve().parent
DATA_PATH: Path = _HERE / "_data" / "frame_operator_study.json"

QUERIES = 30
DEMOS = (1, 2, 3)
KINDS = ("timelike", "null")
MAX_ASKS = 2

_SOURCES = (
    "reasoning/frame_operator_study.py",
    "reasoning/frame_operators.py",
    "reasoning/kappa_anchor.py",
    "reasoning/salvage.py",
)

F = Fraction
State = fo.State

TOOL_REFUSE = "tool frame 1,0 -> 5/3,-4/3 ? 3,1"
TOOL_ANSWER = "tool frame 1,0 -> 5/3,-4/3 ; 2,1 -> 2,-1 ? 3,1"


# ── the deterministic source of parameters and states ─────────────────────

class _Rng:
    def __init__(self, seed: int) -> None:
        self.x = (seed * 2654435761 + 97) % (2 ** 31)

    def next(self, n: int) -> int:
        self.x = (1103515245 * self.x + 12345) % (2 ** 31)
        return (self.x >> 8) % n


def _param(rng: _Rng) -> Fraction:
    """A non-zero ``m/n`` with ``1 <= |m| < n <= 7``."""
    n = 2 + rng.next(6)
    m = 1 + rng.next(n - 1)
    return F(m if rng.next(2) else -m, n)


_SCALES = (F(2), F(1, 2), F(3), F(3, 2), F(2, 3), F(5, 2), F(4, 3), F(3, 4))


def _scale(rng: _Rng) -> Fraction:
    return _SCALES[rng.next(len(_SCALES))]


def _timelike(rng: _Rng) -> State:
    e = 2 + rng.next(8)
    p = rng.next(2 * e - 1) - (e - 1)
    return (F(e), F(p))


def _null(rng: _Rng) -> State:
    e = 1 + rng.next(9)
    return (F(e), F(e))


def _make(name: str, rng: _Rng) -> Tuple[Callable[[State], State], Dict[str, object]]:
    if name == "identity":
        return (lambda q: q), {}
    if name == "swap":
        return (lambda q: (q[1], q[0])), {}
    if name == "parity":
        return (lambda q: (q[0], -q[1])), {}
    if name == "units":
        s = _scale(rng)
        return (lambda q: fo.scale(s, q)), {"s": s}
    if name == "boost":
        u = _param(rng)
        return (lambda q: fo.boost(u, q)), {"u": u}
    if name == "rotation":
        t = _param(rng)
        return (lambda q: fo.rot(t, q)), {"t": t}
    if name == "boost_units":
        u, s = _param(rng), _scale(rng)
        return (lambda q: fo.scale(s, fo.boost(u, q))), {"u": u, "s": s}
    if name == "rotation_units":
        t, s = _param(rng), _scale(rng)
        return (lambda q: fo.scale(s, fo.rot(t, q))), {"t": t, "s": s}
    if name == "boost_chain3":
        us = (_param(rng), _param(rng), _param(rng))
        return (lambda q: fo.boost(us[0], fo.boost(us[1], fo.boost(us[2], q)))
                ), {"us": us}
    if name == "boost_then_rotate":
        u, t = _param(rng), _param(rng)
        return (lambda q: fo.rot(t, fo.boost(u, q))), {"u": u, "t": t}
    if name == "shear":
        return (lambda q: (q[0] + q[1], q[1])), {}
    raise KeyError(name)


IN_VOCAB: Tuple[str, ...] = ("identity", "swap", "parity", "units", "boost",
                             "rotation", "boost_units", "rotation_units",
                             "boost_chain3")
OUT_VOCAB: Tuple[str, ...] = ("boost_then_rotate", "shear")
TASKS: Tuple[str, ...] = IN_VOCAB + OUT_VOCAB


def sample(name: str, kind: str, n: int, q: int):
    """One query: (truth, params, demos, query state)."""
    rng = _Rng(hash_name(name) * 7919 + q * 104729 + n * 31 + (kind == "null"))
    truth, params = _make(name, rng)
    demos: List[Tuple[State, State]] = []
    seen = set()
    while len(demos) < n:
        x = _timelike(rng) if kind == "timelike" else _null(rng)
        if x in seen:
            continue
        seen.add(x)
        demos.append((x, truth(x)))
    while True:
        query = _timelike(rng)
        if query not in seen and fo.inv(query) != 0:
            break
    return truth, params, demos, query


def hash_name(name: str) -> int:
    """A fixed integer per family name (no Python ``hash``, which is
    salted)."""
    h = 0
    for ch in name:
        h = (h * 131 + ord(ch)) % 1000003
    return h


# ── A. exact integrity ────────────────────────────────────────────────────

def _grid(nmax: int) -> List[Fraction]:
    return sorted({F(m, n) for n in range(1, nmax + 1) for m in range(-n + 1, n)})


def integrity_report() -> Dict[str, object]:
    us = _grid(12)
    small = _grid(6)
    states = [(F(e), F(p)) for e in range(-6, 7) for p in range(-6, 7)]
    fail = {k: 0 for k in ("E1", "E2", "E3", "E4", "E5", "E6", "E7")}
    checks = {k: 0 for k in fail}
    unit = ka.KAPPA_BR / ka.NA                      # one work unit, joules
    joule = F(1, 10 ** 19)                          # states in units of 1e-19 J
    for u in us:
        k = fo.doppler(u)
        for q in states:
            b = fo.boost(u, q)
            checks["E1"] += 1
            fail["E1"] += fo.inv(b) != fo.inv(q)
            checks["E2"] += 1
            fail["E2"] += fo.boost(-u, b) != q
            if abs(q[1]) < q[0]:
                checks["E4"] += 1
                fail["E4"] += not abs(b[1]) < b[0]
            lc = fo.from_lightcone(fo.plus(q) / k, k * fo.minus(q))
            checks["E5"] += 1
            fail["E5"] += lc != b
            q_si = fo.scale(joule, q)
            a1 = fo.scale(1 / unit, fo.boost(u, q_si))
            a2 = fo.boost(u, fo.scale(1 / unit, q_si))
            checks["E6"] += 1
            fail["E6"] += a1 != a2
    for u in small:
        for v in small:
            w = fo.compose(u, v)
            for q in states[::7]:
                checks["E3"] += 1
                fail["E3"] += fo.boost(u, fo.boost(v, q)) != fo.boost(w, q)
    for num in range(1, 13):
        for den in range(1, 13):
            r = F(num, den)
            a, b = (r + 1 / r) / 2, (r - 1 / r) / 2
            u = b / (a + 1)
            checks["E7"] += 1
            fail["E7"] += not (abs(u) < 1 and fo.ca(u) == a and fo.sb(u) == b)
    return {"parameters": len(us), "states": len(states), "checks": checks,
            "failures": fail}


def _bits(x: Fraction) -> int:
    return max(abs(x.numerator).bit_length(), x.denominator.bit_length())


def bit_growth(length: int = 16) -> List[int]:
    """Largest numerator or denominator bit length of ``B(1/2)^n (2, 1)``."""
    q: State = (F(2), F(1))
    out = []
    for _ in range(length):
        q = fo.boost(F(1, 2), q)
        out.append(max(_bits(q[0]), _bits(q[1])))
    return out


# ── B. operator inference ─────────────────────────────────────────────────

def _blank() -> Dict[str, int]:
    return {"queries": 0, "right": 0, "wrong": 0, "refused": 0}


def _score(row: Dict[str, int], ans: Optional[State], y: State) -> None:
    row["queries"] += 1
    if ans is None:
        row["refused"] += 1
    elif ans == y:
        row["right"] += 1
    else:
        row["wrong"] += 1


def compute() -> Dict[str, object]:
    solvers = ("shipped", "first_take", "occam", "first_fit", "linear",
               "after_ask")
    table: Dict[str, Dict[str, Dict[str, int]]] = {}
    tot = {s: {"in": _blank(), "out": _blank()} for s in solvers}
    extra = {"filter_mismatch": 0, "tried_filter": 0, "tried_nofilter": 0,
             "shipped_refusals_in": 0, "asks_total": 0,
             "confound_queries": 0, "confound_answered": 0,
             "confound_first_ask_massive": 0, "confound_null_separates": 0,
             "confound_same_ray_separates": 0,
             "chain_queries": 0, "chain_right": 0, "chain_k_product": 0,
             "out_wrong_ge2": 0, "out_wrong_1": 0,
             "two_timelike_in": 0, "two_timelike_in_right": 0}
    nulls = [x for x in fo.POOL if fo.inv(x) == 0]
    for name in TASKS:
        vocab = "in" if name in IN_VOCAB else "out"
        for kind in KINDS:
            for n in DEMOS:
                key = f"{name}/{kind}/{n}"
                rows = {s: _blank() for s in solvers}
                for qi in range(QUERIES):
                    truth, params, demos, query = sample(name, kind, n, qi)
                    y = truth(query)
                    r = fo.solve(demos, query)
                    rn = fo.solve(demos, query, layer_filter=False)
                    rg = fo.solve(demos, query, evidence_guard=False)
                    first = rg.get("answer") if rg["status"] == "answered" else None
                    extra["tried_filter"] += r["tried"]
                    extra["tried_nofilter"] += rn["tried"]
                    if (r["status"], r.get("answer")) != (rn["status"], rn.get("answer")):
                        extra["filter_mismatch"] += 1
                    ship = r.get("answer") if r["status"] == "answered" else None
                    oc = fo.occam(demos, query)
                    occ = oc.get("answer") if oc["status"] == "answered" else None
                    a = fo.ask_loop(demos, query, truth, MAX_ASKS)
                    aft = a.get("answer") if a["status"] == "answered" else None
                    for s, ans in (("shipped", ship), ("first_take", first),
                                   ("occam", occ),
                                   ("first_fit", fo.first_fit(demos, query)),
                                   ("linear", fo.linear_fit(demos, query)),
                                   ("after_ask", aft)):
                        _score(rows[s], ans, y)
                        _score(tot[s][vocab], ans, y)
                    if vocab == "in" and ship is None:
                        extra["shipped_refusals_in"] += 1
                        extra["asks_total"] += len(a["asks"])
                    if vocab == "in" and kind == "timelike" and n == 2:
                        extra["two_timelike_in"] += 1
                        extra["two_timelike_in_right"] += ship == y
                    if (kind == "null" and n >= 1 and
                            name in ("boost", "units", "boost_units")):
                        extra["confound_queries"] += 1
                        extra["confound_answered"] += ship is not None
                        if r["status"] == "ambiguous":
                            x = fo.separating_input(demos, query, r["fitted"])
                            extra["confound_first_ask_massive"] += (
                                x is not None and fo.inv(x) != 0)
                        pb, pu = fo.fit("boost", demos), fo.fit("units", demos)
                        if pb is not None and pu is not None:
                            for x in nulls:
                                ob = fo.apply("boost", pb, x)
                                ou = fo.apply("units", pu, x)
                                if ob is not None and ou is not None and ob != ou:
                                    extra["confound_null_separates"] += 1
                                    extra["confound_same_ray_separates"] += (
                                        fo.minus(x) == 0)
                    if name == "boost_chain3" and kind == "timelike" and n >= 2:
                        extra["chain_queries"] += 1
                        extra["chain_right"] += ship == y
                        kk = r["params"].get("boost", {}).get("k")
                        us = params["us"]
                        prod = fo.doppler(us[0]) * fo.doppler(us[1]) * fo.doppler(us[2])
                        extra["chain_k_product"] += kk == prod
                    if vocab == "out" and ship is not None and ship != y:
                        extra["out_wrong_ge2" if n >= 2 else "out_wrong_1"] += 1
                table[key] = rows
    report: Dict[str, object] = {
        "queries": QUERIES, "demos": list(DEMOS), "kinds": list(KINDS),
        "max_asks": MAX_ASKS, "tasks": list(TASKS), "in_vocab": list(IN_VOCAB),
        "table": table, "totals": tot, "extra": extra,
        "integrity": integrity_report(), "bit_growth": bit_growth(),
        "kappa": _kappa(), "lean": _lean(), "tool": _tool()}
    report["marks"] = _marks(report)
    report["met"] = sum(1 for v in report["marks"].values() if v)
    report["taken"] = len(report["marks"])
    return report


def _kappa() -> Dict[str, object]:
    r = ka.kappa_report()
    order = [n for n, _ in r["ordering"]]
    return {"within": r["within_br2_interval"], "kappa_free": r["kappa_free"],
            "ratio_sweep": r["ratio_sweep"], "order": order,
            "shift_digit": str(r["shift_digit"]),
            "shift_uncertainty": str(r["shift_uncertainty"]),
            "shift_quantity": str(r["shift_quantity"]),
            "shift_tax_lower": str(r["shift_tax"][0])}


def _lean() -> Dict[str, object]:
    root = Path(__file__).resolve().parents[2] / "glm_lean"
    out = {}
    for f, names in ((fo.LEAN_FILE, fo.LEAN_THEOREMS),
                     (ka.LEAN_FILE, ka.LEAN_THEOREMS)):
        text = (root / f).read_text(encoding="utf-8")
        found = [t for t in names if f"theorem {t}" in text]
        out[f] = {"declared": len(names), "theorems": len(found),
                  "sorry": text.count("sorry")}
    return out


def _tool() -> Dict[str, object]:
    from ..runtime.toolbox import run_tool
    r1, r2, r3 = run_tool(TOOL_REFUSE), run_tool(TOOL_ANSWER), run_tool("tool kappa")
    return {"refuse_ok": r1.ok, "refuse_status": r1.figures.get("status"),
            "ask": r1.figures.get("ask"),
            "answer_ok": r2.ok, "answer": r2.figures.get("answer"),
            "kappa_ok": r3.ok}


def _marks(r: Dict[str, object]) -> Dict[str, bool]:
    t, e = r["totals"], r["extra"]
    ia = r["integrity"]
    lean = r["lean"]
    sin = t["shipped"]["in"]
    ain = t["after_ask"]["in"]
    refusals = e["shipped_refusals_in"]
    resolved_right = ain["right"] - sin["right"]
    k = r["kappa"]
    return {
        **{m: ia["checks"][m] > 0 and ia["failures"][m] == 0
           for m in ("E1", "E2", "E3", "E4", "E5", "E6", "E7")},
        "F1": sin["queries"] > 0 and sin["wrong"] == 0,
        "F2": (e["two_timelike_in"] > 0 and
               100 * e["two_timelike_in_right"] >= 95 * e["two_timelike_in"]),
        "F3": (refusals > 0 and ain["wrong"] == 0 and
               10 * resolved_right >= 9 * refusals),
        "F4": (e["confound_queries"] > 0 and e["confound_answered"] == 0 and
               e["confound_first_ask_massive"] == e["confound_queries"] and
               e["confound_null_separates"] == 0),
        "F5": (e["chain_queries"] > 0 and
               e["chain_right"] == e["chain_queries"] and
               e["chain_k_product"] == e["chain_queries"]),
        "F6": e["out_wrong_ge2"] == 0,
        "F7": (e["filter_mismatch"] == 0 and
               e["tried_filter"] < e["tried_nofilter"]),
        "F8": t["first_fit"]["in"]["wrong"] > 0,
        "K": (k["within"] and k["kappa_free"] and k["order"] == [
            "third significant figure", "register uncertainty",
            "tick-budget rounding", "which tabulated quantity"]),
        "L": all(v["theorems"] == v["declared"] and v["sorry"] == 0
                 for v in lean.values()),
        "T": (not r["tool"]["refuse_ok"] and
              r["tool"]["refuse_status"] == "ambiguous" and
              r["tool"]["ask"] is not None and r["tool"]["answer_ok"] and
              r["tool"]["kappa_ok"]),
    }


# ── the cache, guarded by a digest ────────────────────────────────────────

def module_digest() -> str:
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / n for n in sorted(set(_SOURCES))],
                                 root)


def _plain(x):
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {str(k): _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def measure() -> Dict[str, object]:
    report = compute()
    report["source_digest"] = module_digest()
    return report


def write_measurements(path: Optional[Path] = None) -> Path:
    target = Path(path) if path is not None else DATA_PATH
    target.write_text(json.dumps(_plain(measure()), indent=1, sort_keys=True,
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


def frame_operator_report() -> Dict[str, object]:
    """The stored marks, or why there are none."""
    stored = current()
    if stored is None:
        return {"available": False, "reason": (
            f"the stored measurement is {state()['verdict']}; re-take it "
            f"with python3 -m glm_universal.tools frame-operators --write")}
    return dict(stored, available=True)

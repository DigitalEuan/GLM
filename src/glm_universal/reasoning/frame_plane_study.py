"""``glm_universal.reasoning.frame_plane_study`` -- the marks of part B of
``studies/COLOUR_INDUCTION_STUDY.md`` (Phase 178): ``tool frame`` in 1+2
dimensions, and the generator the two improper studies (Phases 179, 181)
reuse so their measurements are comparable.

*Created 22 October 2026.*

*Reconstructed 29 October 2026 (Iteration 2 of the reorganisation): the
generator's seven exports (``_Rng``, ``_turn``, ``_u``, ``_matrix``,
``_timelike``, ``_grade``, ``_SCALES``) were rebuilt from their call sites in
``improper_frame_study.py`` and ``improper_units_study.py``; the measurement
was left a stub.*

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation; rebuilt from ``MASTER_PLAN.md`` (Phase 178,
part B: marks P1-P6, L, T; 1,080 queries inside the families, 360 outside;
Thomas--Wigner 60 of 60 with the exact Wigner rotation; 2-component tasks
unchanged, 200 of 200; the first take's 6 wrong outside from rank-deficient
demonstrations, fixed by the span guard), ``studies/IMPROPER_FRAME_STUDY.md``
(§0 and §7.2: the families inside and outside, the 240 reflect and
time-reverse queries), ``SYSTEM.md`` and ``studies/GLM_ACADEMIC_PAPER.md``
§20.52.  The 29 October stub's measurement (every mark set without reading
anything, ``L`` set true without reading ``LorentzPlane.lean``) is replaced by
a real one.  ``_grade`` no longer fails on an undefined name (``Mapping``),
which had stopped both improper studies.  The samplers were made
non-degenerate (no zero boost, no zero turn, no unit scale, timelike states
drawn rather than picked from a list of nineteen) and ``lorentz`` is a boost
along a rotated axis times a rotation (the 29 October version was a pure
boost, the same map as ``boost``).  The marks' wording below is this
reconstruction's, written into this module before its first run; the
figures are this generator's, not the lost original's.*

What is measured
----------------
Twelve task families on exact rational states ``(E, px, py)``, thirty queries
each at one, two, three and four demonstrations.  *Inside the Phase 178
families* (1,080 queries): ``identity``, ``units``, ``rotation``,
``boost_x``, ``boost_y``, ``boost`` (a pure boost along a rotated axis),
``lorentz`` (a boost along a rotated axis times a rotation), ``thomas``
(``B_x(u) B_y(v)``: a boost times its Wigner rotation) and
``lorentz_units``.  *Outside them* (360 queries): ``reflect`` (``py ->
-py``), ``time_reverse`` (``E -> -E``) and ``shear``.  The reflection and the
time reversal have been declared families since Phase 179, so the shipped
solver now answers them; ``shear`` stays outside.  Solvers: **shipped**
(:func:`frame_plane.solve`, every family), **Phase 178** (the same gate over
the six families of Phase 178), **first fit** (the first family not ruled
out answers).

The marks (this reconstruction's wording, fixed before its first run)
---------------------------------------------------------------------
* **P1** shipped: 0 wrong on the nine families inside, every demonstration
  count;
* **P2** at three demonstrations at least 95 % of the queries inside answered
  right;
* **P3** outside the Phase 178 families: 0 wrong, every demonstration count
  (the first take of Phase 178 gave 6 wrong from rank-deficient
  demonstrations; the span guard is the fix);
* **P4** Thomas--Wigner: every ``thomas`` query at three or more
  demonstrations answered right, with the Wigner rotation of the true map,
  and named not a pure boost;
* **P5** the gate earns its keep: the first-fit control gives at least one
  wrong answer;
* **P6** 2-component tasks unchanged: on 200 tasks on ``(E, p)`` from the
  Phase 177 generator, ``tool frame`` and :func:`frame_plane.frame_tool_text`
  give exactly :func:`frame_operators.frame_text`'s verdict and answer;
* **L** ``LorentzPlane.lean`` states its thirteen theorems with no ``sorry``
  (read through :func:`glm_universal.constants.lean_file`; not met when the
  file is missing);
* **T** ``tool frame`` answers the three-pair task of ``B_x(1/2) B_y(1/2)``
  with the Wigner rotation ``15/17,-8/17`` and refuses its one-pair version.

Exactness
---------
``Fraction`` only (D7).
"""
from __future__ import annotations

import json
from fractions import Fraction as F
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .. import integrity
from . import frame_plane as fp

__all__ = [
    "DATA_PATH", "QUERIES", "DEMOS", "INSIDE", "OUTSIDE", "_SOURCES",
    "LEAN_FILE", "LEAN_THEOREMS", "_Rng", "_turn", "_u", "_matrix",
    "_timelike", "_grade", "_SCALES", "task", "synthetic", "two_component",
    "compute", "measure", "write_measurements", "measurements", "state",
    "current", "module_digest", "frame_plane_report", "_plain",
]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent
DATA_PATH = _HERE / "_data" / "frame_plane_study.json"
QUERIES = 30
DEMOS: Tuple[int, ...] = (1, 2, 3, 4)
TWO_COMPONENT_TASKS = 200

#: The Lean file of part B and its theorems (``frame_plane.LEAN_FILE``).
LEAN_FILE = fp.LEAN_FILE
LEAN_THEOREMS: Tuple[str, ...] = fp.LEAN_THEOREMS

INSIDE: Tuple[str, ...] = ("identity", "units", "rotation", "boost_x",
                           "boost_y", "boost", "lorentz", "thomas",
                           "lorentz_units")
OUTSIDE: Tuple[str, ...] = ("reflect", "time_reverse", "shear")

#: Files whose digest ``module_digest`` covers.  The improper studies list
#: this module in their own ``_SOURCES``, so a change here invalidates them.
_SOURCES: Tuple[str, ...] = (
    "reasoning/frame_plane_study.py",
    "reasoning/frame_plane.py",
    "reasoning/frame_operators.py",
    "reasoning/frame_operator_study.py",
    "runtime/toolbox.py",
)

#: The changes of units drawn by the ``*_units`` families: Phase 177's
#: scales (``frame_operator_study._SCALES``), positive and never 1.
_SCALES: Tuple[F, ...] = (F(2), F(1, 2), F(3), F(3, 2), F(2, 3), F(5, 2),
                          F(4, 3), F(3, 4))

#: ``B_x(1/2) B_y(1/2)`` on three inputs (the outputs computed by
#: :func:`frame_plane.matvec`; ``LorentzPlane.thomas_wigner``'s example).
TOOL_PAIRS = ("1,0,0 -> 25/9,-20/9,-4/3", "2,1,0 -> 38/9,-25/9,-8/3",
              "2,0,1 -> 10/3,-8/3,-1")
TOOL_QUERY = "3,1,1"
TOOL_WIGNER = "15/17,-8/17"

_cache: Optional[Dict[str, object]] = None


# ---------------------------------------------------------------------------
# Deterministic RNG (no ``random`` module -- project rule)
# ---------------------------------------------------------------------------

class _Rng:
    """A deterministic, seed-stable pseudo-random generator.

    xorshift64* on a 64-bit integer state, so the same seed always produces
    the same sequence.  ``next(n)`` returns an int in ``[0, n)``.
    """

    __slots__ = ("_state",)

    def __init__(self, seed: int) -> None:
        # Avoid a zero state (xorshift would stick at zero).
        self._state = (int(seed) & 0xFFFFFFFFFFFFFFFF) or 0x9E3779B97F4A7C15

    def next(self, n: int) -> int:
        """Return an int in ``[0, n)``, advancing the state."""
        if n <= 0:
            raise ValueError("n must be positive")
        x = self._state
        x ^= x >> 12
        x ^= (x << 25) & 0xFFFFFFFFFFFFFFFF
        x ^= x >> 27
        self._state = x
        mixed = (x * 0x2545F4914F6CDD1D) & 0xFFFFFFFFFFFFFFFF
        return int((mixed >> 11) % n)


# ---------------------------------------------------------------------------
# Samplers
# ---------------------------------------------------------------------------

def _ratio(rng: _Rng) -> F:
    """A non-zero ``m/n`` with ``1 <= |m| < n <= 7`` (Phase 177's
    ``_param``)."""
    n = 2 + rng.next(6)
    m = 1 + rng.next(n - 1)
    return F(m if rng.next(2) else -m, n)


def _turn(rng: _Rng) -> Tuple[F, F]:
    """A rational point ``(c, s)`` of the unit circle other than ``(1, 0)``,
    from the slope ``t`` of :func:`_ratio`: ``c = (1 - t²)/(1 + t²)``,
    ``s = 2t/(1 + t²)``."""
    t = _ratio(rng)
    d = 1 + t * t
    return ((1 - t * t) / d, (2 * t) / d)


def _u(rng: _Rng) -> F:
    """A boost parameter ``u`` with ``0 < |u| < 1`` (``frame_plane.boost_x``
    takes ``cosh = (1+u²)/(1-u²)``)."""
    return _ratio(rng)


def _scaled(scale: F, mat: fp.Mat) -> fp.Mat:
    """Multiply a matrix by a scalar ``scale`` (a change of units)."""
    return tuple(tuple(scale * x for x in row) for row in mat)


def _boost_any(rng: _Rng) -> fp.Mat:
    """A pure boost along a rotated axis: ``R B_x(u) R^-1``."""
    c, s = _turn(rng)
    return fp.matmul(fp.matmul(fp.rot(c, s), fp.boost_x(_u(rng))),
                     fp.rot(c, -s))


def _lorentz(rng: _Rng) -> fp.Mat:
    """A proper orthochronous Lorentz map: a boost along a rotated axis times
    a rotation."""
    return fp.matmul(_boost_any(rng), fp.rot(*_turn(rng)))


def _matrix(name: str, rng: _Rng) -> fp.Mat:
    """The 3x3 matrix of a task of the named family."""
    if name == "identity":
        return fp.IDENT
    if name == "units":
        return _scaled(_SCALES[rng.next(len(_SCALES))], fp.IDENT)
    if name == "rotation":
        return fp.rot(*_turn(rng))
    if name == "boost_x":
        return fp.boost_x(_u(rng))
    if name == "boost_y":
        return fp.boost_y(_u(rng))
    if name == "boost":
        return _boost_any(rng)
    if name == "lorentz":
        return _lorentz(rng)
    if name == "lorentz_units":
        sc = _SCALES[rng.next(len(_SCALES))]
        return _scaled(sc, _lorentz(rng))
    if name == "thomas":
        return fp.matmul(fp.boost_x(_u(rng)), fp.boost_y(_u(rng)))
    if name == "reflect":
        return fp.PARITY
    if name == "time_reverse":
        return fp.TIME_REV
    if name == "shear":
        k = _ratio(rng)
        return ((F(1), F(0), F(0)), (F(0), F(1), k), (F(0), F(0), F(1)))
    raise KeyError(name)


def _timelike(rng: _Rng) -> fp.State3:
    """A future-pointing massive state: integer ``E`` in ``2..9`` and integer
    ``px, py`` with ``px² + py² < E²``."""
    e = 2 + rng.next(8)
    while True:
        px = rng.next(2 * e - 1) - (e - 1)
        py = rng.next(2 * e - 1) - (e - 1)
        if px * px + py * py < e * e:
            return (F(e), F(px), F(py))


def _grade(r: Mapping, qy: fp.State3) -> str:
    """Grade a ``fp.solve`` result against the true output: ``right``,
    ``wrong`` or ``refused``."""
    if not isinstance(r, Mapping) or r.get("status") != "answered":
        return "refused"
    return "right" if r.get("answer") == qy else "wrong"


def task(name: str, seed: int, demos: int):
    """``(pairs, (query, truth), matrix)`` for one task: ``demos``
    demonstrations with distinct inputs and a distinct query input."""
    rng = _Rng(seed * 7919 + sum(ord(c) for c in name) + 178)
    m = _matrix(name, rng)
    xs: List[fp.State3] = []
    while len(xs) < demos + 1:
        x = _timelike(rng)
        if x not in xs:
            xs.append(x)
    pairs = [(x, fp.matvec(m, x)) for x in xs[:demos]]
    q = xs[demos]
    return pairs, (q, fp.matvec(m, q)), m


# ---------------------------------------------------------------------------
# The measurement
# ---------------------------------------------------------------------------

def _blank() -> Dict[str, int]:
    return {"queries": 0, "right": 0, "wrong": 0, "refused": 0}


def synthetic() -> Dict[str, object]:
    solvers = ("shipped", "phase_178", "first_fit")
    sides = ("inside", "outside")
    totals = {s: {side: _blank() for side in sides} for s in solvers}
    by_demos = {str(d): {side: _blank() for side in sides} for d in DEMOS}
    fams = {f: {s: _blank() for s in solvers} for f in INSIDE + OUTSIDE}
    thomas = {"queries": 0, "right": 0, "wigner_exact": 0, "not_pure": 0}
    statuses: Dict[str, int] = {}
    for fam in INSIDE + OUTSIDE:
        side = "inside" if fam in INSIDE else "outside"
        for d in DEMOS:
            for q in range(QUERIES):
                pairs, (qx, qy), m = task(fam, q + 1000 * d, d)
                res = {"shipped": fp.solve(pairs, qx),
                       "phase_178": fp.solve(
                           pairs, qx, families=fp.PHASE_178_FAMILIES),
                       "first_fit": fp.first_fit(pairs, qx)}
                for s, r in res.items():
                    g = _grade(r, qy)
                    totals[s][side]["queries"] += 1
                    totals[s][side][g] += 1
                    fams[fam][s]["queries"] += 1
                    fams[fam][s][g] += 1
                sh = res["shipped"]
                g = _grade(sh, qy)
                by_demos[str(d)][side]["queries"] += 1
                by_demos[str(d)][side][g] += 1
                statuses[sh["status"]] = statuses.get(sh["status"], 0) + 1
                if fam == "thomas" and d >= 3:
                    thomas["queries"] += 1
                    if g == "right":
                        thomas["right"] += 1
                        thomas["wigner_exact"] += (
                            sh.get("wigner") == fp.wigner(m)[1])
                        thomas["not_pure"] += sh.get("pure_boost") is False
    return {"totals": totals, "by_demos": by_demos, "families": fams,
            "thomas": thomas, "statuses": statuses}


def two_component() -> Dict[str, object]:
    """``tool frame`` on 2-component tasks, against the Phase 177 tool."""
    from . import frame_operator_study as fos
    from . import frame_operators as fo
    from ..runtime.toolbox import run_tool
    names = fos.TASKS
    same_text = same_tool = 0
    differ: List[str] = []
    for i in range(TWO_COMPONENT_TASKS):
        name = names[i % len(names)]
        n = (1, 2, 3)[(i // len(names)) % 3]
        _t, _p, demos, query = fos.sample(name, "timelike", n, 500 + i)
        arg = (" ; ".join(f"{fo.state_text(x)} -> {fo.state_text(y)}"
                          for x, y in demos) + f" ? {fo.state_text(query)}")
        ok0, _x0, f0 = fo.frame_text(arg)
        want = (ok0, f0.get("status"), f0.get("answer"))
        ok1, _x1, f1 = fp.frame_tool_text(arg)
        if (ok1, f1.get("status"), f1.get("answer")) == want:
            same_text += 1
        t = run_tool(f"tool frame {arg}")
        if (t.ok, t.figures.get("status"), t.figures.get("answer")) == want:
            same_tool += 1
        else:
            differ.append(f"{name}/{n}/{i}")
    return {"tasks": TWO_COMPONENT_TASKS, "same_text": same_text,
            "same_tool": same_tool, "differ": differ[:20]}


def _lean() -> Dict[str, object]:
    from ..constants import LEAN_HOLDING_DIR, lean_file
    path = lean_file(LEAN_FILE)          # built tree, or awaiting_recovery/
    present = path.is_file()
    text = path.read_text(encoding="utf-8") if present else ""
    found = [t for t in LEAN_THEOREMS if f"theorem {t}" in text]
    return {"file": LEAN_FILE, "present": present,
            "declared": len(LEAN_THEOREMS), "theorems": len(found),
            "sorry": text.count("sorry"),
            "held": present and LEAN_HOLDING_DIR in path.parents}


def _tool() -> Dict[str, object]:
    from ..runtime.toolbox import run_tool
    r3 = run_tool(f"tool frame {' ; '.join(TOOL_PAIRS)} ? {TOOL_QUERY}")
    r1 = run_tool(f"tool frame {TOOL_PAIRS[0]} ? {TOOL_QUERY}")
    return {"answer_ok": r3.ok, "answer": r3.figures.get("answer"),
            "wigner": r3.figures.get("wigner"),
            "pure_boost": r3.figures.get("pure_boost"),
            "refuse_ok": r1.ok, "refuse_status": r1.figures.get("status")}


def _expected_tool_answer() -> str:
    m = fp.matmul(fp.boost_x(F(1, 2)), fp.boost_y(F(1, 2)))
    return fp.state_text(fp.matvec(m, fp.parse_state3(TOOL_QUERY)))


def _marks(r: Dict[str, object]) -> Dict[str, bool]:
    s = r["synthetic"]
    t = s["totals"]
    three = s["by_demos"]["3"]["inside"]
    th = s["thomas"]
    two = r["two_component"]
    lean = r["lean"]
    tool = r["tool"]
    ff_wrong = (t["first_fit"]["inside"]["wrong"]
                + t["first_fit"]["outside"]["wrong"])
    return {
        "P1": t["shipped"]["inside"]["queries"] > 0
        and t["shipped"]["inside"]["wrong"] == 0,
        "P2": three["queries"] > 0
        and 100 * three["right"] >= 95 * three["queries"],
        "P3": t["shipped"]["outside"]["queries"] > 0
        and t["shipped"]["outside"]["wrong"] == 0,
        "P4": th["queries"] > 0 and th["right"] == th["queries"]
        and th["wigner_exact"] == th["queries"]
        and th["not_pure"] == th["queries"],
        "P5": ff_wrong > 0,
        "P6": two["same_text"] == two["tasks"]
        and two["same_tool"] == two["tasks"],
        "L": (lean["present"] and lean["theorems"] == lean["declared"]
              and lean["sorry"] == 0),
        "T": (tool["answer_ok"] and tool["answer"] == _expected_tool_answer()
              and tool["wigner"] == TOOL_WIGNER and not tool["refuse_ok"]),
    }


def compute() -> Dict[str, object]:
    """Run the Phase 178 part B measurement and return the report."""
    report: Dict[str, object] = {
        "phase": 178, "synthetic": synthetic(),
        "two_component": two_component(), "lean": _lean(), "tool": _tool(),
        "queries": QUERIES, "demos": list(DEMOS), "inside": list(INSIDE),
        "outside": list(OUTSIDE)}
    marks = _marks(report)
    report["marks"] = marks
    report["met"] = sum(1 for v in marks.values() if v)
    report["taken"] = len(marks)
    return report


# ---------------------------------------------------------------------------
# Stored measurement
# ---------------------------------------------------------------------------

def _plain(x: Any) -> Any:
    """Recursive serializer: Fraction -> str, dict/list -> plain."""
    if isinstance(x, F):
        return str(x)
    if isinstance(x, dict):
        return {str(k): _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


def module_digest() -> str:
    """The digest of every file in :data:`_SOURCES`, relative to the package root."""
    root = _HERE.parent  # glm_universal/ (the package root)
    paths = [root / n for n in sorted(set(_SOURCES))]
    return integrity.tree_digest(paths, root)


def measure() -> Dict[str, object]:
    """``compute()`` plus the ``source_digest``."""
    r = compute()
    r["source_digest"] = module_digest()
    return r


def write_measurements(path: Optional[Path] = None) -> Path:
    """Write ``measure()`` as JSON to :data:`DATA_PATH` (or ``path``)."""
    out = path if path is not None else DATA_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_plain(measure()), indent=1, sort_keys=True,
                      ensure_ascii=False) + "\n"
    out.write_text(text, encoding="utf-8")
    global _cache
    _cache = None
    return out


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """Read the stored measurement from :data:`DATA_PATH`, or ``None`` if absent."""
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
    """``{"present", "fresh", "verdict", "live_digest", "stored_digest"}``."""
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
    """``measurements()`` if fresh, else ``None``."""
    s = state()
    if s["fresh"]:
        return measurements()
    return None


def frame_plane_report() -> Dict[str, object]:
    """If fresh: the stored measurement with ``available=True``.  Else: a
    reason and the command to re-take it."""
    stored = current()
    if stored is not None:
        out = dict(stored)
        out["available"] = True
        return out
    s = state()
    return {
        "available": False,
        "reason": (f"the stored measurement is {s['verdict']}; re-take it with "
                   f"python3 -m glm_universal.tools frame-plane --write"),
    }

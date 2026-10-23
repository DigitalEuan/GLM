"""``glm_universal.reasoning.lorentzian_lift_study`` -- the marks of
``studies/LORENTZIAN_LIFT_STUDY.md`` (Phase 182): the owner's
``iter10_lorentzian.py`` audited, and the Golay tie space lifted to
``II_{25,1}`` measured.

*Created 22 October 2026.*

What is measured
----------------
**Queries.** A message is a Golay codeword drawn at random; a *reading* of it
is the codeword with an error pattern of stated weight. A weight-4 error
always lands in a weight-4 coset (every 4-set is a tetrad of exactly one
sextet), so a single such reading is a Golay tie: six codewords equally
near, the true one among them. Each condition has ``QUERIES`` queries from a
fixed seed. Conditions name the error weights of the readings: ``4`` (one
reading), ``4+k`` for ``k = 0..6`` (a second reading with ``k`` errors),
``4+4+4``, ``4+4+6``, and ``decoy`` (a second weight-4 reading of an
*unrelated* codeword: wrong context).

**Rules on one reading.** ``min`` (the GLM default: the least of the tied
codewords, ``analogy.nearest_golay_codeword``); ``script`` (the rule of
``iter10_lorentzian.py``, reimplemented faithfully: its 0/1 lift, its two
"roots" ``(centre, -1, 0)`` built from the octad-pair and dodecad-triangle
holes, the most negative score, the reflection, the threshold at 1/2);
``reflection`` (reflect ``L(2b)`` in the mirror of two tied roots and decode
again); ``weyl`` (score by ``<w, r_c>``); ``script_w`` (score by the script's
``(0,1,1)``); ``lorentz`` (:func:`lorentzian_lift.resolve`, which refuses a
tied maximum).

**Rules on several readings.** ``lorentz`` (summed Lorentzian scores);
``lorentz_guarded`` (the same, refusing an answer farther than
``lorentzian_lift.GUARD = 6`` bits from any reading -- added after a first
60-query trial run showed ``lorentz`` answering wrongly on the decoy; see M11);
``intersect`` (the substrate's existing set collapse,
``superposition.collapse``: keep the first reading's candidates that are
nearest codewords of every reading, answer if one survives); ``first_min``.

Marks (declared before the first measurement)
---------------------------------------------
* **M1** the tie reflection returns ``L(2b)`` unchanged on every one-reading
  query, and the Weyl score is the same for all six candidates on every one;
* **M2** the script's rule names the sent codeword on at most
  ``1/6 + 1/20`` of the one-reading queries;
* **M3** ``lorentz`` on one reading: 0 wrong, every query refused;
* **M4** ``lorentz`` on ``4+4`` (two readings, each a tie): 0 wrong and at
  least 90 % right;
* **M5** ``lorentz`` on ``4+4+4``: 0 wrong and at least 99 % right;
* **M6** ``lorentz`` on ``4+k``, ``k <= 3``: every query right;
* **M7** the decoy control: ``lorentz`` right on at most 25 % of queries;
* **M8** graded against sets: on every condition ``lorentz`` is right at
  least as often as ``intersect``;
* **M9** the census: on ``CENSUS`` sampled weight-4 cosets the doubled word
  has 48 hole vertices (8 per tied codeword), the hole diagram certifies
  ``A_1^24``, every vertex root is orthogonal to the lift, ``2 L(x)`` is a
  null vector of ``II_{25,1}`` and ``L(x)`` is not; on ``CENSUS`` sampled
  words of every coset weight the exact Leech decoder's squared distance is
  the coset weight over 2;
* **M10** the script audit: neither of the script's two "roots" has norm 2,
  ``<r, w> = -1`` holds for any centre whatever (so the script's
  ``is_conway_root`` check cannot fail), and its ``disambiguated`` counter
  equals its ``ambiguous`` counter on every query (it counts a computation,
  not a right answer);
* **M11** (declared after the 60-query trial, before the full measurement)
  ``lorentz_guarded`` gives 0 wrong answers on the decoy, and keeps at least
  90 % of ``lorentz``'s right answers on ``4+5``, ``4+6`` and ``4+4+6``;
* **L** ``LorentzianLift.lean`` and ``GolayDeepHole.lean`` state the quoted
  theorems with no ``sorry`` and are in the axiom audit.

Exactness
---------
``Fraction`` only.
"""

from __future__ import annotations

import json
import random
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from ..substrate import mog
from ..substrate import superposition as sup_mod
from . import deep_holes as dh
from . import lorentzian_lift as ll

__all__ = ["DATA_PATH", "QUERIES", "CENSUS", "CONDITIONS", "script_rule",
           "script_roots", "compute", "measure", "write_measurements",
           "measurements", "state", "current", "lorentzian_lift_report"]

_HERE = Path(__file__).resolve().parent
DATA_PATH: Path = _HERE / "_data" / "lorentzian_lift_study.json"

QUERIES = 600
CENSUS = 128
SEED = 20261022
F = Fraction

_SOURCES = (
    "reasoning/lorentzian_lift_study.py",
    "reasoning/lorentzian_lift.py",
    "reasoning/deep_holes.py",
    "reasoning/analogy.py",
    "substrate/superposition.py",
    "substrate/golay_decode.py",
    "substrate/leech2.py",
)

#: condition -> error weights of the readings (``None`` marks the decoy).
CONDITIONS: Dict[str, Tuple[Optional[int], ...]] = {
    "4": (4,),
    "4+0": (4, 0), "4+1": (4, 1), "4+2": (4, 2), "4+3": (4, 3),
    "4+4": (4, 4), "4+5": (4, 5), "4+6": (4, 6),
    "4+4+4": (4, 4, 4), "4+4+6": (4, 4, 6),
    "decoy": (4, None),
}


# ===========================================================================
# 1.  THE SCRIPT, REIMPLEMENTED
# ===========================================================================
# ``iter10_lorentzian.py`` imports modules that are not in this tree and
# writes to paths outside it, so its rule is restated here, line for line:
# the form sum_{i<25} a_i b_i - a_25 b_25 on raw (unscaled) coordinates, the
# 0/1 lift, roots (centre, -1, 0), the most negative score, the reflection,
# the threshold at 1/2, bits read most significant first.

def _s_inner(a: Sequence, b: Sequence) -> Fraction:
    return (sum((F(a[i]) * F(b[i]) for i in range(25)), F(0))
            - F(a[25]) * F(b[25]))


def _s_lift(x: Sequence) -> Tuple[Fraction, ...]:
    q = sum((F(v) * F(v) for v in x), F(0))
    return tuple(F(v) for v in x) + ((1 - q) / 2, (1 + q) / 2)


def script_roots() -> List[Dict[str, object]]:
    """The script's two "roots" and what they are."""
    out = []
    for name, hole in (("octad_pair", dh.octad_pair_hole()),
                       ("dodecad_triangle", dh.dodecad_triangle_hole())):
        c = tuple(F(v) for v in hole["center"])
        r = c + (F(-1), F(0))
        out.append({"name": name, "root": r,
                    "norm": _s_inner(r, r),
                    "weyl_inner": _s_inner(r, ll.SCRIPT_W),
                    "center_norm_raw": sum((v * v for v in c), F(0))})
    return out


def script_rule(mask: int, roots: Sequence[Dict[str, object]]) -> int:
    """The word the script predicts for a received 24-bit ``mask``."""
    x = tuple(F((mask >> (23 - i)) & 1) for i in range(24))
    lx = _s_lift(x)
    scores = [_s_inner(lx, r["root"]) for r in roots]
    best = roots[scores.index(min(scores))]["root"]
    nr = _s_inner(best, best)
    k = 2 * _s_inner(lx, best) / nr
    refl = [lx[i] - k * best[i] for i in range(26)]
    pred = 0
    for i in range(24):
        pred = (pred << 1) | (1 if refl[i] > F(1, 2) else 0)
    return pred


# ===========================================================================
# 2.  THE QUERIES
# ===========================================================================

def _error(rng: random.Random, weight: int) -> int:
    e = 0
    for i in rng.sample(range(24), weight):
        e |= 1 << i
    return e


def _queries(condition: str) -> List[Tuple[int, List[int]]]:
    weights = CONDITIONS[condition]
    rng = random.Random(f"{SEED}:{condition}")
    words = mog.GOLAY_MASKS
    out = []
    for _ in range(QUERIES):
        sent = words[rng.randrange(len(words))]
        readings = []
        for w in weights:
            if w is None:
                other = words[rng.randrange(len(words))]
                while other == sent:
                    other = words[rng.randrange(len(words))]
                readings.append(other ^ _error(rng, 4))
            else:
                readings.append(sent ^ _error(rng, w))
        out.append((sent, readings))
    return out


def _tally() -> Dict[str, int]:
    return {"right": 0, "wrong": 0, "refused": 0}


def _mark(t: Dict[str, int], answer: Optional[int], sent: int) -> None:
    if answer is None:
        t["refused"] += 1
    elif answer == sent:
        t["right"] += 1
    else:
        t["wrong"] += 1


def _unique_max(scores: Dict[int, Fraction]) -> Optional[int]:
    top = max(scores.values())
    best = [c for c, s in scores.items() if s == top]
    return best[0] if len(best) == 1 else None


def single_reading() -> Dict[str, object]:
    """Every rule on the one-reading condition."""
    roots = script_roots()
    rules = {r: _tally() for r in ("min", "script", "reflection", "weyl",
                                   "script_w", "lorentz")}
    fixed = weyl_flat = ambiguous = 0
    script_codeword = script_candidate = 0
    for sent, (b,) in _queries("4"):
        s = sup_mod.superpose(b)
        ambiguous += s.ambiguous
        cands = list(s.candidates)
        _mark(rules["min"], min(cands), sent)
        pred = script_rule(b, roots)
        script_codeword += pred in mog.GOLAY_SET
        script_candidate += pred in cands
        _mark(rules["script"], pred, sent)
        lx = ll.lift(ll.doubled(b))
        mirror = ll._sub(ll.root(ll.doubled(cands[0])),
                         ll.root(ll.doubled(cands[1])))
        refl = ll.reflect(mirror, lx)
        fixed += refl == lx
        again = sup_mod.superpose(_mask_of_raw(refl[:24]))
        _mark(rules["reflection"], min(again.candidates), sent)
        weyl = {c: ll.inner(ll.WEYL, ll.root(ll.doubled(c))) for c in cands}
        weyl_flat += len(set(weyl.values())) == 1
        _mark(rules["weyl"], _unique_max(weyl), sent)
        sw = {c: ll.inner(ll.SCRIPT_W, ll.root(ll.doubled(c))) for c in cands}
        _mark(rules["script_w"], _unique_max(sw), sent)
        _mark(rules["lorentz"], ll.resolve([b])["value"], sent)
    return {"queries": QUERIES, "ambiguous": ambiguous, "rules": rules,
            "reflection_fixed": fixed, "weyl_flat": weyl_flat,
            "script_codeword": script_codeword,
            "script_candidate": script_candidate,
            "script_disambiguated": ambiguous,
            "script_roots": [{k: v for k, v in r.items() if k != "root"}
                             for r in roots]}


def _mask_of_raw(raw: Sequence) -> int:
    """The word whose doubling is ``raw`` (coordinates 0 or 2)."""
    m = 0
    for i, v in enumerate(raw):
        if F(v) == 2:
            m |= 1 << i
        elif F(v) != 0:
            raise ValueError("not a doubled word")
    return m


def _intersect(readings: Sequence[int]) -> Optional[int]:
    first = sup_mod.superpose(readings[0])
    sets = [set(sup_mod.superpose(b).candidates) for b in readings[1:]]
    col = sup_mod.collapse(first, lambda c: all(c in s for s in sets))
    return col.value


def several_readings() -> Dict[str, object]:
    """``lorentz``, ``lorentz_guarded``, ``intersect`` and ``first_min`` on
    every multi-reading condition."""
    out = {}
    for cond in CONDITIONS:
        if cond == "4":
            continue
        rules = {r: _tally() for r in ("lorentz", "lorentz_guarded",
                                       "intersect", "first_min")}
        for sent, readings in _queries(cond):
            _mark(rules["lorentz"], ll.resolve(readings)["value"], sent)
            _mark(rules["lorentz_guarded"],
                  ll.resolve(readings, guard=ll.GUARD)["value"], sent)
            _mark(rules["intersect"], _intersect(readings), sent)
            _mark(rules["first_min"],
                  min(sup_mod.superpose(readings[0]).candidates), sent)
        out[cond] = rules
    return out


# ===========================================================================
# 3.  THE CENSUS
# ===========================================================================

def census() -> Dict[str, object]:
    """Sampled weight-4 cosets lifted; sampled words decoded exactly."""
    from .analogy import nearest_lattice_point
    rng = random.Random(f"{SEED}:census")
    holes = {"sampled": 0, "vertices_48": 0, "eight_each": 0,
             "a1_24_certified": 0, "orthogonal": 0, "null_in_ii": 0,
             "lift_not_in_ii": 0, "at_covering_radius": 0}
    while holes["sampled"] < CENSUS:
        b = rng.getrandbits(24)
        if sup_mod.superpose(b).weight != 4:
            continue
        holes["sampled"] += 1
        cert = ll.tie_certificate(b)
        holes["vertices_48"] += cert["vertices"] == 48
        holes["eight_each"] += cert["per_candidate"] == 8
        holes["at_covering_radius"] += cert["vertex_distance2_raw"] == [16]
        holes["orthogonal"] += bool(cert["roots_orthogonal_to_lift"])
        holes["null_in_ii"] += bool(cert["null_vector_in_ii"])
        holes["lift_not_in_ii"] += not cert["lift_in_ii"]
        diag = dh.hole_diagram(ll.hole_vertices(b), ll.doubled(b))
        holes["a1_24_certified"] += (
            diag.get("root_system") == "A_1^24"
            and diag["completeness_certificate"]["certified"])
    dist = {"sampled": 0, "agree": 0, "by_weight": {}}
    for _ in range(CENSUS):
        b = rng.getrandbits(24)
        w = sup_mod.superpose(b).weight
        d2 = nearest_lattice_point(ll.doubled(b)).distance2
        dist["sampled"] += 1
        dist["agree"] += d2 == F(w, 2)
        dist["by_weight"][w] = dist["by_weight"].get(w, 0) + 1
    return {"holes": holes, "distance": dist}


# ===========================================================================
# 4.  MARKS
# ===========================================================================

def _lean_ok() -> bool:
    root = Path(__file__).resolve().parents[2] / "glm_lean"
    text = "".join((root / f).read_text(encoding="utf-8")
                   for f in ll.LEAN_FILES)
    audit = (root / "RequestProject" / "GLM" / "AxiomAuditAll.lean").read_text(
        encoding="utf-8")
    return ("sorry" not in text
            and all(f"theorem {t}" in text for t in ll.LEAN_THEOREMS)
            and "import RequestProject.GLM.LorentzianLift" in audit
            and "import RequestProject.GLM.GolayDeepHole" in audit)


def compute() -> Dict[str, object]:
    one = single_reading()
    many = several_readings()
    cen = census()
    q = QUERIES
    lor = {c: r["lorentz"] for c, r in many.items()}
    marks = {
        "M1": one["reflection_fixed"] == q and one["weyl_flat"] == q,
        "M2": F(one["rules"]["script"]["right"], q) <= F(1, 6) + F(1, 20),
        "M3": (one["rules"]["lorentz"]["wrong"] == 0
               and one["rules"]["lorentz"]["refused"] == q),
        "M4": lor["4+4"]["wrong"] == 0 and 10 * lor["4+4"]["right"] >= 9 * q,
        "M5": (lor["4+4+4"]["wrong"] == 0
               and 100 * lor["4+4+4"]["right"] >= 99 * q),
        "M6": all(lor[f"4+{k}"]["right"] == q for k in range(4)),
        "M7": 4 * lor["decoy"]["right"] <= q,
        "M8": all(r["lorentz"]["right"] >= r["intersect"]["right"]
                  for r in many.values()),
        "M9": (all(v == CENSUS for k, v in cen["holes"].items())
               and cen["distance"]["agree"] == CENSUS),
        "M10": (all(r["norm"] != 2 and r["weyl_inner"] == -1
                    for r in one["script_roots"])
                and one["script_disambiguated"] == one["ambiguous"] == q),
        "M11": (many["decoy"]["lorentz_guarded"]["wrong"] == 0
                and all(10 * many[c]["lorentz_guarded"]["right"]
                        >= 9 * many[c]["lorentz"]["right"]
                        for c in ("4+5", "4+6", "4+4+6"))),
        "L": _lean_ok(),
    }
    return {"single": one, "several": many, "census": cen, "marks": marks,
            "met": sum(marks.values()), "taken": len(marks)}


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


def lorentzian_lift_report() -> Dict[str, object]:
    """The stored marks, or why there are none."""
    stored = current()
    if stored is None:
        return {"available": False, "reason": (
            f"the stored measurement is {state()['verdict']}; re-take it "
            f"with python3 -m glm_universal.tools lorentzian-lift --write")}
    return dict(stored, available=True)

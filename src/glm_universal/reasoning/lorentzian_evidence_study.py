"""``glm_universal.reasoning.lorentzian_evidence_study`` -- the marks of
``studies/LORENTZIAN_EVIDENCE_STUDY.md`` (Phase 183): the Lorentzian lift as an
evidence space for reasoning in general.

*Created 23 October 2026.*

What is measured
----------------
Three surfaces, from the Golay tie space Phase 182 left to two registers that
have nothing to do with codes.

**Golay (``G``).** Phase 182's own queries (``lorentzian_lift_study._queries``,
same seed): every condition, with three rules beside Phase 182's guarded
summed score (``guarded``): ``certificate`` (the answer must also be one of
the first reading's tied candidates, ``lorentzian_evidence.certificate_resolve``),
``dispersion`` (``guarded`` plus a refusal when the readings' dispersion, in
the Leech scale, exceeds the channel budget ``(4 + 6 (k - 1)) / 2`` --
``dispersion_guard_sound`` says an honest set never exceeds it) and, on the
single tied readings, the **settling question**: the sent bits at the five
positions ``lorentzian_evidence.settling_question`` names, against five
positions drawn at random.

**Physics relations (``P``).** A relation is a displacement of EXT10
exponents, taken from the thirteen curated physics analogies of
``benchmarks/suites.py``; its examples are register pairs ``(a, b)`` with
``exps(b) - exps(a)`` equal to it; a query applies it to a register quantity
``c``. Conditions: ``clean1``, ``clean2``, ``clean3`` (one, two, three
examples of the relation) and ``decoy2``, ``decoy3`` (one or two examples
of it and one of a *different* relation, the decoy, in a random position).
A query is answered at the dimension layer: right when the answer is the
class ``exps(c) + d``. Rules: ``first`` (the first example alone),
``lorentz`` (the consensus of the examples' targets, nearest class, a tie
refused), ``guarded`` (``lorentzian_evidence.relation_answer``: refused when
the targets' dispersion is not zero) and ``vote`` (the majority target, a tie
refused). Plus the **name layer** on the thirteen curated analogies: the
shipped physics analogy names one quantity; the lifted answer names the
class and refuses the name.

**Semantic relations (``S``).** The 149-word semantic lexicon, the ten
primitive coordinates, and every relation it states between two of its own
words with at least five pairs: ``c`` stands in the relation to its truth set,
the examples are other pairs of the same relation, ``k = 1, 2, 3``, at most
``SEM_CAP`` example sets per query from a fixed seed. Rules ``lorentz`` and
``vote`` as above, and the dispersion of the targets read as a confidence:
the precision of the answers whose dispersion is at most the median, against
the precision of all answers. Here the relations are mostly *not*
displacements (``studies/ANALOGY_LAYER_STUDY.md``), so this is the surface
where the lift is expected to help least.

Marks
-----
Declared before the full measurement. ``G2`` and ``G3`` were written after a
prototype run of the decoy census (which showed the certificate guard's
effect and the dispersion guard's lack of one) and are labelled so in the
study; all others were written before any run of this module.

* **E1** identities: on every sampled evidence set -- doubled Golay readings
  in the Leech scale, physics targets, semantic targets, and analogy cues
  with weights ``1, -1, 1`` -- ``V = W L(xbar) + (D/2) w`` and
  ``<V, V> = -W D`` hold exactly, and with positive weights ``<V, V> = 0``
  exactly when the cues agree;
* **G1** the certificate guard is sound: on every Golay condition it is right
  exactly as often as ``guarded``;
* **G2** *(after the prototype)* on the decoy it gives fewer wrong answers
  than ``guarded``;
* **G3** *(after the prototype)* every wrong answer it still gives on the
  decoy is indistinguishable from an honest reading set: the answer is one
  of the first reading's tied candidates and every other reading lies within
  the guard of it;
* **G4** the dispersion guard is sound: right exactly as often as
  ``guarded`` on every honest condition;
* **G5** the settling question settles every single tied reading to the sent
  codeword, 0 wrong, and on every one of them no four of its five positions
  do;
* **G5b** *(added after a trial run showed G5 mis-states the theorem: four
  positions do settle the sent codeword whenever they meet its own tetrad)*
  on every single tied reading, every four of the five asked positions leave
  some tied candidate unsettled -- the worst case ``card_ge_of_separates``
  is about;
* **G6** five random positions settle fewer tied readings than the asked
  five;
* **P1** ``guarded`` gives 0 wrong answers on every physics condition;
* **P2** on ``clean1``, ``clean2`` and ``clean3`` ``guarded`` is right on every
  query whose target class is in the register and refuses the rest;
* **P3** on ``decoy2`` and ``decoy3`` ``guarded`` refuses every query (the
  dispersion is never 0 when a decoy is present), and ``first`` and
  ``lorentz`` each give at least one wrong answer;
* **P4** name layer: on every curated analogy whose displacement target is a
  class, the expected name is in the class the lifted answer certifies;
* **S1** ``lorentz`` with ``k = 3`` is right at least as often, per query,
  as with ``k = 1``;
* **S2** the low-dispersion half of ``lorentz``'s answers (``k = 2, 3``) is
  more precise than all of them;
* **L** ``LorentzianEvidence.lean`` states the quoted theorems with no
  ``sorry`` and is in the axiom audit.

Exactness
---------
``Fraction`` only.
"""

from __future__ import annotations

import json
import random
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from ..substrate import superposition as sup_mod
from . import lorentzian_evidence as le
from . import lorentzian_lift as ll
from . import lorentzian_lift_study as lls

__all__ = ["DATA_PATH", "SEED", "PHYS_QUERIES", "SEM_CAP", "compute",
           "measure", "write_measurements", "measurements", "state",
           "current", "lorentzian_evidence_report"]

_HERE = Path(__file__).resolve().parent
DATA_PATH: Path = _HERE / "_data" / "lorentzian_evidence_study.json"

SEED = 20261023
PHYS_QUERIES = 300
SEM_CAP = 12
F = Fraction

_SOURCES = (
    "reasoning/lorentzian_evidence_study.py",
    "reasoning/lorentzian_evidence.py",
    "reasoning/lorentzian_lift.py",
    "reasoning/lorentzian_lift_study.py",
    "reasoning/analogy.py",
    "substrate/superposition.py",
    "substrate/golay_decode.py",
    "data_objects/physics.py",
    "data_objects/semantic_lexicon.py",
    "benchmarks/suites.py",
)


def _tally() -> Dict[str, int]:
    return {"right": 0, "wrong": 0, "refused": 0}


def _mark(t: Dict[str, int], answer, truth) -> None:
    if answer is None:
        t["refused"] += 1
    elif answer == truth:
        t["right"] += 1
    else:
        t["wrong"] += 1


def _ham(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


# ===========================================================================
# 1.  GOLAY
# ===========================================================================

def _golay_dispersion(readings: Sequence[int]) -> Fraction:
    cues = [(tuple(F(v) for v in ll.doubled(b)), F(1)) for b in readings]
    return le.dispersion(cues, ll.SCALE)


def golay() -> Dict[str, object]:
    """Every Phase 182 condition under the three guards; the decoy census."""
    out: Dict[str, object] = {}
    decoy_census = {"certificate_wrong": 0, "honest_looking": 0}
    for cond, weights in lls.CONDITIONS.items():
        if cond == "4":
            continue
        rules = {r: _tally() for r in ("guarded", "certificate", "dispersion")}
        triggered = 0
        budget = F(4 + 6 * (len(weights) - 1), 2)
        for sent, readings in lls._queries(cond):
            g = ll.resolve(readings, guard=ll.GUARD)["value"]
            c = le.certificate_resolve(readings, guard=ll.GUARD)["value"]
            over = _golay_dispersion(readings) > budget
            triggered += over
            _mark(rules["guarded"], g, sent)
            _mark(rules["certificate"], c, sent)
            _mark(rules["dispersion"], None if over else g, sent)
            if cond == "decoy" and c is not None and c != sent:
                decoy_census["certificate_wrong"] += 1
                first = sup_mod.superpose(readings[0])
                decoy_census["honest_looking"] += (
                    c in first.candidates
                    and all(_ham(b, c) <= ll.GUARD for b in readings[1:]))
        out[cond] = dict(rules, dispersion_triggered=triggered,
                         budget=budget)
    return {"conditions": out, "decoy_census": decoy_census}


def settling() -> Dict[str, object]:
    """The settling question on Phase 182's single tied readings."""
    rng = random.Random(f"{SEED}:settle")
    asked = _tally()
    rand = _tally()
    no_four = 0
    worst = 0
    sizes = {}
    for sent, (b,) in lls._queries("4"):
        q = le.settling_question(b)
        sizes[len(q)] = sizes.get(len(q), 0) + 1
        st = le.settle(b, {i: (sent >> i) & 1 for i in q})
        _mark(asked, st["value"], sent)
        no_four += all(
            le.settle(b, {i: (sent >> i) & 1 for i in sub})["status"] != "resolved"
            for sub in combinations(q, len(q) - 1))
        cands = sup_mod.superpose(b).candidates
        worst += all(
            any(le.settle(b, {i: (c >> i) & 1 for i in sub})["status"]
                != "resolved" for c in cands)
            for sub in combinations(q, len(q) - 1))
        r = rng.sample(range(24), 5)
        _mark(rand, le.settle(b, {i: (sent >> i) & 1 for i in r})["value"], sent)
    return {"queries": lls.QUERIES, "asked": asked, "random5": rand,
            "no_four_settle": no_four, "no_four_settle_every": worst,
            "question_sizes": sizes}


# ===========================================================================
# 2.  PHYSICS RELATIONS
# ===========================================================================

def _relations(vec) -> List[Tuple[Fraction, ...]]:
    from ..benchmarks.suites import PHYSICS_ANALOGIES
    out: List[Tuple[Fraction, ...]] = []
    for a, b, _, _ in PHYSICS_ANALOGIES:
        d = tuple(y - x for x, y in zip(vec[a], vec[b]))
        if d not in out:
            out.append(d)
    return out


PHYS_CONDITIONS: Dict[str, Tuple[int, bool]] = {
    "clean1": (1, False), "clean2": (2, False), "clean3": (3, False),
    "decoy2": (1, True), "decoy3": (2, True),
}


def _pairs_for(d, vec, names) -> List[Tuple[str, str]]:
    by = {}
    for n in names:
        by.setdefault(vec[n], []).append(n)
    out = []
    for e, ns in by.items():
        t = tuple(x + y for x, y in zip(e, d))
        for a in ns:
            for b in by.get(t, ()):
                out.append((a, b))
    return sorted(out)


def physics() -> Dict[str, object]:
    vec, cls = le.physics_classes()
    names = sorted(vec)
    rels = _relations(vec)
    pools = {d: _pairs_for(d, vec, names) for d in rels}
    rels = [d for d in rels if len(pools[d]) >= 4]
    class_points = {"|".join(map(str, e)): e for e in cls}
    out: Dict[str, object] = {"relations": len(rels)}
    for cond, (k, decoy) in PHYS_CONDITIONS.items():
        rng = random.Random(f"{SEED}:physics:{cond}")
        rules = {r: _tally() for r in ("first", "lorentz", "guarded", "vote")}
        present = absent = 0
        for _ in range(PHYS_QUERIES):
            d = rels[rng.randrange(len(rels))]
            c = names[rng.randrange(len(names))]
            pool = [p for p in pools[d] if c not in p]
            ex = rng.sample(pool, k)
            if decoy:
                d2 = d
                while d2 == d:
                    d2 = rels[rng.randrange(len(rels))]
                bad = [p for p in pools[d2] if c not in p]
                ex.insert(rng.randrange(k + 1), bad[rng.randrange(len(bad))])
            truth = tuple(x + y for x, y in zip(vec[c], d))
            in_reg = truth in cls
            present += in_reg
            absent += not in_reg
            key = truth if in_reg else None
            targets = [x for x, _ in le.target_cues(
                [(vec[a], vec[b]) for a, b in ex], vec[c])]
            first_t = targets[0]
            _mark(rules["first"], first_t if first_t in cls else None, key)
            res = le.decide([(t, F(1)) for t in targets], class_points)
            lv = class_points[res["value"]] if res["value"] else None
            _mark(rules["lorentz"], lv, key)
            ra = le.relation_answer(ex, c, vec, cls)
            _mark(rules["guarded"],
                  ra["target"] if ra["status"] == "class" else None, key)
            counts: Dict[Tuple[Fraction, ...], int] = {}
            for t in targets:
                counts[t] = counts.get(t, 0) + 1
            top = max(counts.values())
            winners = [t for t, v in counts.items() if v == top]
            vt = winners[0] if len(winners) == 1 and winners[0] in cls else None
            _mark(rules["vote"], vt, key)
        out[cond] = dict(rules, present=present, absent=absent)
    return out


def physics_names() -> Dict[str, object]:
    """The thirteen curated analogies at the name layer."""
    from ..benchmarks.suites import PHYSICS_ANALOGIES
    from .analogy import physics_analogy
    vec, cls = le.physics_classes()
    rows = []
    for a, b, c, want in PHYSICS_ANALOGIES:
        ra = le.relation_answer([(a, b)], c, vec, cls)
        shipped = physics_analogy(a, b, c).answer
        rows.append({
            "task": f"{a} : {b} :: {c} : ?", "expected": want,
            "status": ra["status"], "class_size": len(ra["names"]),
            "expected_in_class": want in ra["names"],
            "shipped": shipped, "shipped_right": shipped == want,
            "shipped_class_right": vec.get(shipped) == vec[want],
        })
    return {"rows": rows,
            "class_answers": sum(r["status"] == "class" for r in rows),
            "expected_in_class": sum(r["expected_in_class"] for r in rows),
            "shipped_name_right": sum(r["shipped_right"] for r in rows),
            "shipped_name_wrong": sum(not r["shipped_right"] for r in rows)}


# ===========================================================================
# 3.  SEMANTIC RELATIONS
# ===========================================================================

def semantic() -> Dict[str, object]:
    from ..data_objects import semantic_lexicon as sl
    concepts = sl.SEMANTIC_SAMPLE_CONCEPTS
    prim = sl.SEMANTIC_PRIMITIVE_NAMES
    vec = {c.subject: tuple(F(c.primitives.get(p, sl.DEFAULT_PRIMITIVE))
                            for p in prim) for c in concepts}
    names = sorted(vec)
    rels: Dict[str, set] = {}
    for c in concepts:
        for p, o in c.relations:
            if o in vec and o != c.subject:
                rels.setdefault(p, set()).add((c.subject, o))
    rels = {r: sorted(v) for r, v in rels.items() if len(v) >= 5}
    by_k = {k: {"lorentz": _tally(), "vote": _tally(), "queries": 0}
            for k in (1, 2, 3)}
    conf: List[Tuple[Fraction, bool]] = []
    for r in sorted(rels):
        pairs = rels[r]
        truth: Dict[str, set] = {}
        for a, b in pairs:
            truth.setdefault(a, set()).add(b)
        for c in sorted(truth):
            others = [(a, b) for a, b in pairs if a != c and b != c]
            for k in (1, 2, 3):
                rng = random.Random(f"{SEED}:semantic:{r}:{c}:{k}")
                sets = list(combinations(others, k))
                if len(sets) > SEM_CAP:
                    sets = rng.sample(sets, SEM_CAP)
                for ex in sets:
                    by_k[k]["queries"] += 1
                    cand = {n: vec[n] for n in names if n != c}
                    targets = [x for x, _ in le.target_cues(
                        [(vec[a], vec[b]) for a, b in ex], vec[c])]
                    res = le.decide([(t, F(1)) for t in targets], cand)
                    v = res["value"]
                    ok = v in truth[c] if v is not None else None
                    _tally_set(by_k[k]["lorentz"], ok)
                    if v is not None and k > 1:
                        conf.append((res["dispersion"], bool(ok)))
                    votes: Dict[str, int] = {}
                    for t in targets:
                        one = le.decide([(t, F(1))], cand)["value"]
                        if one is not None:
                            votes[one] = votes.get(one, 0) + 1
                    if votes:
                        top = max(votes.values())
                        win = [n for n, x in votes.items() if x == top]
                        vv = win[0] if len(win) == 1 else None
                    else:
                        vv = None
                    _tally_set(by_k[k]["vote"],
                               None if vv is None else vv in truth[c])
    conf.sort(key=lambda t: t[0])
    half = conf[: (len(conf) + 1) // 2]
    def prec(xs):
        return F(sum(ok for _, ok in xs), len(xs)) if xs else F(0)
    return {"relations": len(rels), "by_k": by_k,
            "answers_k23": len(conf), "precision_all": prec(conf),
            "precision_low_dispersion_half": prec(half),
            "median_dispersion": conf[len(conf) // 2][0] if conf else None}


def _tally_set(t: Dict[str, int], ok: Optional[bool]) -> None:
    if ok is None:
        t["refused"] += 1
    elif ok:
        t["right"] += 1
    else:
        t["wrong"] += 1


# ===========================================================================
# 4.  IDENTITIES AND MARKS
# ===========================================================================

def identities() -> Dict[str, int]:
    rng = random.Random(f"{SEED}:identities")
    checked = held = null_ok = 0
    for trial in range(200):
        kind = trial % 3
        if kind == 0:
            k = 1 + trial % 3
            cues = [(tuple(F(v) for v in ll.doubled(rng.getrandbits(24))),
                     F(1)) for _ in range(k)]
            scale = ll.SCALE
        elif kind == 1:
            k = 1 + trial % 4
            base = tuple(F(rng.randrange(-4, 5), rng.randrange(1, 5))
                         for _ in range(10))
            cues = [(base if rng.randrange(10) < 3 else
                     tuple(F(rng.randrange(-4, 5), rng.randrange(1, 5))
                           for _ in range(10)),
                     F(rng.randrange(1, 4))) for _ in range(k)]
            scale = 1
        else:
            pts = [tuple(F(rng.randrange(-6, 7), 2) for _ in range(10))
                   for _ in range(3)]
            cues = le.analogy_cues(*pts)
            scale = 1
        checked += 1
        held += le.decomposition_holds(cues, scale)
        if all(w > 0 for _, w in cues):
            V = le.evidence(cues, scale)
            agree = all(x == cues[0][0] for x, _ in cues)
            null_ok += (le.inner(V, V, scale) == 0) == agree
        else:
            null_ok += 1
    return {"checked": checked, "decomposition": held, "null_iff_agree": null_ok}


def _lean_ok() -> bool:
    root = Path(__file__).resolve().parents[2] / "lean"
    text = (root / le.LEAN_FILE).read_text(encoding="utf-8")
    audit = (root / "RequestProject" / "GLM" / "AxiomAuditAll.lean").read_text(
        encoding="utf-8")
    return ("sorry" not in text
            and all(f"theorem {t}" in text for t in le.LEAN_THEOREMS)
            and "import RequestProject.GLM.LorentzianEvidence" in audit)


def compute() -> Dict[str, object]:
    ide = identities()
    gol = golay()
    sett = settling()
    phy = physics()
    names = physics_names()
    sem = semantic()
    gc = gol["conditions"]
    honest = [c for c in gc if c != "decoy"]
    marks = {
        "E1": ide["decomposition"] == ide["checked"] == ide["null_iff_agree"],
        "G1": all(gc[c]["certificate"]["right"] == gc[c]["guarded"]["right"]
                  for c in gc),
        "G2": gc["decoy"]["certificate"]["wrong"] < gc["decoy"]["guarded"]["wrong"],
        "G3": (gol["decoy_census"]["honest_looking"]
               == gol["decoy_census"]["certificate_wrong"]),
        "G4": all(gc[c]["dispersion"]["right"] == gc[c]["guarded"]["right"]
                  for c in honest),
        "G5": (sett["asked"]["right"] == sett["queries"]
               and sett["no_four_settle"] == sett["queries"]),
        "G5b": sett["no_four_settle_every"] == sett["queries"],
        "G6": sett["random5"]["right"] < sett["asked"]["right"],
        "P1": all(phy[c]["guarded"]["wrong"] == 0 for c in PHYS_CONDITIONS),
        "P2": all(phy[c]["guarded"]["right"] == phy[c]["present"]
                  and phy[c]["guarded"]["refused"] == phy[c]["absent"]
                  for c in ("clean1", "clean2", "clean3")),
        "P3": all(phy[c]["guarded"]["refused"] == PHYS_QUERIES
                  and phy[c]["first"]["wrong"] > 0
                  and phy[c]["lorentz"]["wrong"] > 0
                  for c in ("decoy2", "decoy3")),
        "P4": all(r["expected_in_class"] for r in names["rows"]
                  if r["status"] == "class"),
        "S1": (F(sem["by_k"][3]["lorentz"]["right"], sem["by_k"][3]["queries"])
               >= F(sem["by_k"][1]["lorentz"]["right"],
                    sem["by_k"][1]["queries"])),
        "S2": sem["precision_low_dispersion_half"] > sem["precision_all"],
        "L": _lean_ok(),
    }
    return {"identities": ide, "golay": gol, "settling": sett,
            "physics": phy, "physics_names": names, "semantic": sem,
            "marks": marks, "met": sum(marks.values()), "taken": len(marks)}


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


def lorentzian_evidence_report() -> Dict[str, object]:
    """The stored marks, or why there are none."""
    stored = current()
    if stored is None:
        return {"available": False, "reason": (
            f"the stored measurement is {state()['verdict']}; re-take it "
            f"with python3 -m glm_universal.tools lorentzian-evidence --write")}
    return dict(stored, available=True)

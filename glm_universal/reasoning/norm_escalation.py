"""``glm_universal.reasoning.norm_escalation`` -- escalation over the
norm-indexed family of rungs.

What this module is
-------------------
:mod:`glm_universal.reasoning.ladder_escalation` measures escalation over the
*named* construction rungs: eleven of them, with three rungs sharing minimum
norm 32, two sharing 16, two sharing 4 and nothing above 64.
:mod:`glm_universal.substrate.norm_family` re-indexes the same constructions by
the quantity a reading actually escalates over -- the **minimum squared
norm** -- and generates one rung at every power of two.  This module re-takes
the escalation measurement over that family, with the same query set, the same
perturbations, the same stopping rule and the same controls, so the two are
comparable figure for figure.

The declared ladder
-------------------
:data:`NORM_LADDER` is the densest rung at each power-of-two norm, coarsest
first::

    8C  8A  4C  4A  2C  2A  C  A  2D  A/2  D  Z
  2048 1024 512 256 128  64 32  16  8   4   2  1

"Densest" is generated, not chosen: the largest kissing number at that norm,
ties to the smaller covolume.  Every rung is a scaling of one of the five
constructions, so each one's quantiser is the base quantiser applied to the
shrunk vector -- ``ladder_escalation._quantise_scaled`` -- and no new decoder is
written for any of them.

What is measured
----------------
Exactly what the previous round measured, so that the comparison is a
comparison and not a re-definition:

* correct, wrong and refused, over the same 568 queries;
* whether the escalation matches the after-the-fact oracle;
* whether any two rungs ever name *different* carriers, which is the
  hypothesis of ``GLM.ConstructionLadder.firstNamed_order_independent``;
* where the ladder first breaks, over a sweep of family lengths;
* and -- new this round -- what each rung *contributes*:
  :func:`rung_audit` counts the queries a rung is the only one to answer
  correctly, the queries it answers wrongly, and the disagreements it takes
  part in, so a rung that buys nothing but order-dependence can be **retired**
  by a rule rather than by taste.

Refusing rather than answering wrongly is the property that matters, and it is
checked explicitly: :func:`safety` reports it, and a ladder that loses it is
reported as a failure, not as a footnote.

Exactness
---------
Integers and :class:`~fractions.Fraction` throughout; the perturbations are the
declared deterministic ones of :mod:`ladder_escalation`.  No float is
constructed anywhere in this module.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import integrity
from ..substrate import construction_ladder as CL
from ..substrate import norm_family as NF
from . import ladder_escalation as LE

__all__ = [
    "NORM_LADDER", "CHAIN_LADDER", "FAMILY_LENGTHS", "ladder_for",
    "norm_ladder_report", "rung_audit", "retirement", "repair", "safety",
    "family_sweep", "measure", "write_measurements", "measurements",
    "module_digest", "state", "current", "DATA_PATH",
]


def ladder_for(max_log2: int) -> Tuple[str, ...]:
    """The densest-per-norm family up to ``2**max_log2``, coarsest first."""
    return tuple(reversed(NF.densest_by_norm(max_log2)))


#: The declared ladder: one rung at every power-of-two minimum norm from 1 to
#: 2,048, coarsest first.
NORM_LADDER: Tuple[str, ...] = ladder_for(NF.MAX_LOG2)

#: The same family taken through Construction ``B`` instead of the Leech
#: lattice, which makes it a containment chain -- the tower
#: ``GLM.NormFamily.family_tower`` proves.  Measured beside the declared
#: ladder so that the cost of insisting on a chain can be read off.
CHAIN_LADDER: Tuple[str, ...] = tuple(reversed(NF.NORM_CHAIN))

#: The family lengths the sweep measures, one rung at a time so that the
#: breaking point is located exactly.  Six rungs is norms 1 to 32 -- the
#: smallest family that reaches the Leech lattice -- and fourteen is norms 1 to
#: 8,192.
FAMILY_LENGTHS: Tuple[int, ...] = (6, 7, 8, 9, 10, 11, 12, 13, 14)


# ═════════════════════════════════════════════════════════════════════════
# 1.  WHAT EACH RUNG CONTRIBUTES
# ═════════════════════════════════════════════════════════════════════════

def rung_audit(carriers=None, rungs: Sequence[str] = NORM_LADDER,
               perturbations=LE.PERTURBATIONS) -> Tuple[Dict[str, object], ...]:
    """Per rung: what it alone answers, what it gets wrong, what it disputes.

    ``unique_correct`` is the number of queries this rung is the *only* rung of
    the ladder to name correctly -- what would be lost by removing it.
    ``wrong`` is what it names incorrectly; ``disagrees`` is the number of
    queries on which it names a carrier some other rung contradicts.  Those
    three decide :func:`retirement`.
    """
    carriers = carriers if carriers is not None else LE.sample_carriers()
    ladder = tuple(rungs)
    indices = {rung: LE.rung_index(rung, carriers) for rung in ladder}
    unique: Dict[str, int] = {rung: 0 for rung in ladder}
    correct: Dict[str, int] = {rung: 0 for rung in ladder}
    wrong: Dict[str, int] = {rung: 0 for rung in ladder}
    refused: Dict[str, int] = {rung: 0 for rung in ladder}
    disagrees: Dict[str, int] = {rung: 0 for rung in ladder}
    for _, support, magnitude in perturbations:
        for i, (_, _, carrier) in enumerate(carriers):
            query = LE.perturb(carrier, i, support, magnitude)
            named: Dict[str, Optional[int]] = {}
            for rung in ladder:
                answer, _ = LE.answer_at_rung(query, rung, indices)
                named[rung] = answer
                if answer is None:
                    refused[rung] += 1
                elif answer == i:
                    correct[rung] += 1
                else:
                    wrong[rung] += 1
            right = [rung for rung in ladder if named[rung] == i]
            if len(right) == 1:
                unique[right[0]] += 1
            spoken = {rung: answer for rung, answer in named.items()
                      if answer is not None}
            distinct = set(spoken.values())
            if len(distinct) > 1:
                for rung, answer in spoken.items():
                    if any(other != answer for other in distinct):
                        disagrees[rung] += 1
    return tuple({
        "rung": rung,
        "minimum_norm": CL.rung_spec(rung).minimum_norm,
        "correct": correct[rung],
        "wrong": wrong[rung],
        "refused": refused[rung],
        "unique_correct": unique[rung],
        "disagrees": disagrees[rung],
    } for rung in ladder)


def retirement(audit: Sequence[Dict[str, object]]) -> Dict[str, object]:
    """Which rungs the declared rule retires, and why.

    **The rule, declared before it was run**, in two clauses:

    1. *Safety first.*  Retire a rung that answers any query **wrongly**.
       Refusing rather than answering wrongly is the property the escalation
       is for, and a rung that breaks it is not paid for by whatever else it
       answers -- the queries it uniquely answers are recorded, so the price
       of the rule is visible rather than hidden.
    2. *No dead weight that costs order-independence.*  Retire a rung that
       answers no query the rest of the ladder cannot (``unique_correct == 0``)
       and takes part in at least one disagreement.  A rung that contributes
       nothing but agrees with everything is harmless and is kept.
    """
    retired: List[Dict[str, object]] = []
    kept: List[str] = []
    for row in audit:
        if int(row["wrong"]) > 0:
            retired.append({
                "rung": row["rung"],
                "clause": 1,
                "why": (f"it answers {row['wrong']} "
                        f"{'query' if int(row['wrong']) == 1 else 'queries'} "
                        f"wrongly, "
                        f"which is the one thing the escalation is supposed "
                        f"not to do; it uniquely answers "
                        f"{row['unique_correct']}, and that is the price of "
                        f"retiring it"),
            })
        elif int(row["unique_correct"]) == 0 and int(row["disagrees"]) > 0:
            retired.append({
                "rung": row["rung"],
                "clause": 2,
                "why": (f"it answers no query the rest of the ladder cannot "
                        f"(unique_correct = 0) and takes part in "
                        f"{row['disagrees']} disagreement(s)"),
            })
        else:
            kept.append(str(row["rung"]))
    return {
        "rule": ("retire a rung that answers any query wrongly, and retire a "
                 "rung with unique_correct = 0 that takes part in a "
                 "disagreement"),
        "retired": tuple(retired),
        "kept": tuple(kept),
        "any_retired": bool(retired),
    }


def repair(carriers=None, rungs: Sequence[str] = NORM_LADDER,
           limit: int = 4) -> Dict[str, object]:
    """Apply the retirement rule until the ladder is safe, keeping it complete.

    A retired rung is **substituted** rather than simply dropped where the
    family has another rung at the same minimum norm -- the norms are the index
    of the family, and leaving one empty would put a gap back into it.  Where
    no untried rung remains at that norm, the rung is dropped and the gap is
    reported.  The loop is bounded; a ladder still unsafe at the bound is
    returned as it stands, with ``safe = False``, rather than repaired by hand.
    """
    carriers = carriers if carriers is not None else LE.sample_carriers()
    current = tuple(rungs)
    tried: set = set(current)
    history: List[Dict[str, object]] = []
    for _ in range(limit):
        audit = rung_audit(carriers, current)
        verdict = retirement(audit)
        if not verdict["any_retired"]:
            return {"ladder": current, "history": tuple(history),
                    "safe": True, "rounds": len(history),
                    "gaps": tuple(_gaps(current)),
                    "audit": audit, "retirement": verdict}
        retired = {str(row["rung"]): row for row in verdict["retired"]}  # type: ignore[union-attr]
        moves: List[Dict[str, object]] = []
        nxt: List[str] = []
        for rung in current:
            if rung not in retired:
                nxt.append(rung)
                continue
            norm = CL.rung_spec(rung).minimum_norm
            alternatives = [key for key in NF.rungs_at_norm(norm)
                            if key not in tried]
            if alternatives:
                replacement = alternatives[0]
                tried.add(replacement)
                nxt.append(replacement)
                moves.append({"retired": rung, "replaced_by": replacement,
                              "norm": norm,
                              "why": retired[rung]["why"]})
            else:
                moves.append({"retired": rung, "replaced_by": None,
                              "norm": norm,
                              "why": retired[rung]["why"]})
        history.append({"ladder": current, "moves": tuple(moves),
                        "audit": audit})
        current = tuple(nxt)
    audit = rung_audit(carriers, current)
    verdict = retirement(audit)
    return {"ladder": current, "history": tuple(history),
            "safe": not verdict["any_retired"], "rounds": len(history),
            "gaps": tuple(_gaps(current)), "audit": audit,
            "retirement": verdict}


def _gaps(ladder: Sequence[str]) -> Tuple[int, ...]:
    """Powers of two below the ladder's top that carry no rung."""
    norms = {CL.rung_spec(rung).minimum_norm for rung in ladder}
    top = max(norms) if norms else 1
    power = 1
    missing: List[int] = []
    while power <= top:
        if power not in norms:
            missing.append(power)
        power *= 2
    return tuple(missing)


def safety(orders_totals: Dict[str, object]) -> Dict[str, object]:
    """The property that matters: refusing rather than answering wrongly.

    A reading is **safe** when it answers no query incorrectly.  This is
    checked for every visiting order separately, because an order-dependent
    ladder can be safe in one order and unsafe in another, and reporting only
    the best order would hide exactly the failure this is looking for.
    """
    wrong = {name: int(scores["wrong"])                        # type: ignore[index]
             for name, scores in orders_totals.items()}
    return {
        "wrong_by_order": wrong,
        "worst_order": max(wrong.items(), key=lambda item: item[1])[0],
        "wrong": max(wrong.values()),
        "safe": max(wrong.values()) == 0,
        "statement": ("a reading is safe when every query it does not answer "
                      "correctly is refused rather than answered wrongly"),
    }


# ═════════════════════════════════════════════════════════════════════════
# 2.  THE RUN
# ═════════════════════════════════════════════════════════════════════════

def norm_ladder_report(rungs: Sequence[str] = NORM_LADDER,
                       carriers=None) -> Dict[str, object]:
    """The escalation over one norm-indexed ladder, with its controls."""
    carriers = carriers if carriers is not None else LE.sample_carriers()
    ladder = tuple(rungs)
    report = LE.ladder_escalation_report(ladder)
    audit = rung_audit(carriers, ladder)
    report["rung_audit"] = audit
    report["retirement"] = retirement(audit)
    report["safety"] = safety(report["orders"]["totals"])         # type: ignore[index]
    report["norms"] = tuple(CL.rung_spec(rung).minimum_norm for rung in ladder)
    report["norms_are_powers_of_two"] = all(
        norm & (norm - 1) == 0 for norm in report["norms"])       # type: ignore[union-attr]
    report["one_rung_per_norm"] = (
        len(set(report["norms"])) == len(ladder))                 # type: ignore[arg-type]
    return report


def family_sweep(carriers=None,
                 lengths: Sequence[int] = FAMILY_LENGTHS
                 ) -> Dict[str, object]:
    """The same experiment at several family lengths -- where does it break?

    A length of ``n`` is the densest rung at each of the norms ``1`` to
    ``2^(n-1)``.  The ladder is safe at a length when no order answers a query
    wrongly, every order returns the same answers, and no two rungs name
    different carriers.
    """
    carriers = carriers if carriers is not None else LE.sample_carriers()
    rows: List[Dict[str, object]] = []
    for length in lengths:
        ladder = ladder_for(length - 1)
        orders = LE.run_orders(carriers, rungs=ladder)
        fixed = LE.run_fixed_rungs(carriers, rungs=ladder)
        totals = orders["totals"]                                 # type: ignore[index]
        correct = {name: int(scores["correct"])
                   for name, scores in totals.items()}            # type: ignore[union-attr]
        wrong = {name: int(scores["wrong"])
                 for name, scores in totals.items()}              # type: ignore[union-attr]
        refused = {name: int(scores["refused"])
                   for name, scores in totals.items()}            # type: ignore[union-attr]
        oracle = int(fixed["totals"]["oracle"]["correct"])        # type: ignore[index]
        disagree = int(fixed["agreement"]["rungs_disagree"])      # type: ignore[index]
        rows.append({
            "length": length,
            "ladder": ladder,
            "highest_norm": CL.rung_spec(ladder[0]).minimum_norm,
            "correct": correct,
            "wrong": wrong,
            "refused": refused,
            "order_independent": (len(set(correct.values())) == 1
                                  and len(set(wrong.values())) == 1),
            "rungs_disagree": disagree,
            "oracle": oracle,
            "matches_oracle": correct["middle_out"] == oracle,
            "safe": max(wrong.values()) == 0,
            "cost": {name: int(scores["cost"])
                     for name, scores in totals.items()},         # type: ignore[union-attr]
        })
    safe = [row for row in rows
            if row["safe"] and row["order_independent"]
            and row["rungs_disagree"] == 0]
    broken = [row for row in rows if row not in safe]
    best = (max(safe, key=lambda row: int(row["correct"]["middle_out"]))  # type: ignore[index]
            if safe else None)
    return {
        "rows": tuple(rows),
        "lengths": tuple(lengths),
        "longest_safe": (int(best["length"]) if best else None),  # type: ignore[arg-type]
        "best_correct": (int(best["correct"]["middle_out"])       # type: ignore[index]
                         if best else None),
        "first_broken": (int(broken[0]["length"]) if broken else None),  # type: ignore[arg-type]
    }


# ═════════════════════════════════════════════════════════════════════════
# 3.  THE CACHE, GUARDED BY A DIGEST
# ═════════════════════════════════════════════════════════════════════════

DATA_PATH = (Path(__file__).resolve().parent / "_data"
             / "norm_escalation.json")

_SOURCES: Tuple[str, ...] = (
    "reasoning/norm_escalation.py",
    "reasoning/ladder_escalation.py",
    "substrate/norm_family.py",
    "substrate/construction_ladder.py",
    "substrate/leech_construct.py",
    "reasoning/fwht_decode.py",
)


def module_digest() -> str:
    """One digest over the sources this measurement is taken from."""
    root = Path(__file__).resolve().parent.parent
    return integrity.tree_digest([root / name for name in _SOURCES], root)


def _freeze(value: object) -> object:
    if isinstance(value, Fraction):
        return {"__fraction__": f"{value.numerator}/{value.denominator}"}
    if isinstance(value, dict):
        return {str(key): _freeze(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_freeze(item) for item in value]
    return value


def measure() -> Dict[str, object]:
    """The whole round, recomputed: the declared ladder, the chain, the sweep."""
    carriers = LE.sample_carriers()
    repaired = repair(carriers, NORM_LADDER)
    payload: Dict[str, object] = {
        "declared": norm_ladder_report(NORM_LADDER, carriers),
        "repair": repaired,
        "repaired": norm_ladder_report(repaired["ladder"], carriers),   # type: ignore[arg-type]
        "chain": norm_ladder_report(CHAIN_LADDER, carriers),
        "named_rungs": LE.ladder_escalation_report(CL.RUNG_ORDER),
        "family": NF.norm_family_report(),
        "sweep": family_sweep(carriers),
        "source_digest": module_digest(),
    }
    return payload


def write_measurements(path: Optional[Path] = None) -> Path:
    """Take the measurements and store them beside their digest."""
    target = Path(path) if path is not None else DATA_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(_freeze(measure()), indent=1, sort_keys=True,
                   ensure_ascii=False) + "\n", encoding="utf-8")
    return target


_cache: Optional[Dict[str, object]] = None


def measurements(refresh: bool = False) -> Optional[Dict[str, object]]:
    """What is stored, whether or not it is still current."""
    global _cache
    if _cache is not None and not refresh:
        return _cache
    if not DATA_PATH.exists():
        return None
    loaded = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    _cache = loaded if isinstance(loaded, dict) else None
    return _cache


def state() -> Dict[str, object]:
    """Present, and taken from the sources as they stand?"""
    stored = measurements()
    live = module_digest()
    if stored is None:
        return {"present": False, "fresh": False, "live_digest": live,
                "stored_digest": None, "verdict": "absent"}
    same = stored.get("source_digest") == live
    return {"present": True, "fresh": same, "live_digest": live,
            "stored_digest": stored.get("source_digest"),
            "verdict": "fresh" if same else "stale"}


def current() -> Optional[Dict[str, object]]:
    """The measurements if they still describe the sources, else ``None``."""
    stored = measurements()
    if stored is None or stored.get("source_digest") != module_digest():
        return None
    return stored


if __name__ == "__main__":                      # pragma: no cover
    print(f"wrote {write_measurements()}")
    print(f"digest {module_digest()}")

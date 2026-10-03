"""``glm_universal.reasoning.element_completion`` -- every empty cell accounted for.

Where this sits
---------------
:mod:`glm_universal.reasoning.element_coverage` measures the sparsity of the
element register -- **1,257 of 1,652 cells** carry a measurement -- and widens
it three ways without inventing one: exact derivations, one fitted line for
covalent radius, and a cross-check that compares two registers instead of
merging them.  What it does *not* do is say anything about the cells it leaves
empty.  "Sparse chemistry" stayed on the open list for that reason: not
because 395 cells were empty, but because nothing decided what each of them
was -- a value a rule could supply, a value no rule here can reach, or a value
that is not the kind of thing a rule could ever reach.

This module decides them, in the same way the ``related_to`` residue was
decided: **every empty cell gets exactly one disposition, and a disposition is
a decision rather than a failed lookup.**

The four dispositions
---------------------
``estimated``
    an admitted rule reaches the cell and its inputs are present.  The value
    is carried in the completed view with the rule that produced it and that
    rule's *out-of-sample* error, and it is never written back into the
    register.
``inputs_absent``
    the field has an admitted rule and this element does not carry what it
    needs.  The missing input is named.
``no_admitted_rule``
    every rule tried for this field failed the gate below.  The best rule and
    its measured skill are reported, so the decision can be re-argued against
    a number.
``not_derivable``
    the field is not the kind of thing a rule over the register could reach.
    ``year_discovered`` is the clear case: it is a historical fact about
    people, and a line fitted through it would be a category error however
    well it scored.

The gate
--------
A rule is admitted only if, on the elements that *do* carry the field, leaving
each one out in turn and refitting on the rest, its mean absolute error is at
most **half** the error of the constant rule that predicts the field's mean --
and only if at least **20** elements were available to score it on.  Both
numbers are stated here as :data:`GATE_SKILL` and :data:`GATE_MINIMUM` and
neither is tuned per field.

This is deliberately a *skill* test rather than an accuracy test.  An accuracy
threshold in the field's own units is a threshold somebody chose; beating the
mean by a factor of two is a claim that the rule has found something, and the
constant rule is the control it has to beat.

The two rule families
---------------------
``linear``
    an exact rational least-squares line of the target field on one other
    field.  Every other numeric field is tried as a predictor and the best
    scoring one is kept, so which predictor a field takes is a measurement and
    not a preference.
``group``
    linear interpolation in period *within the element's group*, between the
    nearest known member above and the nearest below -- extrapolated from the
    two nearest when the element is at the end of its group.  Group and period
    are the derived table coordinates of
    :mod:`glm_universal.reasoning.periodic_table`, never tabulated.

Both are exact :class:`fractions.Fraction` arithmetic throughout.  Nothing is
rounded and no float is constructed.

What the completed view is, and is not
--------------------------------------
:func:`completed_table` returns every cell of the 118 x 14 grid with its
provenance.  Two properties make it safe, and both are checked -- in
:func:`measured_view_is_the_register`, in the test suite, and in the abstract
in ``RequestProject/GLM/Completion.lean``:

* restricted to ``measured`` cells it *is* the register, cell for cell: a
  reader who wants only measurements has only measurements;
* no estimate ever occupies a cell the register fills, so an estimate cannot
  overwrite a measurement even by accident.

The register file itself is untouched.  What changes is that the empty cells
are no longer silent.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from ..data_objects import elements as el
from ..derived import memo
from . import element_coverage as ec
from . import periodic_table as pt

__all__ = [
    "GATE_SKILL", "GATE_MINIMUM", "DISPOSITIONS", "FIELDS", "NOT_DERIVABLE",
    "Rule", "Cell",
    "round_to_thousandths",
    "NESTED_GATE", "NARROWING_DOMAINS", "in_domain", "nested_holdout",
    "first_gate_rules", "nested_gate_table",
    "linear_rule", "group_rule", "rules_for_field", "admitted_rules",
    "empty_cells_by_field",
    "rule_table", "estimate", "completed_table", "coverage",
    "dispositions", "measured_view_is_the_register",
    "element_completion_report",
]


#: A rule is admitted only if its out-of-sample error is at most this fraction
#: of the constant rule's.  Half: the rule must beat the field's own mean by a
#: factor of two.
GATE_SKILL: Fraction = Fraction(1, 2)

#: And only if it was scored on at least this many elements.
GATE_MINIMUM: int = 20

#: The second gate (Phase 93, H's first item of the substrate-cognition
#: study): each rule was chosen as the best of about fourteen on the same
#: leave-one-out errors it then reports, so its reported skill is flattered
#: by the choice.  A rule is admitted only if the *nested* holdout -- the
#: rule re-chosen without the held-out element, by the same gate, then scored
#: on it -- is also at most :data:`GATE_SKILL`.
NESTED_GATE: Fraction = GATE_SKILL

#: The one declared domain a rule failing the nested gate over every element
#: may be narrowed to: the main-group elements, by their derived group.  It
#: is admitted there only if the nested skill re-measured inside the domain
#: passes, on at least :data:`GATE_MINIMUM` scored folds, and the selection
#: inside the domain chose the field's own rule on every scored fold.
NARROWING_DOMAINS: Dict[str, Tuple[int, ...]] = {
    "main group": (1, 2, 13, 14, 15, 16, 17, 18),
}

#: The four decisions an empty cell may receive.  Every empty cell receives
#: exactly one, which is the claim :func:`dispositions` measures.
DISPOSITIONS: Tuple[str, ...] = (
    "estimated", "inputs_absent", "no_admitted_rule", "not_derivable",
)

#: The fields the coverage table counts -- the measured fields, less the two
#: bookkeeping ones ``element_coverage`` also drops.
FIELDS: Tuple[str, ...] = tuple(
    f for f in el.MEASURED_FIELDS
    if f not in ("period", "electron_count_check"))

#: Fields no rule over this register may fill, with the reason.  A field is
#: here because of what it *is*, not because the rules happened to score
#: badly on it; a field that merely scores badly is ``no_admitted_rule``.
NOT_DERIVABLE: Dict[str, str] = {
    "year_discovered": (
        "the year an element was first isolated is a fact about people and "
        "laboratories, not a function of the element's other properties; a "
        "line through it would be a category error however well it scored"),
}


# ===========================================================================
# 1.  RULES
# ===========================================================================

@dataclass(frozen=True)
class Rule:
    """One estimator for one field, with the score that admits or refuses it.

    ``skill`` is the leave-one-out mean absolute error divided by the constant
    rule's, so smaller is better and 1 means "no better than the mean".
    """

    field: str
    family: str
    predictor: str
    slope: Optional[Fraction]
    intercept: Optional[Fraction]
    fitted_on: int
    scored_on: int
    loo_error: Optional[Fraction]
    baseline_error: Optional[Fraction]
    skill: Optional[Fraction]
    statement: str
    #: The declared domain the rule is admitted on: empty for every element,
    #: else a key of :data:`NARROWING_DOMAINS` (Phase 93).
    domain: str = ""

    @property
    def admitted(self) -> bool:
        """Whether the rule passes the stated gate."""
        return (self.skill is not None
                and self.scored_on >= GATE_MINIMUM
                and self.skill <= GATE_SKILL)

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view.

        The three scores are given twice: exactly, and rounded to three
        decimal places as a rational over 1,000.  The gate is decided on the
        exact value; the rounded one is what a report prints, because a
        least-squares fit over a hundred points is an exact rational with a
        two-hundred-digit denominator and no reader is served by it.
        """
        return {
            "field": self.field, "family": self.family,
            "predictor": self.predictor, "fitted_on": self.fitted_on,
            "scored_on": self.scored_on, "loo_error": self.loo_error,
            "baseline_error": self.baseline_error, "skill": self.skill,
            "loo_error_3dp": round_to_thousandths(self.loo_error),
            "baseline_error_3dp": round_to_thousandths(self.baseline_error),
            "skill_3dp": round_to_thousandths(self.skill),
            "admitted": self.admitted, "statement": self.statement,
            "domain": self.domain or "every element",
        }


def round_to_thousandths(value: Optional[Fraction]) -> Optional[Fraction]:
    """An exact rational rounded to three decimal places, for printing."""
    if value is None:
        return None
    return Fraction(round(value * 1000), 1000)


def _value(element: el.Element, field: str) -> Optional[Fraction]:
    raw = getattr(element, field, None)
    return None if raw is None else Fraction(raw)


def _fit(sums: Tuple[int, Fraction, Fraction, Fraction, Fraction]
         ) -> Optional[Tuple[Fraction, Fraction]]:
    """Least squares from the five sums, or ``None`` when degenerate."""
    n, sx, sy, sxx, sxy = sums
    if n < 2:
        return None
    denominator = n * sxx - sx * sx
    if denominator == 0:
        return None
    return ((n * sxy - sx * sy) / denominator,
            (sy * sxx - sx * sxy) / denominator)


def _mean_error(values: Sequence[Fraction]) -> Optional[Fraction]:
    """Leave-one-out error of the constant rule: predict the mean of the rest."""
    n = len(values)
    if n < 2:
        return None
    total = sum(values)
    return sum(abs(v - (total - v) / (n - 1)) for v in values) / n


def linear_rule(field: str, predictor: str) -> Optional[Rule]:
    """The least-squares line of ``field`` on ``predictor``, scored out of sample.

    The leave-one-out refit is exact and closed form: the five sums of the
    remaining points are the full sums less the point removed, so no fit is
    recomputed from scratch.
    """
    if field == predictor:
        return None
    elements = el.load_element_register()
    pairs = [(x, y) for x, y in
             ((_value(e, predictor), _value(e, field)) for e in elements)
             if x is not None and y is not None]
    n = len(pairs)
    if n < GATE_MINIMUM:
        return None
    sx = sum(x for x, _ in pairs)
    sy = sum(y for _, y in pairs)
    sxx = sum(x * x for x, _ in pairs)
    sxy = sum(x * y for x, y in pairs)
    whole = _fit((n, sx, sy, sxx, sxy))
    if whole is None:
        return None
    errors: List[Fraction] = []
    for x, y in pairs:
        rest = _fit((n - 1, sx - x, sy - y, sxx - x * x, sxy - x * y))
        if rest is None:
            continue
        errors.append(abs(y - (rest[0] * x + rest[1])))
    if not errors:
        return None
    loo = sum(errors) / len(errors)
    baseline = _mean_error([y for _, y in pairs])
    if baseline is None or baseline == 0:
        return None
    return Rule(
        field=field, family="linear", predictor=predictor,
        slope=whole[0], intercept=whole[1], fitted_on=n,
        scored_on=len(errors), loo_error=loo, baseline_error=baseline,
        skill=loo / baseline,
        statement=(f"{field} = {whole[0]} * {predictor} + {whole[1]}, an "
                   f"exact rational least-squares line fitted on {n} "
                   f"elements"))


@lru_cache(maxsize=1)
def _positions() -> Dict[str, pt.Position]:
    out: Dict[str, pt.Position] = {}
    for element in el.load_element_register():
        try:
            out[element.symbol] = pt.position_of_symbol(element.symbol)
        except pt.PositionError:            # pragma: no cover -- all 118 place
            continue
    return out


def _group_estimate(field: str, symbol: str,
                    exclude: Optional[str] = None) -> Optional[Fraction]:
    """Interpolate a field within an element's group, in period.

    ``exclude`` drops one element from the group, which is what makes the
    leave-one-out scoring honest.
    """
    positions = _positions()
    here = positions.get(symbol)
    if here is None:
        return None
    known: List[Tuple[int, Fraction]] = []
    for element in el.load_element_register():
        if element.symbol in (symbol, exclude):
            continue
        place = positions.get(element.symbol)
        value = _value(element, field)
        if place is None or value is None or place.group != here.group:
            continue
        known.append((place.period, value))
    if not known:
        return None
    below = [k for k in known if k[0] < here.period]
    above = [k for k in known if k[0] > here.period]
    if below and above:
        low, high = max(below), min(above)
    else:
        pool = sorted(below or above,
                      key=lambda k: (abs(k[0] - here.period), k[0]))[:2]
        if len(pool) == 1:
            return pool[0][1]
        low, high = sorted(pool)
    if high[0] == low[0]:
        return None
    return low[1] + (high[1] - low[1]) * Fraction(here.period - low[0],
                                                  high[0] - low[0])


def group_rule(field: str) -> Optional[Rule]:
    """Interpolation within the group, scored by leaving each element out."""
    elements = el.load_element_register()
    have = [e for e in elements if _value(e, field) is not None]
    if len(have) < GATE_MINIMUM:
        return None
    errors: List[Fraction] = []
    for element in have:
        predicted = _group_estimate(field, element.symbol,
                                    exclude=element.symbol)
        if predicted is None:
            continue
        actual = _value(element, field)
        assert actual is not None
        errors.append(abs(actual - predicted))
    if len(errors) < GATE_MINIMUM:
        return None
    loo = sum(errors) / len(errors)
    baseline = _mean_error([v for v in (_value(e, field) for e in have)
                            if v is not None])
    if baseline is None or baseline == 0:
        return None
    return Rule(
        field=field, family="group", predictor="group and period",
        slope=None, intercept=None, fitted_on=len(have),
        scored_on=len(errors), loo_error=loo, baseline_error=baseline,
        skill=loo / baseline,
        statement=(f"{field} interpolated in period within the element's "
                   f"group, between the nearest known member above and the "
                   f"nearest below"))


@lru_cache(maxsize=1)
def empty_cells_by_field() -> Dict[str, int]:
    """How many elements are missing each field.  A field with none needs no rule."""
    elements = el.load_element_register()
    return {field: sum(1 for e in elements if _value(e, field) is None)
            for field in FIELDS}


@lru_cache(maxsize=None)
def rules_for_field(field: str) -> Tuple[Rule, ...]:
    """Every rule tried for one field, best first.

    No rule is sought for a field the register already fills for all 118
    elements -- there would be no cell for it to reach -- nor for a field that
    is :data:`NOT_DERIVABLE`.  The search is deterministic, so it is cached.
    """
    if field in NOT_DERIVABLE or not empty_cells_by_field().get(field):
        return ()
    candidates: List[Rule] = []
    for predictor in FIELDS:
        rule = linear_rule(field, predictor)
        if rule is not None:
            candidates.append(rule)
    group = group_rule(field)
    if group is not None:
        candidates.append(group)
    return tuple(sorted(
        candidates,
        key=lambda r: (r.skill if r.skill is not None else Fraction(10**6),
                       r.family, r.predictor)))


@memo
def first_gate_rules() -> Dict[str, Rule]:
    """The rule each field takes under the first gate alone (Phase 61).

    This was ``admitted_rules`` until Phase 93; it is kept under its own name
    because the nested holdout of the substrate-cognition study (Y5) is a
    measurement *of these rules*, and because the second gate is read
    against it.
    """
    out: Dict[str, Rule] = {}
    for field in FIELDS:
        for rule in rules_for_field(field):
            if rule.admitted:
                out[field] = rule
                break
    return out


def in_domain(symbol: str, domain: str) -> bool:
    """Whether an element lies in a declared narrowing domain ("" is all)."""
    if not domain:
        return True
    place = _positions().get(symbol)
    return place is not None and place.group in NARROWING_DOMAINS[domain]


def _loo_linear(pairs: Sequence[Tuple[Fraction, Fraction]]
                ) -> Optional[Fraction]:
    """Leave-one-out mean error of the least-squares line, closed form."""
    n = len(pairs)
    sx = sum(x for x, _ in pairs)
    sy = sum(y for _, y in pairs)
    sxx = sum(x * x for x, _ in pairs)
    sxy = sum(x * y for x, y in pairs)
    errors: List[Fraction] = []
    for x, y in pairs:
        rest = _fit((n - 1, sx - x, sy - y, sxx - x * x, sxy - x * y))
        if rest is not None:
            errors.append(abs(y - (rest[0] * x + rest[1])))
    return sum(errors) / len(errors) if errors else None


def _group_predict(known: Dict[int, List[Tuple[int, Fraction]]], group: int,
                   period: int) -> Optional[Fraction]:
    """The group rule over a given known set (what ``_group_estimate`` does)."""
    pool = known.get(group, [])
    if not pool:
        return None
    below = [k for k in pool if k[0] < period]
    above = [k for k in pool if k[0] > period]
    if below and above:
        low, high = max(below), min(above)
    else:
        near = sorted(below or above,
                      key=lambda k: (abs(k[0] - period), k[0]))[:2]
        if len(near) == 1:
            return near[0][1]
        low, high = sorted(near)
    if high[0] == low[0]:
        return None
    return low[1] + (high[1] - low[1]) * Fraction(period - low[0],
                                                  high[0] - low[0])


def nested_holdout(field: str, rule: Rule, domain: str = ""
                   ) -> Dict[str, object]:
    """The rule re-chosen without each held-out element, then scored on it.

    Every element of ``domain`` that carries the field is held out in turn;
    on the remaining ones alone every candidate rule (a line on each other
    field, and the group rule) is scored by the same leave-one-out skill and
    gated the same way; the winner, fitted on the remaining elements,
    predicts the held-out one.  The constant rule (the mean of the remaining
    elements) is scored on the same folds, and the nested skill is the ratio
    of the two summed errors.  This is the measurement Y5 of
    ``studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md`` made, moved here in
    Phase 93 so that the gate can read it; over every element it gives Y5's
    figures exactly.
    """
    elements = tuple(e for e in el.load_element_register()
                     if in_domain(e.symbol, domain))
    positions = _positions()
    have = [e for e in elements if _value(e, field) is not None]
    outer_err: List[Fraction] = []
    const_err: List[Fraction] = []
    same_rule = no_rule = no_input = 0
    for held in have:
        rest = [e for e in have if e is not held]
        y_rest = [_value(e, field) for e in rest]
        base = _mean_error(y_rest)            # type: ignore[arg-type]
        best: Optional[Tuple[Fraction, str, str]] = None
        for predictor in FIELDS:
            if predictor == field:
                continue
            pairs = [(_value(e, predictor), _value(e, field))
                     for e in rest if _value(e, predictor) is not None]
            if len(pairs) < GATE_MINIMUM:
                continue
            loo = _loo_linear(pairs)          # type: ignore[arg-type]
            pb = _mean_error([y for _, y in pairs])  # type: ignore[misc]
            if loo is None or not pb:
                continue
            cand = (loo / pb, "linear", predictor)
            if best is None or cand < best:
                best = cand
        known: Dict[int, List[Tuple[int, Fraction]]] = {}
        for e in rest:
            p = positions.get(e.symbol)
            if p is not None:
                known.setdefault(p.group, []).append(
                    (p.period, _value(e, field)))   # type: ignore[arg-type]
        g_err: List[Fraction] = []
        for e in rest:
            p = positions.get(e.symbol)
            if p is None:
                continue
            v = _value(e, field)
            pool = {k: [x for x in lst if not (k == p.group and x ==
                                              (p.period, v))]
                    for k, lst in known.items() if k == p.group}
            pred = _group_predict(pool, p.group, p.period)
            if pred is not None:
                g_err.append(abs(v - pred))   # type: ignore[operator]
        if len(g_err) >= GATE_MINIMUM and base:
            cand = (sum(g_err) / len(g_err) / base, "group",
                    "group and period")
            if best is None or cand < best:
                best = cand
        if best is None or best[0] > GATE_SKILL:
            no_rule += 1
            continue
        same_rule += (best[1], best[2]) == (rule.family, rule.predictor)
        actual = _value(held, field)
        if best[1] == "linear":
            xh = _value(held, best[2])
            pairs = [(_value(e, best[2]), _value(e, field))
                     for e in rest if _value(e, best[2]) is not None]
            n = len(pairs)
            fit = _fit((n, sum(x for x, _ in pairs),      # type: ignore[misc]
                        sum(y for _, y in pairs),         # type: ignore[misc]
                        sum(x * x for x, _ in pairs),     # type: ignore[misc]
                        sum(x * y for x, y in pairs)))    # type: ignore[misc]
            pred = None if xh is None or fit is None else \
                fit[0] * xh + fit[1]
        else:
            p = positions.get(held.symbol)
            pred = None if p is None else \
                _group_predict(known, p.group, p.period)
        if pred is None:
            no_input += 1
            continue
        outer_err.append(abs(actual - pred))           # type: ignore[operator]
        const_err.append(abs(actual - sum(y_rest) / len(y_rest)))  # type: ignore
    nested = (sum(outer_err) / sum(const_err)) if outer_err and \
        sum(const_err) else None
    return {
        "field": field, "rule": f"{rule.family}:{rule.predictor}",
        "domain": domain or "every element",
        "reported_skill": rule.skill, "nested_skill": nested,
        "reported_skill_3dp": round_to_thousandths(rule.skill),
        "nested_skill_3dp": round_to_thousandths(nested),
        "folds": len(have), "scored_folds": len(outer_err),
        "same_rule_chosen": same_rule, "no_rule_passed": no_rule,
        "inputs_absent": no_input,
        "survives": nested is not None and nested <= NESTED_GATE,
    }


def _nested_inputs() -> Tuple[Path, ...]:
    package = Path(__file__).resolve().parent.parent
    return (Path(__file__).resolve(),
            package / "reasoning" / "periodic_table.py",
            package / "data_objects" / "elements.py",
            package / "data_objects" / "_data" / "elements_118.json")


def _q(x: Optional[Fraction]) -> Optional[str]:
    return None if x is None else f"{x.numerator}/{x.denominator}"


def _unq(x: object) -> Optional[Fraction]:
    return None if x is None else Fraction(str(x))


@memo
def nested_gate_table() -> Dict[str, Dict[str, object]]:
    """Field -> the nested holdout over every element, and over each
    narrowing domain when the first fails.

    About half a minute of exact arithmetic, so it is kept beside the digest
    of the files it reads (:class:`glm_universal.derived.DerivedStore`) and
    recomputed only when one of them moves.
    """
    from ..derived import DerivedStore
    store = DerivedStore("completion_nested_gate", _nested_inputs, schema=1)

    def compute() -> Dict[str, object]:
        out: Dict[str, object] = {}
        for field, rule in sorted(first_gate_rules().items()):
            rows = [nested_holdout(field, rule)]
            if not rows[0]["survives"]:
                rows += [nested_holdout(field, rule, domain)
                         for domain in NARROWING_DOMAINS]
            out[field] = [
                {k: (_q(v) if isinstance(v, Fraction) else v)
                 for k, v in row.items()} for row in rows]
        return out

    payload = store.cached(compute)
    table: Dict[str, Dict[str, object]] = {}
    for field, rows in dict(payload).items():          # type: ignore[arg-type]
        parsed = []
        for row in rows:
            row = dict(row)
            for key in ("reported_skill", "nested_skill",
                        "reported_skill_3dp", "nested_skill_3dp"):
                row[key] = _unq(row[key])
            parsed.append(row)
        table[field] = {"every": parsed[0], "domains": tuple(parsed[1:])}
    return table


def _narrowing(field: str) -> Optional[Dict[str, object]]:
    """The declared domain a field's rule survives in, if any."""
    for row in nested_gate_table()[field]["domains"]:   # type: ignore[union-attr]
        if (row["survives"] and int(row["scored_folds"]) >= GATE_MINIMUM
                and row["same_rule_chosen"] == row["scored_folds"]):
            return row
    return None


@memo
def admitted_rules() -> Dict[str, Rule]:
    """The rule each field takes: both gates passed, or narrowed (Phase 93).

    A first-gate rule whose nested holdout over every element passes is
    admitted as it was.  One whose nested holdout fails is admitted only on
    a declared narrowing domain it survives in (:func:`_narrowing`), and is
    demoted otherwise -- its field's empty cells become
    ``no_admitted_rule``, with both skills quoted.
    """
    out: Dict[str, Rule] = {}
    table = nested_gate_table()
    for field, rule in first_gate_rules().items():
        if table[field]["every"]["survives"]:            # type: ignore[index]
            out[field] = rule
            continue
        narrowed = _narrowing(field)
        if narrowed is not None:
            out[field] = replace(rule, domain=str(narrowed["domain"]))
    return out


@memo
def rule_table() -> Tuple[Dict[str, object], ...]:
    """One row per field: the best rule tried, its skill, and the verdict."""
    rows: List[Dict[str, object]] = []
    admitted = admitted_rules()
    for field in FIELDS:
        best = rules_for_field(field)
        row: Dict[str, object] = {
            "field": field,
            "empty_cells": empty_cells_by_field()[field],
            "not_derivable": field in NOT_DERIVABLE,
            "reason": NOT_DERIVABLE.get(field, ""),
            "rules_tried": len(best),
            "best_family": best[0].family if best else "",
            "best_predictor": best[0].predictor if best else "",
            "best_skill": best[0].skill if best else None,
            "best_skill_3dp": (round_to_thousandths(best[0].skill)
                               if best else None),
            "scored_on": best[0].scored_on if best else 0,
            "admitted": field in admitted,
            "first_gate": field in first_gate_rules(),
        }
        if field in first_gate_rules():
            nested = nested_gate_table()[field]
            row["nested_skill_3dp"] = nested["every"]["nested_skill_3dp"]  # type: ignore[index]
            row["domain"] = (admitted[field].domain or "every element"
                             if field in admitted else "demoted")
        if field in admitted:
            row["statement"] = admitted[field].statement
        rows.append(row)
    return tuple(rows)


# ===========================================================================
# 2.  THE COMPLETED VIEW
# ===========================================================================

@dataclass(frozen=True)
class Cell:
    """One cell of the completed grid: its value, and where the value came from.

    ``provenance`` is ``measured`` or ``estimated`` for a cell that carries a
    value, and empty for one that does not; ``disposition`` is the decision
    made about an empty cell and is empty for a filled one.
    """

    symbol: str
    field: str
    value: Optional[Fraction]
    provenance: str
    disposition: str
    basis: str


def estimate(symbol: str, field: str) -> Optional[Fraction]:
    """The admitted rule's value for one empty cell, or ``None``.

    Returns ``None`` when the field has no admitted rule, when the element
    already carries a measurement -- an estimate may never occupy a measured
    cell -- or when the rule's inputs are absent for this element.
    """
    element = el.element_by_symbol(symbol)
    if _value(element, field) is not None:
        return None
    rule = admitted_rules().get(field)
    if rule is None or not in_domain(symbol, rule.domain):
        return None
    if rule.family == "group":
        return _group_estimate(field, symbol)
    x = _value(element, rule.predictor)
    if x is None or rule.slope is None or rule.intercept is None:
        return None
    return rule.slope * x + rule.intercept


def _cell(element: el.Element, field: str) -> Cell:
    measured = _value(element, field)
    if measured is not None:
        return Cell(element.symbol, field, measured, "measured", "",
                    "element register")
    if field in NOT_DERIVABLE:
        return Cell(element.symbol, field, None, "", "not_derivable",
                    NOT_DERIVABLE[field])
    rule = admitted_rules().get(field)
    first = first_gate_rules().get(field)
    if rule is None and first is not None:
        nested = nested_gate_table()[field]["every"]     # type: ignore[index]
        return Cell(element.symbol, field, None, "", "no_admitted_rule",
                    f"the best rule tried ({first.family} on "
                    f"{first.predictor}) passes the first gate at skill "
                    f"{round_to_thousandths(first.skill)}, but re-chosen "
                    f"without each held-out element it scores "
                    f"{nested['nested_skill_3dp']} against the nested gate "
                    f"of {NESTED_GATE}, in every declared domain: demoted "
                    f"(Phase 93)")
    if rule is not None and not in_domain(element.symbol, rule.domain):
        nested = nested_gate_table()[field]["every"]     # type: ignore[index]
        return Cell(element.symbol, field, None, "", "no_admitted_rule",
                    f"the rule for {field} ({rule.family} on "
                    f"{rule.predictor}) is admitted only on the "
                    f"{rule.domain} elements; {element.symbol} lies outside, "
                    f"where re-chosen without each held-out element the "
                    f"rule scores {nested['nested_skill_3dp']} against the "
                    f"nested gate of {NESTED_GATE}")
    if rule is None:
        best = rules_for_field(field)
        detail = ("no rule was scored on enough elements" if not best else
                  f"the best rule tried ({best[0].family} on "
                  f"{best[0].predictor}) scores {best[0].skill} against the "
                  f"gate of {GATE_SKILL}")
        return Cell(element.symbol, field, None, "", "no_admitted_rule",
                    detail)
    value = estimate(element.symbol, field)
    if value is None:
        missing = ("no known member of its group carries the field"
                   if rule.family == "group"
                   else f"{element.symbol} carries no {rule.predictor}")
        return Cell(element.symbol, field, None, "", "inputs_absent", missing)
    where = f", admitted on the {rule.domain} elements" if rule.domain \
        else ""
    return Cell(element.symbol, field, value, "estimated", "",
                f"{rule.statement}{where}; leave-one-out error "
                f"{rule.loo_error} against {rule.baseline_error} for the "
                f"field's mean")


@memo
def completed_table() -> Tuple[Cell, ...]:
    """Every cell of the 118 x 14 grid, each with its provenance or disposition."""
    return tuple(_cell(element, field)
                 for element in el.load_element_register()
                 for field in FIELDS)


@memo
def coverage() -> Dict[str, object]:
    """How far the completed view reaches, against the register it never edits."""
    cells = completed_table()
    measured = sum(1 for c in cells if c.provenance == "measured")
    estimated = sum(1 for c in cells if c.provenance == "estimated")
    total = len(cells)
    return {
        "elements": len(el.load_element_register()),
        "fields": len(FIELDS),
        "total_cells": total,
        "measured": measured,
        "estimated": estimated,
        "filled": measured + estimated,
        "empty": total - measured - estimated,
        "measured_fraction": Fraction(measured, total),
        "filled_fraction": Fraction(measured + estimated, total),
        "register_filled_cells": int(ec.coverage_table()["filled_cells"]),
    }


@memo
def dispositions() -> Dict[str, object]:
    """The ledger: every empty cell of the register, and what was decided about it.

    ``accounted`` is the claim -- every empty cell carries exactly one of the
    four dispositions, and none is left as a failed lookup.
    """
    cells = completed_table()
    empty = [c for c in cells if c.provenance != "measured"]
    counts: Dict[str, int] = {name: 0 for name in DISPOSITIONS}
    for cell in empty:
        name = "estimated" if cell.provenance == "estimated" \
            else cell.disposition
        counts[name] = counts.get(name, 0) + 1
    by_field: Dict[str, Dict[str, int]] = {}
    for cell in empty:
        name = "estimated" if cell.provenance == "estimated" \
            else cell.disposition
        by_field.setdefault(cell.field, {})[name] = \
            by_field.setdefault(cell.field, {}).get(name, 0) + 1
    undecided = tuple(f"{c.symbol}.{c.field}" for c in empty
                      if (c.provenance != "estimated"
                          and c.disposition not in DISPOSITIONS))
    unexplained = tuple(f"{c.symbol}.{c.field}" for c in empty
                        if c.provenance != "estimated" and not c.basis)
    return {
        "empty_cells": len(empty),
        "counts": counts,
        "by_field": {k: dict(sorted(v.items())) for k, v in sorted(by_field.items())},
        "undecided": undecided,
        "unexplained": unexplained,
        "accounted": (sum(counts.values()) == len(empty)
                      and not undecided and not unexplained),
    }


def measured_view_is_the_register() -> Dict[str, object]:
    """The safety property: reading only ``measured`` cells returns the register.

    Two ways it could fail, and both are checked: a measured cell could differ
    from the register's value, or an estimate could occupy a cell the register
    fills.  Neither can happen by construction; the point of checking is that
    the construction is what is delivered.
    """
    elements = {e.symbol: e for e in el.load_element_register()}
    mismatched: List[str] = []
    overwritten: List[str] = []
    for cell in completed_table():
        registered = _value(elements[cell.symbol], cell.field)
        if cell.provenance == "measured":
            if registered != cell.value:
                mismatched.append(f"{cell.symbol}.{cell.field}")
        elif cell.provenance == "estimated" and registered is not None:
            overwritten.append(f"{cell.symbol}.{cell.field}")
    return {
        "mismatched": tuple(mismatched),
        "overwritten": tuple(overwritten),
        "holds": not mismatched and not overwritten,
    }


@memo
def element_completion_report() -> Dict[str, object]:
    """Everything this module decides, recomputed on call."""
    cover = coverage()
    ledger = dispositions()
    table = rule_table()
    admitted = admitted_rules()
    examples = tuple(
        {"symbol": c.symbol, "field": c.field, "value": c.value,
         "basis": c.basis}
        for c in completed_table()
        if c.provenance == "estimated")[:6]
    return {
        "gate": {"skill": GATE_SKILL, "minimum_scored_on": GATE_MINIMUM,
                 "statement": (
                     "A rule is admitted only if its leave-one-out mean "
                     "absolute error is at most half the error of predicting "
                     "the field's mean, scored on at least 20 elements.  The "
                     "control is the constant rule, so admission is a claim "
                     "that the rule found something rather than that it fits "
                     "closely.  Since Phase 93 its nested holdout -- the rule "
                     "re-chosen without each held-out element -- must pass "
                     "the same half, or the rule is narrowed to the one "
                     "declared domain it passes in, or demoted.")},
        "nested_gate": {
            field: {"reported_3dp": row["every"]["reported_skill_3dp"],
                    "nested_3dp": row["every"]["nested_skill_3dp"],
                    "survives": row["every"]["survives"],
                    "domains": tuple(
                        {"domain": d["domain"],
                         "nested_3dp": d["nested_skill_3dp"],
                         "scored_folds": d["scored_folds"],
                         "same_rule_chosen": d["same_rule_chosen"],
                         "survives": d["survives"]}
                        for d in row["domains"])}
            for field, row in sorted(nested_gate_table().items())},
        "demoted": tuple(sorted(set(first_gate_rules()) - set(admitted))),
        "narrowed": {k: v.domain for k, v in sorted(admitted.items())
                     if v.domain},
        "coverage": cover,
        "rules": table,
        "admitted_rules": {k: v.as_dict() for k, v in sorted(admitted.items())},
        "admitted_count": len(admitted),
        "dispositions": ledger,
        "safety": measured_view_is_the_register(),
        "examples": examples,
        "limits": (
            "No value here is written back into the element register, and the "
            "completed view is read at a provenance: asking for measurements "
            "returns exactly the register.  An estimate carries the rule that "
            "produced it and that rule's out-of-sample error, which is a "
            "measured quantity rather than a claim about the estimate itself. "
            "Fields with no admitted rule are left empty and named, and a "
            "field that no rule over this register could reach is named as "
            "that rather than as a rule failure."),
    }

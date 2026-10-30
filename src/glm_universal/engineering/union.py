"""``glm_universal.engineering.union`` -- derivation across a declared union
of formula wheels.

What this module is
-------------------
The ``derive`` frame of :mod:`glm_universal.engineering.speak` derives inside
one wheel at a time, as the corrected formula study's protocol does, and so
refuses *derive power from pressure and volume flow rate*: hydraulic power
needs the linear-dynamics wheel (``power = force * velocity``) and the fluid
wheel (``force = pressure * area``, ``volume_flow_rate = area * velocity``)
together.  This module is the second mode that ``studies/ENGINEERING_LANGUAGE_
STUDY.md`` §3 named: derive across the union of the ten wheels, and name the
union used in the answer.

Why it is not simply the union of the axioms
--------------------------------------------
Taken naively, the union of all ten wheels licenses 161 two-input formulas no
single wheel licenses, and 158 of them are physically wrong
(``studies/CONNECTED_MACHINE_STUDY.md`` §3).  The worst is
``energy = 2 * mass * speed_of_light^2``: the linear-dynamics wheel says
``energy = 1/2 * mass * velocity^2`` and ``momentum = mass * velocity``, the
photon wheel says ``energy = speed_of_light * momentum``, and eliminating the
shared names *energy* and *momentum* equates a massive body's kinetic energy
with a photon's.  The algebra is exact; the identification is false.

So a shared name is one variable only where a **junction** declares the two
wheels to mean the same measurand of the same object (:data:`JUNCTIONS`, the
table of the study's §2.1).  Every other occurrence of a name is split into a
copy per wheel -- ``energy@W5``, ``energy@W10`` -- and cannot be eliminated
against itself.  A question's names are tried against every copy; the answer
is given only when every derivation found agrees on one formula, and it names
the wheels whose axioms carry weight and the junctions it crossed.  When the
licensed union refuses but the naive union would answer, the refusal says
what the naive answer would have been and which identification it needs.

``RequestProject/GLM/ConnectedMachine.lean`` proves that splitting is sound
(``licensed_sound``: a derivation over the split names maps to one over the
naive names), that a larger union derives everything a smaller one does
(``derivable_mono``), and that the photon conflation is derivable naively and
not after splitting (``emc2_naive``, ``emc2_refused_split``).

Exact and float-free (D7): relation vectors over ``Fraction``.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from . import wheels as wh

__all__ = [
    "JUNCTIONS", "UnionAnswer", "split_system", "copies_of",
    "derive_relations", "derive_across", "naive_across", "union_census",
    "union_report",
]

#: The declared identities of ``studies/CONNECTED_MACHINE_STUDY.md`` §2.1:
#: ``(wheel, wheel) -> names that mean the same measurand in both``.  A shared
#: name absent from this table is split per wheel.
JUNCTIONS: Dict[Tuple[str, str], Tuple[str, ...]] = {
    ("W5", "W6"): ("force", "velocity"),
    ("W5", "W8"): ("mass",),
    ("W1", "W3"): ("voltage",),
    ("W4", "W9"): ("angular_velocity",),
    ("W9", "W10"): ("frequency",),
}

#: Why each declared non-identity is one (the study's §2.1, second table).
NON_IDENTITIES: Dict[Tuple[str, str], str] = {
    ("W1", "W2"): "DC values against sinusoidal amplitudes: identifying "
                  "them makes resistance equal impedance",
    ("W5", "W8"): "kinetic energy against stored heat",
    ("W5", "W10"): "a massive, non-relativistic body against a photon",
}


# ===========================================================================
# 1.  THE SPLIT SYSTEM
# ===========================================================================

def _find(parent: Dict[Tuple[str, str], Tuple[str, str]],
          x: Tuple[str, str]) -> Tuple[str, str]:
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def _classes() -> Dict[Tuple[str, str], Tuple[str, ...]]:
    """``(wheel, name) -> the wheels whose copy of name it is identified
    with``, by union-find over the junction table."""
    nodes = [(w.id, q) for w in wh.WHEELS for q in wh.wheel_quantities(w)]
    parent = {n: n for n in nodes}
    for (a, b), names in JUNCTIONS.items():
        for q in names:
            if (a, q) in parent and (b, q) in parent:
                ra, rb = _find(parent, (a, q)), _find(parent, (b, q))
                if ra != rb:
                    parent[ra] = rb
    groups: Dict[Tuple[str, str], List[str]] = {}
    for n in nodes:
        groups.setdefault(_find(parent, n), []).append(n[0])
    order = {w.id: i for i, w in enumerate(wh.WHEELS)}
    return {n: tuple(sorted(groups[_find(parent, n)], key=order.get))
            for n in nodes}


def _label(name: str, wheels: Sequence[str]) -> str:
    return f"{name}@{'+'.join(wheels)}"


def base_name(label: str) -> str:
    return label.split("@", 1)[0]


@dataclass(frozen=True)
class SplitSystem:
    """Every axiom of every wheel as a relation over split names."""

    relations: Tuple[Dict[str, Fraction], ...]
    owners: Tuple[str, ...]
    axioms: Tuple[str, ...]
    labels: Tuple[str, ...]


_SPLIT: Dict[bool, SplitSystem] = {}


def split_system(split: bool = True) -> SplitSystem:
    """The union of all ten wheels; ``split=False`` is the naive union."""
    if split in _SPLIT:
        return _SPLIT[split]
    classes = _classes()
    rels: List[Dict[str, Fraction]] = []
    owners: List[str] = []
    axioms: List[str] = []
    for w in wh.WHEELS:
        for a in w.axioms:
            r = wh.relation_vector(a)
            if split:
                r = {(k if k.startswith("#") else
                      _label(k, classes[(w.id, k)])): v for k, v in r.items()}
            rels.append(r)
            owners.append(w.id)
            axioms.append(a)
    labels = sorted({k for r in rels for k in r if not k.startswith("#")})
    system = SplitSystem(tuple(rels), tuple(owners), tuple(axioms),
                         tuple(labels))
    _SPLIT[split] = system
    return system


def copies_of(name: str, split: bool = True) -> Tuple[str, ...]:
    """The split variables a plain quantity name can mean."""
    return tuple(l for l in split_system(split).labels
                 if base_name(l) == name)


# ===========================================================================
# 2.  ONE DERIVATION OVER GIVEN RELATIONS
# ===========================================================================

@dataclass(frozen=True)
class Found:
    """One derivation: the formula over plain names, and what it used."""

    formula: str
    target: str
    inputs: Tuple[str, ...]
    wheels: Tuple[str, ...]
    weights: Tuple[Tuple[str, str, Fraction], ...]


def derive_relations(target: str, inputs: Sequence[str],
                     system: SplitSystem) -> Optional[Found]:
    """``target`` as ``c * prod(Y ** a)`` over ``inputs`` (split labels),
    solved from the system's relations -- the rule of
    :func:`glm_universal.engineering.wheels.derive_from`, over vectors:
    ``None`` when no combination leaves only the inputs, when the exponents
    are not unique, or when every exponent is zero."""
    rels = list(system.relations)
    names = system.labels
    if target not in names or any(y not in names for y in inputs):
        return None
    if target in inputs or len(set(inputs)) != len(inputs) or not inputs:
        return None
    constrained = [n for n in names if n not in inputs]
    vecs = [[r.get(c, Fraction(0)) for c in constrained] for r in rels]
    x = wh._solve(vecs, [Fraction(1) if c == target else Fraction(0)
                         for c in constrained])
    if x is None:
        return None
    n = len(rels)
    null = wh._null_space([[rels[i].get(c, Fraction(0)) for i in range(n)]
                           for c in constrained], n)
    primes = {k for r in rels for k in r if k.startswith("#")}
    for vec in null:
        for key in set(inputs) | primes:
            if sum(vec[i] * rels[i].get(key, Fraction(0)) for i in range(n)):
                return None
    combo: Dict[str, Fraction] = {}
    for w, r in zip(x, rels):
        for k, v in r.items():
            combo[k] = combo.get(k, Fraction(0)) + w * v
    powers = [(y, -combo.get(y, Fraction(0))) for y in inputs]
    if all(e == 0 for _, e in powers):
        return None
    coef = {int(k[1:]): -v for k, v in combo.items()
            if k.startswith("#") and v}
    kept = [(base_name(y), e) for y, e in powers if e]
    formula = wh.render_monomial(coef, kept)
    order = {w.id: i for i, w in enumerate(wh.WHEELS)}
    used = tuple(sorted({system.owners[i] for i in range(n) if x[i]},
                        key=order.get))
    weights = tuple((system.owners[i], system.axioms[i], x[i])
                    for i in range(n) if x[i])
    return Found(formula, target, tuple(inputs), used, weights)


# ===========================================================================
# 3.  THE QUESTION: DERIVE X FROM Y AND Z ACROSS WHEELS
# ===========================================================================

@dataclass(frozen=True)
class UnionAnswer:
    """What the union mode gave."""

    answered: bool
    formula: Optional[str]
    wheels: Tuple[str, ...]
    junctions: Tuple[str, ...]
    reason: str
    naive: Optional[str] = None
    certificate: Tuple[Tuple[str, str, Fraction], ...] = ()

    def text(self, target: str) -> str:
        if not self.answered:
            return f"refused: {self.reason}"
        cross = (f", joined at {', '.join(self.junctions)}"
                 if self.junctions else "")
        titles = ", ".join(f"{w} {wh.wheel_named(w).title}"
                           for w in self.wheels)
        return (f"{target} = {self.formula}  [derived across {titles}{cross}"
                f"; certificate: " + " + ".join(
                    f"{wt} x [{ax}]" for _, ax, wt in self.certificate)
                + "]")


def _junctions_crossed(wheels: Sequence[str]) -> Tuple[str, ...]:
    out = []
    for (a, b), names in JUNCTIONS.items():
        if a in wheels and b in wheels:
            out.extend(f"{q} ({a}={b})" for q in names)
    return tuple(out)


def naive_across(target: str, y: str, z: str) -> Optional[Found]:
    """The naive union's derivation, for the diagnosis of a refusal."""
    return derive_relations(target, (y, z), split_system(False))


def derive_across(target: str, y: str, z: str) -> UnionAnswer:
    """Answer *derive target from y and z across wheels*, or refuse."""
    system = split_system(True)
    ct, cy, cz = copies_of(target), copies_of(y), copies_of(z)
    missing = [n for n, c in ((target, ct), (y, cy), (z, cz)) if not c]
    if missing:
        return UnionAnswer(False, None, (), (),
                           f"no declared wheel names {', '.join(missing)}")
    found: Dict[str, List[Found]] = {}
    for t, a, b in itertools.product(ct, cy, cz):
        f = derive_relations(t, (a, b), system)
        if f is not None:
            found.setdefault(f.formula, []).append(f)
    if len(found) > 1:
        return UnionAnswer(False, None, (), (), "ambiguous: the licensed "
                           "union gives " + "; ".join(
                               f"{target} = {k} ({'+'.join(v[0].wheels)})"
                               for k, v in found.items()))
    if found:
        formula, fs = next(iter(found.items()))
        f = fs[0]
        wheels = tuple(dict.fromkeys(w for g in fs for w in g.wheels))
        return UnionAnswer(True, formula, wheels, _junctions_crossed(wheels),
                           "", certificate=f.weights)
    naive = naive_across(target, y, z)
    if naive is None:
        return UnionAnswer(False, None, (), (),
                           f"no union of the declared wheels derives "
                           f"{target} from {y} and {z} alone")
    conflated = []
    for (a, b), why in NON_IDENTITIES.items():
        if a in naive.wheels and b in naive.wheels:
            conflated.append(f"{a}/{b} ({why})")
    what = "; ".join(conflated) or "a name shared by two wheels that no " \
                                    "junction declares one measurand"
    return UnionAnswer(False, None, (), (),
                       f"the naive union of {'+'.join(naive.wheels)} gives "
                       f"{target} = {naive.formula}, but only by identifying "
                       f"{what}; no declared junction licenses it",
                       naive=naive.formula)


# ===========================================================================
# 4.  THE CENSUS OF THE STUDY'S §3
# ===========================================================================

def _in_one_wheel(target: str, y: str, z: str) -> Optional[str]:
    formulas = set()
    for w in wh.WHEELS:
        qs = wh.wheel_quantities(w)
        if target in qs and y in qs and z in qs:
            s = wh.derive_from(target, (y, z), w.axioms, w.id)
            if s is not None:
                formulas.add(s.formula)
    return next(iter(formulas)) if len(formulas) == 1 else (
        None if not formulas else "ambiguous")


def union_census(labels: Mapping[Tuple[str, str], bool]) -> Dict[str, object]:
    """U1-U3 over every two-input question on the ten wheels' names.

    ``labels`` is the declared physics label of each formula family (absent
    means *not a law*).  Minutes of exact linear algebra: it is a study
    measurement, not something a question runs.
    """
    naive = split_system(False)
    names = [l for l in naive.labels]
    naive_new = naive_right = naive_wrong = 0
    licensed_answered = licensed_right = licensed_wrong = 0
    in_wheel = in_wheel_agree = 0
    wrong_examples: List[str] = []
    for t in names:
        rest = [q for q in names if q != t]
        for y, z in itertools.combinations(rest, 2):
            one = _in_one_wheel(t, y, z)
            if one is not None and one != "ambiguous":
                in_wheel += 1
                got = derive_across(t, y, z)
                in_wheel_agree += got.answered and got.formula == one
                continue
            f = derive_relations(t, (y, z), naive)
            if f is None:
                continue
            naive_new += 1
            right = bool(labels.get((t, f.formula), False))
            naive_right += right
            naive_wrong += not right
            got = derive_across(t, y, z)
            if got.answered:
                licensed_answered += 1
                ok = bool(labels.get((t, got.formula or ""), False))
                licensed_right += ok
                licensed_wrong += not ok
                if not ok:
                    wrong_examples.append(f"{t} = {got.formula}")
    return {"naive_new": naive_new, "naive_right": naive_right,
            "naive_wrong": naive_wrong,
            "licensed_answered": licensed_answered,
            "licensed_right": licensed_right,
            "licensed_wrong": licensed_wrong,
            "licensed_refused": naive_new - licensed_answered,
            "in_wheel": in_wheel, "in_wheel_agree": in_wheel_agree,
            "wrong_examples": wrong_examples}


def union_report() -> Dict[str, object]:
    """The cheap half: the junction table and the split system's size."""
    split, naive = split_system(True), split_system(False)
    return {"junctions": {f"{a}/{b}": list(v)
                          for (a, b), v in JUNCTIONS.items()},
            "non_identities": {f"{a}/{b}": v
                               for (a, b), v in NON_IDENTITIES.items()},
            "axioms": len(split.relations),
            "naive_names": len(naive.labels),
            "split_names": len(split.labels),
            "lean_file": "RequestProject/GLM/ConnectedMachine.lean"}

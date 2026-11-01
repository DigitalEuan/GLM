"""``glm_universal.engineering.domains`` -- the domain wheels W11-W15, their
junctions, the *across domains* frame and the census of the union.

Phase 157 (``studies/DOMAIN_WHEELS_STUDY.md``):

* **the demand census** (§2.1, :func:`demand_census`) -- every string
  constant of at least nine characters holding a space, in every module of
  ``glm_universal/evaluation/``, lower-cased and searched longest name first
  for every quantity name of the physics register of at least four
  characters (underscores read as spaces, whole words only, a matched span
  removed before the next name is tried); a name *lacks a wheel* when no
  wheel of ``engineering/wheels.WHEELS`` names it;
* **the five wheels** W11-W15 (:mod:`glm_universal.wheels`) and **the
  junctions** (§2.3): a name a wheel shares with another is one variable
  only across a declared junction, otherwise split per wheel, by the rule of
  Phase 66 (:mod:`glm_universal.engineering.union`, read and not modified);
* **the frame** *derive X from Y [, Z [and W]] across domains*
  (:func:`derive_domains`, :func:`frame_domains`): every copy of every asked
  name is tried over the split union of the fifteen wheels, and the answer is
  given only when every derivation found agrees on one formula; the aliases
  ``speed`` → ``velocity`` and ``distance`` → ``length`` are read and said;
* **the battery** (§2.4, :func:`battery`), read from
  ``evaluation/domain_cases.py`` when it is present, compared as relations up
  to a positive rational multiple (:func:`same_relation`);
* **the census of the union** (§2.5, :func:`census`) with the post-hoc
  reading of §7.3 beside it (a one-wheel answer is in-wheel; a label matches
  up to any non-zero multiple), stored by :func:`write_census` in
  ``engineering/_data/domains.json`` beside the digest of the code;
* :func:`domains_report` -- the marks D1-D5.

The junction table of the fifteen-wheel union is a parameter throughout, so
Phase 158's four variants (:mod:`glm_universal.engineering.oscillator_junction`)
and Phase 170's per-question pins and joins (``context_frames``) run the same
solver.

Exact and float-free (D7): relation vectors over ``Fraction``.

*Reconstructed 31 October 2026 (repository check): the original was lost in
the October 2026 reorganisation (the previous file here was a stub created 29
October 2026); rebuilt from studies/DOMAIN_WHEELS_STUDY.md (§§2.1-2.5, §7),
studies/OSCILLATOR_JUNCTION_STUDY.md §2.2, studies/CONTEXT_FRAMES_STUDY.md
§1, the CLI handler ``_domains`` in glm_universal/tools.py, the wheel
registry (glm_universal/wheels) and engineering/union.py.  The battery and
the labels of §§2.4-2.5 lived in ``evaluation/domain_cases.py``, which was
lost with this module and is not reconstructed here: without it D1 and D3
are reported not measured (missed).*
"""
from __future__ import annotations

import ast
import itertools
import json
import re
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import (Any, Dict, FrozenSet, Iterable, List, Mapping, Optional,
                    Sequence, Tuple)

from .. import integrity
from ..wheels import (ALL_WHEELS, DOMAIN_WHEELS, JUNCTIONS, NON_IDENTITIES,
                      ALIASES)
from ..wheels.junctions import domain as _dj
from ..wheels.junctions import phase66 as _p66
from . import union as un
from . import wheels as wh

__all__ = [
    "DOMAIN_WHEELS", "DOMAIN_JUNCTIONS", "DOMAIN_NON_IDENTITIES", "ALIASES",
    "ALIAS_REASONS", "DEMANDED", "PHASE66_JUNCTIONS", "DOMAIN_JUNCTION_TABLE",
    "union_junctions", "split_system", "copies_of", "DomainAnswer",
    "derive_domains", "read_question", "frame_domains", "same_relation",
    "same_relation_any", "relation_vector", "battery", "demand_census",
    "axiom_consistency",
    "lean_check", "in_one_wheel", "census", "write_census", "census_state",
    "domains_report", "module_digest",
]

_HERE = Path(__file__).resolve().parent
_CENSUS_PATH = _HERE / "_data" / "domains.json"

#: The five domain wheels' ids.
DOMAIN_IDS: Tuple[str, ...] = tuple(w.id for w in DOMAIN_WHEELS)

#: The Phase 66 junctions (W1-W10) and the ten Phase 157 junctions as
#: shipped (the W9/W13 junction is Phase 158's rule B).
PHASE66_JUNCTIONS: Dict[Tuple[str, str], Tuple[str, ...]] = dict(_p66.JUNCTIONS)
DOMAIN_JUNCTION_TABLE: Dict[Tuple[str, str], Tuple[str, ...]] = dict(_dj.JUNCTIONS)

#: Why each alias reads one name as another (§2.3).
ALIAS_REASONS: Dict[str, str] = {
    "speed": "the wheels relate magnitudes, and a speed is the magnitude of "
             "a velocity",
    "distance": "a distance travelled is a length",
}

#: The names the demand census put forward (§2.5, D4).
DEMANDED: Tuple[str, ...] = ("density", "length", "speed", "time",
                             "molar_mass", "period", "angular_frequency",
                             "volume", "inductance", "spring_constant")

#: The theorems of ``DomainWheels.lean`` (§5).
LEAN_FILE = "DomainWheels.lean"
LEAN_THEOREMS: Tuple[str, ...] = ("oscillator_naive", "oscillator_refused_split",
                                  "swept_volume_licensed")


def _format_junctions() -> Dict[str, Dict[str, Any]]:
    """The ten domain junctions, keyed ``"W5/W11"`` (the CLI's format)."""
    return {f"{a}/{b}": {"names": list(names)}
            for (a, b), names in DOMAIN_JUNCTION_TABLE.items()}


DOMAIN_JUNCTIONS: Dict[str, Dict[str, Any]] = _format_junctions()

#: The domain non-identities, keyed the same way.
DOMAIN_NON_IDENTITIES: Dict[str, str] = {
    f"{a}/{b}": why for (a, b), why in _dj.NON_IDENTITIES.items()}


def union_junctions(domain: Optional[Mapping[Tuple[str, str], Sequence[str]]] = None,
                    phase66: Optional[Mapping[Tuple[str, str], Sequence[str]]] = None
                    ) -> Dict[Tuple[str, str], Tuple[str, ...]]:
    """The fifteen-wheel union's junction table: Phase 66's and the domain
    table (each defaulting to the shipped one)."""
    out: Dict[Tuple[str, str], Tuple[str, ...]] = {}
    for table in (PHASE66_JUNCTIONS if phase66 is None else phase66,
                  DOMAIN_JUNCTION_TABLE if domain is None else domain):
        for pair, names in table.items():
            out[pair] = tuple(dict.fromkeys(tuple(out.get(pair, ())) + tuple(names)))
    return out


# ===========================================================================
# 1.  THE SPLIT SYSTEM OVER FIFTEEN WHEELS
# ===========================================================================

_ORDER = {w.id: i for i, w in enumerate(ALL_WHEELS)}
_SPLITS: Dict[Tuple[Any, ...], un.SplitSystem] = {}


def _key(junctions: Mapping[Tuple[str, str], Sequence[str]]) -> Tuple[Any, ...]:
    return tuple(sorted((a, b, tuple(sorted(v))) for (a, b), v in junctions.items()))


def _classes(junctions: Mapping[Tuple[str, str], Sequence[str]],
             wheels: Sequence[wh.Wheel]) -> Dict[Tuple[str, str], Tuple[str, ...]]:
    """``(wheel, name) -> the wheels whose copy of name it is one variable
    with``, by union-find over the junction table."""
    nodes = [(w.id, q) for w in wheels for q in wh.wheel_quantities(w)]
    parent = {n: n for n in nodes}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for (a, b), names in junctions.items():
        for q in names:
            if (a, q) in parent and (b, q) in parent:
                ra, rb = find((a, q)), find((b, q))
                if ra != rb:
                    parent[ra] = rb
    groups: Dict[Tuple[str, str], List[str]] = {}
    for n in nodes:
        groups.setdefault(find(n), []).append(n[0])
    return {n: tuple(sorted(groups[find(n)], key=_ORDER.get)) for n in nodes}


def split_system(junctions: Optional[Mapping[Tuple[str, str], Sequence[str]]] = None,
                 split: bool = True,
                 wheels: Sequence[wh.Wheel] = ALL_WHEELS) -> un.SplitSystem:
    """The union of ``wheels`` (default: all fifteen) with every shared name
    split except across a junction of ``junctions`` (default: the shipped
    table); ``split=False`` is the naive union."""
    junctions = union_junctions() if junctions is None else junctions
    key = (_key(junctions) if split else "naive", tuple(w.id for w in wheels))
    if key in _SPLITS:
        return _SPLITS[key]
    classes = _classes(junctions, wheels) if split else {}
    rels: List[Dict[str, Fraction]] = []
    owners: List[str] = []
    axioms: List[str] = []
    for w in wheels:
        for a in w.axioms:
            r = wh.relation_vector(a)
            if split:
                r = {(k if k.startswith("#") else
                      f"{k}@{'+'.join(classes[(w.id, k)])}"): v
                     for k, v in r.items()}
            rels.append(r)
            owners.append(w.id)
            axioms.append(a)
    labels = sorted({k for r in rels for k in r if not k.startswith("#")})
    system = un.SplitSystem(tuple(rels), tuple(owners), tuple(axioms),
                            tuple(labels))
    _SPLITS[key] = system
    return system


def copies_of(name: str, system: un.SplitSystem) -> Tuple[str, ...]:
    """The split variables a plain name can mean in ``system``."""
    return tuple(l for l in system.labels if un.base_name(l) == name)


def _wheels_of(label: str) -> Tuple[str, ...]:
    return tuple(label.split("@", 1)[1].split("+")) if "@" in label else ()


def derive_relations(target: str, inputs: Sequence[str],
                     system: un.SplitSystem) -> Optional[un.Found]:
    """``target`` as ``c * prod(Y ** a)`` over ``inputs`` (split labels),
    solved from the system's relations: Phase 66's rule
    (:func:`glm_universal.engineering.union.derive_relations`, which orders
    the wheels it names among the ten only), with the wheels ordered among
    all fifteen.  ``None`` when no combination leaves only the inputs, when
    the exponents are not unique, or when every exponent is zero."""
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
    kept = [(un.base_name(y), e) for y, e in powers if e]
    formula = wh.render_monomial(coef, kept)
    used = tuple(sorted({system.owners[i] for i in range(n) if x[i]},
                        key=lambda w: _ORDER.get(w, len(_ORDER))))
    weights = tuple((system.owners[i], system.axioms[i], x[i])
                    for i in range(n) if x[i])
    return un.Found(formula, target, tuple(inputs), used, weights)


# ===========================================================================
# 2.  THE FRAME: DERIVE X FROM Y [, Z [AND W]] ACROSS DOMAINS
# ===========================================================================

@dataclass(frozen=True)
class DomainAnswer:
    """What the domains frame gave."""

    answered: bool
    target: str
    inputs: Tuple[str, ...]
    formula: Optional[str]
    wheels: Tuple[str, ...]
    junctions: Tuple[str, ...]
    reason: str
    aliases: Tuple[str, ...] = ()
    naive: Optional[str] = None
    certificate: Tuple[Tuple[str, str, Fraction], ...] = ()
    found: Tuple[Tuple[str, Tuple[str, ...]], ...] = ()

    @property
    def equation(self) -> Optional[str]:
        return None if self.formula is None else f"{self.target} = {self.formula}"

    def text(self) -> str:
        said = ("; ".join(self.aliases) + "; ") if self.aliases else ""
        if not self.answered:
            return f"refused: {said}{self.reason}"
        cross = (f", joined at {', '.join(self.junctions)}"
                 if self.junctions else "")
        titles = ", ".join(f"{w} {_title(w)}" for w in self.wheels)
        return (f"{self.target} = {self.formula}  [{said}derived across "
                f"domains: {titles}{cross}; certificate: "
                + " + ".join(f"{wt} x [{ax}]" for _, ax, wt in self.certificate)
                + "]")


def _title(wheel_id: str) -> str:
    for w in ALL_WHEELS:
        if w.id == wheel_id:
            return w.title
    return wheel_id


def _junctions_crossed(wheels: Sequence[str],
                       junctions: Mapping[Tuple[str, str], Sequence[str]]
                       ) -> Tuple[str, ...]:
    out = []
    for (a, b), names in junctions.items():
        if a in wheels and b in wheels:
            out.extend(f"{q} ({a}={b})" for q in names)
    return tuple(out)


def _alias(name: str) -> Tuple[str, Optional[str]]:
    if name in ALIASES:
        return ALIASES[name], (f"read {name} as {ALIASES[name]} "
                               f"({ALIAS_REASONS.get(name, 'a declared alias')})")
    return name, None


def derive_domains(target: str, inputs: Sequence[str],
                   junctions: Optional[Mapping[Tuple[str, str], Sequence[str]]] = None,
                   pins: Optional[Mapping[str, str]] = None,
                   wheels: Sequence[wh.Wheel] = ALL_WHEELS,
                   non_identities: Optional[Mapping[Tuple[str, str], str]] = None
                   ) -> DomainAnswer:
    """Answer *derive target from inputs across domains*, or refuse.

    Every copy of every asked name is tried over the split union; the answer
    is given only when every derivation found agrees on one formula.
    ``pins`` maps a name to a wheel: only the copies whose junction class
    holds that wheel are tried (Phase 170's pin; it only removes
    candidates).  ``junctions`` replaces the union's table (Phase 158's
    variants, Phase 170's join)."""
    junctions = union_junctions() if junctions is None else junctions
    non_identities = NON_IDENTITIES if non_identities is None else non_identities
    notes: List[str] = []
    t, note = _alias(target)
    if note:
        notes.append(note)
    ins: List[str] = []
    for y in inputs:
        y2, note = _alias(y)
        if note:
            notes.append(note)
        ins.append(y2)
    system = split_system(junctions, True, wheels)
    copies = {n: copies_of(n, system) for n in [t] + ins}
    missing = [n for n, c in copies.items() if not c]
    base = dict(target=t, inputs=tuple(ins), aliases=tuple(notes))
    if missing:
        return DomainAnswer(False, formula=None, wheels=(), junctions=(),
                            reason=f"no declared wheel names {', '.join(missing)}",
                            **base)
    if len(set([t] + ins)) != len(ins) + 1:
        return DomainAnswer(False, formula=None, wheels=(), junctions=(),
                            reason="a name is asked twice", **base)
    if pins:
        for name, wheel in pins.items():
            if name in copies:
                copies[name] = tuple(c for c in copies[name]
                                     if wheel in _wheels_of(c))
    found: Dict[str, List[un.Found]] = {}
    for combo in itertools.product(copies[t], *(copies[y] for y in ins)):
        f = derive_relations(combo[0], tuple(combo[1:]), system)
        if f is not None:
            found.setdefault(f.formula, []).append(f)
    summary = tuple((k, tuple(dict.fromkeys(w for g in v for w in g.wheels)))
                    for k, v in found.items())
    if len(found) > 1:
        return DomainAnswer(False, formula=None, wheels=(), junctions=(),
                            reason="ambiguous: the licensed union gives " +
                            "; ".join(f"{t} = {k} ({'+'.join(w)})"
                                      for k, w in summary),
                            found=summary, **base)
    if found:
        formula, fs = next(iter(found.items()))
        used = tuple(sorted(dict.fromkeys(w for g in fs for w in g.wheels),
                            key=_ORDER.get))
        return DomainAnswer(True, formula=formula, wheels=used,
                            junctions=_junctions_crossed(used, junctions),
                            reason="", certificate=fs[0].weights,
                            found=summary, **base)
    naive = derive_relations(t, tuple(ins), split_system(junctions, False,
                                                         wheels))
    if naive is None:
        return DomainAnswer(False, formula=None, wheels=(), junctions=(),
                            reason=f"no union of the declared wheels derives "
                                   f"{t} from {' and '.join(ins)} alone"
                                   + (" in this frame" if pins else ""),
                            **base)
    conflated = [f"{a}/{b} ({why})" for (a, b), why in non_identities.items()
                 if a in naive.wheels and b in naive.wheels]
    what = "; ".join(conflated) or ("a name shared by two wheels that no "
                                     "junction declares one measurand")
    return DomainAnswer(False, formula=None, wheels=(), junctions=(),
                        reason=f"the naive union of {'+'.join(naive.wheels)} "
                               f"gives {t} = {naive.formula}, but only by "
                               f"identifying {what}; no declared junction "
                               f"licenses it",
                        naive=naive.formula, **base)


_QUESTION = re.compile(r"^(?:derive|express) (.+?) (?:from|in terms of) (.+?) "
                       r"across domains(?: where (.+))?$")


def _name(words: str) -> str:
    w = re.sub(r"^(?:the|a|an)\s+", "", words.strip())
    return re.sub(r"\s+", "_", w)


def read_question(text: str) -> Optional[Tuple[str, Tuple[str, ...], Optional[str]]]:
    """``(target, inputs, where-clause)`` of an *across domains* question
    (lower-cased, trailing punctuation dropped), or ``None``."""
    t = re.sub(r"\s+", " ", text.strip().lower().rstrip("?.! "))
    m = _QUESTION.match(t)
    if not m:
        return None
    target, rest, where = m.group(1), m.group(2), m.group(3)
    parts = [p for p in re.split(r",\s*(?:and\s+)?|\s+and\s+", rest) if p.strip()]
    if not 1 <= len(parts) <= 3:
        return None
    return _name(target), tuple(_name(p) for p in parts), where


def frame_domains(t: str):
    """The engineering surface's *domains* frame: ``None`` for text that is
    not an *across domains* question; an ``EngAnswer``, or a ``Refusal``
    raised with the reason.  A ``where`` clause is read by
    :mod:`glm_universal.engineering.context_frames`."""
    from .speak import EngAnswer, Refusal
    got = read_question(t)
    if got is None:
        return None
    target, inputs, where = got
    if where is not None:
        from . import context_frames as cf
        ans = cf.derive_in_context(target, inputs, where)
    else:
        ans = derive_domains(target, inputs)
    if not ans.answered:
        raise Refusal(ans.text()[len("refused: "):])
    return EngAnswer(
        "domains", ans.text(), "derive",
        (f"wheels used: {', '.join(ans.wheels)}",
         "junctions crossed: " + (", ".join(ans.junctions) or "none"),
         "combination: " + " + ".join(f"{wt} x [{ax}]"
                                      for _, ax, wt in ans.certificate)),
        {"formula": ans.formula or "", "wheels": "+".join(ans.wheels)})


# ===========================================================================
# 3.  COMPARING RELATIONS, AND THE BATTERY
# ===========================================================================

def _ratio(a: Mapping[str, Fraction], b: Mapping[str, Fraction]) -> Optional[Fraction]:
    keys = {k for k, v in a.items() if v} | {k for k, v in b.items() if v}
    lam = None
    for k in sorted(keys):
        x, y = a.get(k, Fraction(0)), b.get(k, Fraction(0))
        if not x or not y:
            return None
        r = Fraction(x) / Fraction(y)
        if lam is None:
            lam = r
        elif r != lam:
            return None
    return lam


def _exponent(node: ast.AST) -> Fraction:
    """A rational exponent literal: ``2``, ``-1``, ``(1/2)``, ``(-3/2)``."""
    if (isinstance(node, ast.Constant) and isinstance(node.value, int)
            and not isinstance(node.value, bool)):
        return Fraction(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_exponent(node.operand)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        den = _exponent(node.right)
        if den == 0:
            raise ValueError("a zero denominator in an exponent")
        return _exponent(node.left) / den
    raise ValueError("an exponent must be a rational literal")


def _log_vector(text: str) -> Dict[str, Fraction]:
    """The exponent vector of a positive monomial (names, positive integer
    literals, ``*``, ``/`` and rational powers, so a rendered formula such
    as ``(1 / inductance / capacitance)^(1/2)`` is read); coefficient keys
    are ``#p`` for a prime ``p``, as in ``engineering/wheels``."""
    try:
        tree = ast.parse(text.replace("^", "**").strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"not a monomial: {text!r}") from exc

    def add(a: Dict[str, Fraction], b: Mapping[str, Fraction],
            k: Fraction = Fraction(1)) -> Dict[str, Fraction]:
        out = dict(a)
        for name, e in b.items():
            out[name] = out.get(name, Fraction(0)) + k * e
        return out

    def visit(node: ast.AST) -> Dict[str, Fraction]:
        if isinstance(node, ast.Name):
            return {node.id: Fraction(1)}
        if (isinstance(node, ast.Constant) and isinstance(node.value, int)
                and not isinstance(node.value, bool)):
            if node.value <= 0:
                raise ValueError("a coefficient must be a positive integer")
            return dict(wh._prime_exponents(node.value))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            return add(visit(node.left), visit(node.right))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return add(visit(node.left), visit(node.right), Fraction(-1))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            return add({}, visit(node.left), _exponent(node.right))
        raise ValueError(f"unsupported syntax in {text!r}")

    return visit(tree.body)


def relation_vector(equation: str) -> Dict[str, Fraction]:
    """The relation vector of ``L = R`` (``L``'s exponents less ``R``'s),
    reading rational powers: ``x = y^(1/2)`` gives ``{x: 1, y: -1/2}``.  On
    integer powers it is ``engineering.wheels.relation_vector``."""
    if equation.count("=") != 1:
        raise ValueError("an equation needs exactly one '='")
    lhs, rhs = (part.strip() for part in equation.split("="))
    v = _log_vector(lhs)
    for k, e in _log_vector(rhs).items():
        v[k] = v.get(k, Fraction(0)) - e
    return {k: e for k, e in v.items() if e}


def same_relation(derived: str, declared: str) -> bool:
    """Two equations are the same relation up to a *positive* rational
    multiple of their relation vectors (§2.4: ``x = y^(1/2)`` matches
    ``x^2 = y``)."""
    lam = _ratio(relation_vector(derived), relation_vector(declared))
    return lam is not None and lam > 0


def same_relation_any(derived: str, declared: str) -> bool:
    """The post-hoc reading (§7.3): up to any non-zero multiple."""
    return _ratio(relation_vector(derived),
                  relation_vector(declared)) is not None


def _domain_cases():
    try:
        from ..evaluation import domain_cases as dc  # type: ignore
    except ImportError:
        return None
    return dc


def _case_fields(case: Any) -> Tuple[str, str, Optional[str]]:
    if isinstance(case, (tuple, list)):
        cid, question, law = (list(case) + [None, None, None])[:3]
        return str(cid), str(question), law
    return (str(getattr(case, "id")), str(getattr(case, "question")),
            getattr(case, "law", None) or getattr(case, "expect_law", None))


def battery(cases: Optional[Sequence[Any]] = None,
            junctions: Optional[Mapping[Tuple[str, str], Sequence[str]]] = None,
            where: Optional[str] = None) -> Dict[str, Any]:
    """The declared battery (§2.4): each case ``(id, question, law)`` --
    ``law`` the declared equation, or ``None`` for a declared refusal -- read
    by the frame's own parser over the given junction table (``where``
    appends a context clause to every question, Phase 170's X7).  Without
    ``evaluation/domain_cases.py`` (and no ``cases`` given) the battery is
    not available and nothing is graded."""
    if cases is None:
        dc = _domain_cases()
        cases = getattr(dc, "CASES", None) if dc is not None else None
    if cases is None:
        return {"available": False,
                "reason": "evaluation/domain_cases.py (the battery of "
                          "DOMAIN_WHEELS_STUDY.md §2.4) is not present",
                "tally": {"questions": 0}, "rows": []}
    rows = []
    tally = {"questions": 0, "answer_cases": 0, "refusal_cases": 0,
             "correct": 0, "correct_refusals": 0, "refused": 0, "wrong": 0,
             "unread": 0}
    for case in cases:
        cid, question, law = _case_fields(case)
        q = question if where is None else (
            question.rstrip("?.! ") + f" where {where}")
        got = read_question(q)
        tally["questions"] += 1
        tally["answer_cases" if law else "refusal_cases"] += 1
        if got is None:
            grade, ans = "unread", None
        else:
            target, inputs, wh_clause = got
            if wh_clause is not None:
                from . import context_frames as cf
                ans = cf.derive_in_context(target, inputs, wh_clause,
                                           junctions=junctions)
            else:
                ans = derive_domains(target, inputs, junctions)
            if law:
                if not ans.answered:
                    grade = "refused"
                else:
                    grade = ("correct" if same_relation(ans.equation, law)
                             else "wrong")
            else:
                grade = "wrong" if ans.answered else "correct_refusals"
        tally[grade] += 1
        rows.append({"id": cid, "question": question, "law": law,
                     "grade": grade,
                     "answer": None if ans is None else ans.text()})
    return {"available": True, "tally": tally, "rows": rows}


def _labels() -> Optional[List[str]]:
    """The declared laws of §2.5 (``DOMAIN_LABELS``), as equations, or
    ``None`` without ``evaluation/domain_cases.py``."""
    dc = _domain_cases()
    labels = getattr(dc, "DOMAIN_LABELS", None) if dc is not None else None
    if labels is None:
        return None
    out = []
    for item in labels:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, (tuple, list)) and len(item) >= 2:
            out.append(f"{item[0]} = {item[1]}")
    return out


# ===========================================================================
# 4.  THE DEMAND CENSUS, THE AXIOMS AND THE LEAN FILE
# ===========================================================================

def _evaluation_strings() -> List[str]:
    root = _HERE.parent / "evaluation"
    out: List[str] = []
    for path in sorted(root.glob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and len(node.value) >= 9 and " " in node.value):
                out.append(node.value)
    return out


def demand_census(strings: Optional[Sequence[str]] = None,
                  names: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """§2.1: how many evaluation strings mention each register quantity, and
    which of the mentioned names no wheel of the ten holds."""
    if strings is None:
        strings = _evaluation_strings()
    if names is None:
        from ..data_objects.physics import load_physics_register
        names = [q.name for q in load_physics_register()]
    names = sorted({n for n in names if len(n) >= 4},
                   key=lambda n: (-len(n.replace("_", " ")), n))
    patterns = [(n, re.compile(r"(?<![a-z0-9_])" + re.escape(n.replace("_", " "))
                               + r"(?![a-z0-9_])")) for n in names]
    counts: Dict[str, int] = {}
    for s in strings:
        text = s.lower()
        hit = set()
        for n, pat in patterns:
            if pat.search(text):
                hit.add(n)
                text = pat.sub(" ", text)
        for n in hit:
            counts[n] = counts.get(n, 0) + 1
    held = {q for w in wh.WHEELS for q in wh.wheel_quantities(w)}
    lacking = sorted(((n, c) for n, c in counts.items() if n not in held),
                     key=lambda nc: (-nc[1], nc[0]))
    return {"strings": len(strings), "names": len(names),
            "mentioned": len(counts), "lacking": lacking}


def axiom_consistency(layer: str = "si7") -> Dict[str, Any]:
    """Every axiom of W11-W15 checked for dimensional consistency."""
    rows = []
    for w in DOMAIN_WHEELS:
        for a in w.axioms:
            c = wh.consistency(a, layer)
            rows.append({"wheel": w.id, "axiom": a,
                         "consistent": None if c is None else c["consistent"],
                         "residual": None if c is None else
                         {k: str(v) for k, v in c["residual"].items()}})
    return {"layer": layer, "axioms": len(rows),
            "consistent": sum(1 for r in rows if r["consistent"]),
            "rows": rows}


def lean_check(name: str, theorems: Sequence[str]) -> Dict[str, Any]:
    """Whether a Lean file of the development declares ``theorems`` and holds
    no ``sorry`` (read from the text; the build is the parent's check)."""
    from .. import constants
    path = constants.lean_file(name)
    if not path.exists():
        return {"file": name, "present": False, "declared": len(theorems),
                "theorems": 0, "missing": list(theorems), "sorry": None}
    text = path.read_text(encoding="utf-8")
    code = re.sub(r"/-.*?-/", " ", text, flags=re.S)
    code = re.sub(r"--[^\n]*", " ", code)
    have = [t for t in theorems
            if re.search(r"\b(?:theorem|lemma)\s+" + re.escape(t) + r"\b", code)]
    return {"file": name, "present": True, "declared": len(theorems),
            "theorems": len(have),
            "missing": [t for t in theorems if t not in have],
            "sorry": len(re.findall(r"\bsorry\b", code))}


def _lean_clean(c: Mapping[str, Any]) -> bool:
    return bool(c.get("present")) and c["theorems"] == c["declared"] \
        and c["sorry"] == 0


# ===========================================================================
# 5.  THE CENSUS OF THE UNION
# ===========================================================================

def in_one_wheel(target: str, y: str, z: str) -> Optional[str]:
    """The one-wheel formula over the wheels holding all three names (the
    census code's reading of *in-wheel*); ``"ambiguous"`` when they
    disagree, ``None`` when none derives it."""
    formulas = set()
    for w in ALL_WHEELS:
        qs = wh.wheel_quantities(w)
        if target not in qs or y not in qs or z not in qs:
            continue
        s = wh.derive_from(target, (y, z), w.axioms, w.id)
        if s is not None:
            formulas.add(s.formula)
    if not formulas:
        return None
    return next(iter(formulas)) if len(formulas) == 1 else "ambiguous"


def _census_row(args) -> Optional[Dict[str, Any]]:
    t, y, z, junctions_items = args
    junctions = {(a, b): v for a, b, v in junctions_items}
    one = in_one_wheel(t, y, z)
    if one is not None and one != "ambiguous":
        return {"kind": "in_wheel"}
    row: Dict[str, Any] = {"kind": "other", "t": t, "y": y, "z": z}
    got = derive_domains(t, (y, z), junctions)
    if got.answered:
        ten = un.derive_across(t, y, z)
        if not ten.answered:
            row["kind"] = "gained"
            row["formula"] = got.formula
            row["wheels"] = list(got.wheels)
            # §7.3's post-hoc reading: an answer the union gives from one
            # wheel alone is in-wheel.
            row["one_wheel"] = len(got.wheels) == 1
    naive = derive_relations(t, (y, z), split_system(junctions, False))
    if naive is not None:
        row["naive"] = naive.formula
        row["licensed"] = got.formula if got.answered else None
    if row["kind"] == "other" and "naive" not in row:
        return None
    return row


def census(junctions: Optional[Mapping[Tuple[str, str], Sequence[str]]] = None,
           names: Optional[Sequence[str]] = None, jobs: int = 1,
           labels: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """§2.5 over every question *derive t from y and z* on the names of the
    fifteen wheels (or ``names``): in-wheel, gained (the licensed fifteen
    answer, no wheel holding all three names does, the licensed ten do not),
    right (a declared law, positive multiple), naive-new and its refusals;
    and the post-hoc reading (one-wheel answers in-wheel, labels up to any
    non-zero multiple).  Tens of minutes for the whole union; ``jobs``
    processes."""
    junctions = union_junctions() if junctions is None else junctions
    if names is None:
        names = sorted({q for w in ALL_WHEELS for q in wh.wheel_quantities(w)})
    labels = _labels() if labels is None else list(labels)
    items = tuple((a, b, tuple(v)) for (a, b), v in junctions.items())
    questions = [(t, y, z, items) for t in names
                 for y, z in itertools.combinations([q for q in names if q != t], 2)]
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            rows = list(pool.map(_census_row, questions, chunksize=64))
    else:
        rows = [_census_row(q) for q in questions]

    def declared(t: str, formula: str, any_multiple: bool = False) -> Optional[bool]:
        if labels is None:
            return None
        eq = f"{t} = {formula}"
        test = same_relation_any if any_multiple else same_relation
        return any(test(eq, lab) for lab in labels)

    in_wheel = sum(1 for r in rows if r and r["kind"] == "in_wheel")
    gained = [r for r in rows if r and r["kind"] == "gained"]
    naive_rows = [r for r in rows if r and "naive" in r]
    naive_new = [r for r in naive_rows if declared(r["t"], r["naive"]) is not True]
    gained_right = (None if labels is None else
                    sum(1 for r in gained if declared(r["t"], r["formula"])))
    naive_refused = (None if labels is None else
                     sum(1 for r in naive_new if r["licensed"] is None
                         or declared(r["t"], r["licensed"])))
    reread = [r for r in gained if not r["one_wheel"]]
    distinct = sorted({(r["t"], r["formula"], "+".join(r["wheels"]))
                       for r in gained})
    return {
        "names": len(names), "questions": len(questions),
        "in_wheel": in_wheel, "gained": len(gained),
        "gained_right": gained_right,
        "naive_new": None if labels is None else len(naive_new),
        "naive_answers": len(naive_rows),
        "naive_refused": naive_refused,
        "labelled": labels is not None,
        "distinct": [list(d) for d in distinct],
        "post_hoc": {"one_wheel": len(gained) - len(reread),
                     "gained": len(reread),
                     "right": (None if labels is None else
                               sum(1 for r in reread
                                   if declared(r["t"], r["formula"], True)))},
        "rows": gained,
    }


# ===========================================================================
# 6.  THE STORED CENSUS AND THE REPORT
# ===========================================================================

_SOURCES: Tuple[str, ...] = (
    "engineering/domains.py", "engineering/union.py", "engineering/wheels.py",
    "wheels/__init__.py", "wheels/w11.py", "wheels/w12.py", "wheels/w13.py",
    "wheels/w14.py", "wheels/w15.py", "wheels/junctions/domain.py",
    "wheels/junctions/phase66.py",
)


def module_digest() -> str:
    root = _HERE.parent
    return integrity.tree_digest([root / n for n in sorted(set(_SOURCES))],
                                 root)


def _read_census() -> Optional[Dict[str, Any]]:
    if not _CENSUS_PATH.exists():
        return None
    try:
        return json.loads(_CENSUS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def census_state() -> Dict[str, Any]:
    """``{"present", "fresh", "verdict"}`` for the stored census."""
    stored = _read_census()
    if stored is None:
        return {"present": False, "fresh": False, "verdict": "absent"}
    fresh = stored.get("source_digest") == module_digest()
    return {"present": True, "fresh": fresh,
            "verdict": "current" if fresh else "stale"}


def write_census(jobs: int = 2) -> str:
    """Take the census of the union afresh (tens of minutes) and store it in
    ``engineering/_data/domains.json`` beside the digest of the code."""
    data = {"census": census(jobs=jobs), "source_digest": module_digest()}
    _CENSUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CENSUS_PATH.write_text(json.dumps(data, indent=1, sort_keys=True,
                                       ensure_ascii=False, default=str) + "\n",
                            encoding="utf-8")
    return str(_CENSUS_PATH)


def _wheel_dicts() -> List[Dict[str, Any]]:
    return [{"id": w.id, "title": w.title, "axioms": list(w.axioms)}
            for w in DOMAIN_WHEELS]


def _marks(bat: Mapping[str, Any], cen: Optional[Mapping[str, Any]],
           axioms: Mapping[str, Any], lean: Mapping[str, Any]) -> Dict[str, bool]:
    held = {q for w in ALL_WHEELS for q in wh.wheel_quantities(w)}
    demanded = all(ALIASES.get(n, n) in held for n in DEMANDED)
    t = bat.get("tally", {})
    d1 = bool(bat.get("available")) and t.get("wrong", 1) == 0 \
        and t.get("correct") == t.get("answer_cases") \
        and t.get("correct_refusals") == t.get("refusal_cases")
    d3 = False
    if cen and cen.get("labelled") and cen.get("gained"):
        d3 = (cen["gained_right"] * 10 >= cen["gained"] * 9
              and (cen["naive_new"] == 0 or
                   cen["naive_refused"] * 10 >= cen["naive_new"] * 9))
    return {"D1": d1,
            # D2 (frozen path) needs the evaluation before and after the
            # round and the digests of wheels.py/union.py before it, none of
            # which is stored: not measured.
            "D2": False,
            "D3": bool(d3),
            "D4": demanded and axioms["consistent"] == axioms["axioms"],
            "D5": _lean_clean(lean)}


#: The census section the report carries when no census is stored.
_NOT_TAKEN: Dict[str, Any] = {
    "taken": False, "gained": None, "gained_right": None, "naive_new": None,
    "naive_refused": None, "in_wheel": None, "labelled": False,
    "reason": "the census of the union is not stored (python3 -m "
              "glm_universal.tools domains --write takes it, tens of minutes)",
}


def domains_report(census: bool = False, jobs: int = 2,
                   take: bool = False) -> Dict[str, Any]:
    """The domain-wheels report: the wheels, the junctions, the battery, the
    axioms, the Lean file and the marks.

    The census section is the stored census (``census_fresh`` says whether
    the code that took it is the code now).  ``census=True`` always carries a
    census section: with nothing stored it says the census is not taken
    (``gained`` is ``None``, ``census_fresh`` False) rather than taking it,
    because taking it is tens of minutes of exact linear algebra.
    ``take=True`` takes it afresh in this process (``jobs`` processes)
    without storing it; :func:`write_census` takes and stores it."""
    bat = battery()
    axioms = axiom_consistency("si7")
    lean = lean_check(LEAN_FILE, LEAN_THEOREMS)
    report: Dict[str, Any] = {
        "wheels": _wheel_dicts(),
        "junctions": DOMAIN_JUNCTIONS,
        "non_identities": DOMAIN_NON_IDENTITIES,
        "battery": bat, "axioms": axioms, "lean": lean,
    }
    cen: Optional[Dict[str, Any]] = None
    if take:
        cen = globals()["census"](jobs=jobs)
        report["census_fresh"] = True
    else:
        stored = _read_census()
        if stored is not None:
            cen = stored.get("census")
            report["census_fresh"] = census_state()["fresh"]
        else:
            report["census_fresh"] = False
    unmeasured = []
    if not bat.get("available"):
        unmeasured.append("D1: " + bat["reason"])
    if cen is None:
        unmeasured.append("D3: the census of the union is not stored "
                          "(python3 -m glm_universal.tools domains --write)")
    elif not cen.get("labelled"):
        unmeasured.append("D3: the labels (DOMAIN_LABELS of "
                          "evaluation/domain_cases.py) are not present")
    unmeasured.append("D2: the frozen-path evaluation and the digests of "
                      "wheels.py/union.py before the round are not stored")
    if cen is not None:
        report["census"] = {k: v for k, v in cen.items() if k != "rows"}
        report["census"].setdefault("taken", True)
        report["post_hoc"] = cen.get("post_hoc", {})
    elif census:
        report["census"] = dict(_NOT_TAKEN)
    marks = _marks(bat, cen if (cen is not None and report["census_fresh"])
                   else None, axioms, lean)
    report["marks"] = marks
    report["met"] = sum(marks.values())
    report["taken"] = len(marks)
    report["unmeasured"] = unmeasured
    return report

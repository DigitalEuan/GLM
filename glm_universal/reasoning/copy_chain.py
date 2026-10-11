"""``glm_universal.reasoning.copy_chain`` -- information inequalities past
Zhang-Yeung, and on five variables (Phase 119,
``studies/DERIVATION_FOUR_STUDY.md``).

Why it exists
-------------
Phase 118 (:mod:`.non_shannon`) took a four-variable claim the Shannon cone
leaves undecided and tried the twelve Zhang-Yeung instances and a pool of
rational laws.  Zhang-Yeung is one of infinitely many non-Shannon
inequalities, and the study's §6 left two lines: claims that need others, and
anything on five or more variables.

1. **Chains of copies.**  The copy lemma -- now proved in Lean for every
   finite distribution (``GLM.CopyLemma.copy_lemma``) -- gives, for any
   variable ``x`` and set ``B``, a new variable ``R`` with the joint law of
   ``(x, B)`` and ``I(R; everything else | B) = 0``.  Applying it twice --
   ``R1`` a copy of ``x`` over ``B``, then ``R2`` a copy of ``x`` over
   ``B + R1`` (Matus's construction) -- and searching for a Shannon-type
   certificate over the six variables proves inequalities that no
   Zhang-Yeung combination reaches.  Each certificate is an exact identity:
   the claim equals a nonnegative combination of elemental inequalities plus
   rational multiples of the copy conditions (each ``= 0``).  Verdict
   ``proved_by_copies``.
2. **Five variables.**  Phase 107's exact search (Shannon certificate or a
   GF(2) counterexample) runs unchanged on five variables; past it, the
   Zhang-Yeung instances on every four of the five (60) join the elemental
   inequalities, and a counterexample is sought among Phase 118's rational
   laws *lifted* to five variables: the fifth variable constant, or equal to
   one of the others, which turns the claim into a four-variable claim the
   pool can be screened against.  Every lifted candidate is decided exactly
   on the five-variable claim.

Integers and ``Fraction`` only (D7).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

from . import info_inequality as II
from . import non_shannon as NS

__all__ = ["FIVE", "Chain", "ChainStep", "chain_conditions", "chain_configs",
           "chain_certificate", "decide_chain", "parse_five", "Five",
           "decide_five", "five_zy_instances", "lift_claim"]

#: The largest number of variables this layer reads.
FIVE = 5


# ===========================================================================
# 1.  CHAINS OF COPIES
# ===========================================================================

@dataclass(frozen=True)
class ChainStep:
    name: str                 # the new variable
    of: str                   # the variable copied
    base: Tuple[str, ...]     # the set it is copied over


def chain_conditions(names: Sequence[str], steps: Sequence[ChainStep]
                     ) -> List[Tuple[str, II.Linear]]:
    """The copy conditions of every step, ``(text, form)`` with ``form = 0``:
    ``H(R, T) = H(x, T)`` for every ``T`` within the base, and
    ``I(R; rest | base) = 0`` with ``rest`` every variable so far outside
    the base."""
    out: List[Tuple[str, II.Linear]] = []
    so_far = list(names)
    for st in steps:
        base = list(st.base)
        for r in range(len(base) + 1):
            for T in combinations(base, r):
                lhs = II._H([st.name] + list(T))
                rhs = II._H([st.of] + list(T))
                out.append((f"H({','.join([st.name] + list(T))}) = "
                            f"H({','.join([st.of] + list(T))})",
                            II._add(lhs, rhs, Fraction(-1))))
        rest = [v for v in so_far if v not in base]
        out.append((f"I({st.name};{','.join(rest)}|{','.join(base)}) = 0",
                    II._I([st.name], rest, base)))
        so_far.append(st.name)
    return out


def chain_configs(names: Sequence[str], depth: int
                  ) -> List[Tuple[ChainStep, ...]]:
    """Single copies (``depth`` 1) or Matus chains (``depth`` 2: the same
    variable copied over the same set, then over the set and the first
    copy), bases of two variables first."""
    out = []
    for size in (2, 1, 3):
        for x in names:
            others = [v for v in names if v != x]
            for B in combinations(others, size):
                s1 = ChainStep("R1", x, tuple(B))
                if depth == 1:
                    out.append((s1,))
                else:
                    out.append((s1, ChainStep("R2", x, tuple(B) + ("R1",))))
    return out


@dataclass
class Chain:
    steps: Tuple[ChainStep, ...]
    names: Tuple[str, ...]                      # the originals, then R1, R2
    conditions: List[Tuple[str, II.Linear]]
    lam: List[Tuple[tuple, Fraction]]           # elementals over ``names``
    mu: List[Tuple[int, Fraction]]              # givens of the problem
    nu: List[Tuple[int, Fraction]]              # copy conditions

    def text(self) -> str:
        parts = []
        for st in self.steps:
            parts.append(f"{st.name} a copy of {st.of} over "
                         f"{{{', '.join(st.base)}}}")
        return "; ".join(parts)


def chain_certificate(problem: II.Problem, claim: II.Linear,
                      steps: Sequence[ChainStep]) -> Optional[Chain]:
    """A Shannon-type certificate of ``claim`` over the originals and the
    copies, using the givens and the copy conditions; or ``None``."""
    conds = chain_conditions(problem.names, steps)
    names = tuple(problem.names) + tuple(st.name for st in steps)
    givens = list(problem.givens) + [f for _, f in conds]
    texts = list(problem.given_texts) + [t for t, _ in conds]
    pr = II.Problem(names, givens, texts, [claim], problem.claim_text,
                    ">=", {}, {})
    cert = II._certificate(pr, claim)
    if cert is None:
        return None
    lam, mu_all = cert
    ng = len(problem.givens)
    mu = [(j, c) for j, c in mu_all if j < ng]
    nu = [(j - ng, c) for j, c in mu_all if j >= ng]
    return Chain(tuple(steps), names, conds, lam, mu, nu)


def decide_chain(problem: II.Problem, depths: Sequence[int] = (1, 2)
                 ) -> Optional[List[Chain]]:
    """One chain certificate per claim (an ``=`` claim has two), or ``None``
    if some claim has none within the configurations tried."""
    if len(problem.names) != 4:
        return None
    out = []
    for claim in problem.claims:
        if claim.get(frozenset(), 0) < 0:
            return None
        found = None
        for depth in depths:
            for steps in chain_configs(problem.names, depth):
                found = chain_certificate(problem, claim, steps)
                if found is not None:
                    break
            if found is not None:
                break
        if found is None:
            return None
        out.append(found)
    return out


# ===========================================================================
# 2.  FIVE VARIABLES
# ===========================================================================

def parse_five(text: str) -> II.Problem:
    return II.parse_problem(text, max_variables=FIVE)


def five_zy_instances(names: Sequence[str]
                      ) -> List[Tuple[Tuple[str, str, str, str], II.Linear]]:
    """The Zhang-Yeung instances on every four of the names."""
    out = []
    for four in combinations(names, 4):
        out += NS.zy_instances(list(four))
    return out


def _zy_certificate(problem: II.Problem, claim: II.Linear):
    names = problem.names
    coords = II._coords(names)
    els = II.elementals(names)
    insts = five_zy_instances(names)
    cols: List[II.Linear] = [II.elemental_form(e, names) for e in els]
    for g in problem.givens:
        cols.append(g)
        cols.append({s: -c for s, c in g.items()})
    cols += [f for _, f in insts]
    if claim.get(frozenset(), 0) < 0:
        return None
    A = [[col.get(s, Fraction(0)) for col in cols] for s in coords]
    b = [claim.get(s, Fraction(0)) for s in coords]
    x = II.simplex_feasible(A, b)
    if x is None:
        return None
    ne, ng = len(els), len(problem.givens)
    lam = [(e, x[k]) for k, e in enumerate(els) if x[k]]
    mu = []
    for j in range(ng):
        v = x[ne + 2 * j] - x[ne + 2 * j + 1]
        if v:
            mu.append((j, v))
    base = ne + 2 * ng
    nu = [(inst, x[base + i]) for i, (inst, _) in enumerate(insts)
          if x[base + i]]
    return lam, mu, nu


def lift_claim(form: II.Linear, names: Sequence[str], z: str,
               w: Optional[str]) -> II.Linear:
    """The claim with ``z`` constant (``w is None``) or equal to ``w``: every
    joint entropy ``h(S)`` with ``z`` in ``S`` becomes ``h(S - z)`` or
    ``h(S - z + w)``."""
    out: II.Linear = {}
    for s, c in form.items():
        if z in s:
            s2 = frozenset(v for v in s if v != z)
            if w is not None:
                s2 = s2 | {w}
        else:
            s2 = s
        out = II._add(out, {s2: c})
    return {s: c for s, c in out.items() if c}


def _lifted_counterexample(problem: II.Problem, k: int):
    names = list(problem.names)
    searched = 0
    for z in reversed(names):
        rest = [v for v in names if v != z]
        for w in [None] + rest:
            claim4 = lift_claim(problem.claims[k], names, z, w)
            givens4 = [lift_claim(g, names, z, w) for g in problem.givens]
            pr4 = II.Problem(tuple(rest), givens4,
                             list(problem.given_texts), [claim4],
                             problem.claim_text, ">=", {}, {})
            law, h4, val, count = NS._entropic_counterexample(pr4, 0)
            searched += count
            if law is None:
                continue
            atoms4, weights = law
            col = names.index(z)
            atoms = []
            for a in atoms4:
                full = dict(zip(rest, a))
                full[z] = 0 if w is None else full[w]
                atoms.append(tuple(full[v] for v in names))
            law5 = (tuple(atoms), tuple(weights))
            h = NS.log_entropies(atoms, weights, names)
            if any(NS.lf_sign(NS.lf_value(g, h)) != 0
                   for g in problem.givens):
                continue
            v5 = NS.lf_value(problem.claims[k], h)
            if NS.lf_sign(v5) < 0:
                return law5, h, v5, searched, (z, w)
    return None, None, None, searched, None


@dataclass
class Five:
    kind: str            # proved | NOT_VALID | proved_non_shannon |
    #                      NOT_VALID_ENTROPIC | NOT_SHANNON
    problem: II.Problem
    shannon: II.Verdict
    certificates: list = field(default_factory=list)
    law: Optional[tuple] = None
    entropies: Optional[Dict[frozenset, NS.LogForm]] = None
    violated: Optional[int] = None
    violation: Optional[NS.LogForm] = None
    lifting: Optional[Tuple[str, Optional[str]]] = None
    searched: int = 0

    def instances(self) -> List[Tuple[str, str, str, str]]:
        seen = []
        for _, _, nu in self.certificates:
            for inst, _ in nu:
                if inst not in seen:
                    seen.append(inst)
        return seen


def decide_five(problem: II.Problem,
                shannon: Optional[II.Verdict] = None) -> Five:
    """The five-variable decision: Phase 107's search, then the Zhang-Yeung
    instances on every four, then the lifted pool."""
    v = shannon or II.decide(problem)
    if v.kind in ("proved", "NOT_VALID"):
        return Five(v.kind, problem, v)
    certs = []
    searched = 0
    for k, claim in enumerate(problem.claims):
        cert = _zy_certificate(problem, claim)
        if cert is not None:
            certs.append(cert)
            continue
        law, h, val, count, lift = _lifted_counterexample(problem, k)
        searched += count
        if law is not None:
            return Five("NOT_VALID_ENTROPIC", problem, v, certs, law, h, k,
                        val, lift, searched)
        return Five("NOT_SHANNON", problem, v, certs, violated=k,
                    searched=searched)
    return Five("proved_non_shannon", problem, v, certs)

"""``glm_universal.reasoning.proof_search`` -- propositional proof search
(Phase 106, ``studies/DERIVATION_STUDY.md``).

Why it exists
-------------
The outside question set of Phase 89 located eighteen questions that ask
for a *proof* or a *derivation* (class P of ``studies/QUESTION_SET_B_STUDY.md``
§8).  The machine could compute values; it could not establish that a
conclusion follows from premises.  This module decides that for
propositional logic and hands back a certificate either way:

* **intuitionistic** -- a proof in Dyckhoff's contraction-free sequent
  calculus G4ip.  G4ip is terminating and complete for intuitionistic
  propositional logic, so when the search fails there is *no* constructive
  proof;
* **classical** -- the sequent is a tautology (decided by the truth table)
  but has no G4ip proof.  The proof given is a G4ip proof from the fewest
  instances ``p | ~p`` of excluded middle, and where a Kripke model of at
  most four worlds refutes the sequent intuitionistically the model is
  given as the certificate that no constructive proof exists;
* **NOT_VALID** -- refused, with a valuation that makes every premise true
  and the goal false.

Every proof is a tree of rule instances that :func:`check_proof` re-checks
rule by rule; the column-3 script carries its own checker, written without
this module.  ``RequestProject/GLM/Derivations.lean`` proves every rule
sound for every valuation, so a checked proof is a tautology.

Syntax: atoms are identifiers; ``false`` (or ``bot``) is falsum and
``true`` its negation; ``~A`` is ``A -> false``; ``A <-> B`` is
``(A -> B) & (B -> A)``.  ``->`` associates to the right and binds weaker
than ``|``, which binds weaker than ``&``.  Integers and booleans only
(D7).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import product
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = ["ProofError", "parse_formula", "parse_sequent", "show",
           "Proof", "prove_intuitionistic", "decide", "Verdict",
           "check_proof", "truth_table", "kripke_countermodel",
           "atoms_of", "proof_lines", "rules_used", "MAX_ATOMS"]

#: The truth table is refused beyond this many atoms.
MAX_ATOMS = 12

BOT = ("bot",)


class ProofError(Exception):
    """A refusal of the prover, with the machine's code."""

    def __init__(self, code: str, why: str):
        super().__init__(f"{code}: {why}")
        self.code = code
        self.why = why


# ===========================================================================
# 1.  FORMULAS
# ===========================================================================

def imp(a, b):
    return ("imp", a, b)


def neg(a):
    return ("imp", a, BOT)


_TOK = re.compile(r"\s*(<->|->|\|-|[~&|(),]|[A-Za-z_][A-Za-z0-9_]*)")


def _tokens(text: str) -> List[str]:
    out, i = [], 0
    text = text.replace("¬", "~").replace("∧", "&").replace("∨", "|")
    text = text.replace("→", "->").replace("↔", "<->").replace("⊢", "|-")
    text = text.replace("⊥", "false").replace("\\to", "->")
    while i < len(text):
        if text[i:].strip() == "":
            break
        m = _TOK.match(text, i)
        if not m:
            raise ProofError("UNREADABLE", f"cannot read {text[i:i + 12]!r}")
        out.append(m.group(1))
        i = m.end()
    return out


class _Reader:
    def __init__(self, toks: List[str]):
        self.toks, self.i = toks, 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def take(self, want=None):
        t = self.peek()
        if t is None or (want is not None and t != want):
            raise ProofError("UNREADABLE", f"expected {want or 'a formula'}, "
                                           f"found {t or 'the end'}")
        self.i += 1
        return t

    def iff(self):
        a = self.imp()
        if self.peek() == "<->":
            self.take()
            b = self.iff()
            return ("and", imp(a, b), imp(b, a))
        return a

    def imp(self):
        a = self.disj()
        if self.peek() == "->":
            self.take()
            return imp(a, self.imp())
        return a

    def disj(self):
        a = self.conj()
        while self.peek() == "|":
            self.take()
            a = ("or", a, self.conj())
        return a

    def conj(self):
        a = self.unary()
        while self.peek() == "&":
            self.take()
            a = ("and", a, self.unary())
        return a

    def unary(self):
        t = self.peek()
        if t == "~":
            self.take()
            return neg(self.unary())
        if t == "(":
            self.take()
            a = self.iff()
            self.take(")")
            return a
        if t is None or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", t):
            raise ProofError("UNREADABLE", f"expected a formula, found "
                                           f"{t or 'the end'}")
        self.take()
        if t in ("false", "bot"):
            return BOT
        if t == "true":
            return neg(BOT)
        return ("atom", t)


def parse_formula(text: str):
    r = _Reader(_tokens(text))
    if r.peek() is None:
        raise ProofError("UNREADABLE", "empty formula")
    f = r.iff()
    if r.peek() is not None:
        raise ProofError("UNREADABLE", f"unexpected {r.peek()!r}")
    return f


def parse_sequent(text: str):
    """``PREMISE, PREMISE |- GOAL`` as ``(premises, goal)``."""
    if text.count("|-") + text.count("⊢") != 1:
        raise ProofError("UNREADABLE", "write PREMISES |- GOAL")
    left, right = re.split(r"\|-|⊢", text)
    prem = []
    if left.strip():
        depth, cur = 0, ""
        for ch in left:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if ch == "," and depth == 0:
                prem.append(cur)
                cur = ""
            else:
                cur += ch
        prem.append(cur)
    if any(not p.strip() for p in prem):
        raise ProofError("UNREADABLE", "an empty premise")
    return [parse_formula(p) for p in prem], parse_formula(right)


def show(f) -> str:
    k = f[0]
    if k == "atom":
        return f[1]
    if k == "bot":
        return "false"
    if k == "imp" and f[2] == BOT:
        inner = show(f[1])
        return "~" + (inner if f[1][0] in ("atom", "bot") or
                      (f[1][0] == "imp" and f[1][2] == BOT) else f"({inner})")
    sym = {"imp": "->", "and": "&", "or": "|"}[k]

    def side(g, right):
        s = show(g)
        if g[0] in ("atom", "bot") or (g[0] == "imp" and g[2] == BOT):
            return s
        if k == "imp" and right and g[0] == "imp":
            return s
        if g[0] == k and k in ("and", "or") and not right:
            return s
        return f"({s})"

    return f"{side(f[1], False)} {sym} {side(f[2], True)}"


def atoms_of(fs: Sequence) -> List[str]:
    out: List[str] = []

    def walk(f):
        if f[0] == "atom":
            if f[1] not in out:
                out.append(f[1])
        elif f[0] != "bot":
            walk(f[1])
            walk(f[2])

    for f in fs:
        walk(f)
    return out


def value(f, v: Dict[str, bool]) -> bool:
    k = f[0]
    if k == "atom":
        return v[f[1]]
    if k == "bot":
        return False
    a, b = value(f[1], v), value(f[2], v)
    return (not a or b) if k == "imp" else (a and b) if k == "and" else \
        (a or b)


def truth_table(premises: Sequence, goal) -> Optional[Dict[str, bool]]:
    """``None`` if every valuation making the premises true makes the goal
    true; otherwise the first falsifying valuation."""
    names = atoms_of(list(premises) + [goal])
    if len(names) > MAX_ATOMS:
        raise ProofError("TOO_LARGE", f"{len(names)} atoms; the truth table "
                                      f"is refused beyond {MAX_ATOMS}")
    for bits in product((True, False), repeat=len(names)):
        v = dict(zip(names, bits))
        if all(value(p, v) for p in premises) and not value(goal, v):
            return v
    return None


# ===========================================================================
# 2.  G4ip
# ===========================================================================

@dataclass(frozen=True)
class Proof:
    """A rule instance: the conclusion sequent ``(context, goal)`` with the
    context a sorted tuple (a multiset), the rule's name, the principal
    formula, and the premises' proofs."""

    rule: str
    context: Tuple
    goal: tuple
    principal: Optional[tuple]
    premises: Tuple["Proof", ...]

    def size(self) -> int:
        return 1 + sum(p.size() for p in self.premises)


def _ctx(fs) -> Tuple:
    return tuple(sorted(fs, key=repr))


def _remove(ctx: Tuple, f) -> List:
    out = list(ctx)
    out.remove(f)
    return out


def prove_intuitionistic(premises: Sequence, goal,
                         budget: int = 200000) -> Optional[Proof]:
    """A G4ip proof of ``premises |- goal`` or ``None`` (none exists)."""
    memo: Dict[Tuple, Optional[Proof]] = {}
    steps = [0]

    def search(ctx: Tuple, g) -> Optional[Proof]:
        key = (ctx, g)
        if key in memo:
            return memo[key]
        steps[0] += 1
        if steps[0] > budget:
            raise ProofError("TOO_LARGE", "the proof search exceeded its "
                                          "budget")
        memo[key] = None                     # a loop would be a failure
        got = _search(ctx, g)
        memo[key] = got
        return got

    def node(rule, ctx, g, principal, *prems):
        return Proof(rule, ctx, g, principal, tuple(prems))

    def _search(ctx: Tuple, g) -> Optional[Proof]:
        # --- axioms -------------------------------------------------------
        if BOT in ctx:
            return node("L-false", ctx, g, BOT)
        if g[0] == "atom" and g in ctx:
            return node("axiom", ctx, g, g)
        # --- invertible rules ---------------------------------------------
        if g[0] == "imp":
            p = search(_ctx(list(ctx) + [g[1]]), g[2])
            return node("R->", ctx, g, g, p) if p else None
        if g[0] == "and":
            p1 = search(ctx, g[1])
            if not p1:
                return None
            p2 = search(ctx, g[2])
            return node("R&", ctx, g, g, p1, p2) if p2 else None
        for f in ctx:
            if f[0] == "and":
                rest = _remove(ctx, f)
                p = search(_ctx(rest + [f[1], f[2]]), g)
                return node("L&", ctx, g, f, p) if p else None
        for f in ctx:
            if f[0] == "or":
                rest = _remove(ctx, f)
                p1 = search(_ctx(rest + [f[1]]), g)
                if not p1:
                    return None
                p2 = search(_ctx(rest + [f[2]]), g)
                return node("L|", ctx, g, f, p1, p2) if p2 else None
        for f in ctx:
            if f[0] == "imp":
                a, b = f[1], f[2]
                rest = _remove(ctx, f)
                if a == BOT:
                    p = search(_ctx(rest), g)
                    return node("L-false->", ctx, g, f, p) if p else None
                if a[0] == "atom" and a in rest:
                    p = search(_ctx(rest + [b]), g)
                    return node("L0->", ctx, g, f, p) if p else None
                if a[0] == "and":
                    p = search(_ctx(rest + [imp(a[1], imp(a[2], b))]), g)
                    return node("L&->", ctx, g, f, p) if p else None
                if a[0] == "or":
                    p = search(_ctx(rest + [imp(a[1], b), imp(a[2], b)]), g)
                    return node("L|->", ctx, g, f, p) if p else None
        # --- choices ------------------------------------------------------
        if g[0] == "or":
            p = search(ctx, g[1])
            if p:
                return node("R|1", ctx, g, g, p)
            p = search(ctx, g[2])
            if p:
                return node("R|2", ctx, g, g, p)
        for f in ctx:
            if f[0] == "imp" and f[1][0] == "imp":
                c, d, b = f[1][1], f[1][2], f[2]
                rest = _remove(ctx, f)
                p1 = search(_ctx(rest + [imp(d, b)]), imp(c, d))
                if not p1:
                    continue
                p2 = search(_ctx(rest + [b]), g)
                if p2:
                    return node("L->->", ctx, g, f, p1, p2)
        return None

    return search(_ctx(premises), goal)


def _premise_sequents(p: Proof) -> Optional[List[Tuple[Tuple, tuple]]]:
    """The premises a rule instance must have, or ``None`` if the instance
    is not a rule of G4ip."""
    ctx, g, f = p.context, p.goal, p.principal
    if p.rule == "L-false":
        return [] if BOT in ctx else None
    if p.rule == "axiom":
        return [] if g[0] == "atom" and g in ctx else None
    if p.rule in ("R->", "R&", "R|1", "R|2"):
        if f != g:
            return None
        if p.rule == "R->" and g[0] == "imp":
            return [(_ctx(list(ctx) + [g[1]]), g[2])]
        if p.rule == "R&" and g[0] == "and":
            return [(ctx, g[1]), (ctx, g[2])]
        if p.rule == "R|1" and g[0] == "or":
            return [(ctx, g[1])]
        if p.rule == "R|2" and g[0] == "or":
            return [(ctx, g[2])]
        return None
    if f not in ctx:
        return None
    rest = _remove(ctx, f)
    if p.rule == "L&" and f[0] == "and":
        return [(_ctx(rest + [f[1], f[2]]), g)]
    if p.rule == "L|" and f[0] == "or":
        return [(_ctx(rest + [f[1]]), g), (_ctx(rest + [f[2]]), g)]
    if f[0] != "imp":
        return None
    a, b = f[1], f[2]
    if p.rule == "L-false->" and a == BOT:
        return [(_ctx(rest), g)]
    if p.rule == "L0->" and a[0] == "atom" and a in rest:
        return [(_ctx(rest + [b]), g)]
    if p.rule == "L&->" and a[0] == "and":
        return [(_ctx(rest + [imp(a[1], imp(a[2], b))]), g)]
    if p.rule == "L|->" and a[0] == "or":
        return [(_ctx(rest + [imp(a[1], b), imp(a[2], b)]), g)]
    if p.rule == "L->->" and a[0] == "imp":
        return [(_ctx(rest + [imp(a[2], b)]), imp(a[1], a[2])),
                (_ctx(rest + [b]), g)]
    return None


def check_proof(p: Proof) -> bool:
    """Every node a rule instance of G4ip whose premises are its children."""
    want = _premise_sequents(p)
    if want is None or len(want) != len(p.premises):
        return False
    for (c, g), q in zip(want, p.premises):
        if q.context != c or q.goal != g or not check_proof(q):
            return False
    return True


def rules_used(p: Proof) -> List[str]:
    out: List[str] = []

    def walk(q):
        if q.rule not in out:
            out.append(q.rule)
        for r in q.premises:
            walk(r)

    walk(p)
    return out


def proof_lines(p: Proof, depth: int = 0) -> List[str]:
    ctx = ", ".join(show(f) for f in p.context)
    head = f"{'  ' * depth}{ctx + ' ' if ctx else ''}|- {show(p.goal)}" \
           f"   [{p.rule}]"
    out = [head]
    for q in p.premises:
        out.extend(proof_lines(q, depth + 1))
    return out


# ===========================================================================
# 3.  KRIPKE COUNTERMODELS
# ===========================================================================

def _forces(w: int, f, up: Dict[int, List[int]], val: Dict[int, set]) -> bool:
    k = f[0]
    if k == "atom":
        return f[1] in val[w]
    if k == "bot":
        return False
    if k == "and":
        return _forces(w, f[1], up, val) and _forces(w, f[2], up, val)
    if k == "or":
        return _forces(w, f[1], up, val) or _forces(w, f[2], up, val)
    return all(not _forces(u, f[1], up, val) or _forces(u, f[2], up, val)
               for u in up[w])


def _frames(n: int):
    """Rooted partial orders on ``0..n-1`` with 0 the root, as up-sets
    (world 0 below every world); orders ``i < j`` only for ``i < j``."""
    pairs = [(i, j) for i in range(1, n) for j in range(i + 1, n)]
    for bits in product((False, True), repeat=len(pairs)):
        rel = {(i, i) for i in range(n)} | {(0, j) for j in range(n)}
        rel |= {pr for pr, b in zip(pairs, bits) if b}
        if any((i, j) in rel and (j, k) in rel and (i, k) not in rel
               for i in range(n) for j in range(n) for k in range(n)):
            continue
        yield {i: [j for j in range(n) if (i, j) in rel] for i in range(n)}


def kripke_countermodel(premises: Sequence, goal, max_worlds: int = 4
                        ) -> Optional[Tuple[Dict[int, List[int]],
                                            Dict[int, List[str]]]]:
    """A rooted Kripke model of at most ``max_worlds`` worlds whose root
    forces every premise and not the goal, or ``None``."""
    names = atoms_of(list(premises) + [goal])
    if len(names) > 3:
        return None
    for n in range(1, max_worlds + 1):
        for up in _frames(n):
            worlds = list(range(n))
            # monotone valuations: an atom's worlds form an up-set
            upsets = []
            for bits in product((False, True), repeat=n):
                s = {w for w, b in zip(worlds, bits) if b}
                if all(u in s for w in s for u in up[w]):
                    upsets.append(s)
            for choice in product(upsets, repeat=len(names)):
                val = {w: {a for a, s in zip(names, choice) if w in s}
                       for w in worlds}
                if all(_forces(0, p, up, val) for p in premises) and \
                        not _forces(0, goal, up, val):
                    return up, {w: sorted(val[w]) for w in worlds}
    return None


# ===========================================================================
# 4.  THE DECISION
# ===========================================================================

@dataclass
class Verdict:
    kind: str                         # intuitionistic | classical | NOT_VALID
    premises: List[tuple]
    goal: tuple
    proof: Optional[Proof] = None
    excluded_middle: Tuple[str, ...] = ()
    valuation: Optional[Dict[str, bool]] = None
    kripke: Optional[Tuple[Dict[int, List[int]], Dict[int, List[str]]]] = None


def decide(premises: Sequence, goal) -> Verdict:
    """The verdict on ``premises |- goal`` with its certificate."""
    premises = list(premises)
    bad = truth_table(premises, goal)
    if bad is not None:
        return Verdict("NOT_VALID", premises, goal, valuation=bad)
    p = prove_intuitionistic(premises, goal)
    if p is not None:
        return Verdict("intuitionistic", premises, goal, proof=p)
    names = atoms_of(premises + [goal])
    for k in range(1, len(names) + 1):
        for chosen in _subsets(names, k):
            extra = [("or", ("atom", a), neg(("atom", a))) for a in chosen]
            q = prove_intuitionistic(extra + premises, goal)
            if q is not None:
                return Verdict("classical", premises, goal, proof=q,
                               excluded_middle=tuple(chosen),
                               kripke=kripke_countermodel(premises, goal))
    raise ProofError("TOO_LARGE", "no proof from excluded middle was found "
                                  "within the budget")      # pragma: no cover


def _subsets(names: List[str], k: int):
    if k == 0:
        yield []
        return
    for i, a in enumerate(names):
        for rest in _subsets(names[i + 1:], k - 1):
            yield [a] + rest

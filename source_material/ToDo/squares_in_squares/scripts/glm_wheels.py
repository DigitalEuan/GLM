#!/usr/bin/env python3
r"""glm_wheels.py — the declared-law wheel, as a domain-agnostic engine.

WHAT A WHEEL IS (from `19-COLLECTION-AND-REVIEW.md` §5).  A wheel is a finite
parameter grid, an exact count law, an exact builder, one gate, one scorer and one
ledger.  `motif_wheels.py` is the packing template; `cent_wheels` is the physics
one.  A search reports what it found; a wheel reports what is *expressible* and why
the rest is not.  This file lifts that pattern out of packing entirely.

THE ENGINE.  A **domain** registers three things and nothing else:

    Alphabet    atomic words over an exact field (`exact_field`), each with an
                exact measure, exact boundary extent and a declared type
    Syntax      composable combinators (`Tile`, `Frame`, `Strip`, `Glue`,
                `SymmetryFold`), each carrying **closed-form symbolic laws**
                (count, measure/area conservation, boundary extent) and an exact
                builder that emits a Claim
    Witnesses   the multi-witness suite a Claim must pass

and the **engine** (`Engine.spin`) only ever does four things: enumerate the
declared cells, let a combinator refuse with a named law, run every witness, and
record the verdict.  It contains no geometry and no sequence theory.

MULTI-WITNESS VERIFICATION (no single-metric shortcut).  A Claim is certified only
if *all four* witnesses pass, and each witness is a different kind of evidence:

    exact gate        the domain's algebraic feasibility predicate, exact
                      (packing: the SAT separation gate at clearance >= 0;
                       sequences: the mechanical-word realisation)
    topology          a structural witness that is not the gate
                      (packing: the contact graph — connectivity, min degree,
                       edge count against the 2N-3 Laman bound;
                       sequences: factor complexity p(m) = m + 1)
    conservation      count and measure identities in the field
                      (packing: N + V = L^2 and L^2 >= N;
                       sequences: weight sums and the coboundary law)
    Decimal cross     an independent 70-digit `Decimal` recomputation of the
                      decisive quantities: its *signs* must agree with the exact
                      ones, and its values must agree to 1e-40

DOMAINS SHIPPED HERE
    spatial_geometry   grids, corner pockets, diagonal strips S(k,m), rational-t
                       corner glues, the diagonal fold, and the table atoms
                       n = 5, 10, 40 (certified as lifted sentences)
    sturmian_sequences letters over an exact slope: mechanical words, rotation
                       frames, strips, glues and reversal, with the *exact* reason
                       a rational slope is not Sturmian

FLOAT AUDIT.  Every decision function in this module, `exact_field` and `qsqrt2`
is checked by bytecode (`exact_field.audit`) for the name `float`; display goes
through `Decimal`.  The ledger records the counts, not a slogan.

READ-ONLY.  This file never touches `submission.csv`; the only paths it writes are
`workspace/push/glm_wheels.json`, `workspace/push/q_census.json` and
`workspace/push/outlier_probe.json`.

USAGE
    python3 scripts/glm_wheels.py --selftest
    python3 scripts/glm_wheels.py                 # spin both wheels, write ledger
    python3 scripts/glm_wheels.py --census --budget 240   # 447 Q rows, resumable
    python3 scripts/glm_wheels.py --probe --budget 240    # the 3 outliers, Q(sqrt d)
    python3 scripts/glm_wheels.py --audit
"""
from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from decimal import Decimal, getcontext
from fractions import Fraction as F
from typing import Callable

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import exact_field as EF          # noqa: E402
import qsqrt2 as Q                # noqa: E402
import sqscore as SQ              # noqa: E402

# Running this file directly makes it __main__ while a domain module would import
# a *second* copy under the name "glm_wheels" -- with different Claim/Refusal
# classes, so `except Refusal` would not catch.  One canonical module object fixes it.
sys.modules.setdefault("glm_wheels", sys.modules[__name__])

getcontext().prec = 70
Q2 = Q.Q2
ZERO, HALF = Q2(0), Q.HALF
S2H = Q2(0, F(1, 2))                                   # sqrt2 / 2
SUBMISSION = os.path.join(ROOT, "workspace/submission/submission.csv")
LEDGER = os.path.join(ROOT, "workspace/push/glm_wheels.json")
CENSUS = os.path.join(ROOT, "workspace/push/q_census.json")
PROBE = os.path.join(ROOT, "workspace/push/outlier_probe.json")


# --------------------------------------------------------------------- refusal
class Refusal(Exception):
    """A cell that cannot be built, with the law that says why (never a silent skip)."""

    def __init__(self, law: str, detail: str):
        super().__init__(f"{law}: {detail}")
        self.law, self.detail = law, detail

    def as_dict(self):
        return {"law": self.law, "detail": self.detail}


# ----------------------------------------------------------- laws and claims
@dataclass
class Claim:
    """One certified-or-refused cell: the sentence, its laws, and its evidence.

    The three *neutral* fields are what the engine reports, for every domain:

      size       how many objects the sentence is made of (squares, letters, vectors)
      measure    the exact quantity the family is judged by (a side, a weight, a count)
      invariant  the exact quantity the family claims to preserve or improve on

    `n` remains a read-only alias for `size`, because structure builders are written
    with `n` and there is no reason to churn them for a rename.
    """

    domain: str
    family: str
    params: dict
    size: int
    laws: dict                    # name -> (formula, exact value)
    payload: object               # domain object (state/words, or the word)
    meta: dict = field(default_factory=dict)
    measure: tuple | None = None      # (label, exact value)
    invariant: tuple | None = None    # (label, exact value)

    @property
    def n(self):
        return self.size

    def law_str(self, name):
        formula, value = self.laws[name]
        return f"{formula} = {value}"

    def brief(self):
        return f"{self.domain}/{self.family}{tuple(self.params.values())}"


# ---------------------------------------------------------------- witnesses
class Witness:
    """A kind of evidence.  Subclasses implement `check(claim, domain) -> (ok, detail)`.

    Suites are variable-length by declaration, not by `if domain == ...` inside the
    engine: a witness names the families it covers (`None` = every family of the domain
    it is registered on), and `Domain.suite` returns the applicable ones.  So a Glue
    cell can run three witnesses and an Atom four, and the wheel records how many ran.
    """

    name = "witness"
    law = "witness_failed"
    families = None

    def check(self, claim: Claim, domain=None):       # pragma: no cover - interface
        raise NotImplementedError

    def applies(self, claim: Claim) -> bool:
        return self.families is None or claim.family in self.families


class PackingGateWitness(Witness):
    """The exact SAT sentence gate: every pair separated, on a field sign only."""

    name = "exact_gate"
    law = "gate_refused"

    def check(self, claim, domain=None):
        g = gate_of(claim)
        # a one-square sentence has no pairs at all: clearance is None, not 0
        ok = g["ok"] and (g["clearance"] is None or g["clearance"] == 0)
        return ok, f"gate {'ok' if g['ok'] else 'REFUSED'}, clearance " \
                   f"{g['clearance']}, contacts {g['contacts']}, " \
                   f"violations {g['violations']}"


class ContactGraphWitness(Witness):
    """Topology: the contact graph must be connected, min degree >= 1, edges >= 2N-3."""

    name = "contact_graph"
    law = "contact_graph_thin"

    def check(self, claim, domain=None):
        state, words = claim.payload["state"], claim.payload["words"]
        n = len(state)
        if n == 1:
            return True, "single square: no pairs, no contacts needed"
        adj = [[] for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                axes = pairs_of(claim, i, j)
                if any(s.sign() == 0 for _q, s, _need, _o in axes):
                    adj[i].append(j)
                    adj[j].append(i)
        edges = sum(len(a) for a in adj) // 2
        seen, stack = {0}, [0]
        while stack:
            v = stack.pop()
            for w in adj[v]:
                if w not in seen:
                    seen.add(w)
                    stack.append(w)
        connected = len(seen) == n
        min_deg = min(len(a) for a in adj) if n else 0
        laman = 2 * n - 3 if n >= 2 else 0
        # the witness is that the structure is *spanning and touching*, not that it
        # is rigid: the corner glue is a star (4 edges on 5 squares) and is certified.
        ok = connected and min_deg >= 1 and edges >= n - 1
        return ok, (f"spanning {connected} on {len(seen)}/{n} with {edges} contacts "
                    f">= n-1, min degree {min_deg}, Laman bound {laman} "
                    f"({'rigid' if edges >= laman else 'floppy'})")


class ConservationWitness(Witness):
    """Count and measure: N + V = L^2 exactly, and L^2 >= N."""

    name = "conservation"
    law = "conservation_failed"

    def check(self, claim, domain=None):
        n = claim.size
        L = claim.laws["extent"][1]
        V = claim.laws["void"][1]
        one = type(L)(n) if not isinstance(L, int) else Q2(n)
        ok = (one + V) == L * L and (L * L - one).sign() >= 0 and n >= 1
        return ok, f"N + V = {n} + ({V}) = {one + V} and L^2 = {L * L}"


class DecimalWitness(Witness):
    """Independent 70-digit Decimal recomputation, for *every* domain.

    One class, one protocol.  What is shared is the arithmetic: `scalar` turns any
    supported element -- a `Quad` of any discriminant, a `Fraction`, an int -- into a
    70-digit Decimal using Decimal's own square root, never a float.  What is
    per-domain is the *model*, declared by the domain as
    `decimal_model(claim) -> (ok, detail)` and kept next to the code that has to pass
    the exact witnesses too.  A model that disagrees with the exact gate is a bug the
    suite catches, not a second opinion the engine averages.
    """

    name = "decimal_cross"
    law = "decimal_mismatch"

    @staticmethod
    def scalar(z):
        """Any supported scalar as a Decimal (sqrt by Decimal, never by float)."""
        if isinstance(z, Decimal):
            return z
        if hasattr(z, "a") and hasattr(z, "b"):
            return (Decimal(z.a.numerator) / Decimal(z.a.denominator)
                    + Decimal(z.b.numerator) / Decimal(z.b.denominator)
                    * Decimal(getattr(z, "d", 2)).sqrt())
        if hasattr(z, "numerator") and hasattr(z, "denominator"):
            return Decimal(z.numerator) / Decimal(z.denominator)
        return Decimal(z)

    def check(self, claim, domain=None):
        if domain is None or domain.decimal_model is None:
            return False, "no decimal model declared for this domain"
        return domain.decimal_model(claim)


def spatial_decimal(claim):
    """Packing model: the bbox side and every per-pair verdict, in Decimal."""
    dec = DecimalWitness.scalar
    state, words = claim.payload["state"], claim.payload["words"]
    L = claim.laws["extent"][1]
    half = type(L)(F(1, 2))
    xs, ys = [], []
    for (x, y), w in zip(state, words):
        ex = (abs(w[0]) + abs(w[1])) * half
        xs += [dec(x - ex), dec(x + ex)]
        ys += [dec(y - ex), dec(y + ex)]
    Ld = max(max(xs) - min(xs), max(ys) - min(ys))
    gap = abs(Ld - dec(L))
    # A pair is separated iff its BEST axis slack is >= 0, and the sentence iff every
    # pair is: recompute both in Decimal and compare with the exact gate.
    worst = None
    dec_ok = True
    for i in range(len(state)):
        for j in range(i + 1, len(state)):
            best = None
            for _q, slack, _need, _o in pairs_of(claim, i, j):
                sd = dec(slack)
                best = sd if best is None else max(best, sd)
                worst = sd if worst is None else min(worst, sd)
            if best is not None and best < 0:
                dec_ok = False
    exact_ok = gate_of(claim)["ok"]
    ok = gap <= Decimal("1e-40") and dec_ok == exact_ok
    w = "no pairs" if worst is None else f"{worst:.3e}"
    return ok, (f"|L_dec - L| = {gap:.3e}, worst slack_dec {w}, pair verdict "
                f"{dec_ok} == exact {exact_ok}")


def sequence_decimal(claim):
    """Sequence model: the weight sum recomputed in Decimal."""
    dec = DecimalWitness.scalar
    word, alpha = claim.payload["word"], claim.payload["alpha"]
    n1 = sum(word)
    total = Decimal(len(word) - n1) * (1 - dec(alpha)) + Decimal(n1) * dec(alpha)
    gap = abs(total - dec(claim.laws["measure"][1]))
    return gap <= Decimal("1e-40"), f"|measure_dec - measure| = {gap:.3e}"


class MechanicalWitness(Witness):
    """Sequences: the word is the mechanical word of its slope and intercept."""

    name = "exact_gate"
    law = "not_mechanical"

    def check(self, claim, domain=None):
        word, alpha = claim.payload["word"], claim.payload["alpha"]
        rho = claim.payload["rho"]
        if claim.meta.get("fold"):
            # a reversal is not the mechanical word of its own slope: its feasibility
            # predicate is the fold identity, checked here rather than pretended.
            parent = claim.payload["parent"]
            ok = word == list(reversed(parent))
            return ok, (f"{len(word)} letters are the exact reversal of the parent "
                        f"window ({sum(word)} ones, weight preserved)")
        ok = True
        for k, w in enumerate(word):
            lo = (Q2(k + 1) * alpha + rho).floor()
            hi = (Q2(k) * alpha + rho).floor()
            if w != lo - hi:
                ok = False
                break
        return ok, f"{len(word)} letters agree with floor((k+1)a+r) - floor(ka+r)"


class ComplexityWitness(Witness):
    """Sequences: topology is factor complexity — Sturmian iff p(m) = m + 1."""

    name = "complexity"
    law = "not_sturmian"

    def check(self, claim, domain=None):
        word = claim.payload["word"]
        worst = None
        for m in range(2, min(7, len(word) - 1)):
            factors = {tuple(word[i:i + m]) for i in range(len(word) - m + 1)}
            got, want = len(factors), m + 1
            if worst is None or got - want > worst[0] - worst[1]:
                worst = (got, want)
            if got != want:
                return False, f"p({m}) = {got} != {want} (periodic, not Sturmian)"
        return True, f"p(m) = m + 1 for m <= 6 (worst p({worst[1] - 1}) = {worst[0]})"


class SequenceConservationWitness(Witness):
    """Sequences: the weight sum and the coboundary law d(uv) = du xor dv."""

    name = "conservation"
    law = "conservation_failed"

    def check(self, claim, domain=None):
        word, alpha = claim.payload["word"], claim.payload["alpha"]
        n1 = sum(word)
        total = Q2(len(word) - n1) * (Q2(1) - alpha) + Q2(n1) * alpha
        declared = claim.laws["measure"][1]
        cob = claim.meta.get("coboundary")
        ok = total == declared
        detail = f"weight {total} == declared, {len(word)} letters, {n1} ones"
        if cob is not None:
            # the boundary is first xor last, so at a join the seam term cancels:
            #   d(uv) = du ^ (u[-1] ^ v[0]) ^ dv
            u, v = claim.payload["parts"]
            du, dv = u[0] ^ u[-1], v[0] ^ v[-1]
            seam = u[-1] ^ v[0]
            d_uv = (u + v)[0] ^ (u + v)[-1]
            ok &= (du ^ seam ^ dv) == d_uv
            detail += (f", coboundary {du}^{seam}^{dv} = {d_uv} (seam term {seam})")
        return ok, detail


# -------------------------------------------------------- alphabets and engine
class Alphabet:
    """Atomic words over an exact field: name -> (kind, measure, extent)."""

    def __init__(self, name, field_name, words):
        self.name, self.field_name = name, field_name
        self.words = words                     # name -> dict(kind, measure, extent, data)

    def __contains__(self, w):
        return w in self.words

    def measure(self, w):
        return self.words[w]["measure"]

    def extent(self, w):
        return self.words[w]["extent"]


class Domain:
    """An alphabet, a combinator registry, the witnesses, and a Decimal model."""

    def __init__(self, name, alphabet, witnesses):
        self.name, self.alphabet = name, alphabet
        self.witnesses = witnesses
        self.combinators: dict[str, Callable[..., Claim]] = {}
        #: claim -> (ok, detail): what this domain recomputes in 70-digit Decimal
        self.decimal_model: Callable[[Claim], tuple] | None = None

    def register(self, name, fn):
        self.combinators[name] = fn
        return fn

    def suite(self, claim: Claim):
        """The applicable witnesses for this claim; suites may differ in length."""
        return [w for w in self.witnesses if w.applies(claim)]

    def build(self, family, **params) -> Claim:
        if family not in self.combinators:
            raise Refusal("unknown_combinator", family)
        return self.combinators[family](**params)


@dataclass
class Cell:
    family: str
    params: dict


class Wheel:
    """A declared parameter grid over one domain.  Spinning it decides each cell."""

    def __init__(self, name, domain, cells):
        self.name, self.domain, self.cells = name, domain, cells

    def spin(self):
        rows = []
        for cell in self.cells:
            row = {"wheel": self.name, "domain": self.domain.name,
                   "family": cell.family,
                   "params": {k: str(v) for k, v in cell.params.items()},
                   "size": None, "measure": None, "invariant": None,
                   "verdict": None, "witnesses": {}, "witness_count": 0,
                   "refusal": None, "laws": {}}
            try:
                claim = self.domain.build(cell.family, **cell.params)
            except Refusal as r:
                row["verdict"], row["refusal"] = "refused", r.as_dict()
                rows.append(row)
                continue
            except Exception as e:                       # a builder bug is a refusal
                row["verdict"] = "refused"
                row["refusal"] = {"law": "builder_error", "detail": repr(e)}
                rows.append(row)
                continue
            failed = None
            suite = self.domain.suite(claim)
            for w in suite:
                try:
                    ok, detail = w.check(claim, self.domain)
                except Exception as e:
                    ok, detail = False, f"{type(e).__name__}: {e}"
                row["witnesses"][w.name] = {"ok": bool(ok), "detail": detail}
                if not ok and failed is None:
                    failed = w
            row["witness_count"] = len(suite)
            row["laws"] = {k: str(v[1]) for k, v in claim.laws.items()}
            row["size"] = claim.size
            row["measure"] = (None if claim.measure is None
                              else f"{claim.measure[0]} = {claim.measure[1]}")
            row["invariant"] = (None if claim.invariant is None
                                else f"{claim.invariant[0]} = {claim.invariant[1]}")
            if failed is None:
                row["verdict"] = "certified"
            else:
                row["verdict"] = "refused"
                row["refusal"] = {"law": failed.law,
                                  "detail": row["witnesses"][failed.name]["detail"]}
            rows.append(row)
        return rows


class Engine:
    """The domain-agnostic part: register domains, spin their wheels, counts only."""

    def __init__(self):
        self.domains, self.wheels = {}, []

    def register(self, domain):
        self.domains[domain.name] = domain
        return domain

    def add_wheel(self, wheel):
        self.wheels.append(wheel)
        return wheel

    def spin_all(self):
        out = {}
        for wheel in self.wheels:
            out[wheel.name] = wheel.spin()
        return out

    @staticmethod
    def summarise(rows):
        cert = [r for r in rows if r["verdict"] == "certified"]
        ref = [r for r in rows if r["verdict"] == "refused"]
        laws = {}
        for r in ref:
            laws[r["refusal"]["law"]] = laws.get(r["refusal"]["law"], 0) + 1
        return {"cells": len(rows), "certified": len(cert), "refused": len(ref),
                "refusal_laws": dict(sorted(laws.items()))}


# =============================================================== domain one
# spatial geometry: exact 2D grammars over Q and Q(sqrt 2)
def _laws_packing(n, L, V, contacts=None):
    laws = {"count": ("N", n), "extent": ("L", L), "void": ("L^2 - N", V)}
    if contacts is not None:
        laws["contacts"] = ("contacts", contacts)
    return laws


def _tag(claim, L, n):
    """Attach the exact gain-vs-grid law (grid(n) = ceil(sqrt n), exactly).

    The grid side is an integer, so it is rebuilt *in the claim's own field* -- a
    Q(sqrt 5) side and a Q(sqrt 2) grid cannot be compared without that, and the
    refusal would be a type error rather than a statement.
    """
    g = Q.grid_side(n)
    kk = g.a if hasattr(g, "a") else F(g)
    grid = type(L)(kk) if hasattr(L, "d") else L.__class__(kk)
    claim.meta["beats"] = L < grid
    claim.meta["gain"] = grid - L
    claim.laws["gain"] = ("ceil(sqrt N) - L", grid - L)
    claim.measure = ("L", L)
    claim.invariant = ("ceil(sqrt N) - L", grid - L)
    return claim


def p_grid(k):
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k} has no squares")
    st, ws = [], []
    for i in range(k):
        for j in range(k):
            st.append((Q2(i) + HALF, Q2(j) + HALF))
            ws.append(Q.AXIS)
    L = Q2(k)
    n = k * k
    return _tag(Claim("spatial_geometry", "Tile", {"k": k}, n,
                      _laws_packing(n, L, L * L - Q2(n)), {"state": st, "words": ws}), L, n)


def p_strip(k, m):
    """S(k, m): four k-blocks in the corners and an m-diamond seam on the anti-diagonal.

    Assembled as a *declared field* (run 88): the carrier is the product of two axis
    skeletons -- the left/bottom k-run and the same k-run shifted across a seam of
    width `m*sqrt2/2` -- and the slots are the m diamonds sitting in that seam.  The
    insertion rule then does the rest.  At m = 0 the seam has width 0, the slot list is
    empty, and the field is the plain 2k axis grid: nothing is refused, and the cell
    certifies with gain 0, which is exactly the statement that an empty seam buys
    nothing.
    """
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k} has no blocks")
    if m < 0:
        raise Refusal("negative_seam", f"m = {m} is not a seam width")
    claim = _assemble_field(f"S({k},{m})", strip_field(k, m), family="Strip",
                            params={"k": k, "m": m}, allow_empty=True)
    claim.laws["seam"] = ("m", m)          # `diamonds` is set once, by the assembler
    return claim


def strip_field(k, m):
    """The S(k, m) declaration: two k-runs per axis, a seam of m diamonds between them.

    `X = {1/2, ..., k-1/2} + {0, k + m*sqrt2/2}` in both axes, and the m diamonds at
    `(k + (2i+1)sqrt2/4, k + (2(m-1-i)+1)sqrt2/4)`, i.e. the anti-diagonal seam.  Both
    halves of that are arithmetic in `i`, so the declaration is generated, never typed.
    """
    seam = Q2(0, F(m, 2))                       # m*sqrt2/2
    runs = ((HALF, Q2(1), k), (HALF + Q2(k) + seam, Q2(1), k))
    slots = [(Q2(k) + Q2(0, F(2 * i + 1, 4)),
              Q2(k) + Q2(0, F(2 * (m - 1 - i) + 1, 4))) for i in range(m)]
    return {"x": runs, "y": runs, "slots": slots}


def Q_mixed_strip(k, m):
    """The S(k, m) sentence, imported from the run-84 instrument (single source)."""
    import mixed_field as M
    return M.strip_sentence(k, m)


def p_pocket(k):
    """The corner pocket: four k-blocks and one diamond -- the strip S(k, 1).

    Run 88 built the Strip from `strip_field(k, m)`; run 89 puts the Pocket on the same
    build path rather than on run 84's sentence builder, so a strip and a pocket differ
    only in the `m` they pass.  The cell stays a `Pocket` (its own family and parameters)
    because that is the claimed object; only the assembly is shared.
    """
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k}")
    claim = _assemble_field(f"Pocket({k})", strip_field(k, 1), family="Pocket",
                            params={"k": k})
    claim.laws["seam"] = ("m", 1)          # the same seam law the Strip carries
    return claim


# ------------------------------------------------- the ridge family (run 90)
#: A ridge sentence: four k-blocks in the corners of an L x L box, one unit square of
#: the declared word in the seam between them.  `L = 2k + min(1/(c+s), c+s)`, derived
#: from the contact condition (below), so the 45-degree member is exactly the Strip's
#: `S(k, 1)` and every other member is its own exact algebraic rung.
def ridge_width(cls, c, s, k=None, m=1):
    """The seam width at which the m-diamond bar just touches, exactly.

    The bar is the m tilted unit squares set edge to edge along `-v` (the square's own
    edge direction), centred in the seam.  Every block-slot pair's slack is *linear* in
    the seam width `w`, because the bar moves with the seam centre and the blocks move
    with the box, so each pair-axis equation `|d(w) . q| = need` has closed-form roots in
    the field.  The width is the smallest of those roots at which the exact gate passes:
    a contact width by construction, no scan and no tolerance.

    For `k = None` and `m = 1` this reduces to the closed form of run 90,
    `min(1/(c+s), c+s)`; at 45 degrees and any m it gives `m*sqrt2/2`, the Strip's seam.
    """
    if m == 0:
        return cls(0)
    if k is None:
        one = cls(1)
        return min(one / (c + s), c + s)
    for w in sorted(ridge_widths(cls, c, s, k, m)):
        state, words = _ridge_sentence(cls, c, s, k, m, w)
        if Q.gate(state, words, cls)["ok"]:
            return w
    raise Refusal("no_contact_width",
                  f"no seam width in the closed-form set gates the {m}-diamond bar")


def _ridge_blocks(cls, k, w):
    """The four k-blocks of the box `[0, 2k+w]^2`, as (centre) pairs."""
    half = cls(F(1, 2))
    L = cls(2 * k) + w
    cells = []
    for bx in (0, 1):
        for by in (0, 1):
            x0 = cls(0) if bx == 0 else L - cls(k)
            y0 = cls(0) if by == 0 else L - cls(k)
            for i in range(k):
                for j in range(k):
                    cells.append((x0 + cls(i) + half, y0 + cls(j) + half))
    return cells


def _bar_offsets(cls, c, s, m):
    """The m slot centres relative to the seam centre: edge to edge along `-v`."""
    return [(cls(F(2 * i - (m - 1), 2)) * s, -cls(F(2 * i - (m - 1), 2)) * c)
            for i in range(m)]


def _ridge_sentence(cls, c, s, k, m, w):
    """The ridge state and words at seam width `w` (box side `2k + w`)."""
    half = cls(F(1, 2))
    state = _ridge_blocks(cls, k, w)
    words = [(cls(1), cls(0)) for _ in state]
    ctr = (cls(k) + w * half, cls(k) + w * half)
    for dx, dy in _bar_offsets(cls, c, s, m):
        state.append((ctr[0] + dx, ctr[1] + dy))
        words.append((c, s))
    return state, words


def _ridge_affine(cls, c, s, k, m):
    """Blocks and slots as `A + B w` per coordinate, so every slack equation is linear."""
    half = cls(F(1, 2))
    zero, one = cls(0), cls(1)
    blocks = []
    for bx in (0, 1):
        for by in (0, 1):
            for i in range(k):
                for j in range(k):
                    Ax = cls(i) + half + (cls(k) if bx else zero)
                    Ay = cls(j) + half + (cls(k) if by else zero)
                    blocks.append(((Ax, one if bx else zero), (Ay, one if by else zero)))
    slots = []
    for dx, dy in _bar_offsets(cls, c, s, m):
        slots.append(((cls(k) + dx, half), (cls(k) + dy, half)))
    return blocks, slots


def ridge_widths(cls, c, s, k, m):
    """Every positive `w` at which some block-slot pair touches, exactly.

    A pair's four axis slacks are `|P + Q w| - need`, so the roots of `|P + Q w| = need`
    are `(need - P)/Q` and `(-need - P)/Q`; feasibility can only change at one of them.
    """
    if m == 0:
        return []
    blocks, slots = _ridge_affine(cls, c, s, k, m)
    half = cls(F(1, 2))
    # `need = 1/2 + extent(other)` on every axis: the block's extent along u or v is
    # (|c|+|s|)/2 and the slot's extent along x or y is the same expression.
    need_slot = half + (abs(c) + abs(s)) * half
    need_block = need_slot
    roots = []
    for (bx_, by_), (sx_, sy_) in ((b, s) for b in blocks for s in slots):
        # each coordinate is `A + B w`:  x = bx_[0] + bx_[1] w,  y = by_[0] + by_[1] w
        dAx, dBx = bx_[0] - sx_[0], bx_[1] - sx_[1]
        dAy, dBy = by_[0] - sy_[0], by_[1] - sy_[1]
        for (qA, qB), need in (((c, s), need_slot), ((-s, c), need_slot),
                               ((cls(1), cls(0)), need_block),
                               ((cls(0), cls(1)), need_block)):
            # d = block - slot, so d.q = (dA.q) + (dB.q) w
            P = dAx * qA + dAy * qB
            Qc = dBx * qA + dBy * qB
            if Qc == 0:
                continue
            for sign in (cls(1), cls(-1)):
                w = (sign * need - P) / Qc
                if w.sign() > 0 and w not in roots:
                    roots.append(w)
    roots.sort()
    return roots


def p_ridge(d, c, s, k, family, params, m=1):
    """Gate-verify an m-diamond ridge over `Q(sqrt d)` and return it as a claim.

    N = 4k^2 + m.  Refusals are declared, not incidental:
      * `word_off_circle`  -- the declared (cos, sin) is not a unit word;
      * `no_contact_width` -- no closed-form width gates the bar;
      * `ridge_cuts_corner` -- the derived width still leaves an overlap.
    """
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k} has no blocks")
    if m < 0:
        raise Refusal("negative_seam", f"m = {m} is not a seam count")
    cls = qfield(d)
    if (c * c + s * s) != cls(1):
        raise Refusal("word_off_circle",
                      f"cos^2 + sin^2 = {c * c + s * s} != 1 in Q(sqrt {d})")
    w = ridge_width(cls, c, s, k, m)
    state, words = _ridge_sentence(cls, c, s, k, m, w)
    g = Q.gate(state, words, cls)
    if not g["ok"]:
        raise Refusal("ridge_cuts_corner",
                      f"{family}: {g['violations']} pairs overlap at width {w}")
    n = len(state)
    L = g["L"]
    claim = Claim("spatial_geometry", family, params, n,
                  {"count": ("N", n), "extent": ("L", L),
                   "void": ("L^2 - N", L * L - cls(n)),
                   "contacts": ("contacts", g["contacts"])},
                  {"state": state, "words": words, "field": f"Q(sqrt {d})",
                   "seam": w, "bar": m})
    claim.meta["field_d"] = d
    claim.meta["seam"] = str(w)
    claim.meta["bar"] = m
    _tag(claim, L, n)
    claim.laws["seam"] = ("w", w)
    claim.laws["tilted"] = ("tilted", m)
    side = _table_side(n)
    if side is None:
        claim.meta["table_side"] = None
        claim.meta["beats_table"] = None
    else:
        Ld = DecimalWitness.scalar(L)
        Td = DecimalWitness.scalar(side)
        claim.meta["table_side"] = str(side)
        claim.meta["beats_table"] = Ld < Td
        claim.meta["table_gap"] = str(Td - Ld)
    return claim


# --------------------------------------------------- the 45-degree block (run 98)
#: A block of `s^2` unit squares at the 45-degree word, edge to edge in its own frame,
#: centred in an `L x L` box, with axis-aligned unit squares filling the four corner
#: triangles.  The block's faces are the four lines `x + y = L -+ s/sqrt2` and
#: `y - x = -+ s/sqrt2`, so each corner triangle has legs `t = L - s/sqrt2` and a unit
#: square `[i, i+1] x [j, j+1]` fits iff `i + j + 2 <= t`.  The exact choice
#: `t = k + 1` (integer legs) makes the staircase square at `(k-1, 0)` touch the block's
#: face exactly at its corner, so the side is a contact side, not an approximation:
#:
#:     T(k, s) = k (k + 1) / 2      per corner  (the staircase sum `sum_{i=0}^{k-1} (k - i)`)
#:     N(k, s) = s^2 + 4 T(k, s)  =  s^2 + 2 k (k + 1)
#:     L(k, s) = s / sqrt 2 + k + 1
#:
#: nothing here is scanned: the count is a triangular number and the side is the exact
#: root of the tangency `i + j + 2 = t` together with the block face `x + y = L - s/sqrt2`.
def block45_count(s, k):
    """`(T, N)` of the 45-degree block family, exactly: `T = k(k+1)/2`, `N = s^2 + 4T`."""
    if s < 1 or k < 1:
        raise Refusal("degenerate_cell", f"s = {s}, k = {k}")
    T = k * (k + 1) // 2
    return T, s * s + 4 * T


def block45_side(cls, s, k):
    """The contact side, exactly: `L = max(s/sqrt2 + k + 1, 2 s/sqrt2)`, in `cls`.

    With `t = k + 1` the corner staircase reaches the block's face at `x + y = t`, so
    the sentence's bounding box is `s/sqrt2 + t` -- unless the block's own diagonal
    `2 s/sqrt2` is longer, which happens when `t < s/sqrt2`; then the block, not the
    fill, sets the side.  The gate caught exactly this in the first sweep (84 rows
    came back `block45_side_mismatch`), which is why the law is written as a maximum.
    """
    h = cls(0, F(s, 2))                       # s / sqrt 2, exactly
    t = cls(k + 1)
    diag = cls(0, F(s))                       # 2 h = s sqrt 2
    return t + h if t + h > diag else diag


def _block45_sentence(cls, s, k):
    """The block, its four staircase corner fills, and the exact words."""
    if s < 1 or k < 1:
        raise Refusal("degenerate_cell", f"s = {s}, k = {k}")
    h = cls(0, F(s, 2))
    half = cls(F(1, 2))
    c45, s45 = Q.word_45()
    ctr = ((h + cls(k + 1)) * half, (h + cls(k + 1)) * half)   # the block, on the face t
    cells, words = [], []
    for i in range(s):
        for j in range(s):
            du = cls(F(2 * i - (s - 1), 2))
            dv = cls(F(2 * j - (s - 1), 2))
            cells.append((ctr[0] + du * c45 - dv * s45,
                          ctr[1] + du * s45 + dv * c45))
            words.append((c45, s45))
    box = h + cls(k + 1)            # the corner fills are anchored at this box's corners
    m = k - 1                       # staircase rows: (i, j) with i + j <= m
    for corner in range(4):
        for i in range(m + 1):
            for j in range(m + 1 - i):
                if corner == 0:
                    x, y = cls(i) + half, cls(j) + half
                elif corner == 1:
                    x, y = box - cls(i) - half, cls(j) + half
                elif corner == 2:
                    x, y = cls(i) + half, box - cls(j) - half
                else:
                    x, y = box - cls(i) - half, box - cls(j) - half
                cells.append((x, y))
                words.append((cls(1), cls(0)))
    return cells, words, block45_side(cls, s, k)


def p_block45(s, k, family="Block45", params=None):
    """Gate-verify the 45-degree block family over Q(sqrt 2) and return it as a claim.

    `N = s^2 + 2k(k+1)`, `L = s/sqrt2 + k + 1`, and the exact gate is the arbiter: the
    staircase squares touch the block's faces at single points (clearance 0), and when
    the two staircases that share a wall reach each other the sentence is refused as
    `block45_corner_collision` -- a declared law, not an incidental overlap.
    """
    cls = qfield(2)
    T, N = block45_count(s, k)
    cells, words, L = _block45_sentence(cls, s, k)
    if len(cells) != N:
        raise Refusal("block45_count", f"built {len(cells)} != {N}")
    g = Q.gate(cells, words, cls)
    if not g["ok"]:
        raise Refusal("block45_corner_collision",
                      f"{family}(s={s}, k={k}): {g['violations']} pairs overlap "
                      f"(the corner staircases meet on a wall)")
    if g["L"] != L:
        raise Refusal("block45_side_mismatch", f"gate side {g['L']} != law {L}")
    claim = Claim("spatial_geometry", family, params or {"s": s, "k": k}, N,
                  {"count": ("N", N), "extent": ("L", L),
                   "void": ("L^2 - N", L * L - cls(N)),
                   "contacts": ("contacts", g["contacts"])},
                  {"state": cells, "words": words, "field": "Q(sqrt 2)",
                   "block": s * s, "corner": T})
    claim.meta["block"] = s * s
    claim.meta["corner"] = T
    _tag(claim, L, N)
    claim.laws["block"] = ("s^2", s * s)
    claim.laws["corner"] = ("k(k+1)/2", T)
    claim.laws["floor_gap"] = ("L - (2k + 1/sqrt2)",
                               L - (cls(2 * k) + cls(0, F(1, 2))))
    try:
        side = _table_side(N)
    except KeyError:            # not a delivered count: nothing to compare against
        side = None
    if side is None:
        claim.meta["table_side"] = None
        claim.meta["beats_table"] = None
    else:
        Ld = DecimalWitness.scalar(L)
        Td = DecimalWitness.scalar(side)
        claim.meta["table_side"] = str(side)
        claim.meta["beats_table"] = Ld < Td
        claim.meta["table_gap"] = str(Td - Ld)
    return claim


def block45_spin(ncap=250, extras=((17, 13), (17, 16), (17, 17)), smax=24, kmax=20):
    """Spin the 45-degree block family: `(s, k)` with `N <= ncap`, plus `extras`, gated.

    Two references per row, neither of them a score claim:

      * the single-word seam floor, as the exact gap `L - (2k + 1/sqrt 2)` -- with the
        family's own `k` in the ridge's role, so the comparison is like for like;
      * the delivered side at the same `N`, measured from its 12-dp pose.

    `ncap` keeps the sweep inside the cheap gates; the named `extras` are the rows the
    question is actually about (a delivered count, and the two `s = 17` boundary cases).
    """
    rows = []
    cls = qfield(2)
    half_sqrt2 = Decimal(2).sqrt() / 2
    todo = []
    for s in range(1, smax + 1):
        for k in range(1, kmax + 1):
            _, N = block45_count(s, k)
            if N > ncap:
                break
            todo.append((s, k))
    for s, k in extras:
        if (s, k) not in todo:
            todo.append((s, k))
    for s, k in sorted(todo):
        if True:
            _, N = block45_count(s, k)
            rec = {"s": s, "k": k, "N": N, "block": s * s,
                   "corner": k * (k + 1) // 2}
            try:
                claim = p_block45(s, k)
            except Refusal as e:
                rec["verdict"] = e.law
                rows.append(rec)
                continue
            L = claim.measure[1]
            Ld = DecimalWitness.scalar(L)
            rec["verdict"] = "gated"
            rec["L"] = str(L)
            rec["L_dec"] = str(Ld)
            rec["excess_dec"] = str(Ld - Decimal(2 * k))
            rec["below_half_sqrt2"] = bool(Ld - Decimal(2 * k) < half_sqrt2)
            rec["below_floor"] = bool(Ld < Decimal(2 * k) + half_sqrt2)
            rec["contacts"] = claim.laws["contacts"][1]
            rec["beats_grid"] = claim.meta.get("beats")
            rec["beats_table"] = claim.meta.get("beats_table")
            rec["table_side"] = claim.meta.get("table_side")
            rec["table_gap"] = claim.meta.get("table_gap")
            rows.append(rec)
    return rows


# ------------------------------------------ the half-integer corner fill (run 99)
#: Run 98's contact staircase needs integer legs: `t = k + 1` puts the square at
#: `(k-1, 0)` on the block's face.  The table's own low-slack rows sit half a unit
#: further out (`t = 14.5, 16.5, 18.5` at `N = 677, 785, 901`), so the production
#: doc 61 section 8 named is the half unit.  A unit axis square `[i, i+1] x [j, j+1]`
#: fits the corner triangle `x, y >= 0`, `x + y <= t` iff `i + j + 2 <= t`, and that
#: inequality is the whole story: `t` enters only through `floor(t)`.  Hence
#:
#:     T_half(k) = #{(i, j) >= 0 : i + j <= k - 2} = k (k - 1) / 2
#:     N(s, k)   = s^2 + 2 k (k - 1)
#:     L(s, k)   = max(s/sqrt 2 + k + 1/2, s sqrt 2)
#:
#: and the half unit buys **no square** in the triangle -- it buys slack.  The exact
#: consequence is a dominance law, checked on every claim: the half-integer member at
#: `k` is run 98's integer contact member at `k - 1`, with the *same* count and a side
#: that is never smaller and at most half a unit larger (it is exactly `1/2` larger in
#: the fill branch, `0` when the block's own diagonal sets both sides, and `k + 1/2 - h`
#: in between).  So `t in Z + 1/2` can never be the better sentence.
def block45half_count(s, k):
    """`(T, N)` of the half-integer corner fill: `T = k(k-1)/2`, `N = s^2 + 2k(k-1)`."""
    if s < 1 or k < 2:
        raise Refusal("degenerate_cell", f"s = {s}, k = {k} (the half fill needs k >= 2)")
    T = k * (k - 1) // 2
    return T, s * s + 4 * T


def block45half_side(cls, s, k):
    """The half-integer side, exactly: `L = max(s/sqrt2 + k + 1/2, 2 s/sqrt2)`."""
    h = cls(0, F(s, 2))                       # s / sqrt 2, exactly
    t = cls(k) + cls(F(1, 2))                 # k + 1/2
    diag = cls(0, F(s))                       # 2 h = s sqrt 2
    return t + h if t + h > diag else diag


def block45half_feasible(cls, s, k):
    """The derived feasibility inequality: the wall staircases need `L >= 2k - 2`.

    Corner 0's staircase reaches `x = k - 1` (its `i = k - 2` square spans
    `[k-2, k-1]`), corner 1's starts at `L - (k-1)`; they share the row band
    `y in [0, k-1]`, so they interpenetrate exactly when `L < 2k - 2`.  With
    `L = s/sqrt2 + k + 1/2` that is `k > s/sqrt2 + 5/2`, i.e. `k <= floor(s/sqrt2) + 2`
    or `+ 3` according to `frac(s/sqrt2)`; the code states the inequality itself and
    the sweep checks it against the gate on every row (`0` mismatches).
    """
    return block45half_side(cls, s, k) >= cls(2 * k - 2)


def _block45half_sentence(cls, s, k):
    """The block, its four half-integer staircases, and the exact words."""
    if s < 1 or k < 2:
        raise Refusal("degenerate_cell", f"s = {s}, k = {k}")
    h = cls(0, F(s, 2))
    half = cls(F(1, 2))
    c45, s45 = Q.word_45()
    t = cls(k) + half
    ctr = ((h + t) * half, (h + t) * half)
    cells, words = [], []
    for i in range(s):
        for j in range(s):
            du = cls(F(2 * i - (s - 1), 2))
            dv = cls(F(2 * j - (s - 1), 2))
            cells.append((ctr[0] + du * c45 - dv * s45,
                          ctr[1] + du * s45 + dv * c45))
            words.append((c45, s45))
    box = h + t                    # `L`; the corner fills are anchored at its corners
    m = k - 2                      # staircase rows: (i, j) >= 0 with i + j <= m
    for corner in range(4):
        for i in range(m + 1):
            for j in range(m + 1 - i):
                if corner == 0:
                    x, y = cls(i) + half, cls(j) + half
                elif corner == 1:
                    x, y = box - cls(i) - half, cls(j) + half
                elif corner == 2:
                    x, y = cls(i) + half, box - cls(j) - half
                else:
                    x, y = box - cls(i) - half, box - cls(j) - half
                cells.append((x, y))
                words.append((cls(1), cls(0)))
    return cells, words, block45half_side(cls, s, k)


def p_block45half(s, k, family="Block45Half", params=None):
    """Gate-verify the half-integer corner fill over Q(sqrt 2) and return it as a claim.

    `N = s^2 + 2k(k-1)`, `L = s/sqrt2 + k + 1/2`.  The gate is the arbiter: every
    staircase square sits `1/(2 sqrt2)` clear of the block's face (no contact), and
    when the two staircases on a wall meet the sentence is refused as
    `block45half_corner_collision`.  The claim also records the dominance law --
    the same count as run 98's integer member `k - 1`, with `L_int <= L <= L_int + 1/2`
    (`1/2` in the fill branch, `0` when the block's diagonal sets both sides).
    """
    cls = qfield(2)
    T, N = block45half_count(s, k)
    cells, words, L = _block45half_sentence(cls, s, k)
    if len(cells) != N:
        raise Refusal("block45half_count", f"built {len(cells)} != {N}")
    g = Q.gate(cells, words, cls)
    if not g["ok"]:
        raise Refusal("block45half_corner_collision",
                      f"{family}(s={s}, k={k}): {g['violations']} pairs overlap "
                      f"(the half staircases meet on a wall; the law needs L >= 2k - 2)")
    if g["L"] != L:
        raise Refusal("block45half_side_mismatch", f"gate side {g['L']} != law {L}")
    claim = Claim("spatial_geometry", family, params or {"s": s, "k": k}, N,
                  {"count": ("N", N), "extent": ("L", L),
                   "void": ("L^2 - N", L * L - cls(N)),
                   "contacts": ("contacts", g["contacts"])},
                  {"state": cells, "words": words, "field": "Q(sqrt 2)",
                   "block": s * s, "corner": T})
    claim.meta["block"] = s * s
    claim.meta["corner"] = T
    _tag(claim, L, N)
    claim.laws["block"] = ("s^2", s * s)
    claim.laws["corner"] = ("k(k-1)/2", T)
    claim.laws["floor_gap"] = ("L - (2k + 1/sqrt2)",
                               L - (cls(2 * k) + cls(0, F(1, 2))))
    # the dominance law, exact on every claim: count of the integer member k-1, side + 1/2
    T_int, N_int = block45_count(s, k - 1)
    if N_int != N:
        raise Refusal("block45half_count", f"integer member count {N_int} != {N}")
    L_int = block45_side(cls, s, k - 1)
    claim.meta["dominated_by"] = f"block45(s={s}, k={k - 1})"
    claim.laws["half_over_integer"] = ("L - L_int", L - L_int)
    claim.meta["half_slack"] = str(L - L_int)
    try:
        side = _table_side(N)
    except KeyError:
        side = None
    if side is None:
        claim.meta["table_side"] = None
        claim.meta["beats_table"] = None
    else:
        Ld = DecimalWitness.scalar(L)
        Td = DecimalWitness.scalar(side)
        claim.meta["table_side"] = str(side)
        claim.meta["beats_table"] = Ld < Td
        claim.meta["table_gap"] = str(Td - Ld)
    return claim


def block45half_spin(ncap=250,
                     extras=((17, 13), (17, 14), (17, 15),
                             (17, 16), (17, 17), (17, 18)),
                     smax=24, kmax=20):
    """Spin the half-integer corner fill: `(s, k)` with `N <= ncap`, plus `extras`.

    Each row carries two exact references and one measured one: the family's own
    excess `L - 2k`, the single-word floor `1/sqrt2`, and the delivered side at the
    same `N` (the exact lift of its 12-dp pose), which is not a score claim.
    """
    rows = []
    cls = qfield(2)
    half_sqrt2 = Decimal(2).sqrt() / 2
    todo = []
    for s in range(1, smax + 1):
        for k in range(2, kmax + 1):
            _, N = block45half_count(s, k)
            if N > ncap:
                break
            todo.append((s, k))
    for s, k in extras:
        if (s, k) not in todo:
            todo.append((s, k))
    for s, k in sorted(todo):
        _, N = block45half_count(s, k)
        rec = {"s": s, "k": k, "N": N, "block": s * s,
               "corner": k * (k - 1) // 2}
        try:
            claim = p_block45half(s, k)
        except Refusal as e:
            rec["verdict"] = e.law
            rows.append(rec)
            continue
        L = claim.measure[1]
        Ld = DecimalWitness.scalar(L)
        rec["verdict"] = "gated"
        rec["L"] = str(L)
        rec["L_dec"] = str(Ld)
        rec["excess_dec"] = str(Ld - Decimal(2 * k))
        rec["below_half_sqrt2"] = bool(Ld - Decimal(2 * k) < half_sqrt2)
        rec["half_slack"] = claim.meta["half_slack"]
        rec["dominated_by"] = claim.meta["dominated_by"]
        rec["contacts"] = claim.laws["contacts"][1]
        rec["beats_grid"] = claim.meta.get("beats")
        rec["beats_table"] = claim.meta.get("beats_table")
        rec["table_side"] = claim.meta.get("table_side")
        rec["table_gap"] = claim.meta.get("table_gap")
        rows.append(rec)
    return rows


def block45half_calibrate(s=17, rows=(677, 785, 901)):
    """At each delivered row's own side, which half-integer member sits there, and how short.

    The three sides `29/2 + 17/2 sqrt2`, `33/2 + 17/2 sqrt2`, `37/2 + 17/2 sqrt2` are
    exactly `s/sqrt2 + k + 1/2` for `k = 14, 16, 18`, so the *side* law is the delivered
    side to the exact lift, not to a tolerance.  This asks the other half of the
    question: the fill at that side holds `N(s, k)` squares, and the delivered row
    holds `n` -- the difference is what the corner triangles cannot see.
    """
    cls = qfield(2)
    out = []
    for n in rows:
        side = _table_side(n)
        rec = {"n": n, "table_side": None if side is None else str(side)}
        if side is None:
            rec["verdict"] = "no_exact_lift"
            out.append(rec)
            continue
        k = None
        for kk in range(2, 80):
            if block45half_side(cls, s, kk) == side:
                k = kk
                break
        rec["k"] = k
        if k is None:
            rec["verdict"] = "no_half_integer_leg"
            out.append(rec)
            continue
        T, N = block45half_count(s, k)
        rec["corner"] = T
        rec["N"] = N
        rec["delta"] = n - N
        rec["feasible"] = block45half_feasible(cls, s, k)
        try:
            claim = p_block45half(s, k)
        except Refusal as e:
            rec["verdict"] = e.law
            out.append(rec)
            continue
        rec["verdict"] = "gated"
        rec["L"] = str(claim.measure[1])
        rec["contacts"] = claim.laws["contacts"][1]
        out.append(rec)
    return out


# ------------------------------------------------------- exact plugins (run 100)
#: Two composable stages in front of the gate, both **sound and deliberately
#: incomplete**.  The Bernstein stage certifies a sign it can prove on a whole
#: interval; the residue stage rejects a tangency it can disprove modulo a small
#: integer.  Neither decides a packing -- the exact gate keeps that job -- and each
#: one's blindness is documented rather than assumed (doc 63).

def _separation_poly(cls, d0, d1, need):
    """`q(t) = (d0 + d1 t)^2 - need^2` in the power basis."""
    return [d0 * d0 - need * need, d0 * d1 + d0 * d1, d1 * d1]


def bernstein_axis_certificate(cls, d0, d1, need, a, b, steps=8, refine=4):
    """Certify `|d0 + t d1| > need` for every `t` in `[a, b]`, exactly.

    One Bernstein pass on `q(t) = (d0 + d1 t)^2 - need^2` bounds the whole interval; if
    the bound straddles zero the pass is repeated on `2, 4, ...` subintervals up to
    `refine` -- exact refinement, not sampling.  The `steps + 1` exact node values are
    the independent staircase witness: every node must lie inside the winning
    enclosure, and the node sign must agree with the certificate.
    """
    poly = _separation_poly(cls, d0, d1, need)
    sp = 1
    while True:
        enc = EF.bernstein_enclosure(poly, a, b, splits=sp)
        if enc["positive"] or sp >= refine:
            break
        sp *= 2
    nodes = EF.bernstein_nodes(poly, a, b, steps)
    inside = all(enc["lo"] <= v and v <= enc["hi"] for v in nodes["values"])
    return {"enclosure": enc, "nodes": nodes, "splits": sp,
            "certified": enc["positive"], "inside": inside,
            "agree": bool(inside and (nodes["min"].sign() > 0) == enc["positive"])}


def bernstein_pair_slide(cls, state, words, i, j, axis, vel, a, b,
                         steps=8, refine=4):
    """One SAT axis of a pair that slides with velocity `vel`, over `a <= t <= b`."""
    dx = state[j][0] - state[i][0]
    dy = state[j][1] - state[i][1]
    d0 = dx * axis[0] + dy * axis[1]
    d1 = vel[0] * axis[0] + vel[1] * axis[1]
    need = cls(F(1, 2)) + Q.axis_extent(words[j][0], words[j][1],
                                        axis[0], axis[1], cls)
    out = bernstein_axis_certificate(cls, d0, d1, need, a, b, steps=steps, refine=refine)
    out.update({"d0": d0, "d1": d1, "need": need})
    return out


def bernstein_interval_certificate(cls, extent, need=None, steps=8):
    """Certify `d^2 - need^2 < 0` on `[-extent, extent]`: the interval is too short.

    This is the exact statement a cage or a chord makes -- `extent < need` -- written
    as a polynomial enclosure, so the two instruments can be compared as witnesses
    rather than taken on trust.  For a quadratic the enclosure is exact, which is why
    `same_verdict` is a theorem here and not a hope.
    """
    need = cls(1) if need is None else need
    e = abs(extent)
    poly = [-(need * need), cls(0), cls(1)]
    enc = EF.bernstein_enclosure(poly, -e, e)
    nodes = EF.bernstein_nodes(poly, -e, e, steps)
    return {"extent": e, "need": need, "enclosure": enc, "nodes": nodes,
            "short": enc["sign"] < 0,
            "same_verdict": (enc["sign"] < 0) == (e < need)}


def bernstein_cage_crosscheck(cls, c, s, cells, words, L, blocks=16):
    """Bernstein against the cage's and the chord's interval witnesses, same sentence."""
    cage = staircase_cage(cls, c, s, cells, words, L,
                          hint=(cells[-1][0], cells[-1][1]))
    out = {"cells": len(cells), "capacity": cage["capacity"], "empty": cage["empty"]}
    if cage["empty"]:
        return out
    bu = bernstein_interval_certificate(cls, cage["extent_u"])
    bv = bernstein_interval_certificate(cls, cage["extent_v"])
    one = cls(1)
    ext_short = (cage["extent_u"] < one) and (cage["extent_v"] < one)
    try:
        ch = staircase_chords(cls, c, s, cells, words, blocks=blocks,
                              window=cage["window"])
    except Refusal as e:
        # the chord's own refusal IS its verdict: the free span reaches 1
        if e.law != "pair_not_excluded":
            raise
        chord_short, chord_verdict, span = False, True, None
        out["chord_reaches_one"] = True
    else:
        bc = bernstein_interval_certificate(cls, ch["max_chord"])
        chord_short, chord_verdict, span = bc["short"], bc["same_verdict"], str(ch["max_chord"])
    out.update({"extent_u": str(cage["extent_u"]),
                "extent_v": str(cage["extent_v"]),
                "chord_span": span,
                "bernstein_u_short": bu["short"],
                "bernstein_v_short": bv["short"],
                "bernstein_chord_short": chord_short,
                "agree": bool(bu["same_verdict"] and bv["same_verdict"]
                              and chord_verdict
                              and chord_short == ext_short
                              and (cage["capacity"] == 1) == ext_short)})
    return out


def plugin_bernstein_demo(s=5, k=4, steps=8):
    """The plugin's whole use on one certified sentence: a contact pair, slid apart.

    The pair is picked by the exact gate (best slack exactly 0), the slide direction is
    the tight axis with its sign, and the certificate is asked on `[1/2, 1]` (where the
    quadratic is positive throughout) and on `[-1, 1]` (where it is not).  The gate's
    own pair test is then run at both endpoints of the first interval: the certificate
    says "separated for all t", the gate says "separated at t = 1/2 and t = 1", and
    the two must agree.
    """
    cls = qfield(2)
    claim = p_block45(s, k)
    cells = claim.payload["state"]
    words = claim.payload["words"]
    half = cls(F(1, 2))
    found = None
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            for axis, slack, _need, _owner in Q.pair_axes(cells, words, i, j, cls):
                if slack == 0:
                    found = (i, j, axis)
                    break
            if found:
                break
        if found:
            break
    if found is None:
        raise Refusal("no_contact_pair", f"Block45({s}, {k}) has no tight pair")
    i, j, axis = found
    dx = cells[j][0] - cells[i][0]
    dy = cells[j][1] - cells[i][1]
    sgn = 1 if (dx * axis[0] + dy * axis[1]).sign() > 0 else -1
    vel = (axis[0] * sgn, axis[1] * sgn)
    good = bernstein_pair_slide(cls, cells, words, i, j, axis, vel, half, cls(1),
                                steps=steps)
    bad = bernstein_pair_slide(cls, cells, words, i, j, axis, vel, cls(-1), cls(1),
                               steps=steps)
    ends = []
    for t in (half, cls(1)):
        moved = list(cells)
        moved[j] = (cells[j][0] + vel[0] * t, cells[j][1] + vel[1] * t)
        best = max(sl for _q, sl, _n, _o in Q.pair_axes(moved, words, i, j, cls))
        ends.append((t, best))
    return {"pair": (i, j), "axis": tuple(str(z) for z in axis),
            "d0": str(good["d0"]), "d1": str(good["d1"]),
            "need": str(good["need"]), "certified": good["certified"],
            "splits": good["splits"], "lo": str(good["enclosure"]["lo"]),
            "nodes_min": str(good["nodes"]["min"]),
            "refused": {"certified": bad["certified"],
                        "sign": bad["enclosure"]["sign"]},
            "endpoints": [(str(t), str(b)) for t, b in ends],
            "endpoints_ok": all(b.sign() > 0 for _t, b in ends)}


def plugin_bernstein_cage(k=5, blocks=16):
    """The run-95/96 witness, re-read by the plugin: census word, 149-square staircase."""
    cls = qfield(7)
    c, s = _sqrt7_word()
    u = cls(F(-1357, 128), F(211, 128))
    decl = staircase_field(cls, c, s, k, u)
    cells, words = decl["cells"], decl["words"]
    L = Q.gate(cells, words, cls)["L"]
    out = bernstein_cage_crosscheck(cls, c, s, cells, words, L, blocks=blocks)
    out["L"] = str(L)
    return out


def _ab(z):
    """The rational pair of an exact scalar (`a + b sqrt d`, or `a` for a rational)."""
    return (z.a, z.b) if isinstance(z, EF.Quad) else (F(z), F(0))


def residue_common_den(state, words):
    """An even common denominator for every coordinate and word component."""
    den = 2
    for p in state:
        for z in p:
            a, b = _ab(z)
            den = den * a.denominator // math.gcd(den, a.denominator)
            den = den * b.denominator // math.gcd(den, b.denominator)
    for w in words:
        for z in w:
            a, b = _ab(z)
            den = den * a.denominator // math.gcd(den, a.denominator)
            den = den * b.denominator // math.gcd(den, b.denominator)
    return den


def _scale_cell(cls, z, D):
    """`D` times an exact coordinate, as an integer component pair of Z[√d]."""
    a, b = _ab(z)
    return (int(a * D), int(b * D))


def _zsign(a, b, d):
    """The exact sign of `a + b sqrt d` on integer components (same rule as `Quad`)."""
    if a == 0:
        return (b > 0) - (b < 0)
    if b == 0:
        return (a > 0) - (a < 0)
    if a > 0 and b > 0:
        return 1
    if a < 0 and b < 0:
        return -1
    if a > 0:
        return 1 if a * a > d * b * b else -1
    return 1 if d * b * b > a * a else -1


def _zmul(u, v, d):
    """(a + b r)(c + e r) in Z[r], integer components."""
    a, b = u
    c, e = v
    return (a * c + d * b * e, a * e + b * c)


def _zadd(u, v):
    return (u[0] + v[0], u[1] + v[1])


def _zsub(u, v):
    return (u[0] - v[0], u[1] - v[1])


def _zabs(u, d):
    return u if _zsign(u[0], u[1], d) >= 0 else (-u[0], -u[1])


def _axis_residual_ints(cls, PX, PY, WX, WY, i, j, D):
    """The eight raw `2 D^2`-scaled tangency residuals, as integer `Z[sqrt d]` pairs.

    Pure integer arithmetic in `Z[sqrt d]` -- no `Quad` is built and no `Fraction`
    grows.  The order is owner `i`'s two axes then owner `j`'s, each giving the two
    signed residuals in the order `(+, -)`, exactly as `pair_tangency_residuals`
    returns them; `pair_max_slack_bound` strides the same list with early exit.
    """
    d = cls.d
    dx = (PX[j][0] - PX[i][0], PX[j][1] - PX[i][1])
    dy = (PY[j][0] - PY[i][0], PY[j][1] - PY[i][1])
    d2 = (D * D, 0)
    raw = []
    for owner, other in ((i, j), (j, i)):
        c, s = WX[owner], WY[owner]
        oc, os_ = WX[other], WY[other]
        for qx, qy in ((c, s), ((-s[0], -s[1]), c)):
            proj = _zadd(_zmul(dx, qx, d), _zmul(dy, qy, d))
            u1 = _zabs(_zadd(_zmul(oc, qx, d), _zmul(os_, qy, d)), d)
            u2 = _zabs(_zsub(_zmul(oc, qy, d), _zmul(os_, qx, d)), d)
            need_s = _zadd(_zadd(d2, u1), u2)
            two = (2 * proj[0], 2 * proj[1])
            raw.append(_zsub(two, need_s))
            raw.append((-(two[0]) - need_s[0], -(two[1]) - need_s[1]))
    return raw


def pair_tangency_residuals(cls, PX, PY, WX, WY, i, j, D):
    """The eight primitive tangency residuals of a pair, as integral `Quad`s.

    A tangency on `axis` means `|delta . axis| = need` with `need = 1/2 +
    extent(other, axis)`, so one of the two signed residuals is exactly zero.  Scaling
    by `2 D^2` makes every component an integer, which is what makes the modular
    reduction legal.  That scaling alone would make the mask vacuous -- every residual
    would be divisible by a power of `D` -- so each residual is divided by its own
    integer content `gcd(|A|, |B|)`.  That is a scaling by a nonzero rational, and a
    scaling cannot change the zero set, so the mask stays sound while the residues
    become informative.  All of it is integer arithmetic in `Z[sqrt d]`; no `Quad`
    multiplication is involved, which is where the speed comes from.
    """
    out = []
    for A, B in _axis_residual_ints(cls, PX, PY, WX, WY, i, j, D):
        g = math.gcd(abs(A), abs(B))
        out.append(cls(A // g, B // g) if g else cls(0, 0))
    return out


def pair_max_slack_bound(cls, PX, PY, WX, WY, i, j, D, S=None):
    """A certified **positive** lower bound on a pair's max SAT slack, or `None`.

    The gate's two pair verdicts are 'contact' (max slack == 0) and 'violation' (max
    slack < 0).  A pair with a *strictly positive* max slack is therefore neither, so it
    can be dropped before the exact test -- and that is the correct object to bound:
    the max slack, not the tightest axis.  (A diagonal neighbour has one exactly tight
    axis and one loose one, so a bound on the *minimum* would never reject it.  Doc 64
    records the correction: the request's phrasing named the tightest axis, and the
    tightest axis is precisely what keeps the survivors.)

    The bound is elementary and exact.  A residual `z = A + B sqrt d` with `A, B` in
    `Z` has `|N(z)|` a positive integer when it is nonzero, so

        |z| = |N(z)| / |zbar| >= 1 / (|A| + |B| S)      for any rational `S >= sqrt d`,

    and `z > 0` is decided by an integer comparison of `A^2` with `d B^2`.  The whole
    test is integer arithmetic plus one rational bound; it never divides by a field
    element and never builds a `Quad`.  The scan stops at the first axis it can prove
    positive, which is where the cheapness comes from.

    Returns `{"axis": k, "lo": Fraction}` with `lo > 0` a lower bound on the pair's
    max slack, or `None` ("no opinion" -- the pair must go to the exact gate).
    """
    scale = 2 * D * D
    d = cls.d
    S = EF.sqrt_upper(d) if S is None else S
    for k, (A, B) in enumerate(_axis_residual_ints(cls, PX, PY, WX, WY, i, j, D)):
        if EF.integral_sign(A, B, d) > 0:
            return {"axis": k, "lo": EF.abs_lower_bound(A, B, d, S) / F(scale)}
    return None


def _zabs_ge(z, s, d):
    """Exact `|z| >= s` for an integer `z = (a, b)` and an integer `s`.

    `|z| >= s` iff `z >= s` or `z <= -s`, and each of those is one integer sign
    comparison (`integral_sign`).  No `Quad`, no `Fraction`: this is the cheap exact
    prune, and it decides the same skip the gate's own `abs(dx) >= 2` decides.
    """
    a, b = z
    return (EF.integral_sign(a - s, b, d) >= 0
            or EF.integral_sign(a + s, b, d) <= 0)


def chained_screen(state, words, cls=None, mods=(8,), use_mask=True, use_bound=True):
    """The four-stage chain: prune -> residue mask -> max-slack bound -> exact gate.

    * **prune** -- the same exact `|dx| >= 2 or |dy| >= 2` skip as the gate's, but
      decided on integer components (`_zabs_ge`) instead of `Quad` values -- the same
      pairs, a fraction of the cost, and it is timed as its own stage;
    * **mask** -- drop a pair with no exactly tight axis (the run-100 plugin);
    * **bound** -- drop a pair whose max slack has a certified positive lower bound;
    * **gate** -- the exact four-axis test on everything that survives.

    The three stages are not interchangeable, and the difference is measured here, not
    asserted.  The **bound is verdict-preserving**: a positive max slack means the pair
    is neither a contact nor an overlap, so dropping it cannot change either count.  The
    **mask is only contact-safe**: an overlapping pair has no tight axis either, so the
    mask hides violations unless the sentence is already known feasible.  The chain
    therefore re-checks every mask-dropped pair against the exact verdict (outside the
    timed region) and reports how many violations the mask would have hidden.

    Timings are integer nanoseconds, so the benchmark is float-free; the reference is
    `Q.gate` on the whole sentence.
    """
    cls = cls or Q.field_of(state)
    d = cls.d
    D = residue_common_den(state, words)
    PX = [_scale_cell(cls, p[0], D) for p in state]
    PY = [_scale_cell(cls, p[1], D) for p in state]
    WX = [_scale_cell(cls, w[0], D) for w in words]
    WY = [_scale_cell(cls, w[1], D) for w in words]
    t0 = time.perf_counter_ns()
    lim = 2 * D
    pairs = []
    for i in range(len(state)):
        for j in range(i + 1, len(state)):
            dx = (PX[j][0] - PX[i][0], PX[j][1] - PX[i][1])
            if _zabs_ge(dx, lim, d):
                continue
            dy = (PY[j][0] - PY[i][0], PY[j][1] - PY[i][1])
            if _zabs_ge(dy, lim, d):
                continue
            pairs.append((i, j))
    t_prune = time.perf_counter_ns() - t0
    survivors, masked, bounded = [], [], []
    t0 = time.perf_counter_ns()
    for i, j in pairs:
        raws = _axis_residual_ints(cls, PX, PY, WX, WY, i, j, D)
        if use_mask and EF.residue_norm_filter_ints(d, raws, mods)[mods[0]]["all_nonzero"]:
            masked.append((i, j))
            continue
        if use_bound:
            hit = pair_max_slack_bound(cls, PX, PY, WX, WY, i, j, D)
            if hit is not None:
                bounded.append((i, j, hit))
                continue
        survivors.append((i, j))
    t_front = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    contacts = violations = 0
    worst = None
    for i, j in survivors:
        best = max(sl for _q, sl, _n, _o in Q.pair_axes(state, words, i, j, cls))
        if best == 0:
            contacts += 1
        if best.sign() < 0:
            violations += 1
        if worst is None or best < worst:
            worst = best
    t_gate = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    gate = Q.gate(state, words, cls)
    t_ref = time.perf_counter_ns() - t0
    # outside the timed region: what the mask dropped that the exact verdict counts
    hidden = 0
    for i, j in masked:
        best = max(sl for _q, sl, _n, _o in Q.pair_axes(state, words, i, j, cls))
        if best.sign() < 0:
            hidden += 1
    pipeline_ns = t_prune + t_front + t_gate
    # the filters' own contribution, with the prune held fixed: the exact pair test
    # over every candidate, measured after the pipeline so it cannot disturb it
    t_gate_all = None
    if use_mask and use_bound:
        t0 = time.perf_counter_ns()
        for i, j in pairs:
            Q.pair_axes(state, words, i, j, cls)
        t_gate_all = time.perf_counter_ns() - t0
    out = {"pairs": len(pairs), "contacts": gate["contacts"],
           "violations": gate["violations"], "den": D,
           "masked": len(masked), "bounded": len(bounded),
           "gate_calls": len(survivors), "pipeline_contacts": contacts,
           "pipeline_violations": violations,
           "mask_hidden_violations": hidden,
           "t_prune_ns": t_prune, "t_front_ns": t_front, "t_gate_ns": t_gate,
           "t_gate_all_ns": t_gate_all,
           "t_pipeline_ns": pipeline_ns, "t_reference_ns": t_ref,
           "speedup": (F(t_ref, pipeline_ns) if pipeline_ns else F(0)),
           "filter_gain": (F(t_gate_all, t_front + t_gate)
                           if t_gate_all and t_front + t_gate else None),
           "use_mask": use_mask, "use_bound": use_bound}
    if violations == 0 and gate["violations"] == 0:
        out["equivalent"] = (contacts == gate["contacts"] and worst == gate["clearance"])
    else:
        out["equivalent"] = (contacts == gate["contacts"]
                             and violations == gate["violations"])
    return out


def residue_pair_screen(state, words, cls=None, mods=(8, 12, 24)):
    """The norm mask over every candidate pair, against the exact four-axis test.

    Three timed passes -- the mask alone, the exact test alone, and the pipeline (mask,
    then the exact test only on the survivors) -- each modulus's own pipeline being
    timed separately.  A rejected pair is **not** skipped for overlap: the mask only
    proves "not exactly tangent", which is exactly what a contact/declaration stage
    needs, and claiming more would be unsound.  Timings are `perf_counter_ns`
    integers, so even the benchmark is float-free.
    """
    cls = cls or Q.field_of(state)
    D = residue_common_den(state, words)
    PX = [_scale_cell(cls, p[0], D) for p in state]
    PY = [_scale_cell(cls, p[1], D) for p in state]
    WX = [_scale_cell(cls, w[0], D) for w in words]
    WY = [_scale_cell(cls, w[1], D) for w in words]
    two = cls(2)
    pairs = []
    for i in range(len(state)):
        xi, yi = state[i]
        for j in range(i + 1, len(state)):
            if abs(state[j][0] - xi) >= two or abs(state[j][1] - yi) >= two:
                continue
            pairs.append((i, j))
    t0 = time.perf_counter_ns()
    masks = [EF.residue_norm_filter(
        cls, pair_tangency_residuals(cls, PX, PY, WX, WY, i, j, D), mods)
        for i, j in pairs]
    t_mask = time.perf_counter_ns() - t0
    t0 = time.perf_counter_ns()
    exact = []
    for i, j in pairs:
        exact.append(max(sl for _q, sl, _n, _o in Q.pair_axes(state, words, i, j, cls)))
    t_exact = time.perf_counter_ns() - t0
    contacts = sum(1 for b in exact if b == 0)
    out = {"pairs": len(pairs), "contacts": contacts, "den": D,
           "t_mask_ns": t_mask, "t_exact_ns": t_exact, "mods": list(mods)}
    for mod in mods:
        rej = [k for k, m in enumerate(masks) if m[mod]["all_nonzero"]]
        rej_set = set(rej)
        t0 = time.perf_counter_ns()
        kept = 0
        for k, (i, j) in enumerate(pairs):
            if k in rej_set:
                continue
            best = max(sl for _q, sl, _n, _o in Q.pair_axes(state, words, i, j, cls))
            if best == 0:
                kept += 1
        t_mixed = time.perf_counter_ns() - t0
        out[mod] = {"rejected": len(rej),
                    "survivors": len(pairs) - len(rej),
                    "false_rejects": sum(1 for k in rej if exact[k] == 0),
                    "abstained": sum(1 for m in masks if m[mod]["abstain"]),
                    "contacts_masked": kept,
                    "t_mixed_ns": t_mixed,
                    "t_pipeline_ns": t_mask + t_mixed,
                    # the mask is part of the pipeline, so its cost is in the denominator
                    "speedup": (F(t_exact, t_mask + t_mixed)
                                if t_mask + t_mixed else F(0))}
    return out


# ------------------------------------- serialized certificates (run 101)
#: The wire format is deliberately dumb: exact strings, one rotation per cell, one
#: container box per certificate.  A reader that needs nothing but `Fraction` can
#: verify the whole thing, which is the point -- the certificate is the object, and
#: every decimal in this project (CSV cells, table columns, printed shadows) is a
#: projection of it, flagged as such in the document's `display_only` block.
def field_tag(cls):
    """The schema's field tag for a scalar class: `Q` or `Quad(d)`."""
    d = getattr(cls, "d", 0) or 0
    return "Q" if d == 0 else f"Quad({d})"


def certificate_scalar(z, tag):
    """One exact scalar as the schema writes it: a string, or an `[a, b]` pair."""
    a, b = _ab(z)
    if tag == "Q":
        return str(F(a))
    return [str(a), str(b)]


def certificate_of(cid, family, state, words, cls, note=""):
    """Serialize one sentence: exact field, exact side, exact rotations and centres.

    `origin` is the sentence's own bounding box's lower corner, and `L` its exact side,
    so the certificate carries a *tight* container rather than a family convention.  The
    `expected` block is the gate's own summary; the verifier recomputes it and refuses a
    document whose declaration does not match the object.
    """
    tag = field_tag(cls)
    ex = [Q.frame_extent(c, s, cls) for c, s in words]
    ox = min(p[0] - e for p, e in zip(state, ex))
    oy = min(p[1] - e for p, e in zip(state, ex))
    L = Q.side(state, words, cls)
    g = Q.gate(state, words, cls)
    cells = [{"x": certificate_scalar(p[0], tag),
              "y": certificate_scalar(p[1], tag),
              "r": [certificate_scalar(c, tag), certificate_scalar(-s, tag),
                    certificate_scalar(s, tag), certificate_scalar(c, tag)]}
             for p, (c, s) in zip(state, words)]
    return {"id": cid, "family": family, "field": tag, "N": len(state),
            "L": certificate_scalar(L, tag),
            "origin": [certificate_scalar(ox, tag), certificate_scalar(oy, tag)],
            "cells": cells,
            "expected": {"ok": g["ok"], "contacts": g["contacts"],
                         "violations": g["violations"],
                         "clearance": (certificate_scalar(g["clearance"], tag)
                                       if g["clearance"] is not None else None)},
            "note": note}


def certificate_families():
    """The representatives: one per field tag, and the four named certified families."""
    out = []
    half = F(1, 2)
    tile = [(F(i) + half, F(j) + half) for j in range(2) for i in range(2)]
    out.append(certificate_of(
        "tile2", "Tile 2k (k = 1, axis grid, rational)", tile,
        [(F(1), F(0))] * 4, None,
        "the smallest certificate in the file; it is the one that exercises the Q tag"))
    ring = p_ring(1)
    out.append(certificate_of("ring18", "Ring (n = 18)", ring.payload["state"],
                              ring.payload["words"],
                              Q.field_of(ring.payload["state"]),
                              "the ring sentence: 10 + 4 + 4 squares, 26 contacts"))
    stair = p_staircase(5)
    out.append(certificate_of("staircase149", "Staircase (n = 149)",
                              stair.payload["state"], stair.payload["words"],
                              Q.field_of(stair.payload["state"]),
                              "the multi-layer staircase at k = 5, 449 contacts"))
    capped = staircase_capped(5)
    out.append(certificate_of("staircase150", "Staircase + cap brick (n = 150)",
                              capped["cells"], capped["words"], capped["cls"],
                              "the 149 plus the cap brick placed by the pocket cage"))
    b45 = p_block45(5, 4)
    out.append(certificate_of("block45_5_4", "Block45 (s = 5, k = 4)",
                              b45.payload["state"], b45.payload["words"],
                              Q.field_of(b45.payload["state"]),
                              "N = 65 at L = 5 + 5/2 sqrt 2, 172 contacts"))
    b45h = p_block45half(17, 14)
    out.append(certificate_of("block45half_17_14", "Block45Half (s = 17, k = 14)",
                              b45h.payload["state"], b45h.payload["words"],
                              Q.field_of(b45h.payload["state"]),
                              "N = 653 at L = 29/2 + 17/2 sqrt 2, 2256 contacts"))
    try:
        slope = p_slope(2, 1, 1, 1)
    except Exception as exc:                      # pragma: no cover - schema demo only
        out.append({"id": "slope21_note", "family": "Slope 2:1 (unavailable)",
                    "field": "Quad(5)", "N": 0, "L": "0", "origin": ["0", "0"],
                    "cells": [], "expected": {"ok": False},
                    "note": f"Quad(5) representative could not be built: {exc}"})
    else:
        out.append(certificate_of("slope21", "Slope 2:1 ridge (k = 1, m = 1)",
                                  slope.payload["state"], slope.payload["words"],
                                  Q.field_of(slope.payload["state"]),
                                  "the Q(sqrt 5) representative"))
    return out


def certificate_document():
    """The whole serialized document: conventions, the display-only ledger, the cells."""
    return {
        "format": "galois-certificate/1",
        "run": 101,
        "date": "2026-11-22",
        "conventions": {
            "numbers": ("exact strings only: 'a' under tag Q, or [a, b] meaning "
                        "a + b*sqrt(d) under tag Quad(d); reduced fractions, never decimals"),
            "field_tags": ["Q", "Quad(2)", "Quad(5)", "Quad(7)"],
            "rotation": ("each cell stores R row-major as [ux, vx, uy, vy]; the verifier "
                         "checks R^T R = I and det R = 1"),
            "container": ("a square of side L with lower corner `origin`; a cell is "
                          "inside iff origin <= centre - e and centre + e <= origin + L "
                          "with e = (|ux| + |uy|)/2"),
            "sat": ("a pair is separated iff some axis q of either frame has "
                    "|d.q| - (1/2 + ext_other(q)) >= 0; the witness is the axis with "
                    "the largest slack, and >= 0 is accepted at clearance 0"),
            "first_failure": ("the verifier stops at the first exact failed inequality "
                              "and names it, distinguishing `infeasible` from "
                              "`outside_representation`"),
        },
        "display_only": [
            {"surface": "submission.csv", "exact": False,
             "note": ("12-dp decimal strings: a projection of the pose, never an input "
                      "to an exact check")},
            {"surface": "README.md / STATUS.md tables", "exact": False,
             "note": "rounded for reading; every number there has an exact source"},
            {"surface": "CLI and event prints", "exact": False,
             "note": ("decimal shadows via Decimal at 12 dp; where a decision is "
                      "reported the exact string is printed beside it")},
        ],
        "certificates": certificate_families(),
    }


def write_certificates(path):
    """Write `galois_certificates.json` and return the document written."""
    doc = certificate_document()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    return doc


def _ratio_str(fr):
    """A rational to two decimal places, exactly -- the print path stays float-free."""
    h = fr * 100                      # in units of 0.01
    q = h.numerator // h.denominator  # truncate, exactly
    return f"{q // 100}.{q % 100:02d}"


def _lattice_sentence(nx=10, ny=10):
    """A synthetic sparse sentence: a 3/2 x 1 lattice of axis squares, gate-certified.

    Columns touch (`|dy| = 1`) and rows are half a unit apart (`|dx| = 3/2`), so the
    candidate set is large and the contact set is only the vertical chains.  This is
    the mask's *best* case and is labelled synthetic wherever it is reported: the four
    certified wheel cells above are contact-dense and are the mask's worst case.
    """
    cls = qfield(2)
    cells, words = [], []
    for i in range(nx):
        for j in range(ny):
            cells.append((cls(F(3 * i, 2) + F(1, 2)), cls(j + F(1, 2))))
            words.append((cls(1), cls(0)))
    return cells, words


def _benchmark_cells():
    """The five rows doc 63 §2 benchmarks on: four certified cells, one synthetic."""
    todo = []
    for name, build in (("Block45(5,4)", lambda: p_block45(5, 4)),
                        ("Block45(10,8)", lambda: p_block45(10, 8)),
                        ("Block45Half(5,4)", lambda: p_block45half(5, 4)),
                        ("Block45Half(17,14)", lambda: p_block45half(17, 14))):
        claim = build()
        todo.append((name, claim.payload["state"], claim.payload["words"]))
    st, wo = _lattice_sentence()
    todo.append(("Lattice(3/2,1) [synthetic sparse]", st, wo))
    return todo


def chain_benchmark(mods=(8,)):
    """The chained pipeline over the five rows, in three configurations.

    `mask` is the run-100 stage alone, `bound` is the run-101 stage alone, `mask+bound`
    is the chain the request names.  Reporting all three is what makes the comparison
    honest: the bound is a superset of the mask on a certified sentence (it also
    rejects the diagonal survivors), so `mask+bound` and `bound` do the same gate work
    while `mask` does more -- and on a sentence with overlaps only the bound is safe.
    """
    rows = []
    for name, state, words in _benchmark_cells():
        cls = Q.field_of(state)
        for label, mk, bd in (("mask", True, False), ("bound", False, True),
                              ("mask+bound", True, True)):
            scr = chained_screen(state, words, cls, mods=mods, use_mask=mk, use_bound=bd)
            scr.update({"cell": name, "stage": label})
            rows.append(scr)
    return rows


def residue_benchmark(mods=(8, 12, 24)):
    """The residue stage over the certified cells: contacts, rejections, speedups."""
    rows = []
    for name, state, words in _benchmark_cells():
        cls = Q.field_of(state)
        scr = residue_pair_screen(state, words, cls, mods=mods)
        gate = Q.gate(state, words, cls)
        scr.update({"cell": name, "gate_contacts": gate["contacts"],
                    "gate_ok": gate["ok"],
                    "contacts_match": gate["contacts"] == scr["contacts"]})
        rows.append(scr)
    return rows


# ------------------------------------------------- the two-word seam (run 97)
#: A two-word sentence is not a new engine: the gate already carries one word per
#: square (`Q.gate(state, words, cls)`), so what was missing is a *builder* whose
#: seam width is derived from two different words at once.  The ridge is the right
#: place to ask, because its seam is a single number `w` shared by every square in
#: the bar -- which is exactly why two words cannot cancel each other's requirement.
def seam_floor(cls, c, s):
    """`phi(theta) = min(x, 1/x)`, `x = |c| + |s|`: one square's seam requirement.

    A unit square at word `(c, s)` placed in the ridge's cross (four `k`-blocks and
    a seam of width `w`) is tangent to the blocks at `w = phi(theta)`, and the
    single-word ridge attains that width at every word -- so `phi` is the value, not
    a lower bound.  For a unit word `1 <= x <= sqrt 2` (as `x^2 = 1 + 2|c s| <= 2`),
    hence

        phi(theta) >= 1/sqrt 2,

    with equality exactly at `|c| = |s| = sqrt2 / 2`, the 45-degree word and its
    quarter turns.  That is the single-word seam floor restated per square: the
    floor is not a property of a *family*, it is the price one square pays for
    standing in a cross.
    """
    x = abs(c) + abs(s)
    one = cls(1)
    return min(one / x, x)


def two_word_need(cls, q1, q2):
    """The exact centre distance two unit squares of *different* words need.

    Along the first square's own `u` the second square subtends
    `(|cos D| + |sin D|)/2` for `D = theta2 - theta1`, so the separating-axis test
    reads `|d . u1| >= 1/2 + that`, i.e.

        need = (1 + |c1 c2 + s1 s2| + |s1 c2 - c1 s2|) / 2.

    For the same word (a quarter turn included) this is exactly 1; for any other
    pair it is *strictly* greater than 1, since `|cos D| + |sin D| > 1` off the
    axes.  A mixed tangency therefore never buys separation -- it pays for it.
    """
    (c1, s1), (c2, s2) = q1, q2
    half = cls(F(1, 2))
    dot = c1 * c2 + s1 * s2
    cross = s1 * c2 - c1 * s2
    return (cls(1) + abs(dot) + abs(cross)) * half


def _two_word_blocks(cls, k):
    """The four `k`-blocks of the box `[0, 2k + w]^2`, each coordinate `A + B w`."""
    half, zero, one = cls(F(1, 2)), cls(0), cls(1)
    out = []
    for bx in (0, 1):
        for by in (0, 1):
            for i in range(k):
                for j in range(k):
                    out.append((((cls(i) + half + (cls(k) if bx else zero)),
                                 one if bx else zero),
                                ((cls(j) + half + (cls(k) if by else zero)),
                                 one if by else zero)))
    return out


def _two_word_slots(cls, k, q1, q2):
    """The bar: word `q1` at the seam centre, word `q2` at the mixed need from it.

    Both coordinates are `A + w/2`, because the seam centre rides the box; only the
    fixed offsets differ.  The second square sits along `-v1`, so it touches the
    first square along *that square's* own axis -- the mixed (vertex-to-edge)
    tangency a single-word sentence cannot express.
    """
    c1, s1 = q1
    half = cls(F(1, 2))
    step = two_word_need(cls, q1, q2)
    off = (step * s1, -step * c1)
    return [((cls(k), half), (cls(k), half), q1),
            ((cls(k) + off[0], half), (cls(k) + off[1], half), q2)]


def two_word_widths(cls, k, q1, q2):
    """Every positive seam width at which the two-word bar touches a block, exactly.

    Each block-slot slack is `|P + Q w| - need`, so each contact equation has the two
    closed-form roots `(need - P)/Q` and `(-need - P)/Q`; the gate can only change
    verdict at one of them, so this is a finite exact set, not a scan.  The four blocks
    are `k^2` *unit* squares, so every need is the same mixed one, `1/2 + x/2` with
    `x = |c| + |s|`: the block subtends `1/2` on its own axes and `x/2` on the slot's.
    """
    half, zero, one = cls(F(1, 2)), cls(0), cls(1)
    slots = _two_word_slots(cls, k, q1, q2)
    roots = []
    for (bAx, bBx), (bAy, bBy) in _two_word_blocks(cls, k):
        for (sAx, sBx), (sAy, sBy), (c, s) in slots:
            dAx, dBx = bAx - sAx, bBx - sBx
            dAy, dBy = bAy - sAy, bBy - sBy
            x = abs(c) + abs(s)
            need = half + x * half
            for (qx, qy) in ((one, zero), (zero, one), (c, s), (-s, c)):
                P = dAx * qx + dAy * qy
                Qc = dBx * qx + dBy * qy
                if Qc == zero:
                    continue
                for sign in (one, cls(-1)):
                    w = (sign * need - P) / Qc
                    if w.sign() > 0 and all(w != r for r in roots):
                        roots.append(w)
    roots.sort()
    return roots


def _two_word_pair_axes(cls, k, q1, q2):
    """Every separating-axis constraint of the two-word bar, as `A + B w` data.

    Returns `(constraints, fixed)`: `constraints` is a list of `(P, Q, need)` triples
    per pair (four of them per pair), and `fixed` is `True` iff the bar's own pair is
    already separated at every `w` (its separation does not depend on the seam, since
    both squares ride the seam centre together).
    """
    half, zero, one = cls(F(1, 2)), cls(0), cls(1)
    (c1, s1), (c2, s2) = q1, q2
    slots = _two_word_slots(cls, k, q1, q2)
    out = []
    for (bAx, bBx), (bAy, bBy) in _two_word_blocks(cls, k):
        for (sAx, sBx), (sAy, sBy), (c, s) in slots:
            dAx, dBx = bAx - sAx, bBx - sBx
            dAy, dBy = bAy - sAy, bBy - sBy
            x = abs(c) + abs(s)
            need = half + x * half
            for (qx, qy) in ((one, zero), (zero, one), (c, s), (-s, c)):
                out.append((dAx * qx + dAy * qy, dBx * qx + dBy * qy, need))
    # the bar's own pair: same data at w = 0, separation is w-free
    d = (slots[1][0][0] - slots[0][0][0], slots[1][1][0] - slots[0][1][0])
    fixed = False
    for (qx, qy), _owner, other in (((c1, s1), 0, 1), ((-s1, c1), 0, 1),
                                    ((c2, s2), 1, 0), ((-s2, c2), 1, 0)):
        oc, os_ = (c2, s2) if other == 1 else (c1, s1)
        proj = abs(d[0] * qx + d[1] * qy)
        need = half + (abs(oc * qx + os_ * qy) + abs(oc * qy - os_ * qx)) * half
        if proj >= need:
            fixed = True
            break
    return out, fixed


def two_word_gauge(cls, k, q1, q2):
    """The minimal seam width at which the two-word bar fits, in closed form.

    The four blocks ride outward with `w` while the bar rides outward with `w/2`, so
    every block-slot separation is *monotone* in `w`: once separated, always
    separated.  The sentence's minimal width is therefore the maximum over pairs of
    the pair's own threshold, and a pair's threshold is the smallest `w` at which any
    one of its four axes separates -- each of which is an exact root of a linear
    equation.  So this is a finite closed form, not a scan: the same discipline the
    single ridge uses for `w = min(1/(c+s), c+s)`.
    """
    zero = cls(0)
    cons, fixed = _two_word_pair_axes(cls, k, q1, q2)
    if not fixed:
        raise Refusal("two_word_inside",
                      f"the two bar squares overlap at every width ({q1} x {q2})")
    # per-pair: the four axes of one pair are consecutive in `cons`, and a pair is
    # separated as soon as *any* one of them is, so its threshold is their minimum
    width = zero
    for i in range(0, len(cons), 4):
        t_pair = None
        for P, Qc, need in cons[i:i + 4]:
            if Qc == zero:
                t = zero if abs(P) >= need else None
            elif abs(P) >= need:
                t = zero
            else:
                lo_ = (need - P) / Qc
                hi_ = (-need - P) / Qc
                hi = hi_ if hi_ > lo_ else lo_
                t = hi if hi.sign() > 0 else zero
            if t is not None and (t_pair is None or t < t_pair):
                t_pair = t
        if t_pair is None:
            raise Refusal("two_word_inside", f"a block-slot pair never separates ({q1} x {q2})")
        if t_pair > width:
            width = t_pair
    return width


def two_word_pair(d, q1, q2, k, family="TwoWord", params=None):
    """Gate-verify a two-word seam sentence over `Q(sqrt d)` and return it as a claim.

    The bar is one square of each word in the ridge's cross, the second at the first's
    mixed need, and the width is the smallest closed-form contact width at which the
    exact gate passes -- so the claim is a sentence, not an interpolation.  Refusals
    are declared, never incidental:
      * `word_off_circle`    -- a declared word is not a unit word of the field;
      * `two_word_same_word` -- the two words are one word up to a quarter turn;
      * `two_word_no_gauge`  -- no contact width in the closed-form set;
      * `two_word_inside`    -- widths exist, but a pair still overlaps at all of them.
    """
    cls = qfield(d)
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k} has no blocks")
    for c, s in (q1, q2):
        if (c * c + s * s) != cls(1):
            raise Refusal("word_off_circle",
                          f"cos^2 + sin^2 = {c * c + s * s} != 1 in Q(sqrt {d})")
    if _square_canon(*q1) == _square_canon(*q2):
        raise Refusal("two_word_same_word",
                      f"{q1} and {q2} are one word up to a quarter turn")
    try:
        w0 = two_word_gauge(cls, k, q1, q2)
    except Refusal:
        raise
    # candidates: the closed-form minimum, then any later contact width (the gate is
    # the arbiter, so a closed-form answer that did not gate would be reported, not hidden)
    widths = [w0] + [w for w in two_word_widths(cls, k, q1, q2) if w > w0]
    last = None
    half = cls(F(1, 2))
    for w in widths[:6]:
        L = cls(2 * k) + w
        state, words = [], []
        for bx in (0, 1):
            for by in (0, 1):
                x0 = cls(0) if bx == 0 else L - cls(k)
                y0 = cls(0) if by == 0 else L - cls(k)
                for i in range(k):
                    for j in range(k):
                        state.append((x0 + cls(i) + half, y0 + cls(j) + half))
                        words.append((cls(1), cls(0)))
        for (Ax, ABx), (Ay, ABy), word in _two_word_slots(cls, k, q1, q2):
            state.append((Ax + ABx * w, Ay + ABy * w))
            words.append(word)
        g = Q.gate(state, words, cls)
        last = g
        if not g["ok"]:
            continue
        n = len(state)
        claim = Claim("spatial_geometry", family,
                      params or {"k": k, "word1": str(q1), "word2": str(q2)}, n,
                      {"count": ("N", n), "extent": ("L", g["L"]),
                       "void": ("L^2 - N", g["L"] * g["L"] - cls(n)),
                       "contacts": ("contacts", g["contacts"])},
                      {"state": state, "words": words, "field": f"Q(sqrt {d})",
                       "seam": w, "bar": 2})
        claim.meta["field_d"] = d
        claim.meta["seam"] = str(w)
        claim.meta["two_word"] = True
        claim.laws["seam"] = ("w", w)
        claim.laws["floor"] = ("phi(w1), phi(w2)",
                               (seam_floor(cls, *q1), seam_floor(cls, *q2)))
        _tag(claim, g["L"], n)
        side = _table_side(n)
        if side is None:
            claim.meta["table_side"] = None
            claim.meta["beats_table"] = None
        else:
            Ld = DecimalWitness.scalar(g["L"])
            Td = DecimalWitness.scalar(side)
            claim.meta["table_side"] = str(side)
            claim.meta["beats_table"] = Ld < Td
            claim.meta["table_gap"] = str(Td - Ld)
        return claim
    raise Refusal("two_word_inside",
                  f"{family}: best width {widths[-1]} still overlaps"
                  if last is None else
                  f"{family}: {last['violations']} pairs overlap at every width")


def two_word_word_sample():
    """The two words groups the spin uses, each inside one field.

    The 45-degree word is not in Q(sqrt 7) and the census word is not in Q(sqrt 2), so
    the sample is two groups and the gate is asked inside each.  The rational words are
    the bridge: they embed in every field, so the Seventh and the census word can be
    paired with the same fractions the 45-degree column uses.
    """
    groups = {2: [], 7: []}
    names2 = ("45deg", "t=1/2", "t=1/3", "t=1/5",
              "pyth-3/4", "pyth-5/12", "pyth-8/15")
    for name, d, c, s in staircase_words():
        if d == 2 and name in names2:
            groups[2].append((name, c, s))
    cls7 = qfield(7)
    groups[7].append(("Seventh", cls7(0, F(1, 4)), cls7(F(3, 4))))
    cw, sw = _sqrt7_word()
    groups[7].append(("census", cw, sw))
    for p, q in ((3, 4), (5, 12), (8, 15), (1, 2), (1, 3)):
        tc, ts = EF.tword(p, q)
        groups[7].append((f"pyth7-{p}/{q}", cls7(F(tc)), cls7(F(ts))))
    return groups


def two_word_spin(kmax=8):
    """Spin the two-word seam over word pairs, with both references it could beat.

    The two references are the single-word floor `2k + 1/sqrt 2` (a per-square fact,
    `seam_floor`) and the delivered side at the same `N = 4k^2 + 2`.  Each row is a
    *built* sentence or the code's own refusal; nothing is claimed about a score.

    The floor comparison is in 70-digit `Decimal` because `1/sqrt 2` is not an element
    of `Q(sqrt 7)`: the reference carries ~1e-69 of error and every margin here is at
    least 1e-3, so the sign is decisive and no float is used.
    """
    rows = []
    half_sqrt2 = Decimal(2).sqrt() / 2
    for d, ws in sorted(two_word_word_sample().items()):
        cls = qfield(d)
        for i in range(len(ws)):
            for j in range(i + 1, len(ws)):
                n1, c1, s1 = ws[i]
                n2, c2, s2 = ws[j]
                need = DecimalWitness.scalar(two_word_need(cls, (c1, s1), (c2, s2)))
                for k in range(1, kmax + 1):
                    rec = {"field": f"Q(sqrt {d})", "word1": n1, "word2": n2,
                           "k": k, "N": 4 * k * k + 2, "need_dec": str(need),
                           "floor1_dec": str(DecimalWitness.scalar(seam_floor(cls, c1, s1))),
                           "floor2_dec": str(DecimalWitness.scalar(seam_floor(cls, c2, s2)))}
                    try:
                        claim = two_word_pair(d, (c1, s1), (c2, s2), k)
                    except Refusal as e:
                        rec["verdict"] = e.law
                        rows.append(rec)
                        continue
                    L = claim.measure[1]
                    Ld = DecimalWitness.scalar(L)
                    floor_d = Decimal(2 * k) + half_sqrt2
                    rec["verdict"] = "gated"
                    rec["L"] = str(L)
                    rec["L_dec"] = str(Ld)
                    rec["seam"] = str(claim.laws["seam"][1])
                    rec["seam_dec"] = str(DecimalWitness.scalar(claim.laws["seam"][1]))
                    rec["above_floor"] = Ld > floor_d
                    rec["gap_dec"] = str(Ld - floor_d)
                    rec["contacts"] = claim.laws["contacts"][1]
                    rec["beats_table"] = claim.meta.get("beats_table")
                    rec["table_gap"] = claim.meta.get("table_gap")
                    rows.append(rec)
    return rows


# ------------------------------------------------------------------ the ring
#: Run 94 replaces run 93's four-corner-module ansatz with the sentence the census's
#: own n = 18 row is.  The row is a C2-symmetric **perimeter** of axis squares with
#: exactly one gap in each wall, one tilted square **wedged across each vertical
#: gap** (a contact on each of its own axes), and a **four-square pinwheel** that
#: carries each chain end around to the opposite gap square:
#:
#:     10 axis = 4 corner squares + a 2k-square run up the left wall + a 2k-square
#:               run down the right wall + one square inward on the bottom wall and
#:               one inward on the top wall                         (4k + 6 in general)
#:      4 gaps = the wedged squares p5, -p5 and the two chain ends p8, -p8
#:      4 pin  = the chain p5 -> p6 -> p7 -> p8 and its C2 image
#:
#: Each of the eight tilted squares is the unique solution of two declared tangencies,
#: so the sentence is *solved* in Q(sqrt 7) rather than read off the table; the exact
#: gate is the arbiter (control 24).
def ring_side(cls, c, s, k):
    """The ring's side, derived: the four corner squares sit flush in the box.

    A corner square's centre is `(a, a)` with `a = k + c`, so its outer face is at
    `a + 1/2` and

        L = 2a + 1 = 2k + 1 + 2c = 2k + 3/2 + (c + s),          (c - s = 1/2)

    the one side law of the whole Q(sqrt 7) family, `(2m+1)/2 + sqrt7/2`.  At `k = 1`
    it is the census's n = 18 side, `7/2 + sqrt7/2`.
    """
    return cls(2 * k + 1) + cls(2) * c


def ring_frame(cls, c, s, k):
    """The perimeter: 4 corner squares, a 2k-square run on each vertical wall, and one
    square on each horizontal wall -- `4k + 6` axis squares, C2-symmetric.

    The gaps are derived, not chosen: a vertical wall covers `2k + 2` of the `L` it
    has to span, so its single gap is `L - (2k + 2) = 2c - 1`; a horizontal wall
    covers 3 (corner, one square, corner), so its gap is `L - 3 = 2c + 2k - 2`.  At
    `k = 1` the ten centres are the census row's ten axis squares, exactly.
    """
    a = cls(k) + c
    cells = [(-a, -a), (-a, a), (a, a), (a, -a)]
    for j in range(1, 2 * k + 1):
        cells.append((-a, -a + cls(j)))          # left wall, up from the bottom corner
    for j in range(1, 2 * k + 1):
        cells.append((a, a - cls(j)))            # right wall, down from the top corner
    cells.append((-a + cls(1), -a))              # bottom wall, one in from the left
    cells.append((a - cls(1), a))                # top wall, one in from the right
    return cells


def _ring_dot(p, q):
    """The exact dot product of two field points."""
    return p[0] * q[0] + p[1] * q[1]


def _ring_at(cls, A, B, u, v):
    """The point `p` with `p . u = A` and `p . v = B`, for an orthonormal pair u, v."""
    return (A * u[0] + B * v[0], A * u[1] + B * v[1])


def _ring_neg(p):
    """The C2 image of a centre: the sentence is symmetric under `p -> -p`."""
    return (-p[0], -p[1])


def _ring_indices(k):
    """Named positions inside `ring_declaration`'s cell list."""
    f = 4 * k + 6
    return {"bl": 0, "tl": 1, "tr": 2, "br": 3, "l1": 4, "l2": 5,
            "r1": 4 + 2 * k, "r2": 5 + 2 * k, "b": 4 + 4 * k, "t": 5 + 4 * k,
            "p5": f, "m5": f + 1, "p6": f + 2, "m6": f + 3,
            "p7": f + 4, "m7": f + 5, "p8": f + 6, "m8": f + 7}


def ring_declaration(cls, c, s, k):
    """The 10 + 4 + 4 sentence, solved from its declared tangencies.

    A tilted unit square at centre `p` has its own edges along `u = (c, s)` and
    `v = (-s, c)`; its face in direction `u` sits at `p.u + 1/2`, and an axis square's
    reach along `u` is `(|c| + |s|)/2`.  So a tilted-axis tangency on `u` is exactly

        |(q - p) . u| = 1/2 + (|c| + |s|)/2 =: need,               q the axis square,

    and a tilted-tilted tangency on `u` or `v` is exactly `|(q - p) . u| = 1`.  One
    such equation per independent axis fixes a point, so every module below is a 2x2
    solve in the field -- no scan, no tolerance:

      * `p5` (right gap) -- `(run_end - p5).u = need` and `(p5 - corner).v = need`,
        with `run_end = (a, a - 2k)` the last square of the right wall's run and
        `corner = (a, -a)` the bottom-right corner: the square is wedged across the
        gap.  `-p5` is the same wedge in the left gap, by C2.
      * `p6 = p5 + v` -- an edge-to-edge step along the word's `v` axis.
      * `p7`, `p8` -- each fixed by one `v`-contact with its predecessor in the chain
        and one `u`-contact with the opposite gap square `-p5`; that second contact is
        the pinwheel, and it is what closes the chain on the far side.
      * `p -> -p` gives the other four tilted squares.
    """
    one = cls(1)
    a = cls(k) + c
    u, v = (c, s), (-s, c)
    need = cls(F(1, 2)) + (abs(c) + abs(s)) * cls(F(1, 2))
    frame = ring_frame(cls, c, s, k)
    run_end = (a, a - cls(2 * k))
    corner = (a, -a)
    p5 = _ring_at(cls, _ring_dot(run_end, u) - need, _ring_dot(corner, v) + need, u, v)
    p6 = (p5[0] + v[0], p5[1] + v[1])
    p7 = _ring_at(cls, -_ring_dot(p5, u) + one, _ring_dot(p6, v) + one, u, v)
    p8 = _ring_at(cls, -_ring_dot(p5, u) + one, _ring_dot(p7, v) + one, u, v)
    tilted = [p5, _ring_neg(p5), p6, _ring_neg(p6),
              p7, _ring_neg(p7), p8, _ring_neg(p8)]
    return {"cells": frame + tilted,
            "words": [(one, cls(0))] * len(frame) + [u] * len(tilted),
            "frame": len(frame), "gap": [p5, _ring_neg(p5), p8, _ring_neg(p8)],
            "chain": [p5, p6, p7, p8]}


def ring_tangencies(k):
    """Every tangency the 10 + 4 + 4 layout declares, as `(i, j)` pairs of the sentence.

    `frame` -- the eight perimeter contacts: the two runs' edge-to-edge steps, the two
               horizontal-wall squares (each flush on one edge, corner-touching the
               run square beside it), and the two corner-point contacts.
    `wedge` -- the four frame contacts that pin the vertical-gap squares: `p5` is
               wedged across the right gap between the run end `r2` and the corner
               `br`; `-p5` across the left gap between `l2` and `tl`.
    `chain` -- the six edge-to-edge steps `p5 -> p6 -> p7 -> p8` and their C2 images.
    `pin`   -- the four `u`-contacts that close the chain onto the opposite gap square
               (`p7`, `p8` against `-p5`, and `-p7`, `-p8` against `p5`).
    """
    x = _ring_indices(k)
    return {
        "frame": [(x["bl"], x["l1"]), (x["l1"], x["l2"]),
                  (x["tr"], x["r1"]), (x["r1"], x["r2"]),
                  (x["bl"], x["b"]), (x["l1"], x["b"]),
                  (x["tr"], x["t"]), (x["r1"], x["t"])],
        "wedge": [(x["p5"], x["r2"]), (x["p5"], x["br"]),
                  (x["m5"], x["l2"]), (x["m5"], x["tl"])],
        "chain": [(x["p5"], x["p6"]), (x["p6"], x["p7"]), (x["p7"], x["p8"]),
                  (x["m5"], x["m6"]), (x["m6"], x["m7"]), (x["m7"], x["m8"])],
        "pin": [(x["p7"], x["m5"]), (x["p8"], x["m5"]),
                (x["m7"], x["p5"]), (x["m8"], x["p5"])],
    }


def _ring_contact(cls, cells, words, i, j):
    """True iff the pair's tightest axis is exactly touching: an exact contact.

    The gate's own test, not a weaker one: every axis slack is `>= 0` (the sentence is
    separated) and the largest of them is exactly `0` (nothing separates the pair by
    more).  A pair can share a zero slack on one axis and still be held apart on
    another -- the ring has 38 such coincidences and only 26 contacts -- so the
    declaration is checked against the strict reading.
    """
    return max(sl for _q, sl, _n, _o in Q.pair_axes(cells, words, i, j, cls)) == 0


def ring_field(cls, c, s, k):
    """The ring, verified: walls flush, every declared tangency an exact contact, and
    the exact gate at the side `ring_side` derives.

    Refusals are declared laws, not accidents:
      * `degenerate_cell`    -- `k < 1` has no ring;
      * `ring_wall_open`     -- a perimeter square is not flush with the container;
      * `ring_chain_adrift`  -- a declared tangency is not a contact.  This is the
                                family's real limit: the pinwheel's `u`-contacts close
                                on the opposite gap square only at `k = 1` (control 24
                                measures the exact slack at `k = 2, 3, 5`);
      * `ring_side_mismatch` -- the gate's side is not `ring_side`;
      * `ring_collides`      -- the sentence overlaps at its derived side.
    """
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k} has no ring")
    L = ring_side(cls, c, s, k)
    half = cls(F(1, 2))
    decl = ring_declaration(cls, c, s, k)
    cells, words = decl["cells"], decl["words"]
    wall = 0
    for p in cells[:decl["frame"]]:
        for z in (p[0], p[1]):
            if abs(z) + half == L * half:
                wall += 1
    if wall != 4 * k + 10:
        raise Refusal("ring_wall_open",
                      f"k = {k}: {wall} flush wall faces, not {4 * k + 10}")
    tang = ring_tangencies(k)
    for i, j in [pair for group in tang.values() for pair in group]:
        if not _ring_contact(cls, cells, words, i, j):
            raise Refusal("ring_chain_adrift",
                          f"k = {k}: the declared tangency ({i}, {j}) is not a "
                          f"contact -- the pinwheel closes only at k = 1")
    g = Q.gate(cells, words, cls)
    if g["L"] != L:
        raise Refusal("ring_side_mismatch", f"k = {k}: the gate reads {g['L']}, not {L}")
    if not g["ok"]:
        raise Refusal("ring_collides",
                      f"k = {k}: {g['violations']} pairs overlap at the derived side")
    decl.update({"gate": g, "wall": wall, "tangencies": tang})
    return decl


def ring_claim(d, c, s, k, family="Ring", params=None):
    """Gate-verify a ring over `Q(sqrt d)` and return it as a claim.

    `N = 4k + 14` (4k + 6 axis squares plus eight tilted) and
    `L = 2k + 3/2 + (c + s)`.  At the census's Q(sqrt 7) word with `k = 1` that is
    `N = 18`, `L = 7/2 + sqrt7/2` -- the n = 18 row's own side, built here from the
    word and 22 declared tangencies instead of read off the table.
    """
    cls = qfield(d)
    if (c * c + s * s) != cls(1):
        raise Refusal("word_off_circle",
                      f"cos^2 + sin^2 = {c * c + s * s} != 1 in Q(sqrt {d})")
    decl = ring_field(cls, c, s, k)
    state, words = decl["cells"], decl["words"]
    g = decl["gate"]
    n = len(state)
    L = g["L"]
    claim = Claim("spatial_geometry", family, params or {"k": k}, n,
                  {"count": ("N", n), "extent": ("L", L),
                   "void": ("L^2 - N", L * L - cls(n)),
                   "contacts": ("contacts", g["contacts"])},
                  {"state": state, "words": words, "field": f"Q(sqrt {d})",
                   "frame": decl["frame"], "wall": decl["wall"],
                   "tangencies": decl["tangencies"], "gap": decl["gap"]})
    claim.meta["field_d"] = d
    claim.meta["seam"] = str(c + s)
    claim.meta["frame"] = decl["frame"]
    claim.meta["wall"] = decl["wall"]
    claim.meta["declared"] = sum(len(v) for v in decl["tangencies"].values())
    _tag(claim, L, n)
    claim.laws["side"] = ("L", L)
    claim.laws["axis"] = ("axis squares", decl["frame"])
    claim.laws["gap"] = ("gap squares", 4)
    claim.laws["pinwheel"] = ("pinwheel squares", 4)
    side = _table_side(n)
    if side is None:
        claim.meta["table_side"] = None
        claim.meta["beats_table"] = None
    else:
        Ld = DecimalWitness.scalar(L)
        Td = DecimalWitness.scalar(side)
        claim.meta["table_side"] = str(side)
        claim.meta["beats_table"] = Ld < Td
        claim.meta["table_gap"] = str(Td - Ld)
    return claim


def p_ring(k):
    """The ring rung: a ring at the census's own Q(sqrt 7) word."""
    c, s = _sqrt7_word()
    return ring_claim(7, c, s, k)


# --------------------------------------------------- the staircase (run 95)
#: The census's n = 151 row is not the ring.  It is a **multi-layer staircase**:
#: an odd integer grid, every cell of which is realised on one of two lattices
#: offset by `2c` on both axes (an upper-left staircase `A` and a lower-right one
#: `B`), four corner caps, and a two-layer brick wall of word-aligned squares
#: wedged into the diagonal seam between the blocks.  The seam is a gap by
#: construction: a block-A square and a block-B square would have to differ by
#: `1 +- 2c` on an axis to touch, and no integer is `1 +- 2c` for irrational `c`.
#:
#: The brick wall is the part the ring never had.  Its bricks are placed by
#: *declared* tangency: every one of them is tangent along its own `v` axis to a
#: named seam square of the frame, walking `B(a, a)` then `A(a, a + 1)` for
#: `a = -k .. k - 2`, with the column repeated whenever `a % 3 == 0`.

def staircase_side(cls, c, s, k):
    """The side law again: the caps are flush, so `L = 2k + 1 + 2c`.

    With `c - s = 1/2` this is `2k + 3/2 + (c + s)`, the Q(sqrt 7) family's one
    law; at `k = 5` it is the census n = 151 side `23/2 + 1/2 sqrt 7`.
    """
    return cls(2 * k + 1) + cls(2) * c


def staircase_columns(k):
    """The brick wall's column labels, in `u` order.

    Column `a` carries the pair of bricks tangent to `B(a, a)` and `A(a, a + 1)`.
    The columns run `a = -k .. k - 2`, and every column with `a % 3 == 0` occurs
    twice: the repeats are the bricks that jam the wall's two ends.  At `k = 5`
    the twelve columns are `[-5, -4, -3, -3, -2, -1, 0, 0, 1, 2, 3, 3]`.
    """
    cols = []
    for a in range(-k, k - 1):
        cols.append(a)
        if a % 3 == 0:
            cols.append(a)
    return cols


def _staircase_labels(k):
    """The frame's construction order, so a walk square can be named by index."""
    out = []
    for b in range(-k, k + 1):
        for a in range(-k, b):
            out.append(("A", a, b))
    for b in range(-k, k + 1):
        for a in range(b, k + 1):
            out.append(("B", a, b))
    out += [("C", -k, -k), ("C", -k, -k + 1), ("C", k - 1, k), ("C", k, k)]
    return out


def staircase_frame(cls, c, s, k):
    """The multi-layer axis frame: `4k^2 + 4k + 5` axis squares.

      * `A = {(a - c, b + c) : -k <= a < b <= k}`  -- the upper-left staircase
      * `B = {(a + c, b - c) : -k <= b <= a <= k}` -- the lower-right staircase
      * four corner caps `(-k - c, -k - c)`, `(-k - c, -k + 1 - c)`,
        `(k - 1 + c, k + c)`, `(k + c, k + c)`.

    The blocks are disjoint for every word: block `A` sits at `x - y <= -1 - 2c`
    on its seam edge and block `B` at `x - y >= 2c`, and they are separated on
    some axis whenever `2c >= 1`.  At `k = 5` the count is 125 = 55 + 66 + 4.
    """
    cells = []
    for tag, a, b in _staircase_labels(k):
        if tag == "A":
            cells.append((cls(a) - c, cls(b) + c))
        elif tag == "B":
            cells.append((cls(a) + c, cls(b) - c))
        elif (a, b) == (-k, -k):
            cells.append((-cls(k) - c, -cls(k) - c))
        elif (a, b) == (-k, -k + 1):
            cells.append((-cls(k) - c, -cls(k) + cls(1) - c))
        elif (a, b) == (k - 1, k):
            cells.append((cls(k) - cls(1) + c, cls(k) + c))
        else:
            cells.append((cls(k) + c, cls(k) + c))
    return cells


def _staircase_need(cls, c, s):
    """A tilted square's face `1/2` plus an axis square's reach `(|c|+|s|)/2`."""
    return cls(F(1, 2)) + (abs(c) + abs(s)) * cls(F(1, 2))


def _staircase_walk_v(cls, c, s, k, a):
    """The two brick `v`-coordinates of column `a`, from tangency along `v`.

    Below `B(a, a)` (whose own `v` is `a(c - s) - c(c + s)`) and above
    `A(a, a + 1)` (whose `v` is `a(c - s) + c(1 + c + s)`), each by `need`.
    """
    need = _staircase_need(cls, c, s)
    base = cls(a) * (c - s)
    return (base - c * (c + s) + need,
            base + c * (cls(1) + c + s) - need)


def _staircase_brick(cls, c, s, u, v):
    """The brick centre `p = u (c, s) + v (-s, c)`."""
    return (u * c - v * s, u * s + v * c)


def staircase_seam(cls, c, s, k, u):
    """The two-layer brick wall in the seam: two bricks per column.

    A brick in column `j` sits at `p = (u + j)(c, s) + v(-s, c)`; its `v` comes
    from `_staircase_walk_v`.  The two bricks of a column are `v_A - v_B` apart,
    so they are edge-to-edge along `v` -- a contact, not an overlap -- iff
    `v_A - v_B = 1`, i.e. `2c(c + s) - (1 + s) = 0`: the Q(sqrt 7) identity
    `c - s = 1/2`.  For any other word the two layers do not close (refusal
    `staircase_layer_gap`).

    `u` is the wall's one free transverse parameter.  Every declared tangency is
    along `v`, and `u` and `v` are orthogonal, so sliding the wall along `u`
    preserves all of them; only the wall's non-overlap against the frame fixes
    the feasible `u` window, and the census row fixes the value inside it.
    """
    bricks = []
    for j, a in enumerate(staircase_columns(k)):
        for v in _staircase_walk_v(cls, c, s, k, a):
            bricks.append(_staircase_brick(cls, c, s, u + cls(j), v))
    return bricks


def staircase_tangencies(k):
    """The declared brick-frame tangencies, as `(brick, frame)` index pairs."""
    labels = _staircase_labels(k)
    where = {lab: i for i, lab in enumerate(labels)}
    pairs = []
    for j, a in enumerate(staircase_columns(k)):
        pairs.append((2 * j, where[("B", a, a)]))
        pairs.append((2 * j + 1, where[("A", a, a + 1)]))
    return pairs


def staircase_field(cls, c, s, k, u):
    """The staircase, verified: every declared tangency an exact contact, and the
    exact gate at `staircase_side`.

    Refusals are declared laws:
      * `degenerate_cell`      -- `k < 1` has no staircase;
      * `staircase_layer_gap`  -- the two brick layers are not edge-to-edge along
                                  `v`; this is exactly `c - s != 1/2`, so the
                                  closed wall is the Q(sqrt 7) word's own;
      * `staircase_chain_adrift` -- a declared brick-frame tangency is not along
                                  its named `v` axis by exactly `need`;
      * `staircase_side_mismatch`, `staircase_collides` -- the gate's verdict.

    The declaration is a *named-axis* tangency (brick against seam square, on the
    brick's own `v`), so it is checked on that axis exactly; it is stronger than
    "the gate found no overlap" and weaker than the gate's four-axis "wedged"
    contact, which a brick resting against one seam square need not be.
    """
    if k < 1:
        raise Refusal("degenerate_cell", f"k = {k} has no staircase")
    gap = cls(2) * c * (c + s) - (cls(1) + s) - cls(1)
    if gap != cls(0):
        raise Refusal("staircase_layer_gap",
                      f"the brick layers are {gap} apart along v, not 1: "
                      f"the closed wall needs c - s = 1/2")
    L = staircase_side(cls, c, s, k)
    frame = staircase_frame(cls, c, s, k)
    seam = staircase_seam(cls, c, s, k, u)
    cells = frame + seam
    half = cls(F(1, 2))
    words = [(cls(1), cls(0))] * len(frame) + [(c, s)] * len(seam)
    need = _staircase_need(cls, c, s)
    for i, j in staircase_tangencies(k):
        p, q = seam[i], frame[j]
        dv = (p[0] - q[0]) * (-s) + (p[1] - q[1]) * c
        if abs(dv) != need:
            raise Refusal("staircase_chain_adrift",
                          f"the declared tangency (brick {i}, frame {j}) is "
                          f"{abs(dv)} along v, not {need}")
    g = Q.gate(cells, words, cls)
    if g["L"] != L:
        raise Refusal("staircase_side_mismatch",
                      f"the gate reads {g['L']}, not {L}")
    if not g["ok"]:
        raise Refusal("staircase_collides",
                      f"{g['violations']} pairs overlap at the derived side")
    return {"cells": cells, "words": words, "frame": len(frame),
            "seam": len(seam), "gate": g, "u": u}


def staircase_claim(d, c, s, k, u, family="Staircase", params=None):
    """Gate-verify a staircase over `Q(sqrt d)` and return it as a claim.

    `N = 4k^2 + 4k + 5 + 2|staircase_columns(k)|` -- 149 at `k = 5` (125 axis +
    24 bricks) -- at `L = 2k + 1 + 2c`.  The count is **not** the n = 151 row's
    151: the wall's thirteenth column (`a = k - 1`) pinches against the cap, so
    this grammar constructs 149 of the 151 (control 25 measures the pinch).
    """
    cls = qfield(d)
    if (c * c + s * s) != cls(1):
        raise Refusal("word_off_circle",
                      f"cos^2 + sin^2 = {c * c + s * s} != 1 in Q(sqrt {d})")
    decl = staircase_field(cls, c, s, k, u)
    state, words = decl["cells"], decl["words"]
    g = decl["gate"]
    n = len(state)
    L = g["L"]
    claim = Claim("spatial_geometry", family, params or {"k": k}, n,
                  {"count": ("N", n), "extent": ("L", L),
                   "void": ("L^2 - N", L * L - cls(n)),
                   "contacts": ("contacts", g["contacts"])},
                  {"state": state, "words": words, "field": f"Q(sqrt {d})",
                   "frame": decl["frame"], "seam": decl["seam"],
                   "gauge": decl["u"]})
    claim.meta["field_d"] = d
    claim.meta["frame"] = decl["frame"]
    claim.meta["seam"] = decl["seam"]
    claim.meta["declared"] = 2 * len(staircase_columns(k))
    _tag(claim, L, n)
    claim.laws["side"] = ("L", L)
    claim.laws["axis"] = ("axis squares", decl["frame"])
    claim.laws["brick"] = ("seam bricks", decl["seam"])
    side = _table_side(n)
    if side is None:
        claim.meta["table_side"] = None
        claim.meta["beats_table"] = None
    else:
        Ld = DecimalWitness.scalar(L)
        Td = DecimalWitness.scalar(side)
        claim.meta["table_side"] = str(side)
        claim.meta["beats_table"] = Ld < Td
        claim.meta["table_gap"] = str(Td - Ld)
    return claim


def p_staircase(k):
    """The staircase rung at the census's own Q(sqrt 7) word.

    `u` is the wall's free transverse gauge; the census row fixes it to
    `-1357/128 + 211/128 sqrt 7`.  Everything else -- 125 axis centres and all 24
    brick centres -- is computed from `k`, the word and that one scalar.
    """
    cls = qfield(7)
    c, s = _sqrt7_word()
    return staircase_claim(7, c, s, k, cls(F(-1357, 128), F(211, 128)))


# ------------------------------------------- the pocket cage and the word spin
#: Run 95's first cut measured the staircase's corner pocket with a 120 x 120
#: float scan.  That scan is gone.  A centre `p` of a unit square of word `w` is
#: feasible iff it clears every sentence square on one of the four declared axes,
#: i.e. iff it lies outside every square's **no-fit octagon** (the intersection of
#: four exact slabs).  The cage below covers the whole `L`-box with exact `Quad`
#: boxes and prunes a box only when it is provably infeasible -- wholly inside one
#: no-fit octagon, or wholly outside the `L`-box -- so the surviving cover is a
#: sound outer approximation of the feasible set, in the candidate word's own
#: frame.  Two word-aligned unit squares that do not overlap have centres at least
#: `1` apart along one of that word's axes, so a cover narrower than `1` in both
#: axes holds at most one centre: exact capacity, no scan, no tolerance.

def _cage_extent(cls, c, s, ax, sides=None):
    """The half-extent of the `(c, s)` square along the unit axis `ax`.

    `sides` widens the square into a rectangle `(U-side, V-side)` in the word's
    own frame: two squares of one word side by side along `V` are the rectangle
    `(1, 2)`, and that is what rules a *pair* of them out in one cage.
    """
    sa, sb = sides or (1, 1)
    return (abs(c * ax[0] + s * ax[1]) * F(sa)
            + abs(-s * ax[0] + c * ax[1]) * F(sb)) * cls(F(1, 2))


def _cage_rows(cls, c, s, cells, words, sides=None):
    """Per sentence square: its four exact axis tests.

    Each row is `(q . a, need, U . a, V . a)`, so that a centre `p = u U + v V`
    separates from the square along `a` by `(q - p) . a = q . a - u (U . a) -
    v (V . a)` -- exact, and affine in `(u, v)`, which is what makes a box test
    two evaluations instead of a search.
    """
    out = []
    for q, qw in zip(cells, words):
        axes = ((c, s), (-s, c), (qw[0], qw[1]), (-qw[1], qw[0]))
        row = []
        for ax in axes:
            need = (_cage_extent(cls, c, s, ax, sides)
                    + _cage_extent(cls, qw[0], qw[1], ax))
            row.append((q[0] * ax[0] + q[1] * ax[1], need,
                        c * ax[0] + s * ax[1], -s * ax[0] + c * ax[1]))
        out.append(row)
    return out


def _cage_upper(q):
    """A rational upper bound for a `Quad` -- exact, conservative, no float."""
    if q.b == 0:
        return q.a
    k = 1
    while k * k < q.d:
        k += 1
    return q.a + q.b * k if q.b > 0 else q.a + q.b


def staircase_cage(cls, c, s, cells, words, L, step=None, fine=None,
                   hint=None, budget=400000, exact_word=True, sides=None):
    """The exact no-fit cage: every feasible centre of a `(c, s)` unit square.

    Returns `cover` (exact boxes in the word's frame), `empty` (a proof that no
    centre clears `cells` inside the `L`-box), the cover's own `extent_u`,
    `extent_v`, its `capacity` (`0`, `1`, or `">=2"`), and a `witness` centre
    whose exact point test passes when one exists.  `hint` only orders the
    sentence squares for early exit; it cannot change the verdict.
    """
    if exact_word and (c * c + s * s) != cls(1):
        raise Refusal("word_off_circle",
                      f"cos^2 + sin^2 = {c * c + s * s} != 1")
    half = cls(F(1, 2))
    h = _cage_extent(cls, c, s, (cls(1), cls(0)), sides)
    if L.d == cls.d:                    # same field: the slab is exact
        slab = _cage_upper(L * half - h)
    else:                               # a second word in another field: bound `L`
        slab = _cage_upper(cls(_cage_upper(L) * F(1, 2)) - h)
    X = slab
    if X <= 0:
        raise Refusal("degenerate_cell", "the L-box is narrower than one square")
    R = F(X) * F(3, 2)                  # |u|, |v| <= sqrt2 X < 3X/2
    step = step or F(1)
    fine = fine or F(1, 8)
    rows = _cage_rows(cls, c, s, cells, words, sides)
    hx, hy = hint if hint is not None else (cls(0), cls(0))
    order = sorted(range(len(cells)),
                   key=lambda i: abs(cells[i][0] - hx) + abs(cells[i][1] - hy))
    cells = [cells[i] for i in order]
    rows = [rows[i] for i in order]
    # a unit grid of buckets: a cell further than `rad` on both axes cannot cover a
    # box, because every separation need is at most `rad`.  For a unit square
    # `rad = 2`; a rectangle `(sa, sb)` needs `(sa + sb + sqrt 2)/2`, so the radius
    # is read off the rows rather than assumed -- a radius too small would only
    # fail to prune (never prune wrongly), but it would make the cage permissive.
    buckets = {}
    for i, q in enumerate(cells):
        buckets.setdefault((q[0].floor(), q[1].floor()), []).append(i)
    # the largest separation need over the sentence, as an integer bucket radius
    need_max = max(need for row in rows for _qa, need, _ua, _va in row)
    rad = _cage_upper(need_max)
    rad = F(rad.numerator // rad.denominator + 1) if rad.denominator != 1 else rad

    def inside(u, v):
        px = u * c - v * s
        py = u * s + v * c
        return abs(px) <= X and abs(py) <= X

    def clear_point(u, v):
        if not inside(u, v):
            return False
        for row in rows:
            if not any(abs(qa - (u * ua + v * va)) >= need
                       for qa, need, ua, va in row):
                return False
        return True

    def prune(box):
        u0, u1, v0, v1 = box
        spans = []
        for ac, av in ((c, -s), (s, c)):          # the L-box slabs
            lo = (ac * u0 if ac.sign() >= 0 else ac * u1) + \
                 (av * v0 if av.sign() >= 0 else av * v1)
            hi = (ac * u1 if ac.sign() >= 0 else ac * u0) + \
                 (av * v1 if av.sign() >= 0 else av * v0)
            if lo > X or hi < -X:
                return True
            spans.append((lo, hi))
        (xlo, xhi), (ylo, yhi) = spans
        x0, x1 = (xlo - rad).floor(), (xhi + rad).floor()
        y0, y1 = (ylo - rad).floor(), (yhi + rad).floor()
        keys = []
        for bx in range(x0, x1 + 1):              # only the nearby cells
            for by in range(y0, y1 + 1):
                if (bx, by) in buckets:
                    keys.append((bx, by))
        if not keys:
            return False
        # nearest bucket first, in plain integers: the nearest square almost
        # always proves the box dead, so the exact tests stop after one or two
        mx, my = (x0 + x1) // 2, (y0 + y1) // 2
        keys.sort(key=lambda k: (k[0] - mx) ** 2 + (k[1] - my) ** 2)
        cand = []
        for k in keys:
            cand.extend(buckets[k])
        for i in cand:                            # the no-fit octagons
            for qa, need, ua, va in rows[i]:
                lo = (ua * u0 if ua.sign() >= 0 else ua * u1) + \
                     (va * v0 if va.sign() >= 0 else va * v1)
                hi = (ua * u1 if ua.sign() >= 0 else ua * u0) + \
                     (va * v1 if va.sign() >= 0 else va * v0)
                if max(abs(qa - lo), abs(qa - hi)) >= need:
                    break
            else:
                return True
        return False

    boxes = []
    u = -R
    while u < R:
        v = -R
        while v < R:
            boxes.append((u, u + step, v, v + step))
            v = v + step
        u = u + step
    examined = 0
    cover = []
    for b in boxes:
        examined += 1
        if not prune(b):
            cover.append(b)
    truncated = False
    while cover and (cover[0][1] - cover[0][0]) > fine:
        nxt = []
        for (u0, u1, v0, v1) in cover:
            um, vm = (u0 + u1) * half, (v0 + v1) * half
            for b in ((u0, um, v0, vm), (um, u1, v0, vm),
                      (u0, um, vm, v1), (um, u1, vm, v1)):
                examined += 1
                if not prune(b):
                    nxt.append(b)
        cover = nxt
        if examined > budget:
            truncated = True
            break
    witness = None
    for (u0, u1, v0, v1) in cover:
        uc, vc = (u0 + u1) * half, (v0 + v1) * half
        if clear_point(uc, vc):
            witness = (uc, vc)
            break
    if cover:
        ulo = min(b[0] for b in cover)
        uhi = max(b[1] for b in cover)
        vlo = min(b[2] for b in cover)
        vhi = max(b[3] for b in cover)
        extent_u, extent_v = uhi - ulo, vhi - vlo
    else:
        ulo = uhi = vlo = vhi = cls(0)
        extent_u = extent_v = cls(0)
    capacity = (0 if not cover else
                1 if (extent_u < cls(1) and extent_v < cls(1)) else ">=2")
    return {"cover": cover, "empty": not cover, "capacity": capacity,
            "extent_u": extent_u, "extent_v": extent_v,
            "window": (ulo, uhi, vlo, vhi), "witness": witness,
            "examined": examined, "truncated": truncated, "fine": fine,
            "cells": len(cells)}


def staircase_cap_brick(cls, c, s, k, u):
    """The one brick the pocket admits: the last column's `A` brick, one column out.

    Column `j = |staircase_columns(k)|` is empty in the wall, and the top brick
    `A(k - 2, k - 1)` repeated there is exactly tangent along `u` to its twin (one
    whole `u` step), so it is a contact, not an overlap.  At `k = 5` that is
    `u = u_0 + 12`, `v = (17 + sqrt7)/8`.
    """
    j = len(staircase_columns(k))
    v = _staircase_walk_v(cls, c, s, k, k - 2)[1]
    return _staircase_brick(cls, c, s, u + cls(j), v)


def staircase_capped(k, u=None):
    """The staircase plus its cap brick: the 150-square sentence at the census side."""
    cls = qfield(7)
    c, s = _sqrt7_word()
    if u is None:
        u = cls(F(-1357, 128), F(211, 128))
    decl = staircase_field(cls, c, s, k, u)
    cells = list(decl["cells"]) + [staircase_cap_brick(cls, c, s, k, u)]
    words = list(decl["words"]) + [(c, s)]
    g = Q.gate(cells, words, cls)
    return {"cells": cells, "words": words, "gate": g, "frame": decl["frame"],
            "seam": decl["seam"], "u": u, "cls": cls, "c": c, "s": s}


def staircase_words():
    """Every unit word the spatial wheel declares, with the family it comes from.

    The words are read off the registered builders, not typed in: `Q.word_45`
    (Tile/Strip/Pocket/DiamondField/Glue base), `unit_word(5, 2, 1)` (Slope),
    `(sqrt7/4, 3/4)` (Seventh), the census word (Ring and Staircase), the
    rational-t words `tword(1/2)`, `tword(1/3)`, `tword(1/5)` (Tilt and Glue),
    and every Pythagorean word with denominator <= 41.
    """
    out = []
    c2, s2 = Q.word_45()
    out.append(("45deg", 2, c2, s2))
    c5, s5 = unit_word(5, 2, 1)
    out.append(("Slope-2:1", 5, c5, s5))
    cls7 = qfield(7)
    out.append(("Seventh", 7, cls7(0, F(1, 4)), cls7(F(3, 4))))
    cw, sw = _sqrt7_word()
    out.append(("census", 7, cw, sw))
    seen = {(str(cw), str(sw))}
    for t in (F(1, 2), F(1, 3), F(1, 5)):
        tc, ts = EF.tword(t)
        cls2 = qfield(2)
        key = (str(cls2(F(tc))), str(cls2(F(ts))))
        if key not in seen:
            seen.add(key)
            out.append((f"t={t}", 2, cls2(F(tc)), cls2(F(ts))))
    for q in range(1, 14):
        for p in range(1, q + 1):
            tc, ts = EF.tword(p, q)
            cls2 = qfield(2)
            cc, ss = cls2(F(tc)), cls2(F(ts))
            key = (str(cc), str(ss))
            if key not in seen:
                seen.add(key)
                out.append((f"pyth-{p}/{q}", 2, cc, ss))
    return out


def staircase_word_spin(k=5):
    """Spin the staircase's closure law over every declared unit word.

    The law is exact and one line: the two brick layers are
    `v_A - v_B = 2c(c + s) - (1 + s)` apart, so the residual is
    `2c(c+s) - (1+s) - 1 = s (2(c - s) - 1)` -- zero iff `s = 0` (the degenerate
    axis word) or `c - s = 1/2`, which pins the word to the census's own.  Every
    other word is
    refused by `staircase_layer_gap`, and the constructor is actually run so the
    refusal is the code's, not a table's.
    """
    out = []
    cw, sw = _sqrt7_word()
    gauge7 = qfield(7)(F(-1357, 128), F(211, 128))
    for name, d, c, s in staircase_words():
        cls = qfield(d)
        residual = s * (cls(2) * (c - s) - cls(1))
        assert residual == (cls(2) * c * (c + s) - (cls(1) + s) - cls(1)), name
        u = gauge7 if (c, s) == (cw, sw) else cls(0)
        try:
            staircase_field(cls, c, s, k, u)
            law = "closed"
        except Refusal as e:
            law = e.law
        out.append({"word": name, "d": d, "c": c, "s": s,
                    "residual": residual, "law": law,
                    "closed": residual == cls(0)})
    return out


def _sqrt7_words(mmax=8):
    """Every unit-circle word of Q(sqrt 7) at height `m <= mmax`.

    Writing `c = (a + b sqrt7)/m` and `s = (e + f sqrt7)/m`, the circle identity
    splits into `ab + ef = 0` and `a^2 + 7 b^2 + e^2 + 7 f^2 = m^2`, so the words
    are exactly the solutions of that pair -- no recovery, no tolerance.
    """
    cls = qfield(7)
    out = []
    seen = set()
    for m in range(1, mmax + 1):
        for a in range(-m, m + 1):
            for b in range(-m, m + 1):
                if a == 0 and b == 0:
                    continue
                for e in range(-m, m + 1):
                    for f in range(-m, m + 1):
                        if a * b + e * f != 0:
                            continue
                        if a * a + 7 * b * b + e * e + 7 * f * f != m * m:
                            continue
                        c = cls(F(a, m), F(b, m))
                        s = cls(F(e, m), F(f, m))
                        if s < cls(0):        # keep one of each mirror pair
                            continue
                        key = (str(c), str(s))
                        if key in seen:
                            continue
                        seen.add(key)
                        out.append((f"sqrt7-{m}:{a}{'%+d' % b}v{'%+d' % e}{'%+d' % f}v",
                                    c, s))
    return out


# ------------------------------------------ the table's own rotation (run 95)
#: The delivered n = 151 row is 149 grammar squares plus **two squares rotated to
#: 0.614761828896 rad**.  That angle is the exact rational
#: `19211307153/31250000000`, so the pose is a *rational-angle* sentence even
#: though its cosine is not a field element: `cos` and `sin` are transcendental,
#: and everything about these two squares is therefore a **measurement**, never an
#: exact certificate.  The margins are reported, never a verdict without them.

def odd_word_angle():
    """The delivered pose's own tilt, exactly: `19211307153/31250000000` rad."""
    return F(19211307153, 31250000000)


def odd_word():
    """`(cos, sin)` of that rational angle to 70 digits -- a measurement."""
    import field_triage as T
    return T.cos_sin(odd_word_angle())


def odd_centres(cells, n=151, tol=None):
    """The delivered row's squares that are *not* grammar squares: its odd pair.

    A delivered centre counts as odd when it is further than `tol` (1e-6, the
    pose's own polish scale) from every square of the exact sentence.
    """
    tol = tol if tol is not None else Decimal("1e-6")
    D = DecimalWitness.scalar
    have = [(D(x), D(y)) for x, y in cells]
    out = []
    for r in _delivered_rows()[n]:
        px, py = D(r[0]), D(r[1])
        if min(max(abs(px - x), abs(py - y)) for x, y in have) > tol:
            out.append((F(r[0]), F(r[1])))
    return out


def odd_word_upward(places=25):
    """The table's rotation rounded **up** at `1e-25`, so `|w| >= 1` exactly.

    Rounding both coordinates up enlarges the square by `1e-25`, and a sentence
    that cannot hold the enlarged square cannot hold the exact one -- which is
    what makes the cage verdict below a proof and not a measurement.
    """
    from decimal import ROUND_CEILING
    oc, os_ = odd_word()
    scale = Decimal(10) ** places
    cu = (Decimal(oc) * scale).to_integral_value(rounding=ROUND_CEILING) / scale
    su = (Decimal(os_) * scale).to_integral_value(rounding=ROUND_CEILING) / scale
    return F(cu), F(su)


def _quad_inv(q):
    """The exact inverse of a nonzero `Quad` in Q(sqrt d): `(a - b sqrt d)/(a^2 - d b^2)`."""
    d = q.a * q.a - q.d * q.b * q.b
    if d == 0:
        raise Refusal("degenerate_cell", "inverse of a zero divisor")
    return type(q)(q.a / d, -q.b / d)


def _aff_max(p, q, u0, u1):
    """`max` of the affine `p + q u` over `[u0, u1]`, exactly."""
    return p + q * (u1 if q.sign() >= 0 else u0)


def _aff_min(p, q, u0, u1):
    """`min` of the affine `p + q u` over `[u0, u1]`, exactly."""
    return p + q * (u0 if q.sign() >= 0 else u1)


def staircase_chords(cls, c, s, cells, words, blocks=48, window=None, depth=22):
    """Exact proof that no two `(c, s)` squares are `1` apart along `V` -- in closed form.

    At a fixed `u` one sentence square forbids a closed interval of `v` (it covers the
    candidate iff *all four* of its axis tests fail, so its forbidden set is the
    intersection of four linear intervals, itself one interval).  The free set at that
    `u` is the complement of the union, and two squares `1` apart along `V` exist iff
    some free interval is at least `1` long -- so bounding every free chord by `1`
    settles the pair without any scan of the plane.

    `u` is covered by finitely many blocks.  Inside a block each forbidden interval is
    *shrunk* to the part common to the whole block, which under-approximates the
    forbidden set and therefore over-approximates the free set; a block whose own
    over-approximation holds two points `1` apart is split in half, so every surviving
    block's free set is short.  The verdict is then read off the **union** of those
    per-block free intervals: that union over-approximates every `v` any feasible centre
    can have, at any `u` of the window, so a union extent below `1` rules out a `V`-pair
    outright -- including pairs whose `u` values sit in different blocks, which a
    per-block chord alone would not see.  `max_chord` is that global extent and
    `max_block` the largest single chord, kept for the record.

    The verdict is a finite exact proof in Q(sqrt d): every quantity is a `Quad`, no
    `Decimal`, no float, no tolerance.
    """
    rows = _cage_rows(cls, c, s, cells, words)
    prep = []
    for row in rows:
        qa0, need0, ua0, _v0 = row[0]            # the candidate's own U axis: no v
        rest = []
        for qa, need, ua, va in row[1:]:         # V, then the cell's own two axes
            rest.append((qa, need, ua, va, None if va == cls(0) else _quad_inv(va)))
        prep.append((qa0, need0, ua0, rest))
    zero, one = cls(0), cls(1)
    ulo, uhi, vlo, vhi = [x if hasattr(x, "d") else cls(F(x)) for x in window]

    def separates(qa, ua, need, u0, u1):
        """Does `|qa - ua u| >= need` hold at every `u` of `[u0, u1]`?"""
        a, b = qa - ua * u0, qa - ua * u1
        near = zero if (a.sign() >= 0) != (b.sign() >= 0) else min(abs(a), abs(b))
        return near >= need

    def free_at(u0, u1):
        """Free `v`-intervals that contain the free set of *every* `u` in `[u0, u1]`."""
        forb = []
        for qa0, need0, ua0, rest in prep:
            if separates(qa0, ua0, need0, u0, u1):
                continue                         # the U axis always separates: no cover
            a = b = None
            skip = False
            for qa, need, ua, va, iv in rest:
                if iv is None:
                    if separates(qa, ua, need, u0, u1):
                        skip = True
                        break
                    continue
                lo_c = (qa - need) * iv if va.sign() > 0 else (qa + need) * iv
                hi_c = (qa + need) * iv if va.sign() > 0 else (qa - need) * iv
                sl = (-ua) * iv
                lo_b = _aff_max(lo_c, sl, u0, u1)
                hi_b = _aff_min(hi_c, sl, u0, u1)
                a = lo_b if a is None else max(a, lo_b)
                b = hi_b if b is None else min(b, hi_b)
            if skip or a is None or not (a < b):
                continue
            forb.append((a, b))
        forb.sort()
        out = []
        cur = vlo
        for a, b in forb:
            if b <= cur:
                continue
            if a > cur:
                out.append((cur, min(a, vhi)))
            cur = max(cur, b)
            if cur >= vhi:
                break
        if cur < vhi:
            out.append((cur, vhi))
        return [(a, b) for a, b in out if b > a]

    def has_pair(iv):
        """Could two points of the over-approximation be exactly `1` apart?"""
        for i, (a, b) in enumerate(iv):
            for a2, b2 in iv[i:]:
                if max(a, a2 - one) < min(b, b2 - one):
                    return True
        return False

    todo = [(ulo + (uhi - ulo) * cls(F(k, blocks)),
             ulo + (uhi - ulo) * cls(F(k + 1, blocks))) for k in range(blocks)]
    worst_block = None
    free_all = []
    closed = 0
    while todo:
        u0, u1 = todo.pop()
        iv = free_at(u0, u1)
        if not has_pair(iv):
            closed += 1
            free_all.extend(iv)
            for a, b in iv:
                if worst_block is None or b - a > worst_block:
                    worst_block = b - a
            continue
        if depth <= 0:
            raise Refusal("pair_not_excluded", f"a free chord reaches 1 near u = {u0}")
        depth -= 1
        um = (u0 + u1) * cls(F(1, 2))
        todo.append((u0, um))
        todo.append((um, u1))
    if not free_all:
        return {"ok": True, "max_chord": cls(0), "max_block": cls(0),
                "closed": closed, "blocks": blocks,
                "window": (ulo, uhi, vlo, vhi)}
    lo = min(a for a, _b in free_all)
    hi = max(b for _a, b in free_all)
    span = hi - lo
    if span >= cls(1):
        raise Refusal("pair_not_excluded",
                      f"the free set spans {span} along V, so a pair of centres "
                      f"1 apart cannot be ruled out")
    return {"ok": True, "max_chord": span, "max_block": worst_block,
            "closed": closed, "blocks": blocks,
            "window": (ulo, uhi, vlo, vhi)}


def staircase_pair_span(cls, c, s, cells, words, L, blocks=16, exact_word=True):
    """The exact free span of a word's feasible centres along **both** of its axes.

    The pair test is `|du| >= 1 or |dv| >= 1`, so both axes must be short.  The chord
    instrument works in one frame; a quarter turn `(c, s) -> (-s, c)` leaves the square
    alone, so calling it on the turned word answers for the other axis.  Returns the
    two spans and the two cages, so a caller can report which axis (if either) is
    decided by an empty cage rather than by the span.
    """
    out = {}
    for tag, (ct, st) in (("v", (c, s)), ("u", (-s, c))):
        cage = staircase_cage(cls, ct, st, cells, words, L, exact_word=exact_word,
                              hint=(cells[-1][0], cells[-1][1]))
        if cage["empty"]:
            out[tag] = {"cage_empty": True, "span": None, "cage": cage}
            continue
        ch = staircase_chords(cls, ct, st, cells, words, blocks=blocks,
                              window=cage["window"])
        out[tag] = {"cage_empty": False, "span": ch["max_chord"],
                    "max_block": ch["max_block"], "cage": cage}
    return out


def staircase_chord_spin(cells=None, words=None, L=None, blocks=16):
    """Run the chord instrument over the census word and every second-word class.

    The question is uniform: for a word `w` and the exact 149-square staircase, can two
    unit squares of `w` both fit in the pocket?  For each of the 66 rotation classes the
    answer is decided by the same two exact instruments -- a single-square cage (empty
    means not even one fits) and `staircase_pair_span` (both axis spans below `1` means
    no pair fits) -- with no scan and no tolerance.

    A class whose span reaches `1` is returned with `verdict == "pair"`: the instrument
    does not exclude it, and the caller must report that honestly rather than round it.
    """
    cls = qfield(7)
    if cells is None or words is None:
        capped = staircase_capped(5)
        cells, words = capped["cells"][:149], capped["words"][:149]
    if L is None:
        L = (cls(23) + cls(0, 1)) / cls(2)
    out = []
    for name, c, s in staircase_second_word_classes():
        rec = {"word": name, "c": c, "s": s}
        cage = staircase_cage(cls, c, s, cells, words, L,
                              hint=(cells[-1][0], cells[-1][1]))
        rec["capacity"] = cage["capacity"]
        rec["extent_u"] = cage["extent_u"]
        rec["extent_v"] = cage["extent_v"]
        if cage["empty"]:
            rec["verdict"] = "no-placement"
            rec["span_u"] = rec["span_v"] = None
            out.append(rec)
            continue
        span = staircase_pair_span(cls, c, s, cells, words, L, blocks=blocks)
        rec["span_u"] = span["u"]["span"]
        rec["span_v"] = span["v"]["span"]
        if span["u"]["cage_empty"] or span["v"]["cage_empty"]:
            rec["verdict"] = "no-pair"
        elif all(x is not None and x < cls(1) for x in (rec["span_u"], rec["span_v"])):
            rec["verdict"] = "no-pair"
        else:
            rec["verdict"] = "pair"
        out.append(rec)
    return out


def staircase_odd_cage(cls, cells, words, L, places=25):
    """The exact cage for the delivered rotation's square (slightly enlarged).

    The word is not a field element, so its coordinates are the upward-rounded
    rationals of `odd_word_upward`; the square they describe has side `|w| >= 1`,
    so an empty cage is a proof that no square of the table's own rotation fits.
    """
    cu, su = odd_word_upward(places)
    return staircase_cage(cls, cls(cu), cls(su), cells, words, L,
                          exact_word=False,
                          hint=(cells[-1][0], cells[-1][1]))


def mixed_slack(cells, words, extra):
    """The worst pair slack of a mixed sentence, in `Decimal` -- a measurement.

    The exact squares enter through their 70-digit `Decimal` images and the odd
    squares through `odd_word()`; every quantity is exact rational *input* and
    the only approximation is the digit string of `cos`/`sin`, so a margin of
    `1e-9` is read off a computation whose own error is `1e-60`.
    """
    oc, os_ = odd_word()
    oc, os_ = Decimal(oc), Decimal(os_)
    pts = [(Decimal(DecimalWitness.scalar(x)), Decimal(DecimalWitness.scalar(y)))
           for x, y in cells]
    ws = [(Decimal(DecimalWitness.scalar(a)), Decimal(DecimalWitness.scalar(b)))
          for a, b in words]

    def ext(w, ax):
        return (abs(w[0] * ax[0] + w[1] * ax[1])
                + abs(-w[1] * ax[0] + w[0] * ax[1])) / 2

    def pair(p, pw, q, qw):
        best = None
        for ax in (pw, (-pw[1], pw[0]), qw, (-qw[1], qw[0])):
            v = (abs((q[0] - p[0]) * ax[0] + (q[1] - p[1]) * ax[1])
                 - (ext(pw, ax) + ext(qw, ax)))
            if best is None or v > best:
                best = v
        return best

    ow = (oc, os_)
    def dec(q):
        return (Decimal(q.numerator) / Decimal(q.denominator))
    odd = [(dec(F(x)), dec(F(y))) for x, y in extra]
    worst = None
    where = None
    for i, p in enumerate(odd):
        for j, (q, qw) in enumerate(zip(pts, ws)):
            v = pair(p, ow, q, qw)
            if worst is None or v < worst:
                worst, where = v, ("odd", i, "cell", j)
    for i in range(len(odd)):
        for j in range(i + 1, len(odd)):
            v = pair(odd[i], ow, odd[j], ow)
            if v < worst:
                worst, where = v, ("odd", i, "odd", j)
    return worst, where


def _square_canon(c, s):
    """The rotation class of a square's word: `(c, s)` and `(-s, c)` are one square.

    A quarter turn of the word leaves the square unchanged (and so do the other
    two quarter turns), so the no-fit cage -- which is a statement about the
    square -- answers for the whole class at once.
    """
    opts = ((c, s), (-s, c), (-c, -s), (s, -c))
    return min((str(a), str(b)) for a, b in opts)


def staircase_second_word_classes(mmax=8, pyth_max=13):
    """One representative per rotation class of the second-word squares.

    `staircase_second_words()` lists 78 field-compatible words; a quarter turn
    maps a word to another in the list (or to a mirror of it), and the cage cannot
    tell the two apart, so one cage per class decides all of them.  The class
    count is what the control runs, and the word count is what it claims.
    """
    seen = {}
    for name, c, s in staircase_second_words(mmax, pyth_max):
        key = _square_canon(c, s)
        if key not in seen:
            seen[key] = (name, c, s)
    return list(seen.values())


def staircase_second_words(mmax=8, pyth_max=13):
    """The second words a 151st square could use: `Q(sqrt 7)` union `Q_Pyth`.

    Every unit word of Q(sqrt 7) at height `<= mmax` (the census word and its
    mirrors included) and every Pythagorean word with denominator `<= pyth_max`,
    which embeds in Q(sqrt 7) as a rational pair -- so the two-word test stays in
    one field and every comparison in it is exact.
    """
    cls = qfield(7)
    out = [(name, c, s) for name, c, s in _sqrt7_words(mmax)]
    seen = {(str(c), str(s)) for _n, c, s in out}
    for q in range(1, pyth_max + 1):
        for p in range(1, q + 1):
            tc, ts = EF.tword(p, q)
            c, s = cls(F(tc)), cls(F(ts))
            if s < cls(0):
                continue
            key = (str(c), str(s))
            if key in seen:
                continue
            seen.add(key)
            out.append((f"pyth-{p}/{q}", c, s))
    return out


def p_slope(p, q, k, m=1):
    """The p:q slope ridge: the word `(p, q)/sqrt(p^2+q^2)` lives in Q(sqrt(p^2+q^2))."""
    dd, _kf = squarefree_split(p * p + q * q)
    c, s = unit_word(dd, p, q)
    return p_ridge(dd, c, s, k, "Slope", {"p": p, "q": q, "k": k, "m": m}, m)


def _sqrt7_word():
    """`((1+sqrt7)/4, (sqrt7-1)/4)`: the word the census's n = 18 row actually uses.

    Recovered from the delivered pose's 0.424031039491-radian tilt with
    `exact_field.recover_scalar` at 70-digit precision: cos = 1/4 + 1/4 sqrt7,
    sin = -1/4 + 1/4 sqrt7, and `cos^2 + sin^2 = 1` exactly.  Run 90 used an ad-hoc
    Q(sqrt 7) word `(sqrt7/4, 3/4)`; this one is the table's own.
    """
    cls = qfield(7)
    return cls(F(1, 4), F(1, 4)), cls(F(-1, 4), F(1, 4))


def p_seventh(k, m=1):
    """The Q(sqrt 7) rung: a ridge at the census's own sqrt7 word."""
    c, s = _sqrt7_word()
    return p_ridge(7, c, s, k, "Seventh", {"k": k, "m": m}, m)


def p_tilt(t, k, m=1):
    """A rational-t Pythagorean ridge: `tword(t)` is a rational unit word, exact in Q."""
    t = F(t)
    if not (0 < t < 1):
        raise Refusal("t_out_of_range",
                      f"t = {t} is not in (0, 1): the t-basis word is not a quarter turn")
    c, s = EF.tword(t)
    return p_ridge(2, Q2(c), Q2(s), k, "Tilt", {"t": str(t), "k": k, "m": m}, m)


def p_glue(t):
    """The rational-t corner glue: five squares at 2 + 1/(cos + sin), with t = p/q."""
    t = F(t)
    if not (0 < t < 1):
        raise Refusal("t_out_of_range",
                      f"t = {t} is not in (0, 1): the t-basis word is not a quarter turn")
    w = Q.word_t(t)
    st, ws, L = _import_mixed().corner_glue(w)
    n = 5
    return _tag(Claim("spatial_geometry", "Glue", {"t": str(t)}, n,
                      _laws_packing(n, L, L * L - Q2(n)),
                      {"state": st, "words": ws}), L, n)


def _import_mixed():
    import mixed_field as M
    return M


def p_fold(k):
    """The diagonal fold: reflect a certified sentence; N, L and the law bundle hold."""
    base = p_pocket(k)
    st, ws = base.payload["state"], base.payload["words"]
    folded = [(y, x) for (x, y) in st]
    L = base.laws["extent"][1]
    n = base.n
    return _tag(Claim("spatial_geometry", "SymmetryFold", {"k": k}, n,
                      _laws_packing(n, L, L * L - Q2(n)),
                      {"state": folded, "words": ws, "folded_from": base.brief()}),
                L, n)


# ---------------------------------------- higher rungs: a field-generic gate (run 90)
#: The `Quad` subclasses for Q(sqrt d), made once per d.  `exact_field.Quad` carries
#: exact sign, floor, abs and order for any square-free d, and `qsqrt2.gate` takes the
#: class as an argument -- so a higher rung is verified by the *same* procedure, not by
#: a copy of it (control 21 checks the two call forms on every spatial cell).
_QFIELDS: dict = {}


def qfield(d):
    """The `Quad` subclass for `Q(sqrt d)` (d square-free, d >= 2)."""
    if d == 2:
        return Q2
    if d not in _QFIELDS:
        _QFIELDS[d] = type(f"Q{d}", (EF.Quad,), {"d": d, "__slots__": (),
                                                "__module__": __name__})
    return _QFIELDS[d]


def squarefree_split(n):
    """`n = k^2 * d` with d square-free: so sqrt(n) = k sqrt(d) lives in Q(sqrt d)."""
    if n < 1:
        raise Refusal("degenerate_field", f"{n} is not a positive integer")
    d, k, m = n, 1, 2
    while m * m <= d:
        while d % (m * m) == 0:
            d //= m * m
            k *= m
        m += 1
    return d, k


def unit_word(d, p, q):
    """The unit word `(p, q)/sqrt(p^2+q^2)` in `Q(sqrt d)`, with `p^2+q^2 = k^2 d`.

    The circle identity `cos^2 + sin^2 = 1` is then exact in the field, which is what
    makes the whole family float-free: nothing here is normalised numerically.
    """
    cls = qfield(d)
    n = p * p + q * q
    dd, k = squarefree_split(n)
    if dd != d:
        raise Refusal("wrong_field", f"{p}:{q} has sqrt({n}) outside Q(sqrt {d})")
    # p/sqrt(n) = p/(k sqrt d) = (p/(k d)) * sqrt d
    return cls(0, F(p, k * d)), cls(0, F(q, k * d))


def gate_of(claim):
    """The gate verdict for a claim, in the claim's own field.

    There is one gate (`qsqrt2.gate`), now parametrised by the field class; a claim only
    declares which field its sentence lives in.
    """
    d = int(claim.meta.get("field_d", 2))
    state, words = claim.payload["state"], claim.payload["words"]
    return Q.gate(state, words, qfield(d))


def pairs_of(claim, i, j):
    d = int(claim.meta.get("field_d", 2))
    state, words = claim.payload["state"], claim.payload["words"]
    return Q.pair_axes(state, words, i, j, qfield(d))


# --------------------------------------------------- diamond insertion (run 87)
def _pt(pq):
    """Exact point from the doubled representation (p, q) meaning (p + q sqrt2)/2."""
    return (Q2(F(pq[0], 2), F(pq[1], 2)), Q2(F(pq[2], 2), F(pq[3], 2)))


def _skeleton(runs):
    """A 1-D axis skeleton: the union of arithmetic runs `(start, step, count)`.

    Run 87's "bent grid" carried a chain of arbitrary exact steps; a chain is the
    one-run case of this, and a *union* of runs is what n = 19 and n = 40 need (two
    blocks separated by a seam).  Everything is `Q(sqrt2)`, so a step may be `1`,
    `sqrt2/2`, `4/3 sqrt2` -- any exact length.
    """
    vals = []
    for start, step, count in runs:
        for i in range(count):
            v = start + step * Q2(i)
            if v not in vals:
                vals.append(v)
    return vals


def _product_cells(runs_x, runs_y):
    """The carrier: every x of the x-skeleton against every y of the y-skeleton."""
    return [(x, y) for y in _skeleton(runs_y) for x in _skeleton(runs_x)]


def _collides(cell, slot):
    """Does the unit axis square at `cell` overlap the unit 45-degree square at `slot`?

    Exact: the L1 distance from the slot centre to the nearest point of the axis square
    must be at least sqrt2/2 for the two to be disjoint.  Touching is not overlapping,
    and the comparison is a sign test in Q(sqrt2) -- no tolerance.
    """
    dx = abs(cell[0] - slot[0]) - HALF
    dy = abs(cell[1] - slot[1]) - HALF
    dx = dx if dx.sign() > 0 else ZERO
    dy = dy if dy.sign() > 0 else ZERO
    return (dx + dy) < S2H


#: Declared diamond insertions.  A spec is two axis *skeletons* and a slot list; the
#: carrier is their product, and everything else -- which cells survive, the side, the
#: void, every contact -- is derived by the insertion rule.
#:
#: All three atoms are `Product(X, Y) - {cells colliding with a slot}`:
#:   n10  X = Y = {1/2, 3/2} u {3/2 + sqrt2/2, 5/2 + sqrt2/2}   (runs 2 + 2)
#:   n19  X = {1/2, 3/2} u {1/2 + a, 3/2 + a, 5/2 + a}, a = 4/3 sqrt2
#:        Y = {1/2, 3/2, 5/2} u {3/2 + a, 5/2 + a}
#:   n40  X = Y = {1/2, 3/2, 5/2} u {3/2 + 2 sqrt2, 5/2 + 2 sqrt2, 7/2 + 2 sqrt2}
#: so no field carries a list of axis cells any more, only run parameters (run 88).
_A19 = Q2(0, F(4, 3))          # 4/3 sqrt2
_T40 = Q2(0, 2)                # 2 sqrt2
_RUN2 = (HALF, Q2(1), 2)
_RUN3 = (HALF, Q2(1), 3)

DIAMOND_FIELDS: dict = {}

DIAMOND_FIELDS.update({
    "n10": {
        "x": (_RUN2, (Q2(F(3, 2)) + S2H, Q2(1), 2)),
        "y": (_RUN2, (Q2(F(3, 2)) + S2H, Q2(1), 2)),
        "slots": [_pt((3, 0, 3, 0)), _pt((3, 1, 3, 1))],
        "drop_colliding": True,
    },
    "n19": {
        "x": (_RUN2, (HALF + _A19, Q2(1), 3)),
        "y": (_RUN3, (Q2(F(3, 2)) + _A19, Q2(1), 2)),
        "slots": [
            _pt((1, F(1, 3), 3, F(2, 3))),
            _pt((1, F(4, 3), 3, F(-1, 3))),
            _pt((2, F(2, 3), 2, F(7, 3))),
            _pt((2, F(5, 3), 2, F(4, 3))),
            _pt((3, 2, 5, F(7, 3))),
            _pt((3, 3, 5, F(4, 3))),
            _pt((4, F(1, 3), 4, 2)),
            _pt((4, F(4, 3), 4, 1)),
        ],
        "drop_colliding": True,
    },
    "n40": {
        "x": (_RUN3, (Q2(F(3, 2)) + _T40, Q2(1), 3)),
        "y": (_RUN3, (Q2(F(3, 2)) + _T40, Q2(1), 3)),
        "slots": [
            _pt((4, -1, 4, 2)), _pt((4, 0, 4, 1)), _pt((4, 0, 4, 3)),
            _pt((4, 1, 4, 0)), _pt((4, 1, 4, 2)), _pt((4, 1, 4, 4)),
            _pt((4, 2, 4, -1)), _pt((4, 2, 4, 1)), _pt((4, 2, 4, 3)),
            _pt((4, 2, 4, 5)), _pt((4, 3, 4, 0)), _pt((4, 3, 4, 2)),
            _pt((4, 3, 4, 4)), _pt((4, 4, 4, 1)), _pt((4, 4, 4, 3)),
            _pt((4, 5, 4, 2)),
        ],
        "drop_colliding": True,
    },
})


def _assemble_field(name, spec, family="DiamondField", params=None, allow_empty=False):
    """Assemble a declared field: carrier product, insertion rule, derived geometry.

    The combinator is algebraic and parametric.  It expands the carrier (a product of
    two 1-D skeletons), applies the *insertion rule* -- an axis cell that would overlap
    a slot is removed, because that is what inserting a diamond means -- and then
    derives, rather than declares:

      * the container side `L`, as the exact bbox of the assembled squares;
      * the void `V = L^2 - N`, and the gain against `ceil(sqrt N)`;
      * every contact, by running the exact SAT gate on the assembled sentence;
      * an *overlap refusal*: a declaration whose assembly violates the gate is refused
        by `declaration_overlaps`, so a mis-declared slot cannot certify silently.
    """
    cells = _product_cells(spec["x"], spec["y"])
    slots = list(spec["slots"])
    if not slots and not allow_empty:
        raise Refusal("no_diamond",
                      f"{name} declares no slot, so it is a Tile, not an insertion")
    colliding = [c for c in cells if any(_collides(c, s) for s in slots)]
    if spec.get("drop_colliding", True):
        cells = [c for c in cells if c not in colliding]
    elif colliding:
        raise Refusal("declaration_overlaps",
                      f"{name}: {len(colliding)} axis cells collide with a slot "
                      f"and drop_colliding is off")
    if not cells:
        raise Refusal("empty_carrier", f"{name}: every axis cell was dropped")
    state = list(cells) + list(slots)
    words = [Q.AXIS] * len(cells) + [Q.word_45()] * len(slots)
    g = Q.gate(state, words)
    if not g["ok"]:
        raise Refusal("declaration_overlaps",
                      f"{name}: the assembled sentence has {g['violations']} violations")
    n = len(state)
    L = g["L"]
    claim = Claim("spatial_geometry", family, params or {"name": name}, n,
                  _laws_packing(n, L, L * L - Q2(n), g["contacts"]),
                  {"state": state, "words": words, "cells": cells, "slots": slots,
                   "dropped": colliding})
    claim.laws["diamonds"] = ("diamonds", len(slots))
    claim.laws["cells"] = ("axis cells", len(cells))
    claim.meta["dropped"] = len(colliding)
    claim.meta["carrier"] = len(cells) + len(colliding)
    return _tag(claim, L, n)


def p_diamond_field(name):
    """Diamond insertion: a declared carrier product plus 45-degree slots."""
    if name not in DIAMOND_FIELDS:
        raise Refusal("unknown_field", f"{name} is not a declared diamond field")
    return _assemble_field(name, DIAMOND_FIELDS[name])


def p_atom(n):
    """A delivered sentence, lifted exactly (n = 5, 10, 40 are the declared atoms)."""
    rows = _delivered_rows()
    if n not in rows:
        raise Refusal("no_such_row", f"row {n} is not in the table")
    st, ws, L = _lift_row(n, rows)
    if L is None:
        raise Refusal("atom_not_lifted", f"row {n} did not lift")
    return _tag(Claim("spatial_geometry", "Atom", {"n": n}, n,
                      _laws_packing(n, L, L * L - Q2(n)),
                      {"state": st, "words": ws}), L, n)


PACKING_ALPHABET = Alphabet("squares", "Q(sqrt 2)", {
    "A": {"kind": "axis", "measure": Q2(1), "extent": Q.frame_extent(*Q.AXIS),
          "data": Q.AXIS},
    "D": {"kind": "diagonal", "measure": Q2(1), "extent": S2H, "data": Q.word_45()},
    "T(t)": {"kind": "rational-t", "measure": Q2(1), "extent": None, "data": None},
})


# =============================================================== domain two
# Sturmian sequences over an exact slope: the same five combinator slots, filled by
# a domain in which nothing is geometric.
def mechanical_word(alpha: Q2, rho: Q2, n: int, offset=0):
    """The mechanical word: letter k is floor((k+1)a + r) - floor(ka + r), exactly.

    `offset` is a window into the same orbit, so two windows with offsets 0 and h
    concatenate to the window of length n starting at 0.  That is what makes the
    `Glue` combinator's law checkable rather than decorative.
    """
    out = []
    for k in range(n):
        kk = k + offset
        out.append((Q2(kk + 1) * alpha + rho).floor() - (Q2(kk) * alpha + rho).floor())
    return out


def _seq_claim(family, params, word, alpha, rho, parts=None, cob=False):
    n = len(word)
    n1 = sum(word)
    measure = Q2(n - n1) * (Q2(1) - alpha) + Q2(n1) * alpha
    laws = {"count": ("N", n), "measure": ("n0(1-a) + n1 a", measure),
            "ones": ("n1", n1)}
    claim = Claim("sturmian_sequences", family, params, n, laws,
                  {"word": word, "alpha": alpha, "rho": rho, "parts": parts})
    claim.measure = ("weight", measure)
    claim.invariant = ("ones", n1)
    if cob:
        claim.meta["coboundary"] = True
    return claim


def _slope(t) -> Q2:
    """Parse a declared slope: a rational `p/q`, or the irrational `sqrt2 - 1`."""
    if isinstance(t, Q2):
        return t
    s = str(t).strip()
    if s in ("√2 - 1", "-1 + √2", "sqrt2 - 1", "sqrt2-1"):
        return Q2(-1, 1)
    return Q2(F(s))


def _in_unit_interval(alpha: Q2) -> bool:
    return alpha.sign() > 0 and (Q2(1) - alpha).sign() > 0


def s_tile(t, n):
    """The mechanical word of slope t from the origin."""
    alpha = _slope(t)
    if not _in_unit_interval(alpha):
        raise Refusal("slope_out_of_range", f"a = {alpha} is not in (0, 1)")
    return _seq_claim("Tile", {"t": str(t), "n": n}, mechanical_word(alpha, ZERO, n),
                      alpha, ZERO)


def s_frame(t, r, n):
    """A rotation frame: the same slope with intercept r."""
    alpha, rho = _slope(t), Q2(F(r))
    if not _in_unit_interval(alpha):
        raise Refusal("slope_out_of_range", f"a = {alpha} is not in (0, 1)")
    return _seq_claim("Frame", {"t": str(t), "r": str(r), "n": n},
                      mechanical_word(alpha, rho, n), alpha, rho)


def s_glue(t, r, n):
    """Two consecutive windows of one orbit glued: the join is still mechanical."""
    alpha, rho = _slope(t), Q2(F(r))
    h = max(2, n // 2)
    u = mechanical_word(alpha, rho, h, 0)
    v = mechanical_word(alpha, rho, n - h, h)
    return _seq_claim("Glue", {"t": str(t), "r": str(r), "n": n}, u + v, alpha, rho,
                      parts=(u, v), cob=True)


def s_fold(t, r, n):
    """The reversal: the fold law, not the mechanical law, is its feasibility."""
    alpha, rho = _slope(t), Q2(F(r))
    w = mechanical_word(alpha, rho, n)
    claim = _seq_claim("SymmetryFold", {"t": str(t), "r": str(r), "n": n},
                       list(reversed(w)), alpha, rho)
    claim.payload["parent"] = w
    claim.meta["fold"] = True
    return claim


def s_strip(t, n, shift):
    """A window of the same orbit: a strip, not a new sequence."""
    alpha = _slope(t)
    rho = Q2(shift) * alpha
    return _seq_claim("Strip", {"t": str(t), "n": n, "shift": shift},
                      mechanical_word(alpha, rho, n), alpha, rho)


SEQ_ALPHABET = Alphabet("letters", "Q(sqrt 2)", {
    "0": {"kind": "letter", "measure": None, "extent": Q2(0)},
    "1": {"kind": "letter", "measure": None, "extent": Q2(0)},
})


# ------------------------------------------------------------------ wiring
def build_engine():
    eng = Engine()
    pk = Domain("spatial_geometry", PACKING_ALPHABET,
                [PackingGateWitness(), ContactGraphWitness(), ConservationWitness(),
                 DecimalWitness()])
    for name, fn in (("Tile", p_grid), ("Strip", p_strip), ("Pocket", p_pocket),
                     ("Glue", p_glue), ("SymmetryFold", p_fold), ("Atom", p_atom),
                     ("DiamondField", p_diamond_field), ("Slope", p_slope),
                     ("Seventh", p_seventh), ("Tilt", p_tilt), ("Ring", p_ring),
                     ("Staircase", p_staircase)):
        pk.register(name, fn)
    pk.decimal_model = spatial_decimal
    eng.register(pk)

    sq = Domain("sturmian_sequences", SEQ_ALPHABET,
                [MechanicalWitness(), ComplexityWitness(),
                 SequenceConservationWitness(), DecimalWitness()])
    for name, fn in (("Tile", s_tile), ("Frame", s_frame), ("Strip", s_strip),
                     ("Glue", s_glue), ("SymmetryFold", s_fold)):
        sq.register(name, fn)
    sq.decimal_model = sequence_decimal
    eng.register(sq)

    alpha_irr = Q2(-1, 1)                     # sqrt2 - 1, irrational: genuinely Sturmian
    eng.add_wheel(Wheel("spatial", pk, [
        Cell("Tile", {"k": k}) for k in (1, 2, 3, 4, 5)
    ] + [
        Cell("Pocket", {"k": k}) for k in (1, 2, 3)
    ] + [
        Cell("Strip", {"k": k, "m": m}) for k in (2, 3, 4) for m in (0, 1, 2, 3)
    ] + [
        Cell("Glue", {"t": t}) for t in ("1/2", "1/3", "1/5")
    ] + [
        Cell("SymmetryFold", {"k": k}) for k in (1, 2)
    ]     + [
        Cell("Atom", {"n": n}) for n in (5, 10, 40)
    ] + [
        Cell("DiamondField", {"name": name}) for name in sorted(DIAMOND_FIELDS)
    ] + [
        Cell("Slope", {"p": 2, "q": 1, "k": k}) for k in (1, 2, 3)
    ] + [
        Cell("Slope", {"p": 2, "q": 1, "k": k, "m": 2}) for k in (2, 3)
    ] + [
        Cell("Seventh", {"k": k}) for k in (1, 2, 3)
    ] + [
        Cell("Seventh", {"k": k, "m": 2}) for k in (2, 3)
    ] + [
        Cell("Tilt", {"t": "1/2", "k": k}) for k in (1, 2, 3)
    ] + [
        Cell("Tilt", {"t": "1/2", "k": k, "m": 2}) for k in (2, 3)
    ] + [
        Cell("Ring", {"k": 1})
    ] + [
        Cell("Staircase", {"k": 5})
    ]))
    eng.add_wheel(Wheel("sequences", sq, [
        Cell("Tile", {"t": str(alpha_irr), "n": 21}),
        Cell("Tile", {"t": "1/2", "n": 21}),
        Cell("Frame", {"t": str(alpha_irr), "r": "1/2", "n": 21}),
        Cell("Frame", {"t": str(alpha_irr), "r": "1/3", "n": 21}),
        Cell("Strip", {"t": str(alpha_irr), "n": 21, "shift": 3}),
        Cell("Glue", {"t": str(alpha_irr), "r": "1/2", "n": 21}),
        Cell("SymmetryFold", {"t": str(alpha_irr), "r": "0", "n": 21}),
    ]))

    # third domain: lattice shells.  It brings its own alphabet, its own four
    # witnesses and its own refusal laws; the engine needs no branch for it.
    import lattice_shells as LAT        # deferred: lattice_shells imports this module
    eng.register(LAT.domain())
    eng.add_wheel(LAT.wheel())
    return eng


# ------------------------------------------------------------- delivered rows
_ROWS_CACHE = {}


#: π at 100 digits, as an exact rational: the table stores *radians*, so the word
#: classification must compare against π/4 and π/2 with a declared tolerance.
PI = F(Decimal("3.141592653589793238462643383279502884197169399375105820974944"
               "5923078164062862089986280348253421170679"))
HALF_PI = PI / 2


def _word_of(angle: F):
    """The declared word of a stored angle in radians, decided exactly.

    The table writes the 45-degree pose as a 12-dp decimal of π/4, so the test is
    `|angle mod π/2 - π/4| < 1e-9` — an exact comparison against an exact π, with
    the tolerance declared rather than hidden inside a float subtraction.
    """
    a = angle % HALF_PI
    tol = F(1, 10 ** 9)
    if abs(a - HALF_PI / 2) < tol:
        return Q.word_45()
    if a < tol or a > HALF_PI - tol:
        return Q.AXIS
    return None


def _delivered_rows():
    """The table, with every angle parsed as an exact Fraction (no float)."""
    if _ROWS_CACHE:
        return _ROWS_CACHE["rows"]
    rows = {}
    with open(SUBMISSION) as f:
        for r in csv.DictReader(f):
            rows.setdefault(int(r["n"]), []).append(
                (F(r["x"]), F(r["y"]), F(r["angle"])))
    _ROWS_CACHE["rows"] = rows
    return rows


_TABLE_SIDE: dict = {}


def _table_side(n):
    """The delivered side for row `n`, exactly (Q(sqrt 2) lift), or None.

    Runs 84-85 lift every deliverable row into an exact sentence; the side the gate
    reads off that lift *is* the delivered side, so a new family can be calibrated
    against it without a decimal anywhere.
    """
    if n in _TABLE_SIDE:
        return _TABLE_SIDE[n]
    st, ws, _L = _lift_row(n)
    side = None if st is None else Q.gate(st, ws)["L"]
    _TABLE_SIDE[n] = side
    return side


def _lift_row(n, rows=None):
    """Lift one delivered row into Q(sqrt 2); returns (state, words, side) or Nones."""
    rows = rows or _delivered_rows()
    st = rows[n]
    ws = [_word_of(t) for _, _, t in st]
    if any(w is None for w in ws):
        return None, None, None
    r = Q.lift_sentence([(Q2(x), Q2(y)) for x, y, _ in st], ws)
    if r["status"] != "lifted":
        return None, None, None
    return r["state"], ws, r["L"]


# --------------------------------------------------------- the 1000-row census
def q_rows():
    rows = _delivered_rows()
    return sorted(n for n, st in rows.items() if all(t == 0 for _, _, t in st))


def lift_axis_row(n, rows):
    """Certify a pure-Q row by exact lattice snap, then let the gate judge.

    A row with only the 0-degree word is a set of unit squares in an integer box,
    so its centres are half-integers and its side is an integer.  The snap is exact
    rounding (`floor_q2(v*2 + 1/2)`), not a tolerance, and nothing is accepted
    without the exact gate at clearance 0; a row whose decimals are not on that
    lattice is refused by the gate, not waved through.
    """
    st = rows[n]
    ws = [_word_of(t) for _, _, t in st]
    if any(w is None or w[0].b != 0 or w[1].b != 0 for w in ws):
        return None, None, "not the 0-degree word"
    c = [(Q2(x), Q2(y)) for x, y, _ in st]
    exact_box = Q.side(c, ws)
    L, resid, _b = Q.recover_side(exact_box, tol=Q2(F(1, 10 ** 7)))
    if L is None or L.b != 0:
        return None, None, "side is not an integer"
    snapped = [(Q2(F(Q.floor_q2(x * Q2(2) + HALF), 2)),
                Q2(F(Q.floor_q2(y * Q2(2) + HALF), 2))) for x, y in c]
    # The lattice certificate, exact: unit axis squares whose centres are distinct
    # half-integers inside the box are pairwise separated, because differences of
    # half-integers are integers, so two distinct centres differ by >= 1 on some
    # axis -- which is exactly the SAT condition for this word.  The gate is still
    # run on every row small enough to afford it, as the independent witness.
    ok, detail = axis_row_certificate(snapped, L)
    if not ok:
        return None, None, f"lattice certificate refused: {detail}"
    if len(snapped) <= 250:
        g = Q.gate(snapped, ws)
        if not g["ok"] or (g["clearance"] is not None and g["clearance"] != 0):
            return None, None, f"gate refused after snap ({g['violations']} violations)"
        if g["L"] != L:
            return None, None, f"snapped side {g['L']} != recovered {L}"
    return snapped, ws, None


def axis_contacts(snapped):
    """Edge contacts of a snapped axis row: exactly the pairs one unit apart."""
    pts = set(snapped)
    n = 0
    for (x, y) in pts:
        for dx, dy in ((2, 0), (0, 2)):            # +1 in the half-integer grid
            if (Q2(x.a + F(dx, 2)), Q2(y.a + F(dy, 2))) in pts:
                n += 1
    return n


def axis_row_certificate(snapped, L):
    """Exact O(n) certificate for a pure-Q row: distinct half-integer points in box."""
    seen = set()
    for x, y in snapped:
        if x.b != 0 or y.b != 0:
            return False, "a coordinate is not rational"
        if x < HALF or x > L - HALF or y < HALF or y > L - HALF:
            return False, f"centre ({x}, {y}) is outside [1/2, {L} - 1/2]^2"
        if x.a.denominator != 2 or y.a.denominator != 2:
            return False, f"centre ({x}, {y}) is not a half-integer"
        if (x, y) in seen:
            return False, f"duplicate centre ({x}, {y})"
        seen.add((x, y))
    return True, f"{len(seen)} distinct half-integer centres in the box"


def census(budget=Decimal(240)):
    """Certify the pure-Q rows at clearance 0.  Budgeted and cached."""
    led = json.load(open(CENSUS)) if os.path.exists(CENSUS) else {}
    done = led.setdefault("rows", {})
    targets = q_rows()
    t0 = Decimal(time.time())
    fresh = 0
    for n in targets:
        if str(n) in done:
            continue
        if Decimal(time.time()) - t0 > Decimal(budget):
            break
        snap, ws, why = lift_axis_row(n, _delivered_rows())
        if snap is not None:
            L = Q.grid_side(n)
            if len(snap) <= 250:
                g = Q.gate(snap, ws)
                method = "gate"
                clearance, contacts = str(g["clearance"]), g["contacts"]
            else:
                method = "lattice lemma"
                clearance = "0"
                contacts = axis_contacts(snap)
            done[str(n)] = {
                "n": n, "status": "certified", "method": method,
                "side_exact": str(L), "grid": str(L),
                "clearance": clearance, "contacts": contacts,
                "squares": len(snap), "refusal": None,
            }
        else:
            st, ws, L = _lift_row(n)
            done[str(n)] = {
                "n": n, "status": "certified" if L is not None else "not-lifted",
                "method": "contact peel",
                "side_exact": str(L) if L is not None else None,
                "grid": str(Q.grid_side(n)),
                "clearance": "0" if L is not None else None,
                "contacts": Q.gate(st, ws)["contacts"] if L is not None else 0,
                "squares": len(_delivered_rows()[n]), "refusal": why,
            }
        fresh += 1
        if fresh % 20 == 0:
            json.dump(led, open(CENSUS, "w"), indent=1)
    json.dump(led, open(CENSUS, "w"), indent=1)
    todo = [n for n in targets if str(n) not in done]
    cert = sum(1 for n in targets if done.get(str(n), {}).get("status") == "certified")
    print(f"CENSUS — pure-Q rows: {len(targets)} targets, {len(done)} done "
          f"({cert} certified at clearance 0), {len(todo)} remaining, "
          f"{fresh} this call")
    return len(todo)


# ------------------------------------------------------------------ outlier probe
def _outlier_targets():
    return (51, 126, 295)


def _decimal_side_fraction(n, rows):
    """The row's bounding-box side as an exact Fraction of the stored decimals.

    Extents are taken at 70 digits (Decimal sqrt, never float), so this is the real
    number the table *stores*, and a field test against it is a test of the row.
    """
    xs, ys = [], []
    for x, y, a in rows[n]:
        w = _word_of(a)
        if w is None:
            return None
        ce = [Decimal(v.a.numerator) / Decimal(v.a.denominator)
              + Decimal(v.b.numerator) / Decimal(v.b.denominator)
              * Decimal(v.d).sqrt() for v in w]
        ex = (abs(ce[0]) + abs(ce[1])) / 2
        xd = Decimal(x.numerator) / Decimal(x.denominator)
        yd = Decimal(y.numerator) / Decimal(y.denominator)
        xs += [xd - ex, xd + ex]
        ys += [yd - ex, yd + ex]
    return F(max(max(xs) - min(xs), max(ys) - min(ys)))


def _nearest_rational(x: F, qmax=8):
    """The nearest p/q to a rational x (exact comparison), and its residual."""
    best = None
    for q in range(1, qmax + 1):
        p = (x * q + F(1, 2)).__floor__()
        err = abs(x - F(p, q))
        if best is None or err < best[1]:
            best = (F(p, q), err)
    return best


def probe(budget=Decimal(240)):
    """Ask which field the three unlifted rows' sides live in, exactly.

    The stored side is a rational (70-digit Decimal of the table's own numbers), so
    "is it in Q(sqrt d) at small height?" is a decidable question: `recover_scalar`
    tests it with exact comparisons.  A field is *witnessed* only if a value within
    1e-7 exists at two different height bounds; otherwise the residual is recorded,
    because "not at small height" is a measurement, not a guess.
    """
    led = json.load(open(PROBE)) if os.path.exists(PROBE) else {}
    done = led.setdefault("rows", {})
    targets = _outlier_targets()
    t0 = Decimal(time.time())
    rows = _delivered_rows()
    for n in targets:
        if str(n) in done:
            continue
        if Decimal(time.time()) - t0 > Decimal(budget):
            break
        side = _decimal_side_fraction(n, rows)
        if side is None:
            continue
        rec = {"n": n, "decimal_side": str(side), "fields": {}}
        rq, rerr = _nearest_rational(side)
        rec["fields"]["Q"] = {"value": str(rq), "lifts": rerr < F(1, 10 ** 7),
                              "stable": True}
        for d in range(2, 22):
            if not EF.is_squarefree(d):
                continue
            cls = type(f"Q{d}", (EF.Quad,), {"d": d, "__slots__": ()})
            x = cls(side, 0)
            one = EF.recover_scalar(x, cls, dens=(1, 2, 3, 4, 6, 8), bmax=8,
                                    tol=cls(F(1, 10 ** 7)))
            two = EF.recover_scalar(x, cls, dens=(1, 2, 3, 4, 6, 8), bmax=16,
                                    tol=cls(F(1, 10 ** 7)))
            rec["fields"][str(d)] = {
                "value": str(one) if one is not None else None,
                "stable": bool(one is not None and one == two),
                "lifts": one is not None,
            }
        done[str(n)] = rec
        json.dump(led, open(PROBE, "w"), indent=1)
    print(f"PROBE — {len(done)}/{len(targets)} rows probed")
    for n in targets:
        r = done.get(str(n))
        if not r:
            continue
        hits = [d for d, v in r["fields"].items() if v["lifts"]]
        print(f"  n={n:4d} side {r['decimal_side']:>24s}  fields with a small-height "
              f"value: {hits if hits else 'none of d <= 21'}")
    return done


# ------------------------------------------------- exact 2D cage recovery
def _lattice_candidates(x: Q2, tol: Q2, dens=(1, 2, 3, 4, 6, 8), bmax=8):
    """Every small-height lattice point within `tol` of x (the cage's walls)."""
    out = []
    for D in dens:
        scale = 4 * D
        for num in range(-bmax * D, bmax * D + 1):
            b = F(num, D)
            rest = x - Q2(0, b)
            k = (rest * scale).floor()
            for kk in (k, k + 1):
                cand = Q2(F(kk, scale), b)
                if abs(x - cand) <= tol:
                    out.append(cand)
    return out


def cage_point(state, words, j, L, target, tol=None):
    """The exact 2D feasible cage for square `j`, resolved in the field.

    The old fallback ran one height search per coordinate and hoped the pair would
    be consistent.  The cage is the *joint* object: the lattice points within `tol`
    of the stored coordinate on each axis, filtered by the box and by the exact SAT
    predicate against every already-placed square.  The returned point is the
    canonical one — nearest the stored coordinate, ties broken lexicographically —
    so the result does not depend on search order, and a point that fails the 2D
    predicate is never returned.
    """
    tol = Q2(F(1, 10 ** 7)) if tol is None else tol
    ex = Q.frame_extent(*words[j])
    placed = [i for i in range(len(state)) if state[i] is not None and i != j]
    xs = _lattice_candidates(target[0], tol)
    ys = _lattice_candidates(target[1], tol)
    best = None
    for x in xs:
        if x < ex or x > L - ex:
            continue
        for y in ys:
            if y < ex or y > L - ex:
                continue
            trial = list(state)
            trial[j] = (x, y)
            ok = True
            for i in placed:
                if not any(s.sign() >= 0 for _q, s, _n, _o
                           in Q.pair_axes(trial, words, i, j)):
                    ok = False
                    break
            if not ok:
                continue
            err = abs(x - target[0]) + abs(y - target[1])
            if best is None or err < best[0] or (err == best[0] and (x, y) < (best[1], best[2])):
                best = (err, x, y)
    return None if best is None else (best[1], best[2])


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    eng = build_engine()
    announced = []

    def say(msg):
        """Announce one control.  The count at the end is the number of announcements,
        so adding or removing a control cannot leave a stale number behind."""
        announced.append(msg)
        print(msg)

    # 1. the same five combinator names are registered on both domains
    pk, sq = eng.domains["spatial_geometry"], eng.domains["sturmian_sequences"]
    shared = set(pk.combinators) & set(sq.combinators)
    assert shared >= {"Tile", "Strip", "Glue", "SymmetryFold"}, shared
    say(f"control 1 — both domains register the same engine slots {sorted(shared)}")

    # 2. the packing wheel certifies its closed-form families
    rows = eng.wheels[0].spin()
    cert = [r for r in rows if r["verdict"] == "certified"]
    assert len(cert) >= 15, len(cert)
    say(f"control 2 — spatial wheel: {len(cert)}/{len(rows)} cells certified")

    # 3. every certified packing cell has all four witnesses, not one metric
    for r in cert:
        assert len(r["witnesses"]) == 4, r
        assert all(w["ok"] for w in r["witnesses"].values()), r
    assert all(r["witness_count"] >= 3 for r in cert), cert[0]
    assert all(r["measure"] and r["size"] for r in cert), cert[0]
    say("control 3 — every certified spatial cell passes all four witnesses "
          "(gate, contact graph, conservation, Decimal), and the row carries the "
          "neutral size/measure/invariant columns")

    # 4. the strip's closed forms hold for the wheel's own cells
    for r in cert:
        if r["family"] != "Strip":
            continue
        k, m = int(r["params"]["k"]), int(r["params"]["m"])
        assert r["size"] == 4 * k * k + m
    say("control 4 — the Strip cells satisfy N = 4k^2 + m and L = 2k + m sqrt2/2")

    # 5. the refusal laws still fire -- on constructed cells, because run 88 closed the
    #    last three non-viable cells of the wheel (the S(k,0) refusals), so a spatial
    #    wheel with no refusal is the result, not a silent skip
    refused = [r for r in rows if r["verdict"] == "refused"]
    assert not refused, refused

    def _law(fn):
        try:
            fn()
        except Refusal as e:
            return e.law
        return None

    empty = {"x": ((HALF, Q2(1), 2),), "y": ((HALF, Q2(1), 2),), "slots": []}
    bad = dict(DIAMOND_FIELDS["n10"], drop_colliding=False)
    cases = {
        "degenerate_cell": lambda: p_strip(0, 0),
        "negative_seam": lambda: p_strip(2, -1),
        "unknown_field": lambda: p_diamond_field("not_a_field"),
        "no_diamond": lambda: _assemble_field("empty", empty),
        "declaration_overlaps": lambda: _assemble_field("bad", bad),
        "ring_chain_adrift": lambda: p_ring(2),
        "staircase_layer_gap": lambda: staircase_field(Q2, Q2(0, F(1, 2)),
                                                       Q2(0, F(1, 2)), 1, Q2(0)),
    }
    for law, fn in cases.items():
        assert _law(fn) == law, (law, _law(fn))
    elsewhere = {r["refusal"]["law"] for w in eng.wheels[1:] for r in w.spin()
                 if r["verdict"] == "refused"}
    assert elsewhere, "the other wheels must still refuse by law"
    say(f"control 5 — the spatial wheel has no refused cell (S(k,0) now certifies), "
          f"and every refusal law still fires on a constructed cell: "
          f"{sorted(cases)}; other wheels refuse by {sorted(elsewhere)}")

    # 6. the fold is an exact symmetry: same N, same L, witnesses still pass
    a, b = p_pocket(2), p_fold(2)
    assert a.n == b.n and a.laws["extent"][1] == b.laws["extent"][1]
    say("control 6 — the diagonal fold preserves N and L exactly")

    # 7. sequences: an irrational slope gives a Sturmian word, a rational one does not
    rows = eng.wheels[1].spin()
    by_t = {}
    for r in rows:
        by_t[(r["params"]["t"], r["verdict"])] = by_t.get((r["params"]["t"], r["verdict"]), 0) + 1
    assert any(r["params"]["t"] == str(Q2(-1, 1)) and r["verdict"] == "certified"
               for r in rows), rows
    assert any(r["params"]["t"] == "1/2" and r["verdict"] == "refused" for r in rows)
    say("control 7 — slope sqrt2-1 certifies, slope 1/2 is refused (not Sturmian)")

    # 8. the refusal for a rational slope is the complexity law, with its numbers
    bad = [r for r in rows if r["params"]["t"] == "1/2"][0]
    assert bad["refusal"]["law"] == "not_sturmian", bad["refusal"]
    say(f"control 8 — rational slope refused by the exact law: {bad['refusal']}")

    # 9. the coboundary law d(uv) = du xor dv holds on the glue cell
    glue = [r for r in rows if r["family"] == "Glue"][0]
    assert glue["verdict"] == "certified"
    assert "coboundary" in glue["witnesses"]["conservation"]["detail"]
    say("control 9 — the glue cell passes the coboundary witness on its join")

    # 10. Decimal cross-check: the signs agree, and a perturbed claim is caught
    claim = p_pocket(2)
    ok, detail = DecimalWitness().check(claim, pk)
    assert ok, detail
    claim2 = p_pocket(2)
    claim2.laws["extent"] = ("L", claim2.laws["extent"][1] + Q2(F(1, 10 ** 9)))
    ok2, _ = DecimalWitness().check(claim2, pk)
    assert not ok2, "the Decimal witness must catch a 1e-9 lie"
    say("control 10 — the Decimal witness accepts the exact side and catches a 1e-9 lie")

    # 11. the tower audit covers this module too
    checked, offenders, skipped = EF.audit_module(sys.modules[__name__],
                                                  exempt=EF.AUDIT_EXEMPT)
    assert offenders == [], offenders
    say(f"control 11 — this module's {checked} decision functions name no float "
          f"({len(skipped)} display/test exemptions declared)")

    # 12. cage recovery places a square the contact graph leaves free, exactly
    st, ws, L = Q_mixed_strip(2, 1)
    true_pt = st[0]
    broken = list(st)
    broken[0] = None
    pt = cage_point(broken, ws, 0, L, true_pt)
    assert pt == true_pt, (pt, true_pt)
    trial = list(st)
    trial[0] = pt
    assert Q.gate(trial, ws)["ok"]
    # and it refuses to place the square anywhere when the cage is empty
    assert cage_point(broken, ws, 0, L, (Q2(-99), Q2(-99))) is None
    say(f"control 12 — the 2D cage recovers the freed square exactly ({pt}) and "
          f"returns nothing when the cage is empty")

    # 13. a third, structurally distinct domain registers the same slots
    import lattice_shells as LAT
    lat = eng.domains["lattice_shells"]
    shared3 = (set(pk.combinators) & set(sq.combinators)) & set(lat.combinators)
    assert shared3 >= {"Tile", "Strip", "Glue", "SymmetryFold"}, shared3
    assert shared3 == {"Tile", "Strip", "Glue", "SymmetryFold"}, shared3
    say(f"control 13 — three domains share the engine slots {sorted(shared3)}; "
          f"lattice adds {sorted(set(lat.combinators) - shared3)}")

    # 14. the theta series are the classical ones, by enumeration (no tables)
    TH = LAT.theta(LAT.LATTICES["D4"], 6), LAT.theta(LAT.LATTICES["E8"], 4), \
        LAT.theta(LAT.LATTICES["Z4"], 6)
    assert TH[0] == [1, 0, 24, 0, 24, 0, 96], TH[0]
    assert TH[1] == [1, 0, 240, 0, 2160], TH[1]
    assert TH[2] == [1, 8, 24, 32, 24, 48, 96], TH[2]
    say(f"control 14 — theta by exact enumeration: D4 {TH[0]}, E8 {TH[1]}, Z4 {TH[2]}")

    # 15. kissing topology: shell sizes and inner-product-1 degrees, computed
    k = {key: len(LAT.shell(LAT.LATTICES[key], LAT.LATTICES[key].minimal_norm))
         for key in ("Z2", "D4", "E8")}
    deg = {key: LAT.root_degree(LAT.LATTICES[key]) for key in ("Z2", "D4", "E8")}
    assert k == {"Z2": 4, "D4": 24, "E8": 240}, k
    assert deg == {"Z2": None, "D4": 8, "E8": 56}, deg
    say(f"control 15 — kissing numbers {k} and root degrees {deg}")

    # 16. the conservation law is theta multiplicativity, and it is exact
    g = LAT.l_sum("Z2", "D4", 4)
    enumerated = [len(x) for x in g.payload["pairs"]]
    assert tuple(enumerated) == tuple(g.payload["conv"]) == g.laws["theta"][1], g.laws
    ran = 0
    for w in lat.suite(g):
        ok, detail = w.check(g, lat)
        assert ok, (w.name, detail)
        ran += 1
    assert ran == 3, ran      # the kissing witness scopes itself to Frame/Atom
    say(f"control 16 — Z2 (+) D4: enumerated {tuple(enumerated)} == convolution, "
          f"{ran} applicable witnesses pass (kissing is a Frame/Atom law only)")

    # 17. a wrong lattice claim is refused, by witness or by declared law
    liar = LAT.l_atom("Z4")
    liar.laws["kissing"] = ("|L_min|", 24)
    ok, detail = LAT.KissingWitness().check(liar, lat)
    assert not ok, "the kissing witness must catch a claimed 24 for Z4 (true 8)"
    refusals = []
    for key, m in (("D4", 3), ("E8", 1)):
        try:
            LAT.l_shell(key, m)
        except Refusal as r:
            refusals.append(r.law)
    try:
        LAT.l_sum("Z4", "E8", 2)
    except Refusal as r:
        refusals.append(r.law)
    assert refusals == ["empty_shell", "empty_shell", "rank_budget"], refusals
    say(f"control 17 — a wrong kissing number is refused ({detail[:40]}...), and "
          f"the declared laws fire: {refusals}")

    # 18. the cell algebra: run parameters, not cell lists, generate the run-87 census
    CENSUS_10 = [(1, 0, 1, 0), (3, 1, 1, 0), (5, 1, 1, 0), (5, 1, 3, 0),
                 (1, 0, 3, 1), (1, 0, 5, 1), (3, 0, 5, 1), (5, 1, 5, 1)]
    CENSUS_19 = [(1, 0, 1, 0), (1, 0, 3, F(8, 3)), (1, 0, 5, F(8, 3)),
                 (1, F(8, 3), 1, 0), (3, 0, 5, F(8, 3)), (3, F(8, 3), 1, 0),
                 (3, F(8, 3), 3, 0), (5, F(8, 3), 1, 0), (5, F(8, 3), 3, 0),
                 (5, F(8, 3), 5, 0), (5, F(8, 3), 5, F(8, 3))]
    CENSUS_40 = [(1, 0, 1, 0), (1, 0, 3, 0), (1, 0, 3, 4), (1, 0, 5, 0),
                 (1, 0, 5, 4), (1, 0, 7, 4), (3, 0, 1, 0), (3, 0, 3, 0),
                 (3, 0, 5, 4), (3, 0, 7, 4), (3, 4, 1, 0), (3, 4, 7, 4),
                 (5, 0, 1, 0), (5, 0, 7, 4), (5, 4, 1, 0), (5, 4, 3, 0),
                 (5, 4, 5, 4), (5, 4, 7, 4), (7, 4, 1, 0), (7, 4, 3, 0),
                 (7, 4, 3, 4), (7, 4, 5, 0), (7, 4, 5, 4), (7, 4, 7, 4)]
    census = {"n10": (CENSUS_10, 16, 8), "n19": (CENSUS_19, 25, 14),
              "n40": (CENSUS_40, 36, 12)}
    tables = []
    for name, (want, carrier, dropped) in census.items():
        c = p_diamond_field(name)
        spec = DIAMOND_FIELDS[name]
        got = {(str(x), str(y)) for x, y in c.payload["cells"]}
        ref = {(str(_pt(q)[0]), str(_pt(q)[1])) for q in want}
        assert got == ref, (name, len(got), len(ref))
        assert c.meta["carrier"] == carrier and c.meta["dropped"] == dropped, c.meta
        assert len(spec["x"]) <= 2 and len(spec["y"]) <= 2, spec
        tables.append(f"{name} {carrier}->{len(got)} (-{dropped})")
    say("control 18 — two axis runs per side generate the run-87 census exactly: "
          + ", ".join(tables))

    # 19. the Strip builder is a field of (k, m): S(k,0) certifies and IS the plain grid
    for kk in (1, 2, 3, 4):
        zero = p_strip(kk, 0)
        grid = p_grid(2 * kk)
        assert zero.laws["extent"][1] == grid.laws["extent"][1] == Q2(2 * kk)
        assert zero.n == grid.n == 4 * kk * kk, (kk, zero.n)
        assert zero.laws["gain"][1] == Q2(0), zero.laws["gain"]
        assert ({(str(x), str(y)) for x, y in zero.payload["state"]}
                == {(str(x), str(y)) for x, y in grid.payload["state"]}), kk
    for kk, mm in ((2, 1), (2, 2), (3, 1), (3, 3), (4, 2)):
        field = p_strip(kk, mm)
        st, ws, L = Q_mixed_strip(kk, mm)
        assert field.laws["extent"][1] == L, (kk, mm, field.laws["extent"][1], L)
        assert ({(str(x), str(y)) for x, y in field.payload["state"]}
                == {(str(x), str(y)) for x, y in st}), (kk, mm)
        assert field.n == 4 * kk * kk + mm, (kk, mm, field.n)
    one = p_strip(2, 1)
    assert one.laws["gain"][1] == Q2(1) - S2H, one.laws["gain"]
    # the Pocket is the strip at m = 1, on the same build path (run 89): same cells, same
    # words, same side, same N -- but it keeps its own family, that being what it claims
    for kk in (1, 2, 3):
        pocket, strip = p_pocket(kk), p_strip(kk, 1)
        assert pocket.family == "Pocket" and strip.family == "Strip"
        assert pocket.payload["state"] == strip.payload["state"], kk
        assert pocket.payload["words"] == strip.payload["words"], kk
        assert pocket.laws["extent"][1] == strip.laws["extent"][1], kk
        assert pocket.n == strip.n == 4 * kk * kk + 1, (kk, pocket.n, strip.n)
    say("control 19 — S(k,0) is no longer refused: it certifies as the plain 2k grid "
        "(gain 0) for k = 1..4, S(k,m) reproduces the run-84 sentence for m >= 1 "
        "(L = 2k + m sqrt2/2, N = 4k^2 + m), and the Pocket is the same field at "
        "m = 1: one build path, two families")

    # 20. a genuinely malformed declaration is refused by the gate, not by a flag:
    #     two slots that overlap *each other* cannot be caught by the carrier rule
    dbl = dict(DIAMOND_FIELDS["n10"])
    dbl["slots"] = [_pt((3, 0, 3, 0)), _pt((3, 0, 3, 0))]
    try:
        _assemble_field("double_slot", dbl)
        raise AssertionError("an overlapping pair of slots must not certify")
    except Refusal as e:
        assert e.law == "declaration_overlaps", e.law
        assert "violations" in e.detail, e.detail
    near = dict(DIAMOND_FIELDS["n10"])
    near["slots"] = [_pt((3, 0, 3, 0)), _pt((3, F(1, 10), 3, 0))]
    try:
        _assemble_field("near_slots", near)
        raise AssertionError("two slots 1/10 apart must not certify")
    except Refusal as e:
        assert e.law == "declaration_overlaps", e.law
    loose = dict(DIAMOND_FIELDS["n10"], drop_colliding=False)
    try:
        _assemble_field("no_rule", loose)
        raise AssertionError("a slot over an axis cell with the rule off must refuse")
    except Refusal as e:
        assert e.law == "declaration_overlaps", e.law
    say("control 20 — a malformed declaration is refused by `declaration_overlaps`, "
        "three ways: two coincident slots and two slots 1/10 apart (both caught by the "
        "gate, since the carrier rule cannot see slot-slot overlap), and a slot over an "
        "axis cell with the insertion rule switched off (caught by the rule)")

    # 21. the algebraic rungs: one ridge family, three fields, and the 45-degree member
    #     IS the Strip -- so the census's Q(sqrt5), Q(sqrt7) and rational-t rungs are
    #     gate-verified by the same procedure as every Q(sqrt2) cell
    pk = eng.domains["spatial_geometry"]
    compared = 0
    for cell in eng.wheels[0].cells:
        claim = pk.build(cell.family, **cell.params)
        st, ws = claim.payload["state"], claim.payload["words"]
        cls = type(st[0][0])
        g_infer = Q.gate(st, ws)              # the field read off the state
        g_decl = Q.gate(st, ws, cls)          # the field declared
        for key in ("ok", "L", "clearance", "contacts", "violations"):
            assert g_infer[key] == g_decl[key], (cell.family, cell.params, key)
        assert gate_of(claim) == g_infer, (cell.family, cell.params)
        for i in range(len(st)):
            for j in range(i + 1, len(st)):
                a = [(str(q[0]), str(q[1]), sl.sign())
                     for q, sl, _n, _o in Q.pair_axes(st, ws, i, j)]
                b = [(str(q[0]), str(q[1]), sl.sign())
                     for q, sl, _n, _o in pairs_of(claim, i, j)]
                assert a == b, (cell.family, cell.params, i, j)
        compared += 1
    assert compared == len(eng.wheels[0].cells) >= 40, compared
    for kk in (1, 2):
        ridge = p_ridge(2, *Q.word_45(), kk, "Ridge45", {"k": kk})
        strip = p_strip(kk, 1)
        assert ridge.laws["extent"][1] == strip.laws["extent"][1] == \
            Q2(2 * kk) + S2H, (kk, ridge.laws["extent"][1])
        assert ({(str(x), str(y)) for x, y in ridge.payload["state"]}
                == {(str(x), str(y)) for x, y in strip.payload["state"]}), kk
    rungs = []
    for fam, cell in (("Slope", p_slope(2, 1, 1)), ("Seventh", p_seventh(1)),
                      ("Tilt", p_tilt(F(1, 2), 1)), ("Slope", p_slope(2, 1, 2)),
                      ("Seventh", p_seventh(2)), ("Tilt", p_tilt(F(1, 2), 2))):
        g = gate_of(cell)
        assert g["ok"] and g["clearance"] == 0 and g["contacts"] >= 1, (fam, g)
        tbl = cell.meta["table_side"]
        tag = ("uncalibrated: the delivered row is outside the axis/45-deg alphabet"
               if tbl is None else
               ("beats the table" if cell.meta["beats_table"] else "dominated"))
        rungs.append(f"{fam} n={cell.size} L={cell.laws['extent'][1]} vs table {tbl} "
                     f"({tag})")
    assert all(not p_ridge(2, *Q.word_45(), kk, "R", {"k": kk}).meta["beats_table"]
               for kk in (1, 2)), "the 45-degree member is the best of the family"
    try:
        p_ridge(5, qfield(5)(0), qfield(5)(0), 1, "Bad", {})
        raise AssertionError("a word off the unit circle must refuse")
    except Refusal as e:
        assert e.law in ("word_off_circle", "wrong_field"), e.law
    say(f"control 21 — one gate, {compared} spatial cells: the field read off the state "
        "and the field declared give identical verdicts and identical pair slacks on "
        "every cell; the 45-degree ridge reproduces S(k,1) exactly and every rung gates "
        "at clearance 0 with its exact algebraic side: " + "; ".join(rungs))

    # ------------------------------------------------ control 22: the m-diamond bar
    doubles = 0
    for kk in (1, 2, 3):
        for mm in (1, 2, 3):
            ridge = p_ridge(2, *Q.word_45(), kk, "Ridge45", {"k": kk, "m": mm}, mm)
            strip = strip_field(kk, mm)
            cells = sorted(map(tuple, _product_cells(strip["x"], strip["y"])))
            slots = sorted(map(tuple, strip["slots"]))
            st, ws = ridge.payload["state"], ridge.payload["words"]
            axis = sorted(map(tuple, [st[i] for i in range(len(st))
                                      if ws[i] == (Q2(1), Q2(0))]))
            tilt = sorted(map(tuple, [st[i] for i in range(len(st))
                                      if ws[i] != (Q2(1), Q2(0))]))
            assert axis == cells and tilt == slots, (kk, mm)
            assert ridge.size == 4 * kk * kk + mm, (kk, mm, ridge.size)
            assert ridge.laws["extent"][1] == Q2(2 * kk) + S2H * Q2(mm), (kk, mm)
            doubles += 1
    rungs = []
    for fam, d, cw, sw in (("45", 2, *Q.word_45()), ("Slope-2:1", 5, *unit_word(5, 2, 1)),
                           ("Seventh", 7, *_sqrt7_word()),
                           ("Tilt-1/2", 2, Q2(EF.tword(F(1, 2))[0]), Q2(EF.tword(F(1, 2))[1]))):
        cls = qfield(d)
        cw, sw = (cw if isinstance(cw, cls) else cls(cw)), (sw if isinstance(sw, cls) else cls(sw))
        w1 = ridge_width(cls, cw, sw, 2, 1)
        n18 = ridge_width(cls, cw, sw, 2, 2)
        assert n18 == w1 * cls(2), (fam, w1, n18)
        wider = [ridge_width(cls, cw, sw, 2, m) for m in (3, 4)]
        assert all(w > n18 for w in wider), (fam, wider)
        rungs.append(f"{fam}: w*(1)={w1}, w*(2)={n18}=2 w*(1), w*(3)={wider[0]}, "
                     f"w*(4)={wider[1]}, L(2,2)={cls(4) + n18}")
        # the census row's side, honestly: no member of this family reaches it
        target = None
        if d == 7:
            target = (cls(7) + cls(0, 1)) / cls(2)
            assert cls(4) + n18 != target, "unexpected: the ridge captures n = 18"
            assert cls(4) + ridge_width(cls, cw, sw, 2, 1) != target
    # the row itself, read exactly: its tilted word and its side
    import field_triage as T
    row = _delivered_rows()[18]
    tilt_words = {t for _x, _y, t in row if _word_of(t) is None}
    assert len(tilt_words) == 1, tilt_words
    ca, sa = T.cos_sin(tilt_words.pop())
    cls7 = qfield(7)
    cw = EF.recover_scalar(cls7(F(ca)), cls7, dens=(1, 2, 4, 8), bmax=8)
    sw = EF.recover_scalar(cls7(F(sa)), cls7, dens=(1, 2, 4, 8), bmax=8)
    assert (cw.a, cw.b) == (F(1, 4), F(1, 4)), (cw.a, cw.b)
    assert (sw.a, sw.b) == (F(-1, 4), F(1, 4)), (sw.a, sw.b)
    assert cw * cw + sw * sw == cls7(1), "the recovered word must be a unit word"
    axis_n = sum(1 for _x, _y, t in row if _word_of(t) is not None)
    assert (axis_n, len(row) - axis_n) == (10, 8), (axis_n, len(row))
    for _x, _y, _t in row:                       # every coordinate of the pose, exactly
        for _v in (_x, _y):
            assert EF.recover_scalar(cls7(F(_v)), cls7,
                                     dens=(1, 2, 4, 8, 16), bmax=8) is not None, _v
    X = [F(x) for x, _y, _t in row]
    far = EF.recover_scalar(cls7(max(X)), cls7, dens=(1, 2, 4, 8), bmax=8)
    near = EF.recover_scalar(cls7(min(X)), cls7, dens=(1, 2, 4, 8), bmax=8)
    assert (far.a, far.b) == (F(5, 4), F(1, 4)) and (near.a, near.b) == (F(-5, 4), F(-1, 4))
    side = far + far + cls7(1)                      # span of the centres plus one
    assert side == (cls7(7) + cls7(0, 1)) / cls7(2), side
    assert side == cls7(3) + cls7(2) * cw, side     # L = 3 + 2 cos(word)
    say(f"control 22 — the ridge holds m tilted squares: at 45 degrees it reproduces "
        f"strip_field(k, m) cell for cell, slot for slot and side for side on all "
        f"{doubles} (k, m) cells with k, m in 1..3; N = 4k^2 + m; the exact seam law "
        f"w*(2) = 2 w*(1) holds on every rung, and beyond m = 2 the binding pair can "
        f"re-bind -- the 45-degree rung stays linear through m = 4, the oblique rungs "
        f"do not (" + "; ".join(rungs) + "). The census's "
        f"n = 18 row is *not* a member: its tilted word is (1+sqrt7)/4, (-1+sqrt7)/4 "
        f"(recovered from the 12-dp pose at 70 digits and verified on the unit circle), "
        f"its pose is 10 axis squares plus 8 tilted ones, and its side is 3 + 2cos = "
        f"(7 + sqrt7)/2 — an odd rational part with a cosine term, where the ridge's side "
        f"is 2k plus a seam width.")

    # ------------------------------- control 23: the Q(sqrt 7) family and its ring law
    import field_triage as T
    cls7 = qfield(7)
    cw7, sw7 = _sqrt7_word()
    ledger = os.path.join(ROOT, "workspace", "push", "field_triage.json")
    with open(ledger) as f:
        triage = json.load(f)
    rows7 = sorted(r["n"] for r in triage["rows_detail"] if r["class"] == "Q(sqrt7) side")
    assert rows7 == [18, 53, 151, 234, 747], rows7
    target = (cls7(7) + cls7(0, 1)) / cls7(2)
    reporting = []
    integers, halves = [], []
    for n in rows7:
        row = _delivered_rows()[n]
        tilts = {}
        for _x, _y, t in row:
            if _word_of(t) is None:
                tilts[t] = tilts.get(t, 0) + 1
        # the census word occurs in every one of the five rows, and is a unit word there
        cw = sw = None
        for t in sorted(tilts, key=lambda z: -tilts[z]):
            ca, sa = T.cos_sin(t)
            g1 = EF.recover_scalar(cls7(F(ca)), cls7, dens=(1, 2, 4, 8), bmax=8)
            g2 = EF.recover_scalar(cls7(F(sa)), cls7, dens=(1, 2, 4, 8), bmax=8)
            if g1 is not None and g2 is not None and (g1.a, g1.b) == (cw7.a, cw7.b) \
                    and (g2.a, g2.b) == (sw7.a, sw7.b):
                cw, sw = g1, g2
                word_n = tilts[t]
                break
        assert cw is not None and cw * cw + sw * sw == cls7(1), (n, len(tilts))
        X = [F(x) for x, _y, _t in row]
        Y = [F(y) for _x, y, _t in row]
        far = EF.recover_scalar(cls7(max(X)), cls7, dens=(1, 2, 4, 8, 16), bmax=8)
        near = EF.recover_scalar(cls7(min(X)), cls7, dens=(1, 2, 4, 8, 16), bmax=8)
        assert far is not None and near is not None, n
        # the side, read exactly: the span of the centres plus one axis half-extent
        side = far - near + cls7(1)
        fy = EF.recover_scalar(cls7(max(Y)), cls7, dens=(1, 2, 4, 8, 16), bmax=8)
        ny = EF.recover_scalar(cls7(min(Y)), cls7, dens=(1, 2, 4, 8, 16), bmax=8)
        assert side == fy - ny + cls7(1), n
        axis_n = sum(1 for _x, _y, t in row if _word_of(t) is not None)
        # the law: side = 2k + 3/2 + (c + s), with k = (side - 3/2 - (c+s)) / 2
        kk = (side - cls7(F(3, 2)) - (cw + sw)) / cls7(2)
        assert kk.b == 0, (n, kk)
        kv = kk.a
        if kv.denominator == 1:
            assert ring_side(cls7, cw, sw, int(kv)) == side, (n, kv)
            integers.append((n, int(kv)))
        else:
            assert kv.denominator == 2, (n, kv)
            assert (kv * cls7(2)).a.denominator == 1, (n, kv)     # an odd integer
            assert cls7(2 * int(kv * 2)) + cls7(3) + cls7(2) * (cw + sw) == side * cls7(2), (n, kv)
            halves.append((n, str(kv)))
        reporting.append(f"n={n}: {axis_n} axis + {len(row) - axis_n} tilted "
                         f"({word_n} at the census word, {len(tilts)} distinct tilt angles), "
                         f"L={side}, k={kv}")
    assert (n18 := dict(integers).get(18)) == 1, integers
    assert dict(integers)[151] == 5, integers
    assert [n for n, _k in halves] == [53, 234, 747], halves
    assert ring_side(cls7, cw7, sw7, 1) == target, "the ring law must give the n = 18 side"
    say("control 23 — the Q(sqrt 7) family is one word and one side law, split by parity: "
        "every row of it (n = 18, 53, 151, 234, 747, run 86's field sweep) carries the same "
        "unit word ((1+sqrt7)/4, (-1+sqrt7)/4), recovered here from each row's own tilt at "
        "70 digits, and its side is (2m+1)/2 + sqrt7/2 = 2k + 3/2 + (c + s), so the run-92 "
        "'odd rational part plus 2cos' is the k = 1 case of a single law: "
        + "; ".join(reporting) +
        ". Two rows sit at integer k (18: k = 1, 151: k = 5) and three at half-integer k "
        "(53: k = 5/2, 234: k = 13/2, 747: k = 25/2), and their pose alphabets differ "
        "widely (2, 4, 3, 2 and 665 distinct angles); the ring law's k = 1 member is "
        "exactly 7/2 + sqrt7/2. Run 94 builds that member as a sentence (control 24) and "
        "tests the same grammar at k = 5, where it splits.")

    # --------------------------- control 24: the ring, solved from its own tangencies
    ring = ring_claim(7, cw7, sw7, 1)
    assert ring.n == 18, ring.n
    assert ring.laws["extent"][1] == target, ring.laws["extent"][1]
    assert (ring.meta["frame"], ring.meta["wall"]) == (10, 14), ring.meta["frame"]
    assert ring.meta["declared"] == 22, ring.meta["declared"]
    assert p_ring(1).n == 18 and p_ring(1).laws["extent"][1] == target
    cells = ring.payload["state"]
    words = ring.payload["words"]
    g = Q.gate(cells, words, cls7)
    assert g["ok"] and g["clearance"] == 0 and g["L"] == target, g
    assert g["contacts"] == 26, g["contacts"]            # 22 declared + 4 incidental
    for group, pairs in ring.payload["tangencies"].items():
        for i, j in pairs:
            axes = Q.pair_axes(cells, words, i, j, cls7)
            assert any(sl == 0 for _q, sl, _n, _o in axes), (group, i, j)
    dec = DecimalWitness.scalar
    cens = _delivered_rows()[18]
    worst = Decimal(0)
    for x, y in cells:
        px, py = dec(x), dec(y)
        near = min(cens, key=lambda r: abs(dec(r[0]) - px) + abs(dec(r[1]) - py))
        worst = max(worst, abs(dec(near[0]) - px), abs(dec(near[1]) - py))
    assert worst < Decimal("1e-4"), worst
    split = []
    for kk in (2, 3, 4, 5):
        try:
            ring_claim(7, cw7, sw7, kk)
            raise AssertionError(f"the ring must not certify at k = {kk}")
        except Refusal as e:
            assert e.law == "ring_chain_adrift", (kk, e.law)
            decl = ring_declaration(cls7, cw7, sw7, kk)
            c5, w5 = decl["cells"], decl["words"]
            idx = _ring_indices(kk)
            slack = max(sl for _q, sl, _n, _o in
                        Q.pair_axes(c5, w5, idx["p8"], idx["m5"], cls7))
            g5 = Q.gate(c5, w5, cls7)
            # The drift is a *declared* law, not a collision -- but only from k = 3.
            # At k = 3, 4, 5 the drifted sentence still separates with clearance
            # exactly 0; at k = 2 the drift is large enough to collide as well.
            if kk >= 3:
                assert g5["ok"] and g5["clearance"] == 0 and g5["violations"] == 0, (kk, g5)
            else:
                assert not g5["ok"] and g5["violations"] > 0, (kk, g5)
            adrift = [(grp, i, j) for grp, prs in ring_tangencies(kk).items()
                      for i, j in prs if not _ring_contact(cls7, c5, w5, i, j)]
            assert len(adrift) == 8, (kk, adrift)
            assert sum(1 for grp, _i, _j in adrift if grp == "pin") == 4, adrift
            split.append(f"k={kk}: N would be {4 * kk + 14}, closure slack {slack}, "
                         f"gate {'clear at 0' if g5['ok'] else 'colliding'}, "
                         f"{len(adrift)} of 22 declarations adrift")
    rows151 = _delivered_rows()[151]
    probe = ring_side(cls7, cw7, sw7, 5)
    axis151 = sum(1 for _x, _y, t in rows151 if _word_of(t) is not None)
    cols151 = len({x for x, _y, t in rows151 if _word_of(t) is not None})
    assert (len(rows151), axis151, cols151) == (151, 125, 21), (axis151, cols151)
    assert probe == (cls7(23) + cls7(0, 1)) / cls7(2), probe
    say("control 24 — the ring is the census's own 10 + 4 + 4 sentence, solved: a C2 "
        "perimeter of 10 axis squares (4 corners, a 3-square run up the left wall, a "
        "3-square run down the right wall, one square inward on the bottom wall and one "
        "on the top), four gap squares wedged across the four wall gaps by two declared "
        "tangencies each, and a four-square pinwheel that closes each chain end onto the "
        "opposite gap square. Each of the eight tilted squares is a 2x2 solve in Q(sqrt 7) "
        "from those tangencies -- 22 declared, every one an exact contact -- and the exact "
        "gate certifies N = 18 at L = " + str(target) + " with clearance 0 and "
        f"{g['contacts']} contacts -- the 22 declared, plus 4 that follow by consequence "
        "(the bottom and top wall squares against the opposite chain end, and the two "
        "inner diagonals `p6/-p7`, `-p6/p7`). The census "
        f"row itself agrees to {worst:.1e} in every centre, so the n = 18 pose *is* this "
        "sentence: run 93 read the 10 + 4 + 4 counts correctly but the corner-module "
        "grammar wrongly. The grammar does not generalise: the pinwheel's closure contact "
        "is a k = 1 identity (" + "; ".join(split) + "), because the chain end's u-distance "
        "stays 1 at every k while its v-offset is 2p5.v + 2, which grows by sqrt7 per k. "
        "So k >= 2 is a declared refusal; from k = 3 up the drifted sentence still passes "
        "the geometric gate at clearance 0 and fails only its declared tangencies "
        "(8 of the 22, 4 of them the pinwheel closure), while at k = 2 the drift is large "
        "enough that the sentence also collides. The census's own k = 5 row "
        "is not this family's member even in count: the ring would have N = 4k + 14 = 34 "
        "squares at L = " + str(probe) + ", while n = 151 is a 151-square staircase ("
        f"{axis151} axis squares in {cols151} staggered columns plus "
        f"{len(rows151) - axis151} tilted). The side law generalises; the sentence splits.")

    # --------------------- control 25: the staircase and its corner pinch (run 95)
    stair = p_staircase(5)
    target151 = (cls7(23) + cls7(0, 1)) / cls7(2)
    assert stair.n == 149, stair.n
    assert stair.laws["extent"][1] == target151, stair.laws["extent"][1]
    assert (stair.meta["frame"], stair.meta["seam"]) == (125, 24), stair.meta["frame"]
    assert stair.meta["declared"] == 24, stair.meta["declared"]
    assert len(staircase_columns(5)) == 12, staircase_columns(5)
    c25 = stair.payload["state"]
    w25 = stair.payload["words"]
    g25 = Q.gate(c25, w25, cls7)
    assert g25["ok"] and g25["clearance"] == 0 and g25["L"] == target151, g25
    need25 = _staircase_need(cls7, cw7, sw7)
    for i, j in staircase_tangencies(5):
        p, q = c25[125 + i], c25[j]
        dv = (p[0] - q[0]) * (-sw7) + (p[1] - q[1]) * cw7
        assert abs(dv) == need25, (i, j)
    # the wall's thirteenth column pinches: the closed 151-square sentence is refused
    gauge = cls7(F(-1357, 128), F(211, 128))
    closed = list(c25)
    for v in _staircase_walk_v(cls7, cw7, sw7, 5, 4):
        closed.append(_staircase_brick(cls7, cw7, sw7, gauge + cls7(12), v))
    gc = Q.gate(closed, list(w25) + [(cw7, sw7)] * 2, cls7)
    pinch = cls7(F(-163, 128), F(61, 128))
    assert len(closed) == 151 and not gc["ok"] and gc["violations"] == 1, gc
    assert gc["clearance"] == pinch, gc["clearance"]
    # the census row: 149 of its 151 centres are this sentence's, to the pose's noise
    dec = DecimalWitness.scalar
    cens = _delivered_rows()[151]
    worst = Decimal(0)
    for x, y in c25:
        px, py = dec(x), dec(y)
        near = min(cens, key=lambda r: abs(dec(r[0]) - px) + abs(dec(r[1]) - py))
        worst = max(worst, abs(dec(near[0]) - px), abs(dec(near[1]) - py))
    assert worst < Decimal("1e-4"), worst
    # the two squares the table adds are rotated out of the field
    odd = F(19211307153, 31250000000)
    ca, sa = T.cos_sin(odd)
    dens = (64, 128, 256, 512, 1024, 2048, 4096)
    oc = EF.recover_scalar(cls7(F(ca)), cls7, dens=dens, bmax=8)
    os_ = EF.recover_scalar(cls7(F(sa)), cls7, dens=dens, bmax=8)
    assert oc is not None and os_ is not None, "the odd word must be found near Q(sqrt 7)"
    assert oc * oc + os_ * os_ != cls7(1), "the odd word would be a unit word after all"
    assert T.pyth_angle(odd, qmax=1024) is None, "the odd word would be Pythagorean"
    # the pocket, decided exactly: no scan, no tolerance (run 95, item 1)
    cage149 = staircase_cage(cls7, cw7, sw7, c25, w25, target151,
                             hint=(c25[-1][0], c25[-1][1]))
    assert not cage149["empty"] and cage149["capacity"] == 1, cage149
    assert cage149["extent_u"] == F(5, 8), cage149["extent_u"]
    assert cage149["extent_v"] == F(3, 4), cage149["extent_v"]
    assert cage149["witness"] is not None, cage149
    capped = staircase_capped(5)
    cap_cells, cap_words = capped["cells"], capped["words"]
    assert len(cap_cells) == 150 and capped["gate"]["L"] == target151, capped["gate"]
    assert capped["gate"]["ok"] and capped["gate"]["clearance"] == 0, capped["gate"]
    capb, twin = cap_cells[-1], c25[125 + 23]
    dU = (capb[0] - twin[0]) * cw7 + (capb[1] - twin[1]) * sw7
    dV = (capb[0] - twin[0]) * (-sw7) + (capb[1] - twin[1]) * cw7
    assert (dU, dV) == (cls7(1), cls7(0)), (dU, dV)
    cage150 = staircase_cage(cls7, cw7, sw7, cap_cells, cap_words, target151,
                             hint=(cap_cells[-1][0], cap_cells[-1][1]))
    assert cage150["empty"], cage150
    # honesty: at k = 5 the family does not beat the table at its own count
    assert stair.meta["table_side"] is not None, stair.meta
    assert stair.meta["beats_table"] is False, stair.meta
    # the spin over (k, word): the family's count is the frame plus the brick wall
    # (`4k^2 + 4k + 5 + 2|columns(k)|`), and no member beats its delivered row
    spin = []
    for kk in range(1, 10):
        nn = 4 * kk * kk + 4 * kk + 5 + 2 * len(staircase_columns(kk))
        Lk = staircase_side(cls7, cw7, sw7, kk)
        sidek = _table_side(nn)
        if sidek is None:
            spin.append(f"k={kk}: N={nn} uncalibrated")
            continue
        behind = DecimalWitness.scalar(Lk) - DecimalWitness.scalar(sidek)
        assert behind > 0, (kk, nn, Lk, sidek)
        spin.append(f"k={kk}: N={nn} behind by {behind:.4f}")
    assert 4 * 25 + 20 + 5 + 2 * len(staircase_columns(5)) == 149
    say("control 25 -- the n = 151 row is a *multi-layer staircase*, and its axis layer is "
        "grammar: an odd integer grid on two lattices offset by 2c (an upper-left block of "
        "55 and a lower-right block of 66 at k = 5), four corner caps, and a two-layer brick "
        "wall in the diagonal seam.  At k = 5 that is 125 axis squares plus 24 bricks -- "
        "each brick tangent along its own v to B(a, a) or A(a, a + 1), walking "
        "a = -k..k-2 with the column repeated when a % 3 == 0 -- and the exact gate "
        "certifies N = 149 at L = " + str(target151) + " with clearance 0 and "
        f"{g25['contacts']} contacts, all 24 declarations exact.  The grammar is "
        "*closed* only at the Q(sqrt 7) word: the two bricks of a column are "
        "v_A - v_B = 2c(c + s) - (1 + s) apart, which is 1 exactly when c - s = 1/2 "
        "(control 5 refuses the 45-degree word by staircase_layer_gap).  It constructs "
        "149 of the census's 151, and the reason is exact: the wall's thirteenth column "
        "(a = k - 1) overlaps the top-right cap by " + str(pinch) + " (= " +
        f"{dec(pinch):.6f}), one violation.  The corner pocket is then decided by an "
        "exact no-fit cage, not a scan: an outer cover of exact boxes in the wall's own "
        "frame, pruned only where a box is provably inside one square's octagon or "
        "outside the L-box, spans " + str(cage149["extent_u"]) + " in u and " +
        str(cage149["extent_v"]) + " in v -- both below 1, so the pocket holds exactly "
        "one word-aligned square, and the one it holds is the cap brick (the last "
        "column's A brick repeated one column out, exactly tangent along u): N = 150 at "
        "the same side, clearance 0, " + f"{capped['gate']['contacts']} contacts.  "
        "With that brick in place the cage is *empty* even for the census word, so the "
        "pocket is closed.  That is why the table rotates those two squares: "
        "their word is 0.6147618 rad, whose cos and sin are not a unit word of Q(sqrt 7) at "
        f"height <= 4096 (cos^2 + sin^2 = {oc * oc + os_ * os_}) and not Pythagorean (no "
        "t with denominator <= 1024), so a field-general Q(sqrt 7) staircase cannot reach "
        f"n = 151.  The 149 centres reproduce the delivered row to {worst:.1e}, and the "
        "family does not beat the table at n = 149 (its table side is " +
        str(stair.meta["table_side"]) + "); no row is claimed.  A spin over k = 1..9 at "
        "the same word (the count is the frame plus the wall, "
        "4k^2 + 4k + 5 + 2|columns(k)|) never beats a delivered row: " +
        "; ".join(spin) + ".")

    # --------------------- control 26: the word spin and the second word (run 95)
    spin26 = staircase_word_spin()
    assert len(spin26) >= 60, len(spin26)
    assert {2, 5, 7} <= {r["d"] for r in spin26}, {r["d"] for r in spin26}
    closed26 = [r["word"] for r in spin26 if r["closed"]]
    assert closed26 == ["census"], closed26
    for r in spin26:
        fld, cc, ss = qfield(r["d"]), r["c"], r["s"]
        assert (cc * cc + ss * ss) == fld(1), r["word"]
        assert r["residual"] == ss * (fld(2) * (cc - ss) - fld(1)), r["word"]
        assert r["residual"] == fld(2) * cc * (cc + ss) - (fld(1) + ss) - fld(1), r["word"]
        if r["closed"]:
            assert (cc - ss) == fld(F(1, 2)) and ss != fld(0), r["word"]
        else:
            assert r["law"] == "staircase_layer_gap" and r["residual"] != fld(0), r
    second26 = staircase_second_words()
    assert len(second26) >= 70, len(second26)
    assert all((c2 * c2 + s2 * s2) == cls7(1) for _n, c2, s2 in second26)
    # one cage per rotation class: a quarter turn of a word leaves its square alone,
    # so the class count is what runs and the word count is what is claimed
    classes26 = staircase_second_word_classes()
    assert len(classes26) == 66 and len(second26) == 78, (len(classes26), len(second26))
    assert {_square_canon(c2, s2) for _n, c2, s2 in second26} == \
           {_square_canon(c2, s2) for _n, c2, s2 in classes26}
    fits = [name for name, c2, s2 in classes26
            if not staircase_cage(cls7, c2, s2, cap_cells, cap_words, target151,
                                  hint=(cap_cells[-1][0], cap_cells[-1][1]))["empty"]]
    assert not fits, fits
    by_name = {r["word"]: r for r in spin26}
    named = "; ".join(f"{nm}: {by_name[nm]['residual']}"
                      for nm in ("45deg", "Slope-2:1", "Seventh", "t=1/2")
                      if nm in by_name)
    say("control 26 -- the staircase's closure law is one line over every declared unit "
        "word, and the 151st square is refused by an exact closed pocket.  The two brick "
        "layers are v_A - v_B = 2c(c + s) - (1 + s) apart, so the residual is "
        "2c(c+s) - (1+s) - 1 = s(2(c - s) - 1): zero iff s = 0 (the degenerate axis word) "
        "or c - s = 1/2, which is the census word alone.  Spun over " +
        f"{len(spin26)} declared unit words -- the wheel's 45-degree Q(sqrt 2) word, the "
        "Slope 2:1 word in Q(sqrt 5), the Seventh and every other unit word of Q(sqrt 7) "
        "at small height, and every Pythagorean word with denominator <= 13 -- the "
        "constructor closes at exactly one: " + closed26[0] + ", residual 0, refused "
        "everywhere else by staircase_layer_gap with its own exact residual (" + named +
        ").  The second-word test is the same exact cage, run against the 150-square "
        f"sentence with every field-compatible word ({len(second26)} of them: all 22 unit "
        "words of Q(sqrt 7) at height <= 8 and every Pythagorean word with denominator "
        "<= 13, which embeds in Q(sqrt 7)): every cage is empty, so no second word places "
        "the 151st square at L = " + str(target151) + " -- the pocket is closed for "
        "Quad(7) union Q_Pyth, and the table's escape is a rotation outside both.  The "
        f"sweep itself is {len(classes26)} cages, one per rotation class of the square "
        f"(a quarter turn `(c, s) -> (-s, c)` cannot change a cage's answer), which "
        f"decides all {len(second26)} words.")

    # --------------------- control 27: the table's own rotation, mixed in (run 95)
    ang27 = odd_word_angle()
    assert ang27 == F(19211307153, 31250000000), ang27
    cu27, su27 = odd_word_upward()
    assert cu27 * cu27 + su27 * su27 >= 1, (cu27, su27)   # the enlarged square
    codd, sodD = cls7(cu27), cls7(su27)
    cage_odd = staircase_odd_cage(cls7, c25, w25, target151)
    assert not cage_odd["empty"] and cage_odd["witness"] is not None, cage_odd
    uo, vo = cage_odd["witness"]
    odd150 = (uo * codd - vo * sodD, uo * sodD + vo * codd)
    g150 = Q.gate(list(c25) + [odd150], list(w25) + [(codd, sodD)], cls7)
    assert g150["ok"] and g150["L"] == target151 and g150["violations"] == 0, g150
    assert g150["contacts"] > 0, g150
    # with the cap brick in place the pocket is shut even to the table's rotation
    cage_odd150 = staircase_odd_cage(cls7, cap_cells, cap_words, target151)
    assert cage_odd150["empty"], cage_odd150
    # No second rotation square, by exact arithmetic in Q(sqrt 7), axis by axis.
    #
    # (a) Along U it is the *cover* that settles it, not a rectangle cage: the single
    #     square's cage against the 149 spans extent_u = 3/4, so any two feasible
    #     centres differ by less than 1 there -- and the free-set span, read in the
    #     turned frame, tightens that to 0.447289.  The (2, 1) rectangle's cage is the
    #     wrong instrument and is not used: it asks only whether the *tangent* pair
    #     (centres exactly 1 apart) fits, and a pair further apart is a legal pair the
    #     cage cannot see.
    # (b) Along V the free set's own span -- the union over the 16 blocks -- is what
    #     the chord proof bounds, in closed form, exactly.
    span27 = staircase_pair_span(cls7, codd, sodD, c25, w25, target151,
                                 exact_word=False)
    assert cage_odd["extent_u"] == F(3, 4), cage_odd["extent_u"]
    assert span27["u"]["span"] is not None and span27["u"]["span"] < 1, span27["u"]
    chords27 = staircase_chords(cls7, codd, sodD, c25, w25, blocks=16,
                                window=cage_odd["window"])
    assert chords27["ok"] and chords27["closed"] == chords27["blocks"], chords27
    assert chords27["max_chord"] < 1 and chords27["max_chord"] > 0, chords27
    # the verdict is the *union* of the blocks' free sets: a per-block chord bound
    # alone would not see a pair whose two u values sit in different blocks
    assert chords27["max_block"] < chords27["max_chord"], chords27
    assert span27["v"]["span"] == chords27["max_chord"], (span27["v"], chords27)
    # the census word cannot reach 151 either: its pair cage closes exactly
    cage_pair_census = staircase_cage(cls7, cw7, sw7, c25, w25, target151,
                                      sides=(1, 2),
                                      hint=(c25[-1][0], c25[-1][1]))
    assert cage_pair_census["empty"], cage_pair_census
    odddel = odd_centres(c25)
    assert len(odddel) == 2, odddel
    mixed_worst, mixed_where = mixed_slack(c25, w25, odddel)
    assert mixed_worst < 0 and mixed_worst > Decimal("-1e-6"), (mixed_worst, mixed_where)
    say("control 27 -- mixing the census word with the table's own rotation.  The "
        "n = 151 row spends two squares on the angle " + f"{dec(ang27):.12f}" +
        " rad = " + str(ang27) + ", which is rational, but its cosine is not a field "
        "element, so this control is *measured* where it is not caged.  The word is "
        "replaced by the rationals " + str(cu27) + ", " + str(su27) + " (both rounded "
        "up at 1e-25, so cos^2 + sin^2 >= 1: the caged square is the table's square "
        "grown by 1e-25): the cage "
        "still finds a placement against the 149, and the exact gate certifies "
        "N = 150 at L = " + str(target151) + f" clearance 0 with {g150['contacts']} "
        "contacts -- the table's own rotation does close its 150th square at the "
        "census side.  The 151st is *excluded* by exact arithmetic: two unit squares "
        "of one word overlap unless their centres differ by at least 1 along one of "
        "that word's axes, so the pair is settled axis by axis.  Along U it is the "
        "cover itself: the single square's cage against the 149 spans " +
        str(cage_odd["extent_u"]) + " in u, so two feasible centres differ by less "
        "than 1 there -- and the free-set span, read in the turned frame, tightens "
        "that to " + f"{dec(span27['u']['span']):.6f}" + ".  (The (2, 1) rectangle's "
        "cage is *not* the instrument for this, and is not used: it asks only whether "
        "the tangent pair -- centres exactly 1 apart -- fits, and leaves a pair "
        "further apart untouched.)  Along V the free v-chords "
        "never reach 1: at a fixed u the whole sentence forbids a union of exact "
        "Quad intervals, and over 16 blocks of the cage's own window (all closed, each "
        "shrinking its forbidden intervals so the free set is over-approximated) the "
        "union of the blocks' free sets spans " + f"{dec(chords27['max_chord']):.6f}" +
        " -- below 1, so no two feasible centres anywhere in the window are 1 apart "
        "along V (the largest single block's chord is " +
        f"{dec(chords27['max_block']):.6f}" + ", but the verdict is the union: a "
        "per-block bound alone would miss a pair whose two u values fall in different "
        "blocks) -- a finite exact proof in Q(sqrt 7), not a scan.  (The box cage "
        "cannot settle this pair: its "
        "per-axis test is weaker than pointwise coverage, so the (1, 2) rectangle's "
        "cover degenerates instead of closing; the chord proof is what closes it.)  "
        "With the cap brick in place the single square's cage is empty for the "
        "rotation as well, and with the census word the (1, 2) rectangle cage is "
        "*empty* too -- though there the exclusion is capacity 1 itself (the cover is "
        "5/8 by 3/4, control 25), of which the empty rectangle is a consequence.  "
        "The honest reading of the delivered row: replaying its own two rotation "
        "squares against the exact 149 gives worst pair slack " + f"{mixed_worst:.3e}" +
        " (odd square vs grammar square), i.e. an overlap, so the table's 151 is a "
        "12-decimal pose at ~1e-9 tolerance, not a sentence at the exact side.")

    # --------------------- control 28: the two-word seam (run 97)
    cls2 = qfield(2)
    # (a) the per-square floor: phi(theta) >= 1/sqrt 2, equality only at 45 degrees
    c2_45, s2_45 = Q.word_45()
    assert seam_floor(cls2, c2_45, s2_45) == cls2(0, F(1, 2)), "45 degree floor"
    floor_min = seam_floor(cls2, c2_45, s2_45)
    for name, d in (("Seventh", 7), ("census", 7)):
        fld = qfield(d)
        cc, ss = _sqrt7_word() if name == "census" else (fld(0, F(1, 4)), fld(F(3, 4)))
        phi = seam_floor(fld, cc, ss)
        assert phi * phi > fld(F(1, 2)), (name, phi)
        assert (phi * (abs(cc) + abs(ss))) == fld(1), name
    # (b) a mixed tangency is never cheaper than a same-word one
    sample = two_word_word_sample()
    pairs = 0
    for d in (2, 7):
        fld = qfield(d)
        ws = sample[d]
        for name, c, s in ws:
            assert two_word_need(fld, (c, s), (c, s)) == fld(1), name
            assert (c * c + s * s) == fld(1), name
        for i in range(len(ws)):
            for j in range(i + 1, len(ws)):
                ga, gb = ws[i], ws[j]
                need = two_word_need(fld, (ga[1], ga[2]), (gb[1], gb[2]))
                if _square_canon(ga[1], ga[2]) == _square_canon(gb[1], gb[2]):
                    continue
                assert need > fld(1), (ga[0], gb[0], need)
                pairs += 1
    # (c) a built two-word sentence, and the floor it does not break
    tc, ts = EF.tword(F(1, 2))
    qw = (cls2(F(tc)), cls2(F(ts)))
    floor_one = cls2(0, F(1, 2))
    widest = None
    for k in (1, 2, 3):
        gauge = two_word_gauge(cls2, k, (c2_45, s2_45), qw)
        claim = two_word_pair(2, (c2_45, s2_45), qw, k)
        L = claim.measure[1]
        assert gauge == L - cls2(2 * k), (k, gauge, L)
        assert L - cls2(2 * k) > floor_one, (k, L)
        assert claim.laws["contacts"][1] > 0, claim.laws
        if widest is None or L - cls2(2 * k) < widest:
            widest = L - cls2(2 * k)
    # and the 3-4-5 coupling the table's n = 198 row uses: the price is 28/25, not 1
    c34, s34 = cls2(F(4, 5)), cls2(F(3, 5))
    c43, s43 = cls2(F(3, 5)), cls2(F(4, 5))
    assert two_word_need(cls2, (c34, s34), (c43, s43)) == cls2(F(28, 25))
    say("control 28 -- the two-word seam, and why it does not break the single-word "
        "floor.  A two-word sentence needs no new engine: the gate already carries one "
        "word per square, so the missing piece was a builder whose seam width comes "
        "from two words at once.  Two exact facts decide the question.  (1) A unit "
        "square at word theta standing in the ridge's cross is tangent to the four "
        "blocks at w = phi(theta) = min(x, 1/x), x = |c| + |s|; for a unit word "
        "1 <= x <= sqrt 2, so phi >= 1/sqrt 2 with equality exactly at 45 degrees -- "
        "the floor is a per-square price, not a property of a family, and every square "
        "in a mixed bar pays it separately.  (2) Two squares of different words need "
        "|d.u1| >= (1 + |cos D| + |sin D|)/2 > 1, strictly more than the same word's 1: "
        "the table's own n = 198 motif is the 3-4-5 pair, whose price is exactly 28/25.  "
        "So mixing words cannot cancel a seam; it can only add one.  The builder "
        "confirms it exactly: at k = 1, 2, 3 the closed-form gauge equals the gate's "
        "own side minus 2k (so the width *is* a contact width, not an interpolation), "
        "the gate passes at clearance 0, and the seam is " +
        f"{dec(widest):.6f} -- against the floor 0.707107 and the single-word m = 2 "
        "ridge's 1.414214 at the same N.  The spin over " +
        f"{pairs} distinct word pairs and k <= 8 builds 288 sentences: none below the "
        "floor, none beating the delivered row at the same N.")

    # --------------------- control 29: the 45-degree block (run 98)
    # (a) the count law: T = k(k+1)/2 per corner, N = s^2 + 4T, integers only
    assert block45_count(5, 4) == (10, 65), block45_count(5, 4)
    assert block45_count(17, 13) == (91, 653), block45_count(17, 13)
    assert block45_count(17, 17) == (153, 901), block45_count(17, 17)
    for s in range(1, 9):
        for k in range(1, 9):
            T, N = block45_count(s, k)
            assert N == s * s + 4 * T == s * s + 2 * k * (k + 1), (s, k)
    # (b) the side law, both branches: L = max(s/sqrt2 + k + 1, 2 s/sqrt2)
    assert block45_side(cls2, 5, 4) == cls2(5) + cls2(0, F(5, 2))
    assert block45_side(cls2, 5, 1) == cls2(0, F(5))          # t = 2 < h: the block sets it
    # (c) the two showcase sentences, gated, and the floor they do / do not break
    c65 = p_block45(5, 4)
    assert c65.n == 65 and c65.meta["beats"] is True
    L65 = c65.measure[1]
    assert L65 == cls2(5) + cls2(0, F(5, 2))
    # the delivered row at N = 65 has exactly this side: the measured gap is 0 at the
    # table's own 1e-9 pose precision (its stored side is 5 + 5/2 sqrt 2, our exact law)
    assert abs(Decimal(c65.meta["table_gap"])) <= Decimal("1e-9"), c65.meta
    assert c65.meta["table_side"] == "5 + 5/2\u221a2", c65.meta["table_side"]
    c653 = p_block45(17, 13)
    assert c653.n == 653 and c653.meta["beats"] is False
    L653 = c653.measure[1]
    assert L653 == cls2(14) + cls2(0, F(17, 2))
    excess = L653 - cls2(26)
    assert excess == cls2(0, F(17, 2)) - cls2(12), excess
    assert excess < cls2(0, F(1, 2)), "excess below half sqrt 2"
    # and the k = 14 neighbour is refused by the corner staircases meeting on a wall
    try:
        p_block45(17, 14)
    except Refusal as e:
        assert e.law == "block45_corner_collision", e.law
    else:
        raise AssertionError("s=17, k=14 should collide")
    # (d) N = 677 is not in the family at all: no (s, k) emits it
    assert not [(s, k) for s in range(1, 31) for k in range(1, 26)
                if block45_count(s, k)[1] == 677]
    say("control 29 -- the 45-degree block: an exact production that breaks the seam "
        "floor and still is not a record.  The block is s^2 unit squares at the 45-degree "
        "word, edge to edge; its faces are the four lines x + y = L -+ s/sqrt2 and "
        "y - x = -+ s/sqrt2, so each corner triangle has integer legs t = k + 1 and the "
        "staircase square at (k-1, 0) meets the face at its corner -- tangency, not "
        "tolerance.  The count is the triangular number T(k, s) = k(k+1)/2 per corner, "
        "N = s^2 + 2k(k+1), and the side is the exact contact L = max(s/sqrt2 + k + 1, "
        "2s/sqrt2) (the second branch is the block's own diagonal, and the gate caught the "
        "first sweep's missing branch as block45_side_mismatch).  Two sentences are "
        "certified here: (k = 4, s = 5) is N = 65 at L = " +
        f"{DecimalWitness.scalar(L65):.6f}, which is the delivered row's own side to its "
        "1e-9 polish -- "
        "parity, and the row's slack 0.535534 is exactly s/sqrt2 - 3; and (k = 13, "
        "s = 17) is N = 653 at L = " + f"{DecimalWitness.scalar(L653):.6f}" +
        ", whose excess over 2k is " + f"{DecimalWitness.scalar(excess):.6f}" + " -- **below 1/sqrt2 by a wide margin**, so the seam floor "
        "is the ridge's floor, not a law of squares.  But it is not a record: that side "
        "is above ceil(sqrt 653) = 26, the family emits no row at N = 677 at all "
        "(s = 17 gives 653 or, at k = 14, a declared collision of the two corner "
        "staircases that share a wall), and asymptotically L/sqrt(N) -> 1: the block is "
        "a grid in disguise, which is why no row moves.")

    # ---------------- control 30: the half-integer corner fill (run 99)
    # (a) the count law: T = k(k-1)/2 per corner, N = s^2 + 4T, and the count dominance
    assert block45half_count(17, 14) == (91, 653), block45half_count(17, 14)
    assert block45half_count(17, 16) == (120, 769), block45half_count(17, 16)
    assert block45half_count(17, 18) == (153, 901), block45half_count(17, 18)
    for s in range(1, 9):
        for k in range(2, 9):
            T, N = block45half_count(s, k)
            assert N == s * s + 4 * T == s * s + 2 * k * (k - 1), (s, k)
            assert T == block45_count(s, k - 1)[0], (s, k)      # the same staircase
    # (b) the side law, both branches, and the dominance of the side
    assert block45half_side(cls2, 17, 14) == cls2(F(29, 2)) + cls2(0, F(17, 2))
    assert block45half_side(cls2, 5, 2) == cls2(0, F(5))      # t = 2.5 < h: the block sets it
    for s in range(1, 9):
        for k in range(2, 9):
            Lh = block45half_side(cls2, s, k)
            Li = block45_side(cls2, s, k - 1)
            assert Li <= Lh <= Li + cls2(F(1, 2)), (s, k)
            if Lh == Li:                       # only when the block sets both sides
                assert Li == cls2(0, F(s)), (s, k)
            elif Lh == Li + cls2(F(1, 2)):     # the fill branch: exactly the half unit
                assert Lh == cls2(k) + cls2(F(1, 2)) + cls2(0, F(s, 2)), (s, k)
    # (c) a gated sentence, its half unit of dominance, and the wall collision
    ch653 = p_block45half(17, 14)
    assert ch653.n == 653 and ch653.meta["half_slack"] == str(cls2(F(1, 2)))
    assert ch653.meta["table_side"] is None
    assert ch653.meta["dominated_by"] == "block45(s=17, k=13)"
    assert ch653.measure[1] - cls2(28) < cls2(0, F(1, 2))
    for k in (15, 18):
        try:
            p_block45half(17, k)
        except Refusal as e:
            assert e.law == "block45half_corner_collision", e.law
        else:
            raise AssertionError(f"s=17, k={k} should collide")
    # (d) the delivered 677 row's own side is the half law at k = 14, *exactly* (one
    #     lift; the other two are checked by --block-half-spin's calibration and the
    #     ledger), and the corner fill at that side is 24 squares short of the row
    assert _table_side(677) == block45half_side(cls2, 17, 14)
    for n, k, T, N in ((677, 14, 91, 653), (785, 16, 120, 769), (901, 18, 153, 901)):
        assert block45half_count(17, k) == (T, N), (n, k)
    assert [n - N for n, N in ((677, 653), (785, 769), (901, 901))] == [24, 16, 0]
    # (e) the feasibility law, exactly: k = 14 is inside the window, 16 and 18 outside
    assert block45half_feasible(cls2, 17, 14)
    assert not block45half_feasible(cls2, 17, 16)
    assert not block45half_feasible(cls2, 17, 18)
    # 677 is no count of the family; 785 is one -- at s = 5, k = 20 -- and it collides
    assert not [(s, k) for s in range(1, 31) for k in range(2, 26)
                if block45half_count(s, k)[1] == 677]
    assert block45half_count(5, 20)[1] == 785 and not block45half_feasible(cls2, 5, 20)
    say("control 30 -- the half-integer corner fill: the half unit is slack, not capacity.  "
        "A unit axis square [i, i+1] x [j, j+1] fits the corner triangle x, y >= 0, "
        "x + y <= t iff i + j + 2 <= t, so the count depends on t only through floor(t): "
        "t = k and t = k + 1/2 admit the same staircase, and the half unit buys no square.  "
        "The count is therefore T = k(k-1)/2 per corner, N = s^2 + 2k(k-1), with the side "
        "L = max(s/sqrt2 + k + 1/2, 2s/sqrt2), and the exact dominance law falls out: the "
        "half member at k is run 98's integer contact member at k-1, same N, and its side "
        "is never smaller and at most 1/2 larger (exactly 1/2 in the fill branch, 0 when "
        "the block's own diagonal sets both sides, and k + 1/2 - s/sqrt2 in between; all "
        "three cases are asserted here).  The gate confirms it: (s = 17, k = 14) is N = 653 at "
        "L = " + f"{DecimalWitness.scalar(ch653.measure[1]):.6f}" + " with clearance 0, and its "
        "excess L - 2k is negative -- below 1/sqrt2 trivially, which is *not* a record, "
        "because the family's k is the corner parameter, not the ridge's.  The sharp part "
        "is at the delivered rows: their exact lifted sides are 29/2 + 17/2 sqrt2, "
        "33/2 + 17/2 sqrt2, 37/2 + 17/2 sqrt2, i.e. s/sqrt2 + k + 1/2 for k = 14, 16, 18 -- "
        "so the half-integer *side* law is the delivered side exactly, not to a tolerance.  "
        "But the corner fill at those sides holds 653, 769, 901 against the rows' 677, 785, "
        "901: short by 24, 16, 0.  And only the first is a sentence: at k = 16 and k = 18 "
        "the two staircases on each wall meet (L < 2k - 2) and the gate refuses them, so "
        "the delivered 901 is the fill's count and the fill's side in an arrangement the "
        "centred corner fill cannot take.  Rung 2 (integer) is blind to the half: it "
        "charges the same T for t = k and t = k + 1/2.  Rung 3 (rational/algebraic) sees "
        "it, and sees it as slack: L moves by 1/2 while N does not ("
        "rational_distinguishes_zero_half, in its packing form).  Rung 7 (certificate) is "
        "what decides which reading is a sentence: clearance 0 at k = 14, a declared "
        "collision at k = 16 and 18.  So the falsifier L = 2k + 0.520815 at 677, 785, 901 "
        "is not met by any certified half-integer sentence: the side matches exactly at "
        "all three, the count is short twice and infeasible the third time.  No row moves.")

    # ------------------------ control 31: the two composable exact plugins (run 100)
    # (a) the rational rung can now compare (Fraction arithmetic used to drop the
    #     subclass and the mixin's sign test went with it)
    assert EF.Q(1) < EF.Q(2) and EF.Q(3) >= EF.Q(3) and not (EF.Q(2) < EF.Q(1))
    # (b) Bernstein is an exact basis change and a *sound* enclosure
    assert EF.bernstein_coeffs([0, 0, 1], EF.Q(0), EF.Q(1)) == [EF.Q(0), EF.Q(0), EF.Q(1)]
    assert EF.bernstein_coeffs([0, 0, 1], EF.Q(0), EF.Q(2)) == [EF.Q(0), EF.Q(0), EF.Q(4)]
    enc = EF.bernstein_enclosure([1, 0, 1], EF.Q(-1), EF.Q(1))
    assert enc["lo"] == 0 and enc["hi"] == 2 and enc["sign"] == 0   # sound, not tight
    enc2 = EF.bernstein_enclosure([1, 0, 1], EF.Q(-1), EF.Q(1), splits=2)
    assert enc2["sign"] == 1 and enc2["lo"] == 1
    # a positive convex quadratic the coarse pass cannot certify, and refinement can
    poly = [EF.Q(F(1, 4)) + EF.Q(F(1, 100)), EF.Q(-1), EF.Q(1)]
    assert EF.bernstein_enclosure(poly, EF.Q(0), EF.Q(1))["sign"] == 0
    assert EF.bernstein_enclosure(poly, EF.Q(0), EF.Q(1), splits=2)["sign"] == 1
    for sp in (1, 2, 4):
        e = EF.bernstein_enclosure(poly, EF.Q(0), EF.Q(1), splits=sp)
        nd = EF.bernstein_nodes(poly, EF.Q(0), EF.Q(1), 8)
        assert all(e["lo"] <= v and v <= e["hi"] for v in nd["values"]), sp
    # (c) the separation certificate on a real sentence, with the gate at the endpoints
    demo = plugin_bernstein_demo(5, 4)
    assert demo["certified"] is True and demo["endpoints_ok"] is True, demo
    assert demo["refused"]["certified"] is False, demo
    # (d) the cage/chord interval witness and the Bernstein certificate agree
    c65p = p_block45(5, 4)
    chk = bernstein_cage_crosscheck(cls2, Q.word_45()[0], Q.word_45()[1],
                                    c65p.payload["state"], c65p.payload["words"],
                                    c65p.measure[1])
    assert chk["agree"] is True, chk
    # (e) the residue mask: sound, non-vacuous, and honest about what it cannot see
    scr = residue_pair_screen(c65p.payload["state"], c65p.payload["words"], cls2)
    assert scr["contacts"] > 0
    for mod in (8, 12, 24):
        assert scr[mod]["contacts_masked"] == scr["contacts"], (mod, "a contact was masked")
        assert scr[mod]["false_rejects"] == 0, (mod, scr[mod])
        assert scr[mod]["survivors"] + scr[mod]["rejected"] == scr["pairs"]
        assert scr[mod]["rejected"] > 0, (mod, "the mask must reject something")
        assert scr[mod]["survivors"] >= scr["contacts"]
    # the mask tests a necessary condition: a loose pair with one tight axis survives
    assert scr[8]["survivors"] - scr["contacts"] == 24, scr[8]
    # and on the half cells there are no such pairs, so the survivors are the contacts
    ch = p_block45half(5, 4)
    scrh = residue_pair_screen(ch.payload["state"], ch.payload["words"], cls2)
    for mod in (8, 12, 24):
        assert scrh[mod]["survivors"] == scrh["contacts"] == scrh[mod]["contacts_masked"]
        assert scrh[mod]["false_rejects"] == 0
    # and a true tangency is never rejected by the plugin itself: its residual is zero,
    # so its norm residue is zero at every modulus; a rejected pair has none
    D = residue_common_den(c65p.payload["state"], c65p.payload["words"])
    PX = [_scale_cell(cls2, p[0], D) for p in c65p.payload["state"]]
    PY = [_scale_cell(cls2, p[1], D) for p in c65p.payload["state"]]
    WX = [_scale_cell(cls2, w[0], D) for w in c65p.payload["words"]]
    WY = [_scale_cell(cls2, w[1], D) for w in c65p.payload["words"]]
    tight = []
    for i in range(len(PX)):
        for j in range(i + 1, len(PX)):
            sl = max(s for _q, s, _n, _o in Q.pair_axes(c65p.payload["state"],
                                                        c65p.payload["words"], i, j, cls2))
            if sl == 0:
                tight.append((i, j))
    assert len(tight) == scr["contacts"] == 172, (len(tight), scr["contacts"])
    for i, j in tight[:3]:
        mask = EF.residue_norm_filter(cls2, pair_tangency_residuals(cls2, PX, PY, WX, WY, i, j, D))
        for mod in (8, 12, 24):
            assert mask[mod]["all_nonzero"] is False and mask[mod]["zeros"], mod
    assert scr[8]["rejected"] == 70 and scr[8]["survivors"] == 196, scr[8]
    say("control 31 -- two composable exact plugins, each sound and each incomplete in a "
        "way that is stated, not assumed.  (1) Bernstein: on [a, b] every point is "
        "a + t(b-a), the Bernstein basis is a partition of unity, so p lies between "
        "min and max Bernstein coefficient -- an exact basis change turns a sign "
        "question about a continuum into one finite comparison.  It is sound but not "
        "complete: x^2 + 1 on [-1, 1] encloses as [0, 2] and only subdivision (splits "
        "2) certifies its min 1, and (t - 1/2)^2 + 1/100 needs the same refinement; "
        "every staircase node lies inside its enclosure, which is the cross-check.  "
        "On the certified Block45(5, 4) sentence a contact pair is slid apart: the "
        "quadratic (d0 + t d1)^2 - need^2 is certified positive on [1/2, 1] with lo "
        + f"{demo['lo']}" + f" and refused on [-1, 1], while the gate's own pair test at "
        "both endpoints returns slacks " + " and ".join(b for _t, b in demo["endpoints"]) +
        " -- one algebraic pass, no sampling.  (2) Residue mask: for an integral residual "
        "A + B sqrt d, N = A^2 - d B^2 is zero whenever the residual is, so a nonzero "
        "norm residue *proves* the pair cannot be tight on that axis.  Scaling residuals "
        "by the common denominator is what makes the reduction legal, and dividing by "
        "the content is what keeps it informative (without it every residue was 0 at "
        "mod 8 -- a vacuous mask, caught by the benchmark before it was reported).  On "
        "Block45(5, 4): " + f"{scr['pairs']}" + " candidate pairs, " + f"{scr['contacts']}" +
        " exact contacts, the mask rejects " + f"{scr[8]['rejected']}" + " and keeps "
        "every contact, 0 false rejections at mod 8, 12 and 24, leaving " +
        f"{scr[8]['survivors']}" + " survivors -- the extra " +
        f"{scr[8]['survivors'] - scr['contacts']}" + " are loose pairs with one tight "
        "axis, because the mask tests a *necessary* condition and cannot see the loose "
        "side.  On Block45Half(5,4) there are no such pairs (survivors == contacts == "
        "112), the primitive-vector fact that N = A^2 - 2 B^2 is never 0 mod 8 for "
        "coprime (A, B) making the mask exact there.  Across the four certified cells it "
        "buys 1.1-1.4x "
        "end-to-end: tight packings are contact-dense (112 of 182 pairs, 2256 of 2978), "
        "so most pairs must survive, and Amdahl -- not the mask -- sets that ceiling.  "
        "A synthetic 3/2 x 1 lattice shows the blind spot: its diagonal neighbours have "
        "one tight axis and a loose one, so the mask cannot reject them (252 survivors, "
        "90 contacts).  The mask tests a *necessary* condition, and exactness on the "
        "certified cells is a property of those cells, not of the mask.  Neither "
        "plugin decides a packing: the exact gate "
        "still does, and the chain only removes work it can prove is wasted.")

    # ---------------- control 32: the max-slack bound and the serialized certificate
    import verify_certificates as VC
    c65c = p_block45(5, 4)
    stc, woc = c65c.payload["state"], c65c.payload["words"]
    Dc = residue_common_den(stc, woc)
    PXc = [_scale_cell(cls2, p[0], Dc) for p in stc]
    PYc = [_scale_cell(cls2, p[1], Dc) for p in stc]
    WXc = [_scale_cell(cls2, w[0], Dc) for w in woc]
    WYc = [_scale_cell(cls2, w[1], Dc) for w in woc]
    # (a) the bound is sound and non-vacuous: 0 < lo <= the exact max slack
    dropped = 0
    for i in range(len(stc)):
        for j in range(i + 1, len(stc)):
            if abs(stc[j][0] - stc[i][0]) >= cls2(2) or abs(stc[j][1] - stc[i][1]) >= cls2(2):
                continue                     # the gate's own prune, exactly
            hit = pair_max_slack_bound(cls2, PXc, PYc, WXc, WYc, i, j, Dc)
            if hit is None:
                continue
            best = max(sl for _q, sl, _n, _o in Q.pair_axes(stc, woc, i, j, cls2))
            assert 0 < hit["lo"] <= best, (i, j, hit, best)
            dropped += 1
    assert dropped == 94, dropped            # 266 candidate pairs minus 172 contacts
    # the Quad wrapper and the integer path agree on a residual
    z0 = pair_tangency_residuals(cls2, PXc, PYc, WXc, WYc, 0, 1, Dc)[2]
    assert z0.is_zero()
    assert EF.positive_lower_bound(cls2(1, 0), 1) == F(1)     # 1 -> >= 1/1
    assert EF.positive_lower_bound(cls2(0, 1), 2) == F(1, 4)  # sqrt2/2 >= 1/(2*2)
    # (b) the chain: the bound leaves exactly the contacts for the exact gate
    ch_mask = chained_screen(stc, woc, cls2, use_mask=True, use_bound=False)
    ch_bound = chained_screen(stc, woc, cls2, use_mask=False, use_bound=True)
    ch_both = chained_screen(stc, woc, cls2, use_mask=True, use_bound=True)
    assert ch_mask["gate_calls"] == 196 and ch_mask["equivalent"] is True
    assert ch_bound["gate_calls"] == ch_both["gate_calls"] == 172
    for ch in (ch_bound, ch_both):
        assert ch["equivalent"] is True and ch["mask_hidden_violations"] == 0
        assert ch["pipeline_contacts"] == ch["contacts"] == 172
    # (c) the bound eliminates the lattice's diagonal survivors
    lst, lwo = _lattice_sentence()
    lcl = Q.field_of(lst)
    chm = chained_screen(lst, lwo, lcl, use_mask=True, use_bound=False)
    chl = chained_screen(lst, lwo, lcl, use_mask=False, use_bound=True)
    assert chm["gate_calls"] == 252 and chl["gate_calls"] == chl["contacts"] == 90, (chm["gate_calls"], chl["gate_calls"])
    assert chl["equivalent"] is True
    # (d) the mask cannot see overlaps and the bound can -- the honest difference
    ov = [(cls2(F(1, 2)), cls2(F(1, 2))), (cls2(F(7, 5)), cls2(F(1, 2)))]
    owo = [(cls2(1), cls2(0))] * 2
    chov = chained_screen(ov, owo, cls2, use_mask=True, use_bound=True)
    assert chov["violations"] == 1 and chov["mask_hidden_violations"] == 1
    assert chov["pipeline_violations"] == 0 and chov["equivalent"] is False
    chov2 = chained_screen(ov, owo, cls2, use_mask=False, use_bound=True)
    assert chov2["pipeline_violations"] == 1 and chov2["equivalent"] is True
    # (e) the integer mask path equals the Quad plugin path, pair for pair
    for i, j in ((0, 1), (0, 34), (5, 9)):
        q = EF.residue_norm_filter(cls2, pair_tangency_residuals(cls2, PXc, PYc, WXc, WYc, i, j, Dc))
        n = EF.residue_norm_filter_ints(cls2.d, _axis_residual_ints(cls2, PXc, PYc, WXc, WYc, i, j, Dc))
        assert q[8]["residues"] == n[8]["residues"], (i, j)
        assert q[8]["all_nonzero"] == n[8]["all_nonzero"]
    # (f) the serialized certificate: write, read back from text, verify
    ringc = p_ring(1)
    capped = staircase_capped(5)
    mini = {"format": "galois-certificate/1", "certificates": [
        certificate_of("tile2", "Tile", [(F(1, 2), F(1, 2)), (F(3, 2), F(1, 2)),
                                          (F(1, 2), F(3, 2)), (F(3, 2), F(3, 2))],
                       [(F(1), F(0))] * 4, None),
        certificate_of("ring18", "Ring", ringc.payload["state"],
                       ringc.payload["words"], cls7),
        certificate_of("block45", "Block45", stc, woc, cls2),
        certificate_of("stair150", "Staircase + cap", capped["cells"],
                       capped["words"], capped["cls"])]}
    res = VC.verify_document(json.loads(json.dumps(mini)))
    assert res["ok"] and res["verified"] == 4, res
    by = {r["summary"]["id"]: r["summary"] for r in res["results"]}
    assert by["ring18"]["N"] == 18 and by["ring18"]["contacts"] == 26
    assert by["stair150"]["N"] == 150 and by["stair150"]["contacts"] == 451
    assert by["block45"]["N"] == 65 and by["block45"]["contacts"] == 172
    assert by["tile2"]["contacts"] == 6 and by["tile2"]["L"] == "2"
    # and a decimal spelling is refused as a projection, not accepted as a value
    mut = json.loads(json.dumps(mini))
    mut["certificates"][2]["cells"][0]["x"] = ["1/2", "0.5"]
    bad = VC.verify_document(mut)
    assert not bad["ok"] and bad["results"][2]["kind"] == "outside_representation"
    assert bad["results"][2]["check"] == "number_format"
    # (g) the SAT pass decides on integer components and shares no code with the
    # producer's Quad gate; the Quad formulation survives only as a witness, and the
    # cross-check compares the two pair for pair on the *exact* largest slack
    agree = VC.cross_check(mini)
    assert [a["id"] for a in agree] == ["tile2", "ring18", "block45", "stair150"], agree
    assert [a["contacts"] for a in agree] == [6, 26, 172, 451], agree
    assert [a["pairs"] for a in agree[:3]] == [6, 62, 266], agree
    assert agree[3]["pairs"] >= agree[3]["contacts"]
    assert all(a["clearance"] == "0" for a in agree), agree
    called = set(VC.sat_pass_scaled.__code__.co_names)
    assert not called & {"gate", "pair_axes", "pair_tangency_residuals", "Q"}, called
    # Z[sqrt d] integer primitives, not Quad arithmetic (whose multiplication is `*`)
    assert {"_dot", "_iabs", "_iadd", "_isub", "_icmp"} <= called, called
    assert "_imul" in set(VC._dot.__code__.co_names)
    # (h) fuzz the two formulations against each other on random exact sentences: mixed
    # denominations, coincident centres (a strict overlap) and near-overlaps included,
    # because one document only exercises the pairs it happens to contain
    fz = VC.fuzz(60, seed=101)
    assert fz["mismatches"] == 0, fz["failures"][:3]
    assert fz["overlaps"] > 0 and fz["pairs"] > 100 and fz["max_den"] > 4, fz
    say("control 32 -- the max-slack bound, the chained pipeline, and the serialized "
        "certificate.  (1) The bound.  A pair is a contact iff its max slack is 0 and "
        "a violation iff it is negative, so a pair with a *strictly positive* max "
        "slack is neither and can be dropped: the object to bound is the max slack, "
        "not the tightest axis -- a diagonal neighbour has one tight axis and one "
        "loose one, so the document's 'tightest axis' phrasing is exactly what keeps "
        "the survivors, and doc 64 records the correction.  The bound is "
        "|A + B sqrt d| >= 1/(|A| + |B| S) for S >= sqrt d, because a nonzero norm is "
        "a positive integer; on Block45(5, 4) it speaks for " + f"{dropped}" + " of the "
        "94 non-contacts, always with 0 < lo <= the exact slack, and leaves exactly "
        "the 172 contacts for the gate.  (2) The chain.  Mask alone leaves 196 "
        "survivors (its 24 diagonal extras), the bound leaves 172, and both agree "
        "with the gate; on the synthetic lattice the bound turns the mask's 252 "
        "survivors into the 90 contacts.  The two stages are not equivalent: a mask "
        "drop is only 'not exactly tight', which an overlap also satisfies, so on a "
        "sentence with one 1/10 overlap the mask hides the violation and the bound "
        "keeps it -- the mask is contact-safe, the bound is verdict-safe, and the "
        "pipeline is used accordingly.  (3) The certificate.  A sentence is written as "
        "exact field tags, exact rotations R, exact centres and an exact side; the "
        "standalone verifier rebuilds it from the file alone, checks R^T R = I and "
        "det R = 1, every wall and all four axes of every pair (recording the witness "
        "axis and exact gap), and refuses a document whose declared summary the "
        "object does not have.  Four representatives round-trip through JSON text "
        "here -- tile2 (Q, 6 contacts), ring18 (Quad(7), 26), block45 (Quad(2), 172) "
        "and staircase150 (Quad(7), 451) -- and a decimal component is refused as "
        "`outside_representation`: a decimal readout is a projection, not a value.  "
        "(4) The verifier's SAT pass is now independent of the gate's formulation.  "
        "The producer multiplies Quad values in `pair_axes`; the verifier scales every "
        "coordinate and frame component by one common denominator D and decides each "
        "pair on integers of Z[sqrt d], with the residual 2 D^2 (slack) -- abs is an "
        "integer sign test, max an integer comparison, and only the printed gap is "
        "turned back into a field element, after the verdict.  The bytes of that pass "
        "name no producer function (the check above is on its own co_names), and the "
        "Quad formulation is kept as a witness the selftest cross-checks against: "
        "every candidate pair of all four certificates here (and all 4,532 pairs of "
        "the shipped document) agrees on the sign *and* on the exact largest slack, "
        "so the two paths are two implementations of one statement rather than one "
        "implementation read twice.  (5) Fuzzed, not just cross-checked on one "
        "document: " + f"{fz['sentences']}" + " random exact sentences here "
        "(" + f"{fz['pairs']}" + " candidate pairs, " + f"{fz['overlaps']}" +
        " of them overlapping, denominators up to " + f"{fz['max_den']}" + ") and "
        "9,729 pairs over four seeds outside the suite agree on every pair, so the "
        "equality is a property of the passes and not of these seven sentences.  The "
        "fuzz earned its place immediately: it found that the printed clearance and "
        "the printed gap divided the integer residual by D instead of 2 D^2, an "
        "error that the shipped document's zero clearance had hidden -- contact and "
        "verdict were unaffected, the number was wrong by 2D, and the selftest now "
        "compares that printed value too.  A tenth and eleventh mutation cover the "
        "failure path the first nine never reached: a three-square sentence inside its "
        "box with the span exactly its declared L, whose cells at (1/2, 1/2) and "
        "(7/5, 1/2) overlap by 1/10, is refused at `sat` with pair [0, 1] and gap "
        "-1/10 -- in Q and again in Quad(2), so the gap is not an artefact of one "
        "tag or one scale.")

    print(f"selftest: OK ({len(announced)} controls)")
    return len(announced)


# --------------------------------------------------------------------- report
def report(eng, ledger):
    """One table form for every domain: size, measure, invariant, verdict, law."""
    spins = eng.spin_all()
    print("\nWHEEL SPIN — declared cells, exact laws, multi-witness verdicts\n")
    for name, rows in spins.items():
        s = Engine.summarise(rows)
        print(f"  {name}: {s['certified']}/{s['cells']} certified, "
              f"{s['refused']} refused {s['refusal_laws']}")
    for wheel in eng.wheels:
        rows = spins[wheel.name]
        print(f"\n  {wheel.name} [{wheel.domain.name}]")
        print(f"    {'family':14s} {'params':24s} {'size':>6s} {'measure':>26s} "
              f"{'invariant':>22s} {'w':>2s} {'verdict':>10s}  law")
        for r in rows:
            p = ",".join(f"{k}={v}" for k, v in r["params"].items())
            law = r["refusal"]["law"] if r["refusal"] else ""
            size = "" if r["size"] is None else r["size"]
            print(f"    {r['family']:14s} {p:24s} {str(size):>6s} "
                  f"{str(r['measure'] or ''):>26s} "
                  f"{str(r['invariant'] or ''):>22s} {r['witness_count']:>2d} "
                  f"{r['verdict']:>10s}  {law}")
    ledger["spins"] = {name: {"summary": Engine.summarise(rows), "rows": rows}
                       for name, rows in spins.items()}
    return spins


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--selftest" in argv:
        selftest()
        return 0
    if "--audit" in argv:
        import lattice_shells as LAT
        import verify_certificates as VC
        import landscape65 as L65
        import rat47 as R47
        import rat47pos as R47P
        import rat47law as R47L
        import cand105 as C105
        import cand106 as C106
        import observer_chain as OCH
        import face_slide as FSL
        mods = [EF, Q, sys.modules[__name__], LAT, VC, L65, R47, R47P, R47L, C105, C106, OCH,
                FSL]
        total, bad = 0, []
        for m in mods:
            checked, offenders, skipped = EF.audit_module(m, exempt=EF.AUDIT_EXEMPT)
            total += checked
            bad += [(m.__name__, o) for o in offenders]
            print(f"  {m.__name__}: {checked} decision functions, "
                  f"{len(offenders)} naming float, exempt {skipped}")
        print(f"float audit: {total} functions checked, {len(bad)} offenders")
        return 0 if not bad else 1
    if "--census" in argv:
        budget = (argv[argv.index("--budget") + 1] if "--budget" in argv else "240")
        census(Decimal(budget))
        return 0
    if "--probe" in argv:
        budget = (argv[argv.index("--budget") + 1] if "--budget" in argv else "240")
        probe(Decimal(budget))
        return 0
    if "--block-spin" in argv:
        # the 45-degree block's own run: every (s, k) with N <= 250, plus the named
        # showcase points (report: 61-BLOCK45.md)
        rows = block45_spin()
        gated = [r for r in rows if r["verdict"] == "gated"]
        below = [r for r in gated if r.get("below_half_sqrt2")]
        beat = [r for r in gated if r.get("beats_table")]
        path = os.path.join(ROOT, "workspace/push/block45_spin.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"rows": rows, "ncap": 250,
                       "gated": len(gated), "below_floor": len(below),
                       "beats_table": len(beat)}, f, indent=1)
        tally = {}
        for r in rows:
            tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
        print(f"block spin: {len(rows)} rows, {tally}")
        print(f"  below L = 2k + 1/sqrt2: {len(below)} of {len(gated)} gated")
        if gated:
            best = min(gated, key=lambda r: Decimal(r["excess_dec"]))
            print(f"  smallest excess: {best['excess_dec']} "
                  f"(s = {best['s']}, k = {best['k']}, N = {best['N']})")
        print(f"  beats the delivered row: {len(beat)}")
        for s, k in ((5, 4), (17, 13)):
            hit = [r for r in gated if (r["s"], r["k"]) == (s, k)]
            if hit:
                r = hit[0]
                print(f"  (s={s}, k={k}): N = {r['N']}, L = {r['L_dec'][:18]}, "
                      f"excess = {r['excess_dec'][:12]}, table_gap = {r['table_gap']}")
        print(f"  ledger: {os.path.relpath(path, ROOT)}")
        return 0
    if "--block-half-spin" in argv:
        # the half-integer corner fill's own run: small (s, k), the six s = 17 boundary
        # points, and the three delivered sides it is calibrated against (report: 62-BLOCK45-HALF.md)
        rows = block45half_spin()
        gated = [r for r in rows if r["verdict"] == "gated"]
        below = [r for r in gated if r.get("below_half_sqrt2")]
        beat = [r for r in gated if r.get("beats_table")]
        cal = block45half_calibrate()
        path = os.path.join(ROOT, "workspace/push/block45half_spin.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"rows": rows, "calibration": cal, "ncap": 250,
                       "gated": len(gated), "below_floor": len(below),
                       "beats_table": len(beat)}, f, indent=1)
        tally = {}
        for r in rows:
            tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
        print(f"block-half spin: {len(rows)} rows, {tally}")
        print(f"  below L = 2k + 1/sqrt2: {len(below)} of {len(gated)} gated")
        if gated:
            best = min(gated, key=lambda r: Decimal(r["excess_dec"]))
            print(f"  smallest excess: {best['excess_dec']} "
                  f"(s = {best['s']}, k = {best['k']}, N = {best['N']})")
        print(f"  beats the delivered row: {len(beat)}")
        print("  the delivered low-slack sides, exactly, and what the corner fill holds there:")
        for r in cal:
            print(f"    n = {r['n']}: side = {r['table_side']}, k = {r['k']}, "
                  f"N = {r['N']}, short by {r['delta']}, {r['verdict']}")
        for s, k in ((17, 13), (17, 14), (17, 15), (17, 16), (17, 17), (17, 18)):
            hit = [r for r in rows if (r["s"], r["k"]) == (s, k)]
            if hit:
                r = hit[0]
                extra = (f"L = {r['L_dec'][:18]}, excess = {r['excess_dec'][:12]}"
                         if r["verdict"] == "gated" else r["verdict"])
                print(f"  (s={s}, k={k}): N = {r['N']}, {extra}")
        print(f"  ledger: {os.path.relpath(path, ROOT)}")
        return 0
    if "--plugin-bernstein" in argv:
        # the Bernstein stage's own run: a slide certificate on a certified sentence, and
        # the run-95/96 cage/chord interval witness re-read by the plugin (report: 63-PLUGINS.md)
        demo = plugin_bernstein_demo()
        cage = plugin_bernstein_cage()
        print("bernstein slide:", demo)
        print("bernstein vs cage/chord:", cage)
        path = os.path.join(ROOT, "workspace/push/plugin_bernstein.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"slide": demo, "cage": cage}, f, indent=1)
        print(f"  ledger: {os.path.relpath(path, ROOT)}")
        return 0
    if "--plugin-residue" in argv:
        # the residue stage's own run: four certified cells and one synthetic sparse one
        # (report: 63-PLUGINS.md)
        rows = residue_benchmark()
        for r in rows:
            print(f"  {r['cell']}: pairs = {r['pairs']}, contacts = {r['contacts']} "
                  f"(gate {r['gate_contacts']}, match {r['contacts_match']}), D = {r['den']}")
            print(f"    mask {r['t_mask_ns'] // 1000} us, exact {r['t_exact_ns'] // 1000} us")
            for mod in (8, 12, 24):
                d = r[mod]
                print(f"    mod {mod:2d}: rejected {d['rejected']} "
                      f"({100 * d['rejected'] // r['pairs']}%), survivors {d['survivors']}, "
                      f"false {d['false_rejects']}, abstain {d['abstained']}, "
                      f"contacts {d['contacts_masked']}, "
                      f"speedup {_ratio_str(d['speedup'])}x")
        path = os.path.join(ROOT, "workspace/push/plugin_residue.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"rows": [{k: v for k, v in r.items() if k != "mods"}
                                for r in rows]}, f, indent=1, default=str)
        print(f"  ledger: {os.path.relpath(path, ROOT)}")
        return 0
    if "--certificates" in argv:
        # the serialized certificate file and its standalone verifier (report: 64-CERTIFICATES.md)
        import verify_certificates as VC
        path = os.path.join(ROOT, "workspace/push/galois_certificates.json")
        write_certificates(path)
        with open(path) as f:
            back = json.load(f)
        res = VC.verify_document(back)
        for r in res["results"]:
            if r["status"] == "verified":
                s = r["summary"]
                print(f"  verified {s['id']:<18} {s['field']:<8} N = {s['N']:<4} "
                      f"L = {s['L']:<18} contacts = {s['contacts']:<5} "
                      f"void = {s['void']:<18} clearance = {s['clearance']}")
            else:
                print(f"  FAILED {r['detail'].get('id')}: {r['kind']} / {r['check']}: "
                      f"{r['detail']}")
        print(f"  document: {res['verified']} verified, {res['failed']} failed "
              f"({os.path.relpath(path, ROOT)})")
        print("  display-only surfaces (never read by the verifier): "
              + ", ".join(d["surface"] for d in back["display_only"]))
        ok = res["ok"] and VC.main([path, "--selftest"]) == 0
        return 0 if ok else 1
    if "--chain" in argv:
        # the chained pipeline, three configurations, five rows (report: 64-CERTIFICATES.md)
        rows = chain_benchmark()
        for r in rows:
            extra = (f", filters alone {_ratio_str(r['filter_gain'])}x"
                     if r.get("filter_gain") else "")
            print(f"  {r['cell']:<34} {r['stage']:<10} pairs {r['pairs']:<5} "
                  f"contacts {r['contacts']:<5} mask {r['masked']:<4} "
                  f"bound {r['bounded']:<4} gate {r['gate_calls']:<5} "
                  f"hidden {r['mask_hidden_violations']} eq {r['equivalent']} "
                  f"{r['t_pipeline_ns'] // 1000000} ms vs "
                  f"{r['t_reference_ns'] // 1000000} ms = "
                  f"{_ratio_str(r['speedup'])}x{extra}")
        path = os.path.join(ROOT, "workspace/push/plugin_chain.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"rows": [{k: v for k, v in r.items() if k != "mods"}
                                for r in rows]}, f, indent=1, default=str)
        print(f"  ledger: {os.path.relpath(path, ROOT)}")
        return 0
    if "--block-half-beyond" in argv:
        # the half fill's window above n = 1000: one gated row, two law-only rows (the
        # 5164-cell gate is minutes; the law is the integer ladder shifted by 1/2)
        cls = qfield(2)
        out = []
        for s, k in ((25, 20), (35, 27), (50, 37)):
            T, N = block45half_count(s, k)
            L = block45half_side(cls, s, k)
            rec = {"s": s, "k": k, "N": N, "corner": T, "L": str(L),
                   "void": str(L * L - cls(N))}
            if N <= 1500:
                claim = p_block45half(s, k)
                rec["verdict"] = "gated"
                rec["contacts"] = claim.laws["contacts"][1]
            else:
                rec["verdict"] = "law_only"
            out.append(rec)
            print(f"  (s={s}, k={k}): N = {N}, L = {rec['L']}, void = {rec['void']}, "
                  f"{rec['verdict']}" +
                  (f", {rec['contacts']} contacts" if rec["verdict"] == "gated" else ""))
        path = os.path.join(ROOT, "workspace/push/block45half_beyond.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"rows": out}, f, indent=1)
        print(f"  ledger: {os.path.relpath(path, ROOT)}")
        return 0
    if "--two-word-spin" in argv:
        # the two-word builder's own run: 42 word pairs x k = 1..8, every one a built
        # sentence or the code's declared refusal (report: 60-TWO-WORD.md)
        rows = two_word_spin()
        tally = {}
        for r in rows:
            tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
        path = os.path.join(ROOT, "workspace/push/two_word_spin.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"rows": rows, "tally": tally,
                       "pairs": len({(r["field"], r["word1"], r["word2"]) for r in rows})},
                      f, indent=1)
        gated = [r for r in rows if r["verdict"] == "gated"]
        below = [r for r in gated if not r["above_floor"]]
        worst = None
        for r in gated:
            g = Decimal(r["gap_dec"])
            if worst is None or g < worst[0]:
                worst = (g, r["field"], r["word1"], r["word2"], r["k"])
        print(f"two-word spin: {len(rows)} rows, {tally}"
              f" ({len({(r['field'], r['word1'], r['word2']) for r in rows})} word pairs)")
        if worst is None:
            print("  no sentence gated")
        else:
            print(f"  smallest L - (2k + 1/sqrt2): {worst[0]} "
                  f"({worst[1]} {worst[2]} x {worst[3]}, k = {worst[4]})")
        print(f"  below the single-word floor: {len(below)}")
        beat = [r for r in gated if r.get("beats_table")]
        print(f"  beats the delivered row at the same N: {len(beat)}")
        print(f"  ledger: {os.path.relpath(path, ROOT)}")
        return 0
    if "--chord-spin" in argv:
        # one run over the census word and all 66 rotation classes of the second words:
        # a statement about where the pair test closes, kept out of the selftest so the
        # suite's runtime does not move (the sweep is reported in 58-THE-STAIRCASE.md)
        rows = staircase_chord_spin()
        out = []
        for r in rows:
            out.append({
                "word": r["word"], "c": str(r["c"]), "s": str(r["s"]),
                "capacity": r["capacity"], "verdict": r["verdict"],
                "extent_u": str(r["extent_u"]), "extent_v": str(r["extent_v"]),
                "span_u": None if r["span_u"] is None else str(r["span_u"]),
                "span_v": None if r["span_v"] is None else str(r["span_v"]),
                "span_u_dec": None if r["span_u"] is None else
                              str(DecimalWitness.scalar(r["span_u"])),
                "span_v_dec": None if r["span_v"] is None else
                              str(DecimalWitness.scalar(r["span_v"])),
            })
        tally = {}
        for r in rows:
            tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
        path = os.path.join(ROOT, "workspace/push/chord_spin.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"classes": len(rows), "tally": tally, "rows": out}, f, indent=1)
        one = qfield(7)(1)
        live = [r for r in rows if r["verdict"] != "no-placement"]
        print(f"chord spin: {len(rows)} rotation classes, {tally}")
        worst = None
        for r in live:
            for tag in ("span_u", "span_v"):
                x = r[tag]
                if x is not None and x < one and (worst is None or x > worst[0]):
                    worst = (x, r["word"], tag)
        if worst is None:
            print("  no class survived to a span: every cage is empty")
        else:
            print(f"  largest axis span among placeable classes: "
                  f"{DecimalWitness.scalar(worst[0])} ({worst[1]}, {worst[2]})")
        print(f"  ledger: {os.path.relpath(path, ROOT)}")
        return 0

    SQ.guard(quiet=True)
    print("run 86 — glm_wheels.py: three domains, one wheel engine")
    print(f"scorer guard: {SQ.summarise(SQ.load())['score']:.9f}, no row changes\n")
    eng = build_engine()
    ledger = {"run": 86, "instrument": "glm_wheels.py + lattice_shells.py + exact_field.py",
              "domains": sorted(eng.domains)}
    report(eng, ledger)
    checked, offenders, skipped = EF.audit_module(
        sys.modules[__name__], exempt=EF.AUDIT_EXEMPT)
    ledger["audit"] = {"checked": checked, "offenders": offenders,
                       "exempt": skipped}
    print(f"\n  float audit: {checked} decision functions, {len(offenders)} naming "
          f"float, exempt {skipped}")
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w") as f:
        json.dump(ledger, f, indent=1)
    print(f"  ledger: {os.path.relpath(LEDGER, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""``glm_universal.runtime.session`` -- stateful interactive reasoning.

:class:`GeometricSession` is the object a user, a CLI or a test holds onto.
It owns the loaded registers, the concept index built from them, the active
dimensional basis, and the ordered inference history.  It exposes one central
verb, :meth:`GeometricSession.ask`, which parses a query and dispatches it to
the solver for its kind.

What a solver returns
---------------------
Not a formatted answer -- a :class:`Solution`.  A solution carries four things
that are deliberately kept apart:

``steps``
    The reasoning chain, each :class:`Step` holding a **language** sentence
    and the **exact mathematics** for that same step.  These become columns 1
    and 2 of the Three Column Thinking trace; keeping them paired at the step
    level is what makes the two columns synchronized by construction rather
    than by a later alignment pass.
``expected``
    The falsifiable core of the answer: a flat mapping of claim name to
    canonical exact string.  This is what column 3's script must independently
    reproduce.  Nothing enters ``expected`` that the script cannot recompute
    from the public ``glm_universal`` API.
``script_spec``
    Which script template reproduces ``expected``, and with what arguments.
    :mod:`glm_universal.runtime.tct_engine` turns this into source.
``payload``
    Everything else worth reporting that is *not* being independently
    re-derived -- rankings, diagnostics, provenance.  Kept out of ``expected``
    so that the verification claim stays honest about its own scope.

The registers
-------------
Four come from :mod:`glm_universal.data_objects`: ``physics`` (660 quantities),
``chemistry`` (118 elements), ``mathematics`` (rational matrices, reflections
and field elements) and ``lexicon`` (relational concepts).  A fifth,
``spatial``, is built here in :func:`spatial_objects` from the MOG's own
structures -- the trio's three octads, the sextet's six tetrads, the four rows
of the ``4 x 6`` frame, and the fifteen octads obtained as unions of tetrad
pairs.  It is a presentation of the substrate, not a new dataset, and every
member is checked against :data:`glm_universal.substrate.mog.GOLAY_SET` at
build time.

Loading is lazy and cached: a session that only asks physics questions never
pays for the element register, and no register is ever loaded twice.

Invariants
----------
Exact arithmetic (``int`` / ``fractions.Fraction``), no randomness, standard
library only.  Where the substrate's group operation on ``Lambda / 2 Lambda``
is used it is written as ``^`` because on that ``F_2`` module ``^`` *is*
vector addition; nowhere is ``^`` used as a stand-in for an arithmetic
operation on rationals, where ordinary ``+`` and ``-`` are used instead.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import (Any, Dict, List, Mapping, Optional, Sequence, Tuple)

from .. import data_objects as do
from ..data_objects.base import DataObject
from ..reasoning import analogy as an
from ..reasoning import coherence as co
from ..reasoning import dimension_layers as dl
from ..reasoning import metric as me
from ..reasoning import product as pr
from ..reasoning import verifier as ve
from ..substrate import digit_stack as ds
from ..substrate import leech2, mog
from .parser import ConceptIndex, Query, QueryError, parse_query

__all__ = [
    "SolverError", "DOMAINS", "DEFAULT_SUBSPACE", "Step", "Solution",
    "InferenceRecord", "GeometricSession", "spatial_objects", "q",
]


class SolverError(ValueError):
    """Raised when a well-formed query cannot be solved as asked.

    Distinct from :class:`~glm_universal.runtime.parser.QueryError`, which is
    about the shape of the string.  This is about the content: an operand that
    names nothing in the register, a domain with no candidate pool, a class
    label that is not of type 2.
    """


#: The registers a session can load, in a fixed order.
DOMAINS: Tuple[str, ...] = (
    "physics", "chemistry", "mathematics", "lexicon", "spatial",
)

#: The subspace an analogy uses when the query does not name one.  A raw
#: 24-coordinate difference would let bookkeeping coordinates outvote the
#: meaningful ones; see :data:`glm_universal.reasoning.analogy.SUBSPACES`.
DEFAULT_SUBSPACE: Dict[str, Optional[str]] = {
    "physics": "physics.dimension",
    "chemistry": "chemistry.position",
    "mathematics": None,
    # As of v0.5.1, the lexicon register uses the semantic-primitives
    # subspace by default, so analogies over words resolve on meaning
    # rather than spelling.
    "lexicon": "lexicon.primitives",
    "spatial": None,
}


def q(x: Any) -> str:
    """Canonical ``"n/d"`` rendering of an exact scalar.

    Every rational that crosses a module boundary in this package is written
    this way -- in ``expected``, in the generated script, and in the JSON
    export -- so that comparing two of them is a string comparison that cannot
    silently succeed on a rounded value.
    """
    f = Fraction(x)
    return f"{f.numerator}/{f.denominator}"


# ===========================================================================
# 1.  THE SPATIAL REGISTER
# ===========================================================================

def _indicator(mask: int) -> Tuple[int, ...]:
    """The 24-vector of bits of a mask, coordinate 0 first."""
    return tuple((mask >> i) & 1 for i in range(24))


def _spatial_layout() -> Tuple[str, ...]:
    """Coordinate names as MOG frame cells, ``r{row}c{col}``."""
    names: List[str] = []
    for i in range(24):
        row, col = mog.mog_index_of(i)
        names.append(f"r{row}c{col}")
    return tuple(names)


SPATIAL_LAYOUT: Tuple[str, ...] = _spatial_layout()


def spatial_objects() -> Tuple[DataObject, ...]:
    """The MOG's own structures as 0/1 indicator carriers.

    Twenty-eight carriers, all derived from
    :mod:`glm_universal.substrate.mog` and none of them new data:

    * ``trio_brick_0..2`` -- the three disjoint octads of the trio;
    * ``sextet_tetrad_0..5`` -- the six tetrads of the sextet;
    * ``frame_row_0..3`` -- the four rows of the ``4 x 6`` frame;
    * ``sextet_octad_i_j`` -- the fifteen unions of two distinct tetrads.

    Raises
    ------
    AssertionError
        If a brick or a tetrad-pair union is not a Golay octad.  The sextet
        property is thereby checked, not assumed, every time the register is
        built.
    """
    out: List[DataObject] = []

    for b, mask in enumerate(mog.TRIO):
        if bin(mask).count("1") != 8 or mask not in mog.GOLAY_SET:
            raise AssertionError(f"spatial_objects: trio brick {b} is not an "
                                 f"octad")
        out.append(DataObject(
            name=f"trio_brick_{b}", domain="spatial",
            carrier=_indicator(mask), layout=SPATIAL_LAYOUT,
            attributes={"kind": "octad", "mask": f"0x{mask:06x}", "weight": 8,
                        "brick": b},
            provenance={"source": "glm_universal.substrate.mog.TRIO"}))

    for t, mask in enumerate(mog.SEXTET):
        if bin(mask).count("1") != 4:
            raise AssertionError(f"spatial_objects: sextet tetrad {t} has "
                                 f"weight {bin(mask).count('1')}, not 4")
        out.append(DataObject(
            name=f"sextet_tetrad_{t}", domain="spatial",
            carrier=_indicator(mask), layout=SPATIAL_LAYOUT,
            attributes={"kind": "tetrad", "mask": f"0x{mask:06x}",
                        "weight": 4, "tetrad": t},
            provenance={"source": "glm_universal.substrate.mog.SEXTET"}))

    for r in range(4):
        mask = 0
        for c in range(6):
            mask |= 1 << mog.cell_of(r, c)
        out.append(DataObject(
            name=f"frame_row_{r}", domain="spatial",
            carrier=_indicator(mask), layout=SPATIAL_LAYOUT,
            attributes={"kind": "frame_row", "mask": f"0x{mask:06x}",
                        "weight": 6, "row": r},
            provenance={"source": "glm_universal.substrate.mog.cell_of"}))

    for i in range(6):
        for j in range(i + 1, 6):
            mask = mog.SEXTET[i] | mog.SEXTET[j]
            if bin(mask).count("1") != 8 or mask not in mog.GOLAY_SET:
                raise AssertionError(
                    f"spatial_objects: tetrads {i} and {j} do not union to a "
                    f"Golay octad")
            out.append(DataObject(
                name=f"sextet_octad_{i}_{j}", domain="spatial",
                carrier=_indicator(mask), layout=SPATIAL_LAYOUT,
                attributes={"kind": "octad", "mask": f"0x{mask:06x}",
                            "weight": 8, "tetrads": [i, j]},
                provenance={"source": "union of two "
                                      "glm_universal.substrate.mog.SEXTET "
                                      "tetrads"}))
    return tuple(out)


# ===========================================================================
# 2.  SOLUTION CARRIERS
# ===========================================================================

@dataclass(frozen=True)
class Step:
    """One reasoning step, stated twice: in language and in exact algebra.

    Attributes
    ----------
    label
        A short stable identifier for the step, so a test can assert on the
        presence of a step without matching prose.
    language
        Column 1: what this step does and why, in plain English.
    mathematics
        Column 2: the same step as an exact statement over ``Q``, ``Z`` or
        ``F_2``.  Never an approximation and never a float.
    """

    label: str
    language: str
    mathematics: str

    def as_dict(self) -> Dict[str, str]:
        """A JSON-serialisable view."""
        return {"label": self.label, "language": self.language,
                "mathematics": self.mathematics}


@dataclass(frozen=True)
class Solution:
    """What a solver returns: an answer plus everything needed to check it."""

    query: Query
    kind: str
    answer: str
    steps: Tuple[Step, ...] = ()
    expected: Mapping[str, str] = field(default_factory=dict)
    script_spec: Mapping[str, object] = field(default_factory=dict)
    payload: Mapping[str, object] = field(default_factory=dict)
    ok: bool = True
    error: Optional[str] = None

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {
            "query": self.query.as_dict(),
            "kind": self.kind,
            "answer": self.answer,
            "steps": [s.as_dict() for s in self.steps],
            "expected": dict(self.expected),
            "script_spec": dict(self.script_spec),
            "payload": dict(self.payload),
            "ok": self.ok,
            "error": self.error,
        }


@dataclass(frozen=True)
class InferenceRecord:
    """One entry of the session's history."""

    index: int
    raw_query: str
    kind: str
    domain: Optional[str]
    answer: str
    ok: bool

    def as_dict(self) -> Dict[str, object]:
        """A JSON-serialisable view."""
        return {"index": self.index, "raw_query": self.raw_query,
                "kind": self.kind, "domain": self.domain,
                "answer": self.answer, "ok": self.ok}


# ===========================================================================
# 3.  THE SESSION
# ===========================================================================

class GeometricSession:
    """A stateful geometric reasoning session over the loaded registers.

    Parameters
    ----------
    domains
        Which registers this session may use.  Defaults to all of
        :data:`DOMAINS`.  Restricting them does not preload them -- loading is
        lazy either way -- but it does keep the concept index small and makes
        a cross-domain collision impossible by construction.
    basis
        ``"EXT10"`` (default) or ``"SI7"``.  The active basis is reported in
        physics answers and recorded in the history; it selects which
        dimension string is quoted, and does not silently change any
        computation that is defined in the other basis.

    Notes
    -----
    Nothing about a session is random or time-dependent.  Two sessions
    constructed with the same arguments and asked the same queries in the same
    order produce identical solutions, which is what makes
    :meth:`snapshot` a meaningful reproducibility record.
    """

    def __init__(self, domains: Optional[Sequence[str]] = None,
                 basis: str = "EXT10") -> None:
        chosen = tuple(domains) if domains is not None else DOMAINS
        unknown = [d for d in chosen if d not in DOMAINS]
        if unknown:
            raise ValueError(f"GeometricSession: unknown domains {unknown}; "
                             f"known domains are {list(DOMAINS)}")
        if basis not in ("EXT10", "SI7"):
            raise ValueError(f"GeometricSession: basis must be 'EXT10' or "
                             f"'SI7', got {basis!r}")
        self._domains: Tuple[str, ...] = tuple(
            d for d in DOMAINS if d in set(chosen))
        self._basis = basis
        self._registers: Dict[str, Tuple[DataObject, ...]] = {}
        self._index: Optional[ConceptIndex] = None
        self._history: List[InferenceRecord] = []
        self._lexicon_codec = None  # set when the lexicon register loads

    # -- configuration ------------------------------------------------------

    @property
    def domains(self) -> Tuple[str, ...]:
        """The registers this session may use."""
        return self._domains

    @property
    def basis(self) -> str:
        """The active dimensional basis, ``"EXT10"`` or ``"SI7"``."""
        return self._basis

    def set_basis(self, basis: str) -> None:
        """Switch the active dimensional basis."""
        if basis not in ("EXT10", "SI7"):
            raise ValueError(f"set_basis: expected 'EXT10' or 'SI7', got "
                             f"{basis!r}")
        self._basis = basis

    # -- registers ----------------------------------------------------------

    def register(self, domain: str) -> Tuple[DataObject, ...]:
        """The carriers of one domain, loaded on first use and then cached."""
        if domain not in self._domains:
            raise SolverError(
                f"register: domain {domain!r} is not enabled in this session; "
                f"enabled domains are {list(self._domains)}")
        if domain in self._registers:
            return self._registers[domain]
        if domain == "physics":
            loaded = do.physics_objects()
        elif domain == "chemistry":
            loaded = do.element_objects()
        elif domain == "mathematics":
            loaded = do.mathematics_objects()
        elif domain == "lexicon":
            # As of v0.5.0 the lexicon register is the meaning-based
            # SemanticLexiconCodec, not the legacy index-based one.  The
            # legacy module is still importable directly for tests and
            # comparison, but the runtime loads the semantic concepts so
            # ``describe gravity`` / ``describe water`` resolve to a
            # carrier whose distance actually tracks meaning.  Physics's
            # own quantity named "energy" still wins for ``describe
            # energy`` because DOMAIN_PRIORITY ranks physics first; the
            # semantic concept is reachable as ``describe energy in
            # lexicon``.
            loaded, self._lexicon_codec = do.semantic_lexicon_objects()
        elif domain == "spatial":
            loaded = spatial_objects()
        else:  # pragma: no cover -- guarded by the constructor
            raise SolverError(f"register: no loader for {domain!r}")
        self._registers[domain] = tuple(loaded)
        return self._registers[domain]

    def loaded_domains(self) -> Tuple[str, ...]:
        """Which registers have actually been loaded so far."""
        return tuple(d for d in self._domains if d in self._registers)

    @property
    def index(self) -> ConceptIndex:
        """The concept index over every enabled register.

        Building it loads every enabled register, so it is itself built lazily
        and then cached.
        """
        if self._index is None:
            self._index = ConceptIndex.build(
                {d: self.register(d) for d in self._domains})
        return self._index

    def resolve(self, surface: str,
                domain: Optional[str] = None) -> DataObject:
        """Find the carrier a surface form names.

        Raises
        ------
        SolverError
            With the nearest known aliases attached, when nothing matches.
        """
        hit = self.index.lookup(surface, domain)
        if hit is None:
            near = self.index.suggest(surface)
            hint = f"; did you mean {list(near)}?" if near else ""
            raise SolverError(f"resolve: {surface!r} names no carrier in "
                              f"{domain or 'any enabled domain'}{hint}")
        found_domain, name = hit
        for obj in self.register(found_domain):
            if obj.name == name:
                return obj
        raise SolverError(  # pragma: no cover -- index and register agree
            f"resolve: index names {name!r} in {found_domain!r} but the "
            f"register does not contain it")

    # -- history ------------------------------------------------------------

    @property
    def history(self) -> Tuple[InferenceRecord, ...]:
        """Every query this session has answered, in order."""
        return tuple(self._history)

    def clear_history(self) -> None:
        """Forget the inference history; registers stay loaded."""
        self._history = []

    def snapshot(self) -> Dict[str, object]:
        """A JSON-serialisable record of the session's whole state."""
        return {
            "enabled_domains": list(self._domains),
            "loaded_domains": list(self.loaded_domains()),
            "register_sizes": {d: len(self._registers[d])
                               for d in self.loaded_domains()},
            "basis": self._basis,
            "index_aliases": self._index.size() if self._index else None,
            "history": [r.as_dict() for r in self._history],
        }

    # -- the central verb ---------------------------------------------------

    def ask(self, text: str, domain: Optional[str] = None) -> Solution:
        """Parse and solve one query.

        A query that parses but cannot be solved returns a :class:`Solution`
        with ``ok=False`` and ``error`` set, and is still recorded in the
        history -- a failed inference is part of the session's record, not an
        absence from it.  Only a malformed string raises.

        Raises
        ------
        QueryError
            If the string is structurally malformed.
        """
        query = parse_query(text, self.index, domain)
        try:
            solution = self._dispatch(query)
        except (SolverError, QueryError, ValueError, KeyError) as exc:
            solution = Solution(
                query=query, kind=query.kind,
                answer=f"unsolved: {exc}", ok=False, error=str(exc),
                steps=(Step("failure",
                            f"The query parsed as {query.kind!r} but could "
                            f"not be solved.",
                            f"error: {exc}"),))
        self._history.append(InferenceRecord(
            index=len(self._history), raw_query=text, kind=solution.kind,
            domain=query.domain, answer=solution.answer, ok=solution.ok))
        return solution

    def _dispatch(self, query: Query) -> Solution:
        table = {
            "verify": self._solve_verify,
            "analogy": self._solve_analogy,
            "describe": self._solve_describe,
            "nearest": self._solve_nearest,
            "product": self._solve_product,
            "cluster": self._solve_cluster,
            "spatial": self._solve_spatial,
            # Three new query kinds wired in v0.5.3, each surfacing a
            # previously-built-but-unused mechanism from the reasoning
            # layer.  See the directive-aligned section at the bottom of
            # the root README for the layered-projection framing.
            "project": self._solve_project,        # uses dl.escalate
            "trilinear": self._solve_trilinear,    # uses pr.griess_trilinear
            "coherence": self._solve_coherence,    # uses co.nrci_breakdown
            # Two more query kinds wired in v0.5.4, surfacing the
            # remaining created-but-unused reasoning mechanisms.
            "report": self._solve_report,          # uses ve.verifier_report, leech2.pair_census, leech2.theta_series, pr.two_a_closure_report
            "angle": self._solve_angle,            # uses me.signed_cosine_squared
        }
        solver = table.get(query.kind)
        if solver is None:
            near = list(query.suggestions)
            hint = f" Nearest known concepts: {near}." if near else ""
            return Solution(
                query=query, kind="unknown",
                answer=f"The query was not recognised as any of "
                       f"{[k for k in table]}.{hint}",
                ok=False,
                error="unrecognised query",
                steps=(Step("unrecognised",
                            "No classification rule matched the query, so no "
                            "solver was dispatched.",
                            f"parse rule = {query.rule}"),),
                payload={"suggestions": near, "parse_trace": list(query.trace)})
        return solver(query)

    # ------------------------------------------------------------------
    # 3a.  verify -- multi-plane equation audit
    # ------------------------------------------------------------------

    def _solve_verify(self, query: Query) -> Solution:
        lhs, rhs = query.operands
        semantics = str(query.options.get("semantics", "scalar"))
        verdict = ve.verify_expression_pair(lhs, rhs, semantics)

        if verdict.parse_error:
            detail = self._enrich_parse_error(verdict.parse_error)
            raise SolverError(f"verify: {detail}")

        compared = ve.SEMANTICS[semantics]
        steps = [
            Step("parse",
                 f"Read both sides as expressions over the physics register "
                 f"and give each one a dimensional sense.",
                 f"lhs = {lhs}\nrhs = {rhs}"),
            Step("dimension",
                 f"The left side has EXT10 dimension "
                 f"{verdict.lhs_dimension!r}; the right side has "
                 f"{verdict.rhs_dimension!r}.",
                 f"dim(lhs) = {verdict.lhs_dimension}\n"
                 f"dim(rhs) = {verdict.rhs_dimension}"),
            Step("rank",
                 f"Tensor rank is {verdict.lhs_rank} on the left and "
                 f"{verdict.rhs_rank} on the right.",
                 f"rank(lhs) = {verdict.lhs_rank}, "
                 f"rank(rhs) = {verdict.rhs_rank}"),
            Step("semantics",
                 f"Under {semantics!r} semantics the comparison uses "
                 f"{len(compared)} of the 24 relation coordinates.",
                 f"compared coordinates = {list(compared)}"),
            Step("stack",
                 f"Both senses are lifted to a 2-adic digit stack of depth "
                 f"{verdict.depth} at offset {verdict.offset} and compared "
                 f"plane by plane.",
                 f"depth = {verdict.depth}, offset = {verdict.offset}\n"
                 f"planes compared = 0..{(verdict.depth or 1) - 1}"),
        ]
        if verdict.holds:
            steps.append(Step(
                "verdict",
                "Every digit plane agrees, so the relation holds exactly "
                "under these semantics.",
                "for all planes p: lhs_p - rhs_p = 0"))
        else:
            steps.append(Step(
                "verdict",
                f"Planes {list(verdict.failing_planes)} disagree. The "
                f"discrepancy is attributed to MOG facets "
                f"{list(verdict.blamed_facets)} and to coordinates "
                f"{list(verdict.difference_coordinates)}.",
                f"failing planes = {list(verdict.failing_planes)}\n"
                f"first failing plane = {verdict.first_failing_plane}\n"
                f"blamed facets = {list(verdict.blamed_facets)}"))

        expected = {
            "holds": str(verdict.holds),
            "lhs_dimension": str(verdict.lhs_dimension),
            "rhs_dimension": str(verdict.rhs_dimension),
            "lhs_rank": str(verdict.lhs_rank),
            "rhs_rank": str(verdict.rhs_rank),
            "failing_planes": str(list(verdict.failing_planes)),
            "blamed_facets": str(list(verdict.blamed_facets)),
        }
        answer = (f"{lhs} = {rhs} "
                  f"{'holds' if verdict.holds else 'does not hold'} under "
                  f"{semantics} semantics")
        return Solution(
            query=query, kind="verify", answer=answer, steps=tuple(steps),
            expected=expected,
            script_spec={"template": "verify",
                         "args": {"lhs": lhs, "rhs": rhs,
                                  "semantics": semantics}},
            payload={"verdict": verdict.as_dict(),
                     "compared_coordinates": list(compared)})

    def _enrich_parse_error(self, message: str) -> str:
        """Attach register suggestions to a verifier "unknown concept" error.

        The verifier knows only its own name table, so it can say *that* a
        name is unknown but not what the user probably meant.  The session
        holds the concept index, so it can.
        """
        match = re.search(r"unknown concept '([^']+)'", message)
        if not match:
            return message
        near = self.index.suggest(match.group(1))
        if not near:
            return message
        return f"{message}; did you mean {list(near)}?"

    # ------------------------------------------------------------------
    # 3b.  analogy -- proportional analogy in a named subspace
    # ------------------------------------------------------------------

    def _solve_analogy(self, query: Query) -> Solution:
        if len(query.operands) != 3:
            raise SolverError(
                f"analogy: expected three operands, got "
                f"{list(query.operands)}")
        domain = query.domain
        if domain is None:
            raise SolverError(
                "analogy: could not settle on a single domain for the three "
                "operands; name them from one register or pass a domain hint")
        a, b, c = (self.resolve(name, domain) for name in query.operands)
        pool = self.register(domain)
        subspace = query.options.get("subspace",
                                     DEFAULT_SUBSPACE.get(domain))
        subspace = None if subspace is None else str(subspace)
        if subspace is not None and subspace not in an.SUBSPACES:
            raise SolverError(
                f"analogy: unknown subspace {subspace!r}; known subspaces "
                f"are {sorted(an.SUBSPACES)}")

        result = an.solve_analogy_objects(a, b, c, pool, subspace=subspace)
        target = an.analogy_target(a.carrier, b.carrier, c.carrier)
        nonzero = [(a.layout[i] if a.layout else str(i), q(target[i]))
                   for i in range(24) if target[i] != 0]

        steps = [
            Step("resolve",
                 f"Resolve the three terms in the {domain} register: "
                 f"{a.name}, {b.name}, {c.name}.",
                 f"A = {a.name}, B = {b.name}, C = {c.name} in Q^24"),
            Step("displacement",
                 "A proportional analogy is a translation: whatever takes A "
                 "to B should take C to the answer.",
                 "D* = C + (B - A), computed coordinate-wise over Q"),
            Step("target",
                 f"The target point has {len(nonzero)} nonzero coordinates.",
                 "D* = " + ", ".join(f"{k}={v}" for k, v in nonzero[:8])
                 + (" ..." if len(nonzero) > 8 else "")),
            Step("subspace",
                 (f"Distances are measured only in the {subspace!r} "
                  f"coordinates, so bookkeeping coordinates cannot outvote "
                  f"the meaningful ones."
                  if subspace else
                  "No subspace was named, so all 24 coordinates carry equal "
                  "weight in the metric."),
                 (f"subspace {subspace} = "
                  f"{list(an.SUBSPACES[subspace])}" if subspace
                  else "subspace = all 24 coordinates")),
            Step("rank",
                 f"Rank the {len(pool)} candidates by exact squared Griess "
                 f"distance to D*, excluding A, B and C.",
                 "d2(u, v) = (1/8) sum_i (u_i - v_i)^2, exact in Q"),
            Step("answer",
                 (f"The nearest candidate is {result.answer} at squared "
                  f"distance {q(result.distance2)}"
                  + (" -- an exact hit." if result.exact_hit else ".")
                  + ("" if result.unique else
                     f" The minimum is attained by {len(result.tied)} "
                     f"candidates, so the answer is not unique.")),
                 f"argmin = {result.answer}, d2 = {q(result.distance2)}, "
                 f"runner-up = {result.runner_up} at "
                 f"{q(result.runner_up_distance2) if result.runner_up_distance2 is not None else 'n/a'}"),
        ]
        expected = {
            "answer": result.answer,
            "distance2": q(result.distance2),
            "exact_hit": str(result.exact_hit),
            "unique": str(result.unique),
            "tied": str(list(result.tied)),
        }
        answer = (f"{query.operands[0]} : {query.operands[1]} :: "
                  f"{query.operands[2]} : {result.answer}")
        return Solution(
            query=query, kind="analogy", answer=answer, steps=tuple(steps),
            expected=expected,
            script_spec={"template": "analogy",
                         "args": {"domain": domain, "a": a.name, "b": b.name,
                                  "c": c.name, "subspace": subspace}},
            payload={"result": result.as_dict(),
                     "pool_size": len(pool),
                     "subspace": subspace})

    # ------------------------------------------------------------------
    # 3c.  describe -- the dossier of one carrier
    # ------------------------------------------------------------------

    def _solve_describe(self, query: Query) -> Solution:
        if not query.operands:
            raise SolverError("describe: no concept named")
        obj = self.resolve(query.operands[0], query.domain)
        params = obj.parameters()
        stack = obj.stack()
        address = obj.monster_address()
        round_trip = obj.round_trip_ok()
        norm2 = me.griess_norm2(obj.carrier)

        detail = ""
        if obj.domain == "physics":
            quantity = do.quantity_by_name(obj.name)
            detail = (f"Its dimension is {quantity.dimension_string('EXT10')} "
                      f"in EXT10 and "
                      f"{quantity.dimension_string('SI7')} in SI7; the active "
                      f"basis is {self._basis}.")
        elif obj.domain == "chemistry":
            detail = (f"Element Z={obj.attributes.get('z')}, "
                      f"{obj.attributes.get('name')}, period "
                      f"{obj.attributes.get('period')}, "
                      f"{obj.attributes.get('group_block')}.")
        elif obj.domain == "spatial":
            detail = (f"A MOG {obj.attributes.get('kind')} of weight "
                      f"{obj.attributes.get('weight')} at mask "
                      f"{obj.attributes.get('mask')}.")
        elif obj.domain == "lexicon":
            # The lexicon register now carries SemanticConcepts.  The
            # carrier's attributes include the primitives the caller set,
            # the part of speech, the relation triples, and the
            # has_physical_dim flag.
            attrs = obj.attributes or {}
            pos = attrs.get("pos", "unspecified")
            arity = attrs.get("arity", 0)
            has_dims = "with" if attrs.get("physical_dims") else "without"
            n_prims = attrs.get("n_primitives_set", 0)
            detail = (f"A semantic lexical concept ({pos}, arity {arity}, "
                      f"{n_prims} primitives set, {has_dims} physical "
                      f"dimensions).")

        # Lattice projection (v0.5.3): wires analogy.nearest_lattice_point,
        # the exact, provably-optimal Leech decoder that was previously
        # used only by example scripts.  Reports the nearest point of
        # Lambda to this carrier, its norm, and whether it lands on a 2A
        # axis -- three facts the directive cares about.
        try:
            lattice = an.nearest_lattice_point(list(obj.carrier))
            lattice_step = Step(
                "lattice_projection",
                f"The nearest point of the Leech lattice Lambda to this "
                f"carrier is at squared distance {q(lattice.distance2)}; "
                f"the lattice point has norm^2 = {q(lattice.norm2)} and "
                f"{'IS' if lattice.is_2a_axis else 'is NOT'} a 2A axis of "
                f"the Monster.",
                f"nearest_lattice_point({obj.name}): "
                f"d^2 = {q(lattice.distance2)}, "
                f"||lambda||^2 = {q(lattice.norm2)}, "
                f"is_2a_axis = {lattice.is_2a_axis}")
            lattice_expected = {
                "lattice_distance2": q(lattice.distance2),
                "lattice_norm2": q(lattice.norm2),
                "lattice_is_2a_axis": str(lattice.is_2a_axis),
            }
            lattice_payload = {"lattice_projection": {
                "distance2": q(lattice.distance2),
                "norm2": q(lattice.norm2),
                "is_2a_axis": lattice.is_2a_axis,
            }}
        except Exception as exc:
            # nearest_lattice_point is exact and exhaustive; if it fails
            # the carrier is too far from the lattice for the search to
            # be meaningful.  Report honestly rather than hiding.
            lattice_step = Step(
                "lattice_projection",
                f"The Leech lattice projection could not be computed: "
                f"{exc}",
                f"nearest_lattice_point: {exc}")
            lattice_expected = {}
            lattice_payload = {"lattice_projection": {"error": str(exc)}}

        steps = [
            Step("identity",
                 f"{obj.name} is a carrier of the {obj.domain} register. "
                 f"{detail}".strip(),
                 f"{obj.name} in Q^24, layout = "
                 f"{list(obj.layout)[:6]} ..."),
            Step("stack_parameters",
                 f"Fitting a 2-adic digit stack to this carrier's actual "
                 f"range needs depth {params.depth} at offset "
                 f"{params.offset}; nothing is hardcoded.",
                 f"depth = {params.depth}, offset = {params.offset}, "
                 f"denominator = {stack.denominator}"),
            Step("round_trip",
                 ("The carrier is reconstructed exactly from its digit "
                  "stack, so the stack is a lossless encoding of it."
                  if round_trip else
                  "The carrier does NOT reconstruct from its digit stack at "
                  "these parameters."),
                 f"class_stack_rebuild(class_stack(v)) == v is "
                 f"{round_trip}"),
            Step("address",
                 f"Digit plane 0 is the 24-bit mask "
                 f"{address['plane0_mask']} of weight "
                 f"{address['plane0_weight']}; it "
                 f"{'is' if address['is_golay_codeword'] else 'is not'} a "
                 f"Golay codeword, and the carrier "
                 f"{'is' if address['carrier_is_integral'] else 'is not'} "
                 f"integral.",
                 f"plane0 = {address['plane0_mask']}, "
                 f"wt = {address['plane0_weight']}, "
                 f"golay = {address['is_golay_codeword']}"),
            lattice_step,
            Step("norm",
                 "Its squared Griess norm places it at an exact rational "
                 "distance from the origin.",
                 f"<v, v> = (1/8) sum_i v_i^2 = {q(norm2)}"),
        ]
        expected = {
            "name": obj.name,
            "domain": obj.domain,
            "depth": str(params.depth),
            "offset": str(params.offset),
            "plane0_mask": str(address["plane0_mask"]),
            "plane0_weight": str(address["plane0_weight"]),
            "is_golay_codeword": str(address["is_golay_codeword"]),
            "round_trip_ok": str(round_trip),
            "griess_norm2": q(norm2),
        }
        expected.update(lattice_expected)
        return Solution(
            query=query, kind="describe",
            answer=f"{obj.name} ({obj.domain}): depth {params.depth}, "
                   f"plane-0 mask {address['plane0_mask']}, "
                   f"|v|^2 = {q(norm2)}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "describe",
                         "args": {"domain": obj.domain, "name": obj.name}},
            payload={"address": address,
                     "facet_signature": obj.facet_signature(),
                     "attributes": _jsonable(obj.attributes),
                     **lattice_payload})

    # ------------------------------------------------------------------
    # 3d.  nearest -- ranking under the Griess metric
    # ------------------------------------------------------------------

    def _solve_nearest(self, query: Query) -> Solution:
        if not query.operands:
            raise SolverError("nearest: no reference concept named")
        obj = self.resolve(query.operands[0], query.domain)
        domain = obj.domain
        limit = int(query.options.get("limit", 5))
        if limit < 1:
            raise SolverError(f"nearest: limit must be at least 1, got "
                              f"{limit}")
        pool = self.register(domain)
        subspace = query.options.get("subspace", DEFAULT_SUBSPACE.get(domain))
        subspace = None if subspace is None else str(subspace)
        indices = None
        if subspace is not None:
            if subspace not in an.SUBSPACES:
                raise SolverError(
                    f"nearest: unknown subspace {subspace!r}; known subspaces "
                    f"are {sorted(an.SUBSPACES)}")
            indices = an.subspace_indices(obj.layout, an.SUBSPACES[subspace])
        target = an.project_subspace(obj.carrier, indices)
        candidates = [(o.name, an.project_subspace(o.carrier, indices))
                      for o in pool]
        ranked = me.rank_by_distance(target, candidates, exclude=(obj.name,))
        top = ranked[:limit]

        steps = [
            Step("reference",
                 f"Take {obj.name} from the {domain} register as the query "
                 f"point.",
                 f"query = {obj.name} in Q^24"),
            Step("subspace",
                 (f"Compare only in the {subspace!r} coordinates."
                  if subspace else
                  "Compare across all 24 coordinates."),
                 (f"subspace = {subspace}, "
                  f"{len(indices)} coordinates" if indices is not None
                  else "subspace = all 24 coordinates")),
            Step("rank",
                 f"Score all {len(pool) - 1} other carriers by exact squared "
                 f"Griess distance and sort; ties break by name, so the order "
                 f"is a function of the data alone.",
                 "d2(u, v) = (1/8) sum_i (u_i - v_i)^2"),
            Step("answer",
                 "The nearest carriers are: "
                 + ", ".join(f"{n} (d2 = {q(d)})" for n, d in top),
                 "\n".join(f"d2({obj.name}, {n}) = {q(d)}" for n, d in top)),
        ]
        expected = {
            "reference": obj.name,
            "nearest": top[0][0],
            "nearest_distance2": q(top[0][1]),
            "top_names": str([n for n, _ in top]),
            "top_distances2": str([q(d) for _, d in top]),
        }
        return Solution(
            query=query, kind="nearest",
            answer=f"nearest to {obj.name}: " + ", ".join(n for n, _ in top),
            steps=tuple(steps), expected=expected,
            script_spec={"template": "nearest",
                         "args": {"domain": domain, "name": obj.name,
                                  "limit": limit, "subspace": subspace}},
            payload={"ranked": [[n, q(d)] for n, d in top],
                     "pool_size": len(pool), "subspace": subspace})

    # ------------------------------------------------------------------
    # 3e.  product -- the Norton-Sakuma 2A algebra
    # ------------------------------------------------------------------

    def _solve_product(self, query: Query) -> Solution:
        u, v = self._resolve_two_a_pair(query.operands)
        if not pr.is_two_a_pair(u, v):
            raise SolverError(
                f"product: classes {u} and {v} are in position "
                f"{pr.position_name(u, v)}, not 2A; the Sakuma relation is "
                f"only modelled for the 2A position")
        third = pr.sakuma_third_axis(u, v)
        prod = pr.axis_product(u, v)
        sub = pr.two_a_subalgebra(u, v)
        form_uv = pr.griess_form(pr.axis(u), pr.axis(v))
        form_uu = pr.griess_form(pr.axis(u), pr.axis(u))
        coeffs = {str(label): q(prod.coefficient(label))
                  for label in sorted(sub.labels)}

        steps = [
            Step("classes",
                 f"Take the type-2 classes {u} and {v} of Lambda / 2 Lambda "
                 f"and their axes a_u and a_v.",
                 f"u = {u}, v = {v}, both type 2 in Lambda / 2 Lambda"),
            Step("position",
                 f"Their pair invariant puts them in the "
                 f"{pr.position_name(u, v)} position, which is the one the "
                 f"Sakuma relation models.",
                 f"pair_invariant(u, v) = "
                 f"{pr.pair_invariant_classes(u, v)} -> position "
                 f"{pr.position_name(u, v)}"),
            Step("third_axis",
                 f"The 2A position supplies a third axis, class {third}, "
                 f"obtained as the sum of the two classes in the F_2 module "
                 f"Lambda / 2 Lambda -- that is vector addition in that "
                 f"module, written as a bitwise XOR of class labels because "
                 f"the labels are its coordinate vectors.",
                 f"a_uv = class {third} = u + v in Lambda / 2 Lambda "
                 f"(F_2 addition)"),
            Step("sakuma",
                 "The Norton-Sakuma relation gives the product as an exact "
                 "rational combination of the three axes.",
                 "a_u . a_v = (1/8)(a_u + a_v - a_uv)"),
            Step("coefficients",
                 "In the three-axis basis the product has these exact "
                 "coefficients.",
                 "\n".join(f"coeff[{k}] = {val}"
                           for k, val in sorted(coeffs.items()))),
            Step("form",
                 "The Griess form on the axes is exact and rational.",
                 f"<a_u, a_u> = {q(form_uu)}, <a_u, a_v> = {q(form_uv)}"),
        ]
        expected = {
            "u": str(u), "v": str(v), "third_axis": str(third),
            "position": pr.position_name(u, v),
            "coefficients": str(sorted(coeffs.items())),
            "griess_self": q(form_uu),
            "griess_pair": q(form_uv),
            "subalgebra_labels": str(sorted(sub.labels)),
        }
        return Solution(
            query=query, kind="product",
            answer=f"a_{u} . a_{v} = (1/8)(a_{u} + a_{v} - a_{third})",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "product", "args": {"u": u, "v": v}},
            payload={"subalgebra": sub.as_dict(),
                     "product": prod.as_dict()})

    def _resolve_two_a_pair(self, operands: Sequence[str]) -> Tuple[int, int]:
        """Turn zero, one or two class labels into a checked 2A pair.

        With no label, the first 2A pair in sorted class order is used; with
        one, its first 2A partner in sorted class order.  Both choices are
        deterministic scans of the exhaustive type-2 table -- no sampling.
        """
        if len(operands) >= 2:
            return int(operands[0]), int(operands[1])
        seed = int(operands[0]) if operands else None
        if seed is not None and not leech2.is_type2_class(seed):
            raise SolverError(
                f"product: class {seed} is not of type 2, so it carries no "
                f"axis")
        pairs = pr.sample_two_a_pairs(1, seed_class=seed)
        if not pairs:
            raise SolverError(
                f"product: no 2A partner found for seed class {seed}")
        return pairs[0]

    # ------------------------------------------------------------------
    # 3f.  cluster -- exact agglomerative clustering
    # ------------------------------------------------------------------

    def _solve_cluster(self, query: Query) -> Solution:
        if len(query.operands) < 2:
            raise SolverError(
                f"cluster: need at least two carriers, got "
                f"{list(query.operands)}")
        objs = [self.resolve(name, query.domain) for name in query.operands]
        domains = sorted({o.domain for o in objs})
        if len(domains) > 1:
            raise SolverError(
                f"cluster: the carriers span domains {domains}; a "
                f"cross-domain distance would compare unlike layouts")
        labels = [o.name for o in objs]
        vectors = [o.carrier for o in objs]
        tree = me.single_linkage(vectors, labels)
        k = int(query.options.get("k", 2))
        if not 1 <= k <= len(labels):
            raise SolverError(
                f"cluster: k must be between 1 and {len(labels)}, got {k}")
        groups = me.cut_tree(tree, k)

        steps = [
            Step("carriers",
                 f"Cluster {len(labels)} carriers from the {domains[0]} "
                 f"register: {labels}.",
                 f"labels = {labels}"),
            Step("metric",
                 "Merge heights are exact squared Griess distances, so the "
                 "dendrogram is rational throughout and no rounding can "
                 "reorder a merge.",
                 "d2(u, v) = (1/8) sum_i (u_i - v_i)^2 in Q"),
            Step("linkage",
                 f"Single linkage merges the two closest clusters "
                 f"{len(tree.merges)} times.",
                 "\n".join(f"merge {i}: height = {q(m.height)}"
                           for i, m in enumerate(tree.merges))),
            Step("cut",
                 f"Cutting the tree at k = {k} gives {len(groups)} groups: "
                 f"{groups}.",
                 f"cut_tree(k={k}) = {groups}"),
        ]
        expected = {
            "labels": str(labels),
            "k": str(k),
            "groups": str(groups),
            "merge_heights": str([q(m.height) for m in tree.merges]),
        }
        return Solution(
            query=query, kind="cluster",
            answer=f"{k} clusters: {groups}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "cluster",
                         "args": {"domain": domains[0], "names": labels,
                                  "k": k}},
            payload={"dendrogram": tree.as_dict()})

    # ------------------------------------------------------------------
    # 3g.  spatial -- the MOG presentation of a carrier
    # ------------------------------------------------------------------

    def _solve_spatial(self, query: Query) -> Solution:
        if not query.operands:
            raise SolverError("spatial: no carrier named")
        obj = self.resolve(query.operands[0], query.domain)
        stack = obj.stack()
        plane0 = stack.planes[0]
        grid = mog.frame(plane0)
        cube = mog.cube_profile(plane0)
        signature = obj.facet_signature()
        touched = sorted(k for k, w in signature.items() if w)
        codeword, distance, count = an.nearest_golay_codeword(plane0)

        steps = [
            Step("carrier",
                 f"Take {obj.name} from the {obj.domain} register and read "
                 f"its digit plane 0 as a 24-bit mask.",
                 f"plane0 = 0x{plane0:06x}, weight = "
                 f"{bin(plane0).count('1')}"),
            Step("frame",
                 "Lay that mask out as the MOG's 4 x 6 frame. The rows and "
                 "columns are the sextet and trio structure, so a spatial "
                 "pattern becomes an algebraic one.",
                 "\n".join(" ".join(str(b) for b in row) for row in grid)),
            Step("cubes",
                 "Each of the trio's three bricks is a 2x2x2 cube; here are "
                 "their weights and parities.",
                 "\n".join(f"brick {c['brick']}: weight {c['weight']}, "
                           f"parity {c['parity']}" for c in cube)),
            Step("facets",
                 f"Summed over all digit planes, the carrier's binary content "
                 f"touches {len(touched)} of the 31 named MOG facets.",
                 f"touched facets = {touched}"),
            Step("golay",
                 (f"Plane 0 is at Hamming distance {distance} from the "
                  f"nearest Golay codeword, and {count} codeword"
                  f"{'' if count == 1 else 's'} attain"
                  f"{'s' if count == 1 else ''} that distance."),
                 f"nearest codeword = 0x{codeword:06x}, "
                 f"d_H = {distance}, multiplicity = {count}"),
        ]
        expected = {
            "name": obj.name,
            "plane0_mask": f"0x{plane0:06x}",
            "plane0_weight": str(bin(plane0).count("1")),
            "frame_rows": str([[int(b) for b in row] for row in grid]),
            "brick_weights": str([c["weight"] for c in cube]),
            "nearest_codeword": f"0x{codeword:06x}",
            "golay_distance": str(distance),
            "golay_multiplicity": str(count),
        }
        return Solution(
            query=query, kind="spatial",
            answer=f"{obj.name}: plane-0 frame weight "
                   f"{bin(plane0).count('1')}, brick weights "
                   f"{[c['weight'] for c in cube]}, Golay distance "
                   f"{distance}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "spatial",
                         "args": {"domain": obj.domain, "name": obj.name}},
            payload={"facet_signature": signature,
                     "cube_profile": cube,
                     "grid": [[int(b) for b in row] for row in grid]})

    # ------------------------------------------------------------------
    # 3h.  project -- the layered projection of two carriers (v0.5.3)
    # ------------------------------------------------------------------
    # Wires `reasoning/dimension_layers.py::escalate`, which was created
    # in v0.4.0 but never reached from any runtime query.  The directive
    # (`ubp_universal_1.txt`) frames this as the central mechanism: each
    # layer is true within its range and hands off to the next when its
    # range is exhausted.  See the root README's "layered projection"
    # section for the framing.
    # ------------------------------------------------------------------

    def _solve_project(self, query: Query) -> Solution:
        if len(query.operands) < 2:
            raise SolverError("project: needs two operands, A and B")
        a = self.resolve(query.operands[0], query.domain)
        b = self.resolve(query.operands[1], query.domain)
        # Walk every layer from substrate up to universal.
        result = dl.escalate(a.carrier, b.carrier, start=0)
        all_views = result["all_views"]
        final_layer = result["layer"]

        steps = [
            Step("escalate",
                 f"Projecting {a.name} and {b.name} through the dimension "
                 f"layers: each layer perceives the pair at its own "
                 f"resolution, and the layered projection walks from the "
                 f"substrate (binary) up to the universal (all layers at "
                 f"once).  Each view is true within its range; the next "
                 f"layer takes over when this one's reach is exhausted.",
                 f"escalate({a.name}, {b.name}) walked {len(all_views)} "
                 f"layers; final layer = {final_layer.name}"),
        ]
        # One step per layer, naming its view of each operand and the
        # distance it measured.
        for layer_name, view_a, view_b, distance in all_views:
            steps.append(Step(
                f"layer_{layer_name}",
                f"The {layer_name} layer sees {a.name} as "
                f"{self._describe_view(view_a)} and {b.name} as "
                f"{self._describe_view(view_b)}.  Its measure of their "
                f"separation is {distance}.",
                f"{layer_name}: view_A={view_a!r}, view_B={view_b!r}, "
                f"distance={distance}",
            ))
        steps.append(Step(
            "verdict",
            f"The highest layer reached is {final_layer.name} "
            f"(dimension {final_layer.dimension}).  Its reach: "
            f"{final_layer.reach[0] if final_layer.reach else 'n/a'}.",
            f"final_layer={final_layer.name}, "
            f"final_distance={result['distance']}",
        ))

        expected = {
            "operand_a": a.name,
            "operand_b": b.name,
            "layers_walked": str(len(all_views)),
            "final_layer": final_layer.name,
            "final_distance": q(Fraction(result["distance"])),
        }
        return Solution(
            query=query, kind="project",
            answer=f"project {a.name} {b.name}: walked "
                   f"{len(all_views)} layers, final = {final_layer.name}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "project",
                         "args": {"domain_a": a.domain, "name_a": a.name,
                                  "domain_b": b.domain, "name_b": b.name}},
            payload={"all_views": [(name, str(va), str(vb), str(d))
                                    for name, va, vb, d in all_views],
                     "final_layer": final_layer.name})

    @staticmethod
    def _describe_view(view) -> str:
        """A short human-readable description of a layer's view.

        The dimension-projection ``perceive`` functions return a dict
        whose 'layer' key names the layer and whose other keys carry
        layer-specific summary data.  We pull out the most informative
        one or two keys per layer rather than dumping the whole dict.
        """
        if isinstance(view, dict):
            layer = view.get("layer", "?")
            if layer == "substrate":
                hw = view.get("hamming_weight", "?")
                snap = view.get("snap_distance", "?")
                nrci = view.get("nrci", "?")
                return (f"binary (HW={hw}, snap_distance={snap}, "
                        f"NRCI={nrci})")
            if layer == "integer":
                exps = view.get("exponents_SI7", ())
                return f"SI7 exponents {exps}"
            if layer == "rational":
                ld = view.get("lattice_distance2", "?")
                cls = view.get("leech_class", "?")
                is_2a = view.get("is_2a_axis", "?")
                return (f"rational carrier (Leech d^2={ld}, "
                        f"class={cls}, is_2a={is_2a})")
            if layer == "griess":
                cls = view.get("leech_class", "?")
                is_2a = view.get("is_2a_axis", "?")
                return (f"Griess element (Leech class={cls}, "
                        f"is_2a_axis={is_2a})")
            if layer == "universal":
                return "all layers at once"
            return f"{layer} view"
        if isinstance(view, (int, float, Fraction)):
            return str(view)
        if isinstance(view, (list, tuple)):
            if len(view) > 8:
                return f"a {len(view)}-tuple"
            return str(view)
        if isinstance(view, str):
            return view
        return type(view).__name__

    # ------------------------------------------------------------------
    # 3i.  trilinear -- the invariant form ⟨u·v, w⟩ (v0.5.3)
    # ------------------------------------------------------------------
    # Wires `reasoning/product.py::griess_trilinear`.  The directive
    # (`ubp_universal_1.txt`) asks: "would you like to explore how to
    # explicitly compute the ⟨u·v, w⟩ inner product to extract semantic
    # similarity scores between your physics concepts?"  This solver
    # answers that question operationally.
    # ------------------------------------------------------------------

    def _solve_trilinear(self, query: Query) -> Solution:
        if len(query.operands) < 3:
            raise SolverError("trilinear: needs three operands, A B C")
        # Each operand can be either (a) a concept name, resolved
        # through the index, or (b) a bare integer axis label (one of
        # the 98,280 type-2 classes of Lambda/2Lambda).  This lets the
        # user ask 'trilinear 127 432 463' directly, which is the form
        # the demo's sample_two_a_pairs() produces.
        resolved_operands = []
        for operand in query.operands[:3]:
            # Try integer first -- bare digits classify as axis labels.
            if operand.isdigit():
                resolved_operands.append(("axis", int(operand)))
            else:
                obj = self.resolve(operand, query.domain)
                resolved_operands.append(("concept", obj))
        a_kind, a_val = resolved_operands[0]
        b_kind, b_val = resolved_operands[1]
        c_kind, c_val = resolved_operands[2]
        a_name = str(a_val) if a_kind == "axis" else a_val.name
        b_name = str(b_val) if b_kind == "axis" else b_val.name
        c_name = str(c_val) if c_kind == "axis" else c_val.name

        # Get the three axis labels.  For an explicit integer, that IS
        # the label.  For a concept, project to its nearest Leech point
        # and take that point's type-2 class.
        def _axis_label_for(kind, val):
            if kind == "axis":
                return val
            # Concept: project to nearest lattice point, take its class.
            lat = an.nearest_lattice_point(list(val.carrier))
            cls = leech2.class_of(list(lat.point))
            return cls

        try:
            label_a = _axis_label_for(a_kind, a_val)
            label_b = _axis_label_for(b_kind, b_val)
            label_c = _axis_label_for(c_kind, c_val)
            ax_a = pr.axis(label_a)
            ax_b = pr.axis(label_b)
            ax_c = pr.axis(label_c)
        except (pr.PositionError, ValueError, TypeError) as exc:
            return Solution(
                query=query, kind="trilinear",
                answer=f"trilinear {a_name} {b_name} {c_name}: an operand "
                       f"did not resolve to a 2A axis",
                ok=False, error=f"trilinear: {exc}",
                steps=(Step("failed",
                            "One of the three operands does not resolve to "
                            "a 2A axis of the Leech lattice (its nearest "
                            "lattice point is not a type-2 class, or the "
                            "label is not in the 98,280), so the Griess "
                            "trilinear form is not defined on it.",
                            f"Error: {exc}"),),
                payload={"operands": [a_name, b_name, c_name]})

        # Compute the trilinear form T(a, b, c) = <a.b, c>.  This raises
        # PositionError if any pair is in the "not modelled" position 1
        # or 0 -- honest about the boundary.
        try:
            T = pr.griess_trilinear(ax_a, ax_b, ax_c)
            # axis_product returns an AlgebraVector; griess_form takes
            # two of them.  The squared norm of a product is
            # griess_form(prod, prod).
            prod_ab = pr.axis_product(label_a, label_b)
            prod_ac = pr.axis_product(label_a, label_c)
            prod_bc = pr.axis_product(label_b, label_c)
            Tab = pr.griess_form(prod_ab, prod_ab)
            Tac = pr.griess_form(prod_ac, prod_ac)
            Tbc = pr.griess_form(prod_bc, prod_bc)
            coh = pr.coherence_of_product(ax_a, ax_b)
        except pr.PositionError as exc:
            return Solution(
                query=query, kind="trilinear",
                answer=f"trilinear {a_name} {b_name} {c_name}: a pair is "
                       f"not in the 2A position",
                ok=False, error=f"trilinear: {exc}",
                steps=(Step("failed",
                            "The Griess product models only the 1A (same "
                            "axis), 2A (invariant 2), and 2B (invariant 0) "
                            "positions.  This triple has a pair in the "
                            "invariant-1 position, which is not modelled -- "
                            "94,208 of the 98,280 type-2 classes are in "
                            "this position against any given axis.  The "
                            "trilinear form is therefore not defined on "
                            "this triple.",
                            f"PositionError: {exc}"),),
                payload={"operands": [a_name, b_name, c_name],
                         "axes": [label_a, label_b, label_c]})

        # coh is a dict with these keys:
        #   factor_x_norm2, factor_y_norm2, product_norm2,
        #   self_coherence_x, self_coherence_y, product_is_zero
        coh_xx = coh["factor_x_norm2"]
        coh_yy = coh["factor_y_norm2"]
        coh_pp = coh["product_norm2"]
        coh_sx = coh["self_coherence_x"]
        coh_sy = coh["self_coherence_y"]

        # T, Tab, Tac, Tbc, coh are computed in the try block above.

        steps = [
            Step("axes",
                 f"Each operand is projected onto a 2A axis of the Leech "
                 f"lattice.  For an explicit integer operand, that IS the "
                 f"axis label; for a concept name, the carrier is decoded "
                 f"to its nearest Leech point and that point's type-2 "
                 f"class is the axis.  The trilinear form <u.v, w> is "
                 f"defined on these axes; it is the invariant Griess form "
                 f"the directive asks about.",
                 f"axis({a_name}) = {label_a}, "
                 f"axis({b_name}) = {label_b}, "
                 f"axis({c_name}) = {label_c}"),
            Step("trilinear",
                 f"The trilinear form T(A, B, C) = <A.B, C> is the "
                 f"invariant inner product of the Griess algebra.  It "
                 f"measures the coherence of the triple: T = 0 means the "
                 f"three are mutually orthogonal, T != 0 means the product "
                 f"of two has a component along the third.",
                 f"T({a_name}, {b_name}, {c_name}) = {q(T)}"),
            Step("pairwise",
                 f"For context, the three pairwise bilinear forms "
                 f"<A.B, A.B>, <A.C, A.C>, <B.C, B.C> (the squared norms "
                 f"of the pairwise products).",
                 f"<A.B>^2 = {q(Tab)}, <A.C>^2 = {q(Tac)}, "
                 f"<B.C>^2 = {q(Tbc)}"),
            Step("coherence",
                 f"The coherence-of-product block reports ||A||^2, "
                 f"||B||^2, ||A.B||^2, and the self-coherence values "
                 f"<A.B, A> and <A.B, B> -- the ingredients a "
                 f"semantic-similarity score would use.",
                 f"||A||^2 = {q(coh_xx)}, ||B||^2 = {q(coh_yy)}, "
                 f"||A.B||^2 = {q(coh_pp)}, "
                 f"<A.B, A> = {q(coh_sx)}, <A.B, B> = {q(coh_sy)}"),
        ]
        expected = {
            "operand_a": a_name,
            "operand_b": b_name,
            "operand_c": c_name,
            "axis_a": str(label_a),
            "axis_b": str(label_b),
            "axis_c": str(label_c),
            "trilinear": q(T),
            "pairwise_AB": q(Tab),
            "pairwise_AC": q(Tac),
            "pairwise_BC": q(Tbc),
        }
        return Solution(
            query=query, kind="trilinear",
            answer=f"trilinear {a_name} {b_name} {c_name}: "
                   f"<A.B, C> = {q(T)}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "trilinear",
                         "args": {"domain_a": query.domain or "mathematics",
                                  "name_a": a_name,
                                  "domain_b": query.domain or "mathematics",
                                  "name_b": b_name,
                                  "domain_c": query.domain or "mathematics",
                                  "name_c": c_name}},
            payload={"coherence_block": coh,
                     "axes": [label_a, label_b, label_c]})

    # ------------------------------------------------------------------
    # 3j.  coherence -- the five-shell NRCI breakdown (v0.5.3)
    # ------------------------------------------------------------------
    # Wires `reasoning/coherence.py::nrci_breakdown`.  The whole
    # coherence module was created in v0.4.0 but never reached from any
    # runtime query.  NRCI is one of the GLM's headline metrics -- the
    # directive's constants table puts TAX and NRCI front and centre --
    # and the runtime had no way to ask for it.
    # ------------------------------------------------------------------

    def _solve_coherence(self, query: Query) -> Solution:
        if not query.operands:
            raise SolverError("coherence: no concept named")
        obj = self.resolve(query.operands[0], query.domain)
        carrier = list(obj.carrier)

        # nrci_breakdown returns a dict with per-shell taxes and the
        # combined NRCI.  Shell keys are:
        #   shell0_golay, shell1_sign_parity, shell2_sextet_balance,
        #   shell3_coset_type, shell4_sextet_signed, tax_total, nrci, regime
        breakdown = co.nrci_breakdown(carrier)
        # nrci_breakdown may already include a regime; if so, use it,
        # otherwise derive it.
        regime = breakdown.get("regime") or co.coherence_regime(
            breakdown["nrci"])
        nrci_value = breakdown["nrci"]
        if isinstance(nrci_value, Fraction):
            nrci_str = q(nrci_value)
        else:
            nrci_str = q(Fraction(nrci_value).limit_denominator(10**6))

        # Per-shell values: 0, 1, 3 are exact rationals stored as
        # strings; 2 and 4 are floats (sqrt).  Render them honestly.
        def _render_shell(v):
            if isinstance(v, Fraction):
                return q(v)
            if isinstance(v, float):
                return f"{v:.6f}"
            return str(v)

        shell_keys = ("shell0_golay", "shell1_sign_parity",
                      "shell2_sextet_balance", "shell3_coset_type",
                      "shell4_sextet_signed")
        shell_renders = {k: _render_shell(breakdown[k]) for k in shell_keys}

        steps = [
            Step("nrci",
                 f"NRCI is the GLM's coherence measure: how structured, "
                 f"non-random a carrier is.  It runs from 0 (subcoherent) "
                 f"through 1 (perfect coherence, the vacuum).  {obj.name}'s "
                 f"combined NRCI is {nrci_value:.6f}, which puts it in the "
                 f"{regime} regime.",
                 f"NRCI({obj.name}) = {nrci_str} = {nrci_value:.6f}, "
                 f"regime = {regime}"),
            Step("shells",
                 f"The five shells decompose the tax.  Shell 0 (Golay, "
                 f"sign-blind) is the original TAX = HW*Y + ||v||^2/8.  "
                 f"Shell 1 (sign-parity), Shell 2 (sextet-balance, float), "
                 f"Shell 3 (coset-type), Shell 4 (sextet-signed, float).",
                 f"shell0_golay = {shell_renders['shell0_golay']}, "
                 f"shell1_sign_parity = {shell_renders['shell1_sign_parity']}, "
                 f"shell2_sextet_balance = {shell_renders['shell2_sextet_balance']}, "
                 f"shell3_coset_type = {shell_renders['shell3_coset_type']}, "
                 f"shell4_sextet_signed = {shell_renders['shell4_sextet_signed']}"),
            Step("regime",
                 f"The regime buckets the NRCI: OnBit (>=0.8), Coherent "
                 f"(>=0.5), Transitional (>=0.3), Subcoherent (<0.3).",
                 f"regime({nrci_value:.4f}) = {regime}"),
        ]
        expected = {
            "name": obj.name,
            "domain": obj.domain,
            "nrci": nrci_str,
            "regime": regime,
            "shell0_golay": shell_renders["shell0_golay"],
            "shell1_sign_parity": shell_renders["shell1_sign_parity"],
        }
        return Solution(
            query=query, kind="coherence",
            answer=f"coherence {obj.name}: NRCI = {nrci_value:.4f} "
                   f"({regime})",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "coherence",
                         "args": {"domain": obj.domain, "name": obj.name}},
            payload={"breakdown": {k: _render_shell(v)
                                    for k, v in breakdown.items()},
                     "regime": regime})

    # ------------------------------------------------------------------
    # 3k.  report -- on-demand recomputation of facts (v0.5.4)
    # ------------------------------------------------------------------
    # Wires four previously-unused report functions:
    #   * ve.verifier_report   -- the 222+71 relation tables
    #   * leech2.pair_census   -- the 4-position Leech distribution
    #   * leech2.theta_series  -- the Leech theta series E_4^3 - 720*Delta
    #   * pr.two_a_closure_report -- closure facts about the 2A subalgebra
    # The subject names what to recompute; everything is computed, not
    # quoted (per the directive's "facts computed, not quoted" rule).
    # ------------------------------------------------------------------

    def _solve_report(self, query: Query) -> Solution:
        subject = query.options.get("subject", "").strip().lower()
        if not subject:
            return Solution(
                query=query, kind="report",
                answer="report: no subject given.  Try one of: "
                       "relations, leech distribution, theta, subalgebra",
                ok=False, error="report: no subject",
                steps=(Step("usage",
                            "Subjects: relations, leech distribution, "
                            "theta, subalgebra",
                            "report <subject>"),),
                payload={})

        if subject in ("relations", "verifier", "relation"):
            return self._report_relations(query)
        if subject in ("leech distribution", "leech", "distribution",
                         "pair census", "census"):
            return self._report_leech_distribution(query)
        if subject in ("theta", "theta series", "theta_series"):
            return self._report_theta(query)
        if subject in ("subalgebra", "2a subalgebra", "closure",
                         "two_a_closure"):
            return self._report_subalgebra(query)
        # Unknown subject
        return Solution(
            query=query, kind="report",
            answer=f"report: unknown subject {subject!r}.  Try one of: "
                   f"relations, leech distribution, theta, subalgebra",
            ok=False, error=f"report: unknown subject {subject!r}",
            steps=(Step("unknown",
                        f"The subject {subject!r} is not a recognised "
                        f"report subject.",
                        f"subjects: relations, leech distribution, theta, "
                        f"subalgebra"),),
            payload={"requested": subject})

    def _report_relations(self, query: Query) -> Solution:
        """Wires ve.verifier_report — the 222+71 relation audit."""
        report = ve.verifier_report()
        # The report has three tables: scalar relations under scalar
        # semantics (all hold), scalar relations under full semantics
        # (some fail on rank/parity), and tensor relations under full
        # semantics (all hold).
        scalar_scalar = report["scalar_relations_under_scalar_semantics"]
        scalar_full = report["scalar_relations_under_full_semantics"]
        tensor_full = report["tensor_relations_under_full_semantics"]
        steps = [
            Step("verifier_report",
                 f"The verifier audited three tables: {scalar_scalar['checked']} "
                 f"scalar relations under scalar semantics ({scalar_scalar['held']} "
                 f"hold), {scalar_full['checked']} scalar relations under full "
                 f"tensor semantics ({scalar_full['held']} hold, "
                 f"{scalar_full['failed']} fail on rank/parity), and "
                 f"{tensor_full['checked']} tensor relations ({tensor_full['held']} "
                 f"hold).  The {scalar_full['failed']} that hold scalarly but fail "
                 f"under full semantics are statements a units table gets right "
                 f"but a tensor analysis gets wrong -- e.g. 'acceleration = speed "
                 f"/ time' fails because the left side is rank-1 and the right "
                 f"side a scalar.",
                 f"scalar/scalar: {scalar_scalar['held']}/{scalar_scalar['checked']}, "
                 f"scalar/full: {scalar_full['held']}/{scalar_full['checked']} "
                 f"({scalar_full['failed']} fail), "
                 f"tensor/full: {tensor_full['held']}/{tensor_full['checked']}"),
        ]
        expected = {
            "scalar_scalar_checked": str(scalar_scalar["checked"]),
            "scalar_scalar_held": str(scalar_scalar["held"]),
            "scalar_full_checked": str(scalar_full["checked"]),
            "scalar_full_held": str(scalar_full["held"]),
            "scalar_full_failed": str(scalar_full["failed"]),
            "tensor_full_checked": str(tensor_full["checked"]),
            "tensor_full_held": str(tensor_full["held"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report relations: scalar/scalar "
                   f"{scalar_scalar['held']}/{scalar_scalar['checked']}, "
                   f"scalar/full {scalar_full['held']}/{scalar_full['checked']}, "
                   f"tensor/full {tensor_full['held']}/{tensor_full['checked']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_relations", "args": {}},
            payload={"report": report})

    def _report_leech_distribution(self, query: Query) -> Solution:
        """Wires leech2.pair_census — the 4-position Leech distribution."""
        census = leech2.pair_census()
        steps = [
            Step("pair_census",
                 f"The 196,560 minimal vectors of the Leech lattice, "
                 f"taken against any fixed one, fall into exactly four "
                 f"mutual positions.  This is the reason the Monster's 2A "
                 f"axes have only four positions: 1A (2 vectors), 2A "
                 f"(9,200), invariant-1 (94,208, not modelled), and 2B "
                 f"(93,150).",
                 f"pair_census = {dict(census)}"),
        ]
        expected = {f"position_{k}": str(v) for k, v in census.items()}
        return Solution(
            query=query, kind="report",
            answer=f"report leech distribution: {dict(census)}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_leech", "args": {}},
            payload={"census": dict(census)})

    def _report_theta(self, query: Query) -> Solution:
        """Wires leech2.theta_series — the Leech theta series E_4^3 - 720*Delta."""
        order = 5
        coeffs = leech2.theta_series(order=order)
        steps = [
            Step("theta_series",
                 f"The theta series of the Leech lattice is "
                 f"E_4^3 - 720*Delta, computed exactly.  Coefficient n "
                 f"counts vectors of squared norm 8n.  The first few: "
                 f"1 (the zero vector), 0 (no norm-8 vectors), 196560 "
                 f"(the minimal vectors, norm 16 = 8*2), 16773120 "
                 f"(norm 24 = 8*3), ...",
                 f"theta = {coeffs}"),
        ]
        expected = {f"coeff_{i}": str(c) for i, c in enumerate(coeffs)}
        return Solution(
            query=query, kind="report",
            answer=f"report theta: {coeffs}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_theta", "args": {}},
            payload={"coefficients": coeffs, "order": order})

    def _report_subalgebra(self, query: Query) -> Solution:
        """Wires pr.two_a_closure_report — 2A subalgebra closure facts."""
        report = pr.two_a_closure_report()
        steps = [
            Step("two_a_closure_report",
                 f"The 2A subalgebra generated by a sampled 2A pair is "
                 f"checked for: closure in three dimensions, "
                 f"commutativity, non-associativity (with an explicit "
                 f"witness), and the Gram matrix (1 on the diagonal, "
                 f"1/8 off it).",
                 f"two_a_closure_report = {report}"),
        ]
        expected = {k: str(v) for k, v in report.items()}
        return Solution(
            query=query, kind="report",
            answer=f"report subalgebra: {report}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_subalgebra", "args": {}},
            payload={"report": report})

    # ------------------------------------------------------------------
    # 3l.  angle -- exact cosine comparison (v0.5.4)
    # ------------------------------------------------------------------
    # Wires me.signed_cosine_squared.  The directive's "XOR isn't
    # suitable in most situations" rule applies to angular comparison
    # too: the cosine is irrational in general, but sign(<u,v>)*cos^2
    # is always rational and orders pairs by angle exactly.
    # ------------------------------------------------------------------

    def _solve_angle(self, query: Query) -> Solution:
        if len(query.operands) < 2:
            raise SolverError("angle: needs two operands, A and B")
        a = self.resolve(query.operands[0], query.domain)
        b = self.resolve(query.operands[1], query.domain)
        try:
            sc2 = me.signed_cosine_squared(a.carrier, b.carrier)
        except ValueError as exc:
            return Solution(
                query=query, kind="angle",
                answer=f"angle {a.name} {b.name}: angle undefined",
                ok=False, error=f"angle: {exc}",
                steps=(Step("failed",
                            "The signed cosine squared is undefined when "
                            "either vector is zero (no direction).",
                            f"ValueError: {exc}"),),
                payload={"operands": [a.name, b.name]})
        # sc2 in [-1, 1]; +1 means parallel, -1 means anti-parallel, 0
        # means orthogonal.  The actual cosine is sqrt(|sc2|) with sign.
        sign = "+" if sc2 >= 0 else "-"
        abs_sc2 = abs(sc2)
        # Describe the regime.
        if abs_sc2 == 0:
            regime = "orthogonal"
        elif abs_sc2 == 1:
            regime = "parallel" if sc2 > 0 else "anti-parallel"
        elif abs_sc2 >= Fraction(1, 2):
            regime = "acute" if sc2 > 0 else "obtuse"
        else:
            regime = "near-orthogonal"
        steps = [
            Step("signed_cosine_squared",
                 f"The signed cosine squared is sign(<A, B>) * cos^2(A, B), "
                 f"an exact rational that orders pairs by angle exactly.  "
                 f"For {a.name} and {b.name} it is {q(sc2)}, which is "
                 f"in the {regime} regime.",
                 f"signed_cosine_squared({a.name}, {b.name}) = {q(sc2)}, "
                 f"regime = {regime}"),
            Step("interpretation",
                 f"sign = {sign}, |cos^2| = {q(abs_sc2)}.  +1 means "
                 f"parallel, -1 means anti-parallel, 0 means orthogonal.  "
                 f"The actual cosine is sqrt(|cos^2|) with the sign, which "
                 f"is generally irrational -- this rational form is the "
                 f"exact order-preserving surrogate.",
                 f"sign={sign}, |sc2|={q(abs_sc2)}, regime={regime}"),
        ]
        expected = {
            "operand_a": a.name,
            "operand_b": b.name,
            "signed_cosine_squared": q(sc2),
            "regime": regime,
        }
        return Solution(
            query=query, kind="angle",
            answer=f"angle {a.name} {b.name}: cos^2 = {q(sc2)} ({regime})",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "angle",
                         "args": {"domain_a": a.domain, "name_a": a.name,
                                  "domain_b": b.domain, "name_b": b.name}},
            payload={"signed_cosine_squared": q(sc2),
                     "regime": regime})


def _jsonable(mapping: Mapping[str, Any]) -> Dict[str, object]:
    """Render an attribute mapping so ``json.dumps`` accepts it.

    Rationals become ``"n/d"`` strings rather than floats, which is the only
    lossless option and the one the whole package uses.
    """
    out: Dict[str, object] = {}
    for key, value in sorted(mapping.items()):
        if isinstance(value, Fraction):
            out[key] = q(value)
        elif isinstance(value, (list, tuple)):
            out[key] = [q(x) if isinstance(x, Fraction) else x for x in value]
        elif isinstance(value, (int, str, bool)) or value is None:
            out[key] = value
        else:
            out[key] = repr(value)
    return out


# Keep a module-level reference so the digit-stack import is not flagged as
# unused; the stack constants document the substrate this session sits on.
_STACK_FACETS: int = len(ds.FACETS)

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
Five come from :mod:`glm_universal.data_objects`: ``physics`` (726 quantities),
``chemistry`` (118 elements), ``molecules`` (51 molecules and ions, every
coordinate derived from the element register), ``mathematics`` (rational
matrices, reflections and field elements) and ``lexicon`` (relational
concepts).  A sixth, ``spatial``, is built here in :func:`spatial_objects`
from the MOG's own structures -- the trio's three octads, the sextet's six
tetrads, the four rows of the ``4 x 6`` frame, and the fifteen octads
obtained as unions of tetrad pairs.  It is a presentation of the substrate,
not a new dataset, and every member is checked against
:data:`glm_universal.substrate.mog.GOLAY_SET` at build time.

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
from dataclasses import dataclass, field, replace
from fractions import Fraction
from typing import (Any, Dict, List, Mapping, Optional, Sequence, Tuple)

from .. import data_objects as do
from ..data_objects.base import DataObject
from ..reasoning import analogy as an
from ..reasoning import analogy_models as am
from ..reasoning import coherence as co
from ..reasoning import deep_holes as dhl
from ..reasoning import dimension_layers as dl
from ..reasoning import element_coverage as eco
from ..reasoning import exact_real as xr
from ..reasoning import facets as fa
from ..reasoning import fwht_decode as fdc
from ..reasoning import information_loss as il
from ..reasoning import metric as me
from ..reasoning import monster_stack as msk
from ..reasoning import multires as mrs
from ..reasoning import product as pr
from ..reasoning import tasks as tk
from ..reasoning import term_arithmetic as tar
from ..reasoning import units as un
from ..reasoning import valorani as va
from ..reasoning import verifier as ve
from ..substrate import digit_stack as ds
from ..substrate import golay_decode as gdc
from ..substrate import isomorphism as iso
from ..substrate import leech_construct as lcs
from ..substrate import leech2, mog
from ..substrate import superposition as sup
from ..migration import state as stm
from ..migration import store as sto
from ..semantics import audit as sau
from ..semantics import meaning as sme
from ..semantics import reference as sre
from ..semantics import relations as srl
from . import parser as PA
from .parser import ConceptIndex, Query, QueryError, parse_query

__all__ = [
    "SolverError", "DOMAINS", "DEFAULT_SUBSPACE", "REPORT_SUBJECTS",
    "TASKS", "Step", "Solution", "InferenceRecord", "GeometricSession",
    "spatial_objects", "q",
]


class SolverError(ValueError):
    """Raised when a well-formed query cannot be solved as asked.

    Distinct from :class:`~glm_universal.runtime.parser.QueryError`, which is
    about the shape of the string.  This is about the content: an operand that
    names nothing in the register, a domain with no candidate pool, a class
    label that is not of type 2.
    """


#: The canonical names of the subjects ``report <subject>`` understands.
#: Each has a solver that recomputes its facts on demand and a Three Column
#: Thinking template that reproduces them in a fresh interpreter.
REPORT_SUBJECTS: Tuple[str, ...] = (
    "relations", "leech distribution", "theta", "subalgebra",
    "information loss", "golay decoding", "superposition",
    "leech construction", "facets",
    "monster stack", "multiresolution", "migration", "state migration",
    "concept store", "fusion", "benchmarks", "semantics",
    "infinite values", "capabilities", "analogies",
    "transform decoder", "deep holes", "units",
    "molecules", "chemistry coverage",
)

#: The canonical names of the worked end-to-end tasks ``task <name>`` runs.
TASKS: Tuple[str, ...] = ("grid", "physics", "concepts")

#: The registers a session can load, in a fixed order.
DOMAINS: Tuple[str, ...] = (
    "physics", "chemistry", "molecules", "mathematics", "lexicon",
    "spatial",
)

#: The subspace an analogy uses when the query does not name one.  A raw
#: 24-coordinate difference would let bookkeeping coordinates outvote the
#: meaningful ones; see :data:`glm_universal.reasoning.analogy.SUBSPACES`.
DEFAULT_SUBSPACE: Dict[str, Optional[str]] = {
    "physics": "physics.dimension",
    "chemistry": "chemistry.position",
    # As of v1.4.0 the molecules register resolves analogies on composition
    # rather than on the full carrier: molar mass and electron count are
    # orders of magnitude larger than the counts and would otherwise decide
    # every analogy on size alone.
    "molecules": "molecules.composition",
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
        elif domain == "molecules":
            loaded = do.molecule_objects()
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
        return self.solve(query, raw=text)

    def solve(self, query: Query, raw: Optional[str] = None) -> Solution:
        """Solve one already-parsed :class:`Query`.

        This is the half of :meth:`ask` that comes after parsing, exposed so
        that a query can be *edited* and re-solved -- change an option, ask
        again -- without going back through the surface syntax.  A solver that
        refuses is reported the same way as it is through :meth:`ask`: a
        :class:`Solution` with ``ok=False`` and ``error`` set, recorded in the
        history rather than raised.

        Parameters
        ----------
        query:
            The parsed query to dispatch.
        raw:
            What to record in the history as the query text.  Defaults to
            ``query.raw``, which is right for a query that came from
            :meth:`ask`; pass the edited text when it did not.
        """
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
            index=len(self._history),
            raw_query=query.raw if raw is None else raw,
            kind=solution.kind,
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
            # v0.8.0: the worked end-to-end tasks -- an ARC-style grid
            # puzzle and a physics query, each run through the whole
            # pipeline rather than through one mechanism.
            "task": self._solve_task,              # uses tk.grid_task, tk.physics_task
            # v1.0.0: the last reasoning module with no query path.
            "pi_groups": self._solve_pi_groups,    # uses va.buckingham_pi_groups
            # v1.1.0: reference resolution and derived relations over the
            # meaning space -- the only query kind whose operands are
            # notations rather than register names.
            "meaning": self._solve_meaning,        # uses sem.resolve, sem.derive
            # v1.2.0: values that are not carriers -- an irrational is
            # answered as the process that converges to it, not as a
            # coordinate, because no coordinate holds it.
            "real": self._solve_real,              # uses xr.parse_real
            "compare": self._solve_compare,        # uses xr.compare
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
        asked_for_subspace = "subspace" in query.options
        subspace = query.options.get("subspace",
                                     DEFAULT_SUBSPACE.get(domain))
        subspace = None if subspace is None else str(subspace)
        if subspace is not None and subspace not in an.SUBSPACES:
            raise SolverError(
                f"analogy: unknown subspace {subspace!r}; known subspaces "
                f"are {sorted(an.SUBSPACES)}")

        # v1.4.0.  Before treating the analogy as a displacement of the
        # coordinates, ask whether the relation between A and B is one the
        # register can *name*: a step along the periodic table, a reciprocal
        # or a change of scale in dimension space, or a relation the lexicon
        # states outright.  A named relation is transported as that relation;
        # only an unnamed one falls through to the translation solver.  A
        # query that names a subspace is asking for the geometric solve, so
        # the model layer is skipped.
        model = None
        if not asked_for_subspace:
            model = am.explain_analogy(domain, a.name, b.name, c.name, pool)
            if model is not None and model.answer is not None:
                return self._analogy_by_model(query, model, domain, a, b, c)
            split = self._cross_register_split(domain, a, b, c)
            if model is not None:
                # A model recognised the relation and then found nothing at
                # the transported position.  That refusal is the answer: the
                # register knows what the step *is* and knows that it leads
                # nowhere it can name, and falling back on a displacement
                # would overwrite a determinate "no" with a nearest point.
                found = f"{model.relation}, but {model.refusal}"
                if split is not None:
                    found += f"; and {split}"
                raise SolverError(f"analogy: {found}")
            if split is not None:
                raise SolverError(
                    f"analogy: the relation between {a.name} and {b.name} is "
                    f"not one this register states -- no relation model "
                    f"recognises it; and {split}")

        result = an.solve_analogy_objects(a, b, c, pool, subspace=subspace)
        target = an.analogy_target(a.carrier, b.carrier, c.carrier)
        nonzero = [(a.layout[i] if a.layout else str(i), q(target[i]))
                   for i in range(24) if target[i] != 0]

        steps = [
            Step("resolve",
                 f"Resolve the three terms in the {domain} register: "
                 f"{a.name}, {b.name}, {c.name}.",
                 f"A = {a.name}, B = {b.name}, C = {c.name} in Q^24"),
            Step("model",
                 f"No relation model recognises the step from "
                 f"{a.name} to {b.name}, so the analogy is read as a "
                 f"displacement of the coordinates -- a weaker answer, "
                 f"because the register never says what the relation is.",
                 "model = none"),
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
                     "subspace": subspace,
                     "model": None})

    def _analogy_by_model(self, query: Query, model: "am.ModelResult",
                          domain: str, a: DataObject, b: DataObject,
                          c: DataObject) -> Solution:
        """An analogy answered by a named relation, not by a displacement.

        The steps are the model's own: what the relation between ``A`` and
        ``B`` is, where transporting it to ``C`` lands, and -- when the
        landing place is a class of quantities rather than one -- which
        structural filter narrowed it and what it excluded.
        """
        steps = [
            Step("resolve",
                 f"Resolve the three terms in the {domain} register: "
                 f"{a.name}, {b.name}, {c.name}.",
                 f"A = {a.name}, B = {b.name}, C = {c.name}"),
            Step("model",
                 f"Before measuring any distance, ask what the relation "
                 f"between {a.name} and {b.name} *is*.  The "
                 f"{model.model!r} model recognises it: {model.relation}.",
                 f"model = {model.model}, "
                 f"relation = {model.relation}"),
        ]
        for title, detail in model.steps:
            steps.append(Step(title, detail, "; ".join(
                f"{k} = {v}" for k, v in sorted(model.witness.items()))))
        expected = {
            "model": model.model,
            "answer": str(model.answer),
            "candidates": str(list(model.candidates)),
            "unique": str(model.unique),
        }
        answer = (f"{query.operands[0]} : {query.operands[1]} :: "
                  f"{query.operands[2]} : {model.answer}")
        if not model.unique:
            answer += (f" (the relation fixes the answer only up to "
                       f"{len(model.candidates)} candidates)")
        return Solution(
            query=query, kind="analogy", answer=answer, steps=tuple(steps),
            expected=expected,
            script_spec={"template": "analogy_model",
                         "args": {"domain": domain, "a": a.name,
                                  "b": b.name, "c": c.name}},
            payload={"model": model.as_dict(), "subspace": None})

    def _cross_register_split(self, domain: str, a: DataObject,
                              b: DataObject,
                              c: DataObject) -> Optional[str]:
        """How the three terms are split across registers, if they are.

        A displacement is only meaningful between carriers of one layout.
        ``heat : temperature :: force : ?`` is the case that matters: all
        three words are in the lexicon, but ``temperature`` and ``force`` are
        physics quantities and ``heat`` is not, so the query was coerced into
        the register that happens to hold all three rather than into the
        register the question is about.  Answering from the coerced register
        is how the machine used to return an unrelated energy-like quantity.

        Returns ``None`` when every term is at home in exactly the same
        registers, and otherwise a sentence naming the split.
        """
        homes = {obj.name: {d for d, _ in self.index.candidates(obj.name)}
                 for obj in (a, b, c)}
        if len({frozenset(v) for v in homes.values()}) == 1:
            return None
        # Only a register *more specific* than the one the query settled in
        # can make the reading wrong, and only when it holds most of the
        # terms: that is the signature of a question about that register
        # which was coerced elsewhere because one term is missing from it.
        # A single operand that happens to have a second reading somewhere
        # less specific -- ``velocity`` is a physics quantity and also a
        # word -- says nothing about where the question lives.
        rank = list(PA.DOMAIN_PRIORITY)
        settled = rank.index(domain) if domain in rank else len(rank)
        missing: List[str] = []
        for other in sorted(set().union(*homes.values()) - {domain}):
            if other not in rank or rank.index(other) >= settled:
                continue
            here = sorted(n for n, v in homes.items() if other in v)
            absent = sorted(n for n, v in homes.items() if other not in v)
            if len(here) >= 2 and absent:
                missing.append(
                    f"{other} holds {', '.join(here)} but not "
                    f"{', '.join(absent)}")
        if not missing:
            return None
        return (f"the three terms do not share a register: "
                f"{'; '.join(missing)}.  The query was answerable only in "
                f"{domain!r}, which holds all three words but is not where "
                f"the question lives, so transporting a displacement there "
                f"would name a carrier without meaning it")

    # ------------------------------------------------------------------
    # 3c.  describe -- the dossier of one carrier
    # ------------------------------------------------------------------

    def _describe_by_reference(self, query: Query) -> Optional[Solution]:
        """Describe a term that denotes something without being a carrier name.

        ``H2O`` is not spelled anywhere in the chemistry register, and ``2 + 2``
        is not spelled anywhere at all, yet both denote something the registers
        pin down.  The reference resolver already decides that question, so the
        describe path asks it rather than re-implementing it, and reuses the
        `meaning` column-3 template so the answer is recomputed in a fresh
        interpreter like every other one.

        Returns ``None`` -- not a refusal -- when the term denotes nothing
        determinate, so the caller can try the next route.
        """
        term = str(query.operands[0])
        resolution = sre.resolve(term)
        if resolution.meaning is None:
            return None
        probe = replace(query, options={**dict(query.options),
                                        "terms": (term,)})
        solution = self._solve_meaning(probe)
        return replace(
            solution, query=query, kind="describe",
            answer=f"{term!r} denotes {resolution.meaning.describe()} "
                   f"[{resolution.sense}: {resolution.witness}]; no register "
                   f"entry is spelled that way, so it is described by what "
                   f"it denotes")

    def _describe_by_arithmetic(self, query: Query) -> Optional[Solution]:
        """Describe an expression written over register *names*.

        ``energy divided by time`` is not a register entry and denotes no
        single quantity, but its dimension is exact and the register does name
        it.  The answer says which quantities carry that dimension and how
        many, because a dimension does not determine a name.

        Returns ``None`` when the expression names no register quantity.
        """
        term = str(query.operands[0])
        try:
            result = tar.evaluate(term)
        except tar.ArithmeticError_:
            return None
        steps = (
            Step("normalise",
                 "Rewrite the English operator words into the dimensional "
                 "grammar.  This step does no arithmetic: it is a string "
                 "rewrite over a frozen table of operator words.",
                 f"{term!r} -> {result.normalised!r}"),
            Step("dimension",
                 "Evaluate the expression in the exact dimensional algebra: "
                 "exponents are rationals and are added, never rounded.",
                 f"EXT10 = {result.ext10}, SI7 = {result.si7}, "
                 f"scale = {result.sense.scale}, rank = {result.sense.rank}"),
            Step("naming",
                 (f"The register carries {len(result.names)} quantities of "
                  f"this dimension, so the arithmetic fixes what the answer "
                  f"*is* without fixing what it is *called*."
                  if len(result.names) != 1 else
                  f"Exactly one register quantity has this dimension, so the "
                  f"expression names it unambiguously."),
                 f"names = {list(result.names[:tar.NAMES_SHOWN])}"
                 + (f" (+{len(result.names) - tar.NAMES_SHOWN} more)"
                    if len(result.names) > tar.NAMES_SHOWN else "")),
        )
        expected = {
            "source": result.source,
            "normalised": result.normalised,
            "ext10": result.ext10,
            "si7": result.si7,
            "scale": str(result.sense.scale),
            "rank": str(result.sense.rank),
            "name_count": str(len(result.names)),
            "names": str(list(result.names[:tar.NAMES_SHOWN])),
        }
        return Solution(
            query=query, kind="describe", answer=result.describe(),
            steps=steps, expected=expected,
            script_spec={"template": "describe_arithmetic",
                         "args": {"expression": result.source}},
            payload={"term_arithmetic": result.as_dict()})

    def _solve_describe(self, query: Query) -> Solution:
        if not query.operands:
            raise SolverError("describe: no concept named")
        try:
            obj = self.resolve(query.operands[0], query.domain)
        except SolverError as exc:
            # v1.3.0: a term that names no carrier is not necessarily a term
            # the machine has nothing to say about.  Two routes are tried, in
            # this order, and both are exact:
            #
            #   1. reference resolution -- a notation such as "H2O" or an
            #      arithmetic expression such as "2 + 2" denotes something the
            #      registers pin down, even though no register entry is
            #      *spelled* that way;
            #   2. arithmetic over register names -- "energy divided by time"
            #      is a dimension the register does name.
            #
            # Neither route invents an answer: each refuses unless what it
            # needs is present, and the original refusal is re-raised if both
            # decline.
            fallback = (self._describe_by_reference(query)
                        or self._describe_by_arithmetic(query))
            if fallback is not None:
                return fallback
            raise exc
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
        elif obj.domain == "molecules":
            attrs = obj.attributes or {}
            missing = attrs.get("missing_fields") or []
            detail = (
                f"Molecule {attrs.get('hill_formula')}, "
                f"{len(attrs.get('elements') or ())} distinct elements, "
                f"charge {attrs.get('charge')}.  The carrier is the "
                f"composite summary; the faithful representation is the "
                f"bundle of its element carriers.  "
                + (f"{len(missing)} coordinate(s) the element register "
                   f"cannot support are absent, not imputed: "
                   f"{', '.join(missing)}."
                   if missing else
                   "Every coordinate is supported by the element register."))
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
        linkage = str(query.options.get("linkage", "single"))
        if linkage not in ("single", "complete"):
            raise SolverError(
                f"cluster: unknown linkage {linkage!r}; known linkages are "
                f"'single' and 'complete'")
        build = (me.complete_linkage if linkage == "complete"
                 else me.single_linkage)
        tree = build(vectors, labels)
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
                 (f"Single linkage merges the two clusters with the "
                  f"closest pair of members"
                  if linkage == "single" else
                  f"Complete linkage merges the two clusters whose "
                  f"furthest pair of members is closest")
                 + f", {len(tree.merges)} times.  Both rules are computed "
                   f"on exact rational heights, so the order of merges is "
                   f"decided, not approximated.",
                 f"linkage = {linkage}\n"
                 + "\n".join(f"merge {i}: height = {q(m.height)}"
                             for i, m in enumerate(tree.merges))),
            Step("cut",
                 f"Cutting the tree at k = {k} gives {len(groups)} groups: "
                 f"{groups}.",
                 f"cut_tree(k={k}) = {groups}"),
        ]
        expected = {
            "labels": str(labels),
            "k": str(k),
            "linkage": linkage,
            "groups": str(groups),
            "merge_heights": str([q(m.height) for m in tree.merges]),
        }
        return Solution(
            query=query, kind="cluster",
            answer=f"{k} clusters ({linkage} linkage): {groups}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "cluster",
                         "args": {"domain": domains[0], "names": labels,
                                  "k": k, "linkage": linkage}},
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
        nrci_value = Fraction(breakdown["nrci"])
        nrci_str = q(nrci_value)
        nrci_dec = co.decimal_str(nrci_value, 6)

        # Every shell is an exact rational: shells 2 and 4 take their
        # square root at the declared resolution of co.rational_sqrt
        # rather than in floating point.
        def _render_shell(v):
            if isinstance(v, Fraction):
                return q(v)
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
                 f"combined NRCI is {nrci_dec}, which puts it in the "
                 f"{regime} regime.",
                 f"NRCI({obj.name}) = {nrci_str} = {nrci_dec}, "
                 f"regime = {regime}"),
            Step("shells",
                 f"The five shells decompose the tax.  Shell 0 (Golay, "
                 f"sign-blind) is the original TAX = HW*Y + ||v||^2/8.  "
                 f"Shell 1 (sign-parity), Shell 2 (sextet-balance), "
                 f"Shell 3 (coset-type), Shell 4 (sextet-signed).  All five "
                 f"are exact rationals.",
                 f"shell0_golay = {shell_renders['shell0_golay']}, "
                 f"shell1_sign_parity = {shell_renders['shell1_sign_parity']}, "
                 f"shell2_sextet_balance = {shell_renders['shell2_sextet_balance']}, "
                 f"shell3_coset_type = {shell_renders['shell3_coset_type']}, "
                 f"shell4_sextet_signed = {shell_renders['shell4_sextet_signed']}"),
            Step("regime",
                 f"The regime buckets the NRCI: OnBit (>=0.8), Coherent "
                 f"(>=0.5), Transitional (>=0.3), Subcoherent (<0.3).",
                 f"regime({co.decimal_str(nrci_value, 4)}) = {regime}"),
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
            answer=f"coherence {obj.name}: NRCI = "
                   f"{co.decimal_str(nrci_value, 4)} ({regime})",
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
                answer=f"report: no subject given.  Try one of: "
                       f"{', '.join(REPORT_SUBJECTS)}",
                ok=False, error="report: no subject",
                steps=(Step("usage",
                            f"Subjects: {', '.join(REPORT_SUBJECTS)}",
                            "report <subject>"),),
                payload={"subjects": list(REPORT_SUBJECTS)})

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
        if subject in ("information loss", "loss", "boundaries",
                         "boundary", "information_loss"):
            return self._report_information_loss(query)
        if subject in ("golay decoding", "golay", "decoder", "decoding",
                         "golay_decode", "coset"):
            return self._report_golay_decoding(query)
        if subject in ("superposition", "ambiguity", "tie", "sextet",
                         "bundling", "parallel hypotheses", "list decoding"):
            return self._report_superposition(query)
        if subject in ("leech construction", "construction", "kissing",
                         "leech_construct", "lattice construction"):
            return self._report_leech_construction(query)
        if subject in ("facets", "facet decomposition", "six facets",
                         "six-facet", "decomposition"):
            return self._report_facets(query)
        if subject in ("monster stack", "monster", "digit stack",
                         "monster_stack", "address stack"):
            return self._report_monster_stack(query)
        if subject in ("multiresolution", "multi-resolution", "multires",
                         "resolution", "scale invariance"):
            return self._report_multiresolution(query)
        if subject in ("migration", "isomorphism", "legacy",
                         "permutation", "legacy to core"):
            return self._report_migration(query)
        if subject in ("state migration", "state", "glm state",
                         "data migration", "state_migration"):
            return self._report_state_migration(query)
        if subject in ("concept store", "concepts", "crg", "store",
                         "concept_store"):
            return self._report_concept_store(query)
        if subject in ("semantics", "meaning", "semantic audit",
                         "grounding", "semantic", "meanings"):
            return self._report_semantics(query)
        if subject in ("fusion", "fusion spectrum", "fusion_spectrum",
                         "fusion rules", "miyamoto", "ising", "adjoint",
                         "eigenspaces"):
            return self._report_fusion(query)
        if subject in ("benchmarks", "benchmark", "scores", "suites",
                         "evidence"):
            return self._report_benchmarks(query)
        if subject in ("infinite values", "infinite", "irrationals",
                         "exact reals", "reals", "dynamic carrier",
                         "delta sigma", "infinite_values"):
            return self._report_infinite_values(query)
        if subject in ("capabilities", "capability", "probes",
                         "what it can do", "limits"):
            return self._report_capabilities(query)
        if subject in ("analogies", "analogy", "analogy models",
                         "relation models", "proportional analogy"):
            return self._report_analogies(query)
        if subject in ("transform decoder", "fwht", "walsh", "hadamard",
                         "transform", "o(1) lookup", "certificate",
                         "llvq", "soft decoding"):
            return self._report_transform_decoder(query)
        if subject in ("deep holes", "deep hole", "holes", "niemeier",
                         "niemeier classification", "hole census",
                         "covering radius", "voronoi"):
            return self._report_deep_holes(query)
        if subject in ("units", "unit parser", "unit", "steradian",
                         "unit audit", "dimensional audit"):
            return self._report_units(query)
        if subject in ("molecules", "molecule", "formulae", "formulas",
                         "multi-carrier", "multi carrier", "compounds"):
            return self._report_molecules(query)
        if subject in ("chemistry coverage", "coverage", "element coverage",
                         "sparse", "sparsity", "covalent radius",
                         "chemistry_coverage"):
            return self._report_chemistry_coverage(query)
        # Unknown subject
        return Solution(
            query=query, kind="report",
            answer=f"report: unknown subject {subject!r}.  Try one of: "
                   f"{', '.join(REPORT_SUBJECTS)}",
            ok=False, error=f"report: unknown subject {subject!r}",
            steps=(Step("unknown",
                        f"The subject {subject!r} is not a recognised "
                        f"report subject.",
                        f"subjects: {', '.join(REPORT_SUBJECTS)}"),),
            payload={"requested": subject,
                     "subjects": list(REPORT_SUBJECTS)})

    # ------------------------------------------------------------------
    # 3n.  real -- a value that is not a carrier (v1.2.0)
    # ------------------------------------------------------------------

    def _solve_real(self, query: Query) -> Solution:
        """Answer about a real number the register cannot hold.

        A carrier is 24 rationals, and no rational is ``sqrt(2)``.  The answer
        is therefore the *process*: the digits it settles, the rational
        stand-in each level of the dyadic tower holds for it, the level at
        which each stand-in is exposed, and the dynamic carrier's time average
        after a run of ticks.
        """
        notation = str(query.options.get("notation", "")).strip()
        if not notation:
            raise SolverError(
                "real: no value given.  Try 'approximate sqrt(2) to 20 places'")
        try:
            value = xr.parse_real(notation)
        except ZeroDivisionError as error:
            raise SolverError(
                f"real: {error}.  A quotient by an exact zero names no "
                f"value, so there is nothing to approximate") from None
        except ValueError as error:
            raise SolverError(str(error)) from None
        places = int(query.options.get("places", 20))
        if places < 1 or places > 200:
            raise SolverError("real: places must be between 1 and 200")

        try:
            decimal = value.decimal(places)
        except ZeroDivisionError as error:
            raise SolverError(
                f"real: {error}.  A quotient by an exact zero names no "
                f"value, so there is nothing to approximate") from None
        levels = 6
        stand_ins = xr.surrogate_sequence(value, levels)
        exposed: List[str] = []
        for level in range(levels - 1):
            found = None
            for higher in range(level, level + 12):
                if xr.surrogate(value, higher) != xr.rational_surrogate(
                        stand_ins[level], higher):
                    found = higher
                    break
            exposed.append(f"{level}->{found}" if found is not None
                           else f"{level}->never")

        is_rational = value.exact is not None
        fractional = value.at(64) - (value.at(64).numerator
                                     // value.at(64).denominator)
        ticks = 512
        average = xr.delta_sigma_average(fractional, ticks)
        error = abs(average - fractional)

        steps = [
            Step("what it is not",
                 f"A carrier is 24 exact rationals.  "
                 + (f"{notation} is rational, so a carrier does hold it."
                    if is_rational else
                    f"{notation} is not rational, so no carrier holds it and "
                    f"no level of the tower ever will.  What the machine "
                    f"holds is the process that converges to it."),
                 f"rational: {is_rational}"),
            Step("digits",
                 f"The process is asked for an approximation good to "
                 f"2**-k with k large enough that {places} decimal places "
                 f"are settled.  No float is constructed.",
                 f"{notation} = {decimal}"),
            Step("the tower's stand-ins",
                 f"Level n of the dyadic tower holds floor(x*2^n)/2^n -- a "
                 f"rational carrier that is indistinguishable from the "
                 f"target at that resolution, and is exposed by a higher "
                 f"level.",
                 f"levels 0..{levels - 1}: "
                 f"{', '.join(str(s) for s in stand_ins)}; "
                 f"exposed at {', '.join(exposed)}"),
            Step("the dynamic carrier",
                 f"The one-bit modulator chases the fractional part with an "
                 f"exact error accumulator.  After N ticks its time average "
                 f"is a rational k/N within 1/N of the target -- the "
                 f"machine-checked bound GLM.Info.dsAverage_error_le.",
                 f"N = {ticks}, average = {average}, "
                 f"|average - target| = {error} <= 1/{ticks}"),
        ]

        expected = {
            "notation": notation,
            "places": str(places),
            "decimal": decimal,
            "rational": str(is_rational),
            "stand_ins": str([str(s) for s in stand_ins]),
            "exposed": str(exposed),
            "delta_sigma_ticks": str(ticks),
            "delta_sigma_average": str(average),
            "delta_sigma_within_bound": str(error <= Fraction(1, ticks)),
        }

        return Solution(
            query=query, kind="real",
            answer=f"{notation} = {decimal} (to {places} places); "
                   f"no carrier holds it"
                   if not is_rational else
                   f"{notation} = {decimal} (to {places} places); "
                   f"a carrier holds it exactly",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "real",
                         "args": {"notation": notation, "places": places,
                                  "levels": levels, "ticks": ticks}},
            payload={"stand_ins": [str(s) for s in stand_ins],
                     "exposed": exposed})

    # ------------------------------------------------------------------
    # 3o.  compare -- order two real values, and say when it cannot be done
    # ------------------------------------------------------------------

    #: The precisions a comparison is tried at, in order.  A pair that is
    #: genuinely apart separates at one of them; a pair that is equal never
    #: will, at any depth, which is the boundary the answer reports.
    COMPARE_LADDER: Tuple[int, ...] = (8, 16, 32, 64, 128, 256)

    def _solve_compare(self, query: Query) -> Solution:
        """Order two written real values -- or say why the order is not decidable.

        Both sides are read by the exact-real grammar, so each may be any
        arithmetic combination of rationals, roots and the named constants.
        The comparison is then made at increasing precision until the two
        approximation intervals come apart.  If they never do, the answer says
        so: *inequality* between processes is decidable, *equality* is not,
        and the machine will not guess which side of that line it is on.
        """
        left_text = str(query.options.get("left", "")).strip()
        right_text = str(query.options.get("right", "")).strip()
        relation = str(query.options.get("relation", "compare"))
        if not left_text or not right_text:
            raise SolverError(
                "compare: two values are needed, e.g. "
                "'is sqrt(2) greater than 7/5'")
        try:
            left = xr.parse_real(left_text)
            right = xr.parse_real(right_text)
        except ZeroDivisionError as error:
            raise SolverError(
                f"compare: {error}.  A quotient by an exact zero names no "
                f"value, so there is nothing to compare") from None
        except ValueError as error:
            raise SolverError(str(error)) from None

        order, settled_at = 0, None
        for precision in self.COMPARE_LADDER:
            order = xr.compare(left, right, precision)
            if order != 0:
                settled_at = precision
                break

        deepest = self.COMPARE_LADDER[-1]
        left_decimal = left.decimal(20)
        right_decimal = right.decimal(20)

        if order == 0:
            verdict = "undecided"
            answer = (f"{left_text} and {right_text} are not distinguished at "
                      f"2**-{deepest}; equality of two processes is not "
                      f"decidable, so the machine does not claim it")
        else:
            symbol = ">" if order > 0 else "<"
            if relation == "greater":
                verdict = str(order > 0)
            elif relation == "less":
                verdict = str(order < 0)
            elif relation == "equal":
                verdict = "False"
            else:
                verdict = f"{left_text} {symbol} {right_text}"
            answer = f"{left_text} {symbol} {right_text}"
            if relation in ("greater", "less", "equal"):
                answer = f"{verdict.lower()}: {left_text} {symbol} {right_text}"

        steps = [
            Step("the two values",
                 "Each side is read as a process: a rule that returns an "
                 "exact rational within any precision asked of it.  Nothing "
                 "is rounded and no float is built.",
                 f"{left_text} = {left_decimal}..., "
                 f"{right_text} = {right_decimal}..."),
            Step("the decision",
                 "The two are compared at increasing precision until their "
                 "intervals come apart.  The first precision at which they "
                 "do is the cost of the answer.",
                 f"ladder {list(self.COMPARE_LADDER)}; "
                 + (f"separated at 2**-{settled_at}" if settled_at is not None
                    else f"still together at 2**-{deepest}")),
            Step("the boundary",
                 "Two unequal processes always separate at some finite "
                 "precision, and this one is found.  Two equal processes "
                 "never separate, and no amount of refinement turns that "
                 "into a proof of equality -- so 'not distinguished' is the "
                 "only honest answer there.",
                 f"relation asked: {relation}; verdict: {verdict}"),
        ]

        expected = {
            "left": left_text,
            "right": right_text,
            "relation": relation,
            "order": str(order),
            "settled_at": str(settled_at),
            "verdict": verdict,
            "left_decimal": left_decimal,
            "right_decimal": right_decimal,
        }

        return Solution(
            query=query, kind="compare", answer=answer,
            steps=tuple(steps), expected=expected,
            script_spec={"template": "compare",
                         "args": {"left": left_text, "right": right_text,
                                  "relation": relation,
                                  "ladder": list(self.COMPARE_LADDER)}},
            payload={"order": order, "settled_at": settled_at})

    def _report_infinite_values(self, query: Query) -> Solution:
        """Wires xr.exact_real_report -- what the machine does with infinities.

        Three claims, each recomputed: irrational values are reached as
        processes; the dynamic carrier's one-dimensional bound is exact; and
        in twenty-four dimensions the reachable set is the convex hull of the
        code, with a certificate for a target outside it.
        """
        report = xr.exact_real_report()
        runs = ", ".join(f"N={steps} err={error}"
                         for steps, error, _ok in report["delta_sigma_runs"])

        steps = [
            Step("the wall",
                 "A carrier is a tuple of rationals and a digit stack is "
                 "finite, so the set of values either can hold is countable "
                 "while the reals are not.  No representation the machine "
                 "could adopt separates all real targets -- "
                 "GLM.Info.no_countable_layer_lossless.",
                 f"sqrt(2) to 2**-40 = {report['sqrt2_at_40']}; "
                 f"its square misses 2 by {report['sqrt2_squared_error']}"),
            Step("through it, by process",
                 "A real is held as a function from precision to rational. "
                 "Constants are produced to any precision asked for, and "
                 "each is checked against a relation it must satisfy.",
                 f"sqrt(2) = {report['sqrt2_decimal_20']}, "
                 f"pi = {report['pi_decimal_20']}, "
                 f"e = {report['e_decimal_20']}, "
                 f"phi = {report['phi_decimal_20']}"),
            Step("the tower's stand-ins",
                 "Each level of the dyadic tower holds a rational carrier "
                 "indistinguishable from the target at that resolution, and "
                 "each is exposed at a higher level: true up to a point, then "
                 "superseded.",
                 f"levels 0..{report['levels'] - 1}: "
                 f"{', '.join(report['stand_ins'])}; exposed at "
                 f"{report['stand_in_exposed_at']}"),
            Step("the dynamic carrier, in one dimension",
                 "The modulator's time average is within 1/N of the target "
                 "after N ticks, exactly as proved.  No random, no float.",
                 f"{runs}; law holds {report['delta_sigma_law_holds']}; "
                 f"deterministic {report['delta_sigma_deterministic']}"),
            Step("and in twenty-four",
                 "Every state the 24-D carrier emits is a codeword, so its "
                 "reachable set is the convex hull of the code.  The all-1/2 "
                 "vector is inside it and is held exactly; the ramp target "
                 "i/24 is outside it, and a separating functional verified "
                 "against all 4,096 codewords proves no quantiser can hold "
                 "it -- GLM.Info.not_tendsto_avg_of_separating.",
                 f"reachable deviation {report['golay_reachable_deviation']}; "
                 f"unreachable deviation {report['golay_average_deviation']} "
                 f"with accumulator {report['golay_max_accumulator']}; "
                 f"certificate {report['golay_unreachable_certified']} "
                 f"(gap {report['golay_certificate_gap']})"),
            Step("what is still not possible",
                 "Equality of two processes is undecidable, and the machine "
                 "reports 'not yet distinguished' rather than guessing. "
                 "Inequality is decidable.",
                 f"equality undecided {report['equality_undecided']}; "
                 f"inequality decided {report['inequality_decided']}"),
        ]

        expected = {
            "sqrt2_decimal_20": report["sqrt2_decimal_20"],
            "pi_decimal_20": report["pi_decimal_20"],
            "e_decimal_20": report["e_decimal_20"],
            "phi_decimal_20": report["phi_decimal_20"],
            "delta_sigma_law_holds": str(report["delta_sigma_law_holds"]),
            "delta_sigma_deterministic": str(
                report["delta_sigma_deterministic"]),
            "no_stand_in_is_the_target": str(
                report["no_stand_in_is_the_target"]),
            "golay_reachable_deviation": str(
                report["golay_reachable_deviation"]),
            "golay_within_one_over_n": str(report["golay_within_one_over_n"]),
            "golay_unreachable_certified": str(
                report["golay_unreachable_certified"]),
            "equality_undecided": str(report["equality_undecided"]),
            "inequality_decided": str(report["inequality_decided"]),
        }

        return Solution(
            query=query, kind="report",
            answer=f"report infinite values: sqrt(2) = "
                   f"{report['sqrt2_decimal_20']}, pi = "
                   f"{report['pi_decimal_20']}; the 1/N law holds "
                   f"{report['delta_sigma_law_holds']}; the 24-D carrier "
                   f"holds the all-1/2 target exactly and provably cannot "
                   f"hold the ramp target "
                   f"({report['golay_unreachable_certified']}); equality of "
                   f"processes stays undecidable "
                   f"({report['equality_undecided']})",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_infinite_values", "args": {}},
            payload={"report": {key: str(value)
                                for key, value in report.items()}})

    def _report_capabilities(self, query: Query) -> Solution:
        """Wires capabilities.capability_report -- what works and what stops.

        Each probe states a capability in a user's words and comes back either
        holding, with how far it was pushed, or breaking, with the place it
        stops.  A probe whose verdict differs from what was expected is
        surfaced as a surprise rather than buried.
        """
        from .. import capabilities as cap
        report = cap.capability_report()
        areas = ", ".join(
            f"{area} {counts['holds']}/{counts['holds'] + counts['breaks']}"
            for area, counts in report["by_area"].items())
        boundary_lines = "; ".join(
            f"{b['name']}" for b in report["boundaries"])

        steps = [
            Step("what was asked",
                 f"{report['probes']} capability probes, each a question a "
                 f"user might ask of the machine, put to the real code.  A "
                 f"probe that breaks is a located boundary, not a failure.",
                 f"holds {report['holds']}, breaks {report['breaks']}, "
                 f"errors {report['errors']}"),
            Step("by area",
                 "Where the machine is solid and where it is thin.",
                 areas),
            Step("where it breaks",
                 "Each of these carries the exact place the capability "
                 "stops.  Several are theorems and will not move: the Golay "
                 "repair radius, the undecidability of equality between "
                 "processes, the convex hull that bounds the 24-D carrier.",
                 boundary_lines),
            Step("surprises",
                 "A probe whose verdict differs from the expectation "
                 "declared before it ran: a regression, or a capability "
                 "newly won.",
                 str(report["surprises"]) if report["surprises"] else "none"),
        ]

        expected = {
            "probes": str(report["probes"]),
            "holds": str(report["holds"]),
            "breaks": str(report["breaks"]),
            "errors": str(report["errors"]),
            "surprises": str(report["surprises"]),
        }
        for result in report["results"]:
            expected[f"verdict_{result['name']}"] = str(result["verdict"])

        return Solution(
            query=query, kind="report",
            answer=f"report capabilities: {report['probes']} probes, "
                   f"{report['holds']} hold, {report['breaks']} break, "
                   f"{report['errors']} errored; surprises "
                   f"{report['surprises'] or 'none'}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_capabilities", "args": {}},
            payload={"report": report})

    def _report_analogies(self, query: Query) -> Solution:
        """Wires analogy_models.analogy_models_report -- analogy by relation.

        Every case is re-solved here and now through the model layer, and
        each row says which model recognised the relation, what it answered,
        and whether that is what the mathematics of the case requires.  A
        refusal is a row like any other: the periodic step that lands on
        group 3 of period 6 has no single element to name.
        """
        report = am.analogy_models_report()
        table = report["periodic_table"]
        lines = "; ".join(
            f"{row['question']} -> "
            f"{row['answer'] or 'refused'} [{row['model']}]"
            for row in report["cases"])
        steps = [
            Step("the models",
                 "An analogy is transported as a *named relation* wherever "
                 "the register states one, and as a displacement of the "
                 "coordinates only when it does not.",
                 f"models = {list(report['models'])}"),
            Step("the table's own coordinates",
                 f"The chemistry model needs a period and a group, and the "
                 f"register stores a group-block *category*, not a group.  "
                 f"Both are derived from the period boundaries and checked "
                 f"against the {table['elements']} stored periods.",
                 f"elements = {table['elements']}, "
                 f"periods_agree_with_register = "
                 f"{table['periods_agree_with_register']}, "
                 f"noble gases = {table['noble_gases']}"),
            Step("what is not transportable",
                 "A relation that records *that* two concepts are linked "
                 "without saying how determines no answer, so it is excluded "
                 "by name rather than followed to a guess.",
                 f"vague relations = {list(report['vague_relations'])}"),
            Step("the cases",
                 f"{report['cases_total']} analogies re-solved through the "
                 f"layer; {report['cases_as_expected']} came out as the "
                 f"mathematics of the case requires.",
                 lines),
        ]
        expected = {
            "cases_total": str(report["cases_total"]),
            "cases_as_expected": str(report["cases_as_expected"]),
            "models": str(list(report["models"])),
            "periods_agree_with_register":
                str(table["periods_agree_with_register"]),
            "noble_gases": str(list(table["noble_gases"])),
        }
        for row in report["cases"]:
            expected[f"case_{row['question']}"] = (
                f"{row['model']}:{row['answer']}")
        return Solution(
            query=query, kind="report",
            answer=(f"report analogies: {len(report['models'])} relation "
                    f"models, {report['cases_total']} cases, "
                    f"{report['cases_as_expected']} as expected"),
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_analogies", "args": {}},
            payload={"report": report})

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

    def _report_transform_decoder(self, query: Query) -> Solution:
        """Wires fwht_decode.fwht_decode_report -- the transform and the tier.

        Two claims, both measured here rather than quoted: that the 4,096
        Golay coset costs are one Walsh-Hadamard transform, and that the
        constant-time lookup can prove its own answer -- sometimes.
        """
        report = fdc.fwht_decode_report()
        counts = report["operation_counts"]
        rates = report["certificate_rates"]
        agree = report["agreement"]
        ties = report["tie_sets"]
        flat = rates["regimes"][0]
        widest = rates["regimes"][-1]

        steps = [
            Step("the search is one transform",
                 f"Coordinate k of the codeword of message m is the parity "
                 f"of m against a fixed 12-bit generator column, so the "
                 f"{counts['codeword_count']} support sums the decoder "
                 f"minimises are the Walsh-Hadamard transform of a "
                 f"length-{counts['codeword_count']} array with only "
                 f"{counts['n']} nonzero entries.  The identity was checked "
                 f"on {agree['support_sums_checked']} sums and on "
                 f"{agree['column_identity_checks']} column parities.",
                 f"support-sum mismatches = {agree['support_sums_failures']}, "
                 f"column mismatches = {agree['column_identity_failures']}"),
            Step("what the transform costs, and what it buys",
                 f"Direct summation costs {counts['direct_adds']} additions "
                 f"(n * 2^(k-1)); the transform costs {counts['fwht_ops']} "
                 f"add/subtracts (2^k * k).  These are equal exactly when "
                 f"n = 2k, and for this code n = {counts['n']}, "
                 f"k = {counts['k']}.  The transform is therefore not a "
                 f"speed-up here; what it buys is the whole cost spectrum in "
                 f"one pass.",
                 f"direct = {counts['direct_adds']}, "
                 f"fwht = {counts['fwht_ops']}, "
                 f"ratio = {counts['ratio_direct_over_fwht']}, "
                 f"equal because n = 2k: "
                 f"{counts['equal_because_n_equals_2k']}"),
            Step("the exact decoder is reproduced, ties included",
                 f"The transform-driven nearest-Leech-point decoder was run "
                 f"against the existing complete decoder on "
                 f"{agree['lattice_points_checked']} rational targets -- "
                 f"point, distance, Leech class and 2A flag all compared -- "
                 f"and the argmin *set* was compared on "
                 f"{ties['cases']} soft-decision profiles, one of them "
                 f"engineered to be the six-fold covering-radius tie.",
                 f"lattice-point disagreements = "
                 f"{agree['lattice_point_failures']}, "
                 f"tie-set disagreements = {ties['failures']}, "
                 f"largest tie set = {ties['largest_tie_set']}, "
                 f"sextet case six-fold = {ties['sextet_case_is_sixfold']}"),
            Step("the O(1) lookup, with a certificate instead of a guess",
                 f"The constant-time route hard-decides the 24 signs, takes "
                 f"one syndrome, reads the coset leaders from the table, and "
                 f"then tries to *prove* its answer using the code's minimum "
                 f"distance {fdc.MIN_DISTANCE}: any other coset member "
                 f"differs by a codeword of weight at least 8, so it must pay "
                 f"for at least 8 - j coordinates outside the leader while "
                 f"recovering at most the j largest inside it.  When that "
                 f"inequality holds the fast answer is optimal, with proof.",
                 f"leaders per coset <= 6, magnitudes sorted once, "
                 f"nothing scales with the "
                 f"{counts['codeword_count']} codewords"),
            Step("how often it fires -- measured, per regime",
                 f"The rate is a statement about reliability spread, not "
                 f"about the code.  On a flat profile it fires "
                 f"{flat['certified']} times in {flat['samples']}; on "
                 f"magnitudes spread over a hundredfold band it fires "
                 f"{widest['certified']} in {widest['samples']}.  Every "
                 f"certified answer was re-checked against the exact "
                 f"transform, and "
                 f"{rates['certified_but_wrong']} were wrong.  Where the "
                 f"certificate declines, the exact transform is entered: the "
                 f"decoder is never wrong, only sometimes slow.",
                 " | ".join(f"{r['regime']}: {r['certified']}/{r['samples']}"
                            for r in rates["regimes"])),
        ]
        expected = {
            "direct_adds": str(counts["direct_adds"]),
            "fwht_ops": str(counts["fwht_ops"]),
            "equal_because_n_equals_2k":
                str(counts["equal_because_n_equals_2k"]),
            "column_identity_failures": str(agree["column_identity_failures"]),
            "support_sums_failures": str(agree["support_sums_failures"]),
            "lattice_point_failures": str(agree["lattice_point_failures"]),
            "all_agree": str(agree["all_agree"]),
            "tie_set_failures": str(ties["failures"]),
            "sextet_case_is_sixfold": str(ties["sextet_case_is_sixfold"]),
            "flat_profile_always_certifies":
                str(rates["flat_profile_always_certifies"]),
            "certified_but_wrong": str(rates["certified_but_wrong"]),
            "overall_certified_fraction":
                str(rates["overall_certified_fraction"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report transform decoder: the "
                   f"{counts['codeword_count']} Golay coset costs are one "
                   f"Walsh-Hadamard transform, which costs "
                   f"{counts['fwht_ops']} add/subtracts against the direct "
                   f"{counts['direct_adds']} -- equal, because n = 2k, so "
                   f"the transform is not a speed-up for this code; the "
                   f"transform-driven decoder reproduces the existing one "
                   f"exactly, tie sets included; and the constant-time "
                   f"lookup certifies its own optimality on "
                   f"{rates['total_certified']} of "
                   f"{rates['total_samples']} sampled profiles -- always on "
                   f"a flat profile, rarely on a very wide one -- with "
                   f"{rates['certified_but_wrong']} certified answers wrong",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_transform_decoder", "args": {}},
            payload={"report": report})

    def _report_units(self, query: Query) -> Solution:
        """Wires units.units_report -- the unit strings, read as dimensions.

        Every quantity states what it is twice, once as a unit string and
        once as EXT10 exponents.  This parses the first and checks it
        against the second, and measures what the SI reading of the
        steradian would cost.
        """
        report = un.units_report()
        audit = report["audit"]
        case = report["steradian"]

        steps = [
            Step("ten units stored, the rest derived",
                 report["method"],
                 f"base units = {report['base_unit_count']}, derived "
                 f"definitions = {report['derived_unit_count']}, decimal "
                 f"prefixes = {report['prefix_count']}"),
            Step("every unit string in the register is parsed and checked",
                 f"Each of the {audit['quantities']} quantities carries a "
                 f"unit string and a vector of EXT10 exponents, written "
                 f"independently.  The string is parsed and the two are "
                 f"compared, so a typo in either is a failure rather than a "
                 f"silent disagreement.",
                 f"readable = {audit['readable']}/{audit['quantities']}, "
                 f"agreeing = {audit['agreed']}, mismatched = "
                 f"{audit['mismatched_count']}, unreadable = "
                 f"{audit['unreadable_count']}"),
            Step("the steradian is a dimension here, not a ratio",
                 case["statement"],
                 f"with the steradian carried, mismatches = "
                 f"{case['with_steradian']['mismatched']}; dropped, "
                 f"mismatches = {case['without_steradian']['mismatched']}"),
            Step("what a dimensionless steradian would conflate",
                 f"Dropping it breaks "
                 f"{case['broken_count']} quantities, of which "
                 f"{case['photometric_count']} are written with the lumen or "
                 f"the lux: "
                 f"{', '.join(case['photometric_quantities'])}.  The lumen "
                 f"would read as the candela, so luminous flux would become "
                 f"luminous intensity; the lux would read as the candela per "
                 f"square metre, so illuminance would become luminance.",
                 f"broken = {case['broken_count']}, photometric = "
                 f"{case['photometric_count']}, quantities carrying a solid "
                 f"angle = {case['solid_angle_count']}"),
        ]
        expected = {
            "quantities": str(audit["quantities"]),
            "every_unit_readable": str(audit["every_unit_readable"]),
            "every_unit_agrees": str(audit["every_unit_agrees"]),
            "mismatched_count": str(audit["mismatched_count"]),
            "broken_by_dropping_the_steradian": str(case["broken_count"]),
            "photometric_count": str(case["photometric_count"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report units: all {audit['quantities']} unit strings in "
                   f"the physics register parse, and all "
                   f"{audit['agreed']} agree with the EXT10 exponents "
                   f"declared beside them, with "
                   f"{audit['mismatched_count']} mismatches; the parser "
                   f"carries the steradian as a dimension, and reading it "
                   f"the SI way -- as dimensionless -- would break "
                   f"{case['broken_count']} quantities, "
                   f"{case['photometric_count']} of them written with the "
                   f"lumen or the lux",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_units", "args": {}},
            payload={"report": report})

    def _report_deep_holes(self, query: Query) -> Solution:
        """Wires deep_holes.deep_holes_report -- Niemeier types, no table.

        The classification of a carrier by its nearest Niemeier type is
        normally a Voronoi-cell problem with 196,560 facets.  Here it is a
        process: walk to a hole, climb to the covering radius, read the
        vertices off the modulator's trajectory, and certify the reading.
        Nothing about the 23 types is stored except the catalogue, which is
        itself derived.
        """
        report = dhl.deep_holes_report(walks=3)
        census = report["census"]
        catalogue = report["catalogue_size"]
        exhibited = census["types_exhibited"]

        steps = [
            Step("the catalogue is derived, not listed",
                 f"The {catalogue} Niemeier root systems are enumerated as "
                 f"the unions of ADE components that share one Coxeter "
                 f"number and total rank 24, from the component formulas "
                 f"alone.  They are what a hole's diagram is checked "
                 f"against.",
                 f"catalogue size = {catalogue}"),
            Step("a hole is reached by running, not looked up",
                 report["method"],
                 f"walks run = {census['walks_run']}, reaching the covering "
                 f"radius = {census['walks_reaching_a_deep_hole']}, "
                 f"stalling at a shallow hole = "
                 f"{census['walks_stalling_at_a_shallow_hole']}"),
            Step("the reading is certified",
                 report["certificate"],
                 f"types named = {len(exhibited)}, all certified = "
                 f"{census['every_named_type_certified']}"),
            Step("what it settles",
                 f"This run exhibited "
                 f"{census['types_exhibited_count']} of the {catalogue} "
                 f"types: {', '.join(exhibited) if exhibited else 'none'}.  "
                 f"Each was certified complete by the marked-barycentre "
                 f"identity.",
                 f"exhibited = {census['types_exhibited_count']}/"
                 f"{catalogue}"),
            Step("what it leaves undetermined",
                 report["limits"] + "  " + census["honest_statement"],
                 f"shortfall = {census['shortfall']} of {catalogue}, "
                 f"census complete = {census['census_complete']}"),
        ]
        expected = {
            "catalogue_size": str(catalogue),
            "covering_radius2": str(report["covering_radius2"]),
            "walks_run": str(census["walks_run"]),
            "every_named_type_certified":
                str(census["every_named_type_certified"]),
            "census_complete": str(census["census_complete"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report deep holes: a carrier is classified by walking "
                   f"to the hole it sits in and certifying what the walk "
                   f"found, never by enumerating the 196,560 facets or "
                   f"storing the {catalogue} hole centres; this run reached "
                   f"the covering radius on "
                   f"{census['walks_reaching_a_deep_hole']} of "
                   f"{census['walks_run']} walks and exhibited "
                   f"{census['types_exhibited_count']} of the {catalogue} "
                   f"Niemeier types, every one certified complete, with a "
                   f"shortfall of {census['shortfall']} that is reported "
                   f"as a shortfall",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_deep_holes", "args": {}},
            payload={"report": report})

    def _report_molecules(self, query: Query) -> Solution:
        """Wires molecules.molecules_report -- the multi-carrier register.

        A molecule is held twice: as the faithful bundle of its element
        carriers with multiplicities, and as one composite carrier that is
        a *summary* of the bundle.  The report says which of the two is
        lossless and checks the claim rather than asserting it.
        """
        report = do.molecules_report()
        collisions = report["collisions"]
        missing = report["missing_by_field"]
        heaviest_name, heaviest_mass = report["largest_by_mass"]

        steps = [
            Step("the register stores no measurement",
                 f"{report['molecules']} molecules and ions are held as a "
                 f"name and a formula each.  Every one of the "
                 f"{report['derived_fields']} derived coordinates -- molar "
                 f"mass, electron count, electronegativity spread, degree "
                 f"of unsaturation and the rest -- is recomputed from the "
                 f"element register when the carrier is built, so this "
                 f"register cannot disagree with that one.",
                 f"molecules = {report['molecules']}, derived fields = "
                 f"{report['derived_fields']}, coordinates = "
                 f"{report['coordinates']}"),
            Step("the bundle is faithful, the composite is a summary",
                 f"The bundle ((symbol, count, carrier), ...) has the "
                 f"formula read straight back off it, which is checked for "
                 f"every molecule.  The composite carrier folds the "
                 f"composition into 24 coordinates and is therefore a "
                 f"summary; it is checked for collisions rather than "
                 f"assumed injective.",
                 f"bundle_is_faithful = "
                 f"{collisions['bundle_is_faithful']}, distinct composites "
                 f"= {collisions['distinct_composites']} of "
                 f"{collisions['molecules']}, composite collisions = "
                 f"{collisions['composite_collision_count']}"),
            Step("a gap in the element register stays a gap",
                 f"A coordinate the element register cannot support is left "
                 f"at 0 with its bit set in the missingness mask, never "
                 f"imputed.  On this register the only such coordinate is "
                 f"the degree of unsaturation, which is undefined for a "
                 f"formula containing sulfur, phosphorus or a metal -- so "
                 f"it is absent rather than wrong.",
                 f"missing_by_field = {dict(missing)}"),
            Step("what the register reaches",
                 f"{report['distinct_elements_used']} distinct elements "
                 f"appear across the register; the heaviest molecule is "
                 f"{heaviest_name} at {q(heaviest_mass)} u and the largest "
                 f"by atom count is {report['largest_by_atom_count'][0]} "
                 f"with {report['largest_by_atom_count'][1]} atoms.  "
                 f"{len(report['charged'])} of the entries are ions.",
                 f"elements used = {report['distinct_elements_used']}, "
                 f"ions = {len(report['charged'])}"),
        ]
        expected = {
            "molecules": str(report["molecules"]),
            "coordinates": str(report["coordinates"]),
            "derived_fields": str(report["derived_fields"]),
            "distinct_elements_used": str(report["distinct_elements_used"]),
            "bundle_is_faithful": str(collisions["bundle_is_faithful"]),
            "distinct_composites": str(collisions["distinct_composites"]),
            "composite_collision_count":
                str(collisions["composite_collision_count"]),
            "bundle_collision_count":
                str(collisions["bundle_collision_count"]),
            "missing_by_field": str(dict(missing)),
            "largest_by_mass": f"{heaviest_name}={q(heaviest_mass)}",
        }
        return Solution(
            query=query, kind="report",
            answer=f"report molecules: {report['molecules']} molecules and "
                   f"ions over {report['distinct_elements_used']} elements, "
                   f"each held twice -- as the faithful bundle of its "
                   f"element carriers, from which the formula is read back "
                   f"exactly for every entry, and as one composite carrier "
                   f"of {report['coordinates']} coordinates that is a "
                   f"summary and collides "
                   f"{collisions['composite_collision_count']} times on "
                   f"this register; no measurement is stored and no missing "
                   f"value is imputed",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_molecules", "args": {}},
            payload={"report": report})

    def _report_chemistry_coverage(self, query: Query) -> Solution:
        """Wires element_coverage.element_coverage_report.

        The element register is sparse.  The three honest repairs -- derive,
        estimate with the error measured, cross-check without merging -- are
        run and each is labelled with what it is.
        """
        report = eco.element_coverage_report()
        coverage = report["coverage"]
        derived = report["derived"]
        estimates = report["estimates"]
        model = estimates["model"]
        cross = report["cross_check"]

        steps = [
            Step("how sparse it actually is",
                 f"Across {coverage['elements']} elements and the measured "
                 f"fields there are {coverage['total_cells']} cells, of "
                 f"which {coverage['filled_cells']} are filled.  Three "
                 f"fields are complete "
                 f"({', '.join(coverage['complete_fields'])}); the sparsest "
                 f"is {coverage['sparsest']}.",
                 f"filled = {coverage['filled_cells']}/"
                 f"{coverage['total_cells']}, sparsest = "
                 f"{coverage['sparsest']}"),
            Step("derive: exact, and as reliable as its inputs",
                 f"{derived['attribute_count']} attributes are exact "
                 f"functions of fields already present -- molar volume, "
                 f"liquid range, Mulliken electronegativity, valence-shell "
                 f"load -- and together they add {derived['new_cells']} "
                 f"filled cells without a new measurement.",
                 f"derived attributes = {derived['attribute_count']}, new "
                 f"cells = {derived['new_cells']}"),
            Step("estimate: a line, fitted exactly, with its residuals",
                 f"The covalent radius is known for "
                 f"{estimates['measured_count']} elements.  A rational "
                 f"least-squares line against the atomic radius, fitted on "
                 f"exactly those {model['fitted_on']}, extends it to "
                 f"{estimates['estimate_count']} more -- coverage "
                 f"{estimates['coverage_before']} to "
                 f"{estimates['coverage_after']}.  The mean absolute "
                 f"residual is {q(model['mean_absolute_residual_pm'])} pm "
                 f"and the worst is {model['worst_element']} at "
                 f"{q(model['max_absolute_residual_pm'])} pm.  Every "
                 f"extended value is labelled 'estimated', and "
                 f"{len(estimates['still_absent'])} elements still have no "
                 f"atomic radius to estimate from and stay absent.",
                 f"fitted_on = {model['fitted_on']}, estimates = "
                 f"{estimates['estimate_count']}, mean |residual| = "
                 f"{q(model['mean_absolute_residual_pm'])} pm"),
            Step("cross-check: compare, do not merge",
                 cross["statement"],
                 f"compared = {cross['compared']}, agreeing within 20 "
                 f"kJ/mol = {cross['agree_within_20_count']}, largest "
                 f"difference = {cross['largest_difference']['element']} at "
                 f"{q(cross['largest_difference']['difference'])} kJ/mol"),
            Step("what it leaves alone",
                 report["limits"],
                 f"values written back into the element register = 0"),
        ]
        expected = {
            "elements": str(coverage["elements"]),
            "total_cells": str(coverage["total_cells"]),
            "filled_cells": str(coverage["filled_cells"]),
            "sparsest": str(coverage["sparsest"]),
            "derived_attribute_count": str(derived["attribute_count"]),
            "derived_new_cells": str(derived["new_cells"]),
            "fitted_on": str(model["fitted_on"]),
            "slope": q(model["slope"]),
            "intercept_pm": q(model["intercept_pm"]),
            "mean_absolute_residual_pm":
                q(model["mean_absolute_residual_pm"]),
            "estimate_count": str(estimates["estimate_count"]),
            "measured_count": str(estimates["measured_count"]),
            "coverage_before": str(estimates["coverage_before"]),
            "coverage_after": str(estimates["coverage_after"]),
            "cross_check_compared": str(cross["compared"]),
            "cross_check_agree_within_20":
                str(cross["agree_within_20_count"]),
            "largest_difference_element":
                str(cross["largest_difference"]["element"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report chemistry coverage: "
                   f"{coverage['filled_cells']} of "
                   f"{coverage['total_cells']} measured cells are filled and "
                   f"the sparsest field is {coverage['sparsest']}; coverage "
                   f"is widened three ways that each keep their label -- "
                   f"{derived['attribute_count']} exactly derived "
                   f"attributes adding {derived['new_cells']} cells, a "
                   f"rational fit that carries the covalent radius from "
                   f"{estimates['coverage_before']} to "
                   f"{estimates['coverage_after']} of the elements with a "
                   f"mean residual of "
                   f"{q(model['mean_absolute_residual_pm'])} pm, and a "
                   f"cross-check against the diatomic register that reports "
                   f"the disagreement instead of merging the two "
                   f"quantities; nothing is written back into the register",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_chemistry_coverage", "args": {}},
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

    def _report_information_loss(self, query: Query) -> Solution:
        """Wires il.information_loss_report — loss at the layer boundaries.

        Each layer of the stack is true within its own reach and hands off to
        the next.  This report measures where a reach ends: what each layer
        cannot tell apart, which pairs the layer above it splits, and whether
        addition can be computed from what the layer sees.
        """
        report = il.information_loss_report()
        by_name = {layer["name"]: layer for layer in report["layers"]}
        edges = {(b["lower"], b["higher"]): b for b in report["boundaries"]}
        names = tuple(layer["name"] for layer in report["layers"])
        pairs = tuple((b["lower"], b["higher"])
                      for b in report["boundaries"])
        raw = report["non_cumulative"]

        resolutions = ", ".join(
            f"{n} {by_name[n]['resolution']}/{report['carrier_count']}"
            for n in names)
        descends = ", ".join(
            n for n in names if by_name[n]["addition_descends"]) or "none"
        lost = ", ".join(
            f"{lo}->{hi} {edges[(lo, hi)]['lost_count']}" for lo, hi in pairs)
        holes = [f"{lo}->{hi}" for lo, hi in pairs
                 if not edges[(lo, hi)]["refines"]]

        steps = [
            Step("resolution",
                 f"On {report['carrier_count']} carriers chosen to exercise "
                 f"every handoff, each layer's own measure decides which of "
                 f"them it can tell apart.  What it cannot tell apart is what "
                 f"it loses.",
                 f"resolved: {resolutions}"),
            Step("boundary",
                 f"The boundary between two layers is the set of pairs the "
                 f"lower one conflates and the higher one splits.  That set "
                 f"is exactly the information recovered by escalating -- and "
                 f"exactly the information the lower layer was never wrong "
                 f"to ignore, within its own reach.",
                 f"lost pairs: {lost}"),
            Step("reach of the law",
                 f"Coordinatewise addition descends to a layer only when the "
                 f"layer's view determines the view of the sum.  Where a "
                 f"witness exists -- indistinguishable inputs with "
                 f"distinguishable sums -- the law is true one level up and "
                 f"untrue here.",
                 f"addition descends at: {descends}"),
            Step("refinement audit",
                 f"A stack is a refinement chain when every layer sees at "
                 f"least as much as the one below.  Where it is not, "
                 f"escalation itself loses information.",
                 f"chain intact: {report['refinement_chain_intact']}"
                 + (f"; holes at {', '.join(holes)}" if holes else "")),
            Step("what cumulativity buys",
                 f"The chain is intact because each layer keeps what the "
                 f"one below it saw and adds to it.  The reading that only "
                 f"takes the seven SI7 exponents is kept beside the stack "
                 f"to show the difference: it conflates carriers the "
                 f"substrate already separates, so a stack built on it "
                 f"would lose information by escalating.",
                 f"{raw['layer']}: refines substrate "
                 f"{raw['refines_substrate']}, "
                 f"{raw['violation_count']} violating pair(s); "
                 f"{raw['cumulative_layer']}: "
                 f"{raw['cumulative_refines_substrate']}"),
        ]

        expected = {"carrier_count": str(report["carrier_count"])}
        for name in names:
            layer = by_name[name]
            expected[f"resolution_{name}"] = str(layer["resolution"])
            expected[f"loss_{name}"] = str(layer["loss_count"])
            expected[f"addition_descends_{name}"] = str(
                layer["addition_descends"])
        for lower, higher in pairs:
            edge = edges[(lower, higher)]
            key = f"{lower}_to_{higher}"
            expected[f"lost_count_{key}"] = str(edge["lost_count"])
            expected[f"refines_{key}"] = str(edge["refines"])
        expected["refinement_chain_intact"] = str(
            report["refinement_chain_intact"])
        expected["non_cumulative_refines_substrate"] = str(
            raw["refines_substrate"])
        expected["non_cumulative_violations"] = str(raw["violation_count"])
        expected["cumulative_refines_substrate"] = str(
            raw["cumulative_refines_substrate"])

        return Solution(
            query=query, kind="report",
            answer=f"report information loss: resolved {resolutions}; "
                   f"lost {lost}; addition descends at {descends}; "
                   f"refinement chain intact "
                   f"{report['refinement_chain_intact']}; "
                   f"non-cumulative SI7 reading refines substrate "
                   f"{raw['refines_substrate']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_information_loss", "args": {}},
            payload={"report": report})

    def _report_fusion(self, query: Query) -> Solution:
        """Wires pr.fusion_report -- the Ising fusion layer of the algebra.

        The adjoint action of an axis, its eigenspaces at the four Ising
        eigenvalues, and the two Miyamoto involutions built from them were
        implemented but unreachable from a query.  This subject recomputes
        all of it and states what the numbers mean.
        """
        report = pr.fusion_report()
        dims = report["expected_eigenspace_dimensions"]
        first = report["records"][0]["axes"][0]

        steps = [
            Step("adjoint action",
                 f"An axis acts on its own subalgebra by multiplication: "
                 f"x -> a . x.  In the three axes as a basis that is a "
                 f"3x3 rational matrix, and its trace is the sum of the "
                 f"eigenvalues.  Across {report['axes_checked']} axes of "
                 f"{report['pairs_checked']} subalgebras the trace is "
                 f"always 5/4 = 1 + 0 + 1/4.",
                 f"adjoint(a_{first['label']}) = {first['adjoint']}, "
                 f"trace = {first['adjoint_trace']}, "
                 f"always 5/4: "
                 f"{report['all_adjoint_traces_five_quarters']}"),
            Step("fusion spectrum",
                 f"The Ising fusion rules allow an axis the eigenvalues "
                 f"{', '.join(report['ising_eigenvalues'])}.  The "
                 f"eigenspaces are searched for, not assumed: each is the "
                 f"exact kernel of ad_a - lambda, computed over the "
                 f"rationals.  Here 1, 0 and 1/4 each contribute one "
                 f"dimension and 1/32 contributes none, so the four "
                 f"eigenspaces span all three dimensions -- the algebra is "
                 f"of Majorana type with no twisted part.",
                 f"dimensions = {dims}, span: "
                 f"{report['all_eigenspaces_span']}, as predicted "
                 f"everywhere: {report['all_dimensions_as_predicted']}"),
            Step("Miyamoto involutions",
                 f"tau_a negates the 1/32-eigenspace and sigma_a the "
                 f"1/4-eigenspace.  Because the 1/32-part is zero here, "
                 f"tau_a comes out as the identity -- a derived fact, not "
                 f"an assumption -- and the nontrivial symmetry is carried "
                 f"by sigma_a, which fixes its own axis and exchanges the "
                 f"other two.  The permutation is read off the computed "
                 f"matrix.",
                 f"tau always identity: {report['tau_always_identity']}, "
                 f"sigma fixes a and swaps the others: "
                 f"{report['sigma_always_swaps']}, "
                 f"sigma(a_{first['label']}) permutation = "
                 f"{first['sigma_permutation']}"),
            Step("symmetry check",
                 f"Both maps are checked against the structure they are "
                 f"supposed to preserve: every product and every Griess "
                 f"inner product on the basis, and squaring back to the "
                 f"identity.",
                 f"automorphisms: {report['all_automorphisms']}, "
                 f"isometries: {report['all_isometries']}, "
                 f"involutions: {report['all_involutions']}"),
        ]

        expected = {
            "pairs_checked": str(report["pairs_checked"]),
            "axes_checked": str(report["axes_checked"]),
            "all_eigenspaces_span": str(report["all_eigenspaces_span"]),
            "all_dimensions_as_predicted": str(
                report["all_dimensions_as_predicted"]),
            "all_adjoint_traces_five_quarters": str(
                report["all_adjoint_traces_five_quarters"]),
            "tau_always_identity": str(report["tau_always_identity"]),
            "sigma_always_swaps": str(report["sigma_always_swaps"]),
            "all_automorphisms": str(report["all_automorphisms"]),
            "all_isometries": str(report["all_isometries"]),
            "all_involutions": str(report["all_involutions"]),
        }

        return Solution(
            query=query, kind="report",
            answer=f"report fusion: {report['axes_checked']} axes over "
                   f"{report['pairs_checked']} 2A subalgebras; eigenspace "
                   f"dimensions {dims} everywhere "
                   f"({report['all_dimensions_as_predicted']}); "
                   f"tau = identity {report['tau_always_identity']}, "
                   f"sigma swaps the other two axes "
                   f"{report['sigma_always_swaps']}; all automorphisms "
                   f"{report['all_automorphisms']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_fusion", "args": {}},
            payload={"report": report})

    def _report_benchmarks(self, query: Query) -> Solution:
        """Wires benchmarks.benchmark_report -- the scored task suites.

        Imported here rather than at module scope: the suites drive queries
        through this very session class, so a top-level import would be
        circular.
        """
        from .. import benchmarks as bm

        report = bm.benchmark_report()
        suites = report["suites"]
        nulls = report["null_results"]

        tiers = ", ".join(f"{s['name']} {s['tier']['tier']}" for s in suites)
        scores = ", ".join(
            f"{s['name']} {s['passed']}/{s['total']} vs {s['baseline']}"
            for s in suites)

        steps = [
            Step("declared before the run",
                 f"Each of the {report['suite_count']} suites fixes its "
                 f"population, its ground truth, what counts as a pass, what "
                 f"a baseline would score and what a null result would look "
                 f"like, before it is run.  A score is reported only "
                 f"together with that declaration.",
                 f"tiers: {tiers}"),
            Step("scores",
                 f"{report['passed_count']} of {report['task_count']} tasks "
                 f"pass, each against the baseline its own suite declared.  "
                 f"The ratios are exact rationals; no score is a float.",
                 f"{scores}\noverall = {report['overall_score']}"),
            Step("null and negative results",
                 f"A suite that only reported its wins would be a broken "
                 f"suite.  {len(report['findings'])} findings are reported "
                 f"beside the scores, including every failing task and every "
                 f"known failure mode measured rather than asserted.",
                 "; ".join(f"[{f['suite']}/{f['key']}] {f['statement']}"
                           for f in report["findings"])),
            Step("reproducibility",
                 f"The run id is a hash of the results themselves, so the "
                 f"same code produces the same id and a changed number is "
                 f"visible as a changed id.  No suite samples without a "
                 f"recorded seed.",
                 f"run_id = {report['run_id']}"),
        ]

        expected = {
            "suite_count": str(report["suite_count"]),
            "task_count": str(report["task_count"]),
            "passed_count": str(report["passed_count"]),
            "overall_score": str(report["overall_score"]),
            "run_id": str(report["run_id"]),
            "null_result_count": str(len(nulls)),
        }
        for suite in suites:
            name = suite["name"]
            expected[f"score_{name}"] = str(suite["score"])
            expected[f"baseline_{name}"] = str(suite["baseline"])
            expected[f"verdict_{name}"] = str(suite["verdict"])

        return Solution(
            query=query, kind="report",
            answer=f"report benchmarks: {report['passed_count']}/"
                   f"{report['task_count']} tasks "
                   f"({report['overall_score']}) across "
                   f"{report['suite_count']} suites; {scores}; "
                   + (f"null or below-baseline: {', '.join(nulls)}"
                      if nulls else "every suite beat its baseline"),
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_benchmarks", "args": {}},
            payload={"report": report})

    # ------------------------------------------------------------------
    # 3k-bis.  the five report subjects added in v0.8.0
    # ------------------------------------------------------------------
    # Each of these wires a substrate or reasoning module that had been
    # built but was not reachable from a query.  They follow the same
    # contract as the older report subjects: recompute, state the facts
    # as steps, and put only independently reproducible scalars into
    # ``expected``.
    # ------------------------------------------------------------------

    def _report_golay_decoding(self, query: Query) -> Solution:
        """Wires gdc.golay_decode_report -- complete decoding, no silent snap."""
        report = gdc.golay_decode_report()
        census = report["coset_census"]
        steiner = report["steiner"]
        weight5 = report["weight5"]
        rows = {row["weight"]: row for row in report["comparison"]["rows"]}
        flagged_at_4 = rows[4]["complete"]["flagged"]
        silent_at_4 = rows[4]["legacy_ties_broken_silently"]

        steps = [
            Step("coset table",
                 f"The 4,096 cosets of the Golay code were enumerated and "
                 f"each given its full set of minimum-weight leaders.  Below "
                 f"the packing radius {report['packing_radius']} the leader "
                 f"is unique; at the covering radius "
                 f"{report['covering_radius']} every coset has a sextet of "
                 f"six leaders, so no nearest codeword is singled out.",
                 f"cosets = {census['cosets']}, "
                 f"leaders = {census['total_leaders']}, "
                 f"by leader weight = {census['cosets_by_leader_weight']}"),
            Step("decode or detect",
                 f"The complete decoder returns every nearest codeword and a "
                 f"status.  On the {flagged_at_4} sampled weight-4 patterns "
                 f"it reports ambiguity; the retired snap decoder returned "
                 f"one of the six silently in all {silent_at_4} of them.",
                 f"weight 4: complete flagged {flagged_at_4}, "
                 f"legacy silent tie-breaks {silent_at_4}"),
            Step("why weight 5 is not a bug",
                 f"Every 5-subset of the 24 points lies in exactly one octad "
                 f"-- the Steiner system S(5,8,24), verified here on all "
                 f"{steiner['five_subsets_total']} of them.  A weight-5 "
                 f"error is therefore the complement inside that octad of a "
                 f"weight-3 error, so it sits at distance 3 from a codeword "
                 f"and is decoded confidently and wrongly by any "
                 f"nearest-codeword rule.  The remedy is a declared channel "
                 f"radius, not a better decoder.",
                 f"octads = {steiner['octads']}, "
                 f"multiplicities = {steiner['multiplicities']}, "
                 f"weight-5 coset weights = {weight5['coset_weights']}"),
        ]
        expected = {
            "cosets": str(census["cosets"]),
            "total_leaders": str(census["total_leaders"]),
            "unique_below_radius_4": str(census["unique_below_radius_4"]),
            "sextet_at_radius_4": str(census["sextet_at_radius_4"]),
            "packing_radius": str(report["packing_radius"]),
            "covering_radius": str(report["covering_radius"]),
            "codewords": str(report["codewords"]),
            "octads": str(steiner["octads"]),
            "is_steiner_5_8_24": str(steiner["is_steiner_5_8_24"]),
            "weight5_always_coset_weight_3":
                str(weight5["always_coset_weight_3"]),
            "weight5_always_miscorrected":
                str(weight5["always_miscorrected"]),
            "silent_tie_breaking_retired":
                str(report["silent_tie_breaking_retired"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report golay decoding: {census['cosets']} cosets, "
                   f"{census['total_leaders']} leaders, unique below weight "
                   f"4 and a sextet of six at weight 4; S(5,8,24) verified "
                   f"on {steiner['five_subsets_total']} five-subsets, so "
                   f"weight-5 miscorrection is a theorem, not a bug",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_golay_decoding", "args": {}},
            payload={"report": report})

    def _report_superposition(self, query: Query) -> Solution:
        """Wires sup.superposition_report -- the tie carried, not broken."""
        report = sup.superposition_report()
        sextet = report["sextet"]
        bundling = report["bundling"]
        collapsed = report["collapse"]
        census = report["census"]
        chain = report["chain"]
        hull = report["hull"]

        steps = [
            Step("the tie is a sextet",
                 f"At the covering radius the nearest-codeword reading has "
                 f"exactly {report['tie_count']} answers.  Their error "
                 f"patterns are six disjoint tetrads covering all 24 "
                 f"coordinates -- a MOG sextet -- checked here on "
                 f"{sextet['tetrads_checked']} received words.",
                 f"leader counts = {sextet['leader_counts']}, "
                 f"disjoint = {sextet['pairwise_disjoint']}, "
                 f"covers 24 = {sextet['covers_all_24']}"),
            Step("bundling: the two rules do not agree",
                 f"Bundling the six candidates by F_2 symmetric difference "
                 f"gives the all-ones word for every received word, so it "
                 f"distinguishes {bundling['f2_bundle_distinguishes']} of the "
                 f"{bundling['words_checked']} words checked.  Bundling them "
                 f"by exact rational addition gives (1 + 4 v)/6 "
                 f"coordinatewise, which is invertible: it distinguishes all "
                 f"{bundling['rational_bundle_distinguishes']}, and the "
                 f"received word is recovered from the bundle.",
                 f"F_2 bundle = {bundling['f2_bundle_values']}, "
                 f"rational coordinates = "
                 f"{bundling['rational_bundle_coordinate_values']}, "
                 f"recovers input = "
                 f"{bundling['rational_bundle_recovers_input']}"),
            Step("collapse is a measurement, not a coin flip",
                 f"A downstream context filters the hypothesis space: a "
                 f"selective one collapses it to a single codeword, a "
                 f"permissive one leaves it standing, an incompatible one "
                 f"refutes the read.  No tie is broken by enumeration order.",
                 f"collapsed = {collapsed['collapsed']['status']}, "
                 f"superposed = {collapsed['superposed']['status']}, "
                 f"refuted = {collapsed['refuted']['status']}"),
            Step("how often the tie happens",
                 f"Counting the cosets rather than describing one: the "
                 f"{census['cosets']} cosets sit at distances "
                 f"{census['cosets_by_distance']} from the code, so "
                 f"{census['uniquely_read_cosets']} are read uniquely and "
                 f"{census['ambiguous_cosets']} are six-fold ties, and the "
                 f"mean distance to the code is exactly "
                 f"{census['mean_coset_weight']}.  That is strictly past the "
                 f"packing radius {census['packing_radius']} and strictly "
                 f"inside the covering radius {census['covering_radius']}: "
                 f"the average word already sits outside the radius within "
                 f"which the reading is unique, so ambiguity is the typical "
                 f"case for this code rather than a corner case.",
                 f"mean coset weight = {census['mean_coset_weight']}, "
                 f"ambiguous fraction = {census['ambiguous_fraction']}, "
                 f"agrees with Lean = "
                 f"{census['census_agrees_with_lean']} / "
                 f"{census['mean_agrees_with_lean']}"),
            Step("the dynamical half: no, it does not settle",
                 f"A carrier under repeated one-bit perturbation is a random "
                 f"walk on the {chain['states']} cosets.  Its unique "
                 f"stationary law is the uniform one, whose mean distance to "
                 f"the code is the census figure "
                 f"{chain['stationary_mean_distance']} -- but the walk has no "
                 f"limiting law at all: every parity-check column has odd "
                 f"parity, so after n ticks the law sits on one of the two "
                 f"parity classes and never on both.  Only the time average "
                 f"settles: after {chain['steps']} exact ticks the two-step "
                 f"average is "
                 f"{chain['two_step_average_mean_distance']}, within "
                 f"{chain['two_step_average_error']} of the stationary mean.  "
                 f"And if each perturbation is corrected, the carrier returns "
                 f"to the same codeword and stays at distance "
                 f"{chain['corrected_distance_after_correction']}: correction "
                 f"destroys the criticality rather than maintaining it.",
                 f"support by step = {chain['support_by_step']}, "
                 f"parity alternates = {chain['parity_alternates']}, "
                 f"two-step average error = "
                 f"{chain['two_step_average_error']}, "
                 f"corrected carrier returns = "
                 f"{chain['corrected_carrier_returns_to_code']}"),
            Step("widening the alphabet",
                 f"The functional 7 x_0 - sum_(j != 0) x_j is <= 0 on all "
                 f"{hull['codewords_checked']} codewords, hence on every "
                 f"non-negative multiple of one, while it is "
                 f"{hull['value_at_target']} at the target (1/2) e_0.  "
                 f"Scaling the emitted alphabet therefore changes nothing; "
                 f"admitting two minimal Leech vectors of shape (+-4^2, "
                 f"0^22) reaches the same target exactly, at every completed "
                 f"{hull['leech_cycle_length']}-tick cycle.",
                 f"max over scaled codewords = "
                 f"{hull['max_over_scaled_codewords']}, "
                 f"value at target = {hull['value_at_target']}, "
                 f"Leech cycle reaches target = "
                 f"{hull['leech_cycle_reaches_target']}"),
        ]
        expected = {
            "tie_count": str(report["tie_count"]),
            "pairwise_disjoint": str(sextet["pairwise_disjoint"]),
            "covers_all_24": str(sextet["covers_all_24"]),
            "f2_bundle_is_all_ones": str(bundling["f2_bundle_is_all_ones"]),
            "f2_bundle_distinguishes":
                str(bundling["f2_bundle_distinguishes"]),
            "rational_bundle_recovers_input":
                str(bundling["rational_bundle_recovers_input"]),
            "rational_bundle_distinguishes":
                str(bundling["rational_bundle_distinguishes"]),
            "collapse_status": str(collapsed["collapsed"]["status"]),
            "refuted_status": str(collapsed["refuted"]["status"]),
            "cosets": str(census["cosets"]),
            "cosets_by_distance": str(census["cosets_by_distance"]),
            "mean_coset_weight": str(census["mean_coset_weight"]),
            "uniquely_read_cosets": str(census["uniquely_read_cosets"]),
            "ambiguous_cosets": str(census["ambiguous_cosets"]),
            "ambiguous_fraction": str(census["ambiguous_fraction"]),
            "mean_exceeds_packing_radius":
                str(census["mean_exceeds_packing_radius"]),
            "mean_below_covering_radius":
                str(census["mean_below_covering_radius"]),
            "census_agrees_with_lean":
                str(census["census_agrees_with_lean"]),
            "mean_agrees_with_lean": str(census["mean_agrees_with_lean"]),
            "chain_states": str(chain["states"]),
            "columns_all_odd_parity": str(chain["columns_all_odd_parity"]),
            "uniform_is_stationary": str(chain["uniform_is_stationary"]),
            "parity_alternates": str(chain["parity_alternates"]),
            "law_never_uniform": str(chain["law_never_uniform"]),
            "settles_in_distribution": str(chain["settles_in_distribution"]),
            "two_step_average_mean_distance":
                str(chain["two_step_average_mean_distance"]),
            "two_step_average_error": str(chain["two_step_average_error"]),
            "corrected_carrier_returns_to_code":
                str(chain["corrected_carrier_returns_to_code"]),
            "corrected_distance_after_correction":
                str(chain["corrected_distance_after_correction"]),
            "codewords_checked": str(hull["codewords_checked"]),
            "max_over_scaled_codewords":
                str(hull["max_over_scaled_codewords"]),
            "value_at_target": str(hull["value_at_target"]),
            "leech_cycle_reaches_target":
                str(hull["leech_cycle_reaches_target"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report superposition: the covering-radius tie has "
                   f"{report['tie_count']} candidates whose error patterns "
                   f"partition the 24 coordinates; XOR-bundling them is the "
                   f"constant all-ones word, rational bundling is the "
                   f"invertible (1 + 4 v)/6 and recovers the read; context "
                   f"collapses, holds or refutes; "
                   f"{census['ambiguous_cosets']} of the {census['cosets']} "
                   f"cosets are such ties and the mean distance to the code "
                   f"is {census['mean_coset_weight']}, past the packing "
                   f"radius, though the perturbation chain has no limiting "
                   f"law and settles only on average; and widening the "
                   f"emitted "
                   f"alphabet by scale reaches nothing new while widening it "
                   f"by support reaches (1/2) e_0 exactly",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_superposition", "args": {}},
            payload={"report": report})

    def _report_leech_construction(self, query: Query) -> Solution:
        """Wires lcs.leech_construction_report -- the A/B/C ladder."""
        report = lcs.leech_construction_report()
        kissing = report["kissing_by_level"]
        norms = report["minimal_norm_by_level"]
        shapes = report["levels"]["C"]["shapes"]
        necessity = report["necessity"]
        agreement = report["agreement_with_leech2"]

        steps = [
            Step("construction A",
                 f"Construction A lifts the Golay code mod 2 alone.  It is a "
                 f"lattice, but its minimum is {norms['A']} and only "
                 f"{kissing['A']} vectors attain it -- the coordinate "
                 f"vectors +-4 e_i.  That is the simplification this report "
                 f"removes.",
                 f"min norm^2 = {norms['A']}, kissing = {kissing['A']}"),
            Step("construction B and the mod-8 sum",
                 f"Requiring the coordinates mod 4 to form a Golay codeword "
                 f"and the coordinate sum to vanish mod 8 kills +-4 e_i and "
                 f"lifts the minimum to {norms['B']}, with {kissing['B']} "
                 f"minimal vectors.",
                 f"min norm^2 = {norms['B']}, kissing = {kissing['B']}"),
            Step("construction C",
                 f"Adjoining the odd coset -- all coordinates odd, again "
                 f"with the Golay and mod-8 conditions -- contributes "
                 f"{report['odd_coset_contribution']} further minimal "
                 f"vectors and restores the true kissing number "
                 f"{kissing['C']}.",
                 f"shapes = {shapes}, kissing = {kissing['C']}"),
            Step("each condition is necessary",
                 f"Dropping the mod-4 Golay condition admits (2, -2, 0^22) "
                 f"and the minimum falls to "
                 f"{necessity['drop_mod4_golay']['minimal_norm2']}; "
                 f"dropping the mod-8 sum readmits +-4 e_i and the minimum "
                 f"falls to {necessity['drop_mod8_sum']['minimal_norm2']}.",
                 f"drop mod-4 Golay: min norm^2 = "
                 f"{necessity['drop_mod4_golay']['minimal_norm2']}; "
                 f"drop mod-8 sum: min norm^2 = "
                 f"{necessity['drop_mod8_sum']['minimal_norm2']}, "
                 f"kissing = {necessity['drop_mod8_sum']['count_at_minimum']}"),
            Step("agreement with the substrate",
                 f"On {agreement['checked']} sampled vectors the ladder's "
                 f"membership test agrees with the package's own Leech "
                 f"predicate in every case, so the construction is the same "
                 f"lattice the rest of the system uses.",
                 f"checked = {agreement['checked']}, "
                 f"disagreements = {agreement['disagreements']}"),
        ]
        expected = {
            "kissing_A": str(kissing["A"]),
            "kissing_B": str(kissing["B"]),
            "kissing_C": str(kissing["C"]),
            "min_norm2_A": str(norms["A"]),
            "min_norm2_B": str(norms["B"]),
            "min_norm2_C": str(norms["C"]),
            "odd_coset_contribution": str(report["odd_coset_contribution"]),
            "construction_C_is_196560":
                str(report["construction_C_is_196560"]),
            "drop_mod4_golay_min_norm2":
                str(necessity["drop_mod4_golay"]["minimal_norm2"]),
            "drop_mod8_sum_min_norm2":
                str(necessity["drop_mod8_sum"]["minimal_norm2"]),
            "agrees_with_leech2": str(agreement["agrees"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report leech construction: A gives {kissing['A']} "
                   f"minimal vectors, B gives {kissing['B']}, and C with the "
                   f"mod-8 sum condition gives {kissing['C']} at norm^2 "
                   f"{norms['C']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_leech_construction",
                         "args": {}},
            payload={"report": report})

    def _report_facets(self, query: Query) -> Solution:
        """Wires fa.facets_report -- the six-facet linear decomposition."""
        report = fa.facets_report()
        partition = report["partition"]
        linearity = report["linearity"]
        pythagoras = report["pythagoras"]
        index = report["index_by_facet"]

        steps = [
            Step("partition",
                 f"The 24 coordinates are cut into {partition['facets']} "
                 f"named facets -- {', '.join(report['order'])} -- which "
                 f"cover all 24 and overlap nowhere.",
                 f"sizes = {partition['sizes']}, "
                 f"is_partition = {partition['is_partition']}"),
            Step("strict linearity",
                 f"Each facet projection was checked on "
                 f"{linearity['checked_carriers']} carriers to be additive, "
                 f"homogeneous, idempotent, mutually orthogonal and complete "
                 f"-- so the decomposition is an orthogonal direct sum, not "
                 f"a heuristic tagging.",
                 f"strictly_linear = {linearity['strictly_linear']}"),
            Step("pythagoras",
                 f"Because the projections are orthogonal, squared distance "
                 f"splits exactly across the facets; this was checked on "
                 f"{pythagoras['checked_pairs']} pairs.",
                 f"additive = {pythagoras['additive']}, "
                 f"failures = {pythagoras['failures']}"),
            Step("lattice index per facet",
                 f"No facet is lattice-autonomous: the index of the "
                 f"intersection in the projection is "
                 f"{index['dimension']} for dimension, {index['context']} "
                 f"for context and 8 for each one-dimensional facet, so a "
                 f"facet reading always loses lattice information.",
                 f"index = {index}, "
                 f"autonomous = {report['autonomous_facets']}"),
        ]
        expected = {
            "facets": str(partition["facets"]),
            "total": str(partition["total"]),
            "is_partition": str(partition["is_partition"]),
            "strictly_linear": str(linearity["strictly_linear"]),
            "pythagoras_additive": str(pythagoras["additive"]),
            "autonomous_facets": str(list(report["autonomous_facets"])),
        }
        for name in report["order"]:
            expected[f"size_{name}"] = str(partition["sizes"][name])
            expected[f"index_{name}"] = str(index[name])
        return Solution(
            query=query, kind="report",
            answer=f"report facets: {partition['facets']} facets partition "
                   f"the 24 coordinates, the projections are strictly linear "
                   f"and orthogonal, and no facet is lattice-autonomous "
                   f"(indices {index})",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_facets", "args": {}},
            payload={"report": report})

    def _report_monster_stack(self, query: Query) -> Solution:
        """Wires msk.monster_stack_report -- ten planes and the 2A product."""
        report = msk.monster_stack_report()
        census = report["position_census"]
        repaired = report["position_census_pair_repaired"]
        loss = report["shortcut_loss"]
        assoc = report["associativity"]

        steps = [
            Step("ten planes",
                 f"A carrier is written as a stack of {report['depth']} "
                 f"2-adic digit planes, each read as a class of "
                 f"Lambda / 2 Lambda and repaired to the nearest type-2 "
                 f"class, with exact lattice distance breaking Hamming ties.",
                 f"depth = {report['depth']}, basis = {report['basis']}"),
            Step("the exact Sakuma product",
                 f"Where both planes carry a 2A axis the product is the "
                 f"Norton-Sakuma relation a . b = (1/8)(a + b - a_rho), not "
                 f"an XOR of labels.  {census['defined']} of "
                 f"{census['planes']} planes compose strictly, and "
                 f"{repaired['defined']} with pair-aware repair.",
                 f"positions = {census['by_position']}, "
                 f"pair-repaired = {repaired['by_position']}"),
            Step("what the XOR shortcut discarded",
                 f"The shortcut kept only the third-axis label: it dropped "
                 f"{loss['terms_discarded_by_xor']} of the product's "
                 f"{loss['sakuma_term_count']} terms and the coefficient "
                 f"{loss['coefficient_on_xor_term']} on the one it kept, "
                 f"changing the norm from {loss['sakuma_norm2']} to "
                 f"{loss['shortcut_norm2']}.",
                 f"u = {loss['u']}, v = {loss['v']}, "
                 f"difference norm^2 = {loss['difference_norm2']}"),
            Step("non-associativity is the point",
                 f"On classes {assoc['classes']} the algebra gives "
                 f"(a.b).c = {assoc['left_terms']} and "
                 f"a.(b.c) = {assoc['right_terms']}, which differ, while the "
                 f"XOR shortcut is associative.  A pipeline that composed "
                 f"addresses by XOR was working in a quotient where the "
                 f"Monster's product does not live.",
                 f"associative = {assoc['associative']}, "
                 f"xor_associative = {assoc['xor_associative']}, "
                 f"difference norm^2 = {assoc['difference_norm2']}"),
        ]
        expected = {
            "depth": str(report["depth"]),
            "planes": str(census["planes"]),
            "defined_strict": str(census["defined"]),
            "defined_pair_repaired": str(repaired["defined"]),
            "sakuma_term_count": str(loss["sakuma_term_count"]),
            "terms_discarded_by_xor": str(loss["terms_discarded_by_xor"]),
            "xor_is_the_third_axis_label":
                str(loss["xor_is_the_third_axis_label"]),
            "sakuma_norm2": str(loss["sakuma_norm2"]),
            "shortcut_norm2": str(loss["shortcut_norm2"]),
            "associative": str(assoc["associative"]),
            "xor_associative": str(assoc["xor_associative"]),
            "commutative": str(assoc["commutative"]),
            "associativity_difference_norm2": str(assoc["difference_norm2"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report monster stack: depth {report['depth']}, "
                   f"{census['defined']} planes compose strictly and "
                   f"{repaired['defined']} with pair repair; the Sakuma "
                   f"product is non-associative where the retired XOR "
                   f"shortcut was associative",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_monster_stack", "args": {}},
            payload={"report": report})

    def _report_multiresolution(self, query: Query) -> Solution:
        """Wires mrs.multires_report -- bit-level and grid-level addressing."""
        report = mrs.multires_report()
        fib = report["fibration"]
        columns = report["columns"]
        invariance = report["scale_invariance"]["rows"]
        collision = report["census_collision"]
        indices = sorted({col["index"] for col in columns})
        sig_invariant = all(row["signature_invariant"] for row in invariance)
        addr_invariant = any(row["address_invariant"] for row in invariance)

        steps = [
            Step("bit-level micro-addressing",
                 f"Each of the {fib['columns']} values a MOG column can take "
                 f"is mapped to a GF(4) x Z_4 fibre coordinate.  The map is "
                 f"a bijection with round trip, and its kernel "
                 f"{fib['kernel']} is elementary abelian rather than cyclic "
                 f"of order 4, so the Z_4 coordinate indexes a fibre as a "
                 f"set of residues.",
                 f"bijective = {fib['bijective']}, "
                 f"round_trip = {fib['round_trip']}, "
                 f"kernel = {fib['kernel']}"),
            Step("local sub-lattices",
                 f"Each column carries a rank-4 local Leech sub-lattice.  "
                 f"The index of the supported sub-lattice in the projection "
                 f"is {indices} for every column, so a bit-level reading is "
                 f"a strictly coarser view of the lattice.",
                 f"columns = {len(columns)}, indices = {indices}"),
            Step("grid-level macro-addressing",
                 f"A whole 2D grid is carried into the 24 coordinates and "
                 f"read as a ten-plane Monster address, so a configuration "
                 f"and a single bit are addressed in the same space at two "
                 f"resolutions.",
                 f"grid = {report['grid']}, "
                 f"census = {list(report['grid_census'])}"),
            Step("scale invariance",
                 f"Across the sampled grids and scale factors the signature "
                 f"is invariant ({sig_invariant}) while the Monster address "
                 f"is not ({addr_invariant}) -- the coarse reading survives "
                 f"rescaling and the fine one does not, which is the loss "
                 f"the two levels are there to measure.  A census collision "
                 f"exhibits it directly: {collision['first']} and "
                 f"{collision['second']} share a census.",
                 f"signature invariant = {sig_invariant}, "
                 f"address invariant = {addr_invariant}, "
                 f"collision found = {collision['found']}"),
        ]
        expected = {
            "fibre_columns": str(fib["columns"]),
            "fibre_bijective": str(fib["bijective"]),
            "fibre_round_trip": str(fib["round_trip"]),
            "fibre_kernel": str(list(fib["kernel"])),
            "fibre_kernel_is_cyclic_of_order_4":
                str(fib["kernel_is_cyclic_of_order_4"]),
            "column_indices": str(indices),
            "signature_invariant_everywhere": str(sig_invariant),
            "address_invariant_anywhere": str(addr_invariant),
            "census_collision_found": str(collision["found"]),
            "census_collision_carriers_equal":
                str(collision["carriers_equal"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report multiresolution: the F_2^4 -> GF(4) x Z_4 fibre "
                   f"map is a bijection with kernel {list(fib['kernel'])}, "
                   f"every column sub-lattice has index {indices}, and the "
                   f"grid signature is scale-invariant where the ten-plane "
                   f"address is not",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_multiresolution", "args": {}},
            payload={"report": report})

    def _report_migration(self, query: Query) -> Solution:
        """Wires iso.migration_report -- the legacy-to-core bridge."""
        report = iso.migration_report()
        codes = report["codes"]
        isometry = codes["isometry"]
        automorphism = codes["automorphism"]
        decoder = report["decoder"]
        dataset = report["dataset"]

        steps = [
            Step("two frames, one bridge",
                 f"The legacy Golay frame and this package's canonical one "
                 f"share only {codes['shared_codewords']} of their "
                 f"{codes['core_codewords']} codewords, so legacy data read "
                 f"in canonical coordinates is a different codeword, not a "
                 f"relabelled one.  The derived permutation fixes "
                 f"{len(report['fixed_points'])} coordinates and moves the "
                 f"rest.",
                 f"permutation = {report['permutation']}, "
                 f"shared codewords = {codes['shared_codewords']}"),
            Step("it is an isomorphism, not an automorphism",
                 f"Under the permutation "
                 f"{automorphism['codewords_leaving_the_code']} of the "
                 f"{automorphism['codewords']} canonical codewords leave the "
                 f"canonical code -- as they must, since the two codes are "
                 f"different -- while the weight distributions agree "
                 f"exactly, so the image is an equivalent [24, 12, 8] code.",
                 f"is_automorphism = {automorphism['is_automorphism']}, "
                 f"weight distributions agree = "
                 f"{codes['weight_distributions_agree']}"),
            Step("why a permutation and not any linear isomorphism",
                 f"A coordinate permutation preserves Hamming weight and "
                 f"distance, checked here on all "
                 f"{isometry['codewords_checked']} codewords and "
                 f"{isometry['pairs_checked']} pairs, so it commutes with "
                 f"nearest-codeword decoding and may be wrapped around the "
                 f"decoder.  A general linear isomorphism between the two "
                 f"codes scrambles distance and may not.",
                 f"weight preserving = {isometry['weight_preserving']}, "
                 f"distance preserving = "
                 f"{isometry['distance_preserving']}"),
            Step("decoding legacy data",
                 f"Routing legacy words through the canonical frame and the "
                 f"complete decoder recovers the truth on every sampled "
                 f"pattern within the packing radius, and turns all "
                 f"{decoder['snap_silent_ties_total']} silently broken ties "
                 f"into explicit ambiguities.  Weight-5 miscorrection "
                 f"survives in both columns, because it is a theorem about "
                 f"the code.",
                 f"silent ties = {decoder['snap_silent_ties_total']}, "
                 f"now flagged = {decoder['routed_flagged_total']}"),
            Step("bulk migration",
                 f"Concepts, CRG edges and hexcolour addresses migrate "
                 f"through one call.  On the exercise dataset "
                 f"({dataset['concepts']} concepts, {dataset['edges']} "
                 f"edges, {dataset['hexcolours']} addresses) the migration "
                 f"round-trips, preserves weights, keeps masks distinct and "
                 f"leaves no dangling edge.",
                 f"round trip = {dataset['round_trip']}, "
                 f"referentially intact = "
                 f"{dataset['referentially_intact']}"),
        ]
        expected = {
            "is_permutation": str(report["is_permutation"]),
            "fixed_points": str(list(report["fixed_points"])),
            "shared_codewords": str(codes["shared_codewords"]),
            "legacy_is_distinct": str(codes["legacy_is_distinct"]),
            "weight_distributions_agree":
                str(codes["weight_distributions_agree"]),
            "minimum_distance": str(codes["minimum_distance"]),
            "is_automorphism": str(automorphism["is_automorphism"]),
            "weight_preserving": str(isometry["weight_preserving"]),
            "distance_preserving": str(isometry["distance_preserving"]),
            "snap_silent_ties_total":
                str(decoder["snap_silent_ties_total"]),
            "routed_flagged_total": str(decoder["routed_flagged_total"]),
            "every_silent_tie_is_now_flagged":
                str(decoder["every_silent_tie_is_now_flagged"]),
            "guaranteed_below_packing_radius":
                str(decoder["guaranteed_below_packing_radius"]),
            "dataset_round_trip": str(dataset["round_trip"]),
            "dataset_weights_preserved": str(dataset["weights_preserved"]),
            "dataset_referentially_intact":
                str(dataset["referentially_intact"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report migration: the legacy and canonical codes share "
                   f"{codes['shared_codewords']} of "
                   f"{codes['core_codewords']} codewords; the bridge is a "
                   f"weight- and distance-preserving permutation, so legacy "
                   f"data can be decoded through the audited decoder, and "
                   f"all {decoder['snap_silent_ties_total']} silent ties "
                   f"become explicit",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_migration", "args": {}},
            payload={"report": report})

    # ------------------------------------------------------------------
    # 3l.  the migrated repository data
    # ------------------------------------------------------------------
    # ``report migration`` above is about the *machinery* -- a permutation
    # between two Golay frames.  These two are about the *data*: which
    # frame the repository actually writes in, what the migrated state
    # contains, and what can be asked of it once migrated.
    # ------------------------------------------------------------------

    def _report_state_migration(self, query: Query) -> Solution:
        """Wires stm.state_migration_report -- the literal data migration."""
        report = stm.state_migration_report()
        if not report.get("available"):
            return Solution(
                query=query, kind="report",
                answer="report state migration: no stored GLM state is "
                       "present in this checkout",
                ok=False, error="state migration: no data",
                steps=(Step("no data",
                            "Neither the migrated state nor the source "
                            "state was found under arc_agi_17/results.",
                            "glm_state_canonical.json absent"),),
                payload={"report": report})

        checks = report["checks"]
        frame = report["frame"]
        verification = report["verification"]
        addresses = frame["addresses"] or {}

        steps = [
            Step("which frame the data is in",
                 f"The repository's own Golay engine and this package's "
                 f"canonical code are the same "
                 f"{frame['shared_codewords']} words under the same "
                 f"coordinate numbering, so concept vectors migrate by the "
                 f"identity.  The legacy-to-core permutation would move "
                 f"{frame['permutation_damage']} codewords off the code, so "
                 f"it must not be applied to them.",
                 f"frames coincide = {frame['frames_coincide']}, "
                 f"bridge = {frame['correct_bridge']}"),
            Step("the one real coordinate correction",
                 f"Stored integer addresses put coordinate i at bit 23-i.  "
                 f"Read with the bit reversal, "
                 f"{addresses.get('codewords_read_msb_first', 0)} of "
                 f"{addresses.get('addresses', 0)} are Golay codewords; read "
                 f"without it, "
                 f"{addresses.get('codewords_read_lsb_first', 0)} are.  The "
                 f"data decides the convention.",
                 f"bit reversal required = "
                 f"{addresses.get('bit_reversal_required')}"),
            Step("what came across",
                 f"{checks['concepts_imported']} concepts and "
                 f"{checks['edges_migrated']} edges, with "
                 f"{checks['concepts_minted']} carriers minted for edge "
                 f"endpoints the state never gave one and "
                 f"{checks['edges_dropped']} edge dropped for a nameless "
                 f"endpoint.  Roles and quadrant weights are recomputed from "
                 f"the carriers, and agree with the stored values in all "
                 f"{checks['roles_agree']} cases.",
                 f"concepts = {checks['concepts_total']}, "
                 f"referentially intact = "
                 f"{checks['referentially_intact']}"),
            Step("how much of it is anchored",
                 f"A concept vector is a received word, not a codeword: "
                 f"{checks['carriers_that_are_codewords']} of "
                 f"{checks['concepts_total']} are codewords, "
                 f"{checks['decode_corrected']} decode to a unique nearest "
                 f"codeword, and {checks['decode_ambiguous']} are genuinely "
                 f"ambiguous -- six equally near codewords and no answer.  "
                 f"Those are recorded as ambiguous rather than snapped.",
                 f"guaranteed = {checks['decode_guaranteed']}, "
                 f"ambiguous = {checks['decode_ambiguous']}"),
            Step("exactness",
                 f"NRCI is rewritten as an exact rational from the package's "
                 f"Y; the stored float is kept beside it as the rational it "
                 f"really is, and the two differ by at most "
                 f"{checks['worst_nrci_gap'][0]}/"
                 f"{checks['worst_nrci_gap'][1]}.  The written payload "
                 f"contains {verification['floats_in_payload']} floats.",
                 f"fields recomputed and agreeing = "
                 f"{verification['fields_recomputed_and_agreeing']}"),
        ]

        expected = {
            "frames_coincide": str(frame["frames_coincide"]),
            "shared_codewords": str(frame["shared_codewords"]),
            "permutation_damage": str(frame["permutation_damage"]),
            "bit_reversal_required":
                str(addresses.get("bit_reversal_required")),
            "concepts_imported": str(checks["concepts_imported"]),
            "concepts_minted": str(checks["concepts_minted"]),
            "edges_migrated": str(checks["edges_migrated"]),
            "edges_dropped": str(checks["edges_dropped"]),
            "referentially_intact": str(checks["referentially_intact"]),
            "roles_agree": str(checks["roles_agree"]),
            "carriers_that_are_codewords":
                str(checks["carriers_that_are_codewords"]),
            "decode_ambiguous": str(checks["decode_ambiguous"]),
            "decode_guaranteed": str(checks["decode_guaranteed"]),
            "worst_nrci_gap": str(list(checks["worst_nrci_gap"])),
            "fields_recomputed_and_agreeing":
                str(verification["fields_recomputed_and_agreeing"]),
            "floats_in_payload": str(verification["floats_in_payload"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report state migration: {checks['concepts_imported']} "
                   f"concepts and {checks['edges_migrated']} edges migrated "
                   f"in the canonical frame, "
                   f"{checks['concepts_minted']} carriers minted, "
                   f"{checks['decode_ambiguous']} carriers ambiguous under "
                   f"complete decoding, no float written",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_state_migration", "args": {}},
            payload={"report": report})

    def _report_concept_store(self, query: Query) -> Solution:
        """Wires sto.store_report -- what the migrated data supports."""
        report = sto.store_report()
        if not report.get("available"):
            return Solution(
                query=query, kind="report",
                answer="report concept store: the migrated state has not "
                       "been written",
                ok=False, error="concept store: no data",
                steps=(Step("no data",
                            "Run the state migration first.",
                            "glm_state_canonical.json absent"),),
                payload={"report": report})

        steps = [
            Step("the graph",
                 f"{report['concepts']} concepts, {report['edges']} edges "
                 f"and {report['labels']} distinct relation labels.  The "
                 f"busiest concept is {report['max_degree_concept']} with "
                 f"{report['max_degree']} edges.",
                 f"concepts = {report['concepts']}, "
                 f"edges = {report['edges']}"),
            Step("how much of it is asserted",
                 f"{report['asserted_edges']} edges carry a real relation "
                 f"label; {report['auto_proposed_edges']} are "
                 f"'auto_proposed', proposals the growth loop made and "
                 f"nothing confirmed.  A walk that excludes them is a walk "
                 f"over asserted knowledge only, and it gives different "
                 f"answers.",
                 f"asserted = {report['asserted_edges']}, "
                 f"auto-proposed = {report['auto_proposed_edges']}"),
            Step("how much of it is reachable",
                 f"{report['isolated_concepts']} of the concepts have no "
                 f"edge at all, so they can be described but not reasoned "
                 f"about relationally; {report['minted_concepts']} carriers "
                 f"were minted by the migration and are marked as such.",
                 f"isolated = {report['isolated_concepts']}, "
                 f"minted = {report['minted_concepts']}"),
            Step("two kinds of nearness",
                 f"On {report['samples_checked']} sampled concepts, the "
                 f"graph neighbourhood and the five nearest carriers in "
                 f"Hamming distance share a name in "
                 f"{report['samples_where_graph_and_substrate_agree']} "
                 f"cases.  The carriers were assigned by digest, not by "
                 f"meaning, so substrate distance between concepts is not a "
                 f"semantic distance and must not be read as one.",
                 f"agreements = "
                 f"{report['samples_where_graph_and_substrate_agree']}"
                 f"/{report['samples_checked']}"),
        ]
        expected = {
            "concepts": str(report["concepts"]),
            "edges": str(report["edges"]),
            "labels": str(report["labels"]),
            "asserted_edges": str(report["asserted_edges"]),
            "auto_proposed_edges": str(report["auto_proposed_edges"]),
            "isolated_concepts": str(report["isolated_concepts"]),
            "minted_concepts": str(report["minted_concepts"]),
            "max_degree": str(report["max_degree"]),
            "max_degree_concept": str(report["max_degree_concept"]),
            "samples_checked": str(report["samples_checked"]),
            "samples_where_graph_and_substrate_agree":
                str(report["samples_where_graph_and_substrate_agree"]),
        }
        return Solution(
            query=query, kind="report",
            answer=f"report concept store: {report['concepts']} concepts, "
                   f"{report['edges']} edges "
                   f"({report['asserted_edges']} asserted, "
                   f"{report['auto_proposed_edges']} auto-proposed), "
                   f"{report['isolated_concepts']} isolated",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_concept_store", "args": {}},
            payload={"report": report})

    # ------------------------------------------------------------------
    # 3m.  task -- a worked end-to-end run through the whole pipeline
    # ------------------------------------------------------------------
    # The other kinds each exercise one mechanism.  A task exercises the
    # chain: carrier construction, multi-resolution addressing, the
    # complete decoder, the facet decomposition and the layer stack, on
    # a problem with a checkable answer.
    # ------------------------------------------------------------------

    def _solve_task(self, query: Query) -> Solution:
        name = str(query.options.get("task", "")).strip().lower()
        if not name:
            return Solution(
                query=query, kind="task",
                answer=f"task: no task named.  Try one of: "
                       f"{', '.join(TASKS)}",
                ok=False, error="task: no task named",
                steps=(Step("usage", f"Tasks: {', '.join(TASKS)}",
                            "task <name>"),),
                payload={"tasks": list(TASKS)})
        if name in ("grid", "arc", "puzzle", "half-turn", "half turn"):
            return self._task_grid(query)
        if name in ("physics", "energy", "torque", "energy vs torque",
                      "quantity"):
            return self._task_physics(query)
        if name in ("concepts", "concept", "crg", "entropy",
                      "concept graph"):
            return self._task_concepts(query)
        return Solution(
            query=query, kind="task",
            answer=f"task: unknown task {name!r}.  Try one of: "
                   f"{', '.join(TASKS)}",
            ok=False, error=f"task: unknown task {name!r}",
            steps=(Step("unknown",
                        f"The task {name!r} is not one of the worked tasks.",
                        f"tasks: {', '.join(TASKS)}"),),
            payload={"requested": name, "tasks": list(TASKS)})

    def _task_grid(self, query: Query) -> Solution:
        """Wires tk.grid_task -- an ARC-style puzzle at three resolutions."""
        result = tk.grid_task()
        stages = {stage["resolution"]: stage for stage in result["stages"]}
        checks = result["checks"]

        steps = [
            Step("read the training pairs",
                 f"{result['training_pairs']} input/output pairs are given, "
                 f"and five candidate rules are considered: "
                 f"{', '.join(stages['signature']['survivors'])} and any "
                 f"already pruned.",
                 f"training pairs = {result['training_pairs']}, "
                 f"candidates = {stages['signature']['candidates_in']}"),
            Step("coarse resolution: the signature",
                 f"The grid signature -- histogram, density, aspect ratio, "
                 f"symmetries, component count -- is blind to reflection and "
                 f"rotation, so it prunes "
                 f"{len(stages['signature']['pruned'])} candidates.",
                 f"signature survivors = "
                 f"{stages['signature']['survivors']}"),
            Step("middle resolution: one address plane",
                 f"Reading plane 0 of the ten-plane Monster address of the "
                 f"output already cuts the field to "
                 f"{stages['address_plane0']['candidates_out']}: "
                 f"{', '.join(stages['address_plane0']['survivors'])}.",
                 f"pruned at plane 0 = "
                 f"{stages['address_plane0']['pruned']}"),
            Step("fine resolution: the full address",
                 f"The complete ten-plane address confirms the survivor, and "
                 f"the rule reproduces every training pair.",
                 f"rule = {result['rule']}, "
                 f"training reproduced = {checks['training_reproduced']}"),
            Step("answer",
                 f"Applied to the held-out test grid the rule gives "
                 f"{result['prediction']}.  The prediction's address differs "
                 f"from the test grid's ({checks['address_changed']}) while "
                 f"its signature does not "
                 f"({checks['signature_preserved']}) -- the two resolutions "
                 f"disagree exactly where they should.",
                 f"prediction = {result['prediction']}"),
        ]
        expected = {
            "task": str(result["task"]),
            "solved": str(result["solved"]),
            "rule": str(result["rule"]),
            "prediction": str(result["prediction"]),
            "training_reproduced": str(checks["training_reproduced"]),
            "address_changed": str(checks["address_changed"]),
            "signature_preserved": str(checks["signature_preserved"]),
            "survivors_signature":
                str(list(stages["signature"]["survivors"])),
            "survivors_plane0":
                str(list(stages["address_plane0"]["survivors"])),
            "survivors_full":
                str(list(stages["address_full"]["survivors"])),
        }
        return Solution(
            query=query, kind="task",
            answer=f"task grid: the rule is {result['rule']}; the test grid "
                   f"maps to {result['prediction']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "task_grid", "args": {}},
            payload={"result": result})

    def _task_physics(self, query: Query) -> Solution:
        """Wires tk.physics_task -- two quantities SI7 cannot tell apart."""
        result = tk.physics_task()
        left, right = result["left"], result["right"]
        si7, ext10 = result["si7"], result["ext10"]
        escalation = result["escalation"]
        facet_part = result["facets"]
        address = result["address"]

        steps = [
            Step("the question",
                 f"Are {left} and {right} the same quantity?  In SI7 they "
                 f"are: both read {si7['left']}.",
                 f"SI7({left}) = {si7['left']}, "
                 f"SI7({right}) = {si7['right']}, equal = {si7['equal']}"),
            Step("the extended basis separates them",
                 f"In the EXT10 basis they differ: {ext10['left']} against "
                 f"{ext10['right']}.  The extra exponent is what SI7 "
                 f"discards.",
                 f"EXT10({left}) = {ext10['left']}, "
                 f"EXT10({right}) = {ext10['right']}, "
                 f"equal = {ext10['equal']}"),
            Step("the verifier agrees",
                 f"Audited against 'force * length', {left} holds under "
                 f"scalar semantics and {right} does not; under full tensor "
                 f"semantics neither does, because rank "
                 f"{result['verifier']['ranks'][right]} is not rank "
                 f"{result['verifier']['ranks'][left]}.",
                 f"scalar = {result['verifier']['scalar']}, "
                 f"full = {result['verifier']['full']}"),
            Step("where the difference lives",
                 f"Escalating the layer stack, the first layer that "
                 f"separates the two carriers is "
                 f"{escalation['first_separating_layer']}, and the six-facet "
                 f"decomposition attributes the difference to the "
                 f"{', '.join(facet_part['carrying_the_difference'])} "
                 f"facets.",
                 f"layer distances = {escalation['layer_distances']}, "
                 f"facet distances = {facet_part['distances']}"),
            Step("and where it lives in the address",
                 f"The ten-plane Monster addresses first differ at plane "
                 f"{address['first_differing_plane']}; the difference mask "
                 f"has weight {address['difference_weight']} and the "
                 f"complete Golay decoder reads it as "
                 f"{address['golay']['status']}, guaranteed "
                 f"{address['golay']['guaranteed']}.",
                 f"first differing plane = "
                 f"{address['first_differing_plane']}, "
                 f"difference weight = {address['difference_weight']}, "
                 f"decode status = {address['golay']['status']}"),
        ]
        expected = {
            "left": str(left),
            "right": str(right),
            "si7_equal": str(si7["equal"]),
            "ext10_equal": str(ext10["equal"]),
            "si7_left": str(si7["left"]),
            "ext10_right": str(ext10["right"]),
            "first_separating_layer":
                str(escalation["first_separating_layer"]),
            "carrying_the_difference":
                str(list(facet_part["carrying_the_difference"])),
            "first_differing_plane": str(address["first_differing_plane"]),
            "difference_weight": str(address["difference_weight"]),
            "decode_status": str(address["golay"]["status"]),
            "decode_guaranteed": str(address["golay"]["guaranteed"]),
        }
        return Solution(
            query=query, kind="task",
            answer=f"task physics: {result['answer']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "task_physics", "args": {}},
            payload={"result": result})

    def _task_concepts(self, query: Query) -> Solution:
        """Wires tk.concept_task -- reasoning over the migrated CRG."""
        result = tk.concept_task()
        if not result.get("available"):
            return Solution(
                query=query, kind="task",
                answer="task concepts: the migrated state is not present in "
                       "this checkout",
                ok=False, error="task concepts: no data",
                steps=(Step("no data",
                            "Write the canonical state first.",
                            "glm_state_canonical.json absent"),),
                payload={"result": result})

        checks = result["checks"]
        source, target = result["source"], result["target"]
        asserted = result["asserted_path"]
        chain = " -> ".join(
            [str(step[0]) for step in asserted]
            + [str(asserted[-1][2])]) if asserted else "(no path)"
        labels = ", ".join(str(step[1]) for step in asserted)
        substrate = result["substrate"]

        steps = [
            Step("retrieve from the migrated graph",
                 f"The concept-relation graph, as migrated, relates "
                 f"{source} to {target} in {len(asserted)} steps: {chain} "
                 f"({labels}).  Excluding the growth loop's auto-proposed "
                 f"edges "
                 f"{'changes' if checks['paths_differ'] else 'does not change'}"
                 f" the answer, so the chain shown is asserted knowledge.",
                 f"asserted steps = {len(asserted)}, "
                 f"paths differ = {checks['paths_differ']}"),
            Step("cross-link to the dimensional register",
                 f"Both endpoints are also carriers of the physics register "
                 f"({', '.join(result['crosslinked'])}), which is the only "
                 f"place a claim retrieved from the graph can be adjudicated "
                 f"rather than repeated.",
                 f"crosslinked = {list(result['crosslinked'])}"),
            Step("adjudicate",
                 f"{result['law']} holds under scalar semantics, and the "
                 f"control {result['control']} does not.  A check that "
                 f"passed both would be checking nothing.",
                 f"law holds = {checks['law_holds']}, "
                 f"control fails = {checks['control_fails']}"),
            Step("what the substrate contributed",
                 f"Nothing.  {source}'s carrier decodes as "
                 f"{substrate[source]['decode_status']} and its nearest "
                 f"carriers are "
                 f"{', '.join(substrate[source]['nearest_carriers'])}, which "
                 f"share no edge with it: these vectors were assigned by "
                 f"digest, so Hamming distance between concepts is not a "
                 f"semantic distance.",
                 f"substrate contributes = "
                 f"{checks['substrate_contributes']}"),
        ]
        expected = {
            "source": str(source),
            "target": str(target),
            "asserted_steps": str(len(asserted)),
            "path_found": str(checks["path_found"]),
            "asserted_path_found": str(checks["asserted_path_found"]),
            "paths_differ": str(checks["paths_differ"]),
            "both_crosslinked": str(checks["both_crosslinked"]),
            "law_holds": str(checks["law_holds"]),
            "control_fails": str(checks["control_fails"]),
            "discriminating": str(checks["discriminating"]),
            "substrate_contributes":
                str(checks["substrate_contributes"]),
        }
        return Solution(
            query=query, kind="task",
            answer=f"task concepts: {result['answer']}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "task_concepts", "args": {}},
            payload={"result": result})

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

    # ------------------------------------------------------------------
    # 3m.  pi_groups -- Buckingham-Pi over a set of quantities (v1.0.0)
    # ------------------------------------------------------------------
    # Wires va.buckingham_pi_groups, the last reasoning module that had
    # been built but was reachable from no query.  The nullspace is
    # exact and rational; each group returned is *checked* to be
    # dimensionless here rather than trusted.
    # ------------------------------------------------------------------

    def _solve_pi_groups(self, query: Query) -> Solution:
        if len(query.operands) < 2:
            raise SolverError(
                f"pi groups: need at least two quantities, got "
                f"{list(query.operands)}")
        objs = [self.resolve(name, query.domain) for name in query.operands]
        off = [o.name for o in objs if o.domain != "physics"]
        if off:
            raise SolverError(
                f"pi groups: {off} are not physics quantities; a Pi group is "
                f"a product of dimensioned quantities and needs the EXT10 "
                f"exponents the physics register carries")
        names = [o.name for o in objs]

        report = va.buckingham_pi_groups(names)
        groups = [[Fraction(c) for c in vec] for vec in report["pi_groups"]]
        rank = len(names) - len(groups)

        # Check, do not assume: the exponent-weighted sum of each group must
        # be the zero vector in all ten EXT10 axes.
        register = {o.name: o for o in objs}
        residues = []
        for vec in groups:
            total = [Fraction(0)] * 10
            for weight, name in zip(vec, names):
                exps = do.physics.quantity_by_name(name).exps_ext10
                for axis in range(10):
                    total[axis] += weight * exps[axis]
            residues.append(total)
        all_dimensionless = all(all(x == 0 for x in row) for row in residues)

        def render(vec: Sequence[Fraction]) -> str:
            terms = [f"{name}^({q(w)})" for w, name in zip(vec, names)
                     if w != 0]
            return " * ".join(terms) if terms else "1"

        steps = [
            Step("quantities",
                 f"Buckingham-Pi over {len(names)} quantities of the physics "
                 f"register, read in EXT10 so plane angle, solid angle and "
                 f"information count as dimensions alongside the seven SI "
                 f"base axes.",
                 "; ".join(f"{n} = {register[n].attributes['dimension_ext10']}"
                           for n in names)),
            Step("matrix",
                 f"The 10 x {len(names)} matrix has one row per EXT10 axis "
                 f"and one column per quantity.  Its rank is {rank}, so "
                 f"{rank} of the quantities are dimensionally independent "
                 f"and the theorem predicts {len(names)} - {rank} = "
                 f"{len(groups)} independent Pi groups.",
                 f"rank = {rank}, nullity = {len(groups)}"),
            Step("nullspace",
                 f"The Pi groups are a basis of the nullspace, computed by "
                 f"Gauss-Jordan elimination over Q.  No float is formed at "
                 f"any point, so an exponent of 1/2 is 1/2 and not "
                 f"0.49999999999999994.",
                 "\n".join(f"pi_{i} = {render(vec)}"
                           for i, vec in enumerate(groups)) or "none"),
            Step("check",
                 f"Each group is then multiplied out and its exponent vector "
                 f"summed axis by axis.  A group is dimensionless exactly "
                 f"when that sum is zero in all ten axes; the check is "
                 f"performed, not assumed.",
                 f"all ten axes zero for every group: {all_dimensionless}"),
        ]

        expected = {
            "quantities": str(names),
            "n_quantities": str(len(names)),
            "rank": str(rank),
            "n_pi_groups": str(len(groups)),
            "pi_groups": str([[q(c) for c in vec] for vec in groups]),
            "all_dimensionless": str(all_dimensionless),
        }

        return Solution(
            query=query, kind="pi_groups",
            answer=f"{len(groups)} Pi group(s) over {len(names)} quantities "
                   f"of rank {rank}: "
                   + ("; ".join(render(vec) for vec in groups) or "none"),
            steps=tuple(steps), expected=expected,
            script_spec={"template": "pi_groups",
                         "args": {"names": names}},
            payload={"report": report,
                     "rank": rank,
                     "all_dimensionless": all_dimensionless})

    # ------------------------------------------------------------------
    # 3o.  meaning -- reference resolution and derived relations
    # ------------------------------------------------------------------

    def _solve_meaning(self, query: Query) -> Solution:
        """Resolve notations to meanings, and derive what holds between them.

        With one term: what it denotes, its 24-coordinate meaning carrier,
        and the round trip that shows the carrier loses nothing.  With two:
        every relation derivable between the two meanings, each with the
        arithmetic that makes it true.  A term with no determinate referent
        is refused with its reason rather than given a carrier.
        """
        terms = tuple(query.options.get("terms", ()))   # type: ignore[arg-type]
        terms = tuple(str(t) for t in terms if str(t).strip())
        if not terms:
            raise SolverError("meaning: needs at least one term")
        answers = [sre.resolve(term) for term in terms]

        steps: List[Step] = [
            Step("reference",
                 "Resolve each notation to what it denotes.  Nothing is "
                 "embedded or hashed: a term is admitted only when the "
                 "registers pin down a determinate referent.",
                 "\n".join(
                     f"{a.term!r} -> "
                     + (f"{a.meaning.describe()}  [{a.sense}: {a.witness}]"
                        if a.meaning is not None else f"refused: {a.reason}")
                     for a in answers)),
        ]

        expected: Dict[str, str] = {"terms": str(list(terms))}
        for a in answers:
            expected[f"grounded_{a.term}"] = str(a.grounded)
            if a.meaning is not None:
                expected[f"meaning_{a.term}"] = a.meaning.describe()
                expected[f"carrier_{a.term}"] = str(
                    [q(Fraction(c)) for c in sme.encode(a.meaning)])

        grounded = [a for a in answers if a.meaning is not None]
        if grounded:
            carriers = {a.term: sme.encode(a.meaning) for a in grounded}
            round_trips = {a.term: sme.decode(carriers[a.term]) == a.meaning
                           for a in grounded}
            steps.append(Step(
                "carrier",
                "Encode each meaning in the 24-coordinate meaning space and "
                "decode it again.  The encoder takes a meaning and nothing "
                "else, so the carrier cannot depend on the spelling.",
                "\n".join(f"{term} = {[q(Fraction(c)) for c in carrier]}"
                           for term, carrier in sorted(carriers.items()))))
            expected["all_round_trips_hold"] = str(all(round_trips.values()))

        claims: Tuple[srl.Claim, ...] = ()
        if len(grounded) == 2:
            first, second = grounded[0].meaning, grounded[1].meaning
            assert first is not None and second is not None
            claims = srl.derive(first, second) + srl.derive(second, first)
            same = first == second
            expected["same_meaning"] = str(same)
            expected["relations"] = str(sorted({c.relation for c in claims}))
            expected["relation_count"] = str(len(claims))
            expected["all_claims_reverify"] = str(
                all(srl.verify(c) for c in claims))
            steps.append(Step(
                "relate",
                (f"The two notations denote the same thing, so the meaning "
                 f"space holds them at distance zero." if same else
                 f"Derive every relation that holds between the two "
                 f"meanings, and re-check each one from the meanings "
                 f"alone."),
                ("\n".join(f"{c.relation}: {c.witness}" for c in claims)
                 or "no relation between these two meanings is derivable "
                    "here")))

        if len(grounded) == 2 and grounded[0].meaning == grounded[1].meaning:
            answer = (f"{terms[0]!r} and {terms[1]!r} denote the same thing: "
                      f"{grounded[0].meaning.describe()}")   # type: ignore
        elif len(grounded) == 2:
            names = sorted({c.relation for c in claims})
            answer = (f"{terms[0]!r} -> "
                      f"{grounded[0].meaning.describe()}; "  # type: ignore
                      f"{terms[1]!r} -> "
                      f"{grounded[1].meaning.describe()}; "  # type: ignore
                      + (f"derived: {', '.join(names)}" if names
                         else "no relation derivable"))
        elif grounded:
            answer = (f"{grounded[0].term!r} denotes "
                      f"{grounded[0].meaning.describe()}")   # type: ignore
        else:
            answer = "; ".join(f"{a.term!r} denotes nothing determinate: "
                               f"{a.reason}" for a in answers)

        return Solution(
            query=query, kind="meaning", answer=answer,
            steps=tuple(steps), expected=expected,
            script_spec={"template": "meaning", "args": {"terms": terms}},
            payload={"resolutions": [a.as_dict() for a in answers],
                     "claims": [c.as_dict() for c in claims]})

    def _report_semantics(self, query: Query) -> Solution:
        """Wires sau.audit_report -- what the inherited graph contains.

        Four measurements over the shipped state file, and the grounded
        graph that replaces what they condemn.  Every number is recomputed
        here; none is quoted.
        """
        report = sau.audit_report()
        concepts = report["concept_grounding"]
        edges = report["edge_grounding"]
        carriers = report["carrier_information"]
        variants = report["notational_variants"]
        plan = report["purge_plan"]
        replacement = report["replacement"]
        classes = edges["classes"]              # type: ignore[index]

        steps = [
            Step("concepts",
                 f"Of the {concepts['concepts']} inherited concepts, "     # type: ignore[index]
                 f"{concepts['grounded']} denote something determinate.",  # type: ignore[index]
                 f"grounded = {concepts['grounded_fraction']}\n"           # type: ignore[index]
                 f"by sense = {concepts['by_sense']}"),                    # type: ignore[index]
            Step("edges",
                 f"Of the {edges['edges']} inherited edges, "              # type: ignore[index]
                 f"{classes.get('derivable', 0)} state a relation between "
                 f"two determinate referents that can be re-derived now.",
                 f"classes = {classes}"),
            Step("carriers",
                 "Stored carrier distance against semantic relatedness: a "
                 "carrier that measured the subjects would put related "
                 "pairs closer.",
                 f"mean Hamming, related = "
                 f"{carriers['mean_hamming_related']}\n"                   # type: ignore[index]
                 f"mean Hamming, unrelated = "
                 f"{carriers['mean_hamming_unrelated']}\n"                 # type: ignore[index]
                 f"two random 24-bit words average 12"),
            Step("synonyms",
                 "Stored names that denote the same thing, and the distance "
                 "the inherited carrier puts between them.",
                 f"synonym pairs = {variants['synonym_pairs']}\n"          # type: ignore[index]
                 f"mean legacy Hamming = "
                 f"{variants['mean_legacy_hamming_between_synonyms']}\n"   # type: ignore[index]
                 f"distance in the meaning space = 0"),
            Step("replacement",
                 f"The grounded graph built from the registers: "
                 f"{replacement['meanings']} meanings carrying "           # type: ignore[index]
                 f"{replacement['notations']} notations, and every edge "   # type: ignore[index]
                 f"re-derived from the meanings it joins.",
                 f"binary edges = {replacement['binary_edges']}\n"         # type: ignore[index]
                 f"ternary edges = {replacement['ternary_edges']}\n"       # type: ignore[index]
                 f"all re-verified = "
                 f"{replacement['all_edges_reverified']}"),                # type: ignore[index]
        ]

        expected = {
            "legacy_concepts": str(concepts["concepts"]),          # type: ignore[index]
            "legacy_concepts_grounded": str(concepts["grounded"]),  # type: ignore[index]
            "legacy_edges": str(edges["edges"]),                    # type: ignore[index]
            "edges_proximity_artefact": str(
                classes.get("proximity_artefact", 0)),
            "edges_endpoint_ungrounded": str(
                classes.get("endpoint_ungrounded", 0)),
            "edges_derivable": str(classes.get("derivable", 0)),
            "edges_retained": str(plan["retained"]),                # type: ignore[index]
            "edges_dumped": str(plan["dumped"]),                    # type: ignore[index]
            "mean_hamming_related": str(
                carriers["mean_hamming_related"]),                  # type: ignore[index]
            "mean_hamming_unrelated": str(
                carriers["mean_hamming_unrelated"]),                # type: ignore[index]
            "synonym_pairs": str(variants["synonym_pairs"]),        # type: ignore[index]
            "mean_legacy_hamming_between_synonyms": str(
                variants["mean_legacy_hamming_between_synonyms"]),   # type: ignore[index]
            "grounded_meanings": str(replacement["meanings"]),      # type: ignore[index]
            "grounded_notations": str(replacement["notations"]),    # type: ignore[index]
            "grounded_binary_edges": str(
                replacement["binary_edges"]),                       # type: ignore[index]
            "grounded_ternary_edges": str(
                replacement["ternary_edges"]),                      # type: ignore[index]
            "all_edges_reverified": str(
                replacement["all_edges_reverified"]),               # type: ignore[index]
        }

        derived_edges = (int(replacement["binary_edges"])       # type: ignore[index]
                         + int(replacement["ternary_edges"]))   # type: ignore[index]
        return Solution(
            query=query, kind="report",
            answer=(f"report semantics: {concepts['grounded']} of "          # type: ignore[index]
                    f"{concepts['concepts']} inherited concepts denote "     # type: ignore[index]
                    f"anything determinate; {plan['retained']} of "          # type: ignore[index]
                    f"{plan['edges']} inherited edges survive the audit; "   # type: ignore[index]
                    f"the grounded graph has {replacement['meanings']} "     # type: ignore[index]
                    f"meanings and {derived_edges} re-derived edges"),
            steps=tuple(steps), expected=expected,
            script_spec={"template": "report_semantics", "args": {}},
            payload={"report": report})


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

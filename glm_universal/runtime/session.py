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
Seven come from :mod:`glm_universal.data_objects`:
``physics`` (726 quantities), ``chemistry`` (118 elements),
``molecules`` (51 molecules and ions, every coordinate derived from the
element register), ``mathematics`` (rational matrices, reflections and
field elements),
``lexicon`` (relational concepts), ``harmonics`` (28 musical intervals as
exact rational frequency ratios, every coordinate derived from the pair
``(n, d)``) and ``economics`` (21 quoted prices as exact rationals, every
coordinate derived from the price and its magnitude).  An eighth,
``spatial``, is built here in :func:`spatial_objects`
from the MOG's own structures -- the trio's three octads, the sextet's six
tetrads, the four rows of the ``4 x 6`` frame, and the fifteen octads
obtained as unions of tetrad pairs.  It is a presentation of the substrate,
not a new dataset, and every member is checked against
:data:`glm_universal.substrate.mog.GOLAY_SET` at build time.

Loading is lazy and cached: a session that only asks physics questions never
pays for the element register, and no register is ever loaded twice.

Where the solvers live
----------------------
One solver per query kind, and they are methods of :class:`GeometricSession`
-- except the ``report <subject>`` family, which is forty-seven solvers and
was two thirds of this file.  Those moved to
:mod:`glm_universal.runtime.reports` in v1.12.0, one module per family named
for the sub-package that computes it, each a mixin this class inherits.  What
stays here is the dispatcher: :meth:`_solve_report` maps a subject, and its
aliases, onto one of them, and :data:`REPORT_SUBJECTS` is still the one list
of subject names.  The carriers a solver returns are in
:mod:`glm_universal.runtime.solution` and the payload renderers in
:mod:`glm_universal.runtime.payload`, both re-exported here, so
``from ...session import Solution`` keeps working.

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
from dataclasses import replace
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from .. import data_objects as do
from ..data_objects.base import DataObject
from ..reasoning import analogy as an
from ..reasoning import analogy_models as am
from ..reasoning import coherence as co
from ..reasoning import dimension_layers as dl
from ..reasoning import exact_real as xr
from ..reasoning import measure_view as mvw
from ..reasoning import metric as me
from ..reasoning import product as pr
from ..reasoning import tasks as tk
from ..reasoning import term_arithmetic as tar
from ..reasoning import valorani as va
from ..reasoning import verifier as ve
from ..substrate import digit_stack as ds
from ..substrate import leech2, mog
from .. import recipe as rcp
from ..semantics import meaning as sme
from ..semantics import reference as sre
from ..semantics import relations as srl
from . import parser as PA
from .parser import ConceptIndex, Query, QueryError, parse_query
from .payload import as_magnitude, jsonable
from .reports import (DevelopmentReports, LanguageReports,
                      LatticeGeometryReports, LedgerReports,
                      MigrationReports, ReasoningReports, RecipeReports,
                      RegisterReports,
                      ResolutionReports, SemanticsReports,
                      SignalReports, SubstrateReports)
from .solution import (InferenceRecord, Solution, SolverError, Step, q)

__all__ = [
    "SolverError", "DOMAINS", "DEFAULT_SUBSPACE", "REPORT_SUBJECTS",
    "TASKS", "Step", "Solution", "InferenceRecord", "GeometricSession",
    "spatial_objects", "q",
]


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
    "blueprint", "reversible", "mantissa", "engine", "noise",
    "signature", "drift", "catalog", "containers", "companion",
    "lattices", "shells", "llvq", "harmony", "economics",
    "lean", "directives", "pipeline", "escalation", "measure",
    "names", "recipe", "language", "searchloop", "retrieval",
    "controller",
)

#: The canonical names of the worked end-to-end tasks ``task <name>`` runs.
TASKS: Tuple[str, ...] = ("grid", "physics", "concepts")

#: The registers a session can load, in a fixed order.
DOMAINS: Tuple[str, ...] = (
    "physics", "chemistry", "molecules", "mathematics", "lexicon",
    "spatial", "harmonics", "economics",
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
    # As of v1.7.0.  An interval's carrier holds its numerator and
    # denominator outright beside a dozen quantities derived from them, so a
    # raw 24-coordinate difference would be decided by whichever interval
    # happens to be written over the largest denominator.  ``None`` is left
    # here deliberately rather than a subspace invented for the occasion:
    # the harmony study reads intervals through their prime exponents, and
    # says so in ``reasoning/harmony.tuning_vector``.
    "harmonics": None,
    # As of v1.7.0, and for the same reason as ``harmonics``.  A price
    # carrier holds two magnitude buckets and two mantissas beside ten
    # dimensional exponents, and the mantissas dominate a raw difference,
    # so ``None`` is left here rather than a subspace invented for the
    # occasion: the economics study reads prices through the whole vector
    # and says so in ``reasoning/economics.price_vector``.
    "economics": None,
}


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
# 3.  THE SESSION
# ===========================================================================

class GeometricSession(SubstrateReports, LatticeGeometryReports,
                       RegisterReports, ResolutionReports,
                       SignalReports, LedgerReports,
                       SemanticsReports, MigrationReports,
                       DevelopmentReports, RecipeReports,
                       LanguageReports, ReasoningReports):
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
        elif domain == "harmonics":
            loaded = do.harmonic_objects()
        elif domain == "economics":
            loaded = do.economics_objects()
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
            # v1.5.0: a measure word read against a comparison class -- the
            # only query kind whose answer is a magnitude derived from two
            # registers at once, and whose refusals are register boundaries.
            "measure": self._solve_measure,        # uses mvw.read, mvw.classify
            # v1.9.0: the comparative form of the same reading -- a relation
            # between two *uses*, which the words alone do not decide across
            # comparison classes.
            "comparative": self._solve_comparative,  # uses mvw.answer_comparative
            # v1.11.0: one coordinate of one object, answered off the domain
            # descriptions themselves -- the only query kind that holds no
            # rule of its own, and whose refusals are a description's
            # boundary rather than a register's.
            "derive": self._solve_derive,          # uses rcp.ask
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
        elif obj.domain == "harmonics":
            attrs = obj.attributes or {}
            error = attrs.get("tet_error")
            detail = (
                f"The interval {attrs.get('numerator')}/"
                f"{attrs.get('denominator')}, exactly: a "
                f"{attrs.get('prime_limit')}-limit ratio of Euler gradus "
                f"{attrs.get('euler_gradus')} and Tenney height "
                f"{attrs.get('product_complexity')}.  The nearest "
                f"12-tone equal step is {attrs.get('tet_step')}, decided by "
                f"integer comparison rather than by a logarithm, and "
                + ("that step is the interval itself."
                   if error == 1 else
                   f"equal temperament misses it by {error}, which is not "
                   f"1 and -- by "
                   f"RequestProject/GLM/Harmony.lean -- never can be."))
        elif obj.domain == "economics":
            attrs = obj.attributes or {}
            detail = (
                f"The quoted price {attrs.get('price')} of "
                f"{attrs.get('priced_quantity')} in "
                f"{attrs.get('quoting_unit')}, as an exact rational.  Its "
                f"base-2 magnitude bucket is {obj.carrier[2]} and its "
                f"base-10 bucket {obj.carrier[3]}, each the unique integer "
                f"k with base^k <= price < base^(k+1), decided by integer "
                f"comparison rather than by a logarithm and proved unique "
                f"in RequestProject/GLM/LogBucket.lean.  Source: "
                f"{attrs.get('reference_source')}, retrieved "
                f"{attrs.get('retrieval_date')}.")
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
                     "attributes": jsonable(obj.attributes),
                     **lattice_payload})

    # ------------------------------------------------------------------
    # 3d.  nearest -- ranking under the Griess metric
    # ------------------------------------------------------------------

    def _solve_nearest(self, query: Query) -> Solution:
        if not query.operands:
            raise SolverError("nearest: no reference concept named")
        obj, formula = self._resolve_or_parse_molecule(query.operands[0],
                                                       query.domain)
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
                 (f"Take {obj.name} from the {domain} register as the query "
                  f"point.") if formula is None else
                 (f"{query.operands[0]!r} names no carrier in the register, "
                  f"so it is read as a chemical formula: parsed into an "
                  f"exact composition and encoded into the same 24 "
                  f"coordinates a registered molecule uses, with every "
                  f"coordinate derived from the element register."),
                 f"query = {obj.name} in Q^24"
                 + ("" if formula is None else
                    f", built from the formula {formula!r}: "
                    f"{obj.attributes['composition']}, "
                    f"charge {obj.attributes['charge']}")),
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
                                  "limit": limit, "subspace": subspace,
                                  "formula": formula}},
            payload={"ranked": [[n, q(d)] for n, d in top],
                     "pool_size": len(pool), "subspace": subspace,
                     "formula": formula,
                     "unregistered": formula is not None})

    def _resolve_or_parse_molecule(
            self, surface: str,
            domain: Optional[str] = None) -> Tuple[DataObject, Optional[str]]:
        """Resolve a surface form, falling back to the formula parser.

        The register enumerates 51 molecules and a formula names indefinitely
        many, so an operand that no register knows is offered to the molecule
        formula parser before the query is refused.  Returns the carrier and,
        when it was built rather than looked up, the formula it was built
        from.
        """
        try:
            return self.resolve(surface, domain), None
        except SolverError:
            if domain is not None and domain != "molecules":
                raise
            try:
                obj = do.object_from_formula(surface)
            except (do.FormulaError, ValueError, KeyError):
                raise SolverError(
                    f"resolve: {surface!r} names no carrier in "
                    f"{domain or 'any enabled domain'}, and does not parse "
                    f"as a chemical formula either") from None
            return obj, surface

    @staticmethod
    def _formula_steps(built: Sequence[Tuple[str, DataObject,
                                             Optional[str]]]) -> List[Step]:
        """One step for each operand that had to be built from a formula.

        ``built`` holds ``(surface, object, formula)`` triples as returned by
        :meth:`_resolve_or_parse_molecule`; the entries whose formula is
        ``None`` were register look-ups and say nothing here.
        """
        steps: List[Step] = []
        for surface, obj, formula in built:
            if formula is None:
                continue
            steps.append(Step(
                f"carrier_{obj.name}",
                f"{surface!r} names no carrier in the register, so it is "
                f"read as a chemical formula: parsed into an exact "
                f"composition and encoded into the same 24 coordinates a "
                f"registered molecule uses, with every coordinate derived "
                f"from the element register.",
                f"{obj.name} built from the formula {formula!r}: "
                f"{obj.attributes['composition']}, "
                f"charge {obj.attributes['charge']}"))
        return steps

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
        resolved = [self._resolve_or_parse_molecule(name, query.domain)
                    for name in query.operands]
        objs = [obj for obj, _formula in resolved]
        formulas = [formula for _obj, formula in resolved]
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

        built = [labels[i] for i, f in enumerate(formulas) if f is not None]
        steps = [
            Step("carriers",
                 f"Cluster {len(labels)} carriers from the {domains[0]} "
                 f"register: {labels}."
                 + ("" if not built else
                    f"  {len(built)} of them name no register entry and are "
                    f"built from their chemical formulae instead, every "
                    f"coordinate derived from the element register: "
                    f"{built}."),
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
                                  "k": k, "linkage": linkage,
                                  "formulas": formulas}},
            payload={"dendrogram": tree.as_dict(),
                     "formulas": formulas,
                     "unregistered": built})

    # ------------------------------------------------------------------
    # 3g.  spatial -- the MOG presentation of a carrier
    # ------------------------------------------------------------------

    def _solve_spatial(self, query: Query) -> Solution:
        if not query.operands:
            raise SolverError("spatial: no carrier named")
        obj, formula = self._resolve_or_parse_molecule(query.operands[0],
                                                       query.domain)
        stack = obj.stack()
        plane0 = stack.planes[0]
        grid = mog.frame(plane0)
        cube = mog.cube_profile(plane0)
        signature = obj.facet_signature()
        touched = sorted(k for k, w in signature.items() if w)
        codeword, distance, count = an.nearest_golay_codeword(plane0)

        steps = [
            Step("carrier",
                 (f"Take {obj.name} from the {obj.domain} register and read "
                  f"its digit plane 0 as a 24-bit mask.") if formula is None
                 else
                 (f"{query.operands[0]!r} names no carrier in the register, "
                  f"so it is read as a chemical formula and encoded into the "
                  f"same 24 coordinates a registered molecule uses; its "
                  f"digit plane 0 is then read as a 24-bit mask."),
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
                         "args": {"domain": obj.domain, "name": obj.name,
                                  "formula": formula}},
            payload={"facet_signature": signature,
                     "cube_profile": cube,
                     "grid": [[int(b) for b in row] for row in grid],
                     "formula": formula,
                     "unregistered": formula is not None})

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
        a, formula_a = self._resolve_or_parse_molecule(query.operands[0],
                                                       query.domain)
        b, formula_b = self._resolve_or_parse_molecule(query.operands[1],
                                                       query.domain)
        # Walk every layer from substrate up to universal.
        result = dl.escalate(a.carrier, b.carrier, start=0)
        all_views = result["all_views"]
        final_layer = result["layer"]

        steps = self._formula_steps(
            ((query.operands[0], a, formula_a),
             (query.operands[1], b, formula_b))) + [
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
                                  "domain_b": b.domain, "name_b": b.name,
                                  "formula_a": formula_a,
                                  "formula_b": formula_b}},
            payload={"all_views": [(name, str(va), str(vb), str(d))
                                    for name, va, vb, d in all_views],
                     "final_layer": final_layer.name,
                     "formula_a": formula_a, "formula_b": formula_b,
                     "unregistered": [n for n, f in
                                      ((a.name, formula_a), (b.name, formula_b))
                                      if f is not None]})

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
        # v1.4.0: the coherence solver takes a carrier and nothing else, so
        # an operand no register enumerates is offered to the molecule
        # formula parser before the query is refused -- the same
        # fall-through `nearest` and `describe` already had.
        obj, formula = self._resolve_or_parse_molecule(query.operands[0],
                                                       query.domain)
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

        steps = self._formula_steps(
            ((query.operands[0], obj, formula),)) + [
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
                         "args": {"domain": obj.domain, "name": obj.name,
                                  "formula": formula}},
            payload={"breakdown": {k: _render_shell(v)
                                    for k, v in breakdown.items()},
                     "regime": regime,
                     "formula": formula,
                     "unregistered": formula is not None})

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
        if subject in ("blueprint", "unification blueprint", "claims",
                         "claim ledger", "ledger", "audit"):
            return self._report_blueprint(query)
        if subject in ("reversible", "reversibility", "gray", "gray code",
                         "toffoli", "fredkin", "solitons", "kinks"):
            return self._report_reversible(query)
        if subject in ("mantissa", "ptb", "aoo", "float", "floats",
                         "metrology", "ieee754", "ieee-754"):
            return self._report_mantissa(query)
        if subject in ("engine", "tdce", "carrier engine", "gearbox",
                         "radiator", "turbocharger", "multi-fuel"):
            return self._report_engine(query)
        if subject in ("noise", "wobble", "wiggle", "dither", "cascade",
                         "noise lab", "noise_lab"):
            return self._report_noise(query)
        if subject in ("lattices", "lattice", "higher lattices",
                         "higher_lattices", "barnes-wall", "barnes wall",
                         "32", "48", "extremal", "ladder"):
            return self._report_lattices(query)
        if subject in ("shells", "shell", "shell sigma", "shell_sigma",
                         "gibbs", "leech noise", "leech sigma",
                         "lattice alphabet"):
            return self._report_shells(query)
        if subject in ("llvq", "llvq table", "llvq_table", "lookup table",
                         "quantiser", "quantizer", "class table",
                         "hexacode"):
            return self._report_llvq(query)
        if subject in ("harmony", "harmonics", "music", "intervals",
                         "tuning", "temperament", "consonance"):
            return self._report_harmony(query)
        if subject in ("economics", "economic", "prices", "price",
                         "market", "markets", "price discovery"):
            return self._report_economics(query)
        if subject in ("escalation", "escalation at scale", "at scale",
                         "scale", "registers", "ceiling", "resolution"):
            return self._report_escalation(query)
        if subject in ("names", "name", "name coordinate", "name_coordinate",
                         "naming", "resolution ceiling"):
            return self._report_names(query)
        if subject in ("measure", "measure words", "measure view",
                         "relative measure", "comparison classes",
                         "comparison class", "scales",
                         "denotation", "denotations", "residue",
                         "related_to", "vocabulary"):
            return self._report_measure(query)
        if subject in ("recipe", "recipes", "descriptions", "description",
                         "domain description", "domain descriptions",
                         "regeneration", "generic path"):
            return self._report_recipe(query)
        if subject in ("language", "question", "questions",
                         "question shapes", "question shape", "surface",
                         "surface language", "phrasing", "phrasings"):
            return self._report_language(query)
        if subject in ("searchloop", "search loop", "search_loop",
                         "hard gate", "gate", "reasoning loop",
                         "candidate filter"):
            return self._report_searchloop(query)
        if subject in ("retrieval", "retrieve", "address retrieval",
                         "nearest declarations", "index", "address index",
                         "search"):
            return self._report_retrieval(query)
        if subject in ("controller", "loop", "derivation", "derivations",
                         "propose", "plan", "planner"):
            return self._report_controller(query)
        if subject in ("lean", "lean addresses", "lean address",
                         "declarations", "address book", "addresses"):
            return self._report_lean(query)
        if subject in ("directives", "directive", "standing orders",
                         "rules", "working practice"):
            return self._report_directives(query)
        if subject in ("pipeline", "stages", "study pipeline",
                         "readiness", "board"):
            return self._report_pipeline(query)
        if subject in ("signature", "spectral", "spectral signature",
                         "wobble signature", "sturmian", "resonance",
                         "oscillator", "snr"):
            return self._report_signature(query)
        if subject in ("drift", "iteration drift", "prime drift",
                         "orbit drift", "divergence", "drift ladder"):
            return self._report_drift(query)
        if subject in ("catalog", "catalogue", "study catalog",
                         "study catalogue", "findings", "study findings",
                         "external studies"):
            return self._report_catalog(query)
        if subject in ("containers", "container", "generators",
                         "generators and containers", "hull census",
                         "convergence"):
            return self._report_containers(query)
        if subject in ("companion", "companion studies", "companion study",
                         "preprints", "iteration study", "lattice survey"):
            return self._report_companion(query)
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
        a, formula_a = self._resolve_or_parse_molecule(query.operands[0],
                                                       query.domain)
        b, formula_b = self._resolve_or_parse_molecule(query.operands[1],
                                                       query.domain)
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
        steps = self._formula_steps(
            ((query.operands[0], a, formula_a),
             (query.operands[1], b, formula_b))) + [
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
                                  "domain_b": b.domain, "name_b": b.name,
                                  "formula_a": formula_a,
                                  "formula_b": formula_b}},
            payload={"signed_cosine_squared": q(sc2),
                     "regime": regime,
                     "formula_a": formula_a, "formula_b": formula_b,
                     "unregistered": [n for n, f in
                                      ((a.name, formula_a), (b.name, formula_b))
                                      if f is not None]})

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


    def _solve_measure(self, query: Query) -> Solution:
        """Read a measure word against a comparison class -- or refuse.

        Three shapes, and the third is the point.  ``measure hot in tea``
        answers with an exact magnitude; ``measure 300 in tea`` answers with
        the word a magnitude earns; ``measure hot`` answers with the word read
        against every class of its quantity, which is what shows that *hot*
        is relative rather than absolute.  A word the registers cannot reach
        at all, and a word read against a class of another quantity --
        ``measure large in room``, where *room* brackets a length and
        ``large`` measures a volume -- are **refused with the reason**,
        because ``GLM.Info.boundary_empty_of_unmeasured`` says the widened
        view gains nothing there: there is no measurement to report, and
        inventing one would be inventing a coordinate.
        """
        subject = str(query.options.get("subject", "")).strip()
        klass = str(query.options.get("class", "")).strip()
        if not subject:
            raise SolverError(
                "measure: nothing to measure.  Try 'measure hot in tea'")

        magnitude = as_magnitude(subject)
        try:
            if magnitude is not None:
                if not klass:
                    raise SolverError(
                        f"measure: a magnitude needs a comparison class -- "
                        f"try 'measure {subject} in tea'")
                return self._measure_from_magnitude(query, magnitude, klass)
            if klass:
                return self._measure_from_word(query, subject, klass)
            return self._measure_across_classes(query, subject)
        except mvw.MeasureBoundary as boundary:
            raise SolverError(f"measure: {boundary}") from None
        except KeyError as error:
            raise SolverError(f"measure: {error}") from None

    def _measure_from_word(self, query: Query, word: str,
                           klass: str) -> Solution:
        """``measure hot in tea`` -- the word, as a magnitude."""
        reading = mvw.read(word, klass)
        entry = mvw.word_by_name(word)
        named = mvw.lexicon_quantity(word)
        relations = mvw.measure_relations(word)
        above = mvw.above_on(word)
        others = [mvw.read(word, c.name)
                  for c in do.classes_for_quantity(reading.quantity)
                  if c.name != klass]
        steps = [
            Step("the quantity is not new information",
                 f"The lexicon already says {word} is `property_of "
                 f"{named or reading.quantity}`"
                 + (f", which the register calls {reading.quantity} -- an "
                    f"alias resolves the two names and supplies no "
                    f"coordinate" if named and named != reading.quantity
                    else "") +
                 f", and the physics register already "
                 f"holds {reading.quantity} with dimension "
                 f"{reading.dimension} in {reading.unit}.  Neither is typed "
                 f"twice here: both are read back out of the registers.",
                 f"{word} measures {reading.quantity} "
                 f"[{reading.dimension}], unit {reading.unit}"
                 + (f", lexicon name {named}"
                    if named and named != reading.quantity else "")),
            Step("the class supplies the bracket",
                 f"A comparison class is an exact bracket on the quantity, "
                 f"and it is the only new datum in the answer: "
                 f"{klass} runs from {q(reading.low)} to {q(reading.high)} "
                 f"{reading.unit}.",
                 f"{klass}: [{q(reading.low)}, {q(reading.high)}] "
                 f"{reading.unit}"),
            Step("the word supplies the position",
                 f"{word} sits at {q(reading.position)} of the "
                 f"{reading.quantity} scale, above {list(above) or 'nothing'} "
                 f"and below the rest of it.  The position is exact and the "
                 f"order is the `above_on` relation.",
                 f"position {q(reading.position)}; above_on "
                 f"{list(above)}"),
            Step("the magnitude is the two together",
                 f"low + position * (high - low), in exact rationals and "
                 f"with no float constructed: "
                 f"{q(reading.low)} + {q(reading.position)} * "
                 f"({q(reading.high)} - {q(reading.low)}) = "
                 f"{q(reading.magnitude)} {reading.unit}.",
                 f"{word} in {klass} = {q(reading.magnitude)} "
                 f"{reading.unit}"),
            Step("the same word, measured elsewhere",
                 f"The measurement is relative, and this is what that means: "
                 f"the same word against the other classes of "
                 f"{reading.quantity} names quite different magnitudes.",
                 "; ".join(f"{o.comparison_class} {q(o.magnitude)} {o.unit}"
                           for o in others) or "no other class"),
            Step("what the static reading could not say",
                 f"The concept carrier is the same for every use of {word}: "
                 f"`GLM.Info.staticLayer_conflates_hot_uses` is that as a "
                 f"theorem, and `GLM.Info.measureLayer_separates_hot_uses` "
                 f"is the widened view telling them apart.  The relative "
                 f"reading is added beside the static one, never in place of "
                 f"it -- `GLM.Info.measureLayer_refines_staticLayer`.",
                 f"derived relations: "
                 + "; ".join(f"{p} {o}" for p, o in relations[:4]) + " ..."),
        ]
        expected = {
            "word": word,
            "comparison_class": klass,
            "quantity": reading.quantity,
            "unit": reading.unit,
            "dimension": reading.dimension,
            "position": q(reading.position),
            "magnitude": q(reading.magnitude),
            "low": q(reading.low),
            "high": q(reading.high),
            "above_on": ",".join(above),
            "status": entry.status,
            "other_classes": ",".join(
                f"{o.comparison_class}:{q(o.magnitude)}" for o in others),
        }
        return Solution(
            query=query, kind="measure",
            answer=f"{word} in {klass}: {q(reading.magnitude)} "
                   f"{reading.unit} -- the {reading.quantity} scale puts "
                   f"{word} at {q(reading.position)} of the class bracket "
                   f"[{q(reading.low)}, {q(reading.high)}] {reading.unit}, "
                   f"and the same word against "
                   + ", ".join(f"{o.comparison_class} is {q(o.magnitude)} "
                               f"{o.unit}" for o in others[:2])
                   + f"; the measurement is exact and the static concept "
                     f"carrier is unchanged by it",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "measure",
                         "args": {"word": word, "klass": klass}},
            payload={"reading": jsonable(reading.as_dict()),
                     "relations": [list(r) for r in relations]})

    def _measure_from_magnitude(self, query: Query, magnitude: Fraction,
                                klass: str) -> Solution:
        """``measure 300 in tea`` -- the magnitude, as a word."""
        verdict = mvw.classify(magnitude, klass)
        word = str(verdict["word"])
        steps = [
            Step("the class is read from the register",
                 f"{klass} brackets {verdict['quantity']} between "
                 f"{q(verdict['bracket'][0])} and "
                 f"{q(verdict['bracket'][1])} {verdict['unit']}.",
                 f"bracket [{q(verdict['bracket'][0])}, "
                 f"{q(verdict['bracket'][1])}] {verdict['unit']}"),
            Step("the magnitude is placed exactly",
                 f"(magnitude - low) / (high - low), in exact rationals: "
                 f"{q(magnitude)} sits at {q(verdict['position'])} of the "
                 f"class, and it is "
                 f"{'inside' if verdict['inside_bracket'] else 'outside'} "
                 f"the bracket.  A value outside is reported as outside "
                 f"rather than clamped: the class is a claim about ordinary "
                 f"cases.",
                 f"position {q(verdict['position'])}, inside "
                 f"{verdict['inside_bracket']}"),
            Step("the nearest scale word",
                 f"The {verdict['quantity']} scale is an ordered family of "
                 f"degree words with exact positions, and the nearest to "
                 f"{q(verdict['position'])} is {word} at "
                 f"{q(verdict['word_position'])}.  Above it on the same "
                 f"scale: {list(verdict['above'])}.",
                 f"{word} at {q(verdict['word_position'])}; above "
                 f"{list(verdict['above'])}"),
        ]
        expected = {
            "magnitude": q(magnitude),
            "comparison_class": klass,
            "quantity": str(verdict["quantity"]),
            "unit": str(verdict["unit"]),
            "position": q(verdict["position"]),
            "inside_bracket": str(verdict["inside_bracket"]),
            "word": word,
            "word_position": q(verdict["word_position"]),
            "above": ",".join(verdict["above"]),
        }
        return Solution(
            query=query, kind="measure",
            answer=f"{q(magnitude)} {verdict['unit']} in {klass}: "
                   f"{word} -- it sits at {q(verdict['position'])} of the "
                   f"class bracket, "
                   f"{'inside' if verdict['inside_bracket'] else 'outside'} "
                   f"it, and the words above it on the "
                   f"{verdict['quantity']} scale are "
                   f"{list(verdict['above'])}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "measure_magnitude",
                         "args": {"magnitude": str(magnitude),
                                  "klass": klass}},
            payload={"verdict": jsonable(verdict)})

    def _measure_across_classes(self, query: Query, word: str) -> Solution:
        """``measure hot`` -- the word against every class of its quantity."""
        entry = mvw.word_by_name(word)
        if not entry.scaled or entry.quantity is None:
            raise mvw.MeasureBoundary(
                f"{word!r} has no measure reading: {entry.reason}",
                reason=entry.status)
        readings = [mvw.read(word, c.name)
                    for c in do.classes_for_quantity(entry.quantity)]
        low = min(readings, key=lambda r: r.magnitude)
        high = max(readings, key=lambda r: r.magnitude)
        steps = [
            Step("one word, one position, many magnitudes",
                 f"{word} is at {q(entry.position)} of the "
                 f"{entry.quantity} scale in every class alike; what changes "
                 f"is the bracket the position is read against.",
                 "; ".join(f"{r.comparison_class} {q(r.magnitude)} {r.unit}"
                           for r in readings)),
            Step("the spread is the answer",
                 f"Between {low.comparison_class} and "
                 f"{high.comparison_class} the same word names magnitudes "
                 f"differing by a factor of "
                 f"{q(high.magnitude / low.magnitude)}.  No layer of the "
                 f"carrier stack could have said this, because the concept "
                 f"carrier is identical across the uses.",
                 f"{q(low.magnitude)} .. {q(high.magnitude)} {low.unit}, "
                 f"ratio {q(high.magnitude / low.magnitude)}"),
        ]
        expected = {
            "word": word,
            "quantity": str(entry.quantity),
            "position": q(entry.position),
            "classes": ",".join(r.comparison_class for r in readings),
            "magnitudes": ",".join(q(r.magnitude) for r in readings),
            "lowest": low.comparison_class,
            "highest": high.comparison_class,
            "ratio": q(high.magnitude / low.magnitude),
        }
        return Solution(
            query=query, kind="measure",
            answer=f"{word} measures {entry.quantity} at "
                   f"{q(entry.position)} of its scale, which against the "
                   f"{len(readings)} classes the register holds is "
                   + ", ".join(f"{r.comparison_class} {q(r.magnitude)} "
                               f"{r.unit}" for r in readings)
                   + f" -- a spread of "
                     f"{q(high.magnitude / low.magnitude)} between "
                     f"{low.comparison_class} and {high.comparison_class}",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "measure_word", "args": {"word": word}},
            payload={"readings": [jsonable(r.as_dict()) for r in readings]})

    # ------------------------------------------------------------------
    # 3z.  comparative -- *hotter than*, *as hot as*, between two uses
    # ------------------------------------------------------------------

    def _solve_comparative(self, query: Query) -> Solution:
        """Decide a comparative between two measured uses -- or refuse.

        ``is cold in stellar_surface hotter than hot in tea`` is **true**:
        8000 K against 363 K, although *cold* sits below *hot* on the scale.
        That is the whole point of the query kind -- a comparative is a
        relation between two *uses*, and the words alone do not decide it
        across comparison classes (``GLM.Info.comparative_not_static``,
        ``GLM.Info.comparative_not_determined_by_word_order``).  Within one
        class they do, exactly (``GLM.Info.hotterThan_iff_position_lt``).

        Three refusals, each a register boundary with its reason stated: a
        use the registers cannot measure, two uses of different quantities,
        and a comparative of the wrong quantity for the pair.
        """
        form = str(query.options.get("form", "")).strip()
        equative = bool(query.options.get("equative", False))
        left_word = str(query.options.get("left_word", "")).strip()
        left_class = str(query.options.get("left_class", "")).strip()
        right_word = str(query.options.get("right_word", "")).strip()
        right_class = str(query.options.get("right_class", "")).strip()
        if not (form and left_word and left_class and right_word
                and right_class):
            raise SolverError(
                "comparative: two measured uses are needed -- try 'is cold "
                "in stellar_surface hotter than hot in tea'")
        try:
            verdict = mvw.answer_comparative(
                form, left_word, left_class, right_word, right_class,
                equative=equative)
        except mvw.MeasureBoundary as boundary:
            raise SolverError(f"comparative: {boundary}") from None
        except KeyError as error:
            raise SolverError(f"comparative: {error}") from None

        comparison = verdict["comparison"]
        left, right = comparison.left, comparison.right
        audit = mvw.comparative_audit()
        cross = audit["cross_class"]
        same = audit["same_class"]
        marker = (f"as {verdict['stem']} as" if equative
                  else f"{form} than")
        steps = [
            Step("each side is read as an exact magnitude",
                 f"A comparative is a relation between two *uses*, so both "
                 f"sides are read first: {left_word} in {left_class} is "
                 f"{q(left.magnitude)} {left.unit} and {right_word} in "
                 f"{right_class} is {q(right.magnitude)} {right.unit}, each "
                 f"low + position * (high - low) in exact rationals.",
                 f"{q(left.magnitude)} {left.unit} vs "
                 f"{q(right.magnitude)} {right.unit}"),
            Step("the marker's direction is read off the register",
                 f"{marker!r} is built from the degree word "
                 f"{verdict['stem']!r}, which the register puts at "
                 f"{q(mvw.word_by_name(str(verdict['stem'])).position)} "
                 f"of the {verdict['quantity']} scale"
                 + (", and an equative asserts equality of magnitudes"
                    if equative else
                    f", above the midpoint, so it asserts the greater "
                    f"magnitude" if verdict["direction"] == "greater" else
                    f", below the midpoint, so it asserts the smaller "
                    f"magnitude") +
                 f".  A word exactly at the midpoint names no direction and "
                 f"the query refuses rather than guessing one.",
                 f"stem {verdict['stem']}, direction "
                 f"{verdict['direction']}"),
            Step("the comparison is exact",
                 f"{q(left.magnitude)} - {q(right.magnitude)} = "
                 f"{q(verdict['difference'])} {left.unit}"
                 + (f", a ratio of {q(verdict['ratio'])}"
                    if verdict["ratio"] is not None else "") +
                 f".  No float is constructed, and the trichotomy is the "
                 f"one `GLM.Info.hotterThan_trichotomy` proves: greater, "
                 f"equal or less, and exactly one of them.",
                 f"order {verdict['order']}, claim "
                 f"{'holds' if verdict['holds'] else 'fails'}"),
            Step("what the words alone would have said",
                 f"On the scale, {left_word} is at {q(left.position)} and "
                 f"{right_word} at {q(right.position)}, which orders them "
                 f"{verdict['word_order']}; the magnitudes order them "
                 f"{verdict['order']}.  "
                 + ("The two agree here."
                    if verdict["word_order"] == verdict["order"] else
                    "They disagree -- the class is load-bearing, and a "
                    "reading of the two concepts alone would have answered "
                    "this backwards."),
                 f"word order {verdict['word_order']}, magnitude order "
                 f"{verdict['order']}"),
            Step("how often that happens, measured",
                 f"Over the {audit['uses']} measured uses the registers "
                 f"admit, {audit['comparable_pairs']} pairs share a "
                 f"quantity and are comparable.  Within one class the word "
                 f"order decides every one of the {same['pairs']} pairs -- "
                 f"which `GLM.Info.hotterThan_iff_position_lt` proves it "
                 f"must -- and across classes it gets "
                 f"{cross['disagree']} of {cross['pairs']} backwards.",
                 f"same class {same['disagree']}/{same['pairs']} "
                 f"disagree; cross class {cross['disagree']}/"
                 f"{cross['pairs']}"),
        ]
        expected = {
            "form": form,
            "stem": str(verdict["stem"]),
            "equative": str(equative),
            "direction": str(verdict["direction"]),
            "quantity": str(verdict["quantity"]),
            "unit": str(verdict["unit"]),
            "left_magnitude": q(left.magnitude),
            "right_magnitude": q(right.magnitude),
            "difference": q(verdict["difference"]),
            "order": str(verdict["order"]),
            "word_order": str(verdict["word_order"]),
            "holds": str(verdict["holds"]),
            "same_class_disagree": str(same["disagree"]),
            "cross_class_disagree": str(cross["disagree"]),
            "cross_class_pairs": str(cross["pairs"]),
        }
        return Solution(
            query=query, kind="comparative",
            answer=f"{'Yes' if verdict['holds'] else 'No'}: "
                   f"{verdict['claim']} is "
                   f"{'true' if verdict['holds'] else 'false'} -- "
                   f"{left_word} in {left_class} is {q(left.magnitude)} "
                   f"{left.unit} and {right_word} in {right_class} is "
                   f"{q(right.magnitude)} {right.unit}"
                   + ("; the scale order of the two words agrees with the "
                      "magnitudes here"
                      if verdict["word_order"] == verdict["order"] else
                      "; the scale order of the two words disagrees with "
                      "the magnitudes, so the comparison class decides it"),
            steps=tuple(steps), expected=expected,
            script_spec={"template": "comparative",
                         "args": {"form": form,
                                  "equative": equative,
                                  "left_word": left_word,
                                  "left_class": left_class,
                                  "right_word": right_word,
                                  "right_class": right_class}},
            payload={"comparison": jsonable(comparison.as_dict()),
                     "holds": bool(verdict["holds"]),
                     "audit": {"uses": audit["uses"],
                               "comparable_pairs": audit["comparable_pairs"],
                               "same_class_pairs": same["pairs"],
                               "same_class_disagree": same["disagree"],
                               "cross_class_pairs": cross["pairs"],
                               "cross_class_disagree": cross["disagree"]}})


    # -- v1.11.0: the recipe made into an object -------------------------

    def _solve_derive(self, query: Query) -> Solution:
        """``derive span_ratio of tea`` -- one coordinate, off a description.

        The answering path knows no domain: it asks the descriptions in
        :mod:`glm_universal.recipe.descriptions` which of them derives the
        coordinate, and that description answers.  A coordinate no
        description derives is **refused with the reason**, which is
        ``GLM.Recipe.Spec.answer_eq_none_iff``: the answerable coordinates are
        exactly the described ones, so there is nothing to guess at.
        """
        coordinate = str(query.options.get("coordinate", "")).strip()
        target = str(query.options.get("object", "")).strip()
        named = str(query.options.get("domain", "")).strip() or None
        if not coordinate or not target:
            raise SolverError("derive: name a coordinate and an object, "
                              "e.g. 'derive span_ratio of tea'")
        try:
            result = rcp.ask(coordinate, target, named)
        except KeyError as error:
            raise SolverError(f"derive: {error}") from None
        if not result["answered"]:
            raise SolverError(f"derive: {result['reason']}")

        spec = rcp.description_by_name(str(result["domain"]))
        value = result["value"]
        rendered = q(value) if isinstance(value, Fraction) else str(value)
        steps = [
            Step("the coordinate is looked up in the descriptions",
                 f"Nothing in the answering path knows what "
                 f"{result['domain']} is about.  The described domains are "
                 f"{', '.join(rcp.described_domains())}, and "
                 f"{result['domain']} is the one whose description derives "
                 f"{coordinate!r}.",
                 f"{coordinate} is coordinate "
                 f"{spec.layout.index(coordinate)} of "
                 f"{len(spec.coordinates)} in the {spec.name} description"),
            Step("the rule says what it derives from",
                 f"A description states, for every coordinate, the rule that "
                 f"computes it and the held quantity it comes from -- which "
                 f"is what makes *nothing dimensional is typed twice* "
                 f"checkable rather than aspirational.",
                 f"{coordinate} = {result['rule']}, from {result['source']} "
                 f"({result['kind']})"),
            Step("the value, exactly",
                 f"Computed from {target}'s held facts by the rule above; "
                 f"the value is an integer or an exact rational and no float "
                 f"is constructed anywhere on the path.",
                 f"{coordinate} of {target} = {rendered}"),
            Step("what would be refused instead",
                 f"The same surface would refuse a coordinate no description "
                 f"derives -- there is no `cents` in the harmonic "
                 f"description, because a cent is a logarithm -- and "
                 f"`GLM.Recipe.Spec.answer_eq_none_iff` says that boundary "
                 f"is exactly the undescribed coordinates.  The {spec.name} "
                 f"description keeps witnesses for it.",
                 f"refused for {spec.name}: {', '.join(spec.refuses)}"),
        ]
        expected = {
            "domain": str(result["domain"]),
            "coordinate": coordinate,
            "object": target,
            "value": rendered,
            "kind": str(result["kind"]),
            "rule": str(result["rule"]),
            "index": str(spec.layout.index(coordinate)),
        }
        return Solution(
            query=query, kind="derive",
            answer=f"{coordinate} of {target} = {rendered} -- derived by "
                   f"{result['rule']} from {result['source']}, in the "
                   f"{result['domain']} description ({result['kind']}); the "
                   f"answering path holds no rule of its own, only the "
                   f"description",
            steps=tuple(steps), expected=expected,
            script_spec={"template": "derive",
                         "args": {"coordinate": coordinate,
                                  "object": target,
                                  "domain": str(result["domain"])}},
            payload={"answer": {k: (q(v) if isinstance(v, Fraction) else v)
                                for k, v in result.items()}})


# Keep a module-level reference so the digit-stack import is not flagged as
# unused; the stack constants document the substrate this session sits on.
_STACK_FACETS: int = len(ds.FACETS)

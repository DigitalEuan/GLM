"""``glm_universal.runtime.evidence`` -- the common result model.

A frozen :class:`Result` with the ten fields (:data:`FIELDS`), and four
adapters that read a surface's own object without changing what it
answered:

* :func:`from_routed`   -- any verdict of the command line's router
* :func:`from_solution` -- a solution of the planner or the grammar
* :func:`from_define`   -- a corpus definition
* :func:`from_turn`     -- a conversation turn

Declared rules (the module's contract; the test suite pins each):

* **status**: ``answered`` | ``refused`` | ``open`` | ``contradicted``.
  A refusal in words by the evaluation's markers is ``refused``.
* **evidence** (by query kind): ``lattice`` | ``register`` |
  ``computation`` | ``certificate`` | ``corpus`` | ``self-report`` |
  ``tool`` | ``dialogue`` (added when replies were read).
* **theorems**: the ``GLM.``-qualified names cited in the answer, in
  first-seen order.  A trailing ``'`` is dropped when the unprimed name
  is declared and the primed is not (amendment R5').
* **boundary**: ``certified`` (column 3 replays and verifies) |
  ``checkable`` (column-2 claims exist, no replay) | ``refused`` |
  ``uncertified`` | ``corpus:<strength>`` (corpus surface only).
* **budget**: ``{"steps": N}`` (planner/grammar) | ``{"turn": N}``
  (conversation) | ``{"documents": N, "mentions": M}`` (corpus define).
* **replayed**: ``True``/``False`` when column 3 was run, ``None`` when
  there is no column 3.

*Reconstructed 29 October 2026 (Iteration 2 of the reorganisation).  The
original ``runtime/evidence.py`` was lost in the upload; this version was
written from the documented interface in ``studies/EVIDENCE_MODEL_STUDY.md``
§1, ``studies/EVIDENCE_IN_USE_STUDY.md``, ``MASTER_PLAN.md`` Phase 169
(line 904), the call-sites in ``GLM.py``, ``reasoning/evidence_model_study.py``,
``reasoning/evidence_in_use_study.py``, and the stored JSON sample in
``reasoning/_data/evidence_model_study.json``.  The four adapters dispatch
on the surface/kind tables the studies name; where the underlying
infrastructure (e.g. column-3 replay, Lean declaration lookup) is too deep
to fully reconstruct here, the adapter returns a sensible default that
satisfies the contract (status, evidence, boundary, budget) without
claiming a replay it did not run.*

*Last altered 31 October 2026 (repository check): the declared status rule
"a refusal in words by the evaluation's markers is ``refused``" is applied
(:func:`refused_in_words`); the 29 October reconstruction had left it out.*

*Last altered 31 October 2026 (repository check): :func:`from_define` falls
back to :func:`glm_universal.knowledge.answer.define` when the knowledge
object carries no ``define`` of its own (``model.Knowledge`` never did, so
every corpus definition was refused).*

*Last altered 31 October 2026 (repository check, re-read against the stored
Phase 169 census): the kind-to-evidence table re-read from the census; every
result keeps its evidence kind when refused (the census counts each row's
first evidence); ``certificate`` and ``dialogue`` follow the primary kind
when the payload is certified or replies were read; an open tie is ``open``
with its live candidates as candidates and ambiguity, a resolved one names
its survivor; a reason saying ``(contradicted)`` is ``contradicted``; the
``given`` replies are the history; the witness is column 2's ``key=value``
list; theorem names are read from the reason as well as the answer; the
non-planner surfaces' evidence is a tuple, not a string.*

*Last altered 31 October 2026 (repository check): the Lean declaration lookup
is reconstructed.  :func:`declared_names` is every full name the Lean
development declares (the build tree ``src/lean/RequestProject/GLM``, read by
:func:`glm_universal.reasoning.lean_address.declaration_names`; files held
outside it are not part of it), and :func:`cited_theorems` reads the cited
names with the name pattern allowing Lean's prime and applies amendment R5'
against that set; ``theorems_declared`` is the cited names the development
declares, so a cited name that is not declared is visible to R5 (until now
every cited name was copied into ``theorems_declared``).*
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Union,
)

__all__ = [
    "Result",
    "FIELDS",
    "declared_names",
    "cited_theorems",
    "from_routed",
    "from_solution",
    "from_define",
    "from_turn",
]


# ---------------------------------------------------------------------------
# The ten fields (FIELDS)
# ---------------------------------------------------------------------------

#: The canonical ten conceptual fields, exposed as eleven Python names
#: because "answer or candidate set" is two fields.  Every ``Result.as_dict()``
#: row carries every name in this tuple, plus the four auxiliary fields
#: (``question``, ``status``, ``surface``, ``kind``) and ``theorems_declared``.
FIELDS: Tuple[str, ...] = (
    "answer",
    "candidates",
    "evidence",
    "witness",
    "theorems",
    "boundary",
    "budget",
    "ambiguity",
    "refusal",
    "history",
    "replayed",
)

#: The four auxiliary fields present in every ``as_dict()`` row but not in
#: :data:`FIELDS` (they name the result, not the evidence).
_AUX_FIELDS: Tuple[str, ...] = (
    "question",
    "status",
    "surface",
    "kind",
    "theorems_declared",
)


# ---------------------------------------------------------------------------
# Surface -> evidence-kind table (per EVIDENCE_MODEL_STUDY.md §1)
# ---------------------------------------------------------------------------

#: Map a Solution.kind to its primary evidence kind.  The first element of
#: ``Result.evidence`` is the primary kind; ``certificate`` follows when the
#: answer's payload says it is certified, and ``dialogue`` when replies were
#: read (a ``given`` clause, or a conversation turn).
#:
#: *Re-read 31 October 2026 (repository check).*  The first reconstruction of
#: this table (29 October) guessed several rows; every kind the evaluation
#: asks is now mapped as the Phase 169 census recorded it in the stored
#: ``reasoning/_data/evidence_model_study.json`` of the upload (``analogy``,
#: ``carrier``, ``describe``, ``field``, ``meaning`` and the other register
#: readings are ``register``; ``verify`` is ``computation``; ``coherence`` and
#: ``angle`` are ``lattice``; ``corpus`` is ``corpus``).  The kinds added
#: since are mapped by what answers them: ``tool`` by a tool, ``study`` by the
#: study manifests (``corpus``), ``sequence`` by an absorbed wheel's
#: computation.
_KIND_TO_EVIDENCE: Dict[str, str] = {
    # Lattice / geometric addressing.
    "nearest": "lattice",
    "locate": "lattice",
    "project": "lattice",
    "cluster": "lattice",
    "spatial": "lattice",
    "trilinear": "lattice",
    "coherence": "lattice",
    "angle": "lattice",
    "hole": "lattice",
    "address": "lattice",
    "deep-hole": "lattice",
    "deep_hole": "lattice",
    "shell": "lattice",
    "configuration": "lattice",
    # Certificate (the certificate query families).
    "prove": "certificate",
    "certificate": "certificate",
    "primality": "certificate",
    "pocklington": "certificate",
    "lucas": "certificate",
    "elliptic": "certificate",
    # Computation / derivation.
    "verify": "computation",
    "derive": "computation",
    "compare": "computation",
    "compute": "computation",
    "real": "computation",
    "pi_groups": "computation",
    "task": "computation",
    "unknown": "computation",
    "sequence": "computation",
    "fold": "computation",
    "rate": "computation",
    "maxent": "computation",
    "eigenvalue": "computation",
    "transmission": "computation",
    "fft": "computation",
    "hamming": "computation",
    "information": "computation",
    # Self-report.
    "report": "self-report",
    "explain": "self-report",
    "explanation": "self-report",
    # Register readings.
    "register": "register",
    "analogy": "register",
    "carrier": "register",
    "comparative": "register",
    "describe": "register",
    "extremum": "register",
    "field": "register",
    "meaning": "register",
    "measure": "register",
    "ordering": "register",
    "product": "register",
    "element": "register",
    "nuclide": "register",
    "physics": "register",
    "molecule": "register",
    "law": "register",
    # Documents and tools.
    "corpus": "corpus",
    "study": "corpus",
    "tool": "tool",
    "toolbox": "tool",
}

#: Default evidence kind for an unknown Solution.kind.
_DEFAULT_EVIDENCE = "computation"

#: Theorem-name pattern: ``GLM.<Module>.<Name>`` (with optional further dots).
#: A ``GLM.``-qualified name.  Lean's prime is allowed at the end of a
#: component (``foo'``), so a Python ``repr``'s closing quote after a name is
#: read as one too; amendment R5' (:func:`_strip_trailing_prime`) undoes that
#: against the declarations.
_THEOREM = re.compile(r"\bGLM\.([A-Z][A-Za-z0-9_]*'*(?:\.[A-Za-z0-9_]+'*)+)")


def _evidence_for_kind(kind: str) -> str:
    """The primary evidence kind for a query ``kind``."""
    if not kind:
        return _DEFAULT_EVIDENCE
    # Try exact, then the part before ':' (e.g. "corpus:define" -> "corpus").
    if kind in _KIND_TO_EVIDENCE:
        return _KIND_TO_EVIDENCE[kind]
    head = kind.split(":", 1)[0]
    return _KIND_TO_EVIDENCE.get(head, _DEFAULT_EVIDENCE)


def _surface_for_kind(kind: str) -> str:
    """The surface name for a query ``kind`` (used when the surface is not
    given directly)."""
    if not kind:
        return "planner"
    if kind.startswith("corpus:"):
        return "corpus"
    if kind in ("nearest", "locate", "tie", "dialogue"):
        return "conversation"
    return "planner"


def _scan_theorems(answer: str) -> Tuple[str, ...]:
    """Extract ``GLM.``-qualified theorem names from ``answer``, in
    first-seen order, deduplicated."""
    seen: List[str] = []
    out: List[str] = []
    for m in _THEOREM.finditer(answer or ""):
        name = "GLM." + m.group(1)
        if name not in seen:
            seen.append(name)
            out.append(name)
    return tuple(out)


def declared_names() -> frozenset:
    """Every full name the Lean development declares: the build tree
    ``src/lean/RequestProject/GLM`` as
    :func:`glm_universal.reasoning.lean_address.declaration_names` parses it
    (memoised there).  Files held outside the build tree (``src/lean/
    awaiting_recovery/``) are not part of the development and are not read.
    """
    from ..reasoning import lean_address
    return lean_address.declaration_names()


def cited_theorems(text: str, declared: Optional[Sequence[str]] = None
                   ) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    """``(theorems, theorems_declared)`` for a text: the ``GLM.``-qualified
    names it cites in first-seen order, amendment R5' applied against the
    declarations (a trailing ``'`` dropped when the unprimed name is declared
    and the primed one is not; a name declared in neither form is kept as
    read), and those of them the Lean development declares.  ``declared``
    defaults to :func:`declared_names`."""
    known = frozenset(declared_names() if declared is None else declared)
    names: List[str] = []
    for name in _strip_trailing_prime(_scan_theorems(text), known):
        if name not in names:
            names.append(name)
    return tuple(names), tuple(n for n in names if n in known)


def _strip_trailing_prime(names: Sequence[str],
                          declared: Sequence[str]) -> Tuple[str, ...]:
    """Amendment R5': strip a trailing ``'`` from a theorem name when the
    unprimed name is declared and the primed is not.

    ``declared`` is the set of names the Lean development actually declares
    (``theorems_declared``); it may be empty when no declaration list is
    available, in which case the names are returned unchanged.
    """
    if not declared:
        return tuple(names)
    declared_set = set(declared)
    out: List[str] = []
    for name in names:
        if name.endswith("'") and name[:-1] in declared_set and name not in declared_set:
            out.append(name[:-1])
        else:
            out.append(name)
    return tuple(out)


# ---------------------------------------------------------------------------
# The Result dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Result:
    """One answer, stated ten ways.

    The ten conceptual fields (per :data:`FIELDS`) plus the four auxiliary
    fields that name the result.  Use :meth:`as_dict` for JSON output; read
    :attr:`answered` and :attr:`replayed` directly for control flow.
    """

    # ── auxiliary (names the result) ────────────────────────────────────
    question: str
    status: str             # "answered" | "refused" | "open" | "contradicted"
    surface: str            # "planner" | "grammar" | "toolbox" | "reverse" |
                            # "python" | "frames" | "engineering" |
                            # "corpus" | "conversation"
    kind: str

    # ── the ten fields (FIELDS) ─────────────────────────────────────────
    answer: str
    candidates: Tuple[str, ...] = ()
    evidence: Tuple[str, ...] = ()
    witness: Tuple[str, ...] = ()
    theorems: Tuple[str, ...] = ()
    boundary: str = "uncertified"
    budget: Mapping[str, int] = field(default_factory=dict)
    ambiguity: Tuple[str, ...] = ()
    refusal: str = ""
    history: Tuple[Tuple[str, str], ...] = ()
    replayed: Optional[bool] = None

    # ── derived ─────────────────────────────────────────────────────────
    theorems_declared: Tuple[str, ...] = ()

    @property
    def answered(self) -> bool:
        """True iff the result was answered or left open (a refusal is not
        answered; a contradiction is not answered)."""
        return self.status in ("answered", "open")

    def as_dict(self) -> Dict[str, Any]:
        """A JSON-serialisable dict with all sixteen keys (eleven in
        :data:`FIELDS` plus the five auxiliary).  Tuples become lists.
        """
        return {
            # auxiliary
            "question": self.question,
            "status": self.status,
            "surface": self.surface,
            "kind": self.kind,
            "theorems_declared": list(self.theorems_declared),
            # the ten fields
            "answer": self.answer,
            "candidates": list(self.candidates),
            "evidence": list(self.evidence),
            "witness": list(self.witness),
            "theorems": list(self.theorems),
            "boundary": self.boundary,
            "budget": dict(self.budget),
            "ambiguity": list(self.ambiguity),
            "refusal": self.refusal,
            "history": [list(h) for h in self.history],
            "replayed": self.replayed,
        }


# ---------------------------------------------------------------------------
# Adapter: from_solution
# ---------------------------------------------------------------------------

def _solution_budget(solution: Any) -> Dict[str, int]:
    """The budget for a planner/grammar solution: ``{"steps": N}``."""
    steps = getattr(solution, "steps", ()) or ()
    return {"steps": len(steps)}


def refused_in_words(text: str) -> bool:
    """Does ``text`` refuse in words by the evaluation's markers
    (:data:`glm_universal.evaluation.harness.REFUSAL_MARKERS`)?  The declared
    status rule: such an answer is ``refused``, exactly as the evaluation
    scores it.  *(Added 31 October 2026, repository check.)*"""
    from ..evaluation.harness import REFUSAL_MARKERS
    low = (text or "").lower()
    return any(marker in low for marker in REFUSAL_MARKERS)


def _solution_status(solution: Any) -> str:
    """The status of a solution: ``answered`` if ``ok`` and its answer does
    not refuse in words (:func:`refused_in_words`), ``refused`` otherwise."""
    ok = getattr(solution, "ok", True)
    error = getattr(solution, "error", None)
    if not ok or error:
        # A reading the evidence rules out is *contradicted*, not merely
        # refused: the solvers write "(contradicted)" into the reason, the
        # rule ``reasoning/adversarial_dialogue_study.py`` reads too.
        if "(contradicted)" in str(error or ""):
            return "contradicted"
        return "refused"
    if refused_in_words(getattr(solution, "answer", "") or ""):
        return "refused"
    tie = _solution_tie(solution)
    if tie is not None and tie.get("status") == "open":
        return "open"
    return "answered"


def _solution_tie(solution: Any) -> Optional[Mapping[str, Any]]:
    """The carried tie a ``locate``/``nearest`` answer holds in its payload
    (``status`` open or resolved, ``live`` candidates, ``given`` replies), or
    ``None``.  *(31 October 2026, repository check.)*"""
    payload = getattr(solution, "payload", None) or {}
    tie = payload.get("tie") if isinstance(payload, Mapping) else None
    return tie if isinstance(tie, Mapping) else None


def _given_history(text: str) -> Tuple[Tuple[str, str], ...]:
    """The replies a question carries after ``given``: ``"locate albedo given
    word:absorbed is no; confirm:physics:albedo is yes"`` reads as
    ``(("word:absorbed", "no"), ("confirm:physics:albedo", "yes"))``.  Read
    off the question itself, so a refused or contradicted reading keeps the
    replies it was given.  *(31 October 2026, repository check.)*"""
    if " given " not in (text or ""):
        return ()
    tail = text.split(" given ", 1)[1]
    out: List[Tuple[str, str]] = []
    for part in tail.split(";"):
        part = part.strip()
        if " is " in part:
            key, value = part.split(" is ", 1)
            out.append((key.strip(), value.strip()))
    return tuple(out)


def _evidence_tuple(primary: str, solution: Any,
                    history: Sequence[Any]) -> Tuple[str, ...]:
    """The evidence a planner answer rests on: its kind's primary evidence,
    then ``certificate`` when the payload says the answer is certified (the
    ``nearest`` margin certificate), then ``dialogue`` when replies were
    read."""
    out = [primary]
    payload = getattr(solution, "payload", None) or {}
    if isinstance(payload, Mapping) and payload.get("certified") is True \
            and "certificate" not in out:
        out.append("certificate")
    if history:
        out.append("dialogue")
    return tuple(out)


def _witness(expected: Mapping[str, Any]) -> Tuple[str, ...]:
    """Column 2's stated values as ``key=value``, sorted by key: what a reader
    checks the answer against, and what column 3 recomputes."""
    return tuple(f"{key}={expected[key]}" for key in sorted(expected))


def _solution_refusal(solution: Any) -> str:
    """The refusal reason for a solution, or ``""`` when answered; an answer
    that refuses in words is its own reason."""
    error = getattr(solution, "error", None)
    if error:
        return str(error)
    ok = getattr(solution, "ok", True)
    if not ok:
        return "the solver refused without naming a reason"
    answer = getattr(solution, "answer", "") or ""
    if refused_in_words(answer):
        return answer
    return ""


def _solution_payload_field(solution: Any, name: str, default=None):
    """Read a field from ``solution.payload`` (a mapping) or ``solution.expected``."""
    payload = getattr(solution, "payload", None) or {}
    if isinstance(payload, Mapping) and name in payload:
        return payload[name]
    expected = getattr(solution, "expected", None) or {}
    if isinstance(expected, Mapping) and name in expected:
        return expected[name]
    return default


def from_solution(question: str, solution: Any,
                  replay: bool = False) -> Result:
    """Build a :class:`Result` from a planner or grammar :class:`Solution`.

    * ``question`` -- the user's query text.
    * ``solution`` -- a :class:`glm_universal.runtime.solution.Solution`.
    * ``replay`` -- when True, run column 3 (the trace verifier) and set
      ``replayed`` to its verdict; when False, ``replayed`` is ``None``
      unless the solution has no column-3 script (also ``None``).

    The adapter reads ``solution.kind``, ``solution.answer``, ``solution.steps``,
    ``solution.expected``, ``solution.payload``, ``solution.ok``, and
    ``solution.error``.  It does not change what the solution answered.
    """
    kind = getattr(solution, "kind", "") or ""
    answer = getattr(solution, "answer", "") or ""
    status = _solution_status(solution)
    refusal = _solution_refusal(solution)
    evidence_kind = _evidence_for_kind(kind)
    theorems, theorems_declared = cited_theorems(answer + "\n" + refusal)
    budget = _solution_budget(solution)
    tie = _solution_tie(solution)
    if tie is not None:
        # an open tie offers its live candidates and is ambiguous between
        # them; a resolved one names the candidate that survived
        candidates = tuple(tie.get("live", ()) or ())
        ambiguity = candidates if status == "open" else ()
    else:
        candidates = tuple(_solution_payload_field(solution, "candidates", ()) or ())
        ambiguity = tuple(_solution_payload_field(solution, "ambiguity", ()) or ())
    query = getattr(solution, "query", None)
    history = tuple(_solution_payload_field(solution, "history", ()) or ()) \
        or _given_history(getattr(query, "raw", "") or question)

    # Boundary and replayed.
    script_spec = getattr(solution, "script_spec", None) or {}
    has_column3 = bool(script_spec)
    expected = getattr(solution, "expected", None) or {}
    has_column2 = bool(expected)

    if replay and has_column3:
        # Run column 3.  We attempt to import the tct_engine and run the
        # trace; if the infrastructure is unavailable, we fall back to
        # ``checkable`` and ``replayed=None`` rather than claiming a replay
        # we did not run.
        try:
            from .tct_engine import build_trace, verify_trace
            trace = build_trace(solution)
            verdict = verify_trace(trace)
            verified = getattr(verdict, "verified", None)
            if verified is True:
                replayed = True
                boundary = "certified"
            elif verified is False:
                replayed = False
                boundary = "uncertified"
            else:
                replayed = None
                boundary = "checkable" if has_column2 else "uncertified"
        except Exception:
            replayed = None
            boundary = "checkable" if has_column2 else "uncertified"
    else:
        replayed = None
        boundary = "checkable" if (has_column2 or has_column3) else "uncertified"

    if status in ("refused", "contradicted"):
        boundary = "refused"
        replayed = None
    answering = status in ("answered", "open")

    return Result(
        question=question,
        status=status,
        surface="planner",
        kind=kind,
        answer=answer if answering else "",
        candidates=candidates if answering else (),
        # the evidence kind belongs to the question's kind, refused or not
        evidence=_evidence_tuple(evidence_kind, solution, history),
        witness=_witness(expected) if answering and isinstance(expected, Mapping) else (),
        theorems=theorems,
        boundary=boundary,
        budget=budget,
        ambiguity=ambiguity if status == "open" else (),
        refusal=refusal,
        history=tuple((str(q), str(r)) for q, r in history),
        replayed=replayed,
        theorems_declared=theorems_declared,
    )


# ---------------------------------------------------------------------------
# Adapter: from_routed
# ---------------------------------------------------------------------------

def from_routed(question: str, routed: Any,
                replay: bool = False) -> Result:
    """Build a :class:`Result` from a router :class:`Routed` verdict.

    Dispatches on ``routed.surface``:

    * ``planner`` / ``grammar`` -- delegates to :func:`from_solution`.
    * ``toolbox`` -- a tool verdict; evidence ``tool``, no column 3.
    * ``reverse`` -- a reverse-TCT verdict; no column 3.
    * ``python`` -- a python-speech payload; no column 3.
    * ``frames`` -- a frame verdict; no column 3.
    * ``engineering`` -- an engineering solution; no column 3.
    """
    surface = getattr(routed, "surface", "") or ""
    answered = getattr(routed, "answered", False)
    text = getattr(routed, "text", "") or ""
    solution = getattr(routed, "solution", None)
    payload = getattr(routed, "payload", None)

    if surface in ("planner", "grammar") and solution is not None:
        r = from_solution(question, solution, replay=replay)
        # Override the surface to reflect the router's verdict.
        return Result(
            **{**r.as_dict(),
               "surface": surface,
               "question": question,
               "status": r.status if answered else "refused",
               "answer": r.answer if answered else "",
               "evidence": r.evidence if answered else (),
               "refusal": r.refusal if not answered else (r.refusal or "")}
        ) if False else _override_surface(r, surface, answered)

    # Non-solution surfaces: build a minimal Result from the routed verdict.
    # One evidence kind per result, refused or not (a tuple, as the field
    # is declared; 31 October 2026, repository check).
    evidence = ("tool",) if surface == "toolbox" else (
        _evidence_for_kind(getattr(payload, "kind", "")) if payload
        else _DEFAULT_EVIDENCE,)
    if answered:
        status = "answered"
        refusal = ""
    else:
        status = "refused"
        refusal = (text if refused_in_words(text) else "") or \
            "the surface refused without naming a reason"
    theorems, theorems_declared = cited_theorems(text) if answered else ((), ())

    return Result(
        question=question,
        status=status,
        surface=surface,
        kind=getattr(payload, "kind", "") or getattr(solution, "kind", "") or "",
        answer=text if answered else "",
        candidates=(),
        evidence=evidence,
        witness=(),
        theorems=theorems,
        boundary="uncertified",  # no column 3 on these surfaces
        budget={"steps": 1} if answered else {},
        ambiguity=(),
        refusal=refusal,
        history=(),
        replayed=None,
        theorems_declared=theorems_declared,
    )


def _override_surface(r: Result, surface: str, answered: bool) -> Result:
    """Return a copy of ``r`` with the surface set to ``surface`` and the
    status/answer/evidence/refusal adjusted to reflect ``answered``."""
    if answered:
        return Result(
            question=r.question, status=r.status, surface=surface, kind=r.kind,
            answer=r.answer, candidates=r.candidates, evidence=r.evidence,
            witness=r.witness, theorems=r.theorems, boundary=r.boundary,
            budget=r.budget, ambiguity=r.ambiguity, refusal=r.refusal,
            history=r.history, replayed=r.replayed,
            theorems_declared=r.theorems_declared,
        )
    return Result(
        question=r.question,
        status="contradicted" if r.status == "contradicted" else "refused",
        surface=surface, kind=r.kind,
        answer="", candidates=(), evidence=r.evidence, witness=(),
        theorems=r.theorems, boundary="refused", budget=r.budget, ambiguity=(),
        refusal=r.refusal or "the surface did not answer",
        history=r.history, replayed=None,
        theorems_declared=r.theorems_declared,
    )


# ---------------------------------------------------------------------------
# Adapter: from_define
# ---------------------------------------------------------------------------

def from_define(term: str, knowledge: Any) -> Result:
    """Build a :class:`Result` from a corpus definition lookup of ``term``.

    ``knowledge`` is a :class:`glm_universal.knowledge.model.Knowledge`
    instance (the corpus model).  The adapter reads the model's ``define``
    surface (``knowledge.define(term)`` or ``knowledge.model.define(term)``
    if available); if neither is available, it returns a refused result
    naming the absence.

    The corpus surface has its own boundary logic (``corpus:strong`` etc.)
    rather than the standard four values.
    """
    define_fn = getattr(knowledge, "define", None) or getattr(
        getattr(knowledge, "model", None), "define", None)
    if define_fn is None and knowledge is not None:
        # The corpus's own ``define`` reading (31 October 2026).
        try:
            from ..knowledge import answer as _corpus_answer
        except ImportError:  # pragma: no cover - the package is part of the tree
            _corpus_answer = None
        if _corpus_answer is not None:
            def define_fn(t: str, _k: Any = knowledge) -> Any:
                return _corpus_answer.define(t, _k)
    if define_fn is None:
        return Result(
            question=f"define {term}",
            status="refused",
            surface="corpus",
            kind="corpus:define",
            answer="",
            refusal="the corpus model has no define surface available",
            boundary="refused",
            budget={"mentions": 0},
        )
    try:
        outcome = define_fn(term)
    except Exception as exc:
        return Result(
            question=f"define {term}",
            status="refused",
            surface="corpus",
            kind="corpus:define",
            answer="",
            refusal=f"the corpus define surface raised: {exc}",
            boundary="refused",
            budget={"mentions": 0},
        )

    # The outcome is expected to be a dict-like with at least:
    #   answer (str), candidates (list[str]), witness (list[str]),
    #   strength (str), documents (int), mentions (int), source (str),
    #   support (int), pattern (str)
    if isinstance(outcome, Mapping):
        answered = bool(outcome.get("answer"))
        candidates = tuple(outcome.get("candidates", ()) or ())
        witness = list(outcome.get("witness", ()) or ())
        strength = outcome.get("strength", "strong")
        documents = int(outcome.get("documents", 0))
        mentions = int(outcome.get("mentions", 0))
        if answered:
            # Build the 5-tuple witness the model documents.
            if len(witness) < 5:
                witness = witness + [
                    f"pattern={outcome.get('pattern', '')}",
                    f"strength={outcome.get('strength', 2)}",
                    f"source={outcome.get('source', 'corpus')}",
                    f"support={outcome.get('support', 0)}",
                ][:5 - len(witness)]
            return Result(
                question=f"define {term}",
                status="answered",
                surface="corpus",
                kind="corpus:define",
                answer=str(outcome.get("answer", "")),
                candidates=(),
                evidence=("corpus",),
                witness=tuple(str(w) for w in witness[:5]),
                theorems=(),
                boundary=f"corpus:{strength}",
                budget={"documents": documents, "mentions": mentions},
                ambiguity=(),
                refusal="",
                history=(),
                replayed=None,
            )
        return Result(
            question=f"define {term}",
            status="refused",
            surface="corpus",
            kind="corpus:define",
            answer="",
            candidates=(),
            evidence=(),
            witness=(),
            theorems=(),
            boundary="refused",
            budget={"mentions": mentions},
            ambiguity=(),
            refusal=(
                f"the corpus mentions '{term}' in {mentions} sentences of "
                f"{documents} documents but no sentence defines it by a "
                f"declared pattern"
            ),
            history=(),
            replayed=None,
        )

    # Unexpected outcome type.
    return Result(
        question=f"define {term}",
        status="refused",
        surface="corpus",
        kind="corpus:define",
        answer="",
        refusal=f"the corpus define surface returned an unexpected type: "
                f"{type(outcome).__name__}",
        boundary="refused",
        budget={"mentions": 0},
    )


# ---------------------------------------------------------------------------
# Adapter: from_turn
# ---------------------------------------------------------------------------

def from_turn(turn: Any) -> Result:
    """Build a :class:`Result` from a conversation :class:`Turn`.

    The conversation surface has no column 3, so ``replayed`` is always
    ``None`` and ``boundary`` is ``uncertified`` (or ``refused`` when the
    turn did not answer).  The evidence is ``("lattice",)`` (or
    ``("lattice", "dialogue")`` when replies were read).

    The adapter reads ``turn.index``, ``turn.text``, ``turn.asked``,
    ``turn.kind``, ``turn.ok``, ``turn.answer``, ``turn.mentions``,
    ``turn.binding``, and ``turn.question``.
    """
    index = getattr(turn, "index", 0)
    text = getattr(turn, "text", "") or ""
    asked = getattr(turn, "asked", "") or text
    kind = getattr(turn, "kind", "") or "nearest"
    ok = getattr(turn, "ok", False)
    answer = getattr(turn, "answer", "") or ""
    question_record = getattr(turn, "question", None)
    binding = getattr(turn, "binding", None)
    mentions = getattr(turn, "mentions", ()) or ()

    # The open tie, if any.
    candidates: List[str] = []
    ambiguity: List[str] = []
    history: List[Tuple[str, str]] = []
    has_dialogue = False

    if isinstance(question_record, Mapping):
        options = question_record.get("options", []) or []
        for opt in options:
            keeps = opt.get("keeps", []) or []
            reply = opt.get("reply", "")
            for k in keeps:
                if k not in candidates:
                    candidates.append(k)
            if reply:
                has_dialogue = True
        # Reply history: each (question_token, reply) pair from a `given` reply.
        for opt in options:
            reply = opt.get("reply", "")
            keeps = opt.get("keeps", []) or []
            if reply and keeps:
                history.append((keeps[0], str(reply)))

    if binding is not None:
        has_dialogue = True
        considered = getattr(binding, "considered", ()) or ()
        for c in considered:
            if c not in ambiguity:
                ambiguity.append(c)

    # Status: `open` if there is an unresolved tie, else `answered`/`refused`.
    if not ok and not answer:
        status = "refused"
    elif candidates and not any(
        getattr(question_record, "resolved", False) if question_record else False
        for _ in [0]
    ):
        # If there are live candidates and the tie is not resolved, it's open.
        status = "open" if (question_record is not None and not _tie_resolved(question_record)) else "answered"
    else:
        status = "answered" if ok else "refused"

    evidence: Tuple[str, ...] = ("lattice",)
    if has_dialogue:
        evidence = ("lattice", "dialogue")

    return Result(
        question=asked or text,
        status=status,
        surface="conversation",
        kind=kind,
        answer=answer if status != "refused" else "",
        candidates=tuple(candidates) if status == "open" else (),
        evidence=evidence if status != "refused" else (),
        witness=(f"turn={index}",),
        theorems=(),
        boundary="uncertified" if status != "refused" else "refused",
        budget={"turn": index},
        ambiguity=tuple(ambiguity) if status == "open" else (),
        refusal="" if status != "refused" else "the conversation did not answer",
        history=tuple(history),
        replayed=None,
    )


def _tie_resolved(question_record: Any) -> bool:
    """True if the question record's tie is resolved (not open)."""
    if isinstance(question_record, Mapping):
        return bool(question_record.get("resolved", False))
    return False

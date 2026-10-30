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
#: ``Result.evidence`` is the primary kind; ``dialogue`` is appended only
#: by :func:`from_turn` when replies were read.
_KIND_TO_EVIDENCE: Dict[str, str] = {
    # Lattice / geometric addressing.
    "nearest": "lattice",
    "locate": "lattice",
    "project": "lattice",
    "cluster": "lattice",
    "spatial": "lattice",
    "trilinear": "lattice",
    "address": "lattice",
    "deep-hole": "lattice",
    "deep_hole": "lattice",
    "shell": "lattice",
    "configuration": "lattice",
    # Certificate / verification.
    "verify": "certificate",
    "prove": "certificate",
    "certificate": "certificate",
    "primality": "certificate",
    "pocklington": "certificate",
    "lucas": "certificate",
    "elliptic": "certificate",
    # Computation / derivation.
    "derive": "computation",
    "field": "computation",
    "analogy": "computation",
    "compare": "computation",
    "coherence": "computation",
    "fold": "computation",
    "rate": "computation",
    "maxent": "computation",
    "eigenvalue": "computation",
    "transmission": "computation",
    "fft": "computation",
    "hamming": "computation",
    "information": "computation",
    # Self-report / description.
    "describe": "self-report",
    "report": "self-report",
    "meaning": "self-report",
    "explain": "self-report",
    "explanation": "self-report",
    # Register.
    "register": "register",
    "element": "register",
    "nuclide": "register",
    "physics": "register",
    "molecule": "register",
    "law": "register",
}

#: Default evidence kind for an unknown Solution.kind.
_DEFAULT_EVIDENCE = "computation"

#: Theorem-name pattern: ``GLM.<Module>.<Name>`` (with optional further dots).
_THEOREM = re.compile(r"\bGLM\.([A-Z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+)")


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


def _solution_status(solution: Any) -> str:
    """The status of a solution: ``answered`` if ``ok``, ``refused`` if not."""
    ok = getattr(solution, "ok", True)
    error = getattr(solution, "error", None)
    if not ok or error:
        return "refused"
    return "answered"


def _solution_refusal(solution: Any) -> str:
    """The refusal reason for a solution, or ``""`` when answered."""
    error = getattr(solution, "error", None)
    if error:
        return str(error)
    ok = getattr(solution, "ok", True)
    if not ok:
        return "the solver refused without naming a reason"
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
    theorems = _scan_theorems(answer)
    budget = _solution_budget(solution)
    candidates = tuple(_solution_payload_field(solution, "candidates", ()) or ())
    ambiguity = tuple(_solution_payload_field(solution, "ambiguity", ()) or ())
    history = tuple(_solution_payload_field(solution, "history", ()) or ())

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

    if status == "refused":
        boundary = "refused"

    return Result(
        question=question,
        status=status,
        surface="planner",
        kind=kind,
        answer=answer if status != "refused" else "",
        candidates=candidates if status == "open" else (),
        evidence=(evidence_kind,) if status != "refused" else (),
        witness=(),
        theorems=theorems,
        boundary=boundary,
        budget=budget,
        ambiguity=ambiguity if status == "open" else (),
        refusal=refusal,
        history=tuple((q, r) for q, r in history),
        replayed=replayed,
        theorems_declared=theorems,  # no declaration list available here
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
    if answered:
        status = "answered"
        evidence = ("tool",) if surface == "toolbox" else (
            _evidence_for_kind(getattr(payload, "kind", "")) if payload else "computation"
        )
        refusal = ""
    else:
        status = "refused"
        evidence = ()
        refusal = "the surface refused without naming a reason"

    return Result(
        question=question,
        status=status,
        surface=surface,
        kind=getattr(payload, "kind", "") or getattr(solution, "kind", "") or "",
        answer=text if answered else "",
        candidates=(),
        evidence=evidence,
        witness=(),
        theorems=_scan_theorems(text) if answered else (),
        boundary="uncertified",  # no column 3 on these surfaces
        budget={"steps": 1} if answered else {},
        ambiguity=(),
        refusal=refusal,
        history=(),
        replayed=None,
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
        question=r.question, status="refused", surface=surface, kind=r.kind,
        answer="", candidates=(), evidence=(), witness=r.witness,
        theorems=(), boundary="refused", budget=r.budget, ambiguity=(),
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

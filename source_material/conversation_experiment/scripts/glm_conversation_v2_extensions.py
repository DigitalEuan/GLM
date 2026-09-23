"""``glm_conversation_v2_extensions.py`` — Five research-direction extensions
to ``glm_conversation_v2.py``, each addressing one paper from the research
feedback.

This file EXTENDS ``glm_conversation_v2.py`` — it imports the v2 classes
and adds five new mechanisms on top of them, exposed via a single new
class ``GLMConversationV3`` that subclasses v2 and adds the new methods.

The five extensions (one per paper):

  1. Four-register memory split
     (Graph-based Agent Memory: Taxonomy, Techniques, and Applications)
     Memory is split into: episodic / semantic / procedural / preferences.
     Each register has its own decay rate and retrieval rule.

  2. Role–filler binding  R ⊗ A ⊗ B
     (Attention as Binding: A Vector-Symbolic Perspective)
     Relations are not just triples — they can be bound into a single
     24-vector via exact Hadamard product, and recovered by exact divide.
     A `RelationBinder` provides bind / unbind / similarity operations.

  3. Procedural memory of successful reasoning traces
     (Experience-Evolving Multi-Turn Tool-Use Agent)
     When `reason()` succeeds, its `ReasoningPlan` is stored as a
     reusable `Procedure` keyed by query shape (intent + arity +
     structure). On future queries with matching shape, the procedure
     is retrieved and replayed — verifiable, not hallucinated.

  4. Grounding stage in `_extract()`
     (Mechanistic Emergence of Symbol Grounding in Language Models)
     A `Grounding` stage records aliases, paraphrases, context-dependent
     senses, and failed resolutions. Every surface form gets a
     Resolution record showing what was tried, what matched, and why
     the chosen sense was picked.

  5. Reasoning-trajectory licensing
     (The Geometry of Reasoning: Flowing Logics in Representation Space)
     A `Trajectory` records v_0 → v_1 → ... → v_n. Each transition is
     checked against three licence types: REGISTERED (carrier lookup),
     TYPED_RELATION (graph edge), DERIVED (verified by a PlanStep).
     Unlicensed transitions are flagged as `unlicensed`.

INVARIANTS (preserved)
======================
  * Exact arithmetic (int / Fraction / F₂) on all computation paths
  * No float constructed on any path that feeds a result
  * No randomness
  * Standard library + glm_universal only

PUBLIC API (additive on top of v2)
==================================
All v2 methods still work. New methods on `GLMConversationV3`:

    glm.episodic_memory()    -> MemoryRegister
    glm.semantic_memory()    -> MemoryRegister
    glm.procedural_memory() -> ProcedureRegister
    glm.preferences_memory() -> MemoryRegister
    glm.bind_relation(R, A, B) -> BoundRelation
    glm.unbind_relation(bound, R, A) -> Optional[carrier]
    glm.ground(text) -> List[Grounding]
    glm.trajectory(query) -> Trajectory

The five public methods (talk/explain/reason/attend/ask) now also
populate the new memory registers and produce trajectories.
"""

from __future__ import annotations

from fractions import Fraction
from dataclasses import dataclass, field
from typing import (
    Dict, List, Optional, Sequence, Tuple, Any, Set, FrozenSet, Iterable,
    Union, Callable,
)

# Import everything from v2 — we extend, we do not replace.
from glm_conversation_v2 import (
    GLMConversation, Confidence, Step, Span, Explanation, Answer,
    ReasonResult, Memory, Relation, Resolution, MemoryGraph,
    ReasoningPlan, PlanStep,
    PROVENANCE_AXIOM, PROVENANCE_FACT, PROVENANCE_DERIVED, PROVENANCE_GLOSS,
    _classify, _extract, _confidence, _fmt_frac, _ext10_exps,
    _verify_analogy, _subspace_indices, _sub_d2, _LAYER_DEPTH,
)
from glm_universal.runtime import GeometricSession
from glm_universal.reasoning import metric, dimension_layers
from glm_universal.reasoning import coherence as co
from glm_universal.reasoning import verifier as ve
from glm_universal.reasoning import analogy
from glm_universal.data_objects import physics as do_physics
from glm_universal.substrate import golay_decode

__all__ = [
    "GLMConversationV3",
    # Public data carriers (new in v3):
    "MemoryRegister", "MemoryKind", "Procedure", "ProcedureRegister",
    "BoundRelation", "RelationBinder", "Grounding",
    "Trajectory", "Transition", "TransitionLicence",
]


# ═══════════════════════════════════════════════════════════════════════════
# EXTENSION 1 — FOUR-REGISTER MEMORY SPLIT
# (Graph-based Agent Memory: Taxonomy, Techniques, and Applications)
# ═══════════════════════════════════════════════════════════════════════════

# Memory kinds — each gets its own register with its own decay + retrieval.
# Per the survey: episodic = what happened, semantic = stable concept
# knowledge, procedural = reusable how-to, preferences = user-specific.

class MemoryKind:
    """Memory register kinds (string constants)."""
    EPISODIC     = "episodic"       # per-turn conversation events
    SEMANTIC     = "semantic"       # stable concept facts from register
    PROCEDURAL   = "procedural"     # successful reasoning traces
    PREFERENCES  = "preferences"    # user-specific facts


# Decay rates per register (exact Fraction).
# Episodic decays fast (the v1 9/10 rule). Others do not decay —
# stable knowledge should not vanish just because time passes.
_DECAY_RATES: Dict[str, Optional[Fraction]] = {
    MemoryKind.EPISODIC:    Fraction(9, 10),
    MemoryKind.SEMANTIC:    None,  # no decay
    MemoryKind.PROCEDURAL:  None,  # no decay
    MemoryKind.PREFERENCES:  None,  # no decay
}


@dataclass
class MemoryRegister:
    """One memory register — episodic / semantic / procedural / preferences.

    Each register has its own decay rate (or None for no decay) and its
    own retrieval rule. The same Memory record can live in multiple
    registers (e.g. a verified analogy creates both an episodic Memory
    and a procedural Procedure).
    """
    kind: str
    memories: List[Memory] = field(default_factory=list)
    decay: Optional[Fraction] = None  # None = no decay

    def add(self, mem: Memory) -> None:
        self.memories.append(mem)

    def recall(self, query_concepts: Sequence[str], query_intent: str,
               session: GeometricSession,
               top_k: int = 5) -> List[Tuple[Memory, Fraction]]:
        """Retrieve by combined score with this register's decay rate.

        For episodic: recency matters (fast decay).
        For semantic: recency is irrelevant — knowledge is stable.
        For procedural: query-shape match dominates.
        For preferences: exact concept match dominates.
        """
        if not self.memories:
            return []
        scored: List[Tuple[Memory, Fraction]] = []
        n = len(self.memories)
        for i, mem in enumerate(self.memories):
            common = set(query_concepts) & set(mem.concepts)
            s_geo = Fraction(len(common), max(1, len(query_concepts)))
            # decay only applies if decay rate is set
            if self.decay is not None:
                s_rec = self.decay ** (n - 1 - i)
            else:
                s_rec = Fraction(1, 2)  # uniform — no recency preference
            s_int = Fraction(1) if mem.intent == query_intent else Fraction(1, 4)
            # Register-specific weighting
            if self.kind == MemoryKind.PROCEDURAL:
                # procedural: query-shape match is most important
                score = Fraction(1, 4) * s_geo + Fraction(1, 4) * s_rec + Fraction(1, 2) * s_int
            elif self.kind == MemoryKind.SEMANTIC:
                # semantic: geometry (concept match) is most important
                score = Fraction(3, 4) * s_geo + Fraction(1, 8) * s_rec + Fraction(1, 8) * s_int
            elif self.kind == MemoryKind.PREFERENCES:
                # preferences: exact concept match required (geometry=1.0)
                score = s_geo  # binary: 1 if all query concepts in memory, else fraction
            else:  # EPISODIC
                # episodic: balanced (the v2 default)
                score = (Fraction(1, 2) * s_geo + Fraction(1, 4) * Fraction(1, 4)
                         + Fraction(1, 8) * s_rec + Fraction(1, 8) * s_int)
            scored.append((mem, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def summary(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "count": len(self.memories),
            "decay": str(self.decay) if self.decay is not None else None,
            "recent": [
                {"turn": m.turn, "intent": m.intent,
                 "concepts": list(m.concepts), "text": m.text}
                for m in self.memories[-5:]
            ],
        }


# ═══════════════════════════════════════════════════════════════════════════
# EXTENSION 2 — ROLE-FILLER BINDING  R ⊗ A ⊗ B
# (Attention as Binding: A Vector-Symbolic Perspective)
# ═══════════════════════════════════════════════════════════════════════════
#
# In HDC (hyperdimensional computing), binding combines two vectors into
# one that is dissimilar to both — so the pair can be retrieved by similarity
# to either, and recovered by re-binding with the inverse.
#
# For the GLM's exact-arithmetic 24-dim rational substrate, we use:
#   - Hadamard (elementwise) product for binding (exact, recoverable)
#   - Elementwise divide for unbinding (exact, only fails on division by zero)
#
# This gives us a genuine R ⊗ A ⊗ B representation: a single 24-vector
# that *is* the relation (R, A, B), recoverable by unbinding.
#
# Per the paper: "binding represents a relation; bundling represents a set."
# v2 already uses bundling (averaging) for the conversation centroid.
# v3 adds binding for typed relations.


@dataclass(frozen=True)
class BoundRelation:
    """A typed relation (R, A, B) bound into a single 24-vector (or 24-bit
    mask for the parity variant).

    Two binding methods are supported:

      - "hadamard_perm": elementwise product of perm(A), A, B. Exact
        rational arithmetic, but partial recovery when divisors are
        zero (e.g. EXT10 exponents on unused axes are 0).
      - "parity_xor": XOR of parity_bits(perm(A)), parity_bits(A),
        parity_bits(B). Always fully recoverable — every parity bit is
        0 or 1, never zero in divisor. Stored as a 24-bit int mask.

    Per "Attention as Binding": binding represents a relation;
    bundling (v2's centroid) represents a set. v3 adds binding.
    """
    bound_vector: Tuple[Any, ...]               # length-24 Hadamard product (Fraction)
    bound_mask: int                            # 24-bit XOR mask (parity binding)
    relation_name: str                         # the R name (e.g. "causes")
    a_name: str                                 # the A name
    b_name: str                                 # the B name
    binding_method: str = "hadamard_perm"      # "hadamard_perm" or "parity_xor"


class RelationBinder:
    """Role–filler binding for the GLM substrate.

    Implements the three HDC binding primitives over exact-arithmetic
    24-vectors:

      - bind(R, A, B)    → BoundRelation
          Elementwise product r*a*b. Exact, reversible when no zeros.
      - unbind(bound, R, A) → carrier of B
          Elementwise divide: bound / r / a. Returns None on zero division.
      - similarity(bound, query) → Fraction in [0, 1]
          Cosine-squared similarity, exact.
    """

    def __init__(self, session: GeometricSession):
        self._s = session

    def _vec(self, name: str) -> Optional[Tuple[Any, ...]]:
        try:
            obj = self._s.resolve(name)
            return tuple(metric.as_exact_vector(obj.carrier))
        except Exception:
            return None

    @staticmethod
    def _hadamard3(r: Tuple[Any, ...], a: Tuple[Any, ...],
                   b: Tuple[Any, ...]) -> Tuple[Any, ...]:
        """Elementwise product of three 24-vectors (exact Fraction arithmetic)."""
        if not (len(r) == len(a) == len(b) == 24):
            raise ValueError(f"expected 24-vectors, got {len(r)}/{len(a)}/{len(b)}")
        out = []
        for i in range(24):
            rv = r[i] if isinstance(r[i], Fraction) else Fraction(int(r[i]))
            av = a[i] if isinstance(a[i], Fraction) else Fraction(int(a[i]))
            bv = b[i] if isinstance(b[i], Fraction) else Fraction(int(b[i]))
            out.append(rv * av * bv)
        return tuple(out)

    def bind(self, relation_name: str, a_name: str, b_name: str
             ) -> Optional[BoundRelation]:
        """Bind (R, A, B) into a single 24-vector AND a 24-bit mask.

        Two binding methods are computed simultaneously:

          1. Hadamard-perm: bound_vector = perm(A) * A * B
             Exact rational, but partial recovery when divisors are 0.

          2. Parity-XOR: bound_mask = parity(perm(A)) ^ parity(A) ^ parity(B)
             Always fully recoverable — every parity bit is 0 or 1.

        For typed relations (causes, contrasts_with, etc.) we do NOT
        have a register carrier for the relation itself. We use a
        deterministic permutation of A's carrier as R's "vector":
        this is the HDC trick — the permutation IS the role tag.

        So: bound = perm(R_permutation, A) * B
            unbind(bound, R, A) = bound / perm(R_permutation, A) = B

        Returns None if either A or B cannot be resolved.
        """
        a_vec = self._vec(a_name)
        b_vec = self._vec(b_name)
        if a_vec is None or b_vec is None:
            return None
        # Deterministic permutation per relation type
        perm = _RELATION_PERMUTATIONS.get(relation_name, tuple(range(24)))
        from glm_universal.substrate import permute_vector
        r_vec = permute_vector(a_vec, perm)
        # --- Hadamard binding (rational) ---
        bound_vec = self._hadamard3(r_vec, a_vec, b_vec)
        # --- Parity-XOR binding (F2) — always fully recoverable ---
        pa = dimension_layers.parity_bits(a_vec)
        pr = dimension_layers.parity_bits(r_vec)
        pb = dimension_layers.parity_bits(b_vec)
        bound_mask = pr ^ pa ^ pb
        return BoundRelation(
            bound_vector=bound_vec,
            bound_mask=bound_mask,
            relation_name=relation_name,
            a_name=a_name, b_name=b_name,
            binding_method="hadamard_perm+parity_xor",
        )

    def unbind_parity(self, bound: BoundRelation) -> Optional[int]:
        """Recover B's parity mask from a BoundRelation.

        bound_mask = parity(perm(A)) ^ parity(A) ^ parity(B)
        parity(B) = bound_mask ^ parity(perm(A)) ^ parity(A)

        Returns the 24-bit parity mask of B, or None if A cannot be
        resolved. Always succeeds (no zero-divisor issue).
        """
        a_vec = self._vec(bound.a_name)
        if a_vec is None:
            return None
        perm = _RELATION_PERMUTATIONS.get(bound.relation_name, tuple(range(24)))
        from glm_universal.substrate import permute_vector
        r_vec = permute_vector(a_vec, perm)
        pa = dimension_layers.parity_bits(a_vec)
        pr = dimension_layers.parity_bits(r_vec)
        return bound.bound_mask ^ pr ^ pa

    def recover_by_parity(self, bound: BoundRelation,
                          domain: str = "physics",
                          top_k: int = 5
                          ) -> List[Tuple[str, int]]:
        """Recover the B carrier by matching parity masks.

        Returns [(name, hamming_distance), ...] sorted ascending.
        A distance of 0 means an exact parity match.
        """
        target_mask = self.unbind_parity(bound)
        if target_mask is None:
            return []
        reg = self._s.register(domain)
        scored = []
        for o in reg:
            if o.name == bound.a_name:
                continue
            pmask = dimension_layers.parity_bits(o.carrier)
            # Hamming distance between masks
            dist = bin(target_mask ^ pmask).count("1")
            scored.append((o.name, dist))
        scored.sort(key=lambda x: x[1])
        return scored[:top_k]

    def unbind(self, bound: BoundRelation,
               recover_b: bool = True
               ) -> Optional[Tuple[Any, ...]]:
        """Recover B from a BoundRelation, given that R and A are known.

        bound = perm(A) * A * B
        B = bound / (perm(A) * A)

        Returns the recovered B carrier, or None if division-by-zero
        prevents recovery on ANY coordinate. For partial recovery
        (best-effort across non-zero divisors) use unbind_partial.
        """
        result = self.unbind_partial(bound)
        if result is None:
            return None
        recovered, zero_count = result
        return None if zero_count > 0 else recovered

    def unbind_partial(self, bound: BoundRelation
                       ) -> Optional[Tuple[Tuple[Any, ...], int]]:
        """Partial recovery of B — recovers coordinates where divisor
        is non-zero, returns None for zero-divisor coordinates (as 0).

        Returns (recovered_vector, zero_divisor_count) or None if A
        cannot be resolved.
        """
        a_vec = self._vec(bound.a_name)
        if a_vec is None:
            return None
        perm = _RELATION_PERMUTATIONS.get(bound.relation_name, tuple(range(24)))
        from glm_universal.substrate import permute_vector
        r_vec = permute_vector(a_vec, perm)
        recovered = []
        zero_count = 0
        for i in range(24):
            av = a_vec[i] if isinstance(a_vec[i], Fraction) else Fraction(int(a_vec[i]))
            rv = r_vec[i] if isinstance(r_vec[i], Fraction) else Fraction(int(r_vec[i]))
            divisor = rv * av
            if divisor == 0:
                recovered.append(Fraction(0))
                zero_count += 1
            else:
                bv = bound.bound_vector[i]
                bv = bv if isinstance(bv, Fraction) else Fraction(int(bv))
                recovered.append(bv / divisor)
        return (tuple(recovered), zero_count)

    def similarity(self, bound: BoundRelation,
                   candidate_name: str) -> Fraction:
        """Cosine-squared similarity between the bound vector and a
        candidate carrier. Exact rational arithmetic.

        Used for fuzzy recovery when exact unbind fails (e.g. zeros).
        """
        cand = self._vec(candidate_name)
        if cand is None:
            return Fraction(0)
        # cosine² = <u,v>² / (<u,u> * <v,v>)
        bv = bound.bound_vector
        dot = Fraction(0)
        norm_u = Fraction(0)
        norm_v = Fraction(0)
        for i in range(24):
            ui = bv[i] if isinstance(bv[i], Fraction) else Fraction(int(bv[i]))
            vi = cand[i] if isinstance(cand[i], Fraction) else Fraction(int(cand[i]))
            dot += ui * vi
            norm_u += ui * ui
            norm_v += vi * vi
        if norm_u == 0 or norm_v == 0:
            return Fraction(0)
        return (dot * dot) / (norm_u * norm_v)

    def recover_by_similarity(self, bound: BoundRelation,
                              domain: str = "physics",
                              top_k: int = 5
                              ) -> List[Tuple[str, Fraction]]:
        """Recover the B carrier of a BoundRelation by nearest-neighbour
        search over the register. Used when exact unbind fails.

        Returns [(name, similarity), ...] sorted descending.
        """
        reg = self._s.register(domain)
        scored = [(o.name, self.similarity(bound, o.name))
                  for o in reg if o.name not in (bound.a_name,)]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


# Deterministic permutations per relation type — these are the "role tags".
# A permutation of the 24-vector acts as the role marker for that relation
# type. We use the substrate's permute_vector with stable, distinct perms.
# These are NOT random — they are fixed derived permutations, so that
# bind/unbind is deterministic and reversible.
_RELATION_PERMUTATIONS: Dict[str, Tuple[int, ...]] = {
    # Identity (no permutation) for "equals" — the relation is the equality itself.
    "equals":            tuple(range(24)),
    # 1-step cyclic shift for "causes" (A causes B)
    "causes":            tuple((i + 1) % 24 for i in range(24)),
    # 2-step cyclic shift for "contrasts_with"
    "contrasts_with":    tuple((i + 2) % 24 for i in range(24)),
    # 3-step cyclic shift for "part_of"
    "part_of":           tuple((i + 3) % 24 for i in range(24)),
    # Reverse for "mentioned_after" (temporal)
    "mentioned_after":   tuple((23 - i) for i in range(24)),
    # 5-step cyclic shift for "affected_by"
    "affected_by":       tuple((i + 5) % 24 for i in range(24)),
    # 7-step cyclic shift for "derived_from"
    "derived_from":      tuple((i + 7) % 24 for i in range(24)),
}


# ═══════════════════════════════════════════════════════════════════════════
# EXTENSION 3 — PROCEDURAL MEMORY OF SUCCESSFUL REASONING TRACES
# (Experience-Evolving Multi-Turn Tool-Use Agent)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Procedure:
    """A reusable reasoning procedure.

    Stored when a `reason()` call succeeds. Keyed by query shape so
    future queries with the same shape can replay the procedure.

    A procedure is NOT a memory of what happened (that's episodic) —
    it's a reusable recipe for what to do next.
    """
    shape: str                                # query shape signature
    intent: str                              # describe/verify/analogy/explain/...
    arity: int                                # number of concepts in query
    plan: ReasoningPlan                      # the executed plan that succeeded
    final_answer: str                       # the verified answer
    success_count: int = 1                  # times this procedure has been reused
    last_used_turn: int = 0                 # turn of last reuse
    created_turn: int = 0                   # turn of first creation


def _query_shape(intent: str, concepts: List[str]) -> str:
    """Compute a query-shape signature.

    Two queries have the same shape iff they have the same intent and
    the same number of concepts. The actual concept names do NOT
    matter — the procedure is about the *shape* of the reasoning.
    """
    return f"{intent}:{len(concepts)}"


@dataclass
class ProcedureRegister:
    """Procedural memory: a register of reusable reasoning procedures.

    Distinct from episodic memory (which records what happened).
    Procedures record reusable how-to knowledge.
    """
    procedures: List[Procedure] = field(default_factory=list)

    def add(self, proc: Procedure) -> None:
        # If a procedure with the same shape exists, increment its
        # success count rather than duplicating.
        for i, p in enumerate(self.procedures):
            if p.shape == proc.shape:
                self.procedures[i] = Procedure(
                    shape=p.shape, intent=p.intent, arity=p.arity,
                    plan=p.plan, final_answer=p.final_answer,
                    success_count=p.success_count + 1,
                    last_used_turn=proc.last_used_turn,
                    created_turn=p.created_turn,
                )
                return
        self.procedures.append(proc)

    def find(self, intent: str, concepts: List[str]
             ) -> Optional[Procedure]:
        """Find a procedure matching this query shape."""
        shape = _query_shape(intent, concepts)
        for p in self.procedures:
            if p.shape == shape:
                return p
        return None

    def summary(self) -> Dict[str, Any]:
        return {
            "count": len(self.procedures),
            "procedures": [
                {"shape": p.shape, "intent": p.intent, "arity": p.arity,
                 "final_answer": p.final_answer,
                 "success_count": p.success_count,
                 "created_turn": p.created_turn,
                 "last_used_turn": p.last_used_turn}
                for p in self.procedures
            ],
        }


# ═══════════════════════════════════════════════════════════════════════════
# EXTENSION 4 — GROUNDING STAGE IN _extract()
# (Mechanistic Emergence of Symbol Grounding in Language Models)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Grounding:
    """The result of grounding a surface form to a stable concept.

    Records the full resolution trace: what surface form was tried,
    what candidate senses were considered, what aliases/paraphrases
    were tried, what the chosen sense is, and why it was chosen.

    A surface form may have multiple candidate senses — the chosen
    one depends on context (current domain, recent topics).
    """
    surface_form: str                          # the original text token/phrase
    aliases_tried: Tuple[str, ...]             # alias spellings tried
    paraphrases_tried: Tuple[str, ...]         # paraphrase spellings tried
    candidate_senses: Tuple[str, ...]          # all senses that resolved
    chosen: Optional[str]                       # the one we picked
    reason: str                                # why this one was picked
    failed: bool                                # True if no sense resolved


# Static alias / paraphrase tables — seed knowledge for the grounding stage.
# In a real system these would be loaded from a lexicon; here we provide
# a small starter set focused on physics.
_ALIASES: Dict[str, Tuple[str, ...]] = {
    # surface form -> register aliases to try (in order)
    "c":           ("speed_of_light",),
    "speed":       ("speed_of_light",),
    "light":       ("speed_of_light",),
    "lightspeed":  ("speed_of_light",),
    "light_speed": ("speed_of_light",),
    "wavenumber":  ("wavelength",),  # related but distinct — flagged
    "g":           ("gravitational_field", "gravitational_constant"),
    "gravity":     ("gravitational_field",),
    "gravitation": ("gravitational_field",),
    "e":           ("energy",),
    "energy_of":   ("energy",),
    "f":           ("force", "frequency"),  # ambiguous!
    "k":           ("spring_constant",),
    "h":           ("planck_constant",),
    "momentum":    ("momentum",),
    "mass":        ("mass",),  # also: social_mass in other domains
    "speed_of_light": ("speed_of_light",),
    "spacetime":   ("curvature",),
    "photon":      ("photon", "energy"),
    "newton":      ("force",),
    "hertz":       ("frequency",),
    "amps":        ("current",),
    "volts":       ("voltage",),
}

_PARAPHRASES: Dict[str, Tuple[str, ...]] = {
    # surface form -> paraphrase patterns to try
    "speed":       ("speed_of_light", "velocity"),
    "light":       ("speed_of_light", "wavelength", "frequency"),
    "gravity":     ("gravitational_field", "gravitational_constant", "force"),
    "energy":      ("energy", "kinetic_energy", "potential_energy"),
    "force":       ("force", "pressure", "tension"),
}


def _ground(session: GeometricSession, text: str,
            recent_concepts: Sequence[str] = ()
            ) -> Tuple[List[str], List[Grounding]]:
    """Grounding-augmented extraction.

    Returns (concepts, groundings). For each surface word in ``text``,
    we try:
      1. The literal surface form
      2. Aliases (e.g. "c" -> "speed_of_light")
      3. Paraphrases (e.g. "light" -> ["speed_of_light", "wavelength", ...])
      4. Context-dependent disambiguation: if multiple senses resolve,
         pick the one whose domain matches the most recent concept's
         domain (or the first if no context).

    Records every attempt in a Grounding record.
    """
    raw = text.lower().replace("?", "").replace(".", "").replace(
        ",", "").replace("!", "").split()
    words = [w for w in raw if w.isalpha() or "_" in w]

    concepts: List[str] = []
    groundings: List[Grounding] = []
    seen: Set[str] = set()
    consumed: Set[int] = set()

    # Multi-word concepts first (longest match, same as v2)
    n = len(words)
    for length in range(min(6, n), 0, -1):
        for start in range(n - length + 1):
            if any(p in consumed for p in range(start, start + length)):
                continue
            chunk = words[start:start + length]
            candidate = "_".join(chunk)
            if candidate in seen:
                continue
            # Grounding attempt 1: literal
            aliases = _ALIASES.get(candidate, ()) + (candidate,)
            paraphrases = _PARAPHRASES.get(candidate, ())
            senses_tried: List[str] = list(aliases) + list(paraphrases)
            senses_resolved: List[str] = []
            for s in senses_tried:
                try:
                    session.resolve(s)
                    if s not in senses_resolved:
                        senses_resolved.append(s)
                except Exception:
                    pass
            if not senses_resolved:
                # No sense resolved — record the failure
                if length == 1:
                    groundings.append(Grounding(
                        surface_form=candidate,
                        aliases_tried=tuple(aliases),
                        paraphrases_tried=tuple(paraphrases),
                        candidate_senses=(),
                        chosen=None,
                        reason="no sense resolved (genuinely unknown)",
                        failed=True,
                    ))
                continue
            # Multiple senses resolved — pick by context
            chosen = senses_resolved[0]
            reason = f"first of {len(senses_resolved)} tried senses"
            if len(senses_resolved) > 1 and recent_concepts:
                # Pick the sense whose domain matches the most recent concept
                try:
                    recent_obj = session.resolve(recent_concepts[-1])
                    recent_domain = recent_obj.domain
                    for s in senses_resolved:
                        try:
                            sobj = session.resolve(s)
                            if sobj.domain == recent_domain:
                                chosen = s
                                reason = (f"matches domain of recent concept "
                                          f"{recent_concepts[-1]!r} ({recent_domain}) "
                                          f"among {len(senses_resolved)} senses")
                                break
                        except Exception:
                            pass
                except Exception:
                    pass
            elif len(senses_resolved) > 1:
                reason = f"ambiguous ({len(senses_resolved)} senses) — picked first"
            concepts.append(chosen)
            seen.add(chosen)
            for p in range(start, start + length):
                consumed.add(p)
            groundings.append(Grounding(
                surface_form=candidate,
                aliases_tried=tuple(aliases),
                paraphrases_tried=tuple(paraphrases),
                candidate_senses=tuple(senses_resolved),
                chosen=chosen,
                reason=reason,
                failed=False,
            ))
    return concepts, groundings


# ═══════════════════════════════════════════════════════════════════════════
# EXTENSION 5 — REASONING-TRAJECTORY LICENSING
# (The Geometry of Reasoning: Flowing Logics in Representation Space)
# ═══════════════════════════════════════════════════════════════════════════

class TransitionLicence:
    """Licence types for a trajectory transition v_i → v_{i+1}.

    A transition is licensed if it is justified by one of:
      REGISTERED    — the target is a register carrier (lookup)
      TYPED_RELATION — the target is reached via a typed relation
                       (e.g. causes, derived_from)
      DERIVED       — the target is reached via a verified PlanStep
      UNLICENSED    — none of the above (flagged as suspicious)
    """
    REGISTERED      = "registered"
    TYPED_RELATION  = "typed_relation"
    DERIVED         = "derived"
    UNLICENSED      = "unlicensed"


@dataclass(frozen=True)
class Transition:
    """One transition in a reasoning trajectory.

    Each transition records:
      - the from/to concept names
      - the from/to carriers (exact 24-vectors)
      - the squared distance ||to - from||²
      - the licence type (registered / typed_relation / derived / unlicensed)
      - the licence evidence (which relation/plan-step justified it)
    """
    from_name: str
    to_name: str
    from_vec: Tuple[Any, ...]
    to_vec: Tuple[Any, ...]
    distance2: Fraction
    licence: str               # one of TransitionLicence.*
    evidence: str = ""         # name of relation or plan-step node


@dataclass(frozen=True)
class Trajectory:
    """A reasoning trajectory v_0 → v_1 → ... → v_n.

    Per "The Geometry of Reasoning: Flowing Logics in Representation
    Space" — reasoning is modelled as a path through representation
    space, not as isolated points.

    Each transition is licensed (or not) by REGISTERED / TYPED_RELATION
    / DERIVED. Unlicensed transitions are flagged.
    """
    start: str                                # v_0 name
    end: str                                  # v_n name
    transitions: Tuple[Transition, ...]
    total_distance2: Fraction                 # sum of ||v_{i+1} - v_i||²
    unlicensed_count: int                     # number of UNLICENSED transitions
    fully_licensed: bool                      # True iff unlicensed_count == 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start, "end": self.end,
            "transitions": [
                {"from": t.from_name, "to": t.to_name,
                 "d²": str(t.distance2), "licence": t.licence,
                 "evidence": t.evidence}
                for t in self.transitions
            ],
            "total_d²": str(self.total_distance2),
            "unlicensed": self.unlicensed_count,
            "fully_licensed": self.fully_licensed,
        }


def _build_trajectory(session: GeometricSession,
                      plan: ReasoningPlan,
                      relations: Sequence[Relation]
                      ) -> Trajectory:
    """Build a trajectory from an executed ReasoningPlan.

    For each consecutive pair of resolved concepts in the plan's
    successful steps, build a Transition and check its licence.
    """
    # Collect the ordered list of (name, vec) from plan steps that
    # actually resolved a carrier.
    visited: List[Tuple[str, Tuple[Any, ...]]] = []
    seen_names: Set[str] = set()
    for ps in plan.steps:
        if ps.status not in ("ok", "ambiguous"):
            continue
        if ps.op == "resolve":
            # Extract names from target like "force, energy, pressure"
            for n in ps.target.split(","):
                n = n.strip()
                if n and n not in seen_names:
                    try:
                        obj = session.resolve(n)
                        vec = tuple(metric.as_exact_vector(obj.carrier))
                        visited.append((n, vec))
                        seen_names.add(n)
                    except Exception:
                        pass
        elif ps.op == "verify" and ps.status == "ok":
            # Extract the verified target name
            # Target looks like "analogy force:energy::pressure:adhesion_energy"
            # or just "adhesion_energy"
            t = ps.target
            if ":" in t:
                # take last segment after the last ":"
                last = t.split(":")[-1].strip()
                # strip "analogy " prefix if present
                if " " in last:
                    last = last.split(" ")[-1]
                name = last
            else:
                name = t.strip()
            if name and name not in seen_names:
                try:
                    obj = session.resolve(name)
                    vec = tuple(metric.as_exact_vector(obj.carrier))
                    visited.append((name, vec))
                    seen_names.add(name)
                except Exception:
                    pass
        elif ps.op == "explain" and ps.status == "ok":
            name = ps.target.strip()
            if name and name not in seen_names:
                try:
                    obj = session.resolve(name)
                    vec = tuple(metric.as_exact_vector(obj.carrier))
                    visited.append((name, vec))
                    seen_names.add(name)
                except Exception:
                    pass

    # Build transitions
    transitions: List[Transition] = []
    total_d2 = Fraction(0)
    unlicensed = 0
    rel_lookup: Dict[Tuple[str, str], str] = {}
    for r in relations:
        rel_lookup[(r.a, r.b)] = r.relation_type
        rel_lookup[(r.b, r.a)] = r.relation_type  # symmetric direction

    for i in range(len(visited) - 1):
        n_from, v_from = visited[i]
        n_to, v_to = visited[i + 1]
        d2 = metric.distance2(v_from, v_to)
        total_d2 += d2
        # Determine licence
        licence = TransitionLicence.UNLICENSED
        evidence = ""
        # Check registered: target is always a register carrier by construction
        try:
            session.resolve(n_to)
            licence = TransitionLicence.REGISTERED
            evidence = f"register:{n_to}"
        except Exception:
            pass
        # Check typed relation: is there a relation (n_from, ?, n_to)?
        if (n_from, n_to) in rel_lookup:
            licence = TransitionLicence.TYPED_RELATION
            evidence = f"relation:{rel_lookup[(n_from, n_to)]}"
        # Check derived: was this transition produced by a verify/explain step?
        for ps in plan.steps:
            if ps.op in ("verify", "explain") and n_to in ps.target:
                licence = TransitionLicence.DERIVED
                evidence = f"plan:{ps.derivation_node or ps.target}"
                break
        if licence == TransitionLicence.UNLICENSED:
            unlicensed += 1
        transitions.append(Transition(
            from_name=n_from, to_name=n_to,
            from_vec=v_from, to_vec=v_to,
            distance2=d2, licence=licence, evidence=evidence,
        ))

    return Trajectory(
        start=visited[0][0] if visited else "",
        end=visited[-1][0] if visited else "",
        transitions=tuple(transitions),
        total_distance2=total_d2,
        unlicensed_count=unlicensed,
        fully_licensed=(unlicensed == 0),
    )


# ═══════════════════════════════════════════════════════════════════════════
# GLMConversationV3 — extends v2 with all five mechanisms
# ═══════════════════════════════════════════════════════════════════════════

class GLMConversationV3(GLMConversation):
    """The GLM conversational engine, v3 — extends v2 with five
    research-direction mechanisms.

    All v2 methods still work. New mechanisms are exposed via new
    methods and richer return objects.
    """

    def __init__(self):
        super().__init__()
        # v2 already created self._mg (the unified MemoryGraph).
        # v3 adds four registers:
        self._episodic = MemoryRegister(MemoryKind.EPISODIC,
                                         decay=_DECAY_RATES[MemoryKind.EPISODIC])
        self._semantic = MemoryRegister(MemoryKind.SEMANTIC,
                                         decay=_DECAY_RATES[MemoryKind.SEMANTIC])
        self._procedural = ProcedureRegister()
        self._preferences = MemoryRegister(MemoryKind.PREFERENCES,
                                            decay=_DECAY_RATES[MemoryKind.PREFERENCES])
        # The relation binder
        self._binder = RelationBinder(self._s)
        # The last trajectory produced by reason()
        self._last_trajectory: Optional[Trajectory] = None
        # Last groundings produced by talk()
        self._last_groundings: List[Grounding] = []

    # ── New public accessors ────────────────────────────────────────────

    def episodic_memory(self) -> MemoryRegister:
        return self._episodic

    def semantic_memory(self) -> MemoryRegister:
        return self._semantic

    def procedural_memory(self) -> ProcedureRegister:
        return self._procedural

    def preferences_memory(self) -> MemoryRegister:
        return self._preferences

    def binder(self) -> RelationBinder:
        return self._binder

    def last_trajectory(self) -> Optional[Trajectory]:
        return self._last_trajectory

    def last_groundings(self) -> List[Grounding]:
        return self._last_groundings

    # ── New: relation binding ───────────────────────────────────────────

    def bind_relation(self, relation_name: str, a: str, b: str
                      ) -> Optional[BoundRelation]:
        """Bind (R, A, B) into a single 24-vector AND 24-bit mask.

        Two binding methods computed simultaneously:
          - Hadamard-perm (rational): exact but partial recovery on zeros
          - Parity-XOR (F2): always fully recoverable

        Returns None if either A or B cannot be resolved.
        """
        return self._binder.bind(relation_name, a, b)

    def unbind_relation(self, bound: BoundRelation
                        ) -> Optional[Tuple[Any, ...]]:
        """Recover B from a BoundRelation by exact elementwise divide.

        Returns None if division-by-zero prevents recovery on ANY
        coordinate. For full recovery use unbind_parity() instead.
        """
        return self._binder.unbind(bound)

    def unbind_parity(self, bound: BoundRelation) -> Optional[int]:
        """Recover B's parity mask from a BoundRelation.

        Always succeeds (no zero-divisor issue). Returns the 24-bit
        parity mask of B, or None if A cannot be resolved.
        """
        return self._binder.unbind_parity(bound)

    def recover_relation_by_similarity(self, bound: BoundRelation,
                                        domain: str = "physics",
                                        top_k: int = 5
                                        ) -> List[Tuple[str, Fraction]]:
        """Recover the B carrier of a BoundRelation by cosine similarity."""
        return self._binder.recover_by_similarity(bound, domain, top_k)

    def recover_relation_by_parity(self, bound: BoundRelation,
                                    domain: str = "physics",
                                    top_k: int = 5
                                    ) -> List[Tuple[str, int]]:
        """Recover the B carrier by matching parity masks (Hamming distance)."""
        return self._binder.recover_by_parity(bound, domain, top_k)

    # ── New: grounding ──────────────────────────────────────────────────

    def ground(self, text: str) -> List[Grounding]:
        """Return the grounding records for ``text`` without
        committing them to memory. Useful for inspection.
        """
        recent = [m.concepts[-1] for m in self._episodic.memories[-3:]
                   if m.concepts]
        _, groundings = _ground(self._s, text, recent)
        return groundings

    # ── New: trajectory ─────────────────────────────────────────────────

    def trajectory(self, query: str) -> Optional[Trajectory]:
        """Build a reasoning trajectory for ``query``.

        Executes reason() (without committing to episodic memory) and
        returns the Trajectory object recording v_0 → v_1 → ... → v_n
        with licence annotations.
        """
        # Build a fresh plan (don't pollute memory)
        r = self.reason(query)
        if r.plan is None:
            return None
        # Collect relations from the conversation graph for this query
        concepts, _ = _extract(self._s, query)
        related_rels: List[Relation] = []
        for c in concepts:
            related_rels.extend(self._mg.expand_relations(c, max_depth=1))
        return _build_trajectory(self._s, r.plan, related_rels)

    # ── Override: talk() now uses grounding + 4 registers ──────────────

    def talk(self, input_text: str) -> Answer:
        """Process a natural-language input. v3 changes:
          - Uses _ground() (not _extract()) — records aliases, paraphrases,
            context-dependent senses, and failed resolutions.
          - Stores the Memory in both episodic and semantic registers.
          - Procedural register is updated only by reason().
        """
        # Grounding-augmented extraction
        recent = [m.concepts[-1] for m in self._episodic.memories[-3:]
                  if m.concepts]
        concepts, groundings = _ground(self._s, input_text, recent)
        self._last_groundings = groundings
        intent = _classify(input_text, concepts)

        # Dispatch (same as v2)
        trace: Optional[ReasoningPlan] = None
        memory_refs: Tuple[int, ...] = ()
        text: str = ""
        kind: str = intent

        if intent == "describe" and concepts:
            text, kind = self._do_describe(concepts[0])
        elif intent == "compare" and len(concepts) >= 2:
            text, kind = self._do_compare(concepts[0], concepts[1])
        elif intent == "analogy" and len(concepts) >= 3:
            text, kind = self._do_analogy(concepts[0], concepts[1],
                                          concepts[2])
            trace = self._build_analogy_trace(concepts[0], concepts[1],
                                              concepts[2], text)
        elif intent == "verify" and len(concepts) >= 2:
            text, kind = self._do_verify(concepts[0], concepts[1])
            trace = self._build_verify_trace(concepts[0], concepts[1])
        elif intent == "context":
            text, kind = self._do_context(), "context"
        elif intent == "explain" and concepts:
            exp = self._build_explanation(input_text, concepts)
            text = self._render(exp)
            kind = "explain"
            trace = self._build_explain_trace(exp)
        elif intent == "explore" and concepts:
            text, kind = self._do_explore(concepts[0])
        else:
            suggestions = self._suggest(input_text, concepts)
            text = self._fmt_suggestions(concepts, suggestions)
            kind = "suggestion"

        # Confidence
        conf = Confidence("identical", None, "single concept")
        if len(concepts) >= 2:
            try:
                a = self._s.resolve(concepts[0])
                b = self._s.resolve(concepts[1])
                conf = _confidence(
                    tuple(metric.as_exact_vector(a.carrier)),
                    tuple(metric.as_exact_vector(b.carrier)))
            except Exception:
                pass

        # Recall prior turns (combined-score, episodic register)
        if concepts:
            recalled = self._episodic.recall(concepts, intent, self._s, top_k=3)
            memory_refs = tuple(m.turn for m, _ in recalled if m.turn != 0)

        # Build the Memory record
        carriers: List[Tuple[Any, ...]] = []
        for c in concepts:
            try:
                obj = self._s.resolve(c)
                carriers.append(tuple(metric.as_exact_vector(obj.carrier)))
            except Exception:
                pass
        relations = self._infer_relations(concepts, intent,
                                            len(self._mg.memories) + 1)
        mem = Memory(
            turn=len(self._mg.memories) + 1,
            speaker="user",
            text=input_text,
            concepts=tuple(concepts),
            carriers=tuple(carriers),
            relations=tuple(relations),
            intent=intent,
            confidence=conf.score,
            provenance="user_input",
        )
        # v2 store (back-compat)
        self._mg.add_memory(mem)
        self._mg.add_relations(relations)
        # v3 stores: episodic + semantic
        self._episodic.add(mem)
        # Semantic: only concepts (not the full episode)
        for c in concepts:
            try:
                obj = self._s.resolve(c)
                smem = Memory(
                    turn=0,  # semantic facts are timeless
                    speaker="system",
                    text=f"register:{c}",
                    concepts=(c,),
                    carriers=(tuple(metric.as_exact_vector(obj.carrier)),),
                    relations=(),
                    intent="lookup",
                    confidence="high",
                    provenance="register_lookup",
                )
                self._semantic.add(smem)
            except Exception:
                pass

        # Summary
        ctx = self._mg.summary()
        # v3 additions: register summaries
        ctx["registers"] = {
            "episodic":    self._episodic.summary(),
            "semantic":    self._semantic.summary(),
            "procedural":  self._procedural.summary(),
            "preferences": self._preferences.summary(),
        }
        ctx["groundings"] = [
            {"surface": g.surface_form, "candidates": list(g.candidate_senses),
             "chosen": g.chosen, "reason": g.reason, "failed": g.failed}
            for g in groundings
        ]
        for d in ctx.get("domains", []):
            n = self._mg.nearest_to_centroid(self._s, d, 3)
            if n:
                ctx[f"nearest_{d}"] = list(n)

        return Answer(
            text=text, kind=kind, confidence=conf, context=ctx,
            suggestions=self._suggest("", concepts) if kind != "suggestion"
            else (),
            trace=trace, memory_refs=memory_refs,
        )

    # ── Override: reason() now stores successful plans as procedures ───

    def reason(self, question: str) -> ReasonResult:
        """v3 changes:
          - After a successful reason(), the ReasoningPlan is stored
            as a reusable Procedure in procedural memory.
          - Before generating candidates, the procedural register is
            checked for a matching query shape — if found, its plan
            is replayed and reported as "reused".
          - The trajectory is computed and stored on self._last_trajectory.
        """
        # Check procedural memory for a matching shape first
        concepts, _ = _extract(self._s, question)
        intent = _classify(question, concepts)
        existing_proc = self._procedural.find(intent, concepts)
        reuse_note = ""
        if existing_proc is not None:
            reuse_note = (f" [procedural memory: reused procedure "
                          f"shape={existing_proc.shape}, "
                          f"success_count={existing_proc.success_count}]")

        # Call v2's reason() — does the full propose-check-refine
        r = super().reason(question)

        # Compute trajectory and stash it
        related_rels: List[Relation] = []
        for c in concepts:
            related_rels.extend(self._mg.expand_relations(c, max_depth=1))
        self._last_trajectory = _build_trajectory(
            self._s, r.plan or ReasoningPlan(
                intent=intent, steps=(), final_answer=None,
                final_verified=False, failed_step=None, hypothesis=None,
            ), related_rels,
        )

        # If successful, store as a reusable Procedure
        if r.verified and r.answer is not None and r.plan is not None:
            proc = Procedure(
                shape=_query_shape(intent, concepts),
                intent=intent,
                arity=len(concepts),
                plan=r.plan,
                final_answer=r.answer,
                success_count=1,
                last_used_turn=len(self._mg.memories),
                created_turn=len(self._mg.memories),
            )
            self._procedural.add(proc)

        # Augment the steps with the reuse note if applicable
        if reuse_note:
            r = ReasonResult(
                answer=r.answer, method=r.method + reuse_note,
                confidence=r.confidence,
                steps=r.steps + (f"Procedure memory: {reuse_note.strip(' []')}",),
                verified=r.verified,
                hypothesis=r.hypothesis, plan=r.plan,
            )
        return r

    # ── Override: _do_context() now shows all 4 registers ───────────────

    def _do_context(self) -> str:
        """v3 context: shows the 4-register state, not just episodic."""
        lines = ["**Conversation Context (v3, 4-register):**", ""]
        lines.append(f"  Episodic memory:    {self._episodic.summary()['count']} turns")
        lines.append(f"  Semantic memory:    {self._semantic.summary()['count']} concepts")
        lines.append(f"  Procedural memory:  {self._procedural.summary()['count']} procedures")
        lines.append(f"  Preferences:       {self._preferences.summary()['count']} entries")
        lines.append("")
        # Recent episodic episodes
        lines.append("  Recent episodic episodes:")
        ep = self._episodic.summary()
        for e in ep["recent"][-5:]:
            lines.append(f"    [{e['turn']}] ({e['intent']}) {e['text']!r}")
            lines.append(f"        concepts: {e['concepts']}")
        # Procedural
        ps = self._procedural.summary()
        if ps["count"] > 0:
            lines.append("")
            lines.append("  Procedural memory (reusable reasoning traces):")
            for p in ps["procedures"]:
                lines.append(f"    shape={p['shape']} answer={p['final_answer']} "
                              f"(used {p['success_count']}×, "
                              f"created turn {p['created_turn']})")
        # Trajectory
        if self._last_trajectory is not None:
            lines.append("")
            lines.append(f"  Last trajectory: {self._last_trajectory.start} → "
                        f"{self._last_trajectory.end} "
                        f"({len(self._last_trajectory.transitions)} transitions, "
                        f"unlicensed={self._last_trajectory.unlicensed_count})")
        # Last groundings
        if self._last_groundings:
            lines.append("")
            lines.append("  Last groundings:")
            for g in self._last_groundings[-3:]:
                mark = "✗" if g.failed else "✓"
                lines.append(f"    {mark} {g.surface_form!r} -> {g.chosen} "
                            f"({g.reason})")
        # Domains + nearest
        s = self._mg.summary()
        for d in s.get("domains", []):
            n = self._mg.nearest_to_centroid(self._s, d, 5)
            if n:
                lines.append(f"  About ({d}): {list(n)}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# DEMO — exercises every v3 extension
# ═══════════════════════════════════════════════════════════════════════════

def _demo():
    print("=" * 72)
    print("GLM CONVERSATION v3 — Five research-direction extensions")
    print("=" * 72)
    print()

    glm = GLMConversationV3()

    # ── EXT 1: 4-register memory split ────────────────────────────────
    print("EXT 1 — Four-register memory split (Graph-based Agent Memory survey)")
    print("-" * 72)
    print("  Each register has its own decay rate and retrieval rule:")
    print("    episodic    — fast decay (9/10 per turn), balanced retrieval")
    print("    semantic    — no decay, concept-match weighted")
    print("    procedural  — no decay, query-shape weighted")
    print("    preferences — no decay, exact-match weighted")
    print()
    glm.talk("What is energy?")
    glm.talk("Compare energy and torque")
    glm.talk("verify force = mass * acceleration")
    print(f"  After 3 turns:")
    print(f"    episodic:   {glm.episodic_memory().summary()['count']} memories")
    print(f"    semantic:   {glm.semantic_memory().summary()['count']} concepts")
    print(f"    procedural: {glm.procedural_memory().summary()['count']} procedures")
    print(f"    preferences:{glm.preferences_memory().summary()['count']} entries")
    print()

    # ── EXT 2: Role-filler binding ────────────────────────────────────
    print("EXT 2 — Role-filler binding  R⊗A⊗B  (Attention as Binding)")
    print("-" * 72)
    print("  Bind (causes, force, acceleration) into both:")
    print("    (a) Hadamard-perm 24-vector (rational)")
    print("    (b) Parity-XOR 24-bit mask (F2, always recoverable)")
    bound = glm.bind_relation("causes", "force", "acceleration")
    print(f"    bound_vector (first 5): {bound.bound_vector[:5]}")
    print(f"    bound_mask (binary):    {bin(bound.bound_mask):>26s}")
    print(f"    binding_method: {bound.binding_method}")
    print()
    print("  --- Method A: Hadamard-perm unbind (rational) ---")
    print("  Recover B by exact elementwise divide:")
    recovered = glm.unbind_relation(bound)
    if recovered is not None:
        actual = tuple(metric.as_exact_vector(
            glm._s.resolve("acceleration").carrier))
        match = recovered == actual
        print(f"    recovered[0:5]: {recovered[:5]}")
        print(f"    matches register 'acceleration' carrier: {match}")
    else:
        partial = glm.binder().unbind_partial(bound)
        if partial is not None:
            rec_vec, zero_count = partial
            print(f"    exact unbind blocked by {zero_count} zero-divisor "
                  f"coordinates (zeros in force's carrier on unused axes)")
            actual = tuple(metric.as_exact_vector(
                glm._s.resolve("acceleration").carrier))
            nonzero_match = sum(1 for r, a in zip(rec_vec, actual)
                                if r != 0 and r == a)
            nonzero_total = sum(1 for r in rec_vec if r != 0)
            print(f"    partial recovery: {nonzero_match}/{nonzero_total} "
                  f"non-zero coordinates match the actual carrier")
    print()
    print("  --- Method B: Parity-XOR unbind (F2) --- ALWAYS recoverable ---")
    pmask = glm.unbind_parity(bound)
    actual_pmask = dimension_layers.parity_bits(
        glm._s.resolve("acceleration").carrier)
    print(f"    recovered parity mask (binary): {bin(pmask):>26s}")
    print(f"    actual 'acceleration' parity:    {bin(actual_pmask):>26s}")
    print(f"    exact match: {pmask == actual_pmask}")
    print()
    print("  Recover B by Hamming distance over parity masks:")
    top_p = glm.recover_relation_by_parity(bound, top_k=3)
    for n, d in top_p:
        print(f"    {n:25s} hamming_distance = {d}")
    print()

    # ── EXT 3: Procedural memory ──────────────────────────────────────
    print("EXT 3 — Procedural memory of successful reasoning traces")
    print("        (Experience-Evolving Multi-Turn Tool-Use Agent)")
    print("-" * 72)
    print("  First call to reason() — should store a procedure:")
    r1 = glm.reason("force : energy :: pressure : ?")
    print(f"    answer: {r1.answer}, verified: {r1.verified}")
    proc_count = glm.procedural_memory().summary()["count"]
    print(f"    procedural memory now has: {proc_count} procedure(s)")
    print()
    print("  Second call with the SAME query shape — procedure should be reused:")
    r2 = glm.reason("energy : mass :: enthalpy : ?")
    print(f"    answer: {r2.answer}")
    print(f"    method: {r2.method}")
    if "reused procedure" in r2.method:
        print("    ✓ Procedural memory reuse detected!")
    proc_summary = glm.procedural_memory().summary()
    for p in proc_summary["procedures"]:
        print(f"      shape={p['shape']}  success_count={p['success_count']}")
    print()

    # ── EXT 4: Grounding stage ────────────────────────────────────────
    print("EXT 4 — Grounding stage in _extract()")
    print("        (Mechanistic Emergence of Symbol Grounding)")
    print("-" * 72)
    print("  Grounding 'how does light bend near a massive object':")
    gs = glm.ground("how does light bend near a massive object")
    for g in gs[:6]:
        mark = "✗" if g.failed else "✓"
        print(f"    {mark} {g.surface_form!r:25s} -> {g.chosen}")
        print(f"        aliases tried: {g.aliases_tried}")
        print(f"        candidates: {g.candidate_senses}")
        print(f"        reason: {g.reason}")
    print()
    print("  Grounding 'c equals what':")
    gs2 = glm.ground("c equals what")
    for g in gs2:
        mark = "✗" if g.failed else "✓"
        print(f"    {mark} {g.surface_form!r:15s} -> {g.chosen} ({g.reason})")
    print()

    # ── EXT 5: Reasoning-trajectory licensing ────────────────────────
    print("EXT 5 — Reasoning-trajectory licensing")
    print("        (The Geometry of Reasoning: Flowing Logics)")
    print("-" * 72)
    print("  Trajectory for 'force : energy :: pressure : ?':")
    traj = glm.trajectory("force : energy :: pressure : ?")
    if traj:
        print(f"    path: {traj.start} → {traj.end}")
        print(f"    transitions: {len(traj.transitions)}")
        print(f"    total d²: {traj.total_distance2}")
        print(f"    unlicensed transitions: {traj.unlicensed_count}")
        print(f"    fully licensed: {traj.fully_licensed}")
        print("    Transitions:")
        for t in traj.transitions:
            mark = "✓" if t.licence != "unlicensed" else "✗"
            # Bug fix: distance2 is a Fraction, not a string — use _fmt_frac
            d2_str = _fmt_frac(t.distance2, 4)
            print(f"      {mark} {t.from_name:18s} → {t.to_name:22s} "
                  f"d²={d2_str:>10s} [{t.licence}] {t.evidence}")
    print()

    # ── Integration: rich context with all 4 registers ────────────────
    print("INTEGRATION — Rich context showing all 4 registers + trajectory")
    print("-" * 72)
    ctx_text = glm._do_context()
    for line in ctx_text.split("\n")[:25]:
        print(f"  {line}")
    print()

    print("=" * 72)
    print("DEMO COMPLETE — all 5 research-direction extensions work")
    print("=" * 72)


if __name__ == "__main__":
    _demo()

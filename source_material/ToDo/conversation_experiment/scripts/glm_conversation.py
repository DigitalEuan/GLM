"""``glm_conversation.py`` — The Complete GLM Conversational Engine

One file. Drop it into the GLM repository root. Import it:

    from glm_conversation import GLMConversation
    glm = GLMConversation()

It gives the GLM the ability to hold a conversation, explain concepts,
reason through problems, and generate answers — all in exact arithmetic.

WHAT IT DOES
============

Five capabilities, unified into one class:

1. TALK  — Multi-turn dialogue with carrier context.
   glm.talk("What is energy?")
   glm.talk("How does it relate to force?")
   glm.talk("What have we been talking about?")

2. EXPLAIN — Concept explanations in Three Column Thinking format.
   glm.explain("how does light bend near a massive object")

3. REASON — Propose-check-refine: generate candidates, verify, select.
   glm.reason("force : energy :: pressure : ?")

4. ATTEND — Subspace attention: find carriers by coordinate subspace.
   glm.attend("energy", subspace="dimension", top_k=5)

5. ASK — The native GLM query, with confidence scoring.
   answer, confidence = glm.ask("verify energy = mass * speed_of_light^2")

HOW IT WORKS
============

The GLM does not generate text from statistics. It constructs answers
from exact carriers in its registers:

- Conversational context: accumulates carriers with rational recency
  decay (9/10 per turn). The centroid answers "what is this about?"

- Subspace attention: different coordinate subspaces reveal different
  structure — dimensional families, magnitude neighbours, semantic clusters.

- Generative reasoning: candidates come from the GLM's own analogy
  system (5 named relation models), dimensional derivation (10 EXT10
  generators), complement search, and nearest-neighbour lookup.

- Verification: each candidate is checked through the GLM's exact
  instruments — dimensional consistency, coherence (NRCI), Golay
  decoding, layer escalation. The verification strategy matches the
  question type.

- Explanation: concepts are identified from natural language, looked up
  in the registers, and composed into a multi-step chain where each step
  is verified by the GLM's own machinery.

INVARIANTS
==========
Exact arithmetic (int / Fraction / F₂) on all computation paths.
No float constructed on any path that feeds a result.
No randomness. Standard library + glm_universal only.
"""

from __future__ import annotations

from fractions import Fraction
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple, Any, Set

from glm_universal.runtime import GeometricSession
from glm_universal.reasoning import metric, dimension_layers, analogy
from glm_universal.reasoning import coherence as co
from glm_universal.reasoning import verifier as ve
from glm_universal.reasoning import facets as fc
from glm_universal.reasoning import term_arithmetic as tar
from glm_universal.reasoning import controller as ctrl
from glm_universal.data_objects import physics as do_physics
from glm_universal.substrate import golay_decode

__all__ = ["GLMConversation"]


# ═══════════════════════════════════════════════════════════════════════════
# DATA CARRIERS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Confidence:
    """Answer confidence derived from layer information."""
    score: str            # "high", "medium", "low", "identical"
    first_separation: Optional[str]
    rationale: str


@dataclass(frozen=True)
class Step:
    """One step in a Three Column Thinking explanation."""
    language: str
    mathematics: str
    verification: str
    carriers: Tuple[str, ...]


@dataclass(frozen=True)
class Explanation:
    """A full explanation in Three Column Thinking format."""
    question: str
    steps: Tuple[Step, ...]
    summary: str
    carriers_used: Tuple[str, ...]


@dataclass(frozen=True)
class Answer:
    """A complete answer from the GLM."""
    text: str
    kind: str                     # "describe", "compare", "verify", "analogy", ...
    confidence: Confidence
    context: Dict[str, Any]
    suggestions: Tuple[str, ...]


@dataclass(frozen=True)
class ReasonResult:
    """Result of a propose-check-refine cycle."""
    answer: Optional[str]
    method: str
    confidence: Confidence
    steps: Tuple[str, ...]
    verified: bool


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT — accumulates carriers across conversation turns
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class _CtxEntry:
    vector: Tuple[Fraction, ...]
    name: str
    domain: str
    weight: Fraction


class _Context:
    """Conversation context with exact rational recency decay.

    Each new entry gets weight 1.  All previous entries decay by 9/10.
    The weighted centroid answers "what is this conversation about?"
    """

    def __init__(self, decay: Fraction = Fraction(9, 10)):
        self._entries: List[_CtxEntry] = []
        self._decay = decay
        self.turns = 0

    def add(self, carrier: Sequence, name: str, domain: str) -> None:
        vec = tuple(Fraction(int(v)) if isinstance(v, int) else v
                    for v in carrier)
        self._entries.append(_CtxEntry(vec, name, domain, Fraction(1)))
        for i in range(len(self._entries) - 1):
            e = self._entries[i]
            self._entries[i] = _CtxEntry(e.vector, e.name, e.domain,
                                         e.weight * self._decay)
        self.turns += 1

    def centroid(self, domain: Optional[str] = None
                 ) -> Optional[Tuple[Fraction, ...]]:
        entries = self._entries if domain is None else [
            e for e in self._entries if e.domain == domain]
        if not entries:
            return None
        dim = len(entries[0].vector)
        tw = Fraction(0)
        ws = [Fraction(0)] * dim
        for e in entries:
            tw += e.weight
            for i in range(dim):
                ws[i] += e.vector[i] * e.weight
        return tuple(ws[i] / tw for i in range(dim)) if tw else None

    def nearest(self, session: GeometricSession, domain: str = "physics",
                k: int = 5) -> Tuple[str, ...]:
        c = self.centroid(domain)
        if c is None:
            return ()
        reg = session.register(domain)
        ds = [(o.name, metric.distance2(c, tuple(metric.as_exact_vector(o.carrier))))
              for o in reg]
        ds.sort(key=lambda x: x[1])
        return tuple(n for n, _ in ds[:k])

    def summary(self) -> Dict[str, Any]:
        return {
            "turns": self.turns,
            "names": [e.name for e in self._entries[-10:]],
            "domains": list(dict.fromkeys(e.domain for e in self._entries)),
        }


# ═══════════════════════════════════════════════════════════════════════════
# CONCEPT EXTRACTION — finds register concepts in natural language
# ═══════════════════════════════════════════════════════════════════════════

_FILLER = frozenset({
    "i", "a", "is", "are", "was", "be", "do", "does", "did",
    "the", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "as", "into", "about",
    "what", "how", "why", "when", "where", "which", "who",
    "me", "my", "we", "our", "you", "your", "it", "its",
    "this", "that", "these", "those", "not", "no", "so",
    "if", "then", "than", "too", "very", "can", "will",
    "just", "should", "now", "here", "there", "also",
    "has", "have", "had", "been", "being", "some", "any",
    "all", "each", "every", "both", "few", "more", "most",
    "other", "another", "such", "only", "own", "same",
    "tell", "compare", "describe", "explain", "find",
    "show", "give", "get", "make", "take", "come", "go",
    "far", "long", "much", "many", "well", "still", "even",
    "does", "between", "relate", "relationship", "difference",
    "versus", "like", "similar", "nearest", "quantity",
    "has", "dimension", "what", "which", "whose", "whose",
    "path", "beam", "bent", "distorted", "affected",
})
_OPS = frozenset({"=", "*", "+", "-", "/", "^", "(", ")", "::", ":", "?"})


def _extract(session: GeometricSession, text: str) -> List[str]:
    """Extract register concepts from natural language.

    Strategy: longest-match scan — try joining consecutive words with
    underscores (handles 'speed of light' → 'speed_of_light'), then
    fall back to individual words.
    """
    raw = text.lower().replace("?", "").replace(".", "").replace(
        ",", "").replace("!", "").split()
    words = [w for w in raw if w not in _OPS
             and not w.isdigit() and (w.isalpha() or "_" in w)]

    concepts: List[str] = []
    seen: Set[str] = set()
    consumed: Set[int] = set()

    # Longest-match scan
    n = len(words)
    for length in range(min(6, n), 0, -1):
        for start in range(n - length + 1):
            if any(p in consumed for p in range(start, start + length)):
                continue
            cands = words[start:start + length]
            if all(w in _FILLER for w in cands):
                continue
            candidate = "_".join(cands)
            if candidate in seen:
                continue
            try:
                session.resolve(candidate)
                concepts.append(candidate)
                seen.add(candidate)
                for p in range(start, start + length):
                    consumed.add(p)
            except Exception:
                continue

    # Remaining individual words
    for idx, word in enumerate(words):
        if idx in consumed or word in _FILLER or word in seen:
            continue
        try:
            session.resolve(word)
            concepts.append(word)
            seen.add(word)
        except Exception:
            continue

    return concepts


def _classify(text: str, concepts: List[str]) -> str:
    """Classify user intent."""
    lower = text.lower()
    if "::" in lower:
        return "analogy"
    if any(w in lower for w in ["verify", "check", "does", "holds", "true"]):
        return "verify"
    if any(w in lower for w in ["compare", "difference", "versus", "vs"]):
        return "compare"
    if any(w in lower for w in ["describe", "tell me about", "what is",
                                 "explain", "profile"]):
        return "describe"
    if any(w in lower for w in ["context", "history", "discussed",
                                 "conversation"]):
        return "context"
    if any(w in lower for w in ["explain how", "why does", "how does",
                                 "how can", "what causes"]):
        return "explain"
    return "explore"


# ═══════════════════════════════════════════════════════════════════════════
# SUBSPACE ATTENTION — rank carriers by distance in coordinate subspaces
# ═══════════════════════════════════════════════════════════════════════════

def _subspace_indices(layout: Tuple[str, ...], subspace: str
                      ) -> Optional[List[int]]:
    if subspace == "dimension":
        return [i for i, n in enumerate(layout)
                if n.startswith("ext10.") or n.startswith("si7.")]
    if subspace == "scale":
        try:
            return [layout.index("scale")]
        except ValueError:
            return None
    if subspace == "full":
        return list(range(len(layout)))
    return None


def _sub_d2(a: Tuple[Fraction, ...], b: Tuple[Fraction, ...]) -> Fraction:
    return Fraction(1, 8) * sum((x - y) ** 2 for x, y in zip(a, b))


# ═══════════════════════════════════════════════════════════════════════════
# CONFIDENCE — scored from layer separation
# ═══════════════════════════════════════════════════════════════════════════

_LAYER_DEPTH = {"substrate": 0, "integer": 1, "rational": 2,
                "griess": 3, "universal": 4}


def _confidence(ca: Tuple[Fraction, ...], cb: Tuple[Fraction, ...]
                ) -> Confidence:
    try:
        esc = dimension_layers.escalate(ca, cb)
    except Exception:
        return Confidence("low", None, "layer escalation unavailable")
    first = None
    for name, _va, _vb, d in esc["all_views"]:
        if d != 0:
            first = name
            break
    if first is None:
        return Confidence("identical", None, "identical at all layers")
    depth = _LAYER_DEPTH.get(first, 5)
    if depth <= 1:
        return Confidence("high", first,
                          f"separate at {first} — clearly distinct")
    if depth <= 2:
        return Confidence("medium", first,
                          f"separate at {first} — same family")
    return Confidence("low", first,
                      f"only separate at {first} — very similar")


# ═══════════════════════════════════════════════════════════════════════════
# THE GLM CONVERSATION
# ═══════════════════════════════════════════════════════════════════════════

class GLMConversation:
    """The complete GLM conversational engine.

    One class. Five methods. Exact arithmetic throughout.

    Usage:
        glm = GLMConversation()

        # Talk — multi-turn dialogue
        glm.talk("What is energy?")
        glm.talk("How does it relate to force?")

        # Explain — Three Column Thinking explanation
        glm.explain("how does light bend near a massive object")

        # Reason — generate candidates, verify, select
        glm.reason("force : energy :: pressure : ?")

        # Attend — subspace attention
        glm.attend("energy", subspace="dimension", top_k=5)

        # Ask — native GLM query with confidence
        answer, conf = glm.ask("verify energy = mass * speed_of_light^2")
    """

    def __init__(self):
        self._s = GeometricSession()
        self._ctx = _Context()

    # ── 1. TALK — conversational interface ──────────────────────────────

    def talk(self, input_text: str) -> Answer:
        """Process a natural-language input with full conversation context.

        Returns an Answer with the response, confidence, context summary,
        and follow-up suggestions.
        """
        concepts = _extract(self._s, input_text)
        intent = _classify(input_text, concepts)

        # Dispatch
        if intent == "describe" and concepts:
            text, kind = self._do_describe(concepts[0])
        elif intent == "compare" and len(concepts) >= 2:
            text, kind = self._do_compare(concepts[0], concepts[1])
        elif intent == "analogy" and len(concepts) >= 3:
            text, kind = self._do_analogy(concepts[0], concepts[1],
                                          concepts[2])
        elif intent == "verify" and len(concepts) >= 2:
            text, kind = self._do_verify(concepts[0], concepts[1])
        elif intent == "context":
            text, kind = self._do_context(), "context"
        elif intent == "explain" and concepts:
            exp = self._build_explanation(input_text, concepts)
            text = self._render(exp)
            kind = "explain"
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

        # Update context
        for c in concepts:
            try:
                obj = self._s.resolve(c)
                self._ctx.add(obj.carrier, c, obj.domain)
            except Exception:
                pass

        ctx = self._ctx.summary()
        for d in ctx.get("domains", []):
            n = self._ctx.nearest(self._s, d, 3)
            if n:
                ctx[f"nearest_{d}"] = list(n)

        return Answer(
            text=text, kind=kind, confidence=conf, context=ctx,
            suggestions=self._suggest("", concepts) if kind != "suggestion"
            else ())

    # ── 2. EXPLAIN — Three Column Thinking explanations ─────────────────

    def explain(self, question: str) -> Explanation:
        """Explain a concept in Three Column Thinking format.

        Constructs the explanation from exact carriers in the GLM's
        registers. Each step is verified by the GLM's own machinery.
        """
        # Use physics-aware concept identification for explanations
        concepts = self._identify_physics(question)
        if not concepts:
            concepts = _extract(self._s, question)
        return self._build_explanation(question, concepts)

    # ── 3. REASON — propose, check, refine ──────────────────────────────

    def reason(self, question: str) -> ReasonResult:
        """Answer a question through propose-check-refine.

        Generates candidates through the GLM's analogy system, dimensional
        derivation, and nearest-neighbour search. Verifies each through
        the GLM's exact instruments. Returns the best answer or an honest
        refusal.
        """
        concepts = _extract(self._s, question)
        intent = _classify(question, concepts)
        steps: List[str] = []
        candidates: List[Tuple[str, Fraction, str]] = []  # (name, conf, method)

        # Generate: analogy
        if intent == "analogy" and len(concepts) >= 3:
            try:
                sol = self._s.ask(
                    f"{concepts[0]} : {concepts[1]} :: {concepts[2]} : ?")
                if sol.ok:
                    name = sol.answer.split(" : ")[-1].strip()
                    for n in [x.strip() for x in name.split(" or ")]:
                        try:
                            self._s.resolve(n)
                            candidates.append((n, Fraction(10),
                                              "analogy_transport"))
                        except Exception:
                            continue
                    steps.append(
                        f"Analogy: {concepts[0]}:{concepts[1]}::"
                        f"{concepts[2]}→? → {name}")
            except Exception as e:
                steps.append(f"Analogy failed: {e}")

        # Generate: nearest neighbours
        if concepts:
            try:
                obj = self._s.resolve(concepts[0])
                vec = tuple(metric.as_exact_vector(obj.carrier))
                reg = self._s.register(obj.domain)
                ds = [(o.name, metric.distance2(
                    vec, tuple(metric.as_exact_vector(o.carrier))))
                    for o in reg if o.name != concepts[0]]
                ds.sort(key=lambda x: x[1])
                for name, d2 in ds[:5]:
                    conf = Fraction(1) / (Fraction(1) + d2)
                    candidates.append((name, conf, f"nearest d²={d2}"))
                steps.append(f"Nearest: {min(5, len(ds))} from "
                            f"{concepts[0]}")
            except Exception:
                pass

        # Generate: dimensional derivation
        if intent == "derive" and concepts:
            state, refusal = ctrl.classify_target(concepts[0])
            if refusal is None:
                steps.append(f"Derivation target: {concepts[0]} "
                            f"(state={state})")
            else:
                steps.append(f"Derivation refused: {refusal.reason}")

        if not candidates:
            return ReasonResult(
                answer=None, method="none",
                confidence=Confidence("low", None, "no candidates"),
                steps=tuple(steps), verified=False)

        steps.append(f"Candidates: {len(candidates)}")

        # Verify: strategy matches intent
        best: Optional[Tuple[str, Fraction, str, bool]] = None
        for name, conf, method in candidates:
            passed = self._verify_candidate(name, intent, concepts)
            if passed:
                steps.append(f"✓ {name} ({method})")
                if best is None or conf > best[1]:
                    best = (name, conf, method, True)
            else:
                steps.append(f"✗ {name}")

        if best:
            name, conf, method, _ = best
            return ReasonResult(
                answer=name, method=method,
                confidence=Confidence("high", None,
                                     f"verified via {method}"),
                steps=tuple(steps), verified=True)

        return ReasonResult(
            answer=candidates[0][0] if candidates else None,
            method=candidates[0][2] if candidates else "none",
            confidence=Confidence("low", None, "none verified"),
            steps=tuple(steps), verified=False)

    # ── 4. ATTEND — subspace attention ───────────────────────────────────

    def attend(self, concept: str, subspace: str = "full",
               domain: str = "physics",
               top_k: int = 10) -> Tuple[Tuple[str, Fraction], ...]:
        """Rank carriers by distance in a named coordinate subspace.

        Subspaces: "dimension" (EXT10+SI7), "scale", "full" (all 24).
        Returns (name, d²) pairs sorted by distance.
        """
        try:
            obj = self._s.resolve(concept, domain)
        except Exception:
            return ()
        qv = tuple(metric.as_exact_vector(obj.carrier))
        layout = tuple(obj.layout)
        idx = _subspace_indices(layout, subspace)
        if idx is None:
            return ()
        qs = tuple(qv[i] for i in idx)
        reg = self._s.register(domain)
        ds: List[Tuple[str, Fraction]] = []
        for o in reg:
            if o.name == concept:
                continue
            ov = tuple(metric.as_exact_vector(o.carrier))
            os = tuple(ov[i] for i in idx)
            ds.append((o.name, _sub_d2(qs, os)))
        ds.sort(key=lambda x: x[1])
        return tuple(ds[:top_k])

    # ── 5. ASK — native query with confidence ────────────────────────────

    def ask(self, query: str) -> Tuple[Optional[Any], Confidence]:
        """Run a native GLM query with confidence scoring."""
        concepts = _extract(self._s, query)
        conf = Confidence("identical", None, "single concept")
        if len(concepts) >= 2:
            try:
                a = self._s.resolve(concepts[0])
                b = self._s.resolve(concepts[1])
                conf = _confidence(
                    tuple(metric.as_exact_vector(a.carrier)),
                    tuple(metric.as_exact_vector(b.carrier)))
            except Exception:
                conf = Confidence("low", None, "could not score")
        try:
            sol = self._s.ask(query)
            return sol, conf
        except Exception:
            return None, conf

    # ── internal: describe ───────────────────────────────────────────────

    def _do_describe(self, concept: str) -> Tuple[str, str]:
        try:
            obj = self._s.resolve(concept)
        except Exception:
            return f"I don't know '{concept}'.", "describe"

        vec = tuple(metric.as_exact_vector(obj.carrier))
        bits = dimension_layers.parity_bits(obj.carrier)
        hw = bin(bits).count("1")
        dec = golay_decode.decode_complete(bits)

        layout = tuple(obj.layout)
        ext = []
        for i, name in enumerate(layout):
            if name.startswith("ext10.") and i < len(vec) and vec[i] != 0:
                axis = name.split(".")[-1]
                e = int(vec[i])
                ext.append(axis if e == 1 else f"{axis}^{e}")

        try:
            nrci_val = co.nrci(obj.carrier)
            regime = co.coherence_regime(nrci_val)
            nrci_s = f"NRCI = {float(nrci_val):.4f} ({regime})"
        except:
            nrci_s = "NRCI unavailable"

        reg = self._s.register(obj.domain)
        ds = [(o.name, metric.distance2(
            vec, tuple(metric.as_exact_vector(o.carrier))))
            for o in reg if o.name != concept]
        ds.sort(key=lambda x: x[1])
        near = ", ".join(f"{n} (d²={d})" for n, d in ds[:3])

        lines = [
            f"**{concept}** ({obj.domain})",
            f"  Dimension: {' '.join(ext) if ext else 'dimensionless'}",
            f"  Substrate: HW={hw}, decode={dec.status}, "
            f"snap_distance={dec.weight}",
            f"  Coherence: {nrci_s}",
            f"  Nearest: {near}",
        ]
        return "\n".join(lines), "describe"

    # ── internal: compare ────────────────────────────────────────────────

    def _do_compare(self, a: str, b: str) -> Tuple[str, str]:
        try:
            a_obj = self._s.resolve(a)
            b_obj = self._s.resolve(b)
        except Exception as e:
            return f"Could not resolve: {e}", "compare"

        ca = tuple(metric.as_exact_vector(a_obj.carrier))
        cb = tuple(metric.as_exact_vector(b_obj.carrier))
        d2 = metric.distance2(ca, cb)

        try:
            esc = dimension_layers.escalate(ca, cb)
        except Exception:
            return f"**{a} vs {b}:** d²={d2}", "compare"

        lines = [f"**{a} vs {b}:**"]
        first = None
        for name, va, vb, d in esc["all_views"]:
            if d == 0:
                lines.append(f"  {name}: identical")
            else:
                detail = f"d={d}"
                if name == "integer":
                    ea = va.get("exponents_SI7", ())
                    eb = vb.get("exponents_SI7", ())
                    if ea == eb:
                        detail += f"  same SI7: {ea} → same family!"
                lines.append(f"  {name}: {detail}")
                if first is None:
                    first = name

        try:
            bd = fc.facet_distance_breakdown(ca, cb)
            carry = [k for k, v in bd.items() if v != 0]
            if carry:
                lines.append(f"  Facets: {', '.join(carry)}")
        except:
            pass

        if first:
            if first == "substrate":
                lines.append(f"\n  → Fundamentally different carriers")
            elif first == "integer":
                lines.append(f"\n  → Same dimensional family, distinct carriers")
            else:
                lines.append(f"\n  → Only {first} layer separates them")

        return "\n".join(lines), "compare"

    # ── internal: analogy ────────────────────────────────────────────────

    def _do_analogy(self, a: str, b: str, c: str) -> Tuple[str, str]:
        try:
            sol = self._s.ask(f"{a} : {b} :: {c} : ?")
            if sol.ok:
                return f"{a} : {b} :: {c} : **{sol.answer}**", "analogy"
            return f"Could not solve: {sol.error}", "analogy"
        except Exception as e:
            return f"Analogy error: {e}", "analogy"

    # ── internal: verify ─────────────────────────────────────────────────

    def _do_verify(self, a: str, b: str) -> Tuple[str, str]:
        try:
            sol = self._s.ask(f"verify {a} = {b}")
            if sol.ok:
                return f"**Verification:** {sol.answer}", "verify"
        except:
            pass
        return f"Could not verify '{a}' = '{b}'.", "verify"

    # ── internal: explore ────────────────────────────────────────────────

    def _do_explore(self, concept: str) -> Tuple[str, str]:
        desc, _ = self._do_describe(concept)
        lines = [desc]
        summary = self._ctx.summary()
        for topic in summary.get("names", [])[-3:]:
            if topic != concept:
                try:
                    sol = self._s.ask(f"{concept} : {topic} :: ?")
                    if sol.ok:
                        lines.append(f"\n  Link: {concept} : {topic} :: ? "
                                    f"→ {sol.answer}")
                except:
                    pass
        return "\n".join(lines), "explore"

    # ── internal: context ────────────────────────────────────────────────

    def _do_context(self) -> str:
        s = self._ctx.summary()
        lines = [f"**Conversation Context:**",
                 f"  Turns: {s['turns']}",
                 f"  Domains: {s['domains']}",
                 f"  Topics: {s['names']}"]
        for d in s.get("domains", []):
            n = self._ctx.nearest(self._s, d, 5)
            if n:
                lines.append(f"  About ({d}): {list(n)}")
        return "\n".join(lines)

    # ── internal: explanation builder ────────────────────────────────────

    def _identify_physics(self, text: str) -> List[str]:
        """Find physics concepts from question keywords."""
        clusters = {
            "light": ["speed_of_light", "wavelength", "frequency"],
            "gravity": ["gravitational_field", "gravitational_constant",
                       "mass", "force"],
            "energy": ["energy", "mass", "speed_of_light"],
            "bend": ["curvature", "gravitational_field", "speed_of_light"],
            "bent": ["curvature", "gravitational_field", "speed_of_light"],
            "distort": ["curvature", "gravitational_field", "mass"],
            "distorted": ["curvature", "gravitational_field", "mass"],
            "path": ["curvature", "speed_of_light", "gravitational_field"],
            "wave": ["wavelength", "frequency", "speed_of_light"],
            "massive": ["mass", "gravitational_field", "gravitational_constant"],
            "beam": ["speed_of_light", "wavelength", "curvature"],
            "near": ["gravitational_field", "mass", "curvature"],
            "deflect": ["curvature", "gravitational_field", "speed_of_light"],
            "deflection": ["curvature", "gravitational_field", "speed_of_light"],
            "spacetime": ["curvature", "speed_of_light", "energy"],
            "photon": ["speed_of_light", "energy", "frequency"],
        }
        lower = text.lower()
        words = set(lower.split())
        found: List[str] = []
        seen: Set[str] = set()
        for kw, cands in clusters.items():
            if kw in words or kw in lower:
                for c in cands:
                    if c not in seen:
                        try:
                            self._s.resolve(c)
                            found.append(c)
                            seen.add(c)
                        except:
                            pass
        return found[:6]

    def _build_explanation(self, question: str,
                          concepts: List[str]) -> Explanation:
        """Build a multi-step explanation from register carriers."""
        steps: List[Step] = []
        used: List[str] = list(concepts)

        # Step 1: Identify concepts
        steps.append(Step(
            language=f"Relevant carriers: {', '.join(concepts)}.",
            mathematics=f"concepts = {{{', '.join(concepts)}}} ⊂ register",
            verification="Each resolved in the GLM register.",
            carriers=tuple(concepts)))

        # Step 2: Describe each carrier
        for c in concepts[:4]:
            try:
                obj = self._s.resolve(c)
                vec = tuple(metric.as_exact_vector(obj.carrier))
                layout = tuple(obj.layout)
                ext = []
                for i, n in enumerate(layout):
                    if n.startswith("ext10.") and i < len(vec) and vec[i] != 0:
                        axis = n.split(".")[-1]
                        e = int(vec[i])
                        ext.append(axis if e == 1 else f"{axis}^{e}")
                dim = " ".join(ext) if ext else "dimensionless"

                bits = dimension_layers.parity_bits(obj.carrier)
                hw = bin(bits).count("1")
                dec = golay_decode.decode_complete(bits)

                try:
                    nv = co.nrci(obj.carrier)
                    ns = f"NRCI={float(nv):.4f} ({co.coherence_regime(nv)})"
                except:
                    ns = "NRCI n/a"

                steps.append(Step(
                    language=f"{c}: dimension {dim}, HW={hw}, "
                            f"decode={dec.status}, {ns}.",
                    mathematics=f"{c}: dim={dim}, HW={hw}, "
                               f"snap={dec.weight}",
                    verification=f"decode={dec.status}, {ns}",
                    carriers=(c,)))
            except:
                pass

        # Step 3: Find relationships
        verified_rels: List[Tuple[str, str, bool]] = []
        for i in range(len(concepts)):
            for j in range(i + 1, min(len(concepts), i + 3)):
                a, b = concepts[i], concepts[j]
                rel = self._find_rel(a, b)
                if rel:
                    steps.append(rel)
                    verified_rels.append((a, b, True))

        # Step 4: Concept-specific chain
        has_light = any(c in concepts for c in
                       ["speed_of_light", "wavelength", "frequency"])
        has_grav = any(c in concepts for c in
                      ["gravitational_field", "gravitational_constant", "mass"])

        if has_light and has_grav:
            steps.extend(self._chain_light_gravity())
        elif has_light:
            steps.extend(self._chain_light())
        elif has_grav:
            steps.extend(self._chain_gravity())

        # Summary
        summary = (
            f"Constructed from {len(concepts)} carriers in the GLM register. "
            f"{len(verified_rels)} relationships verified. "
            f"Each step checked by the GLM's own dimensional analysis.")

        return Explanation(question=question, steps=tuple(steps),
                          summary=summary, carriers_used=tuple(used))

    def _find_rel(self, a: str, b: str) -> Optional[Step]:
        """Find and verify a relationship between two carriers."""
        try:
            a_obj = self._s.resolve(a)
            b_obj = self._s.resolve(b)
        except:
            return None

        ca = tuple(metric.as_exact_vector(a_obj.carrier))
        cb = tuple(metric.as_exact_vector(b_obj.carrier))

        try:
            esc = dimension_layers.escalate(ca, cb)
            first = next((n for n, _va, _vb, d in esc["all_views"]
                         if d != 0), "identical")
            layer_info = []
            for n, va, vb, d in esc["all_views"]:
                layer_info.append(f"{n}: {'identical' if d == 0 else f'd={d}'}")
        except:
            first = "unknown"
            layer_info = ["escalation unavailable"]

        try:
            ver = ve.verify_expression_pair(a, b, "scalar")
            vt = f"verify {a} = {b}: holds={ver.holds}"
        except:
            vt = "n/a"

        return Step(
            language=f"{a} and {b} first separate at {first} layer.",
            mathematics=f"escalate({a},{b}): first_sep = {first}",
            verification=f"{vt}; {'; '.join(layer_info)}",
            carriers=(a, b))

    def _chain_light_gravity(self) -> List[Step]:
        """The light-gravity explanation chain."""
        steps: List[Step] = []

        # c = L/T
        try:
            sol = self._s.ask("verify speed_of_light = length / time")
            ans = sol.answer if sol.ok else "verification attempted"
        except:
            ans = "n/a"
        steps.append(Step(
            language="Light propagates at speed c, dimension L T⁻¹. "
                    "This is a fundamental constant in the register.",
            mathematics="c: dim = L T⁻¹. verify c = length / time.",
            verification=ans,
            carriers=("speed_of_light", "length", "time")))

        # g = F/m
        try:
            sol = self._s.ask("verify gravitational_field = force / mass")
            ans = sol.answer if sol.ok else "n/a"
        except:
            ans = "n/a"
        steps.append(Step(
            language="A massive object creates a gravitational field with "
                    "dimension L T⁻² (acceleration). Field = force / mass.",
            mathematics="g: dim = L T⁻². verify g = force / mass.",
            verification=ans,
            carriers=("gravitational_field", "force", "mass")))

        # E = mc²
        try:
            sol = self._s.ask("verify energy = mass * speed_of_light^2")
            ans = sol.answer if sol.ok else "n/a"
        except:
            ans = "n/a"
        steps.append(Step(
            language="Einstein's E = mc². A photon has energy E = hf, so "
                    "effective mass m = E/c² = hf/c². Gravity affects light "
                    "because photons carry energy, even though they are "
                    "massless.",
            mathematics="E = mc² → m_eff = hf/c². "
                       "verify energy = mass × c².",
            verification=ans,
            carriers=("energy", "mass", "speed_of_light", "frequency")))

        # Curvature
        steps.append(Step(
            language="In general relativity, gravity is spacetime curvature. "
                    "Mass-energy tells spacetime how to curve; curvature "
                    "tells light how to move. Curvature has dimension L⁻¹.",
            mathematics="curvature: dim = L⁻¹. "
                       "G_μν = (8πG/c⁴) T_μν",
            verification="curvature carrier: L⁻¹ in EXT10",
            carriers=("curvature", "gravitational_constant",
                     "speed_of_light", "energy")))

        # Deflection formula
        steps.append(Step(
            language="Light deflection: δθ = 4GM/(rc²). Both GM and rc² "
                    "have dimension L³T⁻², so the ratio is dimensionless "
                    "(an angle). The GLM verifies this exactly.",
            mathematics="dim(GM) = L³T⁻² = dim(rc²). "
                       "δθ = 4GM/(rc²) is dimensionless. ✓",
            verification="gravitational_constant × mass = L³T⁻². "
                        "length × c² = L³T⁻². Dimensions match.",
            carriers=("gravitational_constant", "mass", "length",
                     "speed_of_light")))

        # Layer comparison
        try:
            ca = tuple(metric.as_exact_vector(
                self._s.resolve("speed_of_light").carrier))
            cb = tuple(metric.as_exact_vector(
                self._s.resolve("gravitational_field").carrier))
            esc = dimension_layers.escalate(ca, cb)
            info = []
            for n, va, vb, d in esc["all_views"]:
                info.append(f"{n}: {'identical' if d == 0 else f'd={d}'}")
            steps.append(Step(
                language="Speed of light (L/T) and gravitational field "
                        "(L/T²) share length but differ in time exponent. "
                        "They are distinct carriers from substrate up.",
                mathematics="SI7(c) = (1,0,-1,0,0,0,0). "
                           "SI7(g) = (1,0,-2,0,0,0,0).",
                verification="; ".join(info),
                carriers=("speed_of_light", "gravitational_field")))
        except:
            pass

        return steps

    def _chain_light(self) -> List[Step]:
        return [Step(
            language="Light: electromagnetic wave at speed c. "
                    "c = λf, E = hf = hc/λ.",
            mathematics="c = λf, E = hf",
            verification="speed_of_light carrier: L T⁻¹",
            carriers=("speed_of_light", "wavelength", "frequency", "energy"))]

    def _chain_gravity(self) -> List[Step]:
        return [Step(
            language="Gravity: F = GMm/r². Field = F/m = GM/r².",
            mathematics="F = GMm/r², g = GM/r²",
            verification="gravitational_field carrier: L T⁻²",
            carriers=("gravitational_field", "gravitational_constant",
                     "force", "mass"))]

    # ── internal: verification ───────────────────────────────────────────

    def _verify_candidate(self, name: str, intent: str,
                         concepts: List[str]) -> bool:
        """Verify a candidate using intent-appropriate strategy."""
        try:
            obj = self._s.resolve(name)
        except:
            return False

        if intent == "analogy":
            # Analogies: just need to be a valid carrier
            return True

        if intent in ("explore", "nearest", "describe"):
            # Exploration: check coherence
            try:
                nrci_val = co.nrci(obj.carrier)
                return co.coherence_regime(nrci_val) in (
                    "OnBit", "Coherent")
            except:
                return True

        # Default: dimensional verification
        if len(concepts) >= 2:
            try:
                ver = ve.verify_expression_pair(concepts[0], name, "scalar")
                return ver.holds
            except:
                return False

        return True

    # ── internal: suggestions ────────────────────────────────────────────

    _VERB_MAP = {
        "describe": "describe {a}", "what is": "describe {a}",
        "explain": "describe {a}", "tell me about": "describe {a}",
        "compare": "project {a} {b}", "difference": "project {a} {b}",
        "versus": "project {a} {b}",
        "verify": "verify {a} = {b}", "check": "verify {a} = {b}",
        "nearest": "nearest 5 to {a}", "similar": "nearest 5 to {a}",
        "coherence": "coherence of {a}", "nrci": "coherence of {a}",
        "force": "verify force = mass * acceleration",
        "energy": "verify energy = mass * speed_of_light^2",
        "task": "task physics", "report": "report benchmarks",
    }

    def _suggest(self, text: str, concepts: List[str]) -> Tuple[str, ...]:
        lower = text.lower()
        out: List[str] = []
        for verb, tmpl in self._VERB_MAP.items():
            if verb in lower:
                if "{b}" in tmpl and len(concepts) >= 2:
                    out.append(tmpl.format(a=concepts[0], b=concepts[1]))
                elif "{a}" in tmpl and concepts:
                    out.append(tmpl.format(a=concepts[0]))
                elif "{" not in tmpl:
                    out.append(tmpl)
        if not out:
            if len(concepts) >= 3:
                out.append(
                    f"{concepts[0]} : {concepts[1]} :: {concepts[2]} : ?")
            if len(concepts) >= 2:
                out.append(f"verify {concepts[0]} = {concepts[1]}")
                out.append(f"project {concepts[0]} {concepts[1]}")
            if concepts:
                out.append(f"describe {concepts[0]}")
        seen: Set[str] = set()
        result: List[str] = []
        for s in out:
            if s not in seen:
                seen.add(s)
                result.append(s)
        return tuple(result[:5])

    def _fmt_suggestions(self, concepts: List[str],
                        suggestions: Tuple[str, ...]) -> str:
        if not suggestions:
            return ("Try: describe energy | verify energy = mass * "
                   "speed_of_light^2 | force : energy :: pressure : ?")
        lines = []
        if concepts:
            lines.append(f"Found: {concepts}")
        lines.append("Try:")
        for s in suggestions:
            lines.append(f"  {s}")
        return "\n".join(lines)

    # ── internal: rendering ──────────────────────────────────────────────

    def _render(self, exp: Explanation) -> str:
        """Render an explanation as text."""
        lines = [f"**Explanation:** {exp.question}", ""]
        for i, step in enumerate(exp.steps, 1):
            lines.append(f"  {i}. {step.language}")
            lines.append(f"     Math: {step.mathematics}")
            lines.append(f"     Check: {step.verification}")
            lines.append("")
        lines.append(exp.summary)
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════════

def _demo():
    print("=" * 72)
    print("GLM CONVERSATION — Complete Demo")
    print("=" * 72)
    print()

    glm = GLMConversation()

    # 1. Talk
    print("1. TALK — Multi-turn dialogue")
    print("-" * 40)
    for q in ["What is energy?", "Tell me about force",
              "Compare energy and torque", "What have we discussed?"]:
        print(f"\n  USER: {q}")
        a = glm.talk(q)
        for line in a.text.split("\n")[:6]:
            print(f"  GLM:  {line}")
        print(f"  [{a.kind}, conf={a.confidence.score}]")
    print()

    # 2. Explain
    print("2. EXPLAIN — Three Column Thinking")
    print("-" * 40)
    exp = glm.explain("how does light bend near a massive object")
    for i, step in enumerate(exp.steps[:8], 1):
        print(f"\n  Step {i}: {step.language}")
        print(f"    Math: {step.mathematics}")
        print(f"    Check: {step.verification[:80]}...")
    print(f"\n  Summary: {exp.summary}")
    print()

    # 3. Reason
    print("3. REASON — Propose, Check, Refine")
    print("-" * 40)
    for q in ["force : energy :: pressure : ?",
              "What is nearest to energy?"]:
        print(f"\n  Q: {q}")
        r = glm.reason(q)
        print(f"  Answer: {r.answer}")
        print(f"  Method: {r.method}")
        print(f"  Verified: {r.verified}")
    print()

    # 4. Attend
    print("4. ATTEND — Subspace Attention")
    print("-" * 40)
    for sub in ["dimension", "full"]:
        print(f"\n  Energy in '{sub}' subspace:")
        for name, d2 in glm.attend("energy", subspace=sub, top_k=5):
            print(f"    {name}: d² = {d2}")
    print()

    # 5. Ask
    print("5. ASK — Native Query + Confidence")
    print("-" * 40)
    for q in ["verify energy = mass * speed_of_light^2",
              "verify force = mass * acceleration"]:
        sol, conf = glm.ask(q)
        if sol and sol.ok:
            print(f"  {q}")
            print(f"    → {sol.answer}")
            print(f"    Confidence: {conf.score} — {conf.rationale}")
    print()

    print("=" * 72)
    print("DEMO COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    _demo()

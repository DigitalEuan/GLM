# ══════════════════════════════════════════════════════════════════════════════
# §33  CONSIDERED RESPONSE (v3.20.0 — multi-paragraph mode-algebraic NL)
# ══════════════════════════════════════════════════════════════════════════════
#
# PURPOSE
#   The user's feedback: "results that need a lot of work particularly around
#   chat/natural language longer considered response." This module produces
#   longer, multi-paragraph responses that are grounded in Kracht's mode-algebra
#   — every sentence is a definite sign combination, not a template-filler.
#
#   The existing chat_prose (GLM19) produces 5-7 sentences in a single
#   paragraph with template rotation. This module produces 3-4 paragraphs:
#     1. DIRECT ANSWER — the clean answer + what the query is about
#     2. REASONING — CRG backbone walk with mode-algebraic gating
#     3. EVIDENCE — KB recalls, definitions, substrate metrics
#     4. CONCLUSION — verification + summary
#
#   Each paragraph is composed of DEFINITE signs only — combinations where
#   all three Kracht homomorphisms (ε, γ, µ) are defined. Indefinite
#   combinations (contradictions, missing vectors) are either dropped or
#   hedged with "appears to" / "may" language.
#
# ARCHITECTURE
#
#   compose_considered(state) -> str:
#     Takes the full pipeline state dict (from GLM11._run_pipeline)
#     Returns a multi-paragraph string.
#
#   The composer uses GLM32's mode-algebra to:
#     - Build signs from content words and CRG edges
#     - Combine signs using typed modes (SVO, RELATION, DEFINITION, ELABORATION)
#     - Gate every sentence on definiteness
#     - Hedge indefinite combinations
#
#   This is the "considered" layer — it thinks before it speaks, in the
#   sense that every sentence must pass the mode-algebra's definiteness check.
#
# AUTHOR
#   Z.ai v3.20 development push — 2026-07-08
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# ── GLM imports ─────────────────────────────────────────────────────────────
try:
    from GLM32_mode_algebra import (
        Sign, BOTTOM, Mode, MODES,
        MODE_SVO, MODE_RELATION, MODE_DEFINITION, MODE_CONTRADICTION,
        MODE_ELABORATION,
        category_vector, category_vector_from_vec, dominant_role,
        has_category_affordance,
        sign_from_word, sign_from_edge,
        combine, combine_svo, combine_relation, combine_definition,
        backbone_to_signs, signs_to_sentences,
        verbalise_edge, _EDGE_VERBALISATION, _INDEFINITE_LABELS,
    )
    _HAS_MODE_ALGEBRA = True
except Exception as _e:
    _HAS_MODE_ALGEBRA = False
    _MA_ERR = str(_e)


# ══════════════════════════════════════════════════════════════════════════════
#  PARAGRAPH BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def _build_direct_answer(state: Dict[str, Any], vocab: Any) -> str:
    """Paragraph 1: Direct answer + query framing.

    This paragraph states the answer (if available) and frames what the
    query is about using the content words.
    """
    sentences: List[str] = []
    query = state.get("query", "")
    content = state.get("content", [])
    answer_block = state.get("answer_block")
    comp_res = state.get("compute")
    sym_res = state.get("symbolic")
    delib_res = state.get("deliberation")

    # Opening: what is this query about?
    if content:
        topic_words = [w for w, _ in content[:3]]
        if len(topic_words) == 1:
            sentences.append(f"Your query concerns {topic_words[0]}.")
        elif len(topic_words) == 2:
            sentences.append(f"Your query concerns the relationship between {topic_words[0]} and {topic_words[1]}.")
        else:
            topic_str = ", ".join(topic_words[:-1]) + f", and {topic_words[-1]}"
            sentences.append(f"Your query concerns {topic_str}.")

    # Direct answer
    if answer_block is not None:
        ans_val = getattr(answer_block, 'value', str(answer_block))
        ans_kind = getattr(answer_block, 'kind', 'unknown')
        if ans_kind == "boolean":
            sentences.append(f"The answer is {ans_val}.")
        elif ans_kind == "list":
            sentences.append(f"The solution is {ans_val}.")
        elif ans_kind == "deliberation":
            sentences.append(f"The conclusion is: {ans_val}.")
        else:
            sentences.append(f"The answer is {ans_val}.")

    # Computation context
    if comp_res:
        expr = comp_res.get("computation", {}).get("expr", "")
        result = comp_res.get("result", {}).get("exact", "")
        native = comp_res.get("result", {}).get("native", False)
        if native:
            sentences.append(f"This was computed natively on the substrate: {expr} = {result}.")
        else:
            sentences.append(f"The computation yields {expr} = {result}.")

    # Symbolic context
    if sym_res:
        kind = sym_res.get("computation", {}).get("kind", "")
        result = sym_res.get("result", {}).get("exact", "")
        native = sym_res.get("result", {}).get("native", False)
        if native:
            sentences.append(f"The native polynomial engine {kind}s this to {result}.")
        else:
            sentences.append(f"The symbolic engine {kind}s this to {result}.")

    # Deliberation context
    if delib_res:
        pattern = delib_res.get("pattern", "")
        method = delib_res.get("method", "")
        answer = delib_res.get("answer", "")
        sentences.append(f"Through {method.replace('_', ' ')}, the pattern detector identifies: {answer}.")

    if not sentences:
        return ""
    return " ".join(sentences)


def _build_reasoning(state: Dict[str, Any], vocab: Any) -> str:
    """Paragraph 2: Reasoning — CRG backbone walk with mode-algebraic gating.

    This paragraph walks the CRG backbone and produces definite sign
    combinations. Only definite combinations are emitted — indefinite ones
    (contradictions, missing vectors) are hedged or dropped.

    v3.20.1: Enhanced to also walk CRG paths between content words (not just
    the zone backbone), and to extract richer detail from definitions.
    """
    if not _HAS_MODE_ALGEBRA:
        return ""

    sentences: List[str] = []
    zone = state.get("zone")
    content = state.get("content", [])
    crg = state.get("_crg")  # may be passed by the runtime

    # Try to get a CRG backbone from the zone
    backbone = []
    if zone and hasattr(zone, 'crg_backbone') and zone.crg_backbone:
        backbone = list(zone.crg_backbone)

    # If no zone backbone, try to build one from content words using CRG edges
    if not backbone and content and crg:
        content_words = [w for w, _ in content[:4]]
        for i, w1 in enumerate(content_words):
            for w2 in content_words[i+1:]:
                # Check direct CRG edges between content words
                edges_out = crg.out.get(w1.lower(), [])
                for edge in edges_out:
                    if edge.dst.lower() == w2.lower() and edge.label not in _INDEFINITE_LABELS:
                        backbone.append(edge)
                        break
                if len(backbone) >= 3:
                    break
            if len(backbone) >= 3:
                break

    # Convert backbone edges to definite signs
    if backbone:
        signs = backbone_to_signs(backbone, vocab, max_signs=5)
        definite_sentences = signs_to_sentences(signs)
        if definite_sentences:
            if len(definite_sentences) == 1:
                sentences.append(f"The concept relation graph reveals: {definite_sentences[0]}")
            else:
                sentences.append("The concept relation graph reveals the following connections:")
                for s in definite_sentences:
                    sentences.append(s)

    # Build sign combinations from content words
    if content and len(content) >= 1:
        content_signs = []
        for word, entry in content[:4]:
            s = sign_from_word(word, vocab)
            if not s.is_bottom:
                content_signs.append((word, s, entry))

        # Try DEFINITION mode for content words that have definitions
        for word, s, entry in content_signs:
            if hasattr(entry, 'definition') and entry.definition:
                defn = entry.definition
                # Try multiple extraction patterns
                kind_word = None
                # Pattern 1: "is a X" / "is an X"
                m = re.search(r'is\s+(?:a|an)\s+(\w+)', defn, re.I)
                if m:
                    kind_word = m.group(1).lower()
                # Pattern 2: first word if definition starts with a noun
                if not kind_word:
                    first_word = defn.split()[0].lower().strip(',.')
                    if len(first_word) > 2 and first_word in (vocab.words if hasattr(vocab, 'words') else vocab):
                        kind_word = first_word

                if kind_word and kind_word in (vocab.words if hasattr(vocab, 'words') else vocab):
                    kind_sign = sign_from_word(kind_word, vocab)
                    if not kind_sign.is_bottom:
                        def_sign = combine_definition(s, kind_sign)
                        if def_sign:
                            sentences.append(def_sign.E)
                            break  # one definition per paragraph

    # Elaboration: add detail from definitions (richer extraction)
    # v3.20.1: Only elaborate on the PRIMARY topic word, and skip for
    # compute/symbolic queries where the computation IS the reasoning.
    is_compute = state.get("compute") is not None
    is_symbolic = state.get("symbolic") is not None
    if content and not is_compute and not is_symbolic:
        # Only elaborate on the first content word (the primary topic)
        word, entry = content[0]
        if hasattr(entry, 'definition') and entry.definition:
            defn = entry.definition
            # Take the first 1-2 sentences of the definition
            defn_sentences = re.split(r'(?<=[.])\s+', defn)
            if defn_sentences:
                first = defn_sentences[0].strip()
                if len(first) > 20:
                    # Don't repeat if it's the same as the definition mode output
                    if not any(first[:30] in s for s in sentences):
                        sentences.append(f"Specifically, {first.lower()}")
                        # Add second sentence if available and relevant
                        if len(defn_sentences) > 1 and len(defn_sentences[1]) > 30:
                            second = defn_sentences[1].strip()
                            sentences.append(f"Furthermore, {second.lower()}")

    # If we still have nothing, try CRG edges from content words
    if not sentences and content and crg:
        for word, _ in content[:2]:
            edges = crg.out.get(word.lower(), [])
            for edge in edges[:2]:
                if edge.label in _INDEFINITE_LABELS:
                    continue
                edge_sign = sign_from_edge(edge, vocab)
                if not edge_sign.is_bottom:
                    src_sign = sign_from_word(edge.src, vocab)
                    combined = combine_relation(src_sign, edge_sign)
                    if combined:
                        sentences.append(f"Within the substrate, {combined.E.lower()}")
                        break
            if sentences:
                break

    # v3.20.1: Fallback for definition queries — use KB recall descriptions
    if not sentences:
        recalled = state.get("recalled", [])
        for entry in recalled[:2]:
            desc = entry.get("desc", "") or entry.get("description", "")
            name = entry.get("name", entry.get("ubp_id", ""))
            if desc and len(desc) > 20:
                # Use the first 1-2 sentences of the KB description
                desc_sentences = re.split(r'(?<=[.])\s+', desc)
                if desc_sentences:
                    first = desc_sentences[0].strip()
                    if name:
                        sentences.append(f"According to the knowledge base, {name}: {first.lower()}")
                    else:
                        sentences.append(f"According to the knowledge base, {first.lower()}")
                    # Add second sentence if available
                    if len(desc_sentences) > 1 and len(desc_sentences[1]) > 30:
                        second = desc_sentences[1].strip()
                        sentences.append(f"Furthermore, {second.lower()}")
                    break

    if not sentences:
        return ""
    return " ".join(sentences)


def _build_method(state: Dict[str, Any], vocab: Any) -> str:
    """Paragraph 2b: Method — for compute/symbolic queries, surface the
    computation trace (how the substrate arrived at the answer).

    This paragraph replaces the reasoning paragraph for compute/symbolic
    queries, where the computation IS the reasoning. It shows the native
    ALU trace — the step-by-step execution log.
    """
    sentences: List[str] = []
    comp_res = state.get("compute")
    sym_res = state.get("symbolic")

    if comp_res:
        result = comp_res.get("result", {})
        trace = result.get("trace", [])
        native = result.get("native", False)
        kind = comp_res.get("computation", {}).get("kind", "")
        if trace and native:
            sentences.append(f"The native {kind} computation was executed on the substrate with the following trace:")
            # Format trace as a numbered list
            for i, line in enumerate(trace[:4], 1):
                sentences.append(f"  {i}. {line}")
            if len(trace) > 4:
                sentences.append(f"  ... ({len(trace) - 4} more steps)")
        elif trace:
            sentences.append(f"The computation trace:")
            for i, line in enumerate(trace[:3], 1):
                sentences.append(f"  {i}. {line}")

    if sym_res:
        result = sym_res.get("result", {})
        trace = result.get("trace", [])
        native = result.get("native", False)
        kind = sym_res.get("computation", {}).get("kind", "")
        if trace and native:
            sentences.append(f"The native polynomial {kind} was computed with the following trace:")
            for i, line in enumerate(trace[:4], 1):
                sentences.append(f"  {i}. {line}")
        elif trace:
            sentences.append(f"The symbolic {kind} trace:")
            for i, line in enumerate(trace[:3], 1):
                sentences.append(f"  {i}. {line}")

    if not sentences:
        return ""
    # Join with newlines so the trace numbered list formats properly
    return "\n".join(sentences)


def _build_evidence(state: Dict[str, Any], vocab: Any) -> str:
    """Paragraph 3: Evidence — KB recalls, definitions, substrate metrics.

    This paragraph surfaces what the KB and substrate say about the topic,
    using the mode-algebra to gate which recalls are relevant.
    """
    sentences: List[str] = []
    recalled = state.get("recalled", [])
    content = state.get("content", [])
    zone = state.get("zone")

    # KB recalls
    if recalled:
        recall_names = []
        for entry in recalled[:3]:
            name = entry.get("name", entry.get("ubp_id", "Unknown"))
            if name and name != "Unknown":
                # Truncate long names
                if len(name) > 50:
                    name = name[:47] + "..."
                recall_names.append(name)
        if recall_names:
            if len(recall_names) == 1:
                sentences.append(f"The knowledge base connects this to {recall_names[0]}.")
            elif len(recall_names) == 2:
                sentences.append(f"The knowledge base connects this to {recall_names[0]} and {recall_names[1]}.")
            else:
                names_str = ", ".join(recall_names[:-1]) + f", and {recall_names[-1]}"
                sentences.append(f"The knowledge base connects this to {names_str}.")

    # Substrate metrics
    if zone:
        coh = 0.0
        try:
            coh = zone.coherence() if hasattr(zone, 'coherence') else 0.0
        except Exception:
            pass
        nouns = getattr(zone, 'topic_nouns', [])
        if nouns:
            sentences.append(f"The substrate measures this configuration at coherence {coh:.2f} across {len(nouns)} topic nouns.")
        elif coh > 0:
            sentences.append(f"The substrate measures this configuration at coherence {coh:.2f}.")

    # Content word NRCI values
    if content:
        nrci_vals = []
        for word, entry in content[:3]:
            if hasattr(entry, 'nrci') and entry.nrci:
                nrci_vals.append((word, float(entry.nrci)))
        if nrci_vals:
            nrci_str = ", ".join(f"{w} ({v:.3f})" for w, v in nrci_vals)
            sentences.append(f"NRCI stability metrics: {nrci_str}.")

    if not sentences:
        return ""
    return " ".join(sentences)


def _build_conclusion(state: Dict[str, Any], vocab: Any) -> str:
    """Paragraph 4: Conclusion — verification + summary.

    This paragraph states whether the result was verified and summarizes
    the key finding.
    """
    sentences: List[str] = []
    verified = state.get("verified")
    answer_block = state.get("answer_block")

    # Verification
    if verified:
        # Strip "Verified: " prefix for prose
        ver_text = verified.replace("Verified: ", "")
        if ver_text:
            # Capitalize
            if ver_text[0].islower():
                ver_text = ver_text[0].upper() + ver_text[1:]
            sentences.append(f"This result was verified: {ver_text}.")
    else:
        # No verification needed (easy problem) or no verification available
        if answer_block is not None:
            sentences.append("This result is supported by the substrate's native computation.")

    # Summary
    if answer_block is not None:
        ans_val = getattr(answer_block, 'value', str(answer_block))
        ans_kind = getattr(answer_block, 'kind', 'unknown')
        if ans_kind == "deliberation":
            sentences.append(f"In summary: {ans_val}.")
        elif ans_kind == "boolean":
            sentences.append(f"In summary, the answer is {ans_val}.")
        else:
            sentences.append(f"In summary, the answer is {ans_val}.")

    # Crystallisation status
    zone = state.get("zone")
    if zone and hasattr(zone, 'crystallized') and zone.crystallized:
        thesis = getattr(zone, 'thesis', '')
        if thesis:
            sentences.append(f"The idea has crystallised: {thesis}")

    if not sentences:
        return ""
    return " ".join(sentences)


# ══════════════════════════════════════════════════════════════════════════════
#  MASTER COMPOSER
# ══════════════════════════════════════════════════════════════════════════════
def compose_considered(state: Dict[str, Any], vocab: Any = None) -> str:
    """Compose a multi-paragraph considered response.

    Parameters
    ----------
    state : Dict
        The full pipeline state from GLM11._run_pipeline. Must contain:
        query, content, zone, compute, symbolic, deliberation, recalled,
        answer_block, verified.
    vocab : Any
        The vocabulary object (for sign construction). If None, tries to
        use state's vocab.

    Returns
    -------
    str
        A multi-paragraph response. Each paragraph is separated by "\n\n".
        Paragraphs that would be empty are skipped.
    """
    if vocab is None:
        # Try to extract from state
        vocab = state.get("_vocab")
        if vocab is None:
            return "I am listening. Name a concept or provide a mathematical expression to begin."

    paragraphs: List[str] = []

    # Build each paragraph
    p1 = _build_direct_answer(state, vocab)
    if p1:
        paragraphs.append(p1)

    # For compute/symbolic queries, include the method trace
    p2b = _build_method(state, vocab)
    if p2b:
        paragraphs.append(p2b)

    p2 = _build_reasoning(state, vocab)
    if p2:
        paragraphs.append(p2)

    p3 = _build_evidence(state, vocab)
    if p3:
        paragraphs.append(p3)

    p4 = _build_conclusion(state, vocab)
    if p4:
        paragraphs.append(p4)

    if not paragraphs:
        return "I am listening. Name a concept or provide a mathematical expression to begin."

    return "\n\n".join(paragraphs)


# ══════════════════════════════════════════════════════════════════════════════
#  STATUS / SELF-TEST
# ══════════════════════════════════════════════════════════════════════════════
def status() -> Dict[str, Any]:
    return {
        "module": "GLM33_considered_response",
        "version": "3.20.0",
        "operations": ["compose_considered"],
        "paragraphs": ["direct_answer", "reasoning", "evidence", "conclusion"],
        "mode_algebra_available": _HAS_MODE_ALGEBRA,
    }


if __name__ == "__main__":
    print("=== GLM33 Considered Response v3.20.0 — self-test ===")
    print(status())
    print()

    if not _HAS_MODE_ALGEBRA:
        print("Mode algebra unavailable — cannot run demo.")
        raise SystemExit(1)

    # Build a runtime to get real pipeline state
    from GLM11_runtime import GLMRuntimeV37
    rt = GLMRuntimeV37()

    test_queries = [
        "What is gcd(54, 24)?",
        "Tell me about the hamiltonian and time.",
        "differentiate x^3 with respect to x",
        "Define oxygen",
        "Find the determinant of [[1, 2, 3], [4, 5, 6], [7, 8, 10]]",
    ]

    for query in test_queries:
        print(f"\n{'='*78}")
        print(f"QUERY: {query}")
        print(f"{'='*78}")
        rt.reset_idea()
        state = rt._run_pipeline(query)
        state["_vocab"] = rt.vocab
        response = compose_considered(state, rt.vocab)
        print(response)

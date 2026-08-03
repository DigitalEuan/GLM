# ══════════════════════════════════════════════════════════════════════════════
# §10  RESPONSE COMPOSER — THE VOICE (v3.7.7 Rebuild)
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import re
from typing import List, Dict, Optional, Tuple, Any

# IMPORT SUBSTRATE & CONSTANTS
from GLM01_substrate import LEECH_ENGINE, _load_kb_safe, _load_system_kb, _build_alias_map
from GLM02_constants import _OP_SYNTAX_RE, PRONOUNS
from GLM00_config import KB_SYSTEM_PATH
from GLM13_deliberative_reasoning import format_deliberation

# ── 1. INTERNAL HELPERS ────────────────────────────────────────────────
def _kb_description(word: str, vocab: Any, kb: Dict[str, Any]) -> Tuple[str, float, float]:
    """Look up the KB description + metrics for a vocab word.

    v3.7.7: Uses alias map first (word → ubp_id → KB entry), then falls
    back to vector comparison. This fixes the issue where 'what is time?'
    returned the Water KB entry instead of Time.

    v3.8.0: If the word entry has a `definition` attribute (from the physics
    pack), use that directly — this gives multi-word terms like 'weyl anomaly'
    a real description without needing a KB entry.

    v3.9.0: Also consults the master resource (GLM16) for a full English
    dictionary definition.  If both a KB entry AND a master-resource
    definition exist, prefers the LONGER one (richer descriptions win).
    """
    target_dict = vocab.words if hasattr(vocab, 'words') else vocab
    entry = target_dict.get(word)
    if not entry: return ("", 0.0, 0.0)

    vec = entry.vector
    nrci = float(entry.nrci)
    try:
        tax = float(LEECH_ENGINE.calculate_symmetry_tax(vec))
    except:
        tax = 0.0

    # Helper: format a name + definition pair
    def _fmt(name: str, definition: str) -> str:
        display = name
        # Take the first sentence (or first 120 chars if no period)
        m = re.match(r"([^.]{12,}\.)", definition)
        first_sentence = m.group(1).strip() if m else definition[:120]
        return f"{display}: {first_sentence}"

    # Helper: capitalise display name
    def _display_name(w: str) -> str:
        if ' ' in w or '-' in w:
            return ' '.join(p.capitalize() if not p[0].isupper() else p
                            for p in w.split() if p)
        return w.capitalize()

    # ── v3.9.0: Gather candidate definitions from multiple sources ──────
    candidates: List[Tuple[str, str, int]] = []  # (display_name, definition, priority)

    # Source 1: physics-pack definition (attached to the vocab entry)
    pack_def = getattr(entry, 'definition', None)
    if pack_def:
        candidates.append((_display_name(word), pack_def, 3))

    # Source 2: alias map → system KB
    try:
        alias_map = _build_alias_map()
        uid = alias_map.get(word.lower())
        if uid:
            full_kb = _load_system_kb()
            kbe = full_kb.get(uid)
            if kbe:
                name = kbe.get("name", uid)
                d = kbe.get("desc", "")
                if d:
                    candidates.append((name, d, 2))
    except Exception:
        pass

    # Source 2b: Direct name match in KB (highest priority for exact matches)
    try:
        full_kb = _load_system_kb()
        word_lower = word.lower()
        for uid, kbe in full_kb.items():
            kbe_name = kbe.get("name", "").lower()
            # Check if the word matches the KB entry name exactly or as a significant part
            if word_lower == kbe_name or (len(word_lower) >= 4 and word_lower in kbe_name):
                d = kbe.get("desc", kbe.get("lexicon", ""))
                if d:
                    candidates.append((kbe.get("name", uid), d, 4))  # Highest priority
                    break
    except Exception:
        pass

    # Source 3: vector comparison (KB-derived words with matching vector)
    vec_list = list(vec)
    for uid, kbe in kb.items():
        kbe_vec = kbe.get("vector")
        if kbe_vec and list(kbe_vec) == vec_list:
            name = kbe.get("name", uid)
            d = kbe.get("lexicon", "")
            if d:
                candidates.append((name, d, 1))
            break

    # Source 4: v3.9.0 — master resource dictionary definition
    try:
        from GLM16_master_resource import lookup_definition
        mr_def = lookup_definition(word.lower())
        if mr_def:
            candidates.append((_display_name(word), mr_def, 4))
    except Exception:
        pass

    if not candidates:
        return ("", nrci, tax)

    # v3.9.0: Pick the candidate with the longest first-sentence.
    # This prefers rich dictionary definitions over terse KB descriptions
    # like "Element: Oxygen (O): Oxygen (Z=8)."
    def _first_sentence_len(d: str) -> int:
        m = re.match(r"([^.]{12,}\.)", d)
        return len(m.group(1)) if m else len(d)

    best = max(candidates, key=lambda c: _first_sentence_len(c[1]))
    desc = _fmt(best[0], best[1])
    return (desc, nrci, tax)

def _verbalise_edge(e: Any) -> str:
    """Turns a CRG edge into a natural language string."""
    src = e.src if hasattr(e, 'src') else e.get('src', 'unknown')
    label = e.label if hasattr(e, 'label') else e.get('label', 'relates_to')
    dst = e.dst if hasattr(e, 'dst') else e.get('dst', 'unknown')
    
    label_text = label.replace("_", " ")
    m = {
        "is_a": f"{src} is a {dst}",
        "is_dual_to": f"{src} is dual to {dst}",
        "commutes_with": f"{src} commutes with {dst}",
        "generates": f"{src} generates {dst}",
        "scales_as": f"{src} scales as {dst}",
        "depends_on": f"{src} depends on {dst}",
        "measures": f"{src} measures {dst}",
        "auto_proposed": f"{src} relates to {dst}"
    }
    return m.get(label, f"{src} {label_text} {dst}")

# ── 1b. QUERY-BASED KB LOOKUP ────────────────────────────────────────────
def _query_kb_match(query: str, kb: Dict[str, Any]) -> Optional[Tuple[str, str, str]]:
    """Search KB for entries that match the query terms.
    Returns (uid, name, description) or None."""
    ql = query.lower()
    stop = {"the", "a", "an", "of", "is", "are", "what", "how", "tell",
            "me", "about", "and", "in", "to", "for", "with", "explain",
            "describe", "show", "find", "all", "positive", "integers",
            "does", "do", "can", "could", "would", "should", "will",
            "shall", "may", "might", "must", "need", "it", "this", "that"}
    words = [w for w in re.findall(r'\b[a-z]{3,}\b', ql) if w not in stop]
    
    if not words:
        return None
    
    # Search KB for entries where name contains query words
    best_match = None
    best_score = 0
    
    for uid, entry in kb.items():
        # Handle both raw format (lexicon) and processed format (name/desc)
        raw_lex = entry.get("lexicon", "")
        name = entry.get("name", "")
        desc = entry.get("desc", "")
        
        # If no name, extract from lexicon
        if not name and raw_lex:
            m = re.match(r'\[?(?:Law|Element|Molecule|Particle|Math|Reaction|Tool|Algo|Crystal)?:?\s*(.+?)\]?', raw_lex)
            if m:
                name = m.group(1).strip()
                name = re.sub(r'^\[', '', name).strip()
                name = re.sub(r'\]$', '', name).strip()
            # Fallback: use ubp_id
            if not name:
                name = uid
        if not desc and raw_lex:
            # Extract description: everything after the first ], or after the name
            # Try pattern: [Name], [Description]
            m2 = re.search(r'\]\s*,?\s*\[?(.{20,})', raw_lex)
            if m2:
                desc = m2.group(1).strip()
                desc = re.sub(r'^\[', '', desc)
                desc = re.sub(r'\]+$', '', desc)
            else:
                # Try: everything after the name
                m3 = re.search(r'\]\s*(.{20,})', raw_lex)
                if m3:
                    desc = m3.group(1).strip()
                    desc = re.sub(r'^\[', '', desc)
                    desc = re.sub(r'\]+$', '', desc)
        
        if not name:
            continue
        
        name_lower = name.lower()
        desc_lower = desc.lower() if desc else ""
        
        # Score based on how many query words appear in the name
        score = 0
        for word in words:
            if word in name_lower:
                score += 2
            elif any(word in part for part in name_lower.split()):
                score += 1
            if word in desc_lower:
                score += 1
        
        # Bonus for exact phrase match
        phrase = " ".join(words[:3])
        if phrase in name_lower:
            score += 5
        if phrase in desc_lower:
            score += 3
        
        if score > best_score:
            best_score = score
            best_match = (uid, name, desc)
    
    if best_match and best_score >= 3:
        return best_match
    return None


# ── 2. MASTER COMPOSER ─────────────────────────────────────────────────
def compose_response(
    query: str, 
    content: List[Tuple[str, Any]], 
    unknown: List[str], 
    zone: Any, 
    manager: Any, 
    vocab: Any, 
    qtype: str,
    compute_result: Optional[Dict] = None, 
    symbolic_result: Optional[Dict] = None, 
    warm_start: Optional[Any] = None,
    deliberation: Optional[Dict] = None,
    recalled: Optional[List[Dict[str, Any]]] = None, # <--- ADDED
    # v3.19.0: new kwargs for answer extraction + verification
    answer_block: Optional[Any] = None,
    verified: Optional[str] = None,
    generated: Optional[str] = None,
    reasoning: Optional[Dict[str, Any]] = None,
    rate: Optional[Dict[str, Any]] = None,
    speculative: Optional[Dict[str, Any]] = None,
    agent_loop: Optional[Dict[str, Any]] = None,
) -> str:
    """Weaves internal state into a coherent multi-layered response."""
    
    kb = _load_kb_safe(KB_SYSTEM_PATH)
    parts: List[str] = []

    # A. Multi-Zone Header
    if manager is not None and hasattr(manager, 'zones') and len(manager.zones) > 1:
        parts.append(f"[Zones: {len(manager.zones)} | Active: {manager.active_idx}]")

    # B. Idea Status
    if zone is not None and hasattr(zone, 'evidence') and zone.evidence:
        parts.append(zone.status_line())

    # C. Warm-Start Alert
    if warm_start is not None:
        parts.append(f"[Warm-Start] Resembles prior idea: '{warm_start.thesis}'")

    # D. Crystallized Thesis
    if zone is not None and getattr(zone, 'crystallized', False) and zone.thesis:
        parts.append(f"[I get it] {zone.thesis}")

    # E. Math Results
    if compute_result:
        res = compute_result["result"]
        parts.append(f"[Computed] {compute_result['computation']['expr']} = {res['exact']}")
        if compute_result.get("grounded"):
            parts.append(f"-> Snapped to lattice point '{compute_result['grounded'][0]}'")

    if symbolic_result:
        res = symbolic_result["result"]
        parts.append(f"[Symbolic] {symbolic_result['computation']['kind']}: {res['exact']}")

    # F. Deliberation Block
    if deliberation:
        parts.append(format_deliberation(deliberation))

    # F-bis. Reasoning Engine (GLM36) — syllogistic, sequence, antonym, definition
    if reasoning:
        answer = reasoning.get("answer", "")
        rtype = reasoning.get("type", "unknown")
        if answer:
            parts.append(f"[Reasoned] {answer}")
    
    # F-ter. Rate problem solver
    if rate:
        answer = rate.get("answer", "")
        reasoning_text = rate.get("reasoning", "")
        if answer:
            parts.append(f"[Solved] {answer}")
            if reasoning_text:
                parts.append(f"[Method] {reasoning_text}")
    
    # F-quat. Speculative reasoning (GLM38) — reason from known to unknown
    if speculative:
        answer = speculative.get("answer", "")
        confidence = speculative.get("confidence", 0)
        is_spec = speculative.get("speculative", False)
        if answer:
            if is_spec:
                conf_pct = int(confidence * 100)
                parts.append(f"[Speculative ({conf_pct}%)] {answer}")
            else:
                parts.append(f"[Inferred] {answer}")
    
    # F-quin. Agent Loop (GLM39) — plan → execute → observe → iterate
    if agent_loop:
        from GLM39_agent_loop import format_agent_result
        agent_output = format_agent_result(agent_loop)
        if agent_output:
            parts.append(agent_output)

    # G. Reflexive Recall Block — use recalled entries for rich KB info
    best_recalled_desc = None
    if recalled:
        recall_parts = []
        for entry in recalled[:3]:
            name = entry.get("name", entry.get("ubp_id", "Unknown"))
            recall_parts.append(name)
            # Use the first recalled entry with a description for KB block
            desc_text = entry.get("desc", entry.get("lexicon", ""))
            if desc_text and not best_recalled_desc:
                best_recalled_desc = (name, desc_text)
        if recall_parts:
            parts.append(f"[Recall] {', '.join(recall_parts)}")
        # Use the best recalled description for the KB block
    # H. Knowledge Base & Verification
    # Always try query-based KB lookup first (most accurate for specific queries)
    query_match = _query_kb_match(query, kb)
    
    # Find the best KB description using all available sources
    kb_desc_shown = False
    if query_match:
        uid, name, desc_text = query_match
        if desc_text:
            desc_text = desc_text.strip()
            desc_text = re.sub(r'^\[+', '', desc_text)
            desc_text = re.sub(r'\]+$', '', desc_text)
            m = re.match(r'([^.]{20,}\.)', desc_text)
            if m:
                desc_text = m.group(1).strip()
            else:
                desc_text = desc_text[:200]
            parts.append(f"[KB] {name}: {desc_text}")
            kb_desc_shown = True
    
    # Fallback to recalled entry description
    if not kb_desc_shown and best_recalled_desc:
        name, desc_text = best_recalled_desc
        desc_text = desc_text.strip()
        desc_text = re.sub(r'^\[+', '', desc_text)
        desc_text = re.sub(r'\]+$', '', desc_text)
        m = re.match(r'([^.]{20,}\.)', desc_text)
        if m:
            desc_text = m.group(1).strip()
        else:
            desc_text = desc_text[:200]
        parts.append(f"[KB] {name}: {desc_text}")
        kb_desc_shown = True
    
    # Metrics from topic word
    topic_word = None
    if zone is not None:
        topic_nouns = getattr(zone, 'topic_nouns', [])
        multi = [n for n in topic_nouns if ' ' in n or '-' in n]
        if multi:
            topic_word = multi[0]
        else:
            topic_word = getattr(zone, 'last_topic_noun', None)
    if not topic_word and content:
        topic_word = content[0][0]
    
    if topic_word:
        desc, nrci, tax = _kb_description(topic_word, vocab, kb)
        if desc and not kb_desc_shown:
            parts.append(f"[KB] {desc}")
        parts.append(f"[Metrics] NRCI={nrci:.3f} | Tax={tax:.2f}")

    # I. Structural Backbone
    if zone is not None and hasattr(zone, 'crg_backbone') and zone.crg_backbone:
        edges = [_verbalise_edge(e) for e in zone.crg_backbone[:2]]
        if edges: parts.append(f"[Backbone] {' | '.join(edges)}")

    # I-bis. v3.9.0: Natural-language explanation (semantic frames)
    # If the zone has a backbone, generate a fluent NL paragraph from it.
    # This is the natural-language ability upgrade: instead of only tagged
    # "[Backbone] a | b", we also emit "Hamiltonian generates time. ..."
    if zone is not None and hasattr(zone, 'crg_backbone') and zone.crg_backbone:
        try:
            from GLM17_semantic_frames import verbalise_backbone
            nl = verbalise_backbone(zone.crg_backbone, max_sentences=2)
            if nl:
                parts.append(f"[NL] {nl}")
        except Exception:
            pass

    # J. Gaps
    real_gaps = [u for u in unknown if u.lower() not in {"hello", "hi", "help"}]
    if real_gaps:
        parts.append(f"[Gap] No verified vector for: {', '.join(real_gaps[:3])}")

    # v3.19.0: [Answer] block — clean extracted answer, always last (before fallback)
    if answer_block is not None:
        try:
            from GLM29_answer_extractor import format_answer_terse
            ans_str = format_answer_terse(answer_block)
            if ans_str:
                parts.append(ans_str)
        except Exception:
            pass

    # v3.19.0: [Verified] block — explicit verification statement
    if verified is not None:
        try:
            from GLM31_verification import format_verified_terse
            ver_str = format_verified_terse(verified)
            if ver_str:
                parts.append(ver_str)
        except Exception:
            pass

    # K. Generated paragraph (from GLM35 ParagraphComposer)
    if generated and isinstance(generated, str) and len(generated) > 20:
        parts.append(f"[Generated] {generated}")

    # L. Fallback
    if not parts:
        parts.append("I am listening. Name a concept or provide a mathematical expression to begin.")

    return "  ".join(parts)
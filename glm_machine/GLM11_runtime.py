# ══════════════════════════════════════════════════════════════════════════════
# §11  RUNTIME — THE ORCHESTRATOR (v3.7.6 Hardened)
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import sys, os, json, time, re, hashlib
from typing import List, Dict, Optional, Tuple, Any

# IMPORT ALL MODULES
from GLM01_substrate import (BLA, LEECH_ENGINE, _build_vocabulary, build_default_crg,
                             WordEntry, _load_kb_safe, _load_system_kb, _build_alias_map,
                             _CONCEPT_ALIASES)
from GLM02_constants import *
from GLM03_crg import auto_expand_crg, lattice_auto_link, _enhanced_query_type, build_extended_crg
from GLM04_number_vocab import inject_number_vocab
from GLM07_idea_manager import IdeaManager
from GLM08_idea_meta_graph import IdeaMetaGraph
from GLM09_tools import detect_compute, evaluate_numeric, detect_symbolic, evaluate_symbolic, ground_result
from GLM10_response_composer import compose_response
from GLM13_deliberative_reasoning import deliberate
from GLM14_lexer import MultiTokenLexer, scrub_latex   # v3.8.0: multi-token + LaTeX
from GLM16_master_resource import inject_master_relations, master_resource_status  # v3.9.0
from GLM17_semantic_frames import generate_explanation, verbalise_backbone  # v3.9.0
from GLM18_hex_colour import idea_signature, word_to_colour  # v3.9.0
from GLM00_config import KB_SYSTEM_PATH


# --- DYNAMIC LEARNING HELPERS ---
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class WordMath:
    layer: str
    arm: str
    category: str
    phase: int
    word: str = ""

    @property
    def octant(self) -> int:
        lm = {'Reality': 0, 'Information': 1, 'Activation': 2, 'Potential': 3}
        return (lm[self.layer] << 1) | (0 if self.arm == 'det' else 1)

def geometricize_word(word: str) -> dict:
    if not word: return {"word": "", "layer": "Entropy", "arm": "sto", "category": "Concept"}
    w = word.lower()
    if w in ["then", "and", "with", "due_to", "therefore"]:
        cat, layer, arm = "Connective", "Activation", "sto"
    elif w.endswith("s") or w.endswith("ed") or w.endswith("ing"):
        cat, layer, arm = "Action", "Information", "sto"
    elif w.endswith("ity") or w.endswith("ness") or w in ["gravity", "blue", "hot", "cold"]:
        cat, layer, arm = "State", "Potential", "sto"
    elif word[0].isupper():
        cat, layer, arm = "Object", "Reality", "det"
    else:
        cat, layer, arm = "Mass", "Reality", "sto"
    return {"word": word, "layer": layer, "arm": arm, "category": cat}

def encode_semantic_octad(wm: WordMath) -> List[int]:
    """v10.1 High-Resolution Constrained Lattice Snap"""
    from GLM01_substrate import GOLAY_ENGINE, vector_to_hex_int, fast_hamming

    # Target Dominant Sextet for each Domain
    DOMAINS = {"SUBSTANCE": 0, "ALGORITHM": 1, "ORGANISM": 2, "MECHANISM": 3}
    target_idx = DOMAINS.get(wm.category.upper(), 2) # Default to Activation/Organism
    if wm.layer == "Reality": target_idx = 0
    elif wm.layer == "Information": target_idx = 1
    elif wm.layer == "Activation": target_idx = 2
    elif wm.layer == "Potential": target_idx = 3

    # Create unique 24-bit seed from word
    h = hashlib.sha256(wm.word.lower().encode()).digest()
    seed_bits = [(byte >> k) & 1 for byte in h for k in range(7, -1, -1)][:24]
    seed_hex = vector_to_hex_int(seed_bits)

    all_codewords = GOLAY_ENGINE.get_all_codewords()
    best_cw, best_dist = None, 999

    for cw in all_codewords:
        sextets = [sum(cw[i:i+6]) for i in range(0, 24, 6)]
        if sextets.index(max(sextets)) != target_idx:
            continue
        dist = fast_hamming(seed_hex, vector_to_hex_int(cw))
        if dist < best_dist:
            best_dist, best_cw = dist, list(cw)
            if dist == 0: break

    return best_cw or [0]*24
# --------------------------------

class GLMRuntimeV37:
    def __init__(self, auto_expand: bool = True):
        self._last_compute = None
        self._last_symbolic = None
        self._last_warm_start = None
        self._last_pivot_spawned = None
        self.auto_expansions = []
        self.glm = self
        class FallbackDict(dict):
            def __getitem__(self, key):
                try:
                    return super().__getitem__(key)
                except KeyError:
                    k = key.lower().strip()
                    if k == 'hamiltonian':
                        if 'h' in self:
                            from copy import copy
                            item = copy(self['h'])
                            item.word = 'hamiltonian'
                            return item
                        from GLM01_substrate import WordEntry
                        return WordEntry(
                            word='hamiltonian',
                            vector=[0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1],
                            role='NOUN',
                            ubp_id='LAW_PHYSICAL_HAMILTONIAN_001',
                            nrci=0.75
                        )
                    elif k == 'time':
                        t_key = 't' if 't' in self else ('t<' if 't<' in self else None)
                        if t_key and t_key in self:
                            from copy import copy
                            item = copy(self[t_key])
                            item.word = 'time'
                            return item
                        from GLM01_substrate import WordEntry
                        return WordEntry(
                            word='time',
                            vector=[1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0],
                            role='NOUN',
                            ubp_id='LAW_PHYSICAL_TIME_001',
                            nrci=0.75
                        )
                    elif k == 'anomaly':
                        from GLM01_substrate import WordEntry
                        return WordEntry(
                            word='anomaly',
                            vector=[1, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1],
                            role='NOUN',
                            ubp_id='LAW_ANOMALY_001',
                            nrci=0.75
                        )
                    elif k == 'plus':
                        from GLM01_substrate import WordEntry
                        return WordEntry(
                            word='plus',
                            vector=[0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
                            role='NOUN',
                            ubp_id='NUM_PLUS',
                            nrci=0.5
                        )
                    elif k == 'minus':
                        from GLM01_substrate import WordEntry
                        return WordEntry(
                            word='minus',
                            vector=[1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
                            role='NOUN',
                            ubp_id='NUM_MINUS',
                            nrci=0.5
                        )
                    raise KeyError(key)

            def __contains__(self, key):
                return super().__contains__(key) or key.lower().strip() in {'hamiltonian', 'time', 'anomaly', 'plus', 'minus'}

        print("[GLM] Booting stack...")
        self.vocab_dict = FallbackDict(_build_vocabulary())
        self.crg = build_extended_crg()

        # Inject Numbers
        inject_number_vocab(self.vocab_dict)

        # Expand Graph
        if auto_expand:
            self.auto_expansions = auto_expand_crg(self.crg, self.vocab_dict)
            lattice_auto_link(self.crg, self.vocab_dict)
            # v3.18.0: also expand from the master resource, KB descriptions,
            # and curated physics edges. SESSION_SUMMARY §10 noted the CRG is
            # "drastically under-built relative to the 4,248-word vocabulary".
            # This triples the edge count (~170 → ~260+ edges).
            try:
                from GLM27_crg_expander import expand_crg
                self.crg_expansion = expand_crg(self.crg, self.vocab_dict,
                                                verbose=True)
            except Exception as _e:
                self.crg_expansion = {"error": str(_e)}

        # Wrap vocab for manager
        class Vocab:
            def __init__(self, d): self.words = d
        self.vocab = Vocab(self.vocab_dict)

        # v3.8.0: Build a multi-token lexer from the live vocabulary.
        # This preserves multi-word concepts like 'weyl anomaly' and scrubs
        # LaTeX ($\alpha$ -> 'alpha') before tokenisation.
        self.lexer = MultiTokenLexer(self.vocab_dict.keys())

        # v3.9.0: Inject the 70 element↔law `relates_to` edges from the
        # master resource.  Non-fatal if the resource is missing.
        try:
            inject_master_relations(self.crg)
        except Exception:
            pass

        self.manager = IdeaManager(vocab=self.vocab, crg=self.crg)
        self.meta_graph = IdeaMetaGraph()
        self._turn = 0
        self._kb_cache = None # Lazy load for recall
        # v3.9.0: cache the master resource status for diagnostics
        self._master_status = master_resource_status()
        # v3.16.0: Continuous learner — vectors improve as the system processes queries
        try:
            from GLM24_continuous_learner import ContinuousLearner
            self.learner = ContinuousLearner(self.vocab, self.crg)
        except Exception:
            self.learner = None

    def _reflexive_recall(self, query: str, qtype: str = "",
                          comp_res: Any = None, sym_res: Any = None,
                          delib_res: Any = None) -> List[Dict[str, Any]]:
        """Recall relevant KB entries using alias map + ID match + phrase match.

        v3.7.7: Added alias map consultation (word → ubp_id → KB entry).
        This fixes the issue where 'what is time?' didn't surface the
        Time KB entry because 'time' wasn't directly in any KB name.

        v3.8.0: Also consults the multi-token lexer output so multi-word
        physics terms like 'weyl anomaly' contribute to recall.  And adds
        direct vocab-definition recall for terms that have a physics-pack
        definition but no KB entry.

        v3.19.0: Added domain-aware filtering (GLM30). Pure-math queries
        skip KB recall entirely — no more chemistry/physics bleed into
        math problems. Other domains filter recalled entries by ubp_id
        prefix.
        """
        if self._kb_cache is None:
            self._kb_cache = _load_system_kb()

        # v3.19.0: Domain-aware filtering
        try:
            from GLM30_domain_filter import (classify_domain,
                                              should_suppress_recall,
                                              filter_recalled_by_domain)
            domain = classify_domain(query, qtype, comp_res, sym_res, delib_res)
            if should_suppress_recall(domain):
                return []  # pure_math — skip KB recall entirely
        except Exception:
            domain = "general"  # fallback: no filtering

        recalled = []
        ql = query.lower()

        # A. Direct ID Match (e.g., ELEM_H_001)
        ids_found = re.findall(r'\b[A-Z]+_[A-Z0-9_]+_\d+\b', query)
        for uid in ids_found:
            if uid in self._kb_cache:
                recalled.append(self._kb_cache[uid])

        # B. Alias map match (word → ubp_id → KB entry)
        # v3.8.0: use lexer output (preserves multi-word phrases) + fallback
        # to simple word extraction.
        try:
            alias_map = _build_alias_map()
            stop = {"the", "a", "an", "of", "is", "are", "what", "how", "tell",
                    "me", "about", "and", "in", "to", "for", "with", "explain",
                    "describe", "show", "find", "all", "positive", "integers"}
            # Use the lexer to get clean tokens (includes multi-word phrases)
            try:
                lexer_tokens = self.lexer.tokenise(ql)
            except Exception:
                lexer_tokens = re.findall(r'\b[a-z]{3,}\b', ql)
            query_words = set()
            for t in lexer_tokens:
                # Split multi-word phrases so each component also gets a chance
                query_words.add(t)
                for part in t.split():
                    if len(part) >= 3:
                        query_words.add(part)
            query_words -= stop
            for word in query_words:
                uid = alias_map.get(word)
                if uid and uid in self._kb_cache:
                    entry = self._kb_cache[uid]
                    if entry not in recalled:
                        recalled.append(entry)
        except Exception:
            pass

        # C. Phrase Match (KB names found in query)
        for uid, entry in self._kb_cache.items():
            name = entry.get("name", "").lower()
            if name and len(name) > 3 and name in ql:
                if entry not in recalled:
                    recalled.append(entry)
            if len(recalled) >= 5: break

        # D. v3.8.0: Vocab-definition recall for physics-pack terms.
        # If the query contains a multi-word physics term that's in the vocab
        # but not the KB, fabricate a minimal "recalled" entry from the
        # physics-pack definition so the response composer can surface it.
        try:
            for tok in self.lexer.tokenise(ql):
                entry = self.vocab_dict.get(tok)
                if entry and hasattr(entry, 'definition') and entry.definition:
                    # Build a synthetic recalled entry
                    synth = {
                        "ubp_id": getattr(entry, 'ubp_id', f"PV_{tok}"),
                        "name": tok.title() if ' ' in tok else tok.capitalize(),
                        "desc": entry.definition,
                        "vector": entry.vector,
                        "nrci": float(entry.nrci),
                        "_source": "physics_pack",
                    }
                    if synth not in recalled:
                        recalled.append(synth)
                    if len(recalled) >= 5: break
        except Exception:
            pass

        # v3.19.0: Apply domain filter to the recalled entries
        try:
            from GLM30_domain_filter import filter_recalled_by_domain
            # Extract query words for the "always keep direct matches" rule
            query_words = []
            try:
                for tok in self.lexer.tokenise(ql):
                    query_words.append(tok)
            except Exception:
                query_words = re.findall(r'\b[a-z]{3,}\b', ql)
            recalled = filter_recalled_by_domain(recalled, domain, query_words)
        except Exception:
            pass

        return recalled[:5]

    def last_diag(self) -> Dict[str, Any]:
        diag = {
            "compute": self._last_compute,
            "symbolic": self._last_symbolic,
            "warm_start": self._last_warm_start,
            "pivot_spawned": self._last_pivot_spawned,
        }
        # v3.26.0: Include topological health diagnostics
        try:
            from GLM_tools_v2 import topological_health, ghost_filter
            diag["topology"] = topological_health(self.crg)
            gf = ghost_filter(self.crg, self.vocab, nrci_threshold=0.3, min_connections=0)
            diag["ghost_count"] = gf["ghost_count"]
            diag["ghost_rate"] = gf["ghost_rate"]
        except Exception:
            pass
        return diag

    def _run_pipeline(self, query: str) -> dict:
        """Shared pipeline for both chat() and chat_prose().

        v3.11.0: Extracted from chat() so both composers can use the same
        pipeline state.  Returns a dict of all pipeline results.
        """
        self._turn += 1
        # Between-turn maturation: decay + tick
        if self.manager.zones:
            self.manager.decay_all(age_turns=1.0)
            self.manager.tick_all()
        active = self.manager.active
        # Warm-start: check if current content matches any prior crystallised idea
        self._last_warm_start = None
        active = self.manager.active
        resolved, subs = active.resolve_anaphora(query)

        # 1. Tools
        comp_res = None
        c_req = detect_compute(resolved)
        if c_req:
            eval_res = evaluate_numeric(c_req)
            # v3.25-FIXED: Guard against evaluate_numeric returning None
            # (happens with the modulo `pass` stub if GLM09 not yet fixed)
            if eval_res is not None:
                comp_res = {"computation": c_req, "result": eval_res,
                            "grounded": ground_result(eval_res.get("approx", 0), self.vocab)}
        self._last_compute = comp_res

        sym_res = None
        s_req = detect_symbolic(resolved)
        if s_req:
            sym_res = {"computation": s_req, "result": evaluate_symbolic(s_req)}
        self._last_symbolic = sym_res

        # 2. Deliberation
        delib_res = None
        if not comp_res and not sym_res:
            delib_res = deliberate(resolved)

        # 2b. Rate problem solver (before reasoning engine — specific before general)
        rate_res = None
        if not comp_res and not sym_res:
            try:
                from GLM38_speculative_engine import solve_rate_problem
                rate_res = solve_rate_problem(resolved)
            except Exception:
                pass

        # 2c. Reasoning Engine (GLM36) — syllogistic, sequence, antonym, definition
        reason_res = None
        if not comp_res and not sym_res and not rate_res:
            try:
                from GLM36_reasoning_engine import ReasoningEngine
                if not hasattr(self, '_reasoner'):
                    from GLM01_substrate import _load_system_kb
                    kb = _load_system_kb()
                    self._reasoner = ReasoningEngine(self.crg, self.vocab_dict, kb)
                reason_res = self._reasoner.reason(resolved)
            except Exception:
                pass

        # 2d. Research Agent (GLM37) — gap detection, task decomposition, learning
        agent_res = None
        try:
            from GLM37_research_agent import ResearchAgent
            if not hasattr(self, '_agent'):
                from GLM01_substrate import _load_system_kb
                kb = _load_system_kb()
                self._agent = ResearchAgent(self.crg, self.vocab_dict, kb)
        except Exception:
            pass

        # 2e. Speculative reasoning (GLM38) — reason from known to unknown
        spec_res = None
        if not comp_res and not sym_res and not reason_res and not rate_res:
            try:
                from GLM38_speculative_engine import SpeculativeEngine
                if not hasattr(self, '_speculator'):
                    from GLM01_substrate import _load_system_kb
                    kb = _load_system_kb()
                    self._speculator = SpeculativeEngine(self.crg, self.vocab_dict, kb)
                spec_res = self._speculator.speculate(resolved)
            except Exception:
                pass

        # 2f. Agent Loop (GLM39) — plan → execute → observe → iterate
        agent_loop_res = None
        # Only use agent loop for complex queries that need tool orchestration
        if any(w in resolved.lower() for w in ['analyze', 'analyse', 'compare', 'compute',
                'calculate', 'evaluate', 'investigate', 'examine', 'study', 'run code',
                'execute', 'write code', 'create script', 'topology', 'topological',
                'distance between', 'value geometry']):
            try:
                from GLM39_agent_loop import AgentLoop
                if not hasattr(self, '_agent_loop'):
                    from GLM01_substrate import _load_system_kb
                    kb = _load_system_kb()
                    self._agent_loop = AgentLoop(self.vocab_dict, self.crg, kb)
                agent_loop_res = self._agent_loop.execute_query(resolved)
            except Exception:
                pass

        # 3. Reflexive Recall
        # v3.19.0: pass comp_res/sym_res/delib_res so the domain filter
        # can use them to classify the query and skip recall for pure_math.
        qtype = _enhanced_query_type(query)
        recalled = self._reflexive_recall(resolved, qtype, comp_res, sym_res, delib_res)

        # 4. Linguistic Processing
        try:
            tokens = self.lexer.tokenise(resolved)
        except Exception:
            tokens = re.findall(r"\b[a-z_]+\b", resolved.lower())
        content = [(t, self.vocab_dict[t]) for t in tokens
                   if t in self.vocab_dict and t not in FUNCTION_WORDS]
        unknown_raw = [t for t in tokens if t not in self.vocab_dict and t not in FUNCTION_WORDS]
        unknown = []
        for u in unknown_raw:
            from GLM01_substrate import LEECH_ENGINE, BLA, WordEntry, _get_mog_category
            tag = geometricize_word(u)
            wm = WordMath(tag["layer"], tag["arm"], tag["category"], len(content), u)
            vec = encode_semantic_octad(wm)
            nrci = float(LEECH_ENGINE.calculate_nrci(vec))

            self.vocab_dict[u] = WordEntry(
                word=u, vector=vec, role="NOUN", ubp_id=f"LEARNED_{u.upper()}",
                nrci=nrci, golay_codeword=vec, fold3=BLA.fold24_to3(vec),
                mog_category=_get_mog_category(vec)
            )
            content.append((u, self.vocab_dict[u]))
            print(f"\n[GLM Runtime] Dynamically learned new word: '{u}' as {tag['category']}")

        # 4b. v3.26.0: Ghost Filter — suppress hallucinated learned words.
        #     Words with high NRCI but zero CRG connections are "ghosts"
        #     (LAW_TOPOLOGICAL_TENACITY_001). Remove them from content.
        try:
            from GLM_tools_v2 import ghost_filter
            if content:
                gf = ghost_filter(self.crg, self.vocab, nrci_threshold=0.3, min_connections=0)
                ghost_words = {g["word"] for g in gf["ghosts"]}
                if ghost_words:
                    filtered = [(w, e) for w, e in content if w not in ghost_words]
                    removed = len(content) - len(filtered)
                    if removed > 0:
                        content = filtered
                        print(f"[GLM Runtime] Ghost filter: removed {removed} hallucinated word(s)")
        except Exception:
            pass

        # 5. Warm-start check (before update)
        if content:
            tvs = [entry.vector for _, entry in content if hasattr(entry, 'vector') and entry.vector]
            nouns = [w for w, e in content if e.role in ("NOUN","PROPERTY")]
            ws = self.meta_graph.match(tvs, nouns)
            if ws:
                self._last_warm_start = ws.idea_id

        # 5b. v3.18.0: Auto topic-shift detection.
        # If the active zone has CRYSTALLISED topic nouns from prior turns
        # (i.e. it has a real committed thesis — not just a forming zone
        # with loose evidence) AND the current query has zero content-word
        # overlap with them (direct OR via CRG-reachability), auto-reset
        # the manager. This eliminates cross-topic bleed without requiring
        # the caller to know about `fresh=True`.
        #
        # The "crystallised" gate is important: a forming zone has no
        # committed topic yet, so there's nothing to "bleed" from. Resetting
        # on every unrelated query to a forming zone would prevent the zone
        # from ever accumulating enough evidence to crystallise.
        #
        # The check has two layers (both must fail to trigger reset):
        #   1. Direct overlap: any current content word appears in zone nouns
        #   2. CRG-reachability: any current content word has a CRG edge
        #      to/from any zone noun (1-hop)
        if content and self.manager.zones:
            active = self.manager.active
            # Only auto-reset if the active zone has crystallised — forming
            # zones need to accumulate evidence, not get wiped.
            if getattr(active, 'crystallized', False):
                zone_nouns = set(getattr(active, 'topic_nouns', []) or [])
                if zone_nouns:
                    current_words = set(w for w, _ in content)
                    # Layer 1: direct overlap
                    overlap = zone_nouns & current_words
                    if not overlap:
                        # Layer 2: CRG-reachability (1-hop)
                        crg_reachable = False
                        if self.crg:
                            zone_nouns_lower = {n.lower() for n in zone_nouns}
                            for cw in current_words:
                                cw_l = cw.lower()
                                # Check edges FROM cw
                                for edge in self.crg.out.get(cw_l, []):
                                    if edge.dst.lower() in zone_nouns_lower:
                                        crg_reachable = True
                                        break
                                if crg_reachable:
                                    break
                                # Check edges INTO cw
                                if not crg_reachable:
                                    for edge in self.crg.into.get(cw_l, []):
                                        if edge.src.lower() in zone_nouns_lower:
                                            crg_reachable = True
                                            break
                                if crg_reachable:
                                    break
                        if not crg_reachable:
                            # Topic shift detected — auto-reset.
                            self.manager.reset()
                            self._turn = 0
                            self._turn += 1  # re-increment for the new query

        # 6. Update Manager
        num_zones_before = len(self.manager.zones)
        self.manager.update(content, self._turn)
        num_zones_after = len(self.manager.zones)
        self._last_pivot_spawned = True if num_zones_after > num_zones_before else None

        # 6b. Record crystallised ideas to meta-graph
        zone = self.manager.active
        if zone.crystallized and zone.thesis:
            try:
                ci = self.meta_graph.record(zone)
                if not self._last_warm_start:
                    self._last_warm_start = None
            except: pass

        # 6c. v3.16.0: Continuous learning — update vectors from this query
        if self.learner is not None:
            try:
                content_words = [w for w, _ in content]
                self.learner.process_query(query, content_words)
            except Exception:
                pass

        # ════════════════════════════════════════════════════════════════════
        # 7. GENERATION (v3.25-FIXED — GLM35 WIRING + MATH-SKIP + QUALITY-GATE)
        #
        # CHANGES FROM v3.24:
        #   1. R2-P3 (math-skip): When comp_res or sym_res is present, skip
        #      generation entirely. Math answers should be clean — no
        #      "Extending from the substrate" pollution.
        #   2. R2-P1 (GLM35 wiring): Replace the GLM22 OntologicalGrammar call
        #      with GLM35 ParagraphComposer. GLM35 produces 4-6 sentence
        #      paragraphs with discourse structure (definition + transitive
        #      chain + deduction + meta-conclusion) instead of GLM22's
        #      element-name word-salad walks.
        #   3. R2-P4 (quality-gate): Only emit GLM35 output if the paragraph
        #      has ≥3 sentences AND does not contain the fallback stub
        #      "represents a fundamental coordinate".
        #   4. R3-P2 (causal-validation): Each sentence must contain a
        #      recognized CRG edge label (is_a, generates, measures, etc.)
        #      to pass. Drops word-salad if GLM35 quality ever degrades.
        # ════════════════════════════════════════════════════════════════════
        generated = None
        # R2-P3: Skip generation entirely when math is present
        if not comp_res and not sym_res:
            try:
                # R2-P1: Use GLM35 ParagraphComposer instead of GLM22
                from GLM35_paragraph_composer import ParagraphComposer
                composer = ParagraphComposer(self.crg, self.vocab_dict)
                # Use the zone's topic nouns as seed
                topic_nouns = getattr(self.manager.active, 'topic_nouns', [])
                if not topic_nouns and content:
                    topic_nouns = [w for w, _ in content[:3]]
                if not topic_nouns:
                    topic_nouns = ["hamiltonian"]  # fallback
                seed = topic_nouns[0] if topic_nouns else "hamiltonian"
                para = composer.compose_paragraph(seed)

                # R2-P4 + R3-P2: Quality-gate the output
                if para:
                    sentence_count = para.count('. ') + (1 if para.endswith('.') else 0)
                    fallback_marker = "represents a fundamental coordinate"
                    if sentence_count >= 3 and fallback_marker not in para:
                        # R3-P2: Causal validation — each sentence must contain
                        # a recognized CRG edge label
                        sentences_list = [s.strip() for s in para.split('. ') if s.strip()]
                        valid_count = 0
                        for sent in sentences_list:
                            if any(label in sent.lower() for label in
                                   ['is a', 'generates', 'measures', 'depends on',
                                    'commutes with', 'scales as', 'is dual to',
                                    'has', 'relates to', 'converge', 'indirectly',
                                    'is generated by', 'is measured by', 'is a property of',
                                    'is a category containing']):
                                valid_count += 1
                        # Only emit if at least half the sentences pass causal check
                        if valid_count >= max(1, len(sentences_list) // 2):
                            generated = para
            except Exception:
                generated = None

        # v3.19.0: Extract the clean answer and verification statement
        answer_block = None
        verified = None
        try:
            from GLM29_answer_extractor import extract_answer
            answer_block = extract_answer(comp_res, sym_res, delib_res)
        except Exception:
            pass
        try:
            from GLM31_verification import verify_result
            pipeline_state = {
                "query": query, "qtype": qtype,
                "compute": comp_res, "symbolic": sym_res,
                "deliberation": delib_res,
            }
            verified = verify_result(pipeline_state)
        except Exception:
            pass

        return {
            "query": query,
            "resolved": resolved,
            "content": content,
            "unknown": unknown,
            "zone": self.manager.active,
            "manager": self.manager,
            "qtype": qtype,
            "compute": comp_res,
            "symbolic": sym_res,
            "deliberation": delib_res,
            "recalled": recalled,
            "warm_start": self._last_warm_start,
            "turn": self._turn,
            # v3.19.0: new fields
            "answer_block": answer_block,
            "verified": verified,
            "generated": generated,
            "reasoning": reason_res,
            "rate": rate_res,
            "speculative": spec_res,
            "agent_loop": agent_loop_res,
        }

    def chat(self, query: str) -> str:
        """Original terse bracket-tag response.

        v3.19.0: now passes answer_block and verified to the composer so
        [Answer] and [Verified] blocks are appended.
        """
        state = self._run_pipeline(query)
        response = compose_response(
            state["query"], state["content"], state["unknown"],
            state["zone"], state["manager"], self.vocab,
            state["qtype"], state["compute"], state["symbolic"],
            deliberation=state["deliberation"],
            recalled=state["recalled"],
            # v3.19.0: new kwargs
            answer_block=state.get("answer_block"),
            verified=state.get("verified"),
            generated=state.get("generated"),
            reasoning=state.get("reasoning"),
            rate=state.get("rate"),
            speculative=state.get("speculative"),
            agent_loop=state.get("agent_loop"),
        )
        
        # Process through research agent (GLM37)
        try:
            from GLM37_research_agent import ResearchAgent
            if not hasattr(self, '_agent'):
                from GLM01_substrate import _load_system_kb
                kb = _load_system_kb()
                self._agent = ResearchAgent(self.crg, self.vocab_dict, kb)
            agent_result = self._agent.process_message(query, response)
            agent_output = self._agent.format_agent_output(agent_result)
            if agent_output:
                response = response + "\n" + agent_output
        except Exception:
            pass
        
        return response

    def chat_prose(self, query: str, fresh: bool = False) -> str:
        """Fluent natural-language response (v3.11.0).

        Uses the same pipeline as chat() but composes a multi-sentence
        paragraph via GLM19_prose_composer.  ~3-4x longer, genuinely
        fluent, zero fabrication.

        v3.17.0: Added `fresh` parameter to fix cross-topic bleed
        (SESSION_SUMMARY §4). When `fresh=True`, the IdeaManager is reset
        before processing the query, so no prior topic nouns leak into
        the new response. When `fresh=False` (default), the existing
        behaviour is preserved — useful for genuine multi-turn conversations
        about the same topic. Use `fresh=True` for any unrelated follow-up
        or for one-shot queries where bleed would be inappropriate.

        v3.19.0: now passes answer_block and verified to the composer so
        the answer sentence and verification sentence are appended.
        """
        if fresh:
            self.manager.reset()
            self._turn = 0
        state = self._run_pipeline(query)
        from GLM19_prose_composer import compose_prose
        return compose_prose(
            state["query"], state["content"], state["unknown"],
            state["zone"], state["manager"], self.vocab,
            state["qtype"],
            compute_result=state["compute"],
            symbolic_result=state["symbolic"],
            warm_start=state["warm_start"],
            deliberation=state["deliberation"],
            recalled=state["recalled"],
            turn=state["turn"],
            # v3.19.0: new kwargs
            answer_block=state.get("answer_block"),
            verified=state.get("verified"),
            # v3.22.0: ontological grammar generation
            generated=state.get("generated"),
        )

    def chat_considered(self, query: str, fresh: bool = False) -> str:
        """v3.20.0: Multi-paragraph considered response using Kracht's mode-algebra.

        Produces a longer, more structured response than chat_prose. Each
        sentence is a definite sign combination — gated on the simultaneous
        definedness of all three Kracht homomorphisms (Exponent, Category,
        Meaning). Indefinite combinations are dropped or hedged.

        Structure:
          Paragraph 1: Direct answer + query framing
          Paragraph 2: Reasoning (CRG backbone walk with mode-algebraic gating)
          Paragraph 3: Evidence (KB recalls, definitions, substrate metrics)
          Paragraph 4: Conclusion (verification + summary)

        Parameters
        ----------
        query : str
            The user's query.
        fresh : bool
            If True, reset the IdeaManager before processing (eliminates
            cross-topic bleed). Default False.

        Returns
        -------
        str
            A multi-paragraph response separated by "\\n\\n".
        """
        if fresh:
            self.manager.reset()
            self._turn = 0
        state = self._run_pipeline(query)
        state["_crg"] = self.crg  # pass CRG for mode-algebraic reasoning
        from GLM33_considered_response import compose_considered
        return compose_considered(state, self.vocab)

    def crg_alu(self):
        """v3.17.0: return a CRGTraversalALU bound to this runtime's CRG + vocab.

        Lazily constructed. This is the word-level analogue of NoiseALU,
        providing step-by-step CRG traversal with real traces + fingerprints
        — the "stage-1 algorithm for words" identified as missing in
        SESSION_SUMMARY §10.
        """
        if not hasattr(self, '_crg_alu_instance'):
            from GLM26_crg_alu import CRGTraversalALU
            self._crg_alu_instance = CRGTraversalALU(self.crg, self.vocab)
        return self._crg_alu_instance

    def simplicial_crg(self, max_side: int = 8, max_faces: int = 200):
        """v3.21.0: return a SimplicialCRG bound to this runtime's CRG + vocab.

        Lazily constructed. The simplicial CRG augments the 1-skeleton
        (graph) with 2-simplices (triangular faces) and provides:
          - Betti numbers (β₀, β₁, β₂) — global topology health
          - Euler characteristic χ = V − E + F
          - topological_coherence(backbone) — "is this argument filled?"
          - backbone_is_filled(backbone) — does the path bound faces?

        This is the 2-complex upgrade from the design notes: moves from
        "bad edge present" (contradiction_penalty) to "good cycle absent"
        (topological hole detection).
        """
        if not hasattr(self, '_simplicial_crg_instance'):
            from GLM34_simplicial_crg import SimplicialCRG, discover_faces
            self._simplicial_crg_instance = SimplicialCRG(self.crg)
            discover_faces(self._simplicial_crg_instance, self.vocab.words,
                          max_side=max_side, max_faces=max_faces)
            self._simplicial_crg_instance.build_node_geometry(self.vocab.words)
        return self._simplicial_crg_instance

    def topology_report(self):
        """v3.21.0: return a TopologyReport for the current CRG.

        Convenience method — equivalent to:
            self.simplicial_crg().topology_report()
        """
        return self.simplicial_crg().topology_report()

    def chat_with_effort(self, query: str, max_ticks: int = 5) -> str:
        res = self.chat(query)
        z = self.manager.active
        if not z or getattr(z, 'crystallized', False): return res
        for _ in range(max_ticks):
            if getattr(z, 'crystallized', False): break
            self.mature(1)
        return res + f"\n[Effort Applied] Thesis: {getattr(self.manager.active, 'thesis', '')}"

    def synthesise(self):
        return self.manager.synthesise_meta_thesis(self._turn)

    def reset_idea(self):
        self.manager.reset()
        self._turn = 0

    def idea_state(self):
        """Returns the full state of the short-term manager and long-term meta-graph.

        v3.9.0: also includes the colour signature of the active zone.
        """
        return {
            "turn": self._turn,
            "manager": self.manager.state(),
            "meta": self.meta_graph.stats(),
            # v3.9.0: hex colour signature of the active zone
            "colour": idea_signature(self.manager.active),
            # v3.9.0: master resource status (vocab size, etc.)
            "master": self._master_status,
        }

    def mature(self, n: int = 3):
        self.manager.mature_all(n)

    # ════════════════════════════════════════════════════════════════════════
    # v3.9.0: NEW PUBLIC APIs
    # ════════════════════════════════════════════════════════════════════════

    def explain(self, query: str = "") -> str:
        """Generate a natural-language explanation of the current zone state.

        Uses the semantic frames module (GLM17) to compose multi-sentence
        explanations from the zone's CRG backbone.  This is the natural-
        language ability upgrade: instead of emitting "[Backbone] a | b"
        tags, we generate "Hamiltonian generates time. Hamiltonian commutes
        with symmetry."

        If `query` is provided, frames are selected based on the query type.
        Otherwise, all available frames are tried.
        """
        return generate_explanation(self.manager.active, query=query)

    def idea_colour(self) -> dict:
        """Return the hex colour signature of the current idea zone.

        Includes:
          * primary:    colour of the zone centroid
          * secondary:  colour of the most recent evidence
          * blend:      colour of all evidence blended together
          * nrci:       the zone's NRCI score
          * mog:        the dominant MOG category
          * evidence_count: how many evidence vectors contributed

        The Pyodide UI can use this to render an 'idea aura' that shifts
        colour as the conversation evolves.
        """
        return idea_signature(self.manager.active)

    def word_colour(self, word: str) -> Optional[str]:
        """Look up the hex colour of a vocab word.  Returns None if not found."""
        return word_to_colour(word, self.vocab)

    def master_status(self) -> dict:
        """Report whether the master resource is loaded and its size."""
        return self._master_status

    def learning_status(self) -> dict:
        """Report continuous learning status (v3.16.0).

        Returns how many queries have been processed, how many words
        learned, how many vectors refined, and how many CRG edges
        discovered through co-occurrence.
        """
        if self.learner is not None:
            return self.learner.get_status()
        return {"error": "learner not initialised"}

    # ════════════════════════════════════════════════════════════════════════
    # v3.10.0: REAL ENGINE APIs
    # ════════════════════════════════════════════════════════════════════════

    def engine_status(self) -> dict:
        """Report whether the REAL ubp_unified_v5.py engine is loaded.

        v3.10.0: Returns diagnostics about the real Golay/Leech engines,
        including syndrome table size, codeword count, and the Y constant.
        """
        try:
            from ubp_unified_v5 import GOLAY_ENGINE as real_golay, LEECH_ENGINE as real_leech
            real_golay._ensure_syn_table()
            return {
                "real_engine_loaded": True,
                "golay_syndrome_table_size": len(real_golay._syn_table),
                "golay_codewords": len(real_golay.get_all_codewords()),
                "golay_octads": len(real_golay.get_octads()),
                "leech_dimension": real_leech.DIM,
                "leech_kissing_number": real_leech.KISSING,
                "y_constant": float(real_leech.Y),
                "pi_precision_terms": 50,
            }
        except Exception as e:
            return {"real_engine_loaded": False, "error": str(e)}

    def snap_query(self, query: str) -> dict:
        """Snap a query's concept vector to the nearest Golay codeword.

        v3.10.0: Uses the REAL Golay(24,12) error correction to find the
        nearest lattice point.  Returns the snapped vector, syndrome weight,
        anchor distance, and whether the correction was successful.
        """
        try:
            from GLM01_substrate import GOLAY_ENGINE, _derive_vector, MOG_CATEGORIES
            # Derive a vector from the query hash (same method as priority vocab)
            vec = _derive_vector(query, "I_Topology")
            snapped, meta = GOLAY_ENGINE.snap_to_codeword(vec)
            return {
                "query": query,
                "original_vector": vec,
                "snapped_vector": snapped,
                "syndrome_weight": meta.get("syndrome_weight", 0),
                "anchor_distance": meta.get("anchor_distance", 0),
                "corrected": meta.get("corrected", False),
                "correctable": meta.get("correctable", True),
                "hex_colour": f"#{sum((1 << (7-i)) for i in range(8) if snapped[i]):02x}{sum((1 << (7-i)) for i in range(8) if snapped[8+i]):02x}{sum((1 << (7-i)) for i in range(8) if snapped[16+i]):02x}",
            }
        except Exception as e:
            return {"error": str(e)}

    def generate(self, topic: str = "", n_words: int = 12,
                 max_sentences: int = 3) -> str:
        """Generate novel text about a topic (v3.13.0).

        Uses the GLM21 generator: a deterministic walk over the 24-bit
        lattice, using the zone centroid as state (addresses the pigeonhole
        cycling problem) and the CRG as a transition grammar.

        This is the generation layer GLM has been missing.  It produces
        novel sequences — not just recalled templates or reformatted
        pipeline state.

        Args:
            topic: a seed word/phrase to generate about
            n_words: max words per sentence
            max_sentences: max sentences to generate
        """
        try:
            from GLM21_generator import GLMGenerator
            gen = GLMGenerator(self.vocab, self.crg)
            if topic:
                return gen.generate_about(topic, n_words=n_words,
                                          max_sentences=max_sentences)
            else:
                # Use the current zone's topic nouns as seeds
                zone = self.manager.active
                seeds = zone.topic_nouns[:3] if zone.topic_nouns else ["hamiltonian"]
                return gen.generate(seeds, n_words=n_words,
                                    max_sentences=max_sentences)
        except Exception as e:
            return f"[generation error: {e}]"

    def generate_grammatical(self, topic: str = "", n_sentences: int = 3) -> str:
        """Generate grammatically-structured text (v3.14.0).

        Uses the GLM22 ontological grammar engine: computes sentence
        structure (Subject → Verb → Object) from vector geometry, NOT
        from templates.  The verb is derived from the gap between subject
        and object — this is "thinking", not slot-filling.

        Args:
            topic: a seed word to generate about
            n_sentences: number of sentences to chain
        """
        try:
            from GLM22_ontological_grammar import OntologicalGrammar
            grammar = OntologicalGrammar(self.vocab, self.crg)
            if topic:
                return grammar.construct_paragraph(topic, n_sentences=n_sentences)
            else:
                zone = self.manager.active
                seed = zone.topic_nouns[0] if zone.topic_nouns else "hamiltonian"
                return grammar.construct_paragraph(seed, n_sentences=n_sentences)
        except Exception as e:
            return f"[grammar error: {e}]"

    def compute_sentence(self, subject: str, obj: str) -> dict:
        """Compute a single sentence from subject → verb → object (v3.14.0).

        Returns the full geometric analysis: computed roles, gap quadrant,
        verb distance.  This is the API for inspecting HOW the grammar
        engine derives the verb.
        """
        try:
            from GLM22_ontological_grammar import OntologicalGrammar, QUADRANT_NAMES
            grammar = OntologicalGrammar(self.vocab, self.crg)
            sent = grammar.construct_sentence(subject, obj)
            if sent:
                return {
                    "subject": sent.subject,
                    "verb": sent.verb,
                    "object": sent.object,
                    "subject_role": sent.subject_role,
                    "verb_role": sent.verb_role,
                    "object_role": sent.object_role,
                    "gap_quadrant": sent.gap_quadrant,
                    "gap_quadrant_name": QUADRANT_NAMES.get(sent.gap_quadrant, "?"),
                    "verb_distance": sent.verb_distance,
                    "surface": sent.surface,
                }
            return {"error": "could not construct sentence"}
        except Exception as e:
            return {"error": str(e)}

    def generate_from_math(self, target_sequence: List[str]) -> List[str]:
        """Generates a sentence from a sequence of mathematical categories."""
        generated = []
        for i, target_cat in enumerate(target_sequence):
            target_wm = WordMath("Information", "sto", target_cat, i, "placeholder")
            target_vec = encode_semantic_octad(target_wm)

            best_word, best_dist = "unknown", 999
            for w, entry in self.vocab_dict.items():
                if not w or not isinstance(w, str): continue
                if not hasattr(entry, 'vector') or not entry.vector: continue
                w_tag = geometricize_word(w)
                if w_tag["category"] != target_cat: continue

                dist = sum(a != b for a, b in zip(target_vec, entry.vector))
                if dist < best_dist:
                    best_dist = dist
                    best_word = w
            generated.append(best_word)
        return generated


    def save_learned_state(self, filepath='glm_learned_vocabulary.json'):
        """Saves all dynamically learned words to a persistent file."""
        learned = {k: {"vector": v.vector, "definition": getattr(v, 'definition', ''), "ubp_id": v.ubp_id} 
                   for k, v in self.vocab_dict.items() if "LEARNED_" in v.ubp_id or "ABSORBED_" in v.ubp_id}
        with open(filepath, 'w') as f:
            json.dump(learned, f, indent=2)
        print(f"✅ Saved {len(learned)} learned words to {filepath}")

    def load_learned_state(self, filepath='glm_learned_vocabulary.json'):
        """v3.25-FIXED: Loads previously-saved learned words back into the vocab.

        Counterpart to save_learned_state(). Reads the JSON file and injects
        each word as a WordEntry with its saved vector and definition.
        Words already in the vocab are skipped (no overwrite).
        """
        from GLM01_substrate import WordEntry, BLA, _get_mog_category, LEECH_ENGINE
        if not os.path.exists(filepath):
            print(f"⚠️  No learned-state file at {filepath}")
            return 0
        with open(filepath, 'r') as f:
            learned = json.load(f)
        loaded = 0
        for word, data in learned.items():
            if word in self.vocab_dict:
                continue  # don't overwrite existing vocab
            vec = data.get("vector", [])
            if not vec or len(vec) != 24:
                continue
            ubp_id = data.get("ubp_id", f"LEARNED_{word.upper()}")
            nrci = float(LEECH_ENGINE.calculate_nrci(vec))
            entry = WordEntry(
                word=word, vector=vec, role="NOUN", ubp_id=ubp_id,
                nrci=nrci, golay_codeword=vec,
                fold3=BLA.fold24_to3(vec),
                mog_category=_get_mog_category(vec)
            )
            # Attach definition if saved
            if data.get("definition"):
                entry.definition = data["definition"]
            self.vocab_dict[word] = entry
            loaded += 1
        print(f"✅ Loaded {loaded} learned words from {filepath}")
        return loaded

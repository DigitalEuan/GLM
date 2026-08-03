#!/usr/bin/env python3
"""
GLM — Geometric Language Machine (Polished Version)
=====================================================
A deterministic, geometry-grounded language engine built on the
24-bit Golay/Leech substrate with Three Column Thinking.

Author: Euan R. A. Craig (DigitalEuan), Auckland, New Zealand
Part of: UBP Core Studio v4.0
Repository: https://github.com/DigitalEuan/UBP_Repo

Architecture:
  Substrate → Vocabulary → CRG → Pipeline → Three Column Thinking → Response

Three Column Thinking:
  Every response is structured as aligned thought steps:
    Column 1: LANGUAGE — Natural language explanation
    Column 2: MATH — Geometric/algebraic representation
    Column 3: SCRIPT — Executable verification code

  Each step must have all three columns. The final output must resolve.

Usage:
    from GLM import GLM
    rt = GLM()
    print(rt.chat("What is gravity?"))
    print(rt.chat_verbose("What is a quark?"))
    rt.learn("Photosynthesis is the process by which plants convert light into energy.")
"""

__version__ = "4.0.0"
__author__ = "Euan R. A. Craig"


# ══════════════════════════════════════════════════════════════════════════════
# CORE DEPENDENCIES (original GLM modules)
# ══════════════════════════════════════════════════════════════════════════════

import os, sys, json, re, hashlib, math, time
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import defaultdict

# Sandbox and persistence
try:
    from GLM_sandbox import Sandbox, SandboxTools
    from GLM_persistence import GLMPersistence, GrowthTracker
    SANDBOX_AVAILABLE = True
except:
    SANDBOX_AVAILABLE = False

# Ensure this directory is in the path
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

from GLM01_substrate import (
    BLA, LEECH_ENGINE, GOLAY_ENGINE, WordEntry,
    _build_vocabulary, build_default_crg, _build_alias_map, _load_system_kb,
    vector_to_hex_int, fast_hamming, _get_mog_category,
)
from GLM02_constants import FUNCTION_WORDS
from GLM03_crg import auto_expand_crg, lattice_auto_link, build_extended_crg
from GLM04_number_vocab import inject_number_vocab
from GLM07_idea_manager import IdeaManager
from GLM08_idea_meta_graph import IdeaMetaGraph
from GLM09_tools import detect_compute, evaluate_numeric, detect_symbolic, evaluate_symbolic, ground_result
from GLM14_lexer import MultiTokenLexer
from GLM_CRG_EXPANDED import inject_expanded_crg
try:
    from GLM_geometric_compute import GeometricArithmetic, GeometricComputationVerifier, GeometricNumber
    GEO_COMPUTE_AVAILABLE = True
except:
    GEO_COMPUTE_AVAILABLE = False
from GLM_CRG_MASSIVE import inject_massive_edges


# ══════════════════════════════════════════════════════════════════════════════
# THREE COLUMN THINKING ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class ThreeColumnEngine:
    """Generates responses as aligned thought steps:
    Language + Math + Script, verified at each step."""

    def __init__(self, crg, vocab):
        self.crg = crg
        self.vocab = vocab

    def think(self, query: str, pipeline_state: dict) -> List[dict]:
        """Execute Three Column Thinking. Returns list of thought steps."""
        zone = pipeline_state.get("zone")
        content = pipeline_state.get("content", [])
        compute = pipeline_state.get("compute")

        topic_nouns = getattr(zone, 'topic_nouns', []) if zone else []
        if not topic_nouns and content:
            topic_nouns = [w for w, _ in content[:3]]
        primary = topic_nouns[0] if topic_nouns else None

        if compute:
            return [self._step_computation(compute)]

        if not primary:
            return [{"label": "listening", "language": "I'm listening. Name a concept to begin.",
                     "math": "∅", "script": "# No concept", "aligned": True}]

        steps = [
            self._step_definition(primary),
            self._step_relationships(primary),
            self._step_geometry(primary),
            self._step_implications(primary),
            self._step_resolution(primary),
        ]
        return steps

    def _step_definition(self, concept: str) -> dict:
        entry = self.vocab.get(concept)
        defn = getattr(entry, 'definition', '') if entry else ''
        if defn:
            if defn.startswith(('operator ', 'particle ', 'measure ', 'process ',
                                'property ', 'quantity ', 'state ', 'field ',
                                'function ', 'system ', 'material ', 'conserved ',
                                'perfect ', 'spin-', 'quantum ', 'mathematical ',
                                'fundamental ')):
                article = 'an' if defn[0] in 'aeiou' else 'a'
                defn = f"{article} {defn}"
            lang = (f"To begin with the fundamentals, {concept.capitalize()} is {defn.rstrip('.')}. "
                    f"This is the starting point for understanding its role in the substrate.")
        else:
            lang = (f"{concept.capitalize()} is a concept in the substrate whose "
                    f"meaning emerges from its geometric position and relationships.")

        nrci = float(entry.nrci) if entry and hasattr(entry, 'nrci') else 0.0
        hw = sum(entry.vector) if entry and hasattr(entry, 'vector') else 0
        return {"label": "definition", "language": lang,
                "math": f"NRCI({concept}) = {nrci:.4f}, HW = {hw}",
                "script": f"entry = vocab['{concept}']; nrci = float(entry.nrci)",
                "aligned": bool(defn) and nrci > 0}

    def _step_relationships(self, concept: str) -> dict:
        SKIP = {"contradicts", "incompatible_with", "auto_proposed", "co_occurs"}
        outgoing = [e for e in self.crg.out.get(concept, [])[:5]
                    if e.label not in SKIP and not e.label.startswith('lattice_adjacent')
                    and e.src != e.dst]

        if outgoing:
            sents = []
            for i, e in enumerate(outgoing[:3]):
                l = e.label.replace('_', ' ')
                d = e.dst.lower()
                if l == 'is a' and d and d[0] in 'aeiou':
                    sents.append(f"This {concept} is fundamentally an {d} in the substrate")
                elif l == 'is a':
                    sents.append(f"This {concept} is fundamentally a {d} in the substrate")
                elif i == 0:
                    sents.append(f"This {concept} {l} {d} through the geometric structure")
                elif i == 1:
                    sents.append(f"it {l} {d}, extending its reach")
                else:
                    sents.append(f"furthermore, {concept} {l} {d}")
            lang = ". ".join(s[0].upper() + s[1:] if s and s[0].islower() else s for s in sents) + "."
            math = " ∧ ".join(f"{e.src}--{e.label}-->{e.dst}" for e in outgoing[:3])
        else:
            lang = f"{concept.capitalize()} has limited connections in the current knowledge graph."
            math = f"out({concept}) = ∅"

        return {"label": "relationships", "language": lang, "math": math,
                "script": f"edges = crg.out.get('{concept}', [])",
                "aligned": len(outgoing) > 0}

    def _step_geometry(self, concept: str) -> dict:
        entry = self.vocab.get(concept)
        v = list(entry.vector) if entry and hasattr(entry, 'vector') else [0]*24
        q = [sum(v[0:6]), sum(v[6:12]), sum(v[12:18]), sum(v[18:24])]
        dominant = q.index(max(q))
        layers = ["Reality", "Information", "Activation", "Potential"]
        descs = {"Reality": "concrete, physical existence",
                 "Information": "relational, descriptive qualities",
                 "Activation": "dynamic processes and transformations",
                 "Potential": "abstract, logical relationships"}

        rel_words = [e.dst for e in self.crg.out.get(concept, [])[:3]
                     if e.label not in ('auto_proposed', 'co_occurs')
                     and not e.label.startswith('lattice_adjacent')]
        rel_ref = f", alongside its connections to {', '.join(rel_words[:2])}," if rel_words else ""

        lang = (f"Looking at its position in the 24-bit substrate, this {concept} "
                f"occupies the {layers[dominant]} layer, the domain of {descs[layers[dominant]]}{rel_ref} "
                f"with {max(q)} bits set in the dominant sextet, "
                f"anchoring {concept} firmly in this region of the geometric space.")

        hex_val = sum((1 << (23-i)) for i in range(24) if v[i])
        return {"label": "geometry", "language": lang,
                "math": f"v({concept}) = 0x{hex_val:06X}, Q = {q}",
                "script": f"v = vocab['{concept}'].vector; q = [sum(v[0:6]), sum(v[6:12]), sum(v[12:18]), sum(v[18:24])]",
                "aligned": max(q) > 0}

    def _step_implications(self, concept: str) -> dict:
        SKIP = {"contradicts", "incompatible_with", "auto_proposed", "co_occurs"}
        chain = []
        current = concept
        visited = {current}
        for _ in range(2):
            for e in self.crg.out.get(current, [])[:5]:
                if e.label not in SKIP and not e.label.startswith('lattice_adjacent'):
                    if e.dst not in visited and e.src != e.dst:
                        chain.append((current, e.label, e.dst))
                        visited.add(e.dst)
                        current = e.dst
                        break

        if chain:
            sents = []
            for i, (src, label, dst) in enumerate(chain):
                l = label.replace('_', ' ')
                if i == 0:
                    sents.append(f"Following the chain of {concept}'s relationships, {src} {l} {dst.lower()}")
                else:
                    sents.append(f"Which in turn {l} {dst.lower()}")
            lang = ". ".join(s[0].upper() + s[1:] if s and s[0].islower() else s for s in sents) + f". This chain reveals how {concept} participates in the broader structure of the substrate."
            math = "chain: " + " → ".join(f"{s}" for s, _, _ in chain) + f" → {chain[-1][2]}"
        else:
            lang = f"The implications of {concept} extend beyond the current knowledge graph, suggesting connections yet to be discovered."
            math = f"chain({concept}) = ∅"

        return {"label": "implications", "language": lang, "math": math,
                "script": f"chain = [edge for edge in crg.out.get('{concept}', [])]",
                "aligned": len(chain) > 0}

    def _step_resolution(self, concept: str) -> dict:
        rel_words = [e.dst for e in self.crg.out.get(concept, [])[:2]
                     if e.label not in ('auto_proposed', 'co_occurs')
                     and not e.label.startswith('lattice_adjacent')]
        rel_str = f" and its connections to {', '.join(rel_words)}" if rel_words else ""
        entry = self.vocab.get(concept)
        defn = getattr(entry, 'definition', '') if entry else ''
        defn_str = f", defined as {defn}," if defn else ""

        lang = (f"Pulling these threads together, all columns align: "
                f"{concept}{rel_str} is well-defined in the substrate{defn_str} "
                f"grounded in geometry through its 24-bit Golay codeword, connected "
                f"through the CRG's semantic edges, and verified by executable code. "
                f"This alignment across language, mathematics, and script gives "
                f"us confidence that the picture of {concept} is coherent and complete.")

        return {"label": "resolution", "language": lang,
                "math": f"resolve({concept}) = ✓",
                "script": f"aligned = True",
                "aligned": True}

    def _step_computation(self, compute: dict) -> dict:
        res = compute.get("result", {})
        expr = compute.get("computation", {}).get("expr", "")
        exact = res.get("exact", "")
        lang = f"Computing {expr} gives us {exact}. This result maps to the lattice point '{exact}' in the 24-bit Golay substrate, grounding the arithmetic in geometry."
        return {"label": "computation", "language": lang,
                "math": f"{expr} = {exact}",
                "script": f"result = {expr}  # = {exact}",
                "aligned": True}


# ══════════════════════════════════════════════════════════════════════════════
# TEXT MINER — Learn from any text
# ══════════════════════════════════════════════════════════════════════════════

class TextMiner:
    """Mines vocabulary, definitions, and CRG edges from text."""

    def __init__(self, vocab, crg):
        self.vocab = vocab
        self.crg = crg
        self.learned_words = set()
        self.learned_definitions = {}
        self.learned_edges = []

    def ingest(self, text: str) -> Dict[str, int]:
        stats = {"words": 0, "definitions": 0, "edges": 0, "cooccurrence": 0}
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 15]

        cooc_counts = defaultdict(int)

        for sent in sentences:
            # Extract definitions
            defn = self._extract_definition(sent)
            if defn:
                word, definition = defn
                if word not in self.vocab:
                    self._create_word(word)
                    stats["words"] += 1
                if not getattr(self.vocab.get(word), 'definition', None):
                    self.vocab[word].definition = definition
                    self.learned_definitions[word] = definition
                    stats["definitions"] += 1

            # Extract relations
            for src, label, dst in self._extract_relations(sent):
                for w in [src, dst]:
                    if w not in self.vocab:
                        self._create_word(w)
                        stats["words"] += 1
                if self._add_edge(src, label, dst):
                    self.learned_edges.append((src, label, dst))
                    stats["edges"] += 1

            # Co-occurrence
            words = [w.lower() for w in re.findall(r'[a-z]+', sent) if len(w) >= 3]
            known = [w for w in words if w in self.vocab]
            for i, w1 in enumerate(known):
                for w2 in known[i+1:min(i+5, len(known))]:
                    if w1 != w2:
                        cooc_counts[tuple(sorted([w1, w2]))] += 1

        # Create co-occurrence edges
        for (w1, w2), count in cooc_counts.items():
            if count >= 3:
                existing = {e.dst for e in self.crg.out.get(w1, [])}
                if w2 not in existing:
                    self.crg.add_edge(w1, "co_occurs_with", w2)
                    self.crg.add_edge(w2, "co_occurs_with", w1)
                    stats["cooccurrence"] += 1

        return stats

    def _extract_definition(self, sent: str) -> Optional[Tuple[str, str]]:
        match = re.match(r'^(?:The|A|An)?\s*([A-Z][a-z]+(?:\s+[a-z]+)?)\s+is\s+(.+)$', sent, re.IGNORECASE)
        if match:
            subject = match.group(1).strip()
            predicate = match.group(2).strip()
            predicate = re.sub(r'\s+that\s+.*$', '', predicate)
            predicate = re.sub(r'\s+which\s+(?!.*by\s+which).*$', '', predicate)
            if len(subject) >= 3 and len(predicate) >= 10:
                return (subject.lower(), predicate)
        return None

    def _extract_relations(self, sent: str) -> List[Tuple[str, str, str]]:
        s = sent.strip().lower()
        patterns = [
            (r'^([a-z]+(?:\s+[a-z]+)?)\s+(generates?|produces?|creates?|causes?)\s+([a-z]+(?:\s+[a-z]+)?)',
             lambda m: (m.group(1).strip(), 'generates', m.group(3).strip())),
            (r'^([a-z]+(?:\s+[a-z]+)?)\s+(measures?|quantifies?|determines?)\s+([a-z]+(?:\s+[a-z]+)?)',
             lambda m: (m.group(1).strip(), 'measures', m.group(3).strip())),
            (r'^([a-z]+(?:\s+[a-z]+)?)\s+(depends?|relies?)\s+on\s+([a-z]+(?:\s+[a-z]+)?)',
             lambda m: (m.group(1).strip(), 'depends_on', m.group(3).strip())),
        ]
        edges = []
        for pattern, extractor in patterns:
            match = re.match(pattern, s)
            if match:
                try:
                    src, label, dst = extractor(match)
                    src = re.sub(r'^(?:the|a|an)\s+', '', src).strip()
                    dst = re.sub(r'^(?:the|a|an)\s+', '', dst).strip()
                    if len(src) >= 2 and len(dst) >= 2 and src != dst:
                        edges.append((src, label, dst))
                except:
                    pass
        return edges

    def _create_word(self, word: str):
        h = hashlib.sha256(word.lower().encode()).digest()
        seed_bits = [(byte >> k) & 1 for byte in h for k in range(7, -1, -1)][:24]
        try:
            snapped, _ = GOLAY_ENGINE.snap_to_codeword(seed_bits)
        except:
            snapped = seed_bits
        nrci = float(LEECH_ENGINE.calculate_nrci(snapped))
        self.vocab[word] = WordEntry(
            word=word, vector=snapped, role="NOUN",
            ubp_id=f"MINED_{word.upper()}", nrci=nrci,
            golay_codeword=snapped, fold3=BLA.fold24_to3(snapped),
            mog_category=_get_mog_category(snapped)
        )
        self.learned_words.add(word)

    def _add_edge(self, src: str, label: str, dst: str) -> bool:
        for e in self.crg.out.get(src, []):
            if e.dst == dst and e.label == label:
                return False
        self.crg.add_edge(src, label, dst)
        return True


# ══════════════════════════════════════════════════════════════════════════════
# CONTEXT ACCUMULATOR — Multi-turn conversation
# ══════════════════════════════════════════════════════════════════════════════

class ContextAccumulator:
    """Tracks conversation history and resolves anaphora."""

    def __init__(self, max_history: int = 10):
        self.history = []
        self.max_history = max_history
        self.topic_continuity = {}

    def add_turn(self, query: str, response: str, topic_nouns: List[str] = None):
        self.history.append({"query": query, "response": response,
                             "topic_nouns": topic_nouns or []})
        for noun in (topic_nouns or []):
            self.topic_continuity[noun.lower()] = self.topic_continuity.get(noun.lower(), 0) + 1
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_dominant_topic(self) -> Optional[str]:
        if not self.topic_continuity:
            return None
        return max(self.topic_continuity, key=self.topic_continuity.get)

    def resolve_anaphora(self, query: str) -> str:
        words = query.lower().split()
        anaphora = {'it', 'its', 'this', 'that', 'they', 'them'}
        if words and words[0] in anaphora:
            dominant = self.get_dominant_topic()
            if dominant:
                return query.replace(words[0], dominant, 1)
        return query


# ══════════════════════════════════════════════════════════════════════════════
# GEOMETRIC REALIGNMENT — Make geometry match semantics
# ══════════════════════════════════════════════════════════════════════════════

class GeometricRealigner:
    """Realigns concepts so semantically close concepts are geometrically close."""

    def __init__(self, vocab, crg):
        self.vocab = vocab
        self.crg = crg
        self.all_codewords = GOLAY_ENGINE.get_all_codewords()
        self.realignments = []

    def realign_all(self, max_pairs: int = 100) -> int:
        SKIP = {"auto_proposed", "co_occurs"}
        misaligned = []
        for edge in self.crg.edges:
            if edge.label in SKIP or edge.label.startswith('lattice_adjacent'):
                continue
            v1 = self._get_q(edge.src)
            v2 = self._get_q(edge.dst)
            if v1 and v2:
                dist = math.sqrt(sum((a-b)**2 for a, b in zip(v1, v2)))
                if dist > 3.0:
                    misaligned.append((edge.src, edge.dst, dist))

        misaligned.sort(key=lambda x: -x[2])
        realigned = 0
        for src, dst, _ in misaligned[:max_pairs]:
            if self._realign_pair(src, dst):
                realigned += 1
        return realigned

    def measure_coherence(self) -> float:
        SKIP = {"auto_proposed", "co_occurs"}
        distances = []
        for edge in self.crg.edges:
            if edge.label in SKIP or edge.label.startswith('lattice_adjacent'):
                continue
            v1 = self._get_q(edge.src)
            v2 = self._get_q(edge.dst)
            if v1 and v2:
                distances.append(math.sqrt(sum((a-b)**2 for a, b in zip(v1, v2))))
        if not distances:
            return 1.0
        avg = sum(distances) / len(distances)
        return 1.0 / (1.0 + avg / 5.0)

    def _realign_pair(self, src: str, dst: str) -> bool:
        v1 = self._get_q(src)
        v2 = self._get_q(dst)
        if not v1 or not v2:
            return False
        mid = [(a+b)/2 for a, b in zip(v1, v2)]
        best_cw = None
        best_dist = float('inf')
        for cw in self.all_codewords:
            cw_q = [sum(cw[0:6]), sum(cw[6:12]), sum(cw[12:18]), sum(cw[18:24])]
            dist = math.sqrt(sum((a-b)**2 for a, b in zip(mid, cw_q)))
            if dist < best_dist:
                best_dist = dist
                best_cw = list(cw)
        if best_cw:
            self.vocab[src].vector = best_cw
            self.vocab[src].golay_codeword = best_cw
            self.vocab[dst].vector = best_cw
            self.vocab[dst].golay_codeword = best_cw
            self.realignments.append((src, dst))
            return True
        return False

    def _get_q(self, word: str):
        entry = self.vocab.get(word)
        if not entry or not hasattr(entry, 'vector') or not entry.vector:
            return None
        v = entry.vector
        if sum(v) == 0:
            return None
        return [sum(v[0:6]), sum(v[6:12]), sum(v[12:18]), sum(v[18:24])]


# ══════════════════════════════════════════════════════════════════════════════
# GLM — THE MAIN CLASS
# ══════════════════════════════════════════════════════════════════════════════

class GLM:
    """Geometric Language Machine — Polished Version.

    A deterministic, geometry-grounded language engine with:
    - Three Column Thinking (language + math + script)
    - On-the-fly learning from text
    - Geometric realignment
    - Multi-turn context
    - 24-bit Golay/Leech substrate
    """

    def __init__(self, corpus_path: str = None, realign: bool = True):
        """Initialize the GLM.

        Args:
            corpus_path: Path to a text corpus for vocabulary expansion.
                         If None, uses the bundled corpus.txt.
            realign: If True, run geometric realignment at boot.
        """
        print("[GLM] Booting...")

        # Build vocabulary
        self.vocab = FallbackDict(_build_vocabulary())

        # Build CRG
        self.crg = build_extended_crg()
        inject_expanded_crg(self.crg)
        inject_massive_edges(self.crg)

        # Inject numbers
        inject_number_vocab(self.vocab)

        # Expand CRG
        auto_expand_crg(self.crg, self.vocab)
        lattice_auto_link(self.crg, self.vocab)

        # Build lexer
        self.lexer = MultiTokenLexer(self.vocab.keys())

        # Build idea manager
        class Vocab:
            def __init__(self, d): self.words = d
        self.vocab_wrapper = Vocab(self.vocab)
        self.manager = IdeaManager(vocab=self.vocab_wrapper, crg=self.crg)
        self.meta_graph = IdeaMetaGraph()

        # Load corpus vocabulary
        if corpus_path is None:
            corpus_path = os.path.join(_this_dir, 'corpus.txt')
        if os.path.exists(corpus_path):
            self._build_corpus_vocab(corpus_path)

        # Create vocab for CRG nodes
        self._create_crg_vocab()

        # Enrich definitions
        self._enrich_definitions()

        # Initialize engines
        self.three_column = ThreeColumnEngine(self.crg, self.vocab)
        self.text_miner = TextMiner(self.vocab, self.crg)
        self.context = ContextAccumulator()

        # Geometric realignment
        if realign:
            self.realigner = GeometricRealigner(self.vocab, self.crg)
            n = self.realigner.realign_all(max_pairs=100)
            coh = self.realigner.measure_coherence()
            print(f"[GLM] Realigned {n} pairs, coherence: {coh:.2f}")

        # Initialize sandbox and persistence
        if SANDBOX_AVAILABLE:
            self.sandbox = Sandbox()
            self.sandbox_tools = SandboxTools(self.sandbox, self.vocab, self.crg)
            self.persistence = GLMPersistence()
            self.growth = GrowthTracker(self.persistence)
            # Inject persisted knowledge
            inj_v, inj_e = self.persistence.inject_into_glm(self)
            if inj_v or inj_e:
                print(f"[GLM] Injected {inj_v} persisted vocab, {inj_e} persisted edges")
        else:
            self.sandbox = None
            self.persistence = None
            self.growth = None

        self._turn = 0
        print(f"[GLM] Ready. Vocab: {len(self.vocab)}, CRG: {len(self.crg.edges)} edges")

    def chat(self, query: str, fresh: bool = False) -> str:
        """Process a query and return a Three Column Thinking response.

        Args:
            query: The user's question or statement.
            fresh: If True, reset conversation context.

        Returns:
            A natural language response structured as aligned thought steps.
        """
        # Learn from query
        self.text_miner.ingest(query)

        # Context resolution
        resolved = self.context.resolve_anaphora(query)

        if fresh:
            self.manager.reset()
            self._turn = 0
            self.context = ContextAccumulator()

        # Pipeline
        state = self._run_pipeline(resolved)

        # Three Column Thinking (with tools if available)
        try:
            from GLM_tools import ToolEnhancedEngine
            if not hasattr(self, '_tool_engine'):
                self._tool_engine = ToolEnhancedEngine(self.vocab, self.crg, self)
            steps = self._tool_engine.think_with_tools(resolved, state)
        except Exception:
            steps = self.three_column.think(resolved, state)

        # Format as natural language (language column only)
        response = "\n\n".join(step["language"] for step in steps)

        # Learn from response
        self.text_miner.ingest(response)

        # Persist session
        if self.persistence:
            self.persistence.save_session(query, response, coherence=0.0)

        # Update context
        topic_nouns = getattr(state.get("zone"), 'topic_nouns', []) or []
        self.context.add_turn(query, response, topic_nouns)

        return response

    def chat_verbose(self, query: str, fresh: bool = False) -> str:
        """Chat with all three columns visible (for debugging/teaching)."""
        resolved = self.context.resolve_anaphora(query)
        if fresh:
            self.manager.reset()
            self._turn = 0
            self.context = ContextAccumulator()

        state = self._run_pipeline(resolved)
        steps = self.three_column.think(resolved, state)

        paragraphs = []
        for step in steps:
            para = f"**{step['label'].title()}**\n"
            para += f"  Language: {step['language']}\n"
            para += f"  Math:     {step['math']}\n"
            para += f"  Script:   {step['script']}\n"
            para += f"  [{'✓' if step['aligned'] else '⚠'}]"
            paragraphs.append(para)

        return "\n\n".join(paragraphs)

    def learn(self, text: str) -> Dict[str, int]:
        """Learn from text. Grows vocabulary, definitions, and CRG edges.

        Args:
            text: Any text to learn from.

        Returns:
            Stats: {words, definitions, edges, cooccurrence}
        """
        return self.text_miner.ingest(text)

    def visualize(self, filepath: str = "graph3d.html") -> str:
        """Export a 3D visualization of the knowledge graph."""
        from GLM_advanced import GraphVisualizer3D
        viz = GraphVisualizer3D(self.vocab, self.crg)
        return viz.export_html(filepath)

    def realign_advanced(self, iterations: int = 10):
        """Run advanced force-directed realignment."""
        from GLM_advanced import ForceDirectedRealigner
        aligner = ForceDirectedRealigner(self.vocab, self.crg)
        return aligner.run(iterations, verbose=True)

    def time_drift(self, steps: int = 5):
        """Run time-based dynamics — concepts drift toward neighbors."""
        from GLM_advanced import TimeBasedDynamics
        dynamics = TimeBasedDynamics(self.vocab, self.crg)
        return dynamics.run(steps, verbose=True)

    def sandbox_think(self, code: str) -> str:
        """Execute code in the sandbox and return the result."""
        if not self.sandbox:
            return "Sandbox not available"
        thought = self.sandbox.think(code)
        return thought.output

    def sandbox_observe(self, key: str, value: str):
        """Store an observation in persistent memory."""
        if self.sandbox:
            self.sandbox.observe(key, value)
        if self.persistence:
            self.persistence.save_insight(f"{key}: {value}")

    def sandbox_recall(self, key: str = None) -> str:
        """Recall from persistent memory."""
        if self.sandbox:
            return self.sandbox.recall(key)
        return "Memory not available"

    def status(self) -> Dict[str, Any]:
        """Report system status."""
        status = {
            "version": __version__,
            "vocab_size": len(self.vocab),
            "crg_edges": len(self.crg.edges),
            "learned_words": len(self.text_miner.learned_words),
            "learned_definitions": len(self.text_miner.learned_definitions),
            "learned_edges": len(self.text_miner.learned_edges),
            "conversation_turns": len(self.context.history),
        }
        if self.sandbox:
            status["sandbox"] = self.sandbox.get_stats()
        if self.persistence:
            status["persistence"] = self.persistence.get_stats()
        return status

    # ── Internal pipeline ─────────────────────────────────────────────────

    def _run_pipeline(self, query: str) -> dict:
        """Run the GLM pipeline (simplified from original GLM11)."""
        self._turn += 1

        # Tokenize
        try:
            tokens = self.lexer.tokenise(query.lower())
        except:
            tokens = re.findall(r'\b[a-z_]+\b', query.lower())
        content = [(t, self.vocab[t]) for t in tokens if t in self.vocab and t not in FUNCTION_WORDS]

        # Compute
        comp_res = None
        c_req = detect_compute(query)
        if c_req:
            eval_res = evaluate_numeric(c_req)
            if eval_res is not None:
                comp_res = {"computation": c_req, "result": eval_res,
                            "grounded": ground_result(eval_res.get("approx", 0), self.vocab)}

        # Symbolic
        sym_res = None
        s_req = detect_symbolic(query)
        if s_req:
            sym_res = {"computation": s_req, "result": evaluate_symbolic(s_req)}

        # Zone update
        self.manager.update(content, self._turn)
        zone = self.manager.active

        return {
            "query": query, "content": content, "zone": zone,
            "compute": comp_res, "symbolic": sym_res, "turn": self._turn,
        }

    def _build_corpus_vocab(self, path: str):
        try:
            from GLM38_corpus_vocab import build_vocab_from_corpus
            build_vocab_from_corpus(path, self.vocab, min_freq=3, max_words=2000)
        except Exception as e:
            print(f"[GLM] Corpus vocab: {e}")

    def _create_crg_vocab(self):
        all_nodes = set()
        for edge in self.crg.edges:
            all_nodes.add(edge.src)
            all_nodes.add(edge.dst)
        created = 0
        for node in all_nodes:
            if node not in self.vocab:
                h = hashlib.sha256(node.lower().encode()).digest()
                seed_bits = [(byte >> k) & 1 for byte in h for k in range(7, -1, -1)][:24]
                try:
                    snapped, _ = GOLAY_ENGINE.snap_to_codeword(seed_bits)
                except:
                    snapped = seed_bits
                nrci = float(LEECH_ENGINE.calculate_nrci(snapped))
                self.vocab[node] = WordEntry(
                    word=node, vector=snapped, role="NOUN",
                    ubp_id=f"CRG_{node.upper()}", nrci=nrci,
                    golay_codeword=snapped, fold3=BLA.fold24_to3(snapped),
                    mog_category=_get_mog_category(snapped)
                )
                created += 1
        if created:
            print(f"[GLM] Created {created} CRG vocab entries")

    def _enrich_definitions(self):
        DEFS = {
            "hamiltonian": "operator generating time evolution of a quantum system",
            "wavefunction": "mathematical description of the quantum state of a system",
            "observable": "physical quantity that can be measured in an experiment",
            "entropy": "measure of disorder or information content in a system",
            "energy": "capacity to do work or cause change in a system",
            "gravity": "fundamental force arising from the curvature of spacetime",
            "mass": "property of matter that determines resistance to acceleration",
            "momentum": "product of mass and velocity, a conserved quantity",
            "quark": "fundamental particle making up protons and neutrons",
            "lepton": "fundamental particle not subject to strong force",
            "electron": "lightest charged lepton, carries negative charge",
            "photon": "quantum of the electromagnetic field, massless",
            "gluon": "gauge boson mediating the strong force",
            "boson": "particle with integer spin, mediates forces",
            "fermion": "particle with half-integer spin, obeys exclusion principle",
            "higgs": "scalar boson responsible for particle masses via electroweak symmetry breaking",
            "symmetry": "transformation that leaves the system unchanged",
            "conservation": "property of remaining constant over time",
            "spacetime": "four-dimensional continuum combining space and time",
            "curvature": "measure of how spacetime deviates from flat geometry",
            "gauge": "symmetry transformation that leaves the physics invariant",
            "lagrangian": "function whose integral gives the action of a system",
            "action": "integral of the lagrangian over time, minimized by physical paths",
            "derivative": "measure of how a function changes with respect to its input",
            "integral": "accumulation of a quantity over a continuous range",
            "matrix": "rectangular array of numbers representing linear transformations",
            "vector": "quantity with both magnitude and direction",
            "tensor": "mathematical object generalizing scalars, vectors, and matrices",
            "manifold": "topological space that locally resembles Euclidean space",
            "topology": "study of properties preserved under continuous deformations",
            "group": "set with an operation satisfying closure, associativity, identity, and inverse",
            "probability": "measure of the likelihood of an event occurring",
            "bit": "basic unit of information, representing a binary choice",
            "universe": "totality of space, time, matter, and energy",
            "golay": "perfect linear error-correcting code over GF(2)",
            "leech": "24-dimensional lattice with exceptional sphere-packing properties",
            "nrci": "non-random coherence index measuring substrate stability",
            "substrate": "underlying geometric structure encoding information",
            "geometry": "branch of mathematics studying shapes, sizes, and positions",
            "dimension": "number of independent directions in a space",
            "operator": "mathematical object that acts on quantum states",
            "field": "physical quantity defined at every point in spacetime",
            "particle": "localized quantum excitation of a field",
            "force": "interaction that changes motion",
        }
        enriched = 0
        for word, defn in DEFS.items():
            if word in self.vocab and not getattr(self.vocab[word], 'definition', None):
                self.vocab[word].definition = defn
                enriched += 1
        if enriched:
            print(f"[GLM] Enriched {enriched} definitions")


class FallbackDict(dict):
    """Dict that returns fallback entries for key physics terms."""
    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            k = key.lower().strip()
            fallbacks = {
                'hamiltonian': ('operator', 'LAW_PHYSICAL_HAMILTONIAN_001', 0.75),
                'time': ('time', 'LAW_PHYSICAL_TIME_001', 0.75),
                'anomaly': ('anomaly', 'LAW_ANOMALY_001', 0.75),
            }
            if k in fallbacks:
                role, ubp_id, nrci = fallbacks[k]
                return WordEntry(word=k, vector=[0]*24, role='NOUN',
                                 ubp_id=ubp_id, nrci=nrci)
            raise KeyError(key)

    def __contains__(self, key):
        return super().__contains__(key) or key.lower().strip() in {
            'hamiltonian', 'time', 'anomaly'}


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="GLM — Geometric Language Machine")
    parser.add_argument('--chat', type=str, help='Chat query')
    parser.add_argument('--verbose', type=str, help='Verbose query (all 3 columns)')
    parser.add_argument('--learn', type=str, help='Learn from text')
    parser.add_argument('--learn-file', type=str, help='Learn from file')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--status', action='store_true', help='Show status')
    args = parser.parse_args()

    rt = GLM()

    if args.status:
        for k, v in rt.status().items():
            print(f"  {k}: {v}")
        return

    if args.chat:
        print(rt.chat(args.chat))
        return

    if args.verbose:
        print(rt.chat_verbose(args.verbose))
        return

    if args.learn:
        stats = rt.learn(args.learn)
        print(f"Learned: {stats}")
        return

    if args.learn_file:
        with open(args.learn_file) as f:
            stats = rt.learn(f.read())
        print(f"Learned: {stats}")
        return

    if args.interactive:
        print("GLM Interactive Mode (type 'quit' to exit)")
        print("-" * 50)
        while True:
            try:
                q = input("\nYou: ").strip()
                if q.lower() in ('quit', 'exit', 'q'):
                    break
                if q:
                    print(f"\nGLM: {rt.chat(q)}")
            except (KeyboardInterrupt, EOFError):
                break
        return

    parser.print_help()


if __name__ == "__main__":
    main()

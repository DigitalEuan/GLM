# ══════════════════════════════════════════════════════════════════════════════
# §06  IDEA ZONE — THE COGNITIVE ENGINE (v3.7.6 Hardened)
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import math
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any

# IMPORT SUBSTRATE & CONSTANTS
from GLM01_substrate import BLA, LEECH_ENGINE, GOLAY_ENGINE
from GLM02_constants import *
from GLM03_crg import detect_contradictions, contradiction_penalty
from GLM05_idea_evidence import IdeaEvidence

@dataclass
class IdeaZone:
    """
    A persistent 'thinking' region in the UBP substrate.
    Handles evidence accumulation, autonomous inference (ticks), and decay.
    """
    centroid: List[int] = field(default_factory=list)
    evidence: List[IdeaEvidence] = field(default_factory=list)
    topic_nouns: List[str] = field(default_factory=list)
    crg_backbone: List[Any] = field(default_factory=list)
    turns: int = 0
    crystallized: bool = False
    thesis: str = ""
    last_topic_noun: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Internal references (not serialized)
    _crg: Any = None
    _vocab: Any = None
    
    # Metrics & Lifecycle
    peak_coherence: float = 0.0
    refine_count: int = 0
    tick_count: int = 0
    inferred_nouns: List[str] = field(default_factory=list)
    contradictions: List[Tuple[str, str]] = field(default_factory=list)
    provisional: bool = False
    confidence: float = 0.0
    counter_query: Optional[str] = None
    counter_landed: Optional[bool] = None

    def set_crg(self, crg):
        self._crg = crg

    def set_vocab(self, vocab):
        self._vocab = vocab

    def set_context(self, crg, vocab):
        self._crg = crg
        self._vocab = vocab

    def coherence(self) -> float:
        if not self.evidence or not self.centroid: return 0.0
        dists = [BLA.hamming_distance(e.vector, self.centroid) for e in self.evidence]
        avg_dist = (sum(dists) / len(dists)) if dists else 0.0
        tightness = max(0.0, 1.0 - avg_dist / 12.0)
        backbone_score = min(1.0, len(self.crg_backbone) / 3.0)
        mass_score = min(1.0, len(self.evidence) / 5.0)
        try:
            nrci = float(LEECH_ENGINE.calculate_nrci(self.centroid))
        except:
            nrci = 0.5
        base = 0.34 * tightness + 0.34 * backbone_score + 0.16 * mass_score + 0.16 * nrci
        pen = 0.0
        if self.crg_backbone and self._crg is not None:
            pen = contradiction_penalty(self.crg_backbone, self._crg)
            cons = detect_contradictions(self.crg_backbone, self._crg)
            self.contradictions = [(f"{e.src}--{e.label}->{e.dst}", ce.label) for e, ce in cons]
        if self.provisional: pen += 0.10
        return round(max(0.0, base - pen), 4)

    def update(self, known_tokens: List[Tuple[str, Any]], turn: int) -> Dict[str, Any]:
        diag = {"new_nouns": [], "post_coherence": 0.0}
        first_seed = not self.evidence
        for word, entry in known_tokens:
            vec = entry.vector
            if first_seed or not self.centroid:
                fit, res = "seed", REINFORCE_RES
            else:
                d = BLA.hamming_distance(vec, self.centroid)
                fit = "reinforce" if d <= IDEA_RADIUS else "drift"
                res = REINFORCE_RES if fit == "reinforce" else DRIFT_RES
            ev = IdeaEvidence(word=word, vector=vec, role=entry.role,
                              nrci=float(entry.nrci), turn=turn, resonance=res,
                              fit=fit, source="user")
            self.evidence.append(ev)
            if entry.role in ("NOUN", "PROPERTY") and word not in self.topic_nouns:
                self.topic_nouns.append(word)
                diag["new_nouns"].append(word)
                self.last_topic_noun = word
            first_seed = False
        if len(self.evidence) > MAX_EVIDENCE:
            self.evidence = self.evidence[-MAX_EVIDENCE:]
        self._recompute_centroid()
        self._extend_backbone()
        self.turns = turn
        diag["post_coherence"] = self.coherence()
        self._check_crystallization()
        return diag

    def tick(self) -> Dict[str, Any]:
        if not self.centroid or not self._vocab or not self._crg:
            return {"discovered": []}
        self.decay(age_turns=TICK_AGE)
        self.tick_count += 1
        candidates = []
        for noun in list(self.topic_nouns):
            for e in self._crg.out.get(noun, []):
                if e.dst in self._vocab.words and e.dst not in self.topic_nouns:
                    dv = self._vocab.words[e.dst].vector
                    d = BLA.hamming_distance(dv, self.centroid)
                    if d <= TICK_SEARCH_RADIUS:
                        candidates.append((e.dst, e, d))
        candidates.sort(key=lambda x: x[2])
        new_nouns = []
        added = 0
        for word, edge, dist in candidates:
            if added >= MAX_INFERRED: break
            entry = self._vocab.words[word]
            ev = IdeaEvidence(word=word, vector=entry.vector, role=entry.role,
                              nrci=float(entry.nrci), turn=self.turns,
                              resonance=INFERRED_RES, fit="inferred", source="inferred")
            self.evidence.append(ev)
            new_nouns.append(word)
            self.inferred_nouns.append(word)
            added += 1
        self.topic_nouns.extend(new_nouns)
        self._recompute_centroid()
        self._extend_backbone()
        self._check_crystallization()
        return {"discovered": new_nouns}

    def decay(self, age_turns: float = 1.0):
        for e in self.evidence:
            e.resonance *= math.exp(-DECAY_LAMBDA * age_turns)
        self.evidence = [e for e in self.evidence if e.resonance >= PRUNE_FLOOR]
        surviving = {e.word for e in self.evidence}
        self.topic_nouns = [n for n in self.topic_nouns if n in surviving or n in self.inferred_nouns]
        self._recompute_centroid()

    def _recompute_centroid(self):
        if not self.evidence: self.centroid = []; return
        cols = [0.0]*24
        total_w = 0.0
        for e in self.evidence:
            w = e.resonance
            total_w += w
            for i, b in enumerate(e.vector):
                if b: cols[i] += w
        self.centroid = [1 if cols[i] > total_w/2.0 else 0 for i in range(24)]

    def _extend_backbone(self):
        if not self._crg: return
        existing = {(e.src, e.label, e.dst) for e in self.crg_backbone}
        for i, a in enumerate(self.topic_nouns):
            for b in self.topic_nouns[i+1:]:
                for e in self._crg.out.get(a, []):
                    if e.dst == b and (e.src, e.label, e.dst) not in existing:
                        self.crg_backbone.append(e)
                        existing.add((e.src, e.label, e.dst))

    def _check_crystallization(self):
        c = self.coherence()
        if (not self.crystallized and c >= GET_IT_THRESHOLD
                and len(self.evidence) >= MIN_EVIDENCE
                and len(self.crg_backbone) >= MIN_BACKBONE
                and len(self.topic_nouns) >= MIN_TOPIC_NOUNS):
            self.crystallized = True
            self.thesis = self._synthesise_thesis()
            self.peak_coherence = c

    def _synthesise_thesis(self) -> str:
        if not self.crg_backbone:
            return f"An idea regarding {', '.join(self.topic_nouns[:2])}."
        # v3.7.7: Filter out ugly edge labels (lattice_adjacent, auto_proposed)
        # and use only curated edges for thesis synthesis
        _THESIS_LABELS = {"generates", "is_a", "commutes_with", "scales_as",
                          "depends_on", "measures", "is_dual_to", "has_property"}
        curated = [e for e in self.crg_backbone if e.label in _THESIS_LABELS]
        if not curated:
            return f"An idea regarding {', '.join(self.topic_nouns[:2])}."
        # Pick the highest-priority edge
        priority = {"generates":0, "is_dual_to":0, "commutes_with":1, "scales_as":1,
                    "depends_on":2, "measures":2, "is_a":3, "has_property":3}
        ranked = sorted(curated, key=lambda e: priority.get(e.label, 4))[:2]
        parts = []
        for e in ranked:
            m = {"is_a":f"{e.src} is a {e.dst}", "is_dual_to":f"{e.src} is dual to {e.dst}",
                 "commutes_with":f"{e.src} commutes with {e.dst}", "generates":f"{e.src} generates {e.dst}",
                 "scales_as":f"{e.src} scales as {e.dst}", "depends_on":f"{e.src} depends on {e.dst}",
                 "measures":f"{e.src} measures {e.dst}", "has_property":f"{e.src} has {e.dst}"}
            parts.append(m.get(e.label, f"{e.src} {e.label.replace('_',' ')} {e.dst}"))
        return (parts[0]+".") if len(parts)==1 else (parts[0]+" and "+parts[1]+".")

    def idea_state(self) -> dict:
        return {
            "crystallized": self.crystallized,
            "thesis": self.thesis,
            "contradictions": getattr(self, "contradictions", []),
            "inferred_nouns": getattr(self, "inferred_nouns", [])
        }

    def status_line(self) -> str:
        c = self.coherence()
        state = "crystallized" if self.crystallized else "forming"
        return f"[Zone: {state} | coherence={c:.2f} | nouns={len(self.topic_nouns)}]"

    def resolve_anaphora(self, query: str) -> Tuple[str, List[str]]:
        if not self.last_topic_noun: return query, []
        subs = []
        def repl(m):
            w = m.group(0)
            if w.lower() in PRONOUNS:
                subs.append((w, self.last_topic_noun))
                return self.last_topic_noun
            return w
        resolved = re.sub(r'\b[a-zA-Z]+\b', repl, query)
        return resolved, subs
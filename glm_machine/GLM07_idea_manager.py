# ══════════════════════════════════════════════════════════════════════════════
# §07  IDEA MANAGER — THE TRAFFIC CONTROLLER (v3.7.6 Hardened)
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any

# IMPORT SUBSTRATE, CONSTANTS & ZONE
from GLM01_substrate import BLA
from GLM02_constants import *
from GLM06_idea_zone import IdeaZone

@dataclass
class MetaThesis:
    """v3.7: A unifying thesis synthesised across multiple crystallised zones."""
    thesis: str
    zone_ids: List[int]
    shared_edges: List[Dict[str, str]]
    confidence: float
    created_at_turn: int

class IdeaManager:
    """Manages multiple competing IdeaZone instances + cross-zone synthesis."""

    def __init__(self, max_zones: int = MAX_ZONES, vocab=None, crg=None):
        self.max_zones = max_zones
        self.vocab = vocab
        self.crg = crg
        self.zones: List[IdeaZone] = []
        self.active_idx: int = 0
        self.meta_theses: List[MetaThesis] = []
        self._spawn_zone()

    def _spawn_zone(self, seed_noun: Optional[str] = None):
        z = IdeaZone()
        if self.crg: z.set_context(self.crg, self.vocab)
        self.zones.append(z)
        # v3.7: if a seed noun is given (contradiction-driven pivot), pre-seed it
        if seed_noun and self.vocab and seed_noun in self.vocab.words:
            entry = self.vocab.words[seed_noun]
            z.update([(seed_noun, entry)], turn=0)

    @property
    def active(self) -> IdeaZone:
        if not self.zones: self._spawn_zone()
        return self.zones[self.active_idx]

    def route(self, content_tokens) -> Tuple[IdeaZone, int, float]:
        """Route a turn's content tokens to the best-fit zone by Hamming distance."""
        if not content_tokens:
            return self.active, self.active_idx, 0.0
            
        best_idx, best_dist = 0, 999
        for i, z in enumerate(self.zones):
            if not z.centroid:
                return z, i, 0.0
            
            # Hardening fix: ensure entry.vector is valid and has length 24
            dists = [BLA.hamming_distance(entry.vector, z.centroid)
                     for _, entry in content_tokens 
                     if hasattr(entry, 'vector') and entry.vector and len(entry.vector) == 24]
            
            if not dists: continue
            d = min(dists)
            if d < best_dist:
                best_dist, best_idx = d, i
                
        # If the new idea is too far from existing zones, spawn a new one
        if best_dist > ZONE_SPAWN_THRESHOLD and len(self.zones) < self.max_zones:
            self._spawn_zone()
            best_idx = len(self.zones) - 1
            best_dist = 0.0
            
        self.active_idx = best_idx
        return self.zones[best_idx], best_idx, best_dist

    def update(self, content_tokens, turn) -> Dict[str, Any]:
        zone, idx, fit = self.route(content_tokens)
        diag = zone.update(content_tokens, turn)
        diag["zone_idx"] = idx
        diag["zone_fit"] = fit
        
        # v3.7: contradiction-driven pivot
        # If the updated zone now contains contradictions, spawn a new zone pre-seeded with the conflicting noun
        if zone.contradictions and len(self.zones) < self.max_zones:
            for cond_str, _ in zone.contradictions:
                parts = cond_str.split("->")
                if len(parts) == 2:
                    conflicting_noun = parts[1].strip()
                    # Only spawn if this conflicting noun is not already the seed of a newer zone
                    if conflicting_noun and conflicting_noun not in [n for z in self.zones[1:] for n in z.topic_nouns]:
                        self._spawn_zone(seed_noun=conflicting_noun)
                        if self.crg:
                            self.zones[-1].set_crg(self.crg)
                        if self.vocab:
                            self.zones[-1].set_vocab(self.vocab)
        
        # Update active index to the most coherent zone
        cohs = [z.coherence() for z in self.zones]
        self.active_idx = cohs.index(max(cohs))
        
        # v3.7: attempt cross-zone synthesis if multiple zones are stable
        if sum(1 for z in self.zones if z.crystallized) >= 2:
            mt = self.synthesise_meta_thesis(turn)
            if mt: diag["meta_thesis"] = mt.thesis
            
        return diag

    def synthesise_meta_thesis(self, turn: int) -> Optional[MetaThesis]:
        """Attempt to find a link between two different crystallized zones."""
        crystallised = [(i, z) for i, z in enumerate(self.zones) if z.crystallized]
        if len(crystallised) < 2: return None

        shared_edges = []
        # (a) Look for direct CRG edges between zones
        for i, (zi, za) in enumerate(crystallised):
            for j, (zj, zb) in enumerate(crystallised[i+1:], i+1):
                for a in za.topic_nouns:
                    for b in zb.topic_nouns:
                        for e in self.crg.out.get(a, []):
                            if e.dst == b and e.label not in ("contradicts","incompatible_with","auto_proposed"):
                                shared_edges.append({"src":a,"label":e.label,"dst":b,"zone_a":zi,"zone_b":zj,"via":"direct"})

        # (b) Transitive: shared CRG neighbour (e.g. both zones' nouns relate to 'symmetry')
        if not shared_edges:
            for i, (zi, za) in enumerate(crystallised):
                for j, (zj, zb) in enumerate(crystallised[i+1:], i+1):
                    za_neighbours = set()
                    for a in za.topic_nouns:
                        for e in self.crg.out.get(a, []):
                            if e.label not in ("contradicts","incompatible_with"):
                                za_neighbours.add(e.dst)
                        for e in self.crg.into.get(a, []):
                            if e.label not in ("contradicts","incompatible_with"):
                                za_neighbours.add(e.src)
                    for b in zb.topic_nouns:
                        zb_neighbours = set()
                        for e in self.crg.out.get(b, []):
                            if e.label not in ("contradicts","incompatible_with"):
                                zb_neighbours.add(e.dst)
                        for e in self.crg.into.get(b, []):
                            if e.label not in ("contradicts","incompatible_with"):
                                zb_neighbours.add(e.src)
                        shared = za_neighbours & zb_neighbours
                        for s in shared:
                            shared_edges.append({"src":b,"label":"shares_via","dst":s,
                                                 "zone_a":zi,"zone_b":zj,
                                                 "via":f"both zones relate to {s}"})

        if not shared_edges: return None

        # Synthesise a high-level statement
        e = shared_edges[0]
        if e.get("via") and e["via"] != "direct":
            thesis = e["via"] + "."
        else:
            thesis = f"both zones relate to {e['src']} and {e['dst']}."

        mt = MetaThesis(thesis=thesis, zone_ids=[e['zone_a'], e['zone_b']],
                        shared_edges=shared_edges, confidence=0.8, created_at_turn=turn)
        self.meta_theses.append(mt)
        return mt

    def reset(self):
        self.zones = []; self.active_idx = 0; self.meta_theses = []
        self._spawn_zone()

    def state(self) -> Dict[str, Any]:
        """
        Returns the full diagnostic state of the manager.
        Surgically updated to provide deep zone data for the UI.
        """
        st = {
            "num_zones": len(self.zones),
            "active_idx": self.active_idx,
            # Deep export of every zone's internal state
            "zones": [{"crystallized": getattr(z, "crystallized", False), "thesis": getattr(z, "thesis", ""), "contradictions": getattr(z, "contradictions", []), "inferred_nouns": getattr(z, "inferred_nouns", [])} for z in self.zones],
            "meta_theses": [
                {
                    "thesis": mt.thesis,
                    "zone_ids": mt.zone_ids,
                    "confidence": mt.confidence
                } for mt in self.meta_theses
            ]
        }
        return st

    def decay_all(self, age_turns=1.0):
        """Decay all zones' evidence."""
        for z in self.zones:
            z.decay(age_turns)

    def tick_all(self):
        """Tick all zones with evidence."""
        for z in self.zones:
            if z.evidence:
                if hasattr(z, 'ticks_taken') and z.ticks_taken > 50:
                    continue
                z.tick()
                z.ticks_taken = getattr(z, 'ticks_taken', 0) + 1

    def mature_all(self, n: int = 3):
        """Trigger autonomous thinking across all active zones."""
        for _ in range(n):
            for z in self.zones:
                if z.evidence:
                    # Added safety check: prevent infinite ticking
                    if hasattr(z, 'ticks_taken') and z.ticks_taken > 50:
                        continue
                    z.tick()
                    z.ticks_taken = getattr(z, 'ticks_taken', 0) + 1
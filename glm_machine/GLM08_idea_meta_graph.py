# ══════════════════════════════════════════════════════════════════════════════
# §08  IDEA META-GRAPH — LONG-TERM MEMORY (v3.7.6 Hardened)
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from pathlib import Path

# IMPORT SUBSTRATE
from GLM01_substrate import BLA

@dataclass
class CrystallisedIdea:
    """A snapshot of a stable idea for long-term storage."""
    idea_id: str
    centroid: List[int]
    topic_nouns: List[str]
    thesis: str
    backbone: List[Dict[str, str]]
    peak_coherence: float
    turn_count: int
    created_at_turn: int

class IdeaMetaGraph:
    """Handles persistence and 'Warm-Start' matching of prior ideas."""
    
    def __init__(self, path: str = "idea_meta_graph.json"):
        self.path = Path(path)
        self.ideas: List[CrystallisedIdea] = []
        self.load()

    def load(self):
        """Load saved ideas from the workspace."""
        if not self.path.exists(): 
            self.ideas = []
            return
        try:
            with open(self.path, 'r') as f:
                data = json.load(f)
            self.ideas = [CrystallisedIdea(**d) for d in data.get("ideas", [])]
        except Exception: 
            self.ideas = []

    def save(self):
        """Write all ideas to the JSON file."""
        try:
            with open(self.path, 'w') as f:
                json.dump({"ideas": [asdict(i) for i in self.ideas]}, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save meta-graph: {e}")

    def record(self, zone: Any, idea_id: Optional[str] = None) -> CrystallisedIdea:
        """Convert an active IdeaZone into a permanent record."""
        if not idea_id:
            # Generate a deterministic ID based on the thesis text
            h = hashlib.sha256(zone.thesis.encode()).hexdigest()[:8]
            iid = f"idea_{len(self.ideas)+1}_{h}"
        else:
            iid = idea_id

        # Serialize backbone safely
        serialized_backbone = []
        for e in zone.crg_backbone:
            if hasattr(e, 'src'):
                serialized_backbone.append({"src": e.src, "label": e.label, "dst": e.dst})
            elif isinstance(e, dict):
                serialized_backbone.append(e)

        ci = CrystallisedIdea(
            idea_id=iid, 
            centroid=list(zone.centroid),
            topic_nouns=list(zone.topic_nouns), 
            thesis=zone.thesis,
            backbone=serialized_backbone,
            peak_coherence=zone.peak_coherence, 
            turn_count=zone.turns,
            created_at_turn=zone.turns
        )
        self.ideas.append(ci)
        self.save()
        return ci

    def match(self, tokens_vectors: List[List[int]], topic_nouns: List[str], 
              max_hamming: int = 8, min_noun_overlap: int = 1) -> Optional[CrystallisedIdea]:
        """Check if current input matches a previously saved idea (Warm-Start)."""
        if not self.ideas or not tokens_vectors: return None
        
        best, best_score = None, 0.0
        for ci in self.ideas:
            # Calculate geometric proximity
            valid_vecs = [v for v in tokens_vectors if v and len(v) == 24]
            dists = [BLA.hamming_distance(v, ci.centroid) for v in valid_vecs]
            min_d = min(dists) if dists else 999
            
            if min_d > max_hamming: continue
            
            # Calculate conceptual overlap
            overlap = len(set(topic_nouns) & set(ci.topic_nouns))
            if overlap < min_noun_overlap: continue
            
            # Score: Proximity + Overlap
            score = (1.0 - min_d/24.0) + 0.5 * overlap
            if score > best_score:
                best_score, best = score, ci
        return best

    def stats(self) -> Dict[str, Any]:
        return {
            "total_ideas": len(self.ideas),
            "avg_peak_coherence": (sum(i.peak_coherence for i in self.ideas)/len(self.ideas)
                                    if self.ideas else 0.0)
        }
#!/usr/bin/env python3
"""
GLM PERSISTENCE — Long-Term Memory & Growth
==============================================
The GLM persists everything:
1. What it's learned (vocabulary, definitions, edges)
2. What it's computed (tool results, verifications)
3. What it's observed (insights, patterns, gaps)
4. How it's grown (version history, capability tracking)

This makes the GLM a GROWING system — each session builds on the last.
Every conversation makes it smarter. Every computation adds to its knowledge.
Every observation persists across sessions.

The growth log tracks:
- New vocabulary learned
- New CRG edges discovered
- New insights generated
- Coherence improvements
- Capability milestones
"""

import os
import json
import time
from typing import Dict, List, Any, Optional


class GLMPersistence:
    """Long-term persistence for the GLM."""

    def __init__(self, base_dir: str = "glm_state"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

        self.vocab_file = os.path.join(base_dir, "learned_vocab.json")
        self.edges_file = os.path.join(base_dir, "learned_edges.json")
        self.insights_file = os.path.join(base_dir, "insights.json")
        self.growth_file = os.path.join(base_dir, "growth_log.json")
        self.sessions_file = os.path.join(base_dir, "sessions.json")

        # Load existing state
        self.learned_vocab = self._load(self.vocab_file, {})
        self.learned_edges = self._load(self.edges_file, [])
        self.insights = self._load(self.insights_file, [])
        self.growth_log = self._load(self.growth_file, [])
        self.sessions = self._load(self.sessions_file, [])

    def save_vocab(self, word: str, definition: str, vector: list,
                   source: str = "learned"):
        """Save a learned word."""
        self.learned_vocab[word] = {
            "definition": definition,
            "vector": vector,
            "source": source,
            "timestamp": time.time(),
        }
        self._save(self.vocab_file, self.learned_vocab)
        self._log_growth("vocab", f"Learned: {word}")

    def save_edge(self, src: str, label: str, dst: str, source: str = "learned"):
        """Save a learned edge."""
        edge = {"src": src, "label": label, "dst": dst,
                "source": source, "timestamp": time.time()}
        self.learned_edges.append(edge)
        self._save(self.edges_file, self.learned_edges)
        self._log_growth("edge", f"Learned: {src} --{label}--> {dst}")

    def save_insight(self, insight: str, confidence: float = 1.0):
        """Save an insight."""
        self.insights.append({
            "text": insight,
            "confidence": confidence,
            "timestamp": time.time(),
        })
        self._save(self.insights_file, self.insights)
        self._log_growth("insight", insight)

    def save_session(self, query: str, response: str, tools_used: list = None,
                     coherence: float = 0.0):
        """Save a conversation session."""
        self.sessions.append({
            "query": query,
            "response_len": len(response.split()),
            "tools_used": tools_used or [],
            "coherence": coherence,
            "timestamp": time.time(),
        })
        # Keep last 100 sessions
        if len(self.sessions) > 100:
            self.sessions = self.sessions[-100:]
        self._save(self.sessions_file, self.sessions)

    def get_context(self) -> str:
        """Get persistent context for the GLM."""
        parts = []

        # Recent vocabulary
        recent_vocab = list(self.learned_vocab.items())[-5:]
        if recent_vocab:
            parts.append("Recently learned vocabulary:")
            for word, data in recent_vocab:
                parts.append(f"  {word}: {data.get('definition', 'no definition')}")

        # Recent insights
        recent_insights = self.insights[-5:]
        if recent_insights:
            parts.append("\nRecent insights:")
            for insight in recent_insights:
                parts.append(f"  - {insight['text']}")

        # Growth summary
        if self.growth_log:
            parts.append(f"\nTotal growth: {len(self.growth_log)} events")
            parts.append(f"  Vocabulary: {len(self.learned_vocab)} words learned")
            parts.append(f"  Edges: {len(self.learned_edges)} edges learned")
            parts.append(f"  Insights: {len(self.insights)} insights")

        return "\n".join(parts)

    def get_stats(self) -> Dict[str, Any]:
        """Get persistence statistics."""
        return {
            "learned_vocab": len(self.learned_vocab),
            "learned_edges": len(self.learned_edges),
            "insights": len(self.insights),
            "sessions": len(self.sessions),
            "growth_events": len(self.growth_log),
        }

    def inject_into_glm(self, glm_instance):
        """Inject persisted knowledge into a GLM instance."""
        injected_vocab = 0
        injected_edges = 0

        # Inject learned vocabulary
        for word, data in self.learned_vocab.items():
            if word not in glm_instance.vocab:
                try:
                    from GLM01_substrate import WordEntry, BLA, _get_mog_category, LEECH_ENGINE, GOLAY_ENGINE
                    import hashlib
                    h = hashlib.sha256(word.lower().encode()).digest()
                    seed_bits = [(byte >> k) & 1 for byte in h for k in range(7, -1, -1)][:24]
                    try:
                        snapped, _ = GOLAY_ENGINE.snap_to_codeword(seed_bits)
                    except:
                        snapped = seed_bits
                    nrci = float(LEECH_ENGINE.calculate_nrci(snapped))
                    entry = WordEntry(
                        word=word, vector=snapped, role="NOUN",
                        ubp_id=f"PERSIST_{word.upper()}", nrci=nrci,
                        golay_codeword=snapped, fold3=BLA.fold24_to3(snapped),
                        mog_category=_get_mog_category(snapped)
                    )
                    entry.definition = data.get("definition", "")
                    glm_instance.vocab[word] = entry
                    injected_vocab += 1
                except:
                    pass

        # Inject learned edges
        for edge_data in self.learned_edges:
            src, label, dst = edge_data["src"], edge_data["label"], edge_data["dst"]
            existing = {e.dst for e in glm_instance.crg.out.get(src, [])}
            if dst not in existing:
                glm_instance.crg.add_edge(src, label, dst)
                injected_edges += 1

        return injected_vocab, injected_edges

    def _log_growth(self, event_type: str, description: str):
        """Log a growth event."""
        self.growth_log.append({
            "type": event_type,
            "description": description,
            "timestamp": time.time(),
        })
        if len(self.growth_log) > 1000:
            self.growth_log = self.growth_log[-1000:]
        self._save(self.growth_file, self.growth_log)

    def _load(self, filepath: str, default: Any) -> Any:
        """Load JSON from file."""
        if not os.path.exists(filepath):
            return default
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return default

    def _save(self, filepath: str, data: Any):
        """Save JSON to file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass


class GrowthTracker:
    """Tracks the GLM's growth over time."""

    def __init__(self, persistence: GLMPersistence):
        self.persistence = persistence

    def record_capability(self, capability: str, level: float):
        """Record a capability level."""
        self.persistence._log_growth("capability", f"{capability}: {level:.2f}")

    def record_coherence(self, coherence: float):
        """Record a coherence measurement."""
        self.persistence._log_growth("coherence", f"Coherence: {coherence:.3f}")

    def get_growth_summary(self) -> str:
        """Get a summary of growth."""
        stats = self.persistence.get_stats()
        return (f"Growth: {stats['learned_vocab']} vocab, "
                f"{stats['learned_edges']} edges, "
                f"{stats['insights']} insights, "
                f"{stats['sessions']} sessions")


if __name__ == "__main__":
    print("=== GLM Persistence — Long-Term Memory & Growth ===")
    p = GLMPersistence()
    print(f"State: {p.get_stats()}")

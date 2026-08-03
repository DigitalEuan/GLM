#!/usr/bin/env python3
"""
GLM38 — Speculative Reasoning Engine
======================================
The GLM's superpower: working things out from what it knows.
When the answer isn't directly stored, the GLM reasons from
known relationships, geometric proximity, and domain knowledge
to produce speculative answers — clearly marked as such.

This is what makes the GLM more than a database: it can THINK.
"""

import re
import math
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import defaultdict


# ═══════════════════════════════════════════════════════════════════════════
# §1  SPECULATIVE INFERENCE — Reason from known to unknown
# ═══════════════════════════════════════════════════════════════════════════

class SpeculativeEngine:
    """
    When the GLM doesn't know an answer directly, this engine
    reasons from what it DOES know to produce a speculative answer.
    
    Every speculative answer is clearly marked as such.
    """
    
    def __init__(self, crg, vocab_dict, kb=None):
        self.crg = crg
        self.vocab = vocab_dict
        self.kb = kb or {}
        self._kb_indexed = None
    
    def _get_kb_indexed(self):
        """Lazy-load indexed KB."""
        if self._kb_indexed is None:
            from GLM01_substrate import _load_system_kb
            self._kb_indexed = _load_system_kb()
        return self._kb_indexed
    
    def speculate(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Try to work out an answer from what the GLM knows.
        Returns a speculative answer or None.
        """
        q = query.lower().strip()
        
        # Strategy 1: Attribute inference
        # "What is the [attribute] of [entity]?"
        result = self._infer_attribute(q)
        if result:
            return result
        
        # Strategy 2: Relationship inference
        # "How does X relate to Y?"
        result = self._infer_relationship(q)
        if result:
            return result
        
        # Strategy 3: Category inference
        # "What type/kind of thing is X?"
        result = self._infer_category(q)
        if result:
            return result
        
        # Strategy 4: Action inference
        # "What does X do?" / "What is X used for?"
        result = self._infer_action(q)
        if result:
            return result
        
        # Strategy 5: Composition inference
        # "What is X made of?" / "What contains X?"
        result = self._infer_composition(q)
        if result:
            return result
        
        # Strategy 6: Explanation from fragments
        # "Explain X in simple terms"
        result = self._explain_from_fragments(q)
        if result:
            return result
        
        # Strategy 7: Factual recall from KB
        result = self._recall_fact(q)
        if result:
            return result
        
        return None
    
    def _infer_attribute(self, q: str) -> Optional[Dict[str, Any]]:
        """
        Infer an attribute of an entity from known relationships.
        E.g., "What is the speed of light?" → we know light, speed is an attribute
        """
        # Pattern: "what is the [attribute] of [entity]"
        m = re.search(r'what\s+is\s+(?:the\s+)?(\w+)\s+of\s+(?:the\s+)?(\w+)', q)
        if not m:
            m = re.search(r'what\s+(?:is|are)\s+(?:the\s+)?(\w+)\s+(?:of|for)\s+(\w+)', q)
        if not m:
            return None
        
        attribute = m.group(1)
        entity = m.group(2)
        
        # Check if we know the entity
        if entity not in self.vocab and entity not in self.crg.out:
            return None
        
        # Look for the attribute in the entity's KB entry
        kb = self._get_kb_indexed()
        for uid, entry in kb.items():
            name = entry.get('name', '').lower()
            desc = entry.get('desc', entry.get('lexicon', '')).lower()
            
            if entity in name or entity in desc:
                # Check if the attribute is mentioned
                if attribute in desc:
                    # Extract the relevant sentence
                    sentences = re.split(r'[.!?]+', desc)
                    for sent in sentences:
                        if attribute in sent.lower() and entity in sent.lower():
                            return {
                                "type": "speculative_attribute",
                                "entity": entity,
                                "attribute": attribute,
                                "answer": sent.strip(),
                                "confidence": 0.6,
                                "speculative": True,
                            }
        
        # Check vocab definition
        if entity in self.vocab:
            defn = getattr(self.vocab[entity], 'definition', '')
            if defn and attribute in defn.lower():
                return {
                    "type": "speculative_attribute",
                    "entity": entity,
                    "attribute": attribute,
                    "answer": defn,
                    "confidence": 0.5,
                    "speculative": True,
                }
        
        return None
    
    def _infer_relationship(self, q: str) -> Optional[Dict[str, Any]]:
        """
        Infer how X relates to Y from CRG edges.
        """
        # Extract two entities
        m = re.search(r'(?:how|what)\s+(?:does|do|is|are)\s+(\w+)\s+(?:relate|connected|linked)\s+to\s+(\w+)', q)
        if not m:
            m = re.search(r'relationship\s+between\s+(\w+)\s+and\s+(\w+)', q)
        if not m:
            m = re.search(r'(\w+)\s+(?:and|with|versus|vs)\s+(\w+)', q)
        if not m:
            return None
        
        x, y = m.group(1), m.group(2)
        
        # Check CRG for direct relationships
        rels = self.crg.relate(x, y)
        if rels:
            rel_str = ", ".join(r.replace("_", " ") for r in rels)
            return {
                "type": "speculative_relationship",
                "x": x, "y": y,
                "answer": f"Based on what I know, {x} {rel_str} {y}.",
                "confidence": 0.7,
                "speculative": True,
            }
        
        # Check for 2-hop relationships
        path = self.crg.shortest_path(x, y, max_hops=2)
        if path:
            chain = " → ".join([path[0].src] + [e.dst for e in path])
            rels = " → ".join([e.label.replace("_", " ") for e in path])
            return {
                "type": "speculative_relationship",
                "x": x, "y": y,
                "answer": f"From what I can infer: {chain} ({rels}).",
                "confidence": 0.5,
                "speculative": True,
            }
        
        return None
    
    def _infer_category(self, q: str) -> Optional[Dict[str, Any]]:
        """
        Infer what type/kind of thing something is.
        """
        m = re.search(r'what\s+(?:type|kind|sort)\s+of\s+(\w+)\s+is\s+(?:a\s+|an\s+|the\s+)?(\w+)', q)
        if not m:
            m = re.search(r'is\s+(?:a\s+|an\s+|the\s+)?(\w+)\s+(?:a|an)\s+(\w+)', q)
        if not m:
            return None
        
        entity = m.group(2) if m.lastindex >= 2 else m.group(1)
        
        # Check CRG for is_a relationships
        if entity in self.crg.out:
            for edge in self.crg.out[entity]:
                if edge.label == "is_a":
                    return {
                        "type": "speculative_category",
                        "entity": entity,
                        "answer": f"Based on what I know, {entity} is a {edge.dst}.",
                        "confidence": 0.7,
                        "speculative": True,
                    }
        
        return None
    
    def _infer_action(self, q: str) -> Optional[Dict[str, Any]]:
        """
        Infer what something does or is used for.
        """
        m = re.search(r'what\s+does\s+(?:a\s+|an\s+|the\s+)?(\w+)\s+do', q)
        if not m:
            m = re.search(r'what\s+is\s+(\w+)\s+used\s+for', q)
        if not m:
            m = re.search(r'what\s+does\s+(\w+)\s+mean', q)
        if not m:
            return None
        
        entity = m.group(1)
        
        # Check CRG for action relationships
        if entity in self.crg.out:
            actions = []
            for edge in self.crg.out[entity]:
                if edge.label in ("generates", "carries", "produces", "measures", "preserves", "contains"):
                    actions.append(f"{edge.label.replace('_', ' ')} {edge.dst}")
            if actions:
                return {
                    "type": "speculative_action",
                    "entity": entity,
                    "answer": f"From what I know, {entity} {', '.join(actions[:3])}.",
                    "confidence": 0.6,
                    "speculative": True,
                }
        
        # Check vocab definition
        if entity in self.vocab:
            defn = getattr(self.vocab[entity], 'definition', '')
            if defn:
                return {
                    "type": "speculative_action",
                    "entity": entity,
                    "answer": f"From what I know: {defn}",
                    "confidence": 0.6,
                    "speculative": True,
                }
        
        return None
    
    def _infer_composition(self, q: str) -> Optional[Dict[str, Any]]:
        """
        Infer what something is made of or what contains it.
        """
        m = re.search(r'what\s+is\s+(\w+)\s+made\s+of', q)
        if not m:
            m = re.search(r'what\s+(?:is|are)\s+(?:in|inside)\s+(\w+)', q)
        if not m:
            return None
        
        entity = m.group(1)
        
        # Check CRG for contains relationships
        if entity in self.crg.into:
            parts = []
            for edge in self.crg.into[entity]:
                if edge.label == "contains":
                    parts.append(edge.src)
            if parts:
                return {
                    "type": "speculative_composition",
                    "entity": entity,
                    "answer": f"Based on what I know, {entity} contains {', '.join(parts[:5])}.",
                    "confidence": 0.6,
                    "speculative": True,
                }
        
        return None
    
    def _explain_from_fragments(self, q: str) -> Optional[Dict[str, Any]]:
        """
        Build an explanation from fragments of knowledge.
        When asked to explain something, gather what we know and combine it.
        """
        m = re.search(r'explain\s+(\w+(?:\s+\w+)?)', q)
        if not m:
            m = re.search(r'what\s+is\s+(\w+(?:\s+\w+)?)', q)
        if not m:
            return None
        
        topic = m.group(1).strip()
        
        # Gather fragments from multiple sources
        fragments = []
        
        # From vocab definition
        if topic in self.vocab:
            defn = getattr(self.vocab[topic], 'definition', '')
            if defn:
                fragments.append(defn)
        
        # From CRG relationships
        if topic in self.crg.out:
            for edge in self.crg.out[topic][:5]:
                if edge.label not in ("auto_proposed", "co_occurs"):
                    fragments.append(f"{topic} {edge.label.replace('_', ' ')} {edge.dst}")
        
        # From CRG incoming
        if topic in self.crg.into:
            for edge in self.crg.into[topic][:3]:
                if edge.label not in ("auto_proposed", "co_occurs"):
                    fragments.append(f"{edge.src} {edge.label.replace('_', ' ')} {topic}")
        
        # From KB
        kb = self._get_kb_indexed()
        for uid, entry in kb.items():
            name = entry.get('name', '').lower()
            desc = entry.get('desc', '').lower()
            if topic in name or topic in desc:
                desc_text = entry.get('desc', '')
                if desc_text and len(desc_text) > 20:
                    fragments.append(desc_text[:200])
                    break
        
        if fragments:
            # Combine fragments into a coherent explanation
            combined = ". ".join(fragments[:4])
            if not combined.endswith("."):
                combined += "."
            return {
                "type": "speculative_explanation",
                "topic": topic,
                "answer": combined,
                "confidence": 0.5,
                "speculative": True,
                "fragments_used": len(fragments),
            }
        
        return None
    
    def _recall_fact(self, q: str) -> Optional[Dict[str, Any]]:
        """
        Try to recall a fact from the KB that answers the question.
        """
        # Extract key words from the question
        stop = {"what", "is", "the", "a", "an", "of", "how", "does", "do", "can",
                "will", "would", "should", "could", "may", "might", "must", "tell",
                "me", "about", "explain", "describe", "define", "why", "when",
                "where", "which", "who", "whom", "whose", "and", "or", "but",
                "for", "with", "to", "in", "on", "at", "by", "from", "it", "this"}
        
        words = [w for w in re.findall(r'\b[a-z]{3,}\b', q) if w not in stop]
        
        if len(words) < 1:
            return None
        
        # Search KB for entries matching the question words
        kb = self._get_kb_indexed()
        best_match = None
        best_score = 0
        
        for uid, entry in kb.items():
            name = entry.get('name', '').lower()
            desc = entry.get('desc', '').lower()
            
            score = 0
            for word in words:
                if word in name:
                    score += 3
                if word in desc:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = entry
        
        if best_match and best_score >= 3:
            desc = best_match.get('desc', '')
            name = best_match.get('name', '')
            if desc:
                # Take first sentence
                m = re.match(r'([^.]{20,}\.)', desc)
                first_sent = m.group(1).strip() if m else desc[:200]
                return {
                    "type": "speculative_recall",
                    "answer": first_sent,
                    "confidence": 0.6,
                    "speculative": True,
                }
        
        return None


# ═══════════════════════════════════════════════════════════════════════════
# §2  RATE PROBLEM SOLVER — "5 machines, 5 minutes, 5 widgets"
# ═══════════════════════════════════════════════════════════════════════════

def solve_rate_problem(query: str) -> Optional[Dict[str, Any]]:
    """
    Solve rate/work problems.
    E.g., "If it takes 5 machines 5 minutes to make 5 widgets,
    how long would it take 100 machines to make 100 widgets?"
    """
    q = query.lower()
    
    # Pattern: "X machines Y minutes Z widgets ... how long for A machines B widgets"
    m = re.search(
        r'(\d+)\s+machines?\s+(\d+)\s+minutes?\s+(?:to\s+make\s+)?(\d+)\s+widgets?.*?(\d+)\s+machines?.*?(\d+)\s+widgets?',
        q
    )
    if not m:
        return None
    
    given_machines = int(m.group(1))
    given_minutes = int(m.group(2))
    given_widgets = int(m.group(3))
    want_machines = int(m.group(4))
    want_widgets = int(m.group(5))
    
    # Rate: given_machines make given_widgets in given_minutes
    # Rate per machine: given_widgets / (given_machines * given_minutes)
    rate_per_machine = given_widgets / (given_machines * given_minutes)
    
    # Time for want_machines to make want_widgets:
    # want_widgets = rate_per_machine * want_machines * time
    # time = want_widgets / (rate_per_machine * want_machines)
    time_needed = want_widgets / (rate_per_machine * want_machines)
    
    return {
        "type": "rate_problem",
        "answer": f"{int(time_needed)} minutes",
        "reasoning": f"Each machine makes {rate_per_machine:.4f} widgets per minute. "
                     f"{want_machines} machines make {want_machines * rate_per_machine:.1f} widgets per minute. "
                     f"To make {want_widgets} widgets: {want_widgets} / {want_machines * rate_per_machine:.1f} = {time_needed:.1f} minutes.",
        "confidence": 0.95,
    }


# ═══════════════════════════════════════════════════════════════════════════
# §3  FORMAT SPECULATIVE ANSWER
# ═══════════════════════════════════════════════════════════════════════════

def format_speculative(result: Dict[str, Any]) -> str:
    """Format a speculative answer with clear marking."""
    if not result:
        return ""
    
    answer = result.get("answer", "")
    confidence = result.get("confidence", 0)
    speculative = result.get("speculative", False)
    rtype = result.get("type", "unknown")
    
    if speculative:
        # Mark clearly as speculative
        conf_pct = int(confidence * 100)
        return f"[Speculative ({conf_pct}%)] {answer}"
    else:
        return f"[Reasoned] {answer}"


# ═══════════════════════════════════════════════════════════════════════════
# §4  INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=== GLM38 Speculative Reasoning Engine ===")
    
    # Test rate problem
    print("\n--- Rate Problem ---")
    r = solve_rate_problem("If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?")
    if r:
        print(f"Answer: {r['answer']}")
        print(f"Reasoning: {r['reasoning']}")
    
    # Test speculative reasoning
    print("\n--- Speculative Reasoning ---")
    # These would need actual CRG/vocab, so just test the patterns
    test_queries = [
        "What is the speed of light?",
        "What planet is closest to the Sun?",
        "Explain gravity in simple terms",
        "What does ubiquitous mean?",
        "How does gravity relate to mass?",
    ]
    for q in test_queries:
        print(f"Q: {q}")
        # Would call speculate() here with real data
        print()

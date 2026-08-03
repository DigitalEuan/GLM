#!/usr/bin/env python3
"""
GLM37 — Research Suggester & Task Agent
=========================================
Gives the GLM agent-like abilities:
1. Research Suggestions — when it hits a knowledge gap, suggest what to explore
2. Task Decomposition — break complex queries into steps
3. Web Research — search the web and learn from results
4. Smart Learning — learn from conversation, not bulk ingestion

Philosophy: The GLM doesn't need to know everything. It needs to know
HOW to find out and HOW to learn. Light, efficient, geometric.
"""

import re
import json
import hashlib
from typing import List, Dict, Optional, Tuple, Any, Set
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════════════════
# §1  KNOWLEDGE GAP DETECTION
# ═══════════════════════════════════════════════════════════════════════════

# Topic graph — how concepts relate to research directions
_TOPIC_GRAPH = {
    # Physics
    "gravity": ["general relativity", "gravitational waves", "black holes", "quantum gravity", "spacetime curvature"],
    "quantum": ["quantum mechanics", "quantum computing", "quantum entanglement", "superposition", "wave function"],
    "relativity": ["special relativity", "general relativity", "time dilation", "spacetime", "E=mc²"],
    "thermodynamics": ["entropy", "temperature", "heat transfer", "laws of thermodynamics", "statistical mechanics"],
    "electromagnetism": ["Maxwell's equations", "light", "photons", "electric field", "magnetic field"],
    "particle": ["Standard Model", "quarks", "leptons", "bosons", "Higgs boson", "particle accelerator"],
    "cosmology": ["Big Bang", "dark matter", "dark energy", "cosmic microwave background", "expansion of universe"],
    "nuclear": ["fission", "fusion", "radioactivity", "nuclear force", "binding energy"],
    
    # Mathematics
    "calculus": ["derivatives", "integrals", "limits", "differential equations", "multivariable calculus"],
    "algebra": ["linear algebra", "group theory", "ring theory", "abstract algebra", "matrices"],
    "geometry": ["Euclidean geometry", "non-Euclidean geometry", "topology", "differential geometry", "fractals"],
    "number theory": ["prime numbers", "modular arithmetic", "Fermat's last theorem", "Riemann hypothesis"],
    "statistics": ["probability", "distributions", "hypothesis testing", "regression", "Bayesian inference"],
    "analysis": ["real analysis", "complex analysis", "functional analysis", "measure theory"],
    
    # Chemistry
    "chemistry": ["periodic table", "chemical bonds", "reactions", "organic chemistry", "biochemistry"],
    "organic": ["hydrocarbons", "polymers", "biochemistry", "pharmaceuticals", "carbon compounds"],
    "inorganic": ["metals", "minerals", "crystal structures", "coordination compounds"],
    
    # Biology
    "biology": ["cells", "DNA", "evolution", "ecology", "genetics"],
    "genetics": ["DNA", "genes", "chromosomes", "heredity", "genetic engineering"],
    "evolution": ["natural selection", "adaptation", "speciation", "fossil record", "phylogenetics"],
    "neuroscience": ["brain", "neurons", "consciousness", "synapses", "neurotransmitters"],
    "ecology": ["ecosystems", "biodiversity", "food webs", "conservation", "climate change"],
    
    # Computer Science
    "algorithm": ["sorting", "searching", "optimization", "complexity theory", "data structures"],
    "machine learning": ["neural networks", "deep learning", "reinforcement learning", "natural language processing"],
    "programming": ["Python", "JavaScript", "algorithms", "data structures", "software engineering"],
    "cryptography": ["encryption", "hashing", "digital signatures", "blockchain", "quantum cryptography"],
    
    # UBP-specific
    "substrate": ["24-bit substrate", "Golay code", "Leech lattice", "error correction", "NRCI"],
    "coherence": ["NRCI", "coherence snaps", "symmetry tax", "ontological health"],
    "observer": ["observer constant", "Y constant", "measurement", "observation effect"],
    "golay": ["error correction", "24-bit codewords", "Miracle Octad Generator", "Mathieu group M24"],
    "leech": ["24-dimensional lattice", "sphere packing", "symmetry", "Barnes-Wall lattice"],
    "ubp": ["Universal Binary Principle", "computational substrate", "geometric language", "triadic monad"],
}


def detect_knowledge_gap(query: str, response: str, vocab: Dict, crg) -> Optional[Dict[str, Any]]:
    """
    Detect when the GLM's response indicates a knowledge gap.
    Returns suggestions for further research.
    """
    q = query.lower()
    r = response.lower()
    
    # Check if response is too short or generic
    is_generic = (
        len(response) < 100 or
        "i am listening" in r or
        "no verified vector" in r or
        "forming" in r and "crystallized" not in r
    )
    
    # Extract topic from query
    stop = {"what", "is", "the", "a", "an", "of", "how", "does", "do", "can",
            "will", "would", "should", "could", "may", "might", "must", "tell",
            "me", "about", "explain", "describe", "define", "what", "why",
            "when", "where", "which", "who", "whom", "whose", "and", "or",
            "but", "for", "with", "to", "in", "on", "at", "by", "from"}
    
    topic_words = [w for w in re.findall(r'\b[a-z]{3,}\b', q) if w not in stop]
    
    if not topic_words:
        return None
    
    primary_topic = topic_words[0]
    
    # Find related research directions
    suggestions = []
    for keyword, directions in _TOPIC_GRAPH.items():
        if keyword in q or keyword in primary_topic:
            suggestions.extend(directions)
        # Also check if any topic word is in the graph
        for tw in topic_words:
            if tw in keyword or keyword in tw:
                suggestions.extend(directions)
    
    # Check CRG for related concepts
    crg_suggestions = []
    for tw in topic_words:
        if tw in crg.out:
            for edge in crg.out[tw][:5]:
                if edge.label not in ("auto_proposed", "co_occurs"):
                    crg_suggestions.append(edge.dst)
        if tw in crg.into:
            for edge in crg.into[tw][:5]:
                if edge.label not in ("auto_proposed", "co_occurs"):
                    crg_suggestions.append(edge.src)
    
    # Deduplicate and limit
    all_suggestions = list(dict.fromkeys(suggestions + crg_suggestions))[:5]
    
    if all_suggestions or is_generic:
        return {
            "topic": primary_topic,
            "is_gap": is_generic,
            "suggestions": all_suggestions,
            "related_concepts": crg_suggestions[:3],
        }
    
    return None


def format_research_suggestions(gap: Dict[str, Any]) -> str:
    """Format research suggestions for display."""
    topic = gap.get("topic", "this topic")
    suggestions = gap.get("suggestions", [])
    related = gap.get("related_concepts", [])
    
    parts = []
    
    if suggestions:
        suggest_str = ", ".join(suggestions[:4])
        parts.append(f"[Research] To explore '{topic}' further, look into: {suggest_str}.")
    
    if related:
        related_str = ", ".join(related[:3])
        parts.append(f"[Related] Connected concepts: {related_str}.")
    
    parts.append(f"[Tip] You can ask me to 'learn about [topic]' or upload a document for me to study.")
    
    return " ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# §2  TASK DECOMPOSITION
# ═══════════════════════════════════════════════════════════════════════════

def detect_task(query: str) -> Optional[Dict[str, Any]]:
    """
    Detect if the query is a task (not just a question).
    Returns task decomposition or None.
    """
    q = query.lower().strip()
    
    # Task indicators
    task_patterns = [
        (r"(?:can you |please )?(?:help me |)(?:create|build|make|generate|write|design|develop)\s+(.+)", "create"),
        (r"(?:can you |please )?(?:analyze|examine|investigate|study|research)\s+(.+)", "analyze"),
        (r"(?:can you |please )?(?:compare|contrast)\s+(.+?)(?:\s+and\s+|\s+with\s+)(.+)", "compare"),
        (r"(?:can you |please )?(?:summarize|summarise|overview)\s+(.+)", "summarize"),
        (r"(?:can you |please )?(?:explain|describe|clarify)\s+(.+?)(?:\s+in\s+detail|\s+step\s+by\s+step)?$", "explain"),
        (r"(?:can you |please )?(?:find|search|look up|locate)\s+(.+)", "research"),
        (r"(?:can you |please )?(?:list|enumerate|show)\s+(.+)", "list"),
        (r"(?:can you |please )?(?:calculate|compute|determine|figure out)\s+(.+)", "compute"),
        (r"(?:i want to |i need to |help me )?(?:learn|understand|figure out)\s+(.+)", "learn"),
        (r"(?:set a task|do this|here'?s a task|task:)\s*(.+)", "task"),
    ]
    
    for pattern, task_type in task_patterns:
        m = re.match(pattern, q)
        if m:
            subject = m.group(1).strip()
            # Clean up
            subject = re.sub(r'\s+', ' ', subject)
            return {
                "type": task_type,
                "subject": subject,
                "steps": _decompose_task(task_type, subject),
            }
    
    return None


def _decompose_task(task_type: str, subject: str) -> List[str]:
    """Break a task into steps."""
    templates = {
        "create": [
            f"Understand the requirements for: {subject}",
            f"Research existing approaches to {subject}",
            f"Design the structure/architecture",
            f"Implement the core components",
            f"Test and refine",
        ],
        "analyze": [
            f"Gather information about: {subject}",
            f"Identify key components and relationships",
            f"Examine patterns and anomalies",
            f"Draw conclusions and insights",
        ],
        "compare": [
            f"Identify the items to compare: {subject}",
            f"Define comparison criteria",
            f"Evaluate each item against criteria",
            f"Summarize similarities and differences",
        ],
        "summarize": [
            f"Identify the main points of: {subject}",
            f"Extract key facts and arguments",
            f"Organize into logical structure",
            f"Write concise summary",
        ],
        "explain": [
            f"Define the concept: {subject}",
            f"Provide context and background",
            f"Break down into components",
            f"Give examples and analogies",
        ],
        "research": [
            f"Define the research question: {subject}",
            f"Search for relevant information",
            f"Evaluate source quality and relevance",
            f"Synthesize findings",
        ],
        "list": [
            f"Identify the category: {subject}",
            f"Enumerate items systematically",
            f"Provide brief descriptions",
        ],
        "compute": [
            f"Identify the computation needed: {subject}",
            f"Gather input values",
            f"Apply appropriate formulas",
            f"Verify the result",
        ],
        "learn": [
            f"Identify what you want to learn: {subject}",
            f"Find foundational concepts",
            f"Study key principles",
            f"Practice with examples",
        ],
        "task": [
            f"Understand the task: {subject}",
            f"Break into sub-tasks",
            f"Execute each sub-task",
            f"Verify completion",
        ],
    }
    
    return templates.get(task_type, [f"Process: {subject}"])


def format_task_plan(task: Dict[str, Any]) -> str:
    """Format a task plan for display."""
    task_type = task.get("type", "task")
    subject = task.get("subject", "this")
    steps = task.get("steps", [])
    
    parts = [f"[Task] {task_type.capitalize()}: {subject}"]
    
    if steps:
        parts.append("[Plan]")
        for i, step in enumerate(steps, 1):
            parts.append(f"  {i}. {step}")
    
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
# §3  WEB RESEARCH CAPABILITY
# ═══════════════════════════════════════════════════════════════════════════

def generate_search_query(query: str) -> str:
    """Generate an optimized search query from a natural language question."""
    q = query.lower().strip()
    
    # Remove question words
    q = re.sub(r'^(what|how|why|when|where|which|who|can|does|is|are|was|were)\s+', '', q)
    q = re.sub(r'\s+(is|are|was|were|does|do|did|can|could|would|should|will|shall)\s+', ' ', q)
    q = re.sub(r'\?$', '', q)
    q = re.sub(r'\s+', ' ', q).strip()
    
    return q


def extract_key_facts(web_content: str, topic: str) -> List[Dict[str, str]]:
    """Extract key facts from web content for learning."""
    facts = []
    
    # Split into sentences
    sentences = re.split(r'[.!?]+', web_content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    topic_lower = topic.lower()
    
    for sent in sentences[:10]:  # Limit to first 10 relevant sentences
        sent_lower = sent.lower()
        
        # Only keep sentences that mention the topic
        if topic_lower in sent_lower or any(w in sent_lower for w in topic_lower.split()):
            # Clean up
            sent = re.sub(r'\s+', ' ', sent).strip()
            if len(sent) > 20 and len(sent) < 300:
                facts.append({
                    "fact": sent,
                    "topic": topic,
                    "source": "web_research",
                })
    
    return facts[:5]  # Max 5 facts per research


def learn_from_research(facts: List[Dict[str, str]], vocab: Dict, crg, miner) -> Dict[str, Any]:
    """Learn from researched facts — add to vocab and CRG."""
    stats = {"words": 0, "definitions": 0, "edges": 0}
    
    for fact_data in facts:
        fact = fact_data["fact"]
        topic = fact_data["topic"]
        
        # Set as definition for the topic
        topic_key = topic.lower().strip()
        if topic_key in vocab:
            if not getattr(vocab[topic_key], 'definition', None):
                vocab[topic_key].definition = fact
                stats["definitions"] += 1
        
        # Extract relationships
        # Pattern: "X is Y"
        m = re.match(r'(\w+(?:\s+\w+)?)\s+is\s+(?:a|an|the)\s+(.+)', fact)
        if m:
            src = m.group(1).strip().lower()
            dst = m.group(2).strip().lower()
            if src not in vocab:
                miner._create_word(src)
                stats["words"] += 1
            if dst not in vocab:
                miner._create_word(dst)
                stats["words"] += 1
            crg.add_edge(src, "is_a", dst)
            stats["edges"] += 1
    
    return stats


# ═══════════════════════════════════════════════════════════════════════════
# §4  SMART LEARNING FROM CONVERSATION
# ═══════════════════════════════════════════════════════════════════════════

def extract_learning_from_message(message: str) -> List[Dict[str, str]]:
    """
    Extract learnable facts from a user message.
    E.g., "My name is Alice" → {type: "personal", key: "name", value: "alice"}
    E.g., "Gravity is the force of attraction" → {type: "definition", key: "gravity", value: "..."}
    """
    learnings = []
    m = message.lower().strip()
    
    # Personal facts: "my name is X", "I am X", "I'm X"
    patterns = [
        (r"my\s+name\s+is\s+(\w+)", "personal", "user_name"),
        (r"i\s+(?:am|'m)\s+(?:called|named)\s+(\w+)", "personal", "user_name"),
        (r"i\s+(?:am|'m)\s+a\s+(\w+)", "personal", "user_role"),
        (r"i\s+(?:am|'m)\s+(\d+)\s+(?:years?\s+old|year)", "personal", "user_age"),
        (r"i\s+live\s+in\s+(\w+(?:\s+\w+)?)", "personal", "user_location"),
        (r"i\s+work\s+(?:at|for|on)\s+(\w+(?:\s+\w+)?)", "personal", "user_work"),
    ]
    
    for pattern, ltype, key in patterns:
        match = re.search(pattern, m)
        if match:
            learnings.append({
                "type": ltype,
                "key": key,
                "value": match.group(1).strip(),
            })
    
    # Definitions: "X is Y", "X means Y"
    def_patterns = [
        r"^(\w+(?:\s+\w+)?)\s+is\s+(.{10,})",
        r"^(\w+(?:\s+\w+)?)\s+means?\s+(.{5,})",
        r"^(\w+(?:\s+\w+)?)\s+refers?\s+to\s+(.{10,})",
    ]
    
    for pattern in def_patterns:
        match = re.match(pattern, m)
        if match:
            word = match.group(1).strip()
            definition = match.group(2).strip()
            # Only if it looks like a real definition (not a question)
            if not any(q in word for q in ["what", "how", "why", "when", "where"]):
                learnings.append({
                    "type": "definition",
                    "key": word,
                    "value": definition,
                })
    
    return learnings


def apply_learnings(learnings: List[Dict[str, str]], vocab: Dict, crg, miner, 
                    personal_store: Dict) -> Dict[str, Any]:
    """Apply extracted learnings to the GLM."""
    stats = {"personal": 0, "definitions": 0, "words": 0}
    
    for learning in learnings:
        ltype = learning["type"]
        key = learning["key"]
        value = learning["value"]
        
        if ltype == "personal":
            personal_store[key] = value
            stats["personal"] += 1
        
        elif ltype == "definition":
            if key not in vocab:
                miner._create_word(key)
                stats["words"] += 1
            if key in vocab:
                vocab[key].definition = value
                stats["definitions"] += 1
    
    return stats


# ═══════════════════════════════════════════════════════════════════════════
# §5  MASTER AGENT — combines all agent capabilities
# ═══════════════════════════════════════════════════════════════════════════

class ResearchAgent:
    """Master agent that gives the GLM research and task capabilities."""
    
    def __init__(self, crg, vocab_dict, kb=None):
        self.crg = crg
        self.vocab = vocab_dict
        self.kb = kb or {}
        self.personal_store = {}  # Personal facts about the user
        self.research_history = []  # What we've researched
        self.learning_log = []  # What we've learned
    
    def process_message(self, message: str, response: str) -> Dict[str, Any]:
        """
        Process a user message and response to:
        1. Detect knowledge gaps and suggest research
        2. Detect tasks and decompose them
        3. Extract personal facts and definitions
        4. Recall personal facts when asked
        """
        result = {
            "gap": None,
            "task": None,
            "learnings": [],
            "personal_update": None,
            "personal_recall": None,
        }
        
        # 0. Check if the query is asking about personal facts
        m = message.lower()
        if 'my name' in m or 'what was it' in m or 'who am i' in m:
            if 'user_name' in self.personal_store:
                result['personal_recall'] = {
                    'key': 'user_name',
                    'value': self.personal_store['user_name'],
                }
        elif 'what do i do' in m or 'my job' in m or 'my role' in m:
            if 'user_role' in self.personal_store:
                result['personal_recall'] = {
                    'key': 'user_role',
                    'value': self.personal_store['user_role'],
                }
        elif 'where do i live' in m or 'my location' in m:
            if 'user_location' in self.personal_store:
                result['personal_recall'] = {
                    'key': 'user_location',
                    'value': self.personal_store['user_location'],
                }
        
        # 1. Knowledge gap detection
        gap = detect_knowledge_gap(message, response, self.vocab, self.crg)
        if gap:
            result["gap"] = gap
        
        # 2. Task detection
        task = detect_task(message)
        if task:
            result["task"] = task
        
        # 3. Learning extraction
        learnings = extract_learning_from_message(message)
        if learnings:
            from GLM import TextMiner
            miner = TextMiner(self.vocab, self.crg)
            stats = apply_learnings(learnings, self.vocab, self.crg, miner, self.personal_store)
            result["learnings"] = learnings
            result["learning_stats"] = stats
            
            # Check for personal updates
            for l in learnings:
                if l["type"] == "personal":
                    result["personal_update"] = l
        
        return result
    
    def get_personal_context(self) -> str:
        """Get personal context for response generation."""
        if not self.personal_store:
            return ""
        
        parts = []
        if "user_name" in self.personal_store:
            parts.append(f"The user's name is {self.personal_store['user_name']}.")
        if "user_role" in self.personal_store:
            parts.append(f"They are a {self.personal_store['user_role']}.")
        if "user_location" in self.personal_store:
            parts.append(f"They live in {self.personal_store['user_location']}.")
        if "user_work" in self.personal_store:
            parts.append(f"They work on {self.personal_store['user_work']}.")
        
        return " ".join(parts)
    
    def format_agent_output(self, result: Dict[str, Any]) -> str:
        """Format all agent outputs for display."""
        parts = []
        
        # Personal recall (most important — answer the user's question)
        if result.get('personal_recall'):
            key = result['personal_recall']['key'].replace('user_', '')
            value = result['personal_recall']['value']
            parts.append(f"[Remembered] Your {key} is {value}.")
        
        # Task plan
        if result.get("task"):
            parts.append(format_task_plan(result["task"]))
        
        # Research suggestions
        if result.get("gap"):
            parts.append(format_research_suggestions(result["gap"]))
        
        # Learning confirmations
        if result.get("learnings"):
            for l in result["learnings"]:
                if l["type"] == "personal":
                    parts.append(f"[Learned] I'll remember: your {l['key'].replace('user_', '')} is {l['value']}.")
                elif l["type"] == "definition":
                    parts.append(f"[Learned] Got it — {l['key']}: {l['value'][:80]}.")
        
        return "\n".join(parts)


if __name__ == "__main__":
    print("=== GLM37 Research Agent ===")
    
    # Test knowledge gap detection
    print("\n--- Gap Detection ---")
    gap = detect_knowledge_gap(
        "What is quantum entanglement?",
        "I am listening. Name a concept to begin.",
        {},  # empty vocab
        type('obj', (object,), {'out': {}, 'into': {}})()  # empty crg
    )
    if gap:
        print(f"Gap detected: {gap['topic']}")
        print(f"Suggestions: {gap['suggestions']}")
    
    # Test task detection
    print("\n--- Task Detection ---")
    tasks = [
        "Help me create a study plan for quantum mechanics",
        "Can you analyze the relationship between gravity and time?",
        "Compare bosons and fermions",
        "Summarize the UBP framework",
    ]
    for t in tasks:
        task = detect_task(t)
        if task:
            print(f"Task: {task['type']} — {task['subject']}")
            print(f"Steps: {task['steps'][:2]}...")
    
    # Test learning extraction
    print("\n--- Learning Extraction ---")
    messages = [
        "My name is Alice",
        "I am a physicist",
        "I live in Auckland",
        "Gravity is the force that attracts objects with mass",
    ]
    for m in messages:
        learnings = extract_learning_from_message(m)
        if learnings:
            print(f"Message: {m}")
            print(f"Learned: {learnings}")

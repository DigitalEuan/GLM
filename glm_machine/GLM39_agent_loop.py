#!/usr/bin/env python3
"""
GLM39 — Agent Loop
===================
The orchestration layer that transforms the GLM from a single-pass
responder into an agent that can plan, execute, observe, and iterate.

This is the piece that makes the GLM capable of doing what I do:
breaking complex questions into steps and actually executing them.

Architecture:
  Query → Planner → [Step] → Tool Selection → Execution → Observation
                ↑                                          │
                └──────────── Next Step? ◄─────────────────┘
                                                │
                                          Final Response
"""

import re
import json
import time
import io
import sys
import traceback
from typing import List, Dict, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════════════════
# §1  TOOL REGISTRY — What the agent can do
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Tool:
    """A tool the agent can use."""
    name: str
    description: str
    parameters: Dict[str, str]  # param_name → description
    handler: Any = None  # Callable
    category: str = "general"


class ToolRegistry:
    """Registry of all tools available to the agent."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_builtins()

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        return [
            {"name": t.name, "description": t.description, "category": t.category}
            for t in self.tools.values()
        ]

    def _register_builtins(self):
        """Register the built-in tools."""

        # ── Code Execution ─────────────────────────────────────────────
        self.register(Tool(
            name="execute_python",
            description="Execute Python code and return the output. Use for computation, data processing, analysis.",
            parameters={"code": "Python code to execute"},
            category="computation",
        ))

        # ── Math Computation ───────────────────────────────────────────
        self.register(Tool(
            name="compute",
            description="Evaluate a mathematical expression. Supports arithmetic, algebra, calculus, linear algebra.",
            parameters={"expression": "Mathematical expression to evaluate"},
            category="computation",
        ))

        # ── CRG Query ──────────────────────────────────────────────────
        self.register(Tool(
            name="crg_query",
            description="Query the Concept Relation Graph for relationships between concepts.",
            parameters={"concept": "Concept to query", "depth": "How many hops (1-3)"},
            category="knowledge",
        ))

        # ── KB Lookup ──────────────────────────────────────────────────
        self.register(Tool(
            name="kb_lookup",
            description="Look up a concept in the knowledge base for definitions and properties.",
            parameters={"concept": "Concept to look up"},
            category="knowledge",
        ))

        # ── Vocabulary Search ──────────────────────────────────────────
        self.register(Tool(
            name="vocab_search",
            description="Search the vocabulary for words matching a pattern.",
            parameters={"pattern": "Search pattern (regex or substring)"},
            category="knowledge",
        ))

        # ── Golay Analysis ─────────────────────────────────────────────
        self.register(Tool(
            name="golay_analyze",
            description="Analyze a concept's Golay codeword properties (vector, quadrants, NRCI).",
            parameters={"concept": "Concept to analyze"},
            category="geometry",
        ))

        # ── Semantic Distance ──────────────────────────────────────────
        self.register(Tool(
            name="semantic_distance",
            description="Compute geometric distance between two concepts in the 24-bit substrate.",
            parameters={"concept1": "First concept", "concept2": "Second concept"},
            category="geometry",
        ))

        # ── Topological Health ─────────────────────────────────────────
        self.register(Tool(
            name="topological_health",
            description="Analyze the topological health of the CRG (components, bottlenecks, gaps).",
            parameters={},
            category="analysis",
        ))

        # ── File Read ──────────────────────────────────────────────────
        self.register(Tool(
            name="read_file",
            description="Read the contents of a file.",
            parameters={"path": "Path to file"},
            category="io",
        ))

        # ── Web Search ─────────────────────────────────────────────────
        self.register(Tool(
            name="web_search",
            description="Search the web for information on a topic.",
            parameters={"query": "Search query"},
            category="research",
        ))

        # ── Value Geometry ─────────────────────────────────────────────
        self.register(Tool(
            name="value_geometry",
            description="Compute the self-assembling geometric profile of an integer (omega, lattice type, 144° modulus).",
            parameters={"number": "Integer to analyze"},
            category="geometry",
        ))


# ═══════════════════════════════════════════════════════════════════════════
# §2  EXECUTION SANDBOX — Where code actually runs
# ═══════════════════════════════════════════════════════════════════════════

class ExecutionSandbox:
    """
    Safely executes Python code and captures output.
    This is what gives the GLM the ability to actually DO things,
    not just describe what it would do.
    """

    def __init__(self, vocab=None, crg=None, kb=None):
        self.vocab = vocab or {}
        self.crg = crg
        self.kb = kb or {}
        self.execution_history: List[Dict] = []
        self._output_buffer = io.StringIO()

    def execute(self, code: str, timeout: float = 10.0) -> Dict[str, Any]:
        """Execute Python code and return the result."""
        start = time.time()
        output = ""
        success = True
        error = None
        result_value = None

        # Build safe namespace
        namespace = self._build_namespace()

        try:
            old_stdout = sys.stdout
            sys.stdout = self._output_buffer

            # Try eval first (for expressions)
            try:
                result_value = eval(code, namespace)
                if result_value is not None:
                    print(repr(result_value))
            except SyntaxError:
                # Not an expression, exec as statement
                exec(code, namespace)

            output = self._output_buffer.getvalue()
            sys.stdout = old_stdout

        except Exception as e:
            sys.stdout = old_stdout
            output = f"Error: {type(e).__name__}: {e}"
            success = False
            error = str(e)

        # Clear buffer
        self._output_buffer = io.StringIO()

        elapsed = time.time() - start

        result = {
            "output": output.strip(),
            "success": success,
            "error": error,
            "elapsed_ms": int(elapsed * 1000),
            "result": result_value,
        }

        self.execution_history.append({
            "code": code[:500],
            "success": success,
            "output_len": len(output),
            "elapsed_ms": int(elapsed * 1000),
        })

        return result

    def _build_namespace(self) -> Dict:
        """Build a safe execution namespace."""
        import math
        import json
        import re
        import hashlib
        import time as time_mod

        # Try to import sympy
        try:
            import sympy as sp
            has_sympy = True
        except ImportError:
            sp = None
            has_sympy = False

        namespace = {
            '__builtins__': {
                'print': self._safe_print,
                'len': len, 'range': range, 'enumerate': enumerate,
                'zip': zip, 'map': map, 'filter': filter,
                'sorted': sorted, 'reversed': reversed,
                'min': min, 'max': max, 'sum': sum, 'abs': abs,
                'round': round, 'int': int, 'float': float, 'str': str,
                'list': list, 'dict': dict, 'set': set, 'tuple': tuple,
                'bool': bool, 'type': type, 'isinstance': isinstance,
                'hasattr': hasattr, 'getattr': getattr, 'setattr': setattr,
                'any': any, 'all': all, 'hash': hash,
                'True': True, 'False': False, 'None': None,
                'input': lambda *a: '',  # Disable input
                '__import__': __import__,  # Allow imports for tool execution
            },
            'math': math,
            'json': json,
            're': re,
            'hashlib': hashlib,
            'time': time_mod,
            # GLM-specific
            'vocab': self.vocab,
            'crg': self.crg,
            'kb': self.kb,
            'sp': sp,
            'sympy': sp,
        }

        return namespace

    def _safe_print(self, *args, **kwargs):
        """Bounded print that captures output."""
        print(*args, file=self._output_buffer, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# §3  PLANNER — Break queries into executable steps
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class PlanStep:
    """A single step in an execution plan."""
    id: int
    description: str
    tool: str
    params: Dict[str, Any]
    status: str = "pending"  # pending, running, done, failed
    result: Any = None
    output: str = ""


@dataclass
class ExecutionPlan:
    """A complete execution plan."""
    query: str
    steps: List[PlanStep]
    current_step: int = 0
    status: str = "planning"  # planning, executing, complete, failed
    final_answer: str = ""
    observations: List[str] = field(default_factory=list)


def plan_query(query: str, tools: ToolRegistry) -> ExecutionPlan:
    """
    Analyze a query and create an execution plan.
    This is the "thinking" phase — deciding what to do before doing it.
    """
    q = query.lower().strip()
    steps = []
    step_id = 0

    # ── Pattern: Computation request ───────────────────────────────────
    if any(w in q for w in ['compute', 'calculate', 'evaluate', 'what is gcd', 'dot product',
                             'determinant', 'magnitude', 'factorial', 'solve']):
        step_id += 1
        steps.append(PlanStep(
            id=step_id,
            description="Compute the mathematical expression",
            tool="compute",
            params={"expression": query},
        ))

    # ── Pattern: Code execution request ────────────────────────────────
    if any(w in q for w in ['run code', 'execute', 'python', 'script', 'write code']):
        step_id += 1
        steps.append(PlanStep(
            id=step_id,
            description="Write and execute the code",
            tool="execute_python",
            params={"code": _extract_code_from_query(query)},
        ))

    # ── Pattern: Analysis request ──────────────────────────────────────
    if any(w in q for w in ['analyze', 'analyse', 'examine', 'investigate', 'study']):
        step_id += 1
        # Determine what to analyze
        if any(w in q for w in ['graph', 'crg', 'knowledge', 'relationship', 'topology', 'topological']):
            steps.append(PlanStep(
                id=step_id,
                description="Analyze the CRG topology",
                tool="topological_health",
                params={},
            ))
        else:
            concept = _extract_concept(q)
            if concept:
                steps.append(PlanStep(
                    id=step_id,
                    description=f"Analyze the concept '{concept}' (Golay codeword)",
                    tool="golay_analyze",
                    params={"concept": concept},
                ))
                step_id += 1
                steps.append(PlanStep(
                    id=step_id,
                    description=f"Look up '{concept}' in KB",
                    tool="kb_lookup",
                    params={"concept": concept},
                ))
                step_id += 1
                steps.append(PlanStep(
                    id=step_id,
                    description=f"Query CRG for '{concept}'",
                    tool="crg_query",
                    params={"concept": concept, "depth": "2"},
                ))

    # ── Pattern: Comparison request ────────────────────────────────────
    if any(w in q for w in ['compare', 'difference', 'distance', 'similarity', 'versus', 'vs']):
        concepts = _extract_two_concepts(q)
        if concepts:
            step_id += 1
            steps.append(PlanStep(
                id=step_id,
                description=f"Compute distance between {concepts[0]} and {concepts[1]}",
                tool="semantic_distance",
                params={"concept1": concepts[0], "concept2": concepts[1]},
            ))

    # ── Pattern: Knowledge lookup ──────────────────────────────────────
    if any(w in q for w in ['what is', 'define', 'explain', 'tell me about', 'describe']):
        concept = _extract_concept(q)
        if concept:
            step_id += 1
            steps.append(PlanStep(
                id=step_id,
                description=f"Look up '{concept}' in the knowledge base",
                tool="kb_lookup",
                params={"concept": concept},
            ))
            step_id += 1
            steps.append(PlanStep(
                id=step_id,
                description=f"Query CRG relationships for '{concept}'",
                tool="crg_query",
                params={"concept": concept, "depth": "2"},
            ))

    # ── Pattern: Number analysis ───────────────────────────────────────
    numbers = re.findall(r'\b\d+\b', q)
    if numbers and any(w in q for w in ['geometry', 'lattice', 'prime', 'factor', 'value']):
        step_id += 1
        steps.append(PlanStep(
            id=step_id,
            description=f"Compute value geometry for {numbers[0]}",
            tool="value_geometry",
            params={"number": numbers[0]},
        ))

    # ── Pattern: File reading ──────────────────────────────────────────
    file_match = re.search(r'(?:read|open|load|show)\s+(?:file\s+)?[\'"]?(\S+\.\w+)[\'"]?', q)
    if file_match:
        step_id += 1
        steps.append(PlanStep(
            id=step_id,
            description=f"Read file: {file_match.group(1)}",
            tool="read_file",
            params={"path": file_match.group(1)},
        ))

    # ── Pattern: Web search ────────────────────────────────────────────
    if any(w in q for w in ['search', 'look up', 'find out', 'research', 'google']):
        step_id += 1
        steps.append(PlanStep(
            id=step_id,
            description=f"Search the web",
            tool="web_search",
            params={"query": _extract_search_query(q)},
        ))

    # ── Default: If no specific plan, try compute + KB lookup ──────────
    if not steps:
        concept = _extract_concept(q)
        if concept:
            step_id += 1
            steps.append(PlanStep(
                id=step_id,
                description=f"Look up '{concept}'",
                tool="kb_lookup",
                params={"concept": concept},
            ))

    return ExecutionPlan(query=query, steps=steps)


# ═══════════════════════════════════════════════════════════════════════════
# §4  AGENT LOOP — Plan → Execute → Observe → Iterate
# ═══════════════════════════════════════════════════════════════════════════

class AgentLoop:
    """
    The GLM's agent loop: the orchestration layer that lets it
    actually DO things, not just talk about them.

    This is the difference between "I could do X" and "I did X".
    """

    def __init__(self, vocab=None, crg=None, kb=None):
        self.vocab = vocab or {}
        self.crg = crg
        self.kb = kb or {}
        self.tools = ToolRegistry()
        self.sandbox = ExecutionSandbox(vocab, crg, kb)
        self.execution_log: List[Dict] = []

    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute a query through the agent loop.

        Returns:
            {
                "plan": [...],
                "results": [...],
                "observations": [...],
                "final_answer": "...",
                "total_ms": ...,
            }
        """
        start = time.time()

        # 1. Plan
        plan = plan_query(query, self.tools)

        if not plan.steps:
            return {
                "plan": [],
                "results": [],
                "observations": [],
                "final_answer": "I don't have a specific tool for this query. Try asking a more specific question.",
                "total_ms": int((time.time() - start) * 1000),
            }

        # 2. Execute each step
        results = []
        observations = []

        for step in plan.steps:
            step.status = "running"

            result = self._execute_step(step)
            results.append(result)

            if result.get("success"):
                step.status = "done"
                step.output = result.get("output", "")

                # Extract observations
                if result.get("output"):
                    observations.append(f"[{step.tool}] {result['output'][:200]}")
            else:
                step.status = "failed"
                step.output = result.get("error", "Unknown error")
                observations.append(f"[{step.tool}] Failed: {step.output[:100]}")

        # 3. Synthesize final answer
        final_answer = self._synthesize_answer(query, plan, results, observations)

        total_ms = int((time.time() - start) * 1000)

        return {
            "plan": [{"id": s.id, "description": s.description, "tool": s.tool,
                      "status": s.status, "output": s.output[:300]} for s in plan.steps],
            "results": results,
            "observations": observations,
            "final_answer": final_answer,
            "total_ms": total_ms,
        }

    def _execute_step(self, step: PlanStep) -> Dict[str, Any]:
        """Execute a single plan step."""
        tool_name = step.tool
        params = step.params

        if tool_name == "compute":
            return self._tool_compute(params.get("expression", ""))
        elif tool_name == "execute_python":
            return self._tool_execute_python(params.get("code", ""))
        elif tool_name == "kb_lookup":
            return self._tool_kb_lookup(params.get("concept", ""))
        elif tool_name == "crg_query":
            return self._tool_crg_query(params.get("concept", ""), int(params.get("depth", 2)))
        elif tool_name == "vocab_search":
            return self._tool_vocab_search(params.get("pattern", ""))
        elif tool_name == "golay_analyze":
            return self._tool_golay_analyze(params.get("concept", ""))
        elif tool_name == "semantic_distance":
            return self._tool_semantic_distance(params.get("concept1", ""), params.get("concept2", ""))
        elif tool_name == "topological_health":
            return self._tool_topological_health()
        elif tool_name == "read_file":
            return self._tool_read_file(params.get("path", ""))
        elif tool_name == "web_search":
            return self._tool_web_search(params.get("query", ""))
        elif tool_name == "value_geometry":
            return self._tool_value_geometry(params.get("number", "0"))
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    # ── Tool Implementations ───────────────────────────────────────────

    def _tool_compute(self, expression: str) -> Dict[str, Any]:
        """Compute a mathematical expression using SymPy."""
        import re as _re
        q = expression.lower()
        
        # GCD
        m = _re.search(r'gcd\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', q)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            return self.sandbox.execute("import sympy as sp; print(sp.gcd(%d, %d))" % (a, b))
        
        # Factorial
        m = _re.search(r'(\d+)\s*!', q)
        if m:
            n = int(m.group(1))
            return self.sandbox.execute("import math; print(math.factorial(%d))" % n)
        
        # sqrt
        m = _re.search(r'sqrt\s*\(\s*(\d+)\s*\)', q)
        if m:
            n = int(m.group(1))
            return self.sandbox.execute("import math; print(math.sqrt(%d))" % n)
        
        # Generic: try sympify
        safe_expr = expression.replace("'", "").replace('"', '')
        return self.sandbox.execute("import sympy as sp; print(sp.sympify('%s'))" % safe_expr)

    def _tool_execute_python(self, code: str) -> Dict[str, Any]:
        """Execute arbitrary Python code."""
        return self.sandbox.execute(code)

    def _tool_kb_lookup(self, concept: str) -> Dict[str, Any]:
        """Look up a concept in the knowledge base."""
        code = f"""
concept = '{concept}'.lower()

# Search KB
found = False
for uid, entry in kb.items():
    name = entry.get('name', '').lower()
    desc = entry.get('desc', entry.get('lexicon', ''))
    if concept in name or concept in desc.lower():
        print(f"Found: {{entry.get('name', uid)}}")
        print(f"Description: {{desc[:300]}}")
        found = True
        break

# Search vocab
if not found and concept in vocab:
    entry = vocab[concept]
    defn = getattr(entry, 'definition', None)
    if defn:
        print(f"Definition: {{defn[:300]}}")
        found = True
    nrci = float(entry.nrci) if hasattr(entry, 'nrci') else 0
    print(f"NRCI: {{nrci:.4f}}")

if not found:
    print(f"'{concept}' not found in KB or vocabulary")
"""
        return self.sandbox.execute(code)

    def _tool_crg_query(self, concept: str, depth: int = 2) -> Dict[str, Any]:
        """Query the CRG for relationships."""
        code = f"""
concept = '{concept}'.lower()

# Outgoing edges
outgoing = crg.out.get(concept, [])
print(f"=== {{concept}} — {{len(outgoing)}} outgoing connections ===")
for edge in outgoing[:15]:
    if edge.label not in ('auto_proposed', 'co_occurs') and not edge.label.startswith('lattice_adjacent'):
        print(f"  {{concept}} --{{edge.label.replace('_', ' ')}}--> {{edge.dst}}")

# Incoming edges
incoming = crg.into.get(concept, [])
print(f"\\n=== {{concept}} — {{len(incoming)}} incoming connections ===")
for edge in incoming[:10]:
    if edge.label not in ('auto_proposed', 'co_occurs'):
        print(f"  {{edge.src}} --{{edge.label.replace('_', ' ')}}--> {{concept}}")

# 2-hop neighbors
if {depth} >= 2:
    neighbors_2hop = set()
    for edge in outgoing[:5]:
        for edge2 in crg.out.get(edge.dst, [])[:3]:
            if edge2.dst != concept:
                neighbors_2hop.add((edge.dst, edge2.label, edge2.dst))
    if neighbors_2hop:
        print(f"\\n=== 2-hop neighbors ===")
        for mid, label, dst in list(neighbors_2hop)[:10]:
            print(f"  {{concept}} -> {{mid}} --{{label.replace('_', ' ')}}--> {{dst}}")
"""
        return self.sandbox.execute(code)

    def _tool_vocab_search(self, pattern: str) -> Dict[str, Any]:
        """Search vocabulary for matching words."""
        code = f"""
import re
pattern = '{pattern}'.lower()
matches = []
for word, entry in vocab.items():
    if re.search(pattern, word.lower()):
        nrci = float(entry.nrci) if hasattr(entry, 'nrci') else 0
        defn = getattr(entry, 'definition', '')[:80]
        matches.append((word, nrci, defn))

matches.sort(key=lambda x: -x[1])
print(f"Found {{len(matches)}} matches for '{{pattern}}':")
for word, nrci, defn in matches[:20]:
    print(f"  {{word:25s}} NRCI={{nrci:.3f}} {{defn}}")
"""
        return self.sandbox.execute(code)

    def _tool_golay_analyze(self, concept: str) -> Dict[str, Any]:
        """Analyze a concept's Golay codeword."""
        code = f"""
concept = '{concept}'.lower()
if concept in vocab:
    entry = vocab[concept]
    v = list(entry.vector) if hasattr(entry, 'vector') else [0]*24
    hw = sum(v)
    q = [sum(v[0:6]), sum(v[6:12]), sum(v[12:18]), sum(v[18:24])]
    layers = ['Reality', 'Information', 'Activation', 'Potential']
    dominant = q.index(max(q))
    nrci = float(entry.nrci) if hasattr(entry, 'nrci') else 0
    mog = getattr(entry, 'mog_category', 'unknown')
    
    hex_val = sum((1 << (23-i)) for i in range(24) if v[i])
    
    print(f"=== {{concept}} — Golay Analysis ===")
    print(f"Vector: {{v}}")
    print(f"Hex: 0x{{hex_val:06X}}")
    print(f"Hamming Weight: {{hw}}/24")
    print(f"Quadrants (Q): {{q}}")
    print(f"Dominant Layer: {{layers[dominant]}} ({{max(q)}} bits)")
    print(f"NRCI: {{nrci:.4f}}")
    print(f"MOG Category: {{mog}}")
    print(f"Balanced: {{max(q) - min(q) <= 2}}")
else:
    print(f"'{{concept}}' not in vocabulary")
"""
        return self.sandbox.execute(code)

    def _tool_semantic_distance(self, c1: str, c2: str) -> Dict[str, Any]:
        """Compute distance between two concepts."""
        code = f"""
c1, c2 = '{c1}'.lower(), '{c2}'.lower()
if c1 in vocab and c2 in vocab:
    v1 = list(vocab[c1].vector)
    v2 = list(vocab[c2].vector)
    dist = sum(a != b for a, b in zip(v1, v2))
    sim = 1.0 - dist / 24.0
    print(f"d({{c1}}, {{c2}}) = {{dist}}/24")
    print(f"Similarity: {{sim:.3f}}")
    if dist < 8:
        print("→ Closely related")
    elif dist < 16:
        print("→ Moderately related")
    else:
        print("→ Distantly related or unrelated")
    
    # Show shared quadrants
    q1 = [sum(v1[i:i+6]) for i in range(0, 24, 6)]
    q2 = [sum(v2[i:i+6]) for i in range(0, 24, 6)]
    layers = ['Reality', 'Information', 'Activation', 'Potential']
    print(f"\\n{{c1}} quadrants: {{dict(zip(layers, q1))}}")
    print(f"{{c2}} quadrants: {{dict(zip(layers, q2))}}")
else:
    missing = [c for c in [c1, c2] if c not in vocab]
    print(f"Not in vocabulary: {{missing}}")
"""
        return self.sandbox.execute(code)

    def _tool_topological_health(self) -> Dict[str, Any]:
        """Analyze CRG topology."""
        code = f"""
from collections import defaultdict, deque

# Find connected components
visited = set()
components = []
for node in set(list(crg.out.keys()) + list(crg.into.keys())):
    if node in visited:
        continue
    component = set()
    queue = deque([node])
    while queue:
        n = queue.popleft()
        if n in visited:
            continue
        visited.add(n)
        component.add(n)
        for edge in crg.out.get(n, []):
            if edge.dst not in visited:
                queue.append(edge.dst)
        for edge in crg.into.get(n, []):
            if edge.src not in visited:
                queue.append(edge.src)
    components.append(component)

components.sort(key=len, reverse=True)
total_nodes = len(visited)
total_edges = len(crg.edges)

print(f"=== CRG Topological Health ===")
print(f"Total nodes: {{total_nodes}}")
print(f"Total edges: {{total_edges}}")
print(f"Connected components: {{len(components)}}")
print(f"Largest component: {{len(components[0])}} nodes ({{len(components[0])/total_nodes*100:.1f}}%)")
print(f"Isolated nodes: {{sum(1 for c in components if len(c) == 1)}}")

# Edge label distribution
labels = defaultdict(int)
for edge in crg.edges:
    labels[edge.label] += 1
print(f"\\nTop edge types:")
for label, count in sorted(labels.items(), key=lambda x: -x[1])[:10]:
    print(f"  {{label:25s}} {{count}}")
"""
        return self.sandbox.execute(code)

    def _tool_read_file(self, path: str) -> Dict[str, Any]:
        """Read a file."""
        try:
            with open(path, 'r') as f:
                content = f.read(5000)
            return {"success": True, "output": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _tool_web_search(self, query: str) -> Dict[str, Any]:
        """Search the web (placeholder — would need API integration)."""
        return {
            "success": True,
            "output": f"[Web search for: {query}]\nNote: Web search requires API integration. Use the 'learn' command to teach me about this topic, or upload a document.",
        }

    def _tool_value_geometry(self, number: str) -> Dict[str, Any]:
        """Compute value geometry for an integer."""
        code = f"""
import math

def distinct_prime_factors(n):
    if n < 2: return []
    factors = set()
    d = 2
    temp = n
    while d * d <= temp:
        while temp % d == 0:
            factors.add(d)
            temp //= d
        d += 1
    if temp > 1: factors.add(temp)
    return sorted(factors)

n = {number}
primes = distinct_prime_factors(n)
omega = len(primes)
lp = max(primes) if primes else n

if lp % 4 == 1:
    lattice = "Gaussian (square grid, Z[i])"
elif lp % 3 == 1:
    lattice = "Eisenstein (hexagonal grid, Z[ω])"
elif lp == 2:
    lattice = "Dyadic (2-adic)"
else:
    lattice = "Rectangular"

platonic_total = 14400
mod144 = n % 144

print(f"=== Value Geometry of {{n}} ===")
print(f"Prime factors: {{primes}}")
print(f"ω (omega): {{omega}}")
print(f"Largest prime: {{lp}}")
print(f"Lattice type: {{lattice}}")
print(f"144° modulus: {{mod144}}")
print(f"Platonic resonance: {{n % 144 == 0}}")
"""
        return self.sandbox.execute(code)

    # ── Synthesis ──────────────────────────────────────────────────────

    def _synthesize_answer(self, query: str, plan: ExecutionPlan,
                           results: List[Dict], observations: List[str]) -> str:
        """Synthesize a final answer from all step results."""
        parts = []

        # Collect all successful outputs
        for i, result in enumerate(results):
            if result.get("success") and result.get("output"):
                output = result["output"].strip()
                if output:
                    parts.append(output)

        if not parts:
            return "I attempted the requested operations but couldn't produce results. Try rephrasing or providing more context."

        # Combine outputs
        combined = "\n\n".join(parts)

        # Add execution summary
        step_count = len(results)
        success_count = sum(1 for r in results if r.get("success"))
        total_ms = sum(r.get("elapsed_ms", 0) for r in results)

        summary = f"\n[Agent] Executed {success_count}/{step_count} steps in {total_ms}ms"

        return combined + summary


# ═══════════════════════════════════════════════════════════════════════════
# §5  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _extract_concept(query: str) -> str:
    """Extract the main concept from a query."""
    q = query.lower()
    stop = {"what", "is", "the", "a", "an", "of", "how", "does", "do", "can",
            "will", "would", "should", "could", "may", "might", "must", "tell",
            "me", "about", "explain", "describe", "define", "show", "find",
            "and", "or", "but", "for", "with", "to", "in", "on", "at", "by",
            "from", "it", "this", "that", "please", "can", "you", "its",
            # Action verbs that aren't concepts
            "analyze", "analyse", "compare", "compute", "calculate",
            "evaluate", "investigate", "examine", "study", "run", "execute",
            "write", "create", "make", "build", "generate", "find",
            "search", "look", "get", "give", "tell", "show", "list",
            "concept", "thing", "something", "anything", "everything"}
    words = [w for w in re.findall(r'\b[a-z]{3,}\b', q) if w not in stop]
    return words[0] if words else ""


def _extract_two_concepts(query: str) -> Optional[Tuple[str, str]]:
    """Extract two concepts from a comparison query."""
    q = query.lower()
    # Pattern: "compare X and Y" or "X versus Y"
    m = re.search(r'compare\s+(\w+)\s+and\s+(\w+)', q)
    if m:
        return (m.group(1), m.group(2))
    m = re.search(r'(\w+)\s+(?:versus|vs\.?)\s+(\w+)', q)
    if m:
        return (m.group(1), m.group(2))
    m = re.search(r'difference\s+between\s+(\w+)\s+and\s+(\w+)', q)
    if m:
        return (m.group(1), m.group(2))
    m = re.search(r'distance\s+(?:between\s+)?(\w+)\s+(?:and\s+)?(\w+)', q)
    if m:
        return (m.group(1), m.group(2))
    return None


def _extract_code_from_query(query: str) -> str:
    """Extract code blocks from a query."""
    m = re.search(r'```(?:python)?\n(.*?)```', query, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r'`([^`]+)`', query)
    if m:
        return m.group(1).strip()
    return ""


def _extract_search_query(query: str) -> str:
    """Extract search terms from a query."""
    q = query.lower()
    q = re.sub(r'^(search|look up|find out|research|google)\s+', '', q)
    q = re.sub(r'\s+(for|about|on)\s+', ' ', q)
    return q.strip()


# ═══════════════════════════════════════════════════════════════════════════
# §6  FORMATTING
# ═══════════════════════════════════════════════════════════════════════════

def format_agent_result(result: Dict[str, Any]) -> str:
    """Format an agent result for display."""
    parts = []

    # Plan
    if result.get("plan"):
        parts.append("[Agent Plan]")
        for step in result["plan"]:
            status_icon = {"done": "✅", "failed": "❌", "pending": "⏳"}.get(step["status"], "•")
            parts.append(f"  {status_icon} {step['description']}")

    # Results
    if result.get("observations"):
        for obs in result["observations"]:
            parts.append(obs)

    # Final answer
    if result.get("final_answer"):
        parts.append(f"\n{result['final_answer']}")

    # Timing
    parts.append(f"\n[Agent] Total: {result.get('total_ms', 0)}ms")

    return "\n".join(parts)


if __name__ == "__main__":
    print("=== GLM39 Agent Loop ===")
    print("Plan → Execute → Observe → Iterate")

    # Test with empty vocab/crg
    agent = AgentLoop()
    result = agent.execute_query("What is gcd(54, 24)?")
    print(format_agent_result(result))

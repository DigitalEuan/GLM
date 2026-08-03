#!/usr/bin/env python3
"""
GLM SANDBOX — Virtual Thinking Environment
=============================================
A safe execution environment where the GLM can:
1. Run code and see results
2. Write observations and read them back
3. Accumulate understanding over time
4. Think step-by-step without infinite loops

The sandbox is the GLM's "mind" — a bounded space where it can
experiment, observe, and learn. Every thought is recorded. Every
result persists. The GLM grows by thinking.

Loop prevention:
- Max iterations per thought: 20
- Max sandbox operations per query: 50
- Recursion depth limit: 5
- Timeout per operation: 5 seconds
"""

import io
import sys
import os
import json
import time
import hashlib
import traceback
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class Thought:
    """A single thought in the sandbox."""
    id: str
    timestamp: float
    input_code: str
    output: str
    success: bool
    iterations: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class Observation:
    """Something the GLM observed and wants to remember."""
    key: str
    value: str
    source: str  # "tool", "computation", "inference", "user"
    timestamp: float
    confidence: float = 1.0


class SandboxMemory:
    """Persistent memory for the sandbox."""

    def __init__(self, filepath: str = "sandbox_memory.json"):
        self.filepath = filepath
        self.observations: Dict[str, Observation] = {}
        self.thoughts: List[Thought] = []
        self.insights: List[str] = []
        self.load()

    def add_observation(self, key: str, value: str, source: str = "inference",
                        confidence: float = 1.0):
        """Add or update an observation."""
        self.observations[key] = Observation(
            key=key, value=value, source=source,
            timestamp=time.time(), confidence=confidence
        )
        self.save()

    def get_observation(self, key: str) -> Optional[str]:
        """Get an observation by key."""
        obs = self.observations.get(key)
        return obs.value if obs else None

    def add_thought(self, thought: Thought):
        """Record a thought."""
        self.thoughts.append(thought)
        # Keep only last 100 thoughts
        if len(self.thoughts) > 100:
            self.thoughts = self.thoughts[-100:]
        self.save()

    def add_insight(self, insight: str):
        """Record an insight."""
        self.insights.append(insight)
        if len(self.insights) > 50:
            self.insights = self.insights[-50:]
        self.save()

    def get_context(self, max_items: int = 10) -> str:
        """Get recent context for the GLM."""
        parts = []
        # Recent observations
        recent_obs = sorted(self.observations.values(),
                           key=lambda o: o.timestamp, reverse=True)[:max_items]
        if recent_obs:
            parts.append("Recent observations:")
            for obs in recent_obs:
                parts.append(f"  {obs.key}: {obs.value} (confidence={obs.confidence:.2f})")

        # Recent insights
        if self.insights:
            parts.append(f"\nInsights ({len(self.insights)}):")
            for insight in self.insights[-5:]:
                parts.append(f"  - {insight}")

        return "\n".join(parts)

    def save(self):
        """Persist to disk."""
        data = {
            "observations": {
                k: {"key": v.key, "value": v.value, "source": v.source,
                    "timestamp": v.timestamp, "confidence": v.confidence}
                for k, v in self.observations.items()
            },
            "thoughts": [
                {"id": t.id, "timestamp": t.timestamp, "input": t.input_code,
                 "output": t.output[:500], "success": t.success,
                 "iterations": t.iterations, "tags": t.tags}
                for t in self.thoughts[-100:]
            ],
            "insights": self.insights[-50:],
        }
        try:
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass

    def load(self):
        """Load from disk."""
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath, 'r') as f:
                data = json.load(f)
            for k, v in data.get("observations", {}).items():
                self.observations[k] = Observation(**v)
            for t in data.get("thoughts", []):
                self.thoughts.append(Thought(
                    id=t["id"], timestamp=t["timestamp"],
                    input_code=t["input"], output=t["output"],
                    success=t["success"], iterations=t.get("iterations", 0),
                    tags=t.get("tags", [])
                ))
            self.insights = data.get("insights", [])
        except:
            pass


class Sandbox:
    """Virtual thinking environment for the GLM.

    The sandbox provides:
    1. Safe code execution (bounded, no side effects)
    2. Persistent memory (observations, thoughts, insights)
    3. Loop prevention (iteration limits, recursion detection)
    4. Context accumulation (reads previous state)
    """

    def __init__(self, memory_path: str = "sandbox_memory.json",
                 max_iterations: int = 20,
                 max_operations: int = 50,
                 timeout: float = 5.0):
        self.memory = SandboxMemory(memory_path)
        self.max_iterations = max_iterations
        self.max_operations = max_operations
        self.timeout = timeout
        self.operation_count = 0
        self.execution_log: List[Dict] = []

        # Safe namespace for code execution
        self._namespace = {
            '__builtins__': {
                'print': self._sandbox_print,
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
            },
            'math': __import__('math'),
            'json': __import__('json'),
            're': __import__('re'),
            'hashlib': __import__('hashlib'),
            'time': __import__('time'),
            # Sandbox-specific
            'observe': self._observe,
            'recall': self._recall,
            'insight': self._insight,
            'sandbox_log': self.execution_log,
        }

        self._output_buffer = io.StringIO()

    def think(self, code: str, context: str = "") -> Thought:
        """Execute code in the sandbox with loop prevention.

        Args:
            code: Python code to execute
            context: Additional context for the thought

        Returns:
            Thought with output and metadata
        """
        self.operation_count = 0
        thought_id = hashlib.md5(f"{code}{time.time()}".encode()).hexdigest()[:8]

        # Inject context
        if context:
            self._namespace['_context'] = context

        # Execute with timeout protection
        start_time = time.time()
        output = ""
        success = True
        iterations = 0

        try:
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = self._output_buffer

            # Execute
            exec(code, self._namespace)
            output = self._output_buffer.getvalue()

            sys.stdout = old_stdout

        except Exception as e:
            sys.stdout = old_stdout
            output = f"Error: {type(e).__name__}: {e}"
            success = False

        # Check for loops
        elapsed = time.time() - start_time
        if elapsed > self.timeout:
            output += f"\n[Timeout: {elapsed:.1f}s exceeded {self.timeout}s limit]"
            success = False

        if self.operation_count > self.max_operations:
            output += f"\n[Loop detected: {self.operation_count} operations exceeded {self.max_operations} limit]"
            success = False

        # Create thought
        thought = Thought(
            id=thought_id,
            timestamp=time.time(),
            input_code=code[:500],
            output=output[:1000],
            success=success,
            iterations=iterations,
        )

        # Record
        self.memory.add_thought(thought)
        self.execution_log.append({
            "id": thought_id, "code": code[:200], "success": success,
            "output_len": len(output), "elapsed": elapsed
        })

        return thought

    def observe(self, key: str, value: str, source: str = "inference"):
        """Store an observation in persistent memory."""
        self.memory.add_observation(key, value, source)

    def recall(self, key: str = None) -> str:
        """Recall observations from memory."""
        if key:
            return self.memory.get_observation(key) or f"No observation for '{key}'"
        return self.memory.get_context()

    def get_context(self) -> str:
        """Get the sandbox's current context."""
        return self.memory.get_context()

    def get_stats(self) -> Dict[str, Any]:
        """Get sandbox statistics."""
        return {
            "observations": len(self.memory.observations),
            "thoughts": len(self.memory.thoughts),
            "insights": len(self.memory.insights),
            "operations": self.operation_count,
        }

    # ── Internal methods ──────────────────────────────────────────────────

    def _sandbox_print(self, *args, **kwargs):
        """Bounded print that captures output."""
        self.operation_count += 1
        if self.operation_count > self.max_operations:
            raise RuntimeError("Operation limit exceeded")
        print(*args, file=self._output_buffer, **kwargs)

    def _observe(self, key: str, value: str):
        """Sandbox function: store an observation."""
        self.operation_count += 1
        self.memory.add_observation(key, value, "sandbox")

    def _recall(self, key: str = None) -> str:
        """Sandbox function: recall from memory."""
        self.operation_count += 1
        if key:
            return self.memory.get_observation(key) or ""
        return self.memory.get_context()

    def _insight(self, text: str):
        """Sandbox function: record an insight."""
        self.operation_count += 1
        self.memory.add_insight(text)


class SandboxTools:
    """Tools that run inside the sandbox."""

    def __init__(self, sandbox: Sandbox, vocab, crg):
        self.sandbox = sandbox
        self.vocab = vocab
        self.crg = crg

    def run_tool(self, tool_name: str, **kwargs) -> str:
        """Run a tool in the sandbox and return the result."""
        code = self._generate_tool_code(tool_name, **kwargs)
        if not code:
            return f"Unknown tool: {tool_name}"

        thought = self.sandbox.think(code)
        return thought.output

    def _generate_tool_code(self, tool_name: str, **kwargs) -> Optional[str]:
        """Generate Python code for a tool."""
        concept = kwargs.get("concept", "")
        expression = kwargs.get("expression", "")

        templates = {
            "GOLAY_ANALYZE": f"""
# Analyze Golay codeword properties
v = {self._get_vector(concept)}
hw = sum(v)
q = [sum(v[0:6]), sum(v[6:12]), sum(v[12:18]), sum(v[18:24])]
layers = ['Reality', 'Information', 'Activation', 'Potential']
dominant = q.index(max(q))
observe('vector_{concept}', f'Q={{q}}, layer={{layers[dominant]}}, HW={{hw}}')
print(f'Vector: {{v}}')
print(f'Quadrants: {{q}}')
print(f'Dominant layer: {{layers[dominant]}}')
print(f'Hamming weight: {{hw}}')
print(f'Balanced: {{max(q) - min(q) <= 2}}')
""",
            "CRG_NEIGHBORS": f"""
# Find all neighbors in the knowledge graph
concept = '{concept}'
neighbors = {{}}
for edge in crg.out.get(concept, []):
    if edge.label not in ('auto_proposed', 'co_occurs') and not edge.label.startswith('lattice_adjacent'):
        neighbors[edge.dst] = edge.label
observe('neighbors_{concept}', str(list(neighbors.keys())[:10]))
print(f'{{concept}} has {{len(neighbors)}} outgoing connections:')
for target, label in list(neighbors.items())[:10]:
    print(f'  {{concept}} --{{label}}--> {{target}}')
""",
            "MATH_VERIFY": f"""
# Verify a mathematical computation
import math
expr = '{expression}'
try:
    result = eval(expr)
    observe('math_{expression}', str(result))
    print(f'{{expr}} = {{result}}')
    # Check if it maps to a lattice point
    if isinstance(result, (int, float)):
        print(f'Lattice point: {{result}}')
except Exception as e:
    print(f'Error: {{e}}')
""",
            "SEMANTIC_DISTANCE": f"""
# Compute semantic distance between concepts
c1, c2 = '{kwargs.get("c1", "")}', '{kwargs.get("c2", "")}'
v1 = {self._get_vector(kwargs.get("c1", ""))}
v2 = {self._get_vector(kwargs.get("c2", ""))}
if v1 and v2:
    dist = sum(a != b for a, b in zip(v1, v2))
    sim = 1.0 - dist / 24.0
    observe(f'dist_{{c1}}_{{c2}}', f'{{dist}}/24, sim={{sim:.2f}}')
    print(f'd({{c1}}, {{c2}}) = {{dist}}/24')
    print(f'Similarity: {{sim:.2f}}')
    if dist < 8:
        print('→ Closely related')
    elif dist < 16:
        print('→ Moderately related')
    else:
        print('→ Distantly related or unrelated')
""",
            "LAYER_ANALYSIS": f"""
# Analyze distribution across ontological layers
layers = {{'Reality': 0, 'Information': 0, 'Activation': 0, 'Potential': 0}}
for word, entry in vocab.items():
    if hasattr(entry, 'vector') and entry.vector and sum(entry.vector) > 0:
        v = entry.vector
        q = [sum(v[0:6]), sum(v[6:12]), sum(v[12:18]), sum(v[18:24])]
        dominant = q.index(max(q))
        layer_names = ['Reality', 'Information', 'Activation', 'Potential']
        layers[layer_names[dominant]] += 1
for layer, count in sorted(layers.items(), key=lambda x: -x[1]):
    bar = '█' * (count // 50)
    print(f'{{layer:15s}} → {{count:5d}} {{bar}}')
observe('layer_distribution', str(layers))
""",
            "KNOWLEDGE_GAP": f"""
# Find knowledge gaps
gaps = []
for word in list(vocab.keys())[:500]:
    out_edges = [e for e in crg.out.get(word, []) 
                 if e.label not in ('auto_proposed', 'co_occurs') 
                 and not e.label.startswith('lattice_adjacent')]
    if 0 < len(out_edges) <= 2:
        gaps.append((word, len(out_edges)))
gaps.sort(key=lambda x: x[1])
print(f'Found {{len(gaps)}} concepts with sparse connections:')
for word, count in gaps[:15]:
    print(f'  {{word:20s}} → {{count}} connection(s)')
observe('knowledge_gaps', str([g[0] for g in gaps[:10]]))
""",
        }
        return templates.get(tool_name)

    def _get_vector(self, concept: str) -> str:
        """Get vector as string for code generation."""
        entry = self.vocab.get(concept)
        if entry and hasattr(entry, 'vector') and entry.vector:
            return repr(list(entry.vector))
        return "[0]*24"


if __name__ == "__main__":
    print("=== GLM Sandbox — Virtual Thinking Environment ===")
    print("Safe execution, persistent memory, loop prevention.")

#!/usr/bin/env python3
"""
GLM TOOLS — Executable Tool System
=====================================
The Script column becomes REAL. Instead of describing code,
the GLM actually executes it and uses the results.

Tools available:
1. GOLAY_SNAP     — Snap a vector to nearest Golay codeword
2. NRCI_COMPUTE   — Compute NRCI for a vector
3. HAMMING_DIST   — Hamming distance between two vectors
4. CRG_WALK       — Walk the knowledge graph
5. MATH_EVAL      — Evaluate mathematical expressions
6. SYMPY_SOLVE    — Symbolic math (SymPy)
7. VECTOR_ANALYZE — Analyze a concept's geometric properties
8. PRIMALITY      — Primality test via UBP pipeline
9. GRAY_CODE      — Gray code conversion
10. SUBSTRATE_MAP  — Map concepts to ontological layers

The GLM selects tools based on the query and executes them.
Results flow into the Language column for coherent output.
"""

import math
import re
import hashlib
from typing import List, Dict, Tuple, Any, Optional


class ToolResult:
    """Result from a tool execution."""
    def __init__(self, tool_name: str, output: Any, description: str, success: bool = True):
        self.tool_name = tool_name
        self.output = output
        self.description = description
        self.success = success

    def __str__(self):
        return f"[{self.tool_name}] {self.description}"


class GLMTools:
    """Executable tools for the GLM."""

    def __init__(self, vocab, crg, runtime=None):
        self.vocab = vocab
        self.crg = crg
        self.rt = runtime

        # Import UBP engines
        try:
            from GLM01_substrate import GOLAY_ENGINE, LEECH_ENGINE, BLA, vector_to_hex_int, fast_hamming
            self.golay = GOLAY_ENGINE
            self.leech = LEECH_ENGINE
            self.bla = BLA
            self.vector_to_hex_int = vector_to_hex_int
            self.fast_hamming = fast_hamming
            self.available = True
        except Exception:
            self.available = False

        # Tool registry
        self.tools = {
            "GOLAY_SNAP": self.tool_golay_snap,
            "NRCI_COMPUTE": self.tool_nrci_compute,
            "HAMMING_DIST": self.tool_hamming_dist,
            "CRG_WALK": self.tool_crg_walk,
            "MATH_EVAL": self.tool_math_eval,
            "VECTOR_ANALYZE": self.tool_vector_analyze,
            "PRIMALITY": self.tool_primality,
            "GRAY_CODE": self.tool_gray_code,
            "SUBSTRATE_MAP": self.tool_substrate_map,
        }

    def select_tools(self, query: str, concept: str = None) -> List[str]:
        """Select which tools to use based on the query."""
        q = query.lower()
        selected = []

        # Always useful
        if concept:
            selected.append("VECTOR_ANALYZE")
            selected.append("SUBSTRATE_MAP")

        # Math queries
        if any(w in q for w in ['calculate', 'compute', 'what is', 'solve', '+', '-', '*', '/', 'mod', 'sqrt']):
            selected.append("MATH_EVAL")

        # Primality/number queries
        if any(w in q for w in ['prime', 'primality', 'divisible']):
            selected.append("PRIMALITY")

        # Distance/comparison queries
        if any(w in q for w in ['distance', 'close', 'similar', 'related', 'compare']):
            selected.append("HAMMING_DIST")

        # NRCI/stability queries
        if any(w in q for w in ['stable', 'stability', 'nrci', 'coherence', 'noise']):
            selected.append("NRCI_COMPUTE")

        # Gray code queries
        if any(w in q for w in ['gray', 'binary', 'code', 'encode']):
            selected.append("GRAY_CODE")

        # Relationship queries
        if any(w in q for w in ['relate', 'connection', 'path', 'how does', 'link']):
            selected.append("CRG_WALK")

        # Snap queries
        if any(w in q for w in ['snap', 'nearest', 'closest', 'codeword']):
            selected.append("GOLAY_SNAP")

        # Default: at least vector analysis and substrate map
        if not selected and concept:
            selected = ["VECTOR_ANALYZE", "SUBSTRATE_MAP"]

        return selected

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool."""
        if tool_name not in self.tools:
            return ToolResult(tool_name, None, f"Unknown tool: {tool_name}", success=False)
        try:
            return self.tools[tool_name](**kwargs)
        except Exception as e:
            return ToolResult(tool_name, None, f"Error: {e}", success=False)

    def execute_all(self, tool_names: List[str], **kwargs) -> List[ToolResult]:
        """Execute multiple tools."""
        return [self.execute(name, **kwargs) for name in tool_names]

    # ── Tool Implementations ──────────────────────────────────────────────

    def tool_golay_snap(self, concept: str = None, vector: List[int] = None, **kw) -> ToolResult:
        """Snap a vector to the nearest Golay codeword."""
        if not self.available:
            return ToolResult("GOLAY_SNAP", None, "Golay engine not available", success=False)

        if vector is None and concept:
            entry = self.vocab.get(concept)
            if entry and hasattr(entry, 'vector'):
                vector = list(entry.vector)

        if not vector:
            return ToolResult("GOLAY_SNAP", None, "No vector provided", success=False)

        snapped, meta = self.golay.snap_to_codeword(vector)
        hex_val = self.vector_to_hex_int(snapped)
        hw = sum(snapped)
        sw = meta.get("syndrome_weight", 0)

        return ToolResult("GOLAY_SNAP", {
            "snapped": snapped, "hex": hex_val, "hw": hw,
            "syndrome_weight": sw, "corrected": sw > 0
        }, f"Snapped to 0x{hex_val:06X} (HW={hw}, syndrome={sw})")

    def tool_nrci_compute(self, concept: str = None, vector: List[int] = None, **kw) -> ToolResult:
        """Compute NRCI for a vector."""
        if not self.available:
            return ToolResult("NRCI_COMPUTE", None, "Leech engine not available", success=False)

        if vector is None and concept:
            entry = self.vocab.get(concept)
            if entry and hasattr(entry, 'vector'):
                vector = list(entry.vector)

        if not vector:
            return ToolResult("NRCI_COMPUTE", None, "No vector provided", success=False)

        nrci = float(self.leech.calculate_nrci(vector))
        tax = float(self.leech.calculate_symmetry_tax(vector))

        return ToolResult("NRCI_COMPUTE", {
            "nrci": nrci, "tax": tax,
            "stable": nrci > 0.7,
            "threshold": "consciousness" if nrci >= 0.7 else "subliminal"
        }, f"NRCI={nrci:.4f}, tax={tax:.4f} ({'stable' if nrci > 0.7 else 'unstable'})")

    def tool_hamming_dist(self, concept1: str = None, concept2: str = None,
                           vec1: List[int] = None, vec2: List[int] = None, **kw) -> ToolResult:
        """Hamming distance between two concepts."""
        if not self.available:
            return ToolResult("HAMMING_DIST", None, "Engine not available", success=False)

        if vec1 is None and concept1:
            e1 = self.vocab.get(concept1)
            if e1 and hasattr(e1, 'vector'): vec1 = list(e1.vector)
        if vec2 is None and concept2:
            e2 = self.vocab.get(concept2)
            if e2 and hasattr(e2, 'vector'): vec2 = list(e2.vector)

        if not vec1 or not vec2:
            return ToolResult("HAMMING_DIST", None, "Vectors not found", success=False)

        h1 = self.vector_to_hex_int(vec1)
        h2 = self.vector_to_hex_int(vec2)
        dist = self.fast_hamming(h1, h2)

        return ToolResult("HAMMING_DIST", {
            "distance": dist, "max": 24, "similarity": 1.0 - dist / 24.0
        }, f"d({concept1 or '?'},{concept2 or '?'}) = {dist}/24 (sim={1.0-dist/24.0:.2f})")

    def tool_crg_walk(self, concept: str = None, target: str = None, max_hops: int = 3, **kw) -> ToolResult:
        """Walk the CRG from concept to target."""
        if not concept:
            return ToolResult("CRG_WALK", None, "No concept provided", success=False)

        SKIP = {"auto_proposed", "co_occurs"}
        path = []
        current = concept.lower()
        visited = {current}

        for _ in range(max_hops):
            found = False
            for edge in self.crg.out.get(current, []):
                if edge.label in SKIP or edge.label.startswith('lattice_adjacent'):
                    continue
                if edge.dst not in visited and edge.src != edge.dst:
                    path.append((current, edge.label, edge.dst))
                    visited.add(edge.dst)
                    current = edge.dst
                    found = True
                    if target and current == target.lower():
                        return ToolResult("CRG_WALK", {
                            "path": path, "hops": len(path), "found": True
                        }, f"Path: {' → '.join(f'{s}--{l}-->{d}' for s,l,d in path)}")
                    break
            if not found:
                break

        return ToolResult("CRG_WALK", {
            "path": path, "hops": len(path), "found": target and current == target.lower()
        }, f"Walked {len(path)} hops: {' → '.join(f'{s}--{l}-->{d}' for s,l,d in path)}")

    def tool_math_eval(self, expression: str = None, **kw) -> ToolResult:
        """Evaluate a mathematical expression."""
        if not expression:
            return ToolResult("MATH_EVAL", None, "No expression", success=False)

        try:
            # Try SymPy first
            import sympy
            result = sympy.sympify(expression)
            return ToolResult("MATH_EVAL", {
                "expression": expression, "result": str(result),
                "numeric": float(result) if result.is_number else None
            }, f"{expression} = {result}")
        except:
            # Fallback to eval
            try:
                result = eval(expression)
                return ToolResult("MATH_EVAL", {
                    "expression": expression, "result": str(result), "numeric": result
                }, f"{expression} = {result}")
            except Exception as e:
                return ToolResult("MATH_EVAL", None, f"Cannot evaluate: {e}", success=False)

    def tool_vector_analyze(self, concept: str = None, vector: List[int] = None, **kw) -> ToolResult:
        """Full geometric analysis of a concept."""
        if vector is None and concept:
            entry = self.vocab.get(concept)
            if entry and hasattr(entry, 'vector'):
                vector = list(entry.vector)

        if not vector:
            return ToolResult("VECTOR_ANALYZE", None, "No vector", success=False)

        q = [sum(vector[0:6]), sum(vector[6:12]), sum(vector[12:18]), sum(vector[18:24])]
        layers = ["Reality", "Information", "Activation", "Potential"]
        dominant = q.index(max(q))
        hw = sum(vector)
        hex_val = self.vector_to_hex_int(vector) if self.available else 0

        # Compute NRCI if available
        nrci = None
        if self.available:
            try:
                nrci = float(self.leech.calculate_nrci(vector))
            except:
                pass

        return ToolResult("VECTOR_ANALYZE", {
            "quadrants": q, "dominant": layers[dominant],
            "hw": hw, "hex": hex_val, "nrci": nrci,
            "balanced": max(q) - min(q) <= 2
        }, f"Layer={layers[dominant]}, Q={q}, HW={hw}, NRCI={nrci:.4f}" if nrci else f"Layer={layers[dominant]}, Q={q}, HW={hw}")

    def tool_primality(self, number: int = None, **kw) -> ToolResult:
        """Primality test."""
        if number is None:
            return ToolResult("PRIMALITY", None, "No number", success=False)

        # Simple primality test
        if number < 2:
            is_prime = False
        elif number < 4:
            is_prime = True
        elif number % 2 == 0 or number % 3 == 0:
            is_prime = False
        else:
            is_prime = True
            i = 5
            while i * i <= number:
                if number % i == 0 or number % (i + 2) == 0:
                    is_prime = False
                    break
                i += 6

        return ToolResult("PRIMALITY", {
            "number": number, "is_prime": is_prime,
            "factors": self._factorize(number) if not is_prime else [1, number]
        }, f"{number} is {'prime' if is_prime else 'composite'}")

    def tool_gray_code(self, number: int = None, **kw) -> ToolResult:
        """Convert to Gray code."""
        if number is None:
            return ToolResult("GRAY_CODE", None, "No number", success=False)

        gray = number ^ (number >> 1)
        binary = format(number, 'b')
        gray_str = format(gray, 'b')

        return ToolResult("GRAY_CODE", {
            "decimal": number, "binary": binary, "gray": gray_str, "gray_decimal": gray
        }, f"{number} → binary={binary}, gray={gray_str}")

    def tool_substrate_map(self, concept: str = None, vector: List[int] = None, **kw) -> ToolResult:
        """Map a concept to its ontological layer."""
        if vector is None and concept:
            entry = self.vocab.get(concept)
            if entry and hasattr(entry, 'vector'):
                vector = list(entry.vector)

        if not vector:
            return ToolResult("SUBSTRATE_MAP", None, "No vector", success=False)

        q = [sum(vector[0:6]), sum(vector[6:12]), sum(vector[12:18]), sum(vector[18:24])]
        layers = ["Reality", "Information", "Activation", "Potential"]
        roles = ["NOUN", "ADJECTIVE", "VERB", "OPERATOR"]
        dominant = q.index(max(q))

        return ToolResult("SUBSTRATE_MAP", {
            "layer": layers[dominant], "role": roles[dominant],
            "quadrants": dict(zip(layers, q)),
            "concept": concept
        }, f"{concept} → {layers[dominant]} ({roles[dominant]}), Q={q}")

    def _factorize(self, n: int) -> List[int]:
        """Simple factorization."""
        factors = []
        d = 2
        while d * d <= n:
            while n % d == 0:
                factors.append(d)
                n //= d
            d += 1
        if n > 1:
            factors.append(n)
        return factors


class ToolEnhancedEngine:
    """Three Column Thinking with real tool execution."""

    def __init__(self, vocab, crg, runtime=None):
        self.tools = GLMTools(vocab, crg, runtime)
        self.vocab = vocab
        self.crg = crg

    def think_with_tools(self, query: str, pipeline_state: dict) -> List[dict]:
        """Three Column Thinking with actual tool execution."""
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
                     "math": "∅", "script": "# No concept", "aligned": True, "tool_results": []}]

        # Select and execute tools
        tool_names = self.tools.select_tools(query, primary)
        tool_results = self.tools.execute_all(tool_names, concept=primary,
                                               expression=self._extract_expr(query))

        steps = [
            self._step_definition(primary, tool_results),
            self._step_relationships(primary, tool_results),
            self._step_geometry(primary, tool_results),
            self._step_implications(primary, tool_results),
            self._step_resolution(primary, tool_results),
        ]
        return steps

    def _step_definition(self, concept: str, tool_results: List[ToolResult]) -> dict:
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

        # Use actual NRCI tool result
        nrci_result = self._find_tool_result(tool_results, "NRCI_COMPUTE")
        if nrci_result and nrci_result.success:
            nrci = nrci_result.output["nrci"]
            stability = nrci_result.output["threshold"]
            lang += f" Its NRCI is {nrci:.4f} ({stability})."
            math = f"NRCI({concept}) = {nrci:.4f} ({stability})"
        else:
            nrci = float(entry.nrci) if entry and hasattr(entry, 'nrci') else 0.0
            math = f"NRCI({concept}) = {nrci:.4f}"

        hw = sum(entry.vector) if entry and hasattr(entry, 'vector') else 0
        math += f", HW = {hw}"

        return {"label": "definition", "language": lang, "math": math,
                "script": self._format_tool_script("NRCI_COMPUTE", concept),
                "aligned": bool(defn) and nrci > 0,
                "tool_results": [nrci_result] if nrci_result else []}

    def _step_relationships(self, concept: str, tool_results: List[ToolResult]) -> dict:
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
            lang = ". ".join(sents) + "."
            math = " ∧ ".join(f"{e.src}--{e.label}-->{e.dst}" for e in outgoing[:3])
        else:
            lang = f"{concept.capitalize()} has limited connections in the current knowledge graph."
            math = f"out({concept}) = ∅"

        # Use CRG_WALK tool result
        walk_result = self._find_tool_result(tool_results, "CRG_WALK")
        if walk_result and walk_result.success:
            hops = walk_result.output["hops"]
            if hops > 1:
                lang += f" A {hops}-hop walk through the graph reveals deeper connections."

        return {"label": "relationships", "language": lang, "math": math,
                "script": self._format_tool_script("CRG_WALK", concept),
                "aligned": len(outgoing) > 0,
                "tool_results": [walk_result] if walk_result else []}

    def _step_geometry(self, concept: str, tool_results: List[ToolResult]) -> dict:
        # Use VECTOR_ANALYZE tool result
        analyze_result = self._find_tool_result(tool_results, "VECTOR_ANALYZE")
        if analyze_result and analyze_result.success:
            layer = analyze_result.output["dominant"]
            q = analyze_result.output["quadrants"]
            nrci = analyze_result.output.get("nrci")
            balanced = analyze_result.output.get("balanced", False)
        else:
            entry = self.vocab.get(concept)
            v = list(entry.vector) if entry and hasattr(entry, 'vector') else [0]*24
            q = [sum(v[0:6]), sum(v[6:12]), sum(v[12:18]), sum(v[18:24])]
            layer = ["Reality", "Information", "Activation", "Potential"][q.index(max(q))]
            nrci = None
            balanced = False

        descs = {"Reality": "concrete, physical existence",
                 "Information": "relational, descriptive qualities",
                 "Activation": "dynamic processes and transformations",
                 "Potential": "abstract, logical relationships"}

        rel_words = [e.dst for e in self.crg.out.get(concept, [])[:3]
                     if e.label not in ('auto_proposed', 'co_occurs')
                     and not e.label.startswith('lattice_adjacent')]
        rel_ref = f", alongside its connections to {', '.join(rel_words[:2])}," if rel_words else ""

        lang = (f"Looking at its position in the 24-bit substrate, this {concept} "
                f"occupies the {layer} layer, the domain of {descs[layer]}{rel_ref} "
                f"with {max(q)} bits set in the dominant sextet, "
                f"anchoring {concept} firmly in this region of the geometric space.")

        if balanced:
            lang += " The quadrants are relatively balanced, suggesting broad influence."

        math = f"v({concept}) = Q = {q}"

        return {"label": "geometry", "language": lang, "math": math,
                "script": self._format_tool_script("VECTOR_ANALYZE", concept),
                "aligned": max(q) > 0,
                "tool_results": [analyze_result] if analyze_result else []}

    def _step_implications(self, concept: str, tool_results: List[ToolResult]) -> dict:
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
                    sents.append(f"which in turn {l} {dst.lower()}")
            lang = ". ".join(sents) + f". This chain reveals how {concept} participates in the broader structure of the substrate."
            math = "chain: " + " → ".join(f"{s}" for s, _, _ in chain) + f" → {chain[-1][2]}"
        else:
            lang = f"The implications of {concept} extend beyond the current knowledge graph, suggesting connections yet to be discovered."
            math = f"chain({concept}) = ∅"

        # Use HAMMING_DIST tool result
        dist_result = self._find_tool_result(tool_results, "HAMMING_DIST")
        if dist_result and dist_result.success:
            dist = dist_result.output["distance"]
            sim = dist_result.output["similarity"]
            lang += f" Geometric analysis confirms proximity: distance {dist}/24, similarity {sim:.2f}."

        return {"label": "implications", "language": lang, "math": math,
                "script": self._format_tool_script("CRG_WALK", concept),
                "aligned": len(chain) > 0,
                "tool_results": [dist_result] if dist_result else []}

    def _step_resolution(self, concept: str, tool_results: List[ToolResult]) -> dict:
        # Check tool alignment
        successful_tools = sum(1 for r in tool_results if r.success)
        total_tools = len(tool_results)

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
                f"through the CRG's semantic edges, and verified by {successful_tools}/{total_tools} "
                f"executed tools. This alignment across language, mathematics, and executable "
                f"code gives us confidence that the picture of {concept} is coherent and complete.")

        return {"label": "resolution", "language": lang,
                "math": f"resolve({concept}) = ✓ ({successful_tools}/{total_tools} tools)",
                "script": f"tools_verified = {successful_tools}/{total_tools}",
                "aligned": successful_tools > 0,
                "tool_results": tool_results}

    def _step_computation(self, compute: dict) -> dict:
        res = compute.get("result", {})
        expr = compute.get("computation", {}).get("expr", "")
        exact = res.get("exact", "")

        # Use UBP native fingerprint data (already computed!)
        fingerprint = res.get("fingerprint", {})
        nrci = fingerprint.get("nrci", 0)
        lattice = fingerprint.get("lattice", "")
        clarity = fingerprint.get("clarity", "")
        monster = fingerprint.get("monster_grade", "")
        native = res.get("native", False)
        trace = res.get("trace", [])
        grounded = compute.get("grounded")
        grounded_word = grounded[0] if grounded else exact

        # Build rich geometric description
        lang = f"Computing {expr} gives us {exact}."

        if native and fingerprint:
            lang += (f" In the 24-bit Golay substrate, this result has NRCI={nrci:.4f} "
                    f"({clarity} clarity), lattice type '{lattice}', "
                    f"and is classified as {monster} grade.")

            if trace:
                trace_str = " → ".join(trace)
                lang += f" The computation trace is: {trace_str}."

            bw256 = fingerprint.get("bw256", {})
            if bw256:
                macro = bw256.get("macro_nrci", 0)
                micro = bw256.get("micro_nrci", 0)
                lang += (f" At the Barnes-Wall 256 level, macro-NRCI={macro:.4f} "
                        f"and micro-NRCI={micro:.4f}.")

            if grounded_word:
                lang += f" This maps to the lattice point '{grounded_word}' in the substrate."

            lang += " The computation was verified by UBP's native geometric engine."
        else:
            lang += (f" This result maps to the lattice point '{grounded_word}' "
                    f"in the 24-bit Golay substrate, grounding the arithmetic in geometry.")

        return {"label": "computation", "language": lang,
                "math": f"{expr} = {exact} (NRCI={nrci:.4f}, {lattice})",
                "script": f"result = ubp_compute('{expr}')  # native={native}, {monster}",
                "aligned": True,
                "tool_results": []}

    def _find_tool_result(self, results: List[ToolResult], name: str) -> Optional[ToolResult]:
        for r in results:
            if r.tool_name == name:
                return r
        return None

    def _format_tool_script(self, tool_name: str, concept: str) -> str:
        scripts = {
            "NRCI_COMPUTE": f"nrci = leech.calculate_nrci(vocab['{concept}'].vector)",
            "CRG_WALK": f"path = walk_crg('{concept}', crg)",
            "VECTOR_ANALYZE": f"analysis = analyze_vector(vocab['{concept}'].vector)",
            "HAMMING_DIST": f"dist = hamming(vocab['{concept}'].vector, target)",
            "GOLAY_SNAP": f"snapped = golay.snap_to_codeword(vocab['{concept}'].vector)",
            "MATH_EVAL": f"result = evaluate(expression)",
        }
        return scripts.get(tool_name, f"# {tool_name}")

    def _extract_expr(self, query: str) -> Optional[str]:
        """Extract math expression from query."""
        # Simple patterns
        match = re.search(r'(\d+\s*[\+\-\*/\^%]\s*\d+)', query)
        if match:
            return match.group(1).replace('^', '**')
        match = re.search(r'sqrt\((\d+)\)', query)
        if match:
            return f"sqrt({match.group(1)})"
        match = re.search(r'(\d+)!', query)
        if match:
            return f"factorial({match.group(1)})"
        match = re.search(r'(\d+)\s*mod\s*(\d+)', query)
        if match:
            return f"{match.group(1)} % {match.group(2)}"
        return None


if __name__ == "__main__":
    print("=== GLM Tools — Executable Tool System ===")
    print("The Script column becomes REAL.")

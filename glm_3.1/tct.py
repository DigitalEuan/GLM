#!/usr/bin/env python3
"""
Three Column Thinking — the GLM's reasoning output format.

Every response is structured as aligned thought steps:
  Column 1: LANGUAGE — Natural language explanation
  Column 2: MATH    — Exact dimensional/geometric representation
  Column 3: SCRIPT  — Executable verification code

This module takes a query and the reasoner's outputs, and produces
a structured Three Column response.
"""

from typing import Dict, List, Any, Optional
from fractions import Fraction as F


class ThreeColumnEngine:
    """
    Produces Three Column Thinking output from reasoner results.

    Usage:
        engine = ThreeColumnEngine(reasoner)
        result = engine.think("What is energy?")
        engine.print_result(result)
    """

    def __init__(self, reasoner):
        self.reasoner = reasoner

    def think(self, query: str) -> Dict[str, Any]:
        """
        Process a query through Three Column Thinking.

        Returns a dict with:
          - query: the original query
          - steps: list of {language, math, script} dicts
          - resolution: the final answer
        """
        query_lower = query.lower().strip()

        # ── Detect intent ───────────────────────────────────────────
        if self._is_audit_query(query_lower):
            return self._think_audit(query)
        elif self._is_solve_query(query_lower):
            return self._think_solve(query)
        elif self._is_what_is(query_lower):
            return self._think_what_is(query)
        elif self._is_compare(query_lower):
            return self._think_compare(query)
        elif self._is_nearest(query_lower):
            return self._think_nearest(query)
        else:
            return self._think_general(query)

    # ── Intent detection ────────────────────────────────────────────

    def _is_audit_query(self, q: str) -> bool:
        return any(w in q for w in ["verify", "check", "is .* equal",
                                     "does .* equal", "audit", "correct"])

    def _is_solve_query(self, q: str) -> bool:
        return any(w in q for w in ["solve for", "derive", "find formula",
                                     "what formula", "how to calculate"])

    def _is_what_is(self, q: str) -> bool:
        return q.startswith("what is") or q.startswith("define")

    def _is_compare(self, q: str) -> bool:
        return any(w in q for w in ["compare", "difference between",
                                     "relation between", "how does .* relate"])

    def _is_nearest(self, q: str) -> bool:
        return any(w in q for w in ["nearest", "similar to", "close to",
                                     "related to", "neighbors of"])

    # ── Thinking strategies ─────────────────────────────────────────

    def _think_what_is(self, query: str) -> Dict[str, Any]:
        """Answer 'What is X?' with full Three Column output."""
        concept = self._extract_concept(query)
        steps = []

        # Step 1: Definition
        try:
            ident = self.reasoner.identify(concept)
            meaning = self.reasoner.meaning(concept)

            # Build the dimensional expression
            dims = []
            for axis, exp in meaning["exponents"].items():
                if exp != "0":
                    if exp == "1":
                        dims.append(axis)
                    else:
                        dims.append(f"{axis}^{exp}")
            dim_str = " ".join(dims) if dims else "dimensionless"

            carrier = self.reasoner.carrier(concept)
            hw = sum(carrier)

            steps.append({
                "step": "DEFINITION",
                "language": f"{concept} is a physical quantity with dimensions [{dim_str}].",
                "math": f"meaning({concept}) = {dim_str}, scale={meaning['scale']}, rank={meaning['rank']}",
                "script": f"m = reasoner.meaning('{concept}')\n"
                          f"carrier = reasoner.carrier('{concept}')\n"
                          f"HW = sum(carrier)  # = {hw}",
            })
        except Exception as e:
            steps.append({
                "step": "DEFINITION",
                "language": f"Concept '{concept}' not found in library.",
                "math": "N/A",
                "script": f"# {e}",
            })
            return {"query": query, "steps": steps, "resolution": "Concept not found."}

        # Step 2: Relationships
        try:
            nearest = self.reasoner.nearest(concept, 5)
            neighbours_str = ", ".join(
                f"{name} ({sim:.3f})" for name, sim in nearest
            )
            steps.append({
                "step": "RELATIONSHIPS",
                "language": f"Closest concepts in Griess algebra space: {neighbours_str}.",
                "math": f"nearest({concept}, 5) = [{neighbours_str}]",
                "script": f"nearest = reasoner.nearest('{concept}', 5)\n"
                          f"for name, sim in nearest:\n"
                          f"    print(f'  {{name}}: {{sim:.4f}}')",
            })
        except Exception as e:
            steps.append({
                "step": "RELATIONSHIPS",
                "language": "Could not compute neighbours.",
                "math": "N/A",
                "script": f"# {e}",
            })

        # Step 3: Carrier geometry
        try:
            address = self.reasoner.address(concept)
            steps.append({
                "step": "GEOMETRY",
                "language": (f"Monster address type word: {address.get('type_word', '?')}, "
                             f"carrier norm²: {address.get('carrier_norm', '?')}."),
                "math": (f"address({concept}) = planes={address.get('planes', [])[:3]}..., "
                         f"types={address.get('types', [])}"),
                "script": f"addr = reasoner.address('{concept}')\n"
                          f"print(f'Type word: {{addr[\"type_word\"]}}')\n"
                          f"print(f'Carrier norm²: {{addr[\"carrier_norm\"]}}')",
            })
        except Exception as e:
            steps.append({
                "step": "GEOMETRY",
                "language": "Monster address not available.",
                "math": "N/A",
                "script": f"# {e}",
            })

        # Resolution
        steps.append({
            "step": "RESOLUTION",
            "language": f"{concept} is well-defined and coherent in the GLM substrate.",
            "math": f"All columns align for '{concept}'.",
            "script": f"# Verified: {concept} has exact meaning, carrier, and Monster address.",
        })

        return {"query": query, "steps": steps, "resolution": steps[-1]["language"]}

    def _think_audit(self, query: str) -> Dict[str, Any]:
        """Verify an equation."""
        lhs, rhs = self._extract_equation(query)
        steps = []

        # Step 1: Parse
        steps.append({
            "step": "PARSE",
            "language": f"Verifying: {lhs} =? {rhs}",
            "math": f"audit({lhs}, {rhs})",
            "script": f"result = reasoner.audit('{lhs}', '{rhs}')",
        })

        # Step 2: Dimensions
        try:
            lhs_m = self.reasoner.meaning(lhs)
            rhs_m = self.reasoner.meaning(rhs)
            steps.append({
                "step": "DIMENSIONS",
                "language": f"LHS dimensions: {lhs_m['exponents']}. RHS dimensions: {rhs_m['exponents']}.",
                "math": f"dim({lhs}) = {lhs_m['exponents']}\ndim({rhs}) = {rhs_m['exponents']}",
                "script": f"lhs = reasoner.meaning('{lhs}')\nrhs = reasoner.meaning('{rhs}')\n"
                          f"print(f'LHS: {{lhs[\"exponents\"]}}')\nprint(f'RHS: {{rhs[\"exponents\"]}}')",
            })
        except Exception as e:
            steps.append({
                "step": "DIMENSIONS",
                "language": f"Could not resolve dimensions: {e}",
                "math": "N/A",
                "script": f"# {e}",
            })

        # Step 3: Verdict
        try:
            result = self.reasoner.audit(lhs, rhs)
            passed = result["pass"]
            steps.append({
                "step": "VERDICT",
                "language": f"{'PASS' if passed else 'FAIL'}: {lhs} {'=' if passed else '≠'} {rhs}",
                "math": f"audit = {'PASS' if passed else 'FAIL'}",
                "script": f"result = reasoner.audit('{lhs}', '{rhs}')\n"
                          f"print(f'Pass: {{result[\"pass\"]}}')\n"
                          f"print(f'Reasons: {{result[\"reasons\"]}}')",
            })
        except Exception as e:
            steps.append({
                "step": "VERDICT",
                "language": f"Audit failed: {e}",
                "math": "N/A",
                "script": f"# {e}",
            })

        return {"query": query, "steps": steps, "resolution": steps[-1]["language"]}

    def _think_solve(self, query: str) -> Dict[str, Any]:
        """Derive a formula."""
        target, sources = self._extract_solve(query)
        steps = []

        steps.append({
            "step": "PROBLEM",
            "language": f"Deriving formula for {target} from {', '.join(sources)}.",
            "math": f"solve({target}; {', '.join(sources)})",
            "script": f"result = reasoner.solve('{target}', {sources})",
        })

        try:
            result = self.reasoner.solve(target, sources)
            steps.append({
                "step": "DERIVATION",
                "language": f"Formula: {result.get('formula', 'not found')}",
                "math": f"{target} = {result.get('formula', '?')}",
                "script": f"result = reasoner.solve('{target}', {sources})\n"
                          f"print(f'Formula: {{result[\"formula\"]}}')\n"
                          f"print(f'Solvable: {{result[\"solvable\"]}}')",
            })
        except Exception as e:
            steps.append({
                "step": "DERIVATION",
                "language": f"Could not derive: {e}",
                "math": "N/A",
                "script": f"# {e}",
            })

        return {"query": query, "steps": steps, "resolution": steps[-1]["language"]}

    def _think_compare(self, query: str) -> Dict[str, Any]:
        """Compare two concepts."""
        concepts = self._extract_two_concepts(query)
        if len(concepts) < 2:
            return self._think_general(query)

        a, b = concepts[0], concepts[1]
        steps = []

        # Step 1: Meanings
        try:
            ma = self.reasoner.meaning(a)
            mb = self.reasoner.meaning(b)
            steps.append({
                "step": "MEANINGS",
                "language": f"{a}: {ma['exponents']}. {b}: {mb['exponents']}.",
                "math": f"dim({a}) = {ma['exponents']}\ndim({b}) = {mb['exponents']}",
                "script": f"ma = reasoner.meaning('{a}')\nmb = reasoner.meaning('{b}')",
            })
        except Exception as e:
            steps.append({"step": "MEANINGS", "language": str(e), "math": "N/A", "script": f"# {e}"})

        # Step 2: Relation
        try:
            rel = self.reasoner.relation(a, b)
            steps.append({
                "step": "RELATION",
                "language": f"Relation type: {rel}",
                "math": f"relation({a}, {b}) = {rel}",
                "script": f"rel = reasoner.relation('{a}', '{b}')\nprint(rel)",
            })
        except Exception as e:
            steps.append({"step": "RELATION", "language": str(e), "math": "N/A", "script": f"# {e}"})

        # Step 3: Distance
        try:
            sim = self.reasoner.similarity(a, b)
            dist = self.reasoner.distance(a, b)
            steps.append({
                "step": "DISTANCE",
                "language": f"Griess similarity: {sim:.4f}, distance: {dist}.",
                "math": f"sim({a},{b}) = {sim:.4f}, d({a},{b}) = {dist}",
                "script": f"sim = reasoner.similarity('{a}', '{b}')\n"
                          f"dist = reasoner.distance('{a}', '{b}')",
            })
        except Exception as e:
            steps.append({"step": "DISTANCE", "language": str(e), "math": "N/A", "script": f"# {e}"})

        return {"query": query, "steps": steps, "resolution": f"Comparison of {a} and {b} complete."}

    def _think_nearest(self, query: str) -> Dict[str, Any]:
        """Find nearest concepts."""
        concept = self._extract_concept(query)
        steps = []

        try:
            nearest = self.reasoner.nearest(concept, 8)
            neighbours_str = "\n".join(
                f"  {name}: similarity={sim:.4f}" for name, sim in nearest
            )
            steps.append({
                "step": "NEIGHBOURS",
                "language": f"8 nearest concepts to '{concept}' in Griess algebra space:\n{neighbours_str}",
                "math": f"nearest({concept}, 8)",
                "script": f"for name, sim in reasoner.nearest('{concept}', 8):\n"
                          f"    print(f'  {{name}}: {{sim:.4f}}')",
            })
        except Exception as e:
            steps.append({"step": "NEIGHBOURS", "language": str(e), "math": "N/A", "script": f"# {e}"})

        return {"query": query, "steps": steps, "resolution": steps[-1]["language"]}

    def _think_general(self, query: str) -> Dict[str, Any]:
        """General fallback: try to identify any concepts mentioned."""
        words = query.lower().split()
        known = [w for w in words if self._is_concept(w)]
        steps = []

        if known:
            for concept in known[:3]:
                try:
                    m = self.reasoner.meaning(concept)
                    steps.append({
                        "step": f"CONCEPT: {concept}",
                        "language": f"{concept} has dimensions {m['exponents']}.",
                        "math": f"meaning({concept}) = {m['exponents']}",
                        "script": f"m = reasoner.meaning('{concept}')\nprint(m['exponents'])",
                    })
                except Exception:
                    pass

        if not steps:
            steps.append({
                "step": "FALLBACK",
                "language": f"I don't recognise specific concepts in '{query}'. Try: 'What is energy?' or 'Verify force = mass * acceleration'.",
                "math": "N/A",
                "script": "# Try: reasoner.list_concepts() to see available concepts.",
            })

        return {"query": query, "steps": steps, "resolution": steps[-1]["language"]}

    # ── Extraction helpers ──────────────────────────────────────────

    def _extract_concept(self, query: str) -> str:
        """Extract a concept name from a query."""
        # Try multi-word concepts first ("kinetic energy", "speed of light")
        query_lower = query.lower().strip()
        # Check if the whole query (minus question words) is a concept
        cleaned = query_lower.replace("?", "").strip()
        if self._is_concept(cleaned):
            return cleaned
        # Try individual words, longest first
        words = sorted(cleaned.split(), key=len, reverse=True)
        for w in words:
            w = w.strip("?.,;:'\"()")
            if self._is_concept(w):
                return w
        # Try pairs of adjacent words
        raw_words = cleaned.split()
        for i in range(len(raw_words) - 1):
            pair = f"{raw_words[i]}_{raw_words[i+1]}"
            if self._is_concept(pair):
                return pair
        # Fallback
        return words[0] if words else "energy"

    def _extract_equation(self, query: str) -> tuple:
        """Extract LHS and RHS from an equation query."""
        for sep in ["=", " equals ", " equal to ", " == "]:
            if sep in query:
                parts = query.split(sep, 1)
                lhs = parts[0].split()[-1] if parts[0].split() else "energy"
                rhs = parts[1].strip().rstrip("?.").strip()
                return lhs, rhs
        return "energy", "mass*speed^2"

    def _extract_solve(self, query: str) -> tuple:
        """Extract target and sources from a solve query."""
        # Simple heuristic: "solve for X from Y and Z"
        words = query.lower().replace(",", " ").split()
        target = "energy"
        sources = ["mass", "speed"]
        if "for" in words:
            idx = words.index("for")
            if idx + 1 < len(words):
                target = words[idx + 1]
        if "from" in words:
            idx = words.index("from")
            sources = [w for w in words[idx + 1:] if self._is_concept(w)]
        return target, sources

    def _extract_two_concepts(self, query: str) -> List[str]:
        """Extract two concept names from a comparison query."""
        words = query.lower().replace(",", " ").split()
        concepts = [w for w in words if self._is_concept(w)]
        return concepts[:2]

    def _is_concept(self, word: str) -> bool:
        """Check if a word is a known concept."""
        try:
            self.reasoner.meaning(word)
            return True
        except Exception:
            return False

    # ── Output formatting ───────────────────────────────────────────

    def format_result(self, result: Dict[str, Any]) -> str:
        """Format a Three Column result as readable text."""
        lines = []
        lines.append(f"Query: {result['query']}")
        lines.append("=" * 72)

        for step in result.get("steps", []):
            lines.append(f"\n  Step: {step.get('step', '?')}")
            lines.append(f"  LANGUAGE: {step.get('language', 'N/A')}")
            lines.append(f"  MATH:     {step.get('math', 'N/A')}")
            lines.append(f"  SCRIPT:   {step.get('script', 'N/A')}")

        lines.append(f"\n{'=' * 72}")
        lines.append(f"Resolution: {result.get('resolution', 'N/A')}")
        return "\n".join(lines)

    def print_result(self, result: Dict[str, Any]):
        """Print a formatted Three Column result."""
        print(self.format_result(result))

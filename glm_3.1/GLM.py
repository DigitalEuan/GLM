#!/usr/bin/env python3
"""
GLM — The Unified Geometric Language Machine
=============================================

A deterministic reasoning system built on exact mathematics.

Architecture:
  Meaning → Carrier → Reasoning → Language → Learning → Growth

  Meaning:  10 rational exponents (exact, from glm3's 660-concept library)
  Carrier:  Leech lattice point (derived from meaning, never primary)
  Reasoning: Monster algebra verification, formula discovery, Buckingham Pi
  Language:  Three Column Thinking (language + math + script)
  Learning:  Text ingestion → exact meaning extraction → CRG growth

Usage:
    from GLM import GLM
    glm = GLM()

    # Ask a question
    glm.chat("What is energy?")

    # Verify an equation
    glm.verify("energy", "mass*speed^2")

    # Derive a formula
    glm.solve("speed", ["energy", "mass"])

    # Learn from text
    glm.learn("Energy is mass times speed squared.")

    # Find similar concepts
    glm.nearest("energy")

    # List all concepts
    glm.list_concepts()
"""

__version__ = "5.0.0"
__author__ = "Euan R. A. Craig (DigitalEuan)"

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# ── Path setup ──────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent

# Ensure glm_lean modules are importable
for sub in ["glm3", "glm2", "glm"]:
    p = str(_REPO / "glm_lean" / sub)
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Import components ───────────────────────────────────────────────────
from reasoner import GLMReasoner
from tct import ThreeColumnEngine
from learner import Learner


class GLM:
    """
    The Unified Geometric Language Machine.

    Combines:
      - glm_lean/glm3: exact reasoning in the Monster algebra
      - Three Column Thinking: structured output
      - Learning: text ingestion and CRG growth
    """

    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize the GLM.

        Args:
            state_dir: Directory for persistent state (learned concepts, CRG).
                       Defaults to glm_new/state/
        """
        if state_dir is None:
            state_dir = _HERE / "state"

        # Core reasoner (glm_lean/glm3)
        self.reasoner = GLMReasoner()

        # Three Column Thinking engine
        self.tct = ThreeColumnEngine(self.reasoner)

        # Learning engine
        self.learner = Learner(
            self.reasoner,
            state_path=state_dir / "learned.json"
        )

        self._state_dir = state_dir

    # ── Primary interface ───────────────────────────────────────────

    def chat(self, query: str) -> str:
        """
        Process a query and return a Three Column Thinking response.

        Returns formatted text with LANGUAGE + MATH + SCRIPT columns.
        """
        result = self.tct.think(query)
        return self.tct.format_result(result)

    def chat_verbose(self, query: str) -> Dict[str, Any]:
        """
        Process a query and return structured result.

        Returns dict with query, steps, and resolution.
        """
        return self.tct.think(query)

    # ── Reasoning (exact) ───────────────────────────────────────────

    def verify(self, lhs: str, rhs: str) -> bool:
        """Verify that two expressions have the same dimensions."""
        result = self.reasoner.audit(lhs, rhs)
        return result["pass"]

    def solve(self, target: str, sources: List[str]) -> Dict[str, Any]:
        """Derive a formula for target in terms of sources."""
        return self.reasoner.solve(target, sources)

    def meaning(self, concept: str) -> Dict[str, Any]:
        """Get the exact meaning of a concept."""
        return self.reasoner.meaning(concept)

    def carrier(self, concept: str) -> Tuple[int, ...]:
        """Get the Leech lattice point for a concept."""
        return self.reasoner.carrier(concept)

    def address(self, concept: str) -> Dict[str, Any]:
        """Get the Monster address of a concept."""
        return self.reasoner.address(concept)

    def nearest(self, concept: str, count: int = 8) -> List[Tuple[str, float]]:
        """Find nearest concepts in Griess algebra space."""
        return self.reasoner.nearest(concept, count)

    def relation(self, a: str, b: str) -> Dict[str, Any]:
        """Get the relation type code between two concepts."""
        return self.reasoner.relation(a, b)

    def distance(self, a: str, b: str) -> str:
        """Get the exact distance between two concepts."""
        return self.reasoner.distance(a, b)

    def pi_groups(self, names: List[str]) -> List[Dict[str, Any]]:
        """Extract Buckingham Pi dimensionless groups."""
        return self.reasoner.pi_groups(names)

    def domains(self) -> List[str]:
        """List all concept domains."""
        return self.reasoner.domains()

    def list_concepts(self, domain: Optional[str] = None) -> List[str]:
        """List all concepts in the library."""
        return self.reasoner.list_concepts(domain)

    def identify(self, concept: str) -> Dict[str, Any]:
        """Identify a concept — full information."""
        return self.reasoner.identify(concept)

    # ── Learning ────────────────────────────────────────────────────

    def learn(self, text: str) -> Dict[str, Any]:
        """
        Learn from text. Extracts definitions and relations.

        Returns: {definitions, relations, new_concepts}
        """
        result = self.learner.ingest(text)
        self.learner.save()
        return result

    def learned_concepts(self) -> List[str]:
        """List learned concepts."""
        return self.learner.known_concepts()

    def learned_edges(self) -> List[Dict]:
        """List learned CRG edges."""
        return self.learner.crg_edges()

    def definition(self, concept: str) -> Optional[str]:
        """Get the learned definition of a concept."""
        return self.learner.get_definition(concept)

    # ── Status ──────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Get GLM status: concept count, edges, domains."""
        concepts = self.list_concepts()
        return {
            "version": __version__,
            "library_concepts": len(concepts),
            "learned_concepts": len(self.learned_concepts()),
            "learned_edges": len(self.learned_edges()),
            "domains": self.domains(),
            "state_dir": str(self._state_dir),
        }

    # ── Testing ─────────────────────────────────────────────────────

    def quick_test(self) -> Dict[str, Any]:
        """Run a quick self-test of all components."""
        results = self.reasoner.quick_test()
        results["status"] = self.status()
        return results

    # ── CLI ─────────────────────────────────────────────────────────

    @staticmethod
    def main():
        """Command-line interface."""
        import argparse
        parser = argparse.ArgumentParser(description="GLM — Geometric Language Machine")
        parser.add_argument("--chat", type=str, help="Ask a question")
        parser.add_argument("--verify", nargs=2, metavar=("LHS", "RHS"), help="Verify equation")
        parser.add_argument("--solve", nargs="+", help="Solve: target source1 source2 ...")
        parser.add_argument("--meaning", type=str, help="Get meaning of concept")
        parser.add_argument("--nearest", type=str, help="Find nearest concepts")
        parser.add_argument("--learn", type=str, help="Learn from text")
        parser.add_argument("--list", action="store_true", help="List all concepts")
        parser.add_argument("--domains", action="store_true", help="List all domains")
        parser.add_argument("--status", action="store_true", help="Show status")
        parser.add_argument("--test", action="store_true", help="Run quick self-test")
        parser.add_argument("--interactive", action="store_true", help="Interactive mode")
        args = parser.parse_args()

        glm = GLM()

        if args.chat:
            print(glm.chat(args.chat))

        elif args.verify:
            lhs, rhs = args.verify
            result = glm.verify(lhs, rhs)
            print(f"{'PASS' if result else 'FAIL'}: {lhs} {'=' if result else '≠'} {rhs}")

        elif args.solve:
            target = args.solve[0]
            sources = args.solve[1:]
            result = glm.solve(target, sources)
            print(f"Formula: {result.get('formula', 'not found')}")
            print(f"Solvable: {result.get('solvable', False)}")

        elif args.meaning:
            m = glm.meaning(args.meaning)
            print(f"Concept: {args.meaning}")
            print(f"Dimensions: {m['exponents']}")
            print(f"Scale: {m['scale']}, Rank: {m['rank']}")
            print(f"Parities: P={m['parities']['P']}, T={m['parities']['T']}, C={m['parities']['C']}")
            print(f"Kind: {m['kind']}, Domain: {m['domain']}")

        elif args.nearest:
            for name, sim in glm.nearest(args.nearest, 8):
                print(f"  {name}: {sim:.4f}")

        elif args.learn:
            result = glm.learn(args.learn)
            print(f"Learned: {result}")

        elif args.list:
            for c in glm.list_concepts():
                print(f"  {c}")

        elif args.domains:
            for d in glm.domains():
                print(f"  {d}")

        elif args.status:
            import json
            print(json.dumps(glm.status(), indent=2))

        elif args.test:
            import json
            results = glm.quick_test()
            print(json.dumps(results, indent=2, default=str))

        elif args.interactive:
            print(f"GLM v{__version__} — Interactive Mode")
            print("Type a question, 'status' for info, 'quit' to exit.\n")
            while True:
                try:
                    query = input("GLM> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nBye.")
                    break
                if not query:
                    continue
                if query.lower() in ("quit", "exit", "q"):
                    print("Bye.")
                    break
                if query.lower() == "status":
                    import json
                    print(json.dumps(glm.status(), indent=2))
                    continue
                print()
                print(glm.chat(query))
                print()

        else:
            parser.print_help()


if __name__ == "__main__":
    GLM.main()

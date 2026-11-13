#!/usr/bin/env python3
"""
GLM Chat — the GLM answers questions and solves puzzles using the Golay Cube.

The GLM has a limited vocabulary (physics concepts). It can:
  1. Answer "What is X?" — look up the concept and describe its dimensions
  2. Answer "Does X = Y?" — check if dimensions match (integer, not mod-2)
  3. Answer "What is X × Y?" — compose concepts and find the result
  4. Solve puzzles: "If E = mc², what is mc²?" → search for matching concepts
  5. Answer "What equals X?" — search all concepts for dimensional matches
  6. Answer "Is X × Y = Z?" — compose and check

The chat is HONEST — it only knows what it knows. No faking.
"""

import sys
import json
import re
import math
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

sys.path.insert(0, '/home/z/my-project/scripts')
sys.path.insert(0, '/home/z/my-project/download/arc_agi_17')

from glm_clean import DataObject
from ubp_unified_v5 import GOLAY_ENGINE
from glm_clean.tests.test_three_ideas import (
    DimensionedConcept, encode_dimensioned, compose_concepts,
    check_equation, PHYSICS_CONCEPTS,
)


# ══════════════════════════════════════════════════════════════════════════════
# THE GLM CHAT ENGINE
# ══════════════════════════════════════════════════════════════════════════════

DIM_NAMES = ["L", "M", "T", "I", "Θ", "N"]
DIM_FULL = ["length", "mass", "time", "current", "temperature", "amount"]


def dims_to_str(dims: List[int]) -> str:
    parts = []
    for n, e in zip(DIM_NAMES, dims):
        if e == 1: parts.append(n)
        elif e != 0: parts.append(f"{n}^{e}")
    return "·".join(parts) if parts else "dimensionless"


def dims_to_human(dims: List[int]) -> str:
    parts = []
    for full, e in zip(DIM_FULL, dims):
        if e == 1: parts.append(full)
        elif e != 0: parts.append(f"{full}^{e}")
    return " × ".join(parts) if parts else "dimensionless"


class GLMChat:
    """A natural language interface to the GLM.

    The GLM has a limited vocabulary (physics concepts with dimensions).
    It can answer questions, check equations, compose concepts, and solve puzzles.

    Everything is DETERMINISTIC — no random, no XOR, no faking.
    """

    def __init__(self):
        self.concepts = {name: encode_dimensioned(name, dims)
                         for name, dims in PHYSICS_CONCEPTS.items()}
        self.body_state = []  # list of accepted equations
        self.anti_state = []  # list of rejected equations

        # Synonyms and aliases
        self.aliases = {
            "c": "speed", "v": "speed", "a": "acceleration",
            "f": "force", "e": "energy", "m": "mass", "t": "time",
            "p": "momentum", "pwr": "power", "q": "charge",
            "i": "current", "t_temp": "temperature", "n": "amount",
            "f_req": "frequency", "a_area": "area", "v_vol": "volume",
            "ρ": "density", "i_moment": "moment_inertia",
            "ω": "angular_speed", "λ": "wavelength",
            "τ": "torque", "s": "action", "volt": "voltage",
            "r": "resistance", "c_cap": "capacitance",
            "l_ind": "inductance", "φ": "magnetic_flux",
            "s_entropy": "entropy", "c_heat": "heat_capacity",
        }

    def resolve(self, word: str) -> Optional[DimensionedConcept]:
        """Resolve a word to a concept. Returns None if unknown."""
        w = word.lower().strip()
        if w in self.concepts:
            return self.concepts[w]
        if w in self.aliases:
            return self.concepts[self.aliases[w]]
        return None

    def find_by_dims(self, dims: List[int]) -> List[str]:
        """Find all concepts with matching dimensions."""
        return [name for name, c in self.concepts.items() if c.dimensions == dims]

    def chat(self, user_input: str) -> str:
        """Process user input and return a response."""
        text = user_input.lower().strip()

        # ── "what is X?" ──────────────────────────────────────────────────
        m = re.match(r"what is (.+)", text)
        if m:
            return self._what_is(m.group(1))

        # ── "what equals X?" ──────────────────────────────────────────────
        m = re.match(r"what equals (.+)", text)
        if m:
            return self._what_equals(m.group(1))

        # ── "does X = Y?" / "is X = Y?" / "does X equal Y?" ───────────────
        m = re.match(r"(?:does|is)\s+(.+?)\s+(?:=|equal)\s+(.+)", text)
        if m:
            return self._check_equation(m.group(1), m.group(2))

        # ── "what is X times Y?" / "X × Y" ────────────────────────────────
        m = re.match(r"what is (.+?)\s+(?:times|×|\*)\s+(.+)", text)
        if m:
            return self._compose(m.group(1), m.group(2), "multiply")

        # ── "what is X divided by Y?" / "X ÷ Y" ───────────────────────────
        m = re.match(r"what is (.+?)\s+(?:divided by|÷|/)\s+(.+)", text)
        if m:
            return self._compose(m.group(1), m.group(2), "divide")

        # ── "if X = Y, what is Z?" (puzzle) ───────────────────────────────
        m = re.match(r"if (.+?)\s+=\s+(.+?),\s+what is (.+)", text)
        if m:
            return self._puzzle(m.group(1), m.group(2), m.group(3))

        # ── "solve: X = Y" (check and explain) ────────────────────────────
        m = re.match(r"solve:\s*(.+?)\s+=\s+(.+)", text)
        if m:
            return self._solve(m.group(1), m.group(2))

        # ── "list" or "help" ──────────────────────────────────────────────
        if text in ("help", "?", "list", "vocabulary"):
            return self._help()

        # ── "body" — show body state ──────────────────────────────────────
        if text in ("body", "state", "memory"):
            return self._body_state()

        # ── Unknown ───────────────────────────────────────────────────────
        return (f"I don't understand '{user_input}'. Try:\n"
                f"  'what is energy'\n"
                f"  'does energy = mass times speed times speed'\n"
                f"  'what equals energy'\n"
                f"  'what is force times length'\n"
                f"  'if energy = mass times speed times speed, what is mass times speed times speed'\n"
                f"  'help'")

    def _what_is(self, expr: str) -> str:
        """Answer 'What is X?'"""
        # Try to parse as a composition (times)
        if " times " in expr or " × " in expr or " * " in expr:
            parts = re.split(r"\s+(?:times|×|\*)\s+", expr)
            if len(parts) >= 2:
                return self._compose(parts[0], " times ".join(parts[1:]), "multiply")

        # Try division
        if " divided by " in expr or " ÷ " in expr or " / " in expr:
            parts = re.split(r"\s+(?:divided by|÷|/)\s+", expr)
            if len(parts) == 2:
                return self._compose(parts[0], parts[1], "divide")

        concept = self.resolve(expr)
        if concept:
            return (f"{concept.name}: dimensions = [{dims_to_str(concept.dimensions)}]\n"
                    f"  = {dims_to_human(concept.dimensions)}\n"
                    f"  Golay syndrome: {GOLAY_ENGINE.syndrome_weight(concept.bits)}\n"
                    f"  Codeword: {'yes' if GOLAY_ENGINE.syndrome_weight(concept.bits) == 0 else 'no (snaps to nearest)'}")
        return f"I don't know the concept '{expr}'. Known concepts: {', '.join(sorted(self.concepts.keys()))}"

    def _what_equals(self, expr: str) -> str:
        """Answer 'What equals X?' — search for dimensional matches."""
        concept = self.resolve(expr)
        if not concept:
            return f"I don't know '{expr}'."

        matches = self.find_by_dims(concept.dimensions)
        matches = [m for m in matches if m != concept.name]

        if matches:
            return (f"Concepts with the same dimensions as {concept.name} [{dims_to_str(concept.dimensions)}]:\n"
                    f"  {', '.join(matches)}")
        return f"No other known concept has the same dimensions as {concept.name} [{dims_to_str(concept.dimensions)}]."

    def _check_equation(self, lhs_str: str, rhs_str: str) -> str:
        """Answer 'Does X = Y?'"""
        lhs = self._parse_expression(lhs_str)
        rhs = self._parse_expression(rhs_str)

        if lhs is None:
            return f"I don't understand '{lhs_str}'."
        if rhs is None:
            return f"I don't understand '{rhs_str}'."

        result = check_equation(lhs, rhs)

        if result["accepted"]:
            self.body_state.append(f"{lhs.name} = {rhs.name}")
            return (f"✓ YES. {lhs.name} = {rhs.name}\n"
                    f"  {lhs.name}: [{dims_to_str(lhs.dimensions)}]\n"
                    f"  {rhs.name}: [{dims_to_str(rhs.dimensions)}]\n"
                    f"  Dimensions match exactly. (Recorded to body state.)")
        else:
            self.anti_state.append(f"{lhs.name} ≠ {rhs.name}")
            mod2 = "would" if result["mod2_would_accept"] else "would not"
            return (f"✗ NO. {lhs.name} ≠ {rhs.name}\n"
                    f"  {lhs.name}: [{dims_to_str(lhs.dimensions)}]\n"
                    f"  {rhs.name}: [{dims_to_str(rhs.dimensions)}]\n"
                    f"  Dimensions don't match.\n"
                    f"  (Old mod-2 system {mod2} have accepted this — {'that was a false positive!' if result['mod2_would_accept'] else 'correctly rejected.'})")

    def _compose(self, a_str: str, b_str: str, operation: str) -> str:
        """Answer 'What is X times Y?'"""
        a = self._parse_expression(a_str)
        b = self._parse_expression(b_str)

        if a is None:
            return f"I don't understand '{a_str}'."
        if b is None:
            return f"I don't understand '{b_str}'."

        result = compose_concepts(a, b, operation)
        op_symbol = "×" if operation == "multiply" else "÷"
        op_word = "times" if operation == "multiply" else "divided by"

        # Find what this equals
        matches = self.find_by_dims(result.dimensions)
        match_str = ""
        if matches:
            match_str = f"\n  This equals: {', '.join(matches)}"

        return (f"{a.name} {op_symbol} {b.name} = {result.name}\n"
                f"  Dimensions: [{dims_to_str(result.dimensions)}]{match_str}")

    def _puzzle(self, lhs_str: str, rhs_str: str, question_str: str) -> str:
        """Solve: 'If X = Y, what is Z?'"""
        # First verify the equation
        lhs = self._parse_expression(lhs_str)
        rhs = self._parse_expression(rhs_str)

        eq_check = ""
        if lhs and rhs:
            result = check_equation(lhs, rhs)
            if result["accepted"]:
                eq_check = f"✓ Verified: {lhs.name} = {rhs.name}\n"
            else:
                eq_check = f"✗ The premise is false: {lhs.name} ≠ {rhs.name}\n"

        # Now answer the question
        answer = self._what_is(question_str)
        return eq_check + answer

    def _solve(self, lhs_str: str, rhs_str: str) -> str:
        """Solve: check an equation and explain."""
        return self._check_equation(lhs_str, rhs_str)

    def _parse_expression(self, expr: str) -> Optional[DimensionedConcept]:
        """Parse an expression that may be a single concept or a composition."""
        expr = expr.strip()

        # Check for composition (times, ×, *)
        parts = re.split(r"\s+(?:times|×|\*)\s+", expr)
        if len(parts) >= 2:
            result = self.resolve(parts[0])
            if result is None:
                return None
            for part in parts[1:]:
                next_concept = self.resolve(part)
                if next_concept is None:
                    return None
                result = compose_concepts(result, next_concept, "multiply")
            return result

        # Check for division (divided by, ÷, /)
        parts = re.split(r"\s+(?:divided by|÷|/)\s+", expr)
        if len(parts) == 2:
            a = self.resolve(parts[0])
            b = self.resolve(parts[1])
            if a and b:
                return compose_concepts(a, b, "divide")
            return None

        # Single concept
        return self.resolve(expr)

    def _help(self) -> str:
        return (f"GLM Chat — I know {len(self.concepts)} physics concepts.\n"
                f"\nConcepts: {', '.join(sorted(self.concepts.keys()))}\n"
                f"\nYou can ask:\n"
                f"  'what is energy'\n"
                f"  'what is mass times speed'\n"
                f"  'what is force times length'\n"
                f"  'does energy = mass times speed times speed'\n"
                f"  'does energy = mass times speed'\n"
                f"  'what equals energy'\n"
                f"  'what equals force times length'\n"
                f"  'if energy = mass times speed times speed, what is energy'\n"
                f"  'solve: power = energy divided by time'\n"
                f"  'body' (show what I've learned)\n"
                f"  'help'")

    def _body_state(self) -> str:
        lines = [f"Body state: {len(self.body_state)} accepted, {len(self.anti_state)} rejected"]
        if self.body_state:
            lines.append("\nAccepted equations:")
            for eq in self.body_state:
                lines.append(f"  ✓ {eq}")
        if self.anti_state:
            lines.append("\nRejected equations:")
            for eq in self.anti_state:
                lines.append(f"  ✗ {eq}")
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# RUN THE CHAT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70, flush=True)
    print("GLM Chat — Natural Language Interface", flush=True)
    print("=" * 70, flush=True)
    print()

    chat = GLMChat()

    # Simulate a conversation
    conversation = [
        "help",
        "what is energy",
        "what is mass times speed",
        "what equals momentum",
        "does energy = mass times speed times speed",
        "does energy = mass times speed",
        "does force = mass times acceleration",
        "what is force times length",
        "what equals energy",
        "does energy = force times length",
        "does energy = pressure times volume",
        "what is energy divided by time",
        "what equals power",
        "does power = energy divided by time",
        "does energy = mass times speed times speed times speed times speed",
        "if energy = mass times speed times speed, what is energy",
        "solve: action = energy times time",
        "body",
    ]

    for user_input in conversation:
        print(f"User: {user_input}")
        response = chat.chat(user_input)
        print(f"GLM:  {response}")
        print()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
GLM Learning — extract exact meanings from text and grow the CRG.

v2 — fixes:
  - Edge deduplication
  - Proper dimensional inference from definitions ("mass times speed squared")
  - More pattern matching ("per unit", "relates X to Y", "squared", "cubed")
  - Known-concept meaning stored separately from learned-concept meaning
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from fractions import Fraction as F


# ── Math words → multipliers ────────────────────────────────────────
MATH_WORDS = {
    "squared": 2, "square": 2, "²": 2,
    "cubed": 3, "cube": 3, "³": 3,
    "quadrupled": 4, "quartic": 4,
    "inverse": -1, "reciprocal": -1,
    "per": -1,  # "per unit time" = / time
    "inverse_square": -2,
}

# ── Operator words ──────────────────────────────────────────────────
OP_WORDS = {
    "times": "*",
    "multiplied": "*",
    "multiplied_by": "*",
    "divided": "/",
    "divided_by": "/",
    "over": "/",
    "plus": "+",
    "minus": "-",
}


class Learner:
    """
    Learns new concepts and relations from text.

    Usage:
        learner = Learner(reasoner)
        learner.ingest("Energy is mass times speed squared.")
        print(learner.known_concepts())
        print(learner.crg_edges())
    """

    def __init__(self, reasoner, state_path: Optional[Path] = None):
        self.reasoner = reasoner
        self.state_path = state_path

        # Learned state
        self._concepts: Dict[str, Dict] = {}   # name → {definition, meaning, source}
        self._edges: List[Dict] = []            # {src, label, dst, source}
        self._definitions: Dict[str, str] = {}  # name → definition text
        self._edge_set: Set[Tuple[str, str, str]] = set()  # for dedup

        # Load existing state
        if state_path and state_path.exists():
            self._load()

    def ingest(self, text: str) -> Dict[str, Any]:
        """
        Learn from text. Extracts definitions and relations.

        Returns: {definitions: [...], relations: [...], new_concepts: [...]}
        """
        results = {"definitions": [], "relations": [], "new_concepts": []}

        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        for sent in sentences:
            # Try relations FIRST (some patterns like "is proportional to"
            # look like definitions but are actually relations)
            rels = self._extract_relations(sent)
            is_relation = bool(rels)
            for src, label, dst in rels:
                key = (src, label, dst)
                if key not in self._edge_set:
                    self._edge_set.add(key)
                    edge = {"src": src, "label": label, "dst": dst, "source": "learned"}
                    self._edges.append(edge)
                    results["relations"].append(edge)

            # Try definitions: "X is Y" (but not if it was a relation)
            if not is_relation:
                defn = self._extract_definition(sent)
                if defn:
                    name, definition = defn
                    # Only learn if we don't already have a good meaning for this concept
                    if name not in self._concepts:
                        self._definitions[name] = definition
                        results["definitions"].append({"name": name, "definition": definition})

                        meaning = self._infer_meaning(definition)
                        if meaning:
                            self._concepts[name] = {
                                "definition": definition,
                                "meaning": meaning,
                                "source": "learned",
                            }
                            results["new_concepts"].append(name)

        return results

    # ── Extraction ──────────────────────────────────────────────────

    def _extract_definition(self, sent: str) -> Optional[Tuple[str, str]]:
        """Extract 'X is Y' definitions."""
        m = re.match(
            r'^(.+?)\s+(?:is|are|equals?|represents?)\s+(.+)$',
            sent, re.IGNORECASE
        )
        if m:
            name = m.group(1).strip().lower()
            definition = m.group(2).strip().rstrip(".")
            name = re.sub(r'^(the|a|an)\s+', '', name, flags=re.IGNORECASE)
            return name, definition
        return None

    def _extract_relations(self, sent: str) -> List[Tuple[str, str, str]]:
        """Extract relations from various sentence patterns."""
        relations = []
        sent_lower = sent.lower().strip()
        sent_clean = re.sub(r'^(the|a|an)\s+', '', sent_lower, flags=re.IGNORECASE)

        # Pattern 1: "X verb Y"
        m = re.match(
            r'^(.+?)\s+'
            r'(causes?|creates?|produces?|generates?|contains?|'
            r'includes?|measures?|describes?|defines?|determines?|'
            r'affects?|influences?|controls?|transforms?|converts?|'
            r'drives?|induces?|attracts?|repels?)\s+(.+)$',
            sent_clean, re.IGNORECASE
        )
        if m:
            src = self._clean_name(m.group(1))
            label = m.group(2).strip().lower()
            dst = self._clean_name(m.group(3))
            relations.append((src, label, dst))
            return relations

        # Pattern 2: "X relates Y to Z" / "X connects Y to Z"
        m = re.match(
            r'^(.+?)\s+(?:relates?|connects?|links?|binds?)\s+(.+?)\s+to\s+(.+)$',
            sent_clean, re.IGNORECASE
        )
        if m:
            src = self._clean_name(m.group(1))
            dst1 = self._clean_name(m.group(2))
            dst2 = self._clean_name(m.group(3))
            relations.append((dst1, "related_to", dst2))
            relations.append((src, "connects", dst1))
            relations.append((src, "connects", dst2))
            return relations

        # Pattern 3: "X is proportional to Y" / "X is inversely proportional to Y"
        m = re.match(
            r'^(.+?)\s+is\s+(inversely\s+)?proportional\s+to\s+(.+)$',
            sent_clean, re.IGNORECASE
        )
        if m:
            src = self._clean_name(m.group(1))
            inv = bool(m.group(2))
            dst = self._clean_name(m.group(3))
            label = "inversely_proportional" if inv else "proportional"
            relations.append((src, label, dst))
            return relations

        return relations

    def _clean_name(self, s: str) -> str:
        """Clean a concept name."""
        s = s.strip().lower()
        s = re.sub(r'^(the|a|an)\s+', '', s, flags=re.IGNORECASE)
        s = re.sub(r'[.?!]+$', '', s)
        return s

    # ── Dimensional inference ───────────────────────────────────────

    def _infer_meaning(self, definition: str) -> Optional[Dict]:
        """
        Infer a meaning by parsing the definition text.

        Handles:
          "mass times speed squared"  →  M × (LT⁻¹)²  =  L²MT⁻²
          "energy per unit time"      →  L²MT⁻² / T    =  L²MT⁻³
          "force divided by area"     →  LMT⁻² / L²    =  L⁻¹MT⁻²
        """
        tokens = self._tokenize(definition)
        if not tokens:
            return None

        # Parse the token list into a dimensional expression
        result = self._parse_product(tokens)
        if result is None:
            return None

        # Convert to meaning dict format
        axes = ["L", "M", "T", "I", "H", "N", "J", "A", "S", "B"]
        meaning = {
            "exponents": {axes[i]: str(result[i]) for i in range(10)},
            "scale": "0",
            "rank": 0,
            "parities": {"P": 0, "T": 0, "C": 0},
            "kind": 0,
            "domain": 0,
        }
        return meaning

    def _tokenize(self, text: str) -> List[Dict[str, Any]]:
        """
        Tokenize a definition into a sequence of typed tokens.

        Returns list of {type, value, exp_vector} dicts.
        """
        tokens = []
        words = text.lower().split()

        i = 0
        while i < len(words):
            word = re.sub(r'[^a-z²³]', '', words[i])

            # Math word (squared, cubed, per, inverse)
            if word in MATH_WORDS:
                tokens.append({"type": "math_op", "value": word, "mult": MATH_WORDS[word]})
                i += 1
                continue

            # Operator word (times, divided, over)
            if word in OP_WORDS:
                tokens.append({"type": "op", "value": OP_WORDS[word]})
                i += 1
                continue

            # "unit" in "per unit time" — skip
            if word == "unit":
                i += 1
                continue

            # Check if it's a known concept
            try:
                m = self.reasoner.meaning(self._resolve_name(word))
                axes = ["L", "M", "T", "I", "H", "N", "J", "A", "S", "B"]
                exp = tuple(F(m["exponents"][a]) for a in axes)
                tokens.append({"type": "concept", "value": word, "exp": exp})
                i += 1
                continue
            except Exception:
                pass

            # Check multi-word concepts (e.g., "speed of light")
            if i + 2 < len(words):
                for length in [3, 2]:
                    phrase = "_".join(words[i:i+length])
                    try:
                        m = self.reasoner.meaning(self._resolve_name(phrase))
                        axes = ["L", "M", "T", "I", "H", "N", "J", "A", "S", "B"]
                        exp = tuple(F(m["exponents"][a]) for a in axes)
                        tokens.append({"type": "concept", "value": phrase, "exp": exp})
                        i += length
                        break
                    except Exception:
                        continue
                else:
                    i += 1
                continue

            i += 1

        return tokens

    def _resolve_name(self, word: str) -> str:
        """Try common name variants."""
        # Try as-is first
        try:
            self.reasoner.meaning(word)
            return word
        except Exception:
            pass

        # Try singular (remove trailing 's')
        if word.endswith("s") and len(word) > 3:
            try:
                self.reasoner.meaning(word[:-1])
                return word[:-1]
            except Exception:
                pass

        # Try with underscores (multi-word)
        return word

    def _parse_product(self, tokens: List[Dict]) -> Optional[Tuple[F, ...]]:
        """
        Parse a token list as a product of dimensional quantities.

        Handles: "A times B squared" → A × B²
                 "A per unit B" → A / B
                 "A divided by B" → A / B
        """
        ZERO = tuple(F(0) for _ in range(10))
        current = list(ZERO)
        op = "*"

        # First pass: find all concepts with their effective exponents
        # (applying trailing "squared", "cubed" etc. to the preceding concept)
        effective = []  # list of (exponents, op_before)
        i = 0
        while i < len(tokens):
            tok = tokens[i]

            if tok["type"] == "concept":
                exp = list(tok["exp"])
                # Check if the NEXT token is a multiplier (squared, cubed)
                if i + 1 < len(tokens) and tokens[i+1]["type"] == "math_op":
                    mult = tokens[i+1]["mult"]
                    if mult > 0:  # squared, cubed etc.
                        exp = [e * F(mult) for e in exp]
                        i += 1  # skip the math_op token
                effective.append((exp, op))
                op = "*"  # reset after a concept

            elif tok["type"] == "op":
                op = tok["value"]

            elif tok["type"] == "math_op":
                mult = tok["mult"]
                if mult < 0:
                    # "per", "inverse" → next concept will be divided
                    op = "/"
                    if mult < -1:
                        # "inverse_square" — apply to next concept
                        pass  # handled when next concept is processed

            i += 1

        # Second pass: combine all effective exponents
        for exp, op_before in effective:
            if op_before == "*":
                current = [current[j] + exp[j] for j in range(10)]
            elif op_before == "/":
                current = [current[j] - exp[j] for j in range(10)]

        # Check if we actually found any concepts
        if all(v == F(0) for v in current):
            return None

        return tuple(current)

    # ── Query ───────────────────────────────────────────────────────

    def known_concepts(self) -> List[str]:
        return list(self._concepts.keys())

    def crg_edges(self) -> List[Dict]:
        return self._edges.copy()

    def get_definition(self, name: str) -> Optional[str]:
        return self._definitions.get(name)

    def get_concept_info(self, name: str) -> Optional[Dict]:
        return self._concepts.get(name)

    # ── Persistence ─────────────────────────────────────────────────

    def save(self):
        if not self.state_path:
            return
        state = {
            "concepts": self._concepts,
            "edges": self._edges,
            "definitions": self._definitions,
        }
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=2, default=str)

    def _load(self):
        try:
            with open(self.state_path) as f:
                state = json.load(f)
            self._concepts = state.get("concepts", {})
            self._edges = state.get("edges", [])
            self._definitions = state.get("definitions", {})
            # Rebuild dedup set
            self._edge_set = {
                (e["src"], e["label"], e["dst"]) for e in self._edges
            }
        except Exception:
            pass

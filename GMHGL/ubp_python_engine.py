"""
================================================================================
UBP PYTHON CODE ENGINE (UPCE) v2.2 - SELF-HEALING EDITION
================================================================================
Author: E R A Craig & UBP Research Cortex
Date: 10 April 2026
"""

import json
import math
import ast
import hashlib
import re
import io
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any

# UBP Core Imports
from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE, BinaryLinearAlgebra, SUBSTRATE

@dataclass
class PyLawResult:
    ubp_id: str
    lexicon: str
    resonance_score: float
    nrci: float
    tags: List[str]
    vector: List[int]

@dataclass
class CodeResult:
    code: str
    laws_used: List[str]
    nrci_avg: float
    dqi_avg: float
    passed_observer: bool

@dataclass
class ImprovementResult:
    improved_code: str
    issues_found: List[str]
    fixes_applied: List[str]
    nrci_before: float
    nrci_after: float

class PythonSemanticEngine:
    KEYWORD_MAP = {
        "addition": "LAW_PY_ADD", "subtraction": "LAW_PY_SUB",
        "subtracts": "LAW_PY_SUB", "subtract": "LAW_PY_SUB",
        "plus": "LAW_PY_ADD", "minus": "LAW_PY_SUB",
        "xor": "LAW_PY_DUNDER_XOR", "bitwise": "LAW_PY_DUNDER_XOR",
        "hamming": "LAW_PY_ALGO_HAMMING", "distance": "LAW_PY_ALGO_HAMMING",
        "vector": "LAW_PY_ALGO_HAMMING", "closest": "LAW_PY_ALGO_SEARCH",
        "match": "LAW_PY_ALGO_SEARCH", "search": "LAW_PY_ALGO_SEARCH",
        "def": "LAW_PY_DEF", "function": "LAW_PY_DEF", "create": "LAW_PY_DEF",
        "return": "LAW_PY_RETURN", "if": "LAW_PY_IF", "for": "LAW_PY_FOR",
        "print": "LAW_PY_PRINT", "list": "LAW_PY_LIST", "json": "LAW_PY_JSON",
        "from": "LAW_PY_FROM"
    }

    def __init__(self, kb_path: str = "ubp_python_kb.json"):
        self.kb = {}
        self._vectors = {}
        try:
            with open(kb_path, 'r') as f:
                data = json.load(f)
            fields = data["_fields"]
            f_idx = {name: i for i, name in enumerate(fields)}
            for fp, entry_list in data["entries"].items():
                uid = entry_list[f_idx["ubp_id"]]
                self.kb[uid] = {
                    "ubp_id": uid, 
                    "nrci_val": entry_list[f_idx["nrci_val"]], 
                    "lexicon": entry_list[f_idx["lexicon"]], 
                    "tags": entry_list[f_idx["tags"]]
                }
                v = entry_list[f_idx["vector"]]
                self._vectors[uid] = [(b * 2) - 1 for b in v]
        except Exception as e:
            print(f"[UPCE] KB Load Error: {e}")

    def _cosine(self, v1, v2):
        dot = sum(a * b for a, b in zip(v1, v2))
        m1, m2 = math.sqrt(sum(a**2 for a in v1)), math.sqrt(sum(b**2 for b in v2))
        return dot / (m1 * m2) if m1 * m2 > 0 else 0

    def query(self, text: str, top_k: int = 10):
        words = re.sub(r'[^a-z0-9_ ]', ' ', text.lower()).split()
        chord = [0.0] * 24
        for word in words:
            if word in self.KEYWORD_MAP:
                law_id = self.KEYWORD_MAP[word]
                if law_id in self._vectors:
                    weight = 5.0 if word in ["def", "xor", "subtracts", "hamming"] else 1.0
                    if word == "from" and ("subtract" in words): weight = 0.05
                    for j in range(24): chord[j] += self._vectors[law_id][j] * weight

        results = []
        for uid, vec in self._vectors.items():
            sim = self._cosine(chord, vec)
            if sim > 0.25:
                entry = self.kb[uid]
                results.append(PyLawResult(uid, entry["lexicon"], sim, float(entry["nrci_val"]), entry["tags"], vec))
        return sorted(results, key=lambda x: x.resonance_score, reverse=True)[:top_k]

class ObserverWall:
    @staticmethod
    def evaluate(law):
        soc = 2.0 / (1.0/max(1e-9, law.nrci) + 1.0/max(1e-9, law.resonance_score))
        return ("REALITY" if soc >= 0.6 else "ZOMBIE"), soc
    @staticmethod
    def filter_laws(laws):
        return [l for l in laws if ObserverWall.evaluate(l)[0] == "REALITY"]

class PythonCodeGenerator:
    def __init__(self, semantic_engine):
        self.engine = semantic_engine
        self.observer = ObserverWall()

    def _plan_script(self, intent: str) -> List[str]:
        plan = []
        intent_lower = intent.lower()
        if any(x in intent_lower for x in ["list", "data", "vector"]): plan.append("DATA_SETUP")
        if any(x in intent_lower for x in ["xor", "bitwise", "binary"]): plan.append("BITWISE")
        if any(x in intent_lower for x in ["subtract", "add", "sum"]): plan.append("ARITHMETIC")
        if any(x in intent_lower for x in ["print", "show", "display"]): plan.append("OUTPUT")
        return plan

    def generate(self, intent: str, verbose: bool = True) -> CodeResult:
        laws = self.engine.query(intent)
        stable_laws = self.observer.filter_laws(laws)
        code = self._synthesize(intent, stable_laws if stable_laws else laws)
        nrci_avg = sum(l.nrci for l in laws) / len(laws) if laws else 0
        dqi_avg = sum(self.observer.evaluate(l)[1] for l in laws) / len(laws) if laws else 0
        return CodeResult(code, [l.ubp_id for l in laws[:5]], nrci_avg, dqi_avg, len(stable_laws) > 0)

    def _synthesize(self, intent: str, laws: List[PyLawResult]) -> str:
        intent_lower = intent.lower()
        plan = self._plan_script(intent)
        nums = [int(n) for n in re.findall(r"\d+", intent)]
        snippets = []

        if "DATA_SETUP" in plan:
            if "vector" in intent_lower:
                snippets.append("    # Initialize 24-bit vectors\n    vectors = [[1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0], [0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0,1]]")
            else:
                snippets.append(f"    data = list(range(1, {nums[0] if nums else 6}))")

        if "BITWISE" in plan:
            snippets.append("    # Bitwise XOR Logic\n    res = vectors[0]\n    for v in vectors[1:]: res = [a ^ b for a, b in zip(res, v)]\n    val = res")
        elif "ARITHMETIC" in plan and len(nums) >= 2:
            a, b = (nums[1], nums[0]) if "from" in intent_lower else (nums[0], nums[1])
            op = "-" if "subtract" in intent_lower else "+"
            snippets.append(f"    val = {a} {op} {b}")

        if snippets:
            header = "def solve_intent():\n    \"\"\"Automatically authored by UPCE v2.2.\"\"\"\n"
            body = "\n".join(snippets)
            footer = "\n\n    return val\n\nresult = solve_intent()\nprint(f'Result: {result}')"
            return "# UBP Modular Composition\n" + header + body + footer

        return f"# Fallback\nprint('Primary Law: {laws[0].ubp_id if laws else 'CONCEPTUAL_RESONANCE'}')"

class PythonCodeImprover:
    def __init__(self):
        self.max_line_length = 100

    def calculate_nrci(self, code: str) -> float:
        if not code.strip(): return 0.0
        lines = code.split('\n')
        noise = sum(1 for l in lines if len(l) > self.max_line_length or l.endswith(' '))
        return max(0.1, 0.8 - (noise * 0.01))

    def improve(self, code: str, verbose: bool = True) -> ImprovementResult:
        if verbose: print(f"[UPCE Improver] Analyzing code ({len(code)} chars)...")
        issues, fixes = [], []
        nrci_before = self.calculate_nrci(code)

        lines = code.split('\n')
        new_lines = list(lines)

        # 1. Style Audit (Whitespace)
        for i, line in enumerate(new_lines):
            if line.endswith(' '):
                new_lines[i] = line.rstrip()
                if "Removed trailing whitespace" not in fixes:
                    fixes.append("Removed trailing whitespace")

        # 2. AST Audit & Precision Authoring
        try:
            tree = ast.parse("\n".join(new_lines))
            # Work backwards to maintain line indices
            nodes = sorted([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)], 
                           key=lambda x: x.lineno, reverse=True)

            for node in nodes:
                if not ast.get_docstring(node):
                    issues.append(f"STYLE: Function '{node.name}' missing docstring")

                    # LATTICE ALIGNMENT: Use the node's column offset + 4 spaces
                    indent = " " * (node.col_offset + 4)

                    # Insert the docstring on the line immediately following the 'def'
                    new_lines.insert(node.lineno, f'{indent}"""Automatically authored by UPCE v2.2."""')
                    fixes.append(f"Authored docstring for '{node.name}'")
        except Exception as e:
            issues.append(f"ERROR: AST Parse failed: {e}")

        improved_code = "\n".join(new_lines)
        nrci_after = self.calculate_nrci(improved_code)
        return ImprovementResult(improved_code, issues, fixes, nrci_before, nrci_after)

class UBPPythonEngine:
    def __init__(self, kb_path: str = "ubp_python_kb.json"):
        self.semantic = PythonSemanticEngine(kb_path)
        self.generator = PythonCodeGenerator(self.semantic)
        self.improver = PythonCodeImprover()

    def write(self, intent: str, verbose: bool = True):
        return self.generator.generate(intent, verbose=verbose)

    def improve(self, code: str, verbose: bool = True):
        return self.improver.improve(code, verbose=verbose)

if __name__ == "__main__":
    engine = UBPPythonEngine()
    print(engine.write("Subtract 103 from 206").code)

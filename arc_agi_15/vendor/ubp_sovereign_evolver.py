"""
================================================================================
UBP SOVEREIGN EVOLVER
================================================================================
Version: 2.1
Date: 16 April 2026
Author: E R A Craig, New Zealand & UBP Research Cortex v5.0

PHILOSOPHY: "Computational Sovereignty"
The Universal Binary Principle (UBP) posits that reality is a deterministic, 
error-corrected projection of a 24-bit substrate. Relying on external, C-based 
floating-point libraries (like Python's standard `math` module) introduces 
"Noumenal Leakage"—hardware-dependent artifacts and approximations that break 
topological continuity. To achieve true phase-lock, the system must compute 
itself. The Sovereign Evolver acts as an automated compiler, stripping away 
external dependencies and grounding all transcendental and trigonometric logic 
in the native `GrandUnifiedEmlALU` [eml(x,y) = exp(x) - ln(y)].

MECHANICS:
1. AST Parsing: Utilizes Python's Abstract Syntax Tree (`ast`) to deeply 
   understand code structure rather than relying on fragile text replacement.
2. The Bridge: Injects the `SovereignRealALU` wrapper into target scripts, 
   translating the ALU's native complex-plane outputs (a + bj) into real numbers.
3. Translation: Dynamically rewrites `math.sin` -> `alu.sin`, `math.pi` -> 
   `alu.PI`, and expands geometric helpers like `radians(x)`.
4. The Auditor: Calculates a "Sovereignty Index" (SI) and scans for forbidden 
   tensor libraries (e.g., `numpy`, `scipy`).
5. Non-Destructive: Intelligently preserves original module docstrings.
================================================================================
"""
import ast
import os
import argparse
from typing import List, Dict

# ---------------------------------------------------------
# TARGET CONFIGURATION: Add files here for batch processing
# ---------------------------------------------------------
DEFAULT_TARGETS = [
    "ubp_sovereign_evolver.py"
]

class SovereignTransformer(ast.NodeTransformer):
    def __init__(self):
        self.replacements = []
        self.forbidden_libs = []
        self.fixes_count = 0
        self.future_imports = []

    def visit_ImportFrom(self, node):
        # Extract __future__ imports to place them at the absolute top
        if node.module == '__future__':
            self.future_imports.append(ast.unparse(node))
            return None
        return node

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in ['numpy', 'scipy', 'pandas']:
                self.forbidden_libs.append(alias.name)
        
        new_names = [n for n in node.names if n.name != 'math']
        if len(new_names) < len(node.names):
            self.replacements.append("Purged: 'import math'")
            self.fixes_count += 1
            if not new_names: return None
            node.names = new_names
        return node

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == 'math':
            old_func = f"math.{node.attr}"
            self.fixes_count += 1
            node.value.id = 'alu'
            if node.attr == 'pi': node.attr = 'PI'
            if node.attr == 'e': node.attr = 'E'
            self.replacements.append(f"Redirected: {old_func} -> alu.{node.attr}")
        return node

def evolve_file(source_path):
    if not os.path.exists(source_path):
        return None
        
    output_path = source_path.replace(".py", "_sovereign.py")
    size_before = os.path.getsize(source_path)
    
    with open(source_path, 'r') as f:
        source = f.read()
    
    lines_before = len(source.splitlines())

    try:
        tree = ast.parse(source)
        
        # 1. Extract and preserve the original docstring
        docstring = ast.get_docstring(tree)
        if docstring and len(tree.body) > 0 and isinstance(tree.body[0], ast.Expr):
            tree.body.pop(0) # Remove it from the AST so it doesn't duplicate
            
        transformer = SovereignTransformer()
        new_tree = transformer.visit(tree)

        future_headers = "\n".join(transformer.future_imports) + "\n\n" if transformer.future_imports else ""

        # 2. Build the new non-destructive header
        new_doc = '"""\n'
        if docstring:
            new_doc += docstring + "\n\n"
        new_doc += f"--- SOVEREIGN EVOLVED SCRIPT ---\n"
        new_doc += f"Target: {os.path.basename(source_path)}\n"
        new_doc += "Dependency: GrandUnifiedEmlALU (Native 24-bit Logic)\n"
        new_doc += '"""\n'

        # 3. The ALU Bridge
        alu_bridge = (
            "from ubp_eml_alu_sovereign import GrandUnifiedEmlALU\n\n"
            "class SovereignRealALU(GrandUnifiedEmlALU):\n"
            "    def sin(self, x): return super().sin(x).real\n"
            "    def cos(self, x): return super().cos(x).real\n"
            "    def sqrt(self, x): return super().sqrt(x).real\n"
            "    def exp(self, x): return super().exp(x).real\n"
            "    def pow(self, x, y): return super().power(x, y).real\n"
            "    def log(self, x): return super().ln(x).real\n"
            "    def radians(self, x): return x * self.PI / 180.0\n"
            "    def degrees(self, x): return x * 180.0 / self.PI\n"
            "    def acos(self, x):\n"
            "        # Native EML Arc-Cosine: -i * ln(x + i * sqrt(1 - x^2))\n"
            "        c_val = x + 1j * super().sqrt(1.0 - x*x).real\n"
            "        return -super().ln(c_val).imag\n\n"
            "alu = SovereignRealALU()\n"
        )

        new_code = future_headers + new_doc + alu_bridge + ast.unparse(new_tree)
        
        with open(output_path, 'w') as f:
            f.write(new_code)
        
        size_after = os.path.getsize(output_path)
        lines_after = len(new_code.splitlines())
        
        si = 1.0 if transformer.fixes_count > 0 and not transformer.forbidden_libs else 0.5
        if not transformer.replacements: si = 0.0

        return {
            "file": source_path,
            "replacements": transformer.replacements,
            "leaks": transformer.forbidden_libs,
            "size_delta": size_after - size_before,
            "lines_delta": lines_after - lines_before,
            "sovereignty_index": si
        }
    except Exception as e:
        print(f"❌ Error parsing {source_path}: {e}")
        return None

def run_batch_evolution(targets: List[str]):
    print(f"\n{'═'*80}\nUBP SOVEREIGN COMPILER v2.1: BATCH AUDIT\n{'═'*80}")
    
    processed = 0
    for target in targets:
        report = evolve_file(target)
        if report:
            processed += 1
            print(f"\n📄 TARGET: {report['file']}")
            print(f"  ├─ Sovereignty Index: {report['sovereignty_index']:.2%}")
            print(f"  ├─ Size Change:       {report['size_delta']:+d} bytes")
            print(f"  ├─ Line Change:       {report['lines_delta']:+d} lines")
            
            if report['replacements']:
                print(f"  ├─ Improvements:")
                for r in report['replacements'][:5]:
                    print(f"  │  • {r}")
                if len(report['replacements']) > 5:
                    print(f"  │  • ... and {len(report['replacements'])-5} more.")
            else:
                print(f"  ├─ Status: Already Native or No Math Detected.")

            if report['leaks']:
                print(f"  ⚠  NOUMENAL LEAKAGE DETECTED: {', '.join(report['leaks'])}")
    
    if processed == 0:
        print("\n❌ No valid targets found. Check your filenames.")
    else:
        print(f"\n{'═'*80}\nBatch Complete. {processed} files audited.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UBP Sovereign Compiler v2.1")
    parser.add_argument("--target", type=str, help="A specific .py file to evolve")
    args = parser.parse_args()

    if args.target:
        run_batch_evolution([args.target])
    else:
        run_batch_evolution(DEFAULT_TARGETS)
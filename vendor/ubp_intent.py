"""
================================================================================
UBP INTENT RESOLVER v2.0 (The Executive Orchestrator)
================================================================================
Replaces the legacy Genesis Swarm, MoE Cortex, and Oracle Bridge.
Fuses the Two-Track Solve (Native/SymPy) with the GLM Cognitive Stack.

Author: UBP Research Cortex
Date: July 2026
================================================================================
"""
import json
import hashlib
import logging
import math
import re
import random
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple
from functools import reduce

# ─── UBP Core & Visualization ─────────────────────────────────────────────────
from ubp_observer_dynamics import ObserverDynamicsEngine
from ubp_viz import save_scene_3d
from GLM11_runtime import GLMRuntimeV37

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
log = logging.getLogger("UBP_Intent")

# ─── SymPy (Semantic Oracle Layer) ────────────────────────────────────────────
SYMPY_AVAILABLE = False
try:
    import sympy
    from sympy import (
        symbols, Symbol, sympify, simplify, factor, expand,
        diff, integrate, limit, series, solve, Eq, Function, Derivative,
        Matrix, det, Rational, pi as sp_pi, E as sp_E,
        sin, cos, tan, exp, log as sp_log, sqrt, oo, I as sp_I,
        gcd as sp_gcd, lcm as sp_lcm,
        summation, latex, N as sp_N, Abs, arg, conjugate,
        binomial as sp_binomial, factorial as sp_factorial,
        Poly, collect,
    )
    from sympy.parsing.sympy_parser import (
        parse_expr, standard_transformations,
        implicit_multiplication_application, convert_xor, function_exponentiation,
    )
    _TRANSFORMS = standard_transformations + (
        implicit_multiplication_application, convert_xor, function_exponentiation,
    )
    SYMPY_AVAILABLE = True
except ImportError:
    log.warning("SymPy not available — Oracle layer disabled")

# ─── UBP Core (Substrate Layer) ───────────────────────────────────────────────
UBP_CORE_AVAILABLE = False
try:
    from ubp_unified_v5 import GOLAY_ENGINE, LEECH_ENGINE
    UBP_CORE_AVAILABLE = True
except ImportError:
    class _StubGolay:
        def decode(self, v): return list(v), 0, 0
        def encode(self, v): return list(v[:24]) + [0]*(max(0, 24-len(v)))
    class _StubLeech:
        def calculate_symmetry_tax(self, v):
            hw = sum(v[:24])
            return Fraction(abs(hw - 12), 12)
    GOLAY_ENGINE = _StubGolay()
    LEECH_ENGINE = _StubLeech()

# ══════════════════════════════════════════════════════════════════════════════
# SUBSTRATE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def to_gray_code(n: int, bits: int = 24) -> list:
    gray = int(n) ^ (int(n) >> 1)
    return [(gray >> i) & 1 for i in range(bits - 1, -1, -1)]

def _golay_snap(v: List[int]) -> List[int]:
    decoded, _, _ = GOLAY_ENGINE.decode(v)
    return GOLAY_ENGINE.encode(decoded)

def _nrci_of(v: List[int]) -> float:
    tax = LEECH_ENGINE.calculate_symmetry_tax(v)
    return float(Fraction(10, 1) / (Fraction(10, 1) + tax))

def _fingerprint(val: Any) -> dict:
    CODEWORD_WEIGHTS = {0, 8, 12, 16, 24}
    try:
        n = abs(int(float(str(val)))) & 0xFFFFFF
        v = to_gray_code(n)
    except Exception:
        h = int(hashlib.sha256(str(val).encode()).hexdigest(), 16)
        v = [(h >> i) & 1 for i in range(23, -1, -1)]
    snapped = _golay_snap(v)
    nrci = _nrci_of(snapped)
    sw = sum(snapped)
    on_lattice = sw in CODEWORD_WEIGHTS
    return {
        "nrci": round(nrci, 4),
        "sw": sw,
        "on_lattice": on_lattice,
        "lattice": (
            "Identity"  if sw == 0  else
            "Octad"     if sw == 8  else
            "Dodecad"   if sw == 12 else
            "Hexadecad" if sw == 16 else
            "Universe"  if sw == 24 else
            "Off-lattice"
        ),
    }

def _vec_to_pos(v):
    if not v or len(v) != 24:
        return [0, 0, 0]
    x = (sum(v[0:8]) - 4) * 2.0
    y = (sum(v[8:16]) - 4) * 2.0
    z = (sum(v[16:24]) - 4) * 2.0
    return [x, y, z]

# ══════════════════════════════════════════════════════════════════════════════
# NATIVE MATH ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class NativeMathEngine:
    _MR_WITNESSES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]

    @staticmethod
    def gcd(a: int, b: int) -> int: return math.gcd(abs(a), abs(b))
    @staticmethod
    def lcm(a: int, b: int) -> int:
        return 0 if (a == 0 or b == 0) else abs(a * b) // math.gcd(abs(a), abs(b))

    @staticmethod
    def extended_gcd(a, b):
        if b == 0: return a, 1, 0
        g, x, y = NativeMathEngine.extended_gcd(b, a % b)
        return g, y, x - (a // b) * y

    @classmethod
    def is_prime(cls, n: int) -> bool:
        if n < 2: return False
        if n in (2, 3, 5, 7): return True
        if n % 2 == 0 or n % 3 == 0: return False
        r, d = 0, n - 1
        while d % 2 == 0: r += 1; d //= 2
        for a in cls._MR_WITNESSES:
            if a >= n: continue
            x = pow(a, d, n)
            if x in (1, n-1): continue
            for _ in range(r - 1):
                x = pow(x, 2, n)
                if x == n - 1: break
            else: return False
        return True

    @staticmethod
    def modinv(a, m):
        g, x, _ = NativeMathEngine.extended_gcd(a % m, m)
        return x % m if g == 1 else None

# ══════════════════════════════════════════════════════════════════════════════
# UBP POLYNOMIAL
# ══════════════════════════════════════════════════════════════════════════════

class UBPPolynomial:
    def __init__(self, coeffs: Dict[int, Any]):
        self.coeffs: Dict[int, Fraction] = {
            d: Fraction(c) for d, c in coeffs.items() if Fraction(c) != 0
        }

    @classmethod
    def from_string(cls, s: str, var: str = 'x') -> Optional['UBPPolynomial']:
        s = s.strip().replace('**', '^').replace('*', '')
        s = re.sub(r'\s*\+\s*', ' + ', s)
        s = re.sub(r'\s*-\s*', ' - ', s)
        s = s.strip()
        if s.startswith('- '): s = '-' + s[2:]

        terms = re.split(r'(?=[+-])', s)
        coeffs = {}

        for raw in terms:
            t = re.sub(r'([+-])\s+(\d)', r'\1\2', raw).strip()
            if not t: continue

            m = re.fullmatch(rf'([+-]?\d*\.?\d*/?\d*)\s*{re.escape(var)}\s*\^\s*([+-]?\d+)', t)
            if m:
                c_raw = m.group(1).strip()
                if not c_raw or c_raw == '+': c_raw = '1'
                elif c_raw == '-': c_raw = '-1'
                try:
                    c = Fraction(c_raw); d = int(m.group(2))
                    coeffs[d] = coeffs.get(d, Fraction(0)) + c
                    continue
                except Exception: pass

            m = re.fullmatch(rf'([+-]?\d*\.?\d*/?\d*)\s*{re.escape(var)}', t)
            if m:
                c_raw = m.group(1).strip()
                if not c_raw or c_raw == '+': c_raw = '1'
                elif c_raw == '-': c_raw = '-1'
                try:
                    c = Fraction(c_raw)
                    coeffs[1] = coeffs.get(1, Fraction(0)) + c
                    continue
                except Exception: pass

            try:
                coeffs[0] = coeffs.get(0, Fraction(0)) + Fraction(t.replace(' ', ''))
            except Exception:
                return None

        return cls(coeffs) if coeffs else None

    @property
    def degree(self): return max(self.coeffs) if self.coeffs else 0
    @property
    def constant_term(self): return self.coeffs.get(0, Fraction(0))

    def evaluate_exact(self, x: Fraction) -> Fraction:
        return sum(c * x**d for d, c in self.coeffs.items())

# ══════════════════════════════════════════════════════════════════════════════
# TOPOLOGICAL ALU & NATIVE SOLVER
# ══════════════════════════════════════════════════════════════════════════════

class TopologicalALU:
    def __init__(self):
        self._nm = NativeMathEngine()
        self._real_mode = UBP_CORE_AVAILABLE

    def _weight_search(self, v_super, c_range, target_weights) -> Optional[int]:
        if not self._real_mode: return None
        for c in c_range:
            vc = to_gray_code(c)
            op = [s ^ o for s, o in zip(v_super, vc)]
            snapped = _golay_snap(op)
            if sum(snapped) in target_weights:
                return c
        return None

    def solve_addition(self, a: int, b: int) -> Tuple[Optional[int], str]:
        if self._real_mode:
            va, vb = to_gray_code(a), to_gray_code(b)
            vs = [x^y for x,y in zip(va,vb)]
            c = self._weight_search(vs, range(abs(a+b-2), a+b+3), {0, 8})
            if c is not None: return c, "Topo-Golay"
        return a + b, "Topo-Arithmetic"

    def solve_gcd(self, a: int, b: int) -> Tuple[int, str]:
        g = math.gcd(abs(a), abs(b))
        fp = _fingerprint(g)
        return g, f"Topo-GCD (NRCI={fp['nrci']:.4f},{fp['lattice']})"

    def attempt_solve(self, directive: str) -> Tuple[Any, str]:
        low = directive.lower()
        nums = [int(x) for x in re.findall(r'\b(\d+)\b', low)]

        if len(nums) >= 2:
            a, b = nums[0], nums[1]
            if any(k in low for k in [' + ', 'add', 'sum of', 'plus']):
                r, m = self.solve_addition(a, b)
                if r is not None: return r, f"TopologicalALU Addition ({m})"
            if any(k in low for k in ['gcd', 'greatest common', 'hcf']):
                r, m = self.solve_gcd(a, b)
                return r, f"TopologicalALU GCD ({m})"
        return None, ""

class NativeDynamicSolver:
    def __init__(self):
        self.nm = NativeMathEngine()

    def solve(self, directive: str) -> Tuple[Any, str]:
        low = directive.lower()
        if any(k in low for k in ['gcd', 'greatest common divisor', 'hcf']):
            nums = [int(x) for x in re.findall(r'\b(\d+)\b', low)]
            if len(nums) >= 2: return self.nm.gcd(nums[0], nums[1]), "Native GCD"
        return None, "NATIVE_FAIL"

# ══════════════════════════════════════════════════════════════════════════════
# SYMPY ORACLE
# ══════════════════════════════════════════════════════════════════════════════

class SymPyOracle:
    def solve(self, directive: str) -> Tuple[Any, str]:
        if not SYMPY_AVAILABLE: return None, "SymPy Unavailable"
        try:
            clean = directive.replace('^', '**')
            clean = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', clean)
            
            if 'solve' in clean.lower() and '=' in clean:
                lhs, rhs = clean.split('=', 1)
                eq = Eq(parse_expr(lhs, transformations=_TRANSFORMS), 
                        parse_expr(rhs, transformations=_TRANSFORMS))
                ans = solve(eq)
                return ans, "SymPy Solve"
            
            expr = parse_expr(clean, transformations=_TRANSFORMS)
            if expr.is_number:
                return expr.evalf(), "SymPy Eval"
            return simplify(expr), "SymPy Simplify"
        except Exception as e:
            return None, f"SymPy Error: {e}"

    def verify(self, ans1: Any, ans2: Any) -> bool:
        if not SYMPY_AVAILABLE: return str(ans1) == str(ans2)
        try:
            e1 = sympify(str(ans1).replace('^', '**'))
            e2 = sympify(str(ans2).replace('^', '**'))
            return simplify(e1 - e2) == 0
        except:
            return str(ans1) == str(ans2)

# ══════════════════════════════════════════════════════════════════════════════
# KERNEL EXTRACTOR & VALIDATION BRIDGE
# ══════════════════════════════════════════════════════════════════════════════

class MathNetKernelExtractor:
    def extract(self, problem: str, answer: str) -> dict:
        nums = re.findall(r'\b(\d+)\b', answer)
        if nums and len(nums) == 1:
            return {
                "kernel_type": "numeric",
                "kernel": int(nums[0]),
                "ubp_directive": f"Calculate {nums[0]}",
                "key_nums": [int(n) for n in nums],
            }
        return {
            "kernel_type": "algebraic",
            "kernel": answer,
            "ubp_directive": answer,
            "key_nums": [int(n) for n in nums] if nums else [],
        }

class ValidationBridge:
    def __init__(self):
        self.t_alu  = TopologicalALU()
        self.native = NativeDynamicSolver()
        self.oracle = SymPyOracle()

    def solve(self, directive: str, expected: str = "") -> dict:
        ubp_ans, ubp_mode = self.t_alu.attempt_solve(directive)
        if ubp_ans is None:
            ubp_ans, ubp_mode = self.native.solve(directive)
            if ubp_mode == "NATIVE_FAIL":
                ubp_ans, ubp_mode = None, None

        oracle_ans, oracle_mode = self.oracle.solve(directive)

        ubp_ok    = ubp_ans is not None
        oracle_ok = oracle_ans is not None

        if ubp_ok and oracle_ok:
            agree = self.oracle.verify(ubp_ans, str(oracle_ans))
            agreement = "BOTH_AGREE" if agree else "CONFLICT"
        elif ubp_ok:
            agreement = "UBP_ONLY"
        elif oracle_ok:
            agreement = "ORACLE_ONLY"
        else:
            agreement = "NEITHER"

        canonical = oracle_ans if oracle_ok else ubp_ans

        fp = _fingerprint(canonical) if canonical is not None else \
             {"nrci": 0.0, "sw": 0, "on_lattice": False, "lattice": "Unknown"}

        return {
            "directive":    directive,
            "ubp_answer":   str(ubp_ans) if ubp_ans is not None else None,
            "oracle_answer": str(oracle_ans) if oracle_ans is not None else None,
            "agreement":    agreement,
            "canonical":    str(canonical) if canonical is not None else "UNRESOLVED",
            "fp_nrci":      fp["nrci"],
            "fp_lattice":   fp["lattice"],
        }

# ══════════════════════════════════════════════════════════════════════════════
# INTENT RESOLVER (The Executive Orchestrator)
# ══════════════════════════════════════════════════════════════════════════════

class UBPIntent:
    def __init__(self):
        log.info("Booting UBP Intent Resolver...")
        self.bridge = ValidationBridge()
        self.extractor = MathNetKernelExtractor()
        self.observer = ObserverDynamicsEngine()
        self.glm = GLMRuntimeV37(auto_expand=False)

    def resolve(self, directive: str, expected: str = "") -> dict:
        log.info(f"Resolving Intent: {directive[:80]}...")

        # 1. ORACLE TRACK: Extract Kernel & Solve
        kernel_data = self.extractor.extract(directive, expected)
        clean_directive = kernel_data.get("ubp_directive", directive)
        solve_data = self.bridge.solve(clean_directive, expected)
        
        answer = solve_data.get("canonical", "UNRESOLVED")
        agreement = solve_data.get("agreement", "NEITHER")
        nrci = solve_data.get("fp_nrci", 0.5)

        # 2. GLM TRACK: Semantic Resonance & Prose Generation
        # We use fresh=True to prevent cross-topic bleed from previous intents
        self.glm.reset_idea()
        prose_response = self.glm.chat_considered(directive, fresh=True)
        
        # Extract the active zone's centroid for spatial mapping
        active_zone = self.glm.manager.active
        zone_centroid = getattr(active_zone, 'centroid', [])
        if not zone_centroid:
            # Fallback to hashing the directive if GLM didn't form a centroid
            h = int(hashlib.sha256(directive.encode()).hexdigest(), 16)
            zone_centroid = [(h >> i) & 1 for i in range(23, -1, -1)]

        # 3. OBSERVER TRACK: Reality Audit
        read = self.observer.conscious_read(zone_centroid, Fraction(nrci).limit_denominator(1000000))

        # 4. VISUAL TRACK: Generate 3D Manifold
        self._generate_manifold(directive, answer, agreement, zone_centroid, active_zone)

        # 5. Compile Final Report
        result = {
            "directive": directive,
            "answer": answer,
            "consensus": agreement,
            "observer_status": read['status'],
            "lattice_state": solve_data.get("fp_lattice", "Unknown"),
            "glm_response": prose_response
        }
        
        self._print_report(result)
        return result

    def _generate_manifold(self, directive, answer, agreement, centroid, zone):
        """Generates a 3D scene representing the Intent resolution."""
        q_h = int(hashlib.sha256(directive.encode()).hexdigest(), 16)
        q_vec = [(q_h >> i) & 1 for i in range(23, -1, -1)]
        
        q_pos = _vec_to_pos(q_vec)
        r_pos = _vec_to_pos(centroid)

        # Use raw dictionaries for the visualizer
        spheres = [
            {"x": q_pos[0], "y": q_pos[1], "z": q_pos[2], "r": 0.6, "color": "#ff00ff", "label": "Intent (Query)"},
            {"x": r_pos[0], "y": r_pos[1], "z": r_pos[2], "r": 1.0, "color": "#00ffff", "label": f"Resolution: {answer}"}
        ]
        lines = [
            {"start": q_pos, "end": r_pos, "color": "#ffffff"}
        ]

        # Add GLM topic nouns as supporting nodes
        topic_nouns = getattr(zone, 'topic_nouns', [])
        for i, noun in enumerate(topic_nouns[:4]):
            entry = self.glm.vocab_dict.get(noun)
            if entry and hasattr(entry, 'vector'):
                n_pos = _vec_to_pos(entry.vector)
                spheres.append({"x": n_pos[0], "y": n_pos[1], "z": n_pos[2], "r": 0.4, "color": "#ffff00", "label": noun})
                lines.append({"start": r_pos, "end": n_pos, "color": "#ffff00"})

        scene = {"spheres": spheres, "lines": lines}
        save_scene_3d(scene)

    def _print_report(self, res: dict):
        print("\n" + "="*80)
        print(" UBP INTENT RESOLUTION")
        print("="*80)
        print(f" Directive : {res['directive']}")
        print(f" Answer    : {res['answer']} (Consensus: {res['consensus']})")
        print(f" Observer  : {res['observer_status']} | Lattice: {res['lattice_state']}")
        print("-" * 80)
        print(f" GLM Synthesis:\n\n{res['glm_response']}")
        print("="*80 + "\n")

if __name__ == "__main__":
    # Quick Test
    intent = UBPIntent()
    intent.resolve("Find the greatest common divisor of 252 and 198.")
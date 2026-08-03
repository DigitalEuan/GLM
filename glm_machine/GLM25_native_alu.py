# ══════════════════════════════════════════════════════════════════════════════
# §25  NATIVE ALU ADAPTER (v3.17.0 — Sovereign Computation Layer)
# ══════════════════════════════════════════════════════════════════════════════
#
# PURPOSE
#   Wire GLM09's compute layer to the *native* UBP engines (NoiseALU, ExactMath,
#   BinaryLinearAlgebra, PhysicsALU, LinearAlgebraALU, AdaptiveManifold) so that
#   every numeric computation runs through the substrate and produces a real
#   trace + fingerprint. SymPy is demoted to validation-only — when a SymPy
#   cross-check is requested, it runs *after* the native computation and the
#   two results are compared. Disagreements are recorded but never silently
#   override the native answer.
#
# ARCHITECTURE — the "sovereign computation" two-stage pattern (SESSION_SUMMARY §10):
#   Stage-1: an explicit, step-by-step native algorithm produces the answer.
#            NoiseALU already returns a `trace` (List[str]) per op.
#   Stage-2: `AdaptiveManifold.fingerprint(result)` classifies that answer
#            through the substrate (NRCI, lattice, Monster grade).
#
#   This module is the adapter that gives GLM09 a uniform API:
#       native_compute(kind, operands, **kwargs) -> NativeResult
#   where NativeResult carries: result, exact, approx, trace, fingerprint,
#   sympy_check (optional), elapsed_us.
#
# NON-GOALS
#   * Symbolic differentiation / integration / ODE / Taylor / limits — no
#     native equivalent exists. SymPy remains the *only* path for those, but
#     the result is still fingerprinted at the end. See `symbolic_with_fingerprint`.
#
# AUTHOR
#   Z.ai levelling-up pass — 2026-07-06
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import math
import time
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple, Union

# ── Native UBP engines ──────────────────────────────────────────────────────
try:
    from ubp_unified_v5 import (
        ExactMath, ExactRoot, BinaryLinearAlgebra,
        NoiseALU, PhysicsALU, LinearAlgebraALU,
        AdaptiveManifold, GOLAY_ENGINE,
    )
    _HAS_NATIVE = True
except Exception as _e:  # pragma: no cover — env without ubp_unified_v5
    _HAS_NATIVE = False
    _NATIVE_IMPORT_ERR = str(_e)

# ── SymPy (validation only) ─────────────────────────────────────────────────
try:
    import sympy as sp
    _HAS_SYMPY = True
except ImportError:
    _HAS_SYMPY = False


# ── Module-level singletons ─────────────────────────────────────────────────
# NoiseALU instantiation is non-trivial (it builds an AdaptiveManifold and a
# NeuralPatternDetector). Keep one alive for the lifetime of the module.
_NOISE_ALU: Optional[NoiseALU] = None
_PHYS_ALU: Optional[PhysicsALU] = None
_LIN_ALU: Optional[LinearAlgebraALU] = None
_MANIFOLD: Optional[AdaptiveManifold] = None


def _get_alus() -> Tuple[NoiseALU, PhysicsALU, LinearAlgebraALU, AdaptiveManifold]:
    """Lazily instantiate the ALU singletons. Idempotent."""
    global _NOISE_ALU, _PHYS_ALU, _LIN_ALU, _MANIFOLD
    if _NOISE_ALU is None:
        if not _HAS_NATIVE:
            raise RuntimeError(
                f"Native UBP engines not available: {_NATIVE_IMPORT_ERR!r}. "
                "Check that ubp_unified_v5.py is on sys.path."
            )
        _NOISE_ALU = NoiseALU(mode="SV")
        _PHYS_ALU = PhysicsALU(mode="SV")
        _LIN_ALU = LinearAlgebraALU(mode="SV")
        _MANIFOLD = AdaptiveManifold(max_bits=64)
    return _NOISE_ALU, _PHYS_ALU, _LIN_ALU, _MANIFOLD


# ══════════════════════════════════════════════════════════════════════════════
#  RESULT DATACLASS
# ══════════════════════════════════════════════════════════════════════════════
class NativeResult:
    """Uniform return shape for every native computation.

    Fields
    ------
    result : Any
        The native-computed result (int, float, Fraction, ExactRoot, tuple, ...).
    exact : str
        String form suitable for display ("6", "120", "13", "(3, 4, 5)").
    approx : float
        Float approximation for ranking / display.
    trace : List[str]
        Step-by-step execution log from the native algorithm.
    fingerprint : Dict[str, Any]
        Substrate classification (NRCI, lattice name, Monster grade, ...).
    sympy_check : Optional[Dict[str, Any]]
        If a SymPy validation was performed, holds {value, matches, error}.
    elapsed_us : int
        Microseconds spent in the native algorithm.
    operation : str
        Canonical operation name (e.g. "gcd", "is_prime", "det_nxn").
    """

    __slots__ = (
        "result", "exact", "approx", "trace", "fingerprint",
        "sympy_check", "elapsed_us", "operation",
    )

    def __init__(self, operation: str, result: Any, exact: str, approx: float,
                 trace: List[str], fingerprint: Dict[str, Any],
                 sympy_check: Optional[Dict[str, Any]] = None,
                 elapsed_us: int = 0):
        self.operation = operation
        self.result = result
        self.exact = exact
        self.approx = approx
        self.trace = trace
        self.fingerprint = fingerprint
        self.sympy_check = sympy_check
        self.elapsed_us = elapsed_us

    def to_dict(self) -> Dict[str, Any]:
        out = {
            "operation": self.operation,
            "result": self.result,
            "exact": self.exact,
            "approx": self.approx,
            "trace": self.trace,
            "fingerprint": self.fingerprint,
            "elapsed_us": self.elapsed_us,
        }
        if self.sympy_check is not None:
            out["sympy_check"] = self.sympy_check
        return out

    def __repr__(self) -> str:
        return (f"NativeResult(op={self.operation!r}, exact={self.exact!r}, "
                f"nrci={self.fingerprint.get('nrci')}, "
                f"lattice={self.fingerprint.get('lattice')!r}, "
                f"trace_steps={len(self.trace)})")


# ══════════════════════════════════════════════════════════════════════════════
#  SYMPY VALIDATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _sympy_validate_int(expected: int, expr: str) -> Optional[Dict[str, Any]]:
    """Cross-check an integer result against SymPy's evaluation of `expr`."""
    if not _HAS_SYMPY:
        return None
    try:
        sv = sp.sympify(expr)
        # SymPy's isqrt() returns a symbolic expression that needs .evalf()
        if not sv.is_integer and hasattr(sv, 'evalf'):
            ev = sv.evalf()
            if ev.is_integer:
                sv = int(ev)
        # Try direct integer conversion for Integer/Rational types
        if isinstance(sv, int):
            return {"value": sv, "matches": (sv == expected), "source_expr": expr}
        if hasattr(sv, 'is_integer') and sv.is_integer:
            sv_int = int(sv)
            return {"value": sv_int, "matches": (sv_int == expected), "source_expr": expr}
        # v3.19.0: Handle Float results that are actually integers
        # (e.g. Matrix([[1.0,2.0],...]).det() returns -3.00000000000000)
        if hasattr(sv, 'is_Float') and sv.is_Float:
            if sv == int(sv):
                sv_int = int(sv)
                return {"value": sv_int, "matches": (sv_int == expected), "source_expr": expr}
        # Try evalf and check if it's an integer-valued float
        if hasattr(sv, 'evalf'):
            ev = sv.evalf()
            try:
                ev_float = float(ev)
                if ev_float == int(ev_float) and abs(ev_float - expected) < 1e-9:
                    return {"value": int(ev_float), "matches": True, "source_expr": expr}
            except Exception:
                pass
        return {"value": None, "matches": False,
                "error": f"SymPy did not return an integer: {sv!r}"}
    except Exception as e:
        return {"value": None, "matches": False, "error": str(e)}


def _sympy_validate_float(expected: float, expr: str) -> Optional[Dict[str, Any]]:
    """Cross-check a float result against SymPy's evaluation of `expr`."""
    if not _HAS_SYMPY:
        return None
    try:
        sv = float(sp.sympify(expr).evalf())
        return {
            "value": sv,
            "matches": abs(sv - expected) < 1e-9,
            "source_expr": expr,
        }
    except Exception as e:
        return {"value": None, "matches": False, "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
#  FINGERPRINTING HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _fingerprint_of(value: Any) -> Dict[str, Any]:
    """Run AdaptiveManifold.fingerprint on a value, defensively."""
    try:
        _, _, _, manifold = _get_alus()
        return manifold.fingerprint(value)
    except Exception as e:
        return {"error": str(e)}


def _fingerprint_vector(vec: List[int]) -> Dict[str, Any]:
    """Fingerprint a 24-bit vector by converting to its hex int form.

    This is the canonical way the rest of the GLM fingerprints vectors —
    via `vector_to_hex_int` then through `AdaptiveManifold`.
    """
    try:
        n = 0
        for b in vec:
            n = (n << 1) | (1 if b else 0)
        return _fingerprint_of(n)
    except Exception as e:
        return {"error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
#  CORE: native_compute
# ══════════════════════════════════════════════════════════════════════════════
def native_compute(kind: str, operands: Any,
                   validate: bool = True, **kwargs) -> NativeResult:
    """Single entry point for every native numeric computation.

    Parameters
    ----------
    kind : str
        One of: gcd, lcm, factorial, isqrt, sqrt, is_prime, combination,
        permutation, modpow, add, sub, mul, divmod, dot_product,
        cross_product, vector_magnitude, det_2x2, det_3x3, det_nxn,
        matrix_trace, fibonacci, sum_series, mean, variance, stddev,
        extended_gcd, modular_inverse, crt_two, stirling2.
    operands : Any
        Operation-specific. Usually a tuple/list. For matrix ops, a 2D list.
    validate : bool
        If True (default) and SymPy is available, run a cross-check after the
        native computation and attach it as `sympy_check`.
    **kwargs
        Operation-specific extras (e.g. `population=True` for variance).

    Returns
    -------
    NativeResult
    """
    if not _HAS_NATIVE:
        raise RuntimeError("Native engines unavailable; cannot compute.")

    t0 = time.perf_counter()
    noise, phys, lin, _ = _get_alus()
    trace: List[str] = []
    fingerprint: Dict[str, Any] = {}
    result: Any = None
    exact: str = ""
    approx: float = 0.0
    sympy_expr: Optional[str] = None  # for cross-validation if available

    # ── Integer / number-theory ops ─────────────────────────────────────────
    if kind == "gcd":
        a, b = int(operands[0]), int(operands[1])
        r = noise.gcd(a, b)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = str(result); approx = float(result)
        sympy_expr = f"gcd({a},{b})"

    elif kind == "lcm":
        a, b = int(operands[0]), int(operands[1])
        r = noise.lcm(a, b)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = str(result); approx = float(result)
        sympy_expr = f"lcm({a},{b})"

    elif kind == "factorial":
        n = int(operands[0])
        r = noise.factorial(n)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = str(result); approx = float(result)
        sympy_expr = f"factorial({n})"

    elif kind == "isqrt":
        n = int(operands[0])
        r = noise.isqrt(n)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = str(result); approx = float(result)
        sympy_expr = f"isqrt({n})"

    elif kind == "sqrt":
        # Rational / float sqrt. Use ExactMath.sqrt_frac for the exact path,
        # fall through to float for non-rational inputs.
        x = operands[0]
        if isinstance(x, int) or isinstance(x, Fraction):
            f = Fraction(x) if isinstance(x, int) else x
            r = ExactMath.sqrt_frac(f, prec=30)
            result = r
            trace = [f"ExactMath.sqrt_frac({f}, prec=30)",
                     f"-> {r} (≈{float(r):.10f})"]
            fingerprint = _fingerprint_of(r)
            exact = str(r); approx = float(r)
            sympy_expr = f"sqrt({x})"
        else:
            # Float sqrt — keep as float but still fingerprint the rounded int
            xf = float(x)
            r = math.sqrt(xf)
            result = r
            trace = [f"math.sqrt({xf}) -> {r}"]
            fingerprint = _fingerprint_of(int(round(r * 1e6)))
            exact = repr(r); approx = r
            sympy_expr = f"sqrt({x})"

    elif kind == "is_prime":
        n = int(operands[0])
        r = noise.is_prime(n)
        result = bool(r.get("result", False))
        # NoiseALU.is_prime returns {result, nrci, pressure} — NOT the
        # standard _exec shape. We add a `lattice` field by fingerprinting
        # the input n itself through the manifold, so callers get a
        # uniform "nrci + lattice" fingerprint regardless of operation.
        input_fp = _fingerprint_of(n)
        trace = [f"NoiseALU.is_prime({n})",
                 f"  pressure={r.get('pressure')}",
                 f"  substrate_nrci={r.get('nrci')}",
                 f"  input_fingerprint: nrci={input_fp.get('nrci')} "
                 f"lattice={input_fp.get('lattice')!r}",
                 f"  -> {result}"]
        fingerprint = {
            "nrci": r.get("nrci"),
            "pressure": r.get("pressure"),
            "lattice": input_fp.get("lattice"),
            "input_nrci": input_fp.get("nrci"),
            "input_sw": input_fp.get("sw"),
        }
        exact = "True" if result else "False"
        approx = 1.0 if result else 0.0
        sympy_expr = f"isprime({n})"

    elif kind == "combination":
        n, k = int(operands[0]), int(operands[1])
        r = noise.choose(n, k)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = str(result); approx = float(result)
        sympy_expr = f"binomial({n},{k})"

    elif kind == "permutation":
        n, k = int(operands[0]), int(operands[1])
        r = noise.perm(n, k)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = str(result); approx = float(result)
        sympy_expr = f"ff({n},{k})"

    elif kind == "modpow":
        base, exp, mod = int(operands[0]), int(operands[1]), int(operands[2])
        r = noise.modpow(base, exp, mod)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = str(result); approx = float(result)
        sympy_expr = f"pow({base},{exp},{mod})"

    elif kind == "fibonacci":
        n = int(operands[0])
        r = noise.fibonacci(n)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = str(result); approx = float(result)

    elif kind == "sum_series":
        n = int(operands[0])
        r = noise.sum_series(n)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = str(result); approx = float(result)
        sympy_expr = f"summation(x,(x,1,{n}))"

    elif kind == "extended_gcd":
        a, b = int(operands[0]), int(operands[1])
        r = noise.extended_gcd(a, b)
        result = (r["result"][0], r["result"][1], r["result"][2])
        trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = f"({result[0]}, {result[1]}, {result[2]})"
        approx = float(result[0])

    elif kind == "modular_inverse":
        a, m = int(operands[0]), int(operands[1])
        r = noise.modular_inverse(a, m)
        result = r["result"]
        trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = str(result); approx = float(result) if result is not None else 0.0

    elif kind == "crt_two":
        r1, m1, r2, m2 = [int(x) for x in operands]
        r = noise.crt_two(r1, m1, r2, m2)
        result = r["result"]
        trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = str(result); approx = float(result[0]) if result else 0.0

    elif kind == "stirling2":
        n, k = int(operands[0]), int(operands[1])
        r = noise.stirling2(n, k)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = str(result); approx = float(result)

    # ── Basic arithmetic (add/sub/mul/divmod) ──────────────────────────────
    elif kind == "add":
        a, b = int(operands[0]), int(operands[1])
        r = noise.add(a, b)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = str(result); approx = float(result)
        sympy_expr = f"{a}+{b}"

    elif kind == "sub":
        a, b = int(operands[0]), int(operands[1])
        r = noise.sub(a, b)
        result = r["result"]
        trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        if result is None:  # underflow
            # Fallback to plain subtraction (the system should still answer)
            result = a - b
            trace.append(f"[fallback] sub underflow guard: {a} - {b} = {result}")
            fingerprint = _fingerprint_of(result)
        exact = str(result); approx = float(result)
        sympy_expr = f"{a}-{b}"

    elif kind == "mul":
        a, b = int(operands[0]), int(operands[1])
        r = noise.mul(a, b)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = str(result); approx = float(result)
        sympy_expr = f"{a}*{b}"

    elif kind == "divmod":
        a, b = int(operands[0]), int(operands[1])
        r = noise.divmod_(a, b)
        q, rem = r["result"]
        result = (q, rem)
        trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = f"({q}, {rem})"; approx = float(q)
        sympy_expr = f"div({a},{b})"

    elif kind == "power":
        # Native: only modular pow exists. For plain integer pow, use repeated
        # squaring via ExactMath (or built-in **). We fingerprint the result.
        base, exp = operands[0], operands[1]
        try:
            base_i, exp_i = int(base), int(exp)
            if exp_i < 0:
                raise ValueError("Negative exponent")
            result = base_i ** exp_i  # Python's long int pow is exact
            trace = [f"power({base_i}, {exp_i}) = {result}"]
            fingerprint = _fingerprint_of(result)
            exact = str(result); approx = float(result)
            sympy_expr = f"{base_i}**{exp_i}"
        except Exception:
            # Float power — fall back to math.pow, still fingerprint
            base_f, exp_f = float(base), float(exp)
            result = math.pow(base_f, exp_f)
            trace = [f"math.pow({base_f}, {exp_f}) = {result}"]
            fingerprint = _fingerprint_of(int(round(result * 1e6)))
            exact = repr(result); approx = result
            sympy_expr = f"{base}**{exp}"

    # ── Vector ops ─────────────────────────────────────────────────────────
    elif kind == "dot_product":
        v1, v2 = list(operands[0]), list(operands[1])
        r = noise.dot_product(v1, v2)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        # Result is a Fraction — keep both forms
        if isinstance(result, Fraction):
            exact = str(result); approx = float(result)
        else:
            exact = str(result); approx = float(result)

    elif kind == "cross_product":
        v1, v2 = list(operands[0]), list(operands[1])
        r = noise.cross_product(v1, v2)
        # Native returns a string "(cx, cy, cz)" — parse it back to a tuple
        raw = r["result"]
        if isinstance(raw, str):
            inner = raw.strip().strip("()").split(",")
            parsed = tuple(Fraction(s.strip()) for s in inner)
            result = parsed
        else:
            result = raw
        trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        exact = f"({', '.join(str(c) for c in result)})"
        approx = float(sum(float(c) ** 2 for c in result) ** 0.5)

    elif kind == "vector_magnitude":
        v = list(operands[0])
        r = noise.vector_magnitude(v)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        if isinstance(result, ExactRoot):
            exact = str(result); approx = float(result)
        else:
            exact = str(result); approx = float(result)

    # ── Matrix ops (LinearAlgebraALU + native trace/matrix_trace) ──────────
    elif kind == "det_2x2":
        m = operands[0]
        r = lin.det_2x2(m)
        result = r["result"]; fingerprint = r.get("fingerprint", {})
        # Add a manual trace (LinearAlgebraALU doesn't populate one)
        a, b, c, d = m[0][0], m[0][1], m[1][0], m[1][1]
        trace = [f"det_2x2: ad - bc = ({a})({d}) - ({b})({c}) = {result}"]
        exact = str(result); approx = float(result)
        sympy_expr = f"Matrix({m}).det()"

    elif kind == "det_3x3":
        m = operands[0]
        r = lin.det_3x3(m)
        result = r["result"]; fingerprint = r.get("fingerprint", {})
        trace = [f"det_3x3: Sarrus rule on {m} -> {result}"]
        exact = str(result); approx = float(result)
        sympy_expr = f"Matrix({m}).det()"

    elif kind == "det_nxn":
        m = operands[0]
        r = lin.det_nxn(m)
        result = r["result"]; fingerprint = r.get("fingerprint", {})
        trace = [f"det_nxn: Gaussian elimination with Fractions on {len(m)}x{len(m)} matrix",
                 f"-> {r.get('result_exact', result)}"]
        exact = r.get("result_exact", str(result)); approx = float(result)
        sympy_expr = f"Matrix({m}).det()"

    elif kind == "matrix_trace":
        # No native matrix-trace in LinearAlgebraALU — implement directly
        # (sum of diagonal). Still fingerprint the result.
        m = operands[0]
        n = len(m)
        diag = [m[i][i] for i in range(n)]
        s = sum(diag)
        result = s
        trace = [f"matrix_trace: diagonal = {diag}",
                 f"  sum = {s}"]
        fingerprint = _fingerprint_of(s)
        exact = str(s); approx = float(s)
        sympy_expr = f"Matrix({m}).trace()"

    elif kind == "eigenvalues":
        # No native eigenvalue solver. SymPy is the only path here.
        # Mark it clearly so callers know this is *not* a native computation.
        if not _HAS_SYMPY:
            raise RuntimeError("eigenvalues require SymPy (no native equivalent)")
        m = operands[0]
        sm = sp.Matrix(m)
        eigs = sm.eigenvals()
        out = {str(ev): int(mult) for ev, mult in eigs.items()}
        result = out
        trace = [f"[NON-NATIVE] SymPy Matrix({m}).eigenvals() -> {out}"]
        # Fingerprint the eigenvalue count + modulus sum as a proxy
        fp_input = sum(hash(ev) for ev in eigs.keys())
        fingerprint = _fingerprint_of(fp_input)
        exact = str(out); approx = 0.0
        # SymPy validation IS the computation here — mark accordingly
        validate = False

    # ── Statistics ─────────────────────────────────────────────────────────
    elif kind == "mean":
        data = list(operands[0])
        r = noise.mean(data)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        if isinstance(result, Fraction):
            exact = str(result); approx = float(result)
        else:
            exact = str(result); approx = float(result)

    elif kind == "variance":
        data = list(operands[0])
        pop = kwargs.get("population", True)
        r = noise.variance(data, population=pop)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        if isinstance(result, Fraction):
            exact = str(result); approx = float(result)
        else:
            exact = str(result); approx = float(result)

    elif kind == "stddev":
        data = list(operands[0])
        pop = kwargs.get("population", True)
        r = noise.stddev(data, population=pop)
        result = r["result"]; trace = r.get("trace", []); fingerprint = r.get("fingerprint", {})
        if isinstance(result, ExactRoot):
            exact = str(result); approx = float(result)
        else:
            exact = str(result); approx = float(result)

    else:
        raise ValueError(f"Unknown native_compute kind: {kind!r}")

    elapsed_us = int((time.perf_counter() - t0) * 1_000_000)

    # ── Optional SymPy validation ──────────────────────────────────────────
    sympy_check: Optional[Dict[str, Any]] = None
    if validate and sympy_expr is not None and _HAS_SYMPY:
        if isinstance(result, bool):
            # is_prime: use sympy.isprime (returns bool)
            try:
                import sympy
                # The expression is already in the form "isprime(n)"
                if sympy_expr.startswith("isprime("):
                    n_val = int(sympy_expr[len("isprime("):-1])
                    sv = bool(sympy.isprime(n_val))
                    sympy_check = {"value": sv, "matches": (sv == result),
                                   "source_expr": sympy_expr}
            except Exception as e:
                sympy_check = {"value": None, "matches": False, "error": str(e)}
        elif isinstance(result, int):
            sympy_check = _sympy_validate_int(result, sympy_expr)
        elif isinstance(result, float):
            sympy_check = _sympy_validate_float(result, sympy_expr)
        elif isinstance(result, Fraction):
            sympy_check = _sympy_validate_float(float(result), sympy_expr)
        # tuple / dict / ExactRoot results: skip validation (no clean SymPy form)

    return NativeResult(
        operation=kind,
        result=result,
        exact=exact,
        approx=approx,
        trace=trace,
        fingerprint=fingerprint,
        sympy_check=sympy_check,
        elapsed_us=elapsed_us,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  SYMBOLIC WITH FINGERPRINT (no native equivalent — SymPy is the engine,
#  but the result is still classified through the substrate)
# ══════════════════════════════════════════════════════════════════════════════
def symbolic_with_fingerprint(kind: str, expr: str, var: str = "x",
                              **kwargs) -> Dict[str, Any]:
    """Run a symbolic operation via SymPy, then fingerprint the result.

    This is the *explicit* admission that no native engine exists for
    differentiation, integration, ODE solving, Taylor series, limits, etc.
    SymPy is the compute path here; the substrate still classifies the answer.

    Parameters
    ----------
    kind : str
        One of: differentiate, integrate, simplify, solve, partial_diff,
        gradient, ode, taylor, limit, sum_series_symbolic.
    expr : str
        The expression / equation string.
    var : str
        The independent variable (or the partial-diff variable).
    **kwargs
        Operation-specific (e.g. `point="0"` for limit, `around=0` for taylor).

    Returns
    -------
    Dict with keys: operation, expr, var, result, exact, trace, fingerprint,
    sympy_check (None — SymPy IS the engine here), elapsed_us.
    """
    if not _HAS_SYMPY:
        return {"operation": kind, "expr": expr, "var": var,
                "result": None, "exact": "N/A", "trace": [],
                "fingerprint": {}, "sympy_check": None,
                "error": "SymPy not available for symbolic op",
                "elapsed_us": 0}

    t0 = time.perf_counter()
    trace: List[str] = []
    result: Any = None
    exact: str = "N/A"

    try:
        # Normalise the expression (turn ^ into **, 5x into 5*x)
        import re as _re
        clean = expr.replace('^', '**')
        clean = _re.sub(r'(\d)([a-zA-Z])', r'\1*\2', clean)

        x = sp.Symbol(var)

        if kind == "differentiate":
            result = sp.diff(sp.sympify(clean), x)
            trace.append(f"d/d{var}({clean})")
        elif kind == "integrate":
            result = sp.integrate(sp.sympify(clean), x)
            trace.append(f"∫({clean}) d{var}")
        elif kind == "simplify":
            result = sp.simplify(sp.sympify(clean))
            trace.append(f"simplify({clean})")
        elif kind == "solve":
            if '=' in clean:
                parts = clean.split('=')
                eq = sp.Eq(sp.sympify(parts[0]), sp.sympify(parts[1]))
                result = sp.solve(eq, x)
            else:
                result = sp.solve(sp.sympify(clean), x)
            trace.append(f"solve({clean}, {var})")
        elif kind == "partial_diff":
            v = sp.Symbol(var)
            result = sp.diff(sp.sympify(clean), v)
            trace.append(f"∂/∂{var}({clean})")
        elif kind == "gradient":
            e = sp.sympify(clean)
            free = sorted(e.free_symbols, key=lambda s: s.name)
            result = tuple(sp.diff(e, v) for v in free)
            trace.append(f"∇({clean}) over {free}")
        elif kind == "ode":
            x_sym = sp.Symbol('x')
            y = sp.Function('y')
            if '=' in clean:
                rhs_str = clean.split('=', 1)[1].strip()
            else:
                rhs_str = clean.strip()
            rhs_str = _re.sub(r'\by\b', 'y(x)', rhs_str)
            rhs = sp.sympify(rhs_str)
            eq = sp.Eq(sp.diff(y(x_sym), x_sym), rhs)
            result = sp.dsolve(eq, y(x_sym))
            trace.append(f"dsolve(y' = {rhs_str}, y(x))")
        elif kind == "taylor":
            around = int(kwargs.get("around", "0"))
            series_result = sp.series(sp.sympify(clean), x, around, n=5)
            try:
                result = series_result.removeO()
            except Exception:
                result = series_result
            trace.append(f"taylor({clean}, {var}, {around}, n=5)")
        elif kind == "limit":
            point_str = str(kwargs.get("point", "0")).strip().lower()
            if point_str in ("infinity", "inf", "oo"):
                pt = sp.oo
            else:
                try:
                    pt = int(point_str)
                except ValueError:
                    pt = sp.sympify(point_str)
            result = sp.limit(sp.sympify(clean), x, pt)
            trace.append(f"lim({clean}, {var} -> {pt})")
        elif kind == "sum_series_symbolic":
            result = sp.simplify(sp.sympify(clean))
            trace.append(f"simplify_sum({clean})")
        else:
            raise ValueError(f"Unknown symbolic kind: {kind!r}")

        exact = str(result)
        trace.append(f"-> {exact}")

        # Fingerprint the result. For non-numeric results (e.g. expressions),
        # hash the string form — the substrate still classifies it.
        if hasattr(result, 'evalf') and result.is_number:
            try:
                fp_input = Fraction(result.p, result.q) if hasattr(result, 'p') else float(result.evalf())
            except Exception:
                fp_input = hash(str(result))
        else:
            fp_input = hash(str(result))
        fingerprint = _fingerprint_of(fp_input)

    except Exception as e:
        result = None
        exact = f"Error: {e}"
        trace.append(f"[error] {e}")
        fingerprint = {"error": str(e)}

    elapsed_us = int((time.perf_counter() - t0) * 1_000_000)
    return {
        "operation": kind,
        "expr": expr,
        "var": var,
        "result": result,
        "exact": exact,
        "trace": trace,
        "fingerprint": fingerprint,
        "sympy_check": None,  # SymPy IS the engine — no separate check
        "elapsed_us": elapsed_us,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  STATUS / SELF-TEST
# ══════════════════════════════════════════════════════════════════════════════
def status() -> Dict[str, Any]:
    return {
        "module": "GLM25_native_alu",
        "version": "3.17.0",
        "native_available": _HAS_NATIVE,
        "sympy_available": _HAS_SYMPY,
        "native_operations": [
            "gcd", "lcm", "factorial", "isqrt", "sqrt", "is_prime",
            "combination", "permutation", "modpow", "add", "sub", "mul",
            "divmod", "power", "dot_product", "cross_product",
            "vector_magnitude", "det_2x2", "det_3x3", "det_nxn",
            "matrix_trace", "eigenvalues", "fibonacci", "sum_series",
            "extended_gcd", "modular_inverse", "crt_two", "stirling2",
            "mean", "variance", "stddev",
        ],
        "symbolic_operations": [
            "differentiate", "integrate", "simplify", "solve",
            "partial_diff", "gradient", "ode", "taylor", "limit",
            "sum_series_symbolic",
        ],
    }


if __name__ == "__main__":
    print("=== GLM25 Native ALU Adapter v3.17.0 — self-test ===")
    print(status())
    print()

    if not _HAS_NATIVE:
        print("NATIVE ENGINES UNAVAILABLE — cannot run demo.")
        raise SystemExit(1)

    demos = [
        ("gcd", (54, 24)),
        ("lcm", (12, 18)),
        ("factorial", (6,)),
        ("isqrt", (144,)),
        ("is_prime", (97,)),
        ("combination", (10, 3)),
        ("add", (123, 456)),
        ("mul", (7, 9)),
        ("det_3x3", ([[1, 2, 3], [4, 5, 6], [7, 8, 10]],)),
        ("matrix_trace", ([[1, 2, 3], [4, 5, 6], [7, 8, 10]],)),
        ("dot_product", ([3, -1, 4], [2, 5, -3])),
    ]
    for kind, ops in demos:
        r = native_compute(kind, ops, validate=True)
        sym = r.sympy_check or {}
        sym_str = (f"  sympy={sym.get('value')} matches={sym.get('matches')}"
                   if sym else "  [no sympy check]")
        print(f"  {kind:>18}({ops}) -> {r.exact}")
        print(f"     nrci={r.fingerprint.get('nrci')} "
              f"lattice={r.fingerprint.get('lattice')!r} "
              f"steps={len(r.trace)} us={r.elapsed_us}{sym_str}")
        for line in r.trace[:3]:
            print(f"     | {line}")
    print()

    # Symbolic demo (still goes through SymPy, but fingerprinted)
    print("--- symbolic_with_fingerprint demo ---")
    for kind, expr, var in [
        ("differentiate", "x**3 * sin(x)", "x"),
        ("integrate", "x**2", "x"),
        ("solve", "x**2 - 4 = 0", "x"),
    ]:
        r = symbolic_with_fingerprint(kind, expr, var)
        print(f"  {kind}({expr}) = {r['exact']}")
        print(f"     nrci={r['fingerprint'].get('nrci')} "
              f"lattice={r['fingerprint'].get('lattice')!r}")

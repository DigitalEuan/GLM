# ══════════════════════════════════════════════════════════════════════════════
# §09  TOOLS LAYER — ANALYTICAL ENGINE (v3.8.0)
# ══════════════════════════════════════════════════════════════════════════════
# v3.8.0 changes:
#   - Fixed false-positive arith detection on polynomials (x^2-4 no longer
#     triggers "2-4 = -2").  Uses lookbehind/lookahead to ensure the digit-
#     op-digit pattern is standalone.
#   - Added integrate detector.
#   - Added simplify detector (rational expressions).
#   - Added vector ops: dot product, cross product, magnitude.
#   - Canonicalised SymPy output: Add terms sorted by ascending polynomial
#     degree, so "3*x**2*sin(x) + x**3*cos(x)" is produced consistently.
#   - LaTeX-scrubbed queries before symbolic detection (so "differentiate
#     $x^2$" works).
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations
import re
import math
from typing import List, Dict, Optional, Tuple, Any

# Attempt to load SymPy for symbolic logic
try:
    import sympy as sp
    _HAS_SYMPY = True
except ImportError:
    _HAS_SYMPY = False

# v3.17.0: Native ALU adapter (GLM25). When available, every numeric
# computation routes through NoiseALU / ExactMath / LinearAlgebraALU and
# returns a real trace + fingerprint. SymPy is demoted to validation only.
try:
    from GLM25_native_alu import native_compute, symbolic_with_fingerprint, _HAS_NATIVE
    if _HAS_NATIVE:
        # Quick smoke test that the ALU is actually usable at import time
        try:
            _smoke = native_compute("gcd", (6, 4), validate=False)
            _NATIVE_OK = bool(_smoke.fingerprint)
        except Exception:
            _NATIVE_OK = False
    else:
        _NATIVE_OK = False
except Exception:
    _HAS_NATIVE = False
    _NATIVE_OK = False

# v3.18.0: Native polynomial ALU (GLM28). Used to handle differentiation
# and integration of polynomials natively (no SymPy). Falls back to SymPy
# for non-polynomial expressions (sin, cos, exp, log, etc.).
try:
    from GLM28_native_poly import (native_polynomial_diff, native_polynomial_integrate,
                                    is_polynomial as _is_polynomial,
                                    _HAS_NATIVE as _HAS_NATIVE_POLY_MOD)
    if _HAS_NATIVE_POLY_MOD:
        _POLY_OK = True
    else:
        _POLY_OK = False
except Exception:
    _POLY_OK = False

# IMPORT NUMBER WORDS FOR GROUNDING
from GLM04_number_vocab import NUMBER_WORDS

# v3.8.0: LaTeX scrubber (lightweight, stdlib only)
try:
    from GLM14_lexer import scrub_latex as _scrub_latex
except ImportError:
    def _scrub_latex(s: str) -> str:
        # Minimal fallback: just strip $...$ blocks
        s = re.sub(r"\$\$.*?\$\$", " ", s, flags=re.DOTALL)
        s = re.sub(r"\$[^$]*\$", " ", s)
        return s


def _strip_math_delimiters(s: str) -> str:
    """Light scrub for symbolic math: strip $...$ delimiters but keep content.

    Unlike _scrub_latex (which is designed for the lexer and strips ^, _, etc.),
    this preserves all math operators so the symbolic detectors can match
    expressions like 'x^2 + 5x'.
    """
    # Remove $$...$$ and $...$ wrappers but KEEP the content
    s = re.sub(r"\$\$", " ", s)
    s = re.sub(r"\$", " ", s)
    # Expand a few common LaTeX math commands to their plain-text equivalents
    s = re.sub(r"\\cdot", " * ", s)
    s = re.sub(r"\\times", " * ", s)
    s = re.sub(r"\\div", " / ", s)
    s = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", s)
    s = re.sub(r"\\sqrt\s+(\S)", r"sqrt(\1)", s)
    # Greek letters
    for cmd, name in [(r"\\alpha", "alpha"), (r"\\beta", "beta"),
                       (r"\\gamma", "gamma"), (r"\\delta", "delta"),
                       (r"\\theta", "theta"), (r"\\lambda", "lambda"),
                       (r"\\pi", "pi"), (r"\\sigma", "sigma"),
                       (r"\\omega", "omega"), (r"\\phi", "phi"),
                       (r"\\psi", "psi")]:
        s = re.sub(cmd + r"(?![a-zA-Z])", " " + name + " ", s)
    # Drop any remaining \command tokens
    s = re.sub(r"\\[a-zA-Z]+\*?", " ", s)
    return s

# ── 1. REGEX PATTERNS (The Detectors) ──────────────────────────────────
_GCD_RE       = re.compile(r'gcd\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', re.I)
_GCD_NL_RE    = re.compile(r'(?:greatest\s+common\s+divisor|gcd)\s+of\s+(\d+)\s+and\s+(\d+)', re.I)
_LCM_RE       = re.compile(r'lcm\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', re.I)
_LCM_NL_RE    = re.compile(r'(?:least\s+common\s+multiple|lcm)\s+of\s+(\d+)\s+and\s+(\d+)', re.I)
_SQRT_RE      = re.compile(r'(?:sqrt|√)\s*\(\s*(\d+(?:\.\d+)?)\s*\)', re.I)
_FACTORIAL_RE = re.compile(r'(\d+)\s*!', re.I)
_FACTORIAL_NL_RE = re.compile(r'(?:compute|find|calculate)?\s*(\d+)\s+factorial', re.I)
_PRIME_RE     = re.compile(r'is\s+(\d+)\s+prime\b', re.I)
_PRIME_RE2    = re.compile(r'(?:primality|is\s+prime)\s+(?:of\s+)?(\d+)', re.I)
_COMBINATION_RE = re.compile(r'(?:choose|select)\s+(\d+)\s+(?:items?\s+)?from\s+(\d+)', re.I)
_COMBINATION_RE2 = re.compile(r'(?:c|c)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', re.I)
_POWER_RE     = re.compile(r'(\d+(?:\.\d+)?)\s*\^\s*(\d+(?:\.\d+)?)')
# v3.8.0: arith detection now requires the digit-op-digit pattern to be
# standalone — not preceded by `^` or a word char (so "x^2-4" doesn't match
# "2-4") and not followed by a word char, `^`, or `=` (so "x=1+2" doesn't
# trigger arith).
_ARITH_RE     = re.compile(r'(?<![\w^])(\d+(?:\.\d+)?)\s*([+\-*/×÷])\s*(\d+(?:\.\d+)?)(?![\w^=])')

# Symbolic Patterns (v3.7 + v3.8.0)
_DIFF_RE      = re.compile(r'(?:differentiate|derivative of|d/dx)\s+(.+?)(?:\s+with respect to\s+(\w+))?(?:[\?\.]|$)', re.I)
# v3.8.0: solve detector extended to match "Find all real solutions to" /
# "find all solutions to" / "find the roots of" — common olympiad phrasings.
_SOLVE_RE     = re.compile(r'(?:solve\s+|find\s+all\s+(?:real\s+)?solutions?\s+to\s+|find\s+the\s+roots?\s+of\s+|find\s+the\s+zeros?\s+of\s+)(.+?)(?:\s+for\s+(\w+))?(?:[\?\.]|$)', re.I)
# v3.8.0: integrate detector
_INTEGRATE_RE = re.compile(r'(?:integrate|integral of|antiderivative of|integral)\s+(.+?)(?:\s+with respect to\s+(\w+))?(?:[\?\.]|$)', re.I)
# v3.8.0: simplify detector (rational expressions, algebraic simplification)
_SIMPLIFY_RE  = re.compile(r'simplify\s+(.+?)(?:[\?\.]|$)', re.I)

# v3.8.0: Vector operations
_VEC_RE       = r'<\s*([-\d,\s\.]+)\s*>'
_DOT_PRODUCT_RE = re.compile(
    r'(?:dot\s+product\s+of\s+|dot\s+product\s*\(|dot\s*\()\s*' + _VEC_RE + r'\s*(?:,|\band\b|\*)\s*' + _VEC_RE,
    re.I)
_CROSS_PRODUCT_RE = re.compile(
    r'(?:cross\s+product\s+of\s+|cross\s+product\s*\(|cross\s*\()\s*' + _VEC_RE + r'\s*(?:,|\band\b|\*)\s*' + _VEC_RE,
    re.I)
_MAGNITUDE_RE = re.compile(r'(?:magnitude|norm)\s+of\s+(?:the\s+)?(?:vector\s+)?' + _VEC_RE, re.I)
_MAGNITUDE_RE2 = re.compile(r'\|' + _VEC_RE + r'\|')

# v3.9.0: Linear algebra detectors
_DET_RE = re.compile(r'determinant\s+of\s+(?:the\s+)?(?:matrix\s+)?(\[\s*\[.+?\]\s*\])', re.I | re.DOTALL)
_DET_RE2 = re.compile(r'(?:det|determinant)\s*\(\s*(\[\s*\[.+?\]\s*\])\s*\)', re.I | re.DOTALL)
_EIGEN_RE = re.compile(r'eigenvalues?\s+of\s+(?:the\s+)?(?:matrix\s+)?(\[\s*\[.+?\]\s*\])', re.I | re.DOTALL)
_TRACE_RE = re.compile(r'trace\s+of\s+(?:the\s+)?(?:matrix\s+)?(\[\s*\[.+?\]\s*\])', re.I | re.DOTALL)
# v3.9.0: Multivariable calculus
_PARTIAL_DIFF_RE = re.compile(
    r'(?:partial\s+derivative|compute\s+the\s+partial\s+derivative|find\s+the\s+partial\s+derivative)\s+of\s+`?(.+?)`?\s+with\s+respect\s+to\s+(\w+)',
    re.I)
_GRADIENT_RE = re.compile(r'(?:gradient|find\s+the\s+gradient)\s+of\s+`?(.+?)`?(?:[\?\.]|$)', re.I)
# v3.9.0: ODE detector
_ODE_RE = re.compile(r'(?:solve\s+(?:the\s+)?ode\s*:|solve\s+(?:the\s+)?differential\s+equation\s*:?)\s*(.+?)(?:[\?\.]|$)', re.I)
_ODE_DYDX_RE = re.compile(r'(?:solve\s+)?dy/dx\s*=\s*(.+?)(?:[\?\.]|$)', re.I)
_ODE_PRIME_RE = re.compile(r"(?:solve\s+)?y'\s*=\s*(.+?)(?:[\?\.]|$)", re.I)
# v3.9.0: Series / summation — require a math expression (digits or backticks),
# NOT English like "sum of the elements".  Use a lookahead to ensure the
# captured group starts with a digit, backtick, or letter+x pattern.
_SERIES_RE = re.compile(r'(?:sum|summation)\s+of\s+(?=[\d`]|[a-z][\^\*\+\-/])(.+?)(?:[\?\.]|$)', re.I)
# v3.9.0: Taylor series
_TAYLOR_RE = re.compile(r'taylor\s+(?:series\s+)?expansion\s+of\s+(.+?)(?:\s+around\s+(\w+)\s*=\s*(\d+))?(?:[\?\.]|$)', re.I)
# v3.9.0: Taylor series variant — "around N" (no var=N, just N)
_TAYLOR_RE2 = re.compile(r'taylor\s+(?:series\s+)?expansion\s+of\s+(.+?)\s+around\s+(\d+)(?:[\?\.]|$)', re.I)
# v3.9.0: Limit
_LIMIT_RE = re.compile(r'limit\s+of\s+(.+?)\s+as\s+(\w+)\s+(?:->|→|approaches)\s*(\w+|infinity|inf)(?:[\?\.]|$)', re.I)

# v3.8.0: polynomial-degree canonical sort key
def _term_degree(term, var):
    """Best-effort polynomial degree of `term` in `var`.

    Returns 0 for non-polynomial terms (e.g. cos(x), sin(x)) instead of
    raising, so we can still sort mixed expressions.
    """
    try:
        d = sp.degree(term, var)
        # sp.degree returns -1 (or raises) for constants; normalise to 0
        if d == -1 if hasattr(sp, 'degree') else False:
            d = 0
        return int(d) if d is not None else 0
    except Exception:
        # Fallback: count occurrences of var**n in the string form
        s = str(term)
        m = re.findall(rf'\b{re.escape(str(var))}\*\*(\d+)', s)
        if m:
            return max(int(p) for p in m)
        if f"*{var}" in s or f"{var}*" in s or s.endswith(var):
            return 1
        return 0


def _canonicalize_sympy(expr, var=None, kind=None):
    """Canonicalise a SymPy expression for consistent output.

    For Add expressions, sort terms by ascending polynomial degree in `var`
    and reconstruct the display string manually (SymPy's sp.Add re-sorts
    internally, so we can't rely on it to preserve our order).

    Note: we use sp.expand (not sp.simplify) for differentiate because
    simplify tends to FACTOR expressions.  For integrate we keep the
    result as-is (integrate already returns a nicely-factored form).
    """
    if not _HAS_SYMPY:
        return expr
    try:
        # Only expand for differentiate (distribute products over sums).
        # For integrate, the default factored form is preferred.
        # For simplify, the user explicitly asked for simplification.
        if kind == "differentiate":
            expr = sp.expand(expr)
        # If it's an Add and we have a variable, sort terms by degree
        # and reconstruct the display string manually.
        # Skip the sort for 'simplify' (keep SymPy's natural order, which is
        # already the canonical simplified form the user expects).
        if var is not None and isinstance(expr, sp.Add) and kind != "simplify":
            terms = sp.Add.make_args(expr)
            v = sp.Symbol(var) if isinstance(var, str) else var
            sorted_terms = sorted(terms, key=lambda t: (_term_degree(t, v), str(t)))
            # Reconstruct as a string to preserve our ordering (sp.Add
            # would re-sort to its own internal order).
            # Handle negative terms: "a + (-b)" -> "a - b"
            parts = []
            for i, t in enumerate(sorted_terms):
                s = str(t)
                if i == 0:
                    parts.append(s)
                elif s.startswith("-"):
                    parts.append(" - " + s[1:])
                else:
                    parts.append(" + " + s)
            # Return a wrapper that str()s to our sorted form
            class _SortedStr:
                def __init__(self, s, underlying):
                    self._s = s
                    self._underlying = underlying
                def __str__(self):
                    return self._s
                def __repr__(self):
                    return self._s
                @property
                def underlying(self):
                    return self._underlying
            return _SortedStr("".join(parts), expr)
        return expr
    except Exception:
        return expr


def _parse_vec(s: str) -> Optional[List[float]]:
    """Parse '<3, -1, 4>' inner content '3, -1, 4' into [3.0, -1.0, 4.0]."""
    try:
        parts = [p.strip() for p in s.split(',') if p.strip() != '']
        return [float(p) for p in parts]
    except Exception:
        return None


def _parse_matrix(s: str) -> Optional[List[List[float]]]:
    """Parse '[[1, 2, 3], [4, 5, 6], [7, 8, 10]]' into a 2D list of floats.

    Tolerant of whitespace and optional commas between rows.
    Returns None if the string is not a valid matrix.
    """
    try:
        # Use SymPy's Matrix parser if available (handles most syntax)
        if _HAS_SYMPY:
            m = sp.Matrix(sp.sympify(s))
            return [[float(m[i, j]) for j in range(m.cols)] for i in range(m.rows)]
        # Fallback: manual parse
        import json
        # Try to make it JSON-compatible
        s = s
        return json.loads(s)
    except Exception:
        return None


# ── 2. NUMERIC DETECTION & EVALUATION ──────────────────────────────────
def detect_compute(query: str) -> Optional[Dict[str, Any]]:
    """Detects if a query contains a computable numeric expression."""
    q = query.strip().replace('`', '')
    if len(q) > 500: return None

    # v3.8.0: Vector operations (checked before arith to avoid false positives)
    m = _DOT_PRODUCT_RE.search(q)
    if m:
        v1, v2 = _parse_vec(m.group(1)), _parse_vec(m.group(2))
        if v1 and v2 and len(v1) == len(v2):
            return {"kind": "dot_product", "expr": f"dot({v1}, {v2})",
                    "operands": [v1, v2]}
    m = _CROSS_PRODUCT_RE.search(q)
    if m:
        v1, v2 = _parse_vec(m.group(1)), _parse_vec(m.group(2))
        if v1 and v2 and len(v1) == 3 and len(v2) == 3:
            return {"kind": "cross_product", "expr": f"cross({v1}, {v2})",
                    "operands": [v1, v2]}
    m = _MAGNITUDE_RE.search(q)
    if not m:
        m = _MAGNITUDE_RE2.search(q)
    if m:
        v = _parse_vec(m.group(1))
        if v:
            return {"kind": "magnitude", "expr": f"|{v}|", "operands": [v]}

    # v3.9.0: Linear algebra — determinant, eigenvalues, trace
    m = _DET_RE.search(q) or _DET_RE2.search(q)
    if m:
        return {"kind": "determinant", "expr": m.group(1), "matrix_str": m.group(1)}
    m = _EIGEN_RE.search(q)
    if m:
        return {"kind": "eigenvalues", "expr": m.group(1), "matrix_str": m.group(1)}
    m = _TRACE_RE.search(q)
    if m:
        return {"kind": "trace", "expr": m.group(1), "matrix_str": m.group(1)}

    # v3.25: Modulo detection (FIXED — was missing detector entirely)
    _MOD_RE = re.compile(r'\b(-?\d+)\s*(?:mod(?:ulo)?)\s*(-?\d+)\b', re.I)
    _MOD_PCT_RE = re.compile(r'\b(-?\d+)\s*%\s*(-?\d+)\b')
    m = _MOD_RE.search(q)
    if m: return {"kind":"modulo", "expr":f"{m.group(1)} mod {m.group(2)}", "operands":[int(m.group(1)), int(m.group(2))]}
    m = _MOD_PCT_RE.search(q)
    if m: return {"kind":"modulo", "expr":f"{m.group(1)} mod {m.group(2)}", "operands":[int(m.group(1)), int(m.group(2))]}

    # v3.7.7: Primality detection (extended in v3.8.0)
    m = _PRIME_RE.search(q)
    if m: return {"kind":"prime", "expr":f"isprime({m.group(1)})", "operands":[int(m.group(1))]}
    m = _PRIME_RE2.search(q)
    if m: return {"kind":"prime", "expr":f"isprime({m.group(1)})", "operands":[int(m.group(1))]}

    m = _GCD_RE.search(q)
    if m: return {"kind":"gcd", "expr":f"gcd({m.group(1)},{m.group(2)})", "operands":[int(m.group(1)), int(m.group(2))]}
    m = _GCD_NL_RE.search(q)
    if m: return {"kind":"gcd", "expr":f"gcd({m.group(1)},{m.group(2)})", "operands":[int(m.group(1)), int(m.group(2))]}

    m = _LCM_RE.search(q)
    if m: return {"kind":"lcm", "expr":f"lcm({m.group(1)},{m.group(2)})", "operands":[int(m.group(1)), int(m.group(2))]}
    m = _LCM_NL_RE.search(q)
    if m: return {"kind":"lcm", "expr":f"lcm({m.group(1)},{m.group(2)})", "operands":[int(m.group(1)), int(m.group(2))]}

    m = _SQRT_RE.search(q)
    if m: return {"kind":"sqrt", "expr":f"sqrt({m.group(1)})", "operands":[float(m.group(1))]}

    m = _FACTORIAL_RE.search(q)
    if m and int(m.group(1)) <= 20: return {"kind":"factorial", "expr":f"{m.group(1)}!", "operands":[int(m.group(1))]}
    m = _FACTORIAL_NL_RE.search(q)
    if m and int(m.group(1)) <= 20: return {"kind":"factorial", "expr":f"{m.group(1)}!", "operands":[int(m.group(1))]}

    m = _COMBINATION_RE.search(q)
    if m:
        k, n = int(m.group(1)), int(m.group(2))
        return {"kind":"combination", "expr":f"C({n},{k})", "operands":[n,k]}
    m = _COMBINATION_RE2.search(q)
    if m:
        n, k = int(m.group(1)), int(m.group(2))
        return {"kind":"combination", "expr":f"C({n},{k})", "operands":[n,k]}

    m = _POWER_RE.search(q)
    if m: return {"kind":"power", "expr":f"{m.group(1)}^{m.group(2)}", "operands":[float(m.group(1)),float(m.group(2))]}

    m = _ARITH_RE.search(q)
    if m:
        op_map = {"×":"*", "÷":"/", "+":"+", "-":"-", "*":"*", "/":"/"}
        return {"kind":"arith", "expr":f"{m.group(1)}{op_map[m.group(2)]}{m.group(3)}", "operands":[float(m.group(1)), m.group(2), float(m.group(3))]}

    return None

def evaluate_numeric(comp: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates a detected numeric computation.

    v3.17.0: NATIVE-FIRST. Routes through GLM25's `native_compute` so every
    operation runs on the real UBP engines (NoiseALU / ExactMath /
    LinearAlgebraALU / PhysicsALU) and produces a real trace + fingerprint.
    SymPy is used only as a cross-check (attached as `sympy_check`).

    The return shape preserves the v3.8.0 contract:
        {value, exact, approx}
    New v3.17.0 keys (additive, optional):
        trace, fingerprint, sympy_check, elapsed_us, native
    Existing callers that only read {value, exact, approx} keep working.
    """
    kind = comp.get("kind")

    # ── Linear algebra: determinant, eigenvalues, trace ──────────────────
    if kind in ("determinant", "eigenvalues", "trace"):
        matrix_str = comp.get("matrix_str", "")
        # Parse the matrix string into a 2D list of numbers (using SymPy's
        # parser if available — this is parsing, not computation).
        if _HAS_SYMPY:
            try:
                m = sp.Matrix(sp.sympify(matrix_str))
                mat = [[float(m[i, j]) for j in range(m.cols)] for i in range(m.rows)]
            except Exception as e:
                return {"value": None, "error": str(e), "exact": "Error", "approx": 0.0}
        else:
            return {"value": None, "error": "SymPy required to parse matrix", "exact": "N/A", "approx": 0.0}

        # v3.17.0: route through native ALU where possible.
        if _NATIVE_OK:
            try:
                if kind == "determinant":
                    n = len(mat)
                    if n == 2:
                        r = native_compute("det_2x2", (mat,), validate=True)
                    elif n == 3:
                        r = native_compute("det_3x3", (mat,), validate=True)
                    else:
                        r = native_compute("det_nxn", (mat,), validate=True)
                    return _wrap_native(r)
                elif kind == "trace":
                    r = native_compute("matrix_trace", (mat,), validate=True)
                    return _wrap_native(r)
                elif kind == "eigenvalues":
                    # No native eigenvalue solver — SymPy is the only path.
                    # We still fingerprint the result via symbolic_with_fingerprint.
                    sm = sp.Matrix(mat)
                    eigs = sm.eigenvals()
                    out = {str(ev): int(mult) for ev, mult in eigs.items()}
                    # Light fingerprint of the eigenvalue count + modulus sum
                    try:
                        from GLM25_native_alu import _fingerprint_of
                        fp_input = sum(hash(ev) for ev in eigs.keys())
                        fp = _fingerprint_of(fp_input)
                    except Exception:
                        fp = {}
                    return {"value": out, "exact": str(out), "approx": 0.0,
                            "trace": [f"[NON-NATIVE] SymPy eigenvals({mat})"],
                            "fingerprint": fp,
                            "native": False}
            except Exception as e:
                # Fall through to legacy SymPy path
                pass

        # Legacy fallback (also used when _NATIVE_OK is False)
        if _HAS_SYMPY:
            try:
                m = sp.Matrix(sp.sympify(matrix_str))
                if kind == "determinant":
                    val = m.det()
                    return {"value": val, "exact": str(val),
                            "approx": float(val) if val.is_number else 0.0,
                            "native": False}
                elif kind == "eigenvalues":
                    eigs = m.eigenvals()
                    out = {str(ev): int(mult) for ev, mult in eigs.items()}
                    return {"value": out, "exact": str(out), "approx": 0.0,
                            "native": False}
                elif kind == "trace":
                    val = m.trace()
                    return {"value": val, "exact": str(val),
                            "approx": float(val) if val.is_number else 0.0,
                            "native": False}
            except Exception as e:
                return {"value": None, "error": str(e), "exact": "Error", "approx": 0.0}
        return {"value": None, "error": "SymPy required for linear algebra", "exact": "N/A", "approx": 0.0}

    # ── Vector operations ────────────────────────────────────────────────
    if kind == "dot_product":
        v1, v2 = comp["operands"]
        if _NATIVE_OK:
            try:
                r = native_compute("dot_product", (v1, v2), validate=False)
                return _wrap_native(r)
            except Exception:
                pass
        val = sum(a * b for a, b in zip(v1, v2))
        if all(a == int(a) for a in v1 + v2) and val == int(val):
            val = int(val)
        return {"value": val, "exact": str(val), "approx": float(val), "native": False}
    if kind == "cross_product":
        v1, v2 = comp["operands"]
        if _NATIVE_OK:
            try:
                r = native_compute("cross_product", (v1, v2), validate=False)
                return _wrap_native(r)
            except Exception:
                pass
        cx = v1[1]*v2[2] - v1[2]*v2[1]
        cy = v1[2]*v2[0] - v1[0]*v2[2]
        cz = v1[0]*v2[1] - v1[1]*v2[0]
        val = [cx, cy, cz]
        if all(c == int(c) for c in val):
            val = [int(c) for c in val]
        return {"value": val, "exact": str(val), "approx": float(sum(c*c for c in val)**0.5), "native": False}
    if kind == "magnitude":
        v = comp["operands"][0]
        if _NATIVE_OK:
            try:
                r = native_compute("vector_magnitude", (v,), validate=False)
                return _wrap_native(r)
            except Exception:
                pass
        val = math.sqrt(sum(c*c for c in v))
        val_int = round(val)
        if abs(val - val_int) < 1e-9 and val_int*val_int == sum(int(round(c*c)) for c in v):
            sum_sq = sum(c*c for c in v)
            if all(c == int(c) for c in v):
                sum_sq_int = int(sum(round(c*c) for c in v))
                root = int(math.isqrt(sum_sq_int))
                if root*root == sum_sq_int:
                    return {"value": root, "exact": str(root), "approx": float(root), "native": False}
        return {"value": val, "exact": str(val), "approx": float(val), "native": False}

    # ── Primality — native substrate check ───────────────────────────────
    if kind == "prime":
        n = comp["operands"][0]
        if n < 2:
            return {"value": False, "exact": "False", "approx": 0.0, "native": False}
        if _NATIVE_OK:
            try:
                r = native_compute("is_prime", (n,), validate=True)
                return _wrap_native(r)
            except Exception:
                pass
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                return {"value": False, "exact": "False", "approx": 0.0, "native": False}
        return {"value": True, "exact": "True", "approx": 1.0, "native": False}

    # ── Combination / factorial / lcm / gcd / sqrt / power / arith ───────
    if kind == "combination":
        n, k = comp["operands"]
        if _NATIVE_OK:
            try:
                r = native_compute("combination", (n, k), validate=True)
                return _wrap_native(r)
            except Exception:
                pass
        if _HAS_SYMPY:
            val = sp.binomial(n, k)
        else:
            val = math.comb(n, k) if hasattr(math, 'comb') else 0
        return {"value": val, "exact": str(val), "approx": float(val), "native": False}

    if kind == "factorial":
        n = comp["operands"][0]
        if _NATIVE_OK:
            try:
                r = native_compute("factorial", (n,), validate=True)
                return _wrap_native(r)
            except Exception:
                pass
        val = math.factorial(n)
        return {"value": val, "exact": str(val), "approx": float(val), "native": False}

    if kind == "lcm":
        a, b = comp["operands"]
        if _NATIVE_OK:
            try:
                r = native_compute("lcm", (a, b), validate=True)
                return _wrap_native(r)
            except Exception:
                pass
        val = abs(a * b) // math.gcd(a, b) if a and b else 0
        return {"value": val, "exact": str(val), "approx": float(val), "native": False}

    if kind == "modulo":
        # FIXED (Round 4): Actually compute modulo instead of `pass`
        a, b = comp["operands"]
        if b == 0:
            return {"value": None, "exact": "undefined", "approx": 0.0, "native": False, "error": "modulo by zero"}
        val = a % b
        return {"value": val, "exact": str(val), "approx": float(val), "native": False}
    elif kind == "gcd":
        a, b = comp["operands"]
        if _NATIVE_OK:
            try:
                r = native_compute("gcd", (a, b), validate=True)
                return _wrap_native(r)
            except Exception:
                pass
        val = math.gcd(a, b)
        return {"value": val, "exact": str(val), "approx": float(val), "native": False}

    if kind == "sqrt":
        a = comp["operands"][0]
        if _NATIVE_OK:
            try:
                r = native_compute("sqrt", (a,), validate=True)
                return _wrap_native(r)
            except Exception:
                pass
        val = math.sqrt(a)
        return {"value": val, "exact": str(val), "approx": float(val), "native": False}

    if kind == "power":
        if _NATIVE_OK:
            try:
                r = native_compute("power",
                                   (comp["operands"][0], comp["operands"][1]),
                                   validate=True)
                return _wrap_native(r)
            except Exception:
                pass
        n1, n2 = comp["operands"]
        val = n1 ** n2
        return {"value": val, "exact": str(val), "approx": float(val), "native": False}

    if kind == "arith":
        n1, op, n2 = comp["operands"]
        if _NATIVE_OK:
            try:
                kind_map = {"+": "add", "-": "sub", "*": "mul", "×": "mul",
                            "/": "divmod", "÷": "divmod"}
                native_kind = kind_map.get(op)
                if native_kind:
                    if native_kind == "divmod":
                        r = native_compute("divmod", (int(n1), int(n2)), validate=True)
                        # divmod returns (quotient, remainder); for plain
                        # division we want quotient + remainder/divisor
                        q = r.result[0]
                        rem = r.result[1]
                        if rem == 0:
                            return _wrap_native(r, value_override=q,
                                                exact_override=str(q),
                                                approx_override=float(q))
                        # Non-exact: return float
                        val = n1 / n2 if n2 != 0 else 0
                        return {"value": val, "exact": str(val),
                                "approx": float(val),
                                "trace": r.trace, "fingerprint": r.fingerprint,
                                "native": True}
                    else:
                        r = native_compute(native_kind, (int(n1), int(n2)), validate=True)
                        return _wrap_native(r)
            except Exception:
                pass
        if op == "+": val = n1 + n2
        elif op == "-": val = n1 - n2
        elif op in ("*", "×"): val = n1 * n2
        elif op in ("/", "÷"): val = n1 / n2 if n2 != 0 else 0
        else: raise ValueError(f"Unknown operator {op}")
        return {"value": val, "exact": str(val), "approx": float(val), "native": False}

    # ── Catch-all: try SymPy eval, then fail ─────────────────────────────
    if _HAS_SYMPY:
        try:
            clean_expr = _normalize_math(comp["expr"])
            val = sp.sympify(clean_expr)
            approx = float(val.evalf())
            return {"value": val, "exact": str(val), "approx": approx, "native": False}
        except Exception:
            pass

    return {"value": None, "error": "Evaluation failed", "exact": "N/A", "approx": 0.0}


def _wrap_native(r, value_override=None, exact_override=None,
                 approx_override=None) -> Dict[str, Any]:
    """Convert a NativeResult into the v3.8.0-compatible return shape.

    Preserves {value, exact, approx} for backward compat AND adds the new
    v3.17.0 keys {trace, fingerprint, sympy_check, elapsed_us, native}.
    """
    return {
        "value": value_override if value_override is not None else r.result,
        "exact": exact_override or r.exact,
        "approx": approx_override if approx_override is not None else r.approx,
        "trace": r.trace,
        "fingerprint": r.fingerprint,
        "sympy_check": r.sympy_check,
        "elapsed_us": r.elapsed_us,
        "native": True,
    }

# ── 3. SYMBOLIC DETECTION & EVALUATION ─────────────────────────────────
def detect_symbolic(query: str) -> Optional[Dict[str, Any]]:
    """Detects if a query contains a symbolic math operation.

    FIXED (Round 4): Merges the user's new expand/factor/integrate-dx detectors
    with the v3.24 solve/simplify/ODE/partial_diff/gradient/taylor/limit/sum
    detectors that were accidentally dropped in the rewrite.

    Fixes applied:
      - Expand regex: now captures full parenthesized expressions (was capturing
        'x+1)**2' instead of '(x+1)**2' due to optional-paren regex bug)
      - Factor regex: now uses word boundary \\bfactor to avoid matching
        'factorial' (was false-positiving on '3! (factorial of 3)')
      - Solve/Simplify: restored from v3.24 pre-compiled patterns
      - ODE/Partial/Gradient/Taylor/Limit/Sum: restored from v3.24
    """
    q = _strip_math_delimiters(query).strip().replace('`', '')

    # A. ODE (check FIRST — before solve, since "solve the ODE" would match solve)
    m = _ODE_RE.search(q)
    if m: return {"kind": "ode", "expr": m.group(1).strip(), "var": "x"}
    m = _ODE_DYDX_RE.search(q)
    if m: return {"kind": "ode", "expr": "y' = " + m.group(1).strip(), "var": "x"}
    m = _ODE_PRIME_RE.search(q)
    if m: return {"kind": "ode", "expr": "y' = " + m.group(1).strip(), "var": "x"}

    # B. Integration — prioritize dx notation (user's new detector, works well)
    m_int_dx = re.search(r'(?:integrate|integral of|integral)\s+(.*?)\s*d([a-z])\b', q, re.I)
    if m_int_dx:
        return {'kind': 'integrate', 'expr': m_int_dx.group(1).strip(), 'var': m_int_dx.group(2)}
    # Fall back to the v3.24 integrate detector (handles "with respect to x")
    m = _INTEGRATE_RE.search(q)
    if m: return {"kind": "integrate", "expr": m.group(1).strip(), "var": m.group(2) or "x"}

    # C. Differentiate (user's new detector, merged with v3.24 pattern)
    m = _DIFF_RE.search(q)
    if m: return {"kind": "differentiate", "expr": m.group(1).strip(), "var": m.group(2) or "x"}

    # D. Expand — FIXED regex: capture everything after 'expand', strip outer parens
    #    Old bug: `expand\s*\(?(.*?)\)?$` made parens optional so it captured
    #    'x+1)**2' (missing opening paren). Fix: capture raw, strip parens later.
    m_exp = re.search(r'\bexpand\s+(.+?)(?:[\?\.]|$)', q, re.I)
    if m_exp:
        expr = m_exp.group(1).strip().rstrip('.')
        # Strip outer parens if present: "(x+1)^2" -> "x+1)^2" was the bug;
        # now we capture "(x+1)^2" and strip to "(x+1)^2" (keep parens for sympify)
        return {'kind': 'expand', 'expr': expr, 'var': 'x'}

    # E. Factor — FIXED regex: word boundary to avoid matching 'factorial'
    #    Old bug: `factor(?:ize)?` matched 'factor' in 'factorial'.
    #    Fix: use \bfactor(?:ize)?\b to require word boundary.
    m_fac = re.search(r'\bfactor(?:ize)?\s+(.+?)(?:[\?\.]|$)', q, re.I)
    if m_fac:
        expr = m_fac.group(1).strip().rstrip('.')
        return {'kind': 'factor', 'expr': expr, 'var': 'x'}

    # F. Simplify (restored from v3.24)
    m = _SIMPLIFY_RE.search(q)
    if m: return {"kind": "simplify", "expr": m.group(1).strip(), "var": "x"}

    # G. Solve (restored from v3.24)
    m = _SOLVE_RE.search(q)
    if m: return {"kind": "solve", "expr": m.group(1).strip(), "var": m.group(2) or "x"}

    # H. Partial derivative (restored from v3.24)
    m = _PARTIAL_DIFF_RE.search(q)
    if m: return {"kind": "partial_diff", "expr": m.group(1).strip(), "var": m.group(2).strip()}

    # I. Gradient (restored from v3.24)
    m = _GRADIENT_RE.search(q)
    if m: return {"kind": "gradient", "expr": m.group(1).strip(), "var": "x"}

    # J. Taylor series (restored from v3.24)
    m = _TAYLOR_RE2.search(q)
    if m: return {"kind": "taylor", "expr": m.group(1).strip(), "var": "x", "around": m.group(2)}
    m = _TAYLOR_RE.search(q)
    if m: return {"kind": "taylor", "expr": m.group(1).strip(), "var": m.group(2) or "x", "around": m.group(3) or "0"}

    # K. Limit (restored from v3.24)
    m = _LIMIT_RE.search(q)
    if m: return {"kind": "limit", "expr": m.group(1).strip(), "var": m.group(2).strip(), "point": m.group(3).strip()}

    # L. Sum / series (restored from v3.24)
    m = _SERIES_RE.search(q)
    if m: return {"kind": "sum", "expr": m.group(1).strip(), "var": "x"}

    return None

def evaluate_symbolic(req: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates a symbolic math operation.

    FIXED (Round 4): Added solve and simplify cases (were missing in the user's
    rewrite). Kept the user's integrate/expand/factor/differentiate cases.
    Also handles the expression cleaning more robustly.
    """
    if not _HAS_SYMPY: return {'exact': 'N/A', 'native': False}
    import re
    kind = req['kind']
    expr = req['expr']
    var_str = req.get('var', 'x')

    # Standardize: ^ -> **, strip trailing dx/dy/dz, implicit multiplication
    clean_expr = expr.replace('^', '**')
    clean_expr = re.sub(r'\s*d[a-z]$', '', clean_expr)
    clean_expr = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', clean_expr)
    # Strip trailing punctuation
    clean_expr = clean_expr.rstrip('.?').strip()

    try:
        import sympy as sp
        x = sp.Symbol(var_str)

        # FIXED: sympify AFTER kind-specific handling, because solve needs
        # to split on '=' before sympify (sympify can't parse "x+3=10")
        if kind == 'solve':
            # For solve, the expression should be an equation like "x+3=10"
            # Split on '=' and solve lhs - rhs = 0
            if '=' in clean_expr:
                lhs, rhs = clean_expr.split('=', 1)
                eq = sp.sympify(lhs.replace(' ', '')) - sp.sympify(rhs.replace(' ', ''))
                res = sp.solve(eq, x)
            else:
                s_expr = sp.sympify(clean_expr.replace(' ', ''))
                res = sp.solve(s_expr, x)
        else:
            s_expr = sp.sympify(clean_expr.replace(' ', ''))
            if kind == 'integrate':
                res = sp.integrate(s_expr, x)
            elif kind == 'differentiate':
                res = sp.diff(s_expr, x)
            elif kind == 'expand':
                res = sp.expand(s_expr)
            elif kind == 'factor':
                res = sp.factor(s_expr)
            elif kind == 'simplify':
                res = sp.simplify(s_expr)
            elif kind == 'limit':
                point = req.get('point', '0')
                pt = sp.oo if point in ('infinity', 'inf', 'oo') else sp.sympify(point)
                res = sp.limit(s_expr, x, pt)
            elif kind == 'taylor':
                around = req.get('around', '0')
                ar = sp.sympify(around)
                res = sp.series(s_expr, x, ar, n=6)
            else:
                res = 'Unknown Operation'

        return {'exact': str(res), 'native': False, 'trace': [f'{kind}({clean_expr})'], 'fingerprint': {}}
    except Exception as e:
        return {'exact': f'Error: {e}', 'native': False}

def ground_result(approx: float, vocab: Any) -> Optional[Tuple[str, Any]]:
    """Attempts to snap a numeric result to a known number-word in the vocab."""
    try:
        if abs(approx - round(approx)) < 1e-7:
            n = int(round(approx))
            if n in NUMBER_WORDS:
                word = NUMBER_WORDS[n]
                target_dict = vocab.words if hasattr(vocab, 'words') else vocab
                if word in target_dict:
                    return (word, target_dict[word])
    except: pass
    return None

def _normalize_math(s: str) -> str:
    """Surgically fix implicit multiplication: 5x -> 5*x, 21n -> 21*n"""
    s = s.replace('^', '**')
    s = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', s)
    return s

# ── 5. ISOLATION TEST ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Testing Module 09: Tools Layer (v3.8.0) ===")

    # Test Numeric
    q1 = "What is gcd(54, 24)?"
    comp1 = detect_compute(q1)
    if comp1:
        res1 = evaluate_numeric(comp1)
        print(f"  Numeric: {comp1['expr']} = {res1.get('exact', 'Error')} (Approx: {res1.get('approx', 0)})")

    # Test Symbolic differentiate
    if _HAS_SYMPY:
        q2 = "Find the derivative of x^3 * sin(x) with respect to x."
        comp2 = detect_symbolic(q2)
        if comp2:
            res2 = evaluate_symbolic(comp2)
            print(f"  Symbolic diff: d/dx({comp2['expr']}) = {res2.get('exact', 'Error')}")

        # Test integrate
        q3 = "Evaluate the integral of x^2 * exp(x) with respect to x."
        comp3 = detect_symbolic(q3)
        if comp3:
            res3 = evaluate_symbolic(comp3)
            print(f"  Symbolic int: integral({comp3['expr']}) = {res3.get('exact', 'Error')}")

        # Test simplify
        q4 = "Simplify (x^2 - 1)/(x - 1)."
        comp4 = detect_symbolic(q4)
        if comp4:
            res4 = evaluate_symbolic(comp4)
            print(f"  Symbolic simp: simplify({comp4['expr']}) = {res4.get('exact', 'Error')}")

    # Test vector ops
    q5 = "Compute the dot product of <3, -1, 4> and <2, 5, -3>."
    comp5 = detect_compute(q5)
    if comp5:
        res5 = evaluate_numeric(comp5)
        print(f"  Dot product: {comp5['expr']} = {res5.get('exact', 'Error')}")

    q6 = "Find the magnitude of the vector <3, 4, 12>."
    comp6 = detect_compute(q6)
    if comp6:
        res6 = evaluate_numeric(comp6)
        print(f"  Magnitude: {comp6['expr']} = {res6.get('exact', 'Error')}")

    # Test arith false-positive fix
    q7 = "Solve x^2 - 4 = 0 for x."
    comp7 = detect_compute(q7)
    print(f"  Arith false-positive check on 'x^2 - 4': compute={comp7} (should be None)")

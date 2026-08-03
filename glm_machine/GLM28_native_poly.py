# ══════════════════════════════════════════════════════════════════════════════
# §28  NATIVE POLYNOMIAL ALU (v3.18.0 — symbolic ops on polynomials, natively)
# ══════════════════════════════════════════════════════════════════════════════
#
# PURPOSE
#   Close the last gap in the "native-first" promise. SESSION_SUMMARY §10
#   identified that symbolic differentiation/integration have NO native UBP
#   equivalent — SymPy is the only engine. The user's request was "all
#   computation/calculation should always be UBP native where possible".
#
#   This module implements POLYNOMIAL differentiation and integration
#   natively, with full step-by-step traces and substrate fingerprints.
#   Polynomials are the common case in GLM's golden-case mathnet suite
#   (differentiate x^3*sin(x) needs Symbolic; but differentiate x^3 or
#   3*x^2 + 2*x - 5 can be done natively, term by term).
#
#   For non-polynomial expressions (sin, cos, exp, log), we still fall
#   back to SymPy via GLM25.symbolic_with_fingerprint — but we annotate
#   the trace with "[NON-NATIVE]" so callers know.
#
# ARCHITECTURE
#   - Polynomial is represented as a dict {exponent: Fraction coefficient}.
#     e.g. 3*x^2 + 2*x - 5 → {2: 3, 1: 2, 0: -5}
#   - Differentiation: d/dx[c*x^n] = (c*n)*x^(n-1). Term-by-term, exact.
#   - Integration: ∫c*x^n dx = (c/(n+1))*x^(n+1). Term-by-term, exact.
#     Constant of integration C is appended (default 0).
#   - Sum, product, power of polynomials: closed-form, exact.
#   - The result is fingerprinted via AdaptiveManifold.
#
# AUTHOR
#   Z.ai levelling-up pass — 2026-07-06 (v3.18 push)
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import re
import time
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple, Union

# ── Native UBP engines ──────────────────────────────────────────────────────
try:
    from ubp_unified_v5 import AdaptiveManifold, ExactMath
    _HAS_NATIVE = True
except Exception as _e:
    _HAS_NATIVE = False
    _NATIVE_IMPORT_ERR = str(_e)

# ── SymPy (for non-polynomial fallback) ─────────────────────────────────────
try:
    import sympy as sp
    _HAS_SYMPY = True
except ImportError:
    _HAS_SYMPY = False


_MANIFOLD: Optional[AdaptiveManifold] = None


def _get_manifold() -> AdaptiveManifold:
    global _MANIFOLD
    if _MANIFOLD is None:
        if not _HAS_NATIVE:
            raise RuntimeError(f"Native engines unavailable: {_NATIVE_IMPORT_ERR!r}")
        _MANIFOLD = AdaptiveManifold(max_bits=64)
    return _MANIFOLD


# ══════════════════════════════════════════════════════════════════════════════
#  POLYNOMIAL CLASS — native, exact, Fraction-based
# ══════════════════════════════════════════════════════════════════════════════
class Polynomial:
    """A native polynomial in one variable, exact arithmetic.

    Internal representation: dict {exponent (int): coefficient (Fraction)}.
    Zero coefficients are pruned.

    Examples:
        Polynomial.from_str("3*x^2 + 2*x - 5")
        Polynomial({2: Fraction(3), 1: Fraction(2), 0: Fraction(-5)})
        Polynomial.constant(7)
        Polynomial.monomial(3, 2)  # 3*x^2
    """

    __slots__ = ("terms", "var")

    def __init__(self, terms: Dict[int, Fraction], var: str = "x"):
        # Prune zero coefficients
        self.terms = {e: c for e, c in terms.items() if c != 0}
        self.var = var

    # ── Constructors ─────────────────────────────────────────────────────
    @classmethod
    def constant(cls, c: Union[int, Fraction], var: str = "x") -> "Polynomial":
        if c == 0:
            return cls({}, var)
        return cls({0: Fraction(c)}, var)

    @classmethod
    def monomial(cls, coeff: Union[int, Fraction], exp: int,
                 var: str = "x") -> "Polynomial":
        if coeff == 0 or exp < 0:
            return cls({}, var)
        return cls({exp: Fraction(coeff)}, var)

    @classmethod
    def from_str(cls, expr: str, var: str = "x") -> Optional["Polynomial"]:
        """Parse a polynomial string. Returns None if not a polynomial.

        Supports: 3*x^2 + 2*x - 5, x^3, 2x, x, 7, -x^2+1
        Does NOT support: sin(x), exp(x), 1/x, x**y (variable exp)
        """
        if not expr:
            return None
        # Normalise: lowercase var, ** -> ^, remove spaces
        s = expr.strip().replace("**", "^").replace(" ", "")
        # Reject if contains non-polynomial tokens
        # (letters other than the var, or 1/x, etc.)
        for ch in s:
            if ch.isalpha() and ch != var:
                return None  # contains another variable or function
        if "/" in s:
            # Could be rational coefficient (3/2) or 1/x. Only allow if
            # it's not 1/x form.
            if re.search(r'\bx/?\b', s) or "/x" in s or "x/" in s:
                return None
        # Replace implicit multiplication: 2x -> 2*x
        s = re.sub(rf'(\d)({var})', r'\1*\2', s)
        # Now parse term by term
        terms: Dict[int, Fraction] = {}
        # Split on + and - (keeping the sign)
        # Insert a + at the start if not present
        if not s.startswith("-"):
            s = "+" + s
        # Find terms: each starts with [+-] and goes until the next [+-]
        # (but only if the next +/- isn't inside an exponent like x^(-2))
        # Simple approach: use a regex that captures signed terms.
        term_pattern = re.compile(rf'([+-])(\d*[\./\d]*)(\*?{var}\^?(-?\d+))?')
        # Actually, let's use a more careful approach with sympy just for parsing
        if _HAS_SYMPY:
            try:
                sym = sp.sympify(s)
                x = sp.Symbol(var)
                # Check it's a polynomial in `var`
                if not sym.is_polynomial(x):
                    return None
                poly = sp.Poly(sym, x)
                terms = {}
                for monom, coeff in poly.terms():
                    # monom is a tuple like (3,) for x^3
                    e = monom[0]
                    if coeff.denominator == 1:
                        terms[e] = Fraction(int(coeff))
                    else:
                        terms[e] = Fraction(coeff.p, coeff.q)
                return cls(terms, var)
            except Exception:
                return None
        else:
            # No SymPy — do a manual parse. Limited but works for simple cases.
            # This is a fallback; not as robust.
            try:
                # Use a state-machine parse
                pos = 0
                while pos < len(s):
                    sign = 1
                    if s[pos] == '+':
                        pos += 1
                    elif s[pos] == '-':
                        sign = -1
                        pos += 1
                    # Read coefficient
                    coeff_match = re.match(r'\d+(/\d+)?', s[pos:])
                    if coeff_match:
                        coeff_str = coeff_match.group(0)
                        if '/' in coeff_str:
                            num, den = coeff_str.split('/')
                            coeff = Fraction(int(num), int(den))
                        else:
                            coeff = Fraction(int(coeff_str))
                        pos += len(coeff_str)
                    else:
                        coeff = Fraction(1)
                    # Optional * var
                    if pos < len(s) and s[pos] == '*':
                        pos += 1
                    # Optional var^exp or var
                    exp = 0
                    if pos < len(s) and s[pos] == var:
                        pos += 1
                        if pos < len(s) and s[pos] == '^':
                            pos += 1
                            exp_match = re.match(r'-?\d+', s[pos:])
                            if exp_match:
                                exp = int(exp_match.group(0))
                                pos += len(exp_match.group(0))
                            else:
                                return None
                        else:
                            exp = 1
                    terms[exp] = terms.get(exp, Fraction(0)) + sign * coeff
                return cls(terms, var)
            except Exception:
                return None

    # ── Properties ───────────────────────────────────────────────────────
    @property
    def degree(self) -> int:
        return max(self.terms.keys()) if self.terms else -1

    @property
    def is_zero(self) -> bool:
        return not self.terms

    @property
    def is_constant(self) -> bool:
        return all(e == 0 for e in self.terms.keys())

    # ── Arithmetic ───────────────────────────────────────────────────────
    def __add__(self, other: "Polynomial") -> "Polynomial":
        if self.var != other.var:
            other = Polynomial(dict(other.terms), self.var)
        new_terms = dict(self.terms)
        for e, c in other.terms.items():
            new_terms[e] = new_terms.get(e, Fraction(0)) + c
        return Polynomial(new_terms, self.var)

    def __sub__(self, other: "Polynomial") -> "Polynomial":
        if self.var != other.var:
            other = Polynomial(dict(other.terms), self.var)
        new_terms = dict(self.terms)
        for e, c in other.terms.items():
            new_terms[e] = new_terms.get(e, Fraction(0)) - c
        return Polynomial(new_terms, self.var)

    def __mul__(self, other: Union["Polynomial", Fraction, int]) -> "Polynomial":
        if isinstance(other, (int, Fraction)):
            new_terms = {e: c * Fraction(other) for e, c in self.terms.items()}
            return Polynomial(new_terms, self.var)
        if self.var != other.var:
            other = Polynomial(dict(other.terms), self.var)
        new_terms: Dict[int, Fraction] = {}
        for e1, c1 in self.terms.items():
            for e2, c2 in other.terms.items():
                e = e1 + e2
                new_terms[e] = new_terms.get(e, Fraction(0)) + c1 * c2
        return Polynomial(new_terms, self.var)

    __rmul__ = __mul__

    def __pow__(self, n: int) -> "Polynomial":
        if n < 0:
            raise ValueError("Negative powers not supported on polynomials")
        if n == 0:
            return Polynomial.constant(1, self.var)
        result = self
        for _ in range(n - 1):
            result = result * self
        return result

    # ── Calculus ─────────────────────────────────────────────────────────
    def differentiate(self) -> "Polynomial":
        """d/dx of this polynomial. Returns a new Polynomial.

        Rule: d/dx[c*x^n] = (c*n)*x^(n-1). Constants vanish.
        """
        if self.is_zero:
            return Polynomial({}, self.var)
        new_terms: Dict[int, Fraction] = {}
        for e, c in self.terms.items():
            if e == 0:
                continue  # constant term vanishes
            new_terms[e - 1] = c * e
        return Polynomial(new_terms, self.var)

    def integrate(self, constant: Union[int, Fraction] = 0) -> "Polynomial":
        """∫ this polynomial dx. Returns a new Polynomial.

        Rule: ∫c*x^n dx = (c/(n+1))*x^(n+1). Plus a constant of integration.
        """
        new_terms: Dict[int, Fraction] = {}
        for e, c in self.terms.items():
            new_terms[e + 1] = c / (e + 1)
        if constant != 0:
            new_terms[0] = new_terms.get(0, Fraction(0)) + Fraction(constant)
        return Polynomial(new_terms, self.var)

    def evaluate(self, x: Union[int, Fraction]) -> Fraction:
        """Evaluate at x. Returns a Fraction."""
        x = Fraction(x)
        result = Fraction(0)
        for e, c in self.terms.items():
            result += c * (x ** e)
        return result

    # ── Display ──────────────────────────────────────────────────────────
    def __str__(self) -> str:
        if not self.terms:
            return "0"
        parts = []
        for e in sorted(self.terms.keys(), reverse=True):
            c = self.terms[e]
            if c == 0:
                continue
            # Format coefficient
            if e == 0:
                parts.append(str(c))
            elif e == 1:
                if c == 1:
                    parts.append(self.var)
                elif c == -1:
                    parts.append(f"-{self.var}")
                else:
                    parts.append(f"{c}*{self.var}")
            else:
                if c == 1:
                    parts.append(f"{self.var}^{e}")
                elif c == -1:
                    parts.append(f"-{self.var}^{e}")
                else:
                    parts.append(f"{c}*{self.var}^{e}")
        if not parts:
            return "0"
        s = parts[0]
        for p in parts[1:]:
            if p.startswith("-"):
                s += " - " + p[1:]
            else:
                s += " + " + p
        return s

    def __repr__(self) -> str:
        return f"Polynomial({str(self)!r}, var={self.var!r})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Polynomial):
            return False
        return self.terms == other.terms

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.terms.items())))


# ══════════════════════════════════════════════════════════════════════════════
#  NATIVE POLYNOMIAL OPERATIONS WITH TRACE + FINGERPRINT
# ══════════════════════════════════════════════════════════════════════════════
def native_polynomial_diff(expr: str, var: str = "x",
                           validate: bool = True) -> Dict[str, Any]:
    """Native polynomial differentiation.

    Returns a dict with: operation, expr, var, result, exact, trace,
    fingerprint, sympy_check, elapsed_us, native.
    """
    t0 = time.perf_counter()
    trace: List[str] = [f"native_polynomial_diff({expr!r}, var={var!r})"]

    poly = Polynomial.from_str(expr, var=var)
    if poly is None:
        trace.append("[fallback] expression is not a polynomial — using SymPy")
        # Delegate to GLM25.symbolic_with_fingerprint
        try:
            from GLM25_native_alu import symbolic_with_fingerprint
            r = symbolic_with_fingerprint("differentiate", expr, var)
            r["native"] = False
            r["trace"] = trace + r.get("trace", [])
            return r
        except Exception as e:
            return {"operation": "differentiate", "expr": expr, "var": var,
                    "result": None, "exact": f"Error: {e}",
                    "trace": trace, "fingerprint": {},
                    "sympy_check": None, "native": False,
                    "elapsed_us": int((time.perf_counter() - t0) * 1_000_000)}

    trace.append(f"  parsed: {poly}")
    trace.append(f"  terms: {dict(poly.terms)}")

    # Apply differentiation rule term by term
    deriv = poly.differentiate()
    trace.append(f"  d/d{var} rule: c*x^n -> (c*n)*x^(n-1)")
    for e, c in sorted(poly.terms.items(), reverse=True):
        if e == 0:
            trace.append(f"    term {c}*{var}^{e}: constant, vanishes")
        else:
            new_c = c * e
            new_e = e - 1
            trace.append(f"    term {c}*{var}^{e} -> {new_c}*{var}^{new_e}")

    trace.append(f"  result: {deriv}")

    # Fingerprint: hash the result string and classify through the manifold
    result_str = str(deriv)
    try:
        import hashlib
        h = int.from_bytes(hashlib.sha256(result_str.encode()).digest(), "big")
        fp = _get_manifold().fingerprint(h)
    except Exception as e:
        fp = {"error": str(e)}

    # SymPy cross-check
    sympy_check = None
    if validate and _HAS_SYMPY:
        try:
            x = sp.Symbol(var)
            sp_result = sp.diff(sp.sympify(expr.replace("^", "**")), x)
            sp_str = str(sp_result)
            sympy_check = {
                "value": sp_str,
                "matches": (sp_str == result_str) or
                           # Try normalised comparison
                           (sp.simplify(sp.sympify(sp_str) - sp.sympify(result_str.replace("^", "**"))) == 0),
                "source_expr": f"diff({expr}, {var})",
            }
        except Exception as e:
            sympy_check = {"value": None, "matches": False, "error": str(e)}

    return {
        "operation": "differentiate",
        "expr": expr,
        "var": var,
        "result": deriv,
        "exact": result_str,
        "trace": trace,
        "fingerprint": fp,
        "sympy_check": sympy_check,
        "elapsed_us": int((time.perf_counter() - t0) * 1_000_000),
        "native": True,
    }


def native_polynomial_integrate(expr: str, var: str = "x",
                                constant: Union[int, Fraction] = 0,
                                validate: bool = True) -> Dict[str, Any]:
    """Native polynomial integration.

    Returns a dict with: operation, expr, var, result, exact, trace,
    fingerprint, sympy_check, elapsed_us, native.
    """
    t0 = time.perf_counter()
    trace: List[str] = [f"native_polynomial_integrate({expr!r}, var={var!r}, C={constant})"]

    poly = Polynomial.from_str(expr, var=var)
    if poly is None:
        trace.append("[fallback] expression is not a polynomial — using SymPy")
        try:
            from GLM25_native_alu import symbolic_with_fingerprint
            r = symbolic_with_fingerprint("integrate", expr, var)
            r["native"] = False
            r["trace"] = trace + r.get("trace", [])
            return r
        except Exception as e:
            return {"operation": "integrate", "expr": expr, "var": var,
                    "result": None, "exact": f"Error: {e}",
                    "trace": trace, "fingerprint": {},
                    "sympy_check": None, "native": False,
                    "elapsed_us": int((time.perf_counter() - t0) * 1_000_000)}

    trace.append(f"  parsed: {poly}")
    trace.append(f"  terms: {dict(poly.terms)}")

    # Apply integration rule term by term
    integral = poly.integrate(constant=constant)
    trace.append(f"  ∫ rule: c*x^n dx -> (c/(n+1))*x^(n+1) + C")
    for e, c in sorted(poly.terms.items(), reverse=True):
        new_c = c / (e + 1)
        new_e = e + 1
        trace.append(f"    term {c}*{var}^{e} -> {new_c}*{var}^{new_e}")
    if constant != 0:
        trace.append(f"    + C = {constant}")

    trace.append(f"  result: {integral}")

    result_str = str(integral)
    try:
        import hashlib
        h = int.from_bytes(hashlib.sha256(result_str.encode()).digest(), "big")
        fp = _get_manifold().fingerprint(h)
    except Exception as e:
        fp = {"error": str(e)}

    sympy_check = None
    if validate and _HAS_SYMPY:
        try:
            x = sp.Symbol(var)
            sp_result = sp.integrate(sp.sympify(expr.replace("^", "**")), x)
            sp_str = str(sp_result)
            # Compare — SymPy may format differently
            matches = (sp.simplify(sp.sympify(sp_str) - sp.sympify(result_str.replace("^", "**"))) == 0)
            sympy_check = {
                "value": sp_str,
                "matches": bool(matches),
                "source_expr": f"integrate({expr}, {var})",
            }
        except Exception as e:
            sympy_check = {"value": None, "matches": False, "error": str(e)}

    return {
        "operation": "integrate",
        "expr": expr,
        "var": var,
        "result": integral,
        "exact": result_str,
        "trace": trace,
        "fingerprint": fp,
        "sympy_check": sympy_check,
        "elapsed_us": int((time.perf_counter() - t0) * 1_000_000),
        "native": True,
    }


def is_polynomial(expr: str, var: str = "x") -> bool:
    """Quick check: can this expression be handled natively as a polynomial?"""
    return Polynomial.from_str(expr, var=var) is not None


# ══════════════════════════════════════════════════════════════════════════════
#  STATUS / SELF-TEST
# ══════════════════════════════════════════════════════════════════════════════
def status() -> Dict[str, Any]:
    return {
        "module": "GLM28_native_poly",
        "version": "3.18.0",
        "native_available": _HAS_NATIVE,
        "sympy_available": _HAS_SYMPY,
        "operations": ["differentiate", "integrate"],
        "supports": ["polynomials in one variable", "Fraction coefficients",
                     "negative exponents in input (parsed)"],
    }


if __name__ == "__main__":
    print("=== GLM28 Native Polynomial ALU v3.18.0 — self-test ===")
    print(status())
    print()

    test_cases = [
        ("differentiate", "x^3", "x"),
        ("differentiate", "3*x^2 + 2*x - 5", "x"),
        ("differentiate", "5", "x"),  # constant -> 0
        ("differentiate", "x^4 - 2*x^2 + 1", "x"),
        ("integrate", "x^2", "x"),
        ("integrate", "3*x^2 + 2*x - 5", "x"),
        ("integrate", "1", "x"),  # constant -> x
        ("integrate", "2*x^3 + 6*x", "x"),
        # Non-polynomial (should fall back to SymPy)
        ("differentiate", "sin(x)", "x"),
        ("integrate", "exp(x)", "x"),
    ]
    for op, expr, var in test_cases:
        if op == "differentiate":
            r = native_polynomial_diff(expr, var, validate=True)
        else:
            r = native_polynomial_integrate(expr, var, validate=True)
        native = r.get("native", False)
        sym = r.get("sympy_check") or {}
        print(f"\n{op}({expr}, {var}):")
        print(f"  result: {r.get('exact')!r}")
        print(f"  native: {native}  sympy_match: {sym.get('matches')}")
        print(f"  nrci: {r.get('fingerprint', {}).get('nrci')}  "
              f"lattice: {r.get('fingerprint', {}).get('lattice')!r}")
        for line in r.get("trace", [])[:5]:
            print(f"  | {line}")

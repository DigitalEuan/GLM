# ══════════════════════════════════════════════════════════════════════════════
# §29  ANSWER EXTRACTOR (v3.19.0 — output fidelity layer)
# ══════════════════════════════════════════════════════════════════════════════
#
# PURPOSE
#   The user feedback was clear: "GLM reliably solves the problems internally
#   but surfaces them with variable polish... sometimes provides full correct
#   answer but tags only a fragment." This module extracts the actual answer
#   from compute / symbolic / deliberation results and produces a clean,
#   unambiguous "Answer:" string that composers can append as a final block.
#
#   This addresses Feedback Items #1 (Output Parsing) and #4 (Completeness)
#   from the v3.19 development push.
#
# WHAT THIS MODULE DOES
#
#   * `extract_answer(comp_res, sym_res, delib_res) -> Optional[AnswerBlock]`
#     Single entry point. Tries deliberation first (already clean), then
#     compute, then symbolic. Returns an AnswerBlock with:
#       - value: the clean answer string ("84", "x = -2, 2", "Irreducible (GCD=1)")
#       - kind:  "numeric" | "symbolic" | "deliberation" | "boolean" | "list"
#       - source: "deliberation" | "compute" | "symbolic"
#       - original: the raw exact/answer string (for traceability)
#       - verified_hint: optional, e.g. "sympy_check=True" (extracted from comp_res)
#
#   * `format_answer_block(answer: Optional[AnswerBlock]) -> str`
#     Produces the user-visible string. For terse composer:
#       "[Answer] 84"
#     For prose composer:
#       "The answer is 84." (caller picks the template)
#
# EXTRACTION LOGIC
#
#   1. Deliberation: `delib_res["answer"]` is already a clean string. Just
#      extract any numeric tail if present (e.g. "C(9, 3) = 84" → "84"),
#      but if no clean number is extractable, keep the full statement
#      (e.g. "Irreducible (GCD=1)" stays as-is).
#
#   2. Compute: `comp_res["result"]["exact"]` is the answer. Format depends
#      on `comp_res["computation"]["kind"]`:
#        - gcd/lcm/factorial/sqrt/combination/power/arith/magnitude/determinant/trace
#          → number, return as-is
#        - prime → boolean, format as "Yes" / "No"
#        - cross_product → list, format as "(cx, cy, cz)"
#        - eigenvalues → dict, format as "λ₁ = v₁ (mult m₁), λ₂ = v₂ (mult m₂)"
#
#   3. Symbolic: `sym_res["result"]["exact"]` is the answer. Format depends
#      on `sym_res["computation"]["kind"]`:
#        - differentiate/integrate/simplify → expression, return as-is
#        - solve → list of roots, format as "x = -2, 2"
#        - ode → equation, format as-is
#        - taylor → series, return as-is (strip the " + O(...)" tail)
#        - limit → value, return as-is
#        - partial_diff/gradient → expression/tuple, return as-is
#
# AUTHOR
#   Z.ai v3.19 development push — 2026-07-06
# ══════════════════════════════════════════════════════════════════════════════
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# ══════════════════════════════════════════════════════════════════════════════
#  AnswerBlock dataclass
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class AnswerBlock:
    """A clean, extracted answer with metadata for the composer."""
    value: str           # the clean answer: "84", "x = -2, 2", "Irreducible (GCD=1)"
    kind: str            # "numeric" | "symbolic" | "deliberation" | "boolean" | "list" | "dict"
    source: str          # "deliberation" | "compute" | "symbolic"
    original: str        # the raw exact/answer string (for traceability)
    verified_hint: Optional[str] = None  # e.g. "sympy_check=True" or "pattern_match_only"

    def terse_str(self) -> str:
        """Format for the terse bracket-tag composer: '[Answer] 84'."""
        return f"[Answer] {self.value}"

    def prose_str(self) -> str:
        """Format for the prose composer: 'The answer is 84.'."""
        v = self.value
        # If the value starts with "x = " or similar, phrase differently
        if re.match(r'^[a-z]\s*=\s*', v):
            return f"The solution is {v}."
        if v.lower() in ("true", "false", "yes", "no"):
            return f"The answer is {v}."
        # Default: just "The answer is X."
        return f"The answer is {v}."


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS — regex patterns for numeric extraction
# ══════════════════════════════════════════════════════════════════════════════
# Match the LAST number in a string (handles "C(9, 3) = 84" → "84")
_LAST_NUMBER_RE = re.compile(r'-?\d+(?:\.\d+)?(?:/\d+)?(?=[^\d]*$)')
# Match a clean numeric expression (int, fraction, decimal)
_NUMERIC_EXPR_RE = re.compile(r'^-?\d+(?:\.\d+)?(?:/\d+)?$')
# Match "x = ..." or "x_1 = ..." style roots
_ROOT_PREFIX_RE = re.compile(r'^([a-z](?:_\d+)?)\s*=\s*')


def _try_extract_number(s: str) -> Optional[str]:
    """Try to extract a clean number from a string.
    Returns the number string if found, else None.
    """
    s = s.strip()
    if not s:
        return None
    # Already a clean number?
    if _NUMERIC_EXPR_RE.match(s):
        return s
    # Try to find the last number in the string
    m = _LAST_NUMBER_RE.search(s)
    if m:
        return m.group(0)
    return None


def _format_list_as_roots(roots: List[str], var: str = "x") -> str:
    """Format a list of roots as 'x = -2, 2' or 'x = 1 (mult 2), x = -1'."""
    if not roots:
        return f"{var} = (no real roots)"
    if len(roots) == 1:
        return f"{var} = {roots[0]}"
    return f"{var} = {', '.join(str(r) for r in roots)}"


def _format_eigenvalues(eig_dict: Dict[str, int]) -> str:
    """Format eigenvalue dict {'λ': mult} as 'λ₁ = v₁ (mult m₁), ...'."""
    if not eig_dict:
        return "(no eigenvalues)"
    parts = []
    for i, (val, mult) in enumerate(eig_dict.items(), start=1):
        if mult > 1:
            parts.append(f"λ{i} = {val} (mult {mult})")
        else:
            parts.append(f"λ{i} = {val}")
    return ", ".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN EXTRACTION FUNCTION
# ══════════════════════════════════════════════════════════════════════════════
def extract_answer(comp_res: Optional[Dict] = None,
                   sym_res: Optional[Dict] = None,
                   delib_res: Optional[Dict] = None) -> Optional[AnswerBlock]:
    """Extract a clean answer from the pipeline results.

    Priority: deliberation > compute > symbolic. (Deliberation answers are
    already clean; compute is usually a single number; symbolic can be a
    complex expression.)

    Returns None if no answer could be extracted.
    """
    # ── 1. Deliberation ──────────────────────────────────────────────────
    if delib_res and isinstance(delib_res, dict):
        raw = delib_res.get("answer")
        if raw and isinstance(raw, str):
            raw = raw.strip()
            # Heuristic: only extract a clean number if the raw string looks
            # like it ENDS with a number that's the actual answer (e.g.
            # "C(9, 3) = 84", "Number of ways = 84"). If the raw string is
            # a STATEMENT (contains words like "Irreducible", "Reducible",
            # "divisible", "n divisible by"), keep it as-is.
            statement_markers = ("irreducible", "reducible", "divisible",
                                "n divisible", "gcd=", "(gcd", "holds",
                                "is prime", "is not prime")
            is_statement = any(m in raw.lower() for m in statement_markers)
            if is_statement:
                return AnswerBlock(
                    value=raw,
                    kind="deliberation",
                    source="deliberation",
                    original=raw,
                    verified_hint="pattern_match_only",
                )
            # Try to extract a clean number from statements like
            # "C(9, 3) = 84" or "Number of ways = 84"
            num = _try_extract_number(raw)
            if num and len(raw) > len(num) + 3:
                # The raw string has more than just the number — keep both
                # but lead with the clean number for the Answer block.
                return AnswerBlock(
                    value=num,
                    kind="numeric",
                    source="deliberation",
                    original=raw,
                    verified_hint="pattern_match_only",
                )
            # No clean number — return the statement as-is
            return AnswerBlock(
                value=raw,
                kind="deliberation",
                source="deliberation",
                original=raw,
                verified_hint="pattern_match_only",
            )

    # ── 2. Compute ───────────────────────────────────────────────────────
    if comp_res and isinstance(comp_res, dict):
        result = comp_res.get("result", {})
        comp = comp_res.get("computation", {})
        kind = comp.get("kind", "")
        raw = result.get("exact", "")
        if not raw or raw in ("Error", "N/A"):
            return None

        # Extract verification hint from native path
        verified_hint = None
        if result.get("native"):
            sym_check = result.get("sympy_check")
            if sym_check and isinstance(sym_check, dict):
                if sym_check.get("matches"):
                    verified_hint = "sympy_check=True"
                else:
                    verified_hint = "sympy_check=False"

        if kind == "prime":
            # Boolean answer
            val = "Yes" if raw.lower() == "true" else "No"
            return AnswerBlock(
                value=val, kind="boolean", source="compute",
                original=raw, verified_hint=verified_hint,
            )

        if kind == "cross_product":
            # List of 3 numbers — already formatted as "[cx, cy, cz]"
            return AnswerBlock(
                value=raw, kind="list", source="compute",
                original=raw, verified_hint=verified_hint,
            )

        if kind == "eigenvalues":
            # Dict of {value: multiplicity}
            try:
                # raw is a string like "{'2': 1, '-1': 2}"
                # Try to parse it
                import ast
                eig_dict = ast.literal_eval(raw) if isinstance(raw, str) else raw
                if isinstance(eig_dict, dict):
                    formatted = _format_eigenvalues(eig_dict)
                    return AnswerBlock(
                        value=formatted, kind="dict", source="compute",
                        original=raw, verified_hint=verified_hint,
                    )
            except Exception:
                pass
            return AnswerBlock(
                value=raw, kind="dict", source="compute",
                original=raw, verified_hint=verified_hint,
            )

        # Default: numeric (gcd, lcm, factorial, sqrt, combination, power,
        # arith, magnitude, determinant, trace, dot_product)
        # raw is already a clean number string in most cases
        return AnswerBlock(
            value=raw, kind="numeric", source="compute",
            original=raw, verified_hint=verified_hint,
        )

    # ── 3. Symbolic ──────────────────────────────────────────────────────
    if sym_res and isinstance(sym_res, dict):
        result = sym_res.get("result", {})
        comp = sym_res.get("computation", {})
        kind = comp.get("kind", "")
        var = comp.get("var", "x")
        raw = result.get("exact", "")
        if not raw or raw in ("Error", "N/A"):
            return None

        # Extract verification hint
        verified_hint = None
        if result.get("sympy_check") and isinstance(result["sympy_check"], dict):
            if result["sympy_check"].get("matches"):
                verified_hint = "sympy_check=True"

        if kind == "solve":
            # raw is something like "[-2, 2]" or "[-1, 1]"
            try:
                import ast
                roots_list = ast.literal_eval(raw) if isinstance(raw, str) else raw
                if isinstance(roots_list, list):
                    roots_str = [str(r) for r in roots_list]
                    formatted = _format_list_as_roots(roots_str, var)
                    return AnswerBlock(
                        value=formatted, kind="list", source="symbolic",
                        original=raw, verified_hint=verified_hint,
                    )
            except Exception:
                pass
            # If parsing failed, return as-is
            return AnswerBlock(
                value=raw, kind="symbolic", source="symbolic",
                original=raw, verified_hint=verified_hint,
            )

        if kind == "taylor":
            # Strip the " + O(x^5)" tail for a cleaner answer
            cleaned = re.sub(r'\s*\+\s*O\([^)]+\)\s*$', '', raw)
            return AnswerBlock(
                value=cleaned, kind="symbolic", source="symbolic",
                original=raw, verified_hint=verified_hint,
            )

        if kind == "ode":
            # raw is like "Eq(y(x), C1*exp(x))" — convert to "y(x) = C1*exp(x)"
            # Strip the leading "Eq(" and trailing ")", then split on the
            # first ", " to separate LHS from RHS.
            cleaned = raw
            if cleaned.startswith("Eq(") and cleaned.endswith(")"):
                inner = cleaned[3:-1]  # strip "Eq(" and ")"
                # Split on the first ", " — but be careful about nested parens
                # (e.g. "y(x), C1*exp(x)" — split at the top-level comma)
                depth = 0
                split_idx = -1
                for i, ch in enumerate(inner):
                    if ch == '(':
                        depth += 1
                    elif ch == ')':
                        depth -= 1
                    elif ch == ',' and depth == 0:
                        split_idx = i
                        break
                if split_idx >= 0:
                    lhs = inner[:split_idx].strip()
                    rhs = inner[split_idx+1:].strip()
                    cleaned = f"{lhs} = {rhs}"
            return AnswerBlock(
                value=cleaned, kind="symbolic", source="symbolic",
                original=raw, verified_hint=verified_hint,
            )

        # Default: differentiate, integrate, simplify, partial_diff, gradient, limit, sum
        return AnswerBlock(
            value=raw, kind="symbolic", source="symbolic",
            original=raw, verified_hint=verified_hint,
        )

    return None


# ══════════════════════════════════════════════════════════════════════════════
#  FORMATTERS (for the composers to call)
# ══════════════════════════════════════════════════════════════════════════════
def format_answer_terse(answer: Optional[AnswerBlock]) -> str:
    """Format for the terse composer. Returns '' if no answer."""
    if answer is None:
        return ""
    return answer.terse_str()


def format_answer_prose(answer: Optional[AnswerBlock]) -> str:
    """Format for the prose composer. Returns '' if no answer."""
    if answer is None:
        return ""
    return answer.prose_str()


# ══════════════════════════════════════════════════════════════════════════════
#  STATUS / SELF-TEST
# ══════════════════════════════════════════════════════════════════════════════
def status() -> Dict[str, Any]:
    return {
        "module": "GLM29_answer_extractor",
        "version": "3.19.0",
        "operations": ["extract_answer", "format_answer_terse", "format_answer_prose"],
    }


if __name__ == "__main__":
    print("=== GLM29 Answer Extractor v3.19.0 — self-test ===")
    print(status())
    print()

    # Test cases mimicking real pipeline results
    test_cases = [
        # (label, comp_res, sym_res, delib_res, expected_value_substring)
        ("gcd(54,24)",
         {"computation": {"kind": "gcd", "expr": "gcd(54,24)"},
          "result": {"exact": "6", "approx": 6.0, "native": True,
                     "sympy_check": {"matches": True}}},
         None, None, "6"),
        ("is 97 prime?",
         {"computation": {"kind": "prime", "expr": "isprime(97)"},
          "result": {"exact": "True", "approx": 1.0, "native": True,
                     "sympy_check": {"matches": True}}},
         None, None, "Yes"),
        ("det 3x3",
         {"computation": {"kind": "determinant", "expr": "[[1,2,3],[4,5,6],[7,8,10]]"},
          "result": {"exact": "-3", "approx": -3.0, "native": True,
                     "sympy_check": {"matches": True}}},
         None, None, "-3"),
        ("stars and bars (deliberation)",
         None, None,
         {"pattern": "stars_and_bars", "method": "stars_and_bars",
          "answer": "C(9, 3) = 84",
          "trace": ["n = 10 identical balls", "k = 4 boxes",
                    "Stars and bars: C(n-1, k-1)", "Number of ways = C(9, 3) = 84"]},
         "84"),
        ("irreducible fraction (deliberation)",
         None, None,
         {"pattern": "gcd_proof", "method": "euclidean_algorithm",
          "answer": "Irreducible (GCD=1)",
          "trace": ["gcd(21n+4, 14n+3) via Euclidean", "...", "GCD=1"]},
         "Irreducible"),
        ("solve x^2-4",
         None,
         {"computation": {"kind": "solve", "expr": "x^2-4=0", "var": "x"},
          "result": {"exact": "[-2, 2]", "native": False}},
         None, "x = -2, 2"),
        ("differentiate x^3",
         None,
         {"computation": {"kind": "differentiate", "expr": "x^3", "var": "x"},
          "result": {"exact": "3*x**2", "native": True,
                     "sympy_check": {"matches": True}}},
         None, "3*x**2"),
        ("ODE dy/dx=y",
         None,
         {"computation": {"kind": "ode", "expr": "y' = y", "var": "x"},
          "result": {"exact": "Eq(y(x), C1*exp(x))", "native": False}},
         None, "y(x) = C1*exp(x)"),
        ("taylor exp(x)",
         None,
         {"computation": {"kind": "taylor", "expr": "exp(x)", "var": "x", "around": "0"},
          "result": {"exact": "x**4/24 + x**3/6 + x**2/2 + x + 1 + O(x^5)", "native": False}},
         None, "x + 1"),
    ]

    all_ok = True
    for label, comp, sym, delib, expected_sub in test_cases:
        ans = extract_answer(comp, sym, delib)
        if ans is None:
            print(f"  [FAIL] {label}: no answer extracted")
            all_ok = False
            continue
        ok = expected_sub in ans.value
        tag = "PASS" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"  [{tag}] {label}: value={ans.value!r} kind={ans.kind} "
              f"source={ans.source} verified={ans.verified_hint}")
        print(f"         terse: {ans.terse_str()!r}")
        print(f"         prose: {ans.prose_str()!r}")

    print()
    print(f"{'ALL PASS' if all_ok else 'SOME FAILED'}")

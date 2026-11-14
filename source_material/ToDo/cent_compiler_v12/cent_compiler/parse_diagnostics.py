"""Actionable diagnostics for £ parse failures.

A diagnostic never rewrites the user's relation.  It names the unsupported
symbol (or syntax problem), suggests the nearest *accepted* function when one
exists, and otherwise lists the accepted forms.  Every diagnostic ends with a
fixed, known-good command that the user can copy without guessing.
"""
from __future__ import annotations

import difflib
import re
from typing import Any

ACCEPTED_FUNCTIONS = ("sqrt", "exp", "log", "ln", "tanh")
ACCEPTED_OPERATORS = ("+", "-", "*", "/", "^", "**")
ACCEPTED_UNARY = ("-",)
DEFAULT_EXAMPLE = 'cent compile "y = sqrt(5)"'
FUNCTION_EXAMPLES = {
    "sqrt": 'cent compile "y = sqrt(5)"',
    "exp": 'cent compile "y = exp(x)"',
    "log": 'cent compile "y = log(x)"',
    "ln": 'cent compile "y = log(x)"',
    "tanh": 'cent compile "y = tanh(x)"',
}
_OPERATOR_NAMES = {
    "Add": "+",
    "Sub": "-",
    "Mod": "%",
    "FloorDiv": "//",
    "LShift": "<<",
    "RShift": ">>",
    "BitOr": "|",
    "BitXor": "^ (bitwise)",
    "BitAnd": "&",
    "MatMult": "@",
}


def _function_name(message: str, expression: str) -> str | None:
    match = re.search(r"unsupported function call:\s*([A-Za-z_]\w*)\(\)", message)
    if match:
        return match.group(1)
    if "function" not in message.lower():
        return None
    for name in re.findall(r"\b([A-Za-z_]\w*)\s*\(", expression):
        if name not in ACCEPTED_FUNCTIONS:
            return name
    return None


def _operator_symbol(message: str) -> str | None:
    for name, symbol in _OPERATOR_NAMES.items():
        if f"op={name}()" in message:
            return symbol
    return None


def _accepted_operator_forms() -> list[str]:
    return [f"operator {op}" for op in ACCEPTED_OPERATORS]


def diagnose_parse_error(exc: BaseException, expression: str = "") -> dict[str, Any]:
    """Return a structured, non-fabricating diagnostic for a parse failure."""
    message = str(exc).strip() or type(exc).__name__
    lower = message.lower()
    function = _function_name(message, expression)
    operator = _operator_symbol(message)
    exponent_error = "exponent" in lower
    syntax_error = isinstance(exc, SyntaxError)

    nearest = None
    nearest_kind = None
    if function is not None:
        matches = difflib.get_close_matches(
            function, ACCEPTED_FUNCTIONS, n=1, cutoff=0.6
        )
        if matches:
            nearest = matches[0]
            nearest_kind = "function"

    if function is not None:
        accepted = [f"{name}(x)" for name in ACCEPTED_FUNCTIONS]
        if nearest:
            suggestion = f"Did you mean {nearest}(x)?"
        else:
            suggestion = "Use one of the accepted functions."
        example = FUNCTION_EXAMPLES.get(nearest or "", DEFAULT_EXAMPLE)
    elif exponent_error:
        accepted = ["integer powers -2, -1, 1, 2, 3", "fractional power ^(1/2)"]
        suggestion = (
            "Use a supported integer power, or `x^(1/2)` for a square root."
        )
        example = DEFAULT_EXAMPLE
    elif operator is not None:
        accepted = _accepted_operator_forms()
        suggestion = (
            f"The parser has no declared equivalent for {operator!r}; "
            "use only the accepted operators."
        )
        example = DEFAULT_EXAMPLE
    elif syntax_error and ("never closed" in lower or "parenthes" in lower):
        accepted = _accepted_operator_forms()
        suggestion = "Check parentheses: every '(' needs a closing ')'."
        example = DEFAULT_EXAMPLE
    elif syntax_error:
        accepted = _accepted_operator_forms()
        suggestion = "Use one relation of the form target = expression."
        example = DEFAULT_EXAMPLE
    else:
        accepted = _accepted_operator_forms()
        suggestion = "Check the relation against the accepted forms."
        example = DEFAULT_EXAMPLE

    return {
        "message": message,
        "nearest": nearest,
        "nearest_kind": nearest_kind,
        "suggestion": suggestion,
        "accepted": accepted,
        "example": example,
    }


def render_diagnostic(diagnostic: dict[str, Any]) -> str:
    """Render a diagnostic without echoing a rewritten relation."""
    lines = [f"parse: {diagnostic['message']}"]
    if diagnostic.get("nearest"):
        lines.append(
            f"  nearest accepted {diagnostic.get('nearest_kind')}: "
            f"{diagnostic['nearest']}"
        )
    lines.append(f"  suggestion: {diagnostic['suggestion']}")
    lines.append(f"  accepted: {', '.join(diagnostic['accepted'])}")
    lines.append(f"  example: {diagnostic['example']}")
    return "\n".join(lines)


def render_parse_error(exc: BaseException, expression: str = "") -> str:
    """Convenience wrapper used by the CLI."""
    return render_diagnostic(diagnose_parse_error(exc, expression))


__all__ = [
    "ACCEPTED_FUNCTIONS",
    "ACCEPTED_OPERATORS",
    "ACCEPTED_UNARY",
    "DEFAULT_EXAMPLE",
    "diagnose_parse_error",
    "render_diagnostic",
    "render_parse_error",
]

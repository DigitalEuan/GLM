"""``glm_universal.reasoning.exactness`` -- where a float could be made.

Directive **D7** says the package constructs no floating-point number: `int`,
:class:`fractions.Fraction` and exact ``F_2`` arithmetic only.  A directive is
worth no more than the instrument behind it, and until this module existed D7
was checked by reading.  This module checks it by parsing.

**What is scanned.**  Every non-test module of the package is parsed and its
syntax tree walked for the four ways a float can enter a Python program:

``float-literal``
    a literal with a decimal point or an exponent (``0.5``, ``1e-9``), or a
    complex literal;
``float-call``
    a call to the ``float`` builtin;
``float-clock``
    ``time.time()``, ``time.monotonic()`` or ``time.perf_counter()`` -- each of
    which returns a float, which is why every timing layer here measures in
    integer nanoseconds with :func:`time.monotonic_ns` instead;
``inexact-library``
    an import of, or a call into, a library whose results are floats:
    ``statistics``, ``decimal``, ``numpy``, ``random``'s float generators, or
    any ``math`` function outside the exact integer set
    :data:`EXACT_MATH_NAMES` (``isqrt``, ``gcd``, ``lcm``, ``comb``, ``perm``,
    ``factorial``, ``prod``).

Parsing rather than grepping is the point: the word ``float`` in a docstring or
in the name ``carrier_rejects_floats`` is not a float, and ``math.isqrt`` is
not an inexact library call even though ``math`` is imported.

**The inventory.**  :data:`FLOAT_SITES` declares every module that legitimately
contains one of those sites, with the kinds it contains and why they are
warranted.  :func:`exactness_inventory` scans the tree and *fails* -- by
reporting, not by raising -- if a module has acquired a float site without
being classified, or if a declared site no longer exists.  So the rule is not
remembered, it is enforced: the next module that writes ``0.5`` fails the
suite.

**Division.**  ``a / b`` is exact when either side is a :class:`Fraction` and a
float when both are plain ints, and which it is cannot be read off the syntax.
What *can* be read off the syntax is the case where both sides are certainly
integers -- two integer literals, two :func:`len` calls, a literal over a
``len`` -- and :func:`certain_float_divisions` reports those.  There are none,
which is the point: the exact quotients in this package are all built from a
``Fraction`` on at least one side.

**What this module does not claim.**  A static scan cannot prove that no float
is ever constructed at run time -- ``sum()`` over a list someone filled with
floats would escape it.  What it does prove is that no float is *written*, and
that the four syntactic doors a float comes through are all accounted for.  The
run-time half is the ``carrier_rejects_floats`` capability probe, which feeds
floats to the four entry points of the substrate and requires each to raise.
"""

from __future__ import annotations

import ast
import pathlib
from typing import Dict, Tuple

__all__ = [
    "FLOAT_KINDS", "FLOAT_SITES", "EXACT_MATH_NAMES", "INEXACT_MODULES",
    "FLOAT_CLOCKS", "DIGEST_SITES", "module_float_sites",
    "module_digest_uses", "exactness_inventory", "digest_inventory",
    "certain_float_divisions", "exactness_report",
    "warranted_operations_report",
]


#: The four syntactic ways a float enters a Python program.
FLOAT_KINDS: Tuple[str, ...] = (
    "float-literal", "float-call", "float-clock", "inexact-library",
)

#: ``math`` functions that take and return exact integers.
EXACT_MATH_NAMES = frozenset({
    "isqrt", "gcd", "lcm", "comb", "perm", "factorial", "prod",
})

#: Libraries whose ordinary results are floats.
INEXACT_MODULES = frozenset({"statistics", "decimal", "numpy", "np", "cmath"})

#: Clock calls that return a float.  ``time.monotonic_ns`` is not one of them.
FLOAT_CLOCKS = frozenset({"time", "monotonic", "perf_counter", "process_time",
                          "clock"})

#: ``random`` functions that return floats (the integer ones are exact).
INEXACT_RANDOM = frozenset({"random", "uniform", "gauss", "normalvariate",
                            "expovariate", "betavariate", "triangular"})

#: Every non-test module of the package that contains a float site, with the
#: kinds it contains and why the site is warranted.  Checked against the tree
#: by :func:`exactness_inventory`.
FLOAT_SITES: Tuple[Tuple[str, Tuple[str, ...], str], ...] = (
    ("capabilities/probes.py", ("float-literal",),
     "the carrier_rejects_floats probe feeds 0.5 and 2.0 to four entry "
     "points of the substrate and requires each to raise TypeError; the "
     "floats are the adversarial input, and the result of the probe is that "
     "none of them was accepted"),
)


def _package_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent


def _is_float_literal(node: ast.AST) -> bool:
    return (isinstance(node, ast.Constant)
            and isinstance(node.value, (float, complex))
            and not isinstance(node.value, bool))


def module_float_sites(path: pathlib.Path) -> Dict[str, int]:
    """How many sites of each kind in :data:`FLOAT_KINDS` the module has."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: Dict[str, int] = {kind: 0 for kind in FLOAT_KINDS}
    for node in ast.walk(tree):
        if _is_float_literal(node):
            found["float-literal"] += 1
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "float":
                found["float-call"] += 1
            elif isinstance(func, ast.Attribute) and isinstance(
                    func.value, ast.Name):
                owner, name = func.value.id, func.attr
                if owner == "time" and name in FLOAT_CLOCKS:
                    found["float-clock"] += 1
                elif owner == "math" and name not in EXACT_MATH_NAMES:
                    found["inexact-library"] += 1
                elif owner == "random" and name in INEXACT_RANDOM:
                    found["inexact-library"] += 1
                elif owner in INEXACT_MODULES:
                    found["inexact-library"] += 1
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in INEXACT_MODULES:
                    found["inexact-library"] += 1
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in INEXACT_MODULES:
                found["inexact-library"] += 1
    return {kind: count for kind, count in found.items() if count}


def _certainly_integer(node: ast.AST) -> bool:
    """True when the expression is certainly a plain ``int``.

    Integer literals, :func:`len` calls, and sums and differences of those.
    Anything that could be a :class:`Fraction` is not certainly an integer.
    """
    if isinstance(node, ast.Constant):
        return isinstance(node.value, int) and not isinstance(node.value, bool)
    if isinstance(node, ast.Call):
        return isinstance(node.func, ast.Name) and node.func.id == "len"
    if isinstance(node, ast.BinOp) and isinstance(
            node.op, (ast.Add, ast.Sub, ast.Mult)):
        return (_certainly_integer(node.left)
                and _certainly_integer(node.right))
    return False


def certain_float_divisions() -> Tuple[Tuple[str, int], ...]:
    """Every ``a / b`` in the package with both sides certainly integers.

    Such a quotient is a float whatever the surrounding code intends, so it is
    a D7 violation the syntax alone is enough to convict.  Divisions with a
    :class:`Fraction` on either side -- the exact quotients this package is
    built from -- are invisible to this test, by construction.
    """
    root = _package_root()
    hits = []
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if "__pycache__" in rel:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
                    and _certainly_integer(node.left)
                    and _certainly_integer(node.right)):
                hits.append((rel, node.lineno))
    return tuple(hits)


def exactness_inventory() -> Dict[str, object]:
    """Scan the tree and check :data:`FLOAT_SITES` against it.

    Fails -- by reporting, not by raising -- if a module has acquired a float
    site without being classified, or if a declared site no longer has one.
    """
    root = _package_root()
    found: Dict[str, Dict[str, int]] = {}
    tests: Dict[str, Dict[str, int]] = {}
    modules = 0
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if "__pycache__" in rel:
            continue
        sites = module_float_sites(path)
        if rel.startswith("tests/"):
            if sites:
                tests[rel] = sites
            continue
        modules += 1
        if sites:
            found[rel] = sites
    declared = {module: kinds for module, kinds, _ in FLOAT_SITES}
    unclassified = tuple(sorted(set(found) - set(declared)))
    stale = tuple(sorted(set(declared) - set(found)))
    mismatched = tuple(sorted(
        module for module in set(found) & set(declared)
        if set(found[module]) != set(declared[module])))
    by_kind = {kind: 0 for kind in FLOAT_KINDS}
    for sites in found.values():
        for kind, count in sites.items():
            by_kind[kind] += count
    return {
        "modules_scanned": modules,
        "modules_with_float_sites": len(found),
        "sites": {module: dict(sites) for module, sites in found.items()},
        "by_kind": by_kind,
        "declared_modules": len(declared),
        "unclassified_modules": unclassified,
        "stale_declarations": stale,
        "mismatched_kinds": mismatched,
        "inventory_is_complete": (not unclassified and not stale
                                  and not mismatched),
        "test_modules_with_float_sites": tuple(sorted(tests)),
        "certain_float_divisions": certain_float_divisions(),
    }


def exactness_report() -> Dict[str, object]:
    """The D7 instrument in one call: the inventory and what it proves."""
    inventory = exactness_inventory()
    return {
        "directive": "D7",
        "rule": "No floats. Exact integers and Fraction everywhere.",
        "inventory": inventory,
        "float_free_modules": (int(inventory["modules_scanned"])
                               - int(inventory["modules_with_float_sites"])),
        "runtime_check": "capabilities/probes.py: carrier_rejects_floats",
        "holds": bool(inventory["inventory_is_complete"])
        and not inventory["certain_float_divisions"],
    }


# ---------------------------------------------------------------------------
# The digest half of the same rule
# ---------------------------------------------------------------------------
#: Every non-test module that reaches for a cryptographic digest, and what it
#: uses it for.  D3 allows exactly one use -- integrity -- so each row has to
#: name an integrity job, and :func:`digest_inventory` fails if a module starts
#: hashing without a row here.  A digest never addresses meaning: the meaning
#: of a thing in this package is its carrier, and a carrier is computed from
#: the thing itself.
DIGEST_SITES: Tuple[Tuple[str, str], ...] = (
    ("integrity.py",
     "the digest layer itself: file and tree digests used to tell whether a "
     "stored result may be reused (D4)"),
    ("benchmarks/harness.py",
     "a sixteen-character digest of a suite's inputs, so a benchmark result "
     "is only reused against the inputs it was measured on"),
    ("signoff/ledger.py",
     "the signature a unit is signed off with: a digest of the sources and "
     "documents it depended on, which is what makes a signature go stale"),
)


def module_digest_uses(path: pathlib.Path) -> int:
    """How many times the module imports a hashing library.

    Imports inside a function count -- ``signoff/ledger.py`` and
    ``derived.py`` import :mod:`hashlib` locally precisely so that the core
    never imports it at module scope -- and a mention in a docstring or in a
    list of banned names does not, which is why this parses.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    uses = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            uses += sum(1 for alias in node.names
                        if alias.name.split(".")[0] == "hashlib")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] == "hashlib":
                uses += 1
    return uses


def digest_inventory() -> Dict[str, object]:
    """Scan the tree and check :data:`DIGEST_SITES` against it."""
    root = _package_root()
    found: Dict[str, int] = {}
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if rel.startswith("tests/") or "__pycache__" in rel:
            continue
        uses = module_digest_uses(path)
        if uses:
            found[rel] = uses
    declared = {module for module, _ in DIGEST_SITES}
    unclassified = tuple(sorted(set(found) - declared))
    stale = tuple(sorted(declared - set(found)))
    return {
        "modules_using_a_digest": len(found),
        "uses": sum(found.values()),
        "declared_modules": len(declared),
        "unclassified_modules": unclassified,
        "stale_declarations": stale,
        "inventory_is_complete": not unclassified and not stale,
        "every_use_is_integrity": not unclassified,
    }


def warranted_operations_report() -> Dict[str, object]:
    """D9 in one call: the three inventories, and whether all three hold.

    The rule is that an operation which is not the substrate's own arithmetic
    is used only where it is warranted, and that every such site is declared.
    Three classes of operation are checkable from the syntax, and each has an
    inventory that fails when the tree and the declaration disagree:

    * **floats** -- :func:`exactness_inventory`, here;
    * **digests** -- :func:`digest_inventory`, here;
    * **XOR** -- :func:`glm_universal.reasoning.combiner.xor_inventory`,
      which also classifies each site by the role XOR plays in it.
    """
    from .combiner import xor_inventory

    floats = exactness_inventory()
    digests = digest_inventory()
    xor = xor_inventory()
    return {
        "directive": "D9",
        "floats": floats,
        "digests": digests,
        "xor": xor,
        "inventories": 3,
        "complete": sum(1 for part in (floats, digests, xor)
                        if part["inventory_is_complete"]),
        "holds": (bool(floats["inventory_is_complete"])
                  and not floats["certain_float_divisions"]
                  and bool(digests["inventory_is_complete"])
                  and bool(xor["inventory_is_complete"])),
    }

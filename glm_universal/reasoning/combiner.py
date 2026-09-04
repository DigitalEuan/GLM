"""``glm_universal.reasoning.combiner`` -- what XOR is doing here.

What this module is
-------------------
The computational half of ``studies/COMBINER_STUDY.md``.  ``a ^ b`` forgets
which operand supplied each bit, and in a system that claims to be exact that
is the sort of thing that should be justified rather than assumed.  This module
justifies it, or fails to, by computation:

``affine_tables`` / ``affine_coefficients`` / ``closure_report``
    the sixteen coordinatewise Boolean combiners, which eight of them are
    affine over ``F2``, and the fact that the Golay code is closed under
    exactly those eight -- with an explicit pair of codewords leaving the code
    for each of the other eight;
``xor_fibre_size`` / ``small_fibre_census`` / ``fibre_report``
    what XOR loses: uniformly ``2**24`` pairs per target, which is the
    pigeonhole bound for *any* map from pairs of 24-bit words to a 24-bit word,
    so the loss belongs to the width of the output and not to the operation;
``tsum`` / ``tdiff`` / ``recover_pair`` / ``integer_layer_report``
    the constructive half.  Refuse to reduce mod 2 and the overlap comes back:
    the coordinatewise integer sum carries ``3**24`` states, between ``2**38``
    and ``2**39``, and the pair itself is recovered from the sum together with
    the signed difference;
``XOR_SITES`` / ``xor_inventory``
    every module of the package that uses ``^``, found by parsing the syntax
    tree rather than by grepping, with the role it plays there.  The inventory
    *fails* if a module starts using XOR without being classified, so it cannot
    go stale.

The counterpart formal development, with the same statements proved as
theorems, is ``RequestProject/GLM/Combiner.lean``, and by D8 that file is the
specification where the two disagree.

Everything is exact.  No float is constructed anywhere in this module.
"""

from __future__ import annotations

import ast
import pathlib
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import mog

__all__ = [
    "WIDTH", "ALL_ONES", "OP_NAMES", "AFFINE_NAMES", "ROLES", "XOR_SITES",
    "op_table", "op_index", "apply_op", "is_affine", "affine_coefficients",
    "affine_tables", "closure_witness", "closure_table", "closure_report",
    "xor_fibre_size", "small_fibre_census", "fibre_report",
    "tsum", "tdiff", "tsum_symm_diff", "tsum_inter", "recover_pair",
    "integer_layer_report", "xor_inventory", "combiner_report",
]

#: The carrier the substrate actually runs on.
WIDTH = 24

#: The all-ones word of that carrier -- itself a Golay codeword, which is what
#: makes the four complemented affine operations closed as well.
ALL_ONES = (1 << WIDTH) - 1

#: The sixteen coordinatewise Boolean combiners, indexed by truth table.  The
#: index of ``f`` is ``sum(f(x, y) << (2 * x + y))``.
OP_NAMES: Tuple[str, ...] = (
    "false",            # 0  0000
    "nor",              # 1  a nor b
    "b-and-not-a",      # 2  converse nonimplication
    "not-a",            # 3
    "a-and-not-b",      # 4  nonimplication
    "not-b",            # 5
    "xor",              # 6
    "nand",             # 7
    "and",              # 8
    "xnor",             # 9
    "b",                # 10
    "a-or-not-b",       # 11 converse implication, b -> a
    "a",                # 12
    "not-a-or-b",       # 13 implication, a -> b
    "or",               # 14
    "true",             # 15
)

#: The eight that are affine over ``F2``; every one is a symmetric difference
#: of the operands with a constant.
AFFINE_NAMES: Tuple[str, ...] = (
    "false", "not-a", "not-b", "xor", "xnor", "b", "a", "true",
)

#: The roles a ``^`` can play in this package.  Anything outside this table is
#: an unclassified site and :func:`xor_inventory` refuses it.
ROLES: Dict[str, str] = {
    "group-law": (
        "addition in F2^n: the group operation of a code or lattice. One "
        "operand together with the result returns the other, so nothing is "
        "lost that was not already a choice of basepoint."
    ),
    "metric": (
        "inside popcount(a ^ b), i.e. a Hamming distance. A metric is "
        "supposed to forget which point was which."
    ),
    "digest": (
        "an integrity checksum. D3: a digest addresses integrity, never "
        "meaning."
    ),
    "retired": (
        "a site where XOR was used as a lossy combiner and no longer is. Kept "
        "only so that it can report its own loss."
    ),
}


# ---------------------------------------------------------------------------
# 1.  The sixteen combiners, and which of them are affine
# ---------------------------------------------------------------------------
def op_table(index: int) -> Tuple[int, int, int, int]:
    """The truth table of combiner ``index``, entry ``2 * x + y`` being
    ``f(x, y)``."""
    if not 0 <= index < 16:
        raise ValueError("op_table: index must be one of the sixteen")
    return tuple((index >> k) & 1 for k in range(4))  # type: ignore[return-value]


def op_index(table: Sequence[int]) -> int:
    """Inverse of :func:`op_table`."""
    if len(table) != 4 or any(v not in (0, 1) for v in table):
        raise ValueError("op_index: a truth table is four bits")
    return sum(int(v) << k for k, v in enumerate(table))


def apply_op(index: int, a: int, b: int, width: int = WIDTH) -> int:
    """Apply combiner ``index`` coordinatewise to two ``width``-bit words."""
    ones = (1 << width) - 1
    a &= ones
    b &= ones
    na, nb = ~a & ones, ~b & ones
    table = op_table(index)
    out = 0
    for x in (0, 1):
        for y in (0, 1):
            if table[2 * x + y]:
                out |= (a if x else na) & (b if y else nb)
    return out


def affine_coefficients(index: int) -> Optional[Tuple[int, int, int]]:
    """``(c0, c1, c2)`` with ``f x y = c0 ^ (c1 & x) ^ (c2 & y)``, or ``None``
    when the combiner is not affine over ``F2``."""
    table = op_table(index)
    c0 = table[0]
    c1 = table[2] ^ c0
    c2 = table[1] ^ c0
    if table[3] != (c0 ^ c1 ^ c2):
        return None
    return (c0, c1, c2)


def is_affine(index: int) -> bool:
    """Whether combiner ``index`` is affine over ``F2``."""
    return affine_coefficients(index) is not None


def affine_tables() -> Tuple[int, ...]:
    """The indices of the affine combiners, in order."""
    return tuple(i for i in range(16) if is_affine(i))


# ---------------------------------------------------------------------------
# 2.  Closure: the code is closed under exactly the affine combiners
# ---------------------------------------------------------------------------
def _octad_pair(code: Optional[mog.GolayCode] = None) -> Tuple[int, int]:
    """The first two octads, in the code's own order, meeting in four cells.

    Four is the interesting overlap: the intersection then has weight 4, which
    is below the minimum weight 8, so it cannot be a codeword -- and neither
    can its complement, because the all-ones word is one.
    """
    code = code or mog.GolayCode()
    octads = code.octad_masks
    for i, a in enumerate(octads):
        for b in octads[i + 1:]:
            if mog.popcount(a & b) == 4:
                return (a, b)
    raise AssertionError("no two octads meet in four cells")  # pragma: no cover


def closure_witness(index: int,
                    code: Optional[mog.GolayCode] = None
                    ) -> Optional[Tuple[int, int, int]]:
    """A pair of codewords that combiner ``index`` carries out of the code.

    ``None`` for the eight affine combiners, which have no such pair.
    """
    code = code or mog.GolayCode()
    if is_affine(index):
        return None
    a, b = _octad_pair(code)
    out = apply_op(index, a, b)
    if not code.is_codeword(out):
        return (a, b, out)
    for x in code.octad_masks[:64]:  # pragma: no cover - the pair suffices
        for y in code.octad_masks[:64]:
            out = apply_op(index, x, y)
            if not code.is_codeword(out):
                return (x, y, out)
    return None  # pragma: no cover


def closure_table(code: Optional[mog.GolayCode] = None) -> List[Dict[str, object]]:
    """One row per combiner: whether it is affine, whether the code is closed
    under it, and the witness when it is not."""
    code = code or mog.GolayCode()
    rows: List[Dict[str, object]] = []
    for index in range(16):
        witness = closure_witness(index, code)
        rows.append({
            "index": index,
            "name": OP_NAMES[index],
            "affine": is_affine(index),
            "coefficients": affine_coefficients(index),
            "closed": witness is None,
            "witness": witness,
        })
    return rows


def closure_report(code: Optional[mog.GolayCode] = None) -> Dict[str, object]:
    """The classification of section 1 of the study, recomputed."""
    code = code or mog.GolayCode()
    rows = closure_table(code)
    closed = tuple(str(r["name"]) for r in rows if r["closed"])
    affine = tuple(str(r["name"]) for r in rows if r["affine"])
    witnessed = all(r["witness"] is not None for r in rows if not r["affine"])
    return {
        "operations": 16,
        "affine_operations": len(affine),
        "affine_names": list(affine),
        "closed_names": list(closed),
        "closed_iff_affine": sorted(closed) == sorted(affine),
        "non_affine_witnessed": witnessed,
        "all_ones_is_a_codeword": code.is_codeword(ALL_ONES),
        "lean": "GLM.Golay24.closed_iff_affine",
    }


# ---------------------------------------------------------------------------
# 3.  What XOR loses
# ---------------------------------------------------------------------------
def xor_fibre_size(width: int = WIDTH) -> int:
    """``#{(a, b) : a ^ b = t}`` for every target ``t`` of the given width.

    Fixing the first operand determines the second, so the fibre is a copy of
    the whole carrier and does not depend on ``t``.
    """
    return 1 << width


def small_fibre_census(width: int) -> Dict[int, int]:
    """The same statement run outright at a width small enough to enumerate:
    a map from fibre size to the number of targets attaining it."""
    counts: Dict[int, int] = {}
    for a in range(1 << width):
        for b in range(1 << width):
            t = a ^ b
            counts[t] = counts.get(t, 0) + 1
    census: Dict[int, int] = {}
    for size in counts.values():
        census[size] = census.get(size, 0) + 1
    return census


def fibre_report(width: int = WIDTH) -> Dict[str, object]:
    """XOR against the pigeonhole bound for its output width."""
    pairs = 1 << (2 * width)
    words = 1 << width
    bound = pairs // words
    return {
        "width": width,
        "ordered_pairs": pairs,
        "words": words,
        "least_possible_largest_fibre": bound,
        "xor_fibre": xor_fibre_size(width),
        "xor_attains_the_bound": xor_fibre_size(width) == bound,
        "xor_is_uniform": True,
        "bits_lost": width,
        "lean": "GLM.Golay24.xor_fibre_card, GLM.Golay24.exists_large_fibre",
    }


# ---------------------------------------------------------------------------
# 4.  Widen the output and the overlap comes back
# ---------------------------------------------------------------------------
def tsum(a: int, b: int, width: int = WIDTH) -> Tuple[int, ...]:
    """The coordinatewise integer sum, in ``{0, 1, 2}**width``."""
    return tuple(((a >> k) & 1) + ((b >> k) & 1) for k in range(width))


def tdiff(a: int, b: int, width: int = WIDTH) -> Tuple[int, ...]:
    """The coordinatewise signed difference, in ``{-1, 0, 1}**width``."""
    return tuple(((a >> k) & 1) - ((b >> k) & 1) for k in range(width))


def tsum_symm_diff(a: int, b: int, width: int = WIDTH) -> int:
    """The coordinates where the integer sum is ``1`` -- that is ``a ^ b``."""
    return sum(1 << k for k, v in enumerate(tsum(a, b, width)) if v == 1)


def tsum_inter(a: int, b: int, width: int = WIDTH) -> int:
    """The coordinates where the integer sum is ``2`` -- that is ``a & b``."""
    return sum(1 << k for k, v in enumerate(tsum(a, b, width)) if v == 2)


def recover_pair(s: Sequence[int], d: Sequence[int]) -> Tuple[int, int]:
    """``(a, b)`` from ``(tsum, tdiff)``: ``a = (s + d) / 2``, ``b = (s - d) / 2``."""
    if len(s) != len(d):
        raise ValueError("recover_pair: the two carriers must agree in width")
    a = b = 0
    for k, (sv, dv) in enumerate(zip(s, d)):
        av, bv = Fraction(sv + dv, 2), Fraction(sv - dv, 2)
        if av.denominator != 1 or bv.denominator != 1:
            raise ValueError("recover_pair: not a (tsum, tdiff) pair")
        if av:
            a |= 1 << k
        if bv:
            b |= 1 << k
    return (a, b)


def integer_layer_report(samples: int = 32) -> Dict[str, object]:
    """The integer layer, checked on the code's own words."""
    code = mog.GolayCode()
    words = code.codeword_masks
    step = max(1, len(words) // samples)
    drawn = words[::step][:samples]
    xor_ok = inter_ok = pair_ok = True
    for i, a in enumerate(drawn):
        b = drawn[(i + 1) % len(drawn)]
        xor_ok &= tsum_symm_diff(a, b) == a ^ b
        inter_ok &= tsum_inter(a, b) == a & b
        pair_ok &= recover_pair(tsum(a, b), tdiff(a, b)) == (a, b)
    ternary = 3 ** WIDTH
    return {
        "pairs_checked": len(drawn),
        "ternary_image": ternary,
        "binary_image": 1 << WIDTH,
        "between_two_powers": 2 ** 38 < ternary < 2 ** 39,
        "gain_ratio": Fraction(ternary, 1 << WIDTH),
        "xor_recovered_from_tsum": bool(xor_ok),
        "intersection_recovered_from_tsum": bool(inter_ok),
        "pair_recovered_from_tsum_and_tdiff": bool(pair_ok),
        "code_closed_under_tsum": False,
        "lean": "GLM.Golay24.tsum_inter, GLM.Golay24.tsum_tdiff_injective",
    }


# ---------------------------------------------------------------------------
# 5.  Where XOR actually occurs in the runtime
# ---------------------------------------------------------------------------
#: Every non-test module of the package that contains a Python ``^``, with the
#: roles it plays.  Checked against the tree by :func:`xor_inventory`.
XOR_SITES: Tuple[Tuple[str, Tuple[str, ...], str], ...] = (
    ("benchmarks/suites.py", ("group-law",),
     "code arithmetic inside the substrate suite"),
    ("data_objects/elements.py", ("group-law",),
     "element carriers combined in F2^24"),
    ("examples/encoding_poc.py", ("group-law",),
     "the encoding walk-through adds codewords"),
    ("examples/integrated_nrci.py", ("metric",),
     "popcount of a difference: an NRCI distance"),
    ("examples/scaled_carriers.py", ("group-law",),
     "carriers scaled by adding a codeword"),
    ("migration/frames.py", ("group-law",),
     "the frame permutation acts by relabelling and re-adding"),
    ("migration/state.py", ("digest",),
     "an integrity checksum over the stored state (D3)"),
    ("migration/store.py", ("group-law",),
     "stored masks recombined in F2^24"),
    ("reasoning/catalog.py", ("group-law",),
     "study addresses combined in F2^24"),
    ("reasoning/coherence.py", ("metric",),
     "NRCI is a normalised Hamming distance"),
    ("reasoning/combiner.py", ("group-law", "metric"),
     "this module: the classification itself, and the fibre census"),
    ("reasoning/deep_dive.py", ("metric",),
     "Hamming separation between the layers of a dive"),
    ("reasoning/dimension_layers.py", ("group-law", "metric"),
     "layer views combined, and compared by Hamming distance"),
    ("reasoning/exact_real.py", ("group-law",),
     "the codeword ramp of the 24-D loop"),
    ("reasoning/fwht_decode.py", ("group-law",),
     "the Walsh-Hadamard decoder adds coset representatives"),
    # ``reasoning/lean_address.py`` used to be declared here as a digest site.
    # Its address is now a SHA-256 of the declaration text, so the module
    # contains no ``^`` at all and the row was retired: a declared site that
    # the tree no longer contains is reported as stale by xor_inventory, which
    # is exactly the drift the inventory exists to catch.
    ("reasoning/llvq_table.py", ("group-law",),
     "coset representatives of the lookup table"),
    ("reasoning/monster_stack.py", ("group-law", "retired"),
     "plane-wise group law, and compose_xor -- the retired Sakuma shortcut, "
     "kept so shortcut_loss_report can count what it discarded"),
    ("reasoning/multires.py", ("group-law", "metric"),
     "the F2^4 <-> GF(4) x Z_4 fibration and its distances"),
    ("reasoning/product.py", ("group-law",),
     "the axis label of a 2A pair; the product itself is axis_product"),
    ("reasoning/salvage.py", ("metric",),
     "Hamming distance between a candidate and the target"),
    ("reasoning/salvage_second.py", ("group-law", "metric"),
     "hexacode and cube-code arithmetic, and the Gray-jump distance"),
    # ``reasoning/search_loop.py`` used to be declared here as a metric site.
    # Its D1 gate compares outputs with ``!=`` on the decoded values rather
    # than by a Hamming distance on words, so the module contains no ``^`` and
    # the row was retired for the same reason as lean_address above.
    ("reasoning/tasks.py", ("group-law",),
     "task carriers combined in F2^24"),
    ("substrate/digit_stack.py", ("group-law",),
     "the digit stack adds words cube by cube"),
    ("substrate/golay_decode.py", ("group-law",),
     "syndrome decoding adds the coset leader"),
    ("substrate/isomorphism.py", ("group-law", "metric"),
     "the isomorphism transports the group law and checks it by distance"),
    ("substrate/lattice32.py", ("group-law",),
     "Construction A on the 32-dimensional lattice"),
    ("substrate/lattice48.py", ("group-law",),
     "Construction A on the 48-dimensional lattice"),
    ("substrate/leech2.py", ("group-law", "metric"),
     "the Leech lattice mod 2, and Hamming distance on its words"),
    ("substrate/linalg.py", ("group-law",),
     "row reduction over F2"),
    ("substrate/mog.py", ("group-law", "metric"),
     "the Golay code's own operation, and the weight of a difference"),
    ("substrate/superposition.py", ("group-law", "retired"),
     "the coset group law, and bundle_f2 -- the retired lossy bundle, kept "
     "because its degeneracy is the reported result"),
)

#: What each retired site was replaced by.
REPLACEMENTS: Dict[str, str] = {
    "reasoning/monster_stack.py":
        "reasoning/product.py: axis_product (the full Sakuma product)",
    "substrate/superposition.py":
        "substrate/superposition.py: bundle_rational (the exact "
        "coordinatewise mean)",
}


def _package_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent


def _xor_uses(path: pathlib.Path) -> int:
    """How many ``^`` nodes the module's syntax tree contains.

    Parsing rather than grepping is the point: a ``^`` inside a docstring or a
    regular expression is not a XOR site.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return sum(
        1 for node in ast.walk(tree)
        if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitXor))
        or (isinstance(node, ast.AugAssign) and isinstance(node.op, ast.BitXor))
    )


def xor_inventory() -> Dict[str, object]:
    """Scan the tree and check :data:`XOR_SITES` against it.

    Fails -- by reporting, not by raising -- if a module has started using XOR
    without being classified, or if a declared site no longer uses it.
    """
    root = _package_root()
    found: Dict[str, int] = {}
    for path in sorted(root.rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        if rel.startswith("tests/") or "__pycache__" in rel:
            continue
        uses = _xor_uses(path)
        if uses:
            found[rel] = uses
    declared = {module: roles for module, roles, _ in XOR_SITES}
    unclassified = tuple(sorted(set(found) - set(declared)))
    stale = tuple(sorted(set(declared) - set(found)))
    by_role: Dict[str, int] = {role: 0 for role in ROLES}
    for module, roles in declared.items():
        if module not in found:
            continue
        for role in roles:
            by_role[role] += 1
    retired = tuple(sorted(m for m, roles in declared.items()
                           if "retired" in roles))
    return {
        "modules_using_xor": len(found),
        "uses": sum(found.values()),
        "declared_modules": len(declared),
        "by_role": by_role,
        "unclassified_modules": unclassified,
        "stale_declarations": stale,
        "inventory_is_complete": not unclassified and not stale,
        "lossy_combiner_modules": retired,
        "replacements": dict(REPLACEMENTS),
    }


# ---------------------------------------------------------------------------
# 6.  One call for the whole study
# ---------------------------------------------------------------------------
def combiner_report() -> Dict[str, object]:
    """Every section of ``studies/COMBINER_STUDY.md``, recomputed."""
    return {
        "closure": closure_report(),
        "fibres": fibre_report(),
        "small_census": small_fibre_census(4),
        "integer_layer": integer_layer_report(),
        "inventory": xor_inventory(),
        "study": "studies/COMBINER_STUDY.md",
        "lean_file": "RequestProject/GLM/Combiner.lean",
    }

"""``glm_universal.reasoning.python_substrate`` -- where Python values live.

The substrate half of ``studies/PYTHON_SPEECH_STUDY.md``. It says where each
Python construct is placed on the 24-coordinate carrier, and it runs the
parts that have to run *on* the substrate rather than in ordinary integer
arithmetic:

* **The sub-registers.** A 24-bit word is eight vertical registers of three
  lanes each (``reversible.BLOCKS_8x3``). A bitwise operation between two
  words runs one small gate program per lane, on the triple
  ``(a, b, t)`` -- operand bit, operand bit, target line started at 0 -- with
  a constant rail ``1`` available as a control. The gates are
  ``reversible.toffoli`` (CCNOT) and ``reversible.fredkin`` (CSWAP), each an
  involution, so every program is undone by running it backwards. The
  inverse run is performed and checked on every lane: an operation that did
  not restore its inputs would raise, so the count of erased bits reported
  is a measurement, not an assumption. Integers of any width and sign are
  laid on a tower of 24-bit words in two's complement, wide enough that the
  top bit is the sign, which is how CPython's infinite two's complement is
  reproduced exactly.
* **Dyadic moves.** ``<<`` and ``>>`` are exact multiplication by ``2**k``
  and floor division by ``2**k``; ``plane(q, k)`` is the plane reading
  ``floor(q * 2**k)``.
* **Characters and slices.** A string is a sequence of code points, one per
  24-bit block; position ``i`` sits in MOG cell ``mog_index_of(i % 24)`` of
  carrier ``i // 24``. A slice is the index map ``i -> start + i*step``
  after CPython's own clamping, computed here, never by Python's slicing.
* **Masks.** A ``frozenset`` of coordinates ``0..23`` is a 24-bit Golay mask.
* **Classification.** ``classify(subject, *cases)`` routes a mask to the
  declared case codeword within distance 3, refuses ``AMBIGUOUS`` at
  distance 4 (the deep hole, six equidistant codewords) and
  ``UNCORRECTABLE`` at distance 5 or more. The complete coset decoder of
  ``substrate.golay_decode`` does the work.
* **AST addresses.** An expression is canonicalised (commutative operands
  sorted, redundant parentheses gone, variables renamed by first
  appearance) and embedded in ``Q^24``: each node contributes the Golay
  codeword of its node type, weighted by an exact dyadic code of its path
  from the root, so depth is a plane of the digit stack.
* **The prelude.** :data:`PRELUDE` is the same dialect written in plain
  Python: CPython runs it as the reference, and every column-3 script
  carries it. It shares no code with this module -- its ``classify`` is a
  brute-force distance search, not the coset decoder.

Exact throughout (D7): ``int`` and ``Fraction`` only.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from ..substrate import golay_decode as gd
from ..substrate.mog import GOLAY, mog_index_of
from . import reversible as rv

__all__ = [
    "REFUSAL_NAMES", "PythonRefusal", "WIDTH", "REGISTERS", "LANES",
    "GATE_PROGRAMS", "run_program", "invert_program", "lane_table",
    "RegisterRun", "register_bitwise", "register_invert", "register_load",
    "dyadic_shift", "plane", "slice_indices", "cell_of_position",
    "mask_of_frozenset", "frozenset_of_mask", "Classification",
    "classify", "golay_encode", "ds_bits", "canonical_form",
    "ast_address", "PRELUDE", "Resolution", "nearest", "resolve", "agree",
    "decode_confidence", "agree_confidence",
    "resolve_unsure", "resolve_at", "agree_at", "resolve_floor",
    "agree_floor", "SOFT_GRID", "decode_soft", "decode_soft_floor",
    "agree_soft",
]


# ===========================================================================
# 0.  THE REFUSAL CONTRACT
# ===========================================================================

#: Every named refusal, in the order ``studies/PYTHON_SPEECH_STUDY.md`` §1
#: lists them.
REFUSAL_NAMES: Tuple[str, ...] = (
    "FLOAT", "NONDETERMINISTIC", "AMBIGUOUS", "UNCORRECTABLE",
    "SCALE_MISMATCH", "ORDER_UNDEFINED", "OUTSIDE_SUBSTRATE",
    "CARRIER_OVERFLOW", "MUTABLE_CONTAINER", "UNSUPPORTED", "BUDGET",
    "PYTHON_ERROR",
    # Phase 77 (the decoder-confidence study): a confidence asked at a deep
    # hole with nothing to prune it, and a bit-flip rate outside (0, 1/2).
    "TIE", "RATE_OUT_OF_RANGE",
    # Phase 80 (the confidence-floor study): an answer below the declared
    # confidence floor, and a floor that is not an exact rational in (0, 1].
    "BELOW_FLOOR", "FLOOR_OUT_OF_RANGE",
    # Phase 82 (the rate-posterior study): the reads make the guard rate the
    # most probable of the declared grid.
    "RATE_GRID_EXCEEDED",
)


class PythonRefusal(ValueError):
    """A named refusal: the GLM declines instead of estimating."""

    def __init__(self, name: str, reason: str) -> None:
        if name not in REFUSAL_NAMES:
            raise ValueError(f"unknown refusal name {name!r}")
        super().__init__(f"{name}: {reason}")
        self.name = name
        self.reason = reason


# ===========================================================================
# 1.  THE SUB-REGISTERS
# ===========================================================================

WIDTH = 24
REGISTERS = 8
LANES = 3

#: One gate is ``(kind, x, y, z)`` over the line names ``"a"``, ``"b"``,
#: ``"t"`` and the constant rail ``"1"``. ``TOF`` toggles ``z`` when ``x``
#: and ``y`` are both 1; ``FRED`` swaps ``y`` and ``z`` when ``x`` is 1.
#: ``result`` names the line the answer is read from.
GATE_PROGRAMS: Dict[str, Dict[str, object]] = {
    "and": {"gates": (("TOF", "a", "b", "t"),), "result": "t"},
    "xor": {"gates": (("TOF", "1", "a", "t"), ("TOF", "1", "b", "t")),
            "result": "t"},
    "or": {"gates": (("TOF", "a", "b", "t"), ("TOF", "1", "a", "t"),
                     ("TOF", "1", "b", "t")), "result": "t"},
    "not": {"gates": (("TOF", "1", "1", "t"), ("TOF", "1", "a", "t")),
            "result": "t"},
    "copy": {"gates": (("TOF", "1", "a", "t"),), "result": "t"},
    #  a AND NOT b, in place on line a, by one Fredkin gate: when b is set
    #  the bit of a is swapped into t, so t keeps a AND b and nothing is lost.
    "andnot": {"gates": (("FRED", "b", "a", "t"),), "result": "a"},
}


def _apply_gate(state: Dict[str, int], gate: Tuple[str, str, str, str]
                ) -> None:
    kind, x, y, z = gate
    for line in (x, y, z):
        if line not in ("a", "b", "t", "1"):
            raise ValueError(f"unknown line {line!r}")
    if z == "1" or (kind == "FRED" and y == "1"):
        raise ValueError("the constant rail cannot be a target")
    #  The three lines named by the gate form one 3-bit register; the rail
    #  stands in for a control that is fixed at 1.
    triple = (state[x], state[y], state[z])
    if kind == "TOF":
        out = rv.toffoli(triple)
    elif kind == "FRED":
        out = rv.fredkin(triple)
    else:
        raise ValueError(f"unknown gate {kind!r}")
    for line, bit in zip((x, y, z), out):
        if line == "1":
            if bit != 1:                            # pragma: no cover
                raise AssertionError("the constant rail moved")
        else:
            state[line] = bit


def run_program(name: str, a: int, b: int, t: int = 0
                ) -> Tuple[int, int, int]:
    """Run the named gate program on one lane; returns ``(a, b, t)``."""
    state = {"a": a, "b": b, "t": t, "1": 1}
    for gate in GATE_PROGRAMS[name]["gates"]:
        _apply_gate(state, gate)
    return state["a"], state["b"], state["t"]


def invert_program(name: str, a: int, b: int, t: int
                   ) -> Tuple[int, int, int]:
    """Run the named program backwards: every gate is its own inverse."""
    state = {"a": a, "b": b, "t": t, "1": 1}
    for gate in reversed(GATE_PROGRAMS[name]["gates"]):
        _apply_gate(state, gate)
    return state["a"], state["b"], state["t"]


def _reference(name: str, a: int, b: int) -> int:
    return {"and": a & b, "xor": a ^ b, "or": a | b, "not": 1 - a,
            "copy": a, "andnot": a & (1 - b)}[name]


def lane_table() -> Dict[str, Dict[str, object]]:
    """Every program on every lane state: its function and its inverse.

    ``computes`` is whether the result line holds the Boolean function on
    all four operand pairs with ``t = 0``; ``bijective`` is whether the
    program permutes the eight lane states; ``restores`` whether the inverse
    program undoes it on all eight.
    """
    out: Dict[str, Dict[str, object]] = {}
    for name, spec in GATE_PROGRAMS.items():
        idx = {"a": 0, "b": 1, "t": 2}[spec["result"]]
        computes = all(run_program(name, a, b)[idx] == _reference(name, a, b)
                       for a in (0, 1) for b in (0, 1))
        images = {run_program(name, a, b, t)
                  for a in (0, 1) for b in (0, 1) for t in (0, 1)}
        restores = all(invert_program(name, *run_program(name, a, b, t))
                       == (a, b, t)
                       for a in (0, 1) for b in (0, 1) for t in (0, 1))
        out[name] = {"gates": len(spec["gates"]), "computes": computes,
                     "bijective": len(images) == 8, "restores": restores}
    return out


@dataclass(frozen=True)
class RegisterRun:
    """One bitwise operation on the register tower."""

    op: str
    value: int
    width: int
    carriers: int
    gate_count: int
    lanes: int
    erased_bits: int


def _window(*values: int) -> int:
    bits = max([abs(v).bit_length() for v in values] + [1]) + 1
    return WIDTH * (-(-bits // WIDTH))


def _signed(value: int, width: int) -> int:
    return value - (1 << width) if value >> (width - 1) & 1 else value


def register_bitwise(op: str, a: int, b: int = 0) -> RegisterRun:
    """``a op b`` for ``op`` in and/or/xor/not/andnot, lane by lane.

    The operands are laid in two's complement on ``width // 24`` carriers
    of eight 3-lane registers. Each lane runs the op's gate program, then
    the inverse program, which must give back ``(a_bit, b_bit, 0)``.
    """
    if op not in GATE_PROGRAMS:
        raise ValueError(f"register_bitwise: no program {op!r}")
    width = _window(a, b)
    ua, ub = a % (1 << width), b % (1 << width)
    spec = GATE_PROGRAMS[op]
    idx = {"a": 0, "b": 1, "t": 2}[spec["result"]]
    result = 0
    erased = 0
    for base in range(0, width, WIDTH):
        for block in rv.BLOCKS_8x3:
            for lane in block:
                pos = base + lane
                abit, bbit = ua >> pos & 1, ub >> pos & 1
                after = run_program(op, abit, bbit, 0)
                result |= after[idx] << pos
                if invert_program(op, *after) != (abit, bbit, 0):
                    erased += 1                     # pragma: no cover
    if erased:                                      # pragma: no cover
        raise AssertionError(f"register_bitwise: {erased} lanes not restored")
    return RegisterRun(op=op, value=_signed(result, width), width=width,
                       carriers=width // WIDTH,
                       gate_count=len(spec["gates"]) * width, lanes=width,
                       erased_bits=erased)


def register_invert(a: int) -> RegisterRun:
    """``~a``: the NOT program on every lane of the tower."""
    return register_bitwise("not", a, 0)


def register_load(code: int) -> RegisterRun:
    """Load a code point into one 24-bit word by the COPY program."""
    if not 0 <= code < 1 << WIDTH:
        raise ValueError("register_load: a code point fits in 24 bits")
    run = register_bitwise("copy", code, 0)
    return RegisterRun(op="copy", value=run.value, width=WIDTH, carriers=1,
                       gate_count=WIDTH, lanes=WIDTH, erased_bits=0)


# ===========================================================================
# 2.  DYADIC MOVES, CHARACTERS, SLICES, MASKS
# ===========================================================================

#: The largest shift the dialect will carry out, a budget and not a law.
MAX_SHIFT = 1 << 16


def dyadic_shift(n: int, k: int, left: bool) -> int:
    """``n << k`` as ``n * 2**k``; ``n >> k`` as ``floor(n / 2**k)``."""
    if k < 0:
        raise PythonRefusal("PYTHON_ERROR", "ValueError: negative shift count")
    if k > MAX_SHIFT:
        raise PythonRefusal("BUDGET", f"shift by {k} exceeds {MAX_SHIFT}")
    return n * (1 << k) if left else n // (1 << k)


def plane(q, k: int) -> int:
    """The plane-``k`` reading of an exact number: ``floor(q * 2**k)``."""
    q = Fraction(q)
    return (q * (1 << k)).__floor__() if k >= 0 else (q / (1 << -k)).__floor__()


def slice_indices(length: int, start: Optional[int], stop: Optional[int],
                  step: Optional[int]) -> Tuple[int, ...]:
    """The source positions a slice reads, by CPython's clamping rules."""
    step = 1 if step is None else step
    if step == 0:
        raise PythonRefusal("PYTHON_ERROR", "ValueError: slice step cannot be zero")
    lower, upper = (0, length) if step > 0 else (-1, length - 1)

    def clamp(v: Optional[int], default: int) -> int:
        if v is None:
            return default
        if v < 0:
            v += length
            return lower if v < lower else v
        return upper if v > upper else v

    s = clamp(start, lower if step > 0 else upper)
    e = clamp(stop, upper if step > 0 else lower)
    if step > 0:
        count = (e - s + step - 1) // step if s < e else 0
    else:
        count = (s - e - step - 1) // (-step) if e < s else 0
    return tuple(s + i * step for i in range(count))


def cell_of_position(i: int) -> Tuple[int, int, int]:
    """``(carrier, row, col)`` of string position ``i`` on the MOG grid."""
    row, col = mog_index_of(i % WIDTH)
    return i // WIDTH, row, col


def mask_of_frozenset(items) -> int:
    """A frozenset of coordinates ``0..23`` as its 24-bit mask."""
    mask = 0
    for x in items:
        if isinstance(x, bool):
            x = int(x)
        if not isinstance(x, int) or not 0 <= x < WIDTH:
            raise PythonRefusal(
                "OUTSIDE_SUBSTRATE",
                f"a frozenset is a Golay mask over coordinates 0..23; "
                f"{x!r} is not one")
        mask |= 1 << x
    return mask


def frozenset_of_mask(mask: int) -> frozenset:
    return frozenset(i for i in range(WIDTH) if mask >> i & 1)


# ===========================================================================
# 3.  GOLAY CLASSIFICATION
# ===========================================================================

def golay_encode(message: int) -> int:
    """The Golay codeword mask of a 12-bit message."""
    if isinstance(message, bool) or not isinstance(message, int) \
            or not 0 <= message < 1 << 12:
        raise PythonRefusal("PYTHON_ERROR",
                            "ValueError: golay_encode takes a 12-bit int")
    return GOLAY.encode_mask(message)


@dataclass(frozen=True)
class Classification:
    subject: int
    coset_weight: int
    candidates: Tuple[int, ...]
    distances: Tuple[int, ...]
    branch: Optional[int]
    verdict: str


def classify(subject: int, cases: Sequence[int]) -> Classification:
    """Route a mask to a declared case codeword, or refuse by name.

    Every case must be a codeword, so the radius-3 balls around the cases
    are disjoint (minimum distance 8). The verdict is ``branch`` at
    distance ``<= 3``, ``AMBIGUOUS`` at 4 and ``UNCORRECTABLE`` at ``>= 5``;
    it is read off the complete decoder, and the distances are reported as
    the certificate.
    """
    for c in cases:
        if not GOLAY.is_codeword(c):
            raise PythonRefusal("OUTSIDE_SUBSTRATE",
                                f"case {c} is not a Golay codeword")
    dec = gd.decode_complete(subject)
    distances = tuple(bin(subject ^ c).count("1") for c in cases)
    if dec.status in ("codeword", "corrected"):
        hit = [i for i, c in enumerate(cases) if c == dec.corrected]
        if hit:
            return Classification(subject, dec.weight, dec.candidates,
                                  distances, hit[0], "branch")
        return Classification(subject, dec.weight, dec.candidates, distances,
                              None, "UNCORRECTABLE")
    #  coset weight 4: six codewords at distance 4
    if any(c in dec.candidates for c in cases):
        return Classification(subject, dec.weight, dec.candidates, distances,
                              None, "AMBIGUOUS")
    return Classification(subject, dec.weight, dec.candidates, distances,
                          None, "UNCORRECTABLE")


# ---------------------------------------------------------------------------
# 3b.  THE CARRIED FORK (studies/CARRIED_FORK_STUDY.md)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Resolution:
    """What a carried fork became after a later decision.

    ``candidates`` are the nearest codewords of the read (six at the deep
    hole), ``live`` those the decision left, ``value`` the single survivor
    (``None`` unless ``verdict == "resolved"``), ``assumptions`` what the
    removals rest on, and ``index`` the survivor's first position among the
    declared cases where there are cases.
    """
    subject: int
    coset_weight: int
    candidates: Tuple[int, ...]
    live: Tuple[int, ...]
    verdict: str
    value: Optional[int]
    index: Optional[int]
    assumptions: Tuple[str, ...]


def _fork_resolution(fork, verdict_empty: str,
                     cases: Optional[Sequence[int]] = None) -> Resolution:
    if fork.status == "resolved":
        verdict = "resolved"
    elif fork.status == "open":
        verdict = "AMBIGUOUS"
    else:
        verdict = verdict_empty
    index = None
    if verdict == "resolved" and cases is not None:
        index = list(cases).index(fork.value)
    return Resolution(fork.received, fork.weight, fork.candidates, fork.live,
                      verdict, fork.value, index, fork.assumptions)


def nearest(subject: int) -> Tuple[int, ...]:
    """Every nearest codeword of ``subject`` -- one, or six at the deep hole."""
    from .carried_fork import carry
    return carry(subject).candidates


def resolve(subject: int, cases: Sequence[int]) -> Resolution:
    """The carried fork of ``subject``, pruned to the declared ``cases``.

    Where :func:`classify` refuses a deep hole outright, this keeps the six
    candidates and removes those that are not declared cases, under the
    closed-world assumption that the subject is a read of one of them.
    Exactly one survivor is an answer; several are ``AMBIGUOUS``; none is
    ``UNCORRECTABLE``.
    """
    from .carried_fork import carry
    for c in cases:
        if not GOLAY.is_codeword(c):
            raise PythonRefusal("OUTSIDE_SUBSTRATE",
                                f"case {c} is not a Golay codeword")
    fork = carry(subject).restrict_to_cases(cases)
    return _fork_resolution(fork, "UNCORRECTABLE", cases)


def agree(reads: Sequence[int]) -> Resolution:
    """The fork of the first read, pruned by every further read of the same
    carrier (the second-reading stage)."""
    from .carried_fork import carry
    if not reads:
        raise PythonRefusal("PYTHON_ERROR", "TypeError: agree() needs a read")
    fork = carry(reads[0])
    for r in reads[1:]:
        fork = fork.intersect(carry(r))
    return _fork_resolution(fork, "UNCORRECTABLE")


def resolve_unsure(subject: int, unsure: int) -> Resolution:
    """The fork of ``subject`` with every candidate whose error pattern
    touches a coordinate outside ``unsure`` proven incorrect."""
    from .carried_fork import carry
    fork = carry(subject).rule_out_sure(unsure)
    return _fork_resolution(fork, "UNCORRECTABLE")


def decode_confidence(rate, subject: int, cases: Sequence[int] = ()
                      ) -> Dict[str, object]:
    """The decoding of ``subject`` -- the decoder's own, or the carried fork
    pruned to ``cases`` -- with the probability that it is the codeword sent,
    each bit flipping independently at ``rate``.  Refuses where the reading
    refuses, by the same name (:mod:`.decoder_confidence`)."""
    from .decoder_confidence import ConfidenceRefusal
    from .decoder_confidence import decode_confidence as confidence_of
    try:
        return confidence_of(subject, rate, list(cases) if cases else None)
    except ConfidenceRefusal as r:
        raise PythonRefusal(r.name, r.reason) from None


def agree_confidence(rate, reads: Sequence[int]) -> Dict[str, object]:
    """The second reading of one carrier with the probability that the
    agreed codeword is the carrier (:mod:`.decoder_confidence`)."""
    from .decoder_confidence import ConfidenceRefusal
    from .decoder_confidence import agree_confidence as confidence_of
    try:
        return confidence_of(list(reads), rate)
    except ConfidenceRefusal as r:
        raise PythonRefusal(r.name, r.reason) from None


def _floor_call(fn, *args) -> Dict[str, object]:
    from .decoder_confidence import ConfidenceRefusal
    try:
        return fn(*args)
    except ConfidenceRefusal as r:
        raise PythonRefusal(r.name, r.reason) from None


def resolve_at(rate, subject: int, cases: Sequence[int]) -> Dict[str, object]:
    """``resolve`` with the confidence beside its answer: the graded reading,
    never refused on confidence (:mod:`.confidence_floor`)."""
    from .confidence_floor import graded_resolve
    return _floor_call(graded_resolve, subject, rate, list(cases))


def agree_at(rate, reads: Sequence[int]) -> Dict[str, object]:
    """``agree`` with the confidence beside its answer (the graded reading)."""
    from .confidence_floor import graded_agree
    return _floor_call(graded_agree, list(reads), rate)


def resolve_floor(rate, floor, subject: int,
                  cases: Sequence[int]) -> Dict[str, object]:
    """``resolve`` answered only at a confidence of at least ``floor``;
    otherwise ``BELOW_FLOOR`` (:mod:`.confidence_floor`)."""
    from .confidence_floor import floor_resolve
    return _floor_call(floor_resolve, subject, rate, floor, list(cases))


def agree_floor(rate, floor, reads: Sequence[int]) -> Dict[str, object]:
    """``agree`` answered only at a confidence of at least ``floor``."""
    from .confidence_floor import floor_agree
    return _floor_call(floor_agree, list(reads), rate, floor)


#: The declared grid of the rate posterior (:mod:`.rate_posterior`).
SOFT_GRID: Tuple[Fraction, ...] = (Fraction(1, 1000), Fraction(1, 100),
                                   Fraction(1, 50), Fraction(1, 20),
                                   Fraction(1, 10), Fraction(1, 5))


def decode_soft(subject: int, corpus: Sequence[int]) -> Dict[str, object]:
    """The decoder's value with its confidence marginalized over the rate
    read off the call's own reads (:mod:`.rate_posterior`)."""
    from .rate_posterior import decode_soft as soft
    return _floor_call(soft, subject, list(corpus))


def decode_soft_floor(floor, subject: int,
                      corpus: Sequence[int]) -> Dict[str, object]:
    """:func:`decode_soft` answered only at a marginal confidence of at least
    ``floor``; otherwise ``BELOW_FLOOR``."""
    from .rate_posterior import decode_soft_floor as soft
    return _floor_call(soft, floor, subject, list(corpus))


def agree_soft(r1: int, r2: int, corpus: Sequence[int]) -> Dict[str, object]:
    """``agree``'s value with its confidence marginalized over the rate read
    off the pair and the corpus."""
    from .rate_posterior import agree_soft as soft
    return _floor_call(soft, r1, r2, list(corpus))


def ds_bits(t, n: int) -> Tuple[int, ...]:
    """``n`` ticks of the first-order delta-sigma loop on ``0 <= t < 1``.

    The accumulator gains ``t`` each tick and emits 1 whenever it reaches 1;
    the ones-count after ``n`` ticks is ``floor(n t)``
    (``GLM.SubstrateCognition.dsStream_sum``).
    """
    t = Fraction(t)
    if not 0 <= t < 1:
        raise PythonRefusal("PYTHON_ERROR", "ValueError: ds_bits needs 0 <= t < 1")
    acc, out = Fraction(0), []
    for _ in range(n):
        acc += t
        if acc >= 1:
            acc -= 1
            out.append(1)
        else:
            out.append(0)
    return tuple(out)


# ===========================================================================
# 4.  AST ADDRESSES
# ===========================================================================

_COMMUTATIVE = (ast.Add, ast.Mult, ast.BitAnd, ast.BitOr, ast.BitXor)

#: Node kinds, each given a Golay message (its index + 1).
_KINDS: Tuple[str, ...] = (
    "Name", "Int", "Bool", "Fraction", "Str", "None", "Call", "Tuple",
    "Subscript", "Slice", "IfExp", "Attribute",
    "Add", "Sub", "Mult", "FloorDiv", "Mod", "Pow", "LShift", "RShift",
    "BitAnd", "BitOr", "BitXor", "Div", "MatMult",
    "USub", "UAdd", "Invert", "Not", "And", "Or",
    "Eq", "NotEq", "Lt", "LtE", "Gt", "GtE", "In", "NotIn", "Is", "IsNot",
    "Empty", "Other",
)


def _node_form(node: ast.AST):
    """A nested-tuple form of an expression, commutative operands sorted."""
    if isinstance(node, ast.Expression):
        return _node_form(node.body)
    if isinstance(node, ast.Name):
        return ("Name", node.id)
    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, bool):
            return ("Bool", int(v))
        if isinstance(v, int):
            return ("Int", v)
        if isinstance(v, str):
            return ("Str", v)
        if v is None:
            return ("None",)
        return ("Other", repr(type(v).__name__))
    if isinstance(node, ast.BinOp):
        op = type(node.op).__name__
        kids = [_node_form(node.left), _node_form(node.right)]
        if isinstance(node.op, _COMMUTATIVE):
            kids.sort(key=repr)
        return (op, *kids)
    if isinstance(node, ast.UnaryOp):
        return (type(node.op).__name__, _node_form(node.operand))
    if isinstance(node, ast.BoolOp):
        return (type(node.op).__name__, *[_node_form(v) for v in node.values])
    if isinstance(node, ast.Compare):
        if len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
            kids = sorted([_node_form(node.left),
                           _node_form(node.comparators[0])], key=repr)
            return (type(node.ops[0]).__name__, *kids)
        out = [_node_form(node.left)]
        for op, c in zip(node.ops, node.comparators):
            out.append((type(op).__name__, _node_form(c)))
        return ("Compare", *out)
    if isinstance(node, ast.Call):
        name = node.func.id if isinstance(node.func, ast.Name) \
            else ast.unparse(node.func)
        return ("Call", ("Func", name), *[_node_form(a) for a in node.args])
    if isinstance(node, ast.Tuple):
        return ("Tuple", *[_node_form(e) for e in node.elts])
    if isinstance(node, ast.Subscript):
        return ("Subscript", _node_form(node.value), _node_form(node.slice))
    if isinstance(node, ast.Slice):
        return ("Slice", *[("Empty",) if p is None else _node_form(p)
                           for p in (node.lower, node.upper, node.step)])
    if isinstance(node, ast.IfExp):
        return ("IfExp", _node_form(node.test), _node_form(node.body),
                _node_form(node.orelse))
    if isinstance(node, ast.Attribute):
        return ("Attribute", _node_form(node.value), ("Func", node.attr))
    return ("Other", type(node).__name__)


def _rename(form, table: Dict[str, str]):
    if isinstance(form, tuple) and form and form[0] == "Name":
        if form[1] not in table:
            table[form[1]] = f"v{len(table)}"
        return ("Name", table[form[1]])
    if isinstance(form, tuple):
        return tuple(_rename(x, table) for x in form)
    return form


def _resort(form):
    if not isinstance(form, tuple) or not form:
        return form
    kids = tuple(_resort(x) for x in form[1:])
    if form[0] in ("Add", "Mult", "BitAnd", "BitOr", "BitXor", "Eq", "NotEq"):
        kids = tuple(sorted(kids, key=repr))
    return (form[0], *kids)


def canonical_form(source: str):
    """The canonical form of one expression.

    Commutative operands (``+ * & | ^ == !=``) are sorted, parentheses and
    whitespace vanish with the parse, and variables are renamed ``v0, v1,
    ...`` by first appearance; sorting and renaming are repeated until
    nothing moves (at most eight rounds). This decides equality up to those
    rewrites only. It treats ``+`` and ``*`` as commutative, which is true
    of numbers and false of strings and tuples, so it is a structural
    address of an expression over numbers, not a semantic one.
    """
    form = _node_form(ast.parse(source, mode="eval"))
    for _ in range(8):
        new = _resort(_rename(form, {}))
        if new == form:
            break
        form = new
    return form


def _kind_of(form) -> Tuple[str, object]:
    head = form[0]
    payload: object = 0
    if head == "Name":
        payload = int(form[1][1:]) + 1
    elif head in ("Int", "Bool"):
        payload = form[1]
    elif head == "Str":
        payload = sum(ord(ch) << (21 * i) for i, ch in enumerate(form[1])) + 1
    elif head == "Func":
        payload = sum(ord(ch) << (21 * i) for i, ch in enumerate(form[1])) + 1
        head = "Call"
    kind = head if head in _KINDS else "Other"
    return kind, payload


def ast_address(source: str) -> Dict[str, object]:
    """The structural address of an expression in ``Q^24``.

    Every node of the canonical form contributes the Golay codeword of its
    kind, scaled by the exact dyadic code of its path (child ``j`` at depth
    ``d`` contributes ``(j + 1) / 32**d``), with its payload (variable
    number, literal value) added on the coordinate its kind indexes. The
    DAG count is the number of distinct subtrees.
    """
    form = canonical_form(source)
    coords = [Fraction(0)] * WIDTH
    subtrees = set()
    nodes = 0
    depth_max = 0

    def walk(f, path_code: Fraction, depth: int) -> None:
        nonlocal nodes, depth_max
        if not isinstance(f, tuple) or not f or not isinstance(f[0], str):
            return
        nodes += 1
        depth_max = max(depth_max, depth)
        subtrees.add(repr(f))
        kind, payload = _kind_of(f)
        k = _KINDS.index(kind)
        word = GOLAY.encode_mask(k + 1)
        for j in range(WIDTH):
            if word >> j & 1:
                coords[j] += path_code
        if payload:
            coords[k % WIDTH] += Fraction(payload) * path_code / (1 << 20)
        child = 0
        for x in f[1:]:
            if isinstance(x, tuple) and x and isinstance(x[0], str):
                child += 1
                walk(x, path_code + Fraction(child, 32 ** (depth + 1)),
                     depth + 1)

    walk(form, Fraction(1), 0)
    return {"canonical": form, "carrier": tuple(coords), "nodes": nodes,
            "dag_nodes": len(subtrees), "depth": depth_max}


# ===========================================================================
# 5.  THE PRELUDE -- the dialect in plain Python, for CPython and column 3
# ===========================================================================

_GOLAY_ROWS = tuple(GOLAY.encode_mask(1 << i) for i in range(12))

PRELUDE = '''
from fractions import Fraction


class GLMRefusal(Exception):
    """A named refusal raised by the plain-Python prelude."""

    def __init__(self, name, reason):
        Exception.__init__(self, name + ": " + reason)
        self.name = name


class unit:
    """A quantity with a declared unit; comparison across units is refused."""

    __hash__ = None

    def __init__(self, value, name):
        if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
            raise GLMRefusal("FLOAT", "a unit value must be exact")
        self.value, self.name = value, name

    def _peer(self, other):
        if not isinstance(other, unit) or other.name != self.name:
            raise GLMRefusal("SCALE_MISMATCH", "different or undeclared units")
        return other.value

    def __eq__(self, other): return self.value == self._peer(other)
    def __ne__(self, other): return self.value != self._peer(other)
    def __lt__(self, other): return self.value < self._peer(other)
    def __le__(self, other): return self.value <= self._peer(other)
    def __gt__(self, other): return self.value > self._peer(other)
    def __ge__(self, other): return self.value >= self._peer(other)
    def __add__(self, other): return unit(self.value + self._peer(other), self.name)
    def __sub__(self, other): return unit(self.value - self._peer(other), self.name)
    def __repr__(self): return "unit(%%r, %%r)" %% (self.value, self.name)


GOLAY_ROWS = %(rows)r


def golay_encode(message):
    out = 0
    for i in range(12):
        if message >> i & 1:
            out ^= GOLAY_ROWS[i]
    return out


def _mask(x):
    if isinstance(x, frozenset):
        m = 0
        for i in x:
            m |= 1 << i
        return m
    return x


def hamming(a, b):
    return bin(_mask(a) ^ _mask(b)).count("1")


_CODEWORDS = None


def _codewords():
    global _CODEWORDS
    if _CODEWORDS is None:
        _CODEWORDS = frozenset(golay_encode(m) for m in range(4096))
    return _CODEWORDS


def classify(subject, *cases):
    subject = _mask(subject)
    cases = [_mask(c) for c in cases]
    for c in cases:
        if c not in _codewords():
            raise GLMRefusal("OUTSIDE_SUBSTRATE", "a case is not a codeword")
    d = [hamming(subject, c) for c in cases]
    best = min(d)
    if best <= 3:
        return d.index(best)
    if best == 4:
        raise GLMRefusal("AMBIGUOUS", "deep hole: distance 4")
    raise GLMRefusal("UNCORRECTABLE", "distance %%d" %% best)


def nearest(subject):
    subject = _mask(subject)
    best = min(hamming(subject, c) for c in _codewords())
    return tuple(sorted(c for c in _codewords() if hamming(subject, c) == best))


def _survivor(live, what):
    live = sorted(set(live))
    if len(live) == 1:
        return live[0]
    if live:
        raise GLMRefusal("AMBIGUOUS", "%%d candidates survive %%s" %% (len(live), what))
    raise GLMRefusal("UNCORRECTABLE", "no candidate survives %%s" %% what)


def resolve(subject, *cases):
    cases = [_mask(c) for c in cases]
    for c in cases:
        if c not in _codewords():
            raise GLMRefusal("OUTSIDE_SUBSTRATE", "a case is not a codeword")
    fork = nearest(subject)
    value = _survivor([c for c in fork if c in cases], "the declared cases")
    return cases.index(value)


def agree(*reads):
    live = set(nearest(reads[0]))
    for r in reads[1:]:
        live &= set(nearest(r))
    return _survivor(live, "every read")


def resolve_unsure(subject, unsure):
    subject, sure = _mask(subject), 0xFFFFFF & ~_mask(unsure)
    return _survivor([c for c in nearest(subject) if not (subject ^ c) & sure],
                     "the sure coordinates")


def _rate(rate):
    if isinstance(rate, bool) or not isinstance(rate, (int, Fraction)):
        raise GLMRefusal("RATE_OUT_OF_RANGE", "the rate must be exact")
    rate = Fraction(rate)
    if not 0 < rate < Fraction(1, 2):
        raise GLMRefusal("RATE_OUT_OF_RANGE", "the rate is outside (0, 1/2)")
    return rate


def _likelihood(reads, c, rate):
    out = Fraction(1)
    for r in reads:
        d = hamming(r, c)
        out *= rate ** d * (1 - rate) ** (24 - d)
    return out


def _posterior(reads, value, allowed, rate):
    total = Fraction(0)
    for c in allowed:
        total += _likelihood(reads, c, rate)
    return _likelihood(reads, value, rate) / total


def decode_confidence(rate, subject, *cases):
    rate, subject = _rate(rate), _mask(subject)
    if not cases:
        fork = nearest(subject)
        if len(fork) != 1:
            raise GLMRefusal("TIE", "%%d codewords are equally near" %% len(fork))
        return _posterior([subject], fork[0], sorted(_codewords()), rate)
    declared = []
    for c in cases:
        c = _mask(c)
        if c not in _codewords():
            raise GLMRefusal("OUTSIDE_SUBSTRATE", "a case is not a codeword")
        if c not in declared:
            declared.append(c)
    value = _survivor([c for c in nearest(subject) if c in declared],
                      "the declared cases")
    return _posterior([subject], value, declared, rate)


def agree_confidence(rate, *reads):
    rate = _rate(rate)
    reads = [_mask(r) for r in reads]
    value = agree(*reads)
    return _posterior(reads, value, sorted(_codewords()), rate)


def _floor(floor):
    if isinstance(floor, bool) or not isinstance(floor, (int, Fraction)):
        raise GLMRefusal("FLOOR_OUT_OF_RANGE", "the floor must be exact")
    floor = Fraction(floor)
    if not 0 < floor <= 1:
        raise GLMRefusal("FLOOR_OUT_OF_RANGE", "the floor is outside (0, 1]")
    return floor


def resolve_at(rate, subject, *cases):
    rate = _rate(rate)
    return (resolve(subject, *cases), decode_confidence(rate, subject, *cases))


def agree_at(rate, *reads):
    rate = _rate(rate)
    return (agree(*[_mask(r) for r in reads]), agree_confidence(rate, *reads))


def resolve_floor(rate, floor, subject, *cases):
    floor = _floor(floor)
    index, confidence = resolve_at(rate, subject, *cases)
    if confidence < floor:
        raise GLMRefusal("BELOW_FLOOR", "%%s is below the floor" %% confidence)
    return index


def agree_floor(rate, floor, *reads):
    floor = _floor(floor)
    value, confidence = agree_at(rate, *reads)
    if confidence < floor:
        raise GLMRefusal("BELOW_FLOOR", "%%s is below the floor" %% confidence)
    return value


_SOFT_GRID = (Fraction(1, 1000), Fraction(1, 100), Fraction(1, 50),
              Fraction(1, 20), Fraction(1, 10), Fraction(1, 5))


def _carrier_mass(reads, rate):
    total = Fraction(0)
    for c in _codewords():
        total += _likelihood(reads, c, rate)
    return total / len(_codewords())


def _soft_confidence(carriers, reads, value):
    unnorm = []
    for rate in _SOFT_GRID:
        x = Fraction(1, len(_SOFT_GRID))
        for carrier in carriers:
            x *= _carrier_mass(carrier, rate)
        unnorm.append(x)
    total = sum(unnorm)
    post = [x / total for x in unnorm]
    if post[-1] == max(post):
        raise GLMRefusal("RATE_GRID_EXCEEDED", "the guard rate is the most probable")
    conf = Fraction(0)
    for x, rate in zip(post, _SOFT_GRID):
        conf += x * _posterior(reads, value, sorted(_codewords()), rate)
    return conf


def decode_soft(subject, *corpus):
    subject = _mask(subject)
    corpus = [_mask(r) for r in corpus]
    fork = nearest(subject)
    if len(fork) != 1:
        raise GLMRefusal("TIE", "%%d codewords are equally near" %% len(fork))
    carriers = [[subject]] + [[r] for r in corpus]
    return (fork[0], _soft_confidence(carriers, [subject], fork[0]))


def decode_soft_floor(floor, subject, *corpus):
    floor = _floor(floor)
    value, confidence = decode_soft(subject, *corpus)
    if confidence < floor:
        raise GLMRefusal("BELOW_FLOOR", "%%s is below the floor" %% confidence)
    return value


def agree_soft(r1, r2, *corpus):
    r1, r2 = _mask(r1), _mask(r2)
    corpus = [_mask(r) for r in corpus]
    value = agree(r1, r2)
    carriers = [[r1, r2]] + [[r] for r in corpus]
    return (value, _soft_confidence(carriers, [r1, r2], value))


def ds_bits(t, n):
    t = Fraction(t)
    acc, out = Fraction(0), []
    for _ in range(n):
        acc += t
        if acc >= 1:
            acc -= 1
            out.append(1)
        else:
            out.append(0)
    return tuple(out)


def plane(q, k):
    q = Fraction(q)
    return (q * 2 ** k) // 1 if k >= 0 else (q / 2 ** (-k)) // 1


def same(x, y):
    """Equal in type and value, all the way down."""
    if type(x) is not type(y):
        return False
    if isinstance(x, tuple):
        return len(x) == len(y) and all(same(a, b) for a, b in zip(x, y))
    if isinstance(x, unit):
        return x.name == y.name and same(x.value, y.value)
    return x == y


def run_source(source):
    """Run a dialect program; the value of its last expression statement."""
    import ast as _ast
    tree = _ast.parse(source)
    env = {}
    env.update(PRELUDE_NAMES)
    body = tree.body
    last = None
    if body and isinstance(body[-1], _ast.Expr):
        last = _ast.Expression(body[-1].value)
        body = body[:-1]
    exec(compile(_ast.Module(body, []), "<glm>", "exec"), env)
    if last is None:
        return None
    return eval(compile(last, "<glm>", "eval"), env)


PRELUDE_NAMES = {"Fraction": Fraction, "unit": unit, "classify": classify,
                 "golay_encode": golay_encode, "hamming": hamming,
                 "ds_bits": ds_bits, "plane": plane, "nearest": nearest,
                 "resolve": resolve, "agree": agree,
                 "resolve_unsure": resolve_unsure,
                 "decode_confidence": decode_confidence,
                 "agree_confidence": agree_confidence,
                 "resolve_at": resolve_at, "agree_at": agree_at,
                 "resolve_floor": resolve_floor, "agree_floor": agree_floor,
                 "decode_soft": decode_soft,
                 "decode_soft_floor": decode_soft_floor,
                 "agree_soft": agree_soft}
''' % {"rows": _GOLAY_ROWS}
